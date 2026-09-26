"""POWER for the signed H1 (settlement ledger, deposit §9 H1 on Sierra Chart's aggressor-signed flow; AITODO
2026-09-26). Written before the pre-registration and its runner.

It reads NO outcome: no in-sample signed flow. The in-sample rows of `ledger_signed_window_daily.csv.gz` are dropped
on load and a guard raises if one survives. The noise comes from before the sample.

THE DEPENDENT, as the runner will build it (one row per day t, per root):
    S_t = Σ_{h in C_t} net_win(h, t) − mean over k = 1..20 of Σ_{h in C_t} net_win(h, t−k)
  * net_win = Sierra's AskVolume − BidVolume, 14:28:00–14:30:00 ET (+ = buyers);
  * C_t = the COVERED held contracts: held on t (share > 0) AND with a Sierra file whose first record is dated
    before business day t−20, so the trailing norm lies inside the file. The principal (2026-09-26): score only the
    covered contracts. A covered contract with no row on a day traded 0.
THE PREDICTOR: Q_t = q_est at τ* × Σ_{h in C_t} units_share(h) at τ*, the P1 rebalance in the covered contracts only
(Q is linear in the contract split, `build_predicted_flow_panel`). Signed: both funds buy when r > 0.
THE CONTROLS (primary): r_t, the signed held return to 14:28; the calendar flags (D627's sets).

PRE-SAMPLE NOISE, 2015-07-01 → 2017-05-19, from Sierra Chart files of the BCOM lead/next contracts held then
(`gate_0b_cl_nav.era_a_contracts`, `gate_0b_ng_nav.contracts_for`, weights by S0 on the business day):
  * z_t = S_t / V_t, with V_t = the trailing 20-day mean of Σ_{h in C_t} v_win (window volume): signed abnormal flow
    as a fraction of the window's normal volume;
  * residualised on the signed front return from the prior day's 14:29 close to today's 14:27 close (the 1-minute
    fixture's front, `ledger_power_presample.csv.gz`), the primary design's continuous control. Raw z is the
    conservative variant;
  * its mean is reported with its t (lesson of D627: an "abnormal" dependent must be checked for drift on data built
    exactly as the runner builds it).

SIMULATION (as `ledger_power_h1a.py`, adapted): y = β Q_t + V_t × z*_t, where z* is a moving-block bootstrap (10
days) of the pre-sample noise and V_t is the in-sample trailing window volume over C_t from Databento's `vol_win`
(unsigned, read by D627; not this study's outcome). β ∈ {0, 0.05, 0.1, 0.25, 0.5, 1}; 200 datasets each (1,000 at
β = 0); OLS of y on 1, Q, r and the flags; HC1 t and Newey-West (5 lags). Power = share with t ≥ 2 and β̂ > 0.
The rotation control (A9.4: Q residualised on the controls, rolled within year, offsets ≥ 20) is calibrated on 100
datasets at β = 0 and at the plausible β. CL's A4 imputation is not simulated: CL's power is an upper bound.

PLAUSIBLE EFFECT, stated before any run: β = 0.25, A9.5's quarter of the predicted rebalance, here arriving as net
aggressor flow in the window (e.g. TAS counterparties hedging the funds' settlement-priced trades).

Output: `data/ledger_power_signed_h1.json`, and `docs/internal/SETTLEMENT_FLOW_LEDGER_POWER_SIGNED.md`.

    uv run python scripts/ledger_power_signed_h1.py [--check]
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
sys.path.insert(0, str(REPO / "scripts"))
import ledger_power_h1a as P  # noqa: E402  (constants and the HC1 / rotation helpers; its body is definitions only)

FLOW = REPO / "data" / "ledger_predicted_flow_daily.csv.gz"
CONTRACTS = REPO / "data" / "ledger_predicted_flow_contracts.csv.gz"
PANEL = REPO / "data" / "ledger_window_volume_daily.csv.gz"
SIGNED = REPO / "data" / "ledger_signed_window_daily.csv.gz"
SIGNED_SUM = REPO / "data" / "ledger_signed_window_summary.json"
CAL = REPO / "data" / "ledger_calendar_flags.csv"
PRESAMPLE_FIX = REPO / "data" / "ledger_power_presample.csv.gz"
OUT_JSON = REPO / "data" / "ledger_power_signed_h1.json"
OUT_MD = REPO / "docs" / "internal" / "SETTLEMENT_FLOW_LEDGER_POWER_SIGNED.md"
PRE = ("2015-07-01", "2017-05-19")
FIRST_IN, CUT = "2017-05-22", "2025-03-01"
TRANSITION = ("2020-04-01", "2020-09-16")
N_TRAIL, BLOCK, REPS, REPS0, SEED = 20, 10, 200, 1000, 20260926
ROT_DATASETS, ROT_DRAWS, ROT_MIN_OFFSET = 100, 100, 20
Q_COL = 1
BETAS = (0.0, 0.05, 0.1, 0.25, 0.5, 1.0)
PLAUSIBLE_BETA = 0.25
FLAGS = P.FLAGS
LETTER = "FGHJKMNQUVXZ"


class SignedPowerError(RuntimeError):
    pass


# ------------------------------------------------------------------ shared with the runner
def business_days(root: str) -> list[str]:
    """NYMEX business days: the 1-minute fixture's pre-sample days before 2017-05-22, then the ledger calendar."""
    pre = pd.read_csv(PRESAMPLE_FIX, encoding="utf-8", usecols=["root", "day"])
    cal = pd.read_csv(CAL, encoding="utf-8", usecols=["root", "date"])
    a = sorted(pre.loc[(pre["root"] == root) & (pre["day"] < FIRST_IN), "day"])
    b = sorted(cal.loc[cal["root"] == root, "date"])
    if a and b and not a[-1] < b[0]:
        raise SignedPowerError(f"{root}: the day lists overlap")
    return a + b


