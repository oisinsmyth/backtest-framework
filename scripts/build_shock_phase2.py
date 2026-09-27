"""Shock classifier Phase 2 (SHOCK_CLASSIFIER_PREREG.md s.4, s.10; SC-A1..A7): sigma_tod, shock detection, peer betas,
the confirmation ratio and the classification, over 2016-01-04 -> 2025-02-28, and the counts the deposit's Phase 2
gate asks for ("report shock counts per class per instrument per year"). NO FORWARD RETURN IS READ: every quantity is
computed from bars at or before each shock's own bar (deposit s.0.7).

    python scripts/build_shock_phase2.py        # SYSTEM interpreter (pyarrow)
    -> data/shock/phase2_shocks.csv.gz (every shock at z = 3, 4, 5) + data/shock/phase2_counts.json

Prices: fut_day1m's front close per minute (09:00-15:59), and fut_premarket_1m's front close for GC, SI, 6E and ZN
(08:00-08:59), forward-filled within a session for at most 5 minutes (SC-A6's peer pricing; the traded markets are
100% covered). Sessions: SC-A6's usable set, with a 60-session warm-up read from 2015-09 so detection starts on
2016-01-04. Events (s.3.4): CPI, EMPSIT (payrolls), FOMC and FOMC_UNSCHEDULED for all four; EIA_WPSR for CL. SC-A7:
EIA_NGSR is a diagnostic flag on CL, not in the classifying event flag.
"""
from __future__ import annotations

import gzip
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as ds

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from backtest_framework.shock import model as M  # noqa: E402

SH = REPO / "data" / "shock"
DAY1M = REPO / "data" / "fixtures" / "fut_day1m.parquet"
PRE = REPO / "data" / "fixtures" / "fut_premarket_1m.csv.gz"
CAL = REPO / "data" / "fixtures" / "cme_session_calendar.csv.gz"
EVENTS = REPO / "data" / "calendar" / "events.csv"
SPY = REPO / "data" / "raw" / "alphavantage" / "daily" / "SPY.json.gz"
WARM, START, RESERVED_FROM = "2015-09-01", "2016-01-04", "2025-03-01"
PEERS = {"NQ": ["ES", "RTY", "ZN", "6J"], "ES": ["NQ", "RTY", "ZN", "6J"], "CL": ["BZ", "HO", "RB"], "GC": ["SI", "6E", "ZN"]}
PREMARKET = ("GC", "SI", "6E", "ZN")
EV_ALL = ("CPI", "EMPSIT", "FOMC", "FOMC_UNSCHEDULED")
EV_CL = ("EIA_WPSR",)
EV_DIAG = ("EIA_NGSR",)  # SC-A7: a diagnostic flag on CL, not a classifying event
ZS = (3.0, 4.0, 5.0)
C_PAIRS = {"primary": (0.6, 0.2), "alt_0.5_0.3": (0.5, 0.3), "alt_0.7_0.1": (0.7, 0.1)}
FFILL = 5
MINUTES = list(pd.date_range("2000-01-01 08:00", "2000-01-01 15:59", freq="min").strftime("%H:%M"))


def usable_sessions() -> list[str]:
    g0 = json.loads((SH / "gate0.json").read_text(encoding="utf-8"))
    spy = json.load(gzip.open(SPY, "rt", encoding="utf-8"))
    cal = pd.read_csv(CAL, encoding="utf-8", dtype={"day": str})
    half = set(cal.loc[(cal["root"] == "ES") & cal["is_early_close"].astype(bool), "day"])
    days = {d for d in spy if WARM <= d < RESERVED_FROM} - half - set(g0["outage_days_excluded"])
    return sorted(days)


