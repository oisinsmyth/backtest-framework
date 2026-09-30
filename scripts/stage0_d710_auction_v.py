"""D710 STAGE 0: the Treasury auction-day intraday V on Treasury futures (FRBNY SR 1188), per
docs/decisions/D710-STAGE-0-DESIGN-treasury-auction-intraday-v.md. NOT YET RUN.

    python scripts/stage0_d710_auction_v.py --selftest            # synthetic: every assertion shown to RAISE
    uv run --with pyarrow python scripts/stage0_d710_auction_v.py --components-only --data-root D
                                                                  # arm + F2 known answers; no Treasury bar read
    uv run --with pyarrow python scripts/stage0_d710_auction_v.py --run --data-root D
                                                                  # the one run (committed separately first)
Run from the worktree; D is the main checkout's data/ ("C:/Users/O/Desktop/Projects/Backtest Framework/data").
Fixtures are read from D (the component builders' fixture paths are pointed at D); outputs go to THIS checkout's data/.

WHAT IT MEASURES (design sections 5-7)
--------------------------------------
Per session and root, from `fut_day1m.parquet` (09:00-15:59 ET, bar b = minutes after 09:00; a bar's close is the
last trade before the next minute), with anchor prices taken as-of (the last bar at or before the anchor, at most
STALE = 5 minutes old, same contract):
    r_pre  = ln P(12:59) - ln P(09:59)      10:00:00 -> 13:00:00
    r_post = ln P(15:59) - ln P(13:04)      13:05:00 -> 16:00:00   (flat through the close and the release)
    V      = r_post - r_pre                 in bp
Event = a NOMINAL coupon auction (not TIPS/FRN, not a $25m small-value test) closing at 13:00, mapped to its future
(2y,3y->ZT 5y->ZF 7y,10y->ZN 30y->UB; secondary 10y->TN, 20y->ZB, 30y->ZB).
Controls = the paper's rule: the last clean non-auction session on or before d-7 and the first on or after d+7 (each
within CTRL_MAXGAP days of its target). Delta = V - (V_before + V_after)/2. sigma = sd(V) over the 60 most recent
clean non-auction sessions strictly before d. z = Delta / sigma.

Gates (fixed in the design): G1 pooled mean z > 0 with t >= 2 (the larger of NW and ISO-week-clustered SE);
G2 above N1's p95 (exact enumeration of the event schedule over clean non-auction sessions, offsets 10..M-10);
G3 achieved share (mean z / mean E[z]) >= 0.5 on the full span; G4 the same on 2015-2023; G5 the 11:00-centred
placebo does not fire. PRESENT -> stage 2 (the two-leg trade, section 8) runs; otherwise it does not.

SEALS: bars are read with day < 2024-01-01 and asserted; the auction calendar is cut below 2024-01-01 at read and
asserted; the component series are built from inputs cut below 2024-01-01.

DECLARED IN CODE THAT THE DESIGN LEFT IMPLICIT (reported by the runner, never tuned after the run)
- CTRL_MAXGAP = 14 days; an event lacking either control is dropped and counted (late-December-2023 events lose
  their week-after control to the seal).
- The tenor of an auction is the term it was SOLD as (see fetch_treasury_auctions.classify).
- The delivery-window rule: the fixture's volume front rolls ON first notice day (e.g. ZNU0 -> ZNZ0 on 2010-08-31),
  so a late-month auction in Feb/May/Aug/Nov can fall on or after the held contract's first position day (the
  second-to-last session of the month before delivery). Premise events there are KEPT (a measurement, no position)
  and counted; stage-2 legs there are EXCLUDED, and the assertion is that no traded leg is inside the window.
- N1 for a leg book scores a pseudo day's leg only where its fill prices exist (nanmean); the count range is reported.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from d710_paths import REPO, data_root, tracked  # noqa: E402

RESERVED = "2024-01-01"
SPAN_LO = "2010-06-07"
ERA_SPLIT = "2015-01-01"
SUBERA = "2019-01-01"
COMPONENT_WINDOW = ("2016-01-04", "2023-12-29")
F2_WINDOW = ("2018-05-14", "2023-12-29")
N_BARS = 420
STALE = 5
SIGMA_N = 60
CTRL_MAXGAP = 14
N1_EDGE = 10
N4_DRAWS, SEED = 100_000, 710
ROOTS = ("ZT", "ZF", "ZN", "TN", "ZB", "UB")
ROOT_FROM = {"ZT": SPAN_LO, "ZF": SPAN_LO, "ZN": SPAN_LO, "ZB": SPAN_LO, "UB": "2013-01-01", "TN": "2021-01-01"}
PRIMARY = (("2y", "ZT"), ("3y", "ZT"), ("5y", "ZF"), ("7y", "ZN"), ("10y", "ZN"), ("30y", "UB"))
SECONDARY = (("10y", "TN"), ("20y", "ZB"), ("30y", "ZB"))
# design section 5: Table 4 sector factors (SR 1188 p. 49), CTD remaining maturities, cash tenors
SECTOR = {("2y", "ZT"): 1.0, ("3y", "ZT"): 0.677 / 0.749, ("5y", "ZF"): 1.0, ("7y", "ZN"): 1.0,
          ("10y", "ZN"): 0.796 / 1.192, ("10y", "TN"): 1.0, ("30y", "UB"): 1.0}
CASH_N = {"2y": 2, "3y": 3, "5y": 5, "7y": 7, "10y": 10, "30y": 30}
CTD_N = {"ZT": 1.9, "ZF": 4.3, "ZN": 6.6, "TN": 9.6, "UB": 25.5}
T_TABLE_25 = {("2y", "ZT"): 0.951, ("3y", "ZT"): 0.580, ("5y", "ZF"): 0.867, ("7y", "ZN"): 0.947,
              ("10y", "ZN"): 0.459, ("10y", "TN"): 0.965, ("30y", "UB"): 0.893}
# SR 1188 Table 3 (p. 48): price pressure, price bp, S2 2007-2014 and S3 2015-2024; full-sample pre share
VCASH = {"E1": {"2y": 1.852, "3y": 3.660, "5y": 6.518, "7y": 5.628, "10y": 15.222, "30y": 25.514},
         "E2": {"2y": 0.887, "3y": 1.216, "5y": 4.482, "7y": 2.509, "10y": 5.165, "30y": 14.224}}
PRE_SHARE = {"2y": 0.733 / 1.336, "3y": 1.134 / 2.254, "5y": 2.523 / 4.630, "7y": 1.204 / 4.020,
             "10y": 3.822 / 9.906, "30y": 12.075 / 17.106}
ANCH = {"premise": (59, 239, 244, 419), "placebo11": (4, 119, 124, 239)}
LEGS = {"pre": (60, 238, -1), "post": (245, 419, +1)}         # entry bar close, exit bar close, side
CLOSE_BAR = 240                                                # 13:00:00 is the close of bar 239
POST_START_MIN = 245                                           # no post-leg entry before 13:06:00
LEG_MINUTES = {"pre": 178, "post": 174}
DYSFUNCTION = ("2020-03-09", "2020-03-20")
REJECTED = {"2020-02-27": "D589 archive dropout (stops near 13:20)", "2020-06-30": "D589 archive dropout (stops 10:10)",
            "2020-02-28": "60 of 420 bars on all six Treasury roots (D710 section 4)"}
MONTH_CODE = {"H": 3, "M": 6, "U": 9, "Z": 12}


class D710Error(AssertionError):
    pass


def chk(cond, msg):
    if not cond:
        raise D710Error(msg)


def P(*a):
    print(*a, flush=True)


# ================================================================================ small statistics
def nw_se(x: np.ndarray) -> float:
    """Newey-West SE of the mean with the paper's lag, floor(4 (n/100)^(2/9)), Bartlett weights."""
    x = np.asarray(x, float)
    n = x.size
    if n < 3:
        return float("nan")
    L = int(math.floor(4 * (n / 100) ** (2 / 9)))
    e = x - x.mean()
    s = float(e @ e) / n
    for lag in range(1, L + 1):
        s += 2 * (1 - lag / (L + 1)) * float(e[lag:] @ e[:-lag]) / n
    return math.sqrt(max(s, 0.0) / n)


def cluster_se(x: np.ndarray, groups: np.ndarray) -> float:
    x = np.asarray(x, float)
    n = x.size
    if n < 3:
        return float("nan")
    e = x - x.mean()
    _, inv = np.unique(groups, return_inverse=True)
    sums = np.bincount(inv, weights=e)
    return math.sqrt(float(sums @ sums)) / n


def iso_week(days: np.ndarray) -> np.ndarray:
    return np.array([f"{date.fromisoformat(d).isocalendar()[0]}-{date.fromisoformat(d).isocalendar()[1]:02d}"
                     for d in days])


def gate_t(x: np.ndarray, days: np.ndarray) -> dict:
    m = float(np.mean(x)) if len(x) else float("nan")
    a, b = nw_se(x), cluster_se(x, iso_week(days))
    se = max(a, b)
    return {"n": int(len(x)), "mean": m, "se_nw": a, "se_week": b, "se_gate": se,
            "t_gate": m / se if se and np.isfinite(se) and se > 0 else float("nan")}


def par_duration(n: float, y: float) -> float:
    return (1 / y) * (1 - (1 + y / 2) ** (-2 * n))


def transfer(tenor: str, root: str, y: float) -> float:
    return SECTOR[(tenor, root)] * par_duration(CTD_N[root], y) / par_duration(CASH_N[tenor], y)


def era(d: str) -> str:
    return "E1" if d < ERA_SPLIT else "E2"


def qtiles(a: np.ndarray, obs: float) -> dict:
    a = np.asarray(a, float)
    a = a[np.isfinite(a)]
    return {"n": int(a.size), "p05": float(np.quantile(a, 0.05)), "p50": float(np.quantile(a, 0.5)),
            "p95": float(np.quantile(a, 0.95)), "observed": float(obs), "percentile": float((a < obs).mean())}


# ================================================================================ seals
def assert_window(days, what: str):
    days = np.asarray(days, str)
    bad = days[days >= RESERVED]
    chk(bad.size == 0, f"[WINDOW] {what}: {bad.size} rows dated {RESERVED} or later (first {bad[:1]})")


# ================================================================================ loading
def load_bars(root_dir: Path) -> pd.DataFrame:
    import pyarrow.parquet as pq
    t = pq.read_table(root_dir / "fixtures" / "fut_day1m.parquet",
                      columns=["root", "contract", "day", "bar", "close", "same_front", "present"],
                      filters=[("root", "in", list(ROOTS)), ("day", ">=", SPAN_LO), ("day", "<", RESERVED)])
    df = t.to_pandas()
    assert_window(df["day"].to_numpy(str), "fut_day1m")
    return df


def load_calendars(root_dir: Path) -> dict:
    cal = pd.read_csv(tracked("calendar", "treasury_auctions.csv"), dtype=str, keep_default_na=False, encoding="utf-8")
    cal = cal[cal["auction_date"] < RESERVED].copy()
    assert_window(cal["auction_date"].to_numpy(str), "treasury_auctions.csv (after the cut)")
    ev = pd.read_csv(tracked("calendar", "events.csv"), dtype=str, keep_default_na=False, encoding="utf-8")
    fomc = {d[:10] for d, e in zip(ev["datetime_et"], ev["event"]) if e in ("FOMC", "FOMC_UNSCHEDULED") and d[:10] < RESERVED}
    ext = pd.read_csv(tracked("calendar", "fomc_2010_2015.csv"), dtype=str, keep_default_na=False, encoding="utf-8")
    fomc |= set(ext["date_et"])
    macro = {d[:10] for d, e in zip(ev["datetime_et"], ev["event"]) if e in ("CPI", "EMPSIT") and d[:10] < RESERVED}
    sc = pd.read_csv(root_dir / "fixtures" / "cme_session_calendar.csv.gz", usecols=["root", "day", "is_early_close"],
                     dtype={"root": str, "day": str}, encoding="utf-8")
    sc = sc[sc["root"].isin(ROOTS) & (sc["day"] < RESERVED)]
    early = {(r, d) for r, d, e in zip(sc["root"], sc["day"], sc["is_early_close"]) if bool(e)}
    return {"auctions": cal, "fomc": fomc, "macro": macro, "early": early}


