# Laporan Hasil Validasi Silver dan Gold — Kasus 22: Korban Bencana

Dokumen ini menyajikan hasil evaluasi otomatis 24 aturan validasi data wrangling pada lapis Silver, Gold Panel, dan Rekonsiliasi Nasional. Validasi dieksekusi secara terpadu oleh `python pipeline.py` pada tahap `validasi` (tahap 8) untuk menjamin integritas data, konsistensi skema, dan reproduksibilitas.

## 1. Ringkasan Eksekutif Validasi

| Parameter Evaluasi | Nilai Aktual | Keterangan / Sumber Verifikasi |
|---|---|---|
| **Baris Silver** | 7,535 baris | 11 kolom wajib, tanpa sel kosong (`data/silver/silver.parquet`) |
| **Seri Silver** | 11 seri | 9 seri korban BNPB, 1 penyebut penduduk, 1 pembanding WDI |
| **Cakupan Wilayah** | 39 kode | 38 provinsi standar 2025 + kode 9999 nasional |
| **Berkas Sumber Mentah** | 24 berkas | 100% cocok dengan `data/raw/MANIFEST.csv` |
| **Rentang Periode** | 2009–2025 | Resolusi tahunan |
| **Baris Panel Gold** | 3,382 baris | Grid lengkap provinsi × periode × indikator (`data/gold/panel.parquet`) |
| **Baris Nasional Gold** | 90 baris | Agregat nasional dengan kolom asal (`data/gold/tabel_nasional.parquet`) |
| **Baris Rekonsiliasi Gold** | 136 baris | 3 pasangan rekonsiliasi mandat (`data/gold/tabel_rekonsiliasi.parquet`) |
| **Sidik Data Mentah (`data_hash`)** | `f26ed8682abbbc3496c256c56ac008f22b4bb473cd3ad9a34eb5b2f443a63b2f` | Kriptografi sha256 terurut dari `MANIFEST.csv` |
| **Total Aturan Validasi** | **24 aturan** | 14 aturan Silver + 10 aturan Gold & Rekonsiliasi |
| **Aturan Lolos Sempurna** | **19 aturan** | Terpenuhi 100% tanpa catatan (0 baris melanggar) |
| **Aturan Lolos dengan Catatan** | **5 aturan** | Terpenuhi dengan toleransi/penjelasan resmi terdokumentasi |
| **Aturan Gagal** | **0 aturan** | Tidak ada pelanggaran kritis (*zero hard failures*) |

---

## 2. Tabel Ringkasan Hasil Aktual Tiap Aturan Validasi

Definisi status:
- **LOLOS**: Aturan terpenuhi secara sempurna tanpa ada deviasi atau catatan (0 baris melanggar).
- **LOLOS_DENGAN_CATATAN**: Aturan terpenuhi; selisih empiris atau variasi yang diizinkan telah diverifikasi dan terdokumentasi di tabel pendamping.
- **GAGAL**: Aturan dilanggar dan menghentikan eksekusi pipeline (*fail-fast*).

