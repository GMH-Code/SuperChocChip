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
from ..constants import APP_NAME


class Renderer(RendererBase):
    def __init__(self, scale=None, use_colour=True, pygame_palette=None, smoothing=0, **kwargs):
        if scale is None:
            scale = 512  # Default window width if not supplied, or set to default

        pygame.display.init()
        self.set_title(APP_NAME)  # Perhaps an icon would be nice, too?
        self.rgb_buffer = None
        self.scaled_size = (scale, scale // 2)
        self.display_surface = pygame.display.set_mode(self.scaled_size, 0, 8)
        self.display_surface.set_alpha(None)
        self.smoothing = smoothing

        # These are looked up instantly by index, so no need for a dictionary on this occasion
        colour_map = [
            0x222222, 0x00DD88, 0xDD5555, 0xDDDDDD,
            0x333333, 0x00CC77, 0xCC4444, 0xCCCCCC,
            0x444444, 0x00BB66, 0xBB3333, 0xBBBBBB,
            0x555555, 0x00AA55, 0xAA2222, 0xAAAAAA
        ]

        if not use_colour:
            # Swap green for white on monochromatic displays
            colour_map[1] = colour_map[3]

        # Override some (or all) of the colours with a user-defined palette, if necessary
        if pygame_palette is not None:
            pygame_palette_split = pygame_palette.split(",")

            if len(pygame_palette_split) > 0x10:
                raise RendererError("Too many palette colours defined.")

            for pygame_colour_num, pygame_colour in enumerate(pygame_palette_split):
                if len(pygame_colour) != 6:
                    raise RendererError("Palette colours must all be 6 hex digits long.")

                try:
                    colour_map[pygame_colour_num] = int(pygame_colour, 16)
                except ValueError:
                    raise RendererError("Invalid palette colour defined.") from None

        # Split compound RGB values for faster byte-based lookup later
        self.rgb_map = [memoryview(bytearray([i >> 16, (i >> 8) & 0xFF, i & 0xFF])) for i in colour_map]

        super().__init__(scale, use_colour)

    def set_resolution(self, width, height):
        self.render_surface = pygame.Surface((width, height))
        total_pixels = width * height
        self.rgb_buffer = memoryview(bytearray(total_pixels * 3))  # 24-bit

        # Fill the offscreen RGB buffer with the default background colour
        for pixel in range(total_pixels):
            self.set_pixel(pixel, 0)

        # Call superclass method so display size is known on the next refresh
        super().set_resolution(width, height)

        # Force a refresh now, in case nothing else is drawn afterwards
        self.refresh_display(True)

    def set_pixel(self, location, colour):
        # Update RGB buffer in-place to minimise allocations and PyGame calls
        rgb_location = location * 3
        self.rgb_buffer[rgb_location:rgb_location + 3] = self.rgb_map[colour]

    def refresh_display(self, content_changed=False):
        if content_changed and self.rgb_buffer:
            # Blit the bytearray straight to the surface.  This results in a 20
            # percent speed increase over very frequent PixelArray updates
            render_surface = pygame.image.frombuffer(self.rgb_buffer, (self.width, self.height), "RGB")

            # Apply Scale2x rendering passes if requested
            for _ in range(self.smoothing):
                render_surface = pygame.transform.scale2x(render_surface)

            scaled_win = pygame.transform.scale(render_surface, self.scaled_size)
            self.display_surface.blit(scaled_win, (0, 0))
            pygame.display.flip()

    def set_title(self, title):
        pygame.display.set_caption(title)

    def shutdown(self):
        # PyGame currently segfaults if display.quit is called via __del__
        pygame.display.quit()
        super().shutdown()
