"""The opening prize-sizing table (post hoc, after D660): each candidate mechanism's one-way flow (sourced ranges,
docs/research/opening-prize-sizing-sources.md) turned into a price-impact band by the square-root law, against the bar
of data/opening/prize_bar.json (in-sample ES, the two years to 2025-02-28).

    python scripts/diag_opening_prize_table.py

Impact = Y x sigma_d x sqrt(Q / V). HIGH end: Y = 1, V = ES alone. LOW end: Y = 0.5, V = the linked complex
(ES + SPY + the index's stocks, taken as 3 x ES). Q is the one-way flow on the day it trades, in $bn. Flows quoted
"per 1% move" are feedback, not exogenous: they are sized at a 1% move. The law is for patient metaorders; a fast
concentrated flow can peak far higher (6 May 2010: 25x) and reverts, which is noted, not modelled.
Writes data/opening/prize_table.json.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BAR = json.loads((REPO / "data" / "opening" / "prize_bar.json").read_text(encoding="utf-8"))
OUT = REPO / "data" / "opening" / "prize_table.json"
ES = BAR["market"]["ES"]["recent"]
SIGMA, V_ES = ES["sigma_daily_bp"], ES["dollar_volume_median_bn"]
V_COMPLEX = 3.0 * V_ES
B = BAR["bar"]["ES"]
BREAK_EVEN, DAILY60, EVENT40 = B["break_even_s_bp"], B["daily_60min"]["s_needed_bp"], B["event_40_60min"]["s_needed_bp"]

# (id, mechanism, Q low, Q high in $bn one-way on the day, days a year it applies, when it trades,
#  anticipated before 10:00?, direction carried?, source key)
FLOWS = [
    ("8", "Opening-auction imbalance (whole NYSE+Nasdaq opening auction as the ceiling)", 0.2, 4.4, 250,
     "09:30 auction (before a 10:00 entry)", "yes: NYSE feed from 08:00, NOII from 09:28", "yes", "C3"),
    ("6a", "Dealer gamma, typical day (+$2-6bn per 1%; dampens)", 0.5, 2.0, 225, "all day, strongest at the close",
     "yes: carried OI", "no: damps the move", "C1"),
    ("6b", "Dealer gamma, negative tail (p5-p1: -$0.8 to -$2.2bn per 1%, at a 1% move)", 0.8, 2.2, 10,
     "all day; measured effect in the last 30 min", "partly (naive-sign OI)", "amplifies a move", "C1"),
    ("6c", "Dealer gamma, extreme (-$7.5bn per 1%, about 1% of days)", 7.5, 7.5, 2.5, "all day",
     "partly", "amplifies a move", "C1"),
    ("7", "0DTE dealer hedging in the morning, amplifying side only (-$1.1bn IQR to -$5bn extreme per 1% at 15:30, "
          "/2.5 at 10:00; the long-gamma side damps)", 0.44, 2.0,
     250, "weakest after the open (gamma ~ 1/sqrt T)", "no", "amplifies a move", "C1"),
    ("9a", "CTAs, ordinary day (S&P share of $3-8bn a week)", 0.2, 1.0, 250, "unestablished (claims of morning)",
     "yes: weekly bank notes", "yes", "C2"),
    ("9b", "CTAs, trigger day ($12.5-36bn over two weeks)", 1.2, 3.6, 10, "unestablished", "yes: trigger levels published",
     "yes", "C2"),
    ("10", "Vol-control, stress ($37-57bn a day modelled 2015; $84bn over 2 weeks in Aug 2024)", 8.0, 57.0, 5,
     "at or near the close, 1-2 day lag", "yes: rule replicable, notes published", "yes", "C2"),
    ("LETF", "Leveraged ETFs on a 1% day (NDX $1.9bn + SPX $0.8bn per 1%, up to 74% offset by fund flows)", 0.7, 2.7,
     250, "last 30-60 min", "yes: deterministic", "yes (with the day)", "C2"),
    ("PEN", "Pension quarter/month-end, US ($14-32bn over ~3-5 days)", 3.0, 10.0, 12,
     "last week; T-3 morning; close via overlays", "yes: published", "yes", "C2"),
    ("IDX", "Index reconstitution (net index flow ~0)", 0.0, 0.5, 4, "closing auction", "yes: weeks ahead", "no", "C2"),
    ("BB", "Buybacks ($4-6bn a day VWAP, no opening trade; one morning hour ~20%)", 0.8, 1.2, 180, "through the day",
     "yes: seasonality", "yes (buying)", "C2"),
    ("11", "Executed stops (0.9% of ES volume, spread across the day; one cascade a fraction)", 0.1, 0.5, 250,
     "intraday", "levels known, sizes not", "yes (through a level)", "C3"),
    ("12", "Forced deleveraging episode ($100-225bn over days)", 20.0, 50.0, 0.3, "days; often the close",
     "no (until under way)", "yes", "C2"),
]


def impact(q: float, y: float, v: float) -> float:
    return y * SIGMA * math.sqrt(max(q, 0.0) / v)


#: does the flow land after a 10:00 entry, inside a morning hold? (read from "when"; judged, and stated in the record)
AFTER_ENTRY = {"8": False, "6a": True, "6b": True, "6c": True, "7": True, "9a": None, "9b": None, "10": False,
               "LETF": False, "PEN": False, "IDX": False, "BB": True, "11": True, "12": True}
Z = 1.959964 + 0.841621


def bar_for(days_a_year: float) -> tuple[float, float]:
    """(vault events, the push sd needed): the daily bar for a daily mechanism, else the 60-minute event bar at the
    number of events the vault's 390 sessions would hold."""
    if days_a_year >= 200:
        return 390.0, DAILY60
    n = days_a_year * 390 / 252
    sig60, c = B["daily_60min"]["sigma_hold_bp"], BREAK_EVEN * 0.8
    return n, (Z * sig60 / math.sqrt(max(n, 1e-9)) + c) / 0.8


