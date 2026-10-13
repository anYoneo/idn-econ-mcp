#!/usr/bin/env python3
"""
Bangun paket produk LENGKAP sesuai yang dijanjikan deskripsi listing Lynk.id:
CSV long-format (9 kolom) + Excel .xlsx + Parquet + manifest.json + ATRIBUSI.txt + README_PEMBELI.txt.

Berbeda dari build_product.py (CSV per seri), skrip ini menghasilkan SATU tabel panjang
yang siap dianalisis dengan pandas, plus format biner Excel/Parquet.

Jalankan:  <python-venv-dengan-pandas> scripts/build_paket_pembeli.py
Keluaran:  ekspor-pembeli/Indonesia-ASEAN-Macro-Dataset-2026.zip
"""
from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

AKAR = Path(__file__).resolve().parent.parent
DB = AKAR / "data" / "vpsrevenue.db"
OUT = AKAR / "ekspor-pembeli"
NAMA_DASAR = "Indonesia-ASEAN-Macro-Dataset-2026"

NEGARA = {
    "idn": "Indonesia", "mys": "Malaysia", "tha": "Thailand",
    "vnm": "Vietnam", "phl": "Filipina", "sgp": "Singapura",
}
SUMBER_PANJANG = {
    "worldbank": "World Bank Open Data (CC BY 4.0)",
    "imf": "IMF World Economic Outlook (DataMapper API)",
    "fx": "ECB euro foreign exchange reference rates",
}

README = """# Indonesia & ASEAN Macro Dataset 2026

Terima kasih sudah membeli. Paket ini berisi data makroekonomi Indonesia dan 5 negara
ASEAN, siap dianalisis tanpa langkah scraping.

## Isi paket

| Berkas | Isi |
|---|---|
| `data/indonesia_asean_macro.csv` | Tabel lengkap, format long, 9 kolom |
| `data/indonesia_asean_macro.xlsx` | Versi Excel (2 sheet: data + kamus) |
| `data/indonesia_asean_macro.parquet` | Versi kolumnar untuk pandas/polars |
| `manifest.json` | Sumber, lisensi, cakupan, tanggal snapshot |
| `ATRIBUSI.txt` | Atribusi wajib bila Anda menyebarkan ulang |
| `kamus_kolom.csv` | Penjelasan tiap kolom |

## Kolom

`series_id, nama_seri, indikator, negara, neg_iso, satuan, frekuensi, periode, nilai, sumber, lisensi`

(11 kolom pada CSV; kolom `teks` hanya diisi bila nilai bukan angka — praktis kosong.)

## Cara pakai

```python
import pandas as pd
df = pd.read_csv("data/indonesia_asean_macro.csv")
# inflasi Indonesia sejak 2015
df[(df.negara == "Indonesia") & (df.indikator == "FP.CPI.TOTL.ZG") & (df.periode >= 2015)]
```

```sql
-- atau di BI tool apa pun
SELECT negara, periode, nilai FROM data WHERE indikator = 'NGDP_RPCH' ORDER BY periode;
```

## Cakupan

- **{n_seri} seri**, **{n_obs} titik data**, periode **{awal}–{akhir}**
- 6 negara: Indonesia, Malaysia, Thailand, Vietnam, Filipina, Singapura
- World Bank: CPI, inflasi, PDB, PDB per kapita, pengangguran, penanaman modal, pertanian,
  produksi pangan, pupuk, pengguna internet, harapan hidup, populasi, kurs resmi
- IMF WEO: inflasi, PDB, PDB per kapita, pertumbuhan riil, pengangguran, utang pemerintah,
  neraca transaksi berjalan — **termasuk proyeksi sampai {akhir}**
- Kurs harian ECB terhadap IDR: USD, EUR, SGD, CNY, JPY, MYR

## Penting & jujur

- Data **tahunan** untuk World Bank/IMF. Kurs ECB **harian**.
- Periode setelah tahun berjalan pada data IMF adalah **PROYEKSI**, bukan realisasi.
  Jangan menyajikannya sebagai angka aktual.
- Angka dapat **direvisi** oleh lembaga sumbernya. Paket ini mengemas ulang data publik,
  bukan data primer, dan tidak menjanjikan pembaruan otomatis.
- Snapshot: **{tanggal}**.

## Bantuan

Ada pertanyaan atau butuh pembaruan? Hubungi penjual lewat halaman produk Lynk.id.
"""

