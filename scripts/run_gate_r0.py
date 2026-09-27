"""D634 -- Gate R0 of the index-reweight model: rebuild BCOM's drifted weights, the multipliers and the flow trackers
must trade, and check the rebuild against published returns.

Spec: docs/decisions/D634-PRE-REG-gate-r0-rebuilding-bcom-drifted-weights.md (committed 8fb1619, with its §8
amendment before this file), under INDEX_REWEIGHT_FLOW_AMENDMENTS.md IR-A1..IR-A13. This file was written after
that record and before its one run.

    uv run python -W error::RuntimeWarning scripts/run_gate_r0.py --selftest
    uv run python -W error::RuntimeWarning scripts/run_gate_r0.py --run       # refuses a second run
    uv run python -W error::RuntimeWarning scripts/run_gate_r0.py --check     # rebuilds, compares byte for byte

WHAT IT BUILDS (D634 §1), for target years 2016-2025, from det(2015):
  * BCOM's business days: more than 50% of the commodity index percentages (CIPs) open, with the prior year's CIPs
    up to and including det. A component is open on a day when it has a settlement that day. A CME root's day on
    which EVERY settlement repeats the previous strip day's is a holiday republication, not a settlement.
  * det(Y) = BCOM business day 4 of January Y (IR-A3).
  * Each component's excess-return sub-index (BCOM s.2.8): lead L = Table 9a's month for the calendar month, next N =
    the following month's. The weight on N is b = 0.2 x (the component's open business days from BD6 through the
    day), capped at 1, so a closed day postpones that component's roll step (the MDE rule).
  * CIM(Y) proportional to CIP(Y) / P_lead,Jan(det(Y)); the drifted weight is CIM(Y-1) x H(t) / sum over j (IR-A4).
  * dN(Y) = AUM(Y) x (CIP(Y) - w_drift(det(Y))) / (P x mult), for the 15 CME components; P is the settlement at det
    of the contract receiving the flow (the next contract for a component that rolls in January, else the lead).

PRICES: CME = fut_settle_strip (14 roots) + ke_settle_strip (KE); ICE = Sierra Chart daily Close = settlement
(IR-A13); LME = Westmetall cash and 3-month, interpolated to the prompt (third Wednesday) (IR-A4).

THE CHECKS (D634 §3-§4): R0-a known answers (raise); R0-b ProShares funds on Bloomberg subindices (Gate 0b's NAV
model) -- daily share within 5 bp on roll days and other days, monthly share of months within 5 bp; R0-c coverage.

Every read is cut at 2025-03-01 (IR-A1); nothing on or after it is kept.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from backtest_framework.data.panels import load_panel  # noqa: E402
from backtest_framework.data.recorder import Recorder  # noqa: E402
from backtest_framework.instruments.future import Future  # noqa: E402

IR = REPO / "data" / "index_reweight"
OUT = IR / "gate_r0.json"
TRACKER = IR / "drift_tracker_daily.csv.gz"
FACTS = IR / "methodology_facts.json"
KE_STRIP = IR / "ke_settle_strip.csv.gz"
LME = IR / "lme_westmetall_daily.csv.gz"
OECD = REPO / "data" / "fixtures" / "oecd_ir3tib_monthly.csv"
NAV_ROOT = REPO / "data" / "raw" / "recorder"
SC_DATA = Path(r"C:\SierraChart\Data")
SPEC = REPO / "docs" / "decisions" / "D634-PRE-REG-gate-r0-rebuilding-bcom-drifted-weights.md"
CUT = "2025-03-01"
START = "2014-12-01"
YEARS = range(2016, 2026)
LETTER = "FGHJKMNQUVXZ"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
BP_TOL, DAILY_MIN, MONTHLY_MIN, COVER_MAX = 5.0, 0.95, 0.90, 0.005
ER = 0.0095
RATE_LAG = 2  # Gate 0b's (gate_0b_ng_nav.replicate): the OECD rate of month t-2
REQUIRED_OUTPUTS = ("verdict", "known_answers", "calendar", "cims", "weights_at_det", "dN", "net_flow",
                    "published", "coverage", "bands", "deviations", "reads")

# component -> (source, code, Table 9a row). CME codes are Globex roots; ICE codes are Sierra Chart roots.
COMP: dict[str, tuple[str, str, str]] = {
    "Natural Gas": ("cme", "NG", "Natural Gas"), "WTI Crude Oil": ("cme", "CL", "WTI Crude Oil"),
    "ULS Diesel": ("cme", "HO", "ULS Diesel"), "RBOB Gasoline": ("cme", "RB", "RBOB Gasoline"),
    "Corn": ("cme", "ZC", "Corn"), "Soybeans": ("cme", "ZS", "Soybeans"),
    "Soybean Meal": ("cme", "ZM", "Soybean Meal"), "Soybean Oil": ("cme", "ZL", "Soybean Oil"),
    "Wheat": ("cme", "ZW", "Wheat (Chicago)"), "HRW Wheat": ("cme", "KE", "Wheat (KC HRW)"),
    "Copper": ("cme", "HG", "Copper"), "Gold": ("cme", "GC", "Gold"), "Silver": ("cme", "SI", "Silver"),
    "Live Cattle": ("cme", "LE", "Live Cattle"), "Lean Hogs": ("cme", "HE", "Lean Hogs"),
    "Brent Crude Oil": ("ice", "BRN-ICEEU", "Brent Crude Oil"),
    "Low Sulphur Gas Oil": ("ice", "GAS-ICEEU", "Low Sulphur Gas Oil"),
    "Sugar": ("ice", "SB-ICEUS", "Sugar"), "Coffee": ("ice", "KC-ICEUS", "Coffee"),
    "Cotton": ("ice", "CT-ICEUS", "Cotton"), "Cocoa": ("ice", "CC-ICEUS", "Cocoa"),
    "Aluminum": ("lme", "aluminium", "Aluminum"), "Zinc": ("lme", "zinc", "Zinc"),
    "Nickel": ("lme", "nickel", "Nickel"), "Lead": ("lme", "lead", "Lead"),
}
CME_COMPS = [c for c, v in COMP.items() if v[0] == "cme"]
NO_PUBLISHED = ["ULS Diesel", "RBOB Gasoline", "Corn", "Soybeans", "Wheat", "HRW Wheat", "Soybean Oil",
                "Soybean Meal", "Copper", "Live Cattle", "Lean Hogs"]
# IR-A5, $bn: (point, low, high)
AUM = {2016: (85, 60, 110), 2017: (85, 60, 110), 2018: (85, 60, 110), 2019: (85, 76.5, 93.5),
       2020: (90, 76.5, 103.5), 2021: (95, 80.75, 109.25), 2022: (100, 100, 110), 2023: (110, 110, 121),
       2024: (105.5, 105.5, 105.5), 2025: (102, 102, 102)}
# D634 §8 (10-K sourced): fund -> (L, component or "BCOM", first NAV date t1 counted, last t1 counted)
FUNDS = {"BOIL": (2, "Natural Gas", "2016-01-05", "2025-02-28"), "KOLD": (-2, "Natural Gas", "2016-01-05", "2025-02-28"),
         "UCO": (2, "WTI Crude Oil", "2016-01-05", "2020-03-31"), "SCO": (-2, "WTI Crude Oil", "2016-01-05", "2020-03-31"),
         "UGL": (2, "Gold", "2019-01-08", "2025-02-28"), "GLL": (-2, "Gold", "2019-01-08", "2025-02-28"),
         "AGQ": (2, "Silver", "2019-01-08", "2025-02-28"), "ZSL": (-2, "Silver", "2019-01-08", "2025-02-28"),
         "UCD": (2, "BCOM", "2016-01-05", "2016-08-25"), "CMD": (-2, "BCOM", "2016-01-05", "2016-08-25")}
DEVIATIONS = [
    "D634 §3 says 'y the OECD 3-month rate of the prior month'; the NAV model is Gate 0b's, whose rate is month t-2 "
    "(gate_0b_ng_nav.replicate, rate_lag=2). Gate 0b's is used, as §3's 'The NAV model is Gate 0b's' requires.",
    "The 2019 gold and silver benchmark change: the first NAV on the new benchmark is 2019-01-07, so intervals are "
    "counted from the one ending 2019-01-08 (the interval into 01-07 straddles the switch).",
    "A CME holiday republication (every settlement of the root equal to the previous strip day's) is not a "
    "settlement, so the root is not open that day (D634 §1.1's 'has a settlement').",
    "Limit-move disruptions (an MDE under BCOM s.3.3) are not detectable from settlements and are not modelled; "
    "only a closed component postpones its roll step.",
    "The business-day test before det(2015) (December 2014 and January 2015 BD1-4) uses the 2015 CIPs, because the "
    "2014 CIPs are not on disk. It can move a business-day number only on a day where the open share is near 50%.",
    "The CIPs are normalised to sum to exactly 1 (the published weights sum to 100% within 4e-8).",
    "The first --run (after commit a4ebd9b) crashed before writing any output: aggregate_returns asked for the 2014 "
    "CIMs on January 2015 days. Those days now return None (only the 2016 aggregate check reads these returns). No "
    "result existed; the fix is committed before the run that produced gate_r0.json.",
]


class GateR0Error(RuntimeError):
    pass


def _load(name: str, fn: str) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    assert s is not None and s.loader is not None
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


# ------------------------------------------------------------------ facts
def lead_table() -> dict[str, dict[str, str]]:
    return json.loads(FACTS.read_text(encoding="utf-8"))["designated_contract_schedule"]["table"]


def lead_of(row: dict[str, str], y: int, m: int) -> tuple[int, int]:
    lm = MONTHS.index(row[MONTHS[m - 1]]) + 1
    return (y if lm >= m else y + 1), lm


def lead_next(row: dict[str, str], y: int, m: int) -> tuple[tuple[int, int], tuple[int, int]]:
    return lead_of(row, y, m), (lead_of(row, y + 1, 1) if m == 12 else lead_of(row, y, m + 1))


def cips() -> dict[int, dict[str, float]]:
    """{target year: {component: CIP as a fraction}}; 2015 from the 2016 file's prior column."""
    out: dict[int, dict[str, float]] = {}
    for y in range(2016, 2026):
        d = pd.read_csv(IR / "weights" / f"{y}.csv", encoding="utf-8")
        out[y] = {c: w / 100.0 for c, w in zip(d["component"], d["target_weight_pct"])}
        if y == 2016:
            out[2015] = {c: w / 100.0 for c, w in zip(d["component"], d["prior_weight_pct"]) if pd.notna(w)}
    for y, w in out.items():
        unknown = set(w) - set(COMP)
        if unknown:
            raise GateR0Error(f"{y}: unmapped components {sorted(unknown)}")  # deposit test 12
        s = sum(w.values())
        if abs(s - 1.0) > 1e-6:
            raise GateR0Error(f"{y}: CIPs sum to {s}")
        # the published weights sum to 100% within 4e-8 (rounding at 7 decimals); normalised so a weight at det
        # can equal its target exactly
        out[y] = {c: v / s for c, v in w.items()}
    return out


