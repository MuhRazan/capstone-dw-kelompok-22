from pathlib import Path
import re
import pandas as pd
from src.common.manifest import sha256_raw

RAW = Path("data/raw")
TANGAN = RAW / "bnpb/2026-10-20/tangan"
ID_2025 = ["No.", "Kode Wilayah Provinsi", "Provinsi", "Latitude", "Longitude", "Jumlah Penduduk"]
ID_REKAP = ["Provinsi", "Kabupaten/Kota", "Jenis Bencana"]


def _tahun(nama: str) -> int:
    return int(re.findall(r"(?<!\d)(20\d{2})(?!\d)", nama)[-1])


def _baca_rekap(path):
    """Rekap 2021/2022 (provinsi dan kab/kota). Header dua baris dicari dari sel 'Provinsi'."""
    m = pd.read_excel(path, header=None, dtype=object)
    r = m.index[m[0].astype(str).str.strip() == "Provinsi"][0]
    atas = m.iloc[r].ffill()                 # nama grup (Korban/Kerusakan) dibawa ke kanan
    bawah = m.iloc[r + 1]
    nama = [str(a).strip() if pd.isna(b) else f"{str(a).strip()} {str(b).strip()}"
            for a, b in zip(atas, bawah)]
    satuan_baris = m.iloc[r + 2].ffill()     # (jiwa) / (unit), dibawa ke kanan per grup
    satuan = {n: s for n, s in zip(nama, satuan_baris) if pd.notna(s)}
    d = m.iloc[r + 3:].copy()
    d.columns = nama
    idv = [c for c in ID_REKAP if c in d.columns]
    wil = [c for c in idv if c != "Jenis Bencana"]
    d[wil] = d[wil].ffill()                  # sel gabungan wilayah
    d = d.dropna(subset=["Jenis Bencana"])
    n_mentah = len(d)
    d = d.melt(id_vars=idv, var_name="indikator", value_name="nilai")
    d["satuan"] = d["indikator"].map(satuan)
    d["format_asal"] = "rekap"
    return d, n_mentah


def _baca_indikator_2025(path, x):
    sheet = x.sheet_names[1]
    d = pd.read_excel(path, sheet_name=sheet, header=1, dtype=object)
    d.columns = [str(c).strip() for c in d.columns]
    d = d.dropna(how="all")
    n_mentah = len(d)
    idv = [c for c in d.columns if c in ID_2025]
    val = [c for c in d.columns if c not in ID_2025]
    d = d.melt(id_vars=idv, value_vars=val, var_name="jenis_bencana", value_name="nilai")
    d["indikator"] = sheet
    d["format_asal"] = "indikator_2025"
    return d, n_mentah


def _baca_rekapitulasi_2025(path, x):
    sheet = x.sheet_names[1]
    d = pd.read_excel(path, sheet_name=sheet, header=1, dtype=object)
    d.columns = [str(c).strip() for c in d.columns]
    d = d.dropna(how="all")
    n_mentah = len(d)
    idv = ["Kode Bencana", "Jenis Bencana"]
    d = d.melt(id_vars=idv, var_name="indikator", value_name="nilai")
    d["format_asal"] = "rekapitulasi_2025"
    return d, n_mentah


def baca_semua():
    bagian, ringkas = [], []
    for path in sorted(TANGAN.rglob("*.xlsx")):
        rel = path.relative_to(RAW).as_posix()
        x = pd.ExcelFile(path)
        if "Keterangan" not in x.sheet_names:
            d, n = _baca_rekap(path)
        elif x.sheet_names[1].startswith("Rekapitulasi"):
            d, n = _baca_rekapitulasi_2025(path, x)
        else:
            d, n = _baca_indikator_2025(path, x)
        d["tahun"] = _tahun(path.name)
        d["_berkas_raw"] = rel
        d["_sha256_raw"] = sha256_raw(rel)
        bagian.append(d)
        ringkas.append((path.name[-60:], n, len(d)))
    baca_semua.ringkasan = ringkas
    return pd.concat(bagian, ignore_index=True)