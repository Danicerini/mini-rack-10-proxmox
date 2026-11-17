"""Crea Schema_collegamenti.pdf (3 pagine A4 orizzontali) per il firmware cluster_completo.
Uso:  python crea_schema_pdf.py      (serve reportlab)
"""
from pathlib import Path
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas

W, H = landscape(A4)
OUT = Path(__file__).with_name("Schema_collegamenti.pdf")

C5V, C3V, CGND = colors.HexColor("#d62728"), colors.HexColor("#ff7f0e"), colors.black
INK, DIM, BOX = colors.HexColor("#1f2937"), colors.HexColor("#6b7280"), colors.HexColor("#f3f4f6")
PAL = ["#1f77b4", "#2ca02c", "#9467bd", "#8c564b", "#e377c2", "#17becf", "#bcbd22", "#7f7f7f", "#0b5394",
       "#38761d", "#741b47", "#b45f06", "#134f5c", "#a61c00", "#3d85c6", "#c90076", "#6aa84f", "#e69138"]

c = canvas.Canvas(str(OUT), pagesize=(W, H))
c.setTitle("Schema collegamenti - plancia cluster")


def Y(y):  # coordinate dall'alto
    return H - y


def text(x, y, s, size=8, col=INK, bold=False, anchor="l"):
    c.setFillColor(col)
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    {"l": c.drawString, "r": c.drawRightString, "c": c.drawCentredString}[anchor](x, Y(y) - size * 0.35, s)


def box(x0, y0, x1, y1, title, sub=""):
    c.setFillColor(BOX); c.setStrokeColor(INK); c.setLineWidth(1)
    c.roundRect(x0, Y(y1), x1 - x0, y1 - y0, 6, fill=1, stroke=1)
    text((x0 + x1) / 2, y0 + 10, title, 9, bold=True, anchor="c")
    if sub:
        text((x0 + x1) / 2, y0 + 21, sub, 6.5, DIM, anchor="c")


def tag(x, y, net, side):
    """etichetta di alimentazione al posto del filo"""
    col = {"5V": C5V, "3V3": C3V, "GND": CGND}[net]
    w = 24
    x0 = x if side == "r" else x - w
    c.setStrokeColor(col); c.setLineWidth(1.6)
    c.line(x, Y(y), x + (6 if side == "r" else -6), Y(y))
    c.setFillColor(col); c.roundRect(x0 + (6 if side == "r" else -6), Y(y) - 5, w, 10, 3, fill=1, stroke=0)
    text(x0 + (6 if side == "r" else -6) + w / 2, y, net, 6.5, colors.white, True, "c")


def wire(pts, col, lw=1.6):
    c.setStrokeColor(colors.HexColor(col) if isinstance(col, str) else col); c.setLineWidth(lw)
    p = c.beginPath(); p.moveTo(pts[0][0], Y(pts[0][1]))
    for x, y in pts[1:]:
        p.lineTo(x, Y(y))
    c.drawPath(p, stroke=1, fill=0)
    for x, y in (pts[0], pts[-1]):
        c.setFillColor(colors.HexColor(col) if isinstance(col, str) else col); c.circle(x, Y(y), 1.8, fill=1, stroke=0)


def dot(x, y, col):
    c.setFillColor(colors.HexColor(col)); c.circle(x, Y(y), 2.6, fill=1, stroke=0)


# =====================================================================
# PAGINA 1: schema generale
# =====================================================================
text(30, 28, "Plancia cluster - schema dei collegamenti (firmware v2 cluster_completo)", 15, bold=True)
text(30, 44, "I numeri sull'ESP32 sono i GPIO scritti sulla scheda (D23, D22...). Le etichette 5V / 3V3 / GND vanno ai pin "
             "con lo stesso nome dell'ESP32 (conviene una millefori con due file comuni).", 8, DIM)

