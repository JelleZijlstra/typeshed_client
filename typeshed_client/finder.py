"""This module is responsible for finding stub files."""

import ast
import json
import os
import subprocess
import sys
from collections.abc import Generator, Iterable, Sequence
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple, NewType, Optional, Union

import importlib_resources
from typing_extensions import deprecated

PythonVersion = tuple[int, int]
ModulePath = NewType("ModulePath", tuple[str, ...])

_INIT_NAMES = ("__init__.pyi", "__init__.py")
_EXTENSIONS = (".pyi", ".py")


if TYPE_CHECKING:
    _DirEntry = os.DirEntry[str]
else:
    _DirEntry = os.DirEntry


class SearchContext(NamedTuple):
    typeshed: Path
    search_path: Sequence[Path]
    version: PythonVersion
    platform: str
    raise_on_warnings: bool = False
    allow_py_files: bool = False

    def is_python2(self) -> bool:
        return self.version[0] == 2


def get_search_context(
    *,
    typeshed: Optional[Path] = None,
    search_path: Optional[Sequence[Path]] = None,
    python_executable: Optional[str] = None,
    version: Optional[PythonVersion] = None,
    platform: str = sys.platform,
    raise_on_warnings: bool = False,
    allow_py_files: bool = False,
) -> SearchContext:
    """Return a context for finding stubs. This context can be passed to other
    functions in this file.

    Arguments:
    - typeshed: Path to typeshed. If this is not given, typeshed_client's own
      bundled copy of typeshed is used.
    - search_path: Sequence of directories in which to search for stubs. If this
      is not given, ``sys.path`` is used.
    - python_executable: Path to a Python executable that should be used to
      find the search_path. The default is to use ``sys.executable``.
    - version: Version of Python to use, as a two-tuple like (3, 9).
    - platform: Value to use for sys.platform in stubs, defaulting to the current
      process's value.
    - raise_on_warnings: Raise an error for any warnings encountered by the parser.
    - allow_py_files: Search for names in .py files on the path.

    """
    if version is None:
        version = sys.version_info[:2]
    if search_path is None:
        if python_executable is None:
            python_executable = sys.executable
        raw_path = subprocess.check_output(
            [python_executable, "-c", "import sys, json; print(json.dumps(sys.path))"]
        )
        search_path = [Path(path) for path in json.loads(raw_path) if path]
    else:
        if python_executable is not None:
            raise ValueError("python_executable is ignored if search_path is given")
    if typeshed is None:
        typeshed = find_typeshed()
    return SearchContext(
        typeshed=typeshed,
        search_path=search_path,
        version=version,
        platform=platform,
        raise_on_warnings=raise_on_warnings,
        allow_py_files=allow_py_files,
    )


def get_stub_file(
    module_name: str, *, search_context: Optional[SearchContext] = None
) -> Optional[Path]:
    """Return the path to the stub file for this module, if any."""
    if search_context is None:
        search_context = get_search_context()
    return get_stub_file_name(ModulePath(tuple(module_name.split("."))), search_context)


def get_stub_ast(
    module_name: str, *, search_context: Optional[SearchContext] = None
) -> Optional[ast.Module]:
    """Return the AST for the stub for the given module name."""
    path = get_stub_file(module_name, search_context=search_context)
    if path is None:
        return None
    return parse_stub_file(path)


