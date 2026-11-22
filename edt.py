"""Vue semaine de l'emploi du temps (fichier .ics) pour l'ecran e-paper 4.2" (400x300)."""
import datetime as dt
import os
import re
import urllib.request
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw

from polices import police
from reglages import DOSSIER, cfg

WIDTH, HEIGHT = 400, 300
URL = cfg.ICS_URL
CACHE = os.path.join(DOSSIER, "edt.ics")
PARIS = ZoneInfo("Europe/Paris")
JOURS = ["Lun", "Mar", "Mer", "Jeu", "Ven"]
MOIS = ["janv.", "fevr.", "mars", "avril", "mai", "juin", "juil.", "aout",
        "sept.", "oct.", "nov.", "dec."]
H_DEBUT, H_FIN = cfg.EDT_H_DEBUT, cfg.EDT_H_FIN


def telecharger():
    """Met a jour le cache (lance 4 fois par jour) ; garde l'ancienne version en cas d'echec."""
    if not URL:
        print("ICS_URL vide dans config.py : calendrier d'exemple utilise")
        return
    try:
        with urllib.request.urlopen(URL, timeout=20) as r:
            data = r.read()
        if b"BEGIN:VCALENDAR" not in data:
            raise ValueError("reponse inattendue")
        tmp = CACHE + ".tmp"
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, CACHE)
        print(f"{dt.datetime.now():%Y-%m-%d %H:%M} edt.ics mis a jour ({len(data)} octets)")
    except Exception as e:
        print(f"{dt.datetime.now():%Y-%m-%d %H:%M} echec du telechargement : {e}")


def lire_cache(now=None):
    if not URL:  # pas de calendrier configure : emploi du temps fictif
        import exemple_edt
        return exemple_edt.ics_semaine(lundi_affiche(now or dt.datetime.now(PARIS)), PARIS)
    if not os.path.exists(CACHE):
        telecharger()
    with open(CACHE, encoding="utf-8", errors="replace") as f:
        return f.read()


def _date(valeur, params):
    if "VALUE=DATE" in params and "T" not in valeur:
        return dt.datetime.strptime(valeur, "%Y%m%d").replace(tzinfo=PARIS)
    if valeur.endswith("Z"):
        return dt.datetime.strptime(valeur, "%Y%m%dT%H%M%SZ").replace(
            tzinfo=dt.timezone.utc).astimezone(PARIS)
    tz = PARIS
    m = re.search(r"TZID=([^;:]+)", params)
    if m:
        try:
            tz = ZoneInfo(m.group(1))
        except Exception:
            pass
    return dt.datetime.strptime(valeur, "%Y%m%dT%H%M%S").replace(tzinfo=tz).astimezone(PARIS)


def evenements(texte):
    lignes = []
    for l in texte.replace("\r\n", "\n").split("\n"):
        if l[:1] in (" ", "\t") and lignes:
            lignes[-1] += l[1:]
        else:
            lignes.append(l)
    evs, ev = [], None
    for l in lignes:
        if l == "BEGIN:VEVENT":
            ev = {}
        elif l == "END:VEVENT" and ev is not None:
            if "debut" in ev and "fin" in ev:
                evs.append(ev)
            ev = None
        elif ev is not None and ":" in l:
            cle, val = l.split(":", 1)
            nom, _, params = cle.partition(";")
            if nom == "DTSTART":
                ev["debut"] = _date(val, params)
            elif nom == "DTEND":
                ev["fin"] = _date(val, params)
            elif nom == "SUMMARY":
                ev["titre"] = val.replace("\\,", ",").replace("\\;", ";")
            elif nom == "LOCATION":
                ev["lieu"] = val.replace("\\,", ",")
    return evs


def decouper(ev):
    """'G1_INFO - C012 (salle info) / C014 - PETIT / DURAND - TP -'
    -> ('INFO', ['C012', 'C014'], 'TP', ['Petit', 'Durand'])."""
    morceaux = [m.strip().rstrip("-").strip() for m in ev.get("titre", "").split(" - ")]
    morceaux = [m for m in morceaux if m and m != "-"]
    matiere = morceaux[0] if morceaux else "?"
    matiere = matiere.split("_", 1)[1] if "_" in matiere else matiere
    salle = morceaux[1] if len(morceaux) > 1 else ev.get("lieu", "")
    salle = re.sub(r"\s*\(.*?\)", "", salle)
    salles = [s.strip() for s in salle.split("/") if s.strip()]
    profs = morceaux[2] if len(morceaux) > 2 else ""
    profs = [p.strip().title() for p in profs.split("/") if p.strip()]
    typ = morceaux[3] if len(morceaux) > 3 else ""
    return matiere, salles, typ, profs


def _lignes(d, elements, font, largeur, sep):
    """Regroupe les elements (salles, profs) sur le moins de lignes possible."""
    lignes, cour = [], ""
    for el in elements:
        essai = f"{cour}{sep}{el}" if cour else el
        if not cour or d.textlength(essai, font=font) <= largeur:
            cour = essai
        else:
            lignes.append(cour)
            cour = el
    if cour:
        lignes.append(cour)
    return lignes


