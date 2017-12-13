from collections import namedtuple
import gettext

from typing import Tuple, List
from cerberus import ValidationError

from helpers.validation import validate
from models.direction import Direction

_ = lambda s: s

class Position(namedtuple('Position', 'col row')):
    """Position of an object on the screen."""

    SCREEN_W = 79
    SCREEN_H = 21

    def neighbors(self, with_diagonals: bool=False):
        """Returns all neighboring positions.

        :param with_diagonals: includes diagonal neighbors"""
        directions = (
            (d.value for d in Direction) 
            if with_diagonals 
            else (d.value for d in Direction.basic())
        )
        for dc, dr in directions:
            try:
                yield position(self.col + dc, self.row + dr)
            except ValidationError:
                continue

    def __add__(self, other) -> 'Position':
        return Position(self.col + other[0], self.row + other[1])

    def __sub__(self, other) -> 'Position':
        return Position(self.col - other[0], self.row - other[1])

    def __repr__(self):
        return "<Position (%i, %i)>" % (self.col, self.row)

#@validate({
#    1: {'type': 'integer', 'min': 0, 'max': Position.SCREEN_W},
#    2: {'type': 'integer', 'min': 0, 'max': Position.SCREEN_H},
#})
def position(col: int, row: int) -> Position:
    """Validates parameters."""
    return Position(col, row)
