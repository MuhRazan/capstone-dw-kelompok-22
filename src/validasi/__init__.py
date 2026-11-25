"""Tahap 8 — Validasi Silver dan Gold kasus 22 (korban bencana).

Menjalankan 14 aturan dasar pada Silver dan 10 aturan pada Gold & rekonsiliasi:
- Silver: R01-R14 (skema, kunci, nilai, satuan, wilayah, periode, rincian, lineage, cakupan, agregat kab/kota & nasional)
- Gold: R15-R24 (kunci panel unik, satu satuan per indikator, status sel & nilai, sel tertelusur ke Silver,
  nilai sama dengan Silver, tabel nasional unik, rekonsiliasi kategori baku, selisih konsisten,
  baris berpasangan dihitung, periode utama tidak dibuang)

Menulis laporan ke:
- reports/validasi.md
- reports/validasi-agregasi-kabupaten.csv
- reports/validasi-agregat-nasional.csv
"""
from pathlib import Path

import pandas as pd

from .aturan import Temuan, periksa_semua
from .gold import ATURAN as ATURAN_GOLD

SILVER = Path("data/silver/silver.parquet")
REPORTS = Path("reports")
GOLD_PANEL = Path("data/gold/panel.parquet")
GOLD_NASIONAL = Path("data/gold/nasional.parquet")
GOLD_REKONSILIASI = Path("data/gold/rekonsiliasi.parquet")


def _sidik_data() -> str:
    try:
        from src.common.hasil import data_hash
        return data_hash()
    except Exception:
        return "tidak tersedia"


def _tulis_laporan(df_silver: pd.DataFrame, gold_dict: dict, temuan: list[Temuan], artefak: dict) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    total = len(temuan)
    gagal = [t for t in temuan if t.status == "GAGAL"]
    lolos = total - len(gagal)

    panel_len = len(gold_dict["panel"]) if gold_dict and "panel" in gold_dict and gold_dict["panel"] is not None else 0
    nas_len = len(gold_dict["nasional"]) if gold_dict and "nasional" in gold_dict and gold_dict["nasional"] is not None else 0
    rek_len = len(gold_dict["rekonsiliasi"]) if gold_dict and "rekonsiliasi" in gold_dict and gold_dict["rekonsiliasi"] is not None else 0

    baris = [
        "# Validasi Silver dan Gold — Kasus 22 Korban Bencana",
        "",
        "Dijalankan oleh `python pipeline.py` pada tahap `validasi` (tahap 8).",
        "",
        "| Ringkasan | Nilai |",
        "|---|---|",
        f"| Baris Silver | {len(df_silver):,} |",
        f"| Seri Silver | {df_silver['seri_kode'].nunique()} |",
        f"| Wilayah Silver | {df_silver['wilayah_kode'].nunique()} |",
        f"| Berkas sumber | {df_silver['_berkas_raw'].nunique()} |",
        f"| Periode | {df_silver['periode'].min()}–{df_silver['periode'].max()} |",
        f"| Baris Panel Gold | {panel_len:,} |",
        f"| Baris Nasional Gold | {nas_len:,} |",
        f"| Baris Rekonsiliasi | {rek_len:,} |",
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
    """Jalankan validasi Silver dan Gold.

    Mengembalikan ringkasan angka untuk metrics.json dan bukti artefak.
    """
    if silver is None:
        df_silver = pd.read_parquet(SILVER)
    elif isinstance(silver, pd.DataFrame):
        df_silver = silver.copy()
    else:
        raise TypeError("silver harus DataFrame atau None")

    # Siapkan kamus gold
    gold_dict = {}
    if isinstance(gold, dict):
        gold_dict = dict(gold)

    if "panel" not in gold_dict and GOLD_PANEL.exists():
        gold_dict["panel"] = pd.read_parquet(GOLD_PANEL)
    if "nasional" not in gold_dict and GOLD_NASIONAL.exists():
        gold_dict["nasional"] = pd.read_parquet(GOLD_NASIONAL)
    if "rekonsiliasi" not in gold_dict and GOLD_REKONSILIASI.exists():
        gold_dict["rekonsiliasi"] = pd.read_parquet(GOLD_REKONSILIASI)

    # 1. Jalankan 14 aturan Silver (R01 - R14)
    temuan_silver, artefak = periksa_semua(df_silver)

    # 2. Jalankan 10 aturan Gold & Rekonsiliasi (R15 - R24) bila gold tersedia
    temuan_gold = []
    if gold_dict and "panel" in gold_dict:
        id_num = 15
        for nama_aturan, ket, keras, func in ATURAN_GOLD:
            buruk = func(df_silver, gold_dict)
            n_buruk = len(buruk) if hasattr(buruk, "__len__") else (0 if buruk is None else len(buruk))
            if n_buruk == 0:
                status = "LOLOS"
                ringkas = f"{ket} (terpenuhi, 0 pelanggaran)"
                detail = []
            else:
                status = "GAGAL" if keras else "LOLOS_DENGAN_CATATAN"
                ringkas = f"{n_buruk} baris terdeteksi tidak memenuhi aturan"
                detail = [f"{nama_aturan}: ditemukan {n_buruk} baris."]

            temuan_gold.append(Temuan(
                id=f"R{id_num:02d}",
                nama=nama_aturan,
                status=status,
                baris=n_buruk,
                ringkas=ringkas,
                detail=detail
            ))
            id_num += 1

    semua_temuan = temuan_silver + temuan_gold
    laporan = _tulis_laporan(df_silver, gold_dict, semua_temuan, artefak)

    total = len(semua_temuan)
    gagal = [t for t in semua_temuan if t.status == "GAGAL"]
    lolos = total - len(gagal)

    print(f"Validasi Silver & Gold: {lolos}/{total} aturan lolos"
          + (f", {len(gagal)} gagal" if gagal else ""))
    for t in semua_temuan:
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
