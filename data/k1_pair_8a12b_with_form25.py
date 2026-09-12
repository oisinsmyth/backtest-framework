"""K1 stage 2: pair 8-A12B (registration on the NEW exchange) with Form 25 /
25-NSE (removal from the OLD exchange) on the same CIK, which is the primary-
document signature of an exchange listing transfer.

Includes a PLACEBO pairing (CIKs shuffled) to measure how often the +-window
pairs two unrelated filings.
"""
import collections, csv, datetime as dt, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROWS = os.path.join(HERE, "K1_idx_rows.tsv")
WIN = 120  # days

import re
TAIL = re.compile(r"^(\d{4}-\d{2}-\d{2})\s+(\S+)\s*$")

def load():
    """The stage-1 harvest split the fixed-width line two chars early, so the
    'date' and 'file' columns together hold `line[86:]`.  Re-split them here."""
    out, bad = [], 0
    with open(ROWS, encoding="utf-8", newline="") as fh:
        rd = csv.DictReader(fh, delimiter="\t")
        for r in rd:
            joined = (r["date"] or "") + (r["file"] or "")
            m = TAIL.match(joined.strip().replace("\r", ""))
            if not m:
                bad += 1
                continue
            try:
                d = dt.date.fromisoformat(m.group(1))
            except Exception:
                bad += 1
                continue
            out.append((r["form"].strip(), r["company"].strip(),
                        r["cik"].strip(), d, m.group(2)))
    print(f"[load] parsed {len(out)} rows, {bad} unparseable")
    return out

rows = load()
byform = collections.Counter(r[0] for r in rows)
print("=== form types harvested (all years) ===")
for f, c in sorted(byform.items(), key=lambda kv: -kv[1]):
    print(f"  {f:16s} {c}")
print("NEGATIVE CONTROL rows for form ZZ-NOTAFORM:",
      byform.get("ZZ-NOTAFORM", 0), "(must be 0)")

A = collections.defaultdict(list)   # cik -> [(date, file, company)] for 8-A12B
R = collections.defaultdict(list)   # cik -> [(date, file, form, company)] for 25 / 25-NSE
for form, comp, cik, d, fn in rows:
    if form in ("8-A12B", "8-A12B/A"):
        A[cik].append((d, fn, comp, form))
    elif form in ("25", "25/A", "25-NSE", "25-NSE/A"):
        R[cik].append((d, fn, comp, form))

def pair(Amap, Rmap):
    hits = []
    for cik, alist in Amap.items():
        rlist = Rmap.get(cik)
        if not rlist:
            continue
        for ad, afn, comp, aform in alist:
            best = None
            for rd_, rfn, rform, _c in [(x[0], x[1], x[3], x[2]) for x in rlist]:
                gap = (rd_ - ad).days
                if abs(gap) <= WIN:
                    if best is None or abs(gap) < abs(best[0]):
                        best = (gap, rd_, rfn, rform)
            if best:
                hits.append(dict(cik=cik, company=comp, a_date=ad, a_file=afn,
                                 a_form=aform, gap=best[0], r_date=best[1],
                                 r_file=best[2], r_form=best[3]))
    return hits

hits = pair(A, R)
hits = [h for h in hits if 2009 <= h["a_date"].year <= 2026]
print(f"\n=== REAL pairing: {len(hits)} 8-A12B/Form-25 pairs within +-{WIN}d ===")
yr = collections.Counter(h["a_date"].year for h in hits)
for y in sorted(yr):
    print(f"  {y}: {yr[y]}")

# ---- PLACEBO: shuffle the CIK labels on the removal side ----
random.seed(7)
rkeys = list(R.keys())
shuf = rkeys[:]
random.shuffle(shuf)
Rp = {}
for k, v in zip(rkeys, shuf):
    Rp[k] = R[v]
ph = pair(A, Rp)
ph = [h for h in ph if 2009 <= h["a_date"].year <= 2026]
print(f"\n=== PLACEBO pairing (CIK labels shuffled): {len(ph)} pairs "
      f"({100.0*len(ph)/max(1,len(hits)):.1f}% of real) ===")

with open(os.path.join(HERE, "K1_pairs.tsv"), "w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(hits[0].keys()), delimiter="\t")
    w.writeheader()
    for h in sorted(hits, key=lambda x: x["a_date"]):
        w.writerow(h)
print("\nwrote K1_pairs.tsv")
