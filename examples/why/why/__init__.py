from contextlib import asynccontextmanager
from datetime import datetime
import os

from fastapi import FastAPI

from motor.motor_asyncio import AsyncIOMotorClient
# from docbridge import Document, Field, SequenceField
from beanie import Document, init_beanie
from pydantic import BaseModel, Field



CONNECTION_STRING = os.environ["MDB_URI"]

@asynccontextmanager
async def db_lifespan(app: FastAPI):
    # Startup
    app.mongodb_client = motor = AsyncIOMotorClient(CONNECTION_STRING)
    app.database = db = motor.get_database("why")
    ping_response = await db.command("ping")
    if int(ping_response["ok"]) != 1:
        raise Exception("Problem connecting to database cluster.")
    else:
        print("Connected to database cluster.")
    
    await init_beanie(database=db, document_models=[Profile])
    
    yield

    # Shutdown
    app.mongodb_client.close()


app = FastAPI(lifespan=db_lifespan)


class Follower(BaseModel):
    user_id: str

class Profile(Document):
    user_id: str
    user_name: str
    full_name: str
    birth_date: datetime
    email: str
    followers: list[Follower]

    class Settings:
        name = "profiles"
        


@app.get("/profiles/{user_id}")
async def read_item(user_id: str) -> Profile:
    print(dir(Profile))
    profile = await Profile.find_one({"user_id": user_id})

    return profile
