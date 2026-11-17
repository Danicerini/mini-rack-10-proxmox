"""Manuale di montaggio del rack 10" (PDF A4).
Prima: python script/crea_immagini_istruzioni.py <openscad.exe>   (immagini in istruzioni/img)
Poi:   python script/crea_istruzioni_pdf.py
Le viti nella pagina "Viteria" sono disegnate in scala 1:1 (stampare al 100%)."""
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

QUI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(QUI)
IMG = os.path.join(BASE, "istruzioni", "img")
OUT = os.path.join(BASE, "istruzioni", "Manuale_montaggio_rack_10pollici.pdf")

# ---------- font e colori ----------
FD = "C:/Windows/Fonts/"
try:
    pdfmetrics.registerFont(TTFont("R", FD + "segoeui.ttf")); pdfmetrics.registerFont(TTFont("B", FD + "segoeuib.ttf"))
    pdfmetrics.registerFont(TTFont("SB", FD + "seguisb.ttf") if os.path.exists(FD + "seguisb.ttf") else TTFont("SB", FD + "segoeuib.ttf"))
    pdfmetrics.registerFont(TTFont("I", FD + "segoeuii.ttf"))
    from reportlab.lib.fonts import addMapping
    addMapping("R", 0, 0, "R"); addMapping("R", 1, 0, "B"); addMapping("R", 0, 1, "I"); addMapping("R", 1, 1, "B")
except Exception:
    raise SystemExit("Mancano i font Segoe UI in C:/Windows/Fonts")

NAVY = colors.HexColor("#141a26"); BLU = colors.HexColor("#1f7ae0"); ROSSO = colors.HexColor("#d62828")
ARANCIO = colors.HexColor("#f08c00"); GRIGIO = colors.HexColor("#c9ced6"); CHIARO = colors.HexColor("#f2f4f7")
TESTO = colors.HexColor("#23262d"); SPENTO = colors.HexColor("#6b7280"); VERDE = colors.HexColor("#2e9d57")
W, H = A4
M = 15 * mm

st_body = ParagraphStyle("b", fontName="R", fontSize=10.5, leading=14.5, textColor=TESTO)
st_small = ParagraphStyle("s", fontName="R", fontSize=9, leading=12, textColor=SPENTO)
st_box = ParagraphStyle("x", fontName="R", fontSize=9.5, leading=13, textColor=TESTO)

def para(c, txt, x, y_top, w, style=st_body):
    p = Paragraph(txt, style); _, h = p.wrap(w, 1000); p.drawOn(c, x, y_top - h); return h

def immagine(c, nome, x, y, w, h, align="c", valign="c"):
    """Disegna l'immagine dentro il riquadro (x,y = angolo in basso a sinistra) senza deformarla."""
    ir = ImageReader(os.path.join(IMG, nome)); iw, ih = ir.getSize()
    s = min(w / iw, h / ih); dw, dh = iw * s, ih * s
    dx = x + (w - dw) / 2 if align == "c" else x
    dy = y if valign == "b" else y + (h - dh) / 2
    c.drawImage(ir, dx, dy, dw, dh, mask="auto")
    return dx, dy, dw, dh

# ---------- viteria ----------
# sigla: (descrizione breve, descrizione, quantita', tipo testa, diametro, lunghezza, dove)
VITI = {
    "A": ("M6 × 35", "Vite M6 × 35 testa bombata", 20, "bombata", 6, 35, "frontali e plancia (va bene anche M6 × 40)"),
    "B": ("M6 × 25", "Vite M6 × 25 testa bombata", 8, "bombata", 6, 25, "alette posteriori dei ripiani"),
    "C": ("4 × 25", "Vite autofilettante 4 × 25 testa svasata", 8, "svasata", 4, 25, "cornici sui montanti"),
    "D": ("4 × 20", "Vite autofilettante 4 × 20 testa tonda", 4, "tonda", 4, 20, "maniglie"),
    "E": ("4 × 12", "Vite autofilettante 4 × 12 testa tonda", 4, "tonda", 4, 12, "piedini"),
    "F": ("3 × 12", "Vite autofilettante 3 × 12 testa svasata", 26, "svasata", 3, 12, "pannelli laterali e barra dello switch"),
    "G": ("M2 × 6", "Vite M2 × 6 testa bombata", 14, "bombata", 2, 6, "display OLED e sensore PIR"),
    "H": ("M2,5 × 8", "Vite M2,5 × 8 testa bombata", 4, "bombata", 2.5, 8, "joystick"),
    "I": ("M2,5 × 4", "Vite M2,5 × 4 testa bombata", 4, "bombata", 2.5, 4, "display TFT"),
    "N": ("dado M6", "Dado M6 (chiave 10)", 28, "dado", 6, 0, "nelle sedi dei montanti"),
    "R": ("rondella M6", "Rondella piana M6", 20, "rondella", 6, 0, "sotto la testa delle viti A"),
}

def badge(c, x, y, sig, r=4.2 * mm):
    c.setFillColor(ROSSO); c.roundRect(x, y, 2 * r, 2 * r, 1.6 * mm, stroke=0, fill=1)
    c.setFillColor(colors.white); c.setFont("B", r * 1.25); c.drawCentredString(x + r, y + r * 0.58, sig)

