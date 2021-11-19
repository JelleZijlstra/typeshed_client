from _typeshed import StrOrBytesPath
from types import FrameType, TracebackType
from typing import IO, Any, Callable, Optional, Tuple, Type

_ExcInfo = Tuple[
    Optional[Type[BaseException]], Optional[BaseException], Optional[TracebackType]
]

def reset() -> str: ...  # undocumented
def small(text: str) -> str: ...  # undocumented
def strong(text: str) -> str: ...  # undocumented
def grey(text: str) -> str: ...  # undocumented
def lookup(
    name: str, frame: FrameType, locals: dict[str, Any]
) -> tuple[str | None, Any]: ...  # undocumented
def scanvars(
    reader: Callable[[], bytes], frame: FrameType, locals: dict[str, Any]
) -> list[tuple[str, str | None, Any]]: ...  # undocumented
def html(einfo: _ExcInfo, context: int = ...) -> str: ...
def text(einfo: _ExcInfo, context: int = ...) -> str: ...

class Hook:  # undocumented
    def __init__(
        self,
        display: int = ...,
        logdir: StrOrBytesPath | None = ...,
        context: int = ...,
        file: IO[str] | None = ...,
        format: str = ...,
    ) -> None: ...
    def __call__(
        self,
        etype: Type[BaseException] | None,
        evalue: BaseException | None,
        etb: TracebackType | None,
    ) -> None: ...
    def handle(self, info: _ExcInfo | None = ...) -> None: ...

def handler(info: _ExcInfo | None = ...) -> None: ...
def enable(
    display: int = ...,
    logdir: StrOrBytesPath | None = ...,
    context: int = ...,
    format: str = ...,
) -> None: ...
