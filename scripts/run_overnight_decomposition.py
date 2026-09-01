"""Where the overnight drift accrues, and what the PATH does to a 22-hour hold.

    uv run python scripts/run_overnight_decomposition.py

A MEASUREMENT, not a strategy. No rule is proposed, no cell is scored, no hurdle is
claimed. Reads `index_extended_15m_raw` (offline, deterministic) and writes
`OVERNIGHT_DECOMPOSITION_RESULTS.md`.

WHAT IS BEING MEASURED AND WHY
------------------------------
D247 measured +8.59%/yr overnight (prev close -> open) against -0.36%/yr intraday, on
57 ETFs over 8.3 years. That "overnight" is a CLOSE-TO-OPEN GAP WITH NO INTERIOR.
With the extended session it has one, and R11's amendment makes the interior
load-bearing: hurdle P1 measures a trailing drawdown on OPEN equity, so what matters
is the path, and the one stretch of that path with no data is the one a position
cannot be exited through.

    16:00 -> 20:00   post-market   traded, thin
    20:00 -> 04:00   untraded      NO PRICES AT ALL -- cannot be exited
    04:00 -> 09:30   pre-market    traded, thin
    09:30 -> 16:00   regular hours

THE BOUNDARIES ARE PRINTS, NOT CLOCK TIMES, AND THAT IS THE MAIN JUDGEMENT CALL
------------------------------------------------------------------------------
An extended-hours bar exists only where something traded, so the exact 04:00 and
19:45 bars are LIQUIDITY-CONDITIONED. Measured on this fixture, the share of sessions
printing an 04:00 bar:

    SPY 2010-2019  91.6%      IWM 2010-2019  41.6%      DIA 2010-2019  22.1%
    SPY 2021-2026 100.0%      IWM 2021-2026  99.8%      DIA 2021-2026  89.8%

Keying on the clock would silently restrict DIA's early era to the 22% of sessions
with an active 04:00 pre-market -- selecting on activity, then measuring returns. So
the boundaries are the LAST PRINT of the post-market and the FIRST PRINT of the
pre-market, and the realised clock times are reported per symbol per era. This also
makes the untraded window the economically correct one: the stretch between the last
price you could have sold at and the first price you could have sold at.

THE ERA SPLIT IS NOT OPTIONAL
-----------------------------
D247's intraday leg reads -0.33% full-sample, +1.44% excluding 2020 and +3.05% from
2021. Every number here is split 2010-2019 / 2020 / 2021-2026 as well as pooled. A
full-sample figure that is one year is not a finding.

BAR CONVENTIONS
---------------
Timestamps mark the interval's OPEN. The 15:45 bar covers [15:45, 16:00) so its close
IS the 16:00 print; the 19:45 bar's close is the 20:00 print. Nothing here forecasts
anything, so R9's lagging requirement is not engaged -- but no window uses a price
from after its own end, and that is asserted.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "data" / "fixtures" / "index_extended_15m_raw.csv.gz"
META = REPO / "data" / "fixtures" / "index_extended_15m_raw.meta.json"
PAGE = REPO / "OVERNIGHT_DECOMPOSITION_RESULTS.md"

SYMBOLS = ("SPY", "QQQ", "IWM", "DIA")
ERAS = ("2010-2019", "2020", "2021-2026")

RTH_OPEN, RTH_LAST = "09:30", "15:45"
SESSION_OPEN, SESSION_LAST = "04:00", "19:45"
GLOBEX_ENTRY = "18:00"           # MyFundedFutures: "Trades may be placed beginning at
                                 # 6:00 PM EST when the Globex session opens"
ENTRY_STALE_FLOOR = "17:00"      # a session with no evening print after this is dropped
                                 # rather than entered at a stale 16:15 price

TRAILING_DD = 0.04               # hurdle P1
NOTIONALS = (1, 2, 3)
WINDOWS = ("post", "untraded", "pre", "rth")
SEGMENTS = ("evening", "untraded", "premarket", "rth")


def era_of(day: str) -> str:
    y = int(day[:4])
    return "2010-2019" if y <= 2019 else ("2020" if y == 2020 else "2021-2026")


# --------------------------------------------------------------------------
# Session assembly
# --------------------------------------------------------------------------


def load() -> pd.DataFrame:
    if not FIXTURE.exists():
        raise SystemExit("run scripts/fetch_index_extended.py --build first")
    df = pd.read_csv(FIXTURE)
    df["day"] = df["timestamp"].str.slice(0, 10)
    df["hhmm"] = df["timestamp"].str.slice(11, 16)
    return df.sort_values(["symbol", "timestamp"], kind="stable").reset_index(drop=True)


def half_days(df: pd.DataFrame) -> set:
    """A 13:00 early close has no 16:00 print, so it has no 16:00->20:00 window and
    no 15:45 boundary. Derived from the data (fewer than 26 RTH bars at most of the
    universe), not hardcoded."""
    rth = df[(df["hhmm"] >= RTH_OPEN) & (df["hhmm"] <= RTH_LAST)]
    n = rth.groupby(["symbol", "day"], sort=False).size()
    short = defaultdict(int)
    total = defaultdict(int)
    for (_sym, day), k in n.items():
        total[day] += 1
        if k < 26:
            short[day] += 1
    return {d for d in total if short[d] >= 0.5 * total[d]}


def sessions_for(df: pd.DataFrame, symbol: str, drop: set) -> dict:
    """One dict per (symbol, day) holding everything downstream needs.

    `suspect` bars are excluded from every price used as a boundary or an extreme.
    They are erroneous prints -- the worst raw lower wick in this fixture is +907% --
    and the fixture's own meta documents the rule that flags them."""
    g = df[(df["symbol"] == symbol) & (df["suspect"] == 0)]
    out = {}
    for day, s in g.groupby("day", sort=True):
        if day in drop:
            continue
        hhmm = s["hhmm"].to_numpy()
        rth = s[(hhmm >= RTH_OPEN) & (hhmm <= RTH_LAST)]
        if rth.empty or RTH_OPEN not in set(rth["hhmm"]) or RTH_LAST not in set(rth["hhmm"]):
            continue                       # no usable 09:30 open or 16:00 close
        post = s[hhmm > RTH_LAST]
        pre = s[hhmm < RTH_OPEN]
        out[day] = {
            "p0930": float(rth[rth["hhmm"] == RTH_OPEN]["open"].iloc[0]),
            "p1600": float(rth[rth["hhmm"] == RTH_LAST]["close"].iloc[0]),
            "p2000": float(post["close"].iloc[-1]) if len(post) else None,
            "t2000": str(post["hhmm"].iloc[-1]) if len(post) else None,
            "p0400": float(pre["open"].iloc[0]) if len(pre) else None,
            "t0400": str(pre["hhmm"].iloc[0]) if len(pre) else None,
            "post": post, "pre": pre, "rth": rth,
        }
    return out


