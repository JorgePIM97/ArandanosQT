# vista/qdialogs/configurar_db_dialog.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFormLayout, QMessageBox,
                             QGroupBox, QProgressBar, QApplication)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
import sys
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

class DatabaseConnectionTester(QThread):
    """Hilo para probar la conexión a la base de datos sin bloquear la UI"""
    connection_result = pyqtSignal(bool, str)
    
    def __init__(self, connection_string):
        super().__init__()
        self.connection_string = connection_string
    
    def run(self):
        try:
            # Crear engine con timeout corto para prueba
            engine = create_engine(
                self.connection_string,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 5}
            )
            
            # Probar conexión ejecutando una consulta simple
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                if result.fetchone():
                    self.connection_result.emit(True, "Conexión exitosa")
                else:
                    self.connection_result.emit(False, "No se pudo ejecutar consulta de prueba")
        except Exception as e:
            self.connection_result.emit(False, f"Error de conexión: {str(e)}")

class ConfigurarDBDialog(QDialog):
    """Dialog para configurar las credenciales de la base de datos"""
    credentials_configured = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurar Base de Datos")
        self.setModal(True)
        self.setFixedSize(500, 400)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        
        # Variables
        self.connection_tester = None
        self.credentials = {}
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Configurar la interfaz de usuario"""
        layout = QVBoxLayout(self)
        
        # Título
        title_label = QLabel("Configuración de Base de Datos")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Información
        info_label = QLabel("Ingrese las credenciales para conectar a su base de datos local:")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; margin: 10px 0;")
        layout.addWidget(info_label)
        
        # Grupo de credenciales
        credentials_group = QGroupBox("Credenciales de Conexión")
        credentials_layout = QFormLayout(credentials_group)
        
        # Campos de entrada
        self.server_edit = QLineEdit()
        self.server_edit.setPlaceholderText("Ej: SERVIDOR\\SQLEXPRESS")
        self.server_edit.setText("E-PIM_15\\SQLEXPRESS")  # Valor por defecto
        
        self.database_edit = QLineEdit()
        self.database_edit.setPlaceholderText("Nombre de la base de datos")
        self.database_edit.setText("ArandanosDB")  # Valor por defecto
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Nombre de usuario")
        self.username_edit.setText("sa")  # Valor por defecto
        
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Contraseña")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.driver_edit = QLineEdit()
        self.driver_edit.setText("ODBC Driver 17 for SQL Server")  # Valor por defecto
        
        # Agregar campos al formulario
        credentials_layout.addRow("Servidor:", self.server_edit)
        credentials_layout.addRow("Base de Datos:", self.database_edit)
        credentials_layout.addRow("Usuario:", self.username_edit)
        credentials_layout.addRow("Contraseña:", self.password_edit)
        credentials_layout.addRow("Driver:", self.driver_edit)
        
        layout.addWidget(credentials_group)
        
        # Barra de progreso para testing
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Botones
        buttons_layout = QHBoxLayout()
        
        self.test_button = QPushButton("Probar Conexión")
        self.test_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        
        self.save_button = QPushButton("Guardar y Continuar")
        self.save_button.setEnabled(False)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover:enabled {
                background-color: #1976D2;
            }
            QPushButton:pressed:enabled {
                background-color: #1565C0;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)
        
        buttons_layout.addWidget(self.test_button)
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)
        
        layout.addLayout(buttons_layout)
        
    def setup_connections(self):
        """Configurar las conexiones de señales"""
        self.test_button.clicked.connect(self.test_connection)
        self.save_button.clicked.connect(self.save_credentials)
        self.cancel_button.clicked.connect(self.reject)
        
        # Conectar Enter en el campo de contraseña para probar conexión
        self.password_edit.returnPressed.connect(self.test_connection)
        
    def get_connection_string(self):
        """Crear string de conexión con las credenciales actuales"""
        password = quote_plus(self.password_edit.text())
        return (
            f"mssql+pyodbc://{self.username_edit.text()}:{password}@"
            f"{self.server_edit.text()}/{self.database_edit.text()}?"
            f"driver={quote_plus(self.driver_edit.text())}"
        )
    
    def test_connection(self):
        """Probar la conexión a la base de datos"""
        if not all([self.server_edit.text(), self.database_edit.text(), 
                   self.username_edit.text(), self.password_edit.text()]):
            QMessageBox.warning(self, "Campos Requeridos", 
                              "Por favor complete todos los campos requeridos.")
            return
        
        # Deshabilitar botón y mostrar progreso
        self.test_button.setEnabled(False)
        self.test_button.setText("Probando...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Progreso indeterminado
        
        # Crear y ejecutar hilo de prueba
        connection_string = self.get_connection_string()
        self.connection_tester = DatabaseConnectionTester(connection_string)
        self.connection_tester.connection_result.connect(self.handle_connection_result)
        self.connection_tester.start()
    
    def handle_connection_result(self, success, message):
        """Manejar el resultado de la prueba de conexión"""
        # Restaurar UI
        self.test_button.setEnabled(True)
        self.test_button.setText("Probar Conexión")
        self.progress_bar.setVisible(False)
        
        if success:
            QMessageBox.information(self, "Conexión Exitosa", 
                                  "¡Conexión establecida correctamente!")
            self.save_button.setEnabled(True)
            
            # Guardar credenciales temporalmente
            self.credentials = {
                "SERVER": self.server_edit.text(),
                "DATABASE": self.database_edit.text(),
                "USERNAME": self.username_edit.text(),
                "PASSWORD": self.password_edit.text(),
                "DRIVER": self.driver_edit.text()
            }
        else:
            QMessageBox.critical(self, "Error de Conexión", 
                               f"No se pudo conectar a la base de datos:\n\n{message}")
            self.save_button.setEnabled(False)
    
    def save_credentials(self):
        """Guardar las credenciales y cerrar el diálogo"""
        if self.credentials:
            self.credentials_configured.emit(self.credentials)
            self.accept()
        else:
            QMessageBox.warning(self, "Prueba de Conexión", 
                              "Por favor pruebe la conexión antes de guardar.")
