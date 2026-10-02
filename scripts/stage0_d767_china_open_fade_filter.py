"""D767 Stage 0: fade the unconfirmed China open. Spec: docs/decisions/D767-STAGE-0-PRE-REG-fade-the-unconfirmed-china-open.md.

    python scripts/stage0_d767_china_open_fade_filter.py --selftest     # SYSTEM interpreter (pyarrow)
    python scripts/stage0_d767_china_open_fade_filter.py --run --lines temp/d755_other_lines.csv

The base construction is D765's, through D765's own functions (sessions, prices, clocks, exclusions), read from
D765's extraction cache: side = -sign(x), x = P09:30 - P09:00 Beijing, entry at the 09:31 open, exit at P15:00
Beijing. The filter U is the mean of F3 (the AUD not confirming the metal's opening move) and F4 (the other two metals
not confirming), each in its own recent scale; the traded set is U's walk-forward top third.
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
import stage0_d765_china_open as C  # noqa: E402

SPEC = REPO / "docs" / "decisions" / "D767-STAGE-0-PRE-REG-fade-the-unconfirmed-china-open.md"
OUT = REPO / "data" / "stage0_d767_china_open_fade_filter.json"
CELLS = ("mgc", "sil", "mhg")
PARTNERS = {"mgc": ("sil", "mhg"), "sil": ("mgc", "mhg"), "mhg": ("mgc", "sil")}
LOOK, LOOK_MIN = 60, 40
WF, WF_MIN = 250, 100
BALANCE_PP = 5.0
WORKERS = 8


class D767Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D767Error(msg)


# ================================================================================ scores
def valid_x(s: pd.DataFrame) -> pd.Series:
    """A partner's opening move on any of its sessions: finite, one contract, no isolated print."""
    ok = np.isfinite(s["x"]) & ~s["void"].astype(bool) & (s["nk"] == 1)
    return s.loc[ok, "x"]


def prior_median_abs(v: np.ndarray) -> np.ndarray:
    return pd.Series(np.abs(v)).shift(1).rolling(LOOK, min_periods=LOOK_MIN).median().to_numpy()


def scores(e: pd.DataFrame, partner_x: dict[str, pd.Series]) -> pd.DataFrame:
    """F3, F4 and U for the cell's candidate sessions `e` (indexed by day, in order). Higher = less confirmed."""
    days = e.index
    sx = np.sign(e["x"].to_numpy(float))
    xa = partner_x["aud"].reindex(days).to_numpy(float)
    f3 = -sx * xa / prior_median_abs(xa)
    zs = []
    for k in ("p1", "p2"):
        xo = partner_x[k].reindex(days).to_numpy(float)
        zs.append(xo / prior_median_abs(xo))
    Z = np.vstack(zs)
    cnt = np.isfinite(Z).sum(axis=0)
    zm = np.where(cnt > 0, np.nansum(Z, axis=0) / np.maximum(cnt, 1), np.nan)
    f4 = -sx * zm
    u = (f3 + f4) / 2
    return pd.DataFrame({"F3": f3, "F4": f4, "U": u}, index=days)


def wf_select(score: np.ndarray, wf: int = WF, wf_min: int = WF_MIN) -> np.ndarray:
    """The walk-forward top third: score_i > the 2/3 quantile of the prior wf scores' finite values (>= wf_min)."""
    n = len(score)
    out = np.zeros(n, bool)
    for i in range(wf, n):
        if not np.isfinite(score[i]):
            continue
        w = score[i - wf:i]
        w = w[np.isfinite(w)]
        if len(w) >= wf_min:
            out[i] = bool(score[i] > np.quantile(w, 2 / 3))
    return out


def pool_mask(score: np.ndarray) -> np.ndarray:
    """The sessions a walk-forward selection could take: past the burn-in, finite score, enough finite history."""
    n = len(score)
    out = np.zeros(n, bool)
    for i in range(WF, n):
        out[i] = bool(np.isfinite(score[i]) and np.isfinite(score[i - WF:i]).sum() >= WF_MIN)
    return out


