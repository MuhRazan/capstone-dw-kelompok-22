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
4. **Tabel `tabel_rekonsiliasi`** (1.553 baris): Pasangan rekonsiliasi analitik (Pasangan 1 rasio 100rb, Pasangan 2 agregasi kab/kota vs rekap provinsi, dan Pasangan 3 seri utama BNPB vs WDI) beserta selisih dan catatan keterbandingannya.  
   *Kunci Primer:* `(pasangan_id, wilayah_kode, periode, seri_kode, rincian)`.

Verifikasi otomatis pada `pipeline.py` memastikan bahwa **jumlah baris di SQL sama persis (100% cocok) dengan jumlah baris Parquet Silver dan Gold**:
* `silver`: 7.535 baris SQL == 7.535 baris Parquet.
* `panel_gold`: 3.382 baris SQL == 3.382 baris Parquet.
* `tabel_nasional`: 90 baris SQL == 90 baris Parquet.
* `tabel_rekonsiliasi`: 1.553 baris SQL == 1.553 baris Parquet.

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

Integrasi dan rekonsiliasi seri utama terhadap seri pembanding di tingkat nasional (Tahap 6) diwujudkan melalui pembentukan tabel analitik `data/gold/tabel_rekonsiliasi.parquet` (dan salinan CSV di `data/gold/tabel_rekonsiliasi.csv` serta tabel SQL `tabel_rekonsiliasi` di `data/gold/gold.sqlite`). Tabel ini dibentuk otomatis oleh `src/gold/rekonsiliasi.py` dan dijalankan terpadu dari `python pipeline.py` (K-049).

Struktur tabel mencakup 136 baris observasi yang memasangkan seri utama terhadap seri pembanding di seluruh 17 periode (2009 s.d. 2025) untuk 3 pasangan rekonsiliasi mandat panduan kelompok (17 periode × 8 seri indikator). Seluruh periode tanpa pasangan tetap ditampilkan dengan nilai null (*outer join*), dan selisih numerik dihitung apa adanya tanpa manipulasi buatan ($\text{nilai\_seri\_utama} - \text{nilai\_pembanding}$).

### 1. Rincian Tiga Pasangan yang Dibandingkan dan Besar Selisih

#### Pasangan 1: Rasio per 100 Ribu Penduduk (Hitungan Kelompok vs Terbitan Resmi BNPB 2025)
* **Pasangan ID:** `P1_RASIO_100RB`
* **Seri yang Dibandingkan:**
  1. `korban_mengungsi_per_100rb`: Rasio pengungsi per 100 ribu penduduk.
     * *Formula Hitungan Kelompok:* $\frac{\text{korban\_mengungsi}}{\text{jumlah\_penduduk}} \times 100.000 = \frac{1.154.803}{284.438.800} \times 100.000 = \mathbf{405,993486}$.
     * *Terbitan Resmi BNPB:* $\mathbf{405,993486}$ (berkas `jumlah-korban-mengungsi-per-100.000-orang-...-2025.xlsx`).
     * *Besar Selisih:* **0,000000** (selisih nol sempurna).
     * *Kategori Penjelasan:* **metode berbeda** (memvalidasi bahwa formula agregasi kelompok identik sempurna dengan standar terbitan Pusdatinkom BNPB).
  2. `korban_meninggal_hilang_per_100rb`: Rasio gabungan korban meninggal dan hilang per 100 ribu penduduk.
     * *Formula Hitungan Kelompok:* $\frac{\text{korban\_meninggal} + \text{korban\_hilang}}{\text{jumlah\_penduduk}} \times 100.000 = \frac{1.666 + 214}{284.438.800} \times 100.000 = \frac{1.880}{284.438.800} \times 100.000 = \mathbf{0,660951}$.
     * *Terbitan Resmi BNPB:* $\mathbf{0,660951}$ (berkas `jumlah-korban-meninggal-dan-hilang-per-100.000-orang-...-2025.xlsx`).
     * *Besar Selisih:* **0,000000** (selisih nol sempurna).
     * *Kategori Penjelasan:* **metode berbeda** (prosedur penjumlahan pembilang dua berkas terpisah terbukti konsisten).
