"""Tahap 2-4 - Profil, pembersihan, dan penyeragaman ke Silver (pertemuan II-VII). Milik tim.

Keluaran: data/silver/silver.parquet dengan skema minimal di src/common/skema.py.
Satu baris = satu seri x wilayah x periode x rincian x berkas sumber. Nilai dari sumber berbeda
TIDAK digabung di sini. Setiap keputusan pembersihan dicatat di log-keputusan.csv.
"""
import re
from pathlib import Path

import pandas as pd

SILVER = Path("data/silver/silver.parquet")

# indikator mentah -> (seri_kode, satuan). Sumber satuan: judul kolom/grup di XLSX dan
# data/KASUS.md; kerusakan (unit) tidak dipakai karena milik kasus 23.
SERI = {
    "Jumlah Bencana 2025": ("kejadian", "kejadian"),
    "Meninggal 2025": ("korban_meninggal", "jiwa"),
    "Hilang 2025": ("korban_hilang", "jiwa"),
    "Luka_Sakit 2025": ("korban_luka_sakit", "jiwa"),
    "Terdampak 2025": ("korban_terdampak", "jiwa"),
    "Mengungsi 2025": ("korban_mengungsi", "jiwa"),
    "Mengungsi Per 100rb org 2025": ("korban_mengungsi_per_100rb", "per_100000_penduduk"),
    "MD_Hilang Per 100rb org 2025": ("korban_meninggal_hilang_per_100rb", "per_100000_penduduk"),
    "Jumlah Kejadian": ("kejadian", "kejadian"),
    "Korban Meninggal": ("korban_meninggal", "jiwa"),
    "Korban Hilang": ("korban_hilang", "jiwa"),
    "Korban Luka-Luka": ("korban_luka_sakit", "jiwa"),
    "Korban Terdampak - Mengungsi": ("korban_terdampak_mengungsi", "jiwa"),
    "Meninggal": ("korban_meninggal", "jiwa"),
    "Hilang": ("korban_hilang", "jiwa"),
    "Luka": ("korban_luka_sakit", "jiwa"),
    "Terdampak": ("korban_terdampak", "jiwa"),
    "Mengungsi": ("korban_mengungsi", "jiwa"),
}

# ejaan jenis bencana tidak seragam antarberkas -> satu kode rincian
BENCANA = {
    "BANJIR": "banjir",
    "CUACA EKSTREM": "cuaca_ekstrem",
    "GELOMBANG PASANG DAN ABRASI": "gelombang_pasang_dan_abrasi",
    "GELOMBANG PASANG / ABRASI": "gelombang_pasang_dan_abrasi",
    "GEMPABUMI": "gempabumi",
    "GEMPA BUMI": "gempabumi",
    "KEBAKARAN HUTAN DAN LAHAN": "kebakaran_hutan_dan_lahan",
    "KEKERINGAN": "kekeringan",
    "ERUPSI GUNUNG API": "erupsi_gunung_api",
    "LETUSAN GUNUNG API": "erupsi_gunung_api",
    "TANAH LONGSOR": "tanah_longsor",
    "TSUNAMI": "tsunami",
}

# nama provinsi yang hanya muncul di rekap 2021/2022
ALIAS = {"DI YOGYAKARTA": 3400}
INDONESIA = 9999

KOLOM = ["sumber", "seri_kode", "wilayah_kode", "nama_wilayah", "periode", "jenis_periode",
         "rincian", "nilai", "satuan", "_berkas_raw", "_sha256_raw"]


def _norm(nama) -> str:
    return re.sub(r"\s+", " ", str(nama).strip().upper())


def _peta_wilayah(d: pd.DataFrame) -> dict:
    """{nama provinsi: kode BPS x100} dari baris yang punya kode wilayah."""
    ada = d[d["Kode Wilayah Provinsi"].notna()]
    return {_norm(n): int(float(k)) * 100
            for k, n in ada[["Kode Wilayah Provinsi", "Provinsi"]].drop_duplicates().itertuples(index=False)}


