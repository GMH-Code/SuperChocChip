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
from .r_null import RendererError, Renderer as RendererBase
from ..constants import APP_NAME


class Renderer(RendererBase):
    def __init__(self, scale=None, use_colour=True, curses_palette=None, curses_cursor_mode=0, **kwargs):
        if scale is None:
            scale = 2  # Default horizontal stretch if not supplied, or set to default

        self.pixel_char = " " * scale
        self.pad = None
        self.last_screen_height = -1
        self.last_screen_width = -1
        self.palette_index = None
        self.screen = curses.initscr()
        curses.savetty()
        curses.noecho()
        curses.cbreak()

        try:
            curses.curs_set(curses_cursor_mode)
        except _curses.error:
            pass

        if use_colour or (curses_palette is not None):
            curses.start_color()  # Only needed if not B/W
            curses.use_default_colors()

            # Define first colour with inverted background, ensuring that if any text is displayed, it won't be obscured
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)

            # Define remaining 15 colours
            for curses_col_num, curses_col in enumerate([
                curses.COLOR_RED, curses.COLOR_GREEN, curses.COLOR_YELLOW, curses.COLOR_BLUE, curses.COLOR_MAGENTA,
                curses.COLOR_CYAN, curses.COLOR_WHITE
            ]):
                curses.init_pair(curses_col_num + 2, curses.COLOR_BLACK, curses_col)

            # Set up default mapping.  We'll be looking up list entries via index, so we don't need to use a dictionary.
            self.palette_index = [1, 3, 2, 8, 5, 7, 6, 4] * 2

            # Override some (or all) of the colours with a user-defined palette, if necessary
            if curses_palette is not None:
                if len(curses_palette) > 0x10:
                    raise RendererError("Too many palette colours defined.")

                for curses_colour_num, curses_colour in enumerate(curses_palette):
                    try:
                        curses_colour_int = int(curses_colour, 8)
                    except ValueError:
                        raise RendererError("Invalid palette colour defined.") from None

                    self.palette_index[curses_colour_num] = curses_colour_int + 1

        super().__init__(scale, use_colour)

    def __del__(self):
        # PyPy does not call this, but regular CPython does
        self.shutdown()

    def set_resolution(self, width, height):
        # Fast-erase the current pad.  The new one may be smaller, and it will also be empty when initialised.
        if self.pad:
            self.pad.erase()
            self.refresh_display(True)

        # We have to allow one extra character, presumably for the cursor, otherwise we can't write the furthest
        # bottom-right pixel.
        adjusted_width = width * self.scale + 1
        self.pad = curses.newpad(height + 1, adjusted_width)  # Adding one additional line for the title bar

        if self.palette_index:
            # Sometimes the background is not erased correctly if using colours rather than inverted pixels.  This
            # ensures the erase happens properly.
            self.pad.bkgd(" ", curses.color_pair(self.palette_index[0]))

        super().set_resolution(width, height)
        self.set_title(APP_NAME)

    def set_pixel(self, location, colour):
        if self.palette_index:
            curses_colour = curses.color_pair(self.palette_index[colour])
        else:
            curses_colour = curses.A_REVERSE if colour else curses.A_NORMAL

        self.pad.addstr(
            (location // self.width) + 1, (location % self.width) * self.scale, self.pixel_char, curses_colour
        )

    def refresh_display(self, content_changed=False):
        screen_height, screen_width = self.screen.getmaxyx()  # This doesn't seem to ever change/work on Windows?!

        if screen_height == self.last_screen_height and screen_width == self.last_screen_width:
            # Fast delta update
            if content_changed:
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

    def set_title(self, title):
        if self.pad:
            title_len = len(title)

            if self.width > title_len:
                self.pad.addstr(0, 0, "".join((title, " " * (self.width * self.scale - title_len))), curses.A_REVERSE)
                self.refresh_display(True)

    def shutdown(self):
        if self.screen:
            if self.pad:
                del self.pad

            curses.resetty()
            curses.endwin()
            self.screen = None

        super().shutdown()

    # No Superclass for these Curses-specific methods

    def get_curses_screen(self):
        return self.screen
