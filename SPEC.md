# UNFORGE-PREUVE-v1

A proof is a JSON file named `*.unforge.json` sitting beside the object it attests.

Required keys: `format`, `marque`, `id`, `card_id`, `card_public`, `token_id`, `empreinte`, `signature`, `fait`, `created_at`.

Signed material (UTF-8):

    {card_id}|{token_id}|{destination}|{corps}

Destinations: `QUANTUM` (note, corps = body), `REGISTRE` (constat, corps = empreinte), `RETRAIT` (retrait, corps = empreinte).

Fingerprint:

    SHA-256( fait | prev | token_id )

UTF-8, no extra spaces. Genesis `prev` is empty.
Roles:

- QUANTUM signs (private keys stay home).
- Check re-verifies Ed or `UFHY1` + file SHA-256.
- Press does not open the signature; it prints ids.
- Trail compares SHAs; it does not re-sign.
- Retract uses other material: `RETRAIT|{id}|{card}|{empreinte}`, signed by the same card on QUANTUM.
