"""Búsqueda de expedientes mediante soluciones iterativa y recursiva."""


def buscar_expediente_iterativo(codigos, codigo_buscado):
    """Devuelve el índice del código buscado o -1 si no existe."""
    for posicion in range(len(codigos)):
        if codigos[posicion] == codigo_buscado:
            return posicion
    return -1


def buscar_expediente_recursivo(codigos, codigo_buscado, posicion=0):
    """Devuelve recursivamente el índice del código buscado o -1."""
    # Caso base y condición de parada:
    if posicion >= len(codigos):
        return -1

    # Caso base y condición de parada: 
    if codigos[posicion] == codigo_buscado:
        return posicion

    # Caso recursivo: 
    return buscar_expediente_recursivo(codigos, codigo_buscado, posicion + 1)
