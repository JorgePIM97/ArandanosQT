# ArandanosQT — Roadmap

> Plan de trabajo pendiente y evolución futura.  
> **Inicio de seguimiento formal:** 17/09/2026.

## Criterios

- Este archivo contiene trabajo **pendiente, propuesto o en evaluación**.
- Las funcionalidades ya implementadas se documentan en `development.md`.
- Cuando una tarea se complete, debe registrarse en `dev_log.csv` y retirarse o marcarse como completada aquí.

## Prioridad alta — Estabilización y distribución

### [ ] Validar el flujo operativo completo de cosecha

Realizar una prueba de extremo a extremo que cubra configuración de ubicación, recolector, check-in, reconocimiento, inicio de entrega, captura de múltiples cosechas, peso, calificación, fotografía, finalización de entrega, ticket y consulta posterior.

**Criterio de salida:** el flujo se completa sin inconsistencias de datos y los acumulados de entrega coinciden con las cosechas registradas.

### [ ] Formalizar pruebas del proyecto

Crear una estrategia de pruebas reproducibles para controladores y operaciones críticas de base de datos. Priorizar:

- creación/actualización de catálogos;
- registro de recolectores;
- check-in;
- inicio y cierre de entregas;
- registro de cosechas;
- cálculo de pesos y calificaciones;
- generación de reportes.

### [ ] Revisar rutas para el ejecutable

Eliminar o parametrizar rutas absolutas dependientes del equipo de desarrollo. Revisar especialmente:

- `ArandanosGPA.spec`;
- ruta de imágenes de cosecha;
- recursos externos que no estén compilados en Qt;
- rutas de modelos de reconocimiento facial.

### [ ] Definir almacenamiento persistente de imágenes

Revisar el uso de `C:\Program Files\ArandanosData\Imagenes_Cosechas`. Preferir una ubicación de datos escribible sin privilegios administrativos cuando sea compatible con la operación.

### [ ] Revisar manejo seguro de credenciales

Confirmar que `credenciales.json` no se versione ni se distribuya con credenciales reales. Evaluar protección adicional para contraseñas almacenadas localmente.

### [ ] Construir y probar versión distribuible

Generar el ejecutable mediante PyInstaller y probarlo en una computadora limpia que no tenga instalado el entorno Python del desarrollador.

**Validar:** interfaz, SQL Server/ODBC, cámaras, reconocimiento facial, báscula, impresora, exportación USB y persistencia de configuración.

## Prioridad media — Mantenibilidad

### [ ] Reducir responsabilidades de `main.py`

Evaluar la separación progresiva de lógica de navegación, dispositivos y módulos funcionales actualmente coordinados desde la clase principal, sin alterar el comportamiento del sistema.

### [ ] Homogeneizar manejo de errores y sesiones de BD

Definir un patrón común para apertura/cierre de sesiones, `commit`, `rollback`, mensajes de error y registro de excepciones.

### [ ] Agregar logging técnico de ejecución

Separar la bitácora de desarrollo (`dev_log.csv`) de un futuro log de ejecución de la aplicación para errores de cámara, báscula, impresora, SQL Server y reconocimiento facial.

### [ ] Revisar dependencias

Depurar `requirements.txt` para conservar únicamente dependencias necesarias en producción y documentar la versión de Python soportada.

### [ ] Mejorar documentación de instalación

Actualizar `README.md` con requisitos de Windows, ODBC, SQL Server, drivers de hardware, preparación de base de datos, configuración inicial y proceso de build/instalación.

## Prioridad media — Datos y reportes

### [ ] Validar reportes contra la base de datos

Crear casos de prueba con valores conocidos para comprobar vueltas, pesos y cantidades por calificación en reportes y tickets.

### [ ] Documentar consultas de negocio

Explicar las consultas SQL relevantes para sábana, cortes, resumen por cuadrillero y acumulados diarios.

### [ ] Definir política de respaldo

Establecer procedimiento de respaldo y restauración de la base de datos SQL Server y, si aplica, de las fotografías de cosecha.

## Prioridad baja — Evolución futura

### [ ] Evaluar instalador para Windows

Una vez estabilizado el ejecutable, evaluar un instalador que prepare carpetas, accesos directos y prerrequisitos necesarios.

### [ ] Evaluar configuración centralizada

Determinar si parámetros como impresora, puertos/dispositivos, rutas y opciones operativas deben administrarse desde una única configuración de aplicación.

## Próxima meta recomendada

Cerrar primero la fase de **documentación + estabilización**, y después realizar el build reproducible del ejecutable. La prioridad es comprobar que la versión distribuida conserva el mismo comportamiento que el entorno de desarrollo.