* **Periode pra-2025 (2009–2024, 32 baris):**
  * *Nilai Utama & Pembanding:* `null` (BNPB belum menerbitkan penyebut populasi resmi maupun rasio per 100 ribu penduduk pra-2025, K-018).
  * *Kategori Penjelasan:* **cakupan berbeda** (ketiadaan indikator pada rentang tahun tersebut).

#### Pasangan 2: Agregasi Tingkat Kabupaten/Kota vs Rekapitulasi Tingkat Provinsi BNPB (2021 & 2022)
* **Pasangan ID:** `P2_KAB_VS_PROVINSI`
* **Seri yang Dibandingkan:** 5 seri indikator bencana aditif (`korban_meninggal`, `korban_hilang`, `korban_luka_sakit`, `korban_terdampak_mengungsi`, dan `kejadian`).
* **Ketersediaan Periode Beririsan Langsung:** Tahun **2021** dan **2022** (2 periode).
* **Evaluasi Angka dan Besar Selisih:**
  * **Tahun 2021:**
    - `korban_meninggal`: Agregasi Kab/Kota = 728 vs Rekap Provinsi = 728 $\implies$ **Selisih = 0** (**metode berbeda**).
    - `korban_hilang`: Agregasi Kab/Kota = 87 vs Rekap Provinsi = 87 $\implies$ **Selisih = 0** (**metode berbeda**).
    - `korban_luka_sakit`: Agregasi Kab/Kota = 14.915 vs Rekap Provinsi = 14.915 $\implies$ **Selisih = 0** (**metode berbeda**).
    - `korban_terdampak_mengungsi`: Agregasi Kab/Kota = 8.265.462 vs Rekap Provinsi = 8.265.462 $\implies$ **Selisih = 0** (**metode berbeda**).
    - `kejadian`: Agregasi Kab/Kota = 5.451 vs Rekap Provinsi = 5.402 $\implies$ **Selisih = +49 kejadian** (**vintage berbeda**).
  * **Tahun 2022:**
    - `korban_meninggal`: Agregasi Kab/Kota = 858 vs Rekap Provinsi = 858 $\implies$ **Selisih = 0** (**metode berbeda**).
    - `korban_hilang`: Agregasi Kab/Kota = 37 vs Rekap Provinsi = 37 $\implies$ **Selisih = 0** (**metode berbeda**).
    - `korban_luka_sakit`: Agregasi Kab/Kota = 8.733 vs Rekap Provinsi = 8.733 $\implies$ **Selisih = 0** (**metode berbeda**).
    - `korban_terdampak_mengungsi`: Agregasi Kab/Kota = 6.087.878 vs Rekap Provinsi = 6.087.878 $\implies$ **Selisih = 0** (**metode berbeda**).
    - `kejadian`: Agregasi Kab/Kota = 3.595 vs Rekap Provinsi = 3.544 $\implies$ **Selisih = +51 kejadian** (**vintage berbeda**).
* **Periode di luar 2021–2022 (2009–2020 dan 2023–2025, 75 baris):**
  * *Nilai Seri Utama:* `null` (berkas mentah tingkat kabupaten/kota hanya tersedia dan diterbitkan untuk 2021 dan 2022).
  * *Kategori Penjelasan:* **cakupan berbeda**.

#### Pasangan 3: Seri Utama BNPB vs Seri Pembanding WDI (`EN.CLC.MDAT.ZS`)
* **Pasangan ID:** `P3_BNPB_VS_WDI`
* **Seri yang Dibandingkan:**
  * Seri Pembanding WDI: `EN.CLC.MDAT.ZS` (*Droughts, floods, extreme temperatures % of population, average 1990-2009*).
  * Seri Utama BNPB: Persentase penduduk terdampak bencana nasional terhadap populasi acuan 2025.
