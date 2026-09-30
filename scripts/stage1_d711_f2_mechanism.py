"""D711: two mechanism tests of F2 that leave the vault unspent. A1 -- F2's rule on ES at the placebo clocks 10:30 /
11:30 / 12:30 / 13:30 (14:30 the shoulder, 15:30 the anchor), each the prior 60 minutes' sign held 30 minutes. A2 --
F2 unchanged at 15:30 on NQ / YM / RTY. Spec: docs/decisions/D711-PRE-REG-f2-placebo-clocks-and-other-index-roots.md
(a39ec041); the principal: "A1 and A2 as one pre-registration go please".

    uv run python scripts/stage1_d711_f2_mechanism.py --selftest
    uv run python scripts/stage1_d711_f2_mechanism.py --time
    uv run python scripts/stage1_d711_f2_mechanism.py --run        # once

The construction is D707 s.1 with the clock or the root replaced. The generic loader is proved equal to D618's load_es
(through D707's frame) on ES at 15:30, and D707's frozen in-sample answer is reproduced before any statistic. In-sample
to 2023-12-29 on every root. Writes data/stage1_d711_f2_mechanism.json (statistics only).
"""
from __future__ import annotations

import argparse
import contextlib
import json
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Callable, Iterator

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import stage1_d703_last_hour_ep_filter as E  # noqa: E402
import vault_d707_last_hour_f2 as V  # noqa: E402

M702, D, C, P694 = E.Z, E.D, E.C, E.P694
FIX = REPO / "data" / "fixtures"
OUT = REPO / "data" / "stage1_d711_f2_mechanism.json"
FROZEN707 = REPO / "data" / "FROZEN_vault_d707_last_hour_f2.json"
IN_FROM, IN_END, SEAL = "2016-01-04", "2023-12-29", "2024-01-01"
MIN_BARS, EDGE, Q = 380, 21, 0.8
PLACEBO = ("10:30", "11:30", "12:30", "13:30")
SHOULDER, ANCHOR = "14:30", "15:30"
A2_ROOTS = ("NQ", "YM", "RTY")
ES_COST = 4.42  # D705 / D707 round the MES line (4.418) to $4.42, and that rounding is kept (D711 s.1)


class D711Error(RuntimeError):
    pass


def hm(t: str, minutes: int) -> str:
    return (pd.Timestamp("2000-01-01 " + t) + pd.Timedelta(minutes=minutes)).strftime("%H:%M")


def cost_line(root: str) -> dict[str, float]:
    cl = P694.cost_lines(root)
    return {"usd_per_point": cl["usd_per_point"], "cost": ES_COST if root == "ES" else cl["cost_single_usd"],
            "cost_single_usd_file": cl["cost_single_usd"]}


@contextlib.contextmanager
def cost_as(c: float) -> Iterator[None]:
    """D703's book() reads its module COST; score each root at its own line and put it back."""
    old = E.COST
    E.COST = c
    try:
        yield
    finally:
        E.COST = old


# ================================================================================ the build
def load_root(root: str, end: str = IN_END) -> dict[str, Any]:
    if end >= SEAL:
        raise D711Error(f"seal: a build of {root} through {end} was asked for; D711 is in-sample to {IN_END}")
    b = pd.read_csv(FIX / f"fut_{root}_rth_1m.csv.gz", dtype={"day": str, "hhmm": str, "contract": str}, encoding="utf-8")
    b = b[(b["day"] >= IN_FROM) & (b["day"] <= end)]
    if (b["day"] >= SEAL).any():
        raise D711Error(f"seal: a {root} bar on or after 2024-01-01 was read")
    nb = b.groupby("day").size()
    close = b.pivot(index="day", columns="hhmm", values="close")
    open_ = b.pivot(index="day", columns="hhmm", values="open")
    keep = nb.reindex(close.index) >= MIN_BARS
    close, open_ = close[keep], open_[keep]
    contract = b.groupby("day")["contract"].agg(lambda s: s.value_counts().index[0]).reindex(close.index)
    roll = contract != contract.shift(1)
    return {"root": root, "raw": b, "close": close, "open": open_, "roll": roll}


