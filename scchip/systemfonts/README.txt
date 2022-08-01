CHIP-8 / Super-CHIP Font Files for CHIP-8 Emulator
==================================================

These files contain bitmap fonts which are copied into RAM on emulator boot.
Usually they are embedded into the source code (as hex data), but I have opted
to keep them separate.  The SHA-256 of these files is verified in the tests.

They contain:

* 8x5-bit CHIP-8 system font, 16 characters (0x0-0xF), 80 bytes total.
* 8x10-bit Super-CHIP system font, 16 characters (0x0-0xF), 160 bytes total.

These are not the 'standard' CHIP-8 fonts, nor have they been copied from
another emulator.  They have been intentionally created from scratch and can be
viewed in either a hex or binary editor.  Please do not simply include either
(or both) of these files in your own project without respecting the license.

Note that I have included all characters from 0-F, not just 0-9 for CHIP-8 and
Super-CHIP.  There appears to be no problem with this as the contents of RAM
below 0x200 are usually reserved for interpreter functionality.

In terms of creating the fonts, the CHIP-8 character for zero is designed like
this.  We should only use the leftmost 4 bits, as that's what programs expect
when displaying multiple digits:

[ ##     ] -> 0b01100000 -> 0x60
[#  #    ] -> 0b10010000 -> 0x90
[#  #    ] -> 0b10010000 -> 0x90
[#  #    ] -> 0b10010000 -> 0x90
[ ##     ] -> 0b01100000 -> 0x60

Here is the Super-CHIP character for zero.  Note that unlike other computers,
these system fonts should not have borders on any side.  The font should also
be suitably thickened for a double-resolution square-pixel display:

[ ###### ] -> 0b01111110 -> 0x7E
[########] -> 0b11111111 -> 0xFF
[##    ##] -> 0b11000011 -> 0xC3
[##    ##] -> 0b11000011 -> 0xC3
[##    ##] -> 0b11000011 -> 0xC3
[##    ##] -> 0b11000011 -> 0xC3
[##    ##] -> 0b11000011 -> 0xC3
[##    ##] -> 0b11000011 -> 0xC3
[########] -> 0b11111111 -> 0xFF
[ ###### ] -> 0b01111110 -> 0x7E

The hex bytes above should match the start of the system font files.

Copyright (C) 2022 Gregory Maynard-Hoare,
licensed under GNU Affero General Public License v3.0
