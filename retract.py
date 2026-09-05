#!/usr/bin/env python3
"""UNFORGE Retract — brouillon public. Vérif hors coffre. Ne signe pas."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

from check import FORMAT_V1, FORMAT_V2, verify_sig

FORMAT = "UNFORGE-RETRAIT-v1"
PREUVES = {FORMAT_V1, FORMAT_V2}


def materiau_retrait(paquet: dict) -> str:
    return f"RETRAIT|{paquet.get('id') or paquet.get('preuve_id') or ''}|{paquet.get('card_id') or ''}|{paquet.get('empreinte') or ''}"


def brouillon(preuve: Path) -> dict:
    p = json.loads(preuve.read_text(encoding="utf-8"))
    if p.get("format") not in PREUVES:
        raise ValueError("format preuve refusé")
    rec = {
        "format": FORMAT,
        "marque": "UNFORGE",
        "preuve_id": p.get("id"),
        "card_id": p.get("card_id"),
        "card_label": p.get("card_label"),
        "card_public": p.get("card_public"),
        "card_public_pq": p.get("card_public_pq"),
        "token_id": p.get("token_id"),
        "empreinte": p.get("empreinte"),
        "materiau": materiau_retrait(p),
        "signature": None,
        "phrase": "Autre matière. Même carte. Ne signe pas ici.",
    }
    return rec


def verifier(preuve: Path, retrait: Path) -> dict:
    p = json.loads(preuve.read_text(encoding="utf-8"))
    r = json.loads(retrait.read_text(encoding="utf-8"))
    if p.get("format") not in PREUVES:
        return {"ok": False, "erreur": "format preuve"}
    if r.get("format") != FORMAT:
        return {"ok": False, "erreur": "format retrait"}
    memes = (
        p.get("id") == r.get("preuve_id")
        and p.get("card_id") == r.get("card_id")
        and p.get("token_id") == r.get("token_id")
        and p.get("empreinte") == r.get("empreinte")
        and p.get("card_public") == r.get("card_public")
    )
    attendu = materiau_retrait(p)
    mat_ok = (r.get("materiau") or "") == attendu
    sig_raw = r.get("signature") or ""
    fake = {
        "card_public": r.get("card_public"),
        "card_public_pq": r.get("card_public_pq") or p.get("card_public_pq"),
        "signature": sig_raw,
    }
    ok_sig, note = verify_sig(fake, attendu.encode())
    sig_ok = bool(sig_raw) and bool(ok_sig)
    ok = bool(memes and mat_ok and sig_ok)
    rec = {
        "ok": ok,
        "geste": "retrait-verifier",
        "preuve_id": p.get("id"),
        "memes": memes,
        "materiau_ok": mat_ok,
        "signature_ok": sig_ok,
        "materiau": attendu,
        "noeud": "non requis",
        "phrase": "Retrait valable." if ok else "Retrait refusé.",
    }
    if not sig_raw:
        rec["erreur"] = "signature absente"
    if note:
        rec["note"] = note
    return rec


def main() -> int:
    p = argparse.ArgumentParser(description="UNFORGE Retract")
    sub = p.add_subparsers(dest="cmd", required=True)
    pb = sub.add_parser("brouillon")
    pb.add_argument("preuve")
    pv = sub.add_parser("verifier")
    pv.add_argument("preuve")
    pv.add_argument("retrait")
    args = p.parse_args()
    try:
        if args.cmd == "brouillon":
            rec = brouillon(Path(args.preuve))
            print(json.dumps(rec, ensure_ascii=False, indent=2))
            return 0
        rec = verifier(Path(args.preuve), Path(args.retrait))
        print(json.dumps(rec, ensure_ascii=False, indent=2))
        return 0 if rec.get("ok") else 1
    except Exception as e:
        print(json.dumps({"ok": False, "erreur": str(e)}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main())
