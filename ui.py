"""Interfaz gr?fica y l?gica de vistas."""

import tkinter as tk
import csv
from datetime import datetime
from tkinter import filedialog, ttk

import customtkinter as ctk

from animaciones import deslizar_entrada, fade_texto
from archivo import cargar_expedientes_archivo, guardar_expediente_archivo, reescribir_expedientes_archivo
from busqueda import buscar_expediente_iterativo
from codigos import generar_codigo
from constantes import (BG_CAMPO, BG_CONTENIDO, BG_SIDEBAR, BG_TARJETA, COLOR_ACENTO,
                         COLOR_ACENTO_HOVER, COLOR_ERROR, COLOR_EXITO, COLOR_TEXTO,
                         COLOR_TEXTO_SEC, ESTADO_INICIAL, FORMATO_FECHA)
from validaciones import limpiar_campo, validar_dni, validar_texto


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Tema: modo oscuro forzado ---
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Mesa de Partes Digital")
        self.geometry("1100x680")
        self.minsize(960, 600)
        self.configure(fg_color=BG_CONTENIDO)

        # --- Arreglos paralelos cargados desde el archivo al iniciar ---
        (self.codigos, self.dnis, self.remitentes,
         self.asuntos, self.fechas, self.estados) = cargar_expedientes_archivo()

        self.vista_actual = None
        self.botones_nav = {}

        self._configurar_estilo_tabla()
        self._construir_layout()
        self.mostrar_vista("registrar")
        self._fade_in_ventana()

    # -------------------------------------------------------------------------
    # Construcción del layout
    # -------------------------------------------------------------------------
    def _configurar_estilo_tabla(self):
        """Adapta ttk.Treeview al tema oscuro."""
        estilo = ttk.Style(self)
        estilo.theme_use("clam")
        estilo.configure(
            "Treeview",
            background=BG_TARJETA, foreground=COLOR_TEXTO,
            fieldbackground=BG_TARJETA, borderwidth=0,
            rowheight=34, font=("Segoe UI", 11),
        )
        estilo.configure(
            "Treeview.Heading",
            background=BG_CAMPO, foreground=COLOR_TEXTO,
            relief="flat", borderwidth=0, font=("Segoe UI", 11, "bold"),
            padding=(8, 8),
        )
        estilo.map("Treeview",
                   background=[("selected", COLOR_ACENTO)],
                   foreground=[("selected", "white")])
        estilo.map("Treeview.Heading", background=[("active", "#48484a")])

    def _construir_layout(self):
        """Crea el sidebar (izquierda) y el contenedor dinámico (derecha)."""
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ----- Sidebar -----
        self.sidebar = ctk.CTkFrame(self, width=230, corner_radius=0, fg_color=BG_SIDEBAR)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        ctk.CTkLabel(
            self.sidebar, text="Mesa de Partes",
            font=ctk.CTkFont("Segoe UI", 22, "bold"), text_color=COLOR_TEXTO,
        ).pack(anchor="w", padx=24, pady=(36, 0))
        ctk.CTkLabel(
            self.sidebar, text="Municipalidad · Digital",
            font=ctk.CTkFont("Segoe UI", 12), text_color=COLOR_TEXTO_SEC,
        ).pack(anchor="w", padx=24, pady=(0, 32))

        opciones = [("registrar", "Registrar"), ("buscar", "Buscar"), ("listar", "Listar")]
        for clave, texto in opciones:
            boton = ctk.CTkButton(
                self.sidebar, text=texto, anchor="w", height=42, corner_radius=10,
                font=ctk.CTkFont("Segoe UI", 14, "bold"),
                fg_color="transparent", hover_color=BG_TARJETA, text_color=COLOR_TEXTO,
                command=lambda c=clave: self.mostrar_vista(c),
            )
            boton.pack(fill="x", padx=16, pady=4)
            self.botones_nav[clave] = boton

        self.lbl_total = ctk.CTkLabel(
            self.sidebar, text="", font=ctk.CTkFont("Segoe UI", 12),
            text_color=COLOR_TEXTO_SEC,
        )
        self.lbl_total.pack(side="bottom", anchor="w", padx=24, pady=24)
        self._actualizar_total()

        # ----- Contenedor principal (las vistas cambian aquí) -----
        self.contenedor = ctk.CTkFrame(self, corner_radius=0, fg_color=BG_CONTENIDO)
        self.contenedor.grid(row=0, column=1, sticky="nsew")

    def _fade_in_ventana(self):
        """Aparición suave de la ventana al iniciar."""
        try:
            self.attributes("-alpha", 0.0)
        except tk.TclError:
            return

        def paso(i):
            try:
                self.attributes("-alpha", min(i / 12, 1.0))
            except tk.TclError:
                return
            if i < 12:
                self.after(18, paso, i + 1)

        paso(0)

    def _actualizar_total(self):
        self.lbl_total.configure(text=f"{len(self.codigos)} expedientes registrados")

    # -------------------------------------------------------------------------
    # Navegación entre vistas
    # -------------------------------------------------------------------------
    def mostrar_vista(self, nombre):
        """Cambia la vista actual con una transición de deslizamiento + fade."""
        # Resaltar el botón activo del sidebar
        for clave, boton in self.botones_nav.items():
            boton.configure(fg_color=COLOR_ACENTO if clave == nombre else "transparent")

        # Destruir la vista anterior
        if self.vista_actual is not None:
            self.vista_actual.destroy()

        # Crear la nueva vista (empieza un poco desplazada a la derecha)
        self.vista_actual = ctk.CTkFrame(self.contenedor, corner_radius=0, fg_color=BG_CONTENIDO)
        self.vista_actual.place(relx=0.05, rely=0, relwidth=1, relheight=1)

        constructores = {
            "registrar": self.vista_registrar,
            "buscar": self.vista_buscar,
            "listar": self.vista_listar,
        }
        constructores[nombre](self.vista_actual)
        deslizar_entrada(self.vista_actual)

    def _encabezado(self, padre, titulo, subtitulo):
        """Título y subtítulo comunes a todas las vistas (con fade-in)."""
        lbl_titulo = ctk.CTkLabel(
            padre, text=titulo, font=ctk.CTkFont("Segoe UI", 30, "bold"),
            text_color=BG_CONTENIDO,
        )
        lbl_titulo.pack(anchor="w", padx=44, pady=(40, 0))
        lbl_sub = ctk.CTkLabel(
            padre, text=subtitulo, font=ctk.CTkFont("Segoe UI", 14),
            text_color=BG_CONTENIDO,
        )
        lbl_sub.pack(anchor="w", padx=44, pady=(2, 24))
        fade_texto(lbl_titulo, COLOR_TEXTO)
        fade_texto(lbl_sub, COLOR_TEXTO_SEC)

    def mostrar_mensaje(self, etiqueta, texto, exito):
        """Muestra feedback en verde (éxito) o rojo (error) con fade-in. Sin messagebox."""
        etiqueta.configure(text=texto)
        fade_texto(etiqueta, COLOR_EXITO if exito else COLOR_ERROR)

    # -------------------------------------------------------------------------
    # VISTA 1: REGISTRAR
    # -------------------------------------------------------------------------
    def vista_registrar(self, padre):
        self._encabezado(padre, "Registrar expediente",
                         "Complete los datos del remitente para generar un nuevo expediente.")

        tarjeta = ctk.CTkFrame(padre, corner_radius=16, fg_color=BG_TARJETA)
        tarjeta.pack(fill="x", padx=44)

        def campo(texto):
            ctk.CTkLabel(
                tarjeta, text=texto, font=ctk.CTkFont("Segoe UI", 12, "bold"),
                text_color=COLOR_TEXTO_SEC,
            ).pack(anchor="w", padx=28, pady=(18, 4))
            entrada = ctk.CTkEntry(
                tarjeta, height=40, corner_radius=10, border_width=0,
                fg_color=BG_CAMPO, font=ctk.CTkFont("Segoe UI", 14),
            )
            entrada.pack(fill="x", padx=28)
            return entrada

        # Código automático: Entry deshabilitado (solo lectura)
        self.entry_codigo = campo("CÓDIGO (automático)")
        self._poner_codigo(generar_codigo(self.codigos))

        self.entry_dni = campo("DNI")
        self.entry_remitente = campo("REMITENTE")
        self.entry_asunto = campo("ASUNTO")

        ctk.CTkButton(
            tarjeta, text="Guardar expediente", height=42, corner_radius=10,
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            fg_color=COLOR_ACENTO, hover_color=COLOR_ACENTO_HOVER,
            command=self.guardar_expediente,
        ).pack(anchor="w", padx=28, pady=24)

        # Etiqueta de retroalimentación (debajo del formulario)
        self.lbl_msg_registrar = ctk.CTkLabel(
            padre, text="", font=ctk.CTkFont("Segoe UI", 14, "bold"),
            text_color=BG_CONTENIDO,
        )
        self.lbl_msg_registrar.pack(anchor="w", padx=44, pady=14)

        # Enter en el último campo también guarda
        self.entry_asunto.bind("<Return>", lambda e: self.guardar_expediente())

    def _poner_codigo(self, codigo):
        """Escribe el código en el Entry readonly (se habilita solo un instante)."""
        self.entry_codigo.configure(state="normal")
        self.entry_codigo.delete(0, "end")
        self.entry_codigo.insert(0, codigo)
        self.entry_codigo.configure(state="disabled")

    def guardar_expediente(self):
        """Valida el formulario, guarda en memoria y en archivo, y limpia los campos."""
        dni = self.entry_dni.get().strip()
        remitente = limpiar_campo(self.entry_remitente.get())
        asunto = limpiar_campo(self.entry_asunto.get())

        # Validaciones (se muestran en la etiqueta, no en ventanas emergentes)
        if not validar_dni(dni):
            self.mostrar_mensaje(self.lbl_msg_registrar,
                                 "Error: el DNI debe tener exactamente 8 dígitos numéricos.", False)
            return
        if not validar_texto(remitente):
            self.mostrar_mensaje(self.lbl_msg_registrar,
                                 "Error: el remitente no puede estar vacío.", False)
            return
        if not validar_texto(asunto):
            self.mostrar_mensaje(self.lbl_msg_registrar,
                                 "Error: el asunto no puede estar vacío.", False)
            return

        # Datos automáticos
        codigo = generar_codigo(self.codigos)
        fecha = datetime.now().strftime(FORMATO_FECHA)
        estado = ESTADO_INICIAL

        # Guardar en los arreglos paralelos (memoria)
        self.codigos.append(codigo)
        self.dnis.append(dni)
        self.remitentes.append(remitente)
        self.asuntos.append(asunto)
        self.fechas.append(fecha)
        self.estados.append(estado)

        # Guardar en el archivo (persistencia)
        try:
            guardar_expediente_archivo((codigo, dni, remitente, asunto, fecha, estado))
        except OSError as error:
            # Revertir memoria si el archivo falla, para mantener todo sincronizado
            for lista in (self.codigos, self.dnis, self.remitentes,
                          self.asuntos, self.fechas, self.estados):
                lista.pop()
            self.mostrar_mensaje(self.lbl_msg_registrar,
                                 f"Error al guardar en el archivo: {error}", False)
            return

        # Limpiar formulario y preparar el siguiente código
        for entrada in (self.entry_dni, self.entry_remitente, self.entry_asunto):
            entrada.delete(0, "end")
        self._poner_codigo(generar_codigo(self.codigos))
        self._actualizar_total()
        self.mostrar_mensaje(self.lbl_msg_registrar,
                             f"Expediente {codigo} registrado correctamente.", True)

    # -------------------------------------------------------------------------
    # VISTA 2: BUSCAR
    # -------------------------------------------------------------------------
    def vista_buscar(self, padre):
        self._encabezado(padre, "Buscar expediente",
                         "Filtre por código, DNI, remitente o asunto.")
        self._configurar_controles_busqueda(padre)

    def _configurar_controles_busqueda(self, padre):
        self.tipo_busqueda = ctk.StringVar(value="Código")
        barra = ctk.CTkFrame(padre, fg_color="transparent")
        barra.pack(fill="x", padx=44)
        barra.grid_columnconfigure(1, weight=1)

        self.menu_busqueda = ctk.CTkOptionMenu(
            barra, values=["Código", "DNI", "Remitente", "Asunto"],
            variable=self.tipo_busqueda, width=145, height=42,
            corner_radius=10, fg_color=BG_TARJETA, button_color=BG_CAMPO,
            button_hover_color="#48484a", font=ctk.CTkFont("Segoe UI", 13),
            command=self._cambiar_tipo_busqueda,
        )
        self.menu_busqueda.grid(row=0, column=0, padx=(0, 10), sticky="w")

        self.entry_buscar = ctk.CTkEntry(
            barra, height=42, corner_radius=10, border_width=0, fg_color=BG_TARJETA,
            placeholder_text="EXP-2026-001", font=ctk.CTkFont("Segoe UI", 14),
        )
        self.entry_buscar.grid(row=0, column=1, sticky="ew")
        self.entry_buscar.bind("<Return>", lambda e: self.buscar_expediente())
        self.entry_buscar.bind("<KeyRelease>", self._actualizar_sugerencias)

        ctk.CTkButton(
            barra, text="Buscar", width=120, height=42, corner_radius=10,
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            fg_color=COLOR_ACENTO, hover_color=COLOR_ACENTO_HOVER,
            command=self.buscar_expediente,
        ).grid(row=0, column=2, padx=(10, 0), sticky="e")

        self.sugerencias = ctk.CTkFrame(padre, fg_color=BG_TARJETA, corner_radius=10)
        self.sugerencias.pack(fill="x", padx=44, pady=(6, 0))
        self.sugerencias.pack_forget()

        self.lbl_msg_buscar = ctk.CTkLabel(
            padre, text="", font=ctk.CTkFont("Segoe UI", 14, "bold"),
            text_color=BG_CONTENIDO,
        )
        self.lbl_msg_buscar.pack(anchor="w", padx=44, pady=(10, 0))

        self.resultado = ctk.CTkScrollableFrame(
            padre, corner_radius=16, fg_color=BG_CONTENIDO,
            scrollbar_button_color=BG_CAMPO,
            scrollbar_button_hover_color="#48484a",
        )
        self.resultado.pack(fill="both", expand=True, padx=44, pady=(8, 28))
        self.resultado.grid_columnconfigure(0, weight=1)
        self.detalle_busqueda = None

    def _cambiar_tipo_busqueda(self, tipo):
        placeholders = {
            "Código": "EXP-2026-001",
            "DNI": "56781234",
            "Remitente": "José Juan",
            "Asunto": "SUNAT",
        }
        self.entry_buscar.delete(0, "end")
        self.sugerencias.pack_forget()
        self.entry_buscar.configure(placeholder_text=placeholders[tipo])
        self._actualizar_sugerencias()

    def _valores_sugerencias(self):
        indice = {"Código": 0, "DNI": 1, "Remitente": 2, "Asunto": 3}
        campo = indice[self.tipo_busqueda.get()]
        listas = (self.codigos, self.dnis, self.remitentes, self.asuntos)
        return list(dict.fromkeys(listas[campo]))

    def _validar_entrada_busqueda(self, texto):
        if not validar_texto(texto):
            return "Ingrese un valor para buscar."
        if self.tipo_busqueda.get() == "DNI":
            if not texto.isdigit():
                return "El DNI debe contener únicamente dígitos numéricos."
            if len(texto) != 8:
                return "El DNI debe tener exactamente 8 dígitos."
        return ""

    def _actualizar_sugerencias(self, _evento=None):
        texto = self.entry_buscar.get().strip().casefold()
        for widget in self.sugerencias.winfo_children():
            widget.destroy()

        if not texto:
            self.sugerencias.pack_forget()
            return

        coincidencias = [
            valor for valor in self._valores_sugerencias()
            if texto in valor.casefold()
        ][:6]
        if not coincidencias:
            self.sugerencias.pack_forget()
            return

        for valor in coincidencias:
            ctk.CTkButton(
                self.sugerencias, text=valor, anchor="w", height=30,
                fg_color="transparent", hover_color=BG_CAMPO,
                text_color=COLOR_TEXTO, font=ctk.CTkFont("Segoe UI", 12),
                command=lambda valor=valor: self._elegir_sugerencia(valor),
            ).pack(fill="x", padx=6, pady=2)
        self.sugerencias.pack(fill="x", padx=44, pady=(6, 0), before=self.lbl_msg_buscar)

    def _elegir_sugerencia(self, valor):
        self.entry_buscar.delete(0, "end")
        self.entry_buscar.insert(0, valor)
        self.sugerencias.pack_forget()
        self.buscar_expediente()

    def buscar_expediente(self):
        """Busca coincidencias y muestra primero sus tarjetas compactas."""
        texto = self.entry_buscar.get().strip()

        for widget in self.resultado.winfo_children():
            widget.destroy()
        self.sugerencias.pack_forget()
        self.detalle_busqueda = None

        error = self._validar_entrada_busqueda(texto)
        if error:
            self.mostrar_mensaje(self.lbl_msg_buscar, error, False)
            return

        campo = {"Código": 0, "DNI": 1, "Remitente": 2, "Asunto": 3}[self.tipo_busqueda.get()]
        listas = (self.codigos, self.dnis, self.remitentes, self.asuntos)
        valor_buscado = texto.casefold()
        posiciones = [
            posicion for posicion, valor in enumerate(listas[campo])
            if valor_buscado in valor.casefold()
        ]
        if not posiciones:
            self.mostrar_mensaje(self.lbl_msg_buscar,
                                 f"No se encontraron expedientes para “{texto}”.", False)
            return

        self.lbl_msg_buscar.configure(text="")
        self._pintar_resultados_compactos(posiciones)

    def _pintar_resultados_compactos(self, posiciones):
        encabezado = ctk.CTkLabel(
            self.resultado, text=f"{len(posiciones)} resultado(s)",
            anchor="w", font=ctk.CTkFont("Segoe UI", 13, "bold"),
            text_color=COLOR_TEXTO_SEC,
        )
        encabezado.grid(row=0, column=0, sticky="ew", padx=16, pady=(10, 6))

        for fila, posicion in enumerate(posiciones, start=1):
            tarjeta = ctk.CTkFrame(
                self.resultado, height=54, corner_radius=12, fg_color=BG_TARJETA,
            )
            tarjeta.grid(row=fila, column=0, sticky="ew", padx=8, pady=4)
            tarjeta.grid_propagate(False)
            tarjeta.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                tarjeta, text=self.codigos[posicion], width=130, anchor="w",
                font=ctk.CTkFont("Segoe UI", 12, "bold"), text_color=COLOR_TEXTO,
            ).grid(row=0, column=0, padx=(14, 8), sticky="w")
            resumen = f"{self.remitentes[posicion]}  •  {self.dnis[posicion]}  •  {self.asuntos[posicion]}"
            ctk.CTkLabel(
                tarjeta, text=resumen, anchor="w", text_color=COLOR_TEXTO_SEC,
                font=ctk.CTkFont("Segoe UI", 12),
            ).grid(row=0, column=1, padx=8, sticky="ew")
            self._crear_badge(tarjeta, self.estados[posicion]).grid(
                row=0, column=2, padx=8, sticky="e",
            )
            ctk.CTkButton(
                tarjeta, text="Ver detalles", width=106, height=32, corner_radius=8,
                fg_color=BG_CAMPO, hover_color="#48484a",
                font=ctk.CTkFont("Segoe UI", 12, "bold"),
                command=lambda posicion=posicion: self._mostrar_detalles_busqueda(posicion),
            ).grid(row=0, column=3, padx=(4, 12), sticky="e")
            ctk.CTkButton(
                tarjeta, text="Editar estado", width=108, height=32, corner_radius=8,
                fg_color=BG_CAMPO, hover_color="#48484a",
                font=ctk.CTkFont("Segoe UI", 12, "bold"),
                command=lambda posicion=posicion: self._mostrar_detalles_busqueda(
                    posicion, True
                ),
            ).grid(row=0, column=4, padx=(0, 4), sticky="e")
            ctk.CTkButton(
                tarjeta, text="Eliminar", width=88, height=32, corner_radius=8,
                fg_color=COLOR_ERROR, hover_color="#ff6961",
                font=ctk.CTkFont("Segoe UI", 12, "bold"),
                command=lambda posicion=posicion: self._confirmar_eliminacion(
                    self.codigos[posicion]
                ),
            ).grid(row=0, column=5, padx=(0, 12), sticky="e")

    def _crear_badge(self, padre, estado):
        return ctk.CTkLabel(
            padre, text=estado, width=90, height=26, corner_radius=8,
            fg_color=COLOR_EXITO if estado == "RECIBIDO" else COLOR_ACENTO,
            text_color="#102016", font=ctk.CTkFont("Segoe UI", 11, "bold"),
        )

    def _mostrar_detalles_busqueda(self, posicion, editar_estado=False):
        for widget in self.resultado.winfo_children():
            widget.destroy()

        self.detalle_busqueda = ctk.CTkFrame(
            self.resultado, corner_radius=18, fg_color=BG_TARJETA,
        )
        self.detalle_busqueda.grid(row=0, column=0, sticky="ew", padx=16, pady=16)
        self.detalle_busqueda.grid_columnconfigure(1, weight=1)

        cabecera = ctk.CTkFrame(self.detalle_busqueda, fg_color="transparent")
        cabecera.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 8))
        cabecera.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            cabecera, text=self.codigos[posicion], anchor="w",
            font=ctk.CTkFont("Segoe UI", 24, "bold"), text_color=COLOR_TEXTO,
        ).grid(row=0, column=0, sticky="w")
        self._crear_badge(cabecera, self.estados[posicion]).grid(row=0, column=1, sticky="e")

        detalles = [
            ("👤", "Remitente", self.remitentes[posicion]),
            ("🪪", "DNI", self.dnis[posicion]),
            ("📝", "Asunto", self.asuntos[posicion]),
            ("📅", "Fecha", self.fechas[posicion]),
        ]
        for fila, (icono, titulo, valor) in enumerate(detalles, start=1):
            ctk.CTkLabel(
                self.detalle_busqueda, text=icono, width=28,
                font=ctk.CTkFont("Segoe UI", 16),
            ).grid(row=fila, column=0, sticky="w", padx=(28, 4), pady=9)
            contenido = ctk.CTkFrame(self.detalle_busqueda, fg_color="transparent")
            contenido.grid(row=fila, column=1, sticky="ew", padx=(8, 28), pady=7)
            ctk.CTkLabel(
                contenido, text=titulo.upper(), anchor="w",
                font=ctk.CTkFont("Segoe UI", 10, "bold"), text_color=COLOR_TEXTO_SEC,
            ).pack(anchor="w")
            ctk.CTkLabel(
                contenido, text=valor, anchor="w", wraplength=650,
                font=ctk.CTkFont("Segoe UI", 15), text_color=COLOR_TEXTO,
            ).pack(anchor="w")

        estado = ctk.CTkFrame(self.detalle_busqueda, fg_color="transparent")
        estado.grid(row=5, column=0, columnspan=2, sticky="ew", padx=28, pady=(8, 4))
        ctk.CTkLabel(
            estado, text="ESTADO", anchor="w",
            font=ctk.CTkFont("Segoe UI", 10, "bold"), text_color=COLOR_TEXTO_SEC,
        ).pack(anchor="w")
        if editar_estado:
            selector_estado = ctk.CTkOptionMenu(
                estado, values=["RECIBIDO", "EN PROCESO", "ATENDIDO", "ARCHIVADO"],
                width=190, height=36, corner_radius=9,
                fg_color=BG_CAMPO, button_color=BG_CAMPO,
                button_hover_color="#48484a", font=ctk.CTkFont("Segoe UI", 13),
            )
            selector_estado.set(self.estados[posicion])
            selector_estado.pack(side="left", pady=(5, 0))
            ctk.CTkButton(
                estado, text="Guardar", width=110, height=36, corner_radius=9,
                fg_color=COLOR_ACENTO, hover_color=COLOR_ACENTO_HOVER,
                font=ctk.CTkFont("Segoe UI", 12, "bold"),
                command=lambda: self._guardar_estado(posicion, selector_estado.get()),
            ).pack(side="left", padx=(10, 0), pady=(5, 0))
        else:
            self._crear_badge(estado, self.estados[posicion]).pack(anchor="w", pady=(5, 0))

        ctk.CTkButton(
            self.detalle_busqueda, text="← Volver a resultados", width=170,
            height=36, corner_radius=9, fg_color=BG_CAMPO,
            hover_color="#48484a", font=ctk.CTkFont("Segoe UI", 12, "bold"),
            command=self._volver_a_resultados,
        ).grid(row=6, column=0, columnspan=2, sticky="w", padx=28, pady=(16, 24))

    def _guardar_estado(self, posicion, nuevo_estado):
        anterior = self.estados[posicion]
        self.estados[posicion] = nuevo_estado
        try:
            reescribir_expedientes_archivo(
                self.codigos, self.dnis, self.remitentes,
                self.asuntos, self.fechas, self.estados,
            )
        except OSError as error:
            self.estados[posicion] = anterior
            self.mostrar_mensaje(self.lbl_msg_buscar,
                                 f"Error al actualizar el archivo: {error}", False)
            return

        codigo = self.codigos[posicion]
        self.buscar_expediente()
        self.mostrar_mensaje(
            self.lbl_msg_buscar,
            f"Estado de {codigo} actualizado correctamente.",
            True,
        )

    def _volver_a_resultados(self):
        if self.detalle_busqueda is not None:
            self.detalle_busqueda.destroy()
            self.detalle_busqueda = None
        self.buscar_expediente()

    # -------------------------------------------------------------------------
    # VISTA 3: LISTAR
    # -------------------------------------------------------------------------
    def vista_listar(self, padre):
        self._encabezado(padre, "Listado de expedientes",
                         "Filtre los expedientes y ordénelos según sus necesidades.")

        self.filtro_estado = ctk.StringVar(value="Todos los estados")
        self.orden_campo = ctk.StringVar(value="Código")
        self.orden_direccion = ctk.StringVar(value="Ascendente")
        self.mostrar_todos = ctk.BooleanVar(value=False)

        filtros = ctk.CTkFrame(padre, corner_radius=14, fg_color=BG_TARJETA)
        filtros.pack(fill="x", padx=44, pady=(0, 8))
        filtros.grid_columnconfigure(1, weight=1)
        filtros.grid_columnconfigure(3, weight=1)

        ctk.CTkCheckBox(
            filtros, text="Mostrar todos", variable=self.mostrar_todos,
            command=self._alternar_mostrar_todos, font=ctk.CTkFont("Segoe UI", 12),
            text_color=COLOR_TEXTO,
        ).grid(row=0, column=0, padx=(16, 10), pady=(14, 8), sticky="w")
        ctk.CTkLabel(
            filtros, text="Estado", text_color=COLOR_TEXTO_SEC,
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
        ).grid(row=0, column=1, padx=8, pady=(14, 8), sticky="e")
        self.filtro_estado_menu = ctk.CTkOptionMenu(
            filtros, variable=self.filtro_estado,
            values=["Todos los estados", "RECIBIDO", "EN PROCESO", "ATENDIDO", "ARCHIVADO"],
            width=155, height=34, corner_radius=8, fg_color=BG_CAMPO,
            button_color=BG_CAMPO, button_hover_color="#48484a",
            command=lambda _: self._actualizar_listado(),
        )
        self.filtro_estado_menu.grid(row=0, column=2, padx=(0, 16), pady=(14, 8))

        ctk.CTkLabel(
            filtros, text="Remitente", text_color=COLOR_TEXTO_SEC,
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
        ).grid(row=1, column=0, padx=(16, 8), pady=6, sticky="e")
        self.filtro_remitente = ctk.CTkEntry(
            filtros, height=34, corner_radius=8, border_width=0,
            fg_color=BG_CAMPO, placeholder_text="Contiene...",
        )
        self.filtro_remitente.grid(row=1, column=1, padx=8, pady=6, sticky="ew")
        self.filtro_remitente.bind("<KeyRelease>", lambda _: self._actualizar_listado())

        ctk.CTkLabel(
            filtros, text="Asunto", text_color=COLOR_TEXTO_SEC,
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
        ).grid(row=1, column=2, padx=(8, 4), pady=6, sticky="e")
        self.filtro_asunto = ctk.CTkEntry(
            filtros, height=34, corner_radius=8, border_width=0,
            fg_color=BG_CAMPO, placeholder_text="Contiene...",
        )
        self.filtro_asunto.grid(row=1, column=3, padx=(4, 16), pady=6, sticky="ew")
        self.filtro_asunto.bind("<KeyRelease>", lambda _: self._actualizar_listado())

        ctk.CTkLabel(
            filtros, text="Fecha desde", text_color=COLOR_TEXTO_SEC,
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
        ).grid(row=2, column=0, padx=(16, 8), pady=(6, 14), sticky="e")
        self.filtro_fecha_desde = ctk.CTkEntry(
            filtros, height=34, corner_radius=8, border_width=0,
            fg_color=BG_CAMPO, placeholder_text="AAAA-MM-DD",
        )
        self.filtro_fecha_desde.grid(row=2, column=1, padx=8, pady=(6, 14), sticky="ew")
        self.filtro_fecha_desde.bind("<KeyRelease>", lambda _: self._actualizar_listado())

        ctk.CTkLabel(
            filtros, text="Fecha hasta", text_color=COLOR_TEXTO_SEC,
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
        ).grid(row=2, column=2, padx=(8, 4), pady=(6, 14), sticky="e")
        self.filtro_fecha_hasta = ctk.CTkEntry(
            filtros, height=34, corner_radius=8, border_width=0,
            fg_color=BG_CAMPO, placeholder_text="AAAA-MM-DD",
        )
        self.filtro_fecha_hasta.grid(row=2, column=3, padx=(4, 16), pady=(6, 14), sticky="ew")
        self.filtro_fecha_hasta.bind("<KeyRelease>", lambda _: self._actualizar_listado())

        orden = ctk.CTkFrame(padre, corner_radius=14, fg_color=BG_TARJETA)
        orden.pack(fill="x", padx=44, pady=(0, 8))
        ctk.CTkLabel(
            orden, text="Ordenar por", text_color=COLOR_TEXTO_SEC,
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
        ).pack(side="left", padx=(16, 8), pady=10)
        ctk.CTkOptionMenu(
            orden, variable=self.orden_campo, values=["Código", "Fecha", "Remitente"],
            width=130, height=34, corner_radius=8, fg_color=BG_CAMPO,
            button_color=BG_CAMPO, button_hover_color="#48484a",
            command=lambda _: self._actualizar_listado(),
        ).pack(side="left", pady=10)
        ctk.CTkOptionMenu(
            orden, variable=self.orden_direccion, values=["Ascendente", "Descendente"],
            width=135, height=34, corner_radius=8, fg_color=BG_CAMPO,
            button_color=BG_CAMPO, button_hover_color="#48484a",
            command=lambda _: self._actualizar_listado(),
        ).pack(side="left", padx=8, pady=10)
        ctk.CTkButton(
            orden, text="Exportar reporte", width=145, height=34, corner_radius=8,
            fg_color=COLOR_ACENTO, hover_color=COLOR_ACENTO_HOVER,
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            command=self._exportar_reporte,
        ).pack(side="right", padx=16, pady=10)

        self.lbl_estadisticas = ctk.CTkLabel(
            padre, text="", anchor="w", justify="left",
            font=ctk.CTkFont("Segoe UI", 12), text_color=COLOR_TEXTO_SEC,
        )
        self.lbl_estadisticas.pack(fill="x", padx=44, pady=(2, 6))

        self.resultado_listar = ctk.CTkScrollableFrame(
            padre, corner_radius=16, fg_color=BG_CONTENIDO,
            scrollbar_button_color=BG_CAMPO,
            scrollbar_button_hover_color="#48484a",
        )
        self.resultado_listar.pack(fill="both", expand=True, padx=44, pady=(0, 28))
        self.resultado_listar.grid_columnconfigure(0, weight=1)
        self._actualizar_listado()

    def _alternar_mostrar_todos(self):
        if self.mostrar_todos.get():
            self.filtro_estado.set("Todos los estados")
            for entrada in (self.filtro_remitente, self.filtro_asunto,
                            self.filtro_fecha_desde, self.filtro_fecha_hasta):
                entrada.delete(0, "end")
        self._actualizar_listado()

    def _obtener_listado_filtrado(self):
        desde_texto = self.filtro_fecha_desde.get().strip()
        hasta_texto = self.filtro_fecha_hasta.get().strip()
        desde = hasta = None
        if desde_texto:
            desde = datetime.strptime(desde_texto, "%Y-%m-%d")
        if hasta_texto:
            hasta = datetime.strptime(hasta_texto, "%Y-%m-%d").replace(
                hour=23, minute=59
            )
        if desde and hasta and desde > hasta:
            raise ValueError("La fecha desde no puede ser posterior a la fecha hasta.")

        remitente = self.filtro_remitente.get().strip().casefold()
        asunto = self.filtro_asunto.get().strip().casefold()
        posiciones = []
        for posicion, fecha_texto in enumerate(self.fechas):
            fecha = datetime.strptime(fecha_texto, FORMATO_FECHA)
            if not self.mostrar_todos.get():
                if (self.filtro_estado.get() != "Todos los estados"
                        and self.estados[posicion] != self.filtro_estado.get()):
                    continue
                if remitente and remitente not in self.remitentes[posicion].casefold():
                    continue
                if asunto and asunto not in self.asuntos[posicion].casefold():
                    continue
                if desde and fecha < desde:
                    continue
                if hasta and fecha > hasta:
                    continue
            posiciones.append(posicion)

        campo = {"Código": self.codigos, "Fecha": self.fechas,
                 "Remitente": self.remitentes}[self.orden_campo.get()]
        posiciones.sort(key=lambda posicion: campo[posicion].casefold()
                       if isinstance(campo[posicion], str) else campo[posicion])
        if self.orden_direccion.get() == "Descendente":
            posiciones.reverse()
        return posiciones

    def _actualizar_listado(self):
        for widget in self.resultado_listar.winfo_children():
            widget.destroy()
        try:
            posiciones = self._obtener_listado_filtrado()
        except ValueError as error:
            self.lbl_estadisticas.configure(text=f"Error: {error}", text_color=COLOR_ERROR)
            return

        conteo = {estado: 0 for estado in
                  ("RECIBIDO", "EN PROCESO", "ATENDIDO", "ARCHIVADO")}
        for posicion in posiciones:
            conteo[self.estados[posicion]] = conteo.get(self.estados[posicion], 0) + 1
        estadisticas = "Resultados encontrados: " + str(len(posiciones))
        estadisticas += "    |    " + "    ".join(
            f"{estado}: {conteo[estado]}" for estado in conteo
        )
        self.lbl_estadisticas.configure(text=estadisticas, text_color=COLOR_TEXTO_SEC)

        for fila, posicion in enumerate(posiciones):
            self._crear_tarjeta_listado(fila, posicion)

    def _crear_tarjeta_listado(self, fila, posicion):
        tarjeta = ctk.CTkFrame(
            self.resultado_listar, height=74, corner_radius=12, fg_color=BG_TARJETA,
        )
        tarjeta.grid(row=fila, column=0, sticky="ew", padx=8, pady=4)
        tarjeta.grid_propagate(False)
        tarjeta.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            tarjeta, text=self.codigos[posicion], width=130, anchor="w",
            font=ctk.CTkFont("Segoe UI", 12, "bold"), text_color=COLOR_TEXTO,
        ).grid(row=0, column=0, padx=(14, 8), sticky="w")
        contenido = (
            f"{self.dnis[posicion]}  •  {self.remitentes[posicion]}  •  "
            f"{self.asuntos[posicion]}  •  {self.fechas[posicion]}"
        )
        ctk.CTkLabel(
            tarjeta, text=contenido, anchor="w", text_color=COLOR_TEXTO_SEC,
            font=ctk.CTkFont("Segoe UI", 12), wraplength=650,
        ).grid(row=0, column=1, padx=8, sticky="ew")
        self._crear_badge(tarjeta, self.estados[posicion]).grid(
            row=0, column=2, padx=(8, 14), sticky="e",
        )

    def _exportar_reporte(self):
        try:
            posiciones = self._obtener_listado_filtrado()
        except ValueError as error:
            self.lbl_estadisticas.configure(text=f"Error: {error}", text_color=COLOR_ERROR)
            return
        ruta = filedialog.asksaveasfilename(
            title="Exportar reporte", defaultextension=".csv",
            initialfile="reporte.csv",
            filetypes=[("Archivo CSV", "*.csv"), ("Archivo de texto", "*.txt")],
        )
        if not ruta:
            return
        try:
            with open(ruta, "w", newline="", encoding="utf-8-sig") as reporte:
                escritor = csv.writer(reporte)
                escritor.writerow(["Código", "DNI", "Remitente", "Asunto", "Fecha", "Estado"])
                for posicion in posiciones:
                    escritor.writerow([
                        self.codigos[posicion], self.dnis[posicion],
                        self.remitentes[posicion], self.asuntos[posicion],
                        self.fechas[posicion], self.estados[posicion],
                    ])
        except OSError as error:
            self.lbl_estadisticas.configure(
                text=f"Error al exportar el reporte: {error}", text_color=COLOR_ERROR
            )
            return
        self.lbl_estadisticas.configure(
            text=f"Reporte exportado correctamente: {ruta}",
            text_color=COLOR_EXITO,
        )


    def _buscar_posicion(self, codigo):
        """Devuelve el índice del código usando la búsqueda iterativa."""
        return buscar_expediente_iterativo(self.codigos, codigo)

    def _confirmar_eliminacion(self, codigo):
        dialogo = ctk.CTkToplevel(self)
        dialogo.title("Confirmar eliminación")
        dialogo.geometry("420x190")
        dialogo.resizable(False, False)
        dialogo.transient(self)
        dialogo.grab_set()
        dialogo.configure(fg_color=BG_CONTENIDO)

        ctk.CTkLabel(
            dialogo, text=f"¿Está seguro de eliminar el expediente {codigo}?",
            font=ctk.CTkFont("Segoe UI", 15, "bold"),
            text_color=COLOR_TEXTO, wraplength=360,
        ).pack(padx=28, pady=(34, 24))

        botones = ctk.CTkFrame(dialogo, fg_color="transparent")
        botones.pack()
        ctk.CTkButton(
            botones, text="Cancelar", width=110, height=36, corner_radius=9,
            fg_color=BG_CAMPO, hover_color="#48484a",
            command=dialogo.destroy,
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            botones, text="Eliminar", width=110, height=36, corner_radius=9,
            fg_color=COLOR_ERROR, hover_color="#ff6961",
            command=lambda: self._confirmar_y_eliminar(dialogo, codigo),
        ).pack(side="left", padx=6)

    def _confirmar_y_eliminar(self, dialogo, codigo):
        dialogo.destroy()
        self.eliminar_expediente(codigo)

    def eliminar_expediente(self, codigo):
        """Quita el registro de los arreglos paralelos y reescribe el archivo."""
        posicion = self._buscar_posicion(codigo)
        if posicion == -1:
            self.mostrar_mensaje(self.lbl_msg_buscar,
                                 f"El expediente {codigo} ya no existe.", False)
            return

        listas = (self.codigos, self.dnis, self.remitentes,
                  self.asuntos, self.fechas, self.estados)
        registro = [lista.pop(posicion) for lista in listas]

        try:
            reescribir_expedientes_archivo(*listas)
        except OSError as error:
            # Revertir la memoria si el archivo no pudo actualizarse
            for lista, valor in zip(listas, registro):
                lista.insert(posicion, valor)
            self.mostrar_mensaje(self.lbl_msg_buscar,
                                 f"Error al actualizar el archivo: {error}", False)
            return

        self._actualizar_total()
        self.buscar_expediente()
        self.mostrar_mensaje(self.lbl_msg_buscar,
                             f"Expediente {codigo} eliminado correctamente.", True)


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================
