"""Periksa klaim docs/katalog-seri.csv terhadap log-keputusan.csv dan Silver.

    python -m src.validasi.katalog

Gagal (exit 1) bila ada seri tanpa tautan metadata, koreksi katalog yang tidak
tercatat di log, atau periode yang berpotensi dirata-ratakan.
"""
import csv
import re
from pathlib import Path

KATALOG = Path("docs/katalog-seri.csv")
LOG = Path("log-keputusan.csv")
SILVER = Path("data/silver/silver.parquet")

# periode yang bukan satu tahun tunggal: nilai tidak boleh diulang/dirata-ratakan
RERATA = {"rerata_1990_2009": "EN.CLC.MDAT.ZS"}


def main():
    katalog = list(csv.DictReader(KATALOG.open(encoding="utf-8")))
    log = {r["id"]: r for r in csv.DictReader(LOG.open(encoding="utf-8"))}
    salah = []

    for r in katalog:
        seri = r["seri_kode"]
        if not r.get("url_metadata", "").strip():
            salah.append(f"{seri}: url_metadata kosong")
        if not r.get("url_sdg", "").strip():
            salah.append(f"{seri}: url_sdg kosong")
        for k in set(re.findall(r"K-\d{3}", r.get("catatan", ""))):
            if k not in log:
                salah.append(f"{seri}: {k} disebut di katalog tapi tidak ada di log-keputusan.csv")

    for jenis, seri in RERATA.items():
        baris = [r for r in katalog if r["seri_kode"] == seri]
        if not baris or baris[0]["periode_jenis"] != jenis:
            salah.append(f"{seri}: periode_jenis harus {jenis}")

    if SILVER.exists():
        import pandas as pd

        d = pd.read_parquet(SILVER)
        kunci = ["seri_kode", "wilayah_kode", "periode", "rincian", "sumber", "_berkas_raw"]
        ganda = d.duplicated(kunci).sum()
        if ganda:
            salah.append(f"Silver: {ganda} baris duplikat pada kunci {kunci}")
        for jenis, seri in RERATA.items():
            x = d[d.seri_kode == seri]
            if len(x) != 1:
                salah.append(f"{seri}: harus 1 baris (nilai rerata), ditemukan {len(x)}")
            elif x.jenis_periode.iloc[0] == "tahun" and x.periode.iloc[0] != "2009":
                salah.append(f"{seri}: periode {x.periode.iloc[0]} bukan 2009")
    else:
        print(f"lewati cek Silver: {SILVER} tidak ada")

    for r in katalog:
        print(f"{r['seri_kode']:<32} {r['periode_jenis']:<16} {r['url_metadata'][:80]}")
    print(f"\n{len(katalog)} seri; {len(log)} keputusan tercatat; {len(salah)} masalah")
    for s in salah:
        print(f"MASALAH {s}")
    raise SystemExit(1 if salah else 0)


if __name__ == "__main__":
    main()
