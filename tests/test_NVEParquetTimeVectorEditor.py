from framdata.file_editors.NVEParquetTimeVectorEditor import NVEParquetTimeVectorEditor


def test_set_metadata_by_key():
    editor = NVEParquetTimeVectorEditor(source=None)

    editor.set_metadata_by_key("test_key", "test_value")
    editor.set_metadata_by_key("k2", "v2")

    expected = {"test_key": "test_value", "k2": "v2"}
    result = editor._metadata

    assert result == expected
