"""D583 STAGE 0 -- basis momentum's M7: the quarter-end reporting calendar. Design committed BEFORE this file (see SPEC).

    uv run python scripts/stage0_d583_bm_quarter_end.py --selftest   # every audit passes a clean case and RAISES on a break
    uv run python scripts/stage0_d583_bm_quarter_end.py --run        # 2011-07 .. 2023-12-29; no session from 2024-01-01 on

The D564 primary cell (EW High4/Low4, the formation amendment) rebuilt by D564's own functions and harnessed to its
artifact to 1e-9; then the calendar: T1 the 10-session PRE window into each quarter-end against the 63 window
offsets within the quarter; T1b the quarter-end PRE against the other month-ends' PRE, against the 495 four-month
subsets; T2 year-end over quarter-end; T3 the persistence of the monthly curve disturbance after quarter-end months;
T4 by year and era; T5 the POST window and the roll-settlement session. No cost, no construction, no reserved read.
Output data/stage0_d583_bm_quarter_end.json.
"""
from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s); sys.modules[name] = m; s.loader.exec_module(m); return m


R64 = _load("d564", "run_d564_basis_momentum.py"); R61, R56, R55, R57 = R64.R61, R64.R56, R64.R55, R64.R57
OUT = REPO / "data" / "stage0_d583_bm_quarter_end.json"; ART_D564 = REPO / "data" / "d564_basis_momentum.json"
SPEC = "D583 (design commit 00100c5)"
CM = R64.CM; FFILL = R64.FFILL_FORMATION; PRIMARY = R55.PRIMARY; LONG = R55.LONG; RESERVED_FROM = R55.RESERVED_FROM
PRE = 10; POST = 5; QUARTER_MONTHS = (3, 6, 9, 12); OFFSETS = np.arange(-31, 32); PROFILE = np.arange(-30, 16); BOOT = 2000; SEED = 583
REQUIRED_OUTPUTS = ("spec", "windows", "harness", "audits", "sets", "T1", "T1b", "T2", "T3", "T4", "T5", "beside", "predictions", "verdict", "timing_s")


def expect_raise(fn, what, log=print):
    try:
        fn()
    except AssertionError as e:
        log(f"    audit RAISES on {what}: {str(e)[:70]}"); return True
    raise AssertionError(f"audit did not raise on {what}")


def blk(obs, null):
    null = np.asarray(null, float); null = null[np.isfinite(null)]
    return {"observed": float(obs), "p05": float(np.percentile(null, 5)), "p50": float(np.percentile(null, 50)), "p95": float(np.percentile(null, 95)), "n": int(null.size), "pct_rank": float((null < obs).mean()), "above_p95": bool(obs > np.percentile(null, 95))}


# ------------------------------------------------------------------------------------------ the calendar
def month_end_index(days):
    """Index of the last session of each calendar month, and each one's month number. The runner's arithmetic on the day strings."""
    ym = np.array([d[:7] for d in days]); last = np.flatnonzero(np.r_[ym[1:] != ym[:-1], True]); return last, np.array([int(days[i][5:7]) for i in last])


def month_end_index_pandas(days):
    """Second path: pandas groupby on the year-month, taking each group's last positional index."""
    s = pd.Series(np.arange(len(days)), index=pd.to_datetime(pd.Series(days))); last = s.groupby([s.index.year, s.index.month]).max().to_numpy(); return last, np.array([int(str(days[i])[5:7]) for i in last])


def audit_calendar(a, b):
    if a[0].shape != b[0].shape or not (np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1])):
        raise AssertionError("CALENDAR AUDIT: the two paths disagree on the month-end sessions")


def window_mask(T, anchors, k, width_before, width_after):
    """Sessions in [anchor + k - width_before + 1, anchor + k + width_after] for every anchor; PRE is (k=0, 10, 0), POST is (k=0, 0, 5)."""
    m = np.zeros(T, bool)
    for a in anchors:
        lo, hi = a + k - width_before + 1, a + k + width_after
        if 0 <= lo and hi < T:
            m[lo:hi + 1] = True
    return m


