# Data dictionary — Kelompok 22 Korban Bencana

Satu tabel per keluaran. Isi di bawah dihitung dari `data/silver/silver.parquet` yang
dihasilkan `python pipeline.py` (7.535 baris, 11 seri, 39 wilayah, 24 berkas sumber,
periode 2009–2025). Angka dapat diperiksa ulang dengan `python -m src.common.skema
data/silver/silver.parquet` dan `python -m src.validasi`.

## data/silver/silver.parquet

Satu baris = satu seri × wilayah × periode × rincian × berkas sumber. Nilai dari sumber
berbeda tidak digabung di Silver.

| Kolom | Tipe | Satuan/format | Boleh kosong | Rentang atau nilai sah | Asal (berkas/aturan) | Keterangan |
|---|---|---|---|---|---|---|
| `sumber` | string | — | tidak | `bnpb_xlsx` (4.383 baris), `bnpb_json` (3.151 baris), `wdi` (1 baris) | Ditetapkan pembaca `src/ekstraksi/bnpb_xlsx.py`, `src/ekstraksi/bnpb_json.py`, `src/ekstraksi/wdi.py`, lalu diisi di `src/silver/__init__.py` | Arti: keluarga berkas mentah asal baris. `bnpb_xlsx` = 11 berkas XLSX 2021/2022/2025; `bnpb_json` = 12 resource JSON datastore BNPB; `wdi` = metadata/indikator World Bank. |
| `seri_kode` | string | — | tidak | 11 nilai: `kejadian`, `korban_meninggal`, `korban_hilang`, `korban_luka_sakit`, `korban_terdampak`, `korban_mengungsi`, `korban_terdampak_mengungsi`, `korban_mengungsi_per_100rb`, `korban_meninggal_hilang_per_100rb`, `jumlah_penduduk`, `EN.CLC.MDAT.ZS` | Peta nama indikator mentah → kode seri di `SATUAN`/`SERI` (`src/silver/__init__.py`); daftar resmi di `docs/katalog-seri.csv`; K-005, K-017, K-018 | Arti: kode indikator yang diukur. Tujuh seri korban memakai kode SDG 13.1.1/1.5.1/11.5.1; `kejadian`, `jumlah_penduduk`, dan `EN.CLC.MDAT.ZS` tidak memakai kode SDG (K-019). |
| `wilayah_kode` | integer (`int64`) | kode BPS 2 digit × 100; `9999` = Indonesia | tidak | 38 kode provinsi 2025 (1100–9600, kelipatan 100) + `9999`; 39 nilai unik | Aturan pemetaan wilayah K-001/K-002 dan fungsi `_wilayah` di `src/silver/__init__.py`; kode diambil dari kolom `Kode Wilayah Provinsi` atau peta nama provinsi | Arti: wilayah administratif baris. Provinsi baru (Kalimantan Utara, empat provinsi Papua) tidak digabung ke provinsi induk; `9999` memisahkan total nasional agar tidak terjumlah ganda. |
| `nama_wilayah` | string | — | tidak | 41 ejaan untuk 39 kode. Ejaan ganda hanya alias resmi: `DI YOGYAKARTA`/`DAERAH ISTIMEWA YOGYAKARTA` (3400) dan `PAPUA`/`P A P U A` (9100). `9999` = `INDONESIA` | Kolom `Provinsi`/`Nama Provinsi`/`Nama Wilayah` mentah, dinormalisasi dengan `_norm` (huruf besar, spasi dirapatkan); K-001/K-002 | Arti: nama wilayah sebagaimana tertulis di sumber. Nama tidak dipakai sebagai kunci; kunci tetap `wilayah_kode`. Perbedaan ejaan dicatat di `reports/validasi.md` (R08). |
| `periode` | string | tahun `YYYY` | tidak | 2009–2025 (17 nilai); semua 4 digit | Kolom `tahun`, nama berkas, atau nama resource di pembaca ekstraksi; K-005, K-016 | Arti: tahun observasi. Tidak ada agregasi semester/triwulan/bulan ke tahun; Silver hanya memuat tabel tahunan. Baris 2009 hanya berasal dari WDI. |
| `jenis_periode` | string | `tahun` | tidak | hanya `tahun` | Ditetapkan di `src/silver/__init__.py`; K-016 | Arti: granularitas periode. Seluruh sumber yang dipakai sudah tahunan, sehingga tidak ada nilai `semester`, `triwulan`, atau `bulan` di Silver. |
| `rincian` | string | — | tidak | `total` + 9 kode: `banjir`, `cuaca_ekstrem`, `erupsi_gunung_api`, `gelombang_pasang_dan_abrasi`, `gempabumi`, `kebakaran_hutan_dan_lahan`, `kekeringan`, `tanah_longsor`, `tsunami` | Peta eksplisit `BENCANA` di `src/silver/__init__.py`; melt kolom bencana pada JSON; K-008, K-020 | Arti: rincian jenis bencana. `total` = baris rekap seluruh jenis bencana. Ejaan sumber diseragamkan (mis. `GEMPA BUMI`/`GEMPABUMI` → `gempabumi`, `LETUSAN GUNUNG API`/`ERUPSI GUNUNG API` → `erupsi_gunung_api`). |
| `nilai` | float (`float64`) | mengikuti `satuan` | tidak | 0–284.438.800; tidak ada nilai negatif/NaN/inf. Untuk `jiwa`/`kejadian` nilai bulat (toleransi 1e-6 untuk noise float) | Nilai mentah XLSX/JSON/WDI yang dikonversi numerik; tidak dipotong/di-outlier-kan; K-011, K-012, K-018 | Arti: nilai observasi. Nilai ekstrem dipertahankan apa adanya (mis. Aceh banjir 2025 mengungsi 947.224 jiwa); pembersihan outlier bukan wewenang Silver. Batas wajar per satuan diperiksa R06. |
| `satuan` | string | `jiwa`, `kejadian`, `per_100000_penduduk`, `persen_penduduk` | tidak | 4 nilai; tiap seri hanya satu satuan | Peta `SATUAN` (`src/silver/__init__.py`) dan `docs/katalog-seri.csv`; K-011, K-017, K-018 | Arti: satuan `nilai`. `jiwa` = orang; `kejadian` = jumlah peristiwa; `per_100000_penduduk` = rasio per 100.000 penduduk (tidak aditif antarwilayah); `persen_penduduk` = persen penduduk (WDI). |
| `_berkas_raw` | string | path relatif terhadap `data/raw/` | tidak | 24 berkas: 11 XLSX BNPB, 12 JSON BNPB, 1 WDI | Dibentuk pembaca `src/ekstraksi/*` dengan `path.relative_to("data/raw").as_posix()` | Arti: berkas mentah asal baris. Contoh: `bnpb/2026-10-20/tangan/data-bencana/0c165adc-...-tahun-2021-per-provinsi.xlsx`. Untuk membuka: `data/raw/` + nilai kolom ini. |
| `_sha256_raw` | string | 64 karakter heksadesimal | tidak | 64 hex; setiap berkas hanya punya satu hash dan cocok dengan `data/raw/MANIFEST.csv` | `src.common.manifest.sha256_raw(berkas)`, tidak ditulis tangan; README aturan lineage | Arti: sidik SHA-256 berkas mentah untuk membuktikan baris tidak diubah setelah ekstraksi. Diperiksa R11 dan `python -m src.common.skema`. |

