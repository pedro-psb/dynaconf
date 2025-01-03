from dynaconflib.datastructures import LoadRequest
from dynaconflib.utils import ensure_list
from pathlib import Path
from typing import Optional
from functools import partial
import fnmatch
import os


class BaseLoadFactory:
    def build(self) -> list[LoadRequest]:
        raise NotImplementedError()


class FileLoader:
    """Declarative loader for files."""

    def __init__(
        self,
        filenames: str,
        root: Optional[Path] = None,
        namespace_filter: list[str] = None,
    ):
        self.filenames_list = ensure_list(filenames)
        self.root = root or Path()
        self.script_dir = Path(__file__).parent
        self.cwd = Path()
        # load request options
        self.LoadRequest = partial(LoadRequest, namespace_filter=namespace_filter)

    def build(self) -> list[LoadRequest]:
        load_requests = []
        for fn in self.filenames_list:
            absolute_paths = self.expand_paths(fn)
            for path in absolute_paths:
                abs_path = str(path.absolute())
                filetype = self.get_filetype(path.absolute())
                load_requests.append(self.LoadRequest(f"builtin.{filetype}", abs_path))
        return load_requests

    @staticmethod
    def get_filetype(file_path: Path) -> str:
        FILETYPE_SUFFIX_MAP = {
            "yaml": (".yaml", ".yml"),
            "toml": (".toml",),
            "json": (".json",),
        }

        for filetype, accepted_strings in FILETYPE_SUFFIX_MAP.items():
            if file_path.suffix in accepted_strings:
                return filetype
        raise TypeError(f"Filetype not supported: {file_path.absolute()}")

    @staticmethod
    def expand_paths(pattern: str) -> list[Path]:
        """
        Expands a glob pattern into a list of absolute Paths.
        Supports * ? [] expansion characters.

        Args:
            pattern: String with glob pattern

        Returns:
            List of absolute Path objects matching the pattern
        """
        base_path = Path(pattern).parent
        if not base_path.exists():
            return []

        glob_pattern = Path(pattern).name
        matches = []

        for entry in os.listdir(base_path):
            if fnmatch.fnmatch(entry, glob_pattern):
                full_path = (base_path / entry).resolve()
                matches.append(full_path)

        return sorted(matches)
