# Laporan Rancangan Basis Data dan Penyimpanan SQL (Tahap 5 — Kasus 22: Korban Bencana)

Dokumen ini memuat perancangan skema SQL untuk tabel Silver, implementasi pemuat data, alasan pemilihan basis data, serta perbandingannya dengan penyimpanan respons JSON mentah sebagai dokumen.

---

## 1. Rancangan Skema SQL (DDL)

Skema tabel SQL dirancang mengikuti 11 kolom wajib skema minimal Silver (`src/common/skema.py`). Berkas DDL tersimpan di `src/gold/skema_silver.sql`:

```sql
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
```

### Kunci Primer & Indeks
* **Kunci Primer Komposit (6 kolom):** `(sumber, seri_kode, wilayah_kode, periode, rincian, _berkas_raw)`.  
  Kunci ini menjamin secara ketat pada level basis data bahwa tidak ada baris ganda untuk kombinasi observasi dan berkas sumber yang sama (menegakkan aturan validasi R02).
* **Indeks:** Ditambahkan indeks pada `(seri_kode, periode)` dan `(wilayah_kode)` untuk mempercepat *query join* dan pemfilteran pada tahap agregasi Gold.

---

## 2. Alasan Pemilihan Basis Data SQL (SQLite & DuckDB)

Untuk penyimpanan tabel Silver dan Gold di lingkungan Workbench Capstone, dipilih **SQLite** (relasional OLTP tertanam) dan **DuckDB** (kolumnar OLAP tertanam) dengan pertimbangan:

1. **Integritas Skema dan Kunci Primer (*Schema & PK Enforcement*):**
   * Data Silver merupakan tabel terstruktur dengan skema baku 11 kolom. Basis data SQL menegakkan tipe data numerik (`REAL`/`INTEGER`) dan integritas kunci primer gabungan, menolak nilai anomali/duplikat secara otomatis.
2. **Serverless, Ringan, dan Mandiri (*Self-Contained File*):**
   * SQLite dan DuckDB tidak memerlukan instalasi *database daemon* (seperti PostgreSQL/MySQL). Seluruh basis data tersimpan dalam satu berkas tunggal (`gold.sqlite` / `silver.db`), menjamin reproduksibilitas penuh di lingkungan pengujian tanpa ketergantungan konfigurasi jaringan atau port.
3. **Efisiensi Analitik dan Interoperabilitas:**
   * Terintegrasi langsung dengan Python, Pandas, dan PyArrow tanpa *overhead* serialisasi data.

---

## 3. Perbandingan SQL Relasional vs Document-Store (JSON Mentah)

| Aspek Evaluasi | SQL Relasional (Tabel Silver) | Document-Store / JSON Mentah (Bronze) |
|---|---|---|
| **Kesesuaian Tahapan** | **Lapis Silver & Gold** (data bersih, siap analisis). | **Lapis Bronze / Mentah** (hasil unduhan API / CKAN). |
| **Fleksibilitas Skema** | *Schema-on-write*: skema kaku, tipe data terverifikasi, kunci unik ditegakkan. | *Schema-on-read*: sangat fleksibel, bebas menampung struktur bersarang (*nested*). |
| **Penanganan Metadata** | Kolom lineage (`_berkas_raw`, `_sha256_raw`) terdefinisi per baris secara eksplisit. | Menyimpan respons utuh API (termasuk *header*, *pagination*, dan *dictionary* sumber). |
| **Kecepatan Query Agregat** | **Sangat Cepat**: optimasi pemindaian kolom, indeks numerik, dan fungsi `GROUP BY` / `SUM`. | **Lambat**: memerlukan *parsing* teks dokumen JSON utuh dan traversal hirarki JSON. |
| **Integritas Data** | Mencegah baris kembar secara otomatis lewat *Primary Key*. | Rawan duplikasi record jika terjadi penarikan ulang (*pull*) tanpa mekanisme deduplikasi manual. |

**Kesimpulan:**  
Format dokumen JSON tetap dipertahankan pada **data mentah (`data/raw/`)** untuk menjaga keaslian bukti audit silsilah (*lineage auditability*). Sebaliknya, pada **lapis Silver**, data ditransformasikan ke tabel relasional SQL agar siap diagregasi, divalidasi, dan dihubungkan ke tabel panel Gold.

---

## 4. Hasil Uji Coba Pemuatan Silver Pertama

Skrip pemuat [src/gold/muat_sql.py](file:///c:/Users/HP/workbench-workspace\capstone-data-wrangling\src\gold\muat_sql.py) dijalankan dengan hasil:
* **Sumber:** `data/silver/silver.parquet` (7.535 baris).
* **Tujuan:** `data/gold/gold.sqlite` dan `data/silver/silver.db`.
* **Jumlah baris termuat:** **7.535 baris** (100% lengkap).
* **Uji Integritas Primary Key:** Berhasil menolak duplikat observasi (`sqlite3.IntegrityError` terpicu saat baris kembar dicoba dimasukkan).
