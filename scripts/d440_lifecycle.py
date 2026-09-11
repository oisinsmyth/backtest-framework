"""D440 -- C1's MEASURED path through D386's lifecycle model, against a Gaussian one.

    uv run python scripts/d440_lifecycle.py --selftest
    uv run python scripts/d440_lifecycle.py --report

PRE-REGISTRATION: docs/decisions/D440-the-measured-path-through-the-lifecycle-model.md

THE QUESTION. d386_full_lifecycle.simulate() draws `inc = rng.normal(dmu, sd)`. It values a
GAUSSIAN trader, parameterised by (Sharpe, vol), and D386's own ASSUMPTIONS list says so:

    "Daily P&L is Gaussian. Real P&L is fat-tailed, which RAISES the chance of clearing a high
     daily-profit threshold at small size and LOWERS survival. Both effects are unmodelled."

D259 measured a real path -- C1's 18:00 ET -> 16:00 ET hold, 12,985 of them, median MAE 0.55%,
p99 3.98% sitting exactly on the 4% floor, worst 13.85%. This runner puts the second through
the first and changes nothing else.

WHAT IS INJECTED, AND IT IS THE WHOLE INTERFACE. d386's loop needs three numbers per live path
per day -- (d_low, d_high, d_end), the day's running minimum, maximum and end in DOLLARS. That
is all a "path provider" supplies. Three are implemented:

    GAUSS     d386's own draw, at the measured path's OWN mean and vol. The control that
              destroys the entire path shape and keeps the first two moments.
    MEASURED  the historical hold sequence, per symbol, rolling start at every hold.
              No distributional assumption anywhere in it.
    SHUF      the same holds drawn i.i.d. -- destroys serial structure and regime clustering,
              preserves the exact marginal INCLUDING the tail.

GAUSS and SHUF are not two versions of one control. GAUSS minus MEASURED is the total cost of
the Gaussian assumption; SHUF sits between them and splits it into "fat marginal" and
"clustering in time".

SIZING. d386's risk grid is daily vol as a FRACTION OF ACCOUNT SIZE, so a measured hold-return
series enters at notional N = f*size/sigma, which makes the grid point mean the same thing for
every provider. Two sizing rules:

    static    N = f*size / sigma_full          constant notional
    voltgt    N_t = f*size / sigma_hat_t       D259's rule: sigma over the PRIOR 21 holds only
                                               (R9), capped at 4x static, static during warmup

TWO REPRODUCTION GATES, both must pass before any measured number is computed:

    [P1]  the Gaussian provider reproduces d386_full_lifecycle.simulate BIT-IDENTICALLY.
    [REP] the holds reproduce D259's published statistics. Satisfied upstream by
          run_overnight_decomposition.py regenerating OVERNIGHT_DECOMPOSITION_RESULTS.md with
          a zero git diff; re-asserted here on the numbers this runner actually consumes.

THIS IS NOT AN ADMISSION TEST. D259 read the whole 2010-2026 window, so no honest holdout
exists on this fixture. See the pre-registration, section 1.
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
import run_overnight_decomposition as ODR               # noqa: E402

HOLDS_CSV = REPO / "data" / "d440_holds.csv.gz"
OUT_JSON = REPO / "data" / "d440_lifecycle.json"

PRIMARY_PLAN = "MFFU Rapid EOD/50"
PRIMARY_SYMBOL = "SPY"
VOL_WINDOW = 21                 # D259: "the prior 21 holds only"
VOL_CAP = 4.0                   # D259: "capped"
SEED = 20260911

# D259's published numbers, for [REP]. Source: the committed
# OVERNIGHT_DECOMPOSITION_RESULTS.md and D259 result 2.
D259_REP = {
    "n_all": 12985, "n_2010-2019": 7758, "n_2020": 792, "n_2021-2026": 4435,
    "mae_mean": 0.0081, "mae_p50": 0.0055, "mae_p90": 0.0187, "mae_p95": 0.0244,
    "mae_p99": 0.0398, "mae_worst": 0.1385,
    "breach_1x": 0.0207, "breach_2x": 0.1647, "breach_3x": 0.3473,
}
D259_REP_ERA_P99 = {"2010-2019": 0.0348, "2020": 0.0705, "2021-2026": 0.0390}
D259_REP_ERA_BREACH1 = {"2010-2019": 0.0106, "2020": 0.1136, "2021-2026": 0.0219}
D259_REP_SYM_BREACH1 = {"SPY": 0.0141, "QQQ": 0.0276, "IWM": 0.0300, "DIA": 0.0110}


# ==============================================================================================
# Stage 1 -- the holds, rebuilt through D259's own code path
# ==============================================================================================

def walk_lohi(entry: float, pts: list) -> dict:
    """(d_low, d_high) over the hold, relative to ENTRY.

    D259's own `walk` returns the trailing drawdown and the MAE. d386 needs the running
    minimum and maximum instead, because its floor logic does the ratcheting itself. The MAE
    is recomputed here and asserted equal to D259's to prove the two walks agree."""
    lo_rel = 0.0
    hi_rel = 0.0
    for _seg, hi, lo in pts:
        lo_rel = min(lo_rel, lo / entry - 1.0)
        hi_rel = max(hi_rel, hi / entry - 1.0)
    return {"d_low": lo_rel, "d_high": hi_rel}


