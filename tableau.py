"""Page « etat du serveur » (Raspberry Pi) pour l'ecran e-paper 4.2"."""
import datetime
import shutil
import socket
import subprocess

from PIL import Image, ImageDraw

from polices import police
from reglages import cfg

WIDTH, HEIGHT = 400, 300
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = ["janvier", "fevrier", "mars", "avril", "mai", "juin", "juillet", "aout",
        "septembre", "octobre", "novembre", "decembre"]


def ip_locale():
    """IP locale (connect() sur UDP choisit l'interface sans envoyer de paquet)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "?"
    finally:
        s.close()


def temperature():
    try:
        return int(open("/sys/class/thermal/thermal_zone0/temp").read()) / 1000
    except OSError:
        return None


def memoire():
    info = {}
    for line in open("/proc/meminfo"):
        k, v = line.split(":")
        info[k] = int(v.split()[0])
    total, dispo = info["MemTotal"], info["MemAvailable"]
    return (total - dispo) / 1024, total / 1024


def services():
    try:
        out = subprocess.run(["docker", "ps", "--format", "{{.Names}}"],
                             capture_output=True, text=True, timeout=10).stdout.split()
    except Exception:
        out = []
    return [(label, nom in out) for nom, label in cfg.SERVICES]


def disque(path):
    try:
        u = shutil.disk_usage(path)
        return u.used / 1e9, u.total / 1e9
    except OSError:
        return None


def barre(d, x, y, w, h, frac):
    d.rectangle([x, y, x + w, y + h], outline=0, width=2)
    frac = max(0.0, min(1.0, frac))
    if frac > 0:
        d.rectangle([x + 3, y + 3, x + 3 + int((w - 6) * frac), y + h - 3], fill=0)


def dessiner(now=None):
    img = Image.new("1", (WIDTH, HEIGHT), 1)
    d = ImageDraw.Draw(img)
    f_titre = police("sans-gras", 30)
    f_txt = police("sans", 18)
    f_petit = police("sans", 14)
    f_gras = police("sans-gras", 18)

    now = now or datetime.datetime.now()
    # Bandeau
    d.rectangle([0, 0, WIDTH, 52], fill=0)
    d.text((14, 9), now.strftime("%H:%M"), font=f_titre, fill=1)
    date = f"{JOURS[now.weekday()]} {now.day} {MOIS[now.month - 1]}"
    w = d.textlength(date, font=f_txt)
    d.text((WIDTH - 14 - w, 17), date, font=f_txt, fill=1)

    # Systeme
    y = 64
    t = temperature()
    used, total = memoire()
    d.text((14, y), "Raspberry Pi", font=f_gras, fill=0)
    d.text((170, y), ip_locale(), font=f_txt, fill=0)
    y += 28
    d.text((14, y), f"Temp. {t:.0f} C" if t is not None else "Temp. ?", font=f_txt, fill=0)
    d.text((170, y), f"RAM {used:.0f} / {total:.0f} Mo", font=f_txt, fill=0)

    # Stockage
    y += 36
    d.line([14, y - 8, WIDTH - 14, y - 8], fill=0, width=1)
    for label, path in cfg.DISQUES:
        u = disque(path)
        d.text((14, y), label, font=f_txt, fill=0)
        if u:
            barre(d, 130, y + 2, 170, 18, u[0] / u[1])
            d.text((310, y + 2), f"{u[0]:.1f}/{u[1]:.0f} Go", font=f_petit, fill=0)
        y += 30

    # Services
    y += 6
    d.line([14, y - 8, WIDTH - 14, y - 8], fill=0, width=1)
    x = 14
    for label, ok in services():
        r = 7
        cy = y + 11
        if ok:
            d.ellipse([x, cy - r, x + 2 * r, cy + r], fill=0)
        else:
            d.ellipse([x, cy - r, x + 2 * r, cy + r], outline=0, width=2)
        d.text((x + 2 * r + 6, y), label, font=f_txt, fill=0)
        x += 2 * r + 12 + int(d.textlength(label, font=f_txt)) + 14

    d.text((14, HEIGHT - 22), f"Mis a jour a {now:%H:%M}", font=f_petit, fill=0)
    return img


if __name__ == "__main__":
    from epd42 import EPD
    epd = EPD()
    try:
        epd.init()
        epd.display(dessiner())
    finally:
        epd.sleep()
