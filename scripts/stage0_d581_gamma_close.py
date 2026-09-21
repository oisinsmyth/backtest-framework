"""D581 STAGE 0 -- the gamma-conditioned close on ES: the discriminator. Design committed BEFORE this file (see SPEC).

    uv run python scripts/stage0_d581_gamma_close.py --selftest   # every audit passes a clean case and RAISES on a break
    uv run python scripts/stage0_d581_gamma_close.py --run        # 2016-01-04 .. 2023-12-29; no session, option row or quote from 2024-01-01 on

R2 = a + b*F5 + c*F5*F2 + d*F2, R2 the 15:30->16:00 return, F5 the 14:30->15:30 move, F2 = sign of carried dealer net gamma
from prior-close option OI under the stated convention (calls +, puts -), gamma at 15:30 ET with the settlement-implied vol;
predicted c < 0, NW t >= 2, rank >= 0.95 in the enumerated day-shift null of F2. Kill 3 (wrong sign, never flipped), the 0DTE
era split (T3), 0DTE days vs the rest (T4), the flip level (T5), the unsigned 0DTE volume build as a diagnostic (T6).
No cost, no book, no quote. Output data/stage0_d581_gamma_close.json.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from scipy.stats import norm

REPO = Path(__file__).resolve().parents[1]
FIX = REPO / "data" / "fixtures"
OPTS = FIX / "fut_es_options_eod.csv.gz"; ES_1M = FIX / "fut_ES_rth_1m.csv.gz"; STRIP = FIX / "fut_settle_strip.csv.gz"; SESSIONS = FIX / "fut_index_sessions.csv.gz"
OUT = REPO / "data" / "stage0_d581_gamma_close.json"
SPEC = "D581"
RESERVED_FROM = "2024-01-01"; IN_FROM = "2016-01-04"
MULT = 50.0; HOURS = 6.5; YEAR_HOURS = 252 * HOURS; NW_LAG = 5; SHIFT_MIN = 10; BOOT = 1000; SEED = 581
T_MOVE0, T_MOVE1, T_ENTRY, T_R1, T_R3, T_CLOSE = "14:30", "15:30", "15:30", "15:50", "15:45", "16:00"
ERA_SPLIT = "2022-01-01"; DAILIES_FROM = "2022-05-02"; IV_LO, IV_HI = 0.01, 4.0; MONEYNESS_MAX = 0.30
REQUIRED_OUTPUTS = ("spec", "windows", "sets", "premise", "audits", "T1", "T2", "T3", "T4", "T5", "T6", "beside", "predictions", "verdict", "timing_s")


def expect_raise(fn, what, log=print):
    try:
        fn()
    except AssertionError as e:
        log(f"    audit RAISES on {what}: {str(e)[:70]}"); return True
    raise AssertionError(f"audit did not raise on {what}")


def blk(obs, null):
    null = np.asarray(null, float); null = null[np.isfinite(null)]
    return {"observed": float(obs), "p05": float(np.percentile(null, 5)), "p50": float(np.percentile(null, 50)), "p95": float(np.percentile(null, 95)), "n": int(null.size),
            "pct_rank": float((null < obs).mean()), "above_p95": bool(obs > np.percentile(null, 95)), "below_p05": bool(obs < np.percentile(null, 5))}


# ------------------------------------------------------------------------------------------ Black-76, two implementations
def b76_gamma(F, K, sig, tau):
    """Black-76 gamma (rate 0), scipy's normal pdf. Vectorised."""
    F = np.asarray(F, float); K = np.asarray(K, float); sig = np.asarray(sig, float); tau = np.asarray(tau, float)
    d1 = (np.log(F / K) + 0.5 * sig * sig * tau) / (sig * np.sqrt(tau)); return norm.pdf(d1) / (F * sig * np.sqrt(tau))


def b76_gamma_hand(F, K, sig, tau):
    """Second implementation: the pdf written out."""
    d1 = (math.log(F / K) + 0.5 * sig * sig * tau) / (sig * math.sqrt(tau)); return math.exp(-0.5 * d1 * d1) / math.sqrt(2 * math.pi) / (F * sig * math.sqrt(tau))


def b76_price(F, K, sig, tau, right):
    d1 = (np.log(F / K) + 0.5 * sig * sig * tau) / (sig * np.sqrt(tau)); d2 = d1 - sig * np.sqrt(tau)
    return np.where(right == "C", F * norm.cdf(d1) - K * norm.cdf(d2), K * norm.cdf(-d2) - F * norm.cdf(-d1))


