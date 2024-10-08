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
        self.vid_cache = RAM()
        self.ram_banks = []
        self.frame_delta = {}
        self.report_perf()

        for _ in range(num_planes):
            self.ram_banks.append(RAM())

        # Map all the masks into matching planes for fast lookup.  We are looking up by index number, so this will
        # retain O(1) complexity, but should be slightly faster than a dict on access.
        self.mask_to_planes = []

        for mask in range(2 ** num_planes):
            mask_planes = []

            for plane_num in range(num_planes):
                if mask & 2 ** plane_num:
                    mask_planes.append(self.ram_banks[plane_num])

            self.mask_to_planes.append(mask_planes)

        self.affect_planes = self.mask_to_planes[1]

    def resize_vid(self, vid_width, vid_height):
        self.vid_width = vid_width
        self.vid_height = vid_height
        self.vid_size = self.vid_width * self.vid_height
        self.vid_cache.resize(self.vid_size)

        for ram_bank in self.ram_banks:
            ram_bank.resize(self.vid_size)  # Update RAM size

        self.renderer.set_resolution(vid_width, vid_height)  # Update screen resolution
        self.frame_delta = {}  # The video cache and the screen are now both blank

    def reset_vid(self):
        for ram_bank in self.ram_banks:
            ram_bank.clear()

        self._redraw_all()

    def clear(self):
        if not self.affect_planes:
            return

        for plane in self.affect_planes:
            plane.clear()

        self._redraw_all()

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
        pixel = plane.read(vram_loc) ^ 0xFF
        plane.write(vram_loc, pixel)
        self._render_pixel(vram_loc)
        return not pixel

    def _render_pixel(self, vram_loc):
        # Render the pixel to the display
        ram_banks = self.ram_banks
        colour = 0

        for plane_num in range(self.num_planes):
            if ram_banks[plane_num].read(vram_loc):
                colour += 2 ** plane_num

        self.frame_delta[vram_loc] = colour

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

        self._redraw_all()

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

        self._redraw_all()

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

        self._redraw_all()

    def scroll_down(self, rows):
        if not self.affect_planes:
            return

        mem_offset = rows * self.vid_width

        for plane in self.affect_planes:
            plane.move_mem(mem_offset)  # Usually moves contents down by 1 pixel, 0.5 on low resolution
            plane.zero_block(0, mem_offset)  # Erase the top strips

        self._redraw_all()

    def _redraw_all(self):
        # Redraw whole screen after a scroll or clear.  The video cache should take the load off the renderer a bit
        render_pixel = self._render_pixel

        for vram_loc in range(self.vid_size):
            render_pixel(vram_loc)

    def refresh_display(self):
        # Request the renderer updates altered pixels and then refreshes the display.  This method results in a huge
        # (around 5x) speed up when using PyPy with graphically-intensive games, and a tiny improvement with CPython.
        vid_cache_read = self.vid_cache.read
        vid_cache_write = self.vid_cache.write
        renderer_set_pixel = self.renderer.set_pixel
        content_changed = False

        for vram_loc, colour in self.frame_delta.items():
            if vid_cache_read(vram_loc) != colour:
                renderer_set_pixel(vram_loc, colour)
                vid_cache_write(vram_loc, colour)
                content_changed = True

        self.frame_delta.clear()
        self.renderer.refresh_display(content_changed)

    def switch_planes(self, mask):
        try:
            self.affect_planes = self.mask_to_planes[mask]
        except IndexError:
            raise FramebufferError("Selected display plane is out of range for this architecture") from None

    def get_vid_size(self):
        return self.vid_width, self.vid_height

    def report_perf(self, fps=0, ops=0):
        title = "{} - {} FPS, {} OPS".format(APP_NAME, fps, ops)
        self.renderer.set_title(title)
