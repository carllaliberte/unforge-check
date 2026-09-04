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

## Exit

| Code | Meaning |
|---|---|
| 0 | match (`ok: true`, satellites not false) |
| 1 | refuse (format, fingerprint, signature, file, lying quelle, dead horizon) |
| 2 | unreadable (missing path, bad JSON) |

`ok: true` is the only success signal **for the file**. A dead horizon is `horizon.ok: false` — re-press. The file is not forged. Exit may still be 1 so CI asks for a new press.

## Record

JSON on stdout. Shape: `schema/check.v0.json`. Stable keys: `ok`, `geste`, `empreinte_ok`, `signature_ok`, `fichier_ok`, `sha256`, `id`, `card_id`, `marque`, `noeud`, `phrase`. Extra keys may appear. `--human` prints VERT / ROUGE / AMBRE instead of JSON. VERT = the file matches the card. Public eye, not a seal.

## Do not

Stand up a server. Open `quantum.db`. Invent a signature. Call this a coin.
