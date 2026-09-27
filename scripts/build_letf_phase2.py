"""LETF close-flow Phase 2 (deposit s.3.3, s.3.4, s.9): futures bars, the session calendar and event flags, and the
data QA report (bar coverage, excluded dates). NQ first (the principal, 2026-09-27: "start NQ Phase 2"); ES joins
once the pre-2019 Direxion anchors are in (LETF-A5).

    uv run python scripts/build_letf_phase2.py --root NQ          # -> data/letf/phase2_NQ_sessions.csv.gz + _qa.json
    uv run python scripts/build_letf_phase2.py --selftest

SEAL (A10): every read goes through the loader chokepoint (`load_panel`, reserved_from 2025-03-01) except the micro
volume fixture, which is not catalogued yet and is cut with the same D594 layers by hand (filter, then assert).

WHAT IS BUILT, PER SESSION (2016-01-04 -> 2025-02-28):
- the front contract by full-day volume (D462's fixture: 09:30-15:59 ET one-minute bars, no stitching);
- `p1600` = the close of the 15:59 bar (the bar ending 16:00); `p_prev_close_same` = the PRIOR NYSE DAY's close (16:00, or 13:00 on
  a half-day) OF TODAY'S CONTRACT and `p0945_next_same` = the NEXT session's 09:45 open of today's contract (deposit s.4.1 computes r
  within one contract; H5 likewise), both from `fut_index_anchor_bars` (every listed month's 09:45 and 15:59 bars), so
  a roll day is priced in one contract. CME's settlement is NOT used: it equals the 15:59 close on 2.4% of NQ sessions
  (a first draft substituted it on roll days; the measurement stays in the QA as a fact);
- NQ-equivalent volume = NQ front full-day volume + MNQ front full-day volume / 10 (s.4.4; MNQ from 2019-05-06, zero
  before its listing, stated);
- exclusions: early close (s.3.4) and any CME session on a day the NYSE was closed (no NAV, no rebalance);
- flags: FOMC, CPI, quad witching, quarter-end, month-end, Nasdaq-100 rebalance (the
  quarterly third Fridays plus the 2023-07-21 special rebalance, Nasdaq press release 2023-07-07), DST transition
  week, and intraday bar gaps.
- coverage of the bars the model reads: 10:59-11:59 (H4's 11:00 -> 12:00), 14:29-15:59 (entries and exit), and the
  next session's 09:44 (H5's 09:45 open).
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from backtest_framework.data.panels import load_panel
from backtest_framework.validation.frozen import (ReservedSliceError, assert_none_at_or_after, filter_before,
                                                  window_record)

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "letf"
RESERVED_FROM = "2025-03-01"
START = "2016-01-04"
WARM = "2015-12-01"  # read from here so the first session has a t-1; nothing before START is output
MICRO = REPO / "data" / "fixtures" / "fut_micro_day_volume.csv.gz"
ANCHOR = REPO / "data" / "fixtures" / "fut_index_anchor_bars.csv.gz"
SPY = REPO / "data" / "raw" / "alphavantage" / "daily" / "SPY.json.gz"  # the NYSE calendar, as Gate 0 (D637)
MICRO_OF = {"NQ": "MNQ", "ES": "MES"}
TICK = {"NQ": 0.25, "ES": 0.25}
# Nasdaq press release 2023-07-07, "The Nasdaq-100 Index Special Rebalance to be Effective July 24, 2023" (before the
# open on Monday 24 July, so traded at the close of Friday 21 July). The release: the index had rebalanced specially
# only in 1998 and 2011 before, so this is the one inside 2016-2025.
NDX_SPECIAL = ["2023-07-21"]
KEY_BARS = {"h4": ("10:59", "11:59"), "entry_exit": ("14:29", "15:59")}


def third_friday(y: int, m: int) -> pd.Timestamp:
    d = pd.Timestamp(y, m, 1)
    return d + pd.Timedelta(days=(4 - d.dayofweek) % 7 + 14)


def rebalance_days(root: str) -> set[str]:
    """The quarterly index rebalances trade at the close of the third Friday of Mar/Jun/Sep/Dec (for both indices),
    moved to the Thursday if that Friday is a holiday; the calendar's own quad-witching flag is cross-checked."""
    q = {str(third_friday(y, m).date()) for y in range(2016, 2026) for m in (3, 6, 9, 12)}
    return q | (set(NDX_SPECIAL) if root == "NQ" else set())


