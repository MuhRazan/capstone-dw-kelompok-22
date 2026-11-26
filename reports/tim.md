# Laporan tim — KORBAN DEADLINE, kasus 22 Korban bencana

Status: Draf akhir Sprint 1. Angka dapat ditarik ulang dari `data/silver/silver.parquet`, `reports/`, dan `log-keputusan.csv` (id K-001 s.d. K-039).

## Ringkasan

Kasus 22 (Klaster G. Bencana BNPB) berfokus pada data kejadian dan korban bencana tingkat provinsi di Indonesia beserta normalisasinya (SDG 1.5.1, 11.5.1, dan 13.1.1). Dataset mencakup 9 seri utama BNPB (`kejadian`, `korban_meninggal`, `korban_hilang`, `korban_luka_sakit`, `korban_mengungsi`, `korban_terdampak`, `korban_terdampak_mengungsi`, `korban_mengungsi_per_100rb`, `korban_meninggal_hilang_per_100rb`), 1 seri penyebut `jumlah_penduduk` (2025), dan 1 seri pembanding nasional WDI (`EN.CLC.MDAT.ZS`). Tabel Silver pertama berhasil dibangun dengan 7.535 baris dari 11 seri, 39 wilayah (38 provinsi + kode 9999 nasional), dan rentang waktu 2009–2025. Tantangan terbesar data ini adalah format mentah yang sangat kotor (ketiadaan kode seri eksplisit, enam ragam tata letak dalam dua format, sel tergabung/merged cells, rincian kabupaten/kota yang harus diagregasikan ke provinsi, serta observasi berulang antarberkas).

## Data dan lineage

Sebanyak 44 berkas mentah (snapshot 20 Oktober 2026) dengan sidik `data_hash` = `f26ed8682abbbc3496c256c56ac008f22b4bb473cd3ad9a34eb5b2f443a63b2f` diproses, terdiri atas 1 berkas metadata katalog CKAN, 26 berkas DataStore JSON BNPB, 13 berkas XLSX rekapitulasi unduhan tangan, dan 4 berkas WDI (1 data + 3 metadata). Sebanyak 24 berkas sumber masuk ke lapis Silver (7.535 baris), sementara berkas kab/kota dan tabel kerusakan dipisahkan dengan alasan tercatat. Setiap baris Silver membawa lineage terverifikasi melalui kolom `_berkas_raw` dan `_sha256_raw` yang divalidasi langsung terhadap `data/raw/MANIFEST.csv`.

### Arsitektur Penyimpanan dan Rancangan Basis Data SQL (Tahap 5)

Sebagai bagian dari Tahap 5, data analitik Kasus 22 dimuat ke dalam basis data relasional SQL (`data/gold/gold.sqlite` dan `data/silver/silver.db`) melalui eksekusi terpadu `python pipeline.py`. DDL skema terdefinisi di `src/gold/skema.sql` yang mencakup 4 tabel utama dengan tipe data dan kunci primer (*primary key*) yang tegas:

1. **Tabel `silver`** (7.535 baris): Data observasi granular 11 kolom wajib.  
   *Kunci Primer:* `(sumber, seri_kode, wilayah_kode, periode, rincian, _berkas_raw)`. Menegakkan keunikan per sel observasi dan berkas sumber (aturan R02).
2. **Tabel `panel_gold`** (3.382 baris): Panel provinsi × periode × indikator format panjang (disertai penanda anomali, status sel, normalisasi per 100 ribu penduduk, dan transformasi `log1p`).  
   *Kunci Primer:* `(wilayah_kode, periode, seri_kode, rincian)`.
3. **Tabel `tabel_nasional`** (90 baris): Baris agregat nasional periode × seri dengan asal angka (`baris_indonesia`, `agregat_provinsi`, `pembanding`) dan silsilah mentah.  
   *Kunci Primer:* `(periode, seri_kode)`.
