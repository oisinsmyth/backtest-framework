"""D786 Stage 0: five China-open fade filters read once against the outcome (the filter debate's candidates 2, 3,
21, 95 and 117). Spec: docs/decisions/D786-STAGE-0-PRE-REG-five-china-open-filters-read-once.md.

    python scripts/stage0_d786_china_open_five_filters.py --selftest     # SYSTEM interpreter (databento, pyarrow)
    python scripts/stage0_d786_china_open_five_filters.py --run

The construction is D765's MGC cell through D767's own functions (side = -sign(x), x = P09:30 - P09:00 Beijing, entry
at the 09:31 open, exit at P15:00), the passive book D770's primary through its own functions, and the selection
D767's walk-forward third. Each score is frozen as the debate declared it. The null rotates each score's INPUT over
the candidate sequence at every offset (exact, SE 0) and rebuilds the score with the session's own sign(x) and the
rotated series' own scale. Nothing on or after 2024-01-01 is read: every input is asserted.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))
import stage0_d765_china_open as C  # noqa: E402  (module bodies guarded by __main__)
import stage0_d767_china_open_fade_filter as F7  # noqa: E402
import stage0_d769_yuan_fix_residual as V  # noqa: E402
import stage0_d770_china_open_flow_passive as D7  # noqa: E402

SPEC = REPO / "docs" / "decisions" / "D786-STAGE-0-PRE-REG-five-china-open-filters-read-once.md"
OUT = REPO / "data" / "stage0_d786_china_open_five_filters.json"
SHAU = REPO / "data" / "fixtures" / "sge_shau_benchmark_2016_2023.csv"
SEAL = "2024-01-01"
SEAL_NS = int(pd.Timestamp(SEAL, tz="UTC").value)
OZ = 31.1035
DEV_WIN, SGE_STALE_DAYS = 20, 5
REL_LOOK, REL_MIN = 60, 40
KL, MIN_TR_WINDOW, MIN_TR_FILTERED = 20, 60, 50
BAR_ACC, T_G2, B1_PP = 0.05, 2.0, F7.BALANCE_PP
WINTER = (12, 1, 2, 3)
AUCTION_FROM = "2023-05-26"
WORKERS, AUDIT_N, SEED = 14, 40, 786
TAKER_PUB = {"n": 1697, "mean_gross": 3.14, "t_gross": 2.49, "mean_net": -2.79}
PASSIVE_PUB = {"n": 1466, "mean_gross": 2.12, "mean_net": -0.92}
F3_PUB, GUS_PUB = -0.051523129736182775, (0.052435521990603834, 1657)


class D786Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D786Error(msg)


# ================================================================================ the seal
def seal_days(days, what: str) -> None:
    d = pd.Series(list(days), dtype=str)
    need(bool((d < SEAL).all()), f"SEAL: {what} has a date on or after {SEAL}")


def seal_ns(ts, what: str) -> None:
    need(bool((np.asarray(ts).astype(np.int64) < SEAL_NS).all()), f"SEAL: {what} has a timestamp on or after {SEAL}")


def sealed_read(orig):
    """D770's paid-window reader: refuse a 2024 file before opening it, and re-assert every record after."""
    def read(root: str, schema: str, day: str):
        seal_days([day], f"paid {root} {schema} file request")
        a = orig(root, schema, day)
        if a is not None:
            seal_ns(a["ts_recv"], f"paid {root} {schema} {day} ts_recv")
            seal_ns(a["ts_event"], f"paid {root} {schema} {day} ts_event")
        return a
    return read


def _install_seal() -> None:
    if not getattr(D7, "_D786_SEALED", False):
        D7.read = sealed_read(D7.read)
        D7._D786_SEALED = True


def session_micro_sealed(args):
    _install_seal()
    return D7.session_micro(args)


