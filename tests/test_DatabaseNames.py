import re
from pathlib import Path
from unittest.mock import patch

import pytest

from framdata.database_names.DatabaseNames import DatabaseNames


@pytest.fixture
def databasenames_path() -> str:
    """
    Import path for DatabaseNames class to patch.

    Returns:
       str: path to be patched

    """
    return "framdata.database_names.DatabaseNames.DatabaseNames."


def test_get_relative_folder_path(databasenames_path: str) -> None:
    """
    Check that the relative folder path is returned.

    Args:
        databasenames_path (str): path to be patched

    """
    file_id = "test_id"
    expected = "db00"
    mocked_db_folder_map = {
        file_id: expected,
    }

    with patch(f"{databasenames_path}db_folder_map", mocked_db_folder_map):
        result = DatabaseNames.get_relative_folder_path(file_id)

    assert result == Path(expected)


def test_get_relative_folder_path_not_found(databasenames_path: str) -> None:
    """
    Check that KeyError is raised if the file_id is not found.

    Args:
        databasenames_path (str): path to be patched

    """
    file_id = "test_id"
    mocked_db_folder_map = {
        "another_id": ["db00", ".txt"],
    }

    with (
        patch(f"{databasenames_path}db_folder_map", mocked_db_folder_map),
        pytest.raises(KeyError, match=f"File id '{file_id}' not found in database folder map."),
    ):
        DatabaseNames.get_relative_folder_path(file_id)


def test_get_file_name(tmp_path: Path) -> None:
    """Check that the filename is returned."""
    db_folder = "test_db"
    file_id = "test_id"
    expected = f"{file_id}.txt"

    folder_path = tmp_path / db_folder
    folder_path.mkdir()
    with (folder_path / expected).open(mode="w") as f:
        f.write("test")

    result = DatabaseNames.get_file_name(tmp_path, db_folder, file_id)

    assert result == expected


def test_get_file_name_folder_not_found(tmp_path: Path) -> None:
    """Check that FileNotFoundError is raised if the file_id is not found."""
    db_folder = "test_db"
    file_id = "test_id"

    folder_path = tmp_path / db_folder

    with pytest.raises(FileNotFoundError, match=re.escape(f"The database folder {folder_path} does not exist.")):
        __ = DatabaseNames.get_file_name(tmp_path, db_folder, file_id)


def test_get_file_name_file_not_found(tmp_path: Path) -> None:
    """Check that FileNotFoundError is raised if the file_id is not found."""
    db_folder = "test_db"
    file_id = "test_id"

    folder_path = tmp_path / db_folder
    folder_path.mkdir()

    expected = DatabaseNames.get_file_name(tmp_path, db_folder, file_id)
    assert expected is None


def test_get_file_name_multiple_files(tmp_path: Path) -> None:
    """Check that exception is raised when multiple files with same name are present."""
    db_folder = "test_db"
    file_id = "test_id"
    txt_ext = f"{file_id}.txt"
    text_ext = f"{file_id}.text"

    folder_path = tmp_path / db_folder
    folder_path.mkdir()
    with (folder_path / txt_ext).open(mode="w") as f:
        f.write("test txt")

    with (folder_path / text_ext).open(mode="w") as f:
        f.write("test text")

    with pytest.raises(RuntimeError) as cm:
        __ = DatabaseNames.get_file_name(tmp_path, db_folder, file_id)

    message = str(cm.value)
    assert message.startswith(f"Found multiple files with ID {file_id} (with different extensions: ")
    assert "'.text'" in message
    assert "'.txt'" in message
    assert message.endswith(f" in database folder {folder_path}. File names must be unique.")
