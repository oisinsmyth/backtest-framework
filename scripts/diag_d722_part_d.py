"""D722 Part D: one bet or several? (docs/decisions/D722-DIAG-PRE-REG-why-2022-scale-regime-or-one-bet.md, s.5, with Amendment
D722-A1; commits f25e4726, 7880c5a0).

    uv run python scripts/diag_d722_part_d.py --selftest   # the clean case on the real tables, then every canary must RAISE
    uv run python scripts/diag_d722_part_d.py --run        # run-once: refuses if data/diag_d722_part_d.json exists

INPUTS (imported, never edited): `diag_d722_lines.load_lines()` (one row per trade; K1 one row per traded session) and
`diag_d722_conditioners.load_conditioners()` (its (root, session) index is the session calendar of ES, NQ and HO).

THE DAILY SERIES. Per line, one row per session of its calendar: net = the sum of the line's trades that session, 0 on a session
it did not trade; `traded` = it holds at least one trade that session. Every line but L3 holds AT MOST ONE trade a session
(asserted: a second row on a session raises). L3 is D699 V1, whose own design states "A day can hold several trades" (D699 Stage 0
design, Cost bullet); in-sample it has 52 sessions with two trades (47 inside Part D's window, 12 in 2022). Its trades on one session
are summed, and they must be distinct and non-overlapping in time (a duplicated row raises on L3 too). THIS IS A DEVIATION FROM THE
BRIEF'S "one trade per session per line" AND NEEDS THE ORCHESTRATOR'S RULING (MULTI_TRADE_LINES below).

THE CALENDARS (s.5, the brief):
  IDX     the ES panel sessions 2018-05-14 -> 2023-12-29 (NQ's calendar is identical: asserted). L1, L2, L3, K1, K2_ES, K2_NQ.
  HO      HO's own panel sessions 2018-08-01 -> 2023-12-29. L4's daily series.
  IDX_HO  IDX intersect HO (so from 2018-08-01): every pair that includes L4.
  "2022" = the calendar year; "other" = every other year of the pair's calendar, pooled.

THE MEASURES:
  D1  Pearson and Spearman (average ranks) rho of daily net for every pair of L1 L2 L3 L4 K1 K2_ES K2_NQ, in 2022 and in the
      other years, on the pair's calendar with zeros included; and on the sessions both lines trade (with n).
  D2  2022 top-decile overlap, every pair of L1 L2 L3 L4 K1 K2_ES. Top set of a line = the ceil(10 %) of its 2022 trading days
      with the largest net (ties broken by session date, and a tie straddling the cut is reported). DECLARED (conditional): the
      population = 2022 sessions on which BOTH lines trade (N); each top set intersected with it (K, n); k = the overlap;
      p = P(X >= k), X ~ Hypergeometric(N, K, n), computed exactly in integers and cross-checked against scipy. Beside it,
      labelled UNCONDITIONAL: population = every 2022 session of the pair's calendar, top sets unrestricted.
  D3  each of L1 L2 L3 L4 K1: its 2022 daily net on the same session's K2_ES net, OLS with intercept, (a) every 2022 session of
      the pair's calendar, zeros included, (b) the line's 2022 trading days only. Slope, intercept, R^2, and the share of the
      line's 2022 net that the fitted K2 component accounts for, share = b * sum(x) / sum(y) (the intercept is NOT in the
      numerator: with it, the OLS identity makes the ratio 1 by construction). Beside it, labelled: the share of the line's 2022
      net earned on sessions K2_ES nets > 0 (the record's "last-hour continuation days"). L1 trades the same ES 15:30 -> 16:00
      move as K2_ES on its days, by construction: its row is reported and flagged.
  D4  B = L1 + L2 + L3 (one micro each, daily nets summed on IDX): per-year net and 2022's share of the window's total;
      DR = (sum of the three daily-net variances) / Var(B) and the mean pairwise Pearson rho inside B, in 2022 and the
      other years pooled (per year beside). Variances ddof 1.

THE READING (s.5, declared): ONE BET if, for the pair L1-L3 OR the pair L1-L4, the 2022 Pearson rho (pair calendar, zeros
included) >= 0.3 OR the D2 conditional p < 0.01; SEPARATE otherwise. L1-L2 is reported and not read. Every condition that fired
is named.

ASSERTIONS (s.7), each shown to RAISE in --selftest: the seal (a planted 2024 trade; a 2024 calendar session); daily aggregation
(a duplicated trade row on a one-trade line and on L3, a trade off the calendar, a daily series missing a zero day or with an
altered day); the hypergeometric (identical series -> full overlap at p ~ 0; 200 independent synthetic replications -> the share
of p <= alpha matches its exact null expectation within 3 SE and does not exceed alpha + 3 SE, alpha in .05 .10 .25 .50; the
complement p, the off-by-one tail and a broken exact implementation are each caught); the reading (a table of synthetic cases
built to give ONE BET and SEPARATE, plus boundary cases; a reader that reads L1-L2, uses > for >=, or ignores p is caught; the
full pipeline on synthetic trade tables built to give ONE BET and SEPARATE); D3's slope against a second implementation (lstsq);
D4's variance identity (a book that drops a line raises).

SEAL: no value dated 2024-01-01 or later enters anything (both loaders filter and assert; this runner asserts again on every
table and calendar). The vault is never read. The daily series stay in memory: L3 is a per-date derivative of SqueezeMetrics GEX,
so the output JSON holds aggregates only (no per-date values, no dates of top days).

SPEED: the whole analysis is ~1 s of numpy on ~1,450 sessions x 7 lines; there is no independent unit worth a worker (a process
start costs more than the work), so nothing fans out and there is no chunk == whole proof to make.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from fractions import Fraction
from itertools import combinations
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

SPEC = "docs/decisions/D722-DIAG-PRE-REG-why-2022-scale-regime-or-one-bet.md s.5 (f25e4726; Amendment D722-A1 7880c5a0)"
OUT = REPO / "data" / "diag_d722_part_d.json"
SEAL = "2024-01-01"
IDX_LO, HO_LO, HI = "2018-05-14", "2018-08-01", "2023-12-29"
LINES_D1 = ("L1", "L2", "L3", "L4", "K1", "K2_ES", "K2_NQ")
LINES = ("L1", "L2", "L3", "L4", "K1", "K2_ES")
D3_LINES = ("L1", "L2", "L3", "L4", "K1")
BOOK = ("L1", "L2", "L3")
IDX_LINES = ("L1", "L2", "L3", "K1", "K2_ES", "K2_NQ")
HO_LINES = ("L4",)
MULTI_TRADE_LINES = {"L3": "D699 Stage 0 design: 'A day can hold several trades' (the line's own definition)"}
READ_PAIRS = (("L1", "L3"), ("L1", "L4"))
NOT_READ = ("L1", "L2")
RHO_BAR, P_BAR, TOP_FRAC = 0.3, 0.01, 0.10
SEED, N_REPS = 722, 200
ALPHAS = (0.05, 0.10, 0.25, 0.50)
TOL_SUM = 1e-9          # dollars, relative to the sum of |net|: daily sum vs trade total (the float order differs)
TOL_REL = 1e-9          # second implementations and identities


class PartDError(Exception):
    pass


class SealError(PartDError):
    pass


class AggregationError(PartDError):
    pass


class HyperError(PartDError):
    pass


class ReadingError(PartDError):
    pass


class IdentityError(PartDError):
    pass


def P(*a: Any) -> None:
    print(*a, flush=True)


def pk(a: str, b: str) -> str:
    return f"{a}-{b}"


# ================================================================================ seal and calendars
def seal_check(sessions: Any, what: str) -> None:
    s = np.asarray(sessions).astype(str)
    if s.size and (s >= SEAL).any():
        raise SealError(f"[SEAL] {what}: a session on or after {SEAL} ({sorted(s[s >= SEAL])[0]})")


def calendars_from_panel(panel: pd.DataFrame) -> dict[str, np.ndarray]:
    idx = panel.index
    seal_check(idx.get_level_values(1), "the conditioner panel's calendar")
    cal = {r: np.array(sorted(set(idx[idx.get_level_values(0) == r].get_level_values(1).astype(str)))) for r in ("ES", "NQ", "HO")}
    if not np.array_equal(cal["ES"], cal["NQ"]):
        raise AggregationError("the ES and NQ panel calendars differ: the index lines need one common calendar")
    return make_calendars(cal["ES"], cal["HO"])


def make_calendars(es: np.ndarray, ho: np.ndarray) -> dict[str, np.ndarray]:
    es, ho = np.asarray(es).astype(str), np.asarray(ho).astype(str)
    seal_check(es, "the ES calendar")
    seal_check(ho, "the HO calendar")
    c_idx = es[(es >= IDX_LO) & (es <= HI)]
    c_ho = ho[(ho >= HO_LO) & (ho <= HI)]
    c_ixh = np.array(sorted(set(c_idx) & set(c_ho)))
    for k, v in (("IDX", c_idx), ("HO", c_ho), ("IDX_HO", c_ixh)):
        if v.size == 0 or not (np.diff(v.astype("datetime64[D]")).astype(int) > 0).all():
            raise AggregationError(f"calendar {k} is empty or not strictly increasing")
    return {"IDX": c_idx, "HO": c_ho, "IDX_HO": c_ixh}


def own_cal(line: str) -> str:
    return "HO" if line in HO_LINES else "IDX"


def pair_cal(a: str, b: str) -> str:
    return "IDX_HO" if (a in HO_LINES or b in HO_LINES) else "IDX"


# ================================================================================ daily aggregation
def daily_series(tr: pd.DataFrame, cal: np.ndarray, line: str) -> pd.DataFrame:
    """One row per calendar session: net (0 where untraded), n_trades, traded. `tr` holds this line's trades (any span)."""
    seal_check(tr["session"], f"{line}'s trades")
    seal_check(cal, f"{line}'s calendar")
    s = tr["session"].astype(str).to_numpy()
    w = tr[(s >= cal[0]) & (s <= cal[-1])]
    ws = w["session"].astype(str).to_numpy()
    off = sorted(set(ws) - set(cal))
    if off:
        raise AggregationError(f"{line}: {len(off)} trade session(s) inside the window are not on the calendar (first {off[0]})")
    cnt = pd.Series(ws).value_counts()
    multi = cnt[cnt > 1]
    if len(multi) and line not in MULTI_TRADE_LINES:
        raise AggregationError(f"{line}: {len(multi)} session(s) hold more than one trade (first {sorted(multi.index)[0]}); "
                               "this line is declared one trade a session")
    if len(multi):
        m = w[w["session"].astype(str).isin(multi.index)].sort_values(["session", "entry_min", "exit_min"])
        for sess, x in m.groupby("session", sort=True):
            e, xo = x["entry_min"].to_numpy(), x["exit_min"].to_numpy()
            if x.duplicated().any() or (e[1:] < xo[:-1]).any():
                raise AggregationError(f"{line}: session {sess} holds a duplicated or overlapping trade")
    net = w.groupby("session", sort=True)["net_usd"].sum()
    d = pd.DataFrame(index=pd.Index(cal, name="session"))
    d["net"] = net.reindex(d.index).fillna(0.0).to_numpy(float)
    d["n_trades"] = cnt.reindex(d.index).fillna(0).to_numpy(int)
    d["traded"] = d["n_trades"].to_numpy() > 0
    check_daily(d, w, cal, line)
    return d


