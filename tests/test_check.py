#!/usr/bin/env python3
"""Public-eye tests. Never issue. Never invent a valid signature."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from check import (  # noqa: E402
    SCHEMA_ID,
    check,
    check_paquet,
    code_sortie,
    habiller,
    ligne_verdict,
    lire_horizon,
    lire_quelle,
    phrase_check,
    resoudre,
    schema,
    verifier,
    voisin_carte,
)

FICHIER = ROOT / "examples" / "bienvenue.txt"
CARTE = ROOT / "examples" / "bienvenue.txt.unforge.json"
PY = sys.executable


def _run(args: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PY, str(ROOT / "check.py"), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        **kw,
    )


def _paquet() -> dict:
    return json.loads(CARTE.read_text(encoding="utf-8"))


class CheckFichier(unittest.TestCase):
    def test_couple_tient(self):
        rec = check(CARTE, FICHIER)
        self.assertTrue(rec["ok"])
        self.assertTrue(rec["empreinte_ok"])
        self.assertTrue(rec["signature_ok"])
        self.assertTrue(rec["fichier_ok"])
        self.assertEqual(rec["geste"], "check")
        self.assertEqual(rec["schema"], SCHEMA_ID)
        self.assertEqual(rec["noeud"], "non requis")
        self.assertEqual(rec["phrase"], "le fichier correspond à la carte.")
        self.assertEqual(rec["sha256"], rec["sha256_attendu"])
        self.assertEqual(rec["octets"], FICHIER.stat().st_size)

    def test_carte_seule(self):
        rec = check(CARTE, None)
        self.assertTrue(rec["ok"])
        self.assertIsNone(rec["fichier_ok"])
        self.assertEqual(rec["phrase"], "la carte tient. aucun fichier présenté.")

    def test_fichier_altéré(self):
        with tempfile.TemporaryDirectory() as tmp:
            copie = Path(tmp) / "bienvenue.txt"
            copie.write_bytes(FICHIER.read_bytes() + b"\n")
            rec = check(CARTE, copie)
        self.assertFalse(rec["ok"])
        self.assertFalse(rec["fichier_ok"])
        self.assertTrue(rec["signature_ok"])
        self.assertNotEqual(rec["sha256"], rec["sha256_attendu"])
        self.assertEqual(rec["phrase"], "le fichier ne correspond pas à la carte.")
        self.assertEqual(code_sortie(rec), 1)

    def test_empreinte_cassée(self):
        p = _paquet()
        p["empreinte"] = "0" * 64
        rec = check_paquet(p, FICHIER)
        self.assertFalse(rec["ok"])
        self.assertFalse(rec["empreinte_ok"])
        self.assertIn("empreinte", rec["phrase"])

    def test_signature_cassée(self):
        p = _paquet()
        p["signature"] = "A" * len(p["signature"])
        rec = check_paquet(p, FICHIER)
        self.assertFalse(rec["ok"])
        self.assertFalse(rec["signature_ok"])
        self.assertEqual(rec["phrase"], "la signature ne tient pas.")

    def test_ufhy1_malformé(self):
        p = _paquet()
        p["signature"] = "UFHY1:pas-deux-moities"
        rec = check_paquet(p, None)
        self.assertFalse(rec["signature_ok"])
        self.assertFalse(rec["ok"])

    def test_mauvais_format(self):
        rec = check_paquet({"format": "NON"}, None)
        self.assertFalse(rec["ok"])
        self.assertEqual(rec["erreur"], "format")
        self.assertEqual(rec["phrase"], "pas UNFORGE-PREUVE-v1.")

    def test_carte_sans_objet(self):
        p = _paquet()
        p["objet"] = {}
        rec = check_paquet(p, FICHIER)
        self.assertFalse(rec["ok"])
        self.assertEqual(rec["erreur"], "cette preuve ne constate pas un fichier")


class Satellites(unittest.TestCase):
    def test_quelle_os(self):
        with tempfile.TemporaryDirectory() as tmp:
            q = Path(tmp) / "os.quelle.json"
            q.write_text(json.dumps({"format": "quelle.v0", "source": "os", "id": "q1"}), encoding="utf-8")
            rec = lire_quelle(q)
        self.assertTrue(rec["ok"])
        self.assertEqual(rec["source"], "os")

    def test_quelle_mensongère(self):
        with tempfile.TemporaryDirectory() as tmp:
            q = Path(tmp) / "qrng.quelle.json"
            q.write_text(json.dumps({"format": "quelle.v0", "source": "qrng"}), encoding="utf-8")
            rec = lire_quelle(q)
        self.assertFalse(rec["ok"])
        self.assertIn("mensongère", rec["note"])

    def test_horizon_vivant(self):
        jour = (datetime.now(timezone.utc).date() + timedelta(days=30)).isoformat()
        with tempfile.TemporaryDirectory() as tmp:
            h = Path(tmp) / "h.horizon.json"
            h.write_text(json.dumps({"format": "horizon.v0", "suite": "UFHY1", "re_presser_avant": jour}), encoding="utf-8")
            rec = lire_horizon(h)
        self.assertTrue(rec["ok"])
        self.assertEqual(rec["courbe"], "Ed25519 + ML-DSA-65")

    def test_horizon_mort_ne_forge_pas_le_fichier(self):
        jour = (date(2020, 1, 1)).isoformat()
        with tempfile.TemporaryDirectory() as tmp:
            h = Path(tmp) / "h.horizon.json"
            h.write_text(json.dumps({"format": "horizon.v0", "suite": "ed25519", "re_presser_avant": jour}), encoding="utf-8")
            rec = verifier(CARTE, FICHIER, horizon=h)
        self.assertTrue(rec["ok"], "dead horizon does not forge the file")
        self.assertFalse(rec["horizon"]["ok"])
        self.assertEqual(code_sortie(rec), 1)
        self.assertIn("resseller", rec["phrase"])


class Resoudre(unittest.TestCase):
    def test_voisin(self):
        self.assertEqual(voisin_carte(FICHIER), CARTE)
        carte, fichier = resoudre([FICHIER])
        self.assertEqual(carte, CARTE)
        self.assertEqual(fichier, FICHIER)

    def test_carte_seule(self):
        carte, fichier = resoudre([CARTE])
        self.assertEqual(carte, CARTE)
        self.assertIsNone(fichier)

    def test_deux_chemins(self):
        carte, fichier = resoudre([FICHIER, CARTE])
        self.assertEqual(carte, CARTE)
        self.assertEqual(fichier, FICHIER)

    def test_voisin_absent(self):
        with self.assertRaises(FileNotFoundError):
            resoudre([ROOT / "README.md"])


class SchemaEtHabit(unittest.TestCase):
    def test_schema_fichier(self):
        s = schema()
        self.assertEqual(s["title"], "unforge.check.v0")
        self.assertIn("ok", s["required"])
        self.assertIn("geste", s["required"])

    def test_habiller_erreur(self):
        rec = habiller({"ok": False, "erreur": "json"})
        self.assertEqual(rec["geste"], "check")
        self.assertEqual(phrase_check(rec), "JSON illisible.")


class CLI(unittest.TestCase):
    def test_couple_exit_0(self):
        r = _run([str(FICHIER), str(CARTE)])
        self.assertEqual(r.returncode, 0, r.stderr)
        rec = json.loads(r.stdout)
        self.assertTrue(rec["ok"])
        self.assertEqual(rec["geste"], "check")

    def test_voisin_une_commande(self):
        r = _run([str(FICHIER)])
        self.assertEqual(r.returncode, 0, r.stderr)
        rec = json.loads(r.stdout)
        self.assertTrue(rec["ok"])
        self.assertTrue(rec["fichier_ok"])

    def test_human(self):
        r = _run([str(FICHIER), "--human"], env={**os.environ, "NO_COLOR": "1"})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("VERT", r.stdout)
        self.assertIn("le fichier correspond à la carte.", r.stdout)
        self.assertNotIn("{", r.stdout)

    def test_schema_flag(self):
        r = _run(["--schema"])
        self.assertEqual(r.returncode, 0, r.stderr)
        rec = json.loads(r.stdout)
        self.assertEqual(rec["title"], "unforge.check.v0")

    def test_sans_args(self):
        r = _run([])
        self.assertEqual(r.returncode, 2)
        self.assertIn("drop a file", r.stderr)

    def test_fichier_altéré_exit_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            copie = Path(tmp) / "x.txt"
            copie.write_text("pas le fichier scellé\n", encoding="utf-8")
            r = _run([str(copie), str(CARTE)])
        self.assertEqual(r.returncode, 1)
        rec = json.loads(r.stdout)
        self.assertFalse(rec["ok"])
        self.assertFalse(rec["fichier_ok"])

    def test_carte_absente(self):
        with tempfile.TemporaryDirectory() as tmp:
            seul = Path(tmp) / "orphelin.txt"
            seul.write_text("x", encoding="utf-8")
            r = _run([str(seul)])
        self.assertEqual(r.returncode, 2)
        rec = json.loads(r.stdout)
        self.assertEqual(rec["erreur"], "preuve introuvable")


class WordingHold(unittest.TestCase):
    """VERT = match. Public eye, not a seal. No quantum-green gloss."""

    PUBLIC = (
        ROOT / "README.md",
        ROOT / "INTEROP.md",
        ROOT / "schema" / "check.v0.json",
        ROOT / "check.py",
    )

    def test_vert_est_match(self):
        rec = check(CARTE, FICHIER)
        self.assertTrue(rec["ok"])
        ligne = ligne_verdict(rec, color=False)
        self.assertTrue(ligne.startswith("VERT"))
        self.assertIn("le fichier correspond à la carte.", ligne)
        r = _run([str(FICHIER), "--human"], env={**os.environ, "NO_COLOR": "1"})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.splitlines()[0].startswith("VERT"))
        self.assertIn("le fichier correspond à la carte.", r.stdout)

    def test_vert_match_dans_readme_interop_aide_schema(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("VERT means the file matches the card", readme)
        self.assertIn("VERT = match (file ↔ card)", readme)
        interop = (ROOT / "INTEROP.md").read_text(encoding="utf-8")
        self.assertIn("VERT = the file matches the card", interop)
        s = schema()
        desc = s["description"] + " " + s["properties"]["ok"]["description"]
        self.assertIn("match (file ↔ card)", desc)
        self.assertIn("VERT", desc)
        aide = _run(["--help"])
        self.assertEqual(aide.returncode, 0, aide.stderr)
        self.assertIn("VERT = match (file ↔ card)", aide.stdout)

    def test_refuse_quantum_green_comme_gloss_vert(self):
        for chemin in self.PUBLIC:
            texte = chemin.read_text(encoding="utf-8")
            self.assertNotRegex(
                texte,
                r"(?i)quantum\s+green",
                f"{chemin.name} must not gloss VERT as quantum green",
            )
        aide = _run(["--help"])
        self.assertNotRegex(aide.stdout, r"(?i)quantum\s+green")
        self.assertNotRegex(aide.stderr, r"(?i)quantum\s+green")

    def test_refuse_famille_quantique(self):
        for chemin in self.PUBLIC:
            texte = chemin.read_text(encoding="utf-8")
            self.assertNotRegex(
                texte,
                r"(?i)famille\s+quantique",
                f"{chemin.name} must not read FAMILLE as quantique",
            )

    def test_pas_imagine(self):
        for chemin in self.PUBLIC:
            self.assertNotIn("Imagine", chemin.read_text(encoding="utf-8"))
        aide = _run(["--help"])
        self.assertNotIn("Imagine", aide.stdout)
        self.assertNotIn("Imagine", aide.stderr)

    def test_pas_formally_verified(self):
        for chemin in self.PUBLIC:
            self.assertNotRegex(
                chemin.read_text(encoding="utf-8"),
                r"(?i)formally\s+verified",
            )
        aide = _run(["--help"])
        self.assertNotRegex(aide.stdout, r"(?i)formally\s+verified")
        self.assertNotRegex(aide.stderr, r"(?i)formally\s+verified")


if __name__ == "__main__":
    unittest.main()