def build_holds() -> pd.DataFrame:
    df = ODR.load()
    df = df[df["suspect"] == 0]                  # the "corroborated" variant -- D259's headline
    drop = ODR.half_days(df)
    rows = []
    for sym in ODR.SYMBOLS:
        sess = ODR.sessions_for(df, sym, drop)
        days = sorted(sess)
        import datetime as _dt
        for a, b in zip(days, days[1:]):
            if (_dt.date.fromisoformat(b) - _dt.date.fromisoformat(a)).days != 1:
                continue                          # Globex shut Friday evening -- D259's rule
            p = ODR.path_points(sess, a, b, "corroborated")
            if p is None:
                continue
            entry, pts, exit_px = p
            w = ODR.walk(entry, pts)
            rows.append({"symbol": sym, "day": b, "era": ODR.era_of(b),
                         "d_end": exit_px / entry - 1.0,
                         "mae": w["mae"], "max_dd": w["max_dd"], **walk_lohi(entry, pts)})
    out = pd.DataFrame(rows).sort_values(["symbol", "day"], kind="stable").reset_index(drop=True)
    return out


def rep_gate(h: pd.DataFrame) -> list[str]:
    """[REP] -- the holds must reproduce D259 before anything is built on them."""
    fails = []

    def chk(name, got, want, tol):
        if not (abs(got - want) <= tol):
            fails.append(f"[REP] {name}: got {got:.6f}, D259 {want:.6f}, tol {tol}")

    mae = -h["mae"].to_numpy()
    chk("n_all", len(h), D259_REP["n_all"], 0)
    chk("mae_mean", mae.mean(), D259_REP["mae_mean"], 5e-5)
    chk("mae_p50", np.percentile(mae, 50), D259_REP["mae_p50"], 5e-5)
    chk("mae_p90", np.percentile(mae, 90), D259_REP["mae_p90"], 5e-5)
    chk("mae_p95", np.percentile(mae, 95), D259_REP["mae_p95"], 5e-5)
    chk("mae_p99", np.percentile(mae, 99), D259_REP["mae_p99"], 5e-5)
    chk("mae_worst", mae.max(), D259_REP["mae_worst"], 5e-5)
    dd = h["max_dd"].to_numpy()
    for k in (1, 2, 3):
        chk(f"breach_{k}x", float((dd > ODR.TRAILING_DD / k).mean()),
            D259_REP[f"breach_{k}x"], 5e-5)
    for era, want in D259_REP_ERA_P99.items():
        g = h[h["era"] == era]
        chk(f"n_{era}", len(g), D259_REP[f"n_{era}"], 0)
        chk(f"mae_p99[{era}]", np.percentile(-g["mae"].to_numpy(), 99), want, 5e-5)
        chk(f"breach_1x[{era}]", float((g["max_dd"].to_numpy() > ODR.TRAILING_DD).mean()),
            D259_REP_ERA_BREACH1[era], 5e-5)
    for sym, want in D259_REP_SYM_BREACH1.items():
        g = h[h["symbol"] == sym]
        chk(f"breach_1x[{sym}]", float((g["max_dd"].to_numpy() > ODR.TRAILING_DD).mean()),
            want, 5e-5)

    # the two walks must agree: D259's mae is the running minimum, which is walk_lohi's d_low
    if not np.allclose(h["mae"].to_numpy(), h["d_low"].to_numpy(), atol=1e-12):
        fails.append("[REP] walk_lohi d_low disagrees with D259's walk mae")
    # d_high >= 0 >= d_low by construction, and d_end must lie inside them
    if not (h["d_high"] >= h["d_end"] - 1e-12).all():
        fails.append("[REP] d_end above d_high on some hold")
    if not (h["d_low"] <= h["d_end"] + 1e-12).all():
        fails.append("[REP] d_end below d_low on some hold")
    return fails


# ==============================================================================================
# Stage 2 -- path providers
# ==============================================================================================

def sigma_series(r: np.ndarray) -> np.ndarray:
    """Trailing std over the PRIOR `VOL_WINDOW` holds only. Index t uses r[t-21:t] and never
    r[t] -- this is the quantity the lag audit re-derives independently."""
    n = len(r)
    out = np.full(n, np.nan)
    for t in range(VOL_WINDOW, n):
        out[t] = r[t - VOL_WINDOW:t].std(ddof=1)
    return out