def check_daily(d: pd.DataFrame, w: pd.DataFrame, cal: np.ndarray, line: str) -> None:
    """Zero-filling and conservation: one row per calendar session, 0 exactly where untraded, the daily sum == the trade total."""
    if len(d) != len(cal) or not np.array_equal(d.index.to_numpy().astype(str), cal):
        raise AggregationError(f"{line}: the daily series is not one row per calendar session ({len(d)} vs {len(cal)})")
    if (d.loc[~d["traded"], "net"] != 0.0).any():
        raise AggregationError(f"{line}: an untraded session carries a nonzero net")
    if int(d["n_trades"].sum()) != len(w):
        raise AggregationError(f"{line}: the daily trade count {int(d['n_trades'].sum())} != the window's trades {len(w)}")
    tot = math.fsum(w["net_usd"].to_numpy(float))
    got = math.fsum(d["net"].to_numpy(float))
    scale = max(1.0, math.fsum(np.abs(w["net_usd"].to_numpy(float))))
    if abs(got - tot) > TOL_SUM * scale:
        raise AggregationError(f"{line}: the daily sum {got!r} != the trade total {tot!r}")


def build_daily(df: pd.DataFrame, cals: dict[str, np.ndarray], lines: tuple[str, ...] = LINES_D1) -> dict[str, pd.DataFrame]:
    seal_check(df["session"], "the per-trade table")
    out = {}
    for ln in lines:
        tr = df[df["line"] == ln]
        if tr.empty:
            raise AggregationError(f"{ln}: no trades in the table")
        out[ln] = daily_series(tr, cals[own_cal(ln)], ln)
    return out


