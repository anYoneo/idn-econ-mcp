#!/usr/bin/env python3
"""Uji idn-econ-mcp: panggilan tool langsung + handshake stdio MCP."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

hasil = []


def ok(nama, syarat, info=""):
    hasil.append((nama, bool(syarat), info))
    print(("LULUS " if syarat else "GAGAL ") + nama + ("  " + str(info)[:120] if info else ""))


print("=== 1. Panggilan tool langsung (data nyata) ===")
import server as S  # noqa: E402

for fn, nama in [
    (S.cek_server, "cek_server"),
    (S.daftar_indikator, "daftar_indikator"),
]:
    try:
        r = fn()
        ok(f"{nama}()", isinstance(r, dict) and r, str(r)[:100])
    except Exception as e:
        ok(f"{nama}()", False, f"error: {e}")

try:
    r = S.cari_series("inflasi")
    ok("cari_series('inflasi')", r.get("jumlah", 0) > 0, f"{r.get('jumlah')} hasil")
except Exception as e:
    ok("cari_series('inflasi')", False, f"error: {e}")

try:
    r = S.ambil_series("wb:idn:FP.CPI.TOTL.ZG", mulai="2020")
    ok("ambil_series(CPI.ZG, 2020+)", r.get("jumlah_titik", 0) > 0,
       f"{r.get('jumlah_titik')} titik, satuan={r.get('satuan')}")
    if r.get("titik"):
        print("     contoh:", json.dumps(r["titik"][0]))
except Exception as e:
    ok("ambil_series", False, f"error: {e}")

try:
    r = S.ambil_series("wb:idn:TIDAK.ADA")
    ok("ambil_series(id salah) -> error ramah", "error" in r and "mirip" in r)
except Exception as e:
    ok("ambil_series(id salah)", False, f"error: {e}")

try:
    r = S.kurs_terkini("USD", "IDR")
    ok("kurs_terkini(USD/IDR)", r.get("terbaru", {}).get("nilai") is not None,
       f"{r.get('terbaru')}")
except Exception as e:
    ok("kurs_terkini", False, f"error: {e}")

try:
    r = S.banding_asean("inflasi", mulai="2020")
    ada = sum(1 for v in r.get("terbaru_per_negara", {}).values() if v)
    ok("banding_asean('inflasi')", ada >= 5, f"{ada} negara ada data")
except Exception as e:
    ok("banding_asean", False, f"error: {e}")

print()
print("=== 2. Handshake stdio MCP (protokol nyata) ===")
proc = subprocess.Popen(
    [sys.executable, str(ROOT / "src" / "server.py")],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    encoding="utf-8", bufsize=1,
)


def kirim(obj):
    proc.stdin.write(json.dumps(obj) + "\n")
    proc.stdin.flush()


def baca():
    baris = proc.stdout.readline()
    return json.loads(baris) if baris.strip() else None


try:
    kirim({"jsonrpc": "2.0", "id": 1, "method": "initialize",
           "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                      "clientInfo": {"name": "uji-lokal", "version": "1.0"}}})
    init = baca()
    ok("initialize", init and "result" in init,
       (init or {}).get("result", {}).get("serverInfo"))

    kirim({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

    kirim({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    tl = baca()
    tools = (tl or {}).get("result", {}).get("tools", [])
    ok("tools/list", len(tools) >= 6, f"{len(tools)} tool: {[t['name'] for t in tools]}")

    kirim({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
           "params": {"name": "kurs_terkini", "arguments": {"base": "USD", "quote": "IDR"}}})
    call = baca()
    isi = (call or {}).get("result", {})
    teks = ""
    if isi.get("content"):
        teks = isi["content"][0].get("text", "")
    ok("tools/call kurs_terkini", "USD" in teks or "nilai" in teks, teks[:150])
except Exception as e:
    ok("handshake stdio", False, f"error: {e}")
finally:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
    err = proc.stderr.read()
    if err.strip():
        print("--- stderr server (10 baris) ---")
        print("\n".join(err.strip().splitlines()[:10]))

print()
lulus = sum(1 for _, s, _ in hasil if s)
print(f"RINGKASAN: {lulus}/{len(hasil)} lulus")
sys.exit(0 if lulus == len(hasil) else 1)
