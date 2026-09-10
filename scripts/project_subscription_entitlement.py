"""Everything one month of Databento Standard entitles, priced in bytes and HOURS.

    uv run python scripts/project_subscription_entitlement.py [--json]

THE QUESTION
------------
"How much data can I get out of this subscription that would be useful for any and
all prop trading strategies, if storage were free?"

So storage is removed as a constraint and two others take its place:

  1. THE ENTITLEMENT. Standard for CME Globex MDP 3.0 ($199/mo, verified on
     Databento's pricing page 2026-09-10) includes 16+ years of L0, 12 months of L1,
     and 1 month of L2/L3. That is a hard boundary; more history in those schemas is
     pay-as-you-go on top.
  2. THE PIPE. Measured on this machine at 3.04 MB/s. Thirty days of that, running
     continuously, is about 7.9 TB of COMPRESSED download. That is the real ceiling
     on a one-month strip-mine and it lands in the same order of magnitude as the
     entitlement, which is the finding.

THE MASTER ANCHOR, AND EVERYTHING SCALES OFF IT
-----------------------------------------------
Databento's own published worked example gives ES front-month trades:
`get_billable_size(GLBX.MDP3, ESM2, trades, 2022-06-06 -> 2022-06-10T12:10)` =
99,219,648 bytes, which at 48 B/record is 2,067,076 trades over ~4 sessions, so
~517,000 ES trades per session.

CME Group's own press releases put group-wide ADV at 25.9M contracts (April 2026)
through 41.1M (March 2026). Taking ~30M contracts/session and ~2.5 contracts per
trade gives **~12 million trades per session across all of CME**, futures and options
together. Every L1/L2/L3 figure below is that number times a record size times an
events-per-trade ratio.

WHAT IS MEASURED, ANCHORED, AND ASSUMED
---------------------------------------
MEASURED   record sizes (databento_dbn), zstd 2.60x (real bars in DBN layout),
           3.04 MB/s download, and the CME product census in data/
ANCHORED   ES trades/session, and CME group ADV from CME's own releases
ASSUMED    events per trade for MBP-1, MBP-10 and MBO; the 1-second and 1-minute
           aggregation ratios; instrument counts for definition and statistics.
           THESE CARRY THE BIG SCHEMAS AND THEY ARE THE WEAK PART. Ranges are printed.

**ONE FREE CALL REPLACES THE WHOLE FILE.** `metadata.get_billable_size` takes
ALL_SYMBOLS and any schema, costs nothing, and returns the exact figure. Every number
here is a placeholder for that call and should be discarded the moment a key exists.
Not a study; opens and closes nothing.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "subscription_entitlement.json"

TIB = 1024 ** 4
GIB = 1024 ** 3

# ---- measured on this machine ----
ZSTD_RATIO = 2.60                 # scripts/project_futures_storage.py, on real bars
DOWNLOAD_BYTES_PER_S = 3_040_000  # two 53 MB pulls from files.pythonhosted.org
SUBSCRIPTION_DAYS = 30

# ---- record sizes, from the installed databento_dbn ----
SZ = {"ohlcv": 56, "trades": 48, "mbp1": 80, "bbo": 80, "tbbo": 80,
      "mbp10": 368, "mbo": 56, "definition": 520, "statistics": 80, "status": 40}

# ---- anchors ----
ES_TRADES_PER_SESSION = 517_000        # Databento's published worked example
CME_TRADES_PER_SESSION = 12_000_000    # CME ADV ~30M contracts / ~2.5 per trade
SESSIONS_PER_YEAR = 252
L0_YEARS = 16.26                       # GLBX.MDP3 starts 2010-06-06
L1_YEARS = 1.0                         # Standard includes 12 months of L1
L2_L3_SESSIONS = 21                    # Standard includes 1 month of L2/L3

# ---- ASSUMED ratios. These carry the big schemas. ----
BARS_1M_PER_TRADE = 1 / 12.7    # 12M trades -> ~943k 1-minute bars/session
BARS_1S_PER_TRADE = 0.40        # far weaker aggregation at 1 second
MBP1_PER_TRADE = 25.0           # top-of-book changes per trade
MBP10_PER_TRADE = 75.0          # changes anywhere in the top ten levels
MBO_PER_TRADE = 90.0            # order events per trade
INSTRUMENTS_ALL = 650_000       # Databento's own "650,000+ symbols" for CME
STATS_PER_INSTRUMENT_DAY = 4    # settlement, open, high/low, open interest
RANGE_LO, RANGE_HI = 0.5, 2.0   # the assumed ratios are quoted to a factor of 2

# Usefulness for the prop track, and it is the point of the exercise.
#   core       directly serves hurdle P or an open question in 01-prop-lead
#   valuable   answers something the repo has flagged and never measured
#   once       obtainable ONLY during the subscription month, at any price later
#   skip       large and either derivable from something cheaper or not usable here
ITEMS = [
    # (label, level, bytes_fn_key, usefulness, note)
    ("ohlcv-1m, ALL_SYMBOLS, 16 yr", "L0", "ohlcv1m", "core",
     "the core panel: every root, every contract month, every spread, every option"),
    ("ohlcv-1s, ALL_SYMBOLS, 16 yr", "L0", "ohlcv1s", "excluded",
     "EXCLUDED BY THE PRINCIPAL 2026-09-10: 1-minute bars only"),
    ("ohlcv-1h + 1d, ALL_SYMBOLS, 16 yr", "L0", "ohlcvbig", "skip",
     "derivable from 1m at zero cost; never pull it"),
    ("definition, ALL_SYMBOLS, 16 yr", "L0", "defall", "skip",
     "520 B per instrument PER DAY traded or not; scope it to the roots you keep"),
    ("definition, 41 roots, 16 yr", "L0", "def41", "core",
     "roll calendar, expiries, tick sizes -- the fixture is not buildable without it"),
    ("statistics, ALL_SYMBOLS, 16 yr", "L0", "statall", "valuable",
     "open interest and settlements: rung 3 of the smart-money ladder, free with L0"),
    ("statistics, 41 roots, 16 yr", "L0", "stat41", "core",
     "the same open interest and settlements, scoped -- 150x smaller than ALL_SYMBOLS"),
    ("status, ALL_SYMBOLS, 16 yr", "L0", "status", "valuable",
     "halts and auction states -- what a breach looks like when you cannot exit"),
    ("trades, ALL_SYMBOLS, 12 mo", "L1", "trades", "skip",
     "a strict subset of TBBO; taking both buys the same bytes twice"),
    ("tbbo, ALL_SYMBOLS, 12 mo", "L1", "tbbo", "core",
     "WITH 1s BARS OUT THIS IS THE ONLY 12-MONTH SOURCE OF INTRABAR PATH, plus the spread"),
    ("bbo-1m, ALL_SYMBOLS, 12 mo", "L1", "bbo1m", "valuable",
     "quoted spread by time of day, including the overnight where C1 lives; 1-MINUTE variant"),
    ("mbp-1, ALL_SYMBOLS, 12 mo", "L1", "mbp1", "skip",
     "THE BIGGEST ITEM ON THE LIST and TBBO answers the spread question at 1/25 of it"),
    ("mbp-10, ALL_SYMBOLS, 1 mo", "L2", "mbp10", "skip",
     "Databento's own docs say derive it from MBO; pulling both is waste"),
    ("mbo, ALL_SYMBOLS, 1 mo", "L3", "mboall", "once",
     "the only L3 window that will ever exist without a $4,500/mo plan"),
    ("mbo, ES + NQ only, 1 mo", "L3", "mbo2", "once",
     "the same window scoped to the two symbols the prop track would trade"),
]


def sizes() -> dict[str, float]:
    """Uncompressed (billed) bytes for each item."""
    l0_sess = L0_YEARS * SESSIONS_PER_YEAR
    l1_sess = L1_YEARS * SESSIONS_PER_YEAR
    t = CME_TRADES_PER_SESSION
    es_nq_share = (ES_TRADES_PER_SESSION * 1.85) / t     # ES plus an NQ at ~0.85 of ES
    return {
        "ohlcv1m":  l0_sess * t * BARS_1M_PER_TRADE * SZ["ohlcv"],
        "ohlcv1s":  l0_sess * t * BARS_1S_PER_TRADE * SZ["ohlcv"],
        "ohlcvbig": l0_sess * t * BARS_1M_PER_TRADE * SZ["ohlcv"] * (1 / 60 + 1 / 1380),
        "defall":   l0_sess * INSTRUMENTS_ALL * SZ["definition"],
        "def41":    l0_sess * 41 * 120 * SZ["definition"],
        "statall":  l0_sess * INSTRUMENTS_ALL * STATS_PER_INSTRUMENT_DAY * SZ["statistics"],
        "stat41":   l0_sess * 41 * 120 * STATS_PER_INSTRUMENT_DAY * SZ["statistics"],
        "status":   l0_sess * INSTRUMENTS_ALL * 0.15 * SZ["status"],
        "trades":   l1_sess * t * SZ["trades"],
        "tbbo":     l1_sess * t * SZ["tbbo"],
        "bbo1m":    l1_sess * t * BARS_1M_PER_TRADE * SZ["bbo"],
        "mbp1":     l1_sess * t * MBP1_PER_TRADE * SZ["mbp1"],
        "mbp10":    L2_L3_SESSIONS * t * MBP10_PER_TRADE * SZ["mbp10"],
        "mboall":   L2_L3_SESSIONS * t * MBO_PER_TRADE * SZ["mbo"],
        "mbo2":     L2_L3_SESSIONS * t * es_nq_share * MBO_PER_TRADE * SZ["mbo"],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    S = sizes()
    pipe = DOWNLOAD_BYTES_PER_S * 86400 * SUBSCRIPTION_DAYS

    print(f"pipe: {DOWNLOAD_BYTES_PER_S/1e6:.2f} MB/s x {SUBSCRIPTION_DAYS} days flat out "
          f"= {pipe/TIB:.2f} TiB of COMPRESSED download")
    print(f"zstd {ZSTD_RATIO}x measured, so that is {pipe*ZSTD_RATIO/TIB:.1f} TiB of BILLED volume\n")

    print(f"  {'item':40}{'lvl':>4}{'BILLED TiB':>12}{'DISK TiB':>10}{'HOURS':>8}  use")
    rows = []
    for label, lvl, key, use, note in ITEMS:
        billed = S[key]
        disk = billed / ZSTD_RATIO
        hours = disk / DOWNLOAD_BYTES_PER_S / 3600
        rows.append({"item": label, "level": lvl, "usefulness": use, "note": note,
                     "billed_tib": billed / TIB, "disk_tib": disk / TIB,
                     "download_hours": hours})
        print(f"  {label:40}{lvl:>4}{billed/TIB:12.3f}{disk/TIB:10.3f}{hours:8.1f}  {use}")

    def agg(pred):
        b = sum(r["billed_tib"] for r in rows if pred(r))
        d = sum(r["disk_tib"] for r in rows if pred(r))
        return b, d, d * TIB / DOWNLOAD_BYTES_PER_S / 3600

    # "everything" = the whole entitlement, ignoring the principal's 1-minute rule, so
    # the cost of the rule itself is visible. The scoped duplicates are left out.
    dup = ("definition, 41 roots, 16 yr", "mbo, ES + NQ only, 1 mo")
    everything = agg(lambda r: r["item"] not in dup)
    ex_1s = agg(lambda r: r["item"] not in dup and r["usefulness"] != "excluded")
    useful = agg(lambda r: r["usefulness"] in ("core", "valuable", "once")
                 and r["item"] not in ("definition, ALL_SYMBOLS, 16 yr",
                                       "mbo, ALL_SYMBOLS, 1 mo"))
    core = agg(lambda r: r["usefulness"] == "core")

    # DERIVATION KILLS MOST OF THE LIST. Databento publishes the matrix: MBO derives
    # MBP-10, MBP-1, TBBO, BBO, trades and every OHLCV interval; MBP-1 derives TBBO,
    # BBO, trades and OHLCV. So the honest plan takes the MOST GRANULAR schema in each
    # entitlement window and derives the rest locally, instead of buying the same bytes
    # at four resolutions.
    def by_name(*names):
        b = sum(r["billed_tib"] for r in rows if r["item"] in names)
        d = sum(r["disk_tib"] for r in rows if r["item"] in names)
        return b, d, d * TIB / DOWNLOAD_BYTES_PER_S / 3600

    L0_KEEP = ("ohlcv-1m, ALL_SYMBOLS, 16 yr", "definition, 41 roots, 16 yr",
               "statistics, ALL_SYMBOLS, 16 yr", "status, ALL_SYMBOLS, 16 yr")
    maximal = by_name(*L0_KEEP, "mbp-1, ALL_SYMBOLS, 12 mo", "mbo, ALL_SYMBOLS, 1 mo")
    lean = by_name(*L0_KEEP, "tbbo, ALL_SYMBOLS, 12 mo", "bbo-1m, ALL_SYMBOLS, 12 mo",
                   "mbo, ALL_SYMBOLS, 1 mo")
    # LEAN MAXIMAL: keeps every DISTINCT thing the subscription can give and scopes the
    # two items whose full-universe form is pure bulk. Statistics and MBO carry 81% of
    # the lean bundle purely because ALL_SYMBOLS drags in every option strike; scoped to
    # the roots that would actually be traded they nearly vanish, and nothing the prop
    # track can currently use is lost.
    lean_max = by_name("ohlcv-1m, ALL_SYMBOLS, 16 yr", "definition, 41 roots, 16 yr",
                       "statistics, 41 roots, 16 yr", "tbbo, ALL_SYMBOLS, 12 mo",
                       "bbo-1m, ALL_SYMBOLS, 12 mo", "mbo, ES + NQ only, 1 mo")

    print(f"\n  {'bundle':44}{'BILLED TiB':>12}{'DISK TiB':>10}{'HOURS':>8}{'DAYS':>7}  fits 30d")
    for name, (b, d, h) in (
            ("EVERYTHING the entitlement allows", everything),
            ("everything MINUS 1-second bars", ex_1s),
            ("MAXIMAL USEFUL: L0 + MBP-1 12mo + MBO 1mo", maximal),
            ("LEAN: same but TBBO instead of MBP-1", lean),
            ("LEAN MAXIMAL: every distinct thing, scoped", lean_max),
            ("core only", core)):
        print(f"  {name:44}{b:12.2f}{d:10.2f}{h:8.0f}{h/24:7.1f}  "
              f"{'yes' if d * TIB < pipe else 'NO'}")
    print("\n  MAXIMAL USEFUL takes the most granular schema in each entitlement window and")
    print("  derives the rest: MBO gives MBP-10/MBP-1/TBBO/BBO/trades/OHLCV for its month,")
    print("  MBP-1 gives TBBO/BBO/trades/OHLCV for its year. Nothing is bought twice.")
    print("\n  RISK ON THE ONE BIG LINE: mbp-1 assumes 25 book events per trade, which is a")
    print("  FUTURES ratio. Option market makers requote continuously and ALL_SYMBOLS")
    print("  includes every strike, so mbp-1 at full universe could be several times the")
    print("  figure above. Scope mbp-1 to futures parents and check get_billable_size FIRST.")

    print(f"\n  the assumed ratios are quoted to a factor of {RANGE_HI:.0f}, so the useful extract is")
    print(f"  {useful[1]*RANGE_LO:.2f} to {useful[1]*RANGE_HI:.2f} TiB on disk "
          f"and {useful[2]*RANGE_LO/24:.1f} to {useful[2]*RANGE_HI/24:.1f} days of download")

    if a.json:
        OUT.write_text(json.dumps({
            "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "purpose": "what one month of Databento Standard entitles, in bytes and hours. Not a study.",
            "measured": {"zstd_ratio": ZSTD_RATIO, "download_bytes_per_s": DOWNLOAD_BYTES_PER_S,
                         "record_sizes": SZ},
            "anchors": {"es_trades_per_session": ES_TRADES_PER_SESSION,
                        "cme_trades_per_session": CME_TRADES_PER_SESSION,
                        "cme_adv_source": "CME Group press releases, Apr 2026 25.9M .. Mar 2026 41.1M contracts"},
            "assumed": {"bars_1m_per_trade": BARS_1M_PER_TRADE, "bars_1s_per_trade": BARS_1S_PER_TRADE,
                        "mbp1_per_trade": MBP1_PER_TRADE, "mbp10_per_trade": MBP10_PER_TRADE,
                        "mbo_per_trade": MBO_PER_TRADE, "instruments_all": INSTRUMENTS_ALL,
                        "quoted_to_a_factor_of": RANGE_HI},
            "entitlement": {"L0_years": L0_YEARS, "L1_years": L1_YEARS,
                            "L2_L3_sessions": L2_L3_SESSIONS},
            "pipe": {"bytes_per_s": DOWNLOAD_BYTES_PER_S, "days": SUBSCRIPTION_DAYS,
                     "compressed_tib": pipe / TIB},
            "items": rows,
            "bundles": {"everything": everything, "useful": useful, "core": core},
        }, indent=1) + "\n", encoding="utf-8")
        print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
