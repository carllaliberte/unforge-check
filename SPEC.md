# UNFORGE-PREUVE-v1

A proof is a JSON file named `*.unforge.json` sitting beside the object it attests.

Required keys: `format`, `marque`, `id`, `card_id`, `card_public`, `token_id`, `empreinte`, `signature`, `fait`, `created_at`.

Signed material (UTF-8):

    {card_id}|{token_id}|REGISTRE|{empreinte}

Signature is Ed25519, or `UFHY1:<ed>:<mldsa65>` (both inks must hold).
A verifier never needs quantum.db, a private key, or a network.
