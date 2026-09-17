"""D472 -- does the volume-clock exit's 1 pp survive the 2016-2023 in-sample window?

    uv run python scripts/d472_volume_clock_exit_insample.py --self-test
    uv run python scripts/d472_volume_clock_exit_insample.py --measure [--json]

**A MEASUREMENT OF A SAMPLING RULE, NOT A STUDY.** There is no entry signal, no directional
forecast and no Sharpe of any construction. It compares two EXIT rules on the same bars --
"hold 15 minutes" against "hold until V contracts trade" -- at matched bar count, and asks
how much absolute move each captures and what breakeven accuracy each implies. Nothing is
opened, closed or admitted (R15). Scoring an actual rule needs a pre-registration (R8); this
is not that.

WHY
---
[D471 AMENDMENT 2](../docs/decisions/D471-RESULT-the-spread-barely-widens-where-the-moves-are-and-path.md)
found that at matched bar count and matched mean holding time a volume bar captured **15% more
move** than a 15-minute bar (E|M| 27.1 against 23.5 ticks), taking the MES breakeven accuracy
from **57.3% to 56.3%** -- about 1 pp, worth roughly 1.0 of Sharpe by D469's sensitivity. That
was measured on **one recent year** of tick data, and the record said in writing that the
component window is 2016-2023 and that no rule had been scored on it.

This runs the same comparison on **2016-01-04 to 2023-12-29** -- the D462 usable window for the
futures fixtures -- eight years instead of one, and **year by year**, because an eight-year
average that hides a sign flip is not a result.

THREE THINGS THAT ARE DIFFERENT HERE, AND THEY ALL WEAKEN THE CLAIM
-------------------------------------------------------------------
1. **The clock is minute-resolution, not trade-resolution.** There is no tick data before
   2025-09; `ohlcv-1m` carries `volume`, so a volume boundary can only land on a minute edge.
   A ~13-minute volume bar therefore has ~8% granularity in its boundary. **This blunts the
   volume clock**, so whatever advantage survives here is a floor, not a ceiling.
2. **V MUST BE CAUSAL.** Calibrating V from the period's own volume is look-ahead, and
   calibrating it from the session's own volume is look-ahead *within the day*. V is set from
   the **trailing 20 sessions'** mean RTH volume / 26. A consequence: bar counts per session
   are no longer exactly 26 on the volume clock -- busy days produce more bars, which cost
   more. Both clocks' bars/session are reported.
3. **MES DID NOT EXIST BEFORE 2019-05-06.** Breakeven is quoted at MES cost throughout for
   comparability across the window, but for 2016 to mid-2019 the minimum tradable size was one
   full ES contract, which `COMPONENTS_PROP.md` C-d forbids in a $50k account. The pre-2019
   rows are an instrument measurement, not a tradable proposition.

The cost line in TICKS is close to era-independent, which is what makes the comparison legible
across an eight-year window: the ES spread is one tick (crossing ~1.0 tick, the value assumed
here -- NOT measured before 2025-09, since `tbbo` does not reach back) and $3 of commission is
2.40 MES ticks at any price. But the MOVE in ticks is not era-independent -- ES traded near
2,000 in 2016 and near 4,700 in 2023 -- so p_be is expected to be worse in the early years for
reasons that have nothing to do with the exit rule. **That is why the exit comparison is read
WITHIN each year and never across them.**
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
FIX = REPO / "data" / "fixtures" / "fut_ES_rth_1m.csv.gz"
META = REPO / "data" / "fixtures" / "fut_index_1m.meta.json"
OUT = REPO / "data" / "d472_volume_clock_exit_insample.json"

TICK_PTS = 0.25
CROSS_TICKS = 1.009          # D465, measured on 2025-09..2026-09; ASSUMED for 2016-2023
COMMISSION_RT_MES = 3.00
TICK_USD_MES = 1.25
BARS_PER_SESSION = 26        # 390 RTH minutes / 15
TIME_BAR_MIN = 15
TRAIL_SESSIONS = 20          # causal calibration window for V
IN_SAMPLE = ("2016-01-04", "2023-12-29")   # D462 usable window; 2024+ is the holdout
MES_LAUNCH = "2019-05-06"


class GateError(AssertionError):
    """A validation gate refused the input. Raising, never a warning."""


def P(*a, **k):
    print(*a, **k, flush=True)


def cost_ticks() -> float:
    return CROSS_TICKS + COMMISSION_RT_MES / TICK_USD_MES


def breakeven_accuracy(cost: float, e_abs_move: float) -> float:
    return (1.0 + cost / e_abs_move) / 2.0


def bars_from_edges(edge_id: np.ndarray):
    """Group consecutive equal ids into (start, end-inclusive) index pairs."""
    if len(edge_id) == 0:
        return np.array([], dtype=np.int64), np.array([], dtype=np.int64)
    cut = np.flatnonzero(np.diff(edge_id) != 0) + 1
    starts = np.concatenate([[0], cut])
    ends = np.concatenate([cut - 1, [len(edge_id) - 1]])
    return starts.astype(np.int64), ends.astype(np.int64)


def volume_bar_ids(vol: np.ndarray, V: float) -> np.ndarray:
    """Bar id per minute: how many multiples of V have traded BEFORE this minute."""
    before = np.cumsum(vol) - vol
    return (before / max(V, 1.0)).astype(np.int64)


def do_self_test() -> int:
    fails = []

    def chk(label, cond, detail=""):
        P(f"    [{'PASS' if cond else 'FAIL'}] {label:60} {detail}")
        if not cond:
            fails.append(label)

    # --- grouping consecutive ids into bars
    s, e = bars_from_edges(np.array([0, 0, 0, 1, 1, 2]))
    chk("bars_from_edges starts", list(s) == [0, 3, 5], f"{list(s)}")
    chk("bars_from_edges ends are INCLUSIVE", list(e) == [2, 4, 5], f"{list(e)}")
    chk("bars tile the whole series with no gap and no overlap",
        list(s[1:]) == list(e[:-1] + 1) and e[-1] == 5)
    s1, e1 = bars_from_edges(np.array([7, 7, 7]))
    chk("a single bar is one (0, n-1) pair", list(s1) == [0] and list(e1) == [2])

    # --- the volume clock, on volumes whose answer is known by hand
    v = np.array([10, 10, 10, 10, 10, 10], dtype=np.int64)
    ids = volume_bar_ids(v, 20)          # before = 0,10,20,30,40,50 -> //20 = 0,0,1,1,2,2
    chk("volume bar ids on flat volume", list(ids) == [0, 0, 1, 1, 2, 2], f"{list(ids)}")
    chk("volume clock uses volume BEFORE the minute, so it starts at bar 0",
        ids[0] == 0)
    # a single huge minute must SKIP bar ids -- it cannot be split, and that is the
    # minute-resolution limitation stated in the docstring, made visible here
    v2 = np.array([10, 100, 10, 10], dtype=np.int64)
    ids2 = volume_bar_ids(v2, 20)         # before = 0,10,110,120 -> 0,0,5,6
    chk("a huge minute skips bar ids (minute-resolution limit)",
        list(ids2) == [0, 0, 5, 6], f"{list(ids2)}")
    s2, e2 = bars_from_edges(ids2)
    chk("skipped ids still produce contiguous bars", len(s2) == 3 and list(s2) == [0, 2, 3],
        f"{list(s2)}")

    # --- more volume per session must mean MORE bars at fixed V
    quiet = volume_bar_ids(np.full(390, 100, dtype=np.int64), 1500)
    busy = volume_bar_ids(np.full(390, 300, dtype=np.int64), 1500)
    chk("a busy session produces more volume bars than a quiet one at fixed V",
        len(np.unique(busy)) > len(np.unique(quiet)),
        f"{len(np.unique(busy))} vs {len(np.unique(quiet))}")

    # --- the cost/breakeven arithmetic
    c = cost_ticks()
    chk("MES cost is ~3.41 ticks", abs(c - 3.409) < 0.01, f"{c:.3f}")
    chk("a bigger captured move lowers breakeven",
        breakeven_accuracy(c, 27.1) < breakeven_accuracy(c, 23.5),
        f"{breakeven_accuracy(c, 27.1):.3%} vs {breakeven_accuracy(c, 23.5):.3%}")
    chk("D471's 1 pp reproduces from its two E|M| values",
        abs((breakeven_accuracy(c, 23.5) - breakeven_accuracy(c, 27.1)) - 0.0100) < 0.0015,
        f"{(breakeven_accuracy(c, 23.5)-breakeven_accuracy(c, 27.1))*100:.2f} pp")

    # --- adverse excursion on the winning side, from bar highs and lows
    hi = np.array([101., 103., 106.])
    lo = np.array([99., 97., 104.])
    entry, exit_ = 100.0, 105.0
    adv = entry - lo.min() if exit_ > entry else hi.max() - entry
    chk("adverse excursion for a winning long is entry minus the low", abs(adv - 3.0) < 1e-12,
        f"{adv}")
    entry2, exit2 = 100.0, 98.0
    adv2 = entry2 - lo.min() if exit2 > entry2 else hi.max() - entry2
    chk("and for a winning short it is the high minus entry", abs(adv2 - 6.0) < 1e-12,
        f"{adv2}")

    if fails:
        P(f"\n  SELF-TEST FAILED: {fails}")
        return 1
    P("\n  SELF-TEST PASSED.")
    return 0


def do_measure(as_json: bool) -> int:
    import pandas as pd

    # the fixture's own gates must be read, not assumed -- ES passes all five, RTY fails G4
    meta = json.loads(META.read_text(encoding="utf-8"))
    g = meta["gates"]["ES"]
    bad = [k for k, v in g.items() if isinstance(v, dict) and v.get("passes") is False]
    if bad:
        raise GateError(f"[FIXTURE] ES fails gates {bad}; refusing to measure on it")
    if g["G5"]["usable_start"] > IN_SAMPLE[0]:
        raise GateError(f"[FIXTURE] usable_start {g['G5']['usable_start']} is after the "
                        f"requested start {IN_SAMPLE[0]}")
    P(f"fixture gates: ES passes {sorted(g)} · usable_start {g['G5']['usable_start']} · "
      f"front rule {meta['front_rule']!r}")

    d = pd.read_csv(FIX)
    d = d[(d["day"] >= IN_SAMPLE[0]) & (d["day"] <= IN_SAMPLE[1])].copy()
    # HARD STOP on the holdout: nothing from 2024 onward may enter this measurement
    if (d["day"] > "2023-12-31").any():
        raise GateError("[HOLDOUT] rows past 2023 reached the measurement")
    d["minute"] = d["hhmm"].str.slice(0, 2).astype(int) * 60 + \
        d["hhmm"].str.slice(3, 5).astype(int)
    d = d.sort_values(["day", "minute"], kind="stable").reset_index(drop=True)
    P(f"ES RTH 1-minute bars {len(d):,} over {d['day'].nunique():,} sessions, "
      f"{d['day'].min()} .. {d['day'].max()}")

    sess_vol = d.groupby("day")["volume"].sum()
    days = sess_vol.index.to_numpy()
    # CAUSAL V: the trailing 20 sessions' mean RTH volume / 26. Never this session's own.
    trail = sess_vol.rolling(TRAIL_SESSIONS).mean().shift(1)
    V_by_day = (trail / BARS_PER_SESSION).to_dict()

    rows = []
    for day, grp in d.groupby("day", sort=True):
        V = V_by_day.get(day)
        if V is None or not np.isfinite(V) or V <= 0:
            continue                               # first 20 sessions have no causal V
        o = grp["open"].to_numpy(float)
        c = grp["close"].to_numpy(float)
        hi = grp["high"].to_numpy(float)
        lo = grp["low"].to_numpy(float)
        vol = grp["volume"].to_numpy(np.int64)
        con = grp["contract"].to_numpy()
        mins = grp["minute"].to_numpy()
        if len(o) < 200:
            continue                               # half-day; G3 lists 128 of them

        for clock, ids in (("time", (mins - mins[0]) // TIME_BAR_MIN),
                           ("volume", volume_bar_ids(vol, V))):
            st, en = bars_from_edges(np.asarray(ids))
            for a, b in zip(st, en):
                if con[a] != con[b]:
                    continue                       # never straddle a roll
                entry, exit_ = o[a], c[b]
                net = (exit_ - entry) / TICK_PTS
                adv = ((entry - lo[a:b + 1].min()) if exit_ > entry
                       else (hi[a:b + 1].max() - entry)) / TICK_PTS
                rows.append((day[:4], day, clock, abs(net), adv,
                             mins[b] - mins[a] + 1, int(vol[a:b + 1].sum()), entry))

    r = pd.DataFrame(rows, columns=["year", "day", "clock", "abs_ticks", "adverse_ticks",
                                    "minutes", "contracts", "entry_px"])
    cost = cost_ticks()
    P(f"\ncost line: crossing {CROSS_TICKS:.3f} tk (D465, ASSUMED for this era) + "
      f"commission {COMMISSION_RT_MES/TICK_USD_MES:.2f} tk = {cost:.3f} MES ticks\n")

    def summarise(sub: pd.DataFrame) -> dict:
        out = {}
        for clock in ("time", "volume"):
            s = sub[sub["clock"] == clock]
            if len(s) < 200:
                continue
            e_abs = float(s["abs_ticks"].mean())
            px = float(s["entry_px"].mean())
            # INDEPENDENT SANITY CHECK, because a 4.69-tick 15-minute move wants verifying
            # against something outside this file. For a normal, sigma = E|M|/sqrt(2/pi);
            # scale to a day (26 bars) and a year (252 days) as a fraction of price.
            sig_bar = e_abs * TICK_PTS / np.sqrt(2.0 / np.pi) / px
            ann_vol = sig_bar * np.sqrt(BARS_PER_SESSION * 252.0)
            out[clock] = {
                "n_bars": int(len(s)),
                "bars_per_session": float(len(s) / s["day"].nunique()),
                "mean_minutes": float(s["minutes"].mean()),
                "mean_entry_price": px,
                "mean_abs_ticks": e_abs,
                "implied_annualised_rth_vol": float(ann_vol),
                "breakeven_accuracy": breakeven_accuracy(cost, e_abs),
                # RATIO OF MEANS, to be comparable with D471 section 5's 0.48. The mean of
                # the RATIO is a different statistic and is inflated by bars whose net move
                # is near zero -- both are reported rather than one being picked.
                "adverse_over_move_ratio_of_means":
                    float(s["adverse_ticks"].mean() / e_abs),
                "adverse_over_move_mean_of_ratios":
                    float((s["adverse_ticks"] / s["abs_ticks"].replace(0, np.nan)).mean()),
            }
        if "time" in out and "volume" in out:
            out["volume_advantage_pp"] = (out["time"]["breakeven_accuracy"]
                                          - out["volume"]["breakeven_accuracy"]) * 100
            out["move_lift_pct"] = (out["volume"]["mean_abs_ticks"]
                                    / out["time"]["mean_abs_ticks"] - 1) * 100
        return out

    P(f"  {'year':>6}{'clock':>8}{'bars':>9}{'b/sess':>8}{'mins':>6}{'price':>8}"
      f"{'annvol':>8}{'E|M| tk':>9}{'p_be':>8}{'adv r-o-m':>10}   {'lift':>7}"
      f"{'advantage':>11}")
    per_year = {}
    for year in sorted(r["year"].unique()):
        s = summarise(r[r["year"] == year])
        if not s or "volume_advantage_pp" not in s:
            continue
        per_year[year] = s
        for clock in ("time", "volume"):
            q = s[clock]
            tail = (f"   {s['move_lift_pct']:>+6.1f}%{s['volume_advantage_pp']:>+10.2f}"
                    if clock == "volume" else "")
            P(f"  {year if clock == 'time' else '':>6}{clock:>8}{q['n_bars']:>9,}"
              f"{q['bars_per_session']:>8.1f}{q['mean_minutes']:>6.1f}"
              f"{q['mean_entry_price']:>8.0f}{q['implied_annualised_rth_vol']:>8.1%}"
              f"{q['mean_abs_ticks']:>9.2f}{q['breakeven_accuracy']:>8.2%}"
              f"{q['adverse_over_move_ratio_of_means']:>10.2f}{tail}")

    pooled = summarise(r)
    P(f"\n  POOLED 2016-2023:")
    for clock in ("time", "volume"):
        q = pooled[clock]
        P(f"    {clock:>7}  {q['n_bars']:>8,} bars  {q['bars_per_session']:>5.1f}/session  "
          f"{q['mean_minutes']:>5.1f} min  E|M| {q['mean_abs_ticks']:>6.2f} tk  "
          f"p_be {q['breakeven_accuracy']:>6.2%}  "
          f"adv/|M| {q['adverse_over_move_ratio_of_means']:.2f} (r-o-m) / "
          f"{q['adverse_over_move_mean_of_ratios']:.2f} (m-o-r)")
    P(f"    volume captures {pooled['move_lift_pct']:+.1f}% more move, "
      f"advantage {pooled['volume_advantage_pp']:+.2f} pp of breakeven accuracy")

    wins = sum(1 for y in per_year.values() if y["volume_advantage_pp"] > 0)
    P(f"\n  the advantage is POSITIVE in {wins} of {len(per_year)} years"
      f"  (D471 measured +1.00 pp on 2025-09..2026-09)")

    res = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "purpose": "D472: does D471's volume-clock exit advantage survive the 2016-2023 "
                      "in-sample window? A sampling measurement -- no entry signal, no "
                      "directional forecast, no Sharpe of any construction, nothing admitted.",
           "source": "data/fixtures/fut_ES_rth_1m.csv.gz (ES passes G1-G5), "
                     "2016-01-04..2023-12-29, RTH 09:30-15:59",
           "limitations": [
               "the volume clock is MINUTE-resolution: no tick data exists before 2025-09, "
               "so a boundary lands on a minute edge and a ~13-minute bar carries ~8% "
               "granularity -- this BLUNTS the volume clock, so the advantage here is a floor",
               "V is calibrated causally from the trailing 20 sessions, so bars/session is "
               "not exactly 26 on the volume clock and busy days cost more",
               f"MES did not exist before {MES_LAUNCH}; breakeven is quoted at MES cost "
               "throughout for comparability, but pre-2019 rows are not tradable at that "
               "size and C-d forbids one full ES contract in a $50k account",
               "the crossing of 1.009 ticks is D465's 2025-09..2026-09 measurement ASSUMED "
               "for this era; tbbo does not reach back, so it is not measured here",
               "E|M| in ticks is not comparable ACROSS years (ES ~2,000 in 2016 against "
               "~4,700 in 2023); the exit comparison is read WITHIN each year"],
           "cost_ticks": cost, "crossing_ticks_assumed": CROSS_TICKS,
           "trailing_sessions_for_V": TRAIL_SESSIONS,
           "pooled": pooled, "by_year": per_year,
           "years_with_positive_advantage": wins, "years": len(per_year)}
    if as_json:
        OUT.write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
        P(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--measure", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return do_self_test()
    if a.measure:
        return do_measure(a.json)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
