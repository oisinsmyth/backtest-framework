"""D639 runner: the LETF close-flow model's signal frame, Phases 4-5 (Gates 1-2), with LETF-A7's reading, LETF-A8's H3,
the four groups, the component line and the trials log. Committed after D639 (e95c0a9), its POWER step (81dc902) and
LETF-A7/A8, and BEFORE its one run.

    uv run python scripts/run_letf_close_flow.py --selftest     # the audits fire on broken inputs
    uv run python scripts/run_letf_close_flow.py --run          # ONCE -> data/letf/letf_close_flow_signal.json + trials.csv
    uv run python scripts/run_letf_close_flow.py --check        # the rebuild equals the committed output

The book frame, prop lifecycle and walk-forward (Phases 6-7) run only if Gates 1-2 pass, in a later runner (D639 s.11).
Every definition is D639 s.3's; `backtest_framework.letf.model` holds the algebra. In-sample 2016-01-04 -> 2025-02-28;
nothing on or after 2025-03-01 is read (A10).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from backtest_framework.data.panels import load_panel
from backtest_framework.letf import model as M
from backtest_framework.validation.programme import TrialsCsv

REPO = Path(__file__).resolve().parents[1]
LETF = REPO / "data" / "letf"
OUT = LETF / "letf_close_flow_signal.json"
TRIALS = LETF / "trials.csv"  # D592's union schema through TrialsCsv (append-only), doc and family below
TRIAL_DOC, TRIAL_FAMILY = "LETF_CLOSE_FLOW_PREREG.md", "LETF close flow H1"
SPEC = REPO / "docs" / "decisions" / "D639-PRE-REG-letf-close-flow-h1-h5-on-nq-and-es.md"
AMEND = REPO / "docs" / "internal" / "LETF_CLOSE_FLOW_AMENDMENTS.md"
RESERVED_FROM = "2025-03-01"
SPLIT = "2024-01-01"
SETS = {"NQ": {"TQQQ": 3, "SQQQ": -3, "QLD": 2, "QID": -2},
        "ES": {"UPRO": 3, "SPXU": -3, "SSO": 2, "SDS": -2, "SPXL": 3, "SPXS": -3}}
DIREXION = ("SPXL", "SPXS")
USD_PER_POINT = {"NQ": 2.0, "ES": 5.0}  # MNQ, MES
RT_USD = {"NQ": 3.0 + 2.1342422122227602 * 0.5, "ES": 3.0 + 1.1345161408444429 * 1.25}  # D639 s.3 (D508 default line)
RT_POINTS = {r: RT_USD[r] / USD_PER_POINT[r] for r in RT_USD}
TAUS = ["14:30", "15:00", "15:30"]
H4_TAU = "11:00"
KS = (2, 3, 5)
HOLDS = (5, 10, 15, 30, 60)
ALPHA = 0.05
FLAGS = ("fomc", "cpi", "quad_witching", "index_rebalance", "quarter_end")
STRETCH = ("2017-11-01", "2019-07-31")  # LETF-A6: Direxion's quarterly-anchor stretch
DEVIATIONS = [
    "D639 s.6's Direxion band edges use the signed p05/p95 of the N-PORT regime's measured daily error and +/- the "
    "abs p95 in the N-SAR and half-year regimes, whose signed quantiles were not recorded.",
    "LETF-A8: H3's slope is the raw move on the signed q (D639's 's on q' cancels the effect).",
]


class LetfRunError(RuntimeError):
    pass


def _load(name: str, fn: str) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    assert s is not None and s.loader is not None
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


def lag_rule(n: int) -> int:
    return int(math.floor(4 * (n / 100) ** (2 / 9)))


def hac_se(x: np.ndarray) -> float:
    """Newey-West SE of the mean, Bartlett kernel, D639 s.4's lag rule."""
    n = len(x)
    L = lag_rule(n)
    xc = x - x.mean()
    g0 = float((xc * xc).sum()) / n
    s = g0 + 2 * sum((1 - lg / (L + 1)) * float((xc[:-lg] * xc[lg:]).sum()) / n for lg in range(1, L + 1))
    return math.sqrt(max(s, 0.0) / n)


def holm(p: dict[str, float]) -> dict[str, float]:
    keys = sorted(p, key=lambda k: p[k])
    m, out, run = len(keys), {}, 0.0
    for i, k in enumerate(keys):
        run = max(run, min(1.0, (m - i) * p[k]))
        out[k] = run
    return out


