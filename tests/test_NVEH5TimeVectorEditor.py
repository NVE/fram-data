from framdata.file_editors.NVEH5TimeVectorEditor import NVEH5TimeVectorEditor


def test_set_metadata_by_key():
    editor = NVEH5TimeVectorEditor(source=None)

    editor.set_metadata_by_key("test_vector", "test_key", "test_value")

    expected = {"test_vector": {"test_key": "test_value"}}
    result = editor._metadata

    assert result == expected


def test_set_common_metadata_by_key():
    editor = NVEH5TimeVectorEditor(source=None)

    editor.set_common_metadata_by_key("test_key", "test_value")
    editor.set_common_metadata_by_key("k2", "v2")

    expected = {"test_key": "test_value", "k2": "v2"}
    result = editor._common_metadata

    assert result == expected
