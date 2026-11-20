# Validasi Silver — Kasus 22 Korban Bencana

Dijalankan oleh `python pipeline.py` pada tahap `validasi` (tahap 8).

| Ringkasan | Nilai |
|---|---|
| Baris Silver | 7,535 |
| Seri | 11 |
| Wilayah | 39 |
| Berkas sumber | 24 |
| Periode | 2009–2025 |
| Sidik data mentah (`data_hash`) | `f26ed8682abbbc3496c256c56ac008f22b4bb473cd3ad9a34eb5b2f443a63b2f` |
| Aturan validasi | 14 |
| Lolos | 14 |
| Gagal | 0 |

Definisi status:

- **LOLOS** — aturan terpenuhi tanpa catatan.
- **LOLOS_DENGAN_CATATAN** — aturan terpenuhi; selisih/pengecualian yang memang diizinkan sudah dicatat di tabel pendamping.
- **GAGAL** — aturan dilanggar dan perlu diperbaiki. `aturan_lolos` menghitung LOLOS dan LOLOS_DENGAN_CATATAN.

| ID | Aturan | Status | Baris terdampak | Ringkasan |
|---|---|---|---|---|
| R01 | Skema kolom Silver | LOLOS | 0 | 11 kolom wajib lengkap, tanpa sel kosong |
| R02 | Keunikan kunci Silver | LOLOS | 0 | 6 kolom kunci unik untuk 7,535 baris |
| R03 | Nilai tidak negatif dan berhingga | LOLOS | 0 | nilai minimum 0.00; tidak ada nilai negatif atau tak berhingga |
| R04 | Bilangan bulat untuk jiwa/kejadian | LOLOS_DENGAN_CATATAN | 0 | 6,832 baris jiwa/kejadian; 10 baris ber-noise float < 1e-6 (bukan pelanggaran) |
| R05 | Konsistensi satuan per seri | LOLOS | 0 | 11 seri memakai satu satuan sesuai peta SATUAN; satuan: jiwa, kejadian, per_100000_penduduk, persen_penduduk |
| R06 | Rentang nilai masuk akal per satuan | LOLOS | 0 | jiwa 0.00-284,438,800.00 (batas 0-300,000,000); kejadian 0.00-4,727.00 (batas 0-10,000); per_100000_penduduk 0.00-16,836.54 (batas 0-100,000); persen_penduduk 0.16-0.16 (batas 0-100) |
| R07 | Kode wilayah sah | LOLOS | 0 | 39 kode: 38 provinsi BPS x 100 + 9999 Indonesia |
| R08 | Konsistensi nama wilayah | LOLOS_DENGAN_CATATAN | 0 | 41 ejaan untuk 39 kode; ejaan ganda hanya pada alias resmi |
| R09 | Periode dan jenis periode | LOLOS | 0 | semua 7,535 baris bertipe tahun, 2009-2025 |
| R10 | Rincian jenis bencana dikenal | LOLOS | 0 | 10 nilai: total + 9 jenis bencana |
| R11 | Lineage berkas mentah | LOLOS | 0 | 24 berkas sumber cocok dengan MANIFEST.csv |
| R12 | Kelengkapan wilayah per seri/periode | LOLOS_DENGAN_CATATAN | 1,692 | 134 grup lengkap 38 provinsi; 88 grup parsial dicatat (hanya provinsi yang punya kejadian) |
| R13 | Agregat kabupaten/kota ke provinsi | LOLOS_DENGAN_CATATAN | 21 | 1,530 baris agregasi kab/kota; 21 selisih dicatat; 76 baris total provinsi tanpa rincian kab/kota |
| R14 | Agregat provinsi ke nasional | LOLOS_DENGAN_CATATAN | 5 | 157 pasangan aditif dibandingkan; 5 selisih dicatat; 3 seri rasio/persen tidak dijumlahkan |

## Catatan dan selisih

### R08 — Konsistensi nama wilayah