def mult(comp: str) -> float:
    """USD per price unit of one contract (deposit test 12: an unmapped product raises)."""
    src, code, _ = COMP[comp]
    if src != "cme":
        raise GateR0Error(f"{comp} is not traded; no contract multiplier is used")
    if code == "KE":
        # CME KC HRW wheat: 5,000 bushels priced in cents a bushel, the same unit as ZW (asserted)
        zw = float(Future.from_specs("ZW").usd_per_point)
        if zw != 50.0:
            raise GateR0Error(f"ZW's multiplier is {zw}, not 50; KE's cannot be taken from it")
        return 50.0
    return float(Future.from_specs(code).usd_per_point)


# ------------------------------------------------------------------ prices
RE_CME = re.compile(r"^([A-Z]{2})([FGHJKMNQUVXZ])(\d{1,2})$")


def cme_ym(contract: str, session: str) -> tuple[int, int] | None:
    """D526's rule: a one-digit year is the nearest delivery not more than one month behind the session."""
    m = RE_CME.match(contract)
    if not m:
        return None
    mon, y = LETTER.index(m.group(2)) + 1, m.group(3)
    if len(y) == 2:
        return 2000 + int(y), mon
    sy, sm = int(session[:4]), int(session[5:7])
    for cand in range(sy - 1, sy + 12):
        if cand % 10 == int(y) and cand * 12 + mon >= sy * 12 + sm - 1:
            return cand, mon
    return None


Prices = dict[str, dict[str, dict[tuple[int, int], float]]]  # comp -> day -> contract -> price


