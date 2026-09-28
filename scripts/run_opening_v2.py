"""D655 runner: the opening model's v2, a separate construction (OA-A10). Written after D655 (e80012c) and committed
BEFORE its run.

    uv run python scripts/run_opening_v2.py --selftest     # every audit fires on a deliberately broken input
    uv run python scripts/run_opening_v2.py --dry-run      # synthetic bars and G on the real calendar; writes nothing
    uv run python scripts/run_opening_v2.py --run          # ONCE, after D645's Phase 4 run: the in-sample (kill only)
    uv run python scripts/run_opening_v2.py --check        # the rebuild equals the committed output
    uv run python scripts/run_opening_v2.py --power        # D655 s.7, on the committed in-sample series
    uv run python scripts/run_opening_v2.py --freeze       # D655 s.8's freeze, only with a carried cell
    uv run python scripts/run_opening_v2.py --vault        # refuses: the vault-input path is not built yet

Two cells (D655 s.1): V2-F, the gap fade at 09:45 (target the prior close, 60-minute time stop, no price stop), and
V2-C, the continuation from 10:30 held to the RTH close (stop at 1.5 x sigma_h). Each is a binary logistic model of
its OWN trade's outcome, traded when the expected net, with payoffs fixed from the training window and scaled per row,
clears one round-trip cost (OA-A11 = D655-A1, which replaces s.4).

Readings fixed here, before the run (D655 leaves them to the code):
- A V2-F trade cancelled at the entry (the entry price already at or beyond the prior close) has no outcome: y is NaN,
  it is left out of every fit and every m, and it scores 0. Cancellations are counted.
- sigma_h's "20 prior eligible sessions" are the market's prior sessions that pass the base filter (usable, the
  09:30 bar present, >= 90% of the 09:30 -> 10:30 bars, d0 != 0); std with ddof = 1. DV20 is the mean over the 20
  prior fixture sessions with a finite window dollar volume (at least 15).
- "Per session, the mean over the two markets" divides the markets' summed net by 2 whether or not a market has a
  row; the sessions are the test windows' sessions (the cell's union calendar of eligible sessions).
- Robustness variants (s.5) keep the main model's decisions and rescore the trades (2x cost, the stress fill, the
  alternative exits); A4 unscaled and the moved break refit the walk-forward.
- The power study (s.7) applies the vault's Holm as its first step (p < 0.05 / the number of carried cells).
- Slot 9 is registered in the freeze's commit, the first commit after a cell is carried (s.8: "only once a cell is
  carried").
- fast_null.py's rotation machinery does not apply: the null here shuffles predictions over ~4,000 rows, a
  millisecond a draw. The label-equals-scorer audit is this study's assert_matches_scorer.
Nothing on or after 2025-03-01 is read (A10); the vault mode refuses until D655 s.8's input path exists.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from backtest_framework.opening import agents as AG  # noqa: E402
from backtest_framework.validation.frozen import assert_none_at_or_after, filter_before  # noqa: E402
from backtest_framework.validation.programme import TrialsCsv  # noqa: E402


def _load(name: str) -> Any:
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    assert s is not None and s.loader is not None
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


R = _load("run_opening_stages")  # D645's runner: sessions, S-A features, cost line, bar arrays, the leak canary, nw_t
G0 = R.G0

OD = REPO / "data" / "opening"
SPEC = REPO / "docs" / "decisions" / "D655-PRE-REG-opening-v2-fade-and-hold-to-close-on-expected-value.md"
OUT = OD / "v2_insample.json"
SESS_CSV = OD / "v2_sessions.csv"
POWER_OUT = OD / "v2_power.json"
FROZEN = OD / "FROZEN_v2.json"
RESERVED_FROM = "2025-03-01"
FIRST_ROW = "2016-01-04"
ROOTS = R.ROOTS
CELLS = {"V2-F": "09:45", "V2-C": "10:30"}
BREAK = "2022-05-11"
EDGE_K = 2.0  # V2-F: the prior close must lie >= 2 x the round-trip cost ahead
STOP_K = 1.5  # V2-C: the stop at 1.5 x sigma_h
DV_N, DV_MIN = 20, 15
SIGH_N, SIGH_MIN = 20, 15
HOLD_MIN = 60
C_GRID, N_FOLD = R.C_GRID, R.N_FOLD
SEED = 652
N_NULL, N_BOOT = 1000, 2000
VAULT_MIN_TRADES = 30
POWER_N, POWER_BLOCK, POWER_DRAWS = 390, 20, 2000
POWER_EDGE = (1.0, 0.5, 0.25, 0.0)
FEATS = ("gap_atr", "loc_with", "loc_against", "r_sigma", "vol_z", "z4s", "z4s_post")
FEATS_U = ("gap_atr", "loc_with", "loc_against", "r_sigma", "vol_z", "z4u", "z4u_post")
COST_PTS = {r: R.COST_USD[r] / R.USD_PER_POINT[r] for r in ROOTS}
MICRO = R.USD_PER_POINT  # MES $5, MNQ $2 a point


class V2Error(RuntimeError):
    pass


hm = R.hm


# =============================================================================================== inputs
def load_inputs(data_root: Path, dry: bool) -> tuple[pd.DataFrame, list[str], dict[str, pd.Series]]:
    """The bars (sealed at 2025-03-01), the usable sessions and G per market (agents.csv's column, same code)."""
    G0.BARS = data_root / "fixtures" / "fut_opening_globex_1m.csv.gz"
    R.DATA_ROOT = data_root
    b, use = R.load(dry)
    b = filter_before(b, "session", RESERVED_FROM)
    assert_none_at_or_after(b, "session", RESERVED_FROM)
    ag = pd.read_csv(OD / "agents.csv", encoding="utf-8", dtype={"session": str}, usecols=["root", "session", "G"])
    ag = filter_before(ag, "session", RESERVED_FROM)
    assert_none_at_or_after(ag, "session", RESERVED_FROM)
    G = {r: ag[ag["root"] == r].set_index("session")["G"] for r in ROOTS}
    if dry:  # a synthetic dealer gamma, same sessions, no information
        rng = np.random.default_rng(11)
        G = {r: pd.Series(rng.normal(0, 1e6, len(g)), index=g.index) for r, g in G.items()}
    return b, use, G


def window_dollar_volume(x: pd.DataFrame, t0: str) -> pd.Series:
    """Sum of close x volume over one market's 09:30 -> t0 bars, per session."""
    w = R.window(x, t0)
    return (w["close"] * w["volume"]).groupby(w["session"]).sum()


def dv20(dv: pd.Series) -> pd.Series:
    """The mean over the 20 prior sessions (at least 15 finite): never the same day's volume."""
    return dv.shift(1).rolling(DV_N, min_periods=DV_MIN).mean()


def sigma_h(d: pd.DataFrame, c_entry: pd.Series, base: pd.Series) -> pd.Series:
    rh = np.log(d["close"] / c_entry.reindex(d.index))
    compact = rh[base & np.isfinite(rh)]
    return compact.shift(1).rolling(SIGH_N, min_periods=SIGH_MIN).std(ddof=1).reindex(d.index)


def cell_rows(cell: str, tab: dict[str, pd.DataFrame], b: pd.DataFrame, G: dict[str, pd.Series],
              brk: str = BREAK) -> pd.DataFrame:
    """Every eligible (session, market) row of a cell with its features (D655 s.1-s.2). Signed features are x s,
    the cell's own trade direction; R.features_sa multiplies by whatever direction it is given."""
    t0 = CELLS[cell]
    need = 0.9 * (hm(t0) - hm("09:30"))
    out = []
    for r in ROOTS:
        d = tab[r]
        x = b[b["root"] == r]
        px = d[f"px_{t0}"]
        gap = d["open"] - d["prior_close"]
        d0 = np.sign(px - d["open"])
        base = (d["usable"] & d["open"].notna() & (d[f"n_{t0}"] >= need) & d["prior_close"].notna()
                & d["atr20"].notna())
        c_entry = x[x["hhmm"] == t0].set_index("session")["close"]
        sh = pd.Series(np.nan, index=d.index)
        if cell == "V2-F":
            s = -np.sign(gap)
            dist = s * (d["prior_close"] - px)
            elig = base & (gap != 0) & (dist >= EDGE_K * COST_PTS[r])
        else:
            s = d0
            dist = pd.Series(np.nan, index=d.index)
            sh = sigma_h(d, c_entry, base & (d0 != 0))
            elig = base & (d0 != 0) & sh.notna()
        s_arr = np.where(elig, s, np.nan)
        f = R.features_sa(d, t0, s_arr)
        dv = window_dollar_volume(x, t0).reindex(d.index)
        g = G[r].reindex(d.index).to_numpy(float)
        p4 = -g * gap.to_numpy(float) / dv20(dv).to_numpy(float)
        z4 = AG.standardise(p4)
        post = (d.index >= brk).astype(float)
        f["z4s"] = z4 * s_arr
        f["z4s_post"] = f["z4s"] * post
        zu = AG.standardise(-g * gap.to_numpy(float))  # OA-A7.4's z4, unscaled (robustness)
        f["z4u"] = zu * s_arr
        f["z4u_post"] = f["z4u"] * post
        f = f.assign(root=r, session=d.index, s=s_arr, px=px.to_numpy(float), gap=gap.to_numpy(float),
                     dist=dist.to_numpy(float), prior_close=d["prior_close"].to_numpy(float),
                     sh=sh.to_numpy(float), rng_t0=(d[f"hi_{t0}"] - d[f"lo_{t0}"]).to_numpy(float),
                     nq=float(r == "NQ"), elig=elig.to_numpy(bool))
        out.append(f)
    D = pd.concat(out, ignore_index=True)
    D = D[D["elig"] & (D["session"] >= FIRST_ROW)]
    ok = np.isfinite(D[list(FEATS)].to_numpy(float)).all(axis=1)
    return D[ok].sort_values(["session", "root"], kind="stable").reset_index(drop=True)


# =============================================================================================== trades
def sim_fade(bars: dict[str, np.ndarray], entry_bar: int, s: int, target: float,
             stop_dist: float | None = None) -> tuple[float, float, str, int] | None:
    """(entry, exit, reason, exit minute). Entry at the close of the bar starting at entry_bar. The target fills at
    the prior close, never better; the time stop at the close of the bar starting entry_bar + 60. An optional stop
    (robustness only) is taken before the target inside a bar and fills at the stop or the bar's open through it."""
    m = bars["m"]
    k = np.flatnonzero(m == entry_bar)
    if len(k) == 0 or s == 0:
        return None
    i0 = int(k[0])
    entry = float(bars["c"][i0])
    if s * (target - entry) <= 0:
        return entry, entry, "cancel", int(m[i0])
    stop = None if stop_dist is None else entry - s * stop_dist
    last = entry_bar + HOLD_MIN
    for i in range(i0 + 1, len(m)):
        if m[i] > last:
            return entry, float(bars["c"][i - 1]), "time_gap", int(m[i - 1])
        o, h, lo, c = (float(bars[v][i]) for v in ("o", "h", "l", "c"))
        if stop is not None and ((s > 0 and lo <= stop) or (s < 0 and h >= stop)):
            through = (s > 0 and o <= stop) or (s < 0 and o >= stop)
            return entry, (o if through else stop), "stop", int(m[i])
        if (s > 0 and h >= target) or (s < 0 and lo <= target):
            return entry, target, "target", int(m[i])
        if m[i] == last:
            return entry, c, "time", int(m[i])
    return entry, float(bars["c"][-1]), "session_end", int(m[-1])


def sim_hold(bars: dict[str, np.ndarray], entry_bar: int, s: int, sig_h: float | None) -> tuple[float, float, str, int] | None:
    """V2-C: entry at the close of the bar starting at entry_bar; the stop at entry x (1 - s x 1.5 x sigma_h), filled
    at the stop or the bar's open through it (stop first inside a bar); else the RTH close (the session's last bar,
    the 15:59 bar). sig_h None: no stop (robustness)."""
    m = bars["m"]
    k = np.flatnonzero(m == entry_bar)
    if len(k) == 0 or s == 0:
        return None
    i0 = int(k[0])
    entry = float(bars["c"][i0])
    stop = None if sig_h is None else entry * (1 - s * STOP_K * sig_h)
    for i in range(i0 + 1, len(m)):
        o, h, lo = float(bars["o"][i]), float(bars["h"][i]), float(bars["l"][i])
        if stop is not None and ((s > 0 and lo <= stop) or (s < 0 and h >= stop)):
            through = (s > 0 and o <= stop) or (s < 0 and o >= stop)
            return entry, (o if through else stop), "stop", int(m[i])
    return entry, float(bars["c"][-1]), "close", int(m[-1])


def stress_entry(bars: dict[str, np.ndarray], entry_bar: int, s: int) -> float:
    """The worst close of the bars starting t0 .. t0+4 (closing t0+1 .. t0+5) for the trade."""
    m = bars["m"]
    c = bars["c"][(m >= entry_bar) & (m <= entry_bar + 4)]
    if len(c) == 0:
        return float("nan")
    return float(c.max() if s > 0 else c.min())


def outcomes(D: pd.DataFrame, cell: str, bars: dict, variant: str = "main") -> pd.DataFrame:
    """Per row: entry, exit, reason, minutes held, gross and net bp (D645's cost line) and the label y. y is the
    outcome of the SAME simulation that prices the trade (the label equals the scorer)."""
    t0 = CELLS[cell]
    eb = hm(t0)
    rows = []
    for rec in D.itertuples(index=False):
        key = (rec.root, rec.session)
        s = int(rec.s)
        res = None
        if key in bars:
            if cell == "V2-F":
                sd = 0.5 * rec.rng_t0 if variant == "fade_stop" else None
                res = sim_fade(bars[key], eb, s, float(rec.prior_close), sd)
            else:
                res = sim_hold(bars[key], eb, s, None if variant == "hold_nostop" else float(rec.sh))
        if res is None:
            rows.append((np.nan, np.nan, "missing", 0.0, np.nan, np.nan, np.nan, np.nan))
            continue
        e, x, why, mx = res
        if variant == "stress" and why != "cancel":
            e = stress_entry(bars[key], eb, s)
        if why == "cancel":
            rows.append((e, x, why, 0.0, 0.0, 0.0, 0.0, np.nan))
            continue
        gross = R.pnl_bp(s, e, x)
        cost = COST_PTS[rec.root] / e * 1e4
        net = gross - cost
        y = float(why == "target") if cell == "V2-F" else float(net > 0)
        rows.append((e, x, why, float(mx - eb), gross, net, cost, y))
    o = pd.DataFrame(rows, columns=["entry", "exit", "reason", "held_min", "gross", "net", "cost_bp", "y"],
                     index=D.index)
    return o


def audit_label_is_scorer(D: pd.DataFrame, cell: str) -> None:
    """The label equals the scorer on every row: the net is recomputed from (s, entry, exit) by an independent
    formula, and y must agree with the reason (V2-F) or the net's sign (V2-C)."""
    t = D[D["reason"].isin(["target", "time", "time_gap", "session_end", "stop", "close"])]
    net2 = t["s"] * (t["exit"] - t["entry"]) / t["entry"] * 1e4 - t["root"].map(COST_PTS) / t["entry"] * 1e4
    if not np.allclose(net2.to_numpy(float), t["net"].to_numpy(float), rtol=0, atol=1e-9):
        raise V2Error(f"{cell}: the scorer's net differs from the independent recomputation")
    want = (t["reason"] == "target") if cell == "V2-F" else (net2 > 0)
    if not (t["y"].to_numpy(float) == want.to_numpy(float)).all():
        raise V2Error(f"{cell}: a label differs from the scorer's outcome")
    if D.loc[D["reason"] == "cancel", "y"].notna().any():
        raise V2Error(f"{cell}: a cancelled trade carries a label")


# =============================================================================================== walk-forward
def logloss_b(p: np.ndarray, y: np.ndarray) -> float:
    p = np.clip(p, 1e-15, 1 - 1e-15)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def fit_b(X: np.ndarray, y: np.ndarray, C: float) -> LogisticRegression:
    m = LogisticRegression(C=C, max_iter=5000, tol=1e-8)
    m.fit(X, y)
    return m


def p1(m: LogisticRegression, X: np.ndarray) -> np.ndarray:
    return m.predict_proba(X)[:, list(m.classes_).index(1.0)]


PCLIP = 1e-9


def train_m(trl: pd.DataFrame, cell: str, p_tr: np.ndarray) -> dict[str, float]:
    """OA-A11's expected-value inputs, from the training window's completed trades only (pooled over the markets).
    V2-F: (a, beta) of the OLS of a timed-out trade's gross bp on p/(1-p) x dist_bp (a random walk pins them at 0 and
    -1). V2-C: the mean gross in units of sigma_h over the y = 1 trades, and minus it over the y = 0 trades."""
    y = trl["y"].to_numpy(float)
    if cell == "V2-F":
        to = y == 0
        q = np.clip(p_tr[to], PCLIP, 1 - PCLIP)
        x = q / (1 - q) * (trl["dist"] / trl["px"]).to_numpy(float)[to] * 1e4
        A = np.column_stack([np.ones(int(to.sum())), x])
        a, beta = np.linalg.lstsq(A, trl["gross"].to_numpy(float)[to], rcond=None)[0]
        return {"a_T": float(a), "b_T": float(beta)}
    gs = trl["gross"].to_numpy(float) / (trl["sh"].to_numpy(float) * 1e4)
    return {"m_plus_s": float(gs[y == 1].mean()), "m_minus_s": float(-gs[y == 0].mean())}


def walk(D: pd.DataFrame, cell: str, feats: tuple[str, ...], cal: list[str], max_windows: int | None = None) -> pd.DataFrame:
    """OOS p for every test-window row (D655 s.3), the training window's base rate and m values, the chosen C."""
    R.check_budget(list(feats))
    out = []
    p_train: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    joint_diff = float("nan")
    for w, (tr_s, te_s) in enumerate(R.windows(cal)):
        if max_windows is not None and w >= max_windows:
            break
        tr = D[D["session"].isin(set(tr_s))]
        te = D[D["session"].isin(set(te_s))]
        trl = tr[tr["y"].notna()]
        if len(te) == 0 or trl["y"].nunique() < 2:
            continue
        mu = trl[list(feats)].mean()
        sd = trl[list(feats)].std(ddof=0).replace(0, 1.0)
        Xtr = np.column_stack([((trl[list(feats)] - mu) / sd).to_numpy(float), trl["nq"].to_numpy(float)])
        Xte = np.column_stack([((te[list(feats)] - mu) / sd).to_numpy(float), te["nq"].to_numpy(float)])
        ytr = trl["y"].to_numpy(float)
        blocks = np.array_split(np.array(tr_s), N_FOLD)
        best, best_ll = C_GRID[0], math.inf
        for C in C_GRID:
            lls = []
            for blk in blocks:
                vm = trl["session"].isin(set(blk)).to_numpy()
                if vm.all() or not vm.any() or len(set(ytr[~vm])) < 2:
                    continue
                lls.append(logloss_b(p1(fit_b(Xtr[~vm], ytr[~vm], C), Xtr[vm]), ytr[vm]))
            ll = float(np.mean(lls)) if lls else math.inf
            if ll < best_ll - 1e-12:
                best, best_ll = C, ll
        m = fit_b(Xtr, ytr, best)
        p = p1(m, Xte)
        if not out:  # the right-quantity audit: a fit that SAW the test rows predicts them differently
            tel = te["y"].notna().to_numpy()
            mj = fit_b(np.vstack([Xtr, Xte[tel]]), np.concatenate([ytr, te["y"].to_numpy(float)[tel]]), best)
            joint_diff = float(np.abs(p1(mj, Xte) - p).max())
        base = te["root"].map(trl.groupby("root")["y"].mean()).to_numpy(float)
        p_tr = p1(m, Xtr)  # the final model's own probability for each training row (OA-A11's regressor)
        te = te.assign(p=p, base=base, C=best, window=w, **train_m(trl, cell, p_tr))
        p_train[w] = (trl.index.to_numpy(), p_tr)
        out.append(te)
    P = pd.concat(out, ignore_index=True)
    P.attrs["p_train"] = p_train
    P.attrs["oos_vs_joint_maxdiff"] = joint_diff
    P.attrs["test_sessions"] = sorted(set(P["session"]))
    return P


# =============================================================================================== decision
def cost_bp_t0(P: pd.DataFrame) -> np.ndarray:
    """The round-trip cost in bp of the price at t0 (D655 s.1, OA-A11), known at the decision."""
    return (P["root"].map(COST_PTS) / P["px"]).to_numpy(float) * 1e4


def ev(P: pd.DataFrame, cell: str, p: np.ndarray | None = None) -> np.ndarray:
    """OA-A11's expected net bp per row."""
    p = np.clip(P["p"].to_numpy(float) if p is None else p, PCLIP, 1 - PCLIP)
    cost = cost_bp_t0(P)
    if cell == "V2-F":
        dist_bp = (P["dist"] / P["px"]).to_numpy(float) * 1e4
        g_t = P["a_T"].to_numpy(float) + P["b_T"].to_numpy(float) * p / (1 - p) * dist_bp
        return p * (dist_bp - cost) + (1 - p) * (g_t - cost)
    sh_bp = P["sh"].to_numpy(float) * 1e4
    return sh_bp * (p * P["m_plus_s"].to_numpy(float) - (1 - p) * P["m_minus_s"].to_numpy(float)) - cost


def decide(P: pd.DataFrame, cell: str, margin: float = 1.0) -> np.ndarray:
    """OA-A11.3: trade iff EV > margin x the round-trip cost (margin 1; robustness 0)."""
    return ev(P, cell) > margin * cost_bp_t0(P)


def decide_again(P: pd.DataFrame, cell: str, D: pd.DataFrame, margin: float = 1.0) -> np.ndarray:
    """The lag audit's second implementation: it never calls ev/decide/train_m. Each window's training rows are
    re-derived from the calendar (the sessions before the window's first test session) and must be exactly the rows
    the walk trained on; the payoff inputs are re-fitted with np.polyfit / explicit sums, and the rule is evaluated
    row by row in plain floats."""
    out = np.zeros(len(P), dtype=bool)
    cal = sorted(set(D["session"]))
    first_test = {w: g["session"].min() for w, g in P.groupby("window")}
    cache: dict[int, tuple[float, float]] = {}
    for w, s0 in first_test.items():
        i = cal.index(s0)
        tr = D[D["session"].isin(set(cal[max(0, i - R.TRAIN):i])) & D["y"].notna()]
        idx, p_tr = P.attrs["p_train"][w]
        if not np.array_equal(np.sort(tr.index.to_numpy()), np.sort(idx)):
            raise V2Error(f"{cell}: window {w} trained on rows other than the sessions before its test window")
        p_of = dict(zip(idx.tolist(), p_tr.tolist()))
        if cell == "V2-F":
            xs, gs = [], []
            for k, rec in zip(tr.index, tr.itertuples(index=False)):
                if rec.y == 0:
                    q = min(max(p_of[k], PCLIP), 1 - PCLIP)
                    xs.append(q / (1 - q) * rec.dist / rec.px * 1e4)
                    gs.append(rec.gross)
            slope, icpt = np.polyfit(np.array(xs), np.array(gs), 1)
            cache[w] = (float(icpt), float(slope))
        else:
            wins = [r.gross / (r.sh * 1e4) for r in tr.itertuples(index=False) if r.y == 1]
            loss = [r.gross / (r.sh * 1e4) for r in tr.itertuples(index=False) if r.y == 0]
            cache[w] = (sum(wins) / len(wins), -sum(loss) / len(loss))
    for j, rec in enumerate(P.itertuples(index=False)):
        u, v2 = cache[rec.window]
        q = min(max(rec.p, PCLIP), 1 - PCLIP)
        cost = COST_PTS[rec.root] / rec.px * 1e4
        if cell == "V2-F":
            d_bp = rec.dist / rec.px * 1e4
            e = q * (d_bp - cost) + (1 - q) * (u + v2 * q / (1 - q) * d_bp - cost)
        else:
            e = rec.sh * 1e4 * (q * u - (1 - q) * v2) - cost
        out[j] = e > margin * cost
    return out


def audit_lag(P: pd.DataFrame, cell: str, D: pd.DataFrame) -> None:
    a, b2 = decide(P, cell), decide_again(P, cell, D)
    if not (a == b2).all():
        raise V2Error(f"{cell}: the traded set differs between the two implementations ({int((a != b2).sum())} rows)")


def audit_m_blind_to_test(D: pd.DataFrame, cell: str, feats: tuple[str, ...], cal: list[str]) -> None:
    """For each of the first three windows: every outcome from that window's first test session on is scrambled,
    and that window's p and payoff inputs (a, beta / m+_s, m-_s) must not move (a later window legitimately trains on
    earlier test rows)."""
    rng = np.random.default_rng(SEED)
    cols = ["p"] + (["a_T", "b_T"] if cell == "V2-F" else ["m_plus_s", "m_minus_s"])
    for w in range(3):
        P0 = walk(D, cell, feats, cal, max_windows=w + 1)
        P0 = P0[P0["window"] == w]
        if P0.empty:
            continue
        idx = np.flatnonzero((D["session"] >= P0["session"].min()).to_numpy())
        D2 = D.copy()
        perm = rng.permutation(len(idx))
        for col in ("net", "gross"):
            D2.loc[D2.index[idx], col] = D2.loc[D2.index[idx], col].to_numpy()[perm]
        D2.loc[D2.index[idx], "y"] = 1.0 - D2.loc[D2.index[idx], "y"]
        P1 = walk(D2, cell, feats, cal, max_windows=w + 1)
        P1 = P1[P1["window"] == w]
        if not np.array_equal(P0[cols].to_numpy(float), P1[cols].to_numpy(float), equal_nan=True):
            raise V2Error(f"{cell}: window {w}'s training quantities moved when its test-period outcomes moved")


# =============================================================================================== scoring
def per_session(P: pd.DataFrame, col: np.ndarray | pd.Series, sessions: list[str]) -> pd.Series:
    """Per session: the two markets' summed value / 2 (a market with no row, or no trade, contributes 0)."""
    v = pd.Series(np.asarray(col, dtype=float), index=P.index)
    return v.groupby(P["session"].to_numpy()).sum().reindex(sessions, fill_value=0.0) / 2.0


def one_sided(t: float) -> float:
    return float(stats.norm.sf(t)) if np.isfinite(t) else float("nan")


def sharpe(x: np.ndarray) -> float:
    x = np.asarray(x, float)
    sd = x.std(ddof=1)
    return float(x.mean() / sd * math.sqrt(252)) if sd > 0 else float("nan")


def sortino(x: np.ndarray) -> float:
    x = np.asarray(x, float)
    dd = math.sqrt(float(np.mean(np.minimum(x, 0.0) ** 2)))
    return float(x.mean() / dd * math.sqrt(252)) if dd > 0 else float("nan")


def max_dd(x: np.ndarray) -> float:
    c = np.cumsum(x)
    return float((np.maximum.accumulate(np.r_[0.0, c])[1:] - c).max()) if len(c) else float("nan")


def trade_dist(v: np.ndarray) -> dict[str, Any]:
    v = np.sort(v[np.isfinite(v)])
    n = len(v)
    if n < 3:
        return {"n": int(n)}
    k = max(1, int(round(0.01 * n)))
    w, lo = v[v > 0], v[v <= 0]
    return {"n": int(n), "mean": float(v.mean()), "median": float(np.median(v)), "win": float((v > 0).mean()),
            "payoff": float(w.mean() / -lo.mean()) if len(w) and len(lo) and lo.mean() < 0 else float("nan"),
            "skew": float(stats.skew(v)), "kurtosis": float(stats.kurtosis(v)),
            "mean_ex_top1pct": float(v[:-k].mean()), "mean_ex_bottom1pct": float(v[k:].mean()),
            "mean_trimmed_both": float(v[k:-k].mean()), "top1pct_share_of_sum": float(v[-k:].sum() / v.sum())
            if v.sum() != 0 else float("nan")}


def auc_block(P: pd.DataFrame, rng: np.random.Generator) -> dict[str, Any]:
    t = P[P["y"].notna()]
    y, p = t["y"].to_numpy(float), t["p"].to_numpy(float)
    if len(set(y)) < 2:
        return {"auc": float("nan")}
    auc = float(roc_auc_score(y, p))
    sess = t["session"].to_numpy()
    uniq, inv = np.unique(sess, return_inverse=True)
    rows_of = [np.flatnonzero(inv == i) for i in range(len(uniq))]
    bs = []
    for _ in range(N_BOOT):
        pick = rng.integers(0, len(uniq), len(uniq))
        ix = np.concatenate([rows_of[i] for i in pick])
        if len(set(y[ix])) == 2:
            bs.append(roc_auc_score(y[ix], p[ix]))
    return {"auc": auc, "ci95": [float(np.quantile(bs, 0.025)), float(np.quantile(bs, 0.975))], "n": int(len(y))}


def reliability(P: pd.DataFrame) -> dict[str, Any]:
    t = P[P["y"].notna()]
    p, y = t["p"].to_numpy(float), t["y"].to_numpy(float)
    bins = np.minimum((p * 10).astype(int), 9)
    return {f"{k / 10:.1f}": {"n": int((bins == k).sum()), "pred": float(p[bins == k].mean()),
                              "realised": float(y[bins == k].mean())} for k in range(10) if (bins == k).any()}


def null_shuffle(P: pd.DataFrame, cell: str, sessions: list[str], rng: np.random.Generator) -> dict[str, Any]:
    """p shuffled across rows within market x year; the policy's per-session mean recomputed each draw."""
    grp = (P["root"] + "_" + P["session"].str[:4]).to_numpy()
    idx = [np.flatnonzero(grp == g) for g in np.unique(grp)]
    p = P["p"].to_numpy(float)
    net = np.where(P["reason"].eq("cancel") | P["net"].isna(), 0.0, P["net"].to_numpy(float))
    s_ix = pd.Index(sessions).get_indexer(P["session"])
    if (s_ix < 0).any():
        raise V2Error("a scored row's session is outside the test calendar")
    draws = np.empty(N_NULL)
    for k in range(N_NULL):
        q = p.copy()
        for ix in idx:
            q[ix] = p[rng.permutation(ix)]
        tr = ev(P, cell, q) > cost_bp_t0(P)
        draws[k] = np.bincount(s_ix, weights=np.where(tr, net, 0.0), minlength=len(sessions)).sum() / 2 / len(sessions)
    q95 = [float(np.quantile(rng.choice(draws, len(draws)), 0.95)) for _ in range(N_BOOT)]
    return {"p50": float(np.median(draws)), "p95": float(np.quantile(draws, 0.95)), "p95_se": float(np.std(q95, ddof=1)),
            "draws": N_NULL, "_draws": draws}


def score(P: pd.DataFrame, cell: str, sessions: list[str], trade: np.ndarray, net_col: str = "net",
          gross_col: str = "gross") -> dict[str, Any]:
    """The per-session statistic (D655 s.5): policy, always and their paired difference, with the HAC t."""
    done = ~P["reason"].isin(["cancel", "missing"]).to_numpy()
    net = np.where(done, P[net_col].to_numpy(float), 0.0)
    gross = np.where(done, P[gross_col].to_numpy(float), 0.0)
    pol = per_session(P, np.where(trade, net, 0.0), sessions)
    alw = per_session(P, net, sessions)
    diff = pol - alw
    tp, sp = R.nw_t(pol.to_numpy())
    td, sd = R.nw_t(diff.to_numpy())
    return {"n_sessions": len(sessions), "rows": int(len(P)), "traded_rows": int((trade & done).sum()),
            "always_rows": int(done.sum()), "cancelled": int((P["reason"] == "cancel").sum()),
            "policy_mean_bp": float(pol.mean()), "policy_se": sp, "policy_t_hac": tp, "policy_p_one_sided": one_sided(tp),
            "policy_gross_mean_bp": float(per_session(P, np.where(trade, gross, 0.0), sessions).mean()),
            "always_mean_bp": float(alw.mean()), "always_gross_mean_bp": float(per_session(P, gross, sessions).mean()),
            "diff_mean_bp": float(diff.mean()), "diff_se": sd, "diff_t_hac": td, "diff_p_one_sided": one_sided(td)}


def dollars(P: pd.DataFrame, trade: np.ndarray, sessions: list[str]) -> dict[str, Any]:
    """Group 1 in dollars at one micro: the daily P&L over the test sessions, net and gross."""
    done = ~P["reason"].isin(["cancel", "missing"]).to_numpy()
    mult = P["root"].map(MICRO).to_numpy(float)
    g = np.where(trade & done, P["gross"].to_numpy(float) / 1e4 * P["entry"].to_numpy(float) * mult, 0.0)
    n = np.where(trade & done, g - P["root"].map(R.COST_USD).to_numpy(float), 0.0)
    dn = pd.Series(n, index=P.index).groupby(P["session"].to_numpy()).sum().reindex(sessions, fill_value=0.0)
    dg = pd.Series(g, index=P.index).groupby(P["session"].to_numpy()).sum().reindex(sessions, fill_value=0.0)
    t = trade & done
    tr_g = P.loc[t, "gross"].to_numpy(float)
    return {"net_sharpe": sharpe(dn.to_numpy()), "net_sortino": sortino(dn.to_numpy()),
            "gross_sharpe": sharpe(dg.to_numpy()), "gross_sortino": sortino(dg.to_numpy()),
            "net_usd_per_day": float(dn.mean()), "vol_usd_annual": float(dn.std(ddof=1) * math.sqrt(252)),
            "max_dd_usd": max_dd(dn.to_numpy()), "exposure_sessions": float((dn != 0).mean()),
            "mean_minutes_held": float(P.loc[t, "held_min"].mean()) if t.any() else float("nan"),
            "mean_gross_bp_per_trade": float(tr_g.mean()) if t.any() else float("nan"),
            "two_c_bp": float(2 * P.loc[t, "cost_bp"].mean()) if t.any() else float("nan"),
            "breakeven_cost_bp_rt": float(tr_g.mean()) if t.any() else float("nan"),
            "hit_net": float((P.loc[t, "net"] > 0).mean()) if t.any() else float("nan"),
            "skew_per_trade_usd": float(stats.skew(n[t])) if t.sum() > 2 else float("nan"),
            "_daily_net": dn}


def splits(P: pd.DataFrame, trade: np.ndarray) -> dict[str, Any]:
    done = ~P["reason"].isin(["cancel", "missing"]).to_numpy()
    t = P[trade & done]
    out: dict[str, Any] = {"by_year": {}, "by_market": {}, "era": {}}
    for k, g in t.groupby(t["session"].str[:4]):
        out["by_year"][k] = {"n": int(len(g)), "mean_net_bp": float(g["net"].mean()), "sum_net_bp": float(g["net"].sum())}
    for k, g in t.groupby("root"):
        out["by_market"][k] = {"n": int(len(g)), "mean_net_bp": float(g["net"].mean()), "mean_gross_bp": float(g["gross"].mean())}
    for k, g in (("pre", t[t["session"] < BREAK]), ("post", t[t["session"] >= BREAK])):
        out["era"][k] = {"n": int(len(g)), "mean_net_bp": float(g["net"].mean()) if len(g) else float("nan")}
    if len(t):
        top = t.loc[t["net"].abs().idxmax()]
        out["top_trade"] = {"session": top["session"], "root": top["root"], "side": int(top["s"]),
                            "entry": float(top["entry"]), "exit": float(top["exit"]), "reason": top["reason"],
                            "net_bp": float(top["net"])}
        out["names_to_half"] = {"sessions_to_half_of_net": int(np.searchsorted(
            np.cumsum(np.sort(t["net"].to_numpy())[::-1]), 0.5 * t["net"].sum()) + 1) if t["net"].sum() > 0 else None}
    return out


def component_corr(daily_net: pd.Series) -> dict[str, Any]:
    """Correlation with D466's committed ledger series K1..K6 (2016-2023), as D640/D643 did. The prop book's
    admitted MACD arm has no daily series on disk (COMPONENTS_PROP.md), so it is named, not computed."""
    out: dict[str, Any] = {"missing": ["prop entry #2 (MACD day-session arm): its daily P&L is not on disk"]}
    try:
        D466 = _load("run_d466_components")
        _cal, S, _act, _desc = D466.build_series()
    except Exception as e:  # noqa: BLE001 -- a missing ledger input is reported, never silently skipped
        out["missing"].append(f"D466 K1..K6: {type(e).__name__}: {e}")
        return out
    led = daily_net[daily_net.index <= "2023-12-29"]
    for k, v in S.items():
        j = pd.concat([led, v], axis=1, join="inner").dropna()
        if len(j) > 30 and j.iloc[:, 0].std() > 0 and j.iloc[:, 1].std() > 0:
            out[k] = {"rho": round(float(j.corr().iloc[0, 1]), 4), "n_days": int(len(j))}
    return out


# =============================================================================================== build
def build(data_root: Path, dry: bool = False) -> tuple[dict[str, Any], list[dict], pd.DataFrame]:
    t_start = time.time()
    audit_money()
    b, use, G = load_inputs(data_root, dry)
    tab = R.session_table(b, use)
    bars = R.bar_arrays(b)
    rng = np.random.default_rng(SEED)
    leak_checks(b, use, G, rng)
    doc: dict[str, Any] = {"spec": "D655 (e80012c); OA-A10; D645's walk-forward and cost line", "dry_run": dry,
                           "cells": {}, "reads": {}}
    trials: list[dict] = []
    sess_rows = []
    for cell in CELLS:
        D = cell_rows(cell, tab, b, G)
        D = pd.concat([D, outcomes(D, cell, bars)], axis=1)
        D = D[D["reason"] != "missing"].reset_index(drop=True)
        audit_label_is_scorer(D, cell)
        cal = sorted(set(D["session"]))
        P = walk(D, cell, FEATS, cal)
        R.audit_oos(P)
        audit_lag(P, cell, D)
        audit_m_blind_to_test(D, cell, FEATS, cal)
        sessions = P.attrs["test_sessions"]
        trade = decide(P, cell)
        main = score(P, cell, sessions, trade)
        audit_right_quantity(P, trade, sessions, main)
        oracle = audit_oracle(P, cell, sessions)
        usd = dollars(P, trade, sessions)
        daily = usd.pop("_daily_net")
        done = ~P["reason"].isin(["cancel", "missing"]).to_numpy()
        yv = P["y"].to_numpy(float)
        lab = ~np.isnan(yv)
        c: dict[str, Any] = {
            "t0": CELLS[cell], "rows_eligible": int(len(D)), "calendar": [cal[0], cal[-1], len(cal)],
            "windows": int(P["window"].nunique()), "test_span": [sessions[0], sessions[-1], len(sessions)],
            "y_rate": float(np.nanmean(D["y"].to_numpy(float))), "statistic": main, "oracle": oracle,
            "classification": {"logloss": logloss_b(P.loc[lab, "p"].to_numpy(float), yv[lab]),
                               "base_logloss": logloss_b(P.loc[lab, "base"].to_numpy(float), yv[lab]),
                               "brier": float(np.mean((P.loc[lab, "p"].to_numpy(float) - yv[lab]) ** 2)),
                               **auc_block(P, rng), "reliability": reliability(P),
                               "C_chosen": P.groupby("window")["C"].first().value_counts().to_dict()},
            "dollars_1_micro": usd,
            "trades_net_bp": trade_dist(P.loc[trade & done, "net"].to_numpy(float)),
            "trades_gross_bp": trade_dist(P.loc[trade & done, "gross"].to_numpy(float)),
            "always_trades_net_bp": trade_dist(P.loc[done, "net"].to_numpy(float)),
            "exit_reasons": P.loc[trade, "reason"].value_counts().to_dict(),
            "splits": splits(P, trade), "null": null_shuffle(P, cell, sessions, rng),
            "component": {"net_sharpe": usd["net_sharpe"], "net_sortino": usd["net_sortino"],
                          "gross_sharpe": usd["gross_sharpe"], "gross_sortino": usd["gross_sortino"],
                          "hit_net": usd["hit_net"], "skew_per_trade_usd": usd["skew_per_trade_usd"],
                          "correlation": component_corr(daily) if not dry else {"dry_run": True}},
            "robustness": robustness(D, P, cell, sessions, trade, bars, tab, b, G),
            "oos_vs_joint_maxdiff": P.attrs["oos_vs_joint_maxdiff"]}
        nl = c["null"]
        nl["share_of_draws_at_or_above_score"] = float((nl.pop("_draws") >= main["policy_mean_bp"]).mean())
        c["null"]["margin_vs_p95"] = main["policy_mean_bp"] - nl["p95"]
        c["null"]["verdict"] = ("ABOVE" if c["null"]["margin_vs_p95"] > 2 * nl["p95_se"] else
                                "UNRESOLVED" if c["null"]["margin_vs_p95"] > -2 * nl["p95_se"] else "BELOW")
        c["carried_to_vault"] = bool(main["policy_mean_bp"] > 0 and main["diff_mean_bp"] > 0)
        doc["cells"][cell] = c
        trials.append({"trial_id": f"D655_{cell}_insample", "doc": SPEC.name, "family": "opening V2 (D655)",
                       "stage": "in-sample (kill only)", "t0": CELLS[cell],
                       "construction": f"{cell}: EV rule on its own trade's outcome vs always",
                       "n_obs": main["n_sessions"], "mean_net": round(main["policy_mean_bp"], 6),
                       "t_hac": round(main["policy_t_hac"], 6),
                       "notes": f"diff={main['diff_mean_bp']:.6f}; carried={c['carried_to_vault']}; reads_2024_plus=True"})
        tr_sess = per_session(P, (trade & done).astype(float), sessions) * 2
        sess_rows.append(pd.DataFrame({"cell": cell, "session": sessions,
                                       "policy": per_session(P, np.where(trade & done, P["net"], 0.0), sessions).to_numpy(),
                                       "always": per_session(P, np.where(done, P["net"], 0.0), sessions).to_numpy(),
                                       "traded": tr_sess.to_numpy()}))
    doc["carried"] = [k for k, v in doc["cells"].items() if v["carried_to_vault"]]
    doc["reads"] = {"spec_sha256": lf_sha(SPEC), "reserved_from": RESERVED_FROM,
                    "last_session_read": str(b["session"].max())}
    doc["runtime_min"] = round((time.time() - t_start) / 60, 1)
    for tr in trials:
        tr["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return doc, trials, pd.concat(sess_rows, ignore_index=True)


def robustness(D: pd.DataFrame, P: pd.DataFrame, cell: str, sessions: list[str], trade: np.ndarray, bars: dict,
               tab: dict, b: pd.DataFrame, G: dict) -> dict[str, Any]:
    """Reported only (D655 s.5)."""
    out: dict[str, Any] = {}
    out["margin_0"] = score(P, cell, sessions, decide(P, cell, 0.0))  # OA-A11: EV > 0, no margin
    P2 = P.assign(net2=P["gross"] - 2 * P["cost_bp"])
    out["cost_2x"] = score(P2, cell, sessions, trade, net_col="net2")
    key = ["root", "session"]
    ocols = ["entry", "exit", "reason", "held_min", "gross", "net", "cost_bp", "y"]
    for variant in (("stress",) + (("fade_stop",) if cell == "V2-F" else ("hold_nostop",))):
        Pv = P.drop(columns=ocols).join(outcomes(P, cell, bars, variant))
        out[variant] = score(Pv, cell, sessions, trade)
    Du = D[np.isfinite(D[list(FEATS_U)].to_numpy(float)).all(axis=1)]
    calu = sorted(set(Du["session"]))
    Pu = walk(Du, cell, FEATS_U, calu)
    out["a4_unscaled"] = score(Pu, cell, Pu.attrs["test_sessions"], decide(Pu, cell))
    cal_all = sorted(set(D["session"]))
    i = int(np.searchsorted(cal_all, BREAK))
    for name, j in (("break_minus_63", i - 63), ("break_plus_63", i + 63)):
        brk = cal_all[j]
        Db = cell_rows(cell, tab, b, G, brk=brk)
        Db = Db.merge(D[key + ocols], on=key, how="inner")
        Pb = walk(Db, cell, FEATS, sorted(set(Db["session"])))
        out[name] = {"break": brk, **score(Pb, cell, Pb.attrs["test_sessions"], decide(Pb, cell))}
    return out


def lf_sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


# =============================================================================================== audits
def audit_money(pnl: Callable = R.pnl_bp, fade: Callable = sim_fade, hold: Callable = sim_hold) -> None:
    if not (pnl(1, 100.0, 101.0) > 0 and pnl(-1, 100.0, 99.0) > 0 and pnl(1, 100.0, 99.0) < 0):
        raise V2Error("money: a favourable move did not pay")
    m = np.arange(hm("09:45"), hm("10:50"))
    n = len(m)
    # a gap up (prior close 99 below the 100 open): the fade is short, towards the prior close. A bar opening through
    # the target (at 98) must still fill AT the target, never better
    bars = {"m": m, "o": np.r_[100.0, 100.0, 98.0, np.full(n - 3, 98.0)], "h": np.r_[100.2, 100.2, 98.1, np.full(n - 3, 98.1)],
            "l": np.r_[99.8, 99.8, 97.9, np.full(n - 3, 97.9)], "c": np.r_[100.0, 100.0, 98.0, np.full(n - 3, 98.0)]}
    s = int(-np.sign(100.0 - 99.0))
    if s != -1:
        raise V2Error("money: V2-F must trade towards the prior close")
    res = fade(bars, hm("09:45"), s, 99.0)
    if res is None or res[2] != "target" or res[1] != 99.0 or not R.pnl_bp(s, res[0], res[1]) > 0:
        raise V2Error(f"money: the fade's target must fill at the prior close and pay ({res})")
    # V2-C: a long whose stop is gapped through fills at the bar's open, never at the (better) stop
    bars = {"m": m, "o": np.r_[100.0, 100.0, 95.0, np.full(n - 3, 95.0)], "h": np.r_[100.2, 100.2, 95.1, np.full(n - 3, 95.1)],
            "l": np.r_[99.8, 99.8, 94.9, np.full(n - 3, 94.9)], "c": np.r_[100.0, 100.0, 95.0, np.full(n - 3, 95.0)]}
    res = hold(bars, hm("09:45"), 1, 0.01)  # stop at 100 x (1 - 0.015) = 98.5
    if res is None or res[2] != "stop" or res[1] > 95.0:
        raise V2Error(f"money: V2-C's stop filled better than the bar that gapped through it ({res})")


def audit_right_quantity(P: pd.DataFrame, trade: np.ndarray, sessions: list[str], main: dict[str, Any]) -> None:
    done = ~P["reason"].isin(["cancel", "missing"]).to_numpy()
    t = trade & done
    if t.any() and np.allclose(P.loc[t, "net"], P.loc[t, "gross"]):
        raise V2Error("right quantity: the net equals the gross")
    pol = per_session(P, np.where(t, P["net"], 0.0), sessions)
    alw = per_session(P, np.where(done, P["net"], 0.0), sessions)
    if not math.isclose(main["diff_mean_bp"], float((pol - alw).mean()), rel_tol=1e-9, abs_tol=1e-12):
        raise V2Error("right quantity: the difference is not policy minus always")


def audit_oracle(P: pd.DataFrame, cell: str, sessions: list[str]) -> dict[str, Any]:
    """The positive control (D655 s.9.4): trading exactly the rows with y = 1 must make money."""
    o = score(P, cell, sessions, (P["y"] == 1).to_numpy())
    if not o["policy_mean_bp"] > 0:
        raise V2Error(f"{cell}: the oracle (trade exactly y = 1) does not make money: the engine is broken")
    return o


def _as_v2(fn: Callable[[], Any]) -> Callable[[], None]:
    """D645's audits raise OpeningRunError; the selftest counts V2Error."""
    def run() -> None:
        try:
            fn()
        except R.OpeningRunError as e:
            raise V2Error(str(e)) from e
    return run


def leak_checks(b: pd.DataFrame, use: list[str], G: dict, rng: np.random.Generator) -> None:
    """D645's leak canary at each cell's t0 on a year of ES (the features, z4s included), and the DV20 canary."""
    yr = [s for s in sorted(set(b.loc[b["root"] == "ES", "session"])) if "2018-07-01" <= s <= "2019-06-30"]
    x_yr = b[(b["root"] == "ES") & b["session"].isin(yr)]
    for t0 in sorted(set(CELLS.values())):
        def fn(xx: pd.DataFrame, t: str = t0) -> pd.DataFrame:
            d = R.session_table(xx, use, ("ES",))["ES"]
            f = R.features_sa(d, t, np.ones(len(d)))
            dv = window_dollar_volume(xx, t).reindex(d.index)
            gap = (d["open"] - d["prior_close"]).to_numpy(float)
            f["z4s"] = AG.standardise(-G["ES"].reindex(d.index).to_numpy(float) * gap / dv20(dv).to_numpy(float))
            return f
        R.leak_check(fn, x_yr, t0, yr[130:], rng)
        dv_canary(x_yr, t0, yr[130:])


def dv_canary(x: pd.DataFrame, t0: str, sessions: list[str], dv_fn: Callable = dv20) -> None:
    """Corrupt one session's own 09:30 -> t0 volume: its DV20 must not move, and the next session's must."""
    base = dv_fn(window_dollar_volume(x, t0))
    s = sessions[len(sessions) // 2]
    y = x.copy()
    m = (y["session"] == s) & (y["hhmm"] >= "09:30") & (y["hhmm"] < t0)
    y.loc[m, "volume"] = y.loc[m, "volume"] * 50
    got = dv_fn(window_dollar_volume(y, t0))
    nxt = base.index[base.index.get_loc(s) + 1]
    if not math.isclose(float(base[s]), float(got[s]), rel_tol=1e-12):
        raise V2Error(f"DV20 at {s} moved when that day's own volume moved: the same day's volume leaked in")
    if math.isclose(float(base[nxt]), float(got[nxt]), rel_tol=1e-12):
        raise V2Error("the DV20 canary cannot fire: the next session's DV20 did not move either")


# =============================================================================================== selftest
def selftest() -> int:
    fired = []

    def must_raise(name: str, fn: Callable[[], Any]) -> None:
        try:
            fn()
        except V2Error:
            fired.append(name)
            return
        raise AssertionError(f"the {name} audit did not fire")

    audit_money()
    must_raise("money-pnl", lambda: audit_money(pnl=lambda D, e, x: -D * (x / e - 1)))
    must_raise("money-target-better", lambda: audit_money(
        fade=lambda bars, eb, s, tgt, sd=None: (100.0, 98.0, "target", eb + 2)))
    must_raise("money-stop-better", lambda: audit_money(
        hold=lambda bars, eb, s, sh: (100.0, 98.5, "stop", eb + 2)))
    # a synthetic month of minute bars with a volume column, for the DV canary and the walk-forward
    rng = np.random.default_rng(3)
    sess = [str(d.date()) for d in pd.bdate_range("2019-01-02", periods=60)]
    rows = []
    for s in sess:
        for mm in range(hm("09:30"), hm("16:00")):
            c = 100 + rng.normal()
            rows.append((s, R.hhmm(mm), c, c + 0.5, c - 0.5, c, 100 + rng.integers(0, 50)))
    x = pd.DataFrame(rows, columns=["session", "hhmm", "open", "high", "low", "close", "volume"])
    dv_canary(x, "09:45", sess[30:])
    must_raise("dv20-same-day", lambda: dv_canary(x, "09:45", sess[30:],
                                                  dv_fn=lambda dv: dv.rolling(DV_N, min_periods=DV_MIN).mean()))
    # the label equals the scorer; a flipped label fires
    D = pd.DataFrame({"root": ["ES", "ES", "NQ"], "s": [1, -1, 1], "entry": [100.0, 100.0, 200.0],
                      "exit": [101.0, 99.0, 199.0], "reason": ["target", "time", "time"]})
    D["net"] = D["s"] * (D["exit"] - D["entry"]) / D["entry"] * 1e4 - D["root"].map(COST_PTS) / D["entry"] * 1e4
    D["y"] = [1.0, 0.0, 0.0]
    audit_label_is_scorer(D, "V2-F")
    must_raise("label-not-scorer", lambda: audit_label_is_scorer(D.assign(y=[1.0, 1.0, 0.0]), "V2-F"))
    must_raise("net-not-scorer", lambda: audit_label_is_scorer(D.assign(net=D["net"] + 1.0), "V2-F"))
    # a synthetic cell for the walk-forward, the decision and its audits
    n_s = 700
    ss = [str(d.date()) for d in pd.bdate_range("2016-01-04", periods=n_s)]
    k = 2 * n_s
    Dw = pd.DataFrame({"session": np.repeat(ss, 2), "root": np.tile(["ES", "NQ"], n_s)})
    for f in FEATS:
        Dw[f] = rng.normal(size=k)
    Dw["nq"] = (Dw["root"] == "NQ").astype(float)
    Dw["px"] = 4000.0
    Dw["dist"] = rng.uniform(2, 20, k)
    Dw["net"] = rng.normal(0, 20, k) + 3 * Dw["gap_atr"]
    Dw["y"] = (Dw["net"] > 0).astype(float)
    Dw["reason"] = "close"
    Dw["gross"] = Dw["net"] + 3.0
    Dw["sh"] = rng.uniform(0.005, 0.01, k)
    cal = sorted(set(Dw["session"]))
    P = walk(Dw, "V2-C", FEATS, cal)
    R.audit_oos(P)
    audit_lag(P, "V2-C", Dw)
    must_raise("lag-second-implementation", lambda: audit_lag(P.assign(m_plus_s=P["m_plus_s"] * 10), "V2-C", Dw))
    Pf_w = walk(Dw, "V2-F", FEATS, cal)
    audit_lag(Pf_w, "V2-F", Dw)
    must_raise("lag-second-implementation-fade", lambda: audit_lag(Pf_w.assign(b_T=Pf_w["b_T"] + 5), "V2-F", Dw))
    audit_m_blind_to_test(Dw, "V2-F", FEATS, cal)
    # OA-A11's anchor: at a = 0, beta = -1 (a random walk) V2-F's EV is minus the cost on every row
    Pf = pd.DataFrame({"root": ["ES", "NQ", "ES"], "px": [4000.0, 15000.0, 4000.0], "dist": [5.0, 40.0, 30.0],
                       "p": [0.7, 0.2, 0.01], "a_T": 0.0, "b_T": -1.0})
    if not np.allclose(ev(Pf, "V2-F"), -cost_bp_t0(Pf), rtol=0, atol=1e-9):
        raise AssertionError("OA-A11: the random-walk anchor does not give EV = -cost")
    if decide(Pf, "V2-F", 0.0).any():
        raise AssertionError("OA-A11: the rule traded a random walk")
    audit_m_blind_to_test(Dw, "V2-C", FEATS, cal)

    real_walk = walk

    def leaky_walk(D: pd.DataFrame, cell: str, feats: tuple[str, ...], cal: list[str], max_windows: int | None = None):
        Pw = real_walk(D, cell, feats, cal, max_windows)
        return Pw.assign(m_plus_s=Pw["session"].map(D.groupby("session")["net"].mean()))  # reads the test rows

    must_raise("m-reads-test-rows", lambda: _with_walk(leaky_walk, lambda: audit_m_blind_to_test(Dw, "V2-C", FEATS, cal)))
    sessions = P.attrs["test_sessions"]
    trade = decide(P, "V2-C")
    main = score(P, "V2-C", sessions, trade)
    audit_right_quantity(P, trade, sessions, main)
    must_raise("net-equals-gross", lambda: audit_right_quantity(P.assign(gross=P["net"]), trade, sessions, main))
    must_raise("reversed-difference", lambda: audit_right_quantity(P, trade, sessions,
                                                                   {**main, "diff_mean_bp": -main["diff_mean_bp"]}))
    must_raise("budget", _budget_raise)
    audit_oracle(P, "V2-C", sessions)
    must_raise("oracle-sign", lambda: audit_oracle(P.assign(net=-P["net"].abs()), "V2-C", sessions))
    must_raise("walk-forward-overlap", _as_v2(R.windows_broken))

    def clean(xx: pd.DataFrame, t: str) -> pd.DataFrame:
        return R.window(xx, t).groupby("session")["close"].last().to_frame("px")

    def canary(xx: pd.DataFrame, t: str) -> pd.DataFrame:  # reads the bar STARTING at t: one minute too late
        return xx[xx["hhmm"] <= t].groupby("session")["close"].last().to_frame("px")

    R.leak_check(clean, x, "09:45", sess, rng)
    must_raise("leak-canary", _as_v2(lambda: R.leak_check(canary, x, "09:45", sess, rng)))
    fake = pd.DataFrame({"x": [1]})
    fake.attrs["oos_vs_joint_maxdiff"] = 0.0
    try:
        R.audit_oos(fake)
        raise AssertionError("the oos-equals-joint audit did not fire")
    except R.OpeningRunError:
        fired.append("oos-equals-joint-fit")
    # the simulators on known paths
    m = np.arange(hm("10:30"), hm("16:00"))
    flat = {"m": m, "o": np.full(len(m), 100.0), "h": np.full(len(m), 100.1), "l": np.full(len(m), 99.9),
            "c": np.full(len(m), 100.0)}
    e, xt, why, mx = sim_hold(flat, hm("10:30"), 1, 0.01)
    assert why == "close" and mx == hm("15:59"), (why, mx)
    e, xt, why, mx = sim_fade(flat, hm("10:30"), -1, 99.0)
    assert why == "time" and mx == hm("11:30"), (why, mx)
    e, xt, why, mx = sim_fade(flat, hm("10:30"), -1, 101.0)
    assert why == "cancel", why
    print(f"selftest: {len(fired)} audits fire on broken inputs ({', '.join(fired)}); the simulators check out")
    return 0


def _budget_raise() -> None:
    _as_v2(lambda: R.check_budget([f"f{i}" for i in range(12)]))()


def _with_walk(fn: Callable, body: Callable[[], Any]) -> Any:
    global walk
    keep = walk
    walk = fn
    try:
        return body()
    finally:
        walk = keep


# =============================================================================================== power / freeze / vault
def power() -> int:
    doc = json.loads(OUT.read_text(encoding="utf-8"))
    carried = doc["carried"]
    if not carried:
        raise SystemExit("no cell was carried: v2 closes without the vault (D655 s.6); nothing to power")
    S = pd.read_csv(SESS_CSV, encoding="utf-8", dtype={"session": str})
    rng = np.random.default_rng(SEED)
    alpha = 0.05 / len(carried)
    res: dict[str, Any] = {"spec": "D655 s.7", "n_sessions": POWER_N, "block": POWER_BLOCK, "draws": POWER_DRAWS,
                           "alpha_first_holm_step": alpha, "cells": {}}
    for cell in carried:
        x = S[S["cell"] == cell]
        pol, alw, trd = (x[c].to_numpy(float) for c in ("policy", "always", "traded"))
        nb = POWER_N // POWER_BLOCK
        starts_max = len(pol) - POWER_BLOCK
        rows = {}
        for se in POWER_EDGE:
            polx = pol - (1 - se) * pol.mean()
            cnt = {"PASS": 0, "FAIL": 0, "UNRESOLVED": 0}
            for _ in range(POWER_DRAWS):
                st = rng.integers(0, starts_max + 1, nb)
                ix = (st[:, None] + np.arange(POWER_BLOCK)[None, :]).ravel()
                if trd[ix].sum() < VAULT_MIN_TRADES:
                    cnt["UNRESOLVED"] += 1
                    continue
                t, _ = R.nw_t(polx[ix])
                ok = polx[ix].mean() > 0 and one_sided(t) < alpha and (polx[ix] - alw[ix]).mean() > 0
                cnt["PASS" if ok else "FAIL"] += 1
            rows[str(se)] = {k: v / POWER_DRAWS for k, v in cnt.items()}
        res["cells"][cell] = {"edge_kept": rows, "insample_policy_mean_bp": float(pol.mean()),
                              "insample_traded_per_390": float(trd.mean() * POWER_N)}
    POWER_OUT.write_text(R.dump(res), encoding="utf-8", newline="\n")
    for cell, v in res["cells"].items():
        print(cell, {k: round(r["PASS"], 3) for k, r in v["edge_kept"].items()})
    return 0


def freeze() -> int:
    doc = json.loads(OUT.read_text(encoding="utf-8"))
    if not doc["carried"]:
        raise SystemExit("no cell was carried: nothing to freeze (D655 s.6)")
    if FROZEN.exists():
        raise SystemExit("already frozen")
    f = {"spec": SPEC.name, "spec_sha256_lf": lf_sha(SPEC), "runner_sha256_lf": lf_sha(Path(__file__)),
         "carried": doc["carried"], "parameters": {"cells": CELLS, "break": BREAK, "edge_k": EDGE_K, "stop_k": STOP_K,
                                                    "dv": [DV_N, DV_MIN], "sigma_h": [SIGH_N, SIGH_MIN],
                                                    "features": list(FEATS), "train_test": [R.TRAIN, R.TEST],
                                                    "c_grid": list(C_GRID), "vault_min_trades": VAULT_MIN_TRADES,
                                                    "decision": "OA-A11: EV > 1 x cost, payoffs scaled per row"}}
    FROZEN.write_text(R.dump(f), encoding="utf-8", newline="\n")
    print(f"froze {FROZEN.name}: {f['carried']}")
    return 0


def vault(_: argparse.Namespace) -> int:
    raise SystemExit("REFUSED: D655 s.8's vault-input path (the bars and G with the cut moved, proved on the "
                     "in-sample first) is not built, and the vault is read only in the joint run on the principal's word")


# =============================================================================================== main
def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    for m in ("selftest", "dry-run", "run", "check", "power", "freeze", "vault"):
        g.add_argument(f"--{m}", action="store_true")
    ap.add_argument("--data-root", type=Path, default=REPO / "data",
                    help="where the gitignored inputs live; a worktree passes the main checkout's data/")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.power:
        return power()
    if a.freeze:
        return freeze()
    if a.vault:
        return vault(a)
    if a.dry_run:
        doc, trials, _ = build(a.data_root, dry=True)
        R.dump(doc)
        print(f"DRY RUN (synthetic bars and G): every path ran; {len(trials)} trials; "
              + "; ".join(f"{k}: policy {v['statistic']['policy_mean_bp']:+.3f} bp, diff {v['statistic']['diff_mean_bp']:+.3f}, "
                          f"traded {v['statistic']['traded_rows']}/{v['statistic']['always_rows']}"
                          for k, v in doc["cells"].items())
              + f"; {doc['runtime_min']} min; nothing written")
        return 0
    if a.run:
        if OUT.exists() or SESS_CSV.exists():
            raise SystemExit("the in-sample runs once (D655 s.6): its output already exists")
        if not (OD / "phase45.json").exists():
            raise SystemExit("REFUSED: D655 s.6 runs the in-sample after D645's Phase 4 run (phase45.json)")
        doc, trials, S = build(a.data_root)
        OUT.write_text(R.dump(doc), encoding="utf-8", newline="\n")
        S.to_csv(SESS_CSV, index=False, encoding="utf-8", lineterminator="\n", float_format="%.10g")
        log = TrialsCsv(OD / "trials.csv")
        for t in trials:
            log.append(t)
        print(f"wrote {OUT.name}, {SESS_CSV.name} and {len(trials)} trials in {doc['runtime_min']} min; "
              f"carried {doc['carried']}")
        return 0
    doc, _, _ = build(a.data_root)
    old = json.loads(OUT.read_text(encoding="utf-8"))
    doc["runtime_min"] = old["runtime_min"]
    if R.dump(doc) != OUT.read_text(encoding="utf-8"):
        raise SystemExit("CHECK FAILED: the rebuild differs from the committed output")
    print("CHECK: the rebuild equals the committed output")
    return 0


if __name__ == "__main__":
    sys.exit(main())