def disegna_vite(c, x, y, sig, scala=1.0):
    """Vite vista di lato, testa a sinistra, asse orizzontale in y. Scala 1 = misura reale."""
    _, _, _, tipo, d, L, _ = VITI[sig]
    k = mm * scala
    c.setStrokeColor(NAVY); c.setLineWidth(0.6); c.setFillColor(colors.HexColor("#3b4150"))
    if tipo == "dado":
        s = 10 * k; import math
        pts = [(x + s / 2 / math.cos(math.pi / 6) * math.cos(math.pi / 3 * i) + s / 1.7, y + s / 2 / math.cos(math.pi / 6) * math.sin(math.pi / 3 * i)) for i in range(6)]
        p = c.beginPath(); p.moveTo(*pts[0]); [p.lineTo(*q) for q in pts[1:]]; p.close(); c.drawPath(p, fill=1, stroke=1)
        c.setFillColor(colors.white); c.circle(x + s / 1.7, y, 3 * k, fill=1, stroke=1); return 12 * k
    if tipo == "rondella":
        c.circle(x + 6 * k, y, 6 * k, fill=1, stroke=1); c.setFillColor(colors.white); c.circle(x + 6 * k, y, 3.2 * k, fill=1, stroke=1); return 12 * k
    if tipo == "bombata":
        hd, hh = d * 1.75, d * 0.55
        p = c.beginPath(); p.moveTo(x + hh, y - hd / 2 * k / k * k)
        c.wedge(x, y - hd / 2 * k, x + 2 * hh * k, y + hd / 2 * k, 90, 180, fill=1, stroke=1)
        x0 = x + hh * k
    elif tipo == "tonda":
        hd, hh = d * 2, d * 0.7
        c.roundRect(x, y - hd / 2 * k, hh * k, hd * k, hh * k * 0.45, fill=1, stroke=1); x0 = x + hh * k
    else:  # svasata
        hd, hh = d * 2, d * 0.6
        p = c.beginPath(); p.moveTo(x, y - hd / 2 * k); p.lineTo(x, y + hd / 2 * k); p.lineTo(x + hh * k, y + d / 2 * k); p.lineTo(x + hh * k, y - d / 2 * k); p.close()
        c.drawPath(p, fill=1, stroke=1); x0 = x + hh * k
    Ls = L - (0 if tipo == "svasata" else 0)
    lung = (L - (hh if tipo == "svasata" else 0)) * k
    c.setFillColor(colors.HexColor("#7b8494")); c.rect(x0, y - d / 2 * k, lung, d * k, fill=1, stroke=1)
    passo = max(0.5, d * 0.18) * k * 1.6; c.setLineWidth(0.35); xx = x0 + passo
    while xx < x0 + lung - passo * 0.6:
        c.line(xx, y - d / 2 * k, xx + passo * 0.6, y + d / 2 * k); xx += passo
    return x0 - x + lung

# ---------- pagina ----------
pagine = []          # (titolo per l'indice, numero)

def pie(c, n):
    c.setStrokeColor(GRIGIO); c.setLineWidth(0.5); c.line(M, 13 * mm, W - M, 13 * mm)
    c.setFont("R", 8); c.setFillColor(SPENTO)
    c.drawString(M, 9 * mm, "Rack 10\" Cluster Proxmox  ·  Manuale di montaggio  ·  versione 2 (novembre 2026)")
    c.drawRightString(W - M, 9 * mm, f"{n}")

def testata(c, titolo, sotto=None):
    c.setFillColor(NAVY); c.rect(0, H - 22 * mm, W, 22 * mm, stroke=0, fill=1)
    c.setFillColor(colors.white); c.setFont("B", 20); c.drawString(M, H - 14.5 * mm, titolo)
    if sotto: c.setFont("R", 9.5); c.setFillColor(colors.HexColor("#aab4c4")); c.drawRightString(W - M, H - 14 * mm, sotto)

def riquadro(c, x, y_top, w, tipo, testo):
    """tipo: 'attenzione' (arancio) | 'consiglio' (verde) | 'info' (blu). Ritorna l'altezza."""
    col = {"attenzione": ARANCIO, "consiglio": VERDE, "info": BLU}[tipo]
    tit = {"attenzione": "ATTENZIONE", "consiglio": "CONSIGLIO", "info": "NOTA"}[tipo]
    p = Paragraph(f"<font name='B' color='{col.hexval().replace('0x', '#')}'>{tit}</font>&nbsp;&nbsp;{testo}", st_box)
    _, h = p.wrap(w - 16 * mm, 500); hh = h + 6 * mm
    c.setFillColor(colors.Color(col.red, col.green, col.blue, alpha=0.09)); c.setStrokeColor(col); c.setLineWidth(0)
    c.roundRect(x, y_top - hh, w, hh, 2 * mm, stroke=0, fill=1)
    c.setFillColor(col); c.rect(x, y_top - hh, 1.6 * mm, hh, stroke=0, fill=1)
    c.setFillColor(col); c.circle(x + 7.5 * mm, y_top - hh / 2, 3 * mm, stroke=0, fill=1)
    cx, cy = x + 7.5 * mm, y_top - hh / 2
    if tipo == "consiglio":
        c.setStrokeColor(colors.white); c.setLineWidth(1.6); c.setLineCap(1)
        p2 = c.beginPath(); p2.moveTo(cx - 1.4 * mm, cy); p2.lineTo(cx - 0.3 * mm, cy - 1.1 * mm); p2.lineTo(cx + 1.5 * mm, cy + 1.2 * mm); c.drawPath(p2, stroke=1, fill=0)
    else:
        c.setFillColor(colors.white); c.setFont("B", 11); c.drawCentredString(cx, cy - 3.8, "!" if tipo == "attenzione" else "i")
    p.drawOn(c, x + 13 * mm, y_top - hh + 3 * mm); return hh

def elenco_numerato(c, x, y_top, w, voci):
    y = y_top
    for i, v in enumerate(voci, 1):
        c.setFillColor(NAVY); c.circle(x + 3.2 * mm, y - 3.2 * mm, 3.2 * mm, stroke=0, fill=1)
        c.setFillColor(colors.white); c.setFont("B", 9.5); c.drawCentredString(x + 3.2 * mm, y - 4.5 * mm, str(i))
        h = para(c, v, x + 9 * mm, y - 0.4 * mm, w - 9 * mm); y -= max(h, 6.4 * mm) + 3 * mm
    return y_top - y

