from types import ModuleType
from typing import Any, Mapping, Sequence

WINEXE: bool
WINSERVICE: bool

def set_executable(exe: str) -> None: ...
def get_executable() -> str: ...
def is_forking(argv: Sequence[str]) -> bool: ...
def freeze_support() -> None: ...
def get_command_line(**kwds: Any) -> list[str]: ...
def spawn_main(
    pipe_handle: int, parent_pid: int | None = ..., tracker_fd: int | None = ...
) -> None: ...

# undocumented
def _main(fd: int) -> Any: ...
def get_preparation_data(name: str) -> dict[str, Any]: ...

old_main_modules: list[ModuleType]

def prepare(data: Mapping[str, Any]) -> None: ...
def import_main_path(main_path: str) -> None: ...
