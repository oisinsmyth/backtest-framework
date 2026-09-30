"""D722 Part A: is each line's 2022 bigger dollars, more trades, or better direction? Spec: s.2 of
docs/decisions/D722-DIAG-PRE-REG-why-2022-scale-regime-or-one-bet.md (f25e4726), with Amendment D722-A1 (7880c5a0).

    uv run python scripts/diag_d722_part_a.py --selftest   # clean case on synthetics and the real inputs; every gate RAISES
    uv run python scripts/diag_d722_part_a.py --run        # run-once: refuses if data/diag_d722_part_a.json exists

INPUTS (Phase 0, imported, never edited): diag_d722_lines.load_lines() (one row per trade, every known answer re-validated
on load) and diag_d722_conditioners.load_conditioners() (the (root, session) panel; `sig20` is a lagged daily log-return
sd). The by-year-only lines of the share table are read from their committed JSONs, every year > 2023 dropped on read.

WHAT IS COMPUTED, per per-trade line (L1, L2, L3, L4, K1, K2_ES, K2_NQ), for T = 2022 and, identically, T = 2018:
  1  THE EXACT DECOMPOSITION (s.2). g = gross_usd. Per year y: n_y, m_y = mean|g|, e_y = sum g / sum|g|,
     G_y = n_y m_y e_y (= sum g). R = the line's other in-sample years, m_R and e_R pooled over their trades. THE COUNT
     TERM (the orchestrator's A-ruling 1, replacing s.2's "mean count per other year" so a short year cannot bias it) is
     a per-session rate on the line's calendar (its root's panel sessions from its first trade through 2023-12-29):
     n ratio = (n_T / s_T) / (N_R / s_R), n_R = N_R s_T / s_R, G_R = sum g_R x s_T / s_R. The literal s.2 ratio is
     reported beside it as ratio_n_literal_not_read. Reported: the ratios, s_T, s_R, and each log term's share of
     ln(G_T/G_R). The identity
     G_T/G_R = product of the ratios is asserted to 1e-9 relative, with G_T and G_R computed directly from sums. Where
     e_T <= 0 or e_R <= 0 the logs are undefined: the ratios are reported and the shares are null.
  2  THE EFFICIENCY TEST. de = e_T - e_R. Its SE is a block bootstrap over ISO weeks, 10,000 draws, seed 722: the T side's
     trades are grouped into their ISO weeks (key = ISO year x 100 + ISO week of the session) and W_T weeks are drawn with
     replacement from them; independently, the R side's trades are grouped into THEIR ISO weeks and W_R weeks drawn; e is
     recomputed on each side from the drawn weeks' sums (sum g and sum |g| per week), de* = e_T* - e_R*. SE = sd(de*,
     ddof 1); p50 and p95 of de* (np.percentile, linear). A week that straddles the T/R boundary is split by side (each side
     resamples its own trades' weeks, as s.2 says). Streams: numpy SeedSequence(722, spawn_key=(line index, T, side)), so
     every (line, T, side) unit has its own stream and the result does not depend on the order or grouping of units. e_y
     for every year and the rank of e_T among the line's years (1 = highest) are reported.
  3  SCALE IN VOL UNITS. u_i = g_i / (usd_pp * entry_price * sig20 * sqrt(hold_min / 390)), sig20 at (root, session) from
     the panel (K1's root is NQ). Mean u and sum u / sum |u| by year; T's share of sum u against its share of sum g (on the
     same trades). Trades without a finite sig20 are counted per line and excluded from u only.
  4  PERFORMANCE BY YEAR (and all years, and ex-2022): n, net and gross total and mean, median net, hit rate (net > 0),
     net t, net AND gross Sharpe AND Sortino (R17). Per-trade ratios annualised by sqrt(ppy), ppy = the line's trades /
     (its calendar sessions / 252) (A-ruling 2; a filtered book is annualised by its own trade count). Sharpe = mean / sd(ddof 1) * sqrt(ppy); Sortino =
     analytics.metrics.sortino(x, rf 0, ppy) (mean over sqrt(mean(min(x, 0)^2)), all observations).
  5  THE READINGS of s.2, exactly: REGIME if de/SE >= 2; SCALE if the m term's share >= 1/2 AND de/SE < 2; COUNT if the n
     term's share >= 1/2; REGIME and COUNT co-occur and both are named; MIXED if none fires; where the logs are undefined
     the reading follows the efficiency test alone: REGIME if de/SE >= 2, else UNRESOLVED. Flags (not readings): the log
     excess is <= 0 (T below R), and SCALE with COUNT together (s.2 does not address that pair; both are named).
  6  THE BY-YEAR-ONLY SHARE TABLE: D630, D649, D648, D672 C1 (NQ), D689 (ES full), D708, D717 (ES), D721's F2 on YM and
     RTY, each from its committed JSON, years <= 2023, with the JSON's unit and only what the JSON supports.

ASSERTIONS (s.7), each shown to RAISE in --selftest: the seal (a planted 2024 trade, panel row, share-table year, and an
output date); the known answers (Phase 0's gate re-run on a perturbed trade); right-quantity (the decomposition reads gross,
not net); the decomposition identity (a broken m); the bootstrap (chunk == whole bit-identically on the draw axis, and the
per-line fan-out == the serial pass bit-identically; a planted de is detected at >= 90 %; a null with week-clustered
trades crosses |z| >= 2 at <= 10 %; a trade-level bootstrap of the same null crosses it far more often and the gate
raises; a single-week side gives SE 0 and raises); the readings (synthetic trade sets built for each reading, and broken
reading rules that must fail the suite).

SEALS: no value dated 2024-01-01 or later enters anything; the vault is never read; the output holds aggregates only
(L3 is a per-date derivative of SqueezeMetrics GEX): no session date is written, and a guard refuses any date in it.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from backtest_framework.analytics.metrics import sortino as _metrics_sortino  # noqa: E402
from fast_null import parallel_map  # noqa: E402

DATA = REPO / "data"
OUT = DATA / "diag_d722_part_a.json"
SPEC = ("docs/decisions/D722-DIAG-PRE-REG-why-2022-scale-regime-or-one-bet.md (f25e4726), s.2 and s.7; "
        "Amendment D722-A1 (7880c5a0)")
SEAL = "2024-01-01"
IN_END = "2023-12-29"
LINES = ("L1", "L2", "L3", "L4", "K1", "K2_ES", "K2_NQ")
ROOT_OF = {"L1": "ES", "L2": "NQ", "L3": "ES", "L4": "HO", "K1": "NQ", "K2_ES": "ES", "K2_NQ": "NQ"}   # A-ruling 1
TESTED = ("2022", "2018")
SEED = 722
B = 10_000
CHUNK = 2_000                 # bootstrap rows gathered per block (memory bound only; chunk == whole is asserted)
ID_REL = 1e-9                 # the decomposition identity, relative (s.7.3)
Z_BAR = 2.0                   # REGIME: de / SE >= 2
HALF = 0.5                    # SCALE / COUNT: a log term's share >= 1/2
ALLOWED_DATES = {"2024-01-01", "2025-03-01", "2026-09-18", "2023-12-29"}   # the seal, the vault, the in-sample end
DATE_RE = re.compile(r"(?<!\d)\d{4}-\d{2}-\d{2}(?!\d)")


class PartAError(AssertionError):
    """A Part A gate refused. Raising, never a warning."""


class SealError(PartAError):
    pass


class IdentityError(PartAError):
    pass


class BootError(PartAError):
    pass


class ReadingError(PartAError):
    pass


class QuantityError(PartAError):
    pass


class ShareTableError(PartAError):
    pass


def P(*a: Any) -> None:
    print(*a, flush=True)


# ================================================================================ the seal
def seal_sessions(sessions: Any, what: str) -> None:
    s = pd.Series(np.asarray(sessions, dtype=object)).astype(str)
    if len(s) and (s >= SEAL).any():
        raise SealError(f"[SEAL] {what}: a row dated on or after {SEAL} survived")


def guard_output(obj: Any) -> None:
    """The output carries no session date (L3's dates are GEX-derived) and nothing dated >= the seal."""
    text = json.dumps(obj, default=str)
    bad = sorted(set(DATE_RE.findall(text)) - ALLOWED_DATES)
    if bad:
        raise SealError(f"[OUTPUT] the output carries date(s) {bad[:5]}: aggregates only")
    for k in re.findall(r'"(20\d\d)(?:-\d\d)?"\s*:', text):
        if k >= SEAL[:4]:
            raise SealError(f"[OUTPUT] the output carries a year key {k} on or after the seal")


# ================================================================================ statistics
def _f(x: Any) -> Any:
    """JSON-safe: numpy scalars to Python, non-finite to None."""
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        x = float(x)
        return x if math.isfinite(x) else None
    return x


def clean(o: Any) -> Any:
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, np.ndarray):
        return [clean(v) for v in o.tolist()]
    return _f(o)


