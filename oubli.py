#!/usr/bin/env python3
"""UNFORGE Oubli — sha256 then local unlink. Does not sign. Git does not erase."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

FORMAT = "UNFORGE-OUBLI-v1"
PHRASE = "Git ne s'efface pas. Oubli = unlink local après sha256."


def sha256_fichier(chemin: Path) -> tuple[str, int]:
    brut = chemin.read_bytes()
    return hashlib.sha256(brut).hexdigest(), len(brut)


def brouillon(fichier: Path) -> dict:
    if not fichier.is_file():
        raise FileNotFoundError("fichier introuvable")
    sha, octets = sha256_fichier(fichier)
    return {
        "format": FORMAT,
        "marque": "UNFORGE",
        "geste": "oubli",
        "chemin": str(fichier),
        "nom": fichier.name,
        "octets": octets,
        "sha256": sha,
        "applique": False,
        "phrase": PHRASE,
        "note": "Brouillon. Unforge ne signe pas. Pas de token d'oubli. Pas de photon. Pas un wipe cloud.",
    }


def lire(oubli: Path) -> dict:
    paquet = json.loads(oubli.read_text(encoding="utf-8"))
    if paquet.get("format") != FORMAT:
        return {
            "ok": False,
            "geste": "oubli-lire",
            "erreur": "format",
            "attendu": FORMAT,
            "phrase": "pas UNFORGE-OUBLI-v1.",
        }
    return {
        "ok": True,
        "geste": "oubli-lire",
        "format": FORMAT,
        "marque": paquet.get("marque") or "UNFORGE",
        "chemin": paquet.get("chemin"),
        "nom": paquet.get("nom"),
        "octets": paquet.get("octets"),
        "sha256": paquet.get("sha256"),
        "applique": bool(paquet.get("applique")),
        "noeud": "non requis",
        "phrase": paquet.get("phrase") or PHRASE,
    }


def appliquer(fichier: Path, oubli: Path) -> dict:
    paquet = json.loads(oubli.read_text(encoding="utf-8"))
    if paquet.get("format") != FORMAT:
        return {
            "ok": False,
            "geste": "oubli-appliquer",
            "erreur": "format",
            "attendu": FORMAT,
            "phrase": "pas UNFORGE-OUBLI-v1.",
        }
    if not fichier.is_file():
        return {
            "ok": False,
            "geste": "oubli-appliquer",
            "erreur": "fichier introuvable",
            "phrase": "le fichier n'est plus là.",
        }
    sha, octets = sha256_fichier(fichier)
    attendu = paquet.get("sha256") or ""
    if not attendu or sha != attendu:
        return {
            "ok": False,
            "geste": "oubli-appliquer",
            "erreur": "hash bougé",
            "sha256": sha,
            "sha256_attendu": attendu,
            "unlinked": False,
            "noeud": "non requis",
            "phrase": "hash bougé. refus. le fichier reste.",
        }
    fichier.unlink()
    return {
        "ok": True,
        "geste": "oubli-appliquer",
        "format": FORMAT,
        "marque": "UNFORGE",
        "chemin": str(fichier),
        "sha256": sha,
        "octets": octets,
        "unlinked": True,
        "noeud": "non requis",
        "phrase": "sha256 tenu. unlink local. Git ne s'efface pas.",
    }


def main() -> int:
    p = argparse.ArgumentParser(description="UNFORGE Oubli — unlink local après sha256. Ne signe pas.")
    sub = p.add_subparsers(dest="cmd", required=True)
    pb = sub.add_parser("brouillon")
    pb.add_argument("fichier")
    pb.add_argument("--vers", required=True)
    pa = sub.add_parser("appliquer")
    pa.add_argument("fichier")
    pa.add_argument("oubli")
    pl = sub.add_parser("lire")
    pl.add_argument("oubli")
    args = p.parse_args()
    try:
        if args.cmd == "brouillon":
            rec = brouillon(Path(args.fichier))
            dest = Path(args.vers)
            dest.write_text(json.dumps(rec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(rec, ensure_ascii=False, indent=2))
            return 0
        if args.cmd == "lire":
            rec = lire(Path(args.oubli))
            print(json.dumps(rec, ensure_ascii=False, indent=2))
            return 0 if rec.get("ok") else 1
        rec = appliquer(Path(args.fichier), Path(args.oubli))
        print(json.dumps(rec, ensure_ascii=False, indent=2))
        return 0 if rec.get("ok") else 1
    except FileNotFoundError as e:
        print(json.dumps({"ok": False, "erreur": str(e)}, ensure_ascii=False, indent=2))
        return 2
    except Exception as e:
        print(json.dumps({"ok": False, "erreur": str(e)}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main())
