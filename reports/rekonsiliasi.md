# Tabel rekonsiliasi seri utama vs pembanding nasional

Dihasilkan `python pipeline.py` (`src/gold/rekonsiliasi.py`) dari `data/gold/nasional.parquet`. Selisih = nilai utama − nilai pembanding; selisih relatif dalam persen terhadap pembanding. Periode tanpa pasangan tetap ditampilkan. Selisih tidak dihapus dan tidak dipaksa sama.

## Ringkasan per pasangan

| pasangan_id | seri_pembanding | jenis | periode | berpasangan | selisih_dihitung | median_selisih | median_selisih_relatif | kategori |
|---|---|---|---|---|---|---|---|---|
| P4 | korban_terdampak | konteks | 1 | 0 | 0 |  |  | definisi berbeda (1) |

Tidak ada baris yang selisihnya dapat dihitung.

Periode pembanding di luar rentang seri utama yang tidak ditulis: tidak ada.

## Kategori

Kategori baku: *definisi berbeda*, *metode berbeda*, *vintage berbeda*, *cakupan berbeda*, *belum terjelaskan*, *tanpa pasangan*, *tidak berselisih*. Kategori pasangan ditetapkan dari bukti di pasangan rekonsiliasi Sprint 1 (`reports/pasangan-rekonsiliasi.md`); baris satu sisi menjadi *tanpa pasangan*, baris yang angkanya sama menjadi *tidak berselisih*.

## Rincian per pasangan

### P1: Mengungsi per 100.000: angka BNPB vs dihitung ulang dari pengungsi dan penduduk

Jenis **selisih**; kategori pasangan: **metode berbeda**. Pembulatan atau penduduk berbeda; berkas pengungsi dan berkas per 100.000 terbit terpisah.

Rincian: banjir: jenis dengan pengungsi terbanyak 2025; jenis lain dihitung sama di Sprint 2.

_(kosong)_

### P2: Meninggal dan hilang per 100.000: angka BNPB vs (meninggal + hilang) / penduduk

Jenis **selisih**; kategori pasangan: **metode berbeda**. Pembulatan; pembilang dari dua berkas terpisah.

Rincian: banjir, sama dengan P1.

_(kosong)_

### P3: Kejadian banjir: baris INDONESIA vs jumlah 38 provinsi

Jenis **selisih**; kategori pasangan: **definisi berbeda**. Definisi penghitungan: kejadian lintas provinsi dihitung sekali secara nasional.

Rincian: baris INDONESIA di tabel per jenis dibandingkan dengan jumlah baris provinsi di berkas yang sama.

_(kosong)_

### P4: Penduduk terdampak kekeringan, banjir, suhu ekstrem (WDI): konteks

Jenis **konteks**; kategori pasangan: **definisi berbeda**. Periode tidak beririsan: WDI rata-rata 1990–2009, BNPB 2010–2025.

Rincian: WDI tanpa rincian; BNPB banjir sebagai contoh jenis yang tercakup.

| seri_pembanding | periode | nilai_utama | nilai_pembanding | selisih | selisih_relatif | asal | kategori | catatan |
|---|---|---|---|---|---|---|---|---|
| korban_terdampak | 2009 | 0.16 |  |  |  | hanya_utama | definisi berbeda | None |
