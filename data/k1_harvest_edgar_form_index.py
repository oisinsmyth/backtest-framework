"""K1: harvest EDGAR quarterly form indices 2009Q1-2026Q3, keep only the form
types that identify an exchange listing transfer.

Forms kept:
  25, 25/A          issuer-filed notification of removal from listing (voluntary)
  25-NSE, 25-NSE/A  exchange-filed notification of removal
  8-A12B, 8-A12B/A  registration of a class on a national exchange (the NEW exchange)
  8-A12G            registration under 12(g)
  CERT, CERTNYS, CERTNAS, CERTAMEX  exchange certification of approval for listing

Negative control: we also count a form type that MUST NOT EXIST ("ZZ-NOTAFORM").
"""
import gzip, io, os, sys, time, urllib.request

UA = "backtest-framework-research research@backtest-framework.org"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "K1_idx_rows.tsv")
KEEP_PREFIX = ("25", "8-A12B", "8-A12G", "CERT", "ZZ-NOTAFORM")

def quarters():
    for y in range(2009, 2027):
        for q in (1, 2, 3, 4):
            if y == 2026 and q > 3:
                continue
            yield y, q

rows = []
fails = []
for y, q in quarters():
    url = f"https://www.sec.gov/Archives/edgar/full-index/{y}/QTR{q}/form.gz"
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                              "Accept-Encoding": "gzip, deflate"})
    try:
        raw = urllib.request.urlopen(req, timeout=120).read()
    except Exception as e:
        fails.append((y, q, repr(e)))
        print(f"FAIL {y}Q{q} {e}", flush=True)
        continue
    try:
        txt = gzip.decompress(raw).decode("latin-1")
    except Exception:
        txt = raw.decode("latin-1")
    n = 0
    for line in txt.split("\n"):
        if len(line) < 100:
            continue
        form = line[0:12].strip()
        if not form.startswith(KEEP_PREFIX):
            continue
        # fixed-width: form 0:12, company 12:74, cik 74:86, date 86:98, file 98:
        company = line[12:74].strip()
        cik = line[74:86].strip()
        date = line[86:98].strip()
        fn = line[98:].strip()
        rows.append("\t".join([form, company, cik, date, fn, f"{y}Q{q}"]))
        n += 1
    print(f"{y}Q{q}: {len(txt)//1024}KB  kept {n}", flush=True)
    time.sleep(0.12)

with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("form\tcompany\tcik\tdate\tfile\tqtr\n")
    fh.write("\n".join(rows) + "\n")
print("TOTAL ROWS", len(rows))
print("FAILS", fails)
