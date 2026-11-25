const int PIN_LED = 8;
const int PIN_BOTON = 2;

const int TOTAL_RONDAS = 5;
int rondaActual = 0;
long puntosTotales = 0;
unsigned long mejorTiempo = 999999;

void setup() {
  Serial.begin(9600);
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_BOTON, INPUT_PULLUP);
  digitalWrite(PIN_LED, LOW);
  randomSeed(analogRead(A0));

  Serial.println("=== REFLEX CHALLENGE ===");
  Serial.println("Presiona el BOTON o envia 'S' para iniciar.");
}

void loop() {
  bool iniciarDesdeSerial = false;
  if (Serial.available() > 0) {
    char c = Serial.read();
    if (c == 'S' || c == 's') {
      iniciarDesdeSerial = true;
    }
  }

  if (iniciarDesdeSerial || digitalRead(PIN_BOTON) == LOW) {
    delay(250);
    while (digitalRead(PIN_BOTON) == LOW) {}
    jugarPartidaCompleta();
  }
}

void parpadearInicio() {
  Serial.println("Iniciando en 3, 2, 1...");
  for (int i = 0; i < 3; i++) {
    digitalWrite(PIN_LED, HIGH);
    delay(250);
    digitalWrite(PIN_LED, LOW);
    delay(250);
  }
  delay(400);
}

void jugarPartidaCompleta() {
  rondaActual = 0;
  puntosTotales = 0;
  mejorTiempo = 999999;

  parpadearInicio();

  for (rondaActual = 1; rondaActual <= TOTAL_RONDAS; rondaActual++) {
    Serial.print("\n--- Ronda ");
    Serial.print(rondaActual);
    Serial.print("/");
    Serial.print(TOTAL_RONDAS);
    Serial.println(" ---");
    Serial.println("Preparate...");

    digitalWrite(PIN_LED, LOW);
    long espera = random(1500, 4000);
    unsigned long inicioEspera = millis();
    bool seAdelanto = false;

    while (millis() - inicioEspera < espera) {
      if (digitalRead(PIN_BOTON) == LOW) {
        seAdelanto = true;
        break;
      }
    }

    if (seAdelanto) {
      Serial.println("¡TE ADELANTASTE! 0 puntos en esta ronda.");
      while (digitalRead(PIN_BOTON) == LOW) {}
      delay(800);
      continue;
    }

    digitalWrite(PIN_LED, HIGH);
    Serial.println("¡AHORA! PRESIONA EL BOTON");
    unsigned long tiempoInicio = millis();

    while (digitalRead(PIN_BOTON) == HIGH) {}

    unsigned long ms = millis() - tiempoInicio;
    digitalWrite(PIN_LED, LOW);

    long puntos = 1000 - (long)ms;
    if (puntos < 0) puntos = 0;
    puntosTotales += puntos;

    if (ms < mejorTiempo) {
      mejorTiempo = ms;
    }

    Serial.print("TIEMPO:");
    Serial.print(ms);
    Serial.print(" ms | Puntos: +");
    Serial.print(puntos);
    Serial.print(" | Total: ");
    Serial.println(puntosTotales);

    while (digitalRead(PIN_BOTON) == LOW) {}
    delay(1000);
  }

  Serial.println("\n=== JUEGO FINALIZADO ===");
  Serial.print("Puntaje Total: ");
  Serial.println(puntosTotales);
  Serial.print("Mejor Tiempo: ");
  if (mejorTiempo == 999999) {
    Serial.println("---");
  } else {
    Serial.print(mejorTiempo);
    Serial.println(" ms");
  }
  Serial.println("\nPresiona el BOTON para jugar de nuevo.");
}
