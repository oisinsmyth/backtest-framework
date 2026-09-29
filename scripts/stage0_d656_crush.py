"""D656 Stage 0 -- the soybean board crush: the processors' premium (S1) and reversion towards next year (S2).

    uv run python scripts/stage0_d656_crush.py --selftest
    uv run python scripts/stage0_d656_crush.py --run          # -> data/stage0_d656_crush.json

DESIGN: docs/decisions/D656-STAGE-0-DESIGN-the-soybean-crush-premium-and-reversion.md (5a2b6ed), committed before this
file existed.

NOTHING AT OR AFTER 2024-01-01 IS READ: the strip is filtered at the loader and asserted after. Contract codes are
resolved per ROW (D655's resolver). No window ends within ten business days of a leg's first notice day (asserted).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

import run_d655_metals_roll as m655  # noqa: E402
from backtest_framework.validation.frozen import assert_none_at_or_after, filter_before  # noqa: E402

d654 = m655.d654
STRIP = m655.STRIP
OI_FIX = d654.FIX if d654.FIX.exists() else d654._main_checkout(REPO) / "data" / "fixtures" / "fut_oi_expiry_cycles.csv.gz"
OUT = REPO / "data" / "stage0_d656_crush.json"

RESERVED_FROM, LAST, START = "2024-01-01", "2023-12-29", "2011-01-01"
ROOTS = ("ZS", "ZM", "ZL")
BEAN_LETTERS = {1: 1, 3: 3, 5: 5, 7: 7, 8: 8, 9: 9, 11: 12}    # bean month -> product month (X beans -> Z products)
H = 4
NO_DELIVERY_BD = 10
PURGE = 26
DRAWS, SEED = 2000, 656
RT_ONE, RT_TWO = 500.64 / 50000.0, 2 * 500.64 / 50000.0         # D656 s.5, $/bu
TERCILE_WEEKS, STATE_SHARE, LIQ_MIN = 8, 0.60, 0.05


def P(*a, **k):
    print(*a, **k, flush=True)


class GateError(AssertionError):
    pass


# ------------------------------------------------------------------ data
def load_strip(exp) -> dict[str, pd.DataFrame]:
    s = pd.read_csv(STRIP, usecols=["root", "contract", "ref", "settle"], encoding="utf-8")
    s = s[s["root"].isin(ROOTS)]
    s = filter_before(s, "ref", RESERVED_FROM)
    assert_none_at_or_after(s, "ref", RESERVED_FROM)
    s["ref_ts"] = pd.to_datetime(s["ref"])
    out = {}
    for root, g in s.groupby("root"):
        g = g.copy()
        g["dlv"] = m655.resolve_rows(g, exp)
        g = g[g["dlv"].notna()]
        g["dlv"] = g["dlv"].astype(int)
        if g.duplicated(["dlv", "ref_ts"]).any():
            raise GateError(f"[RESOLVE] {root}: two settlements for one (delivery, session)")
        out[root] = g.pivot_table(index="ref_ts", columns="dlv", values="settle", aggfunc="last").sort_index()
    return out


def fnd(dlv: int, sessions: np.ndarray) -> pd.Timestamp:
    y, mth = divmod(dlv - 1, 12)
    mth += 1
    py, pm = (y, mth - 1) if mth > 1 else (y - 1, 12)
    lo, hi = pd.Timestamp(py, pm, 1), pd.Timestamp(y, mth, 1)
    s = sessions[(sessions >= lo) & (sessions < hi)]
    return pd.Timestamp(s[-1]) if len(s) else pd.bdate_range(lo, hi - pd.Timedelta(days=1))[-1]


def pairs(years=range(2010, 2027)) -> list[tuple[int, int]]:
    """(bean delivery, product delivery) as year*12+month; X beans pair with Z products."""
    out = []
    for y in years:
        for bm, pmth in BEAN_LETTERS.items():
            out.append((y * 12 + bm, y * 12 + pmth))
    return sorted(out)


def crush(st: dict, t, pb: int, pp: int) -> float:
    try:
        zs, zm, zl = st["ZS"].at[t, pb], st["ZM"].at[t, pp], st["ZL"].at[t, pp]
    except KeyError:
        return float("nan")
    return 0.022 * zm + 0.11 * zl - zs / 100.0


def legs(st: dict, t0, t1, pb: int, pp: int):
    return (0.022 * (st["ZM"].at[t1, pp] - st["ZM"].at[t0, pp]), 0.11 * (st["ZL"].at[t1, pp] - st["ZL"].at[t0, pp]),
            -(st["ZS"].at[t1, pb] - st["ZS"].at[t0, pb]) / 100.0)


def weekly(st: dict) -> pd.DatetimeIndex:
    have = pd.concat([st[r].notna().any(axis=1) for r in ROOTS], axis=1).dropna().all(axis=1)
    days = have.index[have.to_numpy()]
    iso = days.isocalendar()
    w = pd.Series(days, index=days).groupby([iso.year.to_numpy(), iso.week.to_numpy()]).max()
    w = pd.DatetimeIndex(sorted(w.to_numpy()))
    return w[w >= pd.Timestamp(START)]


def near_pair(t, sessions, prs, fnds, h=H):
    for pb, pp in prs:
        early = min(fnds[pb], fnds[pp])
        if early >= t + pd.Timedelta(weeks=h + 2):
            return pb, pp, early
    return None


# ------------------------------------------------------------------ statistics
def nw_se_slope(x, y, lags):
    X = np.column_stack([np.ones_like(x), x])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ b
    xtx = np.linalg.inv(X.T @ X)
    u = X * e[:, None]
    S = u.T @ u
    for L in range(1, lags + 1):
        w = 1 - L / (lags + 1)
        G = u[L:].T @ u[:-L]
        S += w * (G + G.T)
    return float(b[1]), float(math.sqrt((xtx @ S @ xtx)[1, 1]))


def nw_mean_t(y, lags):
    e = y - y.mean()
    n = len(y)
    s = float(e @ e) / n
    for L in range(1, lags + 1):
        s += 2 * (1 - L / (lags + 1)) * float(e[L:] @ e[:-L]) / n
    return float(y.mean() / math.sqrt(s / n)) if s > 0 else float("nan")


def slope(x, y):
    xc = x - x.mean()
    d = float((xc * xc).sum())
    return float((xc * (y - y.mean())).sum() / d) if d > 0 else float("nan")


def null_positive_years(sd_week: float, sizes: list[int], rng) -> np.ndarray:
    """S1: zero-drift random walks, same observations per year; the count of years with a positive mean 4-week change."""
    out = np.empty(DRAWS, int)
    for d in range(DRAWS):
        c = 0
        for n in sizes:
            w = np.cumsum(rng.normal(0, sd_week, n + H))
            c += (w[H:n + H] - w[:n]).mean() > 0
        out[d] = c
    return out


def null_negative_slope_years(sd_week: float, sizes: list[int], rng) -> np.ndarray:
    """S2: G a random walk; the count of years with a negative within-year slope of G's 4-week change on G."""
    out = np.empty(DRAWS, int)
    for d in range(DRAWS):
        c = 0
        for n in sizes:
            g = np.cumsum(rng.normal(0, sd_week, n + H))
            c += slope(g[:n], g[H:n + H] - g[:n]) < 0
        out[d] = c
    return out


