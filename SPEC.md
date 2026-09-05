# UNFORGE-PREUVE-v2

A proof is a JSON file named `*.unforge.json` sitting beside the object it attests.

Required keys: `format`, `marque`, `id`, `card_id`, `card_public`, `token_id`, `empreinte`, `signature`, `fait`, `created_at`, `objet`.

`format` is `UNFORGE-PREUVE-v2`. v1 cards are still parsed (dual check) and never VERT. See [FORMAT.md](FORMAT.md).

Signed material (UTF-8):

    {card_id}|{token_id}|{destination}|{corps}

Destinations: `QUANTUM` (note, corps = body), `REGISTRE` (constat, corps = empreinte), `RETRAIT` (retrait, corps = empreinte).

Fingerprint:

    SHA-256( fait | prev | token_id | objet.sha256 | objet.octets )

UTF-8, no extra spaces. Genesis `prev` is empty. `objet.octets` is a canonical decimal integer.

v1 (legacy, not a file seal):

    SHA-256( fait | prev | token_id )

Roles:

- QUANTUM signs (private keys stay home).
- Check re-verifies Ed or `UFHY1` + file SHA-256. ML-DSA missing is a named error, not a silent false.
- Press does not open the signature; it prints ids.
- Trail compares SHAs via the same `empreinte()`; it does not re-sign.
- Retract uses other material: `RETRAIT|{id}|{card}|{empreinte}`, signed by the same card on QUANTUM.
- Oubli is not a destination and is not signed. `UNFORGE-OUBLI-v1` records a local unlink after sha256. Hash moved → refuse. Git does not erase. Not a cloud wipe. No oubli token. Unforge does not sign.
