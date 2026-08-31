# UNFORGE Check

Drop a file. Drop the `.unforge.json` next to it. Green or red.

```bash
git clone https://github.com/carllaliberte/unforge-check
cd unforge-check
pip install -r requirements.txt
python3 check.py examples/bienvenue.txt examples/bienvenue.txt.unforge.json
```

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

Issuing stays on a private QUANTUM node. This repo is the public eye.
Brand UNFORGE reserved. Code: Apache-2.0.
