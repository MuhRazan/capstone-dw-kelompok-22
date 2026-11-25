"""Tahap 4 — Panel Gold provinsi x periode x indikator.

Aturan satu nilai per sel:
1. Snapshot: bila satu sel memiliki angka dari beberapa snapshot (17 dan 20 Oktober), snapshot terbaru
   (20 Oktober) diutamakan.
2. Rincian: indikator panel utama menggunakan deret agregat 'total' (jika ada) atau jumlahan semua
   jenis bencana 'jumlah' per berkas. Rincian jenis bencana individual tetap tersimpan di Silver untuk
   audit dan analisis terperinci. Rincian jenis bencana dienkode konsisten di seluruh tahun.
3. Berkas: bila satu sel wilayah x periode memiliki beberapa berkas, berkas dipilih berdasarkan
   URUTAN_BERKAS (deret tabel provinsi langsung -> rekapitulasi provinsi -> kompilasi).
4. Periode: diperiksa jenis periodenya ('tahun', 'semester', 'triwulan', 'bulan'). Disimpan apa adanya,
   tanpa perataan sub-tahunan ke tahunan secara diam-diam di Gold.
5. Penanda: penanda outlier, patahan, dan galat input dari Sprint 1 (reports/anomali.csv) ikut terbawa
   ke Gold sebagai kolom 'penanda'; nilai aslinya dipertahankan utuh, tidak dihapus.
6. Kolom Turunan:
   - nilai_per_100rb: normalisasi rasio per 100 ribu penduduk terhadap penyebut jumlah_penduduk 2025.
   - nilai_log1p: transformasi log(1 + nilai) untuk analisis statistik pada data yang skewed.
   - rincian_kode: kode numerik jenis bencana / kategori agregat yang konsisten.
   Nilai asli tetap tersimpan di kolom 'nilai'.
7. Sel Kosong: panel memuat grid lengkap 38 provinsi x periode x indikator; sel kosong dikategorikan
   dengan status_sel ('tidak_diterbitkan', 'belum_ada') dari reports/grid-sel-kosong.csv tanpa interpolasi.

Keluaran:
- data/gold/panel.parquet (format panjang, memuat sel terisi dan sel kosong berstatus)
- data/gold/panel_lebar.parquet (format lebar, satu kolom per indikator)
- reports/panel-gold.md (dokumentasi aturan, ringkasan indikator, dan status sel)
"""
from fnmatch import fnmatch
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
GOLD = ROOT / "data" / "gold"
REPORTS = ROOT / "reports"

# 38 Provinsi BPS 2025
PROVINSI_NAMA = {
    1100: "Aceh", 1200: "Sumatera Utara", 1300: "Sumatera Barat", 1400: "Riau", 1500: "Jambi",
    1600: "Sumatera Selatan", 1700: "Bengkulu", 1800: "Lampung", 1900: "Kepulauan Bangka Belitung",
    2100: "Kepulauan Riau", 3100: "DKI Jakarta", 3200: "Jawa Barat", 3300: "Jawa Tengah",
    3400: "DI Yogyakarta", 3500: "Jawa Timur", 3600: "Banten", 5100: "Bali", 5200: "Nusa Tenggara Barat",
    5300: "Nusa Tenggara Timur", 6100: "Kalimantan Barat", 6200: "Kalimantan Tengah",
    6300: "Kalimantan Selatan", 6400: "Kalimantan Timur", 6500: "Kalimantan Utara",
    7100: "Sulawesi Utara", 7200: "Sulawesi Tengah", 7300: "Sulawesi Selatan",
    7400: "Sulawesi Tenggara", 7500: "Gorontalo", 7600: "Sulawesi Barat", 8100: "Maluku",
    8200: "Maluku Utara", 9100: "Papua", 9200: "Papua Barat", 9300: "Papua Selatan",
    9400: "Papua Tengah", 9500: "Papua Pegunungan", 9600: "Papua Barat Daya",
}

NAMA_KE_KODE_BPS = {v: k for k, v in PROVINSI_NAMA.items()}

# Urutan prioritas berkas
URUTAN_BERKAS = [
    ("*/5dfcae7e-*", "Jumlah Kejadian Bencana Menurut Provinsi Tahun 2010-2024"),
    ("*/tangan/*per-provinsi*", "rekap provinsi 2021/2022"),
    ("*/tangan/*menurut-provinsi*", "tabel provinsi 2025"),
    ("*/datastore/data-bencana-indonesia/*", "tabel provinsi 2024 data-bencana-indonesia"),
    ("*/datastore/kompilasi-*/*", "salinan tabel 2024 kompilasi"),
    ("*/tangan/*kabup*", "rekap kab/kota cadangan"),
]