# ================================================================================ the null
def _rot_chunk(args: tuple[np.ndarray, np.ndarray, np.ndarray, int, int, int, int]) -> np.ndarray:
    u, net, second, k0, k1, wf, wf_min = args                         # the window travels with the job (spawned workers)
    out = np.full((k1 - k0, 4), np.nan)
    for j, k in enumerate(range(k0, k1)):
        sel = wf_select(np.roll(u, k), wf, wf_min)
        s2 = sel & second
        out[j] = [net[sel].mean() if sel.any() else np.nan, sel.sum(),
                  net[s2].mean() if s2.any() else np.nan, s2.sum()]
    return out


def rotation(u: np.ndarray, net: np.ndarray, second: np.ndarray, workers: int = WORKERS, wf: int = WF,
             wf_min: int = WF_MIN) -> np.ndarray:
    """Rows k = 0 .. n-1: [mean net of U's selection, its count, mean net of the secondary, its count] with U rotated
    circularly by k against the candidate sessions; row 0 is the observed selection."""
    n = len(u)
    if workers == 1:
        return _rot_chunk((u, net, second, 0, n, wf, wf_min))
    cuts = np.linspace(0, n, workers * 4 + 1).astype(int)
    with ProcessPoolExecutor(workers) as ex:
        parts = list(ex.map(_rot_chunk, [(u, net, second, int(a), int(b), wf, wf_min)
                                         for a, b in zip(cuts[:-1], cuts[1:]) if b > a]))
    return np.vstack(parts)


# ================================================================================ audits
def audit_scores(e: pd.DataFrame, partner_x: dict[str, pd.Series], sc: pd.DataFrame, sample: list[int]) -> None:
    """Second implementation: explicit loops over positions, sorted-list medians, no pandas rolling."""
    days = list(e.index)
    px = {k: partner_x[k].to_dict() for k in partner_x}

    def med_prior(name: str, i: int) -> float:
        vals = [abs(px[name][d]) for d in days[max(0, i - LOOK):i] if d in px[name] and math.isfinite(px[name][d])]
        if len(vals) < LOOK_MIN:
            return float("nan")
        v = sorted(vals)
        h = len(v) // 2
        return v[h] if len(v) % 2 else (v[h - 1] + v[h]) / 2

    for i in sample:
        d = days[i]
        s = 1.0 if e["x"].iloc[i] > 0 else -1.0
        a = px["aud"].get(d, float("nan"))
        f3 = -s * a / med_prior("aud", i) if math.isfinite(a) else float("nan")
        zz = []
        for k in ("p1", "p2"):
            v = px[k].get(d, float("nan"))
            if math.isfinite(v):
                m = med_prior(k, i)
                if math.isfinite(m):
                    zz.append(v / m)
        f4 = -s * (sum(zz) / len(zz)) if zz else float("nan")
        u = (f3 + f4) / 2
        for nm, mine, theirs in (("F3", f3, sc["F3"].iloc[i]), ("F4", f4, sc["F4"].iloc[i]), ("U", u, sc["U"].iloc[i])):
            need((math.isnan(mine) and math.isnan(theirs)) or abs(mine - theirs) <= 1e-12 * max(1.0, abs(mine)),
                 f"lag audit: {nm} differs at {d} ({mine} vs {theirs})")


def audit_flags(score: np.ndarray, sel: np.ndarray) -> None:
    """Second implementation of the walk-forward third: sorted lists and a hand-written linear quantile."""
    for i in range(len(score)):
        if i < WF or not math.isfinite(score[i]):
            need(not sel[i], f"lag audit: session {i} selected without a full window or a score")
            continue
        w = sorted(float(v) for v in score[i - WF:i] if math.isfinite(v))
        if len(w) < WF_MIN:
            need(not sel[i], f"lag audit: session {i} selected on too short a history")
            continue
        pos = (len(w) - 1) * 2 / 3
        lo = int(math.floor(pos))
        thr = w[lo] + (w[min(lo + 1, len(w) - 1)] - w[lo]) * (pos - lo)
        need(bool(sel[i]) == bool(score[i] > thr), f"lag audit: the selection flag differs at session {i}")


def sign_audit(side: float = 1.0) -> None:
    """In money: an opening rise (x > 0) followed by a fall (y < 0) pays the fade, which is short."""
    x, y = np.array([0.5, -0.5]), np.array([-1.0, 1.0])
    pnl = side * -np.sign(x) * y * 10.0
    need(bool((pnl > 0).all()), "sign audit: a reversal did not pay the fade")


