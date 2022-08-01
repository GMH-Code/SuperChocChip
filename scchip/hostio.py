#!/usr/bin/env python3

"""
Host I/O Functionality

Handles loading ROM binaries and base system fonts for later writing into RAM.
This could be used to handle snapshots (save states), if and when implemented.
For now, games are not really complex enough to warrant save states.
"""

__copyright__ = "Copyright (C) 2022 Gregory Maynard-Hoare"
__license__ = "GNU Affero General Public License v3.0"

from os import path


class Loader:
    def load_binary(self, filename):
        f = open(filename, "rb")
        data = f.read()
        f.close()
        return data

    def load_system_font(self, filename):
        return self.load_binary(path.join(path.abspath(path.dirname(__file__)), "systemfonts", filename))