def first_days() -> dict[str, str]:
    """symbol-month key 'CL:2021-12' -> the ET date of its Sierra file's first decoded record."""
    s = json.loads(SIGNED_SUM.read_text(encoding="utf-8"))
    out = {}
    for sym, m in s["files"].items():
        if "first_et" in m:
            out[f"{sym[:2]}:20{sym[3:5]}-{LETTER.index(sym[2]) + 1:02d}"] = m["first_et"][:10]
    return out


def signed_pivots(root: str, sample: str, days: list[str]) -> dict[str, pd.DataFrame]:
    """day x ym tables of the signed panel, reindexed to the business days with 0 where a contract has no row.
    `sample` 'pre' drops every in-sample row on load (the power study reads no outcome)."""
    d = pd.read_csv(SIGNED, encoding="utf-8")
    d = d[d["root"] == root]
    if sample == "pre":
        d = d[d["day"] < FIRST_IN]
        if (d["day"] >= FIRST_IN).any():
            raise SignedPowerError("an in-sample signed row is in memory")
    elif (d["day"] >= CUT).any():
        raise SignedPowerError("a signed row on or after the cut is in memory")
    out = {}
    for col in [c for c in d.columns if c.split("_")[0] in ("v", "net", "sided", "n")]:
        out[col] = d.pivot_table(index="day", columns="ym", values=col, aggfunc="sum").reindex(days).fillna(0.0)
    return out


def abnormal(tab: pd.DataFrame, days: list[str], i: int, yms: list[str]) -> tuple[float, float]:
    """(value on day i, mean over i-20..i-1) of the sum over `yms`."""
    cols = tab.reindex(columns=yms, fill_value=0.0)
    now = float(cols.iloc[i].sum())
    trail = float(cols.iloc[i - N_TRAIL:i].sum(axis=1).mean())
    return now, trail


def covered(root: str, ym: str, i: int, days: list[str], first: dict[str, str]) -> bool:
    f = first.get(f"{root}:{ym}")
    return f is not None and i >= N_TRAIL and f < days[i - N_TRAIL]


# ------------------------------------------------------------------ pre-sample noise
def presample_holdings(root: str, days: list[str]) -> dict[str, list[str]]:
    import gate_0b_cl_nav as GCL
    import gate_0b_ng_nav as G
    out: dict[str, list[str]] = {}
    cnt: dict[str, int] = {}
    for d in days:
        cnt[d[:7]] = cnt.get(d[:7], 0) + 1
        if d < PRE[0] or d > PRE[1]:
            continue
        lead, nxt = GCL.era_a_contracts(d) if root == "CL" else G.contracts_for(d)
        b = G.s0(cnt[d[:7]])
        legs = [lead] if b == 0 else [nxt] if b == 1 else [lead, nxt]
        out[d] = [f"{y:04d}-{m:02d}" for y, m in legs]
    return out


