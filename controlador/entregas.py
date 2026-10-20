#controlador/entregas.py
from db.entities.data_entities import Recolector, Cosecha, get_db, Macrotunel, Entrega
from datetime import datetime, date
from sqlalchemy import cast, select, Date
from PyQt6.QtWidgets import QInputDialog, QApplication, QMainWindow, QTableWidgetItem, QDateTimeEdit, QTableWidget, QHeaderView, QMessageBox, QLabel, QDialog, QLineEdit, QVBoxLayout, QDialogButtonBox
from sqlalchemy import text  
from sqlalchemy import func, case
from sqlalchemy.orm import aliased
from sqlalchemy import desc

def iniciar_entrega(id_recolector, id_linea, id_modalidad):
    session = get_db()
    try:
        clave = f"ENT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        nueva_entrega = Entrega(
            Clave=clave,
            id_Recolector=id_recolector,
            id_Linea=id_linea,
            id_Modalidad=id_modalidad,
            Entrega_Inicio=datetime.now()
        )
        
        session.add(nueva_entrega)
        session.commit()
        return nueva_entrega.id_Entrega
    except Exception as e:
        session.rollback()
        print(f"Error al iniciar entrega: {str(e)}")
        return None
    finally:
        session.close()

def finalizar_entrega(id_entrega):
    session = get_db()
    try:
        entrega = session.query(Entrega).get(id_entrega)
        if not entrega:
            print(f"No se encontró la entrega con ID: {id_entrega}")
            return False

        # Calcular peso y calificaciones con SQL directo
        # para evitar interferencia del trigger con el ORM
        result = session.execute(text("""
            SELECT 
                ISNULL(SUM(Peso), 0)        AS peso_total,
                COUNT(*)                     AS total_cosechas
            FROM COSECHA
            WHERE id_Entrega = :id_entrega
        """), {"id_entrega": id_entrega}).fetchone()

        peso_total     = float(result.peso_total)    if result else 0.0
        total_cosechas = int(result.total_cosechas)  if result else 0

        print(f"Cosechas encontradas para entrega {id_entrega}: {total_cosechas}, Peso: {peso_total}")

        entrega.Peso_Total    = peso_total
        entrega.Entrega_Final = datetime.now()

        # Calificación más frecuente también con SQL directo
        cal_result = session.execute(text("""
            SELECT TOP 1 Calificacion, COUNT(*) AS freq
            FROM COSECHA
            WHERE id_Entrega = :id_entrega
              AND Calificacion IS NOT NULL
            GROUP BY Calificacion
            ORDER BY freq DESC
        """), {"id_entrega": id_entrega}).fetchone()

        if cal_result:
            entrega.Calificacion_Total = cal_result.Calificacion

        session.commit()
        print(f"Entrega {id_entrega} finalizada. Peso total: {peso_total}")
        return True

    except Exception as e:
        session.rollback()
        print(f"Error al finalizar entrega: {str(e)}")
        return False
    finally:
        session.close()

# def finalizar_entrega(id_entrega):
#     session = get_db()
#     try:
#         entrega = session.query(Entrega).get(id_entrega)
#         if not entrega:
#             print(f"No se encontró la entrega con ID: {id_entrega}")
#             return False
        
#         # Calcular estadísticas de las cosechas asociadas
#         cosechas = session.query(Cosecha).filter(Cosecha.id_Entrega == id_entrega).all()
        
#         if cosechas:
#             # Calcular peso total usando la función auxiliar
#             peso_total = Obtener_Peso_Total_Entrega(id_entrega)
#             entrega.Peso_Total = peso_total
            
#             # Calcular calificación más frecuente
#             calificaciones = [c.Calificacion for c in cosechas if c.Calificacion]
#             if calificaciones:
#                 calificacion_mas_frecuente = max(set(calificaciones), key=calificaciones.count)
#                 entrega.Calificacion_Total = calificacion_mas_frecuente
            
#         entrega.Entrega_Final = datetime.now()
#         session.commit()
        
#         print(f"Entrega {id_entrega} finalizada. Peso total: {peso_total}")
#         return True
        
#     except Exception as e:
#         session.rollback()
#         print(f"Error al finalizar entrega: {str(e)}")
#         return False
#     finally:
#         session.close()


def Total_Entregas_Hoy():
    session = get_db()
    # Obtener la fecha actual
    fecha_actual = date.today()  # o datetime.now().date()

    # Consulta con ORM
    total_entregas = session.query(Entrega).filter(
        cast(Entrega.Entrega_Inicio, Date) == fecha_actual
    ).count()

    print(f"Total de entregas hoy ({fecha_actual}): {total_entregas}")

