"""D747 Stage 0: the night-break fade. Spec: docs/decisions/D747-STAGE-0-PRE-REG-the-night-break-fade.md.

    uv run --no-sync python scripts/stage0_d747_night_break_fade.py --selftest
    uv run --no-sync python scripts/stage0_d747_night_break_fade.py --run

Resting limits at yesterday's RTH high + 0.25 ATR20 (sell) and low - 0.25 ATR20 (buy), live 03:00-08:29 ET, filled
only when a bar trades through by a tick; a 1:1 bracket of b x ATR20 anchored at the level (b 0.10 / 0.25 / 0.50;
primary 0.25, whose target is yesterday's extreme); flat at the 09:29 close. One MNQ or MES at D744's night cost.
Decided on ES 2016-2023 and NQ 2016-01-04 -> 2018-01-08 (never scored by D744); NQ 2018-01-09 -> 2023 is post hoc.
The chain is D744's loader (D720's lowered_cut at 2024-01-01).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

import stage0_d744_european_open_break as E  # noqa: E402  (D744's functions, read-only)
from backtest_framework.validation import filter_oracle as FO  # noqa: E402

Z = E.Z
SPEC = REPO / "docs" / "decisions" / "D747-STAGE-0-PRE-REG-the-night-break-fade.md"
OUT = REPO / "data" / "stage0_d747_night_break_fade.json"
K = 0.25
BS = (0.10, 0.25, 0.50)
PRIMARY_B = 0.25
SLICES = {"ES_full": ("ES", "2016-01-04", "2023-12-29"), "NQ_early": ("NQ", "2016-01-04", "2018-01-08"),
          "NQ_late_posthoc": ("NQ", "2018-01-09", "2023-12-29")}
COL0, NCOL, LAST_ENTRY_COL = 180, 390, 329          # 03:00 = minute 180; columns 03:00 .. 09:29; 08:29 = col 329
TICK = {"ES": 0.25, "NQ": 0.25}
USD_PT = {"ES": 5.0, "NQ": 2.0}
KNOWN_U = {"trades": 298, "gross_bp": -4.475559322876281}
RHOS = (0.0, 0.025, 0.05, 0.075, 0.10, 0.15, 0.20, 0.30)
N_DRAW, SEED, EDGE, WORKERS = 500, 747, 20, 12


class D747Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D747Error(msg)


def col_hhmm(c: int) -> str:
    m = COL0 + c
    return f"{m // 60:02d}:{m % 60:02d}"


# ================================================================================ inputs (D744's chain)
def load() -> dict[str, Any]:
    import stage0_d662_gamma_product as S662
    import stage0_d691_iv_size as I
    import vault_d680_nq_compression as V
    C, M, Tv = V.C, V.M, V.T
    old = V.CUT
    V.CUT = Z.CUT24
    try:
        with Z.lowered_cut(I, S662, I.T, I.M):
            b, use, _gd, R = M.load_bars(V.DATA, False, ("ES", "NQ"))
            Tv.MULT.update(M.MULT)
            C._R = R
            frames, tabs_all = {}, {}
            for r in ("ES", "NQ"):
                tabs = R.session_table(b, use, roots=(r,))
                tabs_all[r] = tabs[r]
                d = Tv.root_frame(b, tabs[r], r)
                frames[r] = d[np.isfinite(d[["prior_high", "prior_low", "atr20"]]).all(axis=1)].copy()
            dN = frames["NQ"].copy()
            dN["gd_spx"] = np.nan
            cal = pd.read_csv(V.DATA / "fixtures" / "cme_session_calendar.csv.gz", encoding="utf-8", dtype={"day": str})
            cal = cal[(cal["root"] == "NQ") & (cal["day"] < Z.CUT24)].set_index("day")
            Sx = C.session_features(dN, C.overnight(b, "NQ"), cal)
    finally:
        V.CUT = old
    x = {}
    for r in ("ES", "NQ"):
        Z.no_session_after(frames[r].index, f"the {r} session frame")
        xr = b[b["root"] == r][["session", "hhmm", "open", "high", "low", "close"]].copy()
        xr["hhmm"] = xr["hhmm"].astype(str)
        Z.no_session_after(xr["session"].unique(), f"{r}'s Globex bars")
        x[r] = xr
    rth = {r: b[(b["root"] == r) & (b["hhmm"] >= "09:30") & (b["hhmm"] <= "15:59")][["session", "high", "low"]] for r in ("ES", "NQ")}
    return {"C": C, "M": M, "V": V, "frames": frames, "tabs": tabs_all, "Sx": Sx, "x": x, "rth": rth}


def night_matrix(xr: pd.DataFrame, sessions: np.ndarray) -> dict[str, np.ndarray]:
    """Open/high/low/close per session x minute, 03:00 .. 09:29 (NaN where no bar)."""
    v = xr[(xr["hhmm"] >= "03:00") & (xr["hhmm"] <= "09:29")]
    cols = [col_hhmm(c) for c in range(NCOL)]
    out = {}
    for k in ("open", "high", "low", "close"):
        out[k] = v.pivot(index="session", columns="hhmm", values=k).reindex(index=sessions, columns=cols).to_numpy(float)
    out["cf"] = pd.DataFrame(out["close"]).ffill(axis=1).to_numpy(float)
    return out


# ================================================================================ the engine (vectorised)
def rnd(p: np.ndarray, tick: float) -> np.ndarray:
    return np.round(p / tick) * tick


def bracket(N: dict[str, np.ndarray], s: np.ndarray, c0: np.ndarray, F: np.ndarray, entry: np.ndarray, tgt: np.ndarray,
            stp: np.ndarray, tick: float, use_target: bool = True, use_stop: bool = True, last_col: int = NCOL - 1
            ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """From the fill bar c0: on the fill bar only the stop; after it the target (through a tick) and the stop (a tick
    against); a bar reaching both is stopped; else the close of `last_col` (09:29)."""
    n = len(s)
    idx = c0[:, None] + np.arange(NCOL)[None, :]
    live = idx <= last_col
    ix = np.clip(idx, 0, NCOL - 1)
    O, H, L = N["open"][s[:, None], ix], N["high"][s[:, None], ix], N["low"][s[:, None], ix]
    Fc, tg, sp = F[:, None], tgt[:, None], stp[:, None]
    after = np.arange(NCOL)[None, :] >= 1
    with np.errstate(invalid="ignore"):
        hit_s = live & np.where(Fc > 0, L <= sp, H >= sp) if use_stop else np.zeros_like(live)
        hit_t = live & after & np.where(Fc > 0, H >= tg + tick, L <= tg - tick) if use_target else np.zeros_like(live)
    BIG = NCOL + 1
    fs = np.where(hit_s.any(axis=1), hit_s.argmax(axis=1), BIG)
    ft = np.where(hit_t.any(axis=1), hit_t.argmax(axis=1), BIG)
    px = N["cf"][s, last_col].copy()
    kind = np.zeros(n, dtype=int)
    stop = (fs < BIG) & (fs <= ft)
    targ = (ft < BIG) & ~stop
    r = np.arange(n)
    if stop.any():
        o = O[r[stop], fs[stop]]
        beyond = np.isfinite(o) & np.where(F[stop] > 0, o <= stp[stop], o >= stp[stop])
        px[stop] = np.where(beyond, o, stp[stop]) - F[stop] * tick
        kind[stop] = -1
    if targ.any():
        o = O[r[targ], ft[targ]]
        beyond = np.isfinite(o) & np.where(F[targ] > 0, o >= tgt[targ], o <= tgt[targ])
        px[targ] = np.where(beyond, o, tgt[targ])
        kind[targ] = 1
    bar = np.where(stop, c0 + fs, np.where(targ, c0 + ft, last_col))
    return px, kind, bar


def fades(fr: pd.DataFrame, N: dict[str, np.ndarray], tick: float) -> dict[str, np.ndarray]:
    """Every candidate session's first fill (sell at up, buy at dn), vectorised."""
    Lh, Ll, A = (fr[c].to_numpy(float) for c in ("prior_high", "prior_low", "atr20"))
    up, dn = Lh + K * A, Ll - K * A
    o3 = N["open"][:, 0]
    with np.errstate(invalid="ignore"):
        cand = np.isfinite(o3) & (o3 > dn) & (o3 < up)
        hs = N["high"][:, :LAST_ENTRY_COL + 1] >= (up + tick)[:, None]
        hb = N["low"][:, :LAST_ENTRY_COL + 1] <= (dn - tick)[:, None]
    BIG = NCOL + 1
    fs = np.where(hs.any(axis=1), hs.argmax(axis=1), BIG)
    fb = np.where(hb.any(axis=1), hb.argmax(axis=1), BIG)
    both = cand & (fs < BIG) & (fs == fb)
    sell = cand & (fs < fb)
    buy = cand & (fb < fs)
    s = np.flatnonzero(sell | buy)
    F = np.where(sell[s], -1.0, 1.0)
    c0 = np.where(sell[s], fs[s], fb[s])
    o = N["open"][s, c0]
    lvl = np.where(sell[s], up[s], dn[s])
    entry = np.where(np.isfinite(o), np.where(F < 0, np.maximum(lvl, o), np.minimum(lvl, o)), lvl)
    return {"s": s, "F": F, "c0": c0, "entry": entry, "lvl": lvl, "A": A[s], "n_cand": int(cand.sum()),
            "n_outside_at_03": int((np.isfinite(o3) & ~cand).sum()), "n_no_03": int((~np.isfinite(o3)).sum()),
            "n_both_one_bar": int(both.sum())}


