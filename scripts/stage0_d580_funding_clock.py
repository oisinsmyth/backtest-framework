"""D580 STAGE 0 -- the funding-cycle premise on CME bitcoin. Design committed in 382ef54 BEFORE this file.

    uv run python scripts/stage0_d580_funding_clock.py --selftest   # every audit passes a clean case and RAISES on a break
    uv run python scripts/stage0_d580_funding_clock.py --run        # 2017-12-18 .. 2023-12-31; no bar from 2024-01-01 on

T1 concentration of one-minute volume and r^2 in [S-30, S+30) against the construction's own placement null (96
five-minute offsets through the 8-hour cycle, circular on each event's own centred cycle); T2 the funding sign orders
the 30-minute post-move (defaults excluded; placement and event-shift nulls); T3 magnitude; T4 the level path and the
era split with a bar 2023 must clear alone; T5 per settlement time with the 08:00 UTC GMT-season flag. No cost, no
book, no quote, no return outside the premise's own statistic. Output data/stage0_d580_funding_clock.json.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
FIX = REPO / "data" / "fixtures"
BTC_1M = FIX / "fut_btc_1m.csv.gz"; FUNDING = FIX / "perp_funding.csv"; OI = FIX / "perp_open_interest_daily.csv"
OUT = REPO / "data" / "stage0_d580_funding_clock.json"
SPEC = "382ef54"
RESERVED_FROM = "2024-01-01"
T0 = datetime(2017, 12, 17, tzinfo=timezone.utc)          # the Sunday before the first BTC session (its first bar is 2017-12-17T23:00 UTC); every minute index counts from here
CYCLE = 480; HALF = 240; WIN = 30; PLACEMENTS = np.arange(0, CYCLE, 5); TOPS = np.arange(0, CYCLE, 60)
PROFILE = np.arange(-120, 121); MIN_BARS_IN_WINDOW = 50; H_POST = (15, 30, 60); H_PRIMARY = 30
MIN_CYCLE_SHARE = 0.8       # the daily halt (60 of 480 minutes) sits inside every 00:00 UTC event's centred cycle by construction; 0.9 would drop that hour wholesale
DEFAULT_RATE = 1e-4; SHIFT_MIN = 8; BOOT = 2000; SEED = 580
YEARS_GATED = ("2018", "2019", "2020", "2021", "2022", "2023")
REQUIRED_OUTPUTS = ("spec", "windows", "sets", "audits", "T1", "T2", "T3", "T4", "T5", "beside", "predictions", "verdict", "timing_s")


def expect_raise(fn, what, log=print):
    try:
        fn()
    except AssertionError as e:
        log(f"    audit RAISES on {what}: {str(e)[:70]}"); return True
    raise AssertionError(f"audit did not raise on {what}")


def blk(obs, null):
    null = np.asarray(null, float); null = null[np.isfinite(null)]
    return {"observed": float(obs), "p05": float(np.percentile(null, 5)), "p50": float(np.percentile(null, 50)), "p95": float(np.percentile(null, 95)), "n": int(null.size),
            "pct_rank": float((null < obs).mean()), "above_p95": bool(obs > np.percentile(null, 95))}


# ------------------------------------------------------------------------------------------ the minute grid
def minute_index(ts_strings):
    t = pd.to_datetime(pd.Series(ts_strings), utc=True, format="%Y-%m-%dT%H:%M")
    return ((t - pd.Timestamp(T0)) // pd.Timedelta(minutes=1)).to_numpy(np.int64)


def load_bars(root, log):
    """The minute grid. A bar prints only when the contract TRADES, so an absent minute inside an open session is a
    zero-volume minute, not missing data: `open` marks the minutes between each trade date's first and last bar, volume is
    zero-filled there, the close is carried forward there (an untraded minute has no observed move, r = 0). Outside `open`
    (the daily halt, weekends, holidays) everything is NaN. The design's literal "50 of 60 bars present" is reported beside."""
    b = pd.read_csv(BTC_1M, dtype={"ts_utc": str, "root": str, "contract": str, "day": str}, encoding="utf-8"); b = b[(b["root"] == root) & (b["ts_utc"] < RESERVED_FROM)]
    if b["ts_utc"].max() >= RESERVED_FROM:
        raise AssertionError("a reserved bar leaked")
    ix = minute_index(b["ts_utc"]); N = int(ix.max()) + CYCLE + 120
    traded = np.zeros(N, bool); traded[ix] = True; close = np.full(N, np.nan); vol = np.full(N, np.nan); close[ix] = b["close"].to_numpy(float); vol[ix] = b["volume"].to_numpy(float)
    span = pd.DataFrame({"day": b["day"].to_numpy(), "ix": ix}).groupby("day")["ix"].agg(["min", "max"]); is_open = np.zeros(N, bool)
    for lo, hi in zip(span["min"], span["max"]):
        is_open[lo:hi + 1] = True
    vol = np.where(is_open & ~traded, 0.0, vol)
    cf = pd.Series(close).ffill().to_numpy(); close = np.where(is_open, cf, np.nan)
    lr = np.full(N, np.nan); ok = np.isfinite(close[1:]) & np.isfinite(close[:-1]); lr[1:][ok] = np.log(close[1:][ok]) - np.log(close[:-1][ok])
    log(f"  {root}: {len(b):,} bars {b['ts_utc'].min()} .. {b['ts_utc'].max()} (last read, before {RESERVED_FROM}); minute grid {N:,}; open minutes {int(is_open.sum()):,}, traded {int(traded.sum()):,} ({traded.sum()/is_open.sum():.0%} of open)")
    return {"close": close, "vol": vol, "r2": lr ** 2, "open": is_open, "traded": traded, "span": span, "N": N, "first": b["ts_utc"].min(), "last": b["ts_utc"].max(), "n_bars": int(len(b))}


