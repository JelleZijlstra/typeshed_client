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

if sys.version_info >= (3, 10):
    __all__.append("f")
else:
    __all__.append("g")

f: int
g: int

if sys.version_info >= (3, 10):
    __all__.extend(["h"])
else:
    __all__.extend(["i"])

h: int
i: int
