"""Tahap 4–6 — Gold: panel provinsi x periode x indikator, tabel nasional, rekonsiliasi, dan penyimpanan SQL.

Keluaran:
- data/gold/panel.parquet (panel panjang provinsi x periode x indikator)
- data/gold/panel_lebar.parquet (panel lebar untuk analisis)
- data/gold/nasional.parquet (tabel nasional Gold)
- data/gold/rekonsiliasi.parquet (tabel rekonsiliasi seri utama vs pembanding)
- data/gold/tabel_nasional_periode_seri.parquet (tabel agregat nasional periode x seri)
- data/gold/gold.sqlite (penyimpanan relasional SQL)
"""
from src.gold import panel
from src.gold import tabel_nasional
from src.gold import muat_sql
from src.gold import nasional_gold
from src.gold import rekonsiliasi


def jalankan(silver):
    """Terima Silver, bangun tabel Gold, dan kembalikan kamus hasil."""
    hasil = {}
    hasil["panel"] = panel.jalankan(silver)
    hasil["nasional"] = nasional_gold.jalankan(silver)
    hasil["rekonsiliasi"] = rekonsiliasi.jalankan(hasil["nasional"])
    hasil["baris_sql"] = muat_sql.muat_silver_ke_sqlite()
    tabel_nasional.buat_tabel_nasional()
    return hasil
