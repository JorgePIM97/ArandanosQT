# controlador/checador.py
from db.entities.data_entities import get_db, RegistroCheck, Recolector, Modalidad

def listar_checks():
    session = get_db()
    try:
        checks = (
            session.query(RegistroCheck)
            .outerjoin(Recolector, RegistroCheck.id_Recolector == Recolector.id_Recolector)
            .outerjoin(Modalidad,  RegistroCheck.id_Modalidad  == Modalidad.id_Modalidad)
            .order_by(RegistroCheck.Fecha_Hora_Check.desc())
            .all()
        )
        return [
            {
                'id_Check':      check.id_Check,
                'Fecha_Y_Hora':  check.Fecha_Hora_Check.strftime("%d/%m/%Y %H:%M") if check.Fecha_Hora_Check else "",
                'Recolector':    check.recolector.Nombre_Completo if check.recolector else "Sin asignar",
                'Modalidad':     check.modalidad.Clave            if check.modalidad  else "Sin asignar",
            }
            for check in checks
        ]
    except Exception as e:
        print(f"Error al listar checks: {e}")
        return []
    finally:
        session.close()


def crear_check(id_recolector, id_modalidad):
    session = get_db()
    try:
        nuevo_check = RegistroCheck(
            id_Recolector = str(id_recolector).upper() if id_recolector else id_recolector,
            id_Modalidad = str(id_modalidad).upper() if id_modalidad else id_modalidad
        )
        session.add(nuevo_check)
        session.commit()
        return True

    except Exception as e:
        session.rollback()
        print(f"Error al crear checkin: {e}")
        return False

    finally:
        session.close()