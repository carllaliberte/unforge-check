#!/usr/bin/env python3
"""Public-eye tests. Never issue. Never invent a valid QUANTUM signature.

Local Ed25519 keys below are test fixtures, labelled DEMO, not Carl's node.
"""
from __future__ import annotations

import json
import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from check import (  # noqa: E402
    ALERTE_JOURS_DEFAUT,
    FORMAT_V1,
    FORMAT_V2,
    MLDSA_MISSING,
    SCHEMA_ID,
    check,
    check_paquet,
    code_sortie,
    empreinte,
    habiller,
    ligne_verdict,
    lire_horizon,
    lire_quelle,
    materiau,
    materiau_legacy,
    mot_verdict,
    objet_lien,
    phrase_check,
    resoudre,
    resume_markdown,
    schema,
    verifier,
    verifier_signature,
    verify_ml,
    verify_sig,
    voisin_carte,
)

FICHIER = ROOT / "examples" / "bienvenue.txt"
CARTE = ROOT / "examples" / "bienvenue.txt.unforge.json"
LEGACY = ROOT / "examples" / "legacy-v1.unforge.json"
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


def _b64e(raw: bytes) -> str:
    import base64

    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _signer(*, legacy_materiau: bool = False):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

    key = Ed25519PrivateKey.generate()
    pub = _b64e(key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw))

    def sign(paquet: dict, version: int = 2) -> dict:
        paquet = dict(paquet)
        paquet["format"] = FORMAT_V2 if version >= 2 else FORMAT_V1
        paquet["card_public"] = pub
        paquet["signature_algos"] = "ed25519"
        paquet["empreinte"] = empreinte(paquet, version)
        msg = materiau_legacy(paquet) if legacy_materiau else materiau(paquet)
        paquet["signature"] = _b64e(key.sign(msg))
        return paquet

    return sign


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
        self.assertEqual(rec["format"], FORMAT_V2)
        self.assertFalse(rec["legacy"])
        self.assertFalse(rec["materiau_legacy"])
        self.assertEqual(mot_verdict(rec), "VERT")

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
        self.assertEqual(rec["phrase"], "pas UNFORGE-PREUVE-v1 ou v2.")

    def test_carte_sans_objet(self):
        p = _paquet()
        p["objet"] = {}
        rec = check_paquet(p, FICHIER)
        self.assertFalse(rec["ok"])
        self.assertEqual(rec["erreur"], "cette preuve ne constate pas un fichier")