def pair_frame(daily: dict[str, pd.DataFrame], cals: dict[str, np.ndarray], a: str, b: str) -> pd.DataFrame:
    c = cals[pair_cal(a, b)]
    da, db = daily[a].reindex(c), daily[b].reindex(c)
    if da["net"].isna().any() or db["net"].isna().any():
        raise AggregationError(f"{pk(a, b)}: the pair calendar is not inside both lines' calendars")
    return pd.DataFrame({"a": da["net"].to_numpy(float), "b": db["net"].to_numpy(float),
                         "ta": da["traded"].to_numpy(bool), "tb": db["traded"].to_numpy(bool)}, index=pd.Index(c, name="session"))


def is2022(index: pd.Index) -> np.ndarray:
    return index.to_numpy().astype(str).astype("U4") == "2022"


# ================================================================================ D1
def _rank(x: np.ndarray) -> np.ndarray:
    from scipy.stats import rankdata
    return rankdata(x, method="average")


def pearson(x: np.ndarray, y: np.ndarray) -> float:
    if len(x) < 3 or np.std(x) == 0 or np.std(y) == 0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def corr_block(x: np.ndarray, y: np.ndarray) -> dict[str, Any]:
    return {"n": int(len(x)), "pearson": pearson(x, y), "spearman": pearson(_rank(x), _rank(y)) if len(x) >= 3 else float("nan")}


def d1(daily: dict[str, pd.DataFrame], cals: dict[str, np.ndarray], lines: tuple[str, ...] = LINES_D1) -> dict[str, Any]:
    out = {}
    for a, b in combinations(lines, 2):
        f = pair_frame(daily, cals, a, b)
        y22 = is2022(f.index)
        both = f["ta"].to_numpy() & f["tb"].to_numpy()
        r: dict[str, Any] = {"calendar": pair_cal(a, b), "sessions": int(len(f))}
        for per, m in (("2022", y22), ("other", ~y22)):
            r[per] = {"all_sessions": corr_block(f["a"].to_numpy()[m], f["b"].to_numpy()[m]),
                      "both_trade": corr_block(f["a"].to_numpy()[m & both], f["b"].to_numpy()[m & both])}
        if r["2022"]["all_sessions"]["n"] + r["other"]["all_sessions"]["n"] != len(f):
            raise IdentityError(f"D1 {pk(a, b)}: 2022 + other != the pair calendar")
        out[pk(a, b)] = r
    return out


# ================================================================================ D2: the hypergeometric
def hyper_p_exact(k: int, N: int, K: int, n: int) -> float:
    """P(X >= k), X ~ Hypergeometric(population N, K marked, n drawn), in exact integer arithmetic."""
    if not (0 <= K <= N and 0 <= n <= N):
        raise HyperError(f"hypergeometric sizes out of range: N={N} K={K} n={n}")
    lo, hi = max(0, n - (N - K)), min(K, n)
    if k <= lo:
        return 1.0
    if k > hi:
        return 0.0
    num = sum(math.comb(K, x) * math.comb(N - K, n - x) for x in range(k, hi + 1))
    return float(Fraction(num, math.comb(N, n)))


def hyper_p_scipy(k: int, N: int, K: int, n: int) -> float:
    from scipy.stats import hypergeom
    return float(hypergeom.sf(k - 1, N, K, n))


def cross_check_p(k: int, N: int, K: int, n: int, p: float) -> None:
    q = hyper_p_scipy(k, N, K, n)
    if not (abs(p - q) <= 1e-12 or abs(p - q) <= 1e-7 * max(abs(p), abs(q))):
        raise HyperError(f"hypergeometric p {p!r} != scipy's {q!r} (k={k} N={N} K={K} n={n})")


def hyper_p(k: int, N: int, K: int, n: int) -> float:
    p = hyper_p_exact(k, N, K, n)
    cross_check_p(k, N, K, n, p)
    return p


def null_share_le(alpha: float, N: int, K: int, n: int, pfun: Callable[[int, int, int, int], float]) -> float:
    """Exact null P(p <= alpha) for these sizes: the mass of every k whose p (by pfun) is <= alpha."""
    lo, hi = max(0, n - (N - K)), min(K, n)
    tot = Fraction(0)
    for x in range(lo, hi + 1):
        if pfun(x, N, K, n) <= alpha:
            tot += Fraction(math.comb(K, x) * math.comb(N - K, n - x), math.comb(N, n))
    return float(tot)


def top_set(d: pd.DataFrame, frac: float = TOP_FRAC) -> tuple[set[str], int, bool]:
    """The ceil(frac) of the 2022 trading days with the largest net; ties broken by session date (earlier first)."""
    x = d[is2022(d.index) & d["traded"].to_numpy()]
    m = int(math.ceil(frac * len(x)))
    if m == 0:
        return set(), 0, False
    o = x.assign(_s=x.index.to_numpy().astype(str)).sort_values(["net", "_s"], ascending=[False, True], kind="mergesort")
    top = o.iloc[:m]
    tie = bool(m < len(o) and o["net"].iloc[m] == top["net"].iloc[-1])
    return set(top.index.astype(str)), m, tie


def overlap(pop: set[str], A: set[str], B: set[str], pfun: Callable[[int, int, int, int], float]) -> dict[str, Any]:
    a, b = A & pop, B & pop
    N, K, n, k = len(pop), len(a), len(b), len(a & b)
    return {"N": N, "K": K, "n": n, "k": k, "expected": (K * n / N) if N else float("nan"), "p": pfun(k, N, K, n) if N else 1.0}