# --- ESP32 ---
EX0, EX1, EY0 = 345, 470, 82
PY0, STEP = 108, 24
LEFT = ["EN", "36 VP", "39 VN", "34", "35", "32", "33", "25", "26", "27", "14", "12", "GND", "13", "VIN 5V"]
RIGHT = ["23", "22", "TX 1", "RX 3", "21", "19", "18", "5", "17", "16", "4", "2", "15", "GND", "3V3"]
EY1 = PY0 + STEP * 14 + 22
box(EX0, EY0, EX1, EY1, "ESP32 DevKit", "USB verso pve1 (in basso)")
lp, rp = {}, {}
for i, (l, r) in enumerate(zip(LEFT, RIGHT)):
    y = PY0 + i * STEP
    for x, s, a, d in ((EX0, l, "l", lp), (EX1, r, "r", rp)):
        c.setFillColor(colors.white); c.setStrokeColor(INK); c.circle(x, Y(y), 3, fill=1, stroke=1)
        text(x + (7 if a == "l" else -7), y, s, 7.5, INK, True, a)
        d[s.split()[0]] = y
tag(EX0, lp["VIN"], "5V", "l")
tag(EX0, lp["GND"], "GND", "l")
tag(EX1, rp["GND"], "GND", "r")
tag(EX1, rp["3V3"], "3V3", "r")
text((EX0 + EX1) / 2, EY1 + 12, "pin non usati: EN, 36, 32, 26, 12, 2, TX, RX", 6.5, DIM, anchor="c")


def comp(x0, y0, x1, title, sub, pins, side, step=17):
    """pins: lista di (nome, rete|None). side = lato dei pin ('l' o 'r'). Ritorna {nome: (x, y)}"""
    y1 = y0 + 30 + step * len(pins)
    box(x0, y0, x1, y1, title, sub)
    out = {}
    for i, (n, net) in enumerate(pins):
        y = y0 + 34 + i * step
        x = x1 if side == "r" else x0
        c.setFillColor(colors.white); c.setStrokeColor(INK); c.circle(x, Y(y), 2.6, fill=1, stroke=1)
        text(x + (-6 if side == "r" else 6), y, n, 7, INK, False, "r" if side == "r" else "l")
        if net:
            tag(x, y, net, side)
        out[n] = (x, y)
    return out


# --- componenti a destra ---
tft = comp(640, 70, 780, "TFT 2.4\" ST7789", "plancia, sinistra", [
    ("VCC", "5V"), ("GND", "GND"), ("CS", None), ("RESET", None), ("DC", None),
    ("SDI(MOSI)", None), ("SCK", None), ("LED", None), ("SDO", None)], "l", 16)
text(710, 70 + 30 + 16 * 9 + 8, "SDO: non collegato", 6.5, DIM, anchor="c")
oleds = []
for k, (nm, y0) in enumerate((("pve1", 272), ("pve2", 368), ("pve3", 464))):
    oleds.append(comp(640, y0, 760, f"OLED {nm}", "0.96\" I2C 128x64 - frontale del PC", [
        ("GND", "GND"), ("VCC", "3V3"), ("SCL", None), ("SDA", None)], "l", 15))

# --- componenti a sinistra ---
joy = comp(40, 70, 170, "Joystick", "plancia, centro", [
    ("GND", "GND"), ("+5V", "3V3"), ("VRx", None), ("VRy", None), ("SW", None)], "r")
text(105, 70 + 30 + 17 * 5 + 6, "+5V del joystick va al 3V3!", 6.5, C5V, True, "c")
pir = comp(40, 212, 170, "PIR HC-SR501", "plancia, destra", [
    ("VCC", "5V"), ("OUT", None), ("GND", "GND")], "r")
sr = comp(40, 316, 200, "2x 74HC595 + barra", "dettaglio a pagina 2", [
    ("DS (14)", None), ("SH_CP (11)", None), ("ST_CP (12)", None), ("OE (13)", None),
    ("VCC (16)", "3V3"), ("MR (10)", "3V3"), ("GND (8)", "GND")], "r")

# --- fili di segnale ---
k = 0


def col():
    global k
    k += 1
    return PAL[(k - 1) % len(PAL)]


def to_left(p, pin, chx, label=None):
    x, y = p
    ey = lp[pin]
    cc = col()
    wire([(x + (30 if False else 0), y), (chx, y), (chx, ey), (EX0, ey)], cc)


def to_right(p, pin, chx):
    x, y = p
    ey = rp[pin]
    cc = col()
    wire([(x, y), (chx, y), (chx, ey), (EX1, ey)], cc)


