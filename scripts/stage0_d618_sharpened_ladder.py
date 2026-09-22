"""D618 -- the sharpened 0DTE ladder: can a signed distance from the price to a WEIGHTED STRIKE have both
RANGE and INDEPENDENCE from the day's own move? Pre-registered in
`docs/decisions/D618-PRE-REG-the-sharpened-0DTE-ladder-range-or-independence.md`, committed (and amended
with its control set) before this file existed.

    python scripts/stage0_d618_sharpened_ladder.py --selftest   # every audit passes AND raises on its break
    python scripts/stage0_d618_sharpened_ladder.py --run        # the screens, then the scored cells

WHAT IS DIFFERENT FROM D614
---------------------------
D614 scored ONE conditioner and reported its coefficient. This runner scores the FAMILY's construction
first: every cell meets four pre-outcome screens before any return is read, and a cell that fails one is
reported with its numbers and not scored. The screens are the study's main output, because they are the
part a spent window cannot corrupt -- they are statements about the conditioner alone.

The prediction the record commits to is that no cell has both range and independence: nothing with
sd >= 1.0 sigma and |corr with the 09:30-15:30 move| <= 0.40. If that holds, the axis closes.

REUSE, NEVER REIMPLEMENTED
--------------------------
`stage0_d581_gamma_close.py` for Black-76 (`b76_gamma`, the scalar `b76_gamma_hand`, `implied_vol`) and
`stage0_d614_expiry_pin.py` for the estimator ladder, the tail diagnostics, the norm-preserving
Frisch-Waugh shift null, the sign-flip null, the block standard errors, `coef_named` (BY NAME -- D614's W1
was a positional read that returned the interaction instead of the level) and `audit_not_singular`.
"""
from __future__ import annotations

import argparse
import hashlib
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
OPTS = FIX / "fut_es_options_eod.csv.gz"
CUTS = FIX / "fut_es_0dte_volume_cutoffs.csv.gz"
ES_1M = FIX / "fut_ES_rth_1m.csv.gz"
STRIP = FIX / "fut_settle_strip.csv.gz"
SESSIONS = FIX / "fut_index_sessions.csv.gz"
SPECS = REPO / "data" / "futures_contract_specs.json"
OUT = REPO / "data" / "stage0_d618_sharpened_ladder.json"
TEMP = REPO / "temp" / "d618"

SPEC = "D618"
IN_FROM, IN_TO, RESERVED_FROM = "2016-01-04", "2023-12-29", "2024-01-01"
MIN_BARS = 380
T_OPEN, T_NOON, T_MIDE, T_ENTRY, T_LEG, T_CLOSE = "09:30", "12:00", "14:30", "15:30", "15:50", "16:00"
SIG_N, SIG_MIN = 252, 60
HOURS, YEAR_HOURS, MULT, MONEYNESS_MAX = 6.5, 252 * 6.5, 50.0, 0.30      # D581's, verbatim

# ---- the screens, thresholds from the record ----
S1A_FLOOR = 0.20        # measurement floor, sd of LADDER in sigma units of the scored window
# S1b, CORRECTED 2026-09-22 after the principal asked whether the screens were too harsh.
#
# The first version required sd(LADDER) >= 3 x sd of the same cell with FLAT weights over its positive-weight
# strikes. That comparator is wrong, and a known-answer case proved it: a conditioner built from the ACTUAL
# 16:00 close -- perfect information -- scored 0.05 and was REJECTED, as were all 72 real cells. The reason is
# that for any smooth weight the positive-weight set is the whole 220-strike ladder, whose centroid sits ~23
# sigma from the price, so the ratio asks "is this as dispersed as the entire ladder" and therefore PENALISES
# the concentration a real signal has. A within-session permutation comparator fails the same way (oracle
# 0.04, grid 1.00): a reshuffle scatters weight over the ladder, so every informative object is NARROWER than
# its own permutations and the inequality runs the wrong way.
#
# The question S1b was for -- is this distinguishable from the unweighted centroid of the same eligible
# strikes -- is answered directly and scale-freely by corr(LADDER, PING). The grid control IS PING, so it
# scores exactly 1.0 by construction; the oracle, a diluted oracle and a weak oracle score 0.061, 0.036 and
# 0.020. The ceiling is the midpoint of that calibrated gap and is set from the CONTROLS, never from the real
# cells. PING also stays a regression control, so partial overlap is handled again at scoring.
S1B_PING_CEIL = 0.50
S2_CEIL = 0.40          # |corr(LADDER, DAY0)|, D614 section 4's form
S3_CEIL = 0.25          # R^2 of LADDER on the grid offset (P1530 mod step)/step
S4_FLOOR = 5            # median strike count inside the band

# ---- the family ----
# The record's weight table names `vol_to_1530` as "D614's, the known comparator". Those are two different
# columns: D614's own conditioner was the NOON cutoff, which is why D613's panel exists at all, and
# `vol_to_1530` accumulates into the scored window. Both are carried, named apart, and the disagreement is
# reported -- see `corrections` in the artifact.
WEIGHTS = ("gamma_doi", "doi", "gamma", "gamma_oi", "vol_noon", "vol_1530")
GAMMA_WEIGHTS = ("gamma_doi", "gamma", "gamma_oi")
ANCHORS = ("now", "pre")                      # gamma evaluated at P1530, or at the prior settlement
BANDS = ((None, "all"), (3, "3step"), (2, "2step"), (1, "1step"))
WINDOWS = {"w30": (T_ENTRY, T_CLOSE), "w10": (T_LEG, T_CLOSE)}
PRIMARY_WINDOW = "w30"
# fixed in the record, ordered by MECHANISM and not by any in-sample t
PRIORITY = (("gamma_doi", "all", "w30", "now"), ("doi", "all", "w30", None),
            ("gamma_doi", "3step", "w30", "now"), ("doi", "3step", "w30", None),
            ("gamma_oi", "all", "w30", "now"), ("gamma", "all", "w30", "now"))

NW_LAG, SHIFT_MIN, BOOT, FLIP_DRAWS, SEED = 5, 10, 1000, 2000, 618
TAIL_TOP = 10
TAIL_BAR_FRACTION = 0.5       # excluding the ten largest |LADDER| sessions, keep the sign and half the size
ADDITIVITY_TOL_BP = 1e-9      # the record's 1e-12 is in LOG units; these columns are bp, so this is stricter
WEIGHTS_BITE_FLOOR_PTS = 2.0  # median |K_w - P1530| in points; below this the object sits on the price
RIGHT_QUANTITY_CEILING = 0.10 # share of sessions where R10 == R30 exactly (a flat first leg); 1.0 means one column
REQUIRED_OUTPUTS = ("spec", "windows", "sets", "corrections", "audits", "premise", "screens",
                    "predictions", "scored", "family_null", "delta_oi_gate", "component",
                    "priority_order", "chosen_cell", "endogenous_band_diagnostic", "artefact_scored",
                    "verdict_parts",
                    "verdict", "timing_s")


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


def log(*a):
    print(*a, flush=True)


def expect_raise(fn, what, say=log):
    try:
        fn()
    except AssertionError as e:
        say(f"    audit RAISES on {what}: {str(e)[:78]}")
        return True
    raise AssertionError(f"audit did not raise on {what}")


D581 = _load("d581", "stage0_d581_gamma_close.py")
D614 = _load("d614", "stage0_d614_expiry_pin.py")


# ------------------------------------------------------------------ prices
def es_calendar():
    s = pd.read_csv(SESSIONS, dtype={"day": str, "contract": str, "root": str}, encoding="utf-8")
    s = s[(s["root"] == "ES") & (s["bars"] >= 380)]
    return np.array(sorted(s["day"].unique()))


