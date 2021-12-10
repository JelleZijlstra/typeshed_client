"""This module is responsible for finding stub files."""
from functools import lru_cache
import importlib_resources
import json
import os
from pathlib import Path
import subprocess
import sys
from typed_ast import ast3
from typing import (
    Dict,
    Generator,
    Iterable,
    List,
    NamedTuple,
    NewType,
    Optional,
    Sequence,
    Set,
    Tuple,
)

PythonVersion = Tuple[int, int]
ModulePath = NewType("ModulePath", Tuple[str, ...])


class SearchContext(NamedTuple):
    typeshed: Path
    search_path: Sequence[Path]
    version: PythonVersion
    platform: str

    def is_python2(self) -> bool:
        return self.version[0] == 2


def get_search_context(
    *,
    typeshed: Optional[Path] = None,
    search_path: Optional[Sequence[Path]] = None,
    python_executable: Optional[str] = None,
    version: Optional[PythonVersion] = None,
    platform: str = sys.platform,
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
        typeshed=typeshed, search_path=search_path, version=version, platform=platform
    )


def get_stub_file(
    module_name: str, *, search_context: Optional[SearchContext] = None
) -> Optional[Path]:
    """Return the path to the stub file for this module, if any."""
    if search_context is None:
        search_context = get_search_context()
    return get_stub_file_name(tuple(module_name.split(".")), search_context)


def get_stub_ast(
    module_name: str, *, search_context: Optional[SearchContext] = None
) -> Optional[ast3.AST]:
    """Return the AST for the stub for the given module name."""
    path = get_stub_file(module_name, search_context=search_context)
    if path is None:
        return None
    return parse_stub_file(path)


def get_all_stub_files(
    search_context: Optional[SearchContext] = None,
) -> Iterable[Tuple[str, Path]]:
    """Return paths to all stub files for a given Python version.

    Return pairs of (module name, module path).

    """
    if search_context is None:
        search_context = get_search_context()

    seen: Set[str] = set()
    # third-party packages
    for stub_packages in (True, False):
        for search_path_entry in search_context.search_path:
            if not search_path_entry.exists():
                continue
            for directory in os.scandir(search_path_entry):
                if not directory.is_dir():
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
        for entry in os.scandir(typeshed_dir):
            if entry.is_dir() and entry.name.isidentifier():
                module_name = entry.name
            elif entry.is_file() and entry.name.endswith(".pyi"):
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
            if entry.is_dir():
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
    directory: os.DirEntry, root_directory: Path, seen: Set[str]
) -> Generator[Tuple[str, Path], None, Set[str]]:
    new_seen = set(seen)
    to_do: Set[os.PathLike[str]] = {directory}
    while to_do:
        directory = to_do.pop()
        for dir_entry in os.scandir(directory):
            if dir_entry.is_dir():
                if not dir_entry.name.isidentifier():
                    continue
                path = Path(dir_entry)
                if (path / "__init__.pyi").is_file() or (
                    path / "__init__.py"
                ).is_file():
                    to_do.add(path)
            elif dir_entry.is_file():
                path = Path(dir_entry)
                if path.suffix != ".pyi":
                    continue
                module_name = _path_to_module(path.relative_to(root_directory))
                if module_name in new_seen:
                    continue
                yield (module_name, path)
                new_seen.add(module_name)
    return new_seen


@lru_cache()
def get_search_path(typeshed_dir: Path, pyversion: Tuple[int, int]) -> Tuple[Path, ...]:
    # mirrors default_lib_path in mypy/build.py
    path: List[Path] = []

    versions = [
        f"{pyversion[0]}.{minor}" for minor in reversed(range(pyversion[1] + 1))
    ]
    # E.g. for Python 3.2, try 3.2/, 3.1/, 3.0/, 3/, 2and3/.
    for version in versions + [str(pyversion[0]), "2and3"]:
        for lib_type in ("stdlib", "third_party"):
            stubdir = typeshed_dir / lib_type / version
            if stubdir.is_dir():
                path.append(stubdir)
    return tuple(path)


def get_stub_file_name(
    module_name: ModulePath, search_context: SearchContext
) -> Optional[Path]:
    # https://www.python.org/dev/peps/pep-0561/#type-checker-module-resolution-order
    # typeshed_client doesn't support 1 (MYPYPATH equivalent) and 2 (user code)
    top_level_name, *rest = module_name

    # 3. stub packages
    stubs_package = f"{top_level_name}-stubs"
    for path in search_context.search_path:
        stubdir = path / stubs_package
        if stubdir.exists():
            stub = _find_stub_in_dir(stubdir, rest)
            if stub is not None:
                return stub

    # 4. stubs in normal packages
    for path in search_context.search_path:
        stubdir = path / top_level_name
        if stubdir.exists():
            stub = _find_stub_in_dir(stubdir, rest)
            if stub is not None:
                return stub

    # 5. typeshed
    versions = get_typeshed_versions(search_context.typeshed)
    if top_level_name not in versions:
        return None
    version = versions[top_level_name]
    if search_context.version < version.min:
        return None
    if version.max is not None and search_context.version > version.max:
        return None

    if search_context.version[0] == 2:
        python2_dir = search_context.typeshed / "@python2"
        stub = _find_stub_in_dir(python2_dir, module_name)
        if stub is not None or version.in_python2:
            return stub

    return _find_stub_in_dir(search_context.typeshed, module_name)


class _VersionData(NamedTuple):
    min: PythonVersion
    max: Optional[PythonVersion]
    # whether it is present in @python2
    in_python2: bool


@lru_cache()
def get_typeshed_versions(typeshed: Path) -> Dict[str, _VersionData]:
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
            if max_version_str:
                max_version = _parse_version(max_version_str)
            else:
                max_version = None
            min_version = _parse_version(min_version_str)
            python2_only = module in python2_files or module + ".pyi" in python2_files
            versions[module] = _VersionData(min_version, max_version, python2_only)
    return versions


def _parse_version(version: str) -> PythonVersion:
    major, minor = version.split(".")
    return (int(major), int(minor))


def _find_stub_in_dir(stubdir: Path, module: ModulePath) -> Optional[Path]:
    if not module:
        init_name = stubdir / "__init__.pyi"
        if init_name.exists():
            return init_name
        return None
    if len(module) == 1:
        stub_name = stubdir / f"{module[0]}.pyi"
        if stub_name.exists():
            return stub_name
    next_name, *rest = module
    next_dir = stubdir / next_name
    if next_dir.exists():
        return _find_stub_in_dir(next_dir, rest)
    return None


def find_typeshed() -> Path:
    return importlib_resources.files("typeshed_client") / "typeshed"


def parse_stub_file(path: Path) -> ast3.AST:
    text = path.read_text()
    # Always parse stubs as Python 3.6
    return ast3.parse(text, filename=str(path), feature_version=6)


def _path_to_module(path: Path) -> str:
    """Returns the module name corresponding to a file path."""
    parts = path.parts
    if parts[-1] == "__init__.pyi":
        parts = parts[:-1]
    if parts[-1].endswith(".pyi"):
        parts = parts[:-1] + (parts[-1][: -len(".pyi")],)
    return ".".join(parts).replace("-stubs", "")
