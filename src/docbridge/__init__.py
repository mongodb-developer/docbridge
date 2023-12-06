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

from typing import List, Sequence

__all__ = ["Document", "FallthroughField", "Field", "SequenceField"]

_SENTINEL = object()
NO_DEFAULT = object()


class Document:
    def __init__(self, doc, db, strict=False):
        self._doc = doc
        self._db = db
        self._strict = strict

    def __getattr__(self, attr):
        if not self._strict:
            return self._doc[attr]


def identity(val):
    return val


class Field:
    def __init__(self, field_name=None, default=NO_DEFAULT, transform=None):
        self.field_name = None
        self.transform = identity if transform is None else transform

    def __set_name__(self, owner, name):
        self.name = name
        if self.field_name is None:
            self.field_name = name

    def __get__(self, ob, cls):
        try:
            return self.transform(ob._doc[self.field_name])
        except KeyError as ke:
            raise ValueError(
                f"Attribute {self.name!r} is mapped to missing document property {self.field_name!r}."
            ) from ke


class FallthroughField:
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
        print(f"Name set to {name}")
        self.name = name


class SequenceField:
    def __init__(self, type, field_name=None):
        self._type = type
        self.field_name = field_name

    def __get__(self, ob, cls):
        try:
            print("Transforming items:", ob._doc[self.field_name])
            return [self._type(item, ob._db) for item in ob._doc[self.field_name]]
        except KeyError as ke:
            raise ValueError(
                f"Attribute {self.name!r} is mapped to missing document property {self.field_name!r}."
            ) from ke

    def __set_name__(self, owner, name):
        self.name = name
        if self.field_name is None:
            self.field_name = name
