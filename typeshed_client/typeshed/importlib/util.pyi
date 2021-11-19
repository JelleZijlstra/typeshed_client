import importlib.abc
import importlib.machinery
import types
from _typeshed import StrOrBytesPath
from typing import Any, Callable
from typing_extensions import ParamSpec

_P = ParamSpec("_P")

def module_for_loader(fxn: Callable[_P, types.ModuleType]) -> Callable[_P, types.ModuleType]: ...  # type: ignore
def set_loader(fxn: Callable[_P, types.ModuleType]) -> Callable[_P, types.ModuleType]: ...  # type: ignore
def set_package(fxn: Callable[_P, types.ModuleType]) -> Callable[_P, types.ModuleType]: ...  # type: ignore
def resolve_name(name: str, package: str | None) -> str: ...

MAGIC_NUMBER: bytes

def cache_from_source(
    path: str, debug_override: bool | None = ..., *, optimization: Any | None = ...
) -> str: ...
def source_from_cache(path: str) -> str: ...
def decode_source(source_bytes: bytes) -> str: ...
def find_spec(
    name: str, package: str | None = ...
) -> importlib.machinery.ModuleSpec | None: ...
def spec_from_loader(
    name: str,
    loader: importlib.abc.Loader | None,
    *,
    origin: str | None = ...,
    is_package: bool | None = ...,
) -> importlib.machinery.ModuleSpec | None: ...
def spec_from_file_location(
    name: str,
    location: StrOrBytesPath | None = ...,
    *,
    loader: importlib.abc.Loader | None = ...,
    submodule_search_locations: list[str] | None = ...,
) -> importlib.machinery.ModuleSpec | None: ...
def module_from_spec(spec: importlib.machinery.ModuleSpec) -> types.ModuleType: ...

class LazyLoader(importlib.abc.Loader):
    def __init__(self, loader: importlib.abc.Loader) -> None: ...
    @classmethod
    def factory(cls, loader: importlib.abc.Loader) -> Callable[..., LazyLoader]: ...
    def create_module(
        self, spec: importlib.machinery.ModuleSpec
    ) -> types.ModuleType | None: ...
    def exec_module(self, module: types.ModuleType) -> None: ...
