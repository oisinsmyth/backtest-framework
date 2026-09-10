"""C4 [MEASURED IN BRIEF] -- post-publication decay of the profitability spread BY SIZE QUINTILE,
on Ken French's 25 Portfolios Formed on Size and Operating Profitability.

Independent of Chen-Zimmermann: a different construction (FF's OP = (sales - COGS - SG&A -
interest expense) / book equity, NYSE breakpoints, June rebalance, utilities and financials
INCLUDED), a different vendor, and data through 2026-07. FF's OP is R2-02's FOURTH definition,
not gross profitability -- it is a triangulation, not a replication.

Within each size quintile the five OP portfolios are an equal-count partition of that size row,
so the row mean is that row's own universe and LONG - row mean is the within-size long-leg alpha.
"""
import json, math, os, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
Z = "C4_25_Portfolios_ME_OP_5x5_CSV.zip"
MISSING = (-99.99, -999.0)


def tstat(xs):
    n = len(xs)
    if n < 3:
        return None, None, n
    m = sum(xs) / n
    v = sum((x - m) ** 2 for x in xs) / (n - 1)
    se = math.sqrt(v / n)
    return m, (m / se if se else None), n


def blocks(path):
    txt = zipfile.ZipFile(os.path.join(HERE, path)).read(
        zipfile.ZipFile(os.path.join(HERE, path)).namelist()[0]).decode("latin-1").splitlines()
    out, cur, hdr = {}, None, None
    for line in txt:
        s = line.strip()
        if s.startswith(",SMALL LoOP"):
            hdr = [c.strip() for c in s.split(",")[1:]]
            continue
        if s and not s[0].isdigit():
            cur = s
            continue
        if not s or hdr is None:
            continue
        p = [c.strip() for c in s.split(",") if c.strip() != ""]
        if len(p) != len(hdr) + 1 or len(p[0]) != 6:
            continue          # skips the annual blocks, whose date key is 4 digits
        ym = p[0][:4] + "-" + p[0][4:]
        vals = [float(x) for x in p[1:]]
        out.setdefault(cur, {})[ym] = dict(zip(hdr, vals))
    return out, hdr


bl, hdr = blocks(Z)
OUT = {"blocks_found": list(bl.keys()), "n_columns": len(hdr), "columns": hdr}

WINDOWS = [("pre_publication_1963_07_2013_06", "1963-07", "2013-06"),
           ("post_publication_2013_07_2026_07", "2013-07", "2026-07"),
           ("in_sample_era_1963_07_2010_12", "1963-07", "2010-12"),
           ("programme_window_2010_01_2026_07", "2010-01", "2026-07"),
           ("last_five_2021_07_2026_07", "2021-07", "2026-07")]

# the five OP columns inside each size quintile, in the file's own naming
ROWS = {
    "ME1_SMALL": ["SMALL LoOP", "ME1 OP2", "ME1 OP3", "ME1 OP4", "SMALL HiOP"],
    "ME2": ["ME2 OP1", "ME2 OP2", "ME2 OP3", "ME2 OP4", "ME2 OP5"],
    "ME3": ["ME3 OP1", "ME3 OP2", "ME3 OP3", "ME3 OP4", "ME3 OP5"],
    "ME4": ["ME4 OP1", "ME4 OP2", "ME4 OP3", "ME4 OP4", "ME4 OP5"],
    "ME5_BIG": ["BIG LoOP", "ME5 OP2", "ME5 OP3", "ME5 OP4", "BIG HiOP"],
}

ctrl = {}
for wname in ("Average Value Weighted Returns -- Monthly", "Average Equal Weighted Returns -- Monthly"):
    assert wname in bl, sorted(bl)
    ctrl[wname + " :: n_months"] = len(bl[wname])
    ctrl[wname + " :: first"] = min(bl[wname])
    ctrl[wname + " :: last"] = max(bl[wname])
    ctrl[wname + " :: missing_code_cells"] = sum(
        1 for d in bl[wname].values() for v in d.values() if v in MISSING)
# negative controls
ctrl["C10_months_before_1963_07"] = sum(1 for k in bl["Average Value Weighted Returns -- Monthly"] if k < "1963-07")
ctrl["C11_bogus_column_present"] = "ME9 OP9" in hdr
nf = bl.get("Number of Firms in Portfolios", {})
ctrl["C12_number_of_firms_block_months"] = len(nf)

res = {}
for wlabel, wname in [("VW", "Average Value Weighted Returns -- Monthly"),
                      ("EW", "Average Equal Weighted Returns -- Monthly")]:
    d = bl[wname]
    res[wlabel] = {}
    for rname, cols in ROWS.items():
        blk = {}
        for nm, lo, hi in WINDOWS:
            ms = [k for k in sorted(d) if lo <= k <= hi
                  and all(d[k][c] not in MISSING for c in cols)]
            if len(ms) < 12:
                continue
            uni = {k: sum(d[k][c] for c in cols) / 5.0 for k in ms}
            hi_lo = [d[k][cols[-1]] - d[k][cols[0]] for k in ms]
            lng = [d[k][cols[-1]] - uni[k] for k in ms]
            sht = [d[k][cols[0]] - uni[k] for k in ms]
            m1, t1, n1 = tstat(hi_lo); m2, t2, _ = tstat(lng); m3, t3, _ = tstat(sht)
            # names per cell, from the Number of Firms block
            nn = [nf[k][cols[-1]] for k in ms if k in nf and nf[k][cols[-1]] not in MISSING]
            blk[nm] = {"HiOP_minus_LoOP": round(m1, 4), "t": round(t1, 2),
                       "LONG_minus_row_universe": round(m2, 4), "t_long": round(t2, 2),
                       "SHORT_minus_row_universe": round(m3, 4), "t_short": round(t3, 2),
                       "n_months": n1,
                       "avg_firms_in_HiOP_cell": round(sum(nn) / len(nn), 1) if nn else None}
        # negative control inside the row: deviations from the row mean must sum to zero
        ms = [k for k in sorted(d) if all(d[k][c] not in MISSING for c in cols)]
        uni = {k: sum(d[k][c] for c in cols) / 5.0 for k in ms}
        blk["C13_sum_of_row_deviations_max_abs"] = max(
            abs(sum(d[k][c] - uni[k] for c in cols)) for k in ms)
        res[wlabel][rname] = blk

OUT["by_size_quintile"] = res
OUT["controls"] = ctrl
print(json.dumps(OUT, indent=1))
json.dump(OUT, open(os.path.join(HERE, "C4_french_size_op.json"), "w"), indent=1)