def load_es():
    """Both scored windows and every control, with the endpoint convention D462 fixed: the price AT hh:mm
    is the close of the bar STARTING one minute earlier."""
    b = pd.read_csv(ES_1M, dtype={"day": str, "hhmm": str, "contract": str}, encoding="utf-8")
    b = b[(b["day"] >= IN_FROM) & (b["day"] <= IN_TO)]
    if b["day"].max() >= RESERVED_FROM:
        raise AssertionError("a reserved session leaked into the ES read")
    nb = b.groupby("day").size()
    close = b.pivot(index="day", columns="hhmm", values="close")
    open_ = b.pivot(index="day", columns="hhmm", values="open")
    keep = nb.reindex(close.index) >= MIN_BARS
    close, open_ = close[keep], open_[keep]
    contract = b.groupby("day")["contract"].agg(lambda s: s.value_counts().index[0]).reindex(close.index)

    def P(hhmm):
        prev = (pd.Timestamp("2000-01-01 " + hhmm) - pd.Timedelta(minutes=1)).strftime("%H:%M")
        return close[prev]

    s = pd.DataFrame({"P0930": open_[T_OPEN], "P1200": P(T_NOON), "P1430": P(T_MIDE),
                      "P1530": P(T_ENTRY), "P1550": P(T_LEG), "P1600": P(T_CLOSE)}, index=close.index)
    s["contract"] = contract
    s["R30"] = 1e4 * np.log(s["P1600"] / s["P1530"])
    s["R10"] = 1e4 * np.log(s["P1600"] / s["P1550"])
    s["LEG1"] = 1e4 * np.log(s["P1550"] / s["P1530"])
    s["F5"] = 1e4 * np.log(s["P1530"] / s["P1430"])
    s["MIDE"] = 1e4 * np.log(s["P1430"] / s["P1200"])
    s["DAY0"] = 1e4 * np.log(s["P1200"] / s["P0930"])
    s["ON"] = 1e4 * np.log(s["P0930"] / s["P1600"].shift(1))
    s["roll"] = s["contract"] != s["contract"].shift(1)
    for tag, col in (("30", "R30"), ("10", "R10")):
        s[f"sigma{tag}_bp"] = s[col].rolling(SIG_N, min_periods=SIG_MIN).std().shift(1)
        s[f"sigma{tag}_pts"] = s[f"sigma{tag}_bp"] * s["P1530"] / 1e4
    s["year"] = s.index.str[:4]
    iso = pd.to_datetime(pd.Series(s.index)).dt.isocalendar()
    s["week"] = (iso["year"] * 100 + iso["week"]).to_numpy()
    n30 = len([c for c in close.columns if T_ENTRY <= c <= "15:59"])
    n10 = len([c for c in close.columns if T_LEG <= c <= "15:59"])
    return s, {"bars_in_w30": n30, "bars_in_w10": n10}


def audit_window_additivity(s):
    """R30 == LEG1 + R10: the two legs are the same path, so a window mistake shows up here.

    UNITS. The record states the bar as 1e-12, which is the natural scale in LOG units. These columns are
    basis points -- 1e4 x log -- so the equivalent bar is 1e-8, and the tolerance below is 1e-9 bp, a
    decade STRICTER than the record asks for. The measured deviation is reported so the margin is visible
    rather than implied.
    """
    a = s["R30"].to_numpy(float)
    b = s["LEG1"].to_numpy(float) + s["R10"].to_numpy(float)
    ok = np.isfinite(a) & np.isfinite(b)
    d = float(np.max(np.abs(a[ok] - b[ok])))
    if d > ADDITIVITY_TOL_BP:
        raise AssertionError(f"WINDOW ADDITIVITY: R30 - (LEG1 + R10) reaches {d:.3e}")
    # RIGHT QUANTITY: the two windows must not be the same number. They DO coincide when the first leg is
    # exactly flat -- the 15:30 and 15:50 prices are the same tick -- which is a real and countable event on
    # a quiet afternoon, not a bug. So the audit measures that share against a declared ceiling instead of
    # forbidding it; an accidental `R10 = R30` would take the share to 1.0 and fire.
    share_equal = float(np.mean(a[ok] == s["R10"].to_numpy(float)[ok]))
    if share_equal > RIGHT_QUANTITY_CEILING:
        raise AssertionError(f"RIGHT QUANTITY: the ten-minute return equals the half-hour on "
                             f"{share_equal:.4f} of sessions, over the declared ceiling "
                             f"{RIGHT_QUANTITY_CEILING}")
    return dict(max_abs_deviation=d, n=int(ok.sum()), share_r10_equals_r30=share_equal,
                sd_ratio_r10_over_r30=float(np.nanstd(s["R10"]) / np.nanstd(s["R30"])))


def audit_additivity_broken(s):
    """The break: an off-by-one-minute leg. The endpoint convention is the thing being asserted."""
    b = s.copy()
    b["LEG1"] = 1e4 * np.log(b["P1550"].shift(0) / b["P1530"]) + 1.0     # one bp of deliberate slip
    return audit_window_additivity(b)


# ------------------------------------------------------------------ the ladder
def cache_key():
    h = hashlib.sha256()
    for p in (OPTS, CUTS, Path(__file__)):
        h.update(f"{p.name}:{p.stat().st_mtime_ns}:{p.stat().st_size}".encode())
    return h.hexdigest()[:16]


def build_ladder(cal):
    """Per (session, strike) on the 0DTE PM ladder: oi, the one-session CHECKED delta, noon and 15:30
    volume, and |gamma| at both anchors.

    The delta is admitted only where the option's two rows are adjacent ES sessions AND their two
    `oi_ref_session` values are adjacent -- D616's column, without which a revision makes a delta of
    exactly zero that is not a zero position change. Everything else is counted and dropped.
    """
    d = pd.read_csv(OPTS, usecols=["session", "raw_symbol", "right", "strike", "expiry_date",
                                   "expiry_hhmm", "underlying", "oi", "settle", "oi_ref_session"],
                    dtype={"session": str, "raw_symbol": str, "right": str, "expiry_date": str,
                           "expiry_hhmm": str, "underlying": str, "oi_ref_session": str}, encoding="utf-8")
    d = d[(d["session"] >= IN_FROM) & (d["session"] <= IN_TO)]
    if d["session"].max() >= RESERVED_FROM:
        raise AssertionError("a reserved option row leaked")
    pos = {day: i for i, day in enumerate(cal)}
    d = d.sort_values(["raw_symbol", "session"], kind="stable").reset_index(drop=True)
    g = d.groupby("raw_symbol", sort=False)
    d["oi_prev"] = g["oi"].shift(1)
    prev_sess = g["session"].shift(1)
    prev_ref = g["oi_ref_session"].shift(1)
    si = d["session"].map(pos).to_numpy(dtype="float64")
    pi = prev_sess.map(pos).to_numpy(dtype="float64")
    ri = d["oi_ref_session"].map(pos).to_numpy(dtype="float64")
    qi = prev_ref.map(pos).to_numpy(dtype="float64")
    sess_adj = (si - pi) == 1
    ref_adj = (ri - qi) == 1
    d["pair_ok"] = sess_adj & ref_adj & np.isfinite(d["oi_prev"].to_numpy(dtype="float64"))
    drops = dict(rows=int(len(d)), no_prior_row=int((~np.isfinite(pi)).sum()),
                 session_not_adjacent=int((np.isfinite(pi) & ~sess_adj).sum()),
                 reference_not_adjacent=int((np.isfinite(pi) & sess_adj & ~ref_adj).sum()),
                 admitted=int(d["pair_ok"].sum()))
    same = d["expiry_date"].to_numpy() == d["session"].to_numpy()
    pm = d["expiry_hhmm"].to_numpy() >= T_ENTRY
    z = d[same & pm].copy()
    z["doi"] = np.where(z["pair_ok"], z["oi"] - z["oi_prev"], np.nan)
    t = pd.read_csv(CUTS, dtype={"session": str, "raw_symbol": str}, encoding="utf-8")
    t = t[(t["session"] >= IN_FROM) & (t["session"] <= IN_TO)]
    t["vol_noon"] = t["v_0000_1200"]
    t["vol_1530"] = t["v_0000_1200"] + t["v_1200_1530"]
    z = z.merge(t[["session", "raw_symbol", "vol_noon", "vol_1530"]], on=["session", "raw_symbol"], how="left")
    z[["vol_noon", "vol_1530"]] = z[["vol_noon", "vol_1530"]].fillna(0.0)     # absence means zero (D613 meta)
    return z, drops


def gamma_per_strike(z, s, strip):
    """|gamma| per option at both anchors, from the settlement-implied vol. D581's inversion, and its
    moneyness bound, reused; `oi > 0` is NOT required, because a strike going from zero to positive is
    exactly the position build a delta conditioner is about."""
    settle = strip[strip["root"] == "ES"].set_index(["ref", "contract"])["settle"]
    cal = np.array(sorted(s.index))
    prev_of = {day: cal[i - 1] for i, day in enumerate(cal) if i > 0}
    z = z[z["session"].isin(set(cal))].copy()
    z["prev"] = z["session"].map(prev_of)
    z["Fprev"] = [settle.get((p, u), np.nan) for p, u in zip(z["prev"], z["underlying"])]
    z["P1530"] = z["session"].map(s["P1530"])
    tau_settle = np.full(len(z), HOURS / YEAR_HOURS)
    tau_now = np.full(len(z), 0.5 / YEAR_HOURS)
    px = z["settle"].to_numpy(float)
    Fp = z["Fprev"].to_numpy(float)
    K = z["strike"].to_numpy(float)
    right = z["right"].to_numpy()
    m = np.isfinite(px) & np.isfinite(Fp) & (px > 0) & (np.abs(K / Fp - 1) < MONEYNESS_MAX)
    iv = np.full(len(z), np.nan)
    iv[m] = D581.implied_vol(px[m], Fp[m], K[m], tau_settle[m], right[m])
    ok = np.isfinite(iv)
    gnow = np.zeros(len(z))
    gpre = np.zeros(len(z))
    P = z["P1530"].to_numpy(float)
    live = ok & np.isfinite(P) & (P > 0)
    gnow[live] = np.abs(D581.b76_gamma(P[live], K[live], iv[live], tau_now[live]))
    gpre[live] = np.abs(D581.b76_gamma(Fp[live], K[live], iv[live], tau_settle[live]))
    z["gamma_now"] = gnow
    z["gamma_pre"] = gpre
    z["iv"] = iv
    return z, dict(rows=int(len(z)), iv_attempted=int(m.sum()), iv_inverted=int(ok.sum()),
                   share_inverted=float(ok.sum() / max(int(m.sum()), 1)),
                   median_iv=float(np.nanmedian(iv)))