# ------------------------------------------------------------------------------------------------ data
class Root:
    """One instrument's inputs, read once, cut at the seal."""

    def __init__(self, root: str, direxion_scale: dict[str, float] | None = None, dry: bool = False):
        self.root = root
        s = pd.read_csv(LETF / f"phase2_{root}_sessions.csv.gz", encoding="utf-8", dtype={"day": str})
        if (s["day"] >= RESERVED_FROM).any():
            raise LetfRunError("a sealed session reached the runner")
        self.days = M.trade_days(s)
        self.s = s.set_index("day")
        self.nyse = sorted(self.s.index[self.s["nyse_open"].astype(bool)])
        self.prev_of = {d: self.nyse[i - 1] for i, d in enumerate(self.nyse) if i > 0}
        u = pd.Index(self.days)
        self.daily_ret = (self.s.loc[u, "p1600"] / self.s.loc[u, "p_prev_close_same"] - 1).astype(float)
        self.equiv = self.s.loc[u, f"{root.lower()}_equiv_volume"].astype(float)
        self.daily_ret.index = pd.to_datetime(self.daily_ret.index)
        self.equiv.index = pd.to_datetime(self.equiv.index)
        a = pd.read_csv(LETF / "letf_aum_daily.csv.gz", encoding="utf-8", dtype={"date": str})
        if (a["date"] >= RESERVED_FROM).any():
            raise LetfRunError("a sealed AUM row reached the runner")
        a = a[a["ticker"].isin(SETS[root])]
        self.aum = {tk: g.set_index("date")["aum"].astype(float) for tk, g in a.groupby("ticker")}
        if direxion_scale:
            for tk in DIREXION:
                if tk in self.aum:
                    sc = pd.Series([direxion_scale_for(d, direxion_scale) for d in self.aum[tk].index],
                                   index=self.aum[tk].index)
                    self.aum[tk] = self.aum[tk] * sc
        if not dry:
            bp = load_panel(f"fut_{root}_rth_1m", reserved_from=RESERVED_FROM)
            self.bars_record = bp.record
            b = bp.frame
            self.C = b.pivot_table(index="day", columns="hhmm", values="close", aggfunc="first")
        else:
            # DRY RUN: the bars' calendar only (day, minute), never a price; synthetic random walks in their place,
            # so every code path runs and no real move is read
            bp = load_panel(f"fut_{root}_rth_1m", reserved_from=RESERVED_FROM, usecols=["day", "hhmm"])
            self.bars_record = bp.record
            b = bp.frame.assign(one=1.0)
            shape = b.pivot_table(index="day", columns="hhmm", values="one", aggfunc="first")
            rng = np.random.default_rng(639)
            base = self.s["p_prev_close_same"].reindex(shape.index).astype(float).fillna(10_000.0).to_numpy()[:, None]
            walk = np.cumsum(rng.normal(0, 2e-4, shape.shape), axis=1)
            self.C = pd.DataFrame(base * np.exp(walk), index=shape.index, columns=shape.columns).where(shape.notna())
            self.s["p0945_next_same"] = self.s["p_prev_close_same"] * np.exp(rng.normal(0, 2e-3, len(self.s)))


def direxion_scale_for(day: str, edge: dict[str, float]) -> float:
    if day <= "2017-10-31":
        return 1 + edge["nsar_monthly"]
    if day <= "2019-07-31":
        return 1 + edge["semiannual"]
    return 1 + edge["nport_monthly"]


def signals(R: Root, tau: str) -> pd.DataFrame:
    """D639 s.3, one row per usable signal day (the 21st usable session on), for entry time tau."""
    lab_sig, lab_ent = M.bar_label_ending_at(tau), tau
    if not lab_ent > lab_sig:
        raise LetfRunError("lag audit: the entry bar is not after the signal's bar")
    exit_lab = "15:59" if tau != H4_TAU else "11:59"
    rows = []
    for i, d in enumerate(R.days):
        if i < M.TRAILING_DAYS:
            continue
        p = R.prev_of[d]
        A = {tk: float(R.aum[tk][p]) for tk in SETS[R.root] if p in R.aum[tk].index}
        if len(A) != len(SETS[R.root]):
            raise LetfRunError(f"{R.root} {d}: a fund has no AUM for {p}")
        try:
            sig, ent, ex = (float(R.C.at[d, lab_sig]), float(R.C.at[d, lab_ent]), float(R.C.at[d, exit_lab]))
        except KeyError:
            continue
        if not all(np.isfinite([sig, ent, ex])):
            continue
        V = M.trailing_volume(R.equiv, d)
        sd = M.trailing_sigma(R.daily_ret, d)
        r = M.day_return(sig, float(R.s.at[d, "p_prev_close_same"]))
        qusd = M.aggregate_flow(SETS[R.root], A, r)
        q = M.normalised_flow(M.to_contracts(qusd, R.root, sig), V)
        imp = M.predicted_impact(sd, q, sig)
        dr = M.direction(qusd)
        row = {"day": d, "tau": tau, "sig": sig, "A_sum": sum(A.values()), "V": V, "sigma_d": sd, "r": r, "q": q, "impact": imp,
               "impact_bp": imp / sig * 1e4, "dir": dr, "entry": ent, "exit": ex, "move_bp": (ex / ent - 1) * 1e4,
               "s_bp": dr * (ex / ent - 1) * 1e4, "cost_bp": RT_POINTS[R.root] / ent * 1e4,
               "gross_usd": dr * (ex - ent) * USD_PER_POINT[R.root],
               "lsw": sum(L * (L - 1) * A[tk] for tk, L in SETS[R.root].items()),
               **{f"active_k{k}": M.is_active(imp, k, RT_POINTS[R.root]) for k in KS},
               **{f"flag_{f}": bool(R.s.at[d, f]) for f in FLAGS}}
        if tau != H4_TAU:
            for h in HOLDS:
                t_exit = (pd.Timestamp(f"2000-01-01 {tau}") + pd.Timedelta(minutes=h)).strftime("%H:%M")
                t_exit = min(t_exit, "15:59")
                v = R.C.at[d, t_exit] if t_exit in R.C.columns else np.nan
                row[f"s_bp_h{h}"] = dr * (float(v) / ent - 1) * 1e4 if np.isfinite(v) else np.nan
        nxt = R.s.at[d, "p0945_next_same"]
        row["h5_bp"] = dr * (float(nxt) / ex - 1) * 1e4 if tau != H4_TAU and np.isfinite(nxt) else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------------------------------ audits