# ================================================================================ per-root panels
@dataclass
class Panel:
    root: str
    days: np.ndarray                 # str
    dnum: np.ndarray                 # ordinal
    contract: np.ndarray             # str ('MIXED' where a day holds two)
    same_front: np.ndarray
    present: np.ndarray
    price: np.ndarray                # (n, 420) float, NaN where no bar


def root_panel(root: str, df: pd.DataFrame) -> Panel:
    df = df.sort_values(["day", "bar"], kind="mergesort")
    days, di = np.unique(df["day"].to_numpy(str), return_inverse=True)
    n = days.size
    price = np.full((n, N_BARS), np.nan)
    b = df["bar"].to_numpy(np.int64)
    chk(((b >= 0) & (b < N_BARS)).all(), f"{root}: a bar index outside 0..419")
    price[di, b] = df["close"].to_numpy(float)
    g = df.groupby(di, sort=True)
    ncon = g["contract"].nunique().to_numpy()
    con = g["contract"].first().to_numpy(str).astype(object)
    con[ncon > 1] = "MIXED"
    sf = g["same_front"].first().to_numpy(bool) & (ncon == 1)
    pr = g["present"].first().to_numpy(bool)
    dnum = np.array([date.fromisoformat(d).toordinal() for d in days], np.int64)
    return Panel(root, days, dnum, con.astype(str), sf, pr, price)


def build_panels(bars: pd.DataFrame, parallel: bool = True) -> dict[str, Panel]:
    groups = [(r, bars[bars["root"] == r]) for r in ROOTS if (bars["root"] == r).any()]
    if parallel:
        from fast_null import parallel_map
        out = parallel_map(lambda k, v: root_panel(k, v), groups)
    else:
        out = {k: root_panel(k, v) for k, v in groups}
    return {r: out[r] for r, _ in groups}


def asof(price: np.ndarray, bar: int, stale: int = STALE) -> np.ndarray:
    v = price[:, bar].copy()
    for k in range(1, stale + 1):
        if bar - k < 0:
            break
        m = np.isnan(v)
        if not m.any():
            break
        v[m] = price[m, bar - k]
    return v


# ================================================================================ the calendar -> events
@dataclass
class Cfg:
    exclude_shared: bool = True
    exclude_dysfunction: bool = True
    zt_from: str = SPAN_LO
    anchors: tuple = ANCH["premise"]
    sigma_includes_today: bool = False          # a broken book for the self-test only
    trailing_includes_current: bool = False     # a broken book for the self-test only


def auction_days(cal: pd.DataFrame) -> set:
    live = cal[cal["small_value_test"] != "True"]
    return set(live["auction_date"])


def event_table(cal: pd.DataFrame, pairs, cfg: Cfg) -> pd.DataFrame:
    live = cal[cal["small_value_test"] != "True"].copy()
    dur = live[live["kind"].isin(["NOMINAL", "TIPS"])]
    dur_count = dur.groupby("auction_date").size()
    frn_days = set(live.loc[live["kind"] == "FRN", "auction_date"])
    nom = live[(live["kind"] == "NOMINAL")]
    rows = []
    for tenor, root in pairs:
        sub = nom[nom["tenor"] == tenor]
        for _, a in sub.iterrows():
            rows.append({"tenor": tenor, "root": root, "date": a["auction_date"], "close": a["close_comp_et"],
                         "high_yield": float(a["high_yield"]) if a["high_yield"] else float("nan"),
                         "reopening": a["reopening"], "cusip": a["cusip"],
                         "pd_share": float(a["pd_share"]) if a["pd_share"] else float("nan"),
                         "shared": bool(dur_count.get(a["auction_date"], 0) > 1),
                         "frn_shared": a["auction_date"] in frn_days})
    ev = pd.DataFrame(rows)
    if ev.empty:
        return ev
    ev["pd_trailing_median"] = trailing_median(nom, ev, cfg.trailing_includes_current)
    ev["pd_lag_z"] = lagged_pd_z(nom, ev)
    return ev.sort_values(["date", "tenor", "root"], kind="mergesort").reset_index(drop=True)


def trailing_median(nom: pd.DataFrame, ev: pd.DataFrame, include_current: bool = False) -> np.ndarray:
    """The median PD share over the 12 previous auctions of the same tenor, STRICTLY earlier (design 8.4)."""
    out = np.full(len(ev), np.nan)
    by = {t: g.sort_values("auction_date") for t, g in nom.groupby("tenor")}
    for i, (t, d) in enumerate(zip(ev["tenor"], ev["date"])):
        g = by[t]
        prior = g[(g["auction_date"] <= d) if include_current else (g["auction_date"] < d)]
        s = pd.to_numeric(prior["pd_share"], errors="coerce").dropna().to_numpy()[-12:]
        if s.size == 12:
            out[i] = float(np.median(s))
    return out


def lagged_pd_z(nom: pd.DataFrame, ev: pd.DataFrame) -> np.ndarray:
    """F7: the previous same-tenor auction's PD share, standardised by the 24 before it (prior-only)."""
    out = np.full(len(ev), np.nan)
    by = {t: g.sort_values("auction_date") for t, g in nom.groupby("tenor")}
    for i, (t, d) in enumerate(zip(ev["tenor"], ev["date"])):
        s = pd.to_numeric(by[t][by[t]["auction_date"] < d]["pd_share"], errors="coerce").dropna().to_numpy()
        if s.size >= 25:
            base = s[-25:-1]
            sd = base.std(ddof=1)
            if sd > 0:
                out[i] = (s[-1] - base.mean()) / sd
    return out


# ================================================================================ the premise machinery
@dataclass
class RootCalc:
    root: str
    elig: np.ndarray
    ok: np.ndarray
    S: np.ndarray            # clean non-auction mask
    V: np.ndarray
    rpre: np.ndarray
    rpost: np.ndarray
    anchors: np.ndarray      # (n, 4)
    sigma: np.ndarray
    c1: np.ndarray
    c2: np.ndarray
    D: np.ndarray
    Dpre: np.ndarray
    Dpost: np.ndarray
    z: np.ndarray
    Q: np.ndarray            # indices of scoreable clean non-auction days (the N1 group)
    drop: dict = field(default_factory=dict)


def base_eligibility(p: Panel, calx: dict, cfg: Cfg) -> tuple[np.ndarray, dict]:
    frm = cfg.zt_from if p.root == "ZT" else ROOT_FROM[p.root]
    reasons = {
        "before_root_span": p.days < frm,
        "roll_or_mixed": ~p.same_front,
        "present_false": ~p.present,
        "early_close": np.array([(p.root, d) in calx["early"] for d in p.days]),
        "rejected_session": np.isin(p.days, list(REJECTED)),
        "fomc": np.isin(p.days, list(calx["fomc"])),
        "dysfunction": ((p.days >= DYSFUNCTION[0]) & (p.days <= DYSFUNCTION[1])) if cfg.exclude_dysfunction
        else np.zeros(p.days.size, bool),
    }
    bad = np.zeros(p.days.size, bool)
    for v in reasons.values():
        bad |= v
    return ~bad, reasons


