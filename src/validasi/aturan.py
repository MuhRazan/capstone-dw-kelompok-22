"""Aturan validasi Silver kasus 22 (korban bencana).

Aturan dikelompokkan menjadi empat: skema dan kunci, nilai dan satuan, wilayah dan
periode, serta lineage dan rekonsiliasi agregat. Semua aturan deterministik dan tidak
mengubah Silver; hasil rekonsiliasi agregat ditulis sebagai tabel pendamping di
reports/ agar skema Silver 11 kolom tetap utuh.

Status:
- LOLOS                : aturan terpenuhi tanpa catatan.
- LOLOS_DENGAN_CATATAN : aturan terpenuhi, selisih/pengecualian yang diizinkan dicatat.
- GAGAL                : aturan dilanggar dan perlu diperbaiki.
"""
from dataclasses import dataclass, field
import re

import numpy as np
import pandas as pd

from src.common.manifest import baca
from src.common.skema import JENIS_PERIODE, KOLOM, KUNCI, periksa_silver
from src.ekstraksi import bnpb_xlsx
from src.silver import BENCANA, SATUAN, SERI

INDONESIA = 9999

# Susunan 38 provinsi tahun 2025: kode BPS dua digit x 100.
PROVINSI = {
    1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2100,
    3100, 3200, 3300, 3400, 3500, 3600,
    5100, 5200, 5300,
    6100, 6200, 6300, 6400, 6500,
    7100, 7200, 7300, 7400, 7500, 7600,
    8100, 8200,
    9100, 9200, 9300, 9400, 9500, 9600,
}

SATUAN_DIKENAL = {"jiwa", "kejadian", "per_100000_penduduk", "persen_penduduk"}

# Batas masuk akal per satuan. Batas ini bukan pembersihan nilai, hanya penjaga salah baca.
RENTANG = {
    "jiwa": (0, 300_000_000),          # penduduk Indonesia 2025 < 300 juta
    "kejadian": (0, 10_000),           # kejadian per provinsi per tahun
    "per_100000_penduduk": (0, 100_000),
    "persen_penduduk": (0, 100),
}

RINCIAN = set(BENCANA.values()) | {"total"}

SERI_DIKENAL = set(SERI.values()) | {"jumlah_penduduk", "EN.CLC.MDAT.ZS"}

# Ejaan nama wilayah yang sah untuk kode yang punya lebih dari satu ejaan di sumber.
ALIAS_NAMA = {
    3400: {"DI YOGYAKARTA", "DAERAH ISTIMEWA YOGYAKARTA", "YOGYAKARTA"},
    9100: {"PAPUA", "P A P U A"},
    9999: {"INDONESIA"},
}

TAHUN_MIN, TAHUN_MAX = 2009, 2026


@dataclass
class Temuan:
    """Satu aturan validasi beserta hasilnya."""

    id: str
    nama: str
    status: str
    baris: int
    ringkas: str
    detail: list[str] = field(default_factory=list)


def _norm(nama) -> str | None:
    if pd.isna(nama):
        return None
    return re.sub(r"\s+", " ", str(nama).strip().upper())


def _hasil(id_, nama, baris, ringkas, detail=None, catatan=False, gagal=None) -> Temuan:
    if gagal is None:
        gagal = baris > 0
    status = "GAGAL" if gagal else ("LOLOS_DENGAN_CATATAN" if catatan else "LOLOS")
    return Temuan(id_, nama, status, int(baris), ringkas, list(detail or []))


def periksa_skema(df: pd.DataFrame) -> Temuan:
    kurang = [k for k in KOLOM if k not in df.columns]
    if kurang:
        return _hasil("R01", "Skema kolom Silver", len(kurang),
                      f"kolom wajib tidak ada: {kurang}")

    kosong = {k: int(df[k].isna().sum()) for k in KOLOM if df[k].isna().any()}
    salah = periksa_silver(df)  # lantai skema starter, sebagai jaring pengaman
    baris = sum(kosong.values()) + len(salah)
    if baris:
        detail = [f"{k}: {v} sel kosong" for k, v in kosong.items()]
        detail += salah[:5]
        return _hasil("R01", "Skema kolom Silver", baris,
                      f"{len(KOLOM)} kolom wajib diperiksa; {len(salah)} temuan starter",
                      detail)
    return _hasil("R01", "Skema kolom Silver", 0,
                  f"{len(KOLOM)} kolom wajib lengkap, tanpa sel kosong")


