# Laporan tim — KORBAN DEADLINE, kasus 22 Korban bencana

Status: Draf akhir Sprint 1. Angka dapat ditarik ulang dari `data/silver/silver.parquet`, `reports/`, dan `log-keputusan.csv` (id K-001 s.d. K-039).

## Ringkasan

Kasus 22 (Klaster G. Bencana BNPB) berfokus pada data kejadian dan korban bencana tingkat provinsi di Indonesia beserta normalisasinya (SDG 1.5.1, 11.5.1, dan 13.1.1). Dataset mencakup 9 seri utama BNPB (`kejadian`, `korban_meninggal`, `korban_hilang`, `korban_luka_sakit`, `korban_mengungsi`, `korban_terdampak`, `korban_terdampak_mengungsi`, `korban_mengungsi_per_100rb`, `korban_meninggal_hilang_per_100rb`), 1 seri penyebut `jumlah_penduduk` (2025), dan 1 seri pembanding nasional WDI (`EN.CLC.MDAT.ZS`). Tabel Silver pertama berhasil dibangun dengan 7.535 baris dari 11 seri, 39 wilayah (38 provinsi + kode 9999 nasional), dan rentang waktu 2009–2025. Tantangan terbesar data ini adalah format mentah yang sangat kotor (ketiadaan kode seri eksplisit, enam ragam tata letak dalam dua format, sel tergabung/merged cells, rincian kabupaten/kota yang harus diagregasikan ke provinsi, serta observasi berulang antarberkas).

## Data dan lineage

Sebanyak 44 berkas mentah (snapshot 20 Oktober 2026) dengan sidik `data_hash` = `f26ed8682abbbc3496c256c56ac008f22b4bb473cd3ad9a34eb5b2f443a63b2f` diproses, terdiri atas 1 berkas metadata katalog CKAN, 26 berkas DataStore JSON BNPB, 13 berkas XLSX rekapitulasi unduhan tangan, dan 4 berkas WDI (1 data + 3 metadata). Sebanyak 24 berkas sumber masuk ke lapis Silver (7.535 baris), sementara berkas kab/kota dan tabel kerusakan dipisahkan dengan alasan tercatat. Setiap baris Silver membawa lineage terverifikasi melalui kolom `_berkas_raw` dan `_sha256_raw` yang divalidasi langsung terhadap `data/raw/MANIFEST.csv`.

## Masalah data dan penanganannya

Bagian ini merangkum seluruh temuan empiris selama Sprint 1 dari hasil profil data dan pencatatan keputusan wrangling pada `log-keputusan.csv`.

### Tabel Ringkasan Masalah dan Keputusan Wrangling

