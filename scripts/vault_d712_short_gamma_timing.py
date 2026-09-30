"""D712: D708's rule for the joint vault run -- the hourly continuation on ES-book short-gamma days, its side choice
(the timing term T) the primary and MES net the second gate. Spec:
docs/decisions/D712-PRE-REG-short-gamma-hourly-timing-for-the-joint-vault.md (968834a5, amended A1 before this runner);
the principal: "Yes, write it".

    uv run python scripts/vault_d712_short_gamma_timing.py --selftest
    uv run python scripts/vault_d712_short_gamma_timing.py --known-answer --data-root "<main>/data"   # D708 + path equality
    uv run python scripts/vault_d712_short_gamma_timing.py --power --data-root "<main>/data"          # s.5
    uv run python scripts/vault_d712_short_gamma_timing.py --freeze                                   # once
    uv run python scripts/vault_d712_short_gamma_timing.py --vault --principals-word "..." --data-root "<main>/data"

THE RULE (s.1): ES sessions with >= 380 one-minute bars (fut_index_sessions) and G_ES < 0 (the ES options book at the
prior settlement, D706's count_slice machinery). At t = 10:30 .. 14:30 on D689's 5-minute grid: m = 1e4 ln(P(t)/P(t-60)),
side s = sign(m) (m = 0 no trade), held 60 minutes; a decision needs finite P(t-60), P(t), P(t+60) and (A1) every grid
price from the open to t. x = (P(t+60) - P(t)) x $5; the drift mu(y, t) = the mean x over every population row at clock t
in year y within the scored span (m = 0 in, the A1 condition not required); tau = s (x - mu); T = mean tau, clustered t.
THE TEST (s.3), on 2024-01-01 -> 2026-09-18: PASS = >= 300 trades, T > 0 with one-sided clustered t >= 1.2816, both legs
> 0 and the MES net mean > 0 ($4.42); MECHANISM ONLY without the net; FAIL otherwise; UNRESOLVED below 300 trades;
promotion at t >= 2.576 (programme slot 10).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d688_gamma_close as S            # noqa: E402  (importing defines, never runs)
import stage0_d708_short_gamma_timing as R     # noqa: E402
import count_d706_vault_short_gamma as C6      # noqa: E402

SPEC = REPO / "docs" / "decisions" / "D712-PRE-REG-short-gamma-hourly-timing-for-the-joint-vault.md"
FROZEN = REPO / "data" / "FROZEN_vault_d712_short_gamma_timing.json"
POWER_OUT = REPO / "data" / "vault_d712_power.json"
VAULT_OUT = REPO / "data" / "vault_d712_short_gamma_timing_result.json"
D708_JSON = REPO / "data" / "d708_short_gamma_timing.json"
HASHED = ("stage0_d688_gamma_close.py", "stage0_d689_short_gamma_continuation.py", "stage0_d708_short_gamma_timing.py",
          "count_d706_vault_short_gamma.py", "stage0_d581_gamma_close.py", "stage0_d685_month_end_rebalancing.py")
IN_FROM, IN_END, UNSEEN_FROM, HELD_END, VAULT_FROM, VAULT_END = "2016-01-04", "2023-12-29", "2024-01-01", "2025-02-28", "2025-03-01", "2026-09-18"
STRIP_FROM = "2015-10-01"
COST, MES_USD = 4.42, 5.0
T_PASS, T_PROMO, MIN_TRADES = 1.2816, 2.576, 300
N_UNSEEN_SESSIONS, WIN_STEP, UNSEEN_MID_ES = 288, 10, 5800.0
CLOCKS, JS, STEP = R.CLOCKS, R.JS, R.STEP


class D712Error(RuntimeError):
    pass


def P(*a, **k):
    print(*a, **k, flush=True)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


# ------------------------------------------------------------------ the rule path (s.1, s.6)
def grid_prices(b: pd.DataFrame, days: np.ndarray) -> np.ndarray:
    """D689's grid: the 09:30 open, then the close of the bar starting one minute before each 5-minute point."""
    close = b.pivot(index="day", columns="hhmm", values="close").reindex(days)
    op = b[b["hhmm"] == "09:30"].set_index("day")["open"].reindex(days).to_numpy(float)
    grid = [(pd.Timestamp("2000-01-01 09:30") + pd.Timedelta(minutes=5 * k)) for k in range(79)]
    cols = [(g - pd.Timedelta(minutes=1)).strftime("%H:%M") for g in grid[1:]]
    return np.column_stack([op] + [close[c].to_numpy(float) if c in close.columns else np.full(len(days), np.nan) for c in cols])