def outcomes(N: dict[str, np.ndarray], t: dict[str, np.ndarray], b: float, tick: float, upp: float, cost: float,
             last_col: int = NCOL - 1) -> dict[str, np.ndarray]:
    F, lvl, A = t["F"], t["lvl"], t["A"]
    tgt, stp = rnd(lvl + F * b * A, tick), rnd(lvl - F * b * A, tick)
    px, kind, bar = bracket(N, t["s"], t["c0"], F, t["entry"], tgt, stp, tick, last_col=last_col)
    g = F * (px - t["entry"]) * upp
    e2 = F * (N["cf"][t["s"], NCOL - 1] - t["entry"]) * upp
    mpx, _, _ = bracket(N, t["s"], t["c0"], -F, t["entry"], rnd(lvl - F * b * A, tick), rnd(lvl + F * b * A, tick), tick)
    return {"tgt": tgt, "stp": stp, "px": px, "kind": kind, "bar": bar, "g": g, "n": g - cost, "e2": e2,
            "mirror": -F * (mpx - t["entry"]) * upp, "dist_usd": np.abs(tgt - t["entry"]) * upp}


# ================================================================================ the second implementation (a loop)
def loop_trade(bb: dict[str, np.ndarray], Lh: float, Ll: float, A: float, b: float, tick: float, flat_col: int = NCOL - 1
               ) -> tuple[int, int, float, float] | None:
    """An independent bar loop over D744's night arrays: (fill column, side, fill price, exit price)."""
    m, o, h, l, c = bb["m"], bb["o"], bb["h"], bb["l"], bb["c"]
    if len(m) == 0 or m[0] != COL0:
        return None
    up, dn = Lh + K * A, Ll - K * A
    if not (dn < o[0] < up):
        return None
    fill = None
    for i in range(len(m)):
        if m[i] - COL0 > LAST_ENTRY_COL:
            break
        sh, bh = h[i] >= up + tick, l[i] <= dn - tick
        if sh and bh:
            return None
        if sh:
            fill = (i, -1, max(up, o[i]), up)
            break
        if bh:
            fill = (i, 1, min(dn, o[i]), dn)
            break
    if fill is None:
        return None
    i, D, entry, lvl = fill
    tgt = round((lvl + D * b * A) / tick) * tick
    stp = round((lvl - D * b * A) / tick) * tick
    for k in range(i, len(m)):
        if m[k] - COL0 > flat_col:
            break
        stop_hit = (l[k] <= stp) if D > 0 else (h[k] >= stp)
        targ_hit = k > i and ((h[k] >= tgt + tick) if D > 0 else (l[k] <= tgt - tick))
        if stop_hit:
            f = o[k] if ((o[k] <= stp) if D > 0 else (o[k] >= stp)) else stp
            return m[i] - COL0, D, float(entry), float(f - D * tick)
        if targ_hit:
            f = o[k] if ((o[k] >= tgt) if D > 0 else (o[k] <= tgt)) else tgt
            return m[i] - COL0, D, float(entry), float(f)
    j = np.flatnonzero(m - COL0 <= flat_col)
    return m[i] - COL0, D, float(entry), float(c[j[-1]])


