#!/usr/bin/env python3

"""
PyGame Renderer Plugin

Used by a Framebuffer object to draw the screen.  This draws graphics onto an
SDL window surface via PyGame. Note that the surface is allocated at the size
which matches the current screen mode, and then the contents are stretched (in
the correct aspect ratio using 'Nearest Neighbour' translation) to fit the
window itself.  This means we don't have to draw the same pixel multiple times.

If monochrome mode is chosen, white pixels will be drawn (CHIP-8, Super-CHIP
1.0, Super-CHIP 1.1 and CHIP-48).  If colour has been chosen (XO-CHIP), green
is blitted for the first plane, red for the second, and white is drawn if both
are set at the same time.
"""

__copyright__ = "Copyright (C) 2022 Gregory Maynard-Hoare"
__license__ = "GNU Affero General Public License v3.0"

import pygame
from .r_null import Renderer as RendererBase


class Renderer(RendererBase):
    def __init__(self, scale=None, use_colour=True):
        if scale is None:
            scale = 512  # Default window width if not supplied, or set to default

        pygame.init()
        self.set_title("Starting...")  # Perhaps an icon would be nice, too?
        self.pixel_array = None
        self.scaled_size = (scale, scale // 2)
        self.display_surface = pygame.display.set_mode(self.scaled_size, 0, 8)

        if use_colour:
            self.colour_map = {
                1: 0x00E080,
                2: 0xE04040,
                3: 0xE0E0E0
            }
        else:
            self.colour_map = {1: 0xE0E0E0}

        self.colour_map[0] = 0x202020
        super().__init__(scale, use_colour)

    def set_resolution(self, width, height):
        self.render_surface = pygame.Surface((width, height))
        self.render_surface.fill(self.colour_map[0])
        self._set_pixel_array()
        super().set_resolution(width, height)

    def set_pixel(self, x, y, colour):
        self.pixel_array[x][y] = self.colour_map[colour]
        super().set_pixel(x, y, colour)

    def refresh_display(self):
        if self.refresh_needed and self.pixel_array:
            self.pixel_array.close()
            del self.pixel_array
            scaled_win = pygame.transform.scale(self.render_surface, self.scaled_size)
            self.display_surface.blit(scaled_win, (0, 0))
            pygame.display.flip()
            self._set_pixel_array()

        super().refresh_display()

    def set_title(self, title):
        pygame.display.set_caption(title)
        super().set_title(title)

    def _set_pixel_array(self):
        self.pixel_array = pygame.PixelArray(self.render_surface)