def delta(r, valid, mask):
    """mean on the mask minus mean off it, both within `valid` sessions, in bp/day."""
    a = r[valid & mask]; b = r[valid & ~mask]
    return 1e4 * (a.mean() - b.mean()) if a.size and b.size else np.nan


def t1_block(r, valid, anchors, T):
    obs = delta(r, valid, window_mask(T, anchors, 0, PRE, 0)); vals = np.array([delta(r, valid, window_mask(T, anchors, int(k), PRE, 0)) for k in OFFSETS])
    others = vals[OFFSETS != 0]; non = vals[np.abs(OFFSETS) >= PRE]
    prof = np.array([1e4 * r[valid & window_mask(T, anchors, int(k), 1, 0)].mean() for k in PROFILE])
    return {"delta_pre_bp": float(obs), "rank_in_63": float((others < obs).mean()), "null_p05": float(np.nanpercentile(others, 5)), "null_p50": float(np.nanpercentile(others, 50)), "null_p95": float(np.nanpercentile(others, 95)),
            "rank_non_overlapping": float((non < obs).mean()), "n_non_overlapping": int(non.size), "zero_offset_reproduces": bool(np.isclose(vals[OFFSETS == 0][0], obs)),
            "profile_minus30_to_plus15_bp": [float(x) for x in prof], "profile_peak_session": int(PROFILE[int(np.nanargmax(prof))]), "peak_inside_pre": bool(-PRE < PROFILE[int(np.nanargmax(prof))] <= 0),
            "n_pre_sessions": int((valid & window_mask(T, anchors, 0, PRE, 0)).sum()), "n_events": int(len(anchors))}


def quarter_block_se(r, valid, anchors, T, rng):
    """Resample quarters (the anchors) with replacement; ΔPRE on each resample; its std."""
    anchors = np.asarray(anchors); out = []
    for _ in range(BOOT):
        pick = rng.choice(anchors, anchors.size, replace=True); m = window_mask(T, np.unique(pick), 0, PRE, 0)
        w = np.zeros(T);
        for a in pick:
            lo = a - PRE + 1
            if lo >= 0:
                w[lo:a + 1] += 1
        num = (r * w)[valid].sum(); den = w[valid].sum(); off = r[valid & ~m]
        out.append(1e4 * (num / den - off.mean()) if den and off.size else np.nan)
    return float(np.nanstd(out))


def t1b_block(r, valid, me_ix, me_month, T):
    """ΔQ = quarter-end PRE mean − other month-end PRE mean; null = every 4-of-12 month subset."""
    def dq(months):
        q = [i for i, m in zip(me_ix, me_month) if m in months]; o = [i for i, m in zip(me_ix, me_month) if m not in months]
        a = r[valid & window_mask(T, q, 0, PRE, 0)]; b = r[valid & window_mask(T, o, 0, PRE, 0)]; return 1e4 * (a.mean() - b.mean())
    obs = dq(set(QUARTER_MONTHS)); subs = [s for s in itertools.combinations(range(1, 13), 4)]; vals = np.array([dq(set(s)) for s in subs])
    others = vals[[s != QUARTER_MONTHS for s in subs]]
    return {"delta_q_bp": float(obs), "rank_in_495": float((others < obs).mean()), "null_p50": float(np.percentile(others, 50)), "null_p95": float(np.percentile(others, 95)), "n_subsets": int(len(subs)), "subset_reproduces": bool(np.isclose(vals[subs.index(QUARTER_MONTHS)], obs)),
            "top5_subsets": [(list(subs[i]), float(vals[i])) for i in np.argsort(-vals)[:5]]}


def audit_sign_in_money(rng, flip=False):
    T = 3000; anchors = np.arange(62, T - 40, 63); r = np.zeros(T); m = window_mask(T, anchors, 0, PRE, 0); r[m] = 0.001; r += rng.normal(0, 1e-5, T)
    if flip:
        r = -r
    b = t1_block(r, np.ones(T, bool), anchors, T)
    if not (b["delta_pre_bp"] > 5 and b["rank_in_63"] == 1.0):
        raise AssertionError(f"SIGN AUDIT: delta {b['delta_pre_bp']:+.2f} rank {b['rank_in_63']:.2f} on a series built to give a positive PRE")
    return b["delta_pre_bp"]


