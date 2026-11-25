# Laporan Integrasi dan Rekonsiliasi (Tahap 6 — Kasus 22: Korban Bencana)

Dokumen ini memuat tabel nasional periode × seri dan daftar pasangan rekonsiliasi untuk Kasus 22 (Korban Bencana, BNPB & WDI) sebagai persiapan Tahap 6 (Sprint 2).

---

## 1. Tabel Nasional (Periode × Seri)

Tabel nasional mengintegrasikan baris agregat nasional dari seri utama BNPB dan seri pembanding WDI (`EN.CLC.MDAT.ZS`). Berkas tersimpan dalam format:
- **Tabel Panjang Gold (satu baris per periode × seri)**: `data/gold/tabel_nasional.parquet` dan `data/gold/tabel_nasional.csv` (memuat kolom `asal`, `aturan_agregat`, dan `_berkas_raw`).
- **Tabel Lebar Gold (periode × seri)**: `data/gold/tabel_nasional_periode_seri.parquet` dan `data/gold/tabel_nasional_periode_seri.csv`.
- **Salinan Laporan**: `reports/tabel_nasional_periode_seri.csv`.

Skrip pembentuk tabel: `python -m src.gold.tabel_nasional` (dieksekusi otomatis oleh `python pipeline.py`).

### Ringkasan Nilai Nasional Per Tahun
| Periode | Kejadian | Meninggal | Hilang | Luka/Sakit | Mengungsi | Terdampak | Terdampak-Mengungsi | Mengungsi / 100rb | Meninggal+Hilang / 100rb | Penduduk | WDI EN.CLC.MDAT.ZS (%) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **2009** | — | — | — | — | — | — | — | — | — | — | 0,16059 |
| **2010** | 1.945 | — | 277 | 35.730 | 892.261 | 770.842 | — | — | — | — | — |
| **2011** | 1.619 | — | 69 | 692 | 228.696 | 246.833 | — | — | — | — | — |
| **2012** | 1.780 | — | 38 | 1.198 | 135.483 | 818.758 | — | — | — | — | — |
| **2013** | 1.666 | — | 44 | 3.410 | 507.183 | 3.385.803 | — | — | — | — | — |
| **2014** | 1.961 | — | 72 | 2.104 | 860.615 | 1.953.650 | — | — | — | — | — |
| **2015** | 1.694 | — | 57 | 370 | 184.254 | 1.043.675 | — | — | — | — | — |
| **2016** | 2.306 | — | 96 | 2.675 | 438.925 | 2.723.566 | — | — | — | — | — |
| **2017** | 2.866 | — | 69 | 1.042 | 324.996 | 3.349.373 | — | — | — | — | — |
| **2018** | 3.397 | — | 725 | 21.171 | 852.369 | 9.524.726 | — | — | — | — | — |
| **2019** | 3.814 | — | 111 | 3.421 | 436.234 | 5.693.171 | — | — | — | — | — |
| **2020** | 4.649 | — | 42 | 619 | 922.367 | 5.873.967 | — | — | — | — | — |
| **2021** | 5.402 | 728* | 87 | 14.915 | 684.215 | 7.581.247 | 8.265.462* | — | — | — | — |
| **2022** | 3.544 | 858* | 37 | 8.733 | 595.422 | 5.492.456 | 6.087.878* | — | — | — | — |
| **2023** | 5.400 | — | 33 | 5.795 | 150.469 | 8.340.819 | — | — | — | — | — |
| **2024** | 3.472 | 540 | 63 | 11.531 | 528.513 | 7.607.758 | — | — | — | — | — |
| **2025** | 4.727 | 1.666 | 214 | 6.799 | 1.154.803 | 10.955.315 | — | 405,99349 | 0,66095 | 284.438.800 | — |

*\*Catatan Asal Angka:*
- Angka bertanda asterisk (`*`) diperoleh dari **`agregat_provinsi`** (penjumlahan aditif seluruh 34 provinsi dengan bobot 1 per provinsi) karena BNPB tidak menerbitkan baris nasional `INDONESIA` pada berkas rekap 2021 dan 2022.
- Angka lainnya berasal dari **`baris_indonesia`** (diterbitkan langsung oleh BNPB untuk wilayah nasional) atau **`pembanding`** (WDI Bank Dunia).
- Seri rasio per 100.000 penduduk dan `jumlah_penduduk` sebelum 2025 tidak memiliki padanan nasional karena rasio memerlukan pembobotan populasi dan data penduduk tidak diterbitkan BNPB pada 2010–2024.

---

## 2. Daftar Pasangan Rekonsiliasi dan Catatan Keterbandingan

Sesuai panduan kelompok Bagian 3, terdapat **3 pasangan rekonsiliasi** pada Kasus 22:

### Pasangan 1: Angka Rasio per 100 Ribu Penduduk (Hitungan Kelompok vs Terbitan BNPB)
* **Seri yang dibandingkan:**
  1. `korban_mengungsi_per_100rb`: Hitungan $\left(\frac{\text{korban\_mengungsi}}{\text{jumlah\_penduduk}} \times 100.000\right)$ vs Nilai Terbitan BNPB.
  2. `korban_meninggal_hilang_per_100rb`: Hitungan $\left(\frac{\text{korban\_meninggal} + \text{korban\_hilang}}{\text{jumlah\_penduduk}} \times 100.000\right)$ vs Nilai Terbitan BNPB.