def g_es(data_root: Path, days: np.ndarray, tcal: np.ndarray, lo: str, hi: str, log=P) -> pd.Series:
    """G_ES per session through D706's worker (D688's es_book_prior; the seal on [lo, hi] and the 10:00 OI key asserted)."""
    fx = data_root / "fixtures"
    st = pd.read_csv(fx / "fut_settle_strip.csv.gz", dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8")
    st = st[(st["root"] == "ES") & (st["ref"] >= STRIP_FROM) & (st["ref"] <= hi)].reset_index(drop=True)
    refs = np.array(sorted(st["ref"].unique()))
    strides = [days[i::S.N_WORKERS].tolist() for i in range(S.N_WORKERS)]
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=S.N_WORKERS, initializer=C6._init, initargs=(str(fx), st, tcal, refs, lo, hi)) as ex:
        book = pd.concat(list(ex.map(C6._work, strides))).sort_index()
    log(f"  G_ES rebuilt on {len(book)} sessions {lo} .. {hi} ({time.time() - t0:.0f} s)")
    return book["G_ES"].reindex(days) if "G_ES" in book else pd.Series(np.nan, index=days)


def load_rule(data_root: Path, lo: str, hi: str, vault_open: bool = False, log=P) -> dict[str, Any]:
    if hi >= UNSEEN_FROM and not vault_open:
        raise D712Error(f"[SEAL] a rule-path build to {hi} outside --vault")
    fx = data_root / "fixtures"
    sess = pd.read_csv(fx / "fut_index_sessions.csv.gz", usecols=["root", "day", "bars"], dtype={"root": str, "day": str}, encoding="utf-8")
    cal = np.array(sorted(sess[(sess["root"] == "ES") & (sess["bars"] >= 380)]["day"].unique()))
    tcal = np.array(sorted(sess[sess["root"] == "ES"]["day"].unique()))
    b = pd.read_csv(fx / "fut_ES_rth_1m.csv.gz", usecols=["day", "hhmm", "contract", "open", "close"],
                    dtype={"day": str, "hhmm": str, "contract": str}, encoding="utf-8")
    b = b[(b["day"] >= lo) & (b["day"] <= hi)].reset_index(drop=True)
    if not vault_open and len(b) and b["day"].max() >= UNSEEN_FROM:
        raise D712Error("[SEAL] a bar dated 2024-01-01 or later reached an in-sample build")
    nb = b.groupby("day").size()
    days = np.array([d for d in cal if lo <= d <= hi and nb.get(d, 0) >= 380])
    b = b[b["day"].isin(set(days))].reset_index(drop=True)
    G = g_es(data_root, days, tcal, lo, hi, log)
    PG = grid_prices(b, days)
    log(f"  rule path: {len(days)} sessions {days[0]} .. {days[-1]}; G_ES finite on {int(np.isfinite(G.to_numpy()).sum())}")
    return {"days": days, "PG": PG, "G_ES": G.to_numpy(float), "bars": b}


def rows(PG: np.ndarray) -> dict[str, np.ndarray]:
    """Every decision row with finite P(t-60), P(t), P(t+60) (the drift's rows); `trade` adds m != 0 and A1."""
    nd = PG.shape[0]
    L = np.log(PG)
    out = {k: [] for k in ("di", "ci", "m", "f", "dp", "P", "pre")}
    for c, j in enumerate(JS):
        m = 1e4 * (L[:, j] - L[:, j - STEP]); f = 1e4 * (L[:, j + STEP] - L[:, j]); dp = PG[:, j + STEP] - PG[:, j]
        ok = np.isfinite(m) & np.isfinite(f) & np.isfinite(dp) & np.isfinite(PG[:, j])
        pre = np.isfinite(PG[:, :j + 1]).all(1)
        idx = np.flatnonzero(ok)
        out["di"].append(idx); out["ci"].append(np.full(len(idx), c)); out["m"].append(m[idx]); out["f"].append(f[idx])
        out["dp"].append(dp[idx]); out["P"].append(PG[idx, j]); out["pre"].append(pre[idx])
    A = {k: np.concatenate(v) for k, v in out.items()}
    order = np.lexsort((A["di"], A["ci"]))          # clock-major, day order within a clock (D708's concat order)
    A = {k: v[order] for k, v in A.items()}
    A["x"] = A["dp"] * MES_USD
    A["trade"] = (A["m"] != 0) & A["pre"]
    return A