def implied_vol(price, F, K, tau, right, iters=60):
    """Vectorised bisection on [IV_LO, IV_HI]; nan where the price is outside the bracket."""
    lo = np.full(price.shape, IV_LO); hi = np.full(price.shape, IV_HI)
    ok = (b76_price(F, K, lo, tau, right) <= price) & (price <= b76_price(F, K, hi, tau, right))
    for _ in range(iters):
        mid = 0.5 * (lo + hi); below = b76_price(F, K, mid, tau, right) < price; lo = np.where(below, mid, lo); hi = np.where(below, hi, mid)
    return np.where(ok, 0.5 * (lo + hi), np.nan)


def audit_gamma():
    """Closed form: ATM, one year, 20 % vol, F = 100 -> gamma = pdf(0.1)/(100*0.2) ; the two implementations agree; break = a negated d1."""
    ref = norm.pdf(0.1) / (100 * 0.2); a = float(b76_gamma(100.0, 100.0, 0.2, 1.0)); b = b76_gamma_hand(100.0, 100.0, 0.2, 1.0)
    if not (abs(a - ref) < 1e-12 and abs(b - ref) < 1e-12):
        raise AssertionError(f"GAMMA AUDIT: {a} {b} vs {ref}")
    return ref


def audit_gamma_broken():
    ref = norm.pdf(0.1) / (100 * 0.2); wrong = norm.pdf(-0.1 - 0.1) / (100 * 0.2)   # d1 negated and shifted: not the closed form
    if not abs(wrong - ref) < 1e-12:
        raise AssertionError("GAMMA AUDIT: a negated d1 does not reproduce the closed form")


def audit_iv_roundtrip(shift=0.0):
    F, K, tau, sig = 5000.0, 4950.0, 5 / 252, 0.18; p = float(b76_price(F, K, sig, tau, np.array("P"))) + shift
    iv = float(implied_vol(np.array([p]), np.array([F]), np.array([K]), np.array([tau]), np.array(["P"]))[0])
    if not abs(iv - sig) < 1e-6:
        raise AssertionError(f"IV AUDIT: round trip {iv} vs {sig}")


# ------------------------------------------------------------------------------------------ the sessions and the gamma sum
def load_es(log):
    b = pd.read_csv(ES_1M, dtype={"day": str, "hhmm": str, "contract": str}, encoding="utf-8"); b = b[(b["day"] >= IN_FROM) & (b["day"] < RESERVED_FROM)]
    if b["day"].max() >= RESERVED_FROM:
        raise AssertionError("a reserved session leaked")
    close = b.pivot(index="day", columns="hhmm", values="close"); nb = b.groupby("day").size(); close = close[nb.reindex(close.index) >= 380]
    def P(hhmm):   # the close of the minute bar ENDING at hhmm = the bar starting one minute earlier; 16:00 is the 15:59 bar's close (D462)
        prev = (pd.Timestamp("2000-01-01 " + hhmm) - pd.Timedelta(minutes=1)).strftime("%H:%M"); return close[prev]
    s = pd.DataFrame({"P1430": P(T_MOVE0), "P1530": P(T_MOVE1), "P1550": P(T_R1), "P1545": P(T_R3), "P1600": P(T_CLOSE)}).dropna()
    s["F5"] = 1e4 * np.log(s["P1530"] / s["P1430"]); s["R2"] = 1e4 * np.log(s["P1600"] / s["P1530"]); s["R1"] = 1e4 * np.log(s["P1550"] / s["P1530"]); s["R3"] = 1e4 * np.log(s["P1600"] / s["P1545"])
    s["rROD"] = 1e4 * np.log(s["P1530"] / s["P1600"].shift(1))
    tr = np.log(close["15:59"] / close["09:30"]).abs() if "09:30" in close else None
    s["ATR20"] = (close.max(axis=1) - close.min(axis=1)).rolling(20, min_periods=10).mean().reindex(s.index)
    log(f"  ES sessions {s.index.min()} .. {s.index.max()} (last read, before {RESERVED_FROM}): {len(s)}")
    return s


