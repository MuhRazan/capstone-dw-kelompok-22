"""Tahap 5: Rancang tabel SQL untuk Silver dan pemuat data dari silver.parquet."""
import sqlite3
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DDL_FILE = ROOT / "src" / "gold" / "skema_silver.sql"
SILVER_PARQUET = ROOT / "data" / "silver" / "silver.parquet"
SQLITE_DB = ROOT / "data" / "gold" / "gold.sqlite"
SQLITE_SILVER_DB = ROOT / "data" / "silver" / "silver.db"


def muat_silver_ke_sqlite(parquet_path=SILVER_PARQUET, db_path=SQLITE_DB):
    """Muat tabel Silver dari Parquet ke basis data SQLite menggunakan skema DDL."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(parquet_path)
    total_baris_parquet = len(df)
    print(f"Membaca {total_baris_parquet:,} baris dari {parquet_path}...")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Eksekusi DDL
    ddl_sql = DDL_FILE.read_text(encoding="utf-8")
    cur.executescript(ddl_sql)

    # Bersihkan tabel jika sudah ada data sebelumnya
    cur.execute("DELETE FROM silver;")

    # Masukkan data dengan INSERT
    kolom = [
        "sumber", "seri_kode", "wilayah_kode", "nama_wilayah",
        "periode", "jenis_periode", "rincian", "nilai", "satuan",
        "_berkas_raw", "_sha256_raw"
    ]
    placeholders = ", ".join(["?"] * len(kolom))
    insert_sql = f"INSERT INTO silver ({', '.join(kolom)}) VALUES ({placeholders});"

    data_tuples = [tuple(x) for x in df[kolom].to_numpy()]
    cur.executemany(insert_sql, data_tuples)
    conn.commit()

    # Verifikasi jumlah baris yang berhasil termuat
    cur.execute("SELECT count(*) FROM silver;")
    termuat = cur.fetchone()[0]
    print(f"Berhasil memuat {termuat:,} baris ke tabel 'silver' di {db_path}.")

    # Uji integritas Primary Key: coba masukkan baris duplikat, harus gagal
    try:
        cur.execute(insert_sql, data_tuples[0])
        conn.commit()
        raise RuntimeError("Uji Primary Key GAGAL: Baris kembar berhasil dimasukkan!")
    except sqlite3.IntegrityError:
        print("Uji Integritas Primary Key LOLOS: Database berhasil menolak baris duplikat.")

    conn.close()
    return termuat


def main():
    print("=== Pemuatan Silver ke SQLite (data/gold/gold.sqlite) ===")
    muat_silver_ke_sqlite(db_path=SQLITE_DB)
    print("\n=== Pemuatan Silver ke SQLite (data/silver/silver.db) ===")
    muat_silver_ke_sqlite(db_path=SQLITE_SILVER_DB)


if __name__ == "__main__":
    main()