def score_span(A: dict, days: np.ndarray, pop_day: np.ndarray, lo: str, hi: str, cost: float = COST, shift: float = 0.0) -> dict[str, Any]:
    """The s.1.3 statistic on the population's rows in [lo, hi]; `shift` subtracts a constant from every tau (power only)."""
    in_span = (days >= lo) & (days <= hi)
    pop = pop_day & in_span
    yr_day = np.array([d[:4] for d in days])
    mu = R.drift(A["x"], A["di"], A["ci"], yr_day, pop)
    sel = A["trade"] & pop[A["di"]]
    s = np.sign(A["m"][sel]); x = A["x"][sel]; di = A["di"][sel]; ci = A["ci"][sel]
    tau = R.tau_of(s, x, di, ci, yr_day, mu) - shift
    gross = s * x - shift
    net = gross - cost
    out = {"sessions": int(pop.sum()), "trades": int(sel.sum()), "T": R.cl_mean(tau, di) if len(tau) else {"n": 0},
           "long_leg": R.cl_mean(tau[s > 0], di[s > 0]) if (s > 0).any() else {"n": 0},
           "short_leg": R.cl_mean(tau[s < 0], di[s < 0]) if (s < 0).any() else {"n": 0},
           "net_mes": R.cl_mean(net, di) if len(net) else {"n": 0}, "gross_mes": R.cl_mean(gross, di) if len(gross) else {"n": 0}}
    out["verdict"] = verdict(out)
    out["_arrays"] = {"tau": tau, "s": s, "x": x, "di": di, "ci": ci, "gross": gross, "net": net, "f": A["f"][sel], "P": A["P"][sel]}
    return out


def verdict(o: dict) -> str:
    if o["trades"] < MIN_TRADES:
        return "UNRESOLVED"
    T = o["T"]
    t_ok = T["mean"] > 0 and T["t"] >= T_PASS
    legs = o["long_leg"].get("mean", -1) > 0 and o["short_leg"].get("mean", -1) > 0
    if t_ok and legs:
        return "PASS" if o["net_mes"]["mean"] > 0 else "MECHANISM ONLY"
    return "FAIL"


def strip_arrays(o: dict) -> dict:
    return {k: v for k, v in o.items() if k != "_arrays"}


# ------------------------------------------------------------------ the D708 path (the known answer)
def d708_path(data_root: Path, log=P) -> dict[str, Any]:
    """D708's run, up to its P_ES trades, without writing D708's output."""
    m581 = S.d581(data_root / "fixtures")
    I = S.load_inputs(data_root, log)
    es581 = m581.load_es(lambda *a: None)
    strip_es = I["strip"]
    refs = np.array(sorted(strip_es["ref"].unique()))
    win = [d for d in I["days"] if d >= S.IN_FROM]
    strides = [win[i::S.N_WORKERS] for i in range(S.N_WORKERS)]
    with ProcessPoolExecutor(max_workers=S.N_WORKERS, initializer=S._init, initargs=(str(I["fx"]), es581, strip_es, I["cal"], I["tcal"], refs)) as ex:
        futs = [ex.submit(S._work, (s, [])) for s in strides]
        Dfull = S.build_panel(I, log)
        outs = [f.result() for f in futs]
    prior = pd.concat([o["prior"] for o in outs]).sort_index()
    D = Dfull.join(prior[["G_ES"]], how="left")
    D = D[D.index >= S.IN_FROM]
    D["G_SUM"] = D["G_SPX"] + D["G_ES"]
    need = ["P1530", "P1600", "P1100", "P1130", "P1550", "S_prev", "sig", "V", "G_SPX", "G_ES", "A_L"] + ["P" + t.replace(":", "") for t in S.CLOCK]
    D = D[np.isfinite(D[need].to_numpy(float)).all(1)]
    S.guard_window(D.index, "D712 known-answer panel")
    days = D.index.to_numpy().astype(str)
    b = I["bars"]
    b = b[b["day"].isin(set(days))]
    return {"days": days, "PG": grid_prices(b, days), "G_ES": D["G_ES"].to_numpy(float), "bars": b}