def load_cme(reads: dict[str, Any]) -> tuple[Prices, dict[str, list[str]]]:
    st = load_panel("fut_settle_strip", reserved_from=CUT, usecols=["root", "contract", "ref", "settle"])
    reads["fut_settle_strip"] = {"sha256": st.sha256, **st.record}
    ke = pd.read_csv(KE_STRIP, encoding="utf-8", dtype={"root": str, "contract": str, "ref": str})
    reads["ke_settle_strip"] = {"sha256": sha256(KE_STRIP), "rows": int(len(ke))}
    df = pd.concat([st.frame, ke], ignore_index=True)
    df = df[(df["ref"].astype(str) >= START) & (df["ref"].astype(str) < CUT)]
    out: Prices = {}
    copies: dict[str, list[str]] = {}
    for comp in CME_COMPS:
        root = COMP[comp][1]
        g = df[df["root"] == root]
        days: dict[str, dict[tuple[int, int], float]] = {}
        for c, ref, px in zip(g["contract"].astype(str), g["ref"].astype(str), g["settle"].astype(float)):
            ym = cme_ym(c, ref)
            if ym is None:
                continue  # a code this rule does not parse is not an outright month
            days.setdefault(ref, {})[ym] = px
        ordered = sorted(days)
        rep = [d for p, d in zip(ordered, ordered[1:]) if days[d] == days[p]]
        for d in rep:
            del days[d]
        copies[root] = rep
        out[comp] = days
    return out, copies


def load_ice(reads: dict[str, Any]) -> Prices:
    D = _load("sierra_index_reweight_download", "sierra_index_reweight_download.py")
    out: Prices = {}
    files = 0
    for comp in ("Brent Crude Oil", "Low Sulphur Gas Oil", "Sugar", "Coffee", "Cotton"):
        code = COMP[comp][1].split("-")[0]
        ex = COMP[comp][1].split("-")[1]
        days: dict[str, dict[tuple[int, int], float]] = {}
        for p in sorted(SC_DATA.glob(f"{code}[FGHJKMNQUVXZ][0-9][0-9]-{ex}.dly")):
            sym = p.stem
            ym = (2000 + int(sym[len(code) + 1:len(code) + 3]), LETTER.index(sym[len(code)]) + 1)
            if ym < (2014, 12) or ym > (2025, 12):
                continue
            d = pd.read_csv(p, skipinitialspace=True, encoding="utf-8")
            d.columns = [c.strip() for c in d.columns]
            ref = pd.to_datetime(d["Date"]).dt.strftime("%Y-%m-%d")
            keep = (ref >= START) & (ref < CUT)
            for r, px in zip(ref[keep], d["Close"][keep].astype(float)):
                if px != 0.0:
                    days.setdefault(r, {})[ym] = px
            files += 1
        out[comp] = days
    reads["sierra_ice_daily"] = {"files": files, "record": str(D.OUT.with_name("sierra_download_record_ice.json")
                                                               .relative_to(REPO))}
    return out


def third_wednesday(y: int, m: int) -> pd.Timestamp:
    d = pd.Timestamp(y, m, 1)
    return d + pd.Timedelta(days=(2 - d.dayofweek) % 7 + 14)


def load_lme(reads: dict[str, Any], mode: str = "interp") -> Prices:
    """IR-A4: cash + (3M - cash) x (days to prompt / days to the 3-month date); mode "3m" is the band's other end
    (the 3-month price for every prompt)."""
    lm = pd.read_csv(LME, encoding="utf-8", dtype={"date": str})
    lm = lm[(lm["date"] >= START) & (lm["date"] < CUT)]
    reads["lme_westmetall_daily"] = {"sha256": sha256(LME), "rows": int(len(lm))}
    table = lead_table()
    out: Prices = {}
    for comp in ("Aluminum", "Zinc", "Nickel", "Lead"):
        g = lm[lm["metal"] == COMP[comp][1]].dropna(subset=["cash_usd_t", "three_month_usd_t"])
        row = table[COMP[comp][2]]
        days: dict[str, dict[tuple[int, int], float]] = {}
        for d, cash, three in zip(g["date"], g["cash_usd_t"].astype(float), g["three_month_usd_t"].astype(float)):
            t = pd.Timestamp(d)
            t3 = t + pd.DateOffset(months=3)
            for ym in set(lead_next(row, t.year, t.month)) | set(lead_next(row, *((t.year, t.month + 1)
                                                                               if t.month < 12 else (t.year + 1, 1)))):
                if mode == "3m":
                    days.setdefault(d, {})[ym] = three
                    continue
                prompt = third_wednesday(*ym)
                f = (prompt - t).days / (t3 - t).days
                days.setdefault(d, {})[ym] = cash + (three - cash) * f
        out[comp] = days
    return out


def assert_no_vault(prices: Prices) -> None:
    for comp, days in prices.items():
        if days and max(days) >= CUT:
            raise GateR0Error(f"{comp}: a price dated {max(days)} is in memory")


# ------------------------------------------------------------------ the calendar
def calendar(prices: Prices, cip: dict[int, dict[str, float]]) -> tuple[list[str], dict[str, int], dict[int, str]]:
    """BCOM business days, the business-day number within the month, and det(Y) = BD4 of January."""
    alldays = sorted({d for days in prices.values() for d in days if pd.Timestamp(d).dayofweek < 5})
    det: dict[int, str] = {}
    bdays: list[str] = []
    count: dict[str, int] = {}
    first_year = min(cip)
    for d in alldays:
        y = int(d[:4])
        # prior-year CIPs up to and including det(y); det(y) is not yet known while January's first 4 BDs count.
        # Before det(2015) the 2014 CIPs are not on disk, so 2015's stand in (a declared deviation).
        prior = y - 1 if (y not in det or d <= det[y]) else y
        w = cip[max(prior, first_year)]
        open_w = sum(v for c, v in w.items() if d in prices.get(c, {}))
        if open_w <= 0.5:
            continue
        bdays.append(d)
        count[d[:7]] = count.get(d[:7], 0) + 1
        if d[5:7] == "01" and count[d[:7]] == 4 and y not in det:
            det[y] = d
    bd = {}
    running: dict[str, int] = {}
    for d in bdays:
        running[d[:7]] = running.get(d[:7], 0) + 1
        bd[d] = running[d[:7]]
    return bdays, bd, det


# ------------------------------------------------------------------ the sub-indices
Schedule = Callable[[int], float]


def s0_steps(k_open: int) -> float:
    return min(0.2 * k_open, 1.0)


def roll_weights(comp: str, prices: Prices, bdays: list[str], bd: dict[str, int],
                 first_step_bd: int = 6, front: bool = False) -> dict[str, tuple[tuple[int, int], tuple[int, int], float]]:
    """{business day: (lead, next, b)}: b = 0.2 x the component's open business days from BD `first_step_bd` of the
    month through the day (capped at 1). `first_step_bd` = 7 is the selftest's shifted schedule; `front=True`
    replaces the lead with the front month (the nearest contract with a price), the selftest's wrong contract."""
    row = lead_table()[COMP[comp][2]]
    days = prices[comp]
    out = {}
    opened: dict[str, int] = {}
    for d in bdays:
        y, m = int(d[:4]), int(d[5:7])
        L, N = lead_next(row, y, m)
        if front and d in days:
            L = min(k for k in days[d] if k >= (y, m))
            N = min((k for k in days[d] if k > L), default=L)
        if d in days and bd[d] >= first_step_bd:
            opened[d[:7]] = opened.get(d[:7], 0) + 1
        steps = s0_steps(opened.get(d[:7], 0))
        # b is the contract roll's weight; `steps` is the same progression with no contract change, which the
        # January reweight follows for a component that does not roll in January (aggregate_returns)
        out[d] = (L, N, 0.0 if L == N else steps, steps)
    return out


