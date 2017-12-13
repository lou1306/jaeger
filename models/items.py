# -*- coding: utf-8 -*-

from enum import Enum
from typing import Tuple, List, Optional
from random import randrange

from rnd.dice import d

from models.player import Player
from helpers.commands import Heal, AddMessage
#from models.events import Heal

def Category(cls):
    cls.category = cls
    return cls

class Beatitude(Enum):
    """Alters the behavior of an item."""
    CURSED = "cursed"
    UNCURSED = "uncursed"
    BLEssED = "blessed"

class Item():
    category = None
    beatitude = None
    beatitude_known = False

class HasEffect(Item):
    """Item that has an effect (can be quaffed, read, applied etc.).
    
    Returns a list of messages to be displayed."""
    def effect(creature: 'Creature', *args) -> Optional[List[str]]:
        raise NotImplementedError("This is an interface.")

class SingleUse(HasEffect):
    auto_discovery = True
    """Healing item."""
    def effect(self, creature: 'Creature', base: int, roll: Tuple[int, int] = (0,0)) -> Optional[List[str]]:
        creature.health.heal(base + d(*roll))

@Category
class Potion(Item):
    pass

@Category
class Scroll(Item):
    pass

class HealingScroll(Scroll):
    auto_discovery = True
    def effect(self, creature):
        super().effect(creature, 1)

class HealingPotion(Potion):
    auto_discovery = True
    def effect(self, creature):
        return Heal(creature, 3)