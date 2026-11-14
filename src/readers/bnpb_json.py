"""Tahap 1 - pembaca JSON datastore BNPB dan metadata ckan/.

Pembaca ini TIDAK membersihkan apa pun. Nilai dibawa apa adanya (tanpa
konversi tipe, tanpa trim, tanpa imputasi). Transformasi yang ada hanya:
  1. kolom tahun lebar (mis. "2010.0") dilebur ke bentuk panjang;
  2. penambahan kolom konteks (seri, resource, paket, tingkat) dari metadata CKAN;
  3. penambahan _berkas_raw dan _sha256_raw dari src.common.manifest.

BENTUK BERKAS (diamati dari data kasus 22):
  datastore/<slug-paket>/<uuid-resource>.json =
      {"resource_id": "...", "halaman": [ {"success": true, "result": {"records": [...], "total": N}}, ... ]}
  ckan/package_search-*.json = respons package_search (result.results[].resources[]).
  Seri TIDAK bisa dibaca dari nama berkas (namanya UUID); ditentukan dari nama
  resource di metadata CKAN lewat resource_id (lihat seri_dari_nama_resource).

ATURAN KOLOM TAHUN:
  Nama kolom (setelah strip) cocok ^(\\d{4})(\\.0+)?$ -> tahun = int(grup 1).
  "2010", "2010.0", "2010.00" -> 2010. Bentuk lain ("2010.5", "20100", "2010a")
  BUKAN kolom tahun dan diperlakukan sebagai dimensi.
  Berkas tanpa kolom tahun: baris diteruskan apa adanya; kolom_asal/tahun/nilai = NA.

SKEMA KELUARAN DATASTORE (satu baris = satu sel tahun dari baris asal):
  seri, resource_id, resource_nama, paket, tingkat, _id_asal, <dimensi...>,
  kolom_asal, tahun (Int64), nilai (mentah), _berkas_raw, _sha256_raw
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd

from src.common import manifest

SERI = [
    "kejadian", "korban_meninggal", "korban_hilang", "korban_luka_sakit",
    "korban_mengungsi", "korban_terdampak", "korban_terdampak_mengungsi",
    "korban_mengungsi_per_100rb", "korban_meninggal_hilang_per_100rb",
    "jumlah_penduduk",
]
_POLA_TAHUN = re.compile(r"^(\d{4})(\.0+)?$")
_KOLOM_KONTEKS = ["seri", "resource_id", "resource_nama", "paket", "tingkat"]


# ---------------------------------------------------------------- pemetaan seri
def seri_dari_nama_resource(nama: str) -> str | None:
    """Nama resource CKAN -> seri. None bila tidak termasuk 10 seri
    (mis. 'Rumah Rusak', 'Nilai Kerusakan'): pemanggil memutuskan, bukan ditebak."""
    n = (nama or "").lower()
    if "per 100.000" in n:
        if "meninggal" in n and "hilang" in n:
            return "korban_meninggal_hilang_per_100rb"
        if "mengungsi" in n:
            return "korban_mengungsi_per_100rb"
        return None
    if "terdampak" in n and "mengungsi" in n:
        return "korban_terdampak_mengungsi"
    if "rusak" in n or "kerusakan" in n or "luas " in n:
        return None
    for kunci, seri in [
        ("meninggal", "korban_meninggal"),
        ("hilang", "korban_hilang"),
        ("luka", "korban_luka_sakit"),
        ("terdampak", "korban_terdampak"),
        ("mengungsi", "korban_mengungsi"),
        ("penduduk", "jumlah_penduduk"),
        ("kejadian", "kejadian"),
    ]:
        if kunci in n:
            return seri
    return None


def tingkat_dari_nama_resource(nama: str) -> str | None:
    n = (nama or "").lower()
    if "jenis bencana" in n:
        return "jenis_bencana"
    if "kabupaten" in n or "kabupten" in n:  # 'kabupten' = salah ketik di sumber
        return "kabupaten"
    if "provinsi" in n:
        return "provinsi"
    return None


def tahun_dari_kolom(nama) -> int | None:
    m = _POLA_TAHUN.match(str(nama).strip())
    return int(m.group(1)) if m else None


# ---------------------------------------------------------------- util
def _kunci_manifest(path: Path) -> str:
    """Jalur relatif terhadap data/raw dengan '/', seperti di MANIFEST.csv."""
    return Path(path).resolve().relative_to(Path(manifest.RAW).resolve()).as_posix()


def _jejak(path: Path) -> tuple[str, str]:
    kunci = _kunci_manifest(path)
    return kunci, manifest.sha256_raw(kunci)


def _muat_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _ratakan(d: dict, awalan: str = "") -> dict:
    out = {}
    for k, v in d.items():
        kunci = f"{awalan}{k}"
        if isinstance(v, dict):
            out.update(_ratakan(v, kunci + "."))
        elif isinstance(v, list):
            out[kunci] = json.dumps(v, ensure_ascii=False)
        else:
            out[kunci] = v
    return out


# ---------------------------------------------------------------- CKAN
def baca_ckan(path: str | Path) -> pd.DataFrame:
    """package_search -> satu baris per resource (kolom 'paket.*' dan 'resource.*').
    Paket tanpa resource tetap menjadi satu baris. Tidak ada pembersihan."""
    path = Path(path)
    obj = _muat_json(path)
    hasil = obj.get("result", obj) if isinstance(obj, dict) else None
    if not isinstance(hasil, dict):
        raise ValueError(f"{path.name}: bentuk metadata CKAN tidak dikenali.")
    if isinstance(hasil.get("results"), list):
        paket_list = hasil["results"]
    elif isinstance(hasil.get("resources"), list):
        paket_list = [hasil]
    else:
        raise ValueError(f"{path.name}: tidak ada result.results maupun resources.")

    baris = []
    for p in paket_list:
        paket = {k: v for k, v in p.items() if k != "resources"}
        resources = p.get("resources") or []
        if not resources:
            baris.append(_ratakan(paket, "paket."))
        for r in resources:
            b = _ratakan(paket, "paket.")
            b.update(_ratakan(r, "resource."))
            baris.append(b)
    df = pd.DataFrame(baris).astype(object)
    df.insert(0, "seri", "ckan_metadata")
    berkas, sha = _jejak(path)
    df["_berkas_raw"] = berkas
    df["_sha256_raw"] = sha
    return df


def peta_resource(df_ckan: pd.DataFrame) -> dict[str, dict]:
    """resource_id -> {nama, paket}. Resource kembar: yang pertama dipakai."""
    peta = {}
    for rid, nama, paket in zip(
        df_ckan.get("resource.id", []), df_ckan.get("resource.name", []),
        df_ckan.get("paket.name", []),
    ):
        if isinstance(rid, str) and rid not in peta:
            peta[rid] = {"nama": nama, "paket": paket}
    return peta


# ---------------------------------------------------------------- datastore
def _records_datastore(obj, path: Path) -> list[dict]:
    """Gabungkan records seluruh 'halaman'. Cek jumlah terhadap 'total' bila ada."""
    if not (isinstance(obj, dict) and isinstance(obj.get("halaman"), list)):
        raise ValueError(f"{path.name}: tidak ada kunci 'halaman' (bentuk tak dikenali).")
    records, total = [], None
    for i, h in enumerate(obj["halaman"]):
        if not h.get("success", False):
            raise ValueError(f"{path.name}: halaman {i} success=false.")
        res = h["result"]
        records.extend(res["records"])
        if res.get("total") is not None:
            total = res["total"]
    if total is not None and total != len(records):
        raise ValueError(f"{path.name}: records={len(records)} != total={total} (halaman hilang?).")
    return records


def baca_datastore(path: str | Path, peta: dict[str, dict]) -> pd.DataFrame:
    path = Path(path)
    obj = _muat_json(path)
    rid = obj.get("resource_id") or path.stem
    info = peta.get(rid)
    if info is None:
        raise ValueError(f"{path.name}: resource_id {rid} tidak ada di metadata ckan/.")
    seri = seri_dari_nama_resource(info["nama"])
    if seri is None:
        raise ValueError(f"{path.name}: resource '{info['nama']}' tidak termasuk 10 seri.")

    records = _records_datastore(obj, path)
    lebar = pd.DataFrame.from_records(records).astype(object)
    kol_tahun = {c: tahun_dari_kolom(c) for c in lebar.columns}
    kol_tahun = {c: t for c, t in kol_tahun.items() if t is not None}
    dimensi = [c for c in lebar.columns if c not in kol_tahun and c != "_id"]
    bentrok = set(dimensi) & (set(_KOLOM_KONTEKS) | {"kolom_asal", "tahun", "nilai", "_id_asal"})
    if bentrok:
        raise ValueError(f"{path.name}: kolom dimensi bentrok dengan kolom keluaran: {sorted(bentrok)}")

    lebar = lebar.copy()
    lebar["_id_asal"] = lebar["_id"] if "_id" in lebar.columns else lebar.index
    idv = ["_id_asal"] + dimensi
    if kol_tahun:
        lebar["_r"] = range(len(lebar))  # menjaga urutan baris asal
        panjang = lebar.melt(id_vars=idv + ["_r"], value_vars=list(kol_tahun),
                             var_name="kolom_asal", value_name="nilai")
        panjang = panjang.sort_values("_r", kind="stable").drop(columns="_r").reset_index(drop=True)
        panjang["tahun"] = panjang["kolom_asal"].map(kol_tahun).astype("Int64")
        panjang = panjang[idv + ["kolom_asal", "tahun", "nilai"]]
    else:
        panjang = lebar[idv].copy()
        panjang["kolom_asal"] = pd.NA
        panjang["tahun"] = pd.array([pd.NA] * len(panjang), dtype="Int64")
        panjang["nilai"] = pd.NA

    konteks = {"seri": seri, "resource_id": rid, "resource_nama": info["nama"],
               "paket": info["paket"], "tingkat": tingkat_dari_nama_resource(info["nama"])}
    for i, (k, v) in enumerate(konteks.items()):
        panjang.insert(i, k, v)
    berkas, sha = _jejak(path)
    panjang["_berkas_raw"] = berkas
    panjang["_sha256_raw"] = sha
    return panjang


def baca_semua(akar: str | Path):
    """akar = folder bertanggal, mis. data/raw/bnpb/2026-10-20 (berisi ckan/ dan datastore/).
    Kembalikan ({jalur: DataFrame}, [(jalur, galat)])."""
    akar = Path(akar)
    hasil, galat = {}, []
    peta = {}
    for p in sorted((akar / "ckan").rglob("*.json")):
        try:
            df = baca_ckan(p)
            hasil[str(p)] = df
            peta.update({k: v for k, v in peta_resource(df).items() if k not in peta})
        except Exception as e:
            galat.append((str(p), repr(e)))
    for p in sorted((akar / "datastore").rglob("*.json")):
        try:
            hasil[str(p)] = baca_datastore(p, peta)
        except Exception as e:
            galat.append((str(p), repr(e)))
    return hasil, galat


def main():
    ap = argparse.ArgumentParser(description="Pembaca BNPB (Tahap 1)")
    ap.add_argument("--akar", required=True, help="mis. data/raw/bnpb/2026-10-20")
    a = ap.parse_args()
    hasil, galat = baca_semua(a.akar)
    print("| berkas | seri | baris |\n|---|---|---|")
    for k, df in hasil.items():
        rel = Path(k).relative_to(Path(a.akar)).as_posix()
        print(f"| {rel} | {df['seri'].iloc[0] if len(df) else ''} | {len(df)} |")
    print(f"\nTotal berkas terbaca: {len(hasil)}; galat: {len(galat)}")
    for k, e in galat:
        print(f"GALAT {k}: {e}")
    raise SystemExit(1 if galat else 0)


if __name__ == "__main__":
    main()