* **Ketersediaan Periode:**
  * WDI: Tahun **2009** (1 titik data snapshot historis Bank Dunia).
  * BNPB: Tahun **2010 s.d. 2025** (pada tahun 2009 data BNPB null). Periode beririsan langsung = **0 tahun** (K-041).
* **Evaluasi Angka dan Besar Selisih:**
  * **Tahun 2009 (Snapshot WDI):** Nilai WDI = **0,16059%**, Nilai BNPB = `null` $\implies$ **Selisih = null** (**vintage berbeda**; WDI merupakan rata-rata historis 1990–2009 yang mendahului pencatatan sistematis BNPB).
  * **Tahun 2010–2024 (15 periode):** Nilai BNPB ada, Nilai WDI = `null` $\implies$ **Selisih = null** (**vintage berbeda**; WDI tidak merilis pembaruan tahunan di paket).
  * **Tahun 2025 (Komparasi Konteks Paparan Bencana):**
    $$\text{Persentase Terdampak BNPB 2025} = \frac{\text{korban\_terdampak}}{\text{jumlah\_penduduk}} \times 100\% = \frac{10.955.315}{284.438.800} \times 100\% = \mathbf{3,851554\%}$$
    $$\text{Baseline Historis WDI (1990–2009)} = \mathbf{0,160590\%}$$
    $$\mathbf{Selisih = 3,851554\% - 0,160590\% = +3,690964\%}$$
    *Kategori Penjelasan:* **definisi berbeda** (WDI berbasis data bencana iklim ekstrem CRED EM-DAT, sedangkan BNPB mencakup seluruh spektrum bencana hidrometeorologi dan geologi).

---

### 2. Tabel Ringkasan Rekonsiliasi (Bahan Demo Sprint 2)

| Pasangan ID | Nama Pasangan | Seri Indikator | Periode | Nilai Utama | Nilai Pembanding | Satuan | Selisih | Kategori Penjelasan | Status Evaluasi |
|---|---|---|---|---|---|---|---|---|---|
| `P1_RASIO_100RB` | Rasio 100rb vs Terbitan | `korban_mengungsi_per_100rb` | 2025 | 405,993486 | 405,993486 | per_100rb | 0,000000 | metode berbeda | COCOK |
| `P1_RASIO_100RB` | Rasio 100rb vs Terbitan | `korban_meninggal_hilang_per_100rb` | 2025 | 0,660951 | 0,660951 | per_100rb | 0,000000 | metode berbeda | COCOK |
| `P2_KAB_VS_PROVINSI` | Agregasi Kab vs Provinsi | `korban_meninggal` | 2021 | 728 | 728 | jiwa | 0 | metode berbeda | COCOK |
| `P2_KAB_VS_PROVINSI` | Agregasi Kab vs Provinsi | `korban_hilang` | 2021 | 87 | 87 | jiwa | 0 | metode berbeda | COCOK |
| `P2_KAB_VS_PROVINSI` | Agregasi Kab vs Provinsi | `korban_luka_sakit` | 2021 | 14.915 | 14.915 | jiwa | 0 | metode berbeda | COCOK |
| `P2_KAB_VS_PROVINSI` | Agregasi Kab vs Provinsi | `korban_terdampak_mengungsi` | 2021 | 8.265.462 | 8.265.462 | jiwa | 0 | metode berbeda | COCOK |
| `P2_KAB_VS_PROVINSI` | Agregasi Kab vs Provinsi | `kejadian` | 2021 | 5.451 | 5.402 | kejadian | +49 | vintage berbeda | SELISIH_TERJELASKAN |
| `P2_KAB_VS_PROVINSI` | Agregasi Kab vs Provinsi | `korban_meninggal` | 2022 | 858 | 858 | jiwa | 0 | metode berbeda | COCOK |
| `P2_KAB_VS_PROVINSI` | Agregasi Kab vs Provinsi | `korban_hilang` | 2022 | 37 | 37 | jiwa | 0 | metode berbeda | COCOK |
| `P2_KAB_VS_PROVINSI` | Agregasi Kab vs Provinsi | `korban_luka_sakit` | 2022 | 8.733 | 8.733 | jiwa | 0 | metode berbeda | COCOK |
| `P2_KAB_VS_PROVINSI` | Agregasi Kab vs Provinsi | `korban_terdampak_mengungsi` | 2022 | 6.087.878 | 6.087.878 | jiwa | 0 | metode berbeda | COCOK |
| `P2_KAB_VS_PROVINSI` | Agregasi Kab vs Provinsi | `kejadian` | 2022 | 3.595 | 3.544 | kejadian | +51 | vintage berbeda | SELISIH_TERJELASKAN |
| `P3_BNPB_VS_WDI` | Seri BNPB vs WDI | `EN.CLC.MDAT.ZS` | 2009 | null | 0,160590 | persen | null | vintage berbeda | BASELINE_HISTORIS |
| `P3_BNPB_VS_WDI` | Seri BNPB vs WDI | `EN.CLC.MDAT.ZS` | 2025 | 3,851554 | 0,160590 | persen | +3,690964 | definisi berbeda | KOMPARASI_KONTEKS |