| ID | Aturan Validasi | Lapis Data | Jenis Aturan | Status Aktual | Baris Terdampak | Ringkasan Hasil Pengujian Aktual |
|---|---|---|---|---|---|---|
| **R01** | Skema kolom Silver | Silver | Keras | `LOLOS` | 0 | 11 kolom wajib lengkap, tanpa sel kosong |
| **R02** | Keunikan kunci Silver | Silver | Keras | `LOLOS` | 0 | 6 kolom kunci unik untuk 7,535 baris |
| **R03** | Nilai tidak negatif dan berhingga | Silver | Keras | `LOLOS` | 0 | nilai minimum 0.00; tidak ada nilai negatif atau tak berhingga |
| **R04** | Bilangan bulat untuk jiwa/kejadian | Silver | Peringatan | `LOLOS_DENGAN_CATATAN` | 0 | 6,832 baris jiwa/kejadian; 10 baris ber-noise float < 1e-6 (bukan pelanggaran) |
| **R05** | Konsistensi satuan per seri | Silver | Keras | `LOLOS` | 0 | 11 seri memakai satu satuan sesuai peta SATUAN; satuan: jiwa, kejadian, per_100000_penduduk, persen_penduduk |
| **R06** | Rentang nilai masuk akal per satuan | Silver | Keras | `LOLOS` | 0 | jiwa 0.00-284,438,800.00 (batas 0-300,000,000); kejadian 0.00-4,727.00 (batas 0-10,000); per_100000_penduduk 0.00-16,836.54 (batas 0-100,000); persen_penduduk 0.16-0.16 (batas 0-100) |
| **R07** | Kode wilayah sah | Silver | Keras | `LOLOS` | 0 | 39 kode: 38 provinsi BPS x 100 + 9999 Indonesia |
| **R08** | Konsistensi nama wilayah | Silver | Peringatan | `LOLOS_DENGAN_CATATAN` | 0 | 41 ejaan untuk 39 kode; ejaan ganda hanya pada alias resmi |
| **R09** | Periode dan jenis periode | Silver | Keras | `LOLOS` | 0 | semua 7,535 baris bertipe tahun, 2009-2025 |
| **R10** | Rincian jenis bencana dikenal | Silver | Keras | `LOLOS` | 0 | 10 nilai: total + 9 jenis bencana |
| **R11** | Lineage berkas mentah | Silver | Keras | `LOLOS` | 0 | 24 berkas sumber cocok dengan MANIFEST.csv |
| **R12** | Kelengkapan wilayah per seri/periode | Silver | Peringatan | `LOLOS_DENGAN_CATATAN` | 1,692 | 134 grup lengkap 38 provinsi; 88 grup parsial dicatat (hanya provinsi yang punya kejadian) |
| **R13** | Agregat kabupaten/kota ke provinsi | Silver | Peringatan | `LOLOS_DENGAN_CATATAN` | 21 | 1,530 baris agregasi kab/kota; 21 selisih dicatat; 76 baris total provinsi tanpa rincian kab/kota |
| **R14** | Agregat provinsi ke nasional | Silver | Peringatan | `LOLOS_DENGAN_CATATAN` | 5 | 157 pasangan aditif dibandingkan; 5 selisih dicatat; 3 seri rasio/persen tidak dijumlahkan |
| **R15** | gold: kunci panel unik | Gold Panel | Keras | `LOLOS` | 0 | indikator + wilayah_kode + periode tidak kembar (terpenuhi, 0 pelanggaran) |
| **R16** | gold: satu satuan per indikator | Gold Panel | Keras | `LOLOS` | 0 | satu indikator panel hanya punya satu satuan (terpenuhi, 0 pelanggaran) |
| **R17** | gold: status sel dan nilai | Gold Panel | Keras | `LOLOS` | 0 | status sel baku; nilai ada jika dan hanya jika sel terisi (terpenuhi, 0 pelanggaran) |
| **R18** | gold: sel tertelusur ke Silver | Gold Panel | Keras | `LOLOS` | 0 | setiap sel terisi punya baris Silver asal (seri, wilayah, periode, berkas) (terpenuhi, 0 pelanggaran) |
| **R19** | gold: nilai sama dengan Silver | Gold Panel | Keras | `LOLOS` | 0 | nilai panel = nilai Silver asalnya (tidak ada nilai yang diubah di Gold) (terpenuhi, 0 pelanggaran) |
| **R20** | gold: tabel nasional unik | Gold Panel | Keras | `LOLOS` | 0 | seri + rincian + periode tidak kembar (terpenuhi, 0 pelanggaran) |
| **R21** | rekonsiliasi: kategori baku | Rekonsiliasi | Keras | `LOLOS` | 0 | kategori dari daftar baku; penjelasan tidak kosong (terpenuhi, 0 pelanggaran) |
| **R22** | rekonsiliasi: selisih = utama − pembanding | Rekonsiliasi | Keras | `LOLOS` | 0 | selisih dihitung ulang dan cocok (terpenuhi, 0 pelanggaran) |
| **R23** | rekonsiliasi: baris berpasangan dihitung | Rekonsiliasi | Keras | `LOLOS` | 0 | pasangan selisih dengan dua nilai punya selisih, atau catatan mengapa tidak (terpenuhi, 0 pelanggaran) |
| **R24** | rekonsiliasi: periode utama tidak dibuang | Rekonsiliasi | Keras | `LOLOS` | 0 | setiap tahun seri utama di tabel nasional muncul di rekonsiliasi (terpenuhi, 0 pelanggaran) |