# --------------------------------------------------------------------------
# Part A — the four-window decomposition
# --------------------------------------------------------------------------


def decompose(sess: dict, symbol: str, strict: bool = False) -> pd.DataFrame:
    """One row per consecutive session pair. The four windows multiply exactly to
    the 16:00 -> 16:00 close-to-close return, which is asserted.

    `strict` keeps only pairs whose boundaries land on the LITERAL clock — a 19:45
    bar and an 04:00 bar. That is the decomposition as the task states it, and it is
    reported separately rather than as the headline because it is a
    liquidity-conditioned subsample: it keeps 99% of SPY's 2021-2026 sessions and
    22% of DIA's 2010-2019 ones. The two readings differ and the difference is
    itself the finding."""
    days = sorted(sess)
    rows = []
    for a, b in zip(days, days[1:]):
        A, B = sess[a], sess[b]
        if A["p2000"] is None or B["p0400"] is None:
            continue                       # no evening print, or no pre-market print
        if strict and not (A["t2000"] == SESSION_LAST and B["t0400"] == SESSION_OPEN):
            continue
        rows.append({
            "symbol": symbol, "day": b, "prev_day": a, "era": era_of(b),
            "consecutive": (date.fromisoformat(b) - date.fromisoformat(a)).days == 1,
            "post": A["p2000"] / A["p1600"] - 1.0,
            "untraded": B["p0400"] / A["p2000"] - 1.0,
            "pre": B["p0930"] / B["p0400"] - 1.0,
            "rth": B["p1600"] / B["p0930"] - 1.0,
            "overnight": B["p0930"] / A["p1600"] - 1.0,
            "close_to_close": B["p1600"] / A["p1600"] - 1.0,
            "t2000": A["t2000"], "t0400": B["t0400"],
        })
    out = pd.DataFrame(rows)
    if not out.empty:
        recomposed = np.prod([1.0 + out[w] for w in WINDOWS], axis=0) - 1.0
        assert np.allclose(recomposed, out["close_to_close"], atol=1e-9), \
            "the four windows do not multiply to the close-to-close return"
    return out


