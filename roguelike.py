# -*- coding: utf-8 -*-
from asciimatics.screen import Screen
from asciimatics.event import KeyboardEvent

from models.level import Level, Room, SquareType, Square
from models.game import Game
from ui.text_interface import TextInterface
from helpers.i18n import EnglishDescriptionFactory

if __name__ == '__main__':
    game = Game(EnglishDescriptionFactory())
    try:
        interface = TextInterface(game)
    except KeyboardInterrupt:
        print("\nGoodbye & thanks for playing!")
