#!/usr/bin/env python3
"""Prove kem ecrire write calls flock LOCK_EX then LOCK_UN. Existence of .lock is not enough."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import kem  # noqa: E402


class FlockEcrire(unittest.TestCase):
    def test_ecrire_calls_flock_ex(self):
        mock = MagicMock()
        mock.LOCK_EX = 2
        mock.LOCK_UN = 8
        orig = kem.fcntl
        kem.fcntl = mock
        try:
            with tempfile.TemporaryDirectory() as tmp:
                dest = Path(tmp) / "carte.kem.json"
                rc = kem.main(
                    ["ecrire", "--opt-in", "--suite", "mlkem768", "--vers", str(dest)]
                )
                self.assertEqual(rc, 0)
                carte = json.loads(dest.read_text(encoding="utf-8"))
                self.assertEqual(carte["format"], "kem.v0")
                self.assertEqual(carte["suite"], "mlkem768")
                self.assertTrue((dest.with_suffix(dest.suffix + ".lock")).is_file())
            calls = [c.args[1] for c in mock.flock.call_args_list]
            self.assertGreaterEqual(len(calls), 2)
            self.assertEqual(calls[0], mock.LOCK_EX)
            self.assertEqual(calls[-1], mock.LOCK_UN)
        finally:
            kem.fcntl = orig


if __name__ == "__main__":
    unittest.main()
