/*
 * Cluster Completo (v2) - plancia del rack: TFT 2.4" + 3 OLED (uno per PC) + PIR + barra 10 LED + joystick
 * Scheda: ESP32 DevKit (WROOM), collegato via USB a pve1. Dati: riga JSON ogni 5 s sulla seriale (115200)
 * dal servizio cluster-status di pve1, uguale alla v1.
 * La v1 (solo TFT) resta in display_esp32/cluster_display.ino.  Schema: display_esp32/v2_completo/Schema_collegamenti.pdf
 *
 * PIN
 *  TFT ST7789 : CS 5, RESET 4, DC 16, MOSI 23, SCK 18, LED 25 (luminosita' PWM; -1 = LED fisso su 3V3)
 *  OLED x3    : SCL comune 22; SDA pve1 21, pve2 19, pve3 17 (tutti 0x3C: si parla a uno alla volta)
 *  74HC595 x2 : DS 13, SH_CP 14, ST_CP 27, OE 15 (luminosita'), MR su 3V3; Q7' del primo -> DS del secondo
 *  PIR        : OUT 39 (HC-SR501 alimentato a 5V, l'uscita e' a 3.3V)
 *  Joystick   : VRx 34, VRy 35, SW 33 (alimentato a 3V3, NON a 5V)
 */
#define LGFX_USE_V1
#include <LovyanGFX.hpp>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// ---------------- Configurazione ----------------
#define PIN_TFT_BL    25      // -1 se il filo LED del TFT resta su 3V3
#define PIN_SCL       22
static const int   OLED_SDA[3]  = { 21, 19, 17 };
static const char* OLED_NODE[3] = { "pve1", "pve2", "pve3" };
#define PIN_SR_DATA   13
#define PIN_SR_CLK    14
#define PIN_SR_LATCH  27
#define PIN_SR_OE     15
#define PIN_PIR       39
#define USE_PIR       1       // 0 se il PIR non e' collegato (schermi sempre accesi)
#define PIN_JOY_X     34
#define PIN_JOY_Y     35
#define PIN_JOY_SW    33
#define USE_JOY       1       // 0 se il joystick non e' collegato
#define JOY_INVERT_X  0       // 1 se destra e sinistra sono al contrario
#define SCREEN_OFF_MS (10UL * 1000UL)          // PROVA: 10 s. Normale: (5UL * 60UL * 1000UL) = 5 minuti
#define BRIGHT_TFT    255     // 0..255
#define BRIGHT_BAR    120     // 0..255
#define BAR_REVERSED  0       // 1 se la barra si riempie dall'alto invece che dal basso

bool pageLocked = false;      // click del joystick: ferma lo scorrimento automatico

// ---------------- Display ----------------
class LGFX : public lgfx::LGFX_Device {
  lgfx::Panel_ST7789  _panel;
  lgfx::Bus_SPI       _bus;
public:
  LGFX() {
    { auto cfg = _bus.config();
      cfg.spi_host = SPI3_HOST; cfg.spi_mode = 0;
      cfg.freq_write = 20000000; cfg.freq_read = 8000000;
      cfg.spi_3wire = false; cfg.use_lock = true; cfg.dma_channel = SPI_DMA_CH_AUTO;
      cfg.pin_sclk = 18; cfg.pin_mosi = 23; cfg.pin_miso = -1; cfg.pin_dc = 16;   // il 19 serve all'OLED di pve2
      _bus.config(cfg); _panel.setBus(&_bus); }
    { auto cfg = _panel.config();
      cfg.pin_cs = 5; cfg.pin_rst = 4; cfg.pin_busy = -1;
      cfg.panel_width = 240; cfg.panel_height = 320;
      cfg.offset_rotation = 0; cfg.readable = false; cfg.invert = false;   // SDO del display non collegato
      cfg.rgb_order = false; cfg.dlen_16bit = false; cfg.bus_shared = true;
      _panel.config(cfg); }
    setPanel(&_panel);
  }
};

LGFX lcd;
LGFX_Sprite cv(&lcd);

// ---------------- Tema scuro ----------------
static constexpr uint32_t C_BG    = 0x05070Du;
static constexpr uint32_t C_CARD  = 0x0F1726u;
static constexpr uint32_t C_CARD2 = 0x162034u;
static constexpr uint32_t C_LINE  = 0x243049u;
static constexpr uint32_t C_TEXT  = 0xF1F5F9u;
static constexpr uint32_t C_DIM   = 0x7C8BA6u;
static constexpr uint32_t C_ACC   = 0x22D3EEu;
static constexpr uint32_t C_OK    = 0x34D399u;
static constexpr uint32_t C_WARN  = 0xFBBF24u;
static constexpr uint32_t C_BAD   = 0xF87171u;
static constexpr uint32_t C_VIO   = 0xA78BFAu;

