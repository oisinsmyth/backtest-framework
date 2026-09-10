"""D4 analysis: builds the series, runs every statistic with its nulls, writes D4_table.tsv.
Importing D4_run re-runs every control first, by design."""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from D4_run import *   # noqa  -- controls, loaded blocks, LOG, CTRL


def mkt_tot(ff):
    return {m: ff[m]["Mkt-RF"] + ff[m]["RF"] for m in ff
            if ff[m]["Mkt-RF"] is not None and ff[m]["RF"] is not None}


MKT = mkt_tot(ff5)
iop = {c: j for j, c in enumerate(cols_vw)}
iope = {c: j for j, c in enumerate(cols_ew)}
ibm = {c: j for j, c in enumerate(cols_bm)}
DEC = ["Lo 10", "2-Dec", "3-Dec", "4-Dec", "5-Dec", "6-Dec", "7-Dec", "8-Dec", "9-Dec", "Hi 10"]


def dec(src, idx, col):
    return {m: v[idx[col]] for m, v in src.items() if v[idx[col]] is not None}


def univ(src, idx):
    """simple mean of the ten deciles = the equal-count universe of the sort"""
    out = {}
    for m, v in src.items():
        xs = [v[idx[c]] for c in DEC]
        if any(x is None for x in xs):
            continue
        out[m] = sum(xs) / 10.0
    return out


def sub(a, b):
    return {m: a[m] - b[m] for m in a if m in b}


SER = {
    # --- operating profitability, the LONG LEG, three benchmarks
    "OP Hi10 VW - VW market":       sub(dec(op_vw, iop, "Hi 10"), MKT),
    "OP Hi10 EW - EW own universe": sub(dec(op_ew, iope, "Hi 10"), univ(op_ew, iope)),
    "OP Hi10 VW - VW own universe": sub(dec(op_vw, iop, "Hi 10"), univ(op_vw, iop)),
    # --- the SPREAD, same sort, same months
    "OP Hi10-Lo10 VW spread":      sub(dec(op_vw, iop, "Hi 10"), dec(op_vw, iop, "Lo 10")),
    "OP Hi10-Lo10 EW spread":      sub(dec(op_ew, iope, "Hi 10"), dec(op_ew, iope, "Lo 10")),
    "RMW published 2x3 spread":    {m: ff5[m]["RMW"] for m in ff5 if ff5[m]["RMW"] is not None},
    # --- the SHORT LEG alone, for the decomposition
    "OP Lo10 VW - VW market":      sub(dec(op_vw, iop, "Lo 10"), MKT),
    # --- a second characteristic, for breadth
    "BM Hi10 VW - VW market":      sub(dec(bm_vw, ibm, "Hi 10"), MKT),
    "BM Hi10-Lo10 VW spread":      sub(dec(bm_vw, ibm, "Hi 10"), dec(bm_vw, ibm, "Lo 10")),
    "HML published 2x3 spread":    {m: ff5[m]["HML"] for m in ff5 if ff5[m]["HML"] is not None},
    # --- NEGATIVE CONTROLS: series nobody calls a concentrated characteristic premium
    "CTRL market excess Mkt-RF":   {m: ff5[m]["Mkt-RF"] for m in ff5 if ff5[m]["Mkt-RF"] is not None},
    "CTRL SMB":                    {m: ff5[m]["SMB"] for m in ff5 if ff5[m]["SMB"] is not None},
    "CTRL CMA":                    {m: ff5[m]["CMA"] for m in ff5 if ff5[m]["CMA"] is not None},
}

WINDOWS = {
    "post-pub 2014-01..2024-12":  ("2014-01", "2024-12"),
    "post-pub ext ..2026-07":     ("2014-01", "2026-07"),
    "in-sample 1963-07..2013-12": ("1963-07", "2013-12"),
    "full available":             ("1900-01", "2099-12"),
}

RES = {}
for lab, d in SER.items():
    RES[lab] = {}
    for wl, (a, b) in WINDOWS.items():
        months = sorted(m for m in d if a <= m <= b)
        if len(months) < 36:
            continue
        RES[lab][wl] = report(lab + " | " + wl, [d[m] for m in months], months)
    print("done", lab, file=sys.stderr)

json.dump(RES, open(os.path.join(HERE, "D4_series.json"), "w"), indent=1, default=str)

# ----------------------------------------- the t -> k_half map under pure iid normality
MAP = {}
for T in (132, 151, 606, 757):
    MAP[str(T)] = {}
    for t in (0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 7.0, 10.0):
        MAP[str(T)]["t=%.2f" % t] = null_k_half(t / math.sqrt(T), 1.0, T, 2000, 424242)
    print("map done T=", T, file=sys.stderr)
json.dump(MAP, open(os.path.join(HERE, "D4_t_to_khalf.json"), "w"), indent=1, default=str)

# ----------------------------------------- compact table
hdr = ["series", "window", "n", "mean", "median", "t", "sd", "skew", "exkurt", "pctpos",
       "k_half", "nullG_p50", "nullG_p05", "nullG_p95", "boot_p50", "top1sh", "top5sh",
       "exTop", "exBot", "trimBoth", "dropBest3", "dropWorst3",
       "best12mo_share", "clust_p", "rho1", "yrs_t2", "maxDDpct", "trough", "bestMo", "bestMoRet"]
rows = []
for lab in SER:
    for wl in WINDOWS:
        r = RES.get(lab, {}).get(wl)
        if not r:
            continue
        g = r.get("null_k_half_iid_gaussian_matched") or {}
        bs = r.get("null_k_half_iid_bootstrap") or {}
        cl = r.get("clustering_max_12mo_window") or {}

        def rd(x, n=4):
            return None if x is None else round(x, n)
        rows.append([lab, wl, r["n"], rd(r["mean"]), rd(r["median"]), rd(r["t"], 2), rd(r["sd"], 3),
                     rd(r["skew"], 2), rd(r["exkurt"], 2), rd(100 * r["frac_pos"], 1),
                     r["k_half"], g.get("p50"), g.get("p05"), g.get("p95"), bs.get("p50"),
                     rd(r["top1_share"], 3), rd(r["top5_share"], 3),
                     rd(r["trims_1pct"]["ex_top"]), rd(r["trims_1pct"]["ex_bottom"]),
                     rd(r["trims_1pct"]["trimmed_both"]),
                     rd(r["mirror"]["drop_best_3"]), rd(r["mirror"]["drop_worst_3"]),
                     rd(cl.get("observed"), 3), rd(cl.get("p_value"), 4),
                     rd(r["autocorr"]["rho1"], 3), rd(r["years_for_t2"], 1),
                     rd(100 * r["maxdd"], 1), r["maxdd_trough_month"],
                     r["best_month"][0], rd(r["best_month"][1], 2)])
with open(os.path.join(HERE, "D4_table.tsv"), "w") as f:
    f.write("\t".join(hdr) + "\n")
    for r in rows:
        f.write("\t".join("" if x is None else str(x) for x in r) + "\n")
print("rows written:", len(rows), file=sys.stderr)
