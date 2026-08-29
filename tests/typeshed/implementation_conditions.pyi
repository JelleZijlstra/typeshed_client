import sys

if sys.implementation.name == "pypy":
    pypy_name: int
else:
    other_name: int

if sys.implementation.version >= (7, 3):
    recent_implementation: int
else:
    old_implementation: int

if sys.platform.startswith("freebsd"):
    freebsd_platform: int

if sys.platform in {"linux", "freebsd13"}:
    selected_platform: int

if not sys.platform == "win32":
    non_windows_platform: int