def eff(g: np.ndarray) -> float:
    a = float(np.abs(g).sum())
    if a == 0.0:
        raise PartAError("efficiency: sum |g| is zero")
    return float(g.sum()) / a


def assert_gross(g: np.ndarray, df: pd.DataFrame) -> None:
    """Right-quantity: the decomposition's g is the gross column, and differs from the net it must not be."""
    if not np.array_equal(g, df["gross_usd"].to_numpy(float)):
        raise QuantityError("right-quantity: g is not the gross_usd column")
    if np.allclose(g, df["net_usd"].to_numpy(float)):
        raise QuantityError("right-quantity: g equals the net column (s.2 decomposes the gross)")


# -------------------------------------------------------------------------------- 1. the decomposition
def decompose(g: np.ndarray, years: np.ndarray, T: str, cal_years: np.ndarray) -> dict[str, Any]:
    """D722 A-ruling 1 (the orchestrator, after review): the count term is a per-SESSION rate on the line's own calendar
    (its root's panel sessions from its first trade through 2023-12-29), so a short year cannot bias it:
    n ratio = (n_T / s_T) / (N_R / s_R), and G_R = sum g_R x s_T / s_R (R rescaled to T's length). On the R side
    n_R = N_R x s_T / s_R, so n_R m_R e_R = G_R holds as n_T m_T e_T = G_T does. The literal s.2 ratio (n_T over the mean
    count per other year) is reported beside it, labelled literal, and not read."""
    t = years == T
    others = sorted(set(years[~t].tolist()))
    K = len(others)
    sT, sR = int((cal_years == T).sum()), int((cal_years != T).sum())
    if t.sum() < 2 or K < 1 or sT < 1 or sR < 1:
        raise PartAError(f"decomposition: {int(t.sum())} trades in {T}, {K} other years, sessions {sT} / {sR}")
    gT, gR = g[t], g[~t]
    NR = float((~t).sum())
    nT, mT, eT = float(t.sum()), float(np.abs(gT).mean()), eff(gT)
    nR, mR, eR = NR * sT / sR, float(np.abs(gR).mean()), eff(gR)
    d = {"T": T, "other_years": others, "s_T": sT, "s_R": sR, "N_R": NR, "rate_T": nT / sT, "rate_R": NR / sR,
         "n_T": nT, "m_T": mT, "e_T": eT, "n_R": nR, "m_R": mR, "e_R": eR,
         "G_T_direct": float(gT.sum()), "G_R_direct": float(gR.sum()) * sT / sR,
         "ratio_n_literal_not_read": nT / (NR / K)}
    return finish_decomposition(d)


def finish_decomposition(d: dict[str, Any]) -> dict[str, Any]:
    """Ratios, logs and shares from the components, and the identity against the directly summed G's."""
    rn, rm, re_ = d["rate_T"] / d["rate_R"], d["m_T"] / d["m_R"], d["e_T"] / d["e_R"]
    GT, GR = d["n_T"] * d["m_T"] * d["e_T"], d["n_R"] * d["m_R"] * d["e_R"]
    d.update({"ratio_n": rn, "ratio_m": rm, "ratio_e": re_, "G_T": GT, "G_R": GR,
              "ratio_G_direct": d["G_T_direct"] / d["G_R_direct"] if d["G_R_direct"] != 0 else math.nan})
    check_identity(d)
    defined = d["e_T"] > 0 and d["e_R"] > 0
    lnG = math.log(d["G_T_direct"] / d["G_R_direct"]) if defined else math.nan
    if defined and abs(lnG) < 1e-12:
        defined = False                           # no excess to share out: shares undefined
    d["logs_defined"] = bool(defined)
    if defined:
        ln = {"n": math.log(rn), "m": math.log(rm), "e": math.log(re_)}
        if abs(sum(ln.values()) - lnG) > 1e-12 + ID_REL * abs(lnG):
            raise IdentityError(f"identity: the log terms sum to {sum(ln.values())!r}, ln(G_T/G_R) = {lnG!r}")
        d.update({"ln_G_ratio": lnG, "ln_terms": ln, "share": {k: v / lnG for k, v in ln.items()},
                  "log_excess_positive": bool(lnG > 0)})
    else:
        d.update({"ln_G_ratio": None, "ln_terms": None, "share": None,
                  "log_excess_positive": bool(d["G_T_direct"] > d["G_R_direct"]),
                  "why_undefined": ("e_T <= 0" if d["e_T"] <= 0 else "") + (" e_R <= 0" if d["e_R"] <= 0 else "")
                  or "ln(G_T/G_R) = 0"})
    return d


def check_identity(d: dict[str, Any]) -> None:
    """s.7.3: G_T/G_R = (n ratio)(m_T/m_R)(e_T/e_R) to 1e-9 relative, the G's summed directly from the trades, the n
    ratio the per-session rate ratio (A-ruling 1); and n m e = G on each side."""
    prod = (d["rate_T"] / d["rate_R"]) * (d["m_T"] / d["m_R"]) * (d["e_T"] / d["e_R"])
    want = d["G_T_direct"] / d["G_R_direct"]
    if not (math.isfinite(prod) and math.isfinite(want)) or abs(prod - want) > ID_REL * abs(want):
        raise IdentityError(f"identity: product of ratios {prod!r} against G_T/G_R {want!r}")
    for side in ("T", "R"):
        nme = d[f"n_{side}"] * d[f"m_{side}"] * d[f"e_{side}"]
        if abs(nme - d[f"G_{side}_direct"]) > ID_REL * max(abs(d[f"G_{side}_direct"]), 1e-300):
            raise IdentityError(f"identity: n m e on {side} = {nme!r} against the summed {d[f'G_{side}_direct']!r}")


# -------------------------------------------------------------------------------- 2. the efficiency test
def iso_week_keys(sessions: np.ndarray) -> np.ndarray:
    ic = pd.to_datetime(pd.Series(sessions)).dt.isocalendar()
    return (ic["year"].to_numpy(np.int64) * 100 + ic["week"].to_numpy(np.int64))


def block_sums(g: np.ndarray, keys: np.ndarray, block: str = "week") -> tuple[np.ndarray, np.ndarray]:
    """Per-block sum g and sum |g| (blocks = ISO weeks; `block="trade"` exists only for the self-test's broken case)."""
    if block == "trade":
        return g.astype(float).copy(), np.abs(g).astype(float)
    if block != "week":
        raise PartAError(f"unknown block {block}")
    _, inv = np.unique(keys, return_inverse=True)
    S = np.bincount(inv, weights=g)
    A = np.bincount(inv, weights=np.abs(g))
    return S, A