*Catatan:* Dari 13 baris observasi berpasangan yang dihitung selisihnya, 10 baris memiliki selisih tepat 0, sehingga nilai **`selisih_median` = 0.0**.

---

### 3. Penjelasan dan Bukti Setiap Kategori Penjelasan

Sesuai aturan Buku Pedoman dan Lampiran Langkah Kerja Bagian 3, seluruh selisih diklasifikasikan ke dalam 5 kategori baku tanpa menghapus atau memaksakan angka:

1. **Metode Berbeda (10 baris):**
   * *Arti:* Perbedaan prosedur teknis pembentukan data antara agregasi hitungan kelompok (*bottom-up*) dan rekapitulasi terbitan resmi (*top-down*).
   * *Karakteristik & Bukti Kasus:* Digunakan pada seluruh data korban jiwa 2021–2022 (Pasangan 2) dan rasio 100 ribu penduduk 2025 (Pasangan 1). Kategori ini membuktikan kekuatan integritas data kelompok karena menghasilkan **selisih 0**, membuktikan bahwa metode pembobotan dan agregasi kelompok konsisten sempurna dengan metodologi resmi BNPB.
2. **Vintage Berbeda (18 baris):**
   * *Arti:* Perbedaan waktu pemotongan (*cut-off time*) pengumpulan data, revisi bertahap, atau ketidaksejajaran jendela tahun observasi.
   * *Karakteristik & Bukti Kasus:* 
     * Pada seri kejadian 2021 (+49) dan 2022 (+51), Pusdatinkom BNPB menerbitkan rekapitulasi tingkat provinsi sebelum seluruh laporan akhir BPBD kabupaten/kota tuntas dihimpun. Bencana hidrometeorologi lintas wilayah (misal banjir DAS lintas 2–3 kabupaten) dicatat di setiap kabupaten terdampak, sehingga jumlahan kabupaten menghasilkan angka kejadian sedikit lebih tinggi daripada klaster provinsi.
     * Pada seri WDI 2009–2024, snapshot WDI merupakan rata-rata retrospektif 1990–2009 yang mendahului dimulainya pencatatan terstruktur BNPB (2010), sehingga tidak memiliki irisan rilis tahunan.
