from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal
from vista.utils.plantillas.CerrarSesion import Ui_CerrarSesion_Widget

class CerrarSesionWidget(QWidget, Ui_CerrarSesion_Widget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        
        # Configuración de la ventana
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        # Conectar señales de los botones (ya están conectados en el .ui)
        # Los slots ConfirmarCerrarSesion y CancelarCerrarSesion se llamarán automáticamente
        
    def showEvent(self, event):
        """Centrar el widget sobre la ventana principal"""
        if self.parent():
            parent_rect = self.parent().geometry()
            self.move(
                parent_rect.center() - self.rect().center()
            )
        super().showEvent(event)