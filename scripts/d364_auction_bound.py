"""D364 -- the auction bound: what the fade's fills would actually be a share OF.

D363 measured participation against the WHOLE DAY's dollar volume and got 0.0386% at $25k a position (median, entry bar). That is the wrong
denominator. The strategy's two fills are the OPENING print of the entry bar and the CLOSING print of the exit bar, and both are auction
prints. One-minute bars do not isolate an auction, but the 09:30 bar and the 16:00 bar are each "the auction print plus one minute of
continuous trade", so they are a hard UPPER BOUND on the auction's own size -- and therefore the first real bound on participation.

MEASUREMENT ONLY, in the shape of D339's census. NOTHING IS PREDICTED, NO CELL IS SCORED, NO RULE IS PROPOSED, NOTHING IS PROMOTED.

    uv run python scripts/d364_auction_bound.py --selftest
    uv run python scripts/d364_auction_bound.py --plan          no network; writes the sample BEFORE anything is fetched
    uv run python scripts/d364_auction_bound.py --probe         ONE (symbol, month); settles whether a 16:00 bar exists at all
    uv run python scripts/d364_auction_bound.py --fetch         the rest; resumable, refuses to start until the probe has passed
    uv run python scripts/d364_auction_bound.py --report
    --out-dir DIR   (every stage; default data/ -- a smoke run passes temp/... so that nothing under data/ is touched. --report and --fetch
                     read the sample / probe from --out-dir if it is there and from data/ otherwise, and say which.)

THE SAMPLE (--plan, no network)
    THE A2 ARM, RECONSTRUCTED FROM THE COMMITTED EXPORT and nothing else: data/d361_trades_gap_up_fade.csv rows with taken_G2 == 1, minus
    D362's two sinks S1 (pcto_mass_imbalance >= 86.84) and S2 (mkt_vol_20 <= 99.03) -- the thresholds are READ from
    run_d362_sink_filter.SINKS, never typed here. A NaN never hits (the export writes '' for NaN and '' never satisfies a comparison).

    THIS IS D362's ROW-DROP A2 (3,028 trades, mean +60.9727), NOT its re-simulated A2 arm (3,079 trades, mean +61.7083). The task's spec
    named the row-drop construction and the re-simulated arm's numbers; they are different objects and cannot both be asserted. [S] asserts
    the reconstruction EXACTLY against data/d362_sink_filter.json's stored `RD.A2` (which is what this construction is) and REPORTS the gap
    to the stored re-simulated `results.A2.per_trade` beside it. The difference is the slot book: removing an event frees a slot and a
    different event takes it, so re-simulating admits 51 trades the row-drop does not. For a participation measurement the difference is
    immaterial -- it is a measurement of the tape, not of the ledger -- and it is stated rather than hidden.

    STRATA: rank-based equal-count quintiles of the trade's own `half_spread_PUB_bp` (the export's column), 0 tightest .. 4 widest, ties by
    ledger order -- D363's `quintiles` rule on D363's quantity. THE BINS ARE CUT OVER ALL 3,028 A2 TRADES, and the draw is then made from the
    eligible subset within each bin, so a bin means the same thing here as it does in D363 rather than meaning "a fifth of the survivors".

    ELIGIBILITY IS A PROVIDER FACT, NOT A PREFERENCE: TIME_SERIES_INTRADAY serves NOTHING for a delisted ticker (PICKUP.md, probed
    2026-09-01, four for four). So the sample is restricted to status_meta in {survived, collapsed} -- still listed at the span end -- and
    IS THEREFORE SURVIVOR-ONLY AND TILTED TOWARD THE LIQUID HALF. --plan measures the size of that tilt (how many A2 trades are excluded,
    and how their gross mean and half-spread compare to the kept ones) instead of asserting it.

    THE DRAW: numpy.random.default_rng(364) permutes each quintile's eligible trades ONCE; the sample is the first K of each, with K the
    largest value whose DISTINCT (symbol, month) request count is <= MAX_REQUESTS. Alpha Vantage bills one request per (symbol, month), and
    a trade needs two months (its entry month and its exit month, which are usually but not always the same), so the trade count and the
    request count are different quantities and only the second is billed.

THE BARS (--probe, --fetch)
    TIME_SERIES_INTRADAY, interval=1min, outputsize=full, adjusted=false, extended_hours=true, month=YYYY-MM, one request per (symbol,
    month), cached under data/raw/alphavantage/1min/ (gitignored, D191) with a provenance _meta.json. The client, the key handling (env then
    ~/.config/alphavantage/key, never printed), the 66/min pacing under the 75 ceiling, the structural success test and the resumability are
    fetch_etf_intraday's, imported and not reimplemented (D212); the ONE thing changed is the module's INTERVAL, which both fetch_slice and
    slice_path read, so the 1-minute cache lands in its own tree and cannot collide with the 15-minute one. Asserted, not assumed.

    extended_hours=true IS LOAD-BEARING HERE, unlike in the 15-minute fetchers where it was merely free. A 1-minute regular session runs
    09:30..15:59 stamped at the interval OPEN; THE CLOSING AUCTION PRINTS AT 16:00, which is outside that window. The whole measurement is
    the size of that bar. --probe settles it on one name before 150 requests are spent, and --fetch REFUSES to run until the probe has
    passed. If the 16:00 bar is absent the answer is to stop and say so, never to substitute 15:59.

THE MEASUREMENT (--report)
    Per sampled trade: the fill at the OPEN of the entry bar t (the export's bar_entry / date_entry) and the fill at the CLOSE of the exit
    bar e = t + hold_cap10 - 1 (the export's own hold; 3,015 of 3,028 A2 trades hold the full 10, so e is almost always t + 9). The bar index
    -> date map is the fixture's union calendar, derived by streaming data/fixtures/us_shorts_daily_raw.csv.gz and CHECKED against every one
    of the export's 49,500 (bar, date) pairs ([AX]) rather than trusted.
      opening-minute dollar volume = close x volume of the 09:30 bar on the ENTRY date
      closing-minute dollar volume = close x volume of the 16:00 bar on the EXIT date
      whole-day dollar volume      = close x volume of the daily fixture's bar on the same date (D363's denominator, reproduced)
    participation = position / denominator at $10k, $25k, $50k; median, p90, p99, share above 1% and above 5%; both denominators printed side
    by side; the ratio minute/day reported with its quartiles -- THAT RATIO IS THE FINDING. Split by the PUB half-spread quintile, because
    D363 found the edge in the widest quintile and those are the thinnest names.

    A NOTE ON FRAMES. The daily fixture is SPLIT-ADJUSTED (prices divided, volumes multiplied by the same factor) and the 1-minute bars are
    AS-TRADED (adjusted=false). Share volume therefore differs by the split factor across a split; DOLLAR volume does not, because the factor
    cancels. Every participation number here is a dollar-volume ratio and is split-invariant. [REC] reports the share-volume ratio (the
    quantity the task names) and the dollar-volume ratio beside it, precisely so that a split shows up as a discrepancy in one and not the
    other instead of being smoothed away.

ASSERTIONS
    [HOLDOUT-GUARD] an audit hook on every file open in the process refuses any path containing 'holdout' before the file is touched, and is
                    probed with a non-existent holdout path so that it cannot be a check that passes vacuously.
    [AX]  the derived bar->date axis reproduces every (bar_g, date_g) and (bar_entry, date_entry) pair in the export.
    [S]   the reconstructed arm IS D362's row-drop A2, to 1e-9 on the mean and exactly on the count, against data/d362_sink_filter.json;
          the gap to the stored re-simulated arm is reported, not asserted away.
    [K]   --report reads the sample --plan wrote: the file's payload hash matches the hash recorded inside it, and the sample's own
          derivation (trades, quintiles, seed) is re-derived from the export and compared row for row.
    [TZ]  the payload states its timezone (US/Eastern) and its stamps are the interval's OPEN -- stated as the fixture metas state it, and
          checked against the bars: a regular session's first stamp is 09:30 and no regular-hours stamp exceeds 16:00.
    [REC] the summed 1-minute regular-session volume against the daily fixture's volume for the same (symbol, date): the per-name ratio, its
          median and its range, and EVERY symbol outside [0.8, 1.2] named. The consolidated tape and the intraday endpoint need not agree
          exactly; the point is to know by how much. The assertion is on the MEDIAN (a single disagreeing name is a report, not a failure).
    [6]   [REC] raises on a perturbed volume -- both globally (every minute volume scaled) and, for the naming half, on one (symbol, date).

WHAT THIS RECORD DOES NOT DO: it does not re-score the arm, it does not re-cost it, it does not touch a holdout, and it does not say whether
the strategy is tradeable. It measures a denominator.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.util
import json
import math
import os
import sys
import time
import urllib.error
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]

# ------------------------------------------------------------------ the holdout guard, installed before any other module of this file runs
_OPENED = dict(n=0, fixtures=Counter(), refused=0)


def _audit(event, args):
    if event != "open":
        return
    p = args[0]
    if isinstance(p, bytes):
        p = p.decode(errors="replace")
    elif not isinstance(p, (str, os.PathLike)):
        return
    s = os.fspath(p)
    low = s.replace("\\", "/").lower()
    _OPENED["n"] += 1
    if "holdout" in low:
        _OPENED["refused"] += 1
        raise RuntimeError(f"[HOLDOUT-GUARD] refused to open {s}")
    if "data/fixtures/" in low:
        _OPENED["fixtures"][low.rsplit("/", 1)[-1]] += 1


sys.addaudithook(_audit)


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


# The fetcher. fetch_etf_intraday owns the client, the key, the pacing, the structural success test and the cache layout; every one of those
# is IDENTICAL for this study. The ONE constant that differs is the interval, and it is a module global that both `fetch_slice` (the
# `interval=` parameter) and `slice_path` (the cache directory) read at call time -- so setting it here changes both together, which is
# exactly what must not be allowed to drift apart. Asserted below rather than trusted, and the 15-minute cache is untouched by construction.
E = _load("d364_av", "fetch_etf_intraday.py")
_AV_INTERVAL_15M = E.INTERVAL
E.INTERVAL = "1min"
assert E.INTERVAL == "1min" and _AV_INTERVAL_15M == "15min", "the AV interval override did not take"
assert E.slice_path("SPY", "2024-01").parent.parent.name == "1min", "slice_path did not follow the interval override"

# ------------------------------------------------------------------ constants
STUDY = 364
SEED = 364
DATA = REPO / "data"
FIXTURE = DATA / "fixtures" / "us_shorts_daily_raw.csv.gz"
EXPORT_CSV, EXPORT_GZ = DATA / "d361_trades_gap_up_fade.csv", DATA / "d361_trades_gap_up_fade.csv.gz"
D362_REPORT = DATA / "d362_sink_filter.json"
SAMPLE_NAME = "d364_auction_sample.json"
PROBE_NAME = "d364_probe.json"
REPORT_NAME = "d364_auction_bound.json"

MAX_REQUESTS = 150                 # distinct (symbol, month) pairs; Alpha Vantage bills one request per pair
POSITIONS = (10_000, 25_000, 50_000)
N_QUINTILES = 5
LIVE_STATUS = ("survived", "collapsed")     # TIME_SERIES_INTRADAY serves nothing for a delisted ticker
OPEN_STAMP, CLOSE_STAMP = "09:30", "16:00"
RTH_FIRST, RTH_LAST_CONT, RTH_AUCTION = "09:30", "15:59", "16:00"
REC_BAND = (0.8, 1.2)             # the REPORTING band: a pair outside it is named
REC_HARD = (0.5, 2.0)             # the ASSERTED band, on the split-invariant dollar ratio's MEDIAN: outside it is a keying error
MAX_UNSERVED = 20

SINK_SOURCE = "scripts/run_d362_sink_filter.py"
STORED = dict(rd_trades=3_028, rd_mean_bp=60.972681756848560, resim_trades=3_079, resim_mean_bp=61.70833763090267)


# THE THRESHOLDS ARE READ, NEVER TYPED. run_d362_sink_filter owns them, but IMPORTING it pulls the whole D361/D360/D359/D353/D350/D349
# chain in -- minutes and gigabytes -- and this file needs four numbers and two strings from it. So SINKS is parsed out of that module's
# SOURCE (a single literal tuple assignment, exec'd in an empty namespace), and --selftest cross-checks the parse against the INDEPENDENT
# copy D362's committed result file records in its own `sinks` block. Two artefacts, one number: if either moves, this file stops.
def sinks_from_source():
    """S1 and S2 out of run_d362_sink_filter.py's SINKS, by source, so no stage of this file costs a chain load."""
    src = (REPO / SINK_SOURCE).read_text(encoding="utf-8")
    i = src.index("\nSINKS = ")
    j = src.index("\nFEATS", i)
    ns: dict = {}
    exec(src[i:j], ns)                                            # a single literal tuple assignment, nothing else in scope
    s = {nm: (feat, op, th) for nm, feat, op, th in ns["SINKS"]}
    return (("S1",) + s["S1"], ("S2",) + s["S2"])