ATRIBUSI = """ATRIBUSI & LISENSI — Indonesia & ASEAN Macro Dataset 2026
==========================================================

Data dalam paket ini dikemas ulang dari sumber publik berikut.
Atribusi WAJIB disertakan bila Anda menyebarkan ulang data ini:

1. World Bank Open Data — lisensi CC BY 4.0 (komersial diizinkan dengan atribusi).
   https://data.worldbank.org

2. IMF World Economic Outlook (via IMF DataMapper API) — publik.
   Periksa syarat penggunaan IMF untuk keperluan komersial.
   https://www.imf.org/external/datamapper

3. ECB euro foreign exchange reference rates — publik.
   https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates

Kemasan, penamaan kolom, dan dokumen ini: MIT (kode) oleh idn-econ-mcp.
"""

KAMUS = [
    ("series_id", "ID unik seri, mis. 'wb:idn:FP.CPI.TOTL.ZG' atau 'imf:idn:NGDP_RPCH'"),
    ("nama_seri", "Nama deskriptif seri dari sumber"),
    ("indikator", "Kode indikator sumber (World Bank / IMF)"),
    ("negara", "Nama negara dalam bahasa Indonesia"),
    ("neg_iso", "Kode negara 3 huruf (idn, mys, tha, vnm, phl, sgp)"),
    ("satuan", "Satuan nilai: persen, indeks, USD, miliar USD, atau kurs"),
    ("frekuensi", "tahunan atau harian"),
    ("periode", "Tahun (mis. 2025) atau tanggal ISO (kurs harian)"),
    ("nilai", "Nilai numerik"),
    ("sumber", "worldbank | imf | fx"),
    ("lisensi", "Teks lisensi sumber"),
]