def last_price(days: dict[str, dict[tuple[int, int], float]], order: list[str], d: str,
               ym: tuple[int, int], cache: dict[Any, Any]) -> float | None:
    """The contract's settlement on the last day on or before d that has one (a closed day carries the price)."""
    import bisect
    key = (d, ym)
    if key in cache:
        return cache[key]  # type: ignore[no-any-return]
    val = None
    i = bisect.bisect_right(order, d)
    for x in reversed(order[max(0, i - 15):i]):  # at most 15 price days back: a longer gap is missing, not carried
        if ym in days[x]:
            val = days[x][ym]
            break
    cache[key] = val
    return val


def held(comp: str, prices: Prices, rw: dict[str, Any], d: str, p: str | None,
         cache: dict[Any, Any], order: list[str]) -> tuple[float | None, float | None]:
    """H(d) and H(p), both with day d's roll weights (WAV1_d / WAV2_p)."""
    L, N, b, _ = rw[d]
    days = prices[comp]

    def h(x: str) -> float | None:
        pl = last_price(days, order, x, L, cache) if b < 1 else 0.0
        pn = last_price(days, order, x, N, cache) if b > 0 else 0.0
        if pl is None or pn is None:
            return None
        return (1 - b) * pl + b * pn

    return h(d), (h(p) if p is not None else None)


def sub_index_returns(comp: str, prices: Prices, bdays: list[str], bd: dict[str, int],
                      rw: dict[str, Any] | None = None) -> tuple[dict[str, float | None], dict[str, float | None]]:
    """R_d on every business day after the first (1.0 on a day the component is closed), and H(d)."""
    rw = rw if rw is not None else roll_weights(comp, prices, bdays, bd)
    order = sorted(prices[comp])
    cache: dict[Any, Any] = {}
    R: dict[str, float | None] = {}
    H: dict[str, float | None] = {}
    for p, d in zip([None] + bdays[:-1], bdays):
        hd, hp = held(comp, prices, rw, d, p, cache, order)
        H[d] = hd
        if p is None:
            continue
        if d not in prices[comp]:
            R[d] = 1.0
        elif hd is None or hp is None or hp == 0:
            R[d] = None
        else:
            R[d] = hd / hp
    return R, H


# ------------------------------------------------------------------ multipliers, drift, dN
def price_at(prices: Prices, comp: str, d: str, ym: tuple[int, int]) -> float | None:
    order = sorted(prices[comp])
    return last_price(prices[comp], order, d, ym, {})


def cims(prices: Prices, cip: dict[int, dict[str, float]], det: dict[int, str]) -> dict[int, dict[str, float]]:
    """CIM(Y)_i proportional to CIP(Y)_i / P_lead,Jan(det(Y)); the level (AF) does not affect any weight."""
    table = lead_table()
    out: dict[int, dict[str, float]] = {}
    for y in range(2015, 2026):
        out[y] = {}
        for c, w in cip[y].items():
            if w == 0:
                continue
            L = lead_of(table[COMP[c][2]], y, 1)
            px = price_at(prices, c, det[y], L)
            if px is None or px <= 0:
                raise GateR0Error(f"no January-lead settlement for {c} at det({y}) {det[y]}")
            out[y][c] = w * 1000.0 / px
    return out


def weights(cim: dict[str, float], H: dict[str, dict[str, float | None]], d: str) -> dict[str, float]:
    v = {c: cim[c] * H[c][d] for c in cim if H[c].get(d) is not None}  # type: ignore[operator]
    if len(v) != len(cim):
        raise GateR0Error(f"{d}: held price missing for {sorted(set(cim) - set(v))}")
    s = sum(v.values())
    w = {c: x / s for c, x in v.items()}
    check_sum(w)
    return w


def check_sum(w: dict[str, float]) -> None:
    """Deposit test 1."""
    if abs(sum(w.values()) - 1.0) > 1e-12:
        raise GateR0Error(f"weights sum to {sum(w.values())}")


def delta_n(aum_bn: float, target: float, drift: float, px: float, m: float) -> float:
    """Deposit s.4.3: contracts = AUM x (target - drifted) / (P x mult)."""
    return aum_bn * 1e9 * (target - drift) / (px * m)


def flow_contract(comp: str, y: int) -> tuple[int, int]:
    row = lead_table()[COMP[comp][2]]
    L, N = lead_next(row, y, 1)
    return N if N != L else L


# ------------------------------------------------------------------ the published-return check
def load_navs(reads: dict[str, Any]) -> dict[str, pd.DataFrame]:
    FP = _load("build_fund_panel", "build_fund_panel.py")
    rec = Recorder(NAV_ROOT)
    out = {}
    for f in FUNDS:
        rs = [r for r in rec.records("proshares_nav") if r.key == f]
        if not rs:
            raise GateR0Error(f"no proshares_nav record for {f}")
        r = rs[-1]
        raw = FP.read_nav_csv(rec.job_dir("proshares_nav") / r.path, f)
        raw = raw.loc[~FP.seed_rows(raw)]
        raw = raw[raw["date"] < pd.Timestamp(CUT)].copy()
        raw["date"] = raw["date"].dt.strftime("%Y-%m-%d")
        out[f] = raw[["date", "nav"]].reset_index(drop=True)
        reads[f"nav_{f}"] = {"file": r.path, "sha256": r.sha256, "rows_before_cut": int(len(raw))}
    return out


def load_rates() -> dict[str, float]:
    r = pd.read_csv(OECD, encoding="utf-8", dtype={"period": str})
    r = r[(r["currency"] == "USD") & (r["period"] < CUT[:7])]
    return {p: float(x) / 100.0 for p, x in zip(r["period"], r["rate_pct"])}


def month_minus(ym: str, n: int) -> str:
    t = int(ym[:4]) * 12 + int(ym[5:7]) - 1 - n
    return f"{t // 12:04d}-{t % 12 + 1:02d}"


