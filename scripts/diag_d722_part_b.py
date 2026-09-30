"""D722 Part B: which variable, known before the trade, carries each object's 2022? Spec: s.3 (and s.2's u) of
docs/decisions/D722-DIAG-PRE-REG-why-2022-scale-regime-or-one-bet.md (f25e4726) with Amendment D722-A1 (7880c5a0).

    uv run python scripts/diag_d722_part_b.py --selftest   # the real-data gates pass (no statistic printed), then every canary RAISES
    uv run python scripts/diag_d722_part_b.py --run        # run-once: refuses if data/diag_d722_part_b.json exists

INPUTS (Phase 0, imported, never edited): diag_d722_lines.load_lines() (per trade) and diag_d722_conditioners.load_conditioners()
(per (root, session), every variable known before the session; see that module's docstring). Both are sealed at 2024-01-01 and this
runner re-asserts the seal on every frame it touches.

THE OUTCOME (s.2). u_i = g_i / (usd_pp_i * entry_price_i * sig20(root, session_i) * sqrt(hold_min_i / 390)), g = gross_usd.

THE OBJECTS AND FAMILIES (s.3; the Holm family is per object).
  B-base  K2_ES, K2_NQ     X1 X2 X3 X4 X5 X6 X7 X8 X9 X10 X11
  B-lines L1, L2           X1 X2 X3 X4 X5 X6 X7 X8 X9 X10 X11
          L3               the same less X3 (L3 is gated on short gamma: X3 == 1 on every L3 trade; "not read", out of the family)
          L4 (HO)          X1 X4 X5 X6 X7 X8 X9 X12
  X7 = r60 x side (the trade's side). X8 on HO carries EIA_WPSR (the panel's X8). Reported BESIDE, not in any family (A1 rulings 2, 3):
  X6_15m and X9_record, with their unadjusted p. K1 is not a Part B object.

EACH (object, variable) CELL (s.3):
  0. The cell's subset is the object's trades with finite X. Trades with NaN X (X2, X3 and X10 have gaps; X10 is NaN before
     2019-05) enter neither the fit nor the prediction nor the cell's means; n used is reported per year.
  1. Leave one year out: for each year Y of the object, OLS u = a + b X on the subset's trades of the OTHER years (2022 included when
     Y != 2022), and u_hat_Y = mean over Y's subset trades of a + b X_i, reported against the subset's actual mean u_Y and n. A year
     with no finite X has no prediction (null). A second implementation (centered two-pass sums over plain Python lists, the held-out
     year chosen by its own string compare) must agree to 1e-9 relative on every year of every cell, and the training count must be
     the subset total less Y's count: a fit that sees its own held-out year raises.
  2. phi = (u_hat_2022 - ubar_R) / (ubar_2022 - ubar_R), ubar_R = the pooled mean u over the subset's non-2022 trades, ubar_2022 over
     its 2022 trades (the cell's subset). Where the subset's own excess ubar_2022 - ubar_R <= 0 while the object has one, phi carries no
     explained share of an excess and the cell's reading is NO, flagged `subset_excess_le_0` (a ruling the orchestrator is asked for).
  3. The slope's t from the fit EXCLUDING 2022 (the Y = 2022 fit of step 1), SEs clustered by ISO week of the session (isoyear, week):
     CR1, V = c (X'X)^-1 [sum_g S_g S_g'] (X'X)^-1, S_g = sum_{i in g} x_i e_i, c = G/(G-1) * (N-1)/(N-K) (Stata's small-sample
     correction; K = 2 here). A second implementation (the simple-regression identity Var(b) = c sum_g (sum_{i in g} (x_i - xbar) e_i)^2
     / Sxx^2, ISO weeks from datetime.date.isocalendar, plain loops) must agree to 1e-9 relative. p two-sided from the normal:
     erfc(|t| / sqrt 2). Holm step-down across the object's family; a second implementation (the sequential rejection at 0.05) must
     give the same rejected set as Holm p < 0.05. The iid SE is reported beside.
  4. Readings: EXPLAINS if Holm p < 0.05 and phi >= 0.5; PARTIAL if Holm p < 0.05 and 0.2 <= phi < 0.5; NO otherwise.
  5. The joint model: every family variable with Holm p < 0.05, fitted together (OLS, intercept) outside 2022 on trades with ALL of
     them finite; u_hat_joint,2022 = the mean fitted value over that subset's 2022 trades; residual share = (ubar_2022 -
     u_hat_joint,2022) / (ubar_2022 - ubar_R) on that subset. None passing: the intercept alone (residual share 1).
  Object reading: N/A if ubar_2022 <= ubar_R over ALL the object's trades (no excess); UNEXPLAINED if no cell EXPLAINS and the joint
  model's residual share >= 1/2; otherwise NOT_UNEXPLAINED, with the EXPLAINS and PARTIAL cells named. (s.3 declares only N/A and
  UNEXPLAINED at object level; NOT_UNEXPLAINED is their complement, not a new reading.)
  Prediction 10 (s.8; the orchestrator's ruling before --run): SCORED on `prediction_10_ex2022`, 2018's mean prediction from a fit
  that EXCLUDES BOTH 2018 AND 2022 (same finite-X subset rule), against the cell's ubar_R, with n_train; a second implementation
  must agree and n_train must equal the subset total less 2018's and 2022's counts. The literal LOYO 2018 prediction (2022 in its
  training set) is reported beside it, not scored.

THE RUNNER'S ASSERTIONS (s.7 and CLAUDE.md), all run on the real data by both --selftest and --run, each shown to RAISE in --selftest:
  the seal (every trade, every panel row, the joined frame: no session >= 2024-01-01); the join (the panel value at the trade's own
  (root, session), re-derived by a dict lookup, exact); u (a second implementation in plain floats, 1e-12 relative; sign(u) == sign(g);
  u differs from the un-normalised and the un-horizon-scaled quantity); X7 (== r60 where long, -r60 where short, exactly; differs from
  r60 wherever the object has a short); LOYO (the second implementation and the training count); the cluster SE (the second
  implementation; on a synthetic with within-week correlation clustered SE > 1.5 x iid SE); Holm (a hand example, and the sequential
  second implementation); a family variable with no variance outside 2022 raises (X3 on L3 is excluded, not fitted).

AGGREGATES ONLY in data/diag_d722_part_b.json: coefficients, SEs, means by year and counts. No per-date row (X3 and L3 derive from
SqueezeMetrics GEX). Wall: loads ~2 s, analysis a few seconds single-threaded (~90 cells of tiny OLS); nothing here is worth a fan-out.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import math
import sys
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

OUT = REPO / "data" / "diag_d722_part_b.json"
SPEC = ("docs/decisions/D722-DIAG-PRE-REG-why-2022-scale-regime-or-one-bet.md s.3 (f25e4726) with Amendment D722-A1 "
        "(7880c5a0)")
CUT = "2024-01-01"
PRIMARY = "2022"
ALPHA = 0.05
REL = 1e-9
FAM_INDEX = ("X1", "X2", "X3", "X4", "X5", "X6", "X7", "X8", "X9", "X10", "X11")
FAM_HO = ("X1", "X4", "X5", "X6", "X7", "X8", "X9", "X12")
BESIDE = ("X6_15m", "X9_record")
OBJECTS: dict[str, dict[str, Any]] = {
    "K2_ES": {"group": "B-base", "root": "ES", "family": FAM_INDEX, "not_read": ()},
    "K2_NQ": {"group": "B-base", "root": "NQ", "family": FAM_INDEX, "not_read": ()},
    "L1": {"group": "B-lines", "root": "ES", "family": FAM_INDEX, "not_read": ()},
    "L2": {"group": "B-lines", "root": "NQ", "family": FAM_INDEX, "not_read": ()},
    "L3": {"group": "B-lines", "root": "ES", "family": tuple(v for v in FAM_INDEX if v != "X3"),
           "not_read": ("X3",)},
    "L4": {"group": "B-lines", "root": "HO", "family": FAM_HO, "not_read": ()},
}
PANEL_VARS = ("sig20", "X1", "X2", "X3", "X4", "X5", "X6", "X6_15m", "r60", "X8", "X9", "X9_record", "X10", "X11", "X12")


class D722BError(AssertionError):
    """A Part B gate refused. Raising, never a warning."""


def P(*a: Any) -> None:
    print(*a, flush=True)


def need(cond: bool, msg: str) -> None:
    if not cond:
        raise D722BError(msg)


# ================================================================================ seal, join, u, X7
def seal(dates, what: str) -> None:
    d = pd.Series(np.asarray(dates, dtype=object)).astype(str).str[:10]
    if len(d) and (d >= CUT).any():
        raise D722BError(f"[SEAL] {what}: a row dated {d[d >= CUT].min()} is at or after {CUT}")


def outcome_u(g, usd_pp, price, sig20, hold, wrong: str | None = None) -> np.ndarray:
    g, usd_pp, price, sig20, hold = (np.asarray(v, dtype=float) for v in (g, usd_pp, price, sig20, hold))
    if wrong == "no_sig20":
        return g / (usd_pp * price * np.sqrt(hold / 390.0))
    if wrong == "no_hold":
        return g / (usd_pp * price * sig20)
    return g / (usd_pp * price * sig20 * np.sqrt(hold / 390.0))


def make_x7(r60, side, wrong: str | None = None) -> np.ndarray:
    r60 = np.asarray(r60, dtype=float)
    if wrong == "noside":
        return r60.copy()
    return r60 * np.asarray(side, dtype=float)


def attach(lines: pd.DataFrame, panel: pd.DataFrame, shift: int = 0, wrong_u: str | None = None,
           wrong_x7: str | None = None) -> pd.DataFrame:
    """The Part B frame: the objects' trades, each with the panel's row at its own (root, session), u, X7, year and ISO week.
    `shift`, `wrong_u` and `wrong_x7` exist only so the self-test can prove the audits fire."""
    seal(lines["session"], "trade table")
    seal(panel.index.get_level_values("session"), "conditioner panel")
    d = lines[lines["line"].isin(list(OBJECTS))].reset_index(drop=True).copy()
    for c in ("line", "root", "session"):
        d[c] = d[c].astype(str)
    pan = panel
    if shift:
        pan = panel.groupby(level="root", group_keys=False).shift(shift)
    key = pd.MultiIndex.from_arrays([d["root"], d["session"]])
    need(bool(key.isin(panel.index).all()), "[JOIN] a trade's (root, session) is missing from the panel")
    m = pan.reindex(key)
    for c in PANEL_VARS:
        d[c] = m[c].to_numpy(dtype=float)
    d["u"] = outcome_u(d["gross_usd"], d["usd_pp"], d["entry_price"], d["sig20"], d["hold_min"], wrong=wrong_u)
    d["X7"] = make_x7(d["r60"], d["side"], wrong=wrong_x7)
    d["year"] = d["session"].str[:4]
    iso = pd.to_datetime(d["session"]).dt.isocalendar()
    d["week"] = (iso["year"].astype(np.int64) * 100 + iso["week"].astype(np.int64)).to_numpy()
    seal(d["session"], "Part B frame")
    return d


def _same(a: float, b: float) -> bool:
    return (math.isnan(a) and math.isnan(b)) or a == b


def join_audit(d: pd.DataFrame, panel: pd.DataFrame) -> int:
    """A second implementation of the join: a dict of the panel's rows, looked up per trade; every variable exact (NaN == NaN)."""
    cols = list(PANEL_VARS)
    look = {k: tuple(float(x) for x in row) for k, row in zip(panel.index, panel[cols].to_numpy(dtype=float))}
    n = 0
    for r, s, *vals in zip(d["root"], d["session"], *(d[c] for c in cols)):
        want = look[(r, s)]
        for c, got, w in zip(cols, vals, want):
            if not _same(float(got), w):
                raise D722BError(f"[JOIN] {r} {s} {c}: the frame holds {got}, the panel's own row {w}")
            n += 1
    return n


