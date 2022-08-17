#!/usr/bin/env python3

"""
Curses Audio Plugin

Allows beeps to be played in the Terminal window (no sampled sound)!

Beeps will occur when the buzzer is enabled, and at no other time.  Beeps
cannot be stopped since they are effectively just a CTRL+G (character 7 - BEL).
"""

__copyright__ = "Copyright (C) 2022 Gregory Maynard-Hoare"
__license__ = "GNU Affero General Public License v3.0"

import curses
from .a_null import Audio as AudioBase


class Audio(AudioBase):
    def enable_buzzer(self, enabled):
        if enabled:
            curses.beep()

    def is_null(self):
        # Only the null audio device should return True
        return False