# Enkode rincian bencana konsisten
RINCIAN_KODE = {
    "total": 0,
    "jumlah": 0,
    "banjir": 1,
    "cuaca_ekstrem": 2,
    "tanah_longsor": 3,
    "kebakaran_hutan_dan_lahan": 4,
    "gelombang_pasang_dan_abrasi": 5,
    "gempabumi": 6,
    "kekeringan": 7,
    "tsunami": 8,
    "erupsi_gunung_api": 9,
}

SATUAN_MAP = {
    "jumlah_penduduk": "jiwa",
    "kejadian": "kejadian",
    "korban_hilang": "jiwa",
    "korban_luka_sakit": "jiwa",
    "korban_mengungsi": "jiwa",
    "korban_mengungsi_per_100rb": "per_100000_penduduk",
    "korban_meninggal": "jiwa",
    "korban_meninggal_hilang_per_100rb": "per_100000_penduduk",
    "korban_terdampak": "jiwa",
    "korban_terdampak_mengungsi": "jiwa",
}

SERI_LIST = [
    ("jumlah_penduduk", "total"),
    ("kejadian", "jumlah"),
    ("korban_hilang", "jumlah"),
    ("korban_luka_sakit", "jumlah"),
    ("korban_mengungsi", "jumlah"),
    ("korban_mengungsi_per_100rb", "jumlah"),
    ("korban_meninggal", "jumlah"),
    ("korban_meninggal_hilang_per_100rb", "jumlah"),
    ("korban_terdampak", "jumlah"),
    ("korban_terdampak_mengungsi", "jumlah"),
]


def peringkat_berkas(berkas):
    return next((i for i, (p, _) in enumerate(URUTAN_BERKAS) if fnmatch(str(berkas), p)), len(URUTAN_BERKAS))


def deteksi_jenis_periode(periode):
    p = str(periode)
    if len(p) == 4 and p.isdigit():
        return "tahun"
    if "-S" in p:
        return "semester"
    if "-Q" in p:
        return "triwulan"
    if len(p) == 7 and p[4] == "-":
        return "bulan"
    return "tahun"


def pilih_sel_terisi(silver):
    """Pilih tepat satu nilai per provinsi x periode x indikator dari Silver."""
    prov = silver[silver["wilayah_kode"] != 9999].copy()

    all_isi = []
    for seri, rincian_tipe in SERI_LIST:
        s = prov[prov["seri_kode"] == seri].copy()
        if s.empty:
            continue

        if rincian_tipe == "total":
            hasil = s[s["rincian"] == "total"].copy()
            lbl = seri
        else:
            k = ["wilayah_kode", "periode", "_berkas_raw"]
            total = s[s["rincian"] == "total"]
            sisa = s[(s["rincian"] != "total") & ~s.set_index(k).index.isin(total.set_index(k).index)]
            jml = sisa.groupby(k, as_index=False).agg(
                **{c: (c, "first") for c in s.columns if c not in k + ["nilai"]},
                nilai=("nilai", "sum")
            )
            hasil = pd.concat([total, jml], ignore_index=True)
            lbl = f"{seri} [jumlah]"

        # Prioritas berkas kanonik (snapshot terbaru dan jalur terurut)
        hasil = hasil.assign(_p=hasil["_berkas_raw"].map(peringkat_berkas)).sort_values(["_p", "_berkas_raw"])
        satu = hasil.drop_duplicates(["wilayah_kode", "periode"]).copy()
        satu["indikator"] = lbl
        satu["rincian"] = rincian_tipe
        all_isi.append(satu)

    isi_df = pd.concat(all_isi, ignore_index=True)
    isi_df["status_sel"] = "terisi"
    return isi_df