def settlements(N):
    """Every 00/08/16 UTC minute index inside the grid, with room for the centred cycle."""
    s = np.arange(0, N, CYCLE); return s[(s - HALF >= 0) & (s + CYCLE + max(H_POST) + 1 < N)]   # room for the centred cycle and for every placement's post-window


def when(s):
    return (T0 + timedelta(minutes=int(s))).strftime("%Y-%m-%dT%H:%M")


def cme_set(is_open, S):
    """Open minutes in [S-30, S+30) per settlement: the runner's index arithmetic on the open mask."""
    return np.array([int(is_open[s - WIN:s + WIN].sum()) for s in S])


def cme_set_pandas(span, S):
    """Second path: the same counts from the per-trade-date (first, last) bar table through an IntervalIndex, never the mask."""
    iv = pd.IntervalIndex.from_arrays(span["min"].to_numpy(), span["max"].to_numpy(), closed="both"); out = []
    for s in S:
        m = np.arange(s - WIN, s + WIN); out.append(int(iv.get_indexer(m).__ne__(-1).sum()))
    return np.array(out)


def audit_cme_set(a, b):
    if a.shape != b.shape or not np.array_equal(a, b):
        raise AssertionError(f"CME SET AUDIT: {int((a != b).sum())} settlements differ between the two paths")


# ------------------------------------------------------------------------------------------ the statistics
def cycle_matrix(q, S):
    """E x 480: each event's own centred cycle [S-240, S+240) of q, normalised by its own finite mean."""
    M = q[S[:, None] + np.arange(-HALF, HALF)[None, :]]; m = np.nanmean(M, axis=1); return M / m[:, None]


def placement_stats(M):
    """Mean over events of the window mean, at every 5-minute placement (circular on the cycle). Column 0 is the funding clock."""
    out = np.full(PLACEMENTS.size, np.nan); n = np.zeros(PLACEMENTS.size, int)
    for i, k in enumerate(PLACEMENTS):
        cols = (np.arange(-WIN, WIN) + HALF + k) % CYCLE; w = np.nanmean(M[:, cols], axis=1); ok = np.isfinite(w); out[i] = w[ok].mean(); n[i] = int(ok.sum())
    return out, n


NON_OVERLAP_T1 = (PLACEMENTS >= 2 * WIN) & (PLACEMENTS <= CYCLE - 2 * WIN)      # windows disjoint from [-30, 30): 73 placements
NON_OVERLAP_T2 = (PLACEMENTS >= H_PRIMARY) & (PLACEMENTS <= CYCLE - H_PRIMARY)  # post-windows disjoint from [0, 30]: 85 placements


def t1_block(M):
    if M.shape[0] == 0 or not np.isfinite(M).any():
        return {"window_mean_normalised": None, "rank_in_96_placements": None, "rank_among_non_overlapping_placements": None, "rank_among_8_tops_of_hour": None, "beats_all_tops": False, "peak_minute": None, "peak_within_5": False, "events": 0}
    st, n = placement_stats(M); obs = st[0]; others = st[1:]; non = st[NON_OVERLAP_T1]
    top = st[np.isin(PLACEMENTS, TOPS)]; prof = np.nanmean(M[:, HALF + PROFILE], axis=0); peak = int(PROFILE[int(np.nanargmax(prof))])
    return {"window_mean_normalised": float(obs), "rank_in_96_placements": float((others < obs).mean()), "null_p50": float(np.nanpercentile(others, 50)), "null_p95": float(np.nanpercentile(others, 95)),
            "rank_among_non_overlapping_placements": float((non < obs).mean()), "n_non_overlapping": int(non.size),
            "rank_among_8_tops_of_hour": float((top[1:] < obs).mean()), "beats_all_tops": bool(obs > np.nanmax(top[1:])), "peak_minute": peak, "peak_within_5": bool(abs(peak) <= 5),
            "events": int(n[0]), "events_min_over_placements": int(n.min()), "placement_stats": [float(x) for x in st], "profile_pm120": [float(x) for x in prof]}


def p_at(close, t):
    """P(t) = the close of the bar that ENDS at t, i.e. the bar starting at t-1 (D462: ts_event is the bar start)."""
    return close[t - 1]


def post_move(close, S, h, k=0):
    a = p_at(close, S + k); b = p_at(close, S + k + h); return 1e4 * (np.log(b) - np.log(a))


