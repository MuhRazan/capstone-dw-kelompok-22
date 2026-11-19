"""Tahap 2-4 - Profil, pembersihan, dan penyeragaman ke Silver (pertemuan II-VII). Milik tim.

Keluaran: data/silver/silver.parquet dengan skema minimal di src/common/skema.py.
Satu baris = satu seri x wilayah x periode x rincian x berkas sumber. Nilai dari sumber berbeda
TIDAK digabung di sini. Setiap keputusan pembersihan dicatat di log-keputusan.csv.
"""
import re
from pathlib import Path

import pandas as pd

SILVER = Path("data/silver/silver.parquet")

# indikator mentah -> seri_kode. Satuan per seri ada di SATUAN (diverifikasi di
# docs/katalog-seri.csv); kerusakan (unit) tidak dipakai karena milik kasus 23.
SERI = {
    "Jumlah Bencana 2025": "kejadian",
    "Meninggal 2025": "korban_meninggal",
    "Hilang 2025": "korban_hilang",
    "Luka_Sakit 2025": "korban_luka_sakit",
    "Terdampak 2025": "korban_terdampak",
    "Mengungsi 2025": "korban_mengungsi",
    "Mengungsi Per 100rb org 2025": "korban_mengungsi_per_100rb",
    "MD_Hilang Per 100rb org 2025": "korban_meninggal_hilang_per_100rb",
    "Jumlah Kejadian": "kejadian",
    "Korban Meninggal": "korban_meninggal",
    "Korban Hilang": "korban_hilang",
    "Korban Luka-Luka": "korban_luka_sakit",
    "Korban Terdampak - Mengungsi": "korban_terdampak_mengungsi",
    "Meninggal": "korban_meninggal",
    "Hilang": "korban_hilang",
    "Luka": "korban_luka_sakit",
    "Terdampak": "korban_terdampak",
    "Mengungsi": "korban_mengungsi",
}

