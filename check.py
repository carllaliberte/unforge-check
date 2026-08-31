#!/usr/bin/env python3
"""UNFORGE Check — verify a .unforge.json against an optional file."""
from __future__ import annotations
import argparse, base64, hashlib, json
from pathlib import Path

FORMAT = "UNFORGE-PREUVE-v1"
HY = "UFHY1:"

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
    return {"ok": ok, "empreinte_ok": emp_ok, "signature_ok": sig_ok, "fichier_ok": fichier_ok, "sha256": sha, "id": paquet.get("id"), "card_id": paquet.get("card_id"), "marque": "UNFORGE", "noeud": "non requis"}

def check(preuve: Path, fichier: Path | None) -> dict:
    paquet = json.loads(preuve.read_text(encoding="utf-8"))
    return check_paquet(paquet, fichier)

def main() -> int:
    p = argparse.ArgumentParser(description="UNFORGE Check")
    p.add_argument("paths", nargs="+")
    args = p.parse_args()
    chemins = [Path(x) for x in args.paths]
    preuve = next((c for c in chemins if c.name.endswith(".unforge.json")), chemins[-1])
    fichier = next((c for c in chemins if c != preuve), None)
    try:
        rec = check(preuve, fichier)
    except Exception as e:
        print(json.dumps({"ok": False, "erreur": str(e)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(rec, ensure_ascii=False, indent=2))
    return 0 if rec.get("ok") else 1

if __name__ == "__main__":
    raise SystemExit(main())
