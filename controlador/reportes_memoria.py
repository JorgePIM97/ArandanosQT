# controlador/reportes_memoria.py
from PyQt6.QtWidgets import QMessageBox
from sqlalchemy import text
from db.entities.data_entities import get_db
import pandas as pd
from controlador.excel_generator import ExcelGenerator


class ReportesMemoria:
    def __init__(self):
        self.db = get_db()

    def resumen_cuadrillero_recolectores(self, fecha_inicio, fecha_fin):
        """
        Devuelve un dataframe con el resumen por cuadrillero y recolectores
        dentro del rango de fechas.
        """
        query = text("""
        WITH Sabana AS (
            SELECT  
                cu.Responsable AS Cuadrillero,
                cu.Clave AS Clave,
                r.Nombre_Completo AS Nombre_Recolector,

                COUNT(DISTINCT e.id_Entrega) AS Total_Vueltas,
                SUM(co.Peso) AS Total_Peso,

                SUM(CASE WHEN co.Calificacion = 'Buena' THEN 1 ELSE 0 END) AS Total_Buena,
                SUM(CASE WHEN co.Calificacion = 'Regular' THEN 1 ELSE 0 END) AS Total_Regular,
                SUM(CASE WHEN co.Calificacion = 'Mala' THEN 1 ELSE 0 END) AS Total_Mala
            FROM COSECHA co
                INNER JOIN CUADRILLA cu ON co.id_Cuadrilla = cu.id_Cuadrilla
                INNER JOIN ENTREGA e ON co.id_Entrega = e.id_Entrega
                INNER JOIN RECOLECTOR r ON co.id_Recolector = r.id_Recolector
            WHERE CAST(co.Fecha_Transaccion AS DATE) BETWEEN :fecha1 AND :fecha2
            GROUP BY 
                cu.Responsable,
                cu.Clave,
                r.Nombre_Completo
        )
        SELECT 
            Cuadrillero,
            Clave,
            Nombre_Recolector,
            Total_Vueltas,
            Total_Peso,
            Total_Buena,
            Total_Regular,
            Total_Mala
        FROM Sabana
        ORDER BY Cuadrillero, Nombre_Recolector;
        """)

        with self.db as session:
            result = session.execute(
                query,
                {"fecha1": fecha_inicio, "fecha2": fecha_fin}
            )

            df = pd.DataFrame(result.fetchall(), columns=result.keys())

        return df
