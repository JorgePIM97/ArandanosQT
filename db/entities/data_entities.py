# db/entities/data_entities.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, LargeBinary, ForeignKey
from sqlalchemy.orm import relationship
from ..data_connection.config_db import get_connection_string

Base = declarative_base()


# ===========================================================
# FASE
# ===========================================================
class Fase(Base):
    __tablename__ = 'FASE'

    id_Fase     = Column(Integer, primary_key=True, autoincrement=True)
    Clave       = Column(String(20),  unique=True, nullable=False)
    Ubicacion   = Column(String(50),  nullable=False)
    Nombre      = Column(String(100), nullable=True)

    # Una Fase tiene muchas Tablas
    tablas = relationship("Tabla", back_populates="fase")

# ===========================================================
# TABLA
# ===========================================================
class Tabla(Base):
    __tablename__ = 'TABLA'
    __table_args__ = {'implicit_returning': False}  # ← AGREGAR

    id_Tabla           = Column(Integer, primary_key=True, autoincrement=True)
    Clave              = Column(String(20), unique=True, nullable=False)
    Ubicacion          = Column(String(50),  nullable=True)
    Nombre             = Column(String(100), nullable=True)
    Clave_Trazabilidad = Column(String(200), nullable=True)
    id_Fase            = Column(Integer, ForeignKey('FASE.id_Fase', ondelete='SET NULL'), nullable=True)

    fase         = relationship("Fase",       back_populates="tablas")
    macrotuneles = relationship("Macrotunel", back_populates="tabla")


# ===========================================================
# MACROTUNEL
# ===========================================================
class Macrotunel(Base):
    __tablename__ = 'MACROTUNEL'
    __table_args__ = {'implicit_returning': False}  # ← AGREGAR

    id_Macrotunel      = Column(Integer, primary_key=True, autoincrement=True)
    Clave              = Column(String(20), unique=True, nullable=False)
    Ubicacion          = Column(String(50),  nullable=True)
    Nombre             = Column(String(100), nullable=True)
    Clave_Trazabilidad = Column(String(200), nullable=True)
    id_Tabla           = Column(Integer, ForeignKey('TABLA.id_Tabla', ondelete='SET NULL'), nullable=True)

    tabla  = relationship("Tabla",  back_populates="macrotuneles")
    lineas = relationship("Linea",  back_populates="macrotunel")


# ===========================================================
# LINEA
# ===========================================================
class Linea(Base):
    __tablename__ = 'LINEA'
    __table_args__ = {'implicit_returning': False}  # ← AGREGAR

    id_Linea           = Column(Integer, primary_key=True, autoincrement=True)
    Clave              = Column(String(20), nullable=False)
    Nombre             = Column(String(100), nullable=True)
    Ubicacion          = Column(String(50),  nullable=True)
    Num_Macetas        = Column(Integer,     nullable=True)
    Clave_Trazabilidad = Column(String(200), nullable=True)
    id_Macrotunel      = Column(Integer, ForeignKey('MACROTUNEL.id_Macrotunel', ondelete='SET NULL'), nullable=True)

    macrotunel = relationship("Macrotunel", back_populates="lineas")
    cosechas   = relationship("Cosecha",    back_populates="linea")
    entregas   = relationship("Entrega",    back_populates="linea")
# # ===========================================================
# # TABLA
# # ===========================================================
# class Tabla(Base):
#     __tablename__ = 'TABLA'

#     id_Tabla         = Column(Integer, primary_key=True, autoincrement=True)
#     Clave            = Column(String(20), unique=True, nullable=False)
#     Ubicacion        = Column(String(50),  nullable=True)
#     Nombre           = Column(String(100), nullable=True)
#     id_Fase          = Column(Integer, ForeignKey('FASE.id_Fase', ondelete='SET NULL'), nullable=True)

#     fase        = relationship("Fase",       back_populates="tablas")
#     macrotuneles = relationship("Macrotunel", back_populates="tabla")


# # ===========================================================
# # MACROTUNEL
# # ===========================================================
# class Macrotunel(Base):
#     __tablename__ = 'MACROTUNEL'

