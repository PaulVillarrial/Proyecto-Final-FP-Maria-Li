"""Validaciones y limpieza de datos de entrada."""

from archivo import SEPARADOR


def validar_dni(dni):
    """Valida que el DNI contenga exactamente 8 d?gitos num?ricos."""
    return dni.isdigit() and len(dni) == 8


def validar_texto(texto):
    """Valida que la cadena no est? vac?a ni contenga solo espacios."""
    return len(texto.strip()) > 0


def limpiar_campo(texto):
    """Quita espacios sobrantes y evita que el separador '|' rompa el archivo."""
    return texto.strip().replace(SEPARADOR, "/")