def session_prior_settle(z):
    """The prior settlement per session, which is the PRE-SESSION anchor the band is centred on."""
    return z.groupby("session")["Fprev"].median()


def ladder_arrays(z):
    """Collapse to (session, strike): |gamma| averaged over the rights that inverted, everything else
    summed. Gamma is right-independent in Black-76 at one vol, but the INVERTED vol differs between the
    call and the put, so the average is the honest reduction and is stated rather than assumed."""
    z = z.copy()
    z["gn_n"] = (z["gamma_now"] > 0).astype(float)
    a = (z.groupby(["session", "strike"], sort=True)
         .agg(oi=("oi", "sum"), doi=("doi", "sum"), doi_n=("doi", "count"),
              vol_noon=("vol_noon", "sum"), vol_1530=("vol_1530", "sum"),
              gsum_now=("gamma_now", "sum"), gsum_pre=("gamma_pre", "sum"), gn=("gn_n", "sum"),
              rows=("right", "size")).reset_index())
    a["gamma_now"] = np.where(a["gn"] > 0, a["gsum_now"] / a["gn"].where(a["gn"] > 0, 1), 0.0)
    a["gamma_pre"] = np.where(a["gn"] > 0, a["gsum_pre"] / a["gn"].where(a["gn"] > 0, 1), 0.0)
    a["doi"] = np.where(a["doi_n"] > 0, a["doi"], np.nan)
    return a.drop(columns=["gsum_now", "gsum_pre", "gn"])


# ------------------------------------------------------------------ cells
def weight_of(kind, anchor, oi, doi, vol_noon, vol_1530, gnow, gpre):
    g = gnow if anchor == "now" else gpre
    if kind == "gamma_doi":
        return g * np.abs(np.nan_to_num(doi, nan=0.0))
    if kind == "doi":
        return np.abs(np.nan_to_num(doi, nan=0.0))
    if kind == "gamma":
        return g.copy()
    if kind == "gamma_oi":
        return g * oi
    if kind == "vol_noon":
        return vol_noon.copy()
    if kind == "vol_1530":
        return vol_1530.copy()
    raise AssertionError(f"unknown weight {kind}")


def centroid(k, w):
    tot = float(np.sum(w))
    if not np.isfinite(tot) or tot <= 0:
        return np.nan
    return float(np.sum(k * w) / tot)


def centroid_second_path(k, p, w):
    """p + sum((k-p)w)/sum(w): algebraically the same, a different floating-point route."""
    tot = float(np.sum(w))
    if not np.isfinite(tot) or tot <= 0:
        return np.nan
    return float(p + np.sum((k - p) * w) / tot)


def centroid_broken(k, w):
    """The break: divide by the COUNT instead of the weight sum. D614's own."""
    if k.size == 0:
        return np.nan
    return float(np.sum(k * w) / k.size)


def audit_centroid(k, p, w):
    a, b = centroid(k, w), centroid_second_path(k, p, w)
    if not (np.isfinite(a) and np.isfinite(b)) or abs(a - b) > 1e-9 * max(1.0, abs(a)):
        raise AssertionError(f"CENTROID: two paths give {a} and {b}")
    return True


def centroid_unpaired(k, w):
    """The break for the permutation audit: a reduction that has LOST the strike-weight pairing. It uses
    both vectors and returns a plausible number, and it is permutation-invariant, which is exactly the bug
    class a per-strike reduction introduces and a total cannot see."""
    tot = float(np.sum(w))
    if not np.isfinite(tot) or tot <= 0:
        return np.nan
    return float(np.sum(np.sort(k) * np.sort(w)) / tot)


def audit_gamma_permutation(k, w, rng, fn=centroid):
    """The audit D581's could not be. Its `audit_f1` compares a TOTAL, which is permutation-invariant, so
    it cannot catch a strike-mapping bug -- the exact failure a per-strike reduction introduces. Permute
    the weight vector WITHIN the session: same multiset, wrong strikes, and the reduction must MOVE. A
    reduction that does not move under any permutation is not reading the pairing.

    Flat weights are skipped rather than passed: there the permutation is the identity and the check
    cannot fire, which is D613's lesson about a comparison that has no way to disagree.
    """
    if k.size < 4 or np.sum(w) <= 0 or np.allclose(w, w[0]):
        raise AssertionError("GAMMA PERMUTATION: this input cannot exercise the check (flat or empty weights)")
    base = fn(k, w)
    for _ in range(50):
        p = rng.permutation(w.size)
        if not np.allclose(w[p], w):
            if abs(fn(k, w[p]) - base) > 1e-12:
                return True
    raise AssertionError("GAMMA PERMUTATION: no within-session permutation moved the reduction, so it is "
                         "not reading which weight belongs to which strike")


def audit_weights_bite_against_the_price(median_abs_points, floor):
    """RESTATED. D614 compared the centroid to the GRID centroid, which a gamma kernel passes trivially
    while the object is degenerate: the kernel is only sigma*sqrt(tau)*F wide, under three strikes at
    thirty minutes, so it sits on top of the price whatever the weights do. The comparator has to be THE
    PRICE. This audit is EXPECTED to fire on the gamma-weighted cell, which is why it exists."""
    if not np.isfinite(median_abs_points) or median_abs_points < floor:
        raise AssertionError(f"WEIGHTS BITE: median |K_w - P1530| is {median_abs_points:.3f} points, "
                             f"under the declared floor of {floor}")
    return True


def audit_band_not_endogenous(by_session, s, band=3):
    """The pre-registered audit: the strike set the band selects must NOT be a function of the day's move.

    The pre-session band is centred on the prior settlement, so its selection is fixed before the session
    opens -- asserted by the fact that the selected set is unchanged when P1530 is replaced by anything at
    all. The break is the P1530-centred band, and it must visibly DIFFER: the share of sessions whose
    selected set changes is reported, and a share of zero would mean the check cannot fire.
    """
    changed, n, jaccard = 0, 0, []
    for day, g in by_session.items():
        if day not in s.index:
            continue
        p = float(s.at[day, "P1530"])
        fp = float(g.get("Fprev", np.nan))
        if not (np.isfinite(p) and np.isfinite(fp) and np.isfinite(g["step"])):
            continue
        a = band_mask(g["strike"], fp, band, g["step"])
        b = band_mask(g["strike"], p, band, g["step"])
        n += 1
        if not np.array_equal(a, b):
            changed += 1
        inter = float((a & b).sum())
        union = float((a | b).sum())
        if union > 0:
            jaccard.append(inter / union)
    if n == 0:
        raise AssertionError("BAND ENDOGENEITY: no session could be checked")
    share = changed / n
    if share == 0.0:
        raise AssertionError("BAND ENDOGENEITY: the two bands never differ, so this check cannot fire")
    return dict(sessions=n, share_of_sessions_where_the_band_moves=float(share),
                median_jaccard_overlap=float(np.median(jaccard)) if jaccard else None,
                note="the pre-session band is the pre-registered one; the P1530 band is the break, and this "
                     "is how far apart they are")


def band_mask(k, p, band, step):
    if band is None:
        return np.ones(k.size, dtype=bool)
    return np.abs(k - p) <= band * step + 1e-9


def modal_step(k):
    if k.size < 3:
        return np.nan
    d = np.diff(np.unique(k))
    d = d[d > 0]
    if not d.size:
        return np.nan
    v, c = np.unique(np.round(d, 6), return_counts=True)
    return float(v[np.argmax(c)])