def audit_lag(R: Root, sig: pd.DataFrame) -> None:
    """A SECOND implementation of the whole signal, never calling letf.model: A[t-1] from the NYSE calendar's own
    shift, V and sigma_d as pandas rolling windows shifted one session, then r, Q, q, I and the activation from the
    day's own prices. Any disagreement raises."""
    days = pd.Index(R.days)
    vol = pd.Series(R.equiv.to_numpy(), index=days)
    ret = pd.Series(R.daily_ret.to_numpy(), index=days)
    V2 = vol.rolling(20).mean().shift(1)
    S2 = ret.rolling(20).std(ddof=1).shift(1)
    nyse = pd.Series(R.nyse)
    prev = dict(zip(nyse.iloc[1:], nyse.iloc[:-1]))
    mult = {"NQ": 20.0, "ES": 50.0}[R.root]
    for row in sig.itertuples():
        A2 = {tk: float(R.aum[tk].loc[prev[row.day]]) for tk in SETS[R.root]}
        if sum(A2.values()) != row.A_sum:
            raise LetfRunError(f"lag audit: A[t-1] differs on {row.day}")
        if not (math.isclose(V2[row.day], row.V, rel_tol=1e-12) and math.isclose(S2[row.day], row.sigma_d, rel_tol=1e-12)):
            raise LetfRunError(f"lag audit: V or sigma_d differs on {row.day}")
        r2 = row.sig / float(R.s.at[row.day, "p_prev_close_same"]) - 1
        Q2 = sum(L * (L - 1) * A2[tk] * r2 for tk, L in SETS[R.root].items())
        q2 = Q2 / (mult * row.sig) / V2[row.day]
        i2 = 0.7 * S2[row.day] * math.sqrt(abs(q2)) * row.sig
        if not math.isclose(i2, row.impact, rel_tol=1e-9, abs_tol=1e-12):
            raise LetfRunError(f"lag audit: the impact differs on {row.day}")
        if abs(i2 - 3 * RT_POINTS[R.root]) > 1e-9 * i2 and (i2 >= 3 * RT_POINTS[R.root]) != row.active_k3:
            raise LetfRunError(f"lag audit: the activation differs on {row.day}")
        if int(np.sign(Q2)) != row.dir:
            raise LetfRunError(f"lag audit: the direction differs on {row.day}")


def audit_money() -> None:
    """A favourable move pays positively, long and short; an inverse fund's flow has the sign of the move."""
    for dr, ent, ex in ((1, 100.0, 101.0), (-1, 100.0, 99.0)):
        if not dr * (ex - ent) * USD_PER_POINT["NQ"] > 0:
            raise LetfRunError("sign audit: a favourable move did not pay")
    if not M.rebalance_flow(-3, 1e9, 0.01) > 0:
        raise LetfRunError("sign audit: an inverse fund's flow does not have the sign of the move")


def audit_right_quantity(R: Root, sig: pd.DataFrame) -> dict[str, int]:
    """The returns scored are today's contract (they differ from a continuous-front series on a roll day), and the AUM
    is t-1's (it differs from t's)."""
    rolls = R.s.index[R.s["roll"].astype(bool) & ~R.s["excluded"].astype(bool)]
    s_prev_front = R.s["p1600"].shift(1)
    differ = int(sum(1 for d in rolls if np.isfinite(s_prev_front.get(d, np.nan))
                     and s_prev_front[d] != R.s.at[d, "p_prev_close_same"]))
    if len(rolls) and differ == 0:
        raise LetfRunError("right quantity: no roll day's prior close differs from the continuous front's")
    t_aum = sum(1 for row in sig.itertuples()
                if sum(float(R.aum[tk].get(row.day, np.nan)) for tk in SETS[R.root]) != row.A_sum)
    if t_aum == 0:
        raise LetfRunError("right quantity: the AUM used equals day t's on every day")
    return {"roll_days_prior_close_differs": differ, "days_aum_t_minus_1_differs_from_t": t_aum}


