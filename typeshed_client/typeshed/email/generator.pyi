from email.message import Message
from email.policy import Policy
from typing import BinaryIO, TextIO

class Generator:
    def clone(self, fp: TextIO) -> Generator: ...
    def write(self, s: str) -> None: ...
    def __init__(
        self,
        outfp: TextIO,
        mangle_from_: bool | None = ...,
        maxheaderlen: int | None = ...,
        *,
        policy: Policy | None = ...,
    ) -> None: ...
    def flatten(
        self, msg: Message, unixfrom: bool = ..., linesep: str | None = ...
    ) -> None: ...

class BytesGenerator:
    def clone(self, fp: BinaryIO) -> BytesGenerator: ...
    def write(self, s: str) -> None: ...
    def __init__(
        self,
        outfp: BinaryIO,
        mangle_from_: bool | None = ...,
        maxheaderlen: int | None = ...,
        *,
        policy: Policy | None = ...,
    ) -> None: ...
    def flatten(
        self, msg: Message, unixfrom: bool = ..., linesep: str | None = ...
    ) -> None: ...

class DecodedGenerator(Generator):
    def __init__(
        self,
        outfp: TextIO,
        mangle_from_: bool | None = ...,
        maxheaderlen: int | None = ...,
        fmt: str | None = ...,
        *,
        policy: Policy | None = ...,
    ) -> None: ...
