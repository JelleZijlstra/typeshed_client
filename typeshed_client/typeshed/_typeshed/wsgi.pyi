# Types to support PEP 3333 (WSGI)
#
# See the README.md file in this directory for more information.

from sys import _OptExcInfo
from typing import Any, Callable, Dict, Iterable, Protocol

# stable
class StartResponse(Protocol):
    def __call__(
        self,
        status: str,
        headers: list[tuple[str, str]],
        exc_info: _OptExcInfo | None = ...,
    ) -> Callable[[bytes], Any]: ...

WSGIEnvironment = Dict[str, Any]  # stable
WSGIApplication = Callable[[WSGIEnvironment, StartResponse], Iterable[bytes]]  # stable

# WSGI input streams per PEP 3333, stable
class InputStream(Protocol):
    def read(self, size: int = ...) -> bytes: ...
    def readline(self, size: int = ...) -> bytes: ...
    def readlines(self, hint: int = ...) -> list[bytes]: ...
    def __iter__(self) -> Iterable[bytes]: ...

# WSGI error streams per PEP 3333, stable
class ErrorStream(Protocol):
    def flush(self) -> None: ...
    def write(self, s: str) -> None: ...
    def writelines(self, seq: list[str]) -> None: ...

class _Readable(Protocol):
    def read(self, size: int = ...) -> bytes: ...

# Optional file wrapper in wsgi.file_wrapper
class FileWrapper(Protocol):
    def __call__(self, file: _Readable, block_size: int = ...) -> Iterable[bytes]: ...
