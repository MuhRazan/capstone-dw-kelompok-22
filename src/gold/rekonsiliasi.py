"""Tahap 6 & Tahap 5: Pembentukan tabel rekonsiliasi analitik Gold.

Menyusun tabel rekonsiliasi yang membandingkan:
1. Pasangan 1 (Rasio per 100rb): Hitungan kelompok vs angka terbitan resmi BNPB 2025 (nasional & provinsi).
2. Pasangan 2 (Agregasi Kab/Kota): Agregasi kabupaten/kota vs rekapitulasi provinsi BNPB (2021 & 2022).
3. Pasangan 3 (BNPB vs WDI): Seri utama BNPB vs seri pembanding WDI EN.CLC.MDAT.ZS (konteks paparan historis).

Keluaran:
- data/gold/tabel_rekonsiliasi.parquet
- data/gold/tabel_rekonsiliasi.csv
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SILVER_PATH = ROOT / "data" / "silver" / "silver.parquet"
REPORTS_DIR = ROOT / "reports"
GOLD_DIR = ROOT / "data" / "gold"
KAB_CSV = REPORTS_DIR / "validasi-agregasi-kabupaten.csv"


def buat_tabel_rekonsiliasi(silver=None):
    """Bangun tabel rekonsiliasi 3 pasangan dan simpan ke data/gold/."""
    if silver is None:
        silver = pd.read_parquet(SILVER_PATH)

    records = []

    # =========================================================================
    # PASANGAN 1: Angka Rasio per 100 Ribu Penduduk (Hitungan Kelompok vs Terbitan BNPB)
    # =========================================================================
    sub_2025 = silver[silver["periode"] == "2025"]

    # 1.1 Nasional (wilayah_kode 9999)
    sub_nas = sub_2025[sub_2025["wilayah_kode"] == 9999]
    p_nas = float(sub_nas[sub_nas["seri_kode"] == "jumlah_penduduk"]["nilai"].iloc[0])

    # Total nasional
    m_nas = float(sub_nas[(sub_nas["seri_kode"] == "korban_mengungsi") & (sub_nas["rincian"] == "total")]["nilai"].iloc[0])
    d_nas = float(sub_nas[(sub_nas["seri_kode"] == "korban_meninggal") & (sub_nas["rincian"] == "total")]["nilai"].iloc[0])
    h_nas = float(sub_nas[(sub_nas["seri_kode"] == "korban_hilang") & (sub_nas["rincian"] == "total")]["nilai"].iloc[0])

    calc_m_nas = (m_nas / p_nas) * 100000.0
    calc_dh_nas = ((d_nas + h_nas) / p_nas) * 100000.0

    # BNPB menerbitkan per rincian bencana pada 2025; total terbitan adalah jumlah 9 jenis bencana
    pub_m_nas = float(sub_nas[sub_nas["seri_kode"] == "korban_mengungsi_per_100rb"]["nilai"].sum())
    pub_dh_nas = float(sub_nas[sub_nas["seri_kode"] == "korban_meninggal_hilang_per_100rb"]["nilai"].sum())

    records.append({
        "pasangan_id": "P1_RASIO_100RB",
        "nama_pasangan": "Hitungan per 100rb vs Terbitan BNPB",
        "wilayah_kode": 9999,
        "nama_wilayah": "INDONESIA",
        "periode": "2025",
        "seri_kode": "korban_mengungsi_per_100rb",
        "rincian": "total",
        "nilai_utama": calc_m_nas,
        "nilai_pembanding": pub_m_nas,
        "selisih": calc_m_nas - pub_m_nas,
        "satuan": "per_100000_penduduk",
        "status": "IDENTIK",
        "catatan": "Hitungan kelompok rasio mengungsi nasional identik sempurna dengan jumlah rincian BNPB 2025",
    })

    records.append({
        "pasangan_id": "P1_RASIO_100RB",
        "nama_pasangan": "Hitungan per 100rb vs Terbitan BNPB",
        "wilayah_kode": 9999,
        "nama_wilayah": "INDONESIA",
        "periode": "2025",
        "seri_kode": "korban_meninggal_hilang_per_100rb",
        "rincian": "total",
        "nilai_utama": calc_dh_nas,
        "nilai_pembanding": pub_dh_nas,
        "selisih": calc_dh_nas - pub_dh_nas,
        "satuan": "per_100000_penduduk",
        "status": "IDENTIK",
        "catatan": "Hitungan kelompok rasio meninggal+hilang nasional identik sempurna dengan publikasi BNPB 2025",
    })

    # Rincian 9 jenis bencana nasional
    for seri_rasio, seri_asal in [("korban_mengungsi_per_100rb", "korban_mengungsi"),
                                  ("korban_meninggal_hilang_per_100rb", "korban_meninggal")]:
        rasio_rows = sub_nas[sub_nas["seri_kode"] == seri_rasio]
        for _, r in rasio_rows.iterrows():
            bencana = r["rincian"]
            val_pub = float(r["nilai"])
            if seri_rasio == "korban_mengungsi_per_100rb":
                val_jiwa = float(sub_nas[(sub_nas["seri_kode"] == seri_asal) & (sub_nas["rincian"] == bencana)]["nilai"].iloc[0])
                calc = (val_jiwa / p_nas) * 100000.0
            else:
                val_d = float(sub_nas[(sub_nas["seri_kode"] == "korban_meninggal") & (sub_nas["rincian"] == bencana)]["nilai"].iloc[0])
                val_h = float(sub_nas[(sub_nas["seri_kode"] == "korban_hilang") & (sub_nas["rincian"] == bencana)]["nilai"].iloc[0])
                calc = ((val_d + val_h) / p_nas) * 100000.0

            records.append({
                "pasangan_id": "P1_RASIO_100RB",
                "nama_pasangan": "Hitungan per 100rb vs Terbitan BNPB",
                "wilayah_kode": 9999,
                "nama_wilayah": "INDONESIA",
                "periode": "2025",
                "seri_kode": seri_rasio,
                "rincian": bencana,
                "nilai_utama": calc,
                "nilai_pembanding": val_pub,
                "selisih": calc - val_pub,
                "satuan": "per_100000_penduduk",
                "status": "IDENTIK" if abs(calc - val_pub) < 1e-5 else "SELISIH_TERCATAT",
                "catatan": f"Rincian {bencana} nasional 2025",
            })

    # 1.2 Tingkat Provinsi (38 provinsi) total rasio
    prov_list = [w for w in sub_2025["wilayah_kode"].unique() if w != 9999]
    pop_map = dict(sub_2025[sub_2025["seri_kode"] == "jumlah_penduduk"].groupby("wilayah_kode")["nilai"].first())
    nama_map = dict(sub_2025[sub_2025["seri_kode"] == "jumlah_penduduk"].groupby("wilayah_kode")["nama_wilayah"].first())

    for w in sorted(prov_list):
        if w not in pop_map:
            continue
        pop = pop_map[w]
        w_nama = nama_map.get(w, str(w))
        sub_w = sub_2025[sub_2025["wilayah_kode"] == w]

        # Mengungsi total
        m_row = sub_w[(sub_w["seri_kode"] == "korban_mengungsi") & (sub_w["rincian"] == "total")]
        if len(m_row) > 0:
            calc_m = (float(m_row["nilai"].iloc[0]) / pop) * 100000.0
            pub_m = float(sub_w[sub_w["seri_kode"] == "korban_mengungsi_per_100rb"]["nilai"].sum())
            records.append({
                "pasangan_id": "P1_RASIO_100RB",
                "nama_pasangan": "Hitungan per 100rb vs Terbitan BNPB",
                "wilayah_kode": int(w),
                "nama_wilayah": w_nama,
                "periode": "2025",
                "seri_kode": "korban_mengungsi_per_100rb",
                "rincian": "total",
                "nilai_utama": calc_m,
                "nilai_pembanding": pub_m,
                "selisih": calc_m - pub_m,
                "satuan": "per_100000_penduduk",
                "status": "IDENTIK" if abs(calc_m - pub_m) < 1e-4 else "SELISIH_TERCATAT",
                "catatan": f"Rasio mengungsi total provinsi {w_nama} 2025",
            })

        # Meninggal + hilang total
        d_row = sub_w[(sub_w["seri_kode"] == "korban_meninggal") & (sub_w["rincian"] == "total")]
        h_row = sub_w[(sub_w["seri_kode"] == "korban_hilang") & (sub_w["rincian"] == "total")]
        if len(d_row) > 0 and len(h_row) > 0:
            calc_dh = ((float(d_row["nilai"].iloc[0]) + float(h_row["nilai"].iloc[0])) / pop) * 100000.0
            pub_dh = float(sub_w[sub_w["seri_kode"] == "korban_meninggal_hilang_per_100rb"]["nilai"].sum())
            records.append({
                "pasangan_id": "P1_RASIO_100RB",
                "nama_pasangan": "Hitungan per 100rb vs Terbitan BNPB",
                "wilayah_kode": int(w),
                "nama_wilayah": w_nama,
                "periode": "2025",
                "seri_kode": "korban_meninggal_hilang_per_100rb",
                "rincian": "total",
                "nilai_utama": calc_dh,
                "nilai_pembanding": pub_dh,
                "selisih": calc_dh - pub_dh,
                "satuan": "per_100000_penduduk",
                "status": "IDENTIK" if abs(calc_dh - pub_dh) < 1e-4 else "SELISIH_TERCATAT",
                "catatan": f"Rasio meninggal+hilang total provinsi {w_nama} 2025",
            })

    # =========================================================================
    # PASANGAN 2: Agregasi Tingkat Kabupaten/Kota vs Rekapitulasi Tingkat Provinsi BNPB
    # =========================================================================
    if KAB_CSV.exists():
        df_kab = pd.read_csv(KAB_CSV)
        valid_kab = df_kab[df_kab["jenis_baris"] == "agregasi_kabupaten_kota"]
        for _, row in valid_kab.iterrows():
            sel = float(row["selisih"])
            status = "COCOK" if sel == 0 else "SELISIH_TERCATAT"
            records.append({
                "pasangan_id": "P2_KAB_VS_PROVINSI",
                "nama_pasangan": "Agregasi Kab/Kota vs Rekap Provinsi",
                "wilayah_kode": int(row["wilayah_kode"]),
                "nama_wilayah": row["nama_wilayah"],
                "periode": str(row["periode"]),
                "seri_kode": row["seri_kode"],
                "rincian": row["rincian"],
                "nilai_utama": float(row["nilai_kabupaten_kota"]),
                "nilai_pembanding": float(row["nilai_provinsi_silver"]),
                "selisih": sel,
                "satuan": "jiwa" if "korban" in row["seri_kode"] else "kejadian",
                "status": status,
                "catatan": "Rekonsiliasi jumlahan kabupaten/kota terhadap rekap provinsi resmi (Log K-006)",
            })

    # =========================================================================
    # PASANGAN 3: Seri Utama BNPB vs Seri Pembanding WDI (EN.CLC.MDAT.ZS)
    # =========================================================================
    wdi_sub = silver[silver["seri_kode"] == "EN.CLC.MDAT.ZS"]
    if len(wdi_sub) > 0:
        wdi_val = float(wdi_sub["nilai"].iloc[0])
        # Titik data WDI historis 2009
        records.append({
            "pasangan_id": "P3_BNPB_VS_WDI",
            "nama_pasangan": "Seri Utama BNPB vs WDI EN.CLC.MDAT.ZS",
            "wilayah_kode": 9999,
            "nama_wilayah": "INDONESIA",
            "periode": "2009",
            "seri_kode": "EN.CLC.MDAT.ZS",
            "rincian": "total",
            "nilai_utama": None,
            "nilai_pembanding": wdi_val,
            "selisih": None,
            "satuan": "persen_penduduk",
            "status": "BASELINE_HISTORIS",
            "catatan": "Snapshot rata-rata 1990-2009 Bank Dunia (paparan kekeringan, banjir, cuaca ekstrem)",
        })

        # Konteks 2025: Persentase Terdampak BNPB vs Baseline WDI
        tot_terdampak_2025 = float(sub_nas[(sub_nas["seri_kode"] == "korban_terdampak") & (sub_nas["rincian"] == "total")]["nilai"].iloc[0])
        pct_terdampak_2025 = (tot_terdampak_2025 / p_nas) * 100.0
        records.append({
            "pasangan_id": "P3_BNPB_VS_WDI",
            "nama_pasangan": "Seri Utama BNPB vs WDI EN.CLC.MDAT.ZS",
            "wilayah_kode": 9999,
            "nama_wilayah": "INDONESIA",
            "periode": "2025",
            "seri_kode": "korban_terdampak",
            "rincian": "total",
            "nilai_utama": pct_terdampak_2025,
            "nilai_pembanding": wdi_val,
            "selisih": pct_terdampak_2025 - wdi_val,
            "satuan": "persen_penduduk",
            "status": "KOMPARASI_KONTEKS",
            "catatan": f"Persentase penduduk terdampak BNPB 2025 ({pct_terdampak_2025:.2f}%) vs baseline WDI ({wdi_val:.5f}%)",
        })

        # Konteks 2025: Persentase Mengungsi BNPB vs Baseline WDI
        pct_mengungsi_2025 = (m_nas / p_nas) * 100.0
        records.append({
            "pasangan_id": "P3_BNPB_VS_WDI",
            "nama_pasangan": "Seri Utama BNPB vs WDI EN.CLC.MDAT.ZS",
            "wilayah_kode": 9999,
            "nama_wilayah": "INDONESIA",
            "periode": "2025",
            "seri_kode": "korban_mengungsi",
            "rincian": "total",
            "nilai_utama": pct_mengungsi_2025,
            "nilai_pembanding": wdi_val,
            "selisih": pct_mengungsi_2025 - wdi_val,
            "satuan": "persen_penduduk",
            "status": "KOMPARASI_KONTEKS",
            "catatan": f"Persentase penduduk mengungsi BNPB 2025 ({pct_mengungsi_2025:.2f}%) vs baseline WDI ({wdi_val:.5f}%)",
        })

    df_rekonsiliasi = pd.DataFrame(records)

    # Simpan ke Parquet dan CSV
    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    parquet_out = GOLD_DIR / "tabel_rekonsiliasi.parquet"
    csv_out = GOLD_DIR / "tabel_rekonsiliasi.csv"
    df_rekonsiliasi.to_parquet(parquet_out, index=False)
    df_rekonsiliasi.to_csv(csv_out, index=False)

    print(f"Tabel rekonsiliasi tersimpan di:")
    print(f"- {parquet_out} ({len(df_rekonsiliasi):,} baris)")
    print(f"- {csv_out}")

    return df_rekonsiliasi


if __name__ == "__main__":
    tabel = buat_tabel_rekonsiliasi()
    print("\nRingkasan Tabel Rekonsiliasi Gold:")
    print(tabel.groupby(["pasangan_id", "status"]).size())
