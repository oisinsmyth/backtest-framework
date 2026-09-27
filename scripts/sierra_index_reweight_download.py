"""Download Sierra Chart 1-tick files for the index-reweight model's aggressor-signed window flow (Gate C0 and
Stage R1; the principal, 2026-09-27: "Sierra Chart, free").

THE LIST. For each of the 15 CME Group BCOM components, every contract that is BCOM's Lead Future in some calendar
month from 2015-12 to 2025-03. That covers the lead and the next contract of every roll period from January 2016
through February 2025 (the in-sample, A10). The lead-month table is BCOM's Table 9a (identical in every
methodology version 2016-2026), read from `data/index_reweight/methodology_facts.json`. Vault months are not listed.

THE NEED. A contract is needed from 30 business days before the first roll period that rolls into it (the trailing
20-day norm of window flow) to business day 10 of the last roll period that rolls out of it. `--record` marks a
file `covers` when it spans that interval. Sierra Chart serves about five months of 1-tick history per contract.

HOW. The probe of 2026-09-27 (scratchpad `sierra_probe.py`) confirmed 1-tick CBOT and COMEX files before 2020.
Queueing opens each chart through Sierra Chart's UDP port and sends 57078 (Download Data From End of Chart), which
works after a 57081 cancel (memory: sierra-chart-download-quirks). `--record` reads a file's size and its first and
last timestamps only; no price, volume or side is read.

    uv run python scripts/sierra_index_reweight_download.py --list
    uv run python scripts/sierra_index_reweight_download.py --queue
    uv run python scripts/sierra_index_reweight_download.py --wait --record
"""
from __future__ import annotations

import argparse
import json
import re
import socket
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import sierra_ui as U  # noqa: E402

FACTS = REPO / "data" / "index_reweight" / "methodology_facts.json"
OUT = REPO / "data" / "index_reweight" / "sierra_download_record.json"
SC_DATA = Path(r"C:\SierraChart\Data")
UDP = ("127.0.0.1", 22903)
HDR, REC_SIZE = 56, 40
FIRST_MONTH, LAST_MONTH = "2015-12", "2025-03"
NORM_BDAYS = 30
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
LETTER = "FGHJKMNQUVXZ"
# BCOM component -> (Sierra Chart root, exchange suffix). Roots are CME Globex codes; the mapping is the
# exchanges' own product codes, not a BCOM fact.
ROOTS = {"Natural Gas": ("NG", "NYMEX"), "WTI Crude Oil": ("CL", "NYMEX"), "ULS Diesel": ("HO", "NYMEX"),
         "RBOB Gasoline": ("RB", "NYMEX"), "Corn": ("ZC", "CBOT"), "Soybeans": ("ZS", "CBOT"),
         "Soybean Meal": ("ZM", "CBOT"), "Soybean Oil": ("ZL", "CBOT"), "Wheat (Chicago)": ("ZW", "CBOT"),
         "Wheat (KC HRW)": ("KE", "CBOT"), "Copper": ("HG", "COMEX"), "Gold": ("GC", "COMEX"),
         "Silver": ("SI", "COMEX"), "Live Cattle": ("LE", "CME"), "Lean Hogs": ("HE", "CME")}
# The ICE components, for the drift only (amendment IR-A4; the principal, 2026-09-27: "Yes to both"). Gasoil joined
# BCOM for target year 2019, so its list starts 2018-12. Cocoa is not in BCOM in 2016-2025, so it is not listed.
# The others start 2014-12: the 2016 event's drift runs from det(2015), BD4 of January 2015 (D634 §2).
# Sierra's symbols were resolved by chart title on 2026-09-27: GASF20-ICEEU is "Gas Oil LS - ICE EU" (GF20 does
# not resolve); KC and CT on ICEUS are "Coffee C Arabica" and "Cotton #2".
ICE_ROOTS = {"Brent Crude Oil": ("BRN", "ICEEU"), "Low Sulphur Gas Oil": ("GAS", "ICEEU"),
             "Sugar": ("SB", "ICEUS"), "Coffee": ("KC", "ICEUS"), "Cotton": ("CT", "ICEUS")}
ICE_FIRST_MONTH = {"Low Sulphur Gas Oil": "2018-12", "Brent Crude Oil": "2014-12", "Sugar": "2014-12",
                   "Coffee": "2014-12", "Cotton": "2014-12"}
SETS = {"cme": ROOTS, "ice": ICE_ROOTS}


def lead_table(roots: dict[str, tuple[str, str]] = ROOTS) -> dict[str, dict[str, str]]:
    t = json.loads(FACTS.read_text(encoding="utf-8"))["designated_contract_schedule"]["table"]
    missing = set(roots) - set(t)
    if missing:
        raise KeyError(f"no lead-month row for {sorted(missing)}")
    return {k: t[k] for k in roots}


