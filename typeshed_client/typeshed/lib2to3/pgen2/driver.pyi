from _typeshed import StrPath
from lib2to3.pgen2.grammar import Grammar
from lib2to3.pytree import _NL, _Convert
from logging import Logger
from typing import IO, Any, Iterable

class Driver:
    grammar: Grammar
    logger: Logger
    convert: _Convert
    def __init__(
        self,
        grammar: Grammar,
        convert: _Convert | None = ...,
        logger: Logger | None = ...,
    ) -> None: ...
    def parse_tokens(self, tokens: Iterable[Any], debug: bool = ...) -> _NL: ...
    def parse_stream_raw(self, stream: IO[str], debug: bool = ...) -> _NL: ...
    def parse_stream(self, stream: IO[str], debug: bool = ...) -> _NL: ...
    def parse_file(
        self, filename: StrPath, encoding: str | None = ..., debug: bool = ...
    ) -> _NL: ...
    def parse_string(self, text: str, debug: bool = ...) -> _NL: ...

def load_grammar(
    gt: str = ...,
    gp: str | None = ...,
    save: bool = ...,
    force: bool = ...,
    logger: Logger | None = ...,
) -> Grammar: ...