def periksa_kunci(df: pd.DataFrame) -> Temuan:
    kembar = df.duplicated(KUNCI, keep=False)
    jumlah = int(kembar.sum())
    if jumlah:
        contoh = df.loc[kembar, KUNCI].head(3).to_dict("records")
        return _hasil("R02", "Keunikan kunci Silver", jumlah,
                      f"{jumlah} baris memakai kunci yang sama", [str(c) for c in contoh])
    return _hasil("R02", "Keunikan kunci Silver", 0,
                  f"{len(KUNCI)} kolom kunci unik untuk {len(df):,} baris")


def periksa_nilai(df: pd.DataFrame) -> Temuan:
    x = pd.to_numeric(df["nilai"], errors="coerce")
    salah = (~np.isfinite(x)) | (x < 0)
    jumlah = int(salah.sum())
    if jumlah:
        contoh = df.loc[salah, ["seri_kode", "wilayah_kode", "periode", "nilai"]].head(5)
        return _hasil("R03", "Nilai tidak negatif dan berhingga", jumlah,
                      f"{jumlah} nilai negatif/NaN/inf", contoh.to_string(index=False).splitlines())
    return _hasil("R03", "Nilai tidak negatif dan berhingga", 0,
                  f"nilai minimum {x.min():,.2f}; tidak ada nilai negatif atau tak berhingga")


def periksa_bulat(df: pd.DataFrame) -> Temuan:
    lingkup = df[df["satuan"].isin(["jiwa", "kejadian"])]
    x = pd.to_numeric(lingkup["nilai"], errors="coerce").astype(float)
    dekat = np.isclose(x, np.round(x), rtol=0, atol=1e-6)
    noise = ((x % 1) != 0) & dekat
    salah = ~dekat & np.isfinite(x)
    jumlah = int(salah.sum())
    ringkas = (f"{len(lingkup):,} baris jiwa/kejadian; {int(noise.sum())} baris ber-noise "
               "float < 1e-6 (bukan pelanggaran)")
    if jumlah:
        contoh = lingkup.loc[salah, ["seri_kode", "wilayah_kode", "periode", "nilai"]].head(5)
        return _hasil("R04", "Bilangan bulat untuk jiwa/kejadian", jumlah,
                      f"{jumlah} nilai tidak bulat", contoh.to_string(index=False).splitlines())
    return _hasil("R04", "Bilangan bulat untuk jiwa/kejadian", 0, ringkas,
                  catatan=bool(noise.any()))


def periksa_satuan(df: pd.DataFrame) -> Temuan:
    seri_aneh = df.loc[~df["seri_kode"].isin(SERI_DIKENAL), "seri_kode"].unique()
    satuan_aneh = df.loc[~df["satuan"].isin(SATUAN_DIKENAL), "satuan"].unique()
    salah = pd.Series(False, index=df.index)
    detail = []
    for seri, bagian in df.groupby("seri_kode", sort=True):
        harap = SATUAN.get(seri, "jiwa")
        beda = bagian["satuan"].ne(harap)
        if beda.any():
            salah |= beda.reindex(salah.index, fill_value=False)
            detail.append(f"{seri}: satuan {sorted(bagian['satuan'].unique())}, seharusnya {harap}")
    if len(seri_aneh):
        detail.append(f"seri tidak dikenal: {sorted(seri_aneh)}")
    if len(satuan_aneh):
        detail.append(f"satuan tidak dikenal: {sorted(satuan_aneh)}")
    jumlah = int(salah.sum()) + int((~df["seri_kode"].isin(SERI_DIKENAL)).sum()) \
        + int((~df["satuan"].isin(SATUAN_DIKENAL)).sum())
    ringkas = (f"{df['seri_kode'].nunique()} seri memakai satu satuan sesuai peta SATUAN; "
               f"satuan: {', '.join(sorted(df['satuan'].unique()))}")
    return _hasil("R05", "Konsistensi satuan per seri", jumlah, ringkas, detail)


