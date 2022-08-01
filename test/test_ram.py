#!/usr/bin/env python3

__copyright__ = "Copyright (C) 2022 Gregory Maynard-Hoare"
__license__ = "GNU Affero General Public License v3.0"

import unittest
from scchip.ram import RAM, RAMError


class TestRAM(unittest.TestCase):
    def setUp(self):
        self.ram = RAM()
        self.ram.resize(5)

    def test_ram_init(self):
        ram = RAM()
        self.assertEqual("", ram.mem.hex())

    def test_ram_resize(self):
        self.assertEqual("0000000000", self.ram.mem.hex())

    def test_ram_write(self):
        self.ram.write(1, 255)
        self.assertEqual("00ff000000", self.ram.mem.hex())

    def test_ram_write_block(self):
        self.ram.write_block(1, bytearray(b"\xFD\xFE"))
        self.ram.write_block(4, bytearray(b"\xFF"))
        self.assertEqual("00fdfe00ff", self.ram.mem.hex())

    def test_ram_byte_overflow(self):
        self.assertRaises(RAMError, self.ram.write, 5, 255)

    def test_ram_block_overflow(self):
        self.assertRaises(RAMError, self.ram.write_block, 4, bytearray(b"\xFE\xFF"))

    def test_ram_move_left(self):
        self.ram.write_block(1, bytearray(b"\xFC\xFD\xFE"))
        self.assertEqual("00fcfdfe00", self.ram.mem.hex())
        self.ram.move_mem(-1)
        self.assertEqual("fcfdfe0000", self.ram.mem.hex())
        self.ram.move_mem(-2)
        self.assertEqual("fe00000000", self.ram.mem.hex())
        self.ram.move_mem(-1)
        self.assertEqual("0000000000", self.ram.mem.hex())

    def test_ram_move_right(self):
        self.ram.write_block(1, bytearray(b"\xFC\xFD\xFE"))
        self.assertEqual("00fcfdfe00", self.ram.mem.hex())
        self.ram.move_mem(1)
        self.assertEqual("0000fcfdfe", self.ram.mem.hex())
        self.ram.move_mem(2)
        self.assertEqual("00000000fc", self.ram.mem.hex())
        self.ram.move_mem(1)
        self.assertEqual("0000000000", self.ram.mem.hex())

    def test_ram_zero_block(self):
        self.ram.write_block(0, bytearray(b"\xFC\xFD\xFE\xFF"))
        self.assertEqual("fcfdfeff00", self.ram.mem.hex())
        self.ram.zero_block(1, 2)
        self.assertEqual("fc0000ff00", self.ram.mem.hex())

    def test_ram_clear(self):
        self.ram.write_block(1, bytearray(b"\xFD\xFE"))
        self.assertEqual("00fdfe0000", self.ram.mem.hex())
        self.ram.clear()
        self.assertEqual("0000000000", self.ram.mem.hex())
