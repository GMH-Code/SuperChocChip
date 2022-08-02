#!/usr/bin/env python3

"""
Framebuffer Emulator

Pixels are written here and are usually only drawn to the actual display (the
host rendering system) at 60Hz.  We probably could get away with not having a
Framebuffer, but then we'd rely on rendering frameworks to support specific
drawing and scrolling methods. There would also be no guarantee of rendering
speed when calling external libraries that often.  PyGame/Curses can lower
speed substantially when calling some methods tens/hundreds of thousands of
times a second.

Unlike other computers, programs for this system cannot write directly into
video RAM.  Instead sprites are drawn to the screen using an XOR method against
one or more planes.

Collisions (where a pixel was set, but is unset by an XOR), are reported).  If
using Super-CHIP variants, the number of rows are reported, too.

This can easily be extended to 4 planes (for 16 colours).  This has been
trialed, and works, but it is not included because no official specification
(such as a proper palette) has been released for it yet, and I only know of one
game which uses it.
"""

__copyright__ = "Copyright (C) 2022 Gregory Maynard-Hoare"
__license__ = "GNU Affero General Public License v3.0"

from .constants import APP_NAME
from .ram import RAM


class FramebufferError(Exception):
    pass


class Framebuffer():
    def __init__(self, renderer, num_planes=1, allow_wrapping=True):
        if num_planes > 2 or num_planes < 1:
            raise FramebufferError("The framebuffer only supports 1 or 2 planes of VRAM.")

        self.renderer = renderer
        self.num_planes = num_planes
        self.allow_wrapping = allow_wrapping
        self.vid_width = 0
        self.vid_height = 0
        self.vid_size = 0
        self.ram_banks = []
        self.report_perf()

        for _ in range(num_planes):
            self.ram_banks.append(RAM())

        # Set up plane for monochrome display -- white (or green for colour displays)
        self.mask_to_planes = {1: [self.ram_banks[0]]}
        self.affect_planes = self.mask_to_planes[1]

        if num_planes == 2:
            # Add plane for colour display
            self.mask_to_planes.update({
                0: [],                                     # Drop draw request
                2: [self.ram_banks[1]],                    # Red by default
                3: [self.ram_banks[0], self.ram_banks[1]]  # White by default
            })

    def resize_vid(self, vid_width, vid_height):
        self.vid_width = vid_width
        self.vid_height = vid_height
        self.vid_size = self.vid_width * self.vid_height

        for ram_bank in self.ram_banks:
            ram_bank.resize(self.vid_size)  # Update RAM size

        self.renderer.set_resolution(vid_width, vid_height)  # Update screen resolution

    def clear(self):
        if not self.affect_planes:
            return

        # We could fast-clear if there was only one plane rendering, but it's not worth it

        for plane in self.affect_planes:
            plane.clear()

        for y in range(self.vid_height):
            for x in range(self.vid_width):
                self._render_pixel(x, y)

    def get_affected_planes(self):
        return self.affect_planes

    def xor_pixel(self, x, y, plane):
        # Returns flagging any collision

        if self.allow_wrapping:
            x %= self.vid_width
            y %= self.vid_height

        elif x >= self.vid_width or y >= self.vid_height:
            return None

        vram_loc = y * self.vid_width + x
        pixel = plane.read(vram_loc)
        collision = (pixel != 0)
        new_pixel = pixel ^ 0xFF
        plane.write(vram_loc, new_pixel)
        self._render_pixel(x, y)

        return collision

    def _render_pixel(self, x, y):
        # Render the pixel to the display
        vram_loc = x + y * self.vid_width
        colour = 1 if self.ram_banks[0].read(vram_loc) else 0

        if self.num_planes > 1 and self.ram_banks[1].read(vram_loc):
            colour += 2

        self.renderer.set_pixel(x, y, colour)

    # Half-pixel vertical scrolling is unsupported in 64x32 pixel mode

    def scroll_up(self, rows):
        if not self.affect_planes:
            return

        # Ensure this is only called when actually scrolling
        mem_offset = rows * self.vid_width
        vid_size = self.vid_size

        for plane in self.affect_planes:
            plane.move_mem(-mem_offset)  # Usually moves contents up by 1 pixel, or 0.5 on low resolution
            plane.zero_block(vid_size - mem_offset, mem_offset)  # Erase the bottom strips

        self._post_scroll()

    def scroll_left(self, cols):
        if not self.affect_planes:
            return

        vid_width = self.vid_width
        vid_height = self.vid_height

        for plane in self.affect_planes:
            plane.move_mem(-cols)  # Usually moves contents left by 4 pixels, 2 on low resolution

            for y in range(1, vid_height + 1):
                # Erase 4-pixel block to right of line in high resolution, 2 on low resolution
                plane.zero_block(vid_width * y - cols, cols)

        self._post_scroll()

    def scroll_right(self, cols):
        if not self.affect_planes:
            return

        vid_width = self.vid_width
        vid_height = self.vid_height

        for plane in self.affect_planes:
            plane.move_mem(cols)  # Usually moves contents right by 4 pixels, 2 on low resolution

            for y in range(vid_height):
                # Erase 4-pixel block to left of line in high resolution, 2 on low resolution
                plane.zero_block(vid_width * y, cols)

        self._post_scroll()

    def scroll_down(self, rows):
        if not self.affect_planes:
            return

        mem_offset = rows * self.vid_width

        for plane in self.affect_planes:
            plane.move_mem(mem_offset)  # Usually moves contents down by 1 pixel, 0.5 on low resolution
            plane.zero_block(0, mem_offset)  # Erase the top strips

        self._post_scroll()

    def _post_scroll(self):
        # Redraw whole screen after a scroll (slow and nasty)
        for y in range(self.vid_height):
            for x in range(self.vid_width):
                self._render_pixel(x, y)

    def refresh_display(self):
        self.renderer.refresh_display()

    def switch_planes(self, mask):
        self.affect_planes = self.mask_to_planes[mask]

    def get_vid_size(self):
        return self.vid_width, self.vid_height

    def report_perf(self, fps=0, ops=0):
        title = "{} - {} FPS, {} OPS".format(APP_NAME, fps, ops)
        self.renderer.set_title(title)
