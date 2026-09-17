# ArandanosQT — Documentación de desarrollo

> Documento técnico vivo del sistema de control de cosecha de arándanos.
>
> **Inicio de documentación formal:** 17/09/2026  
> La etapa previa se reconstruye a partir del código actual y de la planeación recordada por el desarrollador. No se asignan fechas históricas que no puedan comprobarse.

## 1. Descripción general

**ArandanosQT** es una aplicación de escritorio para Windows orientada al control operativo y trazabilidad de la cosecha de arándanos. Centraliza el registro de la estructura de cultivo, cuadrillas y recolectores, check-in, identificación mediante reconocimiento facial, pesaje y calificación de cosecha, control de entregas o vueltas, impresión de tickets y generación de reportes.

El proyecto está desarrollado principalmente en **Python** y **PyQt6**, con una arquitectura organizada en capas de vista, controlador y acceso/modelado de datos. La persistencia se realiza en **SQL Server** mediante **SQLAlchemy + pyodbc**.

## 2. Planeación inicial reconstruida

De acuerdo con la planeación original recordada, el proyecto comenzó con el siguiente orden conceptual:

1. Diseño de la base de datos de producción de arándanos.
2. Definición del flujo operativo del proceso.
3. Selección del framework y tecnologías de desarrollo.
4. Definición inicial de módulos:
   - CRUD de base de datos.
   - Cosecha.
   - Listados / check-in.
   - Resumen de cosecha.

La implementación evolucionó posteriormente para incorporar reconocimiento facial, cámaras, báscula, impresora térmica, exportación a Excel, control de entregas y configuración de conexión a base de datos, entre otras funciones.

## 3. Tecnologías principales

- **Python**: lenguaje principal.
- **PyQt6**: interfaz gráfica de escritorio.
- **Qt Designer**: diseño de interfaces `.ui`.
- **SQL Server**: base de datos relacional.
- **SQLAlchemy**: ORM y acceso a datos.
- **pyodbc / ODBC Driver 17 for SQL Server**: conexión con SQL Server.
- **OpenCV**: captura y procesamiento de imágenes de cámaras.
- **face_recognition / dlib**: codificación y reconocimiento facial.
- **scikit-learn**: soporte del reconocedor facial KNN.
- **pyserial**: comunicación serial con la báscula.
- **pywin32**: integración con impresora y dispositivos/unidades de Windows.
- **pandas / openpyxl**: generación y exportación de reportes Excel.
- **PyInstaller**: empaquetado de la aplicación para distribución en Windows.

## 4. Arquitectura del proyecto

```text
ArandanosQT/
├── main.py                     # Ventana principal y coordinación de la interfaz
├── controlador/                # Lógica de aplicación y dispositivos
│   ├── accesos/
│   ├── bascula/
│   ├── camaras/
│   ├── facialDetection/
│   ├── impresora/
│   ├── colectores.py
│   ├── cosechas.py
│   ├── cuadrilleros.py
│   ├── entregas.py
│   ├── checador.py
│   ├── fases.py
│   ├── tablas.py
│   ├── macrotuneles.py
│   ├── lineas.py
│   ├── modalidad.py
│   ├── vistas.py
│   ├── reportes_memoria.py
│   └── excel_generator.py
├── db/
│   ├── data_connection/        # Configuración de conexión
│   ├── entities/               # Modelos SQLAlchemy
│   └── queries/                # Scripts y consultas SQL
├── vista/
│   └── utils/
│       ├── plantillas/         # Interfaces Qt Designer y código generado
│       └── resources/          # Iconos, imágenes y recursos Qt
├── logs/
│   ├── development.md
│   ├── dev_log.csv
│   └── roadmap.md
└── ArandanosGPA.spec           # Configuración de PyInstaller
```

### Responsabilidad de las capas

**Vista:** contiene formularios, plantillas e imágenes utilizadas por PyQt6.  
**Controlador:** implementa operaciones de negocio, CRUD, cosecha, check-in, reportes y comunicación con hardware.  
**Datos:** contiene las entidades SQLAlchemy, conexión a SQL Server y scripts SQL.  
**`main.py`:** integra la interfaz con los controladores y coordina navegación, estados, validaciones y dispositivos.

