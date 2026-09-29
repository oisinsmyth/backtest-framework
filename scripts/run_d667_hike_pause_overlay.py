"""D667 -- pause the admitted MACD arm for ten sessions after an NQ margin increase: a disclosed measurement.

    python scripts/run_d667_hike_pause_overlay.py --selftest
    python scripts/run_d667_hike_pause_overlay.py --run          # -> data/d667_hike_pause_overlay.json

PRE-REGISTRATION: docs/decisions/D667-PRE-REG-margin-hike-pause-on-the-macd-arm.md (161f553), committed before this
file existed. The arm is imported through D508's `load_arm()` (D504's build, D491's simulator), which scores only
2016-01-04 -> 2023-12-29: the arm's 2024+ was spent by D503 and is never read here. Margin events come from D657's
table (data/d657_margin_changes.csv) and coverage (data/d657_margin_coverage.csv); no price is read for them.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.validation.hurdle_p import p3  # noqa: E402

OUT = REPO / "data" / "d667_hike_pause_overlay.json"
CHANGES = REPO / "data" / "d657_margin_changes.csv"
COVERAGE = REPO / "data" / "d657_margin_coverage.csv"
PREREG = "161f553"
LO, HI = "2016-01-04", "2023-12-29"
ROOT = "NQ"
MIN_PCT, MERGE, PAUSE, CTRL_GAP, VOLWIN = 0.05, 10, 10, 20, 20
DRAWS, SEED, BOOT = 2000, 667, 1000
REPRO_SESSIONS, REPRO_NET = 1876, 15423.0


def P(*a, **k):
    print(*a, **k, flush=True)


class GateError(AssertionError):
    pass


def _d508():
    """D508's module, loaded by path. Its body only loads its own dependencies; `main` is guarded."""
    s = importlib.util.spec_from_file_location("d508c", REPO / "scripts" / "run_d508_stretch_ranker.py")
    m = importlib.util.module_from_spec(s)
    sys.modules["d508c"] = m
    s.loader.exec_module(m)
    return m


def load_arm() -> dict:
    arm = _d508().load_arm()
    days = np.asarray(arm["days"]).astype(str)
    if max(days) > HI or min(days) < LO:
        raise GateError(f"[WINDOW] the arm scored {min(days)} .. {max(days)}, outside {LO} .. {HI}")
    if len(days) != REPRO_SESSIONS or abs(float(np.sum(arm["net"])) - REPRO_NET) >= 1.0:
        raise GateError(f"[REPRO] {len(days)} sessions, ${float(np.sum(arm['net'])):,.2f} net; "
                        f"D508 recorded {REPRO_SESSIONS} and ${REPRO_NET:,.0f}")
    keep = np.asarray(arm["days_all"]).astype(str) <= HI            # never carry a close past the window
    return {"days": days, "net": np.asarray(arm["net"], float), "gross": np.asarray(arm["gross"], float),
            "trips": np.asarray(arm["trips"], float), "days_all": np.asarray(arm["days_all"]).astype(str)[keep],
            "level_all": np.asarray(arm["level_all"], float)[keep]}


# ------------------------------------------------------------------ statistics
def sharpe(x) -> float:
    x = np.asarray(x, float)
    s = x.std(ddof=1)
    return float(x.mean() / s * math.sqrt(252)) if s > 0 else float("nan")


def sortino(x) -> float:
    x = np.asarray(x, float)
    dn = np.sqrt(np.mean(np.minimum(x, 0.0) ** 2))
    return float(x.mean() / dn * math.sqrt(252)) if dn > 0 else float("nan")


def max_dd(x) -> float:
    eq = np.cumsum(np.asarray(x, float))
    return float(np.max(np.maximum.accumulate(np.concatenate([[0.0], eq]))[1:] - eq))


def apply_pause(net: np.ndarray, paused: np.ndarray) -> np.ndarray:
    out = net.copy()
    out[paused] = 0.0
    return out


def delta(net: np.ndarray, paused: np.ndarray) -> float:
    return sharpe(apply_pause(net, paused)) - sharpe(net)


def qdist(draws: np.ndarray, rng, q: float = 0.95) -> dict:
    boot = np.array([np.quantile(rng.choice(draws, len(draws)), q) for _ in range(BOOT)])
    return {"p05": float(np.quantile(draws, 0.05)), "p50": float(np.quantile(draws, 0.5)),
            "p95": float(np.quantile(draws, 0.95)), "p95_boot_se": float(boot.std(ddof=1)), "draws": int(len(draws))}


# ------------------------------------------------------------------ events and pauses
def merge(idx: list[int], gap: int = MERGE) -> list[int]:
    kept: list[int] = []
    for i in sorted(idx):
        if not kept or i - kept[-1] > gap:
            kept.append(i)
    return kept


