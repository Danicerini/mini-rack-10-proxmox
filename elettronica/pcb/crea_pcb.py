"""Crea la PCB della plancia (ESP32 30 pin + 2x 74HC595 + connettori JST-XH).

Uso (con il Python di KiCad 10):
  python.exe crea_pcb.py tht|smd [ses]
    tht / smd : versione da saldare a mano o da far montare a JLCPCB
    ses       : importa lo sbroglio di Freerouting (out/<v>.ses) invece di creare il .dsn

Coordinate in mm, origine in alto a sinistra, y verso il basso.
In alto (y = 0) c'e' il retro della tasca: li' esce l'USB dell'ESP verso pve1.
I pin sono quelli del firmware v2 (display_esp32/v2_completo): il codice non cambia.
"""
import os, sys
import pcbnew

V = sys.argv[1] if len(sys.argv) > 1 else "tht"
SES = len(sys.argv) > 2 and sys.argv[2] == "ses"
QUI = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(QUI, "out"); os.makedirs(OUT, exist_ok=True)
FP = os.path.join(os.path.dirname(os.path.dirname(pcbnew.__file__)), "share", "kicad", "footprints")
if not os.path.isdir(FP):
    FP = os.environ.get("KICAD_FOOTPRINTS", r"C:\Program Files\KiCad\10.0\share\kicad\footprints")

W, H = 70.0, 47.0            # 14/11: accorciata (prima 63,3 come la basetta); l'antenna dell'ESP sporge oltre il bordo
HOLE_C, HOLE_D = 1.75, 1.6   # fori come quelli della basetta (diametro 1,5 -> 1,6 per M1.4)
MM = pcbnew.FromMM
b = pcbnew.BOARD()
b.SetCopperLayerCount(2)
nets = {}

def net(n):
    if n not in nets:
        ni = pcbnew.NETINFO_ITEM(b, n); b.Add(ni); nets[n] = ni
    return nets[n]

def place(lib, name, ref, val, x, y, rot=0, pins=None, side_note=None):
    fp = pcbnew.FootprintLoad(os.path.join(FP, lib + ".pretty"), name)
    if fp is None: raise SystemExit(f"impronta mancante: {lib}:{name}")
    fp.SetReference(ref); fp.SetValue(val)
    fp.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y))); fp.SetOrientationDegrees(rot)
    b.Add(fp)
    for pad in fp.Pads():
        n = (pins or {}).get(pad.GetNumber())
        if n: pad.SetNet(net(n))
    return fp

# ---------------------------------------------------------------- ESP32 DevKit 30 pin
# Visto dall'alto con l'USB in alto: a sinistra la fila 3V3..D23, a destra VIN..EN.
ESP_L = ["+3V3", "GND", "IO15_OE", "IO2", "IO4_TFT_RST", "IO16_TFT_DC", "IO17_SDA3", "IO5_TFT_CS",
         "IO18_SCK", "IO19_SDA2", "IO21_SDA1", "RX0", "TX0", "IO22_SCL", "IO23_MOSI"]
ESP_R = ["+5V", "GND", "IO13_DS", "IO12", "IO14_SHCP", "IO27_STCP", "IO26", "IO25_TFT_LED",
         "IO33_JOY_SW", "IO32", "IO35_JOY_Y", "IO34_JOY_X", "IO39_PIR", "IO36", "EN"]
NC = {"IO2", "RX0", "TX0", "IO12", "IO26", "IO32", "IO36", "EN"}
ESP_X0, ESP_DX, ESP_Y0 = 22.3, 25.4, 5.0       # file a 25,4 mm (da verificare con la stampa 1:1)
place("Connector_PinSocket_2.54mm", "PinSocket_1x15_P2.54mm_Vertical", "J1", "ESP32 sx (3V3..D23)",
      ESP_X0, ESP_Y0, 0, {str(i + 1): n for i, n in enumerate(ESP_L) if n not in NC})
place("Connector_PinSocket_2.54mm", "PinSocket_1x15_P2.54mm_Vertical", "J2", "ESP32 dx (VIN..EN)",
      ESP_X0 + ESP_DX, ESP_Y0, 0, {str(i + 1): n for i, n in enumerate(ESP_R) if n not in NC})