def d2_pair(da: pd.DataFrame, db: pd.DataFrame, cal: np.ndarray,
            pfun: Callable[[int, int, int, int], float] = hyper_p) -> dict[str, Any]:
    A, mA, tieA = top_set(da)
    B, mB, tieB = top_set(db)
    c22 = cal[cal.astype("U4") == "2022"]
    pop_all = set(c22)
    if not (A <= pop_all and B <= pop_all):
        raise AggregationError("D2: a top set is not inside the pair's 2022 calendar")
    ta = set(da.index[da["traded"].to_numpy()].astype(str)) & pop_all
    tb = set(db.index[db["traded"].to_numpy()].astype(str)) & pop_all
    both = ta & tb
    return {"trade_days_2022": [len(ta), len(tb)], "top_size": [mA, mB], "tie_at_cut": [tieA, tieB],
            "conditional": overlap(both, A, B, pfun), "unconditional": overlap(pop_all, A, B, pfun)}


def d2(daily: dict[str, pd.DataFrame], cals: dict[str, np.ndarray], lines: tuple[str, ...] = LINES,
       pfun: Callable[[int, int, int, int], float] = hyper_p) -> dict[str, Any]:
    out = {}
    for a, b in combinations(lines, 2):
        c = cals[pair_cal(a, b)]
        out[pk(a, b)] = {"calendar": pair_cal(a, b), **d2_pair(daily[a], daily[b], c, pfun)}
    return out


def calibrate_overlap(pfun: Callable[[int, int, int, int], float], log: Callable[..., None] = lambda *a: None) -> dict[str, Any]:
    """(i) identical series -> full overlap at p ~ 0; (ii) 200 independent synthetic pairs through d2_pair: for each alpha the share
    of conditional p <= alpha must match its exact null expectation (the mean over replications of P(p <= alpha | N, K, n)) within
    3 SE, and must not exceed alpha + 3 sqrt(alpha(1-alpha)/200) (validity)."""
    rng = np.random.default_rng(SEED)
    cal = np.array([str(d.date()) for d in pd.bdate_range("2022-01-03", "2022-12-30")])[:258]

    def synth(p_trade: float) -> pd.DataFrame:
        t = rng.random(len(cal)) < p_trade
        net = np.where(t, rng.standard_t(3, len(cal)) * 50.0, 0.0)
        return pd.DataFrame({"net": net, "traded": t, "n_trades": t.astype(int)}, index=pd.Index(cal, name="session"))

    x = synth(0.8)
    r = d2_pair(x, x.copy(), cal, pfun)["conditional"]
    if not (r["k"] == r["K"] == r["n"] > 0 and r["p"] < 1e-10):
        raise HyperError(f"identical series: overlap k={r['k']} of K={r['K']}, p={r['p']!r} (expected full overlap at p ~ 0)")
    ps, exp = [], {a: [] for a in ALPHAS}
    for _ in range(N_REPS):
        c = d2_pair(synth(0.85), synth(0.75), cal, pfun)["conditional"]
        ps.append(c["p"])
        for a in ALPHAS:
            exp[a].append(null_share_le(a, c["N"], c["K"], c["n"], hyper_p_exact))
    ps_a = np.array(ps)
    rows = {}
    for a in ALPHAS:
        q = np.array(exp[a])
        share, e = float((ps_a <= a).mean()), float(q.mean())
        se = math.sqrt(float((q * (1 - q)).sum())) / N_REPS
        cap = a + 3 * math.sqrt(a * (1 - a) / N_REPS)
        rows[str(a)] = {"share": share, "exact_expected": e, "se": se, "cap": cap}
        log(f"    alpha {a:.2f}: share of p <= alpha {share:.3f}, exact null expectation {e:.3f} +/- {se:.3f} (3 SE band), "
            f"validity cap {cap:.3f}")
        if abs(share - e) > 3 * se + 1e-12 or share > cap:
            raise HyperError(f"independent series: share of p <= {a} is {share:.3f}; its exact null expectation is {e:.3f} "
                             f"(3 SE = {3 * se:.3f}), cap {cap:.3f}")
    return {"identical": r, "independent": rows, "mean_p": float(ps_a.mean())}


# ================================================================================ D3
def ols(x: np.ndarray, y: np.ndarray) -> dict[str, Any]:
    n = len(x)
    if n < 3 or np.var(x) == 0:
        return {"n": n, "slope": float("nan"), "intercept": float("nan"), "r2": float("nan"), "share_k2_component": float("nan")}
    xm, ym = x.mean(), y.mean()
    b = float(((x - xm) * (y - ym)).sum() / ((x - xm) ** 2).sum())
    a = float(ym - b * xm)
    # second implementation: least squares on [1, x]
    sol = np.linalg.lstsq(np.column_stack([np.ones(n), x]), y, rcond=None)[0]
    if not (abs(sol[1] - b) <= TOL_REL * max(1.0, abs(b)) and abs(sol[0] - a) <= TOL_REL * max(1.0, abs(a), abs(ym))):
        raise IdentityError(f"D3: the slope {b!r} / intercept {a!r} disagree with lstsq {sol[1]!r} / {sol[0]!r}")
    fit = a + b * x
    sy = float(y.sum())
    if abs(float(fit.sum()) - sy) > TOL_REL * max(1.0, float(np.abs(y).sum())):
        raise IdentityError("D3: the OLS identity sum(fitted) == sum(y) fails")
    ss = float(((y - ym) ** 2).sum())
    r2 = float(1 - ((y - fit) ** 2).sum() / ss) if ss > 0 else float("nan")
    comp = float(b * x.sum())
    return {"n": n, "slope": b, "intercept": a, "r2": r2, "sum_y": sy, "sum_k2_component": comp,
            "sum_intercept": float(a * n), "share_k2_component": comp / sy if sy != 0 else float("nan")}


