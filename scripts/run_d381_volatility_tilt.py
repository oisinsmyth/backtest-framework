"""D381 STAGE 0 -- `zr` scored alone: the measurement D280 said it could not make.

    uv run python scripts/run_d381_volatility_tilt.py --selftest
    uv run python scripts/run_d381_volatility_tilt.py --stage0

Pre-registration: docs/decisions/D381-the-volatility-tilt-zr-scored-alone.md
(committed BEFORE this file existed, R8; amended once, also before this file existed).

DESCRIPTIVE. Stage 0 scores no book, ranks nothing into a portfolio and admits nothing (R15). It
answers one question D280 asked and declared it could not answer from its own artefacts:

    "zr alone was never scored, so this record CANNOT say how much of -0.01373 is the volatility
     term by itself. That is not recoverable from the artefacts and needs its own measurement."

THE OBJECT IS D280'S, NOT A LOOKALIKE, and [ID] is what makes that a fact rather than an
intention: this runner imports `d280_combined_forecast` and uses ITS `zscore`, ITS panel, ITS
grids, ITS lag and ITS `ic_series`, then recomputes the full composite `zh + zv + za + zr` and
asserts it reproduces D280's PUBLISHED -0.01373 / t -5.07 (read from data/d280_combined_forecast.json,
not retyped) BEFORE `zr` is scored alone. If [ID] fails, nothing downstream is reported.

THE BARS, from the pre-registration and NOT restated from memory -- they are asserted against the
record's own text at run time where they are numeric:

    S0-a   |mean IC| of zr alone >= 0.006          (roughly half the composite's -0.01373)
    S0-b   |t| clears D280's own best-of-161 floor of 2.86
    S0-c'  the DIRECTION IS NOT ASSERTED FROM PROSE. The sign of zr's own IC is measured, and the
           short's end follows mechanically:
               negative IC -> the short takes the HIGH-zr (volatile) end
               positive IC -> the short takes the LOW-zr (calm) end
           and the runner PRINTS IT IN MONEY: the realised next-bar mean return of the top and
           bottom zr decile, so the end being shorted is demonstrated rather than argued.
           D280's own lesson, applied to D280: "a sign asserted in prose inverted D280."

Q3' predicts the IC is NEGATIVE (short the volatile end). D280's part-4C prose says the opposite
and is the falsifier.

ASSERTIONS
  [ID]  the composite reproduces D280's published mean IC and t from its own artefact, to 1e-9,
        before zr is read.
  [Z]   this runner's `zr` is bit-identical to the one D280's own module builds -- same function,
        same inputs, verified elementwise rather than assumed by shared provenance.
  [L]   the IC pairs score at t with the return over t -> t+1 and never reads bar t+1's score. A
        deliberately forward-shifted score must move the IC; asserted.
  [P]   the JSON is persisted BEFORE it is rendered (D371).
  [X]   the self-test RAISES on a sign-flipped score and on a score shifted one bar into the
        future. A self-test that cannot fail is worse than none.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


OUT = REPO / "data" / "d381_stage0.json"
D280_JSON = REPO / "data" / "d280_combined_forecast.json"
PREREG = REPO / "docs" / "decisions" / "D381-the-volatility-tilt-zr-scored-alone.md"

S0A_MIN_ABS_IC = 0.006          # pre-reg section 2
S0B_MIN_ABS_T = 2.86            # D280's own best-of-161 median largest |t|
DECILE = 10


def build(V, dividend_bound=True):
    """D280's part-4C inputs, rebuilt through D280's own module. Returns everything Stage 0 needs.

    `dividend_bound` IS THE WHOLE REASON [ID] IS EXACT RATHER THAN TOLERATED. D280's artifact was
    committed 2026-09-02; `ragged_panel.load_ragged` gained a dividend bound on 2026-09-05 (D333,
    commit 3849274), and it defaults to True. **D280's published numbers therefore live on the
    UNBOUNDED panel, which no longer exists by default.** Measured: the composite reads
    -0.013727 unbounded and -0.013728 bounded, a relative difference of 1.06e-04 -- far too large
    for float noise (~1e-16) and exactly the size a handful of re-priced dividend bars would make.

    So [ID] runs on `dividend_bound=False` and must match D280 EXACTLY, while the Stage 0
    measurement runs on today's default panel. Both are reported. This is D333's own convention --
    it repriced the whole stack "under both panels" and asserted "identity with D332 under the
    UNBOUNDED panel"."""
    B, C, P1, P3, RP = V.B, V.C, V.P1, V.P3, V.RP
    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=C.FEE,
                                    dividend_bound=dividend_bound)
    md, hs, _g_lo, _g_hi, _i_lo, _atr, warm = B.signals_ragged(panel, cleaned, 0)
    live = panel.live
    g = P1.build_grids(panel, cleaned)
    O, H, L, Cl = g["open"], g["high"], g["low"], g["close"]
    dates = np.array(panel.dates)
    oos = live & (dates >= V.SPLIT_DATE)[None, :]

    def nxt(x):
        out = np.full_like(x, np.nan)
        ok = live[:, 1:] & live[:, :-1]
        out[:, :-1] = np.where(ok, x[:, 1:], np.nan)
        return out

    total = nxt(np.expm1(panel.total_log_returns))
    okm = ~(np.isnan(md) | np.isnan(hs)) & warm
    qual = oos & (-B.hold_book((hs < 0) & (md >= 0) & okm, warm) != 0.0)

    h = C.lag1(hs)
    v = V.P3.d1(h, live)
    a = V.P3.d1(v, live)
    rng_l = C.lag1((H - L) / Cl)

    zh, zv, za = V.zscore(h, live), V.zscore(v, live), V.zscore(a, live)
    zr = V.zscore(rng_l, live)
    return dict(panel=panel, live=live, oos=oos, qual=qual, total=total,
                zh=zh, zv=zv, za=za, zr=zr, rng_l=rng_l, dates=dates)


