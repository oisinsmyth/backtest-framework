"""D635's design, shared by its POWER step (`power_gate_c0.py`) and its runner: the observation set, and the
predicted roll flows Q_B (BCOM) and Q_G (GSCI, per $1bn), in contracts. No flow is read here.

The BCOM side reuses Gate R0's code (run_gate_r0.py, the IR-A14 re-run inputs: the 2020 holes filled). The tracker
weight on day d-1 is CIM(y) x H(d-1) / sum, with y the calendar year of d (every roll month is Feb-Dec, after January's
reweight). It is asserted equal to the committed D634 re-run tracker on every day both hold.

    uv run python scripts/c0_design.py --summary      # counts only
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
IR = REPO / "data" / "index_reweight"
PANEL = IR / "window_flow_daily.csv.gz"
TRACKER = IR / "drift_tracker_daily_rerun.csv.gz"
RPDW = IR / "gsci_rpdw.csv"
GSCHED = IR / "gsci_schedule.csv"
FIRST_MONTH, LAST_MONTH = "2016-02", "2025-02"
LETTER = "FGHJKMNQUVXZ"
RIC = {"ZW": "W", "KE": "KW", "ZC": "C", "ZS": "S", "HE": "LH", "LE": "LC", "CL": "CL", "HO": "HO", "RB": "RB",
       "NG": "NG", "GC": "GC", "SI": "SI"}


def _load(name: str, fn: str) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    assert s is not None and s.loader is not None
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


G = _load("run_gate_r0", "run_gate_r0.py")


def months() -> list[pd.Period]:
    return [p for p in pd.period_range(FIRST_MONTH, LAST_MONTH, freq="M") if p.month != 1]


def root_days(prices: Any, comp: str) -> list[str]:
    """The root's own exchange days (settlements; holiday republications already removed): GSCI's CME calendar."""
    return sorted(d for d in prices[comp] if pd.Timestamp(d).dayofweek < 5)


def gsci_held(row: pd.Series, y: int, m: int) -> tuple[int, int]:
    """The contract GSCI holds at the start of month m (a letter earlier in the calendar than m is next year's)."""
    lm = LETTER.index(row[f"m{m:02d}"]) + 1
    return (y if lm >= m else y + 1), lm


def build() -> dict[str, Any]:
    reads: dict[str, Any] = {}
    cip = G.cips()
    cme, _ = G.load_cme(reads, fill=True)
    prices = {**cme, **G.load_ice(reads), **G.load_lme(reads)}
    G.assert_no_vault(prices)
    bdays, bd, det = G.calendar(prices, cip)
    bdays = [d for d in bdays if d >= "2015-01-01"]
    comps = sorted({c for y in cip for c, w in cip[y].items() if w > 0})
    rws = {c: G.roll_weights(c, prices, bdays, bd) for c in comps}
    H = {c: G.sub_index_returns(c, prices, bdays, bd, rws[c])[1] for c in comps}
    cim = G.cims(prices, cip, det)
    prev = {d: p for p, d in zip(bdays, bdays[1:])}
    table = G.lead_table()
    rpdw = pd.read_csv(RPDW, encoding="utf-8")
    rp = {(int(y), r): float(v) for y, r, v in zip(rpdw["target_year"], rpdw["ric"], rpdw["rpdw_pct"])}
    gs = pd.read_csv(GSCHED, encoding="utf-8").set_index("ric")
    tr = pd.read_csv(TRACKER, encoding="utf-8", dtype={"day": str})

    obs: list[dict[str, Any]] = []
    wcache: dict[str, dict[str, float]] = {}

    def weight(d: str) -> dict[str, float]:
        if d not in wcache:
            wcache[d] = G.weights(cim[int(d[:4])], H, d)
        return wcache[d]

    for comp in G.CME_COMPS:
        root = G.COMP[comp][1]
        m_ = G.mult(comp)
        rdays = root_days(prices, comp)
        rbd: dict[str, int] = {}
        run: dict[str, int] = {}
        for d in rdays:
            run[d[:7]] = run.get(d[:7], 0) + 1
            rbd[d] = run[d[:7]]
        for per in months():
            y, m = per.year, per.month
            L, N = G.lead_next(table[G.COMP[comp][2]], y, m)
            bcom_days = {d for d in bdays if d[:7] == str(per) and 5 <= bd[d] <= 9}
            gsci_days: set[str] = set()
            g_out = g_in = None
            if root in RIC:
                row = gs.loc[RIC[root]]
                g_out, g_in = gsci_held(row, y, m), (gsci_held(row, y + 1, 1) if m == 12 else gsci_held(row, y, m + 1))
                if g_out != g_in:
                    gsci_days = {d for d in rdays if d[:7] == str(per) and 5 <= rbd[d] <= 9}
            for d in sorted(bcom_days | gsci_days):
                p = prev.get(d)
                if p is None:
                    continue
                pL = G.price_at(prices, comp, p, L)
                pN = G.price_at(prices, comp, p, N)
                w = weight(p)
                for role, c in (("L", L), ("N", N)):
                    qb = 0.0
                    if L != N and d in bcom_days and pL and pN:
                        h = G.AUM[y][0] * 1e9 * w.get(comp, 0.0) / (pL * m_)
                        qb = -0.2 * h if role == "L" else 0.2 * h * pL / pN
                    qg = 0.0
                    if d in gsci_days and g_out is not None and g_in is not None and c in (g_out, g_in):
                        po = G.price_at(prices, comp, p, g_out)
                        pi = G.price_at(prices, comp, p, g_in)
                        if po and pi:
                            gg = rp[(y, RIC[root])] / 100 * 1e9 / (po * m_)
                            qg = -0.2 * gg if c == g_out else 0.2 * gg * po / pi
                    obs.append({"root": root, "comp": comp, "sym": f"{root}{LETTER[c[1] - 1]}{str(c[0])[2:]}",
                                "role": role, "day": d, "prev": p, "month": str(per), "bcom_bd": bd.get(d),
                                "bcom_day": d in bcom_days, "gsci_day": d in gsci_days, "Q_B": qb, "Q_G": qg,
                                "aum_bn": G.AUM[y][0]})
    o = pd.DataFrame(obs)
    # the known answer: the weights used equal the committed D634 re-run tracker wherever both hold
    # the tracker's segment for target year Y holds CIM(Y-1)'s weights, so a day in year y matches segment y+1
    t = {(d, c): float(v) for d, y, c, v in zip(tr["day"], tr["target_year"], tr["component"], tr["weight"])
         if int(y) == int(d[:4]) + 1}
    chk = [(d, c, weight(d)[c]) for d in sorted(set(o["prev"])) for c in weight(d) if (d, c) in t]
    worst = max((abs(v - t[(d, c)]) for d, c, v in chk), default=0.0)
    if not chk or worst > 1e-9:
        raise RuntimeError(f"the design's weights differ from the D634 tracker ({len(chk)} cells, worst {worst})")
    return {"obs": o, "bdays": bdays, "bd": bd, "det": det, "prices": prices, "reads": reads,
            "tracker_check": {"cells": len(chk), "worst_abs_diff": worst}}


def norms(panel: pd.DataFrame, bdays: list[str], keep: set[tuple[str, str]] | None = None) -> pd.DataFrame:
    """S_win = net - mean(net over the 20 prior business days on which the contract has a row), >= 15 required.
    `keep` limits which (sym, day) rows get an S_win (POWER computes non-hedge days only)."""
    out = []
    for sym, g in panel.sort_values("day").groupby("sym"):
        days, net = list(g["day"]), g["net"].to_numpy(float)
        for i, d in enumerate(days):
            if keep is not None and (sym, d) not in keep:
                continue
            prior = net[max(0, i - 20):i]
            lo = days[max(0, i - 20)] if i else d
            span = [x for x in bdays if lo <= x < d]
            if len(prior) < 15 or len(span) > 40:
                out.append((sym, d, np.nan, len(prior)))
                continue
            out.append((sym, d, net[i] - prior.mean(), len(prior)))
    return pd.DataFrame(out, columns=["sym", "day", "S_win", "norm_days"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", action="store_true")
    a = ap.parse_args()
    if a.summary:
        b = build()
        o = b["obs"]
        print(f"observations {len(o)}; months {o['month'].nunique()}; tracker check {b['tracker_check']}")
        print(o.groupby("root").agg(n=("day", "size"), qb_nonzero=("Q_B", lambda s: int((s != 0).sum())),
                                    qg_nonzero=("Q_G", lambda s: int((s != 0).sum()))).to_string())
        both = o[(o["Q_B"] != 0) | (o["Q_G"] != 0)]
        print("corr(Q_B, Q_G) over rows with either nonzero:", round(float(np.corrcoef(both["Q_B"], both["Q_G"])[0, 1]), 4))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
