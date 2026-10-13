# idn-econ-mcp — Data Ekonomi Indonesia untuk Agen AI

MCP server read-only yang menyajikan data ekonomi & keuangan Indonesia dan ASEAN
siap pakai untuk agen AI (Claude Desktop, Cursor, VS Code, klien MCP lain).
**Tanpa API key. Tanpa biaya.**

- Registry MCP resmi: `io.github.anYoneo/indonesia-economic-data`
- Smithery: `bowolime/indonesia-economic-data` — https://smithery.ai/servers/bowolime/indonesia-economic-data

## Kenapa ini ada

Kalau Anda meminta agen AI menjawab pertanyaan seperti *"berapa inflasi Indonesia
dan bagaimana dibanding Vietnam?"*, agen itu menebak atau mengarang. Server ini
memberi angka nyata dari World Bank, IMF, dan ECB — langsung, tanpa scraping.

## Alat yang tersedia

| Tool | Kegunaan |
|---|---|
| `cari_series` | Cari seri data berdasarkan kata kunci (`inflasi`, `PDB`, `kurs`, `imf`) |
| `ambil_series` | Ambil titik data satu seri (mis. `imf:idn:NGDP_RPCH`), dengan filter periode |
| `kurs_terkini` | Kurs terkini vs Rupiah: USD, EUR, SGD, CNY, JPY, MYR |
| `banding_asean` | Bandingkan indikator antar 6 negara ASEAN (`inflasi`, `pertumbuhan`, `utang`, …) |
| `daftar_indikator` | Daftar semua indikator & pasangan kurs yang tersedia |
| `cek_server` | Status & ringkasan isi basis data |

## Cakupan data

- **127 seri**, **16.183 observasi**, periode **1960 – 2031**
- **Negara**: Indonesia, Malaysia, Thailand, Vietnam, Filipina, Singapura
- **World Bank** (realisasi): inflasi, CPI, PDB, PDB per kapita, pengangguran,
  penanaman modal, pertanian, pangan, pupuk, internet, harapan hidup, populasi
- **IMF WEO** (realisasi **+ proyeksi sampai 2031**): inflasi, PDB, PDB per kapita,
  pertumbuhan riil, pengangguran, utang pemerintah (% PDB), neraca transaksi berjalan
- **Kurs harian** terhadap IDR (ECB): USD, EUR, SGD, CNY, JPY, MYR

Prefiks `series_id`: `wb:` = World Bank, `imf:` = IMF WEO, `fx:` = kurs ECB.

## Cara pakai

### Bundle MCP (tanpa Python setup)

Unduh `idn-econ-mcp.mcpb` lalu buka di klien yang mendukung bundle MCP (Claude Desktop).
Bundle berisi server + basis data, ~966 KB.

### stdio manual

```json
{
  "mcpServers": {
    "idn-econ": {
      "command": "python",
      "args": ["/path/ke/idn-econ-mcp/src/server.py"],
      "env": { "IDN_ECON_DB": "/path/ke/vpsrevenue.db" }
    }
  }
}
```

### Contoh tanya ke agen

- *"Ambil inflasi Indonesia 2015–2025, lalu bandingkan dengan Vietnam."*
- *"Berapa proyeksi pertumbuhan PDB Indonesia 2030 menurut IMF?"*
- *"Berapa kurs USD/IDR terbaru dan bagaimana trennya 30 hari terakhir?"*

## Membangun / memperbarui basis data

```bash
python scripts/build_db.py           # World Bank + ECB (butuh collector vps-revenue)
python scripts/collect_imf.py        # IMF WEO lewat DataMapper API (tanpa key)
python scripts/build_bundle.py       # bangun idn-econ-mcp.mcpb
python scripts/build_product.py      # bangun CSV + ZIP paket data untuk dijual
python tests/test_server.py          # 10 uji (pemanggilan langsung + handshake stdio)
```

## Sumber data & lisensi

- **World Bank Open Data** — CC BY 4.0; **komersial diizinkan dengan atribusi**
- **IMF World Economic Outlook** (DataMapper API) — publik; periksa syarat komersial IMF
- **ECB euro foreign exchange reference rates** — boleh dipakai ulang dengan atribusi

Semua keluaran menyertakan kolom `atribusi` supaya Anda mudah mematuhi lisensinya.

## Batasan (jujur)

- Data **tahunan** untuk indikator World Bank/IMF (bukan real-time); publikasi terbaru
  bisa tertinggal beberapa bulan dari kondisi lapangan.
- Periode setelah tahun berjalan pada data IMF adalah **proyeksi**, bukan realisasi.
- **BPS tidak disertakan**: `webapi.bps.go.id` membalas 403 (Perimeter WAF) dan
  mewajibkan pendaftaran API key. IDX juga butuh endpoint internal. Jadi tidak ada
  sumber Indonesia yang lebih baru dari World Bank/IMF di paket ini.
- Cakupan indikator terbatas pada yang terdaftar di `daftar_indikator`.

## Lisensi

MIT (kode). Data mengikuti lisensi masing-masing sumber di atas.