def audit_right_quantity(pre, post):
    if np.array_equal(pre, post) or (pre & post).any():
        raise AssertionError("RIGHT-QUANTITY AUDIT: PRE and POST masks are not disjoint and distinct")


def guard_outputs(res):
    missing = [k for k in REQUIRED_OUTPUTS if k not in res]
    if missing:
        raise AssertionError(f"REQUIRED_OUTPUTS missing: {missing}")


# ------------------------------------------------------------------------------------------ run
def build_book(log):
    df = R55.load_fixture()
    if (df["day"] >= RESERVED_FROM).any():
        raise AssertionError("reserved slice present")
    live_start = R55.live_start_by_rule(df); gfull = R55.build_grids(df, live_start); days = gfull["days"]; T = len(days); me = R55.month_ends(days); K = len(me)
    strip = pd.read_csv(R56.STRIP, dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8"); strip = strip[(strip["ref"] < RESERVED_FROM) & strip["root"].isin(CM)]
    t0 = time.time(); tables = R64.strip_tables(strip, days, CM); n = len(CM)
    def book(ffill):
        ns = R64.nearby_series(tables, CM, days, me, ffill=ffill); BM, mom, elig = R64.signals_at_month_ends(ns["R1"], ns["R2"], ns["stale"])
        span = np.zeros((n, T), dtype=bool)
        for i in range(n):
            ix = np.flatnonzero(ns["live"][i])
            if ix.size:
                span[i, ix[0]:ix[-1] + 1] = True
        member, diag = R64.membership_fixed(BM, elig, CM, R64.N_LEG, R64.MIN_ELIGIBLE); held = R55.hold_from_month_ends(member.astype(float), me, T, span)
        first = next((k for k in range(K) if elig[:, k].sum() >= R64.MIN_ELIGIBLE), None)
        return dict(x=R55.book_return(held, ns["r1d"]), ns=ns, BM=BM, elig=elig, member=member, held=held, first_me=first)
    b = book(FFILL); b0 = book(1)
    member_t, _ = R57.membership_at_month_ends(np.where(b["elig"], b["BM"], np.nan), CM); span_t = np.abs(b["held"]).sum(0) > 0
    log(f"  book rebuilt in {time.time() - t0:.0f}s: {T} sessions {days[0]}..{days[-1]} (nothing from {RESERVED_FROM}); first month-end with >= {R64.MIN_ELIGIBLE} eligible {days[me[b['first_me']]]}")
    return days, T, me, b, b0, member_t, gfull


def run(log=print):
    t0 = time.time(); rng = np.random.default_rng(SEED)
    log(f"D583 STAGE 0 -- basis momentum's M7, the quarter-end reporting calendar; spec {SPEC}; no session from {RESERVED_FROM} on; no cost, no construction")
    days, T, me, b, b0, member_t, gfull = build_book(log); x = b["x"]; wP = R55.window_mask(days, *PRIMARY)
    # ---- harness ----
    art = json.loads(ART_D564.read_text(encoding="utf-8")); ref = art["cells"]["EW High4/Low4"]["gross"]["sharpe"]
    def audit_harness(series):
        s = R55.sharpe(series[wP])
        if abs(s - ref) > 1e-9:
            raise AssertionError(f"HARNESS: rebuilt {s} vs artifact {ref}")
        return s
    sh = audit_harness(x); audits = {"harness_raises": expect_raise(lambda: audit_harness(np.roll(x, 1)), "the series rolled one session", log)}
    harness = {"primary_sharpe_rebuilt": float(sh), "d564_artifact": float(ref), "tolerance": 1e-9}
    log(f"  harness: PRIMARY gross Sharpe {sh:+.6f} = D564 artifact {ref:+.6f}")
    # ---- the calendar ----
    me_ix, me_month = month_end_index(days); audit_calendar((me_ix, me_month), month_end_index_pandas(days)); audits["calendar_second_path_month_ends"] = int(me_ix.size)
    audits["calendar_audit_raises"] = expect_raise(lambda: audit_calendar((me_ix + 1, me_month), month_end_index_pandas(days)), "the mask shifted one session", log)
    first_session = me[b["first_me"]] + 1                                              # the first positioned session
    valid = (np.arange(T) >= first_session) & (np.abs(b["held"]).sum(0) > 0)          # positioned sessions only
    q_anchors = np.array([i for i, m in zip(me_ix, me_month) if m in QUARTER_MONTHS and i >= first_session]); y_anchors = np.array([i for i, m in zip(me_ix, me_month) if m == 12 and i >= first_session])
    o_anchors = np.array([i for i, m in zip(me_ix, me_month) if m not in QUARTER_MONTHS and i >= first_session])
    pre = window_mask(T, q_anchors, 0, PRE, 0); post = window_mask(T, q_anchors, 0, 0, POST); audit_right_quantity(pre, post); audits["right_quantity_pre_vs_post"] = True
    audits["right_quantity_raises"] = expect_raise(lambda: audit_right_quantity(pre, pre), "the same mask twice", log)
    audits["sign_in_money_delta_bp"] = audit_sign_in_money(rng); audits["sign_audit_raises"] = expect_raise(lambda: audit_sign_in_money(rng, True), "a negated series", log)
    sets = {"positioned_sessions": int(valid.sum()), "quarter_ends": int(q_anchors.size), "year_ends": int(y_anchors.size), "other_month_ends": int(o_anchors.size), "pre_sessions": int((valid & pre).sum()), "post_sessions": int((valid & post).sum()),
            "first_positioned_session": str(days[first_session]), "last_session": str(days[-1]), "book_bp_per_day_long": float(1e4 * x[valid].mean()), "book_bp_per_day_primary": float(1e4 * x[valid & wP].mean())}
    log(f"  sets: {sets['positioned_sessions']} positioned sessions {sets['first_positioned_session']}..{sets['last_session']}; {sets['quarter_ends']} quarter-ends ({sets['year_ends']} year-ends); book {sets['book_bp_per_day_long']:+.2f} bp/day (PRIMARY {sets['book_bp_per_day_primary']:+.2f})")
    # ---- T1 ----
    T1 = t1_block(x, valid, q_anchors, T); T1["se_quarter_block"] = quarter_block_se(x, valid, q_anchors, T, rng); T1["t"] = T1["delta_pre_bp"] / T1["se_quarter_block"] if T1["se_quarter_block"] else None
    if not T1["zero_offset_reproduces"]:
        raise AssertionError("placement null: zero offset does not reproduce")
    log(f"  T1: dPRE {T1['delta_pre_bp']:+.2f} bp/day (SE {T1['se_quarter_block']:.2f}, t {T1['t']:+.2f}), rank {T1['rank_in_63']:.3f} in 63 offsets (p05 {T1['null_p05']:+.2f} p50 {T1['null_p50']:+.2f} p95 {T1['null_p95']:+.2f}), non-overlapping rank {T1['rank_non_overlapping']:.3f}; "
        f"profile peak at session {T1['profile_peak_session']:+d} (inside PRE {T1['peak_inside_pre']}); PRE sessions {T1['n_pre_sessions']}")
    # ---- T1b ----
    T1b = t1b_block(x, valid, me_ix[me_ix >= first_session], me_month[me_ix >= first_session], T)
    log(f"  T1b: dQ {T1b['delta_q_bp']:+.2f} bp/day, rank {T1b['rank_in_495']:.3f} in 495 four-month subsets (p50 {T1b['null_p50']:+.2f} p95 {T1b['null_p95']:+.2f}); top subsets {T1b['top5_subsets'][:3]}")
    # ---- T2 year-end over quarter-end ----
    def pre_mean(anchors):
        m = valid & window_mask(T, np.asarray(anchors), 0, PRE, 0); return 1e4 * x[m].mean() if m.any() else np.nan
    dec = pre_mean(y_anchors); q3 = pre_mean([a for a, m in zip(me_ix, me_month) if m in (3, 6, 9) and a >= first_session]); years = sorted({days[a][:4] for a in q_anchors})
    per_year = {}
    for yv in years:
        d_ = [a for a in y_anchors if days[a][:4] == yv]; o_ = [a for a, m in zip(me_ix, me_month) if m in (3, 6, 9) and a >= first_session and days[a][:4] == yv]
        if d_ and len(o_) == 3:
            per_year[yv] = {"dec_pre_bp": float(pre_mean(d_)), "other_q_pre_bp": float(pre_mean(o_))}
    n_dec_wins = sum(v["dec_pre_bp"] > v["other_q_pre_bp"] for v in per_year.values())
    T2 = {"december_pre_bp": float(dec), "mar_jun_sep_pre_bp": float(q3), "december_above": bool(dec > q3), "years_with_december_above": int(n_dec_wins), "years_compared": len(per_year), "per_year": per_year}
    log(f"  T2: December PRE {dec:+.2f} vs Mar/Jun/Sep PRE {q3:+.2f} bp/day; December above in {n_dec_wins} of {len(per_year)} years")
    # ---- T3 persistence of the monthly disturbance ----
    R1, R2 = b["ns"]["R1"], b["ns"]["R2"]; d = R1 - R2; K = d.shape[1]; me_m = np.array([int(days[i][5:7]) for i in me])
    rows = []
    for k in range(b["first_me"], K - 1):
        ok = np.isfinite(d[:, k]) & np.isfinite(d[:, k + 1]) & b["elig"][:, k]
        if ok.sum() >= 8:
            rows.append((k, me_m[k] in QUARTER_MONTHS, float(np.corrcoef(d[ok, k], d[ok, k + 1])[0, 1]), int(days[me[k]][:4])))
    cq = np.array([c for _, q, c, _ in rows if q]); co = np.array([c for _, q, c, _ in rows if not q]); yrs3 = np.array([y for *_, y in rows]); qf = np.array([q for _, q, _, _ in rows]); cc = np.array([c for _, _, c, _ in rows])
    bt = []
    uy = np.unique(yrs3)
    for _ in range(BOOT):
        pick = rng.choice(uy, uy.size, replace=True); sel = np.concatenate([np.flatnonzero(yrs3 == y) for y in pick]); bt.append(cc[sel][qf[sel]].mean() - cc[sel][~qf[sel]].mean())
    T3 = {"corr_next_month_after_quarter_end_months": float(cq.mean()), "after_other_months": float(co.mean()), "difference": float(cq.mean() - co.mean()), "se_year_block": float(np.std(bt)), "n_quarter_months": int(cq.size), "n_other_months": int(co.size)}
    log(f"  T3: cross-root persistence of d_m into d_m+1: after quarter-end months {T3['corr_next_month_after_quarter_end_months']:+.3f} vs others {T3['after_other_months']:+.3f} (diff {T3['difference']:+.3f}, SE {T3['se_year_block']:.3f})")
    # ---- T4 by year and era ----
    yr = np.array([d_[:4] for d_ in days]); T4 = {"by_year": {}}
    for yv in years:
        vy = valid & (yr == yv); qa = [a for a in q_anchors if days[a][:4] == yv]
        if vy.sum() > 100 and len(qa) == 4:
            T4["by_year"][yv] = {"delta_pre_bp": float(delta(x, vy, window_mask(T, qa, 0, PRE, 0))), "book_bp_per_day": float(1e4 * x[vy].mean())}
    full = {y: v for y, v in T4["by_year"].items()}; T4["years_positive"] = int(sum(v["delta_pre_bp"] > 0 for v in full.values())); T4["years_counted"] = len(full)
    for lab, lo, hi in (("2011_2015", "2011", "2015"), ("2016_2023", "2016", "2023")):
        ve = valid & (yr >= lo) & (yr <= hi); qa = [a for a in q_anchors if lo <= days[a][:4] <= hi]; blkx = t1_block(x, ve, np.array(qa), T)
        T4[lab] = {"delta_pre_bp": blkx["delta_pre_bp"], "rank_in_63": blkx["rank_in_63"], "n_events": blkx["n_events"], "book_bp_per_day": float(1e4 * x[ve].mean())}
    log("  T4 by year dPRE (book): " + " ".join(f"{y}:{v['delta_pre_bp']:+.1f}({v['book_bp_per_day']:+.1f})" for y, v in full.items()) + f"; positive {T4['years_positive']}/{T4['years_counted']}; eras " + " | ".join(f"{k}: {v['delta_pre_bp']:+.2f} rank {v['rank_in_63']:.2f} n {v['n_events']}" for k, v in T4.items() if k.startswith("20")))
    # ---- T5 ----
    T5 = {"delta_post_bp": float(delta(x, valid, post)), "delta_pre_ex_last_session_bp": float(delta(x, valid, window_mask(T, q_anchors - 1, 0, PRE - 1, 0))), "delta_pre_other_month_ends_bp": float(delta(x, valid, window_mask(T, o_anchors, 0, PRE, 0))),
          "profile_other_month_ends": [float(1e4 * x[valid & window_mask(T, o_anchors, int(k), 1, 0)].mean()) for k in PROFILE]}
    log(f"  T5: dPOST {T5['delta_post_bp']:+.2f}; dPRE without the settlement session {T5['delta_pre_ex_last_session_bp']:+.2f}; dPRE at the other month-ends {T5['delta_pre_other_month_ends_bp']:+.2f} bp/day")
    # ---- beside ----
    xs = np.sort(1e4 * x[valid & pre]); tr = int(0.01 * xs.size); top = np.argsort(-np.abs(np.where(valid & pre, x, 0)))[:10]
    b0x = b0["x"]; v0 = valid & (np.abs(b0["held"]).sum(0) > 0); held_t = R55.hold_from_month_ends(member_t.astype(float), me, T, np.abs(b["held"]).sum(0)[None, :].repeat(len(CM), 0) > 0); xt = R55.book_return(held_t, b["ns"]["r1d"])
    beside = {"pre_mean_bp": float(xs.mean()), "pre_median_bp": float(np.median(xs)), "pre_trimmed_bp": float(xs[tr:xs.size - tr].mean()), "pre_ex_top1pct_bp": float(xs[:xs.size - tr].mean()), "pre_ex_bottom1pct_bp": float(xs[tr:].mean()),
              "largest_pre_sessions": [{"session": str(days[i]), "r_bp": float(1e4 * x[i])} for i in top], "as_preregistered_ffill1": {k: v for k, v in t1_block(b0x, v0, q_anchors, T).items() if k in ("delta_pre_bp", "rank_in_63", "rank_non_overlapping", "profile_peak_session")},
              "terciles_cell": {k: v for k, v in t1_block(xt, valid & (np.abs(held_t).sum(0) > 0), q_anchors, T).items() if k in ("delta_pre_bp", "rank_in_63", "rank_non_overlapping", "profile_peak_session")}, "december_profile": [float(1e4 * x[valid & window_mask(T, y_anchors, int(k), 1, 0)].mean()) for k in PROFILE]}
    log(f"  beside: PRE mean {beside['pre_mean_bp']:+.2f} median {beside['pre_median_bp']:+.2f} trimmed {beside['pre_trimmed_bp']:+.2f} ex-top {beside['pre_ex_top1pct_bp']:+.2f} ex-bottom {beside['pre_ex_bottom1pct_bp']:+.2f}; as-pre-registered dPRE {beside['as_preregistered_ffill1']['delta_pre_bp']:+.2f} rank {beside['as_preregistered_ffill1']['rank_in_63']:.2f}; terciles dPRE {beside['terciles_cell']['delta_pre_bp']:+.2f} rank {beside['terciles_cell']['rank_in_63']:.2f}")
    # ---- predictions and the verdict ----
    preds = {"T1_dpre_positive_rank_ge_0.95": bool(T1["delta_pre_bp"] > 0 and T1["rank_in_63"] >= 0.95), "T1_peak_inside_pre": T1["peak_inside_pre"], "T1b_dq_positive_rank_ge_0.95": bool(T1b["delta_q_bp"] > 0 and T1b["rank_in_495"] >= 0.95),
             "T2_december_above_pooled": T2["december_above"], "T2_december_above_ge_8_of_12_years": bool(T2["years_with_december_above"] >= 8), "T3_persistence_higher_after_quarter_ends": bool(T3["difference"] > 0),
             "T4_ge_8_of_12_years_positive": bool(T4["years_positive"] >= 8), "T4_post2016_not_weaker": bool(T4["2016_2023"]["delta_pre_bp"] >= T4["2011_2015"]["delta_pre_bp"])}
    if preds["T1_dpre_positive_rank_ge_0.95"] and preds["T1b_dq_positive_rank_ge_0.95"]:
        verdict = "SUPPORTED" if (preds["T4_ge_8_of_12_years_positive"] and preds["T2_december_above_pooled"] and preds["T2_december_above_ge_8_of_12_years"]) else "PARTIAL"
    else:
        verdict = "NOT SUPPORTED"
    log("  predictions: " + "; ".join(f"{k} {v}" for k, v in preds.items())); log(f"  STAGE 0 VERDICT: {verdict}")
    res = {"spec": SPEC, "windows": {"long": [str(days[first_session]), str(days[-1])], "primary": list(PRIMARY), "reserved_from": RESERVED_FROM}, "harness": harness, "audits": audits, "sets": sets, "T1": T1, "T1b": T1b, "T2": T2, "T3": T3, "T4": T4, "T5": T5, "beside": beside,
           "predictions": preds, "verdict": verdict, "timing_s": round(time.time() - t0, 1), "construction": {"cell": "EW High4/Low4, FFILL_FORMATION 5 (D564 primary as D574 carried it)", "pre_window": PRE, "post_window": POST, "quarter_months": QUARTER_MONTHS, "offsets": [-31, 31], "subsets": 495, "boot": BOOT}}
    guard_outputs(res); expect_raise(lambda: guard_outputs({k: v for k, v in res.items() if k != "T1"}), "a missing declared output", log)
    OUT.write_text(json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)), encoding="utf-8"); log(f"  wrote {OUT.relative_to(REPO)} in {res['timing_s']} s"); return 0


