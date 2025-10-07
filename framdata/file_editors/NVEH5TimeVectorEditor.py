"""Contains class for editing time vectors in H5 files."""

from collections import defaultdict
from datetime import datetime, timedelta, tzinfo
from pathlib import Path

import h5py
import numpy as np
from numpy.typing import NDArray

from framdata.database_names.H5Names import H5Names
from framdata.database_names.TimeVectorMetadataNames import TimeVectorMetadataNames as TvMn
from framdata.file_editors.NVEFileEditor import NVEFileEditor

METADATA_TYPES = bool | int | str | datetime | timedelta | tzinfo | None


class NVEH5TimeVectorEditor(NVEFileEditor):
    """Class with functionality concerned with editing time vectors and their metadata in H5 files."""

    def __init__(self, source: Path | str | None = None) -> None:
        """
        Set path to parquet file if supplied, load/initialize table and metadata as pd.DataFrame and dictionary respectively.

        Args:
            source (Path | str | None, optional): Path to parquet file with timevectors. Defaults to None.

        """
        super().__init__(source)

        meta_tuple = ({}, None) if self._source is None or not self._source.exists() else self._read_data(H5Names.METADATA_GROUP, True)
        self._metadata, self._common_metadata = meta_tuple
        index_tuple = (defaultdict(NDArray), None) if self._source is None or not self._source.exists() else self._read_data(H5Names.INDEX_GROUP, False)
        self._index, self._common_index = index_tuple
        self._index = {k: v.astype(str) for k, v in self._index.items()}

        vectors_tuple = (defaultdict(NDArray), None) if self._source is None or not self._source.exists() else self._read_data(H5Names.VECTORS_GROUP, False)
        self._vectors, __ = vectors_tuple

    def get_metadata(self, vector_id: str) -> None | dict:
        """Get a copy of the metadata of the parquet file."""
        try:
            return self._metadata[vector_id]
        except KeyError as e:
            f"Found no ID '{vector_id}' in metadata."
            raise KeyError from e

    def set_metadata(self, vector_id: str, value: dict[str, METADATA_TYPES]) -> None:
        """Set a field (new or overwrite) in the metadata."""
        self._check_type(vector_id, str)
        self._check_type(value, dict)
        self._metadata[vector_id] = value

    def get_common_metadata(self) -> None | dict:
        """Get a copy of the metadata of the parquet file."""
        return self._common_metadata if self._common_metadata is None else self._common_metadata.copy()

    def set_common_metadata(self, value: dict[str, METADATA_TYPES]) -> None:
        """Set a field (new or overwrite) in the metadata."""
        self._check_type(value, dict)
        self._common_metadata = value

    def set_index(self, vector_id: str, index: NDArray) -> None:
        """Set a whole index in the time index table."""
        self._check_type(vector_id, str)
        self._check_type(index, np.ndarray)
        self._index[vector_id] = index

    def get_index(self, vector_id: str) -> NDArray:
        """Return a copy of a given index as a pandas series from the table."""
        try:
            return self._index[vector_id]
        except KeyError as e:
            f"Found no ID '{vector_id}' among indexes."
            raise KeyError from e

    def set_common_index(self, values: NDArray) -> None:
        """Set a whole index in the time index table."""
        self._check_type(values, np.ndarray)
        self._common_index = values

    def get_common_index(self) -> NDArray | None:
        """Return a copy of a given index as a pandas series from the table."""
        return self._common_index

    def set_vector(self, vector_id: str, values: NDArray) -> None:
        """Set a whole vector in the time vector table."""
        self._check_type(vector_id, str)
        self._check_type(values, np.ndarray)
        self._vectors[vector_id] = values

    def get_vector(self, vector_id: str) -> NDArray:
        """Return a copy of a given vector as a pandas series from the table."""
        try:
            return self._vectors[vector_id]
        except KeyError as e:
            msg = f"Found no ID '{vector_id}' among vectors."
            raise KeyError(msg) from e

    def get_vector_ids(self) -> list[str]:
        """Get the IDs of all vectors."""
        return list(self._vectors.keys())

    def save_to_h5(self, path: Path | str) -> None:
        self._check_type(path, (Path, str))
        path = Path(path)

        missing_index = {v for v in self._vectors if v not in self._index}
        if self._common_index is None and len(missing_index) != 0:
            msg = f"Found vectors missing indexes and common index is not set: {missing_index}."
            raise KeyError(msg)

        missing_meta = {v for v in self._vectors if v not in self._metadata}
        if self._common_metadata is None and len(missing_meta) != 0:
            msg = f"Found vectors missing metadata and common metadata is not set: {missing_meta}."
            raise KeyError(msg)

        with h5py.File(path, mode="w") as f:
            if self._common_metadata is not None:
                common_meta_group = f.create_group(H5Names.COMMON_PREFIX + H5Names.METADATA_GROUP)
                self._write_meta_to_group(common_meta_group, self._common_metadata)
            if self._common_index is not None:
                f.create_dataset(H5Names.COMMON_PREFIX + H5Names.INDEX_GROUP, data=self._common_index.astype(bytes))

            if self._metadata:
                meta_group = f.create_group(H5Names.METADATA_GROUP)
                for vector_id, meta in self._metadata.items():
                    vm_group = meta_group.create_group(vector_id)
                    self._write_meta_to_group(vm_group, meta)

            if self._index:
                index_group = f.create_group(H5Names.INDEX_GROUP)
                for vector_id, index in self._index.items():
                    index_group.create_dataset(vector_id, data=index.astype(bytes))

            if self._vectors:
                vector_group = f.create_group(H5Names.VECTORS_GROUP)
                for vector_id, vector in self._vectors.items():
                    vector_group.create_dataset(vector_id, data=vector)

    def _write_meta_to_group(self, meta_group: h5py.Group, metadata: dict) -> None:
        for k, v in metadata.items():
            meta_group.create_dataset(k, data=str(v).encode(TvMn.ENCODING))

    def _read_data(
        self, group_name: str, cast_meta: bool
    ) -> tuple[dict[str, dict[str, METADATA_TYPES]] | dict[str, dict[str, NDArray]], dict[str, METADATA_TYPES] | dict[str, NDArray]]:
        common_field = H5Names.COMMON_PREFIX + group_name
        data = {}
        common_data = None
        with h5py.File(self._source, mode="r") as f:
            if group_name in f and isinstance(f[group_name], h5py.Group):
                group = f[group_name]
                data.update(
                    {
                        vector_id: TvMn.cast_meta(self._read_datasets(vector_data)) if cast_meta else self._read_datasets(vector_data)
                        for vector_id, vector_data in group.items()
                    },
                )

            if common_field in f and isinstance(f[common_field], h5py.Group):
                datasets = self._read_datasets(f[common_field])
                common_data, __ = TvMn.cast_meta(datasets) if cast_meta else (datasets, None)
            elif common_field in f and isinstance(f[common_field], h5py.Dataset):
                common_data = f[common_field][()]

        return data, common_data

    def _read_datasets(self, field: h5py.Group | h5py.Dataset) -> dict | NDArray | bytes:
        if isinstance(field, h5py.Dataset):
            return field[()]
        datasets = {}
        for key, val in field.items():
            if isinstance(val, h5py.Dataset):
                datasets[key] = val[()]
            else:
                msg = f"Expected only {h5py.Dataset} in field, but found {type(val)}"
                raise TypeError(msg)

        return datasets