def t2_block(close, S, sign, weeks, rng):
    """Mean signed post-move at h=30 in bp with the week block-bootstrap SE; placement null; event-shift null; the pre-move and h=15/60 beside."""
    out = {}
    for h in H_POST:
        y = sign * post_move(close, S, h); ok = np.isfinite(y); out[f"y_post_{h}"] = {"mean_bp": float(y[ok].mean()), "n": int(ok.sum()), "median_bp": float(np.median(y[ok])), "share_positive": float((y[ok] > 0).mean())}
    y = sign * post_move(close, S, H_PRIMARY); ok = np.isfinite(y); yy, ww = y[ok], weeks[ok]
    uw = np.unique(ww); groups = [yy[ww == w] for w in uw]; boot = np.array([np.concatenate([groups[i] for i in rng.integers(0, len(groups), len(groups))]).mean() for _ in range(BOOT)])
    out["se_week_block"] = float(boot.std()); out["t"] = float(yy.mean() / boot.std())
    tr = int(0.01 * yy.size); ys = np.sort(yy); out["trimmed_mean_bp"] = float(ys[tr:yy.size - tr].mean()); out["mean_ex_top1pct_bp"] = float(ys[:yy.size - tr].mean()); out["mean_ex_bottom1pct_bp"] = float(ys[tr:].mean())
    # placement null: the same sign attached to the window at every other 5-minute offset
    pl = np.array([np.nanmean(sign * post_move(close, S, H_PRIMARY, int(k))) for k in PLACEMENTS]); out["placement_null"] = blk(pl[0], pl[1:]); out["placement_zero_reproduces"] = bool(np.isclose(pl[0], yy.mean()))
    out["placement_null_non_overlapping"] = blk(pl[0], pl[NON_OVERLAP_T2])
    # event-shift null: the sign series rolled by j events, enumerated
    r = post_move(close, S, H_PRIMARY); ok2 = np.isfinite(r); rr, ss = r[ok2], sign[ok2]; sh = np.array([np.mean(np.roll(ss, j) * rr) for j in range(SHIFT_MIN, rr.size - SHIFT_MIN + 1)])
    out["event_shift_null"] = blk(float((ss * rr).mean()), sh)
    ypre = -sign * (1e4 * (np.log(p_at(close, S)) - np.log(p_at(close, S - WIN)))); okp = np.isfinite(ypre); out["y_pre_30"] = {"mean_bp": float(ypre[okp].mean()), "n": int(okp.sum()), "share_positive": float((ypre[okp] > 0).mean())}
    top = np.argsort(-np.abs(np.where(ok, y, 0)))[:5]; out["largest_abs_events"] = [{"settlement": when(S[i]), "y_post_30_bp": float(y[i]), "sign": int(sign[i])} for i in top]
    return out


def audit_sign_in_money(rng, sign_fn=np.sign):
    """A synthetic path with an injected post-settlement move in the funding-sign direction must give y_post > 0; its negation < 0.
    `sign_fn` is the convention under test; the break passes a negated one."""
    N = 20 * CYCLE; close = 30_000 * np.exp(np.cumsum(rng.normal(0, 1e-4, N))); S = np.arange(CYCLE, N - CYCLE, CYCLE); f = np.where(rng.random(S.size) < 0.5, 1e-3, -1e-3); sign = sign_fn(f)
    inj = close.copy()
    for s, sg in zip(S, np.sign(f)):
        inj[s:s + 60] *= np.exp(sg * 0.01)
    y = sign * post_move(inj, S, H_PRIMARY); yn = sign * post_move(2 * close - inj + 0.0, S, H_PRIMARY)
    if not (np.nanmean(y) > 50 and np.nanmean(yn) < -50):
        raise AssertionError(f"SIGN AUDIT: injected {np.nanmean(y):.1f} bp, negated {np.nanmean(yn):.1f} bp")
    return float(np.nanmean(y)), float(np.nanmean(yn))


def audit_bar_end(pfn=p_at):
    """Known answer: the bar starting at S-1 closes at S. P(S) must be that bar's close, not the bar starting at S. The break passes the wrong convention."""
    close = np.full(10, np.nan); close[4] = 100.0; close[5] = 200.0
    if pfn(close, 5) != 100.0:
        raise AssertionError("BAR-END AUDIT: P(S) is not the close of the bar starting at S-1")


def attach_rate(fund, S_times, venue, symbol):
    """The rate settled at S by dictionary lookup on the settlement string."""
    f = fund[(fund["venue"] == venue) & (fund["symbol"] == symbol)]; d = dict(zip(f["settlement_utc"].str[:16], f["funding_rate"].astype(float)))
    return np.array([d.get(t, np.nan) for t in S_times])


def attach_rate_asof(fund, S_times, venue, symbol):
    """Second path: pandas merge_asof with an exact tolerance of zero minutes."""
    f = fund[(fund["venue"] == venue) & (fund["symbol"] == symbol)].copy(); f["t"] = pd.to_datetime(f["settlement_utc"], utc=True); f = f.sort_values("t")
    q = pd.DataFrame({"t": pd.to_datetime(pd.Series(S_times), utc=True, format="%Y-%m-%dT%H:%M")}).sort_values("t")
    m = pd.merge_asof(q, f[["t", "funding_rate"]], on="t", tolerance=pd.Timedelta(minutes=0), direction="nearest"); return m["funding_rate"].to_numpy(float)


def audit_rate_attachment(a, b):
    ok = np.isfinite(a) | np.isfinite(b)
    if (np.isfinite(a) != np.isfinite(b)).any() or not np.allclose(a[np.isfinite(a)], b[np.isfinite(b)]):
        raise AssertionError(f"RATE AUDIT: {int((~np.isclose(np.nan_to_num(a), np.nan_to_num(b))).sum())} settlements differ between lookup and merge_asof")
    return int(ok.sum())


def audit_right_quantity(Mv, Mr):
    if Mv.shape != Mr.shape or np.allclose(np.nan_to_num(Mv), np.nan_to_num(Mr)):
        raise AssertionError("RIGHT-QUANTITY AUDIT: the volume and r^2 cycle matrices are the same array")


def guard_outputs(res):
    missing = [k for k in REQUIRED_OUTPUTS if k not in res]
    if missing:
        raise AssertionError(f"REQUIRED_OUTPUTS missing: {missing}")