def known_answer(data_root: Path, log=P) -> dict[str, Any]:
    want = json.loads(D708_JSON.read_text(encoding="utf-8"))["populations"]["P_ES"]["T_usd_mes"]
    K = d708_path(data_root, log)
    A8 = rows(K["PG"])
    o8 = score_span(A8, K["days"], K["G_ES"] < 0, IN_FROM, IN_END)
    if not (o8["T"]["n"] == want["n"] and o8["T"]["mean"] == want["mean"] and o8["T"]["t"] == want["t"]):
        raise D712Error(f"[KNOWN] D708's T not reproduced: {strip_arrays(o8)['T']} vs {want}")
    log(f"  D708 REPRODUCED through the runner's rows(): T ${o8['T']['mean']:.10f}, t {o8['T']['t']:.10f}, n {o8['T']['n']}")
    Rr = load_rule(data_root, IN_FROM, IN_END, log=log)
    pos = {d: i for i, d in enumerate(Rr["days"])}
    missing = [d for d in K["days"] if d not in pos]
    if missing:
        raise D712Error(f"[PATH] {len(missing)} D708 panel sessions are not rule-path sessions, e.g. {missing[:3]}")
    ix = np.array([pos[d] for d in K["days"]])
    if not np.array_equal(Rr["G_ES"][ix], K["G_ES"]):
        raise D712Error("[PATH] G_ES differs between the rule path and D708's panel on the panel's sessions")
    if not np.array_equal(Rr["PG"][ix], K["PG"], equal_nan=True):
        raise D712Error("[PATH] the grid prices differ between the rule path and D708's panel")
    on_panel = np.zeros(len(Rr["days"]), bool)
    on_panel[ix] = True
    Ar = rows(Rr["PG"])
    orp = score_span(Ar, Rr["days"], (Rr["G_ES"] < 0) & on_panel, IN_FROM, IN_END)
    if not (orp["T"]["n"] == want["n"] and orp["T"]["mean"] == want["mean"]):
        raise D712Error(f"[PATH] the rule path restricted to D708's panel days gives {strip_arrays(orp)['T']} vs {want}")
    log(f"  PATH EQUALITY: on D708's {len(K['days'])} panel sessions the rule path gives D708's T exactly")
    own = score_span(Ar, Rr["days"], Rr["G_ES"] < 0, IN_FROM, IN_END)
    pop_days = Rr["days"][(Rr["G_ES"] < 0)]
    ka = {"d708_T": want, "rule_path_sessions": int(len(Rr["days"])), "rule_path_extra_sessions_vs_panel": int(len(Rr["days"]) - len(K["days"])),
          "rule_path_in_sample": strip_arrays(own), "population_sessions_sha256": hashlib.sha256("\n".join(pop_days).encode()).hexdigest()}
    log(f"  rule path in-sample (its own {int((Rr['G_ES'] < 0).sum())} population sessions): T ${own['T']['mean']:+.4f} (t {own['T']['t']:+.2f}), "
        f"{own['trades']} trades; legs {own['long_leg']['mean']:+.2f} / {own['short_leg']['mean']:+.2f}; net ${own['net_mes']['mean']:+.2f}; {own['verdict']}")
    # the lag audit (D708's second implementation) on the rule path
    rng = np.random.default_rng(712)
    tr = np.flatnonzero(Ar["trade"])
    sample = rng.choice(tr, 40, replace=False)
    need = set(Rr["days"][Ar["di"][sample]])
    bb = Rr["bars"][Rr["bars"]["day"].isin(need)]
    by = {d: {"open": dict(zip(g["hhmm"], g["open"])), "close": dict(zip(g["hhmm"], g["close"]))} for d, g in bb.groupby("day")}
    R.lag_audit(by, Rr["days"], Rr["PG"], np.sign(Ar["m"]), Ar["di"], Ar["ci"], sample, log)
    return {"ka": ka, "rule": Rr, "A": Ar, "own": own}


