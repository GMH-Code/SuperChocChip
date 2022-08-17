#!/usr/bin/env python3

"""
Null Audio Plugin

Serves as a base class for other Audio plugins.  Can be used on its own if no
sound is required.
"""

__copyright__ = "Copyright (C) 2022 Gregory Maynard-Hoare"
__license__ = "GNU Affero General Public License v3.0"


class Audio:
    def __init__(self):
        # Buzzer should be disabled (not playing sounds) by default
        pass

    def set_frequency(self, frequency):
        # Set playback rate in Hz
        pass

    def enable_buzzer(self, enabled):
        # The buzzer should play sounds when the audio timer is >0
        pass

    def set_buffer(self, buffer):
        # Change the emulated 1-bit (16 length) sound sample
        pass

    def is_null(self):
        # Only the null audio device should return True
        return True
