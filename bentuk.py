import json, pathlib
d = pathlib.Path("data/raw/bnpb/2026-10-20/datastore")
out = []
for uid in ["5dfcae7e", "69605ad2", "f345ba43"]:
    p = next(d.rglob(uid + "*.json"))
    o = json.load(open(p, encoding="utf-8"))
    out.append("## " + p.name + " | tipe: " + type(o).__name__)
    if isinstance(o, dict):
        for k, v in o.items():
            ukuran = len(v) if hasattr(v, "__len__") else ""
            out.append("  kunci %r -> %s (len=%s) %s" % (k, type(v).__name__, ukuran, repr(v)[:300]))
    else:
        out.append("  " + repr(o)[:600])
pathlib.Path("bentuk.txt").write_text("\n".join(out), encoding="utf-8")
print("selesai")
