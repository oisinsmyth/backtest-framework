"""D555 -- time-series momentum AS PUBLISHED (Moskowitz, Ooi & Pedersen 2012) on the 36-root breadth
fixture, checked against AQR's own monthly factor series.

Spec committed in 5ed655b BEFORE this file (R8). Primary window 2016-01-04..2023-12-29; the long
window 2011-01-03..2023-12-29 is a declared diagnostic; the 2024+ slice is RESERVED AND NOT READ.
Nothing admitted (R15).

    uv run python scripts/run_d555_tsmom_replication.py --selftest
    uv run --with openpyxl python scripts/run_d555_tsmom_replication.py --run   # -> data/d555_tsmom_replication.json
    (openpyxl is only needed to read AQR's .xlsx; it is not a project dependency)

One construction, nothing tuned: at each month-end, sign of the trailing 12-month return, sized to
40% ex-ante vol (EW variance, centre of mass 60 days), held one month; the portfolio is the equal
average of the scaled single-root returns. Ten declared cells ({12m, 3m, 1m, 3+12, 1+3+12} x
{return-space book, dollar book at minimum size}); N1 is the EXACT enumerated sign rotation within
each root's live span, N2 the family maximum at each offset. Three audits, each proven to raise.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
FIX = REPO / "data" / "fixtures" / "fut_breadth_hourly.csv.gz"
META = REPO / "data" / "fixtures" / "fut_breadth_hourly.meta.json"
SPECS = REPO / "data" / "futures_contract_specs.json"
AQR = REPO / "data" / "raw" / "aqr" / "Time-Series-Momentum-Factors-Monthly.xlsx"
OUT = REPO / "data" / "d555_tsmom_replication.json"
SPEC = "5ed655b"

SEGS = ["h18", "h19", "h20", "h21", "h22", "h23", "h00", "h01", "h02", "h03", "h04", "h05", "h06",
        "h07", "h08", "h09", "h10", "h11", "h12", "h13", "h14", "h15", "h16"]
PRIMARY = ("2016-01-04", "2023-12-29")
LONG = ("2011-01-03", "2023-12-29")
RESERVED_FROM = "2024-01-01"                       # never read
ERAS = [("2011-01-03", "2015-12-31"), ("2016-01-04", "2019-12-31"), ("2020-01-02", "2023-12-29")]
LOOKBACKS = {"12m": (12,), "3m": (3,), "1m": (1,), "3+12": (3, 12), "1+3+12": (1, 3, 12)}
PRIMARY_CELL = ("12m", "published")
VOL_TARGET = 0.40
COM = 60.0                                        # MOP centre of mass, days
DELTA = COM / (COM + 1.0)                          # 60/61
ANN = 261.0                                        # MOP annualisation of the EW variance
MIN_RET_IN_WINDOW = 240                            # per 12 months; scaled by L/12 for shorter lookbacks
MIN_VOL_OBS = 60
MIN_SESSIONS_YEAR = 240                            # live-span rule
DOLLAR_EXCLUDED = ("BZ", "SR3")                    # roll count > 24 a year; declared in the pre-reg
C_D_SIGMA = 500.0                                  # 1% of a $50k account
COMMISSION_RT = {"micro": 3.0, "full": 6.0}       # D468's convention
N_BOOT, SEED = 1000, 20260919
NULL_PURGE = 252                                   # one 12-month lookback, in sessions; see run()
SECTOR = {"EQ": ["ES", "NQ", "YM", "RTY", "NKD"], "FX": ["6A", "6B", "6C", "6E", "6J", "6S"],
          "FI": ["ZT", "ZF", "ZN", "TN", "ZB", "UB", "SR3"],
          "CM": ["CL", "BZ", "HO", "RB", "NG", "GC", "SI", "HG", "PL", "PA", "ZC", "ZS", "ZW", "ZL",
                 "ZM", "LE", "HE"], "OTHER": ["BTC"]}
# minimum tradable size per root: the micro where CME lists one (data/futures_contract_specs.json),
# the full contract otherwise. usd_per_point is in the FIXTURE's price units (the meta's tick_usd /
# tick_price_units reproduces every root's notional; see the pre-reg's probe).
MICRO_OF = {"ES": "MES", "NQ": "MNQ", "RTY": "M2K", "YM": "MYM", "CL": "MCL", "GC": "MGC",
            "6E": "M6E", "BTC": "MBT", "SI": "SIL", "NG": "MNG", "HG": "MHG"}
LIVE_START_DECLARED = {"TN": 2016, "BTC": 2018, "RTY": 2018, "SR3": 2019}   # every other root 2011

REQUIRED_OUTPUTS = ["spec", "commit", "fixture_sha256", "aqr_sha256", "windows", "live_start",
                    "roll_counts", "nonpositive_closes", "cells", "primary", "null_n1", "null_n2",
                    "per_root", "per_sector", "per_era", "per_year", "aqr", "dollar_book",
                    "predictions", "verdict", "audits", "timing"]


# --------------------------------------------------------------------------------------------
# data
# --------------------------------------------------------------------------------------------
def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_fixture():
    cols = ["root", "day", "contract", "same_front", "h18_o"] + [s + "_c" for s in SEGS]
    df = pd.read_csv(FIX, usecols=cols)
    C = df[[s + "_c" for s in SEGS]].to_numpy(dtype=float)
    fin = np.isfinite(C)
    has = fin.any(1)
    last_idx = C.shape[1] - 1 - np.argmax(fin[:, ::-1], axis=1)
    close = np.where(has, C[np.arange(len(C)), np.clip(last_idx, 0, None)], np.nan)
    df = df[["root", "day", "contract", "same_front", "h18_o"]].copy()
    df["close"] = close
    df["year"] = df["day"].str[:4].astype(int)
    df = df[df["day"] < RESERVED_FROM]                       # the 2024+ slice is never read
    # THE FIXTURE CARRIES A PLACEHOLDER ROW FOR EVERY SUNDAY (0 bars, no close) and a few holiday
    # rows. A row with no finite close is not a session for that root: chaining returns across it
    # loses the Monday return every week (~18% of all returns; the first run of this script did).
    n_before = len(df)
    df = df[df["close"].notna()].copy()
    n_no_close = int(n_before - len(df))
    # ... and 69 WEEKEND-DATED STUBS: one or two hourly bars printed on a Sunday evening and labelled
    # as a Sunday session (seven dates, 18 roots). A session is never weekend-dated on this fixture;
    # a stub with more than a few hourly closes would be a real session and is refused, not dropped.
    wd = pd.to_datetime(df["day"]).dt.dayofweek
    wk = wd >= 5
    if wk.any():
        stub_cols = [s + "_c" for s in SEGS]
        raw = pd.read_csv(FIX, usecols=["root", "day"] + stub_cols)
        raw = raw.merge(df.loc[wk, ["root", "day"]], on=["root", "day"])
        worst = int(raw[stub_cols].notna().sum(axis=1).max())
        if worst > 3:
            raise AssertionError(f"a weekend-dated row carries {worst} hourly closes; that is a session, not a stub")
    df = df[~wk].copy()
    df.attrs["rows_dropped_no_close"] = n_no_close
    df.attrs["rows_dropped_weekend_stub"] = int(wk.sum())
    return df


def live_start_by_rule(df: pd.DataFrame) -> dict:
    """First calendar year from which every year through 2025 carries >= 240 finite closes. The
    reserved slice is not read here either: the rule was run once in the pre-registration probe over
    the full fixture, its answer is DECLARED in LIVE_START_DECLARED, and this function re-derives the
    2011 default on the readable years and asserts the declared exceptions are consistent."""
    tab = df[df["close"].notna()].groupby(["root", "year"]).size().unstack(fill_value=0)
    out = {}
    for r, row in tab.iterrows():
        yrs = sorted(int(y) for y in row.index if int(y) <= 2023)
        fc = None
        for y in yrs:
            if all(row[z] >= MIN_SESSIONS_YEAR for z in yrs if z >= y):
                fc = y
                break
        out[r] = fc
    for r, y in LIVE_START_DECLARED.items():
        if out[r] != y:
            raise AssertionError(f"live-start rule disagrees with the declared value on {r}: {out[r]} vs {y}")
    for r, y in out.items():
        if r not in LIVE_START_DECLARED and y != 2011:
            raise AssertionError(f"{r} live start {y}, pre-reg declared 2011")
    return out


def build_grids(df: pd.DataFrame, live_start: dict):
    roots = sorted(df["root"].unique())
    days = np.array(sorted(df["day"].unique()))
    T, n = len(days), len(roots)
    day_ix = {d: i for i, d in enumerate(days)}
    close = np.full((n, T), np.nan)
    rlog = np.full((n, T), np.nan)      # same-contract log return
    dP = np.full((n, T), np.nan)        # same-contract price change
    roll = np.zeros((n, T), dtype=bool)
    live = np.zeros((n, T), dtype=bool)
    nonpos = []
    for i, r in enumerate(roots):
        g = df[df["root"] == r].sort_values("day")
        c = g["close"].to_numpy(); o = g["h18_o"].to_numpy(); ct = g["contract"].to_numpy()
        d = g["day"].to_numpy(); yr = g["year"].to_numpy()
        ix = np.array([day_ix[x] for x in d])
        close[i, ix] = c
        lv = np.isfinite(c) & (yr >= live_start[r])
        live[i, ix] = lv
        # a roll is the CONTRACT LABEL changing between consecutive kept sessions -- read off the
        # rows that remain, not off `same_front`, which was set against the row before a dropped one
        same = np.r_[True, ct[1:] == ct[:-1]]
        roll[i, ix] = ~same
        for j in range(1, len(c)):
            if not (lv[j] and lv[j - 1]):
                continue
            if same[j]:
                a, b = c[j - 1], c[j]
            else:
                a, b = o[j], c[j]
            if not (np.isfinite(a) and np.isfinite(b)):
                continue
            dP[i, ix[j]] = b - a
            if a > 0 and b > 0:
                rlog[i, ix[j]] = math.log(b / a)
            else:
                nonpos.append((r, str(d[j]), float(a), float(b)))
    # span: the root's contiguous live window. A position is HELD across a session the root does not
    # trade (its own holiday); it is flat only outside the span. `live` (a finite close on the session)
    # is the mask for returns and volatility; `span` is the mask for positions.
    span = np.zeros((n, T), dtype=bool)
    for i in range(n):
        ix = np.flatnonzero(live[i])
        if ix.size:
            span[i, ix[0]:ix[-1] + 1] = True
    return dict(roots=roots, days=days, close=close, rlog=rlog, dP=dP, roll=roll, live=live, span=span,
                nonpositive=nonpos)


def month_ends(days: np.ndarray) -> np.ndarray:
    ym = np.array([d[:7] for d in days])
    return np.flatnonzero(np.r_[ym[1:] != ym[:-1], True])


# --------------------------------------------------------------------------------------------
# signal, vol, positions
# --------------------------------------------------------------------------------------------
def ew_vol(rlog: np.ndarray, live: np.ndarray) -> np.ndarray:
    """MOP: sigma^2_t = 261 * sum (1-d) d^i (r_{t-1-i} - rbar)^2, as the recursion m <- d m + (1-d) r,
    v <- d v + (1-d) (r - m)^2 over each root's finite returns; annualised sigma; NaN until 60 obs."""
    n, T = rlog.shape
    m = np.zeros(n); v = np.zeros(n); cnt = np.zeros(n, dtype=int)
    sig = np.full((n, T), np.nan)
    for t in range(T):
        r = rlog[:, t]
        ok = np.isfinite(r) & live[:, t]
        if ok.any():
            m[ok] = DELTA * m[ok] + (1.0 - DELTA) * r[ok]
            v[ok] = DELTA * v[ok] + (1.0 - DELTA) * (r[ok] - m[ok]) ** 2
            cnt[ok] += 1
        good = cnt >= MIN_VOL_OBS
        sig[good, t] = np.sqrt(ANN * v[good])
    return sig


