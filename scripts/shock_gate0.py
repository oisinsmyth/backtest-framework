"""Shock classifier Phase 1 / Gate 0 (SHOCK_CLASSIFIER_PREREG.md s.7, s.10; SC-A1..A5): data validity, not a hypothesis.

    python scripts/shock_gate0.py          # SYSTEM interpreter (pyarrow) -> data/shock/gate0.json

The deposit's three conditions:
- (G1) bars cover >= 99% of expected session minutes, per root, inside the window the model reads (the detection
  window, plus w = 3's lookback and the 60-minute hold), over USABLE sessions: CME trading sessions that are not
  early closes (cme_session_calendar). GC, SI, 6E and ZN read 08:22 -> 08:59 from fut_premarket_1m (SC-A4) and the
  rest from fut_day1m. Only the `present` flag and the contract are read: no price.
- (G2) the calendar is sourced and verified: data/calendar/events.csv (D585, verified there by its own gates
  G1..G6 against the official schedules). Re-checked here: every row carries a source URL and a method, the five
  events s.3.4 names are present in every in-sample year, and no timestamp fails to parse.
- (G3) roll days are identified: the days the front-by-volume contract changes, per traded root, listed.
In-sample 2016-01-04 -> 2025-02-28; nothing on or after 2025-03-01 is read (A10).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pyarrow.dataset as ds

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "shock" / "gate0.json"
DAY1M = REPO / "data" / "fixtures" / "fut_day1m.parquet"
PRE = REPO / "data" / "fixtures" / "fut_premarket_1m.csv.gz"
CAL = REPO / "data" / "fixtures" / "cme_session_calendar.csv.gz"
EVENTS = REPO / "data" / "calendar" / "events.csv"
START, RESERVED_FROM = "2016-01-04", "2025-03-01"
TRADED = {"NQ": ("09:35", "14:55"), "ES": ("09:35", "14:55"), "CL": ("09:05", "13:25"), "GC": ("08:25", "12:25")}
PEERS = {"NQ": ["ES", "RTY", "ZN", "6J"], "ES": ["NQ", "RTY", "ZN", "6J"], "CL": ["BZ", "HO", "RB"], "GC": ["SI", "6E", "ZN"]}
EVENTS_NEEDED = ("CPI", "EMPSIT", "FOMC", "EIA_WPSR", "EIA_NGSR")


def minutes(a: str, b: str) -> list[str]:
    return list(pd.date_range(f"2000-01-01 {a}", f"2000-01-01 {b}", freq="min").strftime("%H:%M"))


def needed() -> dict[str, list[str]]:
    """Per root, the minutes the model reads: the detection window less w = 3 (lookback), plus 60 minutes of hold."""
    out: dict[str, set[str]] = {}
    for t, (a, b) in TRADED.items():
        lo = (pd.Timestamp(f"2000-01-01 {a}") - pd.Timedelta(minutes=3)).strftime("%H:%M")
        hi = (pd.Timestamp(f"2000-01-01 {b}") + pd.Timedelta(minutes=65)).strftime("%H:%M")
        for r in [t] + PEERS[t]:
            out.setdefault(r, set()).update(minutes(lo, min(hi, "15:59")))
    return {r: sorted(v) for r, v in out.items()}


def main() -> int:
    need = needed()
    roots = sorted(need)
    f = (ds.field("day") >= START) & (ds.field("day") < RESERVED_FROM) & ds.field("root").isin(roots)
    t = ds.dataset(DAY1M).to_table(columns=["root", "day", "bar", "contract", "present"], filter=f).to_pandas()
    t["hhmm"] = (pd.Timestamp("2000-01-01 09:00") + pd.to_timedelta(t["bar"], unit="m")).dt.strftime("%H:%M")
    pre = pd.read_csv(PRE, encoding="utf-8", usecols=["root", "day", "hhmm", "front"], dtype={"day": str})
    pre = pre[(pre["day"] >= START) & (pre["day"] < RESERVED_FROM) & pre["front"]]
    if (t["day"] >= RESERVED_FROM).any() or (pre["day"] >= RESERVED_FROM).any():
        raise RuntimeError("a sealed session was read")
    cal = pd.read_csv(CAL, encoding="utf-8", dtype={"day": str})
    cal = cal[(cal["day"] >= START) & (cal["day"] < RESERVED_FROM)]
    res: dict = {"span": [START, "2025-02-28"], "G1_coverage": {}, "G3_roll_days": {}}
    ok1 = True
    for r in roots:
        usable = set(cal.loc[(cal["root"] == r) & cal["is_trading"].astype(bool) & ~cal["is_early_close"].astype(bool), "day"])
        have = set(zip(t.loc[(t["root"] == r) & t["present"], "day"], t.loc[(t["root"] == r) & t["present"], "hhmm"]))
        have |= set(zip(pre.loc[pre["root"] == r, "day"], pre.loc[pre["root"] == r, "hhmm"]))
        mins = need[r]
        per = pd.Series({d: sum((d, m) in have for m in mins) / len(mins) for d in sorted(usable)})
        pooled = float(per.mean()) if len(per) else 0.0
        worst = per.nsmallest(5)
        res["G1_coverage"][r] = {"window": [mins[0], mins[-1]], "minutes": len(mins), "usable_sessions": int(len(per)),
                                 "pooled": pooled, "sessions_ge_99pct": float((per >= 0.99).mean()),
                                 "worst_sessions": {d: float(v) for d, v in worst.items()}, "pass": bool(pooled >= 0.99)}
        ok1 &= pooled >= 0.99
    # G3: roll days per traded root
    for r in TRADED:
        c = t[t["root"] == r].groupby("day")["contract"].first().sort_index()
        rolls = c.index[c.ne(c.shift(1)) & c.shift(1).notna()]
        res["G3_roll_days"][r] = {"n": int(len(rolls)), "by_year": pd.Series(rolls.str[:4]).value_counts().sort_index().to_dict(),
                                  "days": list(rolls)}
    ok3 = all(v["n"] > 0 for v in res["G3_roll_days"].values())
    # G2: the calendar
    e = pd.read_csv(EVENTS, encoding="utf-8")
    e = e[e["datetime_et"].astype(str).str[:10] < RESERVED_FROM]
    parsed = pd.to_datetime(e["datetime_et"], errors="coerce", utc=True)
    yrs = [str(y) for y in range(2016, 2025)]
    counts = {ev: e[e["event"] == ev]["datetime_et"].astype(str).str[:4].value_counts().to_dict() for ev in EVENTS_NEEDED}
    missing = [(ev, y) for ev in EVENTS_NEEDED for y in yrs if counts[ev].get(y, 0) == 0]
    res["G2_calendar"] = {"rows": int(len(e)), "unparsed": int(parsed.isna().sum()),
                          "rows_without_source": int(e["source_url"].isna().sum() + (e["source_url"].astype(str).str.strip() == "").sum()),
                          "methods": e["method"].value_counts().to_dict(), "per_event_year": counts,
                          "event_years_missing": missing, "verified_by": "D585 gates G1..G6 (scripts/fetch_release_calendar.py)"}
    ok2 = res["G2_calendar"]["unparsed"] == 0 and res["G2_calendar"]["rows_without_source"] == 0 and not missing
    res["verdict"] = {"G1": bool(ok1), "G2": bool(ok2), "G3": bool(ok3), "gate0": bool(ok1 and ok2 and ok3)}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    for r, v in res["G1_coverage"].items():
        print(f"  {r:4s} {v['window'][0]}-{v['window'][1]} ({v['minutes']} min)  usable {v['usable_sessions']}  pooled "
              f"{v['pooled']:.4f}  >=99%: {v['sessions_ge_99pct']:.4f}  worst {list(v['worst_sessions'].items())[:2]}")
    print("  roll days:", {r: v["n"] for r, v in res["G3_roll_days"].items()})
    print("  calendar:", {k: res["G2_calendar"][k] for k in ("rows", "unparsed", "rows_without_source", "event_years_missing", "methods")})
    print("  GATE 0:", res["verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