def lead_of(row: dict[str, str], y: int, m: int) -> tuple[int, int]:
    """The Lead Future (year, month) in calendar month m of year y: the table gives the month; a lead month earlier
    in the calendar than m is next year's."""
    lm = MONTHS.index(row[MONTHS[m - 1]]) + 1
    return (y if lm >= m else y + 1), lm


def bday(y: int, m: int, n: int) -> pd.Timestamp:
    return pd.bdate_range(f"{y}-{m:02d}-01", periods=n)[-1]


def contract_list(which: str = "cme") -> dict[str, dict[str, Any]]:
    """{sierra symbol: {root, exchange, first_roll_in, last_roll_out, need_from, need_until}}."""
    out: dict[str, dict[str, Any]] = {}
    roots = SETS[which]
    for comp, row in lead_table(roots).items():
        root, ex = roots[comp]
        for p in pd.period_range(ICE_FIRST_MONTH.get(comp, FIRST_MONTH), LAST_MONTH, freq="M"):
            y, m = lead_of(row, p.year, p.month)
            sym = f"{root}{LETTER[m - 1]}{str(y)[2:]}-{ex}"
            r = out.setdefault(sym, {"component": comp, "root": root, "exchange": ex, "lead_months": []})
            r["lead_months"].append(str(p))
    for sym, r in out.items():
        first, last = pd.Period(r["lead_months"][0]), pd.Period(r["lead_months"][-1])
        # the roll period of month m moves from lead(m) to lead(m+1): a contract is rolled into during the month
        # before it first leads, and out of during the last month it leads
        roll_in, roll_out = first - 1, last
        r["need_from"] = str((bday(roll_in.year, roll_in.month, 5) - NORM_BDAYS * pd.offsets.BDay()).date())
        r["need_until"] = str(bday(roll_out.year, roll_out.month, 10).date())
    return dict(sorted(out.items()))


def size(sym: str) -> int:
    p = SC_DATA / f"{sym}.scid"
    return p.stat().st_size if p.exists() else 0


def file_span(sym: str) -> dict[str, Any]:
    """Record count and the first/last timestamps only."""
    p = SC_DATA / f"{sym}.scid"
    n = (size(sym) - HDR) // REC_SIZE
    if n <= 0:
        return {"records": 0}
    with open(p, "rb") as fh:
        fh.seek(HDR)
        first = int(np.frombuffer(fh.read(8), "<i8")[0])
        fh.seek(HDR + (n - 1) * REC_SIZE)
        last = int(np.frombuffer(fh.read(8), "<i8")[0])
    t = pd.to_datetime([first, last], unit="us", origin=pd.Timestamp("1899-12-30"))
    return {"records": int(n), "first_utc": str(t[0]), "last_utc": str(t[1])}


def dly_path(sym: str) -> Path:
    return SC_DATA / f"{sym}.dly"


def dly_span(sym: str) -> dict[str, Any]:
    """A daily file's row count and first/last dates. Its Close is the exchange settlement: it equals the CME
    settlement strip exactly on NGH20 and ZCH20, 1,095 of 1,095 days 2018-2020 (checked 2026-09-27)."""
    p = dly_path(sym)
    if not p.exists():
        return {"days": 0}
    lines = [ln for ln in p.read_text(encoding="utf-8").splitlines()[1:] if ln.strip()]
    if not lines:
        return {"days": 0}
    return {"days": len(lines), "first": lines[0].split(",")[0].replace("/", "-"),
            "last": lines[-1].split(",")[0].replace("/", "-")}


def queue(syms: list[str], ext: str = "scid") -> list[str]:
    todo = [x for x in syms if (size(x) <= HDR if ext == "scid" else dly_span(x)["days"] == 0)]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for i, x in enumerate(todo):
        s.sendto(f"{x}.{ext}".encode(), UDP)
        for _ in range(30):
            time.sleep(0.2)
            if any(t.startswith(x) for _h, t in U.mdi_charts()):
                break
        time.sleep(1.0)
        U.cmd_command(57078)
        time.sleep(1.5)
        U.cmd_close("^" + re.escape(x))
        if (i + 1) % 25 == 0:
            print(f"  queued {i + 1}/{len(todo)}", flush=True)
    print(f"queued {len(todo)}", flush=True)
    return todo