D363_REPORT = DATA / "d363_cost_lines.json"


def d363_participation():
    """D363's stored participation block, read rather than retyped. Absent -> None (a smoke run may not have it)."""
    if not D363_REPORT.exists():
        return None
    return json.loads(D363_REPORT.read_text()).get("participation")


def sinks_from_d362_report():
    """The same two sinks as D362's committed RESULT records them -- a second, independent artefact for the same numbers."""
    d = json.loads(D362_REPORT.read_text())["sinks"]
    s = {x["name"]: (x["feature"], x["op"], x["threshold"]) for x in d}
    return (("S1",) + s["S1"], ("S2",) + s["S2"])


S1S2 = sinks_from_source()


# ------------------------------------------------------------------ small helpers
def out_paths(out_dir):
    d = Path(out_dir)
    return dict(dir=d, sample=d / SAMPLE_NAME, probe=d / PROBE_NAME, report=d / REPORT_NAME)


def find_input(out_dir, name):
    """An input written by an earlier stage: --out-dir first, then data/. Returns (path, where) or (None, None)."""
    p = Path(out_dir) / name
    if p.exists():
        return p, "out-dir"
    q = DATA / name
    if q.exists():
        return q, "data/"
    return None, None


def guard_line():
    fx = _OPENED["fixtures"]
    return (f"{_OPENED['n']:,} file opens audited in this process, {sum(fx.values())} under data/fixtures "
            f"({', '.join(f'{k} x{v}' for k, v in sorted(fx.items())) or 'none'}); "
            f"none containing 'holdout' opened ({_OPENED['refused']} refused: the probe)")


def assert_HOLDOUT_GUARD(tag="[HOLDOUT-GUARD]"):
    probe = DATA / "fixtures" / "holdout_probe_that_does_not_exist.txt"
    assert not probe.exists()
    raised = False
    try:
        open(probe, "r")
    except RuntimeError as e:
        raised = tag in str(e)
    except OSError:
        raised = False
    assert raised, f"{tag} the audit hook did not refuse a holdout path"
    assert not any("holdout" in k for k in _OPENED["fixtures"]), f"{tag} a holdout fixture was opened"
    return guard_line()