def boot_e(S: np.ndarray, A: np.ndarray, spawn_key: tuple[int, ...], nb: int = B, chunk: int | None = CHUNK) -> np.ndarray:
    """nb bootstrap draws of e = sum S / sum A over len(S) blocks drawn with replacement. The index matrix is drawn in ONE
    call on the unit's own stream; the gather-and-sum runs in row blocks of `chunk` (None = whole), which cannot change a
    row's sum (asserted bit-identical in the self-test)."""
    W = len(S)
    rng = np.random.default_rng(np.random.SeedSequence(SEED, spawn_key=spawn_key))
    idx = rng.integers(0, W, size=(nb, W))
    out = np.empty(nb)
    step = nb if chunk is None else chunk
    for a in range(0, nb, step):
        blk = idx[a:a + step]
        num = S[blk].sum(axis=1)
        den = A[blk].sum(axis=1)
        if (den == 0).any():
            raise BootError("bootstrap: a draw with sum |g| = 0")
        out[a:a + step] = num / den
    return out


def assert_identical(a: np.ndarray, b: np.ndarray, what: str) -> None:
    """Bit-identity, not tolerance (CLAUDE.md): chunked draws must equal the whole."""
    if a.shape != b.shape or not np.array_equal(a.view(np.int64), b.view(np.int64)):
        raise BootError(f"bootstrap: {what} is not bit-identical to the whole")


def efficiency_test(g: np.ndarray, years: np.ndarray, weeks: np.ndarray, T: str, line_idx: int, nb: int = B,
                    chunk: int | None = CHUNK, block: str = "week") -> dict[str, Any]:
    t = years == T
    ST, AT = block_sums(g[t], weeks[t], block)
    SR, AR = block_sums(g[~t], weeks[~t], block)
    eT, eR = eff(g[t]), eff(g[~t])
    # the observed e's recomputed from the blocks: the same statistic the draws resample (float order differs only)
    for e, S, A in ((eT, ST, AT), (eR, SR, AR)):
        if abs(S.sum() / A.sum() - e) > 1e-12 * max(1.0, abs(e)):
            raise BootError("bootstrap: the block sums do not reproduce the observed e")
    dT = boot_e(ST, AT, (line_idx, int(T), 0), nb, chunk)
    dR = boot_e(SR, AR, (line_idx, int(T), 1), nb, chunk)
    de_star = dT - dR
    se = float(de_star.std(ddof=1))
    if not (math.isfinite(se) and se > 0):
        raise BootError(f"bootstrap: degenerate SE {se!r} (weeks T {len(ST)}, R {len(SR)})")
    de = eT - eR
    p05, p50, p95 = (float(v) for v in np.percentile(de_star, [5, 50, 95]))
    return {"T": T, "e_T": eT, "e_R": eR, "delta_e": de, "se": se, "z": de / se, "boot_p05": p05, "boot_p50": p50,
            "boot_p95": p95, "boot_mean": float(de_star.mean()), "weeks_T": int(len(ST)), "weeks_R": int(len(SR)),
            "draws": int(nb), "_draws": de_star}


# -------------------------------------------------------------------------------- 5. the readings
def reading(dec: dict[str, Any], z: float, broken: str | None = None) -> dict[str, Any]:
    """s.2's declared readings. `broken` exists only so the self-test can prove the reading suite fails a wrong rule."""
    regime = z >= Z_BAR
    if broken == "regime_at_1":
        regime = z >= 1.0
    if not dec["logs_defined"]:
        names = ["REGIME"] if regime else ["UNRESOLVED"]
        if broken == "undefined_is_mixed" and not regime:
            names = ["MIXED"]
        return {"reading": names, "basis": "efficiency test alone (logs undefined)", "flags": []}
    sh = dec["share"]
    count = sh["n"] >= HALF
    scale = sh["m"] >= HALF and z < Z_BAR
    if broken == "scale_ignores_z":
        scale = sh["m"] >= HALF
    if broken == "count_at_third":
        count = sh["n"] >= 1 / 3
    names = [nm for nm, on in (("REGIME", regime), ("SCALE", scale), ("COUNT", count)) if on]
    flags = []
    if scale and count:
        flags.append("SCALE and COUNT both fire: s.2 does not address the pair; both named")
    if not dec["log_excess_positive"]:
        flags.append("log excess <= 0: T is below R; the shares apportion a deficit")
    return {"reading": names or ["MIXED"], "basis": "decomposition and efficiency test", "flags": flags}


# -------------------------------------------------------------------------------- 3. vol units
def vol_units(df: pd.DataFrame, sig20: np.ndarray) -> dict[str, Any]:
    g = df["gross_usd"].to_numpy(float)
    ok = np.isfinite(sig20)
    if (sig20[ok] <= 0).any():
        raise PartAError("vol units: a non-positive sig20")
    den = df["usd_pp"].to_numpy(float) * df["entry_price"].to_numpy(float) * sig20 * np.sqrt(df["hold_min"].to_numpy(float) / 390.0)
    u = np.where(ok, g / np.where(ok, den, 1.0), np.nan)
    if np.allclose(u[ok], g[ok]):
        raise QuantityError("right-quantity: u equals g")
    yrs = df["session"].str[:4].to_numpy()
    by = {}
    for y in sorted(set(yrs.tolist())):
        k = ok & (yrs == y)
        uy, gy = u[k], g[k]
        by[y] = {"n_u": int(k.sum()), "mean_u": float(uy.mean()) if k.any() else None,
                 "eff_u": (float(uy.sum() / np.abs(uy).sum()) if k.any() and np.abs(uy).sum() > 0 else None),
                 "sum_u": float(uy.sum()), "sum_g": float(gy.sum())}
    su, sg = float(u[ok].sum()), float(g[ok].sum())
    shares = {T: {"share_of_sum_u": by[T]["sum_u"] / su if T in by and su != 0 else None,
                  "share_of_sum_g": by[T]["sum_g"] / sg if T in by and sg != 0 else None} for T in TESTED}
    return {"missing_sig20": int((~ok).sum()), "by_year": by, "sum_u_all": su, "sum_g_all": sg, "shares": shares}


# -------------------------------------------------------------------------------- 4. performance
def sharpe(x: np.ndarray, ppy: float) -> float:
    if x.size < 2:
        return math.nan
    s = float(x.std(ddof=1))
    return float(x.mean()) / s * math.sqrt(ppy) if s > 0 else math.nan


def sortino(x: np.ndarray, ppy: float) -> float:
    if x.size < 2:
        return math.nan
    return float(_metrics_sortino(x, 0.0, ppy))


def perf_block(net: np.ndarray, gross: np.ndarray, ppy: float) -> dict[str, Any]:
    n = int(net.size)
    if n == 0:
        return {"n": 0}
    sd = float(net.std(ddof=1)) if n > 1 else math.nan
    return {"n": n, "net_total": float(net.sum()), "net_mean": float(net.mean()), "net_median": float(np.median(net)),
            "gross_total": float(gross.sum()), "gross_mean": float(gross.mean()), "hit_rate_net": float((net > 0).mean()),
            "net_t": float(net.mean()) / (sd / math.sqrt(n)) if n > 1 and sd > 0 else math.nan,
            "net_sharpe": sharpe(net, ppy), "net_sortino": sortino(net, ppy),
            "gross_sharpe": sharpe(gross, ppy), "gross_sortino": sortino(gross, ppy)}


def performance(df: pd.DataFrame, n_cal: int) -> dict[str, Any]:
    yrs = df["session"].str[:4].to_numpy()
    net, gross = df["net_usd"].to_numpy(float), df["gross_usd"].to_numpy(float)
    years = sorted(set(yrs.tolist()))
    ppy = len(df) / (n_cal / 252.0)
    out = {"annualisation": {"ppy": ppy, "rule": "per-trade ratio x sqrt(ppy); ppy = the line's trades / (its calendar "
                                                 "sessions / 252), the calendar = the root's panel sessions from the "
                                                 "line's first trade through 2023-12-29 (A-ruling 2); the same ppy in "
                                                 "every row",
                             "calendar_sessions": int(n_cal), "trades": int(len(df))},
           "by_year": {y: perf_block(net[yrs == y], gross[yrs == y], ppy) for y in years},
           "all": perf_block(net, gross, ppy),
           "ex_2022": perf_block(net[yrs != "2022"], gross[yrs != "2022"], ppy)}
    return out