def d3(daily: dict[str, pd.DataFrame], cals: dict[str, np.ndarray], lines: tuple[str, ...] = D3_LINES) -> dict[str, Any]:
    out = {}
    for ln in lines:
        f = pair_frame(daily, cals, ln, "K2_ES")
        m = is2022(f.index)
        y, x, t = f["a"].to_numpy()[m], f["b"].to_numpy()[m], f["ta"].to_numpy()[m]
        sy = float(y.sum())
        out[ln] = {"calendar": pair_cal(ln, "K2_ES"), "all_2022_sessions": ols(x, y), "trading_days_2022": ols(x[t], y[t]),
                   "beside_share_on_k2_positive_days": (float(y[x > 0].sum()) / sy) if sy != 0 else float("nan"),
                   "beside_k2_positive_days": int((x > 0).sum()),
                   "note": ("L1 trades the same ES 15:30 -> 16:00 move as K2_ES on its days, by construction: reported, not "
                            "evidence of a shared regime") if ln == "L1" else ""}
    return out


# ================================================================================ D4
def book_stats(parts: dict[str, np.ndarray], B: np.ndarray) -> dict[str, Any]:
    names = list(parts)
    if len(B) < 3:
        return {"n": len(B)}
    v = {k: float(np.var(parts[k], ddof=1)) for k in names}
    vb = float(np.var(B, ddof=1))
    cov = {pk(a, b): float(np.cov(parts[a], parts[b], ddof=1)[0, 1]) for a, b in combinations(names, 2)}
    if abs(vb - (sum(v.values()) + 2 * sum(cov.values()))) > TOL_REL * max(1.0, vb):
        raise IdentityError(f"D4: Var(B) {vb!r} != sum var + 2 sum cov {sum(v.values()) + 2 * sum(cov.values())!r}: "
                            "the book is not the sum of its lines")
    rho = {pk(a, b): pearson(parts[a], parts[b]) for a, b in combinations(names, 2)}
    return {"n": int(len(B)), "var": v, "var_book": vb, "dr": sum(v.values()) / vb if vb > 0 else float("nan"),
            "rho": rho, "mean_pairwise_rho": float(np.mean(list(rho.values())))}


def d4(daily: dict[str, pd.DataFrame], cals: dict[str, np.ndarray], book: tuple[str, ...] = BOOK,
       book_fn: Callable[[dict[str, np.ndarray]], np.ndarray] | None = None) -> dict[str, Any]:
    c = cals["IDX"]
    parts = {ln: daily[ln].reindex(c)["net"].to_numpy(float) for ln in book}
    if any(np.isnan(v).any() for v in parts.values()):
        raise AggregationError("D4: a book line is not on the IDX calendar")
    B = book_fn(parts) if book_fn else np.sum(np.vstack([parts[k] for k in book]), axis=0)
    yr = c.astype("U4")
    per_year = {}
    for y in sorted(set(yr)):
        m = yr == y
        per_year[y] = {"sessions": int(m.sum()), "net_book": float(B[m].sum()), **{f"net_{k}": float(parts[k][m].sum()) for k in book},
                       "stats": book_stats({k: parts[k][m] for k in book}, B[m])}
    tot = float(B.sum())
    m22 = yr == "2022"
    return {"calendar": "IDX", "book": list(book), "total_net": tot, "share_2022": float(B[m22].sum()) / tot if tot else float("nan"),
            "per_year": per_year,
            "2022": book_stats({k: parts[k][m22] for k in book}, B[m22]),
            "other": book_stats({k: parts[k][~m22] for k in book}, B[~m22])}


# ================================================================================ the reading
def read_part_d(rho22: dict[str, float], pcond: dict[str, float], pairs: tuple[tuple[str, str], ...] = READ_PAIRS,
                rho_bar: float = RHO_BAR, p_bar: float = P_BAR) -> dict[str, Any]:
    """s.5: ONE BET if, for L1-L3 or L1-L4, rho_2022 >= 0.3 or the conditional overlap p < 0.01; SEPARATE otherwise."""
    fired, checked = [], []
    for a, b in pairs:
        k = pk(a, b)
        r, p = rho22[k], pcond[k]
        fr = bool(np.isfinite(r) and r >= rho_bar)
        fp = bool(np.isfinite(p) and p < p_bar)
        checked.append({"pair": k, "rho_2022": r, "p_conditional": p, "rho_fires": fr, "p_fires": fp})
        if fr:
            fired.append(f"{k}: rho_2022 {r:.4f} >= {rho_bar}")
        if fp:
            fired.append(f"{k}: D2 conditional p {p:.3g} < {p_bar}")
    return {"verdict": "ONE BET" if fired else "SEPARATE", "fired": fired, "checked": checked}


# (rho L1-L3, p L1-L3, rho L1-L4, p L1-L4, rho L1-L2, p L1-L2) -> the declared verdict
READING_CASES = (
    ((0.10, 0.50, 0.05, 0.60, 0.95, 1e-9), "SEPARATE"),     # L1-L2 one bet by both measures: not read
    ((0.30, 0.50, 0.05, 0.60, 0.00, 0.90), "ONE BET"),      # rho exactly at the bar
    ((0.2999, 0.50, 0.05, 0.60, 0.00, 0.90), "SEPARATE"),
    ((0.10, 0.50, 0.05, 0.0099, 0.00, 0.90), "ONE BET"),    # p alone, on L1-L4
    ((0.10, 0.01, 0.05, 0.60, 0.00, 0.90), "SEPARATE"),     # p exactly at the bar is not < 0.01
    ((0.10, 0.50, 0.45, 0.60, 0.00, 0.90), "ONE BET"),      # rho alone, on L1-L4
    ((float("nan"), 0.50, 0.05, 0.60, 0.00, 0.90), "SEPARATE"),
    ((-0.60, 0.50, -0.40, 0.60, 0.00, 0.90), "SEPARATE"),   # a negative rho is not one bet
)


def check_reading(reader: Callable[..., dict[str, Any]]) -> int:
    for vals, want in READING_CASES:
        r13, p13, r14, p14, r12, p12 = vals
        got = reader({"L1-L3": r13, "L1-L4": r14, "L1-L2": r12}, {"L1-L3": p13, "L1-L4": p14, "L1-L2": p12})["verdict"]
        if got != want:
            raise ReadingError(f"the reading gives {got} on {vals}; declared {want}")
    return len(READING_CASES)