#     id_Macrotunel = Column(Integer, primary_key=True, autoincrement=True)
#     Clave         = Column(String(20), unique=True, nullable=False)
#     Ubicacion     = Column(String(50),  nullable=True)
#     Nombre        = Column(String(100), nullable=True)
#     id_Tabla      = Column(Integer, ForeignKey('TABLA.id_Tabla', ondelete='SET NULL'), nullable=True)

#     tabla  = relationship("Tabla",  back_populates="macrotuneles")
#     lineas = relationship("Linea",  back_populates="macrotunel")


# # ===========================================================
# # LINEA
# # ===========================================================
# class Linea(Base):
#     __tablename__ = 'LINEA'

#     id_Linea      = Column(Integer, primary_key=True, autoincrement=True)
#     Clave         = Column(String(20), nullable=False)
#     Nombre        = Column(String(100), nullable=True)
#     Ubicacion     = Column(String(50),  nullable=True)
#     Num_Macetas   = Column(Integer,    nullable=True)
#     id_Macrotunel = Column(Integer, ForeignKey('MACROTUNEL.id_Macrotunel', ondelete='SET NULL'), nullable=True)

#     macrotunel = relationship("Macrotunel", back_populates="lineas")
#     cosechas   = relationship("Cosecha",    back_populates="linea")
#     entregas   = relationship("Entrega",    back_populates="linea")


# ===========================================================
# MODALIDAD
# ===========================================================
class Modalidad(Base):
    __tablename__ = 'MODALIDAD'

    id_Modalidad = Column(Integer,    primary_key=True, autoincrement=True)
    Clave        = Column(String(50), unique=True, nullable=False)

    cosechas        = relationship("Cosecha",       back_populates="modalidad")
    entregas        = relationship("Entrega",        back_populates="modalidad")
    registro_checks = relationship("RegistroCheck",  back_populates="modalidad")


# ===========================================================
# CUADRILLA
# ===========================================================
class Cuadrilla(Base):
    __tablename__ = 'CUADRILLA'

    id_Cuadrilla = Column(Integer,     primary_key=True, autoincrement=True)
    Clave        = Column(String(20),  unique=True, nullable=False)
    Responsable  = Column(String(200), nullable=False)
    Localidad    = Column(String(100), nullable=True)

    recolectores = relationship("Recolector", back_populates="cuadrilla")
    cosechas     = relationship("Cosecha",    back_populates="cuadrilla")


# ===========================================================
# RECOLECTOR
# ===========================================================
class Recolector(Base):
    __tablename__ = 'RECOLECTOR'

    id_Recolector   = Column(Integer,      primary_key=True, autoincrement=True)
    Nombre_Completo = Column(String(200),  nullable=False)
    Encoder         = Column(LargeBinary,  nullable=True)
    Foto_Recolector = Column(LargeBinary,  nullable=True)
    Localidad       = Column(String(100),  nullable=True)
    Telefono        = Column(String(50),   nullable=True)
    Fecha_Registro  = Column(Date,         default=datetime.now)
    Acceso          = Column(Boolean,      nullable=True)
    id_Cuadrilla    = Column(Integer, ForeignKey('CUADRILLA.id_Cuadrilla', ondelete='SET NULL'), nullable=True)

    cuadrilla       = relationship("Cuadrilla",    back_populates="recolectores")
    cosechas        = relationship("Cosecha",       back_populates="recolector")
    entregas        = relationship("Entrega",        back_populates="recolector")
    registro_checks = relationship("RegistroCheck",  back_populates="recolector")


