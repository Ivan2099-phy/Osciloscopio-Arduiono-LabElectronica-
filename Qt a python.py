import numpy
from PyQt5 import uic
from PyQt5.QtWidgets import QDoubleSpinBox, QWidget, QApplication, QMainWindow
from PyQt5.QtCore import pyqtSignal as Signal

# Y cargas el UI así:
#self.ui = uic.loadUi("ui/qt_oscilokopio.ui", self)

def conectar_controles(self):
    # Conexiones
    self.doubleSpinBox.valueChanged.connect(self.eje_horizontal) #División del eje horizontal (tiempo)
    self.doubleSpinBox_2.valueChanged.connect(self.eje_horizontal) #Posición horizontal

    self.QComboBox_algo.currentIndexChanged.connect(self.channel) #Canal seleccionado
    self.doubleSpinBox_algo.valueChanged.connect(self.eje_vertical) #División del eje vertical (voltaje)
    self.doubleSpinBox_algo2.valueChanged.connect(self.eje_vertical) #Posición vertical

    self.TipoWidged_2.stateChanged.connect(self.sett_channel) #Canal activo o inactivo

    # Herramientas
    puntos = 500
    self.tiempo_normalizado = np.linspace(
            -5.0,          # -5 divisiones (izquierda de la pantalla)
            5.0,          # +5 divisiones (derecha de la pantalla)
            self.puntos
        )
    self.div_volts = [0.0, 0.0, 0.0, 0.0]
    Voltajes = [[vCH1], [VCH2], [VCH3]] #lista con listas de los voltajes de cada canal. Modificar
