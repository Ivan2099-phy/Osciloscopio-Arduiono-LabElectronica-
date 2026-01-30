
bool channelActive1 = true;
bool channelActive2 = true;
bool channelActive3 = true;
bool medir = false;

bool TriggerActivo = false;
float TriggerNivel = 2.0; // Voltaje del trigger

operationActive = true; // Ejemplo: Operación activa
VariableTiempo = 1000; // Ejemplo: Tiempo en microsegundos

// Valores de voltaje de los canales
float vCH[];
float resultOP; // Resultado de la operación (suma/resta)

"""
Función lectura de canales:
    ""Lee los valores de los canales activos y los guarda en vCH de 0 a 5 volts""

"""

void readChanels() {
    if (channelActive1) vCH[0] = analogRead(A0) * (5.0 / 1023.0);
    if (channelActive2) vCH[1] = analogRead(A1) * (5.0 / 1023.0);
    if (channelActive3) vCH[2] = analogRead(A2) * (5.0 / 1023.0);
}

"""
Función operación canales:
    ""Realiza la operación (suma(operationMode==1)/resta(operationMode==2)) entre los canales activos y guarda el resultado en resultOP""
"""
void doOperation() {
    
}   
 


"""
Función para mandar los datos de arduino a pc:
    ""Manda los datos a formato csv""
    Ejemplo : DATA = [time, CH1, CH2, CH3]
"""

void send_data_to_pc(DATA):
// Enviar datos en formato CSV a través del puerto serie
    // Vamos a printar  "Data: (time, CH1, CH2, CH3)s"
    Serial.print("DATA: ");
    // Tiempo en microsegundos
    Serial.print(VariableTiempo);
    Serial.print(",");

    // Canal 1
    if (channelActive1) Serial.print(vCH[0]); // Si el canal está activo, envía el valor de voltaje
    else Serial.print("nan");                   // Si no está activo, envía "nan"
    Serial.print(",");                          

    // Canal 2
    if (channelActive2) Serial.print(vCH[1]);
    else Serial.print("nan");
    Serial.print(",");

    // Canal 3
    if (channelActive3) Serial.print(vCH[2]);
    else Serial.print("nan");
    Serial.print(",");

    // Resultado de operación (suma/resta)
    if (operationActive) Serial.println(resultOP);
    else Serial.println("nan");
}


"""
Función para interpretar los comandos de Serial:
    ""Interpreta los comandos recibidos por Serial para activar/desactivar canales, iniciar/parar medición, y configurar trigger""
"""

void interpretSerialCommands() {
    if (Serial.available() > 0) {
        String command = Serial.readStringUntil('\n');
        // Medir ON/OFF
        if (command == "START") {
            medir = true;
            Serial.println("OK: INICIO DE MEDICIÓN")
        } else if (command == "STOP") {
            medir = false;
            Serial.println("OK: MEDICIÓN DETENIDA   ")

        // Configuración de trigger
       
        // Activar/Desactivar canales
          else if (cmd.startsWith("CH1 ")) {
        channelActive1 = cmd.endsWith("ON");
        }
          else if (cmd.startsWith("CH2 ")) {
            channelActive2 = cmd.endsWith("ON");
        }
          else if (cmd.startsWith("CH3 ")) {
            channelActive3 = cmd.endsWith("ON");
        }

        // Operación entre canales
        else if (cmd.startsWith("OP ADD")) {
            operationActive = true;
            operationMode = 1;
            Serial.println("OK: OPERATION ADD");
        }
        else if (cmd.startsWith("OP SUB")) {
            operationActive = true;
            operationMode = 2;
            Serial.println("OK: OPERATION SUB");
        }
        else if (cmd.startsWith("OP OFF")) {
            operationActive = false;
            Serial.println("OK: OPERATION OFF");
        }

    }
}

"""
Función loop principal:
    ""Bucle principal que interpreta comandos, lee canales, verifica trigger, realiza operación y envía datos a PC""
"""

void loop() {
    if (medir) {
            interpretarComandos();
            leerCanales();
            // trigger
            calcularOperacion();
            send_data_to_pc();

            delay(VariableTiempo);
    }
}
