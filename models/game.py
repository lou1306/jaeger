from collections import deque, namedtuple
from typing import List
from random import randrange

from mediator import Mediator

from helpers.i18n import EnglishDescriptionFactory
from models.items import Item, HealingPotion, HealingScroll
from models.level import Level
from models.player import Player
from models.direction import Direction
from helpers.commands import *
from helpers.exceptions import EmptyInventoryException

class Popup(namedtuple("Popup", "title body")):
    pass

class InventoryQuery():
    def __init__(self, game: 'Game', callback: type(Command), filter: 'Item' = None):
        items = game.player.inventory.filter(filter).get_view(game.descriptions.describe)
        if not items:
            if filter:
                msg = "You don't have anything {}.".format(callback.verb)
            else:
                msg = "Your inventory is empty"
            raise EmptyInventoryException(msg)
        self.items = sorted(items.items())
        self.game = game
        self.callback = callback
        self.title = "What do you want {}?".format(callback.verb)
    def execute(self, item):
        if item:
            self.game.add_command(self.callback(item))
        else:
            self.game.add_command(AddMessage("Never mind."))

class Game():
    """The game.
    This is essentially a facade to the whole models package."""

    def __init__(self, description_factory):
        self.descriptions = description_factory
        self.levels = [Level()]
        self.player = Player.create(self.levels[0], self.levels[0].get_random_walkable())
        for n in self.player.pos.neighbors():
            if self.levels[0].locate(n) and self.levels[0][n].is_walkable:
                self.levels[0][n].items = [HealingPotion()]
        self.messages = deque()
        self.commands = deque()
        self.turn = 0

    def add_message(self, msg: str):
        self.messages.appendleft(msg)

    def add_popup(self, title: str, body: List[str]):
        self.messages.appendleft(Popup(title, body))

    def add_inventory_query(self, callback, filter):
        self.messages.appendleft(InventoryQuery(self, callback, filter))

    def handle_command(self, cmd: Command):
        cmd.game = self
        self.commands.extendleft(cmd.execute() or [])

    def add_command(self, cmd: Command):
        self.commands.append(cmd)
        self.dispatch()

    def dispatch(self):
        while self.commands:
            self.handle_command(self.commands.popleft())

    def destroy_item(self, item: Item):
        """Removes an item from the game."""
        self.player.inventory.remove(item)