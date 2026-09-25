"""POWER for Stage A's H1a (settlement ledger A8; deposit §9A.2 rule 1 and §9B's parameter recovery). It must be
written before the H1a runner exists.

It reads NO outcome. H1a's dependent, the window volume `vol_win` of the in-sample 2017-05-22 → 2025-02-28, is never
loaded, and a guard raises if it is. The noise comes from before the sample (the principal, 2026-09-25):

PRE-SAMPLE NOISE, 2011-01-03 → 2017-05-19, from the 1-minute fixture's front contract (`fut_day1m`):
  * win_t = the 14:28 and 14:29 bars' volume; pre_t = 13:30 → 14:28 (bars 270–327). D624/this study showed the 1-s
    window equals these bars exactly;
  * z_t = (win_t − mean over t-20..t-1) / that mean, the abnormal window volume as a fraction of its norm;
  * z is residualised on the pre-sample analogues of H1a's two continuous controls:
      - z_pre, the pre-window's own abnormal fraction;
      - |the front's return from the previous day's 14:29 bar close to today's 14:27 bar close|.
    The residual is the primary noise; raw z is the conservative variant;
  * k = mean(win) / mean(pre), used to scale the in-sample expected window volume from the held contracts' pre-window
    volume (a control, not the dependent).

IN-SAMPLE PREDICTOR SIDE, per root (`data/ledger_predicted_flow_daily.csv.gz`, `data/ledger_window_volume_daily.csv.gz`
WITHOUT vol_win, and `data/ledger_calendar_flags.csv`):
  * |Q_rem| = |q_est| at τ*, on days where τ* is defined;
  * the controls:
      - |r| to 14:28 (the held return at τ = 14:28);
      - the held contracts' abnormal pre-window volume, pre_t minus its mean over t-20..t-1 on the same contracts;
      - flags: index_roll_close, fund_roll, expiry and eia_report; for CL also index_annual_roll and index_reset;
        for NG also ng_spot_last3;
  * excluded: A1's CL transition (2020-04-01 → 2020-09-16), and days without τ* (the warm-up, and 2020-02-28's stale
    legs).

SIMULATION (parameter recovery, §9B):
  * A_sim = β |Q| + e, with e_t = expected_win_t × z*_t, where z* is a moving-block bootstrap of the pre-sample
    residual (block 10 days, which keeps its autocorrelation) and expected_win_t = k × the held contracts' trailing
    pre-window volume;
  * β ∈ {0, 0.05, 0.1, 0.25, 0.5, 1}, 200 datasets each, seed 20260925;
  * each dataset: OLS of A_sim on 1, |Q| and the controls. Recorded: the HC1 t (A8's day-clustered t: one row per
    day), the Newey-West t (5 lags, reported beside it, the principal 2026-09-25), β̂, and the partial correlation
    t / sqrt(t² + df);
  * power = the share with HC1 t ≥ 2 (and β̂ > 0). Recovery: the share with |β̂ − β| ≤ 0.15 (§9B's ±0.15 / 80% rule,
    applied to β);
  * β = 0 is the size check, on 1,000 datasets. Its HC1 and Newey-West size, and the null's p95 of t, are reported.
    On 5 of those null datasets, A8's day shuffle is also run (|Q| permuted within year, 200 times): if the true null's
    p95 exceeds the shuffle's, the shuffle is anti-conservative here. A Newey-West size above 10% raises. (The first
    version raised on an HC1 size above 5%. It fired at 5.5%, and that finding is now measured instead.)
  * A9's replacement for the day shuffle (the principal, 2026-09-25) is calibrated here. |Q| is residualised on the
    controls, the residual is rotated circularly within instrument-year (offsets ≥ 20 days), and it is added back to
    its fitted part. On 100 datasets at β = 0 and at β = 0.25, each dataset's HC1 t is compared with its own
    100-rotation p95. Reported: the share beating it (the size, at β = 0) and the combined gate (t ≥ 2 AND beating
    the rotation's p95);
  * THE PRE-SAMPLE is ~485 days per root, 2015-07 → 2017-05-19: the fixture's day session is `present` on no day in
    2011–14.
  * NOT simulated: the day shuffle (1,000 permutations inside each dataset is out of scale for a power study) and A4's
    imputation. The imputation widens CL's bars, so CL's power is an upper bound.

PLAUSIBLE EFFECT (§9A.2 rule 2), stated here before any run: β = 0.25, i.e. a quarter of the predicted rebalance lands
as extra window volume. In correlation units it is the median partial correlation at β = 0.25, which is what
`power_row` takes. The principal may revise it before the pre-registration is committed.

Output: `docs/internal/SETTLEMENT_FLOW_LEDGER_POWER.md` (through `validation.power.write_power_md`) and
`data/ledger_power_h1a.json`. The deposit names `results/settlement_flow/POWER.md`, but no `results/` tree exists, so
it sits beside the amendments.

    python scripts/ledger_power_h1a.py --extract           # SYSTEM interpreter (pyarrow): the pre-sample file
    uv run python scripts/ledger_power_h1a.py [--check]    # the venv (statsmodels): the simulation and POWER.md
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
PANEL = REPO / "data" / "ledger_window_volume_daily.csv.gz"
CAL = REPO / "data" / "ledger_calendar_flags.csv"
DAY1M = REPO / "data" / "fixtures" / "fut_day1m.parquet"
PRESAMPLE = REPO / "data" / "ledger_power_presample.csv.gz"  # gitignored; `--extract` (system python) rebuilds it
OUT_MD = REPO / "docs" / "internal" / "SETTLEMENT_FLOW_LEDGER_POWER.md"
OUT_JSON = REPO / "data" / "ledger_power_h1a.json"
PRE = ("2011-01-03", "2017-05-19")
CUT = "2025-03-01"
TRANSITION = ("2020-04-01", "2020-09-16")
N_TRAIL, BLOCK, REPS, SEED = 20, 10, 200, 20260925
REPS0 = 1000  # null datasets: the size and the null's p95 need more than 200
SHUFFLE_DATASETS, SHUFFLE_PERMS = 5, 200
ROT_DATASETS, ROT_DRAWS, ROT_MIN_OFFSET = 100, 100, 20  # the amended control's calibration
ABSQ_COL = 1  # |Q| is the first column after the constant
BETAS = (0.0, 0.05, 0.1, 0.25, 0.5, 1.0)
PLAUSIBLE_BETA = 0.25
FLAGS = {"CL": ["index_roll_close", "fund_roll", "expiry", "eia_report", "index_annual_roll", "index_reset"],
         "NG": ["index_roll_close", "fund_roll", "expiry", "eia_report", "ng_spot_last3"]}


class PowerError(RuntimeError):
    pass


# ------------------------------------------------------------------ pre-sample noise
def extract() -> None:
    """SYSTEM interpreter (pyarrow): the pre-sample's per-day front-contract window, pre-window and closes."""
    import pyarrow.parquet as pq  # type: ignore[import-not-found]
    parts = []
    for root in ("CL", "NG"):
        t = pq.read_table(DAY1M, columns=["root", "day", "bar", "volume", "close", "present"],
                          filters=[("root", "==", root), ("day", ">=", PRE[0]), ("day", "<=", PRE[1]),
                                   ("bar", ">=", 270), ("bar", "<=", 329)]).to_pandas()
        t["day"] = t["day"].astype(str).str[:10]
        if (t["day"] > PRE[1]).any():
            raise PowerError("a pre-sample row after 2017-05-19 is in memory")
        t = t[t["present"].astype(bool)]
        days = sorted(t["day"].unique())
        df = pd.DataFrame(index=pd.Index(days, name="day"))
        df["win"] = t[t["bar"].isin([328, 329])].groupby("day")["volume"].sum().reindex(days).fillna(0.0)
        df["pre"] = t[(t["bar"] >= 270) & (t["bar"] <= 327)].groupby("day")["volume"].sum().reindex(days).fillna(0.0)
        df["c27"] = t[t["bar"] == 327].set_index("day")["close"].reindex(days)
        df["c29"] = t[t["bar"] == 329].set_index("day")["close"].reindex(days)
        parts.append(df.reset_index().assign(root=root))
    out = pd.concat(parts)[["root", "day", "win", "pre", "c27", "c29"]]
    out.to_csv(PRESAMPLE, index=False, encoding="utf-8", lineterminator="\n", compression={"method": "gzip", "mtime": 0})
    print(f"wrote {PRESAMPLE.name}: {len(out)} rows")


