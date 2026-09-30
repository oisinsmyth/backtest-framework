"""D709 STAGE 0 -- silver's leveraged-ETF (AGQ/ZSL) rebalance into the COMEX settlement.

Design (committed before this file): docs/decisions/D709-STAGE-0-DESIGN-silver-letf-settlement-flow.md.

    python scripts/stage0_d709_silver_settlement_flow.py --selftest
    python scripts/stage0_d709_silver_settlement_flow.py --power   [--data-root <main checkout>/data]
    python scripts/stage0_d709_silver_settlement_flow.py --run     [--data-root ...]   (refuses a second run)
    python scripts/stage0_d709_silver_settlement_flow.py --check   [--data-root ...]   (reproduces the --run output)

Run with the SYSTEM python (pyarrow is not in the uv environment); `src/` is put on the path here.

THE TRADE (design s.4). From 12:55 ET take s = sign(decision - prior settlement of the same contract), where the
decision price is the last close in bars 12:50..12:54; fill at the close of bar 12:55; exit at the close of bar 13:24,
the last trade in SI's 13:24:00-13:25:00 settlement window; one SIL (1,000 oz) priced off SI's bars; $8.00 a round
trip (futures_costs.json, SI micro, d556_min_size). Eras: post 2019-01-07 -> 2023-12-29 (the treatment), pre
2011-01-03 -> 2019-01-04 (the placebo), 2010-07 -> 2010-12 POWER's noise only.

THE GATES (design s.6, fixed): G1 edge (t >= 2 and above the enumerated rotation p95), G2 the 11:30 placebo, G3 the
pre-era, G4 GC (AMENDMENT A1: fires only if GC's post-era mean in its own sigma units is >= SI's), G5 the
flow-share tercile sign, N net > 0. G5b (the AUM rotation) qualifies the attribution only.
The readings of s.10 are computed by `verdict`.

SEALS. Every source is sliced at read to dates < 2024-01-01 and `guard` asserts it; nothing of CL or NG is read.
--power BLINDS the fixture: for every day on or after 2011-01-01 only the pre-decision bars (09:00-11:29) and the
decision windows keep their prices, so POWER can read the predictor side and never a window move of the study.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
import time
import warnings
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
from backtest_framework.analytics import metrics as MET  # noqa: E402
from backtest_framework.validation import filter_oracle as FO  # noqa: E402
from fast_null import parallel_map  # noqa: E402

SPEC_DOC = REPO / "docs" / "decisions" / "D709-STAGE-0-DESIGN-silver-letf-settlement-flow.md"
OUT = REPO / "data" / "d709_silver_settlement_flow.json"
POWER_OUT = REPO / "data" / "d709_power.json"

CUT = "2024-01-01"
POST = ("2019-01-07", "2023-12-29")
PRE = ("2011-01-03", "2019-01-04")
NOISE = ("2010-07-01", "2010-12-31")
PIT_SPLIT = "2015-07-01"
BLIND_FROM = "2011-01-01"
P0_POST_FROM = "2019-01-08"      # D634: the interval into 01-07 straddles the switch
NBARS = 420                        # bar 0 = 09:00 ET, start-stamped (fut_day1m.meta.json)
LETTER = "FGHJKMNQUVXZ"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
FND_BUFFER, FND_BUFFER_BESIDE = 5, 10
ROT_LO, AUM_ROT_LO = 20, 63
ER = 0.0095                        # D634 / gate 0b
SEED = 709
BETAS = (0.0, 0.155, 0.31, 0.62, 1.0)
N_POWER = 2000
PAPER_KILL = 0.25
STRESS = (13.00, 24.50)


def bar(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m) - 540


# root -> full-contract multiplier, traded (micro) multiplier, settlement close minute, BCOM row, funds (name, L)
ROOTS: dict[str, dict[str, Any]] = {
    "SI": {"mult_full": 5000.0, "mult": 1000.0, "close": "13:24", "comp": "Silver", "funds": (("AGQ", 2), ("ZSL", -2)),
           "unit": "SIL"},
    "GC": {"mult_full": 100.0, "mult": 10.0, "close": "13:29", "comp": "Gold", "funds": (("UGL", 2), ("GLL", -2)),
           "unit": "MGC"},
}
# cell clock: root, decision window (lo, hi), fill bar, exit bar
CLOCKS: dict[str, dict[str, Any]] = {
    "SI_settle": {"root": "SI", "dec": (bar("12:50"), bar("12:54")), "fill": bar("12:55"), "exit": bar("13:24")},
    "SI_mid": {"root": "SI", "dec": (bar("11:25"), bar("11:29")), "fill": bar("11:30"), "exit": bar("11:59")},
    "GC_settle": {"root": "GC", "dec": (bar("12:55"), bar("12:59")), "fill": bar("13:00"), "exit": bar("13:29")},
    "GC_mid": {"root": "GC", "dec": (bar("11:25"), bar("11:29")), "fill": bar("11:30"), "exit": bar("11:59")},
}
CELLS = {  # the seven independent cells of design s.11
    "SI_settle_post": ("SI_settle", POST), "SI_settle_pre": ("SI_settle", PRE),
    "SI_mid_post": ("SI_mid", POST), "SI_mid_pre": ("SI_mid", PRE),
    "GC_settle_post": ("GC_settle", POST), "GC_settle_pre": ("GC_settle", PRE), "GC_mid_post": ("GC_mid", POST),
}
REASONS = ("early_close", "missing_bar", "no_prior_settlement", "roll_session", "fnd", "sign_zero", "carve")
REQUIRED_OUTPUTS = ("spec", "verdict", "gates", "cells", "nulls", "groups", "stress", "component_line", "p0",
                    "waterfall", "secondary", "diagnostics", "power_reference", "audits", "reads", "deviations",
                    "timings")
POWER_REQUIRED = ("spec", "noise", "sample", "betas", "g1_rate", "full_reading_rate", "pass_rate", "n1_size_check",
                  "mde", "paper_kill", "audits", "timings")
DEVIATIONS: list[str] = []


class D709Error(RuntimeError):
    pass


def P(*a: Any) -> None:
    print(*a, flush=True)


def must(cond: bool, msg: str) -> None:
    if not cond:
        raise D709Error(msg)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open(mode="rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def _load(name: str, fn: str) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    assert s is not None and s.loader is not None
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


# ================================================================== the seal
def guard(dates: Any, name: str) -> None:
    """Every source is sliced at read; this asserts it. It RAISES on any date on or after CUT."""
    d = [str(x) for x in np.asarray(dates).ravel().tolist()]
    top = max(d) if d else ""
    if top >= CUT:
        raise D709Error(f"[SEAL] {name}: a row dated {top} (>= {CUT}) reached the study")


def check_bundle(B: dict[str, Any]) -> None:
    for R in ROOTS:
        guard(B[R]["days"], f"{R} bars")
        guard(B[R]["sdays"], f"{R} settlement days")
        guard([k[1] for k in B[R]["settle"]], f"{R} strip")
        guard(B[R]["raw_day"], f"{R} raw rows")
    for f, df in B["nav"].items():
        guard(df["date"], f"{f} NAV")
    guard([k + "-01" for k in B["rates"]], "OECD rates")
    guard([d for d, _ in B["splits"]], "splits")


# ================================================================== schedules and calendars
def facts_table() -> dict[str, dict[str, str]]:
    f = REPO / "data" / "index_reweight" / "methodology_facts.json"
    if not f.exists():
        f = Path(r"C:\Users\O\Desktop\Projects\Backtest Framework\data\index_reweight\methodology_facts.json")
    return json.loads(f.read_text(encoding="utf-8"))["designated_contract_schedule"]["table"]


def gsci_rows(data_root: Path) -> dict[str, list[str]]:
    df = pd.read_csv(data_root / "index_reweight" / "gsci_schedule.csv", encoding="utf-8")
    return {r["cme_root"]: [r[f"m{m:02d}"] for m in range(1, 13)] for _, r in df.iterrows()}


def lead_of(row: dict[str, str], y: int, m: int) -> tuple[int, int]:
    lm = MONTHS.index(row[MONTHS[m - 1]]) + 1
    return (y if lm >= m else y + 1), lm


def lead_next(row: dict[str, str], y: int, m: int) -> tuple[tuple[int, int], tuple[int, int]]:
    return lead_of(row, y, m), (lead_of(row, y + 1, 1) if m == 12 else lead_of(row, y, m + 1))


def carve_months(t9a_row: dict[str, str], gsci: list[str]) -> set[int]:
    """Months where BCOM's Table 9a or GSCI's schedule changes the root's lead contract, plus January (design s.4.3)."""
    out = {1}
    for m in range(1, 13):
        m2 = 1 if m == 12 else m + 1
        if t9a_row[MONTHS[m - 1]] != t9a_row[MONTHS[m2 - 1]] or gsci[m - 1] != gsci[m2 - 1]:
            out.add(m)
    return out


def contract_ym(code: str, day: str) -> tuple[int, int]:
    mon = LETTER.index(code[-2]) + 1
    dig = int(code[-1])
    dy, dm = int(day[:4]), int(day[5:7])
    y = dy - 1
    while not (y % 10 == dig and (y, mon) >= (dy, dm)):
        y += 1
        if y > dy + 10:
            raise D709Error(f"contract {code} on {day}: no year resolves")
    return y, mon


def code_of(root: str, ym: tuple[int, int]) -> str:
    return f"{root}{LETTER[ym[1] - 1]}{ym[0] % 10}"


def s0(k: int) -> float:
    """BCOM s.2.8 (gate 0b's S0): the weight on the Next Future on business day k."""
    return min(max((k - 5) / 5.0, 0.0), 1.0)


# ================================================================== loading
def _republications(st: pd.DataFrame) -> set[str]:
    """A holiday republication: every contract of the root equal to its previous strip day (data-available (v))."""
    out: set[str] = set()
    prev: dict[str, float] | None = None
    for ref, g in st.groupby("ref", sort=True):
        cur = dict(zip(g["contract"], g["settle"].astype(float)))
        if prev is not None:
            common = [c for c in cur if c in prev]
            if len(common) >= 3 and all(cur[c] == prev[c] for c in common):
                out.add(str(ref))
        prev = cur
    return out


def bundle_root(R: str, raw: pd.DataFrame, cal: pd.DataFrame, st: pd.DataFrame, blind: bool) -> dict[str, Any]:
    raw = raw.sort_values(["day", "bar"], kind="mergesort").reset_index(drop=True)
    days = np.array(sorted(raw["day"].unique()), dtype=object).astype(str)
    di = np.searchsorted(days, raw["day"].to_numpy(str))
    b = raw["bar"].to_numpy(int)
    must(bool(((b >= 0) & (b < NBARS)).all()), f"{R}: a bar index outside 0..419")
    C = np.full((days.size, NBARS), np.nan)
    C[di, b] = raw["close"].to_numpy(float)
    PR = np.zeros((days.size, NBARS), dtype=bool)
    PR[di, b] = True
    vol = np.bincount(di, weights=raw["volume"].to_numpy(float), minlength=days.size)
    first = raw.groupby("day", sort=True).first()
    must(bool((raw.groupby("day")["contract"].nunique() == 1).all()), f"{R}: two contracts in one session")
    contract = first["contract"].reindex(days).to_numpy(str)
    same_front = first["same_front"].reindex(days).to_numpy(bool)
    c = cal.set_index("day").reindex(days)
    close_et = c["session_close_et"].fillna("").to_numpy(str)
    trading = c["is_trading"].fillna(False).to_numpy(bool)
    rep = _republications(st)
    sdays = sorted(set(st["ref"]) - rep)
    settle = {(a, r): float(s) for a, r, s in zip(st["contract"], st["ref"], st["settle"])}
    raw_day = raw["day"].to_numpy(str)
    raw_bar = b
    raw_close = raw["close"].to_numpy(float)
    out = {"days": days, "C": C, "PR": PR, "vol": vol, "contract": contract, "same_front": same_front,
           "close_et": close_et, "trading": trading, "settle": settle, "sdays": np.array(sdays, dtype=str),
           "republications": sorted(rep), "raw_day": raw_day, "raw_bar": raw_bar, "raw_close": raw_close,
           "blinded": False}
    if blind:
        blind_root(out, R)
    return out


def blind_root(Br: dict[str, Any], R: str) -> None:
    """POWER's blind: on days >= BLIND_FROM only 09:00-11:29 and the decision windows keep a price."""
    keep = np.zeros(NBARS, dtype=bool)
    keep[: bar("11:30")] = True
    for ck in CLOCKS.values():
        if ck["root"] == R:
            keep[ck["dec"][0]: ck["dec"][1] + 1] = True
    late = Br["days"] >= BLIND_FROM
    C = Br["C"]
    C[np.ix_(late, ~keep)] = np.nan
    rl = (Br["raw_day"] >= BLIND_FROM) & ~keep[Br["raw_bar"]]
    Br["raw_close"] = np.where(rl, np.nan, Br["raw_close"])
    Br["blinded"] = True
    Br["blind_keep_bars"] = keep


