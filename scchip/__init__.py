#!/usr/bin/env python3

"""
Main Startup Module

Simply call main(args) to start the emulator, replacing args with a dictionary
of options.  This can be done via the Terminal or GUI.

All options must be supplied.  Defaults can be specified with a 'None'.
"""

__copyright__ = "Copyright (C) 2022 Gregory Maynard-Hoare"
__license__ = "GNU Affero General Public License v3.0"

from .constants import (
    APP_INTRO, APP_COPYRIGHT, ARCH_CHIP8, ARCH_SUPERCHIP_1_0, ARCH_XO_CHIP, ARCH_XO_CHIP_16, SUPPORTED_CPUS, CPU_QUIRKS
)
from .cpu import CPU
from .debugger import Debugger
from .framebuffer import Framebuffer
from .hostio import Loader
from .ram import RAM
from .stack import Stack


def main(args):
    print("".join((APP_INTRO, APP_COPYRIGHT)))
    quirk_settings = {}

    for cpu_quirk in CPU_QUIRKS:
        quirk_label = "{}_quirks".format(cpu_quirk)
        quirk_setting = args[quirk_label]
        quirk_settings[quirk_label] = None if quirk_setting is None else bool(quirk_setting)

    opt_renderer = args["renderer"]
    if opt_renderer is None:
        # No renderer selected.  Try PyGame first, and if that doesn't work, fall back to Curses.
        try:
            # pylint: disable=unused-import,import-outside-toplevel
            # flake8: noqa: F401
            import pygame
        except ImportError:  # Also catches ModuleNotFoundError
            opt_renderer = "curses"
        else:
            opt_renderer = "pygame"

    if opt_renderer == "pygame":
        from .inputs.i_pygame import Inputs
        from .renderers.r_pygame import Renderer
    elif opt_renderer == "curses":
        from .inputs.i_curses import Inputs
        from .renderers.r_curses import Renderer
    else:
        from .inputs.i_null import Inputs
        from .renderers.r_null import Renderer

    arch = SUPPORTED_CPUS[args["arch"]]
    loader = Loader()

    # Allocate default memory matching system architecture
    ram = RAM()
    ram.resize(0x1000 if arch < ARCH_XO_CHIP else 0x10000)

    # Write system fonts into RAM
    ram.write_block(0x50, loader.load_system_font("8"))

    if arch > ARCH_CHIP8:
        ram.write_block(0xA0, loader.load_system_font("16"))

    # Read ROM binary and write it into RAM
    ram.write_block(0x200, loader.load_binary(args["filename"]))

    # Set up a new rendering system based on the selected guest
    renderer = Renderer(scale=args["scale"], use_colour=(arch >= ARCH_XO_CHIP))

    # If the user is interested in seeing the cursor in Curses mode, show it
    if opt_renderer == "curses":
        renderer.set_curses_cursor(args["curses_cursor_mode"])

    # Initialise framebuffer and attach to rendering system
    screen_wrap_quirks = args["screen_wrap_quirks"]

    # Choose number of planes appropriate to system architecture
    if arch >= ARCH_XO_CHIP_16:
        num_planes = 4
    elif arch >= ARCH_XO_CHIP:
        num_planes = 2
    else:
        num_planes = 1

    framebuffer = Framebuffer(
        renderer,
        num_planes=num_planes,
        allow_wrapping=((arch >= ARCH_XO_CHIP) if screen_wrap_quirks is None else bool(screen_wrap_quirks))
    )

    # Set up host inputs, and link to the chosen rendering module in case it provides inputs too
    inputs = Inputs(args["keymap"], renderer)

    # Set up non-shared CPU stack in host memory -- 12 levels for CHIP-8 CPUs, 16 for Super-CHIP 1.0 and above
    stack = Stack(16 if arch >= ARCH_SUPERCHIP_1_0 else 12)

    # Set up debugger and live output if necessary
    debugger = Debugger()
    debugger.set_live(args["debug"])

    # Create a new CPU, plug it into the rest of the system, and boot it up at the default address
    cpu = CPU(arch, ram, stack, framebuffer, inputs, debugger, clock_speed=args["clock_speed"], **quirk_settings)
    cpu.run(0x200)