4. **Tabel `tabel_rekonsiliasi`** (136 baris): Pasangan rekonsiliasi analitik (Pasangan 1 rasio 100rb, Pasangan 2 agregasi kab/kota vs rekap provinsi, dan Pasangan 3 seri utama BNPB vs WDI) beserta selisih dan catatan keterbandingannya.  
   *Kunci Primer:* `(pasangan_id, wilayah_kode, periode, seri_kode, rincian)`.

Verifikasi otomatis pada `pipeline.py` memastikan bahwa **jumlah baris di SQL sama persis (100% cocok) dengan jumlah baris Parquet Silver dan Gold**:
* `silver`: 7.535 baris SQL == 7.535 baris Parquet.
* `panel_gold`: 3.382 baris SQL == 3.382 baris Parquet.
* `tabel_nasional`: 90 baris SQL == 90 baris Parquet.
* `tabel_rekonsiliasi`: 136 baris SQL == 136 baris Parquet.

#### Alasan Pilihan Basis Data SQL (SQLite & DuckDB)
Pemilihan SQLite (dan kompatibilitas DuckDB) didasarkan pada pertimbangan rekayasa data berikut:
1. **Penegakan Skema dan Integritas Kunci (*Schema & PK Enforcement*):** Berbeda dengan format teks longgar, mesin SQL menolak secara otomatis (*fail-fast*) rekaman duplikat atau pelanggaran tipe kolom melalui penegakan *Primary Key* komposit dan batasan `NOT NULL`.
2. **Reproduksibilitas Penuh dan Serverless (*Self-Contained File*):** Basis data beroperasi tanpa *daemon service*, kredensial pengguna, atau ketergantungan port jaringan. Berkas basis data tunggal dapat langsung dieksekusi di lingkungan uji manapun, menjamin keterulangan (*reproducibility*) hasil tim.
3. **Kecepatan Query Agregasi dan Join:** Mendukung indeks B-tree komposit pada `(wilayah_kode, periode)` dan `(seri_kode, periode)` yang mempercepat pemfilteran cross-section/time-series serta join relasional antar-tabel.

#### Perbandingan Singkat: SQL Relasional vs Document-Store (JSON Mentah)

| Dimensi Evaluasi | Basis Data SQL Relasional (Lapis Silver & Gold) | Document-Store / Berkas JSON Mentah (Lapis Bronze) |
|---|---|---|
| **Paradigma Skema** | *Schema-on-write*: struktur kolom baku, tipe data tervalidasi saat penulisan, kunci primer unik wajib. | *Schema-on-read*: struktur dinamis/bersarang (*nested*), tidak ada pembatasan struktur kaku. |
| **Penyimpanan Metadata** | Metadata silsilah (`_berkas_raw`, `_sha256_raw`) terstruktur rapi pada setiap baris observasi. | Menyimpan keseluruhan *payload* HTTP, *response header*, metadata katalog, dan *dictionary* sumber. |
| **Kinerja Query Agregasi** | **Sangat Cepat**: optimasi pemindaian kolom, indeks numerik, dan fungsi agregasi relasional (`GROUP BY`, `SUM`, `AVG`). | **Lambat**: membutuhkan deserialisasi/parsing teks JSON menyeluruh (*tree-traversal*) di memori. |
| **Integritas Observasi** | Mencegah anomali duplikasi baris melalui mekanisme kunci primer basis data. | Rawan duplikasi catatan jika API dipanggil berulang tanpa logika deduplikasi manual di luar berkas. |

#### Mengapa Pendekatan Tersebut Cocok untuk Lapis Tertentu
1. **Lapis Mentah / Bronze (`data/raw/`): Cocok Menggunakan Document-Store / JSON & XLSX Asli.**  
   Menyimpan respons API mentah sebagai dokumen teks JSON/XLSX mempertahankan bukti silsilah autentik (*ground truth auditability*). Pendekatan *schema-on-read* pada lapis ini krusial karena berkas mentah BNPB dan WDI memiliki variasi struktur yang sangat lebar (26 JSON DataStore dengan hierarki berbeda, 13 XLSX dengan variasi *merged cells*, dan WDI multilabel). Memaksakan skema relasional di lapis mentah berisiko memotong atau mengaburkan informasi kontekstual sumber.
