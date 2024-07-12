try:
    import numpy as np

    def f(x: np.int64) -> np.int64: ...

except ImportError:
    pass
finally:
    x: int
