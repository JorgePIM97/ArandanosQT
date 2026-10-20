#controlador/cuadrilleros.py
from db.entities.data_entities import get_db, Cuadrilla, Recolector, Cosecha, Tabla, Macrotunel, Entrega

session = get_db()

# Operaciones CRUD para Cuadrilla
def listar_cuadrillas():
    session = get_db()
    try:
        cuadrillas = session.query(Cuadrilla).all()
        return cuadrillas
    except Exception as e:
        print(f"Error al listar cuadrillas: {e}")
        return []
    finally:
        session.close()

def listar_cuadrillas_comboBox():
    session = get_db()
    # from db.entities.data_entities import Cuadrilla  # Asegúrate de importar tu modelo
    # session = get_db()
    cuadrillas = session.query(Cuadrilla).all()
    return cuadrillas  # Devuelve lista de objetos Cuadrilla

def obtener_clave_cuadrillero(nombre_recolector: str):
    """
    Devuelve la Clave de la Cuadrilla asociada a un Recolector por su nombre.
    """
    session = get_db()
    try:
        resultado = (
            session.query(Cuadrilla.Clave)
            .join(Recolector, Cuadrilla.id_Cuadrilla == Recolector.id_Cuadrilla)
            .filter(Recolector.Nombre_Completo == nombre_recolector)
            .first()
        )
        return resultado.Clave if resultado else None
    except Exception as e:
        print(f"Error al obtener clave de cuadrillero: {e}")
        return None
    finally:
        session.close()


def crear_cuadrilla(clave, responsable, localidad):
    session = get_db()
    try:
        # Convertir clave, responsable y localidad a mayusculas
        clave = str(clave).upper() if clave else clave
        responsable = str(responsable).upper() if responsable else responsable
        localidad = str(localidad).upper() if localidad else localidad 

        nueva_cuadrilla = Cuadrilla(
            Clave=clave,
            Responsable=responsable,
            Localidad=localidad
        )
        
        session.add(nueva_cuadrilla)
        session.commit()
        print("Cuadrilla creada exitosamente!")
    except Exception as e:
        print("Error: ", e)

def actualizar_cuadrilla(id_cuadrilla, clave, responsable, localidad):
    session = get_db()
    try:
        # Convertir clave, responsable y localidad a mayusculas
        clave = str(clave).upper() if clave else clave
        responsable = str(responsable).upper() if responsable else responsable
        localidad = str(localidad).upper() if localidad else localidad 
        
        cuadrilla = session.query(Cuadrilla).get(id_cuadrilla)
        if cuadrilla:
            cuadrilla.Clave = clave
            cuadrilla.Responsable = responsable
            cuadrilla.Localidad = localidad
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        print(f"Error al actualizar cuadrilla: {e}")
        return False
    finally:
        session.close()

def eliminar_cuadrilla(id_cuadrilla):
    session = get_db()
    try:
        cuadrilla = session.query(Cuadrilla).get(id_cuadrilla)
        if cuadrilla:
            session.delete(cuadrilla)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        print(f"Error al eliminar cuadrilla: {e}")
        return False
    finally:
        session.close()