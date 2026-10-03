"""D783 Stage 0: D775's fade on the other BLS releases at 08:30 ET (PPI primary).
Spec: docs/decisions/D783-STAGE-0-PRE-REG-fade-the-other-bls-0830-releases.md.

    python scripts/stage0_d783_bls_0830_fade.py --selftest
    python scripts/stage0_d783_bls_0830_fade.py --run

D775's `study` (construction, gates, nulls, audits) is imported unchanged; only the release-day dict differs, read from
D782's calendar (data/calendar/events_bls_0830.csv). CPI and Employment Situation sessions (D775's release_days) are
dropped from the bars before the panel is built. D775's loader keeps sessions before 2024-01-01 and raises otherwise.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d775_cpi_nfp_fade as S  # noqa: E402

SPEC = REPO / "docs" / "decisions" / "D783-STAGE-0-PRE-REG-fade-the-other-bls-0830-releases.md"
OUT = REPO / "data" / "stage0_d783_bls_0830_fade.json"
CAL = REPO / "data" / "calendar" / "events_bls_0830.csv"
CELLS = {"PPI": ("PPI",), "IMPEXP": ("IMPEXP",), "PROD": ("PROD_P", "PROD_R"), "ECI": ("ECI",),
         "ALL": ("PPI", "IMPEXP", "PROD_P", "PROD_R", "ECI")}
EXPECTED = {"PPI": 96, "IMPEXP": 96, "PROD": 64, "ECI": 32, "ALL": 288}
PRIMARY_CELL, PRIMARY_ROOT = "PPI", "NQ"
D775_KNOWN = (186, 34.88)


class D783Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D783Error(msg)


def load_cal(path: Path, events: tuple[str, ...]) -> dict[str, str]:
    """{date: event} for the 08:30 ET rows of the given events, sessions 2016-01-01 .. 2023-12-31."""
    e = pd.read_csv(path, encoding="utf-8")
    e = e[e["event"].isin(events) & (e["datetime_et"].str[11:16] == "08:30")]
    e = e[(e["datetime_et"] >= S.START) & (e["datetime_et"] < S.SEAL)]
    d = e["datetime_et"].str[:10]
    need(not d.duplicated().any(), f"two releases of {events} on one day")
    return dict(zip(d, e["event"]))


def drop_days(b: pd.DataFrame, days: set[str]) -> pd.DataFrame:
    out = b[~b["session"].isin(days)]
    need(not out["session"].isin(days).any(), "a dropped session survived")
    return out


def run() -> int:
    t0 = time.time()
    S.sign_audit()
    try:
        S.sign_audit(-1.0)
    except S.D775Error:
        pass
    else:
        raise D783Error("D775's sign audit did not raise on a mirrored book")
    b = S.load_bars()
    d775_days = S.release_days()
    # right quantity, first: the imported study reproduces D775's primary on the unfiltered bars
    ref = S.study(b, "NQ", d775_days, primary=False)["primary"]
    need((ref["n"], ref["mean_gross"]) == D775_KNOWN, f"D775's primary is not reproduced: {ref['n']}, {ref['mean_gross']}")
    print(f"D775 reproduced: {ref['n']} trades, +${ref['mean_gross']}", flush=True)
    bf = drop_days(b, set(d775_days))
    res: dict[str, Any] = {"spec": SPEC.name, "window": [S.START, "2023-12-31"], "d775_reproduced": list(D775_KNOWN),
                           "d775_sessions_dropped": len(d775_days), "cells": {}}
    for cell, evs in CELLS.items():
        rel = load_cal(CAL, evs)
        need(len(rel) == EXPECTED[cell], f"{cell}: {len(rel)} release days, expected {EXPECTED[cell]}")
        need(not set(rel) & set(d775_days), f"{cell} shares a day with CPI/EMPSIT")
        roots = list(S.ROOTS) if cell == PRIMARY_CELL else [PRIMARY_ROOT]
        res["cells"][cell] = {}
        for root in roots:
            r = S.study(bf, root, rel, primary=(cell == PRIMARY_CELL and root == PRIMARY_ROOT))
            res["cells"][cell][root] = r
            p = r["primary"]
            print(f"{cell:6s} {root:3s} | {r['counts']} | mean {p['mean_gross']} t {p['t_gross']} | N p50 "
                  f"{r['N_rotation']['p50']} p95 {r['N_rotation']['p95']} rank {r['N_rotation']['rank']} | {r['reading']}",
                  flush=True)
    rel_ppi = load_cal(CAL, CELLS[PRIMARY_CELL])
    kept = S.study(b, PRIMARY_ROOT, rel_ppi, primary=False)
    res["ppi_nq_with_d775_days_kept"] = {"primary": kept["primary"], "N_rotation": kept["N_rotation"],
                                         "reading": kept["reading"]}
    prim = res["cells"][PRIMARY_CELL][PRIMARY_ROOT]
    pool = res["cells"]["ALL"][PRIMARY_ROOT]
    res["reading"] = prim["reading"]
    res["GO"] = prim["reading"] == "SUPPORTED"
    fetch = (prim["gates"]["G1"] and prim["gates"]["N"]) or (
        pool["gates"]["N"] and pool["primary"]["mean_gross"] >= 2 * S.ROOTS[PRIMARY_ROOT][2])
    res["recommend_fetching_census_bea_dol"] = bool(fetch)
    res["wall_s"] = round(time.time() - t0, 1)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, default=str)
    print("READING", res["reading"], "GO", res["GO"], "| fetch Census/BEA/DOL:", res["recommend_fetching_census_bea_dol"],
          f"| {res['wall_s']}s ->", OUT.relative_to(REPO))
    return 0


def selftest() -> int:
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "cal.csv"
        pd.DataFrame({"datetime_et": ["2015-12-15T08:30:00-05:00", "2016-03-15T08:30:00-04:00", "2016-03-16T10:00:00-04:00",
                                      "2019-05-01T08:30:00-04:00", "2024-01-11T08:30:00-05:00"],
                      "event": ["PPI", "PPI", "PPI", "IMPEXP", "PPI"]}).to_csv(p, index=False, encoding="utf-8")
        got = load_cal(p, ("PPI",))
        need(got == {"2016-03-15": "PPI"}, f"load_cal keeps only in-window 08:30 rows of the cell: {got}")
        need(load_cal(p, ("PPI", "IMPEXP")) == {"2016-03-15": "PPI", "2019-05-01": "IMPEXP"}, "load_cal pooled")
    b = pd.DataFrame({"session": ["2016-03-10", "2016-03-11", "2016-03-11", "2016-03-14"], "close": [1.0, 2.0, 3.0, 4.0]})
    out = drop_days(b, {"2016-03-11"})
    need(list(out["session"]) == ["2016-03-10", "2016-03-14"], "drop_days")
    S.sign_audit()
    try:
        S.sign_audit(-1.0)
    except S.D775Error:
        pass
    else:
        raise D783Error("D775's sign audit did not raise on a mirrored book")
    print("selftest OK: the calendar loader keeps only in-window 08:30 rows of the cell (and pools); the removal drops "
          "exactly the named sessions; D775's sign audit raises on a mirrored book")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args(argv)
    return selftest() if a.selftest else run()


if __name__ == "__main__":
    sys.exit(main())
