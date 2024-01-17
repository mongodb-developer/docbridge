import os
from docbridge import Document, Field, FallthroughField
from pymongo import MongoClient

collection = (
    MongoClient(os.environ["MDB_URI"])
    .get_database("docbridge_test")
    .get_collection("people")
)

collection.delete_many({})  # Clean up any leftover documents.
# Insert a couple of sample documents:
collection.insert_many(
    [
        {
            "name": "Mark Smith",
            "schema_version": 1,
        },
        {
            "full_name": "Mark Smith",
            "first_name": "Mark",
            "last_name": "Smith",
            "schema_version": 2,
        },
    ]
)


# Define a mapping for "person" documents:
class Person(Document):
    version = Field("schema_version")
    name = FallthroughField(
        [
            "name",  # v1
            "full_name",  # v2
        ]
    )


# This finds all the documents in the collection, but wraps each BSON document with a Person wrapper:
people = (Person(doc, None) for doc in collection.find())
for person in people:
    print(
        "Name:",
        person.name,
    )  # The name (or full_name) of the underlying document.
    print(
        "Document version:",
        person.version,  # The schema_version field of the underlying document.
    )


session = mongodb.start_session()
session.start_transaction()
try:
    my_collection.insert_one(
        {"this document": "will be erased"},
        session=session,
    )
finally:
    session.abort_transaction()
