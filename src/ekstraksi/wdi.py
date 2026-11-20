"""Tahap 1 - pembaca WDI (data dan metadata). Tidak membersihkan apa pun."""
import json
from pathlib import Path

import pandas as pd

from src.common.manifest import sha256_raw

RAW = Path("data/raw")
AKAR = RAW / "wdi/2026-10-20"
SERI = "EN.CLC.MDAT.ZS"


def _ratakan(d, awalan=""):
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


def _muat(path):
    with open(path, encoding="utf-8") as f:
        o = json.load(f)
    if not (isinstance(o, list) and len(o) == 2 and isinstance(o[1], list)):
        raise ValueError(f"{path.name}: bentuk tidak dikenali (bukan [meta, daftar]).")
    return o[0], o[1]


def _lineage(df, path):
    rel = path.relative_to(RAW).as_posix()
    df["_berkas_raw"] = rel
    df["_sha256_raw"] = sha256_raw(rel)
    return df


def baca_data(path):
    meta, obs = _muat(path)
    baris = [_ratakan(o) for o in obs if (o.get("indicator") or {}).get("id") == SERI]
    df = pd.DataFrame(baris).astype(object)
    df.attrs["baris_mentah_berkas"] = len(obs)
    return _lineage(df, path)


def baca_metadata(path):
    meta, entri = _muat(path)
    df = pd.DataFrame([_ratakan(e) for e in entri]).astype(object)
    df.attrs["baris_mentah_berkas"] = len(entri)
    return _lineage(df, path)


def baca_semua():
    hasil = {}
    for p in sorted((AKAR / "data").glob("*.json")):
        hasil[p] = baca_data(p)
    for p in sorted((AKAR / "metadata").glob("*.json")):
        hasil[p] = baca_metadata(p)
    return hasil


def main():
    print("| berkas | jenis | baris | baris_mentah | sha256 |")
    print("|---|---|---|---|---|")
    total = 0
    for p, df in baca_semua().items():
        rel = p.relative_to(RAW).as_posix()
        jenis = "data" if p.parent.name == "data" else "metadata"
        sha = df["_sha256_raw"].iloc[0] if len(df) else "-"
        total += len(df)
        print(f"| {rel} | {jenis} | {len(df)} | {df.attrs.get('baris_mentah_berkas')} | {sha[:12]} |")
    print(f"\nTotal baris: {total}")
    raise SystemExit(0 if total else 1)


if __name__ == "__main__":
    main()