class ObjetBoundV2(unittest.TestCase):
    """Regression: rewriting objet after signature must not VERT another file."""

    def test_empreinte_v2_inclut_objet(self):
        sign = _signer()
        brut = FICHIER.read_bytes()
        import hashlib

        sha = hashlib.sha256(brut).hexdigest()
        base = {
            "fait": "attestation de test",
            "prev": "",
            "token_id": "QT-JK-TEST",
            "card_id": "QT-EM-TEST",
            "id": "QT-PR-TEST",
            "objet": {"type": "fichier", "nom": "bienvenue.txt", "octets": len(brut), "sha256": sha},
        }
        signed = sign(base, 2)
        rec = check_paquet(signed, FICHIER)
        self.assertTrue(rec["ok"])
        self.assertTrue(rec["empreinte_ok"])
        other = hashlib.sha256(brut + b"x").hexdigest()
        tampered = dict(signed)
        tampered["objet"] = dict(signed["objet"])
        tampered["objet"]["sha256"] = other
        rec2 = check_paquet(tampered, FICHIER)
        self.assertFalse(rec2["ok"])
        self.assertFalse(rec2["empreinte_ok"])
        self.assertIn("empreinte", rec2["phrase"])

    def test_objet_swap_points_at_another_file_is_refused(self):
        sign = _signer()
        import hashlib

        a = FICHIER.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            b_path = Path(tmp) / "autre.txt"
            b_path.write_bytes(b"pas le fichier scelle\n")
            b = b_path.read_bytes()
            paquet = sign(
                {
                    "fait": "fichier A",
                    "prev": "",
                    "token_id": "T-A",
                    "card_id": "C-A",
                    "id": "P-A",
                    "objet": {
                        "type": "fichier",
                        "nom": "bienvenue.txt",
                        "octets": len(a),
                        "sha256": hashlib.sha256(a).hexdigest(),
                    },
                },
                2,
            )
            rec_a = check_paquet(paquet, FICHIER)
            self.assertTrue(rec_a["ok"], rec_a)
            swapped = dict(paquet)
            swapped["objet"] = {
                "type": "fichier",
                "nom": "autre.txt",
                "octets": len(b),
                "sha256": hashlib.sha256(b).hexdigest(),
            }
            rec_b = check_paquet(swapped, b_path)
            self.assertFalse(rec_b["ok"])
            self.assertFalse(rec_b["empreinte_ok"])
            self.assertEqual(code_sortie(rec_b), 1)
            self.assertTrue(rec_b["fichier_ok"], "naive file match would hold — the seal must not")

    def test_v1_objet_swap_is_not_vert(self):
        """v1 still cannot bind objet; dual check must not VERT a swapped card."""
        p = json.loads(LEGACY.read_text(encoding="utf-8"))
        rec_orig = check_paquet(p, FICHIER)
        self.assertFalse(rec_orig["ok"])
        self.assertTrue(rec_orig["legacy"])
        self.assertTrue(rec_orig["empreinte_ok"])
        self.assertTrue(rec_orig["signature_ok"])
        self.assertEqual(rec_orig["erreur"], "format-v1")
        self.assertEqual(code_sortie(rec_orig), 1)
        self.assertTrue(ligne_verdict(rec_orig, color=False).startswith("AMBRE"))

        import hashlib

        with tempfile.TemporaryDirectory() as tmp:
            autre = Path(tmp) / "autre.txt"
            autre.write_bytes(b"fichier B pour l'attaque v1\n")
            swapped = dict(p)
            swapped["objet"] = dict(p["objet"])
            swapped["objet"]["sha256"] = hashlib.sha256(autre.read_bytes()).hexdigest()
            swapped["objet"]["octets"] = autre.stat().st_size
            rec = check_paquet(swapped, autre)
        self.assertTrue(rec["empreinte_ok"], "v1 formula still ignores objet")
        self.assertTrue(rec["signature_ok"])
        self.assertTrue(rec["fichier_ok"])
        self.assertFalse(rec["ok"])
        self.assertEqual(rec["erreur"], "format-v1")
        self.assertFalse(ligne_verdict(rec, color=False).startswith("VERT"))