# ================================================================================ the analysis
def analyse(df: pd.DataFrame, cals: dict[str, np.ndarray], pfun: Callable[[int, int, int, int], float] = hyper_p,
            reader: Callable[..., dict[str, Any]] = read_part_d) -> dict[str, Any]:
    daily = build_daily(df, cals)
    r1 = d1(daily, cals)
    r2 = d2(daily, cals, pfun=pfun)
    r3 = d3(daily, cals)
    r4 = d4(daily, cals)
    rho22 = {pk(a, b): r1[pk(a, b)]["2022"]["all_sessions"]["pearson"] for a, b in READ_PAIRS + (NOT_READ,)}
    pc = {pk(a, b): r2[pk(a, b)]["conditional"]["p"] for a, b in READ_PAIRS + (NOT_READ,)}
    reading = reader(rho22, pc)
    reading["not_read"] = {"pair": pk(*NOT_READ), "rho_2022": rho22[pk(*NOT_READ)], "p_conditional": pc[pk(*NOT_READ)],
                           "why": "s.5: L1-L2 (rho 0.87, the same trade by D711) is reported, not read"}
    lines_info = {ln: {"calendar": own_cal(ln), "sessions": int(len(daily[ln])), "trades_in_window": int(daily[ln]["n_trades"].sum()),
                       "traded_sessions": int(daily[ln]["traded"].sum()),
                       "multi_trade_sessions": int((daily[ln]["n_trades"] > 1).sum()),
                       "multi_trade_sessions_2022": int(((daily[ln]["n_trades"] > 1) & is2022(daily[ln].index)).sum()),
                       "traded_sessions_2022": int((daily[ln]["traded"] & is2022(daily[ln].index)).sum()),
                       "net_in_window": float(daily[ln]["net"].sum())} for ln in LINES_D1}
    return {"lines": lines_info, "D1": r1, "D2": r2, "D3": r3, "D4": r4, "reading": reading}


# ================================================================================ synthetic tables (self-test)
def synth_calendars() -> dict[str, np.ndarray]:
    es = np.array([str(d.date()) for d in pd.bdate_range(IDX_LO, HI)])
    ho = np.array([d for d in es if d not in ("2019-07-04", "2021-11-25")])
    return make_calendars(es, ho)


def synth_table(cals: dict[str, np.ndarray], rng: np.random.Generator, one_bet: bool) -> pd.DataFrame:
    rows = []
    probs = {"L1": 0.2, "L2": 0.2, "L3": 0.35, "L4": 0.2, "K1": 0.8, "K2_ES": 0.95, "K2_NQ": 0.95}
    nets: dict[str, dict[str, float]] = {}
    for ln in LINES_D1:
        c = cals[own_cal(ln)]
        t = rng.random(len(c)) < probs[ln]
        v = rng.standard_t(3, len(c)) * 40.0
        nets[ln] = {s: float(x) for s, x, tt in zip(c, v, t) if tt}
    if one_bet:            # L3 copies L1 on L1's days: rho = 1 on L1's trade days, full top overlap
        nets["L3"] = dict(nets["L1"])
    for ln, d in nets.items():
        for s, x in d.items():
            rows.append({"line": ln, "session": s, "side": 1, "entry_min": 360, "exit_min": 390, "net_usd": x})
    return pd.DataFrame(rows)