# ===========================================================
# ENTREGA
# (Se declara antes de Cosecha porque Cosecha la referencia)
# ===========================================================
class Entrega(Base):
    __tablename__ = 'ENTREGA'

    id_Entrega         = Column(Integer,    primary_key=True, autoincrement=True)
    Clave              = Column(String(20), nullable=False)
    Calificacion_Total = Column(String(20), nullable=True)
    Peso_Total         = Column(Float,      nullable=True)
    Entrega_Inicio     = Column(DateTime,   default=datetime.now)
    Entrega_Final      = Column(DateTime,   default=datetime.now)
    id_Recolector      = Column(Integer, ForeignKey('RECOLECTOR.id_Recolector', ondelete='SET NULL'), nullable=True)
    id_Linea           = Column(Integer, ForeignKey('LINEA.id_Linea',           ondelete='SET NULL'), nullable=True)
    id_Modalidad       = Column(Integer, ForeignKey('MODALIDAD.id_Modalidad',   ondelete='SET NULL'), nullable=True)

    recolector = relationship("Recolector", back_populates="entregas")
    linea      = relationship("Linea",      back_populates="entregas")
    modalidad  = relationship("Modalidad",  back_populates="entregas")
    cosechas   = relationship("Cosecha",    back_populates="entrega")


# ===========================================================
# COSECHA
# ===========================================================
class Cosecha(Base):
    __tablename__ = 'COSECHA'

    id_Cosecha        = Column(Integer,    primary_key=True, autoincrement=True)
    Clave             = Column(String(20), nullable=False)
    Calificacion      = Column(String(20), nullable=True)
    Peso              = Column(Float,      nullable=False)
    Foto_Cosecha      = Column(String(64), nullable=True)
    Fecha_Transaccion = Column(DateTime,   default=datetime.now)
    id_Recolector     = Column(Integer, ForeignKey('RECOLECTOR.id_Recolector', ondelete='SET NULL'), nullable=True)
    id_Linea          = Column(Integer, ForeignKey('LINEA.id_Linea',           ondelete='SET NULL'), nullable=True)
    id_Entrega        = Column(Integer, ForeignKey('ENTREGA.id_Entrega',       ondelete='SET NULL'), nullable=True)
    id_Cuadrilla      = Column(Integer, ForeignKey('CUADRILLA.id_Cuadrilla',   ondelete='SET NULL'), nullable=True)
    id_Modalidad      = Column(Integer, ForeignKey('MODALIDAD.id_Modalidad',   ondelete='SET NULL'), nullable=True)

    recolector = relationship("Recolector", back_populates="cosechas")
    linea      = relationship("Linea",      back_populates="cosechas")
    entrega    = relationship("Entrega",    back_populates="cosechas")
    cuadrilla  = relationship("Cuadrilla",  back_populates="cosechas")
    modalidad  = relationship("Modalidad",  back_populates="cosechas")


# ===========================================================
# REGISTRO_CHECK  (CHECK es palabra reservada en SQL Server)
# ===========================================================
class RegistroCheck(Base):
    __tablename__ = 'REGISTRO_CHECK'

    id_Check         = Column(Integer,  primary_key=True, autoincrement=True)
    Fecha_Hora_Check = Column(DateTime, nullable=True, default=datetime.now)
    id_Recolector    = Column(Integer, ForeignKey('RECOLECTOR.id_Recolector', ondelete='SET NULL'), nullable=True)
    id_Modalidad     = Column(Integer, ForeignKey('MODALIDAD.id_Modalidad',   ondelete='SET NULL'), nullable=True)

    recolector = relationship("Recolector", back_populates="registro_checks")
    modalidad  = relationship("Modalidad",  back_populates="registro_checks")

# ===========================================================
# KEY_MODULOS
# ===========================================================
class KeyModulos(Base):
    __tablename__ = 'KEY_MODULOS'

    id_Key  = Column(Integer,    primary_key=True, autoincrement=True)
    Key_Modulos   = Column(String(16), nullable=False)

# ===========================================================
# USUARIO
# ===========================================================
class Usuario(Base):
    __tablename__ = 'USUARIO'

    id_Usuario = Column(Integer,    primary_key=True, autoincrement=True)
    Nombre_Usuario   = Column(String(50), nullable=False)
    Paswword_Acceso  = Column(String(16), nullable=False)
    Rol = Column(String(50), nullable=False)
    Status = Column(Boolean, nullable=True)


# ===========================================================
# Sesión de base de datos
# ===========================================================
def get_db():
    engine = create_engine(
        get_connection_string(),
        echo=False,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 5}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        db.close()
        print(f"Error de conexión: {e}")
        raise