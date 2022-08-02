#!/usr/bin/env python3

__copyright__ = "Copyright (C) 2022 Gregory Maynard-Hoare"
__license__ = "GNU Affero General Public License v3.0"

import unittest
from scchip.renderers.r_null import Renderer
from scchip.framebuffer import Framebuffer


class TestFrameBuffer(unittest.TestCase):
    def setUp(self):
        self.renderer_mono = Renderer()
        self.renderer_col = Renderer()
        self.framebuffer_mono = Framebuffer(self.renderer_mono, num_planes=1, allow_wrapping=False)
        self.framebuffer_col = Framebuffer(self.renderer_col, num_planes=2, allow_wrapping=True)
        self.framebuffer_mono.resize_vid(4, 5)
        self.framebuffer_col.resize_vid(3, 4)

    def test_framebuffer_resize_vid(self):
        self.assertEqual(1, len(self.framebuffer_mono.ram_banks))
        self.assertEqual(2, len(self.framebuffer_col.ram_banks))
        self.assertEqual((4, 5), (self.renderer_mono.width, self.renderer_mono.height))
        self.assertEqual((3, 4), (self.renderer_col.width, self.renderer_col.height))

    def test_framebuffer_plane_control(self):
        fbm = self.framebuffer_mono
        fbm.switch_planes(0b1)
        self.assertEqual(1, len(fbm.get_affected_planes()))
        fbm.switch_planes(0b0)
        self.assertEqual(0, len(fbm.get_affected_planes()))
        self.assertRaises(KeyError, fbm.switch_planes, 0b10)

        fbc = self.framebuffer_col
        fbc.switch_planes(0b00)
        self.assertEqual(0, len(fbc.get_affected_planes()))
        fbc.switch_planes(0b01)
        self.assertEqual(1, len(fbc.get_affected_planes()))
        fbc.switch_planes(0b10)
        self.assertEqual(1, len(fbc.get_affected_planes()))
        fbc.switch_planes(0b11)
        self.assertEqual(2, len(fbc.get_affected_planes()))
        self.assertRaises(KeyError, fbc.switch_planes, 0b100)

    def test_framebuffer_writes_mono(self):
        fb = self.framebuffer_mono
        plane = fb.get_affected_planes()[0]
        fb.xor_pixel(0, 0, plane)
        self.assertEqual("ff00000000000000000000000000000000000000", plane.mem.hex())
        fb.xor_pixel(1, 1, plane)
        self.assertEqual("ff00000000ff0000000000000000000000000000", plane.mem.hex())
        fb.xor_pixel(4, 5, plane)  # Should do nothing as wrapping is off
        self.assertEqual("ff00000000ff0000000000000000000000000000", plane.mem.hex())

        # Check clear works
        fb.clear()
        self.assertEqual("0000000000000000000000000000000000000000", plane.mem.hex())

        # Check refresh (call only) works
        fb.refresh_display()

    def test_framebuffer_writes_col(self):
        fb = self.framebuffer_col
        fb.switch_planes(0b11)
        plane = fb.get_affected_planes()[1]
        fb.xor_pixel(0, 0, plane)
        self.assertEqual("ff0000000000000000000000", plane.mem.hex())
        fb.xor_pixel(1, 1, plane)
        self.assertEqual("ff000000ff00000000000000", plane.mem.hex())
        fb.xor_pixel(3, 4, plane)  # Should erase the first byte
        self.assertEqual("00000000ff00000000000000", plane.mem.hex())

        # Check clear works
        fb.clear()
        self.assertEqual("000000000000000000000000", plane.mem.hex())

        # Check refresh (call only) works
        fb.refresh_display()

    def test_framebuffer_scrolling(self):
        fb = self.framebuffer_col
        fb.switch_planes(0b11)
        plane = fb.get_affected_planes()[1]
        fb.xor_pixel(0, 0, plane)
        fb.xor_pixel(1, 1, plane)
        fb.xor_pixel(2, 3, plane)
        self.assertEqual("ff000000ff000000000000ff", plane.mem.hex())
        fb.scroll_right(1)
        self.assertEqual("00ff000000ff000000000000", plane.mem.hex())
        fb.scroll_left(1)
        self.assertEqual("ff000000ff00000000000000", plane.mem.hex())
        fb.scroll_left(1)
        self.assertEqual("000000ff0000000000000000", plane.mem.hex())
        fb.scroll_right(1)
        fb.xor_pixel(0, 0, plane)
        fb.xor_pixel(2, 3, plane)
        self.assertEqual("ff000000ff000000000000ff", plane.mem.hex())
        fb.scroll_down(1)
        self.assertEqual("000000ff000000ff00000000", plane.mem.hex())
        fb.scroll_up(1)
        self.assertEqual("ff000000ff00000000000000", plane.mem.hex())
        fb.clear()
        self.assertEqual("000000000000000000000000", plane.mem.hex())
