#!/usr/bin/env python3
"""
Tambah data IMF World Economic Outlook (lewat IMF DataMapper API) ke data/vpsrevenue.db.

Kenapa IMF: API-nya terbuka TANPA API key dan memuat **proyeksi sampai 2030**, sedangkan
World Bank berhenti di observasi terakhir. Ini pembeda isi untuk paket Pro.

BPS (webapi.bps.go.id) TIDAK dipakai: endpoint-nya membalas 403 (Perimeter WAF Block) dan
wajibkan pendaftaran API key. IDX butuh endpoint internal. Jadi sumber Indonesia utama
di sini adalah IMF (yang juga memuat angka Indonesia), bukan BPS.

Jalankan: python scripts/collect_imf.py
"""
from __future__ import annotations

import json
import sqlite3
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

AKAR = Path(__file__).resolve().parent.parent
DB = AKAR / "data" / "vpsrevenue.db"
DASAR = "https://www.imf.org/external/datamapper/api/v1"

NEGARA = {
    "idn": "IDN", "mys": "MYS", "tha": "THA",
    "vnm": "VNM", "phl": "PHL", "sgp": "SGP",
}
NEGARA_NAMA = {
    "idn": "Indonesia", "mys": "Malaysia", "tha": "Thailand",
    "vnm": "Vietnam", "phl": "Filipina", "sgp": "Singapura",
}

# kode IMF: (label, satuan)
INDIKATOR = {
    "PCPIPCH": ("Inflasi harga konsumen (rata-rata tahunan)", "persen"),
    "NGDPD": ("PDB harga berlaku", "miliar USD"),
    "NGDPDPC": ("PDB per kapita", "USD"),
    "NGDP_RPCH": ("Pertumbuhan PDB riil", "persen"),
    "LUR": ("Tingkat pengangguran", "persen"),
    "GGXWDG_NGDP": ("Utang pemerintah bruto", "persen PDB"),
    "BCA_NGDPD": ("Neraca transaksi berjalan", "persen PDB"),
}

LISENSI = (
    "IMF World Economic Outlook (DataMapper API) — publik, atribusi ke IMF wajib; "
    "memuat proyeksi sampai 2031. Periksa syarat penggunaan komersial IMF."
)


def ambil(indikator: str, kode: list[str]) -> dict:
    url = f"{DASAR}/{indikator}/{'/'.join(kode)}"
    with urllib.request.urlopen(url, timeout=45) as r:
        return json.loads(r.read().decode("utf-8"))


def main() -> None:
    if not DB.exists():
        sys.exit(f"DB tidak ada: {DB}")
    con = sqlite3.connect(DB)
    sekarang = datetime.now(timezone.utc).isoformat(timespec="seconds")
    total_seri = 0
    total_obs = 0

    for ind, (label, satuan) in INDIKATOR.items():
        try:
            data = ambil(ind, list(NEGARA.values()))
        except Exception as e:  # noqa: BLE001
            print(f"  LEWAT {ind}: {e}")
            continue
        nilai = (data.get("values") or {}).get(ind) or {}
        if not nilai:
            print(f"  LEWAT {ind}: tidak ada nilai")
            continue

        for kode_pendek, kode_imf in NEGARA.items():
            baris = nilai.get(kode_imf) or {}
            if not baris:
                print(f"  LEWAT {ind}/{kode_imf}: kosong")
                continue
            series_id = f"imf:{kode_pendek}:{ind}"
            con.execute(
                "INSERT OR REPLACE INTO series(series_id,nama,satuan,frekuensi,sumber,lisensi,dibuat)"
                " VALUES(?,?,?,?,?,?,?)",
                (
                    series_id,
                    f"{label} — {NEGARA_NAMA[kode_pendek]}",
                    satuan,
                    "tahunan",
                    "imf",
                    LISENSI,
                    sekarang,
                ),
            )
            total_seri += 1
            for periode, v in baris.items():
                if v is None:
                    continue
                con.execute(
                    "INSERT OR IGNORE INTO observations(series_id,periode,nilai,teks,diambil)"
                    " VALUES(?,?,?,?,?)",
                    (series_id, str(periode), float(v), None, sekarang),
                )
                total_obs += 1
            print(f"  ok {series_id}: {len(baris)} titik ({min(baris)}-{max(baris)})")

    con.execute(
        "INSERT INTO run_log(sumber,mulai,selesai,status,baris,pesan) VALUES(?,?,?,?,?,?)",
        ("imf", sekarang, datetime.now(timezone.utc).isoformat(timespec="seconds"),
         "ok", total_obs, f"{total_seri} seri"),
    )
    con.commit()

    print()
    print(f"selesai: {total_seri} seri, {total_obs} observasi")
    cur = con.execute("SELECT sumber, COUNT(*) FROM series GROUP BY sumber ORDER BY 2 DESC")
    for sumber, n in cur:
        print(f"  sumber {sumber}: {n} seri")
    cur = con.execute("SELECT COUNT(*) FROM observations")
    print(f"  total observasi: {cur.fetchone()[0]}")
    con.close()


if __name__ == "__main__":
    main()