### Contoh penelusuran satu baris Silver ke berkas mentah

Ambil baris Aceh, kejadian banjir 2021:

| Kolom | Nilai |
|---|---|
| `sumber` | `bnpb_xlsx` |
| `seri_kode` | `kejadian` |
| `wilayah_kode` | `1100` (Aceh) |
| `periode` | `2021` |
| `rincian` | `banjir` |
| `nilai` | `100` |
| `satuan` | `kejadian` |
| `_berkas_raw` | `bnpb/2026-10-20/tangan/data-bencana/0c165adc-5be2-489d-8b1a-e90c6715e73e-tabel-jumlah-kejadian-korban-dan-kerusakan-akibat-bencana-tahun-2021-per-provinsi.xlsx` |
| `_sha256_raw` | `e951a1427459df035aaacd3873ce49295422d64debd670b9df8595645db6f963` |

Langkah verifikasi:

```bash
# 1. Ambil baris dan pasangan lineage-nya
python -c "import pandas as pd; d=pd.read_parquet('data/silver/silver.parquet'); m=(d.seri_kode=='kejadian')&(d.wilayah_kode==1100)&(d.periode=='2021')&(d.rincian=='banjir'); print(d.loc[m,['_berkas_raw','_sha256_raw']].to_string(index=False))"

# 2. Hitung ulang sha256 berkas mentah; hasilnya harus sama dengan _sha256_raw
python -c "from src.common.manifest import sha256_raw; print(sha256_raw('bnpb/2026-10-20/tangan/data-bencana/0c165adc-5be2-489d-8b1a-e90c6715e73e-tabel-jumlah-kejadian-korban-dan-kerusakan-akibat-bencana-tahun-2021-per-provinsi.xlsx'))"

# 3. Periksa seluruh pasangan berkas-hash di Silver
python -m src.common.skema data/silver/silver.parquet
```

Berkas mentahnya ada di `data/raw/bnpb/2026-10-20/tangan/data-bencana/…-tahun-2021-per-provinsi.xlsx`,
pada baris Aceh dan kolom `Jumlah Kejadian` untuk `BANJIR`. Dengan cara yang sama, setiap
baris Silver dapat dilacak karena `_berkas_raw` + `_sha256_raw` selalu berpasangan dan
dibentuk otomatis dari `MANIFEST.csv`.

### Rekonsiliasi agregat (tabel pendamping validasi)

| Berkas | Isi |
|---|---|
| `reports/validasi-agregasi-kabupaten.csv` | Jumlah kabupaten/kota yang dijumlahkan untuk setiap baris Silver hasil agregasi 2021–2022 (`n_kabupaten_kota`), nilai kabupaten/kota vs rekap provinsi, dan selisihnya. 1.530 baris agregasi; 21 selisih pada seri `kejadian` dicatat; 76 baris total provinsi berasal dari rekap provinsi, bukan agregasi kab/kota. |
| `reports/validasi-agregat-nasional.csv` | Rekonsiliasi jumlah provinsi vs baris nasional `9999` untuk satuan aditif (`jiwa`, `kejadian`). 157 pasangan dibandingkan; 5 selisih dicatat (4 gempabumi dan 1 jumlah penduduk −200). Seri rasio/persen tidak dijumlahkan karena tidak aditif. |

## data/gold/<tabel>.parquet

Kolom Gold ditambahkan pada Sprint 2–3, setelah tabel panel provinsi × periode × indikator
dan tabel rekonsiliasi pembanding tersedia. Sprint ini baru memvalidasi dan
mendokumentasikan Silver.
