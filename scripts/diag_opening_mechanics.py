"""D652 (opening v2) post-hoc diagnostic: mechanics, a statistical review, and the oracle edge. In-sample only
(nothing on or after 2025-03-01 is read: the runner's own sealed loader), written after D659, changes no verdict.

    uv run python scripts/diag_opening_v2_mechanics.py --data-root "C:/Users/O/Desktop/Projects/Backtest Framework/data"

Each cell is rebuilt with the runner's own functions (cell_rows, outcomes, walk, decide, score) and the rebuild must
reproduce data/opening/v2_insample.json's statistic exactly before anything else is computed. The two cells run in
two processes (the walk-forward's logistic fits are GIL-bound).

MECHANICS
  M1 a second implementation of every exit (never calls sim_fade / sim_hold): entry, exit and reason class must agree
  M2 the decision-to-entry minute: s x (entry / px_t0 - 1), the move the one-bar latency costs or gains
  M3 fill sensitivity: V2-F's target needs a trade-through of one tick (not a touch); V2-C's stop fills one tick worse
  M4 exit mix, minutes held, data gaps (time_gap / session_end) among traded rows
  M5 the cost line per trade (bp) by market, against the gross move
  M6 the EV forecast against the realised net, by EV decile (all rows, as if traded); per-window EV inputs
  M7 long against short
STATISTICS
  S1 circular block bootstrap (20 sessions, 10,000 draws) of the policy and diff means; the HAC t at lags 0/5/10/20
  S2 leave-one-year-out policy means
  S3 the vault's minimum detectable effect: 80% power at one-sided 0.025 (Holm's first step), SE scaled by
     sqrt(n_in / 390) from the in-sample HAC SE
ORACLE
  O1 perfect foresight of the cell's own label (trade exactly y = 1), per session and per trade
  O2 the information ladder: p_lambda = (1 - lambda) p + lambda y through the SAME EV rule; AUC, policy net, its t, and
     a normal-approximation vault power at each lambda
Writes data/opening/opening_v1_v2_diagnostic.json. v1 (run_v1, per t0) gets M1-M5, M7, S1-S3 and O2 through D645's own policy.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import roc_auc_score

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "opening" / "opening_v1_v2_diagnostic.json"
TICK = 0.25  # ES and NQ (and the micros)
VAULT_N = 390
BLOCK, N_BOOT = 20, 10_000
LAMBDAS = (0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0)
Z_A, Z_POW = stats.norm.isf(0.025), stats.norm.isf(0.2)


def load_v2() -> Any:
    sys.path.insert(0, str(REPO / "scripts"))
    s = importlib.util.spec_from_file_location("run_opening_v2", REPO / "scripts" / "run_opening_v2.py")
    V = importlib.util.module_from_spec(s)
    sys.modules["run_opening_v2"] = V
    s.loader.exec_module(V)
    return V


# ================================================================================ M1/M3: an independent exit engine
def exit_again(bars: dict[str, np.ndarray], eb: int, s: int, cell: str, target: float, sh: float,
               through_ticks: int = 0, stop_slip_ticks: int = 0) -> tuple[float, float, str]:
    """Written without sim_fade / sim_hold. Entry = close of the bar starting eb. Returns (entry, exit, class) with
    class in {target, stop, timed} (timed covers time / time_gap / session_end / close)."""
    m, o, h, lo, c = (bars[k] for k in ("m", "o", "h", "l", "c"))
    i0 = int(np.flatnonzero(m == eb)[0])
    entry = float(c[i0])
    after = np.arange(i0 + 1, len(m))
    if cell == "V2-F":
        if s * (target - entry) <= 0:
            return entry, entry, "cancel"
        inside = after[m[after] <= eb + 60]  # m rises, so this is the prefix the runner walks before its time stop
        lvl = target + s * through_ticks * TICK
        hit = inside[(h[inside] >= lvl) if s > 0 else (lo[inside] <= lvl)]
        if len(hit):
            return entry, target, "target"
        last = inside[-1] if len(inside) else (i0 if len(after) else len(m) - 1)
        return entry, float(c[last]), "timed"
    stop = entry * (1 - s * 1.5 * sh)
    hit = after[(lo[after] <= stop) if s > 0 else (h[after] >= stop)]
    if len(hit):
        i = int(hit[0])
        fill = o[i] if ((s > 0 and o[i] <= stop) or (s < 0 and o[i] >= stop)) else stop
        return entry, float(fill - s * stop_slip_ticks * TICK), "stop"
    return entry, float(c[-1]), "timed"


def cls(reason: str) -> str:
    return {"target": "target", "stop": "stop", "cancel": "cancel"}.get(reason, "timed")


# ================================================================================ statistics helpers
def block_boot(x: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    n = len(x)
    nb = math.ceil(n / BLOCK)
    starts = rng.integers(0, n, (N_BOOT, nb))
    idx = (starts[:, :, None] + np.arange(BLOCK)[None, None, :]).reshape(N_BOOT, -1)[:, :n] % n
    return x[idx].mean(axis=1)


def summarise_boot(x: np.ndarray, rng: np.random.Generator) -> dict[str, float]:
    bs = block_boot(x, rng)
    return {"mean": float(x.mean()), "ci95": [float(np.quantile(bs, 0.025)), float(np.quantile(bs, 0.975))],
            "p_mean_le_0": float((bs <= 0).mean())}


def power_normal(mean: float, se_vault: float) -> float:
    return float(stats.norm.sf(Z_A - mean / se_vault)) if se_vault > 0 else float("nan")


# ================================================================================ one cell
def run_cell(cell: str, data_root: str) -> dict[str, Any]:
    t_start = time.time()
    V = load_v2()
    R = V.R
    b, use, G = V.load_inputs(Path(data_root), False)
    tab = R.session_table(b, use)
    bars = R.bar_arrays(b)
    D = V.cell_rows(cell, tab, b, G)
    D = pd.concat([D, V.outcomes(D, cell, bars)], axis=1)
    D = D[D["reason"] != "missing"].reset_index(drop=True)
    cal = sorted(set(D["session"]))
    P = V.walk(D, cell, V.FEATS, cal)
    sessions = P.attrs["test_sessions"]
    trade = V.decide(P, cell)
    main = V.score(P, cell, sessions, trade)
    ref = json.loads((REPO / "data" / "opening" / "v2_insample.json").read_text(encoding="utf-8"))["cells"][cell]["statistic"]
    for k in ("policy_mean_bp", "diff_mean_bp", "traded_rows", "policy_t_hac"):
        if main[k] != ref[k]:
            raise SystemExit(f"{cell}: the rebuild's {k} {main[k]} differs from v2_insample.json's {ref[k]}")
    eb = R.hm(V.CELLS[cell])
    done = ~P["reason"].isin(["cancel", "missing"]).to_numpy()
    tr = trade & done
    s = P["s"].to_numpy(float)
    out: dict[str, Any] = {"cell": cell, "reproduces_v2_insample": True, "rows": int(len(P)), "traded": int(tr.sum()),
                           "sessions": len(sessions)}

    # M1 + M3
    mism, alt_rows = 0, []
    for i, rec in enumerate(P.itertuples(index=False)):
        key = (rec.root, rec.session)
        e, x, c = exit_again(bars[key], eb, int(rec.s), cell, float(rec.prior_close), float(rec.sh))
        if not (e == rec.entry and x == rec.exit and c == cls(rec.reason)):
            mism += 1
        e2, x2, c2 = exit_again(bars[key], eb, int(rec.s), cell, float(rec.prior_close), float(rec.sh),
                                through_ticks=1 if cell == "V2-F" else 0, stop_slip_ticks=1 if cell == "V2-C" else 0)
        g2 = rec.s * (x2 / e2 - 1) * 1e4 if c2 != "cancel" else 0.0
        alt_rows.append((g2, g2 - rec.cost_bp if c2 != "cancel" else 0.0, c2))
    out["M1_independent_exits"] = {"rows": int(len(P)), "mismatches": mism}
    A = pd.DataFrame(alt_rows, columns=["gross_alt", "net_alt", "cls_alt"], index=P.index)
    Pa = P.assign(gross=A["gross_alt"], net=A["net_alt"])
    alt = V.score(Pa, cell, sessions, trade)
    out["M3_fill_sensitivity"] = {
        "variant": "target needs a one-tick trade-through" if cell == "V2-F" else "stop fills one tick worse",
        "policy_mean_bp": alt["policy_mean_bp"], "policy_t_hac": alt["policy_t_hac"], "diff_mean_bp": alt["diff_mean_bp"],
        "always_mean_bp": alt["always_mean_bp"], "base_policy_mean_bp": main["policy_mean_bp"],
        "traded_targets_lost": int(((P["reason"] == "target") & (A["cls_alt"] != "target") & tr).sum())}

    # M2
    lat = s * (P["entry"].to_numpy(float) / P["px"].to_numpy(float) - 1) * 1e4
    out["M2_entry_minute_bp"] = {"traded_mean": float(np.nanmean(lat[tr])), "traded_median": float(np.nanmedian(lat[tr])),
                                 "all_mean": float(np.nanmean(lat[done])), "note": "s x (entry / px_t0 - 1); >0 favours the trade"}
    # M4
    t = P[tr]
    out["M4_exits"] = {"reasons_traded": t["reason"].value_counts().to_dict(),
                       "held_min_mean": float(t["held_min"].mean()), "held_min_median": float(t["held_min"].median()),
                       "reasons_all": P.loc[done, "reason"].value_counts().to_dict()}
    # M5
    out["M5_cost"] = {r: {"cost_bp_mean": float(g["cost_bp"].mean()), "gross_mean": float(g["gross"].mean()),
                          "abs_gross_mean": float(g["gross"].abs().mean()), "n": int(len(g))}
                      for r, g in t.groupby("root")}
    # M6
    e = V.ev(P, cell)
    q = pd.qcut(pd.Series(e[done]).rank(method="first"), 10, labels=False).to_numpy()
    g = pd.DataFrame({"q": q, "ev": e[done], "net": P.loc[done, "net"].to_numpy(float), "traded": trade[done]})
    dec = g.groupby("q").agg(ev=("ev", "mean"), net=("net", "mean"), n=("ev", "size"), traded=("traded", "mean"))
    X = sm_ols(e[done], P.loc[done, "net"].to_numpy(float))
    out["M6_ev_calibration"] = {"deciles": dec.round(4).reset_index().to_dict("records"),
                                "spearman_decile": float(dec["ev"].corr(dec["net"], method="spearman")),
                                "ols_net_on_ev": X,
                                "window_inputs": P.groupby("window")[["a_T", "b_T"] if cell == "V2-F" else
                                                                     ["m_plus_s", "m_minus_s"]].first()
                                .describe().round(4).to_dict()}
    # M7
    out["M7_long_short"] = {("long" if k > 0 else "short"): {
        "always_net_mean": float(g2.loc[done[g2.index], "net"].mean()),
        "traded_n": int(tr[g2.index].sum()),
        "traded_net_mean": float(g2.loc[tr[g2.index], "net"].mean()) if tr[g2.index].any() else None}
        for k, g2 in P.assign(_i=np.arange(len(P))).set_index("_i").groupby("s")}

    # S1-S3
    rng = np.random.default_rng(652)
    pol = V.per_session(P, np.where(tr, P["net"], 0.0), sessions).to_numpy()
    alw = V.per_session(P, np.where(done, P["net"], 0.0), sessions).to_numpy()
    out["S1_bootstrap"] = {"policy": summarise_boot(pol, rng), "diff": summarise_boot(pol - alw, rng),
                           "always": summarise_boot(alw, rng),
                           "hac_ladder_policy_t": {lag: R.nw_t(pol, lag)[0] for lag in (0, 5, 10, 20)},
                           "hac_ladder_diff_t": {lag: R.nw_t(pol - alw, lag)[0] for lag in (0, 5, 10, 20)},
                           "always_t_hac": R.nw_t(alw)[0]}
    ser = pd.Series(pol, index=sessions)
    yrs = sorted({x[:4] for x in sessions})
    out["S2_leave_one_year_out"] = {y: float(ser[~ser.index.str.startswith(y)].mean()) for y in yrs}
    out["S2_year_means"] = {y: float(ser[ser.index.str.startswith(y)].mean()) for y in yrs}
    se_in = R.nw_t(pol)[1]
    se_v = se_in * math.sqrt(len(sessions) / VAULT_N)
    out["S3_vault_mde"] = {"se_insample": se_in, "se_vault": se_v, "mde80_bp_per_session": (Z_A + Z_POW) * se_v,
                           "insample_mean": float(pol.mean()), "normal_power_at_insample_mean": power_normal(float(pol.mean()), se_v)}

    # O1 + O2
    y = P["y"].to_numpy(float)
    lab = ~np.isnan(y)
    ora = y == 1
    out["O1_perfect_foresight"] = {**V.score(P, cell, sessions, ora),
                                   "per_trade_net_mean": float(P.loc[ora & done, "net"].mean()),
                                   "per_trade_net_median": float(P.loc[ora & done, "net"].median()),
                                   "share_of_rows_y1": float(np.nanmean(y))}
    p = P["p"].to_numpy(float)
    ladder = []
    for lam in LAMBDAS:
        pl = np.where(lab, (1 - lam) * p + lam * np.nan_to_num(y), p)
        trl = V.ev(P, cell, pl) > V.cost_bp_t0(P)
        sc = V.score(P, cell, sessions, trl)
        pser = V.per_session(P, np.where(trl & done, P["net"], 0.0), sessions).to_numpy()
        se_l = R.nw_t(pser)[1] * math.sqrt(len(sessions) / VAULT_N)
        ladder.append({"lambda": lam, "auc": float(roc_auc_score(y[lab], pl[lab])), "traded": int((trl & done).sum()),
                       "policy_mean_bp": sc["policy_mean_bp"], "policy_t_hac": sc["policy_t_hac"],
                       "diff_mean_bp": sc["diff_mean_bp"],
                       "per_trade_net": float(P.loc[trl & done, "net"].mean()) if (trl & done).any() else None,
                       "vault_power_normal": power_normal(sc["policy_mean_bp"], se_l)})
    out["O2_information_ladder"] = ladder
    out["runtime_min"] = round((time.time() - t_start) / 60, 2)
    return out


# ================================================================================ v1: D645's final stage (S-A)
def sim1_again(bars: dict[str, np.ndarray], eb: int, D: int, stop_dist: float, flips: dict[int, bool] | None,
               slip_ticks: int = 0) -> tuple[float, float, str] | None:
    """D645's exit rule written without R.simulate: the window is the bars after entry up to the time stop; the first
    bar with an event exits, stop before flip before time inside a bar. None where D645 takes no trade."""
    m, o, h, lo, c = (bars[k] for k in ("m", "o", "h", "l", "c"))
    k0 = np.flatnonzero(m == eb)
    if len(k0) == 0 or D == 0 or not np.isfinite(stop_dist) or stop_dist <= 0:
        return None
    i0 = int(k0[0])
    entry = float(c[i0])
    stop = entry - D * stop_dist
    last = eb + 60
    after = np.arange(i0 + 1, len(m))
    win = after[m[after] <= last]
    st = (lo[win] <= stop) if D > 0 else (h[win] >= stop)
    fl = np.array([bool(flips and flips.get(int(mm) + 1)) for mm in m[win]], dtype=bool)
    tm = m[win] == last
    ev_ = np.flatnonzero(st | fl | tm)
    if len(ev_):
        i = int(win[ev_[0]])
        if st[ev_[0]]:
            thr = (o[i] <= stop) if D > 0 else (o[i] >= stop)
            return entry, float((o[i] if thr else stop) - D * slip_ticks * TICK), "stop"
        return entry, float(c[i]), "flip" if fl[ev_[0]] else "time"
    return entry, float(c[win[-1]] if len(win) else c[i0]), "gap_or_end"


def run_v1(t0: str, data_root: str) -> dict[str, Any]:
    t_start = time.time()
    V = load_v2()
    R = V.R
    b, use, _ = V.load_inputs(Path(data_root), False)
    tab = R.session_table(b, use)
    bars = R.bar_arrays(b)
    cal = sorted({s for r in R.ROOTS for s in tab[r].index if tab[r].loc[s, "usable"] and s >= "2016-01-04"})
    cols = list(R.S_A)
    P0 = R.walk_forward(R.dataset(tab, t0, t0), cols, cal)
    later = {t: R.walk_forward(R.dataset(tab, t, t0), cols, cal) for t in R.CHECKPOINTS
             if (t, t0) in R.PAIRS45 and R.hm(t0) < R.hm(t) <= R.hm(t0) + 1 + R.HOLD_MIN}
    T, o = R.decision_value(t0, P0, later, tab, bars)
    ref = json.loads((REPO / "data" / "opening" / "phase45.json").read_text(encoding="utf-8"))["final"]["H_O2"][t0]
    for k in ("policy_mean_net_bp", "diff_mean_bp", "traded_rows", "t_hac"):
        if o[k] != ref[k]:
            raise SystemExit(f"v1 {t0}: the rebuild's {k} {o[k]} differs from phase45.json's {ref[k]}")
    eb = R.hm(t0)
    out: dict[str, Any] = {"cell": f"V1 {t0} (S-A)", "reproduces_phase45": True, "rows": int(len(T)),
                           "traded": int(T["policy_traded"].sum()), "sessions": int(T["session"].nunique())}
    lk = {t: P.set_index(["session", "root"]) for t, P in later.items()}
    P0i = P0.set_index(["session", "root"])
    mism, rows = 0, []
    for rec in T.itertuples(index=False):
        d = tab[rec.root].loc[rec.session]
        rng_ = float(d[f"hi_{t0}"] - d[f"lo_{t0}"])
        cost = R.COST_USD[rec.root] / R.USD_PER_POINT[rec.root]
        d0 = int(P0i.loc[(rec.session, rec.root), "d0"])
        b1 = sim1_again(bars[(rec.root, rec.session)], eb, d0, 0.5 * rng_, None)
        mism += int(abs((R.pnl_bp(d0, b1[0], b1[1]) if b1 else 0.0) - rec.B1_gross) > 1e-9)
        row = {"session": rec.session, "root": rec.root, "state": rec.state, "side": rec.side, "px_move_bp": np.nan,
               "reason": None, "gross_alt": 0.0, "net_alt": 0.0, "cost_bp": np.nan}
        if rec.side != 0:
            flips = {R.hm(t): float(L.loc[(rec.session, rec.root), f"p_{rec.state}"]) < R.FLIP
                     for t, L in lk.items() if (rec.session, rec.root) in L.index}
            pr = sim1_again(bars[(rec.root, rec.session)], eb, rec.side, 0.5 * rng_, flips)
            mism += int(abs((R.pnl_bp(rec.side, pr[0], pr[1]) if pr else 0.0) - rec.policy_gross) > 1e-9)
            if pr is None:
                rows.append(row)
                continue
            e, x, why = pr
            e2, x2, _ = sim1_again(bars[(rec.root, rec.session)], eb, rec.side, 0.5 * rng_, flips, slip_ticks=1)
            g2 = R.pnl_bp(rec.side, e2, x2)
            row.update(reason=why, gross_alt=g2, net_alt=g2 - cost / e2 * 1e4, cost_bp=cost / e * 1e4,
                       px_move_bp=rec.side * (e / float(d[f"px_{t0}"]) - 1) * 1e4)
        rows.append(row)
    A = pd.DataFrame(rows)
    tr = T["policy_traded"].to_numpy() > 0
    out["M1_independent_exits"] = {"checked": int(len(T) + tr.sum()), "mismatches": mism,
                                   "note": "B1 on every row and the policy on every traded row, gross bp"}
    out["M2_entry_minute_bp"] = {"traded_mean": float(A.loc[tr, "px_move_bp"].mean()),
                                 "traded_median": float(A.loc[tr, "px_move_bp"].median())}
    alt = A.groupby("session")["net_alt"].mean()
    out["M3_fill_sensitivity"] = {"variant": "stop fills one tick worse", "policy_mean_bp": float(alt.mean()),
                                  "base_policy_mean_bp": o["policy_mean_net_bp"]}
    out["M4_exits"] = {"reasons_traded": A.loc[tr, "reason"].value_counts().to_dict(),
                       "states_traded": A.loc[tr, "state"].value_counts().to_dict()}
    out["M5_cost"] = {r: {"cost_bp_mean": float(g["cost_bp"].mean()),
                          "gross_mean": float(T.loc[g.index, "policy_gross"].mean()), "n": int(len(g))}
                      for r, g in A[tr].groupby("root")}
    out["M7_long_short"] = {("long" if k > 0 else "short"): {"n": int(len(g)), "net_mean": float(T.loc[g.index, "policy"].mean())}
                            for k, g in A[tr].groupby("side")}
    per = T.groupby("session")[["policy", "B1"]].mean()
    pol = per["policy"].to_numpy()
    best = o["best_baseline"]
    diff = (per["policy"] - T.groupby("session")[best].mean()).to_numpy()
    rng = np.random.default_rng(645)
    out["S1_bootstrap"] = {"policy": summarise_boot(pol, rng), "diff_vs_best": summarise_boot(diff, rng),
                           "hac_ladder_policy_t": {lag: R.nw_t(pol, lag)[0] for lag in (0, 5, 10, 20)},
                           "per_traded_row": {"n": int(tr.sum()), "mean": float(T.loc[tr, "policy"].mean()),
                                              "median": float(T.loc[tr, "policy"].median()),
                                              "t": float(stats.ttest_1samp(T.loc[tr, "policy"], 0).statistic)}}
    ser = pd.Series(pol, index=per.index)
    yrs = sorted({x[:4] for x in per.index})
    out["S2_leave_one_year_out"] = {y: float(ser[~ser.index.str.startswith(y)].mean()) for y in yrs}
    se_in = R.nw_t(pol)[1]
    se_v = se_in * math.sqrt(len(pol) / VAULT_N)
    out["S3_vault_mde"] = {"se_insample": se_in, "se_vault": se_v, "mde80_bp_per_session": (Z_A + Z_POW) * se_v,
                           "insample_mean": float(pol.mean())}
    # O2: the information ladder through D645's own policy (argmax >= THETA, RANGE sits out, the flip exits)
    def blend(P: pd.DataFrame, lam: float) -> pd.DataFrame:
        return P.assign(**{f"p_{c}": (1 - lam) * P[f"p_{c}"] + lam * (P["label"] == c).astype(float) for c in R.CLASSES})
    ladder = []
    for lam in LAMBDAS:
        Pl = blend(P0, lam)
        Tl, ol = R.decision_value(t0, Pl, {t: blend(L, lam) for t, L in later.items()}, tab, bars)
        trl = Tl["policy_traded"] > 0
        pser = Tl.groupby("session")["policy"].mean().to_numpy()
        se_l = R.nw_t(pser)[1] * math.sqrt(len(pser) / VAULT_N)
        ladder.append({"lambda": lam,
                       "auc": {c: float(roc_auc_score((Pl["label"] == c).astype(int), Pl[f"p_{c}"])) for c in R.CLASSES},
                       "traded": int(trl.sum()), "states": Tl.loc[trl, "state"].value_counts().to_dict(),
                       "policy_mean_bp": ol["policy_mean_net_bp"], "policy_gross_bp": ol["policy_mean_gross_bp"],
                       "t_hac": R.nw_t(pser)[0], "per_trade_net": float(Tl.loc[trl, "policy"].mean()) if trl.any() else None,
                       "vault_power_normal": power_normal(ol["policy_mean_net_bp"], se_l)})
    out["O2_information_ladder"] = ladder
    out["runtime_min"] = round((time.time() - t_start) / 60, 2)
    return out


def sm_ols(x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    import statsmodels.api as sm
    f = sm.OLS(y, sm.add_constant(x)).fit(cov_type="HC1")
    return {"intercept": float(f.params[0]), "slope": float(f.params[1]), "slope_t": float(f.tvalues[1]), "n": int(len(x))}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    t0 = time.time()
    jobs = {"V2-F": (run_cell, "V2-F"), "V2-C": (run_cell, "V2-C"), "V1 09:45": (run_v1, "09:45"),
            "V1 10:00": (run_v1, "10:00")}
    with ProcessPoolExecutor(max_workers=len(jobs)) as ex:
        futs = {k: ex.submit(fn, arg, str(a.data_root)) for k, (fn, arg) in jobs.items()}
        res = {k: f.result() for k, f in futs.items()}
    wall = time.time() - t0
    work = sum(r["runtime_min"] for r in res.values()) * 60
    doc = {"spec": "post hoc on D658 (v1, the agent model's final stage S-A) and D659 (v2); in-sample only",
           "cells": res, "speed": {"wall_s": round(wall, 1), "sum_item_s": round(work, 1), "parallel_x": round(work / wall, 2)}}
    OUT.write_text(json.dumps(doc, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(f"[SPEED] {work:.0f} s of work in {wall:.0f} s wall ({work / wall:.2f}x on {len(jobs)} processes)")
    for c, r in res.items():
        print(c, "M1 mismatches", r["M1_independent_exits"]["mismatches"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