# ================================================================================ the timing null (enumerated)
def null_offset(N: dict[str, np.ndarray], A_all: np.ndarray, t: dict[str, np.ndarray], b: float, j: int, tick: float,
                upp: float, pool: np.ndarray) -> float:
    """Each trade's fill minute and bracket (in A units) moved to session pool[(pos + j) % n], entered at that minute's
    bar open against that night's move since the 03:00 open."""
    n = len(pool)
    e = pool[(t["pos"] + j) % n]
    c0 = t["c0"]
    o = N["open"][e, c0]
    prev = N["cf"][e, np.maximum(c0 - 1, 0)]
    F = -np.sign(prev - N["open"][e, 0])
    Ae = A_all[e]
    ok = np.isfinite(o) & np.isfinite(F) & (F != 0) & np.isfinite(Ae) & (c0 >= 1)
    if not ok.any():
        return float("nan")
    tg, sp = rnd(o + F * b * Ae, tick), rnd(o - F * b * Ae, tick)
    px, _, _ = bracket(N, e[ok], c0[ok], F[ok], o[ok], tg[ok], sp[ok], tick)
    return float(np.mean(F[ok] * (px - o[ok]) * upp))


def null_all(N, A_all, t, b, tick, upp, pool, offsets=None, workers=WORKERS) -> np.ndarray:
    offs = offsets if offsets is not None else list(range(EDGE, len(pool) - EDGE))
    chunks = [offs[i::workers] for i in range(workers)]

    def run(ch):
        return [(j, null_offset(N, A_all, t, b, j, tick, upp, pool)) for j in ch]

    with ThreadPoolExecutor(workers) as ex:
        got = dict(x for part in ex.map(run, chunks) for x in part)
    return np.array([got[j] for j in offs])


