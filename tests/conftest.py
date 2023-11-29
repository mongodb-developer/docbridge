import pytest
from pymongo import MongoClient
from os import environ


@pytest.fixture(scope="session")
def mongodb():
    mdb_client: MongoClient = MongoClient(environ["MDB_URI"])
    mdb_client.admin.command("ping")
    return mdb_client


@pytest.fixture
def transaction(mongodb):
    with mongodb.start_session() as session:
        session.start_transaction()
        try:
            yield session
        finally:
            session.abort_transaction()