# ================================================================================ the books (the oracle's build)
def build() -> dict[str, Any]:
    fm, hol = C._front_map(), C.load_holidays()
    seal_days([d for (_, d) in fm], "front map")
    seal_days(hol, "China holiday calendar")
    T = F7.cell_tables(fm, hol)
    for r, R in T["roots"].items():
        seal_ns(R["df"]["ts"], f"D765 cache {r} ts")
        seal_days(R["df"]["day"], f"D765 cache {r} day")
    sess = T["sess"]
    for k, s in sess.items():
        seal_days(s.index, f"session table {k}")
    c = C.CELLS["mgc"]
    s = sess["mgc"]
    e = s[(s["why"] == "eligible") & (s["x"] != 0)].copy()
    e["gross"] = -np.sign(e["x"].to_numpy(float)) * e["y"].to_numpy(float) * c["mult"]
    e["net"] = e["gross"] - c["cost"]
    p1, p2 = F7.PARTNERS["mgc"]
    partner_x = {"aud": F7.valid_x(sess["aud"]), "p1": F7.valid_x(sess[p1]), "p2": F7.valid_x(sess[p2])}
    sc = F7.scores(e, partner_x)
    days = list(e.index)
    seal_days(days, "taker candidates")
    R = T["roots"]["GC"]
    p930 = [float(R["C"][C.p_at(R, C.bj(d, "09:30"))]) for d in days]
    with ProcessPoolExecutor(WORKERS) as ex:
        gc = list(ex.map(session_micro_sealed, [("GC", d, p) for d, p in zip(days, p930)], chunksize=8))
    with ProcessPoolExecutor(WORKERS) as ex:
        mg = list(ex.map(session_micro_sealed, [("MGC", d, p) for d, p in zip(days, p930) if d >= "2022-01-03"],
                         chunksize=8))
    G = pd.DataFrame(gc)
    need(len(G) == len(days) and (G["day"].to_numpy() == np.array(days)).all(), "passive: sessions read != candidates")
    ok = (G["why"] == "ok").to_numpy()
    M = pd.DataFrame(mg)
    Mok = M[M["why"] == "ok"]
    adj = 0.0
    if len(Mok):
        j = Mok.set_index("day").join(G[ok].set_index("day"), rsuffix="_gc", how="inner")
        adj = float((((j["ask15"] - j["bid15"]) / 2 - (j["ask15_gc"] - j["bid15_gc"]) / 2) * D7.MULT).mean())
    cost_p = D7.COMMISSION + adj
    side = -np.sign(e["x"].to_numpy(float))
    sell_f = G["sell_through_filled"].fillna(False).to_numpy(bool) if "sell_through_filled" in G else np.zeros(len(G), bool)
    buy_f = G["buy_through_filled"].fillna(False).to_numpy(bool) if "buy_through_filled" in G else np.zeros(len(G), bool)
    filled = ok & np.where(side < 0, sell_f, buy_f)
    g_thr = np.where(side < 0, G.get("sell_through_gross", np.nan), G.get("buy_through_gross", np.nan)).astype(float)
    gross_p = np.where(filled, g_thr, np.nan)
    need(bool(np.isfinite(gross_p[filled]).all()), "passive: a filled session without an outcome")
    need(not np.allclose(gross_p[filled], e["gross"].to_numpy(float)[filled]), "right quantity: passive gross == taker gross")
    e["gross_p"] = gross_p
    e["net_p"] = gross_p - cost_p
    e["filled"] = filled
    e["month"] = pd.to_datetime(pd.Series(days)).dt.month.to_numpy()
    e["year"] = [d[:4] for d in days]
    e["F3"] = sc["F3"].to_numpy(float)
    e["U"] = sc["U"].to_numpy(float)
    e["x6a"] = partner_x["aud"].reindex(days).to_numpy(float)
    return {"e": e, "sess": sess, "roots": T["roots"], "cost_p": cost_p, "hol": hol, "fm": fm}


def reproduce(B: dict[str, Any]) -> dict[str, Any]:
    e = B["e"]
    g = e["gross"].to_numpy(float)
    tk = {"n": int(len(e)), "mean_gross": float(g.mean()), "t_gross": F7.tstat(g), "mean_net": float(e["net"].mean())}
    need(tk["n"] == TAKER_PUB["n"] and all(round(tk[k], 2) == TAKER_PUB[k] for k in ("mean_gross", "t_gross", "mean_net")),
         f"right quantity: the taker book is not D767's MGC pool ({tk})")
    f = e["filled"].to_numpy(bool)
    ps = {"n": int(f.sum()), "mean_gross": float(e["gross_p"][f].mean()), "mean_net": float(e["net_p"][f].mean())}
    need(ps["n"] == PASSIVE_PUB["n"] and all(round(ps[k], 2) == PASSIVE_PUB[k] for k in ("mean_gross", "mean_net")),
         f"right quantity: the passive book is not D770's ({ps})")
    upool = F7.pool_mask(e["U"].to_numpy(float))
    f3 = C.spearman(e["F3"].to_numpy(float)[upool], g[upool])
    need(abs(f3 - F3_PUB) < 1e-6, f"right quantity: spearman(F3, gross) {f3} is not D767's {F3_PUB}")
    s = B["sess"]["mgc"]
    el = s[s["why"] == "eligible"]
    m = np.isfinite(el["g_us"].to_numpy(float)) & np.isfinite(el["y"].to_numpy(float))
    gus = C.spearman(el["g_us"].to_numpy(float), el["y"].to_numpy(float))
    need(abs(gus - GUS_PUB[0]) < 1e-6 and int(m.sum()) == GUS_PUB[1], f"right quantity: rho(g_US, y) {gus} n {m.sum()}")
    return {"taker": tk, "passive": ps, "passive_cost": B["cost_p"], "spearman_F3_gross_D767": f3, "rho_gus_y_D765": gus}


# ================================================================================ the inputs (all pre-entry)
def load_shau(path: Path = SHAU) -> pd.DataFrame:
    s = pd.read_csv(path, dtype={"date_beijing": str}, encoding="utf-8")
    seal_days(s["date_beijing"], "SHAU benchmark")
    need(bool(s["shau_pm_cny_per_g"].between(200, 600).all()), "units: a SHAU PM outside 200-600 CNY/g")
    need(bool(s["date_beijing"].is_monotonic_increasing), "SHAU: dates not ordered")
    return s


