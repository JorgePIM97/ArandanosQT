# controlador/impresora/printer_connection.py
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from controlador.impresora.print_tickets import TicketPrinter


class PrinterCheckWorker(QObject):
    finished = pyqtSignal(bool)  # True = conectada, False = no conectada

    def run(self):
        impresora = TicketPrinter()
        online = impresora.is_printer_online()
        self.finished.emit(online)


class PrinterConnectionManager:
    def __init__(self, parent=None):
        self.parent = parent
        self.thread = None
        self.worker = None

    def start_check(self, callback):
        self.thread = QThread()
        self.worker = PrinterCheckWorker()
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(callback)

        # Limpieza
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()