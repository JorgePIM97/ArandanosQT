#C:\ArandanosQT\controlador\conteos.py
from db.entities.data_entities import get_db, Tabla, Macrotunel, Linea

def contar_tablas_por_fase(id_fase):
    session = get_db()
    try:
        return session.query(Tabla).filter(Tabla.id_Fase == id_fase).count()
    except:
        return 0
    finally:
        session.close()

def contar_macrotuneles_por_tabla(id_tabla):
    session = get_db()
    try:
        return session.query(Macrotunel).filter(Macrotunel.id_Tabla == id_tabla).count()
    except:
        return 0
    finally:
        session.close()

def contar_lineas_por_macrotunel(id_macrotunel):
    session = get_db()
    try:
        return session.query(Linea).filter(Linea.id_Macrotunel == id_macrotunel).count()
    except:
        return 0
    finally:
        session.close()