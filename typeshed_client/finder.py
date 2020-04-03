"""This module is responsible for finding stub files."""
from functools import lru_cache
import importlib_resources
import os
from pathlib import Path
import sys
from typed_ast import ast3
from typing import Iterable, List, Optional, Sequence, Set, Tuple


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
    module_name: Sequence[str], search_path: Iterable[Path]
) -> Optional[Path]:
    *dirs, tail = module_name
    for stubdir in search_path:
        filename = _find_file_in_stub_dir(dirs, tail, stubdir)
        if filename is not None:
            return filename
    else:
        return None


def _find_file_in_stub_dir(
    package_path: Sequence[str], module_name: str, stubdir: Path
) -> Optional[Path]:
    for dirname in package_path:
        subdir = stubdir / dirname
        if subdir.is_dir():
            stubdir = subdir
        else:
            return None

    filename = stubdir / f"{module_name}.pyi"
    if filename.exists():
        return filename
    init_name = stubdir / module_name / "__init__.pyi"
    if init_name.exists():
        return init_name
    return None


def find_typeshed() -> Path:
    # do we need more here? mypy has far more elaborate logic in mypy/build.py
    # maybe typeshed_client could also bundle typeshed itself instead of relying on mypy
    return importlib_resources.files("mypy") / "typeshed"


def get_stub_file(
    module_name: str,
    *,
    version: Tuple[int, int] = sys.version_info[:2],
    typeshed_dir: Optional[Path] = None,
) -> Optional[Path]:
    """Returns the path to the stub file for this module, if any."""
    if typeshed_dir is None:
        typeshed_dir = find_typeshed()
    search_path = get_search_path(typeshed_dir, version)
    return get_stub_file_name(tuple(module_name.split(".")), search_path)


def get_stub_ast(
    module_name: str,
    *,
    version: Tuple[int, int] = sys.version_info[:2],
    typeshed_dir: Optional[Path] = None,
) -> Optional[ast3.AST]:
    path = get_stub_file(module_name, version=version, typeshed_dir=typeshed_dir)
    if path is None:
        return None
    return parse_stub_file(path)


def parse_stub_file(path: Path) -> ast3.AST:
    text = path.read_text()
    # Always parse stubs as Python 3.6
    return ast3.parse(text, filename=str(path), feature_version=6)


def get_all_stub_files(
    version: Tuple[int, int] = sys.version_info[:2], typeshed_dir: Optional[Path] = None
) -> Iterable[Tuple[str, Path]]:
    """Returns paths to all stub files for a given Python version.

    Returns pairs of (module name, module path).

    """
    if typeshed_dir is None:
        typeshed_dir = find_typeshed()
    seen: Set[Path] = set()
    for path in get_search_path(typeshed_dir, version):
        # submitting PR to typeshed to fix os.walk
        for root, _, files in os.walk(path):  # type: ignore
            for file in files:
                full_path = Path(root) / file
                relative_path = full_path.relative_to(path)
                if full_path.suffix != ".pyi":
                    continue
                if relative_path in seen:
                    continue
                yield _path_to_module(relative_path), full_path
                seen.add(relative_path)


def _path_to_module(path: Path) -> str:
    """Returns the module name corresponding to a file path."""
    parts = path.parts
    if parts[-1] == "__init__.pyi":
        parts = parts[:-1]
    if parts[-1].endswith(".pyi"):
        parts = parts[:-1] + (parts[-1][: -len(".pyi")],)
    return ".".join(parts)
