# -*- coding: utf-8 -*-
"""Random number generators.

This module contains some RNGs suitable for a roguelike game.
They simulate dice tosses, coin flips, etc.
"""

from random import randint, getrandbits

from helpers.validation import validate


#@validate({
#    0: {'type': 'integer', 'min': 1},
#    1: {'type': 'integer', 'min': 2}
#})
def d(num: int, max_val: int) -> int:   #pylint: disable=invalid-name
    """Random number such that num <= d(n,x) <= num*x.

    Simulates the roll of `num` dice with `max_val` sides each.

    :Example:

    d(1, 6) = 1d6 (an integer between 1 and 6)

    .. seealso:: https://en.wikipedia.org/wiki/Dice_notation
    """
    return sum(randint(1, max_val) for __ in range(num))

def coin() -> bool:
    """A coin toss, expressed as boolean."""
    return bool(getrandbits(1))