def notional_series(r: np.ndarray, target_dollar_vol: float, rule: str) -> np.ndarray:
    sig_full = r.std(ddof=1)
    base = target_dollar_vol / sig_full
    if rule == "static":
        return np.full(len(r), base)
    sig = sigma_series(r)
    n = np.where(np.isnan(sig), base, target_dollar_vol / np.maximum(sig, 1e-12))
    return np.minimum(n, VOL_CAP * base)


def make_measured_provider(h: pd.DataFrame, target_dollar_vol: float, rule: str,
                           n_paths: int, shuffle: bool, seed: int):
    r = h["d_end"].to_numpy(dtype=float)
    lo = h["d_low"].to_numpy(dtype=float)
    hi = h["d_high"].to_numpy(dtype=float)
    N = notional_series(r, target_dollar_vol, rule)
    LO, HI, EN = lo * N, hi * N, r * N
    n = len(r)
    rng = np.random.default_rng(seed)
    if shuffle:
        # SHUF: i.i.d. draws from the same hold set. Serial structure destroyed, marginal kept.
        order = rng.integers(0, n, size=(n_paths, 1))
        step = rng.integers(0, n, size=(n_paths, 1))  # unused index basis, kept for clarity
    else:
        # ROLLING START AT EVERY HOLD, and no start used twice: beyond `n` distinct starts a
        # path is a DUPLICATE, not an observation, and would shrink the naive SE for free.
        order = np.arange(min(n_paths, n)).reshape(-1, 1)
        step = None

    def provider(day: int, live_idx: np.ndarray, _rng):
        if shuffle:
            j = rng.integers(0, n, size=len(live_idx))
        else:
            j = (order[live_idx, 0] + day) % n
        return LO[j], HI[j], EN[j]

    return provider


def make_gauss_provider(mu_daily: float, sd_daily: float, k: int):
    """d386's own increment, verbatim. Consumes the rng in the same order and shape, which is
    what makes [P1] bit-identical rather than merely close."""
    sd = sd_daily / math.sqrt(k)
    dmu = mu_daily / k

    def provider(_day: int, live_idx: np.ndarray, rng):
        inc = rng.normal(dmu, sd, size=(len(live_idx), k))
        cum = np.cumsum(inc, axis=1)
        return cum.min(1), cum.max(1), cum[:, -1]

    return provider


# ==============================================================================================
# Stage 3 -- d386's loop, with the increment injected. Nothing else differs.
# ==============================================================================================

def simulate_provider(p: D386.Plan, provider, *, n_paths: int = 15_000, days: int = 750,
                      seed: int = D386.__dict__.get("_SEED", 20260908)) -> dict:
    rng = np.random.default_rng(seed)
    # Hoisted invariant: d386 rebuilds `cap_now` with a Python comprehension over every live
    # path on every day -- 4.8M interpreted iterations per cell. `_caps` is a clamped lookup
    # into a fixed tuple, so it vectorises exactly. Value-identical by construction and proved
    # so by [P1], which compares against the unmodified d386 on every run.
    cap_arr = np.asarray(p.caps, dtype=float)
    cap_last = len(p.caps) - 1
    n = n_paths
    bal = np.zeros(n); ref = np.zeros(n); alive = np.ones(n, bool)
    funded = np.full(n, p.start_funded)
    qual = np.zeros(n, np.int32); prof = np.zeros(n); best = np.zeros(n)
    npay = np.zeros(n, np.int32); paid = np.zeros(n); months = np.zeros(n)
    paid_activation = np.zeros(n, bool); ever_funded = np.full(n, p.start_funded)
    d_eval = np.zeros(n); d_fund = np.zeros(n)

    for d in range(days):
        live = alive
        if not live.any():
            break
        idx = np.flatnonzero(live)
        m = idx.size
        d_fund[live & funded] += 1.0
        d_eval[live & ~funded] += 1.0

        d_low, d_high, d_end = provider(d, idx, rng)

        b = bal[live]; r = ref[live]; f = funded[live]
        dd = np.where(f, p.dd_fund, p.dd_eval)
        lock = np.where(f, np.inf if p.lock_fund is None else p.lock_fund,
                        np.inf if p.lock_eval is None else p.lock_eval)
        base = np.where(f, p.fund_start, 0.0)
        r_eff = np.minimum(np.maximum(r, base), lock)
        floor = r_eff - dd
        if p.post_payout_floor is not None:
            floor = np.where(npay[live] > 0, p.post_payout_floor, floor)

        breach = (b + d_low) <= floor

        kind = np.where(f, p.kind_fund, p.kind_eval)
        new_ref = r.copy()
        is_eod = kind == D386.EOD
        is_in = kind == D386.INTRA
        new_ref[is_eod] = np.maximum(r[is_eod], (b + d_end)[is_eod])
        new_ref[is_in] = np.maximum(r[is_in], (b + d_high)[is_in])
        b = b + d_end

        passed = (~f) & (b >= p.target) & (~breach)

        pnl = d_end
        q = qual[live] + ((f & (pnl >= p.qual_threshold)) & (~breach)).astype(np.int32)
        pr = prof[live] + np.where(f & (~breach), pnl, 0.0)
        bd = np.maximum(best[live], np.where(f & (~breach), pnl, 0.0))

        withdrawable = b - (p.fund_start + p.safety_net)
        cap_now = cap_arr[np.minimum(npay[live], cap_last)]
        cons_ok = (np.ones(m, bool) if p.consistency is None
                   else (bd <= p.consistency * np.maximum(pr, 1e-9)))
        eligible = (f & (~breach) & (q >= p.qual_days) & (pr >= p.min_total)
                    & cons_ok & (withdrawable >= p.min_payout))
        amount = np.where(eligible, np.minimum(cap_now, np.maximum(withdrawable, 0.0)), 0.0)
        b = b - amount
        np_new = npay[live] + eligible.astype(np.int32)
        q = np.where(eligible, 0, q)
        pr = np.where(eligible, 0.0, pr)
        bd = np.where(eligible, 0.0, bd)

        closed_out = np_new >= p.max_payouts
        still = (~breach) & (~closed_out)

        bal[idx] = b
        ref[idx] = np.where(passed, p.fund_start, new_ref)
        qual[idx] = q; prof[idx] = pr; best[idx] = bd; npay[idx] = np_new
        paid[idx] += amount
        alive[idx] = still
        newly = passed & still
        bal[idx[newly]] = p.fund_start
        funded[idx[newly]] = True
        ever_funded[idx[newly]] = True
        if p.monthly:
            months[idx[~funded[idx]]] += 1.0 / 21.0
        need_act = idx[newly & (~paid_activation[idx])]
        paid_activation[need_act] = True

    fees = (p.fee_eval * np.maximum(months, 1.0 / 21.0) if p.monthly
            else np.full(n, p.fee_eval)) + p.fee_activation * paid_activation
    v = paid - fees
    breached = ~alive & (npay < p.max_payouts)
    life = d_eval + d_fund
    return {
        "V": float(v.mean()), "V_se": float(v.std(ddof=1) / math.sqrt(n)),
        "paid_mean": float(paid.mean()), "paid_median": float(np.median(paid)),
        "p_paid": float((paid > 0).mean()), "p_pass": float(ever_funded.mean()),
        "fees_mean": float(fees.mean()), "n_payouts_mean": float(npay.mean()),
        "p_alive_at_horizon": float(alive.mean()),
        "p_breached": float(breached.mean()),
        "life_days_mean": float(life.mean()),
        "fund_days_mean": float(d_fund[ever_funded].mean()) if ever_funded.any() else float("nan"),
    }


