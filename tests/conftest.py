import pytest
import pymongo
import os


@pytest.fixture(scope="session")
def mongodb():
    client = pymongo.MongoClient(os.environ["MDB_URI"])
    # TODO: Do something if the value is wrong
    client.admin.command("ping")["ok"] > 0.0
    return client


@pytest.fixture
def rollback_session(mongodb):
    session = mongodb.start_session()
    session.start_transaction()
    try:
        yield session
    finally:
        session.abort_transaction()
