#!/usr/bin/env python3
"""
idn-econ-mcp — MCP server: data ekonomi & keuangan Indonesia untuk agen AI.

Read-only, tanpa API key, tanpa biaya. Membaca database SQLite yang dipanen oleh
pipeline vps-revenue (sumber: World Bank Open Data CC BY 4.0 + ECB FX rates).

Atribusi WAJIB (lisensi CC BY 4.0): sebutkan sumber World Bank / ECB pada keluaran.
"""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

from mcp.server import MCPServer

DB = Path(os.environ.get("IDN_ECON_DB", Path(__file__).resolve().parent.parent / "data" / "vpsrevenue.db"))

server = MCPServer(
    name="idn-econ",
    title="Indonesia Economic & Financial Data",
    version="1.1.0",
    description=(
        "Data ekonomi dan keuangan Indonesia siap pakai untuk agen AI: inflasi, PDB, "
        "kurs, nilai tambah sektoral, dan perbandingan ASEAN. Sumber: World Bank Open Data "
        "(CC BY 4.0), IMF World Economic Outlook (proyeksi s.d. 2031) dan ECB reference rates. "
        "Tanpa API key."
    ),
    instructions=(
        "Alat untuk mengambil data ekonomi Indonesia dan ASEAN. Mulai dari 'cari_series' "
        "untuk menemukan ID seri, lalu 'ambil_series' untuk datanya. Seri berawalan 'wb:' "
        "berasal dari World Bank (realisasi), 'imf:' dari IMF World Economic Outlook "
        "(realisasi + proyeksi sampai 2031). Sertakan atribusi pada keluaran Anda."
    ),
)

ATRIBUSI = (
    "Sumber: World Bank Open Data (CC BY 4.0), IMF World Economic Outlook (DataMapper API) "
    "& ECB euro foreign exchange reference rates. Dihimpun oleh idn-econ-mcp. "
    "Periode setelah tahun berjalan pada data IMF adalah PROYEKSI, bukan realisasi."
)


def _con() -> sqlite3.Connection:
    if not DB.exists():
        raise FileNotFoundError(
            f"Database tidak ditemukan di {DB}. Set env IDN_ECON_DB ke jalur vpsrevenue.db."
        )
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


@server.tool()
def cek_server() -> dict:
    """Cek kesehatan server dan ringkasan isi basis data (jumlah seri, rentang periode)."""
    con = _con()
    try:
        n_series = con.execute("select count(*) from series").fetchone()[0]
        n_obs = con.execute("select count(*) from observations").fetchone()[0]
        rentang = con.execute("select min(periode), max(periode) from observations").fetchone()
        sumber = [r[0] for r in con.execute("select distinct sumber from series order by 1")]
        return {
            "status": "ok",
            "jumlah_series": n_series,
            "jumlah_observasi": n_obs,
            "periode_awal": rentang[0],
            "periode_akhir": rentang[1],
            "sumber": sumber,
            "atribusi": ATRIBUSI,
        }
    finally:
        con.close()


@server.tool()
def cari_series(q: str, batas: int = 15) -> dict:
    """Cari seri data ekonomi berdasarkan kata kunci (Indonesia, ASEAN, inflasi, PDB, kurs, dll).

    Args:
        q: kata kunci pencarian, mis. 'inflasi', 'PDB', 'kurs', 'pertanian', 'Indonesia'
        batas: jumlah maksimum hasil (default 15)
    """
    con = _con()
    try:
        pola = f"%{q.lower()}%"
        rows = con.execute(
            """
            select s.series_id, s.nama, s.satuan, s.frekuensi, s.sumber,
                   (select count(*) from observations o where o.series_id = s.series_id) as n_titik,
                   (select min(periode) from observations o where o.series_id = s.series_id) as awal,
                   (select max(periode) from observations o where o.series_id = s.series_id) as akhir
            from series s
            where lower(s.series_id) like ? or lower(s.nama) like ? or lower(s.sumber) like ?
            order by n_titik desc, s.series_id
            limit ?
            """,
            (pola, pola, pola, max(1, min(int(batas), 100))),
        ).fetchall()
        return {
            "kata_kunci": q,
            "jumlah": len(rows),
            "hasil": [dict(r) for r in rows],
            "petunjuk": "Pakai 'ambil_series' dengan series_id untuk mengambil datanya.",
            "atribusi": ATRIBUSI,
        }
    finally:
        con.close()