def payload_hash(obj):
    """sha256 over the canonical JSON of everything but the hash field itself."""
    d = {k: v for k, v in obj.items() if k != "payload_sha256"}
    return hashlib.sha256(json.dumps(d, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def clean(x):
    """No bare NaN/Infinity in a written artefact -- `NaN` is not JSON and a strict reader chokes on it. A missing number is null."""
    if isinstance(x, dict):
        return {k: clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [clean(v) for v in x]
    if isinstance(x, (np.floating, float)):
        return float(x) if math.isfinite(float(x)) else None
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.bool_,)):
        return bool(x)
    return x


def dump(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    obj = clean(obj)
    obj["payload_sha256"] = payload_hash(obj)
    Path(path).write_text(json.dumps(obj, indent=1, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return obj["payload_sha256"]


def stats_of(x):
    a = np.asarray(x, float)
    f = a[np.isfinite(a)]
    if not f.size:
        return dict(n=0, median=None, p25=None, p75=None, p90=None, p99=None, mean=None, min=None, max=None)
    return dict(n=int(f.size), median=float(np.median(f)), p25=float(np.quantile(f, .25)), p75=float(np.quantile(f, .75)),
                p90=float(np.quantile(f, .90)), p99=float(np.quantile(f, .99)), mean=float(f.mean()), min=float(f.min()), max=float(f.max()))


# ------------------------------------------------------------------ the date axis and the daily fixture
def scan_fixture(want_keys=None):
    """One pass over the daily fixture: the union date axis, and (close, volume) for the wanted (symbol, date) keys.

    Streamed rather than loaded -- 4.1M rows, and this file needs a few hundred of them plus a 4,187-element index."""
    dates, bars = set(), {}
    want = want_keys or set()
    with gzip.open(FIXTURE, "rt", newline="") as f:
        r = csv.reader(f)
        head = next(r)
        c = {k: head.index(k) for k in ("timestamp", "symbol", "close", "volume")}
        for row in r:
            d = row[c["timestamp"]][:10]
            dates.add(d)
            k = (row[c["symbol"]], d)
            if k in want:
                assert k not in bars, f"[FIX] duplicate daily bar {k}"
                bars[k] = (float(row[c["close"]]), float(row[c["volume"]]))
    return sorted(dates), bars


def assert_AX(ax, rows, cols, tag="[AX]"):
    """Every (bar_g, date_g) and (bar_entry, date_entry) pair in the WHOLE export sits at its index in the derived axis."""
    n = 0
    for row in rows:
        for b, d in ((cols["bar_g"], cols["date_g"]), (cols["bar_entry"], cols["date_entry"])):
            k = int(row[b])
            assert 0 <= k < len(ax) and ax[k] == row[d][:10], f"{tag} bar {k} is {ax[k] if k < len(ax) else 'out of range'}, the export says {row[d][:10]}"
            n += 1
    return dict(pairs=n, axis=len(ax), first=ax[0], last=ax[-1])


# ------------------------------------------------------------------ the arm, rebuilt from the committed export
EXPORT_COLS = ("symbol", "row", "bar_g", "date_g", "bar_entry", "date_entry", "hold_cap10", "taken_G2", "pnl_cap10_bp_G2",
               "half_spread_PUB_bp", "half_spread_PB_bp", "status_meta", "dollar_vol_g", "era", "year",
               S1S2[0][1], S1S2[1][1])


def read_export():
    src = EXPORT_CSV if EXPORT_CSV.exists() else EXPORT_GZ
    f = open(src, encoding="utf-8", newline="") if src.suffix == ".csv" else gzip.open(src, "rt", encoding="utf-8", newline="")
    with f:
        r = csv.reader(f)
        head = next(r)
        cols = {c: head.index(c) for c in EXPORT_COLS}
        rows = list(r)
    return rows, cols, src.name


def fnum(row, cols, c):
    """The export writes '' for NaN. Never silently zero."""
    v = row[cols[c]]
    return float(v) if v != "" else float("nan")


def hits(row, cols):
    """S1 / S2 on one export row. '' is the export's NaN and never satisfies a comparison -- the pre-registration's 'a NaN never hits'."""
    out = []
    for _nm, feat, op, th in S1S2:
        v = row[cols[feat]]
        if v == "":
            out.append(False)
            continue
        x = float(v)
        out.append(x >= th if op == ">=" else x <= th)
    return out


def a2_arm(rows, cols, ax):
    """taken_G2 == 1 minus S1 | S2, in the export's row order (which is the ledger's)."""
    tr = []
    for j, row in enumerate(rows):
        if row[cols["taken_G2"]] != "1":
            continue
        if any(hits(row, cols)):
            continue
        t = int(row[cols["bar_entry"]])
        hold = int(row[cols["hold_cap10"]])
        e = t + hold - 1
        tr.append(dict(csv_row=j, symbol=row[cols["symbol"]], row=int(row[cols["row"]]), bar_g=int(row[cols["bar_g"]]), bar_entry=t,
                       date_entry=row[cols["date_entry"]][:10], hold=hold, bar_exit=e, date_exit=ax[e],
                       gross_bp=fnum(row, cols, "pnl_cap10_bp_G2"), pub_bp=fnum(row, cols, "half_spread_PUB_bp"),
                       pb_bp=fnum(row, cols, "half_spread_PB_bp"), status=row[cols["status_meta"]],
                       dollar_vol_g=fnum(row, cols, "dollar_vol_g"), era=int(row[cols["era"]]), year=int(row[cols["year"]])))
    assert all(math.isfinite(t["gross_bp"]) and math.isfinite(t["pub_bp"]) for t in tr), \
        "an A2 trade has no P&L or no PUB half-spread -- the strata and the arm mean would both be silently wrong"
    return tr


def assert_S(tr, tol=1e-9, tag="[S]"):
    """The reconstruction IS D362's stored row-drop A2 -- count exactly, mean to tol -- and the gap to the stored re-simulated arm is
    reported. Both numbers come from data/d362_sink_filter.json; neither is typed."""
    d = json.loads(D362_REPORT.read_text())
    rd, pt = d["RD"]["A2"], d["results"]["A2"]["per_trade"]
    g = np.array([t["gross_bp"] for t in tr])
    m = float(g.mean())
    assert len(tr) == rd["trades"] == STORED["rd_trades"], f"{tag} {len(tr):,} trades != D362's stored row-drop A2 {rd['trades']:,}"
    assert abs(m - rd["mean_bp"]) < tol, f"{tag} mean {m:.10f} != D362's stored row-drop A2 {rd['mean_bp']:.10f}"
    assert abs(m - STORED["rd_mean_bp"]) < tol and abs(rd["mean_bp"] - STORED["rd_mean_bp"]) < tol, f"{tag} the stored row-drop mean moved"
    assert pt["trades"] == STORED["resim_trades"] and abs(pt["mean_bp"] - STORED["resim_mean_bp"]) < tol, f"{tag} the stored re-simulated arm moved"
    # the export's own columns, re-derived a second way: a vectorised mask instead of the per-row loop above
    return dict(trades=len(tr), mean_bp=m, median_bp=float(np.median(g)), stored_rowdrop_trades=rd["trades"], stored_rowdrop_mean_bp=rd["mean_bp"],
                stored_resim_trades=pt["trades"], stored_resim_mean_bp=pt["mean_bp"], resim_minus_rowdrop_trades=pt["trades"] - len(tr),
                resim_minus_rowdrop_bp=pt["mean_bp"] - m, source=D362_REPORT.name,
                construction="taken_G2 == 1 & ~(S1 | S2) on the export's own columns == D362's ROW-DROP A2, not its re-simulated arm")


def quintiles(pub):
    """D363's rule: rank-based equal-count bins, 0 tightest .. 4 widest, ties broken by ledger order (a stable sort)."""
    n = pub.size
    order = np.argsort(pub, kind="stable")
    q = np.empty(n, np.int64)
    q[order] = np.arange(n) * N_QUINTILES // n
    return q


# ------------------------------------------------------------------ --plan
def survivorship_block(tr, q):
    """How big the provider's survivorship hole is, as numbers rather than as a sentence."""
    st = np.array([t["status"] for t in tr])
    g = np.array([t["gross_bp"] for t in tr])
    pub = np.array([t["pub_bp"] for t in tr])
    keep = np.isin(st, LIVE_STATUS)
    px = np.array([t["dollar_vol_g"] for t in tr])
    def side(m):
        return dict(n=int(m.sum()), share=float(m.mean()), gross_mean_bp=float(g[m].mean()), gross_median_bp=float(np.median(g[m])),
                    pub_mean_bp=float(pub[m].mean()), pub_median_bp=float(np.median(pub[m])),
                    dollar_vol_g_median=float(np.nanmedian(px[m])), by_quintile={int(k): int((m & (q == k)).sum()) for k in range(N_QUINTILES)})
    return dict(status_counts={k: int(v) for k, v in sorted(Counter(st.tolist()).items())}, eligible_status=list(LIVE_STATUS),
                kept=side(keep), excluded=side(~keep),
                delta_gross_bp=float(g[keep].mean() - g[~keep].mean()), delta_pub_bp=float(pub[keep].mean() - pub[~keep].mean()),
                statement=("SURVIVOR-ONLY AND NOT BY CHOICE. TIME_SERIES_INTRADAY serves nothing for a delisted ticker (PICKUP.md, probed "
                           "2026-09-01, four for four), so every delisted name is unreachable at this frequency and the sample is restricted "
                           "to names still listed at the span end. The sample is therefore biased toward the liquid half; the numbers above "
                           "are the size of that bias on this arm, measured rather than assumed."))


def months_of(t):
    return {(t["symbol"], t["date_entry"][:7]), (t["symbol"], t["date_exit"][:7])}


def draw_sample(tr, q, max_requests=MAX_REQUESTS, seed=SEED):
    """Permute each quintile's eligible trades once with default_rng(seed), then take the largest equal K per quintile whose distinct
    (symbol, month) request count fits the budget. The request count is monotone non-decreasing in K, so the scan stops at the first breach."""
    rng = np.random.default_rng(seed)
    keep = np.array([t["status"] in LIVE_STATUS for t in tr])
    perms = {}
    for k in range(N_QUINTILES):
        idx = np.nonzero((q == k) & keep)[0]
        perms[k] = idx[rng.permutation(idx.size)]
    kmax = min(len(perms[k]) for k in range(N_QUINTILES))
    chosen, req, K = [], set(), 0
    trace = []
    for cand in range(1, kmax + 1):
        add = [perms[k][cand - 1] for k in range(N_QUINTILES)]
        nxt = set(req)
        for j in add:
            nxt |= months_of(tr[j])
        trace.append((cand, len(nxt)))
        if len(nxt) > max_requests:
            break
        chosen += add
        req, K = nxt, cand
    return dict(K=K, per_quintile=K, idx=sorted(int(x) for x in chosen), requests=sorted(req), eligible_per_quintile={int(k): int(perms[k].size) for k in perms},
                kmax=int(kmax), budget=max_requests, next_K_requests=(trace[-1] if trace and trace[-1][0] == K + 1 else None), seed=seed)


def do_plan(out_dir):
    p = out_paths(out_dir)
    print(f"D364 --plan   (no network)   out-dir {p['dir']}\n")
    print(f"  [HOLDOUT-GUARD] {assert_HOLDOUT_GUARD()}")
    rows, cols, src = read_export()
    ax, _ = scan_fixture()
    axd = assert_AX(ax, rows, cols)
    print(f"  [AX] {axd['pairs']:,} (bar, date) pairs in {src} reproduced by the {axd['axis']:,}-date union axis "
          f"streamed from {FIXTURE.name} ({axd['first']} .. {axd['last']})")
    tr = a2_arm(rows, cols, ax)
    S = assert_S(tr)
    print(f"  [S] the arm rebuilt from {src}: taken_G2 == 1 minus S1 ({S1S2[0][1]} >= {S1S2[0][3]}) and S2 ({S1S2[1][1]} <= {S1S2[1][3]}), "
          f"read from {SINK_SOURCE}")
    print(f"      {S['trades']:,} trades, mean {S['mean_bp']:+.4f} bp == D362's stored ROW-DROP A2 ({S['stored_rowdrop_trades']:,}, "
          f"{S['stored_rowdrop_mean_bp']:+.4f}) exactly")
    print(f"      D362's RE-SIMULATED A2 arm is a different object: {S['stored_resim_trades']:,} trades, {S['stored_resim_mean_bp']:+.4f} bp "
          f"({S['resim_minus_rowdrop_trades']:+d} trades, {S['resim_minus_rowdrop_bp']:+.4f} bp) -- the slot book refills")
    pub = np.array([t["pub_bp"] for t in tr])
    q = quintiles(pub)
    for j, t in enumerate(tr):
        t["quintile"] = int(q[j])
    SV = survivorship_block(tr, q)
    D = draw_sample(tr, q)
    samp = [tr[j] for j in D["idx"]]

    print(f"\n  SURVIVORSHIP -- the provider's hole, measured on this arm")
    print(f"    status              {SV['status_counts']}")
    print(f"    KEPT     {SV['kept']['n']:5,} ({SV['kept']['share']:6.1%})  gross mean {SV['kept']['gross_mean_bp']:+8.2f} bp  "
          f"median {SV['kept']['gross_median_bp']:+8.2f}   PUB half mean {SV['kept']['pub_mean_bp']:7.2f}  median {SV['kept']['pub_median_bp']:7.2f}")
    print(f"    EXCLUDED {SV['excluded']['n']:5,} ({SV['excluded']['share']:6.1%})  gross mean {SV['excluded']['gross_mean_bp']:+8.2f} bp  "
          f"median {SV['excluded']['gross_median_bp']:+8.2f}   PUB half mean {SV['excluded']['pub_mean_bp']:7.2f}  median {SV['excluded']['pub_median_bp']:7.2f}")
    print(f"    delta (kept - excluded)  gross {SV['delta_gross_bp']:+.2f} bp   PUB half-spread {SV['delta_pub_bp']:+.2f} bp")
    print(f"    excluded by quintile     {SV['excluded']['by_quintile']}")

    print(f"\n  STRATA -- rank-based equal-count quintiles of half_spread_PUB_bp over ALL {len(tr):,} A2 trades (D363's rule and quantity)")
    print(f"    {'q':>2} {'trades':>7} {'eligible':>9} {'drawn':>6}   {'PUB half-spread bp':>22}   {'gross mean bp':>14}")
    for k in range(N_QUINTILES):
        m = q == k
        d = [t for t in samp if t["quintile"] == k]
        print(f"    {k:>2} {int(m.sum()):>7,} {D['eligible_per_quintile'][k]:>9,} {len(d):>6}   "
              f"{pub[m].min():>10.2f} .. {pub[m].max():<9.2f}   {np.array([t['gross_bp'] for t in tr])[m].mean():>+14.2f}")

    reqs = D["requests"]
    eta = len(reqs) * E.MIN_INTERVAL / 60.0
    cached = sum(1 for s, mth in reqs if E.slice_path(s, mth).exists())
    print(f"\n  THE DRAW   default_rng({SEED}), each quintile permuted once, first K of each; K is the largest equal draw inside the budget")
    print(f"    K per quintile      {D['K']}  (of {D['kmax']} available in the smallest eligible bin)")
    print(f"    trades sampled      {len(samp):,}  ({len(set(t['symbol'] for t in samp))} distinct symbols)")
    print(f"    DISTINCT (symbol, month) REQUESTS   {len(reqs)}   budget {D['budget']}   already cached {cached}")
    if D["next_K_requests"]:
        print(f"    K = {D['next_K_requests'][0]} would need {D['next_K_requests'][1]} requests -- over budget, so it stops here")
    print(f"    ESTIMATED WALL TIME at {E.REQUESTS_PER_MIN}/min   {eta:.1f} min ({len(reqs) - cached} still to fetch: "
          f"{(len(reqs) - cached) * E.MIN_INTERVAL / 60.0:.1f} min)")
    print(f"    NOTHING HAS BEEN FETCHED. The sample is written first.")
    mset = sorted({m for _s, m in reqs})
    print(f"    months spanned      {len(mset)}  ({mset[0]} .. {mset[-1]})")

    obj = dict(study=STUDY, purpose="the sample for D364's auction-print participation bound; MEASUREMENT ONLY", seed=SEED,
               written_at_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
               export=src, fixture=FIXTURE.name, sinks=[list(x) for x in S1S2], sink_source=SINK_SOURCE,
               arm=S, axis=axd, survivorship=SV,
               strata=dict(rule="rank-based equal-count quintiles of half_spread_PUB_bp over all A2 trades, ties by ledger order (D363's rule)",
                           column="half_spread_PUB_bp",
                           bounds={int(k): [float(pub[q == k].min()), float(pub[q == k].max())] for k in range(N_QUINTILES)},
                           counts={int(k): int((q == k).sum()) for k in range(N_QUINTILES)},
                           eligible={int(k): D["eligible_per_quintile"][k] for k in range(N_QUINTILES)}),
               draw=dict(K_per_quintile=D["K"], kmax=D["kmax"], budget=D["budget"], n_trades=len(samp),
                         n_requests=len(reqs), cached_at_plan=cached, eta_minutes=eta, requests_per_min=E.REQUESTS_PER_MIN,
                         next_K_requests=D["next_K_requests"],
                         note="Alpha Vantage bills one request per (symbol, month); a trade needs its entry month AND its exit month"),
               requests=[list(x) for x in reqs],
               sample=[dict(t) for t in samp],
               guard=guard_line())
    h = dump(p["sample"], obj)
    print(f"\n  wrote {p['sample']}  ({p['sample'].stat().st_size / 1e3:.1f} kB)  payload sha256 {h[:16]}...")
    print(f"\n  NEXT: --probe (one request, settles the 16:00 bar), then --fetch.")
    return 0


# ------------------------------------------------------------------ --probe and --fetch
def session_of(series, day):
    """{HH:MM: (open, high, low, close, volume)} for one date out of an Alpha Vantage intraday payload."""
    out = {}
    for stamp, b in series.items():
        if stamp[:10] != day:
            continue
        out[stamp[11:16]] = (float(b["1. open"]), float(b["2. high"]), float(b["3. low"]), float(b["4. close"]), float(b["5. volume"]))
    return out


def probe_report(symbol, month, payload):
    """What --probe must settle: is there a 16:00 bar, is there a 09:30 bar, and what are the first and last stamps of a regular session."""
    series = E.series_of(payload)
    meta = {k: v for k, v in payload.items() if k.lower().startswith("meta")}
    meta = list(meta.values())[0] if meta else {}
    tz = next((v for k, v in meta.items() if "time zone" in k.lower()), None)
    days = sorted({s[:10] for s in series})
    per_day = []
    for d in days:
        sess = session_of(series, d)
        rth = sorted(k for k in sess if RTH_FIRST <= k <= RTH_AUCTION)
        per_day.append(dict(date=d, bars=len(sess), first=min(sess) if sess else None, last=max(sess) if sess else None,
                            rth_first=rth[0] if rth else None, rth_last=rth[-1] if rth else None, rth_bars=len(rth),
                            has_0930=OPEN_STAMP in sess, has_1559=RTH_LAST_CONT in sess, has_1600=CLOSE_STAMP in sess,
                            v_0930=sess.get(OPEN_STAMP, (0,) * 5)[4], v_1559=sess.get(RTH_LAST_CONT, (0,) * 5)[4],
                            v_1600=sess.get(CLOSE_STAMP, (0,) * 5)[4],
                            v_rth=sum(sess[k][4] for k in rth)))
    full = [d for d in per_day if d["rth_bars"] >= 380]
    ref = max(per_day, key=lambda d: d["rth_bars"]) if per_day else None
    return dict(symbol=symbol, month=month, timezone=tz, meta={k: v for k, v in meta.items() if "key" not in k.lower()},
                bars=len(series), days=len(days), per_day=per_day, full_sessions=len(full), reference_session=ref,
                has_1600_any=any(d["has_1600"] for d in per_day), has_1600_all_full=all(d["has_1600"] for d in full) if full else False,
                has_0930_all_full=all(d["has_0930"] for d in full) if full else False,
                share_1600_of_rth=(ref["v_1600"] / ref["v_rth"]) if ref and ref["v_rth"] else None,
                share_0930_of_rth=(ref["v_0930"] / ref["v_rth"]) if ref and ref["v_rth"] else None)


def assert_TZ(pr, tag="[TZ]"):
    """The payload states its own timezone and the bars behave as OPEN-stamped: a full regular session starts at 09:30 and nothing between
    09:30 and 16:00 is stamped later than 16:00. Stated exactly as the fixture metas state it."""
    assert pr["timezone"] == "US/Eastern", f"{tag} the payload states timezone {pr['timezone']!r}, not 'US/Eastern'"
    full = [d for d in pr["per_day"] if d["rth_bars"] >= 380]
    assert full, f"{tag} no full regular session in the probe month to check the convention against"
    for d in full:
        assert d["rth_first"] == RTH_FIRST, f"{tag} {d['date']} regular session starts at {d['rth_first']}, not {RTH_FIRST}"
        assert d["rth_last"] <= RTH_AUCTION, f"{tag} {d['date']} has a regular-hours stamp beyond {RTH_AUCTION}: {d['rth_last']}"
    return dict(timezone=pr["timezone"], full_sessions=len(full),
                convention=("timestamps mark the interval's OPEN, so a bar stamped t covers [t, t+1m) and is not complete until t+1m "
                            "-- the same sentence the 15-minute fixture metas carry. The continuous regular session is 09:30..15:59; the "
                            "CLOSING AUCTION prints into the bar stamped 16:00, which is why extended_hours=true is required."),
                rth_first=full[0]["rth_first"], rth_last_continuous=RTH_LAST_CONT, auction_stamp=RTH_AUCTION)


def do_probe(out_dir):
    p = out_paths(out_dir)
    sp, where = find_input(out_dir, SAMPLE_NAME)
    if sp is None:
        raise SystemExit(f"no {SAMPLE_NAME} in {out_dir} or {DATA} -- run --plan first")
    S = json.loads(sp.read_text())
    # THE PROBE NAME IS THE SAMPLE'S MOST LIQUID TRADE, not the first row. The probe has to answer a question about the ENDPOINT's
    # CONVENTION -- is there a 16:00 bar, where does a regular session start and end -- and that question is only legible on a name that
    # trades every minute. A thin micro-cap would answer "no 16:00 bar" for a reason that is about the name and not about the endpoint. The
    # pair is already in the plan's request list either way, so this costs no extra request.
    lead = max(S["sample"], key=lambda t: (t["dollar_vol_g"] if isinstance(t["dollar_vol_g"], (int, float))
                                           and math.isfinite(t["dollar_vol_g"]) else -1.0))
    symbol, month = lead["symbol"], lead["date_entry"][:7]
    assert [symbol, month] in S["requests"], "the probe pair is not in the plan's request list"
    print(f"D364 --probe   ONE (symbol, month) -- the sample's most liquid trade, already in the plan's request list, so not an extra request\n")
    print(f"  chosen     {symbol} {month}  (gap-day dollar volume {lead['dollar_vol_g']:,.0f}, PUB quintile {lead['quintile']})")
    print(f"  sample     {sp}  ({where})")
    print(f"  probing    {symbol} {month}   interval={E.INTERVAL}  outputsize=full  adjusted=false  extended_hours=true")
    key = E.api_key()
    limiter = E.RateLimiter(E.MIN_INTERVAL)
    path = E.slice_path(symbol, month)
    if path.exists():
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            payload = json.load(fh)
        print(f"  (already cached at {path.relative_to(REPO)}; no request spent)")
    else:
        t0 = time.monotonic()
        try:
            payload = E.fetch_slice(symbol, month, key, limiter)
        except Exception as exc:
            raise SystemExit(f"PROBE FAILED: {str(exc).replace(key, '***')[:300]}")
        path.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(path, "wt", encoding="utf-8") as fh:
            json.dump(payload, fh, separators=(",", ":"))
        print(f"  fetched in {time.monotonic() - t0:.1f}s, cached to {path.relative_to(REPO)}")

    pr = probe_report(symbol, month, payload)
    print(f"\n  payload    {pr['bars']:,} bars over {pr['days']} days; timezone stated as {pr['timezone']!r}")
    print(f"  {'date':<12}{'bars':>6}{'first':>8}{'last':>8}{'RTH':>6}  {'09:30':>4} {'15:59':>5} {'16:00':>5}   "
          f"{'v(09:30)':>12} {'v(15:59)':>12} {'v(16:00)':>12} {'16:00/RTH':>10}")
    for d in pr["per_day"][:8] + (["..."] if len(pr["per_day"]) > 12 else []) + pr["per_day"][max(8, len(pr["per_day"]) - 4):]:
        if d == "...":
            print("    ...")
            continue
        sh = d["v_1600"] / d["v_rth"] if d["v_rth"] else float("nan")
        print(f"  {d['date']:<12}{d['bars']:>6}{d['first']:>8}{d['last']:>8}{d['rth_bars']:>6}  "
              f"{'Y' if d['has_0930'] else '.':>4} {'Y' if d['has_1559'] else '.':>5} {'Y' if d['has_1600'] else '.':>5}   "
              f"{d['v_0930']:>12,.0f} {d['v_1559']:>12,.0f} {d['v_1600']:>12,.0f} {sh:>9.1%}")

    ok = pr["has_1600_any"] and pr["has_1600_all_full"] and pr["has_0930_all_full"]
    pr["passed"] = bool(ok)
    if ok:
        tz = assert_TZ(pr)
        pr["TZ"] = tz
        print(f"\n  [TZ] {tz['convention']}")
        print(f"       a regular session's FIRST stamp is {tz['rth_first']} and its LAST CONTINUOUS stamp is {tz['rth_last_continuous']}; "
              f"the closing auction is the bar stamped {tz['auction_stamp']}.")
        print(f"\n  PROBE PASSED: the 16:00 bar EXISTS with extended_hours=true, in all {pr['full_sessions']} full sessions of {month}, "
              f"and so does the 09:30 bar.")
        print(f"       on {pr['reference_session']['date']}: the 16:00 minute is {pr['share_1600_of_rth']:.2%} of the whole regular session's "
              f"share volume, the 09:30 minute {pr['share_0930_of_rth']:.2%}.")
    else:
        print(f"\n  *** PROBE FAILED ***  16:00 present on any day: {pr['has_1600_any']}; on every full session: {pr['has_1600_all_full']}; "
              f"09:30 on every full session: {pr['has_0930_all_full']}")
        print(f"      STOPPING. The whole measurement is the size of the 16:00 bar. 15:59 IS NOT A SUBSTITUTE and will not be used as one.")
    dump(p["probe"], pr)
    print(f"\n  wrote {p['probe']}")
    return 0 if ok else 1


def do_fetch(out_dir, limit=None, retry_unserved=False):
    p = out_paths(out_dir)
    sp, _ = find_input(out_dir, SAMPLE_NAME)
    if sp is None:
        raise SystemExit(f"no {SAMPLE_NAME} -- run --plan first")
    pp, _ = find_input(out_dir, PROBE_NAME)
    if pp is None:
        raise SystemExit("no probe result -- run --probe first. The 16:00 bar has to exist before 150 requests are spent on it.")
    pr = json.loads(pp.read_text())
    if not pr.get("passed"):
        raise SystemExit("the probe did NOT pass -- refusing to fetch. See the probe report; do not substitute 15:59.")
    S = json.loads(sp.read_text())
    reqs = [tuple(x) for x in S["requests"]]
    # RESUMABILITY HAS TWO HALVES. A cached slice is never re-fetched -- and neither is a pair the provider has already REFUSED, because
    # that refusal is a fact about the ticker, not a transient failure, and re-asking costs a request every run. --retry-unserved re-asks.
    meta_path = E.CACHE / E.INTERVAL / "_meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    known_unserved = {(u["symbol"], u["month"]) for u in meta.get("unserved", [])} if not retry_unserved else set()
    todo = [(s, m) for s, m in reqs if not E.slice_path(s, m).exists() and (s, m) not in known_unserved]
    if limit:
        todo = todo[:limit]
    print(f"D364 --fetch   {len(reqs)} (symbol, month) requests planned, {sum(1 for s, m in reqs if E.slice_path(s, m).exists())} already "
          f"cached, {len(known_unserved & set(reqs))} already refused by the provider, {len(todo)} this run")
    print(f"  pacing {E.REQUESTS_PER_MIN}/min (tier 75), ETA {len(todo) * E.MIN_INTERVAL / 60:.1f} min")
    print(f"  cache  {E.CACHE / E.INTERVAL}  (gitignored, D191)\n")
    if not todo:
        print("  nothing to do -- the cache is complete")
        return 0
    key = E.api_key()
    limiter = E.RateLimiter(E.MIN_INTERVAL)
    fetched = empty = consecutive = 0
    unserved = []
    t0 = time.monotonic()
    for i, (symbol, month) in enumerate(todo, 1):
        try:
            payload = E.fetch_slice(symbol, month, key, limiter)
        except RuntimeError as exc:
            msg = str(exc).replace(key, "***")[:200]
            if "Error Message" in msg:
                # a definitive provider answer (a ticker it will not serve at this frequency), not a transient failure
                unserved.append(dict(symbol=symbol, month=month, message=msg))
                print(f"  [{i}/{len(todo)}] {symbol} {month}: UNSERVED -- {msg[:120]}")
                if len(unserved) >= MAX_UNSERVED:
                    print(f"\n  STOPPING: {len(unserved)} unserved (symbol, month) pairs. Something systematic is wrong.")
                    return 1
                continue
            consecutive += 1
            if any(w in msg.lower() for w in ("rate", "frequency", "note")):
                back = min(60.0 * consecutive, 300.0)
                print(f"  [{i}/{len(todo)}] {symbol} {month}: THROTTLED -- backing off {back:.0f}s\n      {msg}")
                time.sleep(back)
            else:
                print(f"  [{i}/{len(todo)}] {symbol} {month}: {msg}")
            if consecutive >= E.MAX_CONSECUTIVE_FAILURES:
                print(f"\n  STOPPING after {consecutive} consecutive failures. Re-run to resume; cached slices are kept.")
                return 1
            continue
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            consecutive += 1
            print(f"  [{i}/{len(todo)}] {symbol} {month}: {str(exc).replace(key, '***')[:140]}")
            if consecutive >= E.MAX_CONSECUTIVE_FAILURES:
                print(f"\n  STOPPING after {consecutive} consecutive failures.")
                return 1
            continue
        consecutive = 0
        n = len(E.series_of(payload))
        if n == 0:
            empty += 1
        path = E.slice_path(symbol, month)
        path.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(path, "wt", encoding="utf-8") as fh:
            json.dump(payload, fh, separators=(",", ":"))
        fetched += 1
        if i % 25 == 0 or i == len(todo):
            done = time.monotonic() - t0
            print(f"  [{i}/{len(todo)}] {symbol} {month}  {n:,} bars | {i / done * 60 if done else 0:.0f}/min | "
                  f"{(len(todo) - i) * E.MIN_INTERVAL / 60:.1f} min left")
    wall = time.monotonic() - t0
    # the refusal list is CUMULATIVE across runs -- that is what makes it a resume record rather than a log of the last run
    merged = {(u["symbol"], u["month"]): u for u in meta.get("unserved", [])}
    merged.update({(u["symbol"], u["month"]): u for u in unserved})
    unserved = [merged[k] for k in sorted(merged)]
    meta.update(dict(
        purpose="D364: 1-minute bars for the auction-print participation bound. DATA ONLY -- no strategy, no cell, no rule.",
        provider="Alpha Vantage TIME_SERIES_INTRADAY", interval=E.INTERVAL, outputsize="full", adjusted="false", extended_hours="true",
        month_parameter="YYYY-MM, one request per (symbol, month)", timezone=E.TZ,
        bar_boundary=("timestamps mark the interval's OPEN, so a bar stamped t covers [t, t+1m). The continuous regular session is "
                      "09:30..15:59; the CLOSING AUCTION prints into the bar stamped 16:00, which exists only with extended_hours=true."),
        as_traded=("adjusted=false: prices are AS-TRADED and never change, which the daily fixture's SPLIT-ADJUSTED frame does not share. "
                   "Share volume therefore differs across a split; dollar volume does not."),
        committed=False, gitignore="data/raw/alphavantage/", pacing=f"{E.REQUESTS_PER_MIN}/min against a tier ceiling of 75",
        sample=SAMPLE_NAME, study=STUDY, requests_planned=len(reqs), fetched_this_run=fetched, empty_payloads=empty,
        unserved=unserved, wall_seconds=round(wall, 1), updated_at_utc=datetime.now(timezone.utc).isoformat(timespec="seconds")))
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(meta, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"\n  done: {fetched} slices cached ({empty} empty, {len(unserved)} unserved) in {wall / 60:.1f} min")
    print(f"  wrote {meta_path.relative_to(REPO)}")
    return 0


# ------------------------------------------------------------------ --report
def load_minutes(sample):
    """{(symbol, date): {HH:MM: (o, h, l, c, v)}} for the sampled entry and exit dates ONLY -- a full month of 1-minute extended-hours bars
    is ~20k rows and only a handful of days are ever read, so nothing else is kept."""
    want = {}
    for t in sample:
        for d in (t["date_entry"], t["date_exit"]):
            want.setdefault((t["symbol"], d[:7]), set()).add(d)
    out, missing = {}, []
    for (sym, month), days in sorted(want.items()):
        path = E.slice_path(sym, month)
        if not path.exists():
            missing.append((sym, month))
            continue
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            series = E.series_of(json.load(fh))
        for d in days:
            s = session_of(series, d)
            if s:
                out[(sym, d)] = s
    return out, missing


def minute_dv(sess, stamp):
    """close x volume of one minute bar, or NaN."""
    if sess is None or stamp not in sess:
        return float("nan")
    _o, _h, _l, c, v = sess[stamp]
    return c * v if (math.isfinite(c) and math.isfinite(v) and c * v > 0) else float("nan")


def rth_volume(sess, include_auction):
    last = RTH_AUCTION if include_auction else RTH_LAST_CONT
    ks = [k for k in sess if RTH_FIRST <= k <= last]
    return sum(sess[k][4] for k in ks), sum(sess[k][3] * sess[k][4] for k in ks), len(ks)


def measure(sample, minutes, daily):
    """Per trade: the four dollar-volume denominators and the participation at each position size."""
    rec = []
    for t in sample:
        se, sx = minutes.get((t["symbol"], t["date_entry"])), minutes.get((t["symbol"], t["date_exit"]))
        de, dx = daily.get((t["symbol"], t["date_entry"])), daily.get((t["symbol"], t["date_exit"]))
        r = dict(t)
        r["dv_open_min"] = minute_dv(se, OPEN_STAMP)
        r["dv_close_min"] = minute_dv(sx, CLOSE_STAMP)
        r["dv_day_entry"] = de[0] * de[1] if de and de[0] * de[1] > 0 else float("nan")
        r["dv_day_exit"] = dx[0] * dx[1] if dx and dx[0] * dx[1] > 0 else float("nan")
        r["ratio_open_day"] = r["dv_open_min"] / r["dv_day_entry"]
        r["ratio_close_day"] = r["dv_close_min"] / r["dv_day_exit"]
        r["has_entry_session"] = se is not None
        r["has_exit_session"] = sx is not None
        if sx is not None:
            rth = sorted(k for k in sx if RTH_FIRST <= k <= RTH_AUCTION)
            r["exit_rth_bars"] = len(rth)
            r["exit_last_rth"] = rth[-1] if rth else None
            r["exit_last_any"] = max(sx)
        for lab, dv in (("open_min", r["dv_open_min"]), ("close_min", r["dv_close_min"]),
                        ("day_entry", r["dv_day_entry"]), ("day_exit", r["dv_day_exit"])):
            for pos in POSITIONS:
                r[f"part_{lab}_{pos}"] = pos / dv if math.isfinite(dv) and dv > 0 else float("nan")
        rec.append(r)
    return rec


def part_block(rec, lab):
    out = dict(dollar_volume=stats_of([r[f"dv_{lab}"] for r in rec]))
    for pos in POSITIONS:
        x = np.array([r[f"part_{lab}_{pos}"] for r in rec], float)
        f = x[np.isfinite(x)]
        out[str(pos)] = dict(n=int(f.size), median=float(np.median(f)) if f.size else None,
                             p90=float(np.quantile(f, .90)) if f.size else None, p99=float(np.quantile(f, .99)) if f.size else None,
                             share_above_1pct=float((f > 0.01).mean()) if f.size else None,
                             share_above_5pct=float((f > 0.05).mean()) if f.size else None,
                             max=float(f.max()) if f.size else None)
    return out


def by_quintile(rec, fn):
    return {int(k): fn([r for r in rec if r["quintile"] == k]) for k in range(N_QUINTILES)}


# ---- [REC] the reconciliation
def reconcile(minutes, daily):
    """Per sampled (symbol, date): summed 1-minute regular-session SHARE volume against the daily fixture's volume for the same bar.

    Two sums are carried, 09:30..15:59 and 09:30..16:00, because the difference between them IS the closing auction and the daily
    consolidated bar contains it. The dollar-volume ratio is carried beside the share-volume one: the daily fixture is split-adjusted and
    these bars are as-traded, so a split moves the first and not the second."""
    rows = []
    for (sym, day), sess in sorted(minutes.items()):
        d = daily.get((sym, day))
        if d is None:
            continue
        dc, dv_shares = d
        v_cont, dvv_cont, n_cont = rth_volume(sess, False)
        v_all, dvv_all, n_all = rth_volume(sess, True)
        if dv_shares <= 0:
            continue
        rd = dvv_all / (dc * dv_shares) if dc * dv_shares > 0 else float("nan")
        rs = v_all / dv_shares
        rows.append(dict(symbol=sym, date=day, minute_bars=n_all, minute_bars_continuous=n_cont,
                         v_minutes_0930_1559=v_cont, v_minutes_0930_1600=v_all, v_daily=dv_shares,
                         ratio=rs, ratio_continuous=v_cont / dv_shares,
                         auction_share_of_daily=(v_all - v_cont) / dv_shares,
                         dv_minutes_0930_1600=dvv_all, dv_daily=dc * dv_shares, ratio_dollar=rd,
                         # dollar volume is split-INVARIANT (the fixture divides prices and multiplies volumes by the same factor) and share
                         # volume is not, so the quotient of the two ratios estimates the split factor the fixture has applied to this bar.
                         implied_split_factor=(rd / rs) if (math.isfinite(rd) and rs > 0) else float("nan")))
    return rows


def assert_REC(rows, band=REC_BAND, hard=REC_HARD, tag="[REC]"):
    """The consolidated tape and the intraday endpoint are NOT required to agree exactly, so the assertion and the report are different
    things and are kept apart on purpose.

    ASSERTED (a keying error, not a tape difference): every reconciled pair has positive volume on both sides; no single pair is off by more
    than three orders of magnitude either way; and the median DOLLAR ratio sits inside a wide sanity band. The dollar ratio is the asserted
    one because it is SPLIT-INVARIANT -- the daily fixture multiplies volume by the split factor and these bars are as-traded, so the SHARE
    ratio of a name that split reads 1/f and would fail an assertion for a reason that is about the frame and not about the tape.

    REPORTED, never fatal: the share ratio the task asks for, its median and range, and EVERY (symbol, date) outside [0.8, 1.2] named,
    with the implied split factor (dollar ratio / share ratio) beside it so that a frame artefact is distinguishable from a real gap."""
    assert rows, f"{tag} nothing to reconcile"
    for x in rows:
        assert x["v_daily"] > 0 and x["v_minutes_0930_1600"] > 0, f"{tag} ({x['symbol']}, {x['date']}) has no volume on one side"
        assert 1e-3 < x["ratio_dollar"] < 1e3, f"{tag} ({x['symbol']}, {x['date']}) dollar ratio {x['ratio_dollar']:.3g} -- that is a keying error, not a tape difference"
    r = np.array([x["ratio"] for x in rows], float)
    rd = np.array([x["ratio_dollar"] for x in rows], float)
    med_d = float(np.median(rd))
    assert hard[0] <= med_d <= hard[1], f"{tag} the median DOLLAR ratio {med_d:.4f} is outside the sanity band {hard}"
    def blk(a, key):
        out = [x for x in rows if not (band[0] <= x[key] <= band[1])]
        return dict(median=float(np.median(a)), p25=float(np.quantile(a, .25)), p75=float(np.quantile(a, .75)), min=float(a.min()),
                    max=float(a.max()), outside_band=len(out), outside_share=len(out) / len(rows),
                    symbols_outside=sorted({x["symbol"] for x in out}),
                    outside=[dict(symbol=x["symbol"], date=x["date"], ratio=x["ratio"], ratio_dollar=x["ratio_dollar"],
                                  implied_split_factor=x["implied_split_factor"], minutes=x["v_minutes_0930_1600"], daily=x["v_daily"],
                                  minute_bars=x["minute_bars"]) for x in sorted(out, key=lambda z: abs(math.log(max(z[key], 1e-9))), reverse=True)])
    full = np.array([x["minute_bars"] >= 390 for x in rows])
    return dict(n=len(rows), band=list(band), hard_band=list(hard), share=blk(r, "ratio"), dollar=blk(rd, "ratio_dollar"),
                full_sessions=int(full.sum()),
                median_share_full=float(np.median(r[full])) if full.any() else None,
                median_share_partial=float(np.median(r[~full])) if (~full).any() else None,
                median_dollar_full=float(np.median(rd[full])) if full.any() else None,
                median_dollar_partial=float(np.median(rd[~full])) if (~full).any() else None,
                # kept at the top level because the printed tables and the older key names read from here
                median=float(np.median(r)), p25=float(np.quantile(r, .25)), p75=float(np.quantile(r, .75)), min=float(r.min()), max=float(r.max()),
                outside_band=blk(r, "ratio")["outside_band"], outside_share=blk(r, "ratio")["outside_share"],
                outside=blk(r, "ratio")["outside"], symbols_outside=blk(r, "ratio")["symbols_outside"])


def assert_6(rows, tag="[6]"):
    """[REC] raises on a perturbed volume. Scaling every minute volume scales BOTH ratios (a share is a share and a dollar is a price times
    that share), so the perturbation is applied to both, exactly as a corrupted volume column would. The naming half is checked separately:
    one (symbol, date) is perturbed and must be NAMED without the run failing. A self-test that cannot fail is worse than none."""
    scale = 5.0
    scaled = [dict(x, ratio=x["ratio"] * scale, ratio_dollar=x["ratio_dollar"] * scale,
                   v_minutes_0930_1600=x["v_minutes_0930_1600"] * scale, dv_minutes_0930_1600=x["dv_minutes_0930_1600"] * scale) for x in rows]
    raised = False
    try:
        assert_REC(scaled)
    except AssertionError as e:
        raised = "[REC]" in str(e)
    assert raised, f"{tag} [REC] did NOT raise when every minute volume was scaled by {scale}"
    j = int(np.argmin([abs(x["ratio"] - 1.0) for x in rows]))            # the most in-band row: if THIS gets named, the naming works
    one = [dict(x) for x in rows]
    one[j] = dict(one[j], ratio=one[j]["ratio"] * 5.0, v_minutes_0930_1600=one[j]["v_minutes_0930_1600"] * 5.0)
    d = assert_REC(one)
    named = any(o["symbol"] == one[j]["symbol"] and o["date"] == one[j]["date"] for o in d["share"]["outside"])
    assert named, f"{tag} [REC] did not NAME the single perturbed ({one[j]['symbol']}, {one[j]['date']})"
    return dict(global_scale=scale, global_raised=True, single=dict(symbol=one[j]["symbol"], date=one[j]["date"], scale=5.0, named=True),
                note="a global scaling must RAISE the assertion; a single perturbed pair must be NAMED and must not raise")


def assert_K(sp, S, tr_all, tag="[K]"):
    """--report is reading the file --plan wrote: the payload hash inside the file matches the file's own content, and the sample's rows are
    re-derived from the export and compared field for field."""
    h = payload_hash(S)
    assert h == S["payload_sha256"], f"{tag} {sp} has been edited: payload sha256 {h[:16]} != the recorded {S['payload_sha256'][:16]}"
    idx = {(t["symbol"], t["bar_entry"], t["row"]): t for t in tr_all}
    for t in S["sample"]:
        k = (t["symbol"], t["bar_entry"], t["row"])
        assert k in idx, f"{tag} the sample carries {k}, which is not an A2 trade of the export"
        for f in ("date_entry", "date_exit", "bar_exit", "hold", "gross_bp", "pub_bp", "status", "quintile"):
            assert idx[k][f] == t[f], f"{tag} {k}.{f}: sample {t[f]!r} != re-derived {idx[k][f]!r}"
    file_sha = hashlib.sha256(Path(sp).read_bytes()).hexdigest()
    return dict(path=str(sp), payload_sha256=h, file_sha256=file_sha, sample_rows=len(S["sample"]), seed=S["seed"], rederived=True)


def do_report(out_dir):
    p = out_paths(out_dir)
    p["dir"].mkdir(parents=True, exist_ok=True)
    sp, where = find_input(out_dir, SAMPLE_NAME)
    if sp is None:
        raise SystemExit(f"no {SAMPLE_NAME} -- run --plan first")
    S = json.loads(sp.read_text())
    print(f"D364 --report   out-dir {p['dir']}\n")
    print(f"  [HOLDOUT-GUARD] {assert_HOLDOUT_GUARD()}")

    rows, cols, src = read_export()
    ax, _ = scan_fixture()                                        # pass 1: the union date axis (the exit DATE is not in the export)
    axd = assert_AX(ax, rows, cols)
    tr_all = a2_arm(rows, cols, ax)
    pub = np.array([t["pub_bp"] for t in tr_all])
    q = quintiles(pub)
    for j, t in enumerate(tr_all):
        t["quintile"] = int(q[j])
    Sv = assert_S(tr_all)
    K = assert_K(sp, S, tr_all)
    print(f"  [AX] {axd['pairs']:,} (bar, date) pairs reproduced by the {axd['axis']:,}-date union axis ({axd['first']} .. {axd['last']})")
    print(f"  [S]  {Sv['trades']:,} A2 trades, mean {Sv['mean_bp']:+.4f} bp == D362's stored row-drop A2 exactly; the stored RE-SIMULATED "
          f"arm is {Sv['stored_resim_trades']:,} / {Sv['stored_resim_mean_bp']:+.4f} ({Sv['resim_minus_rowdrop_trades']:+d} trades, "
          f"{Sv['resim_minus_rowdrop_bp']:+.4f} bp)")
    print(f"  [K]  sample {sp} ({where}), {K['sample_rows']} rows, seed {K['seed']}; payload sha256 {K['payload_sha256'][:16]}... matches, "
          f"every row re-derived from {src}")

    pp, _ = find_input(out_dir, PROBE_NAME)
    pr = json.loads(pp.read_text()) if pp else None
    if pr and pr.get("passed"):
        tz = pr.get("TZ") or assert_TZ(pr)
        print(f"  [TZ] {pr['timezone']}, stamps at the interval's OPEN; regular session {tz['rth_first']}..{tz['rth_last_continuous']} "
              f"continuous, the closing auction at {tz['auction_stamp']} (probe {pr['symbol']} {pr['month']})")
    else:
        tz = None
        print(f"  [TZ] NO PASSED PROBE -- the 16:00 convention is unverified for this run")

    # ---- THE FREE RIDERS. A request buys a WHOLE MONTH of one name's minute bars, so every other A2 trade whose entry AND exit months are
    # both already in the request list can be measured for nothing. That set is OPPORTUNISTIC -- it is what the stratified draw happened to
    # pay for, not a random sample of anything -- so it is reported as its OWN panel and never pooled into the headline. The spec did not
    # fix this; it costs zero requests and roughly triples n, and hiding it would be worse than labelling it.
    req = {tuple(x) for x in S["requests"]}
    key = lambda t: (t["symbol"], t["bar_entry"], t["row"])
    have = {key(t) for t in S["sample"]}
    bonus = [t for t in tr_all if key(t) not in have and t["status"] in LIVE_STATUS
             and (t["symbol"], t["date_entry"][:7]) in req and (t["symbol"], t["date_exit"][:7]) in req]
    pool = [dict(t, in_sample=True) for t in S["sample"]] + [dict(t, in_sample=False) for t in bonus]

    want_daily = {(t["symbol"], t["date_entry"]) for t in pool} | {(t["symbol"], t["date_exit"]) for t in pool}
    _ax2, daily = scan_fixture(want_daily)                        # pass 2: the daily bars for the dates the pool actually reads
    assert _ax2 == ax, "the fixture changed between the two passes"

    minutes, missing = load_minutes(pool)
    rec = measure(pool, minutes, daily)
    complete = lambda r: (math.isfinite(r["dv_open_min"]) and math.isfinite(r["dv_close_min"])
                          and math.isfinite(r["dv_day_entry"]) and math.isfinite(r["dv_day_exit"]))
    ok = [r for r in rec if r["in_sample"] and complete(r)]
    ok_pool = [r for r in rec if complete(r)]
    print(f"\n  COVERAGE   {len(S['sample'])} sampled trades (+{len(bonus)} free riders already paid for by the same requests); "
          f"{len(minutes)} (symbol, date) sessions loaded from {len({(s, d[:7]) for s, d in minutes})} cached slices; {len(missing)} missing")
    # WHY a denominator is missing matters: an unfetched slice is a budget fact, a session with no 16:00 bar is a fact about the tape.
    n_no_open = sum(1 for r in rec if r["in_sample"] and not math.isfinite(r["dv_open_min"]))
    n_no_close = sum(1 for r in rec if r["in_sample"] and not math.isfinite(r["dv_close_min"]))
    miss = dict(open_no_session=sum(1 for r in rec if r["in_sample"] and not r["has_entry_session"]),
                open_no_bar=sum(1 for r in rec if r["in_sample"] and r["has_entry_session"] and not math.isfinite(r["dv_open_min"])),
                close_no_session=sum(1 for r in rec if r["in_sample"] and not r["has_exit_session"]),
                close_no_bar=sum(1 for r in rec if r["in_sample"] and r["has_exit_session"] and not math.isfinite(r["dv_close_min"])),
                no_daily=sum(1 for r in rec if r["in_sample"] and not (math.isfinite(r["dv_day_entry"]) and math.isfinite(r["dv_day_exit"]))))
    print(f"             sample: no 09:30 bar on the entry date {n_no_open} ({miss['open_no_session']} because the session was never "
          f"fetched, {miss['open_no_bar']} because the session has no 09:30 print)")
    print(f"             sample: no 16:00 bar on the exit date {n_no_close} ({miss['close_no_session']} unfetched, "
          f"{miss['close_no_bar']} fetched but with no 16:00 print -- a name that did not trade into the closing auction that day)")
    print(f"             no daily bar on one of the two dates: {miss['no_daily']}; complete on all four denominators {len(ok)} "
          f"(pool {len(ok_pool)})")
    if missing:
        print(f"             missing slices: {sorted(missing)[:10]}{' ...' if len(missing) > 10 else ''}")

    # THE 16:00 BAR THAT IS NOT THERE. Not substituted, and not waved through either: every one is named with its session's shape, because
    # a session that runs a full 09:30..15:59 and then prints post-market bars is a session the feed simply gave no 16:00 bucket for -- not
    # a half-day, not a missing session. And because dropping them could bias the surviving set, their quintiles are printed beside.
    nb = [r for r in rec if r["in_sample"] and r["has_exit_session"] and not math.isfinite(r["dv_close_min"])]
    if nb:
        print(f"\n  NO 16:00 BAR ON A FETCHED EXIT SESSION -- {len(nb)} of {sum(1 for r in rec if r['in_sample'] and r['has_exit_session'])}. "
              f"NOT substituted with 15:59; these trades simply carry no closing-minute denominator.")
        print(f"    {'symbol':<8}{'exit date':<12}{'RTH bars':>9}{'last RTH':>10}{'last stamp':>12}{'q':>3}")
        for r in sorted(nb, key=lambda x: x["date_exit"])[:25]:
            print(f"    {r['symbol']:<8}{r['date_exit']:<12}{r['exit_rth_bars']:>9}{str(r['exit_last_rth']):>10}{str(r['exit_last_any']):>12}{r['quintile']:>3}")
        print(f"    by quintile {dict(sorted(Counter(r['quintile'] for r in nb).items()))}   "
              f"(all trades by quintile {dict(sorted(Counter(r['quintile'] for r in rec if r['in_sample']).items()))})")
        print(f"    every one runs a complete 09:30..15:59 and prints post-market bars after it, so this is a MISSING 16:00 BUCKET in the")
        print(f"    feed, not a half-day and not a missing session. The closing auction for those days is most likely inside 15:59; that is a")
        print(f"    guess, it is not used, and the {len(nb)} trades are dropped from the closing-minute column rather than filled.")

    # ---------------- the headline
    print(f"\n{'=' * 132}")
    print(f"  PARTICIPATION -- position / dollar volume, BOTH DENOMINATORS SIDE BY SIDE.  n = {len(ok)} trades complete on all four.")
    print(f"  THE MINUTE BARS ARE AN UPPER BOUND ON THE AUCTION: the 09:30 bar is the opening auction PLUS a minute of continuous trade,")
    print(f"  the 16:00 bar the closing auction plus a minute. The auction's own size is SMALLER than these, so the true participation is")
    print(f"  LARGER than every number in this table.")
    print(f"{'=' * 132}")
    LAB = dict(open_min="09:30 MINUTE (entry)", close_min="16:00 MINUTE (exit)", day_entry="WHOLE DAY (entry)", day_exit="WHOLE DAY (exit)")
    blocks = {lab: part_block(ok, lab) for lab in LAB}
    print(f"\n  {'denominator':<22}{'median $vol':>16}   " + "".join(f"{'$' + str(p // 1000) + 'k med':>11}{'p90':>10}{'p99':>10}{'>1%':>8}{'>5%':>8}" for p in POSITIONS))
    for lab in ("open_min", "day_entry", "close_min", "day_exit"):
        b = blocks[lab]
        line = f"  {LAB[lab]:<22}{b['dollar_volume']['median']:>16,.0f}   "
        for pos in POSITIONS:
            d = b[str(pos)]
            line += f"{d['median'] * 100:>10.3f}%{d['p90'] * 100:>9.2f}%{d['p99'] * 100:>9.2f}%{d['share_above_1pct'] * 100:>7.1f}%{d['share_above_5pct'] * 100:>7.1f}%"
        print(line)

    print(f"\n  THE RATIO -- minute dollar volume / whole-day dollar volume, the same bar. THIS IS THE FINDING.")
    rr = dict(open_over_day=stats_of([r["ratio_open_day"] for r in ok]), close_over_day=stats_of([r["ratio_close_day"] for r in ok]))
    print(f"    {'':<26}{'p25':>10}{'median':>10}{'p75':>10}{'mean':>10}{'p90':>10}{'p99':>10}{'min':>10}{'max':>10}")
    for k, nm in (("open_over_day", "09:30 minute / whole day"), ("close_over_day", "16:00 minute / whole day")):
        s = rr[k]
        print(f"    {nm:<26}" + "".join(f"{s[f] * 100:>9.2f}%" for f in ("p25", "median", "p75", "mean", "p90", "p99", "min", "max")))
    fac_o = rr["open_over_day"]["median"]
    fac_c = rr["close_over_day"]["median"]
    d363p = d363_participation()
    d363_25k = d363p["entry"]["25000"]["median"] if d363p else None
    print(f"\n    So the honest denominator is {1 / fac_o:.0f}x smaller at the open and {1 / fac_c:.0f}x smaller at the close than D363's,")
    print(f"    and the participation numbers scale by the same factors. At $25k a position, median:")
    print(f"      D363's whole-day (its own 3,079-trade ledger, read from {D363_REPORT.name})   {d363_25k * 100:.4f}%"
          if d363_25k else "      (no D363 report to compare against)")
    print(f"      whole day, this sample, entry / exit                                          "
          f"{blocks['day_entry']['25000']['median'] * 100:.4f}% / {blocks['day_exit']['25000']['median'] * 100:.4f}%")
    print(f"      THE 09:30 MINUTE (entry fill) / THE 16:00 MINUTE (exit fill)                  "
          f"{blocks['open_min']['25000']['median'] * 100:.3f}% / {blocks['close_min']['25000']['median'] * 100:.3f}%")

    # ---------------- by quintile
    print(f"\n  BY PUB HALF-SPREAD QUINTILE (0 tightest .. 4 widest; D363 put the edge in Q4 and those are the thinnest names)")
    qb = {lab: by_quintile(ok, lambda rs, l=lab: part_block(rs, l)) for lab in LAB}
    qr = dict(open_over_day=by_quintile(ok, lambda rs: stats_of([r["ratio_open_day"] for r in rs])),
              close_over_day=by_quintile(ok, lambda rs: stats_of([r["ratio_close_day"] for r in rs])))
    for pos in POSITIONS:
        print(f"\n    ${pos // 1000}k a position -- median participation, and the share above 1% / 5%")
        print(f"      {'q':>2}{'n':>6}   {'09:30 min':>10}{'>1%':>7}{'>5%':>7}   {'whole day (in)':>15}   {'16:00 min':>10}{'>1%':>7}{'>5%':>7}   "
              f"{'whole day (out)':>16}   {'09:30/day':>10}{'16:00/day':>11}")
        for k in range(N_QUINTILES):
            n = qb["open_min"][k]["25000"]["n"]
            if not n:
                print(f"      {k:>2}{0:>6}   (no complete trades)")
                continue
            o, c = qb["open_min"][k][str(pos)], qb["close_min"][k][str(pos)]
            de, dx = qb["day_entry"][k][str(pos)], qb["day_exit"][k][str(pos)]
            print(f"      {k:>2}{n:>6}   {o['median'] * 100:>9.3f}%{o['share_above_1pct'] * 100:>6.1f}%{o['share_above_5pct'] * 100:>6.1f}%   "
                  f"{de['median'] * 100:>14.4f}%   {c['median'] * 100:>9.3f}%{c['share_above_1pct'] * 100:>6.1f}%{c['share_above_5pct'] * 100:>6.1f}%   "
                  f"{dx['median'] * 100:>15.4f}%   {qr['open_over_day'][k]['median'] * 100:>9.2f}%{qr['close_over_day'][k]['median'] * 100:>10.2f}%")

    print(f"\n    median dollar volume by quintile (the denominators themselves)")
    print(f"      {'q':>2}{'09:30 minute':>16}{'16:00 minute':>16}{'whole day (in)':>18}{'whole day (out)':>18}")
    for k in range(N_QUINTILES):
        if not qb["open_min"][k]["25000"]["n"]:
            continue
        print(f"      {k:>2}{qb['open_min'][k]['dollar_volume']['median']:>16,.0f}{qb['close_min'][k]['dollar_volume']['median']:>16,.0f}"
              f"{qb['day_entry'][k]['dollar_volume']['median']:>18,.0f}{qb['day_exit'][k]['dollar_volume']['median']:>18,.0f}")

    # ---------------- the free-rider panel
    blocks_pool = {lab: part_block(ok_pool, lab) for lab in LAB}
    rr_pool = dict(open_over_day=stats_of([r["ratio_open_day"] for r in ok_pool]),
                   close_over_day=stats_of([r["ratio_close_day"] for r in ok_pool]))
    print(f"\n  THE SAME TABLE ON THE WHOLE POOL -- the {len(ok)} sampled trades PLUS the {len(ok_pool) - len(ok)} free riders the same "
          f"{len(req)} requests already paid for. OPPORTUNISTIC, NOT A RANDOM SAMPLE: a trade is here because another trade in that name and month")
    print(f"  was drawn, so names with clustered events are over-represented. Printed for its n, never as the headline.")
    print(f"\n  {'denominator':<22}{'median $vol':>16}   " + "".join(f"{'$' + str(p // 1000) + 'k med':>11}{'p90':>10}{'p99':>10}{'>1%':>8}{'>5%':>8}" for p in POSITIONS))
    for lab in ("open_min", "day_entry", "close_min", "day_exit"):
        b = blocks_pool[lab]
        line = f"  {LAB[lab]:<22}{b['dollar_volume']['median']:>16,.0f}   "
        for pos in POSITIONS:
            d = b[str(pos)]
            line += f"{d['median'] * 100:>10.3f}%{d['p90'] * 100:>9.2f}%{d['p99'] * 100:>9.2f}%{d['share_above_1pct'] * 100:>7.1f}%{d['share_above_5pct'] * 100:>7.1f}%"
        print(line)
    print(f"    {'':<26}{'p25':>10}{'median':>10}{'p75':>10}{'mean':>10}{'p90':>10}{'p99':>10}{'min':>10}{'max':>10}")
    for k, nm in (("open_over_day", "09:30 minute / whole day"), ("close_over_day", "16:00 minute / whole day")):
        s = rr_pool[k]
        print(f"    {nm:<26}" + "".join(f"{s[f] * 100:>9.2f}%" for f in ("p25", "median", "p75", "mean", "p90", "p99", "min", "max")))

    print(f"\n  [REC] RECONCILIATION -- summed 1-minute regular-session share volume against the daily fixture's volume, same (symbol, date).")
    rec_rows = reconcile(minutes, daily)
    R = assert_REC(rec_rows)
    SIX = assert_6(rec_rows)
    aud = stats_of([x["auction_share_of_daily"] for x in rec_rows])
    cont = stats_of([x["ratio_continuous"] for x in rec_rows])
    dol = stats_of([x["ratio_dollar"] for x in rec_rows])
    print(f"    {'quantity':<38}{'p25':>10}{'median':>10}{'p75':>10}{'min':>10}{'max':>10}{'n':>7}")
    for nm, s in (("sum(09:30..16:00) / daily volume", dict(p25=R["p25"], median=R["median"], p75=R["p75"], min=R["min"], max=R["max"], n=R["n"])),
                  ("sum(09:30..15:59) / daily volume", cont),
                  ("the 16:00 minute alone / daily volume", aud),
                  ("dollar-volume version (split-invariant)", dol)):
        print(f"    {nm:<38}{s['p25']:>10.4f}{s['median']:>10.4f}{s['p75']:>10.4f}{s['min']:>10.4f}{s['max']:>10.4f}{s['n']:>7}")
    print(f"    a full 1-minute regular session is 391 bars (390 continuous + the 16:00 auction). Complete here: {R['full_sessions']} of {R['n']}.")
    print(f"      median SHARE  ratio   full sessions {R['median_share_full']:.4f}   partial {R['median_share_partial']:.4f}")
    print(f"      median DOLLAR ratio   full sessions {R['median_dollar_full']:.4f}   partial {R['median_dollar_partial']:.4f}")
    print(f"\n    OUTSIDE {R['band']} -- every one named, share ratio and dollar ratio side by side. The daily fixture is SPLIT-ADJUSTED")
    print(f"    (volumes MULTIPLIED by the split factor) and these bars are AS-TRADED, so a name that split after its bar reads 1/f in the")
    print(f"    SHARE ratio and unchanged in the DOLLAR one. `implied f` is dollar/share and is the frame artefact made visible.")
    for nm, key in (("SHARE", "share"), ("DOLLAR (split-invariant)", "dollar")):
        b = R[key]
        print(f"\n    {nm}: {b['outside_band']} of {R['n']} ({b['outside_share']:.1%}) outside; "
              f"{len(b['symbols_outside'])} distinct symbols" + (f" -- {', '.join(b['symbols_outside'])}" if b["symbols_outside"] else ""))
        print(f"      {'symbol':<8}{'date':<12}{'share':>9}{'dollar':>9}{'implied f':>11}{'minutes':>15}{'daily':>15}{'bars':>6}")
        for o in b["outside"][:25]:
            print(f"      {o['symbol']:<8}{o['date']:<12}{o['ratio']:>9.4f}{o['ratio_dollar']:>9.4f}{o['implied_split_factor']:>11.2f}"
                  f"{o['minutes']:>15,.0f}{o['daily']:>15,.0f}{o['minute_bars']:>6}")
        if len(b["outside"]) > 25:
            print(f"      ... and {len(b['outside']) - 25} more, all in the JSON")
    print(f"\n    [6] {SIX['note']}: a global x{SIX['global_scale']:.0f} RAISED; ({SIX['single']['symbol']}, {SIX['single']['date']}) x"
          f"{SIX['single']['scale']:.0f} was NAMED without failing.")
    print(f"    WHAT THIS COSTS THE MEASUREMENT: the endpoint carries a median {R['dollar']['median']:.0%} of the consolidated day in dollar")
    print(f"    terms ({R['median_dollar_full']:.0%} on complete sessions), so if the 09:30 and 16:00 bars are short by the same fraction the")
    print(f"    participation numbers above are OVERSTATED by roughly 1/{R['dollar']['median']:.2f} = {1 / R['dollar']['median']:.2f}x. That")
    print(f"    correction runs the SAME way for both denominators, so it does not touch the RATIO, which is the finding.")

    # ---------------- survivorship
    SV = S["survivorship"]
    print(f"\n  SURVIVORSHIP -- what the intraday endpoint cannot serve, and what that costs this sample")
    print(f"    {SV['excluded']['n']:,} of {SV['kept']['n'] + SV['excluded']['n']:,} A2 trades ({SV['excluded']['share']:.1%}) are on names "
          f"the endpoint will not serve (status_meta 'delisted').")
    print(f"    gross mean      kept {SV['kept']['gross_mean_bp']:+8.2f} bp    excluded {SV['excluded']['gross_mean_bp']:+8.2f} bp    "
          f"delta {SV['delta_gross_bp']:+.2f} bp")
    print(f"    PUB half-spread kept {SV['kept']['pub_mean_bp']:8.2f} bp    excluded {SV['excluded']['pub_mean_bp']:8.2f} bp    "
          f"delta {SV['delta_pub_bp']:+.2f} bp")
    print(f"    median $vol(g)  kept {SV['kept']['dollar_vol_g_median']:>14,.0f}    excluded {SV['excluded']['dollar_vol_g_median']:>14,.0f}")
    print(f"    excluded per quintile {SV['excluded']['by_quintile']}")

    obj = dict(study=STUDY, note=("D364 -- MEASUREMENT ONLY. The auction bound on the gap-up fade's participation: the 09:30 and 16:00 "
                                  "one-minute bars as an UPPER BOUND on the auction prints the strategy actually fills against, beside "
                                  "D363's whole-day denominator. Nothing scored, nothing predicted, nothing promoted."),
               written_at_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
               sample=dict(path=str(sp), where=where, seed=S["seed"], n=len(S["sample"]), requests=len(S["requests"])),
               K=K, S=Sv, AX=axd, TZ=tz, probe=dict(symbol=pr["symbol"], month=pr["month"], passed=pr["passed"],
                                                    share_1600_of_rth=pr.get("share_1600_of_rth"),
                                                    share_0930_of_rth=pr.get("share_0930_of_rth")) if pr else None,
               coverage=dict(sampled=len(S["sample"]), free_riders=len(bonus), pool=len(pool), sessions_loaded=len(minutes),
                             slices_missing=[list(x) for x in missing], no_open_bar=n_no_open, no_close_bar=n_no_close,
                             why_missing=miss, complete=len(ok), complete_pool=len(ok_pool),
                             no_1600_bar=[dict(symbol=r["symbol"], date=r["date_exit"], rth_bars=r["exit_rth_bars"],
                                               last_rth=r["exit_last_rth"], last_stamp=r["exit_last_any"], quintile=r["quintile"])
                                          for r in sorted(nb, key=lambda x: x["date_exit"])],
                             no_1600_by_quintile={str(k): v for k, v in sorted(Counter(r["quintile"] for r in nb).items())}),
               denominators=dict(
                   open_min="close x volume of the 09:30 one-minute bar on the ENTRY date (the opening auction plus one minute of continuous trade)",
                   close_min="close x volume of the 16:00 one-minute bar on the EXIT date (the closing auction plus one minute)",
                   day_entry="close x volume of the daily fixture's bar on the ENTRY date (D363's denominator)",
                   day_exit="close x volume of the daily fixture's bar on the EXIT date",
                   bound="the minute bars are an UPPER bound on the auction, so true auction participation is LARGER than every number here"),
               participation=blocks, participation_by_quintile=qb, ratio=rr, ratio_by_quintile=qr,
               pooled=dict(n=len(ok_pool), participation=blocks_pool, ratio=rr_pool,
                           what=("the stratified sample PLUS every other A2 trade whose entry and exit months were already bought. "
                                 "OPPORTUNISTIC, not a random sample: over-represents names whose events cluster in one month. "
                                 "Reported for its n; the headline is the stratified sample.")),
               positions=list(POSITIONS),
               REC=R, REC_rows=rec_rows, REC_auxiliary=dict(continuous=cont, auction_share_of_daily=aud, dollar=dol), SIX=SIX,
               survivorship=SV, strata=S["strata"], sinks=[list(x) for x in S1S2], guard=guard_line(),
               d363_comparison=dict(stored=d363_participation(),
                                    note=("D363's own stored participation block, READ from data/d363_cost_lines.json and not retyped -- "
                                          "the whole-day denominator this record re-denominates. Its ledger is the RE-SIMULATED A2 arm "
                                          "(3,079 trades) and this sample is drawn from the row-drop arm (3,028), so the two whole-day "
                                          "columns are close but not identical objects.")))
    h = dump(p["report"], obj)
    print(f"\n  wrote {p['report']}  ({p['report'].stat().st_size / 1e3:.1f} kB)  payload sha256 {h[:16]}...")
    print(f"  [HOLDOUT-GUARD] {guard_line()}")
    return 0


# ------------------------------------------------------------------ --selftest
def do_selftest():
    print("D364 --selftest\n")
    ok = []

    print(f"  [HOLDOUT-GUARD] {assert_HOLDOUT_GUARD()}")
    ok.append("HOLDOUT-GUARD")

    s_src, s_rep = S1S2, sinks_from_d362_report()
    assert s_src == s_rep, f"the source-parsed sinks {s_src} differ from D362's committed result {s_rep}"
    assert s_src == (("S1", "pcto_mass_imbalance", ">=", 86.84), ("S2", "mkt_vol_20", "<=", 99.03)), f"the sinks moved: {s_src}"
    print(f"  [SINKS] parsed from {SINK_SOURCE}'s source == {D362_REPORT.name}'s own record: {s_src}")
    ok.append("SINKS")

    rows, cols, src = read_export()
    ax, _ = scan_fixture()
    axd = assert_AX(ax, rows, cols)
    print(f"  [AX] {axd['pairs']:,} pairs reproduced ({axd['axis']:,} dates, {axd['first']} .. {axd['last']})")
    ok.append("AX")
    bad_ax = list(ax)
    bad_ax[axd["axis"] // 2] = "1999-01-01"
    raised = False
    try:
        assert_AX(bad_ax, rows, cols)
    except AssertionError:
        raised = True
    assert raised, "[AX] did not raise on a corrupted axis"
    print(f"  [AX] raises on a corrupted axis")

    tr = a2_arm(rows, cols, ax)
    S = assert_S(tr)
    print(f"  [S] {S['trades']:,} / {S['mean_bp']:+.6f} == D362's stored row-drop A2 {S['stored_rowdrop_trades']:,} / "
          f"{S['stored_rowdrop_mean_bp']:+.6f}; re-simulated arm {S['stored_resim_trades']:,} / {S['stored_resim_mean_bp']:+.6f}")
    ok.append("S")
    raised = False
    try:
        assert_S(tr[:-1])
    except AssertionError:
        raised = True
    assert raised, "[S] did not raise on a truncated arm"
    print(f"  [S] raises on a truncated arm")

    pub = np.array([t["pub_bp"] for t in tr])
    q = quintiles(pub)
    assert sorted(Counter(q.tolist()).values()) == sorted(Counter(q.tolist()).values())
    assert set(q.tolist()) == set(range(N_QUINTILES)) and abs(max(Counter(q.tolist()).values()) - min(Counter(q.tolist()).values())) <= 1, "quintiles are not equal-count"
    for k in range(N_QUINTILES - 1):
        assert pub[q == k].max() <= pub[q == k + 1].max(), "quintiles are not monotone in PUB"
    print(f"  [Q] {N_QUINTILES} equal-count quintiles, monotone in half_spread_PUB_bp, ties by ledger order")
    ok.append("Q")

    for j, t in enumerate(tr):
        t["quintile"] = int(q[j])
    D1 = draw_sample(tr, q)
    D2 = draw_sample(tr, q)
    assert D1["idx"] == D2["idx"] and D1["requests"] == D2["requests"], "the draw is not reproducible under the same seed"
    D3 = draw_sample(tr, q, seed=SEED + 1)
    assert D3["idx"] != D1["idx"], "the draw does not depend on the seed"
    assert len(D1["requests"]) <= MAX_REQUESTS, f"the draw exceeds the budget: {len(D1['requests'])}"
    assert all(tr[j]["status"] in LIVE_STATUS for j in D1["idx"]), "the draw contains a name the endpoint will not serve"
    cnt = Counter(tr[j]["quintile"] for j in D1["idx"])
    assert len(set(cnt.values())) == 1, f"the draw is not equal per quintile: {dict(cnt)}"
    print(f"  [DRAW] seed {SEED} reproducible, seed-dependent, {D1['K']} per quintile = {len(D1['idx'])} trades in "
          f"{len(D1['requests'])} <= {MAX_REQUESTS} requests, every name still listed")
    ok.append("DRAW")

    for j in D1["idx"][:200]:
        t = tr[j]
        assert t["bar_exit"] == t["bar_entry"] + t["hold"] - 1 and ax[t["bar_exit"]] == t["date_exit"], "exit bar / date mismatch"
        assert t["date_exit"] >= t["date_entry"], "the exit precedes the entry"
    print(f"  [EXIT] exit bar == bar_entry + hold_cap10 - 1 and its date is the axis's, on the sample")
    ok.append("EXIT")

    tmp = REPO / "temp" / "d364_selftest"
    tmp.mkdir(parents=True, exist_ok=True)
    obj = dict(a=1, b=[1, 2, 3])
    h = dump(tmp / "h.json", obj)
    back = json.loads((tmp / "h.json").read_text())
    assert payload_hash(back) == back["payload_sha256"] == h, "[K] the payload hash does not round-trip"
    back["a"] = 2
    assert payload_hash(back) != back["payload_sha256"], "[K] the payload hash does not detect an edit"
    print(f"  [K] the payload hash round-trips and detects an edit")
    ok.append("K")

    fake = [dict(symbol=f"S{i:02d}", date="2020-01-02", ratio=1.00 + 0.005 * i, ratio_dollar=1.00 + 0.005 * i, v_minutes_0930_1600=1e6,
                 dv_minutes_0930_1600=1e7, v_daily=1e6, dv_daily=1e7, minute_bars=391, minute_bars_continuous=390,
                 ratio_continuous=0.97, auction_share_of_daily=0.03, implied_split_factor=1.0) for i in range(20)]
    R = assert_REC(fake)
    assert R["share"]["outside_band"] == 0 and R["dollar"]["outside_band"] == 0, "[REC] found a band violation where there is none"
    SIX = assert_6(fake)
    print(f"  [REC] passes a clean set; [6] a global x{SIX['global_scale']:.0f} RAISES and a single x5 is NAMED ({SIX['single']['symbol']})")
    ok.append("REC")
    ok.append("6")

    for bad, why in (([dict(x, ratio=0.2, ratio_dollar=0.2) for x in fake], "a uniformly quartered tape"),
                     ([dict(x, ratio_dollar=1e4) for x in fake], "an order-of-magnitude keying error"),
                     ([dict(x, v_daily=0.0) for x in fake], "zero daily volume")):
        raised = False
        try:
            assert_REC(bad)
        except AssertionError:
            raised = True
        assert raised, f"[REC] did not raise on {why}"
    # and the split case must NOT raise: a 15-for-1 name reads 1/15 in SHARE and 1.0 in DOLLAR, which is a frame fact, not a tape fact
    split = [dict(x, ratio=x["ratio"] / 15.0, implied_split_factor=15.0) for x in fake]
    Rs = assert_REC(split)
    assert Rs["share"]["outside_band"] == len(fake) and Rs["dollar"]["outside_band"] == 0, "[REC] mis-handles a split-adjusted frame"
    print(f"  [REC] raises on a uniformly disagreeing tape, an order-of-magnitude error and a zero daily volume; a 15-for-1 SPLIT is NAMED "
          f"in SHARE ({Rs['share']['outside_band']}) and clean in DOLLAR ({Rs['dollar']['outside_band']}), not fatal")

    pr_ok = dict(timezone="US/Eastern", per_day=[dict(date="2024-01-03", rth_bars=390, rth_first="09:30", rth_last="16:00")])
    assert_TZ(pr_ok)
    for bad, why in ((dict(pr_ok, timezone="UTC"), "timezone"),
                     (dict(pr_ok, per_day=[dict(pr_ok["per_day"][0], rth_first="09:31")]), "first stamp"),
                     (dict(pr_ok, per_day=[dict(pr_ok["per_day"][0], rth_last="16:01")]), "last stamp"),
                     (dict(pr_ok, per_day=[dict(pr_ok["per_day"][0], rth_bars=10)]), "no full session")):
        r = False
        try:
            assert_TZ(bad)
        except AssertionError:
            r = True
        assert r, f"[TZ] did not raise on a bad {why}"
    print(f"  [TZ] passes a good probe and raises on a bad timezone, first stamp, last stamp and a month with no full session")
    ok.append("TZ")

    assert E.INTERVAL == "1min" and E.slice_path("ZZZ", "2020-01") == E.CACHE / "1min" / "ZZZ" / "2020-01.json.gz", "the interval override drifted"
    assert (E.CACHE / "15min").exists(), "the 15-minute cache should still be there and untouched"
    assert not (E.CACHE / "1min" / "ZZZ").exists(), "slice_path should not create anything"
    print(f"  [AV] interval override holds: cache {E.slice_path('ZZZ', '2020-01').parent.parent.relative_to(REPO)}, "
          f"the 15-minute tree untouched")
    ok.append("AV")

    sess = {"09:30": (1, 1, 1, 10.0, 100.0), "09:31": (1, 1, 1, 10.0, 50.0), "15:59": (1, 1, 1, 10.0, 20.0), "16:00": (1, 1, 1, 10.0, 500.0),
            "16:01": (1, 1, 1, 10.0, 7.0), "04:00": (1, 1, 1, 10.0, 3.0)}
    v_c, d_c, n_c = rth_volume(sess, False)
    v_a, d_a, n_a = rth_volume(sess, True)
    assert (v_c, n_c) == (170.0, 3) and (v_a, n_a) == (670.0, 4), f"rth_volume: {(v_c, n_c)} {(v_a, n_a)}"
    assert d_a == 6700.0 and minute_dv(sess, "16:00") == 5000.0 and math.isnan(minute_dv(sess, "12:00")), "minute dollar volume"
    print(f"  [MIN] the regular window is 09:30..15:59 continuous and 09:30..16:00 with the auction; pre- and post-market excluded")
    ok.append("MIN")

    print(f"\n  SELFTEST PASS -- {len(ok)} groups: {', '.join(ok)}")
    return 0


# ------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out-dir", default=str(DATA))
    ap.add_argument("--limit", type=int, default=None, help="cap the requests this run (--fetch)")
    ap.add_argument("--retry-unserved", action="store_true", help="re-ask for (symbol, month) pairs the provider has already refused")
    a = ap.parse_args()
    if a.selftest:
        return do_selftest()
    if a.plan:
        return do_plan(a.out_dir)
    if a.probe:
        return do_probe(a.out_dir)
    if a.fetch:
        return do_fetch(a.out_dir, a.limit, a.retry_unserved)
    if a.report:
        return do_report(a.out_dir)
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
