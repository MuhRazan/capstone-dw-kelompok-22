"""Persiapan Tahap 6: Ekstraksi baris nasional seri utama dan pembanding ke tabel periode x seri."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SILVER_PATH = ROOT / "data" / "silver" / "silver.parquet"
REPORTS_DIR = ROOT / "reports"
GOLD_DIR = ROOT / "data" / "gold"


def buat_tabel_nasional(silver_path=SILVER_PATH):
    df = pd.read_parquet(silver_path)
    indo = df[df["wilayah_kode"] == 9999].copy()

    records = []
    for (periode, seri), g in indo.groupby(["periode", "seri_kode"]):
        if "total" in g["rincian"].values:
            val = g[g["rincian"] == "total"]["nilai"].iloc[0]
        else:
            # Seri per bencana dijumlahkan ke total nasional (mis. 2010-2024 dan seri per 100rb 2025)
            val = g["nilai"].sum()
        records.append({"periode": str(periode), "seri_kode": seri, "nilai": val})

    clean_df = pd.DataFrame(records)
    pivot = clean_df.pivot(index="periode", columns="seri_kode", values="nilai")
    pivot = pivot.sort_index()

    kolom_urut = [
        "kejadian",
        "korban_meninggal",
        "korban_hilang",
        "korban_luka_sakit",
        "korban_mengungsi",
        "korban_terdampak",
        "korban_mengungsi_per_100rb",
        "korban_meninggal_hilang_per_100rb",
        "jumlah_penduduk",
        "EN.CLC.MDAT.ZS",
    ]
    pivot = pivot[[c for c in kolom_urut if c in pivot.columns]]

    # Simpan ke reports dan data/gold
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    csv_reports = REPORTS_DIR / "tabel_nasional_periode_seri.csv"
    csv_gold = GOLD_DIR / "tabel_nasional_periode_seri.csv"
    parquet_gold = GOLD_DIR / "tabel_nasional_periode_seri.parquet"

    pivot.to_csv(csv_reports)
    pivot.to_csv(csv_gold)
    pivot.to_parquet(parquet_gold)

    print(f"Tabel nasional tersimpan di:\n- {csv_reports}\n- {csv_gold}\n- {parquet_gold}")
    return pivot


if __name__ == "__main__":
    tabel = buat_tabel_nasional()
    print("\nRingkasan Tabel Nasional (periode x seri):")
    print(tabel.to_string())
