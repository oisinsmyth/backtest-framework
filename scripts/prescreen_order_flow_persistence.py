"""PRE-SCREEN: is there an ORDER-PERSISTENCE object in signed taker flow at 15m?

    uv run python scripts/prescreen_order_flow_persistence.py

**THIS IS A PRE-SCREEN, NOT A STUDY.** No rule is proposed, no hurdle is run, no
cell is admitted to any book. It follows D250/D251/D263's inversion -- measure
the conditional first, against a bar stated BEFORE looking, and only pay for a
full pre-registration if it clears.

WHY THIS, AND WHY NOW
---------------------
The question is the "smart money" families (a) INFORMATION LEAKAGE and (c) ORDER
PERSISTENCE: go WITH the informed/large trader, personal book first, promote to
prop if viable.

Of the reachable proxies only ONE has a promotion path. Filing flow (Form 4, 13F)
is single-name, and the prop synthesis records that no futures contract exists on
the names our equity books trade -- that lineage is PERSONAL-BOOK TERMINAL. Tape
flow is the same construction on ES/NQ as on BTC/ETH, so the free fixture is a
REHEARSAL OF THE FUTURES STUDY, and its answer decides whether the tick purchase
is justified. Same ladder logic as D262 -> D263.

`data/fixtures/crypto_binance_15m_raw.csv.gz` already carries genuinely signed
flow: `taker_buy_base` is a column, so taker sell is `base_volume - taker_buy_base`
and the aggressor imbalance needs no separate download (docs/results/
binance_provider_probe.md).

WHAT THE LITERATURE ALREADY SETTLES, so we do not pay to rediscover it
----------------------------------------------------------------------
Order flow is strongly autocorrelated with power-law decay. That is NOT an edge:
market impact is TRANSIENT and its decay very nearly offsets the flow
persistence, which is why flow can be predictable while returns are not. So the
naive family-(c) trade is already answered. The only object worth finding is the
RESIDUAL -- persistence that price has not already discounted.

Hence every part of the bar below is stated on flow RESIDUALISED ON RETURNS, and
B3 exists specifically to reject transient impact.

THE PANEL
---------
4 symbols, 765,408 rows, 2018-02-12 -> 2024-06-16 at 15 minutes.
BTCUSDT and ETHUSDT are ~0.8 correlated and XEM/BTG are thin: EFFECTIVE BREADTH
IS ~1.5, NOT 4, and is reported rather than assumed. N is large, so the binding
constraint here is NOT power -- it is economic size. A p<0.05 at N=200k can be
worth 0.1 bp.

**2024 IS NOT READ.** The screen runs on rows <= 2023-12-31 only. The holdout
panel is a separate fixture and is not touched at all (R8: stage 4 or never).

**COSTS ARE NOT THE QUESTION HERE.** Binance taker is ~10 bp/side against ES at
~0.1 bp. Under R15 a signal is a positive GROSS mean above its nulls; costs and
confluences come later, against the TARGET instrument. Killing this on crypto
fees would repeat D163's error, which D400 has just spent a study correcting.

THE SIGNAL -- every parameter fixed here, before any look
---------------------------------------------------------
```
imb(t) = (2*taker_buy_base - base_volume) / base_volume        in [-1, +1]
r(t)   = log( close(t) / close(t-1) )                          gap-masked

e(t)   = imb(t) - ( b0 + b1*r(t) + b2*r(t-1) + ... + b5*r(t-4) )
```
b fitted on the FIRST 30% of each symbol ONLY and applied to the remaining 70%;
every number reported is out-of-fit. Residualising on the CONTEMPORANEOUS return
is the point: taker buying mechanically lifts the bar it occurs in, so raw
imb-vs-return is tautological.

Bucketing uses a TRAILING 2000-bar z-score of e (no lookahead), cut at the normal
quintile points +-0.8416, +-0.2533. Normality is a bucketing convenience only and
is used for no inference.

THE BAR -- stated before looking, all three required
-----------------------------------------------------
B1  THE OBJECT EXISTS.  acf1(e) > 0, outside its shuffle null by >= 2 SE, AND
    >= 0.05 in level, with half-life >= 2 bars.
    Below that the "persistence" is price momentum reflected in flow and family
    (c) has no independent object at this frequency.

B2  IT LEADS PRICE.  Forward return is monotone across the five e-quintiles, in
    the declared direction (HIGH residual buy imbalance -> HIGHER forward
    return), INDEPENDENTLY on BTCUSDT and on ETHUSDT.
    DIRECTION IS DECLARED HERE, +1, so a reversal cannot be re-read as a result
    (D246 Constraint 3, the guard D263 needed).

B3  IT DOES NOT FULLY REVERT.  The event-time Q5-Q1 path retains >= 50% of its
    running peak AT THE END OF THE WINDOW (k = 16 bars, 4 hours).
    Full reversion is transient impact -- priced, not an edge.

    CORRECTED IN PLACE BEFORE ANY VERDICT WAS REPORTED. The first implementation
    compared k=8 against the peak over k=1..16. Both observed paths RISE to the
    right edge, so that peak sits at k=16 and the ratio measured HOW MUCH HAD
    ARRIVED BY HALFWAY, not whether anything decayed -- the criterion's name was
    right and the scalar it compared was wrong. Under the original code a path
    that never reverts at all could score 0.22 and "fail" a reversion test. The
    comparison is now END vs PEAK, which is the quantity the docstring names.
    The bar itself (>= 50%, reject transient impact) is unchanged.

FAILING ANY ONE CLOSES THIS CONSTRUCTION, NOT THE AXIS. 15-minute aggregated
aggressor imbalance is one construction; trade-SIZE decomposition from the
aggTrades archives is a different one and is not tested here.
"""