- 3400: alias resmi ['DAERAH ISTIMEWA YOGYAKARTA', 'DI YOGYAKARTA']
- 9100: alias resmi ['P A P U A', 'PAPUA']

### R12 — Kelengkapan wilayah per seri/periode

- kejadian 2021 banjir: 34 provinsi
- kejadian 2021 cuaca_ekstrem: 34 provinsi
- kejadian 2021 erupsi_gunung_api: 1 provinsi
- kejadian 2021 gelombang_pasang_dan_abrasi: 23 provinsi
- kejadian 2021 gempabumi: 13 provinsi
- kejadian 2021 kebakaran_hutan_dan_lahan: 21 provinsi
- kejadian 2021 kekeringan: 5 provinsi
- kejadian 2021 tanah_longsor: 34 provinsi
- kejadian 2022 banjir: 34 provinsi
- kejadian 2022 cuaca_ekstrem: 33 provinsi
- kejadian 2022 erupsi_gunung_api: 1 provinsi
- kejadian 2022 gelombang_pasang_dan_abrasi: 12 provinsi
- kejadian 2022 gempabumi: 16 provinsi
- kejadian 2022 kebakaran_hutan_dan_lahan: 16 provinsi
- kejadian 2022 kekeringan: 2 provinsi
- ... dan 73 grup parsial lain

### R13 — Agregat kabupaten/kota ke provinsi

- 2021 DKI JAKARTA kejadian/banjir: kab/kota 28 vs provinsi 20 (selisih +8)
- 2021 JAWA BARAT kejadian/gempabumi: kab/kota 2 vs provinsi 1 (selisih +1)
- 2021 DI YOGYAKARTA kejadian/gempabumi: kab/kota 2 vs provinsi 1 (selisih +1)
- 2021 JAWA TIMUR kejadian/gempabumi: kab/kota 28 vs provinsi 4 (selisih +24)
- 2021 BANTEN kejadian/banjir: kab/kota 60 vs provinsi 57 (selisih +3)
- 2021 BALI kejadian/gempabumi: kab/kota 3 vs provinsi 1 (selisih +2)
- 2021 NUSA TENGGARA TIMUR kejadian/gempabumi: kab/kota 3 vs provinsi 1 (selisih +2)
- 2021 SULAWESI TENGAH kejadian/gempabumi: kab/kota 3 vs provinsi 2 (selisih +1)
- 2021 SULAWESI BARAT kejadian/gempabumi: kab/kota 6 vs provinsi 3 (selisih +3)
- 2021 MALUKU kejadian/gempabumi: kab/kota 9 vs provinsi 6 (selisih +3)
- 76 baris total provinsi berasal dari rekap provinsi, bukan agregasi kab/kota

### R14 — Agregat provinsi ke nasional

- jumlah_penduduk 2025 total: provinsi 284,438,600.00 vs nasional 284,438,800.00 (selisih -200.00)
- kejadian 2021 gempabumi: provinsi 25.00 vs nasional 24.00 (selisih +1.00)
- kejadian 2022 gempabumi: provinsi 32.00 vs nasional 28.00 (selisih +4.00)
- kejadian 2024 gempabumi: provinsi 18.00 vs nasional 15.00 (selisih +3.00)
- kejadian 2025 gempabumi: provinsi 29.00 vs nasional 28.00 (selisih +1.00)
- 703 baris bersatuan per 100rb/persen dikecualikan karena tidak aditif antarwilayah

## Aturan gagal

Tidak ada aturan yang gagal.

## Tabel pendamping

- `reports/validasi-agregasi-kabupaten.csv` — jumlah kabupaten/kota yang dijumlahkan untuk setiap baris Silver hasil agregasi 2021–2022, nilai kabupaten/kota vs rekap provinsi, dan selisihnya.
- `reports/validasi-agregat-nasional.csv` — rekonsiliasi provinsi vs nasional untuk satuan aditif (`jiwa`, `kejadian`). Seri rasio/persen tidak dijumlahkan.
