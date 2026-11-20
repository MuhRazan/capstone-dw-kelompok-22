"""Tahap 3: Bentuk grid lengkap wilayah x periode, cek missing, dan penanganan khusus."""
import pandas as pd
import numpy as np
import os

OUT = "reports/profil"

def buat_grid(df):
    os.makedirs(OUT, exist_ok=True)
    
    # 1. Pisahkan Indonesia (9999) dan Provinsi
    df_indo = df[df["wilayah_kode"] == 9999].copy()
    df_prov = df[df["wilayah_kode"] != 9999].copy()
    
    # 2. Tentukan batas tahun (periode) min dan max dari keseluruhan data
    # Grid dibentuk dari tahun min ke max
    tahun_min = df["periode"].min()
    tahun_max = df["periode"].max()
    semua_tahun = sorted(df["periode"].unique())
    
    # Daftar provinsi (hanya kode 4 digit selain 9999)
    provinsi = sorted(df_prov["wilayah_kode"].unique())
    seri_list = sorted(df_prov["seri_kode"].unique())
    
    # --- CEK KHUSUS 1: Korban meninggal & hilang dalam satu kolom ---
    print("\n=== CEK KOLOM MENINGGAL & HILANG ===")
    seri_cek = ["korban_meninggal", "korban_hilang", "korban_meninggal_hilang_per_100rb"]
    for s in seri_cek:
        if s in df_prov["seri_kode"].values:
            subset = df_prov[df_prov["seri_kode"] == s]
            print(f"Seri {s}: {len(subset)} baris, tahun {subset['periode'].min()}-{subset['periode'].max()}")
            # Cek apakah ada tahun di mana salah satu seri kosong
            pivot = subset.groupby("periode")["nilai"].count()
            print(f"  Ketersediaan per tahun: {pivot.to_dict()}")

    # --- CEK KHUSUS 2: Agregasi Kab/Kota ---
    # (Karena di Silver kita sudah membuang kab/kota, kita hanya bisa melaporkan
    # berapa banyak baris mentah yang diagregasi berdasarkan log keputusan K-006)
    print("\n=== CATATAN AGREGASI KAB/KOTA ===")
    print("Berdasarkan log K-006: 28.924 baris kab/kota telah diagregasi ke provinsi di tahap Silver.")
    print("Detail per provinsi x tahun tidak tersedia di Silver karena sudah diagregasi.")
    
    # --- BENTUK GRID LENGKAP ---
    # Grid = (Provinsi x Tahun x Seri)
    # Karena rincian bervariasi, kita agregasi dulu ke total per provinsi per tahun per seri
    df_prov_total = df_prov[df_prov["rincian"] == "total"].copy()
    
    # Buat kerangka kosong
    grid = pd.MultiIndex.from_product(
        [provinsi, semua_tahun, seri_list],
        names=["wilayah_kode", "periode", "seri_kode"]
    ).to_frame(index=False)
    
    # Gabungkan dengan data aktual
    aktual = df_prov_total.groupby(["wilayah_kode", "periode", "seri_kode"])["nilai"].sum().reset_index()
    aktual["terisi"] = 1
    
    grid = grid.merge(aktual, on=["wilayah_kode", "periode", "seri_kode"], how="left")
    grid["terisi"] = grid["terisi"].fillna(0).astype(int)
    
    # --- LAPORKAN KELENGKAPAN PER SERI PER TAHUN ---
    kelengkapan = grid.groupby(["seri_kode", "periode"])["terisi"].agg(["sum", "count"]).reset_index()
    kelengkapan["persen_terisi"] = (kelengkapan["sum"] / kelengkapan["count"] * 100).round(2)
    
    # Pivot untuk laporan
    pivot_kelengkapan = kelengkapan.pivot(index="seri_kode", columns="periode", values="persen_terisi").fillna(0)
    pivot_kelengkapan.to_csv(f"{OUT}/kelengkapan_panel_per_seri.csv")
    print(f"\nTabel kelengkapan panel disimpan di {OUT}/kelengkapan_panel_per_seri.csv")
    
    # --- SIMPAN GRID LENGKAP (Untuk referensi Tahap 4) ---
    grid.to_parquet("data/silver/grid_lengkap.parquet", index=False)
    print("Grid lengkap disimpan di data/silver/grid_lengkap.parquet")
    
    # Hitung total sel kosong
    total_sel = len(grid)
    sel_kosong = grid[grid["terisi"] == 0].shape[0]
    print(f"Total sel grid: {total_sel}, Sel kosong: {sel_kosong} ({sel_kosong/total_sel*100:.2f}%)")

if __name__ == "__main__":
    from src.profil.baca_silver import baca_silver
    df = baca_silver()
    buat_grid(df)
