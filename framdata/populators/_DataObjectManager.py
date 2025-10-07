"""Contain class for creating TimeVectors, Curves and their Loaders."""

from pathlib import Path
from time import time

from framcore import Base
from framcore.curves import LoadedCurve
from framcore.loaders import CurveLoader, Loader, TimeVectorLoader
from framcore.timevectors import LoadedTimeVector

from framdata.loaders import (
    NVEExcelTimeVectorLoader,
    NVEH5TimeVectorLoader,
    NVEParquetTimeVectorLoader,
    NVEYamlTimeVectoroader,
)
from framdata.loaders.curve_loaders import NVEYamlCurveLoader


class _DataObjectManager(Base):
    """Manage TimeVectors, Curves, and their Loaders."""

    def __init__(
        self,
        validate: bool = True,
    ) -> None:
        super().__init__()
        self._validate = validate

    def create_time_vectors(self, source: Path, relative_loc: Path, require_whole_years: bool) -> dict[str, LoadedTimeVector]:
        """
        Create and return a dictionary of LoadedTimeVector objects.

        Args:
            source (Path): _description_
            relative_loc (Path): _description_

        Returns:
            dict[str, LoadedTimeVector]: keys are IDs, values are LoadedTimeVector objects.

        """
        time_vectors = {}
        t = time()
        loader: TimeVectorLoader = self._create_loader(TimeVectorLoader, source, relative_loc=relative_loc, req_whole_years=require_whole_years)
        val_msg = "Create and validate" if self._validate else "Create"
        self.send_debug_event(f"{val_msg} loader for {relative_loc} time: {round(time() - t, 3)}")

        t = time()
        loader_ids = loader.get_ids()
        # self.send_debug_event(f"Loader get_ids time: {round(time() - t, 3)}")

        times = []
        for vector_id in loader_ids:
            t = time()
            tv = LoadedTimeVector(vector_id, loader)
            time_vectors[vector_id] = tv
            times.append(time() - t)

        return time_vectors

    def create_curves(self, source: Path, relative_loc: Path) -> dict[str, LoadedCurve]:
        """
        Create and return a dictionary of LoadedCurve objects.

        Args:
            source (Path): _description_
            relative_loc (Path): _description_

        Returns:
            dict[str, LoadedCurve]: keys are IDs, values are LoadedCurve objects.

        """
        curves = {}
        t = time()
        loader: CurveLoader = self._create_loader(CurveLoader, source, relative_loc=relative_loc)
        self.send_debug_event(f"Create loader for {relative_loc} time: {round(time() - t, 3)}")

        t = time()
        loader_ids = loader.get_ids()
        self.send_debug_event(f"Loader get_ids time: {round(time() - t, 3)}")

        times = []
        for curve_id in loader_ids:
            t = time()
            tv = LoadedCurve(curve_id, loader)
            curves[curve_id] = tv
            times.append(time() - t)
        self.send_debug_event(f"Average curve loop time for {relative_loc}: {round(sum(times) / len(loader_ids), 3)}")

        return curves

    def _create_loader(
        self,
        data_type: TimeVectorLoader | CurveLoader,
        source: Path,
        relative_loc: Path | None = None,
        req_whole_years: bool | None = None,
    ) -> Loader:
        """
        Create and return a Loader based on file extension.

        Args:
            data_type (TimeVectorLoader | CurveLoader): Denoting if the Loader is created for a Curve or TimeVector.
            source (Path): Absolute path to database where the file is located.
            relative_loc (Optional[Path], optional): Path of file in database relative to source. Defaults to None.

        Raises:
            NotImplementedError: Raised when there is no specific Loader which can be created for the file.

        Returns:
            Loader: Loader connected to the input file.

        """
        path = source
        if relative_loc is not None:
            path = source / relative_loc
        suffix = path.suffix
        if data_type == TimeVectorLoader:
            if suffix in NVEExcelTimeVectorLoader.get_supported_suffixes():
                return NVEExcelTimeVectorLoader(source=source, relative_loc=relative_loc, require_whole_years=req_whole_years, validate=self._validate)
            if suffix in NVEH5TimeVectorLoader.get_supported_suffixes():
                return NVEH5TimeVectorLoader(source=source, relative_loc=relative_loc, require_whole_years=req_whole_years, validate=self._validate)
            if suffix in NVEYamlTimeVectoroader.get_supported_suffixes():
                return NVEYamlTimeVectoroader(source=source, relative_loc=relative_loc, require_whole_years=req_whole_years, validate=self._validate)
            if suffix in NVEParquetTimeVectorLoader.get_supported_suffixes():
                return NVEParquetTimeVectorLoader(source=source, relative_loc=relative_loc, require_whole_years=req_whole_years, validate=self._validate)
        if data_type == CurveLoader and suffix in NVEYamlCurveLoader.get_supported_suffixes():
            return NVEYamlCurveLoader(source=source, relative_loc=relative_loc)

        msg = f"Could not create an appropriate loader for source: {source} and relative location: {relative_loc}. No defined loader for filetype {suffix}."
        raise NotImplementedError(msg)
