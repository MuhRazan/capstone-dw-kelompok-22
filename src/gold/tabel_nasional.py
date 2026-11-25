"""Persiapan Tahap 6: Ekstraksi baris nasional seri utama dan pembanding ke tabel Gold periode x seri.

Membentuk tabel nasional satu baris per periode x seri yang memuat:
- Angka nasional seri utama BNPB dan seri pembanding WDI (EN.CLC.MDAT.ZS).
- Aturan agregat provinsi (bobot dan alasan) bila baris Indonesia tidak diterbitkan.
- Kolom asal angka ('baris_indonesia', 'agregat_provinsi', 'pembanding').
- Lineage berkas mentah (_berkas_raw) pada setiap baris.
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SILVER_PATH = ROOT / "data" / "silver" / "silver.parquet"
REPORTS_DIR = ROOT / "reports"
GOLD_DIR = ROOT / "data" / "gold"

SERI_ORDER = [
    "kejadian",
    "korban_meninggal",
    "korban_hilang",
    "korban_luka_sakit",
    "korban_mengungsi",
    "korban_terdampak",
    "korban_terdampak_mengungsi",
    "korban_mengungsi_per_100rb",
    "korban_meninggal_hilang_per_100rb",
    "jumlah_penduduk",
    "EN.CLC.MDAT.ZS",
]


def buat_tabel_nasional(silver=None):
    """Bangun tabel nasional periode x seri dan simpan ke data/gold/."""
    if silver is None:
        silver = pd.read_parquet(SILVER_PATH)

    indo = silver[silver["wilayah_kode"] == 9999].copy()
    prov = silver[silver["wilayah_kode"] != 9999].copy()

    records = []
    for per in sorted(silver["periode"].unique()):
        for seri in SERI_ORDER:
            sub_i = indo[(indo["periode"] == per) & (indo["seri_kode"] == seri)]
            sub_p = prov[(prov["periode"] == per) & (prov["seri_kode"] == seri)]

            if len(sub_i) > 0:
                satuan = sub_i["satuan"].iloc[0]
                if seri == "EN.CLC.MDAT.ZS":
                    asal = "pembanding"
                    aturan = "Angka pembanding nasional Bank Dunia (WDI) untuk Indonesia (IDN)"
                    val = float(sub_i["nilai"].iloc[0])
                    raw = sub_i["_berkas_raw"].iloc[0]
                elif "total" in sub_i["rincian"].values:
                    asal = "baris_indonesia"
                    aturan = "Diterbitkan langsung oleh BNPB (wilayah_kode 9999, rincian total)"
                    r_tot = sub_i[sub_i["rincian"] == "total"]
                    val = float(r_tot["nilai"].iloc[0])
                    raw = r_tot["_berkas_raw"].iloc[0]
                else:
                    asal = "baris_indonesia"
                    aturan = "Diterbitkan langsung oleh BNPB (dijumlahkan seluruh rincian jenis bencana)"
                    val = float(sub_i["nilai"].sum())
                    raw = sub_i["_berkas_raw"].iloc[0]

                records.append({
                    "periode": str(per),
                    "seri_kode": seri,
                    "nilai": val,
                    "satuan": satuan,
                    "asal": asal,
                    "aturan_agregat": aturan,
                    "_berkas_raw": raw,
                })
            elif len(sub_p) > 0 and seri in ["korban_meninggal", "korban_terdampak_mengungsi"]:
                # Bila baris Indonesia tidak diterbitkan, gunakan agregat provinsi (aditif murni)
                satuan = sub_p["satuan"].iloc[0]
                asal = "agregat_provinsi"
                n_prov = sub_p["wilayah_kode"].nunique()
                aturan = f"Agregat penjumlahan seluruh {n_prov} provinsi (bobot 1, aditif murni: total nasional adalah jumlah provinsi)"
                val = float(sub_p["nilai"].sum())
                raw = sub_p["_berkas_raw"].iloc[0]

                records.append({
                    "periode": str(per),
                    "seri_kode": seri,
                    "nilai": val,
                    "satuan": satuan,
                    "asal": asal,
                    "aturan_agregat": aturan,
                    "_berkas_raw": raw,
                })

    df_nasional = pd.DataFrame(records)

    # Simpan berkas
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Tabel panjang Gold (satu baris per periode x seri dengan lineage dan asal)
    parquet_panjang = GOLD_DIR / "tabel_nasional.parquet"
    csv_panjang = GOLD_DIR / "tabel_nasional.csv"
    df_nasional.to_parquet(parquet_panjang, index=False)
    df_nasional.to_csv(csv_panjang, index=False)

    # 2. Tabel lebar / pivot untuk kemudahan inspeksi dan laporan rekonsiliasi
    pivot = df_nasional.pivot(index="periode", columns="seri_kode", values="nilai").sort_index()
    pivot = pivot[[c for c in SERI_ORDER if c in pivot.columns]]

    csv_reports = REPORTS_DIR / "tabel_nasional_periode_seri.csv"
    csv_gold = GOLD_DIR / "tabel_nasional_periode_seri.csv"
    parquet_gold = GOLD_DIR / "tabel_nasional_periode_seri.parquet"

    pivot.to_csv(csv_reports)
    pivot.to_csv(csv_gold)
    pivot.to_parquet(parquet_gold)

    print(f"Tabel nasional Gold tersimpan di:")
    print(f"- {parquet_panjang} (panjang: {len(df_nasional)} baris)")
    print(f"- {parquet_gold} (lebar: {pivot.shape[0]} periode x {pivot.shape[1]} seri)")

    return df_nasional


if __name__ == "__main__":
    tabel = buat_tabel_nasional()
    print("\nRingkasan Tabel Nasional Gold:")
    print(tabel.head(10).to_string())
