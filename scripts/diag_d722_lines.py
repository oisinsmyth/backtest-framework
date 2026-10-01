"""D722 Phase 0a: the per-trade tables of D722 s.1, regenerated in-sample through each line's own imported code path,
checked against each line's recorded known answer, and cached. Spec:
docs/decisions/D722-DIAG-PRE-REG-why-2022-scale-regime-or-one-bet.md (f25e4726).

    uv run python scripts/diag_d722_lines.py --build        # build or refresh the cache; prints the checks
    uv run python scripts/diag_d722_lines.py --selftest     # the clean case passes; every gate raises on a break
    uv run python scripts/diag_d722_lines.py --selftest --serial-proof   # also: a serial build == the parallel cache

Phase 1 imports `load_lines()` and `known_answers(df)`.

THE TABLE (one row per trade; `load_lines`):
  line         L1 ES F2 (D707) | L2 NQ F2, D716's book B | L3 D699 V1 | L4 D719 HO F2 | K1 the MACD arm (D508's load_arm)
               | K2_ES / K2_NQ take-everything 15:30 -> 16:00 (D711)
  root         ES | NQ | HO
  session      "YYYY-MM-DD"
  side         +1 long / -1 short. K1: the side of every trip that session when all trips share one side, else 0
               (a session whose trips flipped); recovered by replaying D491's state machine, proved equal to it.
  entry_min    minutes after 09:30 ET of the fill (the price AT that minute: the close of the bar starting one minute
  exit_min     earlier, D462). Every line uses this one clock, HO included: HO enters at 14:00 ET (270) and exits at
               14:30 ET (300); its bars are labelled in ET from 09:00 (D719 A-2). K1: the open of the hourly segment
               of the FIRST fill, and the exit of the LAST trip (a segment open, or 16:00 = 390 when forced flat).
  hold_min     exit_min - entry_min (K1: the span from the first fill to the last exit, flat time between trips
               included)
  entry_price  the traded unit's price in points at entry_min (K1: the first fill)
  usd_pp       dollars per point of the traded unit (MES 5, MNQ 2, HO full 42,000)
  gross_usd, cost_usd, net_usd   net = gross - cost; K1's cost is trips x the arm's own round trip.

SEALS: no value dated 2024-01-01 or later enters any computation. Every loader here filters the rows of a file that
carries later rows before any computation (D707, D711, D716, D699/D688 and D719 do so themselves; the arm's hourly
fixture is filtered here before D504's build, since D508's load_arm builds over the whole fixture). The vault is never
read; nothing here runs any --vault path.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

OUT_DIR = REPO / "temp" / "d722"
CACHE = OUT_DIR / "lines.csv.gz"
META = OUT_DIR / "lines.meta.json"
SUMMARY = REPO / "data" / "diag_d722_lines_summary.json"
SPEC = "docs/decisions/D722-DIAG-PRE-REG-why-2022-scale-regime-or-one-bet.md (f25e4726)"
SEAL, IN_END = "2024-01-01", "2023-12-29"
LINES = ("L1", "L2", "L3", "L4", "K1", "K2_ES", "K2_NQ")
ROOT_OF = {"L1": "ES", "L2": "NQ", "L3": "ES", "L4": "HO", "K1": "NQ", "K2_ES": "ES", "K2_NQ": "NQ"}
COLS = ["line", "root", "session", "side", "entry_min", "exit_min", "hold_min", "entry_price", "usd_pp", "gross_usd",
        "cost_usd", "net_usd"]
INT_COLS = ("side", "entry_min", "exit_min", "hold_min")
FLOAT_COLS = ("entry_price", "usd_pp", "gross_usd", "cost_usd", "net_usd")
TOL_ROW = 1e-9  # net = gross - cost: exact on every line but K1, whose trips accumulate in ticks (~1e-12 off)
K2_ES_LO = "2018-05-14"   # D711 A1's common start (the max of the six ES clocks' first window sessions)
K2_NQ_LO = "2016-01-01"   # D711 A2's clock_line(X, F, "2016-01-01", arm)

# the known answers (D722 s.1); each is also re-read from its recorded file and the two must agree
KA_L1 = {"trades": 252, "mean_net": 13.208968253968253,
         "take_sessions_sha256": "5427a6c8006773be758d22a475ea2043ab1b87dddac220abf3f344a65c423cbc"}
KA_L2 = {"trades": 271, "mean_net": 20.768672251822206}
KA_L3 = {"trades": 572, "total_net": 5991.570959296225}
KA_L4 = {"trades": 239, "mean_net": 109.21004184100458}
KA_K1 = {"sessions": 1876, "total_net": 15423.0, "tol_usd": 1.0}   # D508 / D667 / D669's REPRO_SESSIONS, REPRO_NET
KA_K2 = {"K2_ES": 1360, "K2_NQ": 1389}

# explicit inputs (the audit hook adds every file the in-process loaders open; D688's worker processes open the
# options file, which only this list can see)
EXPLICIT_INPUTS = (
    "data/fixtures/fut_ES_rth_1m.csv.gz", "data/fixtures/fut_NQ_rth_1m.csv.gz",
    "data/fixtures/fut_sessions_hourly.csv.gz", "data/fixtures/fut_sessions_hourly.meta.json",
    "data/fixtures/fut_es_options_eod.csv.gz", "data/fixtures/fut_settle_strip.csv.gz",
    "data/fixtures/fut_index_sessions.csv.gz", "data/raw/squeezemetrics/DIX.csv", "data/letf/letf_aum_daily.csv.gz",
    "data/fixtures/fut_day1m.parquet", "temp/d719_bars/meta.json", "temp/d719_bars/HO.csv.gz",
    "data/futures_costs.json", "data/futures_contract_specs.json", "data/d688_gamma_close.json",
    "data/d699_gamma_macd_long.json", "data/stage1_d711_f2_mechanism.json", "data/stage1_d719_commodity_settlement_f2.json",
    "data/d504_arm_full_history.json", "data/FROZEN_vault_d707_last_hour_f2.json", "data/FROZEN_vault_d716_nq_f2.json",
    "scripts/diag_d722_lines.py")


class D722Error(RuntimeError):
    pass


class SealError(D722Error):
    pass


class KnownAnswerError(D722Error):
    pass


class RowError(D722Error):
    pass


class StaleCacheError(D722Error):
    pass


def P(*a: Any) -> None:
    print(*a, flush=True)


# ================================================================================ what the build opened
_OPENED: set[str] = set()
_REC = {"on": False, "hooked": False}


def _hook(event: str, args: tuple) -> None:
    if not _REC["on"] or event != "open" or not args:
        return
    p, mode = args[0], (args[1] if len(args) > 1 else "r")
    if isinstance(p, (str, bytes, os.PathLike)) and (mode is None or not any(c in str(mode) for c in "wax+")):
        _OPENED.add(os.fsdecode(p))


@contextlib.contextmanager
def recording() -> Any:
    if not _REC["hooked"]:
        sys.addaudithook(_hook)
        _REC["hooked"] = True
    _REC["on"] = True
    try:
        yield
    finally:
        _REC["on"] = False


def _repo_rel(p: str) -> str | None:
    try:
        q = Path(p).resolve()
        r = q.relative_to(REPO)
    except (ValueError, OSError):
        return None
    s = r.as_posix()
    if s.startswith((".", "temp/d722/")) or "__pycache__" in s or "site-packages" in s or not q.is_file():
        return None
    return s


def _module_files() -> set[str]:
    out = set()
    for m in list(sys.modules.values()):
        f = getattr(m, "__file__", None)
        if f and f.endswith(".py"):
            r = _repo_rel(f)
            if r is not None:
                out.add(r)
    return out


def _stat_key(paths: set[str]) -> dict[str, list[int]]:
    key = {}
    for s in sorted(paths):
        st = (REPO / s).stat()
        key[s] = [int(st.st_size), int(st.st_mtime_ns)]
    return key


def stale_reasons(meta: dict[str, Any]) -> list[str]:
    """Every keyed file must exist with the recorded size and mtime; the table must hash to its recorded sha256."""
    why = []
    for s, (size, mt) in meta.get("key", {}).items():
        p = REPO / s
        if not p.exists():
            why.append(f"missing {s}")
            continue
        st = p.stat()
        if int(st.st_size) != size or int(st.st_mtime_ns) != mt:
            why.append(f"changed {s}")
    if not meta.get("key"):
        why.append("no key recorded")
    if not CACHE.exists():
        why.append("no table")
    elif hashlib.sha256(CACHE.read_bytes()).hexdigest() != meta.get("table_gz_sha256"):
        why.append("the table's bytes differ from the recorded sha256")
    return why


# ================================================================================ shared checks
def _frame(line: str, sess: np.ndarray, side: np.ndarray, ein: np.ndarray, eout: np.ndarray, px: np.ndarray,
           usd: np.ndarray | float, gross: np.ndarray, cost: np.ndarray | float, net: np.ndarray) -> pd.DataFrame:
    n = len(sess)
    f = pd.DataFrame({"line": [line] * n, "root": [ROOT_OF[line]] * n, "session": np.asarray(sess).astype(str),
                      "side": np.asarray(side, float).astype(np.int64), "entry_min": np.asarray(ein, np.int64),
                      "exit_min": np.asarray(eout, np.int64)})
    f["hold_min"] = f["exit_min"] - f["entry_min"]
    f["entry_price"] = np.asarray(px, float)
    f["usd_pp"] = np.broadcast_to(np.asarray(usd, float), (n,)).copy()
    f["gross_usd"] = np.asarray(gross, float)
    f["cost_usd"] = np.broadcast_to(np.asarray(cost, float), (n,)).copy()
    f["net_usd"] = np.asarray(net, float)
    if not np.array_equal(f["side"].to_numpy(float), np.asarray(side, float)):
        raise RowError(f"{line}: a side is not an integer")
    assert_seal(f, line)
    return f[COLS]


def assert_seal(df: pd.DataFrame, what: str = "table") -> None:
    s = df["session"].astype(str)
    if (s >= SEAL).any():
        raise SealError(f"seal: {what} holds a session on or after {SEAL}")


def sign_audit_money(line: str, gross: np.ndarray, side: np.ndarray, p_in: np.ndarray, p_out: np.ndarray,
                     usd: float) -> None:
    """A favourable move pays positively: gross is side x (exit - entry) x $/pt, exactly, on every row."""
    want = np.asarray(side, float) * (np.asarray(p_out, float) - np.asarray(p_in, float)) * usd
    if not np.array_equal(want, np.asarray(gross, float)):
        raise RowError(f"sign: {line}'s gross is not side x (exit - entry) x ${usd}/pt")
    up = np.array([100.0]), np.array([101.0])
    if not ((+1.0 * (up[1] - up[0]) * usd)[0] > 0 and (-1.0 * (up[1] - up[0]) * usd)[0] < 0):
        raise RowError("sign: a long across a rise does not pay, or a short across it does not lose")


def check_rows(df: pd.DataFrame) -> None:
    if list(df.columns) != COLS:
        raise RowError(f"columns {list(df.columns)} are not {COLS}")
    bad = set(df["line"].unique()) - set(LINES)
    if bad:
        raise RowError(f"unknown lines {bad}")
    if not (df["root"].to_numpy(str) == df["line"].map(ROOT_OF).to_numpy(str)).all():
        raise RowError("a row's root is not its line's")
    if not df["side"].isin([-1, 0, 1]).all():
        raise RowError("a side outside {-1, 0, +1}")
    if not (df.loc[df["line"] != "K1", "side"] != 0).all():
        raise RowError("a zero side on a line that always takes a side")
    if not np.array_equal(df["hold_min"].to_numpy(), (df["exit_min"] - df["entry_min"]).to_numpy()):
        raise RowError("hold != exit - entry")
    if not (df["hold_min"] > 0).all() or not ((df["entry_min"] >= 0) & (df["exit_min"] <= 390)).all():
        raise RowError("a hold outside 09:30 -> 16:00 ET or not positive")
    g, c, n = (df[k].to_numpy(float) for k in ("gross_usd", "cost_usd", "net_usd"))
    if not (np.isfinite(g).all() and np.isfinite(c).all() and np.isfinite(n).all()):
        raise RowError("a non-finite dollar value")
    if not (np.abs(n - (g - c)) <= TOL_ROW).all():
        raise RowError("net != gross - cost")
    ex = df["line"] != "K1"
    if not np.array_equal(n[ex.to_numpy()], (g - c)[ex.to_numpy()]):
        raise RowError("net != gross - cost exactly on a line that computes it so")
    if not ((df["entry_price"] > 0) & (df["usd_pp"] > 0) & (df["cost_usd"] > 0)).all():
        raise RowError("a non-positive price, $/pt or cost")


# ================================================================================ the units
def unit_l1() -> tuple[pd.DataFrame, dict[str, Any]]:
    """L1: D707's frame + f2, trades take & window through 2023-12-29 (its in_sample_answer)."""
    import vault_d707_last_hour_f2 as V
    V.E.sign_audit()
    X = V.frame(V.IN_END)
    F = V.f2(X)
    V.audit_tiers(X, F)
    ka = V.in_sample_answer(X, F)
    sess = X.index.to_numpy(str)
    k = F["take"] & F["window"] & (sess <= V.IN_END)
    gross = X["gross"].to_numpy(float)[k]
    net = X["gross"].to_numpy(float)[k] - V.COST
    side = X["side"].to_numpy(float)[k]
    sign_audit_money("L1", gross, side, X["P1530"].to_numpy(float)[k], X["P1600"].to_numpy(float)[k], V.MES_USD)
    f = _frame("L1", sess[k], side, np.full(k.sum(), 360), np.full(k.sum(), 390), X["P1530"].to_numpy(float)[k],
               V.MES_USD, gross, V.COST, net)
    return f, {"d707_in_sample_answer": ka, "d618_known": X.attrs["d618_known"]}


