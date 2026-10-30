"""Persistencia de expedientes en archivo de texto plano."""

import os
import re
from datetime import datetime

from constantes import FORMATO_FECHA

ARCHIVO_EXPEDIENTES = "expedientes.txt"
SEPARADOR = "|"


def formatear_expediente(codigo, dni, remitente, asunto, fecha, estado):
    """Formatea los datos del expediente en una sola l?nea delimitada por '|'.
    
    El orden de los campos debe coincidir con el de los arreglos paralelos.
    """
    return f"{codigo}|{dni}|{remitente}|{asunto}|{fecha}|{estado}\n"


def guardar_expediente_archivo(registro):
    """Escribe un nuevo registro de expediente al final del archivo."""
    with open(ARCHIVO_EXPEDIENTES, "a", encoding="utf-8") as archivo:
        archivo.write(formatear_expediente(*registro))


def reescribir_expedientes_archivo(codigos, dnis, remitentes, asuntos, fechas, estados):
    """Reescribe el archivo completo con los arreglos actuales (se usa al eliminar)."""
    temporal = ARCHIVO_EXPEDIENTES + ".tmp"
    with open(temporal, "w", encoding="utf-8") as archivo:
        for i in range(len(codigos)):
            archivo.write(formatear_expediente(codigos[i], dnis[i], remitentes[i],
                                               asuntos[i], fechas[i], estados[i]))
    os.replace(temporal, ARCHIVO_EXPEDIENTES)


# Rutina de validación de integridad de datos cargados desde archivo
def validar_registro_archivo(codigo, dni, remitente, asunto, fecha, estado):
    """Valida la estructura y los datos esenciales de un registro cargado."""
    codigo_valido = re.fullmatch(r"EXP-\d{4}-\d{3}", codigo) is not None
    dni_valido = dni.isdigit() and len(dni) == 8
    try:
        datetime.strptime(fecha, FORMATO_FECHA)
        fecha_valida = True
    except ValueError:
        fecha_valida = False
    estado_valido = bool(estado.strip())
    return codigo_valido and dni_valido and fecha_valida and estado_valido


def cargar_expedientes_archivo():
    """Lee el archivo plano y carga los datos en arreglos paralelos."""
    codigos, dnis, remitentes, asuntos, fechas, estados = [], [], [], [], [], []
    if os.path.exists(ARCHIVO_EXPEDIENTES):
        with open(ARCHIVO_EXPEDIENTES, "r", encoding="utf-8") as archivo:
            for linea in archivo:
                linea = linea.strip()
                if linea:
                    partes = linea.split(SEPARADOR)
                    if len(partes) == 6:
                        codigo, dni, remitente, asunto, fecha, estado = partes
                        if validar_registro_archivo(codigo, dni, remitente, asunto, fecha, estado):
                            codigos.append(codigo)
                            dnis.append(dni)
                            remitentes.append(remitente)
                            asuntos.append(asunto)
                            fechas.append(fecha)
                            estados.append(estado)
    return codigos, dnis, remitentes, asuntos, fechas, estados
