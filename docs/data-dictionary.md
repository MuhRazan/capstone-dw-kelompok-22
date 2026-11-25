# Data dictionary — Kelompok 22 Korban Bencana

Satu tabel per keluaran. Isi di bawah dihitung dari `data/silver/silver.parquet` yang dihasilkan `python pipeline.py` (7.535 baris, 11 seri, 39 wilayah, 24 berkas sumber, periode 2009–2025). Seluruh isi dokumen ini dapat diperiksa ulang secara reproduktif dengan `python -m src.common.skema data/silver/silver.parquet` dan `python pipeline.py`.

---

## 1. data/silver/silver.parquet

Satu baris = satu seri × wilayah × periode × rincian × berkas sumber. Kunci primer gabungan unik: `["sumber", "seri_kode", "wilayah_kode", "periode", "rincian", "_berkas_raw"]`. Nilai dari sumber berbeda tidak digabung di Silver untuk mempertahankan silsilah (*lineage*) data secara utuh.

Setiap kolom Silver terdokumentasi dengan lengkap mencakup **Nama Kolom**, **Tipe Data**, **Satuan / Format**, **Arti / Makna**, **Asal (Berkas Mentah / Keputusan Log)**, **Boleh Kosong**, serta **Rentang / Nilai Sah**:

| Nama Kolom | Tipe Data | Satuan / Format | Arti / Makna | Asal (Berkas Mentah / Keputusan Log) | Boleh Kosong | Rentang / Nilai Sah |
|---|---|---|---|---|---|---|
| `sumber` | string (`object`) | — (teks identifier) | Lembaga atau keluarga format berkas mentah asal data baris ini (`bnpb_xlsx` = 11 berkas XLSX unduhan tangan BNPB 2021/2022/2025; `bnpb_json` = 12 resource API JSON datastore BNPB; `wdi` = World Bank API v2). | Ditetapkan oleh pembaca ekstraksi (`src/ekstraksi/bnpb_xlsx.py`, `src/ekstraksi/bnpb_json.py`, `src/ekstraksi/wdi.py`) berdasarkan folder sumber di `data/raw/` dan diisi pada `src/silver/__init__.py`. | Tidak (0 kosong) | 3 nilai: `bnpb_xlsx` (4.383 baris), `bnpb_json` (3.151 baris), `wdi` (1 baris). |
| `seri_kode` | string (`object`) | — (kode indikator) | Pengenal / kode unik indikator yang diukur. Tujuh seri korban berkorespondensi dengan target indikator global SDG 13.1.1/1.5.1/11.5.1; `kejadian`, `jumlah_penduduk`, dan `EN.CLC.MDAT.ZS` tidak membawa target SDG. | Pemetaan dari judul resource katalog CKAN dan kepala kolom tabel mentah ke kode seri baku di `src/silver/__init__.py` (didukung `src/kamus_bnpb.py` dan keputusan K-002, K-005, K-012, K-017, K-018; daftar resmi di `docs/katalog-seri.csv`). | Tidak (0 kosong) | 11 nilai: `kejadian`, `korban_meninggal`, `korban_hilang`, `korban_luka_sakit`, `korban_terdampak`, `korban_mengungsi`, `korban_terdampak_mengungsi`, `korban_mengungsi_per_100rb`, `korban_meninggal_hilang_per_100rb`, `jumlah_penduduk`, `EN.CLC.MDAT.ZS`. |
| `wilayah_kode` | integer (`int64`) | Kode wilayah administratif (BPS 2 digit × 100; `9999` = Indonesia) | Kode numerik wilayah administratif tingkat provinsi atau total nasional. Kode `9999` memisahkan agregat nasional agar tidak terjumlah ganda dengan provinsi. | Normalisasi dari kolom `Kode Wilayah Provinsi` (Kemendagri) atau pemetaan nama provinsi mentah via `src/wilayah.py`. Keputusan K-001: kode Kemendagri enam provinsi Papua dipetakan ke urutan kode BPS agar data tidak tertukar. | Tidak (0 kosong) | 39 nilai unik: 38 kode provinsi standar 2025 (1100–9600, kelipatan 100) dan `9999` (nasional). |
| `nama_wilayah` | string (`object`) | — (nama teks baku) | Nama resmi wilayah administratif dalam susunan 38 provinsi tahun 2025 dan Indonesia. Kolom ini bersifat deskriptif *human-readable*, sedangkan kunci proses tetap `wilayah_kode`. | Kolom `Provinsi`/`Nama Provinsi`/`Nama Wilayah` mentah yang dinormalisasi huruf besar dan diselaraskan dengan kamus wilayah `src/wilayah.py` (K-001/K-002). | Tidak (0 kosong) | 39 nama wilayah baku (38 provinsi resmi + `INDONESIA`). Ejaan sumber mentah yang bervariasi telah diselaraskan. |
| `periode` | string (`object`) | Tahun kalender `YYYY` | Periode waktu pencatatan data/kejadian bencana. Pada Kasus 22, seluruh data dianalisis dalam resolusi tahunan (`2009` s.d. `2025`). | Kolom tahun kejadian pada tabel mentah, kolom tahun (`2010.0` dst.), nama resource/berkas, atau field `date` WDI (Keputusan K-005, K-016). | Tidak (0 kosong) | 17 nilai tahun unik 4 digit: `2009` s.d. `2025`. Baris 2009 berasal dari WDI (rata-rata 1990–2009). |
| `jenis_periode` | string (`object`) | — (kategori frekuensi waktu) | Tingkat granularitas waktu periode data. Menunjukkan skala frekuensi pengamatan data yang tercatat. | Diturunkan dari sifat kolom `periode` di pembaca ekstraksi / `src/silver/__init__.py` (Keputusan K-016). | Tidak (0 kosong) | Hanya bernilai `tahun` (karena seluruh sumber yang digunakan berupa tabel tahunan). |
| `rincian` | string (`object`) | — (kategori dimensi) | Dimensi klasifikasi jenis bencana alam atau kategori agregat (`total`). Menunjukkan tipe bencana spesifik dari korban/kejadian yang dicatat pada baris tersebut. | Diturunkan dari nama kolom bencana pada tabel per jenis atau kolom `Jenis Bencana` pada tabel rekap mentah; ejaan diseragamkan lewat `src/kamus_bnpb.py` (Keputusan K-006). | Tidak (0 kosong) | 10 nilai unik: `total` dan 9 jenis bencana (`banjir`, `cuaca_ekstrem`, `erupsi_gunung_api`, `gelombang_pasang_dan_abrasi`, `gempabumi`, `kebakaran_hutan_dan_lahan`, `kekeringan`, `tanah_longsor`, `tsunami`). |
| `nilai` | float (`float64`) | Mengikuti kolom `satuan` (cacah orang/kejadian, rasio, atau persen) | Besaran kuantitatif observasi yang diukur. Mempertahankan nilai riil data mentah termasuk nilai ekstrem tanpa pemotongan buatan. | Nilai sel numerik dari berkas mentah (kolom tabel/JSON) setelah konversi numerik; nilai cacah dengan noise floating-point Excel (< 1e-6) dibulatkan (Keputusan K-010). | Tidak (0 kosong, tidak ada NaN/inf) | Rentang `0.0` hingga `284.438.800.0`. Untuk satuan cacah bernilai bulat. |
| `satuan` | string (`object`) | Unit pengukuran baku (`jiwa`, `kejadian`, `per_100000_penduduk`, `persen_penduduk`) | Satuan ukuran fisik dari angka pada kolom `nilai` (`jiwa` = orang; `kejadian` = frekuensi peristiwa; `per_100000_penduduk` = rasio per 100 ribu penduduk; `persen_penduduk` = persentase penduduk). | Peta `SATUAN` (`src/silver/__init__.py`) dan bukti pada lembar Keterangan / kepala tabel / katalog CKAN (Keputusan K-002, K-011, K-018; `docs/katalog-seri.csv`). | Tidak (0 kosong) | 4 nilai sah: `jiwa`, `kejadian`, `per_100000_penduduk`, `persen_penduduk`. Setiap seri hanya memiliki tepat satu satuan. |
| `_berkas_raw` | string (`object`) | Jalur relatif (*POSIX path*) terhadap `data/raw/` | Jejak silsilah (*lineage*): jalur berkas mentah tempat data baris ini pertama kali diekstraksi. Digunakan untuk merekonstruksi dan mengaudit data dari sumber aslinya. | Dihasilkan otomatis oleh fungsi pembaca ekstraksi saat membaca berkas mentah: `path.relative_to("data/raw").as_posix()`. | Tidak (0 kosong) | 24 jalur berkas mentah unik (11 XLSX BNPB, 12 JSON BNPB, 1 JSON WDI). |
| `_sha256_raw` | string (`object`) | Hash heksadesimal 64 karakter (SHA-256) | Sidik jari integritas digital (*integrity checksum*) berkas mentah. Membuktikan bahwa berkas mentah yang dipakai identik dengan yang terdaftar di `MANIFEST.csv`. | Dihitung otomatis menggunakan fungsi kriptografi `src.common.manifest.sha256_raw()` dan diverifikasi terhadap `data/raw/MANIFEST.csv`. | Tidak (0 kosong) | 24 hash heksadesimal 64 digit unik yang valid dan cocok dengan manifest. |

