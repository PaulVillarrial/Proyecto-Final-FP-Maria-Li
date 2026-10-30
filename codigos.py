"""Generaci?n de c?digos correlativos."""

from datetime import datetime


def generar_codigo(codigos):
    """Genera el siguiente c?digo correlativo (ej. EXP-2026-006)."""
    anio = datetime.now().year
    ultimo_numero = 0
    if codigos:
        partes = codigos[-1].split("-")
        try:
            if len(partes) == 3 and int(partes[1]) == anio:
                ultimo_numero = int(partes[2])
        except ValueError:
            ultimo_numero = 0
    return f"EXP-{anio}-{ultimo_numero + 1:03d}"
