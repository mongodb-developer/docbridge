from typing import List, Sequence

__all__ = ["Document", "Fallthrough"]

_SENTINEL = object()
NO_DEFAULT = object()


class Document:
    def __init__(self, doc, *, strict=False):
        self._doc = doc
        self._strict = strict

    def __getattr__(self, attr):
        if not self._strict:
            return getattr(self._doc, attr)


def identity(val):
    return val


class Simple:
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


class Fallthrough:
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
