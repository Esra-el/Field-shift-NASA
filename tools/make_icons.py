"""Field Shift — genera los íconos PNG de la PWA desde el mismo diseño del SVG.

Produce (en frontend/icons/):
  icon-192.png, icon-512.png   -> purpose "any" (esquinas redondeadas)
  icon-maskable-512.png        -> purpose "maskable" (fondo a sangre + zona segura)

Ejecutar:  .venv/Scripts/python.exe ../tools/make_icons.py
(desde backend/, o ajustar la ruta de salida).
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "frontend" / "icons"

GREEN = (30, 77, 43, 255)        # #1e4d2b fondo (verde profundo)
SUN = (205, 232, 246, 255)       # #cde8f6 cielo
HILL = (62, 142, 65, 255)        # #3e8e41 colina
LEAF = (233, 247, 238, 255)      # #e9f7ee planta
GROUND = (167, 132, 90, 255)     # #a7845a tierra

BASE = 512  # el diseño está definido en un lienzo de 512x512


def _t(points, s, c=256):
    """Escala un conjunto de puntos alrededor del centro c (para zona segura)."""
    return [(c + (x - c) * s, c + (y - c) * s) for x, y in points]


def _draw_content(d: ImageDraw.ImageDraw, s: float) -> None:
    # Sol (círculo).
    cx, cy, r = 368, 150, 52
    sun = _t([(cx - r, cy - r), (cx + r, cy + r)], s)
    d.ellipse(sun, fill=SUN)

    # Colina.
    hill = _t([(96, 392), (180, 300), (256, 216), (332, 300), (416, 392)], s)
    d.polygon(hill, fill=HILL)

    # Planta (hoja clara vertical).
    leaf = _t([(256, 248), (274, 330), (256, 392), (238, 330)], s)
    d.polygon(leaf, fill=LEAF)

    # Barra de tierra.
    gb = _t([(96, 388), (416, 416)], s)
    d.rounded_rectangle([gb[0][0], gb[0][1], gb[1][0], gb[1][1]],
                        radius=14 * s, fill=GROUND)


def make(size: int, maskable: bool) -> Image.Image:
    img = Image.new("RGBA", (BASE, BASE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if maskable:
        # Fondo a sangre (sin esquinas transparentes) para cualquier máscara.
        d.rectangle([0, 0, BASE, BASE], fill=GREEN)
        _draw_content(d, 0.80)   # contenido dentro de la zona segura (~80%)
    else:
        d.rounded_rectangle([0, 0, BASE - 1, BASE - 1], radius=96, fill=GREEN)
        _draw_content(d, 1.0)
    if size != BASE:
        img = img.resize((size, size), Image.LANCZOS)
    return img


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    make(192, False).save(OUT / "icon-192.png")
    make(512, False).save(OUT / "icon-512.png")
    make(512, True).save(OUT / "icon-maskable-512.png")
    print("Íconos generados en", OUT)


if __name__ == "__main__":
    main()
