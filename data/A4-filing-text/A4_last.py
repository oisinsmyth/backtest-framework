import json, time, urllib.request, urllib.parse, sys, io, gzip
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
UA = "Backtest-Framework-Research research@backtest-framework.org"
FTS = "https://efts.sec.gov/LATEST/search-index"

def raw_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip, deflate"})
    try:
        r = urllib.request.urlopen(req, timeout=90); b = r.read(); hd = dict(r.headers); c = r.status
    except urllib.error.HTTPError as e:
        b = e.read(); hd = dict(e.headers); c = e.code
    ce = (hd.get("Content-Encoding") or "").lower()
    if "gzip" in ce or b[:2] == b"\x1f\x8b":
        try: b = gzip.decompress(b)
        except Exception: pass
    time.sleep(0.45)
    return c, b

def n(q, **kw):
    p = {"q": q, "forms": "8-K", "dateRange": "custom", "startdt": "2021-01-01", "enddt": "2021-01-31"}
    p.update(kw)
    c, b = raw_get(FTS + "?" + urllib.parse.urlencode(p))
    try:
        j = json.loads(b); return c, j["hits"]["total"]
    except Exception:
        return c, b[:200]

print("--- stemming / tokenisation test (Jan-2021, forms=8-K) ---")
for q in ["dividend", "dividends", "dividend*", '"dividend"', "DIVIDEND", "zzqxvnqq"]:
    print(f"  q={q:14s} {n(q)}")

print("\n--- repeated identical query: is the count stable? (cache-replay control) ---")
for k in range(4):
    print(f"  try{k} {n('dividend')}")

print("\n--- what the transient efts error body says (hammer once unpaced) ---")
for k in range(3):
    c, b = raw_get(FTS + "?" + urllib.parse.urlencode({"q": "dividend", "forms": "8-K"}))
    print(f"  HTTP={c} bytes={len(b)} body_head={b[:180]!r}")

print("\n--- does FTS index a PDF exhibit? search text known to be in a PDF-only EX-99 ---")
c, b = raw_get(FTS + "?" + urllib.parse.urlencode({"q": '"dividend"', "forms": "8-K",
    "dateRange": "custom", "startdt": "2021-01-01", "enddt": "2021-01-05"}))
j = json.loads(b)
exts = {}
for h in j["hits"]["hits"]:
    fn = h["_id"].split(":", 1)[1]
    e = fn.rsplit(".", 1)[-1].lower()
    exts[e] = exts.get(e, 0) + 1
print(f"  indexed-document extensions among {len(j['hits']['hits'])} hits: {exts}")
