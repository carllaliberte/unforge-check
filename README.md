# UNFORGE Check

Drop a file. Drop the `.unforge.json` next to it. Green or red.

```bash
git clone https://github.com/carllaliberte/unforge-check
cd unforge-check
pip install -r requirements.txt
python3 check.py examples/bienvenue.txt examples/bienvenue.txt.unforge.json
```

Optional cards — read, do not sign:

```bash
python3 check.py FILE FILE.unforge.json --quelle carte.quelle.json --horizon carte.horizon.json
```

`UFHY1` = Ed25519 + ML-DSA-65. Both halves must hold.
A dead HORIZON does not make the file false. It says: re-press.

CI — issuing stays private. This action only looks.

In your repo, `.github/workflows/constat.yml`:

```yaml
name: constat
on: [push, pull_request]
jobs:
  verifier:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: carllaliberte/unforge-check@main
        with:
          file: docs/contrat.pdf
          proof: docs/contrat.pdf.unforge.json
```

## Famille

| Rail | Question |
|---|---|
| [FIGURE](https://github.com/carllaliberte/figure-protocol) | qui |
| [SITUS](https://github.com/carllaliberte/situs-protocol) | où |
| [UNFORGE](https://github.com/carllaliberte/unforge-check) | quoi |
| [QUELLE](https://github.com/carllaliberte/quelle) | d'où le bit |
| [TÉMOIN](https://github.com/carllaliberte/temoin-protocol) | avec quelle force |
| [HORIZON](https://github.com/carllaliberte/horizon-protocol) | jusqu'à quand le sceau tient |

Issuing stays on a private QUANTUM node. This repo is the public eye.
MIT (protocoles) · Apache-2.0 (this eye). Brand UNFORGE reserved.
