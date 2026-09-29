"""D688 STAGE 0 -- the dealer-gamma close on ES: does the hedge flow implied by the SPX + ES option books predict the
last half-hour? Pre-registration: docs/decisions/D688-PRE-REG-the-dealer-gamma-close-on-es-spx-plus-es-books.md
(committed alone, before this file: de4a4f7e).

    uv run python scripts/stage0_d688_gamma_close.py --selftest
    uv run python scripts/stage0_d688_gamma_close.py --run --data-root "<main checkout>/data"

For session d:
  G      SPX GEX (SqueezeMetrics, the last row dated strictly before d) + the ES options book at the PRIOR settlement,
         both $ per 1 % (F1, F1'); the ES book uses D581's audited Black-76 functions, imported unchanged
  r      log P(15:30) - log S_prev(c), in %, c the 15:30 contract (F3)
  Q      -G r ($; > 0 means the dealers buy)
  Z      sigma_d sign(Q) sqrt(|Q| / V), in bp (F5); V the 20-session median ES dollar volume, sigma_d the 20-session
         std of settlement returns, both through d-1
  R2     log P(16:00) - log P(15:30), in bp (F4)
Gate 1: R2 = a + b_G Z_SUM + b_r r + b_L Z_L + b_s sigma_d, NW lag 5; b_G > 0, t >= 2, above the p95 of the
enumerated day-rotation null of G (k = 10 .. n-10, p95 SE 0), and b_G(close) - b_G(11:00) above the p95 of that
difference under the same rotation (F7). Gate 2: 1 MES 15:30 -> 16:00 in the sign of Z_SUM when the prior-only,
regime-split pass-through projects >= 2 x the round trip (F2, F9); NW t >= 2 on >= 60 trades.

Reads ES prices, settlements, options, GEX and AUM from 2015-10 (trailing inputs only) to 2023-12-29; every loader cuts
at 2024-01-01 and raises if a later row survives. The exchange session calendar (dates and bar counts only, no price)
is read in full, as D581 read it, because an option's time to expiry is counted on it.

SqueezeMetrics data are used under the permission of 2026-09-28 (credit: SqueezeMetrics, squeezemetrics.com). The
output holds statistics only: no per-date GEX, and no per-date series derived from it.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "d688_gamma_close.json"
SPEC = "D688 (de4a4f7e)"
CUTOFF = "2024-01-01"; IN_FROM = "2016-01-04"; WARM_FROM = "2015-10-01"
MULT = 50.0; HOURS = 6.5; YEAR_HOURS = 252 * HOURS; MONEYNESS_MAX = 0.30; T_ENTRY = "15:30"
NW_LAG = 5; SHIFT_MIN = 10; TRAIL = 20; BURN = 250; MIN_REG = 60; K_EP = 2.0; MIN_TRADES = 60
ERA_SPLIT = "2022-01-01"; SEED = 681; N_WORKERS = 10; CHUNK = 500_000
D581_C = -0.022772686672947903                        # data/stage0_d581_gamma_close.json, T1.c
LETF_SET = {"UPRO": 3, "SPXU": -3, "SSO": 2, "SDS": -2, "SPXL": 3, "SPXS": -3}
CLOCK = ["09:30"] + [f"{h:02d}:{m:02d}" for h in range(10, 16) for m in (0, 30)] + ["16:00"]
OPT_COLS = ["session", "right", "strike", "expiry_date", "expiry_hhmm", "underlying", "oi", "settle", "oi_pub_et", "vol_to_1530"]
OPT_DTYPE = {"session": str, "right": str, "expiry_date": str, "expiry_hhmm": str, "underlying": str, "oi_pub_et": str}
REQUIRED_OUTPUTS = ("spec", "windows", "audits", "reproduction", "sets", "premise", "gate1", "gate2", "beside", "books",
                    "predictions", "verdict", "construction", "timing_s")


class GateError(AssertionError):
    """An audit refused the input. Raising, never a warning."""


def P(*a, **k):
    print(*a, **k, flush=True)


def _mod(name: str, fn: str):
    if name in sys.modules:
        return sys.modules[name]
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


def d581(fx: Path | None = None):
    """D581's runner, its fixture paths pointed at `fx` (the fixtures live in the main checkout)."""
    m = _mod("d581", "stage0_d581_gamma_close.py")
    if fx is not None:
        m.FIX = fx; m.OPTS = fx / "fut_es_options_eod.csv.gz"; m.ES_1M = fx / "fut_ES_rth_1m.csv.gz"
        m.STRIP = fx / "fut_settle_strip.csv.gz"; m.SESSIONS = fx / "fut_index_sessions.csv.gz"
    return m


def d685():
    return _mod("d685", "stage0_d685_month_end_rebalancing.py")


def expect_raise(fn, what, log=P) -> bool:
    try:
        fn()
    except AssertionError as e:
        log(f"    audit RAISES on {what}: {str(e)[:80]}")
        return True
    raise GateError(f"audit did not raise on {what}")


def guard_window(dates, what: str) -> None:
    d = pd.Series(np.asarray(dates)).astype(str)
    if len(d) and (d >= CUTOFF).any():
        raise GateError(f"[WINDOW] {what}: a row dated {d[d >= CUTOFF].min()} survived the {CUTOFF} cut")


def blk(obs: float, null: np.ndarray) -> dict:
    null = np.asarray(null, float)
    null = null[np.isfinite(null)]
    p95 = float(np.percentile(null, 95))
    return {"observed": float(obs), "p05": float(np.percentile(null, 5)), "p50": float(np.percentile(null, 50)), "p95": p95,
            "n_offsets": int(null.size), "p95_se": 0.0, "pct_rank": float((null < obs).mean()), "above_p95": bool(obs > p95)}


# ------------------------------------------------------------------ the construction (s.4)
def zpush(G, r, sig, V):
    """Z = sigma sign(Q) sqrt(|Q| / V), Q = -G r: G $ per 1 %, r in %, V in $, sigma in bp -> Z in bp."""
    Q = -G * r
    return sig * np.sign(Q) * np.sqrt(np.abs(Q) / V)


def zletf(A_L, r, sig, V):
    """The LETF rebalance in the same square-root form: Q_L = sum_i A_i L_i (L_i - 1) r (D640's flow, r as a fraction)."""
    Q = A_L * r / 100.0
    return sig * np.sign(Q) * np.sqrt(np.abs(Q) / V)


def qraw(G, r):
    """The raw form -G r, in $bn."""
    return -G * r / 1e9


