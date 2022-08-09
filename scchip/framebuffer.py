#!/usr/bin/env python3

"""
Framebuffer Emulator

Pixels are written here, and are usually only drawn to the actual display (the
host rendering system) at 60Hz.  We probably could get away with not having a
Framebuffer, but then we'd rely on rendering frameworks supporting specific
drawing and scrolling methods, and there would also be no guarantee of
rendering speed when calling external libraries that often.  PyGame/Curses can
lower speed substantially when calling some methods tens/hundreds of thousands
of times a second.

Unlike other computers, programs for this system cannot write directly into
video RAM.  Instead, sprites are drawn to the screen using an XOR method
against one or more planes.

Multiple planes are supported, such as 4 planes for 16 colours.  Before
rendering, these planes are merged and form a specific colour depending on
which pixel combinations are set.

Collisions (where any pixel was set, but was unset by an XOR), are reported.
If using Super-CHIP (or higher) variants, the number of collided rows are
reported, rather than just a flag being set.
"""

__copyright__ = "Copyright (C) 2022 Gregory Maynard-Hoare"
__license__ = "GNU Affero General Public License v3.0"

from .constants import APP_NAME
from .ram import RAM


class FramebufferError(Exception):
    pass


class Framebuffer():
    def __init__(self, renderer, num_planes=1, allow_wrapping=True):
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

        # Map all the masks into matching planes for fast lookup
        self.mask_to_planes = {}

        for mask in range(2 ** num_planes):
            self.mask_to_planes[mask] = []

            for plane_num in range(num_planes):
                if mask & 2 ** plane_num:
                    self.mask_to_planes[mask].append(self.ram_banks[plane_num])

        self.affect_planes = self.mask_to_planes[1]

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
        colour = 0

        for plane_num in range(self.num_planes):
            if self.ram_banks[plane_num].read(vram_loc):
                colour += 2 ** plane_num

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
        self.affect_planes = self.mask_to_planes.get(mask)

        if self.affect_planes is None:
            raise FramebufferError("Selected display plane is out of range for this architecture")

    def get_vid_size(self):
        return self.vid_width, self.vid_height

    def report_perf(self, fps=0, ops=0):
        title = "{} - {} FPS, {} OPS".format(APP_NAME, fps, ops)
        self.renderer.set_title(title)
