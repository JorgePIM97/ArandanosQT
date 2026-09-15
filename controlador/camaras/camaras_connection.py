# controlador/camaras/camaras_connection.py

import cv2
from PyQt6.QtCore import QObject, QThread, pyqtSignal


class CameraConnectionWorker(QObject):
    """
    Verifica si las cámaras requeridas están conectadas.
    """
    finished = pyqtSignal(bool, list)

    def __init__(self, required_ports=None):
        super().__init__()

        if required_ports is None:
            required_ports = [0, 1]

        self.required_ports = required_ports

    def run(self):
        detected_ports = []

        for port in self.required_ports:
            cap = cv2.VideoCapture(port, cv2.CAP_DSHOW)

            if cap.isOpened():
                ret, _ = cap.read()

                if ret:
                    detected_ports.append(port)

            cap.release()

        cameras_ok = len(detected_ports) == len(self.required_ports)

        self.finished.emit(cameras_ok, detected_ports)


class CameraConnectionManager:
    """
    Administrador del hilo de verificación.
    """

    def __init__(self, parent=None):
        self.parent = parent
        self.thread = None
        self.worker = None

    def start_check(self, callback):
        self.thread = QThread()

        self.worker = CameraConnectionWorker([0, 1])
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(callback)

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()