# ================================================================================ books and gates
def tstat(v: np.ndarray) -> float:
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    return float(v.mean() / (v.std(ddof=1) / math.sqrt(len(v)))) if len(v) > 2 and v.std(ddof=1) > 0 else float("nan")


def one_sided_p(t: float) -> float:
    return float(0.5 * math.erfc(t / math.sqrt(2))) if np.isfinite(t) else 1.0


def holm(ps: dict[str, float]) -> dict[str, float]:
    items = sorted(ps.items(), key=lambda kv: kv[1])
    m, out, run = len(items), {}, 0.0
    for i, (k, p) in enumerate(items):
        run = max(run, min(1.0, (m - i) * p))
        out[k] = run
    return out


def ex_best_two(net: np.ndarray, days: list[str]) -> float:
    yrs = pd.Series(net, index=[d[:4] for d in days]).groupby(level=0).sum()
    return float(net.sum() - yrs.sort_values(ascending=False).iloc[:2].sum())


def balance(sel_days: list[str], pool_days: list[str]) -> dict[str, Any]:
    mo = lambda ds: pd.Series(pd.to_datetime(pd.Series(ds)).dt.month.to_numpy()).value_counts(normalize=True)  # noqa: E731
    yr = lambda ds: pd.Series([d[:4] for d in ds]).value_counts(normalize=True)  # noqa: E731
    sm, pm = mo(sel_days).reindex(range(1, 13), fill_value=0), mo(pool_days).reindex(range(1, 13), fill_value=0)
    sy, py = yr(sel_days), yr(pool_days)
    sy = sy.reindex(py.index, fill_value=0)
    return {"month_share_selected": {int(k): round(float(v), 4) for k, v in sm.items()},
            "month_share_pool": {int(k): round(float(v), 4) for k, v in pm.items()},
            "max_month_dev_pp": float(100 * (sm - pm).abs().max()),
            "max_year_dev_pp": float(100 * (sy - py).abs().max()),
            "year_share_selected": {k: round(float(v), 4) for k, v in sy.sort_index().items()}}


def book_of(e: pd.DataFrame, sel: np.ndarray, cost: float, mtick_usd: float, lines: Path | None) -> dict[str, Any]:
    from stage0_d755_ecb_press_conference import book
    t = e[sel]
    g = t["gross"].to_numpy(float)
    days = list(t.index)
    span = max((pd.Timestamp(days[-1]) - pd.Timestamp(days[0])).days / 365.25, 1e-9)
    b = book(g, days, cost, len(g) / span)
    net = g - cost
    tn = tstat(net)
    mon = pd.to_datetime(pd.Series(days)).dt.month.to_numpy()
    outside = ~np.isin(mon, [12, 1, 2, 3])
    sub = (t.index >= C.NIGHT_SUSPENDED[0]) & (t.index <= C.NIGHT_SUSPENDED[1])
    grp = lambda m_: {"n": int(m_.sum()), "mean_net": float(net[m_].mean()) if m_.any() else None,  # noqa: E731
                      "total_net": float(net[m_].sum())}
    side = -np.sign(t["x"].to_numpy(float))
    srt = np.argsort(net)
    out = {"book": b, "t_net": tn, "one_sided_p": one_sided_p(tn), "net_ex_best_two_years": ex_best_two(net, days),
           "thin_book_mean_net": float(net.mean() - 2 * mtick_usd),
           "outside_dec_mar": grp(outside), "dec_mar": grp(~outside),
           "by_month": {int(m): grp(mon == m) for m in range(1, 13)},
           "by_year": {y: grp(np.array([d[:4] == y for d in days])) for y in sorted({d[:4] for d in days})},
           "EDT": grp(t["edt"].to_numpy(bool)), "EST": grp(~t["edt"].to_numpy(bool)),
           "long": grp(side > 0), "short": grp(side < 0), "night_suspension_2020": grp(np.asarray(sub)),
           "largest": {"losers": [(days[i], round(float(net[i]), 2)) for i in srt[:5]],
                       "winners": [(days[i], round(float(net[i]), 2)) for i in srt[-5:]]}}
    if lines is not None and lines.exists():
        ol = pd.read_csv(lines, index_col=0, encoding="utf-8")
        ol.index = ol.index.astype(str)
        dnet = pd.Series(net, index=days).groupby(level=0).sum()
        alld = sorted(set(ol.index) | {d for d in dnet.index if ol.index.min() <= d <= ol.index.max()})
        out["component_corr"] = {k: float(np.corrcoef(dnet.reindex(alld, fill_value=0.0), ol[k].reindex(alld).fillna(0.0))[0, 1])
                                 for k in ol.columns}
    return out