def ew_vol_loop(r: np.ndarray, lv: np.ndarray) -> np.ndarray:
    """Pure-Python reference for one root; must be BIT-IDENTICAL to ew_vol's row."""
    m = 0.0; v = 0.0; c = 0
    out = np.full(len(r), np.nan)
    for t in range(len(r)):
        if np.isfinite(r[t]) and lv[t]:
            m = DELTA * m + (1.0 - DELTA) * r[t]
            v = DELTA * v + (1.0 - DELTA) * (r[t] - m) ** 2
            c += 1
        if c >= MIN_VOL_OBS:
            out[t] = math.sqrt(ANN * v)
    return out


def _window_start(days: np.ndarray, m_ix: int, L: int) -> int:
    """First session index of the calendar month L-1 months before the month-end's month, so the
    window is exactly the L calendar months ending with the month-end's own month."""
    p = pd.Timestamp(str(days[m_ix])).to_period("M") - (L - 1)
    lo = p.start_time.strftime("%Y-%m-%d")
    return int(np.searchsorted(days, lo, side="left"))


def signal_at_month_ends(rlog, live, days, me, L: int):
    """Implementation A (numpy cumulative sums). sign[i, k] for month-end k; 0 when < 240*L/12 returns
    or the root is not live at the month-end."""
    n, T = rlog.shape
    fin = np.isfinite(rlog) & live
    r0 = np.where(fin, rlog, 0.0)
    cs = np.concatenate([np.zeros((n, 1)), np.cumsum(r0, axis=1)], axis=1)
    cc = np.concatenate([np.zeros((n, 1), dtype=int), np.cumsum(fin, axis=1)], axis=1)
    need = int(round(MIN_RET_IN_WINDOW * L / 12))
    sign = np.zeros((n, len(me)), dtype=int)
    tot = np.full((n, len(me)), np.nan)
    for k, m_ix in enumerate(me):
        a = _window_start(days, m_ix, L)
        s = cs[:, m_ix + 1] - cs[:, a]
        c = cc[:, m_ix + 1] - cc[:, a]
        ok = (c >= need) & live[:, m_ix]
        tot[ok, k] = s[ok]
        sign[ok, k] = np.sign(s[ok]).astype(int)
    return sign, tot