class HybrideMateriauJalon2(unittest.TestCase):
    """Ed and ML-DSA-65 sign the same bytes; objet_lien is in materiau()."""

    def test_materiau_v2_contient_objet_sha256_et_octets(self):
        p = _paquet()
        lien = objet_lien(p)
        mat = materiau(p).decode()
        self.assertIn(p["objet"]["sha256"], mat)
        self.assertIn(str(p["objet"]["octets"]), mat)
        self.assertEqual(lien, f"{p['objet']['sha256']}|{p['objet']['octets']}")
        self.assertEqual(
            mat,
            f"{p['card_id']}|{p['token_id']}|REGISTRE|{p['empreinte']}|{lien}",
        )
        self.assertNotEqual(materiau(p), materiau_legacy(p))
        self.assertEqual(
            materiau_legacy(p).decode(),
            f"{p['card_id']}|{p['token_id']}|REGISTRE|{p['empreinte']}",
        )

    def test_ufhy1_meme_message_aux_deux_verifieurs(self):
        p = _paquet()
        p["signature"] = "UFHY1:edSIG:mlSIG"
        p["card_public_pq"] = "pqPUB"
        recu = []

        def _ed(pub, message, sig):
            recu.append(("ed", message, sig))
            return True

        def _ml(pub, message, sig):
            recu.append(("ml", message, sig))
            return True

        msg = b"octets-canoniques-identiques"
        with patch("check.verify_ed", side_effect=_ed), patch("check.verify_ml", side_effect=_ml):
            ok, note = verify_sig(p, msg)
        self.assertTrue(ok)
        self.assertIsNone(note)
        self.assertEqual(len(recu), 2)
        self.assertEqual(recu[0][0], "ed")
        self.assertEqual(recu[1][0], "ml")
        self.assertEqual(recu[0][1], recu[1][1])
        self.assertEqual(recu[0][1], msg)
        self.assertEqual(recu[1][1], msg)

    def test_ufhy1_fallback_ne_divise_pas_les_messages(self):
        p = _paquet()
        p["signature"] = "UFHY1:AAAA:BBBB"
        p["card_public_pq"] = "CCCC"
        appels = []

        def _ed(pub, message, sig):
            appels.append(("ed", message))
            return False

        def _ml(pub, message, sig):
            appels.append(("ml", message))
            return False

        with patch("check.verify_ed", side_effect=_ed), patch("check.verify_ml", side_effect=_ml):
            ok, note, used_legacy = verifier_signature(p)
        self.assertFalse(ok)
        self.assertIsNone(note)
        self.assertFalse(used_legacy)
        self.assertEqual(len(appels), 4)
        self.assertEqual(appels[0][1], appels[1][1])
        self.assertEqual(appels[2][1], appels[3][1])
        self.assertEqual(appels[0][1], materiau(p))
        self.assertEqual(appels[2][1], materiau_legacy(p))
        self.assertNotEqual(appels[0][1], appels[2][1])

    def test_fixture_v2_jalon2_vert(self):
        rec = check(CARTE, FICHIER)
        self.assertTrue(rec["ok"])
        self.assertTrue(rec["signature_ok"])
        self.assertTrue(rec["fichier_ok"])
        self.assertFalse(rec["materiau_legacy"])
        self.assertNotIn("erreur", rec)
        self.assertEqual(mot_verdict(rec), "VERT")
        self.assertEqual(rec["phrase"], "le fichier correspond à la carte.")
        self.assertEqual(code_sortie(rec), 0)

    def test_signature_legacy_synthetique_tient(self):
        sign = _signer(legacy_materiau=True)
        brut = FICHIER.read_bytes()
        signed = sign(
            {
                "fait": "attestation legacy materiau",
                "prev": "",
                "token_id": "QT-JK-LEGACY-MAT",
                "card_id": "QT-EM-LEGACY-MAT",
                "id": "QT-PR-LEGACY-MAT",
                "objet": {
                    "type": "fichier",
                    "nom": "bienvenue.txt",
                    "octets": len(brut),
                    "sha256": hashlib.sha256(brut).hexdigest(),
                },
            },
            2,
        )
        rec = check_paquet(signed, FICHIER)
        self.assertFalse(rec["ok"], rec)
        self.assertTrue(rec["signature_ok"])
        self.assertTrue(rec["materiau_legacy"])
        self.assertEqual(mot_verdict(rec), "AMBRE")
        self.assertIn("objet non couvert par la signature d'origine", rec["phrase"])

    def test_objet_swap_after_materiau_legacy_never_vert(self):
        """v2 signed only on materiau_legacy: swapping objet.sha256 to another file is never VERT."""
        sign = _signer(legacy_materiau=True)
        brut = FICHIER.read_bytes()
        autre = b"objet-substitue-apres-signature"
        signed = sign(
            {
                "fait": "attestation legacy materiau swap",
                "prev": "",
                "token_id": "QT-JK-LEGACY-SWAP",
                "card_id": "QT-EM-LEGACY-SWAP",
                "id": "QT-PR-LEGACY-SWAP",
                "objet": {
                    "type": "fichier",
                    "nom": "bienvenue.txt",
                    "octets": len(brut),
                    "sha256": hashlib.sha256(brut).hexdigest(),
                },
            },
            2,
        )
        tampered = dict(signed)
        tampered["objet"] = dict(signed["objet"])
        tampered["objet"]["sha256"] = hashlib.sha256(autre).hexdigest()
        tampered["objet"]["octets"] = len(autre)
        with tempfile.TemporaryDirectory() as tmp:
            autre_path = Path(tmp) / "autre.txt"
            autre_path.write_bytes(autre)
            rec = check_paquet(tampered, autre_path)
        self.assertTrue(rec["signature_ok"], "legacy materiau still verifies the old empreinte")
        self.assertTrue(rec["materiau_legacy"])
        self.assertTrue(rec["fichier_ok"], "presented file matches the swapped objet")
        self.assertFalse(rec["ok"])
        self.assertNotEqual(mot_verdict(rec), "VERT")
        self.assertEqual(code_sortie(rec), 1)

    def test_objet_mismatch_vs_materiau_refuse(self):
        sign = _signer()
        brut = FICHIER.read_bytes()
        import hashlib

        sha = hashlib.sha256(brut).hexdigest()
        signed = sign(
            {
                "fait": "attestation materiau objet",
                "prev": "",
                "token_id": "QT-JK-MAT-OBJ",
                "card_id": "QT-EM-MAT-OBJ",
                "id": "QT-PR-MAT-OBJ",
                "objet": {
                    "type": "fichier",
                    "nom": "bienvenue.txt",
                    "octets": len(brut),
                    "sha256": sha,
                },
            },
            2,
        )
        rec_ok = check_paquet(signed, FICHIER)
        self.assertTrue(rec_ok["ok"], rec_ok)
        self.assertFalse(rec_ok["materiau_legacy"])

        tampered = dict(signed)
        tampered["objet"] = dict(signed["objet"])
        tampered["objet"]["sha256"] = hashlib.sha256(b"autre-objet").hexdigest()
        tampered["empreinte"] = empreinte(tampered, 2)
        rec = check_paquet(tampered, None)
        self.assertTrue(rec["empreinte_ok"], "empreinte recomputed to match swapped objet")
        self.assertFalse(rec["signature_ok"])
        self.assertFalse(rec["ok"])
        self.assertFalse(rec["materiau_legacy"])

    def test_interop_jalon_2(self):
        texte = (ROOT / "INTEROP.md").read_text(encoding="utf-8")
        self.assertIn("jalon 2", texte)
        self.assertIn("objet.sha256", texte)
        self.assertIn("materiau_legacy", texte)
        self.assertIn("empreinte", texte)


