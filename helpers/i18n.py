# -*- coding: utf-8 -*-
"""Factory of strings that describe items.

When a player walks on/picks up an item, its "description" (i.e.
the name the player will see) depends on a number of factors:

* Has the player already identified the item?
* Does the player know its Beatitude status?
* etc.

This module provides a Factory class which stores and retrieves
names for items
"""

from models.items import *
from random import randrange

class DescriptionFactory():
    def __init__(self):
        self.unknown_items = self.random_pairing()
        self.known_items = set()

    def describe(self, item: Item):
        """Returns the name of the item."""
        raise NotImplementedError("This is an abstract class.")

    def _add_article(self, s: str) -> str:
        """Returns the string `s` prepended with the correct article.

        Example:
            add_article("potion") ---> "a potion"
            add_article("amulet") ---> "an amulet"
        """
        raise NotImplementedError("This is an abstract class.")
        
class EnglishDescriptionFactory(DescriptionFactory):
    unknown = {
        Potion: "{unknown} potion",
        Scroll: "scroll labeled {unknown}"
    }

    known = "{category} of {name}"
    """e.g. Potion of healing"""
    
    names = {
        Potion: "potion",
        Scroll: "scroll",
        HealingPotion: "healing",
        HealingScroll: "healing"
    }

    unknown_names = {
        Potion: ["emerald", "black", "golden"],
        Scroll: ["READ ME", "YUM YUM"]
    }

    plurals = {
        Potion: "potions",
        Scroll: "scrolls"
    }

    def item_data(self, item: Item):
        return {
            "beatitude": item.beatitude,
            "unknown": self.unknown_items[type(item)],
            "name": self.names[type(item)],
            "category": self.names[item.category]
        }

    def describe(self, item: Item):
        if type(item) in self.known_items:
            template = self.known
        else:
            template = self.unknown[item.category]
        if item.beatitude_known:
                template = "{beatitude} " + template
        return self.add_article(template.format_map(self.item_data(item)))

    def add_article(self, s: str):
        """"""
        if s[0] in "aeiou":
            return "an " + s
        else:
            return "a " + s

    def random_pairing(self):
        """Generates a random description-to-item pairing."""
        result = {}
        for cls in (Potion, Scroll):
            for key in cls.__subclasses__():
                result[key] = self.unknown_names[cls].pop(randrange(0, len(self.unknown_names[cls])))
        return result
            