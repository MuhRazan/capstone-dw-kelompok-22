import json, pathlib
akar = pathlib.Path("data/raw/bnpb/2026-10-20")
out = []

def jelajah(o, paket=""):
    if isinstance(o, dict):
        if isinstance(o.get("resources"), list):
            paket = o.get("name") or o.get("title") or paket
            out.append("## paket: %s | %s" % (o.get("name"), o.get("title")))
            for r in o["resources"]:
                out.append("  %s | %s | %s | ds=%s" % (r.get("id"), r.get("name"), r.get("format"), r.get("datastore_active")))
        for v in o.values():
            jelajah(v, paket)
    elif isinstance(o, list):
        for v in o:
            jelajah(v, paket)

for p in sorted((akar / "ckan").rglob("*.json")):
    out.append("# CKAN " + p.name)
    jelajah(json.load(open(p, encoding="utf-8")))

out.append("")
out.append("# DATASTORE: berkas | jumlah record | kolom")
for p in sorted((akar / "datastore").rglob("*.json")):
    try:
        o = json.load(open(p, encoding="utf-8"))
        rs = o["result"]["records"] if isinstance(o, dict) and "result" in o else (o.get("records") if isinstance(o, dict) else o)
        kol = list(rs[0].keys()) if rs else []
        out.append("%s/%s | %d | %s" % (p.parent.name, p.name[:8], len(rs), kol))
    except Exception as e:
        out.append("%s | GALAT %r" % (p.name, e))

pathlib.Path("peta_resource.txt").write_text("\n".join(out), encoding="utf-8")
print("selesai:", len(out), "baris")
