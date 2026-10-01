"""D746 Stage 0: intraday mean reversion for the prop book. Is there room to fade an extreme stretch (A) or an opening
gap (B) on ES and YM at one micro? Spec: docs/decisions/D746-STAGE-0-PRE-REG-intraday-fades-stretch-and-gap.md.

    uv run --no-sync python scripts/stage0_d746_intraday_fades.py --selftest
    uv run --no-sync python scripts/stage0_d746_intraday_fades.py --run

A, the stretch fade: the first minute in 10:00-14:30 with |z| >= k (D727's z), faded to the session VWAP with a 1:1
bracket. B, the gap fade: an opening gap >= g_min sigma_oc, faded from the open to yesterday's close with a 1:1 bracket.
E1 = target, stop or the 15:59 close. One MES ($4.42) or MYM ($3.80); the prize bar is 2 x cost. Every fixture and
DIX.csv are restricted AS TEXT to rows before 2024-01-01 before a value is parsed.
"""
from __future__ import annotations

import argparse
import gzip
import io
import json
import math
import re
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

from backtest_framework.validation import filter_oracle as FO  # noqa: E402

MAIN_DATA = Path("C:/Users/O/Desktop/Projects/Backtest Framework/data")
SPEC = REPO / "docs" / "decisions" / "D746-STAGE-0-PRE-REG-intraday-fades-stretch-and-gap.md"
OUT = REPO / "data" / "stage0_d746_intraday_fades.json"
SEAL, LO, HI = "2024-01-01", "2016-01-04", "2023-12-29"
ROOTS = ("ES", "YM")
NMIN, M_LO, M_HI = 390, 30, 300
KS, GS = (2.0, 2.5, 3.0), (0.25, 0.5, 1.0)
PRIMARY = {"A": 2.5, "B": 0.5}
RHOS = (0.0, 0.025, 0.05, 0.075, 0.10, 0.15, 0.20, 0.30)
N_DRAW, SEED, EDGE, NW_LAGS, WORKERS = 500, 746, 20, 5, 12
DATE = re.compile(r"\d{4}-\d{2}-\d{2}$")
MINS = [f"{(570 + m) // 60:02d}:{(570 + m) % 60:02d}" for m in range(NMIN)]


class D746Error(AssertionError):
    pass


# ================================================================================ inputs (text-restricted)
def restrict_text(src: Path, field: int, before: str) -> bytes:
    """The header and every line whose comma field `field` is a date before `before`; no dropped line is parsed."""
    out = io.StringIO()
    opener = gzip.open if src.suffix == ".gz" else open
    with opener(src, "rt", encoding="utf-8", newline="") as f:
        out.write(f.readline())
        for line in f:
            parts = line.split(",", field + 1)
            d = parts[field] if len(parts) > field else ""
            if not DATE.match(d):
                raise D746Error(f"{src.name}: field {field} is not a date on a data line")
            if d < before:
                out.write(line)
    return out.getvalue().encode("utf-8")


def rth(root: str) -> pd.DataFrame:
    b = pd.read_csv(io.BytesIO(restrict_text(MAIN_DATA / "fixtures" / f"fut_{root}_rth_1m.csv.gz", 0, SEAL)),
                    dtype={"day": str, "hhmm": str, "contract": str}, encoding="utf-8")
    b = b[(b["day"] >= LO) & (b["day"] <= HI)]
    if (b["day"] >= SEAL).any():
        raise D746Error("seal: a bar on or after 2024-01-01")
    return b


def costs() -> dict[str, dict[str, float]]:
    j = json.loads((MAIN_DATA / "futures_costs.json").read_text(encoding="utf-8"))
    out = {}
    for r in ROOTS:
        m = j["roots"][r]["micro"]
        x = float(m["crossing_ticks_rt"][m["default_line"]]["value"])
        out[r] = {"symbol": m["symbol"], "usd_pt": float(m["usd_per_point"]), "tick": float(m["tick_points"]),
                  "cost": float(m["commission_rt_usd"]["value"]) + x * float(m["tick_usd"])}
    if abs(out["ES"]["cost"] - 4.418) > 0.001 or abs(out["YM"]["cost"] - 3.797) > 0.001:
        raise D746Error(f"cost lines moved: {out}")
    return out