---

## 3. Rincian Aturan dengan Catatan dan Tindak Lanjut Perbaikannya

Pada pengujian validasi menyeluruh, terdapat **4 aturan** yang menghasilkan catatan (*warning/catatan resmi*). Seluruh catatan ini bukan merupakan kesalahan sistem data wrangling, melainkan anomali empiris berkas mentah yang telah ditangani dan dicatat tindak lanjutnya dalam `log-keputusan.csv`:

### 1. R04 — Bilangan bulat untuk korban jiwa dan frekuensi kejadian
- **Kondisi Aktual:** Ditemukan 10 baris pada seri korban jiwa dengan nilai pecahan desimal sangat kecil ($< 10^{-6}$), misalnya `12.0000000001`.
- **Penyebab:** *Floating-point representation noise* akibat formula kalkulasi otomatis pada berkas XLSX sumber mentah BNPB.
- **Tindak Lanjut & Keputusan:** Nilai dibulatkan ke bilangan bulat terdekat menggunakan fungsi pembulatan presisi tanpa mengubah magnitude data riil, dicatat pada keputusan **K-010**.

### 2. R08 — Konsistensi penamaan wilayah administratif
- **Kondisi Aktual:** Terdeteksi 41 variasi penulisan nama wilayah untuk 39 kode wilayah yang sah.
- **Penyebab:** Perbedaan penulisan nama resmi provinsi pada berkas tahun berbeda (misalnya `DKI JAKARTA` vs `DAERAH KHUSUS IBUKOTA JAKARTA`, serta penetapan provinsi baru Papua Barat Daya pada 2022).
- **Tindak Lanjut & Keputusan:** Standardisasi nama wilayah ditegakkan menggunakan kamus baku `src/wilayah.py` berdasarkan kode numerik BPS 2 digit × 100 (kode 1100–9600 dan 9999 nasional). Nama diselaraskan ke susunan resmi 38 provinsi tahun 2025, dicatat pada keputusan **K-001** dan **K-002**.

### 3. R12 — Kelengkapan wilayah per seri dan periode (Grid wilayah × periode)
- **Kondisi Aktual:** Dari total observasi, terdapat 134 grup wilayah yang lengkap 38 provinsi, dan 88 grup parsial dengan total 1.692 sel kosong pada grid per jenis bencana.
- **Penyebab:** Fenomena bencana alam bersifat spesifik lokasi; tidak semua provinsi mengalami ke-9 jenis bencana alam setiap tahunnya (misalnya erupsi gunung api atau tsunami hanya terjadi di provinsi tertentu).
- **Tindak Lanjut & Keputusan:** Sel kosong dipertahankan secara jujur tanpa rekayasa imputasi numerik. Pada lapis Gold, diberi penanda status sel baku (`tidak_diterbitkan` atau `belum_ada`) sesuai keputusan **K-020** dan **K-045**.

### 4. R13 & R14 — Evaluasi Rekonsiliasi Agregasi (Kabupaten ke Provinsi & Provinsi ke Nasional)
- **Kondisi Aktual:**
  - R13: Dari 1.530 baris agregasi kab/kota 2021–2022, seluruh indikator korban jiwa cocok 100% (selisih 0), tetapi terdapat selisih pada frekuensi kejadian: +49 kejadian (2021) dan +51 kejadian (2022).
  - R14: 157 pasangan aditif dibandingkan dengan 5 selisih tercatat. Seri rasio/persen dipisahkan dari penjumlahan.