def signal_pandas(rlog, live, days, roots, me, L: int):
    """Implementation B: pandas, per root, resample to calendar months, rolling L-month sum and count,
    sign, evaluated at the month-ends. Never calls signal_at_month_ends."""
    idx = pd.to_datetime(days)
    out = np.zeros((len(roots), len(me)), dtype=int)
    need = int(round(MIN_RET_IN_WINDOW * L / 12))
    me_periods = [pd.Timestamp(str(days[m])).to_period("M") for m in me]
    for i in range(len(roots)):
        s = pd.Series(np.where(live[i], rlog[i], np.nan), index=idx)
        ms = s.resample("ME").sum(min_count=1)
        mc = s.resample("ME").count()
        rs = ms.fillna(0.0).rolling(L, min_periods=1).sum()
        rc = mc.rolling(L, min_periods=1).sum()
        rs.index = rs.index.to_period("M"); rc.index = rc.index.to_period("M")
        for k, p in enumerate(me_periods):
            if p in rs.index and rc[p] >= need and live[i, me[k]]:
                out[i, k] = int(np.sign(rs[p]))
    return out


def hold_from_month_ends(vals_at_me: np.ndarray, me: np.ndarray, T: int, live: np.ndarray):
    """Held grid: session t carries the value set at the last month-end STRICTLY before t."""
    n = vals_at_me.shape[0]
    held = np.zeros((n, T), dtype=vals_at_me.dtype)
    for k, m_ix in enumerate(me):
        end = me[k + 1] if k + 1 < len(me) else T - 1
        held[:, m_ix + 1:end + 1] = vals_at_me[:, k][:, None]
    held = np.where(live, held, 0)
    return held


def build_positions(g, sig, me, combo):
    """Returns (sign_held, pos_pub, sign_dollar) for one lookback combination."""
    n, T = g["rlog"].shape
    signs = []
    for L in combo:
        s, _ = signal_at_month_ends(g["rlog"], g["live"], g["days"], me, L)
        signs.append(s)
    avg = np.mean(np.stack(signs), axis=0)                    # in {-1..+1}, the ensemble
    scale_me = np.where(np.isfinite(sig[:, me]) & (sig[:, me] > 0), VOL_TARGET / sig[:, me], 0.0)
    pos_me = avg * scale_me
    dollar_me = np.sign(np.sum(np.stack(signs), axis=0)).astype(int)
    sign_held = hold_from_month_ends(avg, me, T, g["span"])          # float ensemble sign
    pos_pub = hold_from_month_ends(pos_me, me, T, g["span"])
    scale_held = hold_from_month_ends(scale_me, me, T, g["span"])
    sign_dollar = hold_from_month_ends(dollar_me, me, T, g["span"])
    return sign_held, pos_pub, scale_held, sign_dollar


# --------------------------------------------------------------------------------------------
# scoring
# --------------------------------------------------------------------------------------------
def book_return(pos: np.ndarray, rsimple: np.ndarray) -> np.ndarray:
    """Equal average over the roots with a non-zero position of pos x simple return. Root-order
    sequential accumulation so the enumerated null and the plain loop agree bit for bit."""
    n, T = pos.shape
    acc = np.zeros(T); cnt = np.zeros(T)
    for i in range(n):
        p = pos[i]
        acc += p * rsimple[i]
        cnt += (p != 0.0)
    return np.where(cnt > 0, acc / np.where(cnt > 0, cnt, 1.0), 0.0)


def book_return_loop(pos, rsimple):
    n, T = pos.shape
    out = np.zeros(T)
    for t in range(T):
        acc = 0.0; c = 0
        for i in range(n):
            acc += pos[i, t] * rsimple[i, t]
            c += (pos[i, t] != 0.0)
        out[t] = acc / c if c > 0 else 0.0
    return out


def sharpe(x: np.ndarray, ppy: float = 252.0) -> float:
    sd = x.std(ddof=1)
    return float(x.mean() / sd * math.sqrt(ppy)) if sd > 0 else float("nan")


def block_boot_se(x: np.ndarray, days: np.ndarray, n_boot=N_BOOT, seed=SEED) -> float:
    ym = np.array([d[:7] for d in days])
    blocks = [np.flatnonzero(ym == u) for u in np.unique(ym)]
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_boot):
        pick = rng.integers(0, len(blocks), len(blocks))
        vals.append(sharpe(np.concatenate([x[blocks[b]] for b in pick])))
    return float(np.std(vals, ddof=1))


def window_mask(days, lo, hi):
    return (days >= lo) & (days <= hi)


def cost_bp_per_side(g, upp, comm_rt, tick_usd):
    """bp of notional per side at minimum size, per root per session, at that session's close."""
    notional = g["close"] * upp[:, None]
    return np.where(np.isfinite(notional) & (notional > 0),
                    (comm_rt[:, None] / 2.0 + 0.5 * tick_usd[:, None]) / notional, np.nan)


def published_cost(pos, cbp, roll):
    """Return-space cost: turnover in weight units x bp per side; and the roll add-on separately."""
    n, T = pos.shape
    cnt = (pos != 0.0).sum(0)
    w = pos / np.where(cnt > 0, cnt, 1.0)[None, :]
    dw = np.abs(np.diff(w, axis=1, prepend=0.0))
    c = np.where(np.isfinite(cbp), cbp, 0.0)
    turnover = (dw * c).sum(0)
    rolls = (2.0 * np.abs(w) * c * roll).sum(0)
    return turnover, rolls, np.abs(dw).sum(0)


def dollar_book(sign_dollar, g, upp, comm_rt, tick_usd, roots_in):
    """One minimum-size contract per root per sign. Cost per SIDE = comm_rt/2 + 0.5 tick; a sign
    change is |delta sign| sides, a front change while positioned is two sides."""
    n, T = sign_dollar.shape
    dP0 = np.where(np.isfinite(g["dP"]), g["dP"], 0.0)
    keep = np.array([r in roots_in for r in g["roots"]])
    s = np.where(keep[:, None], sign_dollar, 0)
    gross = s * dP0 * upp[:, None]
    sides = np.abs(np.diff(s, axis=1, prepend=0)) + 2 * (g["roll"] & (s != 0))
    cost = sides * (comm_rt[:, None] / 2.0 + 0.5 * tick_usd[:, None])
    return gross, cost, sides


def stats_block(x, days, label):
    return {"label": label, "n_days": int(len(x)), "sharpe": sharpe(x), "mean_daily": float(x.mean()),
            "sd_daily": float(x.std(ddof=1)), "ann_vol": float(x.std(ddof=1) * math.sqrt(252)),
            "total": float(x.sum()), "hit": float((x > 0).mean()),
            "skew": float(pd.Series(x).skew()), "kurt": float(pd.Series(x).kurt()),
            "max_dd": float(max_drawdown(x)), "se": block_boot_se(x, days)}


def max_drawdown(x):
    c = np.cumsum(x); peak = np.maximum.accumulate(c)
    return float((c - peak).min())


# --------------------------------------------------------------------------------------------
# audits
# --------------------------------------------------------------------------------------------
def audit_lag(sign_held, sign_me_pandas, me, live, T):
    """The held grid must equal the pandas-derived month-end signs shifted to the session after the
    month-end -- rebuilt here with a second, independent hold, never via hold_from_month_ends."""
    n = sign_held.shape[0]
    ref = np.zeros((n, T))
    for k in range(len(me)):
        lo = me[k] + 1
        hi = me[k + 1] if k + 1 < len(me) else T - 1
        for t in range(lo, hi + 1):
            ref[:, t] = sign_me_pandas[:, k]
    ref = np.where(live, ref, 0.0)
    bad = np.flatnonzero((ref != sign_held).any(0))
    if bad.size:
        raise AssertionError(f"LAG AUDIT: held sign grid differs from the independent derivation on "
                             f"{bad.size} sessions (first at index {bad[0]})")
    return int((ref != 0).sum())


