# main.py - Sistema para control de cosecha de arandanos
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*sipPyTypeDict.*")
# Librerias de PyQT6 para UI
from controlador.checador import listar_checks
from controlador.lineas import listar_linea, listar_linea_cosecha
from PyQt6.QtWidgets import QComboBox, QInputDialog, QApplication, QMainWindow, QTableWidgetItem, QDateTimeEdit, QTableWidget, QHeaderView, QMessageBox, QLabel, QDialog, QLineEdit, QVBoxLayout, QDialogButtonBox, QFileDialog
from PyQt6.QtCore import Qt, QTimer, QDate, QEvent 
from PyQt6.QtCore import QDateTime
from PyQt6.QtGui import QIcon, QImage, QPixmap, QFont
from PyQt6.QtCore import QThread
# Importar OpenCV y librerias para el reconocimiento facial
import cv2  
import face_recognition
import numpy as np
from controlador.facialDetection.checador_cosecha_knn import FacialRecognitionWorker
from datetime import datetime, date
# Importar recursos para mostrar iconos en UI 
from vista.utils.resources import resources_rc
# Librerias locales
import sys
from sqlalchemy import text
import pandas as pd
import os
import win32api  # Necesario para detectar unidades en Windows
import win32file  # Módulo necesario para GetDriveType
from vista.utils.plantillas.Arandanos import Ui_ArandanoMain
from controlador.cuadrilleros import listar_cuadrillas, crear_cuadrilla, listar_cuadrillas_comboBox, actualizar_cuadrilla, obtener_clave_cuadrillero
from controlador.colectores import listar_recolectores, crear_recolector, actualizar_colector, eliminar_colector, obtener_cuadrilla_por_nombre, actualizar_colector_con_encoder
from controlador.tablas import listar_tabla_cosecha, listar_tabla, crear_tabla, actualizar_tabla, eliminar_tabla, listar_tabla_formulario
from controlador.macrotuneles import listar_macrotunel, crear_macrotunel, actualizar_macrotunel, listar_macrotunel_cosecha, eliminar_macrotunel
from controlador.cosechas import registrar_cosecha, get_peso, obtener_suma_pesos_fecha_actual, cuadrillero_primera_cosecha
from controlador.entregas import iniciar_entrega, finalizar_entrega, Total_Entregas_Hoy_Recolector, Obtener_ID_Recolector, Obtener_Calificaciones_Separadas, Obtener_Peso_Total_Cosechador, Obtener_Peso_Total_Entrega, Obtener_Resumen_Colector, Obtener_Corte_Dia
from db.entities.data_entities import Recolector, Macrotunel, get_db, Cuadrilla, Linea
from controlador.impresora.print_tickets import TicketPrinter
from controlador.vistas import SabanaVistas
from db.data_connection.config_db import guardar_credenciales
from db.data_connection.config_db import cargar_credenciales, get_id_carrito
from db.data_connection.config_db import probar_conexion, tablas_inicializadas
from controlador.reportes_memoria import ReportesMemoria
from controlador.fases import crear_fase, actualizar_fase, eliminar_fase, listar_fases, listar_fases_cosecha, listar_fases
from controlador.lineas import crear_linea, actualizar_linea, eliminar_linea
from controlador.modalidad import ModalidadControlador
from controlador.accesos.keys import KeysAcceso
from controlador.camaras.camaras_connection import CameraConnectionManager
from controlador.bascula.bascula_connection import BasculaTorreyLPCR_USB
import subprocess
import time
import keyboard
from controlador.impresora.printer_connection import PrinterConnectionManager
# import ctypes

# if not ctypes.windll.shell32.IsUserAnAdmin():
#     ctypes.windll.shell32.ShellExecuteW(
#         None,
#         "runas",
#         sys.executable,
#         __file__,
#         None,
#         1
#     )
#     sys.exit()

