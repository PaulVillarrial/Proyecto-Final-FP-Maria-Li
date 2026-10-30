"""Ordenamiento de expedientes."""


def clave_codigo(codigo):
    """Convierte 'EXP-2026-005' en (2026, 5) para comparar num?ricamente."""
    partes = codigo.split("-")
    try:
        return int(partes[1]), int(partes[2])
    except (IndexError, ValueError):
        return 0, 0


def ordenar_burbuja(codigos):
    """Ordenamiento burbuja por c?digo. Devuelve la lista de ?ndices ordenados."""
    orden = list(range(len(codigos)))
    n = len(orden)
    for i in range(n - 1):
        for j in range(n - 1 - i):
            if clave_codigo(codigos[orden[j]]) > clave_codigo(codigos[orden[j + 1]]):
                orden[j], orden[j + 1] = orden[j + 1], orden[j]
    return orden