def cell_series(a_by_session, s, kind, band, band_tag, window, anchor, band_anchor="pre"):
    """LADDER, the grid placebo PING, the FLAT-weight comparator, and the construction diagnostics.

    `band_anchor` is the price the BAND is centred on, and it is not a free choice. The record pre-registers
    it PRE-SESSION -- the prior settlement -- and pre-registers the P1530-centred version as the BREAK,
    because a band selected around the current price is a function of the day's own move, which is exactly
    the circularity the whole study is about. The break is computed too, and reported as a diagnostic that
    carries no verdict weight, so the size of the artefact is visible instead of assumed.
    """
    sig_col = "sigma30_pts" if window == "w30" else "sigma10_pts"
    out = {}
    for day, g in a_by_session.items():
        if day not in s.index:
            continue
        p = float(s.at[day, "P1530"])
        sig = float(s.at[day, sig_col])
        if not (np.isfinite(p) and np.isfinite(sig) and sig > 0) or bool(s.at[day, "roll"]):
            continue
        centre = p if band_anchor == "now" else float(g.get("Fprev", np.nan))
        if not np.isfinite(centre):
            continue
        k = g["strike"]
        step = g["step"]
        if not np.isfinite(step):
            continue
        m = band_mask(k, centre, band, step)
        if m.sum() < 2:
            continue
        w = weight_of(kind, anchor, g["oi"][m], g["doi"][m], g["vol_noon"][m], g["vol_1530"][m],
                      g["gamma_now"][m], g["gamma_pre"][m])
        kk = k[m]
        c = centroid(kk, w)
        pos = w > 0
        out[day] = dict(LADDER=(c - p) / sig if np.isfinite(c) else np.nan,
                        PING=(centroid(kk, np.ones(kk.size)) - p) / sig,
                        FLAT=((centroid(kk[pos], np.ones(int(pos.sum()))) - p) / sig
                              if pos.sum() >= 2 else np.nan),
                        n_strikes=int(m.sum()), n_positive=int(pos.sum()),
                        abs_points=abs(c - p) if np.isfinite(c) else np.nan,
                        grid_off=(p % step) / step if np.isfinite(step) and step > 0 else np.nan)
    return pd.DataFrame.from_dict(out, orient="index").sort_index()


def screen(cell, s, window):
    """The four pre-outcome screens. No return is read here -- DAY0 is a control, measured before 12:00."""
    j = cell.join(s[["DAY0", "R30", "R10"]], how="inner")
    x = j["LADDER"].to_numpy(float)
    fin = np.isfinite(x)
    sd = float(np.nanstd(x)) if fin.sum() > 2 else np.nan
    flat = j["FLAT"].to_numpy(float)
    sd_flat = float(np.nanstd(flat)) if np.isfinite(flat).sum() > 2 else np.nan
    d0 = j["DAY0"].to_numpy(float)
    both = fin & np.isfinite(d0)
    corr = float(np.corrcoef(x[both], d0[both])[0, 1]) if both.sum() > 10 else np.nan
    go = j["grid_off"].to_numpy(float)
    gb = fin & np.isfinite(go)
    if gb.sum() > 10:
        A = np.column_stack([np.ones(gb.sum()), go[gb], np.cos(2 * np.pi * go[gb]), np.sin(2 * np.pi * go[gb])])
        beta = np.linalg.lstsq(A, x[gb], rcond=None)[0]
        resid = x[gb] - A @ beta
        r2 = float(1.0 - resid.var() / x[gb].var()) if x[gb].var() > 0 else np.nan
    else:
        r2 = np.nan
    med_n = float(np.nanmedian(j["n_strikes"].to_numpy(float)))
    med_pts = float(np.nanmedian(j["abs_points"].to_numpy(float)))
    ping = j["PING"].to_numpy(float)
    pb = fin & np.isfinite(ping)
    corr_ping = float(np.corrcoef(x[pb], ping[pb])[0, 1]) if pb.sum() > 10 else np.nan
    res = dict(n_sessions=int(fin.sum()), sd=sd, sd_flat=sd_flat,
               # kept as a DIAGNOSTIC and no longer a gate: it rejected a perfect oracle at 0.05, because
               # for a smooth weight the positive-weight set is the whole ladder (see S1B_PING_CEIL)
               sd_over_flat=float(sd / sd_flat) if np.isfinite(sd_flat) and sd_flat > 0 else np.nan,
               corr_ping=corr_ping,
               corr_day0=corr, grid_r2=r2, median_strikes=med_n, median_abs_points=med_pts)
    res["S1a"] = bool(np.isfinite(sd) and sd >= S1A_FLOOR)
    res["S1b"] = bool(np.isfinite(corr_ping) and abs(corr_ping) <= S1B_PING_CEIL)
    res["S2"] = bool(np.isfinite(corr) and abs(corr) <= S2_CEIL)
    res["S3"] = bool(np.isfinite(r2) and r2 <= S3_CEIL)
    res["S4"] = bool(np.isfinite(med_n) and med_n >= S4_FLOOR)
    res["passes"] = bool(res["S1a"] and res["S1b"] and res["S2"] and res["S3"] and res["S4"])
    res["range_and_independence"] = bool(np.isfinite(sd) and np.isfinite(corr) and sd >= 1.0 and abs(corr) <= S2_CEIL)
    return res


# ------------------------------------------------------------------ scoring
def controls_for(j, window):
    sig = j["sigma30_bp"].to_numpy(float) if window == "w30" else j["sigma10_bp"].to_numpy(float)
    cols = {"ON": j["ON"].to_numpy(float) / sig, "DAY0": j["DAY0"].to_numpy(float) / sig,
            "MIDE": j["MIDE"].to_numpy(float) / sig, "F5": j["F5"].to_numpy(float) / sig,
            "PING": j["PING"].to_numpy(float)}
    if window == "w10":
        cols["LEG1"] = j["LEG1"].to_numpy(float) / sig      # inside the primary's window, so w30 must not have it
    return cols


def score_cell(cell, s, window, label, rng, pt_usd, cost_usd):
    y_col = "R30" if window == "w30" else "R10"
    j = cell.join(s[["ON", "DAY0", "MIDE", "F5", "LEG1", "R30", "R10", "sigma30_bp", "sigma10_bp",
                     "P1530", "P1550", "P1600", "week", "year"]], how="inner")
    j = j[np.isfinite(j["LADDER"]) & np.isfinite(j[y_col]) & np.isfinite(j["ON"])]
    y = j[y_col].to_numpy(float)
    ctrl = controls_for(j, window)
    cols = dict(ctrl)
    cols["LADDER"] = j["LADDER"].to_numpy(float)
    D614.audit_not_singular(cols)
    c = D614.coef_named(y, cols, "LADDER")
    fit = D614.fit_named(y, cols, lag=NW_LAG)
    lad = D614.se_ladder(y, cols, target="LADDER")
    tails = D614.tail_diagnostics(y, cols, target="LADDER", top=TAIL_TOP, labels=list(j.index))
    obs_n, shift = D614.shift_null_norm(y, ctrl, cols["LADDER"], kmin=SHIFT_MIN)
    obs_f, flip = D614.flip_null(y, ctrl, cols["LADDER"], draws=FLIP_DRAWS, seed=SEED)
    wse = D614.week_block_se(y, cols, "LADDER", j["week"].to_numpy(), rng, boot=BOOT)
    # the tail bar: drop the ten largest |LADDER| sessions and the coefficient must keep sign and half size
    order = np.argsort(-np.abs(cols["LADDER"]))
    drop = set(order[:TAIL_TOP].tolist())
    keep = np.array([i not in drop for i in range(len(y))])
    cols_ex = {k: v[keep] for k, v in cols.items()}
    c_ex = D614.coef_named(y[keep], cols_ex, "LADDER")
    tail_bar = bool(np.sign(c_ex) == np.sign(c) and abs(c_ex) >= TAIL_BAR_FRACTION * abs(c))
    # economics, in the units the record declared: dollars per trade at one MES, both directions
    move = (j["P1600"] - (j["P1530"] if window == "w30" else j["P1550"])).to_numpy(float) * pt_usd
    econ = {}
    for tag, sgn in (("attraction", +1.0), ("repulsion", -1.0)):
        gross = sgn * np.sign(cols["LADDER"]) * move
        net = gross - cost_usd
        econ[tag] = dict(gross_usd_per_trade=float(np.mean(gross)), net_usd_per_trade=float(np.mean(net)),
                         gross_sharpe=_ratio(gross)[0], gross_sortino=_ratio(gross)[1],
                         net_sharpe=_ratio(net)[0], net_sortino=_ratio(net)[1],
                         hit_rate=float((gross > 0).mean()), median_gross_usd=float(np.median(gross)))
    mean_abs = float(np.mean(np.abs(cols["LADDER"])))
    econ["expected_move_bp_at_mean_abs_ladder"] = float(abs(c) * mean_abs)
    econ["expected_move_usd_at_mean_abs_ladder"] = float(abs(c) * mean_abs / 1e4 * float(np.mean(j["P1530"])) * pt_usd)
    econ["round_trip_usd"] = cost_usd
    econ["clears_round_trip"] = bool(econ["expected_move_usd_at_mean_abs_ladder"] >= cost_usd)
    return dict(label=label, window=window, n=int(len(y)), coef=c, fit=fit, estimator_ladder=lad,
                tails=tails, week_block_se=wse,
                # |obs| against |null|. Passing the SIGNED coefficient against an absolute null makes every
                # rank 0.000 by construction, which is what the first pass of this runner did.
                shift_null=D581.blk(abs(obs_n), np.abs(shift)) | {"observed_signed": float(obs_n)},
                flip_null=D581.blk(abs(obs_f), np.abs(flip)) | {"observed_signed": float(obs_f)},
                tail_bar=dict(coef_excluding_top=c_ex, keeps_sign_and_half=tail_bar,
                              fraction_required=TAIL_BAR_FRACTION),
                economics=econ, mean_abs_ladder=mean_abs)


