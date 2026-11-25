-- DDL Skema Basis Data Relasional SQL (Tahap 5 & 6 — Kasus 22: Korban Bencana)
-- Komponen: Integrasi, Penyimpanan, dan Skala (124450089)
-- Kompatibel dengan: SQLite, DuckDB, dan PostgreSQL

-- ============================================================================
-- 1. Tabel Silver: Data observasi terstandarisasi 11 kolom wajib
-- ============================================================================
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

-- ============================================================================
-- 2. Tabel Panel Gold: Panel provinsi x periode x indikator (format panjang)
-- ============================================================================
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

-- View/alias 'panel' untuk memudahkan query pemanggilan
CREATE VIEW IF NOT EXISTS panel AS SELECT * FROM panel_gold;

-- ============================================================================
-- 3. Tabel Nasional Gold: Baris nasional periode x seri dengan asal dan lineage
-- ============================================================================
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

-- ============================================================================
-- 4. Tabel Rekonsiliasi Gold: 3 Pasangan rekonsiliasi dan catatan keterbandingan
-- ============================================================================
CREATE TABLE IF NOT EXISTS tabel_rekonsiliasi (
    pasangan_id TEXT NOT NULL,
    nama_pasangan TEXT NOT NULL,
    wilayah_kode INTEGER NOT NULL,
    nama_wilayah TEXT NOT NULL,
    periode TEXT NOT NULL,
    seri_kode TEXT NOT NULL,
    rincian TEXT NOT NULL,
    nilai_seri_utama REAL,
    nilai_utama REAL,
    nilai_pembanding REAL,
    selisih REAL,
    satuan TEXT NOT NULL,
    kategori_penjelasan TEXT NOT NULL,
    kategori TEXT NOT NULL,
    status TEXT NOT NULL,
    catatan TEXT,
    PRIMARY KEY (pasangan_id, wilayah_kode, periode, seri_kode, rincian)
);

CREATE INDEX IF NOT EXISTS idx_rekonsiliasi_pasangan ON tabel_rekonsiliasi (pasangan_id);
CREATE INDEX IF NOT EXISTS idx_rekonsiliasi_periode ON tabel_rekonsiliasi (periode);

-- View/alias 'rekonsiliasi' untuk fleksibilitas query
CREATE VIEW IF NOT EXISTS rekonsiliasi AS SELECT * FROM tabel_rekonsiliasi;
