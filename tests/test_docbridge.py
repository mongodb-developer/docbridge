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
