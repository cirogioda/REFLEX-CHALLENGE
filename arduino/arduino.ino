const int PIN_LED = 8;
const int PIN_BOTON = 2;

void setup() {
  Serial.begin(9600);
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_BOTON, INPUT_PULLUP);
  digitalWrite(PIN_LED, LOW);
  randomSeed(analogRead(A0));
}

void loop() {
  if (Serial.available() > 0) {
    char c = Serial.read();
    if (c == 'P' || c == 'p') {
      parpadearLargada();
      jugarUnaRonda();
    } else if (c == 'S' || c == 's') {
      jugarUnaRonda();
    }
  }
}

void parpadearLargada() {
  for (int i = 1; i <= 3; i++) {
    digitalWrite(PIN_LED, HIGH);
    Serial.print("PARPADEO:");
    Serial.println(i);
    delay(400);
    digitalWrite(PIN_LED, LOW);
    Serial.println("PARPADEO_OFF");
    delay(400);
  }
}

void jugarUnaRonda() {
  digitalWrite(PIN_LED, LOW);
  Serial.println("ESPERANDO");

  long espera = random(1500, 4000);
  unsigned long inicioEspera = millis();

  while (millis() - inicioEspera < espera) {
    if (digitalRead(PIN_BOTON) == LOW) {
      Serial.println("FALSA");
      while (digitalRead(PIN_BOTON) == LOW) {}
      delay(50);
      return;
    }
  }

  digitalWrite(PIN_LED, HIGH);
  Serial.println("LED_ON");
  unsigned long tiempoInicio = millis();

  while (digitalRead(PIN_BOTON) == HIGH) {}

  unsigned long ms = millis() - tiempoInicio;
  digitalWrite(PIN_LED, LOW);

  Serial.print("TIEMPO:");
  Serial.println(ms);

  while (digitalRead(PIN_BOTON) == LOW) {}
  delay(50);
}
