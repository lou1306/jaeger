# -*- coding: utf-8 -*-
from collections import deque
from functools import partial
from time import sleep
from typing import Tuple

from asciimatics.screen import Screen, NextScene
from asciimatics.widgets import Button, PopUpDialog, ListBox, Frame, Layout, Widget, Label
from asciimatics.event import KeyboardEvent, MouseEvent
from asciimatics.scene import Scene
from asciimatics.effects import Effect

from models.game import Game, Popup, InventoryQuery
from models.level import Level, SquareType
from models.player import Player
from models.items import Potion, Scroll, HealingPotion
from models.direction import Direction
from helpers.commands import *

class BasicEffect(Effect):
    """Implements some abstract methods."""
    def _update(self):
        pass
    def register_scene(self, scene):
        return super().register_scene(scene)
    def stop_frame(self):
        return 0

class PopupEffect(PopUpDialog):
    button_text = "Ok"
    more_text = "More"    
    def __init__(self, messages, screen, msg: Popup):
        lines = list(msg.body)
        if len(lines) > 10:
            lines, other_lines = lines[:10], lines[10:]
            messages.appendleft(Popup(msg.title, other_lines))
            self.button_text = self.more_text
        text="{}\n\n{}".format(msg.title, '\n'.join(lines))
        return super().__init__(screen, text, [self.button_text], self.close)

    def process_event(self, event):
        if isinstance(event, KeyboardEvent) and event.key_code == Screen.KEY_ESCAPE:
            event.key_code = 13 # Enter
        return super().process_event(event)

    @staticmethod
    def close(button):
        raise NextScene("Main")

class InventoryQuery(Frame):
    def __init__(self, screen, msg: InventoryQuery):
        super().__init__(
            screen, 
            screen.height * 2 // 3,
            screen.width * 2 // 3,
            title = msg.title
        )
        self.msg = msg
        options = [(k, v) for k, v in msg.items]
        layout = Layout([1,])
        self.add_layout(layout)
        self._list = ListBox(len(options), options, name="item")
        self._list.value = options[0][1]
        layout.add_widget(self._list, 0)
        self.fix()

    def process_event(self, event):
        super().process_event(event)
        if event.key_code == Screen.KEY_ESCAPE:
            self._list.value = None
            self._ok()
        elif event.key_code in range(ord('a'), ord('z')+1):
            self._list.value = self.find_item(event.key_code)
            self._ok()
        elif event.key_code in (13, ord(' ')):
            self._ok()
        return None

    def find_item(self, key: str) -> 'Item':
        find = [v for k, v in self.msg.items if k[0] == chr(key)]
        if find:
            return find[0]

    def _ok(self):
        try:
            self.msg.execute(self._list.value)
        except KeyError:
            print(options)
            print(self._list.value)
            raise KeyboardInterrupt()
        finally:
            self._close()

    def _close(self):
        self._scene.remove_effect(self)
        raise NextScene("Main")

class MessageBox(BasicEffect):
    button_text = "Ok"
    more_text = "More"
    """Displays game messages."""
    def __init__(self, screen: Screen, top_left: Tuple[int, int], messages: deque, **kwargs):
        self._screen = screen
        self._top_left = top_left
        self.messages = messages
        self._history = deque(maxlen=10)
        self.block = False
        self.current_message = None
        return super().__init__(screen, **kwargs)

    def update(self, frame_no):
        num = len(self.messages)
        if num and not self.block:
            msg = self.messages.popleft()
            if isinstance(msg, str):
                self._history.append(msg)
                self._screen.print_at(msg, *self._top_left)
                if num > 1:
                    self._screen.print_at("--More", len(msg) + 2, 0, Screen.COLOUR_WHITE, Screen.A_REVERSE)
                    self.block = True
            elif isinstance(msg, Popup):
                self._scene.add_effect(PopupEffect(self.messages, self._screen, msg))
            else:
                self._scene.add_effect(InventoryQuery(self._screen, msg))

    def process_event(self, event):
        if not self.block:
            self.reset()
            return event
        else:
            if isinstance(event, KeyboardEvent) and event.key_code in (13, 32):
                self.reset()
                return event
            else:
                return None

    def reset(self):
        self.current_message = None
        self.block = False
        self._screen.print_at(' '*79, 0,0)