from __future__ import annotations

import csv
import gzip
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data" / "fixtures" / "crypto_binance_15m_raw.csv.gz"
OUT = ROOT / "data" / "order_flow_persistence_stage0.json"

BAR_SECONDS = 900
CUTOFF = "2024-01-01"          # rows on/after this are NOT read
FIT_FRAC = 0.30                # residualisation betas fitted on the first 30%
N_RET_LAGS = 4                 # r(t), r(t-1) .. r(t-4)
ACF_LAGS = 12
Z_WINDOW = 2000
QUINTILE_Z = (-0.8416, -0.2533, 0.2533, 0.8416)
HORIZONS = (1, 2, 4, 8)
PATH_K = 16
N_SHUFFLE = 200
DECLARED_DIRECTION = +1

B1_ACF_FLOOR = 0.05
B1_SE_MULT = 2.0
B1_HALFLIFE_MIN = 2
B3_RETENTION = 0.50
PRIMARY = ("BTCUSDT", "ETHUSDT")


# ----------------------------------------------------------------- loading

def load():
    cols = defaultdict(list)
    with gzip.open(FIXTURE, "rt", newline="") as fh:
        rdr = csv.reader(fh)
        head = next(rdr)
        i_ts, i_sym = head.index("timestamp"), head.index("symbol")
        i_close = head.index("close")
        i_base, i_tb = head.index("base_volume"), head.index("taker_buy_base")
        for row in rdr:
            if row[i_ts] >= CUTOFF:          # 2024 is not read
                continue
            cols[row[i_sym]].append(
                (row[i_ts], float(row[i_close]), float(row[i_base]), float(row[i_tb]))
            )
    out = {}
    for sym, rows in cols.items():
        rows.sort(key=lambda r: r[0])
        ts = np.array([np.datetime64(r[0], "s") for r in rows])
        out[sym] = {
            "ts": ts,
            "close": np.array([r[1] for r in rows], dtype=np.float64),
            "base": np.array([r[2] for r in rows], dtype=np.float64),
            "tb": np.array([r[3] for r in rows], dtype=np.float64),
        }
    return out


