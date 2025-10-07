import re
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from framdata.database_names.DatabaseNames import DatabaseNames
from framdata.populators._DatabaseInterpreter import _DatabaseInterpreter


@pytest.fixture
def dbn_path() -> str:
    """
    Import path for DbN class to patch.

    Returns:
        str: path to DbN class

    """
    return "framdata.populators._DatabaseInterpreter.DbN"


@pytest.fixture
def tsmn_path() -> str:
    """
    Import path for TimeSeriesMetadataNames (TSMN) class to patch.

    Returns:
        str: path to TSMN class

    """
    return "framdata.DatabaseInterpreter.TSMN"


@pytest.fixture
def amn_path() -> str:
    """
    Import path for AttributeMetadataNames (AMN) class to patch.

    Returns:
        str: path to AMN class

    """
    return "framdata.DatabaseInterpreter.AMN"


@pytest.fixture
def example_metadata() -> pd.DataFrame:
    """
    Provide example metadata for testing.

    Returns:
        pd.DataFrame: example metadata

    """
    return pd.DataFrame(
        [
            ["AttrName1", "string", "File.Id.1", "kWh"],
            ["AttrName2", "string", None, None],
            ["AttrName3", None, None, None],
        ],
        columns=["attribute", "dtype", "reference", "unit"],
    )


def test_get_filepath(tmp_path: Path) -> None:
    """
    Test that the correct filepath is returned.

    Args:
        tmp_path (Path): temporary path

    """
    source = tmp_path / "working_copy"
    dbi = _DatabaseInterpreter(source)

    relative_folder = Path("db00")
    file_name = Path("test_file.xlsx")

    with (
        patch("framdata.populators._DatabaseInterpreter.DbN.get_relative_folder_path", return_value=relative_folder),
        patch("framdata.populators._DatabaseInterpreter.DbN.get_file_name", return_value=file_name),
    ):
        result = dbi.get_filepath("test_id")

    expected = source / relative_folder / file_name

    assert result == expected


@pytest.mark.skip(reason="Worksheet named 'Metadata' not found")
def test_read_attribute_table_with_excel(tmp_path: Path, dbn_path: str) -> None:
    """
    Test reading an attribute table from an Excel file.

    Args:
        tmp_path (Path): temporary path
        dbn_path (str): path to DbN class

    """
    source = tmp_path / "source"
    source.mkdir()
    dbi = _DatabaseInterpreter(source)

    file_id = "test_file"
    relative_folder = Path("db00")
    file_name = Path("test_file.xlsx")
    file_path = source / relative_folder / file_name

    data = pd.DataFrame({"col1": [1, 2], "col2": [3, np.nan]})
    file_path.parent.mkdir(parents=True, exist_ok=True)
    data.to_excel(file_path, index=False, sheet_name=DatabaseNames.data_sheet)
    expected = data.replace([np.nan], [None])

    with (
        patch(dbn_path + ".get_relative_folder_path", return_value=relative_folder),
        patch(dbn_path + ".get_file_name", return_value=file_name),
    ):
        result = dbi.read_attribute_table(file_id)

    pd.testing.assert_frame_equal(result, expected)


def test_read_attribute_table_unsupported_filetype(tmp_path: Path) -> None:
    """
    Test that an error is raised when trying to read an unsupported filetype.

    Args:
        tmp_path (Path): temporary path

    """
    mock_path = tmp_path / "not_xlsx_file.txt"
    dbi = _DatabaseInterpreter(mock_path)

    with (
        patch.object(dbi, "get_filepath", return_value=mock_path),
        pytest.raises(
            NotImplementedError,
            match=re.escape(f"Database attribute files only supports {dbi._supported_attribute_filetypes} filetypes."),
        ),
    ):
        dbi.read_attribute_table("test_id")