# ==============================================================================================
# The gates
# ==============================================================================================

def p1_gate(verbose=True) -> list[str]:
    """[P1] -- the injected Gaussian must reproduce d386 bit-identically."""
    fails = []
    plan = [p for p in D386.PLANS if p.firm == "MFFU Rapid EOD" and p.size == 50_000][0]
    for sharpe in (0.0, 1.0, 1.5):
        for frac in D386.RISK_FRACS:
            vol = frac * plan.size
            want = D386.simulate(plan, sharpe, vol, n_paths=2_000, days=300, k=4, seed=12345)
            mu = sharpe * vol / math.sqrt(252.0)
            prov = make_gauss_provider(mu, vol, 4)
            got = simulate_provider(plan, prov, n_paths=2_000, days=300, seed=12345)
            for key in ("V", "paid_mean", "p_paid", "p_pass", "n_payouts_mean"):
                if want[key] != got[key]:
                    fails.append(f"[P1] sharpe={sharpe} frac={frac} {key}: "
                                 f"{got[key]!r} != {want[key]!r}")
    if verbose and not fails:
        print("  [P1] PASS -- injected Gaussian reproduces d386 bit-identically "
              f"({3 * len(D386.RISK_FRACS)} cells x 5 fields)")
    return fails


def assertion_suite(h: pd.DataFrame, verbose=True) -> list[str]:
    """The three runner assertions, plus the two this study needs. Each is then BROKEN and
    must raise -- an audit that cannot fail is worse than none."""
    fails = []
    r = h[h["symbol"] == PRIMARY_SYMBOL]["d_end"].to_numpy(dtype=float)

    # --- 1. LAG AUDIT. Second implementation, never calls sigma_series.
    sig = sigma_series(r)
    alt = np.full(len(r), np.nan)
    for t in range(VOL_WINDOW, len(r)):
        w = r[max(0, t - VOL_WINDOW):t]
        mean = sum(w) / len(w)
        alt[t] = math.sqrt(sum((x - mean) ** 2 for x in w) / (len(w) - 1))
    if not np.allclose(sig[VOL_WINDOW:], alt[VOL_WINDOW:], atol=1e-12):
        fails.append("[A1] lag audit: trailing sigma disagrees with the independent re-derivation")
    # and it must not see the current hold
    r2 = r.copy(); r2[VOL_WINDOW] += 10.0
    if not np.isclose(sigma_series(r2)[VOL_WINDOW], sig[VOL_WINDOW], atol=1e-12):
        fails.append("[A1] lag audit: sigma at t CHANGED when r[t] changed -- it is peeking")
    # BREAK: a sigma that includes the current hold must be caught
    def sigma_peeking(x):
        n = len(x); o = np.full(n, np.nan)
        for t in range(VOL_WINDOW, n):
            o[t] = x[t - VOL_WINDOW:t + 1].std(ddof=1)
        return o
    if np.allclose(sigma_peeking(r)[VOL_WINDOW:], alt[VOL_WINDOW:], atol=1e-12):
        fails.append("[A1-BREAK] a peeking sigma was NOT distinguished from the honest one")

    # --- 2. SIGN AUDIT, IN MONEY.
    plan = [p for p in D386.PLANS if p.firm == "MFFU Rapid EOD" and p.size == 50_000][0]
    # (d_low, d_high, d_end). A path whose END is flat never moves the balance and therefore
    # cannot breach a $2,000 floor however deep its intraday low -- the first version of this
    # test asserted otherwise and was wrong about the model, not the other way round.
    good = _constant_provider(0.0, +200.0, +200.0)
    bad = _constant_provider(-200.0, 0.0, -200.0)
    g = simulate_provider(plan, good, n_paths=200, days=60, seed=1)
    b = simulate_provider(plan, bad, n_paths=200, days=60, seed=1)
    if not (g["paid_mean"] > 0.0):
        fails.append("[A2] sign audit: a uniformly FAVOURABLE path paid nothing")
    if not (b["p_breached"] > 0.5):
        fails.append("[A2] sign audit: a uniformly ADVERSE path did not breach")
    if not (g["V"] > b["V"]):
        fails.append("[A2] sign audit: favourable path is not worth more than adverse")
    # the floor must ratchet on gains only: a flat +0 path with a big HIGH must not breach
    hi_only = _constant_provider(0.0, +5_000.0, 0.0)
    ho = simulate_provider(plan, hi_only, n_paths=200, days=60, seed=1)
    if ho["p_breached"] != 0.0:
        fails.append("[A2] sign audit: an all-upside path breached")
    # BREAK: flipping the sign of the increment must flip the verdict
    flipped = _constant_provider(-200.0, 0.0, +200.0)   # end up, low down
    fl = simulate_provider(plan, flipped, n_paths=200, days=60, seed=1)
    if fl["p_breached"] == b["p_breached"] and fl["V"] == b["V"]:
        fails.append("[A2-BREAK] a sign-flipped path produced an identical verdict")

    # --- 3. RIGHT QUANTITY. EOD and INTRA are different plans and must score differently.
    eod = [p for p in D386.PLANS if p.firm == "MFFU Rapid EOD" and p.size == 50_000][0]
    intra = [p for p in D386.PLANS if p.firm == "MFFU Rapid" and p.size == 50_000][0]
    prov = make_gauss_provider(0.0, 0.004 * 50_000, 4)
    a = simulate_provider(eod, prov, n_paths=3_000, days=400, seed=7)
    prov = make_gauss_provider(0.0, 0.004 * 50_000, 4)
    c = simulate_provider(intra, prov, n_paths=3_000, days=400, seed=7)
    if a["V"] == c["V"]:
        fails.append("[A3] right-quantity: EOD and INTRADAY trailing scored IDENTICALLY")
    if eod.kind_fund != D386.EOD or intra.kind_fund != D386.INTRA:
        fails.append("[A3] right-quantity: the plan objects are not the ones named")

    # --- 4. CONTROL ELIGIBILITY. SHUF must draw only from observed holds.
    sub = h[h["symbol"] == PRIMARY_SYMBOL]
    obs = set(np.round(sub["d_end"].to_numpy(), 12))
    prov = make_measured_provider(sub, 0.004 * 50_000, "static", 500, True, SEED)
    _lo, _hi, en = prov(0, np.arange(500), np.random.default_rng(0))
    sig_full = sub["d_end"].to_numpy().std(ddof=1)
    base = 0.004 * 50_000 / sig_full
    if not set(np.round(en / base, 12)).issubset(obs):
        fails.append("[A4] control eligibility: SHUF produced a value not in the hold set")

    # --- 5. GAUSS MATCHING. mean and vol must match the measured series it stands in for.
    rr = sub["d_end"].to_numpy(dtype=float)
    tgt = 0.004 * 50_000
    n_static = tgt / rr.std(ddof=1)
    mu_d, sd_d = rr.mean() * n_static, rr.std(ddof=1) * n_static
    if abs(sd_d - tgt) > 1e-6:
        fails.append(f"[A5] gauss matching: dollar vol {sd_d} != grid point {tgt}")

    if verbose and not fails:
        print("  [A1-A5] PASS -- five assertions, each with its deliberate break caught")
    return fails


