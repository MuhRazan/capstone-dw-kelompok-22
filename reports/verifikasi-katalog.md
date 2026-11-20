# Verifikasi katalog seri (kartu #10)

Perintah: `python -m src.validasi.katalog`
Keluaran: 11 seri, 33 keputusan, 0 masalah.

ID log unik: 33 baris, tanpa ID ganda. Duplikat K-024..K-027 hasil merge lintas anggota dibersihkan, sehingga tiap koreksi punya satu entri.

## Tautan metadata per seri

| Seri | Sumber metadata |
|---|---|
| kejadian | [BNPB 2025](https://data.bnpb.go.id/dataset/58878b43-41b5-4ffb-b851-c6d8c8c4d438/resource/df39e8c3-117e-40fa-b518-ff1037743955/download/jumlah-kejadian-bencana-menurut-provinsi-2025.xlsx), [BNPB 2010-2024](https://data.bnpb.go.id/dataset/f61d78e5-04c6-4ce8-9acf-e425dadc1f4d/resource/5dfcae7e-acb3-4548-82b5-61d876ea478a/download/jumlah-kejadian-bencana-menurut-provinsi-tahun-2010-2024.xlsx), [2021](https://dibi.bnpb.go.id/dataset/jumlah-kejadian-dan-dampak-bencana-tahun-2021), [2022](https://dibi.bnpb.go.id/dataset/jumlah-kejadian-dan-dampak-bencana-tahun-2022) |
| korban_meninggal | [BNPB 2025](https://data.bnpb.go.id/dataset/58878b43-41b5-4ffb-b851-c6d8c8c4d438/resource/aefe8331-5962-4610-8b0c-2de637a336cd/download/jumlah-korban-meninggal-akibat-bencana-menurut-provinsi-2025.xlsx), [BNPB 2010-2024](https://data.bnpb.go.id/dataset/f61d78e5-04c6-4ce8-9acf-e425dadc1f4d/resource/b2fa5c46-9a07-4d30-a3bd-57e143e775f1/download/jumlah-korban-meninggal-dunia-akibat-bencana-tahun-2010-2024.xlsx) |
| korban_hilang | [BNPB 2025](https://data.bnpb.go.id/dataset/58878b43-41b5-4ffb-b851-c6d8c8c4d438/resource/f1de565c-c028-43e7-a48d-109ebb8f3081/download/jumlah-korban-hilang-akibat-bencana-menurut-provinsi-2025.xlsx), [BNPB 2010-2024](https://data.bnpb.go.id/dataset/f61d78e5-04c6-4ce8-9acf-e425dadc1f4d/resource/a19366cf-0ac4-45d1-bc6e-89a020ab45a1/download/jumlah-korban-hilang-akibat-bencana-tahun-2010-2024.xlsx) |
| korban_luka_sakit | [BNPB 2025](https://data.bnpb.go.id/dataset/58878b43-41b5-4ffb-b851-c6d8c8c4d438/resource/50b99a45-d8ff-496e-a64f-9e689754371c/download/jumlah-korban-luka-akibat-bencana-menurut-provinsi-2025.xlsx), [BNPB 2010-2024](https://data.bnpb.go.id/dataset/f61d78e5-04c6-4ce8-9acf-e425dadc1f4d/resource/ce67795b-57e4-4c84-8c2a-3bf03828ff0d/download/jumlah-korban-luka-akibat-bencana-tahun-2010-2024.xlsx) |
| korban_mengungsi | [BNPB 2025](https://data.bnpb.go.id/dataset/58878b43-41b5-4ffb-b851-c6d8c8c4d438/resource/eefa5746-5c65-4156-ac74-2eff2bfac767/download/jumlah-korban-mengungsi-akibat-bencana-menurut-provinsi-2025.xlsx), [BNPB 2010-2024](https://data.bnpb.go.id/dataset/f61d78e5-04c6-4ce8-9acf-e425dadc1f4d/resource/d7b61b56-43d5-4dcc-8d7b-45c993e1bdb0/download/jumlah-korban-mengungsi-akibat-bencana-tahun-2010-2024.xlsx) |
| korban_terdampak | [BNPB 2025](https://data.bnpb.go.id/dataset/58878b43-41b5-4ffb-b851-c6d8c8c4d438/resource/8d8db1c8-d79b-4fb1-b735-d8b9c1e0517a/download/jumlah-korban-terdampak-akibat-bencana-menurut-provinsi-2025.xlsx), [BNPB 2010-2024](https://data.bnpb.go.id/dataset/f61d78e5-04c6-4ce8-9acf-e425dadc1f4d/resource/7f9e5218-bbba-4916-a2b8-13cf1764dc96/download/jumlah-korban-terdampak-akibat-bencana-tahun-2010-2024.xlsx) |
| korban_terdampak_mengungsi | [2021](https://dibi.bnpb.go.id/dataset/jumlah-kejadian-dan-dampak-bencana-tahun-2021), [2022](https://dibi.bnpb.go.id/dataset/jumlah-kejadian-dan-dampak-bencana-tahun-2022) |
| korban_mengungsi_per_100rb | [BNPB 2025](https://data.bnpb.go.id/dataset/58878b43-41b5-4ffb-b851-c6d8c8c4d438/resource/31a0d329-a363-4a16-852c-f4fa51f313bf/download/jumlah-korban-mengungsi-per-100.000-orang-akibat-bencana-menurut-provinsi-2025.xlsx) |
| korban_meninggal_hilang_per_100rb | [BNPB 2025](https://data.bnpb.go.id/dataset/58878b43-41b5-4ffb-b851-c6d8c8c4d438/resource/f800105c-ac2f-4b47-b097-0cd4f5d63b82/download/jumlah-korban-meninggal-dan-hilang-per-100.000-orang-akibat-bencana-menurut-provinsi-2025.xlsx) |
| jumlah_penduduk | [BNPB 2025](https://data.bnpb.go.id/dataset/58878b43-41b5-4ffb-b851-c6d8c8c4d438/resource/31a0d329-a363-4a16-852c-f4fa51f313bf/download/jumlah-korban-mengungsi-per-100.000-orang-akibat-bencana-menurut-provinsi-2025.xlsx) (kolom `Jumlah Penduduk`) |
| EN.CLC.MDAT.ZS | [WDI API](https://api.worldbank.org/v2/indicator/EN.CLC.MDAT.ZS?format=json), [laman indikator](https://data.worldbank.org/indicator/EN.CLC.MDAT.ZS) |

Kode SDG 13.1.1 / 1.5.1 / 11.5.1 menaut ke metadata UNSD:
[13.1.1](https://unstats.un.org/sdgs/metadata/files/Metadata-13-01-01.pdf),
[1.5.1](https://unstats.un.org/sdgs/metadata/files/Metadata-01-05-01.pdf),
[11.5.1](https://unstats.un.org/sdgs/metadata/files/Metadata-11-05-01.pdf).

## Koreksi katalog yang tercatat

| Log | Seri | Koreksi |
|---|---|---|
| K-017 | semua | Satuan diverifikasi ke berkas mentah; katalog awal benar untuk 10 seri BNPB |
| K-018 | EN.CLC.MDAT.ZS | Satuan dikoreksi jadi `persen_penduduk` |
| K-028 | korban_terdampak | Katalog awal salah menunjuk `Korban Terdampak - Mengungsi`; itu milik `korban_terdampak_mengungsi` |
| K-029 | jumlah_penduduk | Placeholder `{REKAP}` diganti berkas kanonik `31a0d329-...` |
| K-030 | EN.CLC.MDAT.ZS | Periode ditandai `rerata_1990_2009`, bukan tahun 2009 tunggal |
| K-031 | semua | `sumber_sdg` tidak lagi hanya `data/KASUS.md`; tiap seri punya URL metadata |

## Pemeriksaan periode

`python -m src.validasi.katalog` menolak bila:

1. ada seri tanpa `url_metadata` atau `url_sdg`;
2. ada kode `K-xxx` di katalog yang tidak ada di `log-keputusan.csv`;
3. `EN.CLC.MDAT.ZS` tidak berlabel `rerata_1990_2009`;
4. Silver punya baris duplikat pada `(seri_kode, wilayah_kode, periode, rincian, sumber, _berkas_raw)`;
5. `EN.CLC.MDAT.ZS` tidak tepat 1 baris atau periodenya bukan `2009`.

Poin 3–5 mencegah nilai rerata 1990-2009 diulang per tahun atau dirata-ratakan lagi.
