#!/usr/bin/env python3

"""
Stack Emulator

It is unnecessary to include the CPU call stack as part of system RAM, because
there is no specified location for it.  There is also no stack pointer (SP)
register exposed to the running program.  This means we can simply wrap lists
to fully (and quickly) emulate it.

Keeping the stack out of RAM is technically inaccurate for an emulator, but it
doesn't look like anything does (or should) rely on direct stack manipulation.
To mess with the stack in this way would also be bad practice and somewhat
unpredictable as you couldn't rely on any specific system taking advantage of
it.

For these reasons, and for system performance, we'll leave the stack separate
so we don't have to keep mapping values in and out of system RAM.
"""

__copyright__ = "Copyright (C) 2022 Gregory Maynard-Hoare"
__license__ = "GNU Affero General Public License v3.0"


class StackError(Exception):
    pass


class Stack:
    def __init__(self, size):
        self.items = []
        self.size = size

    def push(self, item):
        # Fetching the stack size with 'len' should be immediate, so no slow loop
        if len(self.items) >= self.size:
            raise StackError("Stack overflow")

        self.items.append(item)

    def pop(self):
        try:
            return self.items.pop()
        except IndexError:
            raise StackError("Stack underflow") from None

    def get_items(self):
        # For debugging
        return self.items