# ------------------------------------------------------------------------------------------------ statistics
def h1_cell(a: pd.DataFrame) -> dict[str, Any]:
    x = a["s_bp"].to_numpy(float)
    if len(x) < 10:
        return {"n": int(len(x)), "note": "fewer than 10 active days", "p": 1.0}
    se = hac_se(x)
    t = float(x.mean() / se) if se > 0 else float("nan")
    return {"n": int(len(x)), "mean_gross_bp": float(x.mean()), "mean_cost_bp": float(a["cost_bp"].mean()),
            "mean_net_bp": float((x - a["cost_bp"]).mean()), "se_hac_bp": se, "t_hac": t,
            "p": float(1 - stats.norm.cdf(t)), "lag": lag_rule(len(x)), "n_2024_plus": int((a["day"] >= SPLIT).sum())}


def calib(a: pd.DataFrame) -> dict[str, Any]:
    """LETF-A7: beta = mean(s) / mean(I_bp), 90% CI from the HAC SE; one-sided p's for BELOW and ABOVE."""
    x = a["s_bp"].to_numpy(float)
    if len(x) < 10:
        return {"n": int(len(x)), "note": "fewer than 10 active days"}
    se, mi = hac_se(x), float(a["impact_bp"].mean())
    return {"mean_s_bp": float(x.mean()), "mean_predicted_bp": mi, "beta": float(x.mean() / mi),
            "ci90": [float((x.mean() - 1.645 * se) / mi), float((x.mean() + 1.645 * se) / mi)],
            "p_below": float(stats.norm.cdf((x.mean() - mi) / se)), "p_above": float(1 - stats.norm.cdf((x.mean() - mi) / se))}


def h2_cell(g: pd.DataFrame) -> dict[str, Any]:
    q = pd.qcut(g["q"].abs(), 5, labels=False, duplicates="drop")
    means = g.groupby(q)["s_bp"].mean()
    rho = float(stats.spearmanr(means.index, means.to_numpy()).statistic) if len(means) > 2 else float("nan")
    inv = int(sum(1 for i in range(len(means) - 1) if means.iloc[i + 1] < means.iloc[i]))
    return {"quintile_mean_s_bp": [float(v) for v in means], "quintile_n": [int(v) for v in g.groupby(q).size()],
            "spearman": rho, "inversions": inv, "pass": bool(rho > 0 and inv <= 1)}


def h3_cell(g: pd.DataFrame) -> dict[str, Any]:
    """LETF-A8: per year, the OLS slope of the RAW move on the signed q; Spearman against the year's mean L(L-1)A,
    with the exact permutation p over the year labels."""
    yrs, beta, lsw = [], [], []
    for y, d in g.groupby(g["day"].str[:4]):
        if len(d) < 20 or d["q"].std() == 0:
            continue
        b = np.polyfit(d["q"].to_numpy(float), d["move_bp"].to_numpy(float), 1)[0]
        yrs.append(y)
        beta.append(float(b))
        lsw.append(float(d["lsw"].mean()))
    n = len(yrs)
    rb, rl = stats.rankdata(beta), stats.rankdata(lsw)
    rho = float(stats.spearmanr(beta, lsw).statistic)
    if n > 10:
        raise LetfRunError("more than ten years: the exact permutation is not enumerable here")
    it = itertools.permutations(range(n))
    hit = total = 0
    while True:
        chunk = np.array(list(itertools.islice(it, 400_000)), dtype=np.int8)
        if not len(chunk):
            break
        d2 = ((rb[chunk] - rl) ** 2).sum(axis=1)
        rho_p = 1 - 6 * d2 / (n * (n * n - 1))
        hit += int((rho_p <= rho + 1e-12).sum())
        total += len(chunk)
    p_neg = hit / total
    return {"years": yrs, "beta_bp_per_q": beta, "mean_lsw_usd": lsw, "spearman": rho, "perm_p_negative": p_neg,
            "n_perm": int(total), "fails": bool(rho < 0 and p_neg < 0.05)}


