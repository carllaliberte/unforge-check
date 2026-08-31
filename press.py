#!/usr/bin/env python3
"""UNFORGE Press — imprime les ids. N'ouvre pas la signature."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path


def feuille(preuve: Path) -> dict:
    paquet = json.loads(preuve.read_text(encoding="utf-8"))
    objet = paquet.get("objet") or {}
    return {
        "ok": paquet.get("format") == "UNFORGE-PREUVE-v1",
        "geste": "press",
        "marque": paquet.get("marque") or "UNFORGE",
        "id": paquet.get("id"),
        "carte": paquet.get("card_id"),
        "label": paquet.get("card_label"),
        "token": paquet.get("token_id"),
        "objet": objet.get("nom"),
        "empreinte": paquet.get("empreinte"),
        "algo": paquet.get("signature_algos") or "ed25519",
        "created_at": paquet.get("created_at"),
        "noeud": "non requis",
        "phrase": "Press n’ouvre pas la signature. Check le fait.",
    }


def main() -> int:
    p = argparse.ArgumentParser(description="UNFORGE Press")
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
