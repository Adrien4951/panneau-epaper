"""Page meteo pour l'ecran e-paper 4.2" (400x300), donnees Open-Meteo (gratuit, sans cle)."""
import datetime as dt
import json
import math
import os
import time
import urllib.request

from PIL import Image, ImageDraw

from polices import police
from reglages import DOSSIER, cfg

WIDTH, HEIGHT = 400, 300
VILLE = cfg.VILLE
LAT, LON = cfg.LATITUDE, cfg.LONGITUDE
CACHE = os.path.join(DOSSIER, "meteo.json")
DUREE_CACHE = 30 * 60  # secondes
JOURS = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]

URL = ("https://api.open-meteo.com/v1/forecast"
       f"?latitude={LAT}&longitude={LON}"
       "&current=temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,"
       "wind_speed_10m,is_day"
       "&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max"
       "&timezone=Europe%2FParis&forecast_days=5")

LIBELLES = {
    0: "Ciel dégagé", 1: "Plutôt dégagé", 2: "Partiellement nuageux", 3: "Couvert",
    45: "Brouillard", 48: "Brouillard givrant",
    51: "Bruine légère", 53: "Bruine", 55: "Bruine forte", 56: "Bruine verglaçante",
    57: "Bruine verglaçante", 61: "Pluie faible", 63: "Pluie", 65: "Forte pluie",
    66: "Pluie verglaçante", 67: "Pluie verglaçante", 71: "Neige faible", 73: "Neige",
    75: "Forte neige", 77: "Grains de neige", 80: "Averses", 81: "Averses",
    82: "Fortes averses", 85: "Averses de neige", 86: "Averses de neige",
    95: "Orage", 96: "Orage avec grêle", 99: "Orage avec grêle",
}


