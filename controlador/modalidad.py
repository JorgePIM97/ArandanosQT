#C:\ArandanosQT\controlador\modalidad.py
from db.entities.data_entities import get_db, Modalidad
from sqlalchemy import text

class ModalidadControlador:
    def __init__(self):
        self.db = get_db()

    def obtener_modalidades(self):
        session = get_db()
        try:
            modalidades = session.query(Modalidad).all()
            return modalidades
        except Exception as e:
            print(f"Error listar modalidades {e}")
            return []
        finally:
            session.close()


    def obtener_modalidad_por_dia(self):
        try:
            query = text("SELECT id_Modalidad, Clave FROM MODALIDAD WHERE id_Modalidad = 2")
            result = self.db.execute(query)
            row = result.fetchone()
            if row:
                return row._mapping["Clave"], row._mapping["id_Modalidad"]
            return None, None
        except Exception as e:
            print("Error obtener modalidad:", e)
            return None, None
        
    def obtener_modalidad_por_recolector_hoy(self, nombre_completo: str):
        """
        Busca en REGISTRO_CHECK si el recolector tiene un check registrado
        hoy. Si existe, retorna la Clave e id_Modalidad de ese check.
        Si no, retorna None, None.
        """
        try:
            query = text("""
                SELECT TOP 1
                    mo.id_Modalidad,
                    mo.Clave
                FROM REGISTRO_CHECK rc
                INNER JOIN RECOLECTOR r  ON r.id_Recolector  = rc.id_Recolector
                INNER JOIN MODALIDAD  mo ON mo.id_Modalidad  = rc.id_Modalidad
                WHERE r.Nombre_Completo = :nombre
                AND CONVERT(date, rc.Fecha_Hora_Check) = CONVERT(date, GETDATE())
                ORDER BY rc.Fecha_Hora_Check DESC
            """)
            result = self.db.execute(query, {"nombre": nombre_completo})
            row = result.fetchone()
            if row:
                return row._mapping["Clave"], row._mapping["id_Modalidad"]
            return None, None
        except Exception as e:
            print("Error obtener modalidad por recolector:", e)
            return None, None