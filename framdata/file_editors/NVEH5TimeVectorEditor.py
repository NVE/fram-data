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


class NVEH5TimeVectorEditor(NVEFileEditor):
    """
    Class with functionality concerned with editing time vectors and their metadata in H5 files.

    Structure of the NVE h5 files:
     - common_index dataset: Contains a numpy array with index applied to all vectors missing a specific index.
     - index group of datasets: Contains indexes coupled to specific vectors by the vector IDs.
     - common_metadata group: Contains dictionary with metadata applied to all vectors missing a specific metadata dictionary.
     - metadata group of groups: Contains metadata dictionaries coupled to specific vectors by the vector IDs.
     - vectors group of datasets: Contains numpy arrays with the vector values.

    """

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
        """Get a copy of the metadata of all vectors in the h5 file."""
        try:
            return self._metadata[vector_id].copy()
        except KeyError as e:
            f"Found no ID '{vector_id}' in metadata."
            raise KeyError from e

    def set_metadata(self, vector_id: str, metadata: dict[str, TvMn.METADATA_TYPES]) -> None:
        """Set the metadata dictionary of a specific vector (overwrites existing)."""
        self._check_type(vector_id, str)
        self._check_type(metadata, dict)
        for key, value in metadata.items():
            self._check_type(key, str)
            self._check_type(value, TvMn.METADATA_TYPES_TUPLE)
        self._metadata[vector_id] = metadata

    def set_metadata_by_key(self, vector_id: str, key: str, value: TvMn.METADATA_TYPES) -> None:
        """Set a field (new or overwrite) in the metadata of a vector."""
        self._check_type(key, str)
        self._check_type(vector_id, str)
        self._check_type(value, TvMn.METADATA_TYPES_TUPLE)
        if vector_id not in self._metadata or not isinstance(self._metadata[vector_id], dict):
            self._metadata[vector_id] = {}
        self._metadata[vector_id][key] = value

    def get_common_metadata(self) -> None | dict:
        """Get a copy of the common metadata of vectors in the h5 file."""
        return self._common_metadata if self._common_metadata is None else self._common_metadata.copy()

    def set_common_metadata(self, metadata: dict[str, TvMn.METADATA_TYPES]) -> None:
        """Set the common metadata dictionary (overwrites existing)."""
        self._check_type(metadata, dict)
        self._common_metadata = metadata

    def set_common_metadata_by_key(self, key: str, value: TvMn.METADATA_TYPES) -> None:
        """Set a field (new or overwrite) in the common metadata."""
        self._check_type(key, str)
        self._check_type(value, TvMn.METADATA_TYPES_TUPLE)
        if self._common_metadata is None:
            self._common_metadata = {}
        self._common_metadata[key] = value

    def set_index(self, vector_id: str, index: NDArray) -> None:
        """
        Set the index of a vector.

        Index is paired with a vector of the same vector_id.

        """
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
        """Set the common index which will be used for vectors which have not specified their own index by its ID."""
        self._check_type(values, np.ndarray)
        self._common_index = values

    def get_common_index(self) -> NDArray | None:
        """Return a copy of a given index as a pandas series from the table."""
        return self._common_index

    def set_vector(self, vector_id: str, values: NDArray) -> None:
        """Set vector values."""
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
        """Get the IDs of all vectors available in the file."""
        return list(self._vectors.keys())

    def save_to_h5(self, path: Path | str) -> None:
        """
        Store the data to h5 file.

        Args:
            path (Path | str): Path to save the file. Overwrites existing files.

        Raises:
            KeyError: If common index is None and there are vectors missing specific index.
            KeyError: If common metadata is None and there are vectors missing specific metadata.

        """
        self._check_type(path, (Path, str))
        path = Path(path)

        self._check_missing_indexes()
        self._check_missing_metadata()

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

    def _check_missing_indexes(self) -> None:
        missing_index = {v for v in self._vectors if v not in self._index}
        if self._common_index is None and len(missing_index) != 0:
            msg = f"Found vectors missing indexes and common index is not set: {missing_index}."
            raise KeyError(msg)

    def _check_missing_metadata(self) -> None:
        missing_meta = {v for v in self._vectors if v not in self._metadata}
        if self._common_metadata is None and len(missing_meta) != 0:
            msg = f"Found vectors missing metadata and common metadata is not set: {missing_meta}."
            raise KeyError(msg)

    def _write_meta_to_group(self, meta_group: h5py.Group, metadata: dict) -> None:
        for k, v in metadata.items():
            meta_group.create_dataset(k, data=str(v).encode(TvMn.ENCODING))

    def _read_data(
        self,
        group_name: str,
        cast_meta: bool,
    ) -> tuple[dict[str, dict[str, TvMn.METADATA_TYPES]] | dict[str, dict[str, NDArray]], dict[str, TvMn.METADATA_TYPES] | dict[str, NDArray]]:
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