# ================================================================================ statistics
def nw_t(x: np.ndarray, lag: int = 5) -> float:
    x = np.asarray(x, float)
    n = len(x)
    if n < 3:
        return float("nan")
    e = x - x.mean()
    s = float(e @ e) / n
    for k in range(1, lag + 1):
        s += 2 * (1 - k / (lag + 1)) * float(e[k:] @ e[:-k]) / n
    se = math.sqrt(s / n)
    return float(x.mean() / se) if se > 0 else float("nan")


def book(net: np.ndarray, gross: np.ndarray, days: np.ndarray, lo: str, hi: str, cost: float, kind: np.ndarray,
         F: np.ndarray, bars: np.ndarray, dist_usd: np.ndarray) -> dict[str, Any]:
    n = len(net)
    if n < 3:
        return {"trades": n}
    yrs = max((pd.Timestamp(hi) - pd.Timestamp(lo)).days / 365.25, 1e-9)
    tpy = n / yrs
    sd, dn = float(net.std(ddof=1)), float(np.sqrt(np.mean(np.minimum(net, 0) ** 2)))
    eq = np.cumsum(net)
    dd = float((np.maximum.accumulate(np.r_[0, eq]) - np.r_[0, eq]).max())
    srt = np.sort(net)
    cut = max(1, int(round(0.01 * n)))
    by_year = pd.Series(net, index=[d[:4] for d in days]).groupby(level=0).sum()
    best2 = by_year.sort_values(ascending=False).index[:2]
    w, l_ = net[net > 0], net[net <= 0]
    s_ = pd.Series(net)
    top = int(np.argmax(net))
    return {"trades": n, "trades_per_year": tpy, "mean_net": float(net.mean()), "mean_gross": float(gross.mean()),
            "median_net": float(np.median(net)), "t_gross_nw": nw_t(gross), "t_net_nw": nw_t(net),
            "sharpe_net": float(net.mean() / sd * math.sqrt(tpy)) if sd > 0 else None,
            "sortino_net": float(net.mean() / dn * math.sqrt(tpy)) if dn > 0 else None,
            "sharpe_gross": float(gross.mean() / gross.std(ddof=1) * math.sqrt(tpy)) if gross.std(ddof=1) > 0 else None,
            "max_dd": dd, "total_net": float(net.sum()), "win_rate": float((net > 0).mean()),
            "payoff": float(w.mean() / -l_.mean()) if len(w) and len(l_) and l_.mean() < 0 else None,
            "skew": float(s_.skew()), "kurtosis": float(s_.kurt()),
            "mean_ex_top1pct": float(srt[:-cut].mean()), "mean_ex_bottom1pct": float(srt[cut:].mean()),
            "mean_trimmed1pct": float(srt[cut:-cut].mean()) if n > 2 * cut else None,
            "exit_mix": {"target": float((kind == 1).mean()), "stop": float((kind == -1).mean()), "close": float((kind == 0).mean())},
            "sell_mean_net": float(net[F < 0].mean()) if (F < 0).any() else None, "sell_n": int((F < 0).sum()),
            "buy_mean_net": float(net[F > 0].mean()) if (F > 0).any() else None, "buy_n": int((F > 0).sum()),
            "minutes_held_mean": float(bars.mean()), "mean_abs_gross_vs_2c": float(np.abs(gross).mean() / (2 * cost)),
            "breakeven_cost_usd": float(gross.mean()), "median_target_usd": float(np.median(dist_usd)),
            "years": {k: round(float(v), 2) for k, v in by_year.items()},
            "positive_years": f"{int((by_year > 0).sum())} of {len(by_year)}",
            "largest_year_share": float(by_year.max() / net.sum()) if net.sum() > 0 else None,
            "net_without_best_two_years": float(by_year.drop(best2).sum()),
            "top_trade": {"session": str(days[top]), "net_usd": float(net[top]), "side": "sell" if F[top] < 0 else "buy"}}