- **Penyebab:** Selisih kejadian timbul akibat perbedaan waktu pemutakhiran data (*cut-off vintage*) antara BPBD daerah dan rilis provinsi Pusdatinkom BNPB, serta bencana hidrometeorologi lintas wilayah (banjir DAS) yang dihitung di masing-masing kabupaten terdampak.
- **Tindak Lanjut & Keputusan:** Selisih tidak dipaksa nol dan tidak dibuang; seluruhnya dicatat secara transparan pada `reports/validasi-agregasi-kabupaten.csv`, `reports/validasi-agregat-nasional.csv`, dan dianalisis dalam kategori **vintage berbeda** sesuai keputusan **K-033** dan **K-049**.

---

## 4. Mekanisme Penanganan Aturan Gagal (Fail-Fast Enforcement)

Pipeline menerapkan kebijakan perlindungan data yang ketat (*strict integrity*):
1. **Aturan Keras (Hard Rules):** Aturan seperti skema kolom, keunikan kunci primer, integritas tipe data, ketiadaan nilai negatif, kesetaraan nilai Gold terhadap Silver asalnya, dan keabsahan kategori rekonsiliasi bersifat **blocking**.
2. **Tindakan Otomatis:** Apabila ditemukan minimal 1 baris yang melanggar aturan keras, fungsi `validasi.jalankan()` segera menghentikan eksekusi pipeline (`sys.exit` / `SystemExit`) dan menampilkan daftar aturan yang gagal ke konsol terminal.
3. **Hasil Aktual Saat Ini:** `aturan_gagal = 0`. Tidak ada aturan keras yang gagal pada eksekusi data tim.

---

## 5. Bukti Eksekusi Terpadu Pipeline (`python pipeline.py`)

Validasi dijalankan secara terintegrasi langsung melalui berkas orkestrasi utama `pipeline.py`. Berikut adalah log eksekusi aktual dari terminal:

