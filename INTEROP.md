# Interop — no server

Other agents and tools verify a card with a local process. No node. No cloud. No coin. Nothing here signs.

## Command

```bash
python3 check.py FILE
python3 check.py FILE FILE.unforge.json
python3 check.py --schema
```

`FILE` alone looks for `FILE.unforge.json` beside it.

## Python

```python
from pathlib import Path
from check import verifier, schema

rec = verifier(Path("doc.pdf.unforge.json"), Path("doc.pdf"))
assert rec["ok"] is True          # only pass signal for the file
schema()                          # check.v0
```

`check`, `check_paquet`, `lire_quelle`, `lire_horizon` stay importable.

`UNFORGE-PREUVE-v2` is the seal that binds the file (`objet.sha256` + `objet.octets` in `empreinte` and, jalon 2, in `materiau()`).
`UNFORGE-PREUVE-v1` is dual-checked and never `ok: true`. See FORMAT.md.

## Jalon 2 — hybrid materiau

`UNFORGE-PREUVE-v2` `materiau()` is `{card_id}|{token_id}|REGISTRE|{empreinte}|{objet.sha256}|{objet.octets}`. `empreinte()` already hashes those objet fields; jalon 2 also writes them into the signed bytes so Ed25519 and ML-DSA-65 (`UFHY1`) both verify one canonical `message`, including the file link. If `materiau()` only embedded the `empreinte` hex, a future bug or alternate path that recomputed `empreinte()` differently from what was sealed would leave the signature unbound to `objet.sha256|octets` — the same class of silent card substitution already found on v1. Cards pressed before jalon 2 still verify: Check tries the new materiau first, then the legacy string without the trailing objet lien. A legacy hit sets `materiau_legacy: true` (structured note; the file can still VERT). Re-press to drop the note.

## Exit

| Code | Meaning |
|---|---|
| 0 | match (`ok: true`, satellites not false) |
| 1 | refuse (format, fingerprint, signature, file, lying quelle, dead horizon, v1 card) |
| 2 | unreadable (missing path, bad JSON) |

`ok: true` is the only success signal **for the file**. A dead horizon is `horizon.ok: false` — re-press. The file is not forged. Exit may still be 1 so CI asks for a new press.

## Record

JSON on stdout. Shape: `schema/check.v0.json`. Stable keys: `ok`, `geste`, `empreinte_ok`, `signature_ok`, `fichier_ok`, `sha256`, `id`, `card_id`, `marque`, `noeud`, `phrase`. Extra keys may appear (`format`, `legacy`, `crypto`, `materiau_legacy`). `--human` prints VERT / ROUGE / AMBRE instead of JSON. VERT = the file matches the card. Public eye, not a seal. `--summary` appends the same words as a CI job summary (`$GITHUB_STEP_SUMMARY`). Digest/match only. Does not sign. Not a receipt.

## Do not

Stand up a server. Open `quantum.db`. Invent a signature. Call this a coin.
Default a KEM. Fuse `kem.v0` into `juge.v0` / `flux.v0`. Call UFHY1 a KEM.

`kem.py ecrire` uses `fcntl.flock` (LOCK_EX) on the output write (jalon 1).
