# Panel Gold provinsi x periode x indikator

Dihasilkan otomatis oleh `python pipeline.py` (`src/gold/panel.py`) dari Silver, grid kelengkapan, dan penanda anomali Sprint 1.

## Aturan satu nilai per sel

1. **Snapshot**: Bila terdapat lebih dari satu snapshot data, snapshot terbaru (20 Oktober) diutamakan.
2. **Rincian**: Satu indikator = satu deret agregat utama ('total' bila tersedia, atau jumlahan semua bencana 'jumlah' per berkas). Rincian jenis bencana individual tetap tersimpan di Silver untuk keperluan audit.
3. **Berkas**: Bila satu sel memiliki data dari beberapa berkas, URUTAN_BERKAS memilih berkas prioritas kanonik.
4. **Periode**: Disimpan apa adanya sesuai format ISO; tidak dilakukan perataan sub-tahunan ke tahunan secara diam-diam.
5. **Penanda**: Outlier asli, patahan wilayah, dan galat input dari Sprint 1 dipertahankan nilainya dan dicatat pada kolom `penanda`.
6. **Kolom Turunan**: Tersedia `nilai_per_100rb` (normalisasi rasio per 100 ribu penduduk) dan `nilai_log1p` (transformasi logaritma log(1+x)) untuk analisis distribusi skewed, sementara `nilai` asli tetap tersimpan utuh.

**Baris Silver provinsi yang tidak terpilih masuk panel utama (rincian per bencana atau berkas non-kanonik)**: 5,410 baris.

## Ringkasan Indikator Panel

| indikator | satuan | periode | jumlah_periode | sel | terisi | ditandai |
| --- | --- | --- | --- | --- | --- | --- |
| jumlah_penduduk | jiwa | 2025 | 1 | 38 | 38 | 0 |
| kejadian [jumlah] | kejadian | 2010–2025 | 16 | 608 | 608 | 62 |
| korban_hilang [jumlah] | jiwa | 2010–2025 | 16 | 608 | 144 | 21 |
| korban_luka_sakit [jumlah] | jiwa | 2010–2025 | 16 | 608 | 144 | 10 |
| korban_mengungsi [jumlah] | jiwa | 2010–2025 | 16 | 608 | 76 | 3 |
| korban_mengungsi_per_100rb [jumlah] | per_100000_penduduk | 2025 | 1 | 38 | 38 | 1 |
| korban_meninggal [jumlah] | jiwa | 2021–2025 | 4 | 152 | 144 | 10 |
| korban_meninggal_hilang_per_100rb [jumlah] | per_100000_penduduk | 2025 | 1 | 38 | 38 | 5 |
| korban_terdampak [jumlah] | jiwa | 2010–2025 | 16 | 608 | 76 | 3 |
| korban_terdampak_mengungsi [jumlah] | jiwa | 2021–2022 | 2 | 76 | 68 | 4 |

## Distribusi Status Sel

| indikator | belum_ada | terisi | tidak_diterbitkan |
| --- | --- | --- | --- |
| jumlah_penduduk | 0 | 38 | 0 |
| kejadian [jumlah] | 0 | 608 | 0 |
| korban_hilang [jumlah] | 55 | 144 | 409 |
| korban_luka_sakit [jumlah] | 55 | 144 | 409 |
| korban_mengungsi [jumlah] | 55 | 76 | 477 |
| korban_mengungsi_per_100rb [jumlah] | 0 | 38 | 0 |
| korban_meninggal [jumlah] | 8 | 144 | 0 |
| korban_meninggal_hilang_per_100rb [jumlah] | 0 | 38 | 0 |
| korban_terdampak [jumlah] | 55 | 76 | 477 |
| korban_terdampak_mengungsi [jumlah] | 8 | 68 | 0 |

Keterangan status sel: `terisi` = observasi riil tersedia; `tidak_diterbitkan` = belum diterbitkan oleh BNPB per provinsi; `belum_ada` = provinsi pemekaran baru belum dibentuk.

## Berkas Keluaran

- `data/gold/panel.parquet`: 3,382 baris (format panjang, memuat sel terisi dan sel kosong berstatus).
- `data/gold/panel_lebar.parquet`: 608 baris x 14 kolom (format lebar untuk pemodelan dan regresi).