> **Catatan Skema Kolom Tambahan (Pandera / Standar Umum):**  
> Kolom opsional seperti `sdg_kode`, `batas_bawah`, `batas_atas`, dan `rujukan_tahun` (yang diperuntukkan bagi estimasi survei/interval ketidakpastian sumber WHO/BPS) tidak dimuat di tabel Silver kasus ini karena Kasus 22 bersumber murni dari data registrasi administratif bencana BNPB dan indikator WDI tanpa interval estimasi. Seluruh 11 kolom wajib di atas terisi penuh 100% tanpa nilai kosong (*zero nulls*).

---

## 2. Kamus Rincian dan Dimensi Bencana

Aturan penulisan rincian (Keputusan K-006):
* Dimensi bencana ditulis dalam format slug baku huruf kecil: `banjir`, `cuaca_ekstrem`, `erupsi_gunung_api`, `gelombang_pasang_dan_abrasi`, `gempabumi`, `kebakaran_hutan_dan_lahan`, `kekeringan`, `tanah_longsor`, `tsunami`.
* Variasi ejaan pada berkas mentah (misalnya `GEMPA BUMI` / `GEMPABUMI`, `LETUSAN GUNUNG API` / `ERUPSI GUNUNG API`, `GELOMBANG PASANG / ABRASI`) diseragamkan lewat `src/kamus_bnpb.py`.
* Nilai baris agregat seluruh jenis bencana pada berkas rekapitulasi dikodekan sebagai `total`.