def micro_volume(root: str, days: pd.Index) -> tuple[pd.Series, dict]:
    m = pd.read_csv(MICRO, encoding="utf-8", dtype={"day": str})
    m = filter_before(m, "day", RESERVED_FROM)
    assert_none_at_or_after(m, "day", RESERVED_FROM)
    rec = window_record(m, "day", RESERVED_FROM)
    s = m[m["root"] == MICRO_OF[root]].set_index("day")["day_volume"]
    return s.reindex(days).fillna(0).astype(np.int64), rec


def anchor_bars(root: str) -> tuple[pd.DataFrame, dict]:
    """Not catalogued yet: cut by hand with the D594 layers (filter, then assert), and recorded."""
    a = pd.read_csv(ANCHOR, encoding="utf-8", dtype={"day": str, "hhmm": str})
    a = filter_before(a, "day", RESERVED_FROM)
    assert_none_at_or_after(a, "day", RESERVED_FROM)
    rec = window_record(a, "day", RESERVED_FROM)
    return a[a["root"] == root], rec


def nyse_days() -> set[str]:
    d = json.load(gzip.open(SPY, "rt", encoding="utf-8"))
    return {x for x in d if WARM <= x < RESERVED_FROM}


def build(root: str) -> int:
    sess_p = load_panel("fut_index_sessions", reserved_from=RESERVED_FROM)
    bars_p = load_panel(f"fut_{root}_rth_1m", reserved_from=RESERVED_FROM)
    cal_p = load_panel("cme_session_calendar", reserved_from=RESERVED_FROM)
    strip_p = load_panel("fut_settle_strip", reserved_from=RESERVED_FROM)  # the settlement fact only
    s = sess_p.frame
    s = s[(s["root"] == root) & (s["day"] >= WARM)].sort_values("day").reset_index(drop=True)
    b = bars_p.frame
    b = b[b["day"] >= WARM]
    cal = cal_p.frame
    cal = cal[(cal["root"] == root) & (cal["day"] >= WARM)].set_index("day")
    strip = strip_p.frame
    strip = strip[strip["root"] == root].set_index(["ref", "contract"])["settle"]

    # t-1 is the PRIOR NYSE TRADING DAY (the fund's NAV day), priced at its NYSE close: the 15:59 bar (ending 16:00),
    # or the 12:59 bar (ending 13:00) on an NYSE half-day. A CME holiday session between them is not t-1.
    # Today's contract throughout (s.4.1): the front's own bar when t-1 had the same front, else the every-month
    # anchor bars (a roll). H5's next 09:45 open is today's contract on the NEXT NYSE day, from the same anchors.
    anc, anc_rec = anchor_bars(root)
    c1559 = anc[anc["hhmm"] == "15:59"].set_index(["day", "contract"])["close"]
    o0945 = anc[anc["hhmm"] == "09:45"].set_index(["day", "contract"])["open"]
    bar_close = b.set_index(["day", "hhmm"])["close"]
    nyse = nyse_days()
    ndays = sorted(set(s["day"]) & nyse)
    front = s.set_index("day")["contract"]
    early = cal["is_early_close"].reindex(ndays).fillna(False).astype(bool)
    prev_px, prev_src, next_px, anchor_diff = [], [], [], []
    for d, c in zip(s["day"], s["contract"]):
        i = int(np.searchsorted(ndays, d))
        p = ndays[i - 1] if i > 0 else None
        n = ndays[i + 1] if i < len(ndays) and ndays[i] == d and i + 1 < len(ndays) else (
            ndays[i] if i < len(ndays) and ndays[i] != d else None)
        px, src = np.nan, "no prior NYSE day"
        if p is not None:
            cb = "12:59" if early[p] else "15:59"
            if front[p] == c:
                px, src = bar_close.get((p, cb), np.nan), f"front {cb} bar of t-1"
                if cb == "15:59" and (p, c) in c1559.index and not np.isnan(px):
                    anchor_diff.append(abs(float(c1559[(p, c)]) - float(px)))
            elif cb == "15:59":
                px, src = c1559.get((p, c), np.nan), "roll: today's contract, 15:59 anchor bar of t-1"
            else:
                src = "roll after a half-day: no 12:59 anchor bar"
        prev_px.append(px)
        prev_src.append(src if not (isinstance(px, float) and np.isnan(px)) else f"MISSING ({src})")
        next_px.append(o0945.get((n, c), np.nan) if n is not None else np.nan)
    s["p_prev_close_same"] = prev_px
    s["prev_close_source"] = prev_src
    s["p0945_next_same"] = next_px
    anchor_vs_fixture = pd.Series(anchor_diff, dtype=float)
    # a documented fact, not a substitute: CME's settlement vs the 15:59 bar close of the same contract, same day
    kk = list(zip(s["day"], s["contract"]))
    st = pd.Series([strip.get(k, np.nan) for k in kk], index=s.index)
    diff_ticks = ((st - s["p1600"]) / TICK[root]).dropna()

    # bars: coverage of what the model reads
    have = b.groupby("day")["hhmm"].apply(set)
    cov = {}
    for name, (lo, hi) in KEY_BARS.items():
        need = pd.date_range(f"2000-01-01 {lo}", f"2000-01-01 {hi}", freq="min").strftime("%H:%M")
        cov[name] = have.apply(lambda h, need=need: sum(x in h for x in need) / len(need))
    tmin = pd.to_datetime(b["day"] + " " + b["hhmm"])
    gaps = tmin.groupby(b["day"]).apply(lambda t: t.sort_values().diff().max().total_seconds() / 60 if len(t) > 1 else np.nan)

    out = s[["day", "contract", "roll", "bars", "p0930", "p1600", "p_prev_close_same", "prev_close_source", "p0945_next_same", "day_volume"]].copy()
    out = out.rename(columns={"day_volume": f"{root}_day_volume"})
    mv, micro_rec = micro_volume(root, pd.Index(out["day"]))
    out[f"{MICRO_OF[root]}_day_volume"] = mv.to_numpy()
    equiv = f"{root.lower()}_equiv_volume"
    out[equiv] = out[f"{root}_day_volume"] + out[f"{MICRO_OF[root]}_day_volume"] / 10
    for c in ("is_early_close", "fomc", "cpi", "quad_witching", "quarter_end", "month_end", "dst_transition_week"):
        out[c] = out["day"].map(cal[c]).fillna(False).astype(bool)
    rb = rebalance_days(root)
    out["index_rebalance"] = out["day"].isin(rb)
    out["cov_h4"] = out["day"].map(cov["h4"]).fillna(0.0)
    out["cov_entry_exit"] = out["day"].map(cov["entry_exit"]).fillna(0.0)
    out["max_bar_gap_min"] = out["day"].map(gaps)
    out["nyse_open"] = out["day"].isin(nyse)
    out["excluded"] = out["is_early_close"] | ~out["nyse_open"]
    out["exclusion_reason"] = np.where(~out["nyse_open"], "NYSE closed: no fund NAV, no rebalance",
                                       np.where(out["is_early_close"], "early close (s.3.4)", ""))

    # QA
    out = out[out["day"] >= START].reset_index(drop=True)  # the warm-up month only supplied t-1
    full = out[~out["excluded"]]
    qa = {
        "root": root, "span": [out["day"].min(), out["day"].max()], "sessions": int(len(out)),
        "excluded": out.loc[out["excluded"], ["day", "exclusion_reason", "bars"]].to_dict("records"),
        "bars_per_session_non_excluded": {"min": int(full["bars"].min()), "p01": float(full["bars"].quantile(0.01)),
                                          "median": float(full["bars"].median()), "sessions_below_380": int((full["bars"] < 380).sum())},
        "sessions_below_380": full.loc[full["bars"] < 380, ["day", "bars", "max_bar_gap_min"]].to_dict("records"),
        "coverage": {"h4_full_share": float((full["cov_h4"] == 1).mean()), "h4_min": float(full["cov_h4"].min()),
                     "entry_exit_full_share": float((full["cov_entry_exit"] == 1).mean()),
                     "entry_exit_min": float(full["cov_entry_exit"].min()),
                     "sessions_entry_exit_incomplete": full.loc[full["cov_entry_exit"] < 1, ["day", "cov_entry_exit"]].to_dict("records"),
                     "next_0945_same_present_share": float(full["p0945_next_same"].notna()[:-1].mean())},
        "p1600_missing": int(out["p1600"].isna().sum()),
        "same_contract_anchors": {
            "roll_days": int(out["roll"].sum()),
            "prev_close_missing": full.loc[full["p_prev_close_same"].isna(), ["day", "prev_close_source"]].to_dict("records"),
            "prev_close_after_half_day": int(full["prev_close_source"].str.contains("12:59").sum()),
            "p0945_next_same_missing": full.loc[full["p0945_next_same"].isna(), "day"].tolist(),
            "roll_days_priced": int((out["roll"] & out["p_prev_close_same"].notna()).sum()),
            "anchor_vs_fixture_prior_p1600": {"n": int(len(anchor_vs_fixture)),
                                              "abs_max": float(anchor_vs_fixture.max())}},
        "nyse_closed_sessions": out.loc[~out["nyse_open"], "day"].tolist(),
        "settlement_vs_1559_close_ticks": {"n": int(len(diff_ticks)), "exact_share": float((diff_ticks.abs() < 1e-9).mean()),
                                           "within_1_tick": float((diff_ticks.abs() <= 1 + 1e-9).mean()),
                                           "abs_p99": float(diff_ticks.abs().quantile(0.99)), "abs_max": float(diff_ticks.abs().max())},
        "flags": {c: int(out[c].sum()) for c in ("fomc", "cpi", "quad_witching", "quarter_end", "month_end", "index_rebalance",
                                                   "dst_transition_week", "is_early_close")},
        "rebalance_vs_quad_witching": {"rebalance_not_quad": sorted(set(out.loc[out["index_rebalance"] & ~out["quad_witching"], "day"])),
                                       "quad_not_rebalance": sorted(set(out.loc[out["quad_witching"] & ~out["index_rebalance"], "day"]))},
        "dst_weeks": {"sessions": int(out["dst_transition_week"].sum()),
                      "first_bar_not_0930": out.loc[out["dst_transition_week"] & out["p0930"].isna(), "day"].tolist()},
        "volume": {f"{MICRO_OF[root]}_first_nonzero": out.loc[out[f"{MICRO_OF[root]}_day_volume"] > 0, "day"].min(),
                   f"{root}_day_volume_zero": int((out[f"{root}_day_volume"] <= 0).sum()),
                   "micro_share_of_equiv_by_year": out.assign(y=out["day"].str[:4]).groupby("y").apply(
                       lambda g: float((g[f"{MICRO_OF[root]}_day_volume"] / 10).sum() / g[equiv].sum())).round(4).to_dict()},
        "reads": {"fut_index_sessions": sess_p.record, f"fut_{root}_rth_1m": bars_p.record, "cme_session_calendar": cal_p.record,
                  "fut_settle_strip": strip_p.record, "fut_micro_day_volume": micro_rec,
                  "fut_index_anchor_bars": anc_rec},
    }
    out.to_csv(OUT / f"phase2_{root}_sessions.csv.gz", index=False, encoding="utf-8", lineterminator="\n")
    (OUT / f"phase2_{root}_qa.json").write_text(json.dumps(qa, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    for name in ("span", "sessions", "bars_per_session_non_excluded", "p1600_missing", "same_contract_anchors", "settlement_vs_1559_close_ticks",
              "flags", "rebalance_vs_quad_witching", "dst_weeks", "volume"):
        print(f"  {name}: {qa[name]}")
    c = qa["coverage"]
    print(f"  coverage: h4 full {c['h4_full_share']:.4f} (min {c['h4_min']:.3f}); entry/exit full {c['entry_exit_full_share']:.4f} "
          f"(min {c['entry_exit_min']:.3f}); next 09:45 (same contract) present {c['next_0945_same_present_share']:.4f}")
    print(f"  excluded: {len(qa['excluded'])} early closes; sessions under 380 bars (non-excluded): {len(qa['sessions_below_380'])}")
    return 0


def selftest() -> int:
    assert str(third_friday(2023, 12).date()) == "2023-12-15" and str(third_friday(2024, 3).date()) == "2024-03-15"
    assert "2023-07-21" in rebalance_days("NQ") and "2023-07-21" not in rebalance_days("ES")
    m = pd.DataFrame({"root": ["MNQ", "MNQ"], "day": ["2025-02-28", "2025-03-03"], "day_volume": [1, 2]})
    try:
        assert_none_at_or_after(m, "day", RESERVED_FROM)
    except ReservedSliceError:
        pass
    else:
        raise AssertionError("a row at the seal must raise")
    print("selftest: 3 checks fire as they must")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", choices=["NQ", "ES"])
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else build(a.root) if a.root else 1)
