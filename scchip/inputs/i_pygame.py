#!/usr/bin/env python3

"""
PyGame Input Plugin

Unlike the Curses plugin, this scans the keyboard and properly detects key
'press' and 'release' events.  Note that the check should not be called more
often than 60Hz, as constantly checking the queue is time consuming.

As with the Curses plugin, this stores the last key pressed, and has the
appropriate 'reset' switch that needs to be called before checking.

If the application is quit, then this will control shutting PyGame down too, so
any linked Renderer must be able to handle that.
"""

__copyright__ = "Copyright (C) 2022 Gregory Maynard-Hoare"
__license__ = "GNU Affero General Public License v3.0"

import pygame
from .i_null import Inputs as InputsBase


class Inputs(InputsBase):
    def __init__(self, keymap, renderer):
        self.key_down = [False] * 0x10

        self.pygame_methods = {
            pygame.QUIT:    self._pygame_quit,
            pygame.KEYDOWN: self._pygame_keydown,
            pygame.KEYUP:   self._pygame_keyup
        }

        super().__init__(keymap, renderer)

    def process_messages(self):
        # Call PyGame method based on fast dictionary lookup of event
        quit_program = False

        for event in pygame.event.get():
            pygame_method = self.pygame_methods.get(event.type)

            if pygame_method and pygame_method(event):  # Check via short circuit that we don't have 'None'
                quit_program = True  # Process more events, even if planning to quit

        return quit_program

    def _pygame_quit(self, _):
        return True

    def _pygame_keydown(self, event):
        hex_key = self.keymap_dict.get(event.key)

        if hex_key is not None:
            self.key_down[hex_key] = True

        return False

    def _pygame_keyup(self, event):
        if event.key == pygame.K_ESCAPE:
            return True

        hex_key = self.keymap_dict.get(event.key)

        if hex_key is not None and self.key_down[hex_key]:
            self.key_down[hex_key] = False
            self.last_keypress = hex_key

        return False

    def is_key_down(self, key):
        return self.key_down[key]

    def get_keypress(self):
        return self.last_keypress