# ---------- passi ----------
# (titolo, immagine, [(sigla, q)], pezzi, voci, riquadri, inserto(immagine, didascalia) o None)
PASSI = [
    ("Piedini sotto la cornice inferiore", "passo01.png", [("E", 4)], "Pezzi: 03 cornice sotto, 10 piedini (×4)",
     ["Appoggia la <b>cornice sotto (03)</b> capovolta su un panno morbido, con il fondo a nido d'ape verso l'alto.",
      "Metti un <b>piedino (10)</b> su ciascuno dei 4 fori laterali, con la parte larga appoggiata alla cornice.",
      "Avvita una vite <b>E</b> in ogni piedino: la testa entra nella sede del piedino e non deve sporgere."],
     [("consiglio", "Avvita a mano finché senti resistenza, poi solo un quarto di giro in più. Il PLA si rovina se stringi troppo.")], None),
    ("Montanti", "passo02.png", [("C", 4)], "Pezzi: 01 montanti (×4)",
     ["Rigira la cornice sui piedini. Il <b>davanti</b> del rack è il lato con la fascia piena.",
      "Appoggia i 4 <b>montanti (01)</b> negli angoli della cornice.",
      "Da sotto, avvita una vite <b>C</b> nella svasatura di ogni angolo: entra al centro del montante."],
     [("attenzione", "Le <b>sedi esagonali dei dadi</b> di tutti e 4 i montanti devono guardare verso il <b>retro</b> del rack.")],
     ("passo02b.png", "Le viti C si avvitano da sotto")),
    ("Pannello laterale destro", "passo03.png", [("F", 12)], "Pezzi: 05 pannello laterale destro",
     ["Guardando il rack dal davanti, appoggia il <b>pannello destro (05)</b> sul fianco destro, con le svasature verso l'esterno.",
      "Avvita 6 viti <b>F</b> nel montante anteriore e 6 in quello posteriore. Inizia dai fori in alto e in basso, poi gli altri."],
     [("consiglio", "Prima metti tutte le viti senza stringerle, poi stringile tutte: il pannello si allinea da solo.")], None),
    ("Pannello laterale sinistro", "passo04.png", [("F", 12)], "Pezzi: 06 pannello laterale sinistro",
     ["Fai lo stesso sul fianco sinistro con il <b>pannello sinistro (06)</b>.",
      "Avvita 6 viti <b>F</b> per montante, svasature verso l'esterno."], [], None),
    ("Dadi nei montanti", "passo05.png", [("N", 28)], "Vista dal retro del rack",
     ["Infila i <b>dadi M6</b> nelle sedi esagonali sul retro dei montanti, solo nei fori indicati nello schema a destra.",
      "Nei <b>montanti anteriori</b> vanno 10 dadi ciascuno, nei <b>montanti posteriori</b> 4 ciascuno.",
      "Spingi ogni dado fino in fondo: deve stare a filo e non girare."],
     [("consiglio", "Se un dado scivola fuori, fermalo con un pezzetto di nastro di carta o una goccia di colla a caldo.")], "SCHEMA"),
    ("Ripiano di pve1 (Teclast)", "passo06.png", [("B", 2)], "Pezzi: 12 ripiano pve1",
     ["Cala dall'alto il <b>ripiano 12</b> fino in fondo al rack.",
      "Le alette anteriori stanno <b>davanti</b> ai montanti anteriori, quelle posteriori <b>davanti</b> ai montanti posteriori.",
      "Avvita solo le <b>2 alette posteriori</b> nel foro 1, con una vite <b>B</b> ciascuna, fino al dado."],
     [("info", "Le alette anteriori per ora restano libere: si fissano al passo 15, insieme al frontale.")], None),
    ("Ripiani di pve2 e pve3", "passo07.png", [("B", 4)], "Pezzi: 11 ripiano HP (×2)",
     ["Cala il primo <b>ripiano HP (11)</b> nel vano sopra il Teclast e avvita le alette posteriori nel <b>foro 4</b>.",
      "Cala il secondo <b>ripiano HP (11)</b> nel vano successivo e avvita le alette posteriori nel <b>foro 7</b>."],
     [("info", "I due ripiani HP sono uguali: non c'è un sopra e un sotto.")], None),
    ("Ripiano della plancia", "passo08.png", [("B", 2)], "Pezzi: 13 ripiano plancia",
     ["Cala il <b>ripiano plancia (13)</b> nel vano più in alto.",
      "Avvita le alette posteriori nel <b>foro 10</b> con 2 viti <b>B</b>."], [], None),
    ("Switch, barra di fermo e ESP32", "passo09.png", [("F", 2)], "Pezzi: 18 barra fermo switch, switch TP-Link, basetta ESP32",
     ["Metti lo <b>switch</b> nella sua tasca con le <b>porte verso il retro</b>: lo tengono la battuta davanti, i fermi dietro e le sponde ai lati.",
      "Appoggia la <b>barra (18)</b> sopra lo switch e avvitala nelle due sponde con 2 viti <b>F</b>.",
      "Metti la <b>basetta dell'ESP32</b> nella sua sede davanti allo switch, con il connettore USB verso il retro."],
     [("info", "La barra preme appena sullo switch: così non si solleva quando colleghi i cavi di rete.")], None),
    ("Cornice superiore", "passo10.png", [("C", 4)], "Pezzi: 04 cornice sopra",
     ["Appoggia la <b>cornice sopra (04)</b> sui montanti, con la scritta CLUSTER PROXMOX sul davanti.",
      "Avvita dall'alto una vite <b>C</b> nella svasatura di ogni angolo."], [], None),
    ("Maniglie", "passo11.png", [("D", 4)], "Pezzi: 09 maniglie (×2)",
     ["Appoggia le due <b>maniglie (09)</b> sui fori ai lati della cornice sopra.",
      "Avvita 2 viti <b>D</b> per maniglia: la testa scende nella sede della maniglia."],
     [("attenzione", "Solleva il rack dalle maniglie solo quando è tutto avvitato.")], None),
    ("Elettronica della plancia", "passo12.png", [("I", 4), ("H", 4), ("G", 2)], "Pezzi: 17 plancia, display TFT, barra LED, joystick, sensore PIR",
     ["<b>Display TFT</b>: appoggia il circuito rosso nell'incavo sul retro, con il vetro dentro la finestra. Fissalo con 4 viti <b>I</b>.",
      "<b>Barra LED</b>: infilala dal retro nella sua tasca, a pressione.",
      "<b>Joystick</b>: la levetta passa nel foro tondo. Avvita il circuito sulle 4 torrette alte con 4 viti <b>H</b>.",
      "<b>Sensore PIR</b>: la lente bianca entra nel foro quadrato. Fissalo con 2 viti <b>G</b>.",
      "Collega i cavi Dupont seguendo lo <b>schema dei collegamenti</b> (cartella display_esp32)."],
     [("attenzione", "Le viti del TFT vanno strette poco: il vetro si crepa facilmente.")],
     ("passo12b.png", "La plancia vista da davanti")),
    ("Display OLED sui frontali", "passo13.png", [("G", 12)], "Pezzi: 14, 15, 16 frontali",
     ["Sul retro di ogni frontale appoggia un <b>display OLED</b> sulle 4 torrette, con lo schermo nella finestrella.",
      "Fissa ogni display con 4 viti <b>G</b>.",
      "Frontale <b>14 = pve1</b>, <b>15 = pve2</b>, <b>16 = pve3</b>: il nome è inciso sotto la finestrella."],
     [("attenzione", "Non premere sul vetro dell'OLED: è sottile e si rompe.")], None),
    ("Mini PC nei vani", "passo14.png", [], "Teclast N30, HP EliteDesk 800 G2, HP EliteDesk 800 G5",
     ["Infila i PC dal davanti: il <b>Teclast N30 (pve1)</b> in basso, l'<b>HP 800 G2 (pve2)</b> sopra, l'<b>HP 800 G5 (pve3)</b> nel vano successivo.",
      "Ogni PC supera il bordo del ripiano e si appoggia alla sponda sinistra e alla guida destra.",
      "Collega dal retro i cavi di rete e di alimentazione (vedi la pagina <b>Collegamenti</b>)."],
     [("consiglio", "Collega i cavi adesso, finché davanti è ancora aperto: dopo è più scomodo.")], None),
    ("Frontali e plancia", "passo15.png", [("A", 20), ("R", 20)], "Pezzi: 14, 15, 16 frontali e 17 plancia",
     ["Avvita i frontali dal basso verso l'alto: <b>14 (pve1)</b>, <b>15 (pve2)</b>, <b>16 (pve3)</b> e infine la <b>plancia (17)</b>.",
      "Ogni vite <b>A</b>, con la <b>rondella</b>, passa nel frontale, nell'aletta del ripiano e nel montante, e si chiude sul dado.",
      "Servono 4 viti per ogni frontale e 8 per la plancia."],
     [("info", "Fori usati, contando dal basso: pve1 → 1 e 3; pve2 → 4 e 6; pve3 → 7 e 9; plancia → 10, 12, 13 e 15.")], None),
]

