"""Definisi: kunci sama + _berkas_raw beda = revisi; kunci sama + berkas sama = duplikat sejati."""
import pandas as pd, os
OUT = "reports/profil"; KUNCI = ["sumber","seri_kode","wilayah_kode","periode","rincian"]

def deteksi(df):
    os.makedirs(OUT, exist_ok=True)
    out = []
    for k, g in df.groupby(KUNCI, dropna=False):
        if len(g) < 2: continue
        berkas = g["_berkas_raw"].tolist()
        nilai  = g["nilai"].tolist()
        if len(set(berkas)) == 1:
            kat = "duplikat_sejati"
        else:
            kat = "revisi"
        out.append({
            "kunci": "|".join(map(str, k)), "n_baris": len(g),
            "berkas_raw_1": berkas[0], "berkas_raw_2": berkas[1] if len(berkas)>1 else "",
            "nilai_1": nilai[0], "nilai_2": nilai[1] if len(nilai)>1 else None,
            "kategori": kat,
        })
    hasil = pd.DataFrame(out)
    hasil.to_csv(f"{OUT}/duplikat_dan_revisi.csv", index=False)
    return hasil
