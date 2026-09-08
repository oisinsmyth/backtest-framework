"""Gate an intraday fixture so `ragged_panel.assert_gates_passed` can accept it.

    uv run python scripts/gate_intraday_fixture.py --fixture etf_intraday_15m_raw
    uv run python scripts/gate_intraday_fixture.py --fixture etf_intraday_15m_raw --write

WHY THIS EXISTS. No intraday fixture in this repo carries a gate the loader recognises. `etf_intraday_15m_raw` has no `gates` key at
all; `wide_extended_15m_raw` and `index_extended_15m_raw` have one, but it holds COVERAGE REPORTS -- booleans and rates -- with no
`failures` list, and `assert_gates_passed` refuses a block that declares no gate. So the substance largely exists and the CONTRACT does
not.

AND THE DAILY GATES DO NOT TRANSFER. gate_a tests confirmed splits against price continuity at the effective date and gate_b tests
adjusted-close ratios; intraday bars carry neither an adjusted close nor a split coefficient. The real intraday failure modes are
different and are what this file gates.

EVERYTHING IS RECOMPUTED FROM THE FIXTURE, NEVER READ FROM THE META. That is the whole lesson of D256: the fixture that carried x300
and x66.7 fabricated returns had a meta that DESCRIBED its own failing gates, and the caller read straight past them. A gate that
trusts the meta it is writing gates nothing.

THE FOUR GATES

  gate_i1  GRID     every timestamp lies on the interval's own grid; per symbol strictly increasing, no duplicates.
                    An off-grid or duplicated stamp means a resampling or merge error upstream.
  gate_i2  OHLC     low <= min(open, close), high >= max(open, close), high >= low, every price > 0.
                    An OHLC bar that fails this is not a bar.
  gate_i3  BAR      no |log(close/prev_close)| WITHIN a session above INTRABAR_LIMIT unless documented. The intraday analogue of
                    gate_b, and the threshold is the one wide_extended_15m already set for itself: 0.15.
  gate_i5  GAP      no |log(open_first / close_last)| ACROSS a session boundary above OVERNIGHT_LIMIT unless documented.
                    THIS IS THE ONE THAT MATTERS MOST for a multi-year intraday ETF panel: provider intraday data is unadjusted, so a
                    split -- and leveraged/inverse ETFs reverse-split often -- appears as a single enormous overnight gap and would be
                    read as a return. The daily fixture catches this with gate_a; intraday has nothing, until here.

Session shape (incomplete sessions, half days) is REPORTED and not gated: the RTH build already drops half days to keep its grid
rectangular, and a short session is a calendar fact rather than a data defect. Reported so a reader can see it, per D192.
"""

from __future__ import annotations

import argparse
import gzip
import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
FIXTURES = REPO / "data" / "fixtures"

INTERVAL_MIN = 15
INTRABAR_LIMIT = 0.15              # wide_extended_15m_raw's own `large_bar_threshold`, adopted rather than invented
OVERNIGHT_LIMIT = 0.25             # an ETF that gaps >25% overnight has had a corporate action, not a return
MAX_SUSPECT_RATE = 0.0             # a gate with a non-empty failures list refuses the fixture; there is no tolerated rate