# ================================================================================ audits
def known_answer(L_: dict[str, Any]) -> dict[str, Any]:
    """D744's U, rebuilt with D744's own night_break / night_exit on NQ sessions with a finite D744 ctier."""
    C, d, Sx, x = L_["C"], L_["frames"]["NQ"], L_["Sx"], L_["x"]["NQ"]
    a = E.asia_frame(x)
    E.asia_audit(a)
    a = a.reindex(d.index)
    asia = ((a["a_high"] - a["a_low"] - (a["a_last"] - d["prior_close"]).abs()) / d["atr20"]).to_numpy(float)
    rv5 = Sx["rv5"].reindex(d.index).to_numpy(float)
    ctier = C.tiers((C.tiers(rv5) + C.tiers(asia)) / 2)
    grp = {s: v for s, v in x[(x["hhmm"] >= E.NIGHT_FROM) & (x["hhmm"] <= E.FLAT)].groupby("session")}
    g = []
    for k, s in enumerate(d.index.astype(str)):
        if not math.isfinite(ctier[k]) or s not in grp:
            continue
        bb = E.night_arrays(grp[s])
        if len(bb["m"]) == 0 or bb["m"][0] != E.mod(E.NIGHT_FROM):
            continue
        rec = d.iloc[k]
        Lh, Ll, A = float(rec["prior_high"]), float(rec["prior_low"]), float(rec["atr20"])
        if not (Ll - E.K_ATR * A < bb["o"][0] < Lh + E.K_ATR * A):
            continue
        p = E.night_break(bb, Lh, Ll, A)
        if p is None:
            continue
        px, _, _ = E.night_exit(bb, p["i"], p["D"], p["entry"], p["L"], A)
        g.append(p["D"] * (px / p["entry"] - 1) * 1e4)
    got = {"trades": len(g), "gross_bp": float(np.mean(g)), "first_window_session": str(d.index[np.isfinite(ctier)][0])}
    need(got["trades"] == KNOWN_U["trades"] and abs(got["gross_bp"] - KNOWN_U["gross_bp"]) < 1e-9,
         f"known answer: D744's U is not reproduced ({got} against {KNOWN_U})")
    return got


def level_audit(L_: dict[str, Any], r: str, sample: list[str], same_day: bool = False) -> None:
    """prior_high / prior_low re-derived from the PREVIOUS fixture session's RTH bars (same_day: the canary)."""
    fr, tabs, rth = L_["frames"][r], L_["tabs"][r], L_["rth"][r]
    order = list(tabs.index.astype(str))
    pos = {s: i for i, s in enumerate(order)}
    for s in sample:
        i = pos[s]
        src = order[i] if same_day else order[i - 1]
        x = rth[rth["session"] == src]
        need(math.isclose(float(x["high"].max()), float(fr.at[s, "prior_high"]), abs_tol=1e-9)
             and math.isclose(float(x["low"].min()), float(fr.at[s, "prior_low"]), abs_tol=1e-9),
             f"lag: {r} {s}'s levels are not the previous session's RTH high and low")