2. **Lapis Silver (`data/silver/`): Cocok Menggunakan Tabel Relasional SQL & Parquet Kolumnar.**  
   Pada lapis Silver, seluruh entitas telah dipilah dan dinormalisasi ke dalam skema seragam 11 kolom. Pendekatan relasional dengan *Primary Key* 6 kolom menjamin bahwa seluruh observasi unik, tipe data angka terbebas dari teks non-numerik, dan relasi lineage ke berkas mentah terkunci rapat sebelum data diolah lebih lanjut.
3. **Lapis Gold (`data/gold/`): Cocok Menggunakan SQL Relasional Terindeks & Parquet Analitik.**  
   Lapis Gold ditujukan untuk konsumsi analitis langsung (tabel panel, agregat nasional, dan rekonsiliasi). Format SQL relasional memudahkan pengguna dan peneliti mengeksekusi analisis kuantitatif dengan query SQL standar (`SELECT`, `JOIN`, `WHERE`), sementara berkas Parquet memberikan kompresi efisien dan pemindaian kolom berkecepatan tinggi untuk model ekonometrika.


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

Rekonsiliasi seri utama terhadap pembanding di tingkat nasional (Tahap 6) dijalankan oleh `src/gold/rekonsiliasi.py` terpadu dari `python pipeline.py` dan menghasilkan `data/gold/rekonsiliasi.parquet` (K-049). Terdapat **empat pasangan** yang dikonfigurasi di `src/konfigurasi.py` → `PASANGAN` (P1–P4). Angka di bagian ini dapat ditarik ulang dengan:

```python
import pandas as pd
silver = pd.read_parquet("data/silver/silver.parquet")
nas    = pd.read_parquet("data/gold/nasional.parquet")
rek    = pd.read_parquet("data/gold/rekonsiliasi.parquet")
# Distribusi kategori (P4 = 1 baris di rekonsiliasi.parquet; P1–P3 diverifikasi dari Silver, lihat query di bawah)
print(rek[["pasangan_id","kategori","penjelasan","nilai_utama","asal"]].to_string())
```

> **Catatan:** `rekonsiliasi.parquet` memuat baris yang dihasilkan dari `nasional.parquet`. Karena nasional.parquet menyimpan rincian `total` sementara P1–P3 memerlukan rincian `jenis_bencana=banjir`, P1–P3 tidak menghasilkan baris di rekonsiliasi.parquet dan diverifikasi langsung dari Silver (query di bawah setiap pasangan). P4 menghasilkan 1 baris konteks. Semua angka dapat ditarik ulang secara deterministik.

---

### Pasangan P1 — Mengungsi per 100.000: angka BNPB vs dihitung ulang

**Jenis:** selisih · **Kategori baku:** `metode berbeda` · **Rincian diuji:** `jenis_bencana=banjir`, nasional (kode 9999) · **Konfigurasi:** `src/konfigurasi.py` → `PASANGAN[0]` (P1)

| Sisi | Nilai (2025, banjir, kode 9999) | Sumber yang dapat ditarik ulang |
|---|---|---|
| **Utama** — terbitan BNPB | **392,085749** per 100.000 | `silver` → `seri_kode=korban_mengungsi_per_100rb, wilayah_kode=9999, rincian=banjir, periode=2025` |
| **Pembanding** — dihitung ulang | **392,085749** per 100.000 | 1.115.244 / 284.438.800 × 100.000 |
| **Selisih** | **0,000000** | cocok sempurna |