// ---------------- Dati ----------------
struct Node  { String name; bool online; int cpu; int cores; float mem; float memt; long up; int temp; int link; };
struct Guest { int id; String name; bool ct; bool on; String node; };

Node  nodes[4];   int nNodes = 0;
Guest guests[24]; int nGuests = 0;
String clusterName = "?", votes = "?", expectedVotes = "?", srvTime = "--:--";
bool quorate = false;
int onCount = 0, total = 0;
bool hasBackup = false, bkOk = false; String bkWhen = ""; int bkFiles = 0;
bool dataOk = false; unsigned long lastOkMs = 0; unsigned long packets = 0;

const int PAGES = 4;
const char* PAGE_NAMES[PAGES] = { "Panoramica", "Nodi", "Macchine", "Backup e rete" };
int page = 0;
unsigned long lastPageChange = 0, lastButton = 0;
String rxLine;

// ---------------- Seriale ----------------
void parseStatus(const String& line) {
  JsonDocument doc;
  if (deserializeJson(doc, line) || !doc["ok"].as<bool>()) return;
  clusterName   = doc["cluster"] | "?";
  quorate       = doc["quorate"] | false;
  votes         = doc["votes"] | "?";
  expectedVotes = doc["expected"] | "?";
  srvTime       = doc["time"] | "--:--";
  onCount       = doc["on"] | 0;
  total         = doc["total"] | 0;
  nNodes = 0;
  for (JsonObject n : doc["nodes"].as<JsonArray>()) {
    if (nNodes >= 4) break;
    Node& d = nodes[nNodes++];
    d.name = n["name"] | "?"; d.online = n["online"] | false;
    d.cpu = n["cpu"] | 0; d.cores = n["cores"] | 0;
    d.mem = n["mem"] | 0.0f; d.memt = n["memt"] | 0.0f; d.up = n["up"] | 0L;
    d.temp = n["temp"].isNull() ? -1 : n["temp"].as<int>();
    d.link = n["link"].isNull() ? 0 : n["link"].as<int>();
  }
  nGuests = 0;
  // prima le accese, poi le spente
  for (int pass = 0; pass < 2; pass++)
    for (JsonObject g : doc["guests"].as<JsonArray>()) {
      bool on = g["on"] | false;
      if ((pass == 0) != on || nGuests >= 24) continue;
      Guest& d = guests[nGuests++];
      d.id = g["id"] | 0; d.name = g["name"] | "";
      d.ct = String((const char*)(g["type"] | "vm")) == "ct";
      d.on = on; d.node = g["node"] | "";
    }
  hasBackup = !doc["backup"].isNull();
  if (hasBackup) {
    bkWhen = doc["backup"]["when"] | ""; bkFiles = doc["backup"]["files"] | 0; bkOk = doc["backup"]["ok"] | false;
  }
  dataOk = true; lastOkMs = millis(); packets++;
}

void readSerial() {
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\n') {
      rxLine.trim();
      if (rxLine.startsWith("{")) parseStatus(rxLine);
      rxLine = "";
    } else if (c != '\r' && rxLine.length() < 6000) rxLine += c;
  }
}

// ---------------- Disegno ----------------
uint32_t tempColor(int t) { if (t < 0) return C_DIM; if (t >= 80) return C_BAD; if (t >= 65) return C_WARN; return C_OK; }
uint32_t pctColor(int p)  { if (p >= 85) return C_BAD; if (p >= 60) return C_WARN; return C_ACC; }
bool fresh() { return dataOk && millis() - lastOkMs < 30000; }

String fmtUp(long s) {
  if (s <= 0) return "-";
  long d = s / 86400, h = (s % 86400) / 3600, m = (s % 3600) / 60;
  if (d > 0) return String(d) + "g " + String(h) + "h";
  if (h > 0) return String(h) + "h " + String(m) + "m";
  return String(m) + "m";
}
String fmtWhen(const String& w) {   // "2026-11-10-1711" -> "10/11 17:11"
  if (w.length() < 15) return w;
  return w.substring(8, 10) + "/" + w.substring(5, 7) + " " + w.substring(11, 13) + ":" + w.substring(13, 15);
}

void card(int x, int y, int w, int h) { cv.fillRoundRect(x, y, w, h, 10, C_CARD); }

void bar(int x, int y, int w, int h, int pct, uint32_t col) {
  pct = constrain(pct, 0, 100);
  cv.fillRoundRect(x, y, w, h, h / 2, C_LINE);
  int fw = (w * pct) / 100;
  if (fw > 0) cv.fillRoundRect(x, y, max(fw, h), h, h / 2, col);
}