# ------------------------------------------------------------------------------------------ run
def run(log=print):
    t0 = time.time(); rng = np.random.default_rng(SEED)
    log(f"D580 STAGE 0 -- the funding clock on CME bitcoin; spec {SPEC}; nothing from {RESERVED_FROM} on is read; no cost, no book")
    btc = load_bars("BTC", log); mbt = load_bars("MBT", log)
    fund = pd.read_csv(FUNDING, dtype={"settlement_utc": str, "venue": str, "symbol": str}, encoding="utf-8"); fund = fund[fund["settlement_utc"] < RESERVED_FROM]
    oi = pd.read_csv(OI, dtype={"day_utc": str, "venue": str, "symbol": str}, encoding="utf-8"); oi = oi[(oi["day_utc"] < RESERVED_FROM) & (oi["venue"] == "bybit_linear") & (oi["symbol"] == "BTCUSDT")]
    windows = {"btc_bars": [btc["first"], btc["last"]], "mbt_bars": [mbt["first"], mbt["last"]], "funding_last_settlement_read": fund["settlement_utc"].max(), "oi_last_day_read": oi["day_utc"].max(), "reserved_from": RESERVED_FROM}
    audits = {}
    # ---- the sets ----
    S_all = settlements(btc["N"]); cnt = cme_set(btc["open"], S_all)
    audit_cme_set(cnt, cme_set_pandas(btc["span"], S_all)); audits["cme_set_second_path_settlements_checked"] = int(S_all.size)
    def broken():
        c2 = cnt.copy(); c2[0] = 0 if c2[0] else 60; audit_cme_set(cnt, c2)
    audits["cme_set_audit_raises"] = expect_raise(broken, "a settlement moved into the weekend gap", log)
    in_cme = cnt >= MIN_BARS_IN_WINDOW; S = S_all[in_cme]
    literal = np.array([int(btc["traded"][s - WIN:s + WIN].sum()) for s in S_all]) >= MIN_BARS_IN_WINDOW
    Mv = cycle_matrix(btc["vol"], S); full = np.isfinite(Mv).mean(axis=1) >= MIN_CYCLE_SHARE; S1 = S[full]; Mv = Mv[full]; Mr = cycle_matrix(btc["r2"], S1)
    audit_right_quantity(Mv, Mr); audits["right_quantity_volume_vs_r2"] = True; audits["right_quantity_raises"] = expect_raise(lambda: audit_right_quantity(Mv, Mv), "the same matrix twice", log)
    hours = np.array([(T0 + timedelta(minutes=int(s))).hour for s in S1]); years1 = np.array([when(s)[:4] for s in S1]); wd1 = np.array([(T0 + timedelta(minutes=int(s))).weekday() for s in S1])
    sets = {"settlements_on_grid": int(S_all.size), "in_cme_set_50_of_60_open_minutes": int(in_cme.sum()), "under_the_designs_literal_rule_50_of_60_traded_bars": int(literal.sum()),
            "presence_rule": "open minutes (between a trade date's first and last bar); an untraded open minute is volume 0 and r = 0, not missing", "t1_full_cycle_set": int(S1.size), "dropped_short_window": int((~in_cme).sum()), "dropped_partial_cycle": int((~full).sum()),
            "t1_by_hour_utc": {int(h): int((hours == h).sum()) for h in (0, 8, 16)}, "monday_00_in_t1_set": int(((wd1 == 0) & (hours == 0)).sum())}
    log(f"  settlements on grid {S_all.size}; CME set {in_cme.sum()}; full-cycle set for T1 {S1.size} (Monday 00:00 UTC survivors {sets['monday_00_in_t1_set']})")
    # ---- T1 ----
    T1 = {"volume": t1_block(Mv), "r2": t1_block(Mr)}
    for q in ("volume", "r2"):
        b = T1[q]; log(f"  T1 {q}: window {b['window_mean_normalised']:.3f}x cycle mean, rank {b['rank_in_96_placements']:.3f} in 96 placements (p50 {b['null_p50']:.3f} p95 {b['null_p95']:.3f}), among tops of hour {b['rank_among_8_tops_of_hour']:.3f}, peak at {b['peak_minute']:+d} min, events {b['events']}")
    T1["by_year"] = {y: {q: {k: v for k, v in t1_block((Mv if q == "volume" else Mr)[years1 == y]).items() if k in ("window_mean_normalised", "rank_in_96_placements", "rank_among_non_overlapping_placements", "peak_minute", "events")} for q in ("volume", "r2")} for y in sorted(set(years1))}
    T1["by_hour"] = {int(h): {q: {k: v for k, v in t1_block((Mv if q == "volume" else Mr)[hours == h]).items() if k in ("window_mean_normalised", "rank_in_96_placements", "rank_among_non_overlapping_placements", "rank_among_8_tops_of_hour", "peak_minute", "events")} for q in ("volume", "r2")} for h in (0, 8, 16)}
    log("  T1 by year (volume rank / r2 rank): " + " ".join(f"{y}:{v['volume']['rank_in_96_placements']:.2f}/{v['r2']['rank_in_96_placements']:.2f}" for y, v in T1["by_year"].items()))
    log("  T1 by hour UTC (volume rank / r2 rank): " + " ".join(f"{h}:{v['volume']['rank_in_96_placements']:.2f}/{v['r2']['rank_in_96_placements']:.2f}" for h, v in T1["by_hour"].items()))
    # ---- F1 on the CME set ----
    S_t = [when(s) for s in S]; f_bin = attach_rate(fund, S_t, "binance", "BTCUSDT"); f_byi = attach_rate(fund, S_t, "bybit_inverse", "BTCUSD"); f_byl = attach_rate(fund, S_t, "bybit_linear", "BTCUSDT")
    audits["rate_attachment_settlements_checked"] = audit_rate_attachment(f_bin, attach_rate_asof(fund, S_t, "binance", "BTCUSDT"))
    audits["rate_attachment_raises"] = expect_raise(lambda: audit_rate_attachment(f_bin, np.roll(attach_rate_asof(fund, S_t, "binance", "BTCUSDT"), 1)), "the rate series shifted one settlement", log)
    f1 = np.where(np.isfinite(f_bin), f_bin, f_byi)                                            # primary: Binance, Bybit inverse for the 2018-11 .. 2019-09 extension
    f_prev = np.full(f1.size, np.nan); f_prev[1:] = f1[:-1]; same_next = (S[1:] - S[:-1]) == CYCLE; f_prev[1:][~same_next] = np.nan   # the rate settled at S-8h, only when S-8h is the previous CME-set event
    f_mean = np.where(np.isfinite(f_bin) & np.isfinite(f_byl), (f_bin + f_byl) / 2, np.where(np.isfinite(f_bin), f_bin, f_byl))
    has = np.isfinite(f1); nodef = has & (f1 != DEFAULT_RATE)
    audits["sign_in_money_injected_bp"], audits["sign_in_money_negated_bp"] = audit_sign_in_money(rng); audits["sign_audit_raises"] = expect_raise(lambda: audit_sign_in_money(rng, lambda f: -np.sign(f)), "a negated sign convention", log)
    audit_bar_end(); audits["bar_end_known_answer"] = True; audits["bar_end_raises"] = expect_raise(lambda: audit_bar_end(lambda c, t: c[t]), "the bar-start convention in place of the bar-end one", log)
    weeks = np.array([(T0 + timedelta(minutes=int(s))).isocalendar()[1] + 100 * (T0 + timedelta(minutes=int(s))).isocalendar()[0] for s in S])
    years = np.array([t[:4] for t in S_t]); hrs = np.array([(T0 + timedelta(minutes=int(s))).hour for s in S])
    sets.update({"with_f1": int(has.sum()), "f1_not_default": int(nodef.sum()), "share_default_among_with_f1": float(1 - nodef.sum() / has.sum()), "f1_from_binance": int(np.isfinite(f_bin).sum()), "f1_from_bybit_inverse_extension": int((np.isfinite(f1) & ~np.isfinite(f_bin)).sum())})
    # ---- T2 ----
    sign = np.sign(f1); T2 = t2_block(btc["close"], S[nodef], sign[nodef], weeks[nodef], rng)
    okp = nodef & np.isfinite(f_prev); T2["sign_agreement_with_s_minus_8h"] = float((np.sign(f_prev[okp]) == sign[okp]).mean()); T2["n_for_agreement"] = int(okp.sum())
    log(f"  T2 y_post(30): {T2['y_post_30']['mean_bp']:+.2f} bp (SE {T2['se_week_block']:.2f}, t {T2['t']:+.2f}, n {T2['y_post_30']['n']}, median {T2['y_post_30']['median_bp']:+.2f}, trimmed {T2['trimmed_mean_bp']:+.2f}); "
        f"placement rank {T2['placement_null']['pct_rank']:.3f} (p95 {T2['placement_null']['p95']:+.2f}); event-shift rank {T2['event_shift_null']['pct_rank']:.3f} (p95 {T2['event_shift_null']['p95']:+.2f}); "
        f"h15 {T2['y_post_15']['mean_bp']:+.2f} h60 {T2['y_post_60']['mean_bp']:+.2f}; y_pre {T2['y_pre_30']['mean_bp']:+.2f}; S-8h sign agreement {T2['sign_agreement_with_s_minus_8h']:.2f}")
    # ---- T3 ----
    y30 = sign * post_move(btc["close"], S, H_PRIMARY); ok3 = nodef & np.isfinite(y30); a3 = np.abs(f1[ok3]); y3 = y30[ok3]
    ter = np.digitize(a3, np.quantile(a3, [1 / 3, 2 / 3])); T3 = {"by_abs_f1_tercile": {int(t): {"mean_bp": float(y3[ter == t].mean()), "n": int((ter == t).sum()), "abs_f1_mean": float(a3[ter == t].mean())} for t in range(3)},
                                                             "spearman_abs_f1_vs_y_post": float(stats.spearmanr(a3, y3).correlation), "top_over_bottom": float(y3[ter == 2].mean() / y3[ter == 0].mean()) if y3[ter == 0].mean() != 0 else None}
    oid = dict(zip(oi["day_utc"], oi["open_interest_contracts"].astype(float))); oiv = np.array([oid.get(t[:10], np.nan) for t in S_t]); f5 = oiv * np.abs(f1); ok5 = ok3 & np.isfinite(f5)
    if ok5.sum() > 100:
        t5 = np.digitize(f5[ok5], np.quantile(f5[ok5], [1 / 3, 2 / 3])); T3["by_f5_tercile"] = {int(t): {"mean_bp": float(y30[ok5][t5 == t].mean()), "n": int((t5 == t).sum())} for t in range(3)}; T3["n_with_oi"] = int(ok5.sum())
    log(f"  T3 by |F1| tercile: " + " ".join(f"{t}:{v['mean_bp']:+.2f}bp(n{v['n']})" for t, v in T3["by_abs_f1_tercile"].items()) + f"; Spearman {T3['spearman_abs_f1_vs_y_post']:+.3f}" + (f"; by F5 tercile " + " ".join(f"{t}:{v['mean_bp']:+.2f}" for t, v in T3["by_f5_tercile"].items()) if "by_f5_tercile" in T3 else ""))
    # ---- T4 the level path and the era split ----
    T4 = {}
    for y in sorted(set(years)):
        m = years == y; mn = m & nodef; yv = y30[mn & np.isfinite(y30)]
        row = {"events_cme": int(m.sum()), "with_f1": int((m & has).sum()), "mean_abs_f1": float(np.nanmean(np.abs(f1[m & has]))) if (m & has).any() else None, "share_default": float(1 - nodef[m & has].mean()) if (m & has).any() else None,
               "share_negative": float((f1[m & has] < 0).mean()) if (m & has).any() else None, "oi_mean_contracts": float(np.nanmean(oiv[m])) if np.isfinite(oiv[m]).any() else None,
               "btc_window_volume_mean": float(np.nanmean(btc["vol"][S[m][:, None] + np.arange(-WIN, WIN)[None, :]])), "price_mean": float(np.nanmean(btc["close"][S[m]]))}
        if yv.size > 30:
            pl = np.array([np.nanmean(sign[mn] * post_move(btc["close"], S[mn], H_PRIMARY, int(k))) for k in PLACEMENTS]); row["t2_mean_bp"] = float(yv.mean()); row["t2_n"] = int(yv.size); row["t2_placement_rank"] = float((pl[1:] < pl[0]).mean())
            uw = np.unique(weeks[mn]); g = [y30[mn][weeks[mn] == w] for w in uw]; g = [x[np.isfinite(x)] for x in g]; g = [x for x in g if x.size]
            boot = np.array([np.concatenate([g[i] for i in rng.integers(0, len(g), len(g))]).mean() for _ in range(500)]); row["t2_se"] = float(boot.std())
        if y in T1["by_year"]:
            row["t1_volume_rank"] = T1["by_year"][y]["volume"]["rank_in_96_placements"]; row["t1_r2_rank"] = T1["by_year"][y]["r2"]["rank_in_96_placements"]
        T4[y] = row
    log("  T4 by year: " + " | ".join(f"{y}: |F1| {v['mean_abs_f1']*1e4 if v['mean_abs_f1'] is not None else float('nan'):.2f}bp def {v['share_default'] if v['share_default'] is not None else float('nan'):.2f} OI {v['oi_mean_contracts']/1e3 if v['oi_mean_contracts'] else float('nan'):.0f}k T1 {v.get('t1_volume_rank', float('nan')):.2f}/{v.get('t1_r2_rank', float('nan')):.2f} T2 {v.get('t2_mean_bp', float('nan')):+.1f}bp r{v.get('t2_placement_rank', float('nan')):.2f}" for y, v in T4.items()))
    # ---- T5 per settlement time ----
    LON = ZoneInfo("Europe/London"); gmt = np.array([(T0 + timedelta(minutes=int(s))).astimezone(LON).utcoffset() == timedelta(0) for s in S])
    T5 = {}
    for h in (0, 8, 16):
        m = (hrs == h) & nodef & np.isfinite(y30); pl = np.array([np.nanmean(sign[m] * post_move(btc["close"], S[m], H_PRIMARY, int(k))) for k in PLACEMENTS])
        T5[int(h)] = {"t1": T1["by_hour"][int(h)], "t2_mean_bp": float(y30[m].mean()), "t2_n": int(m.sum()), "t2_placement_rank": float((pl[1:] < pl[0]).mean())}
        if h == 8:
            for lab, mm in (("gmt_season_london_open_coincides", m & gmt), ("bst_season", m & ~gmt)):
                pl2 = np.array([np.nanmean(sign[mm] * post_move(btc["close"], S[mm], H_PRIMARY, int(k))) for k in PLACEMENTS]); T5[8][lab] = {"t2_mean_bp": float(y30[mm].mean()), "n": int(mm.sum()), "t2_placement_rank": float((pl2[1:] < pl2[0]).mean()),
                                                                                                                                             "t1_volume_rank": t1_block(Mv[(hours == 8) & (np.isin(S1, S[gmt]) if lab.startswith("gmt") else ~np.isin(S1, S[gmt]))])["rank_in_96_placements"]}
    log("  T5 per hour UTC: " + " | ".join(f"{h}: T1 {v['t1']['volume']['rank_in_96_placements']:.2f}/{v['t1']['r2']['rank_in_96_placements']:.2f} T2 {v['t2_mean_bp']:+.2f}bp r{v['t2_placement_rank']:.2f} n{v['t2_n']}" for h, v in T5.items())
        + f"; 08 GMT-season T2 {T5[8]['gmt_season_london_open_coincides']['t2_mean_bp']:+.2f} (T1 vol {T5[8]['gmt_season_london_open_coincides']['t1_volume_rank']:.2f}) vs BST {T5[8]['bst_season']['t2_mean_bp']:+.2f} (T1 vol {T5[8]['bst_season']['t1_volume_rank']:.2f})")
    # ---- beside ----
    beside = {}
    S_m = S[S < mbt["N"] - CYCLE - 120]; cm = cme_set(mbt["open"], S_m) >= MIN_BARS_IN_WINDOW; Sm = S_m[cm]; Mvm = cycle_matrix(mbt["vol"], Sm); fm = np.isfinite(Mvm).mean(axis=1) >= MIN_CYCLE_SHARE
    beside["mbt_t1_volume"] = {k: v for k, v in t1_block(Mvm[fm]).items() if k in ("window_mean_normalised", "rank_in_96_placements", "rank_among_8_tops_of_hour", "peak_minute", "events")}
    beside["mbt_t1_r2"] = {k: v for k, v in t1_block(cycle_matrix(mbt["r2"], Sm[fm])).items() if k in ("window_mean_normalised", "rank_in_96_placements", "peak_minute", "events")}
    idx_m = np.isin(S, Sm); ym = sign * post_move(mbt["close"], S, H_PRIMARY); okm = nodef & idx_m & np.isfinite(ym); beside["mbt_t2_mean_bp"] = float(ym[okm].mean()); beside["mbt_t2_n"] = int(okm.sum())
    for lab, f in (("cross_venue_mean", f_mean), ("s_minus_8h", f_prev)):
        sg = np.sign(f); okk = np.isfinite(f) & (f != DEFAULT_RATE) & np.isfinite(y30 / sign); yv = sg[okk] * (y30[okk] / sign[okk]); beside[f"t2_with_{lab}"] = {"mean_bp": float(yv.mean()), "n": int(okk.sum()), "sign_agreement_with_primary": float((sg[okk] == sign[okk]).mean())}
    wd = np.array([(T0 + timedelta(minutes=int(s))).weekday() for s in S]); beside["t2_by_weekday"] = {int(d): {"mean_bp": float(y30[(wd == d) & nodef & np.isfinite(y30)].mean()), "n": int(((wd == d) & nodef & np.isfinite(y30)).sum())} for d in range(5)}
    beside["t2_monday_00_utc"] = {"mean_bp": float(y30[(wd == 0) & (hrs == 0) & nodef & np.isfinite(y30)].mean()), "n": int(((wd == 0) & (hrs == 0) & nodef & np.isfinite(y30)).sum())}
    px = btc["close"][S[nodef & np.isfinite(y30)]]; beside["mbt_tick_bp_at_mean_price"] = float(1e4 * 5 / np.nanmean(px)); beside["y_post_30_in_mbt_ticks"] = float(T2["y_post_30"]["mean_bp"] / beside["mbt_tick_bp_at_mean_price"])
    beside["eth_met"] = "not in the fixture (BTC and MBT only); not run"
    log(f"  beside: MBT T1 volume rank {beside['mbt_t1_volume']['rank_in_96_placements']:.2f} r2 {beside['mbt_t1_r2']['rank_in_96_placements']:.2f} (events {beside['mbt_t1_volume']['events']}); MBT T2 {beside['mbt_t2_mean_bp']:+.2f} bp; "
        f"cross-venue T2 {beside['t2_with_cross_venue_mean']['mean_bp']:+.2f}; S-8h T2 {beside['t2_with_s_minus_8h']['mean_bp']:+.2f} (agreement {beside['t2_with_s_minus_8h']['sign_agreement_with_primary']:.2f}); y_post in MBT ticks {beside['y_post_30_in_mbt_ticks']:+.2f}")
    # ---- predictions and the verdict ----
    yrs_t1 = [y for y in YEARS_GATED if y in T1["by_year"]]; t1_years_hold = sum(T1["by_year"][y]["volume"]["rank_in_96_placements"] >= 0.95 and T1["by_year"][y]["r2"]["rank_in_96_placements"] >= 0.95 for y in yrs_t1)
    t1_ok = bool(T1["volume"]["rank_in_96_placements"] >= 0.95 and T1["r2"]["rank_in_96_placements"] >= 0.95 and T1["volume"]["peak_within_5"] and T1["r2"]["peak_within_5"])
    t1_tops = bool(T1["volume"]["beats_all_tops"] and T1["r2"]["beats_all_tops"])
    t2_ok = bool(T2["y_post_30"]["mean_bp"] >= 2 and T2["placement_null"]["pct_rank"] >= 0.95 and T2["event_shift_null"]["pct_rank"] >= 0.95)
    t2_2023 = bool("2023" in T4 and T4["2023"].get("t2_mean_bp", -1) > 0 and T4["2023"].get("t2_placement_rank", 0) >= 0.90)
    clean_hour = bool(any(T5[h]["t1"]["volume"]["rank_in_96_placements"] >= 0.95 and T5[h]["t2_mean_bp"] > 0 and T5[h]["t2_placement_rank"] >= 0.95 for h in (0, 16)))
    preds = {"T1_pooled_rank_ge_0.95_both_and_peak_within_5": t1_ok, "T1_beats_all_tops_of_hour": t1_tops, "T1_holds_in_ge_4_of_6_years": bool(t1_years_hold >= 4), "T1_years_holding": int(t1_years_hold),
             "T2_mean_ge_2bp_and_rank_ge_0.95_both_nulls": t2_ok, "T2_holds_in_2023_alone": t2_2023, "T3_spearman_positive": bool(T3["spearman_abs_f1_vs_y_post"] > 0), "T5_a_clean_hour_holds_both": clean_hour}
    if t1_ok and preds["T1_holds_in_ge_4_of_6_years"]:
        verdict = "SUPPORTED" if (t2_ok and t2_2023 and clean_hour) else "PARTIAL"
    else:
        verdict = "NOT SUPPORTED"
    if verdict == "SUPPORTED" and not t2_2023:
        verdict = "NOT SUPPORTED"
    log("  predictions: " + "; ".join(f"{k} {v}" for k, v in preds.items())); log(f"  STAGE 0 VERDICT: {verdict}")
    res = {"spec": SPEC, "windows": windows, "sets": sets, "audits": audits, "T1": T1, "T2": T2, "T3": T3, "T4": T4, "T5": T5, "beside": beside, "predictions": preds, "verdict": verdict, "timing_s": round(time.time() - t0, 1),
           "construction": {"cycle_min": CYCLE, "window": [-WIN, WIN], "placements": int(PLACEMENTS.size), "profile": [-120, 120], "min_bars_in_window": MIN_BARS_IN_WINDOW, "min_cycle_share": MIN_CYCLE_SHARE, "default_rate_excluded": DEFAULT_RATE, "h_primary": H_PRIMARY, "boot": BOOT, "shift_min": SHIFT_MIN,
                            "f1": "Binance BTCUSDT settled at S; Bybit inverse BTCUSD for settlements before 2019-09-10", "no_cost_no_book_no_quote": True}}
    guard_outputs(res); expect_raise(lambda: guard_outputs({k: v for k, v in res.items() if k != "T2"}), "a missing declared output", log)
    OUT.write_text(json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)), encoding="utf-8"); log(f"  wrote {OUT.relative_to(REPO)} in {res['timing_s']} s")
    return 0


