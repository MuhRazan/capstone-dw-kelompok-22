# Uji pembaca ekstraksi (kartu #3 dan #4)

Perintah dan keluaran asli. Setiap baris membawa `_berkas_raw` dan `_sha256_raw`;
lineage dicek dengan `src/common/manifest.py`.

## #3 Pembaca BNPB JSON (27 berkas)

Perintah: `python -m src.ekstraksi.bnpb_json --akar data/raw/bnpb/2026-10-20`

```
Total berkas terbaca: 27; galat: 0
Total baris bnpb_json: 12875
```

Tabel per berkas (`| berkas | seri | baris |`) tercetak oleh perintah; rekap:
- 27 berkas JSON, 0 galat.
- 26 resource `datastore` (15 dari `data-bencana-indonesia` + 11 dari
  `kompilasi-data-jumlah-dan-dampak-kejadian-bencana-2024`) + 1
  `package_search` CKAN.
- Seri utama yang muncul: kejadian, korban_meninggal, korban_hilang, korban_luka_sakit,
  korban_terdampak, korban_mengungsi (beberapa resource juga membawa seri lain,
  tetapi ekstraksi memfilter ke 10 seri yang didefinisikan).
- Tiap baris membawa `_berkas_raw` dan `_sha256_raw`.

## #4 Pembaca WDI (4 berkas)

Perintah: `python -m src.ekstraksi.wdi`

```
| berkas | jenis | baris | baris_mentah | sha256 |
|---|---|---|---|---|
| wdi/2026-10-20/data/kelompok-01-hal-01.json | data | 66 | 3960 | 8d2fae3a9641 |
| wdi/2026-10-20/metadata/sumber.json | metadata | 71 | 71 | eeef380bb108 |
| wdi/2026-10-20/metadata/sumber2_indikator.json | metadata | 1498 | 1498 | 93874b457526 |
| wdi/2026-10-20/metadata/sumber46_indikator.json | metadata | 408 | 408 | 899b4a45ea57 |
Total baris: 2043
```

66 baris data (seri EN.CLC.MDAT.ZS) + 1.977 baris metadata = 2.043, sesuai K-013
(66 + 1.977). `baris_mentah` untuk data = 3.960 observasi WDI, disaring ke seri ini.

## Rekonsiliasi #5

```
bnpb_xlsx  36156
bnpb_json  12875
wdi_data      66
wdi_metadata 1977
----------------
total      51074
```

Semua angka di atas diambil dari keluaran perintah di atas, bukan dari tulisan tangan.
Kode pembaca JSON/CKAN/WDI milik Harvinsyah (commit `0d00d66`); perintah dijalankan di
atas `main` / `124450031/kerja` (sudah merge main).
