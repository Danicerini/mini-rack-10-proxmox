// Test OLED dal vivo: ogni secondo prova SDA 21, 19 e 17 (SCL 22 per tutti).
// Ogni OLED che risponde si accende bianco con scritto su quale filo e' (e per quale PC).
// Puoi spostare i fili con l'ESP acceso: appena un collegamento e' giusto, l'OLED si accende.
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

const int SDA_P[3] = { 21, 19, 17 };
const char* NOME[3] = { "pve1", "pve2", "pve3" };
Adafruit_SSD1306 d(128, 64, &Wire, -1);

void setup() { Serial.begin(115200); delay(300); Serial.println("TEST OLED DAL VIVO"); }

void loop() {
  for (int i = 0; i < 3; i++) {
    Wire.begin(SDA_P[i], 22, 100000);
    Wire.beginTransmission(0x3C);
    bool ok = Wire.endTransmission() == 0;
    Serial.printf("SDA %d (%s): %s\n", SDA_P[i], NOME[i], ok ? "risponde" : "niente");
    if (ok) {
      d.begin(SSD1306_SWITCHCAPVCC, 0x3C, true, false);
      d.clearDisplay(); d.fillRect(0, 0, 128, 64, SSD1306_WHITE);
      d.setTextColor(SSD1306_BLACK); d.setTextSize(2);
      d.setCursor(4, 10); d.print(NOME[i]);
      d.setCursor(4, 38); d.printf("GPIO %d", SDA_P[i]);
      d.display();
    }
    Wire.end();
    pinMode(SDA_P[i], INPUT_PULLUP);
  }
  delay(1000);
}
