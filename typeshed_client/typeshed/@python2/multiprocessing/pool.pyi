from typing import Any, Callable, Dict, Iterable, Iterator, List, TypeVar

_T = TypeVar("_T", bound=Pool)

class AsyncResult:
    def get(self, timeout: float | None = ...) -> Any: ...
    def wait(self, timeout: float | None = ...) -> None: ...
    def ready(self) -> bool: ...
    def successful(self) -> bool: ...

class IMapIterator(Iterator[Any]):
    def __iter__(self) -> Iterator[Any]: ...
    def next(self, timeout: float | None = ...) -> Any: ...

class IMapUnorderedIterator(IMapIterator): ...

class Pool(object):
    def __init__(
        self,
        processes: int | None = ...,
        initializer: Callable[..., None] | None = ...,
        initargs: Iterable[Any] = ...,
        maxtasksperchild: int | None = ...,
    ) -> None: ...
    def apply(
        self,
        func: Callable[..., Any],
        args: Iterable[Any] = ...,
        kwds: Dict[str, Any] = ...,
    ) -> Any: ...
    def apply_async(
        self,
        func: Callable[..., Any],
        args: Iterable[Any] = ...,
        kwds: Dict[str, Any] = ...,
        callback: Callable[..., None] | None = ...,
    ) -> AsyncResult: ...
    def map(
        self,
        func: Callable[..., Any],
        iterable: Iterable[Any] = ...,
        chunksize: int | None = ...,
    ) -> List[Any]: ...
    def map_async(
        self,
        func: Callable[..., Any],
        iterable: Iterable[Any] = ...,
        chunksize: int | None = ...,
        callback: Callable[..., None] | None = ...,
    ) -> AsyncResult: ...
    def imap(
        self,
        func: Callable[..., Any],
        iterable: Iterable[Any] = ...,
        chunksize: int | None = ...,
    ) -> IMapIterator: ...
    def imap_unordered(
        self,
        func: Callable[..., Any],
        iterable: Iterable[Any] = ...,
        chunksize: int | None = ...,
    ) -> IMapIterator: ...
    def close(self) -> None: ...
    def terminate(self) -> None: ...
    def join(self) -> None: ...

class ThreadPool(Pool):
    def __init__(
        self,
        processes: int | None = ...,
        initializer: Callable[..., Any] | None = ...,
        initargs: Iterable[Any] = ...,
    ) -> None: ...
