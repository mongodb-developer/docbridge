# Copyright 2023-present MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
docbridge - An experimental Object-Document Mapper library, primarily designed for teaching.
"""

from itertools import chain
from typing import Any, Sequence, Mapping, Iterable, Callable

__all__ = ["Document", "FallthroughField", "Field", "SequenceField"]

_SENTINEL = object()
NO_DEFAULT = object()


class DocumentMeta(type):
    def __new__(cls, name, bases, dict, strict=False, **kwds):
        result = super().__new__(cls, name, bases, dict, **kwds)
        result._strict = strict
        return result


class Document:
    """
    An object wrapper for a BSON document.

    This class is designed to be subclassed, so that different Fields can be
    configured for attribute lookup.
    """
    _doc = None
    _db = None
    _modified_fields = None

    def __init__(self, doc, db, strict=False):
        self._doc = doc
        self._db = db
        self._modified_fields = {}

    def __getattr__(self, attr):
        if attr == "_doc":
            return object.__getattribute__(self, attr)
        if not self._strict:
            return self._doc[attr]
        else:
            raise AttributeError(
                f"{self.__class__.__name__!r} object has no attribute {attr!r}"
            )

    def __setattr__(self, name: str, value: Any) -> None:
        if hasattr(self.__class__, name):
            super().__setattr__(name, value)
        elif not self._strict:
            self._doc[name] = value
            self._modified_fields[name] = value
        else:
            raise AttributeError(
                f"{self.__class__.__name__!r} cannot have instance attributes dynamically assigned."
            )

    def save(self, collection, match_criteria=None, session=None):
        if match_criteria is None:
            try:
                match_criteria = {"_id": self._doc["_id"]}
            except Exception:
                raise Exception(
                    "Attempt to update a document without _id, without providing `match_criteria`."
                )
        result = self._db.get_collection(collection).update_one(
            match_criteria, {"$set": self._modified_fields}, session=session
        )
        self._modified_fields = {}
        # TODO: Return something that details the update - error if no document updated?

    def __init_subclass__(cls, /, strict=False):
        cls._strict = strict


def identity(val):
    return val


class Field:
    """
    Field is designed to configure attribute lookup for a `Document` attribute.

    Currently it can be configured to map to a different field name in the
    underlying BSON document, and can apply an optional transformation to
    convert the field value to a desired type.
    """

    def __init__(self, field_name=None, default=NO_DEFAULT, transform=None):
        self.field_name = field_name
        self.transform = identity if transform is None else transform

    def __set_name__(self, owner, name):
        self.name = name
        if self.field_name is None:
            self.field_name = name

    def __get__(self, ob, cls):
        if ob is not None:
            try:
                return self.transform(ob._doc[self.field_name])
            except KeyError as ke:
                raise ValueError(
                    f"Attribute {self.name!r} is mapped to missing document property {self.field_name!r}."
                ) from ke

        return self

    def __set__(self, ob, value: Any) -> None:
        transformed_value = self.transform(value)
        ob._doc[self.field_name] = transformed_value
        print(f"Setting configured field {self.field_name} to {transformed_value}")
        ob._modified_fields[self.field_name] = transformed_value


class FallthroughField:
    """
    FallthroughField allows a series of different field names to be tried when looking up the attribute.
    The first field name that exists in the underlying document will be the value that is returned.

    This class's functionality will probably be rolled into `Field` instead of being its own class.
    """

    def __init__(self, field_names: Sequence[str]) -> None:
        self.field_names = field_names

    def __get__(self, ob, cls):
        for field_name in self.field_names:
            try:
                return ob._doc[field_name]
            except KeyError:
                pass
        else:
            raise ValueError(
                f"Attribute {self.name!r} references the field names {', '.join([repr(fn) for fn in self.field_names])} which are not present."
            )

    def __set_name__(self, owner, name):
        self.name = name


class SequenceField:
    """
    Allows an underlying array to have its elements wrapped in `Document` instances.
    """

    def __init__(
        self,
        type,
        field_name=None,
        superset_collection=None,
        superset_query: Callable = None,
    ):
        self._type = type
        self.field_name = field_name
        self.superset_collection = superset_collection
        self.superset_query = superset_query

    def __get__(self, ob, cls):
        if self.superset_query is None:
            # Use an empty sequence if there are no extra items.
            # It's still iterable, like a cursor, but immediately exits.
            superset = []
        else:
            # Call the superset_query callable to obtain the generated query:
            query = self.superset_query(ob)

            # If the query is a mapping, it's a `find` query, otherwise it's an
            # aggregation pipeline.
            if isinstance(query, Mapping):
                superset = ob._db.get_collection(self.superset_collection).find(query)
            elif isinstance(query, Iterable):
                superset = ob._db.get_collection(self.superset_collection).aggregate(
                    query
                )
            else:
                raise Exception("Returned was not a mapping or iterable.")

        try:
            # Return an iterable that first yields all the embedded items, and
            # then once that is exhausted, queries the database for more.
            return chain(
                [self._type(item, ob._db) for item in ob._doc[self.field_name]],
                (self._type(item, ob._db) for item in superset),
            )
        except KeyError as ke:
            raise ValueError(
                f"Attribute {self.name!r} is mapped to missing document property {self.field_name!r}."
            ) from ke

    def __set_name__(self, owner, name):
        self.name = name
        if self.field_name is None:
            self.field_name = name