def gex_series() -> pd.Series:
    raw = restrict_text(MAIN_DATA / "raw" / "squeezemetrics" / "DIX.csv", 0, SEAL)
    d = pd.read_csv(io.BytesIO(raw), encoding="utf-8", dtype={"date": str})
    return d.set_index("date")["gex"].astype(float).sort_index()


def gex_state(gex: pd.Series, days: np.ndarray) -> np.ndarray:
    """Per session, from the GEX row strictly before it (D663's gex_prior): 'short' (< 0), 'long_low' / 'long_high'
    (against the median of the 250 rows up to and including that row), or 'none'."""
    import stage0_d663_per_root_gamma_break as G
    prior = G.gex_prior(gex, pd.Index(days)).to_numpy(float)
    med = gex.rolling(250, min_periods=250).median()
    pos = np.searchsorted(gex.index.to_numpy(), days, side="left") - 1
    m = np.where(pos >= 0, med.to_numpy(float)[np.clip(pos, 0, None)], np.nan)
    out = np.full(len(days), "none", dtype=object)
    ok = np.isfinite(prior)
    out[ok & (prior < 0)] = "short"
    out[ok & (prior >= 0) & np.isfinite(m) & (prior < m)] = "long_low"
    out[ok & (prior >= 0) & np.isfinite(m) & (prior >= m)] = "long_high"
    return out


def panel(root: str, b: pd.DataFrame) -> dict[str, Any]:
    """D727's panel, plus the raw bars' open/high/low/close/volume pivoted on its days, and B's prior close."""
    import stage0_d727_trend_curve as T
    pn = T.panel_from_raw(root, b)
    raw, days = pn["raw"], pn["days"]
    piv = {c: raw.pivot(index="day", columns="hhmm", values=c).reindex(index=days, columns=MINS).to_numpy(float)
           for c in ("open", "high", "low", "close", "volume")}
    con_all = raw.groupby("day")["contract"].agg(lambda s: s.value_counts().index[0]).reindex(pn["all_days"]).to_numpy(str)
    ia = {d: i for i, d in enumerate(pn["all_days"])}
    cprev = np.full(len(days), np.nan)
    for k, d in enumerate(days):
        i = ia[d]
        if i > 0 and con_all[i - 1] == con_all[i]:
            cprev[k] = pn["all_C_last"][i - 1]
    return {"root": root, "days": days, "C": pn["C"], "O": pn["O"], "soc": pn["soc"], "Op": piv["open"],
            "H": piv["high"], "L": piv["low"], "Cr": piv["close"], "V": piv["volume"], "cprev": cprev, "raw": raw,
            "all_days": pn["all_days"]}


def vwap_before(P: dict[str, Any]) -> np.ndarray:
    """VW[d, m] = the volume-weighted typical price of bars 0 .. m-1 (NaN at m = 0)."""
    tp = (P["H"] + P["L"] + P["Cr"]) / 3
    v = np.where(np.isfinite(tp) & np.isfinite(P["V"]), P["V"], 0.0)
    pv = np.where(v > 0, tp * v, 0.0)
    cpv, cv = np.cumsum(pv, axis=1), np.cumsum(v, axis=1)
    out = np.full(P["H"].shape, np.nan)
    with np.errstate(invalid="ignore", divide="ignore"):
        out[:, 1:] = cpv[:, :-1] / cv[:, :-1]
    return out


# ================================================================================ the bracket
def round_target(entry: np.ndarray, tgt: np.ndarray, F: np.ndarray, tick: float) -> np.ndarray:
    """The target on the tick grid, on the near (less favourable) side."""
    q = (tgt - entry) / tick
    return entry + np.where(F > 0, np.floor(q + 1e-9), np.ceil(q - 1e-9)) * tick


