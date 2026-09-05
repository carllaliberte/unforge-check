# Action (étage 1)

GitHub Action : lit une carte JSON, exit 0 ou 2.
N'émet pas. N'ouvre pas QUANTUM.

Pin a release. Do not follow `@main`.

```yaml
- uses: carllaliberte/unforge-check@v1.0.0
  with:
    file: examples/bienvenue.txt
    proof: examples/bienvenue.txt.unforge.json
```

Contrat : https://github.com/carllaliberte/famille/blob/main/schema/juge.v0.json
Proof format : `UNFORGE-PREUVE-v2` — see [FORMAT.md](FORMAT.md).
