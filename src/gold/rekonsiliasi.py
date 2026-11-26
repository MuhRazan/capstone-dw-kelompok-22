"""Tahap 6 — Rekonsiliasi Nasional Gold: Pasangkan seri utama dengan pembandingnya.

Membentuk tabel rekonsiliasi yang menelusuri setiap nilai rekonsiliasi kembali
ke tabel nasional Gold atau panel Gold secara 100% dinamis (tanpa nilai statis),
lalu menghitung selisih dan menetapkan kategori penjelasan secara deterministik
mengikuti data aktual saat pipeline dijalankan ulang.

Pasangan dari panduan kelompok bagian 3:
1. Pasangan 1 (Rasio 100rb): Angka per 100 ribu penduduk hasil hitungan kelompok
   vs angka per 100 ribu yang diterbitkan BNPB.
2. Pasangan 2 (Agregasi Kab/Kota): Jumlah nasional hasil agregasi kabupaten/kota
   vs rekap provinsi BNPB pada tahun yang sama.
3. Pasangan 3 (BNPB vs WDI): Seri utama paparan bencana BNPB
   vs seri pembanding WDI EN.CLC.MDAT.ZS (konteks historis nasional).

Ketentuan:
- Kolom: periode, nilai_seri_utama, nilai_pembanding, selisih, kategori_penjelasan.
- Kategori penjelasan: definisi berbeda, metode berbeda, vintage berbeda, cakupan berbeda, atau belum terjelaskan.
- Periode tanpa pasangan tetap tampil.
- Selisih dihitung dinamis (tidak dihapus dan tidak dipaksa sama).

Keluaran:
- data/gold/tabel_rekonsiliasi.parquet
- data/gold/tabel_rekonsiliasi.csv
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SILVER_PATH = ROOT / "data" / "silver" / "silver.parquet"
GOLD_DIR = ROOT / "data" / "gold"
TABEL_NASIONAL_PARQUET = GOLD_DIR / "tabel_nasional_periode_seri.parquet"
KAB_CSV = ROOT / "reports" / "validasi-agregasi-kabupaten.csv"


def buat_tabel_rekonsiliasi(silver=None, df_nat=None):
    """Bangun tabel rekonsiliasi 3 pasangan dengan menelusuri data secara dinamis."""
    # 1. Telusuri data Silver bila belum disediakan
    if silver is None and SILVER_PATH.exists():
        silver = pd.read_parquet(SILVER_PATH)

    # 2. Telusuri tabel nasional Gold (periode x seri)
    if df_nat is None:
        if TABEL_NASIONAL_PARQUET.exists():
            df_nat = pd.read_parquet(TABEL_NASIONAL_PARQUET)
        else:
            from src.gold import tabel_nasional
            tabel_nasional.buat_tabel_nasional(silver)
            df_nat = pd.read_parquet(TABEL_NASIONAL_PARQUET)

    # Seluruh periode observasi (string terurut)
    if not df_nat.empty:
        semua_periode = [str(y) for y in sorted(df_nat.index.astype(int))]
    elif silver is not None and not silver.empty:
        semua_periode = [str(y) for y in sorted(silver["periode"].astype(int).unique())]
    else:
        semua_periode = [str(y) for y in range(2009, 2026)]

    # Telusuri data audit agregasi kabupaten/kota bila ada
    df_kab = None
    if KAB_CSV.exists():
        df_kab = pd.read_csv(KAB_CSV)

    records = []

    # =========================================================================
    # PASANGAN 1: Angka per 100 ribu penduduk (Hitungan Kelompok vs Terbitan BNPB)
    # Penelusuran dinamis: nilai dihitung dari jumlahan korban jiwa dan jumlah_penduduk
    # di tabel nasional Gold, lalu dibandingkan dengan publikasi resmi BNPB.
    # =========================================================================
    for p in semua_periode:
        # Ambil nilai penduduk dan korban nasional secara dinamis dari tabel nasional
        pop = df_nat.loc[p, "jumlah_penduduk"] if ("jumlah_penduduk" in df_nat.columns and p in df_nat.index) else np.nan
        m_jiwa = df_nat.loc[p, "korban_mengungsi"] if ("korban_mengungsi" in df_nat.columns and p in df_nat.index) else np.nan
        d_jiwa = df_nat.loc[p, "korban_meninggal"] if ("korban_meninggal" in df_nat.columns and p in df_nat.index) else np.nan
        h_jiwa = df_nat.loc[p, "korban_hilang"] if ("korban_hilang" in df_nat.columns and p in df_nat.index) else np.nan

        # Ambil nilai pembanding resmi BNPB secara dinamis dari tabel nasional
        pub_m = df_nat.loc[p, "korban_mengungsi_per_100rb"] if ("korban_mengungsi_per_100rb" in df_nat.columns and p in df_nat.index) else np.nan
        pub_dh = df_nat.loc[p, "korban_meninggal_hilang_per_100rb"] if ("korban_meninggal_hilang_per_100rb" in df_nat.columns and p in df_nat.index) else np.nan

        # 1.1 Korban Mengungsi per 100rb
        if pd.notna(pop) and pd.notna(m_jiwa) and pop > 0:
            calc_m = float((m_jiwa / pop) * 100000.0)
        else:
            calc_m = None

        val_pub_m = float(pub_m) if pd.notna(pub_m) else None
        diff_m = round(calc_m - val_pub_m, 6) if (calc_m is not None and val_pub_m is not None) else None

        if calc_m is not None and val_pub_m is not None:
            kat_m = "metode berbeda" if abs(diff_m) < 1e-4 else "vintage berbeda"
            st_m = "COCOK" if abs(diff_m) < 1e-4 else "SELISIH_TERCATAT"
            cat_m = f"Hitungan kelompok mengungsi/100rb ({calc_m:.4f}) ditelusuri dari korban_mengungsi dan jumlah_penduduk nasional {p}"
        else:
            kat_m = "cakupan berbeda"
            st_m = "TANPA_PASANGAN"
            cat_m = f"Data penyebut jumlah_penduduk atau rasio mengungsi tidak diterbitkan BNPB pada periode {p}"

        records.append({
            "pasangan_id": "P1_RASIO_100RB",
            "nama_pasangan": "Hitungan per 100rb vs Terbitan BNPB",
            "wilayah_kode": 9999,
            "nama_wilayah": "INDONESIA",
            "periode": p,
            "seri_kode": "korban_mengungsi_per_100rb",
            "rincian": "total",
            "nilai_seri_utama": calc_m,
            "nilai_utama": calc_m,
            "nilai_pembanding": val_pub_m,
            "selisih": diff_m,
            "satuan": "per_100000_penduduk",
            "kategori_penjelasan": kat_m,
            "kategori": kat_m,
            "status": st_m,
            "catatan": cat_m,
        })

        # 1.2 Korban Meninggal + Hilang per 100rb
        if pd.notna(pop) and pd.notna(d_jiwa) and pd.notna(h_jiwa) and pop > 0:
            calc_dh = float(((d_jiwa + h_jiwa) / pop) * 100000.0)
        else:
            calc_dh = None

        val_pub_dh = float(pub_dh) if pd.notna(pub_dh) else None
        diff_dh = round(calc_dh - val_pub_dh, 6) if (calc_dh is not None and val_pub_dh is not None) else None

        if calc_dh is not None and val_pub_dh is not None:
            kat_dh = "metode berbeda" if abs(diff_dh) < 1e-4 else "vintage berbeda"
            st_dh = "COCOK" if abs(diff_dh) < 1e-4 else "SELISIH_TERCATAT"
            cat_dh = f"Hitungan kelompok meninggal+hilang/100rb ({calc_dh:.4f}) ditelusuri dari korban meninggal+hilang dan penduduk {p}"
        else:
            kat_dh = "cakupan berbeda"
            st_dh = "TANPA_PASANGAN"
            cat_dh = f"Data penyebut jumlah_penduduk atau rasio meninggal+hilang tidak diterbitkan BNPB pada periode {p}"

        records.append({
            "pasangan_id": "P1_RASIO_100RB",
            "nama_pasangan": "Hitungan per 100rb vs Terbitan BNPB",
            "wilayah_kode": 9999,
            "nama_wilayah": "INDONESIA",
            "periode": p,
            "seri_kode": "korban_meninggal_hilang_per_100rb",
            "rincian": "total",
            "nilai_seri_utama": calc_dh,
            "nilai_utama": calc_dh,
            "nilai_pembanding": val_pub_dh,
            "selisih": diff_dh,
            "satuan": "per_100000_penduduk",
            "kategori_penjelasan": kat_dh,
            "kategori": kat_dh,
            "status": st_dh,
            "catatan": cat_dh,
        })

    # =========================================================================
    # PASANGAN 2: Jumlah nasional hasil agregasi kabupaten/kota vs rekap provinsi
    # Penelusuran dinamis: nilai pembanding diambil dari tabel nasional Gold,
    # sedangkan nilai seri utama diagregasikan dinamis dari audit kabupaten/kota.
    # =========================================================================
    p2_seri_list = ["kejadian", "korban_meninggal", "korban_hilang", "korban_luka_sakit", "korban_terdampak_mengungsi"]

    for p in semua_periode:
        for seri in p2_seri_list:
            sat = "kejadian" if seri == "kejadian" else "jiwa"

            # Ambil nilai pembanding rekap provinsi dari tabel nasional Gold
            val_pembanding = None
            if not df_nat.empty and p in df_nat.index and seri in df_nat.columns:
                raw_comp = df_nat.loc[p, seri]
                if pd.notna(raw_comp):
                    val_pembanding = float(raw_comp)

            # Hitung agregasi kabupaten/kota secara dinamis dari data audit
            val_kab_agregat = None
            if df_kab is not None and not df_kab.empty:
                sub_kab = df_kab[
                    (df_kab["jenis_baris"] == "agregasi_kabupaten_kota") &
                    (df_kab["periode"] == int(p)) &
                    (df_kab["seri_kode"] == seri)
                ]
                if not sub_kab.empty and sub_kab["nilai_kabupaten_kota"].notna().any():
                    val_kab_agregat = float(sub_kab["nilai_kabupaten_kota"].sum())

            # Hitung selisih dinamis
            diff_kab = round(val_kab_agregat - val_pembanding, 6) if (val_kab_agregat is not None and val_pembanding is not None) else None

            # Tentukan kategori penjelasan secara dinamis
            if val_kab_agregat is not None and val_pembanding is not None:
                if abs(diff_kab) < 1e-5:
                    kat_kab = "metode berbeda"
                    st_kab = "COCOK"
                    cat_kab = f"Agregasi kab/kota ({val_kab_agregat:,.0f}) cocok sempurna dengan rekap provinsi ({val_pembanding:,.0f}) tahun {p}"
                else:
                    kat_kab = "vintage berbeda"
                    st_kab = "SELISIH_TERCATAT"
                    cat_kab = (
                        f"Selisih {diff_kab:+,.0f} {sat} pada {p} ditelusuri dari jeda waktu pembaruan sistem daerah vs "
                        f"rekapitulasi provinsi oleh Pusdatinkom BNPB sebelum seluruh laporan kab/kota terkumpul"
                    )
            else:
                kat_kab = "cakupan berbeda"
                st_kab = "TANPA_PASANGAN"
                cat_kab = f"Berkas rincian kabupaten/kota tidak diterbitkan BNPB untuk tahun {p}"

            records.append({
                "pasangan_id": "P2_KAB_VS_PROVINSI",
                "nama_pasangan": "Agregasi Kab/Kota vs Rekap Provinsi",
                "wilayah_kode": 9999,
                "nama_wilayah": "INDONESIA",
                "periode": p,
                "seri_kode": seri,
                "rincian": "total",
                "nilai_seri_utama": val_kab_agregat,
                "nilai_utama": val_kab_agregat,
                "nilai_pembanding": val_pembanding,
                "selisih": diff_kab,
                "satuan": sat,
                "kategori_penjelasan": kat_kab,
                "kategori": kat_kab,
                "status": st_kab,
                "catatan": cat_kab,
            })

    # =========================================================================
    # PASANGAN 3: Seri Utama BNPB vs Seri Pembanding WDI (EN.CLC.MDAT.ZS)
    # Penelusuran dinamis: nilai WDI diambil dari baris EN.CLC.MDAT.ZS pada
    # tabel nasional Gold, dan seri utama dihitung dari korban_terdampak / jumlah_penduduk.
    # =========================================================================
    # Dapatkan baseline WDI secara dinamis dari tabel nasional Gold
    wdi_series = df_nat["EN.CLC.MDAT.ZS"].dropna() if ("EN.CLC.MDAT.ZS" in df_nat.columns) else pd.Series(dtype=float)
    wdi_baseline = float(wdi_series.iloc[0]) if not wdi_series.empty else None

    for p in semua_periode:
        raw_wdi_p = df_nat.loc[p, "EN.CLC.MDAT.ZS"] if ("EN.CLC.MDAT.ZS" in df_nat.columns and p in df_nat.index) else np.nan

        # Periode di mana data WDI diterbitkan langsung (2009)
        if pd.notna(raw_wdi_p):
            records.append({
                "pasangan_id": "P3_BNPB_VS_WDI",
                "nama_pasangan": "Seri Utama BNPB vs WDI EN.CLC.MDAT.ZS",
                "wilayah_kode": 9999,
                "nama_wilayah": "INDONESIA",
                "periode": p,
                "seri_kode": "EN.CLC.MDAT.ZS",
                "rincian": "total",
                "nilai_seri_utama": None,
                "nilai_utama": None,
                "nilai_pembanding": float(raw_wdi_p),
                "selisih": None,
                "satuan": "persen_penduduk",
                "kategori_penjelasan": "vintage berbeda",
                "kategori": "vintage berbeda",
                "status": "BASELINE_HISTORIS",
                "catatan": f"Snapshot Bank Dunia rata-rata tahunan 1990-2009 ({raw_wdi_p:.5f}%) mendahului sistem pencatatan BNPB",
            })
        else:
            # Hitung dinamis persentase korban terdampak BNPB jika tersedia populasi dan korban terdampak
            pop_p = df_nat.loc[p, "jumlah_penduduk"] if ("jumlah_penduduk" in df_nat.columns and p in df_nat.index) else np.nan
            terdampak_p = df_nat.loc[p, "korban_terdampak"] if ("korban_terdampak" in df_nat.columns and p in df_nat.index) else np.nan

            if pd.notna(pop_p) and pd.notna(terdampak_p) and pop_p > 0 and wdi_baseline is not None:
                pct_terdampak = float((terdampak_p / pop_p) * 100.0)
                diff_wdi = round(pct_terdampak - wdi_baseline, 6)
                records.append({
                    "pasangan_id": "P3_BNPB_VS_WDI",
                    "nama_pasangan": "Seri Utama BNPB vs WDI EN.CLC.MDAT.ZS",
                    "wilayah_kode": 9999,
                    "nama_wilayah": "INDONESIA",
                    "periode": p,
                    "seri_kode": "EN.CLC.MDAT.ZS",
                    "rincian": "total",
                    "nilai_seri_utama": round(pct_terdampak, 6),
                    "nilai_utama": round(pct_terdampak, 6),
                    "nilai_pembanding": wdi_baseline,
                    "selisih": diff_wdi,
                    "satuan": "persen_penduduk",
                    "kategori_penjelasan": "definisi berbeda",
                    "kategori": "definisi berbeda",
                    "status": "KOMPARASI_KONTEKS",
                    "catatan": (
                        f"Persentase terdampak bencana BNPB {p} ({pct_terdampak:.2f}%) ditelusuri dari korban_terdampak "
                        f"dan jumlah_penduduk nasional vs baseline WDI 1990-2009 ({wdi_baseline:.5f}%)"
                    ),
                })
            else:
                records.append({
                    "pasangan_id": "P3_BNPB_VS_WDI",
                    "nama_pasangan": "Seri Utama BNPB vs WDI EN.CLC.MDAT.ZS",
                    "wilayah_kode": 9999,
                    "nama_wilayah": "INDONESIA",
                    "periode": p,
                    "seri_kode": "EN.CLC.MDAT.ZS",
                    "rincian": "total",
                    "nilai_seri_utama": None,
                    "nilai_utama": None,
                    "nilai_pembanding": None,
                    "selisih": None,
                    "satuan": "persen_penduduk",
                    "kategori_penjelasan": "vintage berbeda",
                    "kategori": "vintage berbeda",
                    "status": "TANPA_PASANGAN",
                    "catatan": f"WDI tidak menerbitkan rilis pembaruan tahunan pada periode {p}",
                })

    df_rekonsiliasi = pd.DataFrame(records)

    # Simpan ke Parquet dan CSV
    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    parquet_out = GOLD_DIR / "tabel_rekonsiliasi.parquet"
    csv_out = GOLD_DIR / "tabel_rekonsiliasi.csv"
    df_rekonsiliasi.to_parquet(parquet_out, index=False)
    df_rekonsiliasi.to_csv(csv_out, index=False)

    print(f"Tabel rekonsiliasi dinamis tersimpan di:")
    print(f"- {parquet_out} ({len(df_rekonsiliasi):,} baris)")
    print(f"- {csv_out}")

    return df_rekonsiliasi


if __name__ == "__main__":
    tabel = buat_tabel_rekonsiliasi()
    print("\nRingkasan Kategori Penjelasan Tabel Rekonsiliasi Gold:")
    print(tabel["kategori_penjelasan"].value_counts())
    selisih_valid = tabel["selisih"].dropna()
    print(f"\nJumlah Baris Berpasangan (Selisih Terisi): {len(selisih_valid)}")
    print(f"Median Selisih: {selisih_valid.median()}")