def u_audit(d: pd.DataFrame) -> int:
    n = 0
    for g, pp, px, sg, h, u in zip(d["gross_usd"], d["usd_pp"], d["entry_price"], d["sig20"], d["hold_min"], d["u"]):
        need(pp > 0 and px > 0 and sg > 0 and h > 0, "[U] a non-positive denominator term")
        want = float(g) / (float(pp) * float(px) * float(sg) * math.sqrt(float(h) / 390.0))
        need(math.isfinite(float(u)), "[U] a non-finite u")
        need(abs(float(u) - want) <= 1e-12 * max(1.0, abs(want)), f"[U] u = {u} against the second implementation {want}")
        need(np.sign(float(u)) == np.sign(float(g)), "[U] sign(u) != sign(g): a favourable move must score positive")
        n += 1
    for wrong in ("no_sig20", "no_hold"):
        alt = outcome_u(d["gross_usd"], d["usd_pp"], d["entry_price"], d["sig20"], d["hold_min"], wrong=wrong)
        need(not np.allclose(alt, d["u"].to_numpy(), rtol=1e-6, atol=0.0), f"[U] u equals the {wrong} quantity: right-quantity failed")
    return n


def x7_audit(d: pd.DataFrame) -> int:
    n = 0
    for obj, g in d.groupby("line"):
        side = g["side"].to_numpy()
        need(bool(np.isin(side, (-1, 1)).all()), f"[X7] {obj}: a side outside {{-1, +1}}")
        want = np.where(side > 0, g["r60"].to_numpy(), -g["r60"].to_numpy())
        x7 = g["X7"].to_numpy()
        need(bool(np.array_equal(x7, want, equal_nan=True)), f"[X7] {obj}: X7 != r60 (long) / -r60 (short)")
        short = side < 0
        if short.any():
            fin = short & np.isfinite(g["r60"].to_numpy()) & (g["r60"].to_numpy() != 0)
            need(bool(fin.any()) and bool((x7[fin] != g["r60"].to_numpy()[fin]).all()),
                 f"[X7] {obj}: X7 equals r60 on short trades: the side was not applied (right-quantity)")
        n += len(g)
    return n