def pause_mask(starts: list[int], n: int, length: int = PAUSE) -> np.ndarray:
    """Sessions E+1 .. E+length after each start E (the new margin binds from E+1)."""
    m = np.zeros(n, bool)
    for e in starts:
        m[e + 1: min(n, e + 1 + length)] = True
    return m


def load_events(days: np.ndarray) -> tuple[list[int], np.ndarray, np.ndarray, list[str]]:
    ch = pd.read_csv(CHANGES, encoding="utf-8")
    ch = ch[ch["root"] == ROOT]
    cov = pd.read_csv(COVERAGE, encoding="utf-8")
    cov = cov[cov["root"] == ROOT]
    d = pd.to_datetime(days)
    covered = np.zeros(len(days), bool)
    for _, r in cov.iterrows():
        covered |= (d >= pd.Timestamp(r["from"])) & (d <= pd.Timestamp(r["to"]))
    inc = ch[(ch["pct"] >= MIN_PCT) & (ch["date"] >= LO) & (ch["date"] <= HI)]
    ii = np.searchsorted(days, inc["date"].to_numpy(str), side="left")
    starts = merge([int(i) for i in ii if i < len(days)])
    all_idx = np.searchsorted(days, ch["date"].to_numpy(str), side="left")
    change_idx = np.unique(all_idx[(ch["date"] >= LO).to_numpy() & (ch["date"] <= HI).to_numpy() & (all_idx < len(days))])
    return starts, covered, change_idx, [days[i] for i in starts]


def rotation_null(net: np.ndarray, paused: np.ndarray, covered: np.ndarray) -> np.ndarray:
    """Delta at every cyclic shift k = 1 .. m-1 of the pause mask over the COVERED sessions only (exact)."""
    C = np.nonzero(covered)[0]
    if paused[~covered].any():
        raise GateError("[COVERAGE] a hike pause fell outside the covered sessions")
    mc = paused[C]
    out = np.empty(len(C) - 1)
    for k in range(1, len(C)):
        p = np.zeros(len(net), bool)
        p[C[np.roll(mc, k)]] = True
        out[k - 1] = delta(net, p)
    return out


