"""D2 [MEASURED IN BRIEF] step 1: build a firm x fiscal-quarter panel of the FOUR
inputs a profitability sort needs, from SEC Financial Statement Data Sets.

Endpoint: https://www.sec.gov/files/dera/data/financial-statement-data-sets/<q>.zip
Quarters: 2021q4 .. 2024q4 (13 zips, 1,465,690,535 bytes, sha1s in D2_fsds_download.log)

CORRECTNESS POINTS, each one checked rather than assumed:
  * `segments` MUST be empty -- otherwise a row can be a SEGMENT disaggregation
    (revenue by business unit), not the consolidated figure.
  * `coreg` MUST be empty -- otherwise it is a co-registrant's figure.
  * uom MUST be USD.
  * flows are qtrs='1' (a ~3-month duration); Assets is qtrs='0' (an instant).
  * `prevrpt` is a HINDSIGHT column (it flags that a submission was SUBSEQUENTLY
    amended) so it is RECORDED, never used to filter.

GIL-bound pure-Python text scanning over ~5.8 GB, so PROCESSES not threads
(CLAUDE.md). One process per zip, strided over the worker pool.

NEGATIVE CONTROLS built into the harvest:
  (1) a tag that cannot exist must yield 0 rows;
  (2) `Assets` with qtrs='1' must be ~0 rows, because Assets is an instant, not a
      flow -- if the parser is mixing duration and instant rows this WILL fire.
"""
import zipfile, glob, os, csv, sys, time
from multiprocessing import Pool

REV = ("Revenues", "SalesRevenueNet", "SalesRevenueGoodsNet",
       "RevenueFromContractWithCustomerExcludingAssessedTax",
       "RevenueFromContractWithCustomerIncludingAssessedTax")
COST = ("CostOfGoodsSold", "CostOfGoodsAndServicesSold", "CostOfRevenue")
SGA = ("SellingGeneralAndAdministrativeExpense",
       "GeneralAndAdministrativeExpense")
INST = ("Assets",)
CONTROL = ("ZZZZNotATagD2Control",)
WANT = set(REV + COST + SGA + INST + CONTROL)
# cheap byte prefilter so we do not split 3M lines per file
PREFIX = tuple(t.encode() for t in WANT)


def one(zpath):
    t0 = time.time()
    sub = {}
    z = zipfile.ZipFile(zpath)
    with z.open("sub.txt") as f:
        hdr = f.readline().decode("utf-8", "replace").rstrip("\r\n").split("\t")
        ix = {c: i for i, c in enumerate(hdr)}
        for raw in f:
            p = raw.decode("utf-8", "replace").rstrip("\r\n").split("\t")
            if len(p) < len(hdr):
                continue
            sub[p[ix["adsh"]]] = (p[ix["cik"]], p[ix["sic"]], p[ix["fye"]],
                                  p[ix["form"]], p[ix["period"]], p[ix["fp"]],
                                  p[ix["filed"]], p[ix["prevrpt"]], p[ix["detail"]])
    out = []
    nctrl = 0
    nassets_q1 = 0
    nlines = 0
    with z.open("num.txt") as f:
        hdr = f.readline().decode("utf-8", "replace").rstrip("\r\n").split("\t")
        jx = {c: i for i, c in enumerate(hdr)}
        JT, JD, JQ, JU, JS, JC, JV, JA = (jx["tag"], jx["ddate"], jx["qtrs"],
                                          jx["uom"], jx["segments"], jx["coreg"],
                                          jx["value"], jx["adsh"])
        for raw in f:
            nlines += 1
            if not raw.startswith(PREFIX, raw.find(b"\t") + 1):
                continue
            p = raw.decode("utf-8", "replace").rstrip("\r\n").split("\t")
            if len(p) <= JV:
                continue
            tag = p[JT]
            if tag not in WANT:
                continue
            if tag in CONTROL:
                nctrl += 1
                continue
            if p[JS] != "" or p[JC] != "" or p[JU] != "USD":
                continue
            q = p[JQ]
            if tag in INST:
                if q == "1":
                    nassets_q1 += 1
                if q != "0":
                    continue
            else:
                # keep 1 (a quarter), 3 (nine-month YTD) and 4 (full year) so that
                # FISCAL Q4 can be DERIVED as annual - nine-month YTD. A single
                # fiscal Q4 is rarely tagged on its own in a 10-K, so requiring a
                # native qtrs=1 Q4 row silently selects a strange subsample.
                if q not in ("1", "2", "3", "4"):
                    continue
            s = sub.get(p[JA])
            if s is None or s[3] not in ("10-Q", "10-K"):
                continue
            v = p[JV]
            if v == "":
                continue
            out.append((s[0], tag, p[JD], q, v, s[1], s[2], s[3], s[4], s[5],
                        s[6], s[7]))
    dest = zpath.replace(".zip", "_panel.csv")
    with open(dest, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["cik", "tag", "ddate", "qtrs", "value", "sic", "fye", "form",
                    "period", "fp", "filed", "prevrpt"])
        w.writerows(out)
    return (os.path.basename(zpath), len(sub), nlines, len(out), nctrl,
            nassets_q1, round(time.time() - t0, 1))


if __name__ == "__main__":
    zs = sorted(glob.glob("D2_fsds_*.zip"))
    t0 = time.time()
    with Pool(min(8, len(zs))) as pool:
        res = pool.map(one, zs)
    print(f"{'zip':<22}{'subs':>8}{'numlines':>11}{'kept':>9}"
          f"{'CTRLtag':>9}{'Assets@q1':>11}{'sec':>7}")
    tot = ctrl = aq1 = 0
    for r in res:
        print(f"{r[0]:<22}{r[1]:>8,}{r[2]:>11,}{r[3]:>9,}{r[4]:>9}{r[5]:>11}{r[6]:>7}")
        tot += r[3]; ctrl += r[4]; aq1 += r[5]
    print(f"\nTOTAL kept rows: {tot:,}   wall {time.time()-t0:.1f}s"
          f"  (sum item time {sum(r[6] for r in res):.0f}s)")
    print(f"NEGATIVE CONTROL 1 -- impossible tag rows: {ctrl}  <-- MUST BE 0")
    print(f"NEGATIVE CONTROL 2 -- `Assets` with qtrs=1: {aq1}  "
          f"<-- must be ~0; Assets is an INSTANT, not a flow")
