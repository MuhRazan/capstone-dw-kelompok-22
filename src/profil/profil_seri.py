"""Statistik deskriptif per seri & per provinsi. Missing dari grid lengkap."""
import pandas as pd, numpy as np, os

OUT = "reports/profil"

def _grid_lengkap(df):
    prov = sorted(df["wilayah_kode"].dropna().unique())
    per  = sorted(df["periode"].dropna().unique())
    rin  = sorted(df["rincian"].dropna().unique())
    return pd.MultiIndex.from_product([prov, per, rin], names=["wilayah_kode","periode","rincian"])

def profil(df):
    os.makedirs(OUT, exist_ok=True)
    baris_seri, baris_prov = [], []
    for seri, g in df.groupby("seri_kode"):
        grid = _grid_lengkap(g)
        kunci = pd.MultiIndex.from_frame(g[["wilayah_kode","periode","rincian"]])
        n_sel = len(grid); n_isi = len(kunci.intersection(grid))
        r = {
            "seri_kode": seri, "n_observasi": len(g),
            "n_provinsi_unik": g["wilayah_kode"].nunique(),
            "tahun_min": g["periode"].min(), "tahun_max": g["periode"].max(),
            "min": g["nilai"].min(), "q1": g["nilai"].quantile(.25),
            "median": g["nilai"].median(), "q3": g["nilai"].quantile(.75),
            "max": g["nilai"].max(), "mean": g["nilai"].mean(), "std": g["nilai"].std(),
            "sel_grid": n_sel, "sel_isi": n_isi,
            "persen_missing": round(100*(n_sel-n_isi)/n_sel, 2) if n_sel else None,
            "satuan": "|".join(map(str, g["satuan"].dropna().unique())),
            "n_satuan_unik": g["satuan"].nunique(),
        }
        baris_seri.append(r)
        for (prov,), gp in g.groupby(["wilayah_kode"]):
            baris_prov.append({
                "seri_kode": seri, "wilayah_kode": prov,
                "nama_wilayah": gp["nama_wilayah"].iloc[0],
                "n_observasi": len(gp),
                "tahun_min": gp["periode"].min(), "tahun_max": gp["periode"].max(),
                "min": gp["nilai"].min(), "median": gp["nilai"].median(),
                "max": gp["nilai"].max(), "mean": gp["nilai"].mean(),
            })
    pd.DataFrame(baris_seri).to_csv(f"{OUT}/ringkasan_profil_per_seri.csv", index=False)
    pd.DataFrame(baris_prov).to_csv(f"{OUT}/ringkasan_profil_per_provinsi.csv", index=False)
    return pd.DataFrame(baris_seri), pd.DataFrame(baris_prov)
