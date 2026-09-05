#!/usr/bin/env python3
"""Trail path is the .unforge-trail.json suffix, not substring 'trail'."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from trail import choisir_trail  # noqa: E402


class Choisir(unittest.TestCase):
    def test_suffixe_avant_substring(self):
        portrait = Path("portrait-trail.pdf")
        itinerary = Path("portrait.unforge-trail.json")
        picked = choisir_trail([portrait, itinerary])
        self.assertEqual(picked, itinerary)
        picked = choisir_trail([itinerary, portrait])
        self.assertEqual(picked, itinerary)

    def test_sans_suffixe_premier_chemin(self):
        a = Path("a.json")
        b = Path("b.json")
        self.assertEqual(choisir_trail([a, b]), a)


if __name__ == "__main__":
    unittest.main()
