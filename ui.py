"""Interfaz gr?fica y l?gica de vistas."""

import tkinter as tk
from datetime import datetime
from tkinter import ttk

import customtkinter as ctk

from animaciones import deslizar_entrada, fade_texto
from archivo import cargar_expedientes_archivo, guardar_expediente_archivo, reescribir_expedientes_archivo
from codigos import generar_codigo
from constantes import (BG_CAMPO, BG_CONTENIDO, BG_SIDEBAR, BG_TARJETA, COLOR_ACENTO,
                         COLOR_ACENTO_HOVER, COLOR_ERROR, COLOR_EXITO, COLOR_TEXTO,
                         COLOR_TEXTO_SEC, ESTADO_INICIAL, FORMATO_FECHA)
from ordenamiento import ordenar_burbuja
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

        opciones = [("registrar", "Registrar"), ("buscar", "Buscar"), ("listar", "Listar"), ("eliminar", "Eliminar")]
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
            "eliminar": self.vista_eliminar,
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
                         "Ingrese el código del expediente (ej. EXP-2026-001).")

        barra = ctk.CTkFrame(padre, fg_color="transparent")
        barra.pack(fill="x", padx=44)

        self.entry_buscar = ctk.CTkEntry(
            barra, height=42, corner_radius=10, border_width=0, fg_color=BG_TARJETA,
            placeholder_text="EXP-2026-001", font=ctk.CTkFont("Segoe UI", 14),
        )
        self.entry_buscar.pack(side="left", fill="x", expand=True)
        self.entry_buscar.bind("<Return>", lambda e: self.buscar_expediente())

        ctk.CTkButton(
            barra, text="Buscar", width=120, height=42, corner_radius=10,
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            fg_color=COLOR_ACENTO, hover_color=COLOR_ACENTO_HOVER,
            command=self.buscar_expediente,
        ).pack(side="left", padx=(12, 0))

        # Mensaje de "no encontrado" (rojo) debajo de la barra
        self.lbl_msg_buscar = ctk.CTkLabel(
            padre, text="", font=ctk.CTkFont("Segoe UI", 14, "bold"),
            text_color=BG_CONTENIDO,
        )
        self.lbl_msg_buscar.pack(anchor="w", padx=44, pady=(12, 0))

        # Zona donde se pintan los detalles
        self.resultado = ctk.CTkFrame(padre, corner_radius=16, fg_color=BG_CONTENIDO)
        self.resultado.pack(fill="x", padx=44, pady=12)

    def buscar_expediente(self):
        """Busca el código en los arreglos paralelos y muestra los detalles."""
        codigo = self.entry_buscar.get().strip().upper()

        # Limpiar resultado anterior
        for widget in self.resultado.winfo_children():
            widget.destroy()
        self.resultado.configure(fg_color=BG_CONTENIDO)

        if not validar_texto(codigo):
            self.mostrar_mensaje(self.lbl_msg_buscar, "Ingrese un código para buscar.", False)
            return

        # Búsqueda secuencial
        posicion = -1
        for i in range(len(self.codigos)):
            if self.codigos[i] == codigo:
                posicion = i
                break

        if posicion == -1:
            self.mostrar_mensaje(self.lbl_msg_buscar,
                                 f"No se encontró el expediente {codigo}.", False)
            return

        self.lbl_msg_buscar.configure(text="")
        self.resultado.configure(fg_color=BG_TARJETA)

        self._pintar_detalles(self.resultado, posicion)

    def _pintar_detalles(self, contenedor, posicion):
        """Dibuja los datos de un expediente en una tarjeta (aparición escalonada)."""
        detalles = [
            ("CÓDIGO", self.codigos[posicion]),
            ("DNI", self.dnis[posicion]),
            ("REMITENTE", self.remitentes[posicion]),
            ("ASUNTO", self.asuntos[posicion]),
            ("FECHA", self.fechas[posicion]),
            ("ESTADO", self.estados[posicion]),
        ]

        for indice, (titulo, valor) in enumerate(detalles):
            ctk.CTkLabel(
                contenedor, text=titulo, font=ctk.CTkFont("Segoe UI", 12, "bold"),
                text_color=COLOR_TEXTO_SEC,
            ).grid(row=indice, column=0, sticky="nw", padx=(28, 20), pady=10)

            if titulo == "ESTADO":
                # El estado se muestra como una "píldora" de color
                lbl_valor = ctk.CTkLabel(
                    contenedor, text=valor, corner_radius=8, fg_color=COLOR_ACENTO,
                    font=ctk.CTkFont("Segoe UI", 13, "bold"), text_color=BG_TARJETA,
                    width=110, height=28,
                )
            else:
                lbl_valor = ctk.CTkLabel(
                    contenedor, text=valor, anchor="w", justify="left",
                    wraplength=560, font=ctk.CTkFont("Segoe UI", 15),
                    text_color=BG_TARJETA,
                )
            lbl_valor.grid(row=indice, column=1, sticky="w", pady=10, padx=(0, 28))

            # Aparición escalonada de cada fila (efecto fluido)
            if titulo == "ESTADO":
                lbl_valor.configure(text_color=BG_CONTENIDO)
            else:
                self.after(indice * 70, fade_texto, lbl_valor, COLOR_TEXTO, BG_TARJETA)

        # Margen inferior dentro de la tarjeta
        contenedor.grid_rowconfigure(len(detalles), minsize=10)

    # -------------------------------------------------------------------------
    # VISTA 3: LISTAR
    # -------------------------------------------------------------------------
    def vista_listar(self, padre):
        self._encabezado(padre, "Listado de expedientes",
                         "Ordenados por código de forma ascendente.")

        tarjeta = ctk.CTkFrame(padre, corner_radius=16, fg_color=BG_TARJETA)
        tarjeta.pack(fill="both", expand=True, padx=44, pady=(0, 36))
        tarjeta.grid_rowconfigure(0, weight=1)
        tarjeta.grid_columnconfigure(0, weight=1)

        columnas = ("codigo", "dni", "remitente", "asunto", "fecha", "estado")
        encabezados = ("Código", "DNI", "Remitente", "Asunto", "Fecha", "Estado")
        anchos = (130, 90, 190, 260, 140, 100)

        tabla = ttk.Treeview(tarjeta, columns=columnas, show="headings", selectmode="browse")
        for col, texto, ancho in zip(columnas, encabezados, anchos):
            tabla.heading(col, text=texto)
            tabla.column(col, width=ancho, minwidth=70, anchor="w")
        tabla.tag_configure("impar", background="#262628")
        tabla.grid(row=0, column=0, sticky="nsew", padx=(12, 0), pady=12)

        scroll = ctk.CTkScrollbar(tarjeta, command=tabla.yview)
        scroll.grid(row=0, column=1, sticky="ns", padx=(4, 8), pady=12)
        tabla.configure(yscrollcommand=scroll.set)

        # Ordenar con burbuja y cargar filas con aparición progresiva
        orden = ordenar_burbuja(self.codigos)
        filas = [
            (self.codigos[i], self.dnis[i], self.remitentes[i],
             self.asuntos[i], self.fechas[i], self.estados[i])
            for i in orden
        ]
        self._insertar_filas(tabla, filas, 0)

    def _insertar_filas(self, tabla, filas, inicio):
        """Inserta las filas por lotes pequeños para simular una carga fluida."""
        lote = max(1, len(filas) // 40)
        try:
            for k in range(inicio, min(inicio + lote, len(filas))):
                etiqueta = ("impar",) if k % 2 else ()
                tabla.insert("", "end", values=filas[k], tags=etiqueta)
        except tk.TclError:
            return  # La vista cambió mientras se cargaba
        if inicio + lote < len(filas):
            tabla.after(15, self._insertar_filas, tabla, filas, inicio + lote)


    # -------------------------------------------------------------------------
    # VISTA 4: ELIMINAR
    # -------------------------------------------------------------------------
    def vista_eliminar(self, padre):
        self._encabezado(padre, "Eliminar expediente",
                         "Busque el expediente por su código y confirme para eliminarlo.")

        barra = ctk.CTkFrame(padre, fg_color="transparent")
        barra.pack(fill="x", padx=44)

        self.entry_eliminar = ctk.CTkEntry(
            barra, height=42, corner_radius=10, border_width=0, fg_color=BG_TARJETA,
            placeholder_text="EXP-2026-001", font=ctk.CTkFont("Segoe UI", 14),
        )
        self.entry_eliminar.pack(side="left", fill="x", expand=True)
        self.entry_eliminar.bind("<Return>", lambda e: self.buscar_para_eliminar())

        ctk.CTkButton(
            barra, text="Buscar", width=120, height=42, corner_radius=10,
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            fg_color=COLOR_ACENTO, hover_color=COLOR_ACENTO_HOVER,
            command=self.buscar_para_eliminar,
        ).pack(side="left", padx=(12, 0))

        # Mensajes de error / éxito (sin ventanas emergentes)
        self.lbl_msg_eliminar = ctk.CTkLabel(
            padre, text="", font=ctk.CTkFont("Segoe UI", 14, "bold"),
            text_color=BG_CONTENIDO,
        )
        self.lbl_msg_eliminar.pack(anchor="w", padx=44, pady=(12, 0))

        # Tarjeta con los detalles y la confirmación
        self.resultado_eliminar = ctk.CTkFrame(padre, corner_radius=16, fg_color=BG_CONTENIDO)
        self.resultado_eliminar.pack(fill="x", padx=44, pady=12)

    def _buscar_posicion(self, codigo):
        """Búsqueda secuencial: devuelve el índice del código o -1 si no existe."""
        for i in range(len(self.codigos)):
            if self.codigos[i] == codigo:
                return i
        return -1

    def _limpiar_resultado_eliminar(self):
        try:
            for widget in self.resultado_eliminar.winfo_children():
                widget.destroy()
            self.resultado_eliminar.configure(fg_color=BG_CONTENIDO)
        except tk.TclError:
            pass  # La vista ya cambió

    def buscar_para_eliminar(self):
        """Muestra el expediente encontrado y pide confirmación antes de borrarlo."""
        codigo = self.entry_eliminar.get().strip().upper()
        self._limpiar_resultado_eliminar()

        if not validar_texto(codigo):
            self.mostrar_mensaje(self.lbl_msg_eliminar, "Ingrese un código para buscar.", False)
            return

        posicion = self._buscar_posicion(codigo)
        if posicion == -1:
            self.mostrar_mensaje(self.lbl_msg_eliminar,
                                 f"No se encontró el expediente {codigo}.", False)
            return

        self.lbl_msg_eliminar.configure(text="")
        self.resultado_eliminar.configure(fg_color=BG_TARJETA)
        self._pintar_detalles(self.resultado_eliminar, posicion)

        # Zona de confirmación (reemplaza al messagebox)
        confirmacion = ctk.CTkFrame(self.resultado_eliminar, fg_color="transparent")
        confirmacion.grid(row=7, column=0, columnspan=2, sticky="w", padx=28, pady=(0, 24))

        ctk.CTkLabel(
            confirmacion, text=f"¿Eliminar {codigo}? Esta acción no se puede deshacer.",
            font=ctk.CTkFont("Segoe UI", 13, "bold"), text_color=COLOR_ERROR,
        ).pack(anchor="w", pady=(0, 10))

        botones = ctk.CTkFrame(confirmacion, fg_color="transparent")
        botones.pack(anchor="w")
        ctk.CTkButton(
            botones, text="Confirmar eliminación", height=40, corner_radius=10,
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            fg_color=COLOR_ERROR, hover_color="#ff6961",
            command=lambda: self.eliminar_expediente(codigo),
        ).pack(side="left")
        ctk.CTkButton(
            botones, text="Cancelar", height=40, corner_radius=10,
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            fg_color=BG_CAMPO, hover_color="#48484a",
            command=self._cancelar_eliminacion,
        ).pack(side="left", padx=(12, 0))

    def _cancelar_eliminacion(self):
        self.lbl_msg_eliminar.configure(text="")
        self.after(120, self._limpiar_resultado_eliminar)

    def eliminar_expediente(self, codigo):
        """Quita el registro de los arreglos paralelos y reescribe el archivo."""
        posicion = self._buscar_posicion(codigo)
        if posicion == -1:
            self.mostrar_mensaje(self.lbl_msg_eliminar,
                                 f"El expediente {codigo} ya no existe.", False)
            self.after(120, self._limpiar_resultado_eliminar)
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
            self.mostrar_mensaje(self.lbl_msg_eliminar,
                                 f"Error al actualizar el archivo: {error}", False)
            return

        self.entry_eliminar.delete(0, "end")
        self._actualizar_total()
        self.after(120, self._limpiar_resultado_eliminar)
        self.mostrar_mensaje(self.lbl_msg_eliminar,
                             f"Expediente {codigo} eliminado correctamente.", True)


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================