# seri -> satuan (lihat docs/katalog-seri.csv; sisanya jiwa)
SATUAN = {
    "kejadian": "kejadian",
    "korban_mengungsi_per_100rb": "per_100000_penduduk",
    "korban_meninggal_hilang_per_100rb": "per_100000_penduduk",
    "EN.CLC.MDAT.ZS": "persen_penduduk",
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


def _satuan(seri) -> str:
    return SATUAN.get(seri, "jiwa")


def _peta_wilayah(d: pd.DataFrame) -> dict:
    """{nama provinsi: kode BPS x100} dari baris yang punya kode wilayah."""
    if not {"Kode Wilayah Provinsi"} <= set(d.columns):
        return {}
    nama = next((c for c in ("Provinsi", "Nama Provinsi")
                 if c in d.columns and d[c].notna().any()), None)
    if nama is None:
        return {}
    ada = d[d["Kode Wilayah Provinsi"].notna() & d[nama].notna()]
    return {_norm(n): int(float(k)) * 100
            for k, n in ada[["Kode Wilayah Provinsi", nama]].drop_duplicates().itertuples(index=False)}


def _wilayah(d: pd.DataFrame, peta: dict) -> None:
    """Isi kolom _nama dan wilayah_kode in-place."""
    nama = next((c for c in ("Provinsi", "Nama Provinsi")
                 if c in d.columns and d[c].notna().any()), None)
    if nama is None:
        d["_nama"] = "INDONESIA"
        d["_nasional"] = True
    else:
        # baris tanpa nama provinsi = baris total nasional
        d["_nama"] = d[nama].map(_norm).where(d[nama].notna(), "INDONESIA")
        d["_nasional"] = False
    kode = pd.to_numeric(d.get("Kode Wilayah Provinsi"), errors="coerce")
    d["wilayah_kode"] = (kode * 100).astype("Int64")
    kosong = d["wilayah_kode"].isna()
    d.loc[kosong, "wilayah_kode"] = d.loc[kosong, "_nama"].map({**peta, **ALIAS}).astype("Int64")
    d.loc[d["_nama"].isin(["INDONESIA", "TOTAL"]), "wilayah_kode"] = INDONESIA


def _angka(s) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def _dari_xlsx(d: pd.DataFrame, peta: dict) -> pd.DataFrame:
    # baris kabupaten/kota tidak dipakai: rekap provinsi tahun yang sama sudah ada (K-006)
    kab = d["_berkas_raw"].str.contains("kabupaten|kabupten", case=False, regex=True)
    d = d[~kab].copy()
    _wilayah(d, peta)
    # berkas rekapitulasi 2025 hanya berisi baris total nasional
    d["_nasional"] = d["format_asal"].eq("rekapitulasi_2025")

    bencana = d["jenis_bencana"].where(d["jenis_bencana"].notna(), d.get("Jenis Bencana"))
    d["rincian"] = bencana.map(lambda x: BENCANA.get(_norm(x), "total") if pd.notna(x) else "total")
    d["seri_kode"] = d["indikator"].map(SERI)
    d["nilai"] = _angka(d["nilai"])
    d["periode"] = d["tahun"].astype("Int64").astype("string")
    d["sumber"] = "bnpb_xlsx"
    return d


def _json_satu(d: pd.DataFrame, peta: dict) -> pd.DataFrame:
    """Satu berkas datastore: kabupaten/kota dilewati (K-006)."""
    d = d.copy()
    _wilayah(d, peta)
    # berkas satu tahun: tidak ada kolom tahun, tahun diambil dari nama resource
    if d["tahun"].isna().all():
        d["tahun"] = d["resource_nama"].iloc[0][-4:]
        d["tahun"] = _angka(d["tahun"]).astype("Int64")
    d["seri_kode"] = d["seri"]
    d["nilai"] = _angka(d["nilai"])
    d["periode"] = d["tahun"].astype("Int64").astype("string")
    d["sumber"] = "bnpb_json"
    return d


def _dari_json(d: pd.DataFrame, peta: dict) -> pd.DataFrame:
    # satu berkas = satu tabel; kolom bencana hanya ada di berkas satu tahun
    d = d[d["seri"].ne("ckan_metadata")]
    bagian = []
    for _, g in d.groupby("_berkas_raw", sort=False):
        if g["tingkat"].iloc[0] == "kabupaten":
            continue  # rekap provinsi sudah ada (K-006)
        if str(g["resource_nama"].iloc[0]).lower().endswith(".xlsx"):
            continue  # resource kembar, isi identik (K-014)
        kol = [c for c in g.columns if _norm(c) in BENCANA and g[c].notna().any()]
        if kol:
            dasar = g.drop(columns="nilai")
            g = dasar.melt(
                id_vars=[c for c in dasar.columns if c not in kol],
                value_vars=kol, var_name="_bencana", value_name="nilai")
            g["rincian"] = g.pop("_bencana").map(lambda x: BENCANA[_norm(x)])
        elif "JENIS BENCANA" in g.columns:
            g["rincian"] = g["JENIS BENCANA"].map(lambda x: BENCANA.get(_norm(x), "total"))
        else:
            g["rincian"] = "total"
        bagian.append(_json_satu(g, peta))
    if not bagian:
        return d.iloc[0:0]
    return pd.concat(bagian, ignore_index=True)


def _dari_wdi(d: pd.DataFrame) -> pd.DataFrame:
    """Pembanding nasional WDI: satu baris per tahun, Indonesia."""
    d = d[d["countryiso3code"].eq("IDN")].copy()
    d["seri_kode"] = "EN.CLC.MDAT.ZS"
    d["wilayah_kode"] = INDONESIA
    d["_nama"] = "INDONESIA"
    d["periode"] = d["date"].astype("Int64").astype("string")
    d["rincian"] = "total"
    d["nilai"] = _angka(d["value"])
    d["sumber"] = "wdi"
    d["_nasional"] = True
    return d


def _penduduk(d: pd.DataFrame) -> pd.DataFrame:
    """Seri jumlah_penduduk: satu berkas kanonik, satu baris per wilayah."""
    ada = d[d["Jumlah Penduduk"].notna()].sort_values("_berkas_raw")
    if ada.empty:
        return ada
    kanonik = ada["_berkas_raw"].iloc[0]
    p = ada[ada["_berkas_raw"] == kanonik].drop_duplicates(["wilayah_kode", "periode"])
    p = p.assign(seri_kode="jumlah_penduduk", rincian="total",
                 nilai=_angka(p["Jumlah Penduduk"]))
    return p


def jalankan(mentah):
    """Terima keluaran tahap 1, tulis dan kembalikan DataFrame Silver."""
    xlsx = mentah.get("bnpb_xlsx")
    js = mentah.get("bnpb_json")
    wdi = mentah.get("wdi_data")

    peta = {}
    for d in (xlsx, js):
        if d is not None:
            peta.update(_peta_wilayah(d))

    bagian = []
    if xlsx is not None:
        x = _dari_xlsx(xlsx, peta)
        bagian += [x, _penduduk(x)]
    if js is not None:
        bagian.append(_dari_json(js, peta))
    if wdi is not None:
        bagian.append(_dari_wdi(wdi))

    d = pd.concat(bagian, ignore_index=True)
    d["jenis_periode"] = "tahun"
    d["satuan"] = d["seri_kode"].map(_satuan)
    d["nama_wilayah"] = d["_nama"]

    belum = sorted(d.loc[d["wilayah_kode"].isna(), "_nama"].dropna().unique())
    if belum:
        raise ValueError(f"nama wilayah tidak terpetakan ke kode BPS: {belum}")
    d = d[d["seri_kode"].notna() & d["nilai"].notna()]
    # tidak ada agregasi periode: seluruh baris berasal dari tabel tahunan (K-016)
    if not d["periode"].str.fullmatch(r"\d{4}").all():
        raise ValueError("periode bukan tahunan; jangan rata-ratakan semester/bulan ke tahun")

    silver = d[KOLOM + ["_nasional"]].drop_duplicates()
    kunci = ["sumber", "seri_kode", "wilayah_kode", "periode", "rincian"]

    # baris nasional per jenis bencana muncul di berkas provinsi dan di tabel nasional;
    # tabel nasional yang dipakai. Nilainya identik, kecuali kejadian 2024 tanah longsor
    # yang baris provinsinya (27) bertentangan dengan jumlah provinsi (207) = tabel nasional (K-015)
    nas = silver["_nasional"].fillna(False).astype(bool)
    sasaran = silver["wilayah_kode"].eq(INDONESIA) & silver["rincian"].ne("total")
    ada_nas = {tuple(k) for k in silver.loc[sasaran & nas, kunci].itertuples(index=False, name=None)}
    buang = sasaran & ~nas & silver[kunci].apply(lambda r: tuple(r) in ada_nas, axis=1)
    silver = silver[~buang].drop(columns="_nasional")

    kembar = silver.duplicated(kunci, keep=False)
    if kembar.any():
        bentrok = silver[kembar].groupby(kunci).nilai.nunique()
        if (bentrok > 1).any():
            contoh = [list(k) for k in bentrok[bentrok > 1].index[:3]]
            raise ValueError(f"nilai berbeda untuk kunci Silver yang sama: {contoh}")
        silver = silver.sort_values(kunci + ["_berkas_raw"]).drop_duplicates(kunci, keep="first")

    silver = silver.astype({"wilayah_kode": "int64", "periode": "string"})
    SILVER.parent.mkdir(parents=True, exist_ok=True)
    silver.to_parquet(SILVER, index=False)
    print(f"Silver: {len(silver):,} baris, {silver['seri_kode'].nunique()} seri, "
          f"{silver['wilayah_kode'].nunique()} wilayah, {silver['_berkas_raw'].nunique()} berkas, "
          f"periode {silver['periode'].min()}-{silver['periode'].max()}")
    return silver
