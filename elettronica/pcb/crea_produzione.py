"""Prepara i file per JLCPCB partendo dai file esportati con kicad-cli in produzione/<v>/.

- produzione/<v>/gerber_<v>.zip : da caricare su jlcpcb.com (PCB)
- produzione/smd/BOM_JLC.csv e CPL_JLC.csv : per il montaggio SMD di JLCPCB
- produzione/<v>/da_saldare_a_mano.csv : pezzi da saldare a mano

Codici LCSC controllati su lcsc.com il 14/11/2026: C5947 Nexperia 74HC595D (SOIC-16), C17557 220 ohm 1% 0805,
C49678 100nF 50V X7R 0805, C15850 10uF 25V X5R 0805.
"""
import csv, os, zipfile

QUI = os.path.dirname(os.path.abspath(__file__))
LCSC = {  # (valore, impronta) -> codice LCSC
    ("74HC595D", "SOIC-16_3.9x9.9mm_P1.27mm"): "C5947",
    ("220", "R_0805_2012Metric"): "C17557",
    ("100nF", "C_0805_2012Metric"): "C49678",
    ("10uF", "C_0805_2012Metric"): "C15850",
}
A_MANO = {  # cosa si salda a mano in tutte e due le versioni
    "J1": "Pin femmina 1x15 passo 2,54 (ESP sinistra)",
    "J2": "Pin femmina 1x15 passo 2,54 (ESP destra)",
    "J3": "JST-XH 8 pin verticale (TFT)",
    "J4": "JST-XH 4 pin verticale (OLED pve1)",
    "J5": "JST-XH 4 pin verticale (OLED pve2)",
    "J6": "JST-XH 4 pin verticale (OLED pve3)",
    "J7": "JST-XH 11 pin verticale (barra LED)",
    "J8": "JST-XH 5 pin verticale (joystick)",
    "J9": "JST-XH 3 pin verticale (PIR)",
}

for v in ("tht", "smd"):
    d = os.path.join(QUI, "produzione", v)
    g = os.path.join(d, "gerber")
    with zipfile.ZipFile(os.path.join(d, f"gerber_{v}.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(g)):
            if not f.endswith(".gbrjob"): z.write(os.path.join(g, f), f)
    rows = [r for r in csv.DictReader(open(os.path.join(d, "posizioni.csv"), encoding="utf-8")) if not r["Ref"].startswith("H")]  # H = fori
    mano = [(r["Ref"], A_MANO.get(r["Ref"], f'{r["Val"]} ({r["Package"]})')) for r in rows
            if v == "tht" or r["Ref"].startswith("J")]
    with open(os.path.join(d, "da_saldare_a_mano.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["Sigla", "Pezzo"]); w.writerows(mano)
    if v == "smd":
        smd = [r for r in rows if not r["Ref"].startswith("J")]
        with open(os.path.join(d, "CPL_JLC.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
            for r in smd:
                w.writerow([r["Ref"], f'{float(r["PosX"]):.3f}mm', f'{float(r["PosY"]):.3f}mm', "Top", f'{float(r["Rot"]):.0f}'])
        gruppi = {}
        for r in smd: gruppi.setdefault((r["Val"], r["Package"]), []).append(r["Ref"])
        with open(os.path.join(d, "BOM_JLC.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
            for (val, pk), refs in gruppi.items():
                w.writerow([val, ",".join(refs), pk, LCSC.get((val, pk), "??")])
    print(v, "ok:", len(rows), "componenti,", len(mano), "a mano")
