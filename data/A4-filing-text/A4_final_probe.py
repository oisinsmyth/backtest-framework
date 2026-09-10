import json, time, urllib.request, urllib.parse, sys, io, gzip, re, statistics, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
UA = "Backtest-Framework-Research research@backtest-framework.org"
FTS = "https://efts.sec.gov/LATEST/search-index"

def get(url, tries=3):
    for i in range(tries):
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip, deflate"})
        try:
            r = urllib.request.urlopen(req, timeout=90)
            raw = r.read(); hd = dict(r.headers); code = r.status
        except urllib.error.HTTPError as e:
            raw = e.read(); hd = dict(e.headers); code = e.code
            if code not in (404, 403): time.sleep(1.0); continue
        except Exception:
            time.sleep(1.2); continue
        ce = (hd.get("Content-Encoding") or "").lower()
        if "gzip" in ce or raw[:2] == b"\x1f\x8b":
            try: raw = gzip.decompress(raw)
            except Exception: pass
        time.sleep(0.4)
        return code, raw
    return "FAIL", b""

def fts(p):
    c, b = get(FTS + "?" + urllib.parse.urlencode(p))
    return json.loads(b)

def sample(y, n=3):
    j = fts({"q": '"declared a quarterly dividend"', "forms": "8-K", "dateRange": "custom",
             "startdt": f"{y}-01-01", "enddt": f"{y}-06-30"})
    out, seen = [], set()
    for h in j["hits"]["hits"]:
        a = h["_id"].split(":")[0]
        if a in seen: continue
        seen.add(a); out.append((a, h["_source"]["ciks"][0].lstrip("0")))
        if len(out) >= n: break
    return out

# ---- (a) narrow the -index-headers.html era boundary; (b)(c) hdr.sgml items + sizes ----
print("year  n  hdr.sgml 200s  idxhdr 200s  hdr bytes(min/med/max)  item-codes parsed")
hdr_sizes = []
for y in range(2010, 2027):
    rows = sample(y, 3)
    h200 = i200 = 0; sizes = []; itemsets = []
    for adsh, cik in rows:
        nod = adsh.replace("-", "")
        c1, b1 = get(f"https://www.sec.gov/Archives/edgar/data/{cik}/{nod}/{adsh}.hdr.sgml")
        c2, b2 = get(f"https://www.sec.gov/Archives/edgar/data/{cik}/{nod}/{adsh}-index-headers.html")
        if c1 == 200: h200 += 1; sizes.append(len(b1)); hdr_sizes.append(len(b1))
        if c2 == 200: i200 += 1
        t = b1.decode("utf-8", "replace")
        itemsets.append(re.findall(r"<ITEMS>([^\s<]+)", t))
    med = int(statistics.median(sizes)) if sizes else None
    print(f"{y}  {len(rows)}   hdr={h200}/{len(rows)}     idxhdr={i200}/{len(rows)}    "
          f"{min(sizes) if sizes else '-'}/{med}/{max(sizes) if sizes else '-'}   {itemsets}")
    sys.stdout.flush()

print(f"\nhdr.sgml size n={len(hdr_sizes)} mean={statistics.mean(hdr_sizes):.0f}B median={statistics.median(hdr_sizes):.0f}B max={max(hdr_sizes)}B")

# ---- (d) amendments: does forms=8-K match 8-K/A? ----
print("\n--- amendments ---")
for f in ["8-K", "8-K/A"]:
    j = fts({"q": '"declared a quarterly dividend"', "forms": f, "dateRange": "custom",
             "startdt": "2015-01-01", "enddt": "2015-12-31"})
    forms = collections.Counter(h["_source"]["form"] for h in j["hits"]["hits"])
    roots = collections.Counter(tuple(h["_source"]["root_forms"]) for h in j["hits"]["hits"])
    print(f"forms={f:6s} total={j['hits']['total']} forms_in_page={dict(forms)} roots={dict(roots)}")

# how many 8-K/A in window at all (no q filter impossible; use a near-universal token)
for f in ["8-K", "8-K/A"]:
    j = fts({"q": 'the', "forms": f, "dateRange": "custom", "startdt": "2024-01-01", "enddt": "2024-01-31"})
    print(f"q=the forms={f:6s} Jan-2024 total={j['hits']['total']}")
j = fts({"q": 'the', "forms": "ZZ-NOTAFORM", "dateRange": "custom", "startdt": "2024-01-01", "enddt": "2024-01-31"})
print(f"q=the forms=ZZ-NOTAFORM CONTROL total={j['hits']['total']}")

# ---- (e) does FTS index PDF/image-only exhibits? check a filing whose ex99 is a PDF ----
print("\n--- daily index vs full index row counts for one date (PAC deletions) ---")
for u in ["https://www.sec.gov/Archives/edgar/daily-index/2021/QTR1/master.20210104.idx"]:
    c, b = get(u)
    lines = [l for l in b.decode("latin-1").splitlines() if l.count("|") == 4]
    forms = collections.Counter(l.split("|")[2] for l in lines)
    print(f"  daily master.20210104.idx HTTP={c} rows={len(lines)} 8-K={forms.get('8-K')} 8-K/A={forms.get('8-K/A')}")