// Indicatore circolare a 270 gradi
void gauge(int cx, int cy, int r, int th, int pct, uint32_t col, const String& value, const char* label) {
  pct = constrain(pct, 0, 100);
  cv.fillArc(cx, cy, r, r - th, 135, 405, C_LINE);
  if (pct > 0) cv.fillArc(cx, cy, r, r - th, 135, 135 + 270 * pct / 100, col);
  // valore centrato otticamente: posizionato sulla linea di base, simbolo del grado incluso nella larghezza
  cv.setFont(&fonts::FreeSansBold9pt7b); cv.setTextColor(C_TEXT);
  String v = value; bool deg = v.endsWith("C");
  if (deg) v.remove(v.length() - 1);
  int w = cv.textWidth(v), extra = deg ? 7 : 0;
  int left = cx - (w + extra) / 2;
  const int capH = 12;
  cv.setTextDatum(textdatum_t::baseline_left);
  cv.drawString(v, left, cy + capH / 2);
  if (deg) cv.drawCircle(left + w + 4, cy - capH / 2 + 2, 2, C_TEXT);
  cv.setFont(&fonts::Font0); cv.setTextColor(C_DIM); cv.setTextDatum(textdatum_t::middle_center);
  cv.drawString(label, cx, cy + r - 4);
}

// Temperatura con simbolo del grado, allineata a destra in (xr, yc)
void tempRight(int t, int xr, int yc) {
  cv.setFont(&fonts::Font2); cv.setTextDatum(textdatum_t::middle_right); cv.setTextColor(tempColor(t));
  if (t < 0) { cv.drawString("-", xr, yc); return; }
  cv.drawString(String(t), xr - 6, yc);
  cv.drawCircle(xr - 2, yc - 4, 2, tempColor(t));
}

void pill(int x, int y, const String& txt, uint32_t col) {
  cv.setFont(&fonts::Font2);
  int w = cv.textWidth(txt) + 16;
  cv.fillRoundRect(x, y, w, 20, 10, col);
  cv.setTextColor(C_BG); cv.setTextDatum(textdatum_t::middle_center);
  cv.drawString(txt, x + w / 2, y + 10);
}

void header() {
  cv.setFont(&fonts::FreeSansBold9pt7b); cv.setTextColor(C_TEXT); cv.setTextDatum(textdatum_t::middle_left);
  cv.drawString(PAGE_NAMES[page], 12, 16);
  cv.setFont(&fonts::Font2);
  bool f = fresh();
  cv.setTextDatum(textdatum_t::middle_right);
  cv.setTextColor(f ? C_DIM : C_BAD);
  cv.drawString(f ? srvTime : String("offline"), 292, 16);
  cv.fillCircle(304, 16, 4, f ? C_OK : C_BAD);
  cv.drawFastHLine(12, 32, 296, C_LINE);
}

void footer() {
  for (int i = 0; i < PAGES; i++) {
    int x = 160 - (PAGES - 1) * 9 + i * 18;
    if (i == page) cv.fillRoundRect(x - 7, 229, 14, 5, 2, C_ACC); else cv.fillCircle(x, 231, 2, C_LINE);
  }
  if (pageLocked) {
    cv.setFont(&fonts::Font0); cv.setTextColor(C_WARN); cv.setTextDatum(textdatum_t::middle_right);
    cv.drawString("FERMA", 312, 231);
  }
}

void pageOverview() {
  // Macchine accese: anello grande
  card(8, 40, 140, 132);
  int pct = total > 0 ? 100 * onCount / total : 0;
  gauge(78, 102, 50, 9, pct, C_ACC, String(onCount) + "/" + String(total), "MACCHINE ACCESE");
  // Quorum
  card(156, 40, 156, 62);
  cv.setFont(&fonts::Font2); cv.setTextColor(C_DIM); cv.setTextDatum(textdatum_t::top_left);
  cv.drawString("QUORUM", 168, 48);
  pill(168, 72, quorate ? "OK" : "PERSO", quorate ? C_OK : C_BAD);
  cv.setTextColor(C_DIM); cv.setTextDatum(textdatum_t::middle_left);
  cv.drawString("voti " + votes + "/" + expectedVotes, 232, 82);
  // Backup
  card(156, 110, 156, 62);
  cv.setTextColor(C_DIM); cv.setTextDatum(textdatum_t::top_left);
  cv.drawString("BACKUP DB", 168, 118);
  if (hasBackup) {
    pill(168, 142, bkOk ? "OK" : "KO", bkOk ? C_OK : C_BAD);
    cv.setTextColor(C_TEXT); cv.setTextDatum(textdatum_t::middle_left);
    cv.drawString(fmtWhen(bkWhen), 214, 152);
  } else {
    pill(168, 142, "pve2 offline", C_WARN);
  }
  // Nodi (2 o 3 schede affiancate)
  int y = 180, cnt = min(nNodes, 3);
  int w = cnt > 0 ? (304 - (cnt - 1) * 8) / cnt : 304;
  for (int i = 0; i < cnt; i++) {
    Node& n = nodes[i];
    int x = 8 + i * (w + 8);
    card(x, y, w, 42);
    cv.fillCircle(x + 12, y + 13, 4, n.online ? C_OK : C_BAD);
    cv.setFont(&fonts::FreeSansBold9pt7b); cv.setTextColor(C_TEXT); cv.setTextDatum(textdatum_t::middle_left);
    cv.drawString(n.name, x + 21, y + 13);
    cv.setFont(&fonts::Font2); cv.setTextDatum(textdatum_t::middle_right);
    if (n.online) {
      tempRight(n.temp, x + w - 6, y + 13);
      bar(x + 10, y + 28, w - 20, 6, n.cpu, pctColor(n.cpu));
    } else {
      cv.setTextColor(C_BAD); cv.drawString("off", x + w - 8, y + 13);
      bar(x + 10, y + 28, w - 20, 6, 0, C_LINE);
    }
  }
}

