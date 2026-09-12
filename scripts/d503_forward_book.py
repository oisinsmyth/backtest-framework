"""D503 -- the ONE-PASS forward read: K8, the MACD component, and the assembled two-arm book.

    uv run python scripts/d503_forward_book.py --self-test
    uv run python scripts/d503_forward_book.py --run --principals-word [--json]

Pre-registered in
`docs/decisions/D503-PRE-REG-the-one-pass-forward-read-K8-the-MACD-component-and-the-assembled-two-arm-book-on-the-sealed-2024-slice.md`.

**THIS SPENDS THE HOLDOUT.** 2024-01-02 .. 2026-09-09 on the NQ day session is spent for both
components and for the book the moment this runs. It refuses without `--principals-word`, the
same guard K8's own runner carries.

K8's forward numbers are NOT recomputed here -- they are read from
`data/d498_k8_forward.json` and `data/d498_trades_forward_NQ_K8.csv.gz`, produced by that
component's own pre-registered guarded command, and asserted consistent between the two files.

WARM-UP IS PRE-2024 AND THAT IS NOT A LEAK
------------------------------------------
The MACD needs history to exist at all. The signal is computed on a continuous series that
starts in 2023 and **no P&L is attributed to any session before 2024-01-02** -- asserted. Using
past bars to warm a filter is what a real-time implementation does; starting the filter cold on
2024-01-02 would measure a warm-up artefact instead of the component.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from d484_offdiagonal_and_macd import (  # noqa: E402
    CONTRACT_PURE_BARS, CROSS_TICKS, COMMISSION_RT, GateError, SEGMENTS, SPECS,
    impulse_macd, macd_hist, rotate)
from d491_conditional_hold import DAY_FIRST_DECIDE, LAST_SEG, TRADING_DAYS, simulate  # noqa: E402
from d495_agree_confluence import FIX, META, agree_signal, p5_recognised  # noqa: E402
from d496_book_sharpe_bar import expected_profit_before_breach  # noqa: E402
from d501_worst_day_frequency import max_drawdown_life, p_at_least_one, recurrence_years  # noqa: E402

OUT = REPO / "data" / "d503_forward_book.json"
K8_FWD = REPO / "data" / "d498_k8_forward.json"
K8_TRADES = REPO / "data" / "d498_trades_forward_NQ_K8.csv.gz"

ROOT = "NQ"
SIZED = "MNQ"
M_HOLD = 5
FWD_LO, FWD_HI = "2024-01-02", "2026-09-09"
WARM_LO = "2023-01-01"                # signal warm-up only; no P&L attributed before FWD_LO
ACCOUNT = 50_000.0
TRAIL_DD = 0.04 * ACCOUNT
P3_CAP = 0.02 * ACCOUNT
P3A_BAR = 1.0                          # amended P3: breaches a year
P3B_BAR = 0.33                         # amended P3: share of the account's life
C_A = 0.5
N_DRAWS = 2000
SEED = 503

# in-sample figures, committed, for the decay columns
IS = {"macd": {"sharpe": 0.722857225865919, "mean": 8.22, "sigma": 180.48, "worst": -1314.51,
               "trips": 1.0166},
      "k8": {"sharpe": 0.595, "gross_per_trade": 17.87, "hit": 0.57, "worst": -1025.0},
      "book": {"sharpe": 0.856, "mean": 14.63, "sigma": 271.0, "worst": -1801.0},
      "rho": 0.1904}


def P(*a, **k):
    print(*a, **k, flush=True)


# ---------------------------------------------------------------- the component, on a window

def series_window(root, d_all, meta, lo, hi):
    """D484's `series_for`, with the window given explicitly instead of IN_SAMPLE.

    Deliberately a copy and not a call: `series_for` raises on any row past 2023, which is the
    holdout guard, and that guard must stay where it is.
    """
    d = d_all[(d_all["root"] == root) & d_all["same_front"]]
    d = d[d["day"].between(lo, hi)].sort_values("day", kind="stable")
    nseg = len(SEGMENTS)
    O = np.stack([d[f"{s}_o"].to_numpy(float) for s in SEGMENTS], axis=1).ravel()
    H_ = np.stack([d[f"{s}_h"].to_numpy(float) for s in SEGMENTS], axis=1).ravel()
    L_ = np.stack([d[f"{s}_l"].to_numpy(float) for s in SEGMENTS], axis=1).ravel()
    C_ = np.stack([d[f"{s}_c"].to_numpy(float) for s in SEGMENTS], axis=1).ravel()
    con = np.repeat(d["contract"].to_numpy(), nseg)
    pos = (O > 0) & (H_ > 0) & (L_ > 0) & (C_ > 0)
    with np.errstate(invalid="ignore", divide="ignore"):
        lo_, lh, ll, lc = (np.where(pos, np.log(O), np.nan), np.where(pos, np.log(H_), np.nan),
                           np.where(pos, np.log(L_), np.nan), np.where(pos, np.log(C_), np.nan))
    same = np.ones(len(con), dtype=bool)
    for k in range(1, CONTRACT_PURE_BARS + 1):
        same[k:] &= con[k:] == con[:-k]
    same[:CONTRACT_PURE_BARS] = False
    return {"log_open": lo_, "log_high": lh, "log_low": ll, "log_close": lc,
            "pure": same & pos, "days": d["day"].to_numpy()}


def macd_panel(d_all, meta, spec):
    """The frozen component's signal and prices on the forward window, warm-up included."""
    s = series_window(ROOT, d_all, meta, WARM_LO, FWD_HI)
    nseg = len(SEGMENTS)
    k = len(s["log_close"]) // nseg
    g = lambda a: np.exp(a[:k * nseg]).reshape(k, nseg)      # noqa: E731
    md = impulse_macd(s["log_high"], s["log_low"], s["log_close"])[1][:k * nseg]
    b1 = np.where(md == 0.0, 0.0,
                  np.sign(impulse_macd(s["log_high"], s["log_low"],
                                       s["log_close"])[0][:k * nseg])).reshape(k, nseg)
    b2 = np.sign(macd_hist(s["log_close"])[:k * nseg]).reshape(k, nseg)
    pure = s["pure"][:k * nseg].reshape(k, nseg)
    first = DAY_FIRST_DECIDE
    keep = pure[:, first:LAST_SEG + 1].all(axis=1)
    days = s["days"][:k]
    fwd = keep & (days >= FWD_LO)                            # TRADE only the forward slice
    return {"O": g(s["log_open"])[fwd], "C": g(s["log_close"])[fwd],
            "AGREE": agree_signal(b1, b2)[fwd], "days": days[fwd], "first": first,
            "tick_pts": spec[ROOT]["tick_points"], "tick_usd": spec[SIZED]["tick_usd"],
            "cost": COMMISSION_RT / spec[SIZED]["tick_usd"] + CROSS_TICKS,
            "n_warm_dropped": int((keep & (days < FWD_LO)).sum())}