#Clase Principal
class ArandanosControl(QMainWindow, Ui_ArandanoMain):

    def __init__(self):
        super(ArandanosControl, self).__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.resize(1366, 1200)
        self.setupUi(self)
        self.stackedWidget_Principal.setCurrentIndex(7) 
        self.showNormal()

        # # Verificar conexión antes de seguir
        # if probar_conexion():
        #     self.inicializar_dependencias_db()
        #     self.iniciar_id_carrito()
        # else:
        #     QMessageBox.warning(self, "Error de conexión", "No se pudo conectar a la base de datos. Verifica tus credenciales.")

        if probar_conexion():
            self.inicializar_dependencias_db()
            self.iniciar_id_carrito()
        else:
            # Distinguir entre sin credenciales y sin conexión
            creds = cargar_credenciales()
            if not all([creds.get("SERVER"), creds.get("DATABASE"),
                        creds.get("USERNAME"), creds.get("PASSWORD")]):
                QMessageBox.warning(self, "Sin configuración",
                                    "No se encontraron credenciales de base de datos.\n"
                                    "Configure la conexión antes de continuar.")
            else:
                QMessageBox.warning(self, "Error de conexión",
                                    "No se pudo conectar a la base de datos.\n"
                                    "Verifica que el servidor esté disponible y las credenciales sean correctas.")

        # Configurar el reloj en tiempo real
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_reloj)
        self.timer.start(1000)  # Actualizar cada 1000 ms (1 segundo)
        self.update_reloj()

        # Modulos
        self.Modulos_Invisibles()
        self.Back_MenuPrincipalModulos_Btn.setVisible(False)

        # Variables para la cámara
        self.cap = None
        self.cap_cosecha = None
        self.cap_actualizar = None
        self.timer_registroFacial = QTimer()
        self.timer_registroCosecha = QTimer()
        self.timer_deteccionFacial = QTimer()
        self.timer_registroActualizar = QTimer()
        self.timer_registroFacial.timeout.connect(self.update_frame)
        self.timer_registroCosecha.timeout.connect(self.update_frame_cosecha)
        self.timer_registroActualizar.timeout.connect(self.update_frame_rostro_actualizado)


        # Variables para almacenar temporalmente la imagen y encoding
        self.captured_image = None
        self.captured_image_actualizar = None
        self.image_captured_cosecha = None
        self.face_encoding = None
        self.face_encoding_actualizado = None
        self.image_captured = False  # Flag para controlar la visualización
        self.image_captured_actualizar = False

        # Puertos de camaras
        self.puerto_facial = int(0)
        self.puerto_cosecha = int(1)

        # Configuración del reconocimiento facial
        self.facial_thread = QThread()
        self.facial_worker = FacialRecognitionWorker()
        self.facial_worker.moveToThread(self.facial_thread)
        self.facial_worker.frame_ready.connect(self.update_facial_recognition_frame)
        self.facial_thread.start()

        # Configuración del reconocimiento facial checador cosecha
        self.checador_thread = QThread()
        self.checador_worker = FacialRecognitionWorker()
        self.checador_worker.moveToThread(self.checador_thread)
        self.checador_worker.frame_ready.connect(self.update_facial_checador_frame)
        self.checador_thread.start()

        # Añadir estas variables
        self.current_face_data = None  # Almacenará (nombre, emp_info, confidence)
        self.freeze_frame = False
        self.last_frame = None
        self.facial_worker.face_detected.connect(self.handle_face_detected)

        # Añadir estas variables
        self.current_face_data_checador = None  # Almacenará (nombre, emp_info, confidence)
        self.freeze_frame_checador = False
        self.last_frame_checador = None
        self.checador_worker.face_detected.connect(self.handle_face_detected_checador)

        # Nueva variable para control de entrega
        self.current_entrega_id = None
        self.flag_current_entrega = False

        # Configurar datos de estacion
        # self.Estacion_Datos() 

        # Estado inicial calendario
        self.fin_calendar_activo = True  

        # Conectar señales para proteger claves
        self.CrearClaveFase_lineEdit.textChanged.connect(lambda: self.proteger_clave("F", self.CrearClaveFase_lineEdit))
        self.ActualizarClaveFase_lineEdit.textChanged.connect(lambda: self.proteger_clave("F", self.ActualizarClaveFase_lineEdit))


        self.CrearClaveTabla_lineEdit.textChanged.connect(lambda: self.proteger_clave("T", self.CrearClaveTabla_lineEdit))
        self.ActualizarClaveTabla_lineEdit.textChanged.connect(lambda: self.proteger_clave("T", self.ActualizarClaveTabla_lineEdit))

        self.CrearClaveMacrotunel_lineEdit.textChanged.connect(lambda: self.proteger_clave("MT", self.CrearClaveMacrotunel_lineEdit))
        self.ActualizarClaveMacrotunel_lineEdit.textChanged.connect(lambda: self.proteger_clave("MT", self.ActualizarClaveMacrotunel_lineEdit))

        self.CrearClaveLinea_lineEdit.textChanged.connect(lambda: self.proteger_clave("L", self.CrearClaveLinea_lineEdit))
        self.ActualizarClaveLinea_lineEdit.textChanged.connect(lambda: self.proteger_clave("L", self.ActualizarClaveLinea_lineEdit))

        self.CrearCuadrilleroClave_lineEdit.textChanged.connect(lambda: self.proteger_clave("C-", self.CrearCuadrilleroClave_lineEdit))
        self.ActualizarClave_lineEdit.textChanged.connect(lambda: self.proteger_clave("C-", self.ActualizarClave_lineEdit))

        # Cifrar Passwords al escribir
        self.PasswordLogin_lineEdit.setEchoMode(QLineEdit.EchoMode.Password)
        self.PasswordDB_lineEdit.setEchoMode(QLineEdit.EchoMode.Password)

        # Señal para habilitas cuadrilleros de cosecha
        self.CuadrilleroConfiguracion_comboBox.installEventFilter(self)
        self.CuadrilleroConfiguracion_comboBox.activated.connect(self.on_cuadrilla_seleccionada)
        self._cuadrillas_cargadas = False

        self.setup_protected_combobox()

        self.teclas_bloqueadas = False

        # Bloquear teclas al iniciar
        self.bloquear_teclas()

        self.face_count = 0

        # # Verificar cámaras al iniciar
        # self.camera_checker = CameraConnectionManager(self)
        # self.camera_checker.start_check(self.on_cameras_checked)

        # self.camaras_conectas = False
        # self.bascula_conectada = False

        # Verificar impresora al iniciar
        # self.on_impresora_checked()

        self.RECT_X1, self.RECT_Y1 = 273, 60
        self.RECT_X2, self.RECT_Y2 = 590, 425

    def iniciar_id_carrito(self):
        id_carrito = get_id_carrito()

        if not id_carrito:
            QMessageBox.warning(self, "Error Id Carrito", "No se encontró Id del carrito, ingrese uno.")
        else:
            self.EstacionPrincipalText_Lbl.setText(str(id_carrito))

    def on_cameras_checked(self, cameras_ok, detected_ports):

        if cameras_ok:

            self.CamarasTestigo_lbl.setStyleSheet("""
                QToolButton{
                    background-color: #8bc34a;
                    border-radius: 10px;
                }
            """)
            self.camaras_conectas = True
            print(f"Cámaras detectadas: {detected_ports}")

        else:

            self.CamarasTestigo_lbl.setStyleSheet("""
                QToolButton{
                    background-color: rgb(255, 0, 0);
                    border-radius: 10px;
                }
            """)
            self.camaras_conectas = False
            print(
                f"ERROR: Cámaras no conectadas, verifique conexión."
                f"Puertos encontrados: {detected_ports}"
            )

            QMessageBox.critical(
                self,
                "Error de cámaras",
                "Cámaras no conectadas, verifique conexión.\nNo se detectaron las cámaras requeridas en los puertos 0 y 1."
            )
            self.habilitar_modulos()

    def on_bascula_checked(self):
        bascula = BasculaTorreyLPCR_USB()
        bascula_port = bascula.detectar_puerto()
        if not bascula_port:
            self.BasculaTestigo_toolButton.setStyleSheet("""
                QToolButton{
                    background-color: rgb(255, 0, 0);
                    border-radius: 10px;
                }
            """)
            QMessageBox.critical(
                self,
                "Error en bascula",
                "Bascula no conectada, verifique su conexión."
            )

        else:
            self.BasculaTestigo_toolButton.setStyleSheet("""
                QToolButton{
                    background-color: #8bc34a;
                    border-radius: 10px;
                }
            """)
            return True
        
    def on_impresora_checked(self):
        impresora = TicketPrinter()

        if not impresora.printer_name or not impresora.is_printer_online():
            self.ImpresoraTestigo_toolButton.setStyleSheet("""
                QToolButton{
                    background-color: rgb(255, 0, 0);
                    border-radius: 10px;
                }
            """)
            QMessageBox.critical(
                self,
                "Error en impresora",
                "Impresora no conectada, verifique su conexión."
            )
            self.boton_camara_apagado()
            self.boton_impresora_apagado()
            self.habilitar_modulos()
            return False

        self.ImpresoraTestigo_toolButton.setStyleSheet("""
            QToolButton{
                background-color: #8bc34a;
                border-radius: 10px;
            }
        """)
        return True

    def _on_printer_checked_finalizar(self, online):
        if not online:
            self.ImpresoraTestigo_toolButton.setStyleSheet("""
                QToolButton{
                    background-color: rgb(255, 0, 0);
                    border-radius: 10px;
                }
            """)
            QMessageBox.warning(
                self,
                "Impresora no conectada",
                "No se puede finalizar la cosecha sin la impresora conectada.\nVerifique la conexión e intente de nuevo."
            )
            return

        self.ImpresoraTestigo_toolButton.setStyleSheet("""
            QToolButton{
                background-color: #8bc34a;
                border-radius: 10px;
            }
        """)

        try:
            if hasattr(self, 'timer_registroCosecha') and self.timer_registroCosecha.isActive():
                self.timer_registroCosecha.stop()

            if hasattr(self, 'cap_cosecha') and self.cap_cosecha is not None:
                self.cap_cosecha.release()
                self.cap_cosecha = None

            self.FotoCosechaCalificada_Lbl.clear()
            self.FotoCosechaCalificada_Lbl.setText("Cámara no activa")

            self.BotonVerdeOscuro(self.ConfirmarConfiguracionColector_Btn)
            self.ConfirmarConfiguracionColector_Btn.setEnabled(False)
            self.stackedWidget_Cosecha.setCurrentIndex(0)

            if self.current_entrega_id:
                if finalizar_entrega(self.current_entrega_id):
                    peso_total = Obtener_Peso_Total_Entrega(self.current_entrega_id)
                    print(f"Peso total de la entrega: {peso_total} kg")
                    self.Ticket_De_Vuelta(peso_total)

            self.CuadrilleroRegistrado_Lbl.clear()
            self.CuadrillaDatosCosechaText_Lbl.clear()
            self.CuadrilleroConfiguracion_comboBox.clear()
            self.CuadrilleroRegistrado_Lbl.clear()
            self.cargar_modalidades_comboBox_cosecha()

            self.flag_current_entrega = False
            self.current_entrega_id = None
            self.image_captured_cosecha = False
            self.last_cosecha_frame = None
            self.BuenaCalidad_Btn.setEnabled(True)
            self.RegularCalidad_Btn.setEnabled(True)
            self.MalaCalidad_Btn.setEnabled(True)
            self.LimpiarPesoCalificacion()

        except Exception as e:
            QMessageBox.warning(self, "Advertencia",
                            f"Ocurrió un error al finalizar la cosecha: {str(e)}")
        finally:
            self.ReiniciarFaceRecognition()
            self.NombreCompleto_listWidget.setVisible(False)
            self.TomarFotoRecognition_stackedWidget.setCurrentIndex(0)
            self.stackedWidget_Cosecha.setCurrentIndex(0)

    # def ProbarConexionCamaras(self):
    #     self.camera_checker = CameraConnectionManager(self)
    #     self.camera_checker.start_check(self.on_cameras_checked)

    def inicializar_dependencias_db(self):
        total = self.Peso_Total_Estacion()
        self.TotalCosechadoPrincipalText_Lbl.setText(f"{str(total)} Kg")

        self.configurar_tabla_cuadrilleros()
        self.configurar_tabla_colectores()
        self.configurar_tabla_fases()
        self.configurar_tabla_tablas()
        self.configurar_tabla_macrotunel()
        self.configurar_tabla_linea()
        self.configurar_tabla_checkin()

        # Configuracion de tabla vista resumen
        self.configurar_tabla_vista()

        # self.NombreRecolectorVista_lineEdit.textChanged.connect(lambda: self.mostrar_vista_en_tabla(
        #     fecha_inicio=self.Inicio_calendarWidget.selectedDate().toString("yyyy-MM-dd"),
        #     fecha_fin=self.Fin_calendarWidget.selectedDate().toString("yyyy-MM-dd"),
        #     nombre_recolector=self.NombreRecolectorVista_lineEdit.text()
        # ))
        # self.TablaVista_comboBox.currentTextChanged.connect(lambda: self.mostrar_vista_en_tabla(
        #     fecha_inicio=self.Inicio_calendarWidget.selectedDate().toString("yyyy-MM-dd"),
        #     fecha_fin=self.Fin_calendarWidget.selectedDate().toString("yyyy-MM-dd"),
        #     tabla=self.TablaVista_comboBox.currentText(),
        #     nombre_recolector=self.NombreRecolectorVista_lineEdit.text()
        # ))
        # self.MacrotunelVista_comboBox.currentTextChanged.connect(lambda: self.mostrar_vista_en_tabla(
        #     fecha_inicio=self.Inicio_calendarWidget.selectedDate().toString("yyyy-MM-dd"),
        #     fecha_fin=self.Fin_calendarWidget.selectedDate().toString("yyyy-MM-dd"),
        #     macrotunel=self.MacrotunelVista_comboBox.currentText(),
        #     nombre_recolector=self.NombreRecolectorVista_lineEdit.text()
        # ))

        # self.Inicio_calendarWidget.clicked.connect(self.actualizar_vista)
        # self.Fin_calendarWidget.clicked.connect(self.actualizar_vista)
        # En inicializar_dependencias_db — reemplaza los connects de mostrar_vista_en_tabla
        self.NombreRecolectorVista_lineEdit.textChanged.connect(lambda: self.mostrar_vista_en_tabla(
            fecha_inicio=self.Inicio_calendarWidget.selectedDate().toString("yyyy-MM-dd"),
            fecha_fin=self.Fin_calendarWidget.selectedDate().toString("yyyy-MM-dd"),
            nombre_recolector=self.NombreRecolectorVista_lineEdit.text(),
            fase=self.FaseVista_comboBox.currentText(),
            tabla=self.TablaVista_comboBox.currentText(),
            macrotunel=self.MacrotunelVista_comboBox.currentText(),
            linea=self.LineaVista_comboBox.currentText()
        ))
        self.FaseVista_comboBox.currentTextChanged.connect(lambda: self.mostrar_vista_en_tabla(
            fecha_inicio=self.Inicio_calendarWidget.selectedDate().toString("yyyy-MM-dd"),
            fecha_fin=self.Fin_calendarWidget.selectedDate().toString("yyyy-MM-dd"),
            nombre_recolector=self.NombreRecolectorVista_lineEdit.text(),
            fase=self.FaseVista_comboBox.currentText(),
            tabla=self.TablaVista_comboBox.currentText(),
            macrotunel=self.MacrotunelVista_comboBox.currentText(),
            linea=self.LineaVista_comboBox.currentText()
        ))
        self.TablaVista_comboBox.currentTextChanged.connect(lambda: self.mostrar_vista_en_tabla(
            fecha_inicio=self.Inicio_calendarWidget.selectedDate().toString("yyyy-MM-dd"),
            fecha_fin=self.Fin_calendarWidget.selectedDate().toString("yyyy-MM-dd"),
            nombre_recolector=self.NombreRecolectorVista_lineEdit.text(),
            fase=self.FaseVista_comboBox.currentText(),
            tabla=self.TablaVista_comboBox.currentText(),
            macrotunel=self.MacrotunelVista_comboBox.currentText(),
            linea=self.LineaVista_comboBox.currentText()
        ))
        self.MacrotunelVista_comboBox.currentTextChanged.connect(lambda: self.mostrar_vista_en_tabla(
            fecha_inicio=self.Inicio_calendarWidget.selectedDate().toString("yyyy-MM-dd"),
            fecha_fin=self.Fin_calendarWidget.selectedDate().toString("yyyy-MM-dd"),
            nombre_recolector=self.NombreRecolectorVista_lineEdit.text(),
            fase=self.FaseVista_comboBox.currentText(),
            tabla=self.TablaVista_comboBox.currentText(),
            macrotunel=self.MacrotunelVista_comboBox.currentText(),
            linea=self.LineaVista_comboBox.currentText()
        ))
        self.LineaVista_comboBox.currentTextChanged.connect(lambda: self.mostrar_vista_en_tabla(
            fecha_inicio=self.Inicio_calendarWidget.selectedDate().toString("yyyy-MM-dd"),
            fecha_fin=self.Fin_calendarWidget.selectedDate().toString("yyyy-MM-dd"),
            nombre_recolector=self.NombreRecolectorVista_lineEdit.text(),
            fase=self.FaseVista_comboBox.currentText(),
            tabla=self.TablaVista_comboBox.currentText(),
            macrotunel=self.MacrotunelVista_comboBox.currentText(),
            linea=self.LineaVista_comboBox.currentText()
        ))
        self.Inicio_calendarWidget.clicked.connect(self.actualizar_vista)
        self.Fin_calendarWidget.clicked.connect(self.actualizar_vista)

        # self.FaseConfiguracion_comboBox.currentTextChanged.connect(self.cargar_fases_comboBox_cosecha)
        self.TablaConfiguracion_comboBox.currentTextChanged.connect(self.cargar_macrotuneles_comboBox_cosecha)

        # self.TablaVista_comboBox.currentTextChanged.connect(self.cargar_macrotuneles_comboBox_vista)

        # self.cargar_tablas_comboBox_vista()
        # self.cargar_macrotuneles_comboBox_vista()

        # self.setup_autocompletado()


    # def setup_autocompletado(self):
    #     """Configura el sistema de autocompletado para el nombre del recolector"""
    #     # Ocultar inicialmente el listWidget
    #     self.NombreCompleto_listWidget.setVisible(False)
        
    #     # Conectar señales
    #     self.NombreCompletoText_lineEdit.textChanged.connect(self.buscar_recolectores)
    #     self.NombreCompleto_listWidget.itemClicked.connect(self.seleccionar_recolector)
        
    #     # Configurar para que mantenga su posición en el diseño
    #     self.NombreCompleto_listWidget.setWindowFlags(Qt.WindowType.Widget)  # No usar Popup
    #     self.NombreCompleto_listWidget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
    # def buscar_recolectores(self, texto):
    #     """Busca recolectores según el texto ingresado"""
    #     # Siempre hacer la búsqueda sin importar cuántos caracteres lleve
    #     nombres_recolectores = self.obtener_nombres_recolectores(texto)
        
    #     if nombres_recolectores:
    #         self.mostrar_resultados(nombres_recolectores)
    #     else:
    #         self.NombreCompleto_listWidget.setVisible(False)
            
    def obtener_nombres_recolectores(self, texto_busqueda):
        """Consulta la base de datos para obtener nombres de recolectores que coincidan"""
        try:
            print("Obteniendo recolectores con texto:", texto_busqueda)
            session = get_db()
            recolectores = session.query(Recolector.Nombre_Completo).filter(
                Recolector.Nombre_Completo.ilike(f"%{texto_busqueda}%")
            ).all()
            print(f"Recolectores encontrados: {[r[0] for r in recolectores]}")
            return [r[0] for r in recolectores] if recolectores else []

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Ocurrió un error al buscar recolectores:\n{e}")
            return []
        finally:
            try:
                session.close()
            except:
                pass

    def mostrar_resultados(self, resultados):
        """Muestra los resultados en el listWidget"""
        self.NombreCompleto_listWidget.clear()
        
        for resultado in resultados:
            self.NombreCompleto_listWidget.addItem(resultado)
            
        # Mostrar u ocultar según haya resultados
        self.NombreCompleto_listWidget.setVisible(len(resultados) > 0)
        
        # Ajustar el tamaño según el contenido
        self.ajustar_tamano_lista()
        
    def ajustar_tamano_lista(self):
        """Ajusta el tamaño del listWidget según su contenido"""
        count = self.NombreCompleto_listWidget.count()
        if count == 0:
            return
            
        # Calcular altura necesaria
        height = 0
        for i in range(min(count, 5)):  # Máximo 5 items visibles
            height += self.NombreCompleto_listWidget.sizeHintForRow(i)
            
        # Añadir márgenes
        height += 2 * self.NombreCompleto_listWidget.frameWidth()
        
        # Establecer altura
        self.NombreCompleto_listWidget.setMinimumHeight(height)
        self.NombreCompleto_listWidget.setMaximumHeight(height)
        
    # def seleccionar_recolector(self, item):
    #     try:
    #         print(f"Seleccionaste: {item.text()}")
            
    #         # Desconectar temporalmente textChanged para evitar loop o crash
    #         self.NombreCompletoText_lineEdit.textChanged.disconnect()

    #         self.NombreCompletoText_lineEdit.setText(item.text())
    #         self.NombreCompleto_listWidget.setVisible(False)
    #         self.NombreCompletoText_lineEdit.setFocus()

    #         # Reconectar después
    #         self.NombreCompletoText_lineEdit.textChanged.connect(self.buscar_recolectores)

    #     except Exception as e:
    #         import traceback
    #         traceback.print_exc()
    #         QMessageBox.critical(self, "Error", f"Ocurrió un error al seleccionar el recolector:\n{e}")


    def start_search_timer(self):
        """Inicia el timer para la búsqueda incremental"""
        self.search_timer.stop()  # Cancelar cualquier búsqueda pendiente
        self.search_timer.start(300)  # 300ms de delay

    def Peso_Total_Estacion(self):
        total_hoy = obtener_suma_pesos_fecha_actual()
        return total_hoy

    # def Estacion_Datos(self):
    #     self.EstacionPrincipalText_Lbl.setText("1")

    def configurar_tabla_cuadrilleros(self):
        """Configuración inicial de la tabla de cuadrilleros"""
        self.Cuadrilleros_tableWidget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.Cuadrilleros_tableWidget.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.Cuadrilleros_tableWidget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Configurar headers
        self.Cuadrilleros_tableWidget.setColumnCount(4)
        self.Cuadrilleros_tableWidget.setHorizontalHeaderLabels(['ID', 'CLAVE', 'RESPONSABLE', 'LOCALIDAD'])

        # Ajustar columnas
        header = self.Cuadrilleros_tableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        # Cargar datos iniciales
        self.mostrar_cuadrillas_en_tabla()

    def configurar_tabla_colectores(self):
        """Configuración inicial de la tabla de colectores"""
        self.Colectores_tableWidget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.Colectores_tableWidget.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.Colectores_tableWidget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Configurar headers
        self.Colectores_tableWidget.setColumnCount(5)
        self.Colectores_tableWidget.setHorizontalHeaderLabels(['ID', 'NOMBRE', 'LOCALIDAD', 'CUADRILLA', 'TELÉFONO'])
        
        # Ajustar columnas
        header = self.Colectores_tableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        
        # Cargar datos iniciales
        self.mostrar_recolectores_en_tabla()

    def mostrar_recolectores_en_tabla(self):
        """Carga los datos de recolectores en la tabla"""
        try:
            colectores = listar_recolectores()
            self.Colectores_tableWidget.setRowCount(len(colectores))
            
            for row, colector in enumerate(colectores):
                # ID (no editable)
                id_item = QTableWidgetItem(str(colector['id_Colector']))
                id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.Colectores_tableWidget.setItem(row, 0, id_item)
                
                # Resto de campos
                self.Colectores_tableWidget.setItem(row, 1, QTableWidgetItem(colector['Nombre_Colector']))
                self.Colectores_tableWidget.setItem(row, 2, QTableWidgetItem(colector['Localidad'] or ""))
                self.Colectores_tableWidget.setItem(row, 3, QTableWidgetItem(colector['Cuadrilla'] or ""))
                self.Colectores_tableWidget.setItem(row, 4, QTableWidgetItem(colector['Telefono'] or ""))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los colectores:\n{str(e)}")
    ####################################################################################################
    #                      CONFIGURAR TABLA FASE self.Fase_tableWidget
    ####################################################################################################
    def configurar_tabla_fases(self):
        """Configuración inicial de la tabla de tablas"""
        self.Fase_tableWidget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.Fase_tableWidget.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.Fase_tableWidget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Configurar headers
        self.Fase_tableWidget.setColumnCount(4)
        self.Fase_tableWidget.setHorizontalHeaderLabels(['ID', 'CLAVE', 'UBICACION', 'NOMBRE'])
        
        # Ajustar columnas
        header = self.Fase_tableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Clave
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Ubicacion
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Nombre
        
        # Cargar datos iniciales
        self.mostrar_fases_en_tabla()

    def mostrar_fases_en_tabla(self):
        """Carga los datos de tablas en la tabla con la cantidad de macrotúneles"""
        try:
            fases = listar_fases()
            self.Fase_tableWidget.setRowCount(len(fases))
            
            for row, fase in enumerate(fases):
                # ID (no editable)
                id_item = QTableWidgetItem(str(fase['id_Fase']))
                id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.Fase_tableWidget.setItem(row, 0, id_item)
                
                # Resto de campos
                self.Fase_tableWidget.setItem(row, 1, QTableWidgetItem(fase['Clave']))
                self.Fase_tableWidget.setItem(row, 2, QTableWidgetItem(fase['Ubicacion'] or ""))
                self.Fase_tableWidget.setItem(row, 3, QTableWidgetItem(fase['Nombre'] or ""))


        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar las tablas:\n{str(e)}")

    ####################################################################################################


    ####################################################################################################
    #                      CONFIGURAR TABLA FASE self.Tablas_tableWidget
    ####################################################################################################
    def configurar_tabla_tablas(self):
        """Configuración inicial de la tabla de tablas"""
        self.Tablas_tableWidget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.Tablas_tableWidget.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.Tablas_tableWidget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Configurar headers
        self.Tablas_tableWidget.setColumnCount(5)
        self.Tablas_tableWidget.setHorizontalHeaderLabels(['ID', 'CLAVE', 'UBICACIÓN','NOMBRE', 'CLAVE_FASE'])
        
        # Ajustar columnas
        header = self.Tablas_tableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Clave
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Ubicación
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Nombre
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Calve Fase Asociada
        
        # Cargar datos iniciales
        self.mostrar_tablas_en_tabla()

    def mostrar_tablas_en_tabla(self):
        """Carga los datos de tablas en la tabla con la cantidad de macrotúneles"""
        try:
            tablas = listar_tabla()
            self.Tablas_tableWidget.setRowCount(len(tablas))
            
            for row, tabla in enumerate(tablas):
                # ID (no editable)
                id_item = QTableWidgetItem(str(tabla['id_Tabla']))
                id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.Tablas_tableWidget.setItem(row, 0, id_item)
                
                # Resto de campos
                self.Tablas_tableWidget.setItem(row, 1, QTableWidgetItem(tabla['Clave']))
                self.Tablas_tableWidget.setItem(row, 2, QTableWidgetItem(tabla['Ubicacion'] or ""))
                self.Tablas_tableWidget.setItem(row, 3, QTableWidgetItem(tabla['Nombre'] or ""))
                self.Tablas_tableWidget.setItem(row, 4, QTableWidgetItem(tabla['Clave_Fase'] or ""))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar las tablas:\n{str(e)}")

    ####################################################################################################
    #                      CONFIGURAR TABLA MACROTUNEL self.Macrotuneles_tableWidget
    ####################################################################################################
    def configurar_tabla_macrotunel(self):
        """Configuración inicial de la tabla de macrotúneles"""
        self.Macrotuneles_tableWidget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.Macrotuneles_tableWidget.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.Macrotuneles_tableWidget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Configurar headers
        self.Macrotuneles_tableWidget.setColumnCount(5)
        self.Macrotuneles_tableWidget.setHorizontalHeaderLabels(['ID', 'CLAVE', 'UBICACIÓN', 'NOMBRE', 'CLAVE_TABLA'])
        
        # Ajustar columnas
        header = self.Macrotuneles_tableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)           # Clave
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)           # Ubicación
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)           # Nombre
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Clave Tabla Asociada
        
        # Cargar datos iniciales
        self.mostrar_macrotuneles_en_tabla()

    def mostrar_macrotuneles_en_tabla(self):
        """Carga los datos de los macrotuneles en la tabla con su respectiva tabla"""
        try:
            macrotuneles = listar_macrotunel()
            self.Macrotuneles_tableWidget.setRowCount(len(macrotuneles))
            
            for row, macrotunel in enumerate(macrotuneles):
                # ID (no editable)
                id_item = QTableWidgetItem(str(macrotunel['id_Macrotunel']))
                id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.Macrotuneles_tableWidget.setItem(row, 0, id_item)
                
                # Resto de campos
                self.Macrotuneles_tableWidget.setItem(row, 1, QTableWidgetItem(macrotunel['Clave']))
                self.Macrotuneles_tableWidget.setItem(row, 2, QTableWidgetItem(macrotunel['Ubicacion'] or ""))
                self.Macrotuneles_tableWidget.setItem(row, 3, QTableWidgetItem(macrotunel['Nombre'] or ""))
                self.Macrotuneles_tableWidget.setItem(row, 4, QTableWidgetItem(macrotunel['Clave_Tabla'] or ""))


        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los macrotuneles:\n{str(e)}")

    ####################################################################################################
    #                      CONFIGURAR TABLA LINEA self.Linea_tableWidget
    ####################################################################################################
    def configurar_tabla_linea(self):
        """Configuración inicial de la tabla de lineas"""
        self.Linea_tableWidget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.Linea_tableWidget.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.Linea_tableWidget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Configurar headers
        self.Linea_tableWidget.setColumnCount(6)
        self.Linea_tableWidget.setHorizontalHeaderLabels(['ID', 'CLAVE', 'NOMBRE', 'UBICACIÓN', 'NUM. MACETAS', 'CLAVE_MACROTUNEL'])
        
        # Ajustar columnas
        header = self.Linea_tableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)           # Clave
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)           # Nombre
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)           # Ubicacion
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)           # Num. Macetas
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Clave Macrotunel Asociado
        
        # Cargar datos iniciales
        self.mostrar_lineas_en_tabla()

    def mostrar_lineas_en_tabla(self):
        """Carga los datos de las lineas en la tabla con su respectivo macrotunel"""
        try:
            lineas = listar_linea()
            self.Linea_tableWidget.setRowCount(len(lineas))
            
            for row, linea in enumerate(lineas):
                # ID (no editable)
                id_item = QTableWidgetItem(str(linea['id_Linea']))
                id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.Linea_tableWidget.setItem(row, 0, id_item)
                
                # Resto de campos
                self.Linea_tableWidget.setItem(row, 1, QTableWidgetItem(linea['Clave']))
                self.Linea_tableWidget.setItem(row, 2, QTableWidgetItem(linea['Nombre'] or ""))
                self.Linea_tableWidget.setItem(row, 3, QTableWidgetItem(linea['Ubicacion'] or ""))
                self.Linea_tableWidget.setItem(row, 4, QTableWidgetItem(str(linea['Num_Macetas']) if linea['Num_Macetas'] is not None else ""))
                self.Linea_tableWidget.setItem(row, 5, QTableWidgetItem(linea['Clave_Macrotunel'] or ""))


        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar las lineas:\n{str(e)}")

    ####################################################################################################
    #                      CONFIGURAR TABLA CHECKIN self.ChecksPorDia_tableWidget
    ####################################################################################################
    def configurar_tabla_checkin(self):
        """Configuración inicial de la tabla de tablas"""
        self.ChecksPorDia_tableWidget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.ChecksPorDia_tableWidget.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.ChecksPorDia_tableWidget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Configurar headers
        self.ChecksPorDia_tableWidget.setColumnCount(4)
        self.ChecksPorDia_tableWidget.setHorizontalHeaderLabels(['ID', 'FECHA', 'RECOLECTOR', 'MODALIDAD'])
        
        # Ajustar columnas
        header = self.ChecksPorDia_tableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Fecha_Y_HOra
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # id_Recolector (Nombre)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # id_Modalidad (Clave)
        
        # Cargar datos iniciales
        self.mostrar_checks_en_tabla()

    def mostrar_checks_en_tabla(self):
        try:
            checks = listar_checks()
            self.ChecksPorDia_tableWidget.setRowCount(len(checks))

            for row, check in enumerate(checks):
                id_item = QTableWidgetItem(str(check['id_Check']))
                id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.ChecksPorDia_tableWidget.setItem(row, 0, id_item)

                self.ChecksPorDia_tableWidget.setItem(row, 1, QTableWidgetItem(check['Fecha_Y_Hora']))
                self.ChecksPorDia_tableWidget.setItem(row, 2, QTableWidgetItem(check['Recolector']))
                self.ChecksPorDia_tableWidget.setItem(row, 3, QTableWidgetItem(check['Modalidad']))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los checks:\n{str(e)}")

    ####################################################################################################
    #                      CONFIGURAR TABLA VISTA self.Vista_tableWidget
    ####################################################################################################
    # def configurar_tabla_vista(self):
    #     """Configuración inicial de la tabla de macrotúneles"""
    #     self.Vista_tableWidget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    #     self.Vista_tableWidget.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
    #     self.Vista_tableWidget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
    #     # Configurar headers
    #     self.Vista_tableWidget.setColumnCount(12)
    #     self.Vista_tableWidget.setHorizontalHeaderLabels(['ID COSECHA', 'CLAVE COSECHA', 'CALIFICACION', 'PESO (Kg)', 'FECHA TRANSACCION', 'ID RECOLECTOR', 'NOMBRE RECOLECTOR', 'MACROTUNEL', 'TABLA', 'ID VUELTA', 'CUADRILLERO', 'LOCALIDAD'])
        
    #     # Ajustar columnas
    #     header = self.Vista_tableWidget.horizontalHeader()
    #     header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # ID COSECHA
    #     header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # CLAVE
    #     header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # CALIFICACION
    #     header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # PESO
    #     header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) # FECHA TRANSACCION
    #     header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents) # ID RECOLECTOR
    #     header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents) # NOMBRE COMPLETO
    #     header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents) # MACROTUNEL
    #     header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents) # TABLA
    #     header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents) # ID ENTREGA
    #     header.setSectionResizeMode(10, QHeaderView.ResizeMode.ResizeToContents) # CUADRILLERO
    #     header.setSectionResizeMode(11, QHeaderView.ResizeMode.ResizeToContents) # LOCALIDAD
        
    #     # Cargar datos iniciales
    #     self.mostrar_vista_en_tabla()

    # def mostrar_vista_en_tabla(self, fecha_inicio=None, fecha_fin=None, nombre_recolector="", tabla="", macrotunel=""):
    #     """Actualiza la tabla con todos los filtros aplicados"""
    #     sabana_vistas = SabanaVistas()
    #     datos, error = sabana_vistas.obtener_datos_vista(
    #         fecha_inicio=fecha_inicio,
    #         fecha_fin=fecha_fin,
    #         nombre_recolector=nombre_recolector,
    #         tabla=tabla,
    #         macrotunel=macrotunel
    #     )
        
    #     if error:
    #         print(f"Error: {error}")
    #         return
        
    #     self.Vista_tableWidget.setRowCount(0)
        
    #     if not datos:
    #         return  # No mostrar mensaje si no hay datos
        
    #     for fila in datos:
    #         row_position = self.Vista_tableWidget.rowCount()
    #         self.Vista_tableWidget.insertRow(row_position)
            
    #         self.Vista_tableWidget.setItem(row_position, 0, QTableWidgetItem(str(fila['ID_COSECHA'])))
    #         self.Vista_tableWidget.setItem(row_position, 1, QTableWidgetItem(fila['CLAVE']))
    #         self.Vista_tableWidget.setItem(row_position, 2, QTableWidgetItem(fila['CALIFICACION']))
    #         self.Vista_tableWidget.setItem(row_position, 3, QTableWidgetItem(str(fila['PESO'])))
            
    #         fecha = fila['FECHA_TRANSACCION'].strftime("%Y-%m-%d %H:%M:%S") if fila['FECHA_TRANSACCION'] else ""
    #         self.Vista_tableWidget.setItem(row_position, 4, QTableWidgetItem(fecha))
            
    #         self.Vista_tableWidget.setItem(row_position, 5, QTableWidgetItem(str(fila['ID_RECOLECTOR'])))
    #         self.Vista_tableWidget.setItem(row_position, 6, QTableWidgetItem(fila['NOMBRE_RECOLECTOR']))
    #         self.Vista_tableWidget.setItem(row_position, 7, QTableWidgetItem(fila['MACROTUNEL']))
    #         self.Vista_tableWidget.setItem(row_position, 8, QTableWidgetItem(fila['TABLA']))
    #         self.Vista_tableWidget.setItem(row_position, 9, QTableWidgetItem(str(fila['ID_VUELTA']) if fila['ID_VUELTA'] else ""))
    #         self.Vista_tableWidget.setItem(row_position, 10, QTableWidgetItem(fila['CUADRILLERO']))
    #         self.Vista_tableWidget.setItem(row_position, 11, QTableWidgetItem(fila['LOCALIDAD']))
    def configurar_tabla_vista(self):
        """Configuración inicial de la tabla de vista/sábana"""
        self.Vista_tableWidget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.Vista_tableWidget.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.Vista_tableWidget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        columnas = [
            'ID COSECHA', 'CLAVE COSECHA', 'ID VUELTA', 'ID RECOLECTOR',
            'NOMBRE RECOLECTOR', 'PESO (Kg)', 'CALIFICACION', 'MODALIDAD',
            'FASE', 'TABLA', 'MACROTUNEL', 'LINEA',
            'CODIGO',          
            'CUADRILLERO',
            'LOCALIDAD', 'FECHA TRANSACCION'
        ]
        self.Vista_tableWidget.setColumnCount(len(columnas))
        self.Vista_tableWidget.setHorizontalHeaderLabels(columnas)

        header = self.Vista_tableWidget.horizontalHeader()
        for i in range(len(columnas)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        self.mostrar_vista_en_tabla()


    def mostrar_vista_en_tabla(self, fecha_inicio=None, fecha_fin=None,
                                nombre_recolector="", fase="", tabla="",
                                macrotunel="", linea=""):
        """Actualiza la tabla con todos los filtros aplicados"""
        sabana_vistas = SabanaVistas()
        datos, error = sabana_vistas.obtener_datos_vista(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            nombre_recolector=nombre_recolector,
            fase=fase,
            tabla=tabla,
            macrotunel=macrotunel,
            linea=linea
        )

        if error:
            print(f"Error: {error}")
            return

        self.Vista_tableWidget.setRowCount(0)

        if not datos:
            return

        for fila in datos:
            row_position = self.Vista_tableWidget.rowCount()
            self.Vista_tableWidget.insertRow(row_position)

            fecha = fila['FECHA_TRANSACCION'].strftime("%Y-%m-%d %H:%M:%S") if fila['FECHA_TRANSACCION'] else ""

            self.Vista_tableWidget.setItem(row_position, 0,  QTableWidgetItem(str(fila['ID_COSECHA'])))
            self.Vista_tableWidget.setItem(row_position, 1,  QTableWidgetItem(fila['CLAVE']))
            self.Vista_tableWidget.setItem(row_position, 2,  QTableWidgetItem(str(fila['ID_VUELTA']) if fila['ID_VUELTA'] else ""))
            self.Vista_tableWidget.setItem(row_position, 3,  QTableWidgetItem(str(fila['ID_RECOLECTOR'])))
            self.Vista_tableWidget.setItem(row_position, 4,  QTableWidgetItem(fila['NOMBRE_RECOLECTOR']))
            self.Vista_tableWidget.setItem(row_position, 5,  QTableWidgetItem(str(fila['PESO'])))
            self.Vista_tableWidget.setItem(row_position, 6,  QTableWidgetItem(fila['CALIFICACION']))
            self.Vista_tableWidget.setItem(row_position, 7,  QTableWidgetItem(fila['MODALIDAD']))
            self.Vista_tableWidget.setItem(row_position, 8,  QTableWidgetItem(fila['FASE']))
            self.Vista_tableWidget.setItem(row_position, 9,  QTableWidgetItem(fila['TABLA']))
            self.Vista_tableWidget.setItem(row_position, 10, QTableWidgetItem(fila['MACROTUNEL']))
            self.Vista_tableWidget.setItem(row_position, 11, QTableWidgetItem(fila['LINEA']))
            self.Vista_tableWidget.setItem(row_position, 12, QTableWidgetItem(fila['CLAVE_TRAZABILIDAD'] or ""))  # ← NUEVO
            self.Vista_tableWidget.setItem(row_position, 13, QTableWidgetItem(fila['CUADRILLERO']))
            self.Vista_tableWidget.setItem(row_position, 14, QTableWidgetItem(fila['LOCALIDAD']))
            self.Vista_tableWidget.setItem(row_position, 15, QTableWidgetItem(fecha))

    # def actualizar_vista(self):
    #     """Actualiza la tabla con los filtros aplicados"""

    #     # Obtener valores de los widgets
    #     fecha_inicio = self.Inicio_calendarWidget.selectedDate().toString("yyyy-MM-dd")
    #     fecha_fin = self.Fin_calendarWidget.selectedDate().toString("yyyy-MM-dd")
        
    #     # Puedes pasar None si no está habilitado
    #     if self.Inicio_calendarWidget.isEnabled() and self.Fin_calendarWidget.isEnabled():
    #         nombre_recolector = self.NombreRecolectorVista_lineEdit.text().strip()
    #         self.mostrar_vista_en_tabla(fecha_inicio, fecha_fin, nombre_recolector, tabla=None, macrotunel=None)
                
    def actualizar_vista(self):
        fecha_inicio = self.Inicio_calendarWidget.selectedDate().toString("yyyy-MM-dd")
        fecha_fin = self.Fin_calendarWidget.selectedDate().toString("yyyy-MM-dd")
        if self.Inicio_calendarWidget.isEnabled() and self.Fin_calendarWidget.isEnabled():
            self.mostrar_vista_en_tabla(
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                nombre_recolector=self.NombreRecolectorVista_lineEdit.text().strip(),
                fase=self.FaseVista_comboBox.currentText(),
                tabla=self.TablaVista_comboBox.currentText(),
                macrotunel=self.MacrotunelVista_comboBox.currentText(),
                linea=self.LineaVista_comboBox.currentText()
            )

    # def ActualizarVistaHoy(self, checked=False):
    #     if checked:
    #         # Botón activado: fijar fecha de hoy y limpiar filtros
    #         hoy = QDate.currentDate()
    #         self.Inicio_calendarWidget.setSelectedDate(hoy)
    #         self.Fin_calendarWidget.setSelectedDate(hoy)
    #         self.filtrar_por_fecha = True
    #         self.limpiar_filtros_vista()
    #     else:
    #         # Botón desactivado: recargar filtros y mostrar todo
    #         self.filtrar_por_fecha = False
    #         self.cargar_fases_vista_comboBox()
    #         self.cargar_tablas_vista_comboBox()
    #         self.cargar_macrotuneles_vista_comboBox()
    #         self.cargar_linea_vista_comboBox()
    #         self.actualizar_vista()

    def setup_protected_combobox(self):
        """Conecta la protección al combobox después de inicializar la UI"""
        # Guarda el método original y lo reemplaza
        self.ModalidadConfiguracion_comboBox.showPopup = self._protected_showPopup

    def _protected_showPopup(self):
        """Intercepta el desplegado del combobox y pide contraseña primero"""
        key, ok = QInputDialog.getText(
            self,
            "Acceso Restringido",
            "Ingrese la clave de acceso:",
            QLineEdit.EchoMode.Password
        )

        if not ok:
            return  # Canceló el usuario

        key = key.strip()

        if key == "":
            QMessageBox.warning(self, "Error", "No ingresaste ninguna clave")
            return

        acceso = KeysAcceso()

        if acceso.key_acceso_modulo(key):
            # Llama al showPopup original para desplegar el combobox
            QComboBox.showPopup(self.ModalidadConfiguracion_comboBox)
        else:
            QMessageBox.warning(self, "Acceso Denegado", "Clave incorrecta")

    def VistaHoy(self):
        hoy = QDate.currentDate()
        self.Inicio_calendarWidget.setSelectedDate(hoy)
        self.Fin_calendarWidget.setSelectedDate(hoy)
        self.filtrar_por_fecha = True
        self.limpiar_filtros_vista()
        self.ActualizarVistaHoy_Btn.setIcon(QIcon(":/images/iconos/botones/calendar.png"))
        self.ActualizarVistaHoy_Btn.setText("    HOY")

    def VistaFiltro(self):
        self.filtrar_por_fecha = False
        self.cargar_fases_vista_comboBox()
        self.cargar_tablas_vista_comboBox()
        self.cargar_macrotuneles_vista_comboBox()
        self.cargar_linea_vista_comboBox()
        self.actualizar_vista()
        self.ActualizarVistaHoy_Btn.setIcon(QIcon(":/images/iconos/botones/filtro.svg"))
        self.ActualizarVistaHoy_Btn.setText("  FILTRO")

    def ActualizarVistaHoy(self, checked=False):
        if checked:
            self.VistaFiltro()
        else:
            self.VistaHoy()

    def update_reloj(self):
        current_datetime = QDateTime.currentDateTime()
        self.dateLabel.setText("Fecha: " + current_datetime.date().toString("dd/MM/yyyy"))
        self.timeLabel.setText(current_datetime.time().toString("hh:mm:ss"))

    def ShowColectorMenu(self):
        self.stackedWidget_Principal.setCurrentIndex(1)
        self.stackedWidget_Colector.setCurrentIndex(2)
        self.mostrar_recolectores_en_tabla()

    # def ShowCheckinMenu(self):
    #     key, ok = QInputDialog.getText(
    #         self,
    #         "Acceso Restringido",
    #         "Ingrese la clave de acceso:",
    #         QLineEdit.EchoMode.Password
    #     )

    #     if not ok:
    #         return  # Canceló el usuario

    #     key = key.strip()

    #     if key == "":
    #         QMessageBox.warning(self, "Error", "No ingresaste ninguna clave")
    #         return

    #     acceso = KeysAcceso()

    #     if acceso.key_acceso_modulo(key):
    #         self.stackedWidget_Principal.setCurrentIndex(11)
    #         self.TomarFotoCheck_stackedWidget.setCurrentIndex(0)
    #         self.checador_worker.start(0)
    #     else:
    #         QMessageBox.warning(self, "Acceso Denegado", "Clave incorrecta")

    def ShowCheckinMenu(self):
        self.deshabilitar_modulos()
        # Siempre verificar cámaras primero, y manejar todo en el callback
        self.camera_checker = CameraConnectionManager(self)
        self.camera_checker.start_check(self._on_cameras_checked_for_checkin)

    def _on_cameras_checked_for_checkin(self, cameras_ok, detected_ports):
        # Actualizar estado visual y variable
        self.on_cameras_checked(cameras_ok, detected_ports)

        if not cameras_ok:
            self.boton_camara_apagado()
            self.habilitar_modulos()
            return

        key, ok = QInputDialog.getText(
            self,
            "Modulo de Listados",
            "Ingrese la clave de acceso:",
            QLineEdit.EchoMode.Password
        )

        if not ok:
            self.boton_camara_apagado()
            self.habilitar_modulos()
            return

        key = key.strip()

        if key == "":
            QMessageBox.warning(self, "Error", "No ingresaste ninguna clave")
            self.boton_camara_apagado()
            self.habilitar_modulos()
            return

        acceso = KeysAcceso()

        if acceso.key_acceso_modulo(key):
            self.stackedWidget_Principal.setCurrentIndex(11)
            self.TomarFotoCheck_stackedWidget.setCurrentIndex(0)
            self.checador_worker.start(0)
            self.habilitar_modulos()
        else:
            QMessageBox.warning(self, "Acceso Denegado", "Clave incorrecta")
            self.boton_camara_apagado()
            self.habilitar_modulos()

    def TomarFotoCheck(self):
        # self.TomarFotoCheck_stackedWidget.setCurrentIndex(1)
        # if hasattr(self, 'current_face_data_checador') and self.current_face_data_checador:
        #     name, emp_info, confidence = self.current_face_data_checador
        #     if name == "DESCONOCIDO":
        #         QMessageBox.warning(self, "Advertencia", "Rostro no reconocido.")
        #         return
        self.TomarFotoCheck_stackedWidget.setCurrentIndex(1)
        if self.checador_worker.face_count == 0:
            QMessageBox.warning(
                self,
                "Advertencia",
                "No se detectó ningún rostro"
            )
            self.TomarFotoCheck_stackedWidget.setCurrentIndex(0)
            return

        if self.checador_worker.face_count > 1:
            QMessageBox.warning(
                self,
                "Advertencia",
                "Debe haber solamente un rostro frente a la cámara"
            )
            self.TomarFotoCheck_stackedWidget.setCurrentIndex(0)
            return

        if not self.current_face_data_checador:
            QMessageBox.warning(
                self,
                "Advertencia",
                "No se ha detectado ningún rostro"
            )
            self.TomarFotoCheck_stackedWidget.setCurrentIndex(0)
            return

        detection, face_count = self.current_face_data_checador

        if detection is None:
            QMessageBox.warning(
                self,
                "Advertencia",
                "No se detectó ningún rostro válido"
            )
            self.TomarFotoCheck_stackedWidget.setCurrentIndex(0)
            return

        name, emp_info, confidence = detection
        if name == "DESCONOCIDO":
            QMessageBox.warning(
                self,
                "Advertencia",
                "Rostro no reconocido"
            )
            self.TomarFotoCheck_stackedWidget.setCurrentIndex(0)
            return
        
        current_datetime = QDateTime.currentDateTime()
        modalidad_controlador = ModalidadControlador()
        # Ahora recibe (clave_string, id_modalidad)
        modalidad_clave, _ = modalidad_controlador.obtener_modalidad_por_dia()

        self.NombreRecolectorCheck_Lbl.setText(str(name))
        self.FechaRecolectorCheck_Lbl.setText(current_datetime.date().toString("dd/MM/yyyy"))
        self.ModalidadRecolectorCheck_Lbl.setText(modalidad_clave or "")
        self.checador_worker.set_freeze_frame(True)
        # else:
        #     QMessageBox.warning(self, "Advertencia", "No se ha detectado ningún recolector reconocido")


    def TomarOtraFotoCheck(self):
        self.TomarFotoCheck_stackedWidget.setCurrentIndex(0)
        self.ReiniciarFaceRecognitionCheck()

    def ConfirmarColectorCheck(self):
        try:
            """Registra el check-in del recolector detectado en REGISTRO_CHECK."""
            if not self.current_face_data_checador:
                QMessageBox.warning(self, "Advertencia", "No hay recolector detectado para confirmar.")
                return

            detection, face_count = self.current_face_data_checador
            name, emp_info, confidence = detection

            # 1. Buscar id_Recolector por nombre en la BD
            session = get_db()
            try:
                recolector = session.query(Recolector).filter(
                    Recolector.Nombre_Completo == name
                ).first()
            finally:
                session.close()

            if not recolector:
                QMessageBox.critical(self, "Error", f"No se encontró el recolector '{name}' en la base de datos.")
                return

            id_recolector = recolector.id_Recolector
            print("id_recolector", id_recolector)
            print("name", name)
            

            # 2. Obtener id de la modalidad activa
            modalidad_controlador = ModalidadControlador()
            _, id_modalidad = modalidad_controlador.obtener_modalidad_por_dia()
            print("id_modalidad", id_modalidad)

            if not id_modalidad:
                QMessageBox.critical(self, "Error", "No se pudo obtener la modalidad activa.")
                return

            # 3. Registrar el check-in
            from controlador.checador import crear_check
            exito = crear_check(id_recolector, id_modalidad)

            if exito:
                QMessageBox.information(
                    self, "Listados",
                    f"{name} listado correctamente."
                )
                self.ReiniciarFaceRecognitionCheck()
                self.mostrar_checks_en_tabla()
                self.TomarFotoCheck_stackedWidget.setCurrentIndex(0)
            else:
                QMessageBox.critical(self, "Error", "No se pudo registrar el check-in. Intente de nuevo.")
        except Exception as e:
            print("error en confirmar check: ", e)

    def Back_CheckinMenu(self):
        """Apagar camara al cerrar la ventana"""
        self.checador_worker.stop()
        self.checador_thread.quit()
        self.checador_thread.wait()
        self.boton_camara_apagado()
        self.stackedWidget_Principal.setCurrentIndex(0)


    def ShowCrearColector(self):
        self.stackedWidget_Colector.setCurrentIndex(0)
        self.stackedWidget_TomarFoto.setCurrentIndex(0)
        self.cargar_cuadrillas()
        self.TomarFotoColector_Btn.setEnabled(False)
        self.BotonVerdeOscuro(self.TomarFotoColector_Btn) 
        self.CamaraConfig_Rostro()

    #####################################################

    # def CamaraConfig_RostroActualizado(self):
    #     # Si la cámara ya está abierta, no hacer nada
    #     if hasattr(self, 'cap_actualizar') and self.cap_actualizar is not None and self.cap_actualizar.isOpened():
    #         return
        
    #     # Inicializar cámara solo si no está activa
    #     self.cap_actualizar = cv2.VideoCapture(self.puerto_facial, cv2.CAP_DSHOW)
    #     self.cap_actualizar.set(cv2.CAP_PROP_FRAME_WIDTH, 848)
    #     self.cap_actualizar.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
    #     if cv2.cuda.getCudaEnabledDeviceCount() > 0:
    #         self.cap_actualizar.set(cv2.CAP_PROP_BACKEND, cv2.CAP_CUDA)

    #     """
    #     # Variable para controlar el modo espejo
    #     """
    #     self.mirror_mode = True  # True para activar modo espejo
    #     self.timer_registroActualizar.start(44)
        
    # def update_frame_rostro_actualizado(self):
    #     if self.image_captured_actualizar:
    #         return  # No actualizamos si ya se capturó la imagen
    
    #     ret, frame = self.cap_actualizar.read()
    #     if ret:
    #         """
    #         # Aplicar efecto espejo si está activado
    #         """
    #         if hasattr(self, 'mirror_mode') and self.mirror_mode:
    #             frame = cv2.flip(frame, 1)  # 1 para flip horizontal (modo espejo)

    #         # Convertir el frame de BGR (OpenCV) a RGB (Qt)
    #         frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    #         # Recuadro para ubicar la cara
    #         # cv2.rectangle(frame, (324, 90), (524, 390), (255, 0, 0), 2)
    #         cv2.rectangle(frame, (309, 90), (539, 390), (255, 0, 0), 2)
    #         cv2.circle(frame, (424,200), 5, (0, 255, 0), -1)
            
    #         # Convertir a QImage
    #         h, w, ch = frame.shape
    #         bytes_per_line = ch * w
    #         q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
    #         pixmap = QPixmap.fromImage(q_img)
            
    #         # Configurar el QLabel para mantener la relación de aspecto y centrar la imagen
    #         self.FotoActualizada_Lbl.setPixmap(pixmap)
    #         self.FotoActualizada_Lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Centrar la imagen
    #         self.FotoActualizada_Lbl.setScaledContents(False)  # Desactivar escalado automático

    def CamaraConfig_RostroActualizado(self):
        if hasattr(self, 'cap_actualizar') and self.cap_actualizar is not None and self.cap_actualizar.isOpened():
            return
        
        self.cap_actualizar = cv2.VideoCapture(self.puerto_facial, cv2.CAP_DSHOW)
        self.cap_actualizar.set(cv2.CAP_PROP_FRAME_WIDTH, 848)
        self.cap_actualizar.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        if cv2.cuda.getCudaEnabledDeviceCount() > 0:
            self.cap_actualizar.set(cv2.CAP_PROP_BACKEND, cv2.CAP_CUDA)

        self.mirror_mode = True
        self._cap_actualizar_reconnect_attempted = False
        self.timer_registroActualizar.start(44)


    def update_frame_rostro_actualizado(self):
        if self.image_captured_actualizar:
            return

        ret, frame = self.cap_actualizar.read()

        if not ret or self._frame_is_black(frame):
            self._handle_cap_actualizar_disconnected()
            return

        self._cap_actualizar_reconnect_attempted = False
        self._set_testigo_camaras(True)  # 🟢

        if hasattr(self, 'mirror_mode') and self.mirror_mode:
            frame = cv2.flip(frame, 1)

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        cv2.rectangle(frame, (self.RECT_X1, self.RECT_Y1), (self.RECT_X2, self.RECT_Y2), (0, 0, 255), 2)
        cv2.circle(frame, (424, 200), 5, (0, 255, 0), -1)

        h, w, ch = frame.shape
        bytes_per_line = ch * w
        q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)

        self.FotoActualizada_Lbl.setPixmap(pixmap)
        self.FotoActualizada_Lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.FotoActualizada_Lbl.setScaledContents(False)


    def _handle_cap_actualizar_disconnected(self):
        if getattr(self, '_cap_actualizar_reconnect_attempted', False):
            return

        self._cap_actualizar_reconnect_attempted = True
        self._set_testigo_camaras(False)  # 🔴

        self.timer_registroActualizar.stop()
        if self.cap_actualizar is not None:
            self.cap_actualizar.release()
            self.cap_actualizar = None

        print("Cámara de actualización desconectada, reintentando...")
        QTimer.singleShot(2000, self._try_reconnect_cap_actualizar)


    def _try_reconnect_cap_actualizar(self):
        try:
            os.environ["OPENCV_LOG_LEVEL"] = "SILENT"

            cap_test = cv2.VideoCapture(self.puerto_facial, cv2.CAP_DSHOW)
            if cap_test.isOpened():
                ret, frame = cap_test.read()

                if ret and not self._frame_is_black(frame):
                    cap_test.release()
                    os.environ["OPENCV_LOG_LEVEL"] = "ERROR"

                    self.cap_actualizar = cv2.VideoCapture(self.puerto_facial, cv2.CAP_DSHOW)
                    self.cap_actualizar.set(cv2.CAP_PROP_FRAME_WIDTH, 848)
                    self.cap_actualizar.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    self._cap_actualizar_reconnect_attempted = False
                    self.timer_registroActualizar.start(44)
                    print("Cámara de actualización reconectada exitosamente")
                    return

            cap_test.release()

        except Exception as e:
            print(f"Error al reconectar cámara de actualización: {e}")

        finally:
            os.environ["OPENCV_LOG_LEVEL"] = "ERROR"

        print("Cámara aún no disponible, reintentando...")
        QTimer.singleShot(2000, self._try_reconnect_cap_actualizar)


    #####################################################
    #
    #####################################################
    # def CamaraConfig_Rostro(self):
    #     # Si la cámara ya está abierta, no hacer nada
    #     if hasattr(self, 'cap') and self.cap is not None and self.cap.isOpened():
    #         return
        
    #     # Inicializar cámara solo si no está activa
    #     self.cap = cv2.VideoCapture(self.puerto_facial, cv2.CAP_DSHOW)
    #     self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 848)
    #     self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
    #     if cv2.cuda.getCudaEnabledDeviceCount() > 0:
    #         self.cap.set(cv2.CAP_PROP_BACKEND, cv2.CAP_CUDA)

    #     """
    #     # Variable para controlar el modo espejo
    #     """
    #     self.mirror_mode = True  # True para activar modo espejo
    #     self.timer_registroFacial.start(44)
        
    # def update_frame(self):
    #     if self.image_captured:
    #         return  # No actualizamos si ya se capturó la imagen
    
    #     ret, frame = self.cap.read()
    #     if ret:
    #         """
    #         # Aplicar efecto espejo si está activado
    #         """

    #         if hasattr(self, 'mirror_mode') and self.mirror_mode:
    #             frame = cv2.flip(frame, 1)  # 1 para flip horizontal (modo espejo)

    #         # Convertir el frame de BGR (OpenCV) a RGB (Qt)
    #         frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    #         # Recuadro para ubicar la cara
    #         # cv2.rectangle(frame, (324, 90), (524, 390), (255, 0, 0), 2)
    #         cv2.rectangle(frame, (309, 90), (539, 390), (255, 0, 0), 2)
    #         cv2.circle(frame, (424,200), 5, (0, 255, 0), -1)
            
    #         # Convertir a QImage
    #         h, w, ch = frame.shape
    #         bytes_per_line = ch * w
    #         q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
    #         pixmap = QPixmap.fromImage(q_img)
            
    #         # Configurar el QLabel para mantener la relación de aspecto y centrar la imagen
    #         self.Foto_Lbl.setPixmap(pixmap)
    #         self.Foto_Lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Centrar la imagen
    #         self.Foto_Lbl.setScaledContents(False)  # Desactivar escalado automático
    def CamaraConfig_Rostro(self):
        if hasattr(self, 'cap') and self.cap is not None and self.cap.isOpened():
            return
        
        self.cap = cv2.VideoCapture(self.puerto_facial, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 848)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        if cv2.cuda.getCudaEnabledDeviceCount() > 0:
            self.cap.set(cv2.CAP_PROP_BACKEND, cv2.CAP_CUDA)

        self.mirror_mode = True
        self._cap_reconnect_attempted = False  # Resetear flag al iniciar
        self.timer_registroFacial.start(44)


    def update_frame(self):
        if self.image_captured:
            return

        ret, frame = self.cap.read()

        # Cámara desconectada: sin frame o frame negro
        if not ret or self._frame_is_black(frame):
            self._handle_cap_disconnected()
            return

        # Frame válido, resetear flag de reconexión
        self._cap_reconnect_attempted = False
        self._set_testigo_camaras(True)  # 🟢

        if hasattr(self, 'mirror_mode') and self.mirror_mode:
            frame = cv2.flip(frame, 1)

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        cv2.rectangle(frame, (self.RECT_X1, self.RECT_Y1), (self.RECT_X2, self.RECT_Y2), (0, 0, 255), 2)
        cv2.circle(frame, (424, 200), 5, (0, 255, 0), -1)

        h, w, ch = frame.shape
        bytes_per_line = ch * w
        q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)

        self.Foto_Lbl.setPixmap(pixmap)
        self.Foto_Lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.Foto_Lbl.setScaledContents(False)


    def _handle_cap_disconnected(self):
        """Maneja desconexión de self.cap (cámara de captura de foto)"""
        if getattr(self, '_cap_reconnect_attempted', False):
            return

        self._cap_reconnect_attempted = True
        self._set_testigo_camaras(False)  # 🔴

        # Detener timer y liberar cámara
        self.timer_registroFacial.stop()
        if self.cap is not None:
            self.cap.release()
            self.cap = None

        print("Cámara de captura desconectada, reintentando...")
        QTimer.singleShot(2000, self._try_reconnect_cap)


    def _try_reconnect_cap(self):
        """Intenta reconectar self.cap"""
        try:
            cap_test = cv2.VideoCapture(self.puerto_facial, cv2.CAP_DSHOW)
            if cap_test.isOpened():
                ret, frame = cap_test.read()

                if ret and not self._frame_is_black(frame):
                    cap_test.release()

                    # Reconectar con la configuración original
                    self.cap = cv2.VideoCapture(self.puerto_facial, cv2.CAP_DSHOW)
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 848)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    self._cap_reconnect_attempted = False
                    self.timer_registroFacial.start(44)
                    print("Cámara de captura reconectada exitosamente")
                    return

            cap_test.release()
        except Exception as e:
            print(f"Error al reconectar cámara de captura: {e}")

        print("Cámara aún no disponible, reintentando...")
        QTimer.singleShot(2000, self._try_reconnect_cap)

    def CamaraConfig_Cosecha(self):
        # Inicializar cámara solo si no está activa
        self.cap_cosecha = cv2.VideoCapture(self.puerto_cosecha, cv2.CAP_DSHOW)
        self.cap_cosecha.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap_cosecha.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        if cv2.cuda.getCudaEnabledDeviceCount() > 0:
            self.cap_cosecha.set(cv2.CAP_PROP_BACKEND, cv2.CAP_CUDA)

        self.timer_registroCosecha.start(30)

    def update_frame_cosecha(self):
        if self.image_captured_cosecha:
            return  # No actualizamos si ya se capturó la imagen
    
        ret, frame_cosecha = self.cap_cosecha.read()
        if ret:
            # Convertir el frame de BGR (OpenCV) a RGB (Qt)
            frame_cosecha = cv2.cvtColor(frame_cosecha, cv2.COLOR_BGR2RGB)
            
            # Convertir a QImage
            h, w, ch = frame_cosecha.shape
            bytes_per_line = ch * w
            q_img = QImage(frame_cosecha, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img)
            
            # Configurar el QLabel para mantener la relación de aspecto y centrar la imagen
            self.FotoCosechaCalificada_Lbl.setPixmap(pixmap)
            self.FotoCosechaCalificada_Lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Centrar la imagen
            self.FotoCosechaCalificada_Lbl.setScaledContents(True)  # Desactivar escalado automático


    def apagar_camara_registrar(self):
        # Verificar y liberar la cámara solo si está abierta
        if hasattr(self, 'cap') and self.cap is not None:
            if self.cap.isOpened():
                self.cap.release()
            self.cap = None  # Eliminar referencia

        # Detener el temporizador si está activo
        if hasattr(self, 'timer_registroFacial') and self.timer_registroFacial.isActive():
            self.timer_registroFacial.stop()

    def RegistrarBack(self):
        self.apagar_camara_registrar()
        self.limpiar_foto()
        self.boton_camara_apagado()
        # Cambiar de página
        self.stackedWidget_Colector.setCurrentIndex(2)

    #Habilita boton para tomar foto de colector
    def ConfirmarDatosColector(self):
        self.TomarFotoColector_Btn.setEnabled(True)
        self.BotonVerdeClaro(self.TomarFotoColector_Btn)

    def ConfirmarRegistroColector(self):
        """Guarda todos los datos del recolector en la base de datos"""
        try:
            # Obtener datos del formulario
            nombre = self.NombreCompleto_lineEdit.text().strip()
            localidad = self.Comunidad_lineEdit.text().strip()
            telefono = self.Telefono_lineEdit.text().strip()
            acceso = True
            id_cuadrilla = self.Cuadrillero_comboBox.currentData()
            
            # Validación mejorada con mensajes específicos
            if not nombre:
                QMessageBox.warning(self, "Error", "El nombre es obligatorio")
                return
            if not localidad:
                QMessageBox.warning(self, "Error", "La localidad es obligatoria")
                return
            if not telefono:
                QMessageBox.warning(self, "Error", "El teléfono es obligatorio")
                return
            if id_cuadrilla is None:
                QMessageBox.warning(self, "Error", "Debe seleccionar una cuadrilla")
                return
            if self.captured_image is None or self.face_encoding is None:
                QMessageBox.warning(self, "Error", "Debe tomar una foto primero")
                return
                
            # Guardar en la base de datos
            if crear_recolector(nombre, self.captured_image, self.face_encoding, 
                            localidad, telefono, acceso, id_cuadrilla):
                #QMessageBox.information(self, "Éxito", "Recolector registrado exitosamente")
                self.limpiar_formulario_de_colector()
                self.apagar_camara_registrar()
                self.limpiar_foto()
                self.boton_camara_apagado()
                # Volver a la vista principal
                self.stackedWidget_Colector.setCurrentIndex(2)
                self.mostrar_recolectores_en_tabla()
            else:
                QMessageBox.warning(self, "Error", "No se pudo registrar el recolector")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error: {str(e)}")
            print(f"Error al registrar recolector: {str(e)}")
        
    def TomarFoto(self):
        """Captura la imagen actual y detecta el encoding facial solo si el rostro está dentro del rectángulo"""
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb_frame)

                # Dibujar el rectángulo azul de referencia
                cv2.rectangle(frame, 
                              (self.RECT_X1, self.RECT_Y1), 
                              (self.RECT_X2, self.RECT_Y2), 
                              (255, 0, 0), 2)

                rostro_valido = None
                for face_location in face_locations:
                    top, right, bottom, left = face_location

                    dentro = (
                        left   >= self.RECT_X1 and
                        top    >= self.RECT_Y1 and
                        right  <= self.RECT_X2 and
                        bottom <= self.RECT_Y2
                    )

                    if dentro:
                        rostro_valido = face_location
                        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    else:
                        # Rostro fuera del área — dibujar en gris
                        cv2.rectangle(frame, (left, top), (right, bottom), (128, 128, 128), 2)

                if rostro_valido:
                    self.face_encoding = face_recognition.face_encodings(rgb_frame, [rostro_valido])[0]
                    self.captured_image = frame.copy()

                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    rgb_frame = cv2.flip(rgb_frame, 1)
                    h, w, ch = rgb_frame.shape
                    bytes_per_line = ch * w
                    q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                    pixmap = QPixmap.fromImage(q_img)
                    self.Foto_Lbl.setPixmap(pixmap)

                    self.image_captured = True
                    self.stackedWidget_TomarFoto.setCurrentIndex(1)
                elif face_locations:
                    # Se detectaron rostros pero ninguno dentro del rectángulo
                    QMessageBox.warning(self, "Error", 
                                        "Coloca tu rostro dentro del recuadro azul e intenta nuevamente.")
                else:
                    QMessageBox.warning(self, "Error", 
                                        "No se detectó ningún rostro. Intente nuevamente.")

    def TomarFotoActualizada(self):
        """Captura la imagen actual y detecta el encoding facial solo si el rostro está dentro del rectángulo"""
        if self.cap_actualizar and self.cap_actualizar.isOpened():
            ret, frame = self.cap_actualizar.read()
            if ret:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb_frame)

                # Dibujar el rectángulo azul de referencia
                cv2.rectangle(frame, 
                              (self.RECT_X1, self.RECT_Y1), 
                              (self.RECT_X2, self.RECT_Y2), 
                              (255, 0, 0), 2)

                rostro_valido = None
                for face_location in face_locations:
                    top, right, bottom, left = face_location

                    dentro = (
                        left   >= self.RECT_X1 and
                        top    >= self.RECT_Y1 and
                        right  <= self.RECT_X2 and
                        bottom <= self.RECT_Y2
                    )

                    if dentro:
                        rostro_valido = face_location
                        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    else:
                        cv2.rectangle(frame, (left, top), (right, bottom), (128, 128, 128), 2)

                if rostro_valido:
                    self.face_encoding_actualizado = face_recognition.face_encodings(rgb_frame, [rostro_valido])[0]
                    self.captured_image_actualizar = frame.copy()

                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    rgb_frame = cv2.flip(rgb_frame, 1)
                    h, w, ch = rgb_frame.shape
                    bytes_per_line = ch * w
                    q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                    pixmap = QPixmap.fromImage(q_img)
                    self.FotoActualizada_Lbl.setPixmap(pixmap)

                    self.image_captured_actualizar = True
                    self.stackedWidget_TomarFotoActualizada.setCurrentIndex(1)
                elif face_locations:
                    QMessageBox.warning(self, "Error", 
                                        "Coloca tu rostro dentro del recuadro azul e intenta nuevamente.")
                else:
                    QMessageBox.warning(self, "Error", 
                                        "No se detectó ningún rostro. Intente nuevamente.")
    # def TomarFoto(self):
    #     """Captura la imagen actual y detecta el encoding facial"""
    #     if self.cap and self.cap.isOpened():
    #         ret, frame = self.cap.read()
    #         if ret:
    #             rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    #             face_locations = face_recognition.face_locations(rgb_frame)
                
    #             if face_locations:
    #                 top, right, bottom, left = face_locations[0]
    #                 cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
    #                 self.face_encoding = face_recognition.face_encodings(rgb_frame, face_locations)[0]
    #                 self.captured_image = frame.copy()
                    
    #                 # Convertir y mostrar la imagen capturada
    #                 rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    #                 rgb_frame = cv2.flip(rgb_frame, 1) # Congelar modo mirror
    #                 h, w, ch = rgb_frame.shape
    #                 bytes_per_line = ch * w
    #                 q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
    #                 pixmap = QPixmap.fromImage(q_img)
    #                 self.Foto_Lbl.setPixmap(pixmap)
                    
    #                 self.image_captured = True  # Congelamos la imagen
    #                 self.stackedWidget_TomarFoto.setCurrentIndex(1)
    #                 #QMessageBox.information(self, "Éxito", "Rostro detectado y encoding generado")
    #             else:
    #                 QMessageBox.warning(self, "Error", "No se detectó ningún rostro. Intente nuevamente.")
                    
    # def TomarFotoActualizada(self):
    #     """Captura la imagen actual y detecta el encoding facial"""
    #     if self.cap_actualizar and self.cap_actualizar.isOpened():
    #         ret, frame = self.cap_actualizar.read()
    #         if ret:
    #             rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    #             face_locations = face_recognition.face_locations(rgb_frame)
                
    #             if face_locations:
    #                 top, right, bottom, left = face_locations[0]
    #                 cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
    #                 self.face_encoding_actualizado = face_recognition.face_encodings(rgb_frame, face_locations)[0]
    #                 self.captured_image_actualizar = frame.copy()
                    
    #                 # Convertir y mostrar la imagen capturada
    #                 rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    #                 rgb_frame = cv2.flip(rgb_frame, 1) # Congelar modo mirror
    #                 h, w, ch = rgb_frame.shape
    #                 bytes_per_line = ch * w
    #                 q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
    #                 pixmap = QPixmap.fromImage(q_img)
    #                 self.FotoActualizada_Lbl.setPixmap(pixmap)
                    
    #                 self.image_captured_actualizar = True  # Congelamos la imagen
    #                 self.stackedWidget_TomarFotoActualizada.setCurrentIndex(1)
    #                 #QMessageBox.information(self, "Éxito", "Rostro detectado y encoding generado")
    #             else:
    #                 QMessageBox.warning(self, "Error", "No se detectó ningún rostro. Intente nuevamente.")
                    
    def limpiar_foto_actualizada(self):
        self.captured_image_actualizar = None
        self.face_encoding_actualizado = None
        self.stackedWidget_TomarFotoActualizada.setCurrentIndex(0)
        #self.TomarFotoColector_Btn.setEnabled(False)
        self.image_captured_actualizar = False  # Restauramos para permitir nuevas capturas


    def TomarOtraFotoActualizada(self):
        self.limpiar_foto_actualizada()
        self.stackedWidget_TomarFotoActualizada.setCurrentIndex(0)

    def ConfirmarFotoActualizada(self):
        try:
            nombre_completo = self.ActualizarNombre_lineEdit.text()
            localidad = self.ActualizarComunidad_lineEdit.text()
            telefono = self.ActualizarTelefono_lineEdit.text()
            id_Cuadrilla = self.ActualizarCuadrillero_comboBox.currentData()

            if not all([nombre_completo, localidad, telefono]):
                QMessageBox.warning(self, "Advertencia", "Nombre, localidad y teléfono son obligatorios")
                return

            if self.captured_image_actualizar is None or self.face_encoding_actualizado is None:
                QMessageBox.warning(self, "Error", "Debe tomar una foto primero")
                return

            # Convertir la imagen OpenCV a bytes para guardar en DB
            _, img_encoded = cv2.imencode('.jpg', self.captured_image_actualizar)
            foto_bytes = img_encoded.tobytes()

            if actualizar_colector_con_encoder(
                id_Recolector=self.id_recolector,
                nombre_completo=nombre_completo,
                encoder=self.face_encoding_actualizado,  # numpy array, se serializa en la función
                foto=foto_bytes,                          # bytes de la imagen
                localidad=localidad,
                telefono=telefono,
                id_cuadrilla=id_Cuadrilla
            ):
                QMessageBox.information(self, "Éxito", "Colector actualizado correctamente")
                self.mostrar_recolectores_en_tabla()
                self.limpiar_foto_actualizada()
                self.apagar_camara_atualizar()
                self.boton_camara_apagado()

                self.stackedWidget_Colector.setCurrentIndex(2)
            else:
                QMessageBox.warning(self, "Error", "No se pudo actualizar el colector")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error: {str(e)}")

    def limpiar_formulario_de_colector(self):
        """Limpia todos los campos del formulario"""
        self.NombreCompleto_lineEdit.clear()
        self.Comunidad_lineEdit.clear()
        self.Telefono_lineEdit.clear()
        self.Cuadrillero_comboBox.setCurrentIndex(0)
        self.captured_image = None
        self.face_encoding = None
        self.stackedWidget_TomarFoto.setCurrentIndex(0)
        self.TomarFotoColector_Btn.setEnabled(False)
        self.image_captured = False  # Restauramos para permitir nuevas capturas

    def limpiar_foto(self):
        self.captured_image = None
        self.face_encoding = None
        self.stackedWidget_TomarFoto.setCurrentIndex(0)
        #self.TomarFotoColector_Btn.setEnabled(False)
        self.image_captured = False  # Restauramos para permitir nuevas capturas

    def TomarOtraFoto(self):
        self.limpiar_foto()
        self.stackedWidget_TomarFoto.setCurrentIndex(0)
        
    def Back_ColectorMenu(self):
        self.boton_camara_apagado()
        self.stackedWidget_Principal.setCurrentIndex(0)

    # def ShowConfigurarCosecha(self):
    #     self.stackedWidget_Principal.setCurrentIndex(2)
    #     self.stackedWidget_Cosecha.setCurrentIndex(0)
    #     self.cargar_tablas_comboBox()
    #     self.NombreCompleto_listWidget.setVisible(False)
    #     #self.cargar_macrotuneles_comboBox()
    #     self.BotonVerdeOscuro(self.ConfirmarConfiguracionColector_Btn)

    #     # Iniciar el reconocimiento facial
    #     self.facial_worker.start(0)

    # def ShowConfigurarCosecha(self):
    #     # Verificar primero que las camaras estén conectadas
    #     if self.camaras_conectas == True or self.camaras_conectas == False:
    #         try:
    #             self.camera_checker = CameraConnectionManager(self)
    #             self.camera_checker.start_check(self.on_cameras_checked)
    #         except:
    #             pass
    #     if self.camaras_conectas == False:
    #         # QMessageBox.warning(self, "Error", "Camaras no conectadas, verifique conexion")
    #         return
    #     else: 
    #         # Desconectar primero para evitar señales duplicadas
    #         try:
    #             self.FaseConfiguracion_comboBox.currentIndexChanged.disconnect()
    #             self.TablaConfiguracion_comboBox.currentIndexChanged.disconnect()
    #             self.MacrotunelConfiguracion_comboBox.currentIndexChanged.disconnect()
    #         except:
    #             pass

    #         # Conectar en cascada
    #         self.FaseConfiguracion_comboBox.currentIndexChanged.connect(
    #             lambda: (self.cargar_tablas_comboBox_cosecha(),
    #                     self.cargar_macrotuneles_comboBox_cosecha(),
    #                     self.cargar_linea_comboBox_cosecha())
    #         )
    #         self.TablaConfiguracion_comboBox.currentIndexChanged.connect(
    #             lambda: (self.cargar_macrotuneles_comboBox_cosecha(),
    #                     self.cargar_linea_comboBox_cosecha())
    #         )
    #         self.MacrotunelConfiguracion_comboBox.currentIndexChanged.connect(
    #             self.cargar_linea_comboBox_cosecha
    #         )

    #         key, ok = QInputDialog.getText(
    #             self,
    #             "Acceso Restringido",
    #             "Ingrese la clave de acceso:",
    #             QLineEdit.EchoMode.Password
    #         )

    #         if not ok:
    #             return  # Canceló el usuario

    #         key = key.strip()

    #         if key == "":
    #             QMessageBox.warning(self, "Error", "No ingresaste ninguna clave")
    #             return

    #         acceso = KeysAcceso()

    #         if acceso.key_acceso_modulo(key):

    #             # Carga inicial
    #             self.stackedWidget_Principal.setCurrentIndex(2)
    #             self.stackedWidget_Cosecha.setCurrentIndex(0)
    #             self.stackedWidget_cuadrillero.setCurrentIndex(1)
    #             self.TomarFotoRecognition_stackedWidget.setCurrentIndex(0)
    #             self.ConfirmarConfiguracionColector_Btn.setEnabled(False)
    #             self.cargar_fases_comboBox_cosecha()
    #             self.cargar_tablas_comboBox_cosecha()
    #             self.cargar_macrotuneles_comboBox_cosecha()
    #             self.cargar_linea_comboBox_cosecha()
    #             self.cargar_modalidades_comboBox_cosecha()
    #             self.NombreCompleto_listWidget.setVisible(False)
    #             self.BotonVerdeOscuro(self.ConfirmarConfiguracionColector_Btn)
    #             self.facial_worker.start(0)

    #         else:
    #             QMessageBox.warning(self, "Acceso Denegado", "Clave incorrecta")

    def deshabilitar_modulos(self):
        self.CosechaMenu_Btn.setEnabled(False)
        self.ShowModulosCosecha_Btn.setEnabled(False)
        self.Sabana_Btn.setEnabled(False)
        self.CheckingMenu_Btn.setEnabled(False)
        self.CerrarSession_Btn.setEnabled(False)

    def habilitar_modulos(self):
        self.CosechaMenu_Btn.setEnabled(True)
        self.ShowModulosCosecha_Btn.setEnabled(True)
        self.Sabana_Btn.setEnabled(True)
        self.CheckingMenu_Btn.setEnabled(True)
        self.CerrarSession_Btn.setEnabled(True)

    def ShowConfigurarCosecha(self):
        self.deshabilitar_modulos()
        # Siempre verificar cámaras primero, y manejar todo en el callback
        self.camera_checker = CameraConnectionManager(self)
        self.camera_checker.start_check(self._on_cameras_checked_for_cosecha)


    def _on_cameras_checked_for_cosecha(self, cameras_ok, detected_ports):
        # Actualizar estado visual y variable
        self.on_cameras_checked(cameras_ok, detected_ports)
        
        if not self.on_impresora_checked():
            self.habilitar_modulos()
            return

        if not cameras_ok:
            self.habilitar_modulos()
            return

        if not self.on_bascula_checked():
            pass

        # Solo si hay cámaras, continuar con el flujo de acceso
        try:
            self.FaseConfiguracion_comboBox.currentIndexChanged.disconnect()
            self.TablaConfiguracion_comboBox.currentIndexChanged.disconnect()
            self.MacrotunelConfiguracion_comboBox.currentIndexChanged.disconnect()
        except:
            pass

        self.FaseConfiguracion_comboBox.currentIndexChanged.connect(
            lambda: (self.cargar_tablas_comboBox_cosecha(),
                    self.cargar_macrotuneles_comboBox_cosecha(),
                    self.cargar_linea_comboBox_cosecha())
        )
        self.TablaConfiguracion_comboBox.currentIndexChanged.connect(
            lambda: (self.cargar_macrotuneles_comboBox_cosecha(),
                    self.cargar_linea_comboBox_cosecha())
        )
        self.MacrotunelConfiguracion_comboBox.currentIndexChanged.connect(
            self.cargar_linea_comboBox_cosecha
        )

        key, ok = QInputDialog.getText(
            self,
            "Modulo de Cosecha",
            "Ingrese la clave de acceso:",
            QLineEdit.EchoMode.Password
        )

        if not ok:
            self.boton_camara_apagado()
            self.boton_bascula_apagado()
            self.boton_impresora_apagado()
            self.habilitar_modulos()
            return

        key = key.strip()

        if key == "":
            QMessageBox.warning(self, "Error", "No ingresaste ninguna clave")
            self.boton_camara_apagado()
            self.boton_bascula_apagado()
            self.boton_impresora_apagado()
            self.habilitar_modulos()
            return

        acceso = KeysAcceso()

        if acceso.key_acceso_modulo(key):
            self.stackedWidget_Principal.setCurrentIndex(2)
            self.stackedWidget_Cosecha.setCurrentIndex(0)
            self.stackedWidget_cuadrillero.setCurrentIndex(1)
            self.TomarFotoRecognition_stackedWidget.setCurrentIndex(0)
            self.ConfirmarConfiguracionColector_Btn.setEnabled(False)
            self.cargar_fases_comboBox_cosecha()
            self.cargar_tablas_comboBox_cosecha()
            self.cargar_macrotuneles_comboBox_cosecha()
            self.cargar_linea_comboBox_cosecha()
            self.cargar_modalidades_comboBox_cosecha()
            self.habilitar_modulos()
            self.NombreCompleto_listWidget.setVisible(False)
            self.BotonVerdeOscuro(self.ConfirmarConfiguracionColector_Btn)
            self.facial_worker.start(0)
        else:
            QMessageBox.warning(self, "Acceso Denegado", "Clave incorrecta")
            self.boton_camara_apagado()
            self.boton_bascula_apagado()
            self.boton_impresora_apagado()
            self.habilitar_modulos()


    def boton_camara_apagado(self):
        self.CamarasTestigo_lbl.setStyleSheet("""
                QToolButton{
                    background-color: #949192;
                    border-radius: 10px;
                }
            """)
        
    def boton_bascula_apagado(self):
        self.BasculaTestigo_toolButton.setStyleSheet("""
                QToolButton{
                    background-color: #949192;
                    border-radius: 10px;
                }
            """)
        
    def boton_impresora_apagado(self):
        self.ImpresoraTestigo_toolButton.setStyleSheet("""
                QToolButton{
                    background-color: #949192;
                    border-radius: 10px;
                }
            """)

    # def update_facial_recognition_frame(self, frame):
    #     """Actualiza el QLabel con el frame procesado"""
    #     if self.freeze_frame and self.last_frame is not None:
    #         frame = self.last_frame
    #     else:
    #         self.last_frame = frame.copy()
        
    #     frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    #     h, w, ch = frame.shape
    #     bytes_per_line = ch * w
    #     q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
    #     pixmap = QPixmap.fromImage(q_img)
        
    #     self.FaceRecognition_Lbl.setPixmap(pixmap)
    #     self.FaceRecognition_Lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    #     self.FaceRecognition_Lbl.setScaledContents(False)

    ########################################################################
    #
    ########################################################################
    def update_facial_recognition_frame(self, frame):
        if self.freeze_frame and self.last_frame is not None:
            frame = self.last_frame
        else:
            if self._frame_is_black(frame):
                self._handle_camera_disconnected()
                return
            
            self.last_frame = frame.copy()
            self._camera_reconnect_attempted = False

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)

        self.FaceRecognition_Lbl.setPixmap(pixmap)
        self.FaceRecognition_Lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.FaceRecognition_Lbl.setScaledContents(False)


    def _frame_is_black(self, frame, threshold=10):
        """Retorna True si el frame está mayormente negro"""
        return np.mean(frame) < threshold


    def _set_testigo_camaras(self, conectadas: bool):
        """Actualiza el indicador visual de estado de cámaras"""
        if conectadas:
            self.CamarasTestigo_lbl.setStyleSheet("""
                QToolButton {
                    background-color: #8bc34a;
                    border-radius: 10px;
                }
            """)
        else:
            self.CamarasTestigo_lbl.setStyleSheet("""
                QToolButton {
                    background-color: rgb(255, 0, 0);
                    border-radius: 10px;
                }
            """)


    def _handle_camera_disconnected(self):
        if getattr(self, '_camera_reconnect_attempted', False):
            return

        self._camera_reconnect_attempted = True
        self._set_testigo_camaras(False)  # 🔴 Rojo al desconectarse
        self.facial_worker.stop()
        QTimer.singleShot(2000, self._try_reconnect_facial_camera)


    def _try_reconnect_facial_camera(self):
        try:
            cap_test = cv2.VideoCapture(self.puerto_facial)
            if cap_test.isOpened():
                ret, frame = cap_test.read()
                cap_test.release()

                if ret and not self._frame_is_black(frame):
                    self.facial_worker.start(self.puerto_facial)
                    self._camera_reconnect_attempted = False
                    self._set_testigo_camaras(True)  # 🟢 Verde al reconectarse
                    print("Cámara reconectada exitosamente")
                    return

            cap_test.release()
        except Exception as e:
            print(f"Error al intentar reconectar cámara: {e}")

        print("Cámara aún no disponible, reintentando...")
        QTimer.singleShot(2000, self._try_reconnect_facial_camera)



    ########################################################################
    #
    ########################################################################
    def update_facial_checador_frame(self, frame):
        """Actualiza el QLabel con el frame procesado"""
        if self.freeze_frame_checador and self.last_frame_checador is not None:
            frame = self.last_frame_checador
        else:
            if self._frame_is_black(frame):
                self._handle_camera_disconnected()
                return
            self.last_frame_checador = frame.copy()
            self._camera_reconnect_attempted = False
        
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        
        self.FaceRecognitionCheck_Lbl.setPixmap(pixmap)
        self.FaceRecognitionCheck_Lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.FaceRecognitionCheck_Lbl.setScaledContents(False)

    # def ConfirmarFaceRecognition(self):
    #     # self.ConfirmarConfiguracionColector_Btn.setEnabled(True)
    #     """Congela la imagen y muestra el nombre del recolector"""
    #     if hasattr(self, 'current_face_data') and self.current_face_data:
    #         name, emp_info, confidence = self.current_face_data
    #         if name == "DESCONOCIDO":
    #             QMessageBox.warning(self, "Advertencia", "Rostro no reconocido. Por favor, intente de nuevo o regístrese.")
    #             return

    #         self.NombreCompletoText_lineEdit.setText(name)
    #         self.NombreCompleto_listWidget.setVisible(False)
    #         self.facial_worker.set_freeze_frame(True)  
    #         self.stackedWidget_cuadrillero.setCurrentIndex(1)
    #         self.cargar_cuadrillas_cosecha()
    #         self.validar_cuadrillero_registrado()
    #         self._cuadrillas_cargadas = False
    #     else:
    #         QMessageBox.warning(self, "Advertencia", "No se ha detectado ningún recolector reconocido")

    def ConfirmarFaceRecognition(self):

        if self.facial_worker.face_count == 0:
            QMessageBox.warning(
                self,
                "Advertencia",
                "No se detectó ningún rostro"
            )
            return

        if self.facial_worker.face_count > 1:
            QMessageBox.warning(
                self,
                "Advertencia",
                "Debe haber solamente un rostro frente a la cámara"
            )
            return

        if not self.current_face_data:
            QMessageBox.warning(
                self,
                "Advertencia",
                "No se ha detectado ningún rostro"
            )
            return

        detection, face_count = self.current_face_data

        if detection is None:
            QMessageBox.warning(
                self,
                "Advertencia",
                "No se detectó ningún rostro válido"
            )
            return

        name, emp_info, confidence = detection
        if name == "DESCONOCIDO":
            QMessageBox.warning(
                self,
                "Advertencia",
                "Rostro no reconocido"
            )
            return

        self.NombreCompletoText_lbl.setText(name)
        self.NombreCompleto_listWidget.setVisible(False)
        self.facial_worker.set_freeze_frame(True)
        self.stackedWidget_cuadrillero.setCurrentIndex(1)
        self.TomarFotoRecognition_stackedWidget.setCurrentIndex(1)
        self.cargar_modalidades_comboBox_cosecha(name=name)
        self.cargar_cuadrillas_cosecha()
        # self.cargar_cuadrillas_cosecha()
        self.validar_cuadrillero_registrado()
        self._cuadrillas_cargadas = False

    def TomarOtroRecognition(self):
        self.ReiniciarFaceRecognition()
        self.BotonVerdeOscuro(self.ConfirmarConfiguracionColector_Btn)
        self.ConfirmarConfiguracionColector_Btn.setEnabled(False)
        self.NombreCompleto_listWidget.setVisible(False)
        self.CuadrilleroRegistrado_Lbl.clear()
        self.cargar_modalidades_comboBox_cosecha()
        self.TomarFotoRecognition_stackedWidget.setCurrentIndex(0)
        

    def eventFilter(self, obj, event):
        if obj == self.CuadrilleroConfiguracion_comboBox:
            if event.type() == QEvent.Type.MouseButtonPress:
                if not self._cuadrillas_cargadas:
                    self.cargar_cuadrillas_cosecha()
                    self._cuadrillas_cargadas = True
        return super().eventFilter(obj, event)

    def on_cuadrilla_seleccionada(self):
        texto = self.CuadrilleroConfiguracion_comboBox.currentText().strip()

        # Evitar activar si está vacío o es un texto placeholder
        if texto and texto != "Selecciona un cuadrillero":
            self.ConfirmarConfiguracionColector_Btn.setEnabled(True)
            self.BotonVerdeClaro(self.ConfirmarConfiguracionColector_Btn)
        else:
            self.ConfirmarConfiguracionColector_Btn.setEnabled(False)

    def validar_cuadrillero_registrado(self):
        texto = self.CuadrilleroRegistrado_Lbl.text().strip()

        if texto:  # Si NO está vacío
            self.ConfirmarConfiguracionColector_Btn.setEnabled(True)
            self.BotonVerdeClaro(self.ConfirmarConfiguracionColector_Btn)
        else:
            self.ConfirmarConfiguracionColector_Btn.setEnabled(False)

    # Nuevo método para manejar detecciones
    def handle_face_detected(self, face_data):
        """Almacena los datos del rostro detectado"""
        self.current_face_data = face_data

    def update_face_count(self, count):
        self.face_count = count

    def handle_face_detected_checador(self, face_data):
        """Almacena los datos del rostro detectado"""
        self.current_face_data_checador = face_data

    """
    Implementar cuando necesite empezar nueva cosecha
    """
    def ReiniciarFaceRecognition(self):
        """Reinicia el reconocimiento facial"""
        if hasattr(self, 'facial_worker'):
            self.facial_worker.set_freeze_frame(False)
        self.NombreCompletoText_lbl.setText("")
        self.current_face_data = None

    def ReiniciarFaceRecognitionCheck(self):
        """Reinicia el reconocimiento facial"""
        if hasattr(self, 'checador_worker'):
            self.checador_worker.set_freeze_frame(False)
        self.NombreRecolectorCheck_Lbl.setText("")
        self.FechaRecolectorCheck_Lbl.setText("")
        self.ModalidadRecolectorCheck_Lbl.setText("")

        self.current_face_data_checador = None

    def ShowCalificarCosecha(self):
        if not self.on_impresora_checked():
            return
        """Transfiere los datos de configuración a los labels de cosecha con validaciones"""
        try:
            # Validar que haya un nombre seleccionado
            #nombre = self.NombreCompletoText_Lbl.text()
            nombre = self.NombreCompletoText_lbl.text()
            if not nombre:
                QMessageBox.warning(self, "Advertencia", "No se ha seleccionado ningún recolector")
                return
                
            # Validar que haya una fase seleccionada
            fase = self.FaseConfiguracion_comboBox.currentText()
            if not fase:
                QMessageBox.warning(self, "Advertencia", "No se ha seleccionado ninguna fase")
                return

            # Validar que haya una tabla seleccionada
            tabla = self.TablaConfiguracion_comboBox.currentText()
            if not tabla:
                QMessageBox.warning(self, "Advertencia", "No se ha seleccionado ninguna tabla")
                return
                
            # Validar que haya un macrotúnel seleccionado
            macrotunel = self.MacrotunelConfiguracion_comboBox.currentText()
            if not macrotunel:
                QMessageBox.warning(self, "Advertencia", "No se ha seleccionado ningún macrotúnel")
                return
            
            # Validar que haya una linea seleccionada
            linea = self.LineaConfiguracion_comboBox.currentText()
            if not linea:
                QMessageBox.warning(self, "Advertencia", "No se ha seleccionado ninguna linea")
                return
            
            # Validar que haya un cuadrillero seleccionado
            modalidad = self.ModalidadConfiguracion_comboBox.currentText()
            if not modalidad:
                QMessageBox.warning(self, "Advertencia", "No se ha seleccionado ningún modalidad")
                return

            cuadrilla_combo_lbl = self.CuadrilleroConfiguracion_comboBox.currentText()
            cuadrilla_lbl = self.CuadrilleroRegistrado_Lbl.text()
                
            # Transferir los datos
            self.NombreCosechaText_Lbl.setText(nombre)
            self.FaseCosechaText_Lbl.setText(fase)
            self.TablaCosechaText_Lbl.setText(tabla)
            self.MacrotunelCosechaText_Lbl.setText(macrotunel)
            self.LineaCosechaText_Lbl.setText(linea)

            self.ModalidadDatosCosechaText_Lbl.setText(modalidad)

            """Detectar primero si hay texto en cuadrilla_combo_lbl o cuadrilla_lbl
               y luego agregarlo a self.CuadrillaCosechaText_Lbl"""
            if cuadrilla_lbl:  
                self.CuadrillaCosechaText_Lbl.setText(cuadrilla_lbl)
            else:  
                self.CuadrillaCosechaText_Lbl.setText(cuadrilla_combo_lbl)
            
            # Cambiar a la página de calificación
            self.CamaraConfig_Cosecha()
            self.ConfirmarCalificacion_Btn.setEnabled(False)
            
            # Cambiar el estilo del botón
            self.BotonVerdeOscuro(self.ConfirmarCalificacion_Btn)

            # if not self.on_bascula_checked():
            #     pass

            self.stackedWidget_Cosecha.setCurrentIndex(1)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error al transferir los datos: {str(e)}")

    def BotonVerdeClaro(self, botonClaro):
        botonClaro.setStyleSheet("""
            QPushButton {

                background-color: #749540;
                /*border: 2px solid black;*/
                color: white;  /* Cambia el color de la fuente a blanco */
                border-radius: 25px;  /* Ajusta el valor para hacer las esquinas más o menos redondas */
                padding: 10px;  /* Ajusta el margen interno del QLabel */
                border: 4px solid white;
            }
            
        """)

    def BotonVerdeOscuro(self, botonOscuro):
        botonOscuro.setStyleSheet("""
            QPushButton {

                background-color: #4a6b2f;
                /*border: 2px solid black;*/
                color: white;  /* Cambia el color de la fuente a blanco */
                border-radius: 25px;  /* Ajusta el valor para hacer las esquinas más o menos redondas */
                padding: 10px;  /* Ajusta el margen interno del QLabel */
                border: 4px solid white;
            }
            
        """)
    def Modulos_Invisibles(self):
        self.ColectorMenu_Btn.setVisible(False)
        self.TablaMenu_Btn.setVisible(False)
        self.CuadrilleroMenu_Btn.setVisible(False)
        self.MacrotunelMenu_Btn.setVisible(False)
        self.FaseMenu_Btn.setVisible(False)
        self.LineaMenu_Btn.setVisible(False)
        self.Back_MenuPrincipalModulos_Btn.setVisible(False)

    def Modulos_Visibles(self):
        self.ColectorMenu_Btn.setVisible(True)
        self.TablaMenu_Btn.setVisible(True)
        self.CuadrilleroMenu_Btn.setVisible(True)
        self.MacrotunelMenu_Btn.setVisible(True)
        self.FaseMenu_Btn.setVisible(True)
        self.LineaMenu_Btn.setVisible(True)
        self.Back_MenuPrincipalModulos_Btn.setVisible(True)

    # def MostrarModulosCosecha(self):
    #     self.Modulos_Visibles()
    #     #self.Modulos_widget.setVisible(True)
    #     self.ShowModulosCosecha_Btn.setVisible(False)
    #     self.CosechaMenu_Btn.setVisible(False)
    #     self.Sabana_Btn.setVisible(False)
    #     self.CerrarSession_Btn.setVisible(False)
    #     self.Back_MenuPrincipalModulos_Btn.setVisible(True)

    def MostrarModulosCosecha(self):
        self.deshabilitar_modulos()

        key, ok = QInputDialog.getText(
            self,
            "Configurar Datos Cosecha",
            "Ingrese la clave de acceso:",
            QLineEdit.EchoMode.Password
        )

        if not ok:
            self.habilitar_modulos()
            return  # Canceló el usuario

        key = key.strip()

        if key == "":
            QMessageBox.warning(self, "Error", "No ingresaste ninguna clave")
            self.habilitar_modulos()
            return

        acceso = KeysAcceso()

        if acceso.key_acceso_modulo(key):
            self.Modulos_Visibles()
            self.ShowModulosCosecha_Btn.setVisible(False)
            self.CosechaMenu_Btn.setVisible(False)
            self.Sabana_Btn.setVisible(False)
            self.CerrarSession_Btn.setVisible(False)
            self.CheckingMenu_Btn.setVisible(False)
            # self.Gpa_graphicsView.setVisible(False)
            self.Back_MenuPrincipalModulos_Btn.setVisible(True)
            self.habilitar_modulos()

        else:
            QMessageBox.warning(self, "Acceso Denegado", "Clave incorrecta")
            self.habilitar_modulos()

    def Back_MenuPrincipalModulos(self):
        self.Modulos_Invisibles()
        #self.Modulos_widget.setVisible(False)
        self.ShowModulosCosecha_Btn.setVisible(True)
        # self.Gpa_graphicsView.setVisible(True)
        self.CosechaMenu_Btn.setVisible(True)
        self.Sabana_Btn.setVisible(True)
        self.CerrarSession_Btn.setVisible(True)
        self.CheckingMenu_Btn.setVisible(True)
        self.Back_MenuPrincipalModulos_Btn.setVisible(False)
        

    def ShowDatosCosecha(self):
        """Transfiere los datos de configuración a los labels de cosecha con validaciones"""
        try:
            # Validar que haya un nombre seleccionado
            nombre = self.NombreCosechaText_Lbl.text()
            if not nombre:
                QMessageBox.warning(self, "Advertencia", "No se ha seleccionado ningún recolector")
                return
                
            # Validar que haya una tabla seleccionada
            fase = self.FaseCosechaText_Lbl.text()
            if not fase:
                QMessageBox.warning(self, "Advertencia", "No se ha seleccionado ninguna fase")
                return

            # Validar que haya una tabla seleccionada
            tabla = self.TablaCosechaText_Lbl.text()
            if not tabla:
                QMessageBox.warning(self, "Advertencia", "No se ha seleccionado ninguna tabla")
                return
                
            # Validar que haya un macrotúnel seleccionado
            macrotunel = self.MacrotunelCosechaText_Lbl.text()
            if not macrotunel:
                QMessageBox.warning(self, "Advertencia", "No se ha seleccionado ningún macrotúnel")
                return
                
            # Validar que haya una tabla seleccionada
            linea = self.LineaCosechaText_Lbl.text()
            if not linea:
                QMessageBox.warning(self, "Advertencia", "No se ha seleccionado ninguna linea")
                return

            # Validar que haya un cuadrillero seleccionado
            cuadrillero = self.CuadrillaCosechaText_Lbl.text()
            if not cuadrillero:
                QMessageBox.warning(self, "Advertencia", "No se ha seleccionado ningún macrotúnel")
                return

            # Validar que haya un cuadrillero seleccionado
            modalidad_texto = self.ModalidadConfiguracion_comboBox.currentText()   # Para el label
            modalidad_id = self.ModalidadConfiguracion_comboBox.currentData()      # Para registrar

            if not modalidad_texto:
                QMessageBox.warning(self, "Advertencia", "No se ha seleccionado ningún modalidad")
                return

            # Transferir los datos
            self.NombreDatosCosechaText_Lbl.setText(nombre)
            self.FaseDatosCosechaText_Lbl.setText(fase)
            self.TablaDatosCosechaText_Lbl.setText(tabla)
            self.MacrotunelDatosCosechaText_Lbl.setText(macrotunel)
            self.LineaDatosCosechaText_Lbl.setText(linea)
            self.ModalidadDatosCosechaText_Lbl.setText(modalidad_texto)
            self.CuadrillaDatosCosechaText_Lbl.setText(cuadrillero)

            fecha_actual = date.today()
            fecha_formateada = fecha_actual.strftime("%d/%m/%Y")
            id = Obtener_ID_Recolector(self.NombreCosechaText_Lbl)
            entregas = Total_Entregas_Hoy_Recolector(id)
            calificacion = Obtener_Calificaciones_Separadas(id)
            peso_total = Obtener_Peso_Total_Cosechador(id)
            peso_total_entrega = Obtener_Peso_Total_Entrega(self.current_entrega_id)

            # Ticket del dia
            self.FechaTicketText_Lbl.setText(fecha_formateada)
            self.VueltaTicketText_Lbl.setText(str(entregas))
            self.NombreTicketText_Lbl.setText(nombre)
            self.BuenasTicketText_Lbl.setText(str(calificacion.Buenas))
            self.RegularesTicketText_Lbl.setText(str(calificacion.Regulares))
            self.MalasTicketTexto_Lbl.setText(str(calificacion.Malas))
            self.PesoTicketTexto_Lbl.setText(str(peso_total))
            self.PesoVueltaTexto_Lbl.setText(str(peso_total_entrega))
            
            # Cambiar a la página de datos cosecha
            self.stackedWidget_Cosecha.setCurrentIndex(2)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error al transferir los datos: {str(e)}")
            print(f"Ocurrió un error al transferir los datos: {str(e)}")
        
    def LimpiarPesoCalificacion(self):    
        self.CalidadCosechaText_Lbl.clear()
        self.PesoCosechaText_Lbl.clear()

    def NuevaCosecha(self):
        self.BuenaCalidad_Btn.setEnabled(True)
        self.RegularCalidad_Btn.setEnabled(True)
        self.MalaCalidad_Btn.setEnabled(True)
        self.ConfirmarCalificacion_Btn.setEnabled(False)
        self.LimpiarPesoCalificacion()
        self.BotonVerdeOscuro(self.ConfirmarCalificacion_Btn)
        self.stackedWidget_Cosecha.setCurrentIndex(1)

    def Ticket_De_Vuelta(self, peso_vuelta):
        # Ticket del dia
        Fecha = self.FechaTicketText_Lbl.text()
        Vuelta = self.VueltaTicketText_Lbl.text()
        Nombre = self.NombreTicketText_Lbl.text()
        Cant_Buenas = self.BuenasTicketText_Lbl.text()
        Cant_Regulares = self.RegularesTicketText_Lbl.text()
        Cant_Malas = self.MalasTicketTexto_Lbl.text()
        Peso = self.PesoTicketTexto_Lbl.text()

        print("BERRIES LEON - TICKET DE PASADA")
        print("-"*30)
        # print("Fecha: ", Fecha)
        print(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",),
        print("Vuelta: ", Vuelta)
        print("Nombre: ", Nombre)
        print("Buenas: ", Cant_Buenas)
        print("Regulares: ", Cant_Regulares)
        print("Malas: ", Cant_Malas)
        print(f"Peso: {peso_vuelta} Kg")
        print("-"*30)

        # Crear instancia del impresor de tickets e imprimir
        printer = TicketPrinter()  # Se autodetecta o puedes pasar el nombre: TicketPrinter("ZKTeco")
        printer.print_ticket_de_vuelta(
            fecha=Fecha,
            vuelta=Vuelta,
            nombre=Nombre,
            buenas=Cant_Buenas,
            regulares=Cant_Regulares,
            malas=Cant_Malas,
            peso_vuelta=peso_vuelta
    )

    def TicketDelDia(self):
        nombre = self.NombreCompletoText_lbl.text()
        resumen = Obtener_Resumen_Colector(nombre)

        if resumen:
            print("BERRIES LEON - TICKET DE VUELTA")
            print("-"*30)
            # print(f"Fecha: {resumen['Fecha'].strftime("%d/%m/%Y")}")
            print(f"Fecha: {resumen['Fecha'].strftime('%d/%m/%Y %H:%M:%S')}")
            print(f"Nombre: {str(nombre)}")
            print(f"Total Vueltas: {str(resumen['Total_Entregas'])}")
            print(f"Peso Total: {resumen['Peso_Total_Acumulado']} kg")
            print(f"Total Buenas: {str(resumen['Total_Buenas'])}")
            print(f"Total Regulares: {str(resumen['Total_Regulares'])}")
            print(f"Total Malas: {str(resumen['Total_Malas'])}")
            print("-"*30)

            # # Crear instancia del impresor de tickets e imprimir
            printer = TicketPrinter()
            printer.print_ticket_del_dia(
                fecha = resumen['Fecha'].strftime('%d/%m/%Y %H:%M:%S'),
                nombre=nombre,
                total_vueltas=str(resumen['Total_Entregas']),
                peso_total=f"{resumen['Peso_Total_Acumulado']} kg",
                total_buenas=str(resumen['Total_Buenas']),
                total_regulares=str(resumen['Total_Regulares']),
                total_malas=str(resumen['Total_Malas'])
            )
        else:
            print(f"{nombre} no ha cosechado el día de hoy")


    # def FinalizarCosecha(self):
    #     """Punto de entrada: verifica la impresora antes de continuar"""
    #     self.printer_checker = PrinterConnectionManager(self)
    #     self.printer_checker.start_check(self._on_printer_checked_finalizar)


    def FinalizarCosecha(self):
        """Finaliza el proceso de cosecha y libera los recursos de la cámara"""
        try:
            if not self.on_impresora_checked():
                pass
            # Detener el timer de actualización de la cámara
            if hasattr(self, 'timer_registroCosecha') and self.timer_registroCosecha.isActive():
                self.timer_registroCosecha.stop()
            
            # Liberar la cámara de cosecha si está abierta
            if hasattr(self, 'cap_cosecha') and self.cap_cosecha is not None:
                self.cap_cosecha.release()
                self.cap_cosecha = None
            
            # Limpiar el QLabel de la cámara
            self.FotoCosechaCalificada_Lbl.clear()
            self.FotoCosechaCalificada_Lbl.setText("Cámara no activa")
        
            self.BotonVerdeOscuro(self.ConfirmarConfiguracionColector_Btn)
            self.ConfirmarConfiguracionColector_Btn.setEnabled(False)
            self.stackedWidget_Cosecha.setCurrentIndex(0)

            # Finalizar la entrega y obtener el peso total
            if self.current_entrega_id:
                if finalizar_entrega(self.current_entrega_id):
                    peso_total = Obtener_Peso_Total_Entrega(self.current_entrega_id)
                    print(f"Peso total de la entrega: {peso_total} kg")
                    # self.PesoTotalLabel.setText(f"{peso_total} kg")

                    self.Ticket_De_Vuelta(peso_total)
                    
            #Limpiar Cuadrillero Lbl
            self.CuadrilleroRegistrado_Lbl.clear()
            self.CuadrillaDatosCosechaText_Lbl.clear()
            self.CuadrilleroConfiguracion_comboBox.clear()
            self.CuadrilleroRegistrado_Lbl.clear()
            self.cargar_modalidades_comboBox_cosecha()

            # Resetear banderas y variables
            self.flag_current_entrega = False
            self.current_entrega_id = None
            self.image_captured_cosecha = False
            self.last_cosecha_frame = None
            self.BuenaCalidad_Btn.setEnabled(True)
            self.RegularCalidad_Btn.setEnabled(True)
            self.MalaCalidad_Btn.setEnabled(True)
            self.LimpiarPesoCalificacion()
            
        except Exception as e:
            QMessageBox.warning(self, "Advertencia", 
                            f"Ocurrió un error al finalizar la cosecha: {str(e)}")
        finally:
            # Asegurarse de cambiar la vista aunque falle algo
            self.ReiniciarFaceRecognition()
            self.NombreCompleto_listWidget.setVisible(False)
            self.TomarFotoRecognition_stackedWidget.setCurrentIndex(0)
            self.stackedWidget_Cosecha.setCurrentIndex(0)

    def Back_DatosCosecha(self):
        pass

    def Back_CalificacionCosecha(self):
        pass

    def Back_ConfiguracionCosecha(self):
        """Detener todo al cerrar la ventana"""
        self.facial_worker.stop()
        self.facial_thread.quit()
        self.facial_thread.wait()
        self.ReiniciarFaceRecognition()
        self.CuadrilleroConfiguracion_comboBox.clear()
        self.boton_camara_apagado()
        self.boton_bascula_apagado()
        self.boton_impresora_apagado()
        self.stackedWidget_Principal.setCurrentIndex(0)

    def Back_CuadrillerosMenu(self):
        self.stackedWidget_Principal.setCurrentIndex(0) # Refrescar datos al mostrar

    def CrearCuadrillero(self):
        self.stackedWidget_Cuadrilleros.setCurrentIndex(1)
        self.CrearCuadrilleroClave_lineEdit.setText("C-")

    def ShowCuadrillerosMenu(self):
        self.stackedWidget_Principal.setCurrentIndex(3)
        self.stackedWidget_Cuadrilleros.setCurrentIndex(0)
        self.mostrar_cuadrillas_en_tabla()
    
    def Back_CrearCuadrillero(self):
        self.stackedWidget_Cuadrilleros.setCurrentIndex(0)
    
    """
    Metodos para cargar datos a los comboBox para deplegar informacion
    """
    def cargar_cuadrillas(self):
        """Carga las cuadrillas desde la base de datos al ComboBox"""
        try:
            self.Cuadrillero_comboBox.clear()
            cuadrillas = listar_cuadrillas_comboBox()
            
            for cuadrilla in cuadrillas:
                # Guardamos el ID como dato userData y mostramos el texto formateado
                self.Cuadrillero_comboBox.addItem(
                    f"{cuadrilla.Clave} - {cuadrilla.Responsable}",
                    cuadrilla.id_Cuadrilla  # Esto guarda el ID como dato asociado
                )
        except Exception as e:
            print(f"Error al cargar cuadrillas: {e}")
            QMessageBox.warning(self, "Error", "No se pudieron cargar las cuadrillas")

    # def cargar_cuadrillas_cosecha(self):
    #     """Carga las cuadrillas desde la base de datos al ComboBox Cosecha"""
    #     try:
    #         self.CuadrilleroConfiguracion_comboBox.clear()
    #         cuadrillas = listar_cuadrillas_comboBox()

    #         nombre_recolector = self.NombreCompletoText_lineEdit.text()
            
    #         for cuadrilla in cuadrillas:
    #             # Guardamos el ID como dato userData y mostramos el texto formateado
    #             self.CuadrilleroConfiguracion_comboBox.addItem(
    #                 f"{cuadrilla.Clave}",
    #                 cuadrilla.id_Cuadrilla  # Esto guarda el ID como dato asociado
    #             )
    #     except Exception as e:
    #         print(f"Error al cargar cuadrillas: {e}")
    #         QMessageBox.warning(self, "Error", "No se pudieron cargar las cuadrillas")

    def cargar_cuadrillas_cosecha(self):
        """Carga la cuadrilla del recolector identificado por nombre en el ComboBox"""
        try:
            self.CuadrilleroConfiguracion_comboBox.clear()
            nombre_recolector = self.NombreCompletoText_lbl.text().strip()

            if not nombre_recolector:
                return

            cuadrilla = obtener_cuadrilla_por_nombre(nombre_recolector)

            if cuadrilla:
                # self.CuadrilleroConfiguracion_comboBox.addItem(
                #     cuadrilla.Clave,
                #     cuadrilla.id_Cuadrilla
                # )
                self.CuadrilleroRegistrado_Lbl.setText(
                    cuadrilla.Clave
                )
            else:
                print(f"No se encontró cuadrilla para: {nombre_recolector}")
                QMessageBox.warning(self, "Aviso", f"No se encontró cuadrilla para '{nombre_recolector}'")

        except Exception as e:
            print(f"Error al cargar cuadrilla: {e}")
            QMessageBox.warning(self, "Error", "No se pudo cargar la cuadrilla")


    def cargar_tablas_comboBox_vista(self):
        """Carga clave de tablas desde la base de datos al ComboBox Vista"""
        try:
            self.TablaVista_comboBox.clear()
            tablas = listar_tabla_formulario()
            
            for tabla in tablas:
                # Guardamos el Clave como dato userData y mostramos el texto formateado
                self.TablaVista_comboBox.addItem(
                    f"{tabla.Clave}",
                    userData=tabla.Clave  # Guardamos la clave real como dato asociado
                )
        except Exception as e:
            print(f"Error al cargar tablas: {e}")
            QMessageBox.warning(self, "Error", "No se pudieron cargar las tablas")

    def cargar_macrotuneles_comboBox_vista(self):
        """Carga los macrotuneles según la tabla seleccionada"""
        try:
            clave_tabla = self.TablaVista_comboBox.currentData()
            
            if not clave_tabla:
                return

            self.MacrotunelVista_comboBox.clear()
            macrotuneles = listar_macrotunel_cosecha(clave_tabla)
            
            for macrotunel in macrotuneles:
                self.MacrotunelVista_comboBox.addItem(
                    macrotunel.Clave,
                    userData=macrotunel.id_Macrotunel  # Guardamos el ID como dato
                )
                
        except Exception as e:
            print(f"Error al cargar macrotuneles: {e}")
            QMessageBox.warning(self, "Error", f"No se pudieron cargar los macrotuneles: {str(e)}")
            
    def cargar_tablas_comboBox(self):
        """Carga clave de tablas desde la base de datos al ComboBox Vista"""
        try:
            self.TablaConfiguracion_comboBox.clear()
            tablas = listar_tabla_formulario()
            
            for tabla in tablas:
                # Guardamos el Clave como dato userData y mostramos el texto formateado
                self.TablaConfiguracion_comboBox.addItem(
                    f"{tabla.Clave}",
                    userData=tabla.Clave  # Guardamos la clave real como dato asociado
                )
        except Exception as e:
            print(f"Error al cargar tablas: {e}")
            QMessageBox.warning(self, "Error", "No se pudieron cargar las tablas")


    #####################################################################
    #                 CARGA DATOS COMBOBOXES INICIO COSECHA
    #####################################################################
    def cargar_fases_comboBox_cosecha(self):
        try:
            self.FaseConfiguracion_comboBox.clear()
            fases = listar_fases_cosecha()
            for fase in fases:
                self.FaseConfiguracion_comboBox.addItem(
                    fase.Clave,
                    userData=fase.Clave  # Se pasa la Clave para filtrar tablas
                )
        except Exception as e:
            print(f"Error al cargar fases: {e}")
            QMessageBox.warning(self, "Error", "No se pudieron cargar las fases")


    # def cargar_tablas_comboBox_cosecha(self):
    #     try:
    #         clave_fase = self.FaseConfiguracion_comboBox.currentData()
    #         if not clave_fase:
    #             return

    #         self.TablaConfiguracion_comboBox.clear()
    #         tablas = listar_tabla_cosecha(clave_fase)
    #         for tabla in tablas:
    #             self.TablaConfiguracion_comboBox.addItem(
    #                 tabla.Clave,
    #                 userData=tabla.Clave  # ← Clave, no ID, para filtrar macrotuneles
    #             )
    #     except Exception as e:
    #         print(f"Error al cargar tablas: {e}")
    #         QMessageBox.warning(self, "Error", f"No se pudieron cargar las tablas: {str(e)}")


    # def cargar_macrotuneles_comboBox_cosecha(self):
    #     try:
    #         clave_tabla = self.TablaConfiguracion_comboBox.currentData()
    #         if not clave_tabla:
    #             return

    #         self.MacrotunelConfiguracion_comboBox.clear()
    #         macrotuneles = listar_macrotunel_cosecha(clave_tabla)
    #         for macrotunel in macrotuneles:
    #             self.MacrotunelConfiguracion_comboBox.addItem(
    #                 macrotunel.Clave,
    #                 userData=macrotunel.Clave  # ← Clave, no ID, para filtrar lineas
    #             )
    #     except Exception as e:
    #         print(f"Error al cargar macrotuneles: {e}")
    #         QMessageBox.warning(self, "Error", f"No se pudieron cargar los macrotuneles: {str(e)}")


    # def cargar_linea_comboBox_cosecha(self):
    #     try:
    #         clave_macrotunel = self.MacrotunelConfiguracion_comboBox.currentData()
    #         if not clave_macrotunel:
    #             return

    #         self.LineaConfiguracion_comboBox.clear()
    #         lineas = listar_linea_cosecha(clave_macrotunel)
    #         for linea in lineas:
    #             self.LineaConfiguracion_comboBox.addItem(
    #                 linea.Clave,
    #                 userData=linea.id_Linea  # Aquí sí guardamos el ID (es el dato final)
    #             )
    #     except Exception as e:
    #         print(f"Error al cargar lineas: {e}")
    #         QMessageBox.warning(self, "Error", f"No se pudieron cargar las lineas: {str(e)}")
    def cargar_tablas_comboBox_cosecha(self):
        try:
            clave_fase = self.FaseConfiguracion_comboBox.currentData()
            if not clave_fase:
                self.TablaConfiguracion_comboBox.clear()
                self.MacrotunelConfiguracion_comboBox.clear()
                self.LineaConfiguracion_comboBox.clear()
                return

            self.TablaConfiguracion_comboBox.clear()
            tablas = listar_tabla_cosecha(clave_fase)

            if not tablas:  # 👈 Si no hay tablas, limpiar todo lo de abajo
                self.MacrotunelConfiguracion_comboBox.clear()
                self.LineaConfiguracion_comboBox.clear()
                return

            for tabla in tablas:
                self.TablaConfiguracion_comboBox.addItem(tabla.Clave, userData=tabla.Clave)
        except Exception as e:
            print(f"Error al cargar tablas: {e}")
            QMessageBox.warning(self, "Error", f"No se pudieron cargar las tablas: {str(e)}")


    def cargar_macrotuneles_comboBox_cosecha(self):
        try:
            clave_tabla = self.TablaConfiguracion_comboBox.currentData()
            if not clave_tabla:
                self.MacrotunelConfiguracion_comboBox.clear()
                self.LineaConfiguracion_comboBox.clear()  # 👈 Limpiar lineas también
                return

            self.MacrotunelConfiguracion_comboBox.clear()
            macrotuneles = listar_macrotunel_cosecha(clave_tabla)

            if not macrotuneles:  # 👈 Si no hay macrotuneles, limpiar lineas
                self.LineaConfiguracion_comboBox.clear()
                return

            for macrotunel in macrotuneles:
                self.MacrotunelConfiguracion_comboBox.addItem(macrotunel.Clave, userData=macrotunel.Clave)
        except Exception as e:
            print(f"Error al cargar macrotuneles: {e}")
            QMessageBox.warning(self, "Error", f"No se pudieron cargar los macrotuneles: {str(e)}")


    def cargar_linea_comboBox_cosecha(self):
        try:
            clave_macrotunel = self.MacrotunelConfiguracion_comboBox.currentData()
            if not clave_macrotunel:
                self.LineaConfiguracion_comboBox.clear()  # 👈
                return

            self.LineaConfiguracion_comboBox.clear()
            lineas = listar_linea_cosecha(clave_macrotunel)
            for linea in lineas:
                self.LineaConfiguracion_comboBox.addItem(linea.Clave, userData=linea.id_Linea)
        except Exception as e:
            print(f"Error al cargar lineas: {e}")
            QMessageBox.warning(self, "Error", f"No se pudieron cargar las lineas: {str(e)}")

    # def cargar_modalidades_comboBox_cosecha(self):
    #     modalidad_controlador = ModalidadControlador()
    #     modalidades = modalidad_controlador.obtener_modalidades()
    #     self.ModalidadConfiguracion_comboBox.clear()
    #     for modalidad in modalidades:
    #         self.ModalidadConfiguracion_comboBox.addItem(modalidad.Clave, userData=modalidad.id_Modalidad)

    def cargar_modalidades_comboBox_cosecha(self, name: str = ""):
        modalidad_controlador = ModalidadControlador()

        # Cargar todas las modalidades
        modalidades = modalidad_controlador.obtener_modalidades()
        self.ModalidadConfiguracion_comboBox.clear()
        for modalidad in modalidades:
            self.ModalidadConfiguracion_comboBox.addItem(modalidad.Clave, userData=modalidad.id_Modalidad)

        # Si viene un name del face recognition, buscar su check de hoy
        if name:
            clave_check, id_modalidad_check = modalidad_controlador.obtener_modalidad_por_recolector_hoy(name)

            if id_modalidad_check is not None:
                # Buscar el índice en el comboBox que coincida con ese id_Modalidad
                for i in range(self.ModalidadConfiguracion_comboBox.count()):
                    if self.ModalidadConfiguracion_comboBox.itemData(i) == id_modalidad_check:
                        self.ModalidadConfiguracion_comboBox.setCurrentIndex(i)
                        break

    #####################################################################
    #                 CARGA DATOS COMBOBOXES VISTA
    #####################################################################
    def cargar_fases_vista_comboBox(self):
        try:
            self.FaseVista_comboBox.clear()
            fases = listar_fases_cosecha()
            for fase in fases:
                self.FaseVista_comboBox.addItem(
                    fase.Clave,
                    userData=fase.Clave  # Se pasa la Clave para filtrar tablas
                )
        except Exception as e:
            print(f"Error al cargar fases de vista: {e}")
            QMessageBox.warning(self, "Error", "No se pudieron cargar las fases de vista")


    def cargar_tablas_vista_comboBox(self):
        try:
            clave_fase = self.FaseVista_comboBox.currentData()
            if not clave_fase:
                return

            self.TablaVista_comboBox.clear()
            tablas = listar_tabla_cosecha(clave_fase)
            for tabla in tablas:
                self.TablaVista_comboBox.addItem(
                    tabla.Clave,
                    userData=tabla.Clave  # ← Clave, no ID, para filtrar macrotuneles
                )
        except Exception as e:
            print(f"Error al cargar tablas de vista: {e}")
            QMessageBox.warning(self, "Error", f"No se pudieron cargar las tablas de vista: {str(e)}")


    def cargar_macrotuneles_vista_comboBox(self):
        try:
            clave_tabla = self.TablaVista_comboBox.currentData()
            if not clave_tabla:
                return

            self.MacrotunelVista_comboBox.clear()
            macrotuneles = listar_macrotunel_cosecha(clave_tabla)
            for macrotunel in macrotuneles:
                self.MacrotunelVista_comboBox.addItem(
                    macrotunel.Clave,
                    userData=macrotunel.Clave  # ← Clave, no ID, para filtrar lineas
                )
        except Exception as e:
            print(f"Error al cargar macrotuneles de vista: {e}")
            QMessageBox.warning(self, "Error", f"No se pudieron cargar los macrotuneles de vista: {str(e)}")


    def cargar_linea_vista_comboBox(self):
        try:
            clave_macrotunel = self.MacrotunelVista_comboBox.currentData()
            if not clave_macrotunel:
                return

            self.LineaVista_comboBox.clear()
            lineas = listar_linea_cosecha(clave_macrotunel)
            for linea in lineas:
                self.LineaVista_comboBox.addItem(
                    linea.Clave,
                    userData=linea.id_Linea  # Aquí sí guardamos el ID (es el dato final)
                )
        except Exception as e:
            print(f"Error al cargar lineas e vista: {e}")
            QMessageBox.warning(self, "Error", f"No se pudieron cargar las lineas de vista: {str(e)}")

    def limpiar_filtros_vista(self):
        self.NombreRecolectorVista_lineEdit.clear()
        self.FaseVista_comboBox.clear()
        self.TablaVista_comboBox.clear()
        self.MacrotunelVista_comboBox.clear()
        self.LineaVista_comboBox.clear()

    # #####################################################################
    # #                 CARGA DATOS COMBOBOXES INICIO COSECHA
    # #####################################################################
    # def cargar_fases_comboBox_cosecha(self):
    #     """Carga clave de fases desde la base de datos al ComboBox Fase"""
    #     try:
    #         self.FaseConfiguracion_comboBox.clear()
    #         fases = listar_fases_cosecha()
            
    #         for fase in fases:
    #             # Guardamos el Clave como dato userData y mostramos el texto formateado
    #             self.FaseConfiguracion_comboBox.addItem(
    #                 f"{fase.Clave}",
    #                 userData=fase.Clave  # Guardamos la clave real como dato asociado
    #             )
    #     except Exception as e:
    #         print(f"Error al cargar fases: {e}")
    #         QMessageBox.warning(self, "Error", "No se pudieron cargar las fases")



    # def cargar_tablas_comboBox_cosecha(self):
    #     """Carga las tablas según la fase seleccionada"""
    #     try:
    #         clave_fase = self.FaseConfiguracion_comboBox.currentData()
            
    #         if not clave_fase:
    #             return

    #         self.TablaConfiguracion_comboBox.clear()
    #         tablas = listar_tabla_cosecha(clave_fase)
            
    #         for tabla in tablas:
    #             self.TablaConfiguracion_comboBox.addItem(
    #                 tabla.Clave,
    #                 userData=tabla.id_Tabla  # Guardamos el ID como dato
    #             )
                
    #     except Exception as e:
    #         print(f"Error al cargar tablas: {e}")
    #         QMessageBox.warning(self, "Error", f"No se pudieron cargar las tablas: {str(e)}")


    # def cargar_macrotuneles_comboBox_cosecha(self):
    #     """Carga los macrotuneles según la tabla seleccionada"""
    #     try:
    #         clave_tabla = self.TablaConfiguracion_comboBox.currentData()
            
    #         if not clave_tabla:
    #             return

    #         self.MacrotunelConfiguracion_comboBox.clear()
    #         macrotuneles = listar_macrotunel_cosecha(clave_tabla)
            
    #         for macrotunel in macrotuneles:
    #             self.MacrotunelConfiguracion_comboBox.addItem(
    #                 macrotunel.Clave,
    #                 userData=macrotunel.id_Macrotunel  # Guardamos el ID como dato
    #             )
                
    #     except Exception as e:
    #         print(f"Error al cargar macrotuneles: {e}")
    #         QMessageBox.warning(self, "Error", f"No se pudieron cargar los macrotuneles: {str(e)}")

    # def cargar_linea_comboBox_cosecha(self):
    #     """Carga las lineas según el macrotunel seleccionado"""
    #     try:
    #         clave_macrotunel = self.MacrotunelConfiguracion_comboBox.currentData()
            
    #         if not clave_macrotunel:
    #             return

    #         self.LineaConfiguracion_comboBox.clear()
    #         lineas = listar_linea_cosecha(clave_macrotunel)
            
    #         for linea in lineas:
    #             self.LineaConfiguracion_comboBox.addItem(
    #                 linea.Clave,
    #                 userData=linea.id_Linea  # Guardamos el ID como dato
    #             )
                
    #     except Exception as e:
    #         print(f"Error al cargar macrotuneles: {e}")
    #         QMessageBox.warning(self, "Error", f"No se pudieron cargar los macrotuneles: {str(e)}")


    def cargar_cuadrillas_actualizar_comboBox(self):
        """Carga las cuadrillas desde la base de datos al ComboBox"""
        try:
            self.ActualizarCuadrillero_comboBox.clear()
            nombre = self.ActualizarNombre_lineEdit.text()
            cuadrillero_actual = obtener_clave_cuadrillero(nombre)
            cuadrillas_actualizar = listar_cuadrillas_comboBox()

            # Primero agregar la cuadrilla actual
            for cuadrilla in cuadrillas_actualizar:
                if cuadrilla.Clave == cuadrillero_actual:
                    self.ActualizarCuadrillero_comboBox.insertItem(
                        0,
                        f"{cuadrilla.Clave} - {cuadrilla.Responsable}",
                        cuadrilla.id_Cuadrilla
                    )
                    break

            # Luego agregar el resto
            for cuadrilla in cuadrillas_actualizar:
                if cuadrilla.Clave != cuadrillero_actual:
                    self.ActualizarCuadrillero_comboBox.addItem(
                        f"{cuadrilla.Clave} - {cuadrilla.Responsable}",
                        cuadrilla.id_Cuadrilla
                    )
        except Exception as e:
            print(f"Error al cargar cuadrillas: {e}")
            QMessageBox.warning(self, "Error", "No se pudieron cargar las cuadrillas")


    def cargar_tablas_creacion_comboBox(self):
        """Carga las tablas desde la base de datos al ComboBox"""
        try:
            self.CrearTablaAsociadaDeMacrotunel_comboBox.clear()
            tablas = listar_tabla_formulario()
            
            for tabla in tablas:
                # Guardamos el ID como dato userData y mostramos el texto formateado
                self.CrearTablaAsociadaDeMacrotunel_comboBox.addItem(
                    f"{tabla.Clave}",
                    tabla.id_Tabla  # Esto guarda el ID como dato asociado
                )
        except Exception as e:
            print(f"Error al cargar tablas: {e}")
            QMessageBox.warning(self, "Error", "No se pudieron cargar las tablas")

    def cargar_tablas_actualizacion_comboBox(self):
        """Carga las tablas desde la base de datos al ComboBox"""
        try:
            self.ActualizarTablaAsociadaDeMacrotunel_comboBox.clear()
            tablas = listar_tabla_formulario()
            
            for tabla in tablas:
                # Guardamos el ID como dato userData y mostramos el texto formateado
                self.ActualizarTablaAsociadaDeMacrotunel_comboBox.addItem(
                    f"{tabla.Clave}",
                    tabla.id_Tabla  # Esto guarda el ID como dato asociado
                )
        except Exception as e:
            print(f"Error al cargar tablas: {e}")
            QMessageBox.warning(self, "Error", "No se pudieron cargar las tablas")


    """***************************************************************************************"""
    def mostrar_cuadrillas_en_tabla(self):
        """Carga los datos de cuadrillas en la tabla"""
        #from controlador.cuadrilleros import listar_cuadrillas
        try:
            cuadrillas = listar_cuadrillas()
            self.Cuadrilleros_tableWidget.setRowCount(len(cuadrillas))
            
            for row, cuadrilla in enumerate(cuadrillas):
                # ID (no editable)
                id_item = QTableWidgetItem(str(cuadrilla.id_Cuadrilla))
                id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.Cuadrilleros_tableWidget.setItem(row, 0, id_item)
                
                # Resto de campos
                self.Cuadrilleros_tableWidget.setItem(row, 1, QTableWidgetItem(cuadrilla.Clave))
                self.Cuadrilleros_tableWidget.setItem(row, 2, QTableWidgetItem(cuadrilla.Responsable or ""))
                self.Cuadrilleros_tableWidget.setItem(row, 3, QTableWidgetItem(cuadrilla.Localidad or ""))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar las cuadrillas:\n{str(e)}")
            

    def ActualizarColector(self):
        """Muestra el diálogo para actualizar una colector"""
        selected_row_colector = self.Colectores_tableWidget.currentRow()
        
        if selected_row_colector < 0:
            QMessageBox.warning(self, "Advertencia", "Por favor seleccione un colector para editar")
            return
        self.stackedWidget_Colector.setCurrentIndex(1)

        # Obtener datos actuales de la fila seleccionada
        self.id_recolector = self.Colectores_tableWidget.item(selected_row_colector, 0).text()
        nombre_completo = self.Colectores_tableWidget.item(selected_row_colector, 1).text()
        localidad_colector = self.Colectores_tableWidget.item(selected_row_colector, 2).text()
        telefono_colector = self.Colectores_tableWidget.item(selected_row_colector, 4).text()

        self.Id_Colector_Lbl.setText(self.id_recolector)
        self.ActualizarNombre_lineEdit.setText(nombre_completo)
        self.ActualizarComunidad_lineEdit.setText(localidad_colector)
        self.ActualizarTelefono_lineEdit.setText(telefono_colector)

        self.cargar_cuadrillas_actualizar_comboBox()

        self.CamaraConfig_RostroActualizado()
        self.stackedWidget_TomarFotoActualizada.setCurrentIndex(0)


        id_cuadrillero_combobox = self.ActualizarCuadrillero_comboBox.currentText()
        if not id_cuadrillero_combobox:
            QMessageBox.warning(self, "Advertencia", "No se ha seleccionado ningún cuadrillero")
            return

    def apagar_camara_atualizar(self):
        # Verificar y liberar la cámara solo si está abierta
        if hasattr(self, 'cap_actualizar') and self.cap_actualizar is not None:
            if self.cap_actualizar.isOpened():
                self.cap_actualizar.release()
            self.cap_actualizar = None  # Eliminar referencia

        # Detener el temporizador si está activo
        if hasattr(self, 'timer_registroActualizar') and self.timer_registroActualizar.isActive():
            self.timer_registroActualizar.stop()

    def Back_ActualizarColector(self):
        self.apagar_camara_atualizar()
        self.limpiar_foto_actualizada()
        self.stackedWidget_Colector.setCurrentIndex(2)

    def ConfirmarColectorActualizado(self):
        try:
            nombre_completo = self.ActualizarNombre_lineEdit.text() 
            localidad = self.ActualizarComunidad_lineEdit.text()
            telefono = self.ActualizarTelefono_lineEdit.text()
            
            # Obtener el ID de la cuadrilla seleccionada (no el texto)
            id_Cuadrilla = self.ActualizarCuadrillero_comboBox.currentData()
            
            if not all([nombre_completo, localidad, telefono]):
                QMessageBox.warning(self, "Advertencia", "Nombre, localidad y teléfono son obligatorios")
                return
            
            if actualizar_colector(
                id_Recolector=self.id_recolector,
                nombre_completo=nombre_completo,
                localidad=localidad,
                telefono=telefono,
                id_cuadrilla=id_Cuadrilla  # Ahora es el ID numérico
            ):
                QMessageBox.information(self, "Éxito", "Colector actualizado correctamente")
                self.apagar_camara_atualizar()
                self.mostrar_recolectores_en_tabla()
                self.stackedWidget_Colector.setCurrentIndex(2)
            else:
                QMessageBox.warning(self, "Error", "No se pudo actualizar el colector")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error: {str(e)}")


    def ConfirmarNuevoCuadrillero(self):
        clave = self.CrearCuadrilleroClave_lineEdit.text()
        responsable = self.CrearCuadrilleroResponsable_lineEdit.text()
        localidad = self.CrearCuadrilleroLocalidad_lineEdit.text()

        if clave.strip() and responsable.strip() and localidad.strip():
            crear_cuadrilla(clave, responsable, localidad)
            QMessageBox.information(self, "Éxito", "Cuadrillero registrado exitosamente.")
            self.CrearCuadrilleroClave_lineEdit.clear()
            self.CrearCuadrilleroResponsable_lineEdit.clear()
            self.CrearCuadrilleroLocalidad_lineEdit.clear()
            self.mostrar_cuadrillas_en_tabla()  # Refrescar la tabla
            self.stackedWidget_Cuadrilleros.setCurrentIndex(0)  # Volver a la lista
        else:
            QMessageBox.warning(self, "Error", "Por favor, ingrese el ID y el nombre del modelo.")
     

    def ActualizarCuadrillero(self):
        """Muestra el diálogo para actualizar una cuadrilla"""
        selected_row_cuadrillero = self.Cuadrilleros_tableWidget.currentRow()
        
        if selected_row_cuadrillero < 0:
            QMessageBox.warning(self, "Advertencia", "Por favor seleccione una cuadrilla para editar")
            return
        
        self.stackedWidget_Cuadrilleros.setCurrentIndex(2) # Navega a pantalla para actualizar cuadrilleros
        
        # Obtener datos actuales de la fila seleccionada
        self.id_cuadrilla = self.Cuadrilleros_tableWidget.item(selected_row_cuadrillero, 0).text()  # Guardamos como atributo
        clave = self.Cuadrilleros_tableWidget.item(selected_row_cuadrillero, 1).text()
        responsable = self.Cuadrilleros_tableWidget.item(selected_row_cuadrillero, 2).text()
        localidad = self.Cuadrilleros_tableWidget.item(selected_row_cuadrillero, 3).text()

        # self.Id_Cuadrillero_Lbl.setText(self.id_cuadrilla)
        self.Id_Cuadrillero_Lbl.setText(clave)
        self.ActualizarClave_lineEdit.setText(clave)
        self.ActualizarResponsable_lineEdit.setText(responsable)
        self.ActualizarLocalidad_lineEdit.setText(localidad)

    def ConfirmarCuadrilleroActualizado(self):
        """Confirma la actualización de los datos del cuadrillero"""
        try:
            # Obtenemos los valores actuales de los QLineEdit
            clave = self.ActualizarClave_lineEdit.text()
            responsable = self.ActualizarResponsable_lineEdit.text()
            localidad = self.ActualizarLocalidad_lineEdit.text()
            
            # Verificamos que los campos no estén vacíos
            if not all([clave, responsable, localidad]):
                QMessageBox.warning(self, "Advertencia", "Todos los campos son obligatorios")
                return
                
            # Llamamos a la función de actualización
            if actualizar_cuadrilla(
                int(self.id_cuadrilla),  # Usamos el atributo guardado
                clave,
                responsable,
                localidad
            ):
                QMessageBox.information(self, "Éxito", "Cuadrilla actualizada correctamente")
                self.mostrar_cuadrillas_en_tabla()  # Refrescar la tabla
                self.stackedWidget_Cuadrilleros.setCurrentIndex(0)  # Volver a la lista
            else:
                QMessageBox.warning(self, "Error", "No se pudo actualizar la cuadrilla")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error: {str(e)}")

    def CancelarCuadrilleroActualizado(self):
        self.stackedWidget_Cuadrilleros.setCurrentIndex(0)

    def EliminarCuadrillero(self):
        """Slot para el botón de eliminar cuadrilla"""
        selected_items = self.Cuadrilleros_tableWidget.selectedItems()
        
        if not selected_items:
            QMessageBox.warning(self, "Advertencia", "Por favor seleccione una cuadrilla para eliminar")
            return
        
        selected_rows = {item.row() for item in selected_items}
        
        if len(selected_rows) > 1:
            QMessageBox.warning(self, "Advertencia", "Por favor seleccione solo una cuadrilla para eliminar")
            return
        
        row = selected_rows.pop()
        id_cuadrilla = int(self.Cuadrilleros_tableWidget.item(row, 0).text())
        clave = self.Cuadrilleros_tableWidget.item(row, 1).text()
        
        # Verificar si la cuadrilla tiene recolectores asociados
        from controlador.cuadrilleros import get_db, Recolector
        db = get_db()
        try:
            tiene_recolectores = db.query(Recolector).filter_by(id_Cuadrilla=id_cuadrilla).first() is not None
            if tiene_recolectores:
                QMessageBox.warning(
                    self, "No se puede eliminar",
                    "Esta cuadrilla tiene recolectores asociados. Asigne estos recolectores a otra cuadrilla primero."
                )
                return
        finally:
            db.close()
        
        confirmacion = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Está seguro que desea eliminar la cuadrilla {clave}?\nEsta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if confirmacion == QMessageBox.StandardButton.Yes:
            from controlador.cuadrilleros import eliminar_cuadrilla
            if eliminar_cuadrilla(id_cuadrilla):
                QMessageBox.information(self, "Éxito", "Cuadrilla eliminada correctamente")
                self.mostrar_cuadrillas_en_tabla()  # Refrescar la tabla
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar la cuadrilla")

    def EliminarColector(self):
        """Slot para el botón de eliminar colector"""
        selected_items = self.Colectores_tableWidget.selectedItems()
        
        if not selected_items:
            QMessageBox.warning(self, "Advertencia", "Por favor seleccione un colector para eliminar")
            return
        
        selected_rows = {item.row() for item in selected_items}
        
        if len(selected_rows) > 1:
            QMessageBox.warning(self, "Advertencia", "Por favor seleccione solo una cuadrilla para eliminar")
            return
        
        row = selected_rows.pop()
        id_colector = int(self.Colectores_tableWidget.item(row, 0).text())
        nombre = self.Colectores_tableWidget.item(row, 1).text()
        
        confirmacion = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Está seguro que desea eliminar el colector {nombre}?\nEsta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if confirmacion == QMessageBox.StandardButton.Yes:
    
            if eliminar_colector(id_colector):
                QMessageBox.information(self, "Éxito", "Colector eliminado correctamente")
                self.mostrar_recolectores_en_tabla()  # Refrescar la tabla
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar la cuadrilla")

    # def GenerarArchivo(self):
    #     """Exporta los datos de Vista_tableWidget a Excel en USB"""
    #     from controlador.excel_generator import ExcelGenerator, ExcelGeneratorSabana
        
    #     # Elimina las comas al final de estas líneas
    #     fecha_inicio = self.Inicio_calendarWidget.selectedDate().toString("yyyy-MM-dd")
    #     fecha_fin = self.Fin_calendarWidget.selectedDate().toString("yyyy-MM-dd")

    #     try:
    #         ExcelGenerator.save_to_excel(self.Vista_tableWidget)
    #         # reportes = ReportesMemoria()
    #         # df_sabana = reportes.resumen_cuadrillero_recolectores(fecha_inicio, fecha_fin)

    #         # generador_resumen = ExcelGeneratorSabana()
    #         # generador_resumen.exportar_sabana_por_cuadrillero(df_sabana, fecha_inicio, fecha_fin, self)
                
    #     except Exception as e:
    #         QMessageBox.critical(self, "Error", f"Error al generar archivo: {str(e)}")
    #         print(f"Error: {str(e)}")

    def GenerarArchivo(self):
        """Exporta los datos de Vista_tableWidget a Excel en USB"""
        from controlador.excel_generator import ExcelGenerator, ExcelGeneratorSabana
        
        fecha_inicio = self.Inicio_calendarWidget.selectedDate().toString("yyyy-MM-dd")
        fecha_fin = self.Fin_calendarWidget.selectedDate().toString("yyyy-MM-dd")

        try:
            ExcelGenerator.save_to_excel(self.Vista_tableWidget)

            # Expulsar USB automáticamente
            self.expulsar_usb("E")

            # reportes = ReportesMemoria()
            # df_sabana = reportes.resumen_cuadrillero_recolectores(fecha_inicio, fecha_fin)

            # generador_resumen = ExcelGeneratorSabana()
            # generador_resumen.exportar_sabana_por_cuadrillero(df_sabana, fecha_inicio, fecha_fin, self)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al generar archivo: {str(e)}")
            print(f"Error: {str(e)}")

    def expulsar_usb(self, letra_unidad="E"):
        """
        Expulsa de forma segura una memoria USB en Windows.
        """

        try:
            # Esperar un poco para asegurar que Excel terminó de escribir
            time.sleep(2)

            comando = f'''
            $driveEject = New-Object -comObject Shell.Application
            $driveEject.Namespace(17).ParseName("{letra_unidad}:").InvokeVerb("Eject")
            '''

            subprocess.run(
                ["powershell", "-Command", comando],
                capture_output=True,
                text=True
            )

            QMessageBox.information(
                self,
                "USB expulsada",
                f"La unidad {letra_unidad}: puede retirarse de forma segura."
            )

        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"No se pudo expulsar la USB:\n{str(e)}"
            )

    def ActivarTeclas(self, checked):        
        if checked:
            desbloquear_teclas = QMessageBox.question(self, 'Advertencia', 
                                            '¿Seguro que quieres bloquear las teclas?',
                                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if desbloquear_teclas == QMessageBox.StandardButton.Yes:
                self.desbloquear_teclas()
                print("Teclas DESBLOQUEADAS")
            else:
                return
        else:
            bloquear_teclas = QMessageBox.question(self, 'Advertencia', 
                                            '¿Seguro que quieres activar las teclas?',
                                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if bloquear_teclas == QMessageBox.StandardButton.Yes:
                self.bloquear_teclas()
                print("Teclas BLOQUEADAS")
            else:
                return

    def bloquear_teclas(self):
            keyboard.unhook_all()

            # # ALT
            keyboard.block_key("alt")

            # # TAB
            keyboard.block_key("tab")

            # ESC
            keyboard.block_key("esc")

            keyboard.block_key("windows")

            # WINDOWS
            keyboard.add_hotkey(
                "left windows",
                lambda: None,
                suppress=True
            )

            keyboard.add_hotkey(
                "right windows",
                lambda: None,
                suppress=True
            )

            # Combinaciones
            combinaciones = [
                "alt+tab",
                "alt+f4",
                "ctrl+esc","windows",
                "windows+d",
                "windows+e",
                "windows+r",
                "windows+l",
                "windows+tab"
            ]

            for combo in combinaciones:
                keyboard.add_hotkey(
                    combo,
                    lambda: None,
                    suppress=True
                )

            self.teclas_bloqueadas = True


            print("Bloqueo ACTIVADO")


    def desbloquear_teclas(self):

        keyboard.unhook_all()

        self.teclas_bloqueadas = False

        # # Cambiar estilo del botón
        # self.ActivarTeclas_Btn.setStyleSheet("""
        #     QToolButton {
        #         background-color: #228B22;
        #         color: white;
        #         border-radius: 25px;
        #         padding: 10px;
        #         border: 2px solid white;
        #         font-family: "Segoe UI";
        #         font-size: 22px;
        #         font-weight: 650;
        #     }
        # """)

        print("Bloqueo DESACTIVADO")

    def ImprimirCorte(self):
        """Imprime el reporte de corte del día en formato legible"""
        resultados = Obtener_Corte_Dia()
        fecha_actual = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        
        # # Crear instancia del impresor de tickets e imprimir
        printer = TicketPrinter()
        printer.print_corte_dia(
            fecha=fecha_actual,
            resultados=resultados
        )

        print("\nBERRIES LEON - CORTE DEL DIA")
        print(f"Fecha: {fecha_actual}")
        print("-"*60)
        print("{:<20} | {:>10} | {:>10} | {:>10} | {:>10} | {:>10}".format(
            "Nombre", "T. Vueltas", "T. Peso Kg.", "T. Buenas", "T. Regulares", "T. Malas"))
        print("-"*60)

        if resultados:
            for row in resultados:
                print("{:<20} | {:>10} | {:>10.3f} | {:>10} | {:>10} | {:>10}".format(
                    row[0], row[1], row[2], row[3], row[4], row[5]))
        else:
            print("No hay registros de cosecha para el día de hoy")
        
        print("-"*60)

    def FechaFinActivar(self):
        # current_state = self.Fin_calendarWidget.isEnabled()
        # self.Fin_calendarWidget.setEnabled(not current_state)
        # self.Fin_calendarWidget.setVisible(not current_state)
        
        # # Opcional: Resetear la fecha de fin cuando se desactiva
        # if not current_state:
        #     self.Fin_calendarWidget.setSelectedDate(self.Inicio_calendarWidget.selectedDate())
        pass

    def FechaInicioActivar(self):
        # current_state = self.Inicio_calendarWidget.isEnabled()
        # self.Inicio_calendarWidget.setEnabled(not current_state)
        # self.Inicio_calendarWidget.setVisible(not current_state)
        
        # Opcional: Resetear la fecha de fin cuando se desactiva
        # if not current_state:
        #     self.Inicio_calendarWidget.setSelectedDate(self.Inicio_calendarWidget.selectedDate())
        pass

    def Back_GenerarSabana(self):
        self.stackedWidget_Principal.setCurrentIndex(0)
        self.limpiar_filtros_vista()

    def ShowGenerarSabana(self):
        self.deshabilitar_modulos()
        key, ok = QInputDialog.getText(
            self,
            "Modulo de Resumen",
            "Ingrese la clave de acceso:",
            QLineEdit.EchoMode.Password
        )

        if not ok:
            self.habilitar_modulos()
            return  # Canceló el usuario

        key = key.strip()

        if key == "":
            QMessageBox.warning(self, "Error", "No ingresaste ninguna clave")
            self.habilitar_modulos()
            return

        acceso = KeysAcceso()

        if acceso.key_acceso_modulo(key):
            self.stackedWidget_Principal.setCurrentIndex(6)
            self.VistaHoy()
            self.actualizar_vista()
            self.habilitar_modulos()
        else:
            QMessageBox.warning(self, "Acceso Denegado", "Clave incorrecta")
            self.habilitar_modulos()


    def ShowTablaMenu(self):
        self.stackedWidget_Principal.setCurrentIndex(4)
        self.stackedWidget_Tabla.setCurrentIndex(0)
        self.mostrar_tablas_en_tabla()

    def ShowMacrotunelMenu(self):
        self.stackedWidget_Principal.setCurrentIndex(5)
        self.stackedWidget_Macrotunel.setCurrentIndex(0)
        self.mostrar_macrotuneles_en_tabla()

    def ShowFaseMenu(self):
        self.stackedWidget_Principal.setCurrentIndex(9)
        self.stackedWidget_Fase.setCurrentIndex(0)
        # self.mostrar_macrotuneles_en_tabla()
        pass

    def ShowLineaMenu(self):
        self.stackedWidget_Principal.setCurrentIndex(10)
        self.stackedWidget_Linea.setCurrentIndex(0)
        self.mostrar_lineas_en_tabla()
        
    def ShowCrearFase(self):
        self.stackedWidget_Fase.setCurrentIndex(1)
        self.CrearClaveFase_lineEdit.setText("F")

    def ShowActualizarFase(self):
        self.stackedWidget_Fase.setCurrentIndex(2)

    def Back_CrearFase(self):
        self.stackedWidget_Fase.setCurrentIndex(0)

    def Back_ActualizarFase(self):
        self.stackedWidget_Fase.setCurrentIndex(0)



    def Back_CrearLinea(self):
        self.stackedWidget_Linea.setCurrentIndex(0)

    def Back_ActualizarLinea(self):
        self.stackedWidget_Linea.setCurrentIndex(0)



    def proteger_clave(self, clave:str, lineEdit):
        """Protege los primeros caracteres en un QLineEdit"""
        current_text = lineEdit.text()
        
        if not current_text.startswith(clave):
            lineEdit.blockSignals(True)  # Evitar recursión
            # Restauramos el prefijo y mantenemos el resto del texto
            new_text = clave + (current_text[len(clave):] if len(current_text) >= len(clave) else "")
            lineEdit.setText(new_text)
            lineEdit.blockSignals(False)
            # Mover el cursor al final
            lineEdit.setCursorPosition(len(lineEdit.text()))


    # def proteger_clave_Tabla(self, lineEdit):
    #     """Protege los primeros dos caracteres 'T-' en un QLineEdit"""
    #     current_text = lineEdit.text()
        
    #     if not current_text.startswith("T-"):
    #         lineEdit.blockSignals(True)  # Evitar recursión
    #         # Restauramos el prefijo y mantenemos el resto del texto
    #         new_text = "T-" + (current_text[2:] if len(current_text) >= 2 else "")
    #         lineEdit.setText(new_text)
    #         lineEdit.blockSignals(False)
    #         # Mover el cursor al final
    #         lineEdit.setCursorPosition(len(lineEdit.text()))

    # def proteger_clave_Macrotunel(self, lineEdit):
    #     """Protege los primeros tres caracteres 'MT-' en un QLineEdit"""
    #     current_text = lineEdit.text()
        
    #     if not current_text.startswith("MT-"):
    #         lineEdit.blockSignals(True)  # Evitar recursión
    #         # Restauramos el prefijo y mantenemos el resto del texto
    #         new_text = "MT-" + (current_text[3:] if len(current_text) >= 3 else "")
    #         lineEdit.setText(new_text)
    #         lineEdit.blockSignals(False)
    #         # Mover el cursor al final
    #         lineEdit.setCursorPosition(len(lineEdit.text()))

    # def proteger_clave_Cuadrillero(self, lineEdit):
    #     """Protege los primeros dos caracteres 'C-' en un QLineEdit"""
    #     current_text = lineEdit.text()
        
    #     if not current_text.startswith("C-"):
    #         lineEdit.blockSignals(True)  # Evitar recursión
    #         # Restauramos el prefijo y mantenemos el resto del texto
    #         new_text = "C-" + (current_text[2:] if len(current_text) >= 2 else "")
    #         lineEdit.setText(new_text)
    #         lineEdit.blockSignals(False)
    #         # Mover el cursor al final
    #         lineEdit.setCursorPosition(len(lineEdit.text()))
    
    #####################################################################
    #                           CRUD FASE
    #####################################################################
    def ConfirmarCreacionFase(self):
        clave = self.CrearClaveFase_lineEdit.text()
        ubicacion = self.CrearUbicacionFase_lineEdit.text()
        nombre = self.CrearNombreFase_lineEdit.text()

        if clave.strip() and ubicacion.strip() and nombre.strip():
            try:
                # insertar valores
                crear_fase(clave, ubicacion, nombre)
                # mensaje de confirmacion
                QMessageBox.information(self, "Éxito", "Tabla Fase insertada exitosamente.")
                # limpiar line edits
                self.CrearClaveFase_lineEdit.clear()
                self.CrearUbicacionFase_lineEdit.clear()
                self.CrearNombreFase_lineEdit.clear()
                self.mostrar_fases_en_tabla()
                # volver a tabla
                self.stackedWidget_Fase.setCurrentIndex(0)

            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear la tabla: {str(e)}")
        else:
            QMessageBox.warning(self, "Error", "Todos los campos son obligatorios")

    def ConfirmarActualizarFase(self):
        self.id_fase = int(self.id_fase)
        clave = self.ActualizarClaveFase_lineEdit.text()
        ubicacion = self.ActualizarUbicacionFase_lineEdit.text()
        nombre = self.ActualizarNombreFase_lineEdit.text()

        if not all([clave, ubicacion, nombre]):
                QMessageBox.warning(self, "Advertencia", "Todos los campos son obligatorios")
                return

        # insertar valores
        if actualizar_fase(self.id_fase, clave, ubicacion, nombre):
            # mensaje de confirmacion
            QMessageBox.information(self, "Éxito", "Tabla Fase actualizada exitosamente.")
            # limpiar line edits
            self.ActualizarClaveFase_lineEdit.clear()
            self.ActualizarUbicacionFase_lineEdit.clear()
            self.ActualizarNombreFase_lineEdit.clear()
            # volver a tabla
            self.stackedWidget_Fase.setCurrentIndex(0)
            self.mostrar_fases_en_tabla()

        else:
            QMessageBox.warning(self, "Error", "Todos los campos son obligatorios")

    def ActualizarFase(self):
        """Muestra el diálogo para actualizar una tabla"""
        try:
            selected_items = self.Fase_tableWidget.selectedItems()
            
            if not selected_items:
                QMessageBox.warning(self, "Advertencia", "Por favor seleccione una fase para editar")
                return
            
            selected_row_fase = selected_items[0].row()
            
            # Verificar que todas las celdas necesarias existen
            required_columns = 4  # id, clave, ubicación, nombre
            for col in range(required_columns):
                item = self.Fase_tableWidget.item(selected_row_fase, col)
                if item is None or item.text().strip() == "":
                    QMessageBox.warning(self, "Error", f"Datos incompletos en la fila seleccionada (columna {col})")
                    return

            # Obtener datos
            self.id_fase = self.Fase_tableWidget.item(selected_row_fase, 0).text()
            clave = self.Fase_tableWidget.item(selected_row_fase, 1).text()
            ubicacion = self.Fase_tableWidget.item(selected_row_fase, 2).text()
            nombre = self.Fase_tableWidget.item(selected_row_fase, 3).text()

            # Mostrar en el formulario de edición
            self.stackedWidget_Fase.setCurrentIndex(2)
            self.idFase_Lbl.setText(clave)
            self.ActualizarClaveFase_lineEdit.setText(clave)
            self.ActualizarUbicacionFase_lineEdit.setText(ubicacion)
            self.ActualizarNombreFase_lineEdit.setText(nombre)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar datos para editar: {str(e)}")
            self.stackedWidget_Fase.setCurrentIndex(0)

    def EliminarFase(self):
        """Slot para el botón de eliminar cuadrilla"""
        selected_items = self.Fase_tableWidget.selectedItems()
        
        if not selected_items:
            QMessageBox.warning(self, "Advertencia", "Por favor seleccione una fase para eliminar")
            return
        
        selected_rows = {item.row() for item in selected_items}
        
        if len(selected_rows) > 1:
            QMessageBox.warning(self, "Advertencia", "Por favor seleccione solo una fase para eliminar")
            return
        
        row = selected_rows.pop()
        id_fase = int(self.Fase_tableWidget.item(row, 0).text())
        clave = self.Fase_tableWidget.item(row, 1).text()

        confirmacion = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Está seguro que desea eliminar la fase {clave}?\nEsta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if confirmacion == QMessageBox.StandardButton.Yes:
            #from controlador.tablas import eliminar_tabla
            if eliminar_fase(id_fase):
                QMessageBox.information(self, "Éxito", "Fase eliminada correctamente")
                self.mostrar_fases_en_tabla()  # Refrescar la tabla
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar la fase")



    #####################################################################
    #                   CRUD TABLA
    #####################################################################    
    def ConfirmarCreacionTabla(self):
        clave = self.CrearClaveTabla_lineEdit.text()
        ubicacion = self.CrearUbicacionTabla_lineEdit.text()
        nombre = self.CrearNombreTabla_lineEdit.text()
        id_fase = self.CrearFaseAsociadaDeTabla_comboBox.currentData()

        if clave.strip() and ubicacion.strip() and nombre.strip():
            try:
                crear_tabla(clave, ubicacion, nombre, id_fase)
                QMessageBox.information(self, "Éxito", "Tabla insertada exitosamente.")
                self.CrearClaveTabla_lineEdit.clear()
                self.CrearUbicacionTabla_lineEdit.clear()
                self.CrearNombreTabla_lineEdit.clear()
                self.stackedWidget_Tabla.setCurrentIndex(0)
                # Actualizar la tabla de tablas después de la inserción
                self.mostrar_tablas_en_tabla() # Asegúrate de tener este método definido
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear la tabla: {str(e)}")
        else:
            QMessageBox.warning(self, "Error", "Todos los campos son obligatorios")

    def ConfirmarActualizarTabla(self):
        """Actualiza los datos de la tabla seleccionada"""
        try:
            # Obtener los datos actualizados de los QLineEdit
            id_tabla = int(self.id_tabla)
            clave = self.ActualizarClaveTabla_lineEdit.text()
            ubicacion = self.ActualizarUbicacionTabla_lineEdit.text()
            nombre = self.ActualizarNombreTabla_lineEdit.text()
            id_fase = self.ActualizarFaseAsociadaDeTabla_comboBox.currentData()

            if not all([clave, ubicacion, nombre, id_fase]):
                QMessageBox.warning(self, "Advertencia", "Todos los campos son obligatorios")
                return

            # Llamar a la función de actualización en el controlador
            if actualizar_tabla(id_tabla, clave, ubicacion, nombre, id_fase):
                QMessageBox.information(self, "Éxito", "Tabla actualizada correctamente")
                self.stackedWidget_Tabla.setCurrentIndex(0)
                self.mostrar_tablas_en_tabla()
            else:
                QMessageBox.warning(self, "Error", "No se pudo actualizar la tabla")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al actualizar tabla: {str(e)}")

    def EliminarTabla(self):
        """Slot para el botón de eliminar cuadrilla"""
        selected_items = self.Tablas_tableWidget.selectedItems()
        
        if not selected_items:
            QMessageBox.warning(self, "Advertencia", "Por favor seleccione una tabla para eliminar")
            return
        
        selected_rows = {item.row() for item in selected_items}
        
        if len(selected_rows) > 1:
            QMessageBox.warning(self, "Advertencia", "Por favor seleccione solo una tabla para eliminar")
            return
        
        row = selected_rows.pop()
        id_tabla = int(self.Tablas_tableWidget.item(row, 0).text())
        clave = self.Tablas_tableWidget.item(row, 1).text()
        from db.entities.data_entities import Macrotunel, get_db
        db = get_db()
        try:
            tiene_macrotunel = db.query(Macrotunel).filter_by(id_Tabla=id_tabla).first() is not None
            if tiene_macrotunel:
                QMessageBox.warning(
                    self, "No se puede eliminar",
                    "Esta cuadrilla tiene macrotuneles asociados. Asigne estos macrotuneles a otra tabla primero."
                )
                return
        finally:
            db.close()

        confirmacion = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Está seguro que desea eliminar la tabla {clave}?\nEsta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if confirmacion == QMessageBox.StandardButton.Yes:
            #from controlador.tablas import eliminar_tabla
            if eliminar_tabla(id_tabla):
                QMessageBox.information(self, "Éxito", "Tabla eliminada correctamente")
                self.mostrar_tablas_en_tabla()  # Refrescar la tabla
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar la cuadrilla")

    def CrearTabla(self):
        self.stackedWidget_Tabla.setCurrentIndex(1)
        self.cargar_fases_tabla_comboBox()
        self.CrearClaveTabla_lineEdit.setText("T")

    def cargar_fases_tabla_comboBox(self):
        """Carga las fases en el comboBox de crear fase"""
        self.CrearFaseAsociadaDeTabla_comboBox.clear()
        fases = listar_fases()
        self.CrearFaseAsociadaDeTabla_comboBox.addItem("Seleccione una fase")
        for fase in fases:
            self.CrearFaseAsociadaDeTabla_comboBox.addItem(str(fase['Clave']), fase['id_Fase'])

    def ActualizarTabla(self):
        """Muestra el diálogo para actualizar una tabla"""
        try:
            selected_row_tabla = self.Tablas_tableWidget.currentRow()
            
            if selected_row_tabla < 0:
                QMessageBox.warning(self, "Advertencia", "Por favor seleccione una tabla para editar")
                return
            
            # Verificar que todas las celdas necesarias existen
            required_columns = 5  # id, clave, ubicación, descripción, num_macrotuneles
            for col in range(required_columns):
                item = self.Tablas_tableWidget.item(selected_row_tabla, col)
                if item is None or item.text().strip() == "":
                    QMessageBox.warning(self, "Error", f"Datos incompletos en la fila seleccionada (columna {col})")
                    return

            # Obtener datos
            self.id_tabla = self.Tablas_tableWidget.item(selected_row_tabla, 0).text()
            clave = self.Tablas_tableWidget.item(selected_row_tabla, 1).text()
            ubicacion = self.Tablas_tableWidget.item(selected_row_tabla, 2).text()
            nombre = self.Tablas_tableWidget.item(selected_row_tabla, 3).text()

            # Mostrar en el formulario de edición
            self.stackedWidget_Tabla.setCurrentIndex(2)
            # self.idTabla_Lbl.setText(self.id_tabla)
            self.idTabla_Lbl.setText(clave)
            self.ActualizarClaveTabla_lineEdit.setText(clave)
            self.ActualizarUbicacionTabla_lineEdit.setText(ubicacion)
            self.ActualizarNombreTabla_lineEdit.setText(nombre)
            fases = listar_fases()
            self.ActualizarFaseAsociadaDeTabla_comboBox.clear()
            for fase in fases:
                self.ActualizarFaseAsociadaDeTabla_comboBox.addItem(str(fase['Clave']), fase['id_Fase'])
            # Pre-seleccionar la fase actual
            clave_fase = self.Tablas_tableWidget.item(selected_row_tabla, 4).text()
            index = self.ActualizarFaseAsociadaDeTabla_comboBox.findText(clave_fase)
            if index >= 0:
                self.ActualizarFaseAsociadaDeTabla_comboBox.setCurrentIndex(index)

            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar datos para editar: {str(e)}")
            self.stackedWidget_Tabla.setCurrentIndex(0)




    #####################################################################
    #                   CRUD MACROTUNELES
    #####################################################################
    def ConfirmarCreacionMacrotunel(self):
        try:
            clave = self.CrearClaveMacrotunel_lineEdit.text()
            ubicacion = self.CrearUbicacionMacrotunel_lineEdit.text()
            nombre = self.CrearNombreMacrotunel_lineEdit.text()
            id_tabla = self.CrearTablaAsociadaDeMacrotunel_comboBox.currentData()

            # Validación mejorada con mensajes específicos
            if not clave:
                QMessageBox.warning(self, "Error", "Clave obligatoria")
                return
                      
            # Guardar en la base de datos
            if crear_macrotunel(clave, ubicacion, nombre, id_tabla):
                QMessageBox.information(self, "Éxito", "Macrotunel registrado exitosamente")
                self.limpiar_formulario_crear_macrotunel()
                self.stackedWidget_Macrotunel.setCurrentIndex(0)
                self.mostrar_macrotuneles_en_tabla()
            else:
                QMessageBox.warning(self, "Error", "No se pudo registrar macrotunel")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error: {str(e)}")
            print(f"Error al registrar macrotunel: {str(e)}")

    def ConfirmarMacrotunelActualizado(self):
        """Actualiza los datos del macrotunel seleccionado"""
        try:
            # Obtener los datos actualizados
            id_macrotunel = self.id_macrotunel
            clave = self.ActualizarClaveMacrotunel_lineEdit.text().strip()
            ubicacion = self.ActualizarUbicacionMacrotunel_lineEdit.text().strip()
            nombre = self.ActualizarNombreMacrotunel_lineEdit.text().strip()
            id_tabla = self.ActualizarTablaAsociadaDeMacrotunel_comboBox.currentData()
            
            # Validaciones
            if not clave:
                QMessageBox.warning(self, "Advertencia", "La clave es obligatoria")
                return
            
            # Si no se seleccionó tabla, establecer como None
            if id_tabla == "" or id_tabla == "Sin tabla asignada":
                id_tabla = None
            
            # Actualizar en la base de datos
            if actualizar_macrotunel(id_macrotunel, clave, ubicacion, nombre, id_tabla):
                QMessageBox.information(self, "Éxito", "Macrotunel actualizado correctamente")
                self.stackedWidget_Macrotunel.setCurrentIndex(0)
                self.mostrar_macrotuneles_en_tabla()
            else:
                QMessageBox.warning(self, "Error", "No se pudo actualizar el macrotunel")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al actualizar macrotunel: {str(e)}")
            print(f"Error detallado: {e}")

    def ActualizarMacrotunel(self):
        """Muestra el diálogo para actualizar un macrotunel"""
        try:
            selected_items = self.Macrotuneles_tableWidget.selectedItems()
            
            if not selected_items:
                QMessageBox.warning(self, "Advertencia", "Por favor seleccione un macrotunel para editar")
                return
            
            selected_row_macrotunel = selected_items[0].row()
            
            # Obtener datos de la fila seleccionada
            self.id_macrotunel = self.Macrotuneles_tableWidget.item(selected_row_macrotunel, 0).text()
            clave = self.Macrotuneles_tableWidget.item(selected_row_macrotunel, 1).text()
            ubicacion = self.Macrotuneles_tableWidget.item(selected_row_macrotunel, 2).text()
            nombre = self.Macrotuneles_tableWidget.item(selected_row_macrotunel, 3).text()
            
            # Cargar combobox con tablas disponibles
            self.cargar_tablas_actualizacion_comboBox()
            
            # Mostrar en el formulario de edición
            self.stackedWidget_Macrotunel.setCurrentIndex(2)
            self.idMacrotunel_Lbl.setText(clave)
            self.ActualizarClaveMacrotunel_lineEdit.setText(clave)
            self.ActualizarUbicacionMacrotunel_lineEdit.setText(ubicacion)
            self.ActualizarNombreMacrotunel_lineEdit.setText(nombre)
            
            # Seleccionar la tabla actual en el combobox
            clave_tabla = self.Macrotuneles_tableWidget.item(selected_row_macrotunel, 4).text()
            if clave_tabla and clave_tabla != "Sin tabla":
                index = self.ActualizarTablaAsociadaDeMacrotunel_comboBox.findText(clave_tabla)
                if index >= 0:
                    self.ActualizarTablaAsociadaDeMacrotunel_comboBox.setCurrentIndex(index)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar datos para editar: {str(e)}")
            print(f"Error detallado: {e}")
            self.stackedWidget_Macrotunel.setCurrentIndex(0)

    def cargar_tablas_actualizacion_comboBox(self):
        """Carga las tablas desde la base de datos al ComboBox de actualización"""
        try:
            self.ActualizarTablaAsociadaDeMacrotunel_comboBox.clear()
            tablas = listar_tabla_formulario()
            
            for tabla in tablas:
                self.ActualizarTablaAsociadaDeMacrotunel_comboBox.addItem(
                    f"{tabla.Clave}",
                    tabla.id_Tabla
                )
        except Exception as e:
            print(f"Error al cargar tablas: {e}")
            QMessageBox.warning(self, "Error", "No se pudieron cargar las tablas")

    def EliminarMacrotunel(self):
        """Slot para el botón de eliminar macrotunel"""
        selected_items_macrotunel = self.Macrotuneles_tableWidget.selectedItems()
        
        if not selected_items_macrotunel:
            QMessageBox.warning(self, "Advertencia", "Por favor seleccione un macrotunel para eliminar")
            return
        
        selected_rows = {item.row() for item in selected_items_macrotunel}
        
        if len(selected_rows) > 1:
            QMessageBox.warning(self, "Advertencia", "Por favor seleccione solo una macrotunel para eliminar")
            return
        
        row = selected_rows.pop()
        id_macrotunel = int(self.Macrotuneles_tableWidget.item(row, 0).text())
        nombre = self.Macrotuneles_tableWidget.item(row, 1).text()
        
        confirmacion = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Está seguro que desea eliminar el macrotunel {nombre}?\nEsta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if confirmacion == QMessageBox.StandardButton.Yes:
    
            if eliminar_macrotunel(id_macrotunel):
                QMessageBox.information(self, "Éxito", "Macrotunel eliminado correctamente")
                self.mostrar_macrotuneles_en_tabla()  # Refrescar la tabla
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar el macrotunel")

    def CrearMacrotunel(self):
        # Muestra dialogo para crear macrotunel
        self.stackedWidget_Macrotunel.setCurrentIndex(1)
        self.cargar_tablas_creacion_comboBox()
        self.CrearClaveMacrotunel_lineEdit.setText("MT")

    def limpiar_formulario_crear_macrotunel(self):
        self.CrearClaveMacrotunel_lineEdit.clear()
        self.CrearUbicacionTabla_lineEdit.clear()
        self.CrearNombreMacrotunel_lineEdit.clear()


    #####################################################################
    #                           CRUD LINEA
    #####################################################################
    def ConfirmarCreacionLinea(self):
        try:
            clave = self.CrearClaveLinea_lineEdit.text()
            ubicacion = self.CrearUbicacionLinea_lineEdit.text()
            nombre = self.CrearNombreLinea_lineEdit.text()
            num_macetas = self.CrearNumMacetasLinea_lineEdit.text()
            id_macrotunel = self.CrearMacrotunelAsociadoDeLinea_comboBox.currentData()

            # Validación mejorada con mensajes específicos
            if not clave:   
                QMessageBox.warning(self, "Error", "Clave obligatoria")
                return
                      
            # Guardar en la base de datos
            if crear_linea(clave, ubicacion, nombre, num_macetas, id_macrotunel):
                QMessageBox.information(self, "Éxito", "Linea registrada exitosamente")
                self.limpiar_formulario_crear_linea()
                self.stackedWidget_Linea.setCurrentIndex(0)
                self.mostrar_lineas_en_tabla()
            else:
                QMessageBox.warning(self, "Error", "No se pudo registrar linea")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error: {str(e)}")
            print(f"Error al registrar linea: {str(e)}")

    def limpiar_formulario_crear_linea(self):
        self.CrearClaveLinea_lineEdit.clear()
        self.CrearUbicacionLinea_lineEdit.clear()
        self.CrearNombreLinea_lineEdit.clear()
        self.CrearNumMacetasLinea_lineEdit.clear()
        self.CrearMacrotunelAsociadoDeLinea_comboBox.setCurrentIndex(-1)

    def CrearLinea(self):
        self.stackedWidget_Linea.setCurrentIndex(1)  
        self.cargar_macrotuneles_linea_comboBox()
        self.CrearClaveLinea_lineEdit.setText("L")  

    def cargar_macrotuneles_linea_comboBox(self):
        """Carga las macrotuneles en el ComboBox"""
        self.CrearMacrotunelAsociadoDeLinea_comboBox.clear()
        macrotuneles = listar_macrotunel() 
        for macrotunel in macrotuneles:
            self.CrearMacrotunelAsociadoDeLinea_comboBox.addItem(str(macrotunel['Clave']), macrotunel['id_Macrotunel'])

    def ConfirmarActualizarLinea(self):
        """Actualiza los datos de linea seleccionada"""
        try:
            # Obtener los datos actualizados
            id_linea = self.id_linea
            clave = self.ActualizarClaveLinea_lineEdit.text().strip()
            nombre = self.ActualizarNombreLinea_lineEdit.text().strip()
            ubicacion = self.ActualizarUbicacionLinea_lineEdit.text().strip()
            num_macetas = self.ActualizarNumMacetasLinea_lineEdit.text().strip()
            id_macrotunel = self.ActualizarMacrotunelAsociadoDeLinea_comboBox.currentData()
            
            # Validaciones
            if not clave:
                QMessageBox.warning(self, "Advertencia", "La clave es obligatoria")
                return
            
            # Si no se seleccionó tabla, establecer como None
            if id_macrotunel == "" or id_macrotunel == "Sin macrotunel asignado":
                id_macrotunel = None
            
            # Actualizar en la base de datos
            if actualizar_linea(id_linea, clave, ubicacion, nombre, num_macetas, id_macrotunel):
                QMessageBox.information(self, "Éxito", "Linea actualizada correctamente")
                self.stackedWidget_Linea.setCurrentIndex(0)
                self.mostrar_lineas_en_tabla()
            else:
                QMessageBox.warning(self, "Error", "No se pudo actualizar la linea")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al actualizar linea: {str(e)}")
            print(f"Error detallado: {e}")

    def ActualizarLinea(self):
        """Muestra el diálogo para actualizar una linea"""
        try:
            selected_items = self.Linea_tableWidget.selectedItems()
            
            if not selected_items:
                QMessageBox.warning(self, "Advertencia", "Por favor seleccione una linea para editar")
                return
            
            selected_row_linea = selected_items[0].row()
            
            # Obtener datos de la fila seleccionada
            self.id_linea = self.Linea_tableWidget.item(selected_row_linea, 0).text()
            clave = self.Linea_tableWidget.item(selected_row_linea, 1).text()
            nombre = self.Linea_tableWidget.item(selected_row_linea, 2).text()
            ubicacion = self.Linea_tableWidget.item(selected_row_linea, 3).text()
            num_macetas = self.Linea_tableWidget.item(selected_row_linea, 4).text()
            id_macrotunel = self.Linea_tableWidget.item(selected_row_linea, 5).text().split(":")[-1].strip()
            
            # Cargar combobox con tablas disponibles
            self.cargar_macrotunel_asociado_linea_comboBox()
            
            # Mostrar en el formulario de edición
            self.stackedWidget_Linea.setCurrentIndex(2)
            self.idLinea_Lbl.setText(clave)
            self.ActualizarClaveLinea_lineEdit.setText(clave)
            self.ActualizarUbicacionLinea_lineEdit.setText(ubicacion)
            self.ActualizarNombreLinea_lineEdit.setText(nombre)
            self.ActualizarNumMacetasLinea_lineEdit.setText(num_macetas)
            
            # Seleccionar el macrotunel actual en el combobox
            clave_macrotunel = self.Linea_tableWidget.item(selected_row_linea, 5).text()
            if clave_macrotunel and clave_macrotunel != "Sin macrotunel":
                index = self.ActualizarMacrotunelAsociadoDeLinea_comboBox.findText(clave_macrotunel)
                if index >= 0:
                    self.ActualizarMacrotunelAsociadoDeLinea_comboBox.setCurrentIndex(index)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar datos para editar: {str(e)}")
            print(f"Error detallado: {e}")
            self.stackedWidget_Linea.setCurrentIndex(0)

    def cargar_macrotunel_asociado_linea_comboBox(self):
        """Carga los macrotuneles desde la base de datos al ComboBox"""
        try:
            self.ActualizarMacrotunelAsociadoDeLinea_comboBox.clear()
            macrotuneles = listar_macrotunel()
            
            for macrotunel in macrotuneles:
                # Guardamos el ID como dato userData y mostramos el texto formateado
                self.ActualizarMacrotunelAsociadoDeLinea_comboBox.addItem(
                    str(macrotunel['Clave']),
                    macrotunel['id_Macrotunel']  # Esto guarda el ID como dato asociado
                )
        except Exception as e:
            print(f"Error al cargar macrotuneles: {e}")
            QMessageBox.warning(self, "Error", "No se pudieron cargar los macrotuneles")


    def EliminarLinea(self):
        """Slot para el botón de eliminar linea"""
        selected_items_linea = self.Linea_tableWidget.selectedItems()
        
        if not selected_items_linea:
            QMessageBox.warning(self, "Advertencia", "Por favor seleccione una linea para eliminar")
            return
        
        selected_rows = {item.row() for item in selected_items_linea}
        
        if len(selected_rows) > 1:
            QMessageBox.warning(self, "Advertencia", "Por favor seleccione solo una linea para eliminar")
            return
        
        row = selected_rows.pop()
        id_linea = int(self.Linea_tableWidget.item(row, 0).text())
        nombre = self.Linea_tableWidget.item(row, 1).text()
        
        confirmacion = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Está seguro que desea eliminar el la linea {nombre}?\nEsta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if confirmacion == QMessageBox.StandardButton.Yes:
    
            if eliminar_linea(id_linea):
                QMessageBox.information(self, "Éxito", "Linea eliminada correctamente")
                self.mostrar_lineas_en_tabla()  # Refrescar la tabla
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar la linea")






        
    #####################################################################
    #                           RETROCESOS
    #####################################################################        
    def showMainScreen(self):
        self.stackedWidget_Principal.setCurrentIndex(0)

    def Back_TablasMenu(self):
        self.showMainScreen()

    def Back_MacrotunelesMenu(self):
        self.showMainScreen()

    def Back_FaseMenu(self):
        self.showMainScreen()

    def Back_LineaMenu(self):
        self.showMainScreen()

    def Back_CrearMacrotunel(self):
        #self.limpiar_formulario_macrotunel()
        self.stackedWidget_Macrotunel.setCurrentIndex(0)
        
    def Back_ActualizarMacrotunel(self):
        self.stackedWidget_Macrotunel.setCurrentIndex(0)

    def Back_CrearTabla(self):
        self.stackedWidget_Tabla.setCurrentIndex(0)

    def Back_ActualizarTabla(self):
        self.stackedWidget_Tabla.setCurrentIndex(0)



    def CalidadMala(self):
        # if not self.on_impresora_checked():
        #     pass
        if not self.on_bascula_checked():
            pass
        self._registrar_cosecha("Mala")
        total = self.Peso_Total_Estacion()
        self.TotalCosechadoPrincipalText_Lbl.setText(f"{str(total)} Kg")
        self.ConfirmarCalificacion_Btn.setEnabled(True)
        self.CalidadCosechaText_Lbl.setText("Mala")
        self.BuenaCalidad_Btn.setEnabled(False)
        self.RegularCalidad_Btn.setEnabled(False)
        self.MalaCalidad_Btn.setEnabled(False)
        self.BotonVerdeClaro(self.ConfirmarCalificacion_Btn)
   
    def CalidadRegular(self):
        # if not self.on_impresora_checked():
        #     pass
        if not self.on_bascula_checked():
            pass
        self._registrar_cosecha("Regular")
        total = self.Peso_Total_Estacion()
        self.TotalCosechadoPrincipalText_Lbl.setText(f"{str(total)} Kg")
        self.ConfirmarCalificacion_Btn.setEnabled(True)
        self.CalidadCosechaText_Lbl.setText("Regular")
        self.BuenaCalidad_Btn.setEnabled(False)
        self.RegularCalidad_Btn.setEnabled(False)
        self.MalaCalidad_Btn.setEnabled(False)
        self.BotonVerdeClaro(self.ConfirmarCalificacion_Btn)
        
    def CalidadBuena(self):
        # if not self.on_impresora_checked():
        #     pass
        if not self.on_bascula_checked():
            pass
        self._registrar_cosecha("Buena")
        total = self.Peso_Total_Estacion()
        self.TotalCosechadoPrincipalText_Lbl.setText(f"{str(total)} Kg")
        self.ConfirmarCalificacion_Btn.setEnabled(True)
        self.CalidadCosechaText_Lbl.setText("Buena")
        self.BuenaCalidad_Btn.setEnabled(False)
        self.RegularCalidad_Btn.setEnabled(False)
        self.MalaCalidad_Btn.setEnabled(False)
        self.BotonVerdeClaro(self.ConfirmarCalificacion_Btn)
        

    def _registrar_cosecha(self, calificacion):
        """Registra la cosecha con la calificación especificada"""
        try:
            # Obtener datos de la interfaz
            nombre = self.NombreCosechaText_Lbl.text() #Nombre de colector
            # modalidad = self.ModalidadDatosCosechaText_Lbl.text()
            # macrotunel_clave = self.MacrotunelCosechaText_Lbl.text() #Numero de macrotunel
            linea_clave = self.LineaCosechaText_Lbl.text()
            cuadrilla_clave = self.CuadrillaCosechaText_Lbl.text() #Numero de cuadrilla
            
            # Validar datos
            if not nombre or not linea_clave:
                QMessageBox.warning(self, "Error", "Faltan datos del recolector o macrotúnel")
                return
                
            # Obtener el ID de modalidad desde el comboBox (userData guardado con addItem)
            id_modalidad = self.ModalidadConfiguracion_comboBox.currentData()
            
            if not id_modalidad:
                QMessageBox.warning(self, "Error", "No se ha seleccionado una modalidad válida")
                return

            # Obtener peso de la báscula
            peso = get_peso()
            if peso is None:
                #MessageBox para ingresar peso manualmente en caso de no ser detectado
                reply = QMessageBox.warning(self, 'Bascula apagada o desconectada', 
                                        'Ingrese el peso manualmente.',
                                        QMessageBox.StandardButton.Ok)
                self.BasculaTestigo_toolButton.setStyleSheet("""
                    QToolButton{
                        background-color: rgb(255, 0, 0);
                        border-radius: 10px;
                    }
                """)
                if reply == QMessageBox.StandardButton.Ok:
                    peso, ok = QInputDialog.getDouble(self, 'Ingrese peso', 'Peso (kg):', 0, 0, 1, 3) #Tiene que ser float
                    if not ok:
                        return
                else:
                    return

            # Obtener frame actual de la cámara de cosecha
            # Validacion para detectar camara de cosecha conectada
            if not hasattr(self, 'cap_cosecha') or not self.cap_cosecha.isOpened():
                QMessageBox.warning(self, "Error", "Cámara de cosecha no disponible")
                return
                
            ret, frame_cosecha = self.cap_cosecha.read()
            if not ret:
                QMessageBox.warning(self, "Error", "No se pudo capturar imagen de la cosecha")
                return

            # Obtener IDs de la base de datos
            session = get_db()
            try:
                # Buscar recolector
                recolector = session.query(Recolector).filter(
                    Recolector.Nombre_Completo == nombre #Se valida y obtiene de la base de datos el nombre obtenido de NombreCosechaText_Lbl 
                ).first()
                
                # Se valida que exista el nombre del colector en la base de datos
                if not recolector:
                    QMessageBox.warning(self, "Error", f"No se encontró al recolector: {nombre}")
                    return
                
                # Se obtiene el id que le pertenece a Nombre_Completo
                if recolector is not None:
                    id_recolector = recolector.id_Recolector  # Acceder al ID del recolector encontrado
                    print(f"El ID del recolector {nombre} es: {id_recolector}")
                else:
                    print(f"No se encontró un recolector con el nombre {nombre}")
                    
                # Buscar id_MAcrotunel conociendo Clave
                # macrotunel = session.query(Macrotunel).filter(
                #     Macrotunel.Clave == macrotunel_clave
                # ).first()

                # # Buscar id_MAcrotunel conociendo Clave
                # linea = session.query(Linea).filter(
                #     Linea.Clave == linea_clave
                # ).first()
                
                # Obtener el macrotunel seleccionado en la UI
                macrotunel_clave = self.MacrotunelCosechaText_Lbl.text()

                # Buscar la línea filtrando por Clave Y macrotunel para evitar ambigüedad
                linea = session.query(Linea).join(
                    Macrotunel, Linea.id_Macrotunel == Macrotunel.id_Macrotunel
                ).filter(
                    Linea.Clave == linea_clave,
                    Macrotunel.Clave == macrotunel_clave
                ).first()

                if not linea:
                    QMessageBox.warning(self, "Error", 
                                        f"No se encontró la línea {linea_clave} en el macrotúnel {macrotunel_clave}")
                    return
        
                # Se valida que exista el id del macrotunel en la base de datos
                if not linea:
                    QMessageBox.warning(self, "Error", f"No se encontró la linea: {linea_clave}")
                    return

                # Buscar id_Cuadrilla conociendo Clave
                cuadrilla = session.query(Cuadrilla).filter(
                    Cuadrilla.Clave == cuadrilla_clave
                ).first()
                
                # Se valida que exista el id de la cuadrilla en la base de datos
                if not cuadrilla:
                    QMessageBox.warning(self, "Error", f"No se encontró la cuadrilla: {cuadrilla_clave}")
                    return
                    

                # Iniciar nueva entrega
                if not self.flag_current_entrega:
                    self.current_entrega_id = iniciar_entrega(id_recolector=id_recolector, id_linea=linea.id_Linea, id_modalidad=id_modalidad)
                    self.flag_current_entrega = True
                    if self.current_entrega_id:
                        print(f"\n🚚 Iniciando nueva entrega ID: {self.current_entrega_id}")
                        
                success = registrar_cosecha(
                    id_recolector=id_recolector,
                    peso=peso,
                    calificacion=calificacion,
                    frame_cosecha=frame_cosecha,
                    id_linea=linea.id_Linea,
                    id_entrega=self.current_entrega_id,
                    id_modalidad=id_modalidad,
                    id_cuadrilla=cuadrilla.id_Cuadrilla
                )

                self.PesoCosechaText_Lbl.setText(str(peso))

                if success:
                    print("Cosecha registrada correctamente")
                else:
                    print("Error al registrar cosecha")
                    QMessageBox.warning(self, "Error", "No se pudo registrar la cosecha")
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al registrar: {str(e)}")
                print("Error al registrar: ", e)
            finally:
                session.close()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error inesperado: {str(e)}")

    def FinalizarEntrega(self, current_entrega):
        # Finalizar la entrega
        self.flag_current_entrega = False
        finalizar_entrega(current_entrega)
        print(f"\n🏁 Entrega {current_entrega} finalizada correctamente")
        current_entrega = None

    # def EntrarLogin(self):
    #     usuario = self.UsuarioLogin_lineEdit.text().upper()
    #     contraseña = self.PasswordLogin_lineEdit.text().upper()

    #     if usuario == "ADMIN" and contraseña == "ADMIN":  # Reemplaza con tu lógica real
    #         self.stackedWidget_Principal.setCurrentIndex(0)
    #     else:
    #         QMessageBox.warning(self, "Error", "Credenciales incorrectas")

    def EntrarLogin(self):
        usuario = self.UsuarioLogin_lineEdit.text().upper().strip()
        contraseña = self.PasswordLogin_lineEdit.text().strip()

        # Verificar conexión antes de intentar login
        if not probar_conexion():
            QMessageBox.warning(self, "Sin conexión", 
                                "No hay conexión a la base de datos.\nVerifica las credenciales de conexión.")
            return

        try:
            acceso = KeysAcceso()
            ok, result = acceso.login(usuario, contraseña)

            if ok:
                self.stackedWidget_Principal.setCurrentIndex(0)
            else:
                QMessageBox.warning(self, "Error", result)
        except Exception as e:
            # QMessageBox.warning(self, "Error al hacer login", str(e))  # ← str(e)
            QMessageBox.warning(self, "Error al hacer login", "Verifique conexion a base de datos.")


    def BackLogin(self):
        self.stackedWidget_Principal.setCurrentIndex(7)
        
    # def ShowConfigurarCredencialesDB(self):
    #     key, ok = QInputDialog.getText(
    #         self,
    #         "Acceso Restringido",
    #         "Ingrese la clave de acceso:",
    #         QLineEdit.EchoMode.Password
    #     )

    #     if not ok:
    #         return  # Canceló el usuario

    #     key = key.strip()

    #     if key == "":
    #         QMessageBox.warning(self, "Error", "No ingresaste ninguna clave")
    #         return

    #     acceso = KeysAcceso()

    #     if acceso.key_acceso_modulo(key):
    #         self.stackedWidget_Principal.setCurrentIndex(8)
    #     else:
    #         QMessageBox.warning(self, "Acceso Denegado", "Clave incorrecta")
        
    def ShowConfigurarCredencialesDB(self):
        key, ok = QInputDialog.getText(
            self,
            "Credenciales DB",
            "Ingrese la clave de acceso:",
            QLineEdit.EchoMode.Password
        )

        if not ok:
            return

        key = key.strip()

        if key == "":
            QMessageBox.warning(self, "Error", "No ingresaste ninguna clave")
            return

        CLAVE_DEFAULT = "berrisfanfest"

        # Sin conexión al servidor → clave default
        if not probar_conexion():
            if key == CLAVE_DEFAULT:
                self.stackedWidget_Principal.setCurrentIndex(8)
            else:
                QMessageBox.warning(self, "Acceso Denegado",
                                    "Sin conexión a la base de datos. Use la clave de configuración inicial.")
            return

        # Con conexión pero sin tablas creadas → clave default
        if not tablas_inicializadas():
            if key == CLAVE_DEFAULT:
                self.stackedWidget_Principal.setCurrentIndex(8)
            else:
                QMessageBox.warning(self, "Acceso Denegado",
                                    "Base de datos sin inicializar. Use la clave de configuración inicial.")
            return

        # Conexión activa y tablas existentes → validar contra DB
        try:
            acceso = KeysAcceso()
            if acceso.key_acceso_modulo(key):
                self.stackedWidget_Principal.setCurrentIndex(8)
            else:
                QMessageBox.warning(self, "Acceso Denegado", "Clave incorrecta")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def PowerPc(self):
        apagar = QMessageBox.question(self, 'Advertencia', 
                                        '¿Seguro que desea apagar el sistema?',
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if apagar == QMessageBox.StandardButton.Yes:
            os.system("shutdown /s /t 0")
        else:
            return  

    def CerrarSession(self):
        cerrar = QMessageBox.question(self, 'Advertencia', 
                                        '¿Seguro que desea cerrar sesión?',
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if cerrar == QMessageBox.StandardButton.Yes:
            self.UsuarioLogin_lineEdit.clear()
            self.PasswordLogin_lineEdit.clear()
            self.stackedWidget_Principal.setCurrentIndex(7)
            print("Se ha cambiado a login")
        else:
            return    
        

    def AceptarCredencialesDB(self):
        datos = {
            "SERVER": self.Servidor_lineEdit.text(),
            "DATABASE": self.BaseDeDatos_lineEdit.text(),
            "USERNAME": self.UsuarioDB__lineEdit.text(),
            "PASSWORD": self.PasswordDB_lineEdit.text(),
            "ID_CARRITO": self.IdCarrito_lineEdit.text()
        }

        guardar_credenciales(datos)

        if probar_conexion():
            QMessageBox.information(self, "Conexión exitosa", "Se guardaron las credenciales y se conectó exitosamente a la base de datos.")
            
            self.reinicializar_dependencias_db()
            self.iniciar_id_carrito()
            self.stackedWidget_Principal.setCurrentIndex(7)

        else:
            QMessageBox.warning(self, "Error de conexión", "No se pudo conectar a la base de datos. Verifica las credenciales ingresadas.")

    def reinicializar_dependencias_db(self):
        # Limpiar todas las tablas visuales
        self.Colectores_tableWidget.setRowCount(0)
        self.Cuadrilleros_tableWidget.setRowCount(0)
        self.Tablas_tableWidget.setRowCount(0)
        self.Macrotuneles_tableWidget.setRowCount(0)
        self.Vista_tableWidget.setRowCount(0)

        # Limpiar comboboxes
        self.TablaConfiguracion_comboBox.clear()
        self.TablaVista_comboBox.clear()
        self.MacrotunelVista_comboBox.clear()
        self.MacrotunelConfiguracion_comboBox.clear()
        
        # Reconfigurar UI con datos actualizados desde DB
        self.inicializar_dependencias_db()

    
    def cargar_credenciales_en_formulario(self):
        datos = cargar_credenciales()
        self.Servidor_lineEdit.setText(datos.get("SERVER", ""))
        self.BaseDeDatos_lineEdit.setText(datos.get("DATABASE", ""))
        self.UsuarioDB__lineEdit.setText(datos.get("USERNAME", ""))
        self.PasswordDB_lineEdit.setText(datos.get("PASSWORD", ""))
        self.Driver_lineEdit.setText(datos.get("DRIVER", ""))

    def cleanup_resources(self):
        """Versión mejorada para limpieza de recursos"""
        try:
            # Detener timers
            for timer_name in ['timer', 'timer_registroFacial', 'timer_registroCosecha', 'timer_deteccionFacial']:
                if hasattr(self, timer_name):
                    timer = getattr(self, timer_name)
                    if timer.isActive():
                        timer.stop()
                        # Esperar a que realmente se detenga
                        while timer.isActive():
                            QApplication.processEvents()
            
            # Manejar el thread de reconocimiento facial
            if hasattr(self, 'facial_thread') and self.facial_thread.isRunning():
                if hasattr(self, 'facial_worker'):
                    self.facial_worker.stop()  # Asegurarse de llamar al método stop
                    
                self.facial_thread.quit()
                if not self.facial_thread.wait(2000):  # Esperar máximo 2 segundos
                    self.facial_thread.terminate()  # Forzar si no responde
                    
            # Liberar cámaras de manera segura
            for cap_name in ['cap', 'cap_cosecha']:
                if hasattr(self, cap_name):
                    cap = getattr(self, cap_name)
                    if cap is not None and cap.isOpened():
                        cap.release()
                    setattr(self, cap_name, None)
                    
        except Exception as e:
            print(f"Error durante la limpieza: {str(e)}")


    def closeEvent(self, event):
        """Manejar el cierre de la ventana principal"""
        self.cleanup_resources()
        event.accept()

       
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    main_window = ArandanosControl()
    main_window.show()
    app.exec()

    sys.exit(0)