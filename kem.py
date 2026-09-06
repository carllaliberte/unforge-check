#!/usr/bin/env python3
"""KEM v0 — declare an opt-in encapsulation suite. Does not encapsulate.

Not Check. Not HORIZON. Not UFHY1 (signatures only).
Never default. QUANTUM is not this process.
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

try:
    import fcntl
except ImportError:
    fcntl = None  # type: ignore  # Windows: no flock. Documented, not a silent seal.

FORMAT = "kem.v0"
SUITES = ("x25519", "mlkem768", "x25519mlkem768")
SIGNATURE_SUITES = ("UFHY1", "ed25519", "mldsa87")
MENACE = "harvest-now-decrypt-later"
HYPOTHESES = {
    "x25519": "Shor n'existe pas encore à cette taille",
    "mlkem768": "ML-KEM-768 (FIPS 203) tient contre un adversaire harvest-now-decrypt-later",
    "x25519mlkem768": "AND aujourd'hui (X25519 et ML-KEM-768) ; OR plus tard contre harvest-now-decrypt-later",
}
SLOGANS = (
    "quantum-safe",
    "quantum safe",
    "post-quantum-safe",
    "pqc par défaut",
    "pqc par defaut",
)


def _lock(path: Path):
    lock_path = path.with_suffix(path.suffix + ".lock")
    fh = open(lock_path, "a+", encoding="utf-8")
    if fcntl is not None:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
    return fh


def _unlock(fh) -> None:
    if fcntl is not None:
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
    fh.close()


def _ecrire_json(chemin: Path, objet: dict) -> None:
    fh = _lock(chemin)
    try:
        chemin.write_text(json.dumps(objet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    finally:
        _unlock(fh)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _est_slogan(s: str) -> bool:
    n = " ".join((s or "").strip().lower().replace("_", " ").replace("-", " ").split())
    return n in {x.replace("-", " ") for x in SLOGANS} or "quantum safe" in n


def ecrire(suite: str, opt_in: bool, cible: str | None = None) -> dict:
    if opt_in is not True:
        raise SystemExit("refus : pas par défaut. --opt-in explicite.")
    suite = (suite or "").strip()
    if _est_slogan(suite):
        raise SystemExit("refus : slogan, pas une suite. jamais quantum-safe.")
    if suite in SIGNATURE_SUITES:
        raise SystemExit(
            "refus : UFHY1 = Ed25519 + ML-DSA-65 (signatures). Pas un KEM."
        )
    if suite not in SUITES:
        raise SystemExit("suite : x25519 | mlkem768 | x25519mlkem768")
    return {
        "format": FORMAT,
        "kem_id": "KM-" + uuid.uuid4().hex[:12],
        "suite": suite,
        "opt_in": True,
        "menace": MENACE,
        "hypothese": HYPOTHESES[suite],
        "ciphertext": None,
        "pose_at": _now(),
        "revocable": True,
        "cible": cible or None,
        "note": "v0. déclare. n'encapsule pas. pas par défaut.",
    }


def lire(chemin: str) -> dict:
    p = Path(chemin).expanduser()
    carte = json.loads(p.read_text(encoding="utf-8"))
    if carte.get("format") != FORMAT:
        raise SystemExit("pas une fiche kem.v0")
    suite = carte.get("suite") or ""
    if _est_slogan(str(suite)):
        raise SystemExit("refus : slogan, pas une suite. jamais quantum-safe.")
    if suite in SIGNATURE_SUITES:
        raise SystemExit(
            "refus : UFHY1 = Ed25519 + ML-DSA-65 (signatures). Pas un KEM."
        )
    if suite not in SUITES:
        raise SystemExit("suite inconnue")
    if carte.get("opt_in") is not True:
        raise SystemExit("refus : pas par défaut")
    return carte


def juger(carte: dict) -> dict:
    if carte.get("opt_in") is not True:
        return {
            "decision": "deny",
            "flag": "kem",
            "note": "pas par défaut. opt-in explicite requis.",
        }
    suite = carte.get("suite") or ""
    if _est_slogan(str(suite)) or suite in SIGNATURE_SUITES or suite not in SUITES:
        return {
            "decision": "deny",
            "flag": "kem",
            "suite": suite,
            "note": "suite refusée. UFHY1 n'est pas un KEM. pas de slogan.",
        }
    if carte.get("ciphertext") is not None:
        return {
            "decision": "deny",
            "flag": "kem",
            "suite": suite,
            "note": "v0 déclare. ciphertext doit rester null. encapsulage ailleurs.",
        }
    if carte.get("menace") != MENACE:
        return {
            "decision": "deny",
            "flag": "kem",
            "note": "menace : harvest-now-decrypt-later (modèle, pas un produit).",
        }
    dumped = json.dumps(carte, ensure_ascii=False)
    if "QUANTUM" in dumped or "quantique" in dumped.lower():
        return {
            "decision": "deny",
            "flag": "kem",
            "note": "pas un sceau. pas quantique frappé ici.",
        }
    return {
        "decision": "allow",
        "flag": "kem",
        "suite": suite,
        "opt_in": True,
        "ciphertext": None,
        "note": "déclaré, opt-in. n'encapsule pas. Check ne lit pas cette fiche.",
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="kem.py",
        description="KEM v0 — opt-in encapsulation declaration. Never default. Does not encapsulate.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    pe = sub.add_parser("ecrire")
    pe.add_argument("--suite", required=True)
    pe.add_argument(
        "--opt-in",
        action="store_true",
        help="required. without this flag the write is refused.",
    )
    pe.add_argument("--cible", default=None)
    pe.add_argument("--vers", default="carte.kem.json")
    pl = sub.add_parser("lire")
    pl.add_argument("fichier")
    pj = sub.add_parser("juger")
    pj.add_argument("fichier")
    args = p.parse_args(argv)
    if args.cmd == "ecrire":
        carte = ecrire(suite=args.suite, opt_in=bool(args.opt_in), cible=args.cible)
        _ecrire_json(Path(args.vers), carte)
        out = dict(carte)
        out["fichier"] = args.vers
        print(json.dumps(out, ensure_ascii=False, indent=2))
    elif args.cmd == "lire":
        print(json.dumps(lire(args.fichier), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(juger(lire(args.fichier)), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