def unit_l2_k2() -> tuple[pd.DataFrame, dict[str, Any]]:
    """L2: D716's build + masks (book B); K2: D711's load_root + clock_frame at 15:30, every in-window session."""
    import vault_d716_nq_f2 as V16
    M = V16.M
    V16.E.sign_audit()
    bd = V16.build(V16.IN_END)
    ka = V16.in_sample_answers(bd)
    V16.check_known(ka)
    frames = []
    B, _ = V16.masks(bd, V16.B_START, V16.IN_END)
    Xn, Xe = bd["Xn"], bd["Xe"]
    for line, X, Fm, mask in (("L2", Xn, bd["Fn"], B),
                              ("K2_ES", Xe, bd["Fe"], bd["Fe"]["window"] & (Xe.index.to_numpy(str) >= K2_ES_LO)),
                              ("K2_NQ", Xn, bd["Fn"], bd["Fn"]["window"] & (Xn.index.to_numpy(str) >= K2_NQ_LO))):
        sess = X.index.to_numpy(str)
        cost = X.attrs["cost"]
        usd = M.cost_line(X.attrs["root"])["usd_per_point"]
        g = X["gross"].to_numpy(float)[mask]
        net = (bd["net"][mask] if line == "L2" else g - cost)
        if line == "L2" and not np.array_equal(net, g - cost):
            raise D722Error("L2: D716's net is not gross - cost")
        side = X["side"].to_numpy(float)[mask]
        sign_audit_money(line, g, side, X["P_entry"].to_numpy(float)[mask], X["P_exit"].to_numpy(float)[mask], usd)
        frames.append(_frame(line, sess[mask], side, np.full(mask.sum(), 360), np.full(mask.sum(), 390),
                             X["P_entry"].to_numpy(float)[mask], usd, g, cost, net))
    first_es = str(Xe.index.to_numpy(str)[bd["Fe"]["window"]][0])
    if first_es != K2_ES_LO:
        raise D722Error(f"K2_ES: ES 15:30's first window session {first_es} is not D711 A1's common start {K2_ES_LO}")
    return pd.concat(frames, ignore_index=True), {"d716_in_sample_answers": ka, "k2_es_first_window": first_es,
                                                   "k2_nq_first_window": str(Xn.index.to_numpy(str)[bd["Fn"]["window"]][0])}