## 5. Modelo de datos

Las entidades SQLAlchemy actualmente definidas son:

- `Fase`
- `Tabla`
- `Macrotunel`
- `Linea`
- `Modalidad`
- `Cuadrilla`
- `Recolector`
- `Entrega`
- `Cosecha`
- `RegistroCheck`
- `KeyModulos`
- `Usuario`

### 5.1 Estructura agrícola

La ubicación de producción sigue la jerarquía:

```text
FASE
  └── TABLA
       └── MACROTUNEL
            └── LINEA
```

Las cosechas y entregas se relacionan con una `LINEA`, permitiendo conservar información de trazabilidad sobre el lugar de producción.

### 5.2 Organización de personal

```text
CUADRILLA
  └── RECOLECTOR
```

Una cuadrilla contiene recolectores y almacena una clave, responsable y localidad. El recolector conserva datos personales operativos, fotografía, encoder facial, acceso y asociación con su cuadrilla.

### 5.3 Entregas y cosechas

Una `ENTREGA` representa una vuelta o agrupación de registros de cosecha de un recolector. Al iniciarse se registran recolector, línea, modalidad y fecha/hora de inicio. Al finalizarse se calcula el peso total de sus cosechas y la calificación predominante y se registra la fecha/hora final.

Cada `COSECHA` almacena, entre otros datos:

- peso;
- calificación;
- referencia de fotografía;
- fecha de transacción;
- recolector;
- línea;
- entrega;
- cuadrilla;
- modalidad.

### 5.4 Check-in

`REGISTRO_CHECK` registra la fecha/hora, recolector y modalidad asociados al check-in.

## 6. Flujo funcional de alto nivel

El flujo implementado se puede resumir así:

```text
Configuración / catálogos
        ↓
Cuadrillas y recolectores
        ↓
Check-in e identificación
        ↓
Configuración de cosecha
(Fase → Tabla → Macrotúnel → Línea + Modalidad)
        ↓
Reconocimiento / selección de recolector
        ↓
Inicio de entrega
        ↓
Captura de cosecha
(Peso + Calificación + Fotografía + Trazabilidad)
        ↓
Nuevas capturas dentro de la entrega
        ↓
Finalización de entrega
        ↓
Resumen / ticket / consulta / reporte
```

Este diagrama representa el flujo técnico observado en el código y deberá mantenerse actualizado cuando cambie la operación real.

## 7. Módulos funcionales

### 7.1 CRUD de estructura agrícola

Los controladores `fases.py`, `tablas.py`, `macrotuneles.py` y `lineas.py` permiten listar, crear, actualizar y eliminar los elementos que conforman la ubicación de cultivo.

### 7.2 Cuadrillas y recolectores

`cuadrilleros.py` administra las cuadrillas. `colectores.py` administra recolectores y permite almacenar o actualizar fotografía y encoder facial, además de sus datos operativos.

### 7.3 Reconocimiento facial

El directorio `controlador/facialDetection/` contiene la lógica de codificación y reconocimiento facial. El sistema utiliza trabajadores Qt para evitar bloquear la interfaz durante el procesamiento de cámara/reconocimiento.

### 7.4 Check-in

`checador.py` registra y consulta checks de recolectores asociados a una modalidad. La interfaz incorpora captura/reconocimiento para apoyar la identificación del recolector.

### 7.5 Cosecha

`cosechas.py` concentra el registro de cosecha. La operación integra recolector, peso, calificación, imagen, línea, entrega, modalidad y cuadrilla.

### 7.6 Entregas o vueltas

`entregas.py` inicia y finaliza entregas, calcula acumulados y obtiene resúmenes de recolectores. Una entrega agrupa múltiples registros de cosecha.

### 7.7 Báscula

`BasculaTorreyLPCR_USB` detecta un puerto serial compatible, abre comunicación a **9600 baud** y solicita el peso mediante el comando ASCII `P`. Incluye reintentos y procesamiento de la respuesta recibida.

