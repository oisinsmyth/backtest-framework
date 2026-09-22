"""D623 CENSUS -- who actually sells into the close, and is it a cascade?

Pre-registered in `docs/decisions/D623-PRE-REG-the-signed-flow-census-who-sells-into-the-close.md`,
committed alone before this file existed (R8).

    python scripts/census_d623_signed_close_flow.py --selftest   # every audit passes AND raises on its break
    python scripts/census_d623_signed_close_flow.py --run        # the five questions

A CENSUS, not a study. **No return is scored.** Prices are read to CLASSIFY sessions -- the arm, and the
midday volume burst -- and every measured quantity is a flow statistic from
`data/fixtures/fut_micro_flow_5m.csv.gz`. `audit_measured_quantities_are_flow` enforces that: each
comparison names the quantity it measures and the guard raises if that name is not in `MEASURED`.

The five questions, each with a declared direction and a declared failure (pre-registration section 4):

  Q1  is the closing flow one-sided?      arm-session 15:00-16:00 imbalance (sell-buy)/(sell+buy) > 0
                                          and larger than on non-arm sessions
  Q2  does it accelerate into the deadline?  slope of imbalance on bucket index, and last-two minus
                                          first-two of the twelve closing buckets
  Q3  is it small lots?                   the <=2-lot share of volume rises in the trigger and closing
                                          hours on arm sessions, against non-arm sessions AND against
                                          the same session's own midday baseline
  Q4  MES against ES                      the imbalance and the small-lot effect are more extreme in the
                                          micro contract, paired within session
  Q5  the detection regime                a midday volume burst predicts a larger closing imbalance

Every comparison is judged by D373's rule through `resolve()`: a margin inside two standard errors is
UNRESOLVED, not a pass and not a fail. Medians and both-tail trims sit beside every mean through
`tails()`, and the sessions carrying each tail are named (D322). Both are reused from the D622 runner,
which is where the amendment that produced them lives.

D485's reserve: the fixture spans 2025-09-11 -> 2026-09-10 and this census reads only to **2026-06-30**.
2026-07-01 -> 2026-09-10 stays unread, asserted from both sides.
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
FLOW = FIX / "fut_micro_flow_5m.csv.gz"
ES_1M = FIX / "fut_ES_rth_1m.csv.gz"
OUT = REPO / "data" / "census_d623_signed_close_flow.json"

SPEC = "D623"
# --------------------------------------------------------------- declared before the run
CENSUS_FROM, CENSUS_TO = "2025-09-11", "2026-06-30"   # section 1a: D485's in-sample end; the rest unread
RESERVE_FROM = "2026-07-01"
MIN_BARS = 380
# sigma on a one-year window cannot be D622's trailing 252 (section 3). Declared here instead, and the
# census reports a QUANTILE arm beside it so the threshold is not the only definition on offer.
SIG_N, SIG_MIN = 60, 30
H1_THRESHOLD = 1.0
ARM_QUANTILE = 0.12
MIN_ARM = 12                                          # section 3: below this the census stops
CLOSE_MIN, TRIG_MIN, MID_MIN = (900, 960), (840, 900), (660, 840)   # ET minutes since midnight
N_CLOSE_BUCKETS = 12
BURST_BASE_N, BURST_HI = 20, 1.25                     # section 5b of D622, unchanged
ROOTS = ("ES", "MES", "NQ", "MNQ")
PAIRS = (("MES", "ES"), ("MNQ", "NQ"))
NULL_MIN_OFFSETS, NULL_MIN_ARM = 50, 12
# Q1's declared failure is SYMMETRY, and no t-test establishes an equivalence. A material one-sided flow is
# declared as this fraction of the cross-session sd of the SAME quantity on non-arm sessions -- sessions the
# claim is not about -- so the benchmark is not read off the arm it judges.
MATERIAL_SD_FRAC = 0.5

# The declared-output guard. Every comparison names its quantity and the guard raises on anything else --
# in particular on a price-derived name, which is what keeps this a census.
MEASURED = frozenset({
    "imb_close", "imb_trig", "imb_mid", "imb_slope", "imb_last2_first2",
    "small_share_close", "small_share_trig", "small_share_mid", "lot1_share_close",
    "uns_share_close", "vol_close_share_flow", "n_close", "imb_close_minus_mid",
    "small_share_close_minus_mid", "small_share_trig_minus_mid",
    "small_vol_ratio_log", "vol_ratio_log", "excess_small_growth_log",
})
CLASSIFIERS = frozenset({"H1", "H1_bp", "sigma_bp", "burst", "P1400", "P1500", "mid_vol"})
REQUIRED_OUTPUTS = ("spec", "window", "audits", "arm", "coverage", "Q1", "Q2", "Q3", "Q4", "Q5",
                    "multiplicity", "verdicts", "verdict", "timing_s")


def log(*a):
    print(*a, flush=True)


def expect_raise(fn, what, say=log):
    try:
        fn()
    except AssertionError as e:
        say(f"    audit RAISES on {what}: {str(e)[:82]}")
        return True
    raise AssertionError(f"audit did not raise on {what}")


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


D622 = _load("d622", "stage0_d622_close_inventory.py")
resolve, tails, MARGIN_SE = D622.resolve, D622.tails, D622.MARGIN_SE


# ================================================================ the flow panel
def load_flow(path=FLOW, census_to=CENSUS_TO):
    """Signed five-minute flow, restricted to the census window, with the clock re-derived independently.

    `minute` is minutes since ET midnight of `bucket_start`. The census never trusts that column alone: a
    second path recomputes it from the timestamp and the two must agree, because every window in this file
    is a slice of it and a one-hour error would move all five questions at once.
    """
    d = pd.read_csv(path, usecols=["root", "session", "bucket_start", "minute", "rth", "n", "vol",
                                   "buy", "sell", "uns", "lot1", "lot_le2", "at_bid", "at_ask", "agree"],
                    dtype={"root": str, "session": str}, encoding="utf-8")
    ts = pd.to_datetime(d["bucket_start"])
    second = ts.dt.hour.to_numpy("int64") * 60 + ts.dt.minute.to_numpy("int64")
    bad = int((second != d["minute"].to_numpy("int64")).sum())
    if bad:
        raise AssertionError(f"CLOCK: `minute` disagrees with bucket_start on {bad} rows")
    d = d[(d["session"] >= CENSUS_FROM) & (d["session"] <= census_to)].copy()
    if len(d) and d["session"].max() >= RESERVE_FROM:
        raise AssertionError(f"RESERVE: a session at or after {RESERVE_FROM} entered the flow read")
    return d


def audit_window(d, census_to=CENSUS_TO):
    """D485's reserve, asserted from BOTH sides: nothing at or after the reserve start, and the window
    actually reaches its declared end (a filter that silently kept nothing would pass a one-sided check)."""
    if not len(d):
        raise AssertionError("WINDOW: the census read no rows")
    lo, hi = d["session"].min(), d["session"].max()
    if hi >= RESERVE_FROM:
        raise AssertionError(f"WINDOW: last session {hi} is inside the reserve")
    if lo < CENSUS_FROM:
        raise AssertionError(f"WINDOW: first session {lo} precedes the fixture's declared start")
    if hi > census_to:
        raise AssertionError(f"WINDOW: last session {hi} exceeds the declared end {census_to}")
    return dict(first=lo, last=hi, sessions=int(d["session"].nunique()), rows=int(len(d)),
                reserve_from=RESERVE_FROM)


def audit_measured_quantities_are_flow(names):
    """The declared-output guard. A census that emitted a return would be spending the slice it declares
    unspent, so the permitted quantity names are enumerated and anything else raises -- prose cannot do
    this job (memory: declared outputs need a guard, not prose)."""
    # the classifier check runs FIRST, so a price name reaches its own message instead of being swallowed
    # by the generic one -- otherwise that branch is unreachable and its break tests nothing
    leak = sorted(set(names) & CLASSIFIERS)
    if leak:
        raise AssertionError(f"DECLARED OUTPUTS: {leak} is a price classifier and cannot be a measured "
                             "quantity in a census")
    extra = sorted(set(names) - MEASURED)
    if extra:
        raise AssertionError(f"DECLARED OUTPUTS: {extra} is not a flow quantity in MEASURED")
    return dict(measured=sorted(set(names)), permitted=sorted(MEASURED), classifiers=sorted(CLASSIFIERS))


def imbalance(sell, buy):
    """(sell - buy) / (sell + buy): POSITIVE means net sell-initiated, which is Q1's declared direction."""
    sell = np.asarray(sell, float)
    buy = np.asarray(buy, float)
    tot = sell + buy
    out = np.full(tot.shape, np.nan)
    ok = tot > 0
    out[ok] = (sell[ok] - buy[ok]) / tot[ok]
    return out


