"""Konstanta bersama komponen profil: susunan 38 provinsi, jendela terbit seri,
dan aturan sel tidak berlaku.

Semua aturan di sini berasal dari log-keputusan.csv (K-001, K-002, K-020,
K-025 sampai K-027). Modul lain tidak boleh menebak sendiri.
"""

INDONESIA = 9999

# Susunan 38 provinsi tahun 2025 (K-001/K-002). Nama kanonik mengikuti berkas
# 2025 yang sudah memakai 38 provinsi.
PROVINSI = {
    1100: "ACEH",
    1200: "SUMATERA UTARA",
    1300: "SUMATERA BARAT",
    1400: "RIAU",
    1500: "JAMBI",
    1600: "SUMATERA SELATAN",
    1700: "BENGKULU",
    1800: "LAMPUNG",
    1900: "KEPULAUAN BANGKA BELITUNG",
    2100: "KEPULAUAN RIAU",
    3100: "DKI JAKARTA",
    3200: "JAWA BARAT",
    3300: "JAWA TENGAH",
    3400: "DAERAH ISTIMEWA YOGYAKARTA",
    3500: "JAWA TIMUR",
    3600: "BANTEN",
    5100: "BALI",
    5200: "NUSA TENGGARA BARAT",
    5300: "NUSA TENGGARA TIMUR",
    6100: "KALIMANTAN BARAT",
    6200: "KALIMANTAN TENGAH",
    6300: "KALIMANTAN SELATAN",
    6400: "KALIMANTAN TIMUR",
    6500: "KALIMANTAN UTARA",
    7100: "SULAWESI UTARA",
    7200: "SULAWESI TENGAH",
    7300: "SULAWESI SELATAN",
    7400: "SULAWESI TENGGARA",
    7500: "GORONTALO",
    7600: "SULAWESI BARAT",
    8100: "MALUKU",
    8200: "MALUKU UTARA",
    9100: "PAPUA",
    9200: "PAPUA BARAT",
    9300: "PAPUA SELATAN",
    9400: "PAPUA TENGAH",
    9500: "PAPUA PEGUNUNGAN",
    9600: "PAPUA BARAT DAYA",
}

SERI_BNPB = [
    "kejadian",
    "korban_meninggal",
    "korban_hilang",
    "korban_luka_sakit",
    "korban_mengungsi",
    "korban_terdampak",
    "korban_terdampak_mengungsi",
    "korban_mengungsi_per_100rb",
    "korban_meninggal_hilang_per_100rb",
    "jumlah_penduduk",
]

SERI_HITUNG = [
    "kejadian",
    "korban_meninggal",
    "korban_hilang",
    "korban_luka_sakit",
    "korban_mengungsi",
    "korban_terdampak",
    "korban_terdampak_mengungsi",
    "jumlah_penduduk",
]

SERI_LAJU = [
    "korban_mengungsi_per_100rb",
    "korban_meninggal_hilang_per_100rb",
]

# Jendela terbit tingkat provinsi. Tahun di luar jendela = tidak_berlaku,
# bukan missing (K-025). Sumber utama: ketersediaan Silver per seri.
TAHUN_MULAI = {
    "kejadian": 2010,
    "korban_meninggal": 2021,
    "korban_hilang": 2021,
    "korban_luka_sakit": 2021,
    "korban_mengungsi": 2024,
    "korban_terdampak": 2024,
    "korban_terdampak_mengungsi": 2021,
    "korban_mengungsi_per_100rb": 2025,
    "korban_meninggal_hilang_per_100rb": 2025,
    "jumlah_penduduk": 2025,
}

TAHUN_AKHIR = {s: 2025 for s in SERI_BNPB}
TAHUN_AKHIR["korban_terdampak_mengungsi"] = 2022

# Tahun pertama provinsi baru. Sel sebelum tahun ini tidak_berlaku (K-026).
MULAI_PROVINSI = {
    6500: 2012,  # Kalimantan Utara
    9300: 2022,  # Papua Selatan
    9400: 2022,  # Papua Tengah
    9500: 2022,  # Papua Pegunungan
    9600: 2022,  # Papua Barat Daya
}

# Seri korban 2021/2022 hanya tersedia dengan batas lama 34 provinsi.
# Nilai 9100/9200 adalah nilai batas lama; 9300-9600 belum terpisah (K-027).
SERI_KORBAN_BATAS_LAMA = [
    "korban_meninggal",
    "korban_hilang",
    "korban_luka_sakit",
    "korban_terdampak_mengungsi",
]
TAHUN_BATAS_LAMA = [2021, 2022]
PROVINSI_BATAS_LAMA = [9100, 9200]

# Seri yang tidak terbit sama sekali pada 2023 di tingkat provinsi.
TAHUN_KOSONG_TERBIT = {2023: ["korban_meninggal", "korban_hilang", "korban_luka_sakit"]}

NAMA_SERI = {
    "kejadian": "Jumlah kejadian bencana",
    "korban_meninggal": "Korban meninggal",
    "korban_hilang": "Korban hilang",
    "korban_luka_sakit": "Korban luka/sakit",
    "korban_mengungsi": "Korban mengungsi",
    "korban_terdampak": "Korban terdampak",
    "korban_terdampak_mengungsi": "Korban terdampak-mengungsi (kolom gabungan)",
    "korban_mengungsi_per_100rb": "Korban mengungsi per 100.000 penduduk",
    "korban_meninggal_hilang_per_100rb": "Korban meninggal+hilang per 100.000 penduduk",
    "jumlah_penduduk": "Jumlah penduduk",
}

SATUAN = {
    "kejadian": "kejadian",
    "korban_mengungsi_per_100rb": "per_100000_penduduk",
    "korban_meninggal_hilang_per_100rb": "per_100000_penduduk",
    "EN.CLC.MDAT.ZS": "persen_penduduk",
}
