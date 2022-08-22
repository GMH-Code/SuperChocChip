#!/usr/bin/env python3

"""
Curses TTY Terminal Input Plugin

Uses a thread to trap Terminal inputs and redirects them to the emulator.  Note
that standard TTY Terminals only understand characters, they do not know when
an actual key is 'pressed' or 'released'.

What we can do (for this plugin) is assume a key is held for a very short time,
and then take advantage of keyboard repeats to fake a 'press' and 'release'.

To do this, I've stored the last time a character corresponding to a key has
been 'seen'.  If it was last seen a long time ago (when checked), then it has
almost certainly been released.

Additionally, the last character 'seen' is stored.  There is a 'reset' switch
for this, which has to be called before checking.

We will also quit if ESC (char 27) or CTRL+C (char 3) is detected.

Note that using the 'nodelay(True)' setting instead of blocking inside a thread
is slightly slower, and can lag, due to constant external calls.
"""

__copyright__ = "Copyright (C) 2022 Gregory Maynard-Hoare"
__license__ = "GNU Affero General Public License v3.0"

import queue
from threading import Thread
from time import time
from .i_null import Inputs as InputsBase

# Terminals don't have separate key press/release, so we have to pause after a character is seen.
KEYBOARD_FAKE_KEYDOWN_TIME = 0.2


# For thread safety, use proper queues to exchange information, avoiding shared variables.
def input_thread(thread_quitter_queue, input_queue, keymap_dict, curses_screen):
    while thread_quitter_queue.empty():
        # This blocks the thread from proceeding, so it won't get the quit message until at least one key is pressed.
        # However, if set as a daemon thread, it should be terminated when the main thread shuts down.
        char = ord(chr(curses_screen.getch()).lower())

        if char == 27 or char == 3:  # Detect ESC or CTRL+C
            input_queue.put(None, block=True)
            break

        keymap_char = keymap_dict.get(char)

        if keymap_char is not None:
            try:
                input_queue.put(keymap_char, block=False)
            except queue.Full:
                pass


class Inputs(InputsBase):
    def __init__(self, keymap, renderer):
        self.key_timers = {}

        for key_num in range(0x10):
            self.key_timers[key_num] = 0.0

        super().__init__(keymap, renderer, force_lowercase=True)

        self.thread_quitter_queue = queue.Queue(1)  # Used to inform the thread it should quit
        self.input_queue = queue.Queue(16)
        self.thread = Thread(
            target=input_thread,
            args=(
                self.thread_quitter_queue,
                self.input_queue,
                self.keymap_dict,
                renderer.get_curses_screen()
            )
        )
        # Terminate the thread when the main program quits (even if currently waiting for a keypress)
        self.thread.daemon = True
        self.thread.start()

    def __del__(self):
        try:
            self.thread_quitter_queue.put(None, block=False)
        except queue.Full:
            # Something else has already requested the thread quits
            pass
        except AttributeError:
            # Thread quitter queue not defined yet
            pass

        # Don't wait for the thread to quit (because this is likely to happen after a keypress)
        # self.thread.join()

    def process_messages(self):
        # Deal with any keys pressed
        target_time = None

        while True:
            try:
                # Blocking here would lock up the main thread if nothing was pressed
                key_pressed = self.input_queue.get(block=False)
            except queue.Empty:
                break
            else:
                if key_pressed is None:
                    return True

                if target_time is None:
                    target_time = time() + KEYBOARD_FAKE_KEYDOWN_TIME  # + extra_processing_time

                self.key_timers[key_pressed] = target_time
                self.last_keypress = key_pressed

        return False

    def is_key_down(self, key):
        return self.key_timers[key] > time()

    def get_keypress(self):
        return self.last_keypress
