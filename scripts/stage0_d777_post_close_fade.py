"""D777 Stage 0: fade the index futures' post-cash-close hour (16:00 -> 17:00) from the 18:05 reopen to 10:00.
Spec: docs/decisions/D777-STAGE-0-PRE-REG-fade-the-post-close-hour-of-the-index-futures.md.

    python scripts/stage0_d777_post_close_fade.py --selftest
    python scripts/stage0_d777_post_close_fade.py --run

Bars: fut_opening_globex_1m (ES, NQ) and fut_opening_globex_1m_ym_rty (YM, RTY), one-minute, stamped at the bar's
START, each session the Globex span from the evening before (18:00) to 16:59 ET on the session's front. "The close of
bar hh:mm" is the price at hh:mm + 1 minute. Sessions 2016-01-01 .. 2023-12-31 only (asserted); a session's S+1 must
itself be in that range, so nothing on or after 2024-01-01 is read.
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
import stage0_d775_cpi_nfp_fade as D775  # noqa: E402

MAIN = Path("C:/Users/O/Desktop/Projects/Backtest Framework")
FIX = MAIN / "data" / "fixtures"
LINES = REPO / "temp" / "d755_other_lines.csv"
SPEC = REPO / "docs" / "decisions" / "D777-STAGE-0-PRE-REG-fade-the-post-close-hour-of-the-index-futures.md"
OUT = REPO / "data" / "stage0_d777_post_close_fade.json"
START, SEAL = "2016-01-01", "2024-01-01"
ROOTS = {"NQ": ("fut_opening_globex_1m.csv.gz", 2.0, 4.07), "ES": ("fut_opening_globex_1m.csv.gz", 5.0, 4.42),
         "RTY": ("fut_opening_globex_1m_ym_rty.csv.gz", 5.0, 3.76), "YM": ("fut_opening_globex_1m_ym_rty.csv.gz", 0.5, 3.80)}
PRIMARY, CONFIRMABLE = "NQ", ("RTY", "YM")
# S's bars: 09:29 (the 09:30 price), 12:59, 15:59 (16:00), 16:58/16:59 (17:00); S+1's: 18:04 (18:05), 19:59 (20:00),
# 09:29 (09:30), 09:59 (10:00), 10:59 (11:00); D775's bars for the overlap book: 08:29, 08:34, 11:00
BARS = ["08:29", "08:34", "09:29", "09:59", "10:59", "11:00", "12:59", "15:59", "16:58", "16:59", "18:04", "19:59"]
Q, Q_HI, WIN, WIN_MIN = 0.8, 0.9, 250, 120
VOL_N, VOL_MIN, MAX_GAP = 60, 40, 4
REGIME_1, REGIME_2 = "2020-10-26", "2021-06-25"            # settlement 16:15 -> 16:00; the 16:15-16:30 halt ends
WORKERS, SEED, AUDIT_N = 4, 777, 40


class D777Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D777Error(msg)


# ================================================================================ data
def _load_file(args: tuple[str, tuple[str, ...]]) -> pd.DataFrame:
    fn, roots = args
    parts = []
    for ch in pd.read_csv(FIX / fn, encoding="utf-8", chunksize=2_000_000,
                          usecols=["root", "session", "et", "hhmm", "contract", "close"]):
        ch = ch[ch["root"].isin(roots) & (ch["session"] >= START) & (ch["session"] < SEAL) & ch["hhmm"].isin(BARS)]
        lag = (pd.to_datetime(ch["session"]) - pd.to_datetime(ch["et"].str[:10])).dt.days
        parts.append(ch[(lag >= 0) & (lag <= MAX_GAP)])       # drop stray old-dated rows
    d = pd.concat(parts, ignore_index=True)
    need(bool((d["session"] < SEAL).all()), "seal: a session on or after 2024-01-01")
    return d


def load_bars() -> pd.DataFrame:
    jobs: dict[str, list[str]] = {}
    for r, (fn, _, _) in ROOTS.items():
        jobs.setdefault(fn, []).append(r)
    with ProcessPoolExecutor(max_workers=len(jobs)) as ex:
        frames = list(ex.map(_load_file, [(fn, tuple(rs)) for fn, rs in jobs.items()]))
    return pd.concat(frames, ignore_index=True)


# ================================================================================ the panel
def panel(b: pd.DataFrame, root: str) -> pd.DataFrame:
    """One row per session S: the signal from S's bars and the outcome from S+1's."""
    _, mult, _ = ROOTS[root]
    g = b[b["root"] == root]
    P = g.pivot_table(index="session", columns="hhmm", values="close", aggfunc="last").sort_index()
    for c in BARS:
        if c not in P.columns:
            P[c] = np.nan
    P["p17"] = P["16:59"].fillna(P["16:58"])
    D = pd.DataFrame(index=P.index)
    D["m"] = P["p17"] - P["15:59"]
    D["day"] = P["15:59"] - P["09:29"]
    D["aft"] = P["15:59"] - P["12:59"]
    nxt = P.shift(-1)
    nxt_day = pd.Series(P.index, index=P.index).shift(-1)
    gap = (pd.to_datetime(nxt_day) - pd.to_datetime(pd.Series(P.index, index=P.index))).dt.days
    D["s1"] = nxt_day
    D["gap"] = gap
    ok_gap = gap <= MAX_GAP
    D["ent"] = nxt["18:04"].where(ok_gap)
    D["ex"] = nxt["09:59"].where(ok_gap)
    D["y"] = (D["ex"] - D["ent"]) * mult                      # the outcome in $ at one micro (unsigned)
    D["legB"] = (nxt["10:59"] - nxt["09:29"]).where(ok_gap) * mult
    D["over"] = (nxt["09:29"] - D["ent"]) * mult
    D["open"] = (D["ex"] - nxt["09:29"].where(ok_gap)) * mult
    D["pm"] = (nxt["19:59"] - nxt["18:04"]).where(ok_gap)     # the cash-shut placebo move (18:05 -> 20:00)
    D["py"] = (D["ex"] - nxt["19:59"].where(ok_gap)) * mult
    absm = D["m"].abs().where(D["m"] != 0)
    D["thr"] = absm.shift(1).rolling(WIN, min_periods=WIN_MIN).quantile(Q)
    D["thr90"] = absm.shift(1).rolling(WIN, min_periods=WIN_MIN).quantile(Q_HI)
    D["side"] = -np.sign(D["m"])
    D["valid"] = D["m"].notna() & (D["m"] != 0) & D["y"].notna() & D["thr"].notna()
    D["gate"] = D["valid"] & (absm >= D["thr"])
    D["gate90"] = D["valid"] & (absm >= D["thr90"])
    D["gross"] = D["side"] * D["y"]
    D["sigma"] = D["y"].where(D["y"].notna()).shift(1).rolling(VOL_N, min_periods=VOL_MIN).std()
    D["va"] = D["gross"] / D["sigma"]
    D["year"] = D.index.str[:4]
    D["wd"] = pd.to_datetime(D.index).weekday
    pabs = D["pm"].abs().where(D["pm"] != 0)
    D["pthr"] = pabs.shift(1).rolling(WIN, min_periods=WIN_MIN).quantile(Q)
    D["pgate"] = D["pm"].notna() & D["py"].notna() & (pabs >= D["pthr"])
    D["pgross"] = -np.sign(D["pm"]) * D["py"]
    return D


def counts(D: pd.DataFrame) -> dict[str, int]:
    c = {"sessions": int(len(D)),
         "no_next_session_or_gap": int((D["s1"].isna() | (D["gap"] > MAX_GAP)).sum()),
         "missing_bar": 0, "zero_move": 0, "warm_up": 0, "gated_out": 0, "traded": int(D["gate"].sum())}
    rest = D[D["s1"].notna() & (D["gap"] <= MAX_GAP)]
    c["missing_bar"] = int((rest["m"].isna() | rest["y"].isna()).sum())
    r2 = rest[rest["m"].notna() & rest["y"].notna()]
    c["zero_move"] = int((r2["m"] == 0).sum())
    r3 = r2[r2["m"] != 0]
    c["warm_up"] = int(r3["thr"].isna().sum())
    c["gated_out"] = int((r3["thr"].notna() & ~r3["gate"]).sum())
    need(c["sessions"] == sum(v for k, v in c.items() if k != "sessions"), f"right quantity: read != the parts {c}")
    return c


# ================================================================================ nulls, regression
def _rot_chunk(args: tuple[np.ndarray, np.ndarray, list[int]]) -> np.ndarray:
    s, f, ks = args
    n = int((s != 0).sum())
    return np.array([float(np.dot(np.roll(s, k), f)) / n for k in ks])


def rotation(s: np.ndarray, f: np.ndarray, workers: int = 1) -> np.ndarray:
    """Mean P&L of the signal s (side x gate, 0 when not traded) shifted circularly by k against the outcome f, for
    every k = 0 .. n-1; row 0 is the observed."""
    ks = list(range(len(f)))
    if workers == 1:
        return _rot_chunk((s, f, ks))
    parts = [ks[i::workers] for i in range(workers)]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        outs = list(ex.map(_rot_chunk, [(s, f, p) for p in parts]))
    res = np.empty(len(ks))
    for i, o in enumerate(outs):
        res[i::workers] = o
    return res


def rot_summary(s: np.ndarray, f: np.ndarray, workers: int) -> dict[str, Any]:
    r = rotation(s, f, workers)
    obs = r[0]
    need(abs(obs - float(np.dot(s, f)) / int((s != 0).sum())) < 1e-9, "right quantity: rotation offset 0 != observed")
    d = r[1:]
    return {"obs": round(float(obs), 2), "p50": round(float(np.percentile(d, 50)), 2),
            "p95": round(float(np.percentile(d, 95)), 2), "rank": round(float((d < obs).mean()), 4), "n": int(len(d))}


def ols_hc1(y: np.ndarray, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    XtX_inv = np.linalg.inv(X.T @ X)
    b = XtX_inv @ X.T @ y
    e = y - X @ b
    n, k = X.shape
    meat = (X * e[:, None] ** 2).T @ X
    V = XtX_inv @ meat @ XtX_inv * n / (n - k)
    return b, b / np.sqrt(np.diag(V))


def mechanism(D: pd.DataFrame, mult: float) -> dict[str, Any]:
    R = D[D["valid"] & D["day"].notna() & D["aft"].notna()]
    y = R["y"].to_numpy() / mult
    X = np.column_stack([np.ones(len(R)), R["m"].to_numpy(), R["day"].to_numpy(), R["aft"].to_numpy()])
    b, t = ols_hc1(y, X)
    return {"n": int(len(R)), "b_m": round(float(b[1]), 4), "t_m": round(float(t[1]), 2), "b_day": round(float(b[2]), 4),
            "t_day": round(float(t[2]), 2), "b_aft": round(float(b[3]), 4), "t_aft": round(float(t[3]), 2)}


# ================================================================================ statistics
def tstat(x: pd.Series) -> float:
    x = x.dropna()
    return float(x.mean() / x.std(ddof=1) * math.sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else float("nan")


def grp(T: pd.DataFrame, key: Any, cost: float) -> dict[str, Any]:
    return {str(k): {"n": int(len(g)), "mean_gross": round(g["gross"].mean(), 2), "mean_net": round(g["gross"].mean() - cost, 2),
                     "win": round(float((g["gross"] > 0).mean()), 3), "va": round(float(g["va"].mean()), 3),
                     "t": round(tstat(g["gross"]), 2)} for k, g in T.groupby(key)}


def daily_book(D: pd.DataFrame, cost: float) -> tuple[dict[str, Any], pd.Series]:
    """Daily series over every valid session, keyed on S+1 (the exit day), zero on untraded days."""
    V = D[D["valid"]]
    s = pd.Series(0.0, index=V["s1"].to_numpy())
    T = V[V["gate"]]
    s.loc[T["s1"].to_numpy()] = (T["gross"] - cost).to_numpy()
    down = s[s < 0]
    eq = s.cumsum()
    sg = pd.Series(0.0, index=V["s1"].to_numpy())
    sg.loc[T["s1"].to_numpy()] = T["gross"].to_numpy()
    return ({"sharpe_net": round(s.mean() / s.std() * math.sqrt(252), 2),
             "sortino_net": round(s.mean() / math.sqrt((down ** 2).sum() / len(s)) * math.sqrt(252), 2),
             "sharpe_gross": round(sg.mean() / sg.std() * math.sqrt(252), 2),
             "max_drawdown": round(float((eq.cummax() - eq).max()), 0), "total_net": round(float(s.sum()), 0),
             "exposure_share": round(float(len(T) / len(V)), 3)}, s)


# ================================================================================ audits
def sign_audit(mirror: float = 1.0) -> None:
    """In money: an up post-close move (m > 0) followed by a fall overnight pays the fade."""
    m, ent, ex = 10.0, 15000.0, 14980.0
    need((-np.sign(m) * mirror) * (ex - ent) * 2.0 > 0, "sign audit: a faded up-move followed by a fall must pay")


def audit(b: pd.DataFrame, root: str, D: pd.DataFrame, n: int = AUDIT_N) -> None:
    """Second implementation: explicit loops over the raw rows (never the pivot) for sampled trades, and the gate's
    threshold from an explicit list of prior |m|."""
    _, mult, _ = ROOTS[root]
    raw = b[b["root"] == root]
    T = D[D["gate"]]
    pick = T.index[np.random.default_rng(SEED).choice(len(T), size=min(n, len(T)), replace=False)]
    sess = list(D.index)
    absm_hist = D["m"].abs().where(D["m"] != 0)
    for S in pick:
        px: dict[tuple[str, str], float] = {}
        for r in raw[raw["session"].isin([S, T.at[S, "s1"]])].itertuples(index=False):
            px[(r.session, r.hhmm)] = float(r.close)
        p17 = px.get((S, "16:59"), px.get((S, "16:58")))
        m = p17 - px[(S, "15:59")]
        side = -1.0 if m > 0 else 1.0
        g = side * (px[(T.at[S, "s1"], "09:59")] - px[(T.at[S, "s1"], "18:04")]) * mult
        need(abs(g - float(T.at[S, "gross"])) < 1e-9, f"lag audit: the fade differs on {S}")
        i = sess.index(S)
        prior = [v for v in absm_hist.iloc[max(0, i - WIN):i].tolist() if v == v]
        thr = float(np.quantile(prior, Q)) if len(prior) >= WIN_MIN else float("nan")
        need(thr == thr and abs(m) >= thr, f"lag audit: the gate differs on {S}")


# ================================================================================ the study
def study(b: pd.DataFrame, root: str, workers: int = WORKERS) -> dict[str, Any]:
    _, mult, cost = ROOTS[root]
    D = panel(b, root)
    c = counts(D)
    audit(b, root, D)
    V = D[D["valid"]]
    T = V[V["gate"]]
    s = (V["side"] * V["gate"]).to_numpy(dtype=float)
    f = V["y"].to_numpy()
    need(not np.array_equal(V["gross"].to_numpy(), T["gross"].reindex(V.index).fillna(0).to_numpy()) or len(T) == len(V),
         "right quantity: the gated book equals the ungated one")
    out: dict[str, Any] = {"counts": c, "primary": D775.trade_stats(T["gross"], cost)}
    out["N_rotation"] = rot_summary(s, f, workers)
    out["M"] = mechanism(D, mult)
    yr = grp(T, T["year"], cost)
    out["by_year"] = yr
    full = sorted(yr)[1:]                                       # the first year with trades is a warm-up year
    need_years = math.ceil(0.75 * len(full))
    win_years = sum(yr[y]["win"] >= 0.5 for y in full)
    va_years = sum(yr[y]["va"] > 0 for y in full)
    half = np.where(T["year"] <= "2019", "first", "second")
    hv = T.groupby(half)["va"].mean()
    y_i = win_years >= need_years
    y_ii = va_years >= need_years and hv.get("first", np.nan) >= 0.5 * hv.get("second", np.nan)
    net_by_year = {y: yr[y]["mean_net"] * yr[y]["n"] for y in yr}
    best2 = sorted(net_by_year, key=net_by_year.get)[-2:]
    ex_best2 = float((T.loc[~T["year"].isin(best2), "gross"] - cost).sum())
    ex22 = float(T.loc[T["year"] != "2022", "gross"].mean())
    k = max(1, int(round(0.01 * len(T))))
    srt = T["gross"].sort_values()
    trimmed = float(srt.iloc[k:-k].mean())
    p = out["primary"]
    g1 = p["mean_gross"] > 0 and p["t_gross"] >= 2
    n_ok = out["N_rotation"]["obs"] > out["N_rotation"]["p95"]
    m_ok = out["M"]["b_m"] < 0 and out["M"]["t_m"] <= -2
    g2 = p["mean_net"] > 0 and p["t_net"] >= 2 and ex_best2 > 0 and ex22 >= 2 * cost and trimmed >= 2 * cost
    out["gates"] = {"G1": bool(g1), "N": bool(n_ok), "M": bool(m_ok),
                    "Y": {"pass": bool(y_i or y_ii), "full_years": full, "need": need_years, "i_win_years": int(win_years),
                          "ii_va_years": int(va_years), "va_first_half": round(float(hv.get("first", np.nan)), 3),
                          "va_second_half": round(float(hv.get("second", np.nan)), 3), "i": bool(y_i), "ii": bool(y_ii)},
                    "G2": {"pass": bool(g2), "best_two_years": best2, "net_ex_best2": round(ex_best2, 0),
                           "mean_gross_ex2022": round(ex22, 2), "trimmed_gross": round(trimmed, 2), "bar_2x": round(2 * cost, 2)}}
    out["reading"] = ("NO EFFECT" if not g1 else "NOT ABOVE NULL" if not n_ok else "NO MECHANISM" if not m_ok else
                      "CONCENTRATED" if not (y_i or y_ii) else "NO PRIZE" if not g2 else "SUPPORTED")
    # ---- reported
    out["halves"] = grp(T, half, cost)
    out["by_sign"] = grp(T, np.where(T["m"] > 0, "up", "down"), cost)
    out["by_abs_m_tercile"] = grp(T, pd.qcut(T["m"].abs().rank(method="first"), 3, labels=["low", "mid", "high"]), cost)
    out["weekend_vs_weekday"] = grp(T, np.where(T["gap"] > 1, "weekend/holiday", "weekday"), cost)
    out["by_weekday"] = grp(T, T["wd"].map(dict(enumerate(["Mon", "Tue", "Wed", "Thu", "Fri"]))), cost)
    out["regimes"] = grp(T, np.where(T.index < REGIME_1, "a_settle_1615_halt", np.where(T.index <= REGIME_2,
                                                                                       "b_settle_1600_halt", "c_no_halt")), cost)
    lb = (T["side"] * T["legB"] / 1).dropna()
    sB = (V["side"] * V["gate"]).where(V["legB"].notna()).dropna()
    fB = V.loc[sB.index, "legB"].to_numpy()
    out["legB_0930_1100"] = {"mean": round(lb.mean(), 2), "t": round(tstat(lb), 2), "n": int(len(lb)),
                             "rotation": rot_summary(sB.to_numpy(dtype=float), fB, workers)}
    ov, op = (T["side"] * T["over"]).dropna(), (T["side"] * T["open"]).dropna()
    out["hold_split"] = {"overnight_1805_0930": {"mean": round(ov.mean(), 2), "t": round(tstat(ov), 2)},
                         "open_0930_1000": {"mean": round(op.mean(), 2), "t": round(tstat(op), 2)}}
    T90 = V[V["gate90"]]
    s90 = (V["side"] * V["gate90"]).to_numpy(dtype=float)
    out["q90"] = {"n": int(len(T90)), "mean_gross": round(T90["gross"].mean(), 2), "t": round(tstat(T90["gross"]), 2),
                  "rotation": rot_summary(s90, f, workers)}
    PV = D[D["pgate"]]
    out["placebo_1805_2000"] = {"n": int(len(PV)), "mean_gross": round(PV["pgross"].mean(), 2), "t": round(tstat(PV["pgross"]), 2)}
    bk, daily = daily_book(D, cost)
    out["book"] = bk
    net = T["gross"] - cost
    out["top5"] = [[d, round(v, 2)] for d, v in net.nlargest(5).items()]
    out["bottom5"] = [[d, round(v, 2)] for d, v in net.nsmallest(5).items()]
    out["_daily"] = daily
    out["_trades_s1"] = T["s1"].tolist()
    return out


def d775_daily(b: pd.DataFrame) -> pd.Series:
    """D775's MNQ book, rebuilt from these bars with D775's own functions (keyed on the release day)."""
    S = D775.sessions(b[b["root"] == "NQ"], "NQ")
    U, _ = D775.classify(S, D775.release_days())
    R = U[U["is_rel"]]
    need(len(R) == 186 and round(float(R["gross"].mean()), 2) == 34.88, "D775's book is not reproduced from these bars")
    s = pd.Series(0.0, index=U.index)
    s[R.index] = (R["gross"] - 4.07).to_numpy()
    return s


def run() -> int:
    t0 = time.time()
    sign_audit()
    try:
        sign_audit(-1.0)
    except D777Error:
        pass
    else:
        raise D777Error("the sign audit did not raise on a mirrored book")
    b = load_bars()
    res: dict[str, Any] = {"spec": SPEC.name, "window": [START, "2023-12-31"], "q": Q}
    dailies = {}
    for root in ROOTS:
        r = study(b, root)
        dailies[root] = r.pop("_daily")
        r.pop("_trades_s1")
        res[root] = r
        print(root, r["counts"], "| mean", r["primary"]["mean_gross"], "t", r["primary"]["t_gross"], "| N",
              r["N_rotation"], "| M", r["M"]["b_m"], r["M"]["t_m"], "|", r["reading"], flush=True)
    conf = [rt for rt in CONFIRMABLE if res[rt]["gates"]["G1"] and res[rt]["gates"]["N"] and res[rt]["gates"]["M"]]
    res["GO"] = bool(res[PRIMARY]["reading"] == "SUPPORTED" and conf)
    res["confirmable_roots_passing_G1_N_M"] = conf
    # the component line: D775 and the vault lines
    d5 = d775_daily(b)
    nq = dailies["NQ"].groupby(level=0).sum()
    j = pd.concat([nq.rename("d777"), d5.rename("d775")], axis=1).fillna(0.0)
    res["rho_with_d775_daily"] = round(float(j["d777"].corr(j["d775"])), 3)
    rel_days = set(D775.release_days())
    res["nights_before_a_d775_release"] = int(sum(d in rel_days for d in nq[nq != 0].index))
    if LINES.exists():
        lines = pd.read_csv(LINES, index_col=0, encoding="utf-8")
        jj = lines.join(nq.rename("d777"), how="inner")
        res["rho_with_lines"] = {c: round(float(jj["d777"].corr(jj[c])), 3) for c in lines.columns}
        res["rho_days"] = int(len(jj))
    res["reading_primary"] = res[PRIMARY]["reading"]
    res["wall_s"] = round(time.time() - t0, 1)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, default=str)
    print("PRIMARY", res["reading_primary"], "GO", res["GO"], "confirmable", conf, f"{res['wall_s']}s ->", OUT.relative_to(REPO))
    return 0


# ================================================================================ self-test
def _synthetic(root: str, sessions: list[str], effect: float, rng: np.random.Generator) -> pd.DataFrame:
    """Random-walk bars per session; S+1's 18:04 -> 09:59 move is -effect x S's post-close move."""
    rows, prev_m = [], 0.0
    for d in sessions:
        base = 15000.0 + rng.normal(0, 20)
        c = {}
        for h in BARS:
            base += rng.normal(0, 3)
            c[h] = base
        c["09:59"] = c["18:04"] - effect * prev_m + rng.normal(0, 2)
        prev_m = c["16:59"] - c["15:59"]
        for h in BARS:
            day = d if h < "18:00" else (pd.Timestamp(d) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
            rows.append({"root": root, "session": d, "et": f"{day} {h}", "hhmm": h, "contract": "NQZ9", "close": round(c[h], 2)})
    return pd.DataFrame(rows)


def selftest() -> int:
    sign_audit()
    try:
        sign_audit(-1.0)
    except D777Error:
        pass
    else:
        raise D777Error("the sign audit did not raise on a mirrored book")
    rng = np.random.default_rng(1)
    sessions = [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2017-01-02", "2019-12-31")]
    # 1) a planted reversal across weekends is faded correctly and passes G1, N and M
    b = _synthetic("NQ", sessions, 0.8, rng)
    D = panel(b, "NQ")
    fri = [s for s in D.index if pd.Timestamp(s).weekday() == 4 and D.at[s, "valid"]]
    need(len(fri) > 0 and (D.loc[fri, "gap"] == 3).all(), "weekend: a Friday's S+1 must be Monday")
    T = D[D["gate"]]
    need(T["gross"].mean() > 0, "a planted reversal must pay")
    r = study(b, "NQ", workers=1)
    need(r["gates"]["G1"] and r["gates"]["N"] and r["gates"]["M"], f"planted reversal gates: {r['gates']}")
    # 2) the threshold uses no same-day value: a huge |m| today leaves today's threshold unchanged
    b2 = b.copy()
    tgt = sessions[400]
    b2.loc[(b2["session"] == tgt) & (b2["hhmm"] == "16:59"), "close"] += 1e5
    D2 = panel(b2, "NQ")
    need(D2.at[tgt, "thr"] == D.at[tgt, "thr"], "the threshold used a same-day value")
    # 3) the second implementation raises on a broken side
    Dx = D.copy()
    t0 = Dx[Dx["gate"]].index[0]
    Dx.loc[t0, "gross"] = -Dx.loc[t0, "gross"]
    try:
        audit(b, "NQ", Dx.loc[[t0] + [i for i in Dx.index if i != t0]].sort_index(), n=10_000)
    except D777Error:
        pass
    else:
        raise D777Error("the second implementation did not raise on a broken side")
    # 4) chunk == whole for the rotation on a tie-heavy input
    s = rng.integers(-1, 2, size=1501).astype(float)
    f = rng.integers(-3, 4, size=1501).astype(float)
    need(bool(np.array_equal(rotation(s, f, 1), rotation(s, f, 4))), "chunk != whole")
    # 5) a planted continuation fails G1
    r2 = study(_synthetic("NQ", sessions, -0.8, rng), "NQ", workers=1)
    need(not r2["gates"]["G1"], "a planted continuation must not pass G1")
    print("selftest OK: weekend pairing, a planted reversal passes G1/N/M and a continuation fails, the threshold uses "
          "no same-day value, the second implementation raises on a broken side, chunk == whole")
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