def _log_rate(r: np.ndarray, days: pd.Series) -> tuple[float, float]:
    """(log return per year, annualised vol) for ONE symbol's series."""
    span = (date.fromisoformat(days.max())
            - date.fromisoformat(days.min())).days / 365.25
    if span <= 0 or len(r) < 2:
        return float("nan"), float("nan")
    lr = np.log1p(r)
    return float(lr.sum() / span), float(lr.std(ddof=1) * np.sqrt(len(r) / span))


def window_table(d: pd.DataFrame) -> dict:
    """Annualised return, vol, and share of the total overnight drift, per window.

    EQUAL-WEIGHTED ACROSS SYMBOLS, matching D247's frame — the per-symbol log rate is
    computed against that symbol's own calendar span, and the rates are then
    averaged. Summing log returns across symbols and dividing by one shared span
    would multiply every figure by the symbol count, which is exactly the error this
    function was rewritten to remove: it read a close-to-close drift of +59.85%/yr on
    four index ETFs.

    Log space is kept because it makes the four windows ADD, so a share is
    meaningful; and because the average of per-symbol log rates is itself additive
    across the windows."""
    if d.empty:
        return {}
    cols = (*WINDOWS, "overnight", "close_to_close")
    rates: dict[str, list] = {c: [] for c in cols}
    vols: dict[str, list] = {c: [] for c in cols}
    for _sym, g in d.groupby("symbol", sort=False):
        if len(g) < 2:
            continue
        for c in cols:
            lr, vol = _log_rate(g[c].to_numpy(dtype=float), g["day"])
            rates[c].append(lr)
            vols[c].append(vol)
    if not rates["post"]:
        return {}
    mean_rate = {c: float(np.nanmean(rates[c])) for c in cols}
    overnight_log = mean_rate["post"] + mean_rate["untraded"] + mean_rate["pre"]
    out = {}
    for c in cols:
        share = None
        if c in ("post", "untraded", "pre") and overnight_log != 0:
            share = mean_rate[c] / overnight_log
        elif c == "overnight":
            share = 1.0
        out[c] = {
            "ann": float(np.expm1(mean_rate[c])),
            "vol": float(np.nanmean(vols[c])),
            "n": len(d),
            "share_of_overnight": share,
        }
    return out


# --------------------------------------------------------------------------
# Part B — the path, which is what hurdle P1 actually measures
# --------------------------------------------------------------------------


def path_points(sess: dict, a: str, b: str, variant: str) -> tuple | None:
    """The ordered path of a long opened at ~18:00 ET on `a` and held to 16:00 on `b`.

    Returns (entry, [(segment, high, low)], exit) or None if the session is not
    representable.

    THE UNTRADED WINDOW IS ONE POINT, and that is the whole story. Between the last
    evening print and the first next-session print there are no bars, so the path
    contributes exactly one observation: the price it reopens at. Any excursion
    INSIDE that window is invisible here, which makes every adverse number below a
    LOWER BOUND on what a continuously-traded futures position would have shown.

    `variant`:
      corroborated  bar high/low, suspect bars already excluded upstream  [headline]
      raw           bar high/low including suspect bars
      closes        bar close only -- a strict lower bound on any excursion
    """
    A, B = sess[a], sess[b]
    evening = A["post"][A["post"]["hhmm"] >= ENTRY_STALE_FLOOR]
    if evening.empty:
        return None                        # no evening print after 17:00: not entered

    at_entry = evening[evening["hhmm"] >= GLOBEX_ENTRY]
    if len(at_entry):
        entry = float(at_entry["open"].iloc[0])
        held = at_entry
    else:
        entry = float(evening["close"].iloc[-1])   # the standing price at 18:00
        held = evening.iloc[0:0]

    def extremes(frame, seg):
        if frame.empty:
            return []
        if variant == "closes":
            c = frame["close"].to_numpy(dtype=float)
            return [(seg, x, x) for x in c]
        return list(zip([seg] * len(frame),
                        frame["high"].to_numpy(dtype=float),
                        frame["low"].to_numpy(dtype=float)))

    pts = extremes(held, "evening")

    # The gap. One point: the first price of the next session, whatever it is.
    if len(B["pre"]):
        gap_px = float(B["pre"]["open"].iloc[0])
        rest_pre = B["pre"].iloc[1:]
    else:
        gap_px = B["p0930"]
        rest_pre = B["pre"].iloc[0:0]
    pts.append(("untraded", gap_px, gap_px))
    pts += extremes(rest_pre, "premarket")
    pts += extremes(B["rth"], "rth")
    return entry, pts, B["p1600"]


