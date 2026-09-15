#C:\ArandanosQT\controlador\tablas.py
from db.entities.data_entities import get_db, Tabla


# Operaciones CRUD para Tabla
def listar_tabla_cosecha(clave_fase):
    from db.entities.data_entities import get_db, Tabla, Fase
    session = get_db()
    try:
        fase = session.query(Fase).filter(Fase.Clave == clave_fase).first()
        if not fase:
            print(f"No se encontró fase con clave {clave_fase}")
            return []
        tablas = session.query(Tabla).filter(Tabla.id_Fase == fase.id_Fase).all()
        return tablas
    except Exception as e:
        print(f"Error listar tablas {e}")
        return []
    finally:
        session.close()

def listar_tabla_formulario():
    session = get_db()
    try:
        tablas = session.query(Tabla).all()
        return tablas
    except Exception as e:
        print(f"Error listar tablas {e}")
        return []
    finally:
        session.close()

def listar_tabla():
    session = get_db()
    try:
        tablas = session.query(Tabla).all()
        result = []
        for tabla in tablas:
            result.append({
                'id_Tabla': tabla.id_Tabla,
                'Clave': tabla.Clave,
                'Ubicacion': tabla.Ubicacion,
                'Nombre': tabla.Nombre,
                'Clave_Fase': tabla.fase.Clave if tabla.fase else "Sin fase"
            })
        return result
    except Exception as e:
        print(f"Error al listar tablas: {e}")
        return []
    finally:
        session.close()


def crear_tabla(clave, ubicacion, nombre, id_fase):
    session = get_db()
    try:
        clave = str(clave).upper() if clave else clave
        ubicacion = str(ubicacion).upper() if ubicacion else ubicacion
        nombre = str(nombre).upper() if nombre else nombre

        nueva_tabla = Tabla(
            Clave=clave,
            Ubicacion=ubicacion,
            Nombre=nombre,
            id_Fase=id_fase
        )

        session.add(nueva_tabla)
        session.commit()
        return True

    except Exception as e:
        session.rollback()
        print(f"Error al crear tabla: {str(e)}")
        return False

    finally:
        session.close()


def actualizar_tabla(id_tabla, clave, ubicacion, nombre, id_fase):
    session = get_db()
    try:
        clave = str(clave).upper() if clave else clave
        ubicacion = str(ubicacion).upper() if ubicacion else ubicacion
        nombre = str(nombre).upper() if nombre else nombre

        tabla = session.query(Tabla).filter(Tabla.id_Tabla == id_tabla).first()
        if not tabla:
            print(f"No se encontró tabla con ID {id_tabla}")
            return False

        tabla.Clave = clave
        tabla.Ubicacion = ubicacion
        tabla.Nombre = nombre
        tabla.id_Fase = id_fase  

        session.commit()
        return True

    except Exception as e:
        session.rollback()
        print(f"Error al actualizar tabla: {str(e)}")
        return False

    finally:
        session.close()


def eliminar_tabla(id_tabla):
    session = get_db()
    try:
        tabla = session.query(Tabla).get(id_tabla)
        if tabla:
            session.delete(tabla)
            session.commit()
            return True
        return False

    except Exception as e:
        session.rollback()
        print(f"Error al eliminar tabla: {e}")
        return False

    finally:
        session.close()