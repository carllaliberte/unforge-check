# Automatic verification

## This repo

Push to main → workflow `check` runs UNFORGE Check on `examples/bienvenue.txt`.

## Any other repo

```yaml
# .github/workflows/constat.yml
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

Or call the reusable workflow:

```yaml
jobs:
  verifier:
    uses: carllaliberte/unforge-check/.github/workflows/unforge.yml@main
    with:
      file: docs/contrat.pdf
      proof: docs/contrat.pdf.unforge.json
```
