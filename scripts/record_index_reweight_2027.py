"""Track 2 for the index-reweight model's January 2027 forward event (deposit s.3.5 and s.11; IR-A10).

    uv run python scripts/record_index_reweight_2027.py --settlements [--refresh]   # daily, from now
    uv run python scripts/record_index_reweight_2027.py --cim2026                    # once, ON THE PRINCIPAL'S RULING
    uv run python scripts/record_index_reweight_2027.py --forecast                   # daily, from the announcement

--settlements appends, for every post-vault trade date (from 2026-09-19) up to yesterday, the settlement of each BCOM
component's designated lead and next contract (Table 9a): CME and ICE from Sierra Chart's daily files (Close = the
exchange settlement, IR-A13), LME from Westmetall's current-year page (cash and 3-month, interpolated to the prompt,
IR-A4). A recorded (trade date, component, contract) is never overwritten; a later different value is logged as a
revision row. `--refresh` first asks Sierra Chart to extend the daily files (it must be running).

--cim2026 computes the 2026 multipliers, CIM_i proportional to CIP_i(2026) / P_lead,Jan(det 2026), from the
settlements of 2026-01-07 (BCOM's printed and rule-based det). That date is INSIDE the vault (A10), so it REFUSES
unless data/index_reweight/track2/cim2026_ruling.json holds the principal's words. It reads that one day only.

--forecast writes the 2027 flow forecast for the latest recorded date: w_i(t) = CIM_i(2026) x H_i(t) / sum and
dN_i = AUM_2027 x (target_i - w_i(t)) / (P_i x mult_i), for the 15 CME components. It REFUSES until
data/index_reweight/track2/targets_2027.csv exists (the 2027 targets and AUM, transcribed from BCOM's announcement
with its URL, AFTER the freeze) and cim_2026.json exists.
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
T2 = REPO / "data" / "index_reweight" / "track2"
SETTLE = T2 / "settlements.csv"
RULING = T2 / "cim2026_ruling.json"
CIM = T2 / "cim_2026.json"
TARGETS = T2 / "targets_2027.csv"
FORECAST = T2 / "forecasts_2027.csv"
RAW = REPO / "data" / "raw" / "index_reweight" / "track2"
POST_VAULT = "2026-09-19"
DET_2026 = "2026-01-07"
# CL, NG, HO and RB sessions from 2026-09-19 are the settlement ledger's D626 sample: unread until its one read on
# 2026-10-10, so the recorder skips those four before 2026-10-11
D626_ROOTS = {"WTI Crude Oil", "Natural Gas", "ULS Diesel", "RBOB Gasoline"}
D626_FREE_FROM = dt.date(2026, 10, 11)
LETTER = "FGHJKMNQUVXZ"
ICE = {"Brent Crude Oil": ("BRN", "ICEEU"), "Low Sulphur Gas Oil": ("GAS", "ICEEU"), "Sugar": ("SB", "ICEUS"),
       "Coffee": ("KC", "ICEUS"), "Cotton": ("CT", "ICEUS"), "Cocoa": ("CC", "ICEUS")}
LME = {"Aluminum": ("Al", "aluminium"), "Zinc": ("Zn", "zinc"), "Nickel": ("Ni", "nickel"), "Lead": ("Pb", "lead")}
WM_URL = "https://www.westmetall.com/en/markdaten.php?action=table&field=LME_{m}_cash&year={y}"
ROW = re.compile(r"<tr>\s*<td >(\d\d\. \w+ \d{4})</td>\s*<td >([\d,.\-]*)</td>\s*<td >([\d,.\-]*)</td>")


def _load(name: str, fn: str) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    assert s is not None and s.loader is not None
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


def table() -> dict[str, dict[str, str]]:
    return json.loads((REPO / "data" / "index_reweight" / "methodology_facts.json").read_text(encoding="utf-8"))[
        "designated_contract_schedule"]["table"]


TABLE_NAME = {"Wheat": "Wheat (Chicago)", "HRW Wheat": "Wheat (KC HRW)"}


def components() -> list[str]:
    return list(pd.read_csv(REPO / "data" / "index_reweight" / "weights" / "2026.csv", encoding="utf-8")["component"])


def lead_next(comp: str, y: int, m: int) -> tuple[tuple[int, int], tuple[int, int]]:
    row = table()[TABLE_NAME.get(comp, comp)]
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    def lead(yy: int, mm: int) -> tuple[int, int]:
        lm = months.index(row[months[mm - 1]]) + 1
        return (yy if lm >= mm else yy + 1), lm

    return lead(y, m), (lead(y + 1, 1) if m == 12 else lead(y, m + 1))


def sierra_sym(comp: str, ym: tuple[int, int]) -> str | None:
    if comp in ICE:
        code, ex = ICE[comp]
    else:
        SD = _load("sierra_index_reweight_download", "sierra_index_reweight_download.py")
        name = TABLE_NAME.get(comp, comp)
        if name not in SD.ROOTS:
            return None
        code, ex = SD.ROOTS[name]
    return f"{code}{LETTER[ym[1] - 1]}{ym[0] % 100:02d}-{ex}"


def dly(sym: str) -> dict[str, float]:
    p = Path(r"C:\SierraChart\Data") / f"{sym}.dly"
    if not p.exists():
        return {}
    d = pd.read_csv(p, skipinitialspace=True, encoding="utf-8")
    d.columns = [c.strip() for c in d.columns]
    return {r: float(c) for r, c in zip(pd.to_datetime(d["Date"]).dt.strftime("%Y-%m-%d"), d["Close"]) if c}


def westmetall(year: int) -> pd.DataFrame:
    """Fetch the current-year LME pages into Track 2's own raw folder (the in-sample file is never touched)."""
    RAW.mkdir(parents=True, exist_ok=True)
    rows = []
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for comp, (m, name) in LME.items():
        req = urllib.request.Request(WM_URL.format(m=m, y=year), headers={"User-Agent": "Mozilla/5.0 (research data fetch)"})
        with urllib.request.urlopen(req, timeout=60) as r:
            html = r.read()
        (RAW / f"LME_{m}_{year}_{stamp}.html").write_bytes(html)
        for d, cash, three in ROW.findall(html.decode("utf-8", errors="replace")):
            num = [float(x.replace(",", "")) if x.strip() not in ("", "-") else float("nan") for x in (cash, three)]
            rows.append((pd.to_datetime(d, format="%d. %B %Y").strftime("%Y-%m-%d"), comp, name, *num))
    return pd.DataFrame(rows, columns=["date", "component", "metal", "cash", "three_month"])


