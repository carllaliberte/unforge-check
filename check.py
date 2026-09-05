#!/usr/bin/env python3
"""UNFORGE Check — verify a .unforge.json against an optional file.
Optional: read a QUELLE card and an HORIZON card. Does not sign.

UNFORGE-PREUVE-v2 binds objet.sha256 and objet.octets into empreinte.
v1 cards are read (dual check) but never VERT — objet was not in the seal.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

FORMAT_V1 = "UNFORGE-PREUVE-v1"
FORMAT_V2 = "UNFORGE-PREUVE-v2"
FORMAT = FORMAT_V2
FORMATS = {FORMAT_V1: 1, FORMAT_V2: 2}
HY = "UFHY1:"
QUELLE_FMT = "quelle.v0"
HORIZON_FMT = "horizon.v0"
SUITES = ("ed25519", "UFHY1", "mldsa87")
SCHEMA_ID = "check.v0"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema" / "check.v0.json"
MLDSA_MISSING = "ML-DSA non disponible dans cette installation"

# VERT = match (file ↔ card). ROUGE = refuse. AMBRE = match with a dead satellite
# or a v1 card during the transition (objet not bound).
# Public eye, not a seal.
VERT = "\033[38;2;57;255;136m"
ROUGE = "\033[38;2;255;77;79m"
AMBRE = "\033[38;2;245;200;66m"
RESET = "\033[0m"


def b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def format_version(paquet: dict) -> int | None:
    return FORMATS.get(paquet.get("format"))


def octets_canon(value) -> str:
    if value is None or isinstance(value, bool):
        return ""
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    s = str(value).strip()
    if s.isdigit():
        return str(int(s))
    return s


def objet_lien(paquet: dict) -> str:
    objet = paquet.get("objet")
    if not isinstance(objet, dict):
        objet = {}
    sha = str(objet.get("sha256") or "")
    return f"{sha}|{octets_canon(objet.get('octets'))}"


def materiau(paquet: dict) -> bytes:
    return f"{paquet.get('card_id') or ''}|{paquet.get('token_id') or ''}|REGISTRE|{paquet.get('empreinte') or ''}".encode()


def empreinte(paquet: dict, version: int | None = None) -> str:
    """SHA-256 of the attested material.

    v1: fait|prev|token_id
    v2: fait|prev|token_id|objet.sha256|objet.octets
    """
    ver = version if version is not None else (format_version(paquet) or 2)
    base = f"{paquet.get('fait') or ''}|{paquet.get('prev') or ''}|{paquet.get('token_id') or ''}"
    if ver >= 2:
        base = f"{base}|{objet_lien(paquet)}"
    return hashlib.sha256(base.encode()).hexdigest()


def verify_ed(pub, message, sig) -> bool:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    try:
        Ed25519PublicKey.from_public_bytes(b64d(pub)).verify(b64d(sig), message)
        return True
    except (InvalidSignature, ValueError):
        return False


def verify_ml(pub, message, sig) -> bool:
    try:
        from cryptography.hazmat.primitives.asymmetric.mldsa import MLDSA65PublicKey
    except ImportError as e:
        raise ImportError(MLDSA_MISSING) from e
    from cryptography.exceptions import InvalidSignature
    try:
        MLDSA65PublicKey.from_public_bytes(b64d(pub)).verify(b64d(sig), message)
        return True
    except (InvalidSignature, ValueError):
        return False


def verify_sig(paquet, message) -> tuple[bool, str | None]:
    sig = paquet.get("signature") or ""
    ed_pub = paquet.get("card_public") or ""
    if not sig.startswith(HY):
        return verify_ed(ed_pub, message, sig), None
    try:
        _p, reste = sig.split(":", 1)
        ed_sig, ml_sig = reste.split(":", 1)
    except ValueError:
        return False, None
    ed_ok = verify_ed(ed_pub, message, ed_sig)
    try:
        ml_ok = verify_ml(paquet.get("card_public_pq") or "", message, ml_sig)
    except ImportError as e:
        return False, str(e)
    return bool(ed_ok and ml_ok), None


def lire_quelle(chemin: Path) -> dict:
    carte = json.loads(chemin.read_text(encoding="utf-8"))
    if carte.get("format") != QUELLE_FMT:
        return {"ok": False, "erreur": "pas quelle.v0"}
    src = carte.get("source")
    if src not in {"os", "qrng", "qkd"}:
        return {"ok": False, "erreur": "source os|qrng|qkd"}
    mensonge = src != "os" and not carte.get("appareil") and not carte.get("simule")
    return {
        "ok": not mensonge,
        "source": src,
        "simule": bool(carte.get("simule")),
        "id": carte.get("id"),
        "note": "carte mensongère : qrng/qkd sans appareil" if mensonge else "lue. pas signée ici.",
    }


def lire_horizon(chemin: Path) -> dict:
    carte = json.loads(chemin.read_text(encoding="utf-8"))
    if carte.get("format") != HORIZON_FMT:
        return {"ok": False, "erreur": "pas horizon.v0"}
    suite = carte.get("suite")
    if suite not in SUITES:
        return {"ok": False, "erreur": "suite inconnue"}
    jour_s = carte.get("re_presser_avant")
    if not jour_s:
        return {"ok": False, "erreur": "pas de date"}
    try:
        jour = date.fromisoformat(jour_s)
    except ValueError:
        return {"ok": False, "erreur": "date illisible"}
    reste = (jour - datetime.now(timezone.utc).date()).days
    if suite == "UFHY1":
        courbe = "Ed25519 + ML-DSA-65"
    elif suite == "mldsa87":
        courbe = "ML-DSA-87 (QUANTUM v0 ne signe pas)"
    else:
        courbe = "Ed25519"
    if reste < 0:
        return {
            "ok": False,
            "suite": suite,
            "courbe": courbe,
            "re_presser_avant": jour_s,
            "jours_restants": reste,
            "note": "périmé. le sceau n'est pas faux. resseller.",
        }
    return {
        "ok": True,
        "suite": suite,
        "courbe": courbe,
        "re_presser_avant": jour_s,
        "jours_restants": reste,
        "note": "lue. pas signée ici.",
    }


def phrase_check(rec: dict) -> str:
    err = rec.get("erreur")
    if err == "format":
        return "pas UNFORGE-PREUVE-v1 ou v2."
    if err == "format-v1":
        return "v1 tient mais n'inclut pas objet. resseller en v2."
    if err == "cette preuve ne constate pas un fichier":
        return "cette carte ne constate pas un fichier."
    if err == "preuve introuvable":
        return "aucune carte à côté du fichier."
    if err == "fichier introuvable":
        return "fichier introuvable."
    if err == "json":
        return "JSON illisible."
    crypto = rec.get("crypto")
    if isinstance(crypto, dict) and crypto.get("erreur"):
        return str(crypto["erreur"])
    if rec.get("empreinte_ok") is False:
        base = "l'empreinte ne tient pas."
    elif rec.get("signature_ok") is False:
        base = "la signature ne tient pas."
    elif rec.get("fichier_ok") is False:
        base = "le fichier ne correspond pas à la carte."
    elif rec.get("ok") and rec.get("fichier_ok") is None:
        base = "la carte tient. aucun fichier présenté."
    elif rec.get("ok"):
        base = "le fichier correspond à la carte."
    elif err:
        base = str(err)
    else:
        base = "refus."
    extras: list[str] = []
    quelle = rec.get("quelle")
    if isinstance(quelle, dict) and quelle.get("ok") is False:
        extras.append(quelle.get("note") or quelle.get("erreur") or "quelle refusée.")
    horizon = rec.get("horizon")
    if isinstance(horizon, dict) and horizon.get("ok") is False:
        extras.append(horizon.get("note") or horizon.get("erreur") or "horizon périmé. resseller.")
    return " ".join([base, *extras])


def habiller(rec: dict) -> dict:
    rec.setdefault("geste", "check")
    rec.setdefault("marque", "UNFORGE")
    rec.setdefault("noeud", "non requis")
    rec.setdefault("schema", SCHEMA_ID)
    rec["phrase"] = phrase_check(rec)
    return rec


def check_paquet(paquet: dict, fichier: Path | None) -> dict:
    version = format_version(paquet)
    if version is None:
        return habiller({"ok": False, "erreur": "format"})
    emp_ok = empreinte(paquet, version) == paquet.get("empreinte")
    sig_ok, sig_note = verify_sig(paquet, materiau(paquet))
    fichier_ok = None
    sha = None
    sha_attendu = None
    octets = None
    octets_attendus = None
    if fichier is not None:
        brut = fichier.read_bytes()
        sha = hashlib.sha256(brut).hexdigest()
        octets = len(brut)
        objet = paquet.get("objet") or {}
        sha_attendu = objet.get("sha256")
        octets_attendus = objet.get("octets")
        if not sha_attendu:
            return habiller({"ok": False, "erreur": "cette preuve ne constate pas un fichier"})
        fichier_ok = sha == sha_attendu and objet.get("octets") in (None, octets)
    crypto = None
    if sig_note:
        crypto = {"ok": False, "erreur": sig_note}
        sig_ok = False
    legacy = version == 1
    if legacy:
        # Dual check: v1 crypto is still evaluated so a presser can see the card.
        # It is never a file seal — objet is not in the material. Exit 1.
        tient_v1 = bool(emp_ok and sig_ok and fichier_ok is not False)
        rec = {
            "ok": False,
            "empreinte_ok": emp_ok,
            "signature_ok": sig_ok,
            "fichier_ok": fichier_ok,
            "sha256": sha,
            "id": paquet.get("id"),
            "card_id": paquet.get("card_id"),
            "marque": "UNFORGE",
            "noeud": "non requis",
            "format": FORMAT_V1,
            "format_version": 1,
            "legacy": True,
            "preuve": {
                "ok": False,
                "format": FORMAT_V1,
                "note": "v1 n'inclut pas objet dans l'empreinte. resseller en v2.",
            },
        }
        if tient_v1:
            rec["erreur"] = "format-v1"
    else:
        rec = {
            "ok": bool(emp_ok and sig_ok and fichier_ok is not False),
            "empreinte_ok": emp_ok,
            "signature_ok": sig_ok,
            "fichier_ok": fichier_ok,
            "sha256": sha,
            "id": paquet.get("id"),
            "card_id": paquet.get("card_id"),
            "marque": "UNFORGE",
            "noeud": "non requis",
            "format": FORMAT_V2,
            "format_version": 2,
            "legacy": False,
        }
    if sha_attendu is not None:
        rec["sha256_attendu"] = sha_attendu
    if octets is not None:
        rec["octets"] = octets
    if octets_attendus is not None:
        rec["octets_attendus"] = octets_attendus
    if crypto is not None:
        rec["crypto"] = crypto
    return habiller(rec)


def check(preuve: Path, fichier: Path | None) -> dict:
    """Verify a card. Optional file. Never signs. Agents: this is the hook."""
    paquet = json.loads(preuve.read_text(encoding="utf-8"))
    return check_paquet(paquet, fichier)


def verifier(
    preuve: Path,
    fichier: Path | None = None,
    quelle: Path | None = None,
    horizon: Path | None = None,
) -> dict:
    """One call for other agents and tools. Local. No server. Does not sign."""
    rec = check(preuve, fichier)
    if quelle is not None:
        rec["quelle"] = lire_quelle(quelle)
    if horizon is not None:
        rec["horizon"] = lire_horizon(horizon)
    rec["phrase"] = phrase_check(rec)
    return rec


def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def satellites_ok(rec: dict) -> bool:
    for cle in ("quelle", "horizon", "preuve"):
        if cle in rec and rec[cle].get("ok") is False:
            return False
    return True


def code_sortie(rec: dict) -> int:
    return 0 if rec.get("ok") and satellites_ok(rec) else 1


def voisin_carte(fichier: Path) -> Path:
    return Path(str(fichier) + ".unforge.json")


def resoudre(chemins: list[Path]) -> tuple[Path, Path | None]:
    """Pick the card and the optional file. One path may be the file alone."""
    if len(chemins) == 1:
        seul = chemins[0]
        if seul.name.endswith(".unforge.json"):
            return seul, None
        carte = voisin_carte(seul)
        if carte.is_file():
            return carte, seul
        raise FileNotFoundError("preuve introuvable")
    preuve = next((c for c in chemins if c.name.endswith(".unforge.json")), chemins[-1])
    fichier = next((c for c in chemins if c != preuve), None)
    return preuve, fichier


def _colorer() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stderr.isatty() or sys.stdout.isatty()


def ligne_verdict(rec: dict, color: bool) -> str:
    fichier_tient = rec.get("ok") is True
    sat = satellites_ok(rec)
    legacy_lu = (
        rec.get("legacy") is True
        and rec.get("empreinte_ok") is True
        and rec.get("signature_ok") is True
        and rec.get("fichier_ok") is not False
    )
    if fichier_tient and sat:
        mot, teinte = "VERT", VERT
    elif (fichier_tient and not sat) or legacy_lu:
        mot, teinte = "AMBRE", AMBRE
    else:
        mot, teinte = "ROUGE", ROUGE
    if color:
        mot = f"{teinte}{mot}{RESET}"
    return f"{mot}  {rec.get('phrase')}"


def lignes_humaines(rec: dict, color: bool) -> list[str]:
    lignes = [ligne_verdict(rec, color)]
    ident = rec.get("id")
    carte = rec.get("card_id")
    if ident or carte:
        lignes.append(f"      {' · '.join(x for x in (ident, carte) if x)}")
    if rec.get("fichier_ok") is False:
        if rec.get("sha256"):
            lignes.append(f"      obtenu  {rec['sha256']}")
        if rec.get("sha256_attendu"):
            lignes.append(f"      carte   {rec['sha256_attendu']}")
    elif rec.get("sha256"):
        lignes.append(f"      sha256 {rec['sha256']}")
    if rec.get("format"):
        lignes.append(f"      format {rec['format']}")
    return lignes


def imprimer_humain(rec: dict, dest) -> None:
    color = dest.isatty() and not os.environ.get("NO_COLOR")
    dest.write("\n".join(lignes_humaines(rec, color)) + "\n")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="check.py",
        description="UNFORGE Check — see whether a file matches the card. Public eye, not a seal. No node. No cloud. No coin. Does not sign.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  python3 check.py document.pdf\n"
            "  python3 check.py document.pdf document.pdf.unforge.json\n"
            "  python3 check.py document.pdf document.pdf.unforge.json --human\n"
            "\n"
            "If the card path is omitted, Check looks for FILE.unforge.json beside the file.\n"
            "Exit 0 = match. Exit 1 = refuse. Exit 2 = unreadable.\n"
            "ok: true is the only pass for the file. A dead horizon is re-press, not a forged file.\n"
            "UNFORGE-PREUVE-v1 is read (dual check) but never VERT — resseller en v2.\n"
            "Agents: python3 check.py --schema   or   from check import verifier"
        ),
    )
    p.add_argument(
        "paths",
        nargs="*",
        metavar="FILE",
        help="file to check, and/or its .unforge.json card",
    )
    p.add_argument("--quelle", default=None, help="carte .quelle.json à lire (ne signe pas)")
    p.add_argument("--horizon", default=None, help="fiche .horizon.json à lire (ne signe pas)")
    p.add_argument("--schema", action="store_true", help="print check.v0 JSON Schema and exit")
    sortie = p.add_mutually_exclusive_group()
    sortie.add_argument("--json", action="store_true", help="machine record on stdout (default)")
    sortie.add_argument(
        "--human",
        action="store_true",
        help="VERT = match (file ↔ card) · ROUGE = refuse · AMBRE = dead satellite or v1",
    )
    p.add_argument("--quiet", "-q", action="store_true", help="no stderr hint")
    args = p.parse_args(argv)

    if args.schema:
        try:
            print(json.dumps(schema(), ensure_ascii=False, indent=2))
        except Exception as e:
            print(json.dumps({"ok": False, "erreur": str(e)}, ensure_ascii=False, indent=2))
            return 2
        return 0

    if not args.paths:
        p.error("drop a file, or a file and its .unforge.json")

    chemins = [Path(x) for x in args.paths]
    try:
        preuve, fichier = resoudre(chemins)
        if not preuve.is_file():
            rec = habiller({"ok": False, "erreur": "preuve introuvable", "attendu": str(preuve)})
            print(json.dumps(rec, ensure_ascii=False, indent=2))
            return 2
        if fichier is not None and not fichier.is_file():
            rec = habiller({"ok": False, "erreur": "fichier introuvable", "attendu": str(fichier)})
            print(json.dumps(rec, ensure_ascii=False, indent=2))
            return 2
        rec = verifier(
            preuve,
            fichier,
            Path(args.quelle) if args.quelle else None,
            Path(args.horizon) if args.horizon else None,
        )
    except FileNotFoundError:
        attendu = str(voisin_carte(chemins[0])) if chemins else None
        rec = habiller({"ok": False, "erreur": "preuve introuvable", "attendu": attendu})
        print(json.dumps(rec, ensure_ascii=False, indent=2))
        return 2
    except json.JSONDecodeError as e:
        rec = habiller({"ok": False, "erreur": "json", "detail": str(e)})
        print(json.dumps(rec, ensure_ascii=False, indent=2))
        return 2
    except Exception as e:
        rec = habiller({"ok": False, "erreur": str(e)})
        print(json.dumps(rec, ensure_ascii=False, indent=2))
        return 2

    if args.human:
        imprimer_humain(rec, sys.stdout)
    else:
        print(json.dumps(rec, ensure_ascii=False, indent=2))
        if not args.quiet and not args.json and sys.stderr.isatty():
            imprimer_humain(rec, sys.stderr)

    return code_sortie(rec)


if __name__ == "__main__":
    raise SystemExit(main())
