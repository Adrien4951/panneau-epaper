"""Pilote minimal pour l'ecran e-paper WeAct 4.2" (SSD1683, 400x300) sur Raspberry Pi.

Branchement : SCL->GPIO11, SDA->GPIO10, CS->GPIO8 (CE0), D/C->GPIO25, RES->GPIO17, BUSY->GPIO24.
"""
import time

import spidev
from gpiozero import DigitalInputDevice, DigitalOutputDevice

from reglages import cfg

WIDTH = 400
HEIGHT = 300


class EPD:
    def __init__(self, dc=cfg.PIN_DC, rst=cfg.PIN_RST, busy=cfg.PIN_BUSY, bus=0, device=0,
                 speed=4_000_000):
        self.dc = DigitalOutputDevice(dc)
        self.rst = DigitalOutputDevice(rst, initial_value=True)
        self.busy = DigitalInputDevice(busy, pull_up=False)
        self.spi = spidev.SpiDev()
        self.spi.open(bus, device)
        self.spi.max_speed_hz = speed
        self.spi.mode = 0

    # --- bas niveau -------------------------------------------------------
    def _cmd(self, c):
        self.dc.off()
        self.spi.writebytes([c])

    def _data(self, data):
        self.dc.on()
        if isinstance(data, int):
            data = [data]
        data = bytes(data)
        for i in range(0, len(data), 4096):
            self.spi.writebytes2(data[i:i + 4096])

    def _wait(self, minimum=0.0, timeout=30):
        """Attend la fin du travail de l'ecran.

        BUSY = 1 pendant le travail. Sur ce montage BUSY ne remonte pas toujours :
        on attend donc au moins `minimum` secondes dans tous les cas.
        """
        t0 = time.time()
        time.sleep(0.05)
        while self.busy.value:
            if time.time() - t0 > timeout:
                raise TimeoutError("L'ecran reste occupe (BUSY) : verifier le cablage")
            time.sleep(0.01)
        reste = minimum - (time.time() - t0)
        if reste > 0:
            time.sleep(reste)

    def _reset(self):
        self.rst.on(); time.sleep(0.1)
        self.rst.off(); time.sleep(0.002)
        self.rst.on(); time.sleep(0.1)

    # --- haut niveau ------------------------------------------------------
    def init(self):
        self._reset()
        self._wait(minimum=0.05)
        self._cmd(0x12)               # reset logiciel
        self._wait(minimum=0.2)
        self._cmd(0x01); self._data([(HEIGHT - 1) & 0xFF, (HEIGHT - 1) >> 8, 0x00])  # 300 lignes, balayage normal
        self._cmd(0x18); self._data(0x80)          # capteur de temperature interne (sinon image pale)
        self._cmd(0x21); self._data([0x40, 0x00])  # controle de mise a jour
        self._cmd(0x3C); self._data(0x05)          # bordure
        self._cmd(0x11); self._data(0x03)          # X+, Y+
        self._cmd(0x44); self._data([0x00, (WIDTH - 1) >> 3])
        self._cmd(0x45); self._data([0x00, 0x00, (HEIGHT - 1) & 0xFF, (HEIGHT - 1) >> 8])
        self._cmd(0x4E); self._data(0x00)
        self._cmd(0x4F); self._data([0x00, 0x00])
        self._wait()

    def _buffer(self, image):
        img = image.convert("1")
        if img.size != (WIDTH, HEIGHT):
            raise ValueError(f"Image attendue en {WIDTH}x{HEIGHT}, recue {img.size}")
        return img.tobytes()  # 1 bit/pixel, MSB d'abord, 1 = blanc

    def display(self, image):
        buf = self._buffer(image)
        self._cmd(0x4E); self._data(0x00)
        self._cmd(0x4F); self._data([0x00, 0x00])
        self._cmd(0x24); self._data(buf)   # RAM noir/blanc
        self._cmd(0x26); self._data(buf)   # RAM precedente (ou rouge sur la version 3 couleurs)
        self._cmd(0x22); self._data(0xF7)  # rafraichissement complet
        self._cmd(0x20)
        self._wait(minimum=cfg.ATTENTE_COMPLET)             # un rafraichissement complet dure ~3-4 s

    def display_partial(self, image, previous):
        """Rafraichissement partiel (~1 s, sans clignotement).

        `previous` = image actuellement affichee : l'ecran ne redessine que les differences.
        """
        new, old = self._buffer(image), self._buffer(previous)
        self._cmd(0x3C); self._data(0x80)          # bordure inchangee
        self._cmd(0x21); self._data([0x00, 0x00])  # utiliser les deux RAM (comparaison)
        self._cmd(0x4E); self._data(0x00)
        self._cmd(0x4F); self._data([0x00, 0x00])
        self._cmd(0x26); self._data(old)   # ancienne image
        self._cmd(0x4E); self._data(0x00)
        self._cmd(0x4F); self._data([0x00, 0x00])
        self._cmd(0x24); self._data(new)   # nouvelle image
        self._cmd(0x22); self._data(0xFF)  # mise a jour partielle
        self._cmd(0x20)
        self._wait(minimum=cfg.ATTENTE_PARTIEL)

    def clear(self):
        from PIL import Image
        self.display(Image.new("1", (WIDTH, HEIGHT), 1))

    def sleep(self):
        self._cmd(0x10); self._data(0x01)  # veille profonde (l'image reste affichee)
        time.sleep(0.1)
        self.spi.close()
        for d in (self.dc, self.rst, self.busy):
            d.close()