def simulate_trades(O, C, sig, first_decide, M, cost_ticks, tick_pts):
    """The SAME machine as D491's `simulate`, instrumented to emit one row per TRADE.

    Needed because group 2 of the report is a per-trade distribution and `simulate` returns
    per-session totals only. Asserted to reproduce `simulate` exactly.
    """
    n = O.shape[0]
    rows = []
    s_all = np.nan_to_num(sig, nan=0.0)
    pos = np.zeros(n)
    entry_px = np.zeros(n)
    entry_t = np.full(n, -1, dtype=np.int64)
    for t in range(first_decide, LAST_SEG):
        s = s_all[:, t]
        px = O[:, t + 1]
        live = pos != 0
        ex = live & ((t - entry_t) >= M) & (s * pos <= 0) & np.isfinite(px)
        for i in np.flatnonzero(ex):
            rows.append((i, int(entry_t[i]), t + 1, float(pos[i]),
                         float(pos[i] * (px[i] - entry_px[i]) / tick_pts - cost_ticks),
                         "SIGNAL"))
        pos = np.where(ex, 0.0, pos)
        en = (pos == 0) & (s != 0) & np.isfinite(px)
        entry_px = np.where(en, px, entry_px)
        entry_t = np.where(en, t, entry_t)
        pos = np.where(en, s, pos)
    cpx = C[:, LAST_SEG]
    still = (pos != 0) & np.isfinite(cpx)
    for i in np.flatnonzero(still):
        rows.append((i, int(entry_t[i]), LAST_SEG, float(pos[i]),
                     float(pos[i] * (cpx[i] - entry_px[i]) / tick_pts - cost_ticks),
                     "FLATTEN"))
    return rows


# ---------------------------------------------------------------- statistics

