"""Charge `config.py` s'il existe, sinon les valeurs par defaut de `config.example.py`."""
import importlib.util
import os

_DOSSIER = os.path.dirname(os.path.abspath(__file__))


def _charger():
    for nom in ("config.py", "config.example.py"):
        chemin = os.path.join(_DOSSIER, nom)
        if os.path.exists(chemin):
            spec = importlib.util.spec_from_file_location("config_panneau", chemin)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    raise FileNotFoundError("config.example.py introuvable")


cfg = _charger()
DOSSIER = _DOSSIER
