#!/usr/bin/env python3
"""UNFORGE Press (wrapper) — prints ids. Does not open the signature.

The printer lives in carllaliberte/unforge-press. This file only reads
UNFORGE-PREUVE-v1 / v2 and emits the id sheet. v1 never claims a file match.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

FORMAT_V1 = "UNFORGE-PREUVE-v1"
FORMAT_V2 = "UNFORGE-PREUVE-v2"
FORMATS = {FORMAT_V1, FORMAT_V2}


def feuille(preuve: Path) -> dict:
    paquet = json.loads(preuve.read_text(encoding="utf-8"))
    fmt = paquet.get("format")
    objet = paquet.get("objet") or {}
    ok = fmt in FORMATS
    v1 = fmt == FORMAT_V1
    if not ok:
        phrase = "pas UNFORGE-PREUVE-v1/v2. Imprimeur = repo unforge-press."
    elif v1:
        phrase = "v1 n'inclut pas objet — resseller v2. Press n'ouvre pas la signature."
    else:
        phrase = "Press n'ouvre pas la signature. Check le fait."
    rec = {
        "ok": ok,
        "geste": "press",
        "marque": paquet.get("marque") or "UNFORGE",
        "format": fmt,
        "legacy": v1 if ok else False,
        "id": paquet.get("id"),
        "carte": paquet.get("card_id"),
        "label": paquet.get("card_label"),
        "token": paquet.get("token_id"),
        "objet": objet.get("nom"),
        "empreinte": paquet.get("empreinte"),
        "algo": paquet.get("signature_algos") or "ed25519",
        "created_at": paquet.get("created_at"),
        "imprimeur": "unforge-press",
        "noeud": "non requis",
        "phrase": phrase,
    }
    if not ok:
        rec["erreur"] = "format"
    return rec


def main() -> int:
    p = argparse.ArgumentParser(description="UNFORGE Press — ids only. Printer = unforge-press.")
    p.add_argument("preuve")
    args = p.parse_args()
    preuve = Path(args.preuve)
    if not preuve.is_file():
        print(json.dumps({"ok": False, "erreur": "preuve introuvable"}, ensure_ascii=False, indent=2))
        return 2
    try:
        rec = feuille(preuve)
    except Exception as e:
        print(json.dumps({"ok": False, "erreur": str(e)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(rec, ensure_ascii=False, indent=2))
    return 0 if rec.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
