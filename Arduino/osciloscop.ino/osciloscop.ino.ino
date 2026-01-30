// Definición de variables globales
bool channelActive1 = true;  // Controla si el canal 1 está habilitado para medición
bool channelActive2 = true;  // Controla si el canal 2 está habilitado para medición
bool channelActive3 = true;  // Controla si el canal 3 está habilitado para medición
bool medir = false;  // Bandera principal que indica si el sistema está en modo de medición
bool operationActive = false;  // Indica si hay una operación matemática activa (suma/resta)
bool triggerActivo = false;  // Habilita/deshabilita el sistema de trigger
bool triggerDetenido = false;  // Evita retriggering, se activa después de disparar
int operationMode = 0; // 0: ninguna, 1: suma, 2: resta - Define el tipo de operación
float triggerNivel = 2.5; // Voltaje del trigger - Valor umbral para el disparo
String triggerDireccion = "ARRIBA"; // "ARRIBA" o "ABAJO" - Define si el trigger es en flanco ascendente o descendente

// Valores de voltaje de los canales - Array que almacena las lecturas actuales
float vCH[3] = {0.0, 0.0, 0.0};
float resultOP = 0.0; // Resultado de la operación (suma/resta) - Se calcula en cada ciclo

// Variables para el tiempo - Controlan el timestamp de las mediciones
unsigned long tiempoInicio = 0;  // Marca de tiempo inicial (microsegundos)
unsigned long ultimoTiempo = 0;  // No se usa actualmente, podría ser para delta time
unsigned long tiempoActual = 0;  // Tiempo transcurrido desde inicio de medición

void setup() {
  Serial.begin(115200);  // Inicia comunicación serial a alta velocidad
  while (!Serial) {
    ; // Esperar a que se conecte el puerto serie - Importante para Arduino Leonardo/Micro
  }
  tiempoInicio = micros();  // Inicializa el contador de tiempo
}

// Lee los canales analógicos habilitados y convierte a voltaje
void readChannels() {
  // Lectura del canal 1 (pin A0) si está activo, si no se asigna NAN (Not a Number)
  if (channelActive1) vCH[0] = analogRead(A0) * (5.0 / 1023.0);  // Conversión ADC (10-bit) a voltaje (0-5V)
  else vCH[0] = NAN;  // NAN indica que el canal está deshabilitado
  
  // Mismo proceso para canal 2 (pin A1)
  if (channelActive2) vCH[1] = analogRead(A1) * (5.0 / 1023.0);
  else vCH[1] = NAN;
  
  // Mismo proceso para canal 3 (pin A2)
  if (channelActive3) vCH[2] = analogRead(A2) * (5.0 / 1023.0);
  else vCH[2] = NAN;
}

// Realiza operaciones matemáticas con los canales activos
void doOperation() {
  if (!operationActive) {
    resultOP = NAN;  // Si no hay operación activa, resultado es NAN
    return;
  }
  
  float suma = 0.0;
  int canalesActivos = 0;  // Contador para seguimiento (aunque no se usa luego)
  
  // Calcular suma de canales activos - solo suma canales habilitados y válidos
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
  
  if (operationMode == 1) { // SUMA - Suma algebraica de todos los canales
    resultOP = suma;
  } else if (operationMode == 2) { // RESTA (CH1 - CH2 - CH3) - Resta secuencial desde CH1
    resultOP = vCH[0];  // Siempre parte del canal 1
    if (channelActive2 && !isnan(vCH[1])) resultOP -= vCH[1];
    if (channelActive3 && !isnan(vCH[2])) resultOP -= vCH[2];
  }
}

// Verifica condiciones de trigger - retorna true solo en el flanco de disparo
bool checkTrigger() {
  if (!triggerActivo) return false;  // Trigger deshabilitado
  
  float valorTrigger = 0.0;
  
  // Determinar qué canal usar para trigger - prioridad: CH1 > CH2 > CH3
  // Usa el primer canal activo disponible
  if (channelActive1 && !isnan(vCH[0])) valorTrigger = vCH[0];
  else if (channelActive2 && !isnan(vCH[1])) valorTrigger = vCH[1];
  else if (channelActive3 && !isnan(vCH[2])) valorTrigger = vCH[2];
  else return false;  // Ningún canal disponible para trigger
  
  // Lógica de trigger con detección de flanco
  if (triggerDireccion == "ARRIBA") {
    // Trigger en flanco ascendente (cuando sube por encima del umbral)
    if (valorTrigger > triggerNivel) {
      if (!triggerDetenido) {
        triggerDetenido = true;  // Activa bandera para evitar retrigger
        return true; // Trigger activado - solo retorna true una vez por flanco
      }
      return false;
    } else {
      triggerDetenido = false;  // Reset cuando baja del umbral
      return false;
    }
  } else { // ABAJO - flanco descendente
    if (valorTrigger < triggerNivel) {
      if (!triggerDetenido) {
        triggerDetenido = true;
        return true; // Trigger activado
      }
      return false;
    } else {
      triggerDetenido = false;  // Reset cuando sube del umbral
      return false;
    }
  }
}

