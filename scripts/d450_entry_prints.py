"""D450 -- the entry prints, compared directly. Is the proxy's 18:00 print stale?

    python scripts/d450_entry_prints.py

D449 found ES's hold return 1.74%/yr BELOW the proxy's at 0.9987 correlation, which is the
OPPOSITE sign to D448's +1.49%/yr on the 16:00->09:30 window. The two differ in one thing: where
the hold starts. D448 starts at SPY's 16:00 closing auction; D449 starts at SPY's 18:00
POST-MARKET print. D449 named the candidate explanation and did not measure it. This measures it.

THE DECOMPOSITION, and it is exact in logs. For either instrument, with c16 the 16:00 close on
the ENTRY day, e18 the 18:00 entry price, and x the exit on the next day:

    hold  =  x / e18            what the strategy earns
    step  =  e18 / c16          how far the entry print sits from that day's close
    full  =  x / c16            the same window measured from the closing auction

    log full  =  log hold + log step         ... identically

So   log(hold_ES) - log(hold_SPY)  =  [log full_ES - log full_SPY] - [log step_ES - log step_SPY]
and the question is which of those two terms carries D449's -1.74%/yr. If it is the STEP term,
the proxy's entry print is the artefact.

THE CROSS-FIXTURE CHECK. `full` is computed TWICE by independent routes -- once as hold x step
from D449's holds panel, and once directly from D448's boundary panel (p1600 on both days), which
was built in a separate pass over the raw DBN. They must agree to floating point. That is the
gate; if it fails, one of the two extractions is wrong and nothing below means anything.

PREDICTIONS, WRITTEN BEFORE THE RUN:
  W1  SPY's step is systematically NEGATIVE relative to ES's -- the post-market print sits below
      where the market actually is -- and the step term carries most of D449's -1.74%/yr.
  W2  the gap is concentrated in the holds where D259's FALLBACK fired, i.e. where no print
      exists at or after 18:00 and the entry is the last evening price instead.
  W3  the full-window term goes the OTHER way, +1 to +2%/yr, because it is D448's carry q-r
      measured over a slightly longer window.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import run_overnight_decomposition as ODR          # noqa: E402

ES_HOLDS = REPO / "data" / "fixtures" / "es_c1_holds.csv.gz"
ES_BOUND = REPO / "data" / "fixtures" / "es_front_1m_boundaries.csv.gz"
OUT = REPO / "data" / "d450_entry_prints.json"
YR = 252


def spy_entries() -> pd.DataFrame:
    """SPY's 16:00 close and its 18:00 entry, with the branch that produced the entry.

    Reproduces run_overnight_decomposition.path_points' entry rule exactly, and additionally
    reports WHICH branch fired -- a real print at or after 18:00, or D259's fallback to the
    last evening price, which is the staleness the ENTRY_STALE_FLOOR exists to bound."""
    df = ODR.load()
    df = df[df["suspect"] == 0]
    drop = ODR.half_days(df)
    sess = ODR.sessions_for(df, "SPY", drop)
    rows = []
    for day, s in sess.items():
        post = s["post"]
        evening = post[post["hhmm"] >= ODR.ENTRY_STALE_FLOOR]
        if evening.empty:
            continue
        at = evening[evening["hhmm"] >= ODR.GLOBEX_ENTRY]
        if len(at):
            e18, branch, t = float(at["open"].iloc[0]), "print", str(at["hhmm"].iloc[0])
        else:
            e18, branch = float(evening["close"].iloc[-1]), "fallback"
            t = str(evening["hhmm"].iloc[-1])
        rows.append({"day": day, "spy_c16": s["p1600"], "spy_e18": e18,
                     "branch": branch, "entry_hhmm": t})
    return pd.DataFrame(rows).set_index("day")


def main() -> int:
    es_h = pd.read_csv(ES_HOLDS)                      # day = EXIT day, entry = 18:00 on day a
    es_b = pd.read_csv(ES_BOUND, index_col="day")     # D448's independent boundary panel
    spy = spy_entries()

    # rebuild the (a, b) pairing the proxy uses, then keep only pairs present on both sides
    df = ODR.load()
    df = df[df["suspect"] == 0]
    sess = ODR.sessions_for(df, "SPY", ODR.half_days(df))
    pr = ODR.decompose(sess, "SPY")
    pr = pr[pr["consecutive"]].set_index("day")

    es_h = es_h.set_index("day")
    rows = []
    for b in es_h.index:
        if b not in pr.index:
            continue
        a = pr.at[b, "prev_day"]
        if a not in spy.index or b not in spy.index or a not in es_b.index or b not in es_b.index:
            continue
        # the proxy's hold, exactly as D440 scores it
        spy_e18, spy_c16a = spy.at[a, "spy_e18"], spy.at[a, "spy_c16"]
        spy_x = spy.at[b, "spy_c16"]
        rows.append({
            "day": b, "prev_day": a, "branch": spy.at[a, "branch"],
            "entry_hhmm": spy.at[a, "entry_hhmm"],
            "spy_hold": spy_x / spy_e18 - 1.0,
            "spy_step": spy_e18 / spy_c16a - 1.0,
            "spy_full": spy_x / spy_c16a - 1.0,
            "es_hold": es_h.at[b, "d_end"],
            "es_step": es_h.at[b, "entry"] / es_b.at[a, "p1600"] - 1.0,
            "es_full_direct": es_b.at[b, "p1600"] / es_b.at[a, "p1600"] - 1.0,
        })
    d = pd.DataFrame(rows)
    d["es_full"] = (1 + d["es_hold"]) * (1 + d["es_step"]) - 1.0

    print("D450 -- the entry prints, compared directly\n")
    print(f"  {len(d):,} matched holds   {d['day'].min()} .. {d['day'].max()}\n")

    # ---- the cross-fixture gate -------------------------------------------------------
    err = np.abs(d["es_full"] - d["es_full_direct"])
    print(f"  [GATE] ES full window, two independent extractions: max abs diff {err.max():.2e}")
    if err.max() > 1e-9:
        bad = d.loc[err.idxmax()]
        print(f"    WORST {bad['day']}: hold x step = {bad['es_full']:.10f} against "
              f"D448's boundary panel {bad['es_full_direct']:.10f}")
        print("  GATE FAILED -- one of the two extractions is wrong. Stopping.")
        return 1
    print("  [GATE] PASS -- D449's holds and D448's boundaries agree to floating point\n")

    def bp(x):
        return 1e4 * float(np.mean(x))

    def yr(x):
        return 100 * YR * float(np.mean(x)) / 100

    print(f"  {'term':<12}{'SPY bp/day':>12}{'ES bp/day':>11}{'ES-SPY bp':>11}{'ES-SPY %/yr':>13}")
    for lab, s, e in (("hold", "spy_hold", "es_hold"), ("step", "spy_step", "es_step"),
                      ("full", "spy_full", "es_full")):
        diff = d[e] - d[s]
        print(f"  {lab:<12}{bp(d[s]):>12.2f}{bp(d[e]):>11.2f}{bp(diff):>11.2f}"
              f"{YR * float(np.mean(diff)) * 100:>12.2f}%")

    lh = np.log1p(d["es_hold"]) - np.log1p(d["spy_hold"])
    lf = np.log1p(d["es_full"]) - np.log1p(d["spy_full"])
    ls = np.log1p(d["es_step"]) - np.log1p(d["spy_step"])
    print(f"\n  [IDENTITY] log hold-diff {1e4 * lh.mean():+.3f} bp "
          f"= full {1e4 * lf.mean():+.3f} - step {1e4 * ls.mean():+.3f} "
          f"-> residual {1e4 * (lh - (lf - ls)).mean():+.2e} bp")

    print(f"\n  WHERE THE ENTRY CAME FROM")
    for br, g in d.groupby("branch"):
        print(f"    {br:<10}{len(g):>6,} holds ({100 * len(g) / len(d):>5.1f}%)"
              f"   SPY step {bp(g['spy_step']):>+7.2f} bp"
              f"   ES step {bp(g['es_step']):>+7.2f} bp"
              f"   diff {bp(g['es_step'] - g['spy_step']):>+7.2f} bp"
              f"   hold diff {bp(g['es_hold'] - g['spy_hold']):>+7.2f} bp")

    print(f"\n  ENTRY TIME OF THE PROXY'S PRINT (top 8)")
    vc = d["entry_hhmm"].value_counts().head(8)
    for t, n in vc.items():
        g = d[d["entry_hhmm"] == t]
        print(f"    {t}  {n:>5,}  SPY step {bp(g['spy_step']):>+7.2f} bp"
              f"   hold diff {bp(g['es_hold'] - g['spy_hold']):>+7.2f} bp")

    res = {"n": len(d),
           "hold_diff_bp": bp(d["es_hold"] - d["spy_hold"]),
           "step_diff_bp": bp(d["es_step"] - d["spy_step"]),
           "full_diff_bp": bp(d["es_full"] - d["spy_full"]),
           "hold_diff_pct_yr": YR * float((d["es_hold"] - d["spy_hold"]).mean()) * 100,
           "step_diff_pct_yr": YR * float((d["es_step"] - d["spy_step"]).mean()) * 100,
           "full_diff_pct_yr": YR * float((d["es_full"] - d["spy_full"]).mean()) * 100,
           "fallback_share": float((d["branch"] == "fallback").mean())}
    pd.Series(res).to_json(OUT, indent=1)
    d.to_json(REPO / "data" / "d450_entry_pairs.json", orient="records")
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
