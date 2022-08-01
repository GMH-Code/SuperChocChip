#!/usr/bin/env python3

"""
Null Input Plugin

Serves as a base class for other Input plugins.  Can be used on its own if zero
input functionality is required.
"""

__copyright__ = "Copyright (C) 2022 Gregory Maynard-Hoare"
__license__ = "GNU Affero General Public License v3.0"


class InputsError(Exception):
    pass


class Inputs:
    def __init__(self, keymap, renderer):
        self.keymap_dict = {}
        self.renderer = renderer
        keymap_split = keymap.split(",")

        if len(keymap_split) != 0x10:
            raise InputsError("Incorrect number of keys defined -- 16 required.  Use commas to split numbers")

        for key_num, key_defined in enumerate(keymap_split):
            if key_defined in self.keymap_dict:
                raise InputsError("Duplicate keys defined")

            try:
                self.keymap_dict[int(key_defined)] = key_num
            except ValueError:
                raise InputsError("Defined keys are not all integer values") from None

        self.last_keypress = None

    def process_messages(self):
        return False  # Don't exit the program

    def is_key_down(self, key):  # pylint: disable=unused-argument
        return False  # No keys are held

    def setup_keypress(self):
        self.last_keypress = None

    def get_keypress(self):
        return None  # No keys down
