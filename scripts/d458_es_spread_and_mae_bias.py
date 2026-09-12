"""D458 -- what the tick data settles: the ES spread, and whether a bar-based MAE is safe.

    uv run python scripts/d458_es_spread_and_mae_bias.py --extract   # TBBO -> cached ES ticks
    uv run python scripts/d458_es_spread_and_mae_bias.py --self-test # the MAE bounds, on a known path
    uv run python scripts/d458_es_spread_and_mae_bias.py --spread    # measurement 1
    uv run python scripts/d458_es_spread_and_mae_bias.py --mae       # measurement 2

**TWO COST/INSTRUMENT MEASUREMENTS, NOT A STUDY.** Neither computes a return, an edge or a
Sharpe. Nothing is admitted, closed or elevated. What they produce is a spread distribution
and a measurement-bias bracket -- both properties of the instrument and the sampling grid,
which is why they need no pre-registration under R8.

MEASUREMENT 1 -- THE SPREAD, WHICH FOUR STUDIES HAVE ASSUMED
------------------------------------------------------------
Every futures conclusion in this programme rests on ~0.2 bp round-turn commission, and
`data-purchase-proposal.md` 6 flagged the hole: one ES tick is 0.25 index points = $12.50,
and against ~$300k of notional that is ~0.4 bp PER SIDE CROSSED, so the true round trip may
be nearer 1.0 bp than 0.2. Nobody measured it. `tbbo` carries `bid_px_00` and `ask_px_00`
immediately before every trade, so the spread is now directly observable -- including
overnight, where C1 actually lives.

MEASUREMENT 2 -- IS A BAR-BASED MAE SAFE, AND IN WHICH DIRECTION
-----------------------------------------------------------------
Hurdle P1 is a 4% trailing drawdown on OPEN equity, and C1's MAE p99 came in at **3.98%**,
sitting exactly on the floor. That was measured on coarse bars.

**A CLAIM I MADE AND HAVE TO WALK BACK.** I said coarse bars "systematically understate" a
trailing drawdown. That is not established -- it depends entirely on the convention, and
there are two, which BRACKET the truth:

    PESSIMISTIC  running max includes bar t's HIGH, drawdown to bar t's LOW.
                 Assumes high-then-low inside every bar. OVERSTATES.
    OPTIMISTIC   running max only through bar t-1, drawdown to bar t's LOW.
                 Assumes low-then-high inside every bar. UNDERSTATES.

The exact tick path sits between them, and **where it sits is the whole question**: if the
truth is near the pessimistic bound, 3.98% has headroom; if near the optimistic bound, the
published figure may be the optimistic one and the true p99 could be over 4%. So this
computes all three on the same holds and reports the bracket, rather than asserting a
direction.

WHAT IS DELIBERATELY NOT DONE HERE
----------------------------------
No return, no P&L, no verdict on C1. The bracket is reported; what it implies for the
candidate is the principal's call (R15).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "databento"
CACHE = REPO / "temp" / "d458_es_ticks.npz"
OUT = REPO / "data" / "d458_es_spread_and_mae_bias.json"
KEY_FILE = Path.home() / ".config" / "databento" / "key"

# ES front-month instrument_ids over the tbbo window, from symbology.resolve (free call,
# 2026-09-12). Recorded rather than re-fetched so --extract is reproducible offline.
ES_IDS = {
    14160:    ("2025-09-11", "2025-09-17"),
    294973:   ("2025-09-17", "2025-12-17"),
    42140878: ("2025-12-17", "2026-03-18"),
    42140864: ("2026-03-18", "2026-06-17"),
    42140870: ("2026-06-17", "2026-09-11"),
}
PX_SCALE = 1e-9          # DBN fixed-point
TICK = 0.25              # ES minimum price increment, index points (CME spec)
TICK_USD = 12.50         # per contract
USD_PER_POINT = 50.0
ET = "America/New_York"

# C1's window, from D259: enter at the 18:00 ET Globex open, exit 16:10 ET the next day.
ENTRY_MIN = 18 * 60
EXIT_MIN = 16 * 60 + 10


def P(*a, **k):
    print(*a, **k, flush=True)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --------------------------------------------------------------- extract

def do_extract() -> int:
    """Stream tbbo, keep only ES front month, cache a compact array.

    to_ndarray(count=...) yields chunked STRUCTURED numpy, so the filter is vectorised.
    A Python loop over ~1.4 billion tbbo records would be hopeless -- the profile in
    data/decode_pipeline_bench.json puts numpy at 8,755 MB/s against zstd's 754, so the
    only sane path keeps every per-record operation inside numpy.
    """
    import databento as db
    files = sorted(RAW.glob("*/*.tbbo.dbn.zst"))
    if not files:
        raise SystemExit("no tbbo files under data/raw/databento/")
    ids = np.array(sorted(ES_IDS), dtype=np.uint32)
    P(f"extracting ES front month from {len(files)} tbbo files, ids {list(ids)}\n")

    ts, px, sz, side, bid, ask, bsz, asz = [], [], [], [], [], [], [], []
    for i, f in enumerate(files, 1):
        store = db.DBNStore.from_file(f)
        kept = seen = 0
        for chunk in store.to_ndarray(count=2_000_000):
            seen += len(chunk)
            m = np.isin(chunk["instrument_id"], ids)
            if not m.any():
                continue
            c = chunk[m]
            kept += len(c)
            ts.append(c["ts_recv"].copy())
            px.append(c["price"].copy())
            sz.append(c["size"].copy())
            side.append(c["side"].copy())
            bid.append(c["bid_px_00"].copy())
            ask.append(c["ask_px_00"].copy())
            bsz.append(c["bid_sz_00"].copy())
            asz.append(c["ask_sz_00"].copy())
        P(f"  [{i}/{len(files)}] {f.name[:46]:46} {seen:>12,} recs -> {kept:>9,} ES")

    arr = {k: np.concatenate(v) for k, v in
           (("ts", ts), ("px", px), ("sz", sz), ("side", side),
            ("bid", bid), ("ask", ask), ("bsz", bsz), ("asz", asz))}
    order = np.argsort(arr["ts"], kind="stable")
    arr = {k: v[order] for k, v in arr.items()}
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CACHE, **arr)
    P(f"\n  {len(arr['ts']):,} ES trades cached -> {CACHE.relative_to(REPO)} "
      f"({CACHE.stat().st_size/1e6:.0f} MB)")
    return 0


def load_ticks() -> dict:
    if not CACHE.exists():
        raise SystemExit("run --extract first")
    z = np.load(CACHE)
    return {k: z[k] for k in z.files}


def et_minutes(ts_ns: np.ndarray):
    """UTC nanos -> (session date as int yyyymmdd, minute-of-day in ET)."""
    import pandas as pd
    t = pd.DatetimeIndex(pd.to_datetime(ts_ns, utc=True)).tz_convert(ET).tz_localize(None)
    mod = (t.hour * 60 + t.minute).to_numpy()
    # a bar at or after 18:00 ET belongs to the NEXT session date
    day = t.normalize() + pd.to_timedelta((mod >= ENTRY_MIN).astype(int), unit="D")
    return day.strftime("%Y%m%d").astype(np.int64).to_numpy(), mod, t


# ---------------------------------------------------------------- spread

def do_spread() -> int:
    d = load_ticks()
    bid = d["bid"].astype(np.float64) * PX_SCALE
    ask = d["ask"].astype(np.float64) * PX_SCALE
    mid = 0.5 * (bid + ask)
    ok = (bid > 0) & (ask > 0) & (ask >= bid)
    P(f"ES trades cached {len(bid):,}; usable quote on {ok.sum():,} ({ok.mean():.1%})")
    sp_pts = (ask - bid)[ok]
    mid_ok = mid[ok]
    sp_ticks = sp_pts / TICK
    sp_usd = sp_pts * USD_PER_POINT
    sp_bp_side = 0.5 * sp_pts / mid_ok * 1e4      # half-spread, per side crossed
    _, mod, _ = et_minutes(d["ts"][ok])

    def q(a, p):
        return float(np.quantile(a, p))

    res = {
        "n_trades": int(ok.sum()),
        "spread_ticks": {"mean": float(sp_ticks.mean()), "p50": q(sp_ticks, .5),
                         "p90": q(sp_ticks, .9), "p99": q(sp_ticks, .99),
                         "share_at_one_tick": float((sp_ticks <= 1.0001).mean())},
        "spread_usd_per_contract": {"mean": float(sp_usd.mean()), "p50": q(sp_usd, .5),
                                    "p99": q(sp_usd, .99)},
        "half_spread_bp_per_side": {"mean": float(sp_bp_side.mean()),
                                    "p50": q(sp_bp_side, .5), "p99": q(sp_bp_side, .99)},
    }
    P(f"\n  spread in TICKS      mean {res['spread_ticks']['mean']:.3f}  "
      f"p50 {res['spread_ticks']['p50']:.2f}  p90 {res['spread_ticks']['p90']:.2f}  "
      f"p99 {res['spread_ticks']['p99']:.2f}")
    P(f"  at exactly one tick  {res['spread_ticks']['share_at_one_tick']:.1%} of trades")
    P(f"  spread in $/contract mean {res['spread_usd_per_contract']['mean']:.2f}  "
      f"p99 {res['spread_usd_per_contract']['p99']:.2f}")
    P(f"  HALF-spread in bp    mean {res['half_spread_bp_per_side']['mean']:.3f} per side "
      f"crossed  (round trip {2*res['half_spread_bp_per_side']['mean']:.3f} bp)")

    # by hour, because C1 trades the overnight and the assumption was never session-split
    P(f"\n  {'ET hour':>8}{'trades':>12}{'spr ticks p50':>15}{'half-spr bp mean':>18}")
    by_hour = {}
    for h in range(24):
        m = (mod // 60) == h
        if m.sum() < 100:
            continue
        by_hour[h] = {"n": int(m.sum()), "spread_ticks_p50": q(sp_ticks[m], .5),
                      "half_spread_bp_mean": float(sp_bp_side[m].mean())}
        P(f"  {h:>8}{m.sum():>12,}{by_hour[h]['spread_ticks_p50']:>15.2f}"
          f"{by_hour[h]['half_spread_bp_mean']:>18.3f}")
    res["by_et_hour"] = by_hour

    rth = ((mod >= 570) & (mod < 960))
    res["rth_vs_overnight"] = {
        "rth_half_spread_bp": float(sp_bp_side[rth].mean()),
        "overnight_half_spread_bp": float(sp_bp_side[~rth].mean()),
        "rth_trades": int(rth.sum()), "overnight_trades": int((~rth).sum()),
    }
    r = res["rth_vs_overnight"]
    P(f"\n  RTH half-spread {r['rth_half_spread_bp']:.3f} bp on {r['rth_trades']:,} trades")
    P(f"  OVERNIGHT       {r['overnight_half_spread_bp']:.3f} bp on {r['overnight_trades']:,}"
      f"   ratio {r['overnight_half_spread_bp']/r['rth_half_spread_bp']:.2f}x")
    P(f"\n  the programme's standing assumption is ~0.2 bp ROUND TURN commission;")
    P(f"  crossing alone measures {2*res['half_spread_bp_per_side']['mean']:.3f} bp round trip.")
    save({"spread": res})
    return 0


# ------------------------------------------------------------- MAE bias

def mae_three_ways(tick_px: np.ndarray, bar_hi: np.ndarray, bar_lo: np.ndarray) -> tuple:
    """MAE of one long hold, three ways. Returns (exact, pessimistic, optimistic) as
    fractions of the entry price.

    MAE here is the maximum drawdown from the RUNNING PEAK during the hold, which is what
    a trailing floor on open equity actually measures (R11's P1).
    """
    entry = tick_px[0]
    run = np.maximum.accumulate(tick_px)
    exact = float(np.max((run - tick_px) / entry))

    # PESSIMISTIC: peak includes this bar's own high, trough is this bar's low.
    run_incl = np.maximum.accumulate(bar_hi)
    pess = float(np.max((run_incl - bar_lo) / entry))

    # OPTIMISTIC: the low came FIRST inside each bar, so the peak available when the low
    # printed excludes this bar's own high. For the first bar the only peak that exists is
    # the entry itself.
    #
    # A BUG THE SELF-TEST CAUGHT BY BEING WEAK. This previously clamped run_prev up to
    # bar_hi[0], which forced the first bar's high into every peak and made `optimistic`
    # collapse onto `pessimistic` whenever the peak sat in bar 0 -- so all three
    # conventions returned the same number and the bracket looked tight when it was not.
    # A test where every arm agrees is not a passing test, it is an absent one.
    run_prev = np.empty_like(bar_hi)
    run_prev[0] = entry
    if len(bar_hi) > 1:
        run_prev[1:] = np.maximum.accumulate(bar_hi)[:-1]
    opt = float(np.max((run_prev - bar_lo) / entry))
    return exact, pess, opt


def do_self_test() -> int:
    """The three MAE conventions must BRACKET on a path where the answer is known by hand."""
    fails = []

    def chk(label, cond, detail=""):
        P(f"    [{'PASS' if cond else 'FAIL'}] {label:54} {detail}")
        if not cond:
            fails.append(label)

    # CASE A -- HIGH THEN LOW inside one bar. entry 100, path 100 -> 110 -> 95.
    # exact: peak 110, trough 95 -> 15%. pessimistic agrees. optimistic assumes the low
    # came first, so its peak is only the entry -> 5%. OPTIMISTIC MUST UNDERSTATE HERE.
    e, p, o = mae_three_ways(np.array([100., 110., 95.]),
                             np.array([110.]), np.array([95.]))
    chk("A exact = 15%", abs(e - .15) < 1e-9, f"{e:.4f}")
    chk("A pessimistic = exact when the high really came first", abs(p - .15) < 1e-9, f"{p:.4f}")
    chk("A OPTIMISTIC UNDERSTATES: 5% vs 15%", o < e - 1e-9, f"opt {o:.4f} < exact {e:.4f}")

    # CASE B -- LOW THEN HIGH inside one bar. path 100 -> 90 -> 110, same bar H/L.
    # exact: 10%. optimistic agrees (its assumption is true here). pessimistic assumes
    # high-then-low -> 20%. PESSIMISTIC MUST OVERSTATE HERE.
    e2, p2, o2 = mae_three_ways(np.array([100., 90., 110.]),
                                np.array([110.]), np.array([90.]))
    chk("B exact = 10%", abs(e2 - .10) < 1e-9, f"{e2:.4f}")
    chk("B optimistic = exact when the low really came first", abs(o2 - .10) < 1e-9, f"{o2:.4f}")
    chk("B PESSIMISTIC OVERSTATES: 20% vs 10%", p2 > e2 + 1e-9, f"pess {p2:.4f} > exact {e2:.4f}")

    # CASE C -- two bars, and the bracket must be STRICT on both sides at once.
    e3, p3, o3 = mae_three_ways(np.array([100., 108., 96., 104., 99.]),
                                np.array([108., 104.]), np.array([96., 99.]))
    chk("C bracket holds", o3 <= e3 + 1e-9 and e3 <= p3 + 1e-9,
        f"opt {o3:.4f} <= exact {e3:.4f} <= pess {p3:.4f}")
    chk("C bracket is STRICT, not a tie", p3 > o3 + 1e-9,
        f"width {(p3-o3)*100:.1f} pp -- a bracket where every arm agrees is not a test")

    if fails:
        P(f"\n  SELF-TEST FAILED: {fails}")
        return 1
    P("\n  SELF-TEST PASSED: the bar conventions bracket the tick path.")
    return 0


def do_mae() -> int:
    import pandas as pd
    d = load_ticks()
    px = d["px"].astype(np.float64) * PX_SCALE
    good = px > 0
    px, ts = px[good], d["ts"][good]
    sess, mod, t = et_minutes(ts)

    # C1's hold: 18:00 ET -> 16:10 ET. Group by session date; a session runs 18:00..16:10.
    in_hold = (mod >= ENTRY_MIN) | (mod <= EXIT_MIN)
    px, ts, sess, mod, t = px[in_hold], ts[in_hold], sess[in_hold], mod[in_hold], t[in_hold]
    P(f"ES ticks in a C1-shaped 18:00->16:10 window: {len(px):,} over "
      f"{len(np.unique(sess)):,} sessions")

    # one-minute bars from the SAME ticks, so the only difference is the grid
    minute = (ts // 60_000_000_000).astype(np.int64)
    rows = []
    uniq = np.unique(sess)
    for s in uniq:
        m = sess == s
        if m.sum() < 200:
            continue
        p_, mi_ = px[m], minute[m]
        # bar high/low per minute, vectorised
        _, first = np.unique(mi_, return_index=True)
        bounds = np.append(first, len(p_))
        hi = np.maximum.reduceat(p_, first)
        lo = np.minimum.reduceat(p_, first)
        if len(hi) < 10:
            continue
        e, pe, o = mae_three_ways(p_, hi, lo)
        rows.append((int(s), len(p_), len(hi), e, pe, o))

    if not rows:
        raise SystemExit("no usable sessions")
    a = np.array([(r[3], r[4], r[5]) for r in rows])
    exact, pess, opt = a[:, 0], a[:, 1], a[:, 2]

    def q(x, p):
        return float(np.quantile(x, p))

    res = {"sessions": len(rows),
           "note": "MAE as a fraction of the entry price, max drawdown from the running "
                   "peak during an 18:00->16:10 ET hold on ES front month, at 1x size",
           "exact_tick": {"p50": q(exact, .5), "p95": q(exact, .95), "p99": q(exact, .99),
                          "max": float(exact.max()), "mean": float(exact.mean())},
           "bar_pessimistic": {"p50": q(pess, .5), "p95": q(pess, .95), "p99": q(pess, .99),
                               "max": float(pess.max())},
           "bar_optimistic": {"p50": q(opt, .5), "p95": q(opt, .95), "p99": q(opt, .99),
                              "max": float(opt.max())},
           "bracket_holds_every_session": bool(np.all(opt <= exact + 1e-12)
                                               and np.all(exact <= pess + 1e-12))}
    P(f"\n  {'convention':22}{'p50':>9}{'p95':>9}{'p99':>9}{'max':>9}")
    for k, lab in (("bar_optimistic", "bar, optimistic"), ("exact_tick", "EXACT (ticks)"),
                   ("bar_pessimistic", "bar, pessimistic")):
        r = res[k]
        P(f"  {lab:22}{r['p50']*100:>8.3f}%{r['p95']*100:>8.3f}%{r['p99']*100:>8.3f}%"
          f"{r['max']*100:>8.3f}%")
    P(f"\n  bracket holds on every session: {res['bracket_holds_every_session']}")
    ex99, op99, pe99 = res["exact_tick"]["p99"], res["bar_optimistic"]["p99"], res["bar_pessimistic"]["p99"]
    if pe99 > op99:
        pos = (ex99 - op99) / (pe99 - op99)
        res["exact_position_in_bracket_at_p99"] = pos
        P(f"  at p99 the exact path sits {pos:.0%} of the way from the optimistic bound "
          f"to the pessimistic one")
    res["one_minute_bar_error_at_p99"] = {
        "optimistic_understates_by_pct_points": (ex99 - op99) * 100,
        "pessimistic_overstates_by_pct_points": (pe99 - ex99) * 100,
    }
    P(f"\n  a 1-minute grid on the SAME ticks is wrong by "
      f"{(ex99-op99)*100:+.4f} pp (optimistic) / "
      f"{(pe99-ex99)*100:+.4f} pp (pessimistic) at p99")
    P(f"\n  FOR CONTEXT ONLY, not a verdict: D259 published 3.980% on 15-minute equity-proxy")
    P(f"  bars against a 4% floor. This is ES futures, 1x size, {len(rows)} sessions of one")
    P(f"  year -- a different instrument and a far shorter sample. What it settles is the")
    P(f"  SIZE OF THE GRID ERROR, not C1's fate.")
    save({"mae_bias": res})
    return 0


def save(payload: dict) -> None:
    cur = {}
    if OUT.exists():
        cur = json.loads(OUT.read_text(encoding="utf-8"))
    cur.update(payload)
    cur["updated_utc"] = now()
    cur["purpose"] = ("D458: two instrument/cost measurements on the tick data -- the ES "
                      "spread, and how wrong a bar-grid MAE is. No return, no edge, no "
                      "verdict on any candidate.")
    cur["source"] = "data/raw/databento tbbo, ES front month, 2025-09-11..2026-09-11"
    OUT.write_text(json.dumps(cur, indent=1, default=str) + "\n", encoding="utf-8")
    P(f"\nwrote {OUT.relative_to(REPO)}")


def main() -> int:
    ap = argparse.ArgumentParser()
    for f in ("extract", "self-test", "spread", "mae"):
        ap.add_argument(f"--{f}", action="store_true")
    a = ap.parse_args()
    if a.extract:
        return do_extract()
    if a.self_test:
        return do_self_test()
    if a.spread:
        return do_spread()
    if a.mae:
        return do_mae()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
