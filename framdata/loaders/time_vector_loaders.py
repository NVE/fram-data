"""
Contain classes for reading time vector data from various file types with formats specific to NVE.

This module provides:
    - NVEExcelTimeVectorLoader: Handle time vectors in excel files.
    - NVEH5TimeVectorLoader: Handle time vectors in HDF5 files.
    - NVEYamlTimeVectorLoader: Handle time vectors in Yaml files.
    - NVEParquetTieVectorLoader: Handle time vectors in Parquet files.

"""

from datetime import date, datetime, timedelta, tzinfo
from pathlib import Path
from typing import ClassVar

import h5py
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import yaml
from framcore.timeindexes import ConstantTimeIndex, FixedFrequencyTimeIndex, ListTimeIndex, TimeIndex
from numpy.typing import NDArray

from framdata.database_names.H5Names import H5Names
from framdata.database_names.TimeVectorMetadataNames import TimeVectorMetadataNames as TvMn
from framdata.database_names.YamlNames import YamlNames
from framdata.loaders.NVETimeVectorLoader import NVETimeVectorLoader


class NVEExcelTimeVectorLoader(NVETimeVectorLoader):
    """
    Class for loading time vector data from NVE excel file sources.

    Meant for short time vectors (e.g. yearly volumes or installed capacities) which are desireable to view and edit easily through Excel.
    Supports the followinf formats:
        - 'Horizontal': One column containing IDs, the other column names represents the index. Vector values as rows
        - 'Vertical': One column as index (DateTime), the oher columns names are vector IDs. Vectors as column values.

    """

    _SUPPORTED_SUFFIXES: ClassVar[list] = [".xlsx"]
    _DATA_SHEET = "Data"
    _METADATA_SHEET = "Metadata"

    def __init__(self, source: Path | str, require_whole_years: bool, relative_loc: Path | str | None = None, validate: bool = True) -> None:
        """
        Intitialize loader instance and connect it to an Excel file containing time vector data.

        Args:
            source (Path | str): Absolute Path to database or excel file.
            require_whole_years (bool): Flag for validating that the time vectors in the source contain data for complete years.
            relative_loc (Path | str | None, optional): Path to excel file relative to source. Defaults to None.
            validate (bool, optional): Flag to turn on validation of timevectors. NB! Loads all data into memory at once. Defaults to True.

        """
        super().__init__(source, require_whole_years, relative_loc)
        self._index: TimeIndex = None

        if validate:
            self.validate_vectors()

    def get_unit(self, vector_id: str) -> str:
        """
        Get the unit of the given time vector.

        Args:
            vector_id (str): ID of a time vector. Not used since all time vectors in the NVE excel files have the same
                             unit.

        Returns:
            str: Unit of the time vector.

        """
        return self.get_metadata("")[TvMn.UNIT]

    def get_values(self, vector_id: str) -> NDArray:
        """
        Get numpy array with all the values of a given vector in the Loader's excel file.

        Args:
            vector_id (str): Unique id of the vector in the file.

        Returns:
            NDArray: Numpy array with values.

        """
        if self._data is None:
            self._data = pd.DataFrame()
        if vector_id not in self._data.columns:
            is_horizontal = self._is_horizontal_format()
            column_filter = [vector_id]
            usecols = None
            if not is_horizontal:
                usecols = column_filter

            values_df = pd.read_excel(self.get_source(), sheet_name=self._DATA_SHEET, usecols=usecols)

            if is_horizontal:  # Convert the table to large time series format
                values_df = self._process_horizontal_format(values_df)
                values_df = self._enforce_dtypes(values_df, is_horizontal)
                self._data = values_df
            else:
                values_df = self._enforce_dtypes(values_df, is_horizontal)
                self._data[vector_id] = values_df
        return self._data[vector_id].to_numpy()

    def get_index(self, vector_id: str) -> ListTimeIndex:
        """
        Get the TimeIndex describing the time dimension of the vectors in the file.

        Args:
            vector_id (str): Not used since all vectors in the NVE excel files have the same index.

        Returns:
            TimeIndex: TimeIndex object describing the excel file's index.

        """
        meta = self.get_metadata("")
        if self._index is None:
            self._index = self._create_index(
                self.get_values(TvMn.DATETIME_COL),
                is_52_week_years=meta[TvMn.IS_52_WEEK_YEARS],
                extrapolate_first_point=meta[TvMn.EXTRAPOLATE_FISRT_POINT],
                extrapolate_last_point=meta[TvMn.EXTRAPOLATE_LAST_POINT],
            )
        return self._index

    def get_metadata(self, vector_id: str) -> dict[str, bool | int | str | datetime | timedelta | tzinfo | None]:
        """
        Read Excel file metadata.

        Args:
            vector_id (str): Not used.

        Raises:
            KeyError: If an expected metadata key is missing.

        Returns:
            dict[str, bool|int|str|datetime|timedelta|tzinfo|None]: Metadata dictionary.

        """
        if self._meta is None:
            path = self.get_source()
            raw_meta = pd.read_excel(path, sheet_name=self._METADATA_SHEET, na_values=[""]).replace([np.nan], [None]).to_dict("records")[0]

            self._meta = self._process_meta(raw_meta)
        return self._meta

    def _enforce_dtypes(self, values_df: pd.DataFrame | pd.Series, issmallformat: bool) -> pd.DataFrame:
        set_dtypes = "float"
        if isinstance(values_df, pd.DataFrame):
            set_dtypes = {c: "float" for c in values_df.columns if c != TvMn.DATETIME_COL}

        # ensure correct dtypes
        try:
            return values_df.astype(set_dtypes)
        except ValueError as e:
            index_column = TvMn.ID_COLUMN_NAME if issmallformat else TvMn.DATETIME_COL
            message = f"Error in {self} while reading file. All columns except '{index_column}' must consist of only float or integer numbers."
            raise RuntimeError(message) from e

    def _process_horizontal_format(self, horizontal_format_df: pd.DataFrame) -> pd.DataFrame:
        # We have to read the whole file to find the correct series

        # Rename the id column name and then transpose to get the correct format
        # Since the columns are counted as indices when transposing, we need to reset the index (but keep the DateTime
        # column)
        reformat_df = horizontal_format_df.rename(columns={TvMn.ID_COLUMN_NAME: TvMn.DATETIME_COL}).T.reset_index(drop=False)

        # after transposing, column names are set a the first row, which is DateTime, IDs
        reformat_df.columns = reformat_df.iloc[0]
        # We reindex by dropping the first row, thus removing the row of DateTime, IDs
        reformat_df = reformat_df.reindex(reformat_df.index.drop(0)).reset_index(drop=True)

        # Since It is possible to write only year or year-month as timestamp in the table,
        # we need to reformat to correct datetime format
        reformat_df[TvMn.DATETIME_COL] = self._to_iso_datetimes(reformat_df[TvMn.DATETIME_COL])

        return reformat_df

    def _to_iso_datetimes(self, series: pd.Series) -> list[datetime]:
        """
        Convert a series of dates to ISO datetime format.

        Args:
            series (pd.Series): Series which values will be converted to ISO format.

        Raises:
            RuntimeError: When an input value which cannot be converted is encountered.

        Returns:
            list[datetime]: List of formatted datetimes.

        """
        reformatted = []
        three_segments = 3
        two_segments = 2
        one_segment = 1
        for i in series:
            new_i = str(i)
            date_split = len(new_i.split("-"))
            space_split = len(new_i.split(" "))
            time_split = len(new_i.split(":"))
            try:
                if date_split == one_segment:  # Only year is defined
                    # get datetime for first week first day
                    new_i = datetime.fromisocalendar(int(new_i), 1, 1)
                elif date_split == two_segments:
                    # Year and month is defined
                    new_i = datetime.strptime(new_i + "-01", "%Y-%m-%d")  # Add first day
                elif date_split == three_segments and space_split == one_segment and time_split == one_segment:
                    # days defined but not time
                    new_i = datetime.strptime(new_i, "%Y-%m-%d")
                elif date_split == three_segments and space_split == two_segments and time_split == one_segment:
                    new_i = datetime.strptime(new_i, "%Y-%m-%d %H")
                elif date_split == three_segments and space_split == two_segments and time_split == two_segments:
                    new_i = datetime.strptime(new_i, "%Y-%m-%d %H:%M")
                elif date_split == three_segments and space_split == two_segments and time_split == three_segments:
                    # Assume time is defined
                    new_i = datetime.strptime(new_i, "%Y-%m-%d %H:%M:%S")
                else:
                    msg = f"Could not convert value '{new_i}' to datetime format."
                    raise ValueError(msg)
            except Exception as e:
                msg = f"Loader {self} could not convert value '{new_i}' to datetime format. Check formatting, for example number of spaces."
                raise RuntimeError(msg) from e
            reformatted.append(new_i)
        return sorted(reformatted)

    def _is_horizontal_format(self) -> bool:
        """Determine if the file strucure is the NVE small format."""
        column_names = pd.read_excel(self.get_source(), nrows=0, sheet_name=self._DATA_SHEET).columns.tolist()
        return TvMn.ID_COLUMN_NAME in column_names

    def _get_ids(self) -> list[str]:
        if self._content_ids is not None:
            return self._content_ids
        try:
            if self._is_horizontal_format():
                self._content_ids = pd.read_excel(
                    self.get_source(),
                    usecols=[TvMn.ID_COLUMN_NAME],
                    sheet_name=self._DATA_SHEET,
                )[TvMn.ID_COLUMN_NAME].tolist()
            else:
                columns_list = pd.read_excel(self.get_source(), nrows=0, sheet_name=self._DATA_SHEET).columns.tolist()
                columns_list.remove(TvMn.DATETIME_COL)
                self._content_ids = columns_list
        except ValueError as e:
            message = f"{self}: found problem with TimeVector IDs."
            raise RuntimeError(message) from e

        return self._content_ids

    def clear_cache(self) -> None:
        """Clear cached data."""
        self._data = None
        self._meta = None
        self._index = None