# ---------------------------------------------------------------- connettori JST-XH (passo 2,5)
XH = "Connector_JST"
ETICHETTE = []   # (testo, x, y, dimensione): scritte sulla serigrafia, aggiunte piu' sotto
def xh(n, ref, val, x, y, pins, nome=None, nomi_pin=None, lato_pin="dx"):
    """Corpo del JST-XH ruotato: da x-3,45 a x+2,4; pin 1 in alto (lato USB)."""
    name = f"JST_XH_B{n}B-XH-A_1x{n:02d}_P2.50mm_Vertical"
    fp = place(XH, name, ref, val, x, y, -90, {str(i + 1): p for i, p in enumerate(pins)})
    if nome: ETICHETTE.append((nome, x - 0.5 + (0.7 if x < 5 else 0), y - 3.4, 0.8))
    for i, t in enumerate(nomi_pin or []):
        ETICHETTE.append((t, x + 4.0 if lato_pin == "dx" else x - 4.85, y + i * 2.5, 0.8))
    # sigla J3... nascosta sulla serigrafia: al suo posto ci sono il nome sopra e i nomi dei pin
    if nome: fp.Reference().SetVisible(False)
    return fp

# lato sinistro: TFT e OLED (stesso ordine dei pin dei moduli -> cavi dritti)
OLED = ["GND", "VCC", "SCL", "SDA"]
xh(8, "J3", "TFT: VCC GND CS RST DC MOSI SCK LED", 4.0, 9.0,
   ["+5V", "GND", "IO5_TFT_CS", "IO4_TFT_RST", "IO16_TFT_DC", "IO23_MOSI", "IO18_SCK", "IO25_TFT_LED"],
   "TFT", ["VCC", "GND", "CS", "RST", "DC", "MOSI", "SCK", "LED"])
xh(4, "J4", "OLED pve1: GND VCC SCL SDA", 4.0, 33.5, ["GND", "+3V3", "IO22_SCL", "IO21_SDA1"], "OLED pve1", OLED)
xh(4, "J5", "OLED pve2: GND VCC SCL SDA", 13.0, 9.0, ["GND", "+3V3", "IO22_SCL", "IO19_SDA2"], "OLED pve2", OLED)
xh(4, "J6", "OLED pve3: GND VCC SCL SDA", 13.0, 23.5, ["GND", "+3V3", "IO22_SCL", "IO17_SDA3"], "OLED pve3", OLED)
# lato destro: barra, joystick, PIR
xh(11, "J7", "Barra LED: anodi 1-10, GND", 57.5, 9.0, [f"LED{i}" for i in range(1, 11)] + ["GND"],
   "BARRA LED", [f"L{i}" for i in range(1, 11)] + ["GND"], "sx")
xh(5, "J8", "Joystick: GND V SW? -> GND 3V3 VRX VRY SW", 66.4, 9.0,
   ["GND", "+3V3", "IO34_JOY_X", "IO35_JOY_Y", "IO33_JOY_SW"], "JOYSTICK", ["GND", "VCC", "X", "Y", "SW"], "sx")
xh(3, "J9", "PIR: VCC OUT GND", 66.4, 26.0, ["+5V", "IO39_PIR", "GND"], "PIR", ["VCC", "OUT", "GND"], "sx")

# ---------------------------------------------------------------- 74HC595 x2 (sotto l'ESP)
def hc595(ref, x, y, ds, q):
    pins = {"16": "+3V3", "10": "+3V3", "8": "GND", "14": ds, "11": "IO14_SHCP", "12": "IO27_STCP", "13": "IO15_OE"}
    for pin, n in zip(["15", "1", "2", "3", "4", "5", "6", "7"], q): pins[pin] = n
    if ref == "U1": pins["9"] = "QH_CASCATA"
    if V == "tht":
        fp = place("Package_DIP", "DIP-16_W7.62mm", ref, "74HC595", x, y, 0, pins)
        fp.Reference().SetPosition(pcbnew.VECTOR2I(MM(x + 3.81), MM(y + 8.89))); fp.Reference().SetTextAngleDegrees(90)
        return fp
    fp = place("Package_SO", "SOIC-16_3.9x9.9mm_P1.27mm", ref, "74HC595D", x, y, 0, pins)
    fp.Reference().SetPosition(pcbnew.VECTOR2I(MM(x), MM(y))); fp.Reference().SetTextAngleDegrees(90)  # sigla dentro il chip
    return fp

