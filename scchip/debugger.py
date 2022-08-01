#!/usr/bin/env python3

"""
CPU Debugger

If enabled, this will output information before each instruction executed:
    * All 16 of the [V] registers, starting with most significant (Vf) and
      reducing to least significant (V0)
    * I  - Index register
    * DT - Delay timer
    * ST - Sound timer
    * PC - Program counter
    * OP - OpCode number
    * IN - Decoded instruction

If a crash occurs, all of the above will be outputted, with the addition of:
    * RPL   - Storage registers (if Super-CHIP 1.0, CHIP-48, or above)
    * Stack - Stack contents
"""

__copyright__ = "Copyright (C) 2022 Gregory Maynard-Hoare"
__license__ = "GNU Affero General Public License v3.0"

from .constants import ARCH_SUPERCHIP_1_0


class Debugger:
    def __init__(self):
        self.live = False

    def debug(self, cpu, instruction, verbose=False):
        debug_str = (
            "V: 0x" + ("{:02x}" * 16) + " I: 0x{:04x} DT: 0x{:02x} DS: 0x{:02x} PC: 0x{:03x} OP: 0x{:04x} IN: {}"
        ).format(
            *[cpu.v[reg_num] for reg_num in range(15, -1, -1)] +
            [cpu.i, cpu.dt, cpu.ds, cpu.debug_pc, cpu.opcode, instruction]
        )

        if verbose:
            if cpu.arch >= ARCH_SUPERCHIP_1_0:
                debug_str += ("\nRPL: 0x" + "{:02x}" * 16).format(*[cpu.rpl[reg_num] for reg_num in range(15, -1, -1)])

            stack_items = cpu.stack.get_items()
            stack_str = (" 0x{:03x}" * len(stack_items)).format(*stack_items)
            debug_str += ("\nStack:{}").format(stack_str or " (Empty)")

        return debug_str

    def set_live(self, enabled):
        self.live = enabled

    def is_live(self):
        return self.live

    def output(self, cpu, instruction):
        print(self.debug(cpu, instruction))
