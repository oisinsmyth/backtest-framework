"""D447 -- is the overnight drift a property of the SETTLEMENT RULE? The US natural experiment.

    uv run python scripts/d447_settlement_regimes.py

THE CLAIM UNDER TEST, and it is external. Prop-firm research lane 19 found China's natural
experiment -- same underlying, same days, 2016-01-11 to 2019-11-29 -- giving OPPOSITE SIGNS on
the overnight return: T+1 cash index -0.073% (t -4.03), T+0 IF future +0.055% (t +3.19). The
claim it supports: "the overnight drift is a property of the SETTLEMENT RULE, not of the passage
of time."

WHY THIS MATTERS HERE. C1's +9.04%/yr overnight drift is measured on EQUITY extended-hours bars
and would be traded as a FUTURE. If the drift is a settlement artefact it may not exist in the
instrument at all, and D440's entire input series would have no counterpart in what gets traded.

THE FALSIFIER THE LEADS DOC NAMED needs ES beside SPY. The futures acquisition has 2010-06-06 to
2022-08-17 of ohlcv-1m on disk, but as ALL_SYMBOLS raw DBN in temp/ with no continuous series
built and a live job still writing. So that test is NOT run here.

WHAT IS RUN INSTEAD, AND IT NEEDS NO FUTURES DATA. The US changed its settlement rule twice
inside this fixture's window:

    T+3   2010-01-04 .. 2017-09-02        }  both transition dates are the ones the corporate-
    T+2   2017-09-05 .. 2024-05-24        }  action research independently flagged as DECLARED
    T+1   2024-05-28 .. 2026-08           }  EX-DIVIDEND HOLES, which corroborates them

If the drift is a property of the settlement lag, it should STEP DOWN as the lag shortens. This
is a within-instrument comparison -- same market, same names, same construction -- where the
China evidence is cross-instrument. It is weaker in one way (a time series with era confounds)
and stronger in another (only the rule changes).

THE PLACEBO IS THE WHOLE STUDY. Regular trading hours carry no overnight financing and no
settlement exposure of this kind, so RTH must show NO monotone pattern. If it shows the same
pattern, what is being measured is the era and not the rule.

PREDICTIONS, WRITTEN BEFORE THE RUN:
  X1  the overnight drift is NOT cleanly monotone in the settlement lag. A one-day change in
      settlement should not move an 8%/yr drift, and I expect the natural experiment to fail to
      support the mechanism on US data.
  X2  whatever pattern appears in overnight also appears, in the same direction, in RTH --
      which would make it era rather than settlement.
  X3  the T+1 regime is ~2.2 years and its SE is wide enough that T+2 vs T+1 is UNRESOLVED at
      2 SE whichever way the point estimates fall.

NO HURDLE IS CLAIMED AND NO CANDIDATE IS SCORED. This is a MEASUREMENT.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import run_overnight_decomposition as ODR       # noqa: E402

OUT = REPO / "data" / "d447_settlement_regimes.json"

# US settlement-cycle changes, by FIRST TRADE DATE under the new rule.
T2_START = date(2017, 9, 5)      # SEC amendment to Rule 15c6-1: T+3 -> T+2
T1_START = date(2024, 5, 28)     # T+2 -> T+1
REGIMES = ("T+3", "T+2", "T+1")
LAG = {"T+3": 3, "T+2": 2, "T+1": 1}
WINDOWS = ("post", "untraded", "pre", "rth", "overnight")


def regime_of(day: str) -> str:
    """Keyed on the ENTRY date -- the purchase is at that session's close, and it is that
    trade whose settlement lag is in question. One day either side of a boundary is
    immaterial except exactly at it."""
    d = date.fromisoformat(day)
    return "T+3" if d < T2_START else ("T+2" if d < T1_START else "T+1")


def ann(r: np.ndarray, days: pd.Series) -> tuple[float, float, float]:
    """(annualised log return, mean bp/session, t of the mean)."""
    if len(r) < 3:
        return float("nan"), float("nan"), float("nan")
    span = (date.fromisoformat(days.max()) - date.fromisoformat(days.min())).days / 365.25
    lr = np.log1p(r)
    t = float(r.mean() / (r.std(ddof=1) / np.sqrt(len(r))))
    return float(lr.sum() / span) if span > 0 else float("nan"), float(1e4 * r.mean()), t


def main() -> int:
    df = ODR.load()
    df = df[df["suspect"] == 0]
    drop = ODR.half_days(df)

    def build(strict: bool) -> pd.DataFrame:
        frames = []
        for sym in ODR.SYMBOLS:
            sess = ODR.sessions_for(df, sym, drop)
            x = ODR.decompose(sess, sym, strict=strict)
            if not x.empty:
                frames.append(x)
        out = pd.concat(frames, ignore_index=True)
        out["regime"] = out["prev_day"].map(regime_of)
        out["lag"] = out["regime"].map(LAG)
        return out

    d = build(False)
    d_strict = build(True)

    print("D447 -- the overnight drift by US SETTLEMENT REGIME\n")
    print(f"  {len(d):,} session pairs, 4 symbols, suspect bars excluded\n")
    print(f"  {'regime':<7}{'lag':>4}{'from':>12}{'to':>12}{'pairs':>8}")
    for g in REGIMES:
        s = d[d["regime"] == g]
        print(f"  {g:<7}{LAG[g]:>4}{s['prev_day'].min():>12}{s['prev_day'].max():>12}"
              f"{len(s):>8,}")

    rows = []
    for excl_2020 in (False, True):
        sub = d[~d["day"].str.startswith("2020")] if excl_2020 else d
        tag = "EXCLUDING 2020" if excl_2020 else "ALL YEARS"
        print(f"\n{'=' * 78}\n{tag}\n")
        print(f"  {'window':<11}" + "".join(f"{g:>24}" for g in REGIMES))
        print(f"  {'':<11}" + "".join(f"{'ann%':>9}{'bp':>7}{'t':>8}" for _ in REGIMES))
        for w in WINDOWS:
            line = f"  {w:<11}"
            for g in REGIMES:
                s = sub[sub["regime"] == g]
                a, bp, t = ann(s[w].to_numpy(dtype=float), s["day"])
                line += f"{100 * a:>8.2f}%{bp:>7.2f}{t:>8.2f}"
                rows.append({"excl_2020": excl_2020, "window": w, "regime": g,
                             "ann": a, "bp": bp, "t": t, "n": len(s)})
            print(line)

        # the monotonicity test, and its placebo
        print()
        for w in ("overnight", "rth"):
            vals = [ann(sub[sub["regime"] == g][w].to_numpy(dtype=float),
                        sub[sub["regime"] == g]["day"])[0] for g in REGIMES]
            mono = vals[0] > vals[1] > vals[2]
            # OLS of the per-session return on the settlement lag
            x = sub["lag"].to_numpy(dtype=float)
            y = sub[w].to_numpy(dtype=float)
            b1 = np.polyfit(x, y, 1)[0]
            resid = y - np.polyval(np.polyfit(x, y, 1), x)
            se = float(np.sqrt((resid ** 2).sum() / (len(y) - 2)
                               / ((x - x.mean()) ** 2).sum()))
            label = "PLACEBO" if w == "rth" else "TEST   "
            print(f"  {label} {w:<10} monotone T+3>T+2>T+1: {str(mono):<5}"
                  f"   slope/lag {1e4 * b1:>+7.3f} bp   t {b1 / se:>+6.2f}")
            rows.append({"excl_2020": excl_2020, "window": w, "regime": "SLOPE",
                         "monotone": bool(mono), "slope_bp": 1e4 * b1, "t": b1 / se})

    # ------------------------------------------------------------------------------------
    # THE COVERAGE CONFOUND, AND IT IS THE WHOLE STORY. The `pre` window is the one whose
    # MEASUREMENT changed most over sixteen years -- D259 measured the share of sessions
    # printing an actual 04:00 bar at 22.1% for DIA in 2010-2019 against 89.8% in 2021-2026.
    # A window that is observed more often in later years will carry more return in later
    # years for reasons that have nothing to do with any rule. `strict` keeps only sessions
    # printing a literal 19:45 AND a literal 04:00 bar, which makes the windows mean the same
    # thing in every regime at the cost of a liquidity-selected sample. Both readings stand.
    # ------------------------------------------------------------------------------------
    print(f"\n{'=' * 78}\nDECOMPOSING THE REGIME GAP, ex-2020 -- where does T+1's excess live?\n")
    sub = d[~d["day"].str.startswith("2020")]
    base = {w: ann(sub[sub["regime"] == "T+3"][w].to_numpy(dtype=float),
                   sub[sub["regime"] == "T+3"]["day"])[0] for w in WINDOWS}
    top = {w: ann(sub[sub["regime"] == "T+1"][w].to_numpy(dtype=float),
                  sub[sub["regime"] == "T+1"]["day"])[0] for w in WINDOWS}
    gap = top["overnight"] - base["overnight"]
    print(f"  T+1 overnight minus T+3 overnight: {100 * gap:+.2f} pts, of which")
    for w in ("post", "untraded", "pre"):
        c = top[w] - base[w]
        print(f"    {w:<10}{100 * c:>+8.2f} pts  ({100 * c / gap:>5.1f}% of the gap)")

    print(f"\n{'=' * 78}\nSTRICT -- literal 19:45 and 04:00 prints only, so the windows are "
          f"comparable\n")
    ss = d_strict[~d_strict["day"].str.startswith("2020")]
    print(f"  {'window':<11}" + "".join(f"{g:>17}" for g in REGIMES))
    print(f"  {'':<11}" + "".join(f"{'ann%':>9}{'n':>8}" for _ in REGIMES))
    for w in WINDOWS:
        line = f"  {w:<11}"
        for g in REGIMES:
            s = ss[ss["regime"] == g]
            a, _bp, _t = ann(s[w].to_numpy(dtype=float), s["day"])
            line += f"{100 * a:>8.2f}%{len(s):>8,}"
            rows.append({"excl_2020": True, "strict": True, "window": w, "regime": g,
                         "ann": a, "n": len(s)})
        print(line)
    for w in ("overnight", "rth"):
        vals = [ann(ss[ss["regime"] == g][w].to_numpy(dtype=float),
                    ss[ss["regime"] == g]["day"])[0] for g in REGIMES]
        mono = vals[0] > vals[1] > vals[2]
        label = "PLACEBO" if w == "rth" else "TEST   "
        print(f"  {label} {w:<10} monotone T+3>T+2>T+1: {mono}")

    pd.DataFrame(rows).to_json(OUT, orient="records", indent=1)
    print(f"\nwrote {OUT.relative_to(REPO)}  ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