@server.tool()
def ambil_series(series_id: str, mulai: str | None = None, sampai: str | None = None, batas: int = 200) -> dict:
    """Ambil titik data dari satu seri (urut terbaru dulu).

    Args:
        series_id: ID seri persis, mis. 'wb:idn:FP.CPI.TOTL.ZG' (pakai 'cari_series' dulu)
        mulai: periode awal (opsional), mis. '2015'
        sampai: periode akhir (opsional), mis. '2024'
        batas: jumlah maksimum titik data (default 200)
    """
    con = _con()
    try:
        meta = con.execute("select * from series where series_id = ?", (series_id,)).fetchone()
        if not meta:
            mirip = con.execute(
                "select series_id, nama from series where lower(series_id) like ? limit 8",
                (f"%{series_id.lower()}%",),
            ).fetchall()
            return {
                "error": f"series_id '{series_id}' tidak ditemukan.",
                "mirip": [dict(r) for r in mirip],
                "petunjuk": "Pakai 'cari_series' untuk menemukan ID yang benar.",
            }
        sql = "select periode, nilai, teks from observations where series_id = ?"
        par: list = [series_id]
        if mulai:
            sql += " and periode >= ?"
            par.append(mulai)
        if sampai:
            sql += " and periode <= ?"
            par.append(sampai)
        sql += " order by periode desc limit ?"
        par.append(max(1, min(int(batas), 2000)))
        titik = con.execute(sql, par).fetchall()
        return {
            "series_id": series_id,
            "nama": meta["nama"],
            "satuan": meta["satuan"],
            "frekuensi": meta["frekuensi"],
            "sumber": meta["sumber"],
            "lisensi": meta["lisensi"],
            "jumlah_titik": len(titik),
            "titik": [{"periode": t["periode"], "nilai": t["nilai"], "teks": t["teks"]} for t in titik],
            "atribusi": ATRIBUSI,
        }
    finally:
        con.close()


@server.tool()
def kurs_terkini(base: str = "USD", quote: str = "IDR") -> dict:
    """Kurs terkini terhadap Rupiah dari data ECB (mis. USD/IDR, EUR/IDR, SGD/IDR, CNY/IDR).

    Args:
        base: mata uang asal, mis. 'USD', 'EUR', 'SGD', 'CNY', 'JPY', 'MYR'
        quote: mata uang tujuan (default 'IDR')
    """
    con = _con()
    try:
        sid = f"fx:{base.upper()}{quote.upper()}"
        titik = con.execute(
            "select periode, nilai from observations where series_id = ? order by periode desc limit 30",
            (sid,),
        ).fetchall()
        if not titik:
            tersedia = [
                r[0]
                for r in con.execute("select series_id from series where sumber='fx' order by 1")
            ]
            return {"error": f"pasangan {sid} tidak tersedia.", "tersedia": tersedia}
        return {
            "pasangan": f"{base.upper()}/{quote.upper()}",
            "terbaru": {"periode": titik[0]["periode"], "nilai": titik[0]["nilai"]},
            "riwayat_30_terakhir": [
                {"periode": t["periode"], "nilai": t["nilai"]} for t in titik
            ],
            "sumber": "ECB euro foreign exchange reference rates",
            "atribusi": ATRIBUSI,
        }
    finally:
        con.close()


