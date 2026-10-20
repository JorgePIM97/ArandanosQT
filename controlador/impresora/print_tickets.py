# controlador/impresora/print_tickets.py
import win32print
import win32api
from datetime import datetime
import time

class TicketPrinter:
    def __init__(self, printer_name=None, line_spacing=1, cut_spaces=2):
        self.printer_name = printer_name
        self.line_spacing = line_spacing
        self.cut_spaces = cut_spaces
        if not self.printer_name:
            self._detect_printer()

    def _detect_printer(self):
        """Detecta la impresora térmica. Retorna None si no encuentra ninguna coincidencia."""
        printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)
        keywords = ["ZK", "TECO", "POS", "80", "THERMAL"]

        for printer in printers:
            name = printer[2].upper()
            if any(k in name for k in keywords):
                self.printer_name = printer[2]
                return self.printer_name

        # No se encontró ninguna impresora térmica
        self.printer_name = None
        return None

    def is_printer_online(self):
        """Verifica si la impresora está offline según el flag de Windows."""
        if not self.printer_name:
            return False

        try:
            hPrinter = win32print.OpenPrinter(self.printer_name)
            try:
                info = win32print.GetPrinter(hPrinter, 2)
                attributes = info['Attributes']

                if attributes & win32print.PRINTER_ATTRIBUTE_WORK_OFFLINE:
                    return False

                return True
            finally:
                win32print.ClosePrinter(hPrinter)
        except Exception as e:
            print(f"Error verificando estado de impresora: {e}")
            return False
    
    def _add_line_spacing(self, lines):
        """Agrega espaciado entre líneas según configuración"""
        spaced_lines = []
        for line in lines:
            spaced_lines.append(line)
            spaced_lines.extend([""] * self.line_spacing)
        return spaced_lines
    
    def print_ticket_de_vuelta(self, fecha, vuelta, nombre, buenas, regulares, malas, peso_vuelta):
        """
        Imprime un ticket de vuelta con formato mejorado y espaciado para corte.
        
        Args:
            fecha (str): Fecha de la vuelta
            vuelta (str): Número o identificador de vuelta
            nombre (str): Nombre del recolector
            buenas (str): Cantidad de buenas
            regulares (str): Cantidad de regulares
            malas (str): Cantidad de malas
            peso_vuelta (str): Peso total en kg
        """
        try:
            # Construir el contenido del ticket con espaciado
            ticket_lines = [
                "\x1B\x33\x00",
                "CASA LOS OLIVOS - TICKET DE VUELTA", #icono berries_ticket.png
                "-" * 48,
                # f"Fecha: {fecha}",
                f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
                f"Vuelta: {vuelta}",
                f"Nombre: {nombre}",
                "CALIFICACIONES:",
                f"Buenas: {buenas}",
                f"Regulares: {regulares}",
                f"Malas: {malas}",
                f"PESO TOTAL: {peso_vuelta} Kg",
                "-" * 48
            ]
            
            # Aplicar espaciado entre líneas
            spaced_lines = self._add_line_spacing(ticket_lines)
            
            # Agregar espacios para el corte
            spaced_lines.extend(["\n"] * self.cut_spaces)
            
            # Agregar comando de corte (si la impresora lo soporta)
            spaced_lines.append("\x1B\x69")  # Comando ESC/P para corte parcial
            
            # Unir todo el contenido
            text_to_print = "\n".join(spaced_lines)
            
            # Abrir la impresora
            hPrinter = win32print.OpenPrinter(self.printer_name)
            
            # Iniciar el trabajo de impresión
            job_info = win32print.StartDocPrinter(hPrinter, 1, ("Ticket de Vuelta", None, "RAW"))
            win32print.StartPagePrinter(hPrinter)
            
            # Enviar texto a imprimir (en bytes)
            win32print.WritePrinter(hPrinter, text_to_print.encode('utf-8'))
            
            # Finalizar
            win32print.EndPagePrinter(hPrinter)
            win32print.EndDocPrinter(hPrinter)
            win32print.ClosePrinter(hPrinter)
            
            return True
        except Exception as e:
            print(f"Error al imprimir: {e}")
            return False
    
    def print_ticket_del_dia(self, fecha, nombre, total_vueltas, peso_total, total_buenas, total_regulares, total_malas):
        """
        Imprime un ticket del día con formato optimizado para 80mm.
        
        Args:
            fecha (str): Fecha del ticket
            nombre (str): Nombre del recolector
            total_vueltas (str): Total de vueltas del día
            peso_total (str): Peso total acumulado
            total_buenas (str): Total de calificación buenas
            total_regulares (str): Total de calificación regulares
            total_malas (str): Total de calificación malas
        """
        try:
            # Construir el contenido del ticket con formato optimizado
            ticket_lines = [
                "\x1B\x33\x00",
                "CASA LOS OLIVOS - TICKET DEL DIA",
                "=" * 48,
                # f"Fecha: {fecha}",
                f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
                f"Nombre: {nombre}",
                "-" * 48,
                f"Total Vueltas: {total_vueltas}",
                f"Peso Total: {peso_total}",
                "CALIFICACIONES TOTALES:",
                f"Buenas: {total_buenas}",
                f"Regulares: {total_regulares}",
                f"Malas: {total_malas}",
                "=" * 48
            ]
            
            # Aplicar espaciado entre líneas
            spaced_lines = self._add_line_spacing(ticket_lines)
            
            # Agregar espacios para el corte
            spaced_lines.extend(["\n"] * self.cut_spaces)
            spaced_lines.append("\x1B\x69")  # Comando de corte parcial
            
            # Unir todo el contenido
            text_to_print = "\n".join(spaced_lines)
            
            # Abrir la impresora y imprimir
            hPrinter = win32print.OpenPrinter(self.printer_name)
            job_info = win32print.StartDocPrinter(hPrinter, 1, ("Ticket del Día", None, "RAW"))
            win32print.StartPagePrinter(hPrinter)
            win32print.WritePrinter(hPrinter, text_to_print.encode('utf-8'))
            win32print.EndPagePrinter(hPrinter)
            win32print.EndDocPrinter(hPrinter)
            win32print.ClosePrinter(hPrinter)
            
            return True
        except Exception as e:
            print(f"Error al imprimir ticket del día: {e}")
            return False

    def print_corte_dia(self, fecha, resultados):
        """
        Imprime el corte del día en formato de ticket optimizado para 80mm.
        
        Args:
            fecha (str): Fecha del corte
            resultados (list): Lista de resultados del corte
        """
        try:
            # Construir el contenido del ticket
            ticket_lines = [
                "\x1B\x33\x00",
                "CASA LOS OLIVOS - CORTE DEL DIA",
                "=" * 48,
                f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
                "=" * 48
            ]
            
            if resultados:
                # Agregar encabezados de tabla
                ticket_lines.append("Nombre   | Vueltas | T.Kg | T.B | T.R | T.M")
                ticket_lines.append("-" * 32)
                
                # Agregar cada fila de resultados (máximo 8-10 líneas para evitar desborde)
                for i, row in enumerate(resultados[:8]):  # Limitar a 8 registros por ticket
                    # Formatear nombre para que quepa (máximo 15 caracteres)
                    nombre = row[0][:50] if len(row[0]) > 50 else row[0]
                    # Formatear línea compacta
                    line = f"{nombre} | {row[1]} | {row[2]:.3f} | {row[3]:} | {row[4]} | {row[5]}"
                    ticket_lines.append(line)
                
                # Si hay más registros, indicarlo
                if len(resultados) > 8:
                    ticket_lines.append(f"... y {len(resultados) - 8} más")
                    
                # Agregar totales si es necesario
                ticket_lines.append("-" * 32)
                total_vueltas = sum(row[1] for row in resultados)
                total_peso = sum(row[2] for row in resultados)
                total_buenas = sum(row[3] for row in resultados)
                total_regulares = sum(row[4] for row in resultados)
                total_malas = sum(row[5] for row in resultados)
                ticket_lines.append(f"TOTAL: {total_vueltas} Vueltas | {total_peso:>6.2f} Kg. | {total_buenas} B | {total_regulares} R | {total_malas} M")
            else:
                ticket_lines.append("No hay registros de")
                ticket_lines.append("cosecha para hoy")
            
            ticket_lines.extend([
                "=" * 48
            ])
            
            # Aplicar espaciado entre líneas
            spaced_lines = self._add_line_spacing(ticket_lines)
            
            # Agregar espacios para el corte
            spaced_lines.extend(["\n"] * self.cut_spaces)
            spaced_lines.append("\x1B\x69")  # Comando de corte parcial
            
            # Unir todo el contenido
            text_to_print = "\n".join(spaced_lines)
            
            # Abrir la impresora y imprimir
            hPrinter = win32print.OpenPrinter(self.printer_name)
            job_info = win32print.StartDocPrinter(hPrinter, 1, ("Corte del Día", None, "RAW"))
            win32print.StartPagePrinter(hPrinter)
            win32print.WritePrinter(hPrinter, text_to_print.encode('utf-8'))
            win32print.EndPagePrinter(hPrinter)
            win32print.EndDocPrinter(hPrinter)
            win32print.ClosePrinter(hPrinter)
            
            return True
        except Exception as e:
            print(f"Error al imprimir corte del día: {e}")
            return False
        
    @staticmethod
    def list_printers():
        """Lista todas las impresoras disponibles"""
        printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)
        return [printer[2] for printer in printers]