def lundi_affiche(now):
    """Semaine en cours ; le week-end on montre la semaine suivante."""
    lundi = (now - dt.timedelta(days=now.weekday())).date()
    if now.weekday() >= 5:
        lundi += dt.timedelta(days=7)
    return lundi


def _ajuster(d, texte, font, largeur):
    if d.textlength(texte, font=font) <= largeur:
        return texte
    while texte and d.textlength(texte + ".", font=font) > largeur:
        texte = texte[:-1]
    return texte + "." if texte else ""


def dessiner(now=None):
    now = now or dt.datetime.now(PARIS)
    lundi = lundi_affiche(now)
    vendredi = lundi + dt.timedelta(days=4)
    evs = [e for e in evenements(lire_cache(now))
           if lundi <= e["debut"].date() <= vendredi]

    img = Image.new("1", (WIDTH, HEIGHT), 1)
    d = ImageDraw.Draw(img)
    f_titre = police("sans-gras", 15)
    f_jour = police("sans-gras", 12)
    f_mat = police("sans-gras", 12)
    f_txt = police("sans", 10)
    f_heure = police("sans", 9)

    # Bandeau
    d.rectangle([0, 0, WIDTH, 24], fill=0)
    if lundi.month == vendredi.month:
        titre = f"Semaine du {lundi.day} au {vendredi.day} {MOIS[vendredi.month - 1]}"
    else:
        titre = f"Du {lundi.day} {MOIS[lundi.month - 1]} au {vendredi.day} {MOIS[vendredi.month - 1]}"
    d.text((8, 3), titre, font=f_titre, fill=1)
    h = now.strftime("%H:%M")
    d.text((WIDTH - 8 - d.textlength(h, font=f_titre), 3), h, font=f_titre, fill=1)

    # Grille
    x0, y_jours, y0, y1 = 24, 27, 44, HEIGHT - 3
    col = (WIDTH - x0 - 2) / 5
    px_h = (y1 - y0) / (H_FIN - H_DEBUT)

    def y_de(t):
        heures = t.hour + t.minute / 60
        return y0 + (min(max(heures, H_DEBUT), H_FIN) - H_DEBUT) * px_h

    for hh in range(H_DEBUT, H_FIN + 1, 2):
        y = y0 + (hh - H_DEBUT) * px_h
        d.text((2, y - 5), f"{hh}h", font=f_heure, fill=0)
        for x in range(x0, WIDTH - 2, 4):
            d.point((x, int(y)), fill=0)

    for i in range(5):
        jour = lundi + dt.timedelta(days=i)
        xa = x0 + i * col
        lab = f"{JOURS[i]} {jour.day}"
        aujourdhui = jour == now.date()
        if aujourdhui:
            d.rectangle([xa + 1, y_jours, xa + col - 1, y0 - 3], fill=0)
        d.text((xa + (col - d.textlength(lab, font=f_jour)) / 2, y_jours + 1), lab,
               font=f_jour, fill=1 if aujourdhui else 0)
        if i:
            d.line([xa, y_jours, xa, y1], fill=0)

    # Cours
    for e in sorted(evs, key=lambda e: e["debut"]):
        i = e["debut"].weekday()
        if i > 4:
            continue
        xa = x0 + i * col + 2
        xb = x0 + (i + 1) * col - 2
        ya, yb = y_de(e["debut"]), y_de(e["fin"])
        if yb - ya < 6:
            continue
        passe = e["fin"] < now
        d.rectangle([xa, ya + 1, xb, yb - 1], fill=1, outline=0, width=1 if passe else 2)
        matiere, salles, typ, profs = decouper(e)
        larg = xb - xa - 6
        ty = ya + 3
        # Priorite : matiere, toutes les salles (gras), puis le(s) prof(s) s'il reste de la place
        lignes = [(f"{matiere} {typ}".strip(), f_txt, 12)]
        lignes += [(l, f_mat, 13) for l in _lignes(d, salles, f_mat, larg, " / ")]
        lignes += [(l, f_txt, 12) for l in _lignes(d, profs, f_txt, larg, " / ")]
        for txt, f, hauteur in lignes:
            if ty + hauteur > yb - 2:
                break
            d.text((xa + 4, ty), _ajuster(d, txt, f, larg), font=f, fill=0)
            ty += hauteur

    if not evs:
        msg = "Aucun cours cette semaine"
        d.text(((WIDTH - d.textlength(msg, font=f_titre)) / 2, HEIGHT / 2), msg,
               font=f_titre, fill=0)
    return img


if __name__ == "__main__":
    import sys
    if "--telecharger" in sys.argv:
        telecharger()
    elif "--apercu" in sys.argv:
        dessiner().save("/tmp/edt.png")
    else:
        from epd42 import EPD
        epd = EPD()
        try:
            epd.init()
            epd.display(dessiner())
        finally:
            epd.sleep()
