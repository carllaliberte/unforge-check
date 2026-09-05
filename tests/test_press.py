#!/usr/bin/env python3
"""Local press wrapper accepts v1 and v2. Does not sign. Not VERT."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from press import feuille  # noqa: E402

V2 = ROOT / "examples" / "bienvenue.txt.unforge.json"
V1 = ROOT / "examples" / "legacy-v1.unforge.json"
PY = sys.executable


def _run(path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PY, str(ROOT / "press.py"), str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


class Press(unittest.TestCase):
    def test_v2_pas_erreur_format(self):
        rec = feuille(V2)
        self.assertTrue(rec["ok"])
        self.assertNotEqual(rec.get("erreur"), "format")
        self.assertEqual(rec["format"], "UNFORGE-PREUVE-v2")
        self.assertFalse(rec["legacy"])
        self.assertEqual(rec["imprimeur"], "unforge-press")
        self.assertNotIn("VERT", rec["phrase"])
        r = _run(V2)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertTrue(json.loads(r.stdout)["ok"])

    def test_v1_ids_seulement(self):
        rec = feuille(V1)
        self.assertTrue(rec["ok"])
        self.assertTrue(rec["legacy"])
        self.assertIn("resseller v2", rec["phrase"])
        self.assertNotIn("VERT", rec["phrase"])
        r = _run(V1)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_refus_format(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "x.unforge.json"
            p.write_text(json.dumps({"format": "NON"}), encoding="utf-8")
            rec = feuille(p)
            r = _run(p)
        self.assertFalse(rec["ok"])
        self.assertEqual(rec["erreur"], "format")
        self.assertEqual(r.returncode, 1)


if __name__ == "__main__":
    unittest.main()
