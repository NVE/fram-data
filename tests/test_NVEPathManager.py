import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from framdata.populators.NVEPathManager import NVEPathManager


def create_tmp_file(db_folder: Path, subfolder_name: Path, file_name: Path) -> None:
    """
    Create a temporary file in a specified folder structure.

    Args:
        db_folder (Path): temporary path to database folder, e.g. tmp_path / "master_db"
        subfolder_name (Path): name of subfolder, e.g. "db00_test"
        file_name (Path): name of file, e.g. "test_file1.xlsx"

    """
    folder_path = db_folder / subfolder_name
    folder_path.mkdir(parents=True)
    with Path.open(folder_path / file_name, "w") as f:
        f.write("")


def test_create_database_folder_structure(tmp_path: Path) -> None:
    """
    Check that the database folder structure is created with mocked db_folder_list.

    Args:
        tmp_path (Path): temporary path

    """
    mocked_db_folder_list = ["mocked_db00", "mocked_db01", "mocked_db02"]
    destination_path = tmp_path / "database"

    with patch("framdata.populators.NVEPathManager.DbN.db_folder_list", mocked_db_folder_list):
        NVEPathManager.create_database_folder_structure(destination_path)

    for folder in mocked_db_folder_list:
        assert (destination_path / folder).exists()


def test_create_database_folder_structure_require_str_or_path() -> None:
    """Check that the destination_path is a string or Path object."""
    destination_path = 1

    with (  # noqa: PT012
        patch("framdata.populators.NVEPathManager.Base.send_error_event") as mock_send_error_event,
        pytest.raises(TypeError, match="Argument destination_path must be a string or Path object."),
    ):
        NVEPathManager.create_database_folder_structure(destination_path)
        assert mock_send_error_event.call_count == 1


def test_merge_database_hierarchy_to_working_copy(tmp_path: Path) -> None:
    """
    Check that the working copy folder is created with correct structure and files.

    Args:
        tmp_path (Path): temporary path

    """
    working_copy_path = tmp_path / "working_copy"
    master_db_folder = tmp_path / "master_db"
    db_hierarchy = [master_db_folder]
    file_id_request_list = ["test_file1", "test_file2"]

    subfolder_1 = Path("db01_test")
    subfolder_2 = Path("db02_test")
    filename_1 = Path("test_file1.xlsx")
    filename_2 = Path("test_file2.xlsx")

    create_tmp_file(master_db_folder, subfolder_1, filename_1)
    create_tmp_file(master_db_folder, subfolder_2, filename_2)

    nve_path_manager = NVEPathManager(working_copy_path, db_hierarchy, file_id_request_list)

    side_effect_values = [
        (master_db_folder, subfolder_1, filename_1),
        (master_db_folder, subfolder_2, filename_2),
    ]
    with patch.object(nve_path_manager, "_get_file_path_from_hierarchy", side_effect=side_effect_values):
        nve_path_manager.merge_database_hierarchy_to_working_copy()

    assert (working_copy_path / subfolder_1 / filename_1).exists()
    assert (working_copy_path / subfolder_2 / filename_2).exists()


def test_merge_database_hierarchy_to_working_copy_skip_existing_copy(tmp_path: Path) -> None:
    """
    Check that the working copy filepath is not overwritten if it already exists.

    Args:
        tmp_path (Path): temporary path

    """
    working_copy_path = tmp_path / "working_copy"
    master_db_folder = tmp_path / "master_db"
    db_hierarchy = [master_db_folder]
    file_id_request_list = ["test_file1", "test_file1"]

    subfolder_1 = Path("db01_test")
    filename_1 = Path("test_file1.xlsx")

    create_tmp_file(master_db_folder, subfolder_1, filename_1)

    nve_path_manager = NVEPathManager(working_copy_path, db_hierarchy, file_id_request_list)

    side_effect_values = [
        (master_db_folder, subfolder_1, filename_1),
        (master_db_folder, subfolder_1, filename_1),
    ]

    with (
        patch.object(nve_path_manager, "_get_file_path_from_hierarchy", side_effect=side_effect_values),
        patch("shutil.copy", side_effect=shutil.copy) as mock_copy,
    ):
        nve_path_manager.merge_database_hierarchy_to_working_copy()

    assert mock_copy.call_count == 1


def test_merge_database_hierarchy_to_working_copy_require_existing_working_copy(tmp_path: Path) -> None:
    """
    Check that the working copy folder exists.

    Args:
        tmp_path (Path): temporary path

    """
    working_copy_path = tmp_path / "working_copy"
    db_hierarchy = []
    file_id_request_list = []
    nve_path_manager = NVEPathManager(working_copy_path, db_hierarchy, file_id_request_list)

    nve_path_manager.merge_database_hierarchy_to_working_copy()
    assert working_copy_path.exists()