| Kategori Masalah | Deskripsi dan Bukti | Keputusan Penanganan | Baris Terdampak | Alternatif Ditolak | Log ID |
|---|---|---|---|---|---|
| **Struktur Format** | Berkas mentah tidak memuat kode seri eksplisit; 6 tata letak berbeda (XLSX dan JSON). | Ekstraksi ke format seragam per sel; nama seri diturunkan dari judul *resource* katalog CKAN. | 51.074 baris mentah | Mengisi kode seri manual per berkas | K-003, K-005, K-013 |
| **Penyatuan Wilayah** | Sel 'Provinsi' pada XLSX 2021/2022 berupa *merged cells* bertingkat; ejaan nama antarberkas tidak seragam. | Dilakukan *forward-fill* sel gabungan; pemetaan wilayah menggunakan kode numerik BPS 2 digit $\times$ 100 (susunan 38 provinsi 2025) dan kode 9999 untuk nasional. | 4.494 angka jumlahan | Pemetaan berbasis nama provinsi; interpolasi nama | K-001, K-002, K-003 |
| **Pencegahan Double Count** | Berkas XLSX 2021 dan 2022 memuat rincian kab/kota sekaligus rekap total provinsi. | Baris kab/kota dibuang dari Silver; hanya baris rekap provinsi yang dipertahankan. | -28.924 baris | Menyimpan kab/kota dan rekap provinsi bersamaan | K-006, K-027 |
| **Cakupan Topik Kasus** | Berkas rekap BNPB memuat 17 indikator kerusakan fisik (rumah, kantor, jembatan) bersatuan `unit`. | Seri kerusakan fisik dikeluarkan dari Silver Kasus 22 (fokus hanya pada korban jiwa). | -2.834 baris | Memasukkan seri kerusakan dengan satuan campuran | K-007 |
| **Inkonsistensi Ejaan** | Ejaan jenis bencana tidak konsisten (mis. `GEMPABUMI` vs `GEMPA BUMI`, `ERUPSI` vs `LETUSAN`). | Penyeragaman 3 pasangan ejaan menjadi nama baku kanonik melalui pemetaan kamus eksplisit. | 0 (perubahan nilai) | Regex otomatis atau case folding sederhana | K-008 |
| **Redundansi Resource** | Berkas JSON DataStore 2024 berakhiran `.xlsx` berisi tabel identik sel-per-sel dengan versi tanpa ekstensi. | Resource JSON berakhiran `.xlsx` dibuang dari Silver untuk mencegah duplikasi. | -2.106 baris | Membiarkan kedua resource termuat | K-014 |
| **Perbedaan Antarberkas** | Baris INDONESIA tanah longsor 2024 tertulis 27 di tabel provinsi, padahal jumlah 38 provinsi dan tabel nasional bernilai 207. | Baris nasional (kode 9999) diambil dari tabel nasional kanonik; nilai 207 dipertahankan. | -98 baris | Memakai baris provinsi atau membiarkan selisih | K-010, K-015 |
| **Patahan Wilayah** | Pemekaran Kaltara (2012) dan 4 DOB Papua (2022) menyebabkan jumlah provinsi bergeser (34 vs 38). | Provinsi baru hanya muncul sejak tahun berdirinya; tidak digabung ke provinsi induk dengan asumsi bobot buatan. | 6 provinsi pemekaran | Menggabungkan ke induk dengan estimasi proporsi penduduk | K-001, K-002 |
| **Celah Panel (Missing)** | Grid 38 provinsi $\times$ 16 tahun $\times$ 10 seri = 6.080 sel memiliki 5.472 sel kosong (90,00%). | Sel kosong pada tahun awal (2010–2020) ditetapkan sebagai *structurally missing* (belum terbit); tidak diimputasi. | 5.472 sel kosong | Imputasi statistik (mean/KNN/interpolasi deret) | K-020, K-027, K-035 |
| **Pemisahan Indikator** | Pada tahun-tahun awal (2010–2020), rincian korban meninggal dan hilang tidak terpisah per provinsi. | Struktur asli dipertahankan tanpa pemisahan paksa untuk menghindari fabrikasi data. | 990 baris terbit (2021–2025) | Memisahkan rasio meninggal/hilang secara proporsional | K-028, K-036 |
| **Anomali Ekstrem (Outlier)** | Terdeteksi 1.233 nilai ekstrem melalui IQR 1.5 dan Z-Score $|z| > 3$. | 1.227 outlier diklasifikasikan sebagai Outlier Asli (bencana besar empiris) dan dipertahankan apa adanya. | 1.227 baris | Pemotongan (*trimming*) atau penghapusan outlier | K-012, K-021, K-029, K-037 |
| **Galat Input Numerik** | Ditemukan rasio `korban_mengungsi_per_100rb` tahun 2025 yang melampaui batas wajar di Aceh (16.836,54) dan Malut (2.033,56). | Nilai tidak wajar diklasifikasikan sebagai Galat Input dan diubah menjadi `NaN` di Silver bersih. | -2 baris | Mengisi nilai dengan rata-rata atau membiarkan nilai korup | K-024, K-031, K-039 |
| **Deduplikasi Snapshot** | Berkas BNPB snapshot 17 dan 20 Oktober memuat observasi yang sama. | Nilai identik dipertahankan; perbedaan nilai dicatat sebagai revisi resmi dan dipilah di tahap Gold. | 0 | Menghapus langsung kunci kembar | K-023, K-030, K-038 |
| **Koreksi Satuan & SDG** | Satuan katalog awal kosong atau tidak konsisten; kode SDG belum terpetakan. | Satuan dibakukan (`jiwa`, `kejadian`, `per_100000_penduduk`, WDI `persen_penduduk`); 8 seri korban dipetakan ke SDG 13.1.1\|1.5.1\|11.5.1. | 11 seri | Memakai teks satuan mentah apa adanya | K-011, K-017, K-018, K-019, K-028 |
| **Penetapan Pembanding** | Seri WDI `EN.CLC.MDAT.ZS` hanya memiliki 1 titik observasi (tahun 2009). | Dicatat sebagai nilai rerata tahunan 1990–2009 (0,1605897%); rincian total ditandai sebanding dengan agregat nasional kode 9999. | 1 baris | Memproyeksikan WDI ke deret tahunan 2010–2025 | K-018, K-025, K-026, K-030 |