@server.tool()
def banding_asean(indikator: str = "inflasi", mulai: str | None = None) -> dict:
    """Bandingkan satu indikator antar negara ASEAN (IDN, MYS, THA, VNM, PHL, SGP).

    Args:
        indikator: salah satu dari 'inflasi', 'cpi', 'pertanian', 'pangan' (World Bank),
            atau 'pertumbuhan', 'pdb', 'pdb_per_kapita', 'pengangguran', 'utang',
            'transaksi_berjalan' (IMF, memuat proyeksi sampai 2031)
        mulai: periode awal (opsional)
    """
    # World Bank: series_id 'wb:<iso>:<KODE>'
    wb_peta = {
        "inflasi": "FP.CPI.TOTL.ZG",
        "cpi": "FP.CPI.TOTL",
        "pertanian": "NV.AGR.TOTL.ZS",
        "pangan": "AG.PRD.FOOD.XD",
    }
    # IMF: series_id 'imf:<iso>:<KODE>'
    imf_peta = {
        "pertumbuhan": "NGDP_RPCH",
        "pdb": "NGDPD",
        "pdb_per_kapita": "NGDPDPC",
        "pengangguran": "LUR",
        "utang": "GGXWDG_NGDP",
        "transaksi_berjalan": "BCA_NGDPD",
    }
    kunci = indikator.lower().strip()
    if kunci in wb_peta:
        prefiks, kode, sumber_data = "wb", wb_peta[kunci], "worldbank"
    elif kunci in imf_peta:
        prefiks, kode, sumber_data = "imf", imf_peta[kunci], "imf"
    else:
        return {
            "error": f"indikator '{indikator}' tidak dikenal.",
            "pilihan": sorted(list(wb_peta.keys()) + list(imf_peta.keys())),
        }
    con = _con()
    try:
        negara = {"idn": "Indonesia", "mys": "Malaysia", "tha": "Thailand",
                  "vnm": "Vietnam", "phl": "Filipina", "sgp": "Singapura"}
        keluar: dict = {}
        for iso, nm in negara.items():
            sid = f"{prefiks}:{iso}:{kode}"
            sql = "select periode, nilai from observations where series_id = ?"
            par: list = [sid]
            if mulai:
                sql += " and periode >= ?"
                par.append(mulai)
            sql += " order by periode desc limit 1"
            t = con.execute(sql, par).fetchone()
            keluar[nm] = {"periode": t["periode"], "nilai": t["nilai"]} if t else None
        return {
            "indikator": indikator,
            "kode": kode,
            "sumber_data": sumber_data,
            "terbaru_per_negara": keluar,
            "catatan": (
                "Data IMF: periode setelah tahun berjalan adalah proyeksi."
                if sumber_data == "imf"
                else None
            ),
            "atribusi": ATRIBUSI,
        }
    finally:
        con.close()


@server.tool()
def daftar_indikator() -> dict:
    """Daftar semua indikator yang tersedia beserta jumlah seri dan cakupan negaranya."""
    con = _con()
    try:
        # series_id berformat '<prefiks>:<negara>:<KODE>' — ambil KODE-nya di Python
        # (SQLite tidak punya instr() 3-argumen).
        hitung: dict = {}
        for sumber, prefiks in (("worldbank", "wb"), ("imf", "imf")):
            for (sid,) in con.execute(
                "select series_id from series where sumber = ?", (sumber,)
            ):
                bagian = sid.split(":", 2)
                kode = bagian[2] if len(bagian) > 2 else sid
                kunci = f"{prefiks}:{kode}"
                hitung[kunci] = hitung.get(kunci, 0) + 1
        fx = [r[0] for r in con.execute("select series_id from series where sumber='fx' order by 1")]
        return {
            "indikator": [
                {"kode": k, "n_seri": v}
                for k, v in sorted(hitung.items(), key=lambda x: (-x[1], x[0]))
            ],
            "pasangan_kurs": fx,
            "catatan": (
                "Kode negara dalam series_id: idn, mys, tha, vnm, phl, sgp. "
                "Prefiks 'wb:' = World Bank (realisasi), 'imf:' = IMF WEO "
                "(realisasi + proyeksi sampai 2031)."
            ),
            "atribusi": ATRIBUSI,
        }
    finally:
        con.close()


def main() -> None:
    """Entry point untuk `idn-econ-mcp` (stdio)."""
    server.run("stdio")


if __name__ == "__main__":
    main()
