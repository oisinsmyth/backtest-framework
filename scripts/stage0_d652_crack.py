"""D652 Stage 0 -- does the 3-2-1 crack spread revert to its own seasonal norm?

    uv run python scripts/stage0_d652_crack.py --selftest
    uv run python scripts/stage0_d652_crack.py --run          # -> data/stage0_d652_crack.json

DESIGN: docs/decisions/D652-STAGE-0-DESIGN-does-the-crack-spread-revert-to-its-norm.md (a4ddf4f),
committed before this file existed.

NOTHING AT OR AFTER 2024-01-01 IS READ. The strip is filtered at the loader (frozen.filter_before) and asserted
after (frozen.assert_none_at_or_after): two code paths, as D594 requires. The forward power in s.5 is computed from
in-sample quantities and the count of forward WEEKS on the calendar; no forward settlement is opened.

The strip and its expiry file: the gitignored strip is read from this checkout if present, else the main checkout's.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.validation.frozen import assert_none_at_or_after, filter_before  # noqa: E402


def _main_checkout(repo: Path) -> Path:
    p = repo
    while p.parent != p:
        if p.name == "worktrees" and p.parent.name == ".claude":
            return p.parent.parent
        p = p.parent
    return repo


MAIN = _main_checkout(REPO)


def _resolve(rel: str) -> Path:
    p = REPO / rel
    return p if p.exists() else MAIN / rel


STRIP = _resolve("data/fixtures/fut_settle_strip.csv.gz")
EXPIRIES = REPO / "data" / "fut_expiries_from_definition.json"
OUT = REPO / "data" / "stage0_d652_crack.json"

RESERVED_FROM = "2024-01-01"
LAST_TARGET = "2023-12-29"
ULSD_FIRST = 2013 * 12 + 5                 # the first ULSD HO delivery, May 2013, as year*12 + month
BBL = 42.0
ROUND_TRIP_PER_BBL = 180.59 / 3000.0       # D652 s.5, from D651's map and D591's commission
HORIZONS = (2, 4, 8, 13)
PRIMARY_H = 4
NORM_YEARS = 3
NORM_MIN_OBS = 3
PURGE = 26
TERCILE_MIN_WEEKS = 8
FORWARD_WINDOWS = {"2024-01-01..2025-02-28": ("2024-01-01", "2025-02-28"),
                   "2024-01-01..2026-09-18 (with the vault)": ("2024-01-01", "2026-09-18")}
MONTH = {c: i + 1 for i, c in enumerate("FGHJKMNQUVXZ")}
RE_C = re.compile(r"^(CL|HO|RB)([FGHJKMNQUVXZ])(\d{1,2})$")


def P(*a, **k):
    print(*a, **k, flush=True)


class GateError(AssertionError):
    pass


# ------------------------------------------------------------------ loading and contract resolution
def load_strip(path: Path = STRIP) -> pd.DataFrame:
    s = pd.read_csv(path, usecols=["root", "contract", "ref", "settle"], encoding="utf-8")
    s = s[s["root"].isin(["CL", "HO", "RB"])]
    s = filter_before(s, "ref", RESERVED_FROM)
    assert_none_at_or_after(s, "ref", RESERVED_FROM)
    return s.reset_index(drop=True)


def load_expiries() -> dict[str, list[pd.Timestamp]]:
    e = json.loads(EXPIRIES.read_text(encoding="utf-8"))["expiries"]
    out = {}
    for root in ("CL", "HO", "RB"):
        for code, ns in e[root].items():
            out[code] = sorted(pd.Timestamp(int(x), tz="UTC").tz_convert("US/Eastern").tz_localize(None).normalize()
                               for x in ns)
    return out


def resolve(code: str, session: pd.Timestamp, exp: dict) -> tuple[pd.Timestamp, int] | None:
    """(expiry date, delivery year*12+month) of a strip code on a session: the first expiry on or after the
    session among the code's decades. The delivery month is the code's letter; its year is the expiry's year,
    plus one when the letter's month is not after the expiry's month (CL/HO/RB expire in the month before
    delivery)."""
    m = RE_C.match(code)
    if not m or code not in exp:
        return None
    for e in exp[code]:
        if e >= session:
            mon = MONTH[m.group(2)]
            year = e.year if mon > e.month else e.year + 1
            return e, year * 12 + mon
    return None


def wide_table(strip: pd.DataFrame, exp: dict):
    """settle[(root, delivery)] by session, and CL's expiry by delivery."""
    strip = strip.copy()
    strip["ref_ts"] = pd.to_datetime(strip["ref"])
    res = [resolve(c, t, exp) for c, t in zip(strip["contract"], strip["ref_ts"])]
    ok = np.array([r is not None for r in res])
    strip = strip[ok].copy()
    res = [r for r in res if r is not None]
    strip["expiry"] = [r[0] for r in res]
    strip["dlv"] = [r[1] for r in res]
    # a settlement after its own expiry would be a resolution error
    if (strip["ref_ts"] > strip["expiry"]).any():
        raise GateError("[RESOLVE] a settlement dated after its contract's expiry")
    dup = strip.duplicated(["root", "dlv", "ref"])
    if dup.any():
        raise GateError(f"[RESOLVE] {int(dup.sum())} duplicate (root, delivery, session) settlements")
    settle = strip.pivot_table(index="ref_ts", columns=["root", "dlv"], values="settle", aggfunc="first")
    cl_exp = strip[strip["root"] == "CL"].groupby("dlv")["expiry"].first()
    return settle, cl_exp