def es_book_prior(opts: pd.DataFrame, strip_es: pd.DataFrame, tcal: np.ndarray, refs: np.ndarray, m) -> pd.DataFrame:
    """G_ES per session: sum Gamma(F_prev, K, iv, tau_settle) sign OI 50 F_prev^2 0.01 ($ per 1 %), at the prior settlement.

    iv from the prior settlement price (D581's implied_vol), gamma from D581's b76_gamma; calls +, puts -. F_prev is each
    row's own underlying at the last settlement strictly before d, and the moneyness filter uses it (nothing from d).
    D581's expiry filter: a same-day expiry before 15:30 (the AM quarterly) carries no gamma. Sessions to expiry are
    counted on `tcal`, EVERY ES trading day (half days and halt days included: "the trading time to expiry"); D581's
    >= 380-bar calendar drops those days and timed an expiry on one as same-day. An expiry before d is dropped."""
    settle = strip_es.set_index(["ref", "contract"])["settle"]
    calx = {d: i for i, d in enumerate(tcal)}
    rows = {}
    for d, g in opts.groupby("session", sort=True):
        if d not in calx:
            continue
        i = calx[d]
        prev = refs[np.searchsorted(refs, d) - 1]
        und = g["underlying"].to_numpy()
        fmap = {u: settle.get((prev, u), np.nan) for u in pd.unique(und)}
        Fp = np.array([fmap[u] for u in und], float)
        K = g["strike"].to_numpy(float); right = g["right"].to_numpy(); oi = g["oi"].to_numpy(float)
        e = g["expiry_date"].to_numpy().astype(str)
        n_ahead = np.searchsorted(tcal, e) - i
        same_day = n_ahead == 0
        exp_ok = ~same_day | (g["expiry_hhmm"].to_numpy().astype(str) >= T_ENTRY)
        tau = (n_ahead * HOURS + HOURS) / YEAR_HOURS
        px = g["settle"].to_numpy(float)
        fin = np.isfinite(px) & np.isfinite(Fp)
        mk = fin & (e >= d) & exp_ok & (oi > 0)
        mk &= np.abs(K / np.where(fin, Fp, 1.0) - 1) < MONEYNESS_MAX
        iv = np.full(len(g), np.nan)
        iv[mk] = m.implied_vol(px[mk], Fp[mk], K[mk], tau[mk], right[mk])
        ok = np.isfinite(iv)
        gam = m.b76_gamma(Fp[ok], K[ok], iv[ok], tau[ok])
        sgn = np.where(right[ok] == "C", 1.0, -1.0)
        rows[d] = {"G_ES": float((gam * sgn * oi[ok] * MULT * Fp[ok] * Fp[ok] * 0.01).sum()), "n_used": int(ok.sum()),
                   "n_offcal_live": int((mk & ~np.isin(e, tcal)).sum())}
    return pd.DataFrame.from_dict(rows, orient="index").sort_index()


def oi_keyed(opts: pd.DataFrame, shift_days: int = 0) -> bool:
    """D581's OI keying: every row's OI was published before its session's 10:00 ET."""
    pub = pd.to_datetime(opts["oi_pub_et"]) + pd.Timedelta(days=shift_days)
    return bool((pub < pd.to_datetime(opts["session"]) + pd.Timedelta(hours=10)).all())


# ------------------------------------------------------------------ the parallel ES-book rebuild (processes: GIL-bound pandas)
_W: dict = {}


def _init(fx, es581, strip_es, cal, tcal, refs):
    _W.update(m=d581(Path(fx)), fx=Path(fx), es=es581, strip=strip_es, cal=cal, tcal=tcal, refs=refs)


def _work(args):
    mine, keep = args
    t0 = time.time()
    mine = set(mine)
    parts = []
    for ch in pd.read_csv(_W["fx"] / "fut_es_options_eod.csv.gz", usecols=OPT_COLS, dtype=OPT_DTYPE, chunksize=CHUNK, encoding="utf-8"):
        ch = ch[ch["session"].isin(mine)]
        if len(ch):
            parts.append(ch)
    opts = pd.concat(parts, ignore_index=True)
    guard_window(opts["session"], "options")
    oi_ok, oi_fires = oi_keyed(opts, 0), not oi_keyed(opts, 1)
    t581 = _W["m"].gamma_table(opts, _W["es"], _W["strip"], _W["cal"], lambda *a: None)
    prior = es_book_prior(opts, _W["strip"], _W["tcal"], _W["refs"], _W["m"])
    kept = opts[opts["session"].isin(set(keep))].copy()
    return {"t581": t581, "prior": prior, "oi_ok": oi_ok, "oi_fires": oi_fires, "rows": int(len(opts)), "kept": kept, "s": time.time() - t0}


