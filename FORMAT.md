# UNFORGE-PREUVE-v1 → v2

Check does not sign. This bump is a **verification** change.

## Why

v1 hashed `{fait}|{prev}|{token_id}` and signed `{card_id}|{token_id}|REGISTRE|{empreinte}`.
`objet.sha256` / `objet.octets` sat **outside** that material.

A holder of a signed v1 card could rewrite `objet` to another file's digest.
`empreinte_ok` and `signature_ok` stayed true. The public eye would VERT the wrong file.

v2 puts the file into the fingerprint.

## Fingerprint

UTF-8, no extra spaces. Genesis `prev` is empty.

| Format | `empreinte` = SHA-256 of |
|---|---|
| `UNFORGE-PREUVE-v1` | `{fait}\|{prev}\|{token_id}` |
| `UNFORGE-PREUVE-v2` | `{fait}\|{prev}\|{token_id}\|{objet.sha256}\|{objet.octets}` |

`objet.octets` is the canonical decimal integer (`92`, not `92.0`). Missing sha or octets → empty field, still hashed.

Signed material is unchanged:

```
{card_id}|{token_id}|REGISTRE|{empreinte}
```

Because `empreinte` now covers `objet`, the signature covers the file.

## Dual check (transition)

| Card `format` | Crypto evaluated with | `ok` | Human | Exit |
|---|---|---|---|---|
| `UNFORGE-PREUVE-v2` | v2 formula | true only if empreinte + signature + file | VERT | 0 |
| `UNFORGE-PREUVE-v1` | v1 formula (so the presser can still see the card) | **always false** | AMBRE if v1 crypto holds | 1 |
| other | — | false | ROUGE | 1 |

v1 is **read**, never a file seal. Phrase: `v1 tient mais n'inclut pas objet. resseller en v2.`

CI that used v1 cards will go red until QUANTUM re-presses them as v2. That is the fix.

## Trail

`trail.py` imports `empreinte` from `check.py`. Each maillon uses the formula of **its own** `format`. A v2 maillon whose `objet` was swapped fails `empreinte_ok`.

## Migration for a presser (QUANTUM, off this repo)

1. Keep the same `fait`, `prev`, `token_id`, keys.
2. Set `format` to `UNFORGE-PREUVE-v2`.
3. Recompute `empreinte` with the v2 string (include `objet.sha256` and `objet.octets`).
4. Re-sign `materiau`.
5. Old v1 JSON stays in the trail as history; it will AMBRE here, not VERT.

This repository does not issue the new signature.
