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

from docbridge import *

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
        name = Fallthrough(field_names=["name", "cocktail_name"])

    manhattan = Cocktail(manhattan_data)
    assert manhattan.name == "Manhattan"


def test_fallthrough():
    class FallthroughClass(Document):
        a = Fallthrough(["a", "b"])

    myc = FallthroughClass({"a": "the_a_value"})
    assert myc.a == "the_a_value"

    myc = FallthroughClass({"a": None})
    assert myc.a == None

    myc = FallthroughClass({"a": "the_a_value", "b": "the_b_value"})
    assert myc.a == "the_a_value"

    myc = FallthroughClass({"b": "the_b_value"})
    assert myc.a == "the_b_value"

    try:
        myc = FallthroughClass({"c": "not_in_the_cascade"})
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
        != None
    )
