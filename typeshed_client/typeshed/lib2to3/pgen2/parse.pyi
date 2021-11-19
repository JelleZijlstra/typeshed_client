from lib2to3.pgen2.grammar import _DFAS, Grammar
from lib2to3.pytree import _NL, _Convert, _RawNode
from typing import Any, Sequence, Set

_Context = Sequence[Any]

class ParseError(Exception):
    msg: str
    type: int
    value: str | None
    context: _Context
    def __init__(
        self, msg: str, type: int, value: str | None, context: _Context
    ) -> None: ...

class Parser:
    grammar: Grammar
    convert: _Convert
    stack: list[tuple[_DFAS, int, _RawNode]]
    rootnode: _NL | None
    used_names: Set[str]
    def __init__(self, grammar: Grammar, convert: _Convert | None = ...) -> None: ...
    def setup(self, start: int | None = ...) -> None: ...
    def addtoken(self, type: int, value: str | None, context: _Context) -> bool: ...
    def classify(self, type: int, value: str | None, context: _Context) -> int: ...
    def shift(
        self, type: int, value: str | None, newstate: int, context: _Context
    ) -> None: ...
    def push(
        self, type: int, newdfa: _DFAS, newstate: int, context: _Context
    ) -> None: ...
    def pop(self) -> None: ...
