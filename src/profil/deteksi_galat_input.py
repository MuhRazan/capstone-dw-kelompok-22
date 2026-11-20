"""Daftar calon galat input. TIDAK diperbaiki di sini (perbaikan di Tahap 3)."""
import pandas as pd, os
OUT = "reports/profil"

def deteksi(df):
    os.makedirs(OUT, exist_ok=True)
    out = []
    for _, r in df.iterrows():
        masalah = None
        if r["nilai"] < 0:
            masalah = "nilai negatif"
        elif r["seri_kode"].endswith("per_100rb") and r["nilai"] > 1000:
            masalah = "per_100rb > 1000 (mungkin persen/desimal tertukar)"
        elif r["seri_kode"] == "jumlah_penduduk" and r["nilai"] < 1000:
            masalah = "jumlah_penduduk tak wajar (<1000)"
        if masalah:
            out.append({
                "seri_kode": r["seri_kode"], "wilayah_kode": r["wilayah_kode"],
                "nama_wilayah": r["nama_wilayah"], "periode": r["periode"],
                "rincian": r["rincian"], "nilai": r["nilai"],
                "dugaan_masalah": masalah,
                "usulan_perbaikan": "tinjau di Tahap 3 (jangan ubah di sini)",
                "_berkas_raw": r["_berkas_raw"],
            })
    hasil = pd.DataFrame(out)
    hasil.to_csv(f"{OUT}/temuan_galat_input.csv", index=False)
    return hasil
