"""Genere les images de toutes les pages SANS ecran (PC, Mac ou Pi).

    python3 apercu.py            -> donnees fictives, images dans docs/
    python3 apercu.py --reelles  -> vraies donnees (a lancer sur le Pi)

Pratique pour tester une mise en page avant de l'envoyer sur l'ecran.
"""
import datetime as dt
import os
import sys

import edt
import meteo
import nuit
import tableau

SORTIE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")

METEO_FICTIVE = {
    "current": {"temperature_2m": 14.2, "apparent_temperature": 12.8, "relative_humidity_2m": 72,
                "weather_code": 2, "wind_speed_10m": 14, "is_day": 1},
    "daily": {"time": [], "weather_code": [2, 61, 3, 0, 80],
              "temperature_2m_max": [15, 12, 13, 16, 14], "temperature_2m_min": [8, 9, 7, 6, 9],
              "precipitation_probability_max": [10, 85, 30, 0, 60]},
}


def donnees_fictives(now):
    """Remplace les mesures du Pi et la meteo par des valeurs d'exemple."""
    tableau.ip_locale = lambda: "192.168.0.42"
    tableau.temperature = lambda: 47.0
    tableau.memoire = lambda: (412.0, 905.0)
    tableau.services = lambda: [("Homebridge", True), ("Nextcloud", True), ("Partage", False)]
    tailles = {"Nextcloud": (1.3, 5.0), "Partage": (3.6, 5.0), "Carte SD": (10.1, 31.0)}
    noms = {chemin: label for label, chemin in tableau.cfg.DISQUES}
    tableau.disque = lambda chemin: tailles.get(noms.get(chemin), (2.0, 10.0))
    data = dict(METEO_FICTIVE)
    data["daily"] = dict(data["daily"],
                         time=[(now.date() + dt.timedelta(days=i)).isoformat() for i in range(5)])
    meteo.donnees = lambda: data


if __name__ == "__main__":
    os.makedirs(SORTIE, exist_ok=True)
    if "--reelles" in sys.argv:
        now = dt.datetime.now(edt.PARIS)
    else:
        # Un mardi a 10 h 20, pour que la colonne « aujourd'hui » soit visible.
        aujourd = dt.date.today()
        mardi = aujourd - dt.timedelta(days=aujourd.weekday()) + dt.timedelta(days=1)
        now = dt.datetime.combine(mardi, dt.time(10, 20), edt.PARIS)
        donnees_fictives(now)
    pages = {
        "page-edt.png": lambda: edt.dessiner(now),
        "page-meteo.png": lambda: meteo.dessiner(now.replace(tzinfo=None)),
        "page-pi.png": lambda: tableau.dessiner(now.replace(tzinfo=None)),
        "page-nuit.png": lambda: nuit.dessiner(now.replace(hour=0, minute=0)),
    }
    for nom, fabrique in pages.items():
        chemin = os.path.join(SORTIE, nom)
        fabrique().save(chemin)
        print("ecrit", chemin)
