from typing import BinaryIO, Text, Union

_File = Union[Text, BinaryIO]

class Error(Exception): ...

def encode(
    in_file: _File, out_file: _File, name: str | None = ..., mode: int | None = ...
) -> None: ...
def decode(
    in_file: _File,
    out_file: _File | None = ...,
    mode: int | None = ...,
    quiet: int = ...,
) -> None: ...
