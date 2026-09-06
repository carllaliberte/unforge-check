#!/usr/bin/env python3
"""Locks for KEM v0. Tests, not a theorem. Not an encapsulation. Not Check."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import kem  # noqa: E402

PY = sys.executable
EXAMPLE = ROOT / "examples" / "opt-in.kem.json"


def _cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PY, str(ROOT / "kem.py"), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


class OptInRequired(unittest.TestCase):
    def test_ecrire_sans_opt_in_refuse(self):
        with self.assertRaises(SystemExit) as ctx:
            kem.ecrire("x25519mlkem768", opt_in=False)
        self.assertIn("pas par défaut", str(ctx.exception))

    def test_cli_sans_opt_in_refuse(self):
        proc = _cli(["ecrire", "--suite", "mlkem768"])
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("pas par défaut", proc.stderr)

    def test_lire_opt_in_absent_refuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "non.kem.json"
            carte = json.loads(EXAMPLE.read_text(encoding="utf-8"))
            del carte["opt_in"]
            p.write_text(json.dumps(carte), encoding="utf-8")
            with self.assertRaises(SystemExit) as ctx:
                kem.lire(str(p))
            self.assertIn("pas par défaut", str(ctx.exception))

    def test_juger_opt_in_false_deny(self):
        carte = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        carte["opt_in"] = False
        out = kem.juger(carte)
        self.assertEqual(out["decision"], "deny")
        self.assertIn("pas par défaut", out["note"])


class Ufhy1IsNotAKem(unittest.TestCase):
    def test_ecrire_ufhy1_refuse(self):
        with self.assertRaises(SystemExit) as ctx:
            kem.ecrire("UFHY1", opt_in=True)
        self.assertIn("signatures", str(ctx.exception))
        self.assertIn("Pas un KEM", str(ctx.exception))

    def test_each_signature_suite_refused(self):
        for nom in kem.SIGNATURE_SUITES:
            with self.subTest(nom=nom):
                with self.assertRaises(SystemExit) as ctx:
                    kem.ecrire(nom, opt_in=True)
                self.assertIn("Pas un KEM", str(ctx.exception))

    def test_cli_ufhy1_refuse(self):
        proc = _cli(["ecrire", "--opt-in", "--suite", "UFHY1"])
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("Pas un KEM", proc.stderr)


class SloganRefuse(unittest.TestCase):
    def test_quantum_safe_refuse(self):
        with self.assertRaises(SystemExit) as ctx:
            kem.ecrire("quantum-safe", opt_in=True)
        self.assertIn("slogan", str(ctx.exception))
        self.assertIn("quantum-safe", str(ctx.exception))

    def test_cli_quantum_safe_refuse(self):
        proc = _cli(["ecrire", "--opt-in", "--suite", "quantum-safe"])
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("slogan", proc.stderr)


class WritesWhenOptIn(unittest.TestCase):
    def test_three_suites(self):
        for nom in kem.SUITES:
            with self.subTest(nom=nom):
                carte = kem.ecrire(nom, opt_in=True)
                self.assertEqual(carte["format"], "kem.v0")
                self.assertIs(carte["opt_in"], True)
                self.assertIsNone(carte["ciphertext"])
                self.assertEqual(carte["menace"], kem.MENACE)
                self.assertNotIn("UFHY1", json.dumps(carte))
                self.assertNotIn("quantum-safe", json.dumps(carte).lower())
                self.assertNotIn("QUANTUM", json.dumps(carte))
                self.assertNotIn("quantique", json.dumps(carte))

    def test_example_juger_allow(self):
        proc = _cli(["juger", str(EXAMPLE)])
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["decision"], "allow")
        self.assertEqual(out["suite"], "x25519mlkem768")
        self.assertIsNone(out["ciphertext"])

    def test_ciphertext_non_null_deny(self):
        carte = kem.ecrire("mlkem768", opt_in=True)
        carte["ciphertext"] = "AAAA"
        out = kem.juger(carte)
        self.assertEqual(out["decision"], "deny")
        self.assertIn("null", out["note"])


class NotWiredIntoCheck(unittest.TestCase):
    def test_check_py_does_not_mention_kem_v0(self):
        texte = (ROOT / "check.py").read_text(encoding="utf-8")
        self.assertNotIn("kem.v0", texte)
        self.assertNotIn("mlkem768", texte)
        self.assertNotIn("ML-KEM", texte)

    def test_schema_is_not_juge_or_flux(self):
        s = json.loads((ROOT / "schema" / "kem.v0.json").read_text(encoding="utf-8"))
        self.assertEqual(s["title"], "unforge.kem.v0")
        self.assertEqual(s["properties"]["format"]["const"], "kem.v0")
        self.assertNotIn("quelle", s.get("required", []))
        self.assertNotIn("epsilon", s.get("properties", {}))
        check = json.loads((ROOT / "schema" / "check.v0.json").read_text(encoding="utf-8"))
        self.assertNotEqual(s["$id"], check["$id"])

    def test_spec_names_opt_in_and_not_horizon_watch(self):
        text = (ROOT / "KEM.md").read_text(encoding="utf-8")
        self.assertIn("opt-in", text.lower())
        self.assertIn("pas par défaut", text.lower())
        self.assertIn("harvest-now-decrypt-later", text)
        self.assertNotIn("HORIZON Watch", text)
        self.assertIn("juge.v0", text)
        self.assertIn("check.py", text)

    def test_cli_surface_ecrire_lire_juger(self):
        proc = _cli(["-h"])
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        self.assertIn("ecrire", proc.stdout)
        self.assertIn("lire", proc.stdout)
        self.assertIn("juger", proc.stdout)


if __name__ == "__main__":
    unittest.main()