def sign_audit() -> None:
    """A hand-built night: a sold break that falls to its target pays +; one that rises to its stop pays -."""
    def night(path_after: float) -> dict[str, np.ndarray]:
        O = np.full((1, NCOL), 100.0)
        H, Lw = O + 0.5, O - 0.5
        H[0, 10] = 103.0                      # the break: trades through up = 102.5 at col 10
        O[0, 11:], H[0, 11:], Lw[0, 11:] = path_after, path_after + 0.5, path_after - 0.5
        return {"open": O, "high": H, "low": Lw, "close": O.copy(), "cf": O.copy()}
    fr = pd.DataFrame({"prior_high": [100.5], "prior_low": [95.0], "atr20": [8.0]})   # up = 102.5, dn = 93.0
    for after, want in ((97.0, 1), (110.0, -1)):
        N = night(after)
        t = fades(fr, N, 0.25)
        need(len(t["s"]) == 1 and t["F"][0] == -1 and t["c0"][0] == 10, "sign: the sell limit did not fill at the break")
        o = outcomes(N, t, 0.25, 0.25, 2.0, 4.60)
        need(o["kind"][0] == want and (o["n"][0] > 0) == (want == 1), f"sign: the sold break moving to {after} paid {o['n'][0]}")


# ================================================================================ the study
def other_lines() -> dict[str, pd.Series]:
    import forward_f2_c1_ledgers as FW
    import stage0_d746_intraday_fades as S746
    out = S746.other_lines()
    b = FW.g0_bars(Path("C:/Users/O/Desktop/Projects/Backtest Framework/data/fixtures/fut_opening_globex_1m.csv.gz"), "2024-01-01")
    c1 = FW.c1_rows(b, FW.g0_use(Path("C:/Users/O/Desktop/Projects/Backtest Framework/data"), "2024-01-01"), "2016-01-04")
    out["c1"] = c1[c1["status"] == "trade"].set_index("session")["net_usd"].astype(float)
    return out