def price_at(L: dict[str, Any], t: str) -> pd.Series:
    """D462's convention: the price AT t is the close of the bar starting one minute earlier; 09:30 is the open."""
    return L["open"]["09:30"] if t == "09:30" else L["close"][hm(t, -1)]


def rv_to(close: pd.DataFrame, open_: pd.Series, T: str, include_T_bar: bool = False) -> pd.Series:
    """D702's rv_today with 15:30 replaced by T: ln sqrt(sum of 5-minute r^2, bp^2) from 09:30 to T. The canary extends
    the grid by one step, reading the bar that starts at T."""
    end = pd.Timestamp("2000-01-01 " + T) + pd.Timedelta(minutes=5 if include_T_bar else 0)
    grid, t = [], pd.Timestamp("2000-01-01 09:35")
    while t <= end:
        grid.append((t - pd.Timedelta(minutes=1)).strftime("%H:%M"))
        t += pd.Timedelta(minutes=5)
    PG = np.column_stack([open_.to_numpy(float)] + [close[g].to_numpy(float) for g in grid])
    r5 = 1e4 * np.diff(np.log(PG), axis=1)
    with np.errstate(divide="ignore"):
        return pd.Series(np.log(np.sqrt(np.nansum(r5 * r5, axis=1))), index=close.index)


def rv_audit_to(close: pd.DataFrame, open_: pd.Series, got: pd.Series, T: str, days: list[str]) -> None:
    """Second implementation by minute arithmetic: bars whose START minute is before T only."""
    tm = int(T[:2]) * 60 + int(T[3:])
    for d in days:
        row = close.loc[d]
        pts = [float(open_.loc[d])]
        for mnt in range(9 * 60 + 34, tm, 5):
            pts.append(float(row[f"{mnt // 60:02d}:{mnt % 60:02d}"]))
        r = 1e4 * np.diff(np.log(np.array(pts)))
        want = math.log(math.sqrt(float(np.nansum(r * r))))
        if not math.isclose(want, float(got.loc[d]), rel_tol=0, abs_tol=1e-9):
            raise D711Error(f"lag: realised volatility to {T} at {d} reads a bar that starts at or after {T}")


