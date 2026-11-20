"""Loader Silver untuk profil BNPB. Tidak mengubah nilai."""
import pandas as pd

SERI_BNPB = [
    "kejadian", "korban_meninggal", "korban_hilang", "korban_luka_sakit",
    "korban_mengungsi", "korban_terdampak", "korban_terdampak_mengungsi",
    "korban_mengungsi_per_100rb", "korban_meninggal_hilang_per_100rb",
    "jumlah_penduduk",
]
KOLOM_WAJIB = ["sumber","seri_kode","wilayah_kode","nama_wilayah","periode",
               "jenis_periode","rincian","nilai","satuan","_berkas_raw","_sha256_raw"]

def baca_silver(path="data/silver/silver.parquet"):
    df = pd.read_parquet(path)
    hilang = [k for k in KOLOM_WAJIB if k not in df.columns]
    if hilang:
        raise ValueError(f"Kolom wajib hilang: {hilang}")
    
    # Menangkap 'bnpb', 'bnpb_xlsx', 'bnpb_datastore', dll.
    df = df[df["sumber"].astype(str).str.lower().str.contains("bnpb")].copy()
    
    # Filter 10 seri
    df = df[df["seri_kode"].isin(SERI_BNPB)].copy()
    df["nilai"] = pd.to_numeric(df["nilai"], errors="coerce")
    df = df.dropna(subset=["nilai"])
    return df