def build(d):
    base, tb, close, ts = d["base"], d["tb"], d["close"], d["ts"]
    with np.errstate(divide="ignore", invalid="ignore"):
        imb = np.where(base > 0.0, (2.0 * tb - base) / base, np.nan)
    r = np.full(close.shape, np.nan)
    r[1:] = np.log(close[1:] / close[:-1])
    contiguous = np.zeros(close.shape, dtype=bool)
    contiguous[1:] = (ts[1:] - ts[:-1]).astype("int64") == BAR_SECONDS
    r[~contiguous] = np.nan                       # never return across a gap
    return {"imb": imb, "r": r, "contig": contiguous, "ts": ts}


# ----------------------------------------------------------------- assertions

def forward_cum_return_shift(r, k):
    """Cumulative log return over bars t+1 .. t+k, via cumsum."""
    n = r.shape[0]
    out = np.full(n, np.nan)
    csum = np.concatenate([[0.0], np.cumsum(np.nan_to_num(r, nan=0.0))])
    valid = np.isfinite(r)
    vsum = np.concatenate([[0], np.cumsum(valid.astype(np.int64))])
    lo = np.arange(n) + 1
    hi = lo + k
    ok = hi <= n
    idx = np.where(ok)[0]
    seg_valid = (vsum[hi[idx]] - vsum[lo[idx]]) == k
    keep = idx[seg_valid]
    out[keep] = csum[keep + 1 + k] - csum[keep + 1]
    return out


def forward_cum_return_loop(r, k):
    """[LAG] Second implementation. Explicit index arithmetic, no cumsum and no
    reuse of the vectorised path. Must agree with it."""
    n = r.shape[0]
    out = np.full(n, np.nan)
    for t in range(n - k):
        acc = 0.0
        good = True
        for j in range(t + 1, t + 1 + k):
            v = r[j]
            if not np.isfinite(v):
                good = False
                break
            acc += v
        if good:
            out[t] = acc
    return out


def assert_lag_audit(r, k, tag):
    sl = min(r.shape[0], 20000)
    a = forward_cum_return_shift(r[:sl], k)
    b = forward_cum_return_loop(r[:sl], k)
    if not np.array_equal(np.isfinite(a), np.isfinite(b)):
        raise AssertionError(f"[LAG] {tag}: validity masks differ at k={k}")
    both = np.isfinite(a) & np.isfinite(b)
    if both.sum() == 0:
        raise AssertionError(f"[LAG] {tag}: no overlapping finite values at k={k}")
    worst = float(np.max(np.abs(a[both] - b[both])))
    if worst > 1e-10:
        raise AssertionError(f"[LAG] {tag}: max |vec - loop| = {worst:.3e} at k={k}")


def assert_lag_audit_can_fail():
    """[CAN-FAIL] Break the SCALAR the assertion compares, not its name."""
    rng = np.random.default_rng(0)
    r = rng.normal(0.0, 0.01, 5000)
    k = 4
    a = forward_cum_return_shift(r, k)
    b = forward_cum_return_loop(r, k)
    b[100] += 1e-6                                # a real, small, wrong value
    both = np.isfinite(a) & np.isfinite(b)
    if float(np.max(np.abs(a[both] - b[both]))) <= 1e-10:
        raise AssertionError("[CAN-FAIL] the lag audit cannot detect a wrong value")


def assert_sign_in_money():
    """[SIGN] On a synthetic tape where high residual buy imbalance IS followed
    by a rise, the pipeline must report Q5 > Q1 and a positive Q5-Q1."""
    rng = np.random.default_rng(7)
    n = 60000
    e = rng.normal(0.0, 1.0, n)
    r = np.full(n, np.nan)
    r[1:] = 0.001 * e[:-1] + rng.normal(0.0, 0.0005, n - 1)
    z = trailing_z(e, Z_WINDOW)
    q = quintiles(z)
    fwd = forward_cum_return_shift(r, 1)
    m = bucket_means(q, fwd)
    if not (m[4] > m[0] and (m[4] - m[0]) > 0.0):
        raise AssertionError(f"[SIGN] favourable synthetic did not pay: {m}")


