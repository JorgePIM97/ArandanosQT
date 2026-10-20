#controlador/cosechas.py
import cv2
import face_recognition
import numpy as np
from io import BytesIO
from datetime import datetime
from db.entities.data_entities import Recolector, Cosecha, get_db, Macrotunel, Entrega, Linea
from sqlalchemy import text  
from collections import Counter
from controlador.bascula.bascula_connection import BasculaTorreyLPCR_USB
from sqlalchemy import func, cast, Date
import os

def cargar_empleados_desde_db():
    session = get_db()
    try:
        empleados = session.query(
            Recolector.id_Recolector, 
            Recolector.Nombre_Completo, 
            Recolector.Encoder
        ).filter(Recolector.Encoder.isnot(None)).all()
        
        known_encodings = []
        class_names = []
        empleados_info = []
        
        for id_recolector, nombre, encoding_bytes in empleados:
            try:
                encoding = np.load(BytesIO(encoding_bytes), allow_pickle=True)
                known_encodings.append(encoding)
                class_names.append(nombre)
                empleados_info.append((id_recolector, nombre))
            except Exception as e:
                print(f"Error al cargar encoding para {nombre}: {str(e)}")
                continue
        
        return known_encodings, class_names, empleados_info
    except Exception as e:
        print(f"Error al cargar empleados: {str(e)}")
        return [], [], []
    finally:
        session.close()

# def registrar_cosecha(id_recolector, peso, calificacion, frame_cosecha, id_macrotunel, id_entrega=None):
#     session = get_db()
#     try:
#         # Convertir frame a JPEG
#         success, img_encoded = cv2.imencode('.jpg', frame_cosecha)
#         if not success:
#             return False, "Error al codificar la imagen"
            
#         img_bytes = img_encoded.tobytes()
        
#         # Generar clave única
#         clave = f"COS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
#         # Crear registro de cosecha (sin Fecha_Registro ya que se auto-genera)
#         nueva_cosecha = Cosecha(
#             Clave=clave,
#             Peso=peso,
#             Calificacion=calificacion,
#             Foto_Cosecha=img_bytes,
#             id_Recolector=id_recolector,
#             id_Macrotunel=id_macrotunel,
#             id_Entrega=id_entrega
#         )
        
#         session.add(nueva_cosecha)
#         session.commit()
        
#         return True, f"Cosecha registrada con ID: {nueva_cosecha.id_Cosecha}"
        
#     except Exception as e:
#         session.rollback()
#         return False, f"Error al registrar cosecha: {str(e)}"
#     finally:
#         session.close()