# -------------------------------------------------------------------------------- one line
def assert_calendar(sessions: np.ndarray, cal: np.ndarray, what: str) -> None:
    """Every trade session lies on the line's calendar (and the calendar starts at the first trade, ends <= IN_END)."""
    missing = np.setdiff1d(np.asarray(sessions, str), np.asarray(cal, str))
    if missing.size:
        raise PartAError(f"calendar: {what}: {missing.size} trade session(s) are not on the line's calendar")
    if len(cal) and (str(cal[0]) != min(np.asarray(sessions, str).tolist()) or str(cal[-1]) > IN_END):
        raise PartAError(f"calendar: {what}: the calendar does not run from the first trade to <= {IN_END}")


def analyse_line(line: str, df: pd.DataFrame, sig20: np.ndarray, cal: np.ndarray, nb: int = B,
                 chunk: int | None = CHUNK) -> dict[str, Any]:
    seal_sessions(df["session"], f"line {line}")
    seal_sessions(cal, f"calendar {line}")
    if set(df["line"]) != {line}:
        raise PartAError(f"{line}: rows of another line")
    assert_calendar(df["session"].to_numpy(str), cal, line)
    cal_years = np.array([str(s)[:4] for s in cal])
    g = df["gross_usd"].to_numpy(float)
    assert_gross(g, df)
    years = df["session"].str[:4].to_numpy()
    weeks = iso_week_keys(df["session"].to_numpy())
    yl = sorted(set(years.tolist()))
    e_by = {y: eff(g[years == y]) for y in yl}
    order = sorted(yl, key=lambda y: -e_by[y])
    li = LINES.index(line)
    res: dict[str, Any] = {
        "root": str(df["root"].iloc[0]),
        "coverage": {"years": yl, "n_by_year": {y: int((years == y).sum()) for y in yl},
                     "calendar_sessions_by_year": {y: int((cal_years == y).sum()) for y in yl},
                     "first_session_month": str(df["session"].min())[:7], "last_session_month": str(df["session"].max())[:7]},
        "e_by_year": e_by, "decomposition": {}, "efficiency_test": {}, "readings": {}}
    for T in TESTED:
        dec = decompose(g, years, T, cal_years)
        et = efficiency_test(g, years, weeks, T, li, nb, chunk)
        et.pop("_draws")
        et["rank_of_e_T"] = order.index(T) + 1
        et["years_ranked"] = len(yl)
        res["decomposition"][T] = dec
        res["efficiency_test"][T] = et
        res["readings"][T] = reading(dec, et["z"])
    res["vol_units"] = vol_units(df, sig20)
    res["performance"] = performance(df, len(cal))
    return res


def sig20_for(df: pd.DataFrame, panel: pd.DataFrame) -> np.ndarray:
    key = pd.MultiIndex.from_arrays([df["root"].to_numpy(str), df["session"].to_numpy(str)])
    return panel["sig20"].reindex(key).to_numpy(float)


def line_calendar(panel: pd.DataFrame, root: str, first: str) -> np.ndarray:
    """A-ruling 1: the root's panel sessions from the line's first trade session through 2023-12-29."""
    s = np.sort(panel.loc[root].index.to_numpy(str))
    return s[(s >= first) & (s <= IN_END)]


def analyse_all(lines: pd.DataFrame, panel: pd.DataFrame, fan_out: bool = True, nb: int = B,
                chunk: int | None = CHUNK) -> dict[str, Any]:
    items = []
    for ln in LINES:
        d = lines[lines["line"] == ln].reset_index(drop=True)
        roots = set(d["root"])
        if roots != {ROOT_OF[ln]}:
            raise PartAError(f"{ln}: root {roots} is not {ROOT_OF[ln]}")
        items.append((ln, (d, sig20_for(d, panel), line_calendar(panel, ROOT_OF[ln], str(d["session"].min())))))
    fn = lambda k, v: analyse_line(k, v[0], v[1], v[2], nb, chunk)  # noqa: E731
    if fan_out:
        got = parallel_map(fn, items, workers=len(items))
    else:
        got = {k: fn(k, v) for k, v in items}
    return {k: got[k] for k in LINES}


# ================================================================================ 6. the by-year-only share table
def _rj(rel: str) -> Any:
    return json.loads((DATA / rel).read_text(encoding="utf-8"))


def keep_years(d: dict[str, Any]) -> dict[str, Any]:
    """Years <= 2023 only; applied to every by-year dict read, before anything is computed."""
    return {str(k): v for k, v in d.items() if re.fullmatch(r"20\d\d", str(k)) and str(k) < SEAL[:4]}


def _share(net_by: dict[str, float]) -> dict[str, Any]:
    tot = float(sum(net_by.values()))
    v22 = net_by.get("2022")
    return {"total_through_2023": tot, "net_2022": v22,
            "share_2022": (v22 / tot) if v22 is not None and tot != 0 else None,
            "total_positive": bool(tot > 0)}


def _close(a: float, b: float, tol: float, what: str) -> None:
    if not abs(a - b) <= tol * max(1.0, abs(b)):
        raise ShareTableError(f"share table: {what}: {a!r} against {b!r}")