// Envía datos formateados al PC por puerto serie
void sendDataToPC() {
  tiempoActual = micros() - tiempoInicio;  // Calcula tiempo transcurrido desde inicio
  
  // Formato: DATA:tiempo,canal1,canal2,canal3,operacion
  Serial.print("DATA:");
  Serial.print(tiempoActual);
  Serial.print(",");
  
  // Canal 1 - envía valor o "NAN" si está deshabilitado
  if (channelActive1 && !isnan(vCH[0])) {
    Serial.print(vCH[0], 4);  // 4 decimales de precisión
  } else {
    Serial.print("NAN");  // Marcador de canal no disponible
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
  
  // Operación matemática
  if (operationActive && !isnan(resultOP)) {
    Serial.print(resultOP, 4);
  } else {
    Serial.print("NAN");
  }
  Serial.println();  // Fin de línea
}

// Procesa comandos recibidos por puerto serie
void interpretSerialCommands() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();  // Elimina espacios y saltos de línea
    
    // START/STOP - control principal de medición
    if (command == "START") {
      medir = true;
      triggerDetenido = false;  // Reinicia estado del trigger
      tiempoInicio = micros();  // Reinicia contador de tiempo
      Serial.println("OK:INICIO_MEDICION");
    } 
    else if (command == "STOP") {
      medir = false;
      Serial.println("OK:MEDICION_DETENIDA");
    }
    
    // Configuración de canales - comandos para habilitar/deshabilitar
    else if (command.startsWith("CH1_ON")) {
      channelActive1 = true;
      Serial.println("OK:CH1_ON");
    }
    else if (command.startsWith("CH1_OFF")) {
      channelActive1 = false;
      Serial.println("OK:CH1_OFF");
    }
    // ... comandos similares para CH2 y CH3
    
    // Operaciones matemáticas
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
    
    // Configuración de trigger
    else if (command.startsWith("TRIGGER_ON")) {
      triggerActivo = true;
      Serial.println("OK:TRIGGER_ON");
    }
    else if (command.startsWith("TRIGGER_OFF")) {
      triggerActivo = false;
      Serial.println("OK:TRIGGER_OFF");
    }
    else if (command.startsWith("TRIGGER_NIVEL")) {
      // Extrae el valor numérico después de "TRIGGER_NIVEL"
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
    
    // Comando de estado - reporta configuración actual
    else if (command == "STATUS") {
      Serial.print("STATUS:");
      // Canales (1=activo, 0=inactivo)
      Serial.print(channelActive1 ? "1" : "0");
      Serial.print(channelActive2 ? "1" : "0");
      Serial.print(channelActive3 ? "1" : "0");
      Serial.print(",");
      // Modo medición
      Serial.print(medir ? "1" : "0");
      Serial.print(",");
      // Operación (0=nada, 1=suma, 2=resta)
      Serial.print(operationActive ? operationMode : "0");
      Serial.print(",");
      // Trigger
      Serial.print(triggerActivo ? "1" : "0");
      Serial.println();
    }
  }
}

void loop() {
  interpretSerialCommands();  // Primero procesa comandos entrantes
  
  if (medir) {
    readChannels();   // Lee entradas analógicas
    doOperation();    // Calcula operaciones si están activas
    
    // Verificar trigger
    if (triggerActivo) {
      // Modo con trigger: solo envía datos cuando se dispara
      if (checkTrigger()) {
        sendDataToPC();
      }
    } else {
      // Modo sin trigger: envía datos continuamente
      sendDataToPC();
    }
  }
  
  // Pequeña pausa para no saturar el puerto serie
  // 100µs de delay ayuda a estabilizar las lecturas ADC
  delayMicroseconds(100);
}