def presample(root: str) -> dict[str, Any]:
    import statsmodels.api as sm  # type: ignore[import-untyped]
    t = pd.read_csv(PRESAMPLE, encoding="utf-8")
    t = t[t["root"] == root].set_index("day")
    if (t.index > PRE[1]).any():
        raise PowerError("a pre-sample row after 2017-05-19 is in memory")
    days = list(t.index)
    df = t[["win", "pre"]].copy()
    c27, c29 = t["c27"], t["c29"]
    tw = df["win"].rolling(N_TRAIL, min_periods=N_TRAIL).mean().shift(1)
    tp = df["pre"].rolling(N_TRAIL, min_periods=N_TRAIL).mean().shift(1)
    df["z"] = (df["win"] - tw) / tw
    df["z_pre"] = (df["pre"] - tp) / tp
    df["absret"] = (c27.reindex(days) / c29.reindex(days).shift(1) - 1.0).abs()
    df = df.dropna()
    X = sm.add_constant(df[["z_pre", "absret"]])
    fit = sm.OLS(df["z"], X).fit()
    resid = fit.resid.to_numpy()
    raw = (df["z"] - df["z"].mean()).to_numpy()
    k = float(df["win"].mean() / df["pre"].mean())
    return {"days": len(df), "first": df.index[0], "last": df.index[-1], "k_win_over_pre": k,
            "sd_z_raw": float(raw.std(ddof=1)), "sd_z_resid": float(resid.std(ddof=1)),
            "r2_controls": float(fit.rsquared), "ac1_resid": float(pd.Series(resid).autocorr(1)),
            "_resid": resid, "_raw": raw}