# ================================================================================ OLS, clustered SE, Holm
def ols(y: np.ndarray, X: np.ndarray) -> np.ndarray:
    beta, _, rank, _ = np.linalg.lstsq(X, y, rcond=None)
    need(rank == X.shape[1], f"[OLS] rank {rank} < {X.shape[1]}: a regressor has no variance on the fit's subset")
    return beta


def cluster_vcov(X: np.ndarray, e: np.ndarray, cl: np.ndarray) -> tuple[np.ndarray, int]:
    """CR1: c (X'X)^-1 [sum_g S_g S_g'] (X'X)^-1, S_g = sum_{i in g} x_i e_i, c = G/(G-1) (N-1)/(N-K)."""
    n, k = X.shape
    codes, inv = np.unique(cl, return_inverse=True)
    G = len(codes)
    need(G >= 2, "[CLUSTER] fewer than two clusters")
    S = np.zeros((G, k))
    np.add.at(S, inv, X * e[:, None])
    bread = np.linalg.inv(X.T @ X)
    c = G / (G - 1) * (n - 1) / (n - k)
    return c * bread @ (S.T @ S) @ bread, G


def iid_vcov(X: np.ndarray, e: np.ndarray) -> np.ndarray:
    n, k = X.shape
    return float(e @ e) / (n - k) * np.linalg.inv(X.T @ X)


def iso_week_loop(sessions) -> list[int]:
    out = []
    for s in sessions:
        y, w, _ = _dt.date.fromisoformat(str(s)).isocalendar()
        out.append(y * 100 + w)
    return out


def slope_se_loop(x: list[float], y: list[float], sessions: list[str], a: float, b: float) -> float:
    """Second implementation of the clustered slope SE of a simple regression: c sum_g (sum_{i in g} (x_i - xbar) e_i)^2 / Sxx^2."""
    n = len(x)
    xbar = sum(x) / n
    sxx = sum((xi - xbar) ** 2 for xi in x)
    acc: dict[int, float] = {}
    for xi, yi, w in zip(x, y, iso_week_loop(sessions)):
        acc[w] = acc.get(w, 0.0) + (xi - xbar) * (yi - a - b * xi)
    G = len(acc)
    c = G / (G - 1) * (n - 1) / (n - 2)
    return math.sqrt(c * sum(v * v for v in acc.values()) / (sxx * sxx))


def p_normal(t: float) -> float:
    return math.erfc(abs(t) / math.sqrt(2.0))


def holm(p: list[float], broken: str | None = None) -> list[float]:
    """Holm step-down adjusted p: sorted ascending, adj_(i) = max_{j<=i} min(1, (m - j + 1) p_(j)), returned in the input order."""
    p = np.asarray(p, dtype=float)
    need(bool(np.isfinite(p).all()), "[HOLM] a family p is not finite")
    m = len(p)
    order = np.argsort(p, kind="stable")
    mult = np.arange(m, 0, -1, dtype=float)
    if broken == "bonferroni":
        mult = np.full(m, float(m))
    raw = np.minimum(1.0, mult * p[order])
    adj_sorted = raw if broken == "no_stepdown_max" else np.maximum.accumulate(raw)
    adj = np.empty(m)
    adj[order] = adj_sorted
    return [float(v) for v in adj]


def holm_sequential(p: list[float], alpha: float = ALPHA) -> set[int]:
    """Second implementation: reject the smallest p while p_(i) < alpha / (m - i + 1); stop at the first that does not."""
    idx = sorted(range(len(p)), key=lambda i: (p[i], i))
    m, rej = len(p), set()
    for r, i in enumerate(idx):
        if p[i] < alpha / (m - r):
            rej.add(i)
        else:
            break
    return rej


def holm_gate(p: list[float], adj: list[float], impl: Callable[[list[float]], list[float]] = holm) -> None:
    """The family's adjusted p against the sequential second implementation, and `impl` (the Holm in use) on a hand example."""
    need({i for i, v in enumerate(adj) if v < ALPHA} == holm_sequential(p),
         "[HOLM] the adjusted p's rejected set differs from the sequential step-down")
    hand_p = [0.01, 0.04, 0.03, 0.005]
    want = [0.03, 0.06, 0.06, 0.02]   # sorted .005x4=.02, .01x3=.03, .03x2=.06, .04x1=.04 -> running max .06
    got = impl(hand_p)
    need(all(abs(g - w) < 1e-15 for g, w in zip(got, want)), f"[HOLM] the hand example gives {got}, not {want}")


