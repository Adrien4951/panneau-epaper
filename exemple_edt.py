"""Emploi du temps fictif, genere pour la semaine affichee (demo et apercus).

Utilise quand ICS_URL est vide dans config.py. Le format des titres imite celui
attendu par edt.py :  « GROUPE_MATIERE - SALLE(S) - PROF(S) - TYPE - ».
"""
import datetime as dt

# (jour 0=lundi, debut, fin, titre)
COURS = [
    (0, "08:00", "10:00", "G1_MATH - B101 - MARTIN - CM -"),
    (0, "10:15", "12:15", "G1_PHYS - A204 (amphi) - BERNARD - TD -"),
    (0, "13:45", "17:00", "G1_INFO - C012 / C014 - PETIT / DURAND - TP -"),
    (1, "08:30", "12:00", "G1_ELEC - D105 - LEROY - TP -"),
    (1, "13:45", "15:45", "G1_MATH - B101 - MARTIN - TD -"),
    (1, "16:00", "18:00", "G1_LANG - L02 - SMITH - TD -"),
    (2, "10:15", "12:15", "G1_MECA - Amphi A - MOREAU - CM -"),
    (2, "13:45", "17:00", "G1_PROJ - Fablab - DURAND - TP -"),
    (3, "08:00", "12:15", "G1_INFO - C012 / C014 / C016 - PETIT / DURAND - TP -"),
    (3, "13:45", "15:45", "G1_PHYS - A204 - BERNARD - CM -"),
    (4, "08:00", "10:00", "G1_ECO - B210 - GARNIER - CM -"),
    (4, "10:15", "12:15", "G1_MECA - S018 - MOREAU - TD -"),
    (4, "13:45", "15:45", "G1_SPORT - Gymnase - FAURE - TD -"),
]


def ics_semaine(lundi, tz):
    lignes = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//panneau-epaper//exemple//FR"]
    for i, (jour, debut, fin, titre) in enumerate(COURS):
        date = lundi + dt.timedelta(days=jour)
        d0 = dt.datetime.combine(date, dt.time.fromisoformat(debut), tz).astimezone(dt.timezone.utc)
        d1 = dt.datetime.combine(date, dt.time.fromisoformat(fin), tz).astimezone(dt.timezone.utc)
        lignes += ["BEGIN:VEVENT", f"UID:exemple-{i}@panneau-epaper",
                   f"DTSTART:{d0:%Y%m%dT%H%M%SZ}", f"DTEND:{d1:%Y%m%dT%H%M%SZ}",
                   f"SUMMARY:{titre}", "END:VEVENT"]
    lignes.append("END:VCALENDAR")
    return "\r\n".join(lignes) + "\r\n"
