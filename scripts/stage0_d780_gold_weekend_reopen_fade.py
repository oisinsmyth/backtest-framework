"""D780 Stage 0: gold's weekend reopen on MGC (D772's Lead 3).
Spec: docs/decisions/D780-STAGE-0-PRE-REG-fade-gold-s-weekend-reopen-on-mgc.md.

    python scripts/stage0_d780_gold_weekend_reopen_fade.py --selftest
    python scripts/stage0_d780_gold_weekend_reopen_fade.py --run

Bars: fut_opening_globex_1m_cl_ng_gc_si (root GC), one-minute, stamped at the bar's START ("the close of bar hh:mm"
is the price at hh:mm + 1 minute), each session the Globex span from the evening before on the session's front. A
session's evening bars carry the calendar date one to four days before it. Sessions 2015-12-01 .. 2023-12-31 are
loaded (asserted), Mondays from 2016-01-01 scored. The rotation is D777's; the trade statistics are D775's. Base L4's
book (for the component line and the slot-10 power) is D778's frame, unchanged.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d775_cpi_nfp_fade as D775  # noqa: E402
import stage0_d777_post_close_fade as D7  # noqa: E402

SPEC = REPO / "docs" / "decisions" / "D780-STAGE-0-PRE-REG-fade-gold-s-weekend-reopen-on-mgc.md"
OUT = REPO / "data" / "stage0_d780_gold_weekend_reopen_fade.json"
FILE = "fut_opening_globex_1m_cl_ng_gc_si.csv.gz"
LOAD_FROM, SCORE_FROM, SEAL = "2015-12-01", "2016-01-01", "2024-01-01"
MULT, COST = 10.0, 5.93                                           # MGC: $10 a point, $5.93 a round trip
EVE = ("18:59", "20:59")                                          # evening bars: dated 1-4 days before the session
DAYB = ("16:59", "02:59", "09:29", "10:59")
BARS = EVE + DAYB
Q, WIN, WIN_MIN = 0.8, 250, 120
VOL_N, VOL_MIN = 20, 12
VAULT = ("2024-01-01", "2026-09-18")
T_GATE, MIN_TRADES = 1.2816, 40
L4_COST = 3.76
AUDIT_N, SEED, WORKERS = 40, 780, 4


class D780Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D780Error(msg)


# ================================================================================ data
def keep_rows(ch: pd.DataFrame) -> pd.DataFrame:
    ch = ch[(ch["root"] == "GC") & (ch["session"] >= LOAD_FROM) & (ch["session"] < SEAL) & ch["hhmm"].isin(BARS)]
    lag = (pd.to_datetime(ch["session"]) - pd.to_datetime(ch["et"].str[:10])).dt.days
    eve = ch["hhmm"].isin(EVE)
    return ch[(eve & lag.between(1, 4)) | (~eve & (lag == 0))]


def load() -> pd.DataFrame:
    parts = [keep_rows(ch) for ch in pd.read_csv(D7.FIX / FILE, encoding="utf-8", chunksize=2_000_000,
                                                 usecols=["root", "session", "et", "hhmm", "contract", "close"])]
    d = pd.concat(parts, ignore_index=True)
    need(len(d) > 0 and bool((d["session"] < SEAL).all()) and bool((d["et"] < SEAL).all()),
         "seal: a GC row on or after 2024-01-01")
    return d


# ================================================================================ the frame
def frame(d: pd.DataFrame) -> pd.DataFrame:
    P = d.pivot_table(index="session", columns="hhmm", values="close", aggfunc="last").sort_index()
    K = d.pivot_table(index="session", columns="hhmm", values="contract", aggfunc="last").sort_index()
    for h in BARS:
        P[h] = P.get(h, np.nan)
        K[h] = K.get(h, None)
    F = pd.DataFrame(index=P.index)
    F["prev16"], F["prevK"] = P["16:59"].shift(1), K["16:59"].shift(1)
    F["ent"], F["entK"] = P["18:59"], K["18:59"]
    F["ex"], F["exK"] = P["10:59"], K["10:59"]
    F["p2059"], F["p0259"], F["p0929"] = P["20:59"], P["02:59"], P["09:29"]
    F["m_all"] = F["ent"] - F["prev16"]                             # every session's reopen move (the q80 gate's pool)
    thr = F["m_all"].abs().where(F["m_all"] != 0).rolling(WIN, min_periods=WIN_MIN).quantile(Q).shift(1)
    F["thr"] = thr
    F["monday"] = pd.to_datetime(F.index).weekday == 0
    F = F[F["monday"] & (F.index >= SCORE_FROM)].copy()
    F["m"] = F["m_all"]
    have = F[["prev16", "ent", "ex"]].notna().all(axis=1) & (F["m"] != 0)
    F["one_contract"] = (F["prevK"] == F["entK"]) & (F["exK"] == F["entK"])
    F["valid"] = have & F["one_contract"]
    F["valid_pair"] = have                                          # the pair's version: roll weekends kept
    F["side"] = -np.sign(F["m"])
    F["y"] = (F["ex"] - F["ent"]) * MULT                            # the unsigned outcome, $ per MGC
    F["gross"] = F["side"] * F["y"]
    F["gross_0929"] = F["side"] * (F["p0929"] - F["ent"]) * MULT
    F["leg_a"] = F["side"] * (F["p2059"] - F["ent"]) * MULT
    F["leg_b"] = F["side"] * (F["p0259"] - F["p2059"]) * MULT
    F["leg_c"] = F["side"] * (F["ex"] - F["p0259"]) * MULT
    F["gated"] = F["valid"] & (F["m"].abs() >= F["thr"])
    yv = F["y"].where(F["valid"])
    F["sigma"] = yv.dropna().rolling(VOL_N, min_periods=VOL_MIN).std().shift(1).reindex(F.index)
    F["va"] = F["gross"] / F["sigma"]
    F["year"] = F.index.str[:4]
    return F


# ================================================================================ statistics
def tstat(x: pd.Series) -> float:
    x = x.dropna()
    return float(x.mean() / x.std(ddof=1) * math.sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else float("nan")


def grp(T: pd.DataFrame, key: Any, col: str = "gross") -> dict[str, Any]:
    return {str(k): {"n": int(len(g)), "mean_gross": round(float(g[col].mean()), 2),
                     "mean_net": round(float(g[col].mean()) - COST, 2), "win": round(float((g[col] > 0).mean()), 3),
                     "va": round(float(g["va"].mean()), 3) if g["va"].notna().any() else None,
                     "t": round(tstat(g[col]), 2)} for k, g in T.groupby(key)}


def book(F: pd.DataFrame, sessions: pd.Index) -> tuple[dict[str, Any], pd.Series]:
    """Daily series over every GC session 2016-2023, keyed on the Monday the trade closes, zero elsewhere."""
    idx = sessions[(sessions >= SCORE_FROM) & (sessions < SEAL)]
    T = F[F["valid"]]
    s = pd.Series(0.0, index=idx)
    s.loc[T.index] = (T["gross"] - COST).to_numpy()
    sg = pd.Series(0.0, index=idx)
    sg.loc[T.index] = T["gross"].to_numpy()
    down = s[s < 0]
    eq = s.cumsum()
    return ({"sharpe_net": round(s.mean() / s.std() * math.sqrt(252), 2),
             "sortino_net": round(s.mean() / math.sqrt((down ** 2).sum() / len(s)) * math.sqrt(252), 2),
             "sharpe_gross": round(sg.mean() / sg.std() * math.sqrt(252), 2),
             "max_drawdown": round(float((eq.cummax() - eq).max()), 0), "total_net": round(float(s.sum()), 0),
             "exposure_share": round(float(len(T) / len(idx)), 3)}, s)


def gates(F: pd.DataFrame, workers: int) -> dict[str, Any]:
    T = F[F["valid"]]
    out: dict[str, Any] = {"stats": D775.trade_stats(T["gross"], COST)}
    out["N_rotation"] = D7.rot_summary(T["side"].to_numpy(dtype=float), T["y"].to_numpy(dtype=float), workers)
    yr = grp(T, T["year"])
    out["by_year"] = yr
    full = sorted(yr)
    need_years = math.ceil(0.75 * len(full))
    win_years = sum(yr[y]["win"] >= 0.5 for y in full)
    va_years = sum((yr[y]["va"] or 0) > 0 for y in full)
    hv = T.groupby(np.where(T["year"] <= "2019", "first", "second"))["va"].mean()
    y_i = win_years >= need_years
    y_ii = va_years >= need_years and hv.get("first", np.nan) >= 0.5 * hv.get("second", np.nan)
    net_by_year = {y: yr[y]["mean_net"] * yr[y]["n"] for y in yr}
    ranked = sorted(net_by_year, key=net_by_year.get)
    best2, best1 = ranked[-2:], ranked[-1]
    ex_best2 = float((T.loc[~T["year"].isin(best2), "gross"] - COST).sum())
    ex_best1 = float(T.loc[T["year"] != best1, "gross"].mean())
    k = max(1, int(round(0.01 * len(T))))
    trimmed = float(T["gross"].sort_values().iloc[k:-k].mean())
    st = out["stats"]
    g1 = st["mean_gross"] > 0 and st["t_gross"] >= 2
    n_ok = out["N_rotation"]["obs"] > out["N_rotation"]["p95"]
    g2 = st["mean_net"] > 0 and st["t_net"] >= 2 and ex_best2 > 0 and ex_best1 >= 2 * COST and trimmed >= 2 * COST
    out["gates"] = {"G1": bool(g1), "N": bool(n_ok),
                    "Y": {"pass": bool(y_i or y_ii), "full_years": full, "need": need_years, "i_win_years": int(win_years),
                          "ii_va_years": int(va_years), "va_first": round(float(hv.get("first", np.nan)), 3),
                          "va_second": round(float(hv.get("second", np.nan)), 3), "i": bool(y_i), "ii": bool(y_ii)},
                    "G2": {"pass": bool(g2), "t_net": st["t_net"], "best_two_years": best2, "net_ex_best2": round(ex_best2, 0),
                           "best_year": best1, "mean_gross_ex_best_year": round(ex_best1, 2),
                           "trimmed_gross": round(trimmed, 2), "bar_2x": round(2 * COST, 2)}}
    out["reading"] = ("NO EFFECT" if not g1 else "NOT ABOVE NULL" if not n_ok else
                      "CONCENTRATED" if not (y_i or y_ii) else "NO PRIZE" if not g2 else "SUPPORTED")
    return out


def power(mu: float, sd: float, n: float) -> float:
    """P(mean net > 0 and one-sided t >= 1.2816) at a true net mu, normal approximation; 0 below 40 trades."""
    if n < MIN_TRADES:
        return 0.0
    z = T_GATE - mu * math.sqrt(n) / sd
    return round(0.5 * math.erfc(z / math.sqrt(2)), 3)


def vault_power(gross: pd.Series, years: pd.Series | None, span: tuple[str, str]) -> tuple[dict[str, Any], float, float]:
    """The in-sample trade rate per calendar day carried to the vault window, and the per-trade sd."""
    days = (pd.Timestamp(span[1]) - pd.Timestamp(span[0])).days
    vdays = (pd.Timestamp(VAULT[1]) - pd.Timestamp(VAULT[0])).days
    n_v = len(gross) / days * vdays
    sd = float(gross.std(ddof=1))
    return {"in_sample_trades": int(len(gross)), "per_trade_sd": round(sd, 2), "vault_trades_est": round(n_v, 0)}, n_v, sd


def study(d: pd.DataFrame, workers: int = WORKERS, full: bool = True) -> dict[str, Any]:
    F = frame(d)
    need(bool((pd.to_datetime(F.index[F["valid"]]).weekday == 0).all()), "right quantity: a scored session is not a Monday")
    diff = F["valid_pair"] & ~F["valid"]
    need(bool((~F.loc[diff, "one_contract"]).all()), "right quantity: the primary differs from the pair's off a roll")
    need(int(F["valid"].sum()) > 2, "too few scored Mondays")
    out = gates(F, workers)
    if not full:
        return out
    audit(d, F)
    T = F[F["valid"]]
    out["counts"] = {"mondays": int(len(F)), "scored": int(len(T)), "roll_weekends_dropped": int(diff.sum()),
                     "missing_or_flat": int((~F["valid_pair"]).sum())}
    TP = F[F["valid_pair"]]
    out["pair_version_rolls_kept"] = D775.trade_stats(TP["gross"], COST)
    out["exit_0929"] = D775.trade_stats(T["gross_0929"].dropna(), COST)
    G = F[F["gated"]]
    out["gated_q80"] = D775.trade_stats(G["gross"], COST) if len(G) > 2 else None
    L = T.dropna(subset=["leg_a", "leg_b", "leg_c"])
    out["legs"] = {"n": int(len(L)),
                   "all": {k: round(float(L[k].mean()), 2) for k in ("leg_a", "leg_b", "leg_c")},
                   "t": {k: round(tstat(L[k]), 2) for k in ("leg_a", "leg_b", "leg_c")},
                   "ex2020": {k: round(float(L.loc[L["year"] != "2020", k].mean()), 2) for k in ("leg_a", "leg_b", "leg_c")},
                   "by_year": {y: {k: round(float(g[k].mean()), 2) for k in ("leg_a", "leg_b", "leg_c")}
                               for y, g in L.groupby("year")}}
    out["ex2020"] = D775.trade_stats(T.loc[T["year"] != "2020", "gross"], COST)
    out["sides"] = grp(T, np.where(T["m"] > 0, "fade a weekend rise (short)", "fade a weekend fall (long)"))
    out["abs_m_terciles"] = grp(T, pd.qcut(T["m"].abs().rank(method="first"), 3, labels=["low", "mid", "high"]))
    bk, daily = book(F, pd.Index(sorted(d["session"].unique())))
    out["book"] = bk
    out["drift"] = round(float(T["y"].mean()), 2)
    net = T["gross"] - COST
    out["top5"] = [[s, round(v, 2)] for s, v in net.nlargest(5).items()]
    out["bottom5"] = [[s, round(v, 2)] for s, v in net.nsmallest(5).items()]
    out["top5_share_of_total_net"] = round(float(net.nlargest(5).sum() / net.sum()), 3) if net.sum() > 0 else None
    out["_daily"] = daily
    out["_T"] = T
    return out


# ================================================================================ audits
def sign_audit(mirror: float = 1.0) -> None:
    """In money: a weekend rise (m > 0) followed by a fall to 11:00 pays the short fade."""
    m, ent, ex = 4.0, 1900.0, 1895.0
    need((-np.sign(m) * mirror) * (ex - ent) * MULT > 0, "sign audit: a faded weekend rise followed by a fall must pay")


def audit(d: pd.DataFrame, F: pd.DataFrame, n: int = AUDIT_N) -> None:
    """Second implementation: explicit loops over the raw rows for P, m, the contract check, the side and the fade.
    It never calls frame()."""
    close: dict[tuple[str, str], tuple[float, str]] = {}
    for r in d.itertuples(index=False):
        close[(r.session, r.hhmm)] = (float(r.close), r.contract)
    sessions = sorted(d["session"].unique())
    pos = {s: i for i, s in enumerate(sessions)}
    T = F[F["valid"]]
    pick = T.index[np.random.default_rng(SEED).choice(len(T), size=min(n, len(T)), replace=False)]
    for s in pick:
        prev = sessions[pos[s] - 1]
        p, pk = close[(prev, "16:59")]
        e, ek = close[(s, "18:59")]
        x, xk = close[(s, "10:59")]
        need(pk == ek == xk, f"lag audit: {s} is scored across two contracts")
        m = e - p
        need(abs(m - float(F.at[s, "m"])) < 1e-9, f"lag audit: m differs on {s}")
        side = -1.0 if m > 0 else 1.0
        need(side == float(F.at[s, "side"]), f"lag audit: the side differs on {s}")
        need(abs(side * (x - e) * MULT - float(F.at[s, "gross"])) < 1e-6, f"lag audit: the fade differs on {s}")
    for s in F.index[F["valid_pair"] & ~F["one_contract"]]:
        need(not bool(F.at[s, "valid"]), f"a roll weekend was scored: {s}")


# ================================================================================ run
def l4_base() -> tuple[pd.Series, pd.Series, tuple[str, str], pd.DataFrame]:
    """Base L4 (D778's base book, unchanged): its trades, its daily net book (keyed on the exit day), its valid span."""
    import stage0_d778_auction_fade_trend_filter as D8
    b = D8.load_bars()
    D = D8.frame(b, "RTY")
    B = D[D["base"]]
    need(len(B) == 280 and round(float(B["gross"].mean()), 2) == 15.84, "base L4 is not D778's base book")
    _, daily = D8.book_of(D, "base", L4_COST)
    V = D.index[D["cvalid"]]
    return B["gross"], daily.groupby(level=0).sum(), (V.min(), V.max()), b


def run() -> int:
    t0 = time.time()
    sign_audit()
    try:
        sign_audit(-1.0)
    except D780Error:
        pass
    else:
        raise D780Error("the sign audit did not raise on a mirrored book")
    d = load()
    r = study(d)
    daily = r.pop("_daily")
    T = r.pop("_T")
    res: dict[str, Any] = {"spec": SPEC.name, "window": [SCORE_FROM, "2023-12-31"], "root": "GC (MGC terms)", **r}
    # the slot-10 power, L3 beside base L4
    l4g, l4d, l4span, b = l4_base()
    st = r["stats"]
    span3 = (T.index.min(), T.index.max())
    p3, n3, sd3 = vault_power(T["gross"], T["year"], span3)
    best = r["gates"]["G2"]["best_year"]
    mu3 = {"in_sample_net": st["mean_net"], "net_without_best_year": round(r["gates"]["G2"]["mean_gross_ex_best_year"] - COST, 2),
           "zero": 0.0}
    p3["pass_probability"] = {k: power(v, sd3, n3) for k, v in mu3.items()}
    p3["edges"] = mu3
    p4, n4, sd4 = vault_power(l4g, None, l4span)
    l4y = pd.Series(l4g.values, index=l4g.index).groupby(l4g.index.str[:4])
    l4_net_year = (l4y.sum() - L4_COST * l4y.count())
    l4_best = l4_net_year.idxmax()
    mu4 = {"in_sample_net": round(float(l4g.mean()) - L4_COST, 2),
           "net_without_best_year": round(float(l4g[l4g.index.str[:4] != l4_best].mean()) - L4_COST, 2), "zero": 0.0}
    p4["pass_probability"] = {k: power(v, sd4, n4) for k, v in mu4.items()}
    p4["edges"] = mu4
    p4["best_year"] = l4_best
    p3["best_year"] = best
    res["slot10_power"] = {"gate": f">= {MIN_TRADES} trades, mean net > 0 and one-sided t >= {T_GATE} (normal approx; "
                                   "D776's rotation-p95 gate not modelled)", "vault": list(VAULT), "L3": p3, "L4_base": p4}
    # the component line
    d775 = D7.d775_daily(b)
    _, d777 = D7.daily_book(D7.panel(b, "NQ"), 4.07)
    comp = {"l4_base": round(float(pd.concat([daily, l4d], axis=1).fillna(0).corr().iloc[0, 1]), 3),
            "d775": round(float(pd.concat([daily, d775], axis=1).fillna(0).corr().iloc[0, 1]), 3),
            "d777_mnq": round(float(pd.concat([daily, d777.groupby(level=0).sum()], axis=1).fillna(0).corr().iloc[0, 1]), 3)}
    if D7.LINES.exists():
        lines = pd.read_csv(D7.LINES, index_col=0, encoding="utf-8")
        jj = lines.join(daily.rename("d780"), how="inner")
        comp.update({c: round(float(jj["d780"].corr(jj[c])), 3) for c in lines.columns})
    res["component_rho"] = comp
    res["GO"] = bool(r["reading"] == "SUPPORTED")
    res["wall_s"] = round(time.time() - t0, 1)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, default=str)
    print("L3 | n", st["n"], "gross", st["mean_gross"], "t", st["t_gross"], "net t", st["t_net"], "| N", r["N_rotation"],
          "| Y", r["gates"]["Y"], "| G2", r["gates"]["G2"], "|", r["reading"], "GO", res["GO"], flush=True)
    print("slot10", json.dumps(res["slot10_power"]))
    print("rho", comp, f"{res['wall_s']}s ->", OUT.relative_to(REPO))
    return 0


