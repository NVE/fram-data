"""Contain class with common functionality for editing files."""

from pathlib import Path

from framcore.Base import Base


class NVEFileEditor(Base):
    """Parent class with common functionality for classes concerned with editing FRAM files."""

    def __init__(self, source: Path | str | None = None) -> None:
        """
        Set path to parquet file if supplied, load/initialize table and metadata as pd.DataFrame and dictionary respectively.

        Args:
            source (Path | str | None, optional): Path to parquet file with timevectors. Defaults to None.

        """
        super().__init__()

        self._check_type(source, (Path, str, type(None)))
        self._source = None if source is None else Path(source)

    def get_source(self) -> Path:
        """Get the source file path of the editor."""
        return self._source

    def set_source(self, source: Path) -> None:
        """Set the source file path of the editor."""
        self._check_type(source, (Path, str))
        self._source = Path(source)