void pageNodes() {
  int cnt = min(nNodes, 3);
  bool compact = cnt >= 3;
  int h = compact ? 58 : 88, gap = 6, y = 40;
  for (int i = 0; i < cnt; i++) {
    Node& n = nodes[i];
    card(8, y, 304, h);
    if (!compact) {
      cv.fillCircle(22, y + 14, 4, n.online ? C_OK : C_BAD);
      cv.setFont(&fonts::FreeSansBold9pt7b); cv.setTextColor(C_TEXT); cv.setTextDatum(textdatum_t::middle_left);
      cv.drawString(n.name, 32, y + 14);
      cv.setFont(&fonts::Font2); cv.setTextColor(C_DIM); cv.setTextDatum(textdatum_t::middle_right);
      cv.drawString(n.online ? ("acceso da " + fmtUp(n.up)) : String("spento"), 302, y + 14);
    }
    if (n.online) {
      int r = compact ? 22 : 28, th = compact ? 5 : 6;
      int gy = compact ? y + 30 : y + 56;
      int g1 = compact ? 112 : 52, g2 = compact ? 166 : 122;
      if (compact) {
        cv.fillCircle(20, y + 15, 4, C_OK);
        cv.setFont(&fonts::FreeSansBold9pt7b); cv.setTextColor(C_TEXT); cv.setTextDatum(textdatum_t::middle_left);
        cv.drawString(n.name, 30, y + 15);
        cv.setFont(&fonts::Font0); cv.setTextColor(C_DIM);
        cv.drawString(fmtUp(n.up), 30, y + 36);
      }
      gauge(g1, gy, r, th, n.cpu, pctColor(n.cpu), String(n.cpu) + "%", "CPU");
      gauge(g2, gy, r, th, n.temp < 0 ? 0 : n.temp, tempColor(n.temp), n.temp >= 0 ? String(n.temp) + "C" : String("-"), "TEMP");
      int mp = n.memt > 0 ? (int)(100 * n.mem / n.memt) : 0;
      int rx = compact ? 200 : 168, rw = 300 - rx, ry = compact ? y + 10 : y + 34;
      cv.setFont(&fonts::Font2); cv.setTextDatum(textdatum_t::top_left);
      cv.setTextColor(C_DIM); cv.drawString("RAM", rx, ry);
      cv.setTextColor(C_TEXT); cv.setTextDatum(textdatum_t::top_right);
      cv.drawString(String(n.mem, 1) + "/" + String((int)(n.memt + 0.5)) + "G", 300, ry);
      bar(rx, ry + 20, rw, 8, mp, pctColor(mp));
      if (!compact) {
        cv.setTextDatum(textdatum_t::top_left); cv.setTextColor(C_DIM);
        cv.drawString(String(n.cores) + " core  " + (n.link > 0 ? String(n.link) + " Mb/s" : String("")), rx, ry + 34);
      }
    } else if (compact) {
      cv.fillCircle(20, y + 15, 4, C_BAD);
      cv.setFont(&fonts::FreeSansBold9pt7b); cv.setTextColor(C_TEXT); cv.setTextDatum(textdatum_t::middle_left);
      cv.drawString(n.name, 30, y + 15);
      cv.setFont(&fonts::Font2); cv.setTextColor(C_BAD); cv.drawString("spento / non raggiungibile", 110, y + 29);
    }
    y += h + gap;
  }
}

