# Laporan Rancangan Basis Data dan Penyimpanan SQL (Tahap 5 — Kasus 22: Korban Bencana)

Dokumen ini memuat perancangan skema SQL untuk tabel Silver, panel Gold, tabel nasional, dan tabel rekonsiliasi, implementasi pemuat data terpadu pada `pipeline.py`, alasan pemilihan basis data, serta perbandingannya dengan penyimpanan respons JSON mentah sebagai dokumen.

---

## 1. Rancangan Skema SQL (DDL Lengkap)

Skema tabel SQL dirancang dengan tipe data standar ANSI SQL, indeks relasional, dan penegakan kunci primer (*Primary Key*) komposit. Berkas DDL tersimpan di `src/gold/skema.sql`:

```sql
-- DDL Skema Basis Data Relasional SQL (Tahap 5 — Kasus 22: Korban Bencana)
-- Kompatibel dengan: SQLite, DuckDB, dan PostgreSQL

-- 1. Tabel Silver: Data observasi terstandarisasi 11 kolom wajib
CREATE TABLE IF NOT EXISTS silver (
    sumber TEXT NOT NULL,
    seri_kode TEXT NOT NULL,
    wilayah_kode INTEGER NOT NULL,
    nama_wilayah TEXT NOT NULL,
    periode TEXT NOT NULL,
    jenis_periode TEXT NOT NULL,
    rincian TEXT NOT NULL,
    nilai REAL NOT NULL,
    satuan TEXT NOT NULL,
    _berkas_raw TEXT NOT NULL,
    _sha256_raw TEXT NOT NULL,
    PRIMARY KEY (sumber, seri_kode, wilayah_kode, periode, rincian, _berkas_raw)
);
CREATE INDEX IF NOT EXISTS idx_silver_seri_periode ON silver (seri_kode, periode);
CREATE INDEX IF NOT EXISTS idx_silver_wilayah ON silver (wilayah_kode);

-- 2. Tabel Panel Gold: Panel provinsi x periode x indikator (format panjang)
CREATE TABLE IF NOT EXISTS panel_gold (
    indikator TEXT NOT NULL,
    seri_kode TEXT NOT NULL,
    rincian TEXT NOT NULL,
    rincian_kode INTEGER NOT NULL,
    wilayah_kode INTEGER NOT NULL,
    nama_wilayah TEXT NOT NULL,
    periode TEXT NOT NULL,
    jenis_periode TEXT NOT NULL,
    nilai REAL,
    nilai_per_100rb REAL,
    nilai_log1p REAL,
    satuan TEXT NOT NULL,
    status_sel TEXT NOT NULL,
    penanda TEXT,
    _berkas_raw TEXT,
    _sha256_raw TEXT,
    PRIMARY KEY (wilayah_kode, periode, seri_kode, rincian)
);
CREATE INDEX IF NOT EXISTS idx_panel_wilayah_periode ON panel_gold (wilayah_kode, periode);
CREATE INDEX IF NOT EXISTS idx_panel_seri ON panel_gold (seri_kode);
CREATE VIEW IF NOT EXISTS panel AS SELECT * FROM panel_gold;

-- 3. Tabel Nasional Gold: Baris nasional periode x seri dengan asal dan lineage
CREATE TABLE IF NOT EXISTS tabel_nasional (
    periode TEXT NOT NULL,
    seri_kode TEXT NOT NULL,
    nilai REAL NOT NULL,
    satuan TEXT NOT NULL,
    asal TEXT NOT NULL,
    aturan_agregat TEXT NOT NULL,
    _berkas_raw TEXT NOT NULL,
    PRIMARY KEY (periode, seri_kode)
);
CREATE INDEX IF NOT EXISTS idx_tabel_nasional_periode ON tabel_nasional (periode);

-- 4. Tabel Rekonsiliasi Gold: 3 Pasangan rekonsiliasi dan catatan keterbandingan
CREATE TABLE IF NOT EXISTS tabel_rekonsiliasi (
    pasangan_id TEXT NOT NULL,
    nama_pasangan TEXT NOT NULL,
    wilayah_kode INTEGER NOT NULL,
    nama_wilayah TEXT NOT NULL,
    periode TEXT NOT NULL,
    seri_kode TEXT NOT NULL,
    rincian TEXT NOT NULL,
    nilai_utama REAL,
    nilai_pembanding REAL,
    selisih REAL,
    satuan TEXT NOT NULL,
    status TEXT NOT NULL,
    catatan TEXT,
    PRIMARY KEY (pasangan_id, wilayah_kode, periode, seri_kode, rincian)
);
CREATE INDEX IF NOT EXISTS idx_rekonsiliasi_pasangan ON tabel_rekonsiliasi (pasangan_id);
CREATE INDEX IF NOT EXISTS idx_rekonsiliasi_periode ON tabel_rekonsiliasi (periode);
CREATE VIEW IF NOT EXISTS rekonsiliasi AS SELECT * FROM tabel_rekonsiliasi;
```

---

## 2. Hasil Pemuatan Data dan Kesetaraan Baris (SQL vs Parquet)

Seluruh tabel dimuat secara otomatis saat `python pipeline.py` dijalankan melalui pemanggilan `src.gold.muat_sql.muat_semua_ke_sqlite()`.