# sinistra: canali tra 205 e 335
to_left(joy["VRx"], "34", 310)
to_left(joy["VRy"], "35", 300)
to_left(joy["SW"], "33", 290)
to_left(pir["OUT"], "39", 320)
to_left(sr["DS (14)"], "13", 254)
to_left(sr["SH_CP (11)"], "14", 266)
to_left(sr["ST_CP (12)"], "27", 278)

# destra: canali tra 480 e 630
to_right(tft["CS"], "5", 566)
to_right(tft["RESET"], "4", 576)
to_right(tft["DC"], "16", 586)
to_right(tft["SDI(MOSI)"], "23", 556)
to_right(tft["SCK"], "18", 546)
# SCL comune: un bus verticale
scl_x = 506
cc = col()
wire([(EX1, rp["22"]), (scl_x, rp["22"]), (scl_x, oleds[2]["SCL"][1])], cc)
for o in oleds:
    wire([(scl_x, o["SCL"][1]), o["SCL"]], cc)
    dot(scl_x, o["SCL"][1], cc)
text(scl_x - 3, oleds[2]["SCL"][1] + 10, "SCL comune", 6.5, colors.HexColor(cc))
for o, pin, chx in ((oleds[0], "21", 514), (oleds[1], "19", 522), (oleds[2], "17", 530)):
    to_right(o["SDA"], pin, chx)
# incroci: LED del TFT dal pin 25 (sinistra) e OE dal pin 15 (destra)
cc = col()
wire([(EX0, lp["25"]), (333, lp["25"]), (333, 556), (596, 556), (596, tft["LED"][1]), tft["LED"]], cc)
text(470, 549, "GPIO 25 -> LED del TFT (luminosita')", 6.5, colors.HexColor(cc), anchor="c")
cc = col()
wire([(EX1, rp["15"]), (538, rp["15"]), (538, 570), (242, 570), (242, sr["OE (13)"][1]), sr["OE (13)"]], cc)
text(350, 563, "GPIO 15 -> OE dei due 74HC595", 6.5, colors.HexColor(cc), anchor="c")

text(30, 586, "Rosso = 5V   Arancione = 3,3V   Nero = GND.  Tutti i GND insieme. I tre OLED hanno lo stesso indirizzo (0x3C): "
              "per questo SCL e' comune e ognuno ha il suo SDA.", 7.5, DIM)
c.showPage()

# =====================================================================
# PAGINA 2: barra a 10 LED con due 74HC595
# =====================================================================
text(30, 28, "Barra a 10 LED con due 74HC595 (in cascata)", 15, bold=True)
text(30, 44, "Chip visti dall'alto, tacca a sinistra in alto (pin 1 vicino alla tacca). Ogni LED ha la sua resistenza da 220 ohm. "
             "La barra ha i catodi (-) tutti verso GND.", 8, DIM)


def chip(x0, y0, name, left_nets, right_nets):
    """left: pin 1..8 dall'alto, right: pin 16..9 dall'alto. nets: (testo, colore)"""
    w, step = 90, 22
    h = step * 8 + 10
    c.setFillColor(colors.HexColor("#111827")); c.setStrokeColor(INK)
    c.roundRect(x0, Y(y0 + h), w, h, 4, fill=1, stroke=0)
    c.setFillColor(colors.white); c.circle(x0 + w / 2, Y(y0), 7, fill=1, stroke=0)
    text(x0 + w / 2, y0 + h / 2, name, 9, colors.white, True, "c")
    pos = {}
    for i in range(8):
        y = y0 + 16 + i * step
        pl, pr = i + 1, 16 - i
        for x, pin, nets, a in ((x0, pl, left_nets, "r"), (x0 + w, pr, right_nets, "l")):
            c.setFillColor(colors.HexColor("#9ca3af"))
            c.rect(x - (8 if a == "r" else 0), Y(y) - 3, 8, 6, fill=1, stroke=0)
            text(x + (4 if a == "r" else -4), y, str(pin), 6.5, colors.white, True, "l" if a == "r" else "r")
            lbl, cl = nets[i]
            text(x + (-12 if a == "r" else 12), y, lbl, 7, colors.HexColor(cl) if cl.startswith("#") else
                 {"5V": C5V, "3V3": C3V, "GND": CGND, "dim": DIM}[cl], True, a)
            pos[pin] = (x + (-8 if a == "r" else 8), y)
    return pos