3. **Definisi Berbeda (1 baris):**
   * *Arti:* Perbedaan ruang lingkup konsep, batasan populasi, atau kriteria inklusi indikator.
   * *Karakteristik & Bukti Kasus:* Pada komparasi konteks tahun 2025 (Pasangan 3), WDI CRED EM-DAT membatasi populasi terdampak pada 3 jenis bencana iklim spesifik (kekeringan, banjir, dan suhu ekstrem), sedangkan data BNPB mencakup seluruh spektrum 9 jenis bencana alam (termasuk gempa bumi, tanah longsor, dan erupsi gunung api).
4. **Cakupan Berbeda (107 baris):**
   * *Arti:* Ketidakhadiran berkas mentah atau rincian wilayah/indikator pada periode tertentu di dalam paket data resmi.
   * *Karakteristik & Bukti Kasus:* Menjelaskan seluruh periode di mana salah satu sisi bernilai `null` (rincian kab/kota pra-2021 dan pasca-2022; rasio per 100 ribu penduduk pra-2025; serta ketiadaan data BNPB 2009). Periode-periode ini dipertahankan tetap hadir di tabel rekonsiliasi (*outer join*) untuk transparansi kelengkapan data.
5. **Belum Terjelaskan (0 baris):**
   * Seluruh variasi selisih dan ketiadaan pasangan data pada Kasus 22 berhasil diidentifikasi penyebab dan audit silsilahnya secara tuntas, sehingga tidak ada baris yang tersisa tanpa penjelasan.

---

### 4. Keterlacakan ke Berkas Gold dan Log Keputusan

Seluruh angka, parameter, dan status keterbandingan pada draf ini dapat ditarik ulang secara deterministik dari artefak repositori:
* **Tabel Rekonsiliasi Parquet & SQL:** `data/gold/tabel_rekonsiliasi.parquet` (136 baris), `data/gold/tabel_rekonsiliasi.csv`, dan tabel SQL `tabel_rekonsiliasi` di `data/gold/gold.sqlite`.
* **Tabel Nasional Parquet:** `data/gold/tabel_nasional.parquet` (90 baris) dan `data/gold/tabel_nasional_periode_seri.parquet` (17 periode × 11 seri).
* **Lineage & Log Keputusan (`log-keputusan.csv`):**
  * **K-006 & K-010:** Penanganan pemisahan baris kabupaten/kota dan penetapan wilayah nasional 9999.
  * **K-018:** Verifikasi satuan rasio per 100 ribu penduduk dan penetapan tahun 2025.
  * **K-026 & K-041:** Penetapan peran seri WDI `EN.CLC.MDAT.ZS` sebagai pembanding konteks dengan periode beririsan langsung 0 tahun.
  * **K-033:** Aturan validasi agregat provinsi vs nasional (hanya satuan aditif jiwa dan kejadian yang dijumlahkan).
  * **K-047:** Pembentukan tabel nasional Gold dengan kolom asal angka (`baris_indonesia`, `agregat_provinsi`, `pembanding`).
  * **K-049:** Pembentukan tabel rekonsiliasi 3 pasangan dengan kategori penjelasan baku dan metrik `selisih_median = 0.0`.

## Validasi dan reproduksibilitas

Validasi otomatis dijalankan melalui modul `src/validasi/` dan terintegrasi penuh dalam `pipeline.py`:
- **24 dari 24 aturan validasi berhasil lolos** (14 aturan Silver + 10 aturan Gold & Rekonsiliasi; 20 lolos murni, 4 lolos dengan catatan resmi: R04 floating-point noise $< 10^{-6}$, R08 alias nama provinsi, R12 kelengkapan parsial kejadian per jenis bencana, dan R13/R14 selisih agregasi yang terdokumentasi).
- **Kecepatan Pipeline:** Eksekusi penuh dari data mentah hingga Silver, Gold, dan validasi (`python pipeline.py`) tuntas dalam waktu **$\pm$ 4,5–6,0 detik** pada CPU laptop biasa (jauh di bawah batas toleransi maksimal 15 menit).
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