---

### Uraian Temuan Empiris

#### 1. Celah Panel (*Panel Gaps / Structurally Missing*)
Pengujian kelengkapan panel dilakukan dengan membangun kerangka grid lengkap 38 provinsi $\times$ 16 tahun periode pengamatan (2010–2025) $\times$ 10 seri utama BNPB pada rincian `total`, menghasilkan matriks berukuran **6.080 sel** (`reports/profil/kelengkapan_panel_per_seri.csv`). Dari seluruh sel tersebut, tercatat **5.472 sel kosong (90,00%)** dan **608 sel terisi (10,00%)**:
- Seri `kejadian` memiliki kelengkapan sempurna **100% pada rentang 2010–2024** (38 provinsi $\times$ 15 tahun = 570 observasi provinsi, ditambah baris nasional). Namun, tahun 2025 memiliki kelengkapan 0% di tabel dinamis karena data 2025 baru diterbitkan terpisah dalam rekapitulasi kompilasi.
- Seluruh 9 seri korban jiwa (`korban_meninggal`, `korban_hilang`, `korban_luka_sakit`, `korban_mengungsi`, `korban_terdampak`, dsb.) memiliki kelengkapan **0% pada rentang 2010–2020** untuk tingkat provinsi. Berdasarkan verifikasi metadata katalog CKAN, BNPB memang belum mempublikasikan disagregasi korban per provinsi untuk periode tersebut secara terbuka (hanya angka agregat nasional).
- Sesuai prinsip kerja Capstone, sel kosong ini dikategorikan secara tegas sebagai ***structurally missing* (belum/tidak diterbitkan)**, bukan *missing at random*. Tim memutuskan **tidak melakukan imputasi data** (K-027, K-035) karena imputasi pada fenomena bencana alam berisiko tinggi memalsukan sejarah kebencanaan.

#### 2. Anomali Data dan Klasifikasi Outlier
Distribusi nilai pada data korban bencana sangat menceng (*heavily right-skewed*), didominasi oleh nilai nol atau kecil pada kondisi normal dan melonjak drastis saat terjadi bencana katastropik:
- Pemindaian menggunakan gabungan metode IQR 1.5 dan Z-Score $|z| > 3$ pada skala logaritma mendeteksi **1.233 calon anomali** (`reports/profil/calon_anomali.csv`).
- **Outlier Asli (1.227 baris):** Sebanyak 99,5% anomali merupakan representasi akurat kejadian bencana berskala besar di Indonesia (misal: banjir Aceh 2025 dengan 947.224 korban mengungsi, gempabumi Sulawesi Tengah 2018, dan banjir Jawa Barat). Seluruh nilai ini **dipertahankan secara utuh tanpa pemotongan** (K-012, K-029, K-037).
- **Galat Input (6 baris teridentifikasi, 2 baris ekstrim diperbaiki):** Ditemukan kejanggalan pada seri `korban_mengungsi_per_100rb` tahun 2025 di Provinsi Aceh (nilai 16.836,54) dan Maluku Utara (nilai 2.033,56) pada berkas `31a0d329-...-mengungsi-per-100.000-orang-2025.xlsx`. Nilai ini melebihi ambang batas wajar laju pengungsian per 100 ribu penduduk akibat dugaan salah penempatan pembagi di tabel asal. Kedua baris ini dikoreksi menjadi `NaN` di berkas Silver bersih (`data/silver/silver_clean.parquet`) dengan dampak perubahan **-2 baris** (K-031, K-039).