def premium_table(R: dict[str, Any], shau: pd.DataFrame, fix: pd.DataFrame) -> pd.DataFrame:
    """Candidate 3's premium on each SGE day: SHAU_PM x 31.1035 / fix - GC at 14:15 Beijing, chained across rolls."""
    fx = fix.set_index("date")["usdcny_fix"]
    rows = []
    for d, pm in zip(shau["date_beijing"], shau["shau_pm_cny_per_g"]):
        i = C.p_at(R, C.bj(d, "14:15"))
        gc = float(R["C"][i]) if i is not None and not R["iso_c"][i] else np.nan
        k = int(R["K"][i]) if i is not None else -1
        rows.append((d, float(pm), gc, k, float(fx.get(d, np.nan))))
    P = pd.DataFrame(rows, columns=["d", "pm", "gc", "k", "fix"])
    p = P["pm"] * OZ / P["fix"] - P["gc"]
    dp = p.diff()
    same = (P["k"] == P["k"].shift(1)) & (P["k"] >= 0)
    dp = dp.where(same, 0.0)
    dp = dp.where(np.isfinite(dp), 0.0)
    ch = dp.cumsum()
    P["p"] = p
    P["dev"] = (ch - ch.shift(1).rolling(DEV_WIN, min_periods=DEV_WIN).mean()).where(np.isfinite(p))
    return P


def dev_for_sessions(P: pd.DataFrame, days: list[str]) -> np.ndarray:
    sd = P["d"].to_numpy()
    j = np.searchsorted(sd, np.array(days), side="left") - 1
    out = np.full(len(days), np.nan)
    for i, (jj, d) in enumerate(zip(j, days)):
        if jj < 0:
            continue
        need(sd[jj] < d, "lag: an SGE day not strictly before its session")
        if (pd.Timestamp(d) - pd.Timestamp(sd[jj])).days <= SGE_STALE_DAYS:
            out[i] = P["dev"].iloc[jj]
    return out


