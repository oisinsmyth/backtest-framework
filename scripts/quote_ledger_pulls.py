"""Quote, never download: every Databento pull the settlement ledger needs under amendments A6 and A7 (AITODO 4 and 6).

Metadata calls only (`get_dataset_range`, `get_billable_size`, `get_cost`). No batch job is submitted and no bytes
move. The key is the principal's (env DATABENTO_API_KEY or ~/.config/databento/key) and is never printed.

    python scripts/quote_ledger_pulls.py     # SYSTEM interpreter (databento); writes data/ledger_pull_quote.json

Spans, from the amendments: in-sample 2017-05-21 → 2025-02-28 (A6, A7); the ETF sub-sample 2018-05-01 → 2025-02-28
(A7); the vault 2025-03-01 → 2026-09-18, quoted separately because it is read once, at the end. End dates are
exclusive, as Databento takes them.

Stage H's order book is quoted two ways. The whole trading day is one way. The other is a window of 13:45-14:45 ET
around the 14:28-14:30 settlement, on a sample of twelve days, scaled up to the whole span. Databento bills by the
bytes inside the requested range, so a window pull is one request per day.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "ledger_pull_quote.json"
KEY_FILE = Path.home() / ".config" / "databento" / "key"
ETFS = ["BOIL", "KOLD", "UCO", "SCO", "UNG", "USO"]
IN_SAMPLE = ("2017-05-21", "2025-03-01")
ETF_SUB = ("2018-05-01", "2025-03-01")
VAULT = ("2025-03-01", "2026-09-19")
#: one day a quarter-ish across the in-sample, for scaling the windowed order-book quote
MBO_SAMPLE_DAYS = ["2017-08-15", "2018-01-17", "2018-06-13", "2019-03-12", "2019-11-13", "2020-06-16",
                   "2021-02-17", "2021-10-13", "2022-05-17", "2023-01-18", "2023-09-13", "2024-07-17"]
#: the whole-day quotes each windowed estimate is scaled from: (in-sample, vault)
WHOLE = {"mbo": ("cl_ng_mbo_in_sample_whole_days", "cl_ng_mbo_vault_whole_days"),
         "trades": ("cl_ng_trades_in_sample", "cl_ng_trades_vault")}


def api_key() -> str:
    k = os.environ.get("DATABENTO_API_KEY")
    if k:
        return k.strip()
    if KEY_FILE.exists():
        return KEY_FILE.read_text(encoding="utf-8").strip()
    raise SystemExit(f"no key: set DATABENTO_API_KEY or write {KEY_FILE}")


def quote(c: Any, dataset: str, symbols: list[str], schema: str, span: tuple[str, str], stype_in: str) -> dict[str, Any]:
    kw = {"dataset": dataset, "symbols": symbols, "schema": schema, "start": span[0], "end": span[1], "stype_in": stype_in}
    size = c.metadata.get_billable_size(**kw)
    usd = c.metadata.get_cost(**kw)
    return {"dataset": dataset, "symbols": symbols, "schema": schema, "start": span[0], "end_exclusive": span[1],
            "billable_gb": round(size / 1e9, 3), "usd": round(float(usd), 2)}


def et_to_utc(day: str, hhmm: str) -> str:
    """ET wall clock to UTC, US DST rules (second Sunday of March to first Sunday of November)."""
    d = dt.date.fromisoformat(day)
    mar = dt.date(d.year, 3, 8) + dt.timedelta(days=(6 - dt.date(d.year, 3, 8).weekday()) % 7)
    nov = dt.date(d.year, 11, 1) + dt.timedelta(days=(6 - dt.date(d.year, 11, 1).weekday()) % 7)
    off = 4 if mar <= d < nov else 5
    h, m = map(int, hhmm.split(":"))
    return (dt.datetime(d.year, d.month, d.day, h, m) + dt.timedelta(hours=off)).strftime("%Y-%m-%dT%H:%M")


def main() -> int:
    import databento as db
    c = db.Historical(api_key())
    t0 = time.time()
    out: dict[str, Any] = {"quoted_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "submitted": False,
                           "spans": {"in_sample": IN_SAMPLE, "etf_sub_sample": ETF_SUB, "vault": VAULT},
                           "dataset_ranges": {}, "quotes": {}}
    for ds in ("ARCX.PILLAR", "EQUS.MINI", "GLBX.MDP3"):
        r = c.metadata.get_dataset_range(dataset=ds)
        out["dataset_ranges"][ds] = {k: str(v) for k, v in (r.items() if isinstance(r, dict) else {"range": r}.items())}
    eq_start = str(out["dataset_ranges"]["EQUS.MINI"].get("start", "2023-03-28"))[:10]
    q = out["quotes"]
    for schema in ("bbo-1m", "trades"):
        q[f"etf_arca_{schema}_sub_sample"] = quote(c, "ARCX.PILLAR", ETFS, schema, ETF_SUB, "raw_symbol")
        q[f"etf_arca_{schema}_vault"] = quote(c, "ARCX.PILLAR", ETFS, schema, VAULT, "raw_symbol")
    q["etf_consolidated_bbo-1m_check_window"] = quote(c, "EQUS.MINI", ETFS, "bbo-1m", (eq_start, IN_SAMPLE[1]), "raw_symbol")
    q["etf_consolidated_bbo-1m_vault"] = quote(c, "EQUS.MINI", ETFS, "bbo-1m", VAULT, "raw_symbol")
    for label, syms in (("cl_ng", ["CL.FUT", "NG.FUT"]), ("tas", ["CLT.FUT", "NGT.FUT"])):
        q[f"{label}_trades_in_sample"] = quote(c, "GLBX.MDP3", syms, "trades", IN_SAMPLE, "parent")
        q[f"{label}_trades_vault"] = quote(c, "GLBX.MDP3", syms, "trades", VAULT, "parent")
    q["cl_ng_mbo_in_sample_whole_days"] = quote(c, "GLBX.MDP3", ["CL.FUT", "NG.FUT"], "mbo", IN_SAMPLE, "parent")
    q["cl_ng_mbo_vault_whole_days"] = quote(c, "GLBX.MDP3", ["CL.FUT", "NG.FUT"], "mbo", VAULT, "parent")
    # windowed pulls, scaled from the sample days: the order book over 13:30 ET to the window's end (deposit line
    # 828), and trades over 13:30-14:45 (S_pre from 13:30, line 371; the window to 14:30) plus 10:30-12:30 (H5's
    # time placebo, 11:30 ledger applied to 11:50-12:20, line 554)
    windows = {"mbo": [("13:30", "14:35")], "trades": [("13:30", "14:45"), ("10:30", "12:30")]}
    out["window_samples"] = {}
    for schema, spans in windows.items():
        samp = []
        for day in MBO_SAMPLE_DAYS:
            nxt = (dt.date.fromisoformat(day) + dt.timedelta(days=1)).isoformat()
            w_usd = sum(quote(c, "GLBX.MDP3", ["CL.FUT", "NG.FUT"], schema, (et_to_utc(day, a), et_to_utc(day, b)),
                              "parent")["usd"] for a, b in spans)
            whole = quote(c, "GLBX.MDP3", ["CL.FUT", "NG.FUT"], schema, (day, nxt), "parent")["usd"]
            samp.append({"day": day, "window_usd": round(w_usd, 2), "whole_day_usd": whole})
        dsum = sum(s["whole_day_usd"] for s in samp)
        frac = sum(s["window_usd"] for s in samp) / dsum if dsum else None
        full_in, full_vault = WHOLE[schema]
        out["window_samples"][schema] = {
            "windows_et": spans, "days": samp, "window_share_of_whole_day_cost": frac,
            "in_sample_estimate_usd": None if frac is None else round(frac * q[full_in]["usd"], 2),
            "vault_estimate_usd": None if frac is None else round(frac * q[full_vault]["usd"], 2)}
    out["timing_s"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    for k, v in q.items():
        print(f"  {k:44s} {v['start'][:10]} ->{v['end_exclusive'][:10]}  {v['billable_gb']:10.3f} GB  USD {v['usd']:>10,.2f}")
    for schema, m in out["window_samples"].items():
        print(f"  {schema} windows {m['windows_et']} ET: {m['window_share_of_whole_day_cost']:.4f} of whole-day cost ->"
              f" in-sample ~USD {m['in_sample_estimate_usd']}, vault ~USD {m['vault_estimate_usd']}")
    print(f"  wrote {OUT.relative_to(REPO)} in {out['timing_s']} s; nothing submitted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