# Moves ADJUDICATED AGAINST EVIDENCE and recorded with it. Nothing is listed here to make a gate pass; each entry names what
# corroborates it, so a reader can check the adjudication rather than take it.
#
# The first run of this gate flagged exactly three moves. All three survived adjudication, which is why they are here -- and the
# alternative, excluding the symbols, was NOT taken, because the daily builder's precedent is to exclude only what stays UNexplained.
DOCUMENTED = {
    ("USO", "2020-03-09"): "Saudi-Russia oil price war. wide_extended_15m_raw.meta.json documents it; WTI fell ~25% that session.",
    ("USO", "2020-04-02"): "Rebound from the same episode; documented in wide_extended_15m_raw.meta.json.",
    # Already adjudicated by this programme, on THIS date, and my first allow-list simply failed to carry them forward:
    ("XOP", "2020-03-09"): "Same oil-war session. wide_extended_15m_raw.meta.json records D226 documenting XOP -36.9% as REAL.",
    ("OIH", "2020-03-09"): "Same oil-war session. wide_extended_15m_raw.meta.json records D226 documenting OIH -32.2% as REAL.",
    # Adjudicated here, against an INDEPENDENT series rather than by inspection of the intraday bars alone:
    ("GDXJ", "2020-03-19"): ("March 2020, junior gold miners. The 15:45 bar falls 30.53 -> 25.79 and the next session opens 28.57, "
                             "which looks like a print until it is checked against the daily cache: daily 2020-03-19 is "
                             "o 25.07 h 31.81 l 24.05 c 25.82 -- matching the intraday close to 3 cents -- and daily 2020-03-20 "
                             "opens 28.57, matching exactly. Split coefficient 1.0, so no corporate action. Two independent series "
                             "agree bar for bar; the move is REAL."),
}


def read_rows(path):
    per = defaultdict(list)
    with gzip.open(path, "rt") as f:
        hdr = next(f).strip().split(",")
        ix = {c: i for i, c in enumerate(hdr)}
        for line in f:
            p = line.rstrip("\n").split(",")
            per[p[ix["symbol"]]].append((p[ix["timestamp"]], float(p[ix["open"]]), float(p[ix["high"]]),
                                         float(p[ix["low"]]), float(p[ix["close"]]), float(p[ix["volume"]])))
    return per


