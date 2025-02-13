#!/usr/bin/env python3

__author__ = "Gregory Maynard-Hoare"
__copyright__ = "Copyright (C) 2024 Gregory Maynard-Hoare"
__license__ = "GNU Affero General Public License v3.0"
__version__ = "1.4.4"

# App identification
APP_NAME = "SuperChocChip Emulator"
APP_VERSION = __version__
APP_COPYRIGHT = "".join((__copyright__, ", licensed under ", __license__))
APP_INTRO = "{} V{} -- ".format(APP_NAME, APP_VERSION)

# Emulated system architectures
ARCH_CHIP8 = 0
ARCH_CHIP8_HIRES = 5
ARCH_SUPERCHIP_1_0 = 10
ARCH_CHIP48 = 15  # Chip-48 came before Super-CHIP 1.0, but it's mostly the same, just with quirks
ARCH_SUPERCHIP_1_1 = 20
ARCH_XO_CHIP = 30
ARCH_XO_CHIP_16 = 35

# Default mappings for keys 0-F, later populated into a dictionary.  Note that the keyscans (on a UK QWERTY keyboard)
# and ASCII characters for these are the same code
DEFAULT_KEYMAP = "120,49,50,51,113,119,101,97,115,100,122,99,52,114,102,118"

# Startup
SUPPORTED_CPUS = {
    "chip8":        ARCH_CHIP8,          # Base CPU architecture
    "chip8hires":   ARCH_CHIP8_HIRES,    # Double-height resolution mode
    "schip1.0":     ARCH_SUPERCHIP_1_0,  # Extra instructions, additional storage registers, high res mode, etc
    "chip48":       ARCH_CHIP48,         # Super-CHIP 1.0 with different default quirk flags
    "schip1.1":     ARCH_SUPERCHIP_1_1,  # Hardware scrolling, large system font
    "xochip":       ARCH_XO_CHIP,        # Colour screen, 64K extended memory, etc
    "xochip16":     ARCH_XO_CHIP_16      # XO-CHIP with 16-colour (4-plane) support
}

# CPU quirks (not including display wrapping)
CPU_QUIRKS = ["load", "shift", "logic", "index_overflow", "index_increment", "jump", "sprite_delay"]