def cell_tables(fm: dict, hol: set[str]) -> dict[str, Any]:
    roots = {r: C.load_root(r) for r in C.ROOTS}
    sess = {cell: C.build_sessions(roots[C.CELLS[cell]["root"]], cell, fm, hol)[0].set_index("day") for cell in CELLS}
    sess["aud"] = C.build_sessions(roots["6A"], None, fm, hol)[0].set_index("day")
    return {"sess": sess, "roots": roots}


def run(lines: Path | None) -> int:
    from backtest_framework.validation import filter_oracle as FO
    need(not OUT.exists(), f"{OUT.name} exists: D767 is run-once")
    t0 = time.time()
    sign_audit()
    fm, hol = C._front_map(), C.load_holidays()
    T = cell_tables(fm, hol)
    sess = T["sess"]
    res: dict[str, Any] = {"spec": SPEC.name, "seal": f"nothing on or after {C.SEAL}", "window": [C.LO, C.HI], "cells": {}}
    first: dict[str, dict[str, Any]] = {}
    for cell in CELLS:
        c = C.CELLS[cell]
        s = sess[cell]
        e = s[(s["why"] == "eligible") & (s["x"] != 0)].copy()
        e["gross"] = -np.sign(e["x"].to_numpy(float)) * e["y"].to_numpy(float) * c["mult"]
        e["net"] = e["gross"] - c["cost"]
        p1, p2 = PARTNERS[cell]
        partner_x = {"aud": valid_x(sess["aud"]), "p1": valid_x(sess[p1]), "p2": valid_x(sess[p2])}
        sc = scores(e, partner_x)
        rng = np.random.default_rng(767)
        audit_scores(e, partner_x, sc, sorted(rng.choice(np.arange(LOOK, len(e)), size=40, replace=False).tolist()))
        u, f3, f4 = (sc[k].to_numpy(float) for k in ("U", "F3", "F4"))
        need(not np.allclose(u, f3, equal_nan=True) and not np.allclose(u, f4, equal_nan=True), "right quantity: U equals a part")
        sel = wf_select(u)
        audit_flags(u, sel)
        third = C.wf_flags(np.abs(e["x"].to_numpy(float)))[0]
        s2 = sel & third
        net, gross = e["net"].to_numpy(float), e["gross"].to_numpy(float)
        need(sel.sum() > 0 and sel.sum() < len(e), "right quantity: the filtered book equals the unfiltered one")
        pool = pool_mask(u)
        # G1: the unfiltered mechanism (gross)
        g1 = {"n": int(len(e)), "mean_gross": float(gross.mean()), "t_gross": tstat(gross), "mean_net": float(net.mean())}
        g1["pass"] = bool(g1["mean_gross"] > 0 and g1["t_gross"] >= 2)
        # N: the exact rotation null of U (row 0 = observed)
        rot = rotation(u, net, third)
        need(abs(rot[0, 0] - net[sel].mean()) < 1e-9 and rot[0, 1] == sel.sum(), "right quantity: rotation offset 0 != observed")
        d1, d2 = rot[1:, 0], rot[1:, 2]
        nul = {"observed": float(rot[0, 0]), "offsets": int(len(d1)), "p50": float(np.nanquantile(d1, 0.5)),
               "p95": float(np.nanquantile(d1, 0.95)), "rank": float(np.nanmean(d1 < rot[0, 0])),
               "count_observed": int(rot[0, 1]), "count_p5_p95": [float(np.quantile(rot[1:, 1], 0.05)), float(np.quantile(rot[1:, 1], 0.95))]}
        nul["pass"] = bool(nul["observed"] > nul["p95"])
        nul2 = {"observed": float(rot[0, 2]), "p50": float(np.nanquantile(d2, 0.5)), "p95": float(np.nanquantile(d2, 0.95)),
                "rank": float(np.nanmean(d2 < rot[0, 2])), "empty_offsets": int(np.isnan(d2).sum()), "count_observed": int(rot[0, 3])}
        nul2["pass"] = bool(nul2["observed"] > nul2["p95"])
        # accuracy against the oracle, on the selectable pool
        acc = {"spearman_U_gross": C.spearman(u[pool], gross[pool]),
               "spearman_F3_gross": C.spearman(f3[pool], gross[pool]), "spearman_F4_gross": C.spearman(f4[pool], gross[pool]),
               "auc_U_oracle": FO.auc(u[pool], net[pool] > 0),
               "capture": FO.capture(net[pool], sel[pool]), "pool": int(pool.sum())}
        days = list(e.index)
        pool_days = [d for d, p in zip(days, pool) if p]
        bal = balance([d for d, s_ in zip(days, sel) if s_], pool_days)
        bal2 = balance([d for d, s_ in zip(days, s2) if s_], pool_days)
        bk = book_of(e, sel, c["cost"], c["mtick_usd"], lines)
        bk2 = book_of(e, s2, c["cost"], c["mtick_usd"], lines)
        side_books = {}
        for nm, arr in (("F3_alone", f3), ("F4_alone", f4)):
            s_ = wf_select(arr)
            side_books[nm] = {"n": int(s_.sum()), "mean_net": float(net[s_].mean()), "t_net": tstat(net[s_]),
                              "mean_gross": float(gross[s_].mean())}
        side_books["unfiltered"] = {"n": int(len(e)), "mean_net": float(net.mean()), "t_net": tstat(net)}
        first[cell] = {"G1": g1, "N": nul, "N_secondary": nul2, "accuracy": acc, "balance": bal, "balance_secondary": bal2,
                       "U_book": bk, "S2_book": bk2, "reported": side_books, "selected": int(sel.sum()), "selected_S2": int(s2.sum())}
        print(f"[{cell}] candidates {len(e)}, pool {pool.sum()}, U selected {sel.sum()}, S2 {s2.sum()}", flush=True)
    for tag, bkey, nkey, bal_key in (("U", "U_book", "N", "balance"), ("S2", "S2_book", "N_secondary", "balance_secondary")):
        hp = holm({k: first[k][bkey]["one_sided_p"] for k in CELLS})
        for cell in CELLS:
            o = first[cell]
            b = o[bkey]
            b["holm_p"] = hp[cell]
            g2 = bool(b["book"]["mean_net"] > 0 and np.isfinite(b["t_net"]) and b["t_net"] >= 2 and hp[cell] < 0.05
                      and b["net_ex_best_two_years"] > 0)
            b1 = bool(o[bal_key]["max_month_dev_pp"] <= BALANCE_PP)
            b2 = bool(b["outside_dec_mar"]["total_net"] > 0)
            o[f"gates_{tag}"] = {"G1": o["G1"]["pass"], "N": o[nkey]["pass"], "B1": b1, "B2": b2, "G2": g2}
            rd = ("NO MECHANISM" if not o["G1"]["pass"] else "NOT ABOVE NULL" if not o[nkey]["pass"]
                  else "UNBALANCED" if not (b1 and b2) else "MECHANISM ONLY" if not g2 else "SUPPORTED")
            o[f"reading_{tag}"] = rd if tag == "U" else f"SECONDARY: {rd}"
    for cell in CELLS:
        first[cell]["GO"] = bool(first[cell]["reading_U"] == "SUPPORTED")
        res["cells"][cell] = first[cell]
    res["runtime_min"] = round((time.time() - t0) / 60, 2)
    OUT.write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    for cell in CELLS:
        o = res["cells"][cell]
        print(cell, o["reading_U"], "|", o["reading_S2"], json.dumps({
            "G1": {k: o["G1"][k] for k in ("mean_gross", "t_gross")}, "N": {k: o["N"][k] for k in ("observed", "p50", "p95", "rank")},
            "acc": o["accuracy"]["spearman_U_gross"], "B": {"month_dev": o["balance"]["max_month_dev_pp"],
                                                             "outside_dec_mar": o["U_book"]["outside_dec_mar"]},
            "U": {"n": o["U_book"]["book"]["trades"], "net": o["U_book"]["book"]["mean_net"], "t": o["U_book"]["t_net"],
                  "holm": o["U_book"]["holm_p"]},
            "S2": {"n": o["S2_book"]["book"]["trades"], "net": o["S2_book"]["book"]["mean_net"], "t": o["S2_book"]["t_net"]}},
            default=float), flush=True)
    print(f"runtime {res['runtime_min']} min", flush=True)
    return 0