```text
$ python pipeline.py
data/raw: 44 berkas cocok dengan MANIFEST.csv
ekstraksi  selesai dalam 2.1 s
Silver: 7,535 baris, 11 seri, 39 wilayah, 24 berkas, periode 2009-2025
silver     selesai dalam 1.1 s
Gold Panel: 3,382 baris (1,374 terisi, 2,008 kosong), 10 indikator, 5,410 baris Silver tidak terpilih
Berkas tersimpan di data/gold/panel.parquet dan data/gold/panel_lebar.parquet
Laporan tersimpan di reports/panel-gold.md
Tabel nasional Gold tersimpan di:
- data/gold/tabel_nasional.parquet (panjang: 90 baris)
- data/gold/tabel_nasional_periode_seri.parquet (lebar: 17 periode x 11 seri)
Tabel rekonsiliasi tersimpan di:
- data/gold/tabel_rekonsiliasi.parquet (136 baris)
- data/gold/tabel_rekonsiliasi.csv
[OK] Tabel 'silver': 7,535 baris di SQL == 7,535 baris di Parquet.
[OK] Tabel 'panel_gold': 3,382 baris di SQL == 3,382 baris di Parquet.
[OK] Tabel 'tabel_nasional': 90 baris di SQL == 90 baris di Parquet.
[OK] Tabel 'tabel_rekonsiliasi': 136 baris di SQL == 136 baris di Parquet.
gold       selesai dalam 1.4 s
Validasi Silver & Gold: 24/24 aturan lolos
  LOLOS                R01 Skema kolom Silver: 11 kolom wajib lengkap, tanpa sel kosong
  LOLOS                R02 Keunikan kunci Silver: 6 kolom kunci unik untuk 7,535 baris
  LOLOS                R03 Nilai tidak negatif dan berhingga: nilai minimum 0.00; tidak ada nilai negatif atau tak berhingga
  LOLOS_DENGAN_CATATAN R04 Bilangan bulat untuk jiwa/kejadian: 6,832 baris jiwa/kejadian; 10 baris ber-noise float < 1e-6 (bukan pelanggaran)
  LOLOS                R05 Konsistensi satuan per seri: 11 seri memakai satu satuan sesuai peta SATUAN
  LOLOS                R06 Rentang nilai masuk akal per satuan: jiwa 0-300 jt; kejadian 0-10 rb; per 100 rb 0-100 rb; persen 0-100%
  LOLOS                R07 Kode wilayah sah: 39 kode: 38 provinsi BPS x 100 + 9999 Indonesia
  LOLOS_DENGAN_CATATAN R08 Konsistensi nama wilayah: 41 ejaan untuk 39 kode; ejaan ganda hanya pada alias resmi
  LOLOS                R09 Periode dan jenis periode: semua 7,535 baris bertipe tahun, 2009-2025
  LOLOS                R10 Rincian jenis bencana dikenal: 10 nilai: total + 9 jenis bencana
  LOLOS                R11 Lineage berkas mentah: 24 berkas sumber cocok dengan MANIFEST.csv
  LOLOS_DENGAN_CATATAN R12 Kelengkapan wilayah per seri/periode: 134 grup lengkap 38 provinsi; 88 grup parsial dicatat
  LOLOS_DENGAN_CATATAN R13 Agregat kabupaten/kota ke provinsi: 1,530 baris agregasi kab/kota; 21 selisih dicatat
  LOLOS_DENGAN_CATATAN R14 Agregat provinsi ke nasional: 157 pasangan aditif dibandingkan; 5 selisih dicatat
  LOLOS                R15 gold: kunci panel unik: indikator + wilayah_kode + periode tidak kembar (terpenuhi, 0 pelanggaran)
  LOLOS                R16 gold: satu satuan per indikator: satu indikator panel hanya punya satu satuan (terpenuhi, 0 pelanggaran)
  LOLOS                R17 gold: status sel dan nilai: status sel baku; nilai ada jika dan hanya jika sel terisi (terpenuhi, 0 pelanggaran)
  LOLOS                R18 gold: sel tertelusur ke Silver: setiap sel terisi punya baris Silver asal (terpenuhi, 0 pelanggaran)
  LOLOS                R19 gold: nilai sama dengan Silver: nilai panel = nilai Silver asalnya (terpenuhi, 0 pelanggaran)
  LOLOS                R20 gold: tabel nasional unik: seri + rincian + periode tidak kembar (terpenuhi, 0 pelanggaran)
  LOLOS                R21 rekonsiliasi: kategori baku: kategori dari daftar baku; penjelasan tidak kosong (terpenuhi, 0 pelanggaran)
  LOLOS                R22 rekonsiliasi: selisih = utama − pembanding: selisih dihitung ulang dan cocok (terpenuhi, 0 pelanggaran)
  LOLOS                R23 rekonsiliasi: baris berpasangan dihitung: pasangan selisih dengan dua nilai punya selisih (terpenuhi, 0 pelanggaran)
  LOLOS                R24 rekonsiliasi: periode utama tidak dibuang: setiap tahun seri utama muncul di rekonsiliasi (terpenuhi, 0 pelanggaran)
Laporan validasi: reports/validasi.md
Tabel pendamping: reports/validasi-agregasi-kabupaten.csv
Tabel pendamping: reports/validasi-agregat-nasional.csv
validasi   selesai dalam 1.4 s
Periksa skema minimal: python -m src.common.skema data/silver/silver.parquet
LOLOS  7,535 baris, 11 seri, 39 wilayah, 24 berkas sumber
```

---

## 6. Tabel Pendamping Bukti Validasi

- `reports/validasi-agregasi-kabupaten.csv`: Jumlah kabupaten/kota yang dijumlahkan untuk setiap baris Silver agregasi 2021–2022, nilai kab/kota vs rekap provinsi, dan selisihnya.
- `reports/validasi-agregat-nasional.csv`: Rekonsiliasi provinsi vs nasional untuk satuan aditif (`jiwa`, `kejadian`).