def share_table(filt: Callable[[dict[str, Any]], dict[str, Any]] = keep_years,
                reader: Callable[[str], Any] = _rj) -> dict[str, Any]:
    out: dict[str, Any] = {}
    # D630 (NG): the by-year rows and D630's Stage A must agree
    rows = filt({r["year"]: r for r in reader("ledger_d630_by_year.json")["by_year"]})
    sa = filt(reader("ledger_h2_ng_stage_a.json")["NG"]["depends"]["by_year"])
    if set(rows) != set(sa):
        raise ShareTableError("D630: the two JSONs' years differ")
    costs = set()
    for y in rows:
        if rows[y]["trades"] != sa[y]["n"]:
            raise ShareTableError(f"D630 {y}: trades differ between the two JSONs")
        _close(rows[y]["mean_gross"], sa[y]["mean"], 1e-9, f"D630 {y} mean gross")
        _close(rows[y]["total_net_full"], rows[y]["mean_net_full"] * rows[y]["trades"], 1e-9, f"D630 {y} total net")
        costs.add(round(rows[y]["mean_gross"] - rows[y]["mean_net_full"], 6))
    if len(costs) != 1:
        raise ShareTableError(f"D630: the per-trade full cost is not one constant: {costs}")
    net_full = {y: rows[y]["total_net_full"] for y in rows}
    net_mng = {y: rows[y]["mean_net_mng"] * rows[y]["trades"] for y in rows}
    out["D630"] = {"root": "NG", "source": "data/ledger_d630_by_year.json by_year; data/ledger_h2_ng_stage_a.json "
                   "NG.depends.by_year (n and mean gross agree)",
                   "unit": f"$ per trade at 1 full NG (10,000 MMBtu), gross and net (cost ${costs.pop():g} a round trip); "
                           "net also at 1 MNG (mean_net_mng x trades)",
                   "n_by_year": {y: rows[y]["trades"] for y in rows},
                   "gross_by_year_full": {y: rows[y]["mean_gross"] * rows[y]["trades"] for y in rows},
                   "net_by_year_full": net_full, "net_by_year_mng": net_mng,
                   "share_net_full": _share(net_full), "share_net_mng": _share(net_mng)}
    # D649 (NG): the projected-profit filter, counts only
    pp = reader("ledger_d630_projected_profit.json")["lines"]["projected MNG $ >= 2.0 x $5"]
    n49 = filt(pp["trades_by_year"])
    out["D649"] = {"root": "NG", "source": "data/ledger_d630_projected_profit.json lines['projected MNG $ >= 2.0 x $5']",
                   "unit": "trade counts only", "n_by_year": n49,
                   "net_by_year": None, "share_2022_of_n": (n49.get("2022", 0) / sum(n49.values())) if sum(n49.values()) else None,
                   "not_supported": "the JSON has no per-year net; its share_2022 and net_per_trade span the whole "
                                    "in-sample through 2025-02 and cannot be cut at 2023, so they are not used"}
    # D648 (CL): the gate's gross by year; net at the runner's full-size cost
    cl = filt(reader("ledger_theory_cl.json")["depends"]["by_year"])
    src = (REPO / "scripts" / "run_theory_cl.py").read_text(encoding="utf-8")
    if "COST = 21.46 + 10.0" not in src:
        raise ShareTableError("D648: run_theory_cl.py's COST constant is not the one cited")
    cost_cl = 21.46 + 10.0
    g48 = {y: cl[y]["mean"] * cl[y]["n"] for y in cl}
    n48 = {y: cl[y]["n"] for y in cl}
    net48 = {y: g48[y] - n48[y] * cost_cl for y in cl}
    out["D648"] = {"root": "CL", "source": "data/ledger_theory_cl.json depends.by_year (mean = the gate's gross per trade)",
                   "unit": "$ at 1 full CL; gross from the JSON; net = gross - n x $31.46 (run_theory_cl.py COST = 21.46 + 10.0)",
                   "n_by_year": n48, "gross_by_year": g48, "net_by_year": net48,
                   "share_gross": _share(g48), "share_net": _share(net48)}
    # D672 C1 (NQ)
    by72 = filt(reader("stage0_d672_compression_break.json")["roots"]["NQ"]["by_year"])
    c1 = {y: by72[y]["C1"] for y in by72 if by72[y].get("C1", {}).get("trades", 0) > 0}
    net72 = {y: c1[y]["usd_per_year"] for y in c1}
    out["D672_C1"] = {"root": "NQ", "source": "data/stage0_d672_compression_break.json roots.NQ.by_year.<yr>.C1",
                      "unit": "gross and net as the mean bp per trade; net $ per year = usd_per_year (book with years = 1) "
                              "at 1 MNQ ($2/pt, D671's micro costs)",
                      "n_by_year": {y: c1[y]["trades"] for y in c1},
                      "gross_bp_mean_by_year": {y: c1[y]["gross"] for y in c1},
                      "net_bp_mean_by_year": {y: c1[y]["net"] for y in c1}, "net_usd_by_year": net72,
                      "share_net_usd": _share(net72)}
    # D689 (ES full), cell h60_k0.0
    j89 = reader("d689_short_gamma_continuation.json")
    c89 = j89["cells"]["h60_k0.0"]
    cy = filt(c89["C_concentration"]["by_year"])
    nf = filt(c89["books"]["unfiltered_es_full"]["by_year_net_usd"])
    cost_full = float(j89["costs"]["es_full"]["cost_rt_usd"])
    if float(c89["books"]["unfiltered_es_full"]["cost_rt_usd"]) != cost_full:
        raise ShareTableError("D689: the book's cost is not the costs block's")
    for y in nf:
        _close(nf[y], cy[y]["n"] * (10.0 * cy[y]["mean_gross_mes_usd"] - cost_full), 1e-6,
               f"D689 {y} net full = n x (10 x MES gross - cost)")
    out["D689"] = {"root": "ES", "source": "data/d689_short_gamma_continuation.json cells.h60_k0.0 "
                   "(books.unfiltered_es_full.by_year_net_usd; C_concentration.by_year for n and the MES gross)",
                   "unit": f"net $ per year at 1 full ES (cost ${cost_full:.6f} a round trip); gross as the mean $ per "
                           "trade at 1 MES", "n_by_year": {y: cy[y]["n"] for y in cy},
                   "gross_mes_mean_by_year": {y: cy[y]["mean_gross_mes_usd"] for y in cy},
                   "net_by_year_es_full": nf, "share_net_es_full": _share(nf)}
    # D708, book E on MES
    j08 = reader("d708_short_gamma_timing.json")
    pq = filt(j08["price_question_by_year"])
    n08 = filt(j08["books_P_ES"]["E_mes"]["by_year_net_usd"])
    c08 = float(j08["books_P_ES"]["E_mes"]["cost_rt_usd"])
    for y in n08:
        _close(n08[y], pq[y]["trades"] * (pq[y]["gross_usd_mes"] - c08), 1e-6, f"D708 {y} net = n x (gross - cost)")
    out["D708"] = {"root": "ES", "source": "data/d708_short_gamma_timing.json books_P_ES.E_mes.by_year_net_usd; "
                   "price_question_by_year for n and gross",
                   "unit": f"$ at 1 MES (cost ${c08:.6f} a round trip)", "n_by_year": {y: pq[y]["trades"] for y in pq},
                   "gross_by_year": {y: pq[y]["trades"] * pq[y]["gross_usd_mes"] for y in pq}, "net_by_year": n08,
                   "share_net": _share(n08)}
    # D717 (ES), the two-sided reversed book
    j17 = reader("stage0_d717_reversed_flow.json")["roots"]["ES"]
    g4 = filt(j17["gates"]["G4_not_one_episode"]["by_year"])
    fg = filt(j17["books"]["two_sided_reversed"]["four_groups"]["by_year_net_usd"])
    for y in g4:
        _close(g4[y]["net"], g4[y]["n"] * g4[y]["mean"], 1e-9, f"D717 {y} net = n x mean")
        _close(g4[y]["net"], fg[y], 1e-9, f"D717 {y} G4 against the book's by-year")
    n17 = {y: g4[y]["net"] for y in g4}
    out["D717_ES"] = {"root": "ES", "source": "data/stage0_d717_reversed_flow.json roots.ES.gates.G4_not_one_episode.by_year "
                      "(= books.two_sided_reversed.four_groups.by_year_net_usd)",
                      "unit": f"net $ at 1 MES (cost ${float(j17['cost_rt']):.6f} a round trip)",
                      "n_by_year": {y: g4[y]["n"] for y in g4}, "net_by_year": n17, "share_net": _share(n17)}
    # D721, F2 on YM and RTY (M0's F2 book)
    j21 = reader("diag_d721_quiet_day_f2.json")["roots"]
    for r in ("YM", "RTY"):
        f2 = j21[r]["M0"]["books"]["F2"]
        ny = filt(f2["net_by_year"])
        out[f"D721_{r}"] = {"root": r, "source": f"data/diag_d721_quiet_day_f2.json roots.{r}.M0.books.F2.net_by_year",
                            "unit": f"net $ at 1 micro ({'MYM' if r == 'YM' else 'M2K'}; cost ${float(j21[r]['cost_usd']):.6f} "
                                    "a round trip)",
                            "n_total": int(f2["trades"]), "n_by_year": None, "net_by_year": ny, "share_net": _share(ny),
                            "not_supported": "per-year trade counts are not in the JSON"}
    assert_share_table_sealed(out)
    return out


def assert_share_table_sealed(tab: dict[str, Any]) -> None:
    def walk(o: Any, path: str) -> None:
        if isinstance(o, dict):
            for k, v in o.items():
                if re.fullmatch(r"20\d\d", str(k)) and str(k) >= SEAL[:4]:
                    raise SealError(f"[SEAL] share table {path}: year {k} survived")
                walk(v, f"{path}.{k}")
    walk(tab, "")