---

## 3. Contoh Penelusuran Satu Baris Silver ke Berkas Mentah

Bagian ini menunjukkan bukti keterlacakan (*traceability*) penuh dari satu baris Silver sampai ke sel fisik pada berkas mentahnya.

### Sampel Baris Silver: Kejadian Banjir Provinsi Aceh Tahun 2021

Berikut adalah **seluruh 11 kolom** dari baris sampel yang diambil langsung dari `data/silver/silver.parquet`:

| Kolom | Nilai pada Baris Silver | Arti / Keterangan |
|---|---|---|
| `sumber` | `bnpb_xlsx` | Berasal dari berkas unduhan tangan format Excel BNPB |
| `seri_kode` | `kejadian` | Indikator jumlah peristiwa / kejadian bencana |
| `wilayah_kode` | `1100` | Kode administratif provinsi BPS untuk Provinsi Aceh |
| `nama_wilayah` | `ACEH` | Nama resmi wilayah administratif |
| `periode` | `2021` | Tahun observasi bencana |
| `jenis_periode` | `tahun` | Frekuensi pencatatan tahunan |
| `rincian` | `banjir` | Klasifikasi jenis bencana alam |
| `nilai` | `100.0` | 100 kali peristiwa kejadian banjir |
| `satuan` | `kejadian` | Satuan ukur frekuensi peristiwa bencana |
| `_berkas_raw` | `bnpb/2026-10-20/tangan/data-bencana/0c165adc-5be2-489d-8b1a-e90c6715e73e-tabel-jumlah-kejadian-korban-dan-kerusakan-akibat-bencana-tahun-2021-per-provinsi.xlsx` | Jalur relatif berkas Excel sumber di dalam `data/raw/` |
| `_sha256_raw` | `e951a1427459df035aaacd3873ce49295422d64debd670b9df8595645db6f963` | Hash SHA-256 berkas mentah yang cocok dengan MANIFEST.csv |

---

### Langkah Penelusuran dan Audit Sel Fisik

Penelusuran dilakukan secara berlapis untuk memastikan nilai numerik, satuan, dan definisinya otentik:

1. **Verifikasi Jalur Berkas dan Integritas Kriptografis (Lineage Layer)**:
   * Kolom `_berkas_raw` menunjuk ke lokasi fisik berkas di:  
     `data/raw/bnpb/2026-10-20/tangan/data-bencana/0c165adc-5be2-489d-8b1a-e90c6715e73e-tabel-jumlah-kejadian-korban-dan-kerusakan-akibat-bencana-tahun-2021-per-provinsi.xlsx`.
   * Nilai `_sha256_raw` (`e951a1427459df...`) dihitung dari berkas fisik menggunakan fungsi `src.common.manifest.sha256_raw()`.
   * Nilai hash tersebut cocok persis dengan baris pada `data/raw/MANIFEST.csv`, membuktikan berkas mentah belum pernah dimodifikasi atau rusak.

2. **Identifikasi Lembar Kerja (*Worksheet*)**:
   * Di dalam berkas Excel tersebut, data dimuat pada lembar kerja aktif bernama:  
     **`'Bencan Korban Kerusakan Prov'`**.

3. **Struktur Kepala Kolom (*Header Structure*)**:
   * **Baris 1**: Judul dokumen mentah: `"Tabel Jumlah Kejadian, Korban dan Kerusakan Akibat Bencana Tahun 2021 per Provinsi"`.
   * **Baris 3 (Header Tingkat 1)**:
     * Kolom A: `"Provinsi"`
     * Kolom B: `"Jenis Bencana"`
     * Kolom C: `"Jumlah Kejadian"`
     * Kolom D: `"Korban"`
     * Kolom H: `"Kerusakan"`
   * **Baris 4–5 (Header Tingkat 2 & Satuan)**:
     * Kolom D4–G4 memuat rincian korban: `Meninggal`, `Hilang`, `Luka-Luka`, `Terdampak - Mengungsi`.
     * Kolom D5 memuat keterangan satuan `(jiwa)`.
     * Kolom C3 secara mandiri mendefinisikan kolom `Jumlah Kejadian` dengan satuan kejadian.