# ------------------------------------------------------------------ power (s.5)
def cluster_t(tsum: np.ndarray, n: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Rows = draws, columns = sessions: the pooled mean and its CR1 clustered t (clusters = sessions)."""
    N = n.sum(1)
    m = tsum.sum(1) / N
    u = tsum - n * m[:, None]
    G = tsum.shape[1]
    se = np.sqrt((u * u).sum(1) / (N * N) * G / (G - 1))
    return m, m / se


def power(data_root: Path, KA: dict | None = None, log=P) -> dict[str, Any]:
    KA = KA or known_answer(data_root, log)
    own, Rr, Ar = KA["own"], KA["rule"], KA["A"]
    a = own["_arrays"]
    T_in = own["T"]["mean"]
    days = Rr["days"]
    pop_idx = np.flatnonzero(Rr["G_ES"] < 0)
    loc = {d: i for i, d in enumerate(pop_idx)}
    k = np.array([loc[d] for d in a["di"]])
    nP = len(pop_idx)
    gbp = a["s"] * a["f"]
    T_bp = float((a["tau"] / (a["P"] * MES_USD * 1e-4)).mean())

    def sums(w, mask=None):
        mm = np.ones(len(w), bool) if mask is None else mask
        return np.bincount(k[mm], weights=w[mm], minlength=nP), np.bincount(k[mm], minlength=nP).astype(float)
    rng = np.random.default_rng(7121)
    draws = rng.integers(0, nP, (20000, N_UNSEEN_SESSIONS))
    lines = {}
    for frac in (1.0, 0.5, 0.25, 0.0):
        sh = (1 - frac) * T_in
        tt, nn = sums(a["tau"] - sh)
        tl, nl = sums(a["tau"] - sh, a["s"] > 0)
        ts, ns = sums(a["tau"] - sh, a["s"] < 0)
        gb, _ = sums(gbp - (1 - frac) * T_bp)
        m, t = cluster_t(tt[draws], nn[draws])
        leg_l = tl[draws].sum(1) / np.maximum(nl[draws].sum(1), 1)
        leg_s = ts[draws].sum(1) / np.maximum(ns[draws].sum(1), 1)
        net_proj = gb[draws].sum(1) / nn[draws].sum(1) * UNSEEN_MID_ES * MES_USD * 1e-4 - COST
        t_ok = (m > 0) & (t >= T_PASS)
        both = t_ok & (leg_l > 0) & (leg_s > 0)
        lines[f"{int(frac * 100)}pct"] = {"T_condition": float(t_ok.mean()), "T_and_legs": float(both.mean()),
                                          "PASS_with_net_at_es_5800": float((both & (net_proj > 0)).mean()),
                                          "promotion": float(((m > 0) & (t >= T_PROMO)).mean()),
                                          "mean_trades": float(nn[draws].sum(1).mean())}
    size = lines["0pct"]["T_condition"]
    # contiguous windows of 288 population sessions, the full rule (drift re-estimated within the window by year)
    starts = list(range(0, nP - N_UNSEEN_SESSIONS + 1, WIN_STEP))
    win = {}
    for frac in (1.0, 0.5, 0.25, 0.0):
        res = []
        for st_ in starts:
            lo, hi = days[pop_idx[st_]], days[pop_idx[st_ + N_UNSEEN_SESSIONS - 1]]
            res.append(score_span(Ar, days, Rr["G_ES"] < 0, lo, hi, shift=(1 - frac) * T_in)["verdict"])
        win[f"{int(frac * 100)}pct"] = {k_: float(np.mean([r == k_ for r in res])) for k_ in ("PASS", "MECHANISM ONLY", "FAIL", "UNRESOLVED")}
    out = {"effect_T_in_sample_rule_path": T_in, "T_bp": T_bp, "population_sessions_in_sample": nP,
           "size_check": {"draws": 20000, "sessions_a_draw": N_UNSEEN_SESSIONS, "T_condition_rate_at_zero": size, "bar": 0.12, "ok": bool(size <= 0.12)},
           "resampled_lines": lines, "net_projection": f"gross bp x $ a bp at ES {UNSEEN_MID_ES:.0f} (the unseen span's approximate mid) against ${COST}",
           "windows": {"sessions_a_window": N_UNSEEN_SESSIONS, "step": WIN_STEP, "count": len(starts), "independent_approx": round(nP / N_UNSEEN_SESSIONS, 2), "lines": win},
           "note": "the windows overlap, and the 0% line shows time concentration, not the test's size (s.5)"}
    log(f"  POWER: size {size:.3f} (bar 0.12); " + "; ".join(f"{k_} T {v['T_condition']:.2f} T+legs {v['T_and_legs']:.2f} PASS(net) {v['PASS_with_net_at_es_5800']:.2f} promo {v['promotion']:.2f}" for k_, v in lines.items()))
    log("  WINDOWS: " + "; ".join(f"{k_} PASS {v['PASS']:.2f} MECH {v['MECHANISM ONLY']:.2f}" for k_, v in win.items()))
    return out


# ------------------------------------------------------------------ the unseen span (the joint run only)
def report(o: dict, days: np.ndarray, A: dict, G: np.ndarray, lo: str, hi: str) -> dict[str, Any]:
    a = o["_arrays"]
    yr = np.array([days[d][:4] for d in a["di"]])
    net = a["net"]
    E = S.d685()
    arm = E.load_arm()
    nd = len(days)
    four = {}
    for lab, cs in (("mes", E.cost_spec("ES", "micro")), ("es_full", E.cost_spec("ES", "full"))):
        gr = a["s"] * (a["x"] / MES_USD) * cs["usd_per_point"]
        four[lab] = R.Q.four_groups(gr, gr - cs["cost_rt_usd"], a["di"], a["s"], days, nd, arm, cs["cost_rt_usd"])
    by_year_net = {y: float(net[yr == y].sum()) for y in sorted(set(yr))}
    tot = sum(by_year_net.values())
    lg = score_span(A, days, G >= 0, lo, hi)
    return {"four_groups": four, "T_by_year": {y: R.cl_mean(a["tau"][yr == y], a["di"][yr == y]) for y in sorted(set(yr))},
            "T_by_clock": {CLOCKS[c]: R.cl_mean(a["tau"][a["ci"] == c], a["di"][a["ci"] == c]) for c in range(len(CLOCKS))},
            "largest_year_share_of_dollar_net": (max(by_year_net.values()) / tot) if tot > 0 else None, "by_year_net_mes": by_year_net,
            "price": {"gross_bp": float((a["s"] * a["f"]).mean()), "mean_es": float(a["P"].mean()),
                      "round_trip_bp": float(COST / (MES_USD * a["P"].mean()) * 1e4)},
            "long_gamma_contrast": strip_arrays(lg),
            "long_gamma_qualifier": "(not gamma-specific)" if lg["T"].get("mean", -1e9) >= o["T"]["mean"] else None,
            "rho_with_f2": "not computed: F2's unseen daily series is D707's own vault output"}


def vault(word: str | None, data_root: Path) -> int:
    if not (word or "").strip():
        print("refused: the vault is read only in the joint run, on the principal's word (A10; D712 s.6)")
        return 2
    if not FROZEN.exists():
        raise D712Error("the D712 freeze is missing")
    fz = json.loads(FROZEN.read_text(encoding="utf-8"))
    if fz.get("runner_sha256") != sha(Path(__file__).resolve()) or fz.get("prereg_sha256") != sha(SPEC):
        raise D712Error("this runner or D712 has moved since the freeze")
    for p, h in fz["imported_unchanged"].items():
        if sha(REPO / "scripts" / p) != h:
            raise D712Error(f"{p} has moved since the freeze")
    if VAULT_OUT.exists():
        raise D712Error("D712's unseen span has already been scored; a second opening is refused")
    R.sign_audit(MES_USD)
    Rr = load_rule(data_root, IN_FROM, VAULT_END, vault_open=True)
    A = rows(Rr["PG"])
    days, G = Rr["days"], Rr["G_ES"]
    # prefix stability: the extended build's in-sample part reproduces the frozen known answer before any unseen trade
    ins = score_span(A, days, G < 0, IN_FROM, IN_END)
    want = fz["known_answer"]["rule_path_in_sample"]
    pop_in = days[(G < 0) & (days <= IN_END)]
    if ins["trades"] != want["trades"] or ins["T"]["mean"] != want["T"]["mean"] or \
            hashlib.sha256("\n".join(pop_in).encode()).hexdigest() != fz["known_answer"]["population_sessions_sha256"]:
        raise D712Error(f"prefix stability: the extended build's in-sample part {strip_arrays(ins)['T']} differs from the frozen {want['T']}")
    o = score_span(A, days, G < 0, UNSEEN_FROM, VAULT_END)
    promo = bool(o["T"].get("mean", -1) > 0 and o["T"].get("t", 0) >= T_PROMO)
    out = {"principals_word": word, "prefix_stability": "reproduced", "verdict": o["verdict"], "programme_promotion": promo,
           "span": strip_arrays(o),
           "parts": {nm: strip_arrays(score_span(A, days, G < 0, lo, hi)) for nm, lo, hi in (("held_slice", UNSEEN_FROM, HELD_END), ("vault", VAULT_FROM, VAULT_END))},
           "report": report(o, days, A, G, UNSEEN_FROM, VAULT_END), "last_session_in_fixture": str(days[-1])}
    VAULT_OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: out[k] for k in ("verdict", "programme_promotion", "last_session_in_fixture")}, indent=1, default=float))
    return 0


def freeze() -> int:
    if FROZEN.exists():
        raise D712Error(f"{FROZEN.name} exists; a freeze is written once (a change needs a new record)")
    pw = json.loads(POWER_OUT.read_text(encoding="utf-8"))
    if not pw["power"]["size_check"]["ok"]:
        raise D712Error("the size check failed (s.5): nothing is frozen; the principal is told")
    doc = {"spec": SPEC.name, "prereg_sha256": sha(SPEC), "runner": "scripts/vault_d712_short_gamma_timing.py",
           "runner_sha256": sha(Path(__file__).resolve()), "imported_unchanged": {p: sha(REPO / "scripts" / p) for p in HASHED},
           "params": {"clocks": CLOCKS, "hold_minutes": 60, "grid": "D689 5-minute", "population": "G_ES < 0 (D706 count_slice machinery)",
                      "sessions": ">= 380 one-minute bars (fut_index_sessions) and >= 380 in the bar file", "A1": "every grid price from the open to t finite",
                      "drift": "mean x per (calendar year, clock) over the scored span's population rows, m = 0 in", "cost_usd_round_trip": COST,
                      "size": "one MES", "t_pass": T_PASS, "t_promotion": T_PROMO, "min_trades": MIN_TRADES, "se": "day-clustered (statsmodels cluster)"},
           "known_answer": pw["known_answer"], "power": pw["power"], "unseen": [UNSEEN_FROM, VAULT_END], "programme_slot": 10,
           "frozen_date": time.strftime("%Y-%m-%d"), "instruction": "the principal, 2026-09-30: \"Yes, write it\" (D708 to the joint vault run)"}
    FROZEN.write_text(json.dumps(doc, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: doc[k] for k in ("prereg_sha256", "runner_sha256", "imported_unchanged")}, indent=1))
    return 0


# ------------------------------------------------------------------ selftest
def selftest() -> int:
    fired: list[str] = []

    def must_raise(name, fn, exc=(D712Error,)):
        try:
            fn()
        except exc:
            fired.append(name)
            return
        raise SystemExit(f"selftest: the {name} canary did not raise")
    R.selftest()                                           # D708's statistic, lag and sign canaries
    rng = np.random.default_rng(712)
    # a synthetic rule-path book: 400 sessions x 5 clocks
    nd = 400
    days = np.array([str(pd.Timestamp("2024-01-02") + pd.Timedelta(days=i))[:10] for i in range(nd)])
    PG = 5000 * np.exp(np.cumsum(rng.normal(0, 8e-4, (nd, 79)), axis=1))
    A = rows(PG)
    pop = np.ones(nd, bool)
    base = score_span(A, days, pop, days[0], days[-1])
    if base["trades"] < MIN_TRADES:
        raise SystemExit("selftest: the synthetic book is too small")
    # an injected timing effect: move each outcome toward the side of the last hour
    PGe = PG.copy()
    for c, j in enumerate(JS):
        s = np.sign(np.log(PGe[:, j]) - np.log(PGe[:, j - STEP]))
        PGe[:, j + 1:] *= np.exp(s * 25e-4)[:, None]
    inj = score_span(rows(PGe), days, pop, days[0], days[-1], cost=0.0)
    if inj["verdict"] != "PASS":
        raise SystemExit(f"selftest: an injected timing effect did not PASS ({inj['verdict']}, T {inj['T']})")
    if score_span(A, days, pop, days[0], days[20])["verdict"] != "UNRESOLVED":
        raise SystemExit("selftest: fewer than 300 trades did not read UNRESOLVED")
    # noise: the T condition's rate over synthetic random walks
    hits = 0
    for i in range(200):
        Pn = 5000 * np.exp(np.cumsum(rng.normal(0, 8e-4, (nd, 79)), axis=1))
        o = score_span(rows(Pn), days, pop, days[0], days[-1])
        hits += o["T"]["mean"] > 0 and o["T"]["t"] >= T_PASS
    rate = hits / 200
    if not 0.04 <= rate <= 0.18:
        raise SystemExit(f"selftest: noise met the T condition {rate:.3f} of the time (about 0.10 expected)")
    # a pure drift book: every hour rises; T must not pass while the raw mean does
    PGd = PG * np.exp(np.arange(79) * 3e-4)[None, :]
    od = score_span(rows(PGd), days, pop, days[0], days[-1], cost=0.0)
    if od["T"]["t"] >= T_PASS and od["T"]["mean"] > 0:
        raise SystemExit("selftest: a pure drift passed the T condition")
    # A1: a missing earlier grid price drops the decision from the trades, not from the drift's rows
    PG1 = PG.copy(); PG1[0, 3] = np.nan
    A1 = rows(PG1)
    r0 = (A1["di"] == 0) & (A1["ci"] == 0)
    if not (r0.any() and not A1["trade"][r0].any()):
        raise SystemExit("selftest: A1 did not drop a decision with a missing earlier grid price")
    # the seal and the vault gate
    must_raise("a rule-path build past 2023-12-29 outside --vault", lambda: load_rule(REPO / "data", IN_FROM, VAULT_END))
    if main(["--vault"]) != 2:
        raise SystemExit("selftest: --vault ran without the principal's word")
    # the gamma label's 10:00 key: a publication shifted a day later must fail D688's oi_keyed
    fake = pd.DataFrame({"session": ["2020-01-02"], "oi_pub_et": ["2020-01-02 09:00"]})
    if not S.oi_keyed(fake, 0) or S.oi_keyed(fake, 1):
        raise SystemExit("selftest: the OI key check cannot tell a same-session 09:00 publication from a next-day one")
    # the power's clustered t equals statsmodels' on one draw
    tau = rng.normal(0.5, 60, 900); di = np.repeat(np.arange(180), 5)
    ref = R.cl_mean(tau, di)
    ts = np.bincount(di, weights=tau); ns = np.bincount(di).astype(float)
    m, t = cluster_t(ts[None, :], ns[None, :])
    if not (math.isclose(m[0], ref["mean"], rel_tol=1e-12) and math.isclose(t[0], ref["t"], rel_tol=1e-6)):
        raise SystemExit(f"selftest: cluster_t {t[0]!r} differs from statsmodels' {ref['t']!r}")
    print(f"selftest OK: D708's canaries; {len(fired)} canaries fired {fired}; an injected timing effect PASSes; noise met the T "
          f"condition {rate:.3f}; a pure drift fails it; UNRESOLVED below 300; A1 drops the decision; --vault refused without the "
          "word; cluster_t == statsmodels. D708's known answer and the path equality need the fixtures and run in --known-answer.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--known-answer", action="store_true")
    ap.add_argument("--power", action="store_true")
    ap.add_argument("--freeze", action="store_true")
    ap.add_argument("--vault", action="store_true")
    ap.add_argument("--principals-word", default=None)
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.freeze:
        return freeze()
    if a.vault:
        return vault(a.principals_word, a.data_root)
    if a.known_answer or a.power:
        KA = known_answer(a.data_root)
        out = {"known_answer": KA["ka"]}
        if a.power:
            out["power"] = power(a.data_root, KA)
        POWER_OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
        P(f"  wrote {POWER_OUT.relative_to(REPO)}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
