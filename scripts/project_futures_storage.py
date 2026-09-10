"""How much DISK a one-month Databento Standard strip-mine would need. NOT a study.

    uv run python scripts/project_futures_storage.py            # measure + project
    uv run python scripts/project_futures_storage.py --json      # write data/futures_storage_projection.json

WHY THIS EXISTS
---------------
`docs/prop firm leads/02-data-acquisition-prompt.md` costs a usage-based fetch. A
one-month Standard subscription ($199/mo for CME Globex MDP 3.0, verified on
Databento's pricing page 2026-09-10) changes the question from "what can we afford"
to "what can we STORE and DOWNLOAD in 30 days" -- and this machine has 162 GB free
on one drive. That is the binding constraint, not the money.

THREE THINGS THAT MOVE THE ANSWER BY AN ORDER OF MAGNITUDE, ALL VERIFIED
------------------------------------------------------------------------
1. **Databento bills UNCOMPRESSED, delivers COMPRESSED.** Their FAQ: data is metered
   "by its uncompressed size in binary encoding", and "your choice of compression
   method doesn't affect cost". So the billed GB and the GB on disk are DIFFERENT
   NUMBERS, and every figure in the purchase proposal is the billed one.

2. **Schemas are derivable from each other.** Databento's schema page publishes the
   derivation matrix: OHLCV from trades, trades+BBO+OHLCV from TBBO, everything below
   MBP-1 from MBP-1. So pulling `ohlcv-1s` AND `ohlcv-1m` AND `trades` for the same
   window is buying the same bytes three times. Pull the most granular schema the
   window needs and derive the rest locally.

3. **Record sizes are FIXED and are read from the installed `databento_dbn`**, not
   from memory: OHLCV 56 B, trades 48 B, MBP-1/BBO/TBBO 80 B, MBP-10 368 B, MBO 56 B,
   definition 520 B, statistics 80 B.

WHAT IS MEASURED HERE AND WHAT IS ASSUMED
-----------------------------------------
**MEASURED:** the zstd ratio, by encoding REAL bars from a committed fixture into the
exact 56-byte DBN OHLCV record layout and compressing them. This is the number the
whole disk projection scales on, and guessing it was not acceptable.

**ANCHORED ON A PUBLISHED WORKED EXAMPLE:** the trade rate. Databento's own docs give
`get_billable_size(GLBX.MDP3, ESM2, trades, 2022-06-06 -> 2022-06-10T12:10)` =
99,219,648 bytes; at 48 B/record that is 2,067,076 trades over ~4 sessions.

**ASSUMED, AND FLAGGED AS SUCH:** the per-symbol liquidity multipliers, and the
MBP-1/MBO event-to-trade ratios. Those last two are order-of-magnitude only -- they
are used solely to show that L1-full and L2/L3 do not fit on this disk, a conclusion
that survives being wrong by 3x in either direction.
"""

from __future__ import annotations

import argparse
import gzip
import io
import json
import struct
from datetime import datetime, timezone
from pathlib import Path

import zstandard as zstd

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "futures_storage_projection.json"
BARS = REPO / "data" / "fixtures" / "index_extended_15m_raw.csv.gz"

GIB = 1024 ** 3

# ---- record sizes, read from the installed databento_dbn (never hardcoded) ----

def record_sizes() -> dict[str, int]:
    import databento_dbn as d
    return {"ohlcv": d.OHLCVMsg.size_hint, "trades": d.TradeMsg.size_hint,
            "mbp1": d.MBP1Msg.size_hint, "bbo": d.BBOMsg.size_hint,
            "tbbo": d.MBP1Msg.size_hint, "mbp10": d.MBP10Msg.size_hint,
            "mbo": d.MBOMsg.size_hint, "definition": d.InstrumentDefMsg.size_hint,
            "statistics": d.StatMsg.size_hint, "status": d.StatusMsg.size_hint}


# ---- the anchor: Databento's own published worked example ----
ANCHOR = {
    "query": "get_billable_size(GLBX.MDP3, ESM2, trades, 2022-06-06 -> 2022-06-10T12:10)",
    "billable_bytes": 99_219_648,
    "sessions_covered": 4.0,     # Mon(partial) Tue Wed Thu + Fri overnight; deliberately conservative
}