4. **Koordinat Sel Fisik Data (*Exact Cell Coordinates*)**:
   * Pada baris data pertama (**Baris ke-6 / Row 6**):
     * **Sel `A6`**: Bernilai `'ACEH'` $\rightarrow$ Dipetakan menjadi `nama_wilayah: ACEH` dan `wilayah_kode: 1100`.
     * **Sel `B6`**: Bernilai `'BANJIR'` $\rightarrow$ Dipetakan menjadi `rincian: banjir`.
     * **Sel `C6`**: Bernilai **`100`** $\rightarrow$ Diekstrak menjadi `nilai: 100.0`, `satuan: kejadian`, dan `seri_kode: kejadian`.
   * **Penanganan Sel Tergabung (*Merged Cells*)**:
     * Pada berkas mentah Excel aslinya, sel `A6:A9` merupakan sel tergabung (*merged cell*) untuk Provinsi Aceh (baris 6 Banjir, baris 7 Cuaca Ekstrem, baris 8 Tanah Longsor, baris 9 Karhutla).
     * Sesuai **Keputusan K-003**, pembaca ekstraksi melakukan *forward fill* nilai dari sel kiri atas (`A6`) ke baris-baris bawahnya sehingga tidak ada baris rincian bencana yang kehilangan identitas provinsinya.

---

### Skrip Verifikasi Mandiri

Pemeriksa atau reviewer dapat menjalankan skrip mandiri berikut di terminal untuk memverifikasi penelusuran di atas secara otomatis:

```bash
python -c "
import pandas as pd
import openpyxl
from src.common.manifest import sha256_raw

# 1. Ambil baris sampel dari tabel Silver
df = pd.read_parquet('data/silver/silver.parquet')
m = (df['seri_kode'] == 'kejadian') & (df['wilayah_kode'] == 1100) & (df['periode'] == '2021') & (df['rincian'] == 'banjir')
row = df[m].iloc[0]
print('=== 1. Baris Silver ===')
print(row.to_dict())

# 2. Periksa kecocokan hash SHA-256 terhadap berkas mentah
calc_hash = sha256_raw(row['_berkas_raw'])
assert row['_sha256_raw'] == calc_hash, 'Hash tidak cocok!'
print('=== 2. Integritas Lineage ===')
print('Hash SHA-256 Cocok:', calc_hash)

# 3. Buka berkas Excel mentah dan periksa koordinat sel C6
wb = openpyxl.load_workbook('data/raw/' + row['_berkas_raw'], data_only=True)
ws = wb['Bencan Korban Kerusakan Prov']
print('=== 3. Nilai Sel Berkas Mentah ===')
print('Sheet              :', ws.title)
print('Sel A6 (Provinsi)  :', ws['A6'].value)
print('Sel B6 (Jenis)     :', ws['B6'].value)
print('Sel C6 (Kejadian)  :', ws['C6'].value)
assert ws['C6'].value == int(row['nilai']), 'Nilai sel fisik tidak sama dengan Silver!'
print('HASIL: Nilai sel mentah C6 (100) terbukti identik dengan nilai Silver (100.0).')
"
```

---

## 4. Rekonsiliasi Agregat (Tabel Pendamping Validasi)

| Berkas Laporan | Deskripsi Isi |
|---|---|
| `reports/validasi-agregasi-kabupaten.csv` | Jumlah kabupaten/kota yang dijumlahkan untuk setiap baris Silver hasil agregasi 2021–2022 (`n_kabupaten_kota`), nilai kabupaten/kota vs rekap provinsi, dan selisihnya. 1.530 baris agregasi; 21 selisih pada seri `kejadian` dicatat; 76 baris total provinsi berasal dari rekap provinsi, bukan agregasi kab/kota. |
| `reports/validasi-agregat-nasional.csv` | Rekonsiliasi jumlah provinsi vs baris nasional `9999` untuk satuan aditif (`jiwa`, `kejadian`). 157 pasangan dibandingkan; 5 selisih dicatat (4 gempabumi dan 1 jumlah penduduk −200). Seri rasio/persen tidak dijumlahkan karena tidak aditif. |

---

## 5. data/gold/panel.parquet (Panel Provinsi × Periode × Indikator)

Satu baris = satu indikator × provinsi × periode, mencakup seluruh sel dari kerangka grid (termasuk sel kosong). Kunci unik: `["indikator", "wilayah_kode", "periode"]`. Tabel ini memuat 10 indikator utama pada susunan 38 provinsi tahun 2025 untuk rentang waktu 2010–2025 (total 3.382 baris). Tampilan versi lebar (satu kolom per indikator untuk sel terisi) tersedia pada `data/gold/panel_lebar.parquet`.