PEZZI = [("01", "Montante", 4, "Nero"), ("03", "Cornice sotto", 1, "Bianco"), ("04", "Cornice sopra", 1, "Bianco"),
         ("05", "Pannello destro", 1, "Nero"), ("06", "Pannello sinistro", 1, "Nero"), ("09", "Maniglia", 2, "Bianco"),
         ("10", "Piedino", 4, "Bianco"), ("11", "Ripiano HP", 2, "Nero"), ("12", "Ripiano pve1 (Teclast)", 1, "Nero"),
         ("13", "Ripiano plancia", 1, "Nero"), ("14", "Frontale pve1", 1, "Nero"), ("15", "Frontale pve2", 1, "Nero"),
         ("16", "Frontale pve3", 1, "Nero"), ("17", "Plancia inclinata", 1, "Nero"), ("18", "Barra fermo switch", 1, "Nero")]

# ---------- costruzione ----------
c = canvas.Canvas(OUT, pagesize=A4)
c.setTitle("Rack 10\" Cluster Proxmox - Manuale di montaggio"); c.setAuthor("Danicerini")
num = [0]
def nuova():
    if num[0]: c.showPage()
    num[0] += 1

# numeri di pagina (per l'indice)
P_COP, P_IND, P_ATT, P_PEZ, P_VIT, P_ALT = 1, 2, 3, 4, 5, 6
P_PASSO1 = 7
P_COLL = P_PASSO1 + len(PASSI); P_FINE = P_COLL + 1

