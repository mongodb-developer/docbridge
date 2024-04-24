import os
import sys

import docbridge
import pymongo

mdb_uri = os.environ["MDB_URI"]


class Follower(docbridge.Document):
    pass


class Profile(docbridge.Document):
    id = docbridge.Field(field_name="user_id", transform=int)
    followers = docbridge.SequenceField(
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


def main(argv=sys.argv[1:]):
    client = pymongo.MongoClient(mdb_uri)
    db = client.get_database("why")
    profiles = db.get_collection("profiles")

    if db.command("ping")["ok"] < 0.5:
        raise Exception("Problem connected to database cluster.")

    profile = Profile(profiles.find_one({"user_id": "4"}), db)
    print(profile.id)
    print(type(profile.id))
    for index, follower in enumerate(profile.followers):
        # print(f"{index}: {follower['user_name']}")
        print(f"{index}: {follower.user_name}")


if __name__ == "__main__":
    main()