def vol_state(days: np.ndarray, days_all: np.ndarray, level_all: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Trailing 20-session volatility and return of NQ's daily close, ENDING AT each arm session (inclusive),
    from closes up to and including that session only."""
    r = np.diff(np.log(level_all), prepend=np.nan)
    s = pd.Series(r)
    vol = s.rolling(VOLWIN, min_periods=15).std().to_numpy()
    tr = s.rolling(VOLWIN, min_periods=15).sum().to_numpy()
    pos = pd.Index(days_all).get_indexer(days)
    if (pos < 0).any():
        raise GateError("[VOL] an arm session has no daily close")
    return vol[pos], tr[pos]


def matched_pools(starts: list[int], n: int, covered: np.ndarray, change_idx: np.ndarray, vol: np.ndarray,
                  tr: np.ndarray) -> list[np.ndarray]:
    """Per event: candidate starts s with the state at s-1 in the event's (E-1) volatility quintile and trend sign,
    >= CTRL_GAP sessions from any margin change, and the pause s+1 .. s+PAUSE inside covered sessions."""
    ok = np.isfinite(vol)
    q = np.full(n, np.nan)
    q[ok] = pd.qcut(vol[ok], 5, labels=False, duplicates="drop")
    s = np.arange(n)
    far = np.ones(n, bool) if not len(change_idx) else \
        np.abs(s[:, None] - change_idx[None, :]).min(axis=1) >= CTRL_GAP
    fits = np.array([i >= 1 and i + PAUSE < n and covered[i + 1: i + 1 + PAUSE].all() for i in s])
    pools = []
    for e in starts:
        a = e - 1
        prev = np.clip(s - 1, 0, n - 1)
        m = fits & far & np.isfinite(q[prev]) & (q[prev] == q[a]) & (np.sign(tr[prev]) == np.sign(tr[a]))
        pools.append(s[m])
    return pools


def session_stats(net: np.ndarray, trips: np.ndarray, m: np.ndarray) -> dict:
    x = net[m]
    traded = m & (trips > 0)
    return {"sessions": int(m.sum()), "mean": float(x.mean()) if len(x) else None,
            "sd": float(x.std(ddof=1)) if len(x) > 1 else None, "sum": float(x.sum()),
            "traded_sessions": int(traded.sum()),
            "hit_rate": float((net[traded] > 0).mean()) if traded.any() else None}


def book(x: np.ndarray, gross: np.ndarray, trips: np.ndarray) -> dict:
    pp = p3(x)
    return {"net_sharpe": sharpe(x), "net_sortino": sortino(x), "gross_sharpe": sharpe(gross),
            "gross_sortino": sortino(gross), "net_total": float(x.sum()), "max_dd": max_dd(x), "worst_day": float(x.min()),
            "round_trips": float(trips.sum()), "p3a_breaches_per_year": pp["p3a_breaches_per_year"],
            "p3a_breaches": pp["p3a_breaches"], "p3b_life_cost": pp["p3b_life_cost"]}


# ------------------------------------------------------------------ run
def run() -> int:
    t0 = time.time()
    A = load_arm()
    days, net, gross, trips = A["days"], A["net"], A["gross"], A["trips"]
    n = len(days)
    starts, covered, change_idx, start_days = load_events(days)
    paused = pause_mask(starts, n)
    P(f"arm reproduced: {n} sessions, ${net.sum():,.0f} net; events after merging {len(starts)}: {start_days}; "
      f"paused sessions {int(paused.sum())}; covered sessions {int(covered.sum())}")

    rng = np.random.default_rng(SEED)
    n1 = rotation_null(net, paused, covered)
    n1q = {"p05": float(np.quantile(n1, 0.05)), "p50": float(np.quantile(n1, 0.5)),
           "p95": float(np.quantile(n1, 0.95)), "offsets": int(len(n1))}
    P(f"N1 (exact rotation, {len(n1)} offsets): p05 {n1q['p05']:+.4f} p50 {n1q['p50']:+.4f} p95 {n1q['p95']:+.4f} "
      f"-- the smallest delta distinguishable from chance")

    vol, tr = vol_state(days, A["days_all"], A["level_all"])
    pools = matched_pools(starts, n, covered, change_idx, vol, tr)
    if min(len(p) for p in pools) == 0:
        raise GateError(f"[N2] an event has an empty matched pool: {[len(p) for p in pools]}")
    n2 = np.empty(DRAWS)
    n2_mask_any = np.zeros(n, bool)
    n2_sessions_pooled = []
    for d in range(DRAWS):
        pick = [int(rng.choice(p)) for p in pools]
        m = pause_mask(pick, n)
        n2[d] = delta(net, m)
        n2_mask_any |= m
        n2_sessions_pooled.append(net[m])
    n2q = qdist(n2, rng)

    D = delta(net, paused)
    rank_n1 = float((n1 < D).mean())
    base, pz = book(net, gross, trips), book(apply_pause(net, paused), apply_pause(gross, paused),
                                             np.where(paused, 0.0, trips))
    B = {"B1": D > 0, "B2": D > n1q["p95"], "B3": D > n2q["p95"] + 2 * n2q["p95_boot_se"],
         "B3_unresolved": abs(D - n2q["p95"]) <= 2 * n2q["p95_boot_se"],
         "B4": pz["p3a_breaches_per_year"] <= base["p3a_breaches_per_year"]}
    B["pass"] = bool(B["B1"] and B["B2"] and B["B3"] and B["B4"])

    elsewhere = ~paused
    sp, se_ = session_stats(net, trips, paused), session_stats(net, trips, elsewhere)
    n2x = np.concatenate(n2_sessions_pooled)
    welch_t = (sp["mean"] - se_["mean"]) / math.sqrt(sp["sd"] ** 2 / sp["sessions"] + se_["sd"] ** 2 / se_["sessions"])
    years = sorted({d[:4] for d in days})
    per_year = {}
    for y in years:
        ym = np.array([d[:4] == y for d in days])
        per_year[y] = {"paused_sessions": int((paused & ym).sum()),
                       "delta": sharpe(apply_pause(net, paused)[ym]) - sharpe(net[ym]),
                       "removed_net": float(net[paused & ym].sum())}
    ip = np.nonzero(paused)[0]
    top = ip[np.argmax(np.abs(net[ip]))] if len(ip) else None
    out = {
        "decision_record": "docs/decisions/D667-PRE-REG-margin-hike-pause-on-the-macd-arm.md", "prereg": PREREG,
        "window": [LO, HI], "arm_sessions": n, "arm_net_total": float(net.sum()),
        "events": start_days, "paused_sessions": int(paused.sum()), "covered_sessions": int(covered.sum()),
        "delta_net_sharpe": D, "removed_net_usd": float(net[paused].sum()),
        "base": base, "paused": pz,
        "N1_rotation": {**n1q, "rank_of_delta": rank_n1},
        "N2_vol_matched": {**n2q, "pool_sizes": [int(len(p)) for p in pools]},
        "bars": B,
        "diagnostics": {
            "paused_sessions": sp, "elsewhere": se_,
            "n2_windows_pooled": {"sessions": int(len(n2x)), "mean": float(n2x.mean()), "sd": float(n2x.std(ddof=1))},
            "sd_ratio_paused_to_elsewhere": sp["sd"] / se_["sd"], "welch_t_paused_vs_elsewhere": welch_t,
            "per_year": per_year,
            "largest_paused_session": {"day": days[top], "net": float(net[top])} if top is not None else None,
        },
        "predictions": {
            "1_abs_delta_below_0.10": abs(D) < 0.10, "2_B2_fails": not B["B2"], "3_B3_fails": not B["B3"],
            "4_sd_ratio_at_least_1.2": sp["sd"] / se_["sd"] >= 1.2, "5_mean_not_distinguishable": abs(welch_t) < 2},
        "max_drawdown_convention": {
            "sign": "positive",
            "note": "max_dd is a POSITIVE drawdown in US DOLLARS on the cumulative-sum daily P&L curve at one MNQ "
                    "(peak minus trough), not a fraction of peak.",
            "record": "D542"},
        "wall_min": round((time.time() - t0) / 60, 2),
    }
    OUT.write_text(json.dumps(out, indent=1, default=float), encoding="utf-8", newline="\n")
    P(json.dumps({k: out[k] for k in ("delta_net_sharpe", "removed_net_usd", "bars", "predictions")}, default=str))
    P("base  ", {k: round(v, 4) for k, v in base.items()})
    P("paused", {k: round(v, 4) for k, v in pz.items()})
    P("N2", {k: v for k, v in out["N2_vol_matched"].items() if k != "pool_sizes"}, "N1 rank", round(rank_n1, 4))
    return 0


# ------------------------------------------------------------------ selftest
def selftest() -> int:
    bad = []

    def check(label, cond):
        print(("  ok   " if cond else "  FAIL ") + label)
        if not cond:
            bad.append(label)

    check("merging joins starts within 10 sessions and not beyond", merge([5, 10, 15, 26, 40]) == [5, 26, 40])
    m = pause_mask([3, 20], 40)
    check("the pause covers E+1 .. E+10 exactly", list(np.nonzero(m)[0]) == list(range(4, 14)) + list(range(21, 31)))
    x = np.arange(1.0, 41.0)
    y = apply_pause(x, m)
    check("a paused session is zero and every other session untouched", (y[m] == 0).all() and (y[~m] == x[~m]).all())

    A = load_arm()
    days, net = A["days"], A["net"]
    check(f"the arm reproduces D508 ({REPRO_SESSIONS} sessions, ${REPRO_NET:,.0f}) and scores nothing after {HI}",
          len(days) == REPRO_SESSIONS and abs(net.sum() - REPRO_NET) < 1 and max(days) <= HI)
    starts, covered, change_idx, _ = load_events(days)
    paused = pause_mask(starts, len(days))
    n1 = rotation_null(net, paused, covered)
    check("N1 enumerates every offset except zero", len(n1) == int(covered.sum()) - 1)
    C = np.nonzero(covered)[0]
    k = 37
    p = np.zeros(len(net), bool)
    p[C[np.roll(paused[C], k)]] = True
    check("N1 never places a pause outside covered sessions", not p[~covered].any())
    # N2's state reads no close after the session: perturbing later closes leaves it unchanged
    vol, tr = vol_state(days, A["days_all"], A["level_all"])
    lv = A["level_all"].copy()
    j = int(np.searchsorted(A["days_all"], days[900]))
    lv[j + 1:] *= 1.5
    vol2, tr2 = vol_state(days, A["days_all"], lv)
    check("N2's volatility state reads no close after its session",
          np.allclose(vol[:901], vol2[:901], equal_nan=True) and np.allclose(tr[:901], tr2[:901], equal_nan=True))
    pools = matched_pools(starts, len(days), covered, change_idx, vol, tr)
    s_ok = all((np.abs(pl[:, None] - change_idx[None, :]).min(axis=1) >= CTRL_GAP).all() for pl in pools if len(pl))
    check("N2's pools keep >= 20 sessions from every margin change", s_ok)
    # the primary can fire: pausing the 100 worst sessions beats N1's p95; a random mask sits near N1's median
    worst = np.zeros(len(net), bool)
    cw = C[np.argsort(net[C])[:100]]
    worst[cw] = True
    dw = delta(net, worst)
    rnd = np.zeros(len(net), bool)
    rnd[np.random.default_rng(1).choice(C, int(paused.sum()), replace=False)] = True
    dr = delta(net, rnd)
    check(f"a planted worst-100 mask fires above N1's p95 ({dw:+.3f} > {np.quantile(n1, 0.95):+.3f})",
          dw > np.quantile(n1, 0.95))
    check(f"a planted random mask sits inside N1's p05..p95 ({dr:+.4f})",
          np.quantile(n1, 0.05) <= dr <= np.quantile(n1, 0.95))
    print("SELFTEST", "PASSED" if not bad else f"FAILED: {bad}")
    return 0 if not bad else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.run:
        return run()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
