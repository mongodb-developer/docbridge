import os
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient as MotorClient


# @pytest.fixture(scope="session")
# def mongodb():
#     """
#     This fixture provides a pymongo client for test purposes.
#     """
#     client = pymongo.MongoClient(os.environ["MDB_URI"])
#     # TODO: Do something if the value is wrong
#     assert client.admin.command("ping")["ok"] > 0.5
#     return client


@pytest_asyncio.fixture(scope="session")
async def motor():
    client = MotorClient(os.environ["MDB_URI"])
    result = await client.admin.command("ping")
    assert result["ok"] > 0.5

    return client


@pytest_asyncio.fixture(scope="session")
async def rollback_session(motor: MotorClient):
    """
    This fixture provides a session that will be aborted at the end of the test, to clean up any written data.
    """
    session = await motor.start_session()
    session.start_transaction()
    try:
        yield session
    finally:
        await session.abort_transaction()