| Nama Tabel SQL | Berkas Sumber Parquet | Jumlah Baris Parquet | Jumlah Baris SQL | Status Kesetaraan | Kunci Primer (Primary Key) |
|---|---|---|---|---|---|
| `silver` | `data/silver/silver.parquet` | 7.535 | 7.535 | **100% Cocok** | `(sumber, seri_kode, wilayah_kode, periode, rincian, _berkas_raw)` |
| `panel_gold` | `data/gold/panel.parquet` | 3.382 | 3.382 | **100% Cocok** | `(wilayah_kode, periode, seri_kode, rincian)` |
| `tabel_nasional` | `data/gold/tabel_nasional.parquet` | 90 | 90 | **100% Cocok** | `(periode, seri_kode)` |
| `tabel_rekonsiliasi` | `data/gold/tabel_rekonsiliasi.parquet` | 136 | 136 | **100% Cocok** | `(pasangan_id, wilayah_kode, periode, seri_kode, rincian)` |

Setiap tabel melewati uji integritas *Primary Key* dengan memastikan penolakan otomatis (`sqlite3.IntegrityError`) saat baris kembar dicoba dimasukkan.

---

## 3. Alasan Pemilihan Basis Data SQL (SQLite & DuckDB)

Untuk penyimpanan tabel Silver dan Gold di lingkungan Workbench Capstone, dipilih **SQLite** (relasional OLTP tertanam) dan **DuckDB** (kolumnar OLAP tertanam) dengan pertimbangan:

1. **Integritas Skema dan Kunci Primer (*Schema & PK Enforcement*):**
   * Data Silver dan Gold merupakan data terstruktur dengan definisi kolom baku. Mesin basis data SQL menegakkan tipe data numerik (`REAL`/`INTEGER`) dan integritas kunci primer gabungan, menolak rekaman anomali/duplikat secara deterministik.
2. **Serverless, Ringan, dan Mandiri (*Self-Contained File*):**
   * SQLite dan DuckDB tidak memerlukan instalasi *database daemon* (seperti PostgreSQL/MySQL). Seluruh basis data tersimpan dalam satu berkas mandiri (`data/gold/gold.sqlite`), menjamin reproduksibilitas penuh di lingkungan pengujian tanpa ketergantungan konfigurasi jaringan atau port.
3. **Efisiensi Analitik dan Interoperabilitas:**
   * Terintegrasi langsung dengan ekosistem Python, Pandas, dan PyArrow tanpa *overhead* serialisasi data antar-proses.

---

## 4. Perbandingan SQL Relasional vs Document-Store (JSON Mentah)

| Aspek Evaluasi | SQL Relasional (Lapis Silver & Gold) | Document-Store / JSON Mentah (Bronze) |
|---|---|---|
| **Kesesuaian Tahapan** | **Lapis Silver & Gold** (data terstruktur, siap analisis). | **Lapis Bronze / Mentah** (hasil unduhan API / CKAN). |
| **Fleksibilitas Skema** | *Schema-on-write*: skema kaku, tipe data terverifikasi, kunci unik ditegakkan saat penulisan. | *Schema-on-read*: sangat fleksibel, bebas menampung struktur bersarang (*nested*). |
| **Penanganan Metadata** | Kolom lineage (`_berkas_raw`, `_sha256_raw`) terdefinisi per baris secara eksplisit. | Menyimpan respons utuh API (termasuk *header*, *pagination*, dan *dictionary* sumber). |
| **Kecepatan Query Agregat** | **Sangat Cepat**: optimasi pemindaian kolom, indeks numerik, dan fungsi `GROUP BY` / `SUM`. | **Lambat**: memerlukan parsing teks dokumen JSON utuh dan traversal hirarki berkas. |
| **Integritas Data** | Mencegah baris kembar secara otomatis lewat *Primary Key*. | Rawan duplikasi record jika terjadi penarikan ulang (*pull*) tanpa mekanisme deduplikasi manual. |

---

## 5. Mengapa Pendekatan Tersebut Cocok untuk Lapis Tertentu

* **Lapis Bronze / Data Mentah (`data/raw/`):**  
  Menyimpan respons API mentah sebagai dokumen teks JSON/XLSX mempertahankan bukti silsilah autentik (*ground truth auditability*). Pendekatan *schema-on-read* pada lapis ini krusial karena berkas mentah BNPB dan WDI memiliki variasi struktur yang sangat lebar (26 JSON DataStore dengan hierarki berbeda, 13 XLSX dengan variasi *merged cells*, dan WDI multilabel).
* **Lapis Silver (`data/silver/`):**  
  Pada lapis Silver, seluruh entitas telah dipilah dan dinormalisasi ke dalam skema seragam 11 kolom. Pendekatan relasional dengan *Primary Key* 6 kolom menjamin bahwa seluruh observasi unik, tipe data angka terbebas dari teks non-numerik, dan relasi lineage ke berkas mentah terkunci rapat.
* **Lapis Gold (`data/gold/`):**  
  Lapis Gold ditujukan untuk konsumsi analitis langsung (tabel panel, agregat nasional, dan rekonsiliasi). Format SQL relasional memudahkan pengguna dan peneliti mengeksekusi analisis kuantitatif dengan query SQL standar (`SELECT`, `JOIN`, `WHERE`), sementara berkas Parquet memberikan kompresi efisien dan pemindaian kolom berkecepatan tinggi.
