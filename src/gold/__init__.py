"""Tahap 4–6 — Gold: panel provinsi x periode x indikator, tabel nasional, rekonsiliasi, dan penyimpanan SQL.

Keluaran:
- data/gold/panel.parquet (panel panjang provinsi x periode x indikator)
- data/gold/panel_lebar.parquet (panel lebar untuk analisis)
- data/gold/tabel_nasional.parquet & tabel_nasional_periode_seri.parquet (tabel agregat nasional)
- data/gold/tabel_rekonsiliasi.parquet (tabel rekonsiliasi 3 pasangan)
- data/gold/gold.sqlite & data/silver/silver.db (penyimpanan relasional SQL)
"""
from src.gold import panel
from src.gold import tabel_nasional
from src.gold import rekonsiliasi
from src.gold import muat_sql


def jalankan(silver):
    """Terima Silver, bangun tabel Gold, dan kembalikan kamus hasil."""
    hasil = {}
    hasil["panel"] = panel.jalankan(silver)
    hasil["nasional"] = tabel_nasional.buat_tabel_nasional(silver)
    hasil["rekonsiliasi"] = rekonsiliasi.buat_tabel_rekonsiliasi(silver)
    hasil["baris_sql"] = muat_sql.muat_semua_ke_sqlite()
    return hasil