def perf(d_usd, n_avail, trades_usd, tick_usd, cost_ticks, label):
    """Group 1 + group 2 on one arm's daily series and its trade list."""
    d = np.asarray(d_usd, dtype=float)
    tr = np.asarray(trades_usd, dtype=float)
    mu, sd = float(d.mean()), float(d.std(ddof=1))
    eq = np.cumsum(d)
    dd = float((np.maximum.accumulate(eq) - eq).max())
    out = {"label": label, "n_sessions": int(len(d)), "n_available": int(n_avail),
           "exposure": float((d != 0).mean()), "mean_usd": mu, "median_usd": float(np.median(d)),
           "daily_sigma_usd": sd, "sharpe": mu / sd * np.sqrt(TRADING_DAYS) if sd > 0 else np.nan,
           "max_drawdown_usd": dd, "total_usd": float(d.sum()),
           "worst_day_usd": float(d.min()), "best_day_usd": float(d.max()),
           "skew": float(((d - mu) ** 3).mean() / sd ** 3) if sd > 0 else np.nan,
           "kurtosis": float(((d - mu) ** 4).mean() / sd ** 4) if sd > 0 else np.nan}
    if len(tr):
        wins, losses = tr[tr > 0], tr[tr < 0]
        lo1, hi1 = np.percentile(tr, 1), np.percentile(tr, 99)
        out.update({"n_trades": int(len(tr)), "trade_mean_usd": float(tr.mean()),
                    "trade_median_usd": float(np.median(tr)),
                    "hit_rate": float((tr > 0).mean()),
                    "payoff": float(wins.mean() / abs(losses.mean())) if len(losses) else np.nan,
                    "trade_mean_ex_top_usd": float(tr[tr <= hi1].mean()),
                    "trade_mean_ex_bottom_usd": float(tr[tr >= lo1].mean()),
                    "trade_mean_trimmed_usd": float(tr[(tr >= lo1) & (tr <= hi1)].mean()),
                    "cost_usd_per_trade": float(cost_ticks * tick_usd),
                    "gross_mean_per_trade_usd": float(tr.mean() + cost_ticks * tick_usd),
                    "breakeven_cost_ticks": float(tr.mean() / tick_usd + cost_ticks)})
    return out


def concentration(d_usd, days):
    """Group 3: what the winners depend on."""
    d = np.asarray(d_usd, dtype=float)
    total = float(d.sum())
    order = np.argsort(-d)
    half, run = None, 0.0
    for j, i in enumerate(order, 1):
        run += d[i]
        if total > 0 and run >= 0.5 * total:
            half = j
            break
    yrs = np.array([str(x)[:4] for x in days])
    qs = np.array([f"{str(x)[:4]}Q{(int(str(x)[5:7]) - 1) // 3 + 1}" for x in days])
    by_year = {y: float(d[yrs == y].sum()) for y in sorted(set(yrs))}
    by_q = {q: float(d[qs == q].sum()) for q in sorted(set(qs))}
    sh = (lambda n: float(np.sort(d)[-n:].sum() / total) if total > 0 else np.nan)
    return {"sessions_to_half_pnl": half, "n_sessions": int(len(d)),
            "top1_session_share": sh(1), "top5_session_share": sh(5),
            "top10_session_share": sh(10),
            "by_year_usd": by_year, "by_quarter_usd": by_q,
            "profitable_years": sum(1 for v in by_year.values() if v > 0),
            "n_years": len(by_year),
            "profitable_quarters": sum(1 for v in by_q.values() if v > 0),
            "n_quarters": len(by_q)}


def hurdle_p(d_usd, label):
    """Hurdle P on a daily series, under the AMENDED P3 (P3a/P3b/P3c)."""
    d = np.asarray(d_usd, dtype=float)
    n = len(d)
    mu, sd = float(d.mean()), float(d.std(ddof=1))
    sharpe = mu / sd * np.sqrt(TRADING_DAYS) if sd > 0 else np.nan
    n_br = int((d <= -P3_CAP).sum())
    p3a = n_br / n * TRADING_DAYS
    nd_dd, life_dd, _ = max_drawdown_life(d, TRAIL_DD)
    lives2, eq, peak, start = [], 0.0, 0.0, 0
    for i, x in enumerate(d):
        eq += x
        peak = max(peak, eq)
        if peak - eq >= TRAIL_DD or x <= -P3_CAP:
            lives2.append(i - start + 1)
            eq, peak, start = 0.0, 0.0, i + 1
    life_both = float(np.mean(lives2)) if lives2 else 0.0
    p3b = (1.0 - life_both / life_dd) if life_dd > 0 else np.nan
    # the helper works in ACCOUNT-FRACTION units (sigma and D as fractions), so convert both
    # ways rather than feeding it dollars -- which is the slip that crashed the first run
    if sd > 0 and sharpe > 0:
        pf, life = expected_profit_before_breach(sharpe, sd / ACCOUNT, TRAIL_DD / ACCOUNT)
        ep, ep_life = float(pf * ACCOUNT), float(life)
    else:
        ep, ep_life = None, None
    h = p5_recognised(d)
    return {"label": label, "P1_post_sizing_usd_per_year": mu * TRADING_DAYS,
            "P2_pass": True, "P2_note": "both arms exit by 16:00 ET, inside a 16:10 flatten",
            "P3a_breaches_per_year": p3a, "P3a_bar": P3A_BAR, "P3a_pass": bool(p3a <= P3A_BAR),
            "P3a_breaches": n_br, "P3a_recurrence_years": recurrence_years(n_br, n),
            "P3b_life_cost": p3b, "P3b_bar": P3B_BAR,
            "P3b_pass": bool(np.isfinite(p3b) and p3b <= P3B_BAR),
            "P3c_worst_day_usd": float(d.min()),
            "P3c_worst_day_in_sigma": float(d.min() / sd) if sd > 0 else np.nan,
            "P3c_share_of_loss_budget": float(-d.min() / TRAIL_DD),
            "life_dd_only_sessions": life_dd, "life_with_P3_sessions": life_both,
            "deaths_dd_only": nd_dd, "deaths_with_P3": len(lives2),
            "P4_expected_profit_usd": ep, "P4_expected_life_days": ep_life,
            "P5_best_day_share": h["best_day_share"], "P5_haircut_usd": h["haircut_usd"],
            "P5_pass": True,
            "P6": "Topstep or MyFundedFutures -- a venue choice, not a measurement",
            "p_breach_in_252": p_at_least_one(n_br, n, 252)}


