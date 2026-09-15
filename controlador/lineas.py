# C:\ArandanosQT\controlador\lineas.py
# ============================================================
# controlador/lineas.py  — CRUD completo corregido
# ============================================================
from db.entities.data_entities import get_db, Linea, Macrotunel

def listar_linea_cosecha(clave_macrotunel):
    # from db.entities.data_entities import get_db, Linea, Macrotunel
    try:
        session = get_db()
        # Buscar el macrotunel por su Clave (no en Linea)
        macrotunel = session.query(Macrotunel).filter(Macrotunel.Clave == clave_macrotunel).first()
        
        if not macrotunel:
            print(f"No se encontró macrotunel con clave {clave_macrotunel}")
            return []
        
        lineas = session.query(Linea).filter(Linea.id_Macrotunel == macrotunel.id_Macrotunel).all()
        return lineas
    except Exception as e:
        print(f"Error listar lineas {e}")
        return []
    finally:
        session.close()

def listar_linea():
    session = get_db()
    try:
        lineas = session.query(Linea).all()
        result = []
        for linea in lineas:
            result.append({
                'id_Linea':      linea.id_Linea,
                'Clave':         linea.Clave,
                'Nombre':        linea.Nombre,
                'Ubicacion':     linea.Ubicacion,
                'Num_Macetas':   linea.Num_Macetas,
                'Clave_Macrotunel': linea.macrotunel.Clave if linea.macrotunel else "Sin macrotunel",
            })
        return result
    except Exception as e:
        print(f"Error al listar líneas: {e}")
        return []
    finally:
        session.close()


def crear_linea(clave, ubicacion, nombre, num_macetas, id_macrotunel):
    session = get_db()
    try:
        clave = str(clave).upper() if clave else clave  
        ubicacion = str(ubicacion).upper() if ubicacion else ubicacion
        nombre = str(nombre).upper() if nombre else nombre

        nueva_linea = Linea(
            Clave=clave,
            Ubicacion=ubicacion,
            Nombre=nombre,
            Num_Macetas=int(num_macetas),
            id_Macrotunel=id_macrotunel,
        )
        session.add(nueva_linea)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error al crear línea: {e}")
        return False
    finally:
        session.close()


def actualizar_linea(id_linea, clave, ubicacion, nombre, num_macetas, id_macrotunel):
    session = get_db()
    try:
        clave = str(clave).upper() if clave else clave  
        ubicacion = str(ubicacion).upper() if ubicacion else ubicacion
        nombre = str(nombre).upper() if nombre else nombre

        linea = session.query(Linea).filter(Linea.id_Linea == id_linea).first()
        if not linea:
            print(f"No se encontró línea con ID {id_linea}")
            return False

        linea.Clave         = clave
        linea.Ubicacion     = ubicacion
        linea.Nombre        = nombre
        linea.Num_Macetas   = int(num_macetas)
        linea.id_Macrotunel = id_macrotunel

        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error al actualizar línea: {e}")
        return False
    finally:
        session.close()


def eliminar_linea(id_linea):
    session = get_db()
    try:
        linea = session.query(Linea).filter(Linea.id_Linea == id_linea).first()
        if linea:
            session.delete(linea)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        print(f"Error al eliminar línea: {e}")
        return False
    finally:
        session.close()