def periksa_rentang(df: pd.DataFrame) -> Temuan:
    salah = pd.Series(False, index=df.index)
    detail = []
    ringkas = []
    for satuan, (bawah, atas) in RENTANG.items():
        bagian = df[df["satuan"] == satuan]
        if bagian.empty:
            continue
        x = pd.to_numeric(bagian["nilai"], errors="coerce")
        luar = (x < bawah) | (x > atas)
        salah |= luar.reindex(salah.index, fill_value=False)
        ringkas.append(f"{satuan} {x.min():,.2f}-{x.max():,.2f} (batas {bawah:,}-{atas:,})")
        if luar.any():
            detail.append(f"{satuan}: {int(luar.sum())} baris di luar {bawah}-{atas}")
    jumlah = int(salah.sum())
    teks = "; ".join(ringkas)
    if jumlah:
        return _hasil("R06", "Rentang nilai masuk akal per satuan", jumlah,
                      f"{jumlah} baris di luar batas", detail + [teks])
    return _hasil("R06", "Rentang nilai masuk akal per satuan", 0, teks)


def periksa_wilayah(df: pd.DataFrame) -> Temuan:
    kode = pd.to_numeric(df["wilayah_kode"], errors="coerce")
    salah = kode.isna() | (~kode.isin(PROVINSI | {INDONESIA}))
    jumlah = int(salah.sum())
    if jumlah:
        contoh = sorted(kode[salah].dropna().unique().tolist())
        return _hasil("R07", "Kode wilayah sah", jumlah,
                      f"{jumlah} baris memakai kode di luar 38 provinsi/9999", [str(contoh[:20])])
    return _hasil("R07", "Kode wilayah sah", 0,
                  f"{df['wilayah_kode'].nunique()} kode: 38 provinsi BPS x 100 + 9999 Indonesia")


def periksa_nama_wilayah(df: pd.DataFrame) -> Temuan:
    salah = 0
    detail = []
    for kode, bagian in df.groupby("wilayah_kode", sort=True):
        nama = sorted({n for n in bagian["nama_wilayah"].map(_norm).unique() if n})
        izin = ALIAS_NAMA.get(int(kode))
        if izin is not None:
            asing = set(nama) - izin
            if asing:
                salah += int(df["wilayah_kode"].eq(kode).sum())
                detail.append(f"{kode}: nama tidak sah {sorted(asing)}")
        elif len(nama) > 1:
            salah += int(df["wilayah_kode"].eq(kode).sum())
            detail.append(f"{kode}: {len(nama)} ejaan tanpa alias resmi {nama}")
        if len(nama) > 1 and izin is not None:
            detail.append(f"{kode}: alias resmi {nama}")
    if salah:
        return _hasil("R08", "Konsistensi nama wilayah", salah,
                      f"{salah} baris memakai nama wilayah yang tidak konsisten", detail)
    catatan = [d for d in detail if "alias resmi" in d]
    return _hasil("R08", "Konsistensi nama wilayah", 0,
                  f"{df['nama_wilayah'].nunique()} ejaan untuk {df['wilayah_kode'].nunique()} kode; "
                  "ejaan ganda hanya pada alias resmi", catatan, catatan=bool(catatan))


def periksa_periode(df: pd.DataFrame) -> Temuan:
    periode = df["periode"].astype(str)
    tahun = pd.to_numeric(periode, errors="coerce")
    salah = (
        ~periode.str.fullmatch(JENIS_PERIODE["tahun"])
        | df["jenis_periode"].ne("tahun")
        | tahun.isna()
        | (tahun < TAHUN_MIN)
        | (tahun > TAHUN_MAX)
    )
    jumlah = int(salah.sum())
    if jumlah:
        contoh = df.loc[salah, ["seri_kode", "wilayah_kode", "periode", "jenis_periode"]].head(5)
        return _hasil("R09", "Periode dan jenis periode", jumlah,
                      f"{jumlah} baris tidak sesuai format tahun {TAHUN_MIN}-{TAHUN_MAX}",
                      contoh.to_string(index=False).splitlines())
    return _hasil("R09", "Periode dan jenis periode", 0,
                  f"semua {len(df):,} baris bertipe tahun, {int(tahun.min())}-{int(tahun.max())}")


def periksa_rincian(df: pd.DataFrame) -> Temuan:
    salah = ~df["rincian"].isin(RINCIAN)
    jumlah = int(salah.sum())
    if jumlah:
        contoh = sorted(df.loc[salah, "rincian"].astype(str).unique().tolist())
        return _hasil("R10", "Rincian jenis bencana dikenal", jumlah,
                      f"{jumlah} baris memakai rincian di luar peta BENCANA", [str(contoh[:20])])
    return _hasil("R10", "Rincian jenis bencana dikenal", 0,
                  f"{df['rincian'].nunique()} nilai: total + 9 jenis bencana")


