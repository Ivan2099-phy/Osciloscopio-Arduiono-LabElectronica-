import sys
import os
import numpy as np
import serial
import serial.tools.list_ports
from datetime import datetime
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QTimer, pyqtSignal, QThread, QMutex
import pyqtgraph as pg
import csv

# Hilo para lectura serial
class SerialThread(QThread):
    data_received = pyqtSignal(list)
    arduino_disconnected = pyqtSignal()
    status_received = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.serial_port = None
        self.running = False
        self.mutex = QMutex()
        
    def connect_serial(self, port, baudrate=115200):
        self.mutex.lock()
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
            
            self.serial_port = serial.Serial(port, baudrate, timeout=0.1)
            self.running = True
            return True
        except Exception as e:
            print(f"Error conectando: {e}")
            return False
        finally:
            self.mutex.unlock()
    
    def disconnect_serial(self):
        self.mutex.lock()
        self.running = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.mutex.unlock()
    
    def send_command(self, command):
        self.mutex.lock()
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.write((command + '\n').encode())
        except Exception as e:
            print(f"Error enviando comando: {e}")
            self.arduino_disconnected.emit()
        finally:
            self.mutex.unlock()
    
    def run(self):
        buffer = ""
        while self.running:
            self.mutex.lock()
            try:
                if self.serial_port and self.serial_port.is_open:
                    if self.serial_port.in_waiting > 0:
                        data = self.serial_port.read(self.serial_port.in_waiting).decode('utf-8', errors='ignore')
                        buffer += data
                        
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            line = line.strip()
                            
                            if line.startswith("DATA:"):
                                try:
                                    parts = line[5:].split(',')
                                    if len(parts) >= 5:
                                        time_val = float(parts[0]) / 1e6  # Convertir a segundos
                                        ch1 = float(parts[1]) if parts[1] != "NAN" else np.nan
                                        ch2 = float(parts[2]) if parts[2] != "NAN" else np.nan
                                        ch3 = float(parts[3]) if parts[3] != "NAN" else np.nan
                                        op = float(parts[4]) if parts[4] != "NAN" else np.nan
                                        self.data_received.emit([time_val, ch1, ch2, ch3, op])
                                except ValueError as e:
                                    print(f"Error parseando datos: {e}, línea: {line}")
                            elif line.startswith("OK:") or line.startswith("STATUS:") or line.startswith("DEBUG_"):
                                self.status_received.emit(line)
                                
            except Exception as e:
                print(f"Error en lectura serial: {e}")
                self.arduino_disconnected.emit()
            finally:
                self.mutex.unlock()
            
            self.msleep(1)

class OscilloscopeApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Inicializar variables
        self.serial_thread = SerialThread()
        self.measuring = False
        self.data_buffer = []
        self.max_points = 2000  # Aumentado
        self.colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00']
        
        # Configurar ventana principal
        self.setWindowTitle("Osciloscopio Digital")
        self.setGeometry(100, 100, 1200, 700)
        
        # Crear interfaz
        self.create_ui()
        
        # Conectar señales
        self.serial_thread.data_received.connect(self.update_data)
        self.serial_thread.arduino_disconnected.connect(self.arduino_disconnected)
        self.serial_thread.status_received.connect(self.process_status)
        
        # Timer para actualización de gráfico
        self.plot_timer = QTimer()
        self.plot_timer.timeout.connect(self.update_plot)
        self.plot_timer.start(100)  # 10 FPS
        
        # Timer para actualizar tiempo en pantalla
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time_display)
        self.time_timer.start(1000)
        
        # Inicializar lista de puertos
        self.refresh_ports()
        
        # Mostrar ventana
        self.show()
    
    def create_ui(self):
        """Crear toda la interfaz de usuario"""
        # Widget central
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QtWidgets.QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # --------------------- PANEL IZQUIERDO: GRÁFICO ---------------------
        plot_panel = QtWidgets.QWidget()
        plot_layout = QtWidgets.QVBoxLayout()
        plot_panel.setLayout(plot_layout)
        
        # Gráfico
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('k')
        self.plot_widget.setLabel('bottom', 'Tiempo', 's')
        self.plot_widget.setLabel('left', 'Voltaje', 'V')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        
        # Configurar rango inicial
        self.plot_widget.setXRange(-0.5, 0.5)  # -0.5 a 0.5 segundos
        self.plot_widget.setYRange(-0.5, 5.5)  # -0.5 a 5.5 voltios
        
        # Crear curvas
        self.curves = []
        curve_names = ['CH1', 'CH2', 'CH3', 'Operación']
        for i, (color, name) in enumerate(zip(self.colors, curve_names)):
            pen = pg.mkPen(color=color, width=2)
            curve = self.plot_widget.plot([], [], pen=pen, name=name)
            self.curves.append(curve)
        
        self.plot_widget.addLegend()
        
        # Añadir indicadores de voltaje actual
        self.voltage_labels = []
        for i in range(4):
            label = pg.TextItem(text='', color=self.colors[i], anchor=(0, 1))
            label.setPos(0.95, 0.95 - i*0.05)
            self.plot_widget.addItem(label)
            self.voltage_labels.append(label)
        
        plot_layout.addWidget(self.plot_widget)
        
        # --------------------- PANEL DERECHO: CONTROLES ---------------------
        controls_panel = QtWidgets.QWidget()
        controls_layout = QtWidgets.QVBoxLayout()
        controls_panel.setLayout(controls_layout)
        controls_panel.setMaximumWidth(400)
        
        # Conexión
        connection_group = QtWidgets.QGroupBox("Conexión")
        connection_layout = QtWidgets.QGridLayout()
        
        self.combo_ports = QtWidgets.QComboBox()
        self.btn_refresh = QtWidgets.QPushButton("Actualizar")
        self.btn_connect = QtWidgets.QPushButton("Conectar")
        
        connection_layout.addWidget(QtWidgets.QLabel("Puerto:"), 0, 0)
        connection_layout.addWidget(self.combo_ports, 0, 1, 1, 2)
        connection_layout.addWidget(self.btn_refresh, 1, 1)
        connection_layout.addWidget(self.btn_connect, 1, 2)
        connection_group.setLayout(connection_layout)
        
        # Lectura
        reading_group = QtWidgets.QGroupBox("Lectura")
        reading_layout = QtWidgets.QVBoxLayout()
        
        self.btn_start = QtWidgets.QPushButton("Iniciar Medición")
        self.btn_start.setStyleSheet("font-weight: bold;")
        
        # Canales
        channels_layout = QtWidgets.QVBoxLayout()
        self.channel_checks = []
        for i in range(3):
            check = QtWidgets.QCheckBox(f"Canal {i+1} (A{i})")
            check.setChecked(True)
            self.channel_checks.append(check)
            channels_layout.addWidget(check)
        
        self.btn_save = QtWidgets.QPushButton("Guardar Datos")
        self.btn_view_code = QtWidgets.QPushButton("Ver Código Arduino")
        
        # Información en tiempo real
        self.info_label = QtWidgets.QLabel("Esperando datos...")
        self.info_label.setStyleSheet("background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc;")
        
        reading_layout.addWidget(self.btn_start)
        reading_layout.addLayout(channels_layout)
        reading_layout.addWidget(self.info_label)
        reading_layout.addWidget(self.btn_save)
        reading_layout.addWidget(self.btn_view_code)
        reading_group.setLayout(reading_layout)
        
        # Ejes
        axes_group = QtWidgets.QGroupBox("Ejes")
        axes_layout = QtWidgets.QGridLayout()
        
        # Horizontal
        axes_layout.addWidget(QtWidgets.QLabel("Eje X (Tiempo)"), 0, 0, 1, 2)
        axes_layout.addWidget(QtWidgets.QLabel("Escala (s/div):"), 1, 0)
        self.spin_time_scale = QtWidgets.QDoubleSpinBox()
        self.spin_time_scale.setRange(0.001, 10.0)
        self.spin_time_scale.setValue(0.1)  # 100ms/div por defecto
        self.spin_time_scale.setDecimals(3)
        axes_layout.addWidget(self.spin_time_scale, 1, 1)
        
        axes_layout.addWidget(QtWidgets.QLabel("Posición (s):"), 2, 0)
        self.spin_time_pos = QtWidgets.QDoubleSpinBox()
        self.spin_time_pos.setRange(-10, 10)
        self.spin_time_pos.setValue(0.0)
        axes_layout.addWidget(self.spin_time_pos, 2, 1)
        
        # Vertical
        axes_layout.addWidget(QtWidgets.QLabel("Eje Y (Voltaje)"), 3, 0, 1, 2)
        axes_layout.addWidget(QtWidgets.QLabel("Escala (V/div):"), 4, 0)
        self.spin_volt_scale = QtWidgets.QDoubleSpinBox()
        self.spin_volt_scale.setRange(0.1, 5.0)
        self.spin_volt_scale.setValue(1.0)
        axes_layout.addWidget(self.spin_volt_scale, 4, 1)
        
        axes_layout.addWidget(QtWidgets.QLabel("Posición (V):"), 5, 0)
        self.spin_volt_pos = QtWidgets.QDoubleSpinBox()
        self.spin_volt_pos.setRange(-5, 5)
        self.spin_volt_pos.setValue(2.5)  # Centro en 2.5V
        axes_layout.addWidget(self.spin_volt_pos, 5, 1)
        
        axes_group.setLayout(axes_layout)
        
        # Trigger
        trigger_group = QtWidgets.QGroupBox("Trigger")
        trigger_layout = QtWidgets.QGridLayout()
        
        self.check_trigger = QtWidgets.QCheckBox("Activar Trigger")
        trigger_layout.addWidget(self.check_trigger, 0, 0, 1, 2)
        
        trigger_layout.addWidget(QtWidgets.QLabel("Nivel (V):"), 1, 0)
        self.spin_trigger_level = QtWidgets.QDoubleSpinBox()
        self.spin_trigger_level.setRange(0.0, 5.0)
        self.spin_trigger_level.setValue(2.5)
        trigger_layout.addWidget(self.spin_trigger_level, 1, 1)
        
        trigger_layout.addWidget(QtWidgets.QLabel("Dirección:"), 2, 0)
        self.combo_trigger_dir = QtWidgets.QComboBox()
        self.combo_trigger_dir.addItems(["Arriba", "Abajo"])
        trigger_layout.addWidget(self.combo_trigger_dir, 2, 1)
        
        trigger_layout.addWidget(QtWidgets.QLabel("Canal:"), 3, 0)
        self.combo_trigger_ch = QtWidgets.QComboBox()
        self.combo_trigger_ch.addItems(["CH1", "CH2", "CH3"])
        trigger_layout.addWidget(self.combo_trigger_ch, 3, 1)
        
        trigger_group.setLayout(trigger_layout)
        
        # Operaciones
        math_group = QtWidgets.QGroupBox("Operaciones")
        math_layout = QtWidgets.QVBoxLayout()
        
        self.combo_operation = QtWidgets.QComboBox()
        self.combo_operation.addItems(["Ninguna", "Suma (CH1+CH2+CH3)", "Resta (CH1-CH2-CH3)"])
        math_layout.addWidget(self.combo_operation)
        
        math_layout.addWidget(QtWidgets.QLabel("Tamaño Buffer:"))
        self.spin_buffer_size = QtWidgets.QSpinBox()
        self.spin_buffer_size.setRange(100, 10000)
        self.spin_buffer_size.setValue(2000)
        math_layout.addWidget(self.spin_buffer_size)
        
        # Botón para autoscala
        self.btn_autoscale = QtWidgets.QPushButton("Autoescala")
        math_layout.addWidget(self.btn_autoscale)
        
        math_group.setLayout(math_layout)
        
        # Añadir todos los grupos al panel de controles
        controls_layout.addWidget(connection_group)
        controls_layout.addWidget(reading_group)
        controls_layout.addWidget(axes_group)
        controls_layout.addWidget(trigger_group)
        controls_layout.addWidget(math_group)
        controls_layout.addStretch()
        
        # --------------------- CONECTAR SEÑALES ---------------------
        self.btn_refresh.clicked.connect(self.refresh_ports)
        self.btn_connect.clicked.connect(self.connect_disconnect)
        self.btn_start.clicked.connect(self.start_stop_measurement)
        self.btn_save.clicked.connect(self.save_data)
        self.btn_view_code.clicked.connect(self.view_arduino_code)
        self.btn_autoscale.clicked.connect(self.auto_scale)
        
        # Canales
        for i, check in enumerate(self.channel_checks):
            check.stateChanged.connect(lambda state, ch=i+1: self.toggle_channel(ch, state == 2))
        
        # Ejes
        self.spin_time_scale.valueChanged.connect(self.update_time_scale)
        self.spin_time_pos.valueChanged.connect(self.update_time_position)
        self.spin_volt_scale.valueChanged.connect(self.update_voltage_scale)
        self.spin_volt_pos.valueChanged.connect(self.update_voltage_position)
        
        # Trigger
        self.check_trigger.stateChanged.connect(self.toggle_trigger)
        self.spin_trigger_level.valueChanged.connect(self.change_trigger_level)
        self.combo_trigger_dir.currentIndexChanged.connect(self.change_trigger_direction)
        
        # Operaciones
        self.combo_operation.currentIndexChanged.connect(self.change_operation)
        self.spin_buffer_size.valueChanged.connect(self.change_buffer_size)
        
        # --------------------- AÑADIR PANELES AL LAYOUT PRINCIPAL ---------------------
        main_layout.addWidget(plot_panel, 70)
        main_layout.addWidget(controls_panel, 30)
        
        # --------------------- BARRA DE ESTADO ---------------------
        self.statusbar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Listo")
        
        # Inicializar escalas
        self.time_scale = self.spin_time_scale.value()
        self.time_position = self.spin_time_pos.value()
        self.voltage_scale = self.spin_volt_scale.value()
        self.voltage_position = self.spin_volt_pos.value()
        
        # Variables para seguimiento
        self.last_data_time = 0
        self.data_count = 0
    
    def refresh_ports(self):
        """Actualizar lista de puertos COM disponibles"""
        self.combo_ports.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.combo_ports.addItem(f"{port.device} - {port.description}")
        
        if not ports:
            self.combo_ports.addItem("No se encontraron puertos")
    
    def connect_disconnect(self):
        """Conectar o desconectar del Arduino"""
        if not self.serial_thread.running:
            port_text = self.combo_ports.currentText()
            if port_text and "No se encontraron puertos" not in port_text:
                # Extraer solo el nombre del puerto
                port = port_text.split(' - ')[0]
                if self.serial_thread.connect_serial(port):
                    self.statusbar.showMessage(f"Conectado a {port}")
                    self.serial_thread.start()
                    self.btn_connect.setText("Desconectar")
                    
                    # Enviar comando de prueba
                    self.serial_thread.send_command("TEST")
                else:
                    QtWidgets.QMessageBox.critical(self, "Error", f"No se pudo conectar a {port}")
            else:
                QtWidgets.QMessageBox.warning(self, "Advertencia", "Seleccione un puerto primero")
        else:
            self.serial_thread.disconnect_serial()
            self.statusbar.showMessage("Desconectado")
            self.btn_connect.setText("Conectar")
            self.measuring = False
            self.btn_start.setText("Iniciar Medición")
            self.btn_start.setStyleSheet("font-weight: bold;")
    
    def start_stop_measurement(self):
        """Iniciar o detener medición"""
        if not self.serial_thread.running:
            QtWidgets.QMessageBox.warning(self, "Error", "Conecte el Arduino primero")
            return
        
        self.measuring = not self.measuring
        
        if self.measuring:
            # Limpiar buffer de datos
            self.data_buffer = []
            self.data_count = 0
            
            # Enviar comando START
            self.serial_thread.send_command("START")
            
            # Actualizar interfaz
            self.btn_start.setText("Detener Medición")
            self.btn_start.setStyleSheet("background-color: #FF4444; color: white; font-weight: bold;")
            self.statusbar.showMessage("Medición en curso...")
        else:
            # Enviar comando STOP
            self.serial_thread.send_command("STOP")
            
            # Actualizar interfaz
            self.btn_start.setText("Iniciar Medición")
            self.btn_start.setStyleSheet("font-weight: bold;")
            self.statusbar.showMessage("Medición detenida")
    
    def toggle_channel(self, channel, enabled):
        """Activar/desactivar canal"""
        if not self.serial_thread.running:
            return
        
        command = f"CH{channel}_ON" if enabled else f"CH{channel}_OFF"
        self.serial_thread.send_command(command)
        
        # Actualizar estado en barra
        estado = "activado" if enabled else "desactivado"
        self.statusbar.showMessage(f"Canal {channel} {estado}", 2000)
    
    def change_operation(self, index):
        """Cambiar operación entre canales"""
        if not self.serial_thread.running:
            return
        
        if index == 0:  # Ninguna
            self.serial_thread.send_command("OP_OFF")
        elif index == 1:  # Suma
            self.serial_thread.send_command("OP_ADD")
        elif index == 2:  # Resta
            self.serial_thread.send_command("OP_SUB")
    
    def toggle_trigger(self, state):
        """Activar/desactivar trigger"""
        if not self.serial_thread.running:
            return
        
        if state == 2:  # Activado
            self.serial_thread.send_command("TRIGGER_ON")
            self.statusbar.showMessage("Trigger activado", 2000)
        else:
            self.serial_thread.send_command("TRIGGER_OFF")
            self.statusbar.showMessage("Trigger desactivado", 2000)
    
    def change_trigger_level(self, value):
        """Cambiar nivel del trigger"""
        if not self.serial_thread.running:
            return
        
        command = f"TRIGGER_NIVEL {value:.2f}"
        self.serial_thread.send_command(command)
    
    def change_trigger_direction(self, index):
        """Cambiar dirección del trigger"""
        if not self.serial_thread.running:
            return
        
        if index == 0:  # Arriba
            self.serial_thread.send_command("TRIGGER_DIR_ARRIBA")
        else:  # Abajo
            self.serial_thread.send_command("TRIGGER_DIR_ABAJO")
    
    def change_buffer_size(self, value):
        """Cambiar tamaño del buffer"""
        self.max_points = value
        
        # Redimensionar buffer si es necesario
        if len(self.data_buffer) > self.max_points:
            self.data_buffer = self.data_buffer[-self.max_points:]
        
        self.statusbar.showMessage(f"Buffer: {self.max_points} puntos", 2000)
    
    def update_data(self, data):
        """Actualizar buffer de datos"""
        if self.measuring:
            # data[0] ya está en segundos (convertido en SerialThread)
            self.last_data_time = data[0]
            self.data_count += 1
            
            # Agregar al buffer
            self.data_buffer.append(data)
            
            # Mantener tamaño máximo del buffer
            if len(self.data_buffer) > self.max_points:
                self.data_buffer.pop(0)
    
    def update_plot(self):
        """Actualizar gráfico"""
        if not self.data_buffer:
            return
        
        # Separar datos por canal
        times = [d[0] for d in self.data_buffer]
        ch1_data = [d[1] for d in self.data_buffer]
        ch2_data = [d[2] for d in self.data_buffer]
        ch3_data = [d[3] for d in self.data_buffer]
        op_data = [d[4] for d in self.data_buffer]
        
        # Actualizar curvas
        self.curves[0].setData(times, ch1_data)
        self.curves[1].setData(times, ch2_data)
        self.curves[2].setData(times, ch3_data)
        self.curves[3].setData(times, op_data)
        
        # Actualizar indicadores de voltaje
        if not np.isnan(ch1_data[-1]):
            self.voltage_labels[0].setText(f"CH1: {ch1_data[-1]:.3f} V")
        if not np.isnan(ch2_data[-1]):
            self.voltage_labels[1].setText(f"CH2: {ch2_data[-1]:.3f} V")
        if not np.isnan(ch3_data[-1]):
            self.voltage_labels[2].setText(f"CH3: {ch3_data[-1]:.3f} V")
        if not np.isnan(op_data[-1]):
            self.voltage_labels[3].setText(f"OP: {op_data[-1]:.3f} V")
        
        # Actualizar rango del gráfico
        time_span = self.time_scale * 10  # 10 divisiones
        self.plot_widget.setXRange(self.time_position - time_span/2, 
                                  self.time_position + time_span/2)
        
        volt_span = self.voltage_scale * 8  # 8 divisiones
        self.plot_widget.setYRange(self.voltage_position - volt_span/2,
                                  self.voltage_position + volt_span/2)
    
    def update_time_display(self):
        """Actualizar información en tiempo real"""
        if self.data_buffer:
            tiempo_total = self.data_buffer[-1][0] - self.data_buffer[0][0] if len(self.data_buffer) > 1 else 0
            self.info_label.setText(f"Datos: {len(self.data_buffer)} pts\n"
                                  f"Tiempo total: {tiempo_total:.3f} s\n"
                                  f"Último dato: {self.last_data_time:.3f} s")
    
    def update_time_scale(self, value):
        """Actualizar escala de tiempo"""
        self.time_scale = value
        self.statusbar.showMessage(f"Escala tiempo: {value} s/div", 1000)
    
    def update_time_position(self, value):
        """Actualizar posición horizontal"""
        self.time_position = value
    
    def update_voltage_scale(self, value):
        """Actualizar escala de voltaje"""
        self.voltage_scale = value
        self.statusbar.showMessage(f"Escala voltaje: {value} V/div", 1000)
    
    def update_voltage_position(self, value):
        """Actualizar posición vertical"""
        self.voltage_position = value
    
    def auto_scale(self):
        """Ajustar automáticamente la escala"""
        if not self.data_buffer:
            return
        
        # Encontrar valores mínimos y máximos
        all_voltages = []
        for data in self.data_buffer:
            if not np.isnan(data[1]): all_voltages.append(data[1])
            if not np.isnan(data[2]): all_voltages.append(data[2])
            if not np.isnan(data[3]): all_voltages.append(data[3])
            if not np.isnan(data[4]): all_voltages.append(data[4])
        
        if all_voltages:
            min_v = min(all_voltages)
            max_v = max(all_voltages)
            
            # Calcular escala y posición
            volt_span = max_v - min_v
            if volt_span == 0:
                volt_span = 1.0
            
            self.voltage_scale = max(0.1, volt_span / 6)  # 6 divisiones
            self.voltage_position = (min_v + max_v) / 2
            
            # Actualizar controles
            self.spin_volt_scale.setValue(self.voltage_scale)
            self.spin_volt_pos.setValue(self.voltage_position)
            
            self.statusbar.showMessage("Autoescala aplicada", 2000)
    
    def save_data(self):
        """Guardar datos en archivo CSV"""
        if not self.data_buffer:
            QtWidgets.QMessageBox.warning(self, "Advertencia", "No hay datos para guardar")
            return
        
        # Pedir nombre de archivo
        default_name = f"osciloscopio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Guardar datos", default_name, "CSV Files (*.csv);;Text Files (*.txt)"
        )
        
        if filename:
            # Verificar si el archivo ya existe
            if os.path.exists(filename):
                reply = QtWidgets.QMessageBox.question(
                    self, "Archivo existente",
                    f"El archivo '{os.path.basename(filename)}' ya existe. ¿Desea sobrescribirlo?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
                )
                if reply == QtWidgets.QMessageBox.No:
                    return
            
            try:
                with open(filename, 'w', newline='') as file:
                    writer = csv.writer(file)
                    
                    # Escribir encabezado con fecha y hora
                    now = datetime.now()
                    writer.writerow([f"Fecha: {now.strftime('%Y-%m-%d')}"])
                    writer.writerow([f"Hora: {now.strftime('%H:%M:%S')}"])
                    writer.writerow([f"Canales activos: CH1={self.channel_checks[0].isChecked()}, CH2={self.channel_checks[1].isChecked()}, CH3={self.channel_checks[2].isChecked()}"])
                    writer.writerow([f"Operación: {self.combo_operation.currentText()}"])
                    writer.writerow([f"Trigger: {'Activado' if self.check_trigger.isChecked() else 'Desactivado'}"])
                    writer.writerow(["Tiempo (s)", "CH1 (V)", "CH2 (V)", "CH3 (V)", "Operación (V)"])
                    
                    # Escribir datos
                    for row in self.data_buffer:
                        writer.writerow(row)
                
                self.statusbar.showMessage(f"Datos guardados en {filename}")
                QtWidgets.QMessageBox.information(self, "Éxito", f"Datos guardados en:\n{filename}")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"No se pudo guardar: {e}")
    
    def view_arduino_code(self):
        """Mostrar ventana con código Arduino"""
        # Buscar el archivo
        possible_paths = [
            "osciloscopio.ino",
            os.path.join(os.path.dirname(__file__), "osciloscopio.ino"),
            os.path.join(os.path.dirname(__file__), "..", "osciloscopio.ino"),
            os.path.join(os.path.dirname(__file__), "..", "Arduino", "osciloscopio.ino"),
        ]
        
        code = ""
        file_found = False
        file_path = ""
        
        for path in possible_paths:
            path = os.path.normpath(path)
            if os.path.exists(path):
                try:
                    with open(path, 'r') as file:
                        code = file.read()
                    file_found = True
                    file_path = path
                    break
                except:
                    pass
        
        if not file_found:
            QtWidgets.QMessageBox.warning(self, "Advertencia", 
                                         "Archivo 'osciloscopio.ino' no encontrado")
            return
        
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f"Código Arduino - {os.path.basename(file_path)}")
        dialog.resize(800, 600)
        
        layout = QtWidgets.QVBoxLayout()
        
        # Barra de herramientas
        toolbar = QtWidgets.QHBoxLayout()
        btn_copy = QtWidgets.QPushButton("Copiar al Portapapeles")
        btn_close = QtWidgets.QPushButton("Cerrar")
        toolbar.addWidget(btn_copy)
        toolbar.addStretch()
        toolbar.addWidget(btn_close)
        
        # Área de texto para el código
        text_edit = QtWidgets.QTextEdit()
        text_edit.setPlainText(code)
        text_edit.setReadOnly(True)
        
        # Configurar fuente monoespaciada
        font = QtGui.QFont("Consolas", 10)
        text_edit.setFont(font)
        
        # Añadir widgets al layout
        layout.addLayout(toolbar)
        layout.addWidget(text_edit)
        dialog.setLayout(layout)
        
        # Conectar botones
        btn_copy.clicked.connect(lambda: self.copy_to_clipboard(code))
        btn_close.clicked.connect(dialog.close)
        
        dialog.exec_()
    
    def copy_to_clipboard(self, text):
        """Copiar texto al portapapeles"""
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(text)
        self.statusbar.showMessage("Código copiado al portapapeles", 3000)
    
    def process_status(self, status):
        """Procesar mensajes de estado del Arduino"""
        print(f"Arduino: {status}")
        
        if status.startswith("OK:"):
            if "INICIO_MEDICION" in status:
                self.statusbar.showMessage("Medición iniciada")
            elif "MEDICION_DETENIDA" in status:
                self.statusbar.showMessage("Medición detenida")
            elif "OSCILOSCOPIO_INICIADO" in status:
                self.statusbar.showMessage("Arduino listo")
    
    def arduino_disconnected(self):
        """Manejar desconexión del Arduino"""
        self.measuring = False
        self.btn_start.setText("Iniciar Medición")
        self.btn_start.setStyleSheet("font-weight: bold;")
        self.btn_connect.setText("Conectar")
        QtWidgets.QMessageBox.warning(self, "Error", "Arduino desconectado")
        self.statusbar.showMessage("Arduino desconectado")
    
    def closeEvent(self, event):
        """Manejar cierre de la aplicación"""
        if self.serial_thread.running:
            # Detener medición si está activa
            if self.measuring:
                self.serial_thread.send_command("STOP")
            
            # Desconectar
            self.serial_thread.disconnect_serial()
            self.serial_thread.wait()
        
        event.accept()

def main():
    app = QtWidgets.QApplication(sys.argv)
    
    # Estilo moderno
    app.setStyle('Fusion')
    
    # Establecer paleta de colores
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor(240, 240, 240))
    app.setPalette(palette)
    
    window = OscilloscopeApp()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()