#!/usr/bin/env python3
"""
Bangun paket produk: kumpulan CSV dari DB + ZIP + arsip bundle .mcpb, siap dijual.

Keluaran ke ekspor/:
  - <seri>.csv            satu CSV per seri (periode,nilai) — mudah dibuka Excel
  - indonesia-asean-economic-datasets.zip   semua CSV + README + LISENSI
  - <nama>.mcpb           bundle MCP yang sama seperti yang diterbitkan

Jalankan: python scripts/build_product.py
"""
from __future__ import annotations

import csv
import io
import sqlite3
import zipfile
from datetime import datetime, timezone
from pathlib import Path

AKAR = Path(__file__).resolve().parent.parent
DB = AKAR / "data" / "vpsrevenue.db"
EKSPOR = AKAR / "ekspor"
NAMA_ZIP = "indonesia-asean-economic-datasets.zip"

README = """# Indonesia & ASEAN Economic Datasets

Data ekonomi Indonesia + 5 negara ASEAN, siap dipakai di Excel, Python, atau agen AI.

## Isi
- `data/*.csv` : satu berkas per seri, kolom `periode,nilai,satuan,sumber,lisensi`
- `idn-econ-mcp.mcpb` : server MCP (127 seri, 6 alat) untuk Claude Desktop / Cursor / klien MCP lain
- `LISENSI.md` : atribusi sumber yang wajib disertakan

## Cakupan
- 127 seri, 16.183 titik data, periode 1960-2031
- Indonesia, Malaysia, Thailand, Vietnam, Filipina, Singapura
- Inflasi, CPI, PDB & PDB per kapita, pertumbuhan, pengangguran, utang pemerintah,
  neraca transaksi berjalan, pertanian, pangan, penanaman modal, internet, harapan hidup,
  populasi, kurs harian terhadap IDR
- Mencakup PROYEKSI sampai 2031 (IMF World Economic Outlook)

## Sumber
- World Bank Open Data - CC BY 4.0 (komersial diizinkan dengan atribusi)
- IMF World Economic Outlook via DataMapper API - publik, atribusi ke IMF
- ECB euro foreign exchange reference rates - publik

## Catatan kejujuran
Periode setelah tahun berjalan pada data IMF adalah PROYEKSI, bukan realisasi.
Angka dapat direvisi oleh lembaga sumbernya. Paket ini mengemas ulang data publik,
bukan data primer.

Dihimpun oleh idn-econ-mcp.
"""

LISENSI = """# Lisensi & Atribusi

Data di paket ini dikemas ulang dari sumber publik berikut. Atribusi WAJIB disertakan
bila Anda menyebarkan ulang:

1. **World Bank Open Data** - CC BY 4.0. Komersial diizinkan dengan atribusi.
   https://data.worldbank.org
2. **IMF World Economic Outlook** (via IMF DataMapper API) - publik; periksa syarat
   penggunaan IMF untuk penggunaan komersial. https://www.imf.org/external/datamapper
3. **ECB euro foreign exchange reference rates** - publik.
   https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates

Kode dan kemasan (`idn-econ-mcp`) dilisensikan MIT.
"""


def aman(nama: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "-" for c in nama).strip("-")


def main() -> None:
    if not DB.exists():
        raise SystemExit(f"DB tidak ada: {DB}")
    if EKSPOR.exists():
        for f in EKSPOR.glob("*"):
            if f.is_file():
                f.unlink()
    (EKSPOR / "data").mkdir(parents=True, exist_ok=True)
    for f in (EKSPOR / "data").glob("*.csv"):
        f.unlink()

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    seri = con.execute("select * from series order by series_id").fetchall()

    n_baris = 0
    berkas: list[tuple[str, Path]] = []
    for s in seri:
        titik = con.execute(
            "select periode, nilai, teks from observations where series_id = ? order by periode",
            (s["series_id"],),
        ).fetchall()
        if not titik:
            continue
        nama_berkas = aman(s["series_id"].replace(":", "__")) + ".csv"
        jalur = EKSPOR / "data" / nama_berkas
        with jalur.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["periode", "nilai", "teks", "satuan", "sumber", "lisensi"])
            for t in titik:
                w.writerow([t["periode"], t["nilai"], t["teks"] or "",
                            s["satuan"] or "", s["sumber"] or "", s["lisensi"] or ""])
                n_baris += 1
        berkas.append((f"data/{nama_berkas}", jalur))

    (EKSPOR / "README.md").write_text(README, encoding="utf-8")
    (EKSPOR / "LISENSI.md").write_text(LISENSI, encoding="utf-8")

    # bundle MCP (kalau sudah dibangun)
    mcpb = AKAR / "idn-econ-mcp.mcpb"

    zip_jalur = EKSPOR / NAMA_ZIP
    with zipfile.ZipFile(zip_jalur, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(EKSPOR / "README.md", "README.md")
        z.write(EKSPOR / "LISENSI.md", "LISENSI.md")
        for nama, jalur in berkas:
            z.write(jalur, nama)
        if mcpb.exists():
            z.write(mcpb, "idn-econ-mcp.mcpb")

    con.close()
    ukuran = zip_jalur.stat().st_size
    print(f"CSV       : {len(berkas)} berkas, {n_baris} baris")
    print(f"ZIP       : {zip_jalur.name}  {ukuran/1024/1024:.2f} MB")
    print(f"bundle MCP: {'disertakan' if mcpb.exists() else 'TIDAK ada (jalankan build_bundle.py)'}")
    print(f"dibuat    : {datetime.now(timezone.utc).isoformat(timespec='seconds')}")


if __name__ == "__main__":
    main()