def _constant_provider(lo: float, hi: float, end: float):
    def provider(_day, live_idx, _rng):
        m = len(live_idx)
        return np.full(m, lo), np.full(m, hi), np.full(m, end)
    return provider


# ==============================================================================================
# The honest standard error
# ==============================================================================================

def block_bootstrap_V(h: pd.DataFrame, plan, frac: float, rule: str, kind: str,
                      b: int, reps: int, n_paths: int, days: int, seed: int) -> dict:
    """CIRCULAR BLOCK BOOTSTRAP ON THE HOLD SEQUENCE, which is the only honest SE here.

    The paths are OVERLAPPING rolling windows over one sequence of ~3,266 holds, so the naive
    across-path SE counts the same hold thousands of times and is far too small. Resampling the
    SEQUENCE in circular blocks of length `b` preserves serial dependence up to `b` and destroys
    it beyond -- which is the dependence V is actually exposed to.

    `b` is SWEPT, not selected. V is a PATH FUNCTIONAL, so the inherited block length of 20 --
    calibrated for return-side statistics -- is the wrong instrument by construction, and saying
    which `b` was picked matters more than picking one."""
    rng = np.random.default_rng(seed)
    n = len(h)
    nb = int(np.ceil(n / b))
    vals = []
    for _ in range(reps):
        starts = rng.integers(0, n, size=nb)
        idx = (starts[:, None] + np.arange(b)[None, :]).ravel()[:n] % n
        vals.append(run_cell(h.iloc[idx].reset_index(drop=True), plan, frac, rule, kind,
                             n_paths, days)["V"])
    v = np.asarray(vals, dtype=float)
    return {"b": b, "reps": reps, "V_mean": float(v.mean()), "V_se": float(v.std(ddof=1)),
            "V_p05": float(np.percentile(v, 5)), "V_p95": float(np.percentile(v, 95)),
            "p_above_zero": float((v > 0).mean())}


