from typing import IO, Any, Callable, Sequence, Union

_Timer = Callable[[], float]
_Stmt = Union[str, Callable[[], Any]]

default_timer: _Timer

class Timer:
    def __init__(
        self,
        stmt: _Stmt = ...,
        setup: _Stmt = ...,
        timer: _Timer = ...,
        globals: dict[str, Any] | None = ...,
    ) -> None: ...
    def print_exc(self, file: IO[str] | None = ...) -> None: ...
    def timeit(self, number: int = ...) -> float: ...
    def repeat(self, repeat: int = ..., number: int = ...) -> list[float]: ...
    def autorange(
        self, callback: Callable[[int, float], Any] | None = ...
    ) -> tuple[int, float]: ...

def timeit(
    stmt: _Stmt = ...,
    setup: _Stmt = ...,
    timer: _Timer = ...,
    number: int = ...,
    globals: dict[str, Any] | None = ...,
) -> float: ...
def repeat(
    stmt: _Stmt = ...,
    setup: _Stmt = ...,
    timer: _Timer = ...,
    repeat: int = ...,
    number: int = ...,
    globals: dict[str, Any] | None = ...,
) -> list[float]: ...

_timerFunc = Callable[[], float]

def main(
    args: Sequence[str] | None = ...,
    *,
    _wrap_timer: Callable[[_timerFunc], _timerFunc] | None = ...,
) -> None: ...