class LegacyV1(unittest.TestCase):
    def test_legacy_fixture_exists(self):
        p = json.loads(LEGACY.read_text(encoding="utf-8"))
        self.assertEqual(p["format"], FORMAT_V1)

    def test_cli_legacy_exit_1(self):
        r = _run([str(FICHIER), str(LEGACY)])
        self.assertEqual(r.returncode, 1)
        rec = json.loads(r.stdout)
        self.assertFalse(rec["ok"])
        self.assertEqual(rec["erreur"], "format-v1")
        self.assertIn("resseller en v2", rec["phrase"])


class MldsaDisponible(unittest.TestCase):
    def test_import_error_is_named(self):
        with patch.dict("sys.modules", {"cryptography.hazmat.primitives.asymmetric.mldsa": None}):
            with self.assertRaises(ImportError) as ctx:
                verify_ml("A", b"m", "A")
        self.assertIn("ML-DSA non disponible", str(ctx.exception))

    def test_check_paquet_names_missing_mldsa(self):
        p = _paquet()
        p["signature"] = "UFHY1:" + p["signature"] + ":AAAA"
        p["card_public_pq"] = "AAAA"
        with patch("check.verify_ml", side_effect=ImportError(MLDSA_MISSING)):
            rec = check_paquet(p, None)
        self.assertFalse(rec["ok"])
        self.assertFalse(rec["signature_ok"])
        self.assertEqual(rec["crypto"]["erreur"], MLDSA_MISSING)
        self.assertEqual(rec["phrase"], MLDSA_MISSING)

    def test_ufhy1_without_mldsa_is_not_silent_false(self):
        p = _paquet()
        p["signature"] = "UFHY1:AAAA:BBBB"
        p["card_public_pq"] = "AAAA"
        with patch("check.verify_ml", side_effect=ImportError(MLDSA_MISSING)):
            ok, note = verify_sig(p, materiau(p))
        self.assertFalse(ok)
        self.assertEqual(note, MLDSA_MISSING)
        rec = check_paquet({**p}, None)
        # without the patch on check_paquet's import path, ML-DSA may exist;
        # the named error is locked by verify_sig above.


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
        self.assertFalse(rec["horizon"].get("horizon_watch"))
        self.assertEqual(code_sortie(rec), 1)
        self.assertIn("resseller", rec["phrase"])

    def _horizon(self, suite: str, jours: int) -> dict:
        jour = (datetime.now(timezone.utc).date() + timedelta(days=jours)).isoformat()
        with tempfile.TemporaryDirectory() as tmp:
            h = Path(tmp) / "h.horizon.json"
            h.write_text(
                json.dumps({"format": "horizon.v0", "suite": suite, "re_presser_avant": jour}),
                encoding="utf-8",
            )
            return lire_horizon(h)

    def test_horizon_watch_ed25519_dans_90j(self):
        self.assertEqual(ALERTE_JOURS_DEFAUT, 90)
        rec = self._horizon("ed25519", 30)
        self.assertTrue(rec["ok"])
        self.assertTrue(rec["horizon_watch"])
        self.assertIn("approche re_presser_avant", rec["note"])
        bord = self._horizon("ed25519", ALERTE_JOURS_DEFAUT)
        self.assertTrue(bord["ok"])
        self.assertTrue(bord["horizon_watch"])

    def test_horizon_watch_ed25519_loin(self):
        rec = self._horizon("ed25519", ALERTE_JOURS_DEFAUT + 1)
        self.assertTrue(rec["ok"])
        self.assertFalse(rec["horizon_watch"])
        self.assertEqual(rec["note"], "lue. pas signée ici.")

    def test_horizon_watch_ufhy1_dans_90j_pas_de_watch(self):
        rec = self._horizon("UFHY1", 30)
        self.assertTrue(rec["ok"])
        self.assertFalse(rec.get("horizon_watch"))

    def test_horizon_expire_toujours_ok_false(self):
        rec = self._horizon("ed25519", -1)
        self.assertFalse(rec["ok"])
        self.assertFalse(rec.get("horizon_watch"))
        self.assertIn("périmé", rec["note"])

    def test_horizon_watch_ne_casse_pas_vert(self):
        jour = (datetime.now(timezone.utc).date() + timedelta(days=30)).isoformat()
        with tempfile.TemporaryDirectory() as tmp:
            h = Path(tmp) / "h.horizon.json"
            h.write_text(
                json.dumps({"format": "horizon.v0", "suite": "ed25519", "re_presser_avant": jour}),
                encoding="utf-8",
            )
            rec = verifier(CARTE, FICHIER, horizon=h)
        self.assertTrue(rec["ok"])
        self.assertTrue(rec["horizon"]["ok"])
        self.assertTrue(rec["horizon"]["horizon_watch"])
        self.assertEqual(mot_verdict(rec), "VERT")
        self.assertEqual(code_sortie(rec), 0)
        self.assertIn("approche re_presser_avant", rec["phrase"])

    def test_interop_jalon_5(self):
        texte = (ROOT / "INTEROP.md").read_text(encoding="utf-8")
        self.assertIn("jalon 5", texte)
        self.assertIn("horizon_watch", texte)
        self.assertIn("--horizon", texte)


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
        self.assertEqual(rec["format"], FORMAT_V2)
        self.assertFalse(rec["materiau_legacy"])

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

    def test_summary_vert(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "summary.md"
            env = {**os.environ, "NO_COLOR": "1", "GITHUB_STEP_SUMMARY": str(dest)}
            r = _run([str(FICHIER), "--summary"], env=env)
            text = dest.read_text(encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)
        rec = json.loads(r.stdout)
        self.assertTrue(rec["ok"])
        self.assertIn("## VERT — file matches the card", text)
        self.assertIn("Does not sign", text)
        self.assertIn("Not a receipt", text)
        self.assertIn("Digest/match only", text)
        self.assertNotIn("ε=0", text)
        self.assertNotIn("epsilon=0", text.lower())
        self.assertNotIn("signé", text.lower())

    def test_summary_rouge(self):
        with tempfile.TemporaryDirectory() as tmp:
            copie = Path(tmp) / "x.txt"
            copie.write_text("pas le fichier scellé\n", encoding="utf-8")
            dest = Path(tmp) / "summary.md"
            env = {**os.environ, "NO_COLOR": "1", "GITHUB_STEP_SUMMARY": str(dest)}
            r = _run([str(copie), str(CARTE), "--summary"], env=env)
            text = dest.read_text(encoding="utf-8")
        self.assertEqual(r.returncode, 1)
        self.assertIn("## ROUGE — refuse", text)
        self.assertIn("Does not sign", text)
        self.assertIn("Not a receipt", text)
        self.assertNotIn("ε=0", text)

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

    def test_example_public_couple_is_vert(self):
        rec = check(CARTE, FICHIER)
        self.assertFalse(rec["materiau_legacy"])
        self.assertEqual(mot_verdict(rec), "VERT")
        r = _run([str(FICHIER), "--human"], env={**os.environ, "NO_COLOR": "1"})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.splitlines()[0].startswith("VERT"))

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

    def test_porte_60s_et_badge(self):
        porte = (ROOT / "docs" / "porte.html").read_text(encoding="utf-8")
        self.assertIn("python3 check.py examples/bienvenue.txt --human", porte)
        self.assertIn("VERT", porte)
        self.assertIn("unforge-press", porte)
        self.assertIn("@v1.0.0", porte)
        self.assertIn("jamais", porte)
        self.assertNotIn("unforge-check@main", porte)
        self.assertNotIn("quantum.db", porte)
        self.assertNotIn("PRÉSENT", porte)
        self.assertNotIn("consulter", porte.lower())
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("python3 check.py examples/bienvenue.txt --human", readme)
        self.assertIn("carllaliberte/unforge-check@v1.0.0", readme)
        self.assertNotIn("unforge-check@main", readme)
        self.assertNotIn("quantum.db", readme)
        self.assertNotIn("PRÉSENT", readme)
        action = (ROOT / "ACTION.md").read_text(encoding="utf-8")
        self.assertIn("carllaliberte/unforge-check@v1.0.0", action)
        self.assertIn("badge.svg", action)
        self.assertIn("Does not sign", action)
        self.assertIn("Not a receipt", action)
        self.assertIn("Preview ≠ receipt", action)
        self.assertNotIn("unforge-check@main", action)
        self.assertNotIn("ε=0", action)
        self.assertNotIn("epsilon=0", action.lower())