def Total_Entregas_Hoy_Recolector(id):
    session = get_db()
    fecha_actual = date.today()  # Fecha actual sin hora
    id_recolector = id  # Cambiar por el ID deseado

    entregas_unicas = session.query(Cosecha.id_Entrega)\
        .join(Entrega, Cosecha.id_Entrega == Entrega.id_Entrega)\
        .filter(
            Cosecha.id_Recolector == id_recolector,
            cast(Entrega.Entrega_Inicio, Date) == fecha_actual
        )\
        .distinct()\
        .count()

    print(f"Entregas únicas hoy para recolector {id_recolector}: {entregas_unicas}")
    return entregas_unicas

def Obtener_ID_Recolector(nombre_colector: QLabel):
    # Obtener datos de la interfaz
    nombre = nombre_colector.text() #Nombre de colector

    
    # Validar datos
    if not nombre:
        #QMessageBox.warning("Error", "Faltan datos del recolector")
        print("Faltan datos de recolector")
        return
        

    # Obtener IDs de la base de datos
    session = get_db()
    try:
        # Buscar recolector
        recolector = session.query(Recolector).filter(
            Recolector.Nombre_Completo == nombre #Se valida y obtiene de la base de datos el nombre obtenido de NombreCosechaText_Lbl 
        ).first()
        
        # Se valida que exista el nombre del colector en la base de datos
        if not recolector:
            #QMessageBox.warning(self, "Error", f"No se encontró al recolector: {nombre}")
            print("No se encontró al recolector")
            return
        
        # Se obtiene el id que le pertenece a Nombre_Completo
        if recolector is not None:
            id_recolector = recolector.id_Recolector  # Acceder al ID del recolector encontrado
            print(f"El ID del recolector {nombre} es: {id_recolector}")
        else:
            print(f"No se encontró un recolector con el nombre {nombre}")
    except Exception as e:
        print(e)
    return id_recolector

def Obtener_Calificaciones_Separadas(recolector):
    session = get_db()
    ultimo_id = Obtener_Ultimo_Id_Entrega()
    
    if not ultimo_id:
        return None  # Or return a default object if no deliveries exist

    # Consulta usando SQLAlchemy ORM (updated case() syntax)
    query = (
        session.query(
            Entrega.id_Entrega,
            Entrega.Clave.label("Clave_Entrega"),
            func.sum(case((Cosecha.Calificacion == 'Buena', 1), else_=0)).label("Buenas"),
            func.sum(case((Cosecha.Calificacion == 'Regular', 1), else_=0)).label("Regulares"),
            func.sum(case((Cosecha.Calificacion == 'Mala', 1), else_=0)).label("Malas"),
            func.count(Cosecha.id_Cosecha).label("Total_Calificaciones")
        )
        .outerjoin(Cosecha, Entrega.id_Entrega == Cosecha.id_Entrega)
        .filter(
            Entrega.id_Recolector == recolector,
            Entrega.id_Entrega == ultimo_id
        )
        .group_by(Entrega.id_Entrega, Entrega.Clave)
    )

    resultado = query.first()  # We only expect one result
    
    if not resultado:
        # Return a default object if no matches found
        class DefaultResult:
            def __init__(self):
                self.Buenas = 0
                self.Regulares = 0
                self.Malas = 0
                self.Total_Calificaciones = 0
                
        return DefaultResult()
        
    return resultado

def Obtener_Ultimo_Id_Entrega():
    session = get_db()
    # Obtener el último registro ordenado por id_Entrega descendente
    ultima_entrega = session.query(Entrega)\
        .order_by(desc(Entrega.id_Entrega))\
        .first()

    if ultima_entrega:
        ultimo_id = ultima_entrega.id_Entrega
        print(f"El último ID de Entrega registrado es: {ultimo_id}")
        return ultimo_id
    else:
        print("No hay entregas registradas")

def Obtener_Peso_Total_Cosechador(id):
    session = get_db()
    id_recolector = id  # ID del recolector
    fecha_actual = date.today()

    peso_total = session.query(
        func.sum(Cosecha.Peso).label("Peso_Total_Hoy")
    ).filter(
        Cosecha.id_Recolector == id_recolector,
        cast(Cosecha.Fecha_Transaccion, Date) == fecha_actual
    ).scalar()

    print(f"Peso total hoy para recolector {id_recolector}: {peso_total or 0}")
    return round(float(peso_total), 4) if peso_total is not None else 0.0

