"""Integration tests for docbridge.

Tests real MongoDB CRUD operations for the profiles collection used by the
docbridge FastAPI + Beanie example.

Requires a running MongoDB instance. Set MONGODB_URI (default:
mongodb://admin:mongodb@localhost:27017/) or the tests will be skipped.
"""

import os
import asyncio
import pytest
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://admin:mongodb@localhost:27017/")
TEST_DB = "docbridge_integration_test"


@pytest.fixture(scope="module")
def db():
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=2000)
    try:
        client.admin.command("ping")
    except Exception:
        client.close()
        pytest.skip(f"MongoDB not reachable at {MONGODB_URI}")
    database = client[TEST_DB]
    yield database
    client.drop_database(TEST_DB)
    client.close()


def test_mongodb_ping():
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=2000)
    try:
        result = client.admin.command("ping")
        assert result.get("ok") == 1.0
    except Exception:
        pytest.skip(f"MongoDB not reachable at {MONGODB_URI}")
    finally:
        client.close()


def test_profile_crud(db):
    """profiles collection: insert, find, update, delete a profile."""
    profiles = db["profiles"]

    profile_id = ObjectId()
    profile = {
        "_id": profile_id,
        "user_id": "u_001",
        "user_name": "jdoe",
        "full_name": "Jane Doe",
        "birth_date": datetime(1990, 5, 15),
        "email": "jane.doe@example.com",
        "followers": [{"user_id": "u_002"}, {"user_id": "u_003"}],
    }

    # Create
    result = profiles.insert_one(profile)
    assert result.inserted_id == profile_id

    # Read by user_id
    found = profiles.find_one({"user_id": "u_001"})
    assert found["user_name"] == "jdoe"
    assert found["full_name"] == "Jane Doe"
    assert len(found["followers"]) == 2

    # Update
    profiles.update_one(
        {"_id": profile_id},
        {"$push": {"followers": {"user_id": "u_004"}}}
    )
    updated = profiles.find_one({"_id": profile_id})
    assert len(updated["followers"]) == 3

    # Delete
    delete_result = profiles.delete_one({"_id": profile_id})
    assert delete_result.deleted_count == 1
    assert profiles.find_one({"_id": profile_id}) is None


def test_profile_not_found(db):
    """profiles collection: querying a non-existent user_id returns None."""
    profiles = db["profiles"]
    assert profiles.find_one({"user_id": "nonexistent_user"}) is None


def test_profile_follower_query(db):
    """profiles collection: query profiles that have a specific follower."""
    profiles = db["profiles"]

    ids = [ObjectId(), ObjectId()]
    docs = [
        {
            "_id": ids[0],
            "user_id": "u_010",
            "user_name": "alice",
            "full_name": "Alice Smith",
            "birth_date": datetime(1992, 3, 10),
            "email": "alice@example.com",
            "followers": [{"user_id": "u_999"}],
        },
        {
            "_id": ids[1],
            "user_id": "u_011",
            "user_name": "bob",
            "full_name": "Bob Jones",
            "birth_date": datetime(1988, 7, 20),
            "email": "bob@example.com",
            "followers": [],
        },
    ]
    profiles.insert_many(docs)

    followed_by_999 = list(
        profiles.find({"followers.user_id": "u_999", "_id": {"$in": ids}})
    )
    assert len(followed_by_999) == 1
    assert followed_by_999[0]["user_name"] == "alice"

    # Cleanup
    profiles.delete_many({"_id": {"$in": ids}})


def test_read_item_via_beanie(db):
    """Run the read_item endpoint logic against real MongoDB via Beanie."""
    try:
        from beanie import init_beanie, Document
        from pymongo import AsyncMongoClient
        from pydantic import BaseModel, Field

        class Follower(BaseModel):
            user_id: str

        class ProfileDoc(Document):
            user_id: str
            user_name: str
            full_name: str
            birth_date: datetime
            email: str
            followers: list

            class Settings:
                name = "profiles"

        async def _run():
            client = AsyncMongoClient(MONGODB_URI, serverSelectionTimeoutMS=3000)
            database = client[TEST_DB]
            await init_beanie(database=database, document_models=[ProfileDoc])

            # Insert via Beanie
            p = ProfileDoc(
                user_id="u_beanie_test",
                user_name="beanie_user",
                full_name="Beanie Tester",
                birth_date=datetime(1995, 1, 1),
                email="beanie@test.com",
                followers=[],
            )
            await p.insert()

            # Query via Beanie (mimics read_item endpoint)
            found = await ProfileDoc.find_one({"user_id": "u_beanie_test"})
            assert found is not None
            assert found.user_name == "beanie_user"

            await found.delete()
            client.close()

        asyncio.run(_run())
    except ImportError:
        pytest.skip("beanie not installed")
