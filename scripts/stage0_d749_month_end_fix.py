"""D749 Stage 0: the month-end London 4pm fix on M6E. Spec: docs/decisions/D749-STAGE-0-PRE-REG-the-month-end-london-fix-on-m6e.md.

    python scripts/stage0_d749_month_end_fix.py --selftest      # SYSTEM interpreter (the parquet needs pyarrow)
    python scripts/stage0_d749_month_end_fix.py --run
    uv run --no-sync python scripts/stage0_d749_month_end_fix.py --other-lines OUT.csv   # called by --run

On each month's last 6E session, 2011-2023: long (short) one M6E for the 30 minutes into the WM/Reuters fix (16:00
London = 11:00 ET, or 12:00 ET when US and UK daylight saving differ) if SPY's month-to-date return to the prior close
is positive (negative). Controls: the enumerated sign-rotation null, placebo days -5..-2, the DST clock control.
Nothing dated 2024-01-01 or later is read.
"""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import json
import math
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
MAIN_DATA = Path("C:/Users/O/Desktop/Projects/Backtest Framework/data")
SPEC = REPO / "docs" / "decisions" / "D749-STAGE-0-PRE-REG-the-month-end-london-fix-on-m6e.md"
OUT = REPO / "data" / "stage0_d749_month_end_fix.json"
SEAL, LO, HI = "2024-01-01", "2011-01-01", "2023-12-31"
BAR0 = 540                                   # fut_day1m's bar 0 starts 09:00 ET
NBAR = 420
EUR = 12500.0
LONDON, NY = ZoneInfo("Europe/London"), ZoneInfo("America/New_York")
REFORM = "2015-02-15"                        # the WMR window widened from 1 to 5 minutes
PLACEBO = (-5, -4, -3, -2)


class D749Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D749Error(msg)


# ================================================================================ the clock
def fix_et(day: str) -> int:
    """16:00 Europe/London on `day`, in ET minutes after midnight."""
    y, m, d = (int(x) for x in day.split("-"))
    t = dt.datetime(y, m, d, 16, 0, tzinfo=LONDON).astimezone(NY)
    return t.hour * 60 + t.minute


def _nth_sunday(y: int, m: int, n: int) -> dt.date:
    d = dt.date(y, m, 1)
    d += dt.timedelta(days=(6 - d.weekday()) % 7)
    return d + dt.timedelta(weeks=n - 1)


def _last_sunday(y: int, m: int) -> dt.date:
    d = dt.date(y, m + 1, 1) - dt.timedelta(days=1) if m < 12 else dt.date(y, 12, 31)
    return d - dt.timedelta(days=(d.weekday() + 1) % 7)


def fix_et_by_rule(day: str) -> int:
    """Second implementation from the statutory rules (UK: last Sunday of March to last Sunday of October; US: second
    Sunday of March to first Sunday of November), at the date level."""
    d = dt.date.fromisoformat(day)
    uk = 1 if _last_sunday(d.year, 3) <= d < _last_sunday(d.year, 10) else 0
    us = -4 if _nth_sunday(d.year, 3, 2) <= d < _nth_sunday(d.year, 11, 1) else -5
    return (16 - uk + us) * 60


# ================================================================================ inputs
def load_6e() -> dict[str, Any]:
    cols = ["root", "contract", "day", "bar", "open", "close", "same_front", "present"]
    b = pd.read_parquet(MAIN_DATA / "fixtures" / "fut_day1m.parquet", columns=cols,
                        filters=[("root", "==", "6E"), ("day", ">=", "2010-12-01"), ("day", "<", SEAL)])
    need(len(b) > 0 and (b["day"] < SEAL).all(), "seal: a 6E bar on or after 2024-01-01")
    ok = b.groupby("day")[["same_front", "present"]].all()
    days = np.array(sorted(b["day"].unique()))
    Op = b.pivot(index="day", columns="bar", values="open").reindex(index=days, columns=range(NBAR)).to_numpy(float)
    Cl = b.pivot(index="day", columns="bar", values="close").reindex(index=days, columns=range(NBAR)).to_numpy(float)
    Cf = pd.DataFrame(Cl).ffill(axis=1).to_numpy(float)
    good = (ok["same_front"] & ok["present"]).reindex(days).to_numpy(bool)
    return {"days": days, "Op": Op, "Cl": Cl, "Cf": Cf, "good": good}