# ------------------------------------------------------------------ inputs
def load_inputs(data_root: Path, log=P) -> dict:
    fx = data_root / "fixtures"
    sess = pd.read_csv(fx / "fut_index_sessions.csv.gz", usecols=["root", "day", "bars"], dtype={"root": str, "day": str}, encoding="utf-8")
    cal = np.array(sorted(sess[(sess["root"] == "ES") & (sess["bars"] >= 380)]["day"].unique()))   # dates only, as D581
    tcal = np.array(sorted(sess[sess["root"] == "ES"]["day"].unique()))                             # every trading day, for tau
    b = pd.read_csv(fx / "fut_ES_rth_1m.csv.gz", usecols=["day", "hhmm", "contract", "open", "close", "volume"],
                    dtype={"day": str, "hhmm": str, "contract": str}, encoding="utf-8")
    b = b[(b["day"] >= WARM_FROM) & (b["day"] < CUTOFF)].reset_index(drop=True)
    guard_window(b["day"], "ES bars")
    st = pd.read_csv(fx / "fut_settle_strip.csv.gz", dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8")
    st = st[(st["root"] == "ES") & (st["ref"] < CUTOFF)].reset_index(drop=True)
    guard_window(st["ref"], "ES settlements")
    dix = pd.read_csv(data_root / "raw" / "squeezemetrics" / "DIX.csv", usecols=["date", "gex"], dtype={"date": str}, encoding="utf-8")
    dix = dix[dix["date"] < CUTOFF].sort_values("date").reset_index(drop=True)
    guard_window(dix["date"], "SqueezeMetrics GEX")
    aum = pd.read_csv(data_root / "letf" / "letf_aum_daily.csv.gz", usecols=["date", "ticker", "aum"], dtype={"date": str, "ticker": str}, encoding="utf-8")
    aum = aum[(aum["date"] < CUTOFF) & aum["ticker"].isin(LETF_SET)].reset_index(drop=True)
    guard_window(aum["date"], "LETF AUM")
    nb = b.groupby("day").size()
    days = np.array([d for d in cal if WARM_FROM <= d < CUTOFF and nb.get(d, 0) >= 380])
    log(f"  inputs: {len(days)} ES sessions {days[0]} .. {days[-1]} (from {WARM_FROM} for the trailing windows); "
        f"{len(st)} ES settlement rows; GEX rows to {dix['date'].max()}; AUM rows to {aum['date'].max()}")
    return {"fx": fx, "cal": cal, "tcal": tcal, "bars": b, "strip": st, "dix": dix, "aum": aum, "days": days}


def build_panel(I: dict, log=P) -> pd.DataFrame:
    """One row per session in `days`: the clock prices, S_prev, sigma_d, V, G_SPX and the LETF coefficient A_L. Vectorised."""
    b, st, days = I["bars"], I["strip"], I["days"]
    bb = b[b["day"].isin(set(days))]
    close = bb.pivot(index="day", columns="hhmm", values="close").reindex(days)
    op = bb[bb["hhmm"] == "09:30"].set_index("day")["open"].reindex(days)
    con = bb[bb["hhmm"] == "15:29"].set_index("day")["contract"].reindex(days)
    dv = (bb["volume"] * bb["close"] * MULT).groupby(bb["day"]).sum().reindex(days)

    def price(hhmm):   # the price AT hh:mm is the close of the bar labelled one minute earlier (D462); 09:30 is the open
        if hhmm == "09:30":
            return op
        lab = (pd.Timestamp("2000-01-01 " + hhmm) - pd.Timedelta(minutes=1)).strftime("%H:%M")
        return close[lab]

    D = pd.DataFrame(index=pd.Index(days, name="day"))
    for t in sorted(set(CLOCK) | {"15:50", "15:00"}):
        D["P" + t.replace(":", "")] = price(t).to_numpy(float)
    refs = np.array(sorted(st["ref"].unique()))
    settle = st.set_index(["ref", "contract"])["settle"]
    prev = refs[np.searchsorted(refs, days) - 1]
    D["contract"] = con.to_numpy()
    D["S_prev"] = settle.reindex(list(zip(prev, D["contract"]))).to_numpy(float)
    D["S_d"] = settle.reindex(list(zip(days, D["contract"]))).to_numpy(float)
    ret = pd.Series(1e4 * np.log(D["S_d"] / D["S_prev"]).to_numpy(), index=D.index)
    D["sig"] = ret.rolling(TRAIL).std(ddof=1).shift(1).to_numpy()
    D["V"] = dv.rolling(TRAIL).median().shift(1).to_numpy()
    dd = I["dix"]["date"].to_numpy().astype(str)
    j = np.searchsorted(dd, days) - 1                                             # the last GEX row strictly before d
    D["G_SPX"] = np.where(j >= 0, I["dix"]["gex"].to_numpy(float)[np.maximum(j, 0)], np.nan)
    D["G_SPX_sameday"] = I["dix"].set_index("date")["gex"].reindex(days).to_numpy(float)   # for the lag audit's break only
    A = np.zeros(len(days))
    for tk, L in LETF_SET.items():
        s = I["aum"][I["aum"]["ticker"] == tk].sort_values("date")
        sd = s["date"].to_numpy().astype(str)
        k = np.searchsorted(sd, days) - 1
        v = np.where(k >= 0, s["aum"].to_numpy(float)[np.maximum(k, 0)], np.nan)
        gap = (pd.to_datetime(days) - pd.to_datetime(np.where(k >= 0, sd[np.maximum(k, 0)], "1900-01-01"))).days.to_numpy()
        v = np.where(gap <= 7, v, np.nan)                                          # a stale AUM is missing, not carried
        A = A + L * (L - 1) * v
    D["A_L"] = A
    D["year"] = D.index.str[:4]
    log(f"  panel: {len(D)} sessions; contract of the 15:29 bar missing on {int(D['contract'].isna().sum())}; "
        f"S_prev missing on {int(D['S_prev'].isna().sum())}")
    return D


def second_path(d: str, I: dict, opts_d: pd.DataFrame, m) -> dict:
    """The lag audit's second implementation: Z_SUM for one session from inputs filtered by date, row by row where it
    matters, never calling build_panel or es_book_prior."""
    b, st, dix, tcal = I["bars"], I["strip"], I["dix"], I["tcal"]
    past = dix[dix["date"] < d]
    g_spx = float(past.loc[past["date"].idxmax(), "gex"])
    if not (pd.to_datetime(opts_d["oi_pub_et"]) < pd.Timestamp(d) + pd.Timedelta(hours=10)).all():
        raise GateError(f"[LAG] {d}: an OI row was published after 10:00 of its session")
    sp = st[st["ref"] < d]
    pv = sp["ref"].max()
    fp = sp[sp["ref"] == pv].set_index("contract")["settle"]
    px_, F_, K_, tau_, rt_, sg_, oi_ = [], [], [], [], [], [], []
    for r in opts_d.itertuples():
        F = float(fp.get(r.underlying, np.nan))
        if not (np.isfinite(r.settle) and np.isfinite(F) and r.oi > 0 and r.expiry_date >= d and abs(r.strike / F - 1) < MONEYNESS_MAX):
            continue
        n = int(((tcal >= d) & (tcal < r.expiry_date)).sum())
        if n == 0 and r.expiry_hhmm < T_ENTRY:
            continue
        px_.append(r.settle); F_.append(F); K_.append(float(r.strike)); tau_.append((n * HOURS + HOURS) / YEAR_HOURS)
        rt_.append(r.right); sg_.append(1.0 if r.right == "C" else -1.0); oi_.append(float(r.oi))
    iv = m.implied_vol(np.array(px_), np.array(F_), np.array(K_), np.array(tau_), np.array(rt_))
    g_es = 0.0
    for i in range(len(iv)):
        if np.isfinite(iv[i]):
            g_es += m.b76_gamma_hand(F_[i], K_[i], iv[i], tau_[i]) * sg_[i] * oi_[i] * MULT * F_[i] * F_[i] * 0.01
    bd = b[(b["day"] == d) & (b["hhmm"] <= "15:29")]
    last = bd[bd["hhmm"] == "15:29"].iloc[0]
    rr = 100.0 * math.log(float(last["close"]) / float(fp[last["contract"]]))
    prior = [x for x in I["days"] if x < d][-TRAIL:]
    rets, vols = [], []
    for x in prior:
        bx = b[b["day"] == x]
        cx = bx[bx["hhmm"] == "15:29"]["contract"].iloc[0]
        s_before = st[st["ref"] < x]
        s0 = float(s_before[(s_before["ref"] == s_before["ref"].max()) & (s_before["contract"] == cx)]["settle"].iloc[0])
        s1 = float(st[(st["ref"] == x) & (st["contract"] == cx)]["settle"].iloc[0])
        rets.append(1e4 * math.log(s1 / s0))
        vols.append(float((bx["volume"] * bx["close"] * MULT).sum()))
    sig = float(np.std(rets, ddof=1)); V = float(np.median(vols))
    G = g_spx + g_es
    Q = -G * rr
    return {"Z": sig * math.copysign(1.0, Q) * math.sqrt(abs(Q) / V) if Q != 0 else 0.0, "G_SPX": g_spx, "G_ES": g_es, "r": rr, "sig": sig, "V": V}


def audit_lag(vec: dict[str, dict], sec: dict[str, dict]) -> None:
    for d in sec:
        for k in ("Z", "G_SPX", "G_ES", "r", "sig", "V"):
            a, b_ = vec[d][k], sec[d][k]
            if not np.isclose(a, b_, rtol=1e-9, atol=1e-9):
                raise GateError(f"[LAG] {d} {k}: vectorised {a!r} vs second path {b_!r}")


# ------------------------------------------------------------------ the statistics
def nw_fit(y, cols):
    X = sm.add_constant(np.column_stack(cols))
    return sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": NW_LAG})


def rot_ks(n: int) -> np.ndarray:
    """Column 0 is k = 0 (the observed series); the null is k = 10 .. n-10, every offset, so its p95 has SE 0."""
    return np.concatenate([[0], np.arange(SHIFT_MIN, n - SHIFT_MIN + 1)])


def rotate(G: np.ndarray, ks: np.ndarray) -> np.ndarray:
    """Column j is np.roll(G, ks[j])."""
    n = len(G)
    return G[(np.arange(n)[:, None] - ks[None, :]) % n]


def fwl_betas(y, Zm, C):
    """The slope on each column of Zm with the controls C partialled out (Frisch-Waugh-Lovell), one batch."""
    X = np.column_stack([np.ones(len(y))] + list(C))
    Qx, _ = np.linalg.qr(X)
    ry = y - Qx @ (Qx.T @ y)
    rZ = Zm - Qx @ (Qx.T @ Zm)
    return (rZ * ry[:, None]).sum(0) / (rZ * rZ).sum(0)


def audit_rotation_identity(G, ks, Zm_fn) -> None:
    """k = 0 must be the observed series exactly, and k = 10 must not be."""
    R = rotate(G, ks)
    if not np.array_equal(R[:, 0], G):
        raise GateError("[ROTATION] the k = 0 column is not the observed gamma series")
    if np.array_equal(R[:, 1], G):
        raise GateError("[ROTATION] the first null offset reproduces the observed series")


def gamma_regression(y, G, r, sig, V, A_L, form="sqrt", null=True) -> tuple[dict, np.ndarray | None]:
    """Gate 1's regression for one outcome window: y on the gamma push, r, Z_L and sigma_d. Returns the fit and the
    batch of rotated slopes (column 0 = observed)."""
    Z = zpush(G, r, sig, V) if form == "sqrt" else qraw(G, r)
    ZL = zletf(A_L, r, sig, V)
    C = [r, ZL, sig]
    res = nw_fit(y, [Z] + C)
    out = {"beta_G": float(res.params[1]), "t_G": float(res.tvalues[1]), "beta_r": float(res.params[2]), "t_r": float(res.tvalues[2]),
           "beta_L": float(res.params[3]), "t_L": float(res.tvalues[3]), "beta_sig": float(res.params[4]), "t_sig": float(res.tvalues[4]),
           "n": int(len(y)), "r2": float(res.rsquared)}
    if not null:
        return out, None
    ks = rot_ks(len(y))
    Gm = rotate(G, ks)
    Zm = zpush(Gm, r[:, None], sig[:, None], V[:, None]) if form == "sqrt" else qraw(Gm, r[:, None])
    b = fwl_betas(y, Zm, C)
    if not abs(b[0] - out["beta_G"]) <= 1e-9 * max(1.0, abs(out["beta_G"])):
        raise GateError(f"[ROTATION] the batched k = 0 slope {b[0]!r} is not the regression's {out['beta_G']!r}")
    out["rotation_null"] = blk(b[0], b[1:])
    return out, b


# ------------------------------------------------------------------ Gate 2 (vectorised over rotation columns)
def _prior_cum(a):
    c = np.cumsum(a, axis=0)
    o = np.zeros_like(c)
    o[1:] = c[:-1]
    return o


def gate2_book(Zm, Gm, R2, dpts, P1530, cost_rt, usd_pt):
    """Per column: pi = the through-origin slope of sign(Z) R2 on |Z| over PRIOR sessions, by regime (G < 0 / >= 0) once
    the regime has MIN_REG prior sessions, pooled before; no trade in the first BURN sessions. Trade 1 contract in the
    sign of Z when pi |Z| (bp) in dollars >= K_EP x the round trip."""
    Zm = np.atleast_2d(Zm.T).T if Zm.ndim == 1 else Zm
    Gm = np.atleast_2d(Gm.T).T if Gm.ndim == 1 else Gm
    x = np.abs(Zm); s = np.sign(Zm); y = s * R2[:, None]
    neg = (Gm < 0).astype(float); pos = 1.0 - neg
    with np.errstate(invalid="ignore", divide="ignore"):
        pool = _prior_cum(x * y) / _prior_cum(x * x)
        pn = _prior_cum(x * y * neg) / _prior_cum(x * x * neg)
        pp = _prior_cum(x * y * pos) / _prior_cum(x * x * pos)
    cn, cp = _prior_cum(neg), _prior_cum(pos)
    reg_pi = np.where(neg > 0, pn, pp); reg_n = np.where(neg > 0, cn, cp)
    pi = np.where(reg_n >= MIN_REG, reg_pi, pool)
    live = (np.arange(len(R2)) >= BURN)[:, None]
    proj = pi * x / 1e4 * P1530[:, None] * usd_pt
    with np.errstate(invalid="ignore"):
        trade = live & (x > 0) & np.isfinite(pi) & (proj >= K_EP * cost_rt)
    gross = np.where(trade, s * dpts[:, None] * usd_pt, 0.0)
    net = gross - trade * cost_rt
    return {"trade": trade, "gross": gross, "net": net, "pi": pi, "sign": s}


def audit_prior_only(Z, G, R2, pi, idx, include_today=False) -> None:
    """Second implementation of pi at sampled sessions: explicit loops over the prior sessions."""
    for t in idx:
        hi = t + 1 if include_today else t
        xy = xx = xyr = xxr = 0.0; nr = 0
        for u in range(hi):
            xu, yu = abs(Z[u]), np.sign(Z[u]) * R2[u]
            xy += xu * yu; xx += xu * xu
            if (G[u] < 0) == (G[t] < 0):
                xyr += xu * yu; xxr += xu * xu; nr += 1
        ref = (xyr / xxr if xxr > 0 else np.nan) if nr >= MIN_REG else (xy / xx if xx > 0 else np.nan)
        if not (np.isclose(ref, pi[t], rtol=1e-9, atol=1e-12) or (np.isnan(ref) and np.isnan(pi[t]))):
            raise GateError(f"[PRIOR-ONLY] session {t}: pi {pi[t]!r} vs the loop's {ref!r}")


def audit_sign_in_money(zfun=zpush) -> float:
    """Dealers short gamma (G < 0), an up day (r > 0): they must buy, so Z > 0, the book is long, and a rising close pays."""
    Z = float(zfun(np.array([-3e9]), np.array([1.0]), np.array([100.0]), np.array([3e11]))[0])
    b = gate2_book(np.full(BURN + 1, Z), np.full(BURN + 1, -3e9), np.full(BURN + 1, 10.0), np.full(BURN + 1, 5.0),
                   np.full(BURN + 1, 4000.0), 1.0, 5.0)
    pnl = float(b["gross"][-1, 0])
    if not (Z > 0 and b["sign"][-1, 0] > 0 and pnl > 0):
        raise GateError(f"[SIGN] short gamma on an up day gave Z {Z:+.3f}, side {b['sign'][-1, 0]:+.0f}, P&L {pnl:+.2f}")
    return pnl


def audit_right_quantity(a, b_, what) -> None:
    a, b_ = np.asarray(a, float), np.asarray(b_, float)
    if np.allclose(a, b_, equal_nan=True):
        raise GateError(f"[RIGHT QUANTITY] {what}: the two arrays are the same")


def audit_repro(c: float) -> None:
    if not abs(c - D581_C) <= 1e-12:
        raise GateError(f"[REPRO] D581's T1 c {c!r} vs the recorded {D581_C!r}")


def guard_outputs(res: dict) -> None:
    miss = [k for k in REQUIRED_OUTPUTS if k not in res]
    if miss:
        raise GateError(f"[OUTPUTS] missing {miss}")


# ------------------------------------------------------------------ books and the four groups
def book_report(gross, net, trade, sign, days, arm, cost_rt) -> dict:
    E = d685()
    n = len(net); nt = int(trade.sum()); yrs = n / 252.0
    tn, tg = net[trade], gross[trade]
    tpy = nt / yrs if yrs > 0 else float("nan")

    def per_trade_sharpe(x):
        return float(x.mean() / x.std(ddof=1) * math.sqrt(tpy)) if len(x) > 2 and x.std(ddof=1) > 0 else float("nan")

    def side(x):
        return {"sharpe_daily": E.sharpe(x), "sortino_daily": E.sortino(x), "total_usd": float(x.sum()),
                "vol_ann_usd": float(x.std(ddof=1) * math.sqrt(252)), "max_dd_usd": E.max_dd(x)}

    out = {"sessions": n, "trades": nt, "trades_per_year": tpy, "exposure_share_of_sessions": nt / n if n else float("nan"),
           "cost_rt_usd": cost_rt}
    if nt < 3:
        out["note"] = "fewer than three trades"
        return out
    out["net"] = side(net) | {"mean_per_trade_usd": float(tn.mean()), "nw_per_trade": E.nw_mean(tn, NW_LAG), "per_trade_sharpe_by_own_count": per_trade_sharpe(tn)}
    out["gross"] = side(gross) | {"mean_per_trade_usd": float(tg.mean()), "nw_per_trade": E.nw_mean(tg, NW_LAG), "per_trade_sharpe_by_own_count": per_trade_sharpe(tg)}
    out["mean_gross_per_trade_vs_2c"] = {"mean_gross_usd": float(tg.mean()), "two_c_usd": 2 * cost_rt, "ratio": float(tg.mean() / (2 * cost_rt))}
    out["breakeven_cost_rt_usd"] = float(tg.mean())
    out["hit_rate_net"] = float((tn > 0).mean()); out["hit_rate_gross"] = float((tg > 0).mean())
    out["trade_distribution_net_usd"] = E.dist(tn); out["trade_distribution_gross_usd"] = E.dist(tg)
    sg = sign[trade]
    out["long_short"] = {"long": {"n": int((sg > 0).sum()), "net_usd": float(tn[sg > 0].sum())}, "short": {"n": int((sg < 0).sum()), "net_usd": float(tn[sg < 0].sum())}}
    yr = np.array([d[:4] for d in days])
    out["by_year"] = {y: {"trades": int(trade[yr == y].sum()), "net_usd": float(net[yr == y].sum()), "gross_usd": float(gross[yr == y].sum())} for y in sorted(set(yr))}
    out["profitable_years_net"] = int(sum(v["net_usd"] > 0 for v in out["by_year"].values()))
    era = np.asarray(days) >= ERA_SPLIT
    out["eras"] = {lab: {"trades": int(trade[msk].sum()), "net_usd": float(net[msk].sum()), "gross_usd": float(gross[msk].sum()),
                         "sharpe_net": E.sharpe(net[msk]), "sortino_net": E.sortino(net[msk])} for lab, msk in (("2016_2021", ~era), ("2022_2023", era))}
    srt = np.sort(tn)[::-1]; tot = float(tn.sum())
    out["dependence"] = {"total_net_usd": tot,
                         "top_share_of_net": {str(k): (float(srt[:k].sum() / tot) if tot > 0 else None) for k in (1, 5, 10)},
                         "trades_to_half_of_net": (int(np.argmax(np.cumsum(srt) >= 0.5 * tot)) + 1) if tot > 0 else None,
                         "top_trades": [{"session": str(days[i]), "side": int(sign[i]), "gross_usd": float(gross[i]), "net_usd": float(net[i])}
                                        for i in np.flatnonzero(trade)[np.argsort(-np.abs(tn))][:5]]}
    if arm is not None:
        pos_of = {d: i for i, d in enumerate(days)}
        x = np.array([net[pos_of[d]] if d in pos_of else 0.0 for d in arm["days"]])
        out["rho_with_macd_arm"] = float(np.corrcoef(x, arm["net"])[0, 1]) if x.std() > 0 else float("nan")
        out["rho_arm_days"] = int(len(arm["days"]))
    return out


# ------------------------------------------------------------------ run
def run(data_root: Path, log=P) -> int:
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    log(f"D688 STAGE 0 -- the dealer-gamma close on ES; spec {SPEC}; nothing dated {CUTOFF} or later is read (the session calendar aside)")
    m = d581(data_root / "fixtures")
    audits = {}
    m.audit_gamma(); m.audit_iv_roundtrip(); audits["d581_gamma_and_iv_audits"] = True
    audits["sign_in_money_pnl"] = audit_sign_in_money()
    audits["sign_audit_raises"] = expect_raise(lambda: audit_sign_in_money(lambda G, r, s, V: zpush(-G, r, s, V)), "the hedge sign inverted", log)
    audits["window_guard_raises"] = expect_raise(lambda: guard_window(["2023-12-29", "2024-01-02"], "synthetic"), "a 2024 row", log)
    letf = _mod("letf_close_flow", "run_letf_close_flow.py")
    if dict(letf.SETS["ES"]) != LETF_SET:
        raise GateError(f"[LETF] D640's ES set {letf.SETS['ES']} is not the declared one")
    audits["letf_set_is_d640s"] = True

    I = load_inputs(data_root, log)
    es581 = m.load_es(log)                                                  # D581's own loader, for its gamma table
    strip_es = I["strip"]
    refs = np.array(sorted(strip_es["ref"].unique()))
    win = [d for d in I["days"] if d >= IN_FROM]
    keep = sorted(set(rng.choice(np.array(win[TRAIL:]), 6, replace=False).tolist()) | {win[0], "2022-06-15"} & set(win))
    strides = [win[i::N_WORKERS] for i in range(N_WORKERS)]
    log(f"  rebuilding the ES books on {len(win)} sessions over {N_WORKERS} processes (D581's gamma table at 15:30 + the prior-close book)")
    tp = time.time()
    with ProcessPoolExecutor(max_workers=N_WORKERS, initializer=_init, initargs=(str(I["fx"]), es581, strip_es, I["cal"], I["tcal"], refs)) as ex:
        futs = [ex.submit(_work, (s, keep)) for s in strides]
        D = build_panel(I, log)                                             # while the workers run
        outs = [f.result() for f in futs]
    busy = sum(o["s"] for o in outs); wall = time.time() - tp
    log(f"  [SPEED] ES books: {wall:.0f} s wall, {busy:.0f} s summed, {busy / wall:.2f}x on {N_WORKERS} processes ({100 * busy / wall / N_WORKERS:.0f}%)")
    t581 = pd.concat([o["t581"] for o in outs]).sort_index()
    prior = pd.concat([o["prior"] for o in outs]).sort_index()
    kept = pd.concat([o["kept"] for o in outs], ignore_index=True)
    audits["oi_keying_rows"] = int(sum(o["rows"] for o in outs))
    if not all(o["oi_ok"] for o in outs):
        raise GateError("[LAG] an option row's OI was published after 10:00 of its session")
    if not all(o["oi_fires"] for o in outs):
        raise GateError("[LAG] the OI keying audit does not fire on OI shifted a session later")
    audits["oi_keying_raises_when_shifted"] = True
    # chunk == whole: the kept sessions recomputed serially, bit for bit
    ser581 = m.gamma_table(kept, es581, strip_es, I["cal"], lambda *a: None)
    serpr = es_book_prior(kept, strip_es, I["tcal"], refs, m)
    for d in ser581.index:
        if not (ser581.loc[d, "F1"] == t581.loc[d, "F1"] and serpr.loc[d, "G_ES"] == prior.loc[d, "G_ES"]):
            raise GateError(f"[CHUNK] {d}: the parallel book differs from the serial one")
    audits["chunk_equals_whole_sessions"] = list(ser581.index)

    # ---- the D581 reproduction, before any statistic of this study ----
    R = es581.join(t581, how="inner")
    R = R[np.isfinite(R["F1"]) & (R["F1"] != 0)]
    fit581 = m.t1_fit(R["R2"].to_numpy(), R["F5"].to_numpy(), np.sign(R["F1"]).to_numpy())
    audit_repro(fit581["c"])
    reproduction = {"d581_T1_c": fit581["c"], "recorded": D581_C, "t_c": fit581["t_c"], "n": fit581["n"], "exact": True,
                    "raises_on_a_perturbed_c": expect_raise(lambda: audit_repro(fit581["c"] + 1e-6), "a perturbed c", log)}
    log(f"  D581 REPRODUCED: T1 c {fit581['c']:+.6f} (t {fit581['t_c']:+.2f}, n {fit581['n']}) from D581's own code")

    # ---- the panel ----
    D = D.join(prior[["G_ES", "n_used", "n_offcal_live"]], how="left").join(t581[["F1"]].rename(columns={"F1": "G_ES_1530"}), how="left")
    D = D[D.index >= IN_FROM]
    D["G_SUM"] = D["G_SPX"] + D["G_ES"]
    need = ["P1530", "P1600", "P1100", "P1130", "P1550", "S_prev", "sig", "V", "G_SPX", "G_ES", "A_L"] + ["P" + t.replace(":", "") for t in CLOCK]
    ok = np.isfinite(D[need].to_numpy(float)).all(1)
    dropped = {c: int((~np.isfinite(D[c].to_numpy(float))).sum()) for c in need if (~np.isfinite(D[c].to_numpy(float))).any()}
    D = D[ok].copy()
    days = D.index.to_numpy().astype(str)
    guard_window(days, "panel")
    n = len(D)
    log(f"  panel: {n} sessions {days[0]} .. {days[-1]}; dropped for a missing input: {dropped}")
    # same prices as D581 where both exist
    common = D.index.intersection(es581.index)
    if not np.array_equal(D.loc[common, "P1530"].to_numpy(), es581.loc[common, "P1530"].to_numpy()):
        raise GateError("[PRICE] P(15:30) differs from D581's on a common session")
    audits["p1530_equals_d581s_sessions"] = int(len(common))

    def pr(t):
        return D["P" + t.replace(":", "")].to_numpy(float)

    def rto(t):
        return 100.0 * np.log(pr(t) / D["S_prev"].to_numpy(float))

    def win_ret(a, b_):
        return 1e4 * np.log(pr(b_) / pr(a))

    sig = D["sig"].to_numpy(float); V = D["V"].to_numpy(float); A_L = D["A_L"].to_numpy(float)
    G_SUM = D["G_SUM"].to_numpy(float); G_SPX = D["G_SPX"].to_numpy(float); G_ES = D["G_ES"].to_numpy(float); G_1530 = D["G_ES_1530"].to_numpy(float)
    r1530 = rto("15:30"); R2 = win_ret("15:30", "16:00")
    Z = zpush(G_SUM, r1530, sig, V)

    # ---- the lag audit: the second path on sampled sessions, and it fires on the same-day GEX row ----
    sec = {d: second_path(d, I, kept[kept["session"] == d], m) for d in keep if d in D.index}
    pos = {d: i for i, d in enumerate(days)}
    vec = {d: {"Z": Z[pos[d]], "G_SPX": G_SPX[pos[d]], "G_ES": G_ES[pos[d]], "r": r1530[pos[d]], "sig": sig[pos[d]], "V": V[pos[d]]} for d in sec}
    audit_lag(vec, sec)
    Zbad = zpush(D["G_SPX_sameday"].to_numpy(float) + G_ES, r1530, sig, V)
    audits["lag_second_path_sessions"] = sorted(sec)
    audits["lag_audit_raises_on_same_day_gex"] = expect_raise(lambda: audit_lag({d: vec[d] | {"Z": Zbad[pos[d]]} for d in sec}, sec), "the same-day GEX row", log)
    audit_right_quantity(G_ES, G_1530, "the prior-close ES book vs D581's 15:30 book")
    audits["right_quantity_es_book"] = expect_raise(lambda: audit_right_quantity(G_ES, G_ES.copy(), "a copy"), "an identical book", log)
    audit_right_quantity(pr("15:30"), pr("15:00"), "P(15:30) vs P(15:00)")
    audits["right_quantity_entry_price"] = expect_raise(lambda: audit_right_quantity(pr("15:30"), pr("15:30").copy(), "a copy"), "an identical entry price", log)
    ks = rot_ks(n)
    audit_rotation_identity(G_SUM, ks, None)
    audits["rotation_identity"] = True
    audits["rotation_identity_raises"] = expect_raise(lambda: audit_rotation_identity(G_SUM, np.concatenate([[1], ks[1:]]), None), "k = 1 in column 0", log)

    # ---- premise (aggregate statistics only) ----
    yrs = sorted(set(D["year"]))
    yv = D["year"].to_numpy()
    premise = {"abs_median_by_year_usd_bn": {y: {"G_SPX": float(np.median(np.abs(G_SPX[yv == y])) / 1e9), "G_ES_prior_close": float(np.median(np.abs(G_ES[yv == y])) / 1e9),
                                                 "G_ES_1530_d581": float(np.median(np.abs(G_1530[yv == y])) / 1e9), "G_SUM": float(np.median(np.abs(G_SUM[yv == y])) / 1e9)} for y in yrs},
               "share_short_gamma_by_year": {y: {"G_SUM": float((G_SUM[yv == y] < 0).mean()), "G_SPX": float((G_SPX[yv == y] < 0).mean()), "G_ES": float((G_ES[yv == y] < 0).mean())} for y in yrs},
               "share_short_gamma": {"G_SUM": float((G_SUM < 0).mean()), "G_SPX": float((G_SPX < 0).mean()), "G_ES": float((G_ES < 0).mean()), "G_ES_1530": float((G_1530 < 0).mean())},
               "corr_G_SPX_G_ES": float(np.corrcoef(G_SPX, G_ES)[0, 1]), "sign_agreement_G_SPX_G_ES": float((np.sign(G_SPX) == np.sign(G_ES)).mean()),
               "abs_Z_bp_quantiles": {q: float(np.quantile(np.abs(Z), float(q))) for q in ("0.5", "0.9", "0.99")},
               "R2_sd_bp": float(R2.std(ddof=1)), "sigma_d_median_bp": float(np.median(sig)), "V_median_usd_bn": float(np.median(V) / 1e9),
               "offcalendar_live_option_rows_total_every_trading_day_calendar": int(D["n_offcal_live"].sum()), "options_used_median_prior_close": float(D["n_used"].median())}
    log(f"  premise: short-gamma share SUM {premise['share_short_gamma']['G_SUM']:.3f} SPX {premise['share_short_gamma']['G_SPX']:.3f} ES {premise['share_short_gamma']['G_ES']:.3f}; "
        f"corr(SPX, ES) {premise['corr_G_SPX_G_ES']:+.2f}; |Z| p50/p90/p99 " + "/".join(f"{v:.1f}" for v in premise["abs_Z_bp_quantiles"].values()) + " bp; "
        "|G| medians $bn " + " ".join(f"{y}:{v['G_SPX']:.1f}+{v['G_ES_prior_close']:.1f}" for y, v in premise["abs_median_by_year_usd_bn"].items()))

    # ---- Gate 1 ----
    g1, b_close = gamma_regression(R2, G_SUM, r1530, sig, V, A_L)
    r1100 = rto("11:00"); R11 = win_ret("11:00", "11:30")
    plc, b_11 = gamma_regression(R11, G_SUM, r1100, sig, V, A_L)
    diff = b_close - b_11
    g2 = {"beta_close_minus_beta_1100": float(diff[0]), "rotation_null": blk(diff[0], diff[1:]), "placebo_fit": plc}
    G1_pass = bool(g1["beta_G"] > 0 and g1["t_G"] >= 2.0 and g1["rotation_null"]["above_p95"])
    G2_pass = bool(g2["rotation_null"]["above_p95"])
    gate1 = {"G1": g1, "G1_pass": G1_pass, "G2": g2, "G2_pass": G2_pass, "pass": bool(G1_pass and G2_pass)}
    log(f"  GATE 1  G1: beta_G {g1['beta_G']:+.4f} (NW t {g1['t_G']:+.2f}), rotation p50 {g1['rotation_null']['p50']:+.4f} p95 {g1['rotation_null']['p95']:+.4f} "
        f"pct {g1['rotation_null']['pct_rank']:.3f} ({g1['rotation_null']['n_offsets']} offsets); beta_r {g1['beta_r']:+.3f} (t {g1['t_r']:+.2f}), "
        f"beta_L {g1['beta_L']:+.3f} (t {g1['t_L']:+.2f}), beta_sig {g1['beta_sig']:+.4f} (t {g1['t_sig']:+.2f}); n {g1['n']} -> {'PASS' if G1_pass else 'FAIL'}")
    log(f"          G2: beta(11:00) {plc['beta_G']:+.4f} (t {plc['t_G']:+.2f}); close - 11:00 {diff[0]:+.4f}, p50 {g2['rotation_null']['p50']:+.4f} "
        f"p95 {g2['rotation_null']['p95']:+.4f} pct {g2['rotation_null']['pct_rank']:.3f} -> {'PASS' if G2_pass else 'FAIL'}")

    # ---- Gate 2 (and its rotation null) ----
    E = d685()
    mes, esf = E.cost_spec("ES", "micro"), E.cost_spec("ES", "full")
    P1530 = pr("15:30"); dpts = pr("16:00") - P1530
    Gm = rotate(G_SUM, ks)
    Zm = zpush(Gm, r1530[:, None], sig[:, None], V[:, None])
    if not np.array_equal(Zm[:, 0], Z):
        raise GateError("[ROTATION] the k = 0 push column is not the observed push")
    bk = gate2_book(Zm, Gm, R2, dpts, P1530, mes["cost_rt_usd"], mes["usd_per_point"])
    samp = sorted(rng.choice(np.arange(BURN, n), 8, replace=False).tolist()) + [BURN, n - 1]
    audit_prior_only(Z, G_SUM, R2, bk["pi"][:, 0], samp)
    audits["prior_only_sessions"] = samp
    audits["prior_only_raises_with_today"] = expect_raise(lambda: audit_prior_only(Z, G_SUM, R2, bk["pi"][:, 0], samp, include_today=True), "today's return in pi", log)
    tr0 = bk["trade"][:, 0]; net0 = bk["net"][:, 0]; gross0 = bk["gross"][:, 0]
    nt = int(tr0.sum())
    ntr = bk["trade"].sum(0)
    with np.errstate(invalid="ignore", divide="ignore"):
        mean_net_cols = bk["net"].sum(0) / ntr
    shp_cols = bk["net"].mean(0) / bk["net"].std(0, ddof=1) * math.sqrt(252)
    nwt = E.nw_mean(net0[tr0], NW_LAG) if nt >= 3 else {"t": float("nan"), "mean": float("nan"), "n": nt}
    if nt < MIN_TRADES:
        g2v = "UNRESOLVED"
    else:
        g2v = "PASS" if nwt["t"] >= 2.0 else "FAIL"
    pi_last = bk["pi"][-1, 0]
    gate2 = {"trades": nt, "min_trades": MIN_TRADES, "net_mean_per_trade_usd": nwt["mean"], "nw_t_per_trade": nwt["t"], "verdict": g2v,
             "net_per_session_nw": E.nw_mean(net0, NW_LAG),
             "rotation_null_net_mean_per_trade": blk(mean_net_cols[0], mean_net_cols[1:]) if nt else None,
             "rotation_null_net_sharpe_daily": blk(shp_cols[0], shp_cols[1:]) if nt else None,
             "rotation_null_trade_count": blk(float(nt), ntr[1:].astype(float)),
             "pi_at_last_session_bp_per_bp": float(pi_last),
             "regime_trades": {"short_gamma": int((tr0 & (G_SUM < 0)).sum()), "long_gamma": int((tr0 & (G_SUM >= 0)).sum())},
             "threshold_usd": K_EP * mes["cost_rt_usd"]}
    log(f"  GATE 2  {nt} MES trades; net mean ${nwt['mean']:+.2f}/trade, NW t {nwt['t']:+.2f} -> {g2v}; "
        f"rotation trade count p50 {gate2['rotation_null_trade_count']['p50']:.0f}")

    # ---- books: the gated book and an unfiltered sign(Z) book, at MES and full ES ----
    try:
        arm = E.load_arm()
    except Exception as e:                                                     # the component line is declared: fail loudly
        raise GateError(f"[ARM] the MACD arm could not be loaded for rho: {e}") from e
    s0 = np.sign(Z); trU = s0 != 0
    books = {}
    for lab, cs in (("mes", mes), ("es_full", esf)):
        if lab == "mes":
            bg = {k: v[:, 0] for k, v in bk.items()}
        else:
            bg = {k: v[:, 0] for k, v in gate2_book(Z[:, None], G_SUM[:, None], R2, dpts, P1530, cs["cost_rt_usd"], cs["usd_per_point"]).items()}
        books[f"gate2_{lab}"] = book_report(bg["gross"], bg["net"], bg["trade"], bg["sign"], days, arm, cs["cost_rt_usd"])
        gU = np.where(trU, s0 * dpts * cs["usd_per_point"], 0.0); nU = gU - trU * cs["cost_rt_usd"]
        books[f"unfiltered_{lab}"] = book_report(gU, nU, trU, s0, days, arm, cs["cost_rt_usd"])
    # the unfiltered book's rotation null (gross mean per session, in bp)
    gross_bp_cols = (np.sign(Zm) * R2[:, None]).mean(0)
    books["unfiltered_gross_bp_per_session_rotation_null"] = blk(gross_bp_cols[0], gross_bp_cols[1:])
    for k in ("gate2_mes", "unfiltered_mes"):
        v = books[k]
        if "net" in v:
            log(f"  book {k}: {v['trades']} trades ({v['trades_per_year']:.0f}/yr); net Sharpe {v['net']['sharpe_daily']:+.2f} Sortino {v['net']['sortino_daily']:+.2f}; "
                f"gross Sharpe {v['gross']['sharpe_daily']:+.2f} Sortino {v['gross']['sortino_daily']:+.2f}; mean gross ${v['gross']['mean_per_trade_usd']:+.2f} vs 2c ${2 * v['cost_rt_usd']:.2f}; "
                f"hit {v['hit_rate_net']:.3f}; rho arm {v.get('rho_with_macd_arm', float('nan')):+.3f}")

    # ---- beside ----
    beside = {}
    for lab, G in (("spx_only", G_SPX), ("es_only_prior_close", G_ES), ("es_d581_1530", G_1530)):
        beside[lab], _ = gamma_regression(R2, G, r1530, sig, V, A_L)
    beside["sum_raw_form"], _ = gamma_regression(R2, G_SUM, r1530, sig, V, A_L, form="raw")
    beside["outcome_1550_1600"], _ = gamma_regression(win_ret("15:50", "16:00"), G_SUM, rto("15:50"), sig, V, A_L)
    beside["clock_profile"] = {}
    for a, b_ in zip(CLOCK[:-1], CLOCK[1:]):
        f, _ = gamma_regression(win_ret(a, b_), G_SUM, rto(a), sig, V, A_L)
        beside["clock_profile"][f"{a}-{b_}"] = {k: f[k] for k in ("beta_G", "t_G", "beta_r", "t_r", "n")} | {"rotation_pct": f["rotation_null"]["pct_rank"], "rotation_p95": f["rotation_null"]["p95"]}
    beside["regimes"] = {}
    for lab, msk in (("short_gamma", G_SUM < 0), ("long_gamma", G_SUM >= 0)):
        f, _ = gamma_regression(R2[msk], G_SUM[msk], r1530[msk], sig[msk], V[msk], A_L[msk], null=False)
        beside["regimes"][lab] = f
    era = days >= ERA_SPLIT
    beside["eras"] = {}
    for lab, msk in (("2016_2021", ~era), ("2022_2023", era)):
        f, _ = gamma_regression(R2[msk], G_SUM[msk], r1530[msk], sig[msk], V[msk], A_L[msk])
        beside["eras"][lab] = f
    beside["by_year"] = {}
    for y in yrs:
        msk = yv == y
        f, _ = gamma_regression(R2[msk], G_SUM[msk], r1530[msk], sig[msk], V[msk], A_L[msk], null=False)
        beside["by_year"][y] = {k: f[k] for k in ("beta_G", "t_G", "n")}
    log("  beside: " + " | ".join(f"{k} b {beside[k]['beta_G']:+.4f} t {beside[k]['t_G']:+.2f} pct {beside[k]['rotation_null']['pct_rank']:.2f}"
                                  for k in ("spx_only", "es_only_prior_close", "es_d581_1530", "sum_raw_form", "outcome_1550_1600")))
    log("  clock: " + " ".join(f"{k[:5]}:{v['beta_G']:+.3f}({v['t_G']:+.1f})" for k, v in beside["clock_profile"].items()))
    log("  regimes: " + " | ".join(f"{k} b {v['beta_G']:+.4f} t {v['t_G']:+.2f} n {v['n']}" for k, v in beside["regimes"].items())
        + "; eras: " + " | ".join(f"{k} b {v['beta_G']:+.4f} t {v['t_G']:+.2f} pct {v['rotation_null']['pct_rank']:.2f}" for k, v in beside["eras"].items()))
    log("  by year: " + " ".join(f"{y}:{v['beta_G']:+.3f}({v['t_G']:+.1f})" for y, v in beside["by_year"].items()))

    # ---- predictions (s.8) and the verdict (s.5) ----
    preds = {
        "1_beta_positive_but_gate1_fails": bool(g1["beta_G"] > 0 and not gate1["pass"]),
        "2_spx_and_sum_same_sign_es_weaker": bool(np.sign(beside["spx_only"]["beta_G"]) == np.sign(g1["beta_G"]) and abs(beside["es_only_prior_close"]["t_G"]) < abs(g1["t_G"])),
        "3_short_gamma_beta_exceeds_long": bool(beside["regimes"]["short_gamma"]["beta_G"] > beside["regimes"]["long_gamma"]["beta_G"]),
        "4_placebo_at_least_half_the_close": bool(g1["beta_G"] > 0 and plc["beta_G"] >= 0.5 * g1["beta_G"]),
        "5_beta_r_positive": bool(g1["beta_r"] > 0),
        "6_2022_23_exceeds_2016_21": bool(beside["eras"]["2022_2023"]["beta_G"] > beside["eras"]["2016_2021"]["beta_G"]),
        "7_if_gate1_passes_gate2_fails": (None if not gate1["pass"] else bool(g2v != "PASS")),
    }
    verdict = "SUPPORTED" if gate1["pass"] and g2v == "PASS" else "MECHANISM ONLY" if gate1["pass"] else "NOT SUPPORTED"
    log("  predictions: " + "; ".join(f"{k} {v}" for k, v in preds.items()))
    log(f"  VERDICT: {verdict} (Gate 1 {'PASS' if gate1['pass'] else 'FAIL'}, Gate 2 {g2v})")
    res = {"spec": SPEC, "windows": {"panel": [days[0], days[-1]], "cutoff": CUTOFF, "warm_from": WARM_FROM,
                                     "note": "the session calendar (dates and bar counts) is read in full, as D581 read it; no price, option, GEX or AUM row on or after the cutoff"},
           "audits": audits, "reproduction": reproduction,
           "sets": {"sessions": n, "dropped_for_missing_input": dropped, "option_rows_read": audits["oi_keying_rows"]},
           "premise": premise, "gate1": gate1, "gate2": gate2, "beside": beside, "books": books, "predictions": preds, "verdict": verdict,
           "construction": {"G": "SqueezeMetrics SPX GEX (last row strictly before d) + ES options at the prior settlement, $ per 1 %; calls +, puts -",
                            "Z": "sigma_d sign(Q) sqrt(|Q|/V), Q = -G r, r from the prior settlement in %, sigma_d bp, V $ (20 sessions through d-1)",
                            "controls": "r, Z_L (D640's ES set, AUM on the last date before d within 7 days, same square-root form), sigma_d",
                            "nw_lag": NW_LAG, "rotation": f"k = 0 and {SHIFT_MIN} .. n-{SHIFT_MIN}, every offset", "burn_in": BURN, "min_regime": MIN_REG, "k_ep": K_EP,
                            "costs": {"mes": mes, "es_full": esf}, "workers": N_WORKERS,
                            "credit": "SqueezeMetrics (squeezemetrics.com); statistics only, no per-date GEX"},
           "timing_s": round(time.time() - t0, 1)}
    guard_outputs(res)
    audits["outputs_guard_raises"] = expect_raise(lambda: guard_outputs({k: v for k, v in res.items() if k != "gate1"}), "a missing declared output", log)
    OUT.write_text(json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)), encoding="utf-8")
    log(f"  wrote {OUT.relative_to(REPO)} in {res['timing_s']} s")
    return 0