```python
# Tarik ulang P1 dari Silver
terbit   = silver.query("seri_kode=='korban_mengungsi_per_100rb' and wilayah_kode==9999 and rincian=='banjir' and periode=='2025'")["nilai"].iloc[0]
mengungsi= silver.query("seri_kode=='korban_mengungsi' and wilayah_kode==9999 and rincian=='banjir' and periode=='2025'")["nilai"].iloc[0]
penduduk = nas.query("seri_kode=='jumlah_penduduk'")["nilai"].iloc[0]
hitung   = mengungsi / penduduk * 100_000
print(f"Terbit BNPB : {terbit:.6f}")     # → 392.085749
print(f"Hitung ulang: {hitung:.6f}")     # → 392.085749
print(f"Selisih     : {terbit - hitung:.8f}")  # → 0.00000000
```

**Penjelasan kategori `metode berbeda`:** Angka terbit BNPB dan angka dihitung ulang berasal dari dua berkas yang diterbitkan terpisah (berkas per 100.000 dan berkas jumlah pengungsi). Penyebut keduanya adalah kolom *Jumlah Penduduk* yang sama (publikasi BPS 2025, 284.438.800 jiwa). Selisih nol membuktikan konsistensi internal BNPB. Log: **K-018** (satuan per 100.000), **K-030** (penyebut penduduk).

**Periode pra-2025:** BNPB belum menerbitkan angka per 100.000 untuk 2010–2024, dikategorikan `cakupan berbeda` (K-018).

---

### Pasangan P2 — Meninggal dan hilang per 100.000: angka BNPB vs (meninggal + hilang) / penduduk

**Jenis:** selisih · **Kategori baku:** `metode berbeda` · **Rincian diuji:** `jenis_bencana=banjir`, nasional (kode 9999) · **Konfigurasi:** `src/konfigurasi.py` → `PASANGAN[1]` (P2)

| Sisi | Nilai (2025, banjir, kode 9999) | Sumber yang dapat ditarik ulang |
|---|---|---|
| **Utama** — terbitan BNPB | **0,539659** per 100.000 | `silver` → `seri_kode=korban_meninggal_hilang_per_100rb, wilayah_kode=9999, rincian=banjir, periode=2025` |
| **Pembanding** — dihitung ulang | **0,539659** per 100.000 | (1.353 + 182) / 284.438.800 × 100.000 |
| **Selisih** | **0,000000** | cocok sempurna |

```python
# Tarik ulang P2 dari Silver
terbit    = silver.query("seri_kode=='korban_meninggal_hilang_per_100rb' and wilayah_kode==9999 and rincian=='banjir' and periode=='2025'")["nilai"].iloc[0]
meninggal = silver.query("seri_kode=='korban_meninggal' and wilayah_kode==9999 and rincian=='banjir' and periode=='2025'")["nilai"].iloc[0]
hilang    = silver.query("seri_kode=='korban_hilang' and wilayah_kode==9999 and rincian=='banjir' and periode=='2025'")["nilai"].iloc[0]
penduduk  = nas.query("seri_kode=='jumlah_penduduk'")["nilai"].iloc[0]
hitung    = (meninggal + hilang) / penduduk * 100_000
print(f"Meninggal: {meninggal:.0f}, Hilang: {hilang:.0f}")  # → 1353, 182
print(f"Terbit BNPB : {terbit:.6f}")   # → 0.539659
print(f"Hitung ulang: {hitung:.6f}")   # → 0.539659
print(f"Selisih     : {terbit - hitung:.8f}")  # → 0.00000000
```

**Penjelasan kategori `metode berbeda`:** Angka terbit BNPB dan angka dihitung ulang berasal dari tiga berkas terpisah. Selisih nol membuktikan konsistensi. Catatan: indikator 13.1.1 global mencakup terdampak langsung; seri ini hanya meninggal + hilang. Log: **K-018, K-030**.

---

### Pasangan P3 — Kejadian banjir: baris INDONESIA vs jumlah 38 provinsi

**Jenis:** selisih · **Kategori baku:** `definisi berbeda` · **Rincian diuji:** `jenis_bencana=banjir` · **Konfigurasi:** `src/konfigurasi.py` → `PASANGAN[2]` (P3), `GOLD_AGREGAT`