#### 3. Patahan Seri dan Patahan Wilayah
- **Patahan Metodologis (Seri):** Pengujian pergeseran serentak $\ge 70\%$ provinsi dengan pergeseran magnitudo $>$ median delta historis (K-022) menghasilkan **0 patahan seri** (`reports/profil/calon_patahan.csv` kosong). Definisi indikator operasional korban pada BNPB terpantau konsisten sepanjang periode pengamatan.
- **Patahan Wilayah (Pemekaran Administratif):** Terdapat 6 provinsi yang mengalami patahan historis akibat dinamika pemekaran daerah:
  - Kalimantan Utara (kode `6500`): Terbentuk tahun 2012 dari Kalimantan Timur.
  - Empat Daerah Otonom Baru (DOB) Papua: Papua Selatan (`9300`), Papua Tengah (`9400`), Papua Pegunungan (`9500`), dan Papua Barat Daya (`9600`) yang mekar pada tahun 2022 dari Papua (`9100`) dan Papua Barat (`9200`).
  - Sesuai keputusan K-001 dan K-002, seluruh wilayah dipetakan pada susunan 38 provinsi tahun 2025. Provinsi baru dibiarkan hanya terisi data sejak tahun resminya berdiri, tanpa memaksakan rekonstruksi mundur ke provinsi induk dengan asumsi bobot penduduk yang tidak dapat dipertanggungjawabkan.

#### 4. Duplikasi, Revisi, dan Rekonsiliasi Redundansi
- **Pembersihan Rincian Kabupaten/Kota:** Berkas XLSX 2021 dan 2022 menyertakan data tingkat kab/kota dan rekapitulasi provinsi dalam berkas yang berbeda. Sebanyak **28.924 baris kab/kota dikeluarkan** dari Silver (K-006) guna menghindari bahaya *double counting* saat agregasi wilayah. Sebanyak **1.530 baris hasil agregasi kab/kota** diuji silang terhadap rekap provinsi (R13); 21 selisih tercatat dan diverifikasi sah karena kejadian multi-kabupaten dicatat pada masing-masing kabupaten terdampak.
- **Deduplikasi Berkas Ganda:** Resource JSON dengan ekstensi `.xlsx` pada dataset 2024 yang memiliki isi kembar identik sel-per-sel dibuang, mereduksi **2.106 baris duplikat** (K-014).
- **Koreksi Data Nasional Tanah Longsor 2024:** Pada berkas tabel provinsi tahun 2024, baris `INDONESIA` untuk bencana tanah longsor tertulis bernilai 27, sementara jumlahan 38 provinsi dan dua berkas nasional lainnya menunjukkan angka 207. Melalui keputusan K-015, data nasional kode `9999` dipisahkan dan ditarik dari tabel nasional kanonik (mereduksi 98 baris duplikat nasional yang korup).