SESSIONS_PER_YEAR = 252
MINUTES_PER_SESSION = 1380       # 23h Globex
SECONDS_PER_SESSION = 1380 * 60

# Liquidity relative to ES front month, for trade COUNT. ASSUMED, order-of-magnitude.
# Only used for the L1 window; the L0 projection does not depend on it.
LIQ = {"ES": 1.00, "NQ": 0.85, "RTY": 0.12, "YM": 0.10,
       "MES": 0.30, "MNQ": 0.30, "M2K": 0.05, "MYM": 0.05,
       "CL": 0.45, "NG": 0.20, "GC": 0.30, "SI": 0.10, "HG": 0.08,
       "ZN": 0.35, "ZB": 0.15, "ZF": 0.12,
       # tier 4, the breadth expansion. project_futures_breadth.py measures WHY these
       # are here: within a family the marginal contract is nearly free of information,
       # but a new FAMILY moves the participation ratio a lot.
       "SR3": 0.30, "ZT": 0.15, "UB": 0.10, "TN": 0.05,
       "RB": 0.15, "HO": 0.12, "BZ": 0.10,
       "PL": 0.04, "PA": 0.02,
       "6E": 0.18, "6J": 0.12, "6B": 0.09, "6A": 0.10, "6C": 0.07, "6S": 0.05,
       "ZC": 0.12, "ZS": 0.12, "ZW": 0.08, "ZL": 0.08, "ZM": 0.06,
       "LE": 0.04, "HE": 0.03,
       "NKD": 0.03, "BTC": 0.05, "MBT": 0.02}

# Years of history available per symbol (GLBX.MDP3 starts 2010-06-06; listings differ).
YEARS = {s: 16.26 for s in ("ES", "NQ", "YM", "CL", "NG", "GC", "SI", "HG", "ZN", "ZB", "ZF",
                            "ZT", "UB", "RB", "HO", "BZ", "PL", "PA", "6E", "6J", "6B",
                            "6A", "6C", "6S", "ZC", "ZS", "ZW", "ZL", "ZM", "LE", "HE", "NKD")}
YEARS.update({"RTY": 9.17, "MES": 7.35, "MNQ": 7.35, "M2K": 7.35, "MYM": 7.35,
              "SR3": 8.0, "TN": 10.5, "BTC": 8.7, "MBT": 5.3})

# Fraction of the session's 1-minute slots that actually print a bar. ASSUMED.
# ohlcv-1m has no bar for a minute with no trade, so this is a liquidity read.
FILL_1M = {s: min(0.98, 0.35 + 0.63 * min(1.0, v * 2.5)) for s, v in LIQ.items()}
# Same for 1-second slots -- far lower, since most seconds have no trade.
FILL_1S = {s: min(0.80, 0.04 + 0.70 * min(1.0, v)) for s, v in LIQ.items()}

# Event-to-trade ratios. ASSUMED, order-of-magnitude, used only to size L1-full/L2/L3.
MBP1_PER_TRADE = 25.0
MBO_PER_TRADE = 90.0

TIERS = {1: ["ES", "NQ", "RTY", "YM"],
         3: ["MES", "MNQ", "M2K", "MYM"],
         2: ["CL", "NG", "GC", "SI", "HG", "ZN", "ZB", "ZF"],
         4: ["SR3", "ZT", "UB", "TN", "RB", "HO", "BZ", "PL", "PA",
             "6E", "6J", "6B", "6A", "6C", "6S",
             "ZC", "ZS", "ZW", "ZL", "ZM", "LE", "HE", "NKD", "BTC", "MBT"]}
ALL16 = TIERS[1] + TIERS[3] + TIERS[2]
ALL41 = ALL16 + TIERS[4]

# MEASURED on this machine 2026-09-10, not assumed.
FREE_DISK_GIB = 162.3 * 1e9 / GIB          # 162.3 GB free on C:, the only fixed drive
DOWNLOAD_BYTES_PER_S = 3_040_000           # two 53 MB pulls from PyPI: 3.09 and 2.99 MB/s