def test_merge_database_hierarchy_to_working_copy_require_empty_working_copy(tmp_path: Path) -> None:
    """
    Raise Error if working copy folder is not empty.

    Args:
        tmp_path (Path): temporary path

    """
    working_copy_dir = tmp_path / "working_copy/db00"
    working_copy_dir.mkdir(parents=True)
    working_copy_path = tmp_path / "working_copy"
    db_hierarchy = []
    file_id_request_list = []
    nve_path_manager = NVEPathManager(working_copy_path, db_hierarchy, file_id_request_list)

    match_msg = "Working copy of database hierarchy already exists. Cannot edit the working copy."
    with (  # noqa: PT012
        patch("framdata.populators.NVEPathManager.Base.send_error_event") as mock_send_error_event,
        pytest.raises(FileExistsError, match=match_msg),
    ):
        nve_path_manager.merge_database_hierarchy_to_working_copy()
        assert mock_send_error_event.call_count == 1


def test_merge_database_hierarchy_to_working_copy_cache_db_path(tmp_path: Path) -> None:
    """
    Check that the database path for a given file_id is cached in self._db_hierarcy_map.

    Args:
        tmp_path (Path): temporary path

    """
    working_copy_path = tmp_path / "working_copy"
    master_db_folder = tmp_path / "master_db"
    db_hierarchy = [master_db_folder]
    file_id_request_list = ["test_file1"]
    subfolder_1 = Path("db01_test")
    filename_1 = Path("test_file1.xlsx")

    create_tmp_file(master_db_folder, subfolder_1, filename_1)

    nve_path_manager = NVEPathManager(working_copy_path, db_hierarchy, file_id_request_list)

    with patch.object(nve_path_manager, "_get_file_path_from_hierarchy", return_value=(master_db_folder, subfolder_1, filename_1)):
        nve_path_manager.merge_database_hierarchy_to_working_copy()
        result = nve_path_manager._db_hierarchy_map
    expected = {"test_file1": master_db_folder}
    assert result == expected


def test_get_working_copy_path() -> None:
    """Check that the working copy path is returned."""
    working_copy_path = "working_copy"
    db_hierarchy = []
    file_id_request_list = []
    nve_path_manager = NVEPathManager(working_copy_path, db_hierarchy, file_id_request_list)

    assert nve_path_manager.get_working_copy_path() == Path(working_copy_path)


def test_get_filepath_from_hierarchy(tmp_path: Path) -> None:
    """
    Check that the filepath is returned from the hierarchy.

    Args:
        tmp_path (Path): temporary path

    """
    file_id = "test_file"
    file_name = Path(f"{file_id}.xlsx")
    subfolder_name = Path("db00_test")

    master_db_folder = tmp_path / "master_db"
    project_db_folder = tmp_path / "project_db"

    db_hierarchy = [project_db_folder, master_db_folder]
    working_copy_path = ""
    file_id_request_list = []

    create_tmp_file(master_db_folder, subfolder_name, file_name)
    create_tmp_file(project_db_folder, subfolder_name, file_name)

    nve_path_manager = NVEPathManager(working_copy_path, db_hierarchy, file_id_request_list)

    with (
        patch("framdata.populators.NVEPathManager.DbN.get_relative_folder_path", return_value=subfolder_name),
        patch("framdata.populators.NVEPathManager.DbN.get_file_name", return_value=file_name),
    ):
        result = nve_path_manager._get_file_path_from_hierarchy(file_id)

    expected_result = (db_hierarchy[0], subfolder_name, file_name)
    assert result == expected_result


def test_get_filepath_from_hierarchy_require_existing_file(tmp_path: Path) -> None:
    """
    Raise Error if file does not exist in the hierarchy.

    Args:
        tmp_path (Path): temporary path

    """
    file_id = "test_file"
    file_name = Path(f"{file_id}.xlsx")
    subfolder_name = Path("db00_test")

    master_db_folder = tmp_path / "master_db"

    db_hierarchy = [master_db_folder]
    working_copy_path = ""
    file_id_request_list = []

    nve_path_manager = NVEPathManager(working_copy_path, db_hierarchy, file_id_request_list)

    with (
        patch("framdata.populators.NVEPathManager.DbN.get_relative_folder_path", return_value=subfolder_name),
        patch("framdata.populators.NVEPathManager.DbN.get_file_name", return_value=file_name),
        pytest.raises(FileNotFoundError),
    ):
        nve_path_manager._get_file_path_from_hierarchy(file_id)
