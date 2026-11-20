"""Tahap 3: Klasifikasi Anomali (outlier asli, patahan, galat input) & Perbaikan Galat."""
import pandas as pd
import numpy as np
import os

OUT = "reports/profil"

def baca_csv_aman(path):
    """Fungsi bantuan untuk membaca CSV, jika kosong return DataFrame kosong."""
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()

def klasifikasi_dan_perbaiki(df):
    os.makedirs(OUT, exist_ok=True)
    
    # 1. Load calon anomali & temuan galat input (dengan pengaman)
    anomali = baca_csv_aman(f"{OUT}/calon_anomali.csv")
    galat = baca_csv_aman(f"{OUT}/temuan_galat_input.csv")
    patahan = baca_csv_aman(f"{OUT}/calon_patahan.csv")
    
    # Tambahkan kolom kategori
    anomali["kategori"] = "Outlier Asli"
    anomali["alasan_kategori"] = "Nilai ekstrem yang merepresentasikan kejadian bencana besar (fakta)."
    
    # 2. Tandai Patahan (jika ada di calon_patahan)
    if not patahan.empty:
        for idx, row in patahan.iterrows():
            seri = row["seri_kode"]
            periode = row["periode_patahan"]
            mask = (anomali["seri_kode"] == seri) & (anomali["periode"] == periode)
            anomali.loc[mask, "kategori"] = "Patahan Seri"
            anomali.loc[mask, "alasan_kategori"] = f"Lonjakan serentak >70% provinsi. Dugaan: {row['dugaan_penyebab']}"
            
    # 3. Tandai Galat Input (jika ada di temuan_galat_input)
    if not galat.empty:
        for idx, row in galat.iterrows():
            seri = row["seri_kode"]
            wilayah = row["wilayah_kode"]
            periode = row["periode"]
            mask = (anomali["seri_kode"] == seri) & (anomali["wilayah_kode"] == wilayah) & (anomali["periode"] == periode)
            anomali.loc[mask, "kategori"] = "Galat Input"
            anomali.loc[mask, "alasan_kategori"] = f"Salah input: {row['dugaan_masalah']}. Akan diperbaiki."
            
    # Simpan hasil klasifikasi
    anomali.to_csv(f"{OUT}/klasifikasi_anomali.csv", index=False)
    print(f"Total anomali terklasifikasi: {len(anomali)}")
    print(anomali["kategori"].value_counts().to_string())
    
    # 4. Perbaiki Galat Input di Silver
    df_bersih = df.copy()
    if not galat.empty:
        print("\nMelakukan perbaikan pada galat input...")
        for idx, row in galat.iterrows():
            mask = (df_bersih["seri_kode"] == row["seri_kode"]) & \
                   (df_bersih["wilayah_kode"] == row["wilayah_kode"]) & \
                   (df_bersih["periode"] == row["periode"])
            
            # Perbaikan: ubah jadi NaN
            df_bersih.loc[mask, "nilai"] = np.nan 
            print(f"Memperbaiki {row['seri_kode']} di wilayah {row['wilayah_kode']} tahun {row['periode']} (sebelumnya: {row['nilai']})")
            
        # Simpan Silver yang sudah diperbaiki
        df_bersih.to_parquet("data/silver/silver_clean.parquet", index=False)
        print("Silver bersih disimpan di data/silver/silver_clean.parquet")
    else:
        print("Tidak ada galat input yang perlu diperbaiki.")
        df_bersih.to_parquet("data/silver/silver_clean.parquet", index=False)

if __name__ == "__main__":
    from src.profil.baca_silver import baca_silver
    df = baca_silver()
    klasifikasi_dan_perbaiki(df)