def grids(roots: list[str], days: list[str]) -> dict[str, pd.DataFrame]:
    """(session x minute) close grids, front contract, forward-filled within a session for at most FFILL minutes."""
    f = (ds.field("day") >= WARM) & (ds.field("day") < RESERVED_FROM) & ds.field("root").isin(roots)
    t = ds.dataset(DAY1M).to_table(columns=["root", "day", "bar", "close", "present"], filter=f).to_pandas()
    t = t[t["present"]]
    t["hhmm"] = (pd.Timestamp("2000-01-01 09:00") + pd.to_timedelta(t["bar"], unit="m")).dt.strftime("%H:%M")
    pre = pd.read_csv(PRE, encoding="utf-8", dtype={"day": str})
    pre = pre[(pre["day"] >= WARM) & (pre["day"] < RESERVED_FROM) & pre["front"]]
    if (t["day"] >= RESERVED_FROM).any() or (pre["day"] >= RESERVED_FROM).any():
        raise RuntimeError("a sealed session reached Phase 2")
    out = {}
    for r in roots:
        a = t.loc[t["root"] == r, ["day", "hhmm", "close"]]
        if r in PREMARKET:
            a = pd.concat([a, pre.loc[pre["root"] == r, ["day", "hhmm", "close"]]])
        g = a.pivot_table(index="day", columns="hhmm", values="close", aggfunc="first")
        g = g.reindex(index=days, columns=MINUTES)
        out[r] = g.ffill(axis=1, limit=FFILL)
    return out


