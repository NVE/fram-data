import re
from unittest.mock import MagicMock, call, patch

import numpy as np
import pytest

from framdata.database_names._base_names import _BaseComponentsNames


@pytest.mark.parametrize(("test_input", "expected"), [(None, None), (1, 1.0), (1.0, 1.0), ("string", "string")])
def test_parse_float_or_str(test_input: float | int | str | None, expected: float | int | str | None) -> None:
    assert _BaseComponentsNames._parse_float_or_str(test_input) == expected


def test_get_sub_component():
    class TestParent:
        def __init__(self) -> None:
            pass

    class TestChild:
        def __init__(self) -> None:
            pass

    parent_id = "p_id"
    child_id = "sc_id"
    meta = {"meta_key": "meta"}
    expected = (TestChild(), meta)
    attributes = {child_id: expected}

    result = _BaseComponentsNames._get_attribute_object(
        attribute_objects=attributes,
        attribute_id=child_id,
        parent_id=parent_id,
        parent_class=TestParent,
        expected_class=TestChild,
    )

    assert isinstance(result, tuple)
    assert result[0] == expected[0]
    assert result[1] == expected[1]


def test_get_sub_component_key_not_in_dict():
    class TestParent:
        def __init__(self) -> None:
            pass

    class TestChild:
        def __init__(self) -> None:
            pass

    parent_id = "p_id"
    child_id = "sc_id"
    sub_components = {}

    expected_message = (
        f"{TestParent} with ID {parent_id} refers to an attribute object of type {TestChild} with id "
        f"{child_id}. The attribute was not found in the available data. Please make sure all attribute "
        "objects are populated before their parent components."
    )
    with pytest.raises(KeyError, match=re.escape(expected_message)):
        __ = _BaseComponentsNames._get_attribute_object(
            attribute_objects=sub_components,
            attribute_id=child_id,
            parent_id=parent_id,
            parent_class=TestParent,
            expected_class=TestChild,
        )


def test_get_sub_component_wrong_class_in_dict():
    class TestParent:
        def __init__(self) -> None:
            pass

    class TestChild:
        def __init__(self) -> None:
            pass

    parent_id = "p_id"
    child_id = "sc_id"
    wrong_class = list()
    meta = {"meta_key": "meta"}
    sub_components = {child_id: (wrong_class, meta)}

    expected_message = f"{TestParent} with ID {parent_id} expected class {TestChild} for attribute with id {child_id}. Got {type(wrong_class)}."
    with pytest.raises(ValueError, match=re.escape(expected_message)):
        __ = _BaseComponentsNames._get_attribute_object(
            attribute_objects=sub_components,
            attribute_id=child_id,
            parent_id=parent_id,
            parent_class=TestParent,
            expected_class=TestChild,
        )


def test_get_references() -> None:
    row = np.array([1, 2, "ref1", None, "ref2"], dtype=object)
    indices = {
        "c1": 0,
        "c2": 1,
        "c3": 2,
        "c4": 3,
        "c5": 4,
    }
    ref_columns = ["c2", "c3", "c4", "c5"]

    expected = {"ref1", "ref2"}
    result = _BaseComponentsNames.get_references(row, indices, ref_columns)  # noqa: SLF001
    assert result == expected


def test_merge_attribute_meta() -> None:
    class TestParent:
        def __init__(self) -> None:
            self._meta = {"k1": "m1"}

        def get_meta(self, key: str) -> None:
            return self._meta[key]

        def add_meta(self, key: str, value: str) -> None:
            self._meta[key] = value

        def get_meta_keys(self) -> set[str]:
            return set(self._meta.keys())

    parent = TestParent()
    attr_meta = {"attr1": {"k1": "m1", "k2": "m2", "k3": "m3"}, "attr2": {"k2": "m2", "k4": "m4"}}
    _BaseComponentsNames._merge_attribute_meta("testparent", parent, attr_meta)  # noqa: SLF001

    result = parent._meta
    expected = {"k1": "m1", "k2": "m2", "k3": "m3", "k4": "m4"}
    assert result == expected


def test_merge_attribute_meta_conflicts() -> None:
    class TestParent:
        def __init__(self) -> None:
            self._meta = {"k1": "m1"}

        def get_meta(self, key: str) -> None:
            return self._meta[key]

        def add_meta(self, key: str, value: str) -> None:
            self._meta[key] = value

        def get_meta_keys(self) -> set[str]:
            return set(self._meta.keys())

    parent_id = "testparent"
    parent = TestParent()
    attr_meta = {"attr1": {"k1": "m2", "k2": "m2", "k3": "m3"}, "attr2": {"k2": "m3", "k4": "m4"}}

    with pytest.raises(RuntimeError) as cm:
        _BaseComponentsNames._merge_attribute_meta(parent_id, parent, attr_meta)  # noqa: SLF001

    message = str(cm.value)
    assert message.startswith(f"Found errors with metadata connected to attributes of component {parent} with ID {parent_id}:\n")
    assert "Conflicting metadata in attr1 and attribute attr2: metadata key k2 exists in both with different values. Values: m2 and m3\n" in message
    assert f"Conflicting metadata in {parent_id} and attribute attr1: metadata key k1 exists in both with different values. Values: m1 and m2" in message
