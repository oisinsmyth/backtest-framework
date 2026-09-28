"""POWER for the settlement ledger's THEORY test on CL (the principal, 2026-09-28: "a reasoned mechanism, not just
derived from data"; "Run it"). Written before the pre-registration and its runner. It reads NO in-sample CL return: the
in-sample side is the predictor panel only (days, tau*, direction, |q|, V_d, sigma_d, sigma_rem, P_held), and the
noise is the pre-sample's.

THE TWO MECHANISMS, their functional forms fixed by theory before any fit (only a scale is ever estimated):
  SR, square-root impact (the ledger's own |I|, section 5.3): an unannounced metaorder moves the price by
      E[move] = b_SR x sigma_d x sqrt(|q| / V_d) x P x M                     (x_SR)
  GM, inventory risk (Grossman-Miller 1988): liquidity providers absorb a PREDICTABLE flow and are paid for holding it
      over the horizon to the settlement, capacity scaling with the market's volume:
      E[move] = b_GM x sigma_rem^2 x (|q| / V_d) x P x M                       (x_GM)
  q = the funds' predicted rebalance at tau (q_est), V_d = the held contracts' mean whole-session volume t-20..t-1,
  sigma_d the daily return SD, sigma_rem the SD of the return from tau to the settlement (the panel's, trailing),
  P the held price at tau, M = 1,000 (CL). SR is linear in sigma and in sqrt(flow share); GM quadratic in sigma and
  linear in flow share. That difference is the test.

THE DESIGN (CL, in-sample 2017-05-22 -> 2025-02-28, A1's 2020-04-01 -> 2020-09-16 excluded; the NG-side numbers are
the spent sample's and are reported beside only):
  T1 existence, on traded days (the panel's gate at tau*): the mean signed dollar move from the t0+1 fill to the
     14:29 close, one-sided at t >= 2.2414 (D630's Holm bar for two instruments).
  T2 form, on ALL tau* days: g = a + b1 z(x_GM) + b2 z(x_SR) + b3 z(|r_tau| / sigma_d) + e (the last term is the
     continuation control: both x grow with the day's move), Newey-West lag 5. GM if t1 >= 2 and t2 < 2; SR if
     the reverse; BOTH if both; NEITHER otherwise.
  T3 is the post-window fade and is not simulated.

SIMULATION: g_t = dir_t x truth_t + u*_t(t0) x sigma_rem,t x P_t x M, with u* a 10-day moving block of the
pre-sample's standardised t0+1 -> 14:29 returns (CL front, fut_day1m, 2015-07 -> 2017-05-19). Truths: SR at a
pass-through beta of |I| (beta = 0 is the null), and GM scaled to the same mean dollar effect over all tau* days.
400 datasets per cell (1,000 at the null), seed 20260928.

    python scripts/ledger_power_theory_cl.py --extract    # SYSTEM interpreter (pyarrow): the CL pre-sample file
    uv run python scripts/ledger_power_theory_cl.py [--check]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]


def _main_checkout(repo: Path) -> Path:
    p = repo
    while p.parent != p:
        if p.name == "worktrees" and p.parent.name == ".claude":
            return p.parent.parent
        p = p.parent
    return repo


DATA_IN = _main_checkout(REPO) / "data"
FLOW = DATA_IN / "ledger_predicted_flow_daily.csv.gz"
DAY1M = DATA_IN / "fixtures" / "fut_day1m.parquet"
PRESAMPLE = REPO / "data" / "ledger_power_theory_cl_presample.csv.gz"  # gitignored by suffix; --extract rebuilds it
OUT_JSON = REPO / "data" / "ledger_power_theory_cl.json"
PRE = ("2015-06-01", "2017-05-19")
CUT, A1 = "2025-03-01", ("2020-04-01", "2020-09-16")
T0 = ("13:50", "14:00", "14:10")
M = 1_000.0
COST = 21.46 + 10.0  # A9.2's CL line (D508 effective) + one tick of entry slippage
T_HOLM, T_FORM = 2.2414, 2.0
N_TRAIL, BLOCK, SEED = 20, 10, 20260928
REPS0, REPS = 1000, 400
BETAS = (0.0, 0.1, 0.2, 0.31, 0.5)


class PowerError(RuntimeError):
    pass


def _bar(hhmm: str) -> int:
    return (int(hhmm[:2]) - 9) * 60 + int(hhmm[3:])


def extract() -> None:
    import pyarrow.parquet as pq  # type: ignore[import-not-found]
    want = [_bar(t) + 1 for t in T0] + [_bar("14:29")]
    t = pq.read_table(DAY1M, columns=["root", "day", "bar", "close", "present"],
                      filters=[("root", "==", "CL"), ("day", ">=", PRE[0]), ("day", "<=", PRE[1]),
                               ("bar", "in", want)]).to_pandas()
    if (t["day"].astype(str) > PRE[1]).any():
        raise PowerError("a pre-sample row after 2017-05-19 is in memory")
    t = t[t["present"].astype(bool)]
    w = t.pivot_table(index="day", columns="bar", values="close", aggfunc="last")
    w.columns = [f"c{int(c)}" for c in w.columns]
    w.reset_index().to_csv(PRESAMPLE, index=False, encoding="utf-8", lineterminator="\n",
                           compression={"method": "gzip", "mtime": 0})
    print(f"wrote {PRESAMPLE.name}: {len(w)} days")


def presample() -> dict[str, Any]:
    w = pd.read_csv(PRESAMPLE, encoding="utf-8").set_index("day").sort_index()
    if (w.index > PRE[1]).any():
        raise PowerError("a pre-sample row after 2017-05-19 is in memory")
    u = {}
    for t0 in T0:
        r = w[f"c{_bar('14:29')}"] / w[f"c{_bar(t0) + 1}"] - 1.0
        sd = r.rolling(N_TRAIL, min_periods=N_TRAIL).std().shift(1)
        u[t0] = r / sd
    U = pd.DataFrame(u).dropna()
    U = U[U.index >= "2015-07-01"]
    return {"days": int(len(U)), "first": U.index[0], "last": U.index[-1],
            "u_sd": {t: float(U[t].std(ddof=1)) for t in T0}, "u_kurtosis": {t: float(U[t].kurt()) for t in T0},
            "_U": U.to_numpy()}


def design(root: str = "CL") -> pd.DataFrame:
    f = pd.read_csv(FLOW, encoding="utf-8")
    f = f[f["root"] == root]
    if (f["day"] >= CUT).any():
        raise PowerError("a flow row on or after the cut is in memory")
    if root == "CL":
        f = f[~f["day"].between(*A1)]
    s = f[f["is_tau_star"] == 1][["day", "tau", "q_est", "V_d", "sigma_d", "sigma_rem_ret", "p_held",
                                  "signal_day", "r_held"]].copy()
    s = s.dropna(subset=["q_est", "V_d", "sigma_d", "sigma_rem_ret", "p_held", "r_held"])
    s = s[s["V_d"] > 0]
    share = s["q_est"].abs() / s["V_d"]
    s["x_sr"] = s["sigma_d"] * np.sqrt(share) * s["p_held"] * M
    s["x_gm"] = s["sigma_rem_ret"] ** 2 * share * s["p_held"] * M
    s["absI"] = 0.7 * s["x_sr"]  # the ledger's |I| in dollars (Y = 0.7)
    s["sd_usd"] = s["sigma_rem_ret"] * s["p_held"] * M
    s["mom"] = s["r_held"].abs() / s["sigma_d"]  # the day's move to tau in its own daily SD: the continuation control
    s["dir"] = np.sign(s["q_est"])
    s["traded"] = s["signal_day"] == 1
    s["t0_idx"] = s["tau"].map({t: i for i, t in enumerate(T0)})
    return s.reset_index(drop=True)


def _block(U: np.ndarray, n: int, rng: np.random.Generator) -> np.ndarray:
    out = np.empty((n, U.shape[1]))
    i = 0
    while i < n:
        s = int(rng.integers(0, len(U) - BLOCK))
        k = min(BLOCK, n - i)
        out[i:i + k] = U[s:s + k]
        i += k
    return out


def ols_nw(y: np.ndarray, X: np.ndarray, lags: int = 5) -> np.ndarray:
    """OLS t-statistics with a Newey-West (Bartlett) covariance."""
    XtX_inv = np.linalg.inv(X.T @ X)
    b = XtX_inv @ X.T @ y
    e = y - X @ b
    Z = X * e[:, None]
    S = Z.T @ Z
    for k in range(1, lags + 1):
        w = 1 - k / (lags + 1)
        G = Z[k:].T @ Z[:-k]
        S += w * (G + G.T)
    V = XtX_inv @ S @ XtX_inv
    return b / np.sqrt(np.diag(V))


def audit_classifier() -> None:
    """T2's classifier must name the true form on a noiseless-ish dataset, and must fire both ways."""
    rng = np.random.default_rng(1)
    n = 3000
    xg, xs = rng.lognormal(0, 1, n), rng.lognormal(0, 1, n)
    X = np.column_stack([np.ones(n), (xg - xg.mean()) / xg.std(), (xs - xs.mean()) / xs.std()])
    for truth, want in ((xg, "GM"), (xs, "SR")):
        t = ols_nw(truth + rng.standard_normal(n) * 0.5, X)
        if classify(t[1], t[2]) != want:
            raise PowerError(f"audit: the T2 classifier did not name {want}")


