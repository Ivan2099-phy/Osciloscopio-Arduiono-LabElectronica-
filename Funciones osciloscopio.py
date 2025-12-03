def channel(self, canal):
    self.canal_actual = canal
    #Agregar si el canal seleccionado está activo o no

def eje_horizontal(self):
    tdiv = self.doubleSpinBox.value()
    tpos = self.doubleSpinBox_2.value()
    
    self.tiempo = self.time* tdiv + tpos #time es una lista con los valores del tiempo estándar creada anteriormente
    
    self.replot()

def eje_vertical(self):
    canal = self.canal_actual
    vdiv = self.doubleSpinBox_algo.value() #división vertical
    vpos = self.doubleSpinBox_algo2.value() #posición vertical

    self.div_volts[canal] = vdiv #División vertical para canal

    V_CH = self.Voltajes[canal] #Voltajes es una lista con listas de los voltajes de cada canal: Voltajes = [[vCH1], [VCH2], [VCH3]]
    volts = [(v * vdiv) + vpos for v in V_CH]

    self.voltaje[canal] = volts
    
    self.replot()
