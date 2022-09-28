#!/usr/bin/env python3

"""
Null Renderer Plugin

This serves as a base class for other rendering plugins.

This module can be used on its own as a Renderer plugin if you only want to see
debug output.  Without a renderer, performance data will also not be shown.
"""

__copyright__ = "Copyright (C) 2022 Gregory Maynard-Hoare"
__license__ = "GNU Affero General Public License v3.0"


class RendererError(Exception):
    pass


class Renderer:
    def __init__(self, scale=None, use_colour=True, **kwargs):  # pylint: disable=unused-argument
        self.scale = 1 if scale is None else scale
        self.use_colour = use_colour
        self.set_resolution(0, 0)

    def set_resolution(self, width, height):
        self.width = width
        self.height = height

    def set_pixel(self, x, y, colour):  # pylint: disable=unused-argument
        pass

    def refresh_display(self, content_changed=False):
        pass

    def set_title(self, title):
        pass

    def shutdown(self):
        pass