| Nama Kolom | Tipe Data | Satuan / Format | Arti / Makna | Asal (Kolom Silver / Keputusan Log) | Boleh Kosong | Rentang / Nilai Sah |
|---|---|---|---|---|---|---|
| `indikator` | string (`object`) | — (label indikator) | Label deret utama kanonik. Berisi kode seri langsung atau format `kode [rincian]` untuk seri yang memiliki rincian dimensi. | Definisi deret kanonik pada `DERET` (`src/silver/deret.py` / `src/konfigurasi.py`) yang ditransformasi dari Silver (Keputusan K-005). | Tidak (0 kosong) | 10 nilai indikator baku (lihat tabel satuan per indikator di bawah). |
| `seri_kode` | string (`object`) | — (kode indikator) | Identitas kode indikator dasar asal pengukuran. | Diambil langsung dari kolom `seri_kode` pada tabel Silver. | Tidak (0 kosong) | 10 kode seri unik BNPB. |
| `rincian` | string (`object`) | — (kategori dimensi) | Dimensi rincian pengamatan yang dipilih pada panel kanonik (`jumlah` untuk jumlahan jenis bencana, atau `total` untuk agregat). | Diambil dari kolom `rincian` Silver yang difilter sesuai aturan deret (Keputusan K-005, K-006). | Tidak (0 kosong) | 2 nilai: `jumlah` (9 indikator korban/kejadian) dan `total` (`jumlah_penduduk`). |
| `wilayah_kode` | integer (`int64`) | Kode wilayah (BPS 2 digit × 100) | Kode numerik wilayah administratif tingkat provinsi. | Diambil dari kolom `wilayah_kode` Silver (Keputusan K-001: susunan 38 provinsi tahun 2025). | Tidak (0 kosong) | 38 kode provinsi resmi (1100–9700, tanpa kode nasional 9999). |
| `nama_wilayah` | string (`object`) | — (nama baku) | Nama resmi wilayah administratif provinsi. | Diambil dari kolom `nama_wilayah` Silver via kamus `src/wilayah.py`. | Tidak (0 kosong) | 38 nama baku provinsi Indonesia susunan 2025. |
| `periode` | string (`object`) | Tahun kalender `YYYY` | Tahun observasi pengamatan bencana dalam resolusi tahunan. | Diambil dari kolom `periode` Silver (Keputusan K-005, K-016). | Tidak (0 kosong) | 16 nilai tahun unik: `2010` s.d. `2025`. |
| `jenis_periode` | string (`object`) | — (kategori frekuensi) | Skala granularitas waktu pengamatan data panel. | Diambil dari kolom `jenis_periode` Silver. | Tidak (0 kosong) | Hanya bernilai `tahun`. |
| `nilai` | float (`float64`) | Mengikuti kolom `satuan` | Besaran kuantitatif observasi yang diukur. Sel kosong pada grid diisi `NaN` tanpa interpolasi buatan. | Diambil dari kolom `nilai` Silver untuk sel terisi; `NaN` untuk sel yang tidak/belum terbit (Keputusan K-027). | Ya (2.008 kosong dari total 3.382 sel) | Rentang `0.0` hingga `50.759.000.0` (pada sel terisi). |
| `satuan` | string (`object`) | Unit pengukuran baku | Satuan fisik dari angka pada kolom `nilai` (`jiwa`, `kejadian`, `per_100000_penduduk`). | Diambil dari kolom `satuan` Silver sesuai kamus konfigurasi `SATUAN` (Keputusan K-011, K-018). | Tidak (0 kosong) | 3 nilai: `jiwa`, `kejadian`, `per_100000_penduduk`. |
| `status_sel` | string (`object`) | — (kategori status grid) | Kategori keterisian sel pada kerangka panel: `terisi` (ada observasi riil), `tidak_diterbitkan` (tidak ada tabel provinsi di katalog), atau `belum_ada` (provinsi belum terbentuk). | Diturunkan dari analisis grid kelengkapan panel Sprint 1 (`reports/grid-sel-kosong.csv`, Keputusan K-011, K-013). | Tidak (0 kosong) | 3 nilai sah: `terisi` (1.374 sel), `tidak_diterbitkan` (1.772 sel), `belum_ada` (236 sel). |
| `penanda` | string (`object`) | — (kategori anomali) | Label penanda anomali data hasil audit empiris Sprint 1 (misal: `outlier` bencana besar atau `perbedaan_struktural`). Nilai data tetap dipertahankan apa adanya. | Diturunkan dari laporan deteksi anomali Sprint 1 (`reports/anomali.csv`, Keputusan K-004, K-012, K-013). | Ya (3.263 kosong / normal) | 119 sel bertanda: `outlier` (101 sel), `perbedaan_struktural` (18 sel). |
| `rujukan_tahun` | float (`float64`) | Tahun kalender | Lebar jendela rujukan survei (tahun sebelum survei). | Diambil dari kolom `rujukan_tahun` Silver (seluruhnya kosong karena kasus bencana bersumber registrasi administratif). | Ya (seluruhnya kosong / NaN) | Kosong (`NaN`). |
| `_berkas_raw` | string (`object`) | Jalur relatif terhadap `data/raw/` | Jejak silsilah (*lineage*) berkas mentah sumber asal sel terpilih (kosong untuk sel yang tidak terbit/belum ada). | Diambil dari kolom `_berkas_raw` Silver berdasarkan urutan prioritas berkas kanonik (Keputusan K-007). | Ya (2.008 kosong pada sel kosong) | 16 jalur berkas mentah unik BNPB. |
| `_sha256_raw` | string (`object`) | Hash heksadesimal 64 karakter | Sidik integritas kriptografis berkas mentah sumber (kosong untuk sel yang tidak terbit/belum ada). | Diambil dari kolom `_sha256_raw` Silver dan diverifikasi terhadap `MANIFEST.csv`. | Ya (2.008 kosong pada sel kosong) | 16 hash heksadesimal unik valid. |