| Periode | Nasional (kode 9999) | Jumlah 38 provinsi | Selisih | Keterangan |
|---|---|---|---|---|
| 2021 | 1.794 | 1.794 | **0** | `silver`, `wilayah_kode==9999` vs `wilayah_kode!=9999` |
| 2022 | 1.531 | 1.531 | **0** | idem |
| 2024 | 1.420 | 1.420 | **0** | idem |
| 2025 | 2.009 | 2.009 | **0** | idem |
| 2010–2020, 2023 | (ada nasional) | tidak tersedia | — | `cakupan berbeda` |

```python
# Tarik ulang P3 dari Silver
nas_banjir  = (silver.query("seri_kode=='kejadian' and wilayah_kode==9999 and rincian=='banjir'")
               .set_index("periode")["nilai"])
prov_banjir = (silver.query("seri_kode=='kejadian' and wilayah_kode!=9999 and rincian=='banjir'")
               .groupby("periode")["nilai"].sum())
selisih = nas_banjir.subtract(prov_banjir, fill_value=None)
print(selisih[selisih.notna()])
# → 2021: 0.0, 2022: 0.0, 2024: 0.0, 2025: 0.0
```

**Penjelasan kategori `definisi berbeda`:** BNPB mendefinisikan kejadian lintas provinsi dihitung *sekali* secara nasional tetapi di *setiap* provinsi terdampak (Keterangan berkas). Jumlah provinsi bisa ≥ nasional; kebalikannya (provinsi < nasional) adalah anomali. Untuk 4 tahun yang dapat dibandingkan selisih = 0. Log: **K-006** (pemisahan kab/kota), **K-015** (baris nasional per jenis dari tabel nasional kanonik).

---

### Pasangan P4 — Penduduk terdampak kekeringan, banjir, suhu ekstrem (WDI): konteks

**Jenis:** konteks (selisih *tidak* dihitung) · **Kategori baku:** `definisi berbeda` · **Konfigurasi:** `src/konfigurasi.py` → `PASANGAN[3]` (P4)

| Sisi | Nilai | Periode | Satuan | Sumber |
|---|---|---|---|---|
| **Utama** — WDI `EN.CLC.MDAT.ZS` | **0,160590** | 2009 (rata-rata 1990–2009) | % penduduk | `rek` → `rekonsiliasi.parquet`, 1 baris |
| **Pembanding** — BNPB `korban_terdampak` banjir | (tidak ada tahun yang sama) | 2010–2025 | jiwa | `silver` |

```python
# Tarik ulang P4 — satu-satunya baris di rekonsiliasi.parquet
print(rek[["pasangan_id","jenis","seri_utama","periode","nilai_utama","satuan","asal","kategori","penjelasan"]].to_string())
# → P4, konteks, EN.CLC.MDAT.ZS, 2009, 0.16059, persen, hanya_utama, definisi berbeda
# → penjelasan: "periode tidak beririsan: WDI rata-rata 1990–2009, BNPB 2010–2025"

# Verifikasi nilai WDI dari nasional gold
print(nas.query("seri_kode=='EN.CLC.MDAT.ZS'")[["seri_kode","periode","nilai","satuan"]])
# → 0.1605897, persen_penduduk, 2009
```

**Penjelasan kategori `definisi berbeda`:**

1. **Irisan periode: 0 tahun.** WDI `EN.CLC.MDAT.ZS` adalah satu angka rata-rata tahunan 1990–2009 yang diterbitkan pada periode 2009. BNPB mulai mencatat terstruktur dari 2010. Tidak ada tahun yang overlap sehingga selisih tidak dapat dihitung (K-026, K-030, K-041).
2. **Cakupan jenis bencana berbeda.** WDI (CRED EM-DAT) hanya mencakup tiga jenis: kekeringan, banjir, suhu ekstrem. BNPB mencakup sembilan jenis termasuk gempa bumi, tsunami, dan erupsi gunung api.
3. **Satuan berbeda.** WDI dalam `% penduduk`; BNPB dalam `jiwa`. Konversi memerlukan penyebut penduduk yang hanya tersedia untuk 2025.
4. **Konteks kualitatif.** Nilai WDI 0,16% (baseline historis 1990–2009) sebanding secara kualitatif dengan tren BNPB 2010–2025 — konsisten dengan membaiknya pelaporan daerah dan meningkatnya intensitas cuaca ekstrem.