class StatusBar(BasicEffect):
    
    health_color = {
        (0, 20): Screen.COLOUR_RED,
        (21, 89): Screen.COLOUR_WHITE,
        (90, 199): Screen.COLOUR_GREEN
    }
    def __init__(self, screen, top_left: Tuple[int, int], player: Player, **kwargs):
        self._screen = screen
        self._top_left = top_left
        self._player = player
        return super().__init__(screen, **kwargs)

    def reset(self):
        for row in range(2):
            self._screen.print_at(' ' * 79, self._top_left[0], self._top_left[1] + row)

    def update(self, frame_no):
        self.reset()
        self._screen.print_at(str(self._player.name),  *self._top_left, colour=Screen.COLOUR_WHITE, attr=Screen.A_BOLD)
        health = self._player.health
        color = Screen.COLOUR_WHITE
        for range, val in self.health_color.items():
            if range[0] <= health.percent <= range[1]:
                color = val
                break
        self._screen.print_at(
            "HP:{}/{}".format( 
            self._player.health.current_hp, 
            self._player.health.max_hp),
            self._top_left[0], self._top_left[1] + 1,
            color, Screen.A_BOLD)

class MapBox(BasicEffect):
    chars = {
        SquareType.ROOM: '.',
        SquareType.CORRIDOR: '░',
        SquareType.WALL_H: '─',
        SquareType.WALL_V: '│',
        SquareType.WALL_TL: '┌',
        SquareType.WALL_TR: '┐',
        SquareType.WALL_BL: '└',
        SquareType.WALL_BR: '┘',
        SquareType.DOORWAY: '.',
        Potion: '!',
        Scroll: '?'
    }

    commands = {
        ord('h'): Move(Direction.W),
        ord('j'): Move(Direction.S),
        ord('k'): Move(Direction.N),
        ord('l'): Move(Direction.E),
        ord('y'): Move(Direction.NW),
        ord('u'): Move(Direction.NE),
        ord('b'): Move(Direction.SW),
        ord('n'): Move(Direction.SE),
        ord('q'): AddInventoryQuery(Quaff, Potion),
        ord(','): Pickup(),
        ord('i'): ShowInventory()
    }

    color = {
        True: Screen.COLOUR_WHITE,
        False: Screen.COLOUR_BLACK
    }

    def __init__(self, screen: Screen, top_left: Tuple[int, int], game: Game, **kwargs):
        self._screen = screen
        self._top_left = top_left
        self.game = game
        return super().__init__(screen, **kwargs)

    def update(self, frame_no):
        self.draw_level()
        self.draw_player()

    def draw_level(self):
        """Draws the current level."""        
        for pos, sq in self.game.player.level.squares():
            pos += self._top_left
            if sq.known:# and self._can_draw(pos):
                self.draw_square(pos, sq)

    def _can_draw(self, pos):
        """Checks if the position can be drawn over.

        Right now it just scrapes the screen, assuming that
        popups have a non-black background. So it's more of a hack
        than a solution."""
        bg = self._screen.get_from(*pos)[3]
        return bg == 0

    def draw_player(self):
        """Draws the player."""
        pos = self.game.player.pos
        self._screen.print_at('@', *(pos + self._top_left), colour=Screen.COLOUR_WHITE, attr=Screen.A_REVERSE)

    def draw_square(self, pos, square):
        if square.items:
            char = self.chars[square.items[0].category]
        else:
            char = self.chars[square.type]
        self._screen.print_at(
            char,
            pos.col,
            pos.row,
            self.color[square.lit],
            Screen.A_BOLD
        )
    def reset(self):
        pass

    def process_event(self, event):
        try:
            if isinstance(event, KeyboardEvent):
                self.game.add_command(self.commands[event.key_code])
                self.update(0)
                if self.game.player.health.current_hp == 0:
                    self._scene.add_effect(end(self._screen))
        except KeyError:
            return event

def end(screen):
    def quit(button_index: int):
        raise KeyboardInterrupt
    f = PopUpDialog(screen, "You died :(", ["OK"], quit)
    return f

class TextInterface():
    """Main class. Sets up the user interface."""
    def __init__(self, game: Game):
        self.game = game
        Screen.wrapper(self.run)
        
    def run(self, screen):
        map_box = MapBox(screen, (0, 1), self.game)
        msg_box = MessageBox(screen, (0, 0), self.game.messages)
        status_bar = StatusBar(screen, (0,21), self.game.player)
        screen.play([Scene([map_box, msg_box, status_bar], -1, clear=True, name="Main")])
