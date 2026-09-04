# UNFORGE — instructions for agents

You are looking at the public eye, not the node.

## Do

- Verify: `python check.py FILE` (looks for `FILE.unforge.json`) or `python check.py FILE FILE.unforge.json`
- Optional read: `--quelle carte.quelle.json` `--horizon carte.horizon.json`
- Interop (no server): `python check.py --schema` · `from check import verifier` · INTEROP.md
- Or GitHub Action `carllaliberte/unforge-check@main` with `file` + `proof`
- Treat `ok: true` as the only success signal for the file
- A dead horizon is `horizon.ok: false` — re-press, file is not forged
- Keep proofs next to files; never invent a signature
- Oubli: `python3 oubli.py brouillon FILE --vers oubli.json` · `appliquer FILE oubli.json` · `lire oubli.json`
- Appliquer = sha256 then unlink. Hash moved → refuse. The file stays.

## Do not

- Call this a quantum computer, a coin, or a cloud
- Open or request `quantum.db` / private keys
- Issue proofs here (issuing is private QUANTUM: `carllaliberte/unforge`)
- Put a QUANTUM node on the public internet or in an app store
- Merge a Dependabot PR if workflow `check` is red
- Write `UFHY1` for anything other than Ed25519 + ML-DSA-65
- Link mesure-protocol (repo does not exist)
- Invent an oubli token or photon
- Treat oubli as a cloud wipe — Git does not erase
- Sign an oubli (Unforge does not sign)

## Formats

- Proof: `UNFORGE-PREUVE-v1` — see SPEC.md
- Trail: `UNFORGE-TRAIL-v1` — repo unforge-trail
- Retract: `UNFORGE-RETRAIT-v1` — repo unforge-retract
- Oubli: `UNFORGE-OUBLI-v1` — local unlink after sha256, see OUBLI.md
- Press: HTML A5 — repo unforge-press

## Signed material (proof)

```
{card_id}|{token_id}|REGISTRE|{empreinte}
```

empreinte = SHA-256(fait|prev|token_id)
Signature: Ed25519 or `UFHY1:<ed>:<mldsa65>` (both must hold).

## Brand

UNFORGE is a trademark of Carl Laliberté.
This repo: Apache-2.0. The private node is not licensed here.