def third_wednesday(y: int, m: int) -> pd.Timestamp:
    d = pd.Timestamp(y, m, 1)
    return d + pd.Timedelta(days=(2 - d.dayofweek) % 7 + 14)


def lme_price(row: pd.Series, ym: tuple[int, int]) -> float:
    t = pd.Timestamp(row["date"])
    f = (third_wednesday(*ym) - t).days / ((t + pd.DateOffset(months=3)) - t).days
    return float(row["cash"] + (row["three_month"] - row["cash"]) * f)


def record_settlements(refresh: bool) -> int:
    T2.mkdir(parents=True, exist_ok=True)
    today = dt.date.today()
    days = [d.strftime("%Y-%m-%d") for d in pd.bdate_range(POST_VAULT, today - dt.timedelta(days=1))]
    want: dict[str, list[tuple[str, tuple[int, int]]]] = {}
    skip = D626_ROOTS if today < D626_FREE_FROM else set()
    for d in days:
        y, m = int(d[:4]), int(d[5:7])
        for comp in components():
            if comp in skip:
                continue
            for ym in set(lead_next(comp, y, m)):
                want.setdefault(comp, []).append((d, ym))
    if refresh:
        SD = _load("sierra_index_reweight_download", "sierra_index_reweight_download.py")
        syms = sorted({s for comp, v in want.items() for _d, ym in v if (s := sierra_sym(comp, ym))})
        SD.queue(syms, "dly", refresh=True)
    lme = westmetall(today.year)
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    new = []
    for comp, v in want.items():
        for d, ym in v:
            if comp in LME:
                r = lme[(lme["component"] == comp) & (lme["date"] == d)]
                if r.empty or r[["cash", "three_month"]].isna().any(axis=None):
                    continue
                px, src = lme_price(r.iloc[0], ym), "Westmetall LME cash/3M interpolated to the prompt"
            else:
                s = sierra_sym(comp, ym)
                px = dly(s).get(d) if s else None
                if px is None:
                    continue
                src = f"Sierra Chart daily {s}"
            new.append({"trade_date": d, "component": comp, "contract": f"{ym[0]}-{ym[1]:02d}", "settle": px,
                        "source": src, "recorded_utc": now, "kind": "first"})
    old = pd.read_csv(SETTLE, encoding="utf-8", dtype={"trade_date": str}) if SETTLE.exists() else pd.DataFrame(
        columns=["trade_date", "component", "contract", "settle", "source", "recorded_utc", "kind"])
    have = {(r.trade_date, r.component, r.contract): r.settle for r in old[old["kind"] == "first"].itertuples()}
    add = []
    for r in new:
        k = (r["trade_date"], r["component"], r["contract"])
        if k not in have:
            add.append(r)
        elif abs(float(have[k]) - r["settle"]) > 1e-9 and not ((old["trade_date"] == k[0]) & (old["component"] == k[1])
                                                               & (old["contract"] == k[2]) & (old["settle"] == r["settle"])).any():
            add.append({**r, "kind": "revision"})
    if add:
        out = pd.concat([old, pd.DataFrame(add)], ignore_index=True)
        if (out["trade_date"] < POST_VAULT).any():
            raise RuntimeError("a pre-2026-09-19 (vault) trade date would be recorded")
        if today < D626_FREE_FROM and out["component"].isin(D626_ROOTS).any():
            raise RuntimeError("a CL/NG/HO/RB post-vault settlement (D626's unread sample) would be recorded")
        out.to_csv(SETTLE, index=False, encoding="utf-8", lineterminator="\n")
    print(f"recorded {sum(1 for r in add if r['kind'] == 'first')} settlements, "
          f"{sum(1 for r in add if r['kind'] == 'revision')} revisions; {len(days)} post-vault days considered")
    return 0


