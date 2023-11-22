from pytest import fail

from docbridge import *


def test_fallthrough():
    class FallthroughClass(Document):
        a = Fallthrough(["a", "b"])

    myc = FallthroughClass({"a": "the_a_value"})
    assert myc.a == "the_a_value"

    myc = FallthroughClass({"a": None})
    assert myc.a == None

    myc = FallthroughClass({"a": "the_a_value", "b": "the_b_value"})
    assert myc.a == "the_a_value"

    myc = FallthroughClass({"b": "the_b_value"})
    assert myc.a == "the_b_value"

    try:
        myc = FallthroughClass({"c": "not_in_the_cascade"})
        assert myc.a == "should not be evaluated"
        fail()
    except ValueError as v:
        assert (
            str(v)
            == """Attribute 'a' references the field names 'a', 'b' which are not present."""
        )
