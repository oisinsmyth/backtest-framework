import json, time, urllib.request, urllib.parse, sys, io, gzip, re, random, html
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
UA = "Backtest-Framework-Research research@backtest-framework.org"
FTS = "https://efts.sec.gov/LATEST/search-index"
S, E = "2021-01-01", "2021-01-31"

def get(url, tries=4):
    for i in range(tries):
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip, deflate"})
        try:
            r = urllib.request.urlopen(req, timeout=90); raw = r.read(); hd = dict(r.headers); code = r.status
        except urllib.error.HTTPError as e:
            raw = e.read(); hd = dict(e.headers); code = e.code
            if code not in (404, 403): time.sleep(1.2); continue
        except Exception:
            time.sleep(1.5); continue
        ce = (hd.get("Content-Encoding") or "").lower()
        if "gzip" in ce or raw[:2] == b"\x1f\x8b":
            try: raw = gzip.decompress(raw)
            except Exception: pass
        time.sleep(0.4)
        return code, raw
    return "FAIL", b""

def fts_all(q, maxpages=40):
    ids, total = [], None
    for page in range(maxpages):
        p = {"q": q, "forms": "8-K", "dateRange": "custom", "startdt": S, "enddt": E, "from": str(page*100)}
        c, b = get(FTS + "?" + urllib.parse.urlencode(p))
        j = json.loads(b)
        if total is None: total = j["hits"]["total"]
        h = j["hits"]["hits"]
        for x in h:
            ids.append((x["_id"], x["_source"]["form"], x["_source"]["ciks"][0].lstrip("0")))
        if len(h) < 100: break
    return total, ids

PHRASES = ['"declared a quarterly dividend"', '"declared a cash dividend"', '"quarterly cash dividend"',
           '"declared a dividend"', '"dividend declaration"', '"declares quarterly"',
           '"board of directors declared"', '"declared a regular"']
UNION = " OR ".join(PHRASES)

tot_m, ids_m = fts_all("dividend")
print(f"MENTIONS  q=dividend           total={tot_m} collected={len(ids_m)}")
tot_p, ids_p = fts_all(UNION)
print(f"PHRASEFAM q=OR of 8 phrases    total={tot_p} collected={len(ids_p)}")
tot_z, ids_z = fts_all('"zzqxvnqq impossible"')
print(f"ZERO CTRL                      total={tot_z} collected={len(ids_z)}")

acc_m = {i.split(":")[0] for i, f, c in ids_m}
acc_p = {i.split(":")[0] for i, f, c in ids_p}
print(f"\nfilings mentioning 'dividend' = {len(acc_m)}; caught by phrase family = {len(acc_p & acc_m)}; "
      f"phrase-family filings not in mention set = {len(acc_p - acc_m)}")
print(f"UPPER-BOUND RECALL of phrase family vs any-mention set = {len(acc_p & acc_m)/len(acc_m):.3f}")

misses = sorted(acc_m - acc_p)
random.seed(7)
samp = random.sample(misses, min(14, len(misses)))
cikmap = {i.split(":")[0]: (c, i.split(":", 1)[1]) for i, f, c in ids_m}
print(f"\n--- {len(misses)} missed filings; inspecting {len(samp)} at random (seed 7) ---")
for a in samp:
    cik, fn = cikmap[a]
    nod = a.replace("-", "")
    c, b = get(f"https://www.sec.gov/Archives/edgar/data/{cik}/{nod}/{fn}")
    t = re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>', ' ', b.decode("utf-8", "replace"))
    t = html.unescape(re.sub(r'(?s)<[^>]+>', ' ', t))
    t = re.sub(r'\s+', ' ', t)
    wins = []
    for m in re.finditer(r'dividend', t, re.I):
        wins.append(t[max(0, m.start()-170): m.end()+210])
        if len(wins) >= 2: break
    print(f"\n* {a} cik={cik} {fn} HTTP={c} len={len(b)}")
    for w in wins: print(f"    >> {w}")
    sys.stdout.flush()