LEDC = "#2ca02c"
c1 = chip(170, 80, "74HC595 n.1",
          [("Q1 -> R -> LED 2", LEDC), ("Q2 -> R -> LED 3", LEDC), ("Q3 -> R -> LED 4", LEDC), ("Q4 -> R -> LED 5", LEDC),
           ("Q5 -> R -> LED 6", LEDC), ("Q6 -> R -> LED 7", LEDC), ("Q7 -> R -> LED 8", LEDC), ("GND", "GND")],
          [("VCC -> 3V3", "3V3"), ("Q0 -> R -> LED 1", LEDC), ("DS <- ESP GPIO 13", "#1f77b4"), ("OE <- ESP GPIO 15", "#b45f06"),
           ("ST_CP <- ESP GPIO 27", "#9467bd"), ("SH_CP <- ESP GPIO 14", "#2ca02c"), ("MR -> 3V3", "3V3"),
           ("Q7' -> DS del n.2 (pin 14)", "#d62728")])
c2 = chip(170, 330, "74HC595 n.2",
          [("Q1 -> R -> LED 10", LEDC), ("Q2  libero", "dim"), ("Q3  libero", "dim"), ("Q4  libero", "dim"),
           ("Q5  libero", "dim"), ("Q6  libero", "dim"), ("Q7  libero", "dim"), ("GND", "GND")],
          [("VCC -> 3V3", "3V3"), ("Q0 -> R -> LED 9", LEDC), ("DS <- Q7' del n.1 (pin 9)", "#d62728"),
           ("OE <- GPIO 15 (come n.1)", "#b45f06"), ("ST_CP <- GPIO 27 (come n.1)", "#9467bd"),
           ("SH_CP <- GPIO 14 (come n.1)", "#2ca02c"), ("MR -> 3V3", "3V3"), ("Q7'  libero", "dim")])

# barra LED disegnata a destra
bx, by = 560, 90
text(bx + 60, by - 12, "Barra 10 LED (in piedi, accanto al display)", 9, bold=True, anchor="c")
for i in range(10):
    y = by + 12 + (9 - i) * 40          # LED 1 in basso
    text(bx - 70, y, f"dal chip -> R 220", 7, LEDC)
    c.setStrokeColor(colors.HexColor(LEDC)); c.setLineWidth(1.2); c.line(bx - 6, Y(y), bx + 10, Y(y))
    # triangolo del LED
    p = c.beginPath(); p.moveTo(bx + 10, Y(y - 7)); p.lineTo(bx + 10, Y(y + 7)); p.lineTo(bx + 24, Y(y)); p.close()
    c.setFillColor(colors.HexColor("#fde68a")); c.setStrokeColor(INK); c.drawPath(p, fill=1, stroke=1)
    c.line(bx + 24, Y(y - 7), bx + 24, Y(y + 7))
    c.setStrokeColor(CGND); c.line(bx + 24, Y(y), bx + 60, Y(y))
    text(bx + 30, y - 7, f"LED {i + 1}", 7, INK, True)
    text(bx - 12, y + 9, "+ anodo", 5.5, DIM)
    text(bx + 30, y + 7, "- catodo", 5.5, DIM)
c.setStrokeColor(CGND); c.setLineWidth(1.6); c.line(bx + 60, Y(by + 12), bx + 60, Y(by + 12 + 9 * 40))
tag(bx + 60, by + 12 + 9 * 40 + 14, "GND", "r")
c.line(bx + 60, Y(by + 12 + 9 * 40), bx + 60, Y(by + 12 + 9 * 40 + 14))

text(30, 540, "Se un LED resta spento ma gli altri vanno: la barra e' girata (anodo/catodo invertiti), girala di 180 gradi. "
              "Se si riempie dall'alto: BAR_REVERSED 1 nel firmware.", 7.5, DIM)
text(30, 554, "Il pin OE su GPIO 15 regola la luminosita' (BRIGHT_BAR) e spegne la barra all'avvio e quando il PIR non vede nessuno. "
              "Un condensatore da 100 nF tra VCC e GND vicino a ogni chip aiuta.", 7.5, DIM)
c.showPage()