def clock_frame(L: dict[str, Any], T: str) -> pd.DataFrame:
    """Every candidate of root L at decision clock T: gross (one micro), side, a, b, and the three prices."""
    cl = cost_line(L["root"])
    prev, entry, exit_ = price_at(L, hm(T, -60)), price_at(L, T), price_at(L, hm(T, 30))
    F = 1e4 * np.log(entry / prev)
    d = np.sign(F.to_numpy(float))
    pts = d * (exit_ - entry).to_numpy(float)
    ka = np.isfinite(pts) & ~L["roll"].to_numpy(bool)
    cand = ka & (d != 0)
    sig = E.sigma_f5(F)
    X = pd.DataFrame(index=F.index[cand])
    X["P_prev"], X["P_entry"], X["P_exit"] = prev[cand].to_numpy(float), entry[cand].to_numpy(float), exit_[cand].to_numpy(float)
    X["F"] = F[cand].to_numpy(float)
    X["gross"] = d[cand] * (X["P_exit"] - X["P_entry"]).to_numpy(float) * cl["usd_per_point"]
    X["side"] = d[cand]
    X["a"] = (F.abs() / sig).reindex(X.index)
    close, open_ = L["close"].reindex(X.index), L["open"]["09:30"].reindex(X.index)
    X["b"] = rv_to(close, open_, T)
    sample = list(X.index[:: max(1, len(X) // 20)])
    rv_audit_to(close, open_, X["b"], T, sample)
    E.sigma_audit(F, sig, sample)
    rq_audit(L, X, T, sample)
    X.attrs.update(root=L["root"], T=T, cost=cl["cost"])
    return X


def rq_audit(L: dict[str, Any], X: pd.DataFrame, T: str, days: list[str], shift: int = 0) -> None:
    """Right quantity, a second implementation from the raw rows: entry = close of the bar starting T-1, exit = close of
    the bar starting T+29, the prior price = close of the bar starting T-61 (the 09:30 open when T = 10:30). `shift`
    moves the implementation's minutes: the canary."""
    raw = L["raw"]
    for s in days:
        r = raw[raw["day"] == s].set_index("hhmm")
        entry = float(r.at[hm(T, -1 + shift), "close"])
        exit_ = float(r.at[hm(T, 29 + shift), "close"])
        prev = float(r.at["09:30", "open"]) if hm(T, -60) == "09:30" else float(r.at[hm(T, -61 + shift), "close"])
        if (entry, exit_, prev) != (float(X.at[s, "P_entry"]), float(X.at[s, "P_exit"]), float(X.at[s, "P_prev"])):
            raise D711Error(f"right quantity: {L['root']} {T} at {s} does not trade the bars the record names")


# ================================================================================ statistics
def clustered_t(x: np.ndarray, sess: np.ndarray, lags: int = 5) -> tuple[float, float]:
    """Mean's t with the residuals summed within each session and a Newey-West (Bartlett) variance over the session
    sums in session order. With one value a session it is D691's nw_t exactly (asserted in the selftest)."""
    x = np.asarray(x, float)
    n = len(x)
    e = x - x.mean()
    order = np.argsort(sess, kind="stable")
    s_sorted = sess[order]
    _, start = np.unique(s_sorted, return_index=True)
    S = np.add.reduceat(e[order], start)
    v = S @ S / n
    for L in range(1, lags + 1):
        v += 2 * (1 - L / (lags + 1)) * (S[L:] @ S[:-L]) / n
    se = math.sqrt(v / n)
    return float(x.mean() / se), float(se)


def year_share(net: np.ndarray, days: np.ndarray, year: str = "2022") -> float | None:
    tot = float(net.sum())
    if tot <= 0:
        return None
    return float(net[np.char.startswith(days.astype(str), year)].sum() / tot)


# ================================================================================ A2's rotation (D705's construction, one member)
_W: dict[str, Any] = {}


def rule_take(A: np.ndarray, q: float = Q) -> np.ndarray:
    ta, tb = C.tiers(A[:, 0]), C.tiers(A[:, 1])
    tc = C.tiers((ta + tb) / 2)
    with np.errstate(invalid="ignore"):
        return tc >= q


def efficiency(g: np.ndarray) -> float:
    """D711-A1's statistic: the direction efficiency sum(g) / sum(|g|) of a book. It does not grow with the size of the
    trades a filter picks, so a filter that picks big days with no direction information sits inside its rotation."""
    s = float(np.abs(g).sum())
    return float(g.sum()) / s if s > 0 else float("nan")


def rot_mean(A: np.ndarray, g: np.ndarray, W: np.ndarray, k: int) -> tuple[float, int, float]:
    """(mean gross, trades, direction efficiency) of the rule on inputs rotated by k."""
    fin = np.isfinite(A).all(axis=1)
    B = A.copy()
    B[fin] = np.roll(A[fin], k, axis=0)
    t = rule_take(B) & W
    if not t.any():
        return float("nan"), 0, float("nan")
    return float(g[t].mean()), int(t.sum()), efficiency(g[t])


def _init(A, g, W) -> None:
    _W.update(A=A, g=g, W=W)


def _job(ks: list[int]) -> list[tuple[int, tuple[float, int]]]:
    return [(k, rot_mean(_W["A"], _W["g"], _W["W"], k)) for k in ks]


def rotation(A, g, W, ks: list[int], workers: int) -> dict[int, tuple[float, int]]:
    chunks = [ks[i::workers] for i in range(workers)]
    with ProcessPoolExecutor(max_workers=workers, initializer=_init, initargs=(A, g, W)) as ex:
        return dict(kv for part in ex.map(_job, chunks) for kv in part)


# ================================================================================ the study
def f2_on(X: pd.DataFrame) -> dict[str, np.ndarray]:
    return V.f2(X)


def es_known_answer(X1530: pd.DataFrame) -> dict[str, Any]:
    """The generic path equals D707's (which is D618's load_es + D702's rv_today) and reproduces D707's frozen answer."""
    Y = V.frame(IN_END)
    for c in ("gross", "side", "a", "b"):
        if not (Y.index.equals(X1530.index) and np.array_equal(Y[c].to_numpy(float), X1530[c].to_numpy(float), equal_nan=True)):
            raise D711Error(f"the generic loader differs from D707's frame on ES 15:30 ({c})")
    Fx = f2_on(X1530)
    ka = V.in_sample_answer(X1530, Fx)
    fz = json.loads(FROZEN707.read_text(encoding="utf-8"))["known_answer_in_sample_own_window"]
    if ka["trades"] != fz["trades"] or ka["take_sessions_sha256"] != fz["take_sessions_sha256"] or abs(ka["mean_net"] - fz["mean_net"]) > 1e-9:
        raise D711Error(f"D707's frozen answer is not reproduced: {ka} against {fz}")
    return {"d618_known": Y.attrs["d618_known"], "d707_frozen_reproduced": ka}


def clock_line(X: pd.DataFrame, F: dict[str, np.ndarray], lo: str, arm: pd.Series | None) -> dict[str, Any]:
    sess = X.index.to_numpy(str)
    span = F["window"] & (sess >= lo)
    g = X["gross"].to_numpy(float)
    s_T = float(g[span].std(ddof=1))
    take = F["take"] & span
    z = g / s_T
    wd = sess[span]
    years = (pd.Timestamp(str(wd[-1])) - pd.Timestamp(str(wd[0]))).days / 365.25
    cost = X.attrs["cost"]
    with cost_as(cost):
        bk = E.book(g, take, sess, X["side"].to_numpy(float), years, arm)
        all_ = E.book(g, span, sess, X["side"].to_numpy(float), years, None)
    tg = D.nw_t(g[take])[0] if take.sum() > 10 else float("nan")
    return {"root": X.attrs["root"], "clock": X.attrs["T"], "cost_usd": cost, "span": [str(wd[0]), str(wd[-1])],
            "candidates": int(span.sum()), "s_T_usd": s_T,
            "filtered": {"trades": int(take.sum()), "mean_z": float(z[take].mean()), "mean_gross": float(g[take].mean()),
                         "t_gross_hac": tg, "mean_net": float((g[take] - cost).mean()),
                         "share_2022_of_net": year_share(g[take] - cost, sess[take])},
            "take_everything": {"mean_z": float(z[span].mean()), "mean_gross": float(g[span].mean()),
                                "t_gross_hac": D.nw_t(g[span])[0], "mean_net": float((g[span] - cost).mean())},
            "lift_z": float(z[take].mean() - z[span].mean()), "book": bk, "book_take_everything": all_}


def a1(frames: dict[str, pd.DataFrame], fams: dict[str, dict[str, np.ndarray]], arm: pd.Series) -> dict[str, Any]:
    lo = max(str(X.index.to_numpy(str)[fams[T]["window"]][0]) for T, X in frames.items())
    lines = {T: clock_line(frames[T], fams[T], lo, arm) for T in frames}
    zs, ss = [], []
    for T in PLACEBO:
        X, F = frames[T], fams[T]
        sess = X.index.to_numpy(str)
        take = F["take"] & F["window"] & (sess >= lo)
        zs.append(X["gross"].to_numpy(float)[take] / lines[T]["s_T_usd"])
        ss.append(sess[take])
    z, s = np.concatenate(zs), np.concatenate(ss)
    t_p, se_p = clustered_t(z, s)
    g_p = float(z.mean())
    g_f2 = lines[ANCHOR]["filtered"]["mean_z"]
    H = g_f2 / 2
    if g_p + 1.645 * se_p < H:
        reading = "CLOSE-SPECIFIC"
    elif g_p >= H and t_p >= 1.645:
        reading = "GENERIC"
    else:
        reading = "UNRESOLVED"
    return {"common_start": lo, "pooled_placebo": {"trades": int(len(z)), "sessions": int(len(np.unique(s))), "G_P": g_p,
                                                   "se_clustered": se_p, "t": t_p, "upper_95": g_p + 1.645 * se_p},
            "G_F2": g_f2, "H": H, "reading": reading, "clocks": lines}


def eff_null(X: pd.DataFrame, F: dict[str, np.ndarray], workers: int) -> dict[str, Any]:
    """The enumerated joint rotation of (a, b) against the fixed outcomes: the direction efficiency (gating, D711-A1)
    and the mean gross (reported, anti-conservative)."""
    W = F["window"]
    g = X["gross"].to_numpy(float)
    take = F["take"] & W
    A = np.column_stack([X["a"].to_numpy(float), X["b"].to_numpy(float)])
    obs = rot_mean(A, g, W, 0)
    if obs != (float(g[take].mean()), int(take.sum()), efficiency(g[take])):
        raise D711Error(f"{X.attrs['root']} {X.attrs['T']}: the rotation's offset 0 does not reproduce the book")
    fin = int(np.isfinite(A).all(axis=1).sum())
    ks = list(range(EDGE, fin - EDGE))
    t0 = time.time()
    rot = rotation(A, g, W, ks, workers)
    wall = time.time() - t0
    mu = np.array([rot[k][0] for k in ks])
    cnt = np.array([rot[k][1] for k in ks])
    ef = np.array([rot[k][2] for k in ks])
    mu, ef = mu[np.isfinite(mu)], ef[np.isfinite(ef)]
    return {"mean_gross": obs[0], "efficiency": obs[2],
            "rotation": {"offsets": int(len(ef)), "statistic": "direction efficiency sum(g)/sum(|g|) (D711-A1; gating)",
                         "p50": float(np.median(ef)), "p95": float(np.quantile(ef, 0.95)), "p95_se": 0.0,
                         "rank": float((ef < obs[2]).mean()),
                         "count_range": [int(cnt.min()), int(np.median(cnt)), int(cnt.max())], "wall_s": round(wall, 1)},
            "rotation_mean_gross_reported": {"statistic": "mean gross (the registered one; anti-conservative, D711-A1)",
                                             "p50": float(np.median(mu)), "p95": float(np.quantile(mu, 0.95)),
                                             "rank": float((mu < obs[0]).mean())}}


def a2(frames: dict[str, pd.DataFrame], fams: dict[str, dict[str, np.ndarray]], es_daily: pd.Series, arm: pd.Series,
       workers: int) -> dict[str, Any]:
    res, pv = {}, {}
    for r in A2_ROOTS:
        X, F = frames[r], fams[r]
        sess = X.index.to_numpy(str)
        W = F["window"]
        g = X["gross"].to_numpy(float)
        take = F["take"] & W
        nul = eff_null(X, F, workers)
        t_g = D.nw_t(g[take])[0]
        pv[r] = float(stats.norm.sf(t_g))
        line = clock_line(X, F, "2016-01-01", arm)
        daily = pd.Series(np.where(take, g - X.attrs["cost"], 0.0)[W], index=sess[W])
        common = daily.index.intersection(es_daily.index)
        res[r] = {"trades": int(take.sum()), "mean_gross": nul["mean_gross"], "t_gross_hac": t_g, **nul,
                  "rho_with_es_f2_daily_net": float(np.corrcoef(daily.loc[common], es_daily.loc[common])[0, 1]) if len(common) > 30 else None,
                  "rho_common_sessions": int(len(common)), "line": line}
    holm = P694.T.holm(pv)
    n_tr = 0
    for r in A2_ROOTS:
        x = res[r]
        x["holm_p"] = holm[r]
        x["gates"] = {"a_gross_holm": bool(x["mean_gross"] > 0 and holm[r] < 0.05),
                      "b_efficiency_above_rotation_p95": bool(x["efficiency"] > x["rotation"]["p95"])}
        if x["trades"] < 60:
            x["verdict"] = "UNRESOLVED"
        else:
            x["verdict"] = "TRANSFERS" if all(x["gates"].values()) else "DOES NOT TRANSFER"
        n_tr += x["verdict"] == "TRANSFERS"
    reading = "SUPPORTS" if n_tr >= 2 else ("MIXED" if n_tr == 1 else "ES-ONLY")
    return {"reading": reading, "transferring": n_tr, "roots": res}


def study(workers: int) -> dict[str, Any]:
    t0 = time.time()
    for r in ("ES",) + A2_ROOTS:
        mult = cost_line(r)["usd_per_point"]
        for f5, p0, p1 in ((+5.0, 100.0, 101.0), (-5.0, 100.0, 99.0)):
            if not np.sign(f5) * (p1 - p0) * mult > 0:
                raise D711Error(f"sign: a favourable continuation does not pay on {r}")
    Les = load_root("ES")
    es_frames = {T: clock_frame(Les, T) for T in PLACEBO + (SHOULDER, ANCHOR)}
    ka = es_known_answer(es_frames[ANCHOR])
    es_fams = {T: f2_on(X) for T, X in es_frames.items()}
    for T, X in es_frames.items():
        V.audit_tiers(X, es_fams[T])
    arm = P694.arm_daily()
    arm = arm[arm.index <= IN_END]
    res_a1 = a1(es_frames, es_fams, arm)
    Xa, Fa = es_frames[ANCHOR], es_fams[ANCHOR]
    sa = Xa.index.to_numpy(str)
    es_daily = pd.Series(np.where(Fa["take"] & Fa["window"], Xa["gross"].to_numpy(float) - ES_COST, 0.0)[Fa["window"]], index=sa[Fa["window"]])
    frames, fams = {}, {}
    for r in A2_ROOTS:
        frames[r] = clock_frame(load_root(r), ANCHOR)
        fams[r] = f2_on(frames[r])
        V.audit_tiers(frames[r], fams[r])
    res_a2 = a2(frames, fams, es_daily, arm, workers)
    pl = res_a1["clocks"]
    ok_te = all(abs(pl[T]["filtered"]["mean_z"] - pl[T]["take_everything"]["mean_z"]) <= res_a1["pooled_placebo"]["se_clustered"] * 2
                for T in PLACEBO)
    es_null = eff_null(Xa, Fa, workers)
    out = {"spec": "D711 (a39ec041) with D711-A1", "known_answers": ka, "A1": res_a1, "A2": res_a2,
           "es_f2_efficiency_rotation_reported": es_null,
           "costs": {r: cost_line(r) for r in ("ES",) + A2_ROOTS}, "runtime_min": round((time.time() - t0) / 60, 2)}
    rts = res_a2["roots"]
    out["predictions"] = {
        "1_es_known_answer_reproduces": True,
        "2_A1_close_specific": res_a1["reading"] == "CLOSE-SPECIFIC",
        "2b_each_placebo_near_its_take_everything_(2 pooled SE, a proxy for one clock SE)": bool(ok_te),
        "3_shoulder_between": bool(res_a1["pooled_placebo"]["G_P"] < pl[SHOULDER]["filtered"]["mean_z"] < res_a1["G_F2"]),
        "4_A2_supports_nq_ym_transfer_rty_weakest": bool(res_a2["reading"] == "SUPPORTS" and rts["NQ"]["verdict"] == "TRANSFERS"
                                                        and rts["YM"]["verdict"] == "TRANSFERS"
                                                        and rts["RTY"]["t_gross_hac"] <= min(rts["NQ"]["t_gross_hac"], rts["YM"]["t_gross_hac"])),
        "5_rho_nq_ym_above_0.6_rty_lower": bool((rts["NQ"]["rho_with_es_f2_daily_net"] or 0) > 0.6 and (rts["YM"]["rho_with_es_f2_daily_net"] or 0) > 0.6
                                                and (rts["RTY"]["rho_with_es_f2_daily_net"] or 0) < min(rts["NQ"]["rho_with_es_f2_daily_net"], rts["YM"]["rho_with_es_f2_daily_net"])),
        "6_transferring_roots_2022_share_above_0.4": bool(all((rts[r]["line"]["filtered"]["share_2022_of_net"] or 0) > 0.4
                                                              for r in A2_ROOTS if rts[r]["verdict"] == "TRANSFERS"))}
    return out


# ================================================================================ selftest
def selftest() -> int:
    fired: list[str] = []

    def must_raise(name: str, fn: Callable[[], Any], exc: tuple = (D711Error,)) -> None:
        try:
            fn()
        except exc:
            fired.append(name)
            return
        raise SystemExit(f"selftest: the {name} canary did not raise")
    rng = np.random.default_rng(711)
    # the clustered SE is nw_t when every session holds one value
    x = rng.normal(size=300)
    s1 = np.array([f"s{i:04d}" for i in range(300)])
    if not math.isclose(clustered_t(x, s1)[1], D.nw_t(x)[1], rel_tol=1e-12):
        raise SystemExit("selftest: clustered_t differs from nw_t on one value a session")
    # and it widens when a session's values move together
    s2 = np.repeat(np.array([f"s{i:04d}" for i in range(100)]), 3)
    xx = np.repeat(rng.normal(size=100), 3) + rng.normal(0, 0.1, 300)
    perm = rng.permutation(300)  # scattered in trade order, so only the session clustering can see the common shock
    xx, s2 = xx[perm], s2[perm]
    if not clustered_t(xx, s2)[1] > D.nw_t(xx)[1] * 1.3:
        raise SystemExit("selftest: clustered_t does not widen for a common session shock")
    # rv_to is D702's rv_today at 15:30, and its canary fires at a midday clock
    days = [f"2019-01-{i:02d}" for i in range(1, 11)]
    cols = [f"{h:02d}:{m:02d}" for h in range(9, 16) for m in range(60) if (h, m) >= (9, 30)]
    close = pd.DataFrame(100 + np.cumsum(rng.normal(0, 0.05, (10, len(cols))), axis=1), index=days, columns=cols)
    open_ = pd.Series(100.0, index=days)
    if not np.array_equal(rv_to(close, open_, "15:30").to_numpy(), M702.rv_today(close, open_).to_numpy()):
        raise SystemExit("selftest: rv_to at 15:30 differs from D702's rv_today")
    close.loc[:, "11:34"] = close["11:34"] + 5.0
    rv_audit_to(close, open_, rv_to(close, open_, "11:30"), "11:30", days)
    must_raise("a realised volatility that reads the bar starting at T",
               lambda: rv_audit_to(close, open_, rv_to(close, open_, "11:30", include_T_bar=True), "11:30", days))
    # right quantity on a synthetic root
    raw = pd.DataFrame([(d, c, float(close.at[d, c]) - 0.01, float(close.at[d, c])) for d in days for c in cols],
                       columns=["day", "hhmm", "open", "close"])
    Ls = {"root": "ES", "raw": raw, "close": close, "open": pd.DataFrame({"09:30": raw[raw["hhmm"] == "09:30"].set_index("day")["open"]})}
    Xs = pd.DataFrame(index=days)
    Xs["P_entry"], Xs["P_exit"], Xs["P_prev"] = price_at(Ls, "10:30"), price_at(Ls, "11:00"), price_at(Ls, "09:30")
    rq_audit(Ls, Xs, "10:30", days[:4])
    must_raise("an entry one minute late", lambda: rq_audit(Ls, Xs, "10:30", days[:4], shift=1))
    # the seal, the tier and sigma canaries
    must_raise("a build past 2023-12-29", lambda: load_root("NQ", "2024-03-01"))
    v = rng.normal(size=600)
    must_raise("a tier that ranks its own value", lambda: C.tier_audit(C.tiers(v, leak=True), v, [300, 450, 599]), (C.D671Error,))
    f5 = pd.Series(rng.normal(size=400), index=[f"d{i:04d}" for i in range(400)])
    must_raise("a sigma that includes today", lambda: E.sigma_audit(f5, E.sigma_f5(f5, leak=True), list(f5.index[100::50])), (E.D703Error,))
    # A2's rotation: offset 0, processes == serial, an injected effect, and the null's size

    def world(effect: bool, n: int = 900) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        a_ = np.abs(rng.normal(size=n)) + 0.1
        A = np.column_stack([a_, a_ + rng.normal(0, 0.3, n)])  # b moves with a, as today's vol does with the hour's size
        size = 10 + 25 * A[:, 0]
        p = 0.5 + (0.3 * np.tanh(A[:, 0] - 1.0) if effect else 0.0)
        g = np.where(rng.random(n) < p, 1.0, -1.0) * size
        ta, tb = C.tiers(A[:, 0]), C.tiers(A[:, 1])
        W = np.isfinite(ta) & np.isfinite(C.tiers((ta + tb) / 2))
        return A, g, W
    A, g, W = world(True)
    t = rule_take(A) & W
    if rot_mean(A, g, W, 0) != (float(g[t].mean()), int(t.sum()), efficiency(g[t])):
        raise SystemExit("selftest: offset 0 does not reproduce")
    ks = [21, 22, 57]
    if rotation(A, g, W, ks, 2) != {k: rot_mean(A, g, W, k) for k in ks}:
        raise SystemExit("selftest: the rotation's processes differ from the serial run")
    ef = np.array([rot_mean(A, g, W, k)[2] for k in range(EDGE, 900 - EDGE, 5)])
    if not rot_mean(A, g, W, 0)[2] > np.quantile(ef[np.isfinite(ef)], 0.95):
        raise SystemExit("selftest: an injected relative-size effect does not clear the efficiency rotation's p95")
    # the null's size on worlds where the filter picks big days and direction is a coin (D711-A1): the efficiency must
    # hold about 5 %; the registered mean-gross statistic is reported beside to show why it was replaced
    hits_ef = hits_mu = 0
    worlds = 60
    for _ in range(worlds):
        A0, g0, W0 = world(False)
        rr = [rot_mean(A0, g0, W0, k) for k in range(EDGE, 900 - EDGE, 6)]
        o = rot_mean(A0, g0, W0, 0)
        mu0 = np.array([x[0] for x in rr])
        ef0 = np.array([x[2] for x in rr])
        hits_mu += int(o[0] > np.quantile(mu0[np.isfinite(mu0)], 0.95))
        hits_ef += int(o[2] > np.quantile(ef0[np.isfinite(ef0)], 0.95))
    if hits_ef / worlds > 0.12:
        raise SystemExit(f"selftest: with no direction effect the efficiency rotation's p95 was cleared in {hits_ef / worlds:.2f} of worlds")
    print(f"selftest OK: {len(fired)} canaries fired: {fired}; clustered_t == nw_t on one value a session and widens on a "
          f"session shock; rv_to(15:30) == D702's rv_today; offset 0 reproduces; processes == serial; an injected effect "
          f"clears the efficiency rotation's p95; with no direction effect it was cleared in {hits_ef / worlds:.2f} of {worlds} "
          f"worlds (<= 0.12), against {hits_mu / worlds:.2f} for the registered mean-gross statistic (D711-A1). The ES known "
          "answers (D618, D707's frozen F2) need the fixtures and run first in --run.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--time", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 4))
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.time:
        X = clock_frame(load_root("NQ"), ANCHOR)
        A = np.column_stack([X["a"].to_numpy(float), X["b"].to_numpy(float)])
        g = X["gross"].to_numpy(float)
        W = f2_on(X)["window"]
        t0 = time.time()
        for k in (21, 22, 23):
            rot_mean(A, g, W, k)
        per = (time.time() - t0) / 3
        nk = int(np.isfinite(A).all(axis=1).sum()) - 2 * EDGE
        print(f"{per:.3f} s an offset x {nk} offsets x 3 roots / {a.workers} workers = about {3 * per * nk / a.workers / 60:.1f} min")
        return 0
    if not a.run:
        ap.print_help()
        return 1
    if OUT.exists():
        raise D711Error(f"{OUT.name} exists: D711's run is once")
    out = study(a.workers)
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    a1r, a2r = out["A1"], out["A2"]
    brief = {"A1": {"reading": a1r["reading"], "pooled_placebo": a1r["pooled_placebo"], "G_F2": a1r["G_F2"], "H": a1r["H"],
                    "clocks": {T: {"trades": c["filtered"]["trades"], "mean_z": c["filtered"]["mean_z"], "mean_gross": c["filtered"]["mean_gross"],
                                   "mean_net": c["filtered"]["mean_net"], "t": c["filtered"]["t_gross_hac"],
                                   "take_everything_z": c["take_everything"]["mean_z"]} for T, c in a1r["clocks"].items()}},
             "A2": {"reading": a2r["reading"], "roots": {r: {k: x[k] for k in ("verdict", "trades", "mean_gross", "t_gross_hac", "holm_p", "gates", "rho_with_es_f2_daily_net")}
                                                           | {"rotation": x["rotation"], "mean_net": x["line"]["filtered"]["mean_net"],
                                                              "share_2022": x["line"]["filtered"]["share_2022_of_net"]}
                                                           for r, x in a2r["roots"].items()}},
             "predictions": out["predictions"], "runtime_min": out["runtime_min"]}
    print(json.dumps(brief, indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