QA = [f"Q{i}" for i in range(1, 11)]
if V == "tht":
    hc595("U1", 25.7, 6.3, "IO13_DS", QA[:8])
    hc595("U2", 36.7, 6.3, "QH_CASCATA", QA[8:] + [None] * 6)
else:
    hc595("U1", 30.0, 14.0, "IO13_DS", QA[:8])
    hc595("U2", 41.0, 14.0, "QH_CASCATA", QA[8:] + [None] * 6)

# ---------------------------------------------------------------- resistenze 220 ohm e condensatori
for i in range(10):
    ref, pins = f"R{i + 1}", {"1": QA[i], "2": f"LED{i + 1}"}
    if V == "tht":
        x = 25.8 + (i % 5) * 4.4; y = 27.8 + (i // 5) * 10.0
        place("Resistor_THT", "R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal", ref, "220", x, y, -90, pins)
    else:
        x = 27.5 + (i % 5) * 3.6; y = 30.0 + (i // 5) * 5.0
        place("Resistor_SMD", "R_0805_2012Metric", ref, "220", x, y, 90, pins)

if V == "tht":
    c = place("Capacitor_THT", "C_Disc_D3.0mm_W1.6mm_P2.50mm", "C1", "100nF", 28.0, 3.4, 0, {"1": "+3V3", "2": "GND"})
    c.Reference().SetPosition(pcbnew.VECTOR2I(MM(26.0), MM(3.4)))
    c = place("Capacitor_THT", "C_Disc_D3.0mm_W1.6mm_P2.50mm", "C2", "100nF", 39.9, 3.4, 0, {"1": "+3V3", "2": "GND"})
    c.Reference().SetPosition(pcbnew.VECTOR2I(MM(44.4), MM(3.4)))
    place("Capacitor_THT", "C_Disc_D5.0mm_W2.5mm_P5.00mm", "C3", "10uF 5V", 10.5, 40.0, 0, {"1": "+5V", "2": "GND"})
    place("Capacitor_THT", "C_Disc_D5.0mm_W2.5mm_P5.00mm", "C4", "10uF 3V3", 58.5, 41.0, 0, {"1": "+3V3", "2": "GND"})
else:
    place("Capacitor_SMD", "C_0805_2012Metric", "C1", "100nF", 30.0, 7.0, 0, {"1": "+3V3", "2": "GND"})
    place("Capacitor_SMD", "C_0805_2012Metric", "C2", "100nF", 41.0, 7.0, 0, {"1": "+3V3", "2": "GND"})
    place("Capacitor_SMD", "C_0805_2012Metric", "C3", "10uF", 12.0, 40.0, 0, {"1": "+5V", "2": "GND"})
    place("Capacitor_SMD", "C_0805_2012Metric", "C4", "10uF", 60.0, 41.0, 0, {"1": "+3V3", "2": "GND"})

# ---------------------------------------------------------------- fori di fissaggio (NPTH)
for i, (x, y) in enumerate([(HOLE_C, HOLE_C), (W - HOLE_C, HOLE_C), (HOLE_C, H - HOLE_C), (W - HOLE_C, H - HOLE_C)]):
    fp = pcbnew.FOOTPRINT(b); fp.SetReference(f"H{i + 1}"); fp.SetValue("M1.4")
    fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
    pad = pcbnew.PAD(fp); pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH); pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
    pad.SetSize(pcbnew.VECTOR2I(MM(HOLE_D), MM(HOLE_D))); pad.SetDrillSize(pcbnew.VECTOR2I(MM(HOLE_D), MM(HOLE_D)))
    pad.SetLayerSet(pcbnew.LSET.AllCuMask()); fp.Add(pad)
    fp.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y))); b.Add(fp)

# ---------------------------------------------------------------- bordo, regole, scritte
def seg(x0, y0, x1, y1, layer=pcbnew.Edge_Cuts, w=0.1):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(layer); s.SetWidth(MM(w))
    s.SetStart(pcbnew.VECTOR2I(MM(x0), MM(y0))); s.SetEnd(pcbnew.VECTOR2I(MM(x1), MM(y1))); b.Add(s)
