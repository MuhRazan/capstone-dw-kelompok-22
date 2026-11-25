"""Tahap 5: Pemuat data SQL relasional (SQLite/DuckDB) dari berkas Parquet Silver dan Gold.

Memuat 4 tabel utama:
1. silver: dari data/silver/silver.parquet
2. panel_gold (dan view panel): dari data/gold/panel.parquet
3. tabel_nasional: dari data/gold/tabel_nasional.parquet
4. tabel_rekonsiliasi (dan view rekonsiliasi): dari data/gold/tabel_rekonsiliasi.parquet

Memastikan:
- DDL tereksekusi dengan benar dengan tipe kolom dan Primary Key yang jelas.
- Jumlah baris di SQL sama persis dengan jumlah baris Parquet terkait.
- Uji integritas Primary Key (penolakan baris duplikat) berjalan sukses.
"""
from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DDL_FILE = ROOT / "src" / "gold" / "skema.sql"
SQLITE_DB = ROOT / "data" / "gold" / "gold.sqlite"
SQLITE_SILVER_DB = ROOT / "data" / "silver" / "silver.db"

# Pemetaan Berkas Parquet ke Tabel SQL
TABEL_CONFIG = [
    {
        "tabel": "silver",
        "parquet": ROOT / "data" / "silver" / "silver.parquet",
        "kolom": [
            "sumber", "seri_kode", "wilayah_kode", "nama_wilayah",
            "periode", "jenis_periode", "rincian", "nilai", "satuan",
            "_berkas_raw", "_sha256_raw"
        ],
        "kunci_uji": ("sumber", "seri_kode", "wilayah_kode", "periode", "rincian", "_berkas_raw"),
    },
    {
        "tabel": "panel_gold",
        "parquet": ROOT / "data" / "gold" / "panel.parquet",
        "kolom": [
            "indikator", "seri_kode", "rincian", "rincian_kode", "wilayah_kode",
            "nama_wilayah", "periode", "jenis_periode", "nilai", "nilai_per_100rb",
            "nilai_log1p", "satuan", "status_sel", "penanda", "_berkas_raw", "_sha256_raw"
        ],
        "kunci_uji": ("wilayah_kode", "periode", "seri_kode", "rincian"),
    },
    {
        "tabel": "tabel_nasional",
        "parquet": ROOT / "data" / "gold" / "tabel_nasional.parquet",
        "kolom": [
            "periode", "seri_kode", "nilai", "satuan", "asal",
            "aturan_agregat", "_berkas_raw"
        ],
        "kunci_uji": ("periode", "seri_kode"),
    },
    {
        "tabel": "tabel_rekonsiliasi",
        "parquet": ROOT / "data" / "gold" / "tabel_rekonsiliasi.parquet",
        "kolom": [
            "pasangan_id", "nama_pasangan", "wilayah_kode", "nama_wilayah",
            "periode", "seri_kode", "rincian", "nilai_utama", "nilai_pembanding",
            "selisih", "satuan", "status", "catatan"
        ],
        "kunci_uji": ("pasangan_id", "wilayah_kode", "periode", "seri_kode", "rincian"),
    },
]


def muat_semua_ke_sqlite(db_path=SQLITE_DB):
    """Muat seluruh tabel Silver dan Gold dari Parquet ke basis data SQLite."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 1. Jalankan DDL
    ddl_sql = DDL_FILE.read_text(encoding="utf-8")
    cur.executescript(ddl_sql)

    ringkasan_termuat = {}

    for cfg in TABEL_CONFIG:
        tabel = cfg["tabel"]
        parquet_path = cfg["parquet"]
        kolom = cfg["kolom"]

        if not parquet_path.exists():
            print(f"[LEWAT] Berkas {parquet_path} belum ditemukan.")
            continue

        df = pd.read_parquet(parquet_path)
        total_baris_parquet = len(df)

        # Bersihkan tabel sebelum dimuat ulang
        cur.execute(f"DELETE FROM {tabel};")

        # Susun query INSERT
        placeholders = ", ".join(["?"] * len(kolom))
        insert_sql = f"INSERT INTO {tabel} ({', '.join(kolom)}) VALUES ({placeholders});"

        # Ganti NaN/NaT dengan None agar menjadi NULL di SQLite
        df_clean = df[kolom].copy()
        df_clean = df_clean.replace({float("nan"): None, np_nan_substitute: None}) if 'np_nan_substitute' in globals() else df_clean.where(pd.notnull(df_clean), None)

        data_tuples = [tuple(x) for x in df_clean.to_numpy()]
        cur.executemany(insert_sql, data_tuples)
        conn.commit()

        # Verifikasi jumlah baris
        cur.execute(f"SELECT count(*) FROM {tabel};")
        baris_sql = cur.fetchone()[0]

        assert baris_sql == total_baris_parquet, (
            f"Ketidakcocokan baris pada tabel '{tabel}': SQL={baris_sql:,} vs Parquet={total_baris_parquet:,}"
        )
        print(f"[OK] Tabel '{tabel}': {baris_sql:,} baris di SQL == {total_baris_parquet:,} baris di Parquet.")
        ringkasan_termuat[tabel] = baris_sql

        # Uji integritas Primary Key: coba masukkan ulang baris pertama, harus IntegrityError
        if len(data_tuples) > 0:
            try:
                cur.execute(insert_sql, data_tuples[0])
                conn.commit()
                raise RuntimeError(f"Uji Primary Key GAGAL pada tabel '{tabel}': baris duplikat berhasil masuk!")
            except sqlite3.IntegrityError:
                pass  # Lolos uji integritas

    conn.close()
    return ringkasan_termuat


def muat_silver_ke_sqlite(parquet_path=None, db_path=SQLITE_DB):
    """Fungsi kompatibilitas ke belakang untuk memuat Silver."""
    res = muat_semua_ke_sqlite(db_path=db_path)
    return res.get("silver", 0)


def main():
    print("=== Memuat Tabel Silver & Gold ke SQLite (data/gold/gold.sqlite) ===")
    muat_semua_ke_sqlite(db_path=SQLITE_DB)
    print("\n=== Memuat Tabel Silver & Gold ke SQLite (data/silver/silver.db) ===")
    muat_semua_ke_sqlite(db_path=SQLITE_SILVER_DB)


if __name__ == "__main__":
    main()
