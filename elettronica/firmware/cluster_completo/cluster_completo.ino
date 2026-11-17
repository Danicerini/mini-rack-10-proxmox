/*
 * Cluster Completo (v3.1, 17/11/2026: impostazioni salvate da sole, spegnimento da 5 s) - plancia del rack: TFT 2.4" + 3 OLED (uno per PC) + PIR + barra 10 LED + joystick
 * Scheda: ESP32 DevKit (WROOM), collegato via USB a pve1. Dati: riga JSON ogni 5 s sulla seriale (115200)
 * dal servizio cluster-status di pve1.
 * v3: nuova grafica col logo Proxmox (provata nel simulatore display_esp32/simulatore_tft), 5 pagine,
 *     joystick su 4 direzioni: destra/sinistra = pagina, su/giu' = scegli, clic = apri, tenere premuto = conferma.
 *     Azioni sui nodi (Wake on LAN, riavvia, spegni): l'ESP manda "ACT <azione> <nodo>" sulla seriale,
 *     cluster-status su pve1 le esegue e risponde "ACT_OK ..." oppure "ACT_ERR ...".
 *     Impostazioni (luminosita', spegnimento schermi, scorrimento) salvate nella memoria dell'ESP.
 * La v2 e' in v2_completo/cluster_completo_v2_backup_17-11.ino.txt
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
#include <Preferences.h>
#include <esp_partition.h>
#include <esp_flash.h>
// Logo Proxmox (media kit ufficiale): file non incluso nella repo pubblica perche' e' un marchio.
// Se manca, al suo posto viene scritto "Proxmox" in testo.
#if __has_include("logo_proxmox.h")
#include "logo_proxmox.h"
#define HAS_LOGO 1
#else
#define HAS_LOGO 0
#endif

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
#define JOY_INVERT_Y  0       // 1 se su e giu' sono al contrario
#define BAR_REVERSED  0       // 1 se la barra si riempie dall'alto invece che dal basso
#define HOLD_MS       1500    // quanto tenere premuto per confermare un'azione

// Impostazioni modificabili dal joystick (pagina Impostazioni), salvate in memoria
struct Settings { int brightTft = 255; int brightBar = 120; int screenOffSec = 300; bool autoScroll = false; } set;
Preferences prefs;

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

// ---------------- Colori (come nel simulatore) ----------------
static constexpr uint32_t C_BG    = 0x07080Bu;
static constexpr uint32_t C_CARD  = 0x121419u;
static constexpr uint32_t C_CARD2 = 0x1A1D24u;
static constexpr uint32_t C_LINE  = 0x272B35u;
static constexpr uint32_t C_TEXT  = 0xF1F2F4u;
static constexpr uint32_t C_DIM   = 0x7F8593u;
static constexpr uint32_t C_ACC   = 0xE57000u;   // arancione Proxmox
static constexpr uint32_t C_OK    = 0x34D399u;
static constexpr uint32_t C_WARN  = 0xFBBF24u;
static constexpr uint32_t C_BAD   = 0xF87171u;
static constexpr uint32_t C_VIO   = 0xA78BFAu;
static constexpr uint32_t C_CYAN  = 0x22D3EEu;

// Font (LovyanGFX)
#define F_TITLE (&fonts::FreeSansBold9pt7b)
#define F_BIG   (&fonts::FreeSansBold12pt7b)
#define F_BODY  (&fonts::Font2)
#define F_SMALL (&fonts::Font0)

// ---------------- Dati ----------------
struct Node  { String name; String model; bool online; int cpu; int cores; float mem; float memt; long up; int temp; int link; };
struct Guest { int id; String name; bool ct; bool on; String node; int cpu; float mem; };

Node  nodes[4];   int nNodes = 0;
Guest guests[24]; int nGuests = 0;
String clusterName = "?", votes = "?", expectedVotes = "?", srvTime = "--:--";
bool quorate = false;
int onCount = 0, total = 0;
bool hasBackup = false, bkOk = false; String bkWhen = ""; int bkFiles = 0;
bool dataOk = false; unsigned long lastOkMs = 0; unsigned long packets = 0;
String rxLine;

// ---------------- Stato dell'interfaccia ----------------
const int PAGES = 5;
const char* PAGE_NAMES[PAGES] = { "Panoramica", "Nodi", "Macchine", "Backup e rete", "Impostazioni" };
enum View { V_PAGE, V_NODE, V_GUEST };
View view = V_PAGE;
int page = 0, sel = 0, scrollTop = 0, act = 0;
bool editing = false;
String selNode = ""; int selGuest = -1;
unsigned long lastPageChange = 0, lastButton = 0;
unsigned long pressStart = 0; bool holdFired = false;
String toastMsg = ""; unsigned long toastUntil = 0;

struct Action { const char* key; const char* label; bool needOn; uint32_t col; };
const Action ACTIONS[3] = { { "wol", "Accendi (Wake on LAN)", false, C_OK }, { "reboot", "Riavvia", true, C_WARN }, { "shutdown", "Spegni", true, C_BAD } };
// azioni sulle macchine (VM e container): l'ESP manda "GACT <azione> <id>"
const Action GACTIONS[4] = { { "start", "Accendi", false, C_OK }, { "reboot", "Riavvia", true, C_WARN },
                             { "shutdown", "Spegni (normale)", true, C_BAD }, { "stop", "Ferma subito (forzato)", true, C_BAD } };

void toast(const String& m, unsigned long ms = 2200) { toastMsg = m; toastUntil = millis() + ms; }

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
    d.name = n["name"] | "?"; d.model = n["model"] | ""; d.online = n["online"] | false;
    d.cpu = n["cpu"] | 0; d.cores = n["cores"] | 0;
    d.mem = n["mem"] | 0.0f; d.memt = n["memt"] | 0.0f; d.up = n["up"] | 0L;
    d.temp = n["temp"].isNull() ? -1 : n["temp"].as<int>();
    d.link = n["link"].isNull() ? 0 : n["link"].as<int>();
  }
  nGuests = 0;
  for (JsonObject g : doc["guests"].as<JsonArray>()) {     // in ordine di ID, come nel simulatore
    if (nGuests >= 24) break;
    Guest& d = guests[nGuests++];
    d.id = g["id"] | 0; d.name = g["name"] | "";
    d.ct = String((const char*)(g["type"] | "vm")) == "ct";
    d.on = g["on"] | false; d.node = g["node"] | "";
    d.cpu = g["cpu"] | 0; d.mem = g["mem"] | 0.0f;
  }
  hasBackup = !doc["backup"].isNull();
  if (hasBackup) { bkWhen = doc["backup"]["when"] | ""; bkFiles = doc["backup"]["files"] | 0; bkOk = doc["backup"]["ok"] | false; }
  dataOk = true; lastOkMs = millis(); packets++;
}

void readSerial() {
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\n') {
      rxLine.trim();
      if (rxLine.startsWith("{")) parseStatus(rxLine);
      else if (rxLine.startsWith("ACT_OK")) toast("Fatto: " + rxLine.substring(7));
      else if (rxLine.startsWith("ACT_ERR")) toast("Errore: " + rxLine.substring(8), 4000);
      else if (rxLine == "SET_GET") printSettings("ATTUALI");
      else if (rxLine == "FLASH_TEST") flashTest();
      else if (rxLine.startsWith("SET_TEST ")) {   // prova del salvataggio da pve1: SET_TEST <tft> <bar> <secondi>
        int a = 0, b = 0, c = 0;
        if (sscanf(rxLine.c_str() + 9, "%d %d %d", &a, &b, &c) == 3) { set.brightTft = a; set.brightBar = b; set.screenOffSec = c; applyBrightness(); saveSettings(); }
      }
      rxLine = "";
    } else if (c != '\r' && rxLine.length() < 6000) rxLine += c;
  }
}

// ---------------- Aiuti di disegno ----------------
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

void rr(int x, int y, int w, int h, int r, uint32_t c) { if (w <= 0 || h <= 0) return; cv.fillRoundRect(x, y, w, h, min(r, min(w, h) / 2), c); }
void txt(const String& s, int x, int y, uint32_t col, const lgfx::IFont* f, textdatum_t d = textdatum_t::middle_left) {
  cv.setFont(f); cv.setTextColor(col); cv.setTextDatum(d); cv.drawString(s, x, y);
}
int tw(const String& s, const lgfx::IFont* f) { cv.setFont(f); return cv.textWidth(s); }
void card(int x, int y, int w, int h, bool selected = false, uint32_t border = C_ACC) {
  rr(x, y, w, h, 8, selected ? C_CARD2 : C_CARD);
  if (selected) { cv.drawRoundRect(x, y, w, h, 8, border); cv.drawRoundRect(x + 1, y + 1, w - 2, h - 2, 7, border); }
}
void bar(int x, int y, int w, int h, int pct, uint32_t col) {
  pct = constrain(pct, 0, 100); rr(x, y, w, h, h / 2, C_LINE);
  int fw = (w * pct) / 100; if (fw > 0) rr(x, y, max(fw, h), h, h / 2, col);
}
// numero con il simbolo del grado disegnato (i font non hanno il carattere)
void degTxt(int t, int x, int y, uint32_t col, const lgfx::IFont* f, bool right) {
  String s = t < 0 ? String("-") : String(t);
  int w = tw(s, f), x0 = right ? x - w - 6 : x - (w + 6) / 2;
  txt(s, x0, y, col, f, textdatum_t::middle_left);
  if (t >= 0) { int fh = cv.fontHeight(f); cv.drawCircle(x0 + w + 3, y - fh / 2 + 4, 2, col); cv.drawCircle(x0 + w + 3, y - fh / 2 + 4, 1, col); }
}
void gauge(int cx, int cy, int r, int th, int pct, uint32_t col, const String& value, const char* label, bool deg = false, int t = 0) {
  pct = constrain(pct, 0, 100);
  cv.fillArc(cx, cy, r, r - th, 135, 405, C_LINE);
  if (pct > 0) cv.fillArc(cx, cy, r, r - th, 135, 135 + 270 * pct / 100, col);
  const lgfx::IFont* f = r > 30 ? F_BIG : F_TITLE;
  if (deg) degTxt(t, cx, cy, C_TEXT, f, false); else txt(value, cx, cy, C_TEXT, f, textdatum_t::middle_center);
  if (label) txt(label, cx, cy + r - 5, C_DIM, F_SMALL, textdatum_t::middle_center);
}
int pill(int x, int y, const String& s, uint32_t col) {
  int w = tw(s, F_SMALL) + 12; rr(x, y, w, 15, 7, col);
  txt(s, x + w / 2, y + 8, C_BG, F_SMALL, textdatum_t::middle_center); return w;
}
// triangolini per i suggerimenti (i font non hanno le frecce)
void triL(int x, int y, uint32_t c) { cv.fillTriangle(x, y, x + 5, y - 4, x + 5, y + 4, c); }
void triR(int x, int y, uint32_t c) { cv.fillTriangle(x + 5, y, x, y - 4, x, y + 4, c); }
void triU(int x, int y, uint32_t c) { cv.fillTriangle(x, y + 3, x + 8, y + 3, x + 4, y - 3, c); }
void triD(int x, int y, uint32_t c) { cv.fillTriangle(x, y - 3, x + 8, y - 3, x + 4, y + 3, c); }

Node* nodeByName(const String& n) { for (int i = 0; i < nNodes; i++) if (nodes[i].name == n) return &nodes[i]; return nullptr; }
Guest* guestById(int id) { for (int i = 0; i < nGuests; i++) if (guests[i].id == id) return &guests[i]; return nullptr; }
int onlineCount() { int c = 0; for (int i = 0; i < nNodes; i++) if (nodes[i].online) c++; return c; }
int clusterCpu();

// ---------------- Testata e piede ----------------
void header(const String& title, bool back) {
  if (back) { triL(10, 15, C_ACC); txt(title, 22, 16, C_TEXT, F_TITLE); }
  else {
#if HAS_LOGO
    cv.pushImage(10, 8, LOGO_HDR_W, LOGO_HDR_H, (const lgfx::rgb565_t*)LOGO_HDR);
#else
    txt("Proxmox", 10, 16, C_ACC, F_TITLE, textdatum_t::middle_left);
#endif
    txt(title, 124, 16, C_DIM, F_BODY); }
  bool f = fresh();
  txt(f ? srvTime : String("offline"), 296, 16, f ? C_DIM : C_BAD, F_BODY, textdatum_t::middle_right);
  cv.fillCircle(306, 16, 3, f ? C_OK : C_BAD);
  cv.drawFastHLine(10, 31, 300, C_LINE);
}
void footer() {
  if (view == V_PAGE) for (int i = 0; i < PAGES; i++) { int x = 160 - (PAGES - 1) * 8 + i * 16; if (i == page) rr(x - 6, 229, 12, 4, 2, C_ACC); else cv.fillCircle(x, 231, 2, C_LINE); }
  if (view == V_NODE) { triL(10, 231, C_DIM); txt("indietro", 18, 231, C_DIM, F_SMALL); triU(72, 231, C_DIM); triD(82, 231, C_DIM); txt("azione", 94, 231, C_DIM, F_SMALL); }
  if (view == V_GUEST) { triL(10, 231, C_DIM); txt("indietro", 18, 231, C_DIM, F_SMALL); triU(72, 231, C_DIM); triD(82, 231, C_DIM); txt("azione", 94, 231, C_DIM, F_SMALL); }
  if (set.autoScroll && view == V_PAGE) txt("AUTO", 310, 231, C_ACC, F_SMALL, textdatum_t::middle_right);
}

// ---------------- Pagine ----------------
void pageOverview() {
  int on = 0; for (int i = 0; i < nGuests; i++) if (guests[i].on) on++;
  int tot = nGuests, avg = clusterCpu();
  card(10, 40, 128, 120); gauge(74, 96, 46, 8, tot ? 100 * on / tot : 0, C_ACC, String(on) + "/" + String(tot), "MACCHINE ACCESE");
  card(146, 40, 164, 56);
  txt("CLUSTER", 156, 52, C_DIM, F_SMALL); pill(156, 66, quorate ? "QUORUM OK" : "QUORUM PERSO", quorate ? C_OK : C_BAD);
  txt("voti " + votes + "/" + expectedVotes, 300, 74, C_DIM, F_BODY, textdatum_t::middle_right);
  card(146, 104, 164, 56);
  txt("CPU MEDIA", 156, 116, C_DIM, F_SMALL); txt(String(avg) + "%", 300, 116, C_TEXT, F_TITLE, textdatum_t::middle_right);
  bar(156, 134, 144, 7, avg, pctColor(avg));
  if (hasBackup) txt(String("backup ") + (bkOk ? "ok - " : "FALLITO - ") + fmtWhen(bkWhen), 156, 151, bkOk ? C_DIM : C_BAD, F_SMALL);
  else txt("backup: pve2 non risponde", 156, 151, C_WARN, F_SMALL);
  int n = min(nNodes, 3); if (n == 0) return;
  int w = (300 - (n - 1) * 6) / n;
  for (int i = 0; i < n; i++) {
    Node& nd = nodes[i]; int x = 10 + i * (w + 6), y = 168;
    card(x, y, w, 52);
    cv.fillCircle(x + 10, y + 13, 3, nd.online ? C_OK : C_BAD); txt(nd.name, x + 18, y + 13, C_TEXT, F_TITLE);
    if (nd.online) {
      degTxt(nd.temp, x + w - 8, y + 13, tempColor(nd.temp), F_TITLE, true);
      bar(x + 8, y + 30, w - 16, 5, nd.cpu, pctColor(nd.cpu));
      txt("cpu " + String(nd.cpu) + "%", x + 8, y + 43, C_DIM, F_SMALL); txt(fmtUp(nd.up), x + w - 8, y + 43, C_DIM, F_SMALL, textdatum_t::middle_right);
    } else { txt("spento", x + w - 8, y + 13, C_BAD, F_BODY, textdatum_t::middle_right); bar(x + 8, y + 30, w - 16, 5, 0, C_LINE); }
  }
}

void pageNodes() {
  int n = min(nNodes, 3), h = n >= 3 ? 58 : 86;
  for (int i = 0; i < n; i++) {
    Node& nd = nodes[i]; int y = 40 + i * (h + 6);
    card(10, y, 300, h, sel == i);
    cv.fillCircle(22, y + 14, 3, nd.online ? C_OK : C_BAD); txt(nd.name, 30, y + 14, C_TEXT, F_TITLE);
    txt(nd.model, 30 + tw(nd.name, F_TITLE) + 8, y + 14, C_DIM, F_SMALL);
    if (!nd.online) { txt("spento - clic per accenderlo", 300, y + 14, C_BAD, F_BODY, textdatum_t::middle_right); continue; }
    txt("acceso da " + fmtUp(nd.up), 300, y + 14, C_DIM, F_SMALL, textdatum_t::middle_right);
    int by = y + h - 30, mp = nd.memt > 0 ? (int)(100 * nd.mem / nd.memt) : 0;
    struct { const char* l; String v; int p; uint32_t c; } cols[3] = {
      { "CPU", String(nd.cpu) + "%", nd.cpu, pctColor(nd.cpu) },
      { "RAM", String(nd.mem, 1) + "/" + String((int)(nd.memt + 0.5)) + "G", mp, pctColor(mp) },
      { "TEMP", "", min(100, max(0, nd.temp)), tempColor(nd.temp) } };
    for (int k = 0; k < 3; k++) {
      int x = 22 + k * 96;
      txt(cols[k].l, x, by, C_DIM, F_SMALL);
      if (k == 2) degTxt(nd.temp, x + 84, by, C_TEXT, F_BODY, true); else txt(cols[k].v, x + 84, by, C_TEXT, F_BODY, textdatum_t::middle_right);
      bar(x, by + 9, 84, 5, cols[k].p, cols[k].c);
    }
  }
}

void pageGuests() {
  const int vis = 8, rh = 21;
  if (sel < scrollTop) scrollTop = sel;
  if (sel >= scrollTop + vis) scrollTop = sel - vis + 1;
  int nOn = 0; for (int i = 0; i < nGuests; i++) if (guests[i].on) nOn++;
  txt(String(nOn) + " accese - " + String(nGuests - nOn) + " spente", 10, 42, C_DIM, F_SMALL);
  txt("CT", 282, 42, C_CYAN, F_SMALL, textdatum_t::middle_right); txt("VM", 306, 42, C_VIO, F_SMALL, textdatum_t::middle_right);
  for (int i = 0; i < vis && scrollTop + i < nGuests; i++) {
    Guest& g = guests[scrollTop + i]; int y = 50 + i * rh; bool s = scrollTop + i == sel;
    rr(10, y, 292, rh - 3, 5, s ? C_CARD2 : (g.on ? C_CARD : C_BG)); if (s) rr(10, y, 3, rh - 3, 1, C_ACC);
    cv.fillCircle(22, y + 9, 3, g.on ? C_OK : C_LINE);
    txt(String(g.id), 30, y + 9, g.ct ? C_CYAN : C_VIO, F_BODY);
    String nm = g.name; if (nm.length() > 16) nm = nm.substring(0, 16);
    txt(nm, 60, y + 9, g.on ? C_TEXT : C_DIM, F_BODY); txt(g.node, 200, y + 9, C_DIM, F_SMALL);
    txt(g.on ? String(g.cpu) + "%  " + String(g.mem, 1) + "G" : String("spenta"), 296, y + 9, g.on ? C_DIM : C_LINE, F_BODY, textdatum_t::middle_right);
  }
  if (nGuests > 0) { int th = 168 * min(vis, nGuests) / nGuests, ty = 50 + 168 * scrollTop / nGuests; rr(306, 50, 3, 168, 1, C_CARD); rr(306, ty, 3, th, 1, C_DIM); }
}

void pageBackupNet() {
  card(10, 40, 300, 80);
  uint32_t bc = !hasBackup ? C_WARN : (bkOk ? C_OK : C_BAD);
  cv.fillArc(44, 80, 20, 16, 0, 360, bc);
  txt(!hasBackup ? "?" : (bkOk ? "OK" : "!"), 44, 81, bc, F_TITLE, textdatum_t::middle_center);
  txt("ULTIMO BACKUP DATABASE", 76, 54, C_DIM, F_SMALL);
  txt(hasBackup ? fmtWhen(bkWhen) : String("--"), 76, 75, C_TEXT, F_BIG);
  txt(!hasBackup ? String("pve2 non raggiungibile") : (bkOk ? String(bkFiles) + " database - prossimo alle 03:30" : String("copia incompleta: controlla pve2")), 76, 100, bkOk ? C_DIM : C_BAD, F_BODY);
  card(10, 128, 300, 92); txt("RETE", 22, 140, C_DIM, F_SMALL);
  int n = min(nNodes, 3);
  for (int i = 0; i <= n; i++) {
    int y = 158 + i * 17; String a, b; uint32_t c;
    if (i < n) { Node& nd = nodes[i]; a = nd.name; b = !nd.online ? String("offline") : (nd.link >= 1000 ? String("1 Gb/s") : (nd.link > 0 ? String(nd.link) + " Mb/s" : String("?")));
                 c = !nd.online ? C_BAD : (nd.link >= 1000 ? C_OK : C_WARN); }
    else { a = "display"; b = fresh() ? "USB ok - " + String(packets) + " agg." : String("nessun dato"); c = fresh() ? C_OK : C_BAD; }
    cv.fillCircle(24, y, 3, c); txt(a, 34, y, C_TEXT, F_BODY); txt(b, 298, y, c, F_BODY, textdatum_t::middle_right);
  }
}

struct SettingDef { const char* label; };
const SettingDef SETTINGS[4] = { { "Luminosita' TFT" }, { "Luminosita' barra LED" }, { "Spegni schermi dopo" }, { "Scorrimento automatico" } };
String settingValue(int i) {
  switch (i) {
    case 0: return String((set.brightTft * 100 + 127) / 255) + "%";
    case 1: return String((set.brightBar * 100 + 127) / 255) + "%";
    case 2: return set.screenOffSec < 60 ? String(set.screenOffSec) + " s" : String(set.screenOffSec / 60) + " min";
    default: return set.autoScroll ? "si'" : "no";
  }
}
void pageSettings() {
  for (int i = 0; i < 4; i++) {
    int y = 40 + i * 40; bool s = sel == i;
    card(10, y, 300, 34, s);
    txt(SETTINGS[i].label, 22, y + 17, C_TEXT, F_BODY);
    if (s && editing) { triL(205, y + 17, C_ACC); txt(settingValue(i), 252, y + 17, C_ACC, F_TITLE, textdatum_t::middle_center); triR(290, y + 17, C_ACC); }
    else txt(settingValue(i), 298, y + 17, s ? C_TEXT : C_DIM, F_TITLE, textdatum_t::middle_right);
  }
  txt("firmware v3 - ESP32 - dati da pve1 via USB", 160, 214, C_DIM, F_SMALL, textdatum_t::middle_center);
}

int nodeActions(Node* nd, const Action* out[3]) {
  int n = 0; for (int i = 0; i < 3; i++) if (ACTIONS[i].needOn == (nd && nd->online)) out[n++] = &ACTIONS[i];
  return n;
}
int guestActions(Guest* g, const Action* out[4]) {
  int n = 0; for (int i = 0; i < 4; i++) if (GACTIONS[i].needOn == (g && g->on)) out[n++] = &GACTIONS[i];
  return n;
}
void nodeDetail() {
  Node* nd = nodeByName(selNode);
  if (!nd) { view = V_PAGE; return; }
  header(nd->name + (nd->model.length() ? " - " + nd->model : String("")), true);
  if (nd->online) {
    gauge(52, 80, 34, 6, nd->cpu, pctColor(nd->cpu), String(nd->cpu) + "%", "CPU");
    gauge(130, 80, 34, 6, min(100, max(0, nd->temp)), tempColor(nd->temp), "", "TEMP", true, nd->temp);
    int mp = nd->memt > 0 ? (int)(100 * nd->mem / nd->memt) : 0;
    txt("RAM", 180, 52, C_DIM, F_SMALL); txt(String(nd->mem, 1) + " / " + String((int)(nd->memt + 0.5)) + " GB", 308, 52, C_TEXT, F_BODY, textdatum_t::middle_right);
    bar(180, 62, 128, 6, mp, pctColor(mp));
    txt(String(nd->cores) + " thread - " + (nd->link >= 1000 ? String("1 Gb/s") : String(nd->link) + " Mb/s"), 180, 82, C_DIM, F_SMALL);
    txt("acceso da " + fmtUp(nd->up), 180, 96, C_DIM, F_SMALL);
    String ids = ""; int c = 0;
    for (int i = 0; i < nGuests; i++) if (guests[i].on && guests[i].node == nd->name) { ids += " " + String(guests[i].id); c++; }
    txt(c ? String(c) + " macchine accese:" + ids : String("nessuna macchina accesa"), 10, 128, C_DIM, F_SMALL);
  } else {
    txt("Il nodo e' spento o non risponde.", 160, 80, C_BAD, F_TITLE, textdatum_t::middle_center);
    txt("Puoi accenderlo con Wake on LAN.", 160, 100, C_DIM, F_BODY, textdatum_t::middle_center);
  }
  const Action* acts[3]; int n = nodeActions(nd, acts); if (act >= n) act = 0;
  for (int i = 0; i < n; i++) {
    int y = 142 + i * 26; bool s = act == i;
    rr(10, y, 300, 22, 6, s ? C_CARD2 : C_CARD);
    if (s) { cv.drawRoundRect(10, y, 300, 22, 6, acts[i]->col); cv.drawRoundRect(11, y + 1, 298, 20, 5, acts[i]->col); }
    txt(acts[i]->label, 22, y + 11, s ? acts[i]->col : C_TEXT, F_BODY);
    if (s) txt("tieni premuto", 296, y + 11, C_DIM, F_SMALL, textdatum_t::middle_right);
    if (s && pressStart && !holdFired) { int p = min(1000UL, (millis() - pressStart) * 1000UL / HOLD_MS); rr(10, y + 19, 300 * p / 1000, 3, 1, acts[i]->col); }
  }
}

void guestDetail() {
  Guest* g = guestById(selGuest);
  if (!g) { view = V_PAGE; return; }
  header(String(g->id) + " - " + g->name, true);
  card(10, 38, 300, 64);
  const char* k[4] = { "tipo", "nodo", "stato", "CPU / RAM" };
  String v[4] = { g->ct ? "container LXC" : "macchina virtuale", g->node, g->on ? "accesa" : "spenta",
                  g->on ? String(g->cpu) + "%  -  " + String(g->mem, 2) + " GB" : String("-") };
  for (int i = 0; i < 4; i++) { int y = 49 + i * 14; txt(k[i], 22, y, C_DIM, F_BODY); txt(v[i], 298, y, i == 2 ? (g->on ? C_OK : C_DIM) : C_TEXT, F_BODY, textdatum_t::middle_right); }
  const Action* acts[4]; int n = guestActions(g, acts); if (act >= n) act = 0;
  for (int i = 0; i < n; i++) {
    int y = 108 + i * 26; bool s = act == i;
    rr(10, y, 300, 22, 6, s ? C_CARD2 : C_CARD);
    if (s) { cv.drawRoundRect(10, y, 300, 22, 6, acts[i]->col); cv.drawRoundRect(11, y + 1, 298, 20, 5, acts[i]->col); }
    txt(acts[i]->label, 22, y + 11, s ? acts[i]->col : C_TEXT, F_BODY);
    if (s) txt("tieni premuto", 296, y + 11, C_DIM, F_SMALL, textdatum_t::middle_right);
    if (s && pressStart && !holdFired) { int p = min(1000UL, (millis() - pressStart) * 1000UL / HOLD_MS); rr(10, y + 19, 300 * p / 1000, 3, 1, acts[i]->col); }
  }
}

void drawSplash(int pct) {
  cv.fillScreen(C_BG);
#if HAS_LOGO
  cv.pushImage(160 - LOGO_SPLASH_W / 2, 34, LOGO_SPLASH_W, LOGO_SPLASH_H, (const lgfx::rgb565_t*)LOGO_SPLASH);
#else
  txt("Proxmox", 160, 90, C_ACC, F_BIG, textdatum_t::middle_center);
#endif
  txt("cluster casa", 160, 160, C_DIM, F_BODY, textdatum_t::middle_center);
  rr(100, 182, 120, 4, 2, C_LINE); rr(100, 182, 120 * pct / 100, 4, 2, C_ACC);
  txt("in attesa dei dati da pve1...", 160, 200, C_DIM, F_SMALL, textdatum_t::middle_center);
  cv.pushSprite(0, 0);
}

void render() {
  // finche' non arriva il primo dato da pve1 resta la schermata col logo (nessuna pagina vuota)
  if (!dataOk) { drawSplash((millis() / 25) % 101); return; }
  cv.fillScreen(C_BG);
  if (view == V_NODE) nodeDetail();
  if (view == V_GUEST) guestDetail();
  if (view == V_PAGE) {
    header(PAGE_NAMES[page], false);
    if (nNodes == 0 && page < 4) {
      txt("Nessun dato dalla USB", 160, 110, C_TEXT, F_TITLE, textdatum_t::middle_center);
      txt("controlla il cavo verso pve1", 160, 130, C_DIM, F_BODY, textdatum_t::middle_center);
    } else switch (page) {
      case 0: pageOverview(); break;
      case 1: pageNodes(); break;
      case 2: pageGuests(); break;
      case 3: pageBackupNet(); break;
      case 4: pageSettings(); break;
    }
  }
  footer();
  if (toastMsg.length() && millis() < toastUntil) {
    String m = toastMsg; if (m.length() > 40) m = m.substring(0, 40);
    int w = tw(m, F_BODY) + 24; rr(160 - w / 2, 196, w, 24, 12, C_ACC); txt(m, 160, 208, C_BG, F_BODY, textdatum_t::middle_center);
  }
  if (fresh() && !quorate && view == V_PAGE && (millis() / 500) % 2) { cv.drawRect(0, 0, 320, 240, C_BAD); cv.drawRect(1, 1, 318, 238, C_BAD); }
  cv.pushSprite(0, 0);
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
//  PIR: spegne TFT, OLED e barra dopo "Spegni schermi dopo" senza movimento
// =====================================================================
bool screensOn = true;
unsigned long lastMotion = 0;

void applyBrightness() {
  if (PIN_TFT_BL >= 0) ledcWrite(PIN_TFT_BL, screensOn ? set.brightTft : 0);
  barBrightness(screensOn ? set.brightBar : 0);
}

void setScreens(bool on) {
  if (on == screensOn) return;
  screensOn = on;
  // niente lcd.sleep(): se il LED del TFT e' ancora su 3V3, in sleep il pannello diventa tutto bianco.
  if (!on) lcd.fillScreen(0x000000u);
  oledsPower(on);
  applyBrightness();
  Serial.println(on ? "SCHERMI_ACCESI" : "SCHERMI_SPENTI");
}

void pirUpdate() {
#if USE_PIR
  if (digitalRead(PIN_PIR) == HIGH) lastMotion = millis();
#else
  lastMotion = millis();
#endif
  setScreens(millis() - lastMotion < (unsigned long)set.screenOffSec * 1000UL);
}

// =====================================================================
//  Impostazioni salvate nella memoria dell'ESP (Preferences / NVS)
// =====================================================================
void flashTest() {   // diagnosi: legge la NVS e prova a scrivere un settore della partizione spiffs (non usata)
  const esp_partition_t* nv = esp_partition_find_first(ESP_PARTITION_TYPE_DATA, ESP_PARTITION_SUBTYPE_DATA_NVS, NULL);
  const esp_partition_t* sp = esp_partition_find_first(ESP_PARTITION_TYPE_DATA, ESP_PARTITION_SUBTYPE_DATA_SPIFFS, NULL);
  uint8_t b[16];
  if (nv) { esp_partition_read(nv, 0, b, 16); Serial.printf("FLASH nvs @0x%x: %02x %02x %02x %02x %02x %02x %02x %02x\n", (unsigned)nv->address, b[0], b[1], b[2], b[3], b[4], b[5], b[6], b[7]); }
  if (sp) {
    esp_err_t e1 = esp_partition_erase_range(sp, 0, 4096);
    uint8_t w[16]; for (int i = 0; i < 16; i++) w[i] = 0xA0 + i;
    esp_err_t e2 = esp_partition_write(sp, 0, w, 16);
    memset(b, 0, 16); esp_err_t e3 = esp_partition_read(sp, 0, b, 16);
    Serial.printf("FLASH spiffs @0x%x erase=%d write=%d read=%d -> %02x %02x %02x %02x\n", (unsigned)sp->address, e1, e2, e3, b[0], b[1], b[2], b[3]);
  }
  uint32_t id = 0; esp_flash_read_id(NULL, &id); Serial.printf("FLASH id=%06x\n", (unsigned)id);
}
void printSettings(const char* tag) {
  Serial.printf("IMPOSTAZIONI %s tft=%d bar=%d offs=%d auto=%d\n", tag, set.brightTft, set.brightBar, set.screenOffSec, set.autoScroll);
}
void loadSettings() {
  // in scrittura (false) cosi' lo spazio "plancia" viene creato se non c'e' ancora: in sola lettura fallirebbe
  bool ok = prefs.begin("plancia", false);
  Serial.printf("NVS apertura %s\n", ok ? "ok" : "FALLITA");
  set.brightTft = prefs.getInt("tft", 255); set.brightBar = prefs.getInt("bar", 120);
  // "offs" in secondi; "off" (minuti) e' il vecchio formato, letto solo se il nuovo non c'e'
  set.screenOffSec = prefs.isKey("offs") ? prefs.getInt("offs", 300) : prefs.getInt("off", 5) * 60;
  set.autoScroll = prefs.getBool("auto", false);
  prefs.end();
  set.brightTft = constrain(set.brightTft, 15, 255); set.brightBar = constrain(set.brightBar, 0, 255);
  set.screenOffSec = constrain(set.screenOffSec, 5, 1800);
  printSettings("CARICATE");
}
void saveSettings() {
  bool ok = prefs.begin("plancia", false);
  size_t n = 0;
  n += prefs.putInt("tft", set.brightTft); n += prefs.putInt("bar", set.brightBar);
  n += prefs.putInt("offs", set.screenOffSec); n += prefs.putBool("auto", set.autoScroll);
  prefs.end();
  Serial.printf("IMPOSTAZIONI_SALVATE apertura=%s byte=%u\n", ok ? "ok" : "FALLITA", (unsigned)n);
  printSettings("SALVATE");
}
// tempi di spegnimento: 5, 10, 20, 40 s, poi da 1 a 30 minuti
const int OFF_STEPS[] = { 5, 10, 20, 40, 60, 120, 180, 240, 300, 360, 420, 480, 540, 600, 660, 720, 780, 840, 900,
                          960, 1020, 1080, 1140, 1200, 1260, 1320, 1380, 1440, 1500, 1560, 1620, 1680, 1740, 1800 };
const int N_OFF_STEPS = sizeof(OFF_STEPS) / sizeof(OFF_STEPS[0]);
int stepOff(int cur, int dir) {
  int i = 0; while (i < N_OFF_STEPS - 1 && OFF_STEPS[i] < cur) i++;   // passo piu' vicino
  return OFF_STEPS[constrain(i + dir, 0, N_OFF_STEPS - 1)];
}
unsigned long settingsDirtyAt = 0;   // salvataggio automatico 2 s dopo l'ultima modifica
void changeSetting(int i, int dir) {
  switch (i) {
    case 0: set.brightTft = constrain(set.brightTft + dir * 15, 15, 255); break;
    case 1: set.brightBar = constrain(set.brightBar + dir * 15, 0, 255); break;
    case 2: set.screenOffSec = stepOff(set.screenOffSec, dir); break;
    case 3: set.autoScroll = !set.autoScroll; break;
  }
  applyBrightness();
  settingsDirtyAt = millis(); if (!settingsDirtyAt) settingsDirtyAt = 1;
}

// =====================================================================
//  Joystick: destra/sinistra = pagina, su/giu' = scegli, clic = apri,
//  tenere premuto = conferma un'azione su un nodo
// =====================================================================
int itemCount() { return page == 1 ? min(nNodes, 3) : page == 2 ? nGuests : page == 4 ? 4 : 0; }

void goPage(int p) { page = (p + PAGES) % PAGES; sel = 0; scrollTop = 0; lastPageChange = millis(); }

void joyInput(char k) {        // 'L' 'R' 'U' 'D' 'C'
  if (!dataOk) return;         // sulla schermata di avvio il joystick non fa niente
  if (view == V_NODE) {
    Node* nd = nodeByName(selNode); const Action* acts[3]; int n = nodeActions(nd, acts);
    if (k == 'L') view = V_PAGE;
    else if (k == 'U' && n) act = (act + n - 1) % n;
    else if (k == 'D' && n) act = (act + 1) % n;
    else if (k == 'C') toast("tieni premuto per confermare");
    return;
  }
  if (view == V_GUEST) {
    Guest* g = guestById(selGuest); const Action* acts[4]; int n = guestActions(g, acts);
    if (k == 'L') view = V_PAGE;
    else if (k == 'U' && n) act = (act + n - 1) % n;
    else if (k == 'D' && n) act = (act + 1) % n;
    else if (k == 'C') toast("tieni premuto per confermare");
    return;
  }
  if (page == 4 && editing) {
    if (k == 'L' || k == 'R') changeSetting(sel, k == 'R' ? 1 : -1);
    else if (k == 'C') { editing = false; if (settingsDirtyAt) { settingsDirtyAt = 0; saveSettings(); } toast("salvato"); }
    return;
  }
  int n = itemCount();
  if (k == 'L' || k == 'R') goPage(page + (k == 'R' ? 1 : -1));
  else if ((k == 'U' || k == 'D') && n) sel = (sel + (k == 'D' ? 1 : n - 1)) % n;
  else if (k == 'C') {
    if (page == 1 && sel < nNodes) { view = V_NODE; selNode = nodes[sel].name; act = 0; }
    else if (page == 2 && sel < nGuests) { view = V_GUEST; selGuest = guests[sel].id; act = 0; }
    else if (page == 4) editing = true;
    else toast("niente da aprire qui");
  }
}

void holdAction() {
  if (view == V_GUEST) {
    Guest* g = guestById(selGuest); const Action* acts[4]; int n = guestActions(g, acts);
    if (!g || act >= n) return;
    Serial.printf("GACT %s %d\n", acts[act]->key, g->id);
    toast(String("inviato: ") + acts[act]->key + " " + String(g->id));
    return;
  }
  if (view != V_NODE) return;
  Node* nd = nodeByName(selNode); const Action* acts[3]; int n = nodeActions(nd, acts);
  if (!nd || act >= n) return;
  Serial.printf("ACT %s %s\n", acts[act]->key, nd->name.c_str());   // cluster-status su pve1 lo esegue
  toast(String("inviato: ") + acts[act]->key + " " + nd->name);
}

bool joyUpdate() {
#if USE_JOY
  static char dirPrev = 0; static unsigned long tDir = 0;
  static bool swPrev = false; static unsigned long tSw = 0;
  unsigned long now = millis();
  bool changed = false;
  int x = analogRead(PIN_JOY_X), y = analogRead(PIN_JOY_Y);   // 0..4095, centro circa 1900
  int dx = x < 900 ? -1 : (x > 3200 ? 1 : 0), dy = y < 900 ? -1 : (y > 3200 ? 1 : 0);
  if (JOY_INVERT_X) dx = -dx;
  if (JOY_INVERT_Y) dy = -dy;
  char dir = dx < 0 ? 'L' : dx > 0 ? 'R' : dy < 0 ? 'U' : dy > 0 ? 'D' : 0;
  if (dir && (dir != dirPrev || now - tDir > (dir == 'U' || dir == 'D' ? 250UL : 600UL))) {   // tenendo premuto ripete
    if (!screensOn) lastMotion = now;                                     // il primo tocco riaccende soltanto
    else joyInput(dir);
    tDir = now; lastButton = now; lastMotion = now; changed = true;
  }
  dirPrev = dir;
  bool sw = digitalRead(PIN_JOY_SW) == LOW;
  if (sw != swPrev && now - tSw > 40) {
    swPrev = sw; tSw = now; lastMotion = now; lastButton = now; changed = true;
    if (!screensOn) { pressStart = 0; }
    else if (sw) { pressStart = now; holdFired = false; }
    else if (pressStart) { unsigned long dt = now - pressStart; pressStart = 0; if (!holdFired && dt < 450) joyInput('C'); }
  }
  if (sw && pressStart && (view == V_NODE || view == V_GUEST)) {
    changed = true;                                                       // ridisegna la barra che si riempie
    if (!holdFired && now - pressStart >= HOLD_MS) { holdFired = true; holdAction(); }
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
  loadSettings();

  // barra: prima di tutto, cosi' all'accensione non mostra LED a caso
  pinMode(PIN_SR_DATA, OUTPUT); pinMode(PIN_SR_CLK, OUTPUT); pinMode(PIN_SR_LATCH, OUTPUT);
  ledcAttach(PIN_SR_OE, 5000, 8);
  barBrightness(0);
  barWrite(0);

  if (PIN_TFT_BL >= 0) { ledcAttach(PIN_TFT_BL, 5000, 8); ledcWrite(PIN_TFT_BL, set.brightTft); }
  lcd.init();
  lcd.setRotation(1);
  cv.setColorDepth(16);
  if (!cv.createSprite(320, 240)) { cv.setColorDepth(8); cv.createSprite(320, 240); Serial.println("SPRITE 8 bit"); }
  drawSplash(10);

  oledsInit();
  pinMode(PIN_PIR, INPUT);
  pinMode(PIN_JOY_SW, INPUT_PULLUP);
  analogSetPinAttenuation(PIN_JOY_X, ADC_11db);
  analogSetPinAttenuation(PIN_JOY_Y, ADC_11db);

  // prova barra: si riempie e si svuota, intanto la barra della schermata di avvio avanza
  barBrightness(set.brightBar);
  for (int i = 1; i <= 10; i++) { barWrite((1 << i) - 1); drawSplash(10 + i * 4); delay(40); }
  for (int i = 9; i >= 0; i--) { barWrite((1 << i) - 1); drawSplash(50 + (9 - i) * 5); delay(40); }
  for (int p = 100; p <= 100; p++) drawSplash(p);
  delay(600);

  lastMotion = millis();
  Serial.println("DISPLAY_READY");
}

void loop() {
  unsigned long now = millis();
  readSerial();
  pirUpdate();
  bool changed = joyUpdate();
  if (settingsDirtyAt && now - settingsDirtyAt > 2000) { settingsDirtyAt = 0; saveSettings(); }   // salva anche senza clic

  // scorrimento automatico (se attivo): ogni 12 s, pausa di 60 s dopo il joystick
  if (set.autoScroll && view == V_PAGE && !editing && now - lastButton > 60000 && now - lastPageChange > 12000) goPage((page + 1) % 4 == 0 ? 0 : page + 1);

  if (screensOn) {
    static unsigned long lastDraw = 0, lastOled = 0, lastBar = 0;
    if (changed || now - lastDraw > 500) { render(); lastDraw = now; }
    if (now - lastOled > 1000) { oledsDraw(); lastOled = now; }
    if (now - lastBar > 60) { barUpdate(); lastBar = now; }
  }
  delay(5);
}