def periksa_lineage(df: pd.DataFrame) -> Temuan:
    try:
        manifest = baca()
    except FileNotFoundError:
        return _hasil("R11", "Lineage berkas mentah", len(df),
                      "data/raw/MANIFEST.csv tidak ditemukan; lineage tidak dapat diperiksa")

    pasangan = df[["_berkas_raw", "_sha256_raw"]].drop_duplicates()
    format_salah = ~pasangan["_sha256_raw"].astype(str).str.fullmatch(r"[0-9a-f]{64}")
    tidak_ada = ~pasangan["_berkas_raw"].isin(manifest)
    beda = pasangan.apply(
        lambda r: r["_berkas_raw"] in manifest
        and manifest[r["_berkas_raw"]] != r["_sha256_raw"], axis=1)
    ganda = df.groupby("_berkas_raw")["_sha256_raw"].nunique()
    ganda = ganda[ganda > 1]

    buruk = pasangan[format_salah | tidak_ada | beda]
    jumlah = int(len(df.merge(buruk, on=["_berkas_raw", "_sha256_raw"], how="inner")))
    detail = []
    if format_salah.any():
        detail.append(f"{int(format_salah.sum())} sha256 bukan 64 hex")
    if tidak_ada.any():
        detail.append(f"berkas tidak ada di MANIFEST: {sorted(pasangan.loc[tidak_ada, '_berkas_raw'])[:3]}")
    if beda.any():
        detail.append(f"{int(beda.sum())} sha256 tidak cocok dengan MANIFEST")
    if len(ganda):
        detail.append(f"{len(ganda)} berkas punya lebih dari satu sha256")
    if jumlah or len(ganda):
        return _hasil("R11", "Lineage berkas mentah", jumlah + int(ganda.sum()),
                      "lineage tidak cocok dengan MANIFEST.csv", detail)
    return _hasil("R11", "Lineage berkas mentah", 0,
                  f"{len(pasangan)} berkas sumber cocok dengan MANIFEST.csv")


def periksa_cakupan(df: pd.DataFrame) -> Temuan:
    provinsi = df[df["wilayah_kode"] != INDONESIA]
    cakupan = provinsi.groupby(["seri_kode", "periode", "rincian"])["wilayah_kode"].nunique()
    parsial = cakupan[cakupan < 38]
    detail = []
    for (seri, periode, rincian), n in parsial.head(15).items():
        detail.append(f"{seri} {periode} {rincian}: {n} provinsi")
    if len(parsial) > 15:
        detail.append(f"... dan {len(parsial) - 15} grup parsial lain")
    ringkas = (f"{int((cakupan == 38).sum())} grup lengkap 38 provinsi; "
               f"{len(parsial)} grup parsial dicatat (hanya provinsi yang punya kejadian)")
    baris = int(provinsi.merge(
        parsial.rename("n").reset_index(), on=["seri_kode", "periode", "rincian"],
        how="inner").shape[0])
    return _hasil("R12", "Kelengkapan wilayah per seri/periode", baris, ringkas,
                  detail, catatan=bool(len(parsial)), gagal=False)