# ---------------------------------------------------------------- self-test

def do_self_test() -> int:
    fails = []

    def chk(label, cond, detail=""):
        P(f"    [{'PASS' if cond else 'FAIL'}] {label:62} {detail}")
        if not cond:
            fails.append(label)

    # --- the union-calendar sum, and a deliberate misalignment ------------------------------
    cal = np.array(["d1", "d2", "d3", "d4"])
    a = {"d1": 10.0, "d3": -5.0}
    b = {"d2": 3.0, "d3": 7.0}
    va = np.array([a.get(x, 0.0) for x in cal])
    vb = np.array([b.get(x, 0.0) for x in cal])
    chk("union calendar zero-fills an absent arm",
        list(va) == [10.0, 0.0, -5.0, 0.0] and list(vb) == [0.0, 3.0, 7.0, 0.0])
    chk("the book is the session-by-session sum",
        list(va + vb) == [10.0, 3.0, 2.0, 0.0], f"{list(va + vb)}")
    chk("[X] a one-session misalignment changes the book's sum",
        not np.array_equal(va + vb, va + np.roll(vb, 1)),
        f"misaligned {list(va + np.roll(vb, 1))}")

    # --- the holdout boundary ----------------------------------------------------------------
    days = np.array(["2023-12-28", "2024-01-02", "2025-06-10"])
    m = days >= FWD_LO
    chk("the forward mask excludes every pre-2024 session", list(m) == [False, True, True])
    chk("[X] a widened boundary would admit 2023, and this one does not",
        int(m.sum()) == 2 and int((days >= "2023-01-01").sum()) == 3)

    # --- P3a / P3b arithmetic on a hand case ------------------------------------------------
    d = np.zeros(252)
    d[10] = -1200.0                      # one breach in exactly one year
    d[20:30] = 100.0
    hp = hurdle_p(d, "hand")
    chk("P3a counts one breach in 252 sessions as 1.00 a year",
        abs(hp["P3a_breaches_per_year"] - 1.0) < 1e-9, f"{hp['P3a_breaches_per_year']:.4f}")
    chk("P3a passes exactly AT the bar of 1.0", hp["P3a_pass"])
    d2 = d.copy()
    d2[40] = -1200.0                     # two breaches -> 2.0 a year
    chk("[X] two breaches in a year FAIL P3a",
        not hurdle_p(d2, "hand2")["P3a_pass"],
        f"{hurdle_p(d2, 'hand2')['P3a_breaches_per_year']:.2f}/yr")
    chk("P3c reports the worst day and its share of the $2,000 budget",
        abs(hp["P3c_worst_day_usd"] + 1200.0) < 1e-9
        and abs(hp["P3c_share_of_loss_budget"] - 0.6) < 1e-9,
        f"{hp['P3c_share_of_loss_budget']:.2f}")

    # --- the trade instrumentation must reproduce the machine exactly ------------------------
    rng = np.random.default_rng(SEED)
    n, nseg = 60, len(SEGMENTS)
    lp = np.cumsum(rng.normal(0, 0.002, n * nseg)) + 9.0
    O = np.exp(lp).reshape(n, nseg)
    C = np.exp(lp + 0.0003).reshape(n, nseg)
    sig = np.sign(rng.normal(0, 1, (n, nseg)))
    pnl, trips = simulate(O, C, sig, DAY_FIRST_DECIDE, M_HOLD, 2.0, 0.25)
    rows = simulate_trades(O, C, sig, DAY_FIRST_DECIDE, M_HOLD, 2.0, 0.25)
    per = np.zeros(n)
    cnt = np.zeros(n)
    for i, t0, t1, s, v, why in rows:
        per[i] += v
        cnt[i] += 1
    chk("simulate_trades reproduces per-session P&L EXACTLY",
        np.abs(per - pnl).max() < 1e-12, f"max |diff| {np.abs(per - pnl).max():.2e}")
    chk("and reproduces the trip count exactly", np.array_equal(cnt, trips))
    chk("[X] dropping one trade row breaks the reconstruction",
        len(rows) > 1 and abs(sum(r[4] for r in rows[1:]) - pnl.sum()) > 1e-9)
    # THE REAL INVARIANT: a SIGNAL exit must have held >= M decide-segments; the 16:00 FLATTEN
    # is P2 and overrides the minimum hold, so it is exempt. My first assertion read min(all)
    # and fired on a forced exit, which is correct behaviour.
    sig_h = [t1 - 1 - t0 for _, t0, t1, _, _, w in rows if w == "SIGNAL"]
    flat_h = [t1 - t0 for _, t0, t1, _, _, w in rows if w == "FLATTEN"]
    chk("every SIGNAL exit held >= M decide-segments", min(sig_h) >= M_HOLD,
        f"min {min(sig_h)}, max {max(sig_h)}, n={len(sig_h)}")
    chk("the 16:00 FLATTEN is exempt and DOES produce shorter holds -- which is P2, not a bug",
        len(flat_h) > 0 and min(flat_h) < M_HOLD,
        f"min flatten hold {min(flat_h)}, n={len(flat_h)}")
    chk("[X] every SIGNAL exit lands strictly before the forced-exit segment",
        max(t1 for _, _, t1, _, _, w in rows if w == "SIGNAL") <= LAST_SEG)

    # --- concentration on a known series -----------------------------------------------------
    cc = concentration(np.array([100.0, 1.0, 1.0, 1.0]), np.array(["2024-01-02"] * 4))
    chk("one session carrying most of the P&L reads 1 session to half",
        cc["sessions_to_half_pnl"] == 1 and abs(cc["top1_session_share"] - 100 / 103) < 1e-9,
        f"{cc['sessions_to_half_pnl']}, top1 {cc['top1_session_share']:.3f}")
    cc2 = concentration(np.ones(100), np.array(["2024-01-02"] * 100))
    chk("[X] an even series needs 50 sessions, not 1",
        cc2["sessions_to_half_pnl"] == 50, f"{cc2['sessions_to_half_pnl']}")

    # --- the rotation preserves what it must -------------------------------------------------
    x = np.repeat([1.0, -1.0], 30)
    chk("rotation preserves the mean and the marginal distribution",
        abs(rotate(x, 17).mean() - x.mean()) < 1e-15
        and np.array_equal(np.sort(rotate(x, 17)), np.sort(x)))

    P(f"\n  {len(fails)} failed: {fails}" if fails else "\n  all checks pass")
    return 1 if fails else 0


