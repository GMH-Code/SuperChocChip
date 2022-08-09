SuperChocChip Emulator
======================

This emulator can run ROMs (machine code binaries, usually games) for all the following systems:
- CHIP-8
- CHIP-48
- Super-CHIP 1.0
- Super-CHIP 1.1
- XO-CHIP
- XO-CHIP -- Extended colours

It is written from the ground up in Pure Python, runs on Linux (out of the box), or on Windows, and emulates a proper computer with CPU, keypad, display, etc., and can run, and play, native ROMs freely available on the Internet at 100% speed, even on older hosts.

Running a ROM
-------------

One command will start the emulator with the default (and most compatible) settings, providing you have any modern version of Python 3 installed:

    python3 superchocchip.py <filename>

Replace 'python3' with 'python' or 'py' if that does not work.

You can play games in either PyGame (a fast SDL Desktop Window) or Curses (the Terminal).

PyGame will be used to draw graphics and take inputs, if it is available.  This is highly recommended as it is far more responsive for keypresses, draws faster, and looks better.  The Terminal has to use up a lot of space to draw graphics, and key presses / releases are simulated from character inputs.  This does, however, mean you can play emulated games over SSH.

For some older games, you might find you need to play with the command line settings, especially the quirks, to find out what works.  Many games have been written over the years for various emulators with different behaviours, some which did not follow original specifications quite correctly.  I've tried to cover as many of these quirks as possible.


Keypad
------

All the 'CHIP' systems use a hexadecimal keypad for input.  The keys, (by default on a UK/US keyboard), are mapped as follows:

    QWERTY        CHIP
    -------       -------
    1 2 3 4  -->  7 8 9 C
    Q W E R  -->  4 5 6 D
    A S D F  -->  1 2 3 E
    Z X C V  -->  A 0 B F

Command-line Parameters
-----------------------

    Usage:
        superchocchip.py [-h] [-a {chip8,schip1.0,chip48,schip1.1,xochip,xochip16}] [-c CLOCK_SPEED] [-r {pygame,curses,null}] [-s SCALE] [-f SMOOTHING] [-m {0,1,2}] [-k KEYMAP] [--pygame_palette PYGAME_PALETTE] [--curses_palette CURSES_PALETTE] [--load_quirks {0,1}] [--shift_quirks {0,1}] [--logic_quirks {0,1}] [--index_overflow_quirks {0,1}] [--index_increment_quirks {0,1}] [--jump_quirks {0,1}] [--screen_wrap_quirks {0,1}] [-d]
        filename

    Positional arguments:
        filename              ROM to execute (normally ending in .ch8 or .c8)

    Optional arguments:
        -h, --help            show this help message and exit
        -a {chip8,schip1.0,chip48,schip1.1,xochip,xochip16}, --arch {chip8,schip1.0,chip48,schip1.1,xochip,xochip16}
                              set CPU instructions, speed, and quirks automatically for CHIP-8, CHIP-48, Super-CHIP 1.0/1.1, XO-CHIP, or XO-CHIP 16-colour mode
        -c CLOCK_SPEED, --clock_speed CLOCK_SPEED
                              override the CPU speed in operations/second, regardless of architecture (0=force uncapped)
        -r {pygame,curses,null}, --renderer {pygame,curses,null}
                              set the rendering and input systems (pygame by default if available, otherwise curses)
        -s SCALE, --scale SCALE
                              set the window width in PyGame mode (default 512), and scale in Curses mode (default 2)
        -f SMOOTHING, --smoothing SMOOTHING
                              define the number of smoothing filter passes for higher quality rendering (default 0)
        -m {0,1,2}, --curses_cursor_mode {0,1,2}
                              control cursor visibility in the Curses renderer
        -k KEYMAP, --keymap KEYMAP
                              redefine the 16 keyscan codes (PyGame) or character numbers (Curses). Separate each decimal with a comma
        --pygame_palette PYGAME_PALETTE
                              redefine up to 16 colours for the PyGame renderer in comma-separated hex, e.g. 1234ABCD,F987654E,.. etc.
        --curses_palette CURSES_PALETTE
                              redefine up to 16 colours for the Curses renderer using an octal sequence, e.g. 1234567013572460
        --load_quirks {0,1}   manually disable or enable CPU load quirks.
        --shift_quirks {0,1}  manually disable or enable CPU shift quirks.
        --logic_quirks {0,1}  manually disable or enable CPU logic quirks.
        --index_overflow_quirks {0,1}
                              manually disable or enable CPU index overflow quirks.
        --index_increment_quirks {0,1}
                              manually disable or enable CPU index increment quirks.
        --jump_quirks {0,1}   manually disable or enable CPU jump quirks.
        --screen_wrap_quirks {0,1}
                              manually disable or enable screen wrap quirks.
        -d, --debug           enable live debug output. Only visible in PyGame renderer during play. Slows CPU execution

Emulated Hardware
-----------------

The CPU includes variants of:
- CHIP-8, CHIP-48, Super-CHIP 1.0, Super-CHIP 1.1 and XO-CHIP instruction sets