#### 5. Koreksi Metadata dan Katalog Seri
- **Satuan Resmi:** Mengoreksi teks satuan awal katalog yang kosong atau rancu. Ditetapkan 4 satuan baku kanonik: `kejadian` (untuk frekuensi), `jiwa` (untuk korban manusia dan penduduk), `per_100000_penduduk` (untuk normalisasi rasio korban), dan `persen_penduduk` (untuk indikator WDI) (K-011, K-017, K-018).
- **Koreksi Seri WDI `EN.CLC.MDAT.ZS`:** Metadata katalog awal tidak mencantumkan satuan dan durasi waktu yang tepat. Melalui inspeksi metadata WDI resmi, indikator ini terbukti merupakan rata-rata tahunan persentase populasi terdampak pada kurun waktu 1990–2009 (bernilai 0,1605897%), sehingga hanya tersedia tepat satu titik data pada tahun 2009 (K-018, K-025, K-030).
- **Harmonisasi Ejaan Jenis Bencana:** Menyatukan diskrepansi ejaan teks kapital pada 3 varian jenis bencana (K-008):
  1. `GEMPA BUMI` dan `GEMPABUMI` $\to$ `gempabumi`
  2. `LETUSAN GUNUNG API` dan `ERUPSI GUNUNG API` $\to$ `erupsi_gunung_api`
  3. `GELOMBANG PASANG / ABRASI` dan `GELOMBANG PASANG DAN ABRASI` $\to$ `gelombang_pasang_dan_abrasi`
- **Keterlacakan URL Metadata:** Sebanyak 11 seri di `docs/katalog-seri.csv` telah dilengkapi tautan resmi langsung ke CKAN BNPB, API WDI, serta pedoman metadata global PBB/UNSD untuk target SDG 1.5.1, 11.5.1, dan 13.1.1 (K-031).

## Integrasi dan rekonsiliasi
Seri utama vs pembanding nasional: selisih, penjelasannya (definisi, metode, vintage, granularitas),
dan hasil analisis revisi dari arsip WDI. Lihat dokumen lengkap di [reports/rekonsiliasi.md](file:///c:/Users/HP/workbench-workspace/capstone-data-wrangling/reports/rekonsiliasi.md) serta tabel nasional periode × seri di `reports/tabel_nasional_periode_seri.csv`. Rancangan basis data SQL Silver terdokumentasi di [reports/penyimpanan.md](file:///c:/Users/HP/workbench-workspace/capstone-data-wrangling/reports/penyimpanan.md).

## Validasi dan reproduksibilitas

Validasi otomatis dijalankan melalui modul `src/validasi/` dan terintegrasi penuh dalam `pipeline.py`:
- **14 dari 14 aturan validasi berhasil lolos** (10 lolos murni, 4 lolos dengan catatan/tabel pendamping resmi: R04 floating-point noise $< 10^{-6}$, R08 alias nama provinsi, R12 kelengkapan parsial kejadian per jenis bencana, R13 selisih agregasi kab/kota, dan R14 rekonsiliasi nasional).
- **Kecepatan Pipeline:** Eksekusi penuh dari data mentah hingga Silver dan validasi (`python pipeline.py`) tuntas dalam waktu **$\pm$ 4,5–5,5 detik** pada CPU laptop biasa (jauh di bawah batas toleransi maksimal 15 menit).
- **Uji Skema:** Lapis Silver lolos tanpa peringatan pada pemeriksa skema resmi: `python -m src.common.skema data/silver/silver.parquet`.

## Pembagian kerja

| Anggota | NIM | Komponen | Tugas Sampingan | Bagian Laporan yang Ditulis |
|---|---|---|---|---|
| Muhammad Razan Maulana Pratama | 124450031 | Transformasi dan panel | Koordinator | Ringkasan, Struktur Silver |
| Charrlindah | 124450037 | Profil dan pembersihan | Profiling | Masalah data dan penanganannya |
| Nazlah Auliya | 124450054 | Validasi dan dokumentasi | Quality Assurance | Validasi dan reproduksibilitas |
| Muhammad Rafka Fatih A | 124450089 | Integrasi, penyimpanan, dan skala | Integrator | Integrasi dan rekonsiliasi |
| Muhammad Harvinsyah | 124450107 | Ekstraksi dan lineage | Data Engineer | Data dan lineage |
| Cika Adelia Br Marbun | 124450128 | Ekstraksi format | Data Engineer | Ekstraksi WDI dan pembaca berkas |
