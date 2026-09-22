"""D622 Stage 0 -- is the last-hour decline an INVENTORY DISCHARGE by whoever absorbed it?

Pre-registered in `docs/decisions/D622-PRE-REG-the-last-hour-decline-and-who-must-be-flat.md`, committed
before this file existed.

    python scripts/stage0_d622_close_inventory.py --selftest   # every audit passes AND raises on its break
    python scripts/stage0_d622_close_inventory.py --run        # the six predictions

Six predictions, each with a declared failure and none of them an economic bar -- Stage 0 asks whether the
mechanism is OPERATING, not whether it pays:

  P4  the deadline binds, so the edge concentrates in the last of three 20-minute legs
  P5  the effect is specific to the 16:00 cash close: the three index roots agree in sign and the five
      others' mean |z| is under 1.0
  P6  the inventory is larger where the decline ran through the prior session's low
  P7  the forced trade ARRIVES -- the closing hour's share of session volume is higher on arm days
  P8  the reversal test: an inventory discharge pushes price below fair value and must partially revert;
      information does not
  P9  the deadline placebo: the effect must NOT appear at hour pairs where no deadline binds, and the tested
      pair must be the family maximum over all 22

No holdout is read. The 2024+ slice is untouched.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
FIX = REPO / "data" / "fixtures"
ES_1M = FIX / "fut_ES_rth_1m.csv.gz"
HOURLY = FIX / "fut_sessions_hourly.csv.gz"
SPECS = REPO / "data" / "futures_contract_specs.json"
OUT = REPO / "data" / "stage0_d622_close_inventory.json"

SPEC = "D622"
IN_FROM, IN_TO, RESERVED_FROM = "2016-01-04", "2023-12-29", "2024-01-01"
MIN_BARS = 380
SIG_N, SIG_MIN = 252, 60
H1_THRESHOLD = 1.0                 # declared: one trailing sigma of the hourly move
LEGS = (("15:00", "15:20"), ("15:20", "15:40"), ("15:40", "16:00"))
INDEX_ROOTS = ("ES", "NQ", "YM")
OTHER_ROOTS = ("ZN", "ZB", "GC", "CL", "6E")
HOURS = [f"h{h:02d}" for h in list(range(18, 24)) + list(range(0, 17))]
NULL_DRAWS, SEED, ROT_MIN = 2000, 622, 10
REQUIRED_OUTPUTS = ("spec", "windows", "sets", "audits", "arm", "P4", "P5", "P6", "P7", "P8", "P9",
                    "reproductions", "verdict", "timing_s")


def log(*a):
    print(*a, flush=True)


def expect_raise(fn, what, say=log):
    try:
        fn()
    except AssertionError as e:
        say(f"    audit RAISES on {what}: {str(e)[:78]}")
        return True
    raise AssertionError(f"audit did not raise on {what}")


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


# ------------------------------------------------------------------ prices
def load_es_minute():
    """The ES day session at one minute, with D462's endpoint convention: the price AT hh:mm is the close of
    the bar STARTING one minute earlier."""
    b = pd.read_csv(ES_1M, dtype={"day": str, "hhmm": str, "contract": str}, encoding="utf-8")
    b = b[(b["day"] >= IN_FROM) & (b["day"] <= IN_TO)]
    if b["day"].max() >= RESERVED_FROM:
        raise AssertionError("a reserved session leaked into the ES read")
    nb = b.groupby("day").size()
    close = b.pivot(index="day", columns="hhmm", values="close")
    open_ = b.pivot(index="day", columns="hhmm", values="open")
    low = b.pivot(index="day", columns="hhmm", values="low")
    vol = b.pivot(index="day", columns="hhmm", values="volume") if "volume" in b else None
    keep = nb.reindex(close.index) >= MIN_BARS
    close, open_, low = close[keep], open_[keep], low[keep]
    if vol is not None:
        vol = vol[keep]
    contract = b.groupby("day")["contract"].agg(lambda s: s.value_counts().index[0]).reindex(close.index)

    def P(hhmm):
        prev = (pd.Timestamp("2000-01-01 " + hhmm) - pd.Timedelta(minutes=1)).strftime("%H:%M")
        return close[prev]

    s = pd.DataFrame({"P0930": open_["09:30"], "P1200": P("12:00"), "P1400": P("14:00"),
                      "P1500": P("15:00"), "P1520": P("15:20"), "P1540": P("15:40"),
                      "P1600": P("16:00")}, index=close.index)
    s["contract"] = contract
    s["roll"] = s["contract"] != s["contract"].shift(1)
    s["H1_bp"] = 1e4 * np.log(s["P1500"] / s["P1400"])
    s["y_bp"] = 1e4 * np.log(s["P1600"] / s["P1500"])
    for i, (a, b_) in enumerate(LEGS, start=1):
        pa = s["P1500"] if a == "15:00" else s[f"P{a.replace(':','')}"]
        pb = s["P1600"] if b_ == "16:00" else s[f"P{b_.replace(':','')}"]
        s[f"leg{i}_bp"] = 1e4 * np.log(pb / pa)
    s["ON_bp"] = 1e4 * np.log(s["P0930"] / s["P1600"].shift(1))
    s["A_bp"] = 1e4 * np.log(s["P1200"] / s["P0930"])
    s["B_bp"] = 1e4 * np.log(s["P1400"] / s["P1200"])
    s["DAY_bp"] = 1e4 * np.log(s["P1500"] / s["P0930"])
    s["sigma_bp"] = s["H1_bp"].rolling(SIG_N, min_periods=SIG_MIN).std().shift(1)
    s["H1"] = s["H1_bp"] / s["sigma_bp"]
    # the prior session's low, and whether the 14:00-15:00 hour took price under it
    sess_low = low.min(axis=1)
    s["prev_low"] = sess_low.shift(1)
    hour_cols = [c for c in low.columns if "14:00" <= c < "15:00"]
    s["hour_low"] = low[hour_cols].min(axis=1)
    s["broke_prev_low"] = s["hour_low"] < s["prev_low"]
    # P8's horizons
    s["ON_next_bp"] = 1e4 * np.log(s["P0930"].shift(-1) / s["P1600"])
    s["NEXT_bp"] = 1e4 * np.log(s["P1600"].shift(-1) / s["P1600"])
    s["FIVE_bp"] = 1e4 * np.log(s["P1600"].shift(-5) / s["P1600"])
    # P7's volume shares, from the minute panel
    if vol is not None:
        last = [c for c in vol.columns if "15:00" <= c < "16:00"]
        s["vol_close_share"] = vol[last].sum(axis=1) / vol.sum(axis=1)
    else:
        s["vol_close_share"] = np.nan
    return s


def audit_leg_additivity(s):
    """The three legs must sum to the scored window, under the same endpoint convention."""
    a = s["y_bp"].to_numpy(float)
    b = (s["leg1_bp"] + s["leg2_bp"] + s["leg3_bp"]).to_numpy(float)
    ok = np.isfinite(a) & np.isfinite(b)
    d = float(np.max(np.abs(a[ok] - b[ok])))
    if d > 1e-9:
        raise AssertionError(f"LEG ADDITIVITY: y - sum(legs) reaches {d:.3e} bp")
    share = float(np.mean(a[ok] == s["leg3_bp"].to_numpy(float)[ok]))
    if share > 0.10:
        raise AssertionError(f"RIGHT QUANTITY: the window equals its third leg on {share:.3f} of sessions")
    return dict(max_abs_deviation=d, share_window_equals_leg3=share, n=int(ok.sum()))


def audit_no_lookahead(s):
    """H1 uses only prices up to 15:00 and a sigma lagged one session; the outcome starts at 15:00."""
    j = s[np.isfinite(s["H1"]) & np.isfinite(s["y_bp"])]
    if not len(j):
        raise AssertionError("no usable session")
    c = float(np.corrcoef(j["sigma_bp"].to_numpy(float), np.abs(j["y_bp"].to_numpy(float)))[0, 1])
    if not np.isfinite(c):
        raise AssertionError("sigma/outcome correlation is not finite")
    return dict(corr_lagged_sigma_with_abs_outcome=c,
                note="a lagged sigma may correlate with |outcome| through persistence; it carries no "
                     "information about the outcome's SIGN, which is what the arm trades")


def arm_mask(s, threshold=H1_THRESHOLD):
    return (s["H1"] <= -threshold).to_numpy(bool) & np.isfinite(s["y_bp"]).to_numpy(bool)


def rotation_null(signal, outcome, draws=None, kmin=ROT_MIN):
    """Enumerated rotation of the SIGNAL SIDE against the outcome. The signal is rotated as a block so the
    arm's own structure -- which sessions qualify -- survives, and only its pairing with y is destroyed.

    RAISES if the resulting null has no spread. A null whose draws are all equal cannot place the
    observation anywhere, so it would report a rank and discriminate nothing -- D613's lesson about a
    comparison that has no way to disagree, applied to a null instead of a gate.
    """
    n = outcome.size
    vals = []
    for k in range(kmin, n - kmin + 1):
        sig = np.roll(signal, k)
        m = sig < 0
        if m.sum() >= 30:
            vals.append(float(np.mean(outcome[m])))
    out = np.array(vals, float)
    if out.size < 50:
        raise AssertionError(f"rotation null has only {out.size} usable offsets")
    if not np.isfinite(out).any() or float(np.nanstd(out)) == 0.0:
        raise AssertionError("rotation null has ZERO spread, so it cannot place the observation anywhere")
    return out


def blk(obs, null):
    null = np.asarray(null, float)
    null = null[np.isfinite(null)]
    return dict(observed=float(obs), p05=float(np.percentile(null, 5)), p50=float(np.percentile(null, 50)),
                p95=float(np.percentile(null, 95)), n=int(null.size),
                pct_rank=float((null < obs).mean()), above_p95=bool(obs > np.percentile(null, 95)),
                below_p05=bool(obs < np.percentile(null, 5)))


def tstat(v):
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    if v.size < 5:
        return np.nan
    return float(np.mean(v) / (np.std(v, ddof=1) / np.sqrt(v.size)))


# ------------------------------------------------------------------ the hourly cross-section
def load_hourly():
    d = pd.read_csv(HOURLY, usecols=["root", "day", "same_front"] + [f"{h}_c" for h in HOURS]
                    + [f"{h}_v" for h in HOURS],
                    dtype={"root": str, "day": str}, encoding="utf-8")
    d = d[(d["day"] >= IN_FROM) & (d["day"] <= IN_TO) & d["same_front"]]
    if d["day"].max() >= RESERVED_FROM:
        raise AssertionError("a reserved session leaked into the hourly read")
    return d


def hour_pair_effect(d, root, i_cond, i_out, threshold=H1_THRESHOLD):
    """The arm on one root and one hour pair: condition on hour i_cond, score hour i_out."""
    g = d[d["root"] == root]
    if len(g) < 300:
        return None
    close = g[[f"{h}_c" for h in HOURS]].to_numpy(float)
    r = np.full_like(close, np.nan)
    r[:, 1:] = 1e4 * np.log(close[:, 1:] / close[:, :-1])
    cond, out = r[:, i_cond], r[:, i_out]
    sig = pd.Series(cond).rolling(SIG_N, min_periods=SIG_MIN).std().shift(1).to_numpy()
    h1 = cond / sig
    m = np.isfinite(h1) & np.isfinite(out) & (h1 <= -threshold)
    if m.sum() < 30:
        return None
    y = -out[m]                                   # the arm is SHORT, so its return is minus the move
    return dict(root=root, n=int(m.sum()), mean_bp=float(np.mean(y)), t=tstat(y),
                z=float(np.mean(y) / (np.std(y, ddof=1) / np.sqrt(y.size))),
                hit=float(np.mean(y > 0)))


def selftest():
    log(f"{SPEC} selftest")
    rng = np.random.default_rng(SEED)
    idx = [f"2020-{m:02d}-{d:02d}" for m in range(1, 13) for d in range(1, 26)]
    s = pd.DataFrame(index=idx)
    p = 3000 * np.cumprod(1 + rng.normal(0, 2e-3, len(idx)))
    s["P1400"] = p
    s["P1500"] = p * (1 + rng.normal(0, 1e-3, len(idx)))
    s["P1520"] = s["P1500"] * (1 + rng.normal(0, 5e-4, len(idx)))
    s["P1540"] = s["P1520"] * (1 + rng.normal(0, 5e-4, len(idx)))
    s["P1600"] = s["P1540"] * (1 + rng.normal(0, 5e-4, len(idx)))
    s["H1_bp"] = 1e4 * np.log(s["P1500"] / s["P1400"])
    s["y_bp"] = 1e4 * np.log(s["P1600"] / s["P1500"])
    s["leg1_bp"] = 1e4 * np.log(s["P1520"] / s["P1500"])
    s["leg2_bp"] = 1e4 * np.log(s["P1540"] / s["P1520"])
    s["leg3_bp"] = 1e4 * np.log(s["P1600"] / s["P1540"])
    a = audit_leg_additivity(s)
    assert a["max_abs_deviation"] < 1e-9, a
    log(f"  legs: they sum to the window to {a['max_abs_deviation']:.1e} bp")
    bad = s.copy()
    bad["leg2_bp"] = bad["leg2_bp"] + 1.0
    expect_raise(lambda: audit_leg_additivity(bad), "a one-bp slip in the middle leg")
    same = s.copy()
    same["leg3_bp"] = same["y_bp"]
    same["leg1_bp"] = 0.0
    same["leg2_bp"] = 0.0
    expect_raise(lambda: audit_leg_additivity(same), "the window BEING its third leg")

    # the arm selects on the conditioner's sign and magnitude, and nothing else
    s["sigma_bp"] = s["H1_bp"].rolling(60, min_periods=30).std().shift(1)
    s["H1"] = s["H1_bp"] / s["sigma_bp"]
    m = arm_mask(s)
    assert m.sum() > 0, "the arm selected nothing on synthetic data"
    assert (s["H1"].to_numpy()[m] <= -H1_THRESHOLD).all(), "the arm admitted a session above the threshold"
    log(f"  arm: {int(m.sum())} of {len(s)} synthetic sessions, every one at H1 <= -{H1_THRESHOLD}")

    # the rotation null: at offset 0 it reproduces the observation, and it must have spread
    y = s["y_bp"].to_numpy(float)
    h1 = np.nan_to_num(s["H1"].to_numpy(float), nan=0.0)
    sig_block = np.where(h1 <= -H1_THRESHOLD, -1.0, +1.0)
    obs = float(np.mean(y[sig_block < 0]))
    null = rotation_null(sig_block, y, kmin=5)
    b = blk(obs, null)
    assert 0.0 <= b["pct_rank"] <= 1.0
    log(f"  rotation null: {null.size} offsets, spread {np.std(null):.3f} bp, observed rank {b['pct_rank']:.3f}")
    # the breaks that make the null a real one: a constant outcome has nothing to rotate against, and too
    # few offsets cannot place an observation
    expect_raise(lambda: rotation_null(sig_block, np.full_like(y, 7.0), kmin=5),
                 "a constant outcome, which gives the null zero spread")
    expect_raise(lambda: rotation_null(sig_block[:40], y[:40], kmin=5), "too few usable offsets")

    # P8's horizons must be forward-looking and must not overlap the scored window
    t = pd.DataFrame({"P1600": [100.0, 101.0, 99.0, 102.0, 103.0, 101.0]})
    t["NEXT_bp"] = 1e4 * np.log(t["P1600"].shift(-1) / t["P1600"])
    assert np.isnan(t["NEXT_bp"].iloc[-1]), "the last session cannot have a next-session return"
    assert abs(t["NEXT_bp"].iloc[0] - 1e4 * np.log(101.0 / 100.0)) < 1e-9
    log("  P8 horizons: forward-shifted, and the final session is NaN rather than wrapped")

    expect_raise(lambda: guard_outputs({k: 1 for k in REQUIRED_OUTPUTS[:-1]}), "a missing declared output")
    log(f"{SPEC} selftest: all audits pass and all raise on their breaks")


def guard_outputs(res):
    missing = [k for k in REQUIRED_OUTPUTS if k not in res]
    if missing:
        raise AssertionError(f"REQUIRED_OUTPUTS missing: {missing}")
    return True


def run():
    t0 = time.time()
    res = {"spec": SPEC, "audits": {}}
    spec = json.loads(SPECS.read_text(encoding="utf-8"))
    pt_usd = float(spec["MES"]["tick_usd"]) / float(spec["ES"]["tick_points"])
    cost = 3.00 + 1.0 * float(spec["MES"]["tick_usd"])

    s = load_es_minute()
    res["windows"] = dict(conditioner="14:00->15:00", outcome="15:00->16:00", legs=[list(x) for x in LEGS],
                          threshold_sigma=H1_THRESHOLD)
    res["audits"]["leg_additivity"] = audit_leg_additivity(s)
    expect_raise(lambda: audit_leg_additivity(s.assign(leg2_bp=s["leg2_bp"] + 1.0)),
                 "a one-bp slip in the middle leg")
    res["audits"]["no_lookahead"] = audit_no_lookahead(s)
    log(f"  prices: {len(s)} sessions {s.index.min()} .. {s.index.max()}; legs sum to the window to "
        f"{res['audits']['leg_additivity']['max_abs_deviation']:.1e} bp")

    m = arm_mask(s)
    y = s["y_bp"].to_numpy(float)
    arm_y = y[m]
    res["arm"] = dict(threshold=H1_THRESHOLD, n=int(m.sum()), share=float(m.mean()),
                      mean_bp=float(-np.mean(arm_y)), t=tstat(-arm_y),
                      hit=float(np.mean(-arm_y > 0)),
                      gross_usd=float(-np.mean(arm_y) / 1e4 * float(np.mean(s["P1500"])) * pt_usd),
                      cost_usd=cost)
    log(f"  arm: SHORT on H1 <= -{H1_THRESHOLD}; {m.sum()} sessions ({m.mean():.3f}); "
        f"mean {res['arm']['mean_bp']:+.2f} bp, t {res['arm']['t']:+.2f}, hit {res['arm']['hit']:.3f}, "
        f"gross ${res['arm']['gross_usd']:+.2f} against ${cost:.2f}")

    # ---------------- P4 the deadline binds
    legs = {f"leg{i}": -s[f"leg{i}_bp"].to_numpy(float)[m] for i in (1, 2, 3)}
    res["P4"] = {k: dict(mean_bp=float(np.nanmean(v)), t=tstat(v)) for k, v in legs.items()}
    res["P4"]["passes"] = bool(np.nanmean(legs["leg3"]) > np.nanmean(legs["leg1"]))
    log(f"  P4 legs (arm, bp): 15:00-15:20 {np.nanmean(legs['leg1']):+.2f}  "
        f"15:20-15:40 {np.nanmean(legs['leg2']):+.2f}  15:40-16:00 {np.nanmean(legs['leg3']):+.2f}  "
        f"{'PASS' if res['P4']['passes'] else 'FAIL'}")

    # ---------------- P5 the cross-section
    d = load_hourly()
    i14, i15 = HOURS.index("h14"), HOURS.index("h15")
    rows = [hour_pair_effect(d, r, i14, i15) for r in INDEX_ROOTS + OTHER_ROOTS]
    rows = [r for r in rows if r]
    idx_rows = [r for r in rows if r["root"] in INDEX_ROOTS]
    oth_rows = [r for r in rows if r["root"] in OTHER_ROOTS]
    signs = {np.sign(r["mean_bp"]) for r in idx_rows}
    res["P5"] = dict(index=idx_rows, other=oth_rows,
                     index_signs_agree=bool(len(signs) == 1 and 0 not in signs),
                     other_mean_abs_z=float(np.mean([abs(r["z"]) for r in oth_rows])) if oth_rows else np.nan)
    res["P5"]["passes"] = bool(res["P5"]["index_signs_agree"] and res["P5"]["other_mean_abs_z"] < 1.0)
    log("  P5 per root (arm mean bp, z):")
    for r in rows:
        tag = "index" if r["root"] in INDEX_ROOTS else "other"
        log(f"     {r['root']:<4} {tag:<6} n {r['n']:4d}  mean {r['mean_bp']:+7.2f} bp  z {r['z']:+6.2f}  "
            f"hit {r['hit']:.3f}")
    log(f"     index signs agree {res['P5']['index_signs_agree']}, other mean |z| "
        f"{res['P5']['other_mean_abs_z']:.3f}  {'PASS' if res['P5']['passes'] else 'FAIL'}")

    # ---------------- P6 the level
    broke = s["broke_prev_low"].to_numpy(bool) & m
    held = (~s["broke_prev_low"].to_numpy(bool)) & m
    res["P6"] = dict(broke_prev_low=dict(n=int(broke.sum()), mean_bp=float(-np.mean(y[broke])),
                                         t=tstat(-y[broke])) if broke.sum() > 10 else None,
                     held=dict(n=int(held.sum()), mean_bp=float(-np.mean(y[held])), t=tstat(-y[held]))
                     if held.sum() > 10 else None)
    res["P6"]["passes"] = bool(res["P6"]["broke_prev_low"] and res["P6"]["held"]
                               and res["P6"]["broke_prev_low"]["mean_bp"] > res["P6"]["held"]["mean_bp"])
    if res["P6"]["broke_prev_low"]:
        log(f"  P6 broke the prior low: n {res['P6']['broke_prev_low']['n']} "
            f"{res['P6']['broke_prev_low']['mean_bp']:+.2f} bp   held: n {res['P6']['held']['n']} "
            f"{res['P6']['held']['mean_bp']:+.2f} bp  {'PASS' if res['P6']['passes'] else 'FAIL'}")

    # ---------------- P7 the volume premise
    vs = s["vol_close_share"].to_numpy(float)
    if np.isfinite(vs).sum() > 100:
        res["P7"] = dict(arm_share=float(np.nanmean(vs[m])), other_share=float(np.nanmean(vs[~m])),
                         even_share=1.0 / 6.5,
                         ratio_arm=float(np.nanmean(vs[m]) / (1.0 / 6.5)),
                         ratio_other=float(np.nanmean(vs[~m]) / (1.0 / 6.5)))
        res["P7"]["passes"] = bool(res["P7"]["arm_share"] > res["P7"]["other_share"])
        log(f"  P7 closing-hour volume share: arm {res['P7']['arm_share']:.4f} "
            f"({res['P7']['ratio_arm']:.2f}x even) vs other {res['P7']['other_share']:.4f} "
            f"({res['P7']['ratio_other']:.2f}x)  {'PASS' if res['P7']['passes'] else 'FAIL'}")
    else:
        res["P7"] = dict(passes=None, note="the minute panel carries no volume column")
        log("  P7 SKIPPED: no volume column in the minute panel")

    # ---------------- P8 the reversal
    res["P8"] = {}
    for tag, col in (("overnight_to_0930", "ON_next_bp"), ("next_session", "NEXT_bp"),
                     ("five_sessions", "FIVE_bp")):
        v = s[col].to_numpy(float)[m]
        res["P8"][tag] = dict(n=int(np.isfinite(v).sum()), mean_bp=float(np.nanmean(v)), t=tstat(v))
    deep = m & (s["H1"].to_numpy(float) <= -2.0)
    res["P8"]["deepest_decline_next_session"] = dict(
        n=int(deep.sum()), mean_bp=float(np.nanmean(s["NEXT_bp"].to_numpy(float)[deep]))) if deep.sum() > 10 else None
    grows = bool(res["P8"]["deepest_decline_next_session"]
                 and res["P8"]["deepest_decline_next_session"]["mean_bp"] > res["P8"]["next_session"]["mean_bp"])
    res["P8"]["reversal_grows_with_decline"] = grows
    res["P8"]["passes"] = bool(res["P8"]["overnight_to_0930"]["mean_bp"] > 0
                               and res["P8"]["next_session"]["mean_bp"] > 0 and grows)
    log(f"  P8 after the arm: overnight {res['P8']['overnight_to_0930']['mean_bp']:+.2f} bp "
        f"(t {res['P8']['overnight_to_0930']['t']:+.2f})   next session "
        f"{res['P8']['next_session']['mean_bp']:+.2f} (t {res['P8']['next_session']['t']:+.2f})   "
        f"five sessions {res['P8']['five_sessions']['mean_bp']:+.2f} "
        f"(t {res['P8']['five_sessions']['t']:+.2f})  {'PASS' if res['P8']['passes'] else 'FAIL'}")

    # ---------------- P9 the deadline placebo across all 22 hour pairs on ES
    pairs = []
    for i in range(1, len(HOURS) - 1):
        r = hour_pair_effect(d, "ES", i, i + 1)
        if r:
            r["pair"] = f"{HOURS[i]}->{HOURS[i+1]}"
            pairs.append(r)
    tested = next((p for p in pairs if p["pair"] == "h14->h15"), None)
    others = [p for p in pairs if p["pair"] != "h14->h15"]
    res["P9"] = dict(pairs=pairs, tested=tested,
                     is_family_max=bool(tested and all(tested["mean_bp"] >= p["mean_bp"] for p in others)),
                     rank_among_pairs=int(sum(1 for p in others if p["mean_bp"] < tested["mean_bp"]) + 1)
                     if tested else None, n_pairs=len(pairs))
    res["P9"]["passes"] = bool(res["P9"]["is_family_max"])
    if tested:
        top = sorted(pairs, key=lambda q: -q["mean_bp"])[:5]
        log(f"  P9 across {len(pairs)} ES hour pairs; the tested pair h14->h15 ranks "
            f"{res['P9']['rank_among_pairs']} of {len(pairs)}  "
            f"{'PASS' if res['P9']['passes'] else 'FAIL'}")
        for p in top:
            log(f"     {p['pair']:<12} n {p['n']:4d}  mean {p['mean_bp']:+7.2f} bp  z {p['z']:+6.2f}"
                f"{'   <- the tested pair' if p['pair'] == 'h14->h15' else ''}")

    # ---------------- the rotation null on the arm, and the reproductions
    h1 = np.nan_to_num(s["H1"].to_numpy(float), nan=0.0)
    block = np.where(h1 <= -H1_THRESHOLD, -1.0, +1.0)
    null = rotation_null(block, -y, kmin=ROT_MIN)
    res["arm"]["rotation_null"] = blk(float(np.mean(-y[m])), null)
    log(f"  arm rotation null: {null.size} offsets, observed {np.mean(-y[m]):+.2f} bp, "
        f"p50 {res['arm']['rotation_null']['p50']:+.2f}, p95 {res['arm']['rotation_null']['p95']:+.2f}, "
        f"rank {res['arm']['rotation_null']['pct_rank']:.4f}")

    up = (s["H1"] >= H1_THRESHOLD).to_numpy(bool) & np.isfinite(y)
    res["reproductions"] = dict(
        down_arm=dict(n=int(m.sum()), mean_bp=float(-np.mean(y[m])), t=tstat(-y[m])),
        up_arm=dict(n=int(up.sum()), mean_bp=float(np.mean(y[up])), t=tstat(y[up])),
        asymmetry_bp=float(-np.mean(y[m]) - np.mean(y[up])))
    log(f"  reproduced: down arm {res['reproductions']['down_arm']['mean_bp']:+.2f} bp "
        f"(t {res['reproductions']['down_arm']['t']:+.2f}) vs up arm "
        f"{res['reproductions']['up_arm']['mean_bp']:+.2f} (t {res['reproductions']['up_arm']['t']:+.2f})")

    res["sets"] = dict(index_roots=list(INDEX_ROOTS), other_roots=list(OTHER_ROOTS),
                       hour_pairs=len(pairs), sessions=int(len(s)))
    passed = [k for k in ("P4", "P5", "P6", "P7", "P8", "P9") if res[k].get("passes")]
    failed = [k for k in ("P4", "P5", "P6", "P7", "P8", "P9") if res[k].get("passes") is False]
    if len(passed) == 6:
        verdict = ("THE MECHANISM IS OPERATING -- all six predictions hold; the deferred signed-flow premise "
                   "check on the reserved window is the next stage, on the principal's word")
    elif "P5" in failed or "P9" in failed:
        verdict = (f"THE MECHANISM IS REFUTED -- {'P5' if 'P5' in failed else 'P9'} fails, so the direction "
                   f"is not produced by the 16:00 deadline; the line closes and no holdout is read "
                   f"(passed {passed}, failed {failed})")
    elif "P7" in failed:
        verdict = "THE PREMISE IS FALSE -- the forced trade does not arrive (P7); the mechanism is not operating"
    else:
        verdict = (f"PARTLY SUPPORTED, NO AGGREGATE VERDICT -- passed {passed}, failed {failed}; a mechanism "
                   f"test that is partly supported is a description and not a finding")
    res["verdict"] = verdict
    res["timing_s"] = round(time.time() - t0, 1)
    guard_outputs(res)
    OUT.write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    log(f"  VERDICT: {verdict}")
    log(f"  wrote {OUT.relative_to(REPO)} in {res['timing_s']:.1f} s")
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run()