# ================================================================================ self-test
def _synthetic(n: int, plant: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    u = rng.normal(size=n)
    net = plant * u + rng.normal(size=n)
    return u, net


def selftest() -> int:
    sign_audit()
    try:
        sign_audit(-1.0)
        raise SystemExit("FAIL: the sign audit did not raise on a mirrored book")
    except D767Error:
        pass
    # the flag audit passes on the real selection and raises on a threshold that includes the current session
    rng = np.random.default_rng(1)
    sc = rng.normal(size=600)
    sc[rng.choice(600, 40, replace=False)] = np.nan
    sel = wf_select(sc)
    audit_flags(sc, sel)
    # a session just above its honest threshold: a threshold that includes it (and drops the oldest) moves above it
    sc2 = np.r_[np.arange(1.0, WF + 1.0), 0.0]
    sc2[WF] = np.quantile(sc2[:WF], 2 / 3) + 1e-6
    good = wf_select(sc2)
    audit_flags(sc2, good)
    leaky = good.copy()
    leaky[WF] = bool(sc2[WF] > np.quantile(sc2[1:WF + 1], 2 / 3))
    flipped = int(leaky[WF] != good[WF])
    need(flipped > 0, "self-test design: the leaky threshold changed no flag")
    try:
        audit_flags(sc2, leaky)
        raise SystemExit("FAIL: the flag audit did not raise on a threshold that includes the current session")
    except D767Error:
        pass
    # the score audit agrees with scores() on a synthetic table, and raises on a broken score
    days = [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2018-01-02", periods=300)]
    e = pd.DataFrame({"x": rng.normal(size=300)}, index=days)
    px = {k: pd.Series(rng.normal(size=300), index=days) for k in ("aud", "p1", "p2")}
    px["p2"] = px["p2"].drop(days[::7])
    sc_ = scores(e, px)
    audit_scores(e, px, sc_, list(range(LOOK, 300, 13)))
    bad = sc_.copy()
    bad.iloc[100, bad.columns.get_loc("U")] += 1e-6
    try:
        audit_scores(e, px, bad, [100])
        raise SystemExit("FAIL: the score audit did not raise on a broken U")
    except D767Error:
        pass
    # the null on a small window: a planted filter clears p95; noise clears it about 5% of the time; chunk == whole
    small = {"wf": 60, "wf_min": 40}
    u, net = _synthetic(400, 0.35, 3)
    third = np.zeros(400, bool)
    rot = rotation(u, net, third, workers=1, **small)
    need(rot[0, 0] > np.nanquantile(rot[1:, 0], 0.95), "self-test: a planted filter did not clear the rotation null")
    rot4 = rotation(u, net, third, workers=4, **small)
    need(np.array_equal(rot, rot4, equal_nan=True), "chunk != whole: the rotation on processes differs")
    hits = 0
    trials = 60
    for t in range(trials):
        u, net = _synthetic(400, 0.0, 100 + t)
        r = rotation(u, net, third, workers=1, **small)
        hits += r[0, 0] > np.nanquantile(r[1:, 0], 0.95)
    need(hits / trials <= 0.15, f"self-test: noise cleared the null {hits}/{trials}")
    print(f"SELFTEST OK: sign in money (raises on a mirrored book); the flag audit passes and raises on a threshold "
          f"that includes the current session ({flipped} flags flip); the score audit agrees and raises on a broken U; "
          f"a planted filter clears the rotation null; noise cleared it {hits}/{trials}; chunk == whole on 4 processes")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--lines", type=Path, default=None)
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.run:
        return run(a.lines)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
