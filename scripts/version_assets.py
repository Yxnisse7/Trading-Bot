#!/usr/bin/env python3
"""Ajoute aux pages du site (docs/*.html) un numéro de version sur les fichiers communs (yasuke.js, …).

Le numéro est une empreinte du contenu : dès qu'un fichier change, son adresse change aussi et les
navigateurs chargent la nouvelle version au lieu de garder l'ancienne en cache (GitHub Pages autorise
10 minutes de cache : une page neuve avec un ancien script restait bloquée sur « Chargement »).

  python scripts/version_assets.py          # met à jour les pages
  python scripts/version_assets.py --check  # vérifie seulement (utilisé par les tests)
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"
ASSETS = ("yasuke.css", "yasuke.js", "charts.js", "live-chart.js", "sections.js")


def fingerprint(name: str) -> str:
    return hashlib.sha256((DOCS / name).read_bytes()).hexdigest()[:10]


def versioned(html: str) -> str:
    for name in ASSETS:
        html = re.sub(rf'(["\']){re.escape(name)}(\?v=[0-9a-f]+)?\1', rf'\g<1>{name}?v={fingerprint(name)}\g<1>', html)
    return html


def main(argv: list[str]) -> int:
    stale = []
    for page in sorted(DOCS.glob("*.html")):
        text = page.read_text(encoding="utf-8")
        new = versioned(text)
        if new != text:
            stale.append(page.name)
            if "--check" not in argv:
                page.write_text(new, encoding="utf-8")
    if stale and "--check" in argv:
        print("Versions à mettre à jour : " + ", ".join(stale) + " (python scripts/version_assets.py)")
        return 1
    print("Pages mises à jour : " + (", ".join(stale) if stale else "aucune"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