def assert_quantity(imb, tag):
    """[QTY] The imbalance is the thing I think it is, not some other ratio."""
    f = imb[np.isfinite(imb)]
    if f.size == 0:
        raise AssertionError(f"[QTY] {tag}: no finite imbalance")
    if f.min() < -1.0 - 1e-9 or f.max() > 1.0 + 1e-9:
        raise AssertionError(f"[QTY] {tag}: outside [-1,1]: {f.min()} .. {f.max()}")
    mean = float(f.mean())
    if not (-0.20 < mean < 0.20):
        raise AssertionError(f"[QTY] {tag}: mean imbalance {mean:.4f} implausible")


# ----------------------------------------------------------------- machinery

def trailing_z(x, w):
    """Trailing z-score over the PRIOR w observations. Index t uses [t-w, t-1]
    and never t itself."""
    n = x.shape[0]
    g = np.nan_to_num(x, nan=0.0)
    ok = np.isfinite(x).astype(np.float64)
    cs = np.concatenate([[0.0], np.cumsum(g)])
    cs2 = np.concatenate([[0.0], np.cumsum(g * g)])
    cn = np.concatenate([[0.0], np.cumsum(ok)])
    out = np.full(n, np.nan)
    hi = np.arange(n)
    lo = np.maximum(hi - w, 0)
    cnt = cn[hi] - cn[lo]
    good = cnt >= w * 0.8
    s = cs[hi] - cs[lo]
    s2 = cs2[hi] - cs2[lo]
    with np.errstate(invalid="ignore", divide="ignore"):
        mu = s / np.where(cnt > 0, cnt, np.nan)
        var = s2 / np.where(cnt > 0, cnt, np.nan) - mu * mu
        sd = np.sqrt(np.maximum(var, 0.0))
        z = (x - mu) / np.where(sd > 0, sd, np.nan)
    out[good] = z[good]
    return out


def quintiles(z):
    q = np.full(z.shape, -1, dtype=np.int64)
    f = np.isfinite(z)
    q[f & (z < QUINTILE_Z[0])] = 0
    q[f & (z >= QUINTILE_Z[0]) & (z < QUINTILE_Z[1])] = 1
    q[f & (z >= QUINTILE_Z[1]) & (z < QUINTILE_Z[2])] = 2
    q[f & (z >= QUINTILE_Z[2]) & (z < QUINTILE_Z[3])] = 3
    q[f & (z >= QUINTILE_Z[3])] = 4
    return q


def bucket_means(q, y):
    out = []
    for b in range(5):
        m = (q == b) & np.isfinite(y)
        out.append(float(y[m].mean()) if m.sum() else float("nan"))
    return out


def acf(x, lags):
    f = np.isfinite(x)
    if f.sum() == 0:
        return [float("nan")] * lags
    xc = np.where(f, x - x[f].mean(), np.nan)
    den = float(np.nansum(xc * xc))
    out = []
    for L in range(1, lags + 1):
        a, b = xc[:-L], xc[L:]
        m = np.isfinite(a) & np.isfinite(b)
        out.append(float((a[m] * b[m]).sum() / den) if den > 0 else float("nan"))
    return out


def acf1_shuffle_se(x, draws, seed):
    rng = np.random.default_rng(seed)
    f = x[np.isfinite(x)]
    vals = [acf(rng.permutation(f), 1)[0] for _ in range(draws)]
    return float(np.std(vals, ddof=1))


def half_life(a):
    if not a or not np.isfinite(a[0]) or a[0] <= 0:
        return 0
    tgt = 0.5 * a[0]
    for i, v in enumerate(a):
        if not np.isfinite(v) or v < tgt:
            return i          # lags 1..i survived at/above target
    return len(a)


