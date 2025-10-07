"""Contains class for loading Curve data from NVE yaml files."""

from pathlib import Path
from typing import ClassVar

import numpy as np
import yaml  # type: ignore
from framcore.loaders import CurveLoader, FileLoader
from numpy.typing import NDArray

from framdata.database_names.YamlNames import YamlNames


class NVEYamlCurveLoader(FileLoader, CurveLoader):
    """Handle reading of Curve data from a yaml File of NVE specific format."""

    _SUPPORTED_SUFFIXES: ClassVar[list[str]] = [".yaml", ".yml"]

    def __init__(self, source: Path | str, relative_loc: Path | str | None = None) -> None:
        """
        Handle reading of curves from a single yaml file.

        Args:
            source (Path | str): Absolute Path to database or yaml file path.
            relative_loc (Optional[Union[Path, str]], optional): Path to yaml file relative to source. Defaults to None.

        """
        super().__init__(source, relative_loc)

        self._data = None
        self._x_meta: str = None
        self._y_meta: str = None

        self._x_label: str = None
        self._y_label: str = None

    def get_x_axis(self, curve_id: str) -> NDArray:
        """
        Get values of x axis.

        Args:
            curve_id (str): Unique id of the curve in the Loader source.

        Returns:
            NDArray: Numpy array with values of x axis.

        """
        if self._data is None:
            self._parse_file()
        return np.asarray(self._data[curve_id][self._x_label])

    def get_y_axis(self, curve_id: str) -> NDArray:
        """
        Get values of y axis.

        Args:
            curve_id (str): Unique id of the curve in the Loader source.

        Returns:
            NDArray: Numpy array with values of y axis.

        """
        if self._data is None:
            self._parse_file()
        return np.asarray(self._data[curve_id][self._y_label])

    def get_x_unit(self, curve_id: str) -> str:
        """
        Get the unit of the x axis for the specified curve.

        Args:
            curve_id (str): Unique id of the curve in the Loader source.

        Returns:
            str: Unit of the x axis.

        """
        if self._data is None:
            self._parse_file()
        return self._x_meta[YamlNames.unit]

    def get_y_unit(self, curve_id: str) -> str:
        """
        Get the unit of the y axis for the specified curve.

        Args:
            curve_id (str): Unique id of the curve in the Loader source.

        Returns:
            str: Unit of the y axis.

        """
        if self._data is None:
            self._parse_file()
        return self._y_meta[YamlNames.unit]

    def get_metadata(self, content_id: str) -> dict:
        """
        Retrieve metadata for the specified content ID.

        Args:
            content_id (str): Unique identifier for the content.

        Returns:
            dict: Metadata associated with the content.

        """
        if self._data is None:
            self._parse_file()
        return self._data[YamlNames.metadata_field]

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

            self._x_label = self._x_meta[YamlNames.attribute]
            self._y_label = self._y_meta[YamlNames.attribute]

            self._data = d

    def clear_cache(self) -> None:
        """Clear cached data."""
        self._data = None
        self._x_meta = None
        self._y_meta = None

        self._x_label = None
        self._y_label = None