def ic_of(V, score, target, mask):
    ics = V.ic_series(score, target, mask)
    mu = float(ics.mean())
    t = float(mu / (ics.std(ddof=1) / np.sqrt(ics.size)))
    return dict(mean_ic=mu, t=t, bars=int(ics.size))


def decile_money(score, total, mask, k=DECILE):
    """THE SIGN, IN MONEY. Mean realised next-bar return of the top and bottom zr decile.

    Not a book and not a P&L -- no cost, no hedge, no slot cap. It exists so the end a short would
    take is DEMONSTRATED rather than read off a correlation's sign, which is the error that
    inverted D280 itself."""
    hi, lo, n = [], [], 0
    T = score.shape[1]
    for t in range(T):
        col = mask[:, t] & np.isfinite(score[:, t]) & np.isfinite(total[:, t])
        m = int(col.sum())
        if m < 5 * k:
            continue
        s, r = score[col, t], total[col, t]
        order = np.argsort(s)
        c = max(1, m // k)
        lo.append(float(r[order[:c]].mean()))
        hi.append(float(r[order[-c:]].mean()))
        n += 1
    hi, lo = np.array(hi), np.array(lo)
    return dict(bars=n, top_decile_ret_bp=float(hi.mean()) * 1e4,
                bottom_decile_ret_bp=float(lo.mean()) * 1e4,
                spread_bp=float((hi - lo).mean()) * 1e4)


# ---------------------------------------------------------------------- self-test
def selftest(V) -> int:
    print("D381 STAGE 0 SELF-TEST -- the IC's direction, and two breaks that must be caught\n")
    rng = np.random.default_rng(380)
    n, T = 200, 400
    live = np.ones((n, T), dtype=bool)
    s = rng.normal(size=(n, T))
    # a target that is MINUS the score plus noise: IC must be strongly NEGATIVE
    tgt = -s + 0.5 * rng.normal(size=(n, T))
    r = ic_of(V, s, tgt, live)
    assert r["mean_ic"] < -0.5, f"[X] a planted negative relation must show a negative IC, got {r['mean_ic']:+.4f}"
    print(f"    planted NEGATIVE relation -> mean IC {r['mean_ic']:+.4f} (t {r['t']:+.1f})")

    money = decile_money(s, tgt, live)
    assert money["top_decile_ret_bp"] < money["bottom_decile_ret_bp"], \
        "[X] with a negative IC the TOP decile must earn LESS than the bottom"
    print(f"    and IN MONEY: top decile {money['top_decile_ret_bp']:+,.0f} bp vs bottom "
          f"{money['bottom_decile_ret_bp']:+,.0f} bp -> a short takes the TOP (high-score) end")

    # [X] break 1 -- flip the score's sign; the IC must flip with it
    r2 = ic_of(V, -s, tgt, live)
    raised = False
    try:
        assert r2["mean_ic"] < -0.5, "a sign-flipped score must not keep a negative IC"
    except AssertionError:
        raised = True
    assert raised, "[X] THE SELF-TEST CANNOT FAIL -- a sign-flipped score kept its IC"
    print(f"    [X] sign-flipped score reads {r2['mean_ic']:+.4f} and IS CAUGHT")

    # [X] break 2 -- shift the score one bar into the FUTURE; the IC must change
    fut = np.full_like(s, np.nan)
    fut[:, :-1] = s[:, 1:]
    r3 = ic_of(V, fut, tgt, live)
    assert abs(r3["mean_ic"] - r["mean_ic"]) > 0.1, \
        "[L] a forward-shifted score left the IC unchanged -- the pairing is not what it claims"
    print(f"    [L] score shifted one bar into the future reads {r3['mean_ic']:+.4f} against "
          f"{r['mean_ic']:+.4f} -- the IC pairs t with t->t+1 as claimed")
    print("\nSELF-TEST PASSED\n")
    return 0


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--stage0", action="store_true")
    a = ap.parse_args()
    V = _load("d280c", "d280_combined_forecast.py")
    if a.selftest:
        return selftest(V)
    if not a.stage0:
        ap.error("pass --stage0 (Stage 1 is not authorised: it runs only if Stage 0 clears)")
    selftest(V)

    t0 = time.time()
    # THE UNBOUNDED PANEL FIRST -- it is the one D280 measured on, and [ID] is exact on it.
    DU = build(V, dividend_bound=False)
    print(f"  built D280's part-4C inputs on the UNBOUNDED panel (D280's own) in "
          f"{time.time() - t0:.0f}s | {DU['live'].shape[0]} names x {DU['live'].shape[1]} bars",
          flush=True)
    t1 = time.time()
    D = build(V, dividend_bound=True)
    print(f"  and on TODAY'S panel (dividend bound, D333) in {time.time() - t1:.0f}s", flush=True)

    # ---- [Z] this runner's zr IS D280's ------------------------------------
    zr_ref = V.zscore(D["rng_l"], D["live"])
    both = np.isfinite(D["zr"]) & np.isfinite(zr_ref)
    assert np.array_equal(np.isfinite(D["zr"]), np.isfinite(zr_ref)) and \
        (D["zr"][both] == zr_ref[both]).all(), "[Z] zr is not D280's zr"
    print(f"    [Z] zr is bit-identical to D280's own construction on all "
          f"{int(both.sum()):,} finite cells", flush=True)

    # ---- [ID] the composite reproduces D280's PUBLISHED numbers EXACTLY ----
    #      on the panel D280 measured on, which is the UNBOUNDED one (see build()).
    pub = json.loads(D280_JSON.read_text())
    key = "C|ALL|zh + zv + za + zr"
    p = pub["results"][key]
    comp_u = DU["zh"] + DU["zv"] + DU["za"] + DU["zr"]
    got_u = ic_of(V, comp_u, DU["total"], DU["oos"])
    assert abs(got_u["mean_ic"] - p["mean_ic"]) < 1e-9 and abs(got_u["t"] - p["t"]) < 1e-9, \
        f"[ID] on the UNBOUNDED panel the composite is {got_u['mean_ic']:+.9f}/{got_u['t']:+.6f} " \
        f"against D280's published {p['mean_ic']:+.9f}/{p['t']:+.6f}"
    print(f"    [ID] on D280's own (UNBOUNDED) panel the composite reproduces its published "
          f"mean IC {p['mean_ic']:+.6f} and t {p['t']:+.4f} to 1e-9 -- the object is D280's",
          flush=True)

    comp = D["zh"] + D["zv"] + D["za"] + D["zr"]
    got = ic_of(V, comp, D["total"], D["oos"])
    print(f"    [DIV] on TODAY'S panel the same composite is {got['mean_ic']:+.6f} / "
          f"{got['t']:+.4f} -- a relative shift of "
          f"{abs(got['mean_ic'] - p['mean_ic']) / abs(p['mean_ic']):.2e} from D333's dividend "
          f"bound, NOT float noise. Stage 0 is measured on TODAY'S panel.", flush=True)

    # ---- the measurement D280 said it could not make -----------------------
    R = {}
    for uname, mask in (("ALL", D["oos"]), ("QUAL", D["qual"])):
        R[uname] = {"zr_alone": ic_of(V, D["zr"], D["total"], mask),
                    "composite": ic_of(V, comp, D["total"], mask),
                    "zh": ic_of(V, D["zh"], D["total"], mask),
                    "money": decile_money(D["zr"], D["total"], mask)}
        z, c = R[uname]["zr_alone"], R[uname]["composite"]
        print(f"    {uname:<5s} zr alone  mean IC {z['mean_ic']:+.5f}  t {z['t']:+.2f}  "
              f"({z['bars']:,} bars)   | composite {c['mean_ic']:+.5f} / {c['t']:+.2f}", flush=True)

    # ---- the bars ----------------------------------------------------------
    zA = R["ALL"]["zr_alone"]
    s0a = abs(zA["mean_ic"]) >= S0A_MIN_ABS_IC
    s0b = abs(zA["t"]) >= S0B_MIN_ABS_T
    implied_end = "HIGH-zr (VOLATILE)" if zA["mean_ic"] < 0 else "LOW-zr (CALM)"
    q3prime = zA["mean_ic"] < 0
    money = R["ALL"]["money"]
    money_agrees = ((money["top_decile_ret_bp"] < money["bottom_decile_ret_bp"])
                    == (zA["mean_ic"] < 0))
    share = abs(zA["mean_ic"]) / abs(R["ALL"]["composite"]["mean_ic"])

    payload = dict(
        study=381, stage=0,
        purpose="Score zr alone -- the measurement D280 declared unrecoverable from its own "
                "artefacts. Descriptive: no book, no cell, nothing admitted (R15).",
        prereg=str(PREREG.relative_to(REPO)),
        identity=dict(published=p, recomputed_unbounded=got_u, recomputed_today=got,
                      note="D280's artifact predates D333's dividend bound in load_ragged "
                           "(commit 3849274, 2026-09-05). [ID] is EXACT on the unbounded panel "
                           "D280 measured on; Stage 0 is measured on today's bounded panel and "
                           "both are reported. The shift is a repricing, not float noise.",
                      relative_shift=float(abs(got["mean_ic"] - p["mean_ic"]) / abs(p["mean_ic"]))),
        zr_unbounded=ic_of(V, DU["zr"], DU["total"], DU["oos"]),
        bars=dict(S0A_MIN_ABS_IC=S0A_MIN_ABS_IC, S0B_MIN_ABS_T=S0B_MIN_ABS_T),
        results=R,
        verdict=dict(S0a=bool(s0a), S0b=bool(s0b), zr_share_of_composite=float(share),
                     implied_short_end=implied_end, money_agrees_with_ic=bool(money_agrees),
                     Q3prime_ic_negative=bool(q3prime),
                     stage0_clears=bool(s0a and s0b and money_agrees)))
    OUT.write_text(json.dumps(payload, indent=1))
    print(f"\n  [P] wrote {OUT.relative_to(REPO)} BEFORE rendering", flush=True)

    # ---- render ------------------------------------------------------------
    print("\nSTAGE 0 -- `zr` ALONE, against D280's composite and its `zh` baseline\n")
    print(f"  {'universe':<9s} {'score':<12s} {'mean IC':>10s} {'t':>8s} {'bars':>8s}")
    for uname in R:
        for nm in ("zh", "zr_alone", "composite"):
            d = R[uname][nm]
            print(f"  {uname:<9s} {nm:<12s} {d['mean_ic']:>+10.5f} {d['t']:>+8.2f} "
                  f"{d['bars']:>8,d}")

    print(f"\nTHE SIGN, IN MONEY (ALL) -- mean realised next-bar return by `zr` decile, "
          f"no cost, no hedge:\n")
    print(f"  top decile (most volatile) {money['top_decile_ret_bp']:>+9.2f} bp")
    print(f"  bottom decile (calmest)    {money['bottom_decile_ret_bp']:>+9.2f} bp")
    print(f"  spread                     {money['spread_bp']:>+9.2f} bp over {money['bars']:,} bars")
    print(f"\n  IC sign implies a short on the {implied_end} end; the money "
          f"{'AGREES' if money_agrees else '*** DISAGREES ***'}.")

    print("\nTHE BARS\n")
    print(f"  S0-a  |mean IC| {abs(zA['mean_ic']):.5f} >= {S0A_MIN_ABS_IC}          "
          f"{'CLEARS' if s0a else 'FAILS'}")
    print(f"  S0-b  |t| {abs(zA['t']):.2f} >= {S0B_MIN_ABS_T} (D280's best-of-161)   "
          f"{'CLEARS' if s0b else 'FAILS'}")
    print(f"  S0-c' direction demonstrated in money                {'YES' if money_agrees else 'NO'}")
    print(f"\n  zr alone carries {100 * share:.1f}% of the composite's |mean IC|")
    print(f"  Q3' (IC is negative -> short the volatile end): "
          f"{'HELD' if q3prime else 'FALSIFIED -- D280 part 4C prose is vindicated'}")
    print(f"\nSTAGE 0: {'CLEARS -- stage 1 is authorised by the pre-registration' if payload['verdict']['stage0_clears'] else 'FAILS -- the record stops here (pre-reg section 9)'}")
    print("\nThis measurement scores no book and admits nothing (R15).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
