import asyncio
import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path


class RuntimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("MDB_URI", "mongodb://example/test")

        fastapi = types.ModuleType("fastapi")

        class FastAPI:
            def __init__(self, *args, **kwargs):
                self.routes = []

            def get(self, path, **kwargs):
                def wrap(fn):
                    self.routes.append(types.SimpleNamespace(path=path, endpoint=fn))
                    return fn

                return wrap

        fastapi.FastAPI = FastAPI
        sys.modules["fastapi"] = fastapi

        beanie = types.ModuleType("beanie")
        class Document:
            pass
        beanie.Document = Document
        async def init_beanie(*args, **kwargs):
            return None
        beanie.init_beanie = init_beanie
        sys.modules["beanie"] = beanie

        pydantic = types.ModuleType("pydantic")
        class BaseModel:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        pydantic.BaseModel = BaseModel
        pydantic.Field = lambda default=None, **kw: default
        sys.modules["pydantic"] = pydantic

        pymongo = types.ModuleType("pymongo")
        class AsyncMongoClient:
            def __init__(self, *a, **kw): pass
            def __getitem__(self, name): return {}
            def get_database(self, name=None): return {}
        pymongo.AsyncMongoClient = AsyncMongoClient
        sys.modules["pymongo"] = pymongo

        target = Path(__file__).resolve().parents[1] / "examples" / "why" / "why" / "__init__.py"
        spec = importlib.util.spec_from_file_location("docbridge_why", target)
        cls.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.mod)

    def test_read_item_calls_profile_query(self):
        class FakeProfile:
            @staticmethod
            async def find_one(query):
                return {"user_id": query["user_id"]}

        self.mod.Profile = FakeProfile
        result = asyncio.run(self.mod.read_item("u1"))
        self.assertEqual(result["user_id"], "u1")


if __name__ == "__main__":
    unittest.main()
