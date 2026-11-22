"""Page « Bonne nuit » affichee une seule fois a minuit (l'ecran reste fige jusqu'a 6 h)."""
import datetime as dt
import random

from PIL import Image, ImageDraw

import edt
import meteo
from polices import police
from reglages import cfg

WIDTH, HEIGHT = 400, 300
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


def _etoile(d, x, y, r):
    d.line([x - r, y, x + r, y], fill=1)
    d.line([x, y - r, x, y + r], fill=1)
    if r >= 3:
        d.point([(x - 1, y - 1), (x + 1, y + 1), (x - 1, y + 1), (x + 1, y - 1)], fill=1)


def prochain_cours(now):
    try:
        evs = edt.evenements(edt.lire_cache(now))
    except Exception:
        return None
    futurs = [e for e in evs if e["debut"] > now]
    return min(futurs, key=lambda e: e["debut"]) if futurs else None


def dessiner(now=None):
    now = now or dt.datetime.now(edt.PARIS)
    img = Image.new("1", (WIDTH, HEIGHT), 0)  # fond noir
    d = ImageDraw.Draw(img)

    # Ciel etoile (positions fixes, hors des zones de texte)
    rnd = random.Random(42)
    for _ in range(70):
        x, y = rnd.randint(4, WIDTH - 4), rnd.randint(4, HEIGHT - 4)
        if 95 < y < 205 and 110 < x < 395:
            continue
        if y > 215:
            continue
        r = rnd.choice([1, 1, 1, 2, 2, 3])
        if r == 1:
            d.point((x, y), fill=1)
        else:
            _etoile(d, x, y, r)

    # Croissant de lune
    cx, cy, r = 62, 150, 44
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=1)
    d.ellipse([cx - r + 22, cy - r - 12, cx + r + 22, cy + r - 12], fill=0)
    for (x, y, rr) in [(112, 118, 3), (100, 185, 2), (24, 98, 2)]:
        _etoile(d, x, y, rr)

    # Titre
    f_titre = police("serif", 46)
    f_sous = police("sans", 13)
    zone_g, zone_d = 118, 392
    titre = "Bonne nuit"
    tw = d.textlength(titre, font=f_titre)
    d.text((zone_g + (zone_d - zone_g - tw) / 2, 100), titre, font=f_titre, fill=1)
    sous = f"écran en pause jusqu'à {cfg.NUIT_FIN} h"
    sw = d.textlength(sous, font=f_sous)
    xs = zone_g + (zone_d - zone_g - sw) / 2
    d.line([xs - 26, 172, xs - 8, 172], fill=1)
    d.line([xs + sw + 8, 172, xs + sw + 26, 172], fill=1)
    d.text((xs, 164), sous, font=f_sous, fill=1)

    # Bandeau du bas : prochain cours + meteo
    d.rectangle([0, 222, WIDTH, HEIGHT], fill=1)
    f_lab = police("sans", 12)
    f_val = police("sans-gras", 16)
    d.text((12, 230), "PROCHAIN COURS", font=f_lab, fill=0)
    e = prochain_cours(now)
    if e:
        matiere, salles, typ, _ = edt.decouper(e)
        quand = e["debut"]
        jour = "auj." if quand.date() == now.date() else JOURS[quand.weekday()][:3] + "."
        ligne1 = f"{jour} {quand:%Hh%M}  {matiere} {typ}".strip()
        ligne2 = " / ".join(salles)
    else:
        ligne1, ligne2 = "Aucun cours prévu", ""
    d.text((12, 246), ligne1, font=f_val, fill=0)
    d.text((12, 268), ligne2, font=f_val, fill=0)

    d.line([250, 232, 250, 290], fill=0)
    d.text((262, 230), "MÉTÉO DU JOUR", font=f_lab, fill=0)
    data = meteo.donnees()
    if data and data.get("daily"):
        j = data["daily"]
        i = 0
        for k, t in enumerate(j["time"]):
            if dt.date.fromisoformat(t) == now.date():
                i = k
        meteo.icone(d, 285, 268, 17, int(j["weather_code"][i]))
        d.text((310, 248), f"{round(j['temperature_2m_min'][i])}° / {round(j['temperature_2m_max'][i])}°",
               font=f_val, fill=0)
        p = j.get("precipitation_probability_max", [None] * (i + 1))[i]
        if p is not None:
            d.text((310, 270), f"pluie {p} %", font=f_lab, fill=0)
    return img


if __name__ == "__main__":
    dessiner().save("/tmp/nuit.png")
