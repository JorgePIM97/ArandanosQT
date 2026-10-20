from PyQt6.QtWidgets import QMessageBox, QDialog
from vista.utils.plantillas.Login import Ui_Login_Dialog
from PyQt6.QtCore import Qt

class LoginDialog(QDialog, Ui_Login_Dialog):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.resize(1366, 1200)
        self.setupUi(self)
        self.showNormal()
        self.EntrarLogin_Btn.clicked.connect(self.verificar_login)

    def verificar_login(self):
        usuario = self.UsuarioLogin_lineEdit.text().upper()
        contraseña = self.PasswordLogin_lineEdit.text().upper()

        if usuario == "ADMIN" and contraseña == "raul":  # Reemplaza con tu lógica real
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Credenciales incorrectas")

    # def closeEvent(self, event):
    #     """Evitar cierre accidental del diálogo"""
    #     reply = QMessageBox.question(
    #         self, "Salir", "¿Desea cerrar la aplicación?",
    #         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    #     )
    #     if reply == QMessageBox.StandardButton.Yes:
    #         QApplication.quit()  # Cerrar toda la aplicación
    #     else:
    #         event.ignore()  # Ignorar el cierre