def presample(root: str) -> dict[str, Any]:
    import statsmodels.api as sm  # type: ignore[import-untyped]
    days = [d for d in business_days(root) if d < FIRST_IN]
    first = first_days()
    piv = signed_pivots(root, "pre", days)
    hold = presample_holdings(root, days)
    fix = pd.read_csv(PRESAMPLE_FIX, encoding="utf-8")
    fix = fix[fix["root"] == root].set_index("day")
    ret = (fix["c27"] / fix["c29"].shift(1) - 1.0)
    rows = []
    for i, d in enumerate(days):
        if d not in hold:
            continue
        c = [ym for ym in hold[d] if covered(root, ym, i, days, first)]
        if len(c) < len(hold[d]):
            continue  # the pre-sample noise uses fully covered days only
        now, trail = abnormal(piv["net_win"], days, i, c)
        _v, vtrail = abnormal(piv["v_win"], days, i, c)
        rows.append({"day": d, "S": now - trail, "V": vtrail, "r": float(ret.get(d, np.nan))})
    df = pd.DataFrame(rows).dropna()
    df = df[df["V"] > 0]
    df["z"] = df["S"] / df["V"]
    fit = sm.OLS(df["z"], sm.add_constant(df[["r"]])).fit()
    resid = fit.resid.to_numpy()
    raw = (df["z"] - df["z"].mean()).to_numpy()
    z = df["z"].to_numpy()
    return {"days": int(len(df)), "first": df["day"].iloc[0], "last": df["day"].iloc[-1],
            "z_mean": float(z.mean()), "z_mean_t": float(z.mean() / (z.std(ddof=1) / np.sqrt(len(z)))),
            "z_share_positive": float((z > 0).mean()),
            "sd_z_raw": float(raw.std(ddof=1)), "sd_z_resid": float(resid.std(ddof=1)),
            "slope_z_on_r": float(fit.params["r"]), "t_z_on_r": float(fit.tvalues["r"]),
            "r2_controls": float(fit.rsquared), "ac1_resid": float(pd.Series(resid).autocorr(1)),
            "_resid": resid, "_raw": raw}


# ------------------------------------------------------------------ in-sample predictor side
def design(root: str, tau: str | None = None) -> pd.DataFrame:
    """One row per in-sample day: Q over the covered contracts at τ* (or at a fixed `tau`), r to 14:28 (or to
    `tau` for the placebo's 11:30), the flags, V_t from Databento's unsigned window volume, and the covered set."""
    f = pd.read_csv(FLOW, encoding="utf-8")
    f = f[f["root"] == root]
    if (f["day"] >= CUT).any():
        raise SignedPowerError("a flow row on or after the cut is in memory")
    star = f[f["is_tau_star"] == 1] if tau is None else f[f["tau"] == tau]
    star = star[["day", "tau", "q_est", "q1_long", "q1_inverse", "f_est_long", "f_est_inverse", "signal_day"]]
    rcol = f[f["tau"] == ("14:28" if tau is None else tau)].set_index("day")["r_held"]
    con = pd.read_csv(CONTRACTS, encoding="utf-8")
    con = con[con["root"] == root].set_index(["day", "tau"])
    days = business_days(root)
    pos = {d: i for i, d in enumerate(days)}
    first = first_days()
    vw = pd.read_csv(PANEL, encoding="utf-8", usecols=["root", "kind", "day", "ym", "vol_win"])
    vw = vw[(vw["root"] == root) & (vw["kind"] == "outright")]
    vwp = vw.pivot_table(index="day", columns="ym", values="vol_win", aggfunc="sum").reindex(days).fillna(0.0)
    cal = pd.read_csv(CAL, encoding="utf-8")
    cal = cal[cal["root"] == root].set_index("date")
    rows = []
    for _, s in star.iterrows():
        d, t = s["day"], s["tau"]
        i = pos[d]
        legs = con.loc[(d, t)]
        held = list(zip(legs["ym"], legs["units_share"]))
        cov = [(ym, sh) for ym, sh in held if sh > 0 and covered(root, ym, i, days, first)]
        if not cov:
            continue
        share = float(sum(sh for _ym, sh in cov))
        _v, vtrail = abnormal(vwp, days, i, [ym for ym, _sh in cov])
        rows.append({"day": d, "tau": t, "Q": float(s["q_est"]) * share, "share_cov": share,
                     "q_est": float(s["q_est"]), "q1_long": float(s["q1_long"]), "q1_inverse": float(s["q1_inverse"]),
                     "f_est_long": float(s["f_est_long"]), "f_est_inverse": float(s["f_est_inverse"]),
                     "covered": ";".join(ym for ym, _sh in cov), "held": ";".join(ym for ym, _sh in held),
                     "V": vtrail, "r": float(rcol.get(d, np.nan)), "signal_day": int(s["signal_day"])})
    out = pd.DataFrame(rows)
    for fl in FLAGS[root]:
        out[fl] = cal.loc[out["day"], fl].to_numpy()
    if root == "CL":
        out = out[~out["day"].between(*TRANSITION)]
    return out.dropna(subset=["r", "V"]).reset_index(drop=True)