# 1. copertina
nuova()
c.setFillColor(NAVY); c.rect(0, H - 78 * mm, W, 78 * mm, stroke=0, fill=1)
c.setFillColor(BLU); c.rect(0, H - 80 * mm, W, 2 * mm, stroke=0, fill=1)
c.setFillColor(colors.HexColor("#8fb8ef")); c.setFont("SB", 11); c.drawString(M + 2 * mm, H - 24 * mm, "MANUALE DI MONTAGGIO")
c.setFillColor(colors.white); c.setFont("B", 38); c.drawString(M + 2 * mm, H - 42 * mm, "Rack 10\" Cluster")
c.setFont("R", 15); c.setFillColor(colors.HexColor("#c9d3e2")); c.drawString(M + 2 * mm, H - 53 * mm, "Armadio stampato in 3D per tre mini PC Proxmox,")
c.drawString(M + 2 * mm, H - 60.5 * mm, "switch di rete e plancia di controllo")
immagine(c, "copertina.png", M, 52 * mm, W - 2 * M, H - 140 * mm)
y = 34 * mm; bw = (W - 2 * M - 8 * mm) / 3
for i, (t, v) in enumerate([("TEMPO", "circa 2 ore"), ("PERSONE", "1"), ("MISURE", "260 × 220 × 293 mm")]):
    x = M + i * (bw + 4 * mm)
    c.setFillColor(CHIARO); c.roundRect(x, y, bw, 15 * mm, 2 * mm, stroke=0, fill=1)
    c.setFillColor(SPENTO); c.setFont("SB", 8); c.drawString(x + 5 * mm, y + 9.5 * mm, t)
    c.setFillColor(NAVY); c.setFont("B", 12); c.drawString(x + 5 * mm, y + 3.6 * mm, v)
c.setFont("R", 8.5); c.setFillColor(SPENTO)
c.drawString(M, 22 * mm, "Versione 2 · novembre 2026 · 15 pezzi stampati in PLA · leggi tutto il manuale prima di iniziare.")
pie(c, num[0])

# 2. indice e come leggere
nuova(); testata(c, "Indice"); pie(c, num[0])
voci = [("Prima di iniziare: attrezzi e avvertenze", P_ATT), ("Pezzi stampati", P_PEZ), ("Viteria (disegni in scala 1:1)", P_VIT),
        ("Componenti da comprare", P_ALT)] + [(f"Passo {i}: {p[0]}", P_PASSO1 + i - 1) for i, p in enumerate(PASSI, 1)] + \
       [("Collegamenti", P_COLL), ("Controlli finali e problemi comuni", P_FINE)]
y = H - 34 * mm
for t, n in voci:
    c.setFont("R", 10.5); c.setFillColor(TESTO); c.drawString(M, y, t)
    tw = c.stringWidth(t, "R", 10.5); c.setFillColor(GRIGIO)
    c.setFont("R", 10.5); dots = "." * int((W - 2 * M - tw - 12 * mm) / c.stringWidth(".", "R", 10.5))
    c.drawString(M + tw + 2 * mm, y, dots); c.setFillColor(NAVY); c.setFont("B", 10.5); c.drawRightString(W - M, y, str(n)); y -= 6.6 * mm
y -= 6 * mm
c.setFillColor(NAVY); c.setFont("B", 14); c.drawString(M, y, "Come leggere le figure"); y -= 9 * mm
leg = [(BLU, "Blu", "il pezzo da montare in quel passaggio"), (GRIGIO, "Grigio", "i pezzi già montati"),
       (ROSSO, "Rosso", "viti e dadi, con la linea che indica il foro"), (ARANCIO, "Arancione", "la direzione in cui muovere il pezzo")]
for col, n, d in leg:
    c.setFillColor(col); c.roundRect(M, y - 1.5 * mm, 9 * mm, 5.5 * mm, 1.2 * mm, stroke=0, fill=1)
    c.setFillColor(TESTO); c.setFont("B", 10.5); c.drawString(M + 13 * mm, y, n); c.setFont("R", 10.5); c.drawString(M + 36 * mm, y, d); y -= 8 * mm
y -= 2 * mm
y -= riquadro(c, M, y, W - 2 * M, "info", "I numeri tra parentesi, per esempio <b>(13)</b>, sono i numeri dei pezzi stampati. "
              "Le lettere nei quadratini rossi, per esempio <b>C</b>, sono le viti della pagina Viteria. "
              "I <b>fori dei montanti</b> si contano dal basso, da 1 a 15.")

# 3. prima di iniziare
nuova(); testata(c, "Prima di iniziare"); pie(c, num[0])
y = H - 34 * mm
c.setFillColor(NAVY); c.setFont("B", 14); c.drawString(M, y, "Attrezzi necessari"); y -= 8 * mm
attr = [("Cacciavite a croce PH2", "viti autofilettanti C, D, E, F"), ("Chiave a brugola 4 mm", "viti M6 (A, B)"),
        ("Chiave a brugola 1,5 mm", "viti M2,5 (H, I)"), ("Chiave a brugola 1,3 mm", "viti M2 (G)"),
        ("Chiave fissa da 10 o pinza", "per tenere fermi i dadi M6"), ("Nastro di carta o colla a caldo", "per bloccare i dadi che scivolano")]
for t, d in attr:
    c.setFillColor(CHIARO); c.roundRect(M, y - 4 * mm, W - 2 * M, 8.5 * mm, 1.5 * mm, stroke=0, fill=1)
    c.setFillColor(NAVY); c.setFont("B", 10.5); c.drawString(M + 4 * mm, y - 1 * mm, t)
    c.setFillColor(SPENTO); c.setFont("R", 10); c.drawString(M + 80 * mm, y - 1 * mm, d); y -= 10.5 * mm
y -= 4 * mm
c.setFillColor(NAVY); c.setFont("B", 14); c.drawString(M, y, "Avvertenze"); y -= 5 * mm
for tipo, t in [("attenzione", "I pezzi sono in <b>PLA</b>: stringi le viti a mano, senza forzare. Se usi un avvitatore, mettilo alla coppia più bassa."),
                ("attenzione", "Non lasciare il rack al sole o vicino a fonti di calore: il PLA si deforma sopra i 55 °C."),
                ("consiglio", "Prima di iniziare dividi la viteria per lettera, per esempio in una vaschetta per uova."),
                ("consiglio", "Lavora su un tavolo coperto da un panno, così non righi i pezzi."),
                ("info", "Il davanti del rack è il lato con la fascia piena nelle cornici e la plancia inclinata.")]:
    y -= riquadro(c, M, y, W - 2 * M, tipo, t) + 3 * mm