def load_spy() -> tuple[list[str], dict[str, float]]:
    d = json.load(gzip.open(MAIN_DATA / "raw" / "alphavantage" / "daily" / "SPY.json.gz", "rt", encoding="utf-8"))
    keys = sorted(k for k in d if k < SEAL)
    return keys, {k: float(d[k]["4. close"]) for k in keys}


def mtd_sign(day: str, keys: list[str], close: dict[str, float], include_day: bool = False) -> float:
    """sign(SPY's close on the last day strictly before `day` / the last close of the previous month - 1). `include_day`
    (the canary) uses `day`'s own close."""
    i = int(np.searchsorted(keys, day, side="right" if include_day else "left")) - 1
    first = day[:8] + "01"
    j = int(np.searchsorted(keys, first, side="left")) - 1
    if i < 0 or j < 0 or i <= j:
        return float("nan")
    return float(np.sign(close[keys[i]] / close[keys[j]] - 1))


def mtd_sign_loop(day: str, keys: list[str], close: dict[str, float]) -> float:
    prev = [k for k in keys if k < day]
    pm = [k for k in keys if k < day[:8] + "01"]
    if not prev or not pm or prev[-1] <= pm[-1]:
        return float("nan")
    r = close[prev[-1]] / close[pm[-1]] - 1
    return 1.0 if r > 0 else (-1.0 if r < 0 else 0.0)


# ================================================================================ the trade
def window_move(X: dict[str, Any], i: int, start_min: int, end_min: int) -> float:
    """Price change from the open of the bar starting at `start_min` (or the last close before it) to the close of the
    bar starting at `end_min` - 1 (carried forward), in EUR/USD points."""
    a, e = start_min - BAR0, end_min - 1 - BAR0
    if a < 1 or e >= NBAR:
        return float("nan")
    o = X["Op"][i, a]
    entry = o if np.isfinite(o) else X["Cf"][i, a - 1]
    return float(X["Cf"][i, e] - entry)


def events(X: dict[str, Any]) -> tuple[list[int], list[int], int]:
    days = X["days"]
    ym = np.array([d[:7] for d in days])
    me, pl, dropped = [], [], 0
    for m in sorted(set(ym)):
        if m < LO[:7] or m > HI[:7]:
            continue
        idx = np.flatnonzero(ym == m)
        last = int(idx[-1])
        if X["good"][last]:
            me.append(last)
        else:
            dropped += 1
        for k in PLACEBO:
            j = last + k
            if j >= 0 and ym[j] == m and X["good"][j] and j != last:
                pl.append(j)
    return me, pl, dropped


# ================================================================================ statistics
def tstat(x: np.ndarray) -> float:
    x = x[np.isfinite(x)]
    return float(x.mean() / (x.std(ddof=1) / math.sqrt(len(x)))) if len(x) > 2 and x.std(ddof=1) > 0 else float("nan")


def welch(a: np.ndarray, b: np.ndarray) -> float:
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    se = math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return float((a.mean() - b.mean()) / se) if se > 0 else float("nan")