def audit_imbalance_sign(fn=imbalance):
    """Sign audit in the census's own units: a bucket with more sell-initiated volume must read POSITIVE,
    and swapping the two arguments must flip it. A sign asserted in prose inverted D280."""
    v = float(fn([700.0], [300.0])[0])
    if not (v > 0 and abs(v - 0.4) < 1e-12):
        raise AssertionError(f"SIGN: sell-heavy bucket reads {v:+.6f}, expected +0.400000")
    w = float(fn([300.0], [700.0])[0])
    if not (w < 0 and abs(w + 0.4) < 1e-12):
        raise AssertionError(f"SIGN: buy-heavy bucket reads {w:+.6f}, expected -0.400000")
    z = fn([0.0], [0.0])[0]
    if np.isfinite(z):
        raise AssertionError("SIGN: an empty bucket must be NaN, not a number")
    return dict(sell_heavy=v, buy_heavy=w, empty_is_nan=True)


def per_session(d):
    """One row per (root, session): the three windows' imbalances, the small-lot shares, the closing hour's
    bucket-level shape, and the coverage counts the drop rule reads."""
    out = []
    for (root, sess), g in d.groupby(["root", "session"], sort=True):
        m = g["minute"].to_numpy("int64")
        rec = dict(root=root, session=sess)
        for tag, (a, b) in (("close", CLOSE_MIN), ("trig", TRIG_MIN), ("mid", MID_MIN)):
            w = g[(m >= a) & (m < b)]
            sell, buy = float(w["sell"].sum()), float(w["buy"].sum())
            vol = float(w["vol"].sum())
            rec[f"imb_{tag}"] = float((sell - buy) / (sell + buy)) if sell + buy > 0 else np.nan
            rec[f"small_share_{tag}"] = float(w["lot_le2"].sum() / vol) if vol > 0 else np.nan
            rec[f"lot1_share_{tag}"] = float(w["lot1"].sum() / vol) if vol > 0 else np.nan
            rec[f"vol_{tag}"] = vol
            rec[f"small_{tag}"] = float(w["lot_le2"].sum())
            rec[f"n_{tag}"] = int(len(w))
        w = g[(m >= CLOSE_MIN[0]) & (m < CLOSE_MIN[1])].sort_values("minute")
        rec["uns_share_close"] = (float(w["uns"].sum() / w["vol"].sum()) if w["vol"].sum() > 0 else np.nan)
        rec["agree_close"] = (float(w["agree"].sum() / max(w["at_bid"].sum() + w["at_ask"].sum(), 1))
                              if len(w) else np.nan)
        rec["vol_close_share_flow"] = (float(w["vol"].sum() / g["vol"].sum()) if g["vol"].sum() > 0
                                       else np.nan)
        # Q2's shape, over the twelve five-minute buckets of the closing hour
        bi = imbalance(w["sell"].to_numpy(float), w["buy"].to_numpy(float))
        idx = np.arange(bi.size, dtype=float)
        ok = np.isfinite(bi)
        if ok.sum() >= 8 and np.ptp(idx[ok]) > 0:
            rec["imb_slope"] = float(np.polyfit(idx[ok], bi[ok], 1)[0])
        else:
            rec["imb_slope"] = np.nan
        if ok.sum() == bi.size and bi.size >= 4:
            rec["imb_last2_first2"] = float(np.mean(bi[-2:]) - np.mean(bi[:2]))
        else:
            rec["imb_last2_first2"] = np.nan
        out.append(rec)
    t = pd.DataFrame(out)
    for tag in ("close", "trig", "mid"):
        t[f"imb_{tag}_minus_mid"] = t[f"imb_{tag}"] - t["imb_mid"]
        t[f"small_share_{tag}_minus_mid"] = t[f"small_share_{tag}"] - t["small_share_mid"]
    # A SHARE can move because its numerator grew or because its denominator shrank, and those are opposite
    # readings of the same margin. The logged VOLUME ratios separate them: growth in small-lot contracts
    # against growth in the whole book, each measured against the same session's own midday window.
    # PER BUCKET, because midday is three hours against the close's one and an unnormalised ratio would
    # carry a log(12/36) constant. The constant cancels in an arm-minus-non-arm margin but not in a LEVEL,
    # and the level is what says whether the closing hour is small-lot heavy at all.
    with np.errstate(divide="ignore", invalid="ignore"):
        t["small_vol_ratio_log"] = np.log((t["small_close"] / t["n_close"])
                                          / (t["small_mid"] / t["n_mid"]))
        t["vol_ratio_log"] = np.log((t["vol_close"] / t["n_close"]) / (t["vol_mid"] / t["n_mid"]))
    t.loc[~np.isfinite(t["small_vol_ratio_log"]), "small_vol_ratio_log"] = np.nan
    t.loc[~np.isfinite(t["vol_ratio_log"]), "vol_ratio_log"] = np.nan
    t["excess_small_growth_log"] = t["small_vol_ratio_log"] - t["vol_ratio_log"]
    return t


