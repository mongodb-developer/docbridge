import pytest

from docbridge import Document, Field, SequenceField


@pytest.mark.asyncio(scope="session")
async def test_motor_connection(motor):
    assert motor is not None


@pytest.mark.asyncio(scope="session")
async def test_embedded_sequence(motor):
    class Follower(Document):
        _id = Field(transform=str)

    class Profile(Document):
        _id = Field(transform=str)
        followers = SequenceField(type=Follower)

    db = motor.get_database("why")
    profiles = db.get_collection("profiles")

    bson = await profiles.find_one(
        {"user_id": "4"},
    )
    profile = Profile(
        bson,
        db,
    )

    followers = [{"db_id": follower._id} async for follower in profile.followers]
    assert len(followers) == 20


@pytest.mark.asyncio(scope="session")
async def test_related_sequence(motor):
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

    db = motor.get_database("why")
    profiles = db.get_collection("profiles")

    bson = await profiles.find_one(
        {"user_id": "4"},
    )
    profile = Profile(
        bson,
        db,
    )

    followers = [{"db_id": follower._id} async for follower in profile.followers]
    assert len(followers) == 59
