"""PRE-SCREEN: how much of TRUE signed order flow survives in OHLCV-only proxies?

    uv run python scripts/prescreen_flow_proxy_fidelity.py

**THIS IS A PRE-SCREEN, NOT A STUDY.** No rule is proposed and nothing is
admitted to any book. It answers one question, and it is a question about DATA,
not about edge.

THE QUESTION, AND WHY IT IS THE RIGHT ONE TO ASK WITH NO BUDGET
----------------------------------------------------------------
The principal cannot buy data now, and wants the prop-promotable idea run on free
data now and sharpened against paid data later. The promotable idea is
SIZE-CONDITIONED ORDER FLOW: prescreen_order_flow_persistence.py showed that
AGGREGATE aggressor imbalance persists strongly (acf1 +0.1429 at ~60 shuffle SE
on BTC) but does NOT order forward returns -- 0 of 16 cells monotone. Aggregate
imbalance discards exactly the variable families (a) and (c) are about: WHO
traded.

Reaching "who" needs per-trade data, which on the TARGET instrument costs money.
So the question that unlocks the sequence is not "does it pay" but:

    CAN THE FLOW VARIABLE BE SEEN AT ALL AT THE RESOLUTION WE CAN AFFORD?

That is the Stage 0 discipline -- establish the conditioner is observable before
designing anything that conditions on it.

WHY THIS CAN BE ANSWERED FOR FREE, TODAY
-----------------------------------------
`data/fixtures/crypto_binance_15m_raw.csv.gz` is the only rung of the ladder
where we hold GROUND TRUTH and a PROXY on the same bars:

  TRUE aggressor sign   taker_buy_base is a provider column, not an estimate
  TRUE VWAP             quote_volume / base_volume, verified inside [low, high]
  OHLC                  the only thing free futures bars would give us

So the degradation from "truth" to "OHLCV-only proxy" is MEASURABLE FOR FREE, and
that measurement PRICES THE PAID UPGRADE BEFORE IT IS BOUGHT. If a proxy recovers
most of the flow variable, a futures study can run on free bars and Databento is
a refinement. If it recovers nothing, then paid tick is the ONLY path and the
study cannot be rehearsed -- which is worth knowing before spending, not after.

Dukascopy, the other free tick source in docs/research/futures-data, CANNOT
answer this: it is a broker CFD feed with bid/ask and NO EXCHANGE VOLUME, so no
order-flow quantity can be built from it at any resolution.

THE TARGET IS THE FLOW VARIABLE, NOT THE EDGE
----------------------------------------------
Rung 0's EDGE failed. That does not make this ill-posed, because the target here
is I_true itself, which demonstrably exists: acf1 = +0.1429 against a shuffle SE
of 0.0024. We are asking whether OHLCV recovers a variable we KNOW is there, and
a negative answer is as useful as a positive one -- it closes the free-bar route
for futures rather than leaving it as an untested hope.

THE QUANTITIES -- all fixed here, before any look
--------------------------------------------------
```
I_true(t) = (2*taker_buy_base - base_volume) / base_volume        in [-1, +1]
vwap(t)   = quote_volume / base_volume
rng(t)    = high - low                          bars with rng == 0 are dropped

P1 close_in_range = (2*close - high - low) / rng
P2 vwap_in_range  = (2*vwap  - high - low) / rng
P3 close_vs_vwap  = 2 * (close - vwap) / rng
P4 bar_direction  = (close - open) / rng
P5 tick_rule      = sign(close(t) - close(t-1))
```
Every proxy is computable from OHLCV alone. P2 and P3 additionally need VWAP,
which free futures bar sources commonly carry (and which can be approximated by
the typical price where they do not) -- so they are reported separately and their
extra requirement is stated, not hidden.

BOTH LENSES, AND THE SECOND ONE IS THE ONE THAT MATTERS
--------------------------------------------------------
Every proxy and I_true are all driven by the SAME BAR'S RETURN, so a raw
correlation between them is largely tautological and will look flattering. What a
strategy needs is the part of flow that is NOT already in the price -- the
RESIDUAL, the same quantity rung 0 screened. So each fidelity number is reported
twice:

  RAW       corr(proxy, I_true)                          expected high, means little
  RESIDUAL  corr(resid(proxy), resid(I_true))            the operative number

where resid() removes the contemporaneous and 4 lagged returns, betas fitted on
the first 30% and applied out-of-fit, exactly as in rung 0.

THE BAR -- stated before looking
---------------------------------
F1  RESIDUAL |corr| >= 0.30 on both BTCUSDT and ETHUSDT for at least one proxy.
    Below 0.30 the proxy explains under 9% of residual flow variance and a
    free-bar futures study would be measuring mostly something else.

F2  TOP-BUCKET RECALL >= 0.40 on both primaries for that same proxy: of the bars
    truth places in its top residual quintile, at least 40% must land in the
    proxy's top residual quintile. Chance is 0.20. Bucketing is what a screen
    actually does, so agreement on BUCKETS is what decides substitutability, and
    a correlation can look respectable while the buckets disagree.

PASSING means a free-bar futures rehearsal is worth building and Databento would
SHARPEN it. FAILING means the free-bar route is shut for futures and paid tick is
not a refinement but a PREREQUISITE. Either answer directs the spend; that is the
point of running it.

NO EDGE CLAIM IS MADE HERE EITHER WAY. This screen cannot admit anything, and a
pass does not license a strategy -- it licenses a REHEARSAL.

Discipline: 2024 is not read; the holdout is not touched; all reported numbers
are out of the residualisation fit.
"""