def donnees():
    """Lit le cache ; le rafraichit s'il a plus de 30 min (garde l'ancien en cas d'echec)."""
    frais = os.path.exists(CACHE) and time.time() - os.path.getmtime(CACHE) < DUREE_CACHE
    if not frais:
        try:
            with urllib.request.urlopen(URL, timeout=15) as r:
                data = json.load(r)
            if "current" in data:
                tmp = CACHE + ".tmp"
                with open(tmp, "w") as f:
                    json.dump(data, f)
                os.replace(tmp, CACHE)
        except Exception:
            pass
    try:
        with open(CACHE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


# --- Icones dessinees -----------------------------------------------------
def _soleil(d, cx, cy, r, w):
    d.ellipse([cx - r * 0.45, cy - r * 0.45, cx + r * 0.45, cy + r * 0.45], outline=0, width=w)
    for k in range(8):
        a = k * math.pi / 4
        d.line([cx + math.cos(a) * r * 0.62, cy + math.sin(a) * r * 0.62,
                cx + math.cos(a) * r * 0.92, cy + math.sin(a) * r * 0.92], fill=0, width=w)


def _lune(d, cx, cy, r, w):
    d.ellipse([cx - r * 0.55, cy - r * 0.55, cx + r * 0.55, cy + r * 0.55], fill=0)
    d.ellipse([cx - r * 0.25, cy - r * 0.75, cx + r * 0.75, cy + r * 0.25], fill=1)


def _nuage(d, cx, cy, r, w, plein=False):
    """Nuage centre en (cx, cy), largeur ~2r."""
    remp = 0 if plein else 1
    boules = [(-0.55, 0.15, 0.42), (0.0, -0.15, 0.55), (0.55, 0.15, 0.42)]
    for bx, by, br in boules:
        d.ellipse([cx + (bx - br) * r, cy + (by - br) * r, cx + (bx + br) * r, cy + (by + br) * r],
                  fill=0)
    d.rectangle([cx - 0.55 * r, cy + 0.15 * r, cx + 0.55 * r, cy + 0.57 * r], fill=0)
    if not plein:
        e = w
        for bx, by, br in boules:
            d.ellipse([cx + (bx - br) * r + e, cy + (by - br) * r + e,
                       cx + (bx + br) * r - e, cy + (by + br) * r - e], fill=remp)
        d.rectangle([cx - 0.55 * r, cy + 0.15 * r + e, cx + 0.55 * r, cy + 0.57 * r - e],
                    fill=remp)


def icone(d, cx, cy, r, code, jour=True):
    w = max(2, int(r / 10))
    if code in (0, 1):
        (_soleil if jour else _lune)(d, cx, cy, r, w)
        return
    if code == 2:
        (_soleil if jour else _lune)(d, cx - r * 0.35, cy - r * 0.35, r * 0.7, w)
        _nuage(d, cx + r * 0.1, cy + r * 0.15, r * 0.8, w)
        return
    if code in (45, 48):
        for k in range(4):
            y = cy - r * 0.45 + k * r * 0.3
            d.line([cx - r * 0.8 + (k % 2) * r * 0.2, y, cx + r * 0.8 - (k % 2) * r * 0.2, y],
                   fill=0, width=w)
        return
    orage = code >= 95
    _nuage(d, cx, cy - r * 0.25, r * 0.85, w, plein=orage or code == 3 and False)
    if code == 3:
        return
    y0 = cy + r * 0.35
    if orage:
        p = [(cx + r * 0.05, y0), (cx - r * 0.2, y0 + r * 0.35), (cx + r * 0.05, y0 + r * 0.35),
             (cx - r * 0.15, y0 + r * 0.7)]
        d.line(p, fill=0, width=w + 1)
    elif code in (71, 73, 75, 77, 85, 86):
        for k in (-1, 0, 1):
            x, y = cx + k * r * 0.45, y0 + r * 0.25 + (k % 2) * r * 0.2
            for a in range(3):
                ang = a * math.pi / 3
                d.line([x - math.cos(ang) * r * 0.13, y - math.sin(ang) * r * 0.13,
                        x + math.cos(ang) * r * 0.13, y + math.sin(ang) * r * 0.13], fill=0, width=w)
    else:  # bruine / pluie / averses
        n = 2 if code in (51, 53, 55, 56, 57, 61) else 3
        for k in range(n):
            x = cx + (k - (n - 1) / 2) * r * 0.4
            d.line([x, y0, x - r * 0.15, y0 + r * 0.45], fill=0, width=w)


# --- Page -----------------------------------------------------------------
def dessiner(now=None):
    now = now or dt.datetime.now()
    img = Image.new("1", (WIDTH, HEIGHT), 1)
    d = ImageDraw.Draw(img)
    f_titre = police("sans-gras", 15)
    f_temp = police("sans-gras", 56)
    f_txt = police("sans", 16)
    f_petit = police("sans", 13)
    f_jour = police("sans-gras", 14)

    d.rectangle([0, 0, WIDTH, 24], fill=0)
    d.text((8, 3), f"Météo {VILLE}", font=f_titre, fill=1)
    h = now.strftime("%H:%M")
    d.text((WIDTH - 8 - d.textlength(h, font=f_titre), 3), h, font=f_titre, fill=1)

    data = donnees()
    if not data:
        msg = "Météo indisponible"
        d.text(((WIDTH - d.textlength(msg, font=f_titre)) / 2, 140), msg, font=f_titre, fill=0)
        return img

    c = data["current"]
    code = int(c.get("weather_code", 3))
    icone(d, 70, 92, 48, code, bool(c.get("is_day", 1)))
    t = f"{round(c['temperature_2m'])}°"
    d.text((140, 40), t, font=f_temp, fill=0)
    x_info = 150 + d.textlength(t, font=f_temp) + 10
    d.text((x_info, 46), f"ressenti {round(c['apparent_temperature'])}°", font=f_petit, fill=0)
    d.text((x_info, 66), f"vent {round(c['wind_speed_10m'])} km/h", font=f_petit, fill=0)
    d.text((x_info, 86), f"humidité {round(c['relative_humidity_2m'])} %", font=f_petit, fill=0)
    d.text((140, 116), LIBELLES.get(code, ""), font=f_txt, fill=0)

    d.line([10, 150, WIDTH - 10, 150], fill=0, width=1)

    j = data["daily"]
    n = min(5, len(j["time"]))
    larg = (WIDTH - 20) / n
    for i in range(n):
        x = 10 + i * larg
        cx = x + larg / 2
        jour = dt.date.fromisoformat(j["time"][i])
        lab = "Auj." if i == 0 else JOURS[jour.weekday()]
        d.text((cx - d.textlength(lab, font=f_jour) / 2, 158), lab, font=f_jour, fill=0)
        icone(d, cx, 205, 22, int(j["weather_code"][i]))
        tmax, tmin = round(j["temperature_2m_max"][i]), round(j["temperature_2m_min"][i])
        s = f"{tmin}° / {tmax}°"
        d.text((cx - d.textlength(s, font=f_petit) / 2, 240), s, font=f_petit, fill=0)
        p = j.get("precipitation_probability_max", [None] * n)[i]
        if p is not None:
            s = f"pluie {p} %"
            d.text((cx - d.textlength(s, font=f_petit) / 2, 260), s, font=f_petit, fill=0)
        if i:
            d.line([x, 160, x, 285], fill=0)
    return img


if __name__ == "__main__":
    dessiner().save("/tmp/meteo.png")
