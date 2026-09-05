#!/usr/bin/env python3
"""UNFORGE Trail — vérifier une chaîne de constats, hors coffre.

empreinte() is imported from check.py. Each maillon uses the formula of
its own format (v1 or v2). v2 binds objet.sha256|objet.octets.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

from check import empreinte

FORMAT = "UNFORGE-TRAIL-v1"


def choisir_trail(chemins: list[Path]) -> Path:
    """Pick the itinerary by suffix first. Do not match substring 'trail'."""
    for c in chemins:
        if c.name.endswith(".unforge-trail.json"):
            return c
    return chemins[0]


def _prev(m: dict) -> str:
    return m.get("prev") or ""


def verifier(trail: Path, fichier: Path | None) -> dict:
    paquet = json.loads(trail.read_text(encoding="utf-8"))
    if paquet.get("format") != FORMAT:
        return {"ok": False, "erreur": "format", "attendu": FORMAT}
    maillons = paquet.get("maillons") or []
    if not maillons:
        return {"ok": False, "erreur": "chaîne vide"}
    recs = []
    ok = True
    derniere = ""
    for i, m in enumerate(maillons):
        lie = _prev(m) == derniere
        emp_ok = empreinte(m) == m.get("empreinte")
        fichier_ok = None
        sha = None
        if fichier is not None and i == len(maillons) - 1:
            brut = fichier.read_bytes()
            sha = __import__("hashlib").sha256(brut).hexdigest()
            attendu = (m.get("objet") or {}).get("sha256")
            fichier_ok = bool(attendu) and sha == attendu
        maillon_ok = bool(emp_ok and lie and fichier_ok is not False)
        if not maillon_ok:
            ok = False
        recs.append({
            "id": m.get("id"),
            "empreinte": m.get("empreinte"),
            "lie": lie,
            "empreinte_ok": emp_ok,
            "fichier_ok": fichier_ok,
            "ok": maillon_ok,
        })
        derniere = m.get("empreinte") or ""
    feuille_sha = None
    if fichier is not None:
        feuille_sha = __import__("hashlib").sha256(fichier.read_bytes()).hexdigest()
    return {
        "ok": ok,
        "geste": "trail",
        "format": FORMAT,
        "marque": paquet.get("marque") or "UNFORGE",
        "n": len(maillons),
        "feuille": recs[-1]["id"] if recs else None,
        "sha256": feuille_sha,
        "maillons": recs,
        "noeud": "non requis",
        "phrase": "Trail compare les SHA. Check ouvre les signatures.",
    }


def main() -> int:
    p = argparse.ArgumentParser(description="UNFORGE Trail")
    p.add_argument("paths", nargs="+")
    args = p.parse_args()
    chemins = [Path(x) for x in args.paths]
    trail = choisir_trail(chemins)
    fichier = next((c for c in chemins if c != trail), None)
    try:
        rec = verifier(trail, fichier)
    except Exception as e:
        print(json.dumps({"ok": False, "erreur": str(e)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(rec, ensure_ascii=False, indent=2))
    return 0 if rec.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