from __future__ import annotations

import csv
import gzip
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from prescreen_order_flow_persistence import (
    CUTOFF,
    FIT_FRAC,
    N_RET_LAGS,
    PRIMARY,
    QUINTILE_Z,
    Z_WINDOW,
    acf,
    quintiles,
    residualise,
    trailing_z,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data" / "fixtures" / "crypto_binance_15m_raw.csv.gz"
OUT = ROOT / "data" / "flow_proxy_fidelity_stage0.json"

BAR_SECONDS = 900
F1_CORR = 0.30
F2_RECALL = 0.40
PROXIES = ("close_in_range", "vwap_in_range", "close_vs_vwap", "bar_direction", "tick_rule")
NEEDS_VWAP = {"vwap_in_range", "close_vs_vwap"}


def load():
    cols = defaultdict(list)
    with gzip.open(FIXTURE, "rt", newline="") as fh:
        rdr = csv.reader(fh)
        head = next(rdr)
        ix = {k: head.index(k) for k in
              ("timestamp", "symbol", "open", "high", "low", "close",
               "volume", "base_volume", "taker_buy_base")}
        for row in rdr:
            if row[ix["timestamp"]] >= CUTOFF:      # 2024 is not read
                continue
            cols[row[ix["symbol"]]].append(tuple(row[ix[k]] for k in ix))
    out = {}
    for sym, rows in cols.items():
        rows.sort(key=lambda r: r[0])
        out[sym] = {
            "ts": np.array([np.datetime64(r[0], "s") for r in rows]),
            "open": np.array([float(r[2]) for r in rows]),
            "high": np.array([float(r[3]) for r in rows]),
            "low": np.array([float(r[4]) for r in rows]),
            "close": np.array([float(r[5]) for r in rows]),
            "quote": np.array([float(r[6]) for r in rows]),
            "base": np.array([float(r[7]) for r in rows]),
            "tb": np.array([float(r[8]) for r in rows]),
        }
    return out


def build(d):
    o, h, l, c = d["open"], d["high"], d["low"], d["close"]
    q, b, tb, ts = d["quote"], d["base"], d["tb"], d["ts"]
    rng = h - l
    live = (rng > 0) & (b > 0)

    with np.errstate(divide="ignore", invalid="ignore"):
        i_true = np.where(live, (2.0 * tb - b) / b, np.nan)
        vwap = np.where(live, q / b, np.nan)

    r = np.full(c.shape, np.nan)
    r[1:] = np.log(c[1:] / c[:-1])
    contig = np.zeros(c.shape, dtype=bool)
    contig[1:] = (ts[1:] - ts[:-1]).astype("int64") == BAR_SECONDS
    r[~contig] = np.nan

    with np.errstate(divide="ignore", invalid="ignore"):
        p = {
            "close_in_range": np.where(live, (2.0 * c - h - l) / rng, np.nan),
            "vwap_in_range": np.where(live, (2.0 * vwap - h - l) / rng, np.nan),
            "close_vs_vwap": np.where(live, 2.0 * (c - vwap) / rng, np.nan),
            "bar_direction": np.where(live, (c - o) / rng, np.nan),
        }
    tick = np.full(c.shape, np.nan)
    tick[1:] = np.sign(c[1:] - c[:-1])
    tick[~contig] = np.nan
    p["tick_rule"] = np.where(live, tick, np.nan)

    # [QTY] the VWAP is a real VWAP, not a units error
    good = np.isfinite(vwap)
    inside = (vwap[good] >= l[good] - 1e-9) & (vwap[good] <= h[good] + 1e-9)
    if good.sum() and inside.mean() < 0.999:
        raise AssertionError(
            f"[QTY] VWAP outside [low,high] on {(1-inside.mean())*100:.3f}% of bars")
    # [QTY] the truth column is a signed fraction
    f = i_true[np.isfinite(i_true)]
    if f.size and (f.min() < -1 - 1e-9 or f.max() > 1 + 1e-9):
        raise AssertionError(f"[QTY] I_true outside [-1,1]: {f.min()} {f.max()}")
    for k, v in p.items():
        vf = v[np.isfinite(v)]
        if vf.size and (vf.min() < -1 - 1e-9 or vf.max() > 1 + 1e-9):
            raise AssertionError(f"[QTY] proxy {k} outside [-1,1]: {vf.min()} {vf.max()}")

    return {"i_true": i_true, "r": r, "proxies": p, "vwap": vwap, "n": c.shape[0]}


def corr(a, b):
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 1000:
        return float("nan")
    return float(np.corrcoef(a[m], b[m])[0, 1])


def recall_top(q_truth, q_proxy, bucket):
    m = (q_truth == bucket) & (q_proxy >= 0)
    if m.sum() == 0:
        return float("nan")
    return float((q_proxy[m] == bucket).mean())


def assert_recall_can_fail():
    """[CAN-FAIL] Break the SCALAR: a proxy that is truth's NEGATION must score
    far below chance on top-bucket recall, and an identical copy must score 1."""
    rng = np.random.default_rng(3)
    x = rng.normal(0, 1, 40000)
    zt = trailing_z(x, Z_WINDOW)
    qt = quintiles(zt)
    same = recall_top(qt, quintiles(trailing_z(x, Z_WINDOW)), 4)
    flip = recall_top(qt, quintiles(trailing_z(-x, Z_WINDOW)), 4)
    if not (same > 0.99):
        raise AssertionError(f"[CAN-FAIL] identical proxy scored {same:.3f}, expected 1")
    if not (flip < 0.05):
        raise AssertionError(f"[CAN-FAIL] negated proxy scored {flip:.3f}, expected ~0")


def assert_residual_removes_return(sym, res_true, r, fit_end):
    """[SIGN/QTY] The residual must be ORTHOGONAL to the contemporaneous return.
    If it is not, residualise() did not do what its name says."""
    m = np.isfinite(res_true) & np.isfinite(r)
    m[:fit_end] = False
    if m.sum() < 1000:
        raise AssertionError(f"[ORTH] {sym}: too few rows to check orthogonality")
    c = abs(float(np.corrcoef(res_true[m], r[m])[0, 1]))
    if c > 0.05:
        raise AssertionError(f"[ORTH] {sym}: residual still {c:.4f} correlated with return")


def main():
    assert_recall_can_fail()

    data = load()
    res = {}

    for sym, d in sorted(data.items()):
        b = build(d)
        n, r = b["n"], b["r"]
        fit_end = int(n * FIT_FRAC)

        e_true, _, _, n_use = residualise(b["i_true"], r, fit_end)
        assert_residual_removes_return(sym, e_true, r, fit_end)
        q_true = quintiles(trailing_z(e_true, Z_WINDOW))

        acf_true = acf(e_true, 3)
        per = {}
        for name in PROXIES:
            px = b["proxies"][name]
            e_px, _, _, _ = residualise(px, r, fit_end)
            q_px = quintiles(trailing_z(e_px, Z_WINDOW))
            per[name] = {
                "corr_raw": corr(px, b["i_true"]),
                "corr_residual": corr(e_px, e_true),
                "recall_q5": recall_top(q_true, q_px, 4),
                "recall_q1": recall_top(q_true, q_px, 0),
                "acf1_residual_proxy": acf(e_px, 1)[0],
                "needs_vwap": name in NEEDS_VWAP,
            }

        res[sym] = {
            "n_bars": n,
            "n_reported": n_use,
            "acf1_residual_truth": acf_true[0],
            "proxies": per,
        }

    verdict = {}
    for name in PROXIES:
        c_ok = all(
            abs(res[s]["proxies"][name]["corr_residual"]) >= F1_CORR
            for s in PRIMARY if s in res
        )
        r_ok = all(
            res[s]["proxies"][name]["recall_q5"] >= F2_RECALL
            for s in PRIMARY if s in res
        )
        verdict[name] = {"F1_corr": bool(c_ok), "F2_recall": bool(r_ok),
                         "PASSES": bool(c_ok and r_ok)}
    verdict["ANY_PROXY_PASSES"] = bool(any(v["PASSES"] for k, v in verdict.items()
                                           if isinstance(v, dict)))

    payload = {
        "design": {
            "fixture": str(FIXTURE.relative_to(ROOT)).replace("\\", "/"),
            "cutoff_exclusive": CUTOFF,
            "fit_frac": FIT_FRAC,
            "n_ret_lags": N_RET_LAGS,
            "z_window": Z_WINDOW,
            "quintile_z": list(QUINTILE_Z),
            "bar": {"F1_residual_corr": F1_CORR, "F2_top_bucket_recall": F2_RECALL},
        },
        "results": res,
        "verdict": verdict,
    }
    OUT.write_text(json.dumps(payload, indent=1))

    for sym in sorted(res):
        rr = res[sym]
        print(f"\n=== {sym}  n={rr['n_bars']}  reported={rr['n_reported']}"
              f"  acf1(resid truth)={rr['acf1_residual_truth']:+.4f}")
        print(f"  {'proxy':<16} {'corr_raw':>9} {'corr_res':>9} {'rec_Q5':>7} "
              f"{'rec_Q1':>7} {'acf1_px':>8}  vwap?")
        for name in PROXIES:
            p = rr["proxies"][name]
            print(f"  {name:<16} {p['corr_raw']:+9.4f} {p['corr_residual']:+9.4f} "
                  f"{p['recall_q5']:7.3f} {p['recall_q1']:7.3f} "
                  f"{p['acf1_residual_proxy']:+8.4f}  {'yes' if p['needs_vwap'] else '-'}")
    print("\nVERDICT (bar: |corr_resid| >= %.2f and recall_Q5 >= %.2f, both primaries)"
          % (F1_CORR, F2_RECALL))
    for name in PROXIES:
        v = verdict[name]
        print(f"  {name:<16} F1={str(v['F1_corr']):<5} F2={str(v['F2_recall']):<5} "
              f"PASSES={v['PASSES']}")
    print(f"  ANY_PROXY_PASSES = {verdict['ANY_PROXY_PASSES']}")
    print(f"wrote {OUT.name}")


if __name__ == "__main__":
    main()
