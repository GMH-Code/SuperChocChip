#!/usr/bin/env python3

__author__ = "Gregory Maynard-Hoare"
__copyright__ = "Copyright (C) 2022 Gregory Maynard-Hoare"
__license__ = "GNU Affero General Public License v3.0"
__version__ = "1.1.3"

from argparse import ArgumentParser
from scchip import main
from scchip.constants import DEFAULT_KEYMAP, SUPPORTED_CPUS, CPU_QUIRKS


def parse_args():
    parser = ArgumentParser()
    parser.add_argument("filename", help="ROM to execute (normally ending in .ch8 or .c8)")
    parser.add_argument(
        "-a", "--arch", choices=list(SUPPORTED_CPUS.keys()), default="xochip16",
        help="set CPU instructions, speed, and quirks automatically for CHIP-8, CHIP-48, Super-CHIP 1.0/1.1,"
        + " XO-CHIP, or XO-CHIP 16-colour mode"
    )
    parser.add_argument(
        "-c", "--clock_speed", type=int,
        help="override the CPU speed in operations/second, regardless of architecture (0=force uncapped)"
    )
    parser.add_argument(
        "-r", "--renderer", choices=["pygame", "curses", "null"],
        help="set the rendering and input systems (pygame by default if available, otherwise curses)"
    )
    parser.add_argument(
        "-s", "--scale", type=int,
        help=("set the window width in PyGame mode (default 512), and scale in Curses mode (default 2)")
    )
    parser.add_argument(
        "-m", "--curses_cursor_mode", type=int, choices=[0, 1, 2], default=0,
        help="control cursor visibility in the Curses renderer"
    )
    parser.add_argument(
        "-k", "--keymap", default=DEFAULT_KEYMAP,
        help="redefine the 16 keyscan codes (PyGame) or character numbers (Curses).  Separate each decimal with a comma"
    )
    parser.add_argument(
        "--pygame_palette",
        help="redefine up to 16 colours for the PyGame renderer in comma-separated hex, e.g. 1234ABCD,F987654E,.. etc."
    )

    for cpu_quirk in CPU_QUIRKS:
        parser.add_argument(
            "--{}_quirks".format(cpu_quirk), type=int, choices=[0, 1],
            help="Manually disable or enable CPU {} quirks.".format(cpu_quirk.replace("_", " "))
        )

    parser.add_argument(
        "--screen_wrap_quirks", type=int, choices=[0, 1],
        help="Manually disable or enable screen wrap quirks."
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", default=False,
        help="Enables live debug output.  Only visible in PyGame renderer during play.  Slows CPU execution"
    )
    return parser.parse_args()  # Can call sys.exit(2) if args are incorrect


if __name__ == "__main__":
    args = vars(parse_args())
    # It is possible to start the emulator from a GUI by calling this with a dictionary
    main(args)