void guestRow(Guest& g, int x, int y) {
  cv.fillRoundRect(x, y, 148, 20, 6, g.on ? C_CARD2 : C_CARD);
  cv.fillCircle(x + 10, y + 10, 3, g.on ? C_OK : C_LINE);
  cv.setTextDatum(textdatum_t::middle_left);
  cv.setTextColor(g.ct ? C_ACC : C_VIO);
  cv.drawString(String(g.id), x + 20, y + 10);
  cv.setTextColor(g.on ? C_TEXT : C_DIM);
  String nm = g.name; if (nm.length() > 12) nm = nm.substring(0, 12);
  cv.drawString(nm, x + 52, y + 10);
}

void pageGuests() {
  int nOn = 0, nOff = 0;
  for (int i = 0; i < nGuests; i++) (guests[i].on ? nOn : nOff)++;
  cv.setFont(&fonts::Font2); cv.setTextDatum(textdatum_t::middle_left);
  cv.setTextColor(C_OK);  cv.drawString("ACCESE  " + String(nOn), 12, 46);
  cv.setTextColor(C_DIM); cv.drawString("SPENTE  " + String(nOff), 166, 46);
  int yOn = 58, yOff = 58;
  for (int i = 0; i < nGuests; i++) {
    Guest& g = guests[i];
    if (g.on)  { if (yOn  <= 202) { guestRow(g, 8, yOn);    yOn  += 23; } }
    else       { if (yOff <= 202) { guestRow(g, 164, yOff); yOff += 23; } }
  }
  cv.setFont(&fonts::Font0); cv.setTextDatum(textdatum_t::middle_right);
  cv.setTextColor(C_ACC); cv.drawString("CT", 292, 46);
  cv.setTextColor(C_VIO); cv.drawString("VM", 310, 46);
}

void pageBackupNet() {
  // --- Backup: scheda in alto ---
  card(8, 40, 304, 82);
  uint32_t bc = !hasBackup ? C_WARN : (bkOk ? C_OK : C_BAD);
  cv.fillArc(42, 81, 22, 17, 0, 360, bc);
  cv.setFont(&fonts::FreeSansBold9pt7b); cv.setTextColor(bc); cv.setTextDatum(textdatum_t::middle_center);
  cv.drawString(!hasBackup ? "?" : (bkOk ? "OK" : "!"), 42, 81);
  cv.setTextDatum(textdatum_t::top_left);
  cv.setFont(&fonts::Font2); cv.setTextColor(C_DIM);
  cv.drawString("ULTIMO BACKUP DATABASE", 80, 50);
  cv.setFont(&fonts::FreeSansBold12pt7b); cv.setTextColor(C_TEXT);
  cv.drawString(hasBackup ? fmtWhen(bkWhen) : String("--"), 80, 68);
  cv.setFont(&fonts::Font2); cv.setTextColor(C_DIM);
  cv.drawString(hasBackup ? (String(bkFiles) + " database  -  prossimo alle 03:30") : String("pve2 non raggiungibile"), 80, 98);

  // --- Rete: tabella allineata ---
  card(8, 130, 304, 92);
  cv.setFont(&fonts::Font2); cv.setTextDatum(textdatum_t::top_left); cv.setTextColor(C_DIM);
  cv.drawString("RETE", 20, 138);
  int cnt = min(nNodes, 3);
  for (int i = 0; i < cnt + 1; i++) {
    int y = 158 + i * 19;
    if (i < cnt) {
      Node& n = nodes[i];
      cv.fillCircle(24, y + 7, 3, n.online ? C_OK : C_BAD);
      cv.setTextColor(C_TEXT); cv.drawString(n.name, 34, y);
      cv.setTextDatum(textdatum_t::top_right);
      uint32_t c = !n.online ? C_BAD : (n.link >= 1000 ? C_OK : C_WARN);
      cv.setTextColor(c);
      cv.drawString(!n.online ? String("offline") : (n.link > 0 ? String(n.link) + " Mb/s" : String("?")), 300, y);
      cv.setTextDatum(textdatum_t::top_left);
    } else {
      cv.fillCircle(24, y + 7, 3, fresh() ? C_OK : C_BAD);
      cv.setTextColor(C_TEXT); cv.drawString("display", 34, y);
      cv.setTextDatum(textdatum_t::top_right); cv.setTextColor(C_DIM);
      cv.drawString("USB  " + String(packets) + " agg.", 300, y);
      cv.setTextDatum(textdatum_t::top_left);
    }
  }
}

void render() {
  cv.fillScreen(C_BG);
  header();
  if (nNodes == 0) {
    cv.setTextDatum(textdatum_t::middle_center);
    cv.setFont(&fonts::FreeSansBold9pt7b); cv.setTextColor(C_TEXT);
    cv.drawString("In attesa dei dati...", 160, 110);
    cv.setFont(&fonts::Font2); cv.setTextColor(C_DIM);
    cv.drawString("collegami alla USB di pve1", 160, 136);
  } else {
    switch (page) {
      case 0: pageOverview(); break;
      case 1: pageNodes(); break;
      case 2: pageGuests(); break;
      case 3: pageBackupNet(); break;
    }
  }
  footer();
  cv.pushSprite(0, 0);
}

