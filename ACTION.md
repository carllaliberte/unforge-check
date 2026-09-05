# Action (étage 1)

GitHub Action : lit une carte JSON, exit 0 ou 2.
N'émet pas. No node.

Pin a release. Do not follow `@main`.

Copy-paste badge (your repo, your workflow file):

```markdown
[![UNFORGE Check](https://github.com/YOUR/REPO/actions/workflows/constat.yml/badge.svg)](https://github.com/YOUR/REPO/actions/workflows/constat.yml)
```

This repo:

[![UNFORGE Check](https://github.com/carllaliberte/unforge-check/actions/workflows/constat.yml/badge.svg)](https://github.com/carllaliberte/unforge-check/actions/workflows/constat.yml)

```yaml
- uses: carllaliberte/unforge-check@v1.0.0
  with:
    file: examples/bienvenue.txt
    proof: examples/bienvenue.txt.unforge.json
```

Never `@main`. Pin `@v1.0.0` or a commit SHA.

Proof format : `UNFORGE-PREUVE-v2` — see [FORMAT.md](FORMAT.md).
Door: [docs/porte.html](docs/porte.html).
