# OUBLI

UNFORGE scelle un fichier. L'oubli le retire de la machine.

```
retrait  →  la preuve reste, le geste est public
oubli    →  l'objet local disparaît
```

Appliquer = comparer sha256, puis unlink. Hash bougé → refus.

Git ne s'efface pas. Pas de cloud wipe. Pas de token d'oubli. Pas de photon inventé.

Format : `UNFORGE-OUBLI-v1`

Unforge ne signe pas. Pas de nœud QUANTUM ici.

```bash
python3 oubli.py brouillon fichier.txt --vers oubli.json
python3 oubli.py appliquer fichier.txt oubli.json
python3 oubli.py lire oubli.json
```

© 2026 Carl Laliberté. Apache-2.0.
