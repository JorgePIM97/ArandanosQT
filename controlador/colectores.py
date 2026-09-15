#controlador/colectores.py
import cv2
import numpy as np
from io import BytesIO
from db.entities.data_entities import get_db, Recolector

#session = get_db()

def obtener_cuadrilla_por_nombre(nombre_recolector):
    """Retorna la cuadrilla asociada al recolector con ese nombre."""
    session = get_db()
    try:
        nombre_upper = str(nombre_recolector).upper().strip()
        recolector = session.query(Recolector).filter(
            Recolector.Nombre_Completo == nombre_upper
        ).first()

        if recolector and recolector.cuadrilla:
            return recolector.cuadrilla  # Objeto Cuadrilla con .Clave e .id_Cuadrilla
        return None
    except Exception as e:
        print(f"Error al obtener cuadrilla por nombre: {e}")
        return None
    finally:
        session.close()
        
def crear_recolector(nombre, imagen, encoding, localidad, telefono, acceso, id_cuadrilla):
    session = get_db()
    try:
        # Convertir nombre y localidad a mayusculas
        nombre = str(nombre).upper() if nombre else nombre
        localidad = str(localidad).upper() if localidad else localidad 

        # Convertir imagen a bytes
        _, img_encoded = cv2.imencode('.jpg', imagen)
        img_bytes = img_encoded.tobytes()
        
        # Convertir encoding a bytes
        encoding_bytes = BytesIO()
        np.save(encoding_bytes, encoding, allow_pickle=False)
        encoding_bytes = encoding_bytes.getvalue()
        
        # Crear nuevo empleado
        nuevo_empleado = Recolector(
            Nombre_Completo=nombre,
            Foto_Recolector=img_bytes,
            Encoder=encoding_bytes,
            Localidad=localidad,
            Telefono=telefono,
            Acceso=acceso,
            id_Cuadrilla=id_cuadrilla 
        )
        
        # Guardar en la base de datos
        session.add(nuevo_empleado)
        session.commit()
        print(f"Empleado {nombre} registrado exitosamente en la base de datos")
        return True
    except Exception as e:
        session.rollback()
        print(f"Error al guardar empleado: {str(e)}")
        return False
    finally:
        session.close()


# def listar_recolectores():
#     session = get_db()
#     try:
        
#         colectores = session.query(Recolector).all()
#         return colectores
#     except Exception as e:
#         print(f"Error listar colectores {e}")
#         return []
#     finally:
#         session.close()

def listar_recolectores():
    session = get_db()
    try:
        colectores = session.query(Recolector).all()
        result = []
        for colector in colectores:
            result.append({
                'id_Colector':colector.id_Recolector,
                'Nombre_Colector':colector.Nombre_Completo,
                'Localidad':colector.Localidad,
                'Cuadrilla': colector.cuadrilla.Clave if colector.cuadrilla else "Sin macrotunel",
                'Telefono':colector.Telefono
            })
        return result
    except Exception as e:
        print(f"Error listar colectores {e}")
        return []
    finally:
        session.close()


####################################################
#                 MODIFICAR
####################################################
def actualizar_colector_con_encoder(id_Recolector, nombre_completo, encoder, foto, localidad, telefono, id_cuadrilla):
    session = get_db()
    try:
        nombre_completo = str(nombre_completo).upper() if nombre_completo else nombre_completo
        localidad = str(localidad).upper() if localidad else localidad

        # Serializar el encoding numpy a bytes correctamente
        if encoder is not None and isinstance(encoder, np.ndarray):
            buffer = BytesIO()
            np.save(buffer, encoder)
            encoder_bytes = buffer.getvalue()
        else:
            encoder_bytes = encoder  # Ya está serializado o es None

        colector = session.query(Recolector).get(id_Recolector)
        if colector:
            colector.Nombre_Completo = nombre_completo
            colector.Encoder = encoder_bytes  # Guardar bytes serializados
            colector.Foto_Recolector = foto
            colector.Localidad = localidad
            colector.Telefono = telefono
            colector.id_Cuadrilla = id_cuadrilla
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        print(f"Error al actualizar colector: {e}")
        return False
    finally:
        session.close()

def actualizar_colector(id_Recolector, nombre_completo, localidad, telefono, id_cuadrilla):
    session = get_db()
    try:
        # Convertir nombre y localidad a mayusculas
        nombre_completo = str(nombre_completo).upper() if nombre_completo else nombre_completo
        localidad = str(localidad).upper() if localidad else localidad 

        colector = session.query(Recolector).get(id_Recolector)
        if colector:
            colector.Nombre_Completo = nombre_completo
            colector.Localidad = localidad
            colector.Telefono = telefono
            colector.id_Cuadrilla = id_cuadrilla
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        print(f"Error al actualizar cuadrilla: {e}")
        return False
    finally:
        session.close()

def eliminar_colector(id_colector):
    session = get_db()
    try:
        colector = session.query(Recolector).get(id_colector)
        if colector:
            session.delete(colector)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        print(f"Error al eliminar cuadrilla: {e}")
        return False
    finally:
        session.close()