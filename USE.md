# Use UNFORGE on GitHub

```yaml
- uses: actions/checkout@v4
- uses: carllaliberte/unforge-check@main
  with:
    file: docs/contrat.pdf
    proof: docs/contrat.pdf.unforge.json
```

Issuing stays on a local QUANTUM node. GitHub never holds quantum.db.
