# Copyright 2023-present MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pytest import fail

from docbridge import Document, Field, FallthroughField, SequenceField
from itertools import islice
from pprint import pprint

manhattan_data = {
    "_id": {"$oid": "63177d736c36240b38778162"},
    "cocktail_name": "Manhattan",
    "description": "A classic cocktail consisting of Whiskey, Sweet Vermouth, and Angostura Bitters.",
    "created": {"$date": {"$numberLong": "1562176800000"}},
    "modified": {"$date": {"$numberLong": "1586167200000"}},
    "ingredients": [
        {"name": "Bourbon", "quantity": {"$numberInt": "60"}, "unit": "ml"},
        {"name": "Sweet Vermouth", "quantity": {"$numberInt": "30"}, "unit": "ml"},
        {"name": "Angostura Bitters", "quantity": {"$numberInt": "1"}, "unit": "dash"},
        {
            "name": "Spiced Cherry Bitters",
            "quantity": {"$numberInt": "1"},
            "unit": "dash",
        },
    ],
    "instructions": "Stir with ice. Serve in a martini glass with a maraschino cherry.",
    "garnish": "Maraschino Cherry",
    "favourite": True,
    "comments": ["I love this cocktail", "Meh. It's not for me."],
    "comments_length": 2,
    "schema_version": {"$numberInt": "2"},
}


def test_cocktails():
    class Cocktail(Document):
        name = FallthroughField(field_names=["name", "cocktail_name"])

    manhattan = Cocktail(manhattan_data, None)
    assert manhattan.name == "Manhattan"


def test_fallthrough():
    class FallthroughClass(Document):
        a = FallthroughField(["a", "b"])

    myc = FallthroughClass({"a": "the_a_value"}, None)
    assert myc.a == "the_a_value"

    myc = FallthroughClass({"a": None}, None)
    assert myc.a is None

    myc = FallthroughClass({"a": "the_a_value", "b": "the_b_value"}, None)
    assert myc.a == "the_a_value"

    myc = FallthroughClass({"b": "the_b_value"}, None)
    assert myc.a == "the_b_value"

    try:
        myc = FallthroughClass({"c": "not_in_the_cascade"}, None)
        assert myc.a == "should not be evaluated"
        fail()
    except ValueError as v:
        assert (
            str(v)
            == """Attribute 'a' references the field names 'a', 'b' which are not present."""
        )


def test_mongodb_client(mongodb):
    assert mongodb.admin.command("ping")["ok"] == 1.0


def test_update_mongodb(mongodb, rollback_session):
    mongodb.docbridge.tests.insert_one(
        {
            "_id": "bad_document",
            "description": "If this still exists, then transactions aren't working.",
        },
        session=rollback_session,
    )
    assert (
        mongodb.docbridge.tests.find_one(
            {"_id": "bad_document"}, session=rollback_session
        )
        is not None
    )


def test_sequence_field(mongodb):
    sample_profile = {
        "_id": {"$oid": "657072b56731c9e580e9dd6f"},
        "user_id": "4",
        "user_name": "@tara86",
        "full_name": "Bradley Olsen",
        "birth_date": {"$date": {"$numberLong": "1502064000000"}},
        "email": "elizabeth92@yahoo.com",
        "bio": "Discussion maintain watch computer impact tree situation. Vote know dream strong cause recently.",
        "follower_count": {"$numberInt": "11"},
        "followers": [
            {
                "_id": {"$oid": "657072b76731c9e580e9ddc5"},
                "user_id": "89",
                "user_name": "@christopherespinoza",
                "bio": "Require father citizen during. Nearly set of.",
            },
            {
                "_id": {"$oid": "657072b56731c9e580e9dd72"},
                "user_id": "6",
                "user_name": "@karenwilkins",
                "bio": "Each right different describe indicate scientist short look. Turn town either decade.",
            },
            {
                "_id": {"$oid": "657072b76731c9e580e9ddb7"},
                "user_id": "75",
                "user_name": "@tonymartinez",
                "bio": "Structure stage religious fund test. How eight large participant will morning first.",
            },
        ],
    }

    class Follower(Document):
        _id = Field(transform=str)

    class Profile(Document):
        _id = Field(transform=str)
        followers = SequenceField(type=Follower)

    profile = Profile(sample_profile, None)
    assert isinstance(next(profile.followers), Follower)


