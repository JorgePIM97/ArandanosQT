import os
import subprocess
import sys

def compilar_recursos():
    # Ruta al archivo .qrc
    qrc_file = os.path.join("vista", "utils", "resources", "resources.qrc")
    
    # Ruta de salida
    output_file = os.path.join("vista", "utils", "resources", "resources_rc.py")
    
    # Intenta encontrar rcc.exe
    rcc_path = None
    search_paths = [
        os.path.join(sys.prefix, "Lib", "site-packages", "qt6_applications", "Qt", "bin", "rcc.exe"),
        os.path.join(sys.prefix, "Scripts", "rcc.exe"),
        os.path.join(os.environ["VIRTUAL_ENV"], "Lib", "site-packages", "qt6_applications", "Qt", "bin", "rcc.exe")
    ]
    
    for path in search_paths:
        if os.path.exists(path):
            rcc_path = path
            break
    
    if not rcc_path:
        raise FileNotFoundError("No se encontró rcc.exe en las ubicaciones estándar")
    
    # Comando para compilar
    cmd = [rcc_path, qrc_file, "-o", output_file, "--generator", "python"]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"Recursos compilados exitosamente en {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error al compilar recursos: {e}")
        return False

if __name__ == "__main__":
    compilar_recursos()