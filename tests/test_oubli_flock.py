#!/usr/bin/env python3
"""Prove appliquer() calls flock LOCK_EX then LOCK_UN. Existence of .lock is not enough."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import oubli  # noqa: E402
from oubli import appliquer, brouillon  # noqa: E402


class FlockAppliquer(unittest.TestCase):
    def test_appliquer_calls_flock_ex(self):
        mock = MagicMock()
        mock.LOCK_EX = 2
        mock.LOCK_UN = 8
        orig = oubli.fcntl
        oubli.fcntl = mock
        try:
            with tempfile.TemporaryDirectory() as tmp:
                f = Path(tmp) / "fichier.txt"
                dest = Path(tmp) / "oubli.json"
                f.write_text("lock\n", encoding="utf-8")
                dest.write_text(json.dumps(brouillon(f), ensure_ascii=False, indent=2), encoding="utf-8")
                rec = appliquer(f, dest)
                self.assertTrue(rec["ok"])
                self.assertTrue(rec["unlinked"])
            calls = [c.args[1] for c in mock.flock.call_args_list]
            self.assertGreaterEqual(len(calls), 2)
            self.assertEqual(calls[0], mock.LOCK_EX)
            self.assertEqual(calls[-1], mock.LOCK_UN)
        finally:
            oubli.fcntl = orig

    def test_hors_racine_refuse_sans_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            dehors = Path(tmp) / "ailleurs"
            dehors.mkdir()
            f = dehors / "secret.txt"
            dest = Path(tmp) / "oubli.json"
            f.write_text("x\n", encoding="utf-8")
            dest.write_text(json.dumps(brouillon(f), ensure_ascii=False, indent=2), encoding="utf-8")
            rec = appliquer(f, dest, hors_racine=False)
            self.assertFalse(rec["ok"])
            self.assertEqual(rec["erreur"], "hors racine")
            self.assertFalse(rec["unlinked"])
            self.assertTrue(f.is_file())


if __name__ == "__main__":
    unittest.main()
