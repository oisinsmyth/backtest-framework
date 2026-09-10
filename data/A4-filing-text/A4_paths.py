import time, urllib.request, gzip, sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
UA = "Backtest-Framework-Research research@backtest-framework.org"

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip, deflate"})
    try:
        r = urllib.request.urlopen(req, timeout=90)
        raw = r.read(); hdrs = dict(r.headers); code = r.status
    except urllib.error.HTTPError as e:
        raw = e.read(); hdrs = dict(e.headers); code = e.code
    ce = (hdrs.get("Content-Encoding") or "").lower()
    if "gzip" in ce or raw[:2] == b"\x1f\x8b":
        try: raw = gzip.decompress(raw)
        except Exception: pass
    time.sleep(0.45)
    return code, raw

CASES = [
 ("59255",  "0000059255-10-000008"),
 ("1193125","0001193125-10-022203"),   # filer-agent CIK from accession prefix
 ("102037", "0000102037-14-000011"),
 ("883948", "0000883948-22-000010"),
]
print("cik/accession | ROOT .txt | DIR .txt | DIR hdr.sgml | ROOT -index.html | DIR -index-headers")
for cik, adsh in CASES:
    nod = adsh.replace("-", "")
    urls = {
      "root.txt":   f"https://www.sec.gov/Archives/edgar/data/{cik}/{adsh}.txt",
      "dir.txt":    f"https://www.sec.gov/Archives/edgar/data/{cik}/{nod}/{adsh}.txt",
      "dir.hdr":    f"https://www.sec.gov/Archives/edgar/data/{cik}/{nod}/{adsh}.hdr.sgml",
      "root.idx":   f"https://www.sec.gov/Archives/edgar/data/{cik}/{adsh}-index.html",
      "dir.idxhdr": f"https://www.sec.gov/Archives/edgar/data/{cik}/{nod}/{adsh}-index-headers.html",
    }
    out = []
    for k, u in urls.items():
        c, b = get(u)
        ok = b"<SEC-HEADER>" in b or b"ACCEPTANCE-DATETIME" in b or b"Acceptance" in b
        out.append(f"{k}={c}/{len(b)}{'/HDR' if ok else ''}")
    print(f"{cik:9s} {adsh}  " + "  ".join(out))
    sys.stdout.flush()

# Which CIK does the real issuer use? resolve via the accession's own submission index
print("\nResolve CIK for 0000059255-10-000008 via full-index row:")
c, b = get("https://www.sec.gov/Archives/edgar/data/59255/")
print(f"  dir listing for CIK 59255 HTTP={c} bytes={len(b)}")