class NVEH5TimeVectorLoader(NVETimeVectorLoader):
    """
    Class for loading time vector data from NVE HDF5 file sources.

    Meant for large time vectors (e.g. hourly data over multiple years). Supports differing lengths and metadata of vectors stored in the file.

    Specialized to the following format:
        - index (h5py.Group, optional): Used to define indexes for vectors if index is supposed to only apply to that vector.
        - common_index (h5py.Dataset): Contains one numpy array for all vectors. This is a fallback index for vectors which have not defined their own index in
                                       the index group. Also used on purpose if many or all vectors have the same index.
        - metadata (h5py.Group): Used connect a specific set of metadata to a particular vector.
        - common_metadata (h5py.Group): Contains one set of metadata fields for all vectors. Used in a similar way as common_index.
        - vectors (h5py.Group): Contains numpy arrays containing the vector values connected to a unique ID. The same ID is used to connect the vector to an
                                index or metadata.

    """

    _SUPPORTED_SUFFIXES: ClassVar[list] = [".h5", ".hdf5"]

    def __init__(self, source: Path | str, require_whole_years: bool, relative_loc: Path | str | None = None, validate: bool = True) -> None:
        """
        Intitialize loader instance and connect it to a H5 file containing time vector data.

        Args:
            source (Path | str): Absolute Path to database or HDF5 file.
            require_whole_years (bool): Flag for validating that the time vectors in the source contain data for complete years.
            relative_loc (Path | str | None, optional): Path to HDF5 file relative to source. Defaults to None.
            validate (bool, optional): Whether to validate vectors after loading. NB! Loads all data into memory at once. Defaults to True.

        """
        super().__init__(source, require_whole_years, relative_loc)
        self._index: TimeIndex = None
        self._file_pointer = None

        if validate:
            self.validate_vectors()

    def get_values(self, vector_id: str) -> NDArray:
        """
        Get numpy array with all the values of a given vector in the Loader's HDF5 file.

        Args:
            vector_id (str): Unique id of the vector in the file.

        Returns:
            NDArray: Numpy array with values.

        """
        if self._data is None:
            self._data = dict()
        if vector_id not in self._data:
            with h5py.File(self.get_source(), mode="r") as h5f:
                self._data[vector_id] = self._read_vector_field(h5f, H5Names.VECTORS_GROUP, vector_id, field_type=h5py.Dataset, use_fallback=False)[()]
        return self._data[vector_id]

    def get_index(self, vector_id: str) -> TimeIndex:
        """
        Get the TimeIndex describing the time dimension of the vectors in the file.

        Args:
            vector_id (str): Not used since all vectors in the NVE parquet files have the same index.

        Returns:
            TimeIndex: TimeIndex object describing the parquet file's index.

        """
        if self._index is None:
            meta = self.get_metadata("")

            if TvMn.FREQUENCY not in meta or (TvMn.FREQUENCY in meta and meta[TvMn.FREQUENCY] is None):
                self._index = self._create_index(
                    datetimes=self._read_index(vector_id),
                    is_52_week_years=meta[TvMn.IS_52_WEEK_YEARS],
                    extrapolate_first_point=meta[TvMn.EXTRAPOLATE_FISRT_POINT],
                    extrapolate_last_point=meta[TvMn.EXTRAPOLATE_LAST_POINT],
                )
                return self._index
            index_array = self._read_index(vector_id) if meta[TvMn.START] is None or meta[TvMn.NUM_POINTS] is None else None
            start = meta[TvMn.START] if index_array is None else index_array[0].item()
            num_points = meta[TvMn.NUM_POINTS] if index_array is None else index_array.size

            self._index = FixedFrequencyTimeIndex(
                start,
                meta[TvMn.FREQUENCY],
                num_points,
                is_52_week_years=meta[TvMn.IS_52_WEEK_YEARS],
                extrapolate_first_point=meta[TvMn.EXTRAPOLATE_FISRT_POINT],
                extrapolate_last_point=meta[TvMn.EXTRAPOLATE_LAST_POINT],
            )

        return self._index

    def _read_index(self, vector_id: str) -> NDArray[np.datetime64]:
        with h5py.File(self.get_source(), mode="r") as h5f:
            decoded_index = np.char.decode(self._read_vector_field(h5f, H5Names.INDEX_GROUP, vector_id, h5py.Dataset)[()].astype(np.bytes_), encoding="utf-8")
            return decoded_index.astype(np.datetime64)

    def _read_vector_field(
        self,
        h5file: h5py.File,
        field_name: str,
        vector_id: str,
        field_type: type[h5py.Dataset | h5py.Group],
        use_fallback: bool = True,
    ) -> h5py.Dataset | h5py.Group:
        error = ""
        if field_name in h5file:  # check if group_name exists
            main_group = h5file[field_name]
            if not isinstance(main_group, h5py.Group):
                message = f"{self} expected '{field_name}' to be a {h5py.Group} in {h5file}. Got {type(main_group)}."
                raise TypeError(message)

            if vector_id in main_group:
                vector_field = main_group[vector_id]
                if not isinstance(vector_field, field_type):
                    message = f"{self} expected '{vector_id}' to be a {field_type} in {h5file}. Got {type(vector_field)}"
                    raise TypeError(message)
                return vector_field
            error = f"'{vector_id}' was not found in '{field_name}' group"
        else:
            error = f"'{field_name}' was not found in file"

        no_fallback_message = f"{self} expected '{vector_id}' in {h5py.Group} '{field_name}' "
        if not use_fallback:
            no_fallback_message += f"but {error}."
            raise KeyError(no_fallback_message)

        fallback_name = H5Names.COMMON_PREFIX + field_name
        if fallback_name in h5file:  # check if common_ + group_name exists
            fallback_field = h5file[fallback_name]
            if not isinstance(fallback_field, field_type):
                message = f"{self} expected '{fallback_field}' to be a {field_type} in {h5file}. Got {type(fallback_field)}."
                raise TypeError(message)
            return fallback_field

        message = (
            no_fallback_message
            + f"or a fallback {field_type} '{fallback_name}' in H5 file but "
            + f"{error},"
            + f" and fallback {field_type} '{fallback_name}' not found in file."
        )
        raise KeyError(message)

    def get_metadata(self, vector_id: str) -> dict[str, bool | int | str | datetime | timedelta | tzinfo | None]:
        """
        Retrieve and decodes custom metadata from parquet file.

        Args:
            vector_id (str): Not used

        Raises:
            KeyError: If any of the expected metadata keys is not found in file.

        Returns:
            dict: Dictionary with decoded metadata.

        """
        if self._meta is None:
            errors = set()
            meta = {}
            with h5py.File(self.get_source(), mode="r") as h5f:
                meta_group = self._read_vector_field(h5f, H5Names.METADATA_GROUP, vector_id, h5py.Group)
                for k, m in meta_group.items():
                    if isinstance(m, h5py.Dataset):
                        meta[k] = m[()]
                    else:
                        errors.add(f"Improper metadata format: Metadata key {k} exists but is a h5 group when it should be a h5 dataset.")
            self._report_errors(errors)
            self._meta = self._process_meta(meta)
        return self._meta

    def _get_ids(self) -> list[str]:
        with h5py.File(self.get_source(), mode="r") as h5f:
            if H5Names.VECTORS_GROUP in h5f:
                return list(h5f[H5Names.VECTORS_GROUP].keys())
            message = f"{self} required key '{H5Names.VECTORS_GROUP}' was not found in file."
            raise KeyError(message)

    def clear_cache(self) -> None:
        """Clear cached data."""
        self._data = None
        self._meta = None
        self._index = None


