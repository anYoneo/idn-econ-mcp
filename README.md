# idn-econ-mcp — Data Ekonomi Indonesia untuk Agen AI

MCP server read-only yang menyajikan data ekonomi & keuangan Indonesia dan ASEAN
siap pakai untuk agen AI (Claude Desktop, Cursor, VS Code, ChatGPT Desktop, dan
klien MCP lain). **Tanpa API key. Tanpa biaya.**

## Kenapa ini ada

Kalau Anda meminta agen AI menjawab pertanyaan seperti *"berapa inflasi Indonesia
dan bagaimana dibanding Malaysia?"*, agen itu menebak atau mengarang. Server ini
memberi angka nyata dari World Bank Open Data + kurs ECB — langsung, tanpa scraping.

## Alat yang tersedia

| Tool | Kegunaan |
|---|---|
| `cari_series` | Cari seri data berdasarkan kata kunci (`inflasi`, `PDB`, `kurs`, `pertanian`) |
| `ambil_series` | Ambil titik data satu seri (mis. `wb:idn:FP.CPI.TOTL.ZG`), dengan filter periode |
| `kurs_terkini` | Kurs terkini vs Rupiah: USD, EUR, SGD, CNY, JPY, MYR |
| `banding_asean` | Bandingkan indikator antar 6 negara ASEAN (IDN, MYS, THA, VNM, PHL, SGP) |
| `daftar_indikator` | Daftar semua indikator & pasangan kurs yang tersedia |
| `cek_server` | Status & ringkasan isi basis data |

## Cakupan data

- **85 seri**, **14.122 observasi**, periode **1960 – 2026** (diperbarui berkala)
- **Indikator**: inflasi (CPI), indeks harga konsumen, produksi pangan, nilai tambah
  pertanian (% PDB), dan indikator lain per negara
- **Negara**: Indonesia, Malaysia, Thailand, Vietnam, Filipina, Singapura
- **Kurs**: USD, EUR, SGD, CNY, JPY, MYR terhadap IDR (ECB, harian)

## Cara pakai

### Claude Desktop / klien MCP lain (stdio)

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

Atau setelah `pip install idn-econ-mcp`:

```json
{"mcpServers": {"idn-econ": {"command": "idn-econ-mcp"}}}
```

### Contoh tanya ke agen

- *"Ambil inflasi Indonesia 2015–2025, lalu bandingkan dengan Vietnam."*
- *"Berapa kurs USD/IDR terbaru dan bagaimana trennya 30 hari terakhir?"*
- *"Negara ASEAN mana yang nilai tambah pertaniannya paling besar terhadap PDB?"*

## Membangun basis data sendiri

```bash
python scripts/build_db.py          # ambil ulang dari World Bank + ECB
```

Basis data juga bisa disalin dari pipeline `vps-revenue`.

## Sumber data & lisensi

- **World Bank Open Data** — lisensi CC BY 4.0; **komersial diizinkan dengan atribusi**
- **ECB euro foreign exchange reference rates** — boleh dipakai ulang dengan atribusi

Semua keluaran menyertakan kolom `atribusi` supaya Anda mudah mematuhi lisensinya.

## Batasan (jujur)

- Data **tahunan** untuk indikator World Bank (bukan real-time) — publikasi terbaru
  bisa tertinggal beberapa bulan dari kondisi lapangan.
- Cakupan indikator terbatas pada yang terdaftar di `daftar_indikator`.
- Data Indonesia yang lebih baru dari BPS **belum** disertakan.

## Lisensi

MIT (kode). Data mengikuti lisensi masing-masing sumber di atas.