def book(g: np.ndarray, days: list[str], D: np.ndarray, cost: float) -> dict[str, Any]:
    n = g - cost
    k = len(n)
    srt = np.sort(n)
    cut = max(1, int(round(0.01 * k)))
    dn = math.sqrt(float(np.mean(np.minimum(n, 0) ** 2)))
    eq = np.cumsum(n)
    yrs = pd.Series(n, index=[d[:4] for d in days]).groupby(level=0).sum()
    s = pd.Series(n)
    w, l_ = n[n > 0], n[n <= 0]
    return {"trades": k, "mean_gross": float(g.mean()), "t_gross": tstat(g), "mean_net": float(n.mean()),
            "median_net": float(np.median(n)), "sharpe_net": float(n.mean() / n.std(ddof=1) * math.sqrt(12)),
            "sortino_net": float(n.mean() / dn * math.sqrt(12)) if dn > 0 else None,
            "sharpe_gross": float(g.mean() / g.std(ddof=1) * math.sqrt(12)),
            "max_dd": float((np.maximum.accumulate(np.r_[0, eq]) - np.r_[0, eq]).max()), "total_net": float(n.sum()),
            "win_rate": float((n > 0).mean()), "payoff": float(w.mean() / -l_.mean()) if len(w) and len(l_) and l_.mean() < 0 else None,
            "skew": float(s.skew()), "kurtosis": float(s.kurt()), "mean_abs_gross": float(np.abs(g).mean()),
            "mean_abs_vs_2c": float(np.abs(g).mean() / (2 * cost)), "breakeven_cost": float(g.mean()),
            "mean_ex_top1pct": float(srt[:-cut].mean()), "mean_ex_bottom1pct": float(srt[cut:].mean()),
            "mean_trimmed1pct": float(srt[cut:-cut].mean()),
            "long_mean_gross": float(g[D > 0].mean()) if (D > 0).any() else None, "long_n": int((D > 0).sum()),
            "short_mean_gross": float(g[D < 0].mean()) if (D < 0).any() else None, "short_n": int((D < 0).sum()),
            "years": {y: round(float(v), 2) for y, v in yrs.items()},
            "positive_years": f"{int((yrs > 0).sum())} of {len(yrs)}",
            "largest_year_share": float(yrs.max() / n.sum()) if n.sum() > 0 else None}


def cost_m6e() -> float:
    j = json.loads((MAIN_DATA / "futures_costs.json").read_text(encoding="utf-8"))
    m = j["roots"]["6E"]["micro"]
    c = float(m["commission_rt_usd"]["value"]) + float(m["crossing_ticks_rt"][m["default_line"]]["value"]) * float(m["tick_usd"])
    need(m["symbol"] == "M6E" and abs(c - 4.3824) < 0.001, f"the M6E cost line moved: {c}")
    return c


# ================================================================================ the other lines (uv interpreter)
def other_lines(out: Path) -> int:
    sys.path.insert(0, str(REPO / "src"))
    sys.path.insert(0, str(REPO / "scripts"))
    import stage0_d747_night_break_fade as S747
    s = S747.other_lines()
    pd.DataFrame({k: v.groupby(level=0).sum() for k, v in s.items()}).fillna(0.0).to_csv(out, encoding="utf-8")
    return 0