def load(data_root: Path, blind: bool) -> dict[str, Any]:
    import pyarrow.dataset as ds
    t0 = time.time()
    fx = data_root / "fixtures"
    dset = ds.dataset(fx / "fut_day1m.parquet", format="parquet")
    tab = dset.to_table(columns=["root", "contract", "day", "bar", "close", "volume", "same_front"],
                        filter=(ds.field("root").isin(list(ROOTS))) & (ds.field("day") < CUT)).to_pandas()
    tab["day"] = tab["day"].astype(str)
    guard(tab["day"], "fut_day1m")
    cal = pd.read_csv(fx / "cme_session_calendar.csv.gz", usecols=["root", "day", "is_trading", "session_close_et"],
                      dtype={"root": str, "day": str, "session_close_et": str}, encoding="utf-8")
    cal = cal[cal["root"].isin(list(ROOTS)) & (cal["day"] < CUT)]
    guard(cal["day"], "calendar")
    st = pd.read_csv(fx / "fut_settle_strip.csv.gz", usecols=["root", "contract", "ref", "settle"],
                     dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8")
    st = st[st["root"].isin(list(ROOTS)) & (st["ref"] < CUT)]
    guard(st["ref"], "strip")
    B: dict[str, Any] = {}
    for R in ROOTS:
        B[R] = bundle_root(R, tab[tab["root"] == R].drop(columns="root"), cal[cal["root"] == R],
                           st[st["root"] == R], blind)
    nav_dir = data_root / "raw" / "recorder" / "proshares_nav"
    B["nav"] = {}
    B["reads"] = {"fut_day1m.parquet": str(fx / "fut_day1m.parquet"), "calendar": str(fx / "cme_session_calendar.csv.gz"),
                  "strip": str(fx / "fut_settle_strip.csv.gz")}
    for R in ROOTS:
        for f, _L in ROOTS[R]["funds"]:
            files = sorted(nav_dir.glob(f"{f}__*.csv"))
            must(len(files) == 1, f"{f}: expected one NAV file, found {len(files)}")
            df = pd.read_csv(files[0], usecols=["Date", "NAV", "Prior NAV", "Assets Under Management"],
                             encoding="utf-8-sig")
            df["date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y").dt.strftime("%Y-%m-%d")
            df = df[df["date"] < CUT].rename(columns={"NAV": "nav", "Prior NAV": "prior_nav",
                                                      "Assets Under Management": "aum"})
            guard(df["date"], f"{f} NAV")
            df = df.sort_values("date").reset_index(drop=True)[["date", "nav", "prior_nav", "aum"]]
            must(not df["date"].duplicated().any(), f"{f}: duplicate NAV dates")
            B["nav"][f] = df
            B["reads"][f] = str(files[0])
    rates = pd.read_csv(fx / "oecd_ir3tib_monthly.csv", encoding="utf-8", dtype={"period": str})
    rates = rates[(rates["currency"] == "USD") & (rates["period"] < CUT[:7])]
    B["rates"] = {p: float(r) / 100.0 for p, r in zip(rates["period"], rates["rate_pct"])}
    sp = pd.read_csv(data_root / "fund_facts" / "proshares_splits.csv", encoding="utf-8", dtype=str)
    sp["date"] = pd.to_datetime(sp["Date of Split"], format="%m/%d/%Y").dt.strftime("%Y-%m-%d")
    sp = sp[sp["date"] < CUT]
    B["splits"] = [(d, s) for d, s in zip(sp["date"], sp["Symbol"])]
    B["t9a"] = facts_table()
    B["gsci"] = gsci_rows(data_root)
    B["costs"] = costs(data_root)
    B["blind"] = blind
    B["load_s"] = time.time() - t0
    check_bundle(B)
    return B


def costs(data_root: Path) -> dict[str, float]:
    c = json.loads((data_root / "futures_costs.json").read_text(encoding="utf-8"))
    sil = c["roots"]["SI"]["micro"]
    must(sil["symbol"] == "SIL" and sil["runner_lines"]["d556_min_size"]["value"] == 8.0, "SIL d556_min_size is not $8")
    mgc = c["roots"]["GC"]["micro"]
    mgc_cost = mgc["commission_rt_usd"]["value"] + mgc["crossing_ticks_rt"]["d508_exec"]["value"] * mgc["tick_usd"]
    si_q = c["roots"]["SI"]["full"]["crossing_ticks_rt"]["d507_exec"]["value"]
    return {"SI": 8.0, "GC": float(mgc_cost), "SI_quoted_stress": 3.0 + round(si_q, 2) * sil["tick_usd"]}


# ================================================================== the construction
def asof_last(C: np.ndarray, lo: int, hi: int) -> np.ndarray:
    W = C[:, lo: hi + 1]
    f = np.isfinite(W)
    anyf = f.any(axis=1)
    last = (W.shape[1] - 1) - np.argmax(f[:, ::-1], axis=1)
    out = np.full(C.shape[0], np.nan)
    out[anyf] = W[np.nonzero(anyf)[0], last[anyf]]
    return out


def prior_sday(Br: dict[str, Any]) -> np.ndarray:
    sd = Br["sdays"]
    i = np.searchsorted(sd, Br["days"], side="left") - 1
    return np.where(i >= 0, sd[np.maximum(i, 0)], "")


def fnd_sessions(Br: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    """Sessions from d to the traded contract's first notice day (the last session of the month before the contract
    month, counted on the root's own sessions; D676 R2). Returns (sessions_to_fnd or large, contract (y, m) code)."""
    days = Br["days"]
    month = pd.Series(days).str[:7]
    last_of = pd.Series(days).groupby(month.values).max().to_dict()
    idx = {d: i for i, d in enumerate(days)}
    out = np.full(days.size, 10 ** 6, dtype=np.int64)
    ym_code = np.empty(days.size, dtype=object)
    for i, (d, c) in enumerate(zip(days, Br["contract"])):
        y, m = contract_ym(c, d)
        ym_code[i] = (y, m)
        py, pm = (y, m - 1) if m > 1 else (y - 1, 12)
        f = last_of.get(f"{py:04d}-{pm:02d}")
        if f is None:
            must(f"{py:04d}-{pm:02d}" >= CUT[:7] or f"{py:04d}-{pm:02d}" < days[0][:7],
                 f"{c} on {d}: FND month {py}-{pm:02d} is inside the data but has no session")
            continue
        out[i] = idx[f] - i
    return out, ym_code


def bd_of_month(days: np.ndarray) -> np.ndarray:
    return pd.Series(days).groupby(pd.Series(days).str[:7].values).cumcount().to_numpy() + 1


def decide(B: dict[str, Any], clock: dict[str, Any], fnd_buffer: int = FND_BUFFER) -> dict[str, Any]:
    """Per session of the root: s, the decision / fill / exit prices, the prior settlement, and the first failing
    exclusion reason (design s.4.3's order)."""
    R = clock["root"]
    Br = B[R]
    days = Br["days"]
    dec = asof_last(Br["C"], *clock["dec"])
    has_dec = np.isfinite(asof_last(np.where(Br["PR"], 0.0, np.nan), *clock["dec"]))
    fill = Br["C"][:, clock["fill"]]
    exit_ = Br["C"][:, clock["exit"]]
    has_fill, has_exit = Br["PR"][:, clock["fill"]], Br["PR"][:, clock["exit"]]
    psd = prior_sday(Br)
    prev = np.array([Br["settle"].get((c, p), np.nan) if p else np.nan for c, p in zip(Br["contract"], psd)])
    with np.errstate(invalid="ignore"):
        s = np.sign(dec - prev)
    s = np.where(np.isfinite(s), s, 0.0)
    fnd, ym = fnd_sessions(Br)
    cm = carve_months(B["t9a"][ROOTS[R]["comp"]], B["gsci"][R])
    bd = bd_of_month(days)
    mon = np.array([int(d[5:7]) for d in days])
    carve = np.isin(mon, sorted(cm)) & (bd >= 5) & (bd <= 10)
    reason = np.full(days.size, "", dtype=object)
    checks = [
        ("early_close", ~(Br["trading"] & (Br["close_et"] == ROOTS[R]["close"]))),
        ("missing_bar", ~(has_fill & has_exit & has_dec)),
        ("no_prior_settlement", ~np.isfinite(prev)),
        ("roll_session", ~Br["same_front"]),
        ("fnd", fnd <= fnd_buffer),
        ("sign_zero", s == 0),
        ("carve", carve),
    ]
    for name, bad in checks:
        reason = np.where((reason == "") & bad, name, reason)
    elig_x = (reason == "")                       # eligible, ex-carve (the primary's set)
    elig_c = elig_x | (reason == "carve")         # eligible but for the carve
    return {"clock": clock, "root": R, "days": days, "s": s, "dec": dec, "fill": fill, "exit": exit_, "prev": prev,
            "prev_sday": psd, "reason": reason, "elig": elig_x, "elig_or_carve": elig_c, "carve": carve,
            "fnd": fnd, "ym": ym, "bd": bd, "carve_months": sorted(cm)}


def predictors(B: dict[str, Any], D: dict[str, Any]) -> dict[str, np.ndarray]:
    """Point-in-time predictors (design s.5): A_t-1, V_d, sigma_d, Q-hat, share, x_SR, |r|/sigma."""
    R = D["root"]
    Br = B[R]
    days = Br["days"]
    n = days.size
    A = np.zeros(n)
    a_date = np.empty(n, dtype=object)
    for f, L in ROOTS[R]["funds"]:
        nv = B["nav"][f]
        nd = nv["date"].to_numpy(str)
        i = np.searchsorted(nd, days, side="left") - 1
        ok = i >= 0
        aum = np.where(ok, nv["aum"].to_numpy(float)[np.maximum(i, 0)], np.nan)
        A = A + (L * L - L) * aum
        a_date = np.where(ok, nd[np.maximum(i, 0)], None)
    # V_d: mean day-session volume of the 20 prior sessions (>= 15 finite, > 0)
    vol = Br["vol"]
    V = np.full(n, np.nan)
    cs = np.concatenate([[0.0], np.cumsum(vol)])
    for i in range(20, n):
        V[i] = (cs[i] - cs[i - 20]) / 20.0
    V = np.where(V > 0, V, np.nan)
    # sigma_d: SD of 20 prior settle-to-settle log returns of the traded contract (>= 15 finite)
    sd_list = list(Br["sdays"])
    sd_pos = {d: k for k, d in enumerate(sd_list)}
    sig = np.full(n, np.nan)
    for i in range(n):
        p = D["prev_sday"][i]
        if not p:
            continue
        k = sd_pos[p]
        if k < 20:
            continue
        c = Br["contract"][i]
        px = np.array([Br["settle"].get((c, sd_list[j]), np.nan) for j in range(k - 20, k + 1)])
        with np.errstate(invalid="ignore", divide="ignore"):
            r = np.diff(np.log(px))
        r = r[np.isfinite(r)]
        if r.size >= 15:
            sig[i] = float(r.std(ddof=1))
    prev = D["prev"]
    with np.errstate(invalid="ignore", divide="ignore"):
        r_tau = D["dec"] / prev - 1.0
        Q = A * np.abs(r_tau) / (prev * ROOTS[R]["mult_full"])
        share = Q / V
        xsr = 0.7 * sig * np.sqrt(share) * prev * ROOTS[R]["mult"]
        absr_sig = np.abs(np.log(D["dec"] / prev)) / sig
    return {"A": A, "A_date": a_date, "V": V, "sigma": sig, "r_tau": r_tau, "Q": Q, "share": share, "xsr": xsr,
            "absr_sig": absr_sig, "P": prev}


def money(s: np.ndarray, fill: np.ndarray, exit_: np.ndarray, mult: float, cost: float) -> tuple[np.ndarray, np.ndarray]:
    """gross = s x (exit - fill) x mult; net = gross - cost (design s.4.5)."""
    g = s * (exit_ - fill) * mult
    return g, g - cost


# ================================================================== statistics
def t_ord(x: np.ndarray) -> float:
    x = np.asarray(x, float)
    if x.size < 3:
        return float("nan")
    sd = x.std(ddof=1)
    return float(x.mean() / (sd / math.sqrt(x.size))) if sd > 0 else float("nan")


def nw_t(x: np.ndarray, L: int) -> float:
    x = np.asarray(x, float)
    n = x.size
    if n < L + 3:
        return float("nan")
    e = x - x.mean()
    v = float(e @ e) / n
    for lag in range(1, L + 1):
        v += 2 * (1 - lag / (L + 1)) * float(e[lag:] @ e[:-lag]) / n
    return float(x.mean() / math.sqrt(v / n)) if v > 0 else float("nan")


def block_se(x: np.ndarray, days: np.ndarray, B: int = 2000, seed: int = SEED) -> float:
    x = np.asarray(x, float)
    if x.size < 3:
        return float("nan")
    months = pd.Series(np.asarray(days).astype(str)).str[:7].to_numpy()
    u, inv = np.unique(months, return_inverse=True)
    sums = np.bincount(inv, weights=x, minlength=u.size)
    cnt = np.bincount(inv, minlength=u.size).astype(float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, u.size, size=(B, u.size))
    return float((sums[idx].sum(axis=1) / cnt[idx].sum(axis=1)).std(ddof=1))


def ladder(x: np.ndarray, days: np.ndarray) -> dict[str, Any]:
    x = np.asarray(x, float)
    n = x.size
    if n < 12:
        return {"n": int(n)}
    e = x - x.mean()
    if float(e @ e) == 0.0:
        return {"n": int(n), "degenerate": "constant series"}
    hc0 = math.sqrt(float(e @ e)) / n
    hc3 = math.sqrt(float(((e / (1 - 1 / n)) ** 2).sum())) / n
    bse = block_se(x, days)
    ts = {"ordinary": t_ord(x), "HC0": x.mean() / hc0, "HC3": x.mean() / hc3, "NW5": nw_t(x, 5), "NW10": nw_t(x, 10),
          "monthly_block": x.mean() / bse if bse > 0 else float("nan")}
    above = [k for k, v in ts.items() if v >= 2]
    return {"n": int(n), "t": {k: float(v) for k, v in ts.items()}, "block_se": bse,
            "agree": len(above) in (0, len(ts)), "on_the_bar": 0 < len(above) < len(ts)}


def basic(x: np.ndarray) -> dict[str, Any]:
    x = np.asarray(x, float)
    if x.size < 3:
        return {"n": int(x.size), "mean": float(x.mean()) if x.size else float("nan")}
    return {"n": int(x.size), "mean": float(x.mean()), "sd": float(x.std(ddof=1)), "t": t_ord(x),
            "se": float(x.std(ddof=1) / math.sqrt(x.size))}


# ================================================================== the enumerated rotation null
def scorer(s: np.ndarray, m: np.ndarray) -> float:
    """The study's own statistic: the mean of s x move."""
    return float(np.mean(s * m))


def rotation_offsets(n: int, lo: int) -> np.ndarray:
    must(n > 2 * lo + 1, f"rotation: n {n} too small for offsets {lo}..{n - lo}")
    return np.arange(lo, n - lo + 1)


def rotate_enumerated(s: np.ndarray, m: np.ndarray, ks: np.ndarray) -> np.ndarray:
    """ONE axis-wise call: row k is mean(roll(s, k) * m). Asserted bit-equal to `scorer` (selftest and every run)."""
    n = s.size
    idx = (np.arange(n)[None, :] - ks[:, None]) % n
    return (s[idx] * m[None, :]).mean(axis=1)


def null_summary(obs: float, null: np.ndarray) -> dict[str, Any]:
    return {"observed": float(obs), "n_offsets": int(null.size), "p05": float(np.percentile(null, 5)),
            "p50": float(np.percentile(null, 50)), "p95": float(np.percentile(null, 95)), "p95_se": 0.0,
            "rank": float((null < obs).mean()), "mid_rank_pct": float(MET.mid_rank_percentile(null.tolist(), obs))}


def rotation_cell(s: np.ndarray, m: np.ndarray, lo: int = ROT_LO, check: int = 20) -> dict[str, Any]:
    ks = rotation_offsets(s.size, lo)
    null = rotate_enumerated(s, m, ks)
    obs = scorer(s, m)
    must(rotate_enumerated(s, m, np.array([0]))[0] == obs, "[RQ] rotation offset 0 does not reproduce the observed "
                                                           "statistic bit for bit")
    for k in np.linspace(0, ks.size - 1, min(check, ks.size)).astype(int):
        must(null[k] == scorer(np.roll(s, int(ks[k])), m), f"[EXACT] rotation row {ks[k]} differs from the scorer")
    return null_summary(obs, null)


# ================================================================== cells
def cell(B: dict[str, Any], Dc: dict[str, dict[str, Any]], Pc: dict[str, dict[str, np.ndarray]], name: str,
         cost: float | None = None, with_null: bool = True) -> dict[str, Any]:
    ck, era = CELLS[name]
    D, Pr = Dc[ck], Pc[ck]
    R = D["root"]
    days = D["days"]
    inera = (days >= era[0]) & (days <= era[1])
    sel = D["elig"] & inera
    c = B["costs"][R] if cost is None else cost
    g_all, n_all = money(D["s"], D["fill"], D["exit"], ROOTS[R]["mult"], c)
    g, n = g_all[sel], n_all[sel]
    m = (D["exit"] - D["fill"])[sel] * ROOTS[R]["mult"]
    must(bool(np.isfinite(g).all()), f"{name}: a non-finite move on an eligible day")
    out = {"cell": name, "clock": ck, "era": list(era), "n": int(sel.sum()), "gross": basic(g), "net": basic(n),
           "ladder": ladder(g, days[sel]), "cost": c, "_sel": sel, "_g": g, "_n": n, "_m": m, "_s": D["s"][sel],
           "_days": days[sel]}
    if with_null:
        out["null"] = rotation_cell(D["s"][sel], m)
    return out


def public(c: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in c.items() if not k.startswith("_")}


# ================================================================== audits
def audit_lag(B: dict[str, Any], clock: dict[str, Any], D: dict[str, Any], Pr: dict[str, np.ndarray] | None,
              n_sample: int = 60) -> dict[str, Any]:
    """A SECOND IMPLEMENTATION: from the raw rows with a plain loop, never calling `decide`/`predictors`."""
    R = clock["root"]
    Br = B[R]
    days = Br["days"]
    pool = np.nonzero(D["elig_or_carve"])[0]
    must(pool.size > 0, "lag audit: no eligible day")
    pick = pool[np.linspace(0, pool.size - 1, min(n_sample, pool.size)).astype(int)]
    rd, rb, rc = Br["raw_day"], Br["raw_bar"], Br["raw_close"]
    lo_i = np.searchsorted(rd, days[pick], side="left")
    hi_i = np.searchsorted(rd, days[pick], side="right")
    sdl = list(Br["sdays"])
    lo, hi = clock["dec"]
    must(clock["fill"] > hi and clock["exit"] > clock["fill"], "[LAG] the fill bar does not start after the decision")
    for j, i in enumerate(pick):
        d = days[i]
        dec = fill = ex = None
        best = -1
        for r in range(lo_i[j], hi_i[j]):
            b_ = int(rb[r])
            if lo <= b_ <= hi and b_ > best:
                best, dec = b_, rc[r]
            if b_ == clock["fill"]:
                fill = rc[r]
            if b_ == clock["exit"]:
                ex = rc[r]
        p = ""
        for x in sdl:
            if x < d:
                p = x
            else:
                break
        prev = Br["settle"].get((Br["contract"][i], p), float("nan"))
        s = 0.0 if dec is None or not math.isfinite(prev) or dec == prev else (1.0 if dec > prev else -1.0)
        for name, ref, got in (("decision", dec, D["dec"][i]), ("fill", fill, D["fill"][i]), ("exit", ex, D["exit"][i]),
                               ("prior settlement", prev, D["prev"][i]), ("s", s, D["s"][i])):
            ref = float("nan") if ref is None else float(ref)
            if not ((math.isnan(ref) and math.isnan(got)) or ref == got):
                raise D709Error(f"[LAG] {R} {d}: {name} {got!r} from the construction, {ref!r} from the raw rows")
        if Pr is not None:
            a_ref = 0.0
            for f, L in ROOTS[R]["funds"]:
                nv = B["nav"][f]
                ad, av = None, float("nan")
                for x, a in zip(nv["date"], nv["aum"]):
                    if x < d:
                        ad, av = x, float(a)
                must(ad is None or ad < d, f"[LAG] {f} AUM for {d} not dated before it")
                a_ref += (L * L - L) * av
            got = Pr["A"][i]
            must((math.isnan(a_ref) and math.isnan(got)) or a_ref == got,
                 f"[LAG] A on {d}: {got} from predictors, {a_ref} from the NAV rows dated before it")
            if i >= 20:
                v = sum(float(Br["vol"][k]) for k in range(i - 20, i)) / 20.0
                must(abs(v - Pr["V"][i]) <= 1e-9 * max(1.0, v), f"[LAG] V_d on {d}: {Pr['V'][i]} vs {v}")
    return {"days_checked": int(pick.size), "clock": {k: (list(v) if isinstance(v, tuple) else v)
                                                      for k, v in clock.items()}}


def audit_sign(money_fn: Callable[..., tuple[np.ndarray, np.ndarray]]) -> dict[str, Any]:
    g, n = money_fn(np.array([1.0]), np.array([20.000]), np.array([20.010]), 1000.0, 8.0)
    must(abs(g[0] - 10.0) < 1e-9 and abs(n[0] - 2.0) < 1e-9, f"[SIGN] up move after s=+1 booked {g[0]}/{n[0]}")
    g, n = money_fn(np.array([-1.0]), np.array([20.000]), np.array([20.010]), 1000.0, 8.0)
    must(abs(g[0] + 10.0) < 1e-9 and abs(n[0] + 18.0) < 1e-9, f"[SIGN] up move after s=-1 booked {g[0]}/{n[0]}")
    g, _ = money_fn(np.array([1.0]), np.array([1800.0]), np.array([1800.1]), 10.0, 5.93)
    must(abs(g[0] - 1.0) < 1e-9, f"[SIGN] MGC +0.10 booked {g[0]}")
    must(float(np.sign(20.02 - 20.00)) == 1.0, "[SIGN] a decision above the prior settlement is not s=+1")
    return {"up_long_gross": 10.0, "up_long_net": 2.0, "up_short_gross": -10.0, "up_short_net": -18.0, "mgc": 1.0}


def audit_rq(prim: dict[str, Any], mid: dict[str, Any], gc: dict[str, Any], settle_exit_g: np.ndarray,
             D: dict[str, Any], cost: float) -> dict[str, Any]:
    g, n = prim["_g"], prim["_n"]
    must(D["clock"]["exit"] > D["clock"]["fill"], "[RQ] the exit bar is not after the fill bar")
    must(bool(np.any(g != 0)), "[RQ] the primary's moves are identically zero (a zero-length hold)")
    must(bool(np.all(n == g - cost)), "[RQ] net differs from gross by something other than the cost")
    for nm, other in (("the midday placebo", mid["_g"]), ("GC", gc["_g"]), ("the settlement-exit variant", settle_exit_g)):
        must(not (other.size == g.size and np.array_equal(other, g)), f"[RQ] the primary equals {nm}")
    must(bool((D["elig_or_carve"] & ~D["elig"]).any()), "[RQ] the carved set equals the full set")
    must(PRE[1] < POST[0], "[RQ] the eras overlap")
    return {"moves_nonzero": True, "net_is_gross_minus_cost": True, "differs_from": ["midday", "GC", "settlement exit"],
            "carve_nonempty": True, "eras_disjoint": True}


def known_answers(B: dict[str, Any], D: dict[str, Any]) -> dict[str, Any]:
    R = D["root"]
    got = carve_months(B["t9a"][ROOTS[R]["comp"]], B["gsci"][R])
    want = {"SI": {1, 2, 4, 6, 8, 11}, "GC": {1, 3, 5, 7, 11}}[R]
    must(got == want, f"[KNOWN] {R} carve months {sorted(got)} != {sorted(want)}")
    el = D["elig_or_carve"]
    must(bool((B[R]["close_et"][el] == ROOTS[R]["close"]).all()), f"[KNOWN] an eligible {R} day is not a "
                                                                      f"{ROOTS[R]['close']} session")
    days = B[R]["days"]
    for i in np.nonzero(el)[0][:: max(1, int(el.sum()) // 25)]:
        y, m = D["ym"][i]
        py, pm = (y, m - 1) if m > 1 else (y - 1, 12)
        ms = [x for x in days if x[:7] == f"{py:04d}-{pm:02d}"]
        if ms:
            fnd = max(ms)
            must(D["fnd"][i] == int(np.searchsorted(days, fnd)) - i, f"[KNOWN] FND count on {days[i]}")
    return {"carve_months": sorted(got), "close_minute": ROOTS[R]["close"], "fnd_rule": "last session of the prior month"}


# ================================================================== groups (design s.8)
def trims(x: np.ndarray) -> dict[str, float]:
    x = np.sort(np.asarray(x, float))
    k = int(math.floor(0.01 * x.size))
    if k == 0:
        return {"k": 0, "ex_top": float(x.mean()), "ex_bottom": float(x.mean()), "trimmed": float(x.mean())}
    return {"k": k, "ex_top": float(x[:-k].mean()), "ex_bottom": float(x[k:].mean()), "trimmed": float(x[k:-k].mean())}


def distribution(g: np.ndarray, net: np.ndarray) -> dict[str, Any]:
    out = {}
    for lab, x in (("gross", g), ("net", net)):
        x = np.asarray(x, float)
        w, lo = x[x > 0], x[x < 0]
        out[lab] = {"count": int(x.size), "mean": float(x.mean()), "median": float(np.median(x)),
                    "win_rate": float((x > 0).mean()),
                    "payoff": float(w.mean() / -lo.mean()) if w.size and lo.size else float("nan"),
                    "skew": float(pd.Series(x).skew()), "excess_kurtosis": float(pd.Series(x).kurt()),
                    "trims_1pct": trims(x), "mean_below_median": bool(x.mean() < np.median(x))}
    return out


def tercile_means(v: np.ndarray, g: np.ndarray) -> dict[str, Any]:
    ok = np.isfinite(v)
    v, g = v[ok], g[ok]
    n = v.size
    if n < 9:
        return {"n": int(n)}
    o = np.argsort(v, kind="mergesort")
    k = n // 3
    parts = [o[:k], o[k: n - k], o[n - k:]]
    return {"n": int(n), "means": [float(g[p].mean()) for p in parts], "t": [t_ord(g[p]) for p in parts],
            "edges": [float(v[o[k - 1]]), float(v[o[n - k]])], "top_minus_bottom": float(g[parts[2]].mean() - g[parts[0]].mean())}


def quintiles(v: np.ndarray, g: np.ndarray) -> dict[str, Any]:
    ok = np.isfinite(v)
    v, g = v[ok], g[ok]
    n = v.size
    if n < 25:
        return {"n": int(n)}
    o = np.argsort(v, kind="mergesort")
    parts = np.array_split(o, 5)
    means = [float(g[p].mean()) for p in parts]
    return {"n": int(n), "means": means, "spearman": float(FO.spearman(np.arange(5.0), np.array(means)))}


def ols(y: np.ndarray, X: np.ndarray, lags: int = 5) -> dict[str, Any]:
    """OLS with an intercept column in X; Newey-West (Bartlett) t."""
    n, k = X.shape
    XtX = X.T @ X
    b = np.linalg.solve(XtX, X.T @ y)
    e = y - X @ b
    Xe = X * e[:, None]
    S = Xe.T @ Xe
    for lag in range(1, lags + 1):
        w = 1 - lag / (lags + 1)
        G = Xe[lag:].T @ Xe[:-lag]
        S += w * (G + G.T)
    Inv = np.linalg.inv(XtX)
    V = Inv @ S @ Inv
    se = np.sqrt(np.diag(V))
    return {"b": b.tolist(), "t_nw": (b / se).tolist(), "n": int(n)}


def zs(x: np.ndarray) -> np.ndarray:
    return (x - x.mean()) / x.std(ddof=0)


def daily_book(root_days: np.ndarray, era: tuple[str, str], tdays: np.ndarray, net: np.ndarray, gross: np.ndarray,
               ) -> dict[str, Any]:
    sess = root_days[(root_days >= era[0]) & (root_days <= era[1])]
    pos = {d: i for i, d in enumerate(sess)}
    dn, dg = np.zeros(sess.size), np.zeros(sess.size)
    for d, a, b in zip(tdays, net, gross):
        dn[pos[d]] = a
        dg[pos[d]] = b
    out: dict[str, Any] = {"sessions": int(sess.size), "exposure_share_of_sessions": float(len(tdays) / sess.size)}
    for lab, x in (("net", dn), ("gross", dg)):
        cum = np.cumsum(x)
        out[lab] = {"sharpe": float(MET.sharpe(x, 0.0, 252)), "sortino": float(MET.sortino(x, 0.0, 252)),
                    "daily_sd": float(x.std(ddof=1)), "total": float(x.sum()),
                    "max_drawdown": float((cum - np.maximum.accumulate(cum)).min()), "skew_daily": float(pd.Series(x).skew())}
    out["net"]["sharpe_monthly_block_se"] = sharpe_block_se(dn, sess)
    out["_daily_net"], out["_sess"] = dn, sess
    return out


def sharpe_block_se(x: np.ndarray, days: np.ndarray, B: int = 1000, seed: int = SEED) -> float:
    months = pd.Series(days).str[:7].to_numpy()
    u, inv = np.unique(months, return_inverse=True)
    blocks = [x[inv == k] for k in range(u.size)]
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(B):
        xs = np.concatenate([blocks[j] for j in rng.integers(0, u.size, size=u.size)])
        sd = xs.std(ddof=1)
        vals.append(xs.mean() / sd * math.sqrt(252) if sd > 0 else 0.0)
    return float(np.std(vals, ddof=1))


def by_year(days: np.ndarray, g: np.ndarray) -> dict[str, Any]:
    ys = pd.Series(days).str[:4].to_numpy()
    out = {}
    for y in sorted(set(ys)):
        x = g[ys == y]
        out[y] = {"n": int(x.size), "mean": float(x.mean()), "sum": float(x.sum()), "t": t_ord(x)}
    sums = {y: v["sum"] for y, v in out.items()}
    best = max(sums, key=lambda y: sums[y])
    keep = ys != best
    return {"years": out, "profitable_years": f"{sum(v > 0 for v in sums.values())} of {len(sums)}",
            "best_year": best, "mean_without_best_year": float(g[keep].mean()) if keep.any() else float("nan"),
            "t_without_best_year": t_ord(g[keep])}


def concentration(days: np.ndarray, g: np.ndarray) -> dict[str, Any]:
    tot = float(g.sum())
    o = np.argsort(-g, kind="mergesort")
    cs = np.cumsum(g[o])
    half = int(np.searchsorted(cs, 0.5 * tot) + 1) if tot > 0 else None
    return {"total": tot, "days_to_half": half,
            "top_share": {str(k): float(g[o[:k]].sum() / tot) if tot != 0 else float("nan") for k in (1, 5, 10)}}


def index_held(B: dict[str, Any], R: str, D: dict[str, Any]) -> np.ndarray:
    row = B["t9a"][ROOTS[R]["comp"]]
    out = np.zeros(D["days"].size, dtype=bool)
    for i, d in enumerate(D["days"]):
        lead, nxt = lead_next(row, int(d[:4]), int(d[5:7]))
        held = lead if D["bd"][i] <= 9 else nxt
        out[i] = D["ym"][i] == held
    return out


def event_curve(D: dict[str, Any], sel: np.ndarray, C: np.ndarray, mult: float) -> dict[str, Any]:
    f, e = D["clock"]["fill"], D["clock"]["exit"]
    s, fill = D["s"][sel], D["fill"][sel]
    Cs = C[sel]
    curve = []
    for b_ in range(f + 1, e + 1):
        px = asof_last(Cs, f, b_)
        curve.append(float(np.mean(s * (px - fill) * mult)))
    after = asof_last(Cs, e + 1, min(e + 30, NBARS - 1))
    fade = -s * (after - D["exit"][sel]) * mult
    ok = np.isfinite(fade)
    return {"minutes_after_fill": list(range(1, e - f + 1)), "mean_signed_move": curve,
            "fade_30min_against_s": basic(fade[ok]), "fade_days_with_a_trade": int(ok.sum())}


# ================================================================== P0: the natural experiment's premise
def subindex_returns(B: dict[str, Any], R: str) -> dict[str, float | None]:
    row = B["t9a"][ROOTS[R]["comp"]]
    sd = list(B[R]["sdays"])
    bd = bd_of_month(np.array(sd, dtype=str))
    st = B[R]["settle"]
    out: dict[str, float | None] = {}
    for j in range(1, len(sd)):
        p, d = sd[j - 1], sd[j]
        lead, nxt = lead_next(row, int(d[:4]), int(d[5:7]))
        cl, cn = code_of(R, lead), code_of(R, nxt)
        w = s0(int(bd[j]))
        try:
            num = (1 - w) * st[(cl, d)] + w * st[(cn, d)] if w > 0 else st[(cl, d)]
            den = (1 - w) * st[(cl, p)] + w * st[(cn, p)] if w > 0 else st[(cl, p)]
            out[d] = num / den
        except KeyError:
            out[d] = None
    return out


def replicate_fund(B: dict[str, Any], R: str, f: str, L: int, Rt: dict[str, float | None]) -> list[dict[str, Any]]:
    nv = B["nav"][f]
    sd = np.array(sorted(Rt), dtype=str)
    split_days = {d for d, s in B["splits"] if s == f}
    rows = []
    dates, nav, prior = nv["date"].to_numpy(str), nv["nav"].to_numpy(float), nv["prior_nav"].to_numpy(float)
    for i in range(1, dates.size):
        t0, t1 = str(dates[i - 1]), str(dates[i])
        if t1 in split_days:
            continue
        gap = sd[np.searchsorted(sd, t0, side="right"): np.searchsorted(sd, t1, side="right")]
        ratio: float | None = 1.0
        for d in gap:
            r = Rt.get(str(d))
            if r is None:
                ratio = None
                break
            ratio *= r
        per = pd.Timestamp(t1) - pd.DateOffset(months=2)
        y = B["rates"].get(per.strftime("%Y-%m"))
        Dd = (pd.Timestamp(t1) - pd.Timestamp(t0)).days
        if ratio is None or y is None:
            rows.append({"date": t1, "err_bp": None})
            continue
        inav = prior[i] * (1 + L * (ratio - 1)) + prior[i] * Dd * (y / 360 - ER / 365)
        rows.append({"date": t1, "err_bp": (inav - nav[i]) / nav[i] * 1e4})
    return rows


def p0(B: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {"rule": "post-era share within 5 bp >= 0.95 and pre-era <= 0.50 (missing = failure); VOID "
                                   "(era) if either silver fund's pre-era share exceeds 0.50", "funds": {}}
    for R in ROOTS:
        Rt = subindex_returns(B, R)
        for f, L in ROOTS[R]["funds"]:
            rows = replicate_fund(B, R, f, L, Rt)
            res = {}
            for lab, lo, hi in (("pre", PRE[0], PRE[1]), ("post", P0_POST_FROM, POST[1])):
                rr = [r for r in rows if lo <= r["date"] <= hi]
                ok = [r for r in rr if r["err_bp"] is not None and abs(r["err_bp"]) <= 5.0]
                res[lab] = {"days": len(rr), "missing": sum(r["err_bp"] is None for r in rr),
                            "share_within_5bp": len(ok) / len(rr) if rr else float("nan")}
            out["funds"][f] = res
    si = [out["funds"][f] for f, _ in ROOTS["SI"]["funds"]]
    void = any(x["pre"]["share_within_5bp"] > 0.50 for x in si)
    post_ok = all(x["post"]["share_within_5bp"] >= 0.95 for x in si)
    out["status"] = "VOID_ERA" if void else ("PREMISE_HOLDS" if post_ok else "POST_NOT_REPRODUCED")
    if out["status"] == "POST_NOT_REPRODUCED":
        DEVIATIONS.append("P0: the post-era AGQ/ZSL match is below 95%; D634's figure is not reproduced on this build "
                          "(own-calendar business days, Prior NAV as NAV_t-1). Reported; the era is not voided.")
    return out


# ================================================================== components
def components(B: dict[str, Any]) -> dict[str, Any]:
    return B.get("components") or {}


def load_components(data_root: Path | None = None) -> tuple[dict[str, Any], list[str]]:
    notes = []
    if data_root is not None:
        # D618's loader (under F2's frame) resolves its fixtures under its own REPO; in a worktree they live in the main
        # checkout's data/. Point its fixture paths at data_root (the same move D688's d581() makes for D581).
        m618 = _load("m618", "stage0_d618_sharpened_ladder.py")
        fx = Path(data_root) / "fixtures"
        m618.FIX = fx
        m618.OPTS, m618.CUTS, m618.ES_1M = fx / "fut_es_options_eod.csv.gz", fx / "fut_es_0dte_volume_cutoffs.csv.gz", fx / "fut_ES_rth_1m.csv.gz"
        m618.STRIP, m618.SESSIONS = fx / "fut_settle_strip.csv.gz", fx / "fut_index_sessions.csv.gz"
    comp: dict[str, Any] = {}
    m667 = _load("d667r", "run_d667_hike_pause_overlay.py")
    arm = m667.load_arm()
    comp["#2 MACD arm"] = (np.asarray(arm["days"]).astype(str), np.asarray(arm["net"], float))
    notes.append("#2's loader (run_d667_hike_pause_overlay.load_arm, as D685/D699/D707) builds the arm from its own NQ "
                 "fixture and scores 2016-01-04..2023-12-29 only; that fixture's 2024+ slice is spent (D503). No SI, GC "
                 "or fund row >= 2024 is read.")
    m707 = _load("d707r", "vault_d707_last_hour_f2.py")
    X = m707.frame()
    F = m707.f2(X)
    sess = X.index.to_numpy(str)
    span = F["window"]
    g = X["gross"].to_numpy(float)
    comp["#4 F2"] = (sess[span], np.where(F["take"] & span, g - m707.COST, 0.0)[span])
    notes.append("#3 (NG winter spread): D565 stores monthly returns only (data/d565_ng_winter_spread.json); a daily rho "
                 "is not computable.")
    return comp, notes


def component_line(book: dict[str, Any], comp: dict[str, Any], hit: float, cost: float) -> dict[str, Any]:
    out = {"size": "one SIL", "cost_rt": cost, "net_sharpe": book["net"]["sharpe"], "net_sortino": book["net"]["sortino"],
           "gross_sharpe": book["gross"]["sharpe"], "gross_sortino": book["gross"]["sortino"],
           "net_sharpe_se": book["net"]["sharpe_monthly_block_se"], "hit_rate_net": hit,
           "skew_daily_net": book["net"]["skew_daily"], "C_d_daily_sd": book["net"]["daily_sd"], "rho": {}}
    dn, sess = book["_daily_net"], book["_sess"]
    pos = {d: i for i, d in enumerate(sess)}
    for k, (cd, cv) in comp.items():
        common = [(pos[d], j) for j, d in enumerate(cd) if d in pos]
        if len(common) < 30:
            out["rho"][k] = {"value": None, "common_days": len(common)}
            continue
        a = np.array([dn[i] for i, _ in common])
        b = np.array([cv[j] for _, j in common])
        out["rho"][k] = {"value": float(np.corrcoef(a, b)[0, 1]) if a.std() > 0 and b.std() > 0 else None,
                         "common_days": len(common)}
    out["rho"]["#3 NG winter spread"] = {"value": None, "why": "not computable: D565 has no daily series on disk"}
    return out


# ================================================================== the secondary (oracle first)
def secondary(prim: dict[str, Any], Pr: dict[str, np.ndarray], cost: float) -> dict[str, Any]:
    sel = prim["_sel"]
    g, n = prim["_g"], prim["_n"]
    m = prim["_m"]
    out: dict[str, Any] = {"note": "DECLARED SECONDARY, never a gate; the principal designs the filter (D690 tools)"}
    ot = FO.oracle_take(n)
    out["oracle_net_gt_0"] = {"take": int(ot.sum()), **FO.capture(n, ot)}
    ot2 = FO.oracle_take_threshold(g, cost, 2.0)
    out["oracle_gross_ge_2c"] = {"take": int(ot2.sum()), **FO.capture(n, ot2)}
    so = np.abs(m) >= 2 * cost
    out["size_only_oracle"] = {"rule": "take when the realised |move| >= 2c, trading the construction's own s",
                               **FO.capture(n, so)}
    days = prim["_days"]
    prof = {}
    for lab, v in (("year", pd.Series(days).str[:4].to_numpy()),):
        prof[lab] = {y: {"share_of_oracle_takes": float(ot[v == y].sum() / max(1, ot.sum())), "n": int((v == y).sum())}
                     for y in sorted(set(v))}
    for lab in ("absr_sig", "A", "P"):
        prof[lab] = tercile_means(Pr[lab][sel], ot.astype(float))
    out["oracle_winner_profile"] = prof
    # D649's template: b_t prior-only over earlier eligible post-era days, burn-in 250, projected >= 2c
    x = Pr["xsr"][sel]
    ok = np.isfinite(x)
    proj = np.full(g.size, np.nan)
    num = den = 0.0
    seen = 0
    for i in range(g.size):
        if ok[i]:
            if seen >= 250 and den > 0:
                proj[i] = num / den * x[i]
            num += g[i] * x[i]
            den += x[i] * x[i]
            seen += 1
    scored = np.isfinite(proj)
    take = scored & (proj >= 2 * cost)
    res: dict[str, Any] = {"scored_days": int(scored.sum()), "taken": int(take.sum()),
                           "rule": "b_t = sum g x / sum x^2 over earlier eligible post-era days (burn-in 250); take "
                                   "when b_t x_SR >= 2 x $8"}
    if scored.sum() >= 20:
        res["assess"] = FO.assess(proj[scored], take[scored], g[scored], n[scored])
        if np.ptp(proj[scored]) > 0:
            res["calibration"] = FO.calibration(proj[scored], g[scored], 10)
    res["reading"] = "UNRESOLVED (fewer than 30 filtered trades)" if take.sum() < 30 else "scored"
    if take.sum() >= 2:
        res["filtered"] = basic(n[take])
    out["d649_template"] = res
    return out


# ================================================================== gates and the verdict
def sigma_units(g: np.ndarray, scale: np.ndarray) -> np.ndarray:
    """A trade's gross in units of its own trailing daily sigma: g / (sigma_d x P_prev x mult)."""
    with np.errstate(invalid="ignore", divide="ignore"):
        z = g / scale
    return z[np.isfinite(z)]


def g4_rule(z_si: np.ndarray, z_gc: np.ndarray) -> dict[str, Any]:
    """AMENDMENT A1: G4 FIRES (FAIL, not the funds) only if gold's post-era mean in its own sigma units is at least
    silver's post-era mean in the same units. The design's s.5 predicts gold's effect is real but about 1/4 of silver's."""
    ms, mg = float(np.mean(z_si)), float(np.mean(z_gc))
    return {"si_mean_sigma_units": ms, "gc_mean_sigma_units": mg, "fires": bool(mg >= ms), "pass": bool(mg < ms)}


def gates(C: dict[str, dict[str, Any]], Pr: dict[str, np.ndarray], p0res: dict[str, Any],
          aum_null: dict[str, Any], Pgc: dict[str, np.ndarray] | None = None) -> dict[str, Any]:
    post, mid, pre, gcp = C["SI_settle_post"], C["SI_mid_post"], C["SI_settle_pre"], C["GC_settle_post"]
    G: dict[str, Any] = {}
    gp = post["gross"]
    G["G1"] = {"mean": gp["mean"], "t": gp["t"], "p95": post["null"]["p95"],
               "pass": bool(gp["mean"] > 0 and gp["t"] >= 2.0 and gp["mean"] > post["null"]["p95"]),
               "on_the_bar": post["ladder"].get("on_the_bar")}
    common, ia, ib = np.intersect1d(post["_days"], mid["_days"], return_indices=True)
    diff = post["_g"][ia] - mid["_g"][ib]
    G["G2"] = {"placebo_t": mid["gross"]["t"], "paired_days": int(common.size), "paired_diff": basic(diff),
               "pass": bool(mid["gross"]["t"] < 2.0 and diff.mean() > 0)}
    void = p0res["status"] == "VOID_ERA"
    G["G3"] = {"pre_t": pre["gross"]["t"], "post_minus_pre": gp["mean"] - pre["gross"]["mean"],
               "welch_t": (gp["mean"] - pre["gross"]["mean"]) / math.sqrt(gp["se"] ** 2 + pre["gross"]["se"] ** 2),
               "void": void, "pass": None if void else bool(pre["gross"]["t"] < 2.0 and gp["mean"] - pre["gross"]["mean"] > 0)}
    must(Pgc is not None, "G4 (A1) needs GC's predictors")
    z_si = sigma_units(post["_g"], Pr["sigma"][post["_sel"]] * Pr["P"][post["_sel"]] * ROOTS["SI"]["mult"])
    z_gc = sigma_units(gcp["_g"], Pgc["sigma"][gcp["_sel"]] * Pgc["P"][gcp["_sel"]] * ROOTS["GC"]["mult"])
    r4 = g4_rule(z_si, z_gc)
    G["G4"] = {"rule": "A1: fires iff GC's post-era mean (own sigma units) >= SI's post-era mean (same units)",
               **r4, "gc_t": gcp["gross"]["t"], "gc_t_sigma_units": t_ord(z_gc), "si_t_sigma_units": t_ord(z_si),
               "gc_n_sigma_units": int(z_gc.size), "si_n_sigma_units": int(z_si.size),
               "superseded_rule_gc_t_lt_2": bool(gcp["gross"]["t"] < 2.0)}
    share = Pr["share"][post["_sel"]]
    terc = tercile_means(share, post["_g"])
    G["G5"] = {"terciles": terc, "quintiles": quintiles(share, post["_g"]),
               "pass": bool(terc.get("top_minus_bottom", -1) > 0)}
    G["G5b"] = aum_null
    G["N"] = {"mean_net": post["net"]["mean"], "se": post["net"]["se"], "pass": bool(post["net"]["mean"] > 0)}
    G["reading"] = verdict(G)
    return G


def verdict(G: dict[str, Any]) -> str:
    if G["G1"]["t"] <= -2.0:
        return "FAIL (inverted)"
    controls = [G["G2"]["pass"], G["G4"]["pass"]] + ([] if G["G3"]["void"] else [G["G3"]["pass"]])
    if G["G1"]["pass"] and not all(controls):
        return "FAIL (not the funds)"
    if not G["G1"]["pass"]:
        return "NEITHER"
    if not G["G5"]["pass"]:
        return "NEITHER (no dose-response)"
    beats = G["G5b"].get("beats_p95")
    qual = " (funds' scale shown)" if beats else " (scale unresolved)"
    if G["G3"]["void"]:
        return "MECHANISM ONLY (VOID era: G3 not read)" + qual
    if G["N"]["pass"]:
        return "PASS" + qual
    if G["N"]["mean_net"] > -G["N"]["se"]:
        return "MECHANISM ONLY - UNRESOLVED (net)" + qual
    return "MECHANISM ONLY" + qual


def aum_rotation(post: dict[str, Any], Pr: dict[str, np.ndarray], R: str) -> dict[str, Any]:
    sel = post["_sel"]
    A, ar, Pp, V = Pr["A"][sel], np.abs(Pr["r_tau"][sel]), Pr["P"][sel], Pr["V"][sel]
    g = post["_g"]
    ok = np.isfinite(A) & np.isfinite(ar) & np.isfinite(V) & np.isfinite(Pp)
    A, ar, Pp, V, g = A[ok], ar[ok], Pp[ok], V[ok], g[ok]
    n = g.size
    k3 = n // 3

    def stat(Ak: np.ndarray) -> float:
        sh = Ak * ar / (Pp * ROOTS[R]["mult_full"]) / V
        o = np.argsort(sh, kind="mergesort")
        return float(g[o[n - k3:]].mean() - g[o[:k3]].mean())

    obs = stat(A)
    ks = rotation_offsets(n, AUM_ROT_LO)
    null = np.array([stat(np.roll(A, int(k))) for k in ks])
    s = null_summary(obs, null)
    s["beats_p95"] = bool(obs > s["p95"])
    s["note"] = "attribution qualifier, not a gate; AUM is slow (about four regimes in five years), so the null is coarse"
    return s


# ================================================================== the analysis
def build_all(B: dict[str, Any], fnd_buffer: int = FND_BUFFER) -> tuple[dict[str, Any], dict[str, Any]]:
    Dc = {k: decide(B, ck, fnd_buffer) for k, ck in CLOCKS.items()}
    Pc = {k: predictors(B, Dc[k]) for k in CLOCKS}
    return Dc, Pc


def sigma_rem(D: dict[str, Any], sel_all: np.ndarray) -> np.ndarray:
    """SD of the 20 prior eligible days' log(exit/fill) (prior-only)."""
    out = np.full(D["days"].size, np.nan)
    with np.errstate(invalid="ignore", divide="ignore"):
        lr = np.log(D["exit"] / D["fill"])
    hist: list[float] = []
    for i in range(D["days"].size):
        if len(hist) >= 20:
            out[i] = float(np.std(hist[-20:], ddof=1))
        if sel_all[i] and np.isfinite(lr[i]):
            hist.append(float(lr[i]))
    return out


def waterfall(D: dict[str, Any]) -> dict[str, Any]:
    ys = pd.Series(D["days"]).str[:4].to_numpy()
    out = {}
    for y in sorted(set(ys)):
        r = D["reason"][ys == y]
        out[y] = {"sessions": int(r.size), **{k: int((r == k).sum()) for k in REASONS}, "eligible": int((r == "").sum())}
    return out


def analyse(B: dict[str, Any], comp: dict[str, Any] | None = None, comp_notes: list[str] | None = None,
            workers: int | None = None) -> dict[str, Any]:
    t0 = time.time()
    DEVIATIONS.clear()
    Dc, Pc = build_all(B)
    audits = {"lag": {}, "known": {}}
    for k, ck in CLOCKS.items():
        audits["lag"][k] = audit_lag(B, ck, Dc[k], Pc[k])
        audits["known"][k] = known_answers(B, Dc[k])
    audits["sign"] = audit_sign(money)
    cellres = parallel_map(lambda k, v: cell(B, Dc, Pc, k), [(k, None) for k in CELLS], workers=workers)
    C = {k: cellres[k] for k in CELLS}
    post = C["SI_settle_post"]
    D = Dc["SI_settle"]
    Pr = Pc["SI_settle"]
    # the settlement-exit variant (same days)
    st = B["SI"]["settle"]
    sx = np.array([st.get((c, d), np.nan) for c, d in zip(B["SI"]["contract"], D["days"])])
    gsx = (D["s"] * (sx - D["fill"]) * ROOTS["SI"]["mult"])[post["_sel"]]
    audits["right_quantity"] = audit_rq(post, C["SI_mid_post"], C["GC_settle_post"], gsx, D, B["costs"]["SI"])
    p0res = p0(B)
    aumn = aum_rotation(post, Pr, "SI")
    G = gates(C, Pr, p0res, aumn, Pc["GC_settle"])
    cost = B["costs"]["SI"]
    # ---------------- groups
    book = daily_book(B["SI"]["days"], POST, post["_days"], post["_n"], post["_g"])
    grp: dict[str, Any] = {}
    grp["performance"] = {"per_trade_gross": post["gross"], "per_trade_net": post["net"],
                          "daily_book": {k: v for k, v in book.items() if not k.startswith("_")},
                          "mean_move_vs_2c": [post["gross"]["mean"], 2 * cost], "breakeven_cost": post["gross"]["mean"],
                          "hold_minutes": 29}
    grp["distribution"] = distribution(post["_g"], post["_n"])
    o = int(np.argmax(post["_g"]))
    idx = np.nonzero(post["_sel"])[0][o]
    grp["distribution"]["top_trade"] = {"day": str(D["days"][idx]), "contract": str(B["SI"]["contract"][idx]),
                                        "s": float(D["s"][idx]), "decision": float(D["dec"][idx]),
                                        "prior_settle": float(D["prev"][idx]), "fill": float(D["fill"][idx]),
                                        "exit": float(D["exit"][idx]), "gross": float(post["_g"][o])}
    sel = post["_sel"]
    dep: dict[str, Any] = {"by_year": by_year(post["_days"], post["_g"]), "concentration": concentration(post["_days"], post["_g"]),
                           "price_terciles": tercile_means(Pr["P"][sel], post["_g"]),
                           "aum_terciles": tercile_means(Pr["A"][sel], post["_g"]),
                           "absr_sigma_terciles": tercile_means(Pr["absr_sig"][sel], post["_g"])}
    inera = (D["days"] >= POST[0]) & (D["days"] <= POST[1])
    cs = D["carve"] & D["elig_or_carve"] & inera
    gc_, _ = money(D["s"], D["fill"], D["exit"], ROOTS["SI"]["mult"], cost)
    dep["carved_days"] = basic(gc_[cs])
    ih = index_held(B, "SI", D)[sel]
    dep["front_is_index_contract"] = {"yes": basic(post["_g"][ih]), "no": basic(post["_g"][~ih])}
    pre = C["SI_settle_pre"]
    pd_ = pre["_days"]
    dep["pre_era_split_at_pit_closure"] = {"before": basic(pre["_g"][pd_ < PIT_SPLIT]), "after": basic(pre["_g"][pd_ >= PIT_SPLIT])}
    # D629's lesson and D648's form question
    srem = sigma_rem(D, D["elig"])
    with np.errstate(invalid="ignore"):
        xgm = srem ** 2 * Pr["share"] * Pr["P"] * ROOTS["SI"]["mult"]
    fin = np.isfinite(Pr["xsr"][sel]) & np.isfinite(Pr["absr_sig"][sel]) & np.isfinite(xgm[sel])
    y = post["_g"][fin]
    xs, xc, xg = Pr["xsr"][sel][fin], Pr["absr_sig"][sel][fin], xgm[sel][fin]
    one = np.ones(y.size)
    d629: dict[str, Any] = {"slope_on_xsr": ols(y, np.column_stack([one, xs])),
                            "slope_on_xsr_with_control": ols(y, np.column_stack([one, xs, xc]))}
    yrs = pd.Series(post["_days"][fin]).str[:4].to_numpy()
    d629["by_year_slope"] = {yy: ols(y[yrs == yy], np.column_stack([one[yrs == yy], xs[yrs == yy]]))
                             for yy in sorted(set(yrs)) if (yrs == yy).sum() > 20}
    d629["leave_one_year_out"] = {yy: ols(y[yrs != yy], np.column_stack([one[yrs != yy], xs[yrs != yy]]))
                                  for yy in sorted(set(yrs))}
    at = Pr["A"][sel][fin]
    o3 = np.argsort(at, kind="mergesort")
    k3 = at.size // 3
    d629["within_aum_terciles"] = {lab: ols(y[p], np.column_stack([one[p], xs[p]]))
                                   for lab, p in (("low", o3[:k3]), ("mid", o3[k3:-k3]), ("top", o3[-k3:]))}
    dep["d629"] = d629
    d648 = {"settlement": ols(y, np.column_stack([one, zs(xg), zs(xs), zs(xc)]))}
    Dm, Pm = Dc["SI_mid"], Pc["SI_mid"]
    mp = C["SI_mid_post"]
    srm = sigma_rem(Dm, Dm["elig"])
    with np.errstate(invalid="ignore"):
        xgm_m = srm ** 2 * Pm["share"] * Pm["P"] * ROOTS["SI"]["mult"]
    sm = mp["_sel"]
    fm = np.isfinite(Pm["xsr"][sm]) & np.isfinite(Pm["absr_sig"][sm]) & np.isfinite(xgm_m[sm])
    ym = mp["_g"][fm]
    d648["midday"] = ols(ym, np.column_stack([np.ones(ym.size), zs(xgm_m[sm][fm]), zs(Pm["xsr"][sm][fm]),
                                              zs(Pm["absr_sig"][sm][fm])]))
    d648["columns"] = ["intercept", "z(x_GM)", "z(x_SR)", "z(|r|/sigma)"]
    dep["d648_form"] = d648
    grp["dependencies"] = dep
    nulls = {k: C[k]["null"] for k in CELLS}
    nulls["N2_aum_rotation"] = aumn
    grp["nulls"] = nulls
    # ---------------- diagnostics
    diag: dict[str, Any] = {"event_curve": event_curve(D, sel, B["SI"]["C"], ROOTS["SI"]["mult"]),
                            "always_long": basic(post["_m"]), "always_short": basic(-post["_m"]),
                            "settlement_exit_variant": basic(gsx[np.isfinite(gsx)])}
    zsig = {}
    for k in ("SI_settle_post", "SI_settle_pre", "GC_settle_post", "GC_settle_pre"):
        c_ = C[k]
        Pk = Pc[CELLS[k][0]]
        R = CELLS[k][0][:2]
        z = c_["_g"] / (Pk["sigma"][c_["_sel"]] * Pk["P"][c_["_sel"]] * ROOTS[R]["mult"])
        zsig[k] = z[np.isfinite(z)]
    td = (zsig["SI_settle_post"].mean() - zsig["SI_settle_pre"].mean()) - (zsig["GC_settle_post"].mean() - zsig["GC_settle_pre"].mean())
    tse = math.sqrt(sum(v.var(ddof=1) / v.size for v in zsig.values()))
    diag["triple_difference_sigma_units"] = {"value": float(td), "se": tse, "t": float(td / tse)}
    Db, Pb = build_all(B, FND_BUFFER_BESIDE)
    cb = cell(B, Db, Pb, "SI_settle_post", with_null=False)
    diag["fnd_buffer_10_sessions"] = public({k: v for k, v in cb.items() if k != "ladder"})
    # ---------------- stress
    stress = {}
    for c_ in STRESS:
        nn = post["_g"] - c_
        bk = daily_book(B["SI"]["days"], POST, post["_days"], nn, post["_g"])
        stress[f"${c_:.2f}"] = {"mean_net": float(nn.mean()), "t_net": t_ord(nn), "net_sharpe": bk["net"]["sharpe"],
                                "net_sortino": bk["net"]["sortino"]}
    stress["note"] = "$13.00 = $8 + one tick of entry slippage; $24.50 = $3 + SI's quoted spread 4.30 ticks (d507_exec)"
    # ---------------- component line and secondary
    comp = comp or {}
    cl = component_line(book, comp, float((post["_n"] > 0).mean()), cost)
    sec = secondary(post, Pr, cost)
    if comp_notes:
        DEVIATIONS.extend(comp_notes)
    DEVIATIONS.append("Business days for the carve and for P0 are counted on the root's own sessions / settlement days "
                      "(declared approximation, D676 R3).")
    DEVIATIONS.append("P0 uses each NAV row's own 'Prior NAV' as NAV_t-1 and skips split days (gate 0b).")
    doc = {
        "spec": {"record": str(SPEC_DOC.relative_to(REPO)).replace("\\", "/"), "eras": {"post": POST, "pre": PRE},
                 "cut": CUT, "costs": B["costs"], "clocks": {k: {"dec": list(v["dec"]), "fill": v["fill"],
                                                                 "exit": v["exit"]} for k, v in CLOCKS.items()},
                 "fnd_buffer": FND_BUFFER, "rotation_offsets": [ROT_LO, "n-20"]},
        "verdict": G["reading"],
        "gates": G,
        "cells": {k: public(v) for k, v in C.items()},
        "nulls": nulls,
        "groups": grp,
        "stress": stress,
        "component_line": cl,
        "p0": p0res,
        "waterfall": {k: waterfall(Dc[ck]) for k, ck in (("SI_settle", "SI_settle"), ("SI_mid", "SI_mid"),
                                                         ("GC_settle", "GC_settle"), ("GC_mid", "GC_mid"))},
        "secondary": sec,
        "diagnostics": diag,
        "power_reference": str(POWER_OUT.relative_to(REPO)).replace("\\", "/"),
        "audits": audits,
        "reads": B.get("reads", {}),
        "deviations": list(DEVIATIONS),
        "timings": {"analyse_s": time.time() - t0, "load_s": B.get("load_s")},
    }
    missing = [k for k in REQUIRED_OUTPUTS if k not in doc]
    must(not missing, f"REQUIRED_OUTPUTS missing: {missing}")
    return doc


# ================================================================== POWER
def power_inputs(B: dict[str, Any]) -> dict[str, Any]:
    must(B["blind"], "POWER must run on the blinded bundle")
    Dc, Pc = build_all(B)
    for k, ck in CLOCKS.items():
        audit_lag(B, ck, Dc[k], Pc[k])
    for R in ROOTS:
        late = B[R]["days"] >= BLIND_FROM
        for ck in CLOCKS.values():
            if ck["root"] == R:
                must(not np.isfinite(B[R]["C"][late, ck["fill"]]).any() and not np.isfinite(B[R]["C"][late, ck["exit"]]).any(),
                     f"[BLIND] a fill or exit price on or after {BLIND_FROM} is readable in POWER")

    def pool(ck: str) -> np.ndarray:
        D, Pr = Dc[ck], Pc[ck]
        sel = D["elig"] & (D["days"] >= NOISE[0]) & (D["days"] <= NOISE[1]) & np.isfinite(Pr["sigma"])
        z = (D["exit"] - D["fill"])[sel] / (Pr["sigma"][sel] * D["prev"][sel])
        must(bool(np.isfinite(z).all()) and z.size >= 30, f"POWER noise pool {ck}: {z.size} days")
        return z

    def side(ck: str, era: tuple[str, str]) -> dict[str, np.ndarray]:
        D, Pr = Dc[ck], Pc[ck]
        R = D["root"]
        sel = D["elig"] & (D["days"] >= era[0]) & (D["days"] <= era[1])
        fin = sel & np.isfinite(Pr["sigma"]) & np.isfinite(Pr["xsr"]) & np.isfinite(Pr["share"])
        return {"s": D["s"][fin], "scale": Pr["sigma"][fin] * D["prev"][fin] * ROOTS[R]["mult"], "xsr": Pr["xsr"][fin],
                "share": Pr["share"][fin], "days": D["days"][fin], "eligible": int(sel.sum()), "dropped": int((sel & ~fin).sum())}

    return {"noise": {"SI_settle": pool("SI_settle"), "SI_mid": pool("SI_mid"), "GC_settle": pool("GC_settle")},
            "post": side("SI_settle", POST), "mid": side("SI_mid", POST), "pre": side("SI_settle", PRE),
            "gc": side("GC_settle", POST), "cost": B["costs"]["SI"], "waterfall": waterfall(Dc["SI_settle"])}


def sim_dataset(I: dict[str, Any], Srot: np.ndarray, beta: float, bi: int, b: int) -> dict[str, Any]:
    rng = np.random.default_rng([SEED, bi, b])
    po, mi, pr, gc = I["post"], I["mid"], I["pre"], I["gc"]
    nz = I["noise"]
    z = nz["SI_settle"][rng.integers(0, nz["SI_settle"].size, po["s"].size)]
    m = po["s"] * beta * po["xsr"] + z * po["scale"]
    g = po["s"] * m
    rot = (Srot * m[None, :]).mean(axis=1)
    mean, t = float(g.mean()), t_ord(g)
    p95 = float(np.percentile(rot, 95))
    g1 = mean > 0 and t >= 2.0 and mean > p95
    zm = nz["SI_mid"][rng.integers(0, nz["SI_mid"].size, mi["s"].size)]
    gm = mi["s"] * (zm * mi["scale"])
    _, ia, ib = np.intersect1d(po["days"], mi["days"], return_indices=True)
    g2 = t_ord(gm) < 2.0 and float((g[ia] - gm[ib]).mean()) > 0
    zp = nz["SI_settle"][rng.integers(0, nz["SI_settle"].size, pr["s"].size)]
    gp = pr["s"] * (zp * pr["scale"])
    g3 = t_ord(gp) < 2.0 and mean - float(gp.mean()) > 0
    zg = nz["GC_settle"][rng.integers(0, nz["GC_settle"].size, gc["s"].size)]
    gg = gc["s"] * (gc["s"] * beta * gc["xsr"] + zg * gc["scale"])
    g4 = g4_rule(sigma_units(g, po["scale"]), sigma_units(gg, gc["scale"]))["pass"]    # A1
    g4_old = t_ord(gg) < 2.0                                                              # the superseded rule
    n = g.size
    o = np.argsort(po["share"], kind="mergesort")
    k = n // 3
    g5 = float(g[o[n - k:]].mean() - g[o[:k]].mean()) > 0
    net = mean - I["cost"] > 0
    full = g1 and g2 and g3 and g4 and g5
    return {"g1": bool(g1), "full": bool(full), "pass": bool(full and net), "t": t, "mean": mean,
            "beats_p95": bool(mean > p95), "t_ge_2": bool(t >= 2.0), "sd": float(g.std(ddof=1)),
            "g2": bool(g2), "g3": bool(g3), "g4": bool(g4), "g4_superseded_t_lt_2": bool(g4_old), "g5": bool(g5)}


def run_power(I: dict[str, Any], n_sets: int = N_POWER, workers: int | None = None, chunks: int = 8
              ) -> dict[str, list[dict[str, Any]]]:
    po = I["post"]
    ks = rotation_offsets(po["s"].size, ROT_LO)
    Srot = po["s"][(np.arange(po["s"].size)[None, :] - ks[:, None]) % po["s"].size]
    items = [((bi, j), None) for bi in range(len(BETAS)) for j in range(chunks)]

    def work(key: tuple[int, int], _v: Any) -> list[dict[str, Any]]:
        bi, j = key
        return [sim_dataset(I, Srot, BETAS[bi], bi, b) for b in range(j, n_sets, chunks)]

    res = parallel_map(work, items, workers=workers)
    out: dict[str, list[dict[str, Any]]] = {}
    for bi in range(len(BETAS)):
        rows: list[dict[str, Any] | None] = [None] * n_sets
        for j in range(chunks):
            for q, b in enumerate(range(j, n_sets, chunks)):
                rows[b] = res[(bi, j)][q]
        out[str(BETAS[bi])] = rows  # type: ignore[assignment]
    return out


def power_summary(I: dict[str, Any], sims: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    po = I["post"]
    n = po["s"].size
    rate = {b: float(np.mean([r["g1"] for r in rows])) for b, rows in sims.items()}
    full = {b: float(np.mean([r["full"] for r in rows])) for b, rows in sims.items()}
    pas = {b: float(np.mean([r["pass"] for r in rows])) for b, rows in sims.items()}
    comp = {b: {k: float(np.mean([r[k] for r in rows])) for k in ("g2", "g3", "g4", "g4_superseded_t_lt_2", "g5")} for b, rows in sims.items()}
    z0 = sims[str(0.0)]
    sd0 = float(np.median([r["sd"] for r in z0]))
    mde_usd = 2.80 * sd0 / math.sqrt(n)
    xm = float(po["xsr"].mean())
    bs = [float(b) for b in sims]
    rs = [rate[b] for b in sims]
    beta80 = None
    for (b0, r0), (b1, r1) in zip(zip(bs, rs), zip(bs[1:], rs[1:])):
        if r0 < 0.8 <= r1:
            beta80 = b0 + (0.8 - r0) * (b1 - b0) / (r1 - r0)
            break
    return {
        "betas": bs,
        "expected_gross_per_SIL": {b: float(b) * xm for b in sims},
        "g1_rate": rate, "full_reading_rate": full, "pass_rate": pas, "controls_and_g5_rates": comp,
        "mean_t": {b: float(np.mean([r["t"] for r in rows])) for b, rows in sims.items()},
        "n1_size_check": {"beta": 0.0, "share_beating_own_rotation_p95": float(np.mean([r["beats_p95"] for r in z0])),
                          "share_t_ge_2": float(np.mean([r["t_ge_2"] for r in z0])), "target": [0.03, 0.07],
                          "ok": bool(0.03 <= float(np.mean([r["beats_p95"] for r in z0])) <= 0.07)},
        "mde": {"usd_gross_per_SIL_80pct_at_t2": mde_usd, "sd_per_trade_beta0_median": sd0, "n": int(n),
                "beta_at_80pct_g1_interpolated": beta80, "mean_xsr_per_SIL": xm},
        "paper_kill": {"rule": "G1 rate at beta 0.31 below 0.25 sends the record back to the principal (design s.10)",
                       "g1_rate_at_0.31": rate[str(0.31)], "triggered": bool(rate[str(0.31)] < PAPER_KILL)},
    }


def power_main(data_root: Path, workers: int | None = None) -> int:
    t0 = time.time()
    B = load(data_root, blind=True)
    P(f"  loaded (blinded from {BLIND_FROM}) in {B['load_s']:.1f}s")
    I = power_inputs(B)
    P(f"  noise pools: SI settle {I['noise']['SI_settle'].size}, SI mid {I['noise']['SI_mid'].size}, "
      f"GC settle {I['noise']['GC_settle'].size}; post sample {I['post']['s'].size} "
      f"(eligible {I['post']['eligible']}, dropped for predictors {I['post']['dropped']})")
    t1 = time.time()
    sims = run_power(I, N_POWER, workers)
    S = power_summary(I, sims)
    nz = I["noise"]
    doc = {
        "spec": {"record": str(SPEC_DOC.relative_to(REPO)).replace("\\", "/"), "n_datasets_per_beta": N_POWER,
                 "seed": SEED, "injection": "move = s x beta x x_SR + z x sigma_d x P x 1000 (z iid from the noise pool); "
                                             "the effect is in the direction of s",
                 "controls": "G2 midday and G3 pre-era are noise-only; G4 GC carries beta x its own x_SR; G4 is A1 (GC mean in sigma units >= SI's fires); the superseded t < 2 rate is reported beside"},
        "noise": {k: {"days": int(v.size), "sd_sigma_units": float(v.std(ddof=1)), "mean_sigma_units": float(v.mean()),
                      "excess_kurtosis": float(pd.Series(v).kurt())} for k, v in nz.items()} | {"window": NOISE},
        "sample": {k: {"n": int(I[k]["s"].size), "eligible": I[k]["eligible"], "dropped_for_predictors": I[k]["dropped"]}
                   for k in ("post", "mid", "pre", "gc")} | {"post_waterfall": I["waterfall"]},
        "betas": S["betas"], "expected_gross_per_SIL": S["expected_gross_per_SIL"],
        "g1_rate": S["g1_rate"], "full_reading_rate": S["full_reading_rate"], "pass_rate": S["pass_rate"],
        "controls_and_g5_rates": S["controls_and_g5_rates"], "mean_t": S["mean_t"],
        "n1_size_check": S["n1_size_check"], "mde": S["mde"], "paper_kill": S["paper_kill"],
        "audits": {"blind": f"no fill or exit price on or after {BLIND_FROM} readable", "lag": "passed on every clock"},
        "reads": B["reads"],
        "timings": {"load_s": B["load_s"], "simulate_s": time.time() - t1, "total_s": time.time() - t0},
    }
    missing = [k for k in POWER_REQUIRED if k not in doc]
    must(not missing, f"POWER_REQUIRED missing: {missing}")
    POWER_OUT.write_text(dump(doc), encoding="utf-8")
    P(f"  beta   E[gross]/SIL  G1 rate  full  PASS  mean t")
    for b in S["betas"]:
        k = str(b)
        P(f"  {b:5.3f}  {S['expected_gross_per_SIL'][k]:10.2f}  {S['g1_rate'][k]:7.3f}  {S['full_reading_rate'][k]:5.3f}"
          f"  {S['pass_rate'][k]:5.3f}  {S['mean_t'][k]:6.2f}")
    P(f"  N1 size at beta 0: {S['n1_size_check']['share_beating_own_rotation_p95']:.3f} beat their own p95 "
      f"(t >= 2: {S['n1_size_check']['share_t_ge_2']:.3f})")
    P(f"  MDE: ${S['mde']['usd_gross_per_SIL_80pct_at_t2']:.2f} gross per SIL; beta at 80% G1 "
      f"{S['mde']['beta_at_80pct_g1_interpolated']}")
    P(f"  PAPER KILL (G1 rate at 0.31 < 0.25): {S['paper_kill']['triggered']}")
    P(f"  wrote {POWER_OUT} in {time.time() - t0:.0f}s")
    return 0


# ================================================================== output
def _clean(o: Any) -> Any:
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, np.ndarray):
        return [_clean(v) for v in o.tolist()]
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (float, np.floating)):
        f = float(o)
        return f if math.isfinite(f) else None
    return o


def dump(doc: dict[str, Any]) -> str:
    return json.dumps(_clean(doc), indent=1) + "\n"


def run_main(data_root: Path, check: bool = False) -> int:
    if not check and OUT.exists():
        raise D709Error(f"{OUT} exists: --run refuses a second run (use --check)")
    if check and not OUT.exists():
        raise D709Error(f"{OUT} does not exist: nothing to check")
    B = load(data_root, blind=False)
    comp, notes = load_components(data_root)
    doc = analyse(B, comp, notes)
    if check:
        old = json.loads(OUT.read_text(encoding="utf-8"))
        new = json.loads(dump(doc))
        old.pop("timings", None)
        new.pop("timings", None)
        must(dump(old) == dump(new), "[CHECK] the output does not reproduce (timings excluded)")
        P("  CHECK: reproduces byte for byte (timings excluded)")
        return 0
    OUT.write_text(dump(doc), encoding="utf-8")
    P(f"  VERDICT: {doc['verdict']}")
    P(f"  wrote {OUT}")
    return 0


# ================================================================== the self-test
def gc_inject_for(si_inject: float, ratio: float) -> float:
    """The GC injection whose effect in GC's own sigma units is `ratio` x SI's. The injected move is
    inject x sqrt(|r|) x price and |r| scales with sigma, so the sigma-unit effect scales as inject / sqrt(sigma)."""
    return ratio * si_inject * math.sqrt(0.009 / 0.017)


def synthetic(inject: float = 0.0, seed: int = 11, nav_pre_noise_bp: float = 60.0, inject_gc: float = 0.0
              ) -> dict[str, Any]:
    """Synthetic bars, strip, calendar and funds for both roots, 2010-06-01 .. 2023-12-29. `inject` puts a move of
    inject x sqrt(|r_tau|) x price in the direction of s into SI's 12:56..13:24 on post-era days only; `inject_gc`
    does the same on GC's own clock (13:01..13:29)."""
    rng = np.random.default_rng(seed)
    allb = pd.bdate_range("2010-06-01", "2023-12-29").strftime("%Y-%m-%d").to_numpy()
    days = allb[rng.random(allb.size) > 0.01]
    B: dict[str, Any] = {"nav": {}, "reads": {"synthetic": True}, "blind": False, "load_s": 0.0}
    active = {"SI": (3, 5, 7, 9, 12), "GC": (2, 4, 6, 8, 12)}
    sig = {"SI": 0.017, "GC": 0.009}
    px0 = {"SI": 17.0, "GC": 1200.0}
    volb = {"SI": 3.0, "GC": 300.0}
    early = set(rng.choice(days, size=50, replace=False))
    for R in ROOTS:
        nd = days.size
        C = np.full((nd, NBARS), np.nan)
        contract = np.empty(nd, dtype=object)
        settle: dict[tuple[str, str], float] = {}
        price = px0[R]
        prev_front_settle: dict[str, float] = {}
        ms = pd.Series(days).str[:7]
        last_of = pd.Series(days).groupby(ms.values).max().to_dict()
        rows_d, rows_b, rows_c = [], [], []
        close_et = np.full(nd, ROOTS[R]["close"], dtype=object)
        prev_code = None
        same = np.ones(nd, dtype=bool)
        for i, d in enumerate(days):
            y, m = int(d[:4]), int(d[5:7])
            cands = [(yy, mm) for yy in (y, y + 1) for mm in active[R] if (yy, mm) > (y, m)]
            fy, fm = min(cands)
            code = code_of(R, (fy, fm))
            contract[i] = code
            if prev_code is not None and code != prev_code:
                same[i] = False
            prev_code = code
            steps = rng.standard_normal(NBARS) * sig[R] / math.sqrt(NBARS)
            path = price * np.exp(np.cumsum(steps))
            inj = inject if R == "SI" else inject_gc
            if inj and POST[0] <= d <= POST[1] and code in prev_front_settle:
                ck = CLOCKS[f"{R}_settle"]
                pv = prev_front_settle[code]
                dec = path[ck["dec"][1]]
                s = np.sign(dec - pv)
                amp = inj * math.sqrt(abs(dec / pv - 1)) * path[ck["fill"]]
                ramp = np.zeros(NBARS)
                a, e = ck["fill"], ck["exit"]
                ramp[a + 1: e + 1] = np.linspace(0, 1, e - a + 1)[1:]
                ramp[e + 1:] = 1.0
                path = path + s * amp * ramp
            present = rng.random(NBARS) > 0.01
            last = NBARS
            if d in early:
                close_et[i] = "12:59"
                last = bar("12:59") + 1
                present[last:] = False
            C[i, present] = path[present]
            stl_bar = min(bar(ROOTS[R]["close"]), last - 1)
            st_px = float(path[stl_bar])
            for k in range(0, 14):
                yy, mm = (fy * 12 + fm - 1 + k) // 12, (fy * 12 + fm - 1 + k) % 12 + 1
                if mm in active[R]:
                    settle[(code_of(R, (yy, mm)), d)] = round(st_px * math.exp(0.002 * k), 6)
            prev_front_settle = {c: v for (c, dd), v in settle.items() if dd == d}
            price = float(path[-1])
            nz = np.nonzero(present)[0]
            rows_d.append(np.full(nz.size, d))
            rows_b.append(nz)
            rows_c.append(path[nz])
        raw_day = np.concatenate(rows_d)
        raw_bar = np.concatenate(rows_b)
        raw_close = np.concatenate(rows_c)
        PR = np.isfinite(C)
        vol = PR.sum(axis=1) * volb[R]
        sdays = np.array(days, dtype=str)
        B[R] = {"days": np.array(days, dtype=str), "C": C, "PR": PR, "vol": vol.astype(float),
                "contract": contract.astype(str), "same_front": same, "close_et": close_et.astype(str),
                "trading": np.ones(nd, dtype=bool), "settle": settle, "sdays": sdays, "republications": [],
                "raw_day": raw_day, "raw_bar": raw_bar, "raw_close": raw_close, "blinded": False}
    B["rates"] = {f"{y}-{m:02d}": 0.02 for y in range(2009, 2024) for m in range(1, 13)}
    B["splits"] = []
    B["t9a"] = facts_table()
    B["gsci"] = {"SI": ["H", "H", "K", "K", "N", "N", "U", "U", "Z", "Z", "Z", "H"],
                 "GC": ["G", "J", "J", "M", "M", "Q", "Q", "Z", "Z", "Z", "Z", "G"]}
    B["costs"] = {"SI": 8.0, "GC": 5.9334505021406643, "SI_quoted_stress": 24.5}
    for R, aums in (("SI", (3e8, 3e7)), ("GC", (1.5e8, 2e7))):
        Rt = subindex_returns(B, R)
        dts = [str(d) for d in B[R]["sdays"] if Rt.get(str(d)) is not None]
        for (f, L), a in zip(ROOTS[R]["funds"], aums):
            nav = [50.0]
            prior = [50.0]
            dates = [dts[0]]
            for t0, t1 in zip(dts, dts[1:]):
                y = B["rates"][(pd.Timestamp(t1) - pd.DateOffset(months=2)).strftime("%Y-%m")]
                Dd = (pd.Timestamp(t1) - pd.Timestamp(t0)).days
                v = nav[-1] * (1 + L * (Rt[t1] - 1)) + nav[-1] * Dd * (y / 360 - ER / 365)
                if t1 < POST[0]:
                    v *= 1 + rng.standard_normal() * nav_pre_noise_bp / 1e4
                prior.append(nav[-1])
                nav.append(v)
                dates.append(t1)
            B["nav"][f] = pd.DataFrame({"date": dates, "nav": nav, "prior_nav": prior,
                                        "aum": a * (1 + 0.3 * np.sin(np.arange(len(dates)) / 300.0))})
    check_bundle(B)
    return B


def expect_raise(name: str, fn: Callable[[], Any], log: list[str]) -> None:
    try:
        fn()
    except D709Error as e:
        log.append(f"    raises as required -- {name}: {str(e)[:110]}")
        return
    raise D709Error(f"[SELFTEST] {name} did NOT raise on its broken book")


def selftest() -> int:
    t0 = time.time()
    lines: list[str] = []
    P("D709 SELFTEST")
    # [1] exactness of the enumerated rotation, chunk == whole, on a tie-heavy input
    rng = np.random.default_rng(3)
    n = 400
    s = rng.choice([-1.0, 1.0], n)
    m = rng.choice([0.0, 0.0, 0.0, 5.0, -5.0, 10.0], n)
    ks = rotation_offsets(n, ROT_LO)
    whole = rotate_enumerated(s, m, ks)
    parts = np.empty_like(whole)
    for j in range(8):
        parts[j::8] = rotate_enumerated(s, m, ks[j::8])
    must(np.array_equal(whole, parts), "[EXACT] 8 strided chunks differ from the whole")
    for k in range(ks.size):
        must(whole[k] == scorer(np.roll(s, int(ks[k])), m), f"[EXACT] row {ks[k]} differs from the scorer")
    rotation_cell(s, m)
    P(f"  [1] enumerated rotation: {ks.size} offsets, every row == the scorer bit for bit on a tie-heavy input; "
      f"8 strided chunks == whole")
    # [2] the seal
    expect_raise("seal on a 2024-01-02 bar", lambda: guard(["2023-12-29", "2024-01-02"], "bars"), lines)
    Bs = synthetic(inject=0.012, seed=11)
    Bs["SI"]["settle"][("SIH4", "2024-01-02")] = 1.0
    expect_raise("seal on a 2024-01-02 strip row", lambda: check_bundle(Bs), lines)
    del Bs["SI"]["settle"][("SIH4", "2024-01-02")]
    Bs["nav"]["AGQ"] = pd.concat([Bs["nav"]["AGQ"], pd.DataFrame({"date": ["2024-01-02"], "nav": [1.0], "prior_nav": [1.0],
                                                                   "aum": [1.0]})], ignore_index=True)
    expect_raise("seal on a 2024-01-02 NAV row", lambda: check_bundle(Bs), lines)
    Bs["nav"]["AGQ"] = Bs["nav"]["AGQ"].iloc[:-1].reset_index(drop=True)
    check_bundle(Bs)
    P("  [2] seal: a 2024-01-02 bar, strip row and NAV row each RAISE")
    # [3] sign audit, in money
    audit_sign(money)
    expect_raise("sign audit on a flipped s", lambda: audit_sign(lambda s_, f_, e_, mu, c_: money(-s_, f_, e_, mu, c_)), lines)
    P("  [3] sign audit: +$0.010 after s=+1 books +$10.00 / +$2.00 net on one SIL; s=-1 -$10.00 / -$18.00; MGC +$1.00; "
      "a flipped s RAISES")
    # [4] lag audit, second implementation
    Dc, Pc = build_all(Bs)
    audit_lag(Bs, CLOCKS["SI_settle"], Dc["SI_settle"], Pc["SI_settle"])
    broken = dict(CLOCKS["SI_settle"])
    broken["dec"] = (bar("12:51"), bar("12:55"))       # the decision reads the fill bar
    Dbroken = decide(Bs, broken)
    expect_raise("lag audit on a decision read from the fill bar",
                 lambda: audit_lag(Bs, CLOCKS["SI_settle"], Dbroken, None), lines)
    P("  [4] lag audit (a plain loop over raw rows, never calling decide): passes; a decision read at the fill bar RAISES")
    # [5] known answers
    for k in CLOCKS:
        known_answers(Bs, Dc[k])
    Dk = dict(Dc["SI_settle"])
    Dk["fnd"] = Dk["fnd"] + 1
    expect_raise("known answer on a shifted FND count", lambda: known_answers(Bs, Dk), lines)
    P("  [5] known answers: SI carve months {1,2,4,6,8,11}, GC {1,3,5,7,11}, 13:24 / 13:29 closes, FND = last session "
      "of the prior month; a shifted FND RAISES")
    # [6] right quantity
    c_post = cell(Bs, Dc, Pc, "SI_settle_post", with_null=False)
    c_mid = cell(Bs, Dc, Pc, "SI_mid_post", with_null=False)
    c_gc = cell(Bs, Dc, Pc, "GC_settle_post", with_null=False)
    D = Dc["SI_settle"]
    sx = np.array([Bs["SI"]["settle"].get((c, d), np.nan) for c, d in zip(Bs["SI"]["contract"], D["days"])])
    gsx = (D["s"] * (sx - D["fill"]) * 1000)[c_post["_sel"]] + 0.0
    audit_rq(c_post, c_mid, c_gc, gsx, D, 8.0)
    zero = dict(CLOCKS["SI_settle"])
    zero["exit"] = zero["fill"]
    Dz = decide(Bs, zero)
    Dcz = dict(Dc)
    Dcz["SI_settle"] = Dz
    cz = cell(Bs, Dcz, Pc, "SI_settle_post", with_null=False)
    expect_raise("right-quantity on a zero-length hold", lambda: audit_rq(cz, c_mid, c_gc, gsx, Dz, 8.0), lines)
    cz0 = dict(c_post)
    cz0["_g"] = np.zeros_like(c_post["_g"])
    cz0["_n"] = cz0["_g"] - 8.0
    expect_raise("right-quantity on identically zero moves under a valid clock",
                 lambda: audit_rq(cz0, c_mid, c_gc, gsx, D, 8.0), lines)
    cn = dict(c_post)
    cn["_n"] = c_post["_g"] - 13.0
    expect_raise("right-quantity on a net charged at the wrong cost", lambda: audit_rq(cn, c_mid, c_gc, gsx, D, 8.0), lines)
    expect_raise("right-quantity when the primary IS the midday placebo",
                 lambda: audit_rq(c_post, c_post, c_gc, gsx, D, 8.0), lines)
    P("  [6] right quantity: moves nonzero, net = gross - $8 exactly, primary != midday / GC / settlement exit, carve "
      "nonempty, eras disjoint; a zero-length hold RAISES")
    # [7] the book check: end to end on synthetic bars, with and without an injected effect
    doc = analyse(Bs, workers=4)
    json.loads(dump(doc))
    must(doc["verdict"].startswith(("PASS", "MECHANISM ONLY")), f"[BOOK] injected effect read as {doc['verdict']}")
    must(doc["p0"]["status"] == "PREMISE_HOLDS", f"[BOOK] synthetic P0 {doc['p0']['status']}")
    B0 = synthetic(inject=0.0, seed=11)
    doc0 = analyse(B0, workers=4)
    must(not doc0["verdict"].startswith(("PASS", "MECHANISM ONLY")), f"[BOOK] no effect read as {doc0['verdict']}")
    Bv = synthetic(inject=0.012, seed=11, nav_pre_noise_bp=0.0)
    docv = analyse(Bv, workers=4)
    must(docv["p0"]["status"] == "VOID_ERA" and "VOID era" in docv["verdict"], f"[BOOK] void era read {docv['verdict']}")
    P(f"  [7] end to end on synthetic bars: injected -> {doc['verdict']} (G1 t {doc['gates']['G1']['t']:+.2f}); "
      f"none -> {doc0['verdict']} (t {doc0['gates']['G1']['t']:+.2f}); pre-era NAV on the settlement -> {docv['verdict']}")
    # the verdict engine refuses a control that fires
    Gf = json.loads(json.dumps(_clean(doc["gates"])))
    Gf["G2"]["pass"] = False
    must(verdict(Gf) == "FAIL (not the funds)", "[BOOK] a firing placebo did not read FAIL (not the funds)")
    Gi = json.loads(json.dumps(_clean(doc["gates"])))
    Gi["G1"]["t"], Gi["G1"]["pass"] = -2.5, False
    must(verdict(Gi) == "FAIL (inverted)", "[BOOK] t -2.5 did not read FAIL (inverted)")
    P("  [7b] the verdict engine: a firing placebo reads FAIL (not the funds); t -2.5 reads FAIL (inverted)")
    # [9] AMENDMENT A1: G4 compares gold with silver in each one's own sigma units
    rz = np.random.default_rng(91)
    z_si = 0.05 + rz.standard_normal(900) * 0.18
    def audit_g4(rule: Callable[[np.ndarray, np.ndarray], dict[str, Any]]) -> None:
        r_q, r_e = rule(z_si, 0.25 * z_si), rule(z_si, z_si.copy())
        must(bool(r_q["pass"]) and not r_q["fires"], f"[A1] gold at a quarter of silver fired ({r_q})")
        must(bool(r_e["fires"]) and not r_e["pass"], f"[A1] gold equal to silver did not fire ({r_e})")

    audit_g4(g4_rule)
    expect_raise("A1 on a broken rule that never fires",
                 lambda: audit_g4(lambda a, b: {"fires": False, "pass": True}), lines)
    expect_raise("A1 on the superseded rule (gold's t >= 2 fires): it fires at a quarter of silver",
                 lambda: audit_g4(lambda a, b: {"fires": t_ord(b) >= 2, "pass": t_ord(b) < 2}), lines)
    Bq = synthetic(inject=0.012, seed=11, inject_gc=gc_inject_for(0.012, 0.25))
    dq = analyse(Bq, workers=4)
    must(not dq["gates"]["G4"]["fires"] and dq["verdict"].startswith(("PASS", "MECHANISM ONLY")),
         f"[A1] gold at a quarter of silver's effect: {dq['verdict']} / {dq['gates']['G4']}")
    Be = synthetic(inject=0.012, seed=11, inject_gc=gc_inject_for(0.012, 1.0))
    de = analyse(Be, workers=4)
    B2 = synthetic(inject=0.012, seed=11, inject_gc=gc_inject_for(0.012, 2.0))
    d2 = analyse(B2, workers=4)
    must(d2["gates"]["G4"]["fires"] and d2["verdict"] == "FAIL (not the funds)",
         f"[A1] gold at twice silver's effect: {d2['verdict']} / {d2['gates']['G4']}")
    g4q, g4e, g42 = dq["gates"]["G4"], de["gates"]["G4"], d2["gates"]["G4"]
    P(f"  [9] A1 (G4 = gold's post mean in its sigma units >= silver's fires): exact series -- gold at 1/4 of silver "
      f"does not fire, gold equal to silver fires.")
    P(f"      synthetic bars: gold at 1/4 -> {dq['verdict']} (SI {g4q['si_mean_sigma_units']:+.4f}, GC "
      f"{g4q['gc_mean_sigma_units']:+.4f} sigma, GC t {g4q['gc_t']:+.2f}, the superseded t<2 rule would "
      f"{'pass' if g4q['superseded_rule_gc_t_lt_2'] else 'FIRE'}); gold equal in expectation -> {de['verdict']} "
      f"(SI {g4e['si_mean_sigma_units']:+.4f}, GC {g4e['gc_mean_sigma_units']:+.4f}; a coin flip by design, not "
      f"asserted); gold at 2x -> {d2['verdict']} (SI {g42['si_mean_sigma_units']:+.4f}, GC "
      f"{g42['gc_mean_sigma_units']:+.4f})")
    # [8] POWER's engine on the synthetic bundle: beta 0.5 reads PASS/MECHANISM, beta 0 does not; chunk == whole
    Bb = synthetic(inject=0.0, seed=11)
    for R in ROOTS:
        blind_root(Bb[R], R)
    Bb["blind"] = True
    I = power_inputs(Bb)
    po = I["post"]
    ks = rotation_offsets(po["s"].size, ROT_LO)
    Srot = po["s"][(np.arange(po["s"].size)[None, :] - ks[:, None]) % po["s"].size]
    r5 = sim_dataset(I, Srot, 0.5, 9, 0)
    r0 = sim_dataset(I, Srot, 0.0, 9, 0)
    must(r5["full"], f"[BOOK] POWER's engine at beta 0.5 did not read MECHANISM ({r5})")
    must(not r0["full"], f"[BOOK] POWER's engine at beta 0 read MECHANISM ({r0})")
    w = run_power(I, 16, workers=4, chunks=8)
    w1 = run_power(I, 16, workers=1, chunks=1)
    must(json.dumps(_clean(w)) == json.dumps(_clean(w1)), "[EXACT] POWER: 8 strided chunks != the whole")
    expect_raise("POWER's blind on an unblinded bundle", lambda: power_inputs(synthetic(0.0, 11)), lines)
    Bu = synthetic(0.0, 11)
    Bu["blind"] = True                                  # flagged blind, but the prices were never removed
    expect_raise("POWER's [BLIND] price check on a bundle flagged blind with its window prices intact",
                 lambda: power_inputs(Bu), lines)
    P(f"  [8] POWER engine: beta 0.5 -> full reading (t {r5['t']:+.2f}); beta 0 -> not (t {r0['t']:+.2f}); 8 chunks on 4 "
      f"threads == 1 chunk serial; an unblinded bundle RAISES")
    for x in lines:
        P(x)
    P(f"  SELFTEST PASSED in {time.time() - t0:.0f}s")
    return 0


def main(argv: list[str] | None = None) -> int:
    warnings.simplefilter("error", RuntimeWarning)
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--power", action="store_true")
    g.add_argument("--run", action="store_true")
    g.add_argument("--check", action="store_true")
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    ap.add_argument("--workers", type=int, default=None)
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.power:
        return power_main(a.data_root, a.workers)
    return run_main(a.data_root, check=a.check)


if __name__ == "__main__":
    sys.exit(main())
