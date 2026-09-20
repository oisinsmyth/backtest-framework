"""One-time (manual, NETWORK) fetch: perpetual-swap funding rates and open interest, three venues.

    uv run python scripts/fetch_perp_funding.py --probe    # one call per endpoint: prove each answers
    uv run python scripts/fetch_perp_funding.py --fetch    # the series into data/raw/perp_funding/, resumable
    uv run python scripts/fetch_perp_funding.py --build    # cache -> committed fixtures + meta (gates)
    uv run python scripts/fetch_perp_funding.py --selftest # the gates raise on broken panels

Sibling of `fetch_cftc_cot.py`: stdlib only, cache the raw and commit the derived (D191).

WHY THIS EXISTS
---------------
`docs/internal/User-Doc-Deposit/FUNDING_CYCLE_BASIS.md` needs F1 (the published funding rate for
the coming settlement, cross-venue) and F5 (perp open interest x |F1|). Both are published by the
venues themselves and both are free. This fetcher builds the fixture the Stage 0 design reads;
nothing here reads a CME bar or computes a return.

WHAT THE VENUES GIVE, AS PROBED ON 2026-09-20
---------------------------------------------
  Binance USDT-M  fundingRate history      from 2019-09-10 (BTCUSDT), 2019-11-27 (ETHUSDT); 1000 a call, ascending
  Bybit  linear   funding history          from ~2020-03 (BTCUSDT), later for ETHUSDT; 200 a call, descending
  Bybit  inverse  funding history          from 2018-12 or earlier (BTCUSD); the deepest series
  Bybit  open interest, daily              from ~2020-09 (linear BTCUSDT); 200 a call
  OKX    funding-rate-history              SHALLOW: `after` paging returns nothing older than the recent window
  Binance openInterestHist                 the last 30 days only -- useless as history, not fetched

So the cross-venue average the deposit asks for is Binance + Bybit; OKX is carried for the
overlap it has and the meta records its depth. Open interest history is Bybit's alone.

THE SETTLEMENT TIMESTAMP IS THE KEY
-----------------------------------
Every row is keyed on the venue's settlement timestamp in UTC (ms since the epoch on the wire,
ISO in the fixture). The deposit's warning stands: three venues, three conventions -- the meta
records the share of each series' timestamps that fall on the 00/08/16 UTC grid, and the gate
asserts it for the venue whose published schedule is that grid. Bybit changes a contract's
funding interval when the rate hits its cap; its off-grid rows are real settlements and are kept.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "perp_funding"
FIX = REPO / "data" / "fixtures" / "perp_funding.csv"            # plain csv: small, and /data/**/*.csv.gz is gitignored
FIX_OI = REPO / "data" / "fixtures" / "perp_open_interest_daily.csv"
META = REPO / "data" / "fixtures" / "perp_funding.meta.json"
UA = {"User-Agent": "backtest-framework-fetch/1.0 (research; contact via repository)"}
PAUSE_S = 0.25
EPOCH_START_MS = int(datetime(2018, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)

# (venue, api symbol, asset, margin)
FUNDING_SERIES = [
    ("binance", "BTCUSDT", "BTC", "usdt"), ("binance", "ETHUSDT", "ETH", "usdt"),
    ("bybit_linear", "BTCUSDT", "BTC", "usdt"), ("bybit_linear", "ETHUSDT", "ETH", "usdt"),
    ("bybit_inverse", "BTCUSD", "BTC", "coin"), ("bybit_inverse", "ETHUSD", "ETH", "coin"),
    ("okx", "BTC-USDT-SWAP", "BTC", "usdt"), ("okx", "ETH-USDT-SWAP", "ETH", "usdt"),
    ("okx", "BTC-USD-SWAP", "BTC", "coin"), ("okx", "ETH-USD-SWAP", "ETH", "coin"),
]
OI_SERIES = [("bybit_linear", "BTCUSDT", "BTC", "usdt"), ("bybit_linear", "ETHUSDT", "ETH", "usdt"),
             ("bybit_inverse", "BTCUSD", "BTC", "coin"), ("bybit_inverse", "ETHUSD", "ETH", "coin")]


def _get(url, params):
    q = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(q, headers=UA)
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001 -- a network fetch retries on anything and then reports the tool
            if attempt == 4:
                raise RuntimeError(f"GET {q} failed after 5 attempts: {type(e).__name__}: {e}") from e
            time.sleep(2 * (attempt + 1))
    return None


def iso(ms):
    return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---- funding, per venue: each returns a list of {t_ms, rate, mark} ascending, complete ----

def fetch_binance(sym, log):
    out, start = [], EPOCH_START_MS
    while True:
        rows = _get("https://fapi.binance.com/fapi/v1/fundingRate", {"symbol": sym, "startTime": start, "limit": 1000})
        if not rows:
            break
        out += [{"t_ms": int(r["fundingTime"]), "rate": float(r["fundingRate"]), "mark": float(r["markPrice"]) if r.get("markPrice") not in ("", None) else None} for r in rows]
        log(f"    binance {sym}: {len(out)} rows to {iso(out[-1]['t_ms'])}")
        if len(rows) < 1000:
            break
        start = int(rows[-1]["fundingTime"]) + 1; time.sleep(PAUSE_S)
    return out


def fetch_bybit(category, sym, log):
    out, end = [], int(time.time() * 1000)
    while True:
        j = _get("https://api.bybit.com/v5/market/funding/history", {"category": category, "symbol": sym, "startTime": EPOCH_START_MS, "endTime": end, "limit": 200})
        if j.get("retCode") != 0:
            raise RuntimeError(f"bybit {category} {sym}: {j.get('retMsg')}")
        rows = j["result"]["list"]
        if not rows:
            break
        out += [{"t_ms": int(r["fundingRateTimestamp"]), "rate": float(r["fundingRate"]), "mark": None} for r in rows]
        oldest = min(int(r["fundingRateTimestamp"]) for r in rows)
        log(f"    bybit {category} {sym}: {len(out)} rows back to {iso(oldest)}")
        if len(rows) < 200:
            break
        end = oldest - 1; time.sleep(PAUSE_S)
    out.sort(key=lambda r: r["t_ms"]); return out


def fetch_okx(inst, log):
    out, after = [], None
    while True:
        p = {"instId": inst, "limit": 100}
        if after is not None:
            p["after"] = after
        j = _get("https://www.okx.com/api/v5/public/funding-rate-history", p)
        if j.get("code") != "0":
            raise RuntimeError(f"okx {inst}: {j.get('msg')}")
        rows = j["data"]
        if not rows:
            break
        out += [{"t_ms": int(r["fundingTime"]), "rate": float(r.get("realizedRate") or r["fundingRate"]), "mark": None} for r in rows]
        oldest = min(int(r["fundingTime"]) for r in rows)
        log(f"    okx {inst}: {len(out)} rows back to {iso(oldest)}")
        if len(rows) < 100:
            break
        after = oldest; time.sleep(PAUSE_S)
    out.sort(key=lambda r: r["t_ms"]); return out


def fetch_bybit_oi(category, sym, log):
    out, end = [], int(time.time() * 1000)
    while True:
        j = _get("https://api.bybit.com/v5/market/open-interest", {"category": category, "symbol": sym, "intervalTime": "1d", "startTime": EPOCH_START_MS, "endTime": end, "limit": 200})
        if j.get("retCode") != 0:
            raise RuntimeError(f"bybit OI {category} {sym}: {j.get('retMsg')}")
        rows = j["result"]["list"]
        if not rows:
            break
        out += [{"t_ms": int(r["timestamp"]), "oi": float(r["openInterest"])} for r in rows]
        oldest = min(int(r["timestamp"]) for r in rows)
        log(f"    bybit OI {category} {sym}: {len(out)} rows back to {iso(oldest)}")
        if len(rows) < 200:
            break
        end = oldest - 1; time.sleep(PAUSE_S)
    out.sort(key=lambda r: r["t_ms"]); return out


def probe(log=print):
    log("probe: one call per endpoint")
    r = _get("https://fapi.binance.com/fapi/v1/fundingRate", {"symbol": "BTCUSDT", "limit": 2}); log(f"  binance: {len(r)} rows, last {iso(r[-1]['fundingTime'])}")
    r = _get("https://api.bybit.com/v5/market/funding/history", {"category": "linear", "symbol": "BTCUSDT", "limit": 2}); log(f"  bybit linear: retCode {r['retCode']}, last {iso(r['result']['list'][0]['fundingRateTimestamp'])}")
    r = _get("https://api.bybit.com/v5/market/funding/history", {"category": "inverse", "symbol": "BTCUSD", "limit": 2}); log(f"  bybit inverse: retCode {r['retCode']}, last {iso(r['result']['list'][0]['fundingRateTimestamp'])}")
    r = _get("https://www.okx.com/api/v5/public/funding-rate-history", {"instId": "BTC-USDT-SWAP", "limit": 2}); log(f"  okx: code {r['code']}, last {iso(r['data'][0]['fundingTime'])}")
    r = _get("https://api.bybit.com/v5/market/open-interest", {"category": "linear", "symbol": "BTCUSDT", "intervalTime": "1d", "limit": 2}); log(f"  bybit OI: retCode {r['retCode']}, last {iso(r['result']['list'][0]['timestamp'])}")
    return 0


def fetch(log=print):
    RAW.mkdir(parents=True, exist_ok=True); t0 = time.time()
    for venue, sym, asset, margin in FUNDING_SERIES:
        f = RAW / f"funding_{venue}_{sym}.json"
        if f.exists():
            log(f"  {f.name}: cached, skipped"); continue
        if venue == "binance":
            rows = fetch_binance(sym, log)
        elif venue.startswith("bybit"):
            rows = fetch_bybit(venue.split("_")[1], sym, log)
        else:
            rows = fetch_okx(sym, log)
        f.write_text(json.dumps({"venue": venue, "symbol": sym, "asset": asset, "margin": margin, "fetched_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "rows": rows}), encoding="utf-8")
        log(f"  {f.name}: {len(rows)} rows written")
    for venue, sym, asset, margin in OI_SERIES:
        f = RAW / f"oi_{venue}_{sym}.json"
        if f.exists():
            log(f"  {f.name}: cached, skipped"); continue
        rows = fetch_bybit_oi(venue.split("_")[1], sym, log)
        f.write_text(json.dumps({"venue": venue, "symbol": sym, "asset": asset, "margin": margin, "fetched_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "rows": rows}), encoding="utf-8")
        log(f"  {f.name}: {len(rows)} rows written")
    log(f"  fetch done in {time.time() - t0:.0f} s"); return 0


# ---- build: cache -> tidy fixtures, with the gates ----

def _load_raw(prefix):
    out = []
    for f in sorted(RAW.glob(f"{prefix}_*.json")):
        j = json.loads(f.read_text(encoding="utf-8"))
        for r in j["rows"]:
            out.append({"venue": j["venue"], "symbol": j["symbol"], "asset": j["asset"], "margin": j["margin"], **r})
    return out


def gates(rows, oi_rows):
    """The fixture's gates. Raise on a broken panel; return the per-series report."""
    import numpy as np
    keys = [(r["venue"], r["symbol"], r["t_ms"]) for r in rows]
    if len(set(keys)) != len(keys):
        raise AssertionError("G1: duplicate (venue, symbol, settlement) rows")
    rep = {}
    for venue, sym, _, _ in FUNDING_SERIES:
        s = [r for r in rows if r["venue"] == venue and r["symbol"] == sym]
        if not s:
            rep[f"{venue}:{sym}"] = {"rows": 0}; continue
        t = np.array([r["t_ms"] for r in s]); rate = np.array([r["rate"] for r in s])
        on_grid = float(np.mean((t // 1000) % (8 * 3600) == 0))
        span_slots = int((t.max() - t.min()) // (8 * 3600 * 1000)) + 1
        rep[f"{venue}:{sym}"] = {"rows": int(t.size), "first": iso(t.min()), "last": iso(t.max()), "share_on_8h_grid": on_grid,
                                 "expected_8h_slots": span_slots, "coverage_of_8h_slots": float(t.size / span_slots),
                                 "share_exactly_default_0.0001": float(np.mean(rate == 1e-4)), "abs_rate_max": float(np.abs(rate).max()),
                                 "rate_mean": float(rate.mean()), "rate_p05": float(np.percentile(rate, 5)), "rate_p95": float(np.percentile(rate, 95)),
                                 "share_negative": float(np.mean(rate < 0))}
        if np.abs(rate).max() > 0.05:
            raise AssertionError(f"G4: {venue} {sym} has a rate beyond 5% a period: {np.abs(rate).max()}")
    b = rep.get("binance:BTCUSDT", {})
    if b.get("rows", 0) and b["share_on_8h_grid"] < 0.95:
        raise AssertionError(f"G2: binance BTCUSDT settlements off the 00/08/16 UTC grid: {1 - b['share_on_8h_grid']:.3f}")
    # G3: cross-venue agreement of the BTC rate on common settlements
    def series(venue, sym):
        return {r["t_ms"]: r["rate"] for r in rows if r["venue"] == venue and r["symbol"] == sym}
    a, c = series("binance", "BTCUSDT"), series("bybit_linear", "BTCUSDT"); common = sorted(set(a) & set(c))
    if len(common) > 100:
        x = np.array([a[k] for k in common]); y = np.array([c[k] for k in common]); rho = float(np.corrcoef(x, y)[0, 1])
        rep["G3_binance_vs_bybit_linear_BTC"] = {"common_settlements": len(common), "pearson": rho, "sign_agreement": float(np.mean(np.sign(x) == np.sign(y)))}
        if rho <= 0.3:
            raise AssertionError(f"G3: binance and bybit BTC funding disagree: rho {rho:.3f}")
    # OI
    okeys = [(r["venue"], r["symbol"], r["t_ms"]) for r in oi_rows]
    if len(set(okeys)) != len(okeys):
        raise AssertionError("G5: duplicate open-interest rows")
    for venue, sym, _, _ in OI_SERIES:
        s = [r for r in oi_rows if r["venue"] == venue and r["symbol"] == sym]
        if s:
            t = np.array([r["t_ms"] for r in s]); oi = np.array([r["oi"] for r in s])
            if (oi < 0).any():
                raise AssertionError("G6: negative open interest")
            rep[f"OI {venue}:{sym}"] = {"rows": int(t.size), "first": iso(t.min()), "last": iso(t.max()), "days_spanned": int((t.max() - t.min()) // 86_400_000) + 1, "oi_median": float(np.median(oi)), "oi_last": float(oi[-1])}
    return rep


def build(log=print):
    rows = _load_raw("funding"); oi_rows = _load_raw("oi")
    if not rows:
        log("nothing cached; run --fetch first"); return 2
    # Binance carries a +1 ms offset on thousands of settlement timestamps on the wire (1568476800001
    # for 2019-09-14T16:00:00Z); a settlement is on the minute by the venue's schedule, so the key is
    # floored to the minute and the count is recorded. Without this the cross-venue join loses half its rows.
    n_off = {}
    for r in rows:
        if r["t_ms"] % 60_000:
            n_off[r["venue"]] = n_off.get(r["venue"], 0) + 1; r["t_ms"] = (r["t_ms"] // 60_000) * 60_000
    rep = gates(rows, oi_rows); rep["wire_timestamps_off_the_minute_floored"] = n_off
    rows.sort(key=lambda r: (r["venue"], r["symbol"], r["t_ms"])); oi_rows.sort(key=lambda r: (r["venue"], r["symbol"], r["t_ms"]))
    with open(FIX, "w", encoding="utf-8", newline="\n") as f:
        f.write("venue,symbol,asset,margin,settlement_utc,funding_rate,mark_price\n")
        for r in rows:
            f.write(f"{r['venue']},{r['symbol']},{r['asset']},{r['margin']},{iso(r['t_ms'])},{r['rate']:.10g},{'' if r['mark'] is None else format(r['mark'], '.10g')}\n")
    with open(FIX_OI, "w", encoding="utf-8", newline="\n") as f:
        f.write("venue,symbol,asset,margin,day_utc,open_interest_contracts\n")
        for r in oi_rows:
            f.write(f"{r['venue']},{r['symbol']},{r['asset']},{r['margin']},{iso(r['t_ms'])[:10]},{r['oi']:.10g}\n")
    meta = {"built_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "fetcher": "scripts/fetch_perp_funding.py",
            "sources": {"binance": "https://fapi.binance.com/fapi/v1/fundingRate (USDT-margined perpetuals; fundingTime is the settlement)",
                        "bybit": "https://api.bybit.com/v5/market/funding/history (linear = USDT-margined, inverse = coin-margined) and /v5/market/open-interest intervalTime=1d",
                        "okx": "https://www.okx.com/api/v5/public/funding-rate-history (realizedRate; history is shallow, see per-series first/last)"},
            "shape": "TIDY -- one row per (venue, symbol, settlement_utc); funding_rate is the fraction paid per period (0.0001 = 0.01 %); mark_price only where the venue returns it (Binance, later rows)",
            "key": "settlement_utc is the venue's settlement timestamp in UTC; the 00/08/16 UTC grid is the published schedule on every venue here, and off-grid rows are the venue's own interval changes, kept as they were published",
            "rows": len(rows), "oi_rows": len(oi_rows), "series": rep,
            "gates": {"G1": "no duplicate (venue, symbol, settlement)", "G2": "binance BTCUSDT settlements on the 00/08/16 UTC grid >= 95 %", "G3": "binance vs bybit-linear BTC funding on common settlements: Pearson > 0.3",
                      "G4": "no |rate| above 5 % a period", "G5": "no duplicate open-interest rows", "G6": "no negative open interest"},
            "not_fetched": {"binance_openInterestHist": "serves the last 30 days only", "okx_open_interest_history": "Illegal time range beyond the recent window"},
            "licence": "venue public market-data endpoints, no key, no terms restricting redistribution of historical funding rates were presented at fetch; committed as a small derived fixture (D191)"}
    META.write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    log(f"  wrote {FIX.name} ({len(rows)} rows), {FIX_OI.name} ({len(oi_rows)} rows), {META.name}")
    for k, v in rep.items():
        if "rows" in v and v["rows"]:
            log(f"    {k}: {v['rows']} rows {v.get('first', '')} .. {v.get('last', '')}" + (f"  on-grid {v['share_on_8h_grid']:.3f} coverage {v['coverage_of_8h_slots']:.3f} default-share {v['share_exactly_default_0.0001']:.2f} neg {v['share_negative']:.2f}" if "share_on_8h_grid" in v else ""))
        elif k.startswith("G3"):
            log(f"    {k}: {v}")
    return 0


def selftest(log=print):
    """The gates must RAISE on a broken panel."""
    base = [{"venue": "binance", "symbol": "BTCUSDT", "asset": "BTC", "margin": "usdt", "t_ms": EPOCH_START_MS + i * 8 * 3600 * 1000, "rate": 1e-4 * ((i % 3) - 1), "mark": None} for i in range(300)]
    byb = [{**r, "venue": "bybit_linear"} for r in base]
    rep = gates(base + byb, []); assert rep["G3_binance_vs_bybit_linear_BTC"]["pearson"] > 0.99
    def expect_raise(fn, what):
        try:
            fn()
        except AssertionError as e:
            log(f"  gate RAISES on {what}: {str(e)[:60]}"); return
        raise AssertionError(f"gate did not raise on {what}")
    expect_raise(lambda: gates(base + byb + [base[0]], []), "a duplicate row (G1)")
    off = [{**r, "t_ms": r["t_ms"] + 3_600_000} for r in base]; expect_raise(lambda: gates(off + byb, []), "off-grid binance settlements (G2)")
    neg = [{**r, "rate": -r["rate"]} for r in byb]; expect_raise(lambda: gates(base + neg, []), "venues disagreeing (G3)")
    big = [{**base[0], "rate": 0.2}] + base[1:]; expect_raise(lambda: gates(big + byb, []), "a 20 % rate (G4)")
    expect_raise(lambda: gates(base + byb, [{"venue": "bybit_linear", "symbol": "BTCUSDT", "t_ms": 1, "oi": -1.0}]), "negative open interest (G6)")
    log("  selftest: gates pass a clean panel and raise on five breaks"); return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true"); ap.add_argument("--fetch", action="store_true"); ap.add_argument("--build", action="store_true"); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.probe:
        return probe()
    if a.fetch:
        return fetch()
    if a.build:
        return build()
    ap.print_help(); return 1


if __name__ == "__main__":
    sys.exit(main())
