from collections import deque
from enum import Enum
from functools import lru_cache
from itertools import chain
from math import inf
from random import randint, shuffle, choice, sample
from typing import List, Tuple, Dict, Union, Optional, Iterator, Generator

import networkx as nx

from models.position import Position, position
from models.direction import Direction
from rnd.dice import d, coin

class SquareType(Enum):
    # Walkable types
    ROOM        = 0
    CORRIDOR    = 1
    DOORWAY     = 2
    # Non-walkable types
    WALL_TL     = 101
    WALL_TR     = 102
    WALL_BL     = 103
    WALL_BR     = 104
    WALL_H      = 105
    WALL_V      = 106

class Square():
    """Generic map square.

    The Square is the baase element of a level. It can hold
    creatures and items. The `type` attribute specializes the square."""
    __slots__ = "pos", "type", "known", "_lit", "items"

    def __init__(self, sq_type: SquareType):
        self.type = sq_type
        self.known = False
        """When False, the square is hidden from the map."""
        self._lit = False
        self.items = []
    
    @property
    def lit(self):
        """When True, the player can "see" the Square."""
        return self._lit or (self.known and not self.is_walkable)

    @lit.setter
    def lit(self, value: bool):
        self._lit = value

    @property
    def is_walkable(self) -> bool:
        """Returns True if creatures can walk on the square."""
        return self.type.value <= 100

class SquareStore(dict):
    """Maps Positions to Squares.

    A SquareStore is a Position->Square mapping that can perform
    some additional operations."""
    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    def switch_lights(self, switch: bool) -> None:
        """Turns the light on/off on all squares."""
        for _, sq in self.items():
            sq.lit = switch

    def get_random_walkable(self) -> Position:
        """Returns a random Position mapped to a walkable Square."""
        pos = choice(list(self))
        while not self[pos].is_walkable:
            pos = choice(list(self))
        return pos
    
class Room(SquareStore):
    """A room."""
    _MIN_DIM = 5
    _H_DICE = (1, 6)
    _W_DICE = (2, 8)
    def __init__(self, top_left: Position, width: int, height: int):
        self.top_left = top_left
        """Top-left corner of the room."""
        self.width = width
        """Room "width" (horizontal span)."""
        self.height = height
        """Room "height" (vertical span)."""
        self.lit = True
        """When True, """
        super().__init__(self._build_squares())

    def switch_lights(self, switch):
        super().switch_lights(switch and self.lit)
        if switch and self.lit:
            for pos in self:
                self[pos].known = True


    @classmethod
    def create(cls) -> 'Room':
        """Factory method."""
        width = cls._MIN_DIM + d(*cls._W_DICE) - 1
        height = cls._MIN_DIM + d(*cls._H_DICE) - 1
        top_left = position(
            randint(0, Position.SCREEN_W - width-1),
            randint(0, Position.SCREEN_H - height-1))
        return Room(top_left, width, height)

    def _intersect(self, other: 'Room', margin: int = 0) -> bool:
        """Checks if `self` intersects `other` or vice versa."""
        return not any((
            self.bbox[0] > other.bbox[2]+margin,       #self right of other
            self.bbox[2] < other.bbox[0]-margin,       #self left of other
            self.bbox[1] > other.bbox[3]+margin,       #self below other
            self.bbox[3] < other.bbox[1]-margin,       #self above other
        ))

    def _build_squares(self) -> Dict[Position, Square]:
        """ Creates the dictionary of squares for the room. """
        b = self.bbox
        sq = {p: Square(t) for p, t in zip(self.corners, (SquareType.WALL_TL, SquareType.WALL_BL, SquareType.WALL_BR, SquareType.WALL_TR))}
        for idx in range(4):
            if idx % 2:     # Odd = horizontal wall
                sq.update({
                    position(i, b[idx]): Square(SquareType.WALL_H) 
                    for i in range(b[0]+1, b[2])
                })
            else:           # Even = vertical wall
                sq.update({
                    position(b[idx], i): Square(SquareType.WALL_V) 
                    for i in range(b[1]+1, b[3])
                })
        # Fill
        sq.update({position(i, j): Square(SquareType.ROOM) for i in range(b[0]+1, b[2]) for j in range(b[1]+1, b[3])})
        return sq


    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        """Bounding box for the room.

        Expressed as [top_left.col, top_left.row, bottom_right.col, bottom_right.row]."""
        return (self.top_left.col, self.top_left.row, self.top_left.col + self.width-1, self.top_left.row + self.height-1)
        
    @property
    def corners(self) -> Tuple[Position, Position, Position, Position]:
        """Returns positions of corners in CCW order (TL, BL, BR, TR)."""
        return tuple(position(self.bbox[i], self.bbox[j]) for i, j in ((0, 1), (0, 3), (2, 3), (2, 1)))