def muat_sel_kosong():
    """Muat sel kosong berkategori dari grid Sprint 1."""
    grid_csv = REPORTS / "grid-sel-kosong.csv"
    if not grid_csv.exists():
        return pd.DataFrame()

    g = pd.read_csv(grid_csv, dtype={"periode": str})
    g_prov = g[g["tingkat"] == "provinsi"].rename(
        columns={"seri_kode": "indikator", "kategori": "status_sel"}
    ).copy()

    # Petakan nama ke kode wilayah resmi BPS 2025
    g_prov["wilayah_kode"] = g_prov["nama_wilayah"].map(NAMA_KE_KODE_BPS)
    g_prov["seri_kode"] = g_prov["indikator"].map(lambda x: x.split(" [")[0])
    g_prov["rincian"] = g_prov["indikator"].map(lambda x: x.split(" [", 1)[1][:-1] if " [" in x else "total")
    g_prov["nilai"] = np.nan
    g_prov["sumber"] = "bnpb"
    g_prov["_berkas_raw"] = None
    g_prov["_sha256_raw"] = None
    return g_prov


def muat_penanda_anomali():
    """Muat penanda outlier dan patahan dari Sprint 1."""
    anom_csv = REPORTS / "anomali.csv"
    if not anom_csv.exists():
        return {}

    anom = pd.read_csv(anom_csv, dtype={"periode": str})
    anom["wilayah_kode_bps"] = anom["nama_wilayah"].map(NAMA_KE_KODE_BPS)
    return {
        (r.seri_kode, int(r.wilayah_kode_bps), str(r.periode)): r.kategori
        for r in anom.itertuples()
        if pd.notna(r.wilayah_kode_bps)
    }


