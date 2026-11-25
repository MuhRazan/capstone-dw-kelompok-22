"""Aturan validasi Gold dan rekonsiliasi (Sprint 2), berlaku untuk semua kasus.

Setiap aturan = (nama, keterangan, keras, fungsi(silver, gold) -> DataFrame baris yang melanggar).
Aturan keras menghentikan pipeline bila ada baris yang melanggar.
"""
from pathlib import Path
import pandas as pd

from src.silver.deret import JUMLAH

STATUS = {"terisi", "missing", "tidak_diterbitkan", "belum_ada", "batas_lama"}
KUNCI_PANEL = ["indikator", "wilayah_kode", "periode"]
KATEGORI = {
    "definisi berbeda",
    "metode berbeda",
    "vintage berbeda",
    "cakupan berbeda",
    "belum terjelaskan",
    "tanpa pasangan",
    "tidak berselisih",
}


def kunci_panel_unik(silver, gold):
    p = gold["panel"]
    return p[p.duplicated(KUNCI_PANEL, keep=False)]


def satu_satuan_per_indikator(silver, gold):
    p = gold["panel"]
    n = p.groupby("indikator")["satuan"].nunique()
    return p[p["indikator"].isin(n[n != 1].index) | p["satuan"].isna()]


def status_dan_nilai(silver, gold):
    p = gold["panel"]
    return p[~p["status_sel"].isin(STATUS) | ((p["status_sel"] == "terisi") != p["nilai"].notna())]


def tertelusur_ke_silver(silver, gold):
    """Setiap sel terisi punya baris Silver dengan seri, wilayah, periode, dan berkas yang sama."""
    p = gold["panel"]
    p_terisi = p[p["status_sel"] == "terisi"]
    s = silver[["seri_kode", "wilayah_kode", "periode", "rincian", "_berkas_raw", "nilai"]]
    biasa = p_terisi[p_terisi["rincian"] != JUMLAH].merge(
        s, on=["seri_kode", "wilayah_kode", "periode", "rincian", "_berkas_raw"],
        how="left", suffixes=("", "_silver"), indicator=True
    )
    jml = p_terisi[p_terisi["rincian"] == JUMLAH].merge(
        s.drop(columns=["rincian", "nilai"]).drop_duplicates(),
        on=["seri_kode", "wilayah_kode", "periode", "_berkas_raw"],
        how="left", indicator=True
    )
    buruk = pd.concat([biasa[biasa["_merge"] != "both"], jml[jml["_merge"] != "both"]])
    return buruk.drop(columns="_merge")


def nilai_sama_dengan_silver(silver, gold):
    p = gold["panel"]
    p_terisi = p[(p["status_sel"] == "terisi") & (p["rincian"] != JUMLAH)]
    s = silver[["seri_kode", "wilayah_kode", "periode", "rincian", "_berkas_raw", "nilai"]]
    m = p_terisi.merge(s, on=["seri_kode", "wilayah_kode", "periode", "rincian", "_berkas_raw"], suffixes=("", "_silver"))
    return m[(m["nilai"] - m["nilai_silver"]).abs() > 1e-9]


def nasional_unik(silver, gold):
    n = gold["nasional"]
    kunci = ["seri_kode", "rincian", "periode"] if "rincian" in n.columns else ["seri_kode", "periode"]
    return n[n.duplicated(kunci, keep=False)]


def kategori_baku(silver, gold):
    r = gold["rekonsiliasi"]
    kat_col = r["kategori"] if "kategori" in r.columns else r["kategori_penjelasan"]
    penj_col = r["penjelasan"] if "penjelasan" in r.columns else r["catatan"]
    return r[~kat_col.isin(KATEGORI) | penj_col.isna() | (penj_col.str.strip() == "")]


def selisih_konsisten(silver, gold):
    r = gold["rekonsiliasi"]
    u_col = r["nilai_utama"] if "nilai_utama" in r.columns else r["nilai_seri_utama"]
    h = r[r["selisih"].notna()]
    return h[(h["selisih"] - (u_col.loc[h.index] - h["nilai_pembanding"])).abs() > 1e-6]


def berpasangan_dihitung(silver, gold):
    """Baris yang kedua nilainya ada harus punya selisih atau catatan."""
    r = gold["rekonsiliasi"]
    u_col = r["nilai_utama"] if "nilai_utama" in r.columns else r["nilai_seri_utama"]
    penj_col = r["penjelasan"] if "penjelasan" in r.columns else r["catatan"]
    dua_sisi = r[u_col.notna() & r["nilai_pembanding"].notna()]
    penj_dua = penj_col.loc[dua_sisi.index]
    return dua_sisi[dua_sisi["selisih"].isna() & (penj_dua.isna() | (penj_dua.str.strip() == ""))]


def periode_utama_tampil(silver, gold):
    """Semua periode observasi (2009 s.d. 2025) tampil di tabel rekonsiliasi."""
    r = gold["rekonsiliasi"]
    thn_silver = set(silver["periode"].unique())
    thn_rek = set(r["periode"].unique())
    hilang = thn_silver - thn_rek
    if hilang:
        return pd.DataFrame([{"periode_hilang": th} for th in sorted(hilang)])
    return pd.DataFrame()


ATURAN = [
    ("gold: kunci panel unik", "indikator + wilayah_kode + periode tidak kembar", True, kunci_panel_unik),
    ("gold: satu satuan per indikator", "satu indikator panel hanya punya satu satuan", True, satu_satuan_per_indikator),
    ("gold: status sel dan nilai", "status sel baku; nilai ada jika dan hanya jika sel terisi", True, status_dan_nilai),
    ("gold: sel tertelusur ke Silver", "setiap sel terisi punya baris Silver asal (seri, wilayah, periode, berkas)",
     True, tertelusur_ke_silver),
    ("gold: nilai sama dengan Silver", "nilai panel = nilai Silver asalnya (tidak ada nilai yang diubah di Gold)",
     True, nilai_sama_dengan_silver),
    ("gold: tabel nasional unik", "seri + rincian + periode tidak kembar", True, nasional_unik),
    ("rekonsiliasi: kategori baku", "kategori dari daftar baku; penjelasan tidak kosong", True, kategori_baku),
    ("rekonsiliasi: selisih = utama − pembanding", "selisih dihitung ulang dan cocok", True, selisih_konsisten),
    ("rekonsiliasi: baris berpasangan dihitung", "pasangan selisih dengan dua nilai punya selisih, atau catatan mengapa tidak",
     True, berpasangan_dihitung),
    ("rekonsiliasi: periode utama tidak dibuang", "setiap tahun seri utama di tabel nasional muncul di rekonsiliasi",
     True, periode_utama_tampil),
]
