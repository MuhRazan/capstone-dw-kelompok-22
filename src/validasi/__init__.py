"""Tahap 8 — Validasi Silver kasus 22 (korban bencana).

Menjalankan 14 aturan dasar pada Silver dan menulis laporan ke reports/:
- reports/validasi.md
- reports/validasi-agregasi-kabupaten.csv (jumlah kab/kota yang dijumlahkan)
- reports/validasi-agregat-nasional.csv (selisih provinsi vs nasional)

Validasi tidak menunggu Gold: parameter `gold` boleh kosong. Skema Silver tidak diubah.
"""
from pathlib import Path

import pandas as pd

from .aturan import periksa_semua

SILVER = Path("data/silver/silver.parquet")
REPORTS = Path("reports")


def _sidik_data() -> str:
    try:
        from src.common.hasil import data_hash
        return data_hash()
    except Exception:
        return "tidak tersedia"


def _tulis_laporan(df: pd.DataFrame, temuan, artefak) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    total = len(temuan)
    gagal = [t for t in temuan if t.status == "GAGAL"]
    lolos = total - len(gagal)

    baris = [
        "# Validasi Silver — Kasus 22 Korban Bencana",
        "",
        "Dijalankan oleh `python pipeline.py` pada tahap `validasi` (tahap 8).",
        "",
        "| Ringkasan | Nilai |",
        "|---|---|",
        f"| Baris Silver | {len(df):,} |",
        f"| Seri | {df['seri_kode'].nunique()} |",
        f"| Wilayah | {df['wilayah_kode'].nunique()} |",
        f"| Berkas sumber | {df['_berkas_raw'].nunique()} |",
        f"| Periode | {df['periode'].min()}–{df['periode'].max()} |",
        f"| Sidik data mentah (`data_hash`) | `{_sidik_data()}` |",
        f"| Aturan validasi | {total} |",
        f"| Lolos | {lolos} |",
        f"| Gagal | {len(gagal)} |",
        "",
        "Definisi status:",
        "",
        "- **LOLOS** — aturan terpenuhi tanpa catatan.",
        "- **LOLOS_DENGAN_CATATAN** — aturan terpenuhi; selisih/pengecualian yang memang "
        "diizinkan sudah dicatat di tabel pendamping.",
        "- **GAGAL** — aturan dilanggar dan perlu diperbaiki. `aturan_lolos` menghitung "
        "LOLOS dan LOLOS_DENGAN_CATATAN.",
        "",
        "| ID | Aturan | Status | Baris terdampak | Ringkasan |",
        "|---|---|---|---|---|",
    ]
    for t in temuan:
        ringkas = t.ringkas.replace("|", "\\|")
        baris.append(f"| {t.id} | {t.nama} | {t.status} | {t.baris:,} | {ringkas} |")

    baris += ["", "## Catatan dan selisih", ""]
    ada_catatan = False
    for t in temuan:
        if not t.detail:
            continue
        ada_catatan = True
        baris.append(f"### {t.id} — {t.nama}")
        baris.append("")
        baris += [f"- {d}" for d in t.detail]
        baris.append("")
    if not ada_catatan:
        baris += ["Tidak ada catatan tambahan.", ""]

    baris += ["## Aturan gagal", ""]
    if gagal:
        baris += [f"- **{t.id} {t.nama}**: {t.ringkas}" for t in gagal]
    else:
        baris.append("Tidak ada aturan yang gagal.")

    baris += [
        "",
        "## Tabel pendamping",
        "",
        "- `reports/validasi-agregasi-kabupaten.csv` — jumlah kabupaten/kota yang "
        "dijumlahkan untuk setiap baris Silver hasil agregasi 2021–2022, nilai "
        "kabupaten/kota vs rekap provinsi, dan selisihnya.",
        "- `reports/validasi-agregat-nasional.csv` — rekonsiliasi provinsi vs nasional "
        "untuk satuan aditif (`jiwa`, `kejadian`). Seri rasio/persen tidak dijumlahkan.",
        "",
    ]

    tujuan = REPORTS / "validasi.md"
    tujuan.write_text("\n".join(baris), encoding="utf-8")

    for nama, tabel in artefak.items():
        tabel.to_csv(REPORTS / nama, index=False, encoding="utf-8", na_rep="")
    return tujuan


def jalankan(silver, gold=None):
    """Jalankan validasi Silver; Gold boleh belum tersedia.

    Mengembalikan ringkasan angka untuk metrics.json dan bukti artefak.
    """
    if silver is None:
        df = pd.read_parquet(SILVER)
    elif isinstance(silver, pd.DataFrame):
        df = silver.copy()
    else:
        raise TypeError("silver harus DataFrame atau None")

    temuan, artefak = periksa_semua(df)
    laporan = _tulis_laporan(df, temuan, artefak)

    total = len(temuan)
    gagal = [t for t in temuan if t.status == "GAGAL"]
    lolos = total - len(gagal)

    print(f"Validasi Silver: {lolos}/{total} aturan lolos"
          + (f", {len(gagal)} gagal" if gagal else ""))
    for t in temuan:
        print(f"  {t.status:<20} {t.id} {t.nama}: {t.ringkas}")
    print(f"Laporan validasi: {laporan}")
    for nama in artefak:
        print(f"Tabel pendamping: {REPORTS / nama}")

    return {
        "aturan_validasi": total,
        "aturan_lolos": lolos,
        "aturan_gagal": len(gagal),
        "laporan": str(laporan),
        "tabel_pendamping": [str(REPORTS / n) for n in artefak],
    }