# 4. pezzi stampati
nuova(); testata(c, "Pezzi stampati", "15 tipi di pezzo · 24 pezzi in tutto"); pie(c, num[0])
cols, gap = 3, 4 * mm; cw = (W - 2 * M - (cols - 1) * gap) / cols; ch = 46 * mm
for i, (n, nome, q, col) in enumerate(PEZZI):
    x = M + (i % cols) * (cw + gap); yb = H - 30 * mm - (i // cols + 1) * (ch + gap) + gap
    c.setFillColor(CHIARO); c.roundRect(x, yb, cw, ch, 2.5 * mm, stroke=0, fill=1)
    c.setFillColor(colors.white); c.roundRect(x + 2 * mm, yb + 12 * mm, cw - 4 * mm, ch - 14 * mm, 1.8 * mm, stroke=0, fill=1)
    immagine(c, f"pezzo_{n}.png", x + 4 * mm, yb + 13 * mm, cw - 8 * mm, ch - 16 * mm)
    c.setFillColor(NAVY); c.circle(x + 6.5 * mm, yb + 6 * mm, 4.2 * mm, stroke=0, fill=1)
    c.setFillColor(colors.white); c.setFont("B", 10); c.drawCentredString(x + 6.5 * mm, yb + 4.4 * mm, n)
    c.setFillColor(TESTO); c.setFont("SB", 9.5); c.drawString(x + 12.5 * mm, yb + 6.8 * mm, nome)
    c.setFont("R", 8.5); c.setFillColor(SPENTO); c.drawString(x + 12.5 * mm, yb + 2.6 * mm, col)
    c.setFillColor(colors.HexColor("#f2f2ee") if col == "Bianco" else colors.HexColor("#2a2d33")); c.setStrokeColor(GRIGIO); c.setLineWidth(0.5)
    c.circle(x + 12.5 * mm + c.stringWidth(col, "R", 8.5) + 3 * mm, yb + 3.4 * mm, 1.5 * mm, stroke=1, fill=1)
    c.setFillColor(NAVY); c.setFont("B", 13); c.drawRightString(x + cw - 3 * mm, yb + 4 * mm, f"×{q}")

# 5. viteria 1:1
nuova(); testata(c, "Viteria", "disegni in scala 1:1"); pie(c, num[0])
y = H - 30 * mm
y -= riquadro(c, M, y, W - 2 * M, "info", "Stampa questa pagina <b>al 100%</b> (senza \"adatta alla pagina\"): appoggia la vite sul disegno per controllare che sia quella giusta.") + 4 * mm
ordine = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "N", "R"]
rh = 17.5 * mm
for sig in ordine:
    breve, desc, q, tipo, d, L, dove = VITI[sig]
    c.setFillColor(CHIARO); c.roundRect(M, y - rh, W - 2 * M, rh - 2 * mm, 2 * mm, stroke=0, fill=1)
    badge(c, M + 4 * mm, y - rh / 2 - 5.2 * mm, sig, 5 * mm)
    c.setFillColor(NAVY); c.setFont("B", 11); c.drawString(M + 18 * mm, y - 7 * mm, desc)
    c.setFillColor(SPENTO); c.setFont("R", 9); c.drawString(M + 18 * mm, y - 12 * mm, "per: " + dove)
    disegna_vite(c, M + 112 * mm, y - rh / 2 - 1 * mm, sig)
    c.setFillColor(NAVY); c.setFont("B", 15); c.drawRightString(W - M - 4 * mm, y - rh / 2 - 3 * mm, f"×{q}")
    y -= rh

# 6. componenti da comprare
nuova(); testata(c, "Componenti da comprare", "non stampati"); pie(c, num[0])
y = H - 34 * mm
grp = [("Computer e rete", [("Teclast N30 (pve1)", "mini PC, 114 × 106 × 43,5 mm", "1"), ("HP EliteDesk 800 G2 Mini (pve2)", "177 × 175 × 34 mm", "1"),
                             ("HP EliteDesk 800 G5 Mini (pve3)", "177 × 175 × 34 mm", "1"), ("Switch TP-Link TL-SG608E", "8 porte, 158 × 100 × 25 mm", "1"),
                             ("Cavi di rete RJ45 corti", "Cat 6, da 0,25 a 0,5 m", "4"), ("Cavo USB per dati", "dall'ESP32 a pve1 (non solo ricarica)", "1")]),
       ("Elettronica della plancia", [("ESP32 DevKit con basetta a morsetti", "basetta 77 × 63 mm", "1"), ("Display TFT 2,4\" ST7789", "circuito rosso, 320 × 240", "1"),
                                      ("Display OLED 0,96\" SSD1306", "bianchi, I2C indirizzo 0x3C", "3"), ("Barra LED a 10 segmenti", "con due 74HC595 su millefori", "1"),
                                      ("Joystick KY-023", "34 × 26 mm", "1"), ("Sensore di movimento HC-SR501", "con lente quadrata", "1"),
                                      ("Cavi Dupont femmina-femmina", "20 cm", "circa 30")])]
