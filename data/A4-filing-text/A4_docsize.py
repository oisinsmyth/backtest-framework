import json, time, urllib.request, urllib.parse, sys, gzip, statistics

UA = "Backtest-Framework-Research research@backtest-framework.org"

def fetch(url, extra=None, method="GET"):
    h = {"User-Agent": UA, "Accept-Encoding": "gzip, deflate"}
    if extra: h.update(extra)
    req = urllib.request.Request(url, headers=h, method=method)
    try:
        r = urllib.request.urlopen(req, timeout=90)
        raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        time.sleep(0.4)
        return r.status, raw, dict(r.headers)
    except urllib.error.HTTPError as e:
        time.sleep(0.4); return e.code, e.read(), dict(e.headers)

# ---- TEST 1: does SEC honour Range on Archives? ----
u = "https://www.sec.gov/Archives/edgar/full-index/2021/QTR1/master.idx"
code, raw, hdrs = fetch(u, {"Range": "bytes=0-999", "Accept-Encoding": "identity"})
print(f"RANGE TEST master.idx: HTTP={code} got_bytes={len(raw)} CR={hdrs.get('Content-Range')} CL={hdrs.get('Content-Length')}")

u2 = "https://www.sec.gov/Archives/edgar/Feed/2010/QTR1/20100104.nc.tar.gz"
code, raw, hdrs = fetch(u2, {"Range": "bytes=0-4095", "Accept-Encoding": "identity"})
print(f"RANGE TEST feed tar.gz: HTTP={code} got_bytes={len(raw)} CR={hdrs.get('Content-Range')}")

# ---- TEST 2: FTS -> actual document byte sizes for a dividend phrase in 8-K ----
BASE = "https://efts.sec.gov/LATEST/search-index"
p = {"q": '"declared a quarterly dividend"', "forms": "8-K",
     "dateRange": "custom", "startdt": "2021-01-01", "enddt": "2021-01-31"}
code, raw, _ = fetch(BASE + "?" + urllib.parse.urlencode(p))
j = json.loads(raw)
hits = j["hits"]["hits"]
print(f"\nFTS hits for Jan-2021: total={j['hits']['total']} returned={len(hits)}")

doc_sizes = []; sub_sizes = []
for h in hits[:12]:
    adsh, fn = h["_id"].split(":", 1)
    cik = h["_source"]["ciks"][0].lstrip("0")
    nod = adsh.replace("-", "")
    durl = f"https://www.sec.gov/Archives/edgar/data/{cik}/{nod}/{fn}"
    c, b, _ = fetch(durl)
    surl = f"https://www.sec.gov/Archives/edgar/data/{cik}/{nod}/{adsh}.txt"
    c2, b2, _ = fetch(surl)
    doc_sizes.append(len(b)); sub_sizes.append(len(b2))
    print(f"{adsh} {fn:28s} doc HTTP={c} {len(b):>9,}B | full-submission HTTP={c2} {len(b2):>10,}B")
    sys.stdout.flush()

print(f"\nexhibit/doc  n={len(doc_sizes)} mean={statistics.mean(doc_sizes):,.0f}B median={statistics.median(doc_sizes):,.0f}B")
print(f"full submission .txt n={len(sub_sizes)} mean={statistics.mean(sub_sizes):,.0f}B median={statistics.median(sub_sizes):,.0f}B")
json.dump({"doc": doc_sizes, "sub": sub_sizes}, open("A4_docsize.json", "w"))
