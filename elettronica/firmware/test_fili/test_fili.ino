// Test fili.
// 1) pull-down interno: se un pin legge 1, il filo arriva a un OLED alimentato (le sue resistenze lo tirano su).
// 2) corti: porta a 0 un pin alla volta e guarda se un altro scende con lui (vuol dire che sono collegati insieme).
const int P[] = { 21, 19, 17, 22 };
void setup() { Serial.begin(115200); }
void loop() {
  for (int p : P) pinMode(p, INPUT_PULLDOWN);
  delay(5);
  Serial.print("LIVELLI ");
  for (int p : P) Serial.printf("GPIO%d=%d  ", p, digitalRead(p));
  Serial.println();
  for (int a : P) {
    for (int p : P) pinMode(p, INPUT_PULLUP);
    pinMode(a, OUTPUT); digitalWrite(a, LOW);
    delay(5);
    Serial.printf("CORTO %d a 0 ->", a);
    for (int b : P) if (b != a && digitalRead(b) == 0) Serial.printf(" scende %d", b);
    Serial.println();
  }
  for (int p : P) pinMode(p, INPUT);
  delay(2000);
}