def unit_l3() -> tuple[pd.DataFrame, dict[str, Any]]:
    """L3: D699's panel + signals + states + trade_list, V1 on short-gamma sessions: core()'s lines 262-301 for V1."""
    import stage0_d699_gamma_macd_long as D699
    S = D699.S
    D, PM, pidx = D699.panel(REPO / "data")
    days = D.index.to_numpy().astype(str)
    if (days >= SEAL).any():
        raise SealError("seal: D699's panel holds a session on or after 2024-01-01")
    E = S.d685()
    mes = E.cost_spec("ES", "micro")
    cost, usd = mes["cost_rt_usd"], mes["usd_per_point"]
    short = D["G_SUM"].to_numpy(float) < 0
    PB = PM[:, np.concatenate([[0], D699.BAR_J])]
    sig = D699.signals(PB)
    if (round(sig["norm_h"], 4), round(sig["norm_r"], 4)) != (D699.NORM_H_DECLARED, D699.NORM_R_DECLARED):
        raise D722Error("L3: the MACD norms are not D699's declared ones")
    ok = sig["valid"][pidx] & np.isfinite(sig["s15"][pidx]) & np.isfinite(PM[pidx]).all(1)
    ST = D699.states(sig, +1)
    rng = np.random.default_rng(699)
    samp = np.sort(pidx[rng.choice(np.flatnonzero(ok & short), min(40, int((ok & short).sum())), replace=False)])
    D699.lag_audit(ST, PB, samp)  # D699's second implementation (a pure-Python loop from the raw prices)
    rows_s = pidx[ok & short]
    ii, ja, jb = D699.trade_list(ST["V1_HIST"], rows_s)
    if not (ja % 15 == 1).all() or not (jb > ja).all():
        raise D722Error("L3: a fill at or before its deciding close")
    pi = np.searchsorted(pidx, ii)
    gross = (PM[ii, jb] - PM[ii, ja]) * usd
    net = gross - cost
    sign_audit_money("L3", gross, np.ones(len(ii)), PM[ii, ja], PM[ii, jb], usd)
    f = _frame("L3", days[pi], np.ones(len(ii)), ja, jb, PM[ii, ja], usd, gross, cost, net)
    return f, {"sessions": int(len(days)), "short_gamma_sessions": int(short.sum()),
               "tradable_short_gamma_sessions": int((ok & short).sum()), "cost_rt_usd": cost, "usd_per_point": usd,
               "lag_audit_days": int(len(samp))}