# ================================================================================ the run
def run() -> int:
    need(not OUT.exists(), f"{OUT.name} exists: D749 is run-once")
    t0 = time.time()
    sign_audit()
    cost = cost_m6e()
    X = load_6e()
    keys, close = load_spy()
    me, pl, dropped = events(X)
    days = X["days"]
    # the clock, both implementations, on every event and placebo day
    for i in me + pl:
        need(fix_et(days[i]) == fix_et_by_rule(days[i]), f"clock: {days[i]}")
    fx = {i: fix_et(days[i]) for i in me + pl}
    mism = [i for i in me if fx[i] == 720]
    need(len(mism) > 0, "right quantity: no daylight-saving-mismatch month-end")
    need(not set(me) & set(pl), "right quantity: a placebo day is a month-end")
    # the sign, its second implementation and its canary
    D = np.array([mtd_sign(days[i], keys, close) for i in me])
    for i, d_ in zip(me[::7], D[::7]):
        need(mtd_sign_loop(days[i], keys, close) == d_, f"lag: the sign at {days[i]} differs from the loop")
    canary = np.array([mtd_sign(days[i], keys, close, include_day=True) for i in me])
    need((canary != D).any(), "lag: the same-day-close canary changed no sign")
    Dp = np.array([mtd_sign(days[i], keys, close) for i in pl])
    # the moves (EUR/USD points -> $ at one M6E)
    P = np.array([window_move(X, i, fx[i] - 30, fx[i]) for i in me]) * EUR
    Pp = np.array([window_move(X, i, fx[i] - 30, fx[i] + 3) for i in me]) * EUR
    R = np.array([window_move(X, i, fx[i], fx[i] + 30) for i in me]) * EUR
    Pl = np.array([window_move(X, i, fx[i] - 30, fx[i]) for i in pl]) * EUR
    ok = np.isfinite(P) & np.isfinite(D) & (D != 0)
    me_ok = [i for i, k in zip(me, ok) if k]
    g, d_, ev = P[ok] * D[ok], D[ok], [days[i] for i in me_ok]
    need(not np.allclose(P[ok], R[ok]), "right quantity: P equals R")
    okp = np.isfinite(Pl) & np.isfinite(Dp) & (Dp != 0)
    gp = Pl[okp] * Dp[okp]
    # N1: the sign rotation, enumerated
    n = len(g)
    mv = P[ok]
    nul = np.array([float(np.mean(np.roll(d_, k) * mv)) for k in range(1, n)])
    # N3: the clock control on the mismatch month-ends
    mm = [k for k, i in enumerate(me_ok) if fx[i] == 720]
    at11 = np.array([window_move(X, me_ok[k], 630, 660) for k in mm]) * EUR * d_[mm]
    # eras and subsets
    pre = np.array([e < REFORM for e in ev])
    qe = np.array([e[5:7] in ("03", "06", "09", "12") for e in ev])
    res: dict[str, Any] = {
        "spec": SPEC.name, "window": [LO, HI], "seal": f"nothing on or after {SEAL}", "cost_usd": cost, "two_c": 2 * cost,
        "month_ends": len(me), "month_ends_dropped_flags": dropped, "month_ends_scored": n, "placebo_days": int(okp.sum()),
        "mismatch_month_ends": len(mm),
        "P": book(g, ev, d_, cost),
        "P_plus3": {"mean_gross": float(np.nanmean(Pp[ok] * d_)), "t": tstat(Pp[ok] * d_)},
        "R_fade_after": {"mean_gross": float(np.nanmean(-R[ok] * d_)), "t": tstat(-R[ok] * d_)},
        "O1_mean_abs_move": float(np.abs(mv).mean()), "O3_abs_move_quartiles": [float(np.quantile(np.abs(mv), q)) for q in (0.25, 0.5, 0.75)],
        "N1_rotation": {"offsets": len(nul), "score": float(g.mean()), "p50": float(np.median(nul)), "p95": float(np.percentile(nul, 95)),
                        "p": float((nul >= g.mean()).mean())},
        "N2_placebo": {"n": int(len(gp)), "mean_gross": float(gp.mean()), "t": tstat(gp), "welch_t_month_end_minus_placebo": welch(g, gp)},
        "N3_clock": {"n": len(mm), "fix_window_mean": float(g[mm].mean()) if mm else None,
                     "et_11_window_mean": float(np.nanmean(at11)) if mm else None},
        "eras": {"pre_reform": {"n": int(pre.sum()), "mean_gross": float(g[pre].mean()), "t": tstat(g[pre])},
                 "post_reform": {"n": int((~pre).sum()), "mean_gross": float(g[~pre].mean()), "t": tstat(g[~pre])}},
        "quarter_ends": {"n": int(qe.sum()), "mean_gross": float(g[qe].mean()), "t": tstat(g[qe])},
        "other_month_ends": {"n": int((~qe).sum()), "mean_gross": float(g[~qe].mean()), "t": tstat(g[~qe])},
    }
    # the component line: same-day P&L of D737's twin, NQ F2 and C1 on the event days (uv subprocess)
    tmp = REPO / "temp" / "d749_other_lines.csv"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    rc = subprocess.run(["uv", "run", "--no-sync", "python", str(Path(__file__).resolve()), "--other-lines", str(tmp)],
                        cwd=str(REPO), capture_output=True, text=True)
    if rc.returncode == 0 and tmp.exists():
        ol = pd.read_csv(tmp, index_col=0, encoding="utf-8")
        ol.index = ol.index.astype(str)
        ev_net = pd.Series(g - cost, index=ev)
        res["component_event_days"] = {c: {"same_day_net_sum": float(ol[c].reindex(ev).fillna(0).sum()),
                                           "corr_on_event_days": float(np.corrcoef(ev_net.to_numpy(), ol[c].reindex(ev).fillna(0).to_numpy())[0, 1])
                                           if ol[c].reindex(ev).fillna(0).std() > 0 else None} for c in ol.columns}
    else:
        res["component_event_days"] = {"error": (rc.stderr or "")[-400:]}
    # readings
    e = res["P"]
    no_room = res["O1_mean_abs_move"] < 2 * cost
    flow = (e["mean_gross"] > 0 and e["t_gross"] >= 2 and e["mean_gross"] > res["N1_rotation"]["p95"]
            and e["mean_gross"] > res["N2_placebo"]["mean_gross"] and res["N2_placebo"]["welch_t_month_end_minus_placebo"] >= 1.64)
    go = (flow and not no_room and e["mean_net"] > 0 and int(e["positive_years"].split(" of ")[0]) >= 8
          and e["largest_year_share"] is not None and e["largest_year_share"] < 0.5 and res["eras"]["post_reform"]["mean_gross"] > 0)
    res["readings"] = {"NO_ROOM": bool(no_room), "FLOW_PRESENT": bool(flow), "GO_to_design_with_the_principal": bool(go),
                       "reading": "NO ROOM" if no_room else ("FLOW PRESENT" if flow else "NOTHING")}
    res["runtime_min"] = round((time.time() - t0) / 60, 2)
    OUT.write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: res[k] for k in ("readings", "O1_mean_abs_move", "N1_rotation", "N2_placebo", "N3_clock", "eras")}, indent=1))
    print(json.dumps({k: res["P"][k] for k in ("trades", "mean_gross", "t_gross", "mean_net", "positive_years")}, indent=1))
    return 0