for g, rows in grp:
    c.setFillColor(NAVY); c.setFont("B", 14); c.drawString(M, y, g); y -= 4 * mm
    for i, (a, b, q) in enumerate(rows):
        c.setFillColor(CHIARO if i % 2 == 0 else colors.white); c.rect(M, y - 8 * mm, W - 2 * M, 8 * mm, stroke=0, fill=1)
        c.setFillColor(TESTO); c.setFont("SB", 10); c.drawString(M + 3 * mm, y - 5.4 * mm, a)
        c.setFillColor(SPENTO); c.setFont("R", 9.5); c.drawString(M + 88 * mm, y - 5.4 * mm, b)
        c.setFillColor(NAVY); c.setFont("B", 10); c.drawRightString(W - M - 3 * mm, y - 5.4 * mm, q); y -= 8 * mm
    y -= 9 * mm
riquadro(c, M, y, W - 2 * M, "info", "Lo schema dei fili tra plancia, OLED ed ESP32 è in <b>display_esp32/v2_completo/Schema_collegamenti.pdf</b>.")

# schema dei fori per il passo 5
def schema_dadi(c, x, y_top, h):
    mz = [6.35, 25.5, 44.65] + [51 + u * 44.45 + hz for u in range(4) for hz in (6.35, 22.225, 38.1)]
    tot = 51 + 4 * 44.45; s = h / tot
    for j, (tit, usati) in enumerate([("Anteriori", {1, 3, 4, 6, 7, 9, 10, 12, 13, 15}), ("Posteriori", {1, 4, 7, 10})]):
        xx = x + j * 30 * mm
        c.setFillColor(NAVY); c.setFont("B", 9.5); c.drawCentredString(xx + 6 * mm, y_top + 3 * mm, tit)
        c.setFillColor(colors.HexColor("#2a2d33")); c.roundRect(xx + 2 * mm, y_top - h, 8 * mm, h, 1 * mm, stroke=0, fill=1)
        for i, z in enumerate(mz, 1):
            yy = y_top - h + z * s
            if i in usati:
                c.setFillColor(ROSSO); import math
                p = c.beginPath(); r = 3.1 * mm
                for k in range(6):
                    a = math.pi / 3 * k + math.pi / 6; px, py = xx + 6 * mm + r * math.cos(a), yy + r * math.sin(a)
                    p.moveTo(px, py) if k == 0 else p.lineTo(px, py)
                p.close(); c.drawPath(p, stroke=0, fill=1)
            c.setFillColor(colors.white); c.circle(xx + 6 * mm, yy, 1.4 * mm, stroke=0, fill=1)
            c.setFillColor(SPENTO if i not in usati else ROSSO); c.setFont("B" if i in usati else "R", 7.5)
            c.drawRightString(xx + 0.5 * mm, yy - 1.2 * mm, str(i))
    c.setFillColor(SPENTO); c.setFont("R", 8); c.drawString(x - 2 * mm, y_top - h - 5 * mm, "foro 1 = il più in basso")

def altezza_testo(voci_p, box):
    h = 0
    for v in voci_p:
        p = Paragraph(v, st_body); _, hh = p.wrap(W - 2 * M - 9 * mm, 1000); h += max(hh, 6.4 * mm) + 3 * mm
    h += 2 * mm
    for tipo, t in box:
        p = Paragraph("XXXXXXXXXXXX " + t, st_box); _, hh = p.wrap(W - 2 * M - 16 * mm, 500); h += hh + 6 * mm + 3 * mm
    return h

# 7+. passi
for i, (tit, img, viti, pezzi, voci_p, box, inserto) in enumerate(PASSI, 1):
    nuova(); pie(c, num[0])
    c.setFillColor(NAVY); c.rect(0, H - 30 * mm, W, 30 * mm, stroke=0, fill=1)
    c.setFillColor(BLU); c.circle(M + 10 * mm, H - 15 * mm, 10 * mm, stroke=0, fill=1)
    c.setFillColor(colors.white); c.setFont("B", 24); c.drawCentredString(M + 10 * mm, H - 18.6 * mm, str(i))
    c.setFont("B", 18); c.drawString(M + 25 * mm, H - 13.5 * mm, tit)
    c.setFont("R", 9.5); c.setFillColor(colors.HexColor("#aab4c4")); c.drawString(M + 25 * mm, H - 20.5 * mm, pezzi)
    c.setFont("R", 8.5); c.drawRightString(W - M, H - 26 * mm, f"passo {i} di {len(PASSI)}")
    # ti servono
    if viti:
        bx = W - M; yy = H - 13 * mm
        for sig, q in reversed(viti):
            txt = f"×{q}"; c.setFont("B", 12); tw = c.stringWidth(txt, "B", 12)
            bx -= tw; c.setFillColor(colors.white); c.drawString(bx, yy - 1.6 * mm, txt)
            bx -= 10 * mm; badge(c, bx, yy - 4 * mm, sig, 4 * mm); bx -= 6 * mm
    # immagine
    img_top = H - 34 * mm
    div = 20 * mm + altezza_testo(voci_p, box) + 8 * mm
    ib = div + 4 * mm
    if inserto == "SCHEMA":
        immagine(c, img, M, ib, 118 * mm, img_top - ib)
        schema_dadi(c, M + 132 * mm, img_top - 10 * mm, img_top - ib - 20 * mm)
    elif inserto:
        iw, ih = 62 * mm, 56 * mm
        ir = ImageReader(os.path.join(IMG, img)); a_w, a_h = ir.getSize()
        if a_w / a_h > 1.8:   # immagine larga: a tutta pagina in basso, riquadro in alto a destra
            immagine(c, img, M, ib, W - 2 * M, img_top - ib - ih - 2 * mm, valign="b"); ix, iy = W - M - iw, img_top - ih
        else:
            immagine(c, img, M, ib, W - 2 * M - 66 * mm, img_top - ib); ix, iy = W - M - iw, ib + 4 * mm
        c.setFillColor(colors.white); c.setStrokeColor(GRIGIO); c.setLineWidth(0.8); c.roundRect(ix, iy, iw, ih, 2 * mm, stroke=1, fill=1)
        immagine(c, inserto[0], ix + 2 * mm, iy + 8 * mm, iw - 4 * mm, ih - 10 * mm)
        c.setFillColor(SPENTO); c.setFont("I", 8.5); c.drawCentredString(ix + iw / 2, iy + 3 * mm, inserto[1])
    else:
        immagine(c, img, M, ib, W - 2 * M, img_top - ib)
    # testo
    c.setStrokeColor(GRIGIO); c.setLineWidth(0.5); c.line(M, div, W - M, div)
    y = div - 5 * mm
    y -= elenco_numerato(c, M, y, W - 2 * M, voci_p) + 2 * mm
    for tipo, t in box:
        y -= riquadro(c, M, y, W - 2 * M, tipo, t) + 3 * mm