def classify(t_gm: float, t_sr: float) -> str:
    if t_gm >= T_FORM and t_sr >= T_FORM:
        return "BOTH"
    if t_gm >= T_FORM:
        return "GM"
    if t_sr >= T_FORM:
        return "SR"
    return "NEITHER"


def simulate(d: pd.DataFrame, U: np.ndarray, rng: np.random.Generator) -> dict[str, Any]:
    n = len(d)
    t0 = d["t0_idx"].to_numpy()
    sd = d["sd_usd"].to_numpy()
    dirs, traded = d["dir"].to_numpy(), d["traded"].to_numpy()
    xg, xs, absI = d["x_gm"].to_numpy(), d["x_sr"].to_numpy(), d["absI"].to_numpy()
    mom = d["mom"].to_numpy()
    z = [(v - v.mean()) / v.std() for v in (xg, xs, mom)]
    X = np.column_stack([np.ones(n), z[0], z[1], z[2]])
    out: dict[str, Any] = {"n_days": n, "n_traded": int(traded.sum()), "corr_x_gm_x_sr": float(np.corrcoef(xg, xs)[0, 1]),
                           "corr_x_gm_mom": float(np.corrcoef(xg, mom)[0, 1]),
                           "corr_x_sr_mom": float(np.corrcoef(xs, mom)[0, 1])}
    for beta in BETAS:
        for truth in (("SR", "GM") if beta > 0 else ("null",)):
            eff = beta * absI if truth in ("SR", "null") else xg * (beta * absI).mean() / xg.mean()
            t1s, cls, nets = [], [], []
            for _ in range(REPS0 if beta == 0 else REPS):
                u = _block(U, n, rng)[np.arange(n), t0]
                g = eff + u * sd  # signed (in the flow's direction) dollars per contract
                gt = g[traded]
                t1s.append(float(gt.mean() / (gt.std(ddof=1) / np.sqrt(len(gt)))))
                nets.append(float(gt.mean() - COST))
                tt = ols_nw(g, X)
                cls.append(classify(tt[1], tt[2]))
            c = pd.Series(cls).value_counts(normalize=True).to_dict()
            out[f"beta={beta:g} truth={truth}"] = {
                "reps": len(t1s), "T1_power": float(np.mean(np.array(t1s) >= T_HOLM)),
                "T1_t_median": float(np.median(t1s)), "net_mean_median_usd": float(np.median(nets)),
                "T2": {k: float(c.get(k, 0.0)) for k in ("GM", "SR", "BOTH", "NEITHER")},
                "mean_effect_all_days_usd": float(eff.mean()), "mean_effect_traded_usd": float(eff[traded].mean())}
    _ = dirs
    return out