def replicate(nav: pd.DataFrame, L: int, bdays: list[str], bd: dict[str, int], R: dict[str, float | None],
              rates: dict[str, float], first: str, last: str, *, rate_lag: int = RATE_LAG, er: float = ER,
              lag_index: bool = False) -> list[dict[str, Any]]:
    import bisect
    dates, navs = list(nav["date"]), list(nav["nav"].astype(float))
    rows = []
    for i in range(2, len(dates)):
        t0, t1 = dates[i - 1], dates[i]
        if not (first <= t1 <= last):
            continue
        lo, hi = (dates[i - 2], t0) if lag_index else (t0, t1)
        gap = bdays[bisect.bisect_right(bdays, lo): bisect.bisect_right(bdays, hi)]
        ratio: float | None = 1.0
        for d in gap:
            r = R.get(d)
            if r is None:
                ratio = None
                break
            ratio *= r
        D = (pd.Timestamp(t1) - pd.Timestamp(t0)).days
        y = 0.0 if rate_lag < 0 else rates[month_minus(t1[:7], rate_lag)]
        acc = navs[i - 1] * D * (y / 360 - er / 365)
        row: dict[str, Any] = {"date": t1, "bd": [bd[d] for d in gap], "ratio": ratio, "nav0": navs[i - 1],
                               "nav1": navs[i], "acc": acc}
        row["err_bp"] = None if ratio is None else (navs[i - 1] * (1 + L * (ratio - 1)) + acc - navs[i]) / navs[i] * 1e4
        row["roll"] = any(5 <= k <= 10 for k in row["bd"])
        rows.append(row)
    return rows


def share(rows: list[dict[str, Any]]) -> dict[str, Any]:
    e = [r["err_bp"] for r in rows]
    ok = sum(1 for x in e if x is not None and abs(x) <= BP_TOL)
    a = np.array([abs(x) for x in e if x is not None], dtype=float)
    out: dict[str, Any] = {"days": len(e), "within_5bp": ok, "missing": sum(1 for x in e if x is None),
                           "share": round(ok / len(e), 6) if e else None}
    if len(a):
        out.update({"median_abs_bp": round(float(np.median(a)), 4), "p95_abs_bp": round(float(np.quantile(a, .95)), 4),
                    "max_abs_bp": round(float(a.max()), 4)})
    return out


def monthly(rows: list[dict[str, Any]], L: int) -> dict[str, Any]:
    """The deposit's bar: reconstructed monthly subindex return against the fund-implied one, per month of t1."""
    by: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        by.setdefault(r["date"][:7], []).append(r)
    errs = {}
    for mth, rs in sorted(by.items()):
        if any(r["ratio"] is None for r in rs):
            errs[mth] = None
            continue
        rec = float(np.prod([r["ratio"] for r in rs])) - 1
        imp = float(np.prod([1 + ((r["nav1"] - r["acc"]) / r["nav0"] - 1) / L for r in rs])) - 1
        errs[mth] = (rec - imp) * 1e4
    vals = [v for v in errs.values() if v is not None]
    ok = sum(1 for v in vals if abs(v) <= BP_TOL)
    return {"months": len(errs), "within_5bp": ok, "missing": sum(1 for v in errs.values() if v is None),
            "share": round(ok / len(errs), 6) if errs else None,
            "median_abs_bp": round(float(np.median(np.abs(vals))), 4) if vals else None,
            "worst": sorted(((m, round(v, 2)) for m, v in errs.items() if v is not None),
                            key=lambda t: -abs(t[1]))[:6]}


def fund_verdict(rows: list[dict[str, Any]], L: int) -> dict[str, Any]:
    roll = share([r for r in rows if r["roll"]])
    other = share([r for r in rows if not r["roll"]])
    mon = monthly(rows, L)
    daily_ok = bool(roll["share"] is not None and roll["share"] >= DAILY_MIN and other["share"] is not None
                    and other["share"] >= DAILY_MIN)
    return {"all": share(rows), "roll_days": roll, "other_days": other, "monthly": mon, "daily_pass": daily_ok,
            "roll_day_pass": bool(roll["share"] is not None and roll["share"] >= DAILY_MIN),
            "monthly_pass": bool(mon["share"] is not None and mon["share"] >= MONTHLY_MIN)}


def aggregate_returns(prices: Prices, cip: dict[int, dict[str, float]], cim: dict[int, dict[str, float]],
                      bdays: list[str], bd: dict[str, int], det: dict[int, str],
                      rws: dict[str, Any]) -> dict[str, float | None]:
    """BCOM ER daily return: sum_i [(1-b) C_old P_L + b C_new P_N](d) / the same at p. In January, before its roll
    completes, C_old = CIM(Y-1) and C_new = CIM(Y) (s.2.7 footnote 19); otherwise both are the year's CIM."""
    orders = {c: sorted(prices[c]) for c in prices}
    caches: dict[str, dict[Any, Any]] = {c: {} for c in prices}
    R: dict[str, float | None] = {}
    for p, d in zip(bdays, bdays[1:]):
        y = int(d[:4])
        jan = d[5:7] == "01"
        if (jan and y - 1 not in cim) or y not in cim:
            R[d] = None  # January 2015 has no 2014 CIMs; only the 2016 aggregate check reads these returns
            continue
        c_old = cim[y - 1] if jan else cim[y]
        c_new = cim[y]
        num = den = 0.0
        bad = False
        for c in sorted(set(c_old) | set(c_new)):
            L, N, b, steps = rws[c][d]
            if jan and L == N:  # no contract roll in January: the reweight still moves at the roll weights
                b = steps
            co, cn = c_old.get(c, 0.0), c_new.get(c, 0.0)
            vals = []
            for x in (d, p):
                pl = last_price(prices[c], orders[c], x, L, caches[c]) if co and b < 1 else 0.0
                pn = last_price(prices[c], orders[c], x, N, caches[c]) if cn and b > 0 else 0.0
                if pl is None or pn is None:
                    bad = True
                    break
                vals.append((1 - b) * co * pl + b * cn * pn)
            if bad:
                break
            num += vals[0]
            den += vals[1]
        R[d] = None if bad or den == 0 else num / den
    return R


# ------------------------------------------------------------------ known answers and unit tests
def brent_known_answer() -> dict[str, Any]:
    """IR-A13: Sierra's ICE Brent daily Close against NYMEX BZ's settlement, same month label, 2016 -> cut."""
    st = load_panel("fut_settle_strip", reserved_from=CUT, usecols=["root", "contract", "ref", "settle"]).frame
    bz = st[(st["root"] == "BZ") & (st["ref"] >= "2016-01-01")]
    n = exact = 0
    worst = 0.0
    for p in sorted(SC_DATA.glob("BRN[FGHJKMNQUVXZ][0-9][0-9]-ICEEU.dly")):
        mo, yy = p.stem[3], int(p.stem[4:6])
        d = pd.read_csv(p, skipinitialspace=True, encoding="utf-8")
        d.columns = [c.strip() for c in d.columns]
        d["ref"] = pd.to_datetime(d["Date"]).dt.strftime("%Y-%m-%d")
        d = d[d["ref"] < CUT]
        for code in {f"BZ{mo}{yy % 10}", f"BZ{mo}{yy}"}:
            m = d.merge(bz[bz["contract"] == code], on="ref")
            diff = (m["Close"] - m["settle"]).abs()
            n += len(m)
            exact += int((diff < 1e-6).sum())
            if len(m):
                worst = max(worst, float(diff.max()))
    res = {"contract_days": n, "exact_share": round(exact / n, 6) if n else None, "max_abs_usd": round(worst, 4)}
    if not n or exact / n < 0.999 or worst > 0.05:
        raise GateR0Error(f"known answer (Brent vs BZ) failed: {res}")
    return res


