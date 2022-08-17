#!/usr/bin/env python3

"""
PyGame Audio Plugin

Allows emulated and sampled sounds or music to play within PyGame / SDL.

Emulated sounds are normally very basic.  There is simply a buzzer with an 'on'
or 'off' status, but by resonating the buzzer at a very fast frequency, we can
produce more complex waveforms.

The incoming audio buffer is of 1-bit resolution with 16 length.  The waveform
has to effectively be stretched lengthways and have its offset moved to fit in
a modern 8-bit PyGame / SDL buffer, but it will retain the shape of a square
wave.
"""

__copyright__ = "Copyright (C) 2022 Gregory Maynard-Hoare"
__license__ = "GNU Affero General Public License v3.0"

import pygame
from .a_null import Audio as AudioBase


class Audio(AudioBase):
    def __init__(self):
        self.buffer = memoryview(bytearray(128))  # 16 bit buffer * 8 bit output
        self.buzzer_enabled = False
        self.sound = None
        super().__init__()

    def set_frequency(self, frequency):
        # Set PyGame playback rate.  This can be slow if called frequently
        pygame.mixer.quit()
        pygame.mixer.pre_init(
            frequency, size=-8, channels=1, buffer=1, allowedchanges=pygame.AUDIO_ALLOW_FREQUENCY_CHANGE
        )
        pygame.mixer.init()

    def enable_buzzer(self, enabled):
        # Enable or disable the buzzer, but also play any sounds which may be in the buffer already, or stop any playing
        if enabled:
            self.sound.play(-1)
        else:
            self.sound.stop()

        self.buzzer_enabled = enabled

    def set_buffer(self, buffer):
        # Copy the bit-level buffer into PyGame as an extended audio sample
        buffer_pos = 0

        for byte in buffer:
            for bit in range(7, -1, -1):
                self.buffer[buffer_pos] = ((byte >> bit) & 1) * 0xFF
                buffer_pos += 1

        if self.buzzer_enabled:
            self.sound.stop()

        self.sound = pygame.mixer.Sound(self.buffer)

        if self.buzzer_enabled:
            # If the buffer has been replaced before the sound has been disabled, play the new sample now
            self.sound.play(-1)

    def is_null(self):
        # Only the null audio device should return True
        return False