def weekly_sessions(settle: pd.DataFrame) -> pd.DatetimeIndex:
    """The last session of each ISO week on which CL, HO and RB each settle at least one contract."""
    have = pd.concat([settle[r].notna().any(axis=1) for r in ("CL", "HO", "RB")], axis=1).all(axis=1)
    days = settle.index[have.to_numpy()]
    wk = pd.Series(days, index=days).groupby([days.isocalendar().year.to_numpy(), days.isocalendar().week.to_numpy()]).max()
    return pd.DatetimeIndex(sorted(wk.to_numpy()))


def m_star(t: pd.Timestamp, h: int, cl_exp: pd.Series) -> int | None:
    """The nearest delivery whose CL expiry is at least h + 1 weeks after t."""
    alive = cl_exp[cl_exp >= t + pd.Timedelta(weeks=h + 1)]
    return int(alive.index.min()) if len(alive) else None


def crack_value(settle: pd.DataFrame, t: pd.Timestamp, dlv: int, kind: str = "321") -> float:
    try:
        cl = settle.at[t, ("CL", dlv)]
        ho = settle.at[t, ("HO", dlv)] if kind in ("321", "dist") else 0.0
        rb = settle.at[t, ("RB", dlv)] if kind in ("321", "gas") else 0.0
    except KeyError:
        return float("nan")
    if kind == "321":
        return (2 * BBL * rb + BBL * ho - 3 * cl) / 3.0
    if kind == "gas":
        return BBL * rb - cl
    return BBL * ho - cl


def legs(settle, t0, t1, dlv):
    """The three terms of the 3-2-1 crack's change, which sum to it exactly."""
    d = {r: settle.at[t1, (r, dlv)] - settle.at[t0, (r, dlv)] for r in ("CL", "HO", "RB")}
    return 2 * BBL * d["RB"] / 3.0, BBL * d["HO"] / 3.0, -3 * d["CL"] / 3.0


# ------------------------------------------------------------------ the norm, real-time
def build_norm_inputs(settle, weeks, cl_exp, kind: str):
    """Cbar(m, y): the mean crack of delivery (m, y) over the weeks it was m*(., 4), with the last such week."""
    rows = []
    for t in weeks:
        d = m_star(t, PRIMARY_H, cl_exp)
        if d is None:
            continue
        if kind in ("321", "dist") and d < ULSD_FIRST:
            continue
        v = crack_value(settle, t, d, kind)
        if np.isfinite(v):
            rows.append((d, t, v))
    df = pd.DataFrame(rows, columns=["dlv", "t", "c"])
    g = df.groupby("dlv").agg(cbar=("c", "mean"), n=("c", "size"), last=("t", "max"))
    return g


def norm(dlv: int, cbar: pd.DataFrame, kind: str) -> tuple[float, pd.Timestamp] | None:
    """S(m, Y) = mean Cbar over the three prior delivery years of the same month, each with >= 3 weeks and (for
    anything carrying HO) a ULSD delivery. Returns (S, the last session any input used)."""
    vals, lasts = [], []
    for k in range(1, NORM_YEARS + 1):
        prior = dlv - 12 * k
        if kind in ("321", "dist") and prior < ULSD_FIRST:
            return None
        if prior not in cbar.index or cbar.at[prior, "n"] < NORM_MIN_OBS:
            return None
        vals.append(float(cbar.at[prior, "cbar"]))
        lasts.append(cbar.at[prior, "last"])
    return float(np.mean(vals)), max(lasts)


