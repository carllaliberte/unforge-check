#!/usr/bin/env python3
"""Contrat UNFORGE Check — fichiers présents + JSON parse. Vert = l'état désiré."""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FICHIERS = (
    "check.py",
    "SPEC.md",
    "action.yml",
    "requirements.txt",
    "LICENSE",
    "INTEROP.md",
    "schema/check.v0.json",
    "tests/test_check.py",
    "examples/bienvenue.txt",
    "examples/bienvenue.txt.unforge.json",
    "examples/constat.yml",
    ".github/workflows/constat.yml",
)


def verifier() -> dict:
    manques = [f for f in FICHIERS if not (ROOT / f).is_file()]
    jsons = []
    erreurs = []
    for p in sorted((ROOT / "examples").glob("*.json")):
        try:
            json.loads(p.read_text(encoding="utf-8"))
            jsons.append(p.name)
        except json.JSONDecodeError as e:
            erreurs.append(f"{p.name}: {e}")
    ok = not manques and not erreurs
    return {
        "ok": ok,
        "geste": "contrat",
        "manques": manques,
        "json": jsons,
        "erreurs": erreurs,
        "phrase": "main est l'état désiré." if ok else "contrat incomplet.",
    }


def main() -> int:
    rec = verifier()
    print(json.dumps(rec, ensure_ascii=False, indent=2))
    return 0 if rec["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
