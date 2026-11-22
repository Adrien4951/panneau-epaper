"""Configuration du panneau d'affichage.

Copier ce fichier en `config.py` puis l'adapter :

    cp config.example.py config.py

`config.py` est ignore par git : vos adresses et reglages personnels n'y seront jamais publies.
"""

# --- Emploi du temps -------------------------------------------------------
# Adresse d'un calendrier au format iCalendar (.ics) : export de l'ENT, Google Agenda
# (adresse secrete), Nextcloud, etc. Laisser vide pour utiliser le calendrier d'exemple.
ICS_URL = ""

# Heures affichees dans la vue semaine (de H_DEBUT a H_FIN).
EDT_H_DEBUT = 8
EDT_H_FIN = 19

# --- Meteo (Open-Meteo, gratuit, sans cle) ---------------------------------
VILLE = "Paris"
LATITUDE = 48.857
LONGITUDE = 2.352

# --- Page « etat du serveur » ----------------------------------------------
# Conteneurs Docker a surveiller : (nom du conteneur, libelle affiche).
SERVICES = [
    ("homebridge", "Homebridge"),
    ("nextcloud", "Nextcloud"),
    ("samba", "Partage"),
]
# Espaces disque a afficher : (libelle, point de montage).
DISQUES = [
    ("Nextcloud", "/srv/nextcloud"),
    ("Partage", "/srv/partage"),
    ("Carte SD", "/"),
]

# --- Rotation des pages ----------------------------------------------------
# Pages disponibles : "edt", "meteo", "pi".
PAGES = ["edt", "meteo", "pi"]
# Un rafraichissement complet (avec clignotement) toutes les N minutes ; partiel sinon.
PERIODE_COMPLET = 15
# Pause nocturne : page « Bonne nuit » puis ecran fige entre ces heures.
NUIT_DEBUT = 0
NUIT_FIN = 6

# --- Brochage (numeros GPIO BCM) -------------------------------------------
PIN_DC = 25
PIN_RST = 17
PIN_BUSY = 24
# Duree d'attente minimale apres un rafraichissement complet / partiel (secondes).
# Utile si la ligne BUSY n'est pas cablee ou ne remonte pas.
ATTENTE_COMPLET = 5.0
ATTENTE_PARTIEL = 1.5