def main() -> int:
    t0 = time.time()
    days = usable_sessions()
    roots = sorted(set(PEERS) | {p for v in PEERS.values() for p in v})
    G = grids(roots, days)
    R1 = {r: g / g.shift(1, axis=1) - 1 for r, g in G.items()}  # within-session 1-minute returns
    g0 = json.loads((SH / "gate0.json").read_text(encoding="utf-8"))
    rolls = {r: set(v["days"]) for r, v in g0["G3_roll_days"].items()}
    ev = pd.read_csv(EVENTS, encoding="utf-8")
    ev = ev[ev["datetime_et"].astype(str).str[:10] < RESERVED_FROM]
    ev["t"] = pd.to_datetime(ev["datetime_utc"], utc=True)
    rel = {k: sorted(ev.loc[ev["event"].isin(v), "t"]) for k, v in (("all", EV_ALL), ("cl", EV_ALL + EV_CL), ("diag", EV_DIAG))}
    rel_ns = {k: np.array([t.value for t in v], dtype=np.int64) for k, v in rel.items()}

    def flagged(t0_ns: int, arr: np.ndarray) -> bool:
        """4.5 by binary search: a release in [t0 - 5 min, t0 + 1 min] (equivalently t0 in [rel - 1, rel + 5])."""
        lo_ns, hi_ns = t0_ns - 5 * 60_000_000_000, t0_ns + 60_000_000_000
        i = int(np.searchsorted(arr, lo_ns, side="left"))
        return bool(i < len(arr) and arr[i] <= hi_ns)

    day_set, day_pos = set(days), {d: k for k, d in enumerate(days)}
    GA = {r: g.to_numpy(float) for r, g in G.items()}
    skipped_zero_sigma = {}
    rows = []
    for root, peers in PEERS.items():
        lo, hi = M.WINDOWS[root]
        sig = M.sigma_tod(R1[root].abs()).to_numpy(float)
        wcols = [m for m in MINUTES if lo <= m <= hi]
        wmask = np.array([lo <= m <= hi for m in MINUTES])
        skipped_zero_sigma[root] = int(((sig == 0) & wmask[None, :]).sum())
        betas = {}
        for pr_ in peers:
            x, y = R1[root][wcols], R1[pr_][wcols]
            ok = x.notna() & y.notna()
            xs, ys = x.where(ok, 0.0), y.where(ok, 0.0)
            sums = pd.DataFrame({"n": ok.sum(axis=1).astype(float), "sx": xs.sum(axis=1), "sy": ys.sum(axis=1),
                                 "sxx": (xs * xs).sum(axis=1), "syy": (ys * ys).sum(axis=1), "sxy": (xs * ys).sum(axis=1)})
            betas[pr_] = M.rolling_beta_rho(sums)[["beta", "rho"]].to_numpy(float)
        rl = rel_ns["cl"] if root == "CL" else rel_ns["all"]
        for d in days:
            if d < START or not M.eligible_session(d, rolls[root], day_set):
                continue
            k = day_pos[d]
            s = sig[k].copy()
            s[s == 0] = np.nan  # SC-A8: a zero scale is undefined; that minute cannot detect
            if not np.isfinite(s).any():
                continue
            px = GA[root][k]
            for z in ZS:
                for h in M.detect(px, MINUTES, s, (lo, hi), z=z):
                    i, w = h["i"], h["w"]
                    pr = []
                    for pr_ in peers:
                        pp = GA[pr_][k]
                        rpw = pp[i] / pp[i - w] - 1 if np.isfinite(pp[i]) and np.isfinite(pp[i - w]) else float("nan")
                        pr.append((rpw, float(betas[pr_][k, 0]), float(betas[pr_][k, 1])))
                    C, nv = M.confirmation(h["r"], pr)
                    t0_bar = M.et_to_utc(d, h["minute"]) + pd.Timedelta(minutes=1)  # t0 = the bar's close
                    t0_ns = pd.Timestamp(t0_bar).value
                    evf = flagged(t0_ns, rl)
                    row = {"root": root, "day": d, "bar": h["minute"], "z": z, "w": w, "d": h["d"], "r": h["r"],
                           "S": h["S"], "thresh": h["thresh"], "C": C, "n_valid_peers": nv, "event": evf,
                           "event_ngsr_diag": bool(root == "CL" and flagged(t0_ns, rel_ns["diag"]))}
                    for kk, (chi, clo) in C_PAIRS.items():
                        row[f"class_{kk}"] = M.classify(C, evf, chi, clo)
                    rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(SH / "phase2_shocks.csv.gz", index=False, encoding="utf-8", lineterminator="\n")
    prim = df[df["z"] == 4.0]
    yrs = prim["day"].str[:4]
    counts = {
        "span": [START, "2025-02-28"], "usable_sessions": sum(1 for d in days if d >= START),
        "per_root_class": prim.groupby(["root", "class_primary"]).size().unstack(fill_value=0).to_dict("index"),
        "per_root_year_class": {r: g.groupby([g["day"].str[:4], "class_primary"]).size().unstack(fill_value=0).to_dict("index")
                                for r, g in prim.groupby("root")},
        "per_root_per_year_mean": (prim.groupby(["root", yrs]).size().groupby(level=0).mean()).to_dict(),
        "none_for_fewer_than_2_peers": prim[prim["n_valid_peers"] < 2].groupby("root").size().to_dict(),
        "event_flagged": prim[prim["event"]].groupby(["root", "class_primary"]).size().unstack(fill_value=0).to_dict("index"),
        "by_window": prim.groupby(["root", "w"]).size().unstack(fill_value=0).to_dict("index"),
        "sensitivity_z": df.groupby(["root", "z"]).size().unstack(fill_value=0).to_dict("index"),
        "sensitivity_c_pairs": {k: prim[f"class_{k}"].value_counts().to_dict() for k in C_PAIRS},
        "deposit_plan": "s.7A: ~150 shocks per year per market at z = 4; ~2,400 INFO vs ~1,800 LIQ pooled over 10 years",
        "minutes_skipped_zero_sigma_SC_A8": skipped_zero_sigma,
        "runtime_min": round((time.time() - t0) / 60, 1)}
    (SH / "phase2_counts.json").write_text(json.dumps(counts, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: counts[k] for k in ("usable_sessions", "per_root_class", "per_root_per_year_mean",
                                             "minutes_skipped_zero_sigma_SC_A8",
                                             "none_for_fewer_than_2_peers", "event_flagged", "by_window", "sensitivity_z",
                                             "sensitivity_c_pairs", "runtime_min")}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