def audit_sign_in_money(gross, sign_dollar, g, upp):
    """In money, on the SCORED grid: on each root's largest positive same-contract move, the book's
    dollar P&L that session must be +dP x usd_per_point if it was long and -dP x usd_per_point if it
    was short. The audit reads the GROSS grid the scorer produced, not the positions, so the only
    thing that can break it is the P&L machinery -- a negated grid, or one built from a mis-lagged
    price change -- which is exactly what the self-test breaks."""
    n, T = sign_dollar.shape
    checked = 0
    for i in range(n):
        d = np.where(np.isfinite(g["dP"][i]), g["dP"][i], -np.inf)
        t = int(np.argmax(d))
        if not np.isfinite(g["dP"][i, t]) or g["dP"][i, t] <= 0:
            continue
        s = sign_dollar[i, t]
        if s == 0:
            continue
        want = s * g["dP"][i, t] * upp[i]
        if gross[i, t] != want:
            raise AssertionError(f"SIGN AUDIT: {g['roots'][i]} on its best day: book pays {gross[i, t]:+.2f}, "
                                 f"a {'long' if s > 0 else 'short'} must pay {want:+.2f}")
        if s > 0 and not gross[i, t] > 0:
            raise AssertionError(f"SIGN AUDIT: long {g['roots'][i]} on a rise pays {gross[i, t]:+.2f}")
        checked += 1
    if checked == 0:
        raise AssertionError("SIGN AUDIT: nothing checked")
    return checked


def audit_sign_book(gross, sign_dollar, g, upp):
    """Money version on the SCORED book: the gross grid must equal sign x dP x upp cell by cell, and a
    favourable move must pay positively."""
    dP0 = np.where(np.isfinite(g["dP"]), g["dP"], 0.0)
    want = sign_dollar * dP0 * upp[:, None]
    fav = (sign_dollar * dP0) > 0
    if not (gross[fav] > 0).all():
        raise AssertionError("SIGN AUDIT (book): a favourable move paid non-positively")
    if not np.array_equal(gross, want):
        raise AssertionError("SIGN AUDIT (book): gross grid != sign x dP x usd_per_point")


def audit_right_quantity(sign_held, me, T):
    """The held grid may change only on the session after a month-end."""
    allowed = np.zeros(T, dtype=bool)
    allowed[np.clip(me + 1, 0, T - 1)] = True
    ch = (np.diff(sign_held, axis=1) != 0).any(0)          # change at t means sign[t] != sign[t-1]
    offending = np.flatnonzero(ch & ~allowed[1:])
    if offending.size:
        raise AssertionError(f"RIGHT-QUANTITY AUDIT: the held grid changes on {offending.size} sessions "
                             f"that are not the first after a month-end")
    return int(ch.sum())


# --------------------------------------------------------------------------------------------
# the enumerated null
# --------------------------------------------------------------------------------------------
def rotate_signs(sign_held, live_idx, k):
    """Rotate each root's held-sign series by k within its own live index set (k mod its length)."""
    out = np.zeros_like(sign_held)
    for i, idx in enumerate(live_idx):
        if idx.size == 0:
            continue
        s = sign_held[i, idx]
        out[i, idx] = np.roll(s, k % idx.size)
    return out


def enumerate_null(cells, g, live_idx, w, rsimple, upp, comm_rt, tick_usd, dollar_roots, log):
    """For every offset k in 1..L-1: each cell's Sharpe on the window. Returns (L-1) x n_cells."""
    T_w = int(w.sum())
    keys = list(cells.keys())
    out = np.full((T_w - 1, len(keys)), np.nan)
    t0 = time.time()
    for k in range(1, T_w):
        for j, key in enumerate(keys):
            c = cells[key]
            s_rot = rotate_signs(c["sign_held"], live_idx, k)
            if c["book"] == "published":
                pos = s_rot * c["scale_held"]
                x = book_return(pos, rsimple)[w]
            else:
                sd = np.sign(s_rot).astype(int)
                gross, cost, _ = dollar_book(sd, g, upp, comm_rt, tick_usd, dollar_roots)
                x = (gross - cost).sum(0)[w]
            out[k - 1, j] = sharpe(x)
        if k % 500 == 0:
            log(f"    null offset {k}/{T_w - 1}  {time.time() - t0:.0f}s")
    return out, keys


