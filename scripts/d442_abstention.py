"""D442 -- O1, the volatility-regime ABSTENTION rule on C1, on both lenses.

    uv run python scripts/d442_abstention.py --selftest
    uv run python scripts/d442_abstention.py --report

PRE-REGISTRATION: docs/decisions/D442-O1-the-volatility-regime-abstention-rule-on-C1.md

THE INHERITED CRITERION, declared in the prop candidate ledger before any of this was measured:
O1 "survives iff floor-touch probability falls RELATIVELY MORE than expected P&L; else it is an
exposure cut with a story." That is G1 and it is not this runner's invention.

WHY NOW. D440 measured that 82-86% of what a real path costs a funded account is SERIAL
STRUCTURE, not kurtosis. O1 is the only candidate on the ledger shaped like a remedy for that.

THE CONTROL IS THE STUDY. Abstention removes exposure, and less exposure mechanically means fewer
floor-touches. So the control shares the treatment's NUISANCE and not merely its count: ROT
circularly rotates the abstention mask against its own symbol's hold sequence, preserving the
count, the run lengths and the clustering EXACTLY while destroying alignment with returns. The
group is the n-1 offsets -- ~3,265 for SPY, finite and small -- so it is ENUMERATED and the p95
carries no sampling error at all.

A matched-count i.i.d. abstention is deliberately NOT a control here: it churns, and a churning
control for a persistent selector is the error D291 cost 87 cells to.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import d386_full_lifecycle as D386                      # noqa: E402
import d440_lifecycle as D440                           # noqa: E402

OUT_JSON = REPO / "data" / "d442_abstention.json"

VOL_WINDOW = 21          # D259's estimator, inherited
Q_WINDOW = 252           # trailing quantile window
WARMUP = VOL_WINDOW + Q_WINDOW
THETA_PRIMARY = 0.20
THETAS = (0.10, 0.20, 0.30, 0.40)
PRIMARY_SYMBOL = "SPY"
PRIMARY_PLAN = "MFFU Rapid EOD/50"
SEED = 20260911


# ==============================================================================================
# The gate
# ==============================================================================================

def gate_mask(r: np.ndarray, theta: float) -> np.ndarray:
    """True where the hold is ABSTAINED.

    sigma_t uses the PRIOR 21 holds only and q_t the PRIOR 252 sigmas only. Neither ever sees
    hold t. That is the whole failure mode of an abstention study and [A1] re-derives it."""
    n = len(r)
    sig = D440.sigma_series(r)                      # sig[t] from r[t-21:t]; NaN before that
    mask = np.zeros(n, bool)
    for t in range(WARMUP, n):
        hist = sig[t - Q_WINDOW:t]                  # prior sigmas only, never sig[t]
        hist = hist[~np.isnan(hist)]
        if hist.size == 0:
            continue
        mask[t] = sig[t] > np.quantile(hist, 1.0 - theta)
    return mask


def run_lengths(mask: np.ndarray) -> list[int]:
    out, k = [], 0
    for v in mask:
        if v:
            k += 1
        elif k:
            out.append(k); k = 0
    if k:
        out.append(k)
    return out


def apply_mask(h: pd.DataFrame, mask: np.ndarray) -> pd.DataFrame:
    """An abstained hold is FLAT: no P&L, no excursion, and -- the point of the rule -- the
    floor does not ratchet."""
    g = h.copy()
    for c in ("d_low", "d_high", "d_end"):
        g.loc[mask, c] = 0.0
    g.loc[mask, "max_dd"] = 0.0
    g["abstained"] = mask
    return g


# ==============================================================================================
# The per-trade lens -- G1, the ledger's own criterion
# ==============================================================================================

def per_trade(h: pd.DataFrame, mask: np.ndarray) -> dict:
    traded = ~mask
    r = h["d_end"].to_numpy(dtype=float)
    dd = h["max_dd"].to_numpy(dtype=float)
    rt = r[traded]
    ddt = dd[traded]
    out = {
        "n_total": int(len(r)), "n_traded": int(traded.sum()),
        "n_abstained": int(mask.sum()), "abstain_share": float(mask.mean()),
        "mean": float(rt.mean()), "median": float(np.median(rt)),
        "sum": float(rt.sum()),
    }
    for k in (1, 2, 3):
        out[f"touch_{k}x"] = float((ddt > 0.04 / k).mean())
    return out


def g1(base: dict, gated: dict, k: int = 1) -> dict:
    """The INHERITED criterion: does floor-touch fall relatively MORE than expected P&L?"""
    d_pnl = 1.0 - gated["mean"] / base["mean"] if base["mean"] else float("nan")
    d_touch = 1.0 - gated[f"touch_{k}x"] / base[f"touch_{k}x"] if base[f"touch_{k}x"] else float("nan")
    return {"rel_fall_pnl": d_pnl, "rel_fall_touch": d_touch,
            "G1": "PASS" if d_touch > d_pnl else "FAIL", "margin": d_touch - d_pnl}


# ==============================================================================================
# The account lens
# ==============================================================================================

def account(h: pd.DataFrame, plan, frac: float, rule: str, n_paths: int, days: int) -> dict:
    return D440.run_cell(h, plan, frac, rule, "MEASURED", n_paths, days)


def best_over_grid(h, plan, rule, n_paths, days):
    row = [account(h, plan, f, rule, n_paths, days) for f in D386.RISK_FRACS]
    return max(row, key=lambda x: x["V"]), row


# ==============================================================================================
# ROT -- enumerated
# ==============================================================================================

def rot_per_trade(h: pd.DataFrame, mask: np.ndarray, k: int = 1) -> dict:
    """Every circular offset of the mask. Vectorised: the statistic is a mean over the
    complement of a rolled boolean, so all n-1 offsets are one matrix operation per chunk."""
    n = len(mask)
    r = h["d_end"].to_numpy(dtype=float)
    dd = (h["max_dd"].to_numpy(dtype=float) > 0.04 / k).astype(float)
    idx = np.arange(n)
    means, touches = np.empty(n - 1), np.empty(n - 1)
    for j, off in enumerate(range(1, n)):
        m = mask[(idx - off) % n]
        t = ~m
        means[j] = r[t].mean()
        touches[j] = dd[t].mean()
    return {"mean_p50": float(np.median(means)), "mean_p95": float(np.percentile(means, 95)),
            "touch_p50": float(np.median(touches)), "touch_p05": float(np.percentile(touches, 5)),
            "n_offsets": n - 1}


def rot_account(h: pd.DataFrame, mask: np.ndarray, plan, frac: float, rule: str,
                n_paths: int, days: int, every: int = 1) -> dict:
    """The same enumeration on V. `every` subsamples the offsets ONLY when a full enumeration
    would not fit the budget; the report states which was used and every=1 is the default."""
    n = len(mask)
    idx = np.arange(n)
    offs = range(1, n, every)
    vals = []
    for off in offs:
        m = mask[(idx - off) % n]
        vals.append(account(apply_mask(h, m), plan, frac, rule, n_paths, days)["V"])
    v = np.asarray(vals, dtype=float)
    return {"p50": float(np.median(v)), "p95": float(np.percentile(v, 95)),
            "p05": float(np.percentile(v, 5)), "max": float(v.max()),
            "n_offsets": len(v), "enumerated": every == 1}


def blkrand_masks(mask: np.ndarray, draws: int, seed: int):
    """Matched COUNT and matched run-length MULTISET, placed at random. Secondary control --
    it exists to catch a rotation that happens to align with something periodic."""
    rng = np.random.default_rng(seed)
    n = len(mask)
    runs = run_lengths(mask)
    for _ in range(draws):
        m = np.zeros(n, bool)
        for L in rng.permutation(runs):
            for _try in range(64):
                s = int(rng.integers(WARMUP, n - L))
                if not m[max(0, s - 1):min(n, s + L + 1)].any():
                    m[s:s + L] = True
                    break
        yield m


# ==============================================================================================
# Assertions
# ==============================================================================================

def assertion_suite(h: pd.DataFrame, verbose=True) -> list[str]:
    fails = []
    g = h[h["symbol"] == PRIMARY_SYMBOL].reset_index(drop=True)
    r = g["d_end"].to_numpy(dtype=float)
    mask = gate_mask(r, THETA_PRIMARY)

    # --- 1. LAG AUDIT. Independent re-derivation, then prove it cannot see its own day.
    n = len(r)
    alt = np.zeros(n, bool)
    for t in range(WARMUP, n):
        w = r[t - VOL_WINDOW:t]
        mu = sum(w) / len(w)
        s_t = math.sqrt(sum((x - mu) ** 2 for x in w) / (len(w) - 1))
        hist = []
        for u in range(t - Q_WINDOW, t):
            ww = r[u - VOL_WINDOW:u]
            m2 = sum(ww) / len(ww)
            hist.append(math.sqrt(sum((x - m2) ** 2 for x in ww) / (len(ww) - 1)))
        alt[t] = s_t > np.quantile(np.asarray(hist), 1.0 - THETA_PRIMARY)
    if not np.array_equal(mask, alt):
        fails.append(f"[A1] lag audit: masks differ in {int((mask != alt).sum())} positions")
    r2 = r.copy(); r2[WARMUP] += 10.0
    if gate_mask(r2, THETA_PRIMARY)[WARMUP] != mask[WARMUP]:
        fails.append("[A1] lag audit: the gate at t CHANGED when r[t] changed -- it is peeking")
    # BREAK: a gate that includes its own day must be distinguishable
    def peek(x, theta):
        sig = np.full(len(x), np.nan)
        for t in range(VOL_WINDOW, len(x)):
            sig[t] = x[t - VOL_WINDOW:t + 1].std(ddof=1)      # includes t
        mm = np.zeros(len(x), bool)
        for t in range(WARMUP, len(x)):
            hh = sig[t - Q_WINDOW:t]; hh = hh[~np.isnan(hh)]
            if hh.size:
                mm[t] = sig[t] > np.quantile(hh, 1.0 - theta)
        return mm
    if np.array_equal(peek(r, THETA_PRIMARY), mask):
        fails.append("[A1-BREAK] a peeking gate was NOT distinguished from the honest one")

    # --- 2. SIGN AUDIT, IN MONEY.
    losers = r < 0
    winners = r > 0
    base_sum = r.sum()
    if not (r[~losers].sum() > base_sum):
        fails.append("[A2] sign audit: abstaining on every LOSER did not raise total P&L")
    if not (r[~winners].sum() < base_sum):
        fails.append("[A2] sign audit: abstaining on every WINNER did not lower total P&L")

    # --- 3. RIGHT QUANTITY. The gated series differs exactly where the mask is, nowhere else.
    gg = apply_mask(g, mask)
    diff = (gg["d_end"].to_numpy() != g["d_end"].to_numpy())
    nz = g["d_end"].to_numpy() != 0.0
    if not np.array_equal(diff, mask & nz):
        fails.append("[A3] right-quantity: the gated series differs somewhere the mask is not")
    share = mask[WARMUP:].mean()
    if not (abs(share - THETA_PRIMARY) < 0.05):
        fails.append(f"[A3] right-quantity: abstain share {share:.3f} far from theta "
                     f"{THETA_PRIMARY}")

    # --- 4. [REP] -- BASE must reproduce D440 bit-identically.
    plan = [p for p in D386.PLANS if p.firm == "MFFU Rapid EOD" and p.size == 50_000][0]
    for rule in ("static", "voltgt"):
        for f in D386.RISK_FRACS:
            a = account(g, plan, f, rule, 8_000, 600)["V"]
            b = D440.run_cell(g, plan, f, rule, "MEASURED", 8_000, 600)["V"]
            if a != b:
                fails.append(f"[REP] BASE {rule} {f}: {a!r} != D440 {b!r}")

    # --- 5. CONTROL ELIGIBILITY. Every ROT mask matches count and run-length multiset.
    idx = np.arange(len(mask))
    for off in (1, 7, 101, len(mask) // 2):
        m = mask[(idx - off) % len(mask)]
        if m.sum() != mask.sum():
            fails.append(f"[A5] ROT offset {off}: count {m.sum()} != {mask.sum()}")
    # run lengths are preserved up to the wrap point, which merges at most two runs
    if abs(len(run_lengths(mask[(idx - 7) % len(mask)])) - len(run_lengths(mask))) > 1:
        fails.append("[A5] ROT changed the run COUNT by more than the one wrap seam")

    # --- 6. BOTH ENDS OF THE DIAL.
    none_mask = np.zeros(len(g), bool)
    all_mask = np.ones(len(g), bool)
    v_none = account(apply_mask(g, none_mask), plan, 0.004, "static", 4_000, 400)["V"]
    v_base = account(g, plan, 0.004, "static", 4_000, 400)["V"]
    if v_none != v_base:
        fails.append(f"[A6] a never-abstaining mask did not reproduce BASE: {v_none} vs {v_base}")
    v_all = account(apply_mask(g, all_mask), plan, 0.004, "static", 4_000, 400)["V"]
    if not math.isclose(v_all, -plan.fee_eval, abs_tol=1e-9):
        fails.append(f"[A6] a fully-abstaining mask gave V={v_all}, expected -{plan.fee_eval}")

    if verbose and not fails:
        print("  [A1-A6] PASS -- six assertions, each with its deliberate break caught")
    return fails


# ==============================================================================================
# Report
# ==============================================================================================

def report(n_paths=8_000, days=600, rot_every=1) -> int:
    print("D442 -- O1, the volatility-regime abstention rule on C1\n")
    h = pd.read_csv(D440.HOLDS_CSV)
    print(f"  holds {len(h):,} from {D440.HOLDS_CSV.name}; "
          f"{n_paths:,} paths, {days} days, seed {SEED}\n")

    print("GATES")
    fails = assertion_suite(h)
    if fails:
        for f in fails[:10]:
            print("   ", f)
        print("\nASSERTIONS FAILED -- the study stops.")
        return 1

    plan = [p for p in D386.PLANS if p.firm == "MFFU Rapid EOD" and p.size == 50_000][0]
    results = []

    # ---------------------------------------------------------------- per-trade lens, G1
    print("\nPER-TRADE LENS -- G1, the ledger's own criterion (floor-touch vs P&L, relative)")
    print(f"  {'sym':<5}{'theta':>7}{'traded':>8}{'abst':>7}{'mean bp':>9}{'med bp':>8}"
          f"{'touch1x':>9}{'d_pnl':>8}{'d_touch':>9}{'G1':>7}{'maxrun':>8}")
    for sym in D440.ODR.SYMBOLS:
        g = h[h["symbol"] == sym].reset_index(drop=True)
        r = g["d_end"].to_numpy(dtype=float)
        base = per_trade(g, np.zeros(len(g), bool))
        for th in THETAS:
            m = gate_mask(r, th)
            pt = per_trade(g, m)
            res = g1(base, pt)
            mr = max(run_lengths(m)) if m.any() else 0
            star = " *" if th == THETA_PRIMARY else ""
            print(f"  {sym:<5}{th:>7.2f}{pt['n_traded']:>8,}{pt['abstain_share']:>7.1%}"
                  f"{1e4 * pt['mean']:>9.2f}{1e4 * pt['median']:>8.2f}{pt['touch_1x']:>9.3%}"
                  f"{res['rel_fall_pnl']:>8.1%}{res['rel_fall_touch']:>9.1%}"
                  f"{res['G1']:>7}{mr:>8}{star}")
            results.append({"lens": "per_trade", "symbol": sym, "theta": th,
                            "max_run": mr, **pt, **res})

    # ---------------------------------------------------------------- account lens
    print("\nACCOUNT LENS -- V per evaluation, MFFU Rapid EOD 50K, best over the risk grid")
    print(f"  {'sym':<5}{'rule':<8}{'arm':<10}{'V':>8}{'frac':>7}"
          f"{'fund_yr':>9}{'p_pass':>8}{'p_paid':>8}")
    acc = {}
    for sym in D440.ODR.SYMBOLS:
        g = h[h["symbol"] == sym].reset_index(drop=True)
        r = g["d_end"].to_numpy(dtype=float)
        m = gate_mask(r, THETA_PRIMARY)
        gated = apply_mask(g, m)
        for rule in ("static", "voltgt"):
            for arm, frame in (("BASE", g), ("O1", gated)):
                b, _row = best_over_grid(frame, plan, rule, n_paths, days)
                acc[(sym, rule, arm)] = b
                print(f"  {sym:<5}{rule:<8}{arm:<10}{b['V']:>8,.0f}{100 * b['frac']:>6.1f}%"
                      f"{b['fund_days_mean'] / 252:>9.2f}{b['p_pass']:>8.3f}{b['p_paid']:>8.3f}")
                results.append({"lens": "account", "symbol": sym, "rule": rule, "arm": arm,
                                "theta": THETA_PRIMARY, **b})

    print("\n  the increment, O1 - BASE")
    for sym in D440.ODR.SYMBOLS:
        for rule in ("static", "voltgt"):
            d = acc[(sym, rule, "O1")]["V"] - acc[(sym, rule, "BASE")]["V"]
            dl = (acc[(sym, rule, "O1")]["fund_days_mean"]
                  - acc[(sym, rule, "BASE")]["fund_days_mean"]) / 252
            print(f"    {sym:<5}{rule:<8} dV {d:>+8,.0f}   d(funded years) {dl:>+6.2f}")

    # ---------------------------------------------------------------- ROT, enumerated
    print(f"\nROT -- the abstention mask rotated against its own sequence, ENUMERATED")
    g = h[h["symbol"] == PRIMARY_SYMBOL].reset_index(drop=True)
    r = g["d_end"].to_numpy(dtype=float)
    m = gate_mask(r, THETA_PRIMARY)
    rp = rot_per_trade(g, m)
    pt = per_trade(g, m)
    print(f"  per-trade, {rp['n_offsets']:,} offsets, SE of the p95 is exactly zero")
    print(f"    mean bp   treatment {1e4 * pt['mean']:>7.2f}"
          f"   ROT p50 {1e4 * rp['mean_p50']:>7.2f}   ROT p95 {1e4 * rp['mean_p95']:>7.2f}")
    print(f"    touch1x   treatment {pt['touch_1x']:>7.3%}"
          f"   ROT p50 {rp['touch_p50']:>7.3%}   ROT p05 {rp['touch_p05']:>7.3%}")

    for rule in ("static", "voltgt"):
        b = acc[(PRIMARY_SYMBOL, rule, "O1")]
        ra = rot_account(g, m, plan, b["frac"], rule, n_paths, days, every=rot_every)
        verdict = "ABOVE p95" if b["V"] > ra["p95"] else "inside the null"
        print(f"  V, {rule}, frac {100 * b['frac']:.1f}%  "
              f"{'ENUMERATED' if ra['enumerated'] else f'1-in-{rot_every}'}"
              f" {ra['n_offsets']:,} offsets")
        print(f"    treatment {b['V']:>8,.0f}   ROT p50 {ra['p50']:>8,.0f}"
              f"   p95 {ra['p95']:>8,.0f}   max {ra['max']:>8,.0f}   -> {verdict}")
        results.append({"lens": "rot", "symbol": PRIMARY_SYMBOL, "rule": rule,
                        "V": b["V"], **{f"rot_{k}": v for k, v in ra.items()}})

    # ---------------------------------------------------------------- BLKRAND
    print("\nBLKRAND -- matched count and run-length multiset, 200 draws (secondary)")
    vals = []
    for mm in blkrand_masks(m, 200, SEED):
        vals.append(account(apply_mask(g, mm), plan,
                            acc[(PRIMARY_SYMBOL, "voltgt", "O1")]["frac"],
                            "voltgt", n_paths, days)["V"])
    v = np.asarray(vals, dtype=float)
    print(f"    p50 {np.median(v):>8,.0f}   p95 {np.percentile(v, 95):>8,.0f}"
          f"   treatment {acc[(PRIMARY_SYMBOL, 'voltgt', 'O1')]['V']:>8,.0f}")

    # ---------------------------------------------------------------- the bar
    print("\nTHE BAR -- SPY, primary theta 0.20")
    base_pt = per_trade(g, np.zeros(len(g), bool))
    res = g1(base_pt, pt)
    print(f"  G1  floor-touch falls {res['rel_fall_touch']:.1%} against P&L"
          f" {res['rel_fall_pnl']:.1%}  ->  {res['G1']}"
          f"   (margin {res['margin']:+.1%})")
    for rule in ("static", "voltgt"):
        b, ba = acc[(PRIMARY_SYMBOL, rule, "O1")], acc[(PRIMARY_SYMBOL, rule, "BASE")]
        rr = [x for x in results if x.get("lens") == "rot" and x.get("rule") == rule][0]
        up = b["V"] > ba["V"]
        clears = b["V"] > rr["rot_p95"]
        g2 = "PASS" if (up and clears) else "FAIL"
        g3 = "PASS" if b["fund_days_mean"] > ba["fund_days_mean"] else "FAIL"
        print(f"  G2 [{rule}]  V {b['V']:,.0f} vs BASE {ba['V']:,.0f} ({'up' if up else 'down'})"
              f" and vs ROT p95 {rr['rot_p95']:,.0f} ({'above' if clears else 'inside'})"
              f"  ->  {g2}")
        print(f"  G3 [{rule}]  funded years {b['fund_days_mean'] / 252:.2f} vs BASE"
              f" {ba['fund_days_mean'] / 252:.2f}  ->  {g3}"
              f"   (P4 needs 3.00)")

    pd.DataFrame(results).to_json(OUT_JSON, orient="records", indent=1)
    print(f"\nwrote {OUT_JSON.relative_to(REPO)}  ({len(results)} rows)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--paths", type=int, default=8_000)
    ap.add_argument("--days", type=int, default=600)
    ap.add_argument("--rot-every", type=int, default=1)
    a = ap.parse_args()
    if a.selftest:
        h = pd.read_csv(D440.HOLDS_CSV)
        bad = assertion_suite(h)
        for b in bad:
            print("  ", b)
        print("all gates pass" if not bad else "FAILED")
        return 1 if bad else 0
    if a.report:
        return report(n_paths=a.paths, days=a.days, rot_every=a.rot_every)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