# ------------------------------------------------------------------ in-sample predictor side
def design(root: str) -> pd.DataFrame:
    f = pd.read_csv(FLOW, encoding="utf-8")
    f = f[f["root"] == root]
    if (f["day"] >= CUT).any():
        raise PowerError("a flow row on or after the cut is in memory")
    star = f[f["is_tau_star"] == 1][["day", "tau", "q_est", "held", "signal_day"]]
    r28 = f[f["tau"] == "14:28"].set_index("day")["r_held"]
    cols = ["root", "kind", "day", "ym", "vol_pre"]
    p = pd.read_csv(PANEL, encoding="utf-8", usecols=cols)
    if "vol_win" in p.columns:
        raise PowerError("the dependent was loaded")
    p = p[(p["root"] == root) & (p["kind"] == "outright")]
    cal = pd.read_csv(CAL, encoding="utf-8")
    cal = cal[cal["root"] == root].set_index("date")
    bdays = list(cal.index)
    vp = p.pivot_table(index="day", columns="ym", values="vol_pre", aggfunc="sum").reindex(bdays).fillna(0.0)
    trail = vp.rolling(N_TRAIL, min_periods=N_TRAIL).mean().shift(1)
    d = star.copy()
    pre_now, pre_trail = [], []
    for day, h in zip(d["day"], d["held"]):
        keys = h.split(";")
        pre_now.append(float(vp.loc[day].reindex(keys, fill_value=0.0).sum()))
        tr = trail.loc[day].reindex(keys, fill_value=0.0)
        pre_trail.append(float(tr.sum()) if tr.notna().all() else np.nan)
    d["pre_trail"] = pre_trail
    d["pre_abn"] = np.array(pre_now) - d["pre_trail"]
    d["absQ"] = d["q_est"].abs()
    d["absr"] = r28.reindex(d["day"]).abs().to_numpy()
    for fl in FLAGS[root]:
        d[fl] = cal.loc[d["day"], fl].to_numpy()
    if root == "CL":
        d = d[~d["day"].between(*TRANSITION)]
    return d.dropna(subset=["pre_trail", "absr"]).reset_index(drop=True)


# ------------------------------------------------------------------ simulation
def hc1_t(X: np.ndarray, y: np.ndarray, j: int) -> float:
    """The HC1 t of coefficient j (statsmodels' cov_type="HC1"; checked against it in `selfcheck`)."""
    xtx_inv = np.linalg.inv(X.T @ X)
    b = xtx_inv @ (X.T @ y)
    e = y - X @ b
    n, k = X.shape
    meat = (X * (e * e)[:, None]).T @ X
    cov = xtx_inv @ meat @ xtx_inv * n / (n - k)
    return float(b[j] / np.sqrt(cov[j, j]))


def rotation_p95(y: np.ndarray, Xn: np.ndarray, fitted_q: np.ndarray, resid_q: np.ndarray,
                 year_idx: list[np.ndarray], rng: np.random.Generator) -> float:
    """The amended A8 control (the principal, 2026-09-25): |Q|'s residual on the controls, circularly rotated within
    each instrument-year by an independent offset in [ROT_MIN_OFFSET, len - ROT_MIN_OFFSET], added back to its fitted
    part. The p95 of the HC1 t over ROT_DRAWS rotations. The rotation keeps |Q|'s autocorrelation; the fitted part
    stays in place so the control-explained share of |Q| is not rotated against the controls."""
    ts = []
    Xr = Xn.copy()
    for _ in range(ROT_DRAWS):
        rq = resid_q.copy()
        for idx in year_idx:
            if len(idx) > 2 * ROT_MIN_OFFSET:
                rq[idx] = np.roll(resid_q[idx], int(rng.integers(ROT_MIN_OFFSET, len(idx) - ROT_MIN_OFFSET + 1)))
        Xr[:, ABSQ_COL] = fitted_q + rq
        ts.append(hc1_t(Xr, y, ABSQ_COL))
    return float(np.quantile(ts, 0.95))


