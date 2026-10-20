# controlador/accesos/keys.py
from db.entities.data_entities import get_db, Usuario, KeyModulos

class KeysAcceso:
    def login(self, nombre, contraseña):
        db = get_db()
        try:
            usuario = db.query(Usuario).filter(
                Usuario.Nombre_Usuario == nombre
            ).first()

            if usuario is None:
                return False, "Usuario no existe"

            if usuario.Paswword_Acceso != contraseña:
                return False, "Contraseña incorrecta"

            if usuario.Status is not None and usuario.Status == False:
                return False, "Usuario deshabilitado"

            return True, usuario

        finally:
            db.close()

    def key_acceso_modulo(self, key_ingresada):
        db = get_db()
        try:
            key = db.query(KeyModulos).filter(
                KeyModulos.Key_Modulos == key_ingresada
            ).first()

            if key is None:
                return False

            return True

        finally:
            db.close()