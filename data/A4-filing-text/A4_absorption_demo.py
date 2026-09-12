import json, time, urllib.request, urllib.parse, sys, io, gzip, re, collections, random
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
UA = "Backtest-Framework-Research research@backtest-framework.org"
FTS = "https://efts.sec.gov/LATEST/search-index"
S, E = "2021-01-01", "2021-01-31"

def get(url, tries=4):
    for i in range(tries):
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip, deflate"})
        try:
            r = urllib.request.urlopen(req, timeout=90); b = r.read(); hd = dict(r.headers); c = r.status
        except urllib.error.HTTPError as e:
            b = e.read(); hd = dict(e.headers); c = e.code
            if c not in (404, 403): time.sleep(1.2); continue
        except Exception:
            time.sleep(1.5); continue
        ce = (hd.get("Content-Encoding") or "").lower()
        if "gzip" in ce or b[:2] == b"\x1f\x8b":
            try: b = gzip.decompress(b)
            except Exception: pass
        time.sleep(0.38)
        return c, b
    return "FAIL", b""

PH = ['"declared a quarterly dividend"', '"declared a cash dividend"', '"quarterly cash dividend"',
      '"declared a dividend"', '"dividend declaration"', '"declares quarterly"',
      '"board of directors declared"', '"declared a regular"']
UNION = " OR ".join(PH)

rows = []
for page in range(20):
    p = {"q": UNION, "forms": "8-K", "dateRange": "custom", "startdt": S, "enddt": E, "from": str(page*100)}
    c, b = get(FTS + "?" + urllib.parse.urlencode(p))
    j = json.loads(b); h = j["hits"]["hits"]
    for x in h:
        adsh, fn = x["_id"].split(":", 1)
        rows.append((adsh, fn, x["_source"]["ciks"][0].lstrip("0"), x["_source"]["form"], x["_source"]["file_date"]))
    if len(h) < 100: break
print(f"phrase-family documents={len(rows)}; forms={dict(collections.Counter(r[3] for r in rows))}")

byacc = {}
for adsh, fn, cik, form, fd in rows:
    byacc.setdefault(adsh, {"cik": cik, "form": form, "fd": fd, "files": []})["files"].append(fn)
print(f"distinct filings={len(byacc)}")

hit = miss = 0
items_counter = collections.Counter()
has202 = has801 = has701 = 0
for adsh, v in byacc.items():
    nod = adsh.replace("-", "")
    c, b = get(f"https://www.sec.gov/Archives/edgar/data/{v['cik']}/{nod}/{adsh}.hdr.sgml")
    if c != 200:
        miss += 1; v["items"] = None; continue
    hit += 1
    it = re.findall(r"<ITEMS>([^\s<]+)", b.decode("utf-8", "replace"))
    v["items"] = it
    for x in it: items_counter[x] += 1
    subst = [x for x in it if x != "9.01"]
    if "2.02" in it: has202 += 1
    if "8.01" in it: has801 += 1
    if "7.01" in it: has701 += 1

print(f"\nhdr.sgml retrieved {hit}/{len(byacc)} (failed {miss})")
print(f"item incidence among the {hit} phrase-matched filings:")
for k, n in items_counter.most_common(14):
    print(f"   {k:6s} {n:5d}  {n/hit*100:5.1f}%")
print(f"\nITEM 2.02 (results of operations = earnings release) present: {has202}/{hit} = {has202/hit*100:.1f}%")
print(f"ITEM 8.01 present: {has801}/{hit} = {has801/hit*100:.1f}%")
print(f"ITEM 7.01 present: {has701}/{hit} = {has701/hit*100:.1f}%")
only901 = sum(1 for v in byacc.values() if v["items"] and set(v["items"]) <= {"9.01"})
print(f"filings whose only item is 9.01 (no substantive item): {only901}")

# does the matched DOCUMENT live in a filing that also carries 2.02? split by whether matched doc is the 8-K body
body = sum(1 for v in byacc.values() if v["items"] and any(re.search(r'8-?k', f, re.I) for f in v["files"]))
print(f"filings where a matched document filename looks like the 8-K body: {body}")

json.dump({k: v for k, v in byacc.items()}, open("A4_absorption_demo.json", "w"), indent=0)