# ================================================================================ self-test
def _synthetic(rng: np.random.Generator, kappa: float, roll_monday: int = 30) -> pd.DataFrame:
    """GC-like sessions: every session's reopen move m (prior 16:59 -> 18:59) is followed by kappa * (-m) to 10:59
    (kappa > 0 reverts). Mondays' evening bars sit on the Sunday; one Monday sits on a new contract (a roll weekend)."""
    sessions = [x.strftime("%Y-%m-%d") for x in pd.bdate_range("2015-12-01", "2018-12-31")]
    rows, last, mondays = [], 1200.0, 0
    for s in sessions:
        ts = pd.Timestamp(s)
        k = "GCG6"
        if ts.weekday() == 0:
            mondays += 1
            if mondays == roll_monday:
                k = "GCJ6"
        eve_day = (ts - pd.Timedelta(days=1)).strftime("%Y-%m-%d")      # a Monday's evening is the Sunday
        m = rng.normal(0, 4)
        ent = last + m
        p2059 = ent - 0.3 * kappa * m + rng.normal(0, 0.5)
        p0259 = ent - 0.6 * kappa * m + rng.normal(0, 0.5)
        ex = ent - kappa * m + rng.normal(0, 1.0)
        p0929 = ex + rng.normal(0, 0.3)
        close = ex + rng.normal(0, 2)
        for h, p, day in (("18:59", ent, eve_day), ("20:59", p2059, eve_day), ("02:59", p0259, s), ("09:29", p0929, s),
                          ("10:59", ex, s), ("16:59", close, s)):
            rows.append({"root": "GC", "session": s, "et": f"{day} {h}", "hhmm": h, "contract": k, "close": round(p, 1)})
        last = close
    return pd.DataFrame(rows)


