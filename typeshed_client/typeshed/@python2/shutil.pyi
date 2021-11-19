from _typeshed import SupportsRead, SupportsWrite
from typing import (
    Any,
    AnyStr,
    Callable,
    Iterable,
    List,
    Sequence,
    Set,
    Text,
    Tuple,
    Type,
    TypeVar,
    Union,
)

_AnyStr = TypeVar("_AnyStr", str, unicode)
_AnyPath = TypeVar("_AnyPath", str, unicode)
_PathReturn = Type[None]

class Error(EnvironmentError): ...
class SpecialFileError(EnvironmentError): ...
class ExecError(EnvironmentError): ...

def copyfileobj(
    fsrc: SupportsRead[AnyStr], fdst: SupportsWrite[AnyStr], length: int = ...
) -> None: ...
def copyfile(src: Text, dst: Text) -> None: ...
def copymode(src: Text, dst: Text) -> None: ...
def copystat(src: Text, dst: Text) -> None: ...
def copy(src: Text, dst: Text) -> _PathReturn: ...
def copy2(src: Text, dst: Text) -> _PathReturn: ...
def ignore_patterns(
    *patterns: Text,
) -> Callable[[Any, List[_AnyStr]], Set[_AnyStr]]: ...
def copytree(
    src: AnyStr,
    dst: AnyStr,
    symlinks: bool = ...,
    ignore: None | Callable[[AnyStr, List[AnyStr]], Iterable[AnyStr]] = ...,
) -> _PathReturn: ...
def rmtree(
    path: _AnyPath,
    ignore_errors: bool = ...,
    onerror: Callable[[Any, _AnyPath, Any], Any] | None = ...,
) -> None: ...

_CopyFn = Union[Callable[[str, str], None], Callable[[Text, Text], None]]

def move(src: Text, dst: Text) -> _PathReturn: ...
def make_archive(
    base_name: _AnyStr,
    format: str,
    root_dir: Text | None = ...,
    base_dir: Text | None = ...,
    verbose: bool = ...,
    dry_run: bool = ...,
    owner: str | None = ...,
    group: str | None = ...,
    logger: Any | None = ...,
) -> _AnyStr: ...
def get_archive_formats() -> List[Tuple[str, str]]: ...
def register_archive_format(
    name: str,
    function: Callable[..., Any],
    extra_args: Sequence[Tuple[str, Any] | List[Any]] | None = ...,
    description: str = ...,
) -> None: ...
def unregister_archive_format(name: str) -> None: ...