# The anchor is June 2022. ES volume has grown since, so a 12-month window ending
# TODAY plausibly carries more trades per session than the anchor does. Every L1
# figure is therefore also reported at this multiplier.
L1_RECENCY_UPLIFT = 1.5

BUNDLES = {
    "A. minimum -- what the three gated items in 01-prop-lead need": [
        "L0 ohlcv-1m, tiers 1+3 only", "L0 definition, 16 symbols, full history",
        "L0 statistics, 16 symbols, full history"],
    "B. core strip-mine -- 16 symbols, every L0 year + the L1 window": [
        "L0 ohlcv-1m, 16 symbols, full history", "L0 ohlcv-1s, 16 symbols, full history",
        "L0 definition, 16 symbols, full history", "L0 statistics, 16 symbols, full history",
        "L1 tbbo, 16 symbols, 12 months"],
    "C. B + one month of full order book on ES": [
        "L0 ohlcv-1m, 16 symbols, full history", "L0 ohlcv-1s, 16 symbols, full history",
        "L0 definition, 16 symbols, full history", "L0 statistics, 16 symbols, full history",
        "L1 tbbo, 16 symbols, 12 months", "L3 mbo, ES only, 1 month"],
    "E. core strip-mine at FULL BREADTH -- 41 symbols": [
        "L0 ohlcv-1m, 41 symbols, full history", "L0 ohlcv-1s, 41 symbols, full history",
        "L0 definition, 16 symbols, full history", "L0 statistics, 16 symbols, full history",
        "L1 tbbo, 41 symbols, 12 months"],
    "F. E + one month of full order book on ES": [
        "L0 ohlcv-1m, 41 symbols, full history", "L0 ohlcv-1s, 41 symbols, full history",
        "L0 definition, 16 symbols, full history", "L0 statistics, 16 symbols, full history",
        "L1 tbbo, 41 symbols, 12 months", "L3 mbo, ES only, 1 month"],
    "D. C + every top-of-book event on ES for a year": [
        "L0 ohlcv-1m, 16 symbols, full history", "L0 ohlcv-1s, 16 symbols, full history",
        "L0 definition, 16 symbols, full history", "L0 statistics, 16 symbols, full history",
        "L1 tbbo, 16 symbols, 12 months", "L3 mbo, ES only, 1 month",
        "L1 mbp-1, ES only, 12 months"],
}


