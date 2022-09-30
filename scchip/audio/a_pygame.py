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

PLAYBACK_FREQUENCY = 44100.0
DEFAULT_VOLUME = 0.1


class Audio(AudioBase):
    def __init__(self):
        self.orig_buffer = None
        self.sound = None
        self.frequency = None
        self.sample_multiplier = None
        self.resampled_buffer = None
        self.resampled_buffer_size = None
        self.buzzer_enabled = False
        pygame.mixer.pre_init(int(PLAYBACK_FREQUENCY), size=8, channels=1, buffer=1, allowedchanges=0)
        pygame.mixer.init()
        super().__init__()

    def set_frequency(self, frequency):
        # Setting PyGame's playback rate is very slow, so we must resample audio for it when building the buffer
        if frequency != self.frequency:
            self.frequency = frequency
            self.sample_multiplier = PLAYBACK_FREQUENCY / frequency

            # If the frequency has been changed, and there is a sample in the buffer, resample it now
            if self.orig_buffer is not None:
                self.set_buffer()

    def enable_buzzer(self, enabled):
        # Enable or disable the buzzer, i.e. play or stop buffer playback.  If there is already a sound sample being
        # played from the buffer, it won't be restarted.

        if enabled:
            if not self.buzzer_enabled:
                self.sound.play(-1)
                self.buzzer_enabled = True
        else:
            if self.buzzer_enabled:
                self.sound.stop()
                self.buzzer_enabled = False

    def set_buffer(self, buffer=None):
        # Copy the bit-level buffer into PyGame as an extended audio sample.  If None is supplied for the buffer (such
        # as when changing sample playback frequency), then the previously supplied one will be used.

        if buffer is None:
            buffer = self.orig_buffer
        else:
            self.orig_buffer = buffer

        sample_multiplier = self.sample_multiplier
        resampled_buffer_size = int(128 * sample_multiplier)  # 16-bit (2-byte) input buffer width * 8-bit output height

        # Resize host audio buffer if necessary
        if resampled_buffer_size != self.resampled_buffer_size:
            self.resampled_buffer = memoryview(bytearray(resampled_buffer_size))
            self.resampled_buffer_size = resampled_buffer_size

        # Resample (stretch the width and height of) the emulated square waveform to fit the host buffer
        for resampled_buffer_pos in range(resampled_buffer_size):
            buffer_byte_pos = resampled_buffer_pos / sample_multiplier
            byte = int(buffer_byte_pos / 8.0)
            bit = 7 - int(buffer_byte_pos % 8.0)
            self.resampled_buffer[resampled_buffer_pos] = ((buffer[byte] >> bit) & 1) * 0xFF

        if self.buzzer_enabled:
            self.sound.stop()

        self.sound = pygame.mixer.Sound(self.resampled_buffer)
        self.sound.set_volume(DEFAULT_VOLUME)

        if self.buzzer_enabled:
            # If the buffer has been replaced before the sound has been disabled, play the new sample now
            self.sound.play(-1)

    def shutdown(self):
        if self.sound:
            self.sound.stop()

        pygame.mixer.quit()
        super().shutdown()

    def is_null(self):
        # Only the null audio device should return True
        return False