---

### Ringkasan distribusi kategori seluruh pasangan

| Pasangan | Jenis | Kategori | Periode yang diuji | Selisih |
|---|---|---|---|---|
| P1 | selisih | `metode berbeda` | 2025 (banjir, nasional) | **0,000000** (cocok sempurna) |
| P1 | selisih | `cakupan berbeda` | 2010–2024 | — (rasio tidak diterbitkan) |
| P2 | selisih | `metode berbeda` | 2025 (banjir, nasional) | **0,000000** (cocok sempurna) |
| P2 | selisih | `cakupan berbeda` | 2010–2024 | — (rasio tidak diterbitkan) |
| P3 | selisih | `tidak berselisih` | 2021, 2022, 2024, 2025 | **0** untuk semua 4 tahun |
| P3 | selisih | `cakupan berbeda` | 2010–2020, 2023 | — (prov per jenis tidak tersedia) |
| P4 | konteks | `definisi berbeda` | 2009 (WDI rata-rata 1990–2009) | tidak dihitung (konteks) |

**Rujukan lengkap log keputusan:**

| Angka / Klaim | Sumber | Kunci |
|---|---|---|
| Nilai WDI 2009 = 0,160590% | `data/gold/nasional.parquet` atau `data/gold/rekonsiliasi.parquet` | `seri_kode=EN.CLC.MDAT.ZS` |
| Mengungsi banjir nasional 2025 = 1.115.244 jiwa | `data/silver/silver.parquet` | `seri_kode=korban_mengungsi, wilayah_kode=9999, rincian=banjir, periode=2025` |
| Meninggal banjir nasional 2025 = 1.353 jiwa | `data/silver/silver.parquet` | `seri_kode=korban_meninggal, wilayah_kode=9999, rincian=banjir, periode=2025` |
| Hilang banjir nasional 2025 = 182 jiwa | `data/silver/silver.parquet` | `seri_kode=korban_hilang, wilayah_kode=9999, rincian=banjir, periode=2025` |
| Penduduk 2025 = 284.438.800 jiwa | `data/gold/nasional.parquet` | `seri_kode=jumlah_penduduk` |
| P3 selisih = 0 untuk 2021/2022/2024/2025 | `data/silver/silver.parquet` | `seri_kode=kejadian, rincian=banjir` → groupby periode |
| Penghitungan pasangan | `log-keputusan.csv` | K-018, K-025, K-026, K-030, K-041, K-049 |
| Pemisahan kab/kota | `log-keputusan.csv` | K-006, K-015 |


## Validasi dan reproduksibilitas

Validasi otomatis dijalankan melalui modul `src/validasi/` dan terintegrasi penuh sebagai tahap ke-8 dalam `pipeline.py`:

### 1. Ringkasan Eksekutif Validasi
- **24 dari 24 aturan validasi berhasil dievaluasi dan lolos:**
  - **19 aturan lolos murni** tanpa deviasi (*zero violations*).
  - **5 aturan lolos dengan catatan resmi** (toleransi numerik dan anomali empiris berkas mentah yang telah ditangani dan dicatat di `log-keputusan.csv`).
  - **0 aturan gagal kritis** (*zero hard failures*).
- **Kecepatan Pipeline:** Eksekusi penuh dari data mentah hingga Silver, Gold, dan validasi (`python pipeline.py`) tuntas dalam waktu **$\pm$ 5–7 detik** pada CPU laptop biasa (jauh di bawah batas toleransi maksimal 15 menit).
- **Uji Skema:** Lapis Silver lolos tanpa peringatan pada pemeriksa skema resmi: `python -m src.common.skema data/silver/silver.parquet` (7.535 baris, 11 seri, 39 wilayah, 24 berkas).