def measure_zstd_ratio() -> dict:
    """Encode REAL bars into the exact DBN OHLCV layout and compress them.

    The DBN OHLCV record is 56 bytes: a 16-byte header (length, rtype, publisher_id,
    instrument_id, ts_event) then open/high/low/close as int64 fixed-point at 1e-9,
    then volume as uint64. Prices and volumes here are real market data, so the
    compressibility measured is the compressibility of real price paths, not of noise.

    CAVEAT, stated rather than buried: these are 15-minute bars, the finest committed
    in this repo. One-minute bars have SMALLER price deltas between consecutive
    records, so real ohlcv-1m compresses at least this well. The ratio is therefore a
    conservative floor for the projection.
    """
    rows = []
    with gzip.open(BARS, "rt") as fh:
        header = fh.readline()
        for line in fh:
            p = line.rstrip("\n").split(",")
            if p[1] != "SPY":
                continue
            ts = datetime.fromisoformat(p[0]).replace(tzinfo=timezone.utc)
            rows.append((int(ts.timestamp() * 1e9), float(p[2]), float(p[3]), float(p[4]),
                         float(p[5]), int(float(p[6]))))
    if len(rows) < 5000:
        raise SystemExit(f"only {len(rows)} bars available; need a real series to measure on")

    buf = io.BytesIO()
    for ts, o, h, lo, c, v in rows:
        buf.write(struct.pack("<BBHIq", 56 // 4, 0x22, 1, 12345, ts))
        buf.write(struct.pack("<qqqq", *(int(round(x * 1e9)) for x in (o, h, lo, c))))
        buf.write(struct.pack("<Q", v))
    raw = buf.getvalue()
    assert len(raw) == 56 * len(rows), (len(raw), len(rows))

    out = {"bars_encoded": len(rows), "uncompressed_bytes": len(raw), "levels": {}}
    for lvl in (3, 9, 19):
        comp = zstd.ZstdCompressor(level=lvl).compress(raw)
        out["levels"][str(lvl)] = {"compressed_bytes": len(comp),
                                   "ratio": len(raw) / len(comp),
                                   "bytes_per_record": len(comp) / len(rows)}
    out["ratio_used"] = out["levels"]["3"]["ratio"]   # zstd default, what a client sends
    return out


def project(sizes: dict[str, int], ratio: float) -> dict:
    trades_per_session_es = ANCHOR["billable_bytes"] / sizes["trades"] / ANCHOR["sessions_covered"]

    def l0_bytes(syms, per_session_slots, fill):
        """ohlcv at some interval, over each symbol's full available history."""
        return sum(YEARS[s] * SESSIONS_PER_YEAR * per_session_slots * fill[s] * sizes["ohlcv"]
                   for s in syms)

    def l1_bytes(syms, months, rec_size, per_trade=1.0):
        yrs = months / 12.0
        return sum(yrs * SESSIONS_PER_YEAR * trades_per_session_es * LIQ[s] * per_trade * rec_size
                   for s in syms)

    def row(label, uncompressed, note="", is_l1=False):
        return {"item": label, "billed_gib": uncompressed / GIB,
                "disk_gib": uncompressed / ratio / GIB, "is_l1": is_l1, "note": note}

    items = {
        "L0 ohlcv-1m, 16 symbols, full history": row(
            "ohlcv-1m x16", l0_bytes(ALL16, MINUTES_PER_SESSION, FILL_1M),
            "the core fixture; 226 symbol-years"),
        "L0 ohlcv-1m, tiers 1+3 only": row(
            "ohlcv-1m x8", l0_bytes(TIERS[1] + TIERS[3], MINUTES_PER_SESSION, FILL_1M),
            "what the three gated measurements actually need"),
        "L0 ohlcv-1s, 16 symbols, full history": row(
            "ohlcv-1s x16", l0_bytes(ALL16, SECONDS_PER_SESSION, FILL_1S),
            "60x the slots of 1m, but most seconds never trade"),
        "L0 ohlcv-1s, tiers 1+3 only": row(
            "ohlcv-1s x8", l0_bytes(TIERS[1] + TIERS[3], SECONDS_PER_SESSION, FILL_1S),
            "intrabar path for MAE, which is the whole prop question"),
        "L0 definition, 16 symbols, full history": row(
            "definition", 16 * 40 * YEARS["ES"] * SESSIONS_PER_YEAR * sizes["definition"],
            "~40 live contract months per root per day; the roll calendar lives here"),
        "L0 statistics, 16 symbols, full history": row(
            "statistics", 16 * 40 * YEARS["ES"] * SESSIONS_PER_YEAR * 6 * sizes["statistics"],
            "open interest + settlements; rung 3 of the smart-money ladder"),
        "L1 tbbo, 16 symbols, 12 months": row(
            "tbbo x16 12mo", l1_bytes(ALL16, 12, sizes["tbbo"]),
            "every trade WITH the BBO before it: spread + trades + all OHLCV", True),
        "L1 tbbo, ES+NQ only, 12 months": row(
            "tbbo ES+NQ 12mo", l1_bytes(["ES", "NQ"], 12, sizes["tbbo"]),
            "the two symbols the spread question is actually about", True),
        "L1 trades, 16 symbols, 12 months": row(
            "trades x16 12mo", l1_bytes(ALL16, 12, sizes["trades"]),
            "REDUNDANT if tbbo is taken -- trades derives from it", True),
        "L1 mbp-1, ES only, 12 months": row(
            "mbp-1 ES 12mo", l1_bytes(["ES"], 12, sizes["mbp1"], MBP1_PER_TRADE),
            f"ASSUMED {MBP1_PER_TRADE:.0f} book events per trade", True),
        "L3 mbo, ES only, 1 month": row(
            "mbo ES 1mo", l1_bytes(["ES"], 1, sizes["mbo"], MBO_PER_TRADE),
            f"ASSUMED {MBO_PER_TRADE:.0f} order events per trade", True),
        "L0 ohlcv-1m, 41 symbols, full history": row(
            "ohlcv-1m x41", l0_bytes(ALL41, MINUTES_PER_SESSION, FILL_1M),
            "the breadth expansion; see project_futures_breadth.py"),
        "L0 ohlcv-1s, 41 symbols, full history": row(
            "ohlcv-1s x41", l0_bytes(ALL41, SECONDS_PER_SESSION, FILL_1S),
            "added roots are far less liquid, so far fewer seconds print"),
        "L1 tbbo, 41 symbols, 12 months": row(
            "tbbo x41 12mo", l1_bytes(ALL41, 12, sizes["tbbo"]),
            "scales with TRADES, so the thin added roots cost little", True),
    }

    bundles = {}
    for name, keys in BUNDLES.items():
        disk = sum(items[k]["disk_gib"] for k in keys)
        billed = sum(items[k]["billed_gib"] for k in keys)
        disk_hi = sum(items[k]["disk_gib"] * (L1_RECENCY_UPLIFT if items[k]["is_l1"] else 1.0)
                      for k in keys)
        bundles[name] = {
            "items": keys, "billed_gib": billed, "disk_gib": disk, "disk_gib_uplifted": disk_hi,
            "free_disk_gib_after": FREE_DISK_GIB - disk_hi,
            "fits": disk_hi < FREE_DISK_GIB * 0.85,
            "download_hours": disk_hi * GIB / DOWNLOAD_BYTES_PER_S / 3600,
        }
    return {"trades_per_session_es": trades_per_session_es, "items": items, "bundles": bundles}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    sizes = record_sizes()
    print("DBN record sizes, read from the installed databento_dbn:")
    print("  " + "  ".join(f"{k}={v}B" for k, v in sizes.items()))

    z = measure_zstd_ratio()
    print(f"\nzstd ratio MEASURED on {z['bars_encoded']:,} real bars encoded in DBN layout:")
    for lvl, d in z["levels"].items():
        print(f"  level {lvl:>2}: {d['ratio']:.2f}x  ({d['bytes_per_record']:.1f} B/record on disk)")
    ratio = z["ratio_used"]

    p = project(sizes, ratio)
    print(f"\nES trades/session from the published worked example: {p['trades_per_session_es']:,.0f}")
    print(f"\n{'item':44}{'BILLED GiB':>12}{'DISK GiB':>10}   note")
    for _k, r in p["items"].items():
        print(f"  {r['item']:42}{r['billed_gib']:12.1f}{r['disk_gib']:10.1f}   {r['note'][:52]}")

    print(f"\nfree disk MEASURED: {FREE_DISK_GIB:.0f} GiB   "
          f"download MEASURED: {DOWNLOAD_BYTES_PER_S/1e6:.2f} MB/s")
    print(f"L1 rows are also carried at {L1_RECENCY_UPLIFT}x, because the trade-rate anchor is June 2022\n")
    print(f"  {'bundle':52}{'BILLED':>8}{'DISK':>7}{'+L1x1.5':>9}{'left':>7}{'hours':>7}  fits")
    for name, b in p["bundles"].items():
        print(f"  {name:52}{b['billed_gib']:8.0f}{b['disk_gib']:7.0f}{b['disk_gib_uplifted']:9.0f}"
              f"{b['free_disk_gib_after']:7.0f}{b['download_hours']:7.1f}  "
              f"{'yes' if b['fits'] else 'NO'}")

    if a.json:
        OUT.write_text(json.dumps({
            "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "purpose": "disk projection for a one-month Databento Standard strip-mine; not a study",
            "record_sizes_bytes": sizes, "zstd": z, "anchor": ANCHOR,
            "measured_on_this_machine": {
                "free_disk_gib": FREE_DISK_GIB, "download_bytes_per_s": DOWNLOAD_BYTES_PER_S,
                "download_note": "two 53 MB pulls from files.pythonhosted.org, 3.09 and 2.99 MB/s"},
            "assumed": {"liquidity_vs_ES": LIQ, "mbp1_events_per_trade": MBP1_PER_TRADE,
                        "mbo_events_per_trade": MBO_PER_TRADE, "l1_recency_uplift": L1_RECENCY_UPLIFT,
                        "fill_1m": FILL_1M, "fill_1s": FILL_1S},
            "years_available": YEARS, "projection": p,
        }, indent=1) + "\n", encoding="utf-8")
        print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
