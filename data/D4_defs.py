"""D4 shared definitions: the series under test and the windows. Imported by
D4_analyze.py and D4_analyze2.py so both measure THE SAME objects. Importing this
module re-runs every control in D4_run.py first, by design."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from D4_run import *   # noqa  -- controls, loaded blocks, cols_*, ff5, ff3, HERE, CTRL, LOG

DEC = ["Lo 10", "2-Dec", "3-Dec", "4-Dec", "5-Dec", "6-Dec", "7-Dec", "8-Dec", "9-Dec", "Hi 10"]
MKT = {m: ff5[m]["Mkt-RF"] + ff5[m]["RF"] for m in ff5
       if ff5[m]["Mkt-RF"] is not None and ff5[m]["RF"] is not None}
iop = {c: j for j, c in enumerate(cols_vw)}
iope = {c: j for j, c in enumerate(cols_ew)}
ibm = {c: j for j, c in enumerate(cols_bm)}
inf = {c: j for j, c in enumerate(cols_nf)}


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
