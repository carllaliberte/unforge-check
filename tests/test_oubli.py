#!/usr/bin/env python3
"""OUBLI v0. Local unlink after sha256. Never sign. Never invent a token."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from oubli import FORMAT, appliquer, brouillon, lire  # noqa: E402

PY = sys.executable
SPECIMEN = ROOT / "examples" / "oubli-brouillon.json"


def _run(args: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PY, str(ROOT / "oubli.py"), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        **kw,
    )


class FormatOubli(unittest.TestCase):
    def test_format_unforge_oubli_v1(self):
        self.assertEqual(FORMAT, "UNFORGE-OUBLI-v1")
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "fichier.txt"
            f.write_bytes(b"UNFORGE oubli specimen\n")
            rec = brouillon(f)
        self.assertEqual(rec["format"], "UNFORGE-OUBLI-v1")
        self.assertEqual(rec["marque"], "UNFORGE")
        self.assertNotIn("token_id", rec)
        self.assertNotIn("signature", rec)
        self.assertNotIn("photon", rec)
        self.assertFalse(rec["applique"])

    def test_specimen_format(self):
        paquet = json.loads(SPECIMEN.read_text(encoding="utf-8"))
        self.assertEqual(paquet["format"], "UNFORGE-OUBLI-v1")
        self.assertEqual(paquet["marque"], "UNFORGE")
        self.assertNotIn("token_id", paquet)
        self.assertNotIn("signature", paquet)
        self.assertNotIn("photon", paquet)
        rec = lire(SPECIMEN)
        self.assertTrue(rec["ok"])
        self.assertEqual(rec["format"], "UNFORGE-OUBLI-v1")


class Appliquer(unittest.TestCase):
    def test_appliquer_sha256_puis_unlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "fichier.txt"
            dest = Path(tmp) / "oubli.json"
            f.write_text("à oublier\n", encoding="utf-8")
            draft = brouillon(f)
            dest.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
            sha_avant = draft["sha256"]
            self.assertTrue(f.is_file())
            rec = appliquer(f, dest)
            self.assertTrue(rec["ok"])
            self.assertTrue(rec["unlinked"])
            self.assertTrue(rec["applique"])
            self.assertEqual(rec["sha256"], sha_avant)
            self.assertFalse(f.exists())
            self.assertTrue(dest.is_file())
            carte = json.loads(dest.read_text(encoding="utf-8"))
            self.assertTrue(carte["applique"])
            self.assertEqual(carte["format"], "UNFORGE-OUBLI-v1")
            self.assertEqual(carte["sha256"], sha_avant)
            self.assertEqual(lire(dest)["applique"], True)

    def test_applique_flag_écrit_sur_disque(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "fichier.txt"
            dest = Path(tmp) / "oubli.json"
            f.write_text("flag\n", encoding="utf-8")
            dest.write_text(json.dumps(brouillon(f), ensure_ascii=False, indent=2), encoding="utf-8")
            self.assertFalse(json.loads(dest.read_text(encoding="utf-8"))["applique"])
            rec = appliquer(f, dest)
            self.assertTrue(rec["ok"])
            self.assertFalse(f.exists())
            carte = json.loads(dest.read_text(encoding="utf-8"))
            self.assertIs(carte["applique"], True)
            self.assertEqual(carte["format"], "UNFORGE-OUBLI-v1")
            self.assertNotIn("signature", carte)
            self.assertNotIn("token_id", carte)

    def test_hash_bougé_refuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "fichier.txt"
            dest = Path(tmp) / "oubli.json"
            f.write_text("original\n", encoding="utf-8")
            dest.write_text(json.dumps(brouillon(f), ensure_ascii=False, indent=2), encoding="utf-8")
            f.write_text("déplacé\n", encoding="utf-8")
            rec = appliquer(f, dest)
            self.assertFalse(rec["ok"])
            self.assertEqual(rec["erreur"], "hash bougé")
            self.assertFalse(rec["unlinked"])
            self.assertTrue(f.is_file())
            self.assertEqual(f.read_text(encoding="utf-8"), "déplacé\n")
            self.assertFalse(json.loads(dest.read_text(encoding="utf-8"))["applique"])

    def test_mauvais_format_refuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "fichier.txt"
            dest = Path(tmp) / "oubli.json"
            f.write_text("x\n", encoding="utf-8")
            dest.write_text(json.dumps({"format": "UNFORGE-PREUVE-v1", "sha256": "0" * 64}), encoding="utf-8")
            rec = appliquer(f, dest)
            self.assertFalse(rec["ok"])
            self.assertEqual(rec["erreur"], "format")
            self.assertTrue(f.is_file())
            rec_lire = lire(dest)
            self.assertFalse(rec_lire["ok"])
            self.assertEqual(rec_lire["attendu"], "UNFORGE-OUBLI-v1")


class CLI(unittest.TestCase):
    def test_brouillon_vers_appliquer_lire(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "fichier.txt"
            dest = Path(tmp) / "oubli.json"
            f.write_bytes(b"UNFORGE oubli specimen\n")
            r = _run(["brouillon", str(f), "--vers", str(dest)])
            self.assertEqual(r.returncode, 0, r.stderr)
            rec = json.loads(r.stdout)
            self.assertEqual(rec["format"], "UNFORGE-OUBLI-v1")
            self.assertTrue(dest.is_file())
            lu = _run(["lire", str(dest)])
            self.assertEqual(lu.returncode, 0, lu.stderr)
            self.assertTrue(json.loads(lu.stdout)["ok"])
            ap = _run(["appliquer", str(f), str(dest)])
            self.assertEqual(ap.returncode, 0, ap.stderr)
            rec_ap = json.loads(ap.stdout)
            self.assertTrue(rec_ap["ok"])
            self.assertTrue(rec_ap["unlinked"])
            self.assertFalse(f.exists())
            self.assertTrue(json.loads(dest.read_text(encoding="utf-8"))["applique"])
            lu2 = _run(["lire", str(dest)])
            self.assertEqual(lu2.returncode, 0, lu2.stderr)
            self.assertTrue(json.loads(lu2.stdout)["applique"])

    def test_cli_hash_bougé_exit_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "fichier.txt"
            dest = Path(tmp) / "oubli.json"
            f.write_text("a\n", encoding="utf-8")
            self.assertEqual(_run(["brouillon", str(f), "--vers", str(dest)]).returncode, 0)
            f.write_text("b\n", encoding="utf-8")
            r = _run(["appliquer", str(f), str(dest)])
            self.assertEqual(r.returncode, 1)
            rec = json.loads(r.stdout)
            self.assertEqual(rec["erreur"], "hash bougé")
            self.assertTrue(f.is_file())


if __name__ == "__main__":
    unittest.main()