# ------------------------------------------------------------------ the run
def build_panel(st, weeks):
    sessions = np.array(sorted(set(st["ZS"].index) & set(st["ZM"].index) & set(st["ZL"].index)))
    prs = pairs()
    fnds = {}
    for pb, pp in prs:
        fnds[pb] = fnd(pb, sessions)
        fnds[pp] = fnd(pp, sessions)
        fnds[pb + 12], fnds[pp + 12] = fnd(pb + 12, sessions), fnd(pp + 12, sessions)
    wl = list(weeks)
    rows = []
    for i, t in enumerate(wl[:-H]):
        t1 = wl[i + H]
        if t1 > pd.Timestamp(LAST):
            break
        np_ = near_pair(t, sessions, prs, fnds)
        if np_ is None:
            continue
        pb, pp, early = np_
        if np.busday_count(t1.date(), early.date()) < NO_DELIVERY_BD:
            raise GateError(f"[DELIVERY] window ending {t1.date()} is within {NO_DELIVERY_BD} business days of {early.date()}")
        c0, c1 = crush(st, t, pb, pp), crush(st, t1, pb, pp)
        if not (np.isfinite(c0) and np.isfinite(c1)):
            continue
        row = {"t": t, "t1": t1, "pb": pb, "pp": pp, "C": c0, "Y1": c1 - c0}
        row["leg_meal"], row["leg_oil"], row["leg_beans"] = legs(st, t, t1, pb, pp)
        n1 = near_pair(t1, sessions, prs, fnds)
        row["L1"] = crush(st, t1, n1[0], n1[1]) if n1 else np.nan
        cy0, cy1 = crush(st, t, pb + 12, pp + 12), crush(st, t1, pb + 12, pp + 12)
        row["G"] = c0 - cy0 if np.isfinite(cy0) else np.nan
        row["Y2"] = (c1 - cy1) - (c0 - cy0) if np.isfinite(cy0) and np.isfinite(cy1) else np.nan
        rows.append(row)
    p = pd.DataFrame(rows)
    p["dL"] = p["L1"] - p["C"]
    p["R"] = p["Y1"] - p["dL"]
    return p, sessions, prs, fnds


