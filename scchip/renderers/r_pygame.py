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
    def __init__(self, scale=None, use_colour=True, pygame_palette=None, smoothing=0, **kwargs):
        if scale is None:
            scale = 512  # Default window width if not supplied, or set to default

        pygame.init()
        self.pygame_running = True
        self.set_title("Starting...")  # Perhaps an icon would be nice, too?
        self.pixel_array = None
        self.scaled_size = (scale, scale // 2)
        self.display_surface = pygame.display.set_mode(self.scaled_size, 0, 8)
        self.smoothing = smoothing

        # These are looked up instantly by index, so no need for a dictionary on this occasion
        self.colour_map = [
            0x222222, 0x00DD88, 0xDD5555, 0xDDDDDD,
            0x333333, 0x00CC77, 0xCC4444, 0xCCCCCC,
            0x444444, 0x00BB66, 0xBB3333, 0xBBBBBB,
            0x555555, 0x00AA55, 0xAA2222, 0xAAAAAA
        ]

        if not use_colour:
            # Swap green for white on monochromatic displays
            self.colour_map[1] = self.colour_map[3]

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

    def __del__(self):
        self.shutdown()

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
            render_surface = self.render_surface

            # Apply Scale2x rendering passes if requested
            for _ in range(self.smoothing):
                render_surface = pygame.transform.scale2x(render_surface)

            scaled_win = pygame.transform.scale(render_surface, self.scaled_size)
            self.display_surface.blit(scaled_win, (0, 0))
            pygame.display.flip()
            self._set_pixel_array()

        super().refresh_display()

    def set_title(self, title):
        pygame.display.set_caption(title)
        super().set_title(title)

    def _set_pixel_array(self):
        self.pixel_array = pygame.PixelArray(self.render_surface)

    def shutdown(self):
        if self.pygame_running:
            pygame.quit()
            self.pygame_running = False

        super().shutdown()