# ================================================================================ LOYO
def loyo(u: np.ndarray, x: np.ndarray, years: np.ndarray, leak: bool = False) -> dict[str, dict[str, Any]]:
    """For each year Y: OLS on the other years' finite-X trades, the mean prediction over Y's finite-X trades. `leak` (self-test only)
    fits on every year, Y included."""
    fin = np.isfinite(x)
    out: dict[str, dict[str, Any]] = {}
    for Y in sorted(set(years.tolist())):
        tr = fin & ((years != Y) | leak)
        te = fin & (years == Y)
        rec: dict[str, Any] = {"n_test": int(te.sum()), "n_train": int(tr.sum()),
                               "ubar_actual": float(u[te].mean()) if te.any() else None}
        if te.any() and np.var(x[tr]) > 0:
            X = np.column_stack([np.ones(tr.sum()), x[tr]])
            a, b = ols(u[tr], X)
            rec.update(a=float(a), b=float(b), uhat=float(np.mean(a + b * x[te])))
        else:
            rec.update(a=None, b=None, uhat=None)
        out[Y] = rec
    return out


def loyo_audit(u: np.ndarray, x: np.ndarray, sessions: np.ndarray, res: dict[str, dict[str, Any]]) -> int:
    """Second implementation: plain lists, the held-out year chosen by its own string compare, centered two-pass sums."""
    rows = [(str(s)[:4], float(xi), float(ui)) for s, xi, ui in zip(sessions, x, u) if math.isfinite(float(xi))]
    n_fin = len(rows)
    sd_u = float(np.std(u)) or 1.0
    k = 0
    for Y, rec in res.items():
        tr = [(xi, ui) for yy, xi, ui in rows if yy != Y]
        te = [xi for yy, xi, ui in rows if yy == Y]
        need(rec["n_train"] == len(tr) == n_fin - len(te),
             f"[LOYO] {Y}: the fit used {rec['n_train']} trades; the other years hold {len(tr)}: the held-out year leaked")
        need(rec["n_test"] == len(te), f"[LOYO] {Y}: test count {rec['n_test']} != {len(te)}")
        if not te:
            need(rec["uhat"] is None, f"[LOYO] {Y}: a prediction for a year with no finite X")
            continue
        xb = sum(p[0] for p in tr) / len(tr)
        ub = sum(p[1] for p in tr) / len(tr)
        sxx = sum((p[0] - xb) ** 2 for p in tr)
        if sxx == 0.0:
            need(rec["uhat"] is None, f"[LOYO] {Y}: a prediction from a constant X")
            continue
        b = sum((p[0] - xb) * (p[1] - ub) for p in tr) / sxx
        want = ub + b * (sum(te) / len(te) - xb)
        need(rec["uhat"] is not None and abs(rec["uhat"] - want) <= REL * max(abs(want), sd_u),
             f"[LOYO] {Y}: u_hat {rec['uhat']} against the second implementation {want}")
        k += 1
    return k


P10_TARGET, P10_EXCLUDE = "2018", ("2018", "2022")


def pred_ex2022(u: np.ndarray, x: np.ndarray, years: np.ndarray, leak: bool = False) -> dict[str, Any]:
    """Prediction 10 (orchestrator's ruling): 2018's mean prediction from a fit that EXCLUDES BOTH 2018 and 2022 (finite-X subset).
    `leak` (self-test only) keeps 2022 in the fit."""
    fin = np.isfinite(x)
    drop = (years == P10_TARGET) | ((years == PRIMARY) & (not leak))
    tr = fin & ~drop
    te = fin & (years == P10_TARGET)
    rec: dict[str, Any] = {"n_train": int(tr.sum()), "n_test": int(te.sum()), "uhat_2018": None}
    if te.any() and tr.sum() > 2 and np.var(x[tr]) > 0:
        a, b = ols(u[tr], np.column_stack([np.ones(tr.sum()), x[tr]]))
        rec["uhat_2018"] = float(np.mean(a + b * x[te]))
    return rec


def pred_ex2022_audit(u: np.ndarray, x: np.ndarray, sessions: np.ndarray, rec: dict[str, Any]) -> int:
    """Second implementation: plain lists, the years chosen by string compare; the training count must be the subset total less
    2018's and 2022's counts, and u_hat_2018 must agree to 1e-9 relative."""
    rows = [(str(s)[:4], float(xi), float(ui)) for s, xi, ui in zip(sessions, x, u) if math.isfinite(float(xi))]
    n18 = sum(1 for r in rows if r[0] == P10_TARGET)
    n22 = sum(1 for r in rows if r[0] == PRIMARY)
    tr = [(xi, ui) for yy, xi, ui in rows if yy not in P10_EXCLUDE]
    te = [xi for yy, xi, ui in rows if yy == P10_TARGET]
    need(rec["n_train"] == len(tr) == len(rows) - n18 - n22,
         f"[P10] the ex-2022 fit used {rec['n_train']} trades; the subset less 2018 and 2022 holds {len(rows) - n18 - n22}")
    need(rec["n_test"] == len(te), f"[P10] test count {rec['n_test']} != {len(te)}")
    if not te or len(tr) <= 2:
        need(rec["uhat_2018"] is None, "[P10] a prediction with no 2018 subset or no fit")
        return 0
    xb = sum(p[0] for p in tr) / len(tr)
    ub = sum(p[1] for p in tr) / len(tr)
    sxx = sum((p[0] - xb) ** 2 for p in tr)
    if sxx == 0.0:
        need(rec["uhat_2018"] is None, "[P10] a prediction from a constant X")
        return 0
    b = sum((p[0] - xb) * (p[1] - ub) for p in tr) / sxx
    want = ub + b * (sum(te) / len(te) - xb)
    sd_u = float(np.std(u)) or 1.0
    need(rec["uhat_2018"] is not None and abs(rec["uhat_2018"] - want) <= REL * max(abs(want), sd_u),
         f"[P10] u_hat_2018 {rec['uhat_2018']} against the second implementation {want}")
    return 1


# ================================================================================ cells, joint, readings
def cell_reading(p_holm: float | None, phi: float | None, subset_excess_pos: bool) -> str:
    if p_holm is None or phi is None or not subset_excess_pos or not (p_holm < ALPHA):
        return "NO"
    if phi >= 0.5:
        return "EXPLAINS"
    if phi >= 0.2:
        return "PARTIAL"
    return "NO"