def holding_cycles(p: pd.DataFrame, st: dict, weeks: pd.DatetimeIndex) -> pd.DataFrame:
    """Enter a pair the first week it is the near pair, leave the first week it is not: the change of ITS crush."""
    out = []
    p = p.sort_values("t").reset_index(drop=True)
    wl = list(weeks)
    pos = {w: i for i, w in enumerate(wl)}
    grp = (p["pb"] != p["pb"].shift()).cumsum()
    for _, g in p.groupby(grp):
        pb, pp = int(g["pb"].iloc[0]), int(g["pp"].iloc[0])
        j = pos[g["t"].iloc[-1]] + 1
        if j >= len(wl) or wl[j] > pd.Timestamp(LAST):
            continue
        c0, c1 = crush(st, g["t"].iloc[0], pb, pp), crush(st, wl[j], pb, pp)
        if np.isfinite(c0) and np.isfinite(c1):
            out.append({"pb": pb, "entry": g["t"].iloc[0], "exit": wl[j], "change": float(c1 - c0)})
    return pd.DataFrame(out)


def run() -> int:
    exp = d654.load_expiries()
    st = load_strip(exp)
    weeks = weekly(st)
    p, sessions, prs, fnds = build_panel(st, weeks)
    P(f"{len(p)} weekly observations {p['t'].min().date()} -> {p['t1'].max().date()}")
    rng = np.random.default_rng(SEED)
    yrs = p["t"].dt.year
    sizes = p.groupby(yrs).size().tolist()
    out = {"decision_record": "D656", "stage": "0", "reserved_from": RESERVED_FROM, "last_target": LAST,
           "strip_last_session_read": str(max(st[r].index.max() for r in ROOTS).date()), "n": int(len(p))}

    # ---- S1
    y1, r = p["Y1"].to_numpy(float), p["R"].dropna().to_numpy(float)
    sd_week = float(np.std(np.diff(p["C"].to_numpy(float)), ddof=1))
    nullc = null_positive_years(float(np.std(y1, ddof=1)) / 2.0, sizes, rng)
    by_year = p.groupby(yrs)["Y1"].mean()
    jack = {int(y): float(p.loc[yrs != y, "Y1"].mean()) for y in sorted(yrs.unique())}
    hc = holding_cycles(p, st, weeks)
    # a cycle's change: from entry to the exit week's settlement (the week the pair is last near)
    s1 = {"mean_Y1": float(y1.mean()), "t_Y1": nw_mean_t(y1, H), "median_Y1": float(np.median(y1)),
          "mean_R": float(r.mean()), "t_R": nw_mean_t(r, H), "mean_dL": float(p["dL"].mean()),
          "legs": {k: float(p[k].mean()) for k in ("leg_meal", "leg_oil", "leg_beans")},
          "years_positive": int((by_year > 0).sum()), "years": int(len(by_year)),
          "null_years_positive_p95": float(np.percentile(nullc, 95)), "null_years_positive_p50": float(np.median(nullc)),
          "by_year": {int(k): round(float(v), 4) for k, v in by_year.items()}, "jackknife": jack,
          "jackknife_all_positive": bool(all(v > 0 for v in jack.values())),
          "holding_cycles": int(len(hc)), "cycle_change_mean": float(hc["change"].mean()),
          "cycle_change_t": nw_mean_t(hc["change"].to_numpy(float), 1),
          "round_trip_per_bu": RT_ONE,
          "sub_2016_2023": {"mean_Y1": float(p.loc[yrs >= 2016, "Y1"].mean()),
                            "t_Y1": nw_mean_t(p.loc[yrs >= 2016, "Y1"].to_numpy(float), H),
                            "mean_R": float(p.loc[yrs >= 2016, "R"].mean())}}
    s1["bars"] = {"B1_Y1_t_ge_2": bool(s1["mean_Y1"] > 0 and s1["t_Y1"] >= 2),
                  "B2_R_t_ge_2": bool(s1["mean_R"] > 0 and s1["t_R"] >= 2),
                  "B3_years_at_null_p95": bool(s1["years_positive"] >= s1["null_years_positive_p95"]),
                  "B4_every_leave_one_year_out_positive": s1["jackknife_all_positive"],
                  "B5_cycle_ge_3x_round_trip": bool(s1["cycle_change_mean"] >= 3 * RT_ONE)}
    out["S1"] = s1

    # ---- S2
    q = p.dropna(subset=["G", "Y2"]).reset_index(drop=True)
    G, Y2 = q["G"].to_numpy(float), q["Y2"].to_numpy(float)
    beta, se = nw_se_slope(G, Y2, H)
    ks = np.arange(PURGE + 1, len(G) - PURGE)
    rb = np.array([slope(np.roll(G, k), Y2) for k in ks])
    qy = q["t"].dt.year
    within = {int(y): slope(G[qy == y], Y2[qy == y]) for y in sorted(qy.unique()) if (qy == y).sum() >= 10}
    nulln = null_negative_slope_years(float(np.std(np.diff(G), ddof=1)), q.groupby(qy).size().tolist(), rng)
    q1, q2 = np.quantile(G, [1 / 3, 2 / 3])
    tcount = {int(y): (int(((qy == y) & (q["G"] < q1)).sum()), int(((qy == y) & (q["G"] > q2)).sum()))
              for y in sorted(qy.unique())}
    both = sum(lo >= TERCILE_WEEKS and hi >= TERCILE_WEEKS for lo, hi in tcount.values())
    s2 = {"n": int(len(q)), "beta": beta, "t": beta / se, "spearman": float(pd.Series(G).rank().corr(pd.Series(Y2).rank())),
          "rotation": {"offsets": int(len(ks)), "k_min": int(ks.min()), "p05": float(np.percentile(rb, 5)),
                       "p50": float(np.percentile(rb, 50)), "p95": float(np.percentile(rb, 95)),
                       "rank": float((rb < beta).mean())},
          "within_year_beta": within, "years_negative": int(sum(v < 0 for v in within.values())),
          "null_years_negative_p95": float(np.percentile(nulln, 95)), "null_years_negative_p50": float(np.median(nulln)),
          "tercile_counts": tcount, "years_both_states": int(both), "years": int(len(tcount)),
          "median_abs_G": float(np.median(np.abs(G))), "move_at_median_G": float(abs(beta) * np.median(np.abs(G))),
          "round_trip_two_units_per_bu": RT_TWO,
          "sub_2016_2023_beta": slope(G[qy >= 2016], Y2[qy >= 2016])}
    # S2-B6: year-ahead legs' cleared volume against the near legs', 2016-2023, in the weeks used
    liq = liquidity(q, exp)
    s2["liquidity"] = liq
    s2["bars"] = {"B1_beta_t_le_-2": bool(beta < 0 and s2["t"] <= -2),
                  "B2_below_rotation_p05": bool(beta < s2["rotation"]["p05"]),
                  "B3_years_at_null_p95": bool(s2["years_negative"] >= s2["null_years_negative_p95"]),
                  "B4_state_in_60pct_of_years": bool(both >= STATE_SHARE * len(tcount)),
                  "B5_move_ge_3x_two_units": bool(s2["move_at_median_G"] >= 3 * RT_TWO),
                  "B6_year_ahead_legs_trade": bool(all(v is not None and v >= LIQ_MIN for v in liq["ratio_median"].values()))}
    out["S2"] = s2

    def route(b):
        ks_ = list(b)
        if all(b.values()):
            return "routes: all bars pass -> a pre-registration with the expected-profit filter, for the principal"
        if not (b[ks_[0]] and b[ks_[1]]):
            return "B1 or B2 fails: recommend closing this premise"
        return "B1 and B2 pass, a later bar fails: reported, no construction"
    out["S1"]["route"], out["S2"]["route"] = route(s1["bars"]), route(s2["bars"])
    out["route"] = ("both premises fail B1 or B2: recommend closing the crush line"
                    if "closing" in out["S1"]["route"] and "closing" in out["S2"]["route"] else "see each premise")
    most = max(jack, key=lambda y: abs(jack[y] - s1["mean_Y1"]))
    out["predictions"] = {
        "1_S1_B1_holds_B2_borderline": bool(s1["bars"]["B1_Y1_t_ge_2"] and 1.5 <= s1["t_R"] <= 2.5),
        "2_2021_or_2022_most_influential_and_B4_holds": bool(most in (2021, 2022) and s1["bars"]["B4_every_leave_one_year_out_positive"]),
        "3_S2_beta_negative_rank_le_0.10": bool(beta < 0 and s2["rotation"]["rank"] <= 0.10),
        "4_S2_B4_passes": s2["bars"]["B4_state_in_60pct_of_years"],
        "5_S2_B6_fails_for_oil": bool(liq["ratio_median"].get("ZL") is not None and liq["ratio_median"]["ZL"] < LIQ_MIN),
        "6_at_most_one_premise_routes": not (all(s1["bars"].values()) and all(s2["bars"].values())),
    }
    out["most_influential_year_S1"] = int(most)
    OUT.write_text(json.dumps(out, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    P(json.dumps(out, indent=1, default=str))
    return 0


def liquidity(q: pd.DataFrame, exp) -> dict:
    t = pd.read_csv(OI_FIX, dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8")
    t = t[t["root"].isin(ROOTS)].copy()
    t["ref_ts"] = pd.to_datetime(t["ref"])
    ratios = {}
    for root in ROOTS:
        g = t[t["root"] == root].copy()
        g["dlv"] = m655.resolve_rows(g, exp)
        g = g[g["dlv"].notna()]
        g["dlv"] = g["dlv"].astype(int)
        cv = g.pivot_table(index="ref_ts", columns="dlv", values="cv", aggfunc="last")
        vals = []
        for r in q[q["t"] >= pd.Timestamp("2016-01-04")].itertuples():
            near = r.pb if root == "ZS" else r.pp
            if r.t in cv.index and near in cv.columns and near + 12 in cv.columns:
                a, b = cv.at[r.t, near], cv.at[r.t, near + 12]
                if np.isfinite(a) and a > 0:
                    vals.append((b if np.isfinite(b) else 0.0) / a)
        ratios[root] = float(np.median(vals)) if vals else None
    return {"ratio_median": ratios, "window": ["2016-01-04", LAST]}


# ------------------------------------------------------------------ selftest
def selftest() -> int:
    n = 0

    def check(label, cond):
        nonlocal n
        if not cond:
            raise AssertionError(f"FAILED: {label}")
        n += 1
        P(f"  ok  {label}")

    def must_raise(label, fn):
        nonlocal n
        try:
            fn()
        except (GateError, AssertionError):
            n += 1
            P(f"  ok  raises: {label}")
            return
        raise AssertionError(f"did NOT raise: {label}")

    exp = d654.load_expiries()
    g = pd.DataFrame({"contract": ["ZSF1", "ZSF1"], "ref_ts": pd.to_datetime(["2010-12-01", "2012-01-03"])})
    d = m655.resolve_rows(g, exp).tolist()
    check(f"ZSF1 resolves per row: Jan 2011 in 2010, Jan 2021 in 2012 ({d})", d == [2011 * 12 + 1, 2021 * 12 + 1])
    pr = dict(pairs(range(2019, 2020)))
    check("November beans pair with December products", pr[2019 * 12 + 11] == 2019 * 12 + 12)
    check("January beans pair with January products", pr[2019 * 12 + 1] == 2019 * 12 + 1)
    sess = np.array(pd.bdate_range("2019-01-01", "2019-12-31"))
    f = {k: fnd(k, sess) for kk in pairs(range(2019, 2021)) for k in kk}
    for t in pd.date_range("2019-01-04", "2019-10-25", freq="7D"):
        npair = near_pair(t, sess, pairs(range(2019, 2021)), f)
        if npair and np.busday_count((t + pd.Timedelta(weeks=H)).date(), npair[2].date()) < NO_DELIVERY_BD:
            raise AssertionError("a window ends inside ten business days of a first notice")
    check("no window ends inside ten business days of a leg's first notice day", True)
    p = pd.DataFrame({"Y1": [0.1, -0.2, 0.3], "C": [1.0, 1.1, 0.9], "L1": [1.2, 0.8, 1.0]})
    p["dL"] = p["L1"] - p["C"]
    p["R"] = p["Y1"] - p["dL"]
    check("R is Y1 minus the constant-tenor change, exactly", np.allclose(p["R"] + p["dL"], p["Y1"]))
    rng = np.random.default_rng(1)
    nn = null_negative_slope_years(1.0, [52] * 8, rng)
    check(f"the S2 null reproduces Kendall's bias on a random walk (mean {nn.mean():.2f} of 8 negative)", nn.mean() > 6)
    npos = null_positive_years(1.0, [52] * 8, rng)
    check(f"the S1 null is a coin flip on a zero-drift walk (mean {npos.mean():.2f} of 8 positive)", 3.3 < npos.mean() < 4.7)
    ks = np.arange(PURGE + 1, 400 - PURGE)
    check("the rotation excludes the purged offsets", ks.min() == 27 and ks.max() == 400 - 27)
    must_raise("a 2024 settlement past the loader",
               lambda: assert_none_at_or_after(pd.DataFrame({"ref": ["2024-01-02"]}), "ref", RESERVED_FROM))
    P(f"selftest: {n} checks")
    return 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args()
    return selftest() if a.selftest else run()


if __name__ == "__main__":
    sys.exit(main())
