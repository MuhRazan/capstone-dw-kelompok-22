# AI_LOG — <Nama tim>

Satu baris per pemakaian AI yang bermakna (ChatGPT, Claude, Copilot, Bravais, dan sejenisnya).
Ringkas dan jujur; transkrip penuh tidak diminta. Yang dinilai bukan "pakai AI atau tidak",
melainkan "mengerti atau tidak" — isi kolom terakhir dengan apa yang Anda ubah dari keluarannya.

| Tanggal | Siapa (NIM) | Alat | Untuk apa | Apa yang diubah dari keluarannya |
|---|---|---|---|---|
| 2026-11-03 | 12345678 | Copilot | kerangka DataLoader | ganti normalisasi, tambah seed worker |
| 2026-11-25 | 124450128 | Antigravity (Gemini) | Tahap 6: identifikasi rincian pembanding EN.CLC.MDAT.ZS yang sebanding dengan seri utama BNPB, samakan bentuk periode, tulis K-043 di log-keputusan.csv | Cek langsung berkas mentah (kelompok-01-hal-01.json) dan metadata (sumber2_indikator.json); keputusan rincian & periode dikonfirmasi sendiri sebelum ditulis ke CSV |
| 2026-11-26 | 124450128 | Antigravity (Gemini) | Perbaiki K-043 agar tiga aspek (rincian dipakai, periode dipakai, alasan rincian tidak dipasangkan) tertulis eksplisit dan terbaca jelas sesuai revisi reviewer | Memastikan isi setiap poin (a–d) sesuai temuan inspeksi data, bukan hanya parafrase saran AI; validasi `src.validasi.katalog` lolos 0 masalah sebelum commit |