def main() -> None:
    if not DB.exists():
        raise SystemExit(f"DB tidak ada: {DB}")
    if OUT.exists():
        for f in OUT.rglob("*"):
            if f.is_file():
                f.unlink()
    (OUT / "data").mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    baris = con.execute(
        """
        select s.series_id, s.nama, s.satuan, s.frekuensi, s.sumber, s.lisensi,
               o.periode, o.nilai
        from observations o
        join series s on s.series_id = o.series_id
        where o.nilai is not null
        order by s.series_id, o.periode
        """
    ).fetchall()
    con.close()
    if not baris:
        raise SystemExit("tidak ada observasi")

    df = pd.DataFrame([dict(r) for r in baris])
    bagian = df["series_id"].str.split(":", n=2, expand=True)
    df["kode_sumber"] = bagian[0]
    df["neg_iso"] = bagian[1]
    kode_ind = bagian[2] if bagian.shape[1] > 2 else pd.Series([None] * len(df))
    # Seri kurs berformat 'fx:USDIDR' (hanya 2 bagian) — pakai pasangannya sebagai indikator.
    df["indikator"] = kode_ind.fillna(bagian[1])
    df.loc[df["kode_sumber"] == "fx", "neg_iso"] = "global"
    df["negara"] = df["neg_iso"].map(NEGARA).fillna(
        df["neg_iso"].map({"global": "Kurs (global)"}).fillna(df["neg_iso"])
    )
    df["nama_seri"] = df["nama"]
    df = df.rename(columns={"nama": "nama_asli"})
    df["sumber_panjang"] = df["kode_sumber"].map(SUMBER_PANJANG).fillna(df["kode_sumber"])
    df["periode"] = df["periode"].astype(str)
    df["nilai"] = pd.to_numeric(df["nilai"], errors="coerce")
    df = df.dropna(subset=["nilai"])

    kolom = ["series_id", "nama_seri", "indikator", "negara", "neg_iso", "satuan",
             "frekuensi", "periode", "nilai", "sumber_panjang", "lisensi"]
    df = df[kolom].rename(columns={"sumber_panjang": "sumber"})
    df = df.sort_values(["series_id", "periode"]).reset_index(drop=True)

    csv_j = OUT / "data" / "indonesia_asean_macro.csv"
    xlsx_j = OUT / "data" / "indonesia_asean_macro.xlsx"
    parquet_j = OUT / "data" / "indonesia_asean_macro.parquet"

    df.to_csv(csv_j, index=False, encoding="utf-8")
    df.to_parquet(parquet_j, index=False)
    kamus_df = pd.DataFrame(KAMUS, columns=["kolom", "penjelasan"])
    with pd.ExcelWriter(xlsx_j, engine="openpyxl") as w:
        df.to_excel(w, sheet_name="data", index=False)
        kamus_df.to_excel(w, sheet_name="kamus", index=False)
    kamus_df.to_csv(OUT / "kamus_kolom.csv", index=False, encoding="utf-8")

    meta = {
        "nama": "Indonesia & ASEAN Macro Dataset 2026",
        "versi": "2026.10",
        "snapshot": datetime.now(timezone.utc).date().isoformat(),
        "jumlah_seri": int(df["series_id"].nunique()),
        "jumlah_baris": int(len(df)),
        "periode": {"awal": str(df["periode"].min()), "akhir": str(df["periode"].max())},
        "negara": sorted(df["negara"].unique().tolist()),
        "indikator": sorted(df["indikator"].unique().tolist()),
        "kolom": kolom,
        "sumber": [
            {"kode": "worldbank", "nama": "World Bank Open Data", "lisensi": "CC BY 4.0"},
            {"kode": "imf", "nama": "IMF World Economic Outlook", "lisensi": "publik, atribusi IMF"},
            {"kode": "fx", "nama": "ECB euro reference rates", "lisensi": "publik, atribusi ECB"},
        ],
        "catatan": "Data IMF setelah tahun berjalan adalah PROYEKSI. Angka dapat direvisi sumbernya.",
        "dibuat_oleh": "idn-econ-mcp",
    }
    (OUT / "manifest.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUT / "ATRIBUSI.txt").write_text(ATRIBUSI, encoding="utf-8")
    (OUT / "README_PEMBELI.txt").write_text(
        README.format(
            n_seri=meta["jumlah_seri"], n_obs=f"{meta['jumlah_baris']:,}".replace(",", "."),
            awal=meta["periode"]["awal"], akhir=meta["periode"]["akhir"],
            tanggal=meta["snapshot"],
        ),
        encoding="utf-8",
    )

    # ZIP akhir — susun daftar berkas eksplisit supaya ZIP tidak memuat dirinya sendiri
    import zipfile
    zip_jalur = OUT / f"{NAMA_DASAR}.zip"
    if zip_jalur.exists():
        zip_jalur.unlink()
    masuk = [
        ("README_PEMBELI.txt", OUT / "README_PEMBELI.txt"),
        ("ATRIBUSI.txt", OUT / "ATRIBUSI.txt"),
        ("manifest.json", OUT / "manifest.json"),
        ("kamus_kolom.csv", OUT / "kamus_kolom.csv"),
        ("data/indonesia_asean_macro.csv", csv_j),
        ("data/indonesia_asean_macro.xlsx", xlsx_j),
        ("data/indonesia_asean_macro.parquet", parquet_j),
    ]
    with zipfile.ZipFile(zip_jalur, "w", zipfile.ZIP_DEFLATED) as z:
        for nama, jalur in masuk:
            z.write(jalur, nama)

    print(f"CSV    : {csv_j.name}  {csv_j.stat().st_size/1024/1024:.2f} MB")
    print(f"Excel  : {xlsx_j.name}  {xlsx_j.stat().st_size/1024/1024:.2f} MB")
    print(f"Parquet: {parquet_j.name}  {parquet_j.stat().st_size/1024/1024:.2f} MB")
    print(f"ZIP    : {zip_jalur.name}  {zip_jalur.stat().st_size/1024/1024:.2f} MB")
    print(f"isi    : {meta['jumlah_seri']} seri, {meta['jumlah_baris']} baris, "
          f"{meta['periode']['awal']}-{meta['periode']['akhir']}, {len(meta['negara'])} negara")


if __name__ == "__main__":
    main()
