#!/usr/bin/env python3
"""UNFORGE Check — verify a .unforge.json against an optional file.
Optional: read a QUELLE card and an HORIZON card. Does not sign.
"""
from __future__ import annotations
import argparse, base64, hashlib, json
from datetime import date, datetime, timezone
from pathlib import Path

FORMAT = "UNFORGE-PREUVE-v1"
HY = "UFHY1:"
QUELLE_FMT = "quelle.v0"
HORIZON_FMT = "horizon.v0"
SUITES = ("ed25519", "UFHY1", "mldsa87")


def b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def materiau(paquet: dict) -> bytes:
    return f"{paquet.get('card_id') or ''}|{paquet.get('token_id') or ''}|REGISTRE|{paquet.get('empreinte') or ''}".encode()


def empreinte(paquet: dict) -> str:
    return hashlib.sha256(f"{paquet.get('fait') or ''}|{paquet.get('prev') or ''}|{paquet.get('token_id') or ''}".encode()).hexdigest()


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
        MLDSA65PublicKey.from_public_bytes(b64d(pub)).verify(b64d(sig), message)
        return True
    except Exception:
        return False


def verify_sig(paquet, message) -> bool:
    sig = paquet.get("signature") or ""
    ed_pub = paquet.get("card_public") or ""
    if not sig.startswith(HY):
        return verify_ed(ed_pub, message, sig)
    try:
        _p, reste = sig.split(":", 1)
        ed_sig, ml_sig = reste.split(":", 1)
    except ValueError:
        return False
    return verify_ed(ed_pub, message, ed_sig) and verify_ml(paquet.get("card_public_pq") or "", message, ml_sig)


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


def check_paquet(paquet: dict, fichier: Path | None) -> dict:
    if paquet.get("format") != FORMAT:
        return {"ok": False, "erreur": "format"}
    emp_ok = empreinte(paquet) == paquet.get("empreinte")
    sig_ok = verify_sig(paquet, materiau(paquet))
    fichier_ok = None
    sha = None
    if fichier is not None:
        brut = fichier.read_bytes()
        sha = hashlib.sha256(brut).hexdigest()
        objet = paquet.get("objet") or {}
        attendu = objet.get("sha256")
        if not attendu:
            return {"ok": False, "erreur": "cette preuve ne constate pas un fichier"}
        fichier_ok = sha == attendu and objet.get("octets") in (None, len(brut))
    ok = bool(emp_ok and sig_ok and fichier_ok is not False)
    return {
        "ok": ok,
        "empreinte_ok": emp_ok,
        "signature_ok": sig_ok,
        "fichier_ok": fichier_ok,
        "sha256": sha,
        "id": paquet.get("id"),
        "card_id": paquet.get("card_id"),
        "marque": "UNFORGE",
        "noeud": "non requis",
    }


def check(preuve: Path, fichier: Path | None) -> dict:
    paquet = json.loads(preuve.read_text(encoding="utf-8"))
    return check_paquet(paquet, fichier)


def main() -> int:
    p = argparse.ArgumentParser(description="UNFORGE Check")
    p.add_argument("paths", nargs="+")
    p.add_argument("--quelle", default=None, help="carte .quelle.json à lire (ne signe pas)")
    p.add_argument("--horizon", default=None, help="fiche .horizon.json à lire (ne signe pas)")
    args = p.parse_args()
    chemins = [Path(x) for x in args.paths]
    preuve = next((c for c in chemins if c.name.endswith(".unforge.json")), chemins[-1])
    fichier = next((c for c in chemins if c != preuve), None)
    try:
        rec = check(preuve, fichier)
        if args.quelle:
            rec["quelle"] = lire_quelle(Path(args.quelle))
        if args.horizon:
            rec["horizon"] = lire_horizon(Path(args.horizon))
    except Exception as e:
        print(json.dumps({"ok": False, "erreur": str(e)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(rec, ensure_ascii=False, indent=2))
    preuve_ok = rec.get("ok")
    sat_ok = True
    if "quelle" in rec:
        sat_ok = sat_ok and rec["quelle"].get("ok") is not False
    if "horizon" in rec:
        sat_ok = sat_ok and rec["horizon"].get("ok") is not False
    return 0 if preuve_ok and sat_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
