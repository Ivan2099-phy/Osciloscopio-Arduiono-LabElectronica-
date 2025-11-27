void setup() {
  // put your setup code here, to run once:
  VariableTiempo = 
  pinMode(A0, INPUT)
  pinMode(A1, INPUT)
  pinMode(A2, INPUT)
}

void leerComandos(AnalogPin){
  Value = analogRead(AnalogPin)
  }

void loop() {
  // put your main code here, to run repeatedly:
  leerComandos():
  // Si hay medición activa captura los datos
  if (medir) {
    capturarDatos();
    if (TriggerActivo){
      if (!verificarTrigger){
        return ;
      }
    }
    enviarDatos();
  }
  delay(VariableTiempo);
}
