"""This module is responsible for finding stub files."""
from pathlib import Path
import sys
from typed_ast import ast3
from typing import Iterable, Optional, Sequence, Tuple


def get_search_path(typeshed_dir: Path, pyversion: Tuple[int, int]) -> Tuple[Path]:
    # mirrors default_lib_path in mypy/build.py
    path = []  # type: List[str]

    versions = [f'{pyversion[0]}.{minor}' for minor in reversed(range(pyversion[1] + 1))]
    # E.g. for Python 3.2, try 3.2/, 3.1/, 3.0/, 3/, 2and3/.
    for version in versions + [str(pyversion[0]), '2and3']:
        for lib_type in ('stdlib', 'third_party'):
            stubdir = typeshed_dir / lib_type / version
            if stubdir.is_dir():
                path.append(stubdir)
    return tuple(path)


def get_stub_file_name(module_name: Sequence[str], search_path: Iterable[Path]) -> Optional[Path]:
    *dirs, tail = module_name
    for stubdir in search_path:
        for dirname in dirs:
            subdir = stubdir / dirname
            if subdir.is_dir():
                stubdir = subdir
            else:
                break

        filename = stubdir / f'{tail}.pyi'
        if filename.exists():
            return filename
        init_name = stubdir / tail / '__init__.pyi'
        if init_name.exists():
            return init_name
    else:
        return None


def find_typeshed() -> Path:
    # do we need more here? mypy has far more elaborate logic in mypy/build.py
    # maybe typeshed_client could also bundle typeshed itself instead of relying on mypy
    return Path(sys.prefix) / 'lib/mypy/typeshed'


def get_stub_file(module_name: str,
                  version: Tuple[int, int] = sys.version_info[:2]) -> Optional[Path]:
    """Returns the path to the stub file for this module, if any."""
    typeshed_dir = find_typeshed()
    search_path = get_search_path(typeshed_dir, version)
    return get_stub_file_name(tuple(module_name.split('.')), search_path)


def get_stub_ast(module_name: str,
                 version: Tuple[int, int] = sys.version_info[:2]) -> Optional[ast3.AST]:
    path = get_stub_file(module_name, version=version)
    if path is None:
        return None
    return parse_stub_file(path)


def parse_stub_file(path: Path) -> ast3.AST:
    text = path.read_text()
    # Always parse stubs as Python 3.6
    return ast3.parse(text, filename=str(path), feature_version=6)
