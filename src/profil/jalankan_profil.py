"""Entry point: jalankan seluruh tahap profil BNPB."""
from src.profil.baca_silver import baca_silver
from src.profil.profil_seri import profil
from src.profil.deteksi_anomali import tandai
from src.profil.deteksi_patahan import deteksi as det_patahan
from src.profil.deteksi_duplikat import deteksi as det_dup
from src.profil.deteksi_galat_input import deteksi as det_galat
from src.profil.buat_grafik import buat

def main():
    df = baca_silver()
    print("baris BNPB:", len(df), "| seri:", df["seri_kode"].nunique())
    profil(df)
    anom = tandai(df)
    pat  = det_patahan(df)
    dup  = det_dup(df)
    gal  = det_galat(df)
    n_gambar = buat(df, pat)
    print("outlier_ditandai:", len(anom))
    print("patahan_ditandai:", len(pat))
    print("duplikat/revisi:", len(dup), (dup["kategori"].value_counts().to_dict() if len(dup) else {}))
    print("temuan_galat_input:", len(gal))
    print("gambar_dihasilkan:", n_gambar)

if __name__ == "__main__":
    main()
