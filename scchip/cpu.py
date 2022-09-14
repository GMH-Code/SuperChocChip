#!/usr/bin/env python3

"""
CPU Emulator (CHIP-8, Super-CHIP 1.0, Super-CHIP 1.1 and XO-CHIP)

Like a real computer, this is where most of the processing happens.  The main
CPU can potentially cycle at hundreds of thousands of instructions every
second, so this has to be as fast as possible.

Alterations should be checked against the included 'operations per second'
benchmark, to ensure any changes are an improvement.
"""

__copyright__ = "Copyright (C) 2022 Gregory Maynard-Hoare"
__license__ = "GNU Affero General Public License v3.0"

from time import perf_counter
from random import randint
from math import ceil
from .constants import APP_INTRO, ARCH_CHIP8, ARCH_SUPERCHIP_1_0, ARCH_CHIP48, ARCH_SUPERCHIP_1_1, ARCH_XO_CHIP

CPU_ENDIAN = "big"   # CHIP-8 is big-endian
TIMER_FREQ = 60.0    # 60Hz emulated system timer refresh
DISPLAY_FREQ = 60.0  # 60Hz emulated display refresh
DISPLAY_INTERVAL = 1.0 / DISPLAY_FREQ


class CPUError(Exception):
    pass


class CPU:
    def __init__(self, arch, ram, stack, framebuffer, inputs, audio, debugger, clock_speed=None, load_quirks=None,
                 shift_quirks=None, logic_quirks=None, index_overflow_quirks=None, index_increment_quirks=None,
                 jump_quirks=None, sprite_delay_quirks=None):

        self.arch = arch
        self.ram = ram
        self.stack = stack
        self.framebuffer = framebuffer
        self.inputs = inputs
        self.audio = audio
        self.debugger = debugger
        self.live_debug = self.debugger.is_live()
        self.sysfont_sm_loc = 0x50
        self.sysfont_bg_loc = 0xA0
        self.framebuffer.report_perf()

        if clock_speed is None:
            # Default clock speed
            auto_clock_speed = 0 if arch >= ARCH_SUPERCHIP_1_0 else 1000
        else:
            # User-specified clock speed (user can specify 0 for infinite)
            auto_clock_speed = clock_speed

        self.core_interval = None if auto_clock_speed <= 0 else 1.0 / auto_clock_speed
        arch_is_schip = (arch >= ARCH_SUPERCHIP_1_0 and arch <= ARCH_SUPERCHIP_1_1)  # Includes CHIP-48

        """
        Quirks
        ------

        - Load quirks           : Enabled on CHIP-8, Super-CHIP 1.1, and XO-CHIP systems only.
        - Shift quirks          : Enabled on Super-CHIP-based systems only.
        - Logic quirks          : Enabled on CHIP-8 systems only.
        - Index overflow quirks : Disabled.  Some Super-CHIP games fail if enabled.
        - Index increment quirks: Enabled for accurate CHIP-48 behaviour only.
        - Jump quirks           : Enabled on Super-CHIP-based systems only.
        """

        self.load_quirks = (arch >= ARCH_SUPERCHIP_1_1 or arch == ARCH_CHIP8) if load_quirks is None else load_quirks
        self.shift_quirks = arch_is_schip if shift_quirks is None else shift_quirks
        self.logic_quirks = (arch == ARCH_CHIP8) if logic_quirks is None else logic_quirks
        self.index_overflow_quirks = False if index_overflow_quirks is None else index_overflow_quirks
        self.index_increment_quirks = (
            (arch == ARCH_CHIP48) if index_increment_quirks is None else index_increment_quirks
        )
        self.jump_quirks = arch_is_schip if jump_quirks is None else jump_quirks
        self.sprite_delay_quirks = (arch == ARCH_CHIP8) if sprite_delay_quirks is None else sprite_delay_quirks

        # Define instruction pointers.
        # n = Nibble
        # kk = Byte
        # nnn = address
        # x/y = register (0-15)
        self.instructions = {
            # Initial lookup for instructions' first nibble
            0x0: self._0nnn,  # Alias for bitmask 0xFFFF
            0x1: self._1nnn,
            0x2: self._2nnn,
            0x3: self._3xkk,
            0x4: self._4xkk,
            0x5: self._5nnn_8nnn_9nnn,  # Alias for bitmask 0xF00F
            0x6: self._6xkk,
            0x7: self._7xkk,
            0x8: self._5nnn_8nnn_9nnn,  # Alias for bitmask 0xF00F
            0x9: self._5nnn_8nnn_9nnn,  # Alias for bitmask 0xF00F
            0xA: self._Annn,
            0xB: self._Bnnn,
            0xC: self._Cxkk,
            0xD: self._Dxyn,
            0xE: self._Ennn_Fnnn,  # Alias for bitmask 0xF0FF
            0xF: self._Ennn_Fnnn,  # Alias for bitmask 0xF0FF
            # Instructions beginning with nibble 0x0, bitmask 0xFFFF (i.e., exact match)
            0x00E0: self._00E0,
            0x00EE: self._00EE,
            # Instructions beginning with nibble 0x5/0x8/0x9, bitmask 0xF00F
            0x5000: self._5xy0,
            0x8000: self._8xy0,
            0x8001: self._8xy1,
            0x8002: self._8xy2,
            0x8003: self._8xy3,
            0x8004: self._8xy4,
            0x8005: self._8xy5,
            0x8006: self._8xy6,
            0x8007: self._8xy7,
            0x800E: self._8xyE,
            0x9000: self._9xy0,
            # Instructions beginning with nibble 0xE/0xF, bitmask 0xF0FF
            0xE09E: self._Ex9E,
            0xE0A1: self._ExA1,
            0xF000: self._Fx00,
            0xF007: self._Fx07,
            0xF00A: self._Fx0A,
            0xF015: self._Fx15,
            0xF018: self._Fx18,
            0xF01E: self._Fx1E,
            0xF029: self._Fx29,
            0xF033: self._Fx33,
            0xF055: self._Fx55,
            0xF065: self._Fx65
        }

        if arch >= ARCH_SUPERCHIP_1_0:
            # Add instructions for Super-CHIP 1.0 and above
            self.instructions.update(
                {
                    0x00FF: self._00FF,
                    0x00FE: self._00FE,
                    0xF075: self._Fx75,
                    0xF085: self._Fx85,
                    0x00FD: self._00FD
                }
            )

            self.rpl = memoryview(bytearray(16))

        if arch >= ARCH_SUPERCHIP_1_1:
            # Add instructions for Super-CHIP 1.1 and above
            self.instructions.update(
                {
                    0x00FB: self._00FB,
                    0x00FC: self._00FC,
                    0xF030: self._Fx30
                }
            )

            # Not worth having a separate way of accessing these, as there are only 16
            for n in range(0x10):  # Add scroll down functions
                self.instructions[0x00C0 | n] = self._00Cn

        if arch >= ARCH_XO_CHIP:
            # Add instructions for XO-CHIP
            self.instructions.update(
                {
                    0x5002: self._5xy2,
                    0x5003: self._5xy3,
                    0xF002: self._Fx02,  # Only F002 is used
                    0xF03A: self._Fx3A
                }
            )

            # Not worth having a separate way of accessing these, as there are only 16
            for n in range(0x10):  # Add scroll up functions
                self.instructions[0x00D0 | n] = self._00Dn

            for n in range(4):
                self.instructions[0xF001 | n << 8] = self._Fn01

        # Initialise registers
        self.v = memoryview(bytearray(16))  # Bytearrays are mutable, so this should be fast when a register is updated
        self.i = 0  # Index register
        # Index register cap (shouldn't affect programs since it can only reference addresses)
        self.i_bitmask = 0xFFF if arch < ARCH_XO_CHIP else 0xFFFF

        # Initialise timers
        self.dt = 0         # Delay timer integer (byte)
        self.ds = 0         # Sound timer integer (byte)
        self.dt_target = 0  # Delay timer switch-off time target
        self.ds_target = 0  # Sound timer switch-off time target

        # Initialise program counter, current opcode and realtime clock monitor
        self.pc = 0
        self.debug_pc = 0
        self.opcode = 0
        self.this_time = 0

        # Display-related vars
        self.framebuffer.resize_vid(64, 32)
        self.lo_res = True
        self.vblank_wait = False  # CHIP-8 vertical blanking support

        # Input-related vars
        self.awaiting_keypress = False

        # Audio-related vars
        self.audio_null = self.audio.is_null()

        # Performance-related vars
        self.next_display_update_time = 0
        self.perf_counter_fps = 0
        self.perf_counter_ops = 0
        self.next_perf_report_time = 0

    def run(self, start_location):
        self.pc = start_location

        while True:
            this_time = perf_counter()  # Do this first for maximum precision
            self.this_time = this_time

            # Performance counters
            if this_time >= self.next_perf_report_time:
                self.next_perf_report_time = int(this_time) + 1.0
                # Reporting the performance should be done before a refresh, as refreshing will likely show the report
                self.framebuffer.report_perf(self.perf_counter_fps, self.perf_counter_ops)
                self.perf_counter_ops = 0
                self.perf_counter_fps = 0

            # Prevent unnecessary display rendering in excess of host frame rate
            if this_time >= self.next_display_update_time:
                if self.inputs.process_messages():  # Process inputs at 60Hz too, to avoid slowdown
                    return
                self.next_display_update_time = this_time + DISPLAY_INTERVAL
                self.refresh_framebuffer()
                self.perf_counter_fps += 1

            # Decrement delay timers closely in relation to CPU timing.  So, if the CPU gets lagged, the timers will
            # jump.  We would normally attach this to clock speed, but since the clock speed is variable or undefined,
            # we will link it to actual time.
            if self.dt > 0:
                dt_float = (self.dt_target - this_time) * TIMER_FREQ
                self.dt = max(0, ceil(dt_float))

            if self.ds > 0:
                ds_float = (self.ds_target - this_time) * TIMER_FREQ
                self.ds = max(0, ceil(ds_float))

                if self.ds <= 0:
                    # Audio timer just reached zero.  Stop the audio.
                    self.audio.enable_buzzer(False)

            # Keep track of the program counter before altering it in any way for debugging purposes
            self.debug_pc = self.pc  # Do this all the time in case there is a crash
            self.opcode = self.fetch()
            self.inc_pc()  # Program counter updates after fetch (and technically before decode), but before execute
            self.decode_exec()

            if self.vblank_wait:
                # If we're using the original CHIP-8 system and a sprite was drawn, wait for vertical blank interrupt
                next_time = self.next_display_update_time

                while perf_counter() < next_time:
                    pass

                self.vblank_wait = False

            if self.core_interval is not None:
                # Wait for next CPU instruction.  Do this last for maximum precision (takes into account time spent on
                # this instruction)
                next_time = this_time + self.core_interval

                while perf_counter() < next_time:  # Unfortunately we have to do this to get the timing right
                    pass

            self.perf_counter_ops += 1

    def fetch(self):
        return int.from_bytes(self.ram.read_block(self.pc, 2), CPU_ENDIAN, signed=False)

    def _call_masked_instruction(self, masked_opcode):
        instruction = self.instructions.get(masked_opcode)

        if instruction is None:
            self._opcode_unsupported()

        instruction()

    def decode_exec(self):
        self._call_masked_instruction((0xF000 & self.opcode) >> 12)

    def refresh_framebuffer(self):
        # Render pending delta screen updates.  Should be called whenever there
        # will be a pause, a quit, or the display refresh interval expires.
        self.framebuffer.refresh_display()

    def inc_pc(self):
        self.pc = (self.pc + 2) & 0xFFF

    def dec_pc(self):
        # Only used to re-run instructions (e.g. keypress wait and exit types).
        self.pc = (self.pc - 2) & 0xFFF

    # References to Vx, Vy, byte and addr are always in the same opcode position throughout all instructions, so avoid
    # excessive code duplication (ever so slight slowdown).  Don't reference these more than necessary as they are
    # recalculated each time.
    @property
    def vx(self):
        return (self.opcode & 0xF00) >> 8

    @property
    def vy(self):
        return (self.opcode & 0xF0) >> 4

    @property
    def addr(self):
        return self.opcode & 0xFFF

    @property
    def byte(self):
        return self.opcode & 0xFF

    @property
    def nibble(self):
        return self.opcode & 0xF

    def _opcode_unsupported(self):
        raise CPUError(
            (
                "Emulation halted.\n\n" +
                "{}Debug info (arch {}):\n" +
                "{}\n\nOpcode 0x{:04x} at address 0x{:03x} is not emulated for the selected architecture."
            ).format(
                APP_INTRO, self.arch, self.debugger.debug(self, "???", verbose=True), self.opcode, self.debug_pc
            )
        ) from None

    def debug(self, instruction):
        self.debugger.output(self, instruction)

    def _0nnn(self):
        opcode = self.opcode

        if opcode < 0x10:
            # Let's use opcodes 0x0 - 0xF internally for indexing, since they're not used on any CHIP-8 variant
            self._opcode_unsupported()

        self._call_masked_instruction(opcode)

    def _5nnn_8nnn_9nnn(self):
        self._call_masked_instruction(self.opcode & 0xF00F)

    def _Ennn_Fnnn(self):
        self._call_masked_instruction(self.opcode & 0xF0FF)

    def _00E0(self):  # CLS
        if self.live_debug:
            self.debug("CLS")

        self.framebuffer.clear()

    def _00EE(self):  # RET
        if self.live_debug:
            self.debug("RET")

        self.pc = self.stack.pop()

    def _1nnn(self):  # JP addr
        if self.live_debug:
            self.debug("JP 0x{:03x}".format(self.addr))

        self.pc = self.addr

    def _2nnn(self):  # CALL addr
        if self.live_debug:
            self.debug("CALL 0x{:03x}".format(self.addr))

        self.stack.push(self.pc)
        self.pc = self.addr

    def _post_skip(self):
        if self.arch >= ARCH_XO_CHIP and self.fetch() == 0xF000:
            self.inc_pc()

        self.inc_pc()

    def _3xkk(self):  # SE Vx, byte
        if self.live_debug:
            self.debug("SE V{:01x}, 0x{:02x}".format(self.vx, self.byte))

        if self.v[self.vx] == self.byte:
            self._post_skip()

    def _4xkk(self):  # SNE Vx, byte
        if self.live_debug:
            self.debug("SNE V{:01x}, 0x{:02x}".format(self.vx, self.byte))

        if self.v[self.vx] != self.byte:
            self._post_skip()

    def _5xy0(self):  # SE Vx, Vy
        if self.live_debug:
            self.debug("SE V{:01x}, V{:01x}".format(self.vx, self.vy))

        if self.v[self.vx] == self.v[self.vy]:
            self._post_skip()

    def _6xkk(self):  # LD Vx, byte
        if self.live_debug:
            self.debug("LD V{:01x}, 0x{:02x}".format(self.vx, self.byte))

        self.v[self.vx] = self.byte

    def _7xkk(self):  # ADD Vx, byte
        vx = self.vx
        byte = self.byte

        if self.live_debug:
            self.debug("ADD V{:01x}, 0x{:02x}".format(vx, byte))

        byte += self.v[vx]
        self.v[vx] = byte & 0xFF

    def _post_8xy0_8xy1_8xy2_8xy3(self):
        if self.logic_quirks:
            self.v[0xF] = 0

    # All 8 instructions set Vf on original CHIP-8
    def _8xy0(self):  # LD Vx, Vy
        if self.live_debug:
            self.debug("LD V{:01x}, V{:01x}".format(self.vx, self.vy))

        self.v[self.vx] = self.v[self.vy]
        self._post_8xy0_8xy1_8xy2_8xy3()

    def _8xy1(self):  # OR Vx, Vy
        if self.live_debug:
            self.debug("OR V{:01x}, V{:01x}".format(self.vx, self.vy))

        self.v[self.vx] |= self.v[self.vy]
        self._post_8xy0_8xy1_8xy2_8xy3()

    def _8xy2(self):  # AND Vx, Vy
        if self.live_debug:
            self.debug("AND V{:01x}, V{:01x}".format(self.vx, self.vy))

        self.v[self.vx] &= self.v[self.vy]
        self._post_8xy0_8xy1_8xy2_8xy3()

    def _8xy3(self):  # XOR Vx, Vy
        if self.live_debug:
            self.debug("XOR V{:01x}, V{:01x}".format(self.vx, self.vy))

        self.v[self.vx] ^= self.v[self.vy]
        self._post_8xy0_8xy1_8xy2_8xy3()

    def _8xy4(self):  # ADD Vx, Vy
        vx = self.vx
        vy = self.vy

        if self.live_debug:
            self.debug("ADD V{:01x}, V{:01x}".format(vx, vy))

        val = self.v[vx] + self.v[vy]
        self.v[vx] = val & 0xFF
        self.v[0xF] = int(val > 0xFF)  # Vf is set when carrying

    def _post_8xy5_8xy7(self, val):  # Post-SUB/SUBN
        self.v[self.vx] = val & 0xFF
        # Vf is set when NOT borrowing, and this should happen AFTER Vx is set, as sometimes VF is specified in the
        # parameters.  Some XO-CHIP games fail unless this is done properly.
        self.v[0xF] = int(val >= 0)

    def _8xy5(self):  # SUB Vx, Vy
        if self.live_debug:
            self.debug("SUB V{:01x}, V{:01x}".format(self.vx, self.vy))

        self._post_8xy5_8xy7(self.v[self.vx] - self.v[self.vy])

    def _debug_8xy6_8xyE(self, direction):
        self.debug(
            "{} V{:01x}".format(direction, self.vx) if self.shift_quirks else
            "{} V{:01x}, V{:01x}".format(direction, self.vx, self.vy)
        )

    def _8xy6(self):  # SHR Vx {, Vy}
        # On Super-CHIP, Vx is used.  On CHIP-8 and XO-CHIP, Vy is used.
        if self.live_debug:
            self._debug_8xy6_8xyE("SHR")

        val = self.v[self.vx if self.shift_quirks else self.vy]
        self.v[self.vx] = val >> 1  # Apparently the result is put in Vx either way
        self.v[0xF] = val & 1  # The whole byte gets set just for the flag

    def _8xy7(self):  # SUBN Vx, Vy
        if self.live_debug:
            self.debug("SUBN V{:01x}, V{:01x}".format(self.vx, self.vy))

        self._post_8xy5_8xy7(self.v[self.vy] - self.v[self.vx])

    def _8xyE(self):  # SHL Vx {, Vy}
        # On Super-CHIP, Vx is used.  On CHIP-8 and XO-CHIP, Vy is used.
        if self.live_debug:
            self._debug_8xy6_8xyE("SHL")

        val = self.v[self.vx if self.shift_quirks else self.vy]
        self.v[self.vx] = (val << 1) & 0xFF
        self.v[0xF] = val >> 7

    def _9xy0(self):  # SNE Vx, Vy
        if self.live_debug:
            self.debug("SNE V{:01x}, V{:01x}".format(self.vx, self.vy))

        if self.v[self.vx] != self.v[self.vy]:
            self._post_skip()

    def _Annn(self):  # LD I, addr
        if self.live_debug:
            self.debug("LD I, 0x{:03x}".format(self.addr))

        self.i = self.addr

    def _Bnnn(self):  # JP V0, addr
        # This is a nasty quirk which breaks lots of games if set incorrectly. It varies depending on the CPU
        # architecture and occasionally, the ROM.
        vr = self.vx if self.jump_quirks else 0

        if self.live_debug:
            self.debug("JP V{:01x}, 0x{:03x}".format(vr, self.addr))

        self.pc = (self.v[vr] + self.addr) & 0xFFF

    def _Cxkk(self):  # RND Vx, byte
        if self.live_debug:
            self.debug("RND V{:01x}, 0x{:02x}".format(self.vx, self.byte))

        # The ANDing here is intentional.  This is not a random number between 0 and 'byte' inclusive.
        self.v[self.vx] = randint(0, 0xFF) & self.byte

    def _Dxyn(self):  # DRW Vx, Vy, nibble
        # Main sprite drawing routine.  If nibble == 0 and Super-CHIP arch, then draw 16x16 sprite

        height = self.nibble

        if self.live_debug:
            self.debug("DRW V{:01x}, V{:01x}, 0x{:01x}".format(self.vx, self.vy, height))

        if height == 0 and self.arch >= ARCH_SUPERCHIP_1_0:
            # Super-CHIP sprite.  Show 8x16 if low res, otherwise 16x16
            height = 16
            width = 8 if self.lo_res else 16
        else:
            # Standard non-Super-CHIP sprite
            width = 8

        # The sprite's start always wraps regardless of architecture.
        # Bottom-right corners are trimmed in CHIP-8 or Super-CHIP.
        vid_width, vid_height = self.framebuffer.get_vid_size()
        vx_pos = self.v[self.vx] % vid_width
        vy_pos = self.v[self.vy] % vid_height
        big_sprite = width > 8
        rows_collided = 0
        i = self.i

        for affected_plane in self.framebuffer.get_affected_planes():
            for y in range(height):
                spr_data = (
                    (self.ram.read(i + y * 2) << 8) | self.ram.read(i + y * 2 + 1)
                ) if big_sprite else self.ram.read(i + y)
                scr_y = y + vy_pos
                row_collided = False

                for x in range(width):
                    pixel = (spr_data & (0x8000 >> x)) if big_sprite else (spr_data & (0x80 >> x))

                    if pixel:
                        scr_x = x + vx_pos
                        collision = self.framebuffer.xor_pixel(scr_x, scr_y, affected_plane)

                        if collision:
                            # Don't stop drawing.  Set the flag, and never unset it for this row.
                            row_collided = True

                        # According to some sources, if not wrapping the screen, we are supposed to report collisions
                        # outside the area.  However, I have found enabling this breaks BLITZ if enabled in CHIP-8 mode,
                        # and I have found no games it fixes, so, no quirk flag for now.
                        #
                        # elif collision is None:
                        #     row_collided = True

                if row_collided:
                    rows_collided += 1

            i += (height * 2) if big_sprite else height

        # Super-CHIP 1.1 and above reports number of rows collided
        self.v[0xF] = int(rows_collided > 0) if self.arch < ARCH_SUPERCHIP_1_1 else rows_collided

        # Wait for vertical blanking interrupt.  Normally only used if emulating original CHIP-8 system
        if self.sprite_delay_quirks:
            self.vblank_wait = True

    def _Ex9E(self):  # SKP Vx
        if self.live_debug:
            self.debug("SKP V{:01x}".format(self.vx))

        if self.inputs.is_key_down(self.v[self.vx]):
            self._post_skip()

    def _ExA1(self):  # SKNP Vx
        if self.live_debug:
            self.debug("SKNP V{:01x}".format(self.vx))

        if not self.inputs.is_key_down(self.v[self.vx]):
            self._post_skip()

    def _Fx07(self):  # LD Vx, DT
        if self.live_debug:
            self.debug("LD V{:01x}, DT".format(self.vx))

        self.v[self.vx] = self.dt

    def _Fx0A(self):  # LD Vx, K
        if self.live_debug:
            self.debug("LD V{:01x}, K".format(self.vx))

        # This opcode waits for a keypress, but since the sound and delay timers still need to expire correctly, and
        # framebuffer still needs updating, we'll return control to the CPU and simply decrement the incremented program
        # counter.

        if self.awaiting_keypress:
            key = self.inputs.get_keypress()
        else:
            self.inputs.setup_keypress()  # Clear any currently/previously pressed/held keys.
            self.awaiting_keypress = True
            key = None

        if key is None:
            # We need to come back here on the next instruction, because no key is pressed.
            self.dec_pc()
        else:
            self.v[self.vx] = key
            self.awaiting_keypress = False

    def _Fx15(self):  # LD DT, Vx
        if self.live_debug:
            self.debug("LD DT, V{:01x}".format(self.vx))

        dt = self.v[self.vx]
        self.dt = dt
        self.dt_target = self.this_time + (dt / TIMER_FREQ)

    def _Fx18(self):  # LD ST, Vx
        if self.live_debug:
            self.debug("LD ST, V{:01x}".format(self.vx))

        ds = self.v[self.vx]
        # Allow the program to start the buzzer, or immediately stop it before the sound timer hits zero
        self.audio.enable_buzzer(ds > 0)
        self.ds = ds
        self.ds_target = self.this_time + (ds / TIMER_FREQ)

    def _Fx1E(self):  # ADD I, Vx
        if self.live_debug:
            self.debug("ADD I, V{:01x}".format(self.vx))

        val = self.i + self.v[self.vx]
        self.i = val & self.i_bitmask

        # Allow for Amiga CHIP-8 emulator behaviour
        if self.index_overflow_quirks:
            self.v[0xF] = (val > self.i_bitmask)

    def _Fx29(self):  # LD F, Vx
        if self.live_debug:
            self.debug("LD F, V{:01x}".format(self.vx))

        self.i = (self.sysfont_sm_loc + 5 * self.v[self.vx]) & self.i_bitmask

    def _Fx33(self):  # LD B, Vx
        if self.live_debug:
            self.debug("LD B, V{:01x}".format(self.vx))

        val = self.v[self.vx]
        i = self.i
        self.ram.write(i, val // 100)                               # Most-significant digit
        self.ram.write((i + 1) & self.i_bitmask, (val // 10) % 10)  # Middle digit
        self.ram.write((i + 2) & self.i_bitmask, val % 10)          # Least-signifiant digit

    def _post_Fx55_Fx65(self):
        if self.load_quirks:
            self.i += self.vx

            if not self.index_increment_quirks:
                self.i += 1

            self.i &= self.i_bitmask

    def _Fx55(self):  # LD [I], Vx
        if self.live_debug:
            self.debug("LD [I], V{:01x}".format(self.vx))

        i = self.i
        i_bitmask = self.i_bitmask

        for reg in range(self.vx + 1):
            self.ram.write((i + reg) & i_bitmask, self.v[reg])

        self._post_Fx55_Fx65()

    def _Fx65(self):  # LD Vx, [I]
        if self.live_debug:
            self.debug("LD V{:01x}, [I]".format(self.vx))

        i = self.i
        i_bitmask = self.i_bitmask

        for reg in range(self.vx + 1):
            self.v[reg] = self.ram.read((i + reg) & i_bitmask)

        self._post_Fx55_Fx65()

    # Instructions for Super-CHIP 1.0 (and above)

    def _00FD(self):  # EXIT
        if self.live_debug:
            self.debug("EXIT")

        self.dec_pc()

    def _00FE(self):  # LOW
        if self.live_debug:
            self.debug("LOW")

        if not self.lo_res:
            self.framebuffer.resize_vid(64, 32)
            self.lo_res = True

    def _00FF(self):  # HIGH
        if self.live_debug:
            self.debug("HIGH")

        if self.lo_res:
            self.framebuffer.resize_vid(128, 64)
            self.lo_res = False

    def _Fx75(self):  # LD R, Vx
        if self.live_debug:
            self.debug("LD R, V{:01x}".format(self.vx))

        vx = self.vx

        if self.arch < ARCH_XO_CHIP and vx > 7:
            # Fx75 with x set over 7 is only supported on XO-CHIP
            self._opcode_unsupported()

        # NOTE: RPL registers should ideally be saved on emulator quit.
        # Ensure with +1s that the final register is copied.
        self.rpl[:vx + 1] = self.v[:vx + 1]

    def _Fx85(self):  # LD Vx, R
        if self.live_debug:
            self.debug("LD V{:01x}, R".format(self.vx))

        vx = self.vx

        if self.arch < ARCH_XO_CHIP and vx > 7:
            # Fx85 with x set over 7 is only supported on XO-CHIP
            self._opcode_unsupported()

        # NOTE: RPL registers should ideally be restored on emulator boot.
        # Ensure with +1s that the final register is copied.
        self.v[:vx + 1] = self.rpl[:vx + 1]

    # Instructions for Super-CHIP 1.1 (and above)

    def _00FB(self):  # SCR
        if self.live_debug:
            self.debug("SCR")

        self.framebuffer.scroll_right(2 if self.lo_res else 4)

    def _00FC(self):  # SCL
        if self.live_debug:
            self.debug("SCL")

        self.framebuffer.scroll_left(2 if self.lo_res else 4)

    def _Fx30(self):  # LD HF, Vx
        if self.live_debug:
            self.debug("LD HF, V{:01x}".format(self.vx))

        self.i = (self.sysfont_bg_loc + 10 * self.v[self.vx]) & self.i_bitmask

    def _00Cn(self):  # SCD n
        scroll_distance = self.nibble

        if self.live_debug:
            self.debug("SCD {:01x}".format(scroll_distance))

        if self.lo_res:
            if scroll_distance & 1:
                raise CPUError("Scrolling down vertically by a half-pixel in low resolution mode is unsupported.")

            scroll_distance //= 2

        self.framebuffer.scroll_down(scroll_distance)

    # Instructions for XO-CHIP

    def _00Dn(self):  # SCU n
        scroll_distance = self.nibble

        if self.live_debug:
            self.debug("SCU {:01x}".format(scroll_distance))

        if self.lo_res:
            if scroll_distance & 1:
                raise CPUError("Scrolling up vertically by a half-pixel in low resolution mode is unsupported.")

            scroll_distance //= 2

        self.framebuffer.scroll_up(scroll_distance)

    def _5xy2(self):  # XST Vx, Vy
        vx = self.vx
        vy = self.vy

        if self.live_debug:
            self.debug("XST V{:01x}, V{:01x}".format(vx, vy))

        i = self.i
        i_bitmask = self.i_bitmask
        iter_back = vx > vy

        for offset in range(vx - vy + 1) if iter_back else range(vy - vx + 1):
            self.ram.write((i + offset) & i_bitmask, self.v[(vx - offset) if iter_back else (vx + offset)])

    def _5xy3(self):  # XLD Vx, Vy
        vx = self.vx
        vy = self.vy

        if self.live_debug:
            self.debug("XLD V{:01x}, V{:01x}".format(vx, vy))

        i = self.i
        i_bitmask = self.i_bitmask
        iter_back = vx > vy

        for offset in range(vx - vy + 1) if iter_back else range(vy - vx + 1):
            self.v[(vx - offset) if iter_back else (vx + offset)] = self.ram.read((i + offset) & i_bitmask)

    def _Fx00(self):  # XLDL I, addr
        # Only F000 is supported
        if self.vx != 0:
            self._opcode_unsupported()

        i = self.fetch()

        if self.live_debug:
            self.debug("XLDL I, 0x{:04x}".format(i))

        self.i = i
        self.inc_pc()  # Increment PC again as this is a double-length instruction

    def _Fn01(self):  # XPLA Vx
        if self.live_debug:
            self.debug("XPLA 0x{:01x}".format(self.vx))

        self.framebuffer.switch_planes(self.vx)

    def _Fx02(self):  # XSTA
        # Only 0xF002 is supported by the CPU, but since there is no 0xF102, 0xF202, .., 0xFF02, we can catch the
        # entirety of Fx02 with the same bitmask as other 0xFs, and then just check the second nibble (Vx) is 0
        if self.vx != 0:
            self._opcode_unsupported()

        if self.live_debug:
            self.debug("XSTA")

        if self.audio_null:
            # Return without doing anything if we don't have a proper audio driver
            return

        # There is a very unlikely chance this buffer copy may hit the end of RAM.  If it does, the audio buffer will
        # simply only be partially used.  This situation is not worth catching.
        self.audio.set_buffer(self.ram.read_block(self.i, 16))

    def _Fx3A(self):  # XPR Vx
        if self.live_debug:
            self.debug("XPR V{:01x}".format(self.vx))

        if self.audio_null:
            # Return without doing anything if we don't have a proper audio driver
            return

        # This is the standard XO-CHIP translation formula to convert the Vx register to playback frequency in Hz
        self.audio.set_frequency(4000 * (2 ** ((self.v[self.vx] - 64) / 48.0)))
