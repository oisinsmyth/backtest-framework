import json, time, urllib.request, urllib.parse, sys, gzip, re, collections, pathlib

UA = "Backtest-Framework-Research research@backtest-framework.org"

def get(url, tries=3):
    for i in range(tries):
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip, deflate"})
        try:
            r = urllib.request.urlopen(req, timeout=90)
            raw = r.read()
            if r.headers.get("Content-Encoding") == "gzip": raw = gzip.decompress(raw)
            time.sleep(0.4)
            return r.status, raw
        except urllib.error.HTTPError as e:
            body = e.read(); code = e.code
            time.sleep(0.6)
            if code in (403, 404): return code, body
        except Exception:
            time.sleep(1.0)
    return "FAIL", b""

# Absolute, so a deliberate run writes beside this script instead of into whatever
# directory the process happened to start in.
OUT = pathlib.Path(__file__).resolve().parent / "A4_header_rows.json"

# Nothing below runs on IMPORT. pytest imports any file named on its command line,
# whatever python_files says (it is an initial path), and this module fetches from SEC and
# writes its output -- so collecting it used to do both. D546.
if __name__ == "__main__":
    # ---------- PART 1: FTS hit -> filing dedupe ratio ----------
    BASE = "https://efts.sec.gov/LATEST/search-index"
    p = {"q": '"declared a quarterly dividend"', "forms": "8-K",
         "dateRange": "custom", "startdt": "2021-01-01", "enddt": "2021-01-31"}
    code, raw = get(BASE + "?" + urllib.parse.urlencode(p))
    j = json.loads(raw); hits = j["hits"]["hits"]
    acc = [h["_id"].split(":")[0] for h in hits]
    print(f"PART1 FTS hits={len(hits)} (total={j['hits']['total']}) unique accessions={len(set(acc))} "
          f"ratio={len(set(acc))/len(hits):.3f}")
    dupes = {k: v for k, v in collections.Counter(acc).items() if v > 1}
    print(f"  accessions with >1 indexed document matching: {len(dupes)}; max per accession={max(collections.Counter(acc).values())}")

    # ---------- PART 2: hdr.sgml vs -index-headers.html vs submissions JSON acceptance ----------
    # pick 2 filings per era from FTS so they are real
    def sample(y):
        pp = {"q": '"declared a quarterly dividend"', "forms": "8-K", "dateRange": "custom",
              "startdt": f"{y}-01-01", "enddt": f"{y}-03-31"}
        c, r = get(BASE + "?" + urllib.parse.urlencode(pp))
        jj = json.loads(r)
        out = []
        seen = set()
        for h in jj["hits"]["hits"]:
            a = h["_id"].split(":")[0]
            if a in seen: continue
            seen.add(a)
            out.append((a, h["_source"]["ciks"][0].lstrip("0"), h["_source"]["file_date"]))
            if len(out) >= 3: break
        return out

    print("\nPART2  acc | hdr.sgml | index-headers.html | ACCEPTANCE-DATETIME | FILING-DATE | items in header")
    rows = []
    for y in [2010, 2012, 2014, 2018, 2022, 2025]:
        for adsh, cik, fd in sample(y):
            nod = adsh.replace("-", "")
            u_hdr = f"https://www.sec.gov/Archives/edgar/data/{cik}/{nod}/{adsh}.hdr.sgml"
            u_ih  = f"https://www.sec.gov/Archives/edgar/data/{cik}/{nod}/{adsh}-index-headers.html"
            c1, b1 = get(u_hdr)
            c2, b2 = get(u_ih)
            txt = b1.decode("utf-8", "replace")
            accd = re.search(r"<ACCEPTANCE-DATETIME>(\d+)", txt)
            fdt  = re.search(r"<FILING-DATE>(\d+)", txt)
            items = re.findall(r"<ITEM-INFORMATION>([^\n<]*)", txt)
            print(f"{y} {adsh} hdr={c1}/{len(b1)}B  idxhdr={c2}/{len(b2)}B  acc={accd.group(1) if accd else None} "
                  f"fdate={fdt.group(1) if fdt else None} items={items}")
            rows.append({"y": y, "adsh": adsh, "cik": cik, "file_date": fd,
                         "hdr_code": c1, "idxhdr_code": c2,
                         "acceptance": accd.group(1) if accd else None,
                         "hdr_filing_date": fdt.group(1) if fdt else None, "items": items})
            sys.stdout.flush()

    # ---------- PART 3: submissions JSON acceptanceDateTime vs hdr.sgml ----------
    print("\nPART3 submissions-JSON acceptanceDateTime vs SGML header ACCEPTANCE-DATETIME")
    by_cik = {}
    for r in rows: by_cik.setdefault(r["cik"], []).append(r)
    mism = 0; tot = 0
    for cik, rs in by_cik.items():
        c, b = get(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json")
        try:
            js = json.loads(b)
        except Exception:
            print(f"  CIK{cik} submissions HTTP={c} bytes={len(b)} UNPARSEABLE"); continue
        rec = js.get("filings", {}).get("recent", {})
        accs = rec.get("accessionNumber", []); adt = rec.get("acceptanceDateTime", [])
        m = dict(zip(accs, adt))
        for r in rs:
            tot += 1
            jsonv = m.get(r["adsh"], "NOT-IN-RECENT")
            hdrv = r["acceptance"]
            hdr_fmt = None
            if hdrv and len(hdrv) == 14:
                hdr_fmt = f"{hdrv[0:4]}-{hdrv[4:6]}-{hdrv[6:8]}T{hdrv[8:10]}:{hdrv[10:12]}:{hdrv[12:14]}"
            agree = (jsonv.rstrip("Z") == hdr_fmt) if isinstance(jsonv, str) and hdr_fmt else None
            if agree is False: mism += 1
            print(f"  {r['adsh']} json={jsonv} hdr={hdr_fmt} same_wallclock={agree}")
    print(f"  compared={tot} differing_wallclock={mism}")
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=1)
