"""Grafik dari data PRA-pembersihan. Boxplot per provinsi + deret waktu + heatmap."""
import pandas as pd, numpy as np, os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, seaborn as sns
OUT = "reports/gambar"

def buat(df, patahan=None):
    os.makedirs(OUT, exist_ok=True); n = 0
    for seri, g in df.groupby("seri_kode"):
        # boxplot per provinsi
        plt.figure(figsize=(12,6))
        sns.boxplot(data=g, x="wilayah_kode", y="nilai")
        plt.title(f"Boxplot {seri} per provinsi (pra-pembersihan)")
        plt.xticks(rotation=90, fontsize=7); plt.tight_layout()
        plt.savefig(f"{OUT}/boxplot_{seri}.png", dpi=110); plt.close(); n += 1
        # deret waktu nasional (median provinsi per periode)
        ts = g.groupby("periode")["nilai"].median().sort_index()
        plt.figure(figsize=(10,5))
        plt.plot(ts.index.astype(str), ts.values, marker="o")
        if patahan is not None and len(patahan):
            for t in patahan.loc[patahan["seri_kode"]==seri, "periode_patahan"].astype(str):
                plt.axvline(t, color="red", ls="--", alpha=.6)
        plt.title(f"Deret waktu {seri} (median provinsi)"); plt.xticks(rotation=45)
        plt.tight_layout(); plt.savefig(f"{OUT}/deret_waktu_{seri}.png", dpi=110); plt.close(); n += 1
        # heatmap provinsi x periode
        piv = g.pivot_table(index="wilayah_kode", columns="periode", values="nilai", aggfunc="mean")
        if not piv.empty:
            plt.figure(figsize=(12, max(4, len(piv)*0.25)))
            sns.heatmap(piv, cmap="viridis")
            plt.title(f"Heatmap {seri} provinsi x periode"); plt.tight_layout()
            plt.savefig(f"{OUT}/heatmap_{seri}.png", dpi=110); plt.close(); n += 1
    return n
