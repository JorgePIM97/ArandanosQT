Proyecto para el control de cosecha de arandanos de Raul y el licenciado Diego Sinhue.
-Interfaz grafica funcional

El proyecto tiene una arquitectura modelo vista controlador desarrollado usando el lenguaje de programación Python.
La interfaz se realizó utilizando el framework PyQt6 con ayuda del software QtDesigner.
En el archivo C:\ArandanosQT\db\data_connection\config_db.py se define la ruta del json donde se guardan las credenciales del servidor cada vez que se le asigna un servidor al cliente que en este caso es la app.
Es necesarioo tener el archivo .json para poder guardar las credenciales y hacer una correcta conexión con la db.

Crear carpeta C:\Program Files\ArandanosData\Imagenes_Cosechas para guardar las imagenes de las cosechas de los colectores

Hardware:
-PC con Windows 10
-2 Cámaras web c920 PRO HD WEBCAM
-Impresora termica para imprimir tickets ZKTECO Modelo ZKP8001
-Bascula Bascula Torrey L-EQ Series con soporte para conectar por USB

Para evitar que se traslape el explorador de archivos de la memoria USB al insertarla ir a Configuracion -> Dispositivos -> Reproducción Automatica -> Usar la reproducion automatica para todos los medios y dispositivos: DESACTIVADA
Unidad Extraíble: NO REALIZAR NINGUNA ACCIÓN
Tarjeta de memoria: NO REALIZAR NINGUNA ACCIÓN

Instalación driver impresora termica ZKTECO:   
1. Navegar a http://www.cnfujun.com/d/33
2. Elegir sistema operativo de la pc en este caso Windows
3. En Driver Setup and Config seleccionar impresora POS-80 Series Printer
4. Seleccionar USB Port Check y luego iniciar setup
5. Hacer prueba de impresión 