def bracket(P: dict[str, Any], d: np.ndarray, m0: np.ndarray, F: np.ndarray, entry: np.ndarray, tgt: np.ndarray,
            stp: np.ndarray, tick: float, use_stop: bool = True, use_target: bool = True) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Exit price, exit bar and kind (1 target, -1 stop, 0 close) for each trade; bars from the entry bar on. A target
    fills only when a bar trades through it by a tick; a bar reaching both is stopped; a stop fill takes one tick."""
    n = len(d)
    idx = m0[:, None] + np.arange(NMIN)[None, :]
    live = idx < NMIN
    ix = np.clip(idx, 0, NMIN - 1)
    H, L, Op = P["H"][d[:, None], ix], P["L"][d[:, None], ix], P["Op"][d[:, None], ix]
    Fc, tg, sp = F[:, None], tgt[:, None], stp[:, None]
    with np.errstate(invalid="ignore"):
        hit_t = live & np.where(Fc > 0, H >= tg + tick, L <= tg - tick) if use_target else np.zeros_like(live)
        hit_s = live & np.where(Fc > 0, L <= sp, H >= sp) if use_stop else np.zeros_like(live)
    BIG = NMIN + 1
    ft = np.where(hit_t.any(axis=1), hit_t.argmax(axis=1), BIG)
    fs = np.where(hit_s.any(axis=1), hit_s.argmax(axis=1), BIG)
    px = P["C"][d, NMIN - 1].copy()
    bar = np.full(n, NMIN - 1)
    kind = np.zeros(n, dtype=int)
    stop = (fs < BIG) & (fs <= ft)
    targ = (ft < BIG) & ~stop
    r = np.arange(n)
    if stop.any():
        o = Op[r[stop], fs[stop]]
        beyond = np.isfinite(o) & np.where(F[stop] > 0, o <= stp[stop], o >= stp[stop])
        f = np.where(beyond, o, stp[stop])
        px[stop] = f - F[stop] * tick
        bar[stop], kind[stop] = m0[stop] + fs[stop], -1
    if targ.any():
        o = Op[r[targ], ft[targ]]
        beyond = np.isfinite(o) & np.where(F[targ] > 0, o >= tgt[targ], o <= tgt[targ])
        px[targ] = np.where(beyond, o, tgt[targ])
        bar[targ], kind[targ] = m0[targ] + ft[targ], 1
    return px, bar, kind


# ================================================================================ the setups
def setup_a(P: dict[str, Any], k: float, tick: float) -> dict[str, np.ndarray]:
    C, O, s = P["C"], P["O"], P["soc"]
    ms = np.arange(M_LO, M_HI + 1)
    Z = (C[:, ms - 1] - O[:, None]) / (s[:, None] * np.sqrt(ms / NMIN)[None, :])
    hit = np.abs(Z) >= k
    has = hit.any(axis=1)
    d = np.flatnonzero(has)
    m0 = ms[hit[d].argmax(axis=1)]
    z0 = Z[d, m0 - M_LO]
    F = -np.sign(z0)
    entry = np.where(np.isfinite(P["Op"][d, m0]), P["Op"][d, m0], C[d, m0 - 1])
    vw = vwap_before(P)[d, m0]
    tgt = round_target(entry, vw, F, tick)
    ok = np.isfinite(tgt) & (F * (tgt - entry) >= 2 * tick)
    dist = np.abs(tgt - entry)
    return {"d": d[ok], "m0": m0[ok], "F": F[ok], "entry": entry[ok], "tgt": tgt[ok], "stp": (entry - F * dist)[ok],
            "dist": dist[ok], "x": z0[ok], "skipped_vwap": int((~ok).sum()), "triggered": int(len(d))}


def setup_b(P: dict[str, Any], g_min: float, tick: float) -> dict[str, np.ndarray]:
    O, s, cp = P["O"], P["soc"], P["cprev"]
    g = O - cp
    with np.errstate(invalid="ignore"):
        trig = np.isfinite(g) & (np.abs(g) >= g_min * s) & (np.abs(g) >= 2 * tick)
    d = np.flatnonzero(trig)
    F = -np.sign(g[d])
    entry = O[d]
    dist = np.abs(g[d])
    return {"d": d, "m0": np.zeros(len(d), dtype=int), "F": F, "entry": entry, "tgt": cp[d], "stp": entry - F * dist,
            "dist": dist, "x": g[d] / s[d], "skipped_vwap": 0, "triggered": int(len(d))}


def outcomes(P: dict[str, Any], t: dict[str, np.ndarray], cl: dict[str, float]) -> dict[str, np.ndarray]:
    tick, upp = cl["tick"], cl["usd_pt"]
    args = (P, t["d"], t["m0"], t["F"], t["entry"], t["tgt"], t["stp"], tick)
    p1, b1, k1 = bracket(*args)
    p3, _, k3 = bracket(*args, use_stop=False)
    e2 = P["C"][t["d"], NMIN - 1]
    g1 = t["F"] * (p1 - t["entry"]) * upp
    return {"g1": g1, "n1": g1 - cl["cost"], "kind1": k1, "bars1": b1 - t["m0"] + 1,
            "g2": t["F"] * (e2 - t["entry"]) * upp, "g3": t["F"] * (p3 - t["entry"]) * upp, "kind3": k3,
            "mirror_g1": -t["F"] * (bracket(P, t["d"], t["m0"], -t["F"], t["entry"],
                                            t["entry"] - t["F"] * t["dist"], t["entry"] + t["F"] * t["dist"], tick)[0]
                                    - t["entry"]) * upp}


# ================================================================================ the timing null (enumerated)
def null_offset(P: dict[str, Any], setup: str, t: dict[str, np.ndarray], j: int, cl: dict[str, float]) -> float:
    """C2 at offset j: every trade's minute and sigma-unit bracket moved to day d + j, against that day's own move."""
    n = len(P["days"])
    e = (t["d"] + j) % n
    m0 = t["m0"]
    s = P["soc"][e]
    if setup == "A":
        F = -np.sign(P["C"][e, m0 - 1] - P["O"][e])
        entry = np.where(np.isfinite(P["Op"][e, m0]), P["Op"][e, m0], P["C"][e, m0 - 1])
    else:
        F = -np.sign(P["O"][e] - P["cprev"][e])
        entry = P["O"][e]
    a = t["dist"] / P["soc"][t["d"]]
    tgt = round_target(entry, entry + F * a * s, F, cl["tick"])
    ok = np.isfinite(F) & (F != 0) & np.isfinite(entry) & np.isfinite(tgt) & (np.abs(tgt - entry) >= cl["tick"])
    if not ok.any():
        return float("nan")
    dist = np.abs(tgt - entry)
    px, _, _ = bracket(P, e[ok], m0[ok], F[ok], entry[ok], tgt[ok], (entry - F * dist)[ok], cl["tick"])
    return float(np.mean(F[ok] * (px - entry[ok]) * cl["usd_pt"]))


def null_all(P: dict[str, Any], setup: str, t: dict[str, np.ndarray], cl: dict[str, float],
             offsets: list[int] | None = None, workers: int = WORKERS) -> np.ndarray:
    n = len(P["days"])
    offs = offsets if offsets is not None else list(range(EDGE, n - EDGE))
    chunks = [offs[i::workers] for i in range(workers)]

    def run(ch: list[int]) -> list[tuple[int, float]]:
        return [(j, null_offset(P, setup, t, j, cl)) for j in ch]

    with ThreadPoolExecutor(workers) as ex:
        got = dict(x for part in ex.map(run, chunks) for x in part)
    return np.array([got[j] for j in offs])


# ================================================================================ statistics
def nw_t(x: np.ndarray, lag: int = NW_LAGS) -> float:
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


def book(net: np.ndarray, gross: np.ndarray, days: np.ndarray, bars: np.ndarray, cost: float, dist_usd: np.ndarray) -> dict[str, Any]:
    n = len(net)
    if n < 3:
        return {"trades": n}
    yrs = max((pd.Timestamp(HI) - pd.Timestamp(LO)).days / 365.25, 1e-9)
    tpy = n / yrs
    sd, dn = float(net.std(ddof=1)), float(np.sqrt(np.mean(np.minimum(net, 0) ** 2)))
    eq = np.cumsum(net)
    dd = float((np.maximum.accumulate(np.r_[0, eq]) - np.r_[0, eq]).max())
    srt = np.sort(net)
    cut = max(1, int(round(0.01 * n)))
    by_year = pd.Series(net, index=[d[:4] for d in days]).groupby(level=0).sum()
    w, l_ = net[net > 0], net[net <= 0]
    s_ = pd.Series(net)
    return {"trades": n, "trades_per_year": tpy, "mean_net": float(net.mean()), "mean_gross": float(gross.mean()),
            "median_net": float(np.median(net)), "t_net_nw": nw_t(net), "t_gross_nw": nw_t(gross),
            "sharpe_net": float(net.mean() / sd * math.sqrt(tpy)) if sd > 0 else None,
            "sortino_net": float(net.mean() / dn * math.sqrt(tpy)) if dn > 0 else None,
            "sharpe_gross": float(gross.mean() / gross.std(ddof=1) * math.sqrt(tpy)) if gross.std(ddof=1) > 0 else None,
            "max_dd": dd, "total_net": float(net.sum()), "win_rate": float((net > 0).mean()),
            "payoff": float(w.mean() / -l_.mean()) if len(w) and len(l_) and l_.mean() < 0 else None,
            "skew": float(s_.skew()), "kurtosis": float(s_.kurt()),
            "mean_ex_top1pct": float(srt[:-cut].mean()), "mean_ex_bottom1pct": float(srt[cut:].mean()),
            "mean_trimmed1pct": float(srt[cut:-cut].mean()) if n > 2 * cut else None,
            "exposure_minutes_mean": float(bars.mean()), "mean_move_vs_2c": float(np.abs(gross).mean() / (2 * cost)),
            "breakeven_cost_usd": float(gross.mean()), "median_target_usd": float(np.median(dist_usd)),
            "years": {k: round(float(v), 2) for k, v in by_year.items()},
            "positive_years": f"{int((by_year > 0).sum())} of {len(by_year)}",
            "largest_year_share": float(by_year.max() / net.sum()) if net.sum() > 0 else None}


def holm(ps: dict[str, float]) -> dict[str, float]:
    items = sorted(ps.items(), key=lambda kv: kv[1])
    m, out, run = len(items), {}, 0.0
    for i, (k, p) in enumerate(items):
        run = max(run, min(1.0, (m - i) * p))
        out[k] = run
    return out


# ================================================================================ audits
def lag_audit(P: dict[str, Any], setup: str, t: dict[str, np.ndarray], sample: list[int], shift: int = 0) -> None:
    """Second implementation from the raw rows: z at the trigger minute (A), the VWAP at entry (A), C_prev (B). It
    reads bars that start before the entry; shift = 1 (the canary) reads the entry bar."""
    raw = P["raw"]
    ia = {d: i for i, d in enumerate(P["all_days"])}
    for i in sample:
        d, m0 = int(t["d"][i]), int(t["m0"][i])
        day = P["days"][d]
        r = raw[raw["day"] == day].set_index("hhmm")
        if setup == "A":
            last = MINS[m0 - 1 + shift]
            if last not in r.index or MINS[0] not in r.index:
                continue
            o = float(r.at[MINS[0], "open"])
            z = (float(r.at[last, "close"]) - o) / (P["soc"][d] * math.sqrt(m0 / NMIN))
            if not math.isclose(z, float(t["x"][i]), rel_tol=0, abs_tol=1e-9):
                raise D746Error(f"lag: z at {day} {MINS[m0]} is not from the bar before the entry")
            w = r[r.index < MINS[m0 + shift] if m0 + shift < NMIN else r.index <= MINS[-1]]
            w = w[w["volume"] > 0]
            vw = float((((w["high"] + w["low"] + w["close"]) / 3) * w["volume"]).sum() / w["volume"].sum())
            tg = float(round_target(np.array([t["entry"][i]]), np.array([vw]), np.array([t["F"][i]]), TICKS[P["root"]])[0])
            if not math.isclose(tg, float(t["tgt"][i]), rel_tol=0, abs_tol=1e-9):
                raise D746Error(f"lag: the VWAP target at {day} {MINS[m0]} reads a bar at or after the entry")
        else:
            j = ia[day] - 1 + shift
            prev = raw[raw["day"] == P["all_days"][j]]
            cp = float(prev.loc[prev["hhmm"] == prev["hhmm"].max(), "close"].iloc[0])
            if not math.isclose(cp, float(t["tgt"][i]), rel_tol=0, abs_tol=1e-9):
                raise D746Error(f"lag: B's C_prev at {day} is not the prior session's last close")


TICKS = {"ES": 0.25, "YM": 1.0}


def sign_audit() -> None:
    """A synthetic day: a short fade whose price falls to the target pays +; one that rises to the stop pays -."""
    H = np.full((1, NMIN), 101.0)
    L = np.full((1, NMIN), 99.0)
    Op = np.full((1, NMIN), 100.0)
    C = np.full((1, NMIN), 100.0)
    H[0, 40:], L[0, 40:], Op[0, 40:], C[0, 40:] = 96.0, 94.0, 95.0, 95.0
    P = {"H": H, "L": L, "Op": Op, "C": C}
    one = np.array([0])
    px, _, k = bracket(P, one, np.array([30]), np.array([-1.0]), np.array([100.0]), np.array([97.0]), np.array([103.0]), 0.25)
    if not (k[0] == 1 and -1 * (px[0] - 100.0) * 5.0 - 4.42 > 0):
        raise D746Error("sign: a short fade falling to its target did not pay")
    H[0, 40:], L[0, 40:], Op[0, 40:], C[0, 40:] = 106.0, 104.0, 105.0, 105.0
    px, _, k = bracket(P, one, np.array([30]), np.array([-1.0]), np.array([100.0]), np.array([97.0]), np.array([103.0]), 0.25)
    if not (k[0] == -1 and -1 * (px[0] - 100.0) * 5.0 < 0 and px[0] > 105.0):
        raise D746Error("sign: a short fade rising through its stop did not lose (open beyond the stop, plus a tick)")


# ================================================================================ the study
def other_lines() -> dict[str, pd.Series]:
    """Daily net of D737's in-sample twin (D735's YM k1.0 1 sigma_rem, via the recorder's d737_rows) and NQ F2 (D711's
    book, via the forward script's f2_rows), both on text-restricted in-sample bars."""
    import record_forward_nq_lines as REC
    import forward_f2_c1_ledgers as FW
    nq, ym, es = rth("NQ"), rth("YM"), rth("ES")
    rows, _ = REC.d737_rows(nq, ym, LO)
    d737 = rows[rows["status"] == "trade"].set_index("day")["net_usd"].astype(float)
    _VD, M = FW.f2_modules()
    f2 = FW.f2_rows(FW.L_from_bars(M, "NQ", nq[nq["day"] <= M.IN_END]), FW.L_from_bars(M, "ES", es[es["day"] <= M.IN_END]), LO)
    f2 = f2[f2["status"] == "trade"].set_index("session")["net_usd"].astype(float)
    return {"d737_twin": d737, "nq_f2": f2}