def panel(settle, weeks, cl_exp, cbar, h: int, kind: str = "321") -> pd.DataFrame:
    rows = []
    wl = list(weeks)
    for i, t in enumerate(wl[:-h] if h else wl):
        t1 = wl[i + h]
        if t1 > pd.Timestamp(LAST_TARGET):
            break
        d = m_star(t, h, cl_exp)
        if d is None or (kind in ("321", "dist") and d < ULSD_FIRST):
            continue
        nm = norm(d, cbar, kind)
        if nm is None:
            continue
        s, last_used = nm
        if not last_used < t:
            raise GateError(f"[REAL-TIME] the norm for delivery {d} at {t.date()} used a session on {last_used.date()}")
        c0, c1 = crack_value(settle, t, d, kind), crack_value(settle, t1, d, kind)
        if not (np.isfinite(c0) and np.isfinite(c1)):
            continue
        row = {"t": t, "t1": t1, "dlv": d, "C": c0, "S": s, "D": c0 - s, "Y": c1 - c0}
        if kind == "321":
            row["Y_rb"], row["Y_ho"], row["Y_cl"] = legs(settle, t, t1, d)
        rows.append(row)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ statistics
def ols(x: np.ndarray, y: np.ndarray):
    X = np.column_stack([np.ones_like(x), x])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    return b, y - X @ b, X


def nw_se(x: np.ndarray, y: np.ndarray, lags: int) -> tuple[float, float, float]:
    """(beta, Newey-West se, plain OLS se) of the slope; Bartlett weights."""
    b, e, X = ols(x, y)
    n = len(y)
    xtx_inv = np.linalg.inv(X.T @ X)
    u = X * e[:, None]
    S = u.T @ u
    for L in range(1, lags + 1):
        w = 1.0 - L / (lags + 1.0)
        G = u[L:].T @ u[:-L]
        S += w * (G + G.T)
    V = xtx_inv @ S @ xtx_inv
    s2 = float(e @ e) / (n - 2)
    return float(b[1]), float(math.sqrt(V[1, 1])), float(math.sqrt(s2 * xtx_inv[1, 1]))


def nw_mean_se(y: np.ndarray, lags: int) -> float:
    """Newey-West se of a mean (the always-on control's drift), Bartlett weights."""
    e = y - y.mean()
    n = len(y)
    s = float(e @ e) / n
    for L in range(1, lags + 1):
        s += 2 * (1.0 - L / (lags + 1.0)) * float(e[L:] @ e[:-L]) / n
    return math.sqrt(s / n)


def dlv_label(dlv: int) -> str:
    """year*12 + month (month 1..12) -> 'YYYY-MM'."""
    return f"{(dlv - 1) // 12}-{(dlv - 1) % 12 + 1:02d}"


def slope(x, y) -> float:
    xc = x - x.mean()
    return float((xc * (y - y.mean())).sum() / (xc * xc).sum())


def rotation(D: np.ndarray, Y: np.ndarray, purge: int = PURGE) -> tuple[np.ndarray, np.ndarray]:
    n = len(D)
    ks = np.arange(purge + 1, n - purge)
    betas = np.array([slope(np.roll(D, k), Y) for k in ks])
    return ks, betas


def spearman(a, b) -> float:
    return float(pd.Series(a).rank().corr(pd.Series(b).rank()))


def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def forward_weeks(a: str, b: str) -> int:
    """ISO weeks on the calendar between two dates -- a count, no settlement opened."""
    iso = pd.bdate_range(a, b).isocalendar()
    return int(len(set(zip(iso["year"], iso["week"]))))


