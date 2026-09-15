# controlador/vistas.py
from PyQt6.QtWidgets import QMessageBox
from sqlalchemy import text
from db.entities.data_entities import get_db
import pandas as pd
from controlador.excel_generator import ExcelGenerator  # Importar la nueva clase

class SabanaVistas:
    def __init__(self):
        self.db = get_db()

    def GenerarDatos(self, fecha_inicio, fecha_fin, parent_widget=None):
        try:
            # Solo validar rango si el calendario de fin está activo
            if parent_widget.Fin_calendarWidget.isEnabled() and fecha_inicio > fecha_fin:
                QMessageBox.warning(parent_widget, "Error", "La fecha de inicio no puede ser mayor a la fecha final.")
                return

            # Construir consulta según el estado del calendario
            if parent_widget.Fin_calendarWidget.isEnabled():
                # Rango de fechas
                query = text("""
                SELECT * FROM vw_CosechaVista v
                WHERE v.[FECHA TRANSACCION] >= :fecha_inicio
                AND v.[FECHA TRANSACCION] < DATEADD(day, 1, :fecha_fin)
                ORDER BY v.[FECHA TRANSACCION]
            """)
                params = {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin}
            else:
                # Solo fecha exacta
                query = text("""
                    SELECT * FROM vw_CosechaVista v
                    WHERE CAST(v.[FECHA TRANSACCION] AS DATE) = :fecha_inicio
                    ORDER BY v.[FECHA TRANSACCION]
                """)
                params = {"fecha_inicio": fecha_inicio}
                
            result = self.db.execute(query, params)
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
            
            if df.empty:
                QMessageBox.information(parent_widget, "Información", 
                                    "No hay datos para la fecha seleccionada.")
                return

            # Delegar guardado a ExcelGenerator (usamos las mismas fechas para el nombre del archivo)
            ExcelGenerator.save_to_excel(df, fecha_inicio, fecha_fin, parent_widget)

        except Exception as e:
            QMessageBox.critical(parent_widget, "Error", f"Error al generar datos:\n{str(e)}")
        finally:
            self.db.close()


    # # Funcion que se utiliza para mostrar datos en Vista_tableWidget
    # def obtener_datos_vista(self, fecha_inicio=None, fecha_fin=None, nombre_recolector="", tabla="", macrotunel=""):
    #     try:
    #         with self.db:
    #             condiciones = []
    #             parametros = {}

    #             if fecha_inicio:
    #                 condiciones.append("CONVERT(date, Fecha_Transaccion) >= CONVERT(date, :fecha_inicio)")
    #                 parametros["fecha_inicio"] = fecha_inicio

    #             if fecha_fin:
    #                 condiciones.append("CONVERT(date, Fecha_Transaccion) <= CONVERT(date, :fecha_fin)")
    #                 parametros["fecha_fin"] = fecha_fin

    #             if nombre_recolector:
    #                 condiciones.append("r.Nombre_Completo LIKE :nombre_recolector")
    #                 parametros["nombre_recolector"] = f"%{nombre_recolector}%"

    #             if tabla:
    #                 condiciones.append("t.Clave LIKE :tabla")
    #                 parametros["tabla"] = f"%{tabla}%"

    #             if macrotunel:
    #                 condiciones.append("m.Clave LIKE :macrotunel")
    #                 parametros["macrotunel"] = f"%{macrotunel}%"

    #             where_clause = "WHERE " + " AND ".join(condiciones) if condiciones else ""

    #             query = text(f"""
    #                 SELECT c.id_Cosecha AS ID_COSECHA,
    #                     c.Clave AS CLAVE,
    #                     Calificacion AS CALIFICACION,
    #                     Peso AS PESO,
    #                     Fecha_Transaccion AS FECHA_TRANSACCION,
    #                     c.id_Recolector AS ID_RECOLECTOR,
    #                     r.Nombre_Completo AS NOMBRE_RECOLECTOR,
    #                     m.Clave AS MACROTUNEL,
    #                     t.Clave AS TABLA,
    #                     c.id_Entrega AS ID_VUELTA,
    #                     cu.Responsable AS CUADRILLERO,
    #                     cu.Localidad AS LOCALIDAD
    #                 FROM COSECHA c
    #                 INNER JOIN RECOLECTOR r ON r.id_Recolector = c.id_Recolector
    #                 INNER JOIN MACROTUNEL m ON m.id_Macrotunel = c.id_Macrotunel
    #                 INNER JOIN TABLA t ON m.id_Tabla = t.id_Tabla
    #                 INNER JOIN CUADRILLA cu ON c.id_Cuadrilla = cu.id_Cuadrilla
    #                 {where_clause}
    #                 ORDER BY Fecha_Transaccion DESC
    #             """)
    #             result = self.db.execute(query, parametros)
    #             datos = [dict(row._mapping) for row in result]
    #             return datos, None
    #     except Exception as e:
    #         print("Error vista: ", e)
    #         return None, f"Error al obtener datos de la vista: {str(e)}"

    # def obtener_datos_vista(self, fecha_inicio=None, fecha_fin=None,
    #                         nombre_recolector="", fase="", tabla="",
    #                         macrotunel="", linea=""):
    #     try:
    #         with self.db:
    #             condiciones = []
    #             parametros = {}

    #             if fecha_inicio:
    #                 condiciones.append("CONVERT(date, c.Fecha_Transaccion) >= CONVERT(date, :fecha_inicio)")
    #                 parametros["fecha_inicio"] = fecha_inicio

    #             if fecha_fin:
    #                 condiciones.append("CONVERT(date, c.Fecha_Transaccion) <= CONVERT(date, :fecha_fin)")
    #                 parametros["fecha_fin"] = fecha_fin

    #             if nombre_recolector:
    #                 condiciones.append("r.Nombre_Completo LIKE :nombre_recolector")
    #                 parametros["nombre_recolector"] = f"%{nombre_recolector}%"

    #             if fase:
    #                 condiciones.append("f.Clave LIKE :fase")
    #                 parametros["fase"] = f"%{fase}%"

    #             if tabla:
    #                 condiciones.append("t.Clave LIKE :tabla")
    #                 parametros["tabla"] = f"%{tabla}%"

    #             if macrotunel:
    #                 condiciones.append("m.Clave LIKE :macrotunel")
    #                 parametros["macrotunel"] = f"%{macrotunel}%"

    #             if linea:
    #                 condiciones.append("l.Clave LIKE :linea")
    #                 parametros["linea"] = f"%{linea}%"

    #             where_clause = "WHERE " + " AND ".join(condiciones) if condiciones else ""

    #             query = text(f"""
    #                 SELECT
    #                     c.id_Cosecha           AS ID_COSECHA,
    #                     c.Clave                AS CLAVE,
    #                     c.id_Entrega           AS ID_VUELTA,
    #                     c.id_Recolector        AS ID_RECOLECTOR,
    #                     r.Nombre_Completo      AS NOMBRE_RECOLECTOR,
    #                     c.Peso                 AS PESO,
    #                     c.Calificacion         AS CALIFICACION,
    #                     mo.Clave               AS MODALIDAD,
    #                     f.Clave                AS FASE,
    #                     t.Clave                AS TABLA,
    #                     m.Clave                AS MACROTUNEL,
    #                     l.Clave                AS LINEA,
    #                     cu.Responsable         AS CUADRILLERO,
    #                     cu.Localidad           AS LOCALIDAD,
    #                     c.Fecha_Transaccion    AS FECHA_TRANSACCION
    #                 FROM COSECHA c
    #                 INNER JOIN RECOLECTOR r   ON r.id_Recolector   = c.id_Recolector
    #                 INNER JOIN LINEA l        ON l.id_Linea         = c.id_Linea
    #                 INNER JOIN MACROTUNEL m   ON m.id_Macrotunel    = l.id_Macrotunel
    #                 INNER JOIN TABLA t        ON t.id_Tabla          = m.id_Tabla
    #                 INNER JOIN FASE f         ON f.id_Fase           = t.id_Fase
    #                 INNER JOIN CUADRILLA cu   ON cu.id_Cuadrilla     = c.id_Cuadrilla
    #                 LEFT  JOIN MODALIDAD mo   ON mo.id_Modalidad     = c.id_Modalidad
    #                 {where_clause}
    #                 ORDER BY c.Fecha_Transaccion DESC
    #             """)

    #             result = self.db.execute(query, parametros)
    #             datos = [dict(row._mapping) for row in result]
    #             return datos, None

    #     except Exception as e:
    #         print("Error vista: ", e)
    #         return None, f"Error al obtener datos de la vista: {str(e)}"
        


    def obtener_datos_vista(self, fecha_inicio=None, fecha_fin=None,
                            nombre_recolector="", fase="", tabla="",
                            macrotunel="", linea=""):
        try:
            with self.db:
                condiciones = []
                parametros = {}

                if fecha_inicio:
                    condiciones.append("CONVERT(date, c.Fecha_Transaccion) >= CONVERT(date, :fecha_inicio)")
                    parametros["fecha_inicio"] = fecha_inicio

                if fecha_fin:
                    condiciones.append("CONVERT(date, c.Fecha_Transaccion) <= CONVERT(date, :fecha_fin)")
                    parametros["fecha_fin"] = fecha_fin

                if nombre_recolector:
                    condiciones.append("r.Nombre_Completo LIKE :nombre_recolector")
                    parametros["nombre_recolector"] = f"%{nombre_recolector}%"

                if fase:
                    condiciones.append("f.Clave LIKE :fase")
                    parametros["fase"] = f"%{fase}%"

                if tabla:
                    condiciones.append("t.Clave LIKE :tabla")
                    parametros["tabla"] = f"%{tabla}%"

                if macrotunel:
                    condiciones.append("m.Clave LIKE :macrotunel")
                    parametros["macrotunel"] = f"%{macrotunel}%"

                if linea:
                    condiciones.append("l.Clave LIKE :linea")
                    parametros["linea"] = f"%{linea}%"

                where_clause = "WHERE " + " AND ".join(condiciones) if condiciones else ""

                query = text(f"""
                    SELECT
                        c.id_Cosecha              AS ID_COSECHA,
                        c.Clave                   AS CLAVE,
                        c.id_Entrega              AS ID_VUELTA,
                        c.id_Recolector           AS ID_RECOLECTOR,
                        r.Nombre_Completo         AS NOMBRE_RECOLECTOR,
                        c.Peso                    AS PESO,
                        c.Calificacion            AS CALIFICACION,
                        mo.Clave                  AS MODALIDAD,
                        f.Clave                   AS FASE,
                        t.Clave                   AS TABLA,
                        m.Clave                   AS MACROTUNEL,
                        l.Clave                   AS LINEA,
                        c.Clave_Trazabilidad      AS CLAVE_TRAZABILIDAD,  -- ← Viene de COSECHA
                        cu.Responsable            AS CUADRILLERO,
                        cu.Localidad              AS LOCALIDAD,
                        c.Fecha_Transaccion       AS FECHA_TRANSACCION
                    FROM COSECHA c
                    INNER JOIN RECOLECTOR r   ON r.id_Recolector   = c.id_Recolector
                    INNER JOIN LINEA l        ON l.id_Linea         = c.id_Linea
                    INNER JOIN MACROTUNEL m   ON m.id_Macrotunel    = l.id_Macrotunel
                    INNER JOIN TABLA t        ON t.id_Tabla          = m.id_Tabla
                    INNER JOIN FASE f         ON f.id_Fase           = t.id_Fase
                    INNER JOIN CUADRILLA cu   ON cu.id_Cuadrilla     = c.id_Cuadrilla
                    LEFT  JOIN MODALIDAD mo   ON mo.id_Modalidad     = c.id_Modalidad
                    {where_clause}
                    ORDER BY c.Fecha_Transaccion DESC
                """)

                result = self.db.execute(query, parametros)
                datos = [dict(row._mapping) for row in result]
                return datos, None

        except Exception as e:
            print("Error vista: ", e)
            return None, f"Error al obtener datos de la vista: {str(e)}"