class NVEYamlTimeVectoroader(NVETimeVectorLoader):
    """
    Class for loading time vector data from NVE YAML file sources.

    Meant for very sparse time vector data, where the vectors have varying lengths and indexes. Currently all vectors must have the same metadata within each
    file.
    Supported format:
        - Metadata: field containing dictionary with metadata for all vectors.
        - Other fields are vector IDs with lists for x and y axes.

    """

    _SUPPORTED_SUFFIXES: ClassVar[list] = [".yaml", ".yml"]

    def __init__(self, source: Path | str, require_whole_years: bool, relative_loc: Path | str | None = None, validate: bool = True) -> None:
        """
        Intitialize loader instance and connect it to an Yaml file containing time vector data.

        Args:
            source (Path | str): Absolute Path to database or excel file.
            require_whole_years (bool): Flag for validating that the time vectors in the source contain data for complete years.
            relative_loc (Path | str | None, optional): Path to excel file relative to source. Defaults to None.
            validate (bool, optional): Flag to turn on validation of timevectors. NB! Loads all data into memory at once. Defaults to True.

        """
        super().__init__(source, require_whole_years, relative_loc)
        self._content_ids: list[str] = None

        self._values_label: str = None
        self._index_label: str = None

        if validate:
            self.validate_vectors()

    def get_values(self, vector_id: str) -> NDArray:
        """
        Get values of vector.

        Args:
            vector_id (str): Unique id of the curve in the Loader source.

        Returns:
            NDArray: Numpy array with values of vector.

        """
        if self._data is None:
            self._parse_file()
        values_list = self._data[vector_id][self._values_label]
        if len(values_list) == 0:
            message = f"Time vector {vector_id} in {self} contains no points."
            raise ValueError(message)
        return np.asarray(values_list)

    def get_index(self, vector_id: str) -> TimeIndex:
        """
        Get index of vector.

        Args:
            vector_id (str): Unique id of the curve in the Loader source.

        Returns:
            NDArray: Numpy array with index of vector.

        """
        meta = self.get_metadata(vector_id)  # also parses data
        try:
            datetime_list = [self._date_to_datetime(index_val) for index_val in self._data[vector_id][self._index_label]]
        except ValueError as e:
            message = f"{self} got non date or none datetime values in index field of vector {vector_id}."
            raise ValueError(message) from e

        if len(datetime_list) == 0:
            message = f"Index of {vector_id} in {self} contains no points."
            raise ValueError(message)

        if (len(datetime_list) == 1 or self.get_values(vector_id).size == 1) and meta[TvMn.EXTRAPOLATE_FISRT_POINT] and meta[TvMn.EXTRAPOLATE_LAST_POINT]:
            # Even though _create_index can now handle ConstantTimeIndexes,
            # we need to consider that YAML time vectors can have the extra end date for its final period stored in its index.
            # That would lead to _create_time_index not creating a constant one when it should.
            # We may remove this feature in the future.
            return ConstantTimeIndex()

        args = (
            datetime_list,
            meta[TvMn.IS_52_WEEK_YEARS],
            meta[TvMn.EXTRAPOLATE_FISRT_POINT],
            meta[TvMn.EXTRAPOLATE_LAST_POINT],
        )

        if len(datetime_list) == len(self.get_values(vector_id)) + 1:
            return ListTimeIndex(*args)
        # create index with added end datetime
        return self._create_index(*args)

    def get_metadata(self, vector_id: str) -> dict[str, bool | int | str | datetime | timedelta | tzinfo | None]:
        """
        Read YAML file metadata.

        Args:
            vector_id (str): Not used.

        Raises:
            KeyError: If an expected metadata key is missing.

        Returns:
            dict[str, bool|int|str|datetime|timedelta|tzinfo|None]: Metadata dictionary.

        """
        if self._meta is None:
            raw_meta = self._data[YamlNames.metadata_field][YamlNames.x_field]

            self._meta = self._process_meta(raw_meta)
        return self._meta

    def _get_ids(self) -> list[str]:
        if self._content_ids is None:
            if self._data is None:
                self._parse_file()
            ids_list = list(self._data.keys())
            ids_list.remove(YamlNames.metadata_field)
            self._content_ids = ids_list
        return self._content_ids

    def _parse_file(self) -> None:
        with self.get_source().open(encoding=YamlNames.encoding) as f:
            d = yaml.safe_load(f)
            self._x_meta = d[YamlNames.metadata_field][YamlNames.x_field]
            self._y_meta = d[YamlNames.metadata_field][YamlNames.y_field]

            self._values_label = self._x_meta[YamlNames.attribute]
            self._index_label = self._y_meta[YamlNames.attribute]

            self._data = d

    def _date_to_datetime(self, value: date | datetime) -> datetime:
        if isinstance(value, date):
            value = datetime(value.year, value.month, value.day)
        elif not isinstance(value, datetime):
            message = "Value must be date or datetime."
            raise ValueError(message)
        return value

    def clear_cache(self) -> None:
        """Clear cached data."""
        self._data = None
        self._meta = None

        self._content_ids = None

        self._values_label = None
        self._index_label = None


