# Action (étage 1)

GitHub Action : lit une carte JSON, exit 0 ou 2.
N'émet pas. N'ouvre pas QUANTUM.

```yaml
- uses: carllaliberte/unforge-check@main
  with:
    carte: examples/os.json
```

Contrat : https://github.com/carllaliberte/famille/blob/main/schema/juge.v0.json