> **Catatan Variasi Kolom Turunan Workspace:**  
> Pada implementasi repositori kelompok, tabel `data/gold/panel.parquet` memuat 3 kolom kalkulasi pembantu tambahan untuk mempermudah pemodelan lanjutan, yaitu: `rincian_kode` (integer ID rincian), `nilai_per_100rb` (normalisasi rasio per 100 ribu penduduk terhadap penduduk provinsi), dan `nilai_log1p` (transformasi $\log(1 + x)$ untuk analisis sebaran). Nilai asli pada kolom `nilai` tetap murni tanpa modifikasi.

#### Satuan per Indikator Panel:
| Indikator | Satuan |
|---|---|
| `jumlah_penduduk` | `jiwa` |
| `kejadian [jumlah]` | `kejadian` |
| `korban_hilang [jumlah]` | `jiwa` |
| `korban_luka_sakit [jumlah]` | `jiwa` |
| `korban_mengungsi [jumlah]` | `jiwa` |
| `korban_mengungsi_per_100rb [jumlah]` | `per_100000_penduduk` |
| `korban_meninggal [jumlah]` | `jiwa` |
| `korban_meninggal_hilang_per_100rb [jumlah]` | `per_100000_penduduk` |
| `korban_terdampak [jumlah]` | `jiwa` |
| `korban_terdampak_mengungsi [jumlah]` | `jiwa` |

---

## 6. data/gold/nasional.parquet (Tabel Agregat Tingkat Nasional)

Satu baris = satu seri × rincian × periode tingkat Indonesia. Kunci unik: `["seri_kode", "rincian", "periode"]`. Tabel ini mengompilasi seluruh observasi tingkat nasional dari terbitan resmi BNPB kode `9999`, indikator pembanding WDI, serta jumlahan agregat 38 provinsi (78 baris, 11 seri, periode 2009–2025). Pada repositori kelompok juga disediakan versi tabel terdisagregasi `data/gold/tabel_nasional.parquet` dan format matriks periode `tabel_nasional_periode_seri.parquet`.

| Nama Kolom | Tipe Data | Satuan / Format | Arti / Makna | Asal (Kolom Silver / Keputusan Log) | Boleh Kosong | Rentang / Nilai Sah |
|---|---|---|---|---|---|---|
| `seri_kode` | string (`object`) | — (kode indikator) | Pengenal indikator tingkat nasional (mencakup 10 seri bencana BNPB, seri agregat provinsi, dan seri WDI `EN.CLC.MDAT.ZS`). | Diambil dari kolom `seri_kode` Silver atau dibentuk dari agregasi provinsi `kejadian (agregat provinsi)`. | Tidak (0 kosong) | 11 nilai kode seri nasional. |
| `rincian` | string (`object`) | — (kategori dimensi) | Rincian dimensi pengamatan pada tingkat nasional (`total` atau `jenis_bencana=...`). | Diambil dari kolom `rincian` Silver. | Tidak (0 kosong) | Nilai rincian bencana dan `total`. |
| `sumber` | string (`object`) | — (teks identifier) | Lembaga penerbit berkas mentah pengamatan nasional (`bnpb` atau `wdi`). | Diambil dari kolom `sumber` Silver. | Tidak (0 kosong) | 2 nilai: `bnpb` dan `wdi`. |
| `periode` | string (`object`) | Tahun kalender `YYYY` | Tahun observasi pengamatan nasional dalam resolusi tahunan. | Diambil dari kolom `periode` Silver (Keputusan K-016). | Tidak (0 kosong) | 17 nilai tahun unik: `2009` s.d. `2025`. |
| `jenis_periode` | string (`object`) | — (kategori frekuensi) | Skala granularitas waktu pengamatan nasional. | Diambil dari kolom `jenis_periode` Silver. | Tidak (0 kosong) | Hanya bernilai `tahun`. |
| `nilai` | float (`float64`) | Mengikuti kolom `satuan` | Besaran kuantitatif observasi tingkat nasional. | Diambil dari kolom `nilai` Silver pada baris nasional `9999` atau hasil kalkulasi jumlahan provinsi. | Tidak (0 kosong) | Rentang `0.16059` (persen WDI) hingga `284.438.800.0` (penduduk). |
| `satuan` | string (`object`) | Unit pengukuran baku | Satuan ukuran fisik dari kolom `nilai` (`jiwa`, `kejadian`, `per_100000_penduduk`, `persen`). | Diambil dari kolom `satuan` Silver sesuai bukti katalog (Keputusan K-011, K-018). | Tidak (0 kosong) | 4 nilai sah: `jiwa`, `kejadian`, `per_100000_penduduk`, `persen`. |
| `batas_bawah` | float (`float64`) | Sesuai satuan | Batas bawah interval ketidakpastian. | Diambil dari kolom `batas_bawah` Silver (kosong bila sumber tidak menyediakan). | Ya (seluruhnya kosong / NaN) | Kosong (`NaN`). |
| `batas_atas` | float (`float64`) | Sesuai satuan | Batas atas interval ketidakpastian. | Diambil dari kolom `batas_atas` Silver (kosong bila sumber tidak menyediakan). | Ya (seluruhnya kosong / NaN) | Kosong (`NaN`). |
| `rujukan_tahun` | float (`float64`) | Tahun kalender | Lebar jendela rujukan survei. | Diambil dari kolom `rujukan_tahun` Silver. | Ya (seluruhnya kosong / NaN) | Kosong (`NaN`). |
| `asal` | string (`object`) | — (kategori asal baris) | Asal usul pembentukan baris nasional: `baris_indonesia` (terbitan tabel nasional resmi BNPB), `pembanding` (data WDI), atau `agregat` (jumlahan 38 provinsi). | Ditetapkan oleh modul `src/gold/nasional_gold.py` / `tabel_nasional.py` (Keputusan K-015, K-016). | Tidak (0 kosong) | 3 nilai: `baris_indonesia`, `pembanding`, `agregat`. |
| `_berkas_raw` | string (`object`) | Jalur relatif terhadap `data/raw/` | Jalur berkas mentah sumber asal angka nasional. | Diambil dari kolom `_berkas_raw` Silver (Keputusan K-015). | Tidak (0 kosong) | 14 jalur berkas mentah unik. |
| `_sha256_raw` | string (`object`) | Hash heksadesimal 64 karakter | Sidik integritas digital berkas mentah sumber (bernilai null untuk baris hasil agregasi internal). | Diambil dari kolom `_sha256_raw` Silver dan dicocokkan dengan `MANIFEST.csv`. | Ya (2 baris agregat bernilai kosong) | 12 hash heksadesimal unik valid. |