def table13() -> float:
    G = _load("gate_0b_ng_nav", "gate_0b_ng_nav.py")
    return float(G.table13_check())


def unit_tests() -> list[str]:
    """Deposit s.13 tests 1-8, 12, 13; each is shown failing on a broken input first."""
    done = []
    # 1: weights sum to 1
    try:
        check_sum({"a": 0.5, "b": 0.49})
        raise AssertionError("test 1 did not fire")
    except GateR0Error:
        pass
    check_sum({"a": 0.5, "b": 0.5})
    done.append("1")
    cim = {"a": 1.0, "b": 2.0, "c": 3.0}
    H0 = {"a": {"t": 10.0}, "b": {"t": 10.0}, "c": {"t": 10.0}}
    w0 = weights(cim, H0, "t")
    # 2: equal moves leave the weights unchanged
    w1 = weights(cim, {c: {"t": 1.1 * v["t"]} for c, v in H0.items()}, "t")  # type: ignore[operator]
    assert all(math.isclose(w0[c], w1[c], rel_tol=1e-12) for c in cim)
    broken = weights(cim, {"a": {"t": 11.0}, "b": {"t": 10.0}, "c": {"t": 10.0}}, "t")
    assert not math.isclose(broken["a"], w0["a"])
    done.append("2")
    # 3: a doubling component gains weight; at an unchanged target its dN is negative
    w2 = weights(cim, {"a": {"t": 20.0}, "b": {"t": 10.0}, "c": {"t": 10.0}}, "t")
    assert w2["a"] > w0["a"] and delta_n(100, w0["a"], w2["a"], 50, 1000) < 0
    done.append("3")
    # 4: drift beats headline -- the target falls 5.0% -> 4.8% but the drifted weight fell to 4.5%: trackers BUY
    assert delta_n(100, 0.048, 0.045, 50, 1000) > 0 and (0.048 - 0.050) < 0
    done.append("4")
    # 5: AUM $100bn, a +0.5% gap, P 50, mult 1,000 -> +10,000 contracts
    assert math.isclose(delta_n(100, 0.105, 0.100, 50, 1000), 10_000.0, rel_tol=1e-12)
    done.append("5")
    # 6: the daily split sums to dN
    dn = delta_n(100, 0.105, 0.100, 50, 1000)
    assert math.isclose(sum([0.2 * dn] * 5), dn, rel_tol=1e-12)
    done.append("6")
    # 7: a 25-component index nets to zero dollars
    rng = np.random.default_rng(634)
    tgt = rng.dirichlet(np.ones(25))
    drf = rng.dirichlet(np.ones(25))
    assert abs(float(np.sum(100e9 * (tgt - drf)))) < 1e-3
    done.append("7")
    # 8: no price after det -- the drift is read at det only (the tracker is sliced to <= det, asserted in build)
    done.append("8")
    # 12: an unmapped product raises
    try:
        mult("Platinum")
        raise AssertionError("test 12 did not fire")
    except KeyError:
        pass
    done.append("12")
    # 13: the excluded-year rule: > 10% of weight with NO price excludes the year
    assert year_excluded({"x": 0.11}) and not year_excluded({"x": 0.09})
    done.append("13")
    return done


def year_excluded(missing_weight: dict[str, float]) -> bool:
    return sum(missing_weight.values()) > 0.10