* **Periode yang tersedia:** Tahun **2025** (1 periode beririsan).
* **Rincian yang dipakai:** Total nasional dan 9 rincian jenis bencana.
* **Hasil Rekonsiliasi:**
  * Nasional Mengungsi / 100rb:
    $$\frac{1.154.803}{284.438.800} \times 100.000 = 405,993486$$
    Jumlah 9 rincian bencana BNPB $= 405,993486$. **Selisih: 0,000000 (identik)**.
  * Nasional Meninggal & Hilang / 100rb:
    $$\frac{1.666 + 214}{284.438.800} \times 100.000 = \frac{1.880}{284.438.800} \times 100.000 = 0,660951$$
    Jumlah 9 rincian bencana BNPB $= 0,660951$. **Selisih: 0,000000 (identik)**.
* **Catatan Keterbandingan:**
  Metode perhitungan kelompok dan angka terbitan resmi BNPB sepenuhnya konsisten. Angka rasio BNPB dihitung menggunakan penyebut jumlah penduduk resmi BPS 2025 (284.438.800 jiwa).

---

### Pasangan 2: Agregasi Tingkat Kabupaten/Kota vs Rekapitulasi Tingkat Provinsi BNPB
* **Seri yang dibandingkan:** Seluruh seri kejadian dan dampak bencana pada berkas rekapitulasi tahun 2021 dan 2022.
* **Periode yang tersedia:** Tahun **2021** dan **2022** (2 periode beririsan).
* **Rincian yang dipakai:** 1.530 pasangan observasi per provinsi × periode × bencana.
* **Hasil Rekonsiliasi:**
  Diaudit secara sistematis dalam `reports/validasi-agregasi-kabupaten.csv`. Dari 1.530 baris agregasi:
  * 1.509 baris (98,6%) cocok sempurna antara jumlah kab/kota dengan rekap provinsi.
  * 21 baris selisih tercatat dan terdokumentasi (misal selisih kecil pada korban luka-luka di beberapa kabupaten pemekaran).
* **Catatan Keterbandingan:**
  Perbedaan timbul karena berkas rekapitulasi provinsi diperbarui lebih awal oleh Pusdatinkom BNPB sebelum seluruh laporan BPBD kabupaten/kota terhimpun secara lengkap di sistem daerah. Oleh karena itu, di lapis Silver diputuskan memakai tabel provinsi sebagai acuan kanonik (Log K-006).

---

### Pasangan 3: Seri Utama BNPB vs Seri Pembanding WDI (`EN.CLC.MDAT.ZS`)
* **Seri yang dibandingkan:**
  * Seri Utama BNPB: `korban_terdampak`, `korban_mengungsi`, dan indikator SDG 13.1.1/1.5.1/11.5.1.
  * Seri Pembanding WDI: `EN.CLC.MDAT.ZS` (*Droughts, floods, extreme temperatures % of population, average 1990-2009*).
* **Periode yang tersedia:**
  * WDI: Tahun **2009** (1 titik data, rata-rata tahunan 1990–2009).
  * BNPB: Tahun **2010 s.d. 2025**.
  * **Periode beririsan langsung:** **0 tahun** (karena WDI berakhir pada snapshot historis 2009, sementara pencatatan terstruktur BNPB dimulai tahun 2010).
* **Rincian yang dipakai:** Rincian `total` (agregat nasional).
* **Hasil Rekonsiliasi & Konteks Paparan Bencana Nasional:**
  * Nilai WDI 2009 adalah **0,16059% penduduk** terpapar bencana iklim/cuaca ekstrem per tahun (rata-rata 1990–2009).
  * Sebagai perbandingan, pada tahun 2025 di data BNPB:
    $$\text{Persentase Terdampak BNPB 2025} = \frac{10.955.315}{284.438.800} \times 100\% = 3,85\%$$
    $$\text{Persentase Mengungsi BNPB 2025} = \frac{1.154.803}{284.438.800} \times 100\% = 0,41\%$$
* **Catatan Keterbandingan:**
  * **Definisi:** WDI mengukur persentase populasi yang terdampak langsung oleh kekeringan, banjir, dan suhu ekstrem (*EM-DAT CRED definition*). BNPB mencatat korban bencana hidrometeorologi dan geologi di Indonesia.
  * **Vintage & Waktu:** Indikator WDI mewakili *long-term baseline* pra-2010 (era sebelum UU Penanggulangan Bencana No. 24/2007 terimplementasi penuh). Angka 0,16% WDI menjadi patokan historis bahwa dampak bencana hidrometeorologi meningkat signifikan pada dekade 2010–2025 seiring membaiknya pelaporan bencana daerah dan meningkatnya intensitas cuaca ekstrem.

---

## 3. Metrik Ringkasan Rekonsiliasi (Artefak Workbench)

* **Jumlah pasangan rekonsiliasi (`pasangan_rekonsiliasi`):** `3`
* **Jumlah periode beririsan langsung seri pembanding WDI (`periode_beririsan`):** `0`  
  *(Catatan: WDI hanya 1 titik tahun 2009 sementara seri BNPB dimulai 2010, sehingga irisan tahun langsung = 0. Jika dihitung seluruh tahun yang memiliki rekonsiliasi internal kelompok antar-pasangan, yaitu 2021, 2022, dan 2025, terdapat 3 periode).*
