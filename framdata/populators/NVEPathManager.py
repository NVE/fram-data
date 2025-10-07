"""Contain the NVEPathManager class."""

import shutil
from pathlib import Path

from framcore import Base

from framdata.database_names.DatabaseNames import DatabaseNames as DbN


class NVEPathManager(Base):
    """
    Class to manage paths for the FRAM Energy Model data.

    Used to create a hierarchy of multiple FRAM datasets, where existing files are prioritized from a list of databases.
    The first database in the list has the highest priority.

    """

    def __init__(
        self,
        working_copy_path: Path | str,
        database_hierarchy: list[Path | str],
        file_id_request_list: list[str],
    ) -> None:
        """
        Initialize the NVEPathManager object and attributes.

        Args:
            working_copy_path (Path | str): Location to merge the databases in the hierarchy to.
            database_hierarchy (list[Path  |  str]): Ordered prioritization of databases. The first database in the list has highest priority.
            file_id_request_list (list[str]): All the files which should be retrieved from the hierarchy when merging it into working copy.

        """
        self._working_copy_path = Path(working_copy_path)
        self._database_hierarchy = database_hierarchy
        self._file_id_request_list = file_id_request_list
        self._db_hierarchy_map: dict[str, Path] = {}

    @classmethod
    def create_database_folder_structure(cls, destination_path: str | Path) -> None:
        """
        Create database folder structure as defined in DatabaseNames.

        Args:
            destination_path (str | Path): Where to create the new folder structure.

        """
        try:
            destination_path = Path(destination_path)
        except TypeError as e:
            message = "Argument destination_path must be a string or Path object."
            raise TypeError(message) from e

        for db_folder in DbN.db_folder_list:
            db_folder_path = destination_path / Path(db_folder)
            db_folder_path.mkdir(parents=True, exist_ok=True)

    def merge_database_hierarchy_to_working_copy(self) -> None:
        """
        Copy all defined files from the database hierarchy to the folder in self._working_copy_path.

        Raises:
            FileExistsError: Raised if something already exists in the working copy of the data.

        """
        self._working_copy_path.mkdir(parents=True, exist_ok=True)
        self._check_empty_folder(
            self._working_copy_path,
            "Working copy of database hierarchy already exists. Cannot edit the working copy.",
        )

        for file_id in self._file_id_request_list:
            absolute_part, relative_part, file_name = self._get_file_path_from_hierarchy(file_id)
            source = absolute_part / relative_part / file_name
            dst_folder = self._working_copy_path / relative_part
            dst_folder.mkdir(parents=True, exist_ok=True)
            dst_file_path = dst_folder / file_name

            if not dst_file_path.exists():
                self._db_hierarchy_map[file_id] = absolute_part
                shutil.copy(source, dst_file_path)

    def get_working_copy_path(self) -> Path:
        """
        Get the path to the working copy of the data in the database hierarchy.

        Returns:
            Path: Path to the working copy of the data in the database hierarchy.

        """
        return self._working_copy_path

    def _check_empty_folder(self, folder_path: Path, message: str) -> None:
        """
        Check if the working copy folder is empty.

        Args:
            folder_path (Path): Path to the folder to check.
            message (str): Error message to raise if the folder is not empty.

        Raises:
            FileExistsError: Raised if something already exists in the working copy of the data.

        """
        if any(folder_path.iterdir()):
            raise FileExistsError(message)

    def _get_file_path_from_hierarchy(self, file_id: str) -> tuple[Path, Path, Path]:
        """
        Retrieve the file path for a specific file within a designated database, considering sub-folders.

        Loops through database hierarchy and checks if file exist. Returns the first existing file path.

        Args:
            file_id (str): Identifier for the file to retrieve.

        Raises:
            FileNotFoundError: Raised when the file cannot be found in any accessible database.

        Returns:
            tuple[Path, Path, Path]: The three parts of the full file path. Absolute path to the database,
                                     relative folder within the database structure, and file name with file
                                     extention.

        """
        for path in self._database_hierarchy:
            absolute_part = Path(path)
            relative_part = DbN.get_relative_folder_path(file_id)
            file_name = DbN.get_file_name(absolute_part, relative_part, file_id)
            full_path = absolute_part / relative_part / file_name
            if full_path.exists():
                return absolute_part, relative_part, file_name

        message = f"File not found in any database. File id: {file_id}. File location in database structure: {relative_part / file_name}"
        raise FileNotFoundError(message)
