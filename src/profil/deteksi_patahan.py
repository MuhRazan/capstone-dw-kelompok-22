"""Tandai patahan seri: >=70% provinsi berubah searah dgn magnitudo > median delta."""
import pandas as pd, numpy as np, os
OUT = "reports/profil"

def deteksi(df, ambang_prov=0.70):
    os.makedirs(OUT, exist_ok=True)
    out = []
    for seri, g in df.groupby("seri_kode"):
        piv = g.pivot_table(index="wilayah_kode", columns="periode", values="nilai", aggfunc="mean")
        if piv.shape[1] < 2: continue
        delta = piv.diff(axis=1)
        for t in delta.columns[1:]:
            d = delta[t].dropna()
            if len(d) < 5: continue
            med = d.abs().median()
            naik = (d > med).sum(); turun = (d < -med).sum()
            n = len(d)
            if naik/n >= ambang_prov or turun/n >= ambang_prov:
                arah = "naik" if naik >= turun else "turun"
                out.append({
                    "seri_kode": seri, "periode_patahan": t,
                    "n_provinsi_berubah": int(max(naik, turun)), "n_provinsi_total": n,
                    "arah": arah, "magnitudo_median": float(med),
                    "dugaan_penyebab": "perlu cross-check metadata",
                    "sumber_metadata": "manifest_asal.json / catatan BNPB",
                })
    hasil = pd.DataFrame(out)
    hasil.to_csv(f"{OUT}/calon_patahan.csv", index=False)
    return hasil