def rotation_null(g: pd.DataFrame, k: int) -> dict[str, Any]:
    """Exact circular rotation of (direction, active) against the move, all T-1 offsets (D639 s.5)."""
    d = g.sort_values("day")
    act = d[f"active_k{k}"].to_numpy(bool)
    dr = d["dir"].to_numpy(float)
    mv = d["move_bp"].to_numpy(float)
    if act.sum() < 10:
        return {"note": "fewer than 10 active days"}
    obs = float((dr[act] * mv[act]).mean())
    T = len(d)
    null = np.empty(T - 1)
    for o in range(1, T):
        a2, d2 = np.roll(act, o), np.roll(dr, o)
        null[o - 1] = float((d2[a2] * mv[a2]).mean())
    return {"observed_bp": obs, "p50_bp": float(np.median(null)), "p95_bp": float(np.quantile(null, 0.95)),
            "rank_pct": float((null < obs).mean()), "offsets": int(T - 1), "se_of_p95": 0.0}


def four_groups(a: pd.DataFrame, root: str) -> dict[str, Any]:
    """CLAUDE.md's four groups, at 1 micro and D639's dollar cost."""
    if len(a) < 10:
        return {"n": int(len(a)), "note": "fewer than 10 trades"}
    g = a["gross_usd"].to_numpy(float)
    net = g - RT_USD[root]
    per_year = len(a) / (a["day"].str[:4].nunique())

    def shp(x: np.ndarray) -> float:
        return float(x.mean() / x.std(ddof=1) * math.sqrt(per_year)) if x.std(ddof=1) > 0 else float("nan")

    def srt(x: np.ndarray) -> float:
        dn = x[x < 0]
        dd = math.sqrt((dn ** 2).sum() / len(x)) if len(dn) else float("nan")
        return float(x.mean() / dd * math.sqrt(per_year)) if dd and dd > 0 else float("nan")

    eq = np.cumsum(net)
    lo, hi = np.quantile(g, [0.01, 0.99])
    pts = a["exit"].to_numpy(float) - a["entry"].to_numpy(float)
    yrs = a.groupby(a["day"].str[:4])["gross_usd"].agg(["size", "mean"]).reset_index()
    price_t = pd.qcut(a["entry"], 3, labels=["low", "mid", "high"])
    return {
        "performance": {"n": int(len(a)), "trades_per_year": per_year, "sharpe_net": shp(net), "sharpe_gross": shp(g),
                        "sortino_net": srt(net), "sortino_gross": srt(g), "mean_gross_usd": float(g.mean()),
                        "mean_net_usd": float(net.mean()), "vol_usd": float(g.std(ddof=1)),
                        "max_dd_usd": float((eq - np.maximum.accumulate(eq)).min()),
                        "mean_abs_move_points": float(np.abs(pts).mean()), "two_c_points": 2 * RT_POINTS[root],
                        "breakeven_rt_usd": float(g.mean()), "cost_rt_usd": RT_USD[root]},
        "distribution": {"mean": float(g.mean()), "median": float(np.median(g)), "win_rate": float((g > 0).mean()),
                         "payoff": float(g[g > 0].mean() / -g[g < 0].mean()) if (g < 0).any() and (g > 0).any() else None,
                         "skew": float(stats.skew(g)), "kurtosis": float(stats.kurtosis(g)),
                         "mean_ex_top1": float(g[g <= hi].mean()), "mean_ex_bottom1": float(g[g >= lo].mean()),
                         "mean_trimmed_both": float(g[(g >= lo) & (g <= hi)].mean())},
        "dependence": {"by_year": yrs.to_dict("records"),
                       "profitable_years": int((yrs["mean"] > RT_USD[root]).sum()), "years": int(len(yrs)),
                       "by_price_tercile": a.groupby(price_t, observed=True)["gross_usd"].mean().to_dict(),
                       "flagged_vs_not": {f: {"flagged": float(a.loc[a[f"flag_{f}"], "gross_usd"].mean()) if a[f"flag_{f}"].any() else None,
                                              "not": float(a.loc[~a[f"flag_{f}"], "gross_usd"].mean())} for f in FLAGS}},
    }


def daily_series(g: pd.DataFrame, k: int, root: str) -> pd.Series:
    a = g[g[f"active_k{k}"]]
    s = pd.Series(0.0, index=pd.Index(g["day"]))
    s.loc[a["day"].to_numpy()] = (a["gross_usd"] - RT_USD[root]).to_numpy()
    return s