def run() -> int:
    need(not OUT.exists(), f"{OUT.name} exists: D747 is run-once")
    t0 = time.time()
    sign_audit()
    L_ = load()
    mcs = L_["M"].micro_costs()
    costs = {r: {"night": 3.0 + E.NIGHT_X * mcs[r]["crossing_ticks"] * mcs[r]["tick_usd"],
                 "day": 3.0 + mcs[r]["crossing_ticks"] * mcs[r]["tick_usd"]} for r in ("ES", "NQ")}
    need(abs(costs["NQ"]["night"] - 4.60068165916707) < 1e-9, f"the NQ night cost is not D744's: {costs['NQ']}")
    need(all(c["night"] > c["day"] for c in costs.values()), "right quantity: night cost <= day cost")
    ka = known_answer(L_)
    others = other_lines()
    out: dict[str, Any] = {"spec": SPEC.name, "seal": "nothing on or after 2024-01-01", "costs_usd": costs,
                           "known_answer_d744_U": ka, "cells": {}}
    rng = np.random.default_rng(SEED)
    for r in ("ES", "NQ"):
        fr = L_["frames"][r]
        sess = fr.index.astype(str).to_numpy()
        N = night_matrix(L_["x"][r], sess)
        smp = list(rng.choice(sess[sess >= "2016-03-01"], 25, replace=False))
        level_audit(L_, r, smp)
        try:
            level_audit(L_, r, smp, same_day=True)
        except D747Error:
            pass
        else:
            raise D747Error("lag: the same-day level canary did not fire")
        tick, upp = TICK[r], USD_PT[r]
        t_all = fades(fr, N, tick)
        need(t_all["n_outside_at_03"] > 0, "right quantity: the 03:00-inside condition never binds")
        grp = {s: v for s, v in L_["x"][r][(L_["x"][r]["hhmm"] >= "03:00") & (L_["x"][r]["hhmm"] <= "09:29")].groupby("session")}
        A_all = fr["atr20"].to_numpy(float)
        for sl, (root, lo, hi) in SLICES.items():
            if root != r:
                continue
            pool = np.flatnonzero((sess >= lo) & (sess <= hi))
            keep = np.isin(t_all["s"], pool)
            t = {k: (v[keep] if isinstance(v, np.ndarray) else v) for k, v in t_all.items()}
            t["pos"] = np.searchsorted(pool, t["s"])
            days = sess[t["s"]]
            for b in BS:
                key = f"{sl}_b{b:g}"
                cost = costs[r]["night"]
                o = outcomes(N, t, b, tick, upp, cost)
                need(not np.allclose(o["g"], o["e2"]), f"right quantity: E1 equals E2 in {key}")
                # the second implementation, every trade, and its 09:28 canary
                n_dis = 0
                for i, s in enumerate(t["s"]):
                    rec = fr.iloc[s]
                    bb = E.night_arrays(grp[sess[s]])
                    lt = loop_trade(bb, float(rec["prior_high"]), float(rec["prior_low"]), float(rec["atr20"]), b, tick)
                    need(lt is not None and lt[0] == t["c0"][i] and lt[1] == t["F"][i] and lt[2] == t["entry"][i]
                         and lt[3] == o["px"][i], f"{key} {sess[s]}: the loop disagrees ({lt} against "
                         f"{(t['c0'][i], t['F'][i], t['entry'][i], o['px'][i])})")
                    lc = loop_trade(bb, float(rec["prior_high"]), float(rec["prior_low"]), float(rec["atr20"]), b, tick, NCOL - 2)
                    n_dis += int(lc is None or lc[3] != lt[3])
                need(n_dis > 0, f"{key}: the 09:28 canary agreed with every trade")
                res: dict[str, Any] = {"slice": [lo, hi], "candidates": int(np.isin(np.flatnonzero(np.isfinite(N["open"][:, 0])), pool).sum()),
                                       "E1": book(o["n"], o["g"], days, lo, hi, cost, o["kind"], t["F"], o["bar"] - t["c0"] + 1, o["dist_usd"]),
                                       "E1_net_at_day_cost": float((o["g"] - costs[r]["day"]).mean()) if len(o["g"]) else None,
                                       "E2_flat_0929": {"mean_gross": float(o["e2"].mean()), "t": nw_t(o["e2"])} if len(o["e2"]) else None,
                                       "mirror_gross": float(o["mirror"].mean()) if len(o["mirror"]) else None,
                                       "canary_0928_disagreements": n_dis}
                if len(o["g"]) >= 20:
                    curve = FO.partial_oracle_curve(o["n"], o["n"], RHOS, 0.5, N_DRAW, np.random.default_rng(SEED))
                    take = FO.oracle_take(o["n"])
                    res["O1_oracle"] = {"share_taken": float(take.mean()), "per_candidate": float(o["n"][take].sum() / len(o["n"]))}
                    res["O2_curve"] = [(c["rho"], c["mean_net_per_trade"]) for c in curve]
                    res["O2_rho005_mean_net"] = next(c["mean_net_per_trade"] for c in curve if abs(c["rho"] - 0.05) < 1e-12)
                    res["O3_median_target_vs_2c"] = float(np.median(o["dist_usd"]) / (2 * cost))
                    nul = null_all(N, A_all, t, b, tick, upp, pool)
                    nul = nul[np.isfinite(nul)]
                    res["C2_timing_null"] = {"offsets": int(len(nul)), "score": float(o["g"].mean()),
                                             "p50": float(np.median(nul)), "p95": float(np.percentile(nul, 95)),
                                             "p": float((nul >= o["g"].mean()).mean())}
                    daily = pd.Series(o["n"], index=days).groupby(level=0).sum().reindex(sess[pool], fill_value=0.0)
                    res["component_corr"] = {k: float(np.corrcoef(daily.to_numpy(), v.reindex(sess[pool], fill_value=0.0).to_numpy())[0, 1])
                                             for k, v in others.items()}
                out["cells"][key] = res
                e1 = res["E1"]
                c2 = res.get("C2_timing_null", {})
                print(f"[{key}] n {e1.get('trades')}, gross {e1.get('mean_gross', float('nan')):+.2f} (t {e1.get('t_gross_nw', float('nan')):+.2f}), "
                      f"net {e1.get('mean_net', float('nan')):+.2f}, C2 p50/p95 {c2.get('p50', float('nan')):+.2f}/{c2.get('p95', float('nan')):+.2f}",
                      flush=True)
        out[f"{r}_fill_counts"] = {k: t_all[k] for k in ("n_cand", "n_outside_at_03", "n_no_03", "n_both_one_bar")}
    out["decision"] = decide(out, costs)
    out["runtime_min"] = round((time.time() - t0) / 60, 2)
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"decision": out["decision"], "runtime_min": out["runtime_min"]}, indent=1, default=float))
    return 0


