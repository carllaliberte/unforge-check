# Example

```bash
python3 check.py examples/bienvenue.txt
python3 check.py examples/bienvenue.txt examples/bienvenue.txt.unforge.json
```

`bienvenue.txt.unforge.json` is `UNFORGE-PREUVE-v2` (Ed25519-only) so CI stays small.
`legacy-v1.unforge.json` is the previous press of the same file — dual-checked, never VERT.

Carl's live UFHY1 proofs are issued on the private QUANTUM node and sent as file + JSON — never as quantum.db.
