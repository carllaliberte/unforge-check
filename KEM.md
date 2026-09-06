# KEM v0 — encapsulation opt-in

Rail **nouveau**. Pas Check. Pas HORIZON. Pas une 4e carte juge.

Check (`check.py`) **vérifie** Ed25519 / `UFHY1` (Ed25519 + ML-DSA-65). Il ne signe pas. Il n'encapsule pas.

HORIZON (`horizon.py` `ecrire|lire|juger`) nomme une *hypothèse de sceau* et un jour de calendrier. La menace utile 2026, c'est *harvest-now-decrypt-later* ([epsilon-protocol/PHYSIQUE.md](https://github.com/carllaliberte/epsilon-protocol/blob/main/PHYSIQUE.md)) — un modèle de menace, **pas un nom de produit**.

Ce rail nomme **comment** un acte *peut* encapsuler, si et seulement si l'appelant le demande.

Lu : `check.py` (SUITES, UFHY1, `MLDSA65PublicKey`), [SPEC.md](SPEC.md), [horizon-protocol README](https://github.com/carllaliberte/horizon-protocol/blob/main/README.md), [famille/COUCHES.md](https://github.com/carllaliberte/famille/blob/main/COUCHES.md).

## Primitive

```
opt-in explicite  +  suite KEM  +  menace HNDL  →  fiche .kem.json
```

Sans `--opt-in` : refus. Pas par défaut. [COUCHES.md](https://github.com/carllaliberte/famille/blob/main/COUCHES.md) : « PQC par défaut » = interdit.

## Suites (pas UFHY1)

`UFHY1` reste **signatures** : Ed25519 + ML-DSA-65. [AGENTS.md](AGENTS.md) interdit d'écrire UFHY1 pour autre chose.

| Suite | Ce que v0 porte | Hypothèse |
|---|---|---|
| `x25519` | X25519 déclaré | Shor n'existe pas encore à cette taille |
| `mlkem768` | ML-KEM-768 (FIPS 203) déclaré | tient contre un adversaire harvest-now-decrypt-later |
| `x25519mlkem768` | hybride déclaré (X25519 **et** ML-KEM-768) | AND aujourd'hui ; OR plus tard contre HNDL |

v0 **déclare**. `ciphertext` = `null`. Pas d'encapsulage ici. Pas de clé dans Git. QUANTUM encapsule plus tard, ailleurs.

## Verrous

- Opt-in explicite (`opt_in: true`). Absent, faux, manquant → refus « pas par défaut ».
- Suite `UFHY1` / `ed25519` / `mldsa87` → refus (signatures, pas KEM).
- Slogan `quantum-safe` (et variantes) → refus. Voir garde `deny-horizon-slogan.json`.
- Pas fusionné dans `juge.v0.json` ni `flux.v0.json` (famille). Schéma : [`schema/kem.v0.json`](schema/kem.v0.json).
- Pas câblé dans `check.py`. Check ne lit pas `.kem.json`.
- HORIZON reste `horizon.py` `ecrire|lire|juger`.
- Pas un cloud PQC, pas un token, pas un L1, pas un avis juridique.

## Lancer

```bash
python3 kem.py ecrire --opt-in --suite x25519mlkem768 --vers examples/opt-in.kem.json
python3 kem.py lire examples/opt-in.kem.json
python3 kem.py juger examples/opt-in.kem.json
```

Sans `--opt-in` : exit ≠ 0.

## Vérifié vs présumé

| Affirmation | Statut |
|---|---|
| sans opt-in → refus | **vérifié** |
| `UFHY1` comme suite KEM → refus | **vérifié** |
| slogan `quantum-safe` → refus | **vérifié** |
| `ciphertext` v0 = `null` | **vérifié** |
| `check.py` n'importe pas ce rail | **vérifié** |
| harvest-now-decrypt-later comme menace 2026 | **présumé** (modèle, non prouvé ici) |
| ML-KEM-768 tient | **présumé** (FIPS 203, pas un théorème de ce dépôt) |
| encapsulage QUANTUM | **plus tard** — clés hors Git |

Rien ici n'est un sceau. Un merge n'est pas un encapsulage.
