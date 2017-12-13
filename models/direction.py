from enum import Enum
from typing import Tuple, Iterable

class Direction(Enum):
    N = (0, -1)
    NE = (1, -1)
    E = (1, 0)
    SE = (1, 1)
    S = (0, 1)
    SW = (-1, 1)
    W = (-1, 0)
    NW = (-1, -1)

    @staticmethod
    def basic() -> Iterable['Direction']:
        return (d for d in Direction if not all(d.value))

    @staticmethod
    def diagonal() -> Iterable['Direction']:
        return (d for d in Direction if all(d.value))
