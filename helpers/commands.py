from typing import Tuple, List, Optional
from models.player import Player
from helpers.exceptions import EmptyInventoryException

class Command():
    """Minimal implementation of the Command design pattern."""
    verb = None
    def __init__(self):
        self.game = None
    def execute(self) -> Optional[List['Command']]:
        """Excecutes the command."""
        raise NotImplementedError("This is an abstract class.")

class Move(Command):
    def __init__(self, direction: 'Direction'):
        self.direction = direction
 
    def execute(self):
        self.game.player.move(self.direction)
        items = self.game.player.square.items
        msg = None
        if len(items) == 1:
            return [AddMessage("You see here {}.".format(self.game.descriptions.describe(items[0])))]
        elif len(items) > 1:
            return [AddPopup("Things that are here:", (self.game.descriptions.describe(i) for i in items))]

class AddInventoryQuery(Command):
    def __init__(self, callback: type(Command), filter: 'Item' = None):
        self.callback = callback
        self.filter = filter
    def execute(self):
        try:
            self.game.add_inventory_query(self.callback, self.filter)
        except EmptyInventoryException as exc:
            return [AddMessage(str(exc))]

class Quaff(Command):
    verb = "to drink"
    def __init__(self, potion: 'Potion'):
        self.potion = potion
    def execute(self):
        if self.potion.auto_discovery:
            self.game.descriptions.known_items.add(type(self.potion))
        self.game.destroy_item(self.potion)
        return [self.potion.effect(self.game.player)]

class Pickup(Command):
    def execute(self):
        square = self.game.player.square
        if not square.items:
            self.game.messages.appendleft("There is nothing here to pick up.")
        elif len(square.items) == 1:
            item = square.items.pop()
            slot = self.game.player.inventory.add(item)
            if slot:
                self.game.messages.appendleft("{} - {}".format(slot, self.game.descriptions.describe(item)))

class ShowInventory(Command):
    def execute(self):
        inv = self.game.player.inventory.sorted()
        if inv:
            lines = []
            descriptions = self.game.descriptions
            for cat, items in inv.items():
                lines.append(descriptions.plurals[cat].capitalize())
                lines.extend(
                    items.get_view(descriptions.describe).keys()
                )
            return [AddPopup("Your inventory:", sorted(lines))]
        else:
            return [AddMessage("Your inventory is empty.")]

class AddMessage(Command):
    def __init__(self, msg: str):
        self.msg = msg
    def execute(self):
        self.game.add_message(self.msg)

class AddPopup(Command):
    def __init__(self, title: str, body: List[str]):
        self.title = title
        self.body = body
    def execute(self):
        self.game.add_popup(self.title, self.body)

class Heal(Command):
    def __init__(self, creature: 'Creature', points: int):
        self.creature = creature
        self.points = points
    def execute(self):
        self.creature.health.heal(self.points)
        if isinstance(self.creature, Player):
            return [AddMessage("You feel better.")]
        else:
            return [AddMessage("{} looks better.",format(creature.name))]