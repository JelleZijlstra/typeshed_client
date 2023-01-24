import sys

__all__ = ["a", "b"]

if sys.version_info >= (3, 10):
    __all__ += ["c"]
else:
    __all__ += ["d"]

a: int
b: int
c: int
d: int
e: int
