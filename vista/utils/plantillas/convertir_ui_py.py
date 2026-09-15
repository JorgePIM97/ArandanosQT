import subprocess
import sys

# Rutas de entrada y salida
ui_file = r"C:\ArandanosQT\vista\utils\plantillas\Arandanos.ui"
py_file = r"C:\ArandanosQT\vista\utils\plantillas\Arandanos.py"

subprocess.run([
    sys.executable, "-m", "PyQt6.uic.pyuic",
    "-x", ui_file,
    "-o", py_file
], check=True)

print("Conversión completada:", py_file)