# ================================================================================ self-test
def selftest() -> int:
    t0 = time.time()
    fired: list[str] = []

    def must_raise(name: str, fn: Callable[[], Any], exc: type = PartDError) -> None:
        try:
            fn()
        except exc as e:
            fired.append(name)
            P(f"  RAISES on {name}: {type(e).__name__}: {str(e)[:120]}")
            return
        raise SystemExit(f"selftest: the '{name}' canary did not raise")

    # ---- the clean case on the real tables (structure only is printed: no statistic is shown before --run)
    from diag_d722_conditioners import load_conditioners
    from diag_d722_lines import load_lines
    df = load_lines()
    cals = calendars_from_panel(load_conditioners())
    res = analyse(df, cals)
    P(f"  clean case on the real tables: calendars IDX {len(cals['IDX'])} ({cals['IDX'][0]} .. {cals['IDX'][-1]}), "
      f"HO {len(cals['HO'])}, IDX_HO {len(cals['IDX_HO'])}; D1 {len(res['D1'])} pairs, D2 {len(res['D2'])}, D3 {len(res['D3'])} "
      f"lines, D4 {len(res['D4']['per_year'])} years; every gate passed")
    for ln, x in res["lines"].items():
        P(f"    {ln}: {x['calendar']} {x['sessions']} sessions, {x['trades_in_window']} trades on {x['traded_sessions']} sessions "
          f"({x['multi_trade_sessions']} with two or more; {x['multi_trade_sessions_2022']} in 2022)")
    json.dumps(to_json(res), allow_nan=False)
    l1 = df[df["line"] == "L1"]
    l3 = df[df["line"] == "L3"]

    # ---- 1. the seal
    planted = pd.concat([df, l1.iloc[[0]].assign(session="2024-01-02")], ignore_index=True)
    must_raise("seal: a planted 2024-01-02 L1 trade", lambda: build_daily(planted, cals), SealError)
    must_raise("seal: a planted 2024 trade on L4 only", lambda: build_daily(
        pd.concat([df, df[df["line"] == "L4"].iloc[[0]].assign(session="2024-03-04")], ignore_index=True), cals), SealError)
    must_raise("seal: a 2024 session in the ES calendar", lambda: make_calendars(np.append(cals["IDX"], "2024-01-02"), cals["HO"]),
               SealError)

    # ---- 2. daily aggregation
    dup = pd.concat([df, l1.iloc[[3]]], ignore_index=True)
    must_raise("aggregation: a duplicated L1 trade row (two trades one session)", lambda: build_daily(dup, cals), AggregationError)
    second = l1.iloc[[3]].assign(entry_min=375, exit_min=390, net_usd=1.0)
    must_raise("aggregation: a distinct second L1 trade on one session",
               lambda: build_daily(pd.concat([df, second], ignore_index=True), cals), AggregationError)
    for ln in ("L2", "L4", "K1", "K2_ES", "K2_NQ"):
        x = df[(df["line"] == ln) & (df["session"] >= HO_LO)]          # a row inside every calendar's window
        must_raise(f"aggregation: a duplicated {ln} row", lambda x_=x: build_daily(pd.concat([df, x_.iloc[[5]]], ignore_index=True),
                                                                                 cals), AggregationError)
    in_win = l3[l3["session"] >= IDX_LO]
    must_raise("aggregation: a duplicated L3 row (the multi-trade line)",
               lambda: build_daily(pd.concat([df, in_win.iloc[[7]]], ignore_index=True), cals), AggregationError)
    must_raise("aggregation: an L1 trade on a session off the calendar (a Saturday)",
               lambda: build_daily(pd.concat([df, l1.iloc[[0]].assign(session="2022-01-08")], ignore_index=True), cals),
               AggregationError)
    d_l1 = daily_series(l1, cals["IDX"], "L1")
    w_l1 = l1[(l1["session"] >= cals["IDX"][0]) & (l1["session"] <= cals["IDX"][-1])]
    zero_day = d_l1.index[~d_l1["traded"].to_numpy()][10]
    must_raise("zero-fill: a daily series missing one zero day", lambda: check_daily(d_l1.drop(index=zero_day), w_l1, cals["IDX"],
                                                                                    "L1"), AggregationError)
    alt = d_l1.copy()
    alt.loc[alt.index[alt["traded"].to_numpy()][4], "net"] += 0.01
    must_raise("conservation: one day's net altered by $0.01", lambda: check_daily(alt, w_l1, cals["IDX"], "L1"), AggregationError)
    nz = d_l1.copy()
    nz.loc[zero_day, "net"] = 0.5
    must_raise("zero-fill: an untraded day carrying a net", lambda: check_daily(nz, w_l1, cals["IDX"], "L1"), AggregationError)
    d3l = daily_series(l3, cals["IDX"], "L3")
    w3 = l3[(l3["session"] >= cals["IDX"][0]) & (l3["session"] <= cals["IDX"][-1])]
    if abs(math.fsum(d3l["net"]) - math.fsum(w3["net_usd"])) > 1e-6 or int(d3l["n_trades"].sum()) != len(w3):
        raise SystemExit("selftest: L3's summed daily series does not conserve its trades")
    P(f"  L3 conserves: {len(w3)} trades in the window on {int(d3l['traded'].sum())} sessions, the daily sum equals the trade "
      "total; every line's daily sum equals its trade total (check_daily ran on each)")

    # ---- 3. the hypergeometric
    for (k, N, K, n) in ((0, 10, 3, 4), (2, 50, 5, 6), (5, 186, 19, 19), (19, 186, 19, 19), (1, 20, 0, 5), (3, 20, 20, 5)):
        hyper_p(k, N, K, n)
    if hyper_p_exact(0, 10, 3, 4) != 1.0 or hyper_p_exact(4, 10, 3, 4) != 0.0:
        raise SystemExit("selftest: the exact hypergeometric's edges are wrong")
    P("  the hypergeometric (exact integers) equals scipy's sf(k-1) on six cases; identical and independent synthetic series:")
    cal_res = calibrate_overlap(hyper_p, P)
    P(f"    identical: k {cal_res['identical']['k']} of {cal_res['identical']['K']}, p {cal_res['identical']['p']:.3g}; "
      f"independent: mean p {cal_res['mean_p']:.3f} over {N_REPS} replications")

    def p_complement(k: int, N: int, K: int, n: int) -> float:
        return 1.0 - hyper_p_exact(k, N, K, n)

    def p_off_by_one(k: int, N: int, K: int, n: int) -> float:
        return hyper_p_exact(k + 1, N, K, n)          # P(X > k): the wrong tail edge

    def p_broken_exact(k: int, N: int, K: int, n: int) -> float:
        p = hyper_p_exact(k + 1, N, K, n)
        cross_check_p(k, N, K, n, p)
        return p

    must_raise("hypergeometric: the complement p (1 - p)", lambda: calibrate_overlap(p_complement), HyperError)
    must_raise("hypergeometric: the off-by-one tail P(X > k)", lambda: calibrate_overlap(p_off_by_one), HyperError)
    must_raise("hypergeometric: a broken exact implementation vs scipy", lambda: p_broken_exact(2, 50, 5, 6), HyperError)
    must_raise("hypergeometric: sizes out of range", lambda: hyper_p_exact(1, 10, 11, 3), HyperError)

    # ---- 4. the reading
    n_cases = check_reading(read_part_d)
    P(f"  the reading: {n_cases} declared synthetic cases give their verdicts (ONE BET and SEPARATE, both bars' edges, L1-L2 unread)")

    def reads_l1l2(r: dict, p: dict) -> dict:
        return read_part_d(r, p, pairs=READ_PAIRS + (NOT_READ,))

    def strict_rho(r: dict, p: dict) -> dict:
        return read_part_d(r, p, rho_bar=RHO_BAR + 1e-12)

    def ignores_p(r: dict, p: dict) -> dict:
        return read_part_d(r, {k: 1.0 for k in p})

    def and_not_or(r: dict, p: dict) -> dict:
        v = read_part_d(r, p)
        both = any(c["rho_fires"] and c["p_fires"] for c in v["checked"])
        return {**v, "verdict": "ONE BET" if both else "SEPARATE"}

    must_raise("reading: a reader that reads L1-L2", lambda: check_reading(reads_l1l2), ReadingError)
    must_raise("reading: rho > 0.3 in place of >= 0.3", lambda: check_reading(strict_rho), ReadingError)
    must_raise("reading: a reader that ignores the D2 p", lambda: check_reading(ignores_p), ReadingError)
    must_raise("reading: AND in place of OR", lambda: check_reading(and_not_or), ReadingError)

    # the full pipeline on synthetic trade tables
    sc = synth_calendars()
    rng = np.random.default_rng(SEED)
    one = analyse(synth_table(sc, rng, one_bet=True), sc)
    sep = analyse(synth_table(sc, rng, one_bet=False), sc)
    if one["reading"]["verdict"] != "ONE BET" or not any(f.startswith("L1-L3") for f in one["reading"]["fired"]):
        raise SystemExit(f"selftest: the synthetic ONE BET table reads {one['reading']}")
    if sep["reading"]["verdict"] != "SEPARATE":
        raise SystemExit(f"selftest: the synthetic SEPARATE table reads {sep['reading']}")
    P(f"  full pipeline, synthetic ONE BET table: {one['reading']['verdict']}, fired {one['reading']['fired']}")
    P("  full pipeline, synthetic SEPARATE table: " + sep["reading"]["verdict"] + "; " + "; ".join(
        f"{c['pair']} rho {c['rho_2022']:.3f} p {c['p_conditional']:.3f}" for c in sep["reading"]["checked"]))

    # ---- 5. D3's slope against lstsq, and the share's right quantity
    rng2 = np.random.default_rng(SEED + 1)
    x = rng2.normal(0, 10, 250)
    y = 0.7 * x + rng2.normal(0, 5, 250) + 2.0
    o = ols(x, y)
    if not abs(o["slope"] - 0.7) < 0.1 or abs((o["sum_k2_component"] + o["sum_intercept"]) - o["sum_y"]) > 1e-8:
        raise SystemExit(f"selftest: ols on a planted slope 0.7 gave {o['slope']}")
    if abs(o["share_k2_component"] - 1.0) < 1e-6:
        raise SystemExit("selftest: the K2-component share equals the intercept-inclusive ratio (1) on a planted intercept")
    P(f"  D3: planted slope 0.7 -> {o['slope']:.3f}; the K2-component share {o['share_k2_component']:.3f} differs from the "
      "intercept-inclusive ratio, which is 1 by the OLS identity")
    orig_lstsq = np.linalg.lstsq

    def bad_lstsq(A: Any, b: Any, rcond: Any = None) -> Any:
        s = orig_lstsq(A, b, rcond=rcond)
        return (s[0] * np.array([1.0, 1.01]),) + tuple(s[1:])

    np.linalg.lstsq = bad_lstsq
    try:
        must_raise("D3: the slope disagrees with its second implementation", lambda: ols(x, y), IdentityError)
    finally:
        np.linalg.lstsq = orig_lstsq

    # ---- 6. D4's identity (on a synthetic table: no real-data statistic is printed before --run)
    dd = build_daily(synth_table(sc, np.random.default_rng(SEED + 2), one_bet=False), sc)
    d4(dd, sc)
    must_raise("D4: a book that drops L3", lambda: d4(dd, sc, book_fn=lambda p: p["L1"] + p["L2"]), IdentityError)
    must_raise("D4: a book that double-counts L1", lambda: d4(dd, sc, book_fn=lambda p: 2 * p["L1"] + p["L2"] + p["L3"]),
               IdentityError)

    P(f"selftest OK: {len(fired)} canaries raised; {round(time.time() - t0, 1)} s")
    return 0


