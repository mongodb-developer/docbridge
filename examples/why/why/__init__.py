import os

from fastapi import FastAPI

from motor.motor_asyncio import AsyncIOMotorClient as MotorClient
from docbridge import Document, Field, SequenceField

app = FastAPI()
motor = MotorClient(os.environ["MDB_URI"])
db = motor.get_database("why")

profiles = db.get_collection("profiles")
followers = db.get_collection("followers")


class Follower(Document):
    _id = Field(transform=str)


class Profile(Document):
    _id = Field(transform=str)
    followers = SequenceField(type=Follower)


@app.get("/profiles/{user_id}")
async def read_item(user_id: str):
    profile = Profile(
        await profiles.find_one(
            {"user_id": user_id},
        ),
        db,
    )
    return {
        "db_id": profile._id,
        "user_id": profile.user_id,
        "full_name": profile.full_name,
        "followers": [{"db_id": follower._id} for follower in profile.followers],
    }
