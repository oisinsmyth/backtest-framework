"""Shock classifier Phase 1 / Gate 0 (SHOCK_CLASSIFIER_PREREG.md s.7, s.10; SC-A1..A6): data validity, not a hypothesis.

    python scripts/shock_gate0.py          # SYSTEM interpreter (pyarrow) -> data/shock/gate0.json

The deposit's three conditions:
- (G1, as SC-A6 reads it) over USABLE sessions (NYSE trading days that are not half days, less the archive-outage
  days, logged): each TRADED market's bars cover >= 99% of the minutes the model reads in its window (the detection
  window, plus w = 3's lookback and the 60-minute hold); each PEER has a price (its last trade no more than 5 minutes
  old, within the session) on >= 99% of those minutes, with its literal bar coverage reported beside it. RTY is a
  peer from 2017-07-10. GC, SI, 6E and ZN read 08:22 -> 08:59 from fut_premarket_1m (SC-A4) and the rest from
  fut_day1m. Only the `present` flag and the contract are read: no price.
  (The literal reading, CME sessions and bars for every root, FAILED at 775f215; that result is in git history.)
- (G2) the calendar is sourced and verified: data/calendar/events.csv (D585, verified there by its own gates
  G1..G6 against the official schedules). Re-checked here: every row carries a source URL and a method, the five
  events s.3.4 names are present in every in-sample year, and no timestamp fails to parse.
- (G3) roll days are identified: the days the front-by-volume contract changes, per traded root, listed.
In-sample 2016-01-04 -> 2025-02-28; nothing on or after 2025-03-01 is read (A10).
"""
from __future__ import annotations

import gzip
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
SPY = REPO / "data" / "raw" / "alphavantage" / "daily" / "SPY.json.gz"  # the NYSE calendar (D637, D638)
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


STALE_MAX = 5
PEER_FROM = {"RTY": "2017-07-10"}
NON_EQUITY = ("CL", "BZ", "HO", "RB", "GC", "SI", "ZN", "6E", "6J")


def nyse_days() -> set[str]:
    d = json.load(gzip.open(SPY, "rt", encoding="utf-8"))
    return {x for x in d if START <= x < RESERVED_FROM}


def staleness(flags: list[bool]) -> list[int]:
    last, out = -10**6, []
    for i, x in enumerate(flags):
        if x:
            last = i
        out.append(i - last)
    return out


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
    half = set(cal.loc[(cal["root"] == "ES") & cal["is_early_close"].astype(bool), "day"])
    present = {r: set(zip(t.loc[(t["root"] == r) & t["present"], "day"], t.loc[(t["root"] == r) & t["present"], "hhmm"]))
               | set(zip(pre.loc[pre["root"] == r, "day"], pre.loc[pre["root"] == r, "hhmm"])) for r in roots}
    base = sorted(nyse_days() - half)
    empty = {d: sum(1 for r in NON_EQUITY if not any((d, m) in present[r] for m in need[r])) for d in base}
    outage = sorted(d for d, n in empty.items() if n >= 4)
    usable = [d for d in base if d not in outage]
    res: dict = {"span": [START, "2025-02-28"], "usable_sessions": len(usable), "half_days_excluded": len(half & nyse_days()),
                 "outage_days_excluded": outage, "rule": "SC-A6", "G1_coverage": {}, "G3_roll_days": {}}
    ok1 = True
    for r in roots:
        days = [d for d in usable if d >= PEER_FROM.get(r, START)]
        mins = need[r]
        cov, stale_ok, n_min = [], 0, 0
        for d in days:
            fl = [(d, m) in present[r] for m in mins]
            cov.append(sum(fl) / len(fl))
            st = staleness(fl)
            stale_ok += sum(1 for x in st if x <= STALE_MAX)
            n_min += len(st)
        cov_s = pd.Series(cov, index=days)
        role = "traded" if r in TRADED else "peer"
        literal = float(cov_s.mean())
        priced = stale_ok / n_min
        passed = literal >= 0.99 if role == "traded" else priced >= 0.99
        res["G1_coverage"][r] = {"role": role, "window": [mins[0], mins[-1]], "minutes": len(mins),
                                 "sessions": len(days), "from": days[0], "literal_bar_coverage": literal,
                                 "sessions_ge_99pct": float((cov_s >= 0.99).mean()),
                                 f"priced_within_{STALE_MAX}min": priced,
                                 "worst_sessions": {d: float(v) for d, v in cov_s.nsmallest(3).items()}, "pass": bool(passed)}
        ok1 &= passed
    for r in TRADED:
        c = t[(t["root"] == r) & t["day"].isin(usable)].groupby("day")["contract"].first().sort_index()
        rolls = c.index[c.ne(c.shift(1)) & c.shift(1).notna()]
        res["G3_roll_days"][r] = {"n": int(len(rolls)), "by_year": pd.Series(rolls.str[:4]).value_counts().sort_index().to_dict(),
                                  "days": list(rolls)}
    ok3 = all(v["n"] > 0 for v in res["G3_roll_days"].values())
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
    print(f"  usable sessions {len(usable)}; outage days {outage}")
    for r, v in res["G1_coverage"].items():
        print(f"  {r:4s} {v['role']:6s} {v['window'][0]}-{v['window'][1]} sessions {v['sessions']} literal "
              f"{v['literal_bar_coverage']:.4f} (>=99%: {v['sessions_ge_99pct']:.3f}) priced<=5m "
              f"{v[f'priced_within_{STALE_MAX}min']:.4f} -> {'PASS' if v['pass'] else 'FAIL'}")
    print("  roll days:", {r: v["n"] for r, v in res["G3_roll_days"].items()})
    print("  calendar:", {k: res["G2_calendar"][k] for k in ("rows", "unparsed", "rows_without_source", "event_years_missing")})
    print("  GATE 0:", res["verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