# ================================================================================ gates on the real inputs
def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    import diag_d722_conditioners as Cn
    import diag_d722_lines as L
    lines = L.load_lines()
    L.validate(lines)                    # Phase 0's seal, rows and known answers, re-run
    seal_sessions(lines["session"], "lines")
    panel = Cn.load_conditioners()
    seal_sessions(panel.index.get_level_values("session"), "panel")
    return lines, panel


def second_implementation(lines: pd.DataFrame, panel: pd.DataFrame, res: dict[str, Any], rel: float = 1e-12) -> int:
    """The decomposition, the calendar session counts and the week counts re-derived by pandas (a groupby, and the
    calendar read off the panel's index by a boolean query) without calling decompose / block_sums / line_calendar;
    they must agree to 1e-12 relative (the float order differs). Returns the number of quantities compared."""
    k = 0
    idx = panel.index.to_frame(index=False)
    for ln in LINES:
        d = lines[lines["line"] == ln]
        y = d["session"].str[:4]
        wk = pd.to_datetime(d["session"]).dt.isocalendar()
        wkey = wk["year"].astype(int).astype(str) + "W" + wk["week"].astype(int).astype(str)
        per = pd.DataFrame({"y": y, "g": d["gross_usd"], "a": d["gross_usd"].abs()}).groupby("y").agg(
            n=("g", "size"), S=("g", "sum"), A=("a", "sum"))
        root = {"L1": "ES", "L3": "ES", "K2_ES": "ES", "L2": "NQ", "K1": "NQ", "K2_NQ": "NQ", "L4": "HO"}[ln]
        cal = idx.query("root == @root and session >= @d.session.min() and session <= '2023-12-29'")["session"]
        cy = cal.str[:4].value_counts()
        for T in TESTED:
            o = per.index != T
            sT = int(cy.get(T, 0))
            sR = int(cy.sum()) - sT
            NR = float(per.loc[o, "n"].sum())
            want = {"s_T": sT, "s_R": sR, "n_T": float(per.loc[T, "n"]), "m_T": per.loc[T, "A"] / per.loc[T, "n"],
                    "e_T": per.loc[T, "S"] / per.loc[T, "A"], "n_R": NR * sT / sR,
                    "ratio_n": (float(per.loc[T, "n"]) / sT) / (NR / sR),
                    "m_R": per.loc[o, "A"].sum() / per.loc[o, "n"].sum(), "e_R": per.loc[o, "S"].sum() / per.loc[o, "A"].sum(),
                    "G_R_direct": float(per.loc[o, "S"].sum()) * sT / sR,
                    "ratio_n_literal_not_read": float(per.loc[T, "n"]) / float(per.loc[o, "n"].mean())}
            got = res[ln]["decomposition"][T]
            for q, v in want.items():
                if not abs(got[q] - v) <= rel * max(abs(v), 1e-300):
                    raise IdentityError(f"second implementation: {ln} {T} {q} differs, relative "
                                        f"{abs(got[q] - v) / max(abs(v), 1e-300):.2e}")
                k += 1
            et = res[ln]["efficiency_test"][T]
            if et["weeks_T"] != wkey[y == T].nunique() or et["weeks_R"] != wkey[y != T].nunique():
                raise BootError(f"second implementation: {ln} {T}: the week counts differ")
            k += 2
    return k


def gate_results(res: dict[str, Any]) -> dict[str, Any]:
    """Every gate that ran on the real result, as a table (all of them raise when they fail, before this)."""
    miss = {ln: res[ln]["vol_units"]["missing_sig20"] for ln in LINES}
    ids = {ln: {T: res[ln]["decomposition"][T]["ratio_G_direct"] for T in TESTED} for ln in LINES}
    return {"seal_lines_panel_output": "held", "known_answers_phase0": "held (diag_d722_lines.validate)",
            "right_quantity_gross": "held", "decomposition_identity_1e-9": "held on every line x {2022, 2018}",
            "bootstrap_se_finite_positive": "held on every line x {2022, 2018}",
            "fan_out_equals_serial": "asserted in --selftest", "missing_sig20_by_line": miss,
            "lines_tested": list(ids)}