# ------------------------------------------------------------------ simulation
def nw_t(X: np.ndarray, y: np.ndarray, j: int, lags: int = 5) -> float:
    """Newey-West t (Bartlett, `lags`), without a small-sample correction, as statsmodels' cov_type="HAC" (checked
    against it on the first dataset; a first version applied n/(n-k) and the check fired)."""
    xtx_inv = np.linalg.inv(X.T @ X)
    b = xtx_inv @ (X.T @ y)
    u = X * (y - X @ b)[:, None]
    s = u.T @ u
    for lag in range(1, lags + 1):
        g = u[lag:].T @ u[:-lag]
        s += (1 - lag / (lags + 1)) * (g + g.T)
    cov = xtx_inv @ s @ xtx_inv
    return float(b[j] / np.sqrt(cov[j, j]))


def simulate(root: str, d: pd.DataFrame, noise: np.ndarray, rng: np.random.Generator) -> dict[str, Any]:
    import statsmodels.api as sm  # type: ignore[import-untyped]
    X = sm.add_constant(d[["Q", "r"] + FLAGS[root]].astype(float))
    Xn = X.to_numpy()
    if list(X.columns).index("Q") != Q_COL:
        raise SignedPowerError("Q is not column 1")
    q = d["Q"].to_numpy()
    V = d["V"].to_numpy()
    Z = np.delete(Xn, Q_COL, axis=1)
    coef, *_ = np.linalg.lstsq(Z, q, rcond=None)
    fitted_q, resid_q = Z @ coef, q - Z @ coef
    years = d["day"].str[:4].to_numpy()
    year_idx = [np.flatnonzero(years == yv) for yv in np.unique(years)]
    df_resid = len(d) - Xn.shape[1]
    res: dict[str, Any] = {}
    for beta in BETAS:
        t1, tnw, bh, pr, rot = [], [], [], [], []
        for rep in range(REPS0 if beta == 0 else REPS):
            y = beta * q + V * P._block(noise, len(d), rng)
            t = P.hc1_t(Xn, y, Q_COL)
            tn = nw_t(Xn, y, Q_COL)
            if rep == 0 and beta == 0:
                m = sm.OLS(y, X).fit(cov_type="HC1")
                mn = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
                if not (np.isclose(t, m.tvalues["Q"], rtol=1e-9) and np.isclose(tn, mn.tvalues["Q"], rtol=1e-9)):
                    raise SignedPowerError(f"t {t}/{tn} != statsmodels {m.tvalues['Q']}/{mn.tvalues['Q']}")
            b = float(np.linalg.lstsq(Xn, y, rcond=None)[0][Q_COL])
            t1.append(t)
            tnw.append(tn)
            bh.append(b)
            pr.append(t / np.sqrt(t * t + df_resid))
            if beta in (0.0, PLAUSIBLE_BETA) and rep < ROT_DATASETS:
                rot.append((t, P.rotation_p95(y, Xn, fitted_q, resid_q, year_idx, rng), b))
        t1a, tnwa, bha = np.array(t1), np.array(tnw), np.array(bh)
        r: dict[str, Any] = {"reps": len(t1a), "power_hc1": float(np.mean((t1a >= 2) & (bha > 0))),
                             "power_nw5": float(np.mean((tnwa >= 2) & (bha > 0))),
                             "beta_hat_mean": float(bha.mean()), "beta_hat_sd": float(bha.std(ddof=1)),
                             "partial_r_median": float(np.median(pr)), "t_hc1_median": float(np.median(t1a))}
        if rot:
            ra = np.array(rot)
            r["rotation_null"] = {"datasets": len(ra), "draws": ROT_DRAWS,
                                  "beats_own_rotation_p95": float(np.mean(ra[:, 0] > ra[:, 1])),
                                  "combined_gate": float(np.mean((ra[:, 0] >= 2) & (ra[:, 0] > ra[:, 1])
                                                                 & (ra[:, 2] > 0))),
                                  "rotation_p95_median": float(np.median(ra[:, 1]))}
        if beta == 0:
            r["null_t_hc1_p95"] = float(np.quantile(t1a, 0.95))
            r["null_t_nw5_p95"] = float(np.quantile(tnwa, 0.95))
        res[f"{beta:g}"] = r
    return res


