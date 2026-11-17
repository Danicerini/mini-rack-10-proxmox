"""Crea le immagini del manuale (istruzioni/img/) da openscad/istruzioni.scad.
Uso: python script/crea_immagini_istruzioni.py [percorso openscad.exe]
Rende a 2x e riduce (bordi lisci), poi toglie lo sfondo e ritaglia."""
import os, sys, subprocess
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageChops

QUI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(QUI)
SCAD = os.path.join(BASE, "openscad", "istruzioni.scad")
OUT = os.path.join(BASE, "istruzioni", "img")
OPENSCAD = sys.argv[1] if len(sys.argv) > 1 else "openscad"
os.makedirs(OUT, exist_ok=True)

def cam(rx, rz): return f"0,0,0,{rx},0,{rz},500"
SCENE = [  # nome, definizioni, (rx, rz), lato in px
    ("copertina", ['scena="copertina"'], (66, 28), 1800),
    ("finito_sx", ['scena="copertina"'], (70, -32), 1400),
    ("passo01", ['step=1'], (122, 28), 1400),
    ("passo02", ['step=2'], (64, -32), 1400),
    ("passo02b", ['step=21'], (128, -32), 1100),
    ("passo03", ['step=3'], (68, 38), 1400),
    ("passo04", ['step=4'], (72, -58), 1400),
    ("passo05", ['step=5'], (68, 205), 1400),
    ("passo05b", ['step=51'], (80, 140), 1100),
    ("passo06", ['step=6'], (60, -32), 1400),
    ("passo07", ['step=7'], (60, -32), 1400),
    ("passo08", ['step=8'], (60, -32), 1400),
    ("passo09", ['step=9'], (56, -30), 1400),
    ("passo10", ['step=10'], (60, -32), 1400),
    ("passo11", ['step=11'], (60, -32), 1400),
    ("passo12", ['step=12'], (74, 205), 1400),
    ("passo12b", ['step=121'], (84, 8), 1100),
    ("passo13", ['step=13'], (78, 205), 1200),
    ("passo14", ['step=14'], (70, -36), 1400),
    ("passo15", ['step=15'], (72, -36), 1400),
]
for n, ang in [("01", (62, -32)), ("03", (55, -30)), ("04", (55, -30)), ("05", (40, 0)), ("06", (40, 0)), ("09", (60, -30)),
               ("10", (55, -30)), ("11", (55, -30)), ("12", (55, -30)), ("13", (55, -30)), ("14", (70, -20)), ("15", (70, -20)),
               ("16", (70, -20)), ("17", (72, -20)), ("18", (55, -30))]:
    SCENE.append((f"pezzo_{n}", ['scena="pezzo"', f'pezzo="{n}"'], ang, 700))

def pulisci(path):
    im = Image.open(path).convert("RGB")
    bg = im.getpixel((2, 2))
    diff = ImageChops.difference(im, Image.new("RGB", im.size, bg)).convert("L").point(lambda v: 255 if v > 6 else 0)
    box = diff.getbbox()
    if not box: return
    w, h = im.size
    pad = int(0.035 * max(box[2] - box[0], box[3] - box[1]))
    box = (max(0, box[0] - pad), max(0, box[1] - pad), min(w, box[2] + pad), min(h, box[3] + pad))
    white = Image.new("RGB", im.size, (255, 255, 255))
    im = Image.composite(im, white, diff).crop(box)
    im = im.resize((im.width // 2, im.height // 2), Image.LANCZOS)
    im.save(path, optimize=True)

def rendi(sc):
    nome, defs, (rx, rz), lato = sc
    out = os.path.join(OUT, nome + ".png")
    args = [OPENSCAD, "-o", out, f"--imgsize={lato * 2},{lato * 2}", "--viewall", "--autocenter",
            "--colorscheme=Tomorrow", f"--camera={cam(rx, rz)}"]
    for d in defs: args += ["-D", d]
    args.append(SCAD)
    r = subprocess.run(args, capture_output=True, text=True)
    err = [l for l in (r.stdout + r.stderr).splitlines() if "ERROR" in l or "WARNING" in l]
    if r.returncode or not os.path.exists(out): return f"{nome}: ERRORE {err[:3]}"
    pulisci(out)
    return f"{nome}: ok" + (f" ({len(err)} avvisi: {err[0]})" if err else "")

if __name__ == "__main__":
    solo = os.environ.get("SOLO")
    scene = [s for s in SCENE if not solo or s[0] in solo.split(",")]
    with ThreadPoolExecutor(6) as ex:
        for r in ex.map(rendi, scene): print(r)