for a, c in [((0, 0), (W, 0)), ((W, 0), (W, H)), ((W, H), (0, H)), ((0, H), (0, 0))]: seg(*a, *c)

def txt(s, x, y, size=1.0, layer=pcbnew.F_SilkS):
    t = pcbnew.PCB_TEXT(b); t.SetText(s); t.SetLayer(layer)
    t.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y))); t.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size)))
    t.SetTextThickness(MM(max(0.15, size * 0.15))); b.Add(t)  # JLCPCB: tratto min 0,15
txt("PLANCIA v1 " + V.upper(), 60.5, 45.4, 0.8)
for t, x, y, sz in ETICHETTE: txt(t, x, y, sz)
# sagoma dell'ESP (tra le due file di pin) e verso di montaggio
ex0, ex1 = ESP_X0 - 1.7, ESP_X0 + ESP_DX + 1.7
for a, c in [((ex0, 0.6), (ex1, 0.6)), ((ex1, 0.6), (ex1, H - 0.6)), ((ex0, H - 0.6), (ex0, 0.6))]:  # sotto aperto: l'ESP sporge
    seg(*a, *c, layer=pcbnew.F_SilkS, w=0.15)
txt("^ USB ESP32 da questo lato ^", 35, 1.45, 0.8)
fine = ESP_Y0 + 14 * 2.54
txt("3V3", ESP_X0 - 2.9, ESP_Y0, 0.8); txt("D23", ESP_X0 - 2.9, fine, 0.8)
txt("VIN", ESP_X0 + ESP_DX + 2.9, ESP_Y0, 0.8); txt("EN", ESP_X0 + ESP_DX + 2.6, fine, 0.8)

def regole(bb):
    """Regole di progetto (finiscono nel .kicad_pro, quindi vanno rimesse dopo ogni LoadBoard)."""
    ds = bb.GetDesignSettings()
    nc = ds.m_NetSettings.GetDefaultNetclass()
    nc.SetClearance(MM(0.2)); nc.SetTrackWidth(MM(0.3)); nc.SetViaDiameter(MM(0.7)); nc.SetViaDrill(MM(0.35))
    pw = pcbnew.NETCLASS("Power"); pw.SetClearance(MM(0.25)); pw.SetTrackWidth(MM(0.6))
    pw.SetViaDiameter(MM(0.9)); pw.SetViaDrill(MM(0.45))
    ds.m_NetSettings.SetNetclass("Power", pw)
    for n in ["+5V", "+3V3", "GND"]:
        ds.m_NetSettings.SetNetclassPatternAssignment(n, "Power")
    ds.m_TrackMinWidth = MM(0.2); ds.m_MinClearance = MM(0.2); ds.m_HoleClearance = MM(0.25); ds.m_CopperEdgeClearance = MM(0.3)  # JLCPCB: min 0.3
    ds.m_TrackMinWidth = MM(0.15)  # Freerouting stringe a 0,18 vicino ai pad; JLCPCB accetta 0,127
regole(b)

def salva(bb, pcb):
    """Salva scheda + .kicad_pro con le regole. Se KiCad ha il progetto aperto lo blocca,
    quindi il .kicad_pro si scrive in una cartella temporanea e poi si copia accanto."""
    import tempfile, shutil
    pcbnew.SaveBoard(pcb, bb)
    tmp = tempfile.mkdtemp(); t = os.path.join(tmp, "x.kicad_pcb"); shutil.copy(pcb, t)
    tb = pcbnew.LoadBoard(t); regole(tb); pcbnew.SaveBoard(t, tb)
    pcbnew.GetSettingsManager().SaveProjectAs(os.path.join(tmp, "x.kicad_pro"))
    shutil.copy(os.path.join(tmp, "x.kicad_pro"), pcb[:-len(".kicad_pcb")] + ".kicad_pro")