void colorTest() {
  lcd.fillScreen(0x000000u);
  lcd.fillRect(0, 0, 107, 200, 0xFF0000u);
  lcd.fillRect(107, 0, 106, 200, 0x00FF00u);
  lcd.fillRect(213, 0, 107, 200, 0x0000FFu);
  lcd.setFont(&fonts::FreeSansBold9pt7b); lcd.setTextDatum(textdatum_t::middle_center);
  lcd.setTextColor(0xFFFFFFu); lcd.drawString("ROSSO", 53, 100); lcd.drawString("BLU", 266, 100);
  lcd.setTextColor(0x000000u); lcd.drawString("VERDE", 160, 100);
  lcd.setTextColor(0xFFFFFFu); lcd.setFont(&fonts::Font2);
  lcd.drawString("sfondo nero = colori giusti", 160, 220);
}

// =====================================================================
//  OLED dei 3 PC (SSD1306 0.96" 128x64, tutti a 0x3C)
//  Hanno lo SCL in comune e un SDA ciascuno: prima di parlare con uno
//  si sposta l'I2C sul suo SDA. Gli altri vedono SDA fermo e ignorano.
// =====================================================================
Adafruit_SSD1306 oled[3] = { Adafruit_SSD1306(128, 64, &Wire, -1, 100000UL, 100000UL), Adafruit_SSD1306(128, 64, &Wire, -1, 100000UL, 100000UL),
                             Adafruit_SSD1306(128, 64, &Wire, -1, 100000UL, 100000UL) };
bool oledOk[3] = { false, false, false };
int  wireSda = -1;

void useOled(int i) {
  if (wireSda == OLED_SDA[i]) return;
  if (wireSda >= 0) { Wire.end(); pinMode(wireSda, INPUT_PULLUP); }
  Wire.begin(OLED_SDA[i], PIN_SCL, 100000);   // 100 kHz: con fili lunghi e breadboard i 400 kHz davano errori
  wireSda = OLED_SDA[i];
}

Node* findNode(const char* name) {
  for (int i = 0; i < nNodes; i++) if (nodes[i].name == name) return &nodes[i];
  return nullptr;
}

void oledBar(Adafruit_SSD1306& d, int x, int y, int w, int h, int pct) {
  pct = constrain(pct, 0, 100);
  d.drawRect(x, y, w, h, SSD1306_WHITE);
  int fw = (w - 4) * pct / 100;
  if (fw > 0) d.fillRect(x + 2, y + 2, fw, h - 4, SSD1306_WHITE);
}

void drawOled(int i) {
  Adafruit_SSD1306& d = oled[i];
  // spostamento di 1-2 pixel ogni minuto: evita che l'OLED si "bruci" con le scritte fisse
  int sh = (millis() / 60000UL) % 3;
  d.clearDisplay();
  d.setTextColor(SSD1306_WHITE);
  d.setTextSize(2); d.setCursor(sh, 0); d.print(OLED_NODE[i]);
  Node* n = findNode(OLED_NODE[i]);
  if (!fresh()) {
    d.setTextSize(1); d.setCursor(sh, 30); d.print("in attesa dei dati");
  } else if (!n) {
    d.setTextSize(1); d.setCursor(sh, 30); d.print("non nel cluster");
  } else if (!n->online) {
    d.setTextSize(2); d.setCursor(sh, 34); d.print("SPENTO");
  } else {
    // temperatura in alto a destra
    d.setTextSize(2);
    String t = n->temp >= 0 ? String(n->temp) : String("-");
    int tx = 128 - 12 * t.length() - 8 - sh;
    d.setCursor(tx, 0); d.print(t);
    if (n->temp >= 0) d.drawCircle(124 - sh, 2, 2, SSD1306_WHITE);
    // CPU e RAM
    int mp = n->memt > 0 ? (int)(100 * n->mem / n->memt) : 0;
    d.setTextSize(1);
    d.setCursor(sh, 22); d.print("CPU");
    oledBar(d, 24 + sh, 21, 70, 10, n->cpu);
    d.setCursor(98 + sh, 22); d.print(String(n->cpu) + "%");
    d.setCursor(sh, 36); d.print("RAM");
    oledBar(d, 24 + sh, 35, 70, 10, mp);
    d.setCursor(98 + sh, 36); d.print(String(mp) + "%");
    d.setCursor(sh, 54); d.print("su da " + fmtUp(n->up));
    if (n->temp >= 80) { d.setCursor(92 - sh, 54); d.print("CALDO!"); }
  }
  d.display();
}