# collegamenti
nuova(); testata(c, "Collegamenti", "dal retro del rack"); pie(c, num[0])
immagine(c, "finito_sx.png", M, H - 120 * mm, 80 * mm, 84 * mm)
y = H - 36 * mm; x = M + 88 * mm; w = W - M - x
coll = [("pve1, pve2, pve3", "→ switch", "cavo RJ45 corto in una porta qualsiasi"), ("Switch", "→ router", "cavo RJ45 che esce dal retro"),
        ("Alimentatori", "→ ciabatta", "dei 3 PC e dello switch"), ("ESP32", "→ pve1", "cavo USB per dati"),
        ("Plancia e OLED", "→ ESP32", "cavi Dupont, come nello schema")]
for a, b, d in coll:
    c.setFillColor(CHIARO); c.roundRect(x, y - 13 * mm, w, 12 * mm, 1.8 * mm, stroke=0, fill=1)
    c.setFillColor(NAVY); c.setFont("B", 10.5); c.drawString(x + 3 * mm, y - 5.6 * mm, a); c.setFillColor(BLU); c.drawString(x + 40 * mm, y - 5.6 * mm, b)
    c.setFillColor(SPENTO); c.setFont("R", 9); c.drawString(x + 3 * mm, y - 10.4 * mm, d); y -= 14.5 * mm
y = H - 128 * mm
for tipo, t in [("attenzione", "Il cavo USB tra ESP32 e pve1 deve essere un cavo <b>per dati</b>: con un cavo solo di ricarica pve1 non vede l'ESP32 e i display non ricevono niente."),
                ("attenzione", "Collega e scollega i fili della plancia solo con l'USB staccato: altrimenti l'ESP32 si riavvia."),
                ("consiglio", "Raccogli i cavi con fascette lungo i montanti posteriori, così l'aria passa e il rack resta ordinato."),
                ("info", "I PC si accendono dal pulsante sul davanti, visibile nell'apertura dei frontali.")]:
    y -= riquadro(c, M, y, W - 2 * M, tipo, t) + 3 * mm

# fine
nuova(); testata(c, "Controlli finali e problemi comuni"); pie(c, num[0])
y = H - 34 * mm
c.setFillColor(NAVY); c.setFont("B", 14); c.drawString(M, y, "Prima di accendere, controlla che:"); y -= 8 * mm
for t in ["tutte le viti siano strette e nessuna giri a vuoto;", "i frontali siano a filo e non tocchino i PC;",
          "lo switch non si muova quando infili un cavo di rete;", "il rack non dondoli: i 4 piedini devono toccare il tavolo;",
          "dietro ci siano almeno 5 cm liberi per l'aria."]:
    c.setStrokeColor(BLU); c.setLineWidth(1.2); c.roundRect(M, y - 1.2 * mm, 4.2 * mm, 4.2 * mm, 0.8 * mm, stroke=1, fill=0)
    c.setFillColor(TESTO); c.setFont("R", 10.5); c.drawString(M + 8 * mm, y, t); y -= 8 * mm
y -= 6 * mm
c.setFillColor(NAVY); c.setFont("B", 14); c.drawString(M, y, "Problemi comuni"); y -= 6 * mm
prob = [("Una vite autofilettante gira a vuoto", "Il foro si è allargato. Infila uno stuzzicadenti con un po' di colla vinilica, lascia asciugare e riavvita."),
        ("Un dado M6 gira insieme alla vite", "Tienilo fermo con una chiave da 10 o una pinza; se continua, bloccalo con una goccia di colla a caldo."),
        ("Il frontale non va a filo", "Controlla che le alette del ripiano siano davanti al montante e non dietro."),
        ("Un PC non entra nel vano", "Controlla che il PC sia quello giusto per il vano e che non ci siano cavi sotto."),
        ("I display non mostrano i dati", "Controlla il cavo USB per dati tra ESP32 e pve1 e i fili Dupont secondo lo schema."),
        ("Un OLED resta spento", "Controlla i suoi 4 fili: GND, VCC, SCL e SDA. Scollega l'USB prima di toccarli.")]
for a, b in prob:
    c.setFillColor(CHIARO); p = Paragraph(b, st_box); _, hb = p.wrap(W - 2 * M - 70 * mm, 200); hh = max(hb, 5 * mm) + 6 * mm
    c.roundRect(M, y - hh, W - 2 * M, hh, 1.8 * mm, stroke=0, fill=1)
    pa = Paragraph(f"<b>{a}</b>", st_box); pa.wrap(62 * mm, 100); pa.drawOn(c, M + 3 * mm, y - 3 * mm - pa.height)
    p.drawOn(c, M + 68 * mm, y - 3 * mm - hb); y -= hh + 2.5 * mm
immagine(c, "copertina.png", W / 2 - 35 * mm, 18 * mm, 70 * mm, max(20 * mm, y - 24 * mm))
c.save()
print("creato", OUT, "pagine:", num[0])