---

## 7. data/gold/rekonsiliasi.parquet (Tabel Rekonsiliasi Pembanding)

Satu baris = satu pasangan rekonsiliasi × pembanding × periode. Kunci unik: `["pasangan_id", "seri_pembanding", "rincian_pembanding", "periode"]`. Tabel ini memuat hasil evaluasi dan komparasi kuantitatif antara seri utama BNPB dengan seri pembanding (hitungan ulang rasio, agregasi wilayah, dan data WDI) untuk 4 pasangan rekonsiliasi P1–P4 (19 baris pengamatan). Pada repositori kelompok juga tersedia tabel berformat `data/gold/tabel_rekonsiliasi.parquet`.

| Nama Kolom | Tipe Data | Satuan / Format | Arti / Makna | Asal (Kolom Silver / Keputusan Log) | Boleh Kosong | Rentang / Nilai Sah |
|---|---|---|---|---|---|---|
| `pasangan_id` | string (`object`) | — (kode pasangan) | Pengenal unik pasangan rekonsiliasi (`P1`, `P2`, `P3`, `P4`). | Didefinisikan dalam kamus `PASANGAN` di `src/konfigurasi.py` (Keputusan K-016). | Tidak (0 kosong) | 4 nilai: `P1`, `P2`, `P3`, `P4`. |
| `jenis` | string (`object`) | — (kategori evaluasi) | Tipe pembandingan: `selisih` (dihitung gap kuantitatifnya) atau `konteks` (disandingkan sebagai konteks makro tanpa hitungan selisih langsung). | Ditetapkan pada konfigurasi `PASANGAN` (Keputusan K-016). | Tidak (0 kosong) | 2 nilai: `selisih` (P1, P2, P3) dan `konteks` (P4 WDI). |
| `seri_utama` | string (`object`) | — (kode indikator) | Seri indikator utama yang direkonsiliasi. | Diambil dari seri utama BNPB / WDI yang ditetapkan pada konfigurasi `PASANGAN`. | Tidak (0 kosong) | 4 seri: `korban_mengungsi_per_100rb`, `korban_meninggal_hilang_per_100rb`, `kejadian`, `EN.CLC.MDAT.ZS`. |
| `rincian_utama` | string (`object`) | — (kategori dimensi) | Dimensi rincian seri utama yang dibandingkan. | Ditetapkan pada konfigurasi `PASANGAN`. | Tidak (0 kosong) | 2 nilai: `total` dan `jenis_bencana=banjir`. |
| `seri_pembanding` | string (`object`) | — (nama pembanding) | Deskripsi atau nama seri pembanding yang dipasangkan (misal: formula hitungan ulang pembilang/penduduk, jumlahan provinsi, atau indikator sebanding). | Didefinisikan pada konfigurasi `PASANGAN` (`src/gold/rekonsiliasi.py`). | Tidak (0 kosong) | 4 seri pembanding resmi. |
| `rincian_pembanding` | string (`object`) | — (kategori dimensi) | Rincian dimensi pembanding yang sebanding. | Ditetapkan pada konfigurasi `PASANGAN`. | Tidak (0 kosong) | 2 nilai: `hitung` dan `jenis_bencana=banjir`. |
| `periode` | string (`object`) | Tahun kalender `YYYY` | Tahun observasi pembandingan. | Diambil dari kolom `periode` tabel nasional Gold. | Tidak (0 kosong) | 17 nilai tahun unik: `2009` s.d. `2025`. |
| `nilai_utama` | float (`float64`) | Mengikuti kolom `satuan` | Nilai capaian seri utama pada periode terkait. | Diambil dari kolom `nilai` pada tabel nasional Gold (`data/gold/nasional.parquet`). | Tidak (0 kosong) | Rentang `0.16059` hingga `2.009.0`. |
| `nilai_pembanding` | float (`float64`) | Mengikuti kolom `satuan` | Nilai capaian pembanding dalam satuan yang telah disetarakan dengan seri utama. | Dihitung dari tabel nasional / formula konversi `GOLD_KONVERSI` (Keputusan K-016). | Ya (15 kosong pada periode non-irisan) | Rentang `0.539659` hingga `2.009.0` (pada periode beririsan). |
| `satuan` | string (`object`) | Unit pengukuran baku | Satuan ukuran pembandingan (`kejadian`, `per_100000_penduduk`, `persen`). | Ditetapkan pada kamus `PASANGAN` sesuai satuan seri utama (Keputusan K-018). | Tidak (0 kosong) | 3 nilai: `kejadian`, `per_100000_penduduk`, `persen`. |
| `selisih` | float (`float64`) | Mengikuti kolom `satuan` | Selisih absolut antara nilai utama dikurangi nilai pembanding ($\text{nilai\_utama} - \text{nilai\_pembanding}$). | Dihitung secara matematis di `src/gold/rekonsiliasi.py` (kosong pada pasangan konteks atau non-irisan). | Ya (15 kosong pada baris tanpa pembanding) | Rentang `-8.0` hingga `0.0`. |
| `selisih_relatif` | float (`float64`) | Persen (`%`) | Persentase selisih relatif terhadap pembanding: $100 \times \frac{\text{selisih}}{\text{nilai\_pembanding}}$. | Dihitung secara matematis di `src/gold/rekonsiliasi.py`. | Ya (15 kosong) | Rentang `-0.5602%` hingga `0.0%` (median selisih relatif = 0.0%). |
| `asal` | string (`object`) | — (status pasangan) | Status ketersediaan data pembanding: `keduanya` (kedua nilai ada dan dapat dibandingkan) atau `hanya_utama` (hanya seri utama yang terbit). | Ditentukan otomatis oleh algoritma penyandingan rekonsiliasi. | Tidak (0 kosong) | 2 nilai: `keduanya` (4 baris) dan `hanya_utama` (15 baris). |
| `kategori` | string (`object`) | — (kategori baku selisih) | Klasifikasi baku penyebab selisih/hubungan: `tidak berselisih`, `definisi berbeda`, atau `tanpa pasangan`. | Pemetaan kategori baku pada konfigurasi `PASANGAN` (Keputusan K-016). | Tidak (0 kosong) | 3 kategori baku: `tidak berselisih` (P1, P2), `definisi berbeda` (P3), `tanpa pasangan` (P4). |
| `penjelasan` | string (`object`) | — (narasi bukti) | Penjelasan substantif metodologis penyebab selisih didukung bukti empiris data mentah. | Ditetapkan pada konfigurasi `PASANGAN` (Keputusan K-016). | Tidak (0 kosong) | Teks penjelasan lengkap per pasangan (misal: kejadian multi-provinsi dihitung sekali secara nasional pada P3). |
| `catatan` | string (`object`) | — (catatan teknis) | Keterangan teknis alasan selisih tidak dihitung atau metode hitung pembanding. | Dihasilkan otomatis oleh modul rekonsiliasi. | Ya (15 baris kosong) | Deskripsi formula pembanding atau alasan teknis. |

