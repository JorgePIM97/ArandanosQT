# C:\ArandanosQT\controlador\fases.py
from db.entities.data_entities import get_db, Fase

# ==========================================================
# CRUD FASE
# ==========================================================

def listar_fases_cosecha():
    """Devuelve lista de objetos Fase (para uso interno / relaciones ORM)."""
    session = get_db()
    try:
        return session.query(Fase).all()
    except Exception as e:
        print(f"Error al listar fases: {e}")
        return []
    finally:
        session.close()


def listar_fases():
    """Devuelve lista de diccionarios con los datos de cada Fase."""
    session = get_db()
    try:
        fases = session.query(Fase).all()
        return [
            {
                'id_Fase'  : fase.id_Fase,
                'Clave'    : fase.Clave,
                'Ubicacion': fase.Ubicacion,
                'Nombre'   : fase.Nombre,
            }
            for fase in fases
        ]
    except Exception as e:
        print(f"Error al listar fases: {e}")
        return []
    finally:
        session.close()


def crear_fase(clave, ubicacion, nombre):
    session = get_db()
    try:
        nueva_fase = Fase(
            Clave     = str(clave).upper()    if clave     else clave,
            Ubicacion = str(ubicacion).upper() if ubicacion else ubicacion,
            Nombre    = str(nombre).upper()   if nombre    else nombre,
        )
        session.add(nueva_fase)
        session.commit()
        return True

    except Exception as e:
        session.rollback()
        print(f"Error al crear fase: {e}")
        return False

    finally:
        session.close()


def actualizar_fase(id_fase, clave, ubicacion, nombre):
    session = get_db()
    try:
        fase = session.get(Fase, id_fase)
        if not fase:
            print(f"No se encontró fase con ID {id_fase}")
            return False

        fase.Clave     = str(clave).upper()    if clave     else clave
        fase.Ubicacion = str(ubicacion).upper() if ubicacion else ubicacion
        fase.Nombre    = str(nombre).upper()   if nombre    else nombre

        session.commit()
        return True

    except Exception as e:
        session.rollback()
        print(f"Error al actualizar fase: {e}")
        return False

    finally:
        session.close()


def eliminar_fase(id_fase):
    session = get_db()
    try:
        fase = session.get(Fase, id_fase)
        if not fase:
            print(f"No se encontró fase con ID {id_fase}")
            return False

        session.delete(fase)
        session.commit()
        return True

    except Exception as e:
        session.rollback()
        print(f"Error al eliminar fase: {e}")
        return False

    finally:
        session.close()