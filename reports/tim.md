# Laporan tim — <Nama tim>, kasus <NN> <judul kasus>

Satu dokumen bersama, enam bagian. Angka harus dapat ditarik ulang dari `data/silver`, `data/gold`,
dan `log-keputusan.csv` yang sudah di-*commit*.

## Ringkasan
Kasus, seri yang ditangani, dan satu kalimat temuan utama tentang kualitas datanya.

## Data dan lineage
Sumber dan format mentah, jumlah berkas, cara `_berkas_raw`/`_sha256_raw` dibentuk, dan hasil tarik
ulang API (bila dilakukan): apa yang berubah sejak snapshot 17–20 Oktober 2026.

## Masalah data dan penanganannya
Tabel masalah yang ditemukan (missing, outlier, patahan seri, duplikat, format, wilayah) dengan
jumlah baris terdampak, keputusan, dan alternatif yang ditolak. Rujuk id di `log-keputusan.csv`.

## Integrasi dan rekonsiliasi
Seri utama vs pembanding nasional: selisih, penjelasannya (definisi, metode, vintage, granularitas),
dan hasil analisis revisi dari arsip WDI. Lihat dokumen lengkap di [reports/rekonsiliasi.md](file:///c:/Users/HP/workbench-workspace/capstone-data-wrangling/reports/rekonsiliasi.md) serta tabel nasional periode × seri di `reports/tabel_nasional_periode_seri.csv`.

## Validasi dan reproduksibilitas
Skema validasi (aturan, hasil lolos/gagal), waktu `python pipeline.py` dari nol, perbandingan pandas
vs DuckDB/Dask, dan keterbatasan yang tersisa.

## Pembagian kerja
| Anggota | NIM | Komponen | Tugas sampingan | Bagian laporan yang ditulis |
|---|---|---|---|---|
| Muhammad Razan Maulana Pratama | 124450031 | Transformasi dan panel | Koordinator | Ringkasan, Struktur Silver |
| Charrlindah | 124450037 | Profil dan pembersihan | Profiling | Masalah data dan penanganannya |
| Nazlah Auliya | 124450054 | Validasi dan dokumentasi | Quality Assurance | Validasi dan reproduksibilitas |
| Muhammad Rafka Fatih A | 124450089 | Integrasi, penyimpanan, dan skala | Integrator | Integrasi dan rekonsiliasi |
| Muhammad Harvinsyah | 124450107 | Ekstraksi dan lineage | Data Engineer | Data dan lineage |
| Cika Adelia Br Marbun | 124450128 | Ekstraksi format | Data Engineer | Ekstraksi WDI dan pembaca berkas |
