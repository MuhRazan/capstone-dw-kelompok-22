import json, pathlib
akar = pathlib.Path("data/raw/wdi")
out = ["# DAFTAR BERKAS (jalur | bait)"]
berkas = sorted(p for p in akar.rglob("*") if p.is_file())
for p in berkas:
    out.append("%s | %d" % (p.relative_to("data/raw").as_posix(), p.stat().st_size))
out.append("")
out.append("# BENTUK TIAP JSON")
for p in berkas:
    if p.suffix.lower() != ".json":
        continue
    out.append("## " + p.relative_to("data/raw").as_posix())
    try:
        o = json.load(open(p, encoding="utf-8"))
    except Exception as e:
        out.append("  GALAT baca: %r" % (e,))
        continue
    out.append("  tipe: %s" % type(o).__name__)
    if isinstance(o, dict):
        for k, v in o.items():
            n = len(v) if hasattr(v, "__len__") else ""
            out.append("  kunci %r -> %s (len=%s) %s" % (k, type(v).__name__, n, repr(v)[:350]))
    elif isinstance(o, list):
        out.append("  len=%d" % len(o))
        for i, v in enumerate(o[:3]):
            n = len(v) if hasattr(v, "__len__") else ""
            out.append("  [%d] %s (len=%s) %s" % (i, type(v).__name__, n, repr(v)[:450]))
pathlib.Path("bentuk_wdi.txt").write_text("\n".join(out), encoding="utf-8")
print("selesai:", len(out), "baris")