def component_line(g: pd.DataFrame, root: str, ledger: dict[str, pd.Series] | None) -> dict[str, Any]:
    s = daily_series(g, 3, root)
    a = g[g["active_k3"]]
    x = s.to_numpy(float)
    out: dict[str, Any] = {"net_sharpe_all_days": float(x.mean() / x.std(ddof=1) * math.sqrt(252)) if x.std(ddof=1) > 0 else None,
                           "hit": float((a["gross_usd"] > RT_USD[root]).mean()) if len(a) else None,
                           "skew": float(stats.skew(a["gross_usd"])) if len(a) > 2 else None,
                           "gross_mean_usd": float(a["gross_usd"].mean()) if len(a) else None,
                           "net_mean_usd": float((a["gross_usd"] - RT_USD[root]).mean()) if len(a) else None,
                           "size": "1 micro", "rt_usd": RT_USD[root], "correlation": {}}
    if ledger:
        for k, v in ledger.items():
            j = pd.concat([s, v], axis=1, join="inner").dropna()
            if len(j) > 30 and j.iloc[:, 0].std() > 0 and j.iloc[:, 1].std() > 0:
                out["correlation"][k] = {"rho": float(j.corr().iloc[0, 1]), "n_days": int(len(j))}
    return out


def ledger_series() -> tuple[dict[str, pd.Series] | None, str]:
    try:
        D = _load("run_d466_components", "run_d466_components.py")
        _cal, S, _act, _desc = D.build_series()
        return {k: v for k, v in S.items()}, "D466 build_series (2016-01-04 -> 2023-12-29)"
    except Exception as e:  # the component line is still reported; the correlation's absence is named
        return None, f"D466 series unavailable: {type(e).__name__}: {e}"


# ------------------------------------------------------------------------------------------------ build
def trial(rows: list[dict], tid: str, tau: str, inst: str, k: int, hold: str, cost_mult: float, event_filter: str,
          a: pd.DataFrame, col: str = "s_bp", notes: str = "") -> None:
    x = a[col].dropna().to_numpy(float) if len(a) else np.array([])
    net = x - cost_mult * a.loc[a[col].notna(), "cost_bp"].to_numpy(float) if len(a) else x
    t = float(x.mean() / hac_se(x)) if len(x) >= 10 and hac_se(x) > 0 else None
    per_year = len(a) / max(a["day"].str[:4].nunique(), 1) if len(a) else 0
    sh = float(net.mean() / net.std(ddof=1) * math.sqrt(per_year)) if len(net) > 2 and net.std(ddof=1) > 0 else None
    rows.append({"trial_id": tid, "doc": TRIAL_DOC, "family": TRIAL_FAMILY,
                 "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "tau": tau,
                 "instrument": inst, "k": k, "hold": hold, "cost_mult": cost_mult, "event_filter": event_filter,
                 "n_trades": int(len(x)), "mean_gross": float(x.mean()) if len(x) else None,
                 "mean_net": float(net.mean()) if len(net) else None, "t_hac": t, "sharpe_net": sh,
                 "notes": "; ".join(z for z in (notes, f"reads_2024_plus={bool(len(a) and (a['day'] >= SPLIT).any())}") if z)})