class NVEParquetTimeVectorLoader(NVETimeVectorLoader):
    """
    Class for loading time vector data from NVE parquet file sources.

    Meant for large time vectors. All vectors in the file must have the same lenghts and metadata.
    Supports format:
        - 'Vertical' with one index collumn (DateTime) and the others containing vector values.

    """

    _SUPPORTED_SUFFIXES: ClassVar[list] = [".parquet"]

    def __init__(self, source: Path | str, require_whole_years: bool, relative_loc: Path | str | None = None, validate: bool = True) -> None:
        """
        Intitialize loader instance and connect it to an Parquet file containing time vector data.

        Args:
            source (Path | str): Absolute Path to database or parquet file.
            require_whole_years (bool): Flag for validating that the time vectors in the source contain data for complete years.
            relative_loc (Path | str | None, optional): Path to parquet file relative to source. Defaults to None.
            validate (bool, optional): Flag to turn on validation of timevectors. NB! Loads all data into memory at once. Defaults to True.

        """
        super().__init__(source, require_whole_years, relative_loc)
        self._index: TimeIndex = None
        if validate:
            self.validate_vectors()

    def get_values(self, vector_id: str) -> NDArray:
        """
        Get numpy array with all the values of a given vector in the Loader's parquet file.

        Args:
            vector_id (str): Unique id of the vector in the file.

        Returns:
            NDArray: Numpy array with values.

        """
        if self._data is None:
            self._data = dict()
        if vector_id not in self._data:
            table = pq.read_table(self.get_source(), columns=[vector_id])
            self._data[vector_id] = table[vector_id].to_numpy()
        # if self._data is None:
        #     self._data = pq.read_table(self.get_source())
        return self._data[vector_id]  # .to_numpy()

    def get_index(self, vector_id: str) -> TimeIndex:  # Could be more types of indexes?
        """
        Get the TimeIndex describing the time dimension of the vectors in the file.

        Args:
            vector_id (str): Not used since all vectors in the NVE parquet files have the same index.

        Returns:
            TimeIndex: TimeIndex object describing the parquet file's index.

        """
        if self._index is None:
            meta = self.get_metadata("")

            if TvMn.FREQUENCY not in meta or (TvMn.FREQUENCY in meta and meta[TvMn.FREQUENCY] is None):
                datetime_index = pd.DatetimeIndex(
                    pd.read_parquet(self.get_source(), columns=[TvMn.DATETIME_COL])[TvMn.DATETIME_COL],
                    tz=meta[TvMn.TIMEZONE],
                ).tolist()
                self._index = self._create_index(
                    datetimes=datetime_index,
                    is_52_week_years=meta[TvMn.IS_52_WEEK_YEARS],
                    extrapolate_first_point=meta[TvMn.EXTRAPOLATE_FISRT_POINT],
                    extrapolate_last_point=meta[TvMn.EXTRAPOLATE_LAST_POINT],
                )
                return self._index

            parquet_file = None
            if TvMn.START not in meta or (TvMn.START in meta and meta[TvMn.START] is None):
                parquet_file = pq.ParquetFile(self.get_source())
                start = pd.to_datetime(next(parquet_file.iter_batches(batch_size=1, columns=[TvMn.DATETIME_COL])))
            else:
                start = meta[TvMn.START]

            if TvMn.NUM_POINTS not in meta or (TvMn.NUM_POINTS in meta and meta[TvMn.NUM_POINTS] is None):
                if parquet_file is None:
                    parquet_file = pq.ParquetFile(self.get_source())
                num_points = parquet_file.metadata.num_rows
            else:
                num_points = meta[TvMn.NUM_POINTS]
            self._index = FixedFrequencyTimeIndex(
                start,
                meta[TvMn.FREQUENCY],
                num_points,
                is_52_week_years=meta[TvMn.IS_52_WEEK_YEARS],
                extrapolate_first_point=meta[TvMn.EXTRAPOLATE_FISRT_POINT],
                extrapolate_last_point=meta[TvMn.EXTRAPOLATE_LAST_POINT],
            )

        return self._index

    def get_metadata(self, vector_id: str) -> dict[str, bool | int | str | datetime | timedelta | tzinfo | None]:
        """
        Retrieve and decodes custom metadata from parquet file.

        Args:
            vector_id (str): Not used

        Raises:
            KeyError: If any of the expected metadata keys is not found in file.

        Returns:
            dict: Dictionary with decoded metadata.

        """
        if self._meta is None:
            path = self.get_source()
            raw_meta = pq.ParquetFile(path).schema_arrow.metadata

            self._meta = self._process_meta(raw_meta)
        return self._meta

    def _get_ids(self) -> list[str]:
        parquet_file = pq.ParquetFile(self.get_source())
        time_vector_ids: list[str] = parquet_file.schema_arrow.names
        time_vector_ids.remove(TvMn.DATETIME_COL)
        return time_vector_ids

    def clear_cache(self) -> None:
        """Clear cached data."""
        self._data = None
        self._meta = None
        self._index = None
