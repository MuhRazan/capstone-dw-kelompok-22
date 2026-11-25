# Verifikasi panel Gold (tugas #22)

Panel Gold dibuat oleh Charrlindah pada commit `3f891eb` (PR #31) lewat `src/gold/panel.py`.
Laporan ini memeriksa apakah keluaran panel memenuhi syarat selesai kartu #22 di mesin
NIM 124450031.

## Perintah reproduksi

```bash
python pipeline.py
python -m src.common.skema data/silver/silver.parquet
```

Keluaran `pipeline.py`:

```
data/raw: 44 berkas cocok dengan MANIFEST.csv
Silver: 7,535 baris, 11 seri, 39 wilayah, 24 berkas, periode 2009-2025
Gold Panel: 3,382 baris (1,374 terisi, 2,008 kosong), 10 indikator, 5,410 baris Silver tidak terpilih
Validasi Silver: 14/14 aturan lolos
```

## Hasil pemeriksaan

| Pemeriksaan | Cara | Hasil |
|---|---|---|
| Kunci panel tidak kembar | `panel.duplicated(['wilayah_kode','periode','indikator'])` | 0 baris kembar dari 3.382 baris |
| Lineage sel terisi | `_berkas_raw` dan `_sha256_raw` tidak kosong pada 1.374 baris `status_sel=terisi` | 0 sel kosong |
| Sidik berkas mentah | setiap pasangan `_berkas_raw`/`_sha256_raw` dibandingkan dengan `MANIFEST.csv` | 0 pasangan berbeda |
| Jumlah indikator | `indikator.nunique()` | 10, sesuai daftar kartu |
| Satuan per indikator | `groupby('indikator').satuan.nunique()` | tidak ada indikator dengan lebih dari satu satuan |
| Nilai negatif | `panel.nilai < 0` | 0 baris |
| Wilayah | kode unik pada panel | 38 provinsi, tanpa baris 9999 |
| Skema Silver | `python -m src.common.skema` | LOLOS, 7.535 baris |

Status sel: 1.374 `terisi`, 1.772 `tidak_diterbitkan`, 236 `belum_ada`. Angka ini sama
dengan `reports/panel-gold.md` dan ringkasan di `reports/individu/124450037.md`.

## Indikator dan satuan

| Indikator | Satuan | Sel |
|---|---|---|
| `jumlah_penduduk` | jiwa | 38 |
| `kejadian [jumlah]` | kejadian | 608 |
| `korban_meninggal [jumlah]` | jiwa | 152 |
| `korban_hilang [jumlah]` | jiwa | 608 |
| `korban_luka_sakit [jumlah]` | jiwa | 608 |
| `korban_mengungsi [jumlah]` | jiwa | 608 |
| `korban_terdampak [jumlah]` | jiwa | 608 |
| `korban_terdampak_mengungsi [jumlah]` | jiwa | 76 |
| `korban_mengungsi_per_100rb [jumlah]` | per_100000_penduduk | 38 |
| `korban_meninggal_hilang_per_100rb [jumlah]` | per_100000_penduduk | 38 |

Panel panjang mencampur satuan di kolom `nilai`, tetapi setiap baris membawa kolom `satuan`
dan `panel_lebar.parquet` memisahkan nilai per kolom indikator. Panel lebar berisi 608 baris
dan 14 kolom.

## Contoh penelusuran satu sel Gold

Baris Aceh, kejadian tahun 2021:

| Kolom | Nilai |
|---|---|
| `wilayah_kode` | 1100 |
| `nama_wilayah` | Aceh |
| `periode` | 2021 |
| `indikator` | `kejadian [jumlah]` |
| `nilai` | 279 |
| `satuan` | kejadian |
| `_berkas_raw` | `bnpb/2026-10-20/datastore/data-bencana-indonesia/5dfcae7e-acb3-4548-82b5-61d876ea478a.json` |
| `_sha256_raw` | `5d6f131c857403cf28b2e8a5da84000017bd66dbc3a7bace8f1546370b990773` |

Cek ulang sidik berkas:

```bash
python -c "from src.common.manifest import sha256_raw; print(sha256_raw('bnpb/2026-10-20/datastore/data-bencana-indonesia/5dfcae7e-acb3-4548-82b5-61d876ea478a.json'))"
```

Hasilnya sama dengan `_sha256_raw` di atas.

## Catatan

- Nilai `nilai_per_100rb` memakai penyebut `jumlah_penduduk` 2025 untuk semua periode
  (keputusan K-045). Penduduk per tahun belum diunduh sebagai data pendukung.
- Nilai asli tetap tersimpan di kolom `nilai`; `nilai_log1p` hanya tambahan untuk analisis.
- Metrik yang ditulis ke `results/124450031/metrics.json`: `seri_panel=10`,
  `rincian_dienkode=9`, `baris_silver=7535`, `keputusan_dicatat=19`, `baris_gold=3382`.