def cell(d: pd.DataFrame, var: str, gates: dict[str, int], leak: bool = False, leak_p10: bool = False) -> dict[str, Any]:
    u = d["u"].to_numpy()
    x = d[var].to_numpy(dtype=float)
    years = d["year"].to_numpy()
    sessions = d["session"].to_numpy()
    fin = np.isfinite(x)
    lo = loyo(u, x, years, leak=leak)
    gates["loyo_years_checked"] += loyo_audit(u, x, sessions, lo)
    p10 = pred_ex2022(u, x, years, leak=leak_p10)
    gates["p10_ex2022_checked"] = gates.get("p10_ex2022_checked", 0) + pred_ex2022_audit(u, x, sessions, p10)
    R = fin & (years != PRIMARY)
    T = fin & (years == PRIMARY)
    need(R.sum() > 2 and T.any(), f"[CELL] {var}: no fit or no 2022 on the finite subset")
    need(float(np.var(x[R])) > 0.0, f"[CELL] {var}: X has no variance outside 2022 on this object (a definition that cannot be fitted)")
    ubar_R, ubar_22 = float(u[R].mean()), float(u[T].mean())
    uhat_22 = lo[PRIMARY]["uhat"]
    den = ubar_22 - ubar_R
    phi = (uhat_22 - ubar_R) / den if den != 0 else None
    X = np.column_stack([np.ones(R.sum()), x[R]])
    a, b = ols(u[R], X)
    need(abs(a - lo[PRIMARY]["a"]) <= REL * max(1.0, abs(a)) and abs(b - lo[PRIMARY]["b"]) <= REL * max(1.0, abs(b)),
         "[CELL] the primary fit differs from LOYO's 2022 fit")
    e = u[R] - (a + b * x[R])
    V, G = cluster_vcov(X, e, d["week"].to_numpy()[R])
    se = math.sqrt(V[1, 1])
    se_loop = slope_se_loop(x[R].tolist(), u[R].tolist(), sessions[R].tolist(), float(a), float(b))
    need(abs(se - se_loop) <= REL * se_loop, f"[CLUSTER] {var}: the sandwich SE {se} != the loop implementation {se_loop}")
    gates["cluster_se_checked"] += 1
    se_iid = math.sqrt(iid_vcov(X, e)[1, 1])
    t = b / se
    yrs = sorted(lo)
    return {
        "n_used_by_year": {Y: lo[Y]["n_test"] for Y in yrs},
        "n_total_by_year": {Y: int((years == Y).sum()) for Y in yrs},
        "loyo": {Y: {"uhat": lo[Y]["uhat"], "ubar_actual": lo[Y]["ubar_actual"], "a": lo[Y]["a"], "b": lo[Y]["b"],
                     "n_test": lo[Y]["n_test"], "n_train": lo[Y]["n_train"]} for Y in yrs},
        "ubar_R": ubar_R, "ubar_2022": ubar_22, "uhat_2022": uhat_22, "subset_excess": den,
        "subset_excess_le_0": bool(den <= 0), "phi": phi,
        "a": float(a), "b": float(b), "se_cluster": se, "se_iid": se_iid, "t": float(t), "p": p_normal(float(t)),
        "n_fit": int(R.sum()), "clusters_fit": int(G), "xbar_R": float(x[R].mean()), "xbar_2022": float(x[T].mean()),
        "p10_ex2022": p10,
    }


def joint(d: pd.DataFrame, vars_: list[str]) -> dict[str, Any]:
    u = d["u"].to_numpy()
    years = d["year"].to_numpy()
    fin = np.ones(len(d), dtype=bool)
    for v in vars_:
        fin &= np.isfinite(d[v].to_numpy(dtype=float))
    R, T = fin & (years != PRIMARY), fin & (years == PRIMARY)
    Xall = np.column_stack([np.ones(len(d))] + [d[v].to_numpy(dtype=float) for v in vars_])
    beta = ols(u[R], Xall[R])
    ubar_R, ubar_22 = float(u[R].mean()), float(u[T].mean())
    uhat_22 = float(np.mean(Xall[T] @ beta))
    den = ubar_22 - ubar_R
    share = (ubar_22 - uhat_22) / den if den != 0 else None
    if not vars_:
        need(share is not None and abs(share - 1.0) < 1e-9, "[JOINT] the intercept-only model must leave the whole excess")
    e = u[R] - Xall[R] @ beta
    V, G = cluster_vcov(Xall[R], e, d["week"].to_numpy()[R])
    names = ["const"] + list(vars_)
    return {"variables": list(vars_), "n_fit": int(R.sum()), "n_2022": int(T.sum()), "clusters_fit": int(G),
            "coef": {k: float(v) for k, v in zip(names, beta)},
            "se_cluster": {k: float(math.sqrt(V[i, i])) for i, k in enumerate(names)},
            "ubar_R": ubar_R, "ubar_2022": ubar_22, "uhat_joint_2022": uhat_22, "subset_excess": den,
            "residual_share": share}


def by_year(d: pd.DataFrame) -> dict[str, Any]:
    g = d.groupby("year")
    return {"n": g.size().astype(int).to_dict(), "ubar": g["u"].mean().astype(float).to_dict(),
            "mean_gross_usd": g["gross_usd"].mean().astype(float).to_dict(),
            "mean_net_usd": g["net_usd"].mean().astype(float).to_dict()}


