"""Satu perintah reproduksi tim: data mentah -> Silver -> Gold -> validasi.

    python unduh_data.py --kasus <N>     # sekali, isi data/raw/
    python pipeline.py

Urutan tahap tidak diubah; isi tiap tahap di src/<tahap>/. Tahap 7 (skala, arsip WDI) ditulis
sebagai skrip terpisah di src/skala/ karena memakai unduhan tambahan.
"""
import sys
import time

from src import ekstraksi, gold, silver, validasi
from src.common.manifest import periksa


def main():
    n, salah = periksa()
    if salah:
        sys.exit(f"data/raw tidak cocok dengan MANIFEST.csv ({len(salah)} berkas). Jalankan ulang unduh_data.py.")
    print(f"data/raw: {n} berkas cocok dengan MANIFEST.csv")
    for nama, langkah in [("ekstraksi", lambda h: ekstraksi.jalankan()),
                          ("silver", lambda h: silver.jalankan(h["ekstraksi"])),
                          ("gold", lambda h: gold.jalankan(h["silver"])),
                          ("validasi", lambda h: validasi.jalankan(h["silver"], h["gold"]))]:
        mulai = time.time()
        try:
            hasil[nama] = langkah(hasil)
        except NotImplementedError as e:
            # Validasi tidak menunggu Sprint 3: Gold dilewati bila belum tersedia.
            if nama != "gold":
                raise
            print(f"{nama:<10} dilewati (belum tersedia pada Sprint 2): {e}")
            hasil[nama] = {}
            continue
        print(f"{nama:<10} selesai dalam {time.time() - mulai:.1f} s")

    ringkas = hasil.get("validasi", {})
    if ringkas.get("aturan_gagal"):
        sys.exit(f"Validasi Silver gagal: {ringkas['aturan_gagal']} aturan. "
                 f"Lihat {ringkas.get('laporan', 'reports/validasi.md')}.")
    print("Periksa skema minimal: python -m src.common.skema data/silver/silver.parquet")


hasil = {}

if __name__ == "__main__":
    main()
