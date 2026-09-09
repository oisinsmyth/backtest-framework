"""PRE-SCREEN: is the MAGNITUDE of order imbalance more visible in price action
than its SIGN?

    uv run python scripts/prescreen_flow_magnitude_visibility.py

**THIS IS A PRE-SCREEN, NOT A STUDY.** It is a question about what price action
can SEE, not about what pays. Nothing is admitted to any book.

THE QUESTION
------------
prescreen_flow_proxy_fidelity.py measured how well OHLCV recovers SIGNED
aggressor imbalance: best residual corr +0.374 (BTC) / +0.362 (ETH), ~14% of
variance, top-bucket agreement 0.386 against 0.20 chance -- and WORSE on the
liquid names, which is where the prop track is going.

That tested one channel only. There is a second, and it does not need the sign:
IMPACT PER UNIT VOLUME. A large move on thin volume and a small move on heavy
volume are different states, both observable CONTEMPORANEOUSLY with no lookahead.
That is Kyle's lambda; "absorption" is its chart-pattern cousin.

Why this matters for the "smart money" question. In the microstructure
literature INFORMED flow is DEFINED by permanent price impact and uninformed
flow by transient impact -- so labelling a trade informed requires knowing the
subsequent path, which is the thing one wanted to predict. Any price-action rule
claiming to spot institutions inherits that circularity. THE MAGNITUDE CHANNEL
ESCAPES IT, because |imbalance| and volume are contemporaneous observables that
need no forward information to compute.

An unsigned state variable cannot be a directional signal. It can only be a
FILTER. That is worth saying plainly up front so nothing here is over-read.

THE TWO TARGETS
---------------
```
A  I_true(t)   = (2*taker_buy_base - base_volume) / base_volume     SIGNED
B  |I_true(t)|                                                      MAGNITUDE
```
A is already measured. B is new, and B is what a lambda-style proxy could see.

THE PROXIES FOR B -- all from OHLCV, all contemporaneous
---------------------------------------------------------
```
range_frac    = (high - low) / close
abs_bar_dir   = |close - open| / (high - low)
abs_close_pos = |2*close - high - low| / (high - low)
lambda_kyle   = |log(close/open)| / log1p(base_volume)
lambda_range  = ((high - low) / close) / log1p(base_volume)
```
`lambda_*` are the impact-per-volume family and are the reason this screen
exists. `log1p` keeps them finite on the zero-volume tail rather than dropping
those bars silently.

BOTH LENSES AGAIN, AND THE MAGNITUDE ANALOGUE OF THE RESIDUAL
---------------------------------------------------------------
Signed flow was residualised on the signed return. The magnitude analogue is to
residualise on |return| and its lags -- otherwise the tautology just returns in
absolute value, since a bar with a big move mechanically has a big |imbalance|.
Betas fitted on the first 30%, applied out-of-fit, exactly as before.

  RAW       corr(proxy, |I_true|)                    expected high, means little
  RESIDUAL  corr(resid(proxy), resid(|I_true|))      the operative number

THE BAR -- stated before looking, and it is the SAME bar the sign faced
------------------------------------------------------------------------
M1  residual |corr| >= 0.30 on both BTCUSDT and ETHUSDT for at least one proxy.
M2  top-bucket recall >= 0.40 for that proxy on both primaries (chance 0.20).

Identical thresholds to the sign screen ON PURPOSE, so the two channels are
comparable on one statistic and the comparison is not built after the fact.

WHAT EITHER ANSWER MEANS. If magnitude clears where sign failed, price action can
see HOW MUCH but not WHICH WAY, and the usable object is a filter -- a state
variable that gates a directional signal sourced elsewhere. If magnitude also
fails, then OHLCV cannot see the flow variable in EITHER channel and the entire
"infer smart money from price action" route is shut on measurement rather than
on argument.

NO EDGE CLAIM EITHER WAY. Discipline unchanged: 2024 is not read, the holdout is
not touched, all numbers are out of fit.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from prescreen_flow_proxy_fidelity import (
    F1_CORR,
    F2_RECALL,
    build as build_sign,
    corr,
    load,
    recall_top,
)
from prescreen_order_flow_persistence import (
    CUTOFF,
    FIT_FRAC,
    N_RET_LAGS,
    PRIMARY,
    Z_WINDOW,
    quintiles,
    residualise,
    trailing_z,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "flow_magnitude_visibility_stage0.json"

PROXIES = ("range_frac", "abs_bar_dir", "abs_close_pos", "lambda_kyle", "lambda_range")
IS_LAMBDA = {"lambda_kyle", "lambda_range"}


def build_magnitude(d):
    o, h, l, c = d["open"], d["high"], d["low"], d["close"]
    b, ts = d["base"], d["ts"]
    rng = h - l
    live = (rng > 0) & (b > 0)

    with np.errstate(divide="ignore", invalid="ignore"):
        i_true = np.where(live, (2.0 * d["tb"] - b) / b, np.nan)
        mag = np.abs(i_true)

        r = np.full(c.shape, np.nan)
        r[1:] = np.log(c[1:] / c[:-1])
        contig = np.zeros(c.shape, dtype=bool)
        contig[1:] = (ts[1:] - ts[:-1]).astype("int64") == 900
        r[~contig] = np.nan
        absr = np.abs(r)

        lv = np.log1p(np.where(live, b, np.nan))
        p = {
            "range_frac": np.where(live, rng / c, np.nan),
            "abs_bar_dir": np.where(live, np.abs(c - o) / rng, np.nan),
            "abs_close_pos": np.where(live, np.abs(2.0 * c - h - l) / rng, np.nan),
            "lambda_kyle": np.where(live, np.abs(np.log(c / o)) / lv, np.nan),
            "lambda_range": np.where(live, (rng / c) / lv, np.nan),
        }

    # [QTY] magnitude is a non-negative fraction; every proxy is non-negative
    f = mag[np.isfinite(mag)]
    if f.size and (f.min() < -1e-12 or f.max() > 1.0 + 1e-9):
        raise AssertionError(f"[QTY] |I_true| outside [0,1]: {f.min()} {f.max()}")
    for k, v in p.items():
        vf = v[np.isfinite(v)]
        if vf.size and vf.min() < -1e-12:
            raise AssertionError(f"[QTY] proxy {k} went negative: {vf.min()}")
    # [QTY] the two channels must not be the same object
    m = np.isfinite(mag) & np.isfinite(i_true)
    if m.sum() and abs(float(np.corrcoef(mag[m], i_true[m])[0, 1])) > 0.5:
        raise AssertionError("[QTY] magnitude and sign are not distinct channels")

    return {"mag": mag, "absr": absr, "proxies": p, "n": c.shape[0]}


def assert_magnitude_can_fail():
    """[CAN-FAIL] A proxy that IS the target must score ~1 and a proxy that is
    pure noise must score ~0. Breaks the scalar, not the assertion's name."""
    rng = np.random.default_rng(23)
    n = 40000
    tgt = np.abs(rng.normal(0, 1, n))
    same = corr(tgt, tgt)
    noise = corr(rng.normal(0, 1, n), tgt)
    if not (same > 0.99):
        raise AssertionError(f"[CAN-FAIL] identical proxy scored {same:.4f}")
    if abs(noise) > 0.05:
        raise AssertionError(f"[CAN-FAIL] noise proxy scored {noise:.4f}")