def root_calc(p: Panel, calx: dict, adays: set, cfg: Cfg) -> RootCalc:
    elig, reasons = base_eligibility(p, calx, cfg)
    A = np.column_stack([asof(p.price, b) for b in cfg.anchors])
    ok = np.isfinite(A).all(axis=1) & (A > 0).all(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        L = np.log(A)
        rpre = (L[:, 1] - L[:, 0]) * 1e4
        rpost = (L[:, 3] - L[:, 2]) * 1e4
        V = rpost - rpre
    is_auction = np.isin(p.days, list(adays))
    S = elig & ok & ~is_auction
    S_idx = np.flatnonzero(S)
    n = p.days.size
    pos = np.searchsorted(S_idx, np.arange(n), side="right" if cfg.sigma_includes_today else "left")
    sigma = np.full(n, np.nan)
    for i in range(n):
        k = pos[i]
        if k >= SIGMA_N:
            sigma[i] = np.std(V[S_idx[k - SIGMA_N:k]], ddof=1)
    S_ord = p.dnum[S_idx]
    j1 = np.searchsorted(S_ord, p.dnum - 7, side="right") - 1
    j2 = np.searchsorted(S_ord, p.dnum + 7, side="left")
    c1 = np.full(n, -1, np.int64)
    c2 = np.full(n, -1, np.int64)
    okc1 = (j1 >= 0)
    okc1[okc1] &= ((p.dnum[okc1] - 7) - S_ord[j1[okc1]]) <= CTRL_MAXGAP
    okc2 = j2 < S_idx.size
    okc2[okc2] &= (S_ord[j2[okc2]] - (p.dnum[okc2] + 7)) <= CTRL_MAXGAP
    c1[okc1] = S_idx[j1[okc1]]
    c2[okc2] = S_idx[j2[okc2]]
    has = (c1 >= 0) & (c2 >= 0)
    D = np.full(n, np.nan)
    Dpre = np.full(n, np.nan)
    Dpost = np.full(n, np.nan)
    D[has] = V[has] - 0.5 * (V[c1[has]] + V[c2[has]])
    Dpre[has] = rpre[has] - 0.5 * (rpre[c1[has]] + rpre[c2[has]])
    Dpost[has] = rpost[has] - 0.5 * (rpost[c1[has]] + rpost[c2[has]])
    z = D / sigma
    Q = np.flatnonzero(S & np.isfinite(z))
    return RootCalc(p.root, elig, ok, S, V, rpre, rpost, A, sigma, c1, c2, D, Dpre, Dpost, z, Q,
                    {k: int(v.sum()) for k, v in reasons.items()})


def score_events(ev: pd.DataFrame, panels: dict, rcs: dict, calx: dict, cfg: Cfg, primary: bool = True):
    """Attach each event's day index and statistics; return (kept events, drop counts per pair)."""
    kept, drops = [], {}
    for r in ev.itertuples(index=False):
        key = f"{r.tenor}->{r.root}"
        dd = drops.setdefault(key, {})

        def drop(why):
            dd[why] = dd.get(why, 0) + 1

        if r.root not in panels:
            drop("root_not_loaded"); continue
        if r.close != "13:00":
            drop("close_not_13:00"); continue
        if cfg.exclude_shared and r.shared:
            drop("shared_day"); continue
        p, rc = panels[r.root], rcs[r.root]
        i = np.searchsorted(p.days, r.date)
        if i >= p.days.size or p.days[i] != r.date:
            drop("no_session"); continue
        if not rc.elig[i]:
            e, reasons = base_eligibility(p, calx, cfg)
            why = next((k for k, v in reasons.items() if v[i]), "ineligible")
            drop(why); continue
        if not rc.ok[i]:
            drop("anchor_missing_or_stale"); continue
        if not np.isfinite(rc.sigma[i]):
            drop("sigma_burn_in"); continue
        if rc.c1[i] < 0 or rc.c2[i] < 0:
            drop("control_missing"); continue
        T = transfer(r.tenor, r.root, r.high_yield / 100) if (r.tenor, r.root) in SECTOR and np.isfinite(r.high_yield) \
            else float("nan")
        vc = VCASH[era(r.date)].get(r.tenor, float("nan"))
        kept.append({**r._asdict(), "i": int(i), "era": era(r.date), "contract": p.contract[i],
                     "z": float(rc.z[i]), "D_bp": float(rc.D[i]), "Dpre_bp": float(rc.Dpre[i]),
                     "Dpost_bp": float(rc.Dpost[i]), "V_bp": float(rc.V[i]), "rpre_bp": float(rc.rpre[i]),
                     "rpost_bp": float(rc.rpost[i]), "Vc1_bp": float(rc.V[rc.c1[i]]), "Vc2_bp": float(rc.V[rc.c2[i]]),
                     "c1": p.days[rc.c1[i]], "c2": p.days[rc.c2[i]], "sigma_bp": float(rc.sigma[i]),
                     "T": T, "T1_expected_bp": vc, "expected_bp": T * vc, "Ez": T * vc / float(rc.sigma[i]),
                     "Ez_T1": vc / float(rc.sigma[i]),
                     "in_delivery_window": in_delivery_window(p, i),
                     "p0959": float(rc.anchors[i, 0])})
    return pd.DataFrame(kept), drops


def in_delivery_window(p: Panel, i: int) -> bool:
    """True when day i is on or after the first position day of the contract held that day: the second-to-last
    session of the month before delivery, from the root's own session list (CME: two business days before the
    first business day of the delivery month). The contract's year is the first year ending in its digit whose
    delivery month is not before day i's month."""
    c = p.contract[i]
    if len(c) < 2 or c[-2] not in MONTH_CODE:
        return False
    m, yd = MONTH_CODE[c[-2]], int(c[-1])
    y0 = int(p.days[i][:4])
    y = next(y for y in (y0 - 1, y0, y0 + 1, y0 + 2) if y % 10 == yd and (y, m) >= (y0, int(p.days[i][5:7])))
    pm, py = (m - 1, y) if m > 1 else (12, y - 1)
    pref = f"{py}-{pm:02d}"
    mdays = p.days[(p.days >= pref + "-01") & (p.days <= pref + "-31")]
    if mdays.size < 2:
        return False
    return bool(p.days[i] >= mdays[-2])


# ================================================================================ nulls
def n1_offsets(rcs: dict, roots_used) -> np.ndarray:
    M = min(rcs[r].Q.size for r in roots_used)
    return np.arange(N1_EDGE, M - N1_EDGE + 1)


def n1_positions(evk: pd.DataFrame, panels: dict, rcs: dict) -> list[tuple[str, int]]:
    out = []
    for r, d in zip(evk["root"], evk["date"]):
        qd = panels[r].days[rcs[r].Q]
        out.append((r, int(np.searchsorted(qd, d, side="right"))))
    return out


def n1_matrix(evk, panels, rcs, values: dict, offsets: np.ndarray) -> np.ndarray:
    """(offsets x events): event e moved to Q_root[(p_e + j) mod |Q_root|]; values[root] is indexed by day."""
    pos = n1_positions(evk, panels, rcs)
    Z = np.empty((offsets.size, len(pos)))
    for e, (r, pe) in enumerate(pos):
        q = rcs[r].Q
        Z[:, e] = values[r][q[(pe + offsets) % q.size]]
    return Z


def n1_stat_vectorised(Z: np.ndarray) -> np.ndarray:
    return Z.mean(axis=1)


def n1_stat_loop(evk, panels, rcs, values, offsets) -> np.ndarray:
    pos = n1_positions(evk, panels, rcs)
    out = np.empty(offsets.size)
    for k, j in enumerate(offsets):
        row = np.array([values[r][rcs[r].Q[(pe + j) % rcs[r].Q.size]] for r, pe in pos])
        out[k] = np.mean(row)
    return out


def n4_signflip(z: np.ndarray, days: np.ndarray, draws: int = N4_DRAWS, seed: int = SEED) -> dict:
    _, inv = np.unique(iso_week(days), return_inverse=True)
    sums = np.bincount(inv, weights=z)
    rng = np.random.default_rng(seed)
    stats = np.empty(draws)
    step = 10_000
    for s in range(0, draws, step):
        k = min(step, draws - s)
        sg = rng.integers(0, 2, size=(k, sums.size)) * 2 - 1
        stats[s:s + k] = (sg @ sums) / z.size
    p95 = float(np.quantile(stats, 0.95))
    rb = np.random.default_rng(seed + 1)
    boots = [np.quantile(stats[rb.integers(0, draws, draws)], 0.95) for _ in range(200)]
    se = float(np.std(boots, ddof=1))
    obs = float(z.mean())
    res = qtiles(stats, obs)
    res.update({"draws": draws, "clusters": int(sums.size), "p95_bootstrap_se": se,
                "unresolved": bool(abs(obs - p95) < 2 * se)})
    return res


# ================================================================================ the premise
def premise(panels, calx, cfg: Cfg, pairs=PRIMARY, with_nulls: bool = True, with_placebo: bool = True,
            with_n4: bool = True) -> dict:
    cal = calx["auctions"]
    adays = auction_days(cal)
    rcs = {r: root_calc(p, calx, adays, cfg) for r, p in panels.items()}
    ev = event_table(cal, pairs, cfg)
    evk, drops = score_events(ev, panels, rcs, calx, cfg)
    out: dict[str, Any] = {"cfg": {k: v for k, v in cfg.__dict__.items()}, "drops": drops, "rcs": rcs, "events": evk,
                           "root_exclusions": {r: rc.drop for r, rc in rcs.items()}}
    if evk.empty:
        out["verdict"] = "NO EVENTS"
        return out
    assert_no_fomc(evk, calx)
    days = evk["date"].to_numpy(str)
    z = evk["z"].to_numpy(float)
    full = gate_t(z, days)
    e2m = evk["era"].to_numpy() == "E2"
    e2 = gate_t(z[e2m], days[e2m])
    share_full = float(z.mean() / evk["Ez"].mean())
    share_e2 = float(z[e2m].mean() / evk.loc[e2m, "Ez"].mean()) if e2m.any() else float("nan")
    out.update({"pooled": full, "pooled_E2": e2, "achieved_share_full": share_full, "achieved_share_E2": share_e2,
                "literal_T1": {"share_full": float(z.mean() / evk["Ez_T1"].mean()),
                               "share_E2": float(z[e2m].mean() / evk.loc[e2m, "Ez_T1"].mean()) if e2m.any() else None}})
    if with_nulls:
        roots_used = sorted(set(evk["root"]))
        offs = n1_offsets(rcs, roots_used)
        Zm = n1_matrix(evk, panels, rcs, {r: rcs[r].z for r in rcs}, offs)
        n1 = n1_stat_vectorised(Zm)
        out["N1"] = {**qtiles(n1, full["mean"]), "offsets": [int(offs[0]), int(offs[-1])], "p95_se": 0.0}
        out["_N1_draws"] = n1
        if e2m.any():
            out["N1_E2"] = qtiles(n1_matrix(evk[e2m], panels, rcs, {r: rcs[r].z for r in rcs}, offs).mean(axis=1),
                                  e2["mean"])
        if with_n4:
            out["N4"] = n4_signflip(z, days)
            out["N2"] = n2_week_placebo(evk, panels, rcs)
    if with_placebo:
        cfg11 = replace(cfg, anchors=ANCH["placebo11"])
        rcs11 = {r: root_calc(p, calx, adays, cfg11) for r, p in panels.items()}
        z11 = np.array([rcs11[r].z[i] for r, i in zip(evk["root"], evk["i"])])
        m = np.isfinite(z11)
        pl = gate_t(z11[m], days[m])
        fires = bool(full["mean"] > 0 and pl["mean"] >= 0.5 * full["mean"] and pl["t_gate"] >= 2)
        out["N3_placebo11"] = {**pl, "kill_fires": fires}
    g = {"G1_exists": bool(full["mean"] > 0 and full["t_gate"] >= 2)}
    if with_nulls:
        g["G2_above_N1_p95"] = bool(full["mean"] > out["N1"]["p95"])
    g["G3_share_full_ge_half"] = bool(share_full >= 0.5)
    g["G4_share_E2_ge_half"] = bool(share_e2 >= 0.5)
    if with_placebo:
        g["G5_placebo11_does_not_fire"] = not out["N3_placebo11"]["kill_fires"]
    out["gates"] = g
    if not g["G1_exists"] or not g.get("G2_above_N1_p95", True) or not g.get("G5_placebo11_does_not_fire", True):
        out["verdict"] = "ABSENT"
    elif not (g["G3_share_full_ge_half"] and g["G4_share_E2_ge_half"]):
        out["verdict"] = "BELOW HALF" + (" (G4 only)" if g["G3_share_full_ge_half"] else "")
    else:
        out["verdict"] = "PRESENT"
    return out


def assert_no_fomc(evk: pd.DataFrame, calx: dict):
    bad = evk[evk["date"].isin(calx["fomc"])]
    chk(bad.empty, f"[FOMC] {len(bad)} events sit on FOMC statement days: {list(bad['date'][:3])}")


def n2_week_placebo(evk, panels, rcs) -> dict:
    vals, ds = [], []
    for r, d in zip(evk["root"], evk["date"]):
        p, rc = panels[r], rcs[r]
        qset = set(rc.Q.tolist())
        for off in (-7, 7):
            dd = (date.fromisoformat(d) + timedelta(days=off)).isoformat()
            i = np.searchsorted(p.days, dd)
            if i < p.days.size and p.days[i] == dd and int(i) in qset:
                vals.append(rc.z[i]); ds.append(dd)
    v = np.array(vals)
    res = gate_t(v, np.array(ds)) if v.size else {"n": 0}
    cv = np.concatenate([evk["Vc1_bp"].to_numpy() / evk["sigma_bp"].to_numpy(),
                         evk["Vc2_bp"].to_numpy() / evk["sigma_bp"].to_numpy()])
    cd = np.concatenate([evk["c1"].to_numpy(str), evk["c2"].to_numpy(str)])
    res["raw_control_V_z"] = gate_t(cv, cd)
    res["reading"] = ("t >= 2 with the same sign = an auction-WEEK pattern (Lou et al.'s cycle), reported, not a kill")
    return res


# ================================================================================ premise reporting
def pair_table(evk: pd.DataFrame) -> dict:
    out = {}
    for (t, r), g in evk.groupby(["tenor", "root"], sort=False):
        row = {}
        for lab, m in (("full", np.ones(len(g), bool)), ("E1", g["era"].to_numpy() == "E1"),
                       ("E2", g["era"].to_numpy() == "E2"), ("2019_2023", g["date"].to_numpy(str) >= SUBERA)):
            s = g[m]
            if s.empty:
                row[lab] = {"n": 0}
                continue
            dd = s["date"].to_numpy(str)
            row[lab] = {"n": int(len(s)), "D_bp": gate_t(s["D_bp"].to_numpy(), dd), "z": gate_t(s["z"].to_numpy(), dd),
                        "Dpre_bp": float(s["Dpre_bp"].mean()), "Dpost_bp": float(s["Dpost_bp"].mean()),
                        "event_V_bp": float(s["V_bp"].mean()),
                        "control_V_bp": float(((s["Vc1_bp"] + s["Vc2_bp"]) / 2).mean()),
                        "expected_bp": float(s["expected_bp"].mean()),
                        "ratio_to_expected": float(s["D_bp"].mean() / s["expected_bp"].mean())
                        if np.isfinite(s["expected_bp"]).all() else None,
                        "in_delivery_window": int(s["in_delivery_window"].sum())}
        out[f"{t}->{r}"] = row
    return out


def predictions(res: dict) -> dict:
    evk = res["events"]
    pt = pair_table(evk)
    f = {}
    f["F1_pooled_z_positive"] = bool(res["pooled"]["mean"] > 0)
    f["F2_pre_negative_post_positive"] = bool(evk["Dpre_bp"].mean() < 0 and evk["Dpost_bp"].mean() > 0)
    bp = {k: v["full"]["D_bp"]["mean"] for k, v in pt.items() if v["full"].get("n")}
    f["F3_UB_largest_price_bp"] = bool(max(bp, key=bp.get) == "30y->UB") if bp else None
    e1 = evk[evk["era"] == "E1"]["z"].mean()
    e2 = evk[evk["era"] == "E2"]["z"].mean()
    f["F4_E1_z_above_E2_z"] = bool(e1 > e2)
    f["F5_ratio_to_expected_per_pair"] = {k: v["full"].get("ratio_to_expected") for k, v in pt.items()}
    if "N3_placebo11" in res:
        f["F6_placebo11_not_positive"] = bool(res["N3_placebo11"]["mean"] <= 0)
    m = np.isfinite(evk["pd_lag_z"].to_numpy(float))
    if m.sum() > 30:
        x = evk.loc[m, "pd_lag_z"].to_numpy(float)
        y = evk.loc[m, "z"].to_numpy(float)
        xc = x - x.mean()
        b = float(xc @ (y - y.mean()) / (xc @ xc))
        resid = (y - y.mean()) - b * xc
        se = nw_se(resid * xc / (xc @ xc / len(x))) if len(x) > 3 else float("nan")
        f["F7_slope_on_lagged_pd_share"] = {"slope": b, "t_nw": b / se if se else float("nan"), "n": int(m.sum()),
                                            "held": bool(b > 0)}
    return f


# ================================================================================ stage 2: the legs
def leg_pnl(side: int, p_in: float, p_out: float, usd_per_point: float) -> float:
    """Money, not prose: a short (side -1) over a falling price pays positively."""
    return side * (p_out - p_in) * usd_per_point


def leg_gross_arrays(p: Panel, usd: float) -> dict:
    out = {}
    check_leg_spec(LEGS)
    for leg, (b_in, b_out, side) in LEGS.items():
        pi, po = asof(p.price, b_in), asof(p.price, b_out)
        out[leg] = {"in": pi, "out": po, "gross": side * (po - pi) * usd}
    return out


def check_leg_spec(legs: dict):
    b_in, b_out, _ = legs["pre"]
    chk(b_out < CLOSE_BAR - 1, f"[STRADDLE] the pre-leg exit bar {b_out} closes at or after 13:00:00")
    b_in2, _, _ = legs["post"]
    chk(b_in2 >= POST_START_MIN, f"[STRADDLE] the post-leg entry bar {b_in2} fills before 13:06:00")


def costs_table() -> dict:
    j = json.loads(tracked("futures_costs.json").read_text(encoding="utf-8"))
    out = {}
    for r in ROOTS:
        full = j["roots"][r]["full"]
        out[r] = {"usd_per_point": float(full["usd_per_point"]), "tick_usd": float(full["tick_usd"]),
                  "tick_points": float(full["tick_points"]),
                  "cost_rt": float(full["runner_lines"]["d556_min_size"]["value"])}
    return out


def build_trades(res: dict, panels: dict, costs: dict, legs: dict = LEGS, exclude_delivery: bool = True) -> pd.DataFrame:
    check_leg_spec(legs)
    evk = res["events"]
    rows = []
    for e in evk.itertuples(index=False):
        if (e.tenor, e.root) not in PRIMARY:
            continue
        p = panels[e.root]
        c = costs[e.root]
        for leg, (b_in, b_out, side) in legs.items():
            if e.tenor == "30y" and leg == "post":
                continue
            if exclude_delivery and e.in_delivery_window:
                continue
            pi, po = float(asof(p.price[e.i:e.i + 1], b_in)[0]), float(asof(p.price[e.i:e.i + 1], b_out)[0])
            if not (np.isfinite(pi) and np.isfinite(po)):
                continue
            gross = leg_pnl(side, pi, po, c["usd_per_point"])
            dollars_per_bp = e.p0959 * c["usd_per_point"] * 1e-4
            share = PRE_SHARE[e.tenor] if leg == "pre" else 1 - PRE_SHARE[e.tenor]
            proj = e.T * VCASH[e.era][e.tenor] * share * dollars_per_bp
            rows.append({"date": e.date, "tenor": e.tenor, "root": e.root, "leg": leg, "side": side, "i": e.i,
                         "contract": e.contract, "in_delivery_window": bool(e.in_delivery_window),
                         "p_in": pi, "p_out": po, "gross": gross, "cost": c["cost_rt"], "net": gross - c["cost_rt"],
                         "projected": proj, "take_F": bool(proj >= 2 * c["cost_rt"]), "era": e.era,
                         "reopening": e.reopening, "rpre_bp": e.rpre_bp, "pd_share": e.pd_share,
                         "pd_trailing_median": e.pd_trailing_median, "c1": e.c1, "c2": e.c2,
                         "price": e.p0959, "minutes": LEG_MINUTES[leg]})
    tr = pd.DataFrame(rows)
    if not tr.empty:
        chk(not tr["in_delivery_window"].any(), "[DELIVERY] a traded leg sits inside its contract's delivery window")
    return tr


def trims(x: np.ndarray) -> dict:
    x = np.sort(np.asarray(x, float))
    k = max(1, int(round(0.01 * x.size)))
    return {"k_each_tail": k, "mean_ex_top": float(x[:-k].mean()), "mean_ex_bottom": float(x[k:].mean()),
            "mean_trimmed": float(x[k:-k].mean()) if x.size > 2 * k else float("nan")}


def daily_series(tr: pd.DataFrame, calendar_days: np.ndarray, col: str) -> pd.Series:
    s = tr.groupby("date")[col].sum()
    return s.reindex(calendar_days, fill_value=0.0)


def sharpe_sortino(d: np.ndarray) -> dict:
    d = np.asarray(d, float)
    sd = d.std(ddof=1)
    dn = np.sqrt(np.mean(np.minimum(d, 0) ** 2))
    return {"sharpe": float(d.mean() / sd * np.sqrt(252)) if sd > 0 else float("nan"),
            "sortino": float(d.mean() / dn * np.sqrt(252)) if dn > 0 else float("nan")}


def block_bootstrap_sharpe_se(d: pd.Series, draws: int = 1000, seed: int = SEED) -> float:
    months = d.index.str[:7]
    groups = [d[months == m].to_numpy() for m in sorted(set(months))]
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(draws):
        pick = rng.integers(0, len(groups), len(groups))
        x = np.concatenate([groups[k] for k in pick])
        sd = x.std(ddof=1)
        out.append(x.mean() / sd * np.sqrt(252) if sd > 0 else np.nan)
    return float(np.nanstd(out, ddof=1))


def max_drawdown(d: np.ndarray) -> float:
    c = np.cumsum(d)
    return float(np.max(np.maximum.accumulate(np.concatenate([[0.0], c]))[1:] - c)) if c.size else 0.0


def book_report(tr: pd.DataFrame, calendar_days: np.ndarray, costs: dict, years: float) -> dict:
    if tr.empty:
        return {"trades": 0}
    g, n = tr["gross"].to_numpy(float), tr["net"].to_numpy(float)
    dd = tr["date"].to_numpy(str)
    dg, dn = daily_series(tr, calendar_days, "gross"), daily_series(tr, calendar_days, "net")
    tpy = len(tr) / years
    ticks = {r: costs[r]["tick_usd"] for r in costs}
    perf = {
        "trades": int(len(tr)), "trades_per_year": tpy,
        "exposure": float(tr["minutes"].sum() / (len(calendar_days) * N_BARS)),
        "mean_gross": gate_t(g, dd), "mean_net": gate_t(n, dd),
        "daily_gross": sharpe_sortino(dg.to_numpy()), "daily_net": sharpe_sortino(dn.to_numpy()),
        "trade_count_sharpe_net": float(n.mean() / n.std(ddof=1) * np.sqrt(tpy)) if n.std(ddof=1) > 0 else None,
        "trade_count_sharpe_gross": float(g.mean() / g.std(ddof=1) * np.sqrt(tpy)) if g.std(ddof=1) > 0 else None,
        "daily_vol_net": float(dn.std(ddof=1)), "max_drawdown_net": max_drawdown(dn.to_numpy()),
        "mean_move_vs_2c": float(np.mean(g / (2 * tr["cost"].to_numpy(float)))),
        "breakeven_round_trip_usd": float(g.mean()),
        "breakeven_ticks_by_root": {r: float(s["gross"].mean() / ticks[r]) for r, s in tr.groupby("root")},
    }
    dist = {"count": int(n.size), "mean": float(n.mean()), "median": float(np.median(n)), "hit": float((n > 0).mean()),
            "payoff": float(n[n > 0].mean() / -n[n < 0].mean()) if (n > 0).any() and (n < 0).any() else None,
            "hold_minutes": sorted(set(tr["minutes"].astype(int))),
            "skew": float(pd.Series(n).skew()), "kurtosis": float(pd.Series(n).kurt()), "trims_net": trims(n),
            "gross_mean": float(g.mean()), "gross_median": float(np.median(g)), "trims_gross": trims(g)}
    yr = tr.groupby(tr["date"].str[:4])["net"].sum()
    order = np.argsort(-n)
    tot = n.sum()
    top = lambda k: float(n[order[:k]].sum() / tot) if tot else None  # noqa: E731
    dep = {"net_by_year": yr.to_dict(), "profitable_years": int((yr > 0).sum()), "years": int(yr.size),
           "by_era": tr.groupby("era")["net"].agg(["count", "mean"]).to_dict("index"),
           "2019_2023": float(tr.loc[tr["date"] >= SUBERA, "net"].mean()) if (tr["date"] >= SUBERA).any() else None,
           "by_tenor_leg": tr.groupby(["tenor", "leg"])["net"].agg(["count", "mean"]).reset_index()
           .to_dict("records"),
           "new_vs_reopening": tr.groupby("reopening")["net"].agg(["count", "mean"]).to_dict("index"),
           "price_tercile": tr.groupby(pd.qcut(tr["price"], 3, labels=["low", "mid", "high"]), observed=True)["net"]
           .agg(["count", "mean"]).to_dict("index") if len(tr) >= 9 else None,
           "ex_2020": float(tr.loc[~tr["date"].str.startswith("2020"), "net"].mean()),
           "ex_2022": float(tr.loc[~tr["date"].str.startswith("2022"), "net"].mean()),
           "top_share_1_5_10": [top(1), top(5), top(10)],
           "top5_trades": tr.iloc[order[:5]][["date", "tenor", "leg", "net"]].to_dict("records")}
    return {"performance": perf, "distribution": dist, "dependencies": dep}


def leg_null(tr: pd.DataFrame, res: dict, panels: dict, costs: dict, col: str) -> dict:
    """N1 on the leg schedule: each traded leg moved to Q_root[(p_e + j) mod |Q|], scored there (nanmean)."""
    rcs = res["rcs"]
    offs = n1_offsets(rcs, sorted(set(tr["root"])))
    vals = {}
    for r in set(tr["root"]):
        la = leg_gross_arrays(panels[r], costs[r]["usd_per_point"])
        for leg in LEGS:
            v = la[leg]["gross"] - (costs[r]["cost_rt"] if col == "net" else 0.0)
            vals[(r, leg)] = v
    Z = np.empty((offs.size, len(tr)))
    for e, (r, d, leg) in enumerate(zip(tr["root"], tr["date"], tr["leg"])):
        q = rcs[r].Q
        pe = int(np.searchsorted(panels[r].days[q], d, side="right"))
        Z[:, e] = vals[(r, leg)][q[(pe + offs) % q.size]]
    stat = np.nanmean(Z, axis=1)
    cnt = np.isfinite(Z).sum(axis=1)
    res_ = qtiles(stat, float(tr[col].mean()))
    res_["count_range"] = [int(cnt.min()), int(np.median(cnt)), int(cnt.max())]
    return res_


def always_on_control(tr: pd.DataFrame, panels: dict, costs: dict) -> dict:
    """The same legs, same clock, on each trade's two matched control days."""
    vals = []
    arr = {r: leg_gross_arrays(panels[r], costs[r]["usd_per_point"]) for r in set(tr["root"])}
    for r, leg, c1, c2 in zip(tr["root"], tr["leg"], tr["c1"], tr["c2"]):
        la = arr[r][leg]["gross"]
        for c in (c1, c2):
            i = np.searchsorted(panels[r].days, c)
            vals.append(la[i])
    v = np.array(vals)
    return {"mean_gross_on_control_days": float(np.nanmean(v)), "n": int(np.isfinite(v).sum())}


def stage2(res: dict, panels: dict, costs: dict, calendar_days: np.ndarray, years: float) -> dict:
    import backtest_framework.validation.filter_oracle as FO
    tr = build_trades(res, panels, costs)
    out: dict[str, Any] = {"trades_total": int(len(tr))}
    if tr.empty:
        return out
    U = tr
    F = tr[tr["take_F"]]
    dU = U["date"].to_numpy(str)
    g1 = gate_t(U["gross"].to_numpy(float), dU)
    n1U = leg_null(U, res, panels, costs, "gross")
    out["book_U"] = {**book_report(U, calendar_days, costs, years), "N1_gross": n1U,
                     "N4_gross": n4_signflip(U["gross"].to_numpy(float), dU),
                     "always_on_control": always_on_control(U, panels, costs),
                     "gate1": {"mean_gross_positive": bool(g1["mean"] > 0), "t_ge_2": bool(g1["t_gate"] >= 2),
                               "above_N1_p95": bool(g1["mean"] > n1U["p95"])}}
    out["book_U"]["gate1"]["pass"] = all(out["book_U"]["gate1"].values())
    if not F.empty:
        gF = gate_t(F["net"].to_numpy(float), F["date"].to_numpy(str))
        out["book_F"] = {**book_report(F, calendar_days, costs, years), "N1_net": leg_null(F, res, panels, costs, "net"),
                         "gate2": {"n": int(len(F)), "mean_net_positive": bool(gF["mean"] > 0),
                                   "t_ge_2": bool(gF["t_gate"] >= 2)}}
        out["book_F"]["gate2"]["verdict"] = ("UNRESOLVED" if len(F) < 60 else
                                            "PASS" if gF["mean"] > 0 and gF["t_gate"] >= 2 else "FAIL")
    out["filter_oracle"] = {"oracle_take_rate": float(FO.oracle_take(tr["net"].to_numpy(float)).mean()),
                            "calibration": FO.calibration(tr["projected"].to_numpy(float), tr["gross"].to_numpy(float),
                                                          n_bins=min(10, max(2, len(tr) // 20))),
                            "assess": FO.assess(tr["projected"].to_numpy(float), tr["take_F"].to_numpy(bool),
                                                tr["gross"].to_numpy(float), tr["net"].to_numpy(float))}
    post = tr[(tr["leg"] == "post")]
    conf = post[(post["rpre_bp"] < 0) & (post["pd_share"] >= post["pd_trailing_median"])]
    out["secondary_post_confirmation"] = {"n": int(len(conf)), "mean_gross": float(conf["gross"].mean()) if len(conf) else None,
                                          "mean_net": float(conf["net"].mean()) if len(conf) else None,
                                          "all_post_mean_gross": float(post["gross"].mean()) if len(post) else None,
                                          "N1_gross": leg_null(conf, res, panels, costs, "gross") if len(conf) > 5 else None}
    verdict = ("SUPPORTED" if out["book_U"]["gate1"]["pass"] and out.get("book_F", {}).get("gate2", {}).get("verdict") == "PASS"
               else "MECHANISM ONLY" if out["book_U"]["gate1"]["pass"] else "NOT SUPPORTED")
    out["verdict"] = verdict
    out["_trades"] = tr
    return out


def measured_ticks(panels: dict) -> dict:
    out = {}
    for r, p in panels.items():
        yrs = {}
        for y in sorted({d[:4] for d in p.days}):
            m = np.char.startswith(p.days.astype(str), y)
            x = p.price[m]
            dfx = np.abs(np.diff(x, axis=1))
            dfx = dfx[np.isfinite(dfx) & (dfx > 1e-9)]
            yrs[y] = float(dfx.min()) if dfx.size else None
        out[r] = yrs
    return out


def component_line(tr: pd.DataFrame, series: dict, costs: dict) -> dict:
    lo, hi = COMPONENT_WINDOW
    days = series["calendar"][(series["calendar"] >= lo) & (series["calendar"] <= hi)]
    t = tr[(tr["date"] >= lo) & (tr["date"] <= hi)]
    dn = daily_series(t, days, "net")
    dg = daily_series(t, days, "gross")
    out = {"window": [lo, hi], "net": sharpe_sortino(dn.to_numpy()), "gross": sharpe_sortino(dg.to_numpy()),
           "net_sharpe_se_block_bootstrap": block_bootstrap_sharpe_se(dn),
           "hit": float((t["net"] > 0).mean()) if len(t) else None,
           "skew_daily_net": float(dn.skew()), "daily_sigma_usd": float(dn.std(ddof=1)),
           "C_d_daily_sigma_le_500": bool(dn.std(ddof=1) <= 500), "trades": int(len(t))}
    rho = {}
    for name, s in series.get("components", {}).items():
        common = dn.index.intersection(s.index)
        if len(common) > 30:
            rho[name] = {"rho": float(np.corrcoef(dn.loc[common].to_numpy(), s.loc[common].to_numpy())[0, 1]),
                         "days": int(len(common)), "from": str(common.min()), "to": str(common.max())}
    out["rho"] = rho
    return out


def _load_module(name: str, fn: str):
    """Load a sibling script once (reusing sys.modules, as D707's own _load does, so a path patched here is the one
    every later loader sees)."""
    import importlib.util
    if name in sys.modules:
        return sys.modules[name]
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


KNOWN_F2 = {"trades": 252, "mean_net": 13.208968}


def component_series_real(dr: Path) -> dict:
    """The admitted MACD arm (#2) and F2 (#4), each built from inputs cut below 2024-01-01 (design section 9), with
    every fixture path pointed at `dr` so the build runs from a worktree (D709's load_components move).
    Known answers asserted: the arm's 2016-2023 per-year totals equal D504's; F2 is 252 trades at +$13.208968."""
    fx = Path(dr) / "fixtures"
    # D618's loader (under F2's frame) resolves its fixtures under its own REPO; point them at the data root. It must be
    # registered as "m618" BEFORE D707 loads it, because D707's _load reuses sys.modules.
    m618 = _load_module("m618", "stage0_d618_sharpened_ladder.py")
    m618.FIX = fx
    m618.OPTS, m618.CUTS, m618.ES_1M = fx / "fut_es_options_eod.csv.gz", fx / "fut_es_0dte_volume_cutoffs.csv.gz", \
        fx / "fut_ES_rth_1m.csv.gz"
    m618.STRIP, m618.SESSIONS = fx / "fut_settle_strip.csv.gz", fx / "fut_index_sessions.csv.gz"
    D484 = _load_module("d484c710", "d484_offdiagonal_and_macd.py")
    D491 = _load_module("d491c710", "d491_conditional_hold.py")
    D495 = _load_module("d495c710", "d495_agree_confluence.py")
    D504 = _load_module("d504c710", "d504_arm_full_history.py")
    D495.FIX = fx / "fut_sessions_hourly.csv.gz"
    for p in (m618.ES_1M, m618.SESSIONS, D495.FIX):
        chk(Path(p).exists(), f"[COMPONENTS] missing fixture {p}")
    meta = json.loads(D495.META.read_text(encoding="utf-8"))
    spec = json.loads(D484.SPECS.read_text(encoding="utf-8"))
    frame = pd.read_csv(D495.FIX, encoding="utf-8")
    frame = frame[frame["day"].astype(str) < RESERVED]
    assert_window(frame["day"].astype(str).to_numpy(), "the arm's hourly input")
    pk = D504.build(frame, meta, spec)
    days = np.asarray(pk["days"]).astype(str)
    m = days >= D504.USABLE_LO
    net, _ = D491.simulate(pk["O"][m], pk["C"][m], pk["AGREE"][m], pk["first"], D504.M_HOLD, pk["cost"], pk["tick_pts"])
    arm = pd.Series(net * pk["tick_usd"], index=days[m])
    assert_window(arm.index.to_numpy(str), "the arm's daily net")
    per = json.loads((REPO / "data" / "d504_arm_full_history.json").read_text(encoding="utf-8"))["per_year"]
    for y in range(2016, 2024):
        got = float(arm[arm.index.str.startswith(str(y))].sum())
        chk(abs(got - per[str(y)]["total_usd"]) < 0.01,
            f"[ARM] {y}: the sealed rebuild gives ${got:,.2f}, D504 recorded ${per[str(y)]['total_usd']:,.2f} -- "
            f"the arm's build reads ahead of its own day")
    # F2 through D707's frozen build (as D709 does): D707's frame() raises if a session or bar >= 2024-01-01 is read
    m707 = _load_module("d707r", "vault_d707_last_hour_f2.py")
    X = m707.frame()
    assert_window(X.index.to_numpy(str), "F2's candidate frame")
    F = m707.f2(X)
    ans = m707.in_sample_answer(X, F)
    chk(ans["trades"] == KNOWN_F2["trades"] and abs(ans["mean_net"] - KNOWN_F2["mean_net"]) < 1e-6,
        f"[F2] not reproduced: {ans['trades']} trades at {ans['mean_net']:+.6f}, D705/D707 recorded "
        f"{KNOWN_F2['trades']} at {KNOWN_F2['mean_net']:+.6f}")
    sess = X.index.to_numpy(str)
    g = X["gross"].to_numpy(float)
    span = F["window"]
    f2 = pd.Series(np.where(F["take"] & span, g - m707.COST, 0.0), index=sess)[span]
    return {"components": {"#2 MACD arm": arm, "#4 F2": f2},
            "known_answers": {"arm_per_year_2016_2023_usd": {str(y): round(float(arm[arm.index.str.startswith(str(y))]
                                                                                 .sum()), 2) for y in range(2016, 2024)},
                              "F2": ans}}


def components_only(dr: Path) -> int:
    """Build the component series and assert their known answers. No Treasury bar is loaded."""
    t0 = time.time()
    P(f"D710 --components-only: data root {dr} (no Treasury bar price is read)")
    s = component_series_real(dr)
    for k, v in s["components"].items():
        P(f"  {k}: {len(v)} sessions {v.index.min()} .. {v.index.max()}, total ${float(v.sum()):,.2f}, "
          f"traded days {int((v != 0).sum())}")
    P(f"  arm per year (= D504's 2016-2023 totals to the cent): {s['known_answers']['arm_per_year_2016_2023_usd']}")
    f = s["known_answers"]["F2"]
    P(f"  F2: {f['trades']} trades at {f['mean_net']:+.6f} a trade (known {KNOWN_F2['trades']} at "
      f"{KNOWN_F2['mean_net']:+.6f}); window from {f['first_window_session']}")
    P(f"components-only: PASS in {time.time() - t0:.0f} s")
    return 0


# ================================================================================ the lag audit (second implementation)
def audit_loop(bars: pd.DataFrame, calx: dict, pairs, cfg: Cfg) -> list[dict]:
    """A plain loop over events reading bars through a dict. It never calls asof, root_calc, score_events or
    event_table, and must reproduce the vectorised events exactly (prices, controls, sigma) and Delta to 1e-9 bp."""
    B: dict = {}
    flags: dict = {}
    # the session flags from every (root, day, contract) the day holds; the prices only in the minutes an anchor
    # can read (each anchor and the STALE minutes before it) -- the whole 1-minute fixture would not fit a dict
    fl = bars[["root", "day", "contract", "same_front", "present"]].drop_duplicates()
    for r, d, c, sf, pr in zip(fl["root"], fl["day"], fl["contract"], fl["same_front"], fl["present"]):
        f = flags.setdefault((r, d), [set(), bool(sf), bool(pr)])
        f[0].add(c)
    readable = sorted({a - k for a in cfg.anchors for k in range(STALE + 1) if a - k >= 0})
    sub = bars[bars["bar"].isin(readable)]
    for r, c, d, b, cl in zip(sub["root"], sub["contract"], sub["day"], sub["bar"], sub["close"]):
        B[(r, d, int(b))] = (float(cl), c)
    cal = calx["auctions"]
    live = [a for a in cal.to_dict("records") if a["small_value_test"] != "True"]
    adays = {a["auction_date"] for a in live}
    sessions: dict = {}
    for (r, d) in flags:
        sessions.setdefault(r, []).append(d)
    for r in sessions:
        sessions[r].sort()

    def price_at(r, d, bar):
        for k in range(0, STALE + 1):
            if bar - k < 0:
                break
            v = B.get((r, d, bar - k))
            if v is not None:
                return v[0]
        return None

    def eligible(r, d):
        f = flags[(r, d)]
        frm = cfg.zt_from if r == "ZT" else ROOT_FROM[r]
        return (d >= frm and f[1] and len(f[0]) == 1 and f[2] and (r, d) not in calx["early"] and d not in REJECTED
                and d not in calx["fomc"] and not (cfg.exclude_dysfunction and DYSFUNCTION[0] <= d <= DYSFUNCTION[1]))

    def vrow(r, d):
        ps = [price_at(r, d, b) for b in cfg.anchors]
        if any(x is None or x <= 0 for x in ps):
            return None
        lp = np.log(np.array(ps))
        rpre = (lp[1] - lp[0]) * 1e4
        rpost = (lp[3] - lp[2]) * 1e4
        return ps, rpost - rpre

    clean: dict = {}
    for r, ds in sessions.items():
        clean[r] = []
        for d in ds:
            if eligible(r, d) and d not in adays:
                v = vrow(r, d)
                if v is not None:
                    clean[r].append((d, v[1]))
    out = []
    dur_days: dict = {}
    for a in live:
        if a["kind"] in ("NOMINAL", "TIPS"):
            dur_days[a["auction_date"]] = dur_days.get(a["auction_date"], 0) + 1
    for tenor, r in pairs:
        if r not in sessions:
            continue
        for a in live:
            if a["kind"] != "NOMINAL" or a["tenor"] != tenor or a["close_comp_et"] != "13:00":
                continue
            d = a["auction_date"]
            if cfg.exclude_shared and dur_days.get(d, 0) > 1:
                continue
            if (r, d) not in flags or not eligible(r, d):
                continue
            v = vrow(r, d)
            if v is None:
                continue
            prior = [x for (dd, x) in clean[r] if dd < d]
            if len(prior) < SIGMA_N:
                continue
            sigma = float(np.std(np.array(prior[-SIGMA_N:]), ddof=1))
            t1 = (date.fromisoformat(d) - timedelta(days=7)).isoformat()
            t2 = (date.fromisoformat(d) + timedelta(days=7)).isoformat()
            before = [(dd, x) for (dd, x) in clean[r] if dd <= t1]
            after = [(dd, x) for (dd, x) in clean[r] if dd >= t2]
            if not before or not after:
                continue
            if (date.fromisoformat(t1) - date.fromisoformat(before[-1][0])).days > CTRL_MAXGAP:
                continue
            if (date.fromisoformat(after[0][0]) - date.fromisoformat(t2)).days > CTRL_MAXGAP:
                continue
            D = v[1] - 0.5 * (before[-1][1] + after[0][1])
            g = sorted((x for x in live if x["kind"] == "NOMINAL" and x["tenor"] == tenor and x["auction_date"] < d
                        and x["pd_share"]), key=lambda x: x["auction_date"])
            tm = float(np.median([float(x["pd_share"]) for x in g[-12:]])) if len(g) >= 12 else float("nan")
            out.append({"tenor": tenor, "root": r, "date": d, "anchors": v[0], "c1": before[-1][0], "c2": after[0][0],
                        "sigma_bp": sigma, "D_bp": D, "pd_trailing_median": tm})
    return out


def lag_audit(res: dict, bars: pd.DataFrame, calx: dict, pairs, cfg: Cfg) -> dict:
    loop = audit_loop(bars, calx, pairs, replace(cfg, sigma_includes_today=False, trailing_includes_current=False))
    evk = res["events"]
    vec = {(e.tenor, e.root, e.date): e for e in evk.itertuples(index=False)}
    lp = {(x["tenor"], x["root"], x["date"]): x for x in loop}
    chk(set(vec) == set(lp), f"[LAG AUDIT] the event sets differ: {len(set(vec) - set(lp))} only vectorised, "
                             f"{len(set(lp) - set(vec))} only in the loop")
    worst = 0.0
    for k, x in lp.items():
        e = vec[k]
        a = tuple(res["rcs"][e.root].anchors[e.i])
        chk(tuple(x["anchors"]) == a, f"[LAG AUDIT] {k}: anchor prices differ {x['anchors']} vs {a}")
        chk((x["c1"], x["c2"]) == (e.c1, e.c2), f"[LAG AUDIT] {k}: controls differ")
        chk(x["sigma_bp"] == e.sigma_bp, f"[LAG AUDIT] {k}: sigma differs {x['sigma_bp']} vs {e.sigma_bp}")
        worst = max(worst, abs(x["D_bp"] - e.D_bp))
        chk(abs(x["D_bp"] - e.D_bp) <= 1e-9, f"[LAG AUDIT] {k}: Delta differs by {abs(x['D_bp'] - e.D_bp)} bp")
        tm_v, tm_l = e.pd_trailing_median, x["pd_trailing_median"]
        chk((np.isnan(tm_v) and np.isnan(tm_l)) or tm_v == tm_l, f"[LAG AUDIT] {k}: trailing PD median differs")
    return {"events": len(lp), "max_abs_delta_diff_bp": worst, "pass": True}


# ================================================================================ right quantity
def right_quantity(res: dict, panels: dict, calx: dict):
    evk, rcs = res["events"], res["rcs"]
    adays = auction_days(calx["auctions"])
    # (i) the 13:05 post return differs from the 13:00 one: the release jump is excluded
    d13 = []
    for e in evk.itertuples(index=False):
        p = panels[e.root]
        a0, a3 = asof(p.price[e.i:e.i + 1], 239)[0], asof(p.price[e.i:e.i + 1], 419)[0]
        d13.append((math.log(a3) - math.log(a0)) * 1e4 - e.rpost_bp)
    chk(np.nanmax(np.abs(d13)) > 0, "[RIGHT QTY] the 13:05 post return equals the 13:00 one on every event")
    # (ii) Delta is not the raw event-day V
    chk(not np.allclose(evk["D_bp"], evk["V_bp"]), "[RIGHT QTY] Delta equals the raw event V: controls not subtracted")
    # (iii) no control is an auction, FOMC or ineligible (roll) day
    for e in evk.itertuples(index=False):
        for c in (e.c1, e.c2):
            chk(c not in adays and c not in calx["fomc"], f"[RIGHT QTY] control {c} is an auction or FOMC day")
            j = np.searchsorted(panels[e.root].days, c)
            chk(bool(rcs[e.root].elig[j]), f"[RIGHT QTY] control {c} is an ineligible (roll/early/rejected) session")
    # (iv) every window inside one contract
    for e in evk.itertuples(index=False):
        chk(e.contract != "MIXED" and panels[e.root].same_front[e.i], f"[RIGHT QTY] {e.date} {e.root} spans a roll")
    # (v) T recomputed from its formula matches the design's table at 2.5%
    for k, v in T_TABLE_25.items():
        chk(abs(transfer(*k, 0.025) - v) < 0.0006, f"[RIGHT QTY] T{k} = {transfer(*k, 0.025):.4f}, design says {v}")
    return {"post_13_00_vs_13_05_max_abs_bp": float(np.nanmax(np.abs(d13))), "pass": True}


# ================================================================================ the run
def to_jsonable(o):
    if isinstance(o, dict):
        return {str(k): to_jsonable(v) for k, v in o.items() if not str(k).startswith("_") and k != "rcs"}
    if isinstance(o, (list, tuple)):
        return [to_jsonable(v) for v in o]
    if isinstance(o, pd.DataFrame):
        return None
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return o


def run(dr: Path) -> int:
    t0 = time.time()
    P(f"D710 run: data root {dr}")
    # runs from a worktree: every fixture (Treasury bars, the session calendar, and the component builders' inputs,
    # whose paths component_series_real points at the data root) is read from `dr`; every output goes to THIS
    # checkout's data/. Refuse up front rather than after the premise.
    need = [dr / "fixtures" / f for f in ("fut_day1m.parquet", "cme_session_calendar.csv.gz", "fut_ES_rth_1m.csv.gz",
                                          "fut_index_sessions.csv.gz", "fut_sessions_hourly.csv.gz")]
    need += [tracked("calendar", f) for f in ("treasury_auctions.csv", "events.csv", "fomc_2010_2015.csv")]
    missing = [str(p) for p in need if not p.exists()]
    chk(not missing, f"[PREFLIGHT] missing inputs: {missing}")
    P(f"  outputs go to {REPO / 'data'}")
    bars = load_bars(dr)
    calx = load_calendars(dr)
    panels = build_panels(bars)
    costs = costs_table()
    cfg = Cfg()
    res = premise(panels, calx, cfg)
    la = lag_audit(res, bars, calx, PRIMARY, cfg)
    rq = right_quantity(res, panels, calx)
    out = {"record": "D710", "window": [SPAN_LO, "2023-12-29"], "lag_audit": la, "right_quantity": rq,
           "verdict": res["verdict"], "gates": res["gates"], "pooled": res["pooled"], "pooled_E2": res["pooled_E2"],
           "achieved_share_full": res["achieved_share_full"], "achieved_share_E2": res["achieved_share_E2"],
           "literal_T1": res["literal_T1"], "N1": res["N1"], "N1_E2": res.get("N1_E2"), "N2": res["N2"],
           "N3_placebo11": res["N3_placebo11"], "N4": res["N4"], "pairs": pair_table(res["events"]),
           "predictions": predictions(res), "drops": res["drops"], "root_exclusions": res["root_exclusions"],
           "events_in_delivery_window": int(res["events"]["in_delivery_window"].sum())}
    sens = {}
    for name, c in (("shared_day_13h_included", replace(cfg, exclude_shared=False)),
                    ("march_2020_included", replace(cfg, exclude_dysfunction=False)),
                    ("ZT_from_2019", replace(cfg, zt_from="2019-01-01"))):
        s = premise(panels, calx, c, with_nulls=False, with_placebo=False)
        sens[name] = {"pooled": s["pooled"], "achieved_share_full": s["achieved_share_full"],
                      "achieved_share_E2": s["achieved_share_E2"]}
    out["sensitivities"] = sens
    sec = premise(panels, calx, cfg, pairs=SECONDARY, with_nulls=False, with_placebo=False)
    out["secondary_pairs"] = pair_table(sec["events"]) if not sec["events"].empty else {}
    out["measured_tick_points_by_year"] = measured_ticks(panels)
    if res["verdict"] == "PRESENT":
        cal_days = np.unique(np.concatenate([p.days for p in panels.values()]))
        yrs = (date.fromisoformat("2023-12-29") - date.fromisoformat(SPAN_LO)).days / 365.25
        s2 = stage2(res, panels, costs, cal_days, yrs)
        series = component_series_real(dr)
        series["calendar"] = np.unique(np.concatenate([panels["ZN"].days, panels["ZF"].days]))
        s2["component_known_answers"] = series["known_answers"]
        s2["component_line_U"] = component_line(s2["_trades"], series, costs)
        if s2.get("book_F"):
            s2["component_line_F"] = component_line(s2["_trades"][s2["_trades"]["take_F"]], series, costs)
        out["stage2"] = s2
        s2["_trades"].to_csv(REPO / "data" / "d710_trades.csv.gz", index=False, encoding="utf-8")
    else:
        out["stage2"] = {"ran": False, "why": f"premise verdict {res['verdict']}: the study goes no further (design 7)"}
    ev = res["events"].drop(columns=["i"])
    assert_window(ev["date"].to_numpy(str), "the events file")
    ev.to_csv(REPO / "data" / "d710_events.csv.gz", index=False, encoding="utf-8")
    out["runtime_min"] = round((time.time() - t0) / 60, 2)
    (REPO / "data" / "stage0_d710_auction_v.json").write_text(json.dumps(to_jsonable(out), indent=1) + "\n",
                                                              encoding="utf-8")
    P(f"verdict {res['verdict']}; pooled z {res['pooled']['mean']:+.4f} (t {res['pooled']['t_gate']:+.2f}); "
      f"N1 p95 {res['N1']['p95']:+.4f}; share full {res['achieved_share_full']:.2f} E2 {res['achieved_share_E2']:.2f}")
    return 0


# ================================================================================ the self-test
def business_days(lo: str, hi: str) -> list[str]:
    d, e = date.fromisoformat(lo), date.fromisoformat(hi)
    out = []
    while d <= e:
        if d.weekday() < 5 and not (d.month == 12 and d.day == 25) and not (d.month == 1 and d.day == 1):
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def synth_calendar(lo: str, hi: str, days: list[str]) -> pd.DataFrame:
    """Monthly auctions on business days: 2/5/7 on three consecutive days of the last full week, 3/10/30 in the
    second week, 20y mid-month from 2020-05, a TIPS and an FRN; plus two shared days and an 11:30 close."""
    dset = sorted(days)
    rows = []
    rng = np.random.default_rng(3)
    by_month: dict = {}
    for d in dset:
        by_month.setdefault(d[:7], []).append(d)

    def add(d, kind, tenor, close="13:00"):
        rows.append({"auction_date": d, "close_comp_et": close, "kind": kind, "tenor": tenor,
                     "small_value_test": "False", "high_yield": "2.5", "reopening": "No",
                     "cusip": f"{kind}{tenor}{d}", "pd_share": f"{rng.uniform(0.2, 0.6):.6f}"})
    for ym, ds in sorted(by_month.items()):
        if len(ds) < 18:
            continue
        add(ds[6], "NOMINAL", "3y"); add(ds[7], "NOMINAL", "10y"); add(ds[8], "NOMINAL", "30y")
        add(ds[-7], "NOMINAL", "2y"); add(ds[-6], "NOMINAL", "5y")
        # in May and November the 7y falls on the month's second-to-last session: the first position day of the
        # Jun/Dec contract, so the delivery-window rule is exercised
        add(ds[-2] if ym[5:] in ("05", "11") else ds[-5], "NOMINAL", "7y")
        add(ds[-6], "FRN", "2y", "11:30")
        add(ds[12], "TIPS", "10y")
        if ym >= "2020-05":
            add(ds[11], "NOMINAL", "20y")
    for ym in ("2012-06", "2017-06"):
        if ym in by_month:
            add(by_month[ym][7], "NOMINAL", "3y", "11:30")      # a shared day: 3y 11:30 + 10y 13:00
    if "2018-02" in by_month:
        add(by_month["2018-02"][3], "NOMINAL", "5y", "11:30")    # a non-13:00 close on its own day
    cal = pd.DataFrame(rows)
    return cal[(cal["auction_date"] >= lo) & (cal["auction_date"] <= hi)].reset_index(drop=True)


def synth_contract(root: str, d: str, month_last: dict) -> tuple[str, bool]:
    """The fixture's convention: the front rolls ON the last session of Feb/May/Aug/Nov (first notice day), which is
    itself a roll session (same_front False)."""
    y, mon = int(d[:4]), int(d[5:7])
    roll = mon in (2, 5, 8, 11) and d == month_last[d[:7]]
    m = mon + 3 if mon % 3 == 0 else mon + (3 - mon % 3)
    if roll:
        m += 3
    if m > 12:
        m, y = m - 12, y + 1
    return f"{root}{'HMUZ'[m // 3 - 1]}{y % 10}", not roll


def synth(seed: int, plant: float, lo: str = SPAN_LO, hi: str = "2023-12-29", roots=("ZT", "ZF", "ZN", "UB"),
          jump_bp: float = 3.0, drop_frac: float = 0.01) -> tuple[pd.DataFrame, dict]:
    """Bars only at the minutes the runner reads; a random walk whose volatility drifts slowly; on event days a
    planted concession of plant x (T x Vcash x pre share) spread over 10:00->13:00 and its reversal over 13:05->16:00,
    plus a release jump inside 13:00->13:05 that the 13:05 start must exclude."""
    rng = np.random.default_rng(seed)
    days = business_days(lo, hi)
    cal = synth_calendar(lo, hi, days)
    tens = cal[(cal["kind"] == "NOMINAL") & (cal["tenor"] == "10y")]["auction_date"]
    fomc = {d for d in tens if d[5:7] in ("01", "06")}             # two 10y events a year sit on FOMC days
    month_last: dict = {}
    for d in days:
        month_last[d[:7]] = d
    ev_by_root: dict = {}
    for t, r in PRIMARY:
        for d in cal[(cal["kind"] == "NOMINAL") & (cal["tenor"] == t)]["auction_date"]:
            ev_by_root.setdefault(r, {})[d] = t
    need = np.array(sorted({b for a in ANCH.values() for b in a} | {b for v in LEGS.values() for b in v[:2]}))
    level = {"ZT": 108.0, "ZF": 118.0, "ZN": 125.0, "TN": 130.0, "ZB": 150.0, "UB": 170.0}
    prevb = np.concatenate([[0], need[:-1]])
    dt = np.maximum(need - prevb, 1).astype(float)
    ov = lambda a0, a1: np.clip(np.minimum(need, a1) - np.maximum(prevb, a0), 0, None)  # noqa: E731
    f_pre, f_post = ov(59, 239) / 180, ov(244, 419) / 175
    jump_col = (prevb >= 239) & (prevb < 244) & (need >= 244)
    n, m = len(days), need.size
    # slow volatility regimes, and mid-week sessions (when auctions are held) 30% noisier than Mon/Fri, so the
    # calibration check sees the nuisance a rotation null could mishandle
    wdf = np.array([1.3 if date.fromisoformat(d).weekday() in (1, 2, 3) else 0.8 for d in days])
    vol = 0.08 * (1 + 0.5 * np.sin(2 * np.pi * np.arange(n) / 400)) * wdf
    cons = [synth_contract("", d, month_last) for d in days]
    frames = []
    for r in roots:
        evr = ev_by_root.get(r, {})
        is_ev = np.array([d in evr for d in days])
        V = np.array([transfer(evr[d], r, 0.025) * VCASH[era(d)][evr[d]] * plant if d in evr else 0.0 for d in days])
        sh = np.array([PRE_SHARE[evr[d]] if d in evr else 0.0 for d in days])
        inc = rng.normal(0, 1, (n, m)) * vol[:, None] * np.sqrt(dt)[None, :]
        inc += -(V * sh)[:, None] * f_pre[None, :] + (V * (1 - sh))[:, None] * f_post[None, :]
        inc[:, jump_col] += (rng.normal(0, jump_bp, n) * is_ev)[:, None]
        full = np.concatenate([inc, rng.normal(0, 0.5, (n, 1))], axis=1)          # + the overnight
        lp = np.cumsum(full.ravel()).reshape(n, m + 1)[:, :m]
        keep = (rng.random((n, m)) >= drop_frac) | np.isin(need, (59, 239, 244, 419))[None, :]
        di, bj = np.nonzero(keep)
        frames.append(pd.DataFrame({"root": r, "contract": [r + cons[i][0] for i in di], "day": np.array(days)[di],
                                    "bar": need[bj], "close": level[r] * np.exp(lp[di, bj] / 1e4),
                                    "same_front": np.array([cons[i][1] for i in di]), "present": True}))
    bars = pd.concat(frames, ignore_index=True)
    calx = {"auctions": cal, "fomc": fomc, "macro": set(), "early": set()}
    return bars, calx


def expect(fn, tag: str, what: str) -> int:
    try:
        fn()
    except D710Error as e:
        chk(str(e).startswith(tag), f"{what}: raised at the wrong assertion: {str(e)[:100]}")
        P(f"    {tag} RAISES on {what}: {str(e)[:110]}")
        return 1
    raise D710Error(f"{tag} did not raise on {what}")


def selftest(K: int = 400) -> int:
    t0 = time.time()
    P("D710 selftest: synthetic bars and calendars; every assertion shown to RAISE on its broken book")
    n = 0
    cfg = Cfg()
    # ---------------------------------------------------------------- the planted V: PRESENT, share near 1
    bars, calx = synth(1, plant=1.0)
    panels = build_panels(bars, parallel=False)
    res = premise(panels, calx, cfg)
    g = res["gates"]
    P(f"  planted: {res['pooled']['n']} events, pooled z {res['pooled']['mean']:+.3f} t {res['pooled']['t_gate']:+.2f}, "
      f"N1 p95 {res['N1']['p95']:+.3f}, share {res['achieved_share_full']:.2f} / E2 {res['achieved_share_E2']:.2f}, "
      f"placebo {res['N3_placebo11']['mean']:+.3f}, verdict {res['verdict']}")
    chk(res["verdict"] == "PRESENT" and all(g.values()), f"[SELFTEST] the planted V is not PRESENT: {g}")
    ez = float(res["events"]["Ez"].mean())
    chk(abs(res["pooled"]["mean"] - ez) < 2 * res["pooled"]["se_gate"],
        f"[SELFTEST] recovered {res['pooled']['mean']:.3f} not within 2 SE of the planted {ez:.3f}")
    P(f"    recovered mean z {res['pooled']['mean']:.3f} within 2 SE of the planted {ez:.3f}")
    drops = res["drops"]
    chk(any("shared_day" in v for v in drops.values()) and any("close_not_13:00" in v for v in drops.values())
        and any("fomc" in v for v in drops.values()), f"[SELFTEST] the exclusion paths were not exercised: {drops}")
    P(f"    exclusions exercised: {drops}")
    # ---------------------------------------------------------------- chunk == whole
    pan_par = build_panels(bars, parallel=True)
    for r in panels:
        a, b = panels[r], pan_par[r]
        chk(np.array_equal(a.price, b.price, equal_nan=True) and np.array_equal(a.days, b.days)
            and np.array_equal(a.contract, b.contract), f"[CHUNK] {r}: threaded panel differs from the serial one")
    P("    [CHUNK] the threaded per-root panels equal the serial ones bit for bit")
    evk, rcs = res["events"], res["rcs"]
    offs = n1_offsets(rcs, sorted(set(evk["root"])))
    tie = {r: np.round(rcs[r].z * 4) / 4 for r in rcs}                     # tie-heavy probe
    for vals, lab in ((tie, "tie-heavy"), ({r: rcs[r].z for r in rcs}, "real")):
        vv = n1_stat_vectorised(n1_matrix(evk, panels, rcs, vals, offs))
        ll = n1_stat_loop(evk, panels, rcs, vals, offs)
        chk(np.array_equal(vv, ll), f"[CHUNK] N1 vectorised != loop on the {lab} input")
    P(f"    [CHUNK] N1's axis-wise gather equals the plain loop bit for bit ({offs.size} offsets, tie-heavy and real)")
    obs = float(np.mean(evk["z"].to_numpy(float)))
    chk(obs == res["pooled"]["mean"], "[CHUNK] the observed statistic is not the scorer's mean")
    # ---------------------------------------------------------------- the lag audit and its broken books
    la = lag_audit(res, bars, calx, PRIMARY, cfg)
    P(f"    [LAG AUDIT] the loop reproduces {la['events']} events: prices, controls, sigma exactly; "
      f"Delta to {la['max_abs_delta_diff_bp']:.1e} bp")
    broken_post = premise(panels, calx, replace(cfg, anchors=(59, 239, 239, 419)), with_nulls=False, with_placebo=False)
    n += expect(lambda: lag_audit(broken_post, bars, calx, PRIMARY, cfg), "[LAG AUDIT]",
                "a post window starting at 13:00 (straddles the release)")
    n += expect(lambda: build_trades(res, panels, costs_table(), legs={**LEGS, "pre": (60, 240, -1)}), "[STRADDLE]",
                "a pre-leg exit read after 13:00")
    n += expect(lambda: build_trades(res, panels, costs_table(), legs={**LEGS, "post": (240, 419, 1)}), "[STRADDLE]",
                "a post-leg entry before the release")
    broken_pd = premise(panels, calx, replace(cfg, trailing_includes_current=True), with_nulls=False, with_placebo=False)
    n += expect(lambda: lag_audit(broken_pd, bars, calx, PRIMARY, cfg), "[LAG AUDIT]",
                "a trailing PD-share median that includes the current auction")
    broken_sig = premise(panels, calx, replace(cfg, sigma_includes_today=True), with_nulls=False, with_placebo=False)
    # a sigma that includes the event day changes nothing on an auction day (it is never in S), so the break is
    # probed where it bites: sigma is read by the N1 pseudo-events, which ARE S days
    chk(any(not np.array_equal(broken_sig["rcs"][r].sigma, rcs[r].sigma, equal_nan=True) for r in rcs),
        "[SELFTEST] the sigma break did not change sigma")
    n += expect(lambda: sigma_audit(broken_sig, bars, calx), "[SIGMA AUDIT]", "a sigma that includes its own day")
    sigma_audit(res, bars, calx)
    P("    [SIGMA AUDIT] sigma on 40 sampled days equals np.std of the 60 prior clean V's, recomputed from raw bars")
    # ---------------------------------------------------------------- sign audit in money
    chk(leg_pnl(-1, 100.0, 99.5, 1000.0) == 500.0 and leg_pnl(+1, 100.0, 100.5, 1000.0) == 500.0
        and leg_pnl(-1, 100.0, 100.5, 1000.0) == -500.0, "[SIGN] leg P&L")
    chk(leg_pnl(-1, 100.0, 99.5, 2000.0) == 1000.0, "[SIGN] ZT's $2,000 a point")
    n += expect(lambda: sign_audit(lambda s, a, b, u: -leg_pnl(s, a, b, u)), "[SIGN]", "a flipped leg")
    sign_audit(leg_pnl)
    P("    [SIGN] a short pre-leg over a fall and a long post-leg over a rise both pay +$500 on ZN; ZT pays $2,000/pt;"
      " the inverted path loses")
    # ---------------------------------------------------------------- right quantity, window, FOMC
    rq = right_quantity(res, panels, calx)
    P(f"    [RIGHT QTY] 13:00 vs 13:05 post returns differ (max {rq['post_13_00_vs_13_05_max_abs_bp']:.2f} bp); "
      f"Delta != V; controls clean; one contract per window; T matches the design table")
    flat = dict(res)
    flat_ev = res["events"].copy()
    flat_ev["D_bp"] = flat_ev["V_bp"]
    flat["events"] = flat_ev
    n += expect(lambda: right_quantity(flat, panels, calx), "[RIGHT QTY]", "Delta equal to the raw V")
    n += expect(lambda: assert_window(np.append(bars["day"].to_numpy(str), "2024-01-02"), "bars"), "[WINDOW]",
                "a 2024 bar row")
    cal24 = pd.concat([calx["auctions"], calx["auctions"].iloc[:1].assign(auction_date="2024-01-09")])
    n += expect(lambda: assert_window(cal24["auction_date"].to_numpy(str), "calendar after the cut"), "[WINDOW]",
                "a 2024 calendar row past the cut")
    leak = dict(res)
    leak["events"] = pd.concat([res["events"], res["events"].iloc[:1].assign(date=sorted(calx["fomc"])[5])])
    n += expect(lambda: assert_no_fomc(leak["events"], calx), "[FOMC]", "an FOMC day left among the events")
    # ---------------------------------------------------------------- stage 2 on the planted data
    costs = costs_table()
    cal_days = np.unique(np.concatenate([p.days for p in panels.values()]))
    yrs = (date.fromisoformat("2023-12-29") - date.fromisoformat(SPAN_LO)).days / 365.25
    s2 = stage2(res, panels, costs, cal_days, yrs)
    tr = s2["_trades"]
    chk(len(tr) > 0 and {"pre", "post"} <= set(tr["leg"]) and not ((tr["tenor"] == "30y") & (tr["leg"] == "post")).any(),
        "[SELFTEST] stage 2 did not produce both legs with the 30y pre-only")
    dw = int(res["events"]["in_delivery_window"].sum())
    chk(dw > 0, "[SELFTEST] the synthetic calendar put no event in a delivery window")
    n += expect(lambda: build_trades(res, panels, costs, exclude_delivery=False), "[DELIVERY]",
                "a leg traded inside its contract's delivery window")
    series = {"calendar": cal_days, "components": {"#2 synthetic": pd.Series(np.random.default_rng(9).normal(0, 50, cal_days.size),
                                                                             index=cal_days)}}
    cl = component_line(tr, series, costs)
    P(f"  stage 2 (planted): {len(tr)} legs ({dw} events in a delivery window kept for the premise, excluded here); "
      f"U gross ${s2['book_U']['distribution']['gross_mean']:+.2f}, verdict {s2['verdict']}; component net Sharpe "
      f"{cl['net']['sharpe']:+.2f}, rho with a synthetic series {cl['rho']['#2 synthetic']['rho']:+.3f}")
    # ---------------------------------------------------------------- no plant: G1 fails, N1 centred
    bars0, calx0 = synth(2, plant=0.0)
    pan0 = build_panels(bars0, parallel=False)
    r0 = premise(pan0, calx0, cfg)
    P(f"  no plant: pooled z {r0['pooled']['mean']:+.4f} t {r0['pooled']['t_gate']:+.2f}; N1 p50 {r0['N1']['p50']:+.4f} "
      f"p95 {r0['N1']['p95']:+.4f}; verdict {r0['verdict']}")
    chk(abs(r0["pooled"]["t_gate"]) < 2 and not r0["gates"]["G1_exists"], "[SELFTEST] G1 passes with no effect")
    chk(abs(r0["N1"]["p50"]) < 2 * r0["pooled"]["se_gate"], "[SELFTEST] N1's p50 is not centred on zero")
    # ---------------------------------------------------------------- N1 calibration on no-effect data
    # GIL-bound per-dataset work -> processes over ks[i::W]; chunk == whole proved on the first datasets
    from concurrent.futures import ProcessPoolExecutor
    import os
    W = max(1, min(8, (os.cpu_count() or 2) - 1, K))
    ks = list(range(K))
    t_c = time.time()
    with ProcessPoolExecutor(max_workers=W) as ex:
        parts = list(ex.map(_calib_chunk, [ks[i::W] for i in range(W)]))
    got = sorted((x for part in parts for x in part), key=lambda x: x[0])
    chk([x[0] for x in got] == ks, "[CHUNK] the calibration chunks lost or repeated a dataset")
    for k in ks[:2]:
        chk(_calib_one(k) == got[k], f"[CHUNK] calibration dataset {k}: the process result differs from the serial one")
    P(f"    [CHUNK] {K} calibration datasets on {W} processes in {time.time() - t_c:.0f} s; datasets 0-1 equal their "
      f"serial recomputation exactly")
    hits = sum(int(m > p95) for _, m, p95, _ in got)
    g1hits = sum(int(g) for *_, g in got)
    rate = hits / K
    P(f"  N1 calibration: {hits} of {K} no-effect datasets beat N1's p95 ({100 * rate:.1f}%, nominal 5%); "
      f"G1 fired on {g1hits} ({100 * g1hits / K:.1f}%, one-sided nominal ~2.3%)")
    lo_, hi_ = binom_ppf(0.005, K, 0.05), binom_ppf(0.995, K, 0.05)
    chk(lo_ <= hits <= hi_, f"[SELFTEST] N1's p95 is hit {hits}/{K} times on no-effect data (99% band {lo_}..{hi_})")
    g1_hi = binom_ppf(0.995, K, 0.025)
    chk(g1hits <= g1_hi, f"[SELFTEST] G1 fires {g1hits}/{K} times on no-effect data (99% ceiling {g1_hi})")
    P(f"    99% binomial band for N1 hits at 5%: {lo_}..{hi_}; G1 ceiling {g1_hi}")
    P(f"selftest: PASS ({n} breaks raised at their own assertions) in {time.time() - t0:.0f} s")
    return 0


def _calib_one(k: int) -> tuple:
    """One no-effect dataset (2016-2023, three roots): (k, pooled mean z, N1 p95, G1 fired)."""
    bk, ck = synth(1000 + k, plant=0.0, lo="2016-01-04", hi="2023-12-29", roots=("ZF", "ZN", "UB"), jump_bp=0.0,
                   drop_frac=0.0)
    rk = premise(build_panels(bk, parallel=False), ck, Cfg(), with_placebo=False, with_n4=False)
    return (k, float(rk["pooled"]["mean"]), float(rk["N1"]["p95"]), bool(rk["gates"]["G1_exists"]))


def _calib_chunk(ks: list[int]) -> list[tuple]:
    return [_calib_one(k) for k in ks]


def binom_ppf(q: float, n: int, p: float) -> int:
    """The smallest k with P(X <= k) >= q for X ~ Binomial(n, p) (no scipy on the system interpreter)."""
    c = 0.0
    for k in range(n + 1):
        c += math.comb(n, k) * p ** k * (1 - p) ** (n - k)
        if c >= q:
            return k
    return n


def sigma_audit(res: dict, bars: pd.DataFrame, calx: dict):
    """sigma for 40 sampled scoreable days, recomputed from the raw bars with a loop (prior-only by construction)."""
    rcs = res["rcs"]
    cfg = Cfg()
    loop = {}
    for r in rcs:
        sub = bars[bars["root"] == r]
        days = sorted(set(sub["day"]))
        B = {(d, int(b)): float(c) for d, b, c in zip(sub["day"], sub["bar"], sub["close"])}

        def pr(d, bar):
            for k in range(0, STALE + 1):
                v = B.get((d, bar - k))
                if v is not None:
                    return v
            return None
        rc = rcs[r]
        dd = np.array(days)
        Sd = [d for d, s in zip(dd, rc.S) if s]
        vals = {}
        for d in Sd:
            ps = [pr(d, b) for b in cfg.anchors]
            lp = np.log(np.array(ps))
            vals[d] = ((lp[3] - lp[2]) * 1e4) - ((lp[1] - lp[0]) * 1e4)
        idx = rc.Q[:: max(1, rc.Q.size // 10)][:10]
        for i in idx:
            prior = [vals[d] for d in Sd if d < dd[i]]
            want = float(np.std(np.array(prior[-SIGMA_N:]), ddof=1))
            chk(want == rc.sigma[i], f"[SIGMA AUDIT] {r} {dd[i]}: sigma {rc.sigma[i]} != prior-only {want}")
        loop[r] = len(idx)
    return loop


def sign_audit(fn):
    chk(fn(-1, 100.0, 99.5, 1000.0) > 0, "[SIGN] a short pre-leg over a falling price does not pay")
    chk(fn(+1, 100.0, 100.5, 1000.0) > 0, "[SIGN] a long post-leg over a rising price does not pay")
    chk(fn(-1, 100.0, 100.5, 1000.0) < 0 and fn(+1, 100.0, 99.5, 1000.0) < 0, "[SIGN] the inverted path pays")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--components-only", action="store_true",
                    help="build the arm (#2) and F2 (#4) and assert their known answers; no Treasury bar is loaded")
    ap.add_argument("--data-root", type=Path, default=None)
    ap.add_argument("--calibration-datasets", type=int, default=400,
                    help="no-effect datasets in the N1 calibration check (400 is the committed setting)")
    a = ap.parse_args()
    if a.selftest:
        return selftest(a.calibration_datasets)
    if a.components_only:
        return components_only(data_root(a.data_root))
    if a.run:
        return run(data_root(a.data_root))
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