def analyse_object(d: pd.DataFrame, obj: str, gates: dict[str, int], family: tuple[str, ...] | None = None,
                   leak: bool = False) -> dict[str, Any]:
    spec = OBJECTS[obj]
    fam = tuple(family) if family is not None else spec["family"]
    years = d["year"].to_numpy()
    u = d["u"].to_numpy()
    ubar_R, ubar_22 = float(u[years != PRIMARY].mean()), float(u[years == PRIMARY].mean())
    excess = ubar_22 - ubar_R
    cells = {v: cell(d, v, gates, leak=leak) for v in fam}
    p = [cells[v]["p"] for v in fam]
    adj = holm(p)
    holm_gate(p, adj)
    gates["holm_families_checked"] += 1
    for v, pa in zip(fam, adj):
        c = cells[v]
        c["p_holm"] = pa
        c["reading"] = cell_reading(pa, c["phi"], not c["subset_excess_le_0"])
    beside = {}
    for v in BESIDE:
        c = cell(d, v, gates, leak=leak)
        c["p_holm"] = None
        c["reading_unadjusted_beside"] = cell_reading(c["p"], c["phi"], not c["subset_excess_le_0"])
        beside[v] = c
    passing = [v for v in fam if cells[v]["p_holm"] < ALPHA]
    jm = joint(d, passing)
    explains = [v for v in fam if cells[v]["reading"] == "EXPLAINS"]
    partial = [v for v in fam if cells[v]["reading"] == "PARTIAL"]
    if excess <= 0:
        reading = "N/A"
    elif not explains and jm["residual_share"] is not None and jm["residual_share"] >= 0.5:
        reading = "UNEXPLAINED"
    else:
        reading = "NOT_UNEXPLAINED"
    p10 = {v: {"uhat_2018": c["loyo"].get("2018", {}).get("uhat"), "ubar_2018_actual": c["loyo"].get("2018", {}).get("ubar_actual"),
               "ubar_R": c["ubar_R"], "uhat_2018_above_ubar_R": (None if c["loyo"].get("2018", {}).get("uhat") is None
                                                                  else bool(c["loyo"]["2018"]["uhat"] > c["ubar_R"])),
               "n_train": c["loyo"].get("2018", {}).get("n_train"),
               "cell_reading": c["reading"]} for v, c in cells.items()}
    p10x = {v: {"uhat_2018": c["p10_ex2022"]["uhat_2018"], "ubar_R": c["ubar_R"],
                "uhat_2018_above_ubar_R": (None if c["p10_ex2022"]["uhat_2018"] is None
                                           else bool(c["p10_ex2022"]["uhat_2018"] > c["ubar_R"])),
                "n_train": c["p10_ex2022"]["n_train"], "n_2018": c["p10_ex2022"]["n_test"],
                "ubar_2018_actual": c["loyo"].get("2018", {}).get("ubar_actual"), "cell_reading": c["reading"]}
            for v, c in cells.items()}
    return {"group": spec["group"], "root": spec["root"], "family": list(fam), "not_read": list(spec["not_read"]),
            "not_read_note": ("X3 == 1 on every L3 trade (asserted: L3 is gated on short gamma); no fit is possible, so it is "
                              "reported as not read and is outside the family") if spec["not_read"] else None,
            "beside_not_in_family": list(BESIDE), "n_trades": int(len(d)), "by_year": by_year(d),
            "ubar_R": ubar_R, "ubar_2022": ubar_22, "excess_2022": excess, "cells": cells, "beside": beside,
            "holm_passing": passing, "joint": jm, "explains": explains, "partial": partial, "reading": reading,
            "prediction_10_ex2022": p10x,
            "prediction_10_literal_loyo_2018_beside": p10}


def analyse(lines: pd.DataFrame, panel: pd.DataFrame) -> tuple[dict[str, Any], dict[str, int]]:
    d = attach(lines, panel)
    gates = {"join_values_checked": join_audit(d, panel), "u_checked": u_audit(d), "x7_checked": x7_audit(d),
             "loyo_years_checked": 0, "p10_ex2022_checked": 0, "cluster_se_checked": 0, "holm_families_checked": 0}
    out = {}
    for obj in OBJECTS:
        sub = d[d["line"] == obj].reset_index(drop=True)
        need(len(sub) > 0, f"[OBJECT] {obj} has no trades")
        if obj == "L3":
            need(bool((sub["X3"] == 1.0).all()), "[L3] X3 is not 1 on every L3 trade: 'not read' no longer describes it")
        out[obj] = analyse_object(sub, obj, gates)
    return out, gates


# ================================================================================ synthetics (self-test)
def synth(seed: int, mode: str, n_per_year: int = 2000) -> pd.DataFrame:
    """Years 2016-2023 on real business days (so ISO weeks exist). mode:
    planted  X ~ N(0,1) + 1.5 [2022], u = 0.5 X + N(0,1): 2022's whole excess runs through X  (phi ~ 1)
    noise    X ~ N(0,1) + 1.5 [2022], u = N(0,1) + 0.75 [2022]: X moves in 2022 but carries nothing (phi ~ 0)
    weekly   x_i = z_week + 0.3 e, u = v_week + 0.3 eta: within-week correlation in x and the residual (clustered SE > iid SE)
    iid      x, u independent N(0,1)"""
    rng = np.random.default_rng(seed)
    rows = []
    for Y in range(2016, 2024):
        days = pd.bdate_range(f"{Y}-01-04", f"{Y}-12-29")
        s = np.array([days[i % len(days)].strftime("%Y-%m-%d") for i in range(n_per_year)])
        rows.append(pd.DataFrame({"session": s, "year": str(Y)}))
    d = pd.concat(rows, ignore_index=True)
    iso = pd.to_datetime(d["session"]).dt.isocalendar()
    d["week"] = (iso["year"].astype(np.int64) * 100 + iso["week"].astype(np.int64)).to_numpy()
    n = len(d)
    is22 = (d["year"] == PRIMARY).to_numpy().astype(float)
    if mode == "planted":
        d["X"] = rng.standard_normal(n) + 1.5 * is22
        d["u"] = 0.5 * d["X"] + rng.standard_normal(n)
    elif mode == "noise":
        d["X"] = rng.standard_normal(n) + 1.5 * is22
        d["u"] = rng.standard_normal(n) + 0.75 * is22
    elif mode in ("weekly", "iid"):
        _, inv = np.unique(d["week"].to_numpy(), return_inverse=True)
        if mode == "weekly":
            z, v = rng.standard_normal(inv.max() + 1), rng.standard_normal(inv.max() + 1)
            d["X"] = z[inv] + 0.3 * rng.standard_normal(n)
            d["u"] = v[inv] + 0.3 * rng.standard_normal(n)
        else:
            d["X"] = rng.standard_normal(n)
            d["u"] = rng.standard_normal(n)
    else:
        raise ValueError(mode)
    return d


PHI_BAND = 0.15   # planted: |phi - 1| < 0.15; noise: |phi| < 0.15 (2,000 trades a year; phi's sd is ~0.04 on both)


def phi_gate(c: dict[str, Any], target: float, what: str) -> None:
    need(c["phi"] is not None and abs(c["phi"] - target) < PHI_BAND, f"[LOYO] {what}: phi {c['phi']} outside {target} +/- {PHI_BAND}")


