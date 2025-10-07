"""Contains class for editing time vectors in parquet files."""

from datetime import datetime, timedelta, tzinfo
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from framdata.database_names.TimeVectorMetadataNames import TimeVectorMetadataNames as TvMn
from framdata.file_editors.NVEFileEditor import NVEFileEditor


class NVEParquetTimeVectorEditor(NVEFileEditor):
    """Class for managing time vectors and their metadata stored in parquet files."""

    def __init__(self, source: Path | str | None = None) -> None:
        """
        Set path to parquet file if supplied, load/initialize table and metadata as pd.DataFrame and dictionary respectively.

        Args:
            source (Path | str | None, optional): Path to parquet file with timevectors. Defaults to None.

        """
        super().__init__(source)
        self._metadata, __ = ({}, None) if self._source is None or not self._source.exists() else self._read_metadata()
        self._data = pd.DataFrame() if self._source is None or not self._source.exists() else pd.read_parquet(self._source)

    def save_to_parquet(self, path: Path | str) -> None:
        """
        Save the edited dataframe and metadata to parquet file.

        Args:
            path (Path): Path to save tha file to. Must be defined to force user to explicitly overwrite the original file if they want.

        """
        self._check_type(path, (Path, str))
        path = Path(path)
        table = pa.Table.from_pandas(self._data)

        # ensure binary strings with defined encoding, since parquet encodes metadata anyway
        schema_with_meta = table.schema.with_metadata({str(k).encode(TvMn.ENCODING): str(v).encode(TvMn.ENCODING) for k, v in self._metadata.items()})
        table = pa.Table.from_pandas(self._data, schema=schema_with_meta)

        pq.write_table(table, path)

    def get_metadata(self):
        """Get a copy of the metadata of the parquet file."""
        return self._metadata if self._metadata is None else self._metadata.copy()

    def set_metadata(self, key: str, value: bool | int | str | datetime | timedelta | tzinfo | None) -> None:
        """Set a field (new or overwrite) in the metadata."""
        self._check_type(key, str)
        self._check_type(value, (bool, int, str, datetime, timedelta, tzinfo, type(None)))
        self._metadata[key] = value

    def set_vector(self, vector_id: str, values: pd.Series) -> None:
        """Set a whole vector in the time vector table."""
        self._check_type(vector_id, str)
        self._check_type(values, pd.Series)
        if not self._data.empty and len(values) != len(self._data):
            message = f"Series values has different size than the other vectors in the table.\nLength values: {len(values)}\nLength vectors: {len(self._data)}"
            raise IndexError(message)
        self._data[vector_id] = values

    def get_vector(self, vector_id: str) -> pd.Series:
        """Return a copy of a given vector as a pandas series from the table."""
        try:
            return self._data[vector_id].copy()
        except KeyError as e:
            f"Found no vector named '{vector_id}' in table at {self._source}."
            raise KeyError from e

    def get_dataframe(self) -> pd.DataFrame:
        """Return a copy of all of the vector table as a pandas dataframe."""
        return self._data.copy()

    def set_dataframe(self, dataframe: pd.DataFrame) -> None:
        """Set the dataframe of the editor."""
        self._check_type(dataframe, pd.DataFrame)
        self._data = dataframe

    def get_vector_ids(self) -> list[str]:
        """Get the IDs of all vectors."""
        return [c for c in self._data.columns if c != TvMn.DATETIME_COL]

    def set_index_column(self, index: pd.Series) -> None:
        """Set the index column."""
        self._check_type(index, pd.Series)
        if not self._data.empty and len(index) != len(self._data):
            message = f"Series index has different size than the other vectors in the table.\nLength index: {len(index)}\nLength vectors: {len(self._data)}"
            raise IndexError(message)
        self._data[TvMn.DATETIME_COL] = index

    def get_index_column(self) -> pd.Series:
        """Get the datetime column of the dataframe."""
        if TvMn.DATETIME_COL not in self._data:
            message = f"Table at {self._source} does not have an index column. Index column must exist and be named '{TvMn.DATETIME_COL}'."
            raise KeyError(message)
        return self._data[TvMn.DATETIME_COL].copy()

    def _read_metadata(self) -> tuple[dict[str, bool | int | str | datetime | timedelta | tzinfo | None], set[str]]:
        if self._source is None:
            message = "Must set a source before reading file."
            raise ValueError(message)
        metadata = pq.ParquetFile(self._source).schema_arrow.metadata
        return TvMn.cast_meta(metadata)
