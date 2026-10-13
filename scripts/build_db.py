# Muat data ekonomi Indonesia/ASEAN dari World Bank Open Data + kurs ECB (tanpa API key).
# Jalankan: python scripts/build_db.py
#
# Skrip ini memakai collector yang sama dengan pipeline vps-revenue. Kalau Anda sudah
# punya file vpsrevenue.db dari pipeline itu, cukup salin ke data/ dan lewati langkah ini.
import sys
from pathlib import Path

AKAR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AKAR.parent / "vps-revenue"))

INDIKATOR = [
    "FP.CPI.TOTL",       # indeks harga konsumen
    "FP.CPI.TOTL.ZG",    # inflasi
    "AG.PRD.FOOD.XD",    # indeks produksi pangan
    "NV.AGR.TOTL.ZS",    # nilai tambah pertanian (% PDB)
]
NEGARA = ["idn", "mys", "tha", "vnm", "phl", "sgp"]
MATA_UANG = ["USD", "EUR", "SGD", "CNY", "JPY", "MYR"]


def main() -> None:
    try:
        from collectors import worldbank as wb  # type: ignore
        from collectors import fx as fx  # type: ignore
    except ImportError:
        print("Collector vps-revenue tidak ditemukan di sebelah folder ini.")
        print("Salin saja data/vpsrevenue.db dari pipeline vps-revenue, atau jalankan")
        print("skrip ini dari dalam folder vps-revenue.")
        sys.exit(1)

    print(f"mengambil {len(INDIKATOR)} indikator × {len(NEGARA)} negara dari World Bank...")
    for neg in NEGARA:
        for ind in INDIKATOR:
            try:
                wb.ambil(neg, ind) if hasattr(wb, "ambil") else None
            except Exception as e:  # noqa: BLE001
                print(f"  lewat {neg}/{ind}: {e}")
    print("mengambil kurs ECB vs IDR...")
    for mu in MATA_UANG:
        try:
            fx.ambil(mu, "IDR") if hasattr(fx, "ambil") else None
        except Exception as e:  # noqa: BLE001
            print(f"  lewat {mu}/IDR: {e}")
    print("selesai. Periksa data/vpsrevenue.db")


if __name__ == "__main__":
    main()
