"""Alterne les pages de l'ecran e-paper a chaque lancement (cron toutes les minutes).

Rafraichissement partiel (sans clignotement) la plupart du temps,
complet tous les quarts d'heure (h:00, h:15, h:30, h:45) pour effacer les traces.

Usage : python3 ecran.py                   -> page suivante
        python3 ecran.py edt|meteo|pi|nuit -> page imposee
        python3 ecran.py ... --complet     -> force un rafraichissement complet
"""
import datetime
import os
import sys

from PIL import Image

import edt
import meteo
import nuit
import tableau
from epd42 import EPD
from reglages import DOSSIER, cfg

NUIT_DEBUT, NUIT_FIN = cfg.NUIT_DEBUT, cfg.NUIT_FIN  # ecran fige sur « Bonne nuit »
PAGES = {"edt": edt.dessiner, "meteo": meteo.dessiner, "pi": tableau.dessiner}
ORDRE = [p for p in cfg.PAGES if p in PAGES] or list(PAGES)
PERIODE_COMPLET = cfg.PERIODE_COMPLET  # minutes
ETAT = os.path.join(DOSSIER, "page.txt")
DERNIERE = os.path.join(DOSSIER, "derniere.png")   # image actuellement a l'ecran
COMPLET = os.path.join(DOSSIER, "dernier_complet.txt")


def page_suivante():
    try:
        derniere = open(ETAT).read().strip()
        return ORDRE[(ORDRE.index(derniere) + 1) % len(ORDRE)]
    except (OSError, ValueError):
        return ORDRE[0]


def complet_necessaire(now):
    """Un rafraichissement complet par quart d'heure."""
    try:
        dernier = datetime.datetime.fromisoformat(open(COMPLET).read().strip())
    except (OSError, ValueError):
        return True
    debut = now.replace(minute=now.minute - now.minute % PERIODE_COMPLET, second=0, microsecond=0)
    return debut > dernier


if __name__ == "__main__":
    args = sys.argv[1:]
    choix = [a for a in args if a in PAGES or a == "nuit"]
    now = datetime.datetime.now()
    try:
        page_affichee = open(ETAT).read().strip()
    except OSError:
        page_affichee = ""

    if choix:
        page = choix[0]
    elif NUIT_DEBUT <= now.hour < NUIT_FIN:
        if page_affichee == "nuit":
            sys.exit(0)          # deja affichee : on ne touche plus a l'ecran jusqu'au matin
        page = "nuit"
    else:
        page = page_suivante() if page_affichee != "nuit" else ORDRE[0]
    image = nuit.dessiner() if page == "nuit" else PAGES[page]()

    precedente = None
    if os.path.exists(DERNIERE):
        try:
            precedente = Image.open(DERNIERE).convert("1")
        except Exception:
            precedente = None
    complet = ("--complet" in args or precedente is None or complet_necessaire(now)
               or page == "nuit" or page_affichee == "nuit")

    epd = EPD()
    try:
        epd.init()
        if complet:
            epd.display(image)
        else:
            epd.display_partial(image, precedente)
    finally:
        epd.sleep()

    image.convert("1").save(DERNIERE)
    with open(ETAT, "w") as f:
        f.write(page)
    if complet:
        with open(COMPLET, "w") as f:
            f.write(now.isoformat())
    print(f"{now:%Y-%m-%d %H:%M} page={page} {'complet' if complet else 'partiel'}")
