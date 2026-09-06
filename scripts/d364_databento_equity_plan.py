"""D364 -- what US-EQUITY quote and auction data would cost for THIS ledger. OFFLINE. NO KEY, NO NETWORK, NO PURCHASE.

    uv run python scripts/d364_databento_equity_plan.py          arithmetic only; there is no other mode

WHY THIS FILE EXISTS AND WHAT IT IS NOT
---------------------------------------
`scripts/fetch_databento.py` costs a CME FUTURES job. `docs/databento_api.md:186-191` is explicit that **plans
cover CME/CBOT/NYMEX/COMEX only; equities and OPRA are separate products at every tier**, so nothing that script
computes carries over to a US single-name job. This file adds the equity constants, LOCALLY and FLAGGED, and
prices the job the D362 A2 ledger would actually need.

It IMPORTS the API surface, the pricing arithmetic and the helpers from `fetch_databento` rather than copying
them: `unit_price`, `DERIVED_USD_PER_GIB`, `OHLCV_MSG_BYTES`, `BARS_PER_SYMBOL_YEAR`, `FREE_CREDIT_USD`, `BASE`,
`ENDPOINTS`, `ENCODING`, `COMPRESSION`, `config_fingerprint`, `KEY_FILE`, `VERIFY_STAMP`. A second copy of the
$28.00/GiB rate that drifts from the first is exactly the failure that document was written to prevent.

**There is no --verify, no --cost, no --submit here, and no code path that can reach `fetch_databento.call`.**
Asserted: `call` is replaced with a raiser for the whole run ([OFFLINE]). The futures client's own spending gates
are untouched, and `fetch_databento.py --plan` is byte-for-byte the same program it was.

WHAT IS QUOTED, WHAT IS DERIVED, WHAT IS ASSUMED
-------------------------------------------------
The existing client is scrupulous about this and the distinction is the point, so it is kept:

  VERIFIED   read off `docs/databento_api.md`, itself established from three agreeing sources
  DERIVED    computed here from something verified, and wrong if that thing is wrong
  INFERRED   read off the DBN record layout, corroborated but not quoted
  ASSUMED    a number nobody here has measured. **The whole equity costing rests on two of them.**

The two ASSUMED numbers are (a) that a US-equity dataset bills at the SAME $28.00/GiB the GLBX.MDP3 worked
example establishes -- it is a different product, and Databento's unit prices are per-dataset -- and (b) how
many messages a symbol-day of a mid-cap US name carries on each schema. Both are settled EXACTLY and for FREE by
`metadata.list_unit_prices` and `metadata.get_billable_size`. **Neither has ever run, because no API key exists
on this machine.** Every dollar figure below is an estimate until they do, and the script says so on every line.

THE LEDGER PRICED
-----------------
D362's A2 arm, ROW-DROP form: `data/d361_trades_gap_up_fade.csv` rows with `taken_G2 == 1`, less the events hit
by S1 or S2 at `run_d362_sink_filter.SINKS`' own thresholds (S1 pcto_mass_imbalance >= 86.84, S2 mkt_vol_20 <=
99.03; a NaN never hits). That is the row-drop arm, not D363's re-simulated 3,079-trade ledger -- the re-simulated
arm takes a DIFFERENT set of events because removing a position frees its name -- and [A2] asserts the count
against `data/d362_sink_filter.json`'s committed `RD.A2.trades`.

SIZED IN SYMBOL-DAYS, NOT SYMBOL-YEARS. The futures job buys 26 continuous contracts for 16 unbroken years, so
symbol-years is its natural unit. This ledger is ~3,000 (name, day) pairs scattered over fifteen years: 993
distinct names, and for most of them a handful of days each. Charging a symbol-YEAR of quote data for a name we
hold for ten bars would overstate the bill by three orders of magnitude, and a batch job would be built from the
pairs, not from a span.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


FD = _load("fetch_databento_ro", "fetch_databento.py")     # the futures client: imported, never edited, never called
D62 = None                                                 # run_d362_sink_filter is NOT loaded (it drags the whole prep
SINKS = (("S1", "pcto_mass_imbalance", ">=", 86.84),       # chain in); its SINKS tuple is re-read from the source text
         ("S2", "mkt_vol_20", "<=", 99.03),                # below and asserted equal to this literal ([A2]).
         ("S3", "pcto_beta_63", ">=", 87.22),
         ("S4", "pcto_mass_here", "<=", 18.77),
         ("S5", "pcto_gk_minus_cc", "<=", 6.38))
A2_SINKS = ("S1", "S2")

LEDGER = REPO / "data" / "d361_trades_gap_up_fade.csv"
D362_REPORT = REPO / "data" / "d362_sink_filter.json"
DOC = REPO / "docs" / "databento_api.md"

# ---------------------------------------------------------------------------
# THE EQUITY CONSTANTS. Local to this file, because docs/databento_api.md
# documents a FUTURES product and says at :186-191 that equities are separate.
# Every entry tagged, in the tone the futures client uses.
# ---------------------------------------------------------------------------

# UNVERIFIED -- no US-equity dataset code appears anywhere in docs/databento_api.md, which documents GLBX.MDP3
# only. These are the candidates a `metadata.list_datasets` call (GET, FREE, already implemented in
# fetch_databento.ENDPOINTS) would confirm or refute in one request. The choice is not cosmetic: a single-venue
# feed carries only that venue's auctions, and this universe is NYSE and Nasdaq listed both.
EQUITY_DATASETS = (
    ("XNAS.ITCH",  "Nasdaq TotalView-ITCH. Nasdaq-listed auctions only.",                       "UNVERIFIED"),
    ("XNYS.PILLAR", "NYSE Pillar. NYSE-listed auctions only.",                                  "UNVERIFIED"),
    ("DBEQ.BASIC", "a consolidated US equities product; the shape a single job would need.",    "UNVERIFIED"),
    ("EQUS.SUMMARY", "a consolidated summary product, named for completeness.",                 "UNVERIFIED"),
)
DATASET_ASSUMED = "DBEQ.BASIC"     # priced as the consolidated case; the name is UNVERIFIED

# VERIFIED -- docs/databento_api.md:138 names the L1 tier's schemas: "trades, MBP-1, TBBO, BBO". MBP-1 is the
# top-of-book book schema and is the one that carries a quoted spread on every update. `bbo-1s` / `bbo-1m` are
# the subsampled forms; :248 records that whether `bbo-1m` exists AT ALL is STILL UNKNOWN, so nothing here is
# priced on it -- it is named below as the cheaper alternative it would be if it exists.
L1_SCHEMA = "mbp-1"
TRADES_SCHEMA = "trades"           # VERIFIED -- the schema of Databento's own published worked example
BBO_ALTERNATIVE = "bbo-1s"         # UNKNOWN whether the 1-minute sibling exists (docs/databento_api.md:248)

# INFERRED from the DBN record layout, CORROBORATED by the one message size this repo has VERIFIED:
#   RecordHeader = length 1 + rtype 1 + publisher_id 2 + instrument_id 4 + ts_event 8            = 16 B
#   OhlcvMsg     = hd 16 + open/high/low/close 4 x 8 + volume 8                                  = 56 B  <- VERIFIED (FD.OHLCV_MSG_BYTES)
#   TradeMsg     = hd 16 + price 8 + size 4 + action/side/flags/depth 4 + ts_recv 8
#                       + ts_in_delta 4 + sequence 4                                             = 48 B
#   Mbp1Msg      = TradeMsg 48 + one BidAskPair (bid_px 8 + ask_px 8 + bid_sz 4 + ask_sz 4
#                       + bid_ct 4 + ask_ct 4 = 32)                                              = 80 B
# The 16-byte header reproducing the VERIFIED 56 is the corroboration; it is not a quote.
TRADE_MSG_BYTES = 48               # INFERRED
MBP1_MSG_BYTES = 80                # INFERRED

# ASSUMED -- NOBODY HERE HAS MEASURED THESE, and they are the largest source of error in every figure below by a
# wide margin. A symbol-day's message count varies by two orders of magnitude across this universe (the floor is
# $1M median dollar volume, and the events are gap-up days on top-decile relative volume, i.e. the BUSY tail of
# each name's own distribution). Three scenarios are carried rather than one so that the spread is visible.
# `metadata.get_billable_size` (POST, FREE, already implemented) returns the exact byte count for any (symbols,
# schema, start, end) and would replace this entire block with a measurement.
MSGS_PER_SYMBOL_DAY = {
    L1_SCHEMA:      dict(low=50_000,  mid=250_000, high=1_000_000),   # ASSUMED
    TRADES_SCHEMA:  dict(low=5_000,   mid=25_000,  high=100_000),     # ASSUMED
}
SCENARIOS = ("low", "mid", "high")
HEADLINE = "mid"

# VERIFIED -- docs/databento_api.md:138-142, the plan table. L0 reaches 16+ years on the free usage-based tier;
# L1 reaches the LAST 12 MONTHS. Both jobs below are L1.
USAGE_TIER_L1_MONTHS = 12

# INFERRED -- billable size is the UNCOMPRESSED DBN size. Databento's worked example is 99,219,648 bytes for four
# days of ESM2 trades: 99,219,648 / 48 = 2,067,076 TradeMsgs, a sane count for ES, and far larger than the
# zstd-compressed transfer would be. The futures client's own arithmetic (bars x 56 B) assumes the same thing.
BILLABLE_IS_UNCOMPRESSED = True


# ------------------------------------------------------------------ [OFFLINE]
class _Refused(RuntimeError):
    pass


def _no_network(*a, **k):
    raise _Refused("[OFFLINE] this script has no network mode; fetch_databento.call must never be reached")


def assert_OFFLINE(tag="[OFFLINE]"):
    """`call` is replaced for the life of the process and the replacement is proved to raise. The futures client's
    own module object is left otherwise untouched and its file is not written to."""
    FD.call = _no_network
    raised = False
    try:
        FD.call("list_datasets", {}, "not-a-key")
    except _Refused:
        raised = True
    assert raised, f"{tag} the network stub did not raise"
    env = "DATABENTO_API_KEY" in os.environ
    keyfile = FD.KEY_FILE.exists()
    stamp = FD.VERIFY_STAMP.exists()
    return dict(env_key=env, key_file=keyfile, verify_stamp=stamp,
                key_present=bool(env or keyfile))


def assert_IMPORT(tag="[IMPORT]"):
    """The pricing arithmetic is the futures client's, not a second copy: the rate, the message size and the
    bars-per-symbol-year come from FD, and FD.unit_price is exercised on the ARRAY shape the docs record (the
    shape four of this project's earlier assumptions got wrong) so that the parser here and the parser that would
    read a live response are the same function."""
    payload = [{"mode": "batch", "unit_prices": {"trades": 99.0}},
               {"mode": "historical", "unit_prices": {"trades": FD.DERIVED_USD_PER_GIB, "ohlcv-1m": 7.0}}]
    got = FD.unit_price(payload, "trades")
    assert got == FD.DERIVED_USD_PER_GIB, f"{tag} FD.unit_price read {got}"
    assert FD.unit_price({"historical": {"trades": 1.5}}, "trades") == 1.5, f"{tag} the dict shape"
    assert FD.OHLCV_MSG_BYTES == 56 and 16 + 4 * 8 + 8 == FD.OHLCV_MSG_BYTES, \
        f"{tag} the 16-byte header does not reproduce the VERIFIED OhlcvMsg size"
    return dict(rate=FD.DERIVED_USD_PER_GIB, ohlcv_bytes=FD.OHLCV_MSG_BYTES,
                bars_per_symbol_year=FD.BARS_PER_SYMBOL_YEAR, credit=FD.FREE_CREDIT_USD,
                base=FD.BASE, endpoints=len(FD.ENDPOINTS), fingerprint=FD.config_fingerprint())


# ------------------------------------------------------------------ [A2] the ledger
NEED = ("symbol", "row", "bar_entry", "date_entry", "taken_G2", "hold_cap10",
        "pcto_mass_imbalance", "mkt_vol_20", "excluded_reason")


def _f(s):
    return float(s) if s != "" else float("nan")


def _hit(v, op, th):
    if v != v:                       # a NaN never hits
        return False
    return v >= th if op == ">=" else v <= th


def assert_SINKS(tag="[A2]"):
    """The thresholds are run_d362's, not retyped ones: the SINKS tuple literal is read out of the committed
    source text and compared to the copy above. run_d362 itself is not imported -- loading it pulls in the whole
    d348_prep chain, which this offline plan has no use for."""
    src = (REPO / "scripts" / "run_d362_sink_filter.py").read_text(encoding="utf-8")
    i = src.index("SINKS = (")
    j = src.index("\nFEATS", i)
    ns = {}
    exec(src[i:j], ns)                                                   # noqa: S102 -- a tuple literal from a committed file
    assert ns["SINKS"] == SINKS, f"{tag} the local SINKS differ from run_d362_sink_filter.py's:\n  {ns['SINKS']}\n  {SINKS}"
    return ns["SINKS"]


def a2_rows(tag="[A2]"):
    """The A2 row-drop arm out of the committed ledger, and the count asserted against D362's own report."""
    with open(LEDGER, encoding="utf-8", newline="") as f:
        r = csv.reader(f)
        head = next(r)
        ci = {k: head.index(k) for k in NEED}
        rows = [{k: x[ci[k]] for k in NEED} for x in r]
    taken = [x for x in rows if x["taken_G2"] == "1"]
    sink = {nm: (fe, op, th) for nm, fe, op, th in SINKS}
    def hits(x, nm):
        fe, op, th = sink[nm]
        return _hit(_f(x[fe]), op, th)
    n_s1 = sum(1 for x in taken if hits(x, "S1"))
    n_s2 = sum(1 for x in taken if hits(x, "S2"))
    a2 = [x for x in taken if not any(hits(x, nm) for nm in A2_SINKS)]
    stored = json.loads(D362_REPORT.read_text(encoding="utf-8"))["RD"]["A2"]["trades"]
    assert len(a2) == stored, f"{tag} row-drop A2 {len(a2)} != data/{D362_REPORT.name} RD.A2.trades {stored}"
    assert all(x["excluded_reason"] == "" for x in a2), f"{tag} an excluded row reached the arm"
    return a2, dict(rows=len(rows), taken=len(taken), s1=n_s1, s2=n_s2, removed=len(taken) - len(a2),
                    a2=len(a2), stored=stored)


def symbol_days(a2):
    """The (name, bar) pairs a job would have to buy. Bar indices, not dates: the count is what is priced and the
    index identifies a session without needing the calendar. The date SPAN comes from date_entry directly."""
    entry = {(x["row"], int(x["bar_entry"])) for x in a2}
    exit_ = {(x["row"], int(x["bar_entry"]) + int(x["hold_cap10"]) - 1) for x in a2}
    held = set()
    for x in a2:
        b0, h = int(x["bar_entry"]), int(x["hold_cap10"])
        held.update((x["row"], b) for b in range(b0, b0 + h))
    ds = sorted(x["date_entry"] for x in a2)
    cutoff = (date.today() - timedelta(days=365)).isoformat()
    recent = [x for x in a2 if x["date_entry"] >= cutoff]
    r_entry = {(x["row"], int(x["bar_entry"])) for x in recent}
    r_exit = {(x["row"], int(x["bar_entry"]) + int(x["hold_cap10"]) - 1) for x in recent}
    return dict(entry=len(entry), exit=len(exit_), traded=len(entry | exit_), held=len(held),
                names=len({x["symbol"] for x in a2}), trades=len(a2), first=ds[0], last=ds[-1],
                by_year=Counter(d[:4] for d in ds), cutoff=cutoff,
                recent_trades=len(recent), recent_traded=len(r_entry | r_exit))


# ------------------------------------------------------------------ the arithmetic
def price(symbol_day_count, schema, scenario):
    msgs = MSGS_PER_SYMBOL_DAY[schema][scenario]
    per_day_bytes = msgs * (MBP1_MSG_BYTES if schema == L1_SCHEMA else TRADE_MSG_BYTES)
    total_bytes = symbol_day_count * per_day_bytes
    gib = total_bytes / 2 ** 30
    return dict(msgs=msgs, bytes_per_symbol_day=per_day_bytes, bytes=total_bytes, gib=gib,
                usd=gib * FD.DERIVED_USD_PER_GIB)


def do_plan():
    off = assert_OFFLINE()
    imp = assert_IMPORT()
    sinks = assert_SINKS()
    a2, cnt = a2_rows()
    sd = symbol_days(a2)

    print("\nD364 -- US-EQUITY QUOTE AND AUCTION DATA FOR THE A2 LEDGER. OFFLINE PLAN, NOTHING PURCHASED.\n")
    print(f"  [OFFLINE] fetch_databento.call is replaced with a raiser for this whole run and PROVED to raise. "
          f"There is no --verify,\n            --cost or --submit in this file. No socket is opened and no key is read.")
    print(f"            DATABENTO_API_KEY in the environment: {'YES' if off['env_key'] else 'NO'};  "
          f"{FD.KEY_FILE}: {'EXISTS' if off['key_file'] else 'ABSENT'};  "
          f"verify stamp: {'EXISTS' if off['verify_stamp'] else 'ABSENT'}")
    print(f"            => NO API KEY EXISTS ON THIS MACHINE, so `--verify` and `--cost` -- both FREE, both "
          f"already implemented in\n               fetch_databento.py -- have NEVER RUN. Every dollar below is an "
          f"estimate until they do.")
    print(f"\n  [IMPORT]  the arithmetic is fetch_databento's, imported not copied: ${imp['rate']:.2f}/GiB "
          f"(DERIVED there, from Databento's two\n            worked examples on GLBX.MDP3), OhlcvMsg "
          f"{imp['ohlcv_bytes']} B (VERIFIED), {imp['bars_per_symbol_year']:,} bars/symbol-year, "
          f"${imp['credit']:.2f} credit,\n            {imp['endpoints']} endpoints, base {imp['base']}, futures "
          f"config fingerprint {imp['fingerprint']} (unchanged by this file).\n            FD.unit_price parses "
          f"the ARRAY response shape and the dict shape on a probe here, so the plan and the client\n            "
          f"agree on the parser as well as the number.")

    print(f"\n  [A2]      the ledger priced: data/{LEDGER.name}, taken_G2 == 1 less the S1|S2 hits at "
          f"run_d362_sink_filter.SINKS'\n            own thresholds (read out of the committed source and "
          f"compared to the local copy: {len(sinks)} sinks, equal).")
    for nm, fe, op, th in sinks:
        mark = "  <- A2 removes this" if nm in A2_SINKS else ""
        print(f"              {nm}  {fe:24}{op:3}{th:8.2f}{mark}")
    print(f"            {cnt['rows']:,} export rows -> {cnt['taken']:,} taken_G2 trades -> S1 hits {cnt['s1']}, "
          f"S2 hits {cnt['s2']}, {cnt['removed']} removed\n            -> A2 = {cnt['a2']:,} trades == "
          f"data/{D362_REPORT.name} RD.A2.trades {cnt['stored']:,} (asserted). This is the ROW-DROP arm, not "
          f"D363's\n            re-simulated 3,079-trade ledger; the re-simulation takes a different event set "
          f"because a removed position frees its name.")

    print(f"\n  [SIZE]    {sd['trades']:,} trades over {sd['names']} distinct names, {sd['first']} .. {sd['last']}. "
          f"SYMBOL-DAYS, not symbol-years:")
    print(f"              entry sessions (the open auction)   {sd['entry']:>8,} symbol-days")
    print(f"              exit sessions (the close auction)   {sd['exit']:>8,} symbol-days")
    print(f"              distinct traded sessions            {sd['traded']:>8,} symbol-days   <- WHAT THE JOBS BUY")
    print(f"              the whole holding window, for scale {sd['held']:>8,} symbol-days   (every bar of every "
          f"10-bar hold; NOT priced below)")
    yrs = sorted(sd["by_year"].items())
    print(f"            entries by year: {', '.join(f'{y}:{n}' for y, n in yrs)}")
    print(f"            expressed as symbol-YEARS this would be {sd['traded'] / 252.0:.1f} -- the unit the futures "
          f"job uses and the wrong one here:\n            a symbol-year of quotes for a name held ten bars "
          f"overstates the bill by roughly {252 * sd['names'] / sd['traded']:.0f}x.")

    print(f"\n  [PRICE]   two jobs, on {sd['traded']:,} symbol-days each. Dataset {DATASET_ASSUMED} (UNVERIFIED -- "
          f"no equity dataset code appears\n            anywhere in docs/databento_api.md; metadata.list_datasets "
          f"is FREE and settles it).")
    print(f"            encoding {FD.ENCODING}/{FD.COMPRESSION} sent EXPLICITLY (the raw API defaults to csv/none); "
          f"billable size is the UNCOMPRESSED\n            DBN size (INFERRED: 99,219,648 / 48 = 2,067,076 "
          f"TradeMsgs reproduces Databento's own worked example).")
    print(f"\n            job 1  L1 quotes, schema {L1_SCHEMA!r}  -- the spread level. VERIFIED name: "
          f"docs/databento_api.md:138 lists the L1\n                   tier as \"trades, MBP-1, TBBO, BBO\". "
          f"{MBP1_MSG_BYTES} B/message (INFERRED from the DBN layout).")
    print(f"            job 2  trades,     schema {TRADES_SCHEMA!r} -- the auction print at the open and the close. "
          f"{TRADE_MSG_BYTES} B/message (INFERRED).")

    print(f"\n  {'job':7}{'schema':9}{'scenario':10}{'msgs/sym-day':>14}{'B/sym-day':>12}{'sym-days':>10}"
          f"{'GiB':>10}{'USD':>12}")
    tot = {s: 0.0 for s in SCENARIOS}
    for job, schema in ((1, L1_SCHEMA), (2, TRADES_SCHEMA)):
        for s in SCENARIOS:
            d = price(sd["traded"], schema, s)
            tot[s] += d["usd"]
            mark = "  <- headline" if s == HEADLINE else ""
            print(f"  {job:<7}{schema:9}{s + ' ASSUMED':10}{d['msgs']:>14,}{d['bytes_per_symbol_day']:>12,}"
                  f"{sd['traded']:>10,}{d['gib']:>10.1f}{d['usd']:>12,.2f}{mark}")
    print(f"\n  {'TOTAL, both jobs':30}" + "".join(f"{s}: ${tot[s]:,.2f}   " for s in SCENARIOS))
    print(f"  {'HEADLINE (' + HEADLINE + ' scenario)':30}${tot[HEADLINE]:,.2f}   "
          f"less the ${FD.FREE_CREDIT_USD:.2f} new-user credit = ${max(0.0, tot[HEADLINE] - FD.FREE_CREDIT_USD):,.2f} cash")
    print(f"  the low..high spread is {tot['high'] / tot['low']:.0f}x. That is the ASSUMED message rate, not the "
          f"data: get_billable_size is FREE and removes it.")

    print(f"\n  [WINDOW]  BOTH jobs are L1 schemas, and docs/databento_api.md:138-142 gives the usage-based "
          f"($0/mo) tier the LAST\n            {USAGE_TIER_L1_MONTHS} MONTHS of L1 -- against a ledger spanning "
          f"{sd['first']} .. {sd['last']}. On today's window (>= {sd['cutoff']}):")
    r = {schema: price(sd["recent_traded"], schema, HEADLINE) for schema in (L1_SCHEMA, TRADES_SCHEMA)}
    r_tot = sum(d["usd"] for d in r.values())
    print(f"              buyable on the free tier   {sd['recent_trades']:>6,} of {sd['trades']:,} trades "
          f"({sd['recent_trades'] / sd['trades']:.2%}), {sd['recent_traded']:,} symbol-days")
    print(f"              cost of that slice         ${r_tot:,.2f} at the {HEADLINE} scenario "
          f"({L1_SCHEMA} ${r[L1_SCHEMA]['usd']:,.2f} + {TRADES_SCHEMA} ${r[TRADES_SCHEMA]['usd']:,.2f})")
    print(f"            The other {sd['trades'] - sd['recent_trades']:,} trades are NOT PURCHASABLE at $0/mo at "
          f"any price: Standard ($199/mo) or Unlimited\n            ($4,500/mo) is the gate, and that is a "
          f"subscription decision, not a data-volume one.")

    print(f"\n  [FLAGS]   every number above that is not quoted by Databento:")
    for tag, what in (
        ("ASSUMED ", f"${FD.DERIVED_USD_PER_GIB:.2f}/GiB applied to an EQUITY dataset. It is DERIVED for "
                     f"GLBX.MDP3 and unit prices are PER-DATASET;\n                      equities are a separate "
                     f"product at every tier (docs/databento_api.md:186-191). list_unit_prices is FREE."),
        ("ASSUMED ", f"{MSGS_PER_SYMBOL_DAY[L1_SCHEMA][HEADLINE]:,} {L1_SCHEMA} and "
                     f"{MSGS_PER_SYMBOL_DAY[TRADES_SCHEMA][HEADLINE]:,} {TRADES_SCHEMA} messages per symbol-day. "
                     f"Nobody here has measured one.\n                      get_billable_size is FREE and returns "
                     f"the exact byte count."),
        ("INFERRED", f"{MBP1_MSG_BYTES} B/Mbp1Msg and {TRADE_MSG_BYTES} B/TradeMsg, from the DBN layout; "
                     f"corroborated only by the 16-byte header\n                      reproducing the VERIFIED "
                     f"{FD.OHLCV_MSG_BYTES}-byte OhlcvMsg."),
        ("UNVERIFIED", f"the dataset code {DATASET_ASSUMED} and every alternative listed; no equity dataset code "
                       f"appears in this repo's doc."),
        ("UNKNOWN ", f"whether {BBO_ALTERNATIVE}'s 1-minute sibling exists (docs/databento_api.md:248). A "
                     f"subsampled BBO would cut job 1 by\n                      orders of magnitude and is the "
                     f"first thing to ask; nothing here is priced on it."),
        ("UNKNOWN ", "point-in-time symbology. 562 of the fixture's 1,573 names are delisted and this arm holds "
                     "993 names over\n                      fifteen years; a ticker string does not resolve to "
                     "the same instrument across that span. symbology.resolve\n                      is FREE."),
        ("VERIFIED", f"the {USAGE_TIER_L1_MONTHS}-month L1 window on the usage-based tier, and that equities are "
                     f"a separate product (docs/databento_api.md:138-142, :186-191)."),
    ):
        print(f"            {tag}  {what}")
    print(f"\n  Nothing was purchased, nothing was fetched, and nothing here is a book entry (R8). The proposal is\n"
          f"  docs/research/equity-quote-and-auction-data-proposal.md.\n")
    return 0


def main():
    ap = argparse.ArgumentParser(description="offline costing for a US-equity quote and auction job")
    ap.add_argument("--plan", action="store_true", help="the only mode; the default")
    ap.parse_args()
    return do_plan()


if __name__ == "__main__":
    raise SystemExit(main())
