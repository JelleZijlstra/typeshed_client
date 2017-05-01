import sys

if sys.platform == 'win32':
    windows: int
elif sys.platform == 'darwin':
    apples: int
else:
    penguins: int

if sys.version_info >= (3, 6):
    async_generator: int
elif sys.version_info >= (3, 5):
    typing: int
elif sys.version_info >= (3, 4):
    asyncio: int
elif sys.version_info >= (3, 3):
    yield_from: int
else:
    ages_long_past: int

if sys.version_info < (3, 0):
    old_stuff: int
else:
    new_stuff: int

if sys.version_info[0] == 2:
    more_old_stuff: int
