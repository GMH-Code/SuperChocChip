#!/usr/bin/env python3

__copyright__ = "Copyright (C) 2022 Gregory Maynard-Hoare"
__license__ = "GNU Affero General Public License v3.0"

import unittest
from scchip.constants import ARCH_XO_CHIP_16, DEFAULT_KEYMAP
from scchip.cpu import CPU, CPUError
from scchip.debugger import Debugger
from scchip.ram import RAM
from scchip.stack import Stack
from scchip.framebuffer import Framebuffer
from scchip.renderers.r_null import Renderer
from scchip.inputs.i_null import Inputs
from scchip.audio.a_null import Audio

# NOTE: Complete quirk behaviour tests on instructions


class TestCPU(unittest.TestCase):
    def setUp(self):
        self.ram = RAM()
        self.ram.resize(0x10000)
        self.stack = Stack(16)
        renderer = Renderer(use_colour=True)
        self.framebuffer = Framebuffer(renderer, num_planes=4)
        self.cpu = CPU(
            ARCH_XO_CHIP_16, self.ram, self.stack, self.framebuffer, Inputs(DEFAULT_KEYMAP, renderer), Audio(),
            Debugger()
        )
        self.cpu.pc = 0x200

    def test_cpu_fetch(self):
        self.cpu.ram.write_block(0x200, bytearray(b"\xFF\xFE"))
        self.assertEqual(0xFFFE, self.cpu.fetch())

    def test_cpu_refresh_framebuffer(self):
        # Only checks it runs, doesn't check output
        self.cpu.refresh_framebuffer()

    def test_cpu_inc_pc_no_wrap(self):
        self.cpu.inc_pc()
        self.assertEqual(0x202, self.cpu.pc)

    def test_cpu_inc_pc_wrap(self):
        self.cpu.pc = 0xFFE
        self.cpu.inc_pc()
        self.assertEqual(0x000, self.cpu.pc)

    def test_cpu_dec_pc_no_wrap(self):
        self.cpu.dec_pc()
        self.assertEqual(0x1FE, self.cpu.pc)

    def test_cpu_dec_pc_wrap(self):
        self.cpu.pc = 0x000
        self.cpu.dec_pc()
        self.assertEqual(0xFFE, self.cpu.pc)

    def _check_invalid_opcode_caught(self, opcode):
        self.cpu.opcode = opcode
        self.assertRaises(CPUError, self.cpu.decode_exec)

    def test_cpu_decode_exec_fail(self):
        # Not checking Fx75/Fx85
        for i in 0x0000, 0x0001, 0x5001, 0x8008, 0x800F, 0x9001, 0xE09F, 0xE0A2, 0xF100, 0xFFFF:
            self._check_invalid_opcode_caught(i)

    def _check_opcode(self, opcode):
        self.cpu.opcode = opcode
        self.cpu.decode_exec()

    # Tests for CHIP-8 (and above)

    def test_cpu_00e0(self):  # CLS
        self._check_opcode(0x00E0)

    def test_cpu_00ee(self):  # RET
        self.stack.push(0xFFE)
        self._check_opcode(0x00EE)
        self.assertEqual(0xFFE, self.cpu.pc)

    def test_cpu_1nnn(self):  # JP addr
        self._check_opcode(0x1FFD)
        self.assertEqual(0xFFD, self.cpu.pc)

    def test_cpu_2nnn(self):  # CALL addr
        self._check_opcode(0x2FFC)
        self.assertEqual(0xFFC, self.cpu.pc)
        self.assertEqual(0x200, self.stack.pop())

    def test_cpu_3xkk(self):  # SE Vx, byte
        self.cpu.v[0x2] = 0x11
        self._check_opcode(0x3212)
        self.assertEqual(0x200, self.cpu.pc)
        self.cpu.v[0x2] = 0x12
        self._check_opcode(0x3212)
        self.assertEqual(0x202, self.cpu.pc)

    def test_cpu_4xkk(self):  # SNE Vx, byte
        self.cpu.v[0x2] = 0x11
        self._check_opcode(0x4212)
        self.assertEqual(0x202, self.cpu.pc)
        self.cpu.v[0x2] = 0x12
        self._check_opcode(0x4212)
        self.assertEqual(0x202, self.cpu.pc)

    def test_cpu_5xy0(self):  # SE Vx, Vy
        self.cpu.v[0x2] = 0x11
        self.cpu.v[0x3] = 0x12
        self._check_opcode(0x5230)
        self.assertEqual(0x200, self.cpu.pc)
        self.cpu.v[0x3] = 0x11
        self._check_opcode(0x5230)
        self.assertEqual(0x202, self.cpu.pc)

    def test_cpu_6xkk(self):  # LD Vx, byte
        self._check_opcode(0x62FE)
        self.assertEqual(0xFE, self.cpu.v[0x2])

    def test_cpu_7xkk(self):  # ADD Vx, byte
        self._check_opcode(0x72FE)
        self.assertEqual(0xFE, self.cpu.v[0x2])
        self._check_opcode(0x7201)
        self.assertEqual(0xFF, self.cpu.v[0x2])
        self._check_opcode(0x7201)
        self.assertEqual(0x00, self.cpu.v[0x2])

    def test_cpu_8xy0(self):  # LD Vx, Vy
        self.cpu.v[0x1] = 0x1
        self.cpu.v[0x2] = 0x2
        self._check_opcode(0x8120)
        self.assertEqual(0x2, self.cpu.v[0x1])

    def _prepare_alu(self):
        self.cpu.v[0x1] = 0b10111000
        self.cpu.v[0x2] = 0b10001110

    def test_cpu_8xy1(self):  # OR Vx, Vy
        self._prepare_alu()
        self._check_opcode(0x8121)
        self.assertEqual(0b10111110, self.cpu.v[0x1])

    def test_cpu_8xy2(self):  # AND Vx, Vy
        self._prepare_alu()
        self._check_opcode(0x8122)
        self.assertEqual(0b10001000, self.cpu.v[0x1])

    def test_cpu_8xy3(self):  # XOR Vx, Vy
        self._prepare_alu()
        self._check_opcode(0x8123)
        self.assertEqual(0b00110110, self.cpu.v[0x1])

    def test_cpu_8xy4_carry(self):  # ADD Vx, Vy (carry)
        self._prepare_alu()
        self._check_opcode(0x8124)
        self.assertEqual(0b01000110, self.cpu.v[0x1])
        self.assertEqual(0x1, self.cpu.v[0xF])

    def test_cpu_8xy4_no_carry(self):  # ADD Vx, Vy (no carry)
        self.cpu.v[0x1] = 0x1
        self.cpu.v[0xF] = 0x2  # Use Vf as an input to check flag ordering too
        self._check_opcode(0x81F4)
        self.assertEqual(0x3, self.cpu.v[0x1])
        self.assertEqual(0x0, self.cpu.v[0xF])

    def test_cpu_8xy5_borrow(self):  # SUB Vx, Vy (borrow)
        self.cpu.v[0x1] = 0x3
        self.cpu.v[0x2] = 0x1
        self._check_opcode(0x8125)
        self.assertEqual(0x2, self.cpu.v[0x1])
        self.assertEqual(0x1, self.cpu.v[0xF])
        self.cpu.v[0x1] = 0xFF
        self.cpu.v[0xF] = 0xFF
        self._check_opcode(0x81F5)
        self.assertEqual(0x0, self.cpu.v[0x1])
        self.assertEqual(0x1, self.cpu.v[0xF])

    def test_cpu_8xy5_no_borrow(self):  # SUB Vx, Vy (no borrow)
        self.cpu.v[0x1] = 0x1
        self.cpu.v[0x2] = 0x2  # Use Vf as an input to check flag ordering too
        self._check_opcode(0x8125)
        self.assertEqual(0xFF, self.cpu.v[0x1])
        self.assertEqual(0x0, self.cpu.v[0xF])

    def test_cpu_8xy6_borrow(self):  # SHR Vx {, Vy}
        self.cpu.v[0x1] = 0x4
        self.cpu.v[0x2] = 0x1  # Use Vf as an input to check flag ordering too
        self._check_opcode(0x8126)
        self.assertEqual(0x0, self.cpu.v[0x1])
        self.assertEqual(0x1, self.cpu.v[0x2])
        self.assertEqual(0x1, self.cpu.v[0xF])

    def test_cpu_8xy6_no_borrow(self):  # SHR Vx {, Vy}
        self.cpu.v[0x1] = 0x4
        self.cpu.v[0x2] = 0x1
        self._check_opcode(0x8216)
        self.assertEqual(0x4, self.cpu.v[0x1])
        self.assertEqual(0x2, self.cpu.v[0x2])
        self.assertEqual(0x0, self.cpu.v[0xF])

    def test_cpu_8xy7(self):  # SUBN Vx, Vy (borrows already tested in SUB)
        self.cpu.v[0x1] = 0x4
        self.cpu.v[0x2] = 0x2
        self._check_opcode(0x8127)
        self.assertEqual(0xFE, self.cpu.v[0x1])
        self.assertEqual(0x2, self.cpu.v[0x2])
        self.assertEqual(0x0, self.cpu.v[0xF])

    def test_cpu_8xye_carry(self):  # SHL Vx {, Vy}
        self.cpu.v[0x1] = 0x4
        self.cpu.v[0x2] = 0x2
        self._check_opcode(0x812E)
        self.assertEqual(0x4, self.cpu.v[0x1])
        self.assertEqual(0x2, self.cpu.v[0x2])
        self.assertEqual(0x0, self.cpu.v[0xF])

    def test_cpu_8xye_no_carry(self):  # SHL Vx {, Vy}
        self.cpu.v[0x1] = 0xFE
        self.cpu.v[0x4] = 0x1
        self._check_opcode(0x814E)
        self.assertEqual(0x2, self.cpu.v[0x1])
        self.assertEqual(0x1, self.cpu.v[0x4])
        self.assertEqual(0x0, self.cpu.v[0xF])

    def test_cpu_9xy0(self):  # SNE Vx, Vy
        self.cpu.v[0x2] = 0x15
        self.cpu.v[0x3] = 0x16
        self._check_opcode(0x9230)
        self.assertEqual(0x202, self.cpu.pc)
        self.cpu.v[0x3] = 0x15
        self._check_opcode(0x9230)
        self.assertEqual(0x202, self.cpu.pc)

    def test_cpu_annn(self):  # LD I, addr
        self.assertEqual(0, self.cpu.i)
        self._check_opcode(0xAFF1)
        self.assertEqual(0xFF1, self.cpu.i)

    def test_cpu_bnnn(self):  # JP V0, addr
        self._check_opcode(0xB002)
        self.assertEqual(0x2, self.cpu.pc)
        self.cpu.v[0x0] = 0x1
        self._check_opcode(0xB102)
        self.assertEqual(0x103, self.cpu.pc)
        self.cpu.v[0x0] = 0xFD
        self._check_opcode(0xBF0E)
        self.assertEqual(0xB, self.cpu.pc)

    def test_cpu_cxkk(self):  # RND Vx, byte
        # We could properly check this with lots of random samples,
        # but, for now, just check the call is okay.
        self._check_opcode(0xC1FE)

    def test_cpu_dxyn(self):  # DRW Vx, Vy, nibble
        # For now, we will not check the entire drawing routine.
        self._check_opcode(0xD224)

    def test_cpu_ex9e(self):  # SKP Vx
        self._check_opcode(0xE19E)
        self.assertEqual(0x200, self.cpu.pc)

    def test_cpu_exa1(self):  # SKNP Vx
        self._check_opcode(0xE1A1)
        self.assertEqual(0x202, self.cpu.pc)

    def test_cpu_fx07(self):  # LD Vx, DT
        self.assertEqual(0x0, self.cpu.v[0x2])
        self.cpu.dt = 0x2
        self._check_opcode(0xF207)
        self.assertEqual(0x2, self.cpu.v[0x2])

    def test_cpu_fx0a(self):  # LD Vx, K
        self.assertEqual(0x200, self.cpu.pc)
        self._check_opcode(0xF30A)
        self.assertEqual(0x1FE, self.cpu.pc)

    def test_cpu_fx15(self):  # LD DT, Vx
        self.assertEqual(0x0, self.cpu.dt)
        self.cpu.v[0x2] = 0x3
        self._check_opcode(0xF215)
        self.assertEqual(0x3, self.cpu.dt)

    def test_cpu_fx18(self):  # LD ST, Vx
        self.assertEqual(0x0, self.cpu.ds)
        self.cpu.v[0x3] = 0x4
        self._check_opcode(0xF318)
        self.assertEqual(0x4, self.cpu.ds)

    def test_cpu_fx1e_no_overflow(self):  # ADD I, Vx
        self.cpu.v[0x1] = 0x2
        self.cpu.i = 0x3
        self._check_opcode(0xF11E)
        self.assertEqual(0x5, self.cpu.i)
        self.assertEqual(0x0, self.cpu.v[0xF])

    def test_cpu_fx1e_overflow_normal(self):  # ADD I, Vx
        self.cpu.v[0x3] = 0xFE
        self.cpu.i = 0xFFFE
        self._check_opcode(0xF31E)
        self.assertEqual(0xFC, self.cpu.i)
        self.assertEqual(0x0, self.cpu.v[0xF])

    def test_cpu_fx1e_overflow_amiga(self):  # ADD I, Vx
        self.cpu.index_overflow_quirks = True
        self.cpu.v[0x4] = 0xFD
        self.cpu.i = 0xFFFD
        self._check_opcode(0xF41E)
        self.assertEqual(0xFA, self.cpu.i)
        self.assertEqual(0x1, self.cpu.v[0xF])

    def test_cpu_fx29(self):  # LD F, Vx
        self.cpu.v[0x1] = 0x9
        self._check_opcode(0xF129)
        self.assertEqual(0x7D, self.cpu.i)

    def test_cpu_fx33_normal(self):  # LD B, Vx
        self.cpu.i = 0x0
        self.cpu.v[0x1] = 0xFE
        self._check_opcode(0xF133)
        # Ensure 254 (base 10 of 0xFE) is calculated
        self.assertEqual(0x2, self.ram.read(0x0000))
        self.assertEqual(0x5, self.ram.read(0x0001))
        self.assertEqual(0x4, self.ram.read(0x0002))

    def test_cpu_fx33_memory_wrap(self):  # LD B, Vx
        self.cpu.i = 0xFFFE
        self.cpu.v[0x2] = 0xFD
        self._check_opcode(0xF233)
        # Ensure 253 (base 10 of 0xFD) is calculated
        self.assertEqual(0x2, self.ram.read(0xFFFE))
        self.assertEqual(0x5, self.ram.read(0xFFFF))
        self.assertEqual(0x3, self.ram.read(0x0000))

    def test_cpu_fx55(self):  # LD [I], Vx
        self.cpu.v[0x0] = 3
        self.cpu.v[0x1] = 2
        self.cpu.v[0x2] = 1  # Shouldn't be written into RAM @ 0x0001
        self.cpu.i = 0xFFFF
        self._check_opcode(0xF155)
        self.assertEqual(0x3, self.ram.read(0xFFFF))
        self.assertEqual(0x2, self.ram.read(0x0000))
        self.assertEqual(0x0, self.ram.read(0x0001))

    def test_cpu_fx65(self):  # LD Vx, [I]
        self.cpu.i = 0xFFFF
        self.ram.write(0xFFFF, 0x6)
        self.ram.write(0x0000, 0x5)
        self.ram.write(0x0001, 0x4)  # Shouldn't be copied to register V2
        self._check_opcode(0xF165)
        self.assertEqual(0x6, self.cpu.v[0])
        self.assertEqual(0x5, self.cpu.v[1])
        self.assertEqual(0x0, self.cpu.v[2])

    # Tests for Super-CHIP 1.0 (and above)

    def test_cpu_00fd(self):  # EXIT
        self.cpu.pc = 0x0002
        self._check_opcode(0x00FD)
        self.assertEqual(0x0, self.cpu.pc)
        self._check_opcode(0x00FD)
        self.assertEqual(0xFFE, self.cpu.pc)

    def test_cpu_00fe_00ff(self):  # LOW / HIGH
        self.assertEqual(64, self.framebuffer.vid_width)
        self.assertEqual(32, self.framebuffer.vid_height)
        self._check_opcode(0x00FF)
        self.assertEqual(128, self.framebuffer.vid_width)
        self.assertEqual(64, self.framebuffer.vid_height)
        self._check_opcode(0x00FE)
        self.assertEqual(64, self.framebuffer.vid_width)
        self.assertEqual(32, self.framebuffer.vid_height)

    def test_cpu_fx75(self):  # LD R, Vx
        for i in range(0x10):
            self.cpu.v[i] = i + 1

        self._check_opcode(0xF975)
        self.assertEqual(1, self.cpu.rpl[0])
        self.assertEqual(2, self.cpu.rpl[1])
        self.assertEqual(10, self.cpu.rpl[9])
        self.assertEqual(0, self.cpu.rpl[11])

    def test_cpu_fx85(self):  # LD Vx, R
        for i in range(0x10):
            self.cpu.rpl[i] = i + 2

        self._check_opcode(0xF985)
        self.assertEqual(2, self.cpu.v[0])
        self.assertEqual(3, self.cpu.v[1])
        self.assertEqual(11, self.cpu.v[9])
        self.assertEqual(0, self.cpu.v[11])

    # Tests for Super-CHIP 1.1 (and above)

    def test_cpu_00fb_00fc(self):  # SCR / SCL
        # Just check calls execute.  Scrolling checked in framebuffer tests
        self._check_opcode(0x00FB)
        self._check_opcode(0x00FC)

    def test_cpu_fx30(self):  # LD HF, Vx
        # For now, just check call executes
        self._check_opcode(0xF130)

    def test_cpu_00cn_00dn(self):  # SCD n (Super-CHIP 1.1 and above) / SCU n (XO-CHIP only)
        for opcode in 0x00C1, 0x00D1:
            self._check_opcode(0x00FE)  # Switch to lo-res mode
            # Check half-pixel scrolling is raised as unsupported
            self.assertRaises(CPUError, self._check_opcode, opcode)
            self._check_opcode(opcode + 1)
            # Check regular scrolling
            self._check_opcode(0x00FF)  # Switch to high-res mode
            self._check_opcode(opcode)  # This should now work

    # Tests for XO-CHIP

    def test_cpu_5xy2(self):  # XST Vx, Vy
        for i in range(1, 5):
            self.cpu.v[i] = i

        self.cpu.i = 0xFFFF
        self._check_opcode(0x5232)
        self.assertEqual(2, self.ram.read(0xFFFF))
        self.assertEqual(3, self.ram.read(0x0000))
        self.assertEqual(0, self.ram.read(0x0001))

    def test_cpu_5xy3(self):  # XLD Vx, Vy
        for i in range(3, 7):
            self.ram.write((0xFFFC + i) & 0xFFFF, i)

        self.assertEqual(3, self.ram.read(0xFFFF))
        self.assertEqual(4, self.ram.read(0x0000))
        self.assertEqual(5, self.ram.read(0x0001))
        self.cpu.i = 0xFFFF
        self._check_opcode(0x5233)
        self.assertEqual(3, self.cpu.v[2])
        self.assertEqual(4, self.cpu.v[3])
        self.assertEqual(0, self.cpu.v[4])

    def test_cpu_fx00(self):  # XLDL I, addr
        self.assertRaises(CPUError, self._check_opcode, 0xF100)

    def test_cpu_fn01(self):  # XPLA Vx
        for opcode, plane_count in (0xF001, 0), (0xF101, 1), (0xF201, 1), (0xF301, 2), (0xFF01, 4):
            self._check_opcode(opcode)
            self.assertEqual(plane_count, len(self.framebuffer.get_affected_planes()))

    def test_cpu_fx02(self):  # XSTA
        # Only F002 is valid, so check F102 throws exception
        self.assertRaises(CPUError, self._check_opcode, 0xF102)
        # Unsupported, so just check call executes
        self._check_opcode(0xF002)

    def test_cpu_fx3a(self):  # XPR
        # Unsupported, so just check call executes
        self._check_opcode(0xF13A)

    # Tests for other CPU architecture quirks

    def test_cpu_logic_quirks(self):
        for logic_quirks in False, True:
            self.cpu.v[0xF] = 0x2
            self.cpu.logic_quirks = logic_quirks

            for i in range(4):
                self._check_opcode(0x8120 + i)
                self.assertEqual(int(not logic_quirks) * 2, self.cpu.v[0xF])
