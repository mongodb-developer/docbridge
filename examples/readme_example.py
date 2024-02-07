import os
from pprint import pprint
from pymongo import MongoClient

collection = (
    MongoClient(os.environ["MDB_URI"]).get_database("why").get_collection("profiles")
)

user_data_bson = collection.find_one({"user_id": "4"})
pprint(user_data_bson)

# Example 1:
from docbridge import Document


class UserProfile(Document):
    pass


profile = UserProfile(user_data_bson, db=None)
print(repr(profile._id))  # ObjectId('657072b56731c9e580e9dd70')
print(repr(profile.user_id))  # "4"


# Example 2:
from docbridge import Document, Field


class UserProfile(Document):
    id = Field(field_name="_id")  # id maps to the _id doc field.
    user_id = Field(transform=int)  # user_id transforms the field value to an int


profile = UserProfile(user_data_bson, db=None)
print(repr(profile.id))  # ObjectId('657072b56731c9e580e9dd70')
print(repr(profile.user_id))  # 4 <- This is an int now!
print(
    repr(profile.follower_count)
)  # 59 <- You can still access other doc fields as attributes.

# Example 3:
from docbridge import Document, FallthroughField


class UserProfile(Document):
    id = Field(field_name="_id")  # id maps to the _id doc field.
    name = FallthroughField(
        field_names=[
            "full_name",  # v2
            "name",  # v1
        ]
    )
    # The `name` attribute will look up the "full_name" field,
    # and fall back to the "name" if it's missing.


profile = UserProfile({"full_name", "Mark Smith"})
assert profile.name == "Mark Smith"  # Works

profile = UserProfile({"name", "Mark Smith"})
assert profile.name == "Mark Smith"  # Also works!