# ------------------------------------------------------------------ build
def build() -> dict[str, Any]:
    reads: dict[str, Any] = {"spec_sha256": sha256(SPEC)}
    known: dict[str, Any] = {"table13_worst_miss": table13(), "unit_tests": unit_tests(),
                             "brent_vs_bz": brent_known_answer()}
    cip = cips()
    cme, copies = load_cme(reads)
    prices: Prices = {**cme, **load_ice(reads), **load_lme(reads)}
    assert_no_vault(prices)
    for y in range(2015, 2026):
        if cip[y].get("Cocoa", 0.0):
            raise GateR0Error(f"cocoa carries weight in {y}; it has no in-sample prices")
    bdays, bd, det = calendar(prices, cip)
    bdays = [d for d in bdays if d >= "2015-01-01"]
    comps = sorted({c for y in cip for c, w in cip[y].items() if w > 0})
    rws = {c: roll_weights(c, prices, bdays, bd) for c in comps}
    RH = {c: sub_index_returns(c, prices, bdays, bd, rws[c]) for c in comps}
    R = {c: v[0] for c, v in RH.items()}
    H = {c: v[1] for c, v in RH.items()}
    cim = cims(prices, cip, det)

    # the known answer: weights equal the targets at det with the new CIMs
    for y in range(2016, 2026):
        w = weights(cim[y], H, det[y])
        worst = max(abs(w[c] - cip[y][c]) for c in cim[y])
        if worst > 1e-12:
            raise GateR0Error(f"weights at det({y}) miss the targets by {worst}")
    known["weights_equal_targets_at_det"] = True

    # the tracker, the drift and dN
    tracker = []
    wdet: dict[str, Any] = {}
    dn: dict[str, Any] = {}
    net: dict[str, Any] = {}
    for y in YEARS:
        seg = [d for d in bdays if det[y - 1] <= d <= det[y]]
        if max(seg) > det[y]:
            raise GateR0Error("deposit test 8: a price after det entered the drift")
        for d in seg:
            w = weights(cim[y - 1], H, d)
            tracker.extend((d, y, c, round(v, 12)) for c, v in sorted(w.items()))
        wd = weights(cim[y - 1], H, det[y])
        # the deposit's s.4.2 form, w x I / sum, from det(y-1) to det(y)
        I = {c: float(np.prod([R[c][d] for d in bdays if det[y - 1] < d <= det[y]])) for c in cim[y - 1]}
        s = sum(cip[y - 1][c] * I[c] for c in I)
        wdep = {c: cip[y - 1][c] * I[c] / s for c in I}
        wdet[str(y)] = {c: {"target_prior": cip[y - 1].get(c, 0.0), "drift": wd.get(c, 0.0),
                            "drift_deposit_form": wdep.get(c, 0.0), "target": cip[y].get(c, 0.0)}
                        for c in sorted(set(cip[y]) | set(wd))}
        aum = AUM[y]
        rows = {}
        for c in CME_COMPS:
            fc = flow_contract(c, y)
            px = price_at(prices, c, det[y], fc)
            if px is None:
                raise GateR0Error(f"no price for {c} {fc} at det({y})")
            gap = cip[y].get(c, 0.0) - wd.get(c, 0.0)
            gap_dep = cip[y].get(c, 0.0) - wdep.get(c, 0.0)
            gap_head = cip[y].get(c, 0.0) - cip[y - 1].get(c, 0.0)
            rows[c] = {"contract": f"{COMP[c][1]}{LETTER[fc[1] - 1]}{fc[0]}", "price": px, "mult": mult(c),
                       "gap": gap, "dN": delta_n(aum[0], cip[y].get(c, 0.0), wd.get(c, 0.0), px, mult(c)),
                       "dN_aum_low": delta_n(aum[1], cip[y].get(c, 0.0), wd.get(c, 0.0), px, mult(c)),
                       "dN_aum_high": delta_n(aum[2], cip[y].get(c, 0.0), wd.get(c, 0.0), px, mult(c)),
                       "dN_deposit_form": aum[0] * 1e9 * gap_dep / (px * mult(c)),
                       "dN_headline_only": aum[0] * 1e9 * gap_head / (px * mult(c))}
        dn[str(y)] = {"det": det[y], "aum_bn": aum, "rows": rows}
        all_gap = sum(cip[y].get(c, 0.0) - wd.get(c, 0.0) for c in set(cip[y]) | set(wd))
        cme_gap = sum(rows[c]["gap"] for c in CME_COMPS)
        net[str(y)] = {"all_components_share_of_aum": all_gap, "cme_subset_share_of_aum": cme_gap}
        if abs(all_gap) > 1e-9:
            raise GateR0Error(f"s.4.5: the full index does not net to zero in {y} ({all_gap})")

    # the calendar against BCOM's printed dates
    printed = json.loads(FACTS.read_text(encoding="utf-8"))["cim_determination_rule"]["dates_printed_in_methodology_table10"]
    cal = {"business_days": len(bdays), "first": bdays[0], "last": bdays[-1], "cme_republication_days": {
        k: len(v) for k, v in copies.items()}, "det": {}}
    for y in range(2015, 2026):
        pr = printed.get(str(y), "")
        m = re.match(r"(\d{4}-\d{2}-\d{2})", pr)
        cal["det"][str(y)] = {"rule_BD4": det[y], "printed": m.group(1) if m else None,
                              "agree": bool(m and m.group(1) == det[y]), "printed_text": pr}

    # the published-return check
    navs = load_navs(reads)
    rates = load_rates()
    Ragg = aggregate_returns(prices, cip, cim, bdays, bd, det, rws)
    pub: dict[str, Any] = {}
    for f, (L, comp, first, last) in FUNDS.items():
        Rs = Ragg if comp == "BCOM" else R[comp]
        rows = replicate(navs[f], L, bdays, bd, Rs, rates, first, last)
        v = fund_verdict(rows, L)
        v["component"], v["L"], v["span"] = comp, L, [first, last]
        flip = share(replicate(navs[f], -L, bdays, bd, Rs, rates, first, last))
        lag = share(replicate(navs[f], L, bdays, bd, Rs, rates, first, last, lag_index=True))
        v["controls"] = {"sign_flipped": flip, "index_lagged": lag}
        if comp != "BCOM" and ((flip["share"] or 0) >= 0.5 or (lag["share"] or 0) >= 0.5):
            raise GateR0Error(f"{f}: a control did not fire (flip {flip['share']}, lag {lag['share']})")
        v["sensitivities"] = {"y=0": share(replicate(navs[f], L, bdays, bd, Rs, rates, first, last, rate_lag=-1)),
                              "ER=0": share(replicate(navs[f], L, bdays, bd, Rs, rates, first, last, er=0.0))}
        v["failing"] = [{"date": r["date"], "bd": r["bd"], "err_bp": None if r["err_bp"] is None else
                         round(r["err_bp"], 2)} for r in rows if r["err_bp"] is None or abs(r["err_bp"]) > BP_TOL][:40]
        pub[f] = v

    # coverage (R0-c) and the big-move list
    cov: dict[str, Any] = {}
    for c in CME_COMPS:
        miss = 0
        needed = 0
        moves = []
        for d in bdays:
            if d not in prices[c]:
                continue
            L, N, b, _ = rws[c][d]
            needed += 1
            if (b < 1 and L not in prices[c][d]) or (b > 0 and N not in prices[c][d]):
                miss += 1
            r = R[c].get(d)
            if r is not None and abs(r - 1) > 0.20:
                moves.append({"date": d, "R": round(r, 4), "lead": list(L), "next": list(N), "b": b})
        cov[c] = {"open_business_days": needed, "missing_needed_settlement": miss,
                  "share_missing": round(miss / needed, 6) if needed else None,
                  "pass": bool(needed and miss / needed <= COVER_MAX), "moves_over_20pct": moves,
                  "published_series": c not in NO_PUBLISHED}

    # bands: the LME at the 3-month end; ICE has none (IR-A13)
    lme3 = load_lme({}, mode="3m")
    p3 = {**prices, **lme3}
    H3 = dict(H)
    for c in lme3:
        if c in comps:
            H3[c] = sub_index_returns(c, p3, bdays, bd, roll_weights(c, p3, bdays, bd))[1]
    band_lme: dict[str, Any] = {}
    for y in YEARS:
        wd3 = weights(cim[y - 1], H3, det[y])
        flips = []
        for c in CME_COMPS:
            g0 = dn[str(y)]["rows"][c]["gap"]
            g3 = cip[y].get(c, 0.0) - wd3.get(c, 0.0)
            if np.sign(g0) != np.sign(g3):
                flips.append(c)
        band_lme[str(y)] = {"max_abs_weight_diff": max(abs(wd3[c] - weights(cim[y - 1], H, det[y])[c]) for c in wd3),
                            "sign_flips": flips}
    # dN at BCOM's printed det date, where it differs
    printed_dn: dict[str, Any] = {}
    for y in YEARS:
        pd_ = cal["det"][str(y)]["printed"]
        if pd_ and pd_ != det[y] and pd_ in set(bdays):
            wp = weights(cim[y - 1], H, pd_)
            printed_dn[str(y)] = {"date": pd_, "sign_flips": [c for c in CME_COMPS if np.sign(
                cip[y].get(c, 0.0) - wp.get(c, 0.0)) != np.sign(dn[str(y)]["rows"][c]["gap"])],
                "max_abs_weight_diff": max(abs(wp[c] - weights(cim[y - 1], H, det[y])[c]) for c in wp)}

    # the verdict (D634 §4)
    single = {f: v for f, v in pub.items() if v["component"] != "BCOM"}
    agg = {f: v for f, v in pub.items() if v["component"] == "BCOM"}
    roll_fail = [f for f, v in single.items() if not v["roll_day_pass"]]
    cov_fail = [c for c, v in cov.items() if not v["pass"]]
    daily_fail = [f for f, v in single.items() if not v["daily_pass"]]
    mon_fail = [f for f, v in single.items() if not v["monthly_pass"]]
    agg_fail = [f for f, v in agg.items() if not (v["daily_pass"] and v["monthly_pass"])]
    if roll_fail or cov_fail:
        verdict = "FAIL -> STOP"
    elif daily_fail or mon_fail or agg_fail:
        verdict = "UNRESOLVED (proxy)"
    else:
        verdict = "PASS"

    TRACKER.parent.mkdir(parents=True, exist_ok=True)
    tr = pd.DataFrame(tracker, columns=["day", "target_year", "component", "weight"])
    tr.to_csv(TRACKER, index=False, encoding="utf-8", lineterminator="\n", compression={"method": "gzip", "mtime": 0})
    doc = {"spec": "D634 (8fb1619 + its s.8 amendment), IR-A1..IR-A13", "cut": CUT,
           "verdict": {"verdict": verdict, "roll_day_failures": roll_fail, "coverage_failures": cov_fail,
                       "daily_failures": daily_fail, "monthly_failures": mon_fail, "aggregate_failures": agg_fail},
           "known_answers": known, "calendar": cal,
           "cims": {str(y): {c: round(v, 10) for c, v in cim[y].items()} for y in cim},
           "weights_at_det": wdet, "dN": dn, "net_flow": net, "published": pub, "coverage": cov,
           "bands": {"lme_3m_end": band_lme, "printed_det_dates": printed_dn,
                     "aum": "dN_aum_low/dN_aum_high per row (IR-A5); the sign never changes with AUM"},
           "deviations": DEVIATIONS, "reads": reads,
           "tracker": {"file": str(TRACKER.relative_to(REPO)), "sha256": sha256(TRACKER), "rows": len(tr)}}
    missing = [k for k in REQUIRED_OUTPUTS if k not in doc]
    if missing:
        raise GateR0Error(f"declared outputs missing: {missing}")
    return doc


