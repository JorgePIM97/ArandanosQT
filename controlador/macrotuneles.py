#C:\ArandanosQT\controlador\macrotuneles.py
from db.entities.data_entities import get_db, Macrotunel, Tabla

session = get_db()

#Operaciones CRUD para Macrotunel
def listar_macrotunel_cosecha(clave_tabla):
    try:
        session = get_db()
        # Primero obtenemos el id_Tabla correspondiente a la clave
        tabla = session.query(Tabla).filter(Tabla.Clave == clave_tabla).first()
        
        if not tabla:
            print(f"No se encontró tabla con clave {clave_tabla}")
            return []
        
        # Luego filtramos los macrotuneles por id_Tabla
        macrotuneles = session.query(Macrotunel).filter(Macrotunel.id_Tabla == tabla.id_Tabla).all()
        return macrotuneles
    except Exception as e:
        print(f"Error listar macrotuneles {e}")
        return []
    finally:
        session.close()

def listar_macrotunel():
    session = get_db()
    try:
        macrotuneles = session.query(Macrotunel).all()
        result = []
        for macrotunel in macrotuneles:
            result.append({
                'id_Macrotunel': macrotunel.id_Macrotunel,
                'Clave': macrotunel.Clave,
                'Ubicacion': macrotunel.Ubicacion,
                'Nombre': macrotunel.Nombre,
                'Clave_Tabla': macrotunel.tabla.Clave if macrotunel.tabla else "Sin tabla"
            })
        return result
    except Exception as e:
        print(f"Error al listar macrotuneles: {e}")
        return []
    finally:
        session.close()

def crear_macrotunel(clave, ubicacion, nombre, id_tabla):
    try:
        session = get_db()
        # Convertir descripcion y clave a mayusculas
        clave = str(clave).upper() if clave else clave  
        ubicacion = str(ubicacion).upper() if ubicacion else ubicacion
        nombre = str(nombre).upper() if nombre else nombre
        
        nuevo_macrotunel = Macrotunel(
            Clave=clave,
            Ubicacion=ubicacion,
            Nombre=nombre,
            id_Tabla=id_tabla
        )

        session.add(nuevo_macrotunel)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error al crear macrotunel: {str(e)}")
        return False
    

def actualizar_macrotunel(id_macrotunel, clave, ubicacion, nombre, id_tabla):
    session = get_db()
    try:
        # Convertir descripcion y clave a mayusculas
        clave = str(clave).upper() if clave else clave  
        ubicacion = str(ubicacion).upper() if ubicacion else ubicacion
        nombre = str(nombre).upper() if nombre else nombre
            
        # Buscar la tabla existente
        macrotunel = session.query(Macrotunel).filter(Macrotunel.id_Macrotunel == id_macrotunel).first()
        if not macrotunel:
            print(f"No se encontró tabla con ID {id_macrotunel}")
            return False

        # Actualizar los campos
        macrotunel.Clave = clave
        macrotunel.Ubicacion=ubicacion
        macrotunel.Nombre = nombre
        macrotunel.id_Tabla = id_tabla

        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error al actualizar tabla: {str(e)}")
        return False
    finally:
        session.close()

def eliminar_macrotunel(id_Macrotunel):
    session = get_db()
    try:
        macrotunel = session.query(Macrotunel).get(id_Macrotunel)
        if macrotunel:
            session.delete(macrotunel)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        print(f"Error al eliminar macrotunel: {e}")
        return False
    finally:
        session.close()

