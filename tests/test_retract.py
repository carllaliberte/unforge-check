#!/usr/bin/env python3
"""Retract verifies with the unpacked verify_sig tuple. Never signs."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from retract import materiau_retrait, verifier  # noqa: E402

PREUVE = ROOT / "examples" / "bienvenue.txt.unforge.json"
PY = sys.executable


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PY, str(ROOT / "retract.py"), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def _retrait(preuve: dict, signature) -> dict:
    return {
        "format": "UNFORGE-RETRAIT-v1",
        "preuve_id": preuve.get("id"),
        "card_id": preuve.get("card_id"),
        "card_public": preuve.get("card_public"),
        "token_id": preuve.get("token_id"),
        "empreinte": preuve.get("empreinte"),
        "materiau": materiau_retrait(preuve),
        "signature": signature,
    }


class Retract(unittest.TestCase):
    def test_garbage_signature_exit_1(self):
        preuve = json.loads(PREUVE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            rpath = Path(tmp) / "r.json"
            rpath.write_text(json.dumps(_retrait(preuve, "not-a-signature")), encoding="utf-8")
            r = _run(["verifier", str(PREUVE), str(rpath)])
        self.assertEqual(r.returncode, 1, r.stdout)
        rec = json.loads(r.stdout)
        self.assertFalse(rec["ok"])
        self.assertIs(rec["signature_ok"], False)
        self.assertIsInstance(rec["signature_ok"], bool)

    def test_signature_absente_refus(self):
        preuve = json.loads(PREUVE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            rpath = Path(tmp) / "r.json"
            rpath.write_text(json.dumps(_retrait(preuve, None)), encoding="utf-8")
            r = _run(["verifier", str(PREUVE), str(rpath)])
        self.assertEqual(r.returncode, 1)
        rec = json.loads(r.stdout)
        self.assertFalse(rec["ok"])
        self.assertFalse(rec["signature_ok"])
        self.assertEqual(rec.get("erreur"), "signature absente")

    def test_tuple_n_est_pas_un_bool(self):
        preuve = json.loads(PREUVE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            ppath = Path(tmp) / "p.json"
            rpath = Path(tmp) / "r.json"
            ppath.write_text(json.dumps(preuve), encoding="utf-8")
            rpath.write_text(json.dumps(_retrait(preuve, "AAAA")), encoding="utf-8")
            rec = verifier(ppath, rpath)
        self.assertIsInstance(rec["signature_ok"], bool)
        self.assertFalse(rec["signature_ok"])
        self.assertFalse(rec["ok"])
        self.assertNotIsInstance(rec["signature_ok"], tuple)


if __name__ == "__main__":
    unittest.main()