def build() -> dict[str, Any]:
    audit_classifier()
    rng = np.random.default_rng(SEED)
    ps = presample()
    d = design("CL")
    sim = simulate(d, ps["_U"], rng)
    return {"pre_sample": {k: v for k, v in ps.items() if not k.startswith("_")}, "seed": SEED, "betas": BETAS,
            "t_holm": T_HOLM, "t_form": T_FORM, "cost_usd_full_cl": COST,
            "plausible_effect": "beta = 0.31, NG's measured pass-through of |I| (spent sample, D630's trades)",
            "sim": sim}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--extract", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.extract:
        extract()
        return 0
    out = build()
    text = json.dumps(out, indent=1, sort_keys=True, default=str) + "\n"
    if a.check:
        if OUT_JSON.read_text(encoding="utf-8") != text:
            raise PowerError(f"{OUT_JSON.name} does not reproduce")
        print(f"[check] {OUT_JSON.name} reproduces byte for byte")
        return 0
    OUT_JSON.write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps(out["pre_sample"], indent=1, default=str))
    print(f"CL: {out['sim']['n_days']} tau* days, {out['sim']['n_traded']} traded; corr(x_GM, x_SR) "
          f"{out['sim']['corr_x_gm_x_sr']:.3f}")
    for k, v in out["sim"].items():
        if isinstance(v, dict):
            print(f"{k:24s} T1 power {v['T1_power']:.2f} (t med {v['T1_t_median']:.2f}, net med {v['net_mean_median_usd']:+.1f}) "
                  f"T2 {v['T2']}  effect all/traded ${v['mean_effect_all_days_usd']:.1f}/${v['mean_effect_traded_usd']:.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