def get_all_stub_files(
    search_context: Optional[SearchContext] = None,
) -> Iterable[tuple[str, Path]]:
    """Return paths to all stub files for a given Python version.

    Return pairs of (module name, module path).

    """
    if search_context is None:
        search_context = get_search_context()

    seen: set[str] = set()
    # third-party packages
    for stub_packages in (True, False):
        for search_path_entry in search_context.search_path:
            if not safe_exists(search_path_entry):
                continue
            for directory in safe_scandir(search_path_entry):
                if not safe_is_dir(directory):
                    continue
                condition = (
                    directory.name.endswith("-stubs")
                    if stub_packages
                    else directory.name.isidentifier()
                )
                if not condition:
                    continue
                seen = yield from _get_all_stub_files_from_directory(
                    directory, search_path_entry, seen
                )

    # typeshed
    versions = get_typeshed_versions(search_context.typeshed)
    typeshed_dirs = [search_context.typeshed]
    if search_context.is_python2():
        typeshed_dirs.insert(0, search_context.typeshed / "@python2")

    for typeshed_dir in typeshed_dirs:
        for entry in safe_scandir(typeshed_dir):
            if safe_is_dir(entry) and entry.name.isidentifier():
                module_name = entry.name
            elif safe_is_file(entry) and entry.name.endswith(".pyi"):
                module_name = entry.name[: -len(".pyi")]
            else:
                continue
            version = versions[module_name]
            if search_context.version < version.min:
                continue
            if version.max is not None and search_context.version > version.max:
                continue
            if (
                search_context.is_python2()
                and typeshed_dir.name != "@python2"
                and version.in_python2
            ):
                continue
            if safe_is_dir(entry):
                seen = yield from _get_all_stub_files_from_directory(
                    entry, typeshed_dir, seen
                )
            else:
                path = Path(entry)
                module_name = _path_to_module(path.relative_to(typeshed_dir))
                if module_name in seen:
                    continue
                yield (module_name, path)
                seen.add(module_name)


def _get_all_stub_files_from_directory(
    directory: _DirEntry, root_directory: Path, seen: set[str]
) -> Generator[tuple[str, Path], None, set[str]]:
    new_seen = set(seen)
    to_do: list[os.PathLike[str]] = [directory]
    while to_do:
        current_dir = to_do.pop()
        for dir_entry in safe_scandir(current_dir):
            if safe_is_dir(dir_entry):
                if not dir_entry.name.isidentifier():
                    continue
                path = Path(dir_entry)
                if any(safe_is_file(path / init) for init in _INIT_NAMES):
                    to_do.append(path)
            elif safe_is_file(dir_entry):
                path = Path(dir_entry)
                if path.suffix != ".pyi":
                    continue
                module_name = _path_to_module(path.relative_to(root_directory))
                if module_name in new_seen:
                    continue
                yield (module_name, path)
                new_seen.add(module_name)
    return new_seen


@lru_cache
@deprecated(
    "This function is not useful with the current layout of typeshed. "
    "It may be removed from a future version of typeshed-client."
)
def get_search_path(typeshed_dir: Path, pyversion: tuple[int, int]) -> tuple[Path, ...]:
    # mirrors default_lib_path in mypy/build.py
    path: list[Path] = []

    versions = [
        f"{pyversion[0]}.{minor}" for minor in reversed(range(pyversion[1] + 1))
    ]
    # E.g. for Python 3.2, try 3.2/, 3.1/, 3.0/, 3/, 2and3/.
    for version in [*versions, str(pyversion[0]), "2and3"]:
        for lib_type in ("stdlib", "third_party"):
            stubdir = typeshed_dir / lib_type / version
            if safe_is_dir(stubdir):
                path.append(stubdir)
    return tuple(path)


def safe_exists(path: Path) -> bool:
    """Return whether a path exists, assuming it doesn't if we get an error."""
    try:
        return path.exists()
    except OSError:
        return False


def safe_is_dir(path: Union[Path, _DirEntry]) -> bool:
    """Return whether a path is a directory, assuming it isn't if we get an error."""
    try:
        return path.is_dir()
    except OSError:
        return False


def safe_is_file(path: Union[Path, _DirEntry]) -> bool:
    """Return whether a path is a file, assuming it isn't if we get an error."""
    try:
        return path.is_file()
    except OSError:
        return False


def safe_scandir(path: "os.PathLike[str]") -> Iterable[_DirEntry]:
    """Return an iterator over the entries in a directory, or no entries if we get an error."""
    try:
        with os.scandir(path) as sd:
            yield from sd
    except OSError:
        pass