def cluster_gate(d: pd.DataFrame, cl: np.ndarray, what: str) -> float:
    """On a within-week-correlated synthetic the clustered SE must exceed the iid SE by half again."""
    x, u = d["X"].to_numpy(), d["u"].to_numpy()
    X = np.column_stack([np.ones(len(d)), x])
    beta = ols(u, X)
    e = u - X @ beta
    se_c = math.sqrt(cluster_vcov(X, e, cl)[0][1, 1])
    se_i = math.sqrt(iid_vcov(X, e)[1, 1])
    need(se_c > 1.5 * se_i, f"[CLUSTER] {what}: clustered SE {se_c:.4g} is not > 1.5 x the iid SE {se_i:.4g}")
    return se_c / se_i


# ================================================================================ self-test
def expect_raise(fn: Callable[[], Any], what: str, fired: list[str]) -> None:
    try:
        fn()
    except D722BError as e:
        P(f"    RAISES on {what}: {str(e)[:120]}")
        fired.append(what)
        return
    raise SystemExit(f"SELFTEST FAILED: no raise on {what}")


def selftest() -> int:
    t0 = time.time()
    import diag_d722_conditioners as C
    import diag_d722_lines as L
    fired: list[str] = []
    P("D722 Part B --selftest: the real-data gates (no statistic is printed), then every canary must RAISE")
    lines, panel = L.load_lines(), C.load_conditioners()
    P(f"  loaded in {time.time() - t0:.1f} s")
    P("== clean pass on the real (sealed) inputs")
    t1 = time.time()
    res0, gates = analyse(lines, panel)
    aggregates_only(res0)
    gates["aggregates_only"] = 1
    P(f"    every gate passed ({time.time() - t1:.1f} s): {gates}")
    d = attach(lines, panel)

    P("== 1. the seal")
    row = lines[lines["line"] == "K2_ES"].iloc[[0]].copy()
    row["session"] = "2024-01-02"
    expect_raise(lambda: attach(pd.concat([lines, row], ignore_index=True), panel), "a 2024 trade planted in the trade table", fired)
    pr = panel.iloc[[0]].rename(index={panel.index[0][1]: "2024-01-02"}, level=1)
    expect_raise(lambda: attach(lines, pd.concat([panel, pr])), "a 2024 row planted in the conditioner panel", fired)

    P("== 2. the join (lag): the panel read one session late or early")
    for sh in (1, -1):
        bad = attach(lines, panel, shift=sh)
        expect_raise(lambda b=bad: join_audit(b, panel), f"the panel shifted {sh:+d} session", fired)

    P("== 3. u: the outcome without sig20, without the horizon")
    for w in ("no_sig20", "no_hold"):
        bad = attach(lines, panel, wrong_u=w)
        expect_raise(lambda b=bad: u_audit(b), f"u built {w}", fired)
    bad = d.copy()
    bad.loc[bad.index[0], "u"] = -bad.loc[bad.index[0], "u"]
    expect_raise(lambda: u_audit(bad), "one u with its sign inverted", fired)
    bad = d.copy()
    i0 = bad.index[0]
    bad.loc[i0, "sig20"] = -bad.loc[i0, "sig20"]
    bad.loc[i0, "u"] = outcome_u(bad.loc[[i0], "gross_usd"], bad.loc[[i0], "usd_pp"], bad.loc[[i0], "entry_price"],
                                 bad.loc[[i0], "sig20"], bad.loc[[i0], "hold_min"])[0]
    expect_raise(lambda: u_audit(bad), "a negative sig20 with u recomputed from it (sign(u) != sign(g), values consistent)", fired)

    P("== 4. X7 (right-quantity): not multiplied by side")
    bad = attach(lines, panel, wrong_x7="noside")
    expect_raise(lambda: x7_audit(bad), "X7 = r60 (side dropped)", fired)

    P("== 5. leave one year out")
    g = {"loyo_years_checked": 0, "cluster_se_checked": 0}
    sp, sn = synth(722, "planted"), synth(723, "noise")
    cp, cn = cell(sp, "X", g), cell(sn, "X", g)
    phi_gate(cp, 1.0, "planted year effect")
    phi_gate(cn, 0.0, "noise")
    P(f"    clean: planted phi = {cp['phi']:.4f} (band 1 +/- {PHI_BAND}), noise phi = {cn['phi']:.4f} (band 0 +/- {PHI_BAND})")
    expect_raise(lambda: phi_gate(cn, 1.0, "noise scored against the planted band"), "the phi gate handed the noise cell", fired)
    expect_raise(lambda: cell(sn, "X", g, leak=True), "LOYO leaking the held-out year into its own fit (synthetic)", fired)
    k2 = d[d["line"] == "K2_ES"].reset_index(drop=True)
    expect_raise(lambda: cell(k2, "X4", g, leak=True), "LOYO leaking the held-out year into its own fit (K2_ES, X4)", fired)
    expect_raise(lambda: cell(sn, "X", g, leak_p10=True), "prediction 10's ex-2022 fit with 2022 kept in (synthetic)", fired)
    expect_raise(lambda: cell(k2, "X4", g, leak_p10=True), "prediction 10's ex-2022 fit with 2022 kept in (K2_ES, X4)", fired)
    l3 = d[d["line"] == "L3"].reset_index(drop=True)
    expect_raise(lambda: cell(l3, "X3", g), "X3 fitted on L3 (constant: must be excluded, not fitted)", fired)

    P("== 6. the clustered SE")
    sw, si = synth(724, "weekly", 600), synth(725, "iid", 600)
    r = cluster_gate(sw, sw["week"].to_numpy(), "within-week synthetic")
    xi, ui = si["X"].to_numpy(), si["u"].to_numpy()
    Xi = np.column_stack([np.ones(len(si)), xi])
    ei = ui - Xi @ ols(ui, Xi)
    ri = math.sqrt(cluster_vcov(Xi, ei, si["week"].to_numpy())[0][1, 1]) / math.sqrt(iid_vcov(Xi, ei)[1, 1])
    P(f"    clean: clustered / iid SE = {r:.2f} on the within-week synthetic; {ri:.2f} on the iid synthetic (reported, not gated)")
    expect_raise(lambda: cluster_gate(sw, np.arange(len(sw)), "clustering ignored (every trade its own cluster)"),
                 "a cluster SE that ignores clustering", fired)
    bad_d = sw.copy()
    bad_d["week"] = np.arange(len(sw))
    expect_raise(lambda: cell(bad_d, "X", g), "the cell's sandwich built on row clusters against the loop's ISO weeks", fired)

    P("== 7. Holm")
    for br in ("no_stepdown_max", "bonferroni"):
        hp = [0.2]   # a one-member family: the rejected-set check passes, so only the hand example can catch the broken Holm
        expect_raise(lambda b=br, q=hp: holm_gate(q, holm(q, broken=b), impl=lambda z, b_=b: holm(z, broken=b_)),
                     f"the gate run with a Holm {br}", fired)
    fam_p = [0.04, 0.001, 0.03]   # Holm rejects only 0.001 (0.03 x 2 = 0.06); without the max, 0.04 x 1 would slip through
    expect_raise(lambda: holm_gate(fam_p, holm(fam_p, broken="no_stepdown_max")), "the family gate handed a step-down without its max",
                 fired)
    expect_raise(lambda: holm_gate(fam_p, list(fam_p)), "the family gate handed unadjusted p", fired)

    P("== 8. readings and the joint model")
    cases = [((0.01, 0.6, True), "EXPLAINS"), ((0.01, 0.5, True), "EXPLAINS"), ((0.01, 0.3, True), "PARTIAL"),
             ((0.01, 0.2, True), "PARTIAL"), ((0.01, 0.1, True), "NO"), ((0.06, 0.9, True), "NO"), ((0.01, 0.9, False), "NO")]
    for args, want in cases:
        need(cell_reading(*args) == want, f"[READING] {args} -> {cell_reading(*args)}, not {want}")
    P(f"    clean: {len(cases)} hand reading cases")
    jp = joint(sp, ["X"])
    j0 = joint(sp, [])
    need(abs(jp["residual_share"]) < 0.15 and abs(j0["residual_share"] - 1.0) < 1e-12,
         f"[JOINT] planted residual {jp['residual_share']}, intercept {j0['residual_share']}")
    P(f"    clean: joint residual share {jp['residual_share']:.4f} on the planted synthetic, {j0['residual_share']:.12f} intercept-only")
    expect_raise(lambda: need(abs(joint(sn, ["X"])["residual_share"]) < 0.15, "[JOINT] noise X does not explain"),
                 "the joint gate on the noise synthetic", fired)

    P("== 9. aggregates only: a per-date key planted in an object's block")
    bad_res = {"L3": dict(res0["L3"], planted={"2022-03-01": 1.0})}
    expect_raise(lambda: aggregates_only(bad_res), "a session-dated key in the output", fired)
    P("== 10. --run refuses an existing output")
    expect_raise(lambda: refuse_existing(Path(__file__)), "an output path that exists", fired)
    P(f"SELFTEST PASSED in {time.time() - t0:.1f} s: {len(fired)} canaries raised")
    return 0