def _ratio(v):
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    sd = float(np.std(v))
    dn = v[v < 0]
    sdn = float(np.std(dn)) if dn.size else np.nan
    return (float(np.mean(v) / sd * np.sqrt(252)) if sd > 0 else np.nan,
            float(np.mean(v) / sdn * np.sqrt(252)) if np.isfinite(sdn) and sdn > 0 else np.nan)


def guard_outputs(res):
    missing = [k for k in REQUIRED_OUTPUTS if k not in res]
    if missing:
        raise AssertionError(f"REQUIRED_OUTPUTS missing: {missing}")
    return True


def family_max_null(passing, s, rng):
    """max|t| over the passing family, against the max|t| of THE SAME FAMILY recomputed on each null draw.

    The statistic is studentised with each cell's OWN observed standard error, held fixed across draws.
    That is legitimate here for one reason and only one: the null is the NORM-PRESERVING Frisch-Waugh
    rotation, so the regressor's norm -- and therefore the coefficient's standard error -- is identical in
    every draw. Recomputing a HAC standard error per draw per cell would be a different statistic, not a
    more honest one, and it would cost hours.
    """
    if not passing:
        return dict(cells=0, note="no cell passed the screens, so there is no family to price")
    per_cell, offsets = {}, None
    for label, cell, window in passing:
        y_col = "R30" if window == "w30" else "R10"
        j = cell.join(s[["ON", "DAY0", "MIDE", "F5", "LEG1", "R30", "R10", "sigma30_bp", "sigma10_bp"]],
                      how="inner")
        j = j[np.isfinite(j["LADDER"]) & np.isfinite(j[y_col]) & np.isfinite(j["ON"])]
        y = j[y_col].to_numpy(float)
        ctrl = controls_for(j, window)
        cols = dict(ctrl)
        cols["LADDER"] = j["LADDER"].to_numpy(float)
        se = D614.se_ladder(y, cols, target="LADDER")["ols_homoskedastic"]["se"]
        obs, vals = D614.shift_null_norm(y, ctrl, cols["LADDER"], kmin=SHIFT_MIN)
        t = np.abs(vals) / se if se > 0 else np.abs(vals) * np.nan
        per_cell[label] = dict(observed_t=abs(obs) / se if se > 0 else np.nan, draws=t)
        offsets = t.size if offsets is None else min(offsets, t.size)
    obs_max = max(v["observed_t"] for v in per_cell.values())
    stack = np.vstack([v["draws"][:offsets] for v in per_cell.values()])
    fam = np.nanmax(stack, axis=0)
    return dict(cells=len(per_cell), offsets=int(offsets),
                observed_family_max_t=float(obs_max),
                per_cell_observed_t={k: float(v["observed_t"]) for k, v in per_cell.items()},
                family_max_null=D581.blk(obs_max, fam),
                # each cell's OWN p95, so the cost of having looked at the family is visible as the gap
                # between the largest of these and the family-max p95
                per_cell_own_p95_t={k: float(np.nanpercentile(v["draws"][:offsets], 95))
                                    for k, v in per_cell.items()},
                note=("the bar a single pre-registered cell would have faced is its own p95; the bar the "
                      "family faces is the family-max p95, and the difference is what looking at "
                      f"{len(per_cell)} cells costs"))


def delta_oi_gate(by_session, s, step_of):
    """The named gate: the delta centroid residualised against the OI centroid AND the volume centroid on
    the same strike set. If the coefficient lives in the shared part, the record says volume in disguise."""
    rows = {}
    for day, g in by_session.items():
        if day not in s.index:
            continue
        p = float(s.at[day, "P1530"])
        sig = float(s.at[day, "sigma30_pts"])
        if not (np.isfinite(p) and np.isfinite(sig) and sig > 0) or bool(s.at[day, "roll"]):
            continue
        k = g["strike"]
        d = np.abs(np.nan_to_num(g["doi"], nan=0.0))
        o = g["oi"]
        v = g["vol_noon"]
        rows[day] = dict(DOI=(centroid(k, d) - p) / sig, OI=(centroid(k, o) - p) / sig,
                         VOL=(centroid(k, v) - p) / sig,
                         sum_abs_doi=float(np.nansum(np.abs(g["doi"]))),
                         turnover=float(np.nansum(g["vol_1530"])))
    t = pd.DataFrame.from_dict(rows, orient="index").sort_index().join(
        s[["R30", "ON", "DAY0", "MIDE", "F5", "sigma30_bp"]], how="inner")
    t = t[np.isfinite(t[["DOI", "OI", "VOL", "R30", "ON"]]).all(axis=1)]
    y = t["R30"].to_numpy(float)
    sig = t["sigma30_bp"].to_numpy(float)
    base = {"ON": t["ON"].to_numpy(float) / sig, "DAY0": t["DAY0"].to_numpy(float) / sig,
            "MIDE": t["MIDE"].to_numpy(float) / sig, "F5": t["F5"].to_numpy(float) / sig,
            "OI": t["OI"].to_numpy(float), "VOL": t["VOL"].to_numpy(float)}
    cols = dict(base)
    cols["DOI"] = t["DOI"].to_numpy(float)
    D614.audit_not_singular(cols)
    resid_coef = D614.coef_named(y, cols, "DOI")
    naive = D614.coef_named(y, {"ON": base["ON"], "DAY0": base["DAY0"], "MIDE": base["MIDE"],
                                "F5": base["F5"], "DOI": cols["DOI"]}, "DOI")
    Z = np.column_stack([np.ones(len(y))] + [base[k] for k in base])
    xr = D614._resid(cols["DOI"], Z)
    yr = D614._resid(y, Z)
    inc_r2 = float((xr @ yr) ** 2 / ((xr @ xr) * (yr @ yr))) if (xr @ xr) > 0 and (yr @ yr) > 0 else np.nan
    return dict(n=int(len(y)),
                corr_doi_oi=float(np.corrcoef(cols["DOI"], base["OI"])[0, 1]),
                corr_doi_vol=float(np.corrcoef(cols["DOI"], base["VOL"])[0, 1]),
                coef_residualised_on_oi_and_vol=float(resid_coef),
                coef_without_those_two_controls=float(naive),
                incremental_r2=inc_r2,
                share_of_variance_left=float((xr @ xr) / float(cols["DOI"] @ cols["DOI"])),
                median_sum_abs_doi=float(np.nanmedian(t["sum_abs_doi"])),
                median_turnover=float(np.nanmedian(t["turnover"])),
                median_doi_over_turnover=float(np.nanmedian(
                    t["sum_abs_doi"] / t["turnover"].where(t["turnover"] > 0))),
                verdict=("volume in disguise" if abs(resid_coef) < 0.5 * abs(naive)
                         else "the residual carries the coefficient"))


