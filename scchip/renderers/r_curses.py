#!/usr/bin/env python3

"""
Curses Renderer Plugin

Used by a Framebuffer object to draw the screen.  This draws graphics in a
standard Linux-style TTY Terminal, the Windows Command Prompt, or PowerShell.

This will draw inverted spaces to represent each pixel of the screen if set to
monochrome mode (CHIP-8, Super-CHIP 1.0, Super-CHIP 1.1 and CHIP-48). If set to
colour mode, it will draw black for the background, green for the first plane,
red for the second, and white if both planes' pixels are set at the same time.

If the screen mode is changed, Curses will use a different sized pad to draw
the characters.
"""

__copyright__ = "Copyright (C) 2022 Gregory Maynard-Hoare"
__license__ = "GNU Affero General Public License v3.0"

import curses
import _curses
from .r_null import Renderer as RendererBase


class Renderer(RendererBase):
    def __init__(self, scale=None, use_colour=True):
        if scale is None:
            scale = 2  # Default horizontal stretch if not supplied, or set to default

        self.pixel_char = " " * scale
        self.pad = None
        self.last_screen_height = -1
        self.last_screen_width = -1
        self.cursor_mode = 0
        self.screen = curses.initscr()
        curses.curs_set(self.cursor_mode)
        curses.noecho()
        curses.cbreak()

        if use_colour:
            curses.start_color()  # Only needed if not B/W
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)
            curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_RED)
            curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_WHITE)
            curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_BLUE)
            curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_CYAN)
            curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_MAGENTA)
            curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_YELLOW)

        super().__init__(scale, use_colour)

    def __del__(self):
        if self.pad:
            del self.pad

        curses.nocbreak()
        curses.echo()

        if self.cursor_mode != 1:
            try:
                curses.curs_set(1)
            except _curses.error:
                pass

        curses.endwin()

    def set_resolution(self, width, height):
        adjusted_width = width * self.scale + 1

        # We have to allow one extra character, presumably for the cursor, otherwise we can't write the furthest
        # bottom-right pixel.
        self.pad = curses.newpad(height + 1, adjusted_width)

        if self.use_colour:
            # Sometimes the background is not erased correctly if using colours rather than inverted pixels.  This
            # ensures the erase happens properly.
            self.pad.bkgd(" ", curses.color_pair(1))

        super().set_resolution(width, height)

    def set_pixel(self, x, y, colour):
        if self.use_colour:
            curses_colour = curses.color_pair((colour % 8) + 1)
        else:
            curses_colour = curses.A_REVERSE if colour else curses.A_NORMAL

        self.pad.addstr(y + 1, x * self.scale, self.pixel_char, curses_colour)
        super().set_pixel(x, y, colour)

    def refresh_display(self):
        screen_height, screen_width = self.screen.getmaxyx()  # This doesn't seem to ever change/work on Windows?!

        if screen_height == self.last_screen_height and screen_width == self.last_screen_width:
            # Fast delta update
            if self.refresh_needed:
                self.pad.refresh(0, 0, 0, 0, screen_height - 1, screen_width - 1)
        else:
            # Screen resolution changed, redraw everything
            self.screen.clear()

            if hasattr(curses, "resizeterm"):
                # This doesn't work on Windows
                curses.resizeterm(screen_height, screen_width)

            self.screen.refresh()
            self.last_screen_height = screen_height
            self.last_screen_width = screen_width

        super().refresh_display()

    def set_title(self, title):
        if self.pad:
            title_len = len(title)

            if self.width > title_len:
                self.pad.addstr(0, 0, title + " " * (self.width * self.scale - title_len), curses.A_REVERSE)
                self.refresh_needed = True

        super().set_title(title)

    # No Superclass for these Curses-specific methods

    def set_curses_cursor(self, mode):
        self.cursor_mode = mode

    def get_curses_screen(self):
        return self.screen