---

## 8. Contoh Penelusuran Satu Sel Gold ke Silver dan Berkas Mentah

Berikut adalah pembuktian silsilah (*lineage*) satu sel pada tabel panel Gold hingga ke baris Silver dan sel fisik berkas mentah:

| Kolom Indikator | Wilayah Kode | Periode | Nilai Gold | Satuan | Berkas Sumber Mentah (`_berkas_raw`) |
|---|---|---|---|---|---|
| `jumlah_penduduk` | `1100` (Aceh) | `2025` | `5,626,000.00` | `jiwa` | `bnpb/2026-10-20/tangan/kompilasi-data-kejadian-dan-dampak-bencana-2025/31a0d329-a363-4a16-852c-f4fa51f313bf-jumlah-korban-mengungsi-per-100.000-orang-akibat-bencana-menurut-provinsi-2025.xlsx` |

### Tahapan Verifikasi Silsilah (*Lineage Audit*):
1. **Dari Gold ke Silver**:  
   Sel Gold di atas ditelusuri ke tabel Silver `data/silver/silver.parquet` pada kunci: `seri_kode = "jumlah_penduduk"`, `wilayah_kode = 1100`, `periode = "2025"`, dan `rincian = "total"`. Ditemukan tepat satu baris Silver dengan nilai yang sama persis: `5.626.000,0` jiwa.
2. **Dari Silver ke Berkas Mentah**:  
   Baris Silver tersebut membawa `_berkas_raw` yang menunjuk ke berkas Excel `31a0d329-...-menurut-provinsi-2025.xlsx` dan hash `_sha256_raw` sebesar `804d953ed748a1c85da940ae890233d1ee368c6eb05d5ddc90e4a23e25c89bcd`.
3. **Kesesuaian dengan Manifest**:  
   Sidik hash di atas cocok 100% dengan baris berkas terkait pada `data/raw/MANIFEST.csv`. Di lembar kerja Excel aslinya, angka 5.626.000 tercantum pada baris Provinsi Aceh di kolom `Jumlah Penduduk`. Hal ini membuktikan bahwa sel Gold tertelusur secara utuh (*end-to-end traceable*) ke sumber primernya.


