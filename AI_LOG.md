# AI_LOG — KORBAN DEADLINE (Kasus 22: Korban Bencana)

Satu baris per pemakaian AI yang bermakna (ChatGPT, Claude, Copilot, Bravais, dan sejenisnya).
Ringkas dan jujur; transkrip penuh tidak diminta. Yang dinilai bukan "pakai AI atau tidak",
melainkan "mengerti atau tidak" — isi kolom terakhir dengan apa yang Anda ubah dari keluarannya.

| Tanggal | Siapa (NIM) | Alat | Untuk apa | Apa yang diubah dari keluarannya |
|---|---|---|---|---|
| 2026-11-13 | 124450031 | OpenCode + DeepSeek V4.1 Flash (gratis) | Menyiapkan branch 124450031/kerja dan metrik Sprint 1: unduh data, cek sha256, isi `metrics.json` dengan `data_hash` | Struktur folder dipertahankan, akun GitHub diganti sebelum push, branch dan PR dirapikan sendiri |
| 2026-11-19 | 124450031 | OpenCode + DeepSeek V4.1 Flash (gratis) | Memeriksa kode SDG, satuan, dan nama seri katalog (#10) terhadap sumber dan repo kunci | Hasil dicek ulang ke repo kunci, koreksi dicatat di `log-keputusan.csv` |
| 2026-11-21 | 124450089 | Antigravity | DDL awal tabel Silver & pemuat SQLite | Menyesuaikan tipe kolom baku ANSI SQL, menetapkan Primary Key komposit 6 kolom untuk menegakkan aturan R02, dan menambahkan penanganan transaksi commit SQLite. |
| 2026-11-25 | 124450128 | Antigravity (Gemini) | Tahap 6: identifikasi rincian pembanding EN.CLC.MDAT.ZS yang sebanding dengan seri utama BNPB, samakan bentuk periode, tulis K-043 di log-keputusan.csv | Cek langsung berkas mentah (kelompok-01-hal-01.json) dan metadata (sumber2_indikator.json); keputusan rincian & periode dikonfirmasi sendiri sebelum ditulis ke CSV |
| 2026-11-25 | 124450089 | Antigravity | Integrasi skema SQL 4 tabel (Tahap 5) | Memperluas skema DDL untuk mencakup `silver`, `panel_gold`, `tabel_nasional`, dan `tabel_rekonsiliasi`, mengintegrasikannya ke `pipeline.py`, serta menambahkan assertion otomatis kesetaraan baris SQL vs Parquet. |
| 2026-11-25 | 124450089 | Antigravity | Draf tabel rekonsiliasi 3 pasangan (Tahap 6) | Menyesuaikan klasifikasi kategori menjadi 5 kategori baku panduan (*definisi berbeda*, *metode berbeda*, *vintage berbeda*, *cakupan berbeda*, *belum terjelaskan*), dan memastikan periode tanpa pasangan (17 periode 2009–2025) tetap tampil tanpa interpolasi. |
| 2026-11-25 | 124450031 | OpenCode + DeepSeek V4.1 Flash (gratis) | Menjalankan pipeline dan mengaudit panel Gold (#22): kunci unik, lineage, satuan, metrik | Memilih opsi A tanpa mengubah skema panel, angka dihitung ulang, bukti ditulis di `reports/verifikasi-panel.md` |
| 2026-11-26 | 124450128 | Antigravity (Gemini) | Perbaiki K-043 agar tiga aspek (rincian dipakai, periode dipakai, alasan rincian tidak dipasangkan) tertulis eksplisit dan terbaca jelas sesuai revisi reviewer | Memastikan isi setiap poin (a–d) sesuai temuan inspeksi data, bukan hanya parafrase saran AI; validasi `src.validasi.katalog` lolos 0 masalah sebelum commit |
| 2026-11-26 | 124450089 | Antigravity | Penelusuran rekonsiliasi dinamis (Tahap 6 Revisi) | Menghilangkan seluruh nilai numerik statis/hardcode dari skrip, menggantinya dengan ekstraksi dinamis dari tabel nasional Gold (`df_nat`) dan audit daerah (`df_kab`), serta membangun aturan evaluasi kondisional runtime agar kategori otomatis bereaksi mengikuti data saat pipeline dijalankan ulang. |
| 2026-11-26 | 124450031 | OpenCode + DeepSeek V4.1 Flash (gratis) | Merapikan repo: hapus berkas eksplorasi dan duplikat pembaca JSON (PR #41), lengkapi tautan kartu #24 dan #30 | Daftar berkas yang dihapus dipilih sendiri, file yang masih dipakai validasi dipertahankan |