def build(dry: bool = False) -> tuple[dict[str, Any], list[dict]]:
    audit_money()
    g0 = json.loads((LETF / "gate0.json").read_text(encoding="utf-8"))
    nb = g0["band_measured_on_proshares"]["_pooled"]
    br = g0["band_by_regime_on_proshares"]
    edges = {"p05": {"nport_monthly": nb["p05"], "nsar_monthly": -br["nsar_monthly"]["daily"]["abs_p95"],
                     "semiannual": -br["semiannual"]["daily"]["abs_p95"]},
             "p95": {"nport_monthly": nb["p95"], "nsar_monthly": br["nsar_monthly"]["daily"]["abs_p95"],
                     "semiannual": br["semiannual"]["daily"]["abs_p95"]}}
    ledger, ledger_note = ledger_series()
    trials: list[dict] = []
    doc: dict[str, Any] = {"spec": "D639 (e95c0a9) with LETF-A1..A8; POWER 81dc902", "rt_usd": RT_USD,
                           "rt_points": RT_POINTS, "deviations": DEVIATIONS, "ledger_series": ledger_note,
                           "cells": {}, "audits": {}, "reads": {}}
    sigs: dict[str, dict[str, pd.DataFrame]] = {}
    for root in ("NQ", "ES"):
        R = Root(root, dry=dry)
        doc["reads"][root] = {"bars": R.bars_record}
        sigs[root] = {tau: signals(R, tau) for tau in TAUS + [H4_TAU]}
        for tau, g in sigs[root].items():
            audit_lag(R, g)
        doc["audits"][root] = {"lag": "second implementation agrees on A[t-1], V, sigma_d, I and the activation",
                               "money": "favourable moves pay; inverse flow has the move's sign",
                               "right_quantity": audit_right_quantity(R, sigs[root]["15:00"])}
    # H1 over the six primary cells, Holm
    h1 = {f"{r}_{t}": h1_cell(sigs[r][t][sigs[r][t]["active_k3"]]) for r in ("NQ", "ES") for t in TAUS}
    adj = holm({k: v["p"] for k, v in h1.items()})
    for k, v in h1.items():
        v["p_holm"] = adj[k]
        v["pass"] = bool(v.get("mean_gross_bp") is not None and adj[k] < ALPHA and v["mean_gross_bp"] > v["mean_cost_bp"])
    # LETF-A7 calibration, Holm across the six for BELOW / ABOVE
    cal = {k: calib(sigs[k[:2]][k[3:]][sigs[k[:2]][k[3:]]["active_k3"]]) for k in h1}
    for side in ("below", "above"):
        adj2 = holm({k: v[f"p_{side}"] for k, v in cal.items() if f"p_{side}" in v})
        for k, pv in adj2.items():
            cal[k][f"p_{side}_holm"] = pv
    for k, v in cal.items():
        if "beta" in v:
            v["label"] = ("BELOW THE CLAIM" if v["p_below_holm"] < ALPHA else
                          "ABOVE THE CLAIM" if v["p_above_holm"] < ALPHA else "AT THE CLAIM")
            if not h1[k]["pass"] and v["label"] == "BELOW THE CLAIM":
                v["reading"] = "POWERED NULL against the mechanism's claimed size"
    # H4 per instrument
    h4 = {r: h1_cell(sigs[r][H4_TAU][sigs[r][H4_TAU]["active_k3"]]) for r in ("NQ", "ES")}
    for r, v in h4.items():
        v["pass"] = bool("t_hac" in v and abs(v["t_hac"]) < 2)
        v["calibration"] = calib(sigs[r][H4_TAU][sigs[r][H4_TAU]["active_k3"]])
    gate1_cells = [k for k, v in h1.items() if v["pass"] and h4[k[:2]]["pass"]]
    for k in h1:
        r, t = k[:2], k[3:]
        g = sigs[r][t]
        a = g[g["active_k3"]]
        cell: dict[str, Any] = {"H1": h1[k], "LETF_A7": cal[k], "H2": h2_cell(g), "H3": h3_cell(g),
                                "H5": {"n": int(a["h5_bp"].notna().sum()), "mean_bp": float(a["h5_bp"].mean())},
                                "null_rotation": rotation_null(g, 3), "groups": four_groups(a, r),
                                "component_line": component_line(g, r, ledger)}
        rob: dict[str, Any] = {}
        for kk in (2, 5):
            rob[f"k{kk}"] = h1_cell(g[g[f"active_k{kk}"]])
            trial(trials, f"{k}_k{kk}", t, r, kk, "close", 1, "none", g[g[f"active_k{kk}"]], notes="sensitivity k")
        rob["cost_x2_mean_net_bp"] = float((a["s_bp"] - 2 * a["cost_bp"]).mean()) if len(a) else None
        rob["without_flagged_days"] = h1_cell(a[~a[[f"flag_{f}" for f in FLAGS]].any(axis=1)])
        trial(trials, f"{k}_noflags", t, r, 3, "close", 1, "all flags out", a[~a[[f"flag_{f}" for f in FLAGS]].any(axis=1)])
        for f in FLAGS:
            rob[f"without_{f}"] = h1_cell(a[~a[f"flag_{f}"]])
        rob["hold_sweep"] = {}
        for h in HOLDS:
            aa = a.assign(s_bp=a[f"s_bp_h{h}"]).dropna(subset=["s_bp"])
            rob["hold_sweep"][f"{h}min"] = h1_cell(aa)
            trial(trials, f"{k}_hold{h}", t, r, 3, f"{h}min", 1, "none", aa)
        rob["split_2016_2023"] = h1_cell(a[a["day"] < SPLIT])
        rob["split_2024_plus"] = h1_cell(a[a["day"] >= SPLIT])
        if r == "ES":
            rob["without_direxion_stretch"] = h1_cell(a[~a["day"].between(*STRETCH)])
            trial(trials, f"{k}_nostretch", t, r, 3, "close", 1, "Direxion stretch out", a[~a["day"].between(*STRETCH)])
        cell["robustness"] = rob
        doc["cells"][k] = cell
        trial(trials, k, t, r, 3, "close", 1, "none", a, notes="PRIMARY")
        trial(trials, f"{k}_cost2", t, r, 3, "close", 2, "none", a)
    # ES under Direxion's band edges
    doc["es_band_edges"] = {}
    for edge, sc in edges.items():
        Re = Root("ES", sc, dry=dry)
        e = {}
        for t in TAUS:
            g = signals(Re, t)
            e[t] = {"active": int(g["active_k3"].sum()), "H1": h1_cell(g[g["active_k3"]])}
            trial(trials, f"ES_{t}_band_{edge}", t, "ES", 3, "close", 1, f"Direxion AUM at band {edge}", g[g["active_k3"]])
        doc["es_band_edges"][edge] = e
    for r in ("NQ", "ES"):
        trial(trials, f"{r}_{H4_TAU}_H4", H4_TAU, r, 3, "11:59", 1, "none", sigs[r][H4_TAU][sigs[r][H4_TAU]["active_k3"]],
              notes="H4 placebo")
    # the gates (D639 s.4)
    g2 = {k: bool(doc["cells"][k]["H2"]["pass"] and not doc["cells"][k]["H3"]["fails"]) for k in gate1_cells}
    doc["H4"] = h4
    doc["gates"] = {"gate1_cells": gate1_cells, "gate1": bool(gate1_cells), "gate2": g2,
                    "gate2_pass": bool(any(g2.values())),
                    "verdict": ("GATE 1 FAILED: STOP -> write-up" if not gate1_cells else
                                "GATE 2 FAILED: STOP -> write-up" if not any(g2.values()) else
                                "GATES 1-2 PASSED: Phase 6 (book frame) follows")}
    kill = [r for r in ("NQ", "ES") if not h4[r]["pass"] and any(h1[f"{r}_{t}"]["pass"] for t in TAUS)]
    if kill:
        doc["gates"]["verdict"] += f"; H4 placebo significant on {kill}: generic intraday momentum (deposit s.11)"
    doc["reads"]["spec_sha256"] = hashlib.sha256(SPEC.read_bytes()).hexdigest()
    doc["reads"]["amendments_sha256"] = hashlib.sha256(AMEND.read_bytes()).hexdigest()
    doc["trials"] = len(trials)
    return doc, trials


