"""Profil seri pembanding WDI: EN.CLC.MDAT.ZS (Droughts, floods, extreme temperatures)."""
import pandas as pd
import os

OUT = "reports/profil"
SERI_WDI = "EN.CLC.MDAT.ZS"

def profil_pembanding(path="data/silver/silver.parquet"):
    os.makedirs(OUT, exist_ok=True)
    df = pd.read_parquet(path)
    
    # Filter hanya untuk seri WDI yang diminta
    wdi = df[df["seri_kode"] == SERI_WDI].copy()
    
    if wdi.empty:
        print(f"Peringatan: Seri {SERI_WDI} tidak ditemukan di Silver.")
        return

    # 1. Cek Periode (Tahun)
    periode = sorted(wdi["periode"].unique())
    print(f"Periode tersedia: {periode[0]} s/d {periode[-1]} ({len(periode)} tahun)")
    
    # 2. Cek Rincian (Jenis kelamin, umur, daerah, dll.)
    rincian = wdi["rincian"].unique()
    print(f"Rincian tersedia: {rincian}")
    
    # 3. Cek Satuan
    satuan = wdi["satuan"].unique()
    print(f"Satuan: {satuan}")
    
    # 4. Cek Wilayah
    wilayah = wdi["wilayah_kode"].unique()
    print(f"Wilayah: {wilayah}")

    # --- SIMPAN HASIL PROFIL ---
    # Tabel ketersediaan (Tahun x Rincian)
    tabel_ketersediaan = wdi.pivot_table(
        index="periode", 
        columns="rincian", 
        values="nilai", 
        aggfunc="count"
    ).fillna(0).astype(int)
    
    tabel_ketersediaan.to_csv(f"{OUT}/ketersediaan_pembanding_{SERI_WDI}.csv")
    print(f"Tabel ketersediaan disimpan di {OUT}/ketersediaan_pembanding_{SERI_WDI}.csv")

    # --- TANDAI RINCIAN YANG SEBANDING ---
    # Asumsi: Seri utama BNPB adalah total provinsi (tanpa rincian gender/umur)
    # WDI biasanya memiliki rincian "total" atau kosong untuk indikator ini.
    kandidat = []
    for r in rincian:
        if str(r).lower() in ["total", "semua", "all", "nan", "none", ""]:
            alasan = "Rincian total cocok dengan agregat provinsi BNPB"
            sebanding = True
        else:
            alasan = f"Rincian '{r}' kemungkinan tidak sebanding karena BNPB tidak memecah data berdasarkan ini"
            sebanding = False
            
        kandidat.append({
            "seri_pembanding": SERI_WDI,
            "rincian": r,
            "sebanding": sebanding,
            "alasan": alasan
        })
    
    df_kandidat = pd.DataFrame(kandidat)
    df_kandidat.to_csv(f"{OUT}/kandidat_sebanding_{SERI_WDI}.csv", index=False)
    print(f"Kandidat sebanding disimpan di {OUT}/kandidat_sebanding_{SERI_WDI}.csv")

if __name__ == "__main__":
    profil_pembanding()
