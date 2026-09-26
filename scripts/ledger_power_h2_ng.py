"""POWER for H2 on NG (settlement ledger deposit §9 H2, §9A; the principal, 2026-09-26: "Pre-register H2 on NG").
Written before the pre-registration and its runner. It reads NO in-sample return after τ: the in-sample side is the
predictor panel only (days, τ*, direction, |I|, σ_rem, P_held), and the noise is the pre-sample's.

H2 (deposit line 542): the signed return from the t0+1 fill to the W_end close, in direction = sign(Q_rem), on traded
days (τ*'s §7.2 gate passes). In dollars per full-size contract:  g_t = dir_t × (C_14:29 − C_t0+1) × 10,000.

PRE-SAMPLE NOISE, 2015-07-01 → 2017-05-19, the 1-minute fixture's NG front contract (`fut_day1m`, bar b = 09:00 + b
minutes): for each t0 ∈ {13:50, 14:00, 14:10}, the fractional return from the close of bar t0+1 to the close of
the 14:29 bar, standardised by its own trailing 20-day SD (days t−20..t−1): u_t(t0). The three t0 of one day are
drawn together (a moving block of 10 days), so their nesting is kept.

SIMULATION: on NG's in-sample days (every business day with τ*; traded = τ* passes the gate),
    g_t(t0) = β × |I_t| × 10,000 × dir_t  +  u*_t(t0) × σ_rem,t × P_t × 10,000
where σ_rem is the panel's trailing SD of the held return from τ to the settlement (the gate's own input) and |I_t|
the ledger's predicted move at τ*. β = 0 is the null; β = 1 is the ledger's own prediction. 1,000 datasets at β = 0,
400 otherwise, seed 20260926.
  * The gate t: the mean of g over traded days / its SE (one trade per day, so the day-clustered SE). Holm across
    the deposit's two instruments (A2) needs two-sided p ≤ 0.025: t ≥ 2.2414.
  * Power: the share with t ≥ 2.2414; and with the net mean > 0 at 1× cost ($16 round trip + 1 tick = $26).
  * The rotation control (A9's shape for H2): the day-level signal (traded flag, direction, t0) is rotated
    circularly within year by an offset in [20, n_year − 20] over ALL business days and scored against the day's own
    returns at the rotated t0; 200 rotations per dataset on 100 datasets at β = 0 and β = 0.5. Reported: its
    false-pass rate (the share of null datasets beating their own p95) and the combined gate.
  * The time placebo is not simulated (it runs on a different window with the same design).
  * THE VAULT (2025-03-01 → 2026-09-18, ~390 business days): the same design on a random 20% of in-sample days'
    shape, i.e. n_trades × 0.2; pass = one-sided p < 0.10 (t ≥ 1.2816) and net mean > 0.

PLAUSIBLE EFFECT, stated before any run (§9A.2 rule 2): the smallest that matters is the round-trip cost, $26 per
contract (the mean at which the net is zero). The ledger's own claim is β = 1 (|I| ≥ 3 × RT on every traded day).

    python scripts/ledger_power_h2_ng.py --extract       # SYSTEM interpreter (pyarrow): the pre-sample file
    uv run python scripts/ledger_power_h2_ng.py [--check]
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
FLOW = REPO / "data" / "ledger_predicted_flow_daily.csv.gz"
DAY1M = REPO / "data" / "fixtures" / "fut_day1m.parquet"
PRESAMPLE = REPO / "data" / "ledger_power_h2_presample.csv.gz"  # gitignored by suffix; --extract rebuilds it
OUT_JSON = REPO / "data" / "ledger_power_h2_ng.json"
PRE = ("2015-06-01", "2017-05-19")
CUT = "2025-03-01"
T0 = ("13:50", "14:00", "14:10")
MULT, RT_USD, SLIP_USD = 10_000.0, 16.0, 10.0
T_HOLM, T_VAULT = 2.2414, 1.2816
N_TRAIL, BLOCK, SEED = 20, 10, 20260926
REPS0, REPS, ROT_DATASETS, ROT_DRAWS, ROT_MIN = 1000, 400, 100, 200, 20
BETAS = (0.0, 0.1, 0.25, 0.5, 1.0)
VAULT_SHARE = 0.2


class H2PowerError(RuntimeError):
    pass


def _bar(hhmm: str) -> int:
    return (int(hhmm[:2]) - 9) * 60 + int(hhmm[3:])


def extract() -> None:
    import pyarrow.parquet as pq  # type: ignore[import-not-found]
    want = [_bar(t) + 1 for t in T0] + [_bar("14:29")]
    t = pq.read_table(DAY1M, columns=["root", "day", "bar", "close", "present"],
                      filters=[("root", "==", "NG"), ("day", ">=", PRE[0]), ("day", "<=", PRE[1]),
                               ("bar", "in", want)]).to_pandas()
    if (t["day"].astype(str) > PRE[1]).any():
        raise H2PowerError("a pre-sample row after 2017-05-19 is in memory")
    t = t[t["present"].astype(bool)]
    w = t.pivot_table(index="day", columns="bar", values="close", aggfunc="last")
    w.columns = [f"c{int(c)}" for c in w.columns]
    w.reset_index().to_csv(PRESAMPLE, index=False, encoding="utf-8", lineterminator="\n",
                           compression={"method": "gzip", "mtime": 0})
    print(f"wrote {PRESAMPLE.name}: {len(w)} days")


def presample() -> dict[str, Any]:
    w = pd.read_csv(PRESAMPLE, encoding="utf-8").set_index("day").sort_index()
    if (w.index > PRE[1]).any():
        raise H2PowerError("a pre-sample row after 2017-05-19 is in memory")
    u = {}
    for t0 in T0:
        r = w[f"c{_bar('14:29')}"] / w[f"c{_bar(t0) + 1}"] - 1.0
        sd = r.rolling(N_TRAIL, min_periods=N_TRAIL).std().shift(1)
        u[t0] = r / sd
    U = pd.DataFrame(u).dropna()
    U = U[U.index >= "2015-07-01"]
    return {"days": int(len(U)), "first": U.index[0], "last": U.index[-1],
            "u_mean": {t: float(U[t].mean()) for t in T0}, "u_sd": {t: float(U[t].std(ddof=1)) for t in T0},
            "u_kurtosis": {t: float(U[t].kurt()) for t in T0}, "_U": U.to_numpy()}


def design() -> pd.DataFrame:
    f = pd.read_csv(FLOW, encoding="utf-8")
    f = f[f["root"] == "NG"]
    if (f["day"] >= CUT).any():
        raise H2PowerError("a flow row on or after the cut is in memory")
    s = f[f["is_tau_star"] == 1][["day", "tau", "q_est", "I", "sigma_rem_ret", "p_held", "signal_day"]].copy()
    sd = f[f["tau"].isin(T0)].pivot(index="day", columns="tau", values="sigma_rem_ret")
    s = s.join(sd.add_prefix("sd_"), on="day")
    s["dir"] = np.sign(s["q_est"])
    s["traded"] = (s["signal_day"] == 1).astype(int)
    s["absI_usd"] = s["I"].abs() * MULT
    return s.dropna(subset=[f"sd_{t}" for t in T0] + ["p_held"]).reset_index(drop=True)


def _block(U: np.ndarray, n: int, rng: np.random.Generator) -> np.ndarray:
    out = np.empty((n, U.shape[1]))
    i = 0
    while i < n:
        s = int(rng.integers(0, len(U) - BLOCK))
        k = min(BLOCK, n - i)
        out[i:i + k] = U[s:s + k]
        i += k
    return out


def tstat(x: np.ndarray) -> float:
    return float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x))))


def simulate(d: pd.DataFrame, U: np.ndarray, rng: np.random.Generator) -> dict[str, Any]:
    n = len(d)
    t0_idx = d["tau"].map({t: i for i, t in enumerate(T0)}).to_numpy()
    sd = d[[f"sd_{t}" for t in T0]].to_numpy() * d["p_held"].to_numpy()[:, None] * MULT  # $ per contract, per t0
    dirs, traded, absI = d["dir"].to_numpy(), d["traded"].to_numpy().astype(bool), d["absI_usd"].to_numpy()
    years = d["day"].str[:4].to_numpy()
    yidx = [np.flatnonzero(years == y) for y in np.unique(years)]
    res: dict[str, Any] = {"n_days": n, "n_traded": int(traded.sum()),
                           "median_absI_usd_traded": float(np.median(absI[traded])),
                           "median_sd_usd_traded": float(np.median(sd[traded, :].max(axis=1)))}
    for beta in BETAS:
        ts, nets, rot = [], [], []
        vault_pass = []
        for rep in range(REPS0 if beta == 0 else REPS):
            G = _block(U, n, rng) * sd + (beta * absI * dirs)[:, None]  # $ return at each t0 on each day
            g = dirs * (G[np.arange(n), t0_idx] - (beta * absI * dirs)) + beta * absI  # signed; effect in direction
            gt = g[traded]
            ts.append(tstat(gt))
            nets.append(float(gt.mean() - RT_USD - SLIP_USD))
            # the vault: a sample of VAULT_SHARE of the traded days' shape
            m = max(20, int(round(VAULT_SHARE * len(gt))))
            v = gt[rng.choice(len(gt), size=m, replace=False)]
            vault_pass.append(bool(tstat(v) >= T_VAULT and v.mean() - RT_USD - SLIP_USD > 0))
            if beta in (0.0, 0.5) and rep < ROT_DATASETS:
                # rotate the day-level signal (traded, dir, t0) within year; score against the day's own returns
                rts = []
                for _ in range(ROT_DRAWS):
                    tr_r, dr_r, t0_r = traded.copy(), dirs.copy(), t0_idx.copy()
                    for idx in yidx:
                        if len(idx) > 2 * ROT_MIN:
                            k = int(rng.integers(ROT_MIN, len(idx) - ROT_MIN + 1))
                            tr_r[idx], dr_r[idx], t0_r[idx] = (np.roll(traded[idx], k), np.roll(dirs[idx], k),
                                                               np.roll(t0_idx[idx], k))
                    base = G[np.arange(n), t0_r]
                    rts.append(tstat((dr_r * base)[tr_r]))
                rot.append((ts[-1], float(np.quantile(rts, 0.95))))
        ta, na = np.array(ts), np.array(nets)
        r: dict[str, Any] = {"reps": len(ta), "power_t_holm": float(np.mean(ta >= T_HOLM)),
             "power_t_holm_and_net_positive": float(np.mean((ta >= T_HOLM) & (na > 0))),
             "t_median": float(np.median(ta)), "net_mean_median_usd": float(np.median(na)),
             "vault_pass_rate": float(np.mean(vault_pass))}
        if rot:
            ra = np.array(rot)
            r["rotation"] = {"datasets": len(ra), "draws": ROT_DRAWS,
                             "beats_own_p95": float(np.mean(ra[:, 0] > ra[:, 1])),
                             "combined_gate": float(np.mean((ra[:, 0] >= T_HOLM) & (ra[:, 0] > ra[:, 1]))),
                             "p95_median": float(np.median(ra[:, 1]))}
        if beta == 0:
            r["null_t_p95"] = float(np.quantile(ta, 0.95))
            r["size_two_sided_holm"] = float(np.mean(np.abs(ta) >= T_HOLM))
        res[f"{beta:g}"] = r
    return res


def build() -> dict[str, Any]:
    rng = np.random.default_rng(SEED)
    ps = presample()
    d = design()
    sim = simulate(d, ps["_U"], rng)
    sd_trade = d.loc[d["traded"] == 1, [f"sd_{t}" for t in T0]].to_numpy().mean(axis=1) * \
        d.loc[d["traded"] == 1, "p_held"].to_numpy() * MULT
    se_mean = float(np.sqrt(np.sum(sd_trade ** 2)) / len(sd_trade))
    return {"pre_sample": {k: v for k, v in ps.items() if not k.startswith("_")}, "seed": SEED, "betas": BETAS,
            "t_holm": T_HOLM, "t_vault_one_sided_p10": T_VAULT, "cost_usd_rt_plus_slip": RT_USD + SLIP_USD,
            "analytic": {"se_of_mean_usd": se_mean, "mde_t_holm_usd": T_HOLM * se_mean,
                         "mde_80pct_usd": (T_HOLM + 0.8416) * se_mean,
                         "plausible_effect_usd": RT_USD + SLIP_USD,
                         "underpowered": bool(T_HOLM * se_mean > RT_USD + SLIP_USD)},
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
            raise H2PowerError(f"{OUT_JSON.name} does not reproduce")
        print(f"[check] {OUT_JSON.name} reproduces byte for byte")
        return 0
    OUT_JSON.write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps({k: out[k] for k in ("pre_sample", "analytic")}, indent=1, default=str))
    for b in BETAS:
        print(b, out["sim"][f"{b:g}"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