Depending on the hardware/modes chosen in the emulator, included is:
- 4KB / 64KB system RAM with byte/block access and fast moves
- 64x32 / 128x64 monochromatic, 4-colour / 16-colour displays
- 4KB video RAM with legacy modes (1KB, 256-byte etc.)
- 12-level / 16-level 12-bit CPU call stacks
- 16x 8-bit aligned system registers
- 16x user flag registers
- 1x 16-bit index register (address storage)
- 1x 12-bit program counter
- 1x main system clock
- 2x independent delay/sound hardware timers
- 1x video timer
- 1x video framebuffer, supporting multiple planes / VRAM banks
- 2x video blitters, supported via plugin
- 2x input devices, supported via plugin
- Two custom-built high and low-res bitmap character sets, loaded from ROM on boot

Supported Features
------------------

- Large, small, and colour sprites.  ROMs which make use of 4 planes (16-colours) are also supported, even though the specification on this is still unofficial.
- Fast 4-way scrolling.
- The extra video timer is set to 60Hz, which ensures unnecessary rendering and flickering doesn't occur.  Modern games which use the delay timer to provide VSync emulation are supported.
- Performance monitoring output (frames drawn and instructions executed per second).
- Live visual disassembly of OpCodes/instructions about to be run (disabled by default, unless a CPU exception occurs).
- The input and rendering modules can be swapped for your own creations.  In theory, you can make a game run on almost any custom display and keypad.
- Custom-built CHIP-8 and Super-CHIP system fonts, with all characters drawable.
- Redefinable palettes, in both PyGame and Curses renderers.  In the Curses renderer, you can choose which of the 8 colours are allocated to each of the 16 colours in the emulator.
- Scale2x (high quality) smoothing in the PyGame renderer, off by default.

Notes
-----

### Project Purpose

- This project is intended as a sample for potential employers to demonstrate hardware and software understanding, and a level of computer science.  If there is enough interest in the emulator itself, I may give support and updates for it.
- Please consult my website for examples of lots of successful projects written in a variety of languages.

### Screen Modes and Sub-Pixel Scrolling

- Due to the framebuffer implementation, and a huge performance increase, this emulator will not allow the unusual situation of half-pixel scrolls in low-resolution mode.  The display will also be cleared when the screen mode is changed.  No ROMs have been found which rely on the display staying intact during a mode change, and taking the rendering shortcuts result in one quarter of pixel blits in lower (standard) resolution modes.

### Code Optimisation

- Loops or condition blocks are avoided whereever possible to optimise emulation speed.  For example, this CPU uses bitmasks and hashed dictionaries to find the right opcodes, rather than huge conditions and switch (C/C++) statements.
- There are a few portions of the CPU code that are a bit repetitive, for example the checks to see if the debugger is active on each instruction.  This is preferred to the shorter, but slower method (calling unified debug functionality and then checking to see if the debugger is active before returning).

### Quirks

- All known quirks and system behaviours are accounted for, except for one case I can never find in use: Vf flag ordering.  This controls the alternative (and potentially dangerous) point to set the carry/borrow/overflow flag in the Arithmetic Logic Unit emulation.  I couldn't find any ROMs at all which rely on this behaviour, but I've found a few ROMs it breaks, usually corrupting moving graphics because this flag is also used for XOR screen writes.  In some cases games even end up calling invalid OpCodes.  As far as I know, the ALU implementation in all other devices/emulators sets Vf the end of the operations by default, and, it is rather important to update the carry flag afterwards, so Vf can be used before it is clobbered.  A ROM developer could opt to use Vf from another calculation as an input, or set a temporary input if the other (V0-Ve) registers are full, so allowing Vf to be used makes sense.  It'd also be rather odd (and confusing to understand) if a ROM didn't set Vf, but used the single-bit flag result as an input for the operation itself.  The developer would then have to document the usage of the quirk, and possibly deal with the effect of this situation elsewhere in the code rather than simply avoiding it in the first place.

Running Tests
-------------

Run the following command in the project directory:

    python3 -m unittest

Future Expansion
----------------

- The CPU testing is okay, but it'd be nice to have full testing for all quirk combinations.
- Ideally, we should have 100% testing coverage across the board.
- The test ROMs could be automatically validated as part of the tests, which would be nice.  This will require halting the CPU after a specified number of cycles and then verifying a SHA checksum of the Framebuffer VRAM banks against an expected value.
- Snapshots (save states) and saving/restoring of RPL registers to/from disk.  I'm not so bothered about this at the moment, but some games, such as RPGs, are becoming longer to play, so saving your progress would be good to have.
- Per-game saved configuration of palette(s) and quirks, at least.
- Audio output, despite the fact I'll probably end up muting it anyway.

Extending
---------

- This program has three Input and Rendering plugins.  It is possible, and quite easy, to write your own Inputs or Renderers if you want, (for example) to write to a small LED display instead of the Desktop or Terminal and control that using your own custom keypad.  This could probably be done with MicroPython, since the core of this program does not rely on any special Python libraries.

License
-------

See the 'LICENSE' file for full details. The 'Affero' version of the GPL v3.0 has been chosen as this emulator can potentially be run over SSH or another kind of remote Terminal.

---

Copyright (C) 2022 Gregory Maynard-Hoare, licensed under GNU Affero General Public License v3.0