def format_tabel_markdown(df, desimal=2):
    """Format DataFrame ke tabel markdown."""
    if df.empty:
        return "_(kosong)_"
    kolom = [str(c) for c in df.columns]

    def format_sel(v):
        if isinstance(v, (float, np.floating)):
            return "" if pd.isna(v) else f"{v:,.{desimal}f}"
        if isinstance(v, (int, np.integer)):
            return f"{v:,}"
        return str(v).replace("|", "\\|").replace("\n", " ")

    header = "| " + " | ".join(kolom) + " |"
    divider = "| " + " | ".join("---" for _ in kolom) + " |"
    baris = ["| " + " | ".join(format_sel(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join([header, divider] + baris)


def jalankan(silver):
    """Bentuk panel Gold provinsi x periode x indikator dan simpan ke data/gold/."""
    GOLD.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    # 1. Pilih sel terisi
    isi = pilih_sel_terisi(silver)
    total_silver_prov = len(silver[silver["wilayah_kode"] != 9999])
    tidak_terpilih = total_silver_prov - len(isi)

    # 2. Muat sel kosong
    kosong = muat_sel_kosong()

    # 3. Gabungkan panel
    p = pd.concat([isi, kosong], ignore_index=True)
    p["wilayah_kode"] = p["wilayah_kode"].astype(int)
    p["nama_wilayah"] = p["wilayah_kode"].map(PROVINSI_NAMA)
    p["jenis_periode"] = p["periode"].map(deteksi_jenis_periode)
    p["satuan"] = p["seri_kode"].map(SATUAN_MAP)
    p["rincian_kode"] = p["rincian"].map(RINCIAN_KODE).fillna(0).astype(int)

    # 4. Tempelkan penanda anomali Sprint 1
    tanda_map = muat_penanda_anomali()
    p["penanda"] = [
        tanda_map.get((ind, int(w), str(per)))
        for ind, w, per in zip(p["indikator"], p["wilayah_kode"], p["periode"])
    ]

    # 5. Normalisasi per 100 ribu penduduk terhadap penduduk 2025
    pddk_map = silver[
        (silver["seri_kode"] == "jumlah_penduduk") &
        (silver["rincian"] == "total") &
        (silver["wilayah_kode"] != 9999)
    ].set_index("wilayah_kode")["nilai"].to_dict()

    def normalisasi_per_100rb(row):
        if pd.isna(row["nilai"]):
            return np.nan
        if row["satuan"] == "per_100000_penduduk":
            return float(row["nilai"])
        pop = pddk_map.get(row["wilayah_kode"])
        if pop and pop > 0:
            return float((row["nilai"] / pop) * 100000.0)
        return np.nan

    p["nilai_per_100rb"] = p.apply(normalisasi_per_100rb, axis=1)

    # 6. Transformasi logaritma log(1 + nilai)
    p["nilai_log1p"] = np.log1p(p["nilai"].astype(float))

    # 7. Susun kolom panel panjang
    kolom_urut = [
        "indikator", "seri_kode", "rincian", "rincian_kode", "wilayah_kode", "nama_wilayah",
        "periode", "jenis_periode", "nilai", "nilai_per_100rb", "nilai_log1p",
        "satuan", "status_sel", "penanda", "_berkas_raw", "_sha256_raw"
    ]
    p = p[kolom_urut].sort_values(["indikator", "periode", "wilayah_kode"]).reset_index(drop=True)

    # Simpan panel panjang ke Parquet
    panel_parquet = GOLD / "panel.parquet"
    p.to_parquet(panel_parquet, index=False)

    # 8. Susun panel lebar (hanya sel terisi)
    lebar = (
        p[p["status_sel"] == "terisi"]
        .pivot_table(
            index=["wilayah_kode", "nama_wilayah", "jenis_periode", "periode"],
            columns="indikator",
            values="nilai",
            aggfunc="first"
        )
        .reset_index()
    )
    lebar.columns.name = None
    lebar_parquet = GOLD / "panel_lebar.parquet"
    lebar.to_parquet(lebar_parquet, index=False)

    # 9. Laporan panel-gold.md
    ringkas_ind = (
        p.assign(t=p["status_sel"] == "terisi")
        .groupby(["indikator", "satuan"])
        .agg(
            periode=("periode", lambda s: f"{s.min()}–{s.max()}" if s.nunique() > 1 else s.min()),
            jumlah_periode=("periode", "nunique"),
            sel=("t", "size"),
            terisi=("t", "sum"),
            ditandai=("penanda", lambda s: int(s.notna().sum()))
        )
        .reset_index()
    )

    status_sel_df = p.pivot_table(
        index="indikator", columns="status_sel", values="wilayah_kode", aggfunc="size", fill_value=0
    ).reset_index()

    laporan_md = "\n\n".join([
        "# Panel Gold provinsi x periode x indikator",
        "Dihasilkan otomatis oleh `python pipeline.py` (`src/gold/panel.py`) dari Silver, grid kelengkapan, dan penanda anomali Sprint 1.",
        "## Aturan satu nilai per sel",
        "1. **Snapshot**: Bila terdapat lebih dari satu snapshot data, snapshot terbaru (20 Oktober) diutamakan.\n"
        "2. **Rincian**: Satu indikator = satu deret agregat utama ('total' bila tersedia, atau jumlahan semua bencana 'jumlah' per berkas). Rincian jenis bencana individual tetap tersimpan di Silver untuk keperluan audit.\n"
        "3. **Berkas**: Bila satu sel memiliki data dari beberapa berkas, URUTAN_BERKAS memilih berkas prioritas kanonik.\n"
        "4. **Periode**: Disimpan apa adanya sesuai format ISO; tidak dilakukan perataan sub-tahunan ke tahunan secara diam-diam.\n"
        "5. **Penanda**: Outlier asli, patahan wilayah, dan galat input dari Sprint 1 dipertahankan nilainya dan dicatat pada kolom `penanda`.\n"
        "6. **Kolom Turunan**: Tersedia `nilai_per_100rb` (normalisasi rasio per 100 ribu penduduk) dan `nilai_log1p` (transformasi logaritma log(1+x)) untuk analisis distribusi skewed, sementara `nilai` asli tetap tersimpan utuh.",
        f"**Baris Silver provinsi yang tidak terpilih masuk panel utama (rincian per bencana atau berkas non-kanonik)**: {tidak_terpilih:,} baris.",
        "## Ringkasan Indikator Panel",
        format_tabel_markdown(ringkas_ind),
        "## Distribusi Status Sel",
        format_tabel_markdown(status_sel_df),
        "Keterangan status sel: `terisi` = observasi riil tersedia; `tidak_diterbitkan` = belum diterbitkan oleh BNPB per provinsi; `belum_ada` = provinsi pemekaran baru belum dibentuk.",
        f"## Berkas Keluaran\n\n- `data/gold/panel.parquet`: {len(p):,} baris (format panjang, memuat sel terisi dan sel kosong berstatus).\n"
        f"- `data/gold/panel_lebar.parquet`: {len(lebar):,} baris x {lebar.shape[1]} kolom (format lebar untuk pemodelan dan regresi).",
    ])

    laporan_path = REPORTS / "panel-gold.md"
    laporan_path.write_text(laporan_md, encoding="utf-8")

    print(f"Gold Panel: {len(p):,} baris ({len(isi):,} terisi, {len(kosong):,} kosong), "
          f"{p['indikator'].nunique()} indikator, {tidak_terpilih:,} baris Silver tidak terpilih")
    print(f"Berkas tersimpan di {panel_parquet} dan {lebar_parquet}")
    print(f"Laporan tersimpan di {laporan_path}")

    return p