class CiBadge(unittest.TestCase):
    """CI badge / job summary: digest/match only. Does not sign."""

    def test_mot_verdict_couple(self):
        rec = check(CARTE, FICHIER)
        self.assertEqual(mot_verdict(rec), "VERT")
        md = resume_markdown(rec)
        self.assertIn("## VERT — file matches the card", md)
        self.assertIn("Does not sign", md)
        self.assertIn("Not a receipt", md)
        self.assertNotIn("ε=0", md)
        self.assertNotIn("receipt of", md.lower())

    def test_mot_verdict_refuse(self):
        rec = habiller({"ok": False, "erreur": "json"})
        self.assertEqual(mot_verdict(rec), "ROUGE")
        self.assertIn("## ROUGE — refuse", resume_markdown(rec))

    def test_mot_verdict_legacy_ambre(self):
        rec = check(LEGACY, FICHIER)
        self.assertEqual(mot_verdict(rec), "AMBRE")
        self.assertFalse(rec["ok"])
        self.assertIn("re-press", resume_markdown(rec))

    def test_action_writes_summary_and_does_not_sign(self):
        action = (ROOT / "action.yml").read_text(encoding="utf-8")
        self.assertIn("--summary", action)
        self.assertIn("Does not sign", action)
        self.assertNotRegex(action, r"(?i)openssl\s+dgst")
        self.assertNotIn("quantum.db", action)
        self.assertNotIn("ε=0", action)

    def test_constat_has_check_job(self):
        yml = (ROOT / ".github" / "workflows" / "constat.yml").read_text(encoding="utf-8")
        self.assertIn("name: Check", yml)
        self.assertIn("--human --summary", yml)
        self.assertIn("uses: ./", yml)
        self.assertNotIn("quantum.db", yml)
        self.assertNotRegex(yml, r"(?i)sign\s+the")
        self.assertNotIn("ε=0", yml)

    def test_readme_badge_is_match_not_receipt(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("badge.svg?branch=main", readme)
        self.assertIn("Does not sign", readme)
        self.assertIn("Not a receipt", readme)
        self.assertIn("job summary", readme)
        self.assertNotIn("ε=0", readme)



if __name__ == "__main__":
    unittest.main()
