from typing import IO, Any, Callable, List, Sequence, Text, Union

_str = Union[str, Text]
_Timer = Callable[[], float]
_stmt = Union[_str, Callable[[], Any]]

default_timer: _Timer

class Timer:
    def __init__(
        self, stmt: _stmt = ..., setup: _stmt = ..., timer: _Timer = ...
    ) -> None: ...
    def print_exc(self, file: IO[str] | None = ...) -> None: ...
    def timeit(self, number: int = ...) -> float: ...
    def repeat(self, repeat: int = ..., number: int = ...) -> List[float]: ...

def timeit(
    stmt: _stmt = ..., setup: _stmt = ..., timer: _Timer = ..., number: int = ...
) -> float: ...
def repeat(
    stmt: _stmt = ...,
    setup: _stmt = ...,
    timer: _Timer = ...,
    repeat: int = ...,
    number: int = ...,
) -> List[float]: ...

_timerFunc = Callable[[], float]

def main(
    args: Sequence[str] | None = ...,
    *,
    _wrap_timer: Callable[[_timerFunc], _timerFunc] | None = ...,
) -> None: ...