# --------------------------------------------------------------------------------------------
# run
# --------------------------------------------------------------------------------------------
def run(log=print):
    t_start = time.time()
    log(f"D555 -- TSMOM as published, 36 roots\n      spec {SPEC} committed BEFORE this runner (R8)\n"
        f"      primary {PRIMARY[0]}..{PRIMARY[1]}; long {LONG[0]}..{LONG[1]}; 2024+ NOT READ")
    df = load_fixture()
    if (df["day"] >= RESERVED_FROM).any():
        raise AssertionError("reserved slice present after filtering")
    live_start = live_start_by_rule(df)
    g = build_grids(df, live_start)
    roots, days = g["roots"], g["days"]
    n, T = g["rlog"].shape
    log(f"  fixture: {n} roots x {T} sessions {days[0]}..{days[-1]}; non-positive closes: {len(g['nonpositive'])}; "
        f"placeholder rows dropped: {df.attrs['rows_dropped_no_close']}; weekend stubs dropped: {df.attrs['rows_dropped_weekend_stub']}")
    fin_share = (np.isfinite(g["rlog"]) & g["live"]).sum() / max(g["live"].sum(), 1)
    if fin_share < 0.97:
        raise AssertionError(f"only {fin_share:.1%} of live sessions carry a return; the chain is broken")
    for r, d, a, b in g["nonpositive"]:
        log(f"    {r} {d}: {a} -> {b} (log return undefined; return-space contribution 0, dollar P&L kept)")

    meta = json.load(open(META)); specs = json.load(open(SPECS))
    upp = np.zeros(n); tick_usd = np.zeros(n); comm_rt = np.zeros(n); size_name = []
    for i, r in enumerate(roots):
        sp = meta["specs"][r]
        full_upp = sp["tick_usd_full_contract"] / sp["tick_price_units"]     # in the FIXTURE's price units
        if r in MICRO_OF:
            if MICRO_OF[r] in specs:
                m = specs[MICRO_OF[r]]
                upp[i] = m["usd_per_point"]; tick_usd[i] = m["tick_usd"]
            else:
                # MBT is absent from the specs file; the fixture meta carries the minimum-size tick the
                # builder resolved from the exchange definition (sized_as, tick_usd)
                if sp["sized_as"] != MICRO_OF[r]:
                    raise AssertionError(f"{r}: meta sized_as {sp['sized_as']} != {MICRO_OF[r]}")
                upp[i] = sp["tick_usd"] / sp["tick_price_units"]; tick_usd[i] = sp["tick_usd"]
            comm_rt[i] = COMMISSION_RT["micro"]; size_name.append(MICRO_OF[r])
            # the micro quotes the parent's price units: its usd_per_point must be a fixed fraction of
            # the full contract's, and where the specs file carries the parent, the parent must agree
            # with the fixture's own scaling to the ULP
            if r in specs and abs(specs[r]["usd_per_point"] - full_upp) > 1e-9 * full_upp:
                raise AssertionError(f"{r}: specs usd_per_point {specs[r]['usd_per_point']} != fixture-derived {full_upp}")
            if not (0.005 <= upp[i] / full_upp <= 0.5):
                raise AssertionError(f"{r}: micro/full ratio {upp[i] / full_upp} is not a CME micro ratio")
        else:
            upp[i] = full_upp
            tick_usd[i] = sp["tick_usd"]; comm_rt[i] = COMMISSION_RT["full"]; size_name.append(r)
    log(f"  minimum size: " + ", ".join(f"{r}:{s}" for r, s in zip(roots, size_name)))

    me = month_ends(days)
    sig = ew_vol(g["rlog"], g["live"])
    for i in [roots.index("ES"), roots.index("ZN"), roots.index("CL")]:
        ref = ew_vol_loop(g["rlog"][i], g["live"][i])
        if not np.array_equal(np.nan_to_num(ref, nan=-1), np.nan_to_num(sig[i], nan=-1)):
            raise AssertionError(f"EW vol is not bit-identical to the loop on {roots[i]}")
    rsimple = np.where(np.isfinite(g["rlog"]), np.expm1(np.nan_to_num(g["rlog"])), 0.0)

    # cells
    cells = {}
    for lb, combo in LOOKBACKS.items():
        sign_held, pos_pub, scale_held, sign_dollar = build_positions(g, sig, me, combo)
        cells[(lb, "published")] = dict(book="published", sign_held=sign_held, scale_held=scale_held, pos=pos_pub)
        cells[(lb, "dollar")] = dict(book="dollar", sign_held=sign_dollar.astype(float), scale_held=None, pos=None)

    # audits on the primary cell
    audits = {}
    prim = cells[PRIMARY_CELL]
    s12_pd = signal_pandas(g["rlog"], g["live"], days, roots, me, 12)
    audits["lag_held_cells"] = audit_lag(prim["sign_held"], s12_pd.astype(float), me, g["span"], T)
    s12_np, _ = signal_at_month_ends(g["rlog"], g["live"], days, me, 12)
    audits["lag_month_end_sign_agree"] = bool(np.array_equal(s12_np, s12_pd))
    if not audits["lag_month_end_sign_agree"]:
        raise AssertionError("month-end signs: numpy and pandas implementations disagree")
    audits["right_quantity_changes"] = audit_right_quantity(prim["sign_held"], me, T)
    daily_sign = np.sign(np.nan_to_num(np.cumsum(np.nan_to_num(g["rlog"]), axis=1)))
    try:
        audit_right_quantity(daily_sign, me, T); raise RuntimeError("right-quantity audit accepted a daily grid")
    except AssertionError:
        audits["right_quantity_raises_on_daily_grid"] = True
    sd12 = cells[("12m", "dollar")]["sign_held"].astype(int)
    gross12, _, _ = dollar_book(sd12, g, upp, comm_rt, tick_usd, roots)
    audits["sign_in_money_roots_checked"] = audit_sign_in_money(gross12, sd12, g, upp)
    try:
        audit_sign_in_money(-gross12, sd12, g, upp); raise RuntimeError("sign audit accepted a NEGATED gross grid")
    except AssertionError:
        audits["sign_raises_on_negated_grid"] = True
    g_lag = dict(g, dP=np.roll(g["dP"], 1, axis=1))          # P&L from the wrong session's move
    gross_lag, _, _ = dollar_book(sd12, g_lag, upp, comm_rt, tick_usd, roots)
    try:
        audit_sign_in_money(gross_lag, sd12, g, upp); raise RuntimeError("sign audit accepted a MIS-LAGGED grid")
    except AssertionError:
        audits["sign_raises_on_mislagged_grid"] = True
    # unlagged book must be rejected by the lag audit
    unlagged = np.zeros_like(prim["sign_held"])
    for k, m_ix in enumerate(me):
        lo = me[k - 1] + 1 if k > 0 else 0
        unlagged[:, lo:m_ix + 1] = s12_np[:, k][:, None]
    unlagged = np.where(g["span"], unlagged, 0.0)
    try:
        audit_lag(unlagged, s12_pd.astype(float), me, g["span"], T); raise RuntimeError("lag audit accepted an UNLAGGED book")
    except AssertionError:
        audits["lag_raises_on_unlagged_book"] = True
    # scored P&L differs from the unlagged one
    x_lag = book_return(prim["pos"], rsimple); x_unl = book_return(unlagged * prim["scale_held"], rsimple)
    audits["pnl_differs_from_unlagged"] = bool(not np.allclose(x_lag, x_unl))
    if not audits["pnl_differs_from_unlagged"]:
        raise AssertionError("lagged and unlagged P&L coincide")
    log(f"  audits: {audits}")

    # windows
    wP = window_mask(days, *PRIMARY); wL = window_mask(days, *LONG)
    dP_days, dL_days = days[wP], days[wL]
    cbp = cost_bp_per_side(g, upp, comm_rt, tick_usd)
    dollar_roots = [r for r in roots if r not in DOLLAR_EXCLUDED]

    # per-root sigma at minimum size (C-d), on the primary window, of the unsigned 1-contract P&L
    root_sigma = {}
    for i, r in enumerate(roots):
        d = g["dP"][i][wP]; d = d[np.isfinite(d)] * upp[i]
        root_sigma[r] = float(d.std(ddof=1)) if d.size > 30 else float("nan")
    cd_roots = [r for r in dollar_roots if np.isfinite(root_sigma[r]) and root_sigma[r] <= C_D_SIGMA]

    results_cells = {}
    scored = {}
    for key, c in cells.items():
        lb, book = key
        name = f"{lb}/{book}"
        if book == "published":
            x = book_return(c["pos"], rsimple)
            turn, rolls, tw = published_cost(c["pos"], cbp, g["roll"])
            xn = x - turn
            entry = {"gross": stats_block(x[wP], dP_days, name), "net": stats_block(xn[wP], dP_days, name + " net"),
                     "net_incl_rolls": sharpe((x - turn - rolls)[wP]),
                     "ann_turnover_weight_units": float(tw[wP].sum() / (wP.sum() / 252)),
                     "cost_ann_bp": float(turn[wP].sum() / (wP.sum() / 252) * 1e4),
                     "breakeven_bp_per_side": float(x[wP].mean() / max(tw[wP].mean(), 1e-12) * 1e4),
                     "gross_long": stats_block(x[wL], dL_days, name + " 2011-2023")}
            scored[key] = dict(gross=x, net=xn)
        else:
            # scored on the grid MASKED to the window, exactly as the null is: the book enters on the
            # window's first session and pays that side, observed and null alike
            sP = np.where(wP[None, :], c["sign_held"], 0.0).astype(int)
            sL = np.where(wL[None, :], c["sign_held"], 0.0).astype(int)
            gross, cost, sides = dollar_book(sP, g, upp, comm_rt, tick_usd, dollar_roots)
            gb, cb = gross.sum(0), cost.sum(0)
            xg, xn = gb, gb - cb
            g_cd, c_cd, _ = dollar_book(sP, g, upp, comm_rt, tick_usd, cd_roots)
            gL, _, _ = dollar_book(sL, g, upp, comm_rt, tick_usd, dollar_roots)
            entry = {"gross": stats_block(xg[wP], dP_days, name), "net": stats_block(xn[wP], dP_days, name + " net"),
                     "cost_total": float(cb[wP].sum()), "sides_total": int(sides[:, wP].sum()),
                     "roll_sides_total": int((2 * (g["roll"] & (sP != 0)))[:, wP].sum()),
                     "cd_subset": {"roots": cd_roots, "gross": stats_block(g_cd.sum(0)[wP], dP_days, name + " C-d subset"),
                                   "net": stats_block((g_cd - c_cd).sum(0)[wP], dP_days, name + " C-d subset net")},
                     "gross_long": stats_block(gL.sum(0)[wL], dL_days, name + " 2011-2023 $")}
            scored[key] = dict(gross=xg, net=xn)
            if key == ("12m", "dollar"):
                audit_sign_book(gross, np.where(np.array([r in dollar_roots for r in roots])[:, None], sP, 0), g, upp)
        results_cells[name] = entry
        log(f"  {name:16s} gross SR {entry['gross']['sharpe']:+.3f} (SE {entry['gross']['se']:.2f})  net {entry['net']['sharpe']:+.3f}")

    # primary diagnostics
    x = scored[PRIMARY_CELL]["gross"]; pos = prim["pos"]
    per_root = {}
    for i, r in enumerate(roots):
        xi = pos[i] * rsimple[i]
        live_i = (pos[i] != 0)
        per_root[r] = {"sharpe_long": sharpe(xi[wL & live_i]) if (wL & live_i).sum() > 60 else None,
                       "total_long": float(xi[wL].sum()), "total_primary": float(xi[wP].sum()),
                       "sharpe_primary": sharpe(xi[wP & live_i]) if (wP & live_i).sum() > 60 else None,
                       "live_start": live_start[r], "sessions_positioned_long": int((wL & live_i).sum()),
                       "rolls_2011_2023": int(g["roll"][i][wL].sum()), "sigma_usd_min_size": root_sigma[r],
                       "min_size": size_name[i]}
    n_pos = sum(1 for r in roots if per_root[r]["total_long"] > 0)
    n_pos_full = sum(1 for r in roots if live_start[r] == 2011 and per_root[r]["total_long"] > 0)
    per_sector = {}
    for sec, lst in SECTOR.items():
        ix = [roots.index(r) for r in lst if r in roots]
        xs = book_return(pos[ix], rsimple[ix])
        per_sector[sec] = {"roots": [roots[j] for j in ix], "sharpe_primary": sharpe(xs[wP]), "sharpe_long": sharpe(xs[wL])}
    per_era = {f"{a}..{b}": {"sharpe": sharpe(x[window_mask(days, a, b)]), "n_days": int(window_mask(days, a, b).sum())} for a, b in ERAS}
    yrs = sorted(set(d[:4] for d in days[wL]))
    per_year = {y: {"sharpe": sharpe(x[np.array([d[:4] == y for d in days])]), "total": float(x[np.array([d[:4] == y for d in days])].sum())} for y in yrs}

    # AQR check, monthly, 2011-01..2023-12 only
    aqr = pd.read_excel(AQR, sheet_name="TSMOM Factors", header=None)
    hdr = int(np.flatnonzero(aqr.iloc[:, 1].astype(str) == "TSMOM")[0])
    cols = ["date"] + [str(c) for c in aqr.iloc[hdr, 1:].tolist()]
    aq = aqr.iloc[hdr + 1:, :].copy(); aq.columns = cols
    aq["date"] = pd.to_datetime(aq["date"]); aq = aq.set_index("date").astype(float)
    aq["ym"] = aq.index.to_period("M"); aq = aq.set_index("ym")
    mine = pd.Series(x, index=pd.to_datetime(days))
    mine_m = (1.0 + mine).groupby(mine.index.to_period("M")).prod() - 1.0
    ov = [p for p in mine_m.index if pd.Period("2011-01", "M") <= p <= pd.Period("2023-12", "M") and p in aq.index]
    a = aq.loc[ov]; m = mine_m.loc[ov]
    aqr_out = {"file_sha256": sha256(AQR), "months": len(ov), "first": str(ov[0]), "last": str(ov[-1]),
               "corr_all": float(np.corrcoef(m.values, a["TSMOM"].values)[0, 1]),
               "aqr_sharpe_2011_2023": float(a["TSMOM"].mean() / a["TSMOM"].std(ddof=1) * math.sqrt(12)),
               "mine_monthly_sharpe_2011_2023": float(m.mean() / m.std(ddof=1) * math.sqrt(12)),
               "aqr_sharpe_2016_2023": float(a.loc[[p for p in ov if p >= pd.Period("2016-01", "M")], "TSMOM"].pipe(lambda s: s.mean() / s.std(ddof=1) * math.sqrt(12))),
               "sector": {}}
    for sec, col in [("CM", "TSMOM^CM"), ("EQ", "TSMOM^EQ"), ("FI", "TSMOM^FI"), ("FX", "TSMOM^FX")]:
        ix = [roots.index(r) for r in SECTOR[sec]]
        xs = pd.Series(book_return(pos[ix], rsimple[ix]), index=pd.to_datetime(days))
        xs_m = (1.0 + xs).groupby(xs.index.to_period("M")).prod() - 1.0
        aqr_out["sector"][sec] = float(np.corrcoef(xs_m.loc[ov].values, a[col].values)[0, 1])
    log(f"  AQR: corr {aqr_out['corr_all']:+.3f} over {len(ov)} months; sectors {aqr_out['sector']}")

    # the enumerated null, primary window
    live_idx = [np.flatnonzero(g["span"][i] & wP) for i in range(n)]
    null_cells = {k: dict(v, sign_held=np.where(wP[None, :], v["sign_held"], 0.0)) for k, v in cells.items()}
    log(f"  enumerating N1/N2 over {int(wP.sum()) - 1} offsets x {len(cells)} cells ...")
    # exactness guard: 20 offsets, vectorised vs plain loop, on the primary cell
    for k in (1, 7, 63, 250, 999, 1500, 1777, 2000, 2010, 3, 11, 101, 333, 444, 555, 666, 777, 888, 1234, 1999):
        k = k % (int(wP.sum()) - 1) or 1
        s_rot = rotate_signs(null_cells[PRIMARY_CELL]["sign_held"], live_idx, k)
        p = s_rot * prim["scale_held"]
        a1 = book_return(p, rsimple)[wP]; a2 = book_return_loop(p[:, wP], rsimple[:, wP])
        if not np.array_equal(a1, a2):
            raise AssertionError(f"enumeration is not bit-identical to the loop at offset {k}")
    log("  exactness guard: 20 offsets bit-identical against the plain loop")
    null_all, keys = enumerate_null(null_cells, g, live_idx, wP, rsimple, upp, comm_rt, tick_usd, dollar_roots, log)
    names = [f"{a}/{b}" for a, b in keys]
    obs = np.array([results_cells[nm]["gross"]["sharpe"] if b == "published" else results_cells[nm]["net"]["sharpe"]
                    for nm, (a, b) in zip(names, keys)])
    # the dollar cells are scored NET in the family (the component question); the published ones GROSS
    jP = keys.index(PRIMARY_CELL)
    # AMENDMENT TO THE PRE-REGISTERED NULL, made on the first run and recorded in the RESULT. The
    # pre-registration enumerated every offset 1..L-1. An offset k rotates the sign at t to the sign
    # from t+k (mod L): for k within one lookback of L the position carries a sign whose 12-month
    # window CONTAINS the returns being scored (look-ahead: the first run's best offset was L-95, and
    # it earned on all 36 roots at once, Sharpe ~ +1 each); for k within one lookback of 0 the
    # position is a slightly staler momentum signal, which is still momentum. Neither is a null for
    # this construction. Offsets within PURGE = 252 sessions of either end are excluded; the full
    # profile is kept as a diagnostic, and the un-purged percentiles are reported beside the purged.
    ks_all = np.arange(1, null_all.shape[0] + 1)
    keep = (ks_all >= NULL_PURGE) & (ks_all <= int(wP.sum()) - NULL_PURGE)
    null = null_all[keep]
    n1 = {"offsets_enumerated": int(null_all.shape[0]), "purge_sessions": NULL_PURGE,
          "offsets_after_purge": int(null.shape[0]), "per_cell": {}, "per_cell_unpurged": {},
          "offset_profile_primary": {"k": ks_all.tolist(), "sharpe": null_all[:, jP].tolist()}}
    for j, nm in enumerate(names):
        col = null[:, j]; raw = null_all[:, j]
        n1["per_cell"][nm] = {"observed": float(obs[j]), "p50": float(np.percentile(col, 50)),
                              "p95": float(np.percentile(col, 95)), "p05": float(np.percentile(col, 5)),
                              "pct_rank": float((col < obs[j]).mean()), "clears_p95": bool(obs[j] > np.percentile(col, 95))}
        n1["per_cell_unpurged"][nm] = {"p50": float(np.percentile(raw, 50)), "p95": float(np.percentile(raw, 95)),
                                       "p05": float(np.percentile(raw, 5)), "pct_rank": float((raw < obs[j]).mean()),
                                       "max": float(raw.max()), "argmax_k": int(ks_all[int(raw.argmax())])}
    fam = null.max(1); fam_raw = null_all.max(1)
    n2 = {"observed_best": float(obs.max()), "observed_best_cell": names[int(obs.argmax())],
          "p50": float(np.percentile(fam, 50)), "p95": float(np.percentile(fam, 95)),
          "pct_rank": float((fam < obs.max()).mean()), "clears_p95": bool(obs.max() > np.percentile(fam, 95)),
          "unpurged": {"p50": float(np.percentile(fam_raw, 50)), "p95": float(np.percentile(fam_raw, 95)),
                       "pct_rank": float((fam_raw < obs.max()).mean())}}
    primary = n1["per_cell"][f"{PRIMARY_CELL[0]}/{PRIMARY_CELL[1]}"]
    log(f"  UNPURGED null (as pre-registered, contaminated): primary p50 {n1['per_cell_unpurged'][names[jP]]['p50']:+.3f} "
        f"p95 {n1['per_cell_unpurged'][names[jP]]['p95']:+.3f}, max {n1['per_cell_unpurged'][names[jP]]['max']:+.3f} at k={n1['per_cell_unpurged'][names[jP]]['argmax_k']}")
    log(f"  N1 primary: observed {primary['observed']:+.3f}  p50 {primary['p50']:+.3f}  p95 {primary['p95']:+.3f}  "
        f"rank {primary['pct_rank']:.3f}\n  N2 family: best {n2['observed_best']:+.3f} ({n2['observed_best_cell']})  "
        f"p50 {n2['p50']:+.3f}  p95 {n2['p95']:+.3f}")

    # predictions
    c12 = results_cells["12m/published"]; c3 = results_cells["3m/published"]; c1 = results_cells["1m/published"]
    d12 = results_cells["12m/dollar"]
    era_keys = list(per_era.keys())
    preds = {
        "P-1": {"claim": "12m published gross Sharpe 2016-2023 > 0 and above N1 p95; point 0.4-0.8",
                "value": c12["gross"]["sharpe"], "p95": primary["p95"],
                "holds": bool(c12["gross"]["sharpe"] > 0 and primary["clears_p95"]),
                "in_point_range": bool(0.4 <= c12["gross"]["sharpe"] <= 0.8)},
        "P-2": {"claim": "monthly corr with AQR TSMOM 2011-2023 >= 0.5; point ~0.7", "value": aqr_out["corr_all"],
                "holds": bool(aqr_out["corr_all"] >= 0.5)},
        "P-3": {"claim": "12m > 3m > 1m gross Sharpe 2016-2023, and 1m < 0.3",
                "values": [c12["gross"]["sharpe"], c3["gross"]["sharpe"], c1["gross"]["sharpe"]],
                "holds": bool(c12["gross"]["sharpe"] > c3["gross"]["sharpe"] > c1["gross"]["sharpe"] and c1["gross"]["sharpe"] < 0.3)},
        "P-4": {"claim": "12m gross P&L positive on >= 21 roots over 2011-2023", "n_positive_all36": n_pos,
                "n_positive_of_32_full_span": n_pos_full, "holds": bool(n_pos >= 21)},
        "P-5": {"claim": "dollar book net Sharpe 0.3-0.7, gross-net < 0.1, full book fails C-d",
                "net": d12["net"]["sharpe"], "gross": d12["gross"]["sharpe"], "sigma_daily": d12["net"]["sd_daily"],
                "holds": bool(0.3 <= d12["net"]["sharpe"] <= 0.7 and (d12["gross"]["sharpe"] - d12["net"]["sharpe"]) < 0.1
                              and d12["net"]["sd_daily"] > C_D_SIGMA)},
        "P-6": {"claim": "2016-2019 weakest era (< 0.3), 2020-2023 strongest",
                "eras": {k: v["sharpe"] for k, v in per_era.items()},
                "holds": bool(per_era[era_keys[1]]["sharpe"] < 0.3 and
                              per_era[era_keys[1]]["sharpe"] == min(v["sharpe"] for v in per_era.values()) and
                              per_era[era_keys[2]]["sharpe"] == max(v["sharpe"] for v in per_era.values()))},
        "P-7": {"claim": "falsifier: primary below N1 p50 with P-2 holding -> trend did badly here; P-2 failing -> layer wrong",
                "primary_below_p50": bool(c12["gross"]["sharpe"] < primary["p50"]), "p2_holds": bool(aqr_out["corr_all"] >= 0.5)},
    }
    verdict = ("PASS" if (c12["gross"]["sharpe"] > 0 and primary["clears_p95"] and n2["clears_p95"]) else "DOES NOT PASS")
    harness = ("HARNESS OK" if aqr_out["corr_all"] >= 0.5 else "HARNESS SUSPECT")

    res = {"max_drawdown_convention": {
               "sign": "negative",
               "note": "Drawdown LEVELS in this file are NEGATIVE: for the published book the minimum of "
                       "(cumulative daily return - its running peak), a fraction of NAV in simple-return "
                       "units (a -0.364 is a 36.4-point decline in cumulative return); for the dollar book "
                       "the same in dollars at minimum size. Not a fraction of a compounded peak (D542).",
               "record": "D542"},
           "spec": "D555", "commit": SPEC, "fixture_sha256": sha256(FIX), "aqr_sha256": aqr_out["file_sha256"],
           "windows": {"primary": PRIMARY, "long": LONG, "reserved_from": RESERVED_FROM, "sessions_primary": int(wP.sum()),
                       "sessions_long": int(wL.sum()), "month_ends": int(len(me))},
           "live_start": live_start, "roll_counts": {r: int(g["roll"][i][wL].sum()) for i, r in enumerate(roots)},
           "nonpositive_closes": g["nonpositive"],
           "rows_dropped": {"no_close": df.attrs["rows_dropped_no_close"], "weekend_stub": df.attrs["rows_dropped_weekend_stub"]},
           "cells": results_cells, "primary": primary,
           "null_n1": n1, "null_n2": n2, "per_root": per_root, "per_sector": per_sector, "per_era": per_era,
           "per_year": per_year, "aqr": aqr_out,
           "dollar_book": {"excluded": list(DOLLAR_EXCLUDED), "roots": dollar_roots, "cd_roots": cd_roots,
                           "cost_convention": "$3 RT micro / $6 RT full + one tick crossed, per side = half of each; a roll is two sides",
                           "min_size": dict(zip(roots, size_name)), "usd_per_point": dict(zip(roots, upp.tolist())),
                           "rho_with_ledger_entry": "ABSENT: the MACD arm's per-session P&L series is not on disk (D504's json holds aggregates only)"},
           "predictions": preds, "verdict": {"declared": verdict, "harness": harness},
           "audits": audits, "timing": {"wall_s": round(time.time() - t_start, 1)}}
    missing = [k for k in REQUIRED_OUTPUTS if k not in res]
    if missing:
        raise AssertionError(f"REQUIRED_OUTPUTS missing: {missing}")
    OUT.write_text(json.dumps(res, indent=1, default=_json_default), encoding="utf-8")
    log(f"\n  VERDICT {verdict} / {harness}   -> {OUT}   ({res['timing']['wall_s']}s)")
    return res


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, tuple):
        return list(o)
    raise TypeError(str(type(o)))