def main():
    assert_magnitude_can_fail()

    data = load()
    res = {}
    for sym, d in sorted(data.items()):
        build_sign(d)                       # re-runs that screen's [QTY] gates
        b = build_magnitude(d)
        n, absr = b["n"], b["absr"]
        fit_end = int(n * FIT_FRAC)

        e_mag, _, _, n_use = residualise(b["mag"], absr, fit_end)
        q_mag = quintiles(trailing_z(e_mag, Z_WINDOW))

        per = {}
        for name in PROXIES:
            px = b["proxies"][name]
            e_px, _, _, _ = residualise(px, absr, fit_end)
            q_px = quintiles(trailing_z(e_px, Z_WINDOW))
            per[name] = {
                "corr_raw": corr(px, b["mag"]),
                "corr_residual": corr(e_px, e_mag),
                "recall_q5": recall_top(q_mag, q_px, 4),
                "recall_q1": recall_top(q_mag, q_px, 0),
                "is_lambda": name in IS_LAMBDA,
            }
        res[sym] = {"n_bars": n, "n_reported": n_use, "proxies": per}

    verdict = {}
    for name in PROXIES:
        c_ok = all(abs(res[s]["proxies"][name]["corr_residual"]) >= F1_CORR
                   for s in PRIMARY if s in res)
        r_ok = all(res[s]["proxies"][name]["recall_q5"] >= F2_RECALL
                   for s in PRIMARY if s in res)
        verdict[name] = {"M1_corr": bool(c_ok), "M2_recall": bool(r_ok),
                         "PASSES": bool(c_ok and r_ok)}
    verdict["ANY_PROXY_PASSES"] = bool(
        any(v["PASSES"] for k, v in verdict.items() if isinstance(v, dict)))

    OUT.write_text(json.dumps({
        "design": {"cutoff_exclusive": CUTOFF, "fit_frac": FIT_FRAC,
                   "n_ret_lags": N_RET_LAGS, "z_window": Z_WINDOW,
                   "residualised_on": "abs(return) and its lags",
                   "bar": {"M1_residual_corr": F1_CORR,
                           "M2_top_bucket_recall": F2_RECALL}},
        "results": res, "verdict": verdict}, indent=1))

    for sym in sorted(res):
        rr = res[sym]
        print(f"\n=== {sym}  n={rr['n_bars']}  reported={rr['n_reported']}")
        print(f"  {'proxy':<15} {'corr_raw':>9} {'corr_res':>9} {'rec_Q5':>7} {'rec_Q1':>7}  lambda?")
        for name in PROXIES:
            p = rr["proxies"][name]
            print(f"  {name:<15} {p['corr_raw']:+9.4f} {p['corr_residual']:+9.4f} "
                  f"{p['recall_q5']:7.3f} {p['recall_q1']:7.3f}  "
                  f"{'yes' if p['is_lambda'] else '-'}")
    print(f"\nVERDICT (bar: |corr_resid| >= {F1_CORR:.2f} and recall_Q5 >= {F2_RECALL:.2f})")
    for name in PROXIES:
        v = verdict[name]
        print(f"  {name:<15} M1={str(v['M1_corr']):<5} M2={str(v['M2_recall']):<5} "
              f"PASSES={v['PASSES']}")
    print(f"  ANY_PROXY_PASSES = {verdict['ANY_PROXY_PASSES']}")
    print(f"wrote {OUT.name}")


if __name__ == "__main__":
    main()