def _block(noise: np.ndarray, n: int, rng: np.random.Generator) -> np.ndarray:
    out = np.empty(n)
    i = 0
    while i < n:
        s = int(rng.integers(0, len(noise) - BLOCK))
        take = min(BLOCK, n - i)
        out[i:i + take] = noise[s:s + take]
        i += take
    return out


def simulate(root: str, d: pd.DataFrame, noise: np.ndarray, k: float, rng: np.random.Generator) -> dict[str, Any]:
    import statsmodels.api as sm  # type: ignore[import-untyped]
    X = sm.add_constant(d[["absQ", "absr", "pre_abn"] + FLAGS[root]].astype(float))
    expected = k * d["pre_trail"].to_numpy()
    absq = d["absQ"].to_numpy()
    df_resid = len(d) - X.shape[1]
    res: dict[str, Any] = {}
    years = d["day"].str[:4].to_numpy()
    # residualise |Q| on the controls once; the rotation null rolls the residual within instrument-year
    Xn = X.to_numpy()
    j = list(X.columns).index("absQ")
    if j != ABSQ_COL:
        raise PowerError(f"|Q| is column {j}, not {ABSQ_COL}")
    Z = np.delete(Xn, j, axis=1)
    coef, *_ = np.linalg.lstsq(Z, absq, rcond=None)
    fitted_q = Z @ coef
    resid_q = absq - fitted_q
    year_idx = [np.flatnonzero(years == yv) for yv in np.unique(years)]
    for beta in BETAS:
        t1, tnw, bh, pr = [], [], [], []
        shuffle_p95: list[float] = []
        rot: list[tuple[float, float, float]] = []
        res_rot: dict[str, Any] | None = None
        for rep in range(REPS0 if beta == 0 else REPS):
            y = beta * absq + expected * _block(noise, len(d), rng)
            m = sm.OLS(y, X).fit(cov_type="HC1")
            t = float(m.tvalues["absQ"])
            if rep == 0 and not np.isclose(hc1_t(Xn, y, j), t, rtol=1e-9, atol=0):
                raise PowerError(f"hc1_t {hc1_t(Xn, y, j)!r} != statsmodels HC1 {t!r}")
            t1.append(t)
            bh.append(float(m.params["absQ"]))
            pr.append(t / np.sqrt(t * t + df_resid))
            tnw.append(float(sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 5}).tvalues["absQ"]))
            if beta == 0 and rep < SHUFFLE_DATASETS:
                # A8's day shuffle on this null dataset: |Q| permuted within year, the HC1 t each time
                ts = []
                Xs = X.copy()
                for _ in range(SHUFFLE_PERMS):
                    perm = absq.copy()
                    for yv in np.unique(years):
                        idx = np.flatnonzero(years == yv)
                        perm[idx] = perm[rng.permutation(idx)]
                    Xs["absQ"] = perm
                    ts.append(float(sm.OLS(y, Xs).fit(cov_type="HC1").tvalues["absQ"]))
                shuffle_p95.append(float(np.quantile(ts, 0.95)))
            if beta in (0.0, PLAUSIBLE_BETA) and rep < ROT_DATASETS:
                p95 = rotation_p95(y, Xn, fitted_q, resid_q, year_idx, rng)
                rot.append((t, p95, float(m.params["absQ"])))
        t1a, tnwa, bha = np.array(t1), np.array(tnw), np.array(bh)
        if rot:
            ra = np.array(rot)
            res_rot = {"datasets": len(ra), "draws": ROT_DRAWS, "min_offset": ROT_MIN_OFFSET,
                       "beats_own_rotation_p95": float(np.mean(ra[:, 0] > ra[:, 1])),
                       "combined_gate": float(np.mean((ra[:, 0] >= 2) & (ra[:, 0] > ra[:, 1]) & (ra[:, 2] > 0))),
                       "rotation_p95_median": float(np.median(ra[:, 1]))}
        res[f"{beta:g}"] = {
            "reps": len(t1a),
            "power_hc1": float(np.mean((t1a >= 2) & (bha > 0))), "power_nw5": float(np.mean((tnwa >= 2) & (bha > 0))),
            "beta_hat_mean": float(bha.mean()), "beta_hat_sd": float(bha.std(ddof=1)),
            "recovery_within_0.15": float(np.mean(np.abs(bha - beta) <= 0.15)),
            "partial_r_median": float(np.median(pr)), "t_hc1_median": float(np.median(t1a))}
        if res_rot is not None:
            res[f"{beta:g}"]["rotation_null"] = res_rot
        if beta == 0:
            res["0"]["null_t_hc1_p95"] = float(np.quantile(t1a, 0.95))
            res["0"]["null_t_nw5_p95"] = float(np.quantile(tnwa, 0.95))
            res["0"]["day_shuffle_p95_mean"] = float(np.mean(shuffle_p95))
            res["0"]["day_shuffle_datasets"] = SHUFFLE_DATASETS
            # the share of null datasets whose observed t beats the shuffle's p95 (A8's control), estimated with the
            # mean shuffle p95: above 5% means the shuffle is anti-conservative here
            res["0"]["null_beats_mean_shuffle_p95"] = float(np.mean(t1a > np.mean(shuffle_p95)))
    if res["0"]["power_nw5"] > 0.10:
        raise PowerError(f"{root}: Newey-West size {res['0']['power_nw5']:.3f} > 10% at beta = 0")
    return res


