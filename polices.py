"""Trouve les polices : DejaVu (Raspberry Pi OS / Debian), sinon equivalents Windows/macOS."""
import os

from PIL import ImageFont

_DOSSIERS = [
    "/usr/share/fonts/truetype/dejavu",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts"),
]
_CANDIDATS = {
    "sans": ["DejaVuSans.ttf", "/Library/Fonts/Verdana.ttf", "C:/Windows/Fonts/verdana.ttf"],
    "sans-gras": ["DejaVuSans-Bold.ttf", "/Library/Fonts/Verdana Bold.ttf",
                  "C:/Windows/Fonts/verdanab.ttf"],
    "serif": ["DejaVuSerif.ttf", "/Library/Fonts/Georgia.ttf", "C:/Windows/Fonts/georgia.ttf"],
}
_cache = {}


def _chemin(style):
    for c in _CANDIDATS[style]:
        if os.path.isabs(c):
            if os.path.exists(c):
                return c
        else:
            for d in _DOSSIERS:
                p = os.path.join(d, c)
                if os.path.exists(p):
                    return p
    raise FileNotFoundError(
        f"Police '{style}' introuvable : installer fonts-dejavu-core (sudo apt install fonts-dejavu-core)")


def police(style, taille):
    cle = (style, taille)
    if cle not in _cache:
        _cache[cle] = ImageFont.truetype(_chemin(style), taille)
    return _cache[cle]
