# -*- coding: utf-8 -*-
from collections import deque
from typing import Tuple, Optional, List
from weakref import ref, WeakMethod
    
from helpers.skills import Inventory

from models.direction import Direction
from models.position import Position
from models.level import Level, Room

class Creature():
    def __init__(self, level: Level, pos: Position):
        """Initializator for creatures.

        Don't instantiate creatures outside this module. Use factories"""
        self._level = ref(level)
        self.pos = pos  
        self.health = None

    @property
    def level(self) -> Level:
        return self._level()

    def die(self):
        raise NotImplementedError("This is an abstract class.")

class Player(Creature):
    
    def __init__(self, level: Level, pos: Position, name: str = "Luca"):
        super().__init__(level, pos)
        self.name = name
        
    @classmethod
    def create(cls, level: Level, pos: Position) -> 'Player':
        """Factory method"""
        player = Player(level, pos)
        player.health = Health(player, 10)
        player.inventory = Inventory()
        player.update_lights()
        return player

    @property
    def square(self):
        return self.level[self.pos]

    def update_lights(self) -> None:
        """Updates the lighting in the current level."""
        feature = self.level.locate(self.pos)
        for f in self.level.rooms:
            f.switch_lights(f is feature and isinstance(f, Room))
        #for corridor in self.level.corridors:
        #    corridor.switch_lights(False)
        self.level[self.pos].lit = True
        self.level[self.pos].known = True
        for n in self.pos.neighbors(True):
            try:
                n_feature = self.level.locate(n)
                if n_feature:
                    n_feature[n].lit = True
                    self.level[n].known = True
            except KeyError:
                continue

    def move(self, direction: Direction) -> None:
        new_pos = self.pos + direction.value
        try:
            if self.level[new_pos].is_walkable:
                self.pos = new_pos
                self.update_lights()
            else:
                pass
                # TODO: remove
                self.health.damage(1)
        except KeyError:
            return None

    def die(self):
        pass

class Health():
    def __init__(self, creature: Creature, max_hp: int):
        self.max_hp = max_hp
        self.current_hp = max_hp
        self._creature = ref(creature)
    
    @property
    def creature(self) -> Creature:   
        return self._creature()

    @property
    def percent(self) -> int:
        """Returns the creature's percentage healt."""
        return int(self.current_hp / self.max_hp * 100)

    def damage(self, points) -> None:
        """Deals a `points`-HP damage to the creature."""
        self.current_hp = max(0, self.current_hp - points)
        if self.current_hp == 0:
            self.creature.die()

    def heal(self, points) -> None:
        self.current_hp = min(self.max_hp, self.current_hp + points)