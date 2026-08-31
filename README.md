# UNFORGE Check

Drop a file. Drop the `.unforge.json`. Green or red.

## On GitHub

```yaml
- uses: carllaliberte/unforge-check@main
  with:
    file: examples/bienvenue.txt
    proof: examples/bienvenue.txt.unforge.json
```

## On your machine

```bash
git clone https://github.com/carllaliberte/unforge-check
cd unforge-check
pip install -r requirements.txt
python3 check.py examples/bienvenue.txt examples/bienvenue.txt.unforge.json
```

Issuing is a private QUANTUM node. This repo is the public eye.
See [USE.md](USE.md) and [FAMILY.md](FAMILY.md).

Brand UNFORGE reserved. Code: Apache-2.0.
