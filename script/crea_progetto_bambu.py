"""
Crea un progetto Bambu Studio (.3mf) per il CASA Rack 10":
  - 9 piatti con i pezzi gia' disposti e pronti da stampare
  - 1 piatto con il rack montato (solo da guardare)
Uso: python crea_progetto_bambu.py   (dalla cartella rack, con gli STL in ./stl)
"""
import math, os, re, struct, zipfile, uuid

BED = 256.0           # Bambu Lab A1
GAP = 8.0
STL = "stl"
OUT = "mini_rack_10_proxmox.3mf"

# misure dal file rack10.scad
U, PW, D, post, ring_h, base_h, NU, side_t = 44.45, 254.0, 220.0, 18.0, 16.0, 51.0, 4, 3.0
H = base_h + NU * U
EAR = post / 2
handle_y = [45.0, D - 45.0]
z0 = ring_h
pe = 12.0                 # blocco pieno alle estremita' dei montanti
zr = z0 + pe              # inizio zona a U

# ---------------------------------------------------------------- matrici 4x4
def mat_mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]
def T(x, y, z): return [[1, 0, 0, x], [0, 1, 0, y], [0, 0, 1, z], [0, 0, 0, 1]]
def Rx(d):
    c, s = math.cos(math.radians(d)), math.sin(math.radians(d))
    return [[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1]]
def Ry(d):
    c, s = math.cos(math.radians(d)), math.sin(math.radians(d))
    return [[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]]