# --------------------------------------------------------------------------------------------
# self-test: synthetic bars, no fixture, no cell scored
# --------------------------------------------------------------------------------------------
def selftest() -> int:
    print("D555 SELF-TEST -- synthetic bars, no fixture read, no cell scored\n")
    rng = np.random.default_rng(1)
    days = pd.bdate_range("2010-06-07", "2014-12-31").strftime("%Y-%m-%d").to_numpy()
    T = len(days); roots = ["UP", "DOWN", "FLAT"]
    n = 3
    drift = np.array([+0.0015, -0.0015, 0.0])
    rlog = drift[:, None] + 0.01 * rng.standard_normal((n, T))
    rlog[:, 0] = np.nan
    live = np.ones((n, T), dtype=bool)
    close = np.exp(np.nancumsum(rlog, axis=1)) * 100.0
    dP = np.diff(close, axis=1, prepend=np.nan)
    roll = np.zeros((n, T), dtype=bool); roll[:, 300] = True
    g = dict(roots=roots, days=days, close=close, rlog=rlog, dP=dP, roll=roll, live=live, span=live.copy(),
             nonpositive=[])
    me = month_ends(days)
    sig = ew_vol(rlog, live)
    for i in range(n):
        if not np.array_equal(np.nan_to_num(ew_vol_loop(rlog[i], live[i]), nan=-1), np.nan_to_num(sig[i], nan=-1)):
            raise AssertionError("EW vol vectorised != loop")
    print("  [1] EW volatility recursion is bit-identical to the per-root pure loop")

    s_np, _ = signal_at_month_ends(rlog, live, days, me, 12)
    s_pd = signal_pandas(rlog, live, days, roots, me, 12)
    if not np.array_equal(s_np, s_pd):
        raise AssertionError("numpy and pandas month-end signs disagree")
    k_last = len(me) - 1
    if not (s_np[0, k_last] == 1 and s_np[1, k_last] == -1):
        raise AssertionError("known drift not recovered by the sign")
    print(f"  [2] month-end signs agree across implementations; UP -> +1, DOWN -> -1 after warm-up")

    sign_held, pos_pub, scale_held, sign_dollar = build_positions(g, sig, me, (12,))
    audit_lag(sign_held, s_pd.astype(float), me, live, T)
    unl = np.zeros_like(sign_held)
    for k, m_ix in enumerate(me):
        lo = me[k - 1] + 1 if k > 0 else 0
        unl[:, lo:m_ix + 1] = s_np[:, k][:, None]
    raised = False
    try:
        audit_lag(unl, s_pd.astype(float), me, live, T)
    except AssertionError:
        raised = True
    if not raised:
        raise AssertionError("lag audit accepted an UNLAGGED grid")
    print("  [3] lag audit passes the held grid and RAISES on the unlagged one")

    audit_right_quantity(sign_held, me, T)
    raised = False
    try:
        audit_right_quantity(np.sign(np.nan_to_num(rlog)), me, T)
    except AssertionError:
        raised = True
    if not raised:
        raise AssertionError("right-quantity audit accepted a daily grid")
    print("  [4] right-quantity audit passes the monthly grid and RAISES on a daily one")

    upp = np.array([5.0, 5.0, 5.0]); tick = np.array([1.25] * 3); comm = np.array([3.0] * 3)
    gross, cost, sides = dollar_book(sign_dollar, g, upp, comm, tick, roots)
    audit_sign_in_money(gross, sign_dollar, g, upp)
    audit_sign_book(gross, sign_dollar, g, upp)
    for label, bad in (("NEGATED", -gross),
                       ("MIS-LAGGED", dollar_book(sign_dollar, dict(g, dP=np.roll(dP, 1, axis=1)), upp, comm, tick, roots)[0])):
        raised = False
        try:
            audit_sign_in_money(bad, sign_dollar, g, upp)
        except AssertionError:
            raised = True
        if not raised:
            raise AssertionError(f"sign audit accepted a {label} gross grid")
    raised = False
    try:
        audit_sign_book(-gross, sign_dollar, g, upp)
    except AssertionError:
        raised = True
    if not raised:
        raise AssertionError("book sign audit accepted a negated gross grid")
    # a roll while positioned costs exactly two sides
    i = 0; t = 300
    if sign_dollar[i, t] != 0 and sides[i, t] < 2:
        raise AssertionError("roll did not charge two sides")
    print("  [5] sign audit in money passes the book and RAISES on a negated and on a mis-lagged gross grid; a roll is two sides")

    rsimple = np.where(np.isfinite(rlog), np.expm1(np.nan_to_num(rlog)), 0.0)
    w = np.ones(T, dtype=bool)
    live_idx = [np.flatnonzero(live[i]) for i in range(n)]
    for k in (1, 5, 77, 400):
        p = rotate_signs(sign_held, live_idx, k) * scale_held
        if not np.array_equal(book_return(p, rsimple), book_return_loop(p, rsimple)):
            raise AssertionError("book_return vectorised != loop")
    p0 = sign_held * scale_held
    x = book_return(p0, rsimple)
    if not sharpe(x[300:]) > 1.0:
        raise AssertionError("a known trend did not produce a positive book")
    if not np.array_equal(rotate_signs(sign_held, live_idx, T), sign_held):
        raise AssertionError("rotation by the full length is not the identity")
    print(f"  [6] enumeration path bit-identical to the loop; known-trend book Sharpe {sharpe(x[300:]):+.2f}; rotation by L is the identity")
    print("\n  ALL SELF-TESTS PASSED. No fixture was read and no cell was scored.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    gq = ap.add_mutually_exclusive_group(required=True)
    gq.add_argument("--run", action="store_true"); gq.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else (0 if run() else 1))
