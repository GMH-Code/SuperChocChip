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
from .r_null import RendererError, Renderer as RendererBase


class Renderer(RendererBase):
    def __init__(self, scale=None, use_colour=True, pygame_palette=None, **kwargs):
        if scale is None:
            scale = 512  # Default window width if not supplied, or set to default

        pygame.init()
        self.set_title("Starting...")  # Perhaps an icon would be nice, too?
        self.pixel_array = None
        self.scaled_size = (scale, scale // 2)
        self.display_surface = pygame.display.set_mode(self.scaled_size, 0, 8)

        if use_colour:
            self.colour_map = {
                0x1: 0x00E080, 0x2: 0xE05050, 0x3: 0xE0E0E0, 0x4: 0x303030,
                0x5: 0x00D070, 0x6: 0xD04040, 0x7: 0xD0D0D0, 0x8: 0x404040,
                0x9: 0x00C060, 0xA: 0xC03030, 0xB: 0xC0C0C0, 0xC: 0x505050,
                0xD: 0x00B050, 0xE: 0xB02020, 0xF: 0xB0B0B0
            }
        else:
            self.colour_map = {1: 0xE0E0E0}

        self.colour_map[0] = 0x202020

        # Override some (or all) of the colours with a user-defined palette, if necessary
        if pygame_palette is not None:
            pygame_palette_split = pygame_palette.split(",")

            if len(pygame_palette_split) > 0x10:
                raise RendererError("Too many palette colours defined.")

            for pygame_colour_num, pygame_colour in enumerate(pygame_palette_split):
                if len(pygame_colour) != 6:
                    raise RendererError("Palette colours must all be 6 hex digits long.")

                try:
                    self.colour_map[pygame_colour_num] = int(pygame_colour, 16)
                except ValueError:
                    raise RendererError("Invalid palette colour defined.") from None

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