### 7.8 Cámaras

El sistema contiene un administrador de conexión de cámaras y utiliza OpenCV para captura. Las cámaras participan en el registro/actualización de rostro, check-in, reconocimiento y evidencia de cosecha.

### 7.9 Impresora térmica

`TicketPrinter` detecta impresoras locales mediante palabras clave y envía contenido RAW usando las APIs de impresión de Windows. Existen tickets de vuelta y del día, con información de peso y calificaciones.

### 7.10 Listados, vistas y reportes

`vistas.py` y `reportes_memoria.py` realizan consultas de información operativa. Existen filtros por fechas y estructura de cultivo, así como resúmenes por cuadrillero/recolector.

### 7.11 Exportación Excel

`excel_generator.py` convierte tablas de la interfaz a `DataFrame` y permite exportarlas a Excel. También genera reportes por cuadrillero. La exportación detecta unidades USB removibles y escribe los archivos en ellas.

## 8. Configuración de base de datos

La conexión se construye dinámicamente desde:

```text
%APPDATA%\ArandanosGPA\credenciales.json
```

El archivo contiene los parámetros de servidor, base de datos, usuario y contraseña, y también puede almacenar el identificador del carrito.

La conexión utiliza:

```text
mssql+pyodbc
ODBC Driver 17 for SQL Server
```

Esta estrategia evita depender de una ruta escribible dentro del directorio de instalación del ejecutable.

> **Seguridad:** `credenciales.json` contiene información sensible y no debe versionarse ni distribuirse con credenciales reales. Debe revisarse el tratamiento de contraseñas antes de una distribución productiva.

## 9. Hardware identificado

El proyecto contempla actualmente:

- PC con Windows.
- Cámaras web Logitech C920 Pro HD o equivalentes compatibles con OpenCV.
- Báscula Torrey L-EQ Series mediante interfaz USB/serial.
- Impresora térmica ZKTeco ZKP8001 / POS-80 compatible.
- Memoria USB removible para exportación de reportes.

La disponibilidad de cámaras, báscula e impresora se comprueba desde la aplicación antes de determinadas operaciones.

## 10. Archivos generados y almacenamiento local

El README histórico indica el uso de:

```text
C:\Program Files\ArandanosData\Imagenes_Cosechas
```

para imágenes de cosecha. Esta ruta debe validarse antes de la distribución definitiva porque `Program Files` puede requerir permisos elevados para escritura.

La configuración de conexión, en cambio, ya se almacena bajo `%APPDATA%`, una ubicación adecuada para datos escribibles del usuario.

## 11. Empaquetado

Existe `ArandanosGPA.spec` para construir el ejecutable con PyInstaller. El archivo incorpora dependencias especiales de reconocimiento facial (`dlib`, `face_recognition`), `scikit-learn`, `pyqtgraph`, QR/barcode, SQL Server y componentes Win32.

El `.spec` contiene actualmente rutas absolutas de desarrollo como `C:\ArandanosQT` y una ruta fija al entorno virtual. Estas rutas funcionan para el entorno donde fueron configuradas, pero deberán revisarse si el build se realiza en otra computadora o ubicación.

## 12. Estado de documentación

Antes del 17/09/2026 no existía una bitácora formal de desarrollo. Por esta razón:

- los primeros hitos de `dev_log.csv` se identifican como **reconstrucción histórica**;
- no se inventarán fechas para funcionalidades anteriores;
- desde el 17/09/2026 los cambios nuevos deberán registrarse cronológicamente;
- `development.md` describe el estado técnico vigente;
- `roadmap.md` contiene únicamente trabajo pendiente o propuesto.

## 13. Convención de documentación futura

Para cada cambio significativo:

1. realizar el cambio en código;
2. probarlo;
3. registrar una entrada en `dev_log.csv`;
4. actualizar `development.md` si cambió el comportamiento o arquitectura;
5. actualizar `roadmap.md` si se completó, agregó o modificó un pendiente;
6. realizar el commit correspondiente en Git.

El objetivo es que código, historial y documentación permanezcan sincronizados.
