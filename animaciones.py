"""Utilidades de animaci?n para la interfaz gr?fica."""

import tkinter as tk

from constantes import BG_CONTENIDO


def hex_a_rgb(color):
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def mezclar_colores(color_a, color_b, t):
    """Interpola entre dos colores hex. t=0 -> color_a, t=1 -> color_b."""
    ra, ga, ba = hex_a_rgb(color_a)
    rb, gb, bb = hex_a_rgb(color_b)
    r = int(ra + (rb - ra) * t)
    g = int(ga + (gb - ga) * t)
    b = int(ba + (bb - ba) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def fade_texto(widget, color_final, color_fondo=BG_CONTENIDO, pasos=12, intervalo=18):
    """Simula un fade-in cambiando el color del texto desde el fondo hasta su color final."""
    widget._fade_token = getattr(widget, "_fade_token", 0) + 1
    token = widget._fade_token

    def paso(i):
        if getattr(widget, "_fade_token", None) != token:
            return
        try:
            widget.configure(text_color=mezclar_colores(color_fondo, color_final, i / pasos))
        except tk.TclError:
            return
        if i < pasos:
            widget.after(intervalo, paso, i + 1)
    paso(0)


def deslizar_entrada(frame, desplazamiento=0.05, pasos=14, intervalo=15):
    """Desliza el frame desde la derecha hasta su posici?n (ease-out c?bico)."""
    def paso(i):
        try:
            if i >= pasos:
                frame.place_configure(relx=0)
                return
            t = i / pasos
            frame.place_configure(relx=desplazamiento * (1 - t) ** 3)
        except tk.TclError:
            return
        frame.after(intervalo, paso, i + 1)
    paso(0)