def registrar_cosecha(id_recolector, peso, calificacion, frame_cosecha, id_linea, id_entrega, id_modalidad, id_cuadrilla=None):
    session = get_db()
    try:
         # Cambiar a una ruta local en lugar de OneDrive
        ruta_imagenes = "C:\\ArandanosGPA\\Imagenes_Cosechas"
        #ruta_imagenes = "C:&ArandanosGPA/Imagenes_Cosechas" # Ruta para ejecutable

        # Crear el directorio si no existe
        try:
            os.makedirs(ruta_imagenes, exist_ok=True)
            if not os.path.isdir(ruta_imagenes):
                raise Exception(f"No se pudo crear/validar el directorio: {ruta_imagenes}")
        except Exception as dir_error:
            # Si falla, intentar en el directorio temporal
            ruta_imagenes = os.path.join(os.environ['TEMP'], 'Cosechas')
            os.makedirs(ruta_imagenes, exist_ok=True)
        
        # Generar nombre único para la imagen
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_imagen = f"cos_{id_recolector}_{timestamp}_{calificacion}.jpg"
        ruta_completa = os.path.join(ruta_imagenes, nombre_imagen)
        
        # Verificar y convertir el frame si es necesario
        if frame_cosecha is None:
            raise ValueError("Frame de imagen es None")
            
        if len(frame_cosecha.shape) == 2:  # Si es escala de grises
            frame_cosecha = cv2.cvtColor(frame_cosecha, cv2.COLOR_GRAY2BGR)
        elif frame_cosecha.shape[2] == 4:  # Si tiene canal alpha
            frame_cosecha = cv2.cvtColor(frame_cosecha, cv2.COLOR_BGRA2BGR)
        
        # Intentar guardar con diferentes métodos si falla
        try:
            success = cv2.imwrite(ruta_completa, frame_cosecha)
            if not success:
                # Intentar método alternativo
                from PIL import Image
                img_pil = Image.fromarray(cv2.cvtColor(frame_cosecha, cv2.COLOR_BGR2RGB))
                img_pil.save(ruta_completa, quality=95)
                
            if not os.path.exists(ruta_completa):
                raise Exception("No se pudo verificar el archivo guardado")
                
        except Exception as img_error:
            print(f"Error al guardar imagen: {str(img_error)}")
            # Intentar guardar en ubicación alternativa
            ruta_alternativa = os.path.join(os.path.expanduser("~"), "Cosechas", nombre_imagen)
            os.makedirs(os.path.dirname(ruta_alternativa), exist_ok=True)
            cv2.imwrite(ruta_alternativa, frame_cosecha)
            ruta_completa = ruta_alternativa

        clave = f"COS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        nueva_cosecha = Cosecha(
            Clave=clave,
            Peso=peso,
            Calificacion=calificacion,
            Foto_Cosecha=nombre_imagen,
            id_Recolector=id_recolector,
            id_Linea=id_linea,
            id_Entrega=id_entrega,
            id_Modalidad=id_modalidad,
            id_Cuadrilla=id_cuadrilla
        )
        
        session.add(nueva_cosecha)
        session.commit()
        session.refresh(nueva_cosecha)  # Asegura que id_Cosecha esté disponible

        # Copiar trazabilidad en la MISMA sesión inmediatamente después del commit
        if id_linea and nueva_cosecha.id_Cosecha:
            try:
                result = session.execute(
                    text("SELECT Clave_Trazabilidad FROM LINEA WHERE id_Linea = :id"),
                    {"id": id_linea}
                ).fetchone()

                if result and result.Clave_Trazabilidad:
                    session.execute(
                        text("""
                            UPDATE COSECHA 
                            SET Clave_Trazabilidad = :trz 
                            WHERE id_Cosecha = :id
                        """),
                        {"trz": result.Clave_Trazabilidad, "id": nueva_cosecha.id_Cosecha}
                    )
                    session.commit()
                    print(f"Trazabilidad asignada: {result.Clave_Trazabilidad}")
                else:
                    print(f"LINEA {id_linea} no tiene Clave_Trazabilidad")
            except Exception as trz_error:
                print(f"Error al asignar trazabilidad: {trz_error}")

        print(f"Cosecha registrada con ID: {nueva_cosecha.id_Cosecha}, Entrega: {id_entrega}")
        return True

    except Exception as e:
        session.rollback()
        print(f"Error al registrar cosecha: {str(e)}")
        return False  # ← Retornar solo bool
    finally:
        session.close()

# def registrar_cosecha(id_recolector, peso, calificacion, frame_cosecha, id_linea, id_entrega, id_modalidad, id_cuadrilla=None):
#     session = get_db()
#     try:
#          # Cambiar a una ruta local en lugar de OneDrive
#         ruta_imagenes = r"C:\Imagenes_Cosechas"
        
#         # Crear el directorio si no existe
#         try:
#             os.makedirs(ruta_imagenes, exist_ok=True)
#             if not os.path.isdir(ruta_imagenes):
#                 raise Exception(f"No se pudo crear/validar el directorio: {ruta_imagenes}")
#         except Exception as dir_error:
#             # Si falla, intentar en el directorio temporal
#             ruta_imagenes = os.path.join(os.environ['TEMP'], 'Cosechas')
#             os.makedirs(ruta_imagenes, exist_ok=True)
        
#         # Generar nombre único para la imagen
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         nombre_imagen = f"cos_{id_recolector}_{timestamp}_{calificacion}.jpg"
#         ruta_completa = os.path.join(ruta_imagenes, nombre_imagen)
        
#         # Verificar y convertir el frame si es necesario
#         if frame_cosecha is None:
#             raise ValueError("Frame de imagen es None")
            
#         if len(frame_cosecha.shape) == 2:  # Si es escala de grises
#             frame_cosecha = cv2.cvtColor(frame_cosecha, cv2.COLOR_GRAY2BGR)
#         elif frame_cosecha.shape[2] == 4:  # Si tiene canal alpha
#             frame_cosecha = cv2.cvtColor(frame_cosecha, cv2.COLOR_BGRA2BGR)
        
#         # Intentar guardar con diferentes métodos si falla
#         try:
#             success = cv2.imwrite(ruta_completa, frame_cosecha)
#             if not success:
#                 # Intentar método alternativo
#                 from PIL import Image
#                 img_pil = Image.fromarray(cv2.cvtColor(frame_cosecha, cv2.COLOR_BGR2RGB))
#                 img_pil.save(ruta_completa, quality=95)
                
#             if not os.path.exists(ruta_completa):
#                 raise Exception("No se pudo verificar el archivo guardado")
                
