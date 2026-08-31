# UNFORGE Check

Drop a file. Drop the `.unforge.json` next to it. Green or red.

No account. No node. No chain. No coin.

The QUANTUM node that *issues* a proof stays on the owner’s machine
(`carllaliberte/unforge`, private). This repo is only the **public eye**.

```bash
pip install cryptography
python3 check.py photo.jpg photo.jpg.unforge.json
```

`ok: true` — that file is still the one the card sealed.
`ok: false` — it moved, or the ink does not hold.

## Why this exists

People already send photos, PDFs, recordings.
They need one sentence the other side can test without trusting a website.

UNFORGE Check is that sentence.

Mobile app comes after the format is boring and stable. See `MOBILE.md`.

## What this is not

- Not a quantum computer
- Not a token you trade
- Not a place to deposit notes
- Not QUANTUM-as-a-service

Brand **UNFORGE** is reserved. Code in this repository: Apache-2.0.