def selftest() -> int:
    sign_audit()
    try:
        sign_audit(-1.0)
    except D780Error:
        pass
    else:
        raise D780Error("the sign audit did not raise on a mirrored book")
    rng = np.random.default_rng(SEED)
    # 1) a planted reversion passes G1 and N; a planted continuation fails G1
    d = keep_rows(_synthetic(rng, 0.8))
    r = study(d, workers=1, full=False)
    need(r["gates"]["G1"] and r["gates"]["N"], f"a planted reversion must pass G1 and N: {r['stats']} {r['N_rotation']}")
    dc = keep_rows(_synthetic(rng, -0.8))
    rc = study(dc, workers=1, full=False)
    need(not rc["gates"]["G1"], f"a planted continuation must fail G1: {rc['stats']}")
    # 2) the roll weekend is dropped (and kept in the pair's version)
    F = frame(d)
    roll = F.index[F["valid_pair"] & ~F["one_contract"]]
    need(len(roll) >= 1 and not F.loc[roll, "valid"].any(), "the roll weekend was not dropped")
    # 3) the evening bars: a Monday's 18:59 comes from the Sunday; a row dated the session itself is dropped
    bad = d[(d["hhmm"] == "18:59")].head(1).assign(et=lambda x: x["session"] + " 18:59")
    need(len(keep_rows(bad)) == 0, "an 18:59 row dated the session itself was kept")
    # 4) the second implementation agrees, and raises on a broken side
    audit(d, F, n=10_000)
    Fx = F.copy()
    s0 = Fx.index[Fx["valid"]][5]
    Fx.loc[s0, "side"] = -Fx.loc[s0, "side"]
    try:
        audit(d, Fx, n=10_000)
    except D780Error:
        pass
    else:
        raise D780Error("the second implementation did not raise on a broken side")
    # 5) chunk == whole for the rotation (tie-heavy)
    s = rng.integers(-1, 2, size=401).astype(float)
    f = rng.integers(-3, 4, size=401).astype(float)
    need(bool(np.array_equal(D7.rotation(s, f, 1), D7.rotation(s, f, 4))), "chunk != whole")
    # 6) the power function: monotone in the edge, zero below 40 trades
    need(power(10, 100, 140) > power(0, 100, 140) > 0 and power(10, 100, 30) == 0.0, "the power function")
    # 7) the whole study end to end
    full = study(d, workers=1, full=True)
    need(full["reading"] in {"NO EFFECT", "NOT ABOVE NULL", "CONCENTRATED", "NO PRIZE", "SUPPORTED"}, "the whole study")
    print("selftest OK: a planted reversion passes G1 and N, a continuation fails G1; the roll weekend is dropped; "
          "evening bars come from the day before; the second implementation agrees and raises on a broken side; "
          f"chunk == whole; the power function; the whole study runs (synthetic reading {full['reading']})")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args(argv)
    return selftest() if a.selftest else run()


if __name__ == "__main__":
    sys.exit(main())
