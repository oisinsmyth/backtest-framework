"""D257 — the cross-sectional trend arm, on a name holdout.

S2's uptrend state, dollar-neutralised across live names, on a 50/50 split of the
1,573-name universe pinned by seed 20260829. Cohort B carries the verdict.

HALVING THE UNIVERSE HALVES BREADTH, so a perfectly reproducing signal scores
about 0.607/sqrt(2) = 0.43 per half. THE PRIMARY COMPARABLE IS IC, which is
breadth-independent; Sharpes are reported breadth-adjusted beside the raw ones.

Offline, deterministic. `--report-only` re-renders from the artifact.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


D = _load("d256", "run_book_single_names.py")
E = _load("d243_extended", "run_book_extended.py")
RP, U = D.RP, D.U

FIX = REPO / "data" / "fixtures"
SUMMARY = REPO / "data" / "xsec_trend_arm_summary.json"
RESULTS = REPO / "docs" / "results" / "XSEC_TREND_ARM_RESULTS.md"

SPLIT_SEED = 20260829          # pinned in D257 BEFORE this file existed
SEED, N_SIMS = 0, 400
PPY, H = 252.0, 21
FEE_SN, FEE_ETF = 5e-4, 1.9e-4
BLOCK, NBOOT = 21, 2000


def rank(x):
    o = np.argsort(np.argsort(x)).astype(float)
    return (o - o.mean()) / max(o.std(), 1e-12)


def neutral(pos, live, ret, nl, fee):
    """w_i = (pos_i - f)/n_live. Sums to zero. Two-leg gross turnover charged."""
    f = (pos.sum(axis=0) / nl)[None, :]
    w = np.where(live, pos - f, 0.0) / nl[None, :]
    turn = np.abs(np.diff(w, axis=1, prepend=0.0)).sum(axis=0)
    return (w * ret).sum(axis=0) - fee * turn, w, turn


def sharpe(v):
    s = float(np.std(v, ddof=1))
    return float(np.mean(v) / s * math.sqrt(PPY)) if s > 0 else 0.0


def breadth_residual(ret, live, cols, window=1000):
    sub = np.flatnonzero(live[np.ix_(cols, np.arange(ret.shape[1] - window, ret.shape[1]))].all(axis=1))
    if sub.size < 20:
        return float("nan")
    rr = ret[np.ix_(cols[sub], np.arange(ret.shape[1] - window, ret.shape[1]))]
    dm = rr - rr.mean(axis=0, keepdims=True)
    ev = np.linalg.eigvalsh(np.corrcoef(dm))
    ev = ev[ev > 1e-10]
    return float(ev.sum() ** 2 / (ev * ev).sum())


def ic_series(sig, fwd, live, cols, keep):
    out = []
    for t in np.flatnonzero(keep):
        m = np.isfinite(sig[cols, t]) & np.isfinite(fwd[cols, t]) & live[cols, t]
        if m.sum() < 20:
            continue
        a, b = sig[cols, t][m], fwd[cols, t][m]
        if np.std(a) == 0:
            continue
        out.append(float(np.corrcoef(rank(a), rank(b - b.mean()))[0, 1]))
    return np.array(out)


def matched_null(pos, live, ret, nl, fee, cols, keep, n_sims, seed):
    """Rotate each symbol's position INSIDE its own live window, rebuild the neutral
    book from the rotated positions, and rescore. Exposure, turnover and holding
    periods are preserved; only the timing is wrong."""
    rng = np.random.default_rng(seed)
    sh = np.empty(n_sims)
    mn = np.empty(n_sims)
    idxs = [np.flatnonzero(live[i]) for i in cols]
    sub_live = live[cols]
    sub_ret = ret[cols]
    sub_nl = np.maximum(sub_live.sum(axis=0), 1)
    for k in range(n_sims):
        rot = np.zeros_like(pos[cols])
        for j, at in enumerate(idxs):
            if at.size > 1:
                rot[j, at] = np.roll(pos[cols[j], at], int(rng.integers(0, at.size)))
        r, _, _ = neutral(rot, sub_live, sub_ret, sub_nl, fee)
        r = r[keep]
        sh[k] = sharpe(r)
        mn[k] = float(np.expm1(np.sum(r)))
    return sh, mn


def build() -> dict:
    t0 = time.time()
    panel, cleaned = RP.load_ragged(FIX / "us_shorts_daily_raw.csv.gz",
                                    FIX / "us_shorts_daily_raw_events.json", fee_bps=5.0)
    n, T = panel.closes.shape
    md, hs, g_lo, g_hi, i_lo, atr, warm = D.signals_ragged(panel, cleaned, 0)
    sok = ~(np.isnan(g_lo) | np.isnan(g_hi) | np.isnan(atr)) & warm
    pos = D.walk_state(panel, (g_lo > 0) & (g_hi > 0) & sok, warm, U.AGE_CAP) * panel.live

    ret = np.where(panel.live, panel.total_log_returns, 0.0)
    live = panel.live
    keep = live.sum(axis=0) >= 100

    # forward returns, for IC
    cs = np.concatenate([np.zeros((n, 1)), np.cumsum(ret, axis=1)], axis=1)
    fwd = np.full((n, T), np.nan)
    fwd[:, :T - H - 1] = cs[:, H + 1:T] - cs[:, 1:T - H]
    fwd = np.where(live, fwd, np.nan)
    lag = np.full((n, T), np.nan)
    lag[:, 1:] = pos[:, :-1]

    # THE SPLIT -- pinned seed, no performance input
    order = np.random.default_rng(SPLIT_SEED).permutation(n)
    cohorts = {"A_screen": np.sort(order[: n // 2]), "B_holdout": np.sort(order[n // 2:])}

    out = {}
    for name, cols in cohorts.items():
        sub_live = live[cols]
        sub_nl = np.maximum(sub_live.sum(axis=0), 1)
        r, w, turn = neutral(pos[cols], sub_live, ret[cols], sub_nl, FEE_SN)
        rk = r[keep]
        ic = ic_series(lag, fwd, live, cols, keep)
        gross = np.abs(w).sum(axis=0)[keep]
        # breakeven cost: the fee at which the mean net return hits zero
        gross_ret, _, turn2 = neutral(pos[cols], sub_live, ret[cols], sub_nl, 0.0)
        be = (float(np.mean(gross_ret[keep])) / float(np.mean(turn2[keep]))
              if np.mean(turn2[keep]) > 0 else float("nan"))
        sh_n, mn_n = matched_null(pos, live, ret, nl=None, fee=FEE_SN, cols=cols,
                                  keep=keep, n_sims=N_SIMS, seed=SEED)
        money = float(np.expm1(np.sum(rk)))
        out[name] = {
            "n_names": int(len(cols)),
            "sharpe": sharpe(rk),
            "ann_return": float(np.expm1(np.mean(rk) * PPY)),
            "ann_vol": float(np.std(rk, ddof=1) * math.sqrt(PPY)),
            "gross_exposure": float(np.mean(gross)),
            "total_return": money,
            "ic_mean": float(ic.mean()), "ic_n": int(len(ic)),
            "ic_t_naive": float(ic.mean() / ic.std(ddof=1) * math.sqrt(len(ic))),
            "ic_t_corrected": float(ic.mean() / ic.std(ddof=1) * math.sqrt(len(ic) / H)),
            "breadth_residual": breadth_residual(ret, live, cols),
            "breakeven_cost_per_side": float(be),
            "null_sharpe_p95": float(np.percentile(sh_n, 95)),
            "null_money_p95": float(np.percentile(mn_n, 95)),
            "sharpe_pct": float((sh_n < sharpe(rk)).mean() * 100.0),
            "money_pct": float((mn_n < money).mean() * 100.0),
            "series": rk.tolist(),
        }
        out[name]["clears_H"] = bool(out[name]["sharpe_pct"] >= 95.0
                                     and out[name]["money_pct"] >= 95.0)
        out[name]["clears_V"] = bool(out[name]["ann_return"] > 0.0)
        print(f"  {name}: {len(cols)} names, Sharpe {out[name]['sharpe']:+.3f}, "
              f"IC {out[name]['ic_mean']:+.4f} (t {out[name]['ic_t_corrected']:+.1f}), "
              f"null {out[name]['sharpe_pct']:.1f}/{out[name]['money_pct']:.1f}  "
              f"[{time.time()-t0:.0f}s]")

    # hurdle G -- IC consistency
    a, b = out["A_screen"]["ic_mean"], out["B_holdout"]["ic_mean"]
    same_sign = (a > 0) == (b > 0)
    ratio = abs(b / a) if a != 0 else float("nan")
    out["hurdle_G"] = {"same_sign": bool(same_sign), "ratio_B_over_A": float(ratio),
                       "clears": bool(same_sign and 0.5 <= ratio <= 2.0)}

    # rho with the committed ETF book, on cohort B alone
    epanel, estart, ebooks, _ = E.books_on(*E.FIXTURES["extended"])
    er = epanel.total_log_returns
    turn_e = np.abs(np.diff(ebooks["C"], axis=1, prepend=0.0))
    etfc = ((ebooks["C"] * er).mean(axis=0) - FEE_ETF * turn_e.mean(axis=0))[estart:]
    edates = [str(d)[:10] for d in epanel.dates][estart:]
    sdates = [str(d)[:10] for d in panel.dates]
    kd = [d for d, k in zip(sdates, keep) if k]
    common = sorted(set(edates) & set(kd))
    ei = {d: i for i, d in enumerate(edates)}
    ki = {d: i for i, d in enumerate(kd)}
    A_ = etfc[[ei[d] for d in common]]
    B_ = np.asarray(out["B_holdout"]["series"])[[ki[d] for d in common]]
    rho = float(np.corrcoef(A_, B_)[0, 1])
    rng = np.random.default_rng(SEED)
    N = len(common)
    draws = np.empty(NBOOT)
    for i in range(NBOOT):
        st = rng.integers(0, N - BLOCK, size=N // BLOCK)
        ix = (st[:, None] + np.arange(BLOCK)[None, :]).ravel()
        draws[i] = np.corrcoef(A_[ix], B_[ix])[0, 1]
    sr_a, sr_b = sharpe(A_), sharpe(B_)
    combo = {}
    za, zb = A_ / A_.std(ddof=1), B_ / B_.std(ddof=1)
    for wgt in (0.0, 0.25, 0.5, 0.75, 1.0):
        combo[f"{wgt:.2f}"] = sharpe((1 - wgt) * za + wgt * zb)
    out["vs_etf_book"] = {
        "common_dates": N, "rho": rho,
        "rho_p05": float(np.percentile(draws, 5)),
        "rho_p95": float(np.percentile(draws, 95)),
        "sr_etf": sr_a, "sr_arm": sr_b, "bar": rho * sr_a,
        "adds": bool(sr_b > rho * sr_a), "combined": combo,
    }
    out["meta"] = {"study": "D257", "split_seed": SPLIT_SEED, "n_sims": N_SIMS,
                   "fee_bps_per_side": FEE_SN * 1e4, "seconds": time.time() - t0,
                   "n_symbols": n, "bars": T,
                   "span": [str(panel.dates[0])[:10], str(panel.dates[-1])[:10]]}
    for k in ("A_screen", "B_holdout"):
        out[k].pop("series")
    SUMMARY.write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
    return out


def render(p):
    o, a = [], None
    a = o.append
    m = p["meta"]
    a("# D257 — the cross-sectional trend arm, on a name holdout\n")
    a(f"**Produced by** `scripts/run_xsec_trend_arm.py` · split seed {m['split_seed']} · "
      f"{m['n_sims']:,} null draws · {m['seconds']:.0f}s\n")
    a(f"{m['n_symbols']:,} names, {m['span'][0]} → {m['span'][1]}, "
      f"{m['fee_bps_per_side']:.0f} bp/side on two legs.\n")
    a("\n**Halving the universe halves breadth**, so a perfectly reproducing signal scores about "
      "**0.43** per cohort, not 0.607. IC is the breadth-independent comparable.\n")
    a("\n| | names | Sharpe | ann. return | ann. vol | gross expo | **IC** | corr. t | "
      "residual breadth | breakeven/side | H (Sharpe/money) | V |")
    a("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:--:|")
    for k in ("A_screen", "B_holdout"):
        c = p[k]
        a(f"| **{k}** | {c['n_names']} | {c['sharpe']:+.3f} | {c['ann_return']:+.2%} | "
          f"{c['ann_vol']:.2%} | {c['gross_exposure']:.1%} | **{c['ic_mean']:+.4f}** | "
          f"{c['ic_t_corrected']:+.1f} | {c['breadth_residual']:.1f} | "
          f"{c['breakeven_cost_per_side']*1e4:.0f} bp | "
          f"{c['sharpe_pct']:.1f}th / {c['money_pct']:.1f}th | "
          f"{'y' if c['clears_V'] else 'n'} |")
    g = p["hurdle_G"]
    a(f"\n**Hurdle G** — same sign: {g['same_sign']}; ratio B/A = {g['ratio_B_over_A']:.2f}; "
      f"**{'CLEARS' if g['clears'] else 'FAILS'}**\n")
    v = p["vs_etf_book"]
    a(f"\n## Cohort B against the committed ETF book\n")
    a(f"| | |\n|---|---:|")
    a(f"| common dates | {v['common_dates']:,} |")
    a(f"| **rho** | **{v['rho']:+.3f}** (p05 {v['rho_p05']:+.3f}, p95 {v['rho_p95']:+.3f}) |")
    a(f"| SR ETF book | {v['sr_etf']:+.3f} |")
    a(f"| SR arm (cohort B) | {v['sr_arm']:+.3f} |")
    a(f"| bar `rho x SR_A` | {v['bar']:+.3f} |")
    a(f"| **diversification** | **{'ADDS' if v['adds'] else 'does NOT add'}** |")
    a("\n| weight on the arm | combined Sharpe |\n|---:|---:|")
    for w, s in v["combined"].items():
        a(f"| {float(w):.0%} | {s:+.3f} |")
    ok = p["B_holdout"]["clears_H"] and g["clears"] and p["B_holdout"]["clears_V"]
    a(f"\n## Verdict\n\n**" + ("Cohort B clears H, G and V." if ok else
      "COHORT B DOES NOT CLEAR H, G AND V TOGETHER. Per D257's stop this is CLOSED — no re-split, "
      "no second seed, no alternative neutralisation, no fallback to a time holdout.") + "**\n")
    return "\n".join(o) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()
    p = json.loads(SUMMARY.read_text(encoding="utf-8")) if args.report_only else build()
    RESULTS.write_text(render(p), encoding="utf-8")
    g, v, b = p["hurdle_G"], p["vs_etf_book"], p["B_holdout"]
    print(f"\nG: same sign {g['same_sign']}, ratio {g['ratio_B_over_A']:.2f} -> "
          f"{'CLEARS' if g['clears'] else 'FAILS'}")
    print(f"rho vs ETF book {v['rho']:+.3f} [{v['rho_p05']:+.3f},{v['rho_p95']:+.3f}], "
          f"adds={v['adds']}, combined@50% {v['combined']['0.50']:+.3f}")
    print(f"VERDICT: H={b['clears_H']} G={g['clears']} V={b['clears_V']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