def periksa_agregat_kabupaten(df: pd.DataFrame) -> tuple[Temuan, pd.DataFrame]:
    """Bandingkan jumlah kab/kota 2021-2022 dengan rekap provinsi di Silver.

    Jumlah kab/kota yang dijumlahkan disimpan di tabel pendamping, bukan kolom baru,
    agar skema Silver 11 kolom tidak berubah.
    """
    kosong = pd.DataFrame(columns=[
        "periode", "wilayah_kode", "nama_wilayah", "seri_kode", "rincian",
        "n_kabupaten_kota", "n_baris_kabupaten_kota", "nilai_kabupaten_kota",
        "nilai_provinsi_silver", "selisih", "jenis_baris"])
    try:
        mentah = bnpb_xlsx.baca_semua()
    except Exception as e:  # data/raw belum ada saat validasi dijalankan
        return _hasil("R13", "Agregat kabupaten/kota ke provinsi", len(df),
                      f"data mentah tidak dapat dibaca: {e}"), kosong

    d = mentah[mentah["tahun"].isin([2021, 2022])].copy()
    d["nilai"] = pd.to_numeric(d["nilai"], errors="coerce")
    d["_prov"] = d["Provinsi"].map(_norm)
    d["_dis"] = d["Jenis Bencana"].map(_norm)
    kab = d[d["_berkas_raw"].str.contains("kabupaten|kabupten", case=False, regex=True)].copy()
    kab["seri_kode"] = kab["indikator"].map(SERI)
    kab["rincian"] = kab["_dis"].map(lambda x: BENCANA.get(x, "total"))
    kab = kab[kab["seri_kode"].notna() & kab["nilai"].notna()]

    s = df[(df["wilayah_kode"] != INDONESIA) & df["periode"].astype(str).isin(["2021", "2022"])].copy()
    s["periode"] = s["periode"].astype(str)
    peta_nama = {_norm(n): int(k) for k, n in
                 s[["wilayah_kode", "nama_wilayah"]].drop_duplicates().itertuples(index=False)}
    kab["wilayah_kode"] = kab["_prov"].map(peta_nama)

    g = kab.groupby(["tahun", "wilayah_kode", "seri_kode", "rincian"], as_index=False).agg(
        n_kabupaten_kota=("Kabupaten/Kota", "nunique"),
        n_baris_kabupaten_kota=("nilai", "size"),
        nilai_kabupaten_kota=("nilai", "sum"))
    g["periode"] = g.pop("tahun").astype(str)

    scope = s[["periode", "wilayah_kode", "nama_wilayah", "seri_kode", "rincian", "nilai"]].rename(
        columns={"nilai": "nilai_provinsi_silver"})
    j = g.merge(scope, on=["periode", "wilayah_kode", "seri_kode", "rincian"],
                how="outer", indicator=True)
    j["selisih"] = j["nilai_kabupaten_kota"] - j["nilai_provinsi_silver"]
    j["jenis_baris"] = np.select(
        [j["_merge"].eq("both"),
         j["_merge"].eq("right_only") & j["rincian"].eq("total")],
        ["agregasi_kabupaten_kota", "rekap_provinsi_tanpa_rincian_kabupaten_kota"],
        default="kabupaten_kota_tanpa_baris_silver")
    peta_kode = {int(k): n for k, n in s[["wilayah_kode", "nama_wilayah"]].drop_duplicates()
                 .sort_values("wilayah_kode").itertuples(index=False)}
    j["nama_wilayah"] = j["nama_wilayah"].fillna(j["wilayah_kode"].map(peta_kode))
    j = j.sort_values(["periode", "wilayah_kode", "seri_kode", "rincian"]).reset_index(drop=True)

    kolom = ["periode", "wilayah_kode", "nama_wilayah", "seri_kode", "rincian",
             "n_kabupaten_kota", "n_baris_kabupaten_kota", "nilai_kabupaten_kota",
             "nilai_provinsi_silver", "selisih", "jenis_baris"]
    luar = j[kolom].copy()
    for k in ["n_kabupaten_kota", "n_baris_kabupaten_kota"]:
        luar[k] = luar[k].astype("Int64")

    agregasi = j[j["jenis_baris"] == "agregasi_kabupaten_kota"]
    tanpa_silver = j[j["jenis_baris"] == "kabupaten_kota_tanpa_baris_silver"]
    total_prov = j[j["jenis_baris"] == "rekap_provinsi_tanpa_rincian_kabupaten_kota"]
    selisih = agregasi[agregasi["selisih"].abs() > 1e-6]
    baris = int(len(tanpa_silver) + len(selisih))
    ringkas = (f"{len(agregasi):,} baris agregasi kab/kota; {len(selisih)} selisih dicatat; "
               f"{len(total_prov)} baris total provinsi tanpa rincian kab/kota")
    detail = []
    if len(tanpa_silver):
        detail.append(f"{len(tanpa_silver)} kelompok kab/kota tidak punya baris Silver")
    for r in selisih.head(10).itertuples(index=False):
        detail.append(f"{r.periode} {r.nama_wilayah} {r.seri_kode}/{r.rincian}: "
                      f"kab/kota {r.nilai_kabupaten_kota:,.0f} vs provinsi "
                      f"{r.nilai_provinsi_silver:,.0f} (selisih {r.selisih:+,.0f})")
    if len(total_prov):
        detail.append(f"{len(total_prov)} baris total provinsi berasal dari rekap provinsi, "
                      "bukan agregasi kab/kota")
    return _hasil("R13", "Agregat kabupaten/kota ke provinsi", baris, ringkas,
                  detail, catatan=bool(len(selisih) or len(total_prov)),
                  gagal=bool(len(tanpa_silver))), luar