# piano di massa sotto (e sopra dopo lo sbroglio), niente rame sotto l'antenna dell'ESP
def zone(layer, pts, netname=None, keepout=False):
    z = pcbnew.ZONE(b); z.SetLayer(layer)
    if keepout:
        z.SetIsRuleArea(True); z.SetDoNotAllowZoneFills(True); z.SetDoNotAllowTracks(False); z.SetDoNotAllowVias(False); z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
        z.SetLayerSet(pcbnew.LSET.AllCuMask())
    else:
        z.SetNet(net(netname)); z.SetMinThickness(MM(0.25)); z.SetLocalClearance(MM(0.3))
        z.SetThermalReliefGap(MM(0.5)); z.SetThermalReliefSpokeWidth(MM(0.5))
    ol = z.Outline(); ol.NewOutline()
    for x, y in pts: ol.Append(MM(x), MM(y))
    b.Add(z); return z
ANT = [(ESP_X0 - 1, 42.0), (ESP_X0 + ESP_DX + 1, 42.0), (ESP_X0 + ESP_DX + 1, H), (ESP_X0 - 1, H)]
zone(pcbnew.F_Cu, ANT, keepout=True)

base = os.path.join(OUT, f"plancia_{V}")
if SES:
    b2 = pcbnew.LoadBoard(base + "_pre.kicad_pcb"); regole(b2)
    # i fori di fissaggio non hanno nome libreria: Freerouting scrive "(component " vuoto e KiCad non lo legge
    s = open(base + ".ses").read().replace("(component \n", '(component "MH"\n')
    open(base + "_fix.ses", "w").write(s)
    if not pcbnew.ImportSpecctraSES(b2, base + "_fix.ses"): raise SystemExit("import .ses fallito")
    for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(b2); z.SetLayer(lay); z.SetNet(b2.FindNet("GND")); z.SetMinThickness(MM(0.25))
        z.SetLocalClearance(MM(0.3)); z.SetThermalReliefGap(MM(0.5)); z.SetThermalReliefSpokeWidth(MM(0.5))
        ol = z.Outline(); ol.NewOutline()
        for x, y in [(0.6, 0.6), (W - 0.6, 0.6), (W - 0.6, H - 0.6), (0.6, H - 0.6)]: ol.Append(MM(x), MM(y))
        b2.Add(z)
    pcbnew.ZONE_FILLER(b2).Fill(b2.Zones())
    salva(b2, base + ".kicad_pcb")
    print("salvato", base + ".kicad_pcb")
else:
    pcbnew.SaveBoard(base + "_pre.kicad_pcb", b)
    b = pcbnew.LoadBoard(base + "_pre.kicad_pcb"); regole(b)
    salva(b, base + "_pre.kicad_pcb")
    ok = pcbnew.ExportSpecctraDSN(b, base + ".dsn")
    print("dsn", ok, base + ".dsn")
    # per lo sbroglio le piste possono passare sotto l'antenna (l'ESP sta ~1 cm sopra sui pin femmina);
    # resta vietato solo il piano di massa lì. Tolgo l'area vietata del bordo dal .dsn.
    import re
    t = open(base + ".dsn").read()
    t = re.sub(r'\n\s*\(keepout "" \(polygon [FB]\.Cu 0[^)]*\)\)', "", t)
    # contorno ristretto di 0,15 mm: Freerouting non conosce il margine dal bordo di KiCad
    e, w, h = 150, int(W * 1000), int(H * 1000)
    t = t.replace(f"(path pcb 0  {w} -{h}  0 -{h}  0 0  {w} 0  {w} -{h})",
                  f"(path pcb 0  {w-e} -{h-e}  {e} -{h-e}  {e} -{e}  {w-e} -{e}  {w-e} -{h-e})")
    open(base + ".dsn", "w").write(t)
    for fp in b.GetFootprints():
        if fp.GetReference().startswith(("J", "U")):
            p1 = [p for p in fp.Pads() if p.GetNumber() == "1"]
            if p1:
                pp = p1[0].GetPosition(); print(fp.GetReference(), "pin1", round(pcbnew.ToMM(pp.x), 2), round(pcbnew.ToMM(pp.y), 2),
                      "bbox", [round(pcbnew.ToMM(v), 1) for v in (fp.GetBoundingBox().GetLeft(), fp.GetBoundingBox().GetTop(), fp.GetBoundingBox().GetRight(), fp.GetBoundingBox().GetBottom())])