def get_stub_file_name(
    module_name: ModulePath, search_context: SearchContext
) -> Optional[Path]:
    # https://typing.python.org/en/latest/spec/distributing.html#import-resolution-ordering
    # typeshed_client doesn't support 1 (MYPYPATH equivalent) and 2 (user code)
    top_level_name, *rest = module_name
    rest_module_path = ModulePath(tuple(rest))

    # 3. typeshed
    stub = _find_stub_in_typeshed(module_name, search_context)
    if stub is not None:
        return stub

    # 4. stub packages
    stubs_package = f"{top_level_name}-stubs"
    for path in search_context.search_path:
        stubdir = path / stubs_package
        if safe_exists(stubdir):
            stub = _find_file_in_dir(stubdir, rest_module_path, "pyi")
            if stub is not None:
                return stub

    # 5. stubs or .py files in normal packages
    for path in search_context.search_path:
        stubdir = path / top_level_name
        if safe_exists(stubdir):
            stub = _find_file_in_dir(stubdir, rest_module_path, "pyi")
            if stub is not None:
                return stub
            if search_context.allow_py_files:
                py_file = _find_file_in_dir(stubdir, rest_module_path, "py")
                if py_file is not None:
                    return py_file

    return None


def _find_stub_in_typeshed(
    module_name: ModulePath, search_context: SearchContext
) -> Optional[Path]:
    versions = get_typeshed_versions(search_context.typeshed)
    top_level_name = module_name[0]
    if top_level_name not in versions:
        return None
    version = versions[top_level_name]
    if search_context.version < version.min:
        return None
    if version.max is not None and search_context.version > version.max:
        return None

    if search_context.version[0] == 2:
        python2_dir = search_context.typeshed / "@python2"
        stub = _find_file_in_dir(python2_dir, module_name, "pyi")
        if stub is not None or version.in_python2:
            return stub

    return _find_file_in_dir(search_context.typeshed, module_name, "pyi")


class _VersionData(NamedTuple):
    min: PythonVersion
    max: Optional[PythonVersion]
    # whether it is present in @python2
    in_python2: bool


@lru_cache
def get_typeshed_versions(typeshed: Path) -> dict[str, _VersionData]:
    versions = {}
    try:
        python2_files = set(os.listdir(typeshed / "@python2"))
    except FileNotFoundError:
        python2_files = set()
    with (typeshed / "VERSIONS").open() as f:
        for line in f:
            line = line.split("#")[0].strip()
            if not line:
                continue
            module, version = line.split(": ")
            if "-" in version:
                min_version_str, max_version_str = version.split("-")
            else:
                min_version_str = version
                max_version_str = None
            max_version = _parse_version(max_version_str) if max_version_str else None
            min_version = _parse_version(min_version_str)
            python2_only = module in python2_files or module + ".pyi" in python2_files
            versions[module] = _VersionData(min_version, max_version, python2_only)
    return versions


def _parse_version(version: str) -> PythonVersion:
    major, minor = version.split(".")
    return (int(major), int(minor))


def _find_file_in_dir(
    stubdir: Path, module: ModulePath, extension: str
) -> Optional[Path]:
    if not module:
        init_name = stubdir / f"__init__.{extension}"
        if safe_exists(init_name):
            return init_name
        return None
    if len(module) == 1:
        stub_name = stubdir / f"{module[0]}.{extension}"
        if safe_exists(stub_name):
            return stub_name
    next_name, *rest = module
    next_dir = stubdir / next_name
    if safe_exists(next_dir):
        return _find_file_in_dir(next_dir, ModulePath(tuple(rest)), extension)
    return None


def find_typeshed() -> Path:
    return importlib_resources.files("typeshed_client") / "typeshed"


def parse_stub_file(path: Path) -> ast.Module:
    text = path.read_text(encoding="utf-8")
    return ast.parse(text, filename=str(path))


def _path_to_module(path: Path) -> str:
    """Returns the module name corresponding to a file path."""
    parts = path.parts
    if parts[-1] in _INIT_NAMES:
        parts = parts[:-1]
    for suffix in _EXTENSIONS:
        if parts[-1].endswith(suffix):
            parts = (*parts[:-1], parts[-1][: -len(suffix)])
            break
    return ".".join(parts).replace("-stubs", "")
