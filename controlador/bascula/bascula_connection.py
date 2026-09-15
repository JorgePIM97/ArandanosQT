#controlador/bascula/bascula_connection.py
import serial
import time
from serial.tools import list_ports

class BasculaTorreyLPCR_USB:
    def __init__(self, port=None):
        self.port = port
        self.ser = None
        
    def detectar_puerto(self):
        """Mejorada la detección de puertos"""
        for port in list_ports.comports():
            if 'USB' in port.description or 'Pesaje' in port.description or 'Serial' in port.description:
                return port.device 
        return None
    
    def conectar(self):
        try:
            if not self.port:
                self.port = self.detectar_puerto()
                if not self.port:
                    raise Exception("No se detectó puerto de báscula. Conecte la báscula y verifique")
            
            self.ser = serial.Serial(
                port=self.port,
                baudrate=9600,       # Asegúrate que coincida con la configuración de tu báscula
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=2,          # Aumenté el timeout para esperar respuesta
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )
            # Limpiar buffers antes de usar
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            return True
        except Exception as e:
            print(f"[BÁSCULA] Error de conexión: {str(e)}")
            return False
    
    def obtener_peso(self, intentos=3):
        """Método mejorado para obtener peso con reintentos"""
        for intento in range(intentos):
            try:
                if not self.ser or not self.ser.is_open:
                    if not self.conectar():
                        continue
                
                # Limpiar buffer antes de enviar comando
                self.ser.reset_input_buffer()
                
                # Enviar comando "P" en ASCII
                self.ser.write(b'P')
                
                # Leer hasta CR (0x0D) o timeout
                respuesta = self.ser.read_until(b'\r').decode('ascii', errors='ignore').strip()
                
                # Procesar respuesta (ejemplo: "1.23 kg" o "0.00 kg")
                if respuesta:
                    try:
                        # Eliminar texto "TARE" si está presente
                        respuesta = respuesta.replace('TARE', '').strip()
                        
                        # Manejar diferentes formatos de respuesta
                        if ' ' in respuesta:
                            peso, unidad = respuesta.rsplit(' ', 1)
                        elif ',' in respuesta:
                            peso, unidad = respuesta.rsplit(',', 1)
                        else:
                            peso = respuesta
                            unidad = 'kg'  # Asumir kg si no se especifica
                        
                        return {
                            'success': True,
                            'peso': float(peso),
                            'unidad': unidad,
                            'raw': respuesta
                        }
                    except ValueError as ve:
                        print(f"[BÁSCULA] Error al procesar respuesta '{respuesta}': {str(ve)}")
                        continue
                
            except Exception as e:
                print(f"[BÁSCULA] Error en intento {intento + 1}: {str(e)}")
                time.sleep(0.5)
                continue
        
        return {
            'success': False,
            'error': f"No se pudo obtener peso después de {intentos} intentos",
            'peso': None,
            'unidad': None
        }
    
    def cerrar(self):
        if self.ser and self.ser.is_open:
            self.ser.close()