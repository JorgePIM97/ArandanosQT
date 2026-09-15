#controlador/facialDetection/encoder.py
import cv2
import face_recognition
import numpy as np
from io import BytesIO
from db.entities.data_entities import get_db, Recolector

session = get_db()

def guardar_empleado(nombre, imagen, encoding, localidad, telefono, acceso, id_cuadrilla):
    try:
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

def get_input(prompt):
    """Función genérica para obtener entrada del usuario"""
    return input(prompt + " (o 'q' para salir): ")

def main():
    # Inicializar captura de video
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: No se pudo abrir la cámara")
        return

    while True:
        # Obtener datos del nuevo empleado
        name = get_input("Ingrese el nombre del empleado")
        if name.lower() == 'q':
            break
            
        localidad = get_input("Ingrese el nombre de la localidad")
        if localidad.lower() == 'q':
            break
            
        telefono = get_input("Ingrese el número de teléfono")
        if telefono.lower() == 'q':
            break
            
        acceso = input("¿Tiene acceso? (S/N): ").upper() == 'S'
        cuadrilla = get_input("Ingrese id de cuadrilla")
        if cuadrilla.lower() == 'q':
            break

        # Modo de captura para el empleado actual
        capturing = True
        while capturing:
            success, frame = cap.read()
            if not success:
                print("Error al capturar el frame")
                break

            # Mostrar instrucciones en el frame
            cv2.putText(frame, f"Registrando: {name}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, "Presione 'c' para capturar", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, "Presione 'n' para nuevo empleado", (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, "Presione 'q' para salir", (10, 120), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            cv2.imshow("Registro Facial - Captura de Rostros", frame)

            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('c'):  # Capturar rostro
                img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                encodings = face_recognition.face_encodings(img_rgb)

                if encodings:
                    if guardar_empleado(name, frame, encodings[0], localidad, telefono, acceso, cuadrilla):
                        print(f"Registro completado para {name}")
                        # No salimos, solo mostramos mensaje de éxito
                        cv2.putText(frame, "¡Registro exitoso!", (10, 150), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        cv2.imshow("Registro Facial - Captura de Rostros", frame)
                        cv2.waitKey(2000)  # Mostrar mensaje por 2 segundos
                    else:
                        print("Error al guardar en la base de datos")
                else:
                    print("No se detecto un rostro. Intente nuevamente.")
            
            elif key == ord('n'):  # Nuevo empleado
                capturing = False
                
            elif key == ord('q'):  # Salir completamente
                cap.release()
                cv2.destroyAllWindows()
                return

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
