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
        self.key_down = {}

        for i in range(0x10):
            self.key_down[i] = False

        super().__init__(keymap, renderer)

    def __del__(self):
        pygame.quit()

    def process_messages(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True

            if event.type == pygame.KEYDOWN:
                hex_key = self.keymap_dict.get(event.key)

                if hex_key is not None:
                    self.key_down[hex_key] = True

            elif event.type == pygame.KEYUP:
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