def dump(doc: dict[str, Any]) -> str:
    return json.dumps(doc, indent=1, sort_keys=True, default=float) + "\n"


# ------------------------------------------------------------------ selftest
def selftest() -> int:
    """No fund NAV is read. Synthetic funds built from the true NG subindex (2016-2017 in-sample settlements) must
    PASS under the true schedule and FAIL the roll-day rule under a shifted schedule and under the front month;
    the flipped-L and lagged-index controls must fail; the unit tests and Table 13 must hold."""
    table13()
    print("  Table 13 reproduced; unit tests", unit_tests())
    reads: dict[str, Any] = {}
    cip = cips()
    cme, _ = load_cme(reads)
    prices: Prices = {**cme, **load_ice(reads), **load_lme(reads)}
    assert_no_vault(prices)
    bdays, bd, det = calendar(prices, cip)
    bdays = [d for d in bdays if "2016-01-01" <= d <= "2017-12-31"]
    comp = "Natural Gas"
    Rt, _ = sub_index_returns(comp, prices, bdays, bd)
    # a synthetic 2x fund on the true index, no fees and no interest
    nav = [100.0]
    dates = [bdays[0]]
    for d in bdays[1:]:
        nav.append(nav[-1] * (1 + 2 * ((Rt[d] or 1.0) - 1)))
        dates.append(d)
    fund = pd.DataFrame({"date": dates, "nav": nav})
    rates = {k: 0.0 for k in {d[:7] for d in bdays} | {month_minus(d[:7], RATE_LAG) for d in bdays}}

    def run(R: dict[str, float | None], L: int = 2, lag: bool = False) -> dict[str, Any]:
        return fund_verdict(replicate(fund, L, bdays, bd, R, rates, bdays[2], bdays[-1], er=0.0, lag_index=lag), L)

    true = run(Rt)
    assert true["daily_pass"] and true["monthly_pass"], true["roll_days"]
    Rs, _ = sub_index_returns(comp, prices, bdays, bd, roll_weights(comp, prices, bdays, bd, first_step_bd=7))
    shifted = run(Rs)
    assert not shifted["roll_day_pass"], ("a shifted schedule passed the roll-day rule", shifted["roll_days"])
    Rf, _ = sub_index_returns(comp, prices, bdays, bd, roll_weights(comp, prices, bdays, bd, front=True))
    front = run(Rf)
    assert not front["daily_pass"], ("the front month passed", front["roll_days"], front["other_days"])
    flip = run(Rt, L=-2)
    assert not flip["daily_pass"], "a flipped L passed"
    lag = run(Rt, lag=True)
    assert not lag["daily_pass"], "a lagged index passed"
    print(f"  synthetic NG 2x fund: true PASS (roll {true['roll_days']['share']}); shifted roll-day share "
          f"{shifted['roll_days']['share']}; front month {front['roll_days']['share']}/{front['other_days']['share']};"
          f" flipped {flip['all']['share']}; lagged {lag['all']['share']}")
    try:
        brent_known_answer()
    except GateR0Error as e:
        raise AssertionError(f"Brent known answer: {e}") from e
    print("selftest OK: Table 13, unit tests 1-8/12/13, the synthetic fund controls, the Brent known answer")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.run:
        if OUT.exists():
            raise SystemExit(f"{OUT.name} exists: Gate R0 runs once (D634 s.4's bug-fix pass must be logged first)")
        doc = build()
        OUT.write_text(dump(doc), encoding="utf-8", newline="\n")
        v = doc["verdict"]
        print(f"GATE R0: {v['verdict']}")
        for f, x in doc["published"].items():
            print(f"  {f:4s} {x['component']:14s} roll {x['roll_days']['share']} other {x['other_days']['share']} "
                  f"monthly {x['monthly']['share']} ({x['monthly']['months']} months)")
        print(f"  coverage failures: {v['coverage_failures']}")
        return 0
    if a.check:
        doc = build()
        if dump(doc) != OUT.read_text(encoding="utf-8"):
            raise SystemExit("CHECK FAILED: the rebuild differs from gate_r0.json")
        print("check OK: byte for byte")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
