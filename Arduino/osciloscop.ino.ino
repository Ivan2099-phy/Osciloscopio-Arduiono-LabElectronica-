// Definición de variables globales
bool channelActive1 = true;
bool channelActive2 = true;
bool channelActive3 = true;
bool medir = false;
bool operationActive = false;
bool triggerActivo = false;
bool triggerDetenido = false;
int operationMode = 0; // 0: ninguna, 1: suma, 2: resta
float triggerNivel = 2.5; // Voltaje del trigger
String triggerDireccion = "ARRIBA"; // "ARRIBA" o "ABAJO"

// Valores de voltaje de los canales
float vCH[3] = {0.0, 0.0, 0.0};
float resultOP = 0.0; // Resultado de la operación (suma/resta)

// Variables para el tiempo
unsigned long tiempoInicio = 0;
unsigned long ultimoTiempo = 0;
unsigned long tiempoActual = 0;

void setup() {
  Serial.begin(115200);
  while (!Serial) {
    ; // Esperar a que se conecte el puerto serie
  }
  tiempoInicio = micros();
}

void readChannels() {
  if (channelActive1) vCH[0] = analogRead(A0) * (5.0 / 1023.0);
  else vCH[0] = NAN;
  
  if (channelActive2) vCH[1] = analogRead(A1) * (5.0 / 1023.0);
  else vCH[1] = NAN;
  
  if (channelActive3) vCH[2] = analogRead(A2) * (5.0 / 1023.0);
  else vCH[2] = NAN;
}

void doOperation() {
  if (!operationActive) {
    resultOP = NAN;
    return;
  }
  
  float suma = 0.0;
  int canalesActivos = 0;
  
  // Calcular suma de canales activos
  if (channelActive1 && !isnan(vCH[0])) {
    suma += vCH[0];
    canalesActivos++;
  }
  if (channelActive2 && !isnan(vCH[1])) {
    suma += vCH[1];
    canalesActivos++;
  }
  if (channelActive3 && !isnan(vCH[2])) {
    suma += vCH[2];
    canalesActivos++;
  }
  
  if (operationMode == 1) { // SUMA
    resultOP = suma;
  } else if (operationMode == 2) { // RESTA (CH1 - CH2 - CH3)
    resultOP = vCH[0];
    if (channelActive2 && !isnan(vCH[1])) resultOP -= vCH[1];
    if (channelActive3 && !isnan(vCH[2])) resultOP -= vCH[2];
  }
}

bool checkTrigger() {
  if (!triggerActivo) return false;
  
  float valorTrigger = 0.0;
  
  // Determinar qué canal usar para trigger
  if (channelActive1 && !isnan(vCH[0])) valorTrigger = vCH[0];
  else if (channelActive2 && !isnan(vCH[1])) valorTrigger = vCH[1];
  else if (channelActive3 && !isnan(vCH[2])) valorTrigger = vCH[2];
  else return false;
  
  if (triggerDireccion == "ARRIBA") {
    if (valorTrigger > triggerNivel) {
      if (!triggerDetenido) {
        triggerDetenido = true;
        return true; // Trigger activado
      }
      return false;
    } else {
      triggerDetenido = false;
      return false;
    }
  } else { // ABAJO
    if (valorTrigger < triggerNivel) {
      if (!triggerDetenido) {
        triggerDetenido = true;
        return true; // Trigger activado
      }
      return false;
    } else {
      triggerDetenido = false;
      return false;
    }
  }
}

void sendDataToPC() {
  tiempoActual = micros() - tiempoInicio;
  
  Serial.print("DATA:");
  Serial.print(tiempoActual);
  Serial.print(",");
  
  // Canal 1
  if (channelActive1 && !isnan(vCH[0])) {
    Serial.print(vCH[0], 4);
  } else {
    Serial.print("NAN");
  }
  Serial.print(",");
  
  // Canal 2
  if (channelActive2 && !isnan(vCH[1])) {
    Serial.print(vCH[1], 4);
  } else {
    Serial.print("NAN");
  }
  Serial.print(",");
  
  // Canal 3
  if (channelActive3 && !isnan(vCH[2])) {
    Serial.print(vCH[2], 4);
  } else {
    Serial.print("NAN");
  }
  Serial.print(",");
  
  // Operación
  if (operationActive && !isnan(resultOP)) {
    Serial.print(resultOP, 4);
  } else {
    Serial.print("NAN");
  }
  Serial.println();
}