def audit_close_bucket_coverage(t, need=N_CLOSE_BUCKETS):
    """The closing hour is twelve five-minute buckets. A (root, session) short of that is dropped, and the
    drop rule is a declared output rather than a silent filter -- D580's lesson that presence is the
    session, applied to a window inside one."""
    n = t["n_close"].to_numpy("int64")
    if n.max() > need:
        raise AssertionError(f"COVERAGE: a (root, session) carries {n.max()} closing buckets, above {need}")
    full = int((n == need).sum())
    if full < 0.5 * len(t):
        raise AssertionError(f"COVERAGE: only {full} of {len(t)} pairs carry {need} closing buckets")
    return dict(pairs=int(len(t)), full=full, dropped=int(len(t) - full),
                share_full=float(full / len(t)), need=need)


# ================================================================ the classifiers (prices, never scored)
def load_classifiers(path=ES_1M, census_to=CENSUS_TO):
    """The arm and the midday burst. D462's endpoint convention: the price AT hh:mm is the close of the bar
    STARTING one minute earlier. Nothing after 15:00 is read -- not P1600, not any close-window price --
    which is what makes the classification non-endogenous by construction rather than by assertion."""
    b = pd.read_csv(path, dtype={"day": str, "hhmm": str, "contract": str}, encoding="utf-8")
    b = b[(b["day"] >= CENSUS_FROM) & (b["day"] <= census_to)]
    nb = b.groupby("day").size()
    close = b.pivot(index="day", columns="hhmm", values="close")
    vol = b.pivot(index="day", columns="hhmm", values="volume")
    keep = nb.reindex(close.index) >= MIN_BARS
    close, vol = close[keep], vol[keep]

    def P(hhmm):
        prev = (pd.Timestamp("2000-01-01 " + hhmm) - pd.Timedelta(minutes=1)).strftime("%H:%M")
        return close[prev]

    s = pd.DataFrame({"P1400": P("14:00"), "P1500": P("15:00")}, index=close.index)
    s["H1_bp"] = 1e4 * np.log(s["P1500"] / s["P1400"])
    s["sigma_bp"] = s["H1_bp"].rolling(SIG_N, min_periods=SIG_MIN).std().shift(1)
    s["H1"] = s["H1_bp"] / s["sigma_bp"]
    mid = [c for c in vol.columns if "11:00" <= c < "14:00"]
    s["mid_vol"] = vol[mid].sum(axis=1)
    s["burst"] = s["mid_vol"] / s["mid_vol"].rolling(BURST_BASE_N, min_periods=BURST_BASE_N).median().shift(1)
    s.index.name = "session"
    return s.reset_index()


def audit_sigma_is_lagged(s):
    """sigma at session i must use H1 only up to i-1. Recomputed here by a second path that never calls
    rolling(), so a missing `.shift(1)` cannot pass."""
    h = s["H1_bp"].to_numpy(float)
    sg = s["sigma_bp"].to_numpy(float)
    worst, at = 0.0, None
    for i in range(len(s)):
        if not np.isfinite(sg[i]):
            continue
        past = h[max(0, i - SIG_N):i]
        past = past[np.isfinite(past)]
        if past.size < SIG_MIN:
            raise AssertionError(f"SIGMA: session {i} has a sigma on {past.size} past observations")
        ref = float(np.std(past, ddof=1))
        if abs(ref - sg[i]) > worst:
            worst, at = abs(ref - sg[i]), i
    if worst > 1e-9:
        raise AssertionError(f"SIGMA IS NOT LAGGED: second path differs by {worst:.3e} at row {at}")
    return dict(max_abs_deviation=worst, n_with_sigma=int(np.isfinite(sg).sum()))


def audit_arm_not_endogenous(s, path=ES_1M):
    """The arm must be identical when every price from 15:00 onward is destroyed. Re-derived from a panel
    whose close-window bars are overwritten, so the check reads the arm mask itself and not a comment."""
    b = pd.read_csv(path, dtype={"day": str, "hhmm": str, "contract": str}, encoding="utf-8")
    b = b[(b["day"] >= CENSUS_FROM) & (b["day"] <= CENSUS_TO)].copy()
    late = b["hhmm"] >= "15:00"
    rng = np.random.default_rng(623)
    b.loc[late, "close"] = rng.normal(5000.0, 50.0, int(late.sum()))
    b.loc[late, "volume"] = rng.integers(1, 10_000, int(late.sum()))
    t = b.to_csv(index=False, encoding="utf-8")
    from io import StringIO
    s2 = load_classifiers(StringIO(t))
    a1 = set(s.loc[arm_mask(s), "session"])
    a2 = set(s2.loc[arm_mask(s2), "session"])
    if a1 != a2:
        raise AssertionError(f"ARM IS ENDOGENOUS: {len(a1 ^ a2)} sessions change when 15:00+ is destroyed")
    return dict(arm_sessions=len(a1), unchanged_when_close_window_destroyed=True)


def arm_mask(s, threshold=H1_THRESHOLD):
    return (s["H1"] <= -threshold).to_numpy(bool)


def quantile_arm_mask(s, q=ARM_QUANTILE):
    """The arm without the sigma convention: the worst q of the window's own 14:00->15:00 moves. Declared
    as a BESIDE so the threshold is not the only definition the census can be read under."""
    h = s["H1_bp"].to_numpy(float)
    ok = np.isfinite(h)
    if ok.sum() < 20:
        return np.zeros(len(s), bool)
    cut = float(np.quantile(h[ok], q))
    return ok & (h <= cut)