def build() -> tuple[dict[str, Any], list[Any]]:
    from backtest_framework.validation.power import power_row
    rng = np.random.default_rng(SEED)
    out: dict[str, Any] = {"pre_sample": PRE, "betas": BETAS, "reps": REPS, "reps_null": REPS0, "seed": SEED,
                           "block": BLOCK, "plausible_beta": PLAUSIBLE_BETA, "roots": {}}
    rows = []
    for root in ("CL", "NG"):
        ps = presample(root)
        d = design(root)
        sims = {v: simulate(root, d, ps[f"_{v}"], rng) for v in ("resid", "raw")}
        pl = sims["resid"][f"{PLAUSIBLE_BETA:g}"]
        out["roots"][root] = {
            "pre_sample": {k: v for k, v in ps.items() if not k.startswith("_")},
            "n_days": int(len(d)), "signal_days": int((d["signal_day"] == 1).sum()),
            "first": d["day"].iloc[0], "last": d["day"].iloc[-1],
            "share_cov_median": float(d["share_cov"].median()),
            "days_fully_covered": int((d["covered"] == d["held"]).sum()),
            "absQ_median": float(d["Q"].abs().median()), "V_median": float(d["V"].median()), "sim": sims}
        rows.append(power_row(stage="A: P1 rebalance (signed H1)",
                              test=f"{root}: Q_rem (covered contracts) vs abnormal signed window flow",
                              n=len(d), m=1.0, rho=0.0, track="Track 1", plausible_effect=round(pl["partial_r_median"], 4),
                              note=f"one row per day; pre-sample residual AC(1) {ps['ac1_resid']:.3f}; sim power at "
                                   f"beta {PLAUSIBLE_BETA}: HC1 {pl['power_hc1']:.2f}, NW5 {pl['power_nw5']:.2f}"))
    return out, rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    from backtest_framework.validation.power import write_power_md
    out, rows = build()
    text = json.dumps(out, indent=1, sort_keys=True, default=str) + "\n"
    if a.check:
        if OUT_JSON.read_text(encoding="utf-8") != text:
            raise SignedPowerError(f"{OUT_JSON.name} does not reproduce")
        print(f"[check] {OUT_JSON.name} reproduces byte for byte")
        return 0
    OUT_JSON.write_text(text, encoding="utf-8", newline="\n")
    write_power_md(rows, OUT_MD, title="POWER: settlement flow ledger, signed H1 (Sierra Chart)", date="2026-09-26")
    for root, v in out["roots"].items():
        print(root, "n", v["n_days"], "share_cov_med", round(v["share_cov_median"], 3), "full", v["days_fully_covered"],
              {k: round(x, 4) if isinstance(x, float) else x for k, x in v["pre_sample"].items()})
        for var in ("resid", "raw"):
            for b, s in v["sim"][var].items():
                rn = s.get("rotation_null", {})
                print(f"  {var:5s} beta {b:5s} HC1 {s['power_hc1']:.3f} NW {s['power_nw5']:.3f} "
                      f"bhat {s['beta_hat_mean']:.3f}±{s['beta_hat_sd']:.3f} pr {s['partial_r_median']:.4f} "
                      f"rot {rn.get('beats_own_rotation_p95', '')} gate {rn.get('combined_gate', '')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