def _kerangka(d: pd.DataFrame, peta: dict) -> pd.DataFrame:
    d = d.copy()
    d["_nama"] = d["Provinsi"].map(_norm)
    kode = pd.to_numeric(d["Kode Wilayah Provinsi"], errors="coerce")
    d["wilayah_kode"] = (kode * 100).astype("Int64")
    d.loc[d["wilayah_kode"].isna() & d["_nama"].eq("INDONESIA"), "wilayah_kode"] = INDONESIA
    d.loc[d["wilayah_kode"].isna() & d["format_asal"].eq("rekapitulasi_2025"), "wilayah_kode"] = INDONESIA
    kurang = d["wilayah_kode"].isna()
    d.loc[kurang, "wilayah_kode"] = d.loc[kurang, "_nama"].map(peta).astype("Int64")
    d.loc[kurang, "wilayah_kode"] = d.loc[kurang, "_nama"].map(ALIAS).fillna(d.loc[kurang, "wilayah_kode"])

    seri = d["indikator"].map(SERI)
    d["seri_kode"] = seri.str[0]
    d["satuan"] = seri.str[1]

    bencana = d["jenis_bencana"].where(d["jenis_bencana"].notna(), d.get("Jenis Bencana"))
    d["rincian"] = bencana.map(lambda x: BENCANA.get(_norm(x), "total") if pd.notna(x) else "total")

    d["nilai"] = pd.to_numeric(d["nilai"], errors="coerce")
    d["periode"] = d["tahun"].astype(int).astype(str)
    d["jenis_periode"] = "tahun"
    d["nama_wilayah"] = d["_nama"]
    d["sumber"] = "bnpb"
    return d


def _penduduk(d: pd.DataFrame) -> pd.DataFrame:
    """Seri jumlah_penduduk: satu berkas kanonik, satu baris per wilayah."""
    ada = d[d["Jumlah Penduduk"].notna()].sort_values("_berkas_raw")
    if ada.empty:
        return ada
    kanonik = ada["_berkas_raw"].iloc[0]
    p = ada[ada["_berkas_raw"] == kanonik].drop_duplicates(["wilayah_kode", "periode"])
    p = p.assign(seri_kode="jumlah_penduduk", satuan="jiwa", rincian="total",
                 nilai=pd.to_numeric(p["Jumlah Penduduk"], errors="coerce"))
    return p


def jalankan(mentah):
    """Terima keluaran tahap 1, tulis dan kembalikan DataFrame Silver."""
    d = pd.concat(mentah.values(), ignore_index=True)
    peta = _peta_wilayah(d)

    # baris kabupaten/kota tidak dipakai: rekap provinsi tahun yang sama sudah ada (K-006)
    kab = d["_berkas_raw"].str.contains("kabupaten|kabupten", case=False, regex=True)
    d = d[~kab]
    d = _kerangka(d, peta)

    belum = sorted(d.loc[d["wilayah_kode"].isna(), "_nama"].dropna().unique())
    if belum:
        raise ValueError(f"nama wilayah tidak terpetakan ke kode BPS: {belum}")
    tanpa_seri = sorted(d.loc[d["seri_kode"].isna(), "indikator"].dropna().unique())
    d = d[d["seri_kode"].notna() & d["nilai"].notna()]

    pend = _penduduk(d)
    kolom = KOLOM + ["Jumlah Penduduk", "format_asal", "indikator"]
    silver = pd.concat([d[kolom], pend[kolom]], ignore_index=True)[KOLOM]
    silver = silver.drop_duplicates()

    kembar = silver.duplicated(["sumber", "seri_kode", "wilayah_kode", "periode", "rincian", "_berkas_raw"])
    if kembar.any():
        raise ValueError(f"{int(kembar.sum())} baris kembar pada kunci Silver")

    silver = silver.astype({"wilayah_kode": "int64", "periode": "string"})
    SILVER.parent.mkdir(parents=True, exist_ok=True)
    silver.to_parquet(SILVER, index=False)
    print(f"Silver: {len(silver):,} baris, {silver['seri_kode'].nunique()} seri, "
          f"{silver['wilayah_kode'].nunique()} wilayah, {silver['_berkas_raw'].nunique()} berkas; "
          f"kerusakan dilewati: {len(tanpa_seri)} indikator")
    return silver
