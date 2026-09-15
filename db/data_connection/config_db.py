# db/data_connection/config_db.py
from urllib.parse import quote_plus
import json
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text 


#CRED_FILE = os.path.join(os.path.dirname(__file__), "credenciales.json")
#CRED_FILE = "C:\\ArandanosGPA\\credenciales.json"

# Carpeta de datos en AppData (siempre escribible, sin permisos de admin)
APP_DATA_DIR = os.path.join(os.environ.get("APPDATA", "C:\\"), "ArandanosGPA")
os.makedirs(APP_DATA_DIR, exist_ok=True)
CRED_FILE = os.path.join(APP_DATA_DIR, "credenciales.json")

def guardar_credenciales(data: dict):
    with open(CRED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def cargar_credenciales() -> dict:
    if not os.path.exists(CRED_FILE):
        return {
            "SERVER": "", "DATABASE": "", "USERNAME": "", "PASSWORD": ""
        }
    with open(CRED_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    
def cargar_id_carrito() -> dict:
    if not os.path.exists(CRED_FILE):
        return {"ID_CARRITO": ""}
    with open(CRED_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        # Si el JSON existe pero aún no tiene ID_CARRITO, agregarlo con valor vacío
        if "ID_CARRITO" not in data:
            data["ID_CARRITO"] = ""
            with open(CRED_FILE, "w", encoding="utf-8") as fw:
                json.dump(data, fw, indent=4)
        return data

def get_id_carrito():
    creds = cargar_id_carrito()
    return creds.get("ID_CARRITO", "")  # .get() evita KeyError si falta la clave

def get_connection_string():
    creds = cargar_credenciales()
    password = quote_plus(creds['PASSWORD'])
    driverDB = "ODBC Driver 17 for SQL Server"
    return (
        f"mssql+pyodbc://{creds['USERNAME']}:{password}@"
        f"{creds['SERVER']}/{creds['DATABASE']}?"
        f"driver={str(driverDB)}"
    )

def tablas_inicializadas():
    """Verifica que las tablas principales existan en la DB conectada"""
    try:
        engine = create_engine(get_connection_string())
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = 'KEY_MODULOS'
            """))
            count = result.scalar()
            return count > 0
    except Exception:
        return False

# def probar_conexion():
#     try:
#         from .config_db import get_connection_string
#         engine = create_engine(get_connection_string())
#         with engine.connect() as conn:
#             conn.execute(text("SELECT 1"))
#         return True
#     except SQLAlchemyError:
#         return False

def probar_conexion():
    try:
        # Verificar primero que existan credenciales configuradas
        creds = cargar_credenciales()
        if not all([creds.get("SERVER"), creds.get("DATABASE"), 
                    creds.get("USERNAME"), creds.get("PASSWORD")]):
            return False

        engine = create_engine(get_connection_string())
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:  # ← Capturar cualquier excepción, no solo SQLAlchemyError
        return False

# DB_CONFIG = {
#     "SERVER": "D-AIN-TII-002",  # Usa doble barra invertida
#     "DATABASE": "ArandanosDB",
#     "USERNAME": "sa",
#     "PASSWORD": "P0T4tO",
#     "DRIVER": "ODBC Driver 17 for SQL Server"  # Nombre exacto del driver
# }

# DB_CONFIG = {
#     "SERVER": "E-PIM_15\SQLEXPRESS",  # Usa doble barra invertida
#     "DATABASE": "ArandanosDB",
#     "USERNAME": "sa",
#     "PASSWORD": "1234",
#     "DRIVER": "ODBC Driver 17 for SQL Server"  # Nombre exacto del driver
# }

# DB_CONFIG = {
#     "SERVER": "",  # Usa doble barra invertida
#     "DATABASE": "",
#     "USERNAME": "",
#     "PASSWORD": "",
#     "DRIVER": ""  # Nombre exacto del driver
# }

# DB_CONFIG = {
#     "SERVER": "DESKTOP-BIUVOHT\SQLEXPRESS",  # Usa doble barra invertida
#     "DATABASE": "ArandanosDB",
#     "USERNAME": "",
#     "PASSWORD": "",
#     "DRIVER": "ODBC Driver 17 for SQL Server"  # Nombre exacto del driver
# }

# def get_connection_string():
#     # Codificar la contraseña por si tiene caracteres especiales
#     password = quote_plus(DB_CONFIG['PASSWORD'])
#     return (
#         f"mssql+pyodbc://{DB_CONFIG['USERNAME']}:{password}@"
#         f"{DB_CONFIG['SERVER']}/{DB_CONFIG['DATABASE']}?"
#         f"driver={quote_plus(DB_CONFIG['DRIVER'])}"
#     )