void oledsInit() {
  for (int i = 0; i < 3; i++) {
    useOled(i);
    // begin() della libreria non controlla se il display risponde: lo verifichiamo noi (ACK I2C)
    uint8_t addr = 0;
    String seen = "";
    for (uint8_t a = 1; a < 127; a++) {
      Wire.beginTransmission(a);
      if (Wire.endTransmission() == 0) { seen += String(" 0x") + String(a, HEX); if (!addr && (a == 0x3C || a == 0x3D)) addr = a; }
    }
    Serial.printf("I2C SDA %d / SCL %d: trovati%s\n", OLED_SDA[i], PIN_SCL, seen.length() ? seen.c_str() : " nessuno");
    oledOk[i] = addr && oled[i].begin(SSD1306_SWITCHCAPVCC, addr, true, false);   // false: l'I2C lo gestiamo noi
    if (oledOk[i]) drawOled(i);   // subito il nome del PC, cosi' si vede che va
    Serial.printf("OLED %s: %s\n", OLED_NODE[i], oledOk[i] ? "ok" : "NON RISPONDE");
  }
}

void oledsPower(bool on) {
  for (int i = 0; i < 3; i++) if (oledOk[i]) { useOled(i); oled[i].ssd1306_command(on ? SSD1306_DISPLAYON : SSD1306_DISPLAYOFF); }
}

extern bool screensOn;

// Ogni 30 s ricontrolla gli OLED: se uno torna a rispondere lo reinizializza (si riprende da disturbi
// o fili mossi), se non risponde piu' smette di scrivergli. Lo scrive sulla seriale quando cambia.
void oledsRecheck() {
  for (int i = 0; i < 3; i++) {
    useOled(i);
    Wire.beginTransmission(0x3C);
    bool ack = Wire.endTransmission() == 0;
    if (ack && !oledOk[i]) {   // solo quando torna a rispondere: begin() spegne e riaccende (lampeggio)
      oled[i].begin(SSD1306_SWITCHCAPVCC, 0x3C, true, false);
      if (!screensOn) oled[i].ssd1306_command(SSD1306_DISPLAYOFF);
    }
    if (ack != oledOk[i]) Serial.printf("OLED %s: %s\n", OLED_NODE[i], ack ? "ok" : "NON RISPONDE");
    oledOk[i] = ack;
  }
}

void oledsDraw() {
  static unsigned long lastCheck = 0;
  if (millis() - lastCheck > 30000) { oledsRecheck(); lastCheck = millis(); }
  for (int i = 0; i < 3; i++) if (oledOk[i]) { useOled(i); drawOled(i); }
}

// =====================================================================
//  Barra 10 LED con due 74HC595: carico CPU medio del cluster
// =====================================================================
void barWrite(uint16_t bits) {   // bit 0 = LED in basso
  if (BAR_REVERSED) { uint16_t r = 0; for (int i = 0; i < 10; i++) if (bits & (1 << i)) r |= 1 << (9 - i); bits = r; }
  digitalWrite(PIN_SR_LATCH, LOW);
  shiftOut(PIN_SR_DATA, PIN_SR_CLK, MSBFIRST, (bits >> 8) & 0xFF);   // secondo chip: LED 9 e 10
  shiftOut(PIN_SR_DATA, PIN_SR_CLK, MSBFIRST, bits & 0xFF);          // primo chip: LED 1-8
  digitalWrite(PIN_SR_LATCH, HIGH);
}

void barBrightness(int v) { ledcWrite(PIN_SR_OE, 255 - constrain(v, 0, 255)); }   // OE e' attivo basso

int clusterCpu() {
  long sum = 0, cores = 0;
  for (int i = 0; i < nNodes; i++) if (nodes[i].online) { int c = max(nodes[i].cores, 1); sum += (long)nodes[i].cpu * c; cores += c; }
  return cores > 0 ? (int)(sum / cores) : 0;
}

void barUpdate() {
  unsigned long now = millis();
  if (!fresh()) {                       // niente dati: un LED che sale e scende
    int k = (now / 120) % 18; k = k < 10 ? k : 18 - k;
    barWrite(1 << k);
  } else if (!quorate) {                // quorum perso: tutta la barra lampeggia
    barWrite((now / 400) % 2 ? 0x3FF : 0);
  } else {
    int cpu = clusterCpu();
    int lit = (cpu + 9) / 10;           // 1% accende gia' il primo LED
    lit = constrain(lit, 1, 10);        // il primo resta sempre acceso: "vivo"
    barWrite((1 << lit) - 1);
  }
}

// =====================================================================
//  PIR: spegne TFT, OLED e barra dopo SCREEN_OFF_MS senza movimento
// =====================================================================
bool screensOn = true;
unsigned long lastMotion = 0;

