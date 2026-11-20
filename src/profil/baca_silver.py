"""Loader Silver untuk profil. Tidak mengubah nilai apa pun.

`baca_bnpb()` mengembalikan 10 seri BNPB; `baca_wdi()` mengembalikan satu baris
pembanding nasional EN.CLC.MDAT.ZS; `baca_semua()` mengembalikan keduanya.
"""
import pandas as pd

from src.profil.konstanta import SERI_BNPB

KOLOM_WAJIB = [
    "sumber", "seri_kode", "wilayah_kode", "nama_wilayah", "periode",
    "jenis_periode", "rincian", "nilai", "satuan", "_berkas_raw", "_sha256_raw",
]


def baca_semua(path="data/silver/silver.parquet"):
    df = pd.read_parquet(path)
    hilang = [k for k in KOLOM_WAJIB if k not in df.columns]
    if hilang:
        raise ValueError(f"Kolom wajib hilang: {hilang}")
    df = df.copy()
    df["nilai"] = pd.to_numeric(df["nilai"], errors="coerce")
    df["periode"] = df["periode"].astype("string")
    df["wilayah_kode"] = pd.to_numeric(df["wilayah_kode"], errors="raise").astype("int64")
    return df


def baca_bnpb(path="data/silver/silver.parquet"):
    df = baca_semua(path)
    b = df[df["sumber"].astype(str).str.lower().str.contains("bnpb")].copy()
    b = b[b["seri_kode"].isin(SERI_BNPB)].copy()
    return b.dropna(subset=["nilai"])


def baca_wdi(path="data/silver/silver.parquet"):
    df = baca_semua(path)
    w = df[df["sumber"].astype(str).str.lower().eq("wdi")].copy()
    return w.dropna(subset=["nilai"])


# nama lama dipertahankan agar pemanggil Tahap 2 sebelumnya tetap berjalan
def baca_silver(path="data/silver/silver.parquet"):
    return baca_bnpb(path)