def western_returns(R: dict[str, Any], days: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """Candidate 95: R_US = log P(13:30 ET)/P(08:20 ET) and R_LDN = log P(08:20 ET)/P(03:00 ET) on the prior weekday."""
    rus, rld = [], []
    for d in days:
        u = C.prev_weekday(d)
        t0 = C.bj(d, "09:00")
        a_t, b_t, c_t = C.et(u, "03:00"), C.et(u, "08:20"), C.et(u, "13:30")
        need(c_t < t0, f"lag: 13:30 ET is not before 09:00 Beijing on {d}")
        q = C.Px(R)
        a, b, c = q.p(a_t), q.p(b_t), q.p(c_t)
        ok = len(q.k) == 1 and not q.void
        rus.append(math.log(c / b) if ok and b > 0 and c > 0 else np.nan)
        rld.append(math.log(b / a) if ok and a > 0 and b > 0 else np.nan)
    return np.array(rus, float), np.array(rld, float)


def rstar_ratio(q: np.ndarray, m: np.ndarray) -> tuple[float, float]:
    n = len(q)
    if n < KL + 30:
        return np.nan, np.nan
    d1 = m[1:] - m[:-1]
    dl = m[KL:] - m[:-KL]
    i1 = float(np.mean(q[:-1] * d1))
    cs = np.concatenate([[0.0], np.cumsum(q)])
    fut = cs[KL + 1:n + 1] - cs[1:n - KL + 1]
    X = np.column_stack([q[:-KL], fut])
    beta = np.linalg.lstsq(X, dl, rcond=None)[0]
    return (float(beta[0]) / i1 if i1 > 0 else np.nan), i1


def rstar_one(day: str) -> tuple:
    """Candidate 117's R* for one session from the paid GC tbbo in [09:00, 09:30) Beijing (and its two halves)."""
    _install_seal()
    need(day < SEAL, "seal: an R* session on or after 2024")
    tr = D7.read("GC", "tbbo", day)
    if tr is None:
        return day, np.nan, np.nan, np.nan, 0
    t0, t15, t30 = D7.bj_ns(day, "09:00"), D7.bj_ns(day, "09:15"), D7.bj_ns(day, "09:30")
    ts = tr["ts_recv"].astype(np.int64)
    tr = tr[(ts >= t0) & (ts < t30)]
    need(bool((tr["ts_recv"].astype(np.int64) < t30).all()), "outcome-blind: a tbbo record at or after 09:30")
    if len(tr) < MIN_TR_WINDOW:
        return day, np.nan, np.nan, np.nan, int(len(tr))
    ids, inv = np.unique(tr["instrument_id"], return_inverse=True)
    k = int(np.argmax(np.bincount(inv, weights=tr["size"].astype(np.int64))))
    tr = tr[inv == k]
    a, b = D7.px(tr["ask_px_00"]), D7.px(tr["bid_px_00"])
    side = tr["side"]
    ok = np.isfinite(a) & np.isfinite(b) & (a > b) & ((side == b"B") | (side == b"A"))
    tr, a, b, side = tr[ok], a[ok], b[ok], side[ok]
    if len(tr) < MIN_TR_FILTERED:
        return day, np.nan, np.nan, np.nan, int(len(tr))
    q = np.where(side == b"B", 1.0, -1.0)
    m = (a + b) / 2 / D7.TICK
    R, _ = rstar_ratio(q, m)
    h = tr["ts_recv"].astype(np.int64) < t15
    R1, _ = rstar_ratio(q[h], m[h])
    R2, _ = rstar_ratio(q[~h], m[~h])
    return day, R, R1, R2, int(len(q))


def _rstar_chunk(days: list[str]) -> list[tuple]:
    return [rstar_one(d) for d in days]


def rstar_all(days: list[str], workers: int = WORKERS) -> pd.DataFrame:
    with ProcessPoolExecutor(workers) as ex:
        parts = list(ex.map(_rstar_chunk, [days[i::workers] for i in range(workers)]))
    res: list[Any] = [None] * len(days)
    for i, part in enumerate(parts):
        for j, r in enumerate(part):
            res[i + j * workers] = r
    need([r[0] for r in res] == days, "R*: stride reassembly lost the day order")
    return pd.DataFrame(res, columns=["day", "R", "R1", "R2", "n"])


# ================================================================================ scores
def prior_rel(v: np.ndarray) -> np.ndarray:
    return pd.Series(v).shift(1).rolling(REL_LOOK, min_periods=REL_MIN).median().to_numpy()


def make_score(z: np.ndarray, sx: np.ndarray, kind: str) -> np.ndarray:
    if kind == "neg_sx":
        return -sx * z / F7.prior_median_abs(z)
    if kind == "pos_sx":
        return sx * z / F7.prior_median_abs(z)
    if kind == "neg_rel":
        return -(z - prior_rel(z))
    raise D786Error(f"unknown score kind {kind}")


def fast_pool(s: np.ndarray) -> np.ndarray:
    """D767's pool_mask, vectorised: i >= 250, finite score, >= 100 finite among the prior 250."""
    fin = np.isfinite(s)
    c = np.concatenate([[0], np.cumsum(fin)])
    n = len(s)
    i = np.arange(n)
    prior = np.where(i >= F7.WF, c[i] - c[np.maximum(i - F7.WF, 0)], 0)
    return (i >= F7.WF) & fin & (prior >= F7.WF_MIN)


def _rot_chunk(args: tuple) -> np.ndarray:
    """Rows: [offset, rho taker, rho passive, third mean net taker, its count, third mean net passive, its count]."""
    z, sx, kind, gross, gross_p, net, net_p, filled, offsets = args
    out = np.full((len(offsets), 7), np.nan)
    for j, k in enumerate(offsets):
        s = make_score(np.roll(z, k), sx, kind)
        pool = fast_pool(s)
        pf = pool & filled
        sel = F7.wf_select(s)
        sp = sel & filled
        out[j] = [k, C.spearman(s[pool], gross[pool]), C.spearman(s[pf], gross_p[pf]),
                  net[sel].mean() if sel.any() else np.nan, sel.sum(),
                  net_p[sp].mean() if sp.any() else np.nan, sp.sum()]
    return out


def rotation(z, sx, kind, gross, gross_p, net, net_p, filled, workers: int = WORKERS,
             offsets: list[int] | None = None) -> np.ndarray:
    n = len(z)
    offs = list(range(n)) if offsets is None else offsets
    if workers == 1:
        return _rot_chunk((z, sx, kind, gross, gross_p, net, net_p, filled, offs))
    with ProcessPoolExecutor(workers) as ex:
        parts = list(ex.map(_rot_chunk, [(z, sx, kind, gross, gross_p, net, net_p, filled, offs[i::workers])
                                         for i in range(workers)]))
    out = np.vstack(parts)
    return out[np.argsort(out[:, 0], kind="mergesort")]


def null_summary(obs: float, d: np.ndarray) -> dict[str, Any]:
    d = d[np.isfinite(d)]
    return {"observed": obs, "p50": float(np.quantile(d, 0.5)), "p95": float(np.quantile(d, 0.95)),
            "rank": float((d < obs).mean()), "p_one_sided": float((1 + (d >= obs).sum()) / (1 + len(d))),
            "offsets": int(len(d))}


# ================================================================================ audits
def _med(v: list[float]) -> float:
    v = sorted(v)
    h = len(v) // 2
    return v[h] if len(v) % 2 else (v[h - 1] + v[h]) / 2


def audit_score(z: np.ndarray, sx: np.ndarray, kind: str, s: np.ndarray, sample: list[int]) -> None:
    """Second implementation of each score on sampled sessions: explicit loops, sorted-list medians, no pandas."""
    for i in sample:
        if kind in ("neg_sx", "pos_sx"):
            prior = [abs(v) for v in z[max(0, i - F7.LOOK):i] if math.isfinite(v)]
            sc = _med(prior) if len(prior) >= F7.LOOK_MIN else float("nan")
            sgn = -1.0 if kind == "neg_sx" else 1.0
            mine = sgn * sx[i] * z[i] / sc if math.isfinite(z[i]) and math.isfinite(sc) else float("nan")
        else:
            prior = [v for v in z[max(0, i - REL_LOOK):i] if math.isfinite(v)]
            mine = -(z[i] - _med(prior)) if len(prior) >= REL_MIN and math.isfinite(z[i]) else float("nan")
        need((math.isnan(mine) and math.isnan(s[i])) or abs(mine - s[i]) <= 1e-9 * max(1.0, abs(mine)),
             f"lag audit: the {kind} score differs at position {i} ({mine} vs {s[i]})")


def audit_dev(P: pd.DataFrame, sample_rows: list[int]) -> None:
    """Second implementation of the chain and the 20-day demean on sampled SGE days."""
    p = (P["pm"] * OZ / P["fix"] - P["gc"]).to_list()
    k = P["k"].to_list()
    chain, acc = [], 0.0
    for i in range(len(p)):
        if i > 0 and k[i] == k[i - 1] and k[i] >= 0 and math.isfinite(p[i]) and math.isfinite(p[i - 1]):
            acc += p[i] - p[i - 1]
        chain.append(acc)
    for i in sample_rows:
        if i < DEV_WIN or not math.isfinite(p[i]):
            need(not math.isfinite(P["dev"].iloc[i]), f"lag audit: dev defined without a full window at {i}")
            continue
        mine = chain[i] - sum(chain[i - DEV_WIN:i]) / DEV_WIN
        need(abs(mine - P["dev"].iloc[i]) <= 1e-8 * max(1.0, abs(mine)), f"lag audit: dev differs at SGE row {i}")


def sign_audit(side: float = 1.0) -> None:
    x, y = np.array([0.5, -0.5]), np.array([-1.0, 1.0])
    pnl = side * -np.sign(x) * y * 10.0
    need(bool((pnl > 0).all()), "sign audit: a reversal did not pay the fade")


# ================================================================================ reporting
def book_stats(gross: np.ndarray, net: np.ndarray, days: np.ndarray) -> dict[str, Any]:
    m = np.isfinite(net)
    gross, net, days = gross[m], net[m], days[m]
    n = len(net)
    if n < 20:
        return {"n": n, "note": "n<20"}
    yrs = sorted({d[:4] for d in days})
    span = (pd.Timestamp(days[-1]) - pd.Timestamp(days[0])).days / 365.25
    tpy = n / max(span, 1e-9)
    sd = net.std(ddof=1)
    down = np.sqrt(np.mean(np.minimum(net, 0.0) ** 2))
    srt = np.sort(net)
    k = max(1, int(round(0.01 * n)))
    wins, losses = net[net > 0], net[net <= 0]
    eq = np.cumsum(net)
    by_year = pd.Series(net).groupby(pd.Series([d[:4] for d in days])).sum()
    best = by_year.idxmax()
    order = np.argsort(net)
    s = pd.Series(net)
    return {"n": n, "trades_per_year": round(tpy, 1), "mean_gross": float(gross.mean()), "t_gross": F7.tstat(gross),
            "mean_net": float(net.mean()), "t_net": F7.tstat(net), "median_net": float(np.median(net)),
            "win_rate": float((net > 0).mean()),
            "payoff": float(wins.mean() / -losses.mean()) if len(wins) and len(losses) and losses.mean() < 0 else None,
            "skew": float(s.skew()), "kurtosis_excess": float(s.kurt()),
            "mean_ex_top1pct": float(srt[:-k].mean()), "mean_ex_bottom1pct": float(srt[k:].mean()),
            "mean_trimmed_both": float(srt[k:-k].mean()),
            "sharpe_net_ann": float(net.mean() / sd * math.sqrt(tpy)) if sd > 0 else None,
            "sortino_net_ann": float(net.mean() / down * math.sqrt(tpy)) if down > 0 else None,
            "sharpe_gross_ann": float(gross.mean() / gross.std(ddof=1) * math.sqrt(tpy)),
            "max_drawdown": float((np.maximum.accumulate(eq) - eq).max()), "total_net": float(net.sum()),
            "breakeven_cost_rt": float(gross.mean()),
            "profitable_years": f"{int((by_year > 0).sum())} of {len(yrs)}", "best_year": str(best),
            "mean_net_without_best_year": float(net[np.array([d[:4] != best for d in days])].mean()),
            "worst5": [(str(days[i]), round(float(net[i]), 2)) for i in order[:5]],
            "best5": [(str(days[i]), round(float(net[i]), 2)) for i in order[-5:][::-1]]}


def splits(s: np.ndarray, gross: np.ndarray, pool: np.ndarray, e: pd.DataFrame) -> dict[str, Any]:
    days = e.index.to_numpy()
    edt = e["edt"].to_numpy(bool)
    win = np.isin(e["month"].to_numpy(), WINTER)
    after = days >= AUCTION_FROM

    def rho(mask):
        m = pool & mask
        return {"rho": C.spearman(s[m], gross[m]) if m.sum() >= 10 else None, "n": int(m.sum())}
    yr = e["year"].to_numpy()
    return {"EST": rho(~edt), "EDT": rho(edt), "Dec_Mar": rho(win), "Apr_Nov": rho(~win),
            "years": {y: rho(yr == y) for y in sorted(set(yr))},
            "before_shfe_auction": rho(~after), "after_shfe_auction": rho(after)}


def evaluate(name: str, z: np.ndarray, kind: str, e: pd.DataFrame, workers: int) -> dict[str, Any]:
    sx = np.sign(e["x"].to_numpy(float))
    gross, net = e["gross"].to_numpy(float), e["net"].to_numpy(float)
    gross_p, net_p, filled = e["gross_p"].to_numpy(float), e["net_p"].to_numpy(float), e["filled"].to_numpy(bool)
    days = e.index.to_numpy()
    s = make_score(z, sx, kind)
    pool = F7.pool_mask(s)
    need(bool((fast_pool(s) == pool).all()), f"{name}: the vectorised pool differs from D767's pool_mask")
    sel = F7.wf_select(s)
    F7.audit_flags(s, sel)
    rng = np.random.default_rng(SEED)
    audit_score(z, sx, kind, s, sorted(rng.choice(np.arange(REL_LOOK, len(z)), size=AUDIT_N, replace=False).tolist()))
    pf, sp = pool & filled, sel & filled
    rho_t, rho_p = C.spearman(s[pool], gross[pool]), C.spearman(s[pf], gross_p[pf])
    rot = rotation(z, sx, kind, gross, gross_p, net, net_p, filled, workers)
    need(int(rot[0, 0]) == 0 and len(rot) == len(z), f"{name}: the rotation does not enumerate every offset")
    need(abs(rot[0, 1] - rho_t) < 1e-12 and abs(rot[0, 3] - net[sel].mean()) < 1e-9 and int(rot[0, 4]) == int(sel.sum()),
         f"{name}: rotation offset 0 does not reproduce the observed statistics")
    nul = rot[1:]
    acc_t, acc_p = null_summary(rho_t, nul[:, 1]), null_summary(rho_p, nul[:, 2])
    third_t, third_p = null_summary(float(net[sel].mean()), nul[:, 3]), null_summary(float(net_p[sp].mean()), nul[:, 5])
    bal = F7.balance(list(days[sel]), list(days[pool]))
    win = np.isin(e["month"].to_numpy(), WINTER)
    st_t = book_stats(gross[sel], net[sel], days[sel])
    st_p = book_stats(gross_p[sp], net_p[sp], days[sp])
    b2_t, b2_p = float(net[sel & ~win].sum()), float(net_p[sp & ~win].sum())

    def gates(acc, st, b2):
        g = {"A": bool(acc["observed"] >= BAR_ACC and acc["observed"] > acc["p95"]),
             "G2": bool(st.get("mean_net", -1) > 0 and (st.get("t_net") or 0) >= T_G2),
             "B1": bool(bal["max_month_dev_pp"] <= B1_PP), "B2": bool(b2 > 0)}
        if not g["A"]:
            r = "NO EFFECT"
        elif not g["G2"]:
            r = "BELOW THE BAR"
        elif not g["B1"]:
            r = "B1 FAILS"
        elif not g["B2"]:
            r = "SEASONAL"
        else:
            r = "SUPPORTED IN-SAMPLE"
        g["reading"] = r
        g["season_free_pass"] = bool(g["A"] and g["G2"] and g["B1"])
        return g
    x, gg = e["x"].to_numpy(float), e["g"].to_numpy(float)
    prof = {"z_defined": int(np.isfinite(z).sum()), "pool": int(pool.sum()), "selected": int(sel.sum()),
            "passive_pool": int(pf.sum()), "passive_selected": int(sp.sum()),
            "rho_S_absx": C.spearman(s[pool], np.abs(x)[pool]), "rho_Z_x": C.spearman(z, x), "rho_Z_g": C.spearman(z, gg),
            "max_month_dev_pp": bal["max_month_dev_pp"], "max_year_dev_pp": bal["max_year_dev_pp"],
            "DecMar_share_sel_vs_pool": (float(win[sel].mean()), float(win[pool].mean()))}
    return {"name": name, "kind": kind, "profile": prof,
            "accuracy_taker": acc_t, "accuracy_passive": acc_p, "accuracy_se": 1 / math.sqrt(max(int(pool.sum()) - 1, 1)),
            "third_mean_net_null_taker": third_t, "third_mean_net_null_passive": third_p,
            "book_taker": st_t, "book_passive": st_p, "B2_net_outside_DecMar_taker": b2_t, "B2_net_outside_DecMar_passive": b2_p,
            "gates_taker": gates(acc_t, st_t, b2_t), "gates_passive": gates(acc_p, st_p, b2_p),
            "splits_taker": splits(s, gross, pool, e), "_sel": sel}


def component_line(e: pd.DataFrame, sels: dict[str, np.ndarray]) -> dict[str, Any]:
    import stage0_d777_post_close_fade as P7
    b = P7.load_bars()
    d775 = P7.d775_daily(b)
    _, d777 = P7.daily_book(P7.panel(b, "NQ"), 4.07)
    d777 = d777.groupby(level=0).sum()
    days = e.index.to_numpy()
    net = e["net"].to_numpy(float)
    base = pd.Series(net, index=days)
    out: dict[str, Any] = {"joined_on": "the session date each runner keys on (as D780)",
                           "not_computed": "D755's other-lines file (temp/d755_other_lines.csv) no longer exists"}
    for k, sel in sels.items():
        daily = pd.Series(net[sel], index=days[sel])
        row = {}
        for nm, other in (("unfiltered_d765_mgc_fade", base), ("d775", d775), ("d777_mnq", d777)):
            row[nm] = round(float(pd.concat([daily, other], axis=1).fillna(0.0).corr().iloc[0, 1]), 3)
        out[k] = row
    return out


# ================================================================================ the study
CANDS = (("c2_B-US", "neg_sx", False, 0.0524), ("c21_A-INVAUD", "pos_sx", False, 0.0515),
         ("c3_A-PREM", "neg_sx", True, -0.0032), ("c95_A-CLIENTELE", "pos_sx", True, 0.0004),
         ("c117_A-TRANSIENT", "neg_rel", True, None))


def inputs(B: dict[str, Any]) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    e = B["e"]
    days = list(e.index)
    R = B["roots"]["GC"]
    shau = load_shau()
    fix = V.load_fix()
    P = premium_table(R, shau, fix)
    rng = np.random.default_rng(SEED)
    audit_dev(P, sorted(rng.choice(np.arange(len(P)), size=AUDIT_N, replace=False).tolist()))
    dev = dev_for_sessions(P, days)
    rus, rld = western_returns(R, days)
    rs = rstar_all(days)
    for r in _rstar_chunk(days[::131]):                            # serial == the stride's result, bit for bit
        need(np.array_equal(np.array(r[1:4], float), rs.iloc[days.index(r[0])][["R", "R1", "R2"]].to_numpy(float),
                            equal_nan=True), f"R*: chunk != whole at {r[0]}")
    Z = {"c2_B-US": e["g_us"].to_numpy(float), "c21_A-INVAUD": e["x6a"].to_numpy(float), "c3_A-PREM": dev,
         "c95_A-CLIENTELE": rus, "c117_A-TRANSIENT": rs["R"].to_numpy(float), "c95_secondary_London": rld}
    meta = {"sge_days": int(len(P)), "gc_at_1415_missing": int(P["gc"].isna().sum()),
            "rstar_split_half_rho": C.spearman(rs["R1"].to_numpy(float), rs["R2"].to_numpy(float)),
            "rstar_median_by_year": rs.groupby(rs["day"].str[:4])["R"].median().round(3).to_dict()}
    return Z, meta


def run() -> int:
    need(not OUT.exists(), f"{OUT.name} exists: D786 is run-once")
    t0 = time.time()
    sign_audit()
    try:
        sign_audit(-1.0)
    except D786Error:
        pass
    else:
        raise D786Error("the sign audit did not raise on a mirrored book")
    B = build()
    rep = reproduce(B)
    print("reproduced:", rep, f"{time.time() - t0:.0f}s", flush=True)
    Z, meta = inputs(B)
    print("inputs built:", meta, f"{time.time() - t0:.0f}s", flush=True)
    e = B["e"]
    res: dict[str, Any] = {"spec": SPEC.name, "seal": f"nothing on or after {SEAL}", "window": [C.LO, C.HI],
                           "reproduced": rep, "inputs": meta, "candidates": {}}
    sels = {}
    for name, kind, unread, derived in CANDS + (("c95_secondary_London", "pos_sx", False, None),):
        r = evaluate(name, Z[name], kind, e, WORKERS)
        sels[name] = r.pop("_sel")
        r["unread_before_D786"] = unread
        r["derived_or_published"] = derived
        if derived is not None:
            r["measured_minus_derived_in_se"] = (r["accuracy_taker"]["observed"] - derived) / r["accuracy_se"]
        res["candidates"][name] = r
        g = r["gates_taker"]
        print(f"{name}: rho {r['accuracy_taker']['observed']:+.4f} (p95 {r['accuracy_taker']['p95']:+.4f}) "
              f"| third net {r['book_taker'].get('mean_net', float('nan')):+.2f} t {r['book_taker'].get('t_net', float('nan')):.2f} "
              f"| {g['reading']} | {time.time() - t0:.0f}s", flush=True)
    ps = {k: res["candidates"][k]["accuracy_taker"]["p_one_sided"] for k, _, u, _ in CANDS if u}
    hm = F7.holm(ps)
    res["holm_unread"] = hm
    for k, _, u, _ in CANDS:
        g = res["candidates"][k]["gates_taker"]
        g["nominates"] = bool(u and g["reading"] == "SUPPORTED IN-SAMPLE" and hm.get(k, 1.0) <= 0.05)
        if not u:
            g["label"] = "POST HOC (published accuracy); cannot nominate"
    res["component_line"] = component_line(e, {k: v for k, v in sels.items() if k != "c95_secondary_London"})
    res["any_nomination"] = any(res["candidates"][k]["gates_taker"]["nominates"] for k, _, _, _ in CANDS)
    res["wall_s"] = round(time.time() - t0, 1)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, default=str)
    print("nomination:", res["any_nomination"], "| holm", hm, f"| {res['wall_s']}s ->", OUT.relative_to(REPO), flush=True)
    return 0


