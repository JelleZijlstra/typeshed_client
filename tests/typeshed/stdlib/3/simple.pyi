import other
from other import unexported, exported as exported, renamed as new_name, made_private as _made_private

_private: int

var: int
old_var = ...  # type: int
multiple = assignment = exported

def func() -> None: ...
async def async_func() -> None: ...

class Cls:
    attr: int
    def method(self) -> None: ...
