from _typeshed import StrPath
from threading import Thread
from typing import IO, Any, Dict

_Path = StrPath

def dictConfig(config: Dict[str, Any]) -> None: ...
def fileConfig(
    fname: str | IO[str],
    defaults: Dict[str, str] | None = ...,
    disable_existing_loggers: bool = ...,
) -> None: ...
def listen(port: int = ...) -> Thread: ...
def stopListening() -> None: ...