def gamma_table(opts, es, strip, cal, log):
    """Per session: F1 (carried net GEX, $ per 1 % at 15:30), F4 (0DTE share), the flip level, F1b (0DTE volume build), counts."""
    strip = strip[strip["root"] == "ES"]; settle = strip.set_index(["ref", "contract"])["settle"]
    calx = {d: i for i, d in enumerate(cal)}; rows = {}
    for d, g in opts.groupby("session", sort=True):
        if d not in es.index or d not in calx:
            continue
        i = calx[d]; prev = cal[i - 1] if i > 0 else None
        Fprev = g["underlying"].map(lambda u: settle.get((prev, u), np.nan)) if prev else pd.Series(np.nan, index=g.index)
        F = float(es.loc[d, "P1530"]); K = g["strike"].to_numpy(float); right = g["right"].to_numpy(); oi = g["oi"].to_numpy(float)
        n_ahead = np.array([calx.get(e, i) - i for e in g["expiry_date"]]); same_day = n_ahead == 0
        tau_1530 = (n_ahead * HOURS + 0.5) / YEAR_HOURS                                                       # remaining trading time to the 16:00 expiry
        exp_ok = ~same_day | (g["expiry_hhmm"].to_numpy() >= T_ENTRY)                                          # a same-day expiry already past 15:30 (the AM quarterly) carries no gamma
        tau_settle = (n_ahead * HOURS + HOURS) / YEAR_HOURS                                                     # from the prior settlement to expiry
        px = g["settle"].to_numpy(float); Fp = Fprev.to_numpy(float); m = np.isfinite(px) & np.isfinite(Fp) & (np.abs(K / F - 1) < MONEYNESS_MAX) & exp_ok & (oi > 0)
        iv = np.full(len(g), np.nan); iv[m] = implied_vol(px[m], Fp[m], K[m], tau_settle[m], right[m]); ok = np.isfinite(iv)
        gam = np.zeros(len(g)); gam[ok] = b76_gamma(F, K[ok], iv[ok], tau_1530[ok])
        sgn = np.where(right == "C", 1.0, -1.0); gex = gam * sgn * oi * MULT * F * F * 0.01; absg = np.abs(gam * oi)
        f1 = float(gex[ok].sum()); f4 = float(absg[ok & same_day].sum() / absg[ok].sum()) if absg[ok].sum() > 0 else np.nan
        # the flip level: re-evaluate the sum on a +-5 % grid of the futures price
        grid = F * (1 + np.arange(-0.05, 0.0501, 0.001)); sums = np.array([(b76_gamma(x, K[ok], iv[ok], tau_1530[ok]) * sgn[ok] * oi[ok] * MULT * x * x * 0.01).sum() for x in grid])
        sc = np.flatnonzero(np.sign(sums[1:]) != np.sign(sums[:-1])); flip = float(grid[sc[np.argmin(np.abs(sc - len(grid) // 2))]]) if sc.size else np.nan
        v = g["vol_to_1530"].to_numpy(float); vb = ok & same_day & np.isfinite(v); f1b = float((gam[vb] * sgn[vb] * v[vb] * MULT * F * F * 0.01).sum()) if vb.any() else np.nan
        rows[d] = dict(F1=f1, F4=f4, flip=flip, F1b=f1b, n_options=int(len(g)), n_used=int(ok.sum()), n_no_iv=int((m & ~ok).sum()), has_0dte=bool((same_day & exp_ok).any()), abs_gamma_oi=float(absg[ok].sum()))
    t = pd.DataFrame.from_dict(rows, orient="index").sort_index(); log(f"  gamma table: {len(t)} sessions, options used per session median {t['n_used'].median():.0f}, no-IV median {t['n_no_iv'].median():.0f}, F1 < 0 on {float((t['F1'] < 0).mean()):.2f}")
    return t


def gamma_table_pandas_check(opts, es, strip, cal, days):
    """Second path for F1 on a few sessions: the same sum through a pandas groupby with a scalar loop -- never the vectorised path."""
    strip = strip[strip["root"] == "ES"].set_index(["ref", "contract"])["settle"]; calx = {d: i for i, d in enumerate(cal)}; out = {}
    for d in days:
        g = opts[opts["session"] == d]; i = calx[d]; prev = cal[i - 1]; F = float(es.loc[d, "P1530"]); tot = 0.0
        for r in g.itertuples():
            Fp = strip.get((prev, r.underlying), np.nan)
            if not (np.isfinite(r.settle) and np.isfinite(Fp) and abs(r.strike / F - 1) < MONEYNESS_MAX and r.oi > 0):
                continue
            n = calx.get(r.expiry_date, i) - i
            if n == 0 and r.expiry_hhmm < T_ENTRY:
                continue
            iv = float(implied_vol(np.array([r.settle]), np.array([Fp]), np.array([r.strike]), np.array([(n * HOURS + HOURS) / YEAR_HOURS]), np.array([r.right]))[0])
            if not np.isfinite(iv):
                continue
            tot += b76_gamma_hand(F, r.strike, iv, (n * HOURS + 0.5) / YEAR_HOURS) * (1 if r.right == "C" else -1) * r.oi * MULT * F * F * 0.01
        out[d] = tot
    return out


def audit_f1(a, b):
    for d in b:
        if not np.isclose(a[d], b[d], rtol=1e-9, atol=1e-6):
            raise AssertionError(f"F1 AUDIT: {d} {a[d]} vs {b[d]}")


# ------------------------------------------------------------------------------------------ the tests
def nw(y, X, lag=NW_LAG):
    res = sm.OLS(y, sm.add_constant(X)).fit(cov_type="HAC", cov_kwds={"maxlags": lag}); return res


def t1_fit(R2, F5, F2, lag=NW_LAG):
    ok = np.isfinite(R2) & np.isfinite(F5) & np.isfinite(F2); R2, F5, F2 = R2[ok], F5[ok], F2[ok]   # a first-session rROD or a missing window is NaN, never a row
    X = np.column_stack([F5, F5 * F2, F2]); res = nw(R2, X, lag); b, c, d = res.params[1:4]; tb, tc, td = res.tvalues[1:4]
    neg = F2 < 0; pos = F2 > 0
    bneg = float(np.polyfit(F5[neg], R2[neg], 1)[0]) if neg.sum() > 20 else np.nan; bpos = float(np.polyfit(F5[pos], R2[pos], 1)[0]) if pos.sum() > 20 else np.nan
    return {"b": float(b), "c": float(c), "d": float(d), "t_c": float(tc), "t_b": float(tb), "n": int(R2.size), "n_neg": int(neg.sum()), "n_pos": int(pos.sum()), "slope_neg": bneg, "slope_pos": bpos, "ordered": bool(np.isfinite(bneg) and np.isfinite(bpos) and bneg > bpos)}


def c_only(R2, F5, F2):
    X = sm.add_constant(np.column_stack([F5, F5 * F2, F2])); beta = np.linalg.lstsq(X, R2, rcond=None)[0]; return float(beta[2])


def shift_null(R2, F5, F2, kmin=SHIFT_MIN):
    N = R2.size; ks = np.arange(kmin, N - kmin + 1); vals = np.array([c_only(R2, F5, np.roll(F2, int(k))) for k in ks])
    if not np.isclose(c_only(R2, F5, np.roll(F2, 0)), c_only(R2, F5, F2)):
        raise AssertionError("shift null: zero offset does not reproduce")
    return vals


def t1_block(R2, F5, F2, weeks, rng, lag=NW_LAG):
    fit = t1_fit(R2, F5, F2, lag); null = shift_null(R2, F5, F2); fit["day_shift_null"] = blk(fit["c"], null)
    nullF5 = np.array([c_only(R2, np.roll(F5, int(k)), F2) for k in range(SHIFT_MIN, R2.size - SHIFT_MIN + 1)]); fit["f5_shift_null"] = blk(fit["c"], nullF5)
    uw = np.unique(weeks); groups = [np.flatnonzero(weeks == w) for w in uw]; boot = []
    for _ in range(BOOT):
        idx = np.concatenate([groups[i] for i in rng.integers(0, len(groups), len(groups))]); boot.append(c_only(R2[idx], F5[idx], F2[idx]))
    fit["c_se_week_block"] = float(np.std(boot)); return fit


def audit_sign_in_money(rng, flip=False):
    """Synthetic panel: negative-gamma sessions continue F5, positive-gamma sessions revert it -> c < 0; negated -> c > 0."""
    N = 1500; F5 = rng.normal(0, 30, N); F2 = np.where(rng.random(N) < 0.5, -1.0, 1.0); R2 = -0.3 * F2 * F5 + rng.normal(0, 20, N)
    c = c_only(R2, F5, -F2 if flip else F2)
    if not c < -0.1:
        raise AssertionError(f"SIGN AUDIT: c {c:+.3f} on a panel built to give c < 0")
    return c


def guard_outputs(res):
    missing = [k for k in REQUIRED_OUTPUTS if k not in res]
    if missing:
        raise AssertionError(f"REQUIRED_OUTPUTS missing: {missing}")


# ------------------------------------------------------------------------------------------ run
def run(log=print):
    t0 = time.time(); rng = np.random.default_rng(SEED)
    log(f"D581 STAGE 0 -- the gamma-conditioned close on ES; spec {SPEC}; nothing from {RESERVED_FROM} on is read; no cost, no book, no quote")
    audits = {"gamma_closed_form": audit_gamma(), "gamma_audit_raises": expect_raise(audit_gamma_broken, "a negated d1", log)}
    audit_iv_roundtrip(); audits["iv_roundtrip"] = True; audits["iv_audit_raises"] = expect_raise(lambda: audit_iv_roundtrip(0.25), "the price shifted a tick", log)
    audits["sign_in_money_c"] = audit_sign_in_money(rng); audits["sign_audit_raises"] = expect_raise(lambda: audit_sign_in_money(rng, True), "a negated regime label", log)
    es = load_es(log)
    opts = pd.read_csv(OPTS, dtype={"session": str, "raw_symbol": str, "family": str, "right": str, "expiry_date": str, "expiry_hhmm": str, "underlying": str, "oi_pub_et": str}, encoding="utf-8"); opts = opts[opts["session"] < RESERVED_FROM]
    strip = pd.read_csv(STRIP, dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8")
    sess = pd.read_csv(SESSIONS, dtype={"day": str, "contract": str, "root": str}, encoding="utf-8"); cal = np.array(sorted(sess[(sess["root"] == "ES") & (sess["bars"] >= 380)]["day"].unique()))
    windows = {"es_sessions": [es.index.min(), es.index.max()], "options_last_session_read": opts["session"].max(), "reserved_from": RESERVED_FROM}
    # OI keying audit on a known-answer session: the OI used on session d was published before d's 10:00 ET
    pub = pd.to_datetime(opts["oi_pub_et"]); sd = pd.to_datetime(opts["session"])
    def audit_oi_keying(shift_days=0):
        if not ((pub + pd.Timedelta(days=shift_days) < sd + pd.Timedelta(hours=10)).all()):
            raise AssertionError("OI KEYING: a row's OI was published after its session's entry")
    audit_oi_keying(); audits["oi_keying_rows"] = int(len(opts)); audits["oi_keying_raises"] = expect_raise(lambda: audit_oi_keying(1), "the OI series shifted a session later", log)
    G = gamma_table(opts, es, strip, cal, log)
    chk = sorted(rng.choice(G.index.to_numpy(), 4, replace=False)); second = gamma_table_pandas_check(opts, es, strip, cal, chk); audit_f1(G["F1"].to_dict(), second); audits["f1_second_path_sessions"] = chk
    audits["f1_audit_raises"] = expect_raise(lambda: audit_f1(G["F1"].to_dict(), {d: -v for d, v in second.items()}), "a negated second path", log)
    if np.allclose(np.nan_to_num(G["F1"]), np.nan_to_num(G["F1b"])):
        raise AssertionError("RIGHT QUANTITY: F1 and F1b are the same array")
    audits["right_quantity_f1_vs_f1b"] = True
    # ---- the panel ----
    P = es.join(G, how="inner"); P = P[np.isfinite(P["F1"]) & (P["F1"] != 0)]; P["F2"] = np.sign(P["F1"]); P["year"] = P.index.str[:4]
    iso = pd.to_datetime(pd.Series(P.index)).dt.isocalendar(); P["week"] = (iso["year"] * 100 + iso["week"]).to_numpy()
    sets = {"es_sessions": int(len(es)), "sessions_with_gamma": int(len(P)), "share_f2_negative": float((P["F2"] < 0).mean()), "sessions_with_0dte": int(P["has_0dte"].sum()), "options_used_median": float(P["n_used"].median()), "no_iv_median": float(P["n_no_iv"].median())}
    # ---- the premise's persistence, before any T-statistic ----
    f2 = P["F2"].to_numpy(); switches = int((f2[1:] != f2[:-1]).sum()); yrs = sorted(set(P["year"]))
    premise = {"f2_autocorrelation": float(np.corrcoef(f2[1:], f2[:-1])[0, 1]), "regime_switches": switches, "switches_per_year": float(switches / len(yrs)), "share_negative_by_year": {y: float((P.loc[P["year"] == y, "F2"] < 0).mean()) for y in yrs},
               "abs_f1_median_by_year_musd": {y: float(P.loc[P["year"] == y, "F1"].abs().median() / 1e6) for y in yrs}, "f4_0dte_share_median_by_year": {y: float(P.loc[P["year"] == y, "F4"].median()) for y in yrs},
               "n_eff_note": "a regime that switches every few sessions has n_eff in sessions; one that holds for months has it in regimes"}
    log(f"  premise: F2 autocorrelation {premise['f2_autocorrelation']:+.2f}, {switches} switches ({premise['switches_per_year']:.0f}/yr), negative share {sets['share_f2_negative']:.2f}; |F1| median by year ($m): " + " ".join(f"{y}:{v:.0f}" for y, v in premise["abs_f1_median_by_year_musd"].items()))
    R2 = P["R2"].to_numpy(); F5 = P["F5"].to_numpy(); F2 = P["F2"].to_numpy(); W = P["week"].to_numpy()
    # ---- T1 ----
    T1 = t1_block(R2, F5, F2, W, rng); T1["zero_offset_reproduces"] = True
    log(f"  T1: c {T1['c']:+.4f} (NW t {T1['t_c']:+.2f}, week-block SE {T1['c_se_week_block']:.4f}), b {T1['b']:+.3f}; slopes neg {T1['slope_neg']:+.3f} pos {T1['slope_pos']:+.3f} ordered {T1['ordered']}; "
        f"day-shift rank {T1['day_shift_null']['pct_rank']:.3f} (p05 {T1['day_shift_null']['p05']:+.4f} p95 {T1['day_shift_null']['p95']:+.4f}); F5-shift rank {T1['f5_shift_null']['pct_rank']:.3f}; n {T1['n']} (neg {T1['n_neg']}, pos {T1['n_pos']})")
    # ---- T2 scale ----
    a1 = P["F1"].abs().to_numpy(); ter = np.digitize(a1, np.quantile(a1, [1 / 3, 2 / 3])); conform = -F2 * np.sign(F5) * R2
    T2 = {"c_by_abs_f1_tercile": {int(t): {"c": c_only(R2[ter == t], F5[ter == t], F2[ter == t]), "n": int((ter == t).sum())} for t in range(3)}, "spearman_abs_f1_vs_conformity": float(stats.spearmanr(a1, conform).correlation)}
    T2["top_over_bottom"] = float(T2["c_by_abs_f1_tercile"][2]["c"] / T2["c_by_abs_f1_tercile"][0]["c"]) if T2["c_by_abs_f1_tercile"][0]["c"] != 0 else None
    log("  T2 c by |F1| tercile: " + " ".join(f"{t}:{v['c']:+.4f}(n{v['n']})" for t, v in T2["c_by_abs_f1_tercile"].items()) + f"; Spearman(|F1|, conformity) {T2['spearman_abs_f1_vs_conformity']:+.3f}")
    # ---- T3 the era split ----
    def sub(mask, label):
        if mask.sum() < 60:
            return {"n": int(mask.sum()), "note": "too few sessions"}
        if np.unique(F2[mask]).size < 2:
            return {"n": int(mask.sum()), "note": f"one regime sign only ({int(F2[mask][0])}); the interaction is not identified"}
        r = t1_block(R2[mask], F5[mask], F2[mask], W[mask], rng); return {k: r[k] for k in ("c", "t_c", "n", "slope_neg", "slope_pos", "ordered", "c_se_week_block")} | {"day_shift_rank": r["day_shift_null"]["pct_rank"], "day_shift_p05": r["day_shift_null"]["p05"]}
    idx = P.index.to_numpy(); T3 = {"2016_2021": sub(idx < ERA_SPLIT, "pre"), "2022_2023": sub(idx >= ERA_SPLIT, "post"), "2023_alone": sub(P["year"].to_numpy() == "2023", "2023"), "by_year": {y: sub(P["year"].to_numpy() == y, y) for y in yrs}}
    log("  T3: " + " | ".join(f"{k}: c {v.get('c', float('nan')):+.4f} t {v.get('t_c', float('nan')):+.2f} rank {v.get('day_shift_rank', float('nan')):.2f} n {v['n']}" for k, v in T3.items() if k != "by_year"))
    log("  T3 by year: " + " ".join(f"{y}:{v.get('c', float('nan')):+.3f}(r{v.get('day_shift_rank', float('nan')):.2f})" for y, v in T3["by_year"].items()))
    # ---- T4 0DTE days vs the rest ----
    h0 = P["has_0dte"].to_numpy(); pre = idx < ERA_SPLIT; T4 = {"0dte_sessions": sub(h0, "0dte"), "non_0dte_sessions": sub(~h0, "non"), "pre2022_0dte": sub(pre & h0, "pre0"), "pre2022_non_0dte": sub(pre & ~h0, "pren")}
    log("  T4: " + " | ".join(f"{k}: c {v.get('c', float('nan')):+.4f} t {v.get('t_c', float('nan')):+.2f} rank {v.get('day_shift_rank', float('nan')):.2f} n {v['n']}" for k, v in T4.items()))
    # ---- T5 the flip level: the regime is fragile near it (open question 3) ----
    fl = P["flip"].to_numpy(); okf = np.isfinite(fl); F3 = np.abs(P["P1530"].to_numpy() - fl) / P["ATR20"].to_numpy(); far = okf & (F3 >= np.nanmedian(F3[okf])) if okf.any() else np.zeros(len(P), bool)
    T5 = {"sessions_with_flip_in_5pct": int(okf.sum()), "abs_f3_median_atr": float(np.nanmedian(F3[okf])) if okf.any() else None,
          "near_flip": sub(okf & ~far, "near"), "far_from_flip": sub(far, "far"), "no_flip_in_5pct": sub(~okf, "none")}
    log(f"  T5: flip within 5 % on {T5['sessions_with_flip_in_5pct']} sessions (|F3| median {T5['abs_f3_median_atr']} ATR); c near {T5['near_flip'].get('c', float('nan')):+.4f} far {T5['far_from_flip'].get('c', float('nan')):+.4f} none {T5['no_flip_in_5pct'].get('c', float('nan')):+.4f}")
    # ---- T6 the unsigned 0DTE volume build ----
    f1b = P["F1b"].to_numpy(); ok6 = np.isfinite(f1b) & (f1b != 0); T6 = {"n": int(ok6.sum())}
    if ok6.sum() > 60:
        T6["f1b_alone"] = {k: v for k, v in t1_fit(R2[ok6], F5[ok6], np.sign(f1b[ok6])).items() if k in ("c", "t_c", "n")}; T6["f1_plus_f1b"] = {k: v for k, v in t1_fit(R2[ok6], F5[ok6], np.sign(P["F1"].to_numpy()[ok6] + f1b[ok6])).items() if k in ("c", "t_c", "n")}
        T6["sign_agreement_f1b_vs_f1"] = float(np.mean(np.sign(f1b[ok6]) == F2[ok6]))
    log(f"  T6: F1b on {T6['n']} sessions; c with F1b {T6.get('f1b_alone', {}).get('c', float('nan')):+.4f}, with F1+F1b {T6.get('f1_plus_f1b', {}).get('c', float('nan')):+.4f}; sign agreement {T6.get('sign_agreement_f1b_vs_f1', float('nan')):.2f}")
    # ---- beside ----
    tick_bp = 1e4 * 0.25 / float(P["P1530"].mean()); two = {}
    for lab, m in (("neg_up", (F2 < 0) & (F5 > 0)), ("neg_down", (F2 < 0) & (F5 < 0)), ("pos_up", (F2 > 0) & (F5 > 0)), ("pos_down", (F2 > 0) & (F5 < 0))):
        two[lab] = {"mean_R2_bp": float(R2[m].mean()), "n": int(m.sum()), "in_mes_ticks": float(R2[m].mean() / tick_bp)}
    ys = np.sort(conform); tr = int(0.01 * ys.size)
    beside = {"two_by_two": two, "mes_tick_bp": tick_bp, "conformity_mean_bp": float(conform.mean()), "conformity_trimmed": float(ys[tr:ys.size - tr].mean()), "conformity_ex_top1pct": float(ys[:ys.size - tr].mean()), "conformity_ex_bottom1pct": float(ys[tr:].mean()),
              "R1_fit": {k: v for k, v in t1_fit(P["R1"].to_numpy(), F5, F2).items() if k in ("c", "t_c")}, "R3_fit": {k: v for k, v in t1_fit(P["R3"].to_numpy(), F5, F2).items() if k in ("c", "t_c")},
              "rROD_beside": {k: v for k, v in t1_fit(R2, P["rROD"].to_numpy(), F2).items() if k in ("b", "c", "t_c")},
              "largest_abs_R2": [{"session": str(P.index[i]), "R2_bp": float(R2[i]), "F5_bp": float(F5[i]), "F2": int(F2[i])} for i in np.argsort(-np.abs(R2))[:10]],
              "dropped_by_year": {y: {"no_iv_median": float(P.loc[P["year"] == y, "n_no_iv"].median())} for y in yrs}}
    log("  2x2 mean R2 bp: " + " ".join(f"{k}:{v['mean_R2_bp']:+.2f}(n{v['n']})" for k, v in two.items()) + f"; R1 c {beside['R1_fit']['c']:+.4f} R3 c {beside['R3_fit']['c']:+.4f}; rROD b {beside['rROD_beside']['b']:+.3f}")
    # ---- predictions and the verdict ----
    t1_ok = bool(T1["c"] < 0 and T1["t_c"] <= -2 and T1["day_shift_null"]["below_p05"]); wrong = bool(T1["c"] > 0 and T1["day_shift_null"]["above_p95"])
    post_c, pre_c = T3["2022_2023"].get("c", np.nan), T3["2016_2021"].get("c", np.nan); stronger_post = bool(np.isfinite(post_c) and (not np.isfinite(pre_c) or post_c < pre_c))
    y23 = bool(T3["2023_alone"].get("c", 1) < 0 and T3["2023_alone"].get("day_shift_rank", 1) <= 0.10); lives_0dte = bool(T4["0dte_sessions"].get("c", 1) < 0 and not (T4["non_0dte_sessions"].get("c", 0) < 0 and T4["non_0dte_sessions"].get("day_shift_rank", 1) <= 0.05))
    preds = {"T1_c_negative_t_le_-2_below_p05": t1_ok, "T1_wrong_sign_above_p95": wrong, "T1_slopes_ordered": T1["ordered"], "T3_stronger_2022_2023": stronger_post, "T3_2023_alone_holds": y23, "T4_lives_on_0dte_sessions": lives_0dte, "T2_spearman_positive": bool(T2["spearman_abs_f1_vs_conformity"] > 0)}
    if wrong:
        verdict = "WRONG SIGN"
    elif not t1_ok:
        verdict = "NOT SUPPORTED"
    elif stronger_post and y23 and lives_0dte and T1["ordered"]:
        verdict = "SUPPORTED"
    else:
        verdict = "GENERIC"
    log("  predictions: " + "; ".join(f"{k} {v}" for k, v in preds.items())); log(f"  STAGE 0 VERDICT: {verdict}")
    res = {"spec": SPEC, "windows": windows, "sets": sets, "premise": premise, "audits": audits, "T1": T1, "T2": T2, "T3": T3, "T4": T4, "T5": T5, "T6": T6, "beside": beside, "predictions": preds, "verdict": verdict, "timing_s": round(time.time() - t0, 1),
           "construction": {"convention": "calls +, puts - (dealers long calls, short puts)", "gamma_at": "15:30 ET, P(15:30), settlement-implied vol from the prior session, rate 0, tau = remaining trading time to the 16:00 expiry", "moneyness_max": MONEYNESS_MAX, "nw_lag": NW_LAG, "shift_min": SHIFT_MIN, "boot": BOOT, "era_split": ERA_SPLIT}}
    guard_outputs(res); expect_raise(lambda: guard_outputs({k: v for k, v in res.items() if k != "T1"}), "a missing declared output", log)
    OUT.write_text(json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)), encoding="utf-8"); log(f"  wrote {OUT.relative_to(REPO)} in {res['timing_s']} s")
    return 0


def selftest(log=print):
    rng = np.random.default_rng(2)
    audit_gamma(); log("  gamma closed form and two implementations agree"); expect_raise(audit_gamma_broken, "a negated d1", log)
    audit_iv_roundtrip(); log("  IV round trip passes"); expect_raise(lambda: audit_iv_roundtrip(0.25), "the price shifted a tick", log)
    c = audit_sign_in_money(rng); log(f"  sign in money: c {c:+.3f} on the synthetic panel"); expect_raise(lambda: audit_sign_in_money(rng, True), "a negated regime label", log)
    N = 1200; F5 = rng.normal(0, 30, N); F2 = np.where(rng.random(N) < 0.5, -1.0, 1.0); R2 = -0.3 * F2 * F5 + rng.normal(0, 20, N); W = np.arange(N) // 5
    r = t1_block(R2, F5, F2, W, rng); assert r["c"] < -0.2 and r["day_shift_null"]["below_p05"] and r["ordered"], r
    flat = t1_block(rng.normal(0, 20, N), F5, F2, W, rng); assert not flat["day_shift_null"]["below_p05"] or abs(flat["c"]) < 0.1
    log(f"  T1 on a synthetic regime: c {r['c']:+.3f} rank {r['day_shift_null']['pct_rank']:.3f}; on noise c {flat['c']:+.3f} rank {flat['day_shift_null']['pct_rank']:.2f}")
    expect_raise(lambda: audit_f1({"a": 1.0}, {"a": -1.0}), "a negated second path", log); expect_raise(lambda: guard_outputs({"spec": 1}), "missing outputs", log)
    log("  selftest: every audit passes its clean case and raises on its break"); return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--selftest", action="store_true"); ap.add_argument("--run", action="store_true"); a = ap.parse_args()
    sys.exit(selftest() if a.selftest else run() if a.run else 1)
