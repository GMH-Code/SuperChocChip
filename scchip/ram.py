#!/usr/bin/env python3

"""
RAM Emulator

Supports reading and writing of blocks of memory or individual bytes.  Also
supports fast moving (copying) and zeroing of memory blocks.

Currently the moving of memory only needs to support rotating the entire bank,
when emulating screen scrolling.
"""

__copyright__ = "Copyright (C) 2022 Gregory Maynard-Hoare"
__license__ = "GNU Affero General Public License v3.0"


class RAMError(Exception):
    pass


class RAM:
    def __init__(self):
        self.resize(0)

    def resize(self, mem_size):
        self.mem = memoryview(bytearray(b"\x00" * mem_size))
        self.mem_top = mem_size - 1
        self.mem_size = mem_size

    def read(self, location):
        return self.mem[location]

    def read_block(self, location, size=1):
        return self.mem[location:location + size]

    def write(self, location, byte):
        self.check_overflow(location)
        self.mem[location] = byte

    def write_block(self, location, block):
        block_size = len(block)
        block_top = location + block_size
        self.check_overflow(block_top - 1)
        self.mem[location:block_top] = block

    def check_overflow(self, location):
        if location > self.mem_top:
            raise RAMError("Memory overflow")

    def move_mem(self, offset):
        # Fast slice-based memory mover.  Leaves original data behind.  At present, this is only used to shift
        # everything, so there is no start, end, or size.
        if offset < 0:
            self.mem[:offset] = self.mem[-offset:]
        else:
            self.mem[offset:] = self.mem[:-offset]

    def zero_block(self, offset, size):
        block_top = offset + size
        self.check_overflow(block_top - 1)

        for i in range(offset, block_top):
            self.mem[i] = 0x00

    def clear(self):
        # We could reallocate the entire array instead
        self.zero_block(0, self.mem_size)