def decide(out: dict[str, Any], costs: dict[str, Any]) -> dict[str, Any]:
    es, nq = out["cells"][f"ES_full_b{PRIMARY_B:g}"], out["cells"][f"NQ_early_b{PRIMARY_B:g}"]
    e, q = es["E1"], nq["E1"]
    c1 = (e["trades"] >= 100 and e["mean_gross"] > 0 and e["t_gross_nw"] >= 2
          and e["mean_gross"] > es["C2_timing_null"]["p95"] and e["mean_net"] > 0)
    c2 = q.get("mean_gross", -1) > 0
    c3 = (int(e["positive_years"].split(" of ")[0]) >= 5 and e["largest_year_share"] is not None
          and e["largest_year_share"] < 0.5 and e["net_without_best_two_years"] > 0)
    lead = ((e["mean_gross"] > 0 and e["t_gross_nw"] >= 1.28 and e["mean_net"] > 0)
            or (q.get("t_gross_nw", 0) >= 2 and q.get("mean_gross", -1) > nq.get("C2_timing_null", {}).get("p95", np.inf)))
    no_room = e["mean_gross"] < 2 * costs["ES"]["night"] and es.get("O2_rho005_mean_net", 0) <= 0
    verdict = "SUPPORTED" if (c1 and c2 and c3) else ("LEAD" if lead else "NOT SUPPORTED")
    return {"cond1_es_full": bool(c1), "cond2_nq_early_same_sign": bool(c2), "cond3_es_standard": bool(c3),
            "NO_ROOM_es_full": bool(no_room), "verdict": verdict}


# ================================================================================ self-test
def selftest() -> int:
    fails: list[str] = []
    try:
        sign_audit()
    except D747Error as e:
        fails.append(str(e))
    # the vectorised engine against the loop on a synthetic random night panel
    rng = np.random.default_rng(1)
    S = 300
    O = 100 + np.cumsum(rng.normal(0, 0.4, (S, NCOL)), axis=1)
    O = np.round(O / 0.25) * 0.25
    H = O + np.round(rng.uniform(0, 1.0, (S, NCOL)) / 0.25) * 0.25
    Lw = O - np.round(rng.uniform(0, 1.0, (S, NCOL)) / 0.25) * 0.25
    Cc = np.clip(np.round((O + rng.normal(0, 0.3, (S, NCOL))) / 0.25) * 0.25, Lw, H)
    N = {"open": O, "high": H, "low": Lw, "close": Cc, "cf": Cc}
    fr = pd.DataFrame({"prior_high": O[:, 0] + rng.uniform(0.5, 4, S), "prior_low": O[:, 0] - rng.uniform(0.5, 4, S),
                       "atr20": rng.uniform(2, 6, S)})
    t = fades(fr, N, 0.25)
    o = outcomes(N, t, 0.25, 0.25, 2.0, 4.6)
    bad = 0
    for i, s in enumerate(t["s"]):
        bb = {"m": np.arange(COL0, COL0 + NCOL), "o": O[s], "h": H[s], "l": Lw[s], "c": Cc[s]}
        lt = loop_trade(bb, float(fr.iloc[s]["prior_high"]), float(fr.iloc[s]["prior_low"]), float(fr.iloc[s]["atr20"]), 0.25, 0.25)
        bad += int(lt is None or lt[0] != t["c0"][i] or lt[1] != t["F"][i] or lt[2] != t["entry"][i] or lt[3] != o["px"][i])
    if bad or len(t["s"]) < 50:
        fails.append(f"engine vs loop: {bad} disagreements on {len(t['s'])} synthetic trades")
    # chunk == whole on the null
    t["pos"] = t["s"].copy()
    pool = np.arange(S)
    offs = list(range(EDGE, EDGE + 30))
    if not np.array_equal(null_all(N, fr["atr20"].to_numpy(float), t, 0.25, 0.25, 2.0, pool, offs, 1),
                          null_all(N, fr["atr20"].to_numpy(float), t, 0.25, 0.25, 2.0, pool, offs, 6), equal_nan=True):
        fails.append("threaded null != serial null")
    if fails:
        print("SELFTEST FAILED:", fails)
        return 1
    print(f"SELFTEST OK: the sign audit in money (a sold break falling to its target pays, rising to its stop loses); "
          f"the vectorised engine equals the independent loop on {len(t['s'])} synthetic trades (fill bar, side, fill, "
          f"exit); the threaded timing null equals the serial one")
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
    return 2


if __name__ == "__main__":
    sys.exit(main())
