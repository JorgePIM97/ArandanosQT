# controlador/facialDetection/checador_cosecha_knn.py
import cv2
import face_recognition
import numpy as np
from io import BytesIO
from datetime import datetime
from db.entities.data_entities import Recolector, Cosecha, get_db, Macrotunel, Entrega
from sqlalchemy import text
from collections import Counter
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QApplication

class FacialRecognitionWorker(QObject):
    frame_ready = pyqtSignal(object)
    face_detected = pyqtSignal(tuple)
    
    def __init__(self):
        super().__init__()
        self.face_recognizer = FaceRecognizerKNN(k=3, threshold=0.62)
        self.cap = None
        self.scale = 0.25
        self.confidence_threshold = 0.62
        self.running = False
        self.freeze_frame = False  
        self.mirror_mode = True  
        self.timer = QTimer()
        self.timer.timeout.connect(self.process_frame)
        self.face_count = 0

    def start(self, camera_index=0):
        if not self.face_recognizer.load_from_db():
            print("No se encontraron recolectores registrados con encodings faciales")
            return False

        self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 848)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        if not self.cap.isOpened():
            print("Error al abrir la cámara")
            return False
        
        # # Propiedad para controlar el modo espejo
        # self.mirror_mode = True  # True para modo espejo, False para normal

        self.running = True
        self.timer.start(30)  # ~30 FPS
        return True

    def stop(self):
        """Método mejorado para detener el worker de manera segura"""
        self.running = False
        self.timer.stop()
        
        # Esperar a que el timer realmente se detenga
        while self.timer.isActive():
            QApplication.processEvents()
            
        if self.cap is not None:
            if self.cap.isOpened():
                self.cap.release()
            self.cap = None

    # def process_frame(self):
    #     if not self.running or not self.cap.isOpened() or self.freeze_frame:
    #         return

    #     ret, frame = self.cap.read()
    #     if not ret:
    #         return
        
    #     # Aplicar modo espejo si está activado
    #     if self.mirror_mode:
    #         frame = cv2.flip(frame, 1)  # 1 = flip horizontal

    #     # Recuadro para limitar el reconocimiento del rostro en el frame
    #     cv2.rectangle(frame, (309, 90), (539, 390), (255, 0, 0), 2)

    #     # Procesamiento de reconocimiento facial
    #     small_frame = cv2.resize(frame, (0, 0), fx=self.scale, fy=self.scale)
    #     rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
    #     rgb_small_frame = cv2.GaussianBlur(rgb_small, (3, 3), 0)

    #     face_locations = face_recognition.face_locations(rgb_small_frame)
    #     face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

    #     current_detection = None
    #     self.face_count = len(face_locations)
        
    #     for face_encoding, face_location in zip(face_encodings, face_locations):
    #         name, emp_info, confidence = self.face_recognizer.recognize_face(face_encoding)
            
    #         # display_name = f"{name} ({confidence*100:.1f}%)" if confidence >= self.confidence_threshold else "DESCONOCIDO"
    #         display_name = f"{name}" if confidence >= self.confidence_threshold else "DESCONOCIDO"
            
    #         y1, x2, y2, x1 = [int(coord / self.scale) for coord in face_location]
    #         color = (0, 255, 0) if name != "DESCONOCIDO" else (0, 0, 255)
            
    #         cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    #         cv2.rectangle(frame, (x1, y2 - 35), (x2, y2), color, cv2.FILLED)
    #         cv2.putText(frame, display_name, (x1 + 6, y2 - 6), 
    #                   cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)
            
    #         # print(self.face_count)

    #         # Almacenar datos del rostro detectado (incluso si es desconocido)
    #         current_detection = (name, emp_info, confidence)
        
    #     # Emitir los datos del rostro detectado
    #     self.face_detected.emit((current_detection, len(face_locations)))
        
    #     # Emitir el frame procesado
    #     self.frame_ready.emit(frame)

    def process_frame(self):
        if not self.running or not self.cap.isOpened() or self.freeze_frame:
            return

        ret, frame = self.cap.read()
        if not ret:
            return
        
        if self.mirror_mode:
            frame = cv2.flip(frame, 1)

        # Coordenadas del rectángulo azul
        # rect_x1, rect_y1 = 309, 90
        # rect_x2, rect_y2 = 539, 390

        rect_x1, rect_y1 = 273, 60
        rect_x2, rect_y2 = 590, 425

        cv2.rectangle(frame, (rect_x1, rect_y1), (rect_x2, rect_y2), (255, 0, 0), 2)

        small_frame = cv2.resize(frame, (0, 0), fx=self.scale, fy=self.scale)
        rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        rgb_small_frame = cv2.GaussianBlur(rgb_small, (3, 3), 0)

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        current_detection = None
        self.face_count = 0  # ← Solo contar rostros dentro del rectángulo

        for face_encoding, face_location in zip(face_encodings, face_locations):
            y1, x2, y2, x1 = [int(coord / self.scale) for coord in face_location]

            # Verificar si el rostro está DENTRO del rectángulo azul
            dentro_del_rectangulo = (
                x1 >= rect_x1 and
                y1 >= rect_y1 and
                x2 <= rect_x2 and
                y2 <= rect_y2
            )

            if not dentro_del_rectangulo:
                # Dibujar en gris los rostros fuera del rectángulo e ignorarlos
                cv2.rectangle(frame, (x1, y1), (x2, y2), (128, 128, 128), 2)
                continue

            # Solo procesar rostros dentro del rectángulo
            self.face_count += 1
            name, emp_info, confidence = self.face_recognizer.recognize_face(face_encoding)

            display_name = f"{name}" if confidence >= self.confidence_threshold else "DESCONOCIDO"

            color = (0, 255, 0) if name != "DESCONOCIDO" else (0, 0, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.rectangle(frame, (x1, y2 - 35), (x2, y2), color, cv2.FILLED)
            cv2.putText(frame, display_name, (x1 + 6, y2 - 6),
                        cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)

            current_detection = (name, emp_info, confidence)

        self.face_detected.emit((current_detection, self.face_count))
        self.frame_ready.emit(frame)

    def set_freeze_frame(self, freeze):
        """Método para controlar la congelación desde fuera"""
        self.freeze_frame = freeze

class FaceRecognizerKNN:
    def __init__(self, k=3, threshold=0.62):
        self.k = k
        self.threshold = threshold
        self.known_encodings = []
        self.class_names = []
        self.empleados_info = []
    
    def load_from_db(self):
        """Carga los datos de los empleados desde la base de datos"""
        known_encodings, class_names, empleados_info = self.cargar_empleados_desde_db()
        if not class_names:
            return False
        
        self.known_encodings = known_encodings
        self.class_names = class_names
        self.empleados_info = empleados_info
        return True  

    def recognize_face(self, face_encoding):
        if not self.known_encodings:
            return "DESCONOCIDO", None, 0.0

        distances = np.linalg.norm(self.known_encodings - face_encoding, axis=1)

        # Ajustar k si hay menos encodings que k
        k = min(self.k, len(distances))
        if k == 0:
            return "DESCONOCIDO", None, 0.0

        k_indices = np.argpartition(distances, k - 1)[:k]  # k-1 por índice 0-based
        k_distances = distances[k_indices]
        k_names = [self.class_names[i] for i in k_indices]
        k_info = [self.empleados_info[i] for i in k_indices]

        min_distance = min(k_distances)
        confidence = 1.0 / (1.0 + min_distance)

        if confidence >= self.threshold:
            most_common = Counter(k_names).most_common(1)[0]
            name = most_common[0]
            emp_info = k_info[k_names.index(name)]
            return name, emp_info, confidence

        return "DESCONOCIDO", None, confidence


    def cargar_empleados_desde_db(self):
        session = get_db()
        try:
            empleados = session.query(
                Recolector.id_Recolector, 
                Recolector.Nombre_Completo, 
                Recolector.Encoder
            ).filter(Recolector.Encoder.isnot(None)).all()
            
            known_encodings = []
            class_names = []
            empleados_info = []
            
            for id_recolector, nombre, encoding_bytes in empleados:
                try:
                    encoding = np.load(BytesIO(encoding_bytes), allow_pickle=True)
                    known_encodings.append(encoding)
                    class_names.append(nombre)
                    empleados_info.append((id_recolector, nombre))
                except Exception as e:
                    print(f"Error al cargar encoding para {nombre}: {str(e)}")
                    continue
            
            return known_encodings, class_names, empleados_info
        except Exception as e:
            print(f"Error al cargar empleados: {str(e)}")
            return [], [], []
        finally:
            session.close()