void interpretSerialCommands() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    // START/STOP
    if (command == "START") {
      medir = true;
      triggerDetenido = false;
      tiempoInicio = micros();
      Serial.println("OK:INICIO_MEDICION");
    } 
    else if (command == "STOP") {
      medir = false;
      Serial.println("OK:MEDICION_DETENIDA");
    }
    
    // Configuración de canales
    else if (command.startsWith("CH1_ON")) {
      channelActive1 = true;
      Serial.println("OK:CH1_ON");
    }
    else if (command.startsWith("CH1_OFF")) {
      channelActive1 = false;
      Serial.println("OK:CH1_OFF");
    }
    else if (command.startsWith("CH2_ON")) {
      channelActive2 = true;
      Serial.println("OK:CH2_ON");
    }
    else if (command.startsWith("CH2_OFF")) {
      channelActive2 = false;
      Serial.println("OK:CH2_OFF");
    }
    else if (command.startsWith("CH3_ON")) {
      channelActive3 = true;
      Serial.println("OK:CH3_ON");
    }
    else if (command.startsWith("CH3_OFF")) {
      channelActive3 = false;
      Serial.println("OK:CH3_OFF");
    }
    
    // Operaciones
    else if (command == "OP_ADD") {
      operationActive = true;
      operationMode = 1;
      Serial.println("OK:OPERACION_SUMA");
    }
    else if (command == "OP_SUB") {
      operationActive = true;
      operationMode = 2;
      Serial.println("OK:OPERACION_RESTA");
    }
    else if (command == "OP_OFF") {
      operationActive = false;
      Serial.println("OK:OPERACION_OFF");
    }
    
    // Trigger
    else if (command.startsWith("TRIGGER_ON")) {
      triggerActivo = true;
      Serial.println("OK:TRIGGER_ON");
    }
    else if (command.startsWith("TRIGGER_OFF")) {
      triggerActivo = false;
      Serial.println("OK:TRIGGER_OFF");
    }
    else if (command.startsWith("TRIGGER_NIVEL")) {
      triggerNivel = command.substring(14).toFloat();
      Serial.print("OK:NIVEL:");
      Serial.println(triggerNivel, 4);
    }
    else if (command.startsWith("TRIGGER_DIR_ARRIBA")) {
      triggerDireccion = "ARRIBA";
      Serial.println("OK:DIRECCION_ARRIBA");
    }
    else if (command.startsWith("TRIGGER_DIR_ABAJO")) {
      triggerDireccion = "ABAJO";
      Serial.println("OK:DIRECCION_ABAJO");
    }
    
    // Estado
    else if (command == "STATUS") {
      Serial.print("STATUS:");
      Serial.print(channelActive1 ? "1" : "0");
      Serial.print(channelActive2 ? "1" : "0");
      Serial.print(channelActive3 ? "1" : "0");
      Serial.print(",");
      Serial.print(medir ? "1" : "0");
      Serial.print(",");
      Serial.print(operationActive ? operationMode : "0");
      Serial.print(",");
      Serial.print(triggerActivo ? "1" : "0");
      Serial.println();
    }
  }
}

void loop() {
  interpretSerialCommands();
  
  if (medir) {
    readChannels();
    doOperation();
    
    // Verificar trigger
    if (triggerActivo) {
      if (checkTrigger()) {
        // Enviar datos cuando se activa el trigger
        sendDataToPC();
      }
    } else {
      // Sin trigger, enviar datos continuamente
      sendDataToPC();
    }
  }
  
  // Pequeña pausa para no saturar el puerto serie
  delayMicroseconds(100);
}