class ICorridorFactory():
    """Interface for a corridor factory.
    A corridor factory should build a suitable set of CORRIDOR and DOORWAY squares
    for the given level."""
    def make_corridors(self, level: 'Level') -> SquareStore:
        """Returns the "Corridor" SquareStore for a given Level."""
        raise NotImplementedError("This is an abstract class.")

class CorridorFactory():
    """Implementation of a corridor factory"""
    def make_corridors(self, level: 'Level') -> SquareStore:
        def heuristic(pos1: tuple, pos2: tuple) -> Union[float, int]:
            """A* heuristic for corridor creation (Manhattan distance)."""
            if any(level.locate(p) for p in (pos1, pos2)):
                return inf      # Avoid squares that contain something other than corridors
            return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

        result = SquareStore()
        graph = nx.grid_2d_graph(Position.SCREEN_W, Position.SCREEN_H)
        # Sorts the rooms and then swaps them, in order to get a not-so-random dungeon
        rooms = sorted(list(level.rooms), key= lambda r: r.top_left)
        swaps = 0
        while d(1, 4) > 1 and swaps < len(level.rooms):
            a, b = sample(range(len(level.rooms)), 2)
            rooms[a], rooms[b] = rooms[b], rooms[a]
            swaps += 1
        graph.remove_nodes_from(pos for r in rooms for pos in r)#.squares)
        for r1, r2 in zip(rooms, rooms[1:]):
            start, end = CorridorFactory._rnd_doorway(r1), CorridorFactory._rnd_doorway(r2)
            del r1[start]
            del r2[end]
            for p in start, end:
                graph.add_node(p)            
                graph.add_edges_from((p, n) for n in p.neighbors(False) if level.locate(n) is None)
                result[position(*p)] = Square(SquareType.DOORWAY)
            path = nx.astar_path(graph, start, end, heuristic)
            result.update({position(*pos): Square(SquareType.CORRIDOR) for pos in path[1:-1]})
            graph.remove_nodes_from((start, end))   # Avoid using doorways in next computations
        return result

    @staticmethod
    def _rnd_doorway(room: Room) -> Position:
        tl, __, br, __ = room.corners
        candidates = [
            tl + (randint(1, room.width-1), 0),
            tl + (0, randint(1, room.height-1)),
            br - (randint(1, room.width-1), 0),
            br - (0, randint(1, room.height-1))
        ]
        candidates[:] = [
            pos for pos in candidates 
            if CorridorFactory._is_valid_doorway(pos) 
            and pos in room#.squares
            and room[pos].type in (SquareType.WALL_H, SquareType.WALL_V)
        ]
        if candidates:
            p = choice(candidates)
            return position(*p)
        else:
            return CorridorFactory._rnd_doorway(room)
        
    @staticmethod
    def _is_valid_doorway(pos: Position) -> bool:
        """Doorways can't be placed on the map's edge."""
        return 1 <= pos.col <= Position.SCREEN_W - 1 and 1 <= pos.row <= Position.SCREEN_H - 1

class Level():
    """A dungeon level."""

    MAX_ROOMS = 9
    """Maximum number of rooms in a level"""
    MAX_ATTEMPTS = 400
    """Maximum number of attempts before the generator gives up."""

    def __init__(self):
        """Builds a random dungeon level."""
        self.rooms = deque(maxlen=self.MAX_ROOMS)
        self.corridors = []
        for __ in range(self.MAX_ATTEMPTS):
            if len(self.rooms) == self.MAX_ROOMS:
                break
            new_room = Room.create()
            if not any(new_room._intersect(room, randint(3, 6)) for room in self.rooms):
                self.rooms.append(new_room)
        factory = CorridorFactory()
        self.corridors = [factory.make_corridors(self)]

    def get_random_walkable(self, with_corridors: bool=False) -> Square:
        """ Returns a random walkable position inside the level.

        :param with_corridors: include corridors' squares."""

        if with_corridors:        
            feature = choice(chain(self.rooms, self.corridors))
        else:
            feature = choice(self.rooms)
        return feature.get_random_walkable()

    @property
    def features(self):
        """Yields all features in the level (rooms and corridors)."""
        return chain(self.rooms, self.corridors)

    def __getitem__(self, pos: Position) -> Square:
        for feature in self.features:
            try:
                return feature[pos]
            except KeyError:
                continue
        raise KeyError

    def squares(self) -> Generator:
        """Yields all (position, square) couples in the level"""
        for feature in self.features:
            for item in feature.items():
                yield item
    
    def locate(self, pos: Position) -> Optional[SquareStore]:
        """Returns the feature (room or corridor) that contains `pos`.

        If no such feature exists, returns `None`."""
        for feature in self.features:
            if pos in feature:
                return feature
        return None
        
    @staticmethod
    def _corridor_heuristics(level: 'Level', pos1: tuple, pos2: tuple) -> Union[float, int]:
        """A* heuristic for corridor creation (Manhattan distance)"""
        for p in (pos1, pos2):
            if level.locate(p):# and level.squares()[p] != SquareType.CORRIDOR:
                return inf      # Avoid squares that contain something other than corridors
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
