"""D704 DIAG -- a volume gate on V1: did the price rise over the last hour without a matching aggressive-buy imbalance?
Ranked against V1's oracle before any threshold (the principal, 2026-09-30: "the MACD again plus some sort of volume
type gate"; then gate "B: no aggressive push", window "Last hour", scoring "Continuous ranking first"). Design:
docs/decisions/D704-DIAG-DESIGN-a-no-aggressive-push-gate-on-v1.md, committed before this runner.

    uv run python scripts/diag_d704_no_push_gate_on_v1.py --selftest
    uv run python scripts/diag_d704_no_push_gate_on_v1.py --run --data-root "<main checkout>/data"

In-sample, 2016-01-05 -> 2023-12-29; nothing on or after 2024-01-01 is read. V1 is reproduced through D699's functions
and guarded against its published mean net exactly.

THE SCORE (higher = more confirmation)
  window  the minutes labelled jd - L .. jd - 1 (jd = V1's deciding close, in minutes after 09:30; L = min(60, jd):
          truncated to the session for the early entries)
  I       (buy - sell) / volume over the window (the Sierra aggressor fixture fut_ES_signed_1m; VOID if its declared
          validation failed)
  z       log(P_jd / P_jd-L) / (s60 * sqrt(L / 60)); s60 = the sd of the within-session 60-minute log moves at the
          15-minute closes 10:30 .. 16:00 over the 20 sessions before d (prior-only)
  I_hat   a + b z, OLS over every window (the 15-minute closes 09:45 .. 15:45, every in-sample day, both gamma classes;
          no outcome)
  S_B     -(I - I_hat(z))   PRIMARY          S_A1   -I   SECONDARY (D695's A1, sign reversed)
DECLARED READING: INFORMATIVE if S_B's Spearman against net is above its rotation null's p95 and the quintile calibration
slope is positive; WORTH A THRESHOLD DESIGN if also the upper half's edge per unit of noise (mean drift excess / its sd)
is >= 1.7 x V1's; else NO INFORMATION.

Output data/d704_no_push_gate_on_v1.json: statistics only, no per-date GEX (SqueezeMetrics, under the permission of
2026-09-28).
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

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))
import stage0_d688_gamma_close as S                 # noqa: E402  (importing defines, never runs)
import stage0_d699_gamma_macd_long as V             # noqa: E402
from backtest_framework.validation import filter_oracle as F  # noqa: E402

OUT = REPO / "data" / "d704_no_push_gate_on_v1.json"
D699_JSON = REPO / "data" / "d699_gamma_macd_long.json"
V1 = "V1_HIST"
WIN = 60
TRAIL = 20
FIT_J = np.arange(15, 376, 15)                     # 09:45 .. 15:45
SIG_J = np.arange(60, 391, 15)                     # 10:30 .. 16:00
LIFT = 1.7
N_AUDIT = 30


def P(*a, **k):
    print(*a, **k, flush=True)


def s60_of(PM):
    """Per session: the sd of the within-session 60-minute log moves at SIG_J over the 20 sessions before it."""
    with np.errstate(divide="ignore", invalid="ignore"):
        mv = np.log(PM[:, SIG_J] / PM[:, SIG_J - WIN])
    out = np.full(PM.shape[0], np.nan)
    for i in range(TRAIL, PM.shape[0]):
        x = mv[i - TRAIL:i].ravel()
        x = x[np.isfinite(x)]
        if x.size > 50:
            out[i] = np.std(x, ddof=1)
    return out


def window_stats(PM, VOL, NBY, s60, prow, rows, jd):
    """I and z for windows ending at the close jd on PM rows `rows` (VOL/NBY are indexed by panel row prow[rows])."""
    L = np.minimum(WIN, jd)
    q = prow[rows]
    cs_v = np.concatenate([np.zeros((VOL.shape[0], 1)), np.cumsum(VOL, 1)], axis=1)
    cs_n = np.concatenate([np.zeros((NBY.shape[0], 1)), np.cumsum(NBY, 1)], axis=1)
    v = cs_v[q, jd] - cs_v[q, jd - L]
    nb = cs_n[q, jd] - cs_n[q, jd - L]
    with np.errstate(divide="ignore", invalid="ignore"):
        I = np.where(v > 0, nb / v, np.nan)
        z = np.log(PM[rows, jd] / PM[rows, jd - L]) / (s60[rows] * np.sqrt(L / WIN))
    return I, z


def core(PM, pidx, short, days, VOL, NBY, has_flow, usd, cost, log=P, guard=None):
    """PM: every loaded session x 391 prices; pidx: the panel's rows in PM; days: the panel's dates; VOL, NBY: panel
    sessions x 390 minutes of volume and (buy - sell), minute k labelled 09:30 + k; has_flow: panel sessions the
    fixture covers."""
    nd = len(days)
    prow = np.full(PM.shape[0], -1); prow[pidx] = np.arange(nd)
    PB = PM[:, np.concatenate([[0], V.BAR_J])]
    sig = V.signals(PB)
    ST = V.states(sig, +1)
    ok = sig["valid"][pidx] & np.isfinite(sig["s15"][pidx]) & np.isfinite(PM[pidx]).all(1)
    rows_s, rows_l = pidx[ok & short], pidx[ok & ~short]
    ii, ja, jb = V.trade_list(ST[V1], rows_s)
    gross = (PM[ii, jb] - PM[ii, ja]) * usd
    net = gross - cost
    if guard is not None and float(net.mean()) != guard:
        raise S.GateError(f"[REPRO] V1 mean net {float(net.mean())!r} vs D699's {guard!r}")
    log(f"  V1 {'REPRODUCED' if guard is not None else '(unguarded)'}: {len(ii)} trades, mean net ${net.mean():+.4f}")
    mbar = PM[rows_s].mean(0)
    excess = gross - (mbar[jb] - mbar[ja]) * usd
    s60 = s60_of(PM)
    # ---- I_hat: every window, every in-sample day with flow, both classes (no outcome)
    fr = pidx[has_flow & np.isfinite(PM[pidx]).all(1)]
    Ifit, zfit = [], []
    for j in FIT_J:
        I_, z_ = window_stats(PM, VOL, NBY, s60, prow, fr, np.full(fr.size, j))
        Ifit.append(I_); zfit.append(z_)
    Ifit, zfit = np.concatenate(Ifit), np.concatenate(zfit)
    m = np.isfinite(Ifit) & np.isfinite(zfit)
    b, a = np.polyfit(zfit[m], Ifit[m], 1)
    r2 = float(np.corrcoef(zfit[m], Ifit[m])[0, 1] ** 2)
    if not b > 0:
        raise S.GateError(f"[QUANTITY] the fitted imbalance-per-move slope b = {b} is not positive: aggressive buying should come with rises")
    log(f"  I_hat = {a:+.4f} + {b:.4f} z over {int(m.sum())} windows (R^2 {r2:.3f})")

    def scores(rows, ja_):
        I_, z_ = window_stats(PM, VOL, NBY, s60, prow, rows, ja_ - 1)
        return -(I_ - (a + b * z_)), -I_, I_, z_

    SB, SA1, I, z = scores(ii, ja)
    # ---- the second implementation, on sampled trades: plain loops over the minute arrays; it must fire when shifted
    rng = np.random.default_rng(704)
    samp = rng.choice(len(ii), min(N_AUDIT, len(ii)), replace=False)

    def loop_I_z(k, shift=0):
        r, jd = int(ii[k]), int(ja[k]) - 1 + shift
        L = min(WIN, jd)
        q = int(prow[r])
        vs = sum(float(VOL[q, t]) for t in range(jd - L, jd))
        ns = sum(float(NBY[q, t]) for t in range(jd - L, jd))
        return (ns / vs if vs > 0 else float("nan")), math.log(PM[r, jd] / PM[r, jd - L]) / (s60[r] * math.sqrt(L / WIN))

    for k in samp:
        li, lz = loop_I_z(k)
        if not ((math.isnan(li) and math.isnan(I[k])) or abs(li - I[k]) <= 1e-9 * max(1.0, abs(li))) or not abs(lz - z[k]) <= 1e-9 * max(1.0, abs(lz)):
            raise S.GateError(f"[LAG] trade {k}: the vectorised window ({I[k]}, {z[k]}) differs from the loop's ({li}, {lz})")
    if all(abs(loop_I_z(k, 15)[0] - I[k]) <= 1e-9 for k in samp if np.isfinite(I[k])):
        raise S.GateError("[LAG] the window check does not fire on a window shifted 15 minutes forward")
    # the sign: more aggressive buying for the same move scores LOWER
    if not (-(0.5 - (a + b * 1.0)) < -(0.0 - (a + b * 1.0))):
        raise S.GateError("[SIGN] more aggressive buying does not score lower")
    if abs(np.corrcoef(SB[np.isfinite(SB)], SA1[np.isfinite(SB)])[0, 1]) > 0.999:
        raise S.GateError("[QUANTITY] S_B is S_A1: the residualisation did nothing")
    log(f"  audits: {len(samp)} windows re-derived by a loop, and it fires on a 15-minute shift; sign and residualisation checked")
    use = np.isfinite(SB)
    res = {"v1": {"trades": int(len(ii)), "scored": int(use.sum()), "mean_net": float(net.mean()), "mean_gross": float(gross.mean())},
           "i_hat": {"a": float(a), "b": float(b), "r2": r2, "windows": int(m.sum())},
           "oracle_d699": {"share": float((net > 0).mean()), "mean_net_winners": float(net[net > 0].mean())}}
    n_, g_, x_, ii_, ja_ = net[use], gross[use], excess[use], ii[use], ja[use]
    pi = np.searchsorted(pidx, ii_)
    E = S.d685()

    def daily(v, mask):
        d = np.zeros(nd); np.add.at(d, pi[mask], v[mask]); return d

    x_snr = lambda v: float(v.mean() / v.std(ddof=1)) if v.size > 2 else float("nan")
    v1_snr = x_snr(x_)
    res["v1"]["edge_per_noise"] = v1_snr
    for nm, sc in (("S_B", SB[use]), ("S_A1", SA1[use])):
        rk = F.average_ranks(sc) / sc.size
        cal = F.calibration(rk, n_, n_bins=5)
        take = sc >= np.median(sc)
        null = np.array([F.spearman(np.roll(sc, int(k)), n_) for k in S.rot_ks(sc.size)[1:]])
        blk = S.blk(F.spearman(sc, n_), null)
        up = {"trades": int(take.sum()), "mean_net": float(n_[take].mean()), "median_net": float(np.median(n_[take])), "hit": float((n_[take] > 0).mean()),
              "net_sharpe": E.sharpe(daily(n_, take)), "net_sortino": E.sortino(daily(n_, take)),
              "mean_excess": float(x_[take].mean()), "edge_per_noise": x_snr(x_[take]), "lift_vs_v1": x_snr(x_[take]) / v1_snr}
        lo = ~take
        res[nm] = {"spearman_net": blk, "spearman_excess": F.spearman(sc, x_), "auc_oracle": F.auc(sc, n_ > 0),
                   "calibration_on_rank": cal, "assess_upper_half": F.assess(sc, take, g_, n_), "upper_half": up,
                   "lower_half": {"trades": int(lo.sum()), "mean_net": float(n_[lo].mean()), "mean_excess": float(x_[lo].mean())}}
        q5 = [b_["mean_realized"] for b_ in cal["bins"]] if "bins" in cal else None
        log(f"  {nm}: Spearman vs net {blk['observed']:+.4f} (rotation p50 {blk['p50']:+.4f} p95 {blk['p95']:+.4f}, pct {blk['pct_rank']:.3f}); vs excess {res[nm]['spearman_excess']:+.4f}; "
            f"AUC {res[nm]['auc_oracle']:.4f}; calibration slope {cal.get('slope', float('nan')):+.2f}; quintile net {q5}")
        log(f"      upper half: {up['trades']} trades, mean net ${up['mean_net']:+.2f} (median ${up['median_net']:+.2f}, hit {up['hit']:.3f}), net Sharpe {up['net_sharpe']:+.2f} "
            f"Sortino {up['net_sortino']:+.2f}, edge/noise {up['edge_per_noise']:.4f} = {up['lift_vs_v1']:.2f} x V1's {v1_snr:.4f}; lower half mean net ${res[nm]['lower_half']['mean_net']:+.2f}")
    # the mechanism check: V1 on long-gamma days
    li, lja, ljb = V.trade_list(ST[V1], rows_l)
    lnet = (PM[li, ljb] - PM[li, lja]) * usd - cost
    lSB = scores(li, lja)[0]
    lu = np.isfinite(lSB)
    res["long_gamma_check"] = {"trades": int(lu.sum()), "spearman_S_B_net": F.spearman(lSB[lu], lnet[lu]), "mean_net": float(lnet.mean())}
    # the known false positives, against S_B
    sb = SB[use]
    hr = (ja_ - 1 + 30) // 60 + 9
    yr = np.array([days[p][:4] for p in pi])
    res["false_positive_checks"] = {
        "spearman_S_B_abs_z": F.spearman(sb, np.abs(z[use])), "spearman_S_B_z": F.spearman(sb, z[use]), "spearman_S_B_hour": F.spearman(sb, hr.astype(float)),
        "truncated_window_share": float((ja_ - 1 < WIN).mean()),
        "spearman_net_by_year": {y: F.spearman(sb[yr == y], n_[yr == y]) for y in sorted(set(yr)) if (yr == y).sum() > 5},
        "spearman_net_ex_2022": F.spearman(sb[yr != "2022"], n_[yr != "2022"]),
        "spearman_net_full_windows_only": F.spearman(sb[ja_ - 1 >= WIN], n_[ja_ - 1 >= WIN])}
    fp = res["false_positive_checks"]
    log(f"  long-gamma check: Spearman {res['long_gamma_check']['spearman_S_B_net']:+.4f} on {res['long_gamma_check']['trades']} trades")
    log(f"  false positives: S_B vs |z| {fp['spearman_S_B_abs_z']:+.3f}, vs z {fp['spearman_S_B_z']:+.3f}, vs hour {fp['spearman_S_B_hour']:+.3f}; truncated windows {fp['truncated_window_share']:.2f}; "
        f"Spearman ex-2022 {fp['spearman_net_ex_2022']:+.4f}; full windows only {fp['spearman_net_full_windows_only']:+.4f}; by year " +
        " ".join(f"{y}:{v:+.3f}" for y, v in fp["spearman_net_by_year"].items()))
    B_ = res["S_B"]
    informative = bool(B_["spearman_net"]["above_p95"] and B_["calibration_on_rank"].get("slope", -1) > 0)
    worth = bool(informative and B_["upper_half"]["lift_vs_v1"] >= LIFT)
    res["reading"] = "WORTH A THRESHOLD DESIGN" if worth else "INFORMATIVE" if informative else "NO INFORMATION"
    res["detection_limit_spearman_se"] = 1 / math.sqrt(int(use.sum()) - 1)
    log(f"  READING: {res['reading']} (Spearman SE about {res['detection_limit_spearman_se']:.3f})")
    return res


def load_flow(data_root: Path, days):
    fx = data_root / "fixtures"
    meta = json.loads((fx / "fut_ES_signed_1m.meta.json").read_text(encoding="utf-8"))
    if not bool(meta["validation"]["pass"]):
        raise S.GateError("[VOID] the signed-flow fixture's declared validation failed")
    fl = pd.read_csv(fx / "fut_ES_signed_1m.csv.gz", usecols=["day", "hhmm", "volume", "buy", "sell"], dtype={"day": str, "hhmm": str}, encoding="utf-8")
    fl = fl[(fl["day"] < S.CUTOFF) & fl["day"].isin(set(days))]
    S.guard_window(fl["day"], "D704 signed flow")
    mins = [(pd.Timestamp("2000-01-01 09:30") + pd.Timedelta(minutes=k)).strftime("%H:%M") for k in range(390)]
    VOL = fl.pivot_table(index="day", columns="hhmm", values="volume", aggfunc="sum").reindex(index=days, columns=mins).fillna(0.0).to_numpy()
    NBY = fl.assign(nb=fl["buy"] - fl["sell"]).pivot_table(index="day", columns="hhmm", values="nb", aggfunc="sum").reindex(index=days, columns=mins).fillna(0.0).to_numpy()
    has = np.isin(days, fl["day"].unique())
    return VOL, NBY, has, meta["validation"]


def run(data_root: Path, log=P) -> int:
    t0 = time.time()
    D, PM, pidx = V.panel(data_root, log)
    days = D.index.to_numpy().astype(str)
    VOL, NBY, has, val = load_flow(data_root, days)
    log(f"  signed flow: {int(has.sum())} of {len(days)} panel sessions; fixture validation {val.get('pass')}")
    E = S.d685()
    mes = E.cost_spec("ES", "micro")
    short = D["G_SUM"].to_numpy(float) < 0
    guard = json.loads(D699_JSON.read_text(encoding="utf-8"))["variants"][V1]["2_book"]["mean_net"]
    res = core(PM, pidx, short, days, VOL, NBY, has, mes["usd_per_point"], mes["cost_rt_usd"], log, guard=guard)
    res = {"spec": "D704 DIAG (in-sample; the no-aggressive-push volume gate on D699's V1, ranked against its oracle)", "cost_rt_usd": mes["cost_rt_usd"],
           "fixture_validation": val, **res, "timing_s": round(time.time() - t0, 1)}
    OUT.write_text(json.dumps(res, indent=1, default=lambda o_: o_.item() if hasattr(o_, "item") else str(o_)), encoding="utf-8")
    log(f"  wrote {OUT.relative_to(REPO)} in {res['timing_s']} s")
    return 0


def selftest(log=P) -> int:
    """Synthetic sessions whose aggressor flow is tied to price, through every path of core()."""
    rng = np.random.default_rng(3)
    n = 400
    r = 0.0004 * rng.standard_normal((n, 390))
    PM = 4000.0 * np.exp(np.cumsum(np.column_stack([np.zeros(n), r]).ravel()).reshape(n, 391))
    VOL = rng.integers(500, 5000, (n - 30, 390)).astype(float)
    NBY = np.clip(0.3 * np.sign(r[30:]) + 0.2 * rng.standard_normal((n - 30, 390)), -1, 1) * VOL
    pidx = np.arange(30, n)
    short = rng.random(pidx.size) < 0.5
    days = np.array([str((pd.Timestamp("2016-01-04") + pd.Timedelta(days=int(i))).date()) for i in range(pidx.size)])
    res = core(PM, pidx, short, days, VOL, NBY, np.ones(pidx.size, bool), 5.0, 4.42, log)
    assert res["reading"] in ("NO INFORMATION", "INFORMATIVE", "WORTH A THRESHOLD DESIGN")
    log("  SELFTEST PASSED")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a_ = ap.parse_args()
    sys.exit(run(a_.data_root) if a_.run else selftest() if a_.selftest else 1)