def gate(path):
    per = read_rows(path)
    f1, f2, f3, f5 = [], [], [], []
    sessions = defaultdict(int)
    n_rows = 0
    for sym, rows in per.items():
        n_rows += len(rows)
        ts = [r[0] for r in rows]
        # gate_i1 -- grid, order, duplicates
        seen = set()
        prev_t = None
        for t in ts:
            if t in seen:
                f1.append(dict(symbol=sym, timestamp=t, why="duplicate timestamp"))
            seen.add(t)
            if prev_t is not None and t <= prev_t:
                f1.append(dict(symbol=sym, timestamp=t, why=f"not strictly increasing after {prev_t}"))
            mn = int(t[14:16]) if len(t) >= 16 else 0
            if mn % INTERVAL_MIN:
                f1.append(dict(symbol=sym, timestamp=t, why=f"off the {INTERVAL_MIN}-minute grid"))
            prev_t = t
        # gate_i2 -- OHLC consistency
        for t, o, h, l, c, _v in rows:
            if not (o > 0 and h > 0 and l > 0 and c > 0):
                f2.append(dict(symbol=sym, timestamp=t, why="non-positive price"))
            elif l > min(o, c) + 1e-9 or h < max(o, c) - 1e-9 or h < l:
                f2.append(dict(symbol=sym, timestamp=t, why=f"o{o} h{h} l{l} c{c} is not an OHLC bar"))
        # gate_i3 / gate_i5 -- moves within a session and across its boundary
        for i in range(1, len(rows)):
            t0, c0 = rows[i - 1][0], rows[i - 1][4]
            t1, o1, c1 = rows[i][0], rows[i][1], rows[i][4]
            same_day = t0[:10] == t1[:10]
            if same_day:
                r = abs(np.log(c1 / c0)) if c0 > 0 and c1 > 0 else np.inf
                if r > INTRABAR_LIMIT and (sym, t1[:10]) not in DOCUMENTED:
                    f3.append(dict(symbol=sym, timestamp=t1, log_move=round(float(r), 4),
                                   why=f"|log move| {r:.3f} within a session, above {INTRABAR_LIMIT}"))
            else:
                r = abs(np.log(o1 / c0)) if c0 > 0 and o1 > 0 else np.inf
                if r > OVERNIGHT_LIMIT and (sym, t1[:10]) not in DOCUMENTED:
                    f5.append(dict(symbol=sym, date=t1[:10], prev_close=c0, open=o1,
                                   log_move=round(float(r), 4), ratio=round(float(o1 / c0), 4),
                                   why=f"|log gap| {r:.3f} across a session boundary, above {OVERNIGHT_LIMIT} -- "
                                       "unadjusted intraday data shows a split as exactly this"))
            sessions[(sym, t1[:10])] += 1

    counts = np.array(list(sessions.values()), float)
    return dict(
        fixture=path.name, symbols=len(per), rows=n_rows,
        gates={
            "gate_i1": dict(definition=f"every timestamp on the {INTERVAL_MIN}-minute grid, strictly increasing, no duplicates",
                            failures=f1[:200], n_failures=len(f1)),
            "gate_i2": dict(definition="low <= min(open, close), high >= max(open, close), high >= low, every price > 0",
                            failures=f2[:200], n_failures=len(f2)),
            "gate_i3": dict(definition=f"no |log(close/prev_close)| WITHIN a session above {INTRABAR_LIMIT} unless documented",
                            threshold=INTRABAR_LIMIT, failures=f3[:200], n_failures=len(f3)),
            "gate_i5": dict(definition=(f"no |log(open/prev_close)| ACROSS a session boundary above {OVERNIGHT_LIMIT} unless "
                                        "documented -- unadjusted intraday data shows a split as exactly this"),
                            threshold=OVERNIGHT_LIMIT, failures=f5[:200], n_failures=len(f5)),
            "session_shape_REPORTED_NOT_GATED": dict(
                note="a short session is a calendar fact, not a data defect (D192): reported so a reader can see it",
                sessions=int(counts.size), median_bars=float(np.median(counts)) if counts.size else None,
                p05_bars=float(np.percentile(counts, 5)) if counts.size else None,
                short_session_rate=float((counts < 0.5 * np.median(counts)).mean()) if counts.size else None),
            "documented_moves": {f"{s}|{d}": w for (s, d), w in DOCUMENTED.items()},
        })


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", required=True)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    path = FIXTURES / f"{a.fixture}.csv.gz"
    print(f"gating {path.name}  (everything RECOMPUTED from the fixture, nothing read from its meta -- D256)")
    t0 = time.time()
    rep = gate(path)
    print(f"  {rep['symbols']} symbols, {rep['rows']:,} rows  ({time.time() - t0:.0f}s)")
    clean = True
    for k, v in rep["gates"].items():
        if isinstance(v, dict) and "failures" in v:
            n = v["n_failures"]
            clean &= n == 0
            print(f"  {k:<10} {n:>6,} failures   {v['definition'][:78]}")
            for r in v["failures"][:3]:
                print(f"       {r}")
    ss = rep["gates"]["session_shape_REPORTED_NOT_GATED"]
    print(f"  session shape (reported): {ss['sessions']:,} sessions, median {ss['median_bars']} bars, "
          f"short-session rate {ss['short_session_rate']:.3%}")
    print(f"\n  {'GATES CLEAN' if clean else 'GATES FAILED -- this fixture is not fit to load'}")
    if a.write:
        mp = FIXTURES / f"{a.fixture}.meta.json"
        meta = json.loads(mp.read_text(encoding="utf-8")) if mp.exists() else {}
        assert "gates" not in meta or not [k for k, v in meta["gates"].items()
                                           if isinstance(v, dict) and "failures" in v], \
            "[SAFE] this meta already declares a real gate; refusing to overwrite it"
        meta["gates"] = rep["gates"]
        meta["gated_by"] = dict(script="scripts/gate_intraday_fixture.py", at_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                note="the fetcher's own keys are preserved; only `gates` was added")
        mp.write_text(json.dumps(meta, indent=1))
        print(f"  wrote {mp}")
    return 0 if clean else 1


if __name__ == "__main__":
    raise SystemExit(main())