def wait_drained(syms: list[str], quiet_s: int = 600, cap_s: int = 12 * 3600) -> None:
    t0, last = time.time(), {x: size(x) for x in syms}
    changed = time.time()
    while time.time() - t0 < cap_s:
        time.sleep(60)
        now = {x: size(x) for x in syms}
        if now != last:
            grew = sum(1 for x in syms if now[x] != last[x])
            last, changed = now, time.time()
            got = sum(1 for x in syms if now[x] > HDR)
            print(f"  {time.strftime('%H:%M')} {got}/{len(syms)} files with data, {grew} grew, "
                  f"{sum(now.values()) / 1e9:.1f} GB", flush=True)
        elif time.time() - changed >= quiet_s:
            return


def record(lst: dict[str, dict[str, Any]], out: Path = OUT) -> dict[str, Any]:
    rec: dict[str, Any] = {"span": [FIRST_MONTH, LAST_MONTH], "contracts": {}}
    for sym, r in lst.items():
        sp = file_span(sym)
        covers = bool(sp.get("records", 0) > 0 and sp["first_utc"][:10] <= r["need_from"]
                      and sp["last_utc"][:10] >= r["need_until"])
        dl = dly_span(sym)
        # the daily file serves prices (settlements), for which the 30-day flow norm is not needed: it must span
        # the roll-in period to the roll-out period
        roll_in = str((pd.Timestamp(r["need_from"]) + NORM_BDAYS * pd.offsets.BDay()).date())
        rec["contracts"][sym] = {**{k: r[k] for k in ("root", "need_from", "need_until")}, "bytes": size(sym),
                                 **sp, "covers": covers, "daily": dl,
                                 "daily_covers": bool(dl["days"] > 0 and dl["first"] <= roll_in
                                                      and dl["last"] >= r["need_until"])}
    c = rec["contracts"]
    rec["summary"] = {root: {"files": sum(1 for v in c.values() if v["root"] == root),
                             "with_data": sum(1 for v in c.values() if v["root"] == root and v.get("records", 0) > 0),
                             "covers": sum(1 for v in c.values() if v["root"] == root and v["covers"]),
                             "daily_covers": sum(1 for v in c.values() if v["root"] == root and v["daily_covers"]),
                             "gb": round(sum(v["bytes"] for v in c.values() if v["root"] == root) / 1e9, 2)}
                      for root in sorted({v["root"] for v in c.values()})}
    out.write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return rec


def selftest() -> None:
    t = lead_table()
    assert lead_of(t["Natural Gas"], 2016, 11) == (2017, 1), "NG's November lead is next January"
    assert lead_of(t["Natural Gas"], 2016, 1) == (2016, 3)
    assert lead_of(t["Corn"], 2016, 12) == (2017, 3), "corn's December lead is next March"
    assert lead_of(t["Corn"], 2016, 11) == (2016, 12)
    lst = contract_list()
    assert "NGH16-NYMEX" in lst and "ZCZ16-CBOT" in lst and "GCG16-COMEX" in lst
    assert all(r["need_from"] < r["need_until"] for r in lst.values())
    # NG Jan-17 leads Nov and Dec 2016 (Table 9a), so it is rolled out of in December 2016's roll period
    assert lst["NGF17-NYMEX"]["need_until"] == str(bday(2016, 12, 10).date()), lst["NGF17-NYMEX"]
    ice = contract_list("ice")
    assert "BRNH16-ICEEU" in ice and "SBH16-ICEUS" in ice
    gas = [r for r in ice.values() if r["component"] == "Low Sulphur Gas Oil"]
    assert gas and min(m for r in gas for m in r["lead_months"]) == "2018-12", "gasoil starts with target year 2019"
    print(f"selftest OK: {len(lst)} CME contracts, {len(ice)} ICE contracts")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    for f in ("selftest", "list", "queue", "queue-daily", "wait", "record"):
        ap.add_argument(f"--{f}", action="store_true")
    ap.add_argument("--set", choices=sorted(SETS), default="cme")
    a = ap.parse_args(argv)
    lst = contract_list(a.set)
    syms = list(lst)
    out = OUT if a.set == "cme" else OUT.with_name(f"sierra_download_record_{a.set}.json")
    if a.selftest:
        selftest()
    if a.list:
        roots: dict[str, int] = {}
        for r in lst.values():
            roots[r["root"]] = roots.get(r["root"], 0) + 1
        have = sum(1 for x in syms if size(x) > HDR)
        print(f"{len(syms)} contracts ({have} already on disk): {roots}")
    if a.queue:
        queue(syms)
    if a.queue_daily:
        queue(syms, "dly")
    if a.wait:
        wait_drained(syms)
    if a.record:
        s = record(lst, out)["summary"]
        for root, v in s.items():
            print(f"  {root}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