def test_sequence_field_superset(mongodb):
    class Follower(Document):
        _id = Field(transform=str)

    class Profile(Document):
        _id = Field(transform=str)
        followers = SequenceField(
            type=Follower,
            superset_collection="followers",
            superset_query=lambda ob: [
                {
                    "$match": {"user_id": ob.user_id},
                },
                {"$unwind": "$followers"},
                {"$replaceRoot": {"newRoot": "$followers"}},
            ],
        )

    db = mongodb.get_database("why")
    profile = Profile(db.get_collection("profiles").find_one({"user_id": "4"}), db)
    assert profile.user_id == "4"
    assert profile.full_name == "Deborah White"
    follower_boundary = islice(profile.followers, 19, 21)
    last_embed = next(follower_boundary)
    assert last_embed.user_name == "@nbrown"
    first_related = next(follower_boundary)
    print(first_related)
    assert first_related.user_name == "@hooperchristopher"


def test_update_field(mongodb, rollback_session):
    class Profile(Document):
        user_id = Field(transform=str.lower)

    db = mongodb.get_database("why")
    profile = Profile(db.get_collection("profiles").find_one({"user_id": "4"}), db)

    assert isinstance(Profile.user_id, Field)

    # Test that storing a configured value stores the (transformed) value on _doc:
    profile.user_id = "TEST_VALUE_4"
    assert profile.user_id == "test_value_4"
    assert profile._doc["user_id"] == "test_value_4"
    assert profile._modified_fields["user_id"] == "test_value_4"
    assert len(profile._modified_fields) == 1

    # Test that storing dynamic attributes stores the value in _doc:
    profile.non_existant = "new value"
    profile.non_existant == "new value"
    assert profile._doc["non_existant"] == "new value"
    assert profile._modified_fields["non_existant"] == "new value"
    assert len(profile._modified_fields) == 2


def test_update_strict_document(mongodb, rollback_session):
    class Profile(Document, strict=True):
        user_id = Field(transform=str.lower)

    db = mongodb.get_database("why")
    profile = Profile(db.get_collection("profiles").find_one({"user_id": "4"}), db)

    # Pre-defined field:
    profile.user_id = "TEST_VALUE_4"

    assert profile.user_id == "test_value_4"
    assert profile._doc["user_id"] == "test_value_4"
    assert profile._modified_fields["user_id"] == "test_value_4"
    assert len(profile._modified_fields) == 1

    try:
        profile.non_existant = "new value"
        fail("Should not be able to set dynamic value")
    except Exception:
        pass


def test_save(mongodb, rollback_session):
    from bson import ObjectId

    class Profile(Document):
        user_id = Field(transform=str.lower)

    db = mongodb.get_database("why")
    profile = Profile(
        db.get_collection("profiles").find_one(
            {"user_id": "4"}, session=rollback_session
        ),
        db,
    )

    # This is a dynamic field:
    assert profile.user_name == "@tanya15"
    profile.user_name = "new name value"
    assert "user_name" in profile._modified_fields

    # This is a configured field:
    assert profile.user_id == "4"
    profile.user_id = "new id value"
    assert "user_id" in profile._modified_fields

    profile.save("profiles", session=rollback_session)

    doc = db.get_collection("profiles").find_one(
        {"user_id": "new id value"}, session=rollback_session
    )
    assert doc is not None
    assert doc["user_id"] == "new id value"
    assert doc["user_name"] == "new name value"

    assert profile._modified_fields == {}


def test_meta():
    class StrictProfile(Document, strict=True):
        user_id = Field(transform=str.lower)

    assert StrictProfile._strict is True

    class Profile(Document):
        user_id = Field(transform=str.lower)

    assert Profile._strict is False