# ------------------------------------------------------------------ self-test (synthetic; no fixture is read)
def selftest(log=P) -> int:
    rng = np.random.default_rng(6810)
    m = d581()
    m.audit_gamma(); m.audit_iv_roundtrip(); log("  D581's gamma closed form and IV round trip pass")
    log(f"  sign in money: P&L {audit_sign_in_money():+.2f} on a short-gamma up day")
    expect_raise(lambda: audit_sign_in_money(lambda G, r, s, V: zpush(-G, r, s, V)), "the hedge sign inverted", log)
    expect_raise(lambda: guard_window(["2023-12-29", "2024-01-02"], "synthetic"), "a 2024 row", log)
    expect_raise(lambda: audit_right_quantity(np.arange(5.0), np.arange(5.0), "synthetic"), "an identical array", log)
    expect_raise(lambda: audit_repro(D581_C + 1e-6), "a perturbed c", log)
    expect_raise(lambda: guard_outputs({"spec": 1}), "missing outputs", log)
    v = {"d": {"Z": 1.0, "G_SPX": 2.0, "G_ES": 3.0, "r": 0.1, "sig": 90.0, "V": 1e11}}
    audit_lag(v, v); expect_raise(lambda: audit_lag({"d": v["d"] | {"Z": 1.1}}, v), "a shifted push", log)
    # a synthetic panel with the mechanism built in, and one without
    n = 1200
    G = np.cumsum(rng.normal(0, 2e8, n)) + 2e9
    r = rng.normal(0, 0.8, n); sig = np.full(n, 90.0) + rng.normal(0, 5, n); V = np.full(n, 2e11); A = np.full(n, 5e10)
    Z = zpush(G, r, sig, V)
    y = 0.8 * Z + rng.normal(0, 20, n)
    ks = rot_ks(n)
    audit_rotation_identity(G, ks, None); expect_raise(lambda: audit_rotation_identity(G, np.concatenate([[1], ks[1:]]), None), "k = 1 in column 0", log)
    f, _ = gamma_regression(y, G, r, sig, V, A)
    if not (f["beta_G"] > 0.5 and f["rotation_null"]["above_p95"]):
        raise GateError(f"selftest: the built-in mechanism was not found: {f['beta_G']:+.3f} pct {f['rotation_null']['pct_rank']:.3f}")
    fn, _ = gamma_regression(rng.normal(0, 20, n), G, r, sig, V, A)
    log(f"  Gate 1 on a built-in mechanism: beta {f['beta_G']:+.3f} pct {f['rotation_null']['pct_rank']:.3f}; on noise: beta {fn['beta_G']:+.3f} pct {fn['rotation_null']['pct_rank']:.3f}")
    bk = gate2_book(Z[:, None], G[:, None], y, y / 1e4 * 4000.0, np.full(n, 4000.0), 4.42, 5.0)
    idx = [BURN, BURN + 7, n - 1]
    audit_prior_only(Z, G, y, bk["pi"][:, 0], idx)
    expect_raise(lambda: audit_prior_only(Z, G, y, bk["pi"][:, 0], idx, include_today=True), "today's return in pi", log)
    nt = int(bk["trade"][:, 0].sum())
    if not (nt > 0 and bk["net"][:, 0].sum() > 0 and not bk["trade"][:BURN, 0].any()):
        raise GateError(f"selftest: Gate 2 on a built-in mechanism: {nt} trades, net {bk['net'][:, 0].sum():+.1f}")
    log(f"  Gate 2 on a built-in mechanism: {nt} trades, net ${bk['net'][:, 0].sum():+,.0f}, none in the burn-in")
    log("  selftest: every audit passes its clean case and raises on its break")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else run(a.data_root) if a.run else 1)