def main() -> int:
    rows = []
    for fid, name, lo, hi, days, when, antic, direction, src in FLOWS:
        i_lo, i_hi = impact(lo, 0.5, V_COMPLEX), impact(hi, 1.0, V_ES)
        n_v, need = bar_for(days)
        size_ok = i_hi >= need
        after = AFTER_ENTRY[fid]
        verdict = ("FAILS size: its best case is below the bar for its frequency" if not size_ok else
                   "FAILS timing: it lands before the entry or at the close" if after is False else
                   "FAILS direction: it damps moves" if direction.startswith("no") else
                   "OPEN: size clears; timing unestablished" if after is None else "SURVIVES")
        rows.append({"id": fid, "mechanism": name, "flow_bn": [lo, hi], "days_a_year": days,
                     "vault_events": round(n_v, 1), "push_needed_bp": round(need, 1),
                     "impact_bp": [round(i_lo, 1), round(i_hi, 1)], "lands_after_10am": after,
                     "when": when, "anticipated": antic, "direction": direction, "source": src, "verdict": verdict})
    # POOLING (the principal: "Does the frequency really matter if we overlay the flow of different candidates?").
    # One pre-registered book trades every member's events on one clock; the bar is set by the pooled count. Best case
    # per member (the HIGH impact), events counted with no overlap (upper n) and with the rare stress members sharing
    # days (lower n: the stress members count once, at the largest member's frequency).
    by = {r["id"]: r for r in rows}
    c_rt = BREAK_EVEN * 0.8
    pools = {
        "morning_60min": {"sigma": B["daily_60min"]["sigma_hold_bp"],
                          "members": {"6b": 10, "6c": 2.5, "9b": 10, "12": 0.3}, "stress": ["6b", "6c", "9b", "12"]},
        "close_30min": {"sigma": ES["sigma_1530_close_bp"],
                        "members": {"6b": 10, "6c": 2.5, "10": 5, "PEN": 12, "LETF": 55},
                        "stress": ["6b", "6c", "10"]},
    }
    pooled = {}
    for name, p in pools.items():
        mem = p["members"]
        w_imp = sum(by[k]["impact_bp"][1] * d for k, d in mem.items()) / sum(mem.values())
        out_p = {"sigma_hold_bp": p["sigma"], "members": mem, "freq_weighted_best_case_impact_bp": round(w_imp, 1)}
        for lab, days in (("no_overlap", sum(mem.values())),
                          ("stress_days_shared", sum(d for k, d in mem.items() if k not in p["stress"])
                           + max(mem[k] for k in p["stress"]))):
            n = days * 390 / 252
            need = (Z * p["sigma"] / math.sqrt(n) + c_rt) / 0.8
            out_p[lab] = {"days_a_year": days, "vault_events": round(n, 1), "push_needed_bp": round(need, 1),
                          "clears_at_best_case": bool(w_imp >= need)}
        pooled[name] = out_p
    doc_pooled = pooled
    doc = {"pooled": doc_pooled, "inputs": {"sigma_daily_bp": SIGMA, "V_es_bn": V_ES, "V_complex_bn": V_COMPLEX, "bar_break_even_bp": BREAK_EVEN,
                      "bar_daily_60min_bp": DAILY60, "bar_event_40_bp": EVENT40}, "rows": rows}
    OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    for r in rows:
        print(f"{r['id']:>5} {r['impact_bp'][0]:5.1f}-{r['impact_bp'][1]:5.1f} bp  need {r['push_needed_bp']:5.1f} "
              f"(n {r['vault_events']:6.1f})  {r['verdict']:<58} {r['mechanism'][:50]}")
    print(json.dumps(doc["inputs"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