def periksa_agregat_nasional(df: pd.DataFrame) -> tuple[Temuan, pd.DataFrame]:
    """Rekonsiliasi provinsi vs nasional untuk satuan aditif saja (jiwa/kejadian)."""
    kolom = ["seri_kode", "periode", "rincian", "satuan", "n_provinsi",
             "nilai_provinsi", "nilai_nasional", "selisih", "keterangan"]
    aditif = df[df["satuan"].isin(["jiwa", "kejadian"])]
    rasio = df[df["satuan"].isin(["per_100000_penduduk", "persen_penduduk"])]
    if aditif.empty:
        return _hasil("R14", "Agregat provinsi ke nasional", 0,
                      "tidak ada baris aditif"), pd.DataFrame(columns=kolom)

    prov = aditif[aditif["wilayah_kode"] != INDONESIA].groupby(
        ["seri_kode", "periode", "rincian"], as_index=False).agg(
        n_provinsi=("wilayah_kode", "nunique"), nilai_provinsi=("nilai", "sum"))
    nas = aditif[aditif["wilayah_kode"] == INDONESIA].groupby(
        ["seri_kode", "periode", "rincian"], as_index=False).agg(
        nilai_nasional=("nilai", "sum"))
    j = prov.merge(nas, on=["seri_kode", "periode", "rincian"], how="outer", indicator=True)
    j = j.merge(df[["seri_kode", "satuan"]].drop_duplicates("seri_kode"),
                on="seri_kode", how="left")
    j["selisih"] = j["nilai_provinsi"] - j["nilai_nasional"]
    j["keterangan"] = np.select(
        [j["_merge"].eq("both") & (j["selisih"].abs() <= 1e-6),
         j["_merge"].eq("both"),
         j["_merge"].eq("left_only")],
        ["cocok", "selisih dicatat", "tidak ada baris nasional"],
        default="tidak ada baris provinsi")
    j = j.sort_values(["seri_kode", "periode", "rincian"]).reset_index(drop=True)

    selisih = j[j["_merge"].eq("both") & (j["selisih"].abs() > 1e-6)]
    ringkas = (f"{int(j['_merge'].eq('both').sum())} pasangan aditif dibandingkan; "
               f"{len(selisih)} selisih dicatat; "
               f"{rasio['seri_kode'].nunique()} seri rasio/persen tidak dijumlahkan")
    detail = []
    for r in selisih.head(10).itertuples(index=False):
        detail.append(f"{r.seri_kode} {r.periode} {r.rincian}: provinsi "
                      f"{r.nilai_provinsi:,.2f} vs nasional {r.nilai_nasional:,.2f} "
                      f"(selisih {r.selisih:+,.2f})")
    if len(rasio):
        detail.append(f"{len(rasio):,} baris bersatuan per 100rb/persen dikecualikan karena "
                      "tidak aditif antarwilayah")
    return _hasil("R14", "Agregat provinsi ke nasional", len(selisih), ringkas,
                  detail, catatan=bool(len(selisih)), gagal=False), j[kolom]


def periksa_semua(df: pd.DataFrame) -> tuple[list[Temuan], dict[str, pd.DataFrame]]:
    """Jalankan seluruh aturan; kembalikan temuan dan tabel pendamping."""
    temuan = [
        periksa_skema(df),
        periksa_kunci(df),
        periksa_nilai(df),
        periksa_bulat(df),
        periksa_satuan(df),
        periksa_rentang(df),
        periksa_wilayah(df),
        periksa_nama_wilayah(df),
        periksa_periode(df),
        periksa_rincian(df),
        periksa_lineage(df),
        periksa_cakupan(df),
    ]
    r13, tabel_kab = periksa_agregat_kabupaten(df)
    r14, tabel_nas = periksa_agregat_nasional(df)
    temuan += [r13, r14]
    artefak = {
        "validasi-agregasi-kabupaten.csv": tabel_kab,
        "validasi-agregat-nasional.csv": tabel_nas,
    }
    return temuan, artefak
