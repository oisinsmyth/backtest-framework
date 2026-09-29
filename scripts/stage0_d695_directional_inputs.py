"""D695 STAGE 0 -- three new directional inputs for the short-gamma long continuation, ranked continuously at MES (the
principal, 2026-09-29: "Look for a new directional input"; then "A, B and C, continuous ranking, 2016-2023 only").

    uv run python scripts/stage0_d695_directional_inputs.py --run --data-root "<main checkout>/data"

In-sample on D688's panel, 2016-01-05 -> 2023-12-29; nothing on or after 2024-01-01 is read. No filter is fitted: each
input is a raw score with a direction DECLARED HERE, ranked against the trade's MES outcome. The filter is designed
with the principal afterwards.

THE UNIVERSE (D693's): G_SUM < 0 (SPX GEX + the ES options book at the prior settlement), the last 60 minutes up; buy
1 MES at t in {10:30, 11:30, 12:30, 13:30, 14:30}, sell 60 minutes later. Outcome: net = gross - $4.42; the oracle
label: net > 0. The last hour is the minutes labelled t-60 .. t-1 (the D462 bar convention, as the move m).

THE INPUTS (a higher score is declared BETTER for the long trade):
  A  ORDER FLOW (the fixture fut_ES_signed_1m, Sierra aggressor side; VOID if its declared validation failed)
     A1  (buy - sell) / volume over the last hour. Mechanism: a rise driven by aggressive buying (dealers hedging with
         market orders on a short-gamma day, a metaorder being worked) is still running and continues.
     A2  (buy - sell) over the last hour / the median volume of the same hour over the prior 20 sessions (the flow's
         size, normalised prior-only).
     A3  (buy - sell) / volume over the last 15 minutes (is the flow still running at t?).
  B  BREADTH across the index futures (fut_NQ/RTY/YM_rth_1m, the same minutes)
     B1  how many of NQ, RTY, YM also rose over the last hour (0 .. 3). Mechanism: index-wide hedging and macro flow
         are broad and continue; an ES-only rise is idiosyncratic.
     B2  the mean of their last-hour log returns, each divided by that root's standard deviation of 60-minute returns
         over the prior 20 sessions.
  C  WHERE THE PRICE SITS IN THE GAMMA PROFILE (the ES options book, D688's construction, re-evaluated at the decision)
     G_ES(t): the same options (D688's mask), gamma at F = F_prev x P(t)/S_prev (the front's move since the prior
     settlement) and tau = (sessions to expiry x 6.5 h + the hours left to 16:00) / (252 x 6.5); iv held at the prior
     settlement's. SPX GEX has no strikes, so it is held fixed.
     C1  -(G_SPX + G_ES(t)): how short gamma the dealers are NOW. More short -> more amplification -> better.
     C2  -(G_ES(t) - G_ES(prior settlement)): how much the move so far has made them shorter. Mechanism: a rise that
         carries the price toward long-gamma territory weakens the amplification.

DECLARED STATISTICS, per input, on the universe:
  - Spearman (score, net) -- the partial-oracle curve's axis; the target D693's curve set is about 0.05
  - AUC against the oracle label (net > 0)
  - the curve's net Sharpe at that Spearman (the partial-oracle curve on this universe, q = 50 %, 200 draws)
  - the enumerated day-rotation null of the Spearman (k = 10 .. n-10: the score grid rotated across days against the
    outcome grid), its p05/p50/p95 and percentile; and the FAMILY null: for each rotation, the max over the 7 scores
  - terciles of the score (full-sample edges; descriptive): n, mean net, win rate
READING (declared): an input CARRIES DIRECTION if its Spearman > 0 and above its own rotation p95; it SURVIVES THE
FAMILY if above the family-max p95; it is WORTH A FILTER if, in addition, its Spearman >= 0.05.
AUDITS: G_ES re-evaluated at the prior settlement (scale 1, tau from the settlement) must equal D688's G_ES exactly;
the rotation's k = 0 must reproduce each observed Spearman; every loader cuts at 2024-01-01.

Output data/d695_directional_inputs.json: statistics only, no per-date GEX (SqueezeMetrics, under the permission of
2026-09-28).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import diag_d692_oracle_profile_mes as B  # noqa: E402  (importing defines, never runs)
import stage0_d688_gamma_close as S  # noqa: E402

from backtest_framework.validation import filter_oracle as FO  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "d695_directional_inputs.json"
SLOT_T = ("10:30", "11:30", "12:30", "13:30", "14:30")
HOURS_LEFT = (5.5, 4.5, 3.5, 2.5, 1.5)
TRAIL = 20
RHOS = (0.0, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2)
N_DRAW = 200
SEED = 695
SCORES = ("A1", "A2", "A3", "B1", "B2", "C1", "C2")


def P(*a, **k):
    print(*a, **k, flush=True)


# ------------------------------------------------------------------ C: the gamma profile at the decision (process workers)
_W: dict = {}


def _init(fx, strip_es, tcal, refs, scales):
    _W.update(m=S.d581(Path(fx)), fx=Path(fx), strip=strip_es, tcal=tcal, refs=refs, scales=scales)


def gamma_path(g, d, m, settle, tcal, refs, scale5):
    """G_ES at the prior settlement (D688's es_book_prior arithmetic) and at the five decision times."""
    calx = {x: i for i, x in enumerate(tcal)}
    i = calx[d]
    prev = refs[np.searchsorted(refs, d) - 1]
    und = g["underlying"].to_numpy()
    fmap = {u: settle.get((prev, u), np.nan) for u in pd.unique(und)}
    Fp = np.array([fmap[u] for u in und], float)
    K = g["strike"].to_numpy(float); right = g["right"].to_numpy(); oi = g["oi"].to_numpy(float)
    e = g["expiry_date"].to_numpy().astype(str)
    n_ahead = np.searchsorted(tcal, e) - i
    same_day = n_ahead == 0
    exp_ok = ~same_day | (g["expiry_hhmm"].to_numpy().astype(str) >= S.T_ENTRY)
    tau = (n_ahead * S.HOURS + S.HOURS) / S.YEAR_HOURS
    px = g["settle"].to_numpy(float)
    fin = np.isfinite(px) & np.isfinite(Fp)
    mk = fin & (e >= d) & exp_ok & (oi > 0)
    mk &= np.abs(K / np.where(fin, Fp, 1.0) - 1) < S.MONEYNESS_MAX
    iv = np.full(len(g), np.nan)
    iv[mk] = m.implied_vol(px[mk], Fp[mk], K[mk], tau[mk], right[mk])
    ok = np.isfinite(iv)
    sgn = np.where(right[ok] == "C", 1.0, -1.0)
    Fo, Ko, ivo, oio, na = Fp[ok], K[ok], iv[ok], oi[ok], n_ahead[ok]
    g0 = float((m.b76_gamma(Fo, Ko, ivo, tau[ok]) * sgn * oio * S.MULT * Fo * Fo * 0.01).sum())
    gt = np.full(5, np.nan)
    for s in range(5):
        sc = scale5[s]
        if not np.isfinite(sc):
            continue
        F = Fo * sc
        tt = (na * S.HOURS + HOURS_LEFT[s]) / S.YEAR_HOURS
        gt[s] = float((m.b76_gamma(F, Ko, ivo, tt) * sgn * oio * S.MULT * F * F * 0.01).sum())
    return g0, gt


def _work(mine):
    mine = set(mine)
    parts = []
    for ch in pd.read_csv(_W["fx"] / "fut_es_options_eod.csv.gz", usecols=S.OPT_COLS, dtype=S.OPT_DTYPE, chunksize=S.CHUNK, encoding="utf-8"):
        ch = ch[ch["session"].isin(mine)]
        if len(ch):
            parts.append(ch)
    opts = pd.concat(parts, ignore_index=True)
    S.guard_window(opts["session"], "options")
    settle = _W["strip"].set_index(["ref", "contract"])["settle"]
    out = {}
    for d, g in opts.groupby("session", sort=True):
        if d not in _W["scales"]:
            continue
        out[d] = gamma_path(g, d, _W["m"], settle, _W["tcal"], _W["refs"], _W["scales"][d])
    return out


# ------------------------------------------------------------------ helpers
def price_grid(fx: Path, root: str, days: np.ndarray) -> np.ndarray:
    """days x 79: the price at 09:30, 09:35, ..., 16:00 (09:30 = the open; otherwise the close of the bar a minute before)."""
    b = pd.read_csv(fx / f"fut_{root}_rth_1m.csv.gz", usecols=["day", "hhmm", "open", "close"], dtype={"day": str, "hhmm": str}, encoding="utf-8")
    b = b[(b["day"] >= S.IN_FROM) & (b["day"] < S.CUTOFF) & b["day"].isin(set(days))]
    S.guard_window(b["day"], f"{root} bars")
    close = b.pivot_table(index="day", columns="hhmm", values="close", aggfunc="first").reindex(days)
    op = b[b["hhmm"] == "09:30"].groupby("day")["open"].first().reindex(days).to_numpy(float)
    grid = [(pd.Timestamp("2000-01-01 09:30") + pd.Timedelta(minutes=5 * k)) for k in range(79)]
    cols = [op] + [close[(g - pd.Timedelta(minutes=1)).strftime("%H:%M")].to_numpy(float) if (g - pd.Timedelta(minutes=1)).strftime("%H:%M") in close else np.full(len(days), np.nan) for g in grid[1:]]
    return np.column_stack(cols)


def rotation_spearman(score_grid, net_grid, uni_grid, ks):
    """For each rotation k of the score grid across days: Spearman(score, net) over universe cells with a finite score."""
    out = np.full(len(ks), np.nan)
    for a, k in enumerate(ks):
        sc = np.roll(score_grid, int(k), axis=0)
        mk = uni_grid & np.isfinite(sc)
        if mk.sum() > 30 and np.ptp(sc[mk]) > 0:
            out[a] = FO.spearman(sc[mk], net_grid[mk])
    return out


def run(data_root: Path, log=P) -> int:
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    fx = data_root / "fixtures"
    T, nd = B.build(data_root, log)                                      # D692's candidates (D688 reproduced inside)
    days = np.array(sorted(set(T["day"])))
    E = S.d685()
    mes = E.cost_spec("ES", "micro")
    cost = mes["cost_rt_usd"]
    di = T["di"].to_numpy(); slot = T["slot"].to_numpy(); m = T["m"].to_numpy()
    side = np.sign(m)
    net = side * T["dp"].to_numpy() * mes["usd_per_point"] - cost
    uni = (T["G_SUM"].to_numpy() < 0) & (side > 0)
    res = {"spec": "D695 STAGE 0 (in-sample; three directional inputs ranked at MES; no filter fitted)", "cost_rt_usd": cost,
           "universe": {"rows": int(uni.sum()), "per_year": float(uni.sum()) / (nd / 252.0), "win_rate": float((net[uni] > 0).mean()), "mean_net": float(net[uni].mean())}}
    log(f"  universe: {int(uni.sum())} trades ({res['universe']['per_year']:.0f}/yr), win {res['universe']['win_rate']:.3f}, mean net ${res['universe']['mean_net']:+.2f}")
    scores = {s: np.full(len(T), np.nan) for s in SCORES}

    # ---- A: order flow ----
    meta = json.loads((fx / "fut_ES_signed_1m.meta.json").read_text(encoding="utf-8"))
    a_valid = bool(meta["validation"]["pass"])
    res["A_fixture_validation"] = meta["validation"]
    fl = pd.read_csv(fx / "fut_ES_signed_1m.csv.gz", usecols=["day", "hhmm", "volume", "buy", "sell"], dtype={"day": str, "hhmm": str}, encoding="utf-8")
    fl = fl[(fl["day"] < S.CUTOFF) & fl["day"].isin(set(days))]
    S.guard_window(fl["day"], "ES signed flow")
    mins = [(pd.Timestamp("2000-01-01 09:30") + pd.Timedelta(minutes=k)).strftime("%H:%M") for k in range(390)]
    V = fl.pivot_table(index="day", columns="hhmm", values="volume", aggfunc="sum").reindex(index=days, columns=mins).fillna(0.0).to_numpy()
    NB = (fl.assign(nb=fl["buy"] - fl["sell"]).pivot_table(index="day", columns="hhmm", values="nb", aggfunc="sum").reindex(index=days, columns=mins).fillna(0.0).to_numpy())
    has_day = np.isin(days, fl["day"].unique())
    vol_hour = np.full((nd, 5), np.nan); nb_hour = np.full((nd, 5), np.nan); nb_15 = np.full((nd, 5), np.nan); vol_15 = np.full((nd, 5), np.nan)
    for s, t in enumerate(SLOT_T):
        j = mins.index(t)
        vol_hour[:, s] = V[:, j - 60:j].sum(1); nb_hour[:, s] = NB[:, j - 60:j].sum(1)
        vol_15[:, s] = V[:, j - 15:j].sum(1); nb_15[:, s] = NB[:, j - 15:j].sum(1)
    vol_hour[~has_day] = np.nan; vol_15[~has_day] = np.nan
    med_prior = pd.DataFrame(vol_hour).rolling(TRAIL).median().shift(1).to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        A1 = nb_hour / vol_hour; A2 = nb_hour / med_prior; A3 = nb_15 / vol_15
    scores["A1"] = A1[di, slot]; scores["A2"] = A2[di, slot]; scores["A3"] = A3[di, slot]

    # ---- B: breadth across NQ, RTY, YM ----
    step = 12
    rets = {}
    for root in ("NQ", "RTY", "YM"):
        PGx = price_grid(fx, root, days)
        r60 = np.full((nd, 5), np.nan)
        for s in range(5):
            jj = 12 * (s + 1)
            r60[:, s] = 1e4 * np.log(PGx[:, jj] / PGx[:, jj - step])
        # the prior 20 sessions' standard deviation of 60-minute returns (all five slots pooled), prior-only
        pooled = np.array([np.nanstd(r60[max(0, i - TRAIL):i].ravel(), ddof=1) if i >= TRAIL else np.nan for i in range(nd)])
        rets[root] = (r60, pooled)
    up = np.zeros((nd, 5)); zs = np.zeros((nd, 5)); okb = np.ones((nd, 5), bool)
    for root, (r60, pooled) in rets.items():
        okb &= np.isfinite(r60) & np.isfinite(pooled)[:, None]
        up += (r60 > 0)
        zs += r60 / pooled[:, None]
    B1g = np.where(okb, up, np.nan); B2g = np.where(okb, zs / 3.0, np.nan)
    scores["B1"] = B1g[di, slot]; scores["B2"] = B2g[di, slot]

    # ---- C: the gamma profile at the decision ----
    scale_grid = np.full((nd, 5), np.nan)
    scale_grid[di, slot] = np.exp(T["rt"].to_numpy() / 100.0)
    need_days = sorted(set(days[di[uni]]))                               # the universe's sessions only
    scales = {d: scale_grid[np.searchsorted(days, d)] for d in need_days}
    I = S.load_inputs(data_root, lambda *a: None)
    strip_es = I["strip"]
    refs = np.array(sorted(strip_es["ref"].unique()))
    strides = [need_days[i::S.N_WORKERS] for i in range(S.N_WORKERS)]
    tc = time.time()
    with ProcessPoolExecutor(max_workers=S.N_WORKERS, initializer=_init, initargs=(str(fx), strip_es, I["tcal"], refs, scales)) as ex:
        gp = {}
        for part in ex.map(_work, strides):
            gp.update(part)
    log(f"  gamma profile on {len(gp)} short-gamma sessions in {time.time() - tc:.0f} s")
    g_es_panel = T.groupby("day")["G_ES"].first()
    for d, (g0, _) in gp.items():
        if g0 != g_es_panel[d]:
            raise S.GateError(f"[AUDIT] {d}: G_ES at the prior settlement {g0!r} is not D688's {g_es_panel[d]!r}")
    res["audits"] = {"g_es_prior_equals_d688": len(gp)}
    Gt = np.full((nd, 5), np.nan); G0 = np.full(nd, np.nan)
    for d, (g0, gt) in gp.items():
        i = np.searchsorted(days, d)
        Gt[i] = gt; G0[i] = g0
    gspx = T.groupby("di")["G_SPX"].first().reindex(range(nd)).to_numpy()
    scores["C1"] = -(gspx[di] + Gt[di, slot])
    scores["C2"] = -(Gt[di, slot] - G0[di])

    # ---- the ranking ----
    nslot = 5
    net_grid = np.full((nd, nslot), np.nan); uni_grid = np.zeros((nd, nslot), bool)
    net_grid[di[uni], slot[uni]] = net[uni]; uni_grid[di[uni], slot[uni]] = True
    ks = S.rot_ks(nd)
    # the partial-oracle curve on the universe
    nu, du = net[uni], di[uni]
    z = FO.normal_scores(nu)
    curve = []
    for rho in RHOS:
        sh, sp = [], []
        for _ in range(N_DRAW):
            s_ = FO._partial(z, rho, rng)
            keep = FO.top_fraction(s_, 0.5)
            dd = np.bincount(du[keep], weights=nu[keep], minlength=nd)
            sd_ = dd.std(ddof=1)
            sh.append(dd.mean() / sd_ * math.sqrt(252) if sd_ > 0 else np.nan); sp.append(FO.spearman(s_, nu))
        curve.append({"rho": rho, "net_sharpe_mean": float(np.nanmean(sh)), "spearman_mean": float(np.mean(sp))})
    res["curve_q50"] = curve
    cx = np.array([c["spearman_mean"] for c in curve]); cy = np.array([c["net_sharpe_mean"] for c in curve])
    log("  curve (q 50%): " + " ".join(f"sp {x:+.3f}->{y:+.2f}" for x, y in zip(cx, cy)))
    rots = {}
    out = {}
    for name in SCORES:
        sv = scores[name]
        mk = uni & np.isfinite(sv)
        grid = np.full((nd, nslot), np.nan); grid[di[mk], slot[mk]] = sv[mk]
        rot = rotation_spearman(grid, net_grid, uni_grid, ks)
        obs = FO.spearman(sv[mk], net[mk])
        if not np.isclose(rot[0], obs, rtol=1e-12, atol=1e-12):
            raise S.GateError(f"[ROTATION] {name}: k = 0 gives {rot[0]!r}, the observed Spearman is {obs!r}")
        rots[name] = rot[1:]
        e1, e2 = np.quantile(sv[mk], [1 / 3, 2 / 3])
        tb = np.digitize(sv[mk], [e1, e2])
        out[name] = {"n": int(mk.sum()), "coverage_of_universe": float(mk.sum() / uni.sum()), "spearman": float(obs),
                     "auc_vs_oracle": FO.auc(sv[mk], net[mk] > 0), "curve_sharpe_at_spearman": float(np.interp(obs, cx, cy)),
                     "rotation": S.blk(obs, rot[1:]),
                     "terciles": {str(k): {"n": int((tb == k).sum()), "mean_net": float(net[mk][tb == k].mean()), "win_rate": float((net[mk][tb == k] > 0).mean())} for k in range(3)},
                     "void": bool(name.startswith("A") and not a_valid)}
    fam = np.nanmax(np.vstack([rots[n] for n in SCORES if not out[n]["void"]]), axis=0)
    fam_p95 = float(np.nanpercentile(fam, 95))
    res["family_max_null"] = {"p50": float(np.nanpercentile(fam, 50)), "p95": fam_p95, "n_offsets": int(np.isfinite(fam).sum()), "scores_in_family": [n for n in SCORES if not out[n]["void"]]}
    for name, o in out.items():
        o["carries_direction"] = bool(not o["void"] and o["spearman"] > 0 and o["rotation"]["above_p95"])
        o["survives_family"] = bool(o["carries_direction"] and o["spearman"] > fam_p95)
        o["worth_a_filter"] = bool(o["survives_family"] and o["spearman"] >= 0.05)
        t_ = o["terciles"]
        log(f"  {name}{' (VOID)' if o['void'] else ''}: n {o['n']} ({o['coverage_of_universe']:.2f} of universe) Spearman {o['spearman']:+.4f} AUC {o['auc_vs_oracle']:.3f} "
            f"-> curve Sharpe {o['curve_sharpe_at_spearman']:+.2f}; rotation p50 {o['rotation']['p50']:+.4f} p95 {o['rotation']['p95']:+.4f} pct {o['rotation']['pct_rank']:.3f}; "
            f"terciles ${t_['0']['mean_net']:+.2f}/{t_['1']['mean_net']:+.2f}/{t_['2']['mean_net']:+.2f} win {t_['0']['win_rate']:.2f}/{t_['1']['win_rate']:.2f}/{t_['2']['win_rate']:.2f}; "
            f"carries {o['carries_direction']} family {o['survives_family']} filter {o['worth_a_filter']}")
    log(f"  family-max null p50 {res['family_max_null']['p50']:+.4f} p95 {fam_p95:+.4f}")
    res["inputs"] = out
    res["timing_s"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(res, indent=1, default=lambda o_: o_.item() if hasattr(o_, "item") else str(o_)), encoding="utf-8")
    log(f"  wrote {OUT.relative_to(REPO)} in {res['timing_s']} s")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    sys.exit(run(a.data_root) if a.run else 1)