def run() -> int:
    if OUT.exists():
        raise SystemExit(f"[RUN-ONCE] {OUT.relative_to(REPO)} exists: Part A has been run; refusing")
    t0 = time.time()
    lines, panel = load_inputs()
    res = analyse_all(lines, panel, fan_out=True)
    n_second = second_implementation(lines, panel, res)
    tab = share_table()
    out = {"spec": SPEC, "seal": f"no value dated {SEAL} or later; the vault is never read",
           "bootstrap": {"draws": B, "seed": SEED, "blocks": "ISO weeks (ISO year x 100 + ISO week of the session)",
                         "scheme": "each side (T; R = the line's other in-sample years) resamples its own trades' weeks "
                                   "with replacement, as many weeks as it has; e = sum g / sum |g| over the drawn weeks; "
                                   "de* = e_T* - e_R*; SE = sd(de*, ddof 1); p50/p95 by np.percentile (linear)",
                         "streams": "SeedSequence(722, spawn_key=(line index in LINES, T, side 0 = T / 1 = R))"},
           "calendar": "per line: its root's panel sessions (ES: L1, L3, K2_ES; NQ: L2, K1, K2_NQ; HO: L4) from the "
                       "line's first trade session through 2023-12-29 (A-ruling 1)",
           "count_term": "A-ruling 1: n ratio = (n_T / s_T) / (N_R / s_R) on the line's calendar; G_R = sum g_R x s_T / "
                         "s_R; n_R = N_R x s_T / s_R. ratio_n_literal_not_read = s.2's literal n_T / (mean count per "
                         "other year), reported and not read",
           "annualisation": "A-ruling 2: per line, sqrt(ppy), ppy = its trades / (its calendar sessions / 252)",
           "lines": res, "share_table": tab,
           "gates": {**gate_results(res), "second_implementation_quantities_1e-12": n_second},
           "notes": ["reading flags are reported beside the reading and do not change it",
                     "boot_p05/p50/p95 describe the sampling distribution of de (centred on de), not a null"],
           "runtime_s": round(time.time() - t0, 2)}
    out = clean(out)
    guard_output(out)
    with open(OUT, "x", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
        f.write("\n")
    P(f"[D722 A] wrote {OUT.relative_to(REPO)} in {time.time() - t0:.1f}s")
    return 0


# ================================================================================ self-test
def _synth_sessions(year: int, weeks: np.ndarray, k: np.ndarray) -> np.ndarray:
    return np.array([dt.date.fromisocalendar(year, int(w), 1 + int(i) % 5).isoformat() for w, i in zip(weeks, k)])


def _clustered(rng: np.random.Generator, n_weeks: int, per_week: int, mu: float, week_sd: float) -> tuple[np.ndarray, np.ndarray]:
    """g = c_w + eps, c_w ~ N(mu, week_sd), eps ~ N(0, 1): trades that share a week share its direction."""
    c = rng.normal(mu, week_sd, n_weeks)
    wk = np.repeat(np.arange(n_weeks), per_week)
    return c[wk] + rng.normal(0.0, 1.0, wk.size), wk


def _rate(mu_T: float, week_sd: float, block: str, reps: int, nb: int, seed: int) -> float:
    """The share of replications with |de / SE| >= 2 on synthetic T (52 weeks) vs R (260 weeks), 8 trades a week."""
    rng = np.random.default_rng(seed)
    hits = 0
    for r in range(reps):
        gT, wT = _clustered(rng, 52, 8, mu_T, week_sd)
        gR, wR = _clustered(rng, 260, 8, 0.0, week_sd)
        g = np.r_[gT, gR]
        years = np.r_[np.full(gT.size, "2022"), np.full(gR.size, "2019")]
        weeks = np.r_[wT, 10_000 + wR]
        et = efficiency_test(g, years, weeks, "2022", 1000 * seed + r, nb, None, block)
        hits += abs(et["z"]) >= Z_BAR
    return hits / reps


NULL_RATE_MAX, DETECT_MIN = 0.10, 0.90


def assert_null_rate(rate: float) -> None:
    if rate > NULL_RATE_MAX:
        raise BootError(f"bootstrap: a null crosses |z| >= 2 at {rate:.3f} > {NULL_RATE_MAX}: the SE is too small")


def assert_detects(rate: float) -> None:
    if rate < DETECT_MIN:
        raise BootError(f"bootstrap: a planted de is detected at {rate:.3f} < {DETECT_MIN}")


FLIP_N = 13


def _synth_line(kind: str, seed: int = 7) -> pd.DataFrame:
    """A synthetic line built to give one reading: 7 reference years that are copies of one pattern P (50 weeks x 5
    trades, week-clustered), and a 2022 built from P."""
    rng = np.random.default_rng(seed)
    mu = -0.3 if kind.startswith("UNRESOLVED") or kind == "REGIME_UNDEF" else 0.3
    c = rng.normal(mu, 0.3, 50)
    wk = np.repeat(np.arange(1, 51), 5)
    kk = np.tile(np.arange(5), 50)
    Pg = c[wk - 1] + rng.normal(0.0, 1.0, wk.size)
    rows_s, rows_g = [], []
    for y in (2016, 2017, 2018, 2019, 2020, 2021, 2023):
        rows_s.append(_synth_sessions(y, wk, kk))
        rows_g.append(Pg)
    if kind == "SCALE":
        gT, wT, kT = 3.0 * Pg, wk, kk                                     # m x3, n and e unchanged, de = 0
    elif kind == "COUNT":
        gT, wT, kT = np.tile(Pg, 3), np.tile(wk, 3), np.tile(kk, 3)       # n x3, m and e unchanged
    elif kind == "REGIME":
        gT, wT, kT = np.abs(Pg), wk, kk                                   # every trade right: e = 1, m and n unchanged
    elif kind == "REGIME_BIG_M":
        gT, wT, kT = 10.0 * np.abs(Pg), wk, kk                            # m carries >= 1/2 but z >= 2: not SCALE
    elif kind == "REGIME_COUNT":
        gT, wT, kT = np.tile(np.abs(Pg), 20), np.tile(wk, 20), np.tile(kk, 20)
    elif kind in ("MIXED", "MIXED_N"):
        dup = np.arange(wk.size) % (4 if kind == "MIXED" else 2) == 0     # n x1.25 (MIXED) or x1.5 (MIXED_N)
        gT = 1.1 * np.r_[Pg, Pg[dup]]
        wT, kT = np.r_[wk, wk[dup]], np.r_[kk, kk[dup]]
        flip = (gT < 0) & (np.arange(gT.size) % (7 if kind == "MIXED" else FLIP_N) == 0)   # a few losers right: e up
        gT = np.where(flip, -gT, gT)
    elif kind in ("UNRESOLVED", "REGIME_UNDEF"):
        gT, wT, kT = (Pg.copy(), wk, kk) if kind == "UNRESOLVED" else (np.abs(Pg), wk, kk)
    else:
        raise PartAError(kind)
    rows_s.append(_synth_sessions(2022, wT, kT))
    rows_g.append(gT)
    s = np.concatenate(rows_s)
    g = np.concatenate(rows_g)
    return pd.DataFrame({"line": "SYN", "root": "ES", "session": s, "side": 1, "entry_min": 360, "exit_min": 390,
                         "hold_min": 30, "entry_price": 4000.0, "usd_pp": 5.0, "gross_usd": g, "cost_usd": 4.42,
                         "net_usd": g - 4.42})


def _synth_calendar(years: tuple[int, ...] = tuple(range(2016, 2024))) -> np.ndarray:
    """The synthetic lines' calendar: ISO weeks 1..50 x Monday..Friday of each year (250 sessions a year)."""
    return np.array([dt.date.fromisocalendar(y, w, dd).isoformat() for y in years for w in range(1, 51)
                     for dd in range(1, 6)])


def _synth_cal_years() -> np.ndarray:
    return np.array([s[:4] for s in _synth_calendar()])


def _half_year_calendar() -> np.ndarray:
    """Every weekday from 2018-07-02 (a half-length first year) through 2023-12-29."""
    d = pd.bdate_range("2018-07-02", IN_END)
    return np.array([x.strftime("%Y-%m-%d") for x in d])


def _half_year_line() -> pd.DataFrame:
    """One trade on every calendar session: a constant per-session rate, a half-length 2018."""
    s = _half_year_calendar()
    g = np.random.default_rng(3).normal(0.2, 1.0, s.size)
    return pd.DataFrame({"session": s, "gross_usd": g})


def assert_count_neutral(ratio: float, what: str) -> None:
    if ratio != 1.0:
        raise IdentityError(f"count term: {what} = {ratio!r} on a constant per-session rate (must be exactly 1)")


READING_CASES = {"SCALE": ["SCALE"], "COUNT": ["COUNT"], "REGIME": ["REGIME"], "REGIME_BIG_M": ["REGIME"],
                 "REGIME_COUNT": ["REGIME", "COUNT"],
                 "MIXED": ["MIXED"], "MIXED_N": ["MIXED"], "UNRESOLVED": ["UNRESOLVED"], "REGIME_UNDEF": ["REGIME"]}


def reading_suite(broken: str | None = None, nb: int = 2_000) -> dict[str, Any]:
    out = {}
    for kind, want in READING_CASES.items():
        df = _synth_line(kind)
        g = df["gross_usd"].to_numpy(float)
        years = df["session"].str[:4].to_numpy()
        weeks = iso_week_keys(df["session"].to_numpy())
        dec = decompose(g, years, "2022", _synth_cal_years())
        et = efficiency_test(g, years, weeks, "2022", 99, nb, None)
        got = reading(dec, et["z"], broken)["reading"]
        if got != want:
            raise ReadingError(f"reading suite: {kind} read {got}, built to read {want} (z {et['z']:.2f}, shares "
                               f"{dec['share']})")
        out[kind] = {"z": et["z"], "share": dec["share"], "reading": got}
    return out


def selftest() -> int:
    t0 = time.time()
    fired: list[str] = []
    table: list[tuple[str, str]] = []

    def must_raise(name: str, fn: Callable[[], Any], exc: type = PartAError) -> None:
        try:
            fn()
        except exc as e:
            fired.append(name)
            P(f"  RAISES  {name}: {str(e)[:150]}")
            return
        raise SystemExit(f"[SELFTEST] canary DID NOT RAISE: {name}")

    def ok(name: str, fn: Callable[[], Any]) -> Any:
        v = fn()
        table.append((name, "PASS"))
        P(f"  PASS    {name}")
        return v

    P("[D722 A selftest] synthetic gates")
    # ---- the decomposition identity
    rng = np.random.default_rng(1)
    gs = rng.normal(0.4, 1.0, 600)
    ys = np.array([str(2016 + i % 8) for i in range(600)])
    d = ok("identity holds on a synthetic line", lambda: decompose(gs, ys, "2022", _synth_cal_years()))

    def broken_m() -> None:
        bad = dict(d)
        bad["m_T"] *= 1 + 1e-6
        finish_decomposition(bad)
    must_raise("identity: a broken m (x 1+1e-6)", broken_m, IdentityError)

    def broken_n() -> None:
        bad = dict(d)
        bad["n_R"] += 1.0                           # n_R off the rescaled count N_R x s_T / s_R
        finish_decomposition(bad)
    must_raise("identity: n_R not N_R x s_T / s_R", broken_n, IdentityError)

    # ---- A-ruling 1: a half-length first year at a constant per-session rate gives n ratio 1 exactly
    hc = _half_year_line()
    hy = hc["session"].str[:4].to_numpy()
    hcal = np.array([s[:4] for s in _half_year_calendar()])
    hd = {T: decompose(hc["gross_usd"].to_numpy(float), hy, T, hcal) for T in TESTED}
    ok("count term: half-length first year, constant rate -> n ratio exactly 1 (2022 and 2018)",
       lambda: [assert_count_neutral(hd[T]["ratio_n"], f"rate ratio {T}") for T in TESTED])
    for T in TESTED:
        must_raise(f"count term: the literal per-year ratio fails the same line ({T})",
                   lambda T=T: assert_count_neutral(hd[T]["ratio_n_literal_not_read"], f"literal ratio {T}"),
                   IdentityError)
    must_raise("calendar: a trade session off the line's calendar",
               lambda: assert_calendar(np.r_[_half_year_calendar()[:3], ["2020-07-04"]], _half_year_calendar(), "SYN"))

    # ---- right-quantity
    syn = _synth_line("SCALE")
    ok("right-quantity: g is gross", lambda: assert_gross(syn["gross_usd"].to_numpy(float), syn))
    must_raise("right-quantity: net passed as g", lambda: assert_gross(syn["net_usd"].to_numpy(float), syn), QuantityError)

    # ---- the seal
    planted = syn.copy()
    planted.loc[len(planted)] = planted.iloc[0]
    planted.loc[len(planted) - 1, "session"] = "2024-01-02"
    must_raise("seal: a planted 2024 trade", lambda: analyse_line("SYN", planted.assign(line="SYN"),
                                                                  np.full(len(planted), 0.01), _synth_calendar(), 200, None), SealError)
    must_raise("seal: a planted 2024 panel row",
               lambda: seal_sessions(pd.Index(["2023-12-29", "2024-01-02"]), "panel"), SealError)
    must_raise("seal: a session date in the output", lambda: guard_output({"x": {"first": "2022-03-07"}}), SealError)
    must_raise("seal: a 2024 year key in the output", lambda: guard_output({"by_year": {"2024": 1.0}}), SealError)

    def leaky_reader(rel: str) -> Any:
        j = _rj(rel)
        if rel == "stage0_d717_reversed_flow.json":
            j = json.loads(json.dumps(j))
            j["roots"]["ES"]["gates"]["G4_not_one_episode"]["by_year"]["2099"] = {"n": 1, "net": 1.0, "mean": 1.0}
            j["roots"]["ES"]["books"]["two_sided_reversed"]["four_groups"]["by_year_net_usd"]["2099"] = 1.0
        return j
    ok("seal: share table with a planted future year filtered on read", lambda: share_table(keep_years, leaky_reader))
    must_raise("seal: share table with the year filter bypassed", lambda: share_table(lambda x: dict(x), leaky_reader),
               SealError)

    # ---- the bootstrap
    S_, A_ = block_sums(gs, np.arange(600) // 5)
    w1 = boot_e(S_, A_, (5, 2022, 0), B, None)
    w2 = boot_e(S_, A_, (5, 2022, 0), B, CHUNK)
    w3 = boot_e(S_, A_, (5, 2022, 0), B, 777)
    ok("bootstrap: chunk == whole on the draw axis (2,000 and 777 rows), bit-identical",
       lambda: (assert_identical(w1, w2, "chunk 2,000"), assert_identical(w1, w3, "chunk 777")))
    w_ulp = w2.copy()
    w_ulp[4321] = np.nextafter(w_ulp[4321], np.inf)
    must_raise("bootstrap: the chunk == whole gate on a draw one ULP off", lambda: assert_identical(w1, w_ulp, "one ULP"),
               BootError)
    one = np.r_[np.full(40, "2022"), np.full(200, "2019")]
    gw = np.r_[rng.normal(0.2, 1, 40), rng.normal(0, 1, 200)]
    wk1 = np.r_[np.zeros(40, np.int64), 100 + np.arange(200) // 5]
    must_raise("bootstrap: a single-week side with a single-week reference gives SE 0",
               lambda: efficiency_test(np.r_[gw[:40], gw[:40]], np.r_[one[:40], np.full(40, "2019")],
                                       np.r_[wk1[:40], np.full(40, 7)], "2022", 0, 500, None), BootError)
    reps, nbs = 200, 400
    r_det = ok("bootstrap: a planted de (mu 1.0, week sd 1) is detected at >= 90 %",
               lambda: (lambda r: (assert_detects(r), r)[1])(_rate(1.0, 1.0, "week", reps, nbs, 11)))
    r_null = ok("bootstrap: a week-clustered null (week sd 2) crosses |z| >= 2 at <= 10 %",
                lambda: (lambda r: (assert_null_rate(r), r)[1])(_rate(0.0, 2.0, "week", reps, nbs, 12)))
    r_trade = _rate(0.0, 2.0, "trade", reps, nbs, 12)
    must_raise(f"bootstrap: the same null resampled by TRADE (rate {r_trade:.3f}) fails the null-rate gate",
               lambda: assert_null_rate(r_trade), BootError)
    P(f"          rates: planted {r_det:.3f}, null by week {r_null:.3f}, null by trade {r_trade:.3f} "
      f"({reps} replications x {nbs} draws)")

    # ---- the readings
    ok("readings: every synthetic built for a reading reads it", lambda: reading_suite())
    for br in ("scale_ignores_z", "count_at_third", "regime_at_1", "undefined_is_mixed"):
        must_raise(f"readings: the broken rule '{br}' fails the suite", lambda br=br: reading_suite(br), ReadingError)

    # ---- the real inputs: the clean case (gates only; no statistic is printed)
    P("[D722 A selftest] the real inputs (gates only; nothing below prints a statistic)")
    import diag_d722_lines as L
    lines, panel = ok("inputs load; Phase 0's seal, rows and known answers re-validated", load_inputs)
    pert = lines.copy()
    i0 = int(np.flatnonzero(pert["line"].to_numpy() == "L1")[0])
    pert.loc[i0, "net_usd"] += 0.01
    pert.loc[i0, "gross_usd"] += 0.01
    must_raise("known answers: a perturbed L1 trade (Phase 0's gate)", lambda: L.validate(pert), L.D722Error)
    t1 = time.time()
    whole = ok("the real analysis, serial (every identity, seal, right-quantity and SE gate)",
               lambda: analyse_all(lines, panel, fan_out=False))
    t_serial = time.time() - t1
    t1 = time.time()
    fan = ok("the real analysis, fanned out over the seven lines", lambda: analyse_all(lines, panel, fan_out=True))
    t_fan = time.time() - t1
    nq = ok("second implementation (pandas groupby) == the decomposition and week counts, every line x {2022, 2018}",
            lambda: second_implementation(lines, panel, whole))
    P(f"          {nq} quantities compared")
    bent = json.loads(json.dumps(clean(whole)))
    bent["L2"]["decomposition"]["2018"]["m_R"] *= 1 + 1e-9
    must_raise("second implementation: m_R one part in 1e9 off on L2 2018", lambda: second_implementation(lines, panel, bent),
               IdentityError)
    a = json.dumps(clean(whole), sort_keys=True)
    b = json.dumps(clean(fan), sort_keys=True)
    ok("fan-out == serial, bit-identical (JSON of every float by repr)",
       lambda: a == b or (_ for _ in ()).throw(BootError("fan-out != serial")))
    miss = {ln: whole[ln]["vol_units"]["missing_sig20"] for ln in LINES}
    P(f"          missing sig20 by line: {miss}")
    ok("share table builds, every internal consistency check holds, sealed", share_table)
    ok("the output guard passes the assembled (unwritten) result",
       lambda: guard_output(clean({"lines": whole, "share_table": share_table(), "gates": gate_results(whole)})))
    P(f"[D722 A selftest] PASS: {len(table)} clean checks, {len(fired)} canaries raised; serial {t_serial:.1f}s, "
      f"fan-out {t_fan:.1f}s, total {time.time() - t0:.1f}s")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.run:
        return run()
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