def build() -> tuple[dict[str, Any], list[Any]]:
    from backtest_framework.validation.power import power_row
    rng = np.random.default_rng(SEED)
    out: dict[str, Any] = {"pre_sample": PRE, "betas": BETAS, "reps": REPS, "seed": SEED, "block": BLOCK,
                           "plausible_beta": PLAUSIBLE_BETA, "roots": {}}
    rows = []
    for root in ("CL", "NG"):
        ps = presample(root)
        d = design(root)
        sims = {v: simulate(root, d, ps[f"_{v}"], ps["k_win_over_pre"], rng) for v in ("resid", "raw")}
        plaus = sims["resid"][f"{PLAUSIBLE_BETA:g}"]["partial_r_median"]
        n = len(d)
        out["roots"][root] = {"pre_sample": {k: v for k, v in ps.items() if not k.startswith("_")},
                              "n_days": n, "signal_days": int((d["signal_day"] == 1).sum()),
                              "first": d["day"].iloc[0], "last": d["day"].iloc[-1],
                              "absQ_median": float(d["absQ"].median()), "sim": sims}
        rows.append(power_row(stage="A: P1 rebalance (H1a)", test=f"{root}: abs(Q_rem) vs abnormal window volume",
                              n=n, m=1.0, rho=0.0, track="Track 1", plausible_effect=round(plaus, 4),
                              note=f"one row per day; pre-sample residual AC(1) {ps['ac1_resid']:.3f}; "
                                   f"sim power at beta {PLAUSIBLE_BETA}: HC1 "
                                   f"{sims['resid'][f'{PLAUSIBLE_BETA:g}']['power_hc1']:.2f}, "
                                   f"NW5 {sims['resid'][f'{PLAUSIBLE_BETA:g}']['power_nw5']:.2f}"))
    return out, rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--extract", action="store_true", help="system interpreter: write the pre-sample file")
    a = ap.parse_args(argv)
    if a.extract:
        extract()
        return 0
    from backtest_framework.validation.power import write_power_md
    out, rows = build()
    text = json.dumps(out, indent=1, sort_keys=True, default=str) + "\n"
    if a.check:
        if OUT_JSON.read_text(encoding="utf-8") != text:
            raise PowerError(f"{OUT_JSON.name} does not reproduce")
        print(f"[check] {OUT_JSON.name} reproduces byte for byte")
        return 0
    OUT_JSON.write_text(text, encoding="utf-8", newline="\n")
    write_power_md(rows, OUT_MD, title="POWER: settlement flow ledger, Stage A (H1a)", date="2026-09-25")
    for root, v in out["roots"].items():
        print(root, "n", v["n_days"], "pre", {k: round(x, 4) if isinstance(x, float) else x
                                             for k, x in v["pre_sample"].items()})
        for var in ("resid", "raw"):
            for b, s in v["sim"][var].items():
                print(f"  {var:5s} beta {b:5s} powerHC1 {s['power_hc1']:.3f} powerNW {s['power_nw5']:.3f} "
                      f"bhat {s['beta_hat_mean']:.3f}±{s['beta_hat_sd']:.3f} rec {s['recovery_within_0.15']:.2f} "
                      f"pr {s['partial_r_median']:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