def selftest(log=print):
    rng = np.random.default_rng(1)
    audit_bar_end(); log("  bar-end known answer passes"); expect_raise(lambda: audit_bar_end(lambda c, t: c[t]), "the bar-start convention", log)
    a, b = audit_sign_in_money(rng); log(f"  sign in money: injected {a:+.0f} bp, negated {b:+.0f} bp"); expect_raise(lambda: audit_sign_in_money(rng, lambda f: -np.sign(f)), "a negated sign convention", log)
    # a synthetic clock: volume spikes at the funding minutes. The 11 placements within 55 minutes of the clock OVERLAP the
    # window and share the spike, so the declared 96-placement rank of a true clock is decided against them by noise alone;
    # the non-overlapping rank must be 1.0 and the declared rank must clear 0.9. A flat series must rank low on both.
    N = 60 * CYCLE; vol = rng.gamma(2, 1, N); S = settlements(N)
    for s in S:
        vol[s - 10:s + 10] *= 4
    M = cycle_matrix(vol, S); b1 = t1_block(M); assert b1["rank_among_non_overlapping_placements"] == 1.0 and b1["rank_in_96_placements"] >= 0.9 and abs(b1["peak_minute"]) <= 10, (b1["rank_in_96_placements"], b1["rank_among_non_overlapping_placements"])
    flat = t1_block(cycle_matrix(rng.gamma(2, 1, N), S)); assert flat["rank_in_96_placements"] < 0.95 and flat["rank_among_non_overlapping_placements"] < 0.95, "a flat series ranks high"
    log(f"  T1 on a synthetic clock: declared rank {b1['rank_in_96_placements']:.3f}, non-overlapping rank {b1['rank_among_non_overlapping_placements']:.2f}, peak {b1['peak_minute']:+d}; on noise: {flat['rank_in_96_placements']:.2f} / {flat['rank_among_non_overlapping_placements']:.2f}")
    # the CME-set second path agrees and raises: two "trade dates" open [100, 700] and [960, 1300]; the settlement at 480 is fully open, 960's window [930, 990) is open on 30 of 60, 1440 is closed
    span = pd.DataFrame({"min": [100, 960], "max": [700, 1300]}, index=["d1", "d2"]); is_open = np.zeros(4 * CYCLE, bool); is_open[100:701] = True; is_open[960:1301] = True; S2 = np.array([480, 960, 1440])
    c = cme_set(is_open, S2); assert list(c) == [60, 30, 0], list(c); audit_cme_set(c, cme_set_pandas(span, S2)); expect_raise(lambda: audit_cme_set(c, cme_set_pandas(span, S2) + 1), "a differing count", log)
    # the T2 machinery: a synthetic path with the injected move gives a placement rank of 1 and an event-shift rank near 1
    Np = 200 * CYCLE; close = 30_000 * np.exp(np.cumsum(rng.normal(0, 1e-4, Np))); Sp = settlements(Np); sign = np.where(rng.random(Sp.size) < 0.5, 1, -1)
    for s, sg in zip(Sp, sign):
        close[s:s + 45] *= np.exp(sg * 0.002)
    weeks = Sp // (CYCLE * 21); t2 = t2_block(close, Sp, sign, weeks, rng); assert t2["placement_null"]["pct_rank"] == 1.0 and t2["event_shift_null"]["pct_rank"] > 0.99 and t2["placement_zero_reproduces"], t2["placement_null"]
    log(f"  T2 on a synthetic signed move: {t2['y_post_30']['mean_bp']:+.1f} bp, placement rank {t2['placement_null']['pct_rank']:.2f}, event-shift rank {t2['event_shift_null']['pct_rank']:.3f}")
    expect_raise(lambda: audit_right_quantity(M, M), "the same matrix twice", log); expect_raise(lambda: guard_outputs({"spec": 1}), "missing outputs", log)
    log("  selftest: every audit passes its clean case and raises on its break"); return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--selftest", action="store_true"); ap.add_argument("--run", action="store_true"); a = ap.parse_args()
    sys.exit(selftest() if a.selftest else run() if a.run else 1)
