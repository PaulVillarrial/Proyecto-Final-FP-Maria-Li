# Mesa de Partes Digital

Aplicación de escritorio para registrar y administrar expedientes de una mesa de partes. Está desarrollada en Python con una interfaz gráfica en Tkinter/CustomTkinter y guarda la información en un archivo de texto local.

## Funcionalidades

- **Registrar expedientes**
  - Genera automáticamente un código con el formato `EXP-AAAA-NNN`.
  - Registra DNI, remitente y asunto.
  - Asigna la fecha y hora actuales.
  - Usa `RECIBIDO` como estado inicial.
- **Buscar expedientes** por código.
- **Listar expedientes** ordenados ascendentemente por código.
- **Administrar expedientes desde Buscar**
  - Edita únicamente el estado (`RECIBIDO`, `EN PROCESO`, `ATENDIDO` o `ARCHIVADO`).
  - Elimina expedientes después de una confirmación.
- Conserva los datos entre ejecuciones mediante `expedientes.txt`.
- Valida los registros cargados para evitar incorporar datos con formato inválido.

## Requisitos

- Python 3.10 o superior.
- Tkinter, incluido normalmente en las instalaciones de Python para Windows.
- Paquete [`customtkinter`](https://pypi.org/project/customtkinter/).

## Instalación

1. Clona o descarga este repositorio.
2. Abre una terminal en la carpeta del proyecto.
3. Instala la dependencia:

   ```bash
   python -m pip install customtkinter
   ```

## Ejecución

Desde la carpeta raíz del proyecto, ejecuta:

```bash
python main.py
```

La aplicación se abrirá con la vista **Registrar**. Para navegar, utiliza el menú lateral.

## Uso

### Registrar

Completa los campos **DNI**, **Remitente** y **Asunto**, y selecciona **Guardar expediente**. El DNI debe contener exactamente ocho dígitos. Los campos de texto no pueden estar vacíos; además, el carácter `|` se reemplaza por `/` para conservar la estructura del archivo.

### Buscar

Selecciona el tipo de búsqueda (Código, DNI, Remitente o Asunto), escribe el valor y selecciona **Buscar**. La búsqueda no distingue entre mayúsculas y minúsculas y muestra sugerencias mientras escribes.

La lógica de búsqueda está disponible en dos versiones para fines académicos:

- `buscar_expediente_iterativo()`: recorre la lista con un ciclo.
- `buscar_expediente_recursivo()`: revisa un expediente por llamada y avanza mediante llamadas recursivas.

Ambas funciones devuelven la posición del expediente encontrado o `-1` si no existe. La interfaz utiliza la versión iterativa para mantener el comportamiento original.

Cada resultado permite ver sus detalles, editar únicamente el estado o eliminar el expediente con confirmación. Los cambios de estado y las eliminaciones se guardan en `expedientes.txt`.

### Listar

Muestra todos los expedientes cargados en una tabla con código, DNI, remitente, asunto, fecha y estado.

## Persistencia de datos

Cada expediente ocupa una línea en `expedientes.txt` con el siguiente formato:

```text
codigo|dni|remitente|asunto|fecha|estado
```

La fecha se almacena como `AAAA-MM-DD HH:MM`. El archivo se crea automáticamente al guardar el primer expediente. Para conservar los registros, realiza una copia de seguridad de este archivo antes de mover o reinstalar el proyecto.

## Estructura principal

```text
.
├── main.py           # Punto de entrada de la aplicación
├── ui.py             # Ventanas, navegación y operaciones de usuario
├── busqueda.py       # Búsquedas iterativa y recursiva de expedientes
├── archivo.py        # Lectura y escritura de expedientes
├── validaciones.py   # Validación y limpieza de datos
├── codigos.py        # Generación de códigos correlativos
├── ordenamiento.py   # Ordenamiento de expedientes
├── constantes.py     # Configuración visual y formatos
├── animaciones.py    # Transiciones y efectos visuales
└── expedientes.txt   # Datos persistidos localmente
```

## Notas

- La aplicación utiliza un tema oscuro.
- Los datos se guardan en la carpeta desde la que se ejecuta `main.py`; por eso se recomienda ejecutar el comando desde la raíz del proyecto.
- No se requiere una base de datos externa ni conexión a internet para utilizar la aplicación después de instalar `customtkinter`.