void setScreens(bool on) {
  if (on == screensOn) return;
  screensOn = on;
  if (PIN_TFT_BL >= 0) ledcWrite(PIN_TFT_BL, on ? BRIGHT_TFT : 0);
  // niente lcd.sleep(): se il LED del TFT e' ancora su 3V3, in sleep il pannello diventa tutto bianco.
  // Lo riempiamo di nero (con il LED su GPIO 25 si spegne anche la retroilluminazione).
  if (!on) lcd.fillScreen(0x000000u);
  oledsPower(on);
  barBrightness(on ? BRIGHT_BAR : 0);
  Serial.println(on ? "SCHERMI_ACCESI" : "SCHERMI_SPENTI");
}

void pirUpdate() {
#if USE_PIR
  if (digitalRead(PIN_PIR) == HIGH) lastMotion = millis();
#else
  lastMotion = millis();
#endif
  setScreens(millis() - lastMotion < SCREEN_OFF_MS);
}

// =====================================================================
//  Joystick: sinistra/destra = pagina, click = ferma/riprende lo scorrimento
// =====================================================================
void goPage(int p) { page = (p + PAGES) % PAGES; lastPageChange = millis(); }

bool joyUpdate() {
#if USE_JOY
  static int dirPrev = 0; static unsigned long tDir = 0;
  static bool swPrev = false; static unsigned long tSw = 0;
  unsigned long now = millis();
  bool changed = false;
  int x = analogRead(PIN_JOY_X);                      // 0..4095, centro circa 1900
  int dir = x < 900 ? -1 : (x > 3200 ? 1 : 0);
  if (JOY_INVERT_X) dir = -dir;
  if (dir != 0 && (dir != dirPrev || now - tDir > 600)) {   // tenendo premuto avanza ogni 0,6 s
    if (!screensOn) lastMotion = now;                       // il primo tocco riaccende soltanto
    else goPage(page + dir);
    tDir = now; lastButton = now; changed = true;
  }
  dirPrev = dir;
  bool sw = digitalRead(PIN_JOY_SW) == LOW;
  if (sw != swPrev && now - tSw > 40) {
    swPrev = sw; tSw = now;
    if (sw) { if (screensOn) pageLocked = !pageLocked; lastMotion = now; lastButton = now; changed = true; }
  }
  return changed;
#else
  return false;
#endif
}

// =====================================================================
//  Setup / loop
// =====================================================================
void setup() {
  Serial.setRxBufferSize(8192);
  Serial.begin(115200);

  // barra: prima di tutto, cosi' all'accensione non mostra LED a caso
  pinMode(PIN_SR_DATA, OUTPUT); pinMode(PIN_SR_CLK, OUTPUT); pinMode(PIN_SR_LATCH, OUTPUT);
  ledcAttach(PIN_SR_OE, 5000, 8);
  barBrightness(0);
  barWrite(0);

  if (PIN_TFT_BL >= 0) { ledcAttach(PIN_TFT_BL, 5000, 8); ledcWrite(PIN_TFT_BL, BRIGHT_TFT); }
  lcd.init();
  lcd.setRotation(1);
  cv.setColorDepth(16);
  if (!cv.createSprite(320, 240)) { cv.setColorDepth(8); cv.createSprite(320, 240); Serial.println("SPRITE 8 bit"); }
  render();

  oledsInit();
  pinMode(PIN_PIR, INPUT);
  pinMode(PIN_JOY_SW, INPUT_PULLUP);
  analogSetPinAttenuation(PIN_JOY_X, ADC_11db);
  analogSetPinAttenuation(PIN_JOY_Y, ADC_11db);

  // prova barra: si riempie e si svuota
  barBrightness(BRIGHT_BAR);
  for (int i = 1; i <= 10; i++) { barWrite((1 << i) - 1); delay(40); }
  for (int i = 9; i >= 0; i--) { barWrite((1 << i) - 1); delay(40); }

  lastMotion = millis();
  Serial.println("DISPLAY_READY");
}

void loop() {
  unsigned long now = millis();
  readSerial();
  pirUpdate();
  bool changed = joyUpdate();

  // scorrimento automatico ogni 12 s (pausa di 60 s dopo il joystick, fermo se bloccato)
  if (!pageLocked && now - lastButton > 60000 && now - lastPageChange > 12000) goPage(page + 1);

  if (screensOn) {
    static unsigned long lastDraw = 0, lastOled = 0, lastBar = 0;
    if (changed || now - lastDraw > 500) { render(); lastDraw = now; }
    if (now - lastOled > 1000) { oledsDraw(); lastOled = now; }
    if (now - lastBar > 60) { barUpdate(); lastBar = now; }
  }
  delay(5);
}