#         except Exception as img_error:
#             print(f"Error al guardar imagen: {str(img_error)}")
#             # Intentar guardar en ubicación alternativa
#             ruta_alternativa = os.path.join(os.path.expanduser("~"), "Cosechas", nombre_imagen)
#             os.makedirs(os.path.dirname(ruta_alternativa), exist_ok=True)
#             cv2.imwrite(ruta_alternativa, frame_cosecha)
#             ruta_completa = ruta_alternativa
            
#         # Generar clave única
#         clave = f"COS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
#         # Crear registro de cosecha (sin la imagen, solo con el nombre del archivo)
#         nueva_cosecha = Cosecha(
#             Clave=clave,
#             Peso=peso,
#             Calificacion=calificacion,
#             Foto_Cosecha=nombre_imagen,  # Solo guardamos el nombre
#             id_Recolector=id_recolector,
#             id_Linea=id_linea,
#             id_Entrega=id_entrega,
#             id_Modalidad=id_modalidad,
#             id_Cuadrilla=id_cuadrilla
#         )
        
#         session.add(nueva_cosecha)
#         session.commit()
        
#         return True, f"Cosecha registrada con ID: {nueva_cosecha.id_Cosecha}"
        
#     except Exception as e:
#         session.rollback()
#         return False, f"Error al registrar cosecha: {str(e)}"
#     finally:
#         session.close()




def seleccionar_calificacion():
    while True:
        print("\nSeleccione la calificación:")
        print("1 - Buena")
        print("2 - Regular")
        print("3 - Mala")
        
        opcion = input("Opción (1-3): ").strip()
        
        if opcion == '1':
            return "Buena"
        elif opcion == '2':
            return "Regular"
        elif opcion == '3':
            return "Mala"
        else:
            print("Opción no válida. Intente nuevamente.")

def capturar_y_registrar(cap_cosecha, id_recolector, nombre, macrotunel, id_entrega=None):
    print(f"\nRegistrando cosecha para: {nombre}")
    
    try:
        calificacion = seleccionar_calificacion()
        
        peso = get_peso()
        if peso is None:
            print("No se pudo obtener el peso de la báscula. ¿Desea continuar?")
            opcion = input("Ingrese el peso manualmente (kg) o presione Enter para cancelar: ").strip()
            if not opcion:
                return False
            try:
                peso = float(opcion)
            except ValueError:
                print("Error: Peso no válido")
                return False
        
        success, frame_cosecha = cap_cosecha.read()
        if not success:
            print("Error al capturar imagen de la cosecha")
            return False
        
        cv2.imshow("Foto de Cosecha Capturada", frame_cosecha)
        cv2.waitKey(1000)
        
        success, message = registrar_cosecha(id_recolector, peso, calificacion, frame_cosecha, macrotunel, id_entrega)
        print(message)
        
        # if success:
        #     print(f"\n✅ Cosecha registrada exitosamente\nMacrotunel: {macrotunel}\nPeso: {peso} kg\nCalificación: {calificacion}")
        #     obtener_estadisticas_recolector(id_recolector, nombre)
        # return success
        
    except Exception as e:
        print(f"Error inesperado: {str(e)}")
        return False
    finally:
        cv2.destroyWindow("Foto de Cosecha Capturada")




def get_peso():
    bascula = BasculaTorreyLPCR_USB()
    try:
        resultado = bascula.obtener_peso()
        if resultado['success']:
            print(f"[BÁSCULA] Peso obtenido: {resultado['peso']} {resultado['unidad']}")
            return resultado['peso']
        else:
            print(f"[BÁSCULA] Error: {resultado['error']}")
            return None
    except Exception as e:
        print(f"[BÁSCULA] Error inesperado: {str(e)}")
        return None
    finally:
        bascula.cerrar()