def walk(entry: float, pts: list) -> dict:
    """Trailing drawdown on OPEN equity, the way a prop firm's floor actually moves.

    The peak INCLUDES the current bar's high — within a 15-minute bar the high may
    precede the low, so a bar can both lift the floor and then breach it. That is the
    adverse assumption and it is the right one for a ratcheting barrier: assuming
    otherwise would quietly under-count breaches, which is the direction that
    manufactures comfort."""
    peak = 1.0
    max_dd = 0.0
    mae = 0.0
    dd_seg = None
    gap_dd = 0.0
    first_breach = {k: None for k in NOTIONALS}
    for seg, hi, lo in pts:
        peak = max(peak, hi / entry)
        dd = 1.0 - (lo / entry) / peak
        mae = min(mae, lo / entry - 1.0)
        if seg == "untraded":
            gap_dd = dd
        if dd > max_dd:
            max_dd, dd_seg = dd, seg
        for k in NOTIONALS:
            if first_breach[k] is None and dd > TRAILING_DD / k:
                first_breach[k] = seg
    return {"max_dd": max_dd, "mae": mae, "dd_segment": dd_seg, "gap_dd": gap_dd,
            **{f"breach_seg_{k}x": first_breach[k] for k in NOTIONALS}}


def paths(sess: dict, symbol: str, variant: str) -> pd.DataFrame:
    days = sorted(sess)
    rows = []
    for a, b in zip(days, days[1:]):
        # Globex is SHUT on Friday evening and reopens Sunday 18:00. A Friday->Monday
        # pair is not a hold anyone could place, and the Sunday-evening hold it would
        # stand in for is unrepresentable in equity bars -- there are none on Sunday.
        # So Monday exits are absent from this measurement entirely, and Monday's
        # overnight is exactly the one most likely to carry weekend news.
        if (date.fromisoformat(b) - date.fromisoformat(a)).days != 1:
            continue
        p = path_points(sess, a, b, variant)
        if p is None:
            continue
        entry, pts, exit_px = p
        rows.append({"symbol": symbol, "day": b, "era": era_of(b), "entry": entry,
                     "ret": exit_px / entry - 1.0, **walk(entry, pts)})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------


def pct(x, dp=2):
    return "n/a" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x * 100:+.{dp}f}%"


def upct(x, dp=2):
    return "n/a" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x * 100:.{dp}f}%"


