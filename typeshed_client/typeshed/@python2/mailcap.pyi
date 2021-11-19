from typing import Dict, List, Mapping, Sequence, Tuple, Union

_Cap = Dict[str, Union[str, int]]

def findmatch(
    caps: Mapping[str, List[_Cap]],
    MIMEtype: str,
    key: str = ...,
    filename: str = ...,
    plist: Sequence[str] = ...,
) -> Tuple[str | None, _Cap | None]: ...
def getcaps() -> Dict[str, List[_Cap]]: ...