# ---------------------------------------------------------------- the run

def do_run(word: bool, as_json: bool) -> int:
    import pandas as pd

    if not word:
        P("REFUSED: --run reads the reserved 2024+ slice for BOTH components and the book.")
        P("Re-run with --principals-word only on the principal's word.")
        return 2

    meta = json.loads(META.read_text(encoding="utf-8"))
    spec = json.loads(SPECS.read_text(encoding="utf-8"))
    d_all = pd.read_csv(FIX)

    P("D503 -- the ONE-PASS forward read, on the principal's word")
    P(f"  slice {FWD_LO} .. {FWD_HI}   (signal warm-up from {WARM_LO}, no P&L before {FWD_LO})\n")

    # ---- arm 1: the MACD component
    pk = macd_panel(d_all, meta, spec)
    days = pk["days"]
    if len(days) == 0 or str(days.min()) < FWD_LO:
        raise GateError(f"[HOLDOUT] a session before {FWD_LO} reached the P&L path")
    if str(days.max()) > FWD_HI:
        raise GateError(f"[HOLDOUT] a session past {FWD_HI} reached the P&L path")
    pnl_tk, trips = simulate(pk["O"], pk["C"], pk["AGREE"], pk["first"], M_HOLD,
                             pk["cost"], pk["tick_pts"])
    gross_tk, _ = simulate(pk["O"], pk["C"], pk["AGREE"], pk["first"], M_HOLD, 0.0,
                           pk["tick_pts"])
    rows = simulate_trades(pk["O"], pk["C"], pk["AGREE"], pk["first"], M_HOLD, pk["cost"],
                           pk["tick_pts"])
    per = np.zeros(len(days))
    for i, _, _, _, v, _w in rows:
        per[i] += v
    if np.abs(per - pnl_tk).max() > 1e-12:
        raise GateError("[TRADES] the instrumented machine disagrees with simulate")
    macd_d = pnl_tk * pk["tick_usd"]
    macd_tr = np.array([r[4] * pk["tick_usd"] for r in rows])
    holds = [t1 - t0 for _, t0, t1, _, _, _w in rows]
    P(f"  MACD arm: {len(days):,} sessions, {pk['n_warm_dropped']:,} warm-up sessions dropped, "
      f"{len(rows):,} trades, mean hold {np.mean(holds):.1f} segments")

    # ---- arm 2: K8, read from its OWN runner's artifacts, two paths asserted equal
    k8j = json.loads(K8_FWD.read_text(encoding="utf-8"))
    k8t = pd.read_csv(K8_TRADES)
    k8_ser = k8t.groupby("day")["net_usd"].sum()
    if abs(float(k8t["gross_usd"].mean()) - float(k8j["forward"]["NQ"]["gross_mean"])) > 0.01:
        raise GateError("[K8] the trade CSV and the JSON artifact disagree on the gross mean")
    if len(k8t) != int(k8j["forward"]["NQ"]["trades"]):
        raise GateError("[K8] trade counts disagree between the two artifacts")
    P(f"  K8 arm  : {len(k8t):,} trades from its own guarded read, verdict "
      f"{k8j['verdict']}, gross ${float(k8t['gross_usd'].mean()):+.2f} a trade")

    # ---- the union calendar
    cal = np.array(sorted(set(days.tolist()) | set(k8_ser.index.tolist())))
    cal = cal[(cal >= FWD_LO) & (cal <= FWD_HI)]
    m_map = dict(zip(days.tolist(), macd_d.tolist()))
    a_macd = np.array([m_map.get(x, 0.0) for x in cal])
    a_k8 = np.array([float(k8_ser.get(x, 0.0)) for x in cal])
    book = a_macd + a_k8
    miss_macd = int(sum(1 for x in cal if x not in m_map))
    miss_k8 = int(sum(1 for x in cal if x not in k8_ser.index))
    P(f"  union calendar {len(cal):,} sessions   MACD absent {miss_macd}   "
      f"K8 absent {miss_k8} (K8 trades only after down days)\n")

    # ---- group 1 + 2
    P("=== 1. PERFORMANCE, NET AND GROSS, PER ARM AND FOR THE BOOK ===")
    st = {"macd": perf(a_macd, len(cal), macd_tr, pk["tick_usd"], pk["cost"], "MACD component"),
          "k8": perf(a_k8, len(cal), k8t["net_usd"].to_numpy(float), pk["tick_usd"],
                     COMMISSION_RT / pk["tick_usd"], "K8"),
          "book": perf(book, len(cal), np.concatenate([macd_tr, k8t["net_usd"].to_numpy(float)]),
                       pk["tick_usd"], pk["cost"], "the assembled book")}
    gross_d = gross_tk * pk["tick_usd"]
    st["macd"]["gross_sharpe"] = float(gross_d.mean() / gross_d.std(ddof=1)
                                       * np.sqrt(TRADING_DAYS))
    st["macd"]["trips_per_session"] = float(trips.mean())
    P(f"{'':22}{'MACD':>12}{'K8':>12}{'BOOK':>12}{'in-samp book':>14}")
    for key, lab, f in (("sharpe", "net Sharpe", "{:+.3f}"), ("mean_usd", "mean $/session",
                        "{:+.2f}"), ("median_usd", "median $/session", "{:+.2f}"),
                        ("daily_sigma_usd", "daily sigma $", "{:.0f}"),
                        ("exposure", "exposure", "{:.1%}"),
                        ("max_drawdown_usd", "max drawdown $", "{:,.0f}"),
                        ("total_usd", "total $", "{:,.0f}"),
                        ("worst_day_usd", "worst day $", "{:,.0f}"),
                        ("skew", "skew", "{:+.2f}"), ("kurtosis", "kurtosis", "{:.1f}")):
        vals = "".join(f.format(st[a][key]).rjust(12) for a in ("macd", "k8", "book"))
        isv = IS["book"].get(key.replace("_usd", "").replace("mean", "mean")
                             if key != "sharpe" else "sharpe")
        P(f"  {lab:<20}{vals}" + (f"{isv:>14.3f}" if key == "sharpe" else ""))

    P("\n=== 2. TRADE DISTRIBUTION ===")
    P(f"{'':22}{'MACD':>12}{'K8':>12}")
    for key, lab, f in (("n_trades", "trades", "{:,.0f}"),
                        ("trade_mean_usd", "mean $/trade (net)", "{:+.2f}"),
                        ("trade_median_usd", "median $/trade", "{:+.2f}"),
                        ("gross_mean_per_trade_usd", "mean $/trade GROSS", "{:+.2f}"),
                        ("hit_rate", "hit rate", "{:.1%}"), ("payoff", "payoff", "{:.2f}"),
                        ("trade_mean_ex_top_usd", "mean ex-top 1%", "{:+.2f}"),
                        ("trade_mean_ex_bottom_usd", "mean ex-bottom 1%", "{:+.2f}"),
                        ("trade_mean_trimmed_usd", "mean trimmed both", "{:+.2f}"),
                        ("cost_usd_per_trade", "cost $/trade", "{:.2f}"),
                        ("breakeven_cost_ticks", "breakeven cost, ticks", "{:+.2f}")):
        P(f"  {lab:<20}" + "".join(f.format(st[a][key]).rjust(12) for a in ("macd", "k8")))

    P("\n=== 3. WHAT THE WINNERS DEPEND ON ===")
    con = {a: concentration(v, cal) for a, v in (("macd", a_macd), ("k8", a_k8),
                                                 ("book", book))}
    P(f"{'':22}{'MACD':>12}{'K8':>12}{'BOOK':>12}")
    for key, lab, f in (("sessions_to_half_pnl", "sessions to half", "{}"),
                        ("top1_session_share", "top 1 session", "{:.1%}"),
                        ("top5_session_share", "top 5 sessions", "{:.1%}"),
                        ("top10_session_share", "top 10 sessions", "{:.1%}")):
        P(f"  {lab:<20}" + "".join(str(f.format(con[a][key])).rjust(12)
                                   for a in ("macd", "k8", "book")))
    P(f"  profitable years    " + "".join(f"{con[a]['profitable_years']}/{con[a]['n_years']}"
                                          .rjust(12) for a in ("macd", "k8", "book")))
    P(f"  profitable quarters " + "".join(
        f"{con[a]['profitable_quarters']}/{con[a]['n_quarters']}".rjust(12)
        for a in ("macd", "k8", "book")))
    P("\n     by year, total $:")
    for y in sorted(con["book"]["by_year_usd"]):
        P(f"       {y}" + "".join(f"{con[a]['by_year_usd'].get(y, 0.0):>12,.0f}"
                                  for a in ("macd", "k8", "book")))

    # ---- group 4: nulls
    P(f"\n=== 4. NULLS, {N_DRAWS:,} draws ===")
    rng = np.random.default_rng(SEED)
    nm = len(days)
    nsig = np.empty(N_DRAWS)
    for i in range(N_DRAWS):
        off = int(rng.integers(1, nm))
        sg = rotate(pk["AGREE"], off)
        pn, _ = simulate(pk["O"], pk["C"], sg, pk["first"], M_HOLD, pk["cost"], pk["tick_pts"])
        dd = pn * pk["tick_usd"]
        nsig[i] = dd.mean() / dd.std(ddof=1) * np.sqrt(TRADING_DAYS) if dd.std(ddof=1) > 0 else 0
    nbook = np.empty(N_DRAWS)
    for i in range(N_DRAWS):
        off = int(rng.integers(1, len(cal)))
        b = a_macd + rotate(a_k8, off)
        nbook[i] = b.mean() / b.std(ddof=1) * np.sqrt(TRADING_DAYS)

    def band(x, obs, lab):
        p50, p95 = float(np.percentile(x, 50)), float(np.percentile(x, 95))
        bs = np.array([np.percentile(rng.choice(x, len(x)), 95) for _ in range(200)])
        se = float(bs.std(ddof=1))
        marg = (obs - p95) / se if se > 0 else float("inf")
        P(f"  {lab:<34}obs {obs:+.3f}   p50 {p50:+.3f}   p95 {p95:+.3f}   "
          f"SE {se:.4f}   {marg:+.1f} SE"
          + ("   UNRESOLVED" if abs(marg) < 2 else ""))
        return {"observed": obs, "p50": p50, "p95": p95, "p95_se": se, "margin_se": marg,
                "clears": bool(obs > p95), "unresolved": bool(abs(marg) < 2)}

    nulls = {"macd_signal_rotation": band(nsig, st["macd"]["sharpe"],
                                          "MACD arm, signal rotated"),
             "book_alignment_rotation": band(nbook, st["book"]["sharpe"],
                                             "BOOK, K8's P&L rotated")}
    P("  the BOOK null rotates K8's realised P&L against the MACD's, so it prices the")
    P("  ALIGNMENT (the diversification benefit), not either arm's edge. K8's own edge null")
    P(f"  is its runner's N1: p95 +{k8j['forward']['NQ']['N1']['p95']:.1f} bp against an")
    P(f"  observed {k8j['forward']['NQ']['bp_mean']:+.1f} bp.")

    # ---- rho, forward
    rho_f = float(np.corrcoef(a_macd, a_k8)[0, 1])
    mk = a_k8 != 0
    rho_t = float(np.corrcoef(a_macd[mk], a_k8[mk])[0, 1])
    P(f"\n=== 5. CORRELATION, FORWARD vs IN-SAMPLE ===")
    P(f"  rho on the union calendar   forward {rho_f:+.4f}   in-sample {IS['rho']:+.4f}")
    P(f"  rho on K8's trading days    forward {rho_t:+.4f}   in-sample +0.2692")
    P(f"  C-b (< 0.3): {'PASS -- Book 1' if rho_f < 0.3 else 'FAIL -- routes to the VAULT'}")

    # ---- verdicts
    P(f"\n=== 6. VERDICTS, BY THE RULES DECLARED IN THE PRE-REGISTRATION ===")
    g_macd = st["macd"]["gross_mean_per_trade_usd"]
    s_macd = st["macd"]["sharpe"]
    v_macd = ("REMOVED" if (s_macd < -0.3 or g_macd <= 0)
              else ("FULL" if (s_macd > C_A and g_macd > 0) else "PROVISIONAL"))
    P(f"  MACD component: {v_macd}   (net Sharpe {s_macd:+.3f}, gross ${g_macd:+.2f} a trade)")
    P(f"  K8            : {k8j['verdict']}   (from its own guarded read)")
    assembled = v_macd != "REMOVED" and k8j["verdict"] != "REMOVED"
    P(f"  the book is {'ASSEMBLED' if assembled else 'NOT assembled'} "
      f"(assembled only if neither arm is REMOVED)")

    # ---- hurdle P
    P(f"\n=== 7. HURDLE P ON THE ASSEMBLED BOOK (amended P3) ===")
    hp = {a: hurdle_p(v, a) for a, v in (("macd", a_macd), ("k8", a_k8), ("book", book))}
    h = hp["book"]
    P(f"  P1 sizing        ${h['P1_post_sizing_usd_per_year']:+,.0f}/yr post-sizing")
    P(f"  P2 flatten       PASS -- {h['P2_note']}")
    P(f"  P3a rate         {h['P3a_breaches_per_year']:.2f}/yr against a bar of "
      f"{P3A_BAR:.1f}   {'PASS' if h['P3a_pass'] else 'FAIL'}   "
      f"({h['P3a_breaches']} breaches, one every {h['P3a_recurrence_years']:.2f} yr)")
    P(f"  P3b life cost    {h['P3b_life_cost']:.1%} against a bar of {P3B_BAR:.0%}   "
      f"{'PASS' if h['P3b_pass'] else 'FAIL'}   "
      f"(life {h['life_dd_only_sessions']:.0f} -> {h['life_with_P3_sessions']:.0f} sessions)")
    P(f"  P3c worst day    ${h['P3c_worst_day_usd']:,.0f} = "
      f"{h['P3c_worst_day_in_sigma']:.2f} sigma = "
      f"{h['P3c_share_of_loss_budget']:.0%} of the $2,000 budget   (reported, not a gate)")
    if h["P4_expected_profit_usd"]:
        P(f"  P4 profit/breach ${h['P4_expected_profit_usd']:,.0f}, "
          f"E[life] {h['P4_expected_life_days']:.0f} d (Brownian)")
    else:
        P(f"  P4 profit/breach n/a -- the book's drift is not positive")
    P(f"  P5 haircut       best day {h['P5_best_day_share']:.1%} of total, "
      f"haircut ${h['P5_haircut_usd']:,.0f}")
    P(f"  P6 automation    {h['P6']}")
    P(f"\n  EMPIRICAL trailing-4% life (D501's walker): "
      f"{h['life_dd_only_sessions']:.0f} sessions, {h['deaths_dd_only']} deaths")

    art = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "purpose": "D503: the ONE-PASS forward read of K8, the MACD component and the "
                      "assembled two-arm book on 2024-01-02..2026-09-09. THE HOLDOUT IS NOW "
                      "SPENT for both components and the book.",
           "slice": [FWD_LO, FWD_HI], "warmup_from": WARM_LO,
           "n_union_sessions": int(len(cal)),
           "macd_absent_sessions": miss_macd, "k8_absent_sessions": miss_k8,
           "mean_hold_segments": float(np.mean(holds)),
           "performance": st, "concentration": con, "nulls": nulls,
           "rho_forward_union": rho_f, "rho_forward_k8_days": rho_t,
           "rho_in_sample_union": IS["rho"],
           "verdicts": {"macd_component": v_macd, "k8": k8j["verdict"],
                        "book_assembled": bool(assembled)},
           "hurdle_p": hp, "in_sample_reference": IS,
           "limitations": [
               "THE HOLDOUT IS SPENT. No cell may be re-read, sharpened against or re-scored "
               "on 2024-01-02..2026-09-09 for these components or this book.",
               "the book is UN-NETTED: one MNQ on each arm, so opposing arms pay two sets of "
               "costs and sit flat; netting and weighting are new constructions, untested",
               "fills are open-of-next-segment / open-plus-a-tick at the measured half-spread, "
               "no queue, no partial fills -- and the WORST DAY, which P3 reads, is the figure "
               "most exposed to that optimism",
               "K8 runs on the 1-minute fixture (09:30+tick -> 15:59) and the MACD arm on the "
               "hourly fixture (h09 decisions -> 16:00); the union calendar carries that "
               "asymmetry explicitly rather than intersecting it away"]}
    OUT.write_text(json.dumps(art, indent=2, default=float), encoding="utf-8")
    P(f"\n  wrote {OUT.relative_to(REPO)}")
    if as_json:
        P(json.dumps(art, indent=2, default=float))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--principals-word", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return do_self_test()
    if a.run:
        return do_run(a.principals_word, a.json)
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