# ================================================================================ run
def refuse_existing(path: Path) -> None:
    need(not path.exists(), f"[RUN] {path.name} exists: --run is run-once")


def aggregates_only(objects: dict[str, Any]) -> str:
    """The committed JSON carries no per-date row: no YYYY-MM-DD anywhere in the objects' block (keys or values)."""
    import re
    s = json.dumps(jsonable(objects))
    hit = re.search(r"(19|20)\d\d-\d\d-\d\d", s)
    need(hit is None, f"[AGGREGATES] a date {hit.group(0) if hit else ''} in the output: per-date rows are not allowed in data/")
    return s


def jsonable(o: Any) -> Any:
    if isinstance(o, dict):
        return {str(k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    if isinstance(o, (np.floating, float)):
        f = float(o)
        return f if math.isfinite(f) else None
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def run() -> int:
    t0 = time.time()
    refuse_existing(OUT)
    import diag_d722_conditioners as C
    import diag_d722_lines as L
    lines, panel = L.load_lines(), C.load_conditioners()
    res, gates = analyse(lines, panel)
    aggregates_only(res)
    gates["aggregates_only"] = 1
    wall = time.time() - t0
    doc = {
        "spec": SPEC, "generated_utc": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "seal": f"no session >= {CUT} (asserted on the trade table, the panel and the joined frame)",
        "outcome": "u = gross_usd / (usd_pp * entry_price * sig20(root, session) * sqrt(hold_min / 390))",
        "method": {
            "subset": "per cell, the object's trades with finite X; NaN-X trades enter neither fit, prediction nor the cell's means",
            "loyo": "OLS u = a + b X on the other years' subset trades (2022 in the training set when Y != 2022); u_hat_Y = mean fitted "
                    "value over Y's subset trades",
            "phi": "(u_hat_2022 - ubar_R) / (ubar_2022 - ubar_R) on the cell's subset; ubar_R pooled over non-2022 trades",
            "se": "cluster-robust by ISO week (isoyear, week) of the session, CR1: c = G/(G-1) (N-1)/(N-K), K = 2; fit excludes 2022",
            "p": "two-sided normal, erfc(|t|/sqrt 2); Holm step-down across the object's family",
            "readings": "EXPLAINS: Holm p < 0.05 and phi >= 0.5; PARTIAL: Holm p < 0.05 and 0.2 <= phi < 0.5; NO otherwise (also NO "
                        "where the cell's subset has no 2022 excess, flagged subset_excess_le_0)",
            "joint": "OLS on every Holm-passing variable (intercept), outside 2022, trades with all finite; residual share = "
                     "(ubar_2022 - u_hat_joint_2022) / (ubar_2022 - ubar_R) on that subset",
            "object": "N/A if ubar_2022 <= ubar_R (all trades); UNEXPLAINED if no cell EXPLAINS and the joint residual share >= 0.5; "
                      "else NOT_UNEXPLAINED",
            "beside": "X6_15m and X9_record: the same cell, unadjusted p only, not in any Holm family (D722-A1)",
        },
        "gates": gates, "wall_s": round(wall, 1), "objects": res,
        "readings": {k: {"reading": v["reading"], "explains": v["explains"], "partial": v["partial"],
                         "joint_residual_share": v["joint"]["residual_share"]} for k, v in res.items()},
    }
    OUT.write_text(json.dumps(jsonable(doc), indent=1) + "\n", encoding="utf-8", newline="\n")
    for k, v in res.items():
        P(f"{k:6s} excess {v['excess_2022']:+.4f}  reading {v['reading']:16s} explains {v['explains']} partial {v['partial']} "
          f"joint residual {v['joint']['residual_share']}")
    P(f"wrote {OUT.relative_to(REPO)} in {wall:.1f} s; gates {gates}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args()
    return selftest() if a.selftest else run()


if __name__ == "__main__":
    raise SystemExit(main())