# ================================================================================ self-test
def sign_audit() -> None:
    X = {"Op": np.full((1, NBAR), 1.1000), "Cf": np.full((1, NBAR), 1.1000)}
    X["Cf"][0, 120:] = 1.1010                                # +10 pips from 11:00
    mv = window_move(X, 0, 630, 661) * EUR                   # 10:30 -> close of the 11:00 bar
    need(mv > 0 and +1 * mv > 0 and -1 * mv < 0, f"sign: a rise did not pay the long ({mv})")


def selftest() -> int:
    fails: list[str] = []
    try:
        sign_audit()
    except D749Error as e:
        fails.append(str(e))
    days = [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2011-01-01", "2023-12-31")]
    bad = [d for d in days if fix_et(d) != fix_et_by_rule(d)]
    if bad:
        fails.append(f"clock: {len(bad)} days differ, e.g. {bad[:3]}")
    if fix_et("2019-10-31") != 720 or fix_et("2019-11-29") != 660 or fix_et("2019-06-28") != 660 or fix_et("2018-03-29") != 660:
        fails.append("clock: a known date is wrong (2019-10-31 should be 12:00 ET)")
    keys, close = load_spy()
    for d in ("2015-08-31", "2020-03-31", "2023-12-29"):
        if mtd_sign(d, keys, close) != mtd_sign_loop(d, keys, close):
            fails.append(f"sign implementations differ at {d}")
    if fails:
        print("SELFTEST FAILED:", fails)
        return 1
    print("SELFTEST OK: the sign audit in money; the fix clock equals the statutory-rule implementation on every business "
          "day 2011-2023 (12:00 ET in the October mismatch week); the month-to-date sign equals its loop")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--other-lines", type=Path, default=None)
    a = ap.parse_args(argv)
    if a.other_lines is not None:
        return other_lines(a.other_lines)
    if a.selftest:
        return selftest()
    if a.run:
        return run()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
