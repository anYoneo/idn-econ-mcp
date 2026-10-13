#!/usr/bin/env python3
"""Uji image Docker lewat protokol MCP nyata (dengan jeda agar tiap permintaan terproses)."""
import json
import subprocess
import sys
import time

IMAGE = sys.argv[1] if len(sys.argv) > 1 else "idn-econ-mcp:1.1.0"

p = subprocess.Popen(
    ["docker", "run", "--rm", "-i", IMAGE],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    text=True, encoding="utf-8", bufsize=1,
)


def kirim(obj):
    p.stdin.write(json.dumps(obj) + "\n")
    p.stdin.flush()


def baca(n=1, timeout=25):
    out = []
    akhir = time.time() + timeout
    while len(out) < n and time.time() < akhir:
        ln = p.stdout.readline()
        if not ln:
            break
        ln = ln.strip()
        if ln.startswith("{"):
            out.append(json.loads(ln))
    return out


kirim({"jsonrpc": "2.0", "id": 1, "method": "initialize",
       "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                  "clientInfo": {"name": "uji", "version": "1"}}})
r = baca(1)
info = r[0]["result"]["serverInfo"]
print(f"initialize -> {info['name']} v{info['version']}")

kirim({"jsonrpc": "2.0", "method": "notifications/initialized"})
time.sleep(0.3)

kirim({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
r = baca(1)
nama = [t["name"] for t in r[0]["result"]["tools"]]
print(f"tools/list -> {len(nama)} tool: {nama}")

for id_, tool, args in [
    (3, "cek_server", {}),
    (4, "banding_asean", {"indikator": "pertumbuhan"}),
    (5, "cari_series", {"q": "imf", "batas": 5}),
]:
    kirim({"jsonrpc": "2.0", "id": id_, "method": "tools/call",
           "params": {"name": tool, "arguments": args}})
    r = baca(1, timeout=20)
    if not r:
        print(f"tools/call {tool} -> TIDAK ADA BALASAN")
        continue
    j = json.loads(r[0]["result"]["content"][0]["text"])
    if tool == "cek_server":
        print(f"tools/call cek_server -> {j['jumlah_series']} seri | {j['jumlah_observasi']} obs "
              f"| {j['periode_awal']}-{j['periode_akhir']} | {j['sumber']}")
    elif tool == "banding_asean":
        print(f"tools/call banding_asean(pertumbuhan) -> sumber={j['sumber_data']} "
              f"Indonesia {j['terbaru_per_negara']['Indonesia']}")
    else:
        print(f"tools/call cari_series('imf') -> {j['jumlah']} hasil, mis. {j['hasil'][0]['series_id']}, "
              f"periode s.d. {j['hasil'][0]['akhir']}")

p.stdin.close()
p.terminate()
