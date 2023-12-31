import pytest
import pymongo
import os


@pytest.fixture(scope="session")
def mongodb():
    client = pymongo.MongoClient(os.environ["MDB_URI"])
    client.admin.command("ping")
    return client


@pytest.fixture
def rollback_session(mongodb):
    session = mongodb.start_session()
    session.start_transaction()
    try:
        yield session
    finally:
        session.abort_transaction()
