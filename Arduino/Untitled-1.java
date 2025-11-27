"""
Función para mandar los datos de arduino a pc:
    ""Manda los datos a formato csv""
    Ejemplo : DATA = [time, CH1, CH2, CH3]

"""
channelActive1 = true; // Ejemplo: Canal 1 activo
channelActive2 = false; // Ejemplo: Canal 2 inactivo
channelActive3 = true; // Ejemplo: Canal 3 activo
operationActive = true; // Ejemplo: Operación activa
VariableTiempo = 1000; // Ejemplo: Tiempo en microsegundos

void send_data_to_pc(DATA):
// Enviar datos en formato CSV a través del puerto serie
    // Vamos a printar  "Data: (time, CH1, CH2, CH3)"
    serial.print("DATA: ");
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