### 2. Ringkasan Hasil Aktual 24 Aturan Validasi

| ID | Nama Aturan | Lapis | Jenis | Status Aktual | Baris Terdampak | Ringkasan Temuan Aktual |
|---|---|---|---|---|---|---|
| **R01** | Skema kolom Silver | Silver | Keras | `LOLOS` | 0 | 11 kolom wajib lengkap, 100% tanpa sel kosong |
| **R02** | Keunikan kunci Silver | Silver | Keras | `LOLOS` | 0 | 6 kolom kunci unik untuk seluruh 7.535 baris |
| **R03** | Nilai tidak negatif dan berhingga | Silver | Keras | `LOLOS` | 0 | Nilai minimum 0.00; tidak ada nilai negatif atau inf |
| **R04** | Bilangan bulat untuk jiwa/kejadian | Silver | Peringatan | `LOLOS_DENGAN_CATATAN` | 0 | 6.832 baris jiwa/kejadian; 10 baris ber-noise float $< 10^{-6}$ (bukan pelanggaran) |
| **R05** | Konsistensi satuan per seri | Silver | Keras | `LOLOS` | 0 | 11 seri memakai tepat satu satuan baku sesuai peta SATUAN |
| **R06** | Rentang nilai masuk akal per satuan | Silver | Keras | `LOLOS` | 0 | Jiwa 0–284 jt; kejadian 0–4.727; per 100rb 0–16.836; persen 0,16% |
| **R07** | Kode wilayah sah | Silver | Keras | `LOLOS` | 0 | 39 kode wilayah sah: 38 provinsi BPS × 100 + 9999 nasional |
| **R08** | Konsistensi nama wilayah | Silver | Peringatan | `LOLOS_DENGAN_CATATAN` | 0 | 41 ejaan unik untuk 39 kode; ejaan ganda hanya alias resmi kementerian |
| **R09** | Periode dan jenis periode | Silver | Keras | `LOLOS` | 0 | Seluruh 7.535 baris bertipe tahun, 2009–2025 |
| **R10** | Rincian jenis bencana dikenal | Silver | Keras | `LOLOS` | 0 | 10 nilai sah: total + 9 jenis bencana standar BNPB |
| **R11** | Lineage berkas mentah | Silver | Keras | `LOLOS` | 0 | 24 berkas sumber cocok 100% dengan MANIFEST.csv |
| **R12** | Kelengkapan wilayah per seri/periode | Silver | Peringatan | `LOLOS_DENGAN_CATATAN` | 1.692 | 134 grup lengkap 38 provinsi; 88 grup parsial bencana lokal dicatat |
| **R13** | Agregat kabupaten/kota ke provinsi | Silver | Peringatan | `LOLOS_DENGAN_CATATAN` | 21 | 1.530 baris agregasi kab/kota; 21 selisih kejadian dicatat |
| **R14** | Agregat provinsi ke nasional | Silver | Peringatan | `LOLOS_DENGAN_CATATAN` | 5 | 157 pasangan aditif dibandingkan; 5 selisih dicatat; rasio dipisahkan |
| **R15** | Kunci panel Gold unik | Gold Panel | Keras | `LOLOS` | 0 | Kombinasi indikator + wilayah_kode + periode tidak kembar |
| **R16** | Satu satuan per indikator Gold | Gold Panel | Keras | `LOLOS` | 0 | Setiap indikator panel hanya memiliki satu satuan ukuran |
| **R17** | Status sel dan nilai Gold | Gold Panel | Keras | `LOLOS` | 0 | Status sel baku (terisi, missing, tidak_diterbitkan, belum_ada) |
| **R18** | Sel Gold tertelusur ke Silver | Gold Panel | Keras | `LOLOS` | 0 | Setiap sel terisi memiliki baris Silver asal yang identik |
| **R19** | Nilai Gold sama dengan Silver | Gold Panel | Keras | `LOLOS` | 0 | Nilai panel sama persis dengan nilai Silver (tidak ada mutasi angka) |
| **R20** | Tabel nasional unik | Gold Panel | Keras | `LOLOS` | 0 | Kombinasi seri + rincian + periode tidak kembar |
| **R21** | Kategori rekonsiliasi baku | Rekonsiliasi | Keras | `LOLOS` | 0 | Kategori dari daftar baku; narasi penjelasan tidak kosong |
| **R22** | Selisih konsisten | Rekonsiliasi | Keras | `LOLOS` | 0 | Nilai selisih = nilai_utama − nilai_pembanding terverifikasi |
| **R23** | Baris berpasangan dihitung | Rekonsiliasi | Keras | `LOLOS` | 0 | Seluruh baris berpasangan yang ada nilainya memiliki selisih |
| **R24** | Periode utama tidak dibuang | Rekonsiliasi | Keras | `LOLOS` | 0 | Seluruh tahun observasi seri utama tetap tampil di rekonsiliasi |