def dump(doc: dict[str, Any]) -> str:
    return json.dumps(doc, indent=1, sort_keys=True, default=lambda o: o if isinstance(o, str) else float(o)) + "\n"


def selftest() -> int:
    audit_money()
    x = np.array([1.0, -1.0] * 50)
    assert hac_se(x) > 0 and lag_rule(100) == 4
    assert holm({"a": 0.01, "b": 0.04}) == {"a": 0.02, "b": 0.04}
    # the lag audit fires on a signal that read day t
    R = Root("NQ", dry=True)  # synthetic prices: the selftest reads no real move
    g = signals(R, "15:00").head(60).copy()
    audit_lag(R, g)
    bad = g.copy()
    bad.loc[bad.index[30], "V"] = bad.loc[bad.index[30], "V"] * 1.01
    try:
        audit_lag(R, bad)
        raise AssertionError("the lag audit must fire on a changed V")
    except LetfRunError:
        pass
    bad = g.copy()
    bad.loc[bad.index[30], "A_sum"] += 1.0
    try:
        audit_lag(R, bad)
        raise AssertionError("the lag audit must fire on a changed A")
    except LetfRunError:
        pass
    try:
        signals(R, "00:00")
        raise AssertionError("an entry bar not after the signal's must raise")
    except LetfRunError:
        pass
    # the rotation null of a perfectly predictive signal is outside its own null
    d = pd.DataFrame({"day": [f"2020-{i // 28 + 1:02d}-{i % 28 + 1:02d}" for i in range(200)],
                      "move_bp": np.random.default_rng(1).normal(0, 10, 200)})
    d["dir"] = np.sign(d["move_bp"])
    d["active_k3"] = True
    rn = rotation_null(d, 3)
    assert rn["rank_pct"] > 0.99, rn
    print("selftest: 7 checks fire as they must")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.dry_run:
        t0 = time.time()
        doc, trials = build(dry=True)
        need = ("cells", "gates", "H4", "es_band_edges", "audits", "reads", "trials")
        miss = [k for k in need if k not in doc]
        if miss or len(doc["cells"]) != 6:
            raise SystemExit(f"DRY RUN INCOMPLETE: missing {miss}, cells {len(doc['cells'])}")
        dump(doc)  # serialises
        print(f"DRY RUN (synthetic prices, no real move read): every path ran; {len(doc['cells'])} cells, "
              f"{len(trials)} trials, in {(time.time() - t0) / 60:.1f} min. Nothing written.")
        return 0
    if a.run:
        if OUT.exists():
            raise SystemExit(f"{OUT.name} exists: the signal frame runs once (D639)")
        t0 = time.time()
        doc, trials = build()
        if TRIALS.exists():
            raise SystemExit(f"{TRIALS.name} exists: the run's trials are logged once")
        OUT.write_text(dump(doc), encoding="utf-8", newline="\n")
        log = TrialsCsv(TRIALS)
        for tr in trials:
            log.append(tr)
        print(json.dumps(doc["gates"], indent=1))
        print(f"wrote {OUT.name} and {TRIALS.name} ({len(trials)} trials) in {(time.time() - t0) / 60:.1f} min")
        return 0
    if a.check:
        doc, _ = build()
        if dump(doc) != OUT.read_text(encoding="utf-8"):
            raise SystemExit("CHECK FAILED: the rebuild differs from the committed output")
        print("CHECK: the rebuild equals the committed output")
        return 0
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
