"""Tahap 4–6 — Gold: panel provinsi x periode x indikator, tabel nasional, dan penyimpanan SQL.

Keluaran:
- data/gold/panel.parquet (panel panjang provinsi x periode x indikator)
- data/gold/panel_lebar.parquet (panel lebar untuk analisis)
- data/gold/tabel_nasional_periode_seri.parquet (tabel agregat nasional)
- data/gold/gold.sqlite & data/silver/silver.db (penyimpanan relasional SQL)
"""
from src.gold import panel
from src.gold import tabel_nasional
from src.gold import muat_sql


def jalankan(silver):
    """Terima Silver, bangun tabel Gold, dan kembalikan kamus hasil."""
    hasil = {}
    hasil["panel"] = panel.jalankan(silver)
    hasil["nasional"] = tabel_nasional.buat_tabel_nasional(silver)
    hasil["baris_sql"] = muat_sql.muat_silver_ke_sqlite()
    return hasil