# ================================================================================ output
def to_json(o: Any) -> Any:
    if isinstance(o, dict):
        return {str(k): to_json(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [to_json(v) for v in o]
    if isinstance(o, (np.floating, float)):
        f = float(o)
        return f if math.isfinite(f) else None
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return o


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run() -> int:
    if OUT.exists():
        raise SystemExit(f"--run is run-once: {OUT.relative_to(REPO)} exists")
    t0 = time.time()
    from diag_d722_conditioners import CACHE_META, load_conditioners
    from diag_d722_lines import META, load_lines
    df = load_lines()
    cals = calendars_from_panel(load_conditioners())
    res = analyse(df, cals)
    cal_res = calibrate_overlap(hyper_p)
    lm = json.loads(META.read_text(encoding="utf-8"))
    cm = json.loads(CACHE_META.read_text(encoding="utf-8"))
    out = {
        "spec": SPEC, "runner": "scripts/diag_d722_part_d.py", "runner_sha256": sha(Path(__file__).resolve()),
        "inputs": {"lines_table_csv_sha256": lm["table_csv_sha256"], "conditioners_panel_sha256": cm["sha256"]},
        "seal": SEAL, "window": {"index_lines": [IDX_LO, HI], "ho_pairs_from": HO_LO},
        "calendars": {k: {"sessions": int(len(v)), "first": v[0], "last": v[-1]} for k, v in cals.items()},
        "definitions": {
            "daily": "net = sum of the line's trades that session, 0 where untraded; one trade a session asserted on every line but "
                     "L3 (MULTI_TRADE_LINES), whose same-session trades are summed and must be distinct and non-overlapping",
            "multi_trade_lines": MULTI_TRADE_LINES,
            "periods": "2022 = calendar year 2022; other = every other year of the pair's calendar, pooled",
            "D2": "top set = ceil(10 %) of the line's 2022 trading days by net (ties by date); conditional (DECLARED): population "
                  "= 2022 sessions both lines trade, top sets intersected with it, p = P(X >= k) hypergeometric, exact; "
                  "unconditional: population = all 2022 pair-calendar sessions",
            "D3": "OLS with intercept of the line's 2022 daily net on K2_ES's; share = slope * sum(K2_ES) / sum(line)",
            "D4": "B = L1 + L2 + L3 on IDX; DR = sum var / var(B), ddof 1",
            "reading": "ONE BET if for L1-L3 or L1-L4 Pearson rho_2022 (pair calendar, zeros included) >= 0.3 or D2 conditional "
                       "p < 0.01; SEPARATE otherwise; L1-L2 not read"},
        "hypergeometric_calibration": cal_res,
        **res,
        "wall_s": round(time.time() - t0, 2),
    }
    text = json.dumps(to_json(out), indent=1, allow_nan=False)
    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write(text + "\n")
    r = res["reading"]
    P(f"READING: {r['verdict']}" + (f" (fired: {'; '.join(r['fired'])})" if r["fired"] else ""))
    for c in r["checked"]:
        P(f"  {c['pair']}: rho_2022 {c['rho_2022']:.4f}, D2 conditional p {c['p_conditional']:.4g}")
    P(f"  not read {r['not_read']['pair']}: rho_2022 {r['not_read']['rho_2022']:.4f}, p {r['not_read']['p_conditional']:.4g}")
    P(f"wrote {OUT.relative_to(REPO)} in {out['wall_s']} s")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.run:
        return run()
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