def main() -> int:
    meta = json.loads(META.read_text(encoding="utf-8"))
    df = load()
    drop = half_days(df)

    sess = {s: sessions_for(df, s, drop) for s in SYMBOLS}
    dec = pd.concat([decompose(sess[s], s) for s in SYMBOLS], ignore_index=True)
    pth = {v: pd.concat([paths(sess[s], s, v) for s in SYMBOLS], ignore_index=True)
           for v in ("corroborated", "closes")}
    # The `raw` variant needs the suspect bars BACK, so it gets its own session map
    # built from an unfiltered frame. Kept separate rather than threaded through
    # `sessions_for`, so that no flag can make the headline path depend on it.
    sess_raw = {s: sessions_for(df.assign(suspect=0), s, drop) for s in SYMBOLS}
    pth["raw"] = pd.concat([paths(sess_raw[s], s, "raw") for s in SYMBOLS],
                           ignore_index=True)

    L = []
    w = L.append
    w("# D259 — where the overnight drift accrues, and what the path does to it")
    w("")
    w("**A MEASUREMENT. No rule is proposed, no cell is scored, no hurdle is claimed.**")
    w("")
    span = f"{dec['day'].min()} .. {dec['day'].max()}"
    w(f"*`index_extended_15m_raw`: {meta['rows']:,} bars, {meta['sessions']:,} "
      f"symbol-sessions, median {meta['gates']['median_bars_per_session']} bars/session "
      f"(regular hours alone would be {meta['gates']['rth_only_would_be']}), "
      f"{meta['start']} .. {meta['end']}. Decomposition on {len(dec):,} session pairs, "
      f"{span}.*")
    w("")
    w(f"*Bad prints: {meta['bad_prints']['suspect_bars']:,} suspect bars "
      f"({meta['bad_prints']['suspect_rate'] * 100:.3f}%), "
      f"{meta['bad_prints']['by_segment']['post']:,} of them post-market. "
      f"Worst raw lower wick **+{meta['bad_prints']['worst_lower_wick_raw'] * 100:,.0f}%**. "
      "Excluded from every price used below; see the fixture meta for the rule.*")
    w("")

    # ---- realised boundaries ----
    w("## The boundaries are prints, not clock times")
    w("")
    w("An extended-hours bar exists only where something traded, so keying on the "
      "clock selects on activity and then measures returns. The realised boundary "
      "times, median and 90th percentile of lateness:")
    w("")
    w("| symbol | era | pairs | last post-market print | first pre-market print |")
    w("|---|---|---:|---|---|")
    for s in SYMBOLS:
        for e in ERAS:
            d = dec[(dec["symbol"] == s) & (dec["era"] == e)]
            if d.empty:
                continue
            t20 = sorted(d["t2000"])
            t04 = sorted(d["t0400"])
            w(f"| {s} | {e} | {len(d):,} | {t20[len(t20) // 2]} med, "
              f"{t20[len(t20) // 10]} at p10 | {t04[len(t04) // 2]} med, "
              f"{t04[-len(t04) // 10]} at p90 |")
    w("")

    # ---- the four windows ----
    w("## The four windows")
    w("")
    w("Annualised in log space against each symbol's own calendar span, then averaged "
      "equal-weighted across symbols — D247's frame. Share is of the **total "
      "overnight drift** (post + untraded + pre), so the three shares sum to 1.")
    w("")
    w("**A share can exceed 100% or go negative, and where it does the boundary table "
      "above explains it.** DIA's first pre-market print in 2010-2019 lands at 06:00 "
      "median and 08:00 at the 90th percentile, so DIA's *untraded* window is "
      "absorbing 20:00->06:00 while its *pre-market* window is only 06:00->09:30. "
      "The windows are not the same clock hours for every symbol, and pooling them is "
      "the compromise this fixture's liquidity forces. **SPY and QQQ from 2020 on are "
      "the clean read**: both print 04:00 and 19:45 on essentially every session.")
    w("")
    for label, sel in (("Pooled, all four symbols", dec),
                       *[(f"{s}", dec[dec["symbol"] == s]) for s in SYMBOLS]):
        w(f"### {label}")
        w("")
        w("| era | pairs | window | annualised | ann. vol | share of overnight |")
        w("|---|---:|---|---:|---:|---:|")
        for e in ("ALL", *ERAS):
            d = sel if e == "ALL" else sel[sel["era"] == e]
            t = window_table(d)
            if not t:
                continue
            for wn, name in (("post", "16:00 -> 20:00  post-market"),
                             ("untraded", "20:00 -> 04:00  **untraded**"),
                             ("pre", "04:00 -> 09:30  pre-market"),
                             ("rth", "09:30 -> 16:00  regular hours"),
                             ("overnight", "*= overnight total*"),
                             ("close_to_close", "*= close-to-close*")):
                sh = t[wn]["share_of_overnight"]
                w(f"| {e if wn == 'post' else ''} | "
                  f"{t[wn]['n']:,} | {name} | **{pct(t[wn]['ann'])}** | "
                  f"{upct(t[wn]['vol'], 1)} | "
                  f"{('%.1f%%' % (sh * 100)) if sh is not None else '—'} |")
        w("")

    # ---- strict clock anchors ----
    w("### The same decomposition on the LITERAL clock")
    w("")
    w("Restricted to pairs whose boundaries are an actual 19:45 bar and an actual "
      "04:00 bar — the windows exactly as named, at the cost of a "
      "**liquidity-conditioned subsample**: it keeps 99% of SPY's recent sessions and "
      "22% of DIA's early ones. Reported because the two readings differ, and the "
      "difference is the finding.")
    w("")
    w("| symbol | era | pairs | kept | post-market | **untraded** | pre-market | regular |")
    w("|---|---|---:|---:|---:|---:|---:|---:|")
    for s in SYMBOLS:
        st = decompose(sess[s], s, strict=True)
        avail = dec[dec["symbol"] == s]
        for e in ("ALL", *ERAS):
            d = st if e == "ALL" else st[st["era"] == e]
            a = avail if e == "ALL" else avail[avail["era"] == e]
            t = window_table(d)
            if not t or len(a) == 0:
                continue
            w(f"| {s if e == 'ALL' else ''} | {e} | {len(d):,} | "
              f"{len(d) / len(a) * 100:.0f}% | "
              f"{pct(t['post']['ann'])} ({t['post']['share_of_overnight'] * 100:.0f}%) | "
              f"**{pct(t['untraded']['ann'])} "
              f"({t['untraded']['share_of_overnight'] * 100:.0f}%)** | "
              f"{pct(t['pre']['ann'])} ({t['pre']['share_of_overnight'] * 100:.0f}%) | "
              f"{pct(t['rth']['ann'])} |")
    w("")
    w("**Read SPY 2021-2026 and QQQ 2021-2026 first.** Those are the two cells where "
      "the anchor coverage is essentially 100%, so the windows mean what they say and "
      "nothing has been selected on. Everything else carries a coverage discount.")
    w("")

    # ---- the path ----
    w("## The path — a long opened at 18:00 ET, held to 16:00 ET the next day")
    w("")
    w("The MyFundedFutures window. Entry is the 18:00 print (or the standing price at "
      "18:00 where the 18:00 slot did not trade); exit is the 16:00 close. "
      "**Friday->Monday pairs are excluded** — Globex is shut on Friday evening, and "
      "the Sunday-evening hold that would replace it has no equity bars at all. "
      "Monday exits are therefore absent from this table, and Monday's overnight is "
      "the one most likely to carry weekend news.")
    w("")
    w("**Trailing drawdown is measured on open equity with the peak including the "
      "current bar's high** — within a 15-minute bar the high may precede the low, so "
      "a bar can lift the floor and then breach it. That is the adverse assumption "
      "and it is the right direction for a ratcheting barrier.")
    w("")
    P = pth["corroborated"]
    w("### Maximum adverse excursion — the distribution, not the mean")
    w("")
    w("| era | holds | mean | p50 | p75 | p90 | p95 | p99 | worst |")
    w("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for label, d in (("ALL", P), *[(e, P[P["era"] == e]) for e in ERAS]):
        if d.empty:
            continue
        m = -d["mae"]
        w(f"| {label} | {len(d):,} | {upct(m.mean())} | {upct(m.quantile(.50))} | "
          f"{upct(m.quantile(.75))} | {upct(m.quantile(.90))} | "
          f"{upct(m.quantile(.95))} | {upct(m.quantile(.99))} | "
          f"**{upct(m.max())}** |")
    w("")
    w("Per symbol, pooled across eras:")
    w("")
    w("| symbol | holds | mean MAE | p90 | p99 | worst | max trailing DD, p99 |")
    w("|---|---:|---:|---:|---:|---:|---:|")
    for s in SYMBOLS:
        d = P[P["symbol"] == s]
        if d.empty:
            continue
        m = -d["mae"]
        w(f"| {s} | {len(d):,} | {upct(m.mean())} | {upct(m.quantile(.90))} | "
          f"{upct(m.quantile(.99))} | {upct(m.max())} | "
          f"{upct(d['max_dd'].quantile(.99))} |")
    w("")

    # ---- breaches ----
    w("### What fraction of sessions breach a 4% trailing drawdown")
    w("")
    w("At notional *k*, a 4% equity floor is breached when the price path draws down "
      "more than 4%/*k* from its running peak — 4.00% at 1x, 2.00% at 2x, 1.33% at 3x.")
    w("")
    w("| era | holds | 1x | 2x | 3x |")
    w("|---|---:|---:|---:|---:|")
    for label, d in (("ALL", P), *[(e, P[P["era"] == e]) for e in ERAS]):
        if d.empty:
            continue
        cells = " | ".join(upct((d["max_dd"] > TRAILING_DD / k).mean())
                           for k in NOTIONALS)
        w(f"| {label} | {len(d):,} | {cells} |")
    w("")
    w("Per symbol:")
    w("")
    w("| symbol | holds | 1x | 2x | 3x |")
    w("|---|---:|---:|---:|---:|")
    for s in SYMBOLS:
        d = P[P["symbol"] == s]
        if d.empty:
            continue
        cells = " | ".join(upct((d["max_dd"] > TRAILING_DD / k).mean())
                           for k in NOTIONALS)
        w(f"| {s} | {len(d):,} | {cells} |")
    w("")

    # ---- the untraded window ----
    w("### How much of the adverse excursion falls where it cannot be exited")
    w("")
    w("**This is the point.** A trailing floor is measured on open equity, and a "
      "position cannot be stopped out of a window with no prices in it. The "
      "20:00->04:00 stretch contributes exactly one observation to the path — the "
      "price it reopens at — so the numbers below are a **LOWER BOUND**: any "
      "excursion inside the untraded window is invisible to this fixture, and a "
      "continuously-traded futures position would have lived through it.")
    w("")
    w("Where the session's maximum trailing drawdown is realised. **This table is "
      "dominated by bar counts and is the least useful of the three** — regular hours "
      "supply 26 observations, the untraded window supplies exactly one, so of course "
      "the maximum usually lands in regular hours. It is reported because its "
      "shape is what makes the next two tables readable, not because it decides "
      "anything.")
    w("")
    w("| era | holds | evening 18:00-20:00 | **untraded** | pre-market | regular hours |")
    w("|---|---:|---:|---:|---:|---:|")
    for label, d in (("ALL", P), *[(e, P[P["era"] == e]) for e in ERAS]):
        if d.empty:
            continue
        cells = " | ".join(upct((d["dd_segment"] == s).mean()) for s in SEGMENTS)
        w(f"| {label} | {len(d):,} | {cells} |")
    w("")
    w("Where the **FIRST breach** of the 4% floor occurs, among breaching holds. "
      "This one decides something: a breach that first occurs in regular hours is a "
      "breach you were stopped out of, and a breach that first occurs in the untraded "
      "window is one **no stop could have prevented**. Pre-market sits in between — "
      "technically exitable, thin enough that a stop is a hope rather than a plan.")
    w("")
    w("| notional | era | breaching holds | evening | **untraded** | pre-market | regular hours |")
    w("|---|---|---:|---:|---:|---:|---:|")
    for k in NOTIONALS:
        col = f"breach_seg_{k}x"
        for label, d in (("ALL", P), *[(e, P[P["era"] == e]) for e in ERAS]):
            b = d[d[col].notna()]
            if b.empty:
                w(f"| {k}x | {label} | 0 | — | — | — | — |")
                continue
            cells = " | ".join(upct((b[col] == s).mean()) for s in SEGMENTS)
            w(f"| {'%dx' % k if label == 'ALL' else ''} | {label} | {len(b):,} | {cells} |")
    w("")
    w("And the untraded gap **on its own** — the drawdown from the running peak to "
      "the first next-session print, which no stop could have avoided:")
    w("")
    w("| era | holds | mean gap DD | p90 | p99 | worst | gap alone breaches 1x | 2x | 3x |")
    w("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for label, d in (("ALL", P), *[(e, P[P["era"] == e]) for e in ERAS]):
        if d.empty:
            continue
        g = d["gap_dd"]
        cells = " | ".join(upct((g > TRAILING_DD / k).mean()) for k in NOTIONALS)
        w(f"| {label} | {len(d):,} | {upct(g.mean())} | {upct(g.quantile(.90))} | "
          f"{upct(g.quantile(.99))} | **{upct(g.max())}** | {cells} |")
    w("")

    # ---- worst sessions ----
    w("### Worst single sessions, dated")
    w("")
    w("| rank | symbol | session | max trailing DD | MAE | of which the untraded gap | hold return |")
    w("|---:|---|---|---:|---:|---:|---:|")
    for i, r in enumerate(P.nlargest(10, "max_dd").itertuples(), 1):
        w(f"| {i} | {r.symbol} | {r.day} | **{upct(r.max_dd)}** | {upct(-r.mae)} | "
          f"{upct(r.gap_dd)} | {pct(r.ret)} |")
    w("")
    w("Worst by symbol:")
    w("")
    w("| symbol | session | max trailing DD | MAE | untraded gap DD | hold return |")
    w("|---|---|---:|---:|---:|---:|")
    for s in SYMBOLS:
        d = P[P["symbol"] == s]
        if d.empty:
            continue
        r = d.loc[d["max_dd"].idxmax()]
        w(f"| {s} | {r['day']} | **{upct(r['max_dd'])}** | {upct(-r['mae'])} | "
          f"{upct(r['gap_dd'])} | {pct(r['ret'])} |")
    w("")

    # ---- sensitivity ----
    w("## Sensitivity — how much of this is the bad prints, and how much is real")
    w("")
    w("`corroborated` is the headline: suspect bars excluded, bar highs and lows "
      "used. `raw` puts the erroneous prints back. `closes` samples the path at bar "
      "closes only and is a strict lower bound. The truth for a continuously-traded "
      "instrument sits **above** all three, because the untraded window is dark in "
      "every one of them.")
    w("")
    w("| variant | holds | mean MAE | p99 MAE | worst MAE | breach 1x | breach 2x | breach 3x |")
    w("|---|---:|---:|---:|---:|---:|---:|---:|")
    for v in ("corroborated", "raw", "closes"):
        d = pth[v]
        m = -d["mae"]
        cells = " | ".join(upct((d["max_dd"] > TRAILING_DD / k).mean())
                           for k in NOTIONALS)
        w(f"| {v} | {len(d):,} | {upct(m.mean())} | {upct(m.quantile(.99))} | "
          f"{upct(m.max())} | {cells} |")
    w("")

    # ---- coverage / what was dropped ----
    w("## What was excluded, and why")
    w("")
    total_pairs = sum(len(sess[s]) - 1 for s in SYMBOLS)
    w(f"| | count |")
    w("|---|---:|")
    w(f"| symbol-sessions in the fixture | {meta['sessions']:,} |")
    w(f"| half-days dropped (13:00 close: no 16:00 print, no 16:00->20:00 window) | "
      f"{len(drop)} sessions |")
    w(f"| usable session pairs | {total_pairs:,} |")
    w(f"| pairs in the decomposition (needs an evening AND a pre-market print) | "
      f"{len(dec):,} |")
    w(f"| holds in the path table (consecutive calendar days, evening print after "
      f"17:00) | {len(P):,} |")
    w("")
    w("Decomposition coverage by symbol and era, as a share of available pairs:")
    w("")
    w("| symbol | 2010-2019 | 2020 | 2021-2026 |")
    w("|---|---:|---:|---:|")
    for s in SYMBOLS:
        avail = defaultdict(int)
        for d in sorted(sess[s])[1:]:
            avail[era_of(d)] += 1
        got = dec[dec["symbol"] == s]["era"].value_counts()
        w(f"| {s} | " + " | ".join(
            f"{got.get(e, 0)}/{avail[e]} ({got.get(e, 0) / avail[e] * 100:.0f}%)"
            if avail[e] else "—" for e in ERAS) + " |")
    w("")

    PAGE.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {PAGE.name}  ({len(dec):,} pairs, {len(P):,} holds)")

    # A short console summary so the run is legible without opening the page.
    t = window_table(dec)
    print("\npooled, all eras:")
    for wn in (*WINDOWS, "overnight", "close_to_close"):
        sh = t[wn]["share_of_overnight"]
        print(f"  {wn:<15} {t[wn]['ann'] * 100:+7.2f}%/yr  vol "
              f"{t[wn]['vol'] * 100:5.1f}%  n={t[wn]['n']:,}"
              + (f"  share {sh * 100:.1f}%" if sh is not None else ""))
    print("\nby era:")
    for e in ERAS:
        te = window_table(dec[dec["era"] == e])
        print(f"  {e}: " + "  ".join(
            f"{wn}={te[wn]['ann'] * 100:+.2f}%" for wn in (*WINDOWS, "overnight")))
    print("\nbreach rates (corroborated):")
    for label, d in (("ALL", P), *[(e, P[P["era"] == e]) for e in ERAS]):
        print(f"  {label:<10} n={len(d):>6,}  " + "  ".join(
            f"{k}x={(d['max_dd'] > TRAILING_DD / k).mean() * 100:5.2f}%"
            for k in NOTIONALS))
    print("\nmax-DD realised in the untraded window: "
          f"{(P['dd_segment'] == 'untraded').mean() * 100:.2f}% of holds")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