def Obtener_Peso_Total_Entrega(id_entrega):
    """Obtiene el peso total acumulado de todas las cosechas asociadas a una entrega"""
    session = get_db()
    try:
        # Verificar si la entrega existe
        entrega = session.query(Entrega).get(id_entrega)
        if not entrega:
            print(f"No se encontró la entrega con ID: {id_entrega}")
            return None
        
        # Si el peso ya está calculado en la tabla ENTREGA, devolverlo
        if entrega.Peso_Total is not None:
            return entrega.Peso_Total
        
        # Calcular el peso sumando todas las cosechas asociadas
        peso_total = session.query(func.sum(Cosecha.Peso)).\
            filter(Cosecha.id_Entrega == id_entrega).\
            scalar()
        
        return round(float(peso_total), 4) if peso_total is not None else 0.0
        
    except Exception as e:
        print(f"Error al obtener peso total de la entrega: {str(e)}")
        return None
    finally:
        session.close()

def Obtener_Resumen_Colector(nombre_colector):
    """Obtiene el resumen de entregas para un recolector en la fecha actual"""
    try:
        session = get_db()
        fecha_actual = datetime.now().date()
        
        query = text("""
            SELECT 
                CONVERT(DATE, e.Entrega_Inicio) AS Fecha,
                r.Nombre_Completo AS Nombre,
                COUNT(DISTINCT e.id_Entrega) AS [Total Entregas],
                SUM(c.Peso) AS [Peso Total Acumulado],
                SUM(CASE WHEN c.Calificacion = 'Buena' THEN 1 ELSE 0 END) AS [Total Buenas],
                SUM(CASE WHEN c.Calificacion = 'Regular' THEN 1 ELSE 0 END) AS [Total Regulares],
                SUM(CASE WHEN c.Calificacion = 'Mala' THEN 1 ELSE 0 END) AS [Total Malas]
            FROM 
                ENTREGA e
            INNER JOIN 
                RECOLECTOR r ON e.id_Recolector = r.id_Recolector
            INNER JOIN 
                COSECHA c ON e.id_Entrega = c.id_Entrega
            WHERE 
                r.Nombre_Completo LIKE :nombre
                AND CAST(e.Entrega_Inicio AS DATE) = :fecha
            GROUP BY 
                CONVERT(DATE, e.Entrega_Inicio),
                r.Nombre_Completo
            ORDER BY 
                Fecha, Nombre
        """)

        result = session.execute(query, {
            'nombre': f'%{nombre_colector}%',
            'fecha': fecha_actual
        }).fetchone()

        if result:
            return {
                'Fecha': result[0],
                'Nombre': result[1],
                'Total_Entregas': result[2],
                'Peso_Total_Acumulado': round(float(result[3]), 4) if result[3] is not None else 0.0,
                'Total_Buenas': result[4],
                'Total_Regulares': result[5],
                'Total_Malas': result[6]
            }
        return None

    except Exception as e:
        print(f"Error al obtener resumen de entregas: {e}")
        return None
    finally:
        session.close()


def Obtener_Corte_Dia():
    """Obtiene el reporte de corte del día para todos los recolectores"""
    try:
        session = get_db()

        # Consulta SQL corregida
        query = text("""
            SELECT 
                r.Nombre_Completo AS Nombre,
                COUNT(DISTINCT e.id_Entrega) AS Total_Entregas,
                SUM(c.Peso) AS Peso_Total,
                SUM(CASE WHEN c.Calificacion = 'Buena' THEN 1 ELSE 0 END) AS Buenas,
                SUM(CASE WHEN c.Calificacion = 'Regular' THEN 1 ELSE 0 END) AS Regulares,
                SUM(CASE WHEN c.Calificacion = 'Mala' THEN 1 ELSE 0 END) AS Malas
            FROM 
                ENTREGA e
            INNER JOIN 
                RECOLECTOR r ON e.id_Recolector = r.id_Recolector
            INNER JOIN 
                COSECHA c ON e.id_Entrega = c.id_Entrega
            WHERE 
                CAST(e.Entrega_Inicio AS DATE) = CAST(GETDATE() AS DATE)
            GROUP BY 
                r.Nombre_Completo
            ORDER BY 
                Peso_Total DESC
        """)

        resultados = session.execute(query).fetchall()
        return resultados

    except Exception as e:
        print(f"Error al obtener corte del día: {e}")
        return None

    finally:
        session.close()
