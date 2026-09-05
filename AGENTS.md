# UNFORGE — instructions for agents

You are looking at the public eye, not the node.

## Do

- Verify: `python check.py FILE` (looks for `FILE.unforge.json`) or `python check.py FILE FILE.unforge.json`
- Optional read: `--quelle carte.quelle.json` `--horizon carte.horizon.json`
- Interop (no server): `python check.py --schema` · `from check import verifier` · INTEROP.md
- Or GitHub Action `carllaliberte/unforge-check@v1.0.0` with `file` + `proof` (pin a release; never `@main`)
- Mesure: https://github.com/carllaliberte/mesure-protocol
- Treat `ok: true` as the only success signal for the file
- A dead horizon is `horizon.ok: false` — re-press, file is not forged
- Keep proofs next to files; never invent a signature
- Oubli: `python3 oubli.py brouillon FILE --vers oubli.json` · `appliquer FILE oubli.json` · `lire oubli.json`
- Appliquer = sha256 then unlink. Hash moved → refuse (l'objet local reste). After unlink the local object is gone; the oubli card and Git history stay.

## Do not

- Call this a quantum computer, a coin, or a cloud
- Open or request `quantum.db` / private keys
- Issue proofs here (issuing is private QUANTUM: `carllaliberte/unforge`)
- Put a QUANTUM node on the public internet or in an app store
- Merge a Dependabot PR if workflow `check` is red
- Write `UFHY1` for anything other than Ed25519 + ML-DSA-65
- Invent an oubli token or photon
- Treat oubli as a cloud wipe — Git does not erase
- Sign an oubli (Unforge does not sign)
- Follow `carllaliberte/unforge-check@main` in a workflow — pin `@v1.0.0` or a commit SHA

## Formats

- Proof: `UNFORGE-PREUVE-v2` — see SPEC.md and FORMAT.md. v1 is read, never VERT.
- Trail: `UNFORGE-TRAIL-v1` — repo unforge-trail
- Retract: `UNFORGE-RETRAIT-v1` — repo unforge-retract
- Oubli: `UNFORGE-OUBLI-v1` — local unlink after sha256, see OUBLI.md
- Press: HTML A5 — repo unforge-press

## Signed material (proof)

```
{card_id}|{token_id}|REGISTRE|{empreinte}
```

v1 empreinte = SHA-256(fait|prev|token_id) — does **not** bind the file.
v2 empreinte = SHA-256(fait|prev|token_id|objet.sha256|objet.octets)
Signature: Ed25519 or `UFHY1:<ed>:<mldsa65>` (both must hold).
Missing ML-DSA in `cryptography` is named: `ML-DSA non disponible dans cette installation`.

## Brand

UNFORGE is a trademark of Carl Laliberté.
This repo: Apache-2.0. The private node is not licensed here.