def unit_l4() -> tuple[pd.DataFrame, dict[str, Any]]:
    """L4: D719's load("HO") + core + D711's f2_on, HO's band/T/W, size from the burn-in; root_study's trade selection
    without its rotation null."""
    import stage1_d719_commodity_settlement_f2 as D19
    M = D19.M
    r = "HO"
    L = D19.load(r)
    cl = D19.cost_lines(r)
    T, W = D19.hm(D19.W_END[r], -30), D19.W_END[r]
    X = D19.core(L["close"], L["open"], D19.BAND_OPEN[r], T, W, cl["full"]["usd_per_point"], L["exclude"])
    X.attrs.update(root=r, T=T, cost=cl["full"]["cost"])
    D19.rq_audit(L, X, T, W, list(X.index[:: max(1, len(X) // 15)]))
    F = M.f2_on(X)
    M.V.audit_tiers(X, F)
    sz = D19.size(r, X, F)
    share, cost = sz["share"], sz["cost"]
    sess = X.index.to_numpy(str)
    if (sess >= SEAL).any():
        raise SealError("seal: HO's frame holds a session on or after 2024-01-01")
    take = F["take"] & F["window"]
    gc = X["gross"].to_numpy(float) * share
    net = gc[take] - cost
    usd = cl["full"]["usd_per_point"] * share
    side = X["side"].to_numpy(float)[take]
    sign_audit_money("L4", gc[take], side, X["P_entry"].to_numpy(float)[take], X["P_exit"].to_numpy(float)[take], usd)
    ein, eout = D19.mins(T) - 570, D19.mins(W) - 570
    f = _frame("L4", sess[take], side, np.full(take.sum(), ein), np.full(take.sum(), eout),
               X["P_entry"].to_numpy(float)[take], usd, gc[take], cost, net)
    wd = sess[F["window"]]
    return f, {"size": sz, "T": T, "W": W, "window": [str(wd[0]), str(wd[-1])], "candidates": int(len(X)),
               "sessions_in_frame": int(len(L["close"]))}


def replay_arm(O: np.ndarray, C: np.ndarray, sig: np.ndarray, first_decide: int, M_: int, cost_ticks: float,
               tick_pts: float, last_seg: int) -> dict[str, np.ndarray]:
    """D491's simulate, line for line, with the fills recorded: the first fill's segment and price, the last exit's
    segment (-1 = forced flat at the last segment's close), and which sides were entered. Its pnl and trips are
    asserted equal to simulate's, bit for bit, by the caller."""
    n = O.shape[0]
    pos = np.zeros(n)
    entry_px = np.zeros(n)
    entry_t = np.full(n, -1, dtype=np.int64)
    pnl = np.zeros(n)
    trips = np.zeros(n)
    s_all = np.nan_to_num(sig, nan=0.0)
    first_seg = np.full(n, -1, dtype=np.int64)
    first_px = np.full(n, np.nan)
    last_exit = np.full(n, -2, dtype=np.int64)
    longs = np.zeros(n, bool)
    shorts = np.zeros(n, bool)
    for t in range(first_decide, last_seg):
        s = s_all[:, t]
        px = O[:, t + 1]
        live = pos != 0
        elapsed = t - entry_t
        ex = live & (elapsed >= M_) & (s * pos <= 0) & np.isfinite(px)
        pnl = np.where(ex, pnl + pos * (px - entry_px) / tick_pts - cost_ticks, pnl)
        trips = np.where(ex, trips + 1, trips)
        last_exit = np.where(ex, t + 1, last_exit)
        pos = np.where(ex, 0.0, pos)
        en = (pos == 0) & (s != 0) & np.isfinite(px)
        first_px = np.where(en & (first_seg < 0), px, first_px)
        first_seg = np.where(en & (first_seg < 0), t + 1, first_seg)
        longs |= en & (s > 0)
        shorts |= en & (s < 0)
        entry_px = np.where(en, px, entry_px)
        entry_t = np.where(en, t, entry_t)
        pos = np.where(en, s, pos)
    cpx = C[:, last_seg]
    still = (pos != 0) & np.isfinite(cpx)
    pnl = np.where(still, pnl + pos * (cpx - entry_px) / tick_pts - cost_ticks, pnl)
    trips = np.where(still, trips + 1, trips)
    last_exit = np.where(still, -1, last_exit)
    return {"pnl": pnl, "trips": trips, "first_seg": first_seg, "first_px": first_px, "last_exit": last_exit,
            "longs": longs, "shorts": shorts}


def unit_k1() -> tuple[pd.DataFrame, dict[str, Any]]:
    """K1: D508's load_arm, with the hourly fixture filtered to sessions before 2024-01-01 BEFORE D504's build (load_arm
    builds over the whole fixture, through the vault). D504's build is causal (EMAs, a backward contract-purity run),
    so the in-window sessions are unchanged; D504's published per-year figures and D508's REPRO_NET prove it."""
    import run_d508_stretch_ranker as R
    D484, D491, D495, D504 = R.D484, R.D491, R.D495, R.D504
    meta = json.loads(D495.META.read_text(encoding="utf-8"))
    spec = json.loads(D484.SPECS.read_text(encoding="utf-8"))
    d_all = pd.read_csv(D495.FIX, encoding="utf-8")
    d_all = d_all[d_all["day"].astype(str) < SEAL].reset_index(drop=True)          # filtered before any computation
    if (d_all["day"].astype(str) >= SEAL).any():
        raise SealError("seal: an hourly row on or after 2024-01-01 reached D504's build")
    pk = D504.build(d_all, meta, spec)
    days_all = np.asarray(pk["days"]).astype(str)
    if (days_all >= SEAL).any():
        raise SealError("seal: D504's build holds a session on or after 2024-01-01")
    m = (days_all >= R.LO) & (days_all <= R.HI)
    O, C, AG = pk["O"][m], pk["C"][m], pk["AGREE"][m]
    net_tk, trips = D491.simulate(O, C, AG, pk["first"], R.M_HOLD, pk["cost"], pk["tick_pts"])
    gross_tk, trips_g = D491.simulate(O, C, AG, pk["first"], R.M_HOLD, 0.0, pk["tick_pts"])
    tick = pk["tick_usd"]
    net, gross = net_tk * tick, gross_tk * tick
    days = days_all[m]
    if len(days) != KA_K1["sessions"] or abs(float(net.sum()) - KA_K1["total_net"]) >= KA_K1["tol_usd"]:
        raise KnownAnswerError(f"K1: {len(days)} sessions, ${net.sum():,.2f} against D508's {KA_K1}")
    rp = replay_arm(O, C, AG, pk["first"], R.M_HOLD, pk["cost"], pk["tick_pts"], D491.LAST_SEG)
    rg = replay_arm(O, C, AG, pk["first"], R.M_HOLD, 0.0, pk["tick_pts"], D491.LAST_SEG)
    for a, b, nm in ((rp["pnl"], net_tk, "net pnl"), (rp["trips"], trips, "trips"), (rg["pnl"], gross_tk, "gross pnl"),
                     (rg["trips"], trips_g, "gross trips")):
        if not np.array_equal(a, b):
            raise D722Error(f"K1: the replay's {nm} differs from D491's simulate")
    traded = trips > 0
    if (net_tk[~traded] != 0).any():
        raise D722Error("K1: an untraded session carries P&L")
    hour = np.array([int(s_[1:]) for s_ in D484.SEGMENTS])
    seg_min = hour * 60 - 570                                           # the open of segment j, minutes after 09:30 ET
    close_min = (hour[D491.LAST_SEG] + 1) * 60 - 570
    if close_min != 390 or seg_min[pk["first"] + 1] != 30:
        raise D722Error(f"K1: the segment clock is not 10:00 -> 16:00 ET ({seg_min[pk['first'] + 1]}, {close_min})")
    fs, le = rp["first_seg"][traded], rp["last_exit"][traded]
    ein = seg_min[fs]
    eout = np.where(le == -1, close_min, seg_min[np.maximum(le, 0)])
    lg, sh = rp["longs"][traded], rp["shorts"][traded]
    side = np.where(lg & ~sh, 1, np.where(sh & ~lg, -1, 0))
    cost_usd = trips[traded] * pk["cost"] * tick
    point_usd = pk["point_usd"]
    # the sign audit, in money, on the arm's own machine: a held long across a rise pays, a short loses the same
    Os = np.full((2, O.shape[1]), 100.0)
    Os[:, pk["first"] + 1:] = np.linspace(100.0, 110.0, O.shape[1] - pk["first"] - 1)
    Cs = Os.copy()
    sg = np.zeros_like(Os)
    sg[0, :], sg[1, :] = 1.0, -1.0
    ps, _ = D491.simulate(Os, Cs, sg, pk["first"], R.M_HOLD, 0.0, pk["tick_pts"])
    if not (ps[0] > 0 and math.isclose(ps[1], -ps[0])):
        raise RowError("sign: the arm's long across a rise does not pay, or its short does not lose the same")
    f = _frame("K1", days[traded], side, ein, eout, rp["first_px"][traded], point_usd, gross[traded], cost_usd,
               net[traded])
    yrs = sorted({d[:4] for d in days})
    by_year_sessions = {y: int(sum(d[:4] == y for d in days)) for y in yrs}
    return f, {"sessions": int(len(days)), "traded_sessions": int(traded.sum()), "total_net": float(net.sum()),
               "by_year_sessions": by_year_sessions, "trips": int(trips.sum()),
               "cost_rt_usd": float(pk["cost"] * tick), "tick_usd": float(tick), "point_usd": float(point_usd),
               "mixed_side_sessions": int((side == 0).sum()), "hourly_rows_read_before_seal": int(len(d_all))}


UNITS: dict[str, Callable[[], tuple[pd.DataFrame, dict[str, Any]]]] = {
    "L1": unit_l1, "L2_K2": unit_l2_k2, "L3": unit_l3, "L4": unit_l4, "K1": unit_k1}


def run_unit(name: str) -> dict[str, Any]:
    t0 = time.time()
    with recording():
        f, info = UNITS[name]()
    opened = {r for r in (_repo_rel(p) for p in _OPENED) if r is not None}
    return {"name": name, "frame": f, "info": info, "opened": sorted(opened), "modules": sorted(_module_files()),
            "wall_s": round(time.time() - t0, 1)}


# ================================================================================ the known answers
def take_hash(days: np.ndarray) -> str:
    """D707's take_hash, verbatim (sha256 of the take sessions joined by newlines)."""
    return hashlib.sha256("\n".join(map(str, days)).encode("utf-8")).hexdigest()


def _book_by_year(nt: np.ndarray, dt: np.ndarray) -> dict[str, dict[str, Any]]:
    """D703's book() by_year, verbatim: {year: {n, mean net}} over a pandas groupby of the net."""
    yrs = pd.Series(nt, index=dt).groupby(lambda s: s[:4])
    return {y: {"n": int(len(v)), "net": float(v.mean())} for y, v in yrs}


def _rj(p: str) -> Any:
    return json.loads((REPO / p).read_text(encoding="utf-8"))


def _need(cond: bool, msg: str) -> None:
    if not cond:
        raise KnownAnswerError(msg)


def known_answers(df: pd.DataFrame) -> dict[str, Any]:
    """Each line's recorded known answer, recomputed from the table's rows and asserted exactly (K1: D504's per-year
    figures to 1e-6 and D508's REPRO_NET to $1, the precision they were recorded at)."""
    out: dict[str, Any] = {}
    g = {ln: df[df["line"] == ln] for ln in LINES}
    for ln in LINES:
        _need(len(g[ln]) > 0, f"{ln}: no rows")
    # L1: D707's frozen in-sample answer
    fz = _rj("data/FROZEN_vault_d707_last_hour_f2.json")["known_answer_in_sample_own_window"]
    _need(fz["trades"] == KA_L1["trades"] and fz["mean_net"] == KA_L1["mean_net"]
          and fz["take_sessions_sha256"] == KA_L1["take_sessions_sha256"], "L1: the frozen file disagrees with D722 s.1")
    x = g["L1"]
    net = x["net_usd"].to_numpy(float)
    got = {"trades": int(len(x)), "mean_net": float(net.mean()), "sum_net": float(net.sum()),
           "take_sessions_sha256": take_hash(x["session"].to_numpy(str))}
    _need(got["trades"] == KA_L1["trades"] and got["mean_net"] == KA_L1["mean_net"]
          and got["take_sessions_sha256"] == KA_L1["take_sessions_sha256"] and got["sum_net"] == fz["sum_net"],
          f"L1: {got} against D707's frozen {fz}")
    out["L1"] = {"got": got, "want": fz, "source": "data/FROZEN_vault_d707_last_hour_f2.json"}
    # L2: D716's book B
    fb = _rj("data/FROZEN_vault_d716_nq_f2.json")["known_answers"]["B"]
    _need(fb["trades"] == KA_L2["trades"] and fb["mean_net"] == KA_L2["mean_net"], "L2: the frozen file disagrees")
    net = g["L2"]["net_usd"].to_numpy(float)
    got = {"trades": int(len(net)), "mean_net": float(net.mean())}
    _need(got == KA_L2, f"L2: {got} against D716's frozen B {fb}")
    out["L2"] = {"got": got, "want": fb, "source": "data/FROZEN_vault_d716_nq_f2.json known_answers.B"}
    # L3: D699 V1's book, total and by year (sums of net)
    bk = _rj("data/d699_gamma_macd_long.json")["variants"]["V1_HIST"]["2_book"]
    _need(bk["trades"] == KA_L3["trades"] and bk["total_net"] == KA_L3["total_net"], "L3: the recorded file disagrees")
    x = g["L3"]
    net = x["net_usd"].to_numpy(float)
    yr = np.array([s[:4] for s in x["session"].to_numpy(str)])
    got = {"trades": int(len(net)), "total_net": float(net.sum()),
           "by_year": {y: {"trades": int((yr == y).sum()), "net": float(net[yr == y].sum())} for y in sorted(set(yr))}}
    _need(got["trades"] == KA_L3["trades"] and got["total_net"] == KA_L3["total_net"] and got["by_year"] == bk["by_year"],
          f"L3: {got} against D699's V1 {bk['trades']}, {bk['total_net']}, {bk['by_year']}")
    out["L3"] = {"got": got, "want": {k: bk[k] for k in ("trades", "total_net", "by_year")},
                 "source": "data/d699_gamma_macd_long.json variants.V1_HIST.2_book"}
    # L4: D719's HO
    ho = _rj("data/stage1_d719_commodity_settlement_f2.json")["roots"]["HO"]
    _need(ho["trades"] == KA_L4["trades"] and ho["mean_net"] == KA_L4["mean_net"], "L4: the recorded file disagrees")
    x = g["L4"]
    net = x["net_usd"].to_numpy(float)
    got = {"trades": int(len(net)), "mean_net": float(net.mean()),
           "by_year": _book_by_year(net, x["session"].to_numpy(str))}
    _need(got["trades"] == KA_L4["trades"] and got["mean_net"] == KA_L4["mean_net"]
          and got["by_year"] == ho["book"]["by_year"], f"L4: {got} against D719's HO {ho['trades']}, {ho['mean_net']}")
    _need(bool((x["cost_usd"] == ho["size"]["cost"]).all()) and ho["size"]["share"] == 1.0, "L4: not one full HO at $10.20")
    out["L4"] = {"got": got, "want": {"trades": ho["trades"], "mean_net": ho["mean_net"], "by_year": ho["book"]["by_year"]},
                 "source": "data/stage1_d719_commodity_settlement_f2.json roots.HO"}
    # K1: D504's published per-year arm (traded sessions and total net), and D508's REPRO_NET
    py = _rj("data/d504_arm_full_history.json")["per_year"]
    x = g["K1"]
    net = x["net_usd"].to_numpy(float)
    yr = np.array([s[:4] for s in x["session"].to_numpy(str)])
    want_y = {y: {"n_traded": py[y]["n_traded"], "total_usd": py[y]["total_usd"]} for y in sorted(py) if "2016" <= y <= "2023"}
    got_y = {y: {"n_traded": int((yr == y).sum()), "total_usd": float(net[yr == y].sum())} for y in sorted(set(yr))}
    _need(sorted(got_y) == sorted(want_y), f"K1: years {sorted(got_y)} against {sorted(want_y)}")
    dmax = max(abs(got_y[y]["total_usd"] - want_y[y]["total_usd"]) for y in want_y)
    _need(all(got_y[y]["n_traded"] == want_y[y]["n_traded"] for y in want_y) and dmax <= 1e-6,
          f"K1: per year {got_y} against D504's {want_y}")
    tot = float(net.sum())
    _need(abs(tot - KA_K1["total_net"]) < KA_K1["tol_usd"], f"K1: total ${tot:,.2f} against D508's ${KA_K1['total_net']:,.0f}")
    _need(sum(py[y]["n_sessions"] for y in want_y) == KA_K1["sessions"], "K1: D504's sessions are not D508's 1,876")
    out["K1"] = {"got": {"traded_sessions": int(len(net)), "total_net": tot, "by_year": got_y,
                         "max_abs_diff_by_year_usd": dmax},
                 "want": {"sessions_incl_untraded": KA_K1["sessions"], "total_net_pm_1": KA_K1["total_net"], "by_year": want_y},
                 "source": "data/d504_arm_full_history.json per_year (2016-2023); D508 REPRO_SESSIONS/REPRO_NET"}
    # K2: D711's book_take_everything.by_year
    d711 = _rj("data/stage1_d711_f2_mechanism.json")
    ref = {"K2_ES": d711["A1"]["clocks"]["15:30"]["book_take_everything"],
           "K2_NQ": d711["A2"]["roots"]["NQ"]["line"]["book_take_everything"]}
    _need(d711["A1"]["common_start"] == K2_ES_LO, "K2_ES: D711 A1's common start moved")
    for ln in ("K2_ES", "K2_NQ"):
        x = g[ln]
        net = x["net_usd"].to_numpy(float)
        got = {"trades": int(len(net)), "mean_net": float(net.mean()), "by_year": _book_by_year(net, x["session"].to_numpy(str))}
        _need(got["trades"] == KA_K2[ln] == ref[ln]["trades"] and got["by_year"] == ref[ln]["by_year"]
              and got["mean_net"] == ref[ln]["mean_net"], f"{ln}: {got} against D711's {ref[ln]['trades']}, {ref[ln]['by_year']}")
        out[ln] = {"got": got, "want": {k: ref[ln][k] for k in ("trades", "mean_net", "by_year")},
                   "source": "data/stage1_d711_f2_mechanism.json " + ("A1.clocks.15:30" if ln == "K2_ES" else "A2.roots.NQ.line")
                   + ".book_take_everything"}
    return out


def validate(df: pd.DataFrame) -> dict[str, Any]:
    assert_seal(df)
    check_rows(df)
    return known_answers(df)


# ================================================================================ build, cache, load
def _to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, lineterminator="\n", encoding="utf-8").encode("utf-8")


def _read_table(raw: bytes) -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(raw), compression="gzip", encoding="utf-8", float_precision="round_trip",
                     dtype={"line": str, "root": str, "session": str, **{c: np.int64 for c in INT_COLS},
                            **{c: np.float64 for c in FLOAT_COLS}})
    return df[COLS]


def build(parallel: bool = True, log: Callable[..., None] = P) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Every unit; L3 in this process (D688's panel runs its own process pool), the other four in worker processes
    while it runs (GIL-bound pandas pivots and loops: processes, not threads)."""
    t0 = time.time()
    res: dict[str, dict[str, Any]] = {}
    others = [u for u in UNITS if u != "L3"]
    if parallel:
        with ProcessPoolExecutor(max_workers=len(others)) as ex:
            futs = {u: ex.submit(run_unit, u) for u in others}
            res["L3"] = run_unit("L3")
            for u, fu in futs.items():
                res[u] = fu.result()
    else:
        for u in UNITS:
            res[u] = run_unit(u)
    for u in UNITS:
        log(f"  unit {u}: {len(res[u]['frame'])} rows in {res[u]['wall_s']} s")
    order = {"L1": 0, "L2": 1, "L3": 2, "L4": 3, "K1": 4, "K2_ES": 5, "K2_NQ": 6}
    df = pd.concat([res[u]["frame"] for u in UNITS], ignore_index=True)
    df = df.iloc[np.argsort(df["line"].map(order).to_numpy(), kind="stable")].reset_index(drop=True)
    ka = validate(df)
    info = {u: res[u]["info"] for u in UNITS}
    paths = set(EXPLICIT_INPUTS) | _module_files()
    for u in UNITS:
        paths |= set(res[u]["opened"]) | set(res[u]["modules"])
    paths = {p for p in paths if (REPO / p).is_file()}
    missing = [p for p in EXPLICIT_INPUTS if not (REPO / p).is_file()]
    if missing:
        raise D722Error(f"inputs missing: {missing}")
    wall = round(time.time() - t0, 1)
    return df, {"known_answers": ka, "unit_info": info, "key_paths": sorted(paths),
                "unit_wall_s": {u: res[u]["wall_s"] for u in UNITS}, "build_wall_s": wall, "parallel": parallel}


def write_cache(df: pd.DataFrame, bi: dict[str, Any]) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    raw = _to_csv_bytes(df)
    import gzip
    gz = gzip.compress(raw, mtime=0)
    back = _read_table(gz)
    if not back.equals(df) or not all(np.array_equal(back[c].to_numpy(), df[c].to_numpy()) for c in COLS):
        raise D722Error("the cached table does not read back bit-identically")
    CACHE.write_bytes(gz)
    meta = {"spec": SPEC, "table": CACHE.relative_to(REPO).as_posix(), "rows": int(len(df)),
            "rows_by_line": {ln: int((df["line"] == ln).sum()) for ln in LINES},
            "table_csv_sha256": hashlib.sha256(raw).hexdigest(), "table_gz_sha256": hashlib.sha256(gz).hexdigest(),
            "key": _stat_key(set(bi["key_paths"])), "build_wall_s": bi["build_wall_s"], "unit_wall_s": bi["unit_wall_s"],
            "parallel": bi["parallel"], "unit_info": bi["unit_info"], "known_answers": bi["known_answers"]}
    META.write_text(json.dumps(meta, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    return meta


def summary(df: pd.DataFrame, meta: dict[str, Any]) -> dict[str, Any]:
    """Aggregates only: no per-date rows (L3 is a per-date derivative of SqueezeMetrics GEX)."""
    unit = {"L1": "1 MES", "L2": "1 MNQ", "L3": "1 MES", "L4": "1 HO (full)", "K1": "1 MNQ (the arm's session P&L)",
            "K2_ES": "1 MES", "K2_NQ": "1 MNQ"}
    path = {"L1": "vault_d707_last_hour_f2.frame + f2; take & window, <= 2023-12-29",
            "L2": "vault_d716_nq_f2.build + masks (book B, 2018-05-14 -> 2023-12-29)",
            "L3": "stage0_d699_gamma_macd_long.panel, signals, states, trade_list: V1 on short-gamma sessions (core's rows)",
            "L4": "stage1_d719_commodity_settlement_f2.load('HO') + core + D711 f2_on; size from the burn-in (root_study's selection, no null)",
            "K1": "run_d508_stretch_ranker.load_arm's steps, the hourly fixture filtered < 2024-01-01 before D504.build; one row per traded session",
            "K2_ES": "stage1_d711_f2_mechanism.load_root('ES') + clock_frame(L, '15:30'); window & session >= 2018-05-14 (A1's common start)",
            "K2_NQ": "stage1_d711_f2_mechanism.load_root('NQ') + clock_frame(L, '15:30'); window (A2's lo 2016-01-01)"}
    lines = {}
    for ln in LINES:
        x = df[df["line"] == ln]
        s = x["session"].to_numpy(str)
        g, c, n = (x[k].to_numpy(float) for k in ("gross_usd", "cost_usd", "net_usd"))
        yr = np.array([d[:4] for d in s])
        lines[ln] = {"root": ROOT_OF[ln], "unit": unit[ln], "code_path": path[ln], "n": int(len(x)),
                     "window": ([str(min(s)), str(max(s))] if ln != "L3"   # L3's trade dates are short-gamma dates (GEX)
                                else [f"{min(s)[:4]} (year only: GEX-derived dates)", f"{max(s)[:4]}"]), "mean_gross": float(g.mean()), "mean_net": float(n.mean()),
                     "sum_net": float(n.sum()), "cost_usd": ({"min": float(c.min()), "max": float(c.max()), "mean": float(c.mean())}
                                                             if ln == "K1" else float(c[0])),
                     "usd_pp": float(x["usd_pp"].iloc[0]),
                     "side_counts": {str(k): int(v) for k, v in x["side"].value_counts().sort_index().items()},
                     "entry_exit_min": sorted({(int(a), int(b)) for a, b in zip(x["entry_min"], x["exit_min"])})[:3]
                     if ln not in ("L3", "K1") else "varies",
                     "by_year": {y: {"n": int((yr == y).sum()), "mean_gross": float(g[yr == y].mean()),
                                     "mean_net": float(n[yr == y].mean()), "sum_net": float(n[yr == y].sum())} for y in sorted(set(yr))},
                     "known_answer": meta["known_answers"][ln]}
    return {"spec": SPEC, "runner": "scripts/diag_d722_lines.py", "in_sample_end": IN_END, "seal": SEAL,
            "table": "temp/d722/lines.csv.gz (gitignored; one row per trade)", "table_csv_sha256": meta["table_csv_sha256"],
            "rows": meta["rows"],
            "conventions": {"minutes": "minutes after 09:30 ET of the price AT that minute (the close of the bar starting a minute earlier); HO too (14:00 -> 14:30 ET = 270 -> 300)",
                            "K1": "one row per traded session; side = the common side of its trips, 0 when they flipped; entry = the first fill, exit = the last exit, hold = the span; cost = trips x the round trip",
                            "net": "gross - cost"},
            "k1_sessions_incl_untraded": meta["unit_info"]["K1"]["sessions"],
            "k1_mixed_side_sessions": meta["unit_info"]["K1"]["mixed_side_sessions"],
            "l3_sessions": {k: meta["unit_info"]["L3"][k] for k in ("sessions", "short_gamma_sessions", "tradable_short_gamma_sessions")},
            "l4_size": meta["unit_info"]["L4"]["size"], "lines": lines}


def write_summary(df: pd.DataFrame, meta: dict[str, Any]) -> None:
    SUMMARY.write_text(json.dumps(summary(df, meta), indent=1, default=float) + "\n", encoding="utf-8", newline="\n")


def rebuild(parallel: bool = True, log: Callable[..., None] = P) -> tuple[pd.DataFrame, dict[str, Any]]:
    df, bi = build(parallel and _PARALLEL_OK, log)
    meta = write_cache(df, bi)
    write_summary(df, meta)
    return df, meta


def assert_fresh(meta: dict[str, Any] | None) -> None:
    why = ["no cache"] if meta is None else stale_reasons(meta)
    if why:
        raise StaleCacheError("; ".join(why[:4]) + (" ..." if len(why) > 4 else ""))


def load_lines(refresh: bool = False) -> pd.DataFrame:
    """The per-trade table. Refuses a stale cache (any keyed input or module moved, or the table's bytes) and rebuilds;
    validates the seal, the rows and every known answer on every load."""
    try:
        if refresh:
            raise StaleCacheError("refresh asked")
        assert_fresh(json.loads(META.read_text(encoding="utf-8")) if META.exists() else None)
    except StaleCacheError as e:
        P(f"[D722 lines] building: {e}")
        df, _ = rebuild()
        return df
    df = _read_table(CACHE.read_bytes())
    validate(df)
    return df


_PARALLEL_OK = __name__ in ("__main__", "__mp_main__", "diag_d722_lines")


# ================================================================================ selftest
def selftest(serial_proof: bool = False) -> int:
    t0 = time.time()
    fired: list[str] = []

    def must_raise(name: str, fn: Callable[[], Any], exc: type = D722Error) -> None:
        try:
            fn()
        except exc as e:
            fired.append(name)
            P(f"  RAISES on {name}: {type(e).__name__}: {str(e)[:110]}")
            return
        raise SystemExit(f"selftest: the {name} canary did not raise")

    df = load_lines()
    validate(df)  # the clean case
    P(f"  clean table: {len(df)} rows, every known answer exact")
    # 1. the seal
    planted = pd.concat([df, df[df["line"] == "L1"].iloc[[0]].assign(session="2024-01-02")], ignore_index=True)
    must_raise("a planted 2024-01-02 row", lambda: validate(planted), SealError)
    must_raise("a planted 2024 row inside a unit's frame",
               lambda: _frame("L1", np.array(["2023-12-29", "2024-01-02"]), np.ones(2), [360, 360], [390, 390],
                              np.ones(2), 5.0, np.zeros(2), 4.42, -4.42 * np.ones(2)), SealError)
    # 2. known answers: every line, one trade perturbed by $0.01 (gross and net together, so the row stays consistent),
    #    and one trade dropped
    for ln in LINES:
        i = int(np.flatnonzero(df["line"].to_numpy() == ln)[len(np.flatnonzero(df["line"].to_numpy() == ln)) // 2])
        bad = df.copy()
        bad.loc[i, "gross_usd"] += 0.01
        if ln == "K1":  # K1's net carries its own tick arithmetic (within TOL_ROW of gross - cost)
            bad.loc[i, "net_usd"] += 0.01
        else:
            bad.loc[i, "net_usd"] = bad.loc[i, "gross_usd"] - bad.loc[i, "cost_usd"]
        check_rows(bad)  # the row stays consistent: only the known answer can catch it
        must_raise(f"{ln}: one trade's gross +$0.01", lambda b=bad: known_answers(b), KnownAnswerError)
        must_raise(f"{ln}: one trade dropped", lambda i_=i: known_answers(df.drop(index=i_)), KnownAnswerError)
    # 3. rows
    b = df.copy()
    b.loc[5, "net_usd"] += 0.01
    must_raise("net != gross - cost", lambda: check_rows(b), RowError)
    b = df.copy()
    b.loc[5, "exit_min"] += 1
    must_raise("hold != exit - entry", lambda: check_rows(b), RowError)
    b = df.copy()
    b.loc[5, "side"] = 2
    must_raise("a side of +2", lambda: check_rows(b), RowError)
    b = df.copy()
    b.loc[int(np.flatnonzero(df["line"].to_numpy() == "L2")[0]), "side"] = 0
    must_raise("a zero side on L2", lambda: check_rows(b), RowError)
    # the sign audit in money
    must_raise("a gross with the side flipped", lambda: sign_audit_money("X", np.array([5.0]), np.array([-1.0]),
                                                                         np.array([100.0]), np.array([101.0]), 5.0), RowError)
    sign_audit_money("X", np.array([5.0]), np.array([1.0]), np.array([100.0]), np.array([101.0]), 5.0)
    # 4. the cache refuses staleness: a moved input, a missing input, and altered table bytes
    meta = json.loads(META.read_text(encoding="utf-8"))
    if stale_reasons(meta):
        raise SystemExit(f"selftest: the fresh cache reads stale: {stale_reasons(meta)}")
    k0 = sorted(meta["key"])
    for nm, mut in (("an input's mtime moved", lambda m: m["key"].__setitem__(k0[0], [m["key"][k0[0]][0], m["key"][k0[0]][1] + 1])),
                    ("an input's size moved", lambda m: m["key"].__setitem__(k0[-1], [m["key"][k0[-1]][0] + 1, m["key"][k0[-1]][1]])),
                    ("a keyed file missing", lambda m: m["key"].__setitem__("data/no_such_input.csv", [1, 1])),
                    ("the table's bytes differ", lambda m: m.__setitem__("table_gz_sha256", "0" * 64))):
        mm = json.loads(json.dumps(meta))
        mut(mm)
        must_raise(f"a stale cache ({nm})", lambda m_=mm: assert_fresh(m_), StaleCacheError)
    for need in ("scripts/diag_d722_lines.py", "scripts/vault_d707_last_hour_f2.py", "scripts/vault_d716_nq_f2.py",
                 "scripts/stage1_d711_f2_mechanism.py", "scripts/stage0_d699_gamma_macd_long.py",
                 "scripts/stage0_d688_gamma_close.py", "scripts/stage1_d719_commodity_settlement_f2.py",
                 "scripts/run_d508_stretch_ranker.py", "scripts/d491_conditional_hold.py", "scripts/d504_arm_full_history.py",
                 "data/fixtures/fut_ES_rth_1m.csv.gz", "data/fixtures/fut_es_options_eod.csv.gz", "temp/d719_bars/HO.csv.gz"):
        if need not in meta["key"]:
            raise SystemExit(f"selftest: the cache key omits {need}")
    # 5. the arm's replay equals D491's simulate on a synthetic book with flips, and a broken replay would be caught
    import run_d508_stretch_ranker as R
    rng = np.random.default_rng(722)
    O = 100 + np.cumsum(rng.normal(0, 0.5, (60, 23)), axis=1)
    C = O + rng.normal(0, 0.2, (60, 23))
    sg = np.sign(rng.normal(0, 1, (60, 23)))
    ref, trips = R.D491.simulate(O, C, sg, 15, R.M_HOLD, 1.5, 0.25)
    rp = replay_arm(O, C, sg, 15, R.M_HOLD, 1.5, 0.25, R.D491.LAST_SEG)
    if not (np.array_equal(rp["pnl"], ref) and np.array_equal(rp["trips"], trips)):
        raise SystemExit("selftest: the arm's replay differs from D491's simulate")
    rb = replay_arm(O, C, sg, 15, R.M_HOLD + 1, 1.5, 0.25, R.D491.LAST_SEG)
    if np.array_equal(rb["pnl"], ref):
        raise SystemExit("selftest: a replay with the wrong hold equals simulate (the equality check could not fire)")
    P(f"  the arm's replay == D491's simulate on 60 synthetic sessions ({int((rp['longs'] & rp['shorts']).sum())} with flips)")
    # 6. chunk == whole: a serial build must equal the parallel cache, byte for byte
    if serial_proof:
        d2, _ = build(parallel=False)
        if hashlib.sha256(_to_csv_bytes(d2)).hexdigest() != meta["table_csv_sha256"]:
            raise SystemExit("selftest: the serial build differs from the cached parallel build")
        P("  serial build == cached parallel build (table sha256 equal)")
    P(f"selftest OK: {len(fired)} canaries fired; {round(time.time() - t0, 1)} s")
    return 0


# ================================================================================ CLI
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--serial-proof", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--serial", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest(a.serial_proof)
    if not a.build:
        ap.print_help()
        return 1
    t0 = time.time()
    df, meta = rebuild(parallel=not a.serial)
    P(f"built {meta['rows']} rows in {meta['build_wall_s']} s ({'parallel' if meta['parallel'] else 'serial'}); "
      f"table sha256 {meta['table_csv_sha256'][:16]}")
    for ln in LINES:
        k = meta["known_answers"][ln]
        P(f"  {ln}: known answer EXACT: {json.dumps({kk: vv for kk, vv in k['got'].items() if kk != 'by_year'}, default=float)}")
        x = df[df["line"] == ln]
        yr = x["session"].str[:4]
        P("      by year n / mean net: " + "  ".join(f"{y}: {int((yr == y).sum())} / {x['net_usd'][yr == y].mean():+.2f}"
                                                   for y in sorted(yr.unique())))
    P(f"wrote {CACHE.relative_to(REPO)}, {META.relative_to(REPO)}, {SUMMARY.relative_to(REPO)}; total {round(time.time() - t0, 1)} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