def cim2026() -> int:
    if not RULING.exists() or not json.loads(RULING.read_text(encoding="utf-8")).get("instruction"):
        raise SystemExit(f"REFUSING: {DET_2026} is inside the vault (A10). {RULING.name} must hold the principal's "
                         "words before its settlements are read.")
    cip = pd.read_csv(REPO / "data" / "index_reweight" / "weights" / "2026.csv", encoding="utf-8")
    cip = dict(zip(cip["component"], cip["target_weight_pct"] / cip["target_weight_pct"].sum()))
    lme = westmetall(2026)
    out: dict[str, Any] = {"det": DET_2026, "ruling": json.loads(RULING.read_text(encoding="utf-8")), "components": {}}
    for comp, w in cip.items():
        L, _ = lead_next(comp, 2026, 1)
        if comp in LME:
            r = lme[(lme["component"] == comp) & (lme["date"] == DET_2026)]
            px = lme_price(r.iloc[0], L) if not r.empty else None
        else:
            s = sierra_sym(comp, L)
            px = dly(s).get(DET_2026) if s else None
        if px is None or px <= 0:
            raise RuntimeError(f"no {DET_2026} settlement for {comp} {L}")
        out["components"][comp] = {"contract": f"{L[0]}-{L[1]:02d}", "price": px, "cip": w, "cim": w * 1000 / px}
    CIM.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {CIM.name}: {len(out['components'])} components at {DET_2026}")
    return 0


def forecast() -> int:
    for p in (CIM, TARGETS, SETTLE):
        if not p.exists():
            raise SystemExit(f"REFUSING: {p.name} is missing. The forecast needs the 2026 multipliers (--cim2026, on "
                             "the principal's ruling), the 2027 targets (after the announcement) and recorded settlements.")
    G = _load("run_gate_r0", "run_gate_r0.py")
    cim = {c: v["cim"] for c, v in json.loads(CIM.read_text(encoding="utf-8"))["components"].items()}
    tg = pd.read_csv(TARGETS, encoding="utf-8")
    target = dict(zip(tg["component"], tg["target_weight_pct"] / tg["target_weight_pct"].sum()))
    aum = float(tg["tracking_aum_usd_bn"].iloc[0])
    s = pd.read_csv(SETTLE, encoding="utf-8", dtype={"trade_date": str})
    s = s[s["kind"] == "first"]
    t = s["trade_date"].max()
    y, m = int(t[:4]), int(t[5:7])
    month_days = sorted(s[s["trade_date"].str[:7] == t[:7]]["trade_date"].unique())
    k = month_days.index(t) + 1  # the business-day number, on the recorded calendar
    b = min(max((k - 5) / 5.0, 0.0), 1.0)  # the index roll weight (BCOM s.2.8; BD6-10)
    H = {}
    for comp in cim:
        L, N = lead_next(comp, y, m)
        px = s[(s["trade_date"] == t) & (s["component"] == comp)].set_index("contract")["settle"]
        pl, pn = px.get(f"{L[0]}-{L[1]:02d}"), px.get(f"{N[0]}-{N[1]:02d}")
        bb = 0.0 if L == N else b
        if pl is None or (bb > 0 and pn is None):
            raise RuntimeError(f"no settlement for {comp} on {t}")
        H[comp] = (1 - bb) * pl + bb * (pn if pn is not None else 0.0)
    tot = sum(cim[c] * H[c] for c in cim)
    rows = []
    for comp in G.CME_COMPS:
        w = cim[comp] * H[comp] / tot
        L, _ = lead_next(comp, y, m)
        p = float(s[(s["trade_date"] == t) & (s["component"] == comp) & (s["contract"] == f"{L[0]}-{L[1]:02d}")]["settle"].iloc[0])
        dn = aum * 1e9 * (target.get(comp, 0.0) - w) / (p * G.mult(comp))
        rows.append({"as_of": t, "component": comp, "w_drift": w, "target": target.get(comp, 0.0),
                     "gap": target.get(comp, 0.0) - w, "dN": dn, "price": p, "aum_bn": aum,
                     "recorded_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")})
    f = pd.DataFrame(rows)
    old = pd.read_csv(FORECAST, encoding="utf-8", dtype={"as_of": str}) if FORECAST.exists() else None
    if old is not None and (old["as_of"] == t).any():
        print(f"a forecast for {t} is already recorded; nothing appended")
        return 0
    pd.concat([old, f] if old is not None else [f]).to_csv(FORECAST, index=False, encoding="utf-8", lineterminator="\n")
    print(f"recorded the 2027 forecast as of {t} for {len(f)} components")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--settlements", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--cim2026", action="store_true")
    ap.add_argument("--forecast", action="store_true")
    a = ap.parse_args()
    if a.settlements:
        return record_settlements(a.refresh)
    if a.cim2026:
        return cim2026()
    if a.forecast:
        return forecast()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
