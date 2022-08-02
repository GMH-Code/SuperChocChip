#!/usr/bin/env python3

__copyright__ = "Copyright (C) 2022 Gregory Maynard-Hoare"
__license__ = "GNU Affero General Public License v3.0"

# App identification
APP_NAME = "SuperChocChip Emulator"
APP_VERSION = "1.0.3"
APP_COPYRIGHT = "Copyright (C) 2022 Gregory Maynard-Hoare, licensed under GNU Affero General Public License v3.0"
APP_INTRO = "{} V{} -- ".format(APP_NAME, APP_VERSION)

# Emulated system architectures
ARCH_CHIP8 = 0
ARCH_SUPERCHIP_1_0 = 10
ARCH_CHIP48 = 15  # Chip-48 came before Super-CHIP 1.0, but it's mostly the same, just with quirks
ARCH_SUPERCHIP_1_1 = 20
ARCH_XO_CHIP = 30

# Default mappings for keys 0-F, later populated into a dictionary.  Note that the keyscans (on a UK QWERTY keyboard)
# and ASCII characters for these are the same code
DEFAULT_KEYMAP = "120,49,50,51,113,119,101,97,115,100,122,99,52,114,102,118"

# Startup
SUPPORTED_CPUS = {
    "chip8":        ARCH_CHIP8,          # Base CPU architecture
    "schip1.0":     ARCH_SUPERCHIP_1_0,  # Extra instructions, additional storage registers, high res mode, etc
    "chip48":       ARCH_CHIP48,         # Super-CHIP 1.0 with different default quirk flags
    "schip1.1":     ARCH_SUPERCHIP_1_1,  # Hardware scrolling, large system font
    "xochip":       ARCH_XO_CHIP         # Colour screen, 64K extended memory, etc
}

# CPU quirks (not including display wrapping)
CPU_QUIRKS = ["load", "shift", "logic", "index_overflow", "index_increment", "jump"]
