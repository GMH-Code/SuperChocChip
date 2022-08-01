#!/usr/bin/env python3

__copyright__ = "Copyright (C) 2022 Gregory Maynard-Hoare"
__license__ = "GNU Affero General Public License v3.0"

import unittest
from scchip.stack import Stack, StackError


class TestStack(unittest.TestCase):
    def setUp(self):
        self.stack = Stack(3)

    def _populate_stack(self):
        self.stack.push(0x0)
        self.stack.push(0x1)
        self.stack.push(0xFFF)

    def test_stack_push_pop(self):
        self._populate_stack()
        self.assertEqual(0xFFF, self.stack.pop())
        self.assertEqual(0x1, self.stack.pop())
        self.assertEqual(0x0, self.stack.pop())

    def test_stack_overflow(self):
        self._populate_stack()
        self.assertRaises(StackError, self.stack.push, 0x1)

    def test_stack_underflow(self):
        self.assertRaises(StackError, self.stack.pop)