# ================================================================================ self-test
def selftest() -> int:
    t0 = time.time()
    sign_audit()
    try:
        sign_audit(-1.0)
    except D786Error:
        pass
    else:
        raise D786Error("the sign audit did not raise on a mirrored book")
    # the seal: planted 2024 rows raise in every loader this study uses
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "shau.csv"
        pd.DataFrame({"date_beijing": ["2023-12-29", "2024-01-02"], "shau_am_cny_per_g": [480.0, 481.0],
                      "shau_pm_cny_per_g": [480.0, 481.0]}).to_csv(p, index=False, encoding="utf-8")
        try:
            load_shau(p)
        except D786Error:
            pass
        else:
            raise D786Error("seal: the SHAU loader did not raise on a planted 2024 row")
    for fn, arg in ((seal_days, ["2023-12-29", "2024-01-02"]), (seal_ns, [SEAL_NS - 1, SEAL_NS])):
        try:
            fn(arg, "planted")
        except D786Error:
            pass
        else:
            raise D786Error(f"seal: {fn.__name__} did not raise on a planted 2024 value")
    try:
        sealed_read(lambda r, s, d: None)("GC", "tbbo", "2024-01-02")
    except D786Error:
        pass
    else:
        raise D786Error("seal: the paid reader did not refuse a 2024 file")
    need(V.load_fix()["date"].max() < SEAL, "seal: the fix fixture reaches 2024")
    # the gates fire: a planted score passes A, a shuffled one fails
    rng = np.random.default_rng(1)
    n = 1500
    gross = rng.standard_t(3, n) * 30
    x = rng.normal(size=n)
    sx = np.sign(x)
    zp = -sx * (gross / 30 + rng.normal(scale=2.0, size=n))         # neg_sx -> S = gross/30 + noise, rho about 0.3
    e = pd.DataFrame({"x": x, "gross": gross, "net": gross - 5.93, "gross_p": gross, "net_p": gross - 3.0,
                      "filled": np.ones(n, bool), "edt": rng.random(n) < 0.6, "g": rng.normal(size=n)},
                     index=pd.date_range("2016-01-04", periods=n, freq="B").strftime("%Y-%m-%d"))
    e["month"] = pd.to_datetime(e.index).month
    e["year"] = [d[:4] for d in e.index]
    r1 = evaluate("planted", zp, "neg_sx", e, 4)
    need(r1["gates_taker"]["A"], f"self-test: a planted score failed A ({r1['accuracy_taker']})")
    r0 = evaluate("shuffled", rng.permutation(zp), "neg_sx", e, 4)
    need(not r0["gates_taker"]["A"], f"self-test: a shuffled score passed A ({r0['accuracy_taker']})")
    # rotation chunk == whole, bit for bit
    gp, npn, fl = e["gross_p"].to_numpy(), e["net_p"].to_numpy(), e["filled"].to_numpy()
    whole = rotation(zp, sx, "neg_sx", gross, gp, gross - 5.93, npn, fl, workers=1, offsets=list(range(0, n, 97)))
    par = rotation(zp, sx, "neg_sx", gross, gp, gross - 5.93, npn, fl, workers=4, offsets=list(range(0, n, 97)))
    need(np.array_equal(whole, par, equal_nan=True), "rotation: chunk != whole")
    # the score audits raise on a broken score
    s = make_score(zp, sx, "neg_sx")
    bad = s.copy()
    bad[300] += 1.0
    try:
        audit_score(zp, sx, "neg_sx", bad, [300])
    except D786Error:
        pass
    else:
        raise D786Error("lag audit: a broken score was not caught")
    zr = rng.normal(size=n)
    audit_score(zr, sx, "neg_rel", make_score(zr, sx, "neg_rel"), list(range(60, 400, 7)))
    # R*: the estimator recovers a planted build-up (informed) against decay (transient), and the stride is exact
    q = rng.choice([-1.0, 1.0], size=2000)
    pre = np.r_[0.0, np.cumsum(q)[:-1]]                            # pre-trade mid: trades strictly before t
    m_inf = 0.5 * pre                                              # permanent impact only: R* = 1
    m_tr = 0.1 * pre + 0.4 * np.r_[0.0, q[:-1]]                    # 0.4 of 0.5 reverts after one trade: R* = 0.2
    need(abs(rstar_ratio(q, m_inf)[0] - 1.0) < 0.05 and abs(rstar_ratio(q, m_tr)[0] - 0.2) < 0.05,
         f"R*: the estimator failed its plant ({rstar_ratio(q, m_inf)[0]}, {rstar_ratio(q, m_tr)[0]})")
    samp = [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2022-03-01", "2022-03-14")][:8]
    a = _rstar_chunk(samp)
    b = rstar_all(samp, workers=3)
    need(all(np.array_equal(np.array(x_[1:4], float), b.iloc[i][["R", "R1", "R2"]].to_numpy(float), equal_nan=True)
             for i, x_ in enumerate(a)), "R*: chunk != whole")
    # candidate 3's chain: a planted roll step is removed
    P = pd.DataFrame({"d": [f"2020-01-{i:02d}" for i in range(1, 31)], "pm": 400.0, "fix": 7.0,
                      "gc": [1800.0] * 15 + [1810.0] * 15, "k": [1] * 15 + [2] * 15})
    p = P["pm"] * OZ / P["fix"] - P["gc"]
    dp = p.diff()
    dp = dp.where((P["k"] == P["k"].shift(1)) & (P["k"] >= 0), 0.0).fillna(0.0)
    need(float(dp.cumsum().abs().max()) == 0.0, "chain: a roll step leaked into the chained premium")
    print(f"selftest OK ({time.time() - t0:.0f}s)", flush=True)
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