def residualise(imb, r, fit_end):
    lags = [r]
    for L in range(1, N_RET_LAGS + 1):
        s = np.full(r.shape, np.nan)
        s[L:] = r[:-L]
        lags.append(s)
    X = np.column_stack([np.ones(r.shape[0])] + lags)
    ok = np.isfinite(imb) & np.all(np.isfinite(X), axis=1)
    fit = ok.copy()
    fit[fit_end:] = False
    if fit.sum() < 1000:
        raise AssertionError("[FIT] too few rows to fit the residualisation")
    beta, *_ = np.linalg.lstsq(X[fit], imb[fit], rcond=None)
    e = np.full(imb.shape, np.nan)
    use = ok.copy()
    use[:fit_end] = False                # report OUT OF FIT only
    e[use] = imb[use] - X[use] @ beta
    return e, beta.tolist(), int(fit.sum()), int(use.sum())


# ----------------------------------------------------------------- main

def main():
    assert_lag_audit_can_fail()
    assert_sign_in_money()

    data = load()
    res = {}
    rets = {}

    for sym, d in sorted(data.items()):
        b = build(d)
        assert_quantity(b["imb"], sym)
        for k in HORIZONS:
            assert_lag_audit(b["r"], k, sym)

        n = b["imb"].shape[0]
        fit_end = int(n * FIT_FRAC)
        e, beta, n_fit, n_use = residualise(b["imb"], b["r"], fit_end)

        raw_oof = np.where(np.arange(n) >= fit_end, b["imb"], np.nan)
        a_raw = acf(raw_oof, ACF_LAGS)
        a_res = acf(e, ACF_LAGS)
        se = acf1_shuffle_se(e, N_SHUFFLE, seed=abs(hash(sym)) % 10_000)

        z = trailing_z(e, Z_WINDOW)
        q = quintiles(z)

        per_h = {}
        for k in HORIZONS:
            fwd = forward_cum_return_shift(b["r"], k)
            bp = [x * 1e4 for x in bucket_means(q, fwd)]
            inc = all(bp[i] <= bp[i + 1] for i in range(4))
            dec = all(bp[i] >= bp[i + 1] for i in range(4))
            per_h[str(k)] = {
                "quintile_bp": bp,
                "spread_q5_q1_bp": bp[4] - bp[0],
                "monotone": bool(inc if DECLARED_DIRECTION > 0 else dec),
                "n_q5": int(((q == 4) & np.isfinite(fwd)).sum()),
            }

        path = []
        for k in range(1, PATH_K + 1):
            fwd = forward_cum_return_shift(b["r"], k)
            mm = bucket_means(q, fwd)
            path.append((mm[4] - mm[0]) * 1e4)
        # B3 tests DECAY: the end of the window against the running peak. Using
        # k=8 against a peak that sits at k=16 measured build-up instead.
        peak = max(path)
        peak_k = int(np.argmax(path)) + 1
        end = path[-1]
        retention = (end / peak) if peak > 0 else float("nan")

        b1_acf = a_res[0]
        b1_hl = half_life(a_res)
        b1 = bool(
            b1_acf > 0
            and b1_acf >= B1_SE_MULT * se
            and b1_acf >= B1_ACF_FLOOR
            and b1_hl >= B1_HALFLIFE_MIN
        )
        b3 = bool(np.isfinite(retention) and retention >= B3_RETENTION)

        res[sym] = {
            "n_bars": n,
            "n_fit": n_fit,
            "n_reported": n_use,
            "beta": beta,
            "acf_raw_imb": a_raw,
            "acf_residual": a_res,
            "acf1_shuffle_se": se,
            "half_life_bars": b1_hl,
            "horizons": per_h,
            "event_path_spread_bp": path,
            "peak_bp": peak,
            "peak_k": peak_k,
            "end_bp": end,
            "retention_end_over_peak": retention,
            "B1_object_exists": b1,
            "B3_no_full_reversion": b3,
        }
        rets[sym] = (b["ts"], b["r"])

    rho = float("nan")
    if all(s in rets for s in PRIMARY):
        (ta, ra), (tb_, rb) = rets[PRIMARY[0]], rets[PRIMARY[1]]
        common, ia, ib = np.intersect1d(ta, tb_, return_indices=True)
        xa, xb = ra[ia], rb[ib]
        m = np.isfinite(xa) & np.isfinite(xb)
        if m.sum() > 100:
            rho = float(np.corrcoef(xa[m], xb[m])[0, 1])
    n_eff = len(PRIMARY) / (1.0 + (len(PRIMARY) - 1) * rho) if np.isfinite(rho) else 1.0

    b2 = {}
    for k in HORIZONS:
        b2[str(k)] = bool(all(
            res[s]["horizons"][str(k)]["monotone"]
            and res[s]["horizons"][str(k)]["spread_q5_q1_bp"] * DECLARED_DIRECTION > 0
            for s in PRIMARY if s in res
        ))

    verdict = {
        "B1_all_primary": bool(all(res[s]["B1_object_exists"] for s in PRIMARY if s in res)),
        "B2_any_horizon": bool(any(b2.values())),
        "B2_by_horizon": b2,
        "B3_all_primary": bool(all(res[s]["B3_no_full_reversion"] for s in PRIMARY if s in res)),
    }
    verdict["CLEARS"] = bool(
        verdict["B1_all_primary"] and verdict["B2_any_horizon"] and verdict["B3_all_primary"]
    )

    payload = {
        "design": {
            "fixture": str(FIXTURE.relative_to(ROOT)).replace("\\", "/"),
            "cutoff_exclusive": CUTOFF,
            "fit_frac": FIT_FRAC,
            "n_ret_lags": N_RET_LAGS,
            "z_window": Z_WINDOW,
            "horizons": list(HORIZONS),
            "declared_direction": DECLARED_DIRECTION,
            "bar": {
                "B1_acf_floor": B1_ACF_FLOOR,
                "B1_se_mult": B1_SE_MULT,
                "B1_halflife_min": B1_HALFLIFE_MIN,
                "B3_retention": B3_RETENTION,
            },
        },
        "breadth": {"rho_btc_eth": rho, "n_eff_primary": n_eff},
        "results": res,
        "verdict": verdict,
    }
    OUT.write_text(json.dumps(payload, indent=1))

    print(f"rho(BTC,ETH) = {rho:.4f}   n_eff(primary) = {n_eff:.2f}")
    for sym in sorted(res):
        r = res[sym]
        print(f"\n=== {sym}  n={r['n_bars']}  reported={r['n_reported']}")
        print(f"  acf1 raw={r['acf_raw_imb'][0]:+.4f}  resid={r['acf_residual'][0]:+.4f}"
              f"  (shuffle SE {r['acf1_shuffle_se']:.5f})  half-life={r['half_life_bars']}")
        print("  acf resid 1..6: " + " ".join(f"{v:+.4f}" for v in r["acf_residual"][:6]))
        for k in HORIZONS:
            h = r["horizons"][str(k)]
            print(f"  k={k:<2} " + " ".join(f"{v:+7.2f}" for v in h["quintile_bp"])
                  + f"  | Q5-Q1 {h['spread_q5_q1_bp']:+7.2f} bp  mono={h['monotone']}")
        print(f"  path k=1..16: " + " ".join(f"{v:+.2f}" for v in r["event_path_spread_bp"]))
        print(f"  peak={r['peak_bp']:+.2f} bp at k={r['peak_k']}  end={r['end_bp']:+.2f} bp"
              f"  retention(end/peak)={r['retention_end_over_peak']:+.2f}")
        print(f"  B1={r['B1_object_exists']}  B3={r['B3_no_full_reversion']}")
    print(f"\nVERDICT {json.dumps(verdict)}")
    print(f"wrote {OUT.name}")


if __name__ == "__main__":
    main()