def selftest(log=print):
    rng = np.random.default_rng(3)
    days = np.array([str(d.date()) for d in pd.bdate_range("2015-01-01", "2018-12-31")]); a = month_end_index(days); b = month_end_index_pandas(days); audit_calendar(a, b)
    assert days[a[0][2]] == "2015-03-31" and a[1][2] == 3 and days[a[0][-1]] == "2018-12-31", (days[a[0][:3]], a[1][:3])
    expect_raise(lambda: audit_calendar((a[0] + 1, a[1]), b), "the mask shifted one session", log); log("  calendar: two paths agree on 48 month-ends")
    d_ = audit_sign_in_money(rng); log(f"  sign in money: dPRE {d_:+.1f} bp on a synthetic series"); expect_raise(lambda: audit_sign_in_money(rng, True), "a negated series", log)
    T = 3000; anchors = np.arange(62, T - 40, 63); pre = window_mask(T, anchors, 0, PRE, 0); post = window_mask(T, anchors, 0, 0, POST); audit_right_quantity(pre, post); expect_raise(lambda: audit_right_quantity(pre, pre), "the same mask twice", log)
    assert pre.sum() == PRE * anchors.size and post.sum() == POST * anchors.size and pre[anchors].all() and not post[anchors].any()
    # T1b on a synthetic year: month-ends every 21 sessions; +x before months 3,6,9,12 only -> rank 1.0 among the 495 subsets
    T2_ = 21 * 12 * 6; days2 = np.array([str(d.date()) for d in pd.bdate_range("2012-01-02", periods=T2_)]); me_ix, me_m = month_end_index(days2); r = rng.normal(0, 1e-5, T2_)
    for i, m in zip(me_ix, me_m):
        if m in QUARTER_MONTHS and i >= PRE:
            r[i - PRE + 1:i + 1] += 0.001
    tb = t1b_block(r, np.ones(T2_, bool), me_ix, me_m, T2_); assert tb["rank_in_495"] == 1.0 and tb["subset_reproduces"], tb
    flat = t1b_block(rng.normal(0, 1e-4, T2_), np.ones(T2_, bool), me_ix, me_m, T2_); assert flat["rank_in_495"] < 0.95
    log(f"  T1b on a synthetic quarter-end effect: rank {tb['rank_in_495']:.2f}; on noise {flat['rank_in_495']:.2f}")
    expect_raise(lambda: guard_outputs({"spec": 1}), "missing outputs", log); log("  selftest: every audit passes its clean case and raises on its break"); return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--selftest", action="store_true"); ap.add_argument("--run", action="store_true"); a = ap.parse_args()
    sys.exit(selftest() if a.selftest else run() if a.run else 1)