# =====================================================================
# PAGINA 3: tabella e note
# =====================================================================
text(30, 28, "Tabella dei collegamenti e note", 15, bold=True)
rows = [
    ("Componente", "Pin componente", "Va a (ESP32)", "Note"),
    ("TFT 2.4\" ST7789", "VCC / GND", "VIN 5V / GND", "uguale alla v1"),
    ("", "CS / RESET / DC", "GPIO 5 / 4 / 16", "uguale alla v1"),
    ("", "SDI(MOSI) / SCK", "GPIO 23 / 18", "uguale alla v1"),
    ("", "LED", "GPIO 25", "NUOVO: prima era su 3V3. Serve per luminosita' e spegnimento"),
    ("", "SDO", "-", "non collegato (il GPIO 19 ora serve all'OLED di pve2)"),
    ("OLED pve1", "VCC / GND / SCL / SDA", "3V3 / GND / GPIO 22 / GPIO 21", "frontale del Teclast"),
    ("OLED pve2", "VCC / GND / SCL / SDA", "3V3 / GND / GPIO 22 / GPIO 19", "frontale HP in basso"),
    ("OLED pve3", "VCC / GND / SCL / SDA", "3V3 / GND / GPIO 22 / GPIO 17", "frontale HP in alto"),
    ("PIR HC-SR501", "VCC / OUT / GND", "VIN 5V / GPIO 39 (VN) / GND", "uscita a 3,3V: nessuna resistenza"),
    ("Joystick", "+5V / GND", "3V3 / GND", "a 3,3V: l'ESP legge al massimo 3,3V"),
    ("", "VRx / VRy / SW", "GPIO 34 / 35 / 33", "sinistra/destra = pagina, click = ferma pagina"),
    ("74HC595 (x2)", "DS (14) del n.1", "GPIO 13", "DS del n.2 <- Q7' (9) del n.1"),
    ("", "SH_CP (11) / ST_CP (12)", "GPIO 14 / 27", "in comune ai due chip"),
    ("", "OE (13)", "GPIO 15", "in comune ai due chip"),
    ("", "VCC (16) / MR (10) / GND (8)", "3V3 / 3V3 / GND", "su entrambi"),
    ("Barra 10 LED", "anodi LED 1-8 / 9-10", "Q0-Q7 del n.1 / Q0-Q1 del n.2", "ognuno con una resistenza da 220 ohm"),
    ("", "catodi", "GND", ""),
]
x_cols = [30, 150, 300, 480]
y = 60
for i, r in enumerate(rows):
    if i == 0:
        c.setFillColor(colors.HexColor("#e5e7eb")); c.rect(25, Y(y + 9), W - 50, 18, fill=1, stroke=0)
    elif r[0]:
        c.setStrokeColor(colors.HexColor("#d1d5db")); c.setLineWidth(0.5); c.line(25, Y(y - 9), W - 25, Y(y - 9))
    for x, s in zip(x_cols, r):
        text(x, y, s, 8, INK, i == 0 or (x == 30))
    y += 18

notes = [
    "Prima di collegare: stacca l'USB. Collega tutti i GND insieme. 5V solo a TFT e PIR, tutto il resto al 3V3.",
    "Consumo totale circa 350 mA: la USB di pve1 basta.",
    "Se il TFT con LED su GPIO 25 resta scuro o l'ESP si riavvia, rimetti LED su 3V3 e nel firmware PIN_TFT_BL -1.",
    "PIR HC-SR501: trimmer del tempo tutto a sinistra (circa 3 s), ponticello su H (riattivabile). Lo spegnimento lo decide il firmware (5 minuti).",
    "OLED non trovato: sul monitor seriale compare 'OLED pveX: non trovato'. Controlla SDA e SCL (spesso sono scambiati) e che sia un SSD1306 a 0x3C.",
    "Joystick al contrario: JOY_INVERT_X 1. Senza joystick o PIR: USE_JOY 0 / USE_PIR 0.",
    "Firmware: display_esp32/v2_completo/cluster_completo (arduino-cli, scheda esp32:esp32:esp32). "
    "Librerie: LovyanGFX, ArduinoJson, Adafruit SSD1306 + GFX. La v1 (solo TFT) resta in display_esp32/cluster_display.ino.",
]
y += 10
text(30, y, "Note", 11, bold=True)
for n in notes:
    y += 16
    text(36, y, "- " + n, 8)
c.showPage()
c.save()
print("scritto", OUT)
