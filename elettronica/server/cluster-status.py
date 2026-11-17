#!/usr/bin/python3
# Stato del cluster Proxmox in JSON, sola lettura, per il display ESP32.
# - Lo pubblica in HTTP sulla porta 9101 (http://IP-DEL-NODO:9101/status.json).
# - Lo manda sulla seriale USB all'ESP32 (una riga JSON ogni 5 s).
# Va eseguito come root su un nodo del cluster (quello a cui e' collegato l'ESP32 via USB).

import json, subprocess, threading, time, os, glob, termios, tty, select
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

# ===================== IMPOSTAZIONI: cambiale per il tuo cluster =====================
# Nome del nodo -> IP. Serve per leggere temperatura e velocita' di rete via SSH
# (usa le chiavi SSH che Proxmox gia' scambia tra i nodi del cluster).
IP = {"pve1": "192.168.1.10", "pve2": "192.168.1.11", "pve3": "192.168.1.12"}
PORTA_HTTP = 9101
# Facoltativo: nodo e cartella dove ci sono i backup dei database (cartelle con data, file *.sql.gz).
# Lascia BACKUP_NODO = None se non ti serve.
BACKUP_NODO = None
BACKUP_DIR = "/tank/db-backup"
# =====================================================================================

REMOTE = ("cat /sys/class/hwmon/hwmon*/temp1_input 2>/dev/null | sort -n | tail -1; "
          "for i in /sys/class/net/vmbr0/brif/*; do cat $i/../../$(basename $i)/speed 2>/dev/null; break; done; "
          "cat /sys/class/powercap/intel-rapl:0/constraint_0_power_limit_uw 2>/dev/null || echo 0")
BACKUP = ("d=$(ls -1d %s/20* 2>/dev/null | tail -1); "
          "[ -n \"$d\" ] && echo $(basename $d) $(ls $d/*.sql.gz 2>/dev/null | wc -l) $([ -e $d/ATTENZIONE-COPIA-INCOMPLETA ] && echo KO || echo OK)"
          % BACKUP_DIR)
data = {"ok": False}

def sh(cmd, t=8):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=t).stdout.strip()

def on_node(node, cmd):
    if node == os.uname().nodename:
        return sh(cmd)
    return sh("ssh -e none -o BatchMode=yes -o ConnectTimeout=3 -o HostKeyAlias=%s "
              "-o UserKnownHostsFile=/etc/pve/nodes/%s/ssh_known_hosts -o GlobalKnownHostsFile=none root@%s '%s'"
              % (node, node, IP.get(node, node), cmd.replace("'", "'\''")))

def collect():
    res = json.loads(sh("pvesh get /cluster/resources --output-format json", 15) or "[]")
    st = json.loads(sh("pvesh get /cluster/status --output-format json", 10) or "[]")
    q = sh("corosync-quorumtool -s")
    def qv(k):
        for l in q.splitlines():
            if l.strip().startswith(k):
                return l.split(":")[1].strip().split()[0]
        return "?"
    nodes = []
    for n in sorted([r for r in res if r.get("type") == "node"], key=lambda r: r["node"]):
        e = {"name": n["node"], "online": n.get("status") == "online",
             "cpu": round(100 * n.get("cpu", 0)), "cores": n.get("maxcpu", 0),
             "mem": round(n.get("mem", 0) / 2**30, 1), "memt": round(n.get("maxmem", 0) / 2**30, 1),
             "up": n.get("uptime", 0), "temp": None, "link": None, "plim": None}
        if e["online"]:
            try:
                t, l, p = (on_node(e["name"], REMOTE).splitlines() + ["", "", ""])[:3]
                e["temp"] = int(t) // 1000 if t.isdigit() else None
                e["link"] = int(l) if l.lstrip("-").isdigit() and int(l) > 0 else None
                e["plim"] = int(p) // 1000000 if p.isdigit() and 0 < int(p) // 1000000 < 60 else None
            except Exception:
                pass
        nodes.append(e)
    guests = sorted([{"id": r["vmid"], "name": r.get("name", ""), "type": "ct" if r["type"] == "lxc" else "vm",
                      "node": r.get("node"), "on": r.get("status") == "running",
                      "cpu": round(100 * r.get("cpu", 0)), "mem": round(r.get("mem", 0) / 2**30, 2)}
                     for r in res if r.get("type") in ("lxc", "qemu")], key=lambda g: g["id"])
    cl = next((s for s in st if s.get("type") == "cluster"), {})
    b = None
    if BACKUP_NODO:
        try:
            p = on_node(BACKUP_NODO, BACKUP).split()
            if len(p) == 3:
                b = {"when": p[0], "files": int(p[1]), "ok": p[2] == "OK"}
        except Exception:
            pass
    return {"ok": True, "ts": int(time.time()), "time": time.strftime("%H:%M"),
            "cluster": cl.get("name", "?"), "quorate": cl.get("quorate") == 1,
            "votes": qv("Total votes"), "expected": qv("Expected votes"),
            "nodes": nodes, "guests": guests,
            "on": sum(g["on"] for g in guests), "total": len(guests), "backup": b}

def loop():
    global data
    while True:
        try:
            data = collect()
        except Exception as ex:
            data = {"ok": False, "err": str(ex)[:80], "ts": int(time.time())}
        time.sleep(10)

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.split("?")[0] not in ("/", "/status.json"):
            self.send_response(404); self.end_headers(); return
        body = json.dumps(data, separators=(",", ":")).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *a):
        pass

# ---- ESP32 via USB (chip CH340): una riga JSON ogni 5 s ----
def serial_loop():
    while True:
        devs = sorted(glob.glob("/dev/serial/by-id/usb-1a86*")) or sorted(glob.glob("/dev/ttyUSB*"))
        if not devs:
            time.sleep(5)
            continue
        fd = None
        try:
            fd = os.open(devs[0], os.O_RDWR | os.O_NOCTTY)
            tty.setraw(fd)
            a = termios.tcgetattr(fd)
            a[4] = a[5] = termios.B115200
            a[2] = (a[2] & ~termios.HUPCL) | termios.CLOCAL | termios.CREAD   # non resettare l'ESP all'apertura
            termios.tcsetattr(fd, termios.TCSANOW, a)
            last = 0
            while True:
                if time.time() - last >= 5:
                    os.write(fd, (json.dumps(data, separators=(",", ":")) + "\n").encode())
                    last = time.time()
                r, _, _ = select.select([fd], [], [], 0.5)
                if r and not os.read(fd, 1024):
                    raise OSError("seriale chiusa")
        except Exception:
            pass
        finally:
            if fd is not None:
                try:
                    os.close(fd)
                except Exception:
                    pass
        time.sleep(3)

threading.Thread(target=loop, daemon=True).start()
threading.Thread(target=serial_loop, daemon=True).start()
ThreadingHTTPServer(("0.0.0.0", PORTA_HTTP), H).serve_forever()