def run():
    t0 = time.time()
    TEMP.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    spec = json.loads(SPECS.read_text(encoding="utf-8"))
    tick_pts, tick_usd = float(spec["ES"]["tick_points"]), float(spec["MES"]["tick_usd"])
    pt_usd = tick_usd / tick_pts
    cost_usd = 3.00 + 1.0 * tick_usd
    res = {"spec": SPEC, "corrections": [], "audits": {}}

    s, wmeta = load_es()
    res["windows"] = dict(WINDOWS, primary=PRIMARY_WINDOW, **wmeta)
    res["audits"]["window_additivity"] = audit_window_additivity(s)
    expect_raise(lambda: audit_additivity_broken(s), "a one-bp slip in the first leg")
    log(f"  prices: {len(s)} sessions {s.index.min()} .. {s.index.max()}; "
        f"R30 == LEG1 + R10 to {res['audits']['window_additivity']['max_abs_deviation']:.1e}; "
        f"sd(R10)/sd(R30) = {res['audits']['window_additivity']['sd_ratio_r10_over_r30']:.4f}")

    cal = es_calendar()
    cf = TEMP / f"ladder_{cache_key()}.pkl"
    if cf.exists():
        z, drops, ivstats = pd.read_pickle(cf)
    else:
        z, drops = build_ladder(cal)
        z, ivstats = gamma_per_strike(z, s, pd.read_csv(STRIP, dtype={"root": str, "contract": str, "ref": str},
                                                       encoding="utf-8"))
        pd.to_pickle((z, drops, ivstats), cf)
    a = ladder_arrays(z)
    res["premise"] = dict(delta_oi=drops, iv=ivstats)
    zero_share = float((np.abs(a["doi"].to_numpy(float)) < 1e-12).mean())
    res["premise"]["zero_delta_share"] = zero_share
    log(f"  ladder: {len(a):,} (session, strike) cells over {a['session'].nunique():,} sessions; "
        f"delta admitted on {drops['admitted']:,} of {drops['rows']:,} option rows "
        f"(session not adjacent {drops['session_not_adjacent']:,}, reference not adjacent "
        f"{drops['reference_not_adjacent']:,}); zero-delta share {zero_share:.4f}; "
        f"IV inverted on {ivstats['share_inverted']:.4f}, median {ivstats['median_iv']:.3f}")

    fprev = session_prior_settle(z)
    by_session, step_of = {}, {}
    for day, g in a.groupby("session", sort=True):
        k = g["strike"].to_numpy(float)
        st = modal_step(k)
        step_of[day] = st
        by_session[day] = dict(strike=k, step=st, oi=g["oi"].to_numpy(float), doi=g["doi"].to_numpy(float),
                               vol_noon=g["vol_noon"].to_numpy(float), vol_1530=g["vol_1530"].to_numpy(float),
                               gamma_now=g["gamma_now"].to_numpy(float), gamma_pre=g["gamma_pre"].to_numpy(float),
                               Fprev=float(fprev.get(day, np.nan)))
    # the band-endogeneity audit: the pre-session band cannot depend on the day's move, and the P1530 band does
    res["audits"]["band_endogeneity"] = audit_band_not_endogenous(by_session, s)
    # the centroid's two paths and the permutation audit, on seeded real sessions
    days = sorted(by_session)
    pick = [days[i] for i in rng.choice(len(days), 6, replace=False)]
    checks = []
    for day in pick:
        g = by_session[day]
        p = float(s.at[day, "P1530"]) if day in s.index else np.nan
        w = weight_of("gamma_oi", "now", g["oi"], g["doi"], g["vol_noon"], g["vol_1530"],
                      g["gamma_now"], g["gamma_pre"])
        if not np.isfinite(p) or np.sum(w) <= 0:
            continue
        audit_centroid(g["strike"], p, w)
        audit_gamma_permutation(g["strike"], w, rng)
        hand = D581.b76_gamma_hand
        i = int(np.argmax(g["gamma_now"]))
        checks.append(dict(session=day, strikes=int(g["strike"].size), peak_strike=float(g["strike"][i])))
    res["audits"]["centroid_and_permutation"] = dict(sessions=checks, passes=True)
    expect_raise(lambda: audit_centroid(np.array([1.0, 2.0]), 1.5, np.zeros(2)), "a zero weight sum on real shape")
    log(f"  audits: centroid two paths and the within-session permutation hold on {len(checks)} seeded sessions")

    # ---------------- the screens, every cell, before any return is read
    screens, cells, endo = [], {}, []
    for kind in WEIGHTS:
        anchs = ANCHORS if kind in GAMMA_WEIGHTS else (None,)
        for anchor in anchs:
            for band, btag in BANDS:
                for window in WINDOWS:
                    label = f"{kind}|{btag}|{window}" + (f"|{anchor}" if anchor else "")
                    cell = cell_series(by_session, s, kind, band, btag, window, anchor or "now",
                                       band_anchor="pre")
                    if not len(cell):
                        continue
                    sc = screen(cell, s, window)
                    sc.update(weight=kind, band=btag, window=window, anchor=anchor, label=label,
                              band_anchor="pre")
                    screens.append(sc)
                    cells[label] = (cell, window)
                    if band is not None:      # the unbanded cell is identical under both anchors
                        d = cell_series(by_session, s, kind, band, btag, window, anchor or "now",
                                        band_anchor="now")
                        if len(d):
                            sd = screen(d, s, window)
                            sd.update(weight=kind, band=btag, window=window, anchor=anchor,
                                      label=label + "|ENDOGENOUS_BAND", band_anchor="now")
                            endo.append(sd)
    res["endogenous_band_diagnostic"] = endo
    # The artefact, measured rather than asserted. Banding around P1530 is the pre-registered BREAK, and on
    # the first pass of this runner it was what the runner did -- four cells "passed" and one cleared both
    # its own nulls. Those cells are scored HERE under a label that says what they are, so the size of the
    # illusion is on the record. They carry NO verdict weight and are not in the family-maximum null.
    res["artefact_scored"] = []
    for kind in WEIGHTS:
        anchs = ANCHORS if kind in GAMMA_WEIGHTS else (None,)
        for anchor in anchs:
            for band, btag in BANDS:
                if band is None:
                    continue
                for window in WINDOWS:
                    lab = f"{kind}|{btag}|{window}" + (f"|{anchor}" if anchor else "") + "|ENDOGENOUS_BAND"
                    sd_ = next((x for x in endo if x["label"] == lab), None)
                    if sd_ is None or not sd_["passes"]:
                        continue
                    d = cell_series(by_session, s, kind, band, btag, window, anchor or "now",
                                    band_anchor="now")
                    try:
                        r = score_cell(d, s, window, lab, rng, pt_usd, cost_usd)
                        r["carries_no_verdict_weight"] = True
                        r["why"] = ("the band is centred on P1530, so the strike set is a function of the "
                                    "day's own move -- the pre-registered break, not the specification")
                        res["artefact_scored"].append(r)
                    except AssertionError as e:
                        res["artefact_scored"].append(dict(label=lab, error=str(e)))
    for r in res["artefact_scored"]:
        if "coef" in r:
            log(f"    ARTEFACT {r['label'][:40]:<40} c {r['coef']:+7.3f}  NW t {r['fit']['t']['LADDER']:+6.2f}  "
                f"shift rank {r['shift_null']['pct_rank']:.3f}  flip rank {r['flip_null']['pct_rank']:.3f}  "
                f"$move {r['economics']['expected_move_usd_at_mean_abs_ladder']:.2f} vs {cost_usd:.2f}")
    res["screens"] = screens
    res["sets"] = dict(cells=len(screens), weights=list(WEIGHTS), bands=[b[1] for b in BANDS],
                       windows=list(WINDOWS), anchors=list(ANCHORS),
                       thresholds=dict(S1a=S1A_FLOOR, S1b_corr_with_ping=S1B_PING_CEIL, S2=S2_CEIL,
                                       S3=S3_CEIL, S4=S4_FLOOR))
    passed = [x for x in screens if x["passes"]]
    both = [x for x in screens if x["range_and_independence"]]
    log(f"  screens: {len(screens)} cells, {len(passed)} pass all four, "
        f"{len(both)} have BOTH range (sd >= 1.0) and independence (|corr| <= 0.40)")
    for x in sorted(screens, key=lambda q: -(q["sd"] if np.isfinite(q["sd"]) else -1))[:12]:
        failed = ",".join(k for k in ("S1a", "S1b", "S2", "S3", "S4") if not x[k])
        log(f"    {x['label']:<34} sd {x['sd']:7.3f}  corr(PING) {x['corr_ping']:+.3f}  "
            f"corr(DAY0) {x['corr_day0']:+.3f}  gridR2 {x['grid_r2']:.3f}  strikes {x['median_strikes']:5.0f}  "
            f"{'PASS' if x['passes'] else 'fails ' + failed}")
    for x in [q for q in screens if q["passes"]]:
        log(f"    PASSES ALL FIVE: {x['label']:<30} sd {x['sd']:7.3f}  corr(PING) {x['corr_ping']:+.4f}  "
            f"corr(DAY0) {x['corr_day0']:+.3f}")

    # the WEIGHTS BITE audit, restated against the price, on the gamma-weighted primary
    prim = next((x for x in screens if x["label"].startswith("gamma_doi|all|w30")), None)
    if prim is not None:
        try:
            audit_weights_bite_against_the_price(prim["median_abs_points"], WEIGHTS_BITE_FLOOR_PTS)
            res["audits"]["weights_bite"] = dict(fired=False, median_abs_points=prim["median_abs_points"])
        except AssertionError as e:
            res["audits"]["weights_bite"] = dict(fired=True, median_abs_points=prim["median_abs_points"],
                                                 message=str(e))
            log(f"  WEIGHTS BITE fired on the gamma-weighted cell, as the record predicted: {e}")

    # ---------------- predictions
    sd_of = {x["label"]: x["sd"] for x in screens}
    corr_of = {x["label"]: x["corr_day0"] for x in screens}
    res["predictions"] = {
        "1_no_cell_has_both_range_and_independence": dict(
            holds=bool(not both), falsifying_cells=[x["label"] for x in both],
            max_sd_among_independent=float(max([x["sd"] for x in screens
                                                if np.isfinite(x["corr_day0"]) and abs(x["corr_day0"]) <= S2_CEIL]
                                               or [np.nan])),
            min_abs_corr_among_wide=float(min([abs(x["corr_day0"]) for x in screens
                                               if np.isfinite(x["sd"]) and x["sd"] >= 1.0]
                                              or [np.nan]))),
        "2_gamma_doi_passes_S1": dict(sd=sd_of.get("gamma_doi|all|w30|now"),
                                      corr=corr_of.get("gamma_doi|all|w30|now"),
                                      passes_S1a=bool((sd_of.get("gamma_doi|all|w30|now") or 0) >= S1A_FLOOR)),
        "3_tight_bands_fail_S3_or_S4": [
            dict(label=x["label"], grid_r2=x["grid_r2"], median_strikes=x["median_strikes"],
                 fails=bool(not (x["S3"] and x["S4"])))
            for x in screens if x["band"] in ("1step", "2step") and x["window"] == "w30"],
    }

    # ---------------- the Delta-OI gate
    res["delta_oi_gate"] = delta_oi_gate(by_session, s, step_of)
    g = res["delta_oi_gate"]
    log(f"  delta-OI gate: corr with the OI centroid {g['corr_doi_oi']:+.3f} and the volume centroid "
        f"{g['corr_doi_vol']:+.3f}; residualised coefficient {g['coef_residualised_on_oi_and_vol']:+.4f} "
        f"against {g['coef_without_those_two_controls']:+.4f} without them; {g['verdict']}")

    # ---------------- scoring, in the declared priority order
    res["scored"] = []
    chosen = None
    for kind, btag, window, anchor in PRIORITY:
        label = f"{kind}|{btag}|{window}" + (f"|{anchor}" if anchor else "")
        sc = next((x for x in screens if x["label"] == label), None)
        if sc is None or not sc["passes"]:
            continue
        chosen = label
        break
    res["priority_order"] = [f"{k}|{b}|{w}" + (f"|{a}" if a else "") for k, b, w, a in PRIORITY]
    res["chosen_cell"] = chosen
    to_score = [chosen] if chosen else []
    to_score += [x["label"] for x in passed if x["label"] != chosen]
    for label in to_score:
        cell, window = cells[label]
        try:
            res["scored"].append(score_cell(cell, s, window, label, rng, pt_usd, cost_usd))
        except AssertionError as e:
            res["scored"].append(dict(label=label, error=str(e)))
    for r in res["scored"]:
        if "coef" in r:
            log(f"    scored {r['label']:<34} c {r['coef']:+8.4f}  NW t {r['fit']['t']['LADDER']:+6.2f}  "
                f"shift p95 {r['shift_null']['p95']:.4f}  tail bar "
                f"{'held' if r['tail_bar']['keeps_sign_and_half'] else 'FAILED'}  "
                f"$/trade {max(r['economics']['attraction']['gross_usd_per_trade'], r['economics']['repulsion']['gross_usd_per_trade']):+.2f}")

    res["family_null"] = family_max_null([(x["label"], cells[x["label"]][0], cells[x["label"]][1])
                                          for x in passed], s, rng)

    # ---------------- the component line, whatever the verdict
    res["component"] = []
    # If nothing in the SPECIFIED family was scored, the component line is computed on the best ARTEFACT
    # cell instead, labelled as such. CLAUDE.md requires a component line for every construction scored
    # against returns and the artefact cells were; omitting it would hide the economics of the only thing
    # measured, and including it unlabelled would dress an artefact as a candidate.
    comp_src = [(r, cells[r["label"]][0], cells[r["label"]][1]) for r in res["scored"][:1] if "coef" in r]
    if not comp_src:
        best = max((r for r in res["artefact_scored"] if "coef" in r),
                   key=lambda q: q["economics"]["expected_move_usd_at_mean_abs_ladder"], default=None)
        if best is not None:
            k2, b2, w2, a2 = best["label"].split("|")[:4]
            band2 = next(bb for bb, tt in BANDS if tt == b2)
            comp_src = [(best, cell_series(by_session, s, k2, band2, b2, w2, a2, band_anchor="now"), w2)]
    for r, cell, window in comp_src:
        j = cell.join(s[["P1530", "P1550", "P1600", "R30", "R10"]], how="inner")
        j = j[np.isfinite(j["LADDER"]) & np.isfinite(j["P1600"])]
        entry = j["P1530"] if window == "w30" else j["P1550"]
        for tag, sgn in (("attraction", +1.0), ("repulsion", -1.0)):
            pos = sgn * np.sign(j["LADDER"].to_numpy(float))
            gross = pos * (j["P1600"] - entry).to_numpy(float) * pt_usd
            net = gross - cost_usd
            gs, gso = _ratio(gross)
            ns, nso = _ratio(net)
            eq = np.cumsum(net)
            comp = dict(cell=r["label"], direction=tag, n=int(len(net)),
                        gross_sharpe=gs, gross_sortino=gso, net_sharpe=ns, net_sortino=nso,
                        gross_usd_per_trade=float(np.mean(gross)), net_usd_per_trade=float(np.mean(net)),
                        median_net_usd=float(np.median(net)), hit_rate=float((gross > 0).mean()),
                        payoff=float(np.mean(gross[gross > 0]) / abs(np.mean(gross[gross < 0])))
                        if (gross < 0).any() and (gross > 0).any() else None,
                        skew=float(pd.Series(net).skew()), kurtosis=float(pd.Series(net).kurt()),
                        exposure="one MES for the scored window on every eligible session",
                        # named `maxdd` so `label_drawdown_convention.py` can DERIVE the sign marker from
                        # the values (D542). `maxDD_usd` escaped its key regex, which is anchored at the
                        # end of the name, and a convention typed in prose is a comment where a derived
                        # one is a gate.
                        maxdd=float(np.max(np.maximum.accumulate(eq) - eq)),
                        maxdd_units="dollars at one MES, positive from peak",
                        cost_usd_per_round_trip=cost_usd,
                        carries_no_verdict_weight=bool(r.get("carries_no_verdict_weight")),
                        what_this_measures=(r.get("why") or "the cell scored from the specified family"))
            P = j.copy()
            P[f"PIN_{tag}"] = j["LADDER"]
            comp["rho_with_macd_arm"] = D614.macd_rho(P.index, comp, j["R30"].to_numpy(float), P,
                                                      pt_usd, cost_usd, tag)
            res["component"].append(comp)
            log(f"    component {tag:<11} gross Sharpe {gs:+.3f} / Sortino {gso:+.3f}   "
                f"net {ns:+.3f} / {nso:+.3f}   net ${np.mean(net):+.2f} a session   "
                f"rho {comp['rho_with_macd_arm'].get('rho')}")

    # ---------------- verdict
    # Three questions, kept apart, because the first pass of this runner collapsed them and called a cell
    # that FAILS the placebo floor a reason to go forward.
    both_and_pass = [x["label"] for x in both if x["passes"]]
    both_but_fail = [dict(label=x["label"], sd=x["sd"], corr_day0=x["corr_day0"],
                          sd_over_flat=x["sd_over_flat"], corr_ping=x["corr_ping"],
                          failed=[k for k in ("S1a", "S1b", "S2", "S3", "S4") if not x[k]]) for x in both
                     if not x["passes"]]
    clears_nulls = [r["label"] for r in res["scored"] if "coef" in r
                    and r["shift_null"]["above_p95"] and r["flip_null"]["above_p95"]]
    clears_econ = [r["label"] for r in res["scored"] if "coef" in r and r["economics"]["clears_round_trip"]]
    fam_clears = bool(res["family_null"].get("family_max_null", {}).get("above_p95"))
    res["verdict_parts"] = dict(prediction1_falsified=bool(both), falsified_by_cells_that_pass=both_and_pass,
                                falsified_by_cells_that_fail_a_screen=both_but_fail,
                                cells_clearing_both_nulls=clears_nulls,
                                cells_clearing_the_economic_bar=clears_econ,
                                family_max_null_cleared=fam_clears)
    if not passed:
        verdict = "THE FAMILY IS DEGENERATE -- no cell passes the construction screens; no return was scored"
    elif both_and_pass and clears_nulls and clears_econ and fam_clears:
        verdict = ("A CELL SURVIVES EVERYTHING -- it passes the screens, clears both nulls, clears the "
                   "family-maximum null and the economic bar; a forward read on the principal's word is warranted")
    elif clears_nulls and not (clears_econ and fam_clears):
        verdict = ("NOTHING GOES FORWARD -- a cell clears its own two nulls but not the family-maximum null "
                   "that prices the 72 looks and not the economic bar, so the line stays closed")
    else:
        verdict = ("NOTHING GOES FORWARD -- no cell that passes the construction screens clears its own "
                   "nulls, and the line stays closed")
    if both_but_fail and not both_and_pass:
        verdict += ("; prediction 1 is falsified on its literal terms, but ONLY by cells whose dispersion is "
                    "the ladder's own extent rather than the weights' -- they fail the flat-weight placebo "
                    "floor, which is a THIRD source of variance the prediction did not anticipate")
    res["verdict"] = verdict
    res["timing_s"] = round(time.time() - t0, 1)
    guard_outputs(res)
    expect_raise(lambda: guard_outputs({k: v for k, v in res.items() if k != "screens"}),
                 "a missing declared output")
    OUT.write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    log(f"  VERDICT: {verdict}")
    log(f"  wrote {OUT.relative_to(REPO)} in {res['timing_s']:.1f} s")
    return res


