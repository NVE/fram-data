"""Contain class for getting file paths and reading attribute files in database."""

from pathlib import Path

import numpy as np
import pandas as pd
from framcore import Base

from framdata.database_names.DatabaseNames import DatabaseNames as DbN


class _DatabaseInterpreter(Base):
    """Class containing functions for interacting with DatabaseNames methods."""

    def __init__(self, source: Path | str) -> None:
        """
        Initialize DatabaseInterpreter object connected to the source database.

        Args:
            source (Path | str): Path to the database.

        """
        self._source = Path(source)
        self._supported_attribute_filetypes = [DbN.ext_excel]

    def get_source_and_relative_loc(self, file_id: str) -> tuple[Path, Path | None]:
        """
        Retrieve the source path to the database and the relative path to the file.

        The relative path is retrieved from DatabaseNames. The two parts of the filepath are returned separately.

        Args:
            file_id (str): DatabaseNames' ID of the file to retrieve location of.

        Returns:
            tuple[Path, Path]: Tuple with the absolute source path first, then the relative file location in the
                               database.

        """
        db_folder = DbN.get_relative_folder_path(file_id)
        file_name = DbN.get_file_name(self._source, db_folder, file_id)

        return (self._source, None) if file_name is None else (self._source, db_folder / file_name)

    def read_attribute_table(self, file_id: str) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Read an attribute table to pandas dataframe based on its DatabaseNames ID.

        Args:
            file_id (str): DatabaseNames' ID of the file to retrieve location of.

        Raises:
            NotImplementedError: If the file type is not supported by DatabaseInterpreter.

        Returns:
            tuple[Union[pd.DataFrame, str], Union[pd.DataFrame, dict]]: Dataframes of the attribute table and it's
                                                                        metadata, respectively.

        """
        self.send_info_event(f"reading table {file_id}")
        path = self.get_filepath(file_id)
        if path.suffix == DbN.ext_excel:  # Assume table is small enough to be read at once
            return (
                pd.read_excel(
                    path,
                    sheet_name=DbN.data_sheet,
                    dtype=None,  # Important to not infer types, we use types for later checks
                    na_values=[""],
                ).replace([np.nan], [None]),
                pd.read_excel(path, sheet_name=DbN.metadata_sheet, na_values=[""]).replace([np.nan], [None]),
            )
        message = f"Database attribute files only supports {self._supported_attribute_filetypes} filetypes. Tried to read {path}."
        raise NotImplementedError(message)

    def get_filepath(self, file_id: str) -> Path:
        """
        Retrieve absolute file path by the file's ID in DatabaseNames.

        The absolute path of source is combined with the relative part from DatabaseNames into one path.

        Args:
            file_id (str): DatabaseNames' ID of the file to retrieve location of.

        Returns:
            Path: Absolute path to the file.

        """
        db_folder = DbN.get_relative_folder_path(file_id)
        file_name = DbN.get_file_name(self._source, db_folder, file_id)

        return self._source / db_folder / file_name