def cell(P: dict[str, Any], setup: str, thr: float, cl: dict[str, float], gst: np.ndarray, others: dict[str, pd.Series],
         workers: int) -> tuple[dict[str, Any], float]:
    t = setup_a(P, thr, cl["tick"]) if setup == "A" else setup_b(P, thr, cl["tick"])
    o = outcomes(P, t, cl)
    days = P["days"][t["d"]]
    dist_usd = t["dist"] * cl["usd_pt"]
    res: dict[str, Any] = {"triggered": t["triggered"], "skipped_vwap_not_favourable": t["skipped_vwap"]}
    res["E1"] = book(o["n1"], o["g1"], days, o["bars1"], cl["cost"], dist_usd)
    res["E1"]["exit_mix"] = {"target": float((o["kind1"] == 1).mean()), "stop": float((o["kind1"] == -1).mean()),
                             "close": float((o["kind1"] == 0).mean())}
    res["E2_hold_to_close"] = {"mean_gross": float(o["g2"].mean()), "mean_net": float((o["g2"] - cl["cost"]).mean()),
                               "t_gross_nw": nw_t(o["g2"])}
    res["E3_target_no_stop"] = {"mean_gross": float(o["g3"].mean()), "mean_net": float((o["g3"] - cl["cost"]).mean()),
                                "target_share": float((o["kind3"] == 1).mean()), "t_gross_nw": nw_t(o["g3"])}
    res["mirror_E1_gross"] = float(o["mirror_g1"].mean())
    if len(o["g1"]) and np.allclose(o["g1"], o["g2"]):
        raise D746Error("right quantity: E1 equals E2")
    # oracles
    n1 = o["n1"]
    take = FO.oracle_take(n1)
    res["O1_oracle"] = {"share_taken": float(take.mean()), "mean_net_taken": float(n1[take].mean()) if take.any() else None,
                        "total_net_taken": float(n1[take].sum()), "per_trade_over_all": float(n1[take].sum() / len(n1))}
    if len(n1) >= 20:
        curve = FO.partial_oracle_curve(n1, n1, RHOS, 0.5, N_DRAW, np.random.default_rng(SEED))
        res["O2_partial_oracle_keep_half"] = curve
        res["O2_rho_breakeven"] = next((c["rho"] for c in curve if c["mean_net_per_trade"] >= 0), None)
        res["O2_rho_2x_cost"] = next((c["rho"] for c in curve if c["mean_net_per_trade"] >= 2 * cl["cost"]), None)
        r05 = next(c for c in curve if abs(c["rho"] - 0.05) < 1e-12)
        res["O2_rho005_mean_net"] = r05["mean_net_per_trade"]
        kept_sd = float(np.std(n1, ddof=1))
        res["O2_rho005_sharpe_approx"] = float(r05["mean_net_per_trade"] / kept_sd * math.sqrt(res["E1"]["trades_per_year"] / 2)) if kept_sd > 0 else None
    res["O3_median_target_usd"] = float(np.median(dist_usd))
    res["O3_median_target_vs_2c"] = float(np.median(dist_usd) / (2 * cl["cost"]))
    # bins, hours, gamma
    xb = np.abs(t["x"])
    edges = (2.0, 2.5, 3.0, 4.0, np.inf) if setup == "A" else (0.25, 0.5, 1.0, 1.5, np.inf)
    res["by_x_bin"] = [{"bin": [lo, hi], "n": int(((xb >= lo) & (xb < hi)).sum()),
                        "mean_gross": float(o["g1"][(xb >= lo) & (xb < hi)].mean()) if ((xb >= lo) & (xb < hi)).any() else None}
                       for lo, hi in zip(edges[:-1], edges[1:])]
    hrs = np.array([MINS[m][:2] for m in t["m0"]])
    res["by_entry_hour"] = {h: {"n": int((hrs == h).sum()), "mean_gross": float(o["g1"][hrs == h].mean())} for h in sorted(set(hrs))}
    g = gst[t["d"]]
    res["by_gamma"] = {s: {"n": int((g == s).sum()), "mean_gross": float(o["g1"][g == s].mean()) if (g == s).any() else None}
                       for s in ("short", "long_low", "long_high", "none")}
    a, b_ = o["g1"][g == "long_high"], o["g1"][g == "short"]
    if len(a) > 2 and len(b_) > 2:
        se = math.sqrt(a.var(ddof=1) / len(a) + b_.var(ddof=1) / len(b_))
        res["gamma_contrast_long_high_minus_short"] = {"diff": float(a.mean() - b_.mean()), "welch_t": float((a.mean() - b_.mean()) / se)}
    # the component line: daily-net correlation with D737's twin and NQ F2
    daily = pd.Series(n1, index=days).groupby(level=0).sum().reindex(P["days"], fill_value=0.0)
    res["component_corr"] = {k: float(np.corrcoef(daily.to_numpy(), v.reindex(P["days"], fill_value=0.0).to_numpy())[0, 1])
                             for k, v in others.items()}
    # audits on this cell
    if len(t["d"]):
        smp = list(range(0, len(t["d"]), max(1, len(t["d"]) // 15)))
        lag_audit(P, setup, t, smp)
    # C2
    t0 = time.time()
    nul = null_all(P, setup, t, cl, workers=workers)
    nul = nul[np.isfinite(nul)]
    score = float(o["g1"].mean())
    p = float((nul >= score).mean())
    res["C2_timing_null"] = {"offsets": int(len(nul)), "score_mean_gross": score, "p50": float(np.median(nul)),
                             "p95": float(np.percentile(nul, 95)), "p": p, "seconds": round(time.time() - t0, 1)}
    return res, p


def readings(r: dict[str, Any], cost: float) -> dict[str, Any]:
    e1 = r["E1"]
    if e1.get("trades", 0) < 3:
        return {"reading": "NOTHING (too few trades)"}
    no_room = e1["mean_gross"] < 2 * cost and (r.get("O2_rho005_mean_net") is None or r["O2_rho005_mean_net"] <= 0)
    rev = e1["mean_gross"] > 0 and (e1["t_gross_nw"] or 0) >= 2 and e1["mean_gross"] > r["C2_timing_null"]["p95"]
    sh = max(x for x in (e1.get("sharpe_net") or -9, r.get("O2_rho005_sharpe_approx") or -9))
    pos = int(e1["positive_years"].split(" of ")[0])
    go = (rev and not no_room and r["holm_p"] <= 0.05 and sh >= 0.4 and pos >= 5
          and (e1["largest_year_share"] is not None and e1["largest_year_share"] < 0.5))
    return {"NO_ROOM": bool(no_room), "REVERSION": bool(rev),
            "reading": "NO ROOM" if no_room else ("REVERSION" if rev else "DRIFT / NOTHING"),
            "GO_to_design_with_the_principal": bool(go)}


def run() -> int:
    t0 = time.time()
    sign_audit()
    cls = costs()
    gex = gex_series()
    others = other_lines()
    out: dict[str, Any] = {"spec": SPEC.name, "window": [LO, HI], "seal": SEAL, "costs": cls, "cells": {}}
    ps: dict[str, float] = {}
    for root in ROOTS:
        P = panel(root, rth(root))
        gst = gex_state(gex, P["days"])
        out[f"{root}_days"] = int(len(P["days"]))
        out[f"{root}_gamma_days"] = {s: int((gst == s).sum()) for s in ("short", "long_low", "long_high", "none")}
        # chunk == whole on the first cell's null, before anything is scored
        if root == ROOTS[0]:
            t = setup_a(P, PRIMARY["A"], cls[root]["tick"])
            offs = list(range(EDGE, EDGE + 48))
            a1 = null_all(P, "A", t, cls[root], offs, workers=1)
            a2 = null_all(P, "A", t, cls[root], offs, workers=WORKERS)
            if not np.array_equal(a1, a2, equal_nan=True):
                raise D746Error("the threaded null differs from the serial null")
            out["chunk_equals_whole"] = True
        for setup, thrs in (("A", KS), ("B", GS)):
            for thr in thrs:
                key = f"{setup}_{root}_{thr:g}"
                res, p = cell(P, setup, thr, cls[root], gst, others, WORKERS)
                out["cells"][key] = res
                ps[key] = p
                e1 = res["E1"]
                print(f"[{key}] n {e1.get('trades')}, gross {e1.get('mean_gross', float('nan')):+.2f}, net "
                      f"{e1.get('mean_net', float('nan')):+.2f}, C2 p50/p95 {res['C2_timing_null']['p50']:+.2f}/"
                      f"{res['C2_timing_null']['p95']:+.2f}, p {p:.3f}, {res['C2_timing_null']['seconds']} s", flush=True)
    hp = holm(ps)
    for key, r in out["cells"].items():
        r["holm_p"] = hp[key]
        r["readings"] = readings(r, cls[key.split("_")[1]]["cost"])
    out["primary"] = {f"{s}_{r}_{PRIMARY[s]:g}": out["cells"][f"{s}_{r}_{PRIMARY[s]:g}"]["readings"] for s in ("A", "B") for r in ROOTS}
    out["runtime_min"] = round((time.time() - t0) / 60, 2)
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"primary": out["primary"], "runtime_min": out["runtime_min"]}, indent=1))
    return 0