def selftest():
    log(f"{SPEC} selftest")
    rng = np.random.default_rng(SEED)
    # Black-76 and the scalar second path
    g = float(D581.b76_gamma(100.0, 100.0, 0.2, 1.0))
    gh = D581.b76_gamma_hand(100.0, 100.0, 0.2, 1.0)
    assert abs(g - gh) < 1e-12, (g, gh)
    log(f"  gamma: vectorised and scalar agree to {abs(g-gh):.1e}")
    # the centroid, its second path, and its two breaks
    k = np.array([4000.0, 4005.0, 4010.0, 4015.0])
    w = np.array([1.0, 3.0, 1.0, 0.0])
    p = 4004.0
    assert audit_centroid(k, p, w)
    assert abs(centroid(k, w) - 4005.0) < 1e-12, centroid(k, w)
    expect_raise(lambda: audit_centroid(k, p, np.zeros(4)), "a zero weight sum")
    assert abs(centroid_broken(k, w) - centroid(k, w)) > 1.0, "the count-divided break must differ"
    log("  centroid: two paths agree; the count-divided break differs")
    assert audit_gamma_permutation(k, w, rng)
    expect_raise(lambda: audit_gamma_permutation(k, w, rng, fn=centroid_unpaired),
                 "a reduction that lost the strike-weight pairing")
    expect_raise(lambda: audit_gamma_permutation(k, np.ones(4), rng),
                 "a flat weight, where the permutation is the identity and the check cannot fire")
    log("  gamma permutation: the real centroid moves under a within-session permutation, the unpaired "
        "reduction does not, and a check that cannot fire is refused")
    # WEIGHTS BITE against the price: it must fire on a degenerate object and pass a biting one
    assert audit_weights_bite_against_the_price(4.0, 2.0)
    expect_raise(lambda: audit_weights_bite_against_the_price(1.3, 2.0), "a centroid sitting on the price")
    # the band, the modal step, and the screens
    assert modal_step(np.arange(4000.0, 4100.0, 5.0)) == 5.0
    assert band_mask(k, p, 1, 5.0).sum() == 2 and band_mask(k, p, None, 5.0).all()
    idx = [f"2020-01-{d:02d}" for d in range(1, 29)]
    s = pd.DataFrame(index=idx)
    s["DAY0"] = rng.normal(0, 30, len(idx))
    s["R30"] = rng.normal(0, 30, len(idx))
    s["R10"] = rng.normal(0, 20, len(idx))
    wide = pd.DataFrame(index=idx)
    wide["LADDER"] = rng.normal(0, 2.0, len(idx))
    wide["FLAT"] = wide["LADDER"] / 10.0
    wide["PING"] = rng.normal(0, 0.1, len(idx))
    wide["n_strikes"] = 40
    wide["abs_points"] = 20.0
    wide["grid_off"] = rng.uniform(0, 1, len(idx))
    r = screen(wide, s, "w30")
    assert r["S1a"] and r["S1b"] and r["S4"], r
    tiny = wide.copy()
    tiny["LADDER"] = wide["LADDER"] * 0.01
    assert not screen(tiny, s, "w30")["S1a"], "a 0.02 sigma cell must fail the measurement floor"
    # S1b, corrected: a cell that IS the grid centroid must fail; one distinguishable from it must pass.
    isgrid = wide.copy()
    isgrid["PING"] = isgrid["LADDER"]
    assert not screen(isgrid, s, "w30")["S1b"], "a cell identical to the grid centroid must fail S1b"
    assert screen(wide, s, "w30")["S1b"], "a cell uncorrelated with the grid centroid must pass S1b"
    half = wide.copy()
    half["PING"] = 0.95 * wide["LADDER"] + 0.05 * rng.normal(0, wide["LADDER"].std(), len(idx))
    assert not screen(half, s, "w30")["S1b"], "a cell 95 % explained by the grid centroid must fail S1b"
    conf = wide.copy()
    conf["LADDER"] = s["DAY0"].to_numpy() / 30.0
    assert not screen(conf, s, "w30")["S2"], "a conditioner that IS the day's move must fail S2"
    saw = wide.copy()
    saw["LADDER"] = wide["grid_off"].to_numpy() * 3.0
    assert not screen(saw, s, "w30")["S3"], "a conditioner that is the grid offset must fail S3"
    thin = wide.copy()
    thin["n_strikes"] = 2
    assert not screen(thin, s, "w30")["S4"], "a two-strike band must fail S4"
    log("  screens: each passes clean input and FAILS on the break that hits the scalar it reads")
    # window additivity and its break
    sw = pd.DataFrame(index=idx)
    sw["P1530"] = 4000.0 + rng.normal(0, 5, len(idx))
    sw["P1550"] = sw["P1530"] * (1 + rng.normal(0, 1e-3, len(idx)))
    sw["P1600"] = sw["P1550"] * (1 + rng.normal(0, 1e-3, len(idx)))
    sw["R30"] = 1e4 * np.log(sw["P1600"] / sw["P1530"])
    sw["R10"] = 1e4 * np.log(sw["P1600"] / sw["P1550"])
    sw["LEG1"] = 1e4 * np.log(sw["P1550"] / sw["P1530"])
    a = audit_window_additivity(sw)
    assert a["max_abs_deviation"] < ADDITIVITY_TOL_BP, a
    expect_raise(lambda: audit_additivity_broken(sw), "a one-bp slip in the first leg")
    same = sw.copy()
    same["R10"] = same["R30"]                      # the two windows collapsed into one column
    same["LEG1"] = 0.0
    expect_raise(lambda: audit_window_additivity(same), "the ten-minute window BEING the half-hour")
    log(f"  windows: R30 == LEG1 + R10 to {a['max_abs_deviation']:.1e}, and the slipped leg raises")
    # the control sets differ by exactly the leg that would sit inside the primary's window
    j = pd.DataFrame(index=idx)
    for c in ("ON", "DAY0", "MIDE", "F5", "LEG1"):
        j[c] = rng.normal(0, 20, len(idx))
    j["PING"] = rng.normal(0, 0.1, len(idx))
    j["sigma30_bp"] = 30.0
    j["sigma10_bp"] = 20.0
    c30, c10 = controls_for(j, "w30"), controls_for(j, "w10")
    assert "LEG1" not in c30 and "LEG1" in c10, (list(c30), list(c10))
    assert set(c10) - set(c30) == {"LEG1"}
    log("  controls: the 15:30-15:50 leg is a control for the ten-minute window and NOT for the half-hour")
    # the singularity guard, on the placebo cell that broke D614
    good = {"A": rng.normal(size=40), "B": rng.normal(size=40)}
    assert D614.audit_not_singular(good)
    expect_raise(lambda: D614.audit_not_singular({"A": good["A"], "SAME": good["A"].copy()}),
                 "two columns that are one variable")
    # by NAME, never by position (D614's W1)
    yy = rng.normal(size=60)
    cc = {"c1": rng.normal(size=60), "LADDER": rng.normal(size=60), "c3": rng.normal(size=60)}
    by_name = D614.coef_named(yy, cc, "LADDER")
    by_index = D614.coef_at_index(yy, cc, 0)
    assert abs(by_name - by_index) > 1e-12, "the positional read must differ, or the audit proves nothing"
    log("  mapping: the coefficient read BY NAME differs from the first column's, as it must")
    # declared outputs
    expect_raise(lambda: guard_outputs({k: 1 for k in REQUIRED_OUTPUTS[:-1]}), "a missing declared output")
    log(f"{SPEC} selftest: all audits pass and all raise on their breaks")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
    else:
        run()
