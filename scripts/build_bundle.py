#!/usr/bin/env python3
"""
Bangun idn-econ-mcp.mcpb secara manual.

Kenapa tidak pakai `mcpb pack`: skema MCPB hanya mengizinkan `name` + `description`
per tool, sedangkan Smithery mewajibkan `inputSchema` di tiap tool (validator mereka
menerimanya; `mcpb validate` menolaknya). Format .mcpb cuma arsip ZIP dengan
manifest.json di akar, jadi kita susun sendiri agar kedua pihak puas.
"""
import json
import zipfile
from pathlib import Path

AKAR = Path(__file__).resolve().parent.parent
BUNDLE = AKAR / "bundle"
KELUARAN = AKAR / "idn-econ-mcp.mcpb"

# berkas yang masuk arsip: (jalur di dalam arsip, jalur di disk)
BERKAS = [
    ("manifest.json", BUNDLE / "manifest.json"),
    ("server/server.py", AKAR / "src" / "server.py"),
    ("server/data/vpsrevenue.db", AKAR / "data" / "vpsrevenue.db"),
]


def main() -> None:
    manifest = json.loads((BUNDLE / "manifest.json").read_text(encoding="utf-8"))
    for t in manifest.get("tools", []):
        assert "inputSchema" in t, f"tool {t.get('name')} tanpa inputSchema (Smithery akan menolak)"

    if KELUARAN.exists():
        KELUARAN.unlink()

    with zipfile.ZipFile(KELUARAN, "w", zipfile.ZIP_DEFLATED) as z:
        for nama, jalur in BERKAS:
            if not jalur.exists():
                raise SystemExit(f"hilang: {jalur}")
            z.write(jalur, nama)

    ukuran = KELUARAN.stat().st_size
    print(f"dibuat: {KELUARAN}  ({ukuran/1024:.1f} KB)")
    if ukuran > 25 * 1024 * 1024:
        raise SystemExit("melebihi batas 25 MB Smithery")
    with zipfile.ZipFile(KELUARAN) as z:
        print("isi:", z.namelist())
        assert "manifest.json" in z.namelist(), "manifest.json harus di akar arsip"


if __name__ == "__main__":
    main()
