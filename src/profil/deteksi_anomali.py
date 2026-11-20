"""Tandai outlier per seri dengan IQR & z-score. TIDAK mengubah nilai."""
import pandas as pd, numpy as np, os
OUT = "reports/profil"

def tandai(df, z_thr=3.0, iqr_k=1.5):
    os.makedirs(OUT, exist_ok=True)
    out = []
    for seri, g in df.groupby("seri_kode"):
        x = g["nilai"].astype(float)
        q1, q3 = x.quantile(.25), x.quantile(.75); iqr = q3 - q1
        lo, hi = q1 - iqr_k*iqr, q3 + iqr_k*iqr
        mu, sd = x.mean(), x.std(ddof=0)
        z = (x - mu)/sd if sd and sd > 0 else pd.Series(0, index=x.index)
        mask_iqr = (x < lo) | (x > hi)
        mask_z   = z.abs() > z_thr
        for idx in g.index[mask_iqr | mask_z]:
            row = g.loc[idx]
            metode = []
            if mask_iqr.loc[idx]: metode.append("iqr")
            if mask_z.loc[idx]:   metode.append("zscore")
            out.append({
                "seri_kode": seri, "wilayah_kode": row["wilayah_kode"],
                "nama_wilayah": row["nama_wilayah"], "periode": row["periode"],
                "rincian": row["rincian"], "nilai": row["nilai"],
                "metode": "+".join(metode),
                "alasan_ditandai": f"iqr[{lo:.3g},{hi:.3g}] z|{z.loc[idx]:.2f}|",
                "catatan": "outlier asli, tidak diubah",
                "_berkas_raw": row["_berkas_raw"],
            })
    hasil = pd.DataFrame(out)
    hasil.to_csv(f"{OUT}/calon_anomali.csv", index=False)
    return hasil
