"""Tahap 1 - Ekstraksi. Milik tim.

Baca setiap berkas di data/raw/ menjadi DataFrame mentah yang setia pada sumbernya:
jangan membersihkan di sini; catat asal tiap baris (_berkas_raw, _sha256_raw).
"""
import pandas as pd

from . import bnpb_json, bnpb_xlsx, wdi


def jalankan():
    """Kembalikan {nama_sumber: DataFrame mentah}."""
    hasil, galat = bnpb_json.baca_semua("data/raw/bnpb/2026-10-20")
    if galat:
        raise RuntimeError(f"pembaca JSON galat: {galat[:3]}")
    w = list(wdi.baca_semua().values())
    return {
        "bnpb_xlsx": bnpb_xlsx.baca_semua(),
        "bnpb_json": pd.concat(hasil.values(), ignore_index=True),
        "wdi_data": w[0],
        "wdi_metadata": pd.concat(w[1:], ignore_index=True),
    }