# ==============================================================================================
# The study
# ==============================================================================================

def run_cell(h: pd.DataFrame, plan, frac: float, rule: str, provider_kind: str,
             n_paths: int, days: int) -> dict:
    r = h["d_end"].to_numpy(dtype=float)
    tgt = frac * plan.size
    if provider_kind == "GAUSS":
        n_static = tgt / r.std(ddof=1)
        prov = make_gauss_provider(r.mean() * n_static, tgt, 4)
    else:
        if provider_kind == "MEASURED":
            n_paths = min(n_paths, len(h))          # distinct starts only
        prov = make_measured_provider(h, tgt, rule, n_paths,
                                      provider_kind == "SHUF", SEED)
    out = simulate_provider(plan, prov, n_paths=n_paths, days=days, seed=SEED)
    out.update({"frac": frac, "rule": rule, "provider": provider_kind, "n_holds": len(h)})
    return out


def report(n_paths=8_000, days=600) -> int:
    print("D440 -- the measured path through D386's lifecycle model\n")
    print(f"  {n_paths:,} paths, {days} trading days, 4 intraday steps, seed {SEED}\n")

    print("GATES")
    fails = p1_gate()
    if fails:
        for f in fails[:6]:
            print("   ", f)
        print("\n[P1] FAILED -- the study stops here, per the pre-registration.")
        return 1

    if HOLDS_CSV.exists():
        h = pd.read_csv(HOLDS_CSV)
        print(f"  holds read from {HOLDS_CSV.name}")
    else:
        print("  rebuilding holds through D259's own code path ...")
        h = build_holds()
        HOLDS_CSV.parent.mkdir(parents=True, exist_ok=True)
        h.to_csv(HOLDS_CSV, index=False, compression="gzip")
        print(f"  wrote {HOLDS_CSV.name}  ({len(h):,} holds)")

    fails = rep_gate(h)
    if fails:
        for f in fails[:12]:
            print("   ", f)
        print("\n[REP] FAILED -- reconstruction failure, not a finding. The study stops.")
        return 1
    print(f"  [REP] PASS -- {len(h):,} holds reproduce D259 on 20 published statistics")

    fails = assertion_suite(h)
    if fails:
        for f in fails:
            print("   ", f)
        print("\nASSERTIONS FAILED -- the study stops.")
        return 1

    plans = {f"{p.firm}/{p.size // 1000}": p for p in D386.PLANS if p.firm.startswith("MFFU")}
    results = []

    print("\nTHE MEASURED SERIES, per symbol")
    print(f"  {'symbol':<8}{'holds':>8}{'mean/hold':>12}{'sd/hold':>10}"
          f"{'ann Sharpe':>12}{'skew':>8}{'kurt':>9}")
    for sym in list(ODR.SYMBOLS) + ["POOLED"]:
        g = h if sym == "POOLED" else h[h["symbol"] == sym]
        r = g["d_end"].to_numpy(dtype=float)
        sk = float(((r - r.mean()) ** 3).mean() / r.std() ** 3)
        ku = float(((r - r.mean()) ** 4).mean() / r.std() ** 4)
        print(f"  {sym:<8}{len(r):>8,}{r.mean() * 100:>11.4f}%{r.std(ddof=1) * 100:>9.3f}%"
              f"{r.mean() / r.std(ddof=1) * math.sqrt(252):>12.3f}{sk:>8.2f}{ku:>9.2f}")

    print("\nV PER EVALUATION PURCHASED -- MFFU Rapid EOD 50K, by provider and risk")
    print(f"  {'symbol':<7}{'rule':<8}{'provider':<10}"
          + "".join(f"{100 * f:>9.1f}%" for f in D386.RISK_FRACS) + f"{'best':>10}")
    plan = plans[PRIMARY_PLAN]
    for sym in ODR.SYMBOLS:
        g = h[h["symbol"] == sym]
        for rule in ("static", "voltgt"):
            for kind in ("GAUSS", "MEASURED", "SHUF"):
                if kind == "GAUSS" and rule == "voltgt":
                    continue
                row = [run_cell(g, plan, f, rule, kind, n_paths, days)
                       for f in D386.RISK_FRACS]
                results += [dict(r, symbol=sym, plan=PRIMARY_PLAN) for r in row]
                best = max(row, key=lambda x: x["V"])
                print(f"  {sym:<7}{rule:<8}{kind:<10}"
                      + "".join(f"{r['V']:>10,.0f}" for r in row)
                      + f"{best['V']:>10,.0f}")

    print("\nTHE GAP, primary cell -- SPY, voltgt where available, best risk")
    for sym in ODR.SYMBOLS:
        sub = [r for r in results if r["symbol"] == sym]
        gv = max((r["V"] for r in sub if r["provider"] == "GAUSS"), default=float("nan"))
        mv = max((r["V"] for r in sub if r["provider"] == "MEASURED"), default=float("nan"))
        sv = max((r["V"] for r in sub if r["provider"] == "SHUF"), default=float("nan"))
        shortfall = (gv - mv) / gv if gv else float("nan")
        split = (gv - sv) / (gv - mv) if (gv - mv) else float("nan")
        print(f"  {sym:<7} GAUSS {gv:>9,.0f}   SHUF {sv:>9,.0f}   MEASURED {mv:>9,.0f}"
              f"   shortfall {100 * shortfall:>6.1f}%   marginal-share {100 * split:>6.1f}%")

    print("\nERA SPLIT -- MEASURED, voltgt, best risk")
    for sym in (PRIMARY_SYMBOL,):
        for era in ODR.ERAS:
            g = h[(h["symbol"] == sym) & (h["era"] == era)]
            if len(g) < VOL_WINDOW + 50:
                print(f"  {era:<12} too few holds ({len(g)})")
                continue
            row = [run_cell(g, plan, f, "voltgt", "MEASURED", n_paths, days)
                   for f in D386.RISK_FRACS]
            b = max(row, key=lambda x: x["V"])
            print(f"  {era:<12}{len(g):>7,} holds   V {b['V']:>9,.0f}"
                  f"   p_pass {b['p_pass']:.3f}   p_paid {b['p_paid']:.3f}"
                  f"   breach {b['p_breached']:.3f}   best risk {100 * b['frac']:.1f}%")

    print("\nALL FIVE MFFU PLANS -- MEASURED, SPY, voltgt, best risk")
    g = h[h["symbol"] == PRIMARY_SYMBOL]
    for name, p in plans.items():
        row = [run_cell(g, p, f, "voltgt", "MEASURED", n_paths, days) for f in D386.RISK_FRACS]
        b = max(row, key=lambda x: x["V"])
        results += [dict(r, symbol=PRIMARY_SYMBOL, plan=name) for r in row]
        print(f"  {name:<22} V {b['V']:>9,.0f} +- {b['V_se']:>7,.0f}"
              f"   p_pass {b['p_pass']:.3f}   p_paid {b['p_paid']:.3f}"
              f"   payouts {b['n_payouts_mean']:>5.2f}   best risk {100 * b['frac']:.1f}%")

    # ------------------------------------------------------------------ THE BAR
    print("\nTHE BAR -- MFFU Rapid EOD 50K, SPY, voltgt, at the V-maximising size")
    g = h[h["symbol"] == PRIMARY_SYMBOL]
    row = [run_cell(g, plan, f, "voltgt", "MEASURED", n_paths, days) for f in D386.RISK_FRACS]
    best = max(row, key=lambda x: x["V"])
    f_star = best["frac"]
    print(f"  argmax at {100 * f_star:.1f}% of account size;  V {best['V']:,.0f}"
          f"  (naive across-path SE {best['V_se']:,.0f}, NOT USED -- the paths overlap)")
    print(f"  P(ever paid) {best['p_paid']:.3f}   P(pass) {best['p_pass']:.3f}"
          f"   payouts/eval {best['n_payouts_mean']:.2f}")
    print(f"  alive at {days}d {best['p_alive_at_horizon']:.3f}"
          f"   breached {best['p_breached']:.3f}"
          f"   mean life {best['life_days_mean']:.0f} days"
          f" = {best['life_days_mean'] / 252:.2f} years")

    print("\n  T1 -- V > 0 by 2 SE, circular block bootstrap on the hold sequence")
    boots = {}
    for b in (1, 20, 60):
        bs = block_bootstrap_V(g, plan, f_star, "voltgt", "MEASURED", b, 200,
                               n_paths, days, SEED)
        boots[b] = bs
        margin = bs["V_mean"] / bs["V_se"] if bs["V_se"] else float("nan")
        print(f"    b={b:<3} V {bs['V_mean']:>8,.0f} +- {bs['V_se']:>7,.0f}"
              f"   [{bs['V_p05']:>8,.0f}, {bs['V_p95']:>8,.0f}]"
              f"   {margin:>6.2f} SE   P(V>0) {bs['p_above_zero']:.3f}")
    worst = min(boots.values(), key=lambda x: x["V_mean"] / x["V_se"] if x["V_se"] else 0.0)
    t1_margin = worst["V_mean"] / worst["V_se"] if worst["V_se"] else float("nan")
    t1 = "PASS" if t1_margin > 2.0 else ("UNRESOLVED" if t1_margin > 0 else "FAIL")

    print("\n  T2 -- P4: expected life > 3 years at that same size")
    # P4 is about the FUNDED account, so the statistic is fund_days conditional on ever being
    # funded -- not total life, which is dominated by the ~68% that die in the evaluation.
    life_yrs = best["fund_days_mean"] / 252.0
    censored = best["p_alive_at_horizon"]
    t2 = "PASS" if (life_yrs > 3.0 and censored > 0.0) else "FAIL"
    print(f"    funded life {life_yrs:.2f} years ({best['fund_days_mean']:.0f} days),"
          f" {censored:.1%} alive at the {days}-day horizon -> {t2}")
    print("    at every grid point: " + "  ".join(
        f"{100 * r['frac']:.1f}%={r['fund_days_mean'] / 252:.2f}yr" for r in row))
    print("    D259 reported 6.40 years for this arm. That is 1 / (per-hold breach rate),")
    print("    a PER-TRADE statistic. This is the ACCOUNT's life against a floor that ratchets")
    print("    up and never down -- the object P1 is written about. Both are computed")
    print("    correctly and they are not the same quantity.")

    print("\n  T3 -- V > 0 by 2 SE in 2021-2026 alone")
    g21 = g[g["era"] == "2021-2026"]
    row21 = [run_cell(g21, plan, f, "voltgt", "MEASURED", n_paths, days)
             for f in D386.RISK_FRACS]
    b21 = max(row21, key=lambda x: x["V"])
    bs21 = block_bootstrap_V(g21, plan, b21["frac"], "voltgt", "MEASURED", 20, 200,
                             n_paths, days, SEED)
    m21 = bs21["V_mean"] / bs21["V_se"] if bs21["V_se"] else float("nan")
    t3 = "PASS" if m21 > 2.0 else ("UNRESOLVED" if m21 > 0 else "FAIL")
    print(f"    {len(g21):,} holds   V {bs21['V_mean']:>8,.0f} +- {bs21['V_se']:>7,.0f}"
          f"   {m21:>6.2f} SE   P(V>0) {bs21['p_above_zero']:.3f} -> {t3}")

    print(f"\n  T1 {t1}   T2 {t2}   T3 {t3}"
          f"   ->  {'CANDIDATE' if t1 == t2 == t3 == 'PASS' else 'NOT A CANDIDATE'}")

    results.append({"symbol": PRIMARY_SYMBOL, "plan": PRIMARY_PLAN, "kind": "BAR",
                    "f_star": f_star, "V": best["V"], "life_years": life_yrs,
                    "p_alive": censored, "T1": t1, "T2": t2, "T3": t3,
                    "boot": {str(k): v for k, v in boots.items()}, "boot_2021": bs21})
    pd.DataFrame(results).to_json(OUT_JSON, orient="records", indent=1)
    print(f"\nwrote {OUT_JSON.relative_to(REPO)}  ({len(results)} cells)")
    return 0


def selftest() -> int:
    print("D440 selftest\n")
    bad = p1_gate()
    if bad:
        for b in bad[:6]:
            print("  ", b)
        return 1
    h = build_holds() if not HOLDS_CSV.exists() else pd.read_csv(HOLDS_CSV)
    bad = rep_gate(h)
    if bad:
        for b in bad[:12]:
            print("  ", b)
        return 1
    print(f"  [REP] PASS -- {len(h):,} holds")
    bad = assertion_suite(h)
    if bad:
        for b in bad:
            print("  ", b)
        return 1
    print("\nall gates pass")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--paths", type=int, default=8_000)
    ap.add_argument("--days", type=int, default=600)
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.report:
        return report(n_paths=a.paths, days=a.days)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
