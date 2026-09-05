# Bots — UNFORGE only

These are not the CreatorFlow « Quantum bus » agents.

| Bot | Kind | Job |
|---|---|---|
| GitHub Action `check` | CI | verify examples on every push |
| Action `carllaliberte/unforge-check@v1.0.0` | CI in other repos | verify file + proof |
| Dependabot | weekly | cryptography + actions |
| Grok `unforge-ci-casse` | on fail `rigueur` (private node) | diagnose, do not emit |
| Grok `unforge-check-ci-casse` | on fail `check` | diagnose public eye |
| Grok `unforge-check-pr` | PR opened | read AGENTS.md, never merge |
| Grok `github-revue-hebdo` | Monday 09:30 Toronto | family health |

No bot signs. No bot holds quantum.db. No bot opens the node.
Pin the Action at `@v1.0.0`. Do not follow `@main`.