def score(p: pd.DataFrame, h: int) -> dict:
    D, Y = p["D"].to_numpy(float), p["Y"].to_numpy(float)
    beta, se_nw, se_ols = nw_se(D, Y, lags=h)
    ks, rb = rotation(D, Y)
    years = p["t"].dt.year.to_numpy()
    by_year = {int(y): slope(D[years == y], Y[years == y]) for y in sorted(set(years)) if (years == y).sum() >= 10}
    jack = {int(y): slope(D[years != y], Y[years != y]) for y in sorted(set(years))}
    phases = [slope(D[i::h], Y[i::h]) for i in range(h)] if h > 1 else [beta]
    return {"n": int(len(p)), "beta": beta, "t_nw": beta / se_nw, "se_nw": se_nw, "se_ols": se_ols,
            "spearman": spearman(D, Y), "phases": phases,
            "rotation": {"offsets": int(len(ks)), "k_min": int(ks.min()), "k_max": int(ks.max()),
                         "p05": float(np.percentile(rb, 5)), "p50": float(np.percentile(rb, 50)),
                         "p95": float(np.percentile(rb, 95)), "rank": float((rb < beta).mean()),
                         "profile": {int(k): round(float(b), 5) for k, b in zip(ks, rb)}},
            "by_year": by_year, "years_negative": int(sum(v < 0 for v in by_year.values())),
            "years_scored": int(len(by_year)),
            "jackknife": jack, "jackknife_all_negative": bool(all(v < 0 for v in jack.values())),
            "median_abs_D": float(np.median(np.abs(D))), "mean_Y": float(Y.mean()),
            "window": [str(p["t"].min().date()), str(p["t1"].max().date())]}