# ================================================================================ self-test
def selftest() -> int:
    fails: list[str] = []
    try:
        sign_audit()
    except D746Error as e:
        fails.append(str(e))
    # round_target: near side
    if not np.allclose(round_target(np.array([100.0, 100.0]), np.array([101.3, 98.7]), np.array([1.0, -1.0]), 0.25), [101.25, 98.75]):
        fails.append("round_target")
    # holm
    h = holm({"a": 0.01, "b": 0.04, "c": 0.5})
    if not (math.isclose(h["a"], 0.03) and math.isclose(h["b"], 0.08) and math.isclose(h["c"], 0.5)):
        fails.append(f"holm {h}")
    # a real panel (in-sample ES 2023 only, text-restricted): the lag audit passes and its canary raises
    b = rth("ES")
    b = b[b["day"] >= "2022-06-01"]
    P = panel("ES", b)
    t = setup_a(P, 2.0, 0.25)
    smp = list(range(0, len(t["d"]), max(1, len(t["d"]) // 10)))
    try:
        lag_audit(P, "A", t, smp)
    except D746Error as e:
        fails.append(f"lag audit on real A: {e}")
    try:
        lag_audit(P, "A", t, smp, shift=1)
        fails.append("the A canary (reading the entry bar) did not raise")
    except D746Error:
        pass
    tb = setup_b(P, 0.5, 0.25)
    smb = list(range(0, len(tb["d"]), max(1, len(tb["d"]) // 10)))
    try:
        lag_audit(P, "B", tb, smb)
    except D746Error as e:
        fails.append(f"lag audit on real B: {e}")
    try:
        lag_audit(P, "B", tb, smb, shift=-1)
        fails.append("the B canary (two sessions back) did not raise")
    except D746Error:
        pass
    # chunk == whole on the null
    offs = list(range(EDGE, EDGE + 24))
    if not np.array_equal(null_all(P, "A", t, costs()["ES"], offs, 1), null_all(P, "A", t, costs()["ES"], offs, 6), equal_nan=True):
        fails.append("threaded null != serial null")
    if fails:
        print("SELFTEST FAILED:", fails)
        return 1
    print("SELFTEST OK: the sign audit in money (target pays, stop loses with the open beyond it and a tick); targets on "
          "the near tick; Holm; the lag audit passes on real ES bars (A's z and VWAP, B's prior close) and both canaries "
          "raise; the threaded timing null equals the serial one")
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