def obtener_estadisticas_recolector(id_recolector, nombre):
    session = get_db()
    try:
        # Consulta SQL como texto explícito
        sql = text("""
        SELECT 
            e.id_Recolector,
            e.Nombre_Completo,
            SUM(rp.Peso) AS Peso_Total_Kg,
            COUNT(rp.id_Cosecha) AS Cubetas_Cosecha,
            CONVERT(DATE, rp.Fecha_Transaccion) AS Fecha,
            (
                SELECT TOP 1 Calificacion
                FROM COSECHA 
                WHERE id_Recolector = e.id_Recolector
                AND CONVERT(DATE, Fecha_Transaccion) = CONVERT(DATE, GETDATE())
                GROUP BY Calificacion
                ORDER BY COUNT(*) DESC
            ) AS Calificacion_Mas_Frecuente
        FROM COSECHA rp
        JOIN RECOLECTOR e ON rp.id_Recolector = e.id_Recolector
        WHERE e.id_Recolector = :id_recolector
        AND CONVERT(DATE, rp.Fecha_Transaccion) = CONVERT(DATE, GETDATE())
        GROUP BY 
            e.id_Recolector,
            e.Nombre_Completo,
            CONVERT(DATE, rp.Fecha_Transaccion)
        """)
        
        result = session.execute(sql, {'id_recolector': id_recolector}).fetchone()
        
        if result:
            print("\n📊 Estadísticas del recolector:")
            print(f"Fecha: {result.Fecha.strftime('%Y-%m-%d')}")
            print(f"ID: {result.id_Recolector}")
            print(f"Nombre: {result.Nombre_Completo}")
            print(f"Peso total hoy: {result.Peso_Total_Kg or 0} kg")
            print(f"Cubetas entregadas hoy: {result.Cubetas_Cosecha or 0}")
            print(f"Calificación más frecuente hoy: {result.Calificacion_Mas_Frecuente or 'N/A'}")
        else:
            print("\nℹ️ No hay registros previos de cosecha para hoy")
            
    except Exception as e:
        print(f"\n⚠️ Error al obtener estadísticas: {str(e)}")
    finally:
        session.close()

# def obtener_suma_pesos_fecha_actual():
#     session = get_db()
#     try:
#         hoy = datetime.now().date()
#         total = session.query(
#             func.sum(Cosecha.Peso)
#         ).filter(
#             cast(Cosecha.Fecha_Transaccion, Date) == hoy
#         ).scalar()
        
#         return float(total) if total is not None else 0.0
        
#     except Exception as e:
#         print(f"Error al sumar pesos: {str(e)}")
#         return 0.0
#     finally:
#         session.close()

def obtener_suma_pesos_fecha_actual():
    session = get_db()
    try:
        hoy = datetime.now().date()
        total = session.query(
            func.sum(Cosecha.Peso)
        ).filter(
            cast(Cosecha.Fecha_Transaccion, Date) == hoy
        ).scalar()
        
        # Redondear a 4 decimales si hay valor, sino retornar 0.0
        return round(float(total), 4) if total is not None else 0.0
        
    except Exception as e:
        print(f"Error al sumar pesos: {str(e)}")
        return 0.0
    finally:
        session.close()


"""Funcion que devuelva true si el cosechador ya registro cosecha hoy, 
    el id_Cuadrilla de COSECHA y Responsable de tabla CUADRILLA
    conociendo Nombre_Completo de tabla Recolector"""

from sqlalchemy import text
from db.entities.data_entities import get_db


def cuadrillero_primera_cosecha(nombre_completo: str):
    session = get_db()

    sql = text("""
        ;WITH PrimerCorte AS (
            SELECT TOP 1
                   r.Nombre_Completo,
                   c.id_Cuadrilla,
                   q.Responsable,
                   q.Clave
            FROM COSECHA c
            INNER JOIN RECOLECTOR r ON r.id_Recolector = c.id_Recolector
            INNER JOIN CUADRILLA q ON q.id_Cuadrilla = c.id_Cuadrilla
            WHERE r.Nombre_Completo = :nombre
              AND CAST(c.Fecha_Transaccion AS DATE) = CAST(GETDATE() AS DATE)
              AND c.id_Cuadrilla IS NOT NULL
            ORDER BY c.Fecha_Transaccion ASC
        )
        SELECT 
            (SELECT Nombre_Completo FROM PrimerCorte) AS Nombre_Recolector,
            CASE WHEN EXISTS(SELECT 1 FROM PrimerCorte) THEN 1 ELSE 0 END AS Tiene_Cosecha_Hoy,
            (SELECT id_Cuadrilla FROM PrimerCorte) AS id_Cuadrilla_Hoy,
            (SELECT Responsable FROM PrimerCorte) AS Responsable_Hoy,
            (SELECT Clave FROM PrimerCorte) AS Responsable_Clave_Hoy;
    """)

    result = session.execute(sql, {"nombre": nombre_completo}).fetchone()

    if result is None:
        # No existe ningún registro hoy
        return {
            "nombre_recolector": nombre_completo,
            "tiene_cosecha_hoy": False,
            "id_cuadrilla": None,
            "responsable": None,
            "responsable_clave": None
        }

    return {
        "nombre_recolector": result.Nombre_Recolector,
        "tiene_cosecha_hoy": bool(result.Tiene_Cosecha_Hoy),
        "id_cuadrilla": result.id_Cuadrilla_Hoy,
        "responsable": result.Responsable_Hoy,
        "responsable_clave": result.Responsable_Clave_Hoy
    }