def run() -> int:
    exp = load_expiries()
    strip = load_strip()
    settle, cl_exp = wide_table(strip, exp)
    weeks = weekly_sessions(settle)
    P(f"strip CL/HO/RB {len(strip):,} rows to {strip['ref'].max()}; {len(weeks)} weekly sessions")
    out = {"decision_record": "D652", "stage": "0", "reserved_from": RESERVED_FROM, "last_target": LAST_TARGET,
           "strip_last_session_read": str(strip["ref"].max()), "objects": {}}
    for kind in ("321", "gas", "dist"):
        cbar = build_norm_inputs(settle, weeks, cl_exp, kind)
        res = {}
        for h in HORIZONS:
            p = panel(settle, weeks, cl_exp, cbar, h, kind)
            if len(p) < 50:
                res[str(h)] = {"n": int(len(p)), "note": "too few observations"}
                continue
            sc = score(p, h)
            if kind == "321" and h == PRIMARY_H:
                D = p["D"].to_numpy(float)
                comps = {c: slope(D, p[c].to_numpy(float)) for c in ("Y_rb", "Y_ho", "Y_cl")}
                if abs(sum(comps.values()) - sc["beta"]) > 1e-9:
                    raise GateError(f"[LEGS] leg betas sum to {sum(comps.values())}, beta {sc['beta']}")
                sc["legs"] = comps
                sc["products_share"] = (comps["Y_rb"] + comps["Y_ho"]) / sc["beta"] if sc["beta"] else None
                rho = float(np.corrcoef(D[:-1], D[1:])[0, 1])
                sc["ar1"] = rho
                sc["half_life_weeks"] = (math.log(2) / -math.log(rho)) if 0 < rho < 1 else None
                q1, q2 = np.quantile(D, [1 / 3, 2 / 3])
                yrs = p["t"].dt.year
                counts = {int(y): (int(((yrs == y) & (p["D"] < q1)).sum()), int(((yrs == y) & (p["D"] > q2)).sum()))
                          for y in sorted(yrs.unique())}
                sc["tercile_counts"] = counts
                sc["years_with_both_states"] = int(sum(lo >= TERCILE_MIN_WEEKS and hi >= TERCILE_MIN_WEEKS
                                                       for lo, hi in counts.values()))
                sc["move_at_median_D"] = abs(sc["beta"]) * sc["median_abs_D"]
                sc["round_trip_per_bbl"] = ROUND_TRIP_PER_BBL
                sc["always_on"] = {"mean_Y": sc["mean_Y"],
                                   "t_nw": sc["mean_Y"] / nw_mean_se(p["Y"].to_numpy(float), h)}
                big = p.reindex(p["D"].abs().sort_values(ascending=False).index[:5])
                sc["largest_D"] = [{"t": str(r.t.date()), "delivery": dlv_label(r.dlv),
                                    "C": round(r.C, 3), "S": round(r.S, 3), "D": round(r.D, 3), "Y": round(r.Y, 3)}
                                   for r in big.itertuples()]
                # forward power from in-sample quantities only
                pw = {}
                for name, (a, b) in FORWARD_WINDOWS.items():
                    nf = forward_weeks(a, b) - h
                    se_f = sc["se_nw"] * math.sqrt(sc["n"] / nf)
                    pw[name] = {"weeks": nf, **{f"power_at_{int(f * 100)}pct": norm_cdf(-2.0 - f * sc["beta"] / se_f)
                                                if sc["beta"] < 0 else None for f in (1.0, 0.5)}}
                sc["forward_power"] = pw
            res[str(h)] = sc
        out["objects"][kind] = res
    pr = out["objects"]["321"][str(PRIMARY_H)]
    bars = {
        "B1_beta_negative_t_le_-2": bool(pr["beta"] < 0 and pr["t_nw"] <= -2.0),
        "B2_below_rotation_p05": bool(pr["beta"] < pr["rotation"]["p05"]),
        "B3_negative_in_6_of_8_years": bool(pr["years_negative"] >= 6),
        "B4_both_states_in_6_of_8_years": bool(pr["years_with_both_states"] >= 6),
        "B5_move_ge_3x_round_trip": bool(pr["move_at_median_D"] >= 3 * ROUND_TRIP_PER_BBL),
        "B6_every_leave_one_year_out_negative": bool(pr["jackknife_all_negative"]),
    }
    out["bars"] = bars
    b12 = bars["B1_beta_negative_t_le_-2"] and bars["B2_below_rotation_p05"]
    if all(bars.values()):
        route = "all six pass: draft a personal-book pre-registration; the principal decides the forward read"
    elif not b12:
        route = "B1 or B2 fails: the premise is not supported; recommend closing the crack line"
    elif not (bars["B3_negative_in_6_of_8_years"] and bars["B4_both_states_in_6_of_8_years"]
              and bars["B6_every_leave_one_year_out_negative"]):
        route = "B1 and B2 pass, but an era or a year carries it: reported, no construction recommended"
    else:
        route = "B5 alone fails: real, not tradable"
    out["route"] = route
    jack = pr["jackknife"]
    out["predictions"] = {
        "1_half_life_4_to_26_weeks": pr["half_life_weeks"] is not None and 4 <= pr["half_life_weeks"] <= 26,
        "2_beta_-0.05_to_-0.30_t_-1.5_to_-3.5": bool(-0.30 <= pr["beta"] <= -0.05 and -3.5 <= pr["t_nw"] <= -1.5),
        "3_B4_passes": bars["B4_both_states_in_6_of_8_years"],
        "4_2022_most_influential": max(jack, key=lambda y: abs(jack[y] - pr["beta"])) == 2022,
        "5_products_share_above_half": pr["products_share"] is not None and pr["products_share"] > 0.5,
        "6_always_on_small": abs(pr["mean_Y"]) < 0.25 * pr["move_at_median_D"],
        "7_B5_by_an_order_of_magnitude": pr["move_at_median_D"] >= 10 * ROUND_TRIP_PER_BBL,
        "8_forward_power_2024_2025_below_half": (pr["forward_power"]["2024-01-01..2025-02-28"]["power_at_100pct"] or 0) < 0.5,
    }
    OUT.write_text(json.dumps(out, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    brief = {k: v for k, v in pr.items() if k not in ("rotation", "by_year", "jackknife", "tercile_counts")}
    P(json.dumps({"primary": brief, "rotation": {k: v for k, v in pr["rotation"].items() if k != "profile"},
                  "by_year": pr["by_year"], "jackknife": pr["jackknife"], "tercile_counts": pr["tercile_counts"],
                  "bars": bars, "route": route, "predictions": out["predictions"]}, indent=1, default=str))
    for kind in ("gas", "dist"):
        for h in HORIZONS:
            s = out["objects"][kind][str(h)]
            if "beta" in s:
                P(f"  {kind} h={h}: n {s['n']} beta {s['beta']:+.4f} t {s['t_nw']:+.2f} rank {s['rotation']['rank']:.3f} "
                  f"years- {s['years_negative']}/{s['years_scored']}")
    for h in HORIZONS:
        s = out["objects"]["321"][str(h)]
        P(f"  321 h={h}: n {s['n']} beta {s['beta']:+.4f} t {s['t_nw']:+.2f} rank {s['rotation']['rank']:.3f} "
          f"years- {s['years_negative']}/{s['years_scored']}")
    return 0


# ------------------------------------------------------------------ selftest
def selftest() -> int:
    n_ok = 0

    def check(label, cond):
        nonlocal n_ok
        if not cond:
            raise AssertionError(f"FAILED: {label}")
        n_ok += 1
        P(f"  ok  {label}")

    def must_raise(label, fn, exc=AssertionError):
        nonlocal n_ok
        try:
            fn()
        except exc:
            n_ok += 1
            P(f"  ok  raises: {label}")
            return
        raise AssertionError(f"did NOT raise: {label}")

    exp = load_expiries()
    e, d = resolve("CLF1", pd.Timestamp("2010-06-07"), exp)
    check(f"CLF1 on 2010-06-07 is January 2011 (expiry {e.date()})", d == 2011 * 12 + 1 and e.year == 2010)
    e, d = resolve("CLF1", pd.Timestamp("2011-06-01"), exp)
    check(f"CLF1 on 2011-06-01 is January 2021, the recycled code (expiry {e.date()})", d == 2021 * 12 + 1)
    e, d = resolve("HOK3", pd.Timestamp("2013-01-02"), exp)
    check("HOK3 on 2013-01-02 is May 2013, the first ULSD delivery", d == ULSD_FIRST)
    check("delivery labels: December and January decode", dlv_label(2016 * 12 + 12) == "2016-12"
          and dlv_label(2017 * 12 + 1) == "2017-01")

    cl_exp = pd.Series({2020 * 12 + m: pd.Timestamp(2020, m - 1 if m > 1 else 1, 20) for m in range(2, 13)})
    for t in pd.date_range("2020-01-06", "2020-08-31", freq="7D"):
        for h in HORIZONS:
            ms = m_star(t, h, cl_exp)
            if ms is not None and not cl_exp[ms] >= t + pd.Timedelta(weeks=h + 1):
                raise AssertionError("m* expires inside the horizon")
    check("m* never selects a contract expiring inside h + 1 weeks", True)

    cb = pd.DataFrame({"cbar": [10.0, 12.0, 14.0, 99.0], "n": [5, 5, 5, 5],
                       "last": pd.to_datetime(["2016-04-01", "2017-04-01", "2018-04-01", "2019-04-01"])},
                      index=[2016 * 12 + 5, 2017 * 12 + 5, 2018 * 12 + 5, 2019 * 12 + 5])
    s, last = norm(2019 * 12 + 5, cb, "321")
    check("the norm for May 2019 is the mean of 2016-2018 and never 2019's own", s == 12.0 and last.year == 2018)
    check("the norm refuses a pre-ULSD HO delivery (May 2015 needs May 2012)", norm(2015 * 12 + 5, cb, "321") is None)
    check("the gasoline crack's norm does not need ULSD", norm(2019 * 12 + 5, cb, "gas") == (12.0, last))

    rng = np.random.default_rng(652)
    x = rng.normal(size=400)
    parts = [rng.normal(size=400) - 0.1 * x for _ in range(3)]
    y = sum(parts)
    check("three leg slopes sum to the total slope to 1e-9", abs(sum(slope(x, q) for q in parts) - slope(x, y)) < 1e-9)
    ks, _ = rotation(x, y)
    check("the rotation excludes the purged offsets", ks.min() == PURGE + 1 and ks.max() == len(x) - PURGE - 1)
    b, se_nw, se_ols = nw_se(x, rng.normal(size=400), lags=4)
    check(f"on iid data Newey-West se is close to OLS se ({se_nw:.4f} vs {se_ols:.4f})", abs(se_nw / se_ols - 1) < 0.25)

    # the premise test can fire both ways: an AR(1) deviation that reverts, and a random walk that does not
    n = 420
    dev = np.zeros(n)
    for i in range(1, n):
        dev[i] = 0.9 * dev[i - 1] + rng.normal()
    y_rev = np.roll(dev, -4) - dev
    y_rev[-4:] = 0
    b1, s1, _ = nw_se(dev[:-4], y_rev[:-4], 4)
    ks, rb = rotation(dev[:-4], y_rev[:-4])
    check(f"a reverting deviation reads beta < 0 at t {b1 / s1:.1f} and below its rotation p05",
          b1 < 0 and b1 / s1 <= -2 and b1 < np.percentile(rb, 5))
    rw = np.cumsum(rng.normal(size=n))
    y_rw = rng.normal(size=n - 4)
    b2, s2, _ = nw_se(rw[:-4], y_rw, 4)
    check(f"an unrelated target reads no reversion (t {b2 / s2:+.1f})", abs(b2 / s2) < 2.5)

    bad = pd.DataFrame({"root": ["CL"], "contract": ["CLF4"], "ref": ["2024-01-02"], "settle": [70.0]})
    must_raise("a 2024 settlement past the loader", lambda: assert_none_at_or_after(bad, "ref", RESERVED_FROM))
    check("the loader drops it", len(filter_before(bad, "ref", RESERVED_FROM)) == 0)
    P(f"selftest: {n_ok} checks")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args()
    return selftest() if a.selftest else run()


if __name__ == "__main__":
    sys.exit(main())