def Rz(d):
    c, s = math.cos(math.radians(d)), math.sin(math.radians(d))
    return [[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
def M(x, y, z): return [[x, 0, 0, 0], [0, y, 0, 0], [0, 0, z, 0], [0, 0, 0, 1]]
def chain(*ms):
    r = T(0, 0, 0)
    for m in ms: r = mat_mul(r, m)
    return r
I = T(0, 0, 0)

# ---------------------------------------------------------------- STL
def read_stl(path):
    data = open(path, "rb").read()
    tris = []
    if data[:5] == b"solid" and b"facet" in data[:400]:
        v = [tuple(map(float, m.groups())) for m in re.finditer(rb"vertex\s+(\S+)\s+(\S+)\s+(\S+)", data)]
        tris = [v[i:i + 3] for i in range(0, len(v), 3)]
    else:
        n = struct.unpack("<I", data[80:84])[0]
        for i in range(n):
            f = struct.unpack("<12f", data[84 + i * 50: 84 + i * 50 + 48])
            tris.append([f[3:6], f[6:9], f[9:12]])
    verts, idx, faces = [], {}, []
    for t in tris:
        f = []
        for p in t:
            k = (round(p[0], 4), round(p[1], 4), round(p[2], 4))
            if k not in idx: idx[k] = len(verts); verts.append(k)
            f.append(idx[k])
        if len(set(f)) == 3: faces.append(f)
    mn = [min(v[i] for v in verts) for i in range(3)]
    mx = [max(v[i] for v in verts) for i in range(3)]
    return {"verts": verts, "faces": faces, "min": mn, "size": [mx[i] - mn[i] for i in range(3)]}

# ---------------------------------------------------------------- pezzi
# file, nome, quante copie, funzione che restituisce la trasformazione "in assemblaggio"
# (dalle coordinate di stampa originali, come esportate da OpenSCAD)
corners = [(0, 0), (PW - post, 0), (0, D - post), (PW - post, D - post)]
inv_post = Rx(90)                                   # stampa: rotate([-90,0,0])
inv_ring_top = chain(Rx(180), T(0, -D, -ring_h))    # stampa: translate([0,D,ring_h]) rotate([180,0,0])
inv_handle = Ry(-90)                                 # stampa: rotate([0,90,0])
side_right = lambda z: chain(T(PW, 0, z), Rz(90), Rx(90))
side_left_from_sx = lambda z: chain(T(-side_t, 0, z), Rz(90), Rx(90), T(0, 0, side_t), M(1, 1, -1), M(-1, 1, 1))

parts = [
    ("01_montante__x4", "Montante", [chain(T(cx, cy, z0), inv_post) for cx, cy in corners]),
    ("09_maniglia__x2", "Maniglia", [chain(T(x, handle_y[0], z0 + H + 2 * pe + ring_h), inv_handle) for x in (EAR, PW - EAR)]),
    ("10_piedino__x4", "Piedino", [T(x, y, -8) for x in (EAR, PW - EAR) for y in handle_y]),
    ("03_cornice_sotto", "Cornice sotto", [I]),
    ("04_cornice_sopra", "Cornice sopra", [chain(T(0, 0, z0 + H + 2 * pe), inv_ring_top)]),
    ("05_pannello_laterale_destro", "Pannello laterale destro", [side_right(z0 + 3)]),
    ("06_pannello_laterale_sinistro", "Pannello laterale sinistro", [side_left_from_sx(z0 + 3)]),
    ("11_ripiano_HP__x2", "Ripiano HP (pve2/pve3)", [T(0, 0, zr + base_h + U), T(0, 0, zr + base_h)]),
    ("12_ripiano_pve1_teclast", "Ripiano pve1 (Teclast N30, base 51 mm)", [T(0, 0, zr)]),
    ("13_ripiano_plancia_switch_esp", "Ripiano plancia (switch + ESP32)", [T(0, 0, zr + base_h + 2 * U)]),
    ("14_frontale_pve1", "Frontale pve1 (Teclast)", [chain(T(0, 0, zr), Rx(-90))]),
    ("15_frontale_pve2", "Frontale pve2", [chain(T(0, 0, zr + base_h), Rx(-90))]),
    ("16_frontale_pve3", "Frontale pve3 (HP 800 G5)", [chain(T(0, 0, zr + base_h + U), Rx(-90))]),
    ("17_plancia_inclinata", "Plancia inclinata", [T(0, 0, zr + base_h + 2 * U)]),
    ("18_barra_fermo_switch", "Barra fermo switch", [T(127 - 79.5 - 6, 98 + 50.5, zr + base_h + 2 * U + 0.4 + 28.5)]),
]
plates = [
    ("Cornice sopra", ["04_cornice_sopra"]),
    ("Cornice sotto", ["03_cornice_sotto"]),
    ("Pannello laterale destro", ["05_pannello_laterale_destro"]),
    ("Pannello laterale sinistro", ["06_pannello_laterale_sinistro"]),
    ("Ripiano pve3", [("11_ripiano_HP__x2", 0)]),
    ("Ripiano pve2", [("11_ripiano_HP__x2", 1)]),
    ("Ripiano pve1 Teclast (base)", ["12_ripiano_pve1_teclast"]),
    ("Ripiano plancia (switch + ESP32)", ["13_ripiano_plancia_switch_esp"]),
    ("Frontali pve1, pve2, pve3", ["14_frontale_pve1", "15_frontale_pve2", "16_frontale_pve3"]),
    ("Plancia inclinata (in piedi)", ["17_plancia_inclinata"]),
    ("Montanti interi (in diagonale)", ["01_montante__x4"]),
    ("Maniglie, piedini e barra switch", ["09_maniglia__x2", "10_piedino__x4", "18_barra_fermo_switch"]),
]
VIEW_PLATE = "RACK MONTATO (solo da guardare)"

# ---------------------------------------------------------------- disposizione sui piatti (stile Bambu)
n_plates = len(plates) + 1
v = math.sqrt(n_plates); cols = int(round(v)) + (1 if v > round(v) else 0)
stride = BED * 1.2
def plate_origin(i): return ((i % cols) * stride, -(i // cols) * stride)

meshes = {f: read_stl(os.path.join(STL, f + ".stl")) for f, _, _ in parts}
objects = []   # (nome, file, matrice, piatto)

for pi, (pname, files) in enumerate(plates):
    ox, oy = plate_origin(pi)
    items = []
    for f in files:   # un file intero, oppure (file, copia) per una sola copia
        if isinstance(f, tuple): items.append(f)
        else: items += [(f, k) for k in range(len(next(p for p in parts if p[0] == f)[2]))]
    # ripiani: righe da sinistra a destra, centrate se un solo pezzo
    x = y = GAP; row_h = 0
    placed = []
    for f, k in items:
        sx, sy, _ = meshes[f]["size"]
        if x + sx > BED - GAP and x > GAP: x = GAP; y += row_h + GAP; row_h = 0
        placed.append((f, k, x, y)); x += sx + GAP; row_h = max(row_h, sy)
    if pname.startswith("Montanti"):   # 4 montanti interi (252.8 mm) paralleli in diagonale, ruotati di 45 gradi
        placed = [("01_montante__x4", k, BED / 2 + t * 0.70710678, BED / 2 - t * 0.70710678, "diag") for k, t in enumerate((-39, -13, 13, 39))]
    if pname.startswith("Frontali"):   # pezzi larghi 254 mm: centrati, uno sotto l'altro
        y = GAP; placed = []
        for f, k in items:
            sx, sy, _ = meshes[f]["size"]
            placed.append((f, k, (BED - sx) / 2, y)); y += sy + GAP
    if len(items) == 1 and not pname.startswith("Montanti"):
        f, k = placed[0][0], placed[0][1]
        sx, sy, _ = meshes[f]["size"]
        placed = [(f, k, (BED - sx) / 2, (BED - sy) / 2)]
    for it in placed:
        f, k, px, py = it[:4]; rot = it[4] if len(it) > 4 else 0
        mn = meshes[f]["min"]; sy0 = meshes[f]["size"][1]
        if rot == "diag":   # (px, py) = centro del pezzo sul piatto
            c = [mn[i] + meshes[f]["size"][i] / 2 for i in range(2)]
            mtx = chain(T(ox + px, oy + py, -mn[2]), Rz(-45), T(-c[0], -c[1], 0))
        elif rot: mtx = chain(T(ox + px + sy0, oy + py, -mn[2]), Rz(90), T(-mn[0], -mn[1], 0))
        else:   mtx = T(ox + px - mn[0], oy + py - mn[1], -mn[2])
        nm = next(p[1] for p in parts if p[0] == f) + (f" {k + 1}" if len(next(p for p in parts if p[0] == f)[2]) > 1 else "")
        objects.append((nm, f, mtx, pi + 1))

# piatto finale: rack montato
ox, oy = plate_origin(len(plates))
cx, cy = (BED - PW) / 2, (BED - D) / 2
for f, nm, inst in parts:
    for k, a in enumerate(inst):
        objects.append(("Rack - " + nm + (f" {k + 1}" if len(inst) > 1 else ""), f, chain(T(ox + cx, oy + cy, 8), a), n_plates))

# ---------------------------------------------------------------- scrittura 3MF
def fmt(m):   # trasformazione 3MF: 12 numeri, colonne della 3x3 + traslazione
    return " ".join(f"{m[r][c]:.6f}" for c in range(3) for r in range(3)) + " " + " ".join(f"{m[r][3]:.6f}" for r in range(3))

mesh_xml = {}
for f, m in meshes.items():
    vs = "".join(f'<vertex x="{x}" y="{y}" z="{z}"/>' for x, y, z in m["verts"])
    ts = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in m["faces"])
    mesh_xml[f] = f"<mesh><vertices>{vs}</vertices><triangles>{ts}</triangles></mesh>"

res, build, cfg_obj = [], [], []
for i, (nm, f, mtx, pl) in enumerate(objects, start=1):
    res.append(f'<object id="{i}" name="{nm}" type="model" p:UUID="{uuid.uuid4()}">{mesh_xml[f]}</object>')
    build.append(f'<item objectid="{i}" transform="{fmt(mtx)}" printable="1" p:UUID="{uuid.uuid4()}"/>')
    cfg_obj.append(f'  <object id="{i}">\n    <metadata key="name" value="{nm}"/>\n    <metadata key="extruder" value="1"/>\n  </object>')

model = ('<?xml version="1.0" encoding="UTF-8"?>\n'
         '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
         'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
         'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">\n'
         '<metadata name="Application">BambuStudio-01.10.00.00</metadata>\n'
         '<metadata name="BambuStudio:3mfVersion">1</metadata>\n'
         '<metadata name="Title">CASA Rack 10 pollici</metadata>\n'
         f'<resources>{"".join(res)}</resources>\n<build>{"".join(build)}</build>\n</model>')

plate_xml = []
for pi in range(n_plates):
    name = plates[pi][0] if pi < len(plates) else VIEW_PLATE
    inst = "".join(f'\n    <model_instance>\n      <metadata key="object_id" value="{i}"/>\n      <metadata key="instance_id" value="0"/>\n      <metadata key="identify_id" value="{1000 + i}"/>\n    </model_instance>'
                   for i, o in enumerate(objects, start=1) if o[3] == pi + 1)
    plate_xml.append(f'  <plate>\n    <metadata key="plater_id" value="{pi + 1}"/>\n    <metadata key="plater_name" value="{name}"/>\n    <metadata key="locked" value="false"/>{inst}\n  </plate>')
config = '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n' + "\n".join(cfg_obj) + "\n" + "\n".join(plate_xml) + "\n</config>\n"

ctypes = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
          '<Default Extension="config" ContentType="text/xml"/></Types>')
rels = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("[Content_Types].xml", ctypes)
    z.writestr("_rels/.rels", rels)
    z.writestr("3D/3dmodel.model", model)
    z.writestr("Metadata/model_settings.config", config)

print(f"{OUT}: {len(objects)} oggetti su {n_plates} piatti, {os.path.getsize(OUT) / 1e6:.1f} MB")
for pi in range(n_plates):
    name = plates[pi][0] if pi < len(plates) else VIEW_PLATE
    objs = [o for o in objects if o[3] == pi + 1]
    print(f"  piatto {pi + 1}: {name} ({len(objs)} pezzi)")
# controllo ingombri sui piatti di stampa
bad = False
for pi, (pname, files) in enumerate(plates):
    ox, oy = plate_origin(pi)
    for nm, f, mtx, pl in objects:
        if pl != pi + 1: continue
        mn = meshes[f]["min"]; sz3 = meshes[f]["size"]
        pts = [[mn[0] + a * sz3[0], mn[1] + b * sz3[1], mn[2] + c * sz3[2], 1] for a in (0, 1) for b in (0, 1) for c in (0, 1)]
        tp = [[sum(mtx[r][i] * q[i] for i in range(4)) for r in range(3)] for q in pts]
        x0, x1 = min(t[0] for t in tp) - ox, max(t[0] for t in tp) - ox
        y0, y1 = min(t[1] for t in tp) - oy, max(t[1] for t in tp) - oy
        z0_, z1_ = min(t[2] for t in tp), max(t[2] for t in tp)
        if x0 < -0.01 or y0 < -0.01 or x1 > BED + 0.01 or y1 > BED + 0.01 or z0_ < -0.01 or z1_ > BED:
            print(f"  ATTENZIONE: {nm} esce dal piatto {pi + 1}"); bad = True

print("CONTROLLO PIATTI:", "qualche pezzo esce" if bad else "tutti i pezzi dentro il piatto 256 x 256")
