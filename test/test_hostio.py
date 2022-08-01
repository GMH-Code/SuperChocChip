#!/usr/bin/env python3

__copyright__ = "Copyright (C) 2022 Gregory Maynard-Hoare"
__license__ = "GNU Affero General Public License v3.0"

import unittest
from hashlib import sha256
from scchip.hostio import Loader


class TestLoader(unittest.TestCase):
    def setUp(self):
        self.loader = Loader()

    def test_loader_load_file_present(self):
        # Test the loader works, and verify the system fonts are okay
        self.assertEqual(
            "3f8cbcb386d6ae22714031094184446bb9d9b639d7fbacc39eb2b47c6723d22d",
            sha256(self.loader.load_system_font("8")).hexdigest()
        )

        self.assertEqual(
            "f5389e19e1b3b14cc2f0c836effccaf03b9ef8e0b1348bcc432e39e06d72e3df",
            sha256(self.loader.load_system_font("16")).hexdigest()
        )

    def test_loader_load_file_missing(self):
        self.assertRaises(FileNotFoundError, self.loader.load_binary, "NoFile.ch8")