### 3. Rincian Catatan Validasi dan Tindak Lanjut Penanganannya
1. **R04 (Floating-point noise):** 10 baris observasi Excel memiliki noise float $< 10^{-6}$. *Tindak lanjut:* Dibulatkan dengan `round()` sesuai keputusan **K-010**.
2. **R08 (Variasi nama provinsi):** 41 ejaan untuk 39 wilayah. *Tindak lanjut:* Dinormalisasi ke kode numerik resmi BPS 2 digit × 100 melalui `src/wilayah.py`, dicatat di **K-001** dan **K-002**.
3. **R12 (Kelengkapan wilayah per rincian bencana):** 88 grup parsial (1.692 sel kosong pada grid). *Tindak lanjut:* Tidak diimputasi buatan karena bencana spesifik wilayah; di Gold diberi status sel `tidak_diterbitkan` atau `belum_ada` (**K-020** dan **K-045**).
4. **R13 & R14 (Selisih agregasi kejadian 2021/2022):** Terdapat selisih +49 kejadian (2021) dan +51 kejadian (2022) pada jumlahan kab/kota vs provinsi. *Tindak lanjut:* Diklasifikasikan sebagai `vintage berbeda` (*cut-off* sistem pelaporan daerah vs rilis provinsi), dicatat di `reports/validasi-agregasi-kabupaten.csv` dan **K-049**.
5. **Mekanisme Aturan Gagal (Fail-Fast):** Seluruh aturan keras menerapkan *fail-fast*. Apabila ada 1 baris melanggar (misalnya kunci panel ganda atau nilai negatif), pipeline langsung menghentikan proses (`sys.exit`) dan mencatat pelanggaran di `reports/validasi.md`. Pada eksekusi data tim saat ini: `aturan_gagal = 0`.

Laporan lengkap hasil validasi terdokumentasi di [reports/validasi.md](file:///c:/Users/HP/workbench-workspace/capstone-data-wrangling/reports/validasi.md).

## Pembagian kerja

| Anggota | NIM | Komponen | Tugas Sampingan | Bagian Laporan yang Ditulis |
|---|---|---|---|---|
| Muhammad Razan Maulana Pratama | 124450031 | Transformasi dan panel | Koordinator | Ringkasan, Struktur Silver |
| Charrlindah | 124450037 | Profil dan pembersihan | Profiling | Masalah data dan penanganannya |
| Nazlah Auliya | 124450054 | Validasi dan dokumentasi | Quality Assurance | Validasi dan reproduksibilitas |
| Muhammad Rafka Fatih A | 124450089 | Integrasi, penyimpanan, dan skala | Integrator | Integrasi dan rekonsiliasi |
| Muhammad Harvinsyah | 124450107 | Ekstraksi dan lineage | Data Engineer | Data dan lineage |
| Cika Adelia Br Marbun | 124450128 | Ekstraksi format | Data Engineer | Ekstraksi WDI dan pembaca berkas |
