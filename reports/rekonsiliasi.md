# Laporan Integrasi dan Rekonsiliasi (Tahap 6 — Kasus 22: Korban Bencana)

Dokumen ini memuat tabel rekonsiliasi analitik nasional Gold, perbandingan seri utama terhadap seri pembanding, analisis selisih, dan klasifikasi kategori penjelasan sesuai panduan kelompok bagian 3.

---

## 1. Arsitektur Tabel Rekonsiliasi Nasional Gold

Tabel rekonsiliasi analitik dibentuk langsung dari tabel nasional Gold melalui modul [src/gold/rekonsiliasi.py](file:///c:/Users/HP/workbench-workspace/capstone-data-wrangling/src/gold/rekonsiliasi.py) yang dieksekusi otomatis oleh `python pipeline.py`.

* **Format Berkas:**
  * Parquet: `data/gold/tabel_rekonsiliasi.parquet` (136 baris)
  * CSV: `data/gold/tabel_rekonsiliasi.csv`
  * Tabel SQL Relasional: `tabel_rekonsiliasi` dan view `rekonsiliasi` di `data/gold/gold.sqlite`
* **Struktur Kolom:**
  * `periode`: Tahun observasi (string 4 digit: 2009 s.d. 2025). Seluruh 17 periode tetap tampil.
  * `pasangan_id`: Kode unik pasangan rekonsiliasi (`P1_RASIO_100RB`, `P2_KAB_VS_PROVINSI`, `P3_BNPB_VS_WDI`).
  * `nama_pasangan`: Nama pasangan rekonsiliasi.
  * `seri_kode`: Kode indikator yang dibandingkan.
  * `nilai_seri_utama` (alias `nilai_utama`): Nilai numerik seri utama kelompok.
  * `nilai_pembanding`: Nilai numerik dari seri pembanding resmi.
  * `selisih`: Nilai selisih eksak ($\text{nilai\_seri\_utama} - \text{nilai\_pembanding}$). Nilai asli tidak dihapus dan tidak dipaksa nol.
  * `satuan`: Satuan ukuran (`per_100000_penduduk`, `kejadian`, `jiwa`, `persen_penduduk`).
  * `kategori_penjelasan` (alias `kategori`): Klasifikasi baku keterbandingan data (*definisi berbeda*, *metode berbeda*, *vintage berbeda*, *cakupan berbeda*, atau *belum terjelaskan*).
  * `catatan`: Narasi konteks, dugaan penyebab, dan bukti audit lapangan.

---

## 2. Rincian 3 Pasangan Rekonsiliasi Kasus 22

### Pasangan 1: Angka per 100 Ribu Penduduk (Hitungan Kelompok vs Terbitan BNPB)
* **Pasangan ID:** `P1_RASIO_100RB`
* **Seri yang dibandingkan:**
  1. `korban_mengungsi_per_100rb`: Hitungan $\left(\frac{\text{korban\_mengungsi}}{\text{jumlah\_penduduk}} \times 100.000\right)$ vs Nilai Terbitan BNPB.
  2. `korban_meninggal_hilang_per_100rb`: Hitungan $\left(\frac{\text{korban\_meninggal} + \text{korban\_hilang}}{\text{jumlah\_penduduk}} \times 100.000\right)$ vs Nilai Terbitan BNPB.
* **Ketersediaan Periode:** Tahun **2025** (1 periode beririsan langsung; 2009–2024 berstatus *cakupan berbeda*).
* **Evaluasi Hasil Rekonsiliasi:**
  * **Mengungsi / 100rb (2025):**
    $$\text{Hitungan Kelompok} = \frac{1.154.803}{284.438.800} \times 100.000 = 405,993486$$
    $$\text{Terbitan Resmi BNPB} = 405,993486 \implies \mathbf{Selisih = 0,000000}$$
    *Kategori:* **metode berbeda** (rumus kelompok terverifikasi konsisten sempurna dengan metodologi pembobotan agregasi BPS/BNPB).
  * **Meninggal & Hilang / 100rb (2025):**
    $$\text{Hitungan Kelompok} = \frac{1.666 + 214}{284.438.800} \times 100.000 = \frac{1.880}{284.438.800} \times 100.000 = 0,660951$$
    $$\text{Terbitan Resmi BNPB} = 0,660951 \implies \mathbf{Selisih = 0,000000}$$
    *Kategori:* **metode berbeda** (metodologi perhitungan kelompok terbukti identik).
  * **Periode 2009–2024:**
    *Kategori:* **cakupan berbeda** (BNPB tidak menerbitkan data populasi resmi dan rasio per 100 ribu penduduk pada publikasi pra-2025).

---

### Pasangan 2: Agregasi Kabupaten/Kota vs Rekapitulasi Tingkat Provinsi BNPB
* **Pasangan ID:** `P2_KAB_VS_PROVINSI`
* **Seri yang dibandingkan:** `kejadian`, `korban_meninggal`, `korban_hilang`, `korban_luka_sakit`, `korban_terdampak_mengungsi`.
* **Ketersediaan Periode:** Tahun **2021** dan **2022** (2 periode beririsan langsung; 2009–2020 dan 2023–2025 berstatus *cakupan berbeda*).
* **Evaluasi Hasil Rekonsiliasi:**
  * **Tahun 2021:**
    * `korban_meninggal`: 728 vs 728 $\implies$ Selisih = 0 (**metode berbeda**)
    * `korban_hilang`: 87 vs 87 $\implies$ Selisih = 0 (**metode berbeda**)
    * `korban_luka_sakit`: 14.915 vs 14.915 $\implies$ Selisih = 0 (**metode berbeda**)
    * `korban_terdampak_mengungsi`: 8.265.462 vs 8.265.462 $\implies$ Selisih = 0 (**metode berbeda**)
    * `kejadian`: 5.451 vs 5.402 $\implies$ **Selisih = +49 kejadian** (**vintage berbeda**)
  * **Tahun 2022:**
    * `korban_meninggal`: 858 vs 858 $\implies$ Selisih = 0 (**metode berbeda**)
    * `korban_hilang`: 37 vs 37 $\implies$ Selisih = 0 (**metode berbeda**)
    * `korban_luka_sakit`: 8.733 vs 8.733 $\implies$ Selisih = 0 (**metode berbeda**)
    * `korban_terdampak_mengungsi`: 6.087.878 vs 6.087.878 $\implies$ Selisih = 0 (**metode berbeda**)
    * `kejadian`: 3.595 vs 3.544 $\implies$ **Selisih = +51 kejadian** (**vintage berbeda**)
* **Dugaan dan Bukti Keterbandingan Selisih Kejadian:**
  * *Dugaan:* Selisih 49 kejadian (2021) dan 51 kejadian (2022) timbul akibat perbedaan waktu pemutakhiran data (*cut-off vintage*). Pusdatinkom BNPB merilis rekapitulasi tingkat provinsi sebelum seluruh laporan rekonsiliasi daerah dari BPBD kabupaten/kota terhimpun secara lengkap, atau terdapat bencana hidrometeorologi lintas wilayah (misal banjir DAS lintas 2–3 kabupaten) yang dicatat per kabupaten oleh BPBD setempat namun diagregasi sebagai 1 klaster bencana oleh provinsi.
  * *Bukti yang dicari:* Audit silsilah pada `reports/validasi-agregasi-kabupaten.csv` mengonfirmasi bahwa 1.503 dari 1.530 baris (98,2%) cocok sempurna, dan selisih hanya terkonsentrasi pada beberapa kabupaten perbatasan/pemekaran.

---

### Pasangan 3: Seri Utama BNPB vs Seri Pembanding WDI (`EN.CLC.MDAT.ZS`)
* **Pasangan ID:** `P3_BNPB_VS_WDI`
* **Seri yang dibandingkan:**
  * Seri Pembanding WDI: `EN.CLC.MDAT.ZS` (*Droughts, floods, extreme temperatures % of population, average 1990-2009*).
  * Seri Utama BNPB: Persentase populasi terpapar/terdampak bencana nasional (SDG 13.1.1 / 1.5.1 / 11.5.1).
* **Ketersediaan Periode:**
  * WDI: Tahun **2009** (1 titik data snapshot historis).
  * BNPB: Tahun **2010 s.d. 2025**.
  * Periode beririsan langsung: **0 tahun** (WDI berakhir 2009, BNPB mulai 2010).
* **Evaluasi Hasil Rekonsiliasi & Komparasi Konteks:**
  * **Tahun 2009:** Nilai WDI = **0,16059%**, Nilai BNPB = null $\implies$ Kategori: **vintage berbeda** (WDI mendahului periode pencatatan BNPB).
  * **Tahun 2010–2024:** Nilai WDI = null $\implies$ Kategori: **vintage berbeda** (WDI tidak menerbitkan pembaruan tahunan pasca-2009).
  * **Tahun 2025 (Komparasi Konteks Bencana):**
    $$\text{Persentase Terdampak BNPB 2025} = \frac{10.955.315}{284.438.800} \times 100\% = 3,851554\%$$
    $$\text{Baseline WDI (1990–2009)} = 0,160590\% \implies \mathbf{Selisih = +3,690964\%}$$
    *Kategori:* **definisi berbeda**.
* **Catatan Keterbandingan:**
  * *Definisi:* WDI mengukur rerata persentase populasi yang terdampak oleh 3 jenis bencana iklim spesifik (kekeringan, banjir, dan suhu ekstrem) berdasarkan basis data CRED EM-DAT. Sebaliknya, BNPB mencatat seluruh korban jiwa akibat spektrum bencana hidrometeorologi dan geologi di seluruh Indonesia.
  * *Vintage & Konteks:* Indikator WDI mewakili *long-term baseline* pra-2010. Peningkatan angka paparan pada data BNPB 2025 (3,85% vs 0,16%) mencerminkan meningkatnya frekuensi anomali cuaca ekstrem serta membaiknya sistem pelaporan bencana daerah di bawah payung UU Penanggulangan Bencana No. 24/2007.

---

## 3. Distribusi Kategori Penjelasan dan Metrik Hasil

Dari 136 baris tabel rekonsiliasi nasional Gold (17 periode × 8 seri pasangan), distribusi kategori penjelasan terbagi sebagai berikut:

| Kategori Penjelasan | Jumlah Baris | Penjelasan Karakteristik |
|---|---|---|
| **cakupan berbeda** | 107 baris | Ketiadaan berkas/indikator pembanding pada periode tertentu (kab/kota di luar 2021–2022, rasio 100rb pra-2025). |
| **vintage berbeda** | 18 baris | Perbedaan waktu snapshot pelaporan WDI 1990–2009 vs BNPB 2010–2025, serta jeda pelaporan kejadian kab/kota. |
| **metode berbeda** | 10 baris | Kesesuaian metodologi hitungan rasio 100rb (selisih 0) dan agregasi dampak kab/kota vs provinsi 2021–2022. |
| **definisi berbeda** | 1 baris | Komparasi konteks WDI EM-DAT (bencana iklim) vs BNPB (seluruh bencana). |
| **Total** | **136 baris** | **100% baris memiliki kategori baku.** |

### Nilai Metrik Artefak Workbench (`results/124450089/metrics.json`)
* `pasangan_rekonsiliasi`: **3**
* `selisih_median`: **0.0** (dari 13 baris berpasangan yang memiliki selisih terisi, 10 baris memiliki selisih 0.0, sehingga median tepat **0.0**).
* `tabel_sql`: **4**
* `periode_beririsan`: **0**