# ================================================================ comparison machinery
def two_sample(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    if a.size < 5 or b.size < 5:
        return dict(margin=None, se=None, t=None, verdict="unresolved",
                    note=f"too few observations ({a.size} against {b.size})"), a, b
    se = float(np.sqrt(np.var(a, ddof=1) / a.size + np.var(b, ddof=1) / b.size))
    return resolve(float(np.mean(a) - np.mean(b)), se), a, b


def equivalence_bound(arm_vals, nonarm_vals, frac=MATERIAL_SD_FRAC):
    """What the data EXCLUDES, which is the only honest way to report a symmetry claim.

    D373's rule labels a small margin UNRESOLVED, and that is correct for a directional prediction -- but
    Q1's declared FAILURE is that the imbalance is symmetric, and "unresolved" cannot distinguish "no
    effect" from "no power". The upper 2-SE bound answers the question the prediction actually poses: is a
    one-sided flow of the size a forced-seller story needs still consistent with what was measured?
    """
    a = np.asarray(arm_vals, float)
    b = np.asarray(nonarm_vals, float)
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    if a.size < 5 or b.size < 5:
        return dict(note=f"too few observations ({a.size} against {b.size})")
    se = float(np.std(a, ddof=1) / np.sqrt(a.size))
    sd = float(np.std(b, ddof=1))
    mat = frac * sd
    up = float(np.mean(a) + MARGIN_SE * se)
    return dict(n=int(a.size), mean=float(np.mean(a)), se=se, upper_2se=up, sd_nonarm=sd,
                material_threshold=mat, material_sd_frac=frac,
                excludes_material=bool(up < mat),
                reading=(f"the data EXCLUDE a one-sided imbalance of {mat:+.5f} or more"
                         if up < mat else "the data cannot exclude a material one-sided imbalance"))


def one_sample(v):
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    if v.size < 5:
        return dict(margin=None, se=None, t=None, verdict="unresolved", note=f"only {v.size} observations")
    return resolve(float(np.mean(v)), float(np.std(v, ddof=1) / np.sqrt(v.size)))


def paired(a, b):
    """Within-session pairing, which the pre-registration's section 5 says to label as the stronger lens."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    ok = np.isfinite(a) & np.isfinite(b)
    return one_sample(a[ok] - b[ok]), int(ok.sum())


def rotation_null(arm, series, kmin=NULL_MIN_OFFSETS // 5):
    """Enumerated rotation of the ARM LABEL against the flow series. The label moves as a block, so its
    count and its clustering survive and only its pairing with the flow is destroyed.

    RAISES on a null with no spread or too few offsets -- a null whose draws are all equal reports a rank
    and discriminates nothing.
    """
    arm = np.asarray(arm, bool)
    series = np.asarray(series, float)
    n = series.size
    vals = []
    for k in range(kmin, n - kmin + 1):
        m = np.roll(arm, k) & np.isfinite(series)
        if m.sum() >= NULL_MIN_ARM:
            vals.append(float(np.mean(series[m])))
    out = np.array(vals, float)
    if out.size < NULL_MIN_OFFSETS:
        raise AssertionError(f"rotation null has only {out.size} usable offsets")
    if float(np.nanstd(out)) == 0.0:
        raise AssertionError("rotation null has ZERO spread, so it cannot place the observation anywhere")
    return out


def blk(obs, null):
    null = np.asarray(null, float)
    null = null[np.isfinite(null)]
    se95 = float(np.std(null, ddof=1) / np.sqrt(null.size))
    return dict(observed=float(obs), p05=float(np.percentile(null, 5)), p50=float(np.percentile(null, 50)),
                p95=float(np.percentile(null, 95)), n=int(null.size), p95_se=se95,
                pct_rank=float((null < obs).mean()),
                above_p95=bool(obs > np.percentile(null, 95)),
                within_2se_of_p95=bool(abs(obs - np.percentile(null, 95)) <= 2 * se95))


CALLS: list[str] = []


def report(label, quantity, res, sample=None, labels=None, note="", n2=None, say=log):
    """Every comparison goes through here, which is what makes the declared-output guard binding: the
    quantity name is recorded and checked against MEASURED at the end of the run."""
    CALLS.append(quantity)
    out = dict(label=label, quantity=quantity, **res)
    if sample is not None:
        out["tails"] = tails(sample, labels=labels)
    if note:
        out["note"] = note
    t = res.get("t")
    if n2 is not None:
        out["n_groups"] = [int(x) for x in n2]
    nshow = (out.get("tails") or {}).get("n") or (int(sum(n2)) if n2 else 0)
    say(f"  {label:<58} n {nshow:4d}  "
        f"margin {('%+9.5f' % res['margin']) if res.get('margin') is not None else '     n/a'}  "
        f"t {('%+6.2f' % t) if t is not None else '   n/a'}  {res['verdict'].upper()}")
    td = out.get("tails") or {}
    if td.get("n", 0) >= 10:
        say(f"      median {td['median']:+9.5f}  trim {td['symmetric_trim']:+9.5f}  "
            f"ex-top {td['ex_top']:+9.5f}  ex-bottom {td['ex_bottom']:+9.5f}  "
            f"share>0 {td['share_positive']:.3f}"
            + ("   MEAN BELOW MEDIAN" if td["mean_below_median"] else "")
            + ("   SIGN FLIPS ON MEDIAN" if td["sign_flips_on_median"] else ""))
    return out


# ================================================================ the census
def run():
    t0 = time.time()
    res = dict(spec=SPEC, audits={}, multiplicity={})
    log("=" * 118)
    log("D623 CENSUS -- the signed closing flow. No return is scored; prices classify sessions only.")
    log("=" * 118)

    d = load_flow()
    res["window"] = audit_window(d)
    res["audits"]["window"] = res["window"]
    res["audits"]["imbalance_sign"] = audit_imbalance_sign()
    log(f"flow: {res['window']['rows']:,} buckets, {res['window']['sessions']} sessions "
        f"{res['window']['first']} .. {res['window']['last']}; the reserve from {RESERVE_FROM} is unread")

    t = per_session(d)
    res["coverage"] = audit_close_bucket_coverage(t)
    res["audits"]["close_bucket_coverage"] = res["coverage"]
    t = t[t["n_close"] == N_CLOSE_BUCKETS].copy()
    log(f"per-(root, session) rows with all {N_CLOSE_BUCKETS} closing buckets: {len(t)} "
        f"of {res['coverage']['pairs']} ({res['coverage']['share_full']:.3f})")

    s = load_classifiers()
    res["audits"]["sigma_is_lagged"] = audit_sigma_is_lagged(s)
    res["audits"]["arm_not_endogenous"] = audit_arm_not_endogenous(s)
    s["arm"] = arm_mask(s)
    s["arm_q"] = quantile_arm_mask(s)
    s["burst_hi"] = (s["burst"] >= BURST_HI)

    # ---- the arm count, BEFORE any comparison (section 3's own instruction)
    usable = s[np.isfinite(s["H1"])]
    arm_sessions = sorted(usable.loc[usable["arm"], "session"])
    res["arm"] = dict(sessions_with_sigma=int(len(usable)), threshold=-H1_THRESHOLD,
                      sigma_window=SIG_N, sigma_min_periods=SIG_MIN,
                      n_arm=len(arm_sessions), arm_sessions=arm_sessions,
                      n_arm_quantile=int(s["arm_q"].sum()), arm_quantile=ARM_QUANTILE,
                      overlap_threshold_and_quantile=int((s["arm"] & s["arm_q"]).sum()),
                      n_burst=int(s["burst_hi"].sum()),
                      n_arm_and_burst=int((s["arm"] & s["burst_hi"]).sum()), min_required=MIN_ARM)
    log("-" * 118)
    log(f"ARM COUNT FIRST: {len(arm_sessions)} arm sessions of {len(usable)} with a usable sigma "
        f"(H1 <= {-H1_THRESHOLD:.1f}); quantile arm {res['arm']['n_arm_quantile']} at q {ARM_QUANTILE}, "
        f"overlap {res['arm']['overlap_threshold_and_quantile']}")
    log(f"  midday burst >= {BURST_HI}: {res['arm']['n_burst']} sessions; arm AND burst "
        f"{res['arm']['n_arm_and_burst']}")
    if len(arm_sessions) < MIN_ARM:
        res["verdict"] = (f"STOPPED: {len(arm_sessions)} arm sessions is below the declared floor of "
                         f"{MIN_ARM}. The census reports the count and does not strain.")
        log(res["verdict"])
        res.update(Q1={}, Q2={}, Q3={}, Q4={}, Q5={}, verdicts={}, timing_s=round(time.time() - t0, 1))
        return res

    # Only CLASSIFIED sessions enter a comparison. A session in the sigma warm-up has no H1, so it is
    # unclassified rather than non-arm, and leaving it in the control would make the control group partly a
    # calendar filter -- the first weeks of the window -- instead of "sessions that were measured and did
    # not qualify".
    cls = s[np.isfinite(s["H1"])][["session", "H1", "arm", "arm_q", "burst", "burst_hi"]]
    j = t.merge(cls, on="session", how="inner")
    res["arm"]["sessions_in_comparisons"] = int(j["session"].nunique())
    res["arm"]["sessions_dropped_unclassified"] = int(t["session"].nunique() - j["session"].nunique())
    log(f"joined rows {len(j)} over {j['session'].nunique()} CLASSIFIED sessions and "
        f"{j['root'].nunique()} roots; {res['arm']['sessions_dropped_unclassified']} sessions dropped for "
        "having no trailing sigma (the warm-up), so the control is not partly a calendar filter")

    # ------------------------------------------------------------ Q1
    log("-" * 118)
    log("Q1  IS THE CLOSING FLOW ONE-SIDED?  positive = net SELL-initiated, which is the declared direction")
    log("-" * 118)
    q1 = {}
    for root in ROOTS:
        r = j[j["root"] == root]
        a = r[r["arm"]]
        b = r[~r["arm"]]
        q1[f"{root}_arm_level"] = report(f"{root}: arm sessions, closing imbalance vs zero", "imb_close",
                                        one_sample(a["imb_close"]), a["imb_close"], a["session"])
        cmp_, av, bv = two_sample(a["imb_close"], b["imb_close"])
        q1[f"{root}_arm_minus_nonarm"] = report(f"{root}: arm minus non-arm", "imb_close", cmp_,
                                               note="between-session lens", n2=(av.size, bv.size))
        eb = equivalence_bound(a["imb_close"], b["imb_close"])
        q1[f"{root}_equivalence_bound"] = eb
        if "upper_2se" in eb:
            log(f"      EQUIVALENCE: mean {eb['mean']:+.5f}, upper 2-SE bound {eb['upper_2se']:+.5f} "
                f"against a material {eb['material_threshold']:+.5f} "
                f"({MATERIAL_SD_FRAC} sd of the non-arm distribution) -> "
                + ("EXCLUDES a material one-sided imbalance" if eb["excludes_material"]
                   else "cannot exclude one"))
        q1[f"{root}_nonarm_level"] = report(f"{root}: non-arm sessions, for the level", "imb_close",
                                           one_sample(b["imb_close"]), b["imb_close"], b["session"])
        pr, npair = paired(a["imb_close"], a["imb_mid"])
        q1[f"{root}_arm_close_minus_own_midday"] = report(
            f"{root}: arm, closing minus its OWN midday", "imb_close_minus_mid", pr,
            (a["imb_close"] - a["imb_mid"]), a["session"],
            note=f"within-session lens (the stronger one), {npair} pairs")
    # the quantile arm, as the declared robustness beside
    r = j[j["root"] == "ES"]
    q1["ES_quantile_arm_level"] = report("ES: QUANTILE arm, closing imbalance vs zero", "imb_close",
                                        one_sample(r.loc[r["arm_q"], "imb_close"]),
                                        r.loc[r["arm_q"], "imb_close"], r.loc[r["arm_q"], "session"],
                                        note="the arm without the sigma convention")
    # the rotation null on ES, enumerated
    e = r.sort_values("session")
    try:
        null = rotation_null(e["arm"].to_numpy(bool), e["imb_close"].to_numpy(float))
        obs = float(e.loc[e["arm"], "imb_close"].mean())
        q1["ES_rotation_null"] = blk(obs, null)
        n_ = q1["ES_rotation_null"]
        log(f"  ES rotation null (enumerated, {n_['n']} offsets): observed {n_['observed']:+.5f}  "
            f"p50 {n_['p50']:+.5f}  p95 {n_['p95']:+.5f} (SE {n_['p95_se']:.5f})  "
            f"rank {n_['pct_rank']:.3f}"
            + ("  WITHIN 2 SE OF p95 -> UNRESOLVED" if n_["within_2se_of_p95"] else ""))
    except AssertionError as ex:
        q1["ES_rotation_null"] = dict(error=str(ex))
        log(f"  ES rotation null unavailable: {ex}")
    res["Q1"] = q1

    # ------------------------------------------------------------ Q2
    log("-" * 118)
    log("Q2  DOES IT ACCELERATE INTO THE DEADLINE?  slope on bucket index, and last two minus first two")
    log("-" * 118)
    q2 = {}
    for root in ROOTS:
        r = j[j["root"] == root]
        a, b = r[r["arm"]], r[~r["arm"]]
        q2[f"{root}_arm_slope"] = report(f"{root}: arm, slope of imbalance on bucket index", "imb_slope",
                                        one_sample(a["imb_slope"]), a["imb_slope"], a["session"])
        q2[f"{root}_arm_last2_first2"] = report(f"{root}: arm, last two minus first two buckets",
                                               "imb_last2_first2", one_sample(a["imb_last2_first2"]),
                                               a["imb_last2_first2"], a["session"])
        cmp_, _, _ = two_sample(a["imb_slope"], b["imb_slope"])
        q2[f"{root}_slope_arm_minus_nonarm"] = report(f"{root}: slope, arm minus non-arm", "imb_slope",
                                                     cmp_, note="between-session lens")
    res["Q2"] = q2

    # ------------------------------------------------------------ Q3
    log("-" * 118)
    log("Q3  IS IT SMALL LOTS?  the <=2-lot share of volume. NOTE: the fixture's lot1/lot_le2 are volume")
    log("    in small trades and are NOT split by aggressor side, so this is the share of TOTAL volume --")
    log("    a weaker object than the pre-registration's 'share of sell-initiated volume'.")
    log("-" * 118)
    q3 = {"specification_change": (
        "The pre-registration asks for the small-lot share OF SELL-INITIATED volume. "
        "`fut_micro_flow_5m.csv.gz` carries lot1 and lot_le2 as volume in <=1-lot and <=2-lot trades "
        "WITHOUT a side split (build_fut_micro_flow.py:105 sums size where size<=2 over all trades), so "
        "that quantity does not exist in the fixture and cannot be recovered from it. The census measures "
        "the small-lot share of TOTAL volume instead and says so: on a window where Q1 establishes net "
        "selling, a rise is suggestive of small-lot selling but does not identify it.")}
    log("  " + q3["specification_change"][:112] + " ...")
    log("  THE CONTROL THE FIRST PASS LACKED: the same arm-minus-non-arm comparison on the MIDDAY window.")
    log("  If the small-lot share is also higher on arm sessions at MIDDAY, the closing-hour margin is a")
    log("  session-level characteristic and says nothing about a deadline.")
    for root in ROOTS:
        r = j[j["root"] == root]
        a, b = r[r["arm"]], r[~r["arm"]]
        cmp_, av, bv = two_sample(a["small_share_mid"], b["small_share_mid"])
        q3[f"{root}_mid_arm_minus_nonarm"] = report(
            f"{root}: MIDDAY <=2-lot share, arm minus non-arm (THE CONTROL)", "small_share_mid", cmp_,
            note="if this matches the closing margin, the closing margin is not about the close",
            n2=(av.size, bv.size))
        for tag in ("close", "trig"):
            cmp_, av, bv = two_sample(a[f"small_share_{tag}"], b[f"small_share_{tag}"])
            q3[f"{root}_{tag}_arm_minus_nonarm"] = report(
                f"{root}: {tag} <=2-lot share, arm minus non-arm", f"small_share_{tag}", cmp_,
                note="between-session lens; read against the MIDDAY control above",
                n2=(av.size, bv.size))
            pr, npair = paired(a[f"small_share_{tag}"], a["small_share_mid"])
            q3[f"{root}_{tag}_minus_own_midday"] = report(
                f"{root}: {tag} <=2-lot share minus its OWN midday", f"small_share_{tag}_minus_mid", pr,
                (a[f"small_share_{tag}"] - a["small_share_mid"]), a["session"],
                note=f"within-session lens, {npair} pairs")
        # the difference-in-differences, which is what the control implies and what Q3 actually claims:
        # does the closing hour's small-lot share rise MORE on arm sessions than it does on other sessions?
        cmp_, av, bv = two_sample(a["small_share_close_minus_mid"], b["small_share_close_minus_mid"])
        q3[f"{root}_did_close_vs_mid_arm_minus_nonarm"] = report(
            f"{root}: DiD -- (close minus midday), arm minus non-arm", "small_share_close_minus_mid",
            cmp_, note="Q3's primary once the midday control exists", n2=(av.size, bv.size))
        # numerator or denominator? the logged volume ratios, which a share cannot distinguish
        for qty, lbl in (("small_vol_ratio_log", "small-lot contracts PER BUCKET, close/midday (log)"),
                         ("vol_ratio_log", "ALL contracts PER BUCKET, close/midday (log)"),
                         ("excess_small_growth_log", "EXCESS small-lot growth over the book (log)")):
            cmp_, av, bv = two_sample(a[qty], b[qty])
            q3[f"{root}_{qty}_arm_minus_nonarm"] = report(
                f"{root}: {lbl}, arm minus non-arm", qty, cmp_,
                note="separates a bigger numerator from a smaller denominator", n2=(av.size, bv.size))
            q3[f"{root}_{qty}_arm_level"] = report(
                f"{root}: {lbl}, arm level", qty, one_sample(a[qty]), a[qty], a["session"])
        cmp_, av, bv = two_sample(a["lot1_share_close"], b["lot1_share_close"])
        q3[f"{root}_lot1_close_arm_minus_nonarm"] = report(
            f"{root}: close 1-lot share, arm minus non-arm", "lot1_share_close", cmp_,
            note="the tighter lot proxy; same midday caveat", n2=(av.size, bv.size))
        # the unsigned share is a COVERAGE figure, not a comparison: on this fixture the aggressor side
        # covers the whole closing hour, so a two-sample test on it has no standard error and reporting one
        # would be a comparison with no way to disagree
        q3[f"{root}_coverage"] = dict(
            uns_share_close_mean=float(np.nanmean(r["uns_share_close"])),
            uns_share_close_max=float(np.nanmax(r["uns_share_close"])),
            agree_close_mean=float(np.nanmean(r["agree_close"])),
            note="aggressor-side coverage of the closing hour on the census window (D485's T1, restated)")
        log(f"  {root}: closing-hour UNSIGNED share mean "
            f"{q3[f'{root}_coverage']['uns_share_close_mean']:.6f} "
            f"(max {q3[f'{root}_coverage']['uns_share_close_max']:.6f}); aggressor agreement "
            f"{q3[f'{root}_coverage']['agree_close_mean']:.5f}")
    res["Q3"] = q3

    # ------------------------------------------------------------ Q4
    log("-" * 118)
    log("Q4  MES AGAINST ES (and MNQ against NQ), PAIRED WITHIN SESSION")
    log("-" * 118)
    q4 = {"lot_legs_are_void": (
        "A LOT IS A DIFFERENT NOTIONAL IN EACH CONTRACT, so the <=2-lot share is not comparable between a "
        "micro and its mini, and Q4's lot legs cannot test what they were written to test. The two pairs "
        "come out with OPPOSITE signs -- MES-ES positive, MNQ-NQ large and negative -- which is the "
        "statistic measuring contract size rather than trader type. That is D485's own finding (the micro "
        "crowd's trades are no smaller) reappearing as an artefact. The legs are reported for the record "
        "and carry no weight; only Q4's IMBALANCE leg is interpretable.")}
    log("  " + q4["lot_legs_are_void"][:112] + " ...")
    for micro, mini in PAIRS:
        w = j[j["root"] == micro].merge(j[j["root"] == mini], on="session", suffixes=("_m", "_e"))
        am = w[w["arm_m"]]
        for qty in ("imb_close", "small_share_close", "lot1_share_close"):
            pr, npair = paired(am[f"{qty}_m"], am[f"{qty}_e"])
            q4[f"{micro}_minus_{mini}_arm_{qty}"] = report(
                f"{micro} minus {mini} on arm sessions: {qty}"
                + ("" if qty == "imb_close" else "  [VOID: lot notional]"),
                qty if qty in MEASURED else "imb_close",
                pr, (am[f"{qty}_m"] - am[f"{qty}_e"]), am["session"],
                note=(f"within-session pairing, {npair} sessions"
                      + ("" if qty == "imb_close" else "; VOID, see lot_legs_are_void")))
        nm = w[~w["arm_m"]]
        pr, npair = paired(nm["imb_close_m"], nm["imb_close_e"])
        q4[f"{micro}_minus_{mini}_nonarm_imb_close"] = report(
            f"{micro} minus {mini} on NON-arm sessions: imb_close", "imb_close", pr, n2=(npair, 0),
            note=f"the baseline gap, {npair} sessions -- Q4 needs the ARM gap to exceed it")
        d_arm = (am["imb_close_m"] - am["imb_close_e"]).to_numpy(float)
        d_non = (nm["imb_close_m"] - nm["imb_close_e"]).to_numpy(float)
        cmp_, _, _ = two_sample(d_arm, d_non)
        q4[f"{micro}_minus_{mini}_gap_arm_minus_nonarm"] = report(
            f"{micro}-{mini} gap: arm minus non-arm", "imb_close", cmp_,
            note="the difference in differences, which is what Q4 actually claims")
    res["Q4"] = q4

    # ------------------------------------------------------------ Q5
    log("-" * 118)
    log(f"Q5  THE DETECTION REGIME: does a midday volume burst (>= {BURST_HI}x its trailing "
        f"{BURST_BASE_N}-session median) predict a larger closing imbalance on arm sessions?")
    log("-" * 118)
    q5 = {}
    n_ab = res["arm"]["n_arm_and_burst"]
    if n_ab < MIN_ARM:
        q5["not_tested"] = (
            f"Q5 IS NOT TESTED. Only {n_ab} sessions are both arm and burst, against this census's own "
            f"declared floor of {MIN_ARM} (pre-registration section 3). The comparisons below are printed "
            "for the record and must not be read as evidence either way: a question asked on fewer "
            "observations than the design declared usable has not been asked.")
        log("  " + q5["not_tested"][:114] + " ...")
    for root in ROOTS:
        r = j[j["root"] == root]
        a = r[r["arm"]]
        hi, lo = a[a["burst_hi"]], a[~a["burst_hi"]]
        q5[f"{root}_arm_burst_level"] = report(f"{root}: arm AND burst, closing imbalance", "imb_close",
                                              one_sample(hi["imb_close"]), hi["imb_close"], hi["session"])
        cmp_, av, bv = two_sample(hi["imb_close"], lo["imb_close"])
        q5[f"{root}_arm_burst_minus_noburst"] = report(f"{root}: arm, burst minus no-burst", "imb_close",
                                                      cmp_, note=f"n {av.size} against {bv.size}")
        cmp_, _, _ = two_sample(r.loc[r["burst_hi"], "imb_close"], r.loc[~r["burst_hi"], "imb_close"])
        q5[f"{root}_all_burst_minus_noburst"] = report(f"{root}: ALL sessions, burst minus no-burst",
                                                      "imb_close", cmp_,
                                                      note="the burst's unconditional effect on flow")
    res["Q5"] = q5

    # ------------------------------------------------------------ bookkeeping
    res["audits"]["declared_outputs"] = audit_measured_quantities_are_flow(CALLS)
    res["multiplicity"] = dict(
        comparisons=len(CALLS), roots=len(ROOTS),
        note=("Every comparison in this file is disclosed (R13/R14). Five questions across four roots with "
              "a between-session and a within-session lens is a large look count, and the census is "
              "therefore read on the SHAPE of the answers -- do they agree across roots and lenses -- "
              "rather than on any single margin clearing 2 SE."))

    def verdict_of(block, keys):
        vs = [block[k]["verdict"] for k in keys if k in block and "verdict" in block[k]]
        if not vs:
            return "unresolved"
        if all(v == "pass" for v in vs):
            return "pass"
        if any(v == "fail" for v in vs) and not any(v == "pass" for v in vs):
            return "fail"
        return "mixed" if ("pass" in vs and "fail" in vs) else ("pass" if "pass" in vs else "unresolved")

    n_excl = sum(1 for r in ROOTS if res["Q1"].get(f"{r}_equivalence_bound", {}).get("excludes_material"))
    res["verdicts"] = dict(
        Q1=verdict_of(res["Q1"], [f"{r}_arm_level" for r in ROOTS]),
        Q1_vs_nonarm=verdict_of(res["Q1"], [f"{r}_arm_minus_nonarm" for r in ROOTS]),
        Q1_equivalence=f"{n_excl} of {len(ROOTS)} roots EXCLUDE a material one-sided closing imbalance",
        Q2=verdict_of(res["Q2"], [f"{r}_arm_slope" for r in ROOTS]
                      + [f"{r}_arm_last2_first2" for r in ROOTS]),
        # Q3 is a CONJUNCTION in the pre-registration -- the share must rise against non-arm sessions AND
        # against the session's own midday baseline -- so the verdict is the difference-in-differences,
        # not the raw level margin, which the midday control shows is a session-level characteristic.
        Q3=verdict_of(res["Q3"], [f"{r}_did_close_vs_mid_arm_minus_nonarm" for r in ROOTS]),
        Q3_level_leg_only=verdict_of(res["Q3"], [f"{r}_close_arm_minus_nonarm" for r in ROOTS]),
        Q3_own_midday_leg=verdict_of(res["Q3"], [f"{r}_close_minus_own_midday" for r in ROOTS]),
        Q4=verdict_of(res["Q4"], [f"{m}_minus_{e}_gap_arm_minus_nonarm" for m, e in PAIRS]),
        Q5=("not tested" if "not_tested" in res["Q5"]
            else verdict_of(res["Q5"], [f"{r}_arm_burst_minus_noburst" for r in ROOTS])))
    res["verdict"] = ("; ".join(f"{k} {v.upper()}" for k, v in res["verdicts"].items()))
    res["timing_s"] = round(time.time() - t0, 1)
    log("=" * 118)
    log("VERDICTS: " + res["verdict"])
    log(f"comparisons made and disclosed: {len(CALLS)}; wall {res['timing_s']}s")
    log("=" * 118)
    missing = [k for k in REQUIRED_OUTPUTS if k not in res]
    if missing:
        raise AssertionError(f"DECLARED OUTPUTS missing from the artifact: {missing}")
    return res


# ================================================================ selftest
def selftest():
    log("=" * 118)
    log("D623 SELFTEST -- every audit passes on real data AND raises on a break that hits the scalar it reads")
    log("=" * 118)

    log("[1] the imbalance sign, in the census's own units")
    a = audit_imbalance_sign()
    log(f"    passes: sell-heavy {a['sell_heavy']:+.4f}, buy-heavy {a['buy_heavy']:+.4f}, empty is NaN")
    expect_raise(lambda: audit_imbalance_sign(lambda s, b: -imbalance(s, b)), "a NEGATED imbalance")
    expect_raise(lambda: audit_imbalance_sign(lambda s, b: imbalance(b, s)), "buy and sell swapped")
    expect_raise(lambda: audit_imbalance_sign(lambda s, b: np.nan_to_num(imbalance(s, b))),
                 "an empty bucket returning 0.0 instead of NaN")

    log("[2] the clock: `minute` against a second path from bucket_start")
    d = load_flow()
    log(f"    passes: {len(d):,} rows, minute == bucket_start's own ET clock on every one")
    bad = d.copy()
    bad["minute"] = bad["minute"] + 60
    tmp = Path(sys.argv[0]).parent.parent / "temp"
    tmp.mkdir(exist_ok=True)
    p = tmp / "_d623_clock_break.csv"
    bad.to_csv(p, index=False, encoding="utf-8")
    expect_raise(lambda: load_flow(p), "a `minute` column shifted one hour")
    p.unlink()

    log("[3] the window, asserted from both sides")
    w = audit_window(d)
    log(f"    passes: {w['first']} .. {w['last']}, {w['sessions']} sessions, reserve from {w['reserve_from']}")
    expect_raise(lambda: audit_window(d.iloc[:0]), "an empty read")
    leak = d.iloc[:5].copy()
    leak["session"] = "2026-08-03"
    expect_raise(lambda: audit_window(pd.concat([d, leak])), "a session inside D485's reserve")
    expect_raise(lambda: audit_window(d, census_to="2026-01-31"),
                 "a read that runs past its own declared end")

    log("[4] the declared-output guard")
    g = audit_measured_quantities_are_flow(["imb_close", "small_share_trig"])
    log(f"    passes: {len(g['permitted'])} permitted flow quantities, {len(g['classifiers'])} classifiers")
    expect_raise(lambda: audit_measured_quantities_are_flow(["imb_close", "y_bp"]),
                 "a quantity that is not in MEASURED")
    expect_raise(lambda: audit_measured_quantities_are_flow(["imb_close", "H1_bp"]),
                 "a PRICE CLASSIFIER used as a measured quantity")

    log("[5] the closing-hour bucket coverage and its drop rule")
    t = per_session(d)
    c = audit_close_bucket_coverage(t)
    log(f"    passes: {c['full']} of {c['pairs']} pairs carry {c['need']} buckets "
        f"({c['share_full']:.3f}); {c['dropped']} dropped")
    expect_raise(lambda: audit_close_bucket_coverage(t, need=6), "a bucket count above the declared need")
    thin = t.copy()
    thin["n_close"] = 3
    expect_raise(lambda: audit_close_bucket_coverage(thin), "a panel where most closing hours are short")

    log("[6] sigma is lagged, by a second path that never calls rolling()")
    s = load_classifiers()
    sg = audit_sigma_is_lagged(s)
    log(f"    passes: {sg['n_with_sigma']} sessions with a sigma, max deviation "
        f"{sg['max_abs_deviation']:.3e}")
    unlagged = s.copy()
    unlagged["sigma_bp"] = s["H1_bp"].rolling(SIG_N, min_periods=SIG_MIN).std()   # no .shift(1)
    expect_raise(lambda: audit_sigma_is_lagged(unlagged), "a sigma that is NOT shifted one session")

    log("[7] the arm is not endogenous")
    e = audit_arm_not_endogenous(s)
    log(f"    passes: {e['arm_sessions']} arm sessions, unchanged when every 15:00+ price is destroyed")

    def endogenous():
        b = pd.read_csv(ES_1M, dtype={"day": str, "hhmm": str, "contract": str}, encoding="utf-8")
        b = b[(b["day"] >= CENSUS_FROM) & (b["day"] <= CENSUS_TO)]
        close = b.pivot(index="day", columns="hhmm", values="close")
        nb = b.groupby("day").size()
        close = close[nb.reindex(close.index) >= MIN_BARS]
        s2 = pd.DataFrame(index=close.index)
        s2["H1_bp"] = 1e4 * np.log(close["15:59"] / close["13:59"])      # reads the CLOSE window
        s2["sigma_bp"] = s2["H1_bp"].rolling(SIG_N, min_periods=SIG_MIN).std().shift(1)
        s2["H1"] = s2["H1_bp"] / s2["sigma_bp"]
        s2.index.name = "session"
        s2 = s2.reset_index()
        a1 = set(s.loc[arm_mask(s), "session"])
        a2 = set(s2.loc[arm_mask(s2), "session"])
        if a1 != a2:
            raise AssertionError(f"ARM IS ENDOGENOUS: {len(a1 ^ a2)} sessions change")
    expect_raise(endogenous, "an arm defined on a window that REACHES 16:00")

    log("[8] the rotation null raises rather than reporting an empty rank")
    arm = np.zeros(200, bool)
    arm[:40] = True
    rng = np.random.default_rng(623)
    nl = rotation_null(arm, rng.normal(size=200))
    log(f"    passes: {nl.size} enumerated offsets, spread {np.std(nl):.5f}")
    expect_raise(lambda: rotation_null(arm, np.ones(200)), "a constant flow series (zero spread)")
    expect_raise(lambda: rotation_null(arm[:30], rng.normal(size=30)), "a series too short to enumerate")

    log("[9] resolve() and tails() label rather than rubber-stamp (reused from the D622 runner)")
    for m_, se_, want in ((10.0, 1.0, "pass"), (-10.0, 1.0, "fail"), (1.0, 1.0, "unresolved"),
                          (1.9, 1.0, "unresolved"), (1.0, 0.0, "unresolved")):
        got = resolve(m_, se_)["verdict"]
        if got != want:
            raise AssertionError(f"resolve({m_}, {se_}) -> {got}, expected {want}")
    log("    passes: pass at 10 SE, fail at -10 SE, unresolved at 1.0 and 1.9 SE and on a zero SE")
    v = np.concatenate([np.full(90, 1.0), np.full(10, -30.0)])
    td = tails(v)
    if not (td["mean_below_median"] and td["sign_flips_on_median"]):
        raise AssertionError("tails() did not detect a mean below its median with a sign flip")
    log(f"    passes: a series with mean {td['mean']:+.2f} and median {td['median']:+.2f} is flagged")

    log("=" * 118)
    log("SELFTEST GREEN -- 9 audits, each proven to raise on a break that hits the scalar it reads")
    log("=" * 118)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
    if a.run:
        r = run()
        OUT.write_text(json.dumps(r, indent=1, default=str), encoding="utf-8")
        log(f"wrote {OUT.relative_to(REPO)}")
    if not (a.selftest or a.run):
        ap.print_help()


if __name__ == "__main__":
    main()
