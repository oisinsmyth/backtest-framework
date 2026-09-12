"""CME futures, 1-minute bars, for the prop track: fetch, validate, record. NOT a study.

    uv run python scripts/fetch_futures_1m.py --plan                # offline: the prior, per symbol
    uv run python scripts/fetch_futures_1m.py --self-test           # offline: every gate fires on a broken book
    uv run python scripts/fetch_futures_1m.py --verify              # FREE: unit prices, range, roll rules, negative controls
    uv run python scripts/fetch_futures_1m.py --cost --tiers 1,3    # FREE: Databento's own quote, PER SYMBOL
    uv run python scripts/fetch_futures_1m.py --submit --tiers 1,3 --i-accept-the-cost USD
                                                                    # THE ONLY MODE THAT SPENDS
    uv run python scripts/fetch_futures_1m.py --download            # free: pull finished batch jobs to temp/
    uv run python scripts/fetch_futures_1m.py --build               # decode -> fixture (gitignored) + meta + rolls
    uv run python scripts/fetch_futures_1m.py --validate            # the seven gates; every one RAISES

The order is the order. `--cost` refuses without a `--verify` stamp bound to this
configuration; `--submit` refuses without a `--cost` stamp for the same tiers and an
accepted figure equal to Databento's quote to the cent; and a running ledger refuses
any submission that would take cumulative accepted spend above SPEND_CAP_USD.

WHAT THIS IS
------------
`docs/prop firm leads/02-data-acquisition-prompt.md`. The prop track has never looked at
the instrument it would trade: every number on it is measured on an extended-hours
equity proxy covering 16 of 23 futures hours. This fetches GLBX.MDP3 `ohlcv-1m` on
continuous symbology for three tiers and validates it. **No returns, no signals, no
strategy code live here.** If a function in this file computes an edge, it is a bug.

WHAT THE CONTINUOUS SERIES IS -- settled on Databento's own documentation, 2026-09-10
-----------------------------------------------------------------------------------
`[ROOT].[ROLL_RULE].[RANK]`; `c` = calendar (offset from nearest expiry), `v` = ranked
by the PREVIOUS DAY's volume, `n` = ranked by the previous day's open interest. And,
verbatim: *"The continuous contract prices returned are the original, unadjusted
prices. We don't create a synthetic time series by back-adjusting the prices to remove
jumps during rollovers."*

So the fixture is UNADJUSTED, and every roll is a real basis jump between two
contracts, not a synthetic one. That decides how the roll trap is handled: the bars
carry the instrument_id, the roll dates are a committed artifact, and the MAE consumer
must never measure an excursion across an instrument change. Gate 2 asserts that every
instrument change in the bars is in the artifact and that no UNFLAGGED bar-to-bar move
exceeds the D226 limit; it reports every roll gap against the non-roll distribution.

`v` is chosen over `c` because `c` is the Yahoo ES=F failure bought deliberately (rolls
at expiry, so the last week of each quarter tracks the dying contract). `v` ranks by the
previous day's volume, so it can flip back and forth around a crossover; the artifact
counts those and the validator reports them.

WHAT CANNOT BE COMMITTED
------------------------
Exchange-licensed bars. `.gitignore` already excludes `data/fixtures/*glbx*`, and
`docs/research/futures-data/00-SYNTHESIS.md` §3 is the reason. What IS committed:
the spec file, the meta, the roll-date artifact, the validation report and the spend
ledger -- everything a record would quote -- plus this script, which rebuilds the
fixture from a re-download (free for 30 days after the job).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------- configuration

DATASET = "GLBX.MDP3"
SCHEMA = "ohlcv-1m"
STYPE_IN = "continuous"
STYPE_OUT = "instrument_id"     # the only stype_out continuous supports (Databento symbology table)
ROLL_RULE = "v"                 # previous-day volume rank; see the docstring
RANK = 0
ENCODING = "dbn"
COMPRESSION = "zstd"
DATASET_START = "2010-06-06"    # GLBX.MDP3 begins here

TIERS: dict[int, list[str]] = {
    1: ["ES", "NQ", "RTY", "YM"],
    # PROPOSED, not assumed: energy x2, metals x3, rates x3. The principal approves this
    # list from the per-symbol cost lines that --cost prints.
    2: ["CL", "NG", "GC", "SI", "HG", "ZN", "ZB", "ZF"],
    3: ["MES", "MNQ", "M2K", "MYM"],
}
# Expected first bar, for the PRIOR only. The fixture's own first bar is what is recorded.
EXPECTED_FIRST_BAR = {
    "RTY": "2017-07-10",        # E-mini Russell moved to CME in July 2017 -- market structure
    "MES": "2019-05-06", "MNQ": "2019-05-06", "M2K": "2019-05-06", "MYM": "2019-05-06",
}

FREE_CREDIT_USD = 125.00
SPEND_CAP_USD = 110.00          # hard boundary 2 of the prompt
PRIOR_USD_PER_SYMBOL_YEAR = 0.5079   # derived in data-purchase-proposal.md §4
PRIOR_TOLERANCE = 2.0           # "if your dry run differs by more than 2x, stop"
OHLCV_MSG_BYTES = 56

KEY_FILE = Path.home() / ".config" / "databento" / "key"
RAW = REPO / "data" / "raw" / "databento"             # moved 2026-09-12: 111 GB is NOT deletable
FIXTURE_DIR = REPO / "data" / "fixtures"             # glbx_1m_{SYM}.parquet -- gitignored by *glbx*
META = REPO / "data" / "futures_1m.meta.json"        # committed
ROLLS = REPO / "data" / "futures_1m_rolls.json"      # committed
REPORT = REPO / "data" / "futures_1m_validation.json"  # committed
LEDGER = REPO / "data" / "futures_1m_spend.json"     # committed
SPECS = REPO / "data" / "futures_contract_specs.json"  # committed, from CME's own pages
VERIFY_STAMP = RAW / "verify.json"
COST_STAMP = RAW / "cost.json"
JOBS = RAW / "jobs.json"
SPY_DAILY = FIXTURE_DIR / "etf_wide_daily_raw.csv.gz"

ET = "America/New_York"
MOVE_LIMIT = 0.15               # D226's single-bar limit, reused by futures_continuous.py
CORR_FLOOR = 0.95               # ES RTH close vs SPY close, daily log returns
USER_AGENT = "backtest-framework (personal research)"


class GateError(AssertionError):
    """A validation gate failed. Every gate raises this and nothing catches it
    except --self-test, which exists to prove they fire."""


def fixture_path(sym: str) -> Path:
    return FIXTURE_DIR / f"glbx_1m_{sym}.parquet"


def continuous(sym: str) -> str:
    return f"{sym}.{ROLL_RULE}.{RANK}"


def tiers_arg(s: str | None) -> list[int]:
    if not s:
        return [1, 3]
    out = sorted({int(x) for x in s.split(",") if x.strip()})
    bad = [t for t in out if t not in TIERS]
    if bad:
        raise SystemExit(f"unknown tiers {bad}; known {sorted(TIERS)}")
    return out


def symbols_for(tiers: list[int]) -> list[str]:
    return [s for t in tiers for s in TIERS[t]]


def config_fingerprint() -> str:
    payload = json.dumps({
        "dataset": DATASET, "schema": SCHEMA, "stype_in": STYPE_IN, "stype_out": STYPE_OUT,
        "roll_rule": ROLL_RULE, "rank": RANK, "encoding": ENCODING,
        "compression": COMPRESSION, "tiers": {str(k): v for k, v in TIERS.items()},
        "start": DATASET_START,
    }, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def api_key() -> str:
    key = os.environ.get("DATABENTO_API_KEY")
    if key:
        return key.strip()
    if KEY_FILE.exists():
        return KEY_FILE.read_text(encoding="utf-8").strip()
    raise SystemExit(
        "No Databento API key. The principal creates the account and holds the key "
        f"(hard boundary 1). Set DATABENTO_API_KEY or write {KEY_FILE}."
    )


def client():
    import databento as db
    c = db.Historical(api_key())
    return c


def specs() -> dict:
    s = json.loads(SPECS.read_text(encoding="utf-8"))
    out = {k: v for k, v in s.items() if isinstance(v, dict) and "usd_per_point" in v}
    for k, v in out.items():
        if abs(v["usd_per_point"] * v["tick_points"] - v["tick_usd"]) > 1e-9:
            raise GateError(f"spec {k}: usd_per_point*tick_points != tick_usd")
    return out


def load_stamp(path: Path, what: str) -> dict:
    if not path.exists():
        raise SystemExit(f"{what}: run the previous mode first (it is free).")
    st = json.loads(path.read_text(encoding="utf-8"))
    if st.get("config_fingerprint") != config_fingerprint():
        raise SystemExit(
            f"{what}: the configuration changed since {path.name} was written "
            f"({st.get('config_fingerprint')} vs {config_fingerprint()}). Re-run from --verify."
        )
    return st


def years_between(a: str, b: str) -> float:
    return (pd.Timestamp(b) - pd.Timestamp(a)).days / 365.25


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ------------------------------------------------------------------ --plan

def do_plan(tiers: list[int]) -> int:
    end = date.today().isoformat()
    print(f"prior: ${PRIOR_USD_PER_SYMBOL_YEAR:.4f}/symbol-year, {OHLCV_MSG_BYTES} B/bar, "
          f"no bar without a trade\n")
    print(f"  {'tier':4} {'sym':4} {'from':10} {'years':>6} {'USD':>7}")
    tot = 0.0
    for t in tiers:
        for s in TIERS[t]:
            start = EXPECTED_FIRST_BAR.get(s, DATASET_START)
            yrs = years_between(start, end)
            usd = yrs * PRIOR_USD_PER_SYMBOL_YEAR
            tot += usd
            print(f"  {t:<4} {s:4} {start:10} {yrs:6.2f} {usd:7.2f}")
    print(f"\n  TOTAL (prior)  ${tot:.2f}   cap ${SPEND_CAP_USD:.2f}   credit ${FREE_CREDIT_USD:.2f}")
    print(f"  symbology      {continuous('ES')}  ({ROLL_RULE} = previous-day volume rank; unadjusted)")
    return 0


# ---------------------------------------------------------------- --verify

def do_verify() -> int:
    c = client()
    checks: list[tuple[str, bool, str]] = []

    prices = c.metadata.list_unit_prices(DATASET)
    print("\nlist_unit_prices(GLBX.MDP3) -- the actual table:")
    rate = None
    for entry in prices:
        mode = entry.get("mode")
        up = entry.get("unit_prices", {})
        line = ", ".join(f"{k}={v}" for k, v in sorted(up.items()))
        print(f"  [{mode}] {line}")
        if mode == "historical":
            rate = float(up.get(SCHEMA)) if SCHEMA in up else None
            trades_rate = float(up.get("trades")) if "trades" in up else None
    checks.append((f"{SCHEMA} unit price present", rate is not None, f"{rate}"))
    if rate is not None and trades_rate is not None:
        checks.append((f"{SCHEMA} bills like trades (the one inferred step)",
                       abs(rate - trades_rate) < 1e-9, f"{rate} vs trades {trades_rate}"))
    checks.append((f"{SCHEMA} unit price ~ $28/GB", rate is not None and abs(rate - 28.0) / 28.0 < 0.10,
                   f"{rate}"))

    rng = c.metadata.get_dataset_range(DATASET)
    start = str(rng.get("start", ""))[:10]
    end = str(rng.get("end", ""))[:10]
    checks.append((f"history reaches {DATASET_START}", bool(start) and start <= DATASET_START,
                   f"{start}..{end}"))

    schemas = c.metadata.list_schemas(DATASET)
    checks.append((f"schema {SCHEMA} listed", SCHEMA in schemas, ""))

    # Roll-rule letters, from a free resolve, and the negative control on the resolver.
    for letter, meaning in (("c", "calendar"), ("v", "volume"), ("n", "open interest")):
        r = c.symbology.resolve(DATASET, symbols=[f"ES.{letter}.0"], stype_in=STYPE_IN,
                                stype_out=STYPE_OUT, start_date="2024-03-01", end_date="2024-03-31")
        ok = r.get("status") == 0 and bool(r.get("result", {}).get(f"ES.{letter}.0"))
        n = len(r.get("result", {}).get(f"ES.{letter}.0", []))
        checks.append((f"ES.{letter}.0 resolves ({meaning})", ok, f"{n} intervals in March 2024"))
        if letter == ROLL_RULE:
            print(f"  ES.{letter}.0 March 2024 intervals: {r['result'][f'ES.{letter}.0']}")

    # NEGATIVE CONTROL 1: a root that cannot exist must NOT resolve.
    r = c.symbology.resolve(DATASET, symbols=["ZZZQ.v.0"], stype_in=STYPE_IN, stype_out=STYPE_OUT,
                            start_date="2024-03-01", end_date="2024-03-31")
    nf = r.get("not_found", [])
    checks.append(("NEGATIVE CONTROL: ZZZQ.v.0 is not_found", "ZZZQ.v.0" in nf and not r.get("result", {}).get("ZZZQ.v.0"),
                   f"status={r.get('status')} not_found={nf}"))

    # NEGATIVE CONTROL 2: the counter must return ZERO for a symbol that cannot exist,
    # and a positive count for one that does, over the same window.
    n_real = c.metadata.get_record_count(DATASET, start="2024-03-04", end="2024-03-05",
                                         symbols=[continuous("ES")], schema=SCHEMA, stype_in=STYPE_IN)
    try:
        n_fake = c.metadata.get_record_count(DATASET, start="2024-03-04", end="2024-03-05",
                                             symbols=["ZZZQ.v.0"], schema=SCHEMA, stype_in=STYPE_IN)
        fake_detail = f"count={n_fake}"
        fake_ok = n_fake == 0
    except Exception as exc:  # a 4xx here is also "returns nothing", and is recorded as such
        fake_detail = f"{type(exc).__name__}: {str(exc)[:80]}"
        fake_ok = True
    checks.append(("POSITIVE CONTROL: ES.v.0 one day has bars", n_real > 0, f"count={n_real}"))
    checks.append(("NEGATIVE CONTROL: ZZZQ.v.0 one day has none", fake_ok, fake_detail))
    checks.append(("one ES day is at most 1380 bars", 0 < n_real <= 1380, f"count={n_real}"))

    print()
    for label, ok, detail in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {label:52} {detail}")
    if any(not ok for _l, ok, _d in checks):
        print("\nVERIFY FAILED. --cost and --submit stay locked.")
        return 1

    RAW.mkdir(parents=True, exist_ok=True)
    VERIFY_STAMP.write_text(json.dumps({
        "verified_utc": now_iso(), "config_fingerprint": config_fingerprint(),
        "unit_prices": prices, "unit_price_ohlcv_1m": rate,
        "dataset_range": {"start": start, "end": end},
        "checks": [{"check": l, "pass": ok, "detail": d} for l, ok, d in checks],
    }, indent=1) + "\n", encoding="utf-8")
    print(f"\nVERIFY PASSED -> {VERIFY_STAMP}")
    return 0


# ------------------------------------------------------------------ --cost

def do_cost(tiers: list[int]) -> int:
    st = load_stamp(VERIFY_STAMP, "--cost")
    end = st["dataset_range"]["end"]
    c = client()
    rows = []
    print(f"\n  {'tier':4} {'symbol':8} {'start':10} {'end':10} {'bytes':>14} {'bars':>12} {'USD':>8} {'prior':>7}")
    for t in tiers:
        for s in TIERS[t]:
            sym = continuous(s)
            size = c.metadata.get_billable_size(DATASET, start=DATASET_START, end=end, symbols=[sym],
                                                schema=SCHEMA, stype_in=STYPE_IN)
            usd = c.metadata.get_cost(DATASET, start=DATASET_START, end=end, symbols=[sym],
                                      schema=SCHEMA, stype_in=STYPE_IN)
            prior = years_between(EXPECTED_FIRST_BAR.get(s, DATASET_START), end) * PRIOR_USD_PER_SYMBOL_YEAR
            rows.append({"tier": t, "symbol": s, "continuous": sym, "start": DATASET_START, "end": end,
                         "billable_bytes": int(size), "bars_implied": int(size) // OHLCV_MSG_BYTES,
                         "usd": float(usd), "prior_usd": prior})
            print(f"  {t:<4} {sym:8} {DATASET_START:10} {end:10} "
                  f"{int(size):14,} {int(size)//OHLCV_MSG_BYTES:12,} {float(usd):8.2f} {prior:7.2f}")
            time.sleep(0.5)
    total = sum(r["usd"] for r in rows)
    prior = sum(r["prior_usd"] for r in rows)
    ratio = total / prior if prior else float("inf")
    print(f"\n  DATABENTO QUOTE  ${total:.2f}   prior ${prior:.2f}   ratio {ratio:.2f}x")
    print(f"  cap ${SPEND_CAP_USD:.2f}   credit ${FREE_CREDIT_USD:.2f}   ledger ${ledger_total():.2f}")
    RAW.mkdir(parents=True, exist_ok=True)
    COST_STAMP.write_text(json.dumps({
        "quoted_utc": now_iso(), "config_fingerprint": config_fingerprint(),
        "tiers": tiers, "rows": rows, "total_usd": total, "prior_usd": prior, "ratio": ratio,
    }, indent=1) + "\n", encoding="utf-8")
    if ratio > PRIOR_TOLERANCE or ratio < 1 / PRIOR_TOLERANCE:
        print(f"\n  STOP: the quote differs from the prior by more than {PRIOR_TOLERANCE}x. "
              "Do not proceed; report this.")
        return 2
    if ledger_total() + total > SPEND_CAP_USD:
        print(f"\n  STOP: ledger ${ledger_total():.2f} + quote ${total:.2f} exceeds the "
              f"${SPEND_CAP_USD:.2f} cap.")
        return 2
    print(f"\n  To proceed, after the principal's go-ahead:\n"
          f"    --submit --tiers {','.join(map(str, tiers))} --i-accept-the-cost {total:.2f}")
    return 0


def ledger_total() -> float:
    if not LEDGER.exists():
        return 0.0
    return float(sum(j.get("accepted_usd", 0.0) for j in json.loads(LEDGER.read_text(encoding="utf-8"))["jobs"]))


# ---------------------------------------------------------------- --submit

def do_submit(tiers: list[int], accepted: float | None) -> int:
    load_stamp(VERIFY_STAMP, "--submit")
    cost = load_stamp(COST_STAMP, "--submit")
    if cost["tiers"] != tiers:
        raise SystemExit(f"--submit: the cost stamp is for tiers {cost['tiers']}, not {tiers}. Re-run --cost.")
    if accepted is None:
        raise SystemExit("REFUSING TO SPEND: pass --i-accept-the-cost <Databento's quoted figure>.")
    if abs(accepted - cost["total_usd"]) > 0.005:
        raise SystemExit(f"REFUSING TO SPEND: accepted ${accepted:.2f} != quoted ${cost['total_usd']:.2f}.")
    if ledger_total() + accepted > SPEND_CAP_USD:
        raise SystemExit(f"REFUSING TO SPEND: ledger ${ledger_total():.2f} + ${accepted:.2f} > cap ${SPEND_CAP_USD:.2f}.")

    c = client()
    end = cost["rows"][0]["end"]
    jobs = json.loads(JOBS.read_text(encoding="utf-8")) if JOBS.exists() else {"jobs": []}
    ledger = json.loads(LEDGER.read_text(encoding="utf-8")) if LEDGER.exists() else {"jobs": []}
    for t in tiers:
        syms = [continuous(s) for s in TIERS[t]]
        quoted = sum(r["usd"] for r in cost["rows"] if r["tier"] == t)
        # batch.submit_job, never streaming: billed once, re-downloadable free for 30 days.
        job = c.batch.submit_job(
            dataset=DATASET, symbols=syms, schema=SCHEMA, start=DATASET_START, end=end,
            encoding=ENCODING, compression=COMPRESSION, split_symbols=True, split_duration="year",
            stype_in=STYPE_IN, stype_out=STYPE_OUT, delivery="download",
        )
        rec = {"tier": t, "symbols": syms, "start": DATASET_START, "end": end,
               "submitted_utc": now_iso(), "job": job, "accepted_usd": quoted}
        jobs["jobs"].append(rec)
        ledger["jobs"].append({"tier": t, "symbols": syms, "job_id": job.get("id"),
                               "submitted_utc": rec["submitted_utc"], "accepted_usd": quoted,
                               "vendor_cost_field": {k: v for k, v in job.items() if "cost" in k.lower()}})
        print(f"  submitted tier {t}: job {job.get('id')}  state={job.get('state')}  quoted ${quoted:.2f}")
        JOBS.write_text(json.dumps(jobs, indent=1, default=str) + "\n", encoding="utf-8")
        LEDGER.write_text(json.dumps(ledger, indent=1, default=str) + "\n", encoding="utf-8")
    print(f"\n  ledger now ${ledger_total():.2f} of ${SPEND_CAP_USD:.2f} cap. Next: --download (free).")
    return 0


# -------------------------------------------------------------- --download

def do_download() -> int:
    if not JOBS.exists():
        raise SystemExit("--download: no jobs recorded; run --submit first.")
    c = client()
    jobs = json.loads(JOBS.read_text(encoding="utf-8"))
    live = {j["id"]: j for j in c.batch.list_jobs(states="queued,processing,done,expired")}
    pending = 0
    for rec in jobs["jobs"]:
        jid = rec["job"]["id"]
        state = live.get(jid, {}).get("state", "unknown")
        rec["job"] = live.get(jid, rec["job"])
        out = RAW / jid
        if state != "done":
            print(f"  job {jid} tier {rec['tier']}: {state}")
            pending += 1
            continue
        if out.exists() and any(out.glob("*.dbn.zst")):
            print(f"  job {jid} tier {rec['tier']}: already on disk ({len(list(out.glob('*.dbn.zst')))} files)")
            continue
        out.mkdir(parents=True, exist_ok=True)
        paths = c.batch.download(job_id=jid, output_dir=RAW)
        print(f"  job {jid} tier {rec['tier']}: downloaded {len(paths)} files -> {out}")
    JOBS.write_text(json.dumps(jobs, indent=1, default=str) + "\n", encoding="utf-8")
    if pending:
        print(f"\n  {pending} job(s) not done yet. Re-run --download later; do NOT resubmit.")
        return 3
    return 0


# ----------------------------------------------------------------- --build

def decode_job_dir(job_dir: Path) -> tuple[dict[str, pd.DataFrame], dict[str, list[dict]]]:
    """DBN -> per-root DataFrame of bars (UTC index) + per-root vendor mapping intervals."""
    import databento as db
    frames: dict[str, list[pd.DataFrame]] = {}
    mappings: dict[str, list[dict]] = {}
    for p in sorted(job_dir.glob("*.dbn.zst")):
        store = db.DBNStore.from_file(p)
        df = store.to_df(price_type="float", pretty_ts=True, map_symbols=False)
        for csym, ivs in store.mappings.items():
            root = csym.split(".")[0]
            mappings.setdefault(root, [])
            for iv in ivs:
                d = {"start_date": str(iv["start_date"])[:10], "end_date": str(iv["end_date"])[:10],
                     "instrument_id": int(iv["symbol"])}
                if d not in mappings[root]:
                    mappings[root].append(d)
        if df.empty:
            continue
        # One continuous symbol per file when split_symbols=True; recover the root from
        # the mapping, since map_symbols=False leaves only instrument_id in the frame.
        roots = list(store.mappings.keys())
        if len(roots) != 1:
            raise GateError(f"{p.name}: expected one continuous symbol per file, got {roots}")
        root = roots[0].split(".")[0]
        keep = df[["instrument_id", "open", "high", "low", "close", "volume"]].copy()
        frames.setdefault(root, []).append(keep)
    out = {}
    for root, parts in frames.items():
        df = pd.concat(parts).sort_index()
        df.index.name = "ts_event"
        out[root] = df
    for root in mappings:
        mappings[root].sort(key=lambda d: d["start_date"])
    return out, mappings


def raw_symbols_for(c, ids_by_window: list[tuple[str, str, int]]) -> dict[int, str]:
    """instrument_id -> raw contract symbol, via the free resolver, one call per year."""
    out: dict[int, str] = {}
    by_year: dict[str, set[int]] = {}
    for d0, _d1, iid in ids_by_window:
        by_year.setdefault(d0[:4], set()).add(iid)
    for yr, ids in sorted(by_year.items()):
        r = c.symbology.resolve(DATASET, symbols=[str(i) for i in sorted(ids)], stype_in="instrument_id",
                                stype_out="raw_symbol", start_date=f"{yr}-01-01", end_date=f"{yr}-12-31")
        for k, ivs in r.get("result", {}).items():
            if ivs:
                out[int(k)] = ivs[0]["s"]
        time.sleep(0.5)
    return out


def do_build() -> int:
    if not JOBS.exists():
        raise SystemExit("--build: nothing downloaded.")
    jobs = json.loads(JOBS.read_text(encoding="utf-8"))
    c = client()
    meta_syms: dict[str, dict] = {}
    rolls_out: dict[str, dict] = {}
    for rec in jobs["jobs"]:
        jid = rec["job"]["id"]
        job_dir = RAW / jid
        if not job_dir.exists():
            raise SystemExit(f"--build: job {jid} not downloaded.")
        frames, mappings = decode_job_dir(job_dir)
        for root, df in frames.items():
            ivs = mappings.get(root, [])
            names = raw_symbols_for(c, [(iv["start_date"], iv["end_date"], iv["instrument_id"]) for iv in ivs])
            # Roll dates from the BARS (instrument change), cross-checked against the vendor mapping.
            iid = df["instrument_id"].to_numpy()
            change = np.flatnonzero(iid[1:] != iid[:-1]) + 1
            seen: set[int] = {int(iid[0])} if len(iid) else set()
            rolls = []
            for i in change:
                fr, to = int(iid[i - 1]), int(iid[i])
                rolls.append({"ts_utc": df.index[i].isoformat(), "from_instrument_id": fr, "to_instrument_id": to,
                              "from_raw": names.get(fr), "to_raw": names.get(to),
                              "from_close": float(df["close"].iloc[i - 1]), "to_open": float(df["open"].iloc[i]),
                              "gap_log": float(np.log(df["open"].iloc[i] / df["close"].iloc[i - 1])),
                              "flip_back": to in seen})
                seen.add(to)
            rolls_out[root] = {"continuous": continuous(root), "roll_rule": "previous-day volume rank (Databento 'v')",
                               "adjustment": "unadjusted", "n_rolls": len(rolls),
                               "n_flip_backs": int(sum(r["flip_back"] for r in rolls)),
                               "vendor_intervals": [dict(iv, raw_symbol=names.get(iv["instrument_id"])) for iv in ivs],
                               "rolls": rolls}
            FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
            df.to_parquet(fixture_path(root))
            meta_syms[root] = {"tier": rec["tier"], "job_id": jid, "requested_start": rec["start"],
                               "requested_end": rec["end"], "first_bar_utc": df.index[0].isoformat(),
                               "last_bar_utc": df.index[-1].isoformat(), "n_bars": int(len(df)),
                               "n_instruments": int(len(set(iid.tolist()))),
                               "fixture": str(fixture_path(root).relative_to(REPO)),
                               "fixture_sha256": sha256(fixture_path(root))}
            print(f"  {root:4} {len(df):>10,} bars  {df.index[0].date()}..{df.index[-1].date()}  "
                  f"{len(rolls)} rolls ({rolls_out[root]['n_flip_backs']} flip-backs)")
    meta = {
        "built_utc": now_iso(), "dataset": DATASET, "schema": SCHEMA, "stype_in": STYPE_IN,
        "stype_out": STYPE_OUT, "roll_rule": ROLL_RULE,
        "roll_rule_meaning": "Databento continuous symbology, rank 0 by the PREVIOUS DAY's volume",
        "adjustment": "unadjusted -- Databento: 'The continuous contract prices returned are the original, unadjusted prices.'",
        "session_filter": "none; full Globex session as captured (GLBX.MDP3 has no RTH variant)",
        "bars": "ohlcv-1m; a minute with no trade has NO bar (asserted by gate 5)",
        "timestamps": "ts_event, UTC, marks the OPEN of the minute",
        "columns": ["ts_event", "instrument_id", "open", "high", "low", "close", "volume"],
        "licence": "CME data: the parquet fixtures are gitignored and never committed; this meta, the rolls, the specs and the validation report are.",
        "symbols": meta_syms, "config_fingerprint": config_fingerprint(),
        "builder": "scripts/fetch_futures_1m.py --build",
    }
    META.write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    ROLLS.write_text(json.dumps(rolls_out, indent=1) + "\n", encoding="utf-8")
    print(f"\n  wrote {META.name}, {ROLLS.name}. Next: --validate.")
    return 0


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# -------------------------------------------------------------- --validate
#
# Each gate is a function (df, ctx) -> dict of evidence, and RAISES GateError on
# failure. --self-test proves each one raises by breaking exactly the quantity it reads.

def et_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Add naive-ET time columns: mod (minute of day), sdate (session date), wday."""
    et = df.index.tz_convert(ET).tz_localize(None)
    mod = (et.hour * 60 + et.minute).to_numpy()
    day = et.normalize()
    sdate = day + pd.to_timedelta((mod >= 1080).astype(int), unit="D")   # >= 18:00 belongs to the next date
    out = pd.DataFrame({"mod": mod, "sdate": sdate.to_numpy(), "wday": sdate.weekday.to_numpy()}, index=df.index)
    return out


def gate1_roll_recorded(df: pd.DataFrame, ctx: dict) -> dict:
    """The roll is a construction: rule and basis stated, every instrument change in the artifact."""
    meta, rolls = ctx["meta"], ctx["rolls"]
    for k in ("roll_rule", "adjustment", "roll_rule_meaning"):
        if not meta.get(k):
            raise GateError(f"gate 1: meta lacks {k}")
    if meta["adjustment"].split()[0] != "unadjusted":
        raise GateError(f"gate 1: adjustment basis must be stated as unadjusted for Databento continuous; got {meta['adjustment']!r}")
    iid = df["instrument_id"].to_numpy()
    change = np.flatnonzero(iid[1:] != iid[:-1]) + 1
    in_bars = {(int(iid[i - 1]), int(iid[i]), df.index[i].isoformat()) for i in change}
    in_art = {(r["from_instrument_id"], r["to_instrument_id"], r["ts_utc"]) for r in rolls["rolls"]}
    if in_bars != in_art:
        raise GateError(f"gate 1: {len(in_bars ^ in_art)} instrument changes differ between bars and the roll artifact")
    return {"n_rolls": len(in_bars), "n_flip_backs": rolls["n_flip_backs"], "adjustment": meta["adjustment"]}


def gate2_roll_trap(df: pd.DataFrame, ctx: dict) -> dict:
    """No UNFLAGGED bar-to-bar move beyond the D226 limit; every roll gap reported against
    the non-roll distribution. The consumer excludes flagged bars; nothing else may jump."""
    close = df["close"].to_numpy()
    opn = df["open"].to_numpy()
    iid = df["instrument_id"].to_numpy()
    mv = np.log(opn[1:] / close[:-1])          # open-to-previous-close: where a roll gap lives
    is_roll = iid[1:] != iid[:-1]
    non = np.abs(mv[~is_roll])
    worst_non = float(non.max()) if non.size else 0.0
    if worst_non > MOVE_LIMIT:
        i = int(np.argmax(np.where(is_roll, -1.0, np.abs(mv)))) + 1
        raise GateError(f"gate 2: unflagged move {worst_non:.4f} > {MOVE_LIMIT} at {df.index[i]} "
                        f"(instrument {iid[i]}) -- a synthetic jump that is not a recorded roll")
    gaps = np.abs(mv[is_roll])
    q = lambda a, p: float(np.quantile(a, p)) if a.size else 0.0
    ev = {"non_roll_abs_move": {"p50": q(non, .5), "p99": q(non, .99), "p999": q(non, .999), "max": worst_non},
          "roll_gap_abs": {"n": int(gaps.size), "p50": q(gaps, .5), "max": float(gaps.max()) if gaps.size else 0.0},
          "roll_gaps_beyond_non_roll_max": int((gaps > worst_non).sum()),
          "roll_gaps_beyond_non_roll_p999": int((gaps > q(non, .999)).sum())}
    return ev


def gate3_multipliers(df: pd.DataFrame, ctx: dict) -> dict:
    """Multiplier and tick from the exchange's own spec, and every price on the tick grid."""
    sp = ctx["specs"].get(ctx["symbol"])
    if sp is None:
        raise GateError(f"gate 3: no CME spec for {ctx['symbol']} in {SPECS.name}")
    tick = sp["tick_points"]
    off = 0
    for col in ("open", "high", "low", "close"):
        x = df[col].to_numpy() / tick
        off += int((np.abs(x - np.round(x)) > 1e-6).sum())
    if off:
        raise GateError(f"gate 3: {off} prices off the {tick} tick grid for {ctx['symbol']} -- wrong instrument or wrong unit")
    return {"usd_per_point": sp["usd_per_point"], "tick_points": tick, "tick_usd": sp["tick_usd"],
            "product_id": sp["product_id"], "prices_off_grid": 0}


def gate4_session(df: pd.DataFrame, ctx: dict) -> dict:
    """Assert the session template FOUND, count sessions, record holidays and half-days."""
    e = ctx["et"]
    if (e["wday"] >= 5).any():
        n = int((e["wday"] >= 5).sum())
        raise GateError(f"gate 4: {n} bars fall in weekend sessions (Saturday/Sunday session dates)")
    g = e.groupby("sdate")["mod"]
    # order minutes so that 18:00 (opening) sorts first: shift by -1080 mod 1440
    rel = ((e["mod"] - 1080) % 1440)
    rg = rel.groupby(e["sdate"])
    first_rel, last_rel = rg.min(), rg.max()
    modal_open = int(first_rel.mode().iloc[0])
    modal_close = int(last_rel.mode().iloc[0])
    share_open = float((first_rel == modal_open).mean())
    share_close = float((last_rel == modal_close).mean())
    if share_open < 0.90:
        raise GateError(f"gate 4: only {share_open:.1%} of sessions open at the modal minute")
    # daily closed block: minute-of-day slots that essentially never print
    n_sessions = int(first_rel.index.nunique())
    slot_share = np.bincount(e["mod"].to_numpy(), minlength=1440) / n_sessions
    closed = np.flatnonzero(slot_share < 0.01)
    # contiguity mod 1440
    if closed.size:
        d = np.diff(np.concatenate([closed, [closed[0] + 1440]]))
        blocks = int((d > 1).sum())
    else:
        blocks = 0
    early = last_rel[last_rel < modal_close - 60]
    dates = pd.DatetimeIndex(first_rel.index)
    all_wd = pd.bdate_range(dates.min(), dates.max())
    missing = all_wd.difference(dates)
    ev = {"n_sessions": n_sessions,
          "modal_open_et": f"{(modal_open + 1080) % 1440 // 60:02d}:{(modal_open + 1080) % 1440 % 60:02d}",
          "modal_close_et": f"{(modal_close + 1080) % 1440 // 60:02d}:{(modal_close + 1080) % 1440 % 60:02d}",
          "share_open_at_modal": share_open, "share_close_at_modal": share_close,
          "closed_minutes_per_day": int(closed.size), "closed_blocks": blocks,
          "closed_block_et": [f"{int(closed.min())//60:02d}:{int(closed.min())%60:02d}",
                              f"{int(closed.max())//60:02d}:{int(closed.max())%60:02d}"] if closed.size else None,
          "early_close_sessions": int(len(early)),
          "early_close_examples": [f"{d.date()} {(int(m)+1080)%1440//60:02d}:{(int(m)+1080)%1440%60:02d}"
                                   for d, m in list(early.items())[:8]],
          "weekday_dates_with_no_session": int(len(missing)),
          "no_session_examples": [str(x.date()) for x in missing[:8]]}
    ctx["expected_minutes"] = (modal_close - modal_open + 1)
    return ev


def gate5_no_fill(df: pd.DataFrame, ctx: dict) -> dict:
    """Bars are absent, not fabricated: no zero-volume bar; empty-minute rate reported."""
    v = df["volume"].to_numpy()
    if (v <= 0).any():
        i = int(np.argmax(v <= 0))
        raise GateError(f"gate 5: {int((v <= 0).sum())} zero-volume bars (first {df.index[i]}) -- a forward-filled or fabricated minute")
    e = ctx["et"]
    exp = ctx.get("expected_minutes", 1380)
    per = e.groupby("sdate").size()
    regular = per[per <= exp]
    empty = 1.0 - regular / exp
    rth = e[(e["mod"] >= 570) & (e["mod"] < 960)].groupby("sdate").size()
    rth_rate = 1.0 - rth / 390
    yrs = pd.DatetimeIndex(empty.index).year
    by_year = {int(y): float(empty[yrs == y].mean()) for y in sorted(set(yrs))}
    overnight = 1.0 - (regular - rth.reindex(regular.index).fillna(0)) / (exp - 390) if exp > 390 else None
    return {"expected_minutes_per_session": int(exp), "empty_minute_rate_mean": float(empty.mean()),
            "empty_minute_rate_median": float(empty.median()), "rth_empty_minute_rate_mean": float(rth_rate.mean()),
            "overnight_empty_minute_rate_mean": float(overnight.mean()) if overnight is not None else None,
            "flat_bar_share": float(((df["open"] == df["close"]) & (df["high"] == df["low"])).mean()),
            "by_year": by_year}


def gate6_in_range(df: pd.DataFrame, ctx: dict) -> dict:
    """Offline half of the negative control: every bar inside the window that was requested."""
    m = ctx["meta"]["symbols"][ctx["symbol"]]
    lo = pd.Timestamp(m["requested_start"], tz="UTC")
    hi = pd.Timestamp(m["requested_end"], tz="UTC") + pd.Timedelta(days=1)
    n_out = int(((df.index < lo) | (df.index >= hi)).sum())
    if n_out:
        raise GateError(f"gate 6: {n_out} bars outside the requested window {m['requested_start']}..{m['requested_end']}")
    if len(df) == 0:
        raise GateError("gate 6: empty fixture")
    return {"requested": [m["requested_start"], m["requested_end"]], "first_bar": df.index[0].isoformat(),
            "last_bar": df.index[-1].isoformat(), "bars_outside_window": 0}


def es_rth_daily_close(df: pd.DataFrame, e: pd.DataFrame) -> pd.Series:
    rth = e[(e["mod"] >= 570) & (e["mod"] <= 959)]
    last = rth.groupby("sdate").apply(lambda g: g.index[-1])
    return pd.Series(df.loc[last.to_numpy(), "close"].to_numpy(), index=pd.DatetimeIndex(last.index))


def gate7_es_vs_spy(df: pd.DataFrame, ctx: dict) -> dict:
    """Is it the instrument we think it is? ES RTH close vs SPY close, daily log returns."""
    spy = ctx["spy"]
    es = es_rth_daily_close(df, ctx["et"])
    j = pd.concat([np.log(es).diff().rename("es"), np.log(spy).diff().rename("spy")], axis=1).dropna()
    if len(j) < 250:
        raise GateError(f"gate 7: only {len(j)} overlapping days")
    corr = float(j["es"].corr(j["spy"]))
    if not corr > CORR_FLOOR:
        raise GateError(f"gate 7: ES~SPY daily-return correlation {corr:.4f} <= {CORR_FLOOR}")
    d = (j["es"] - j["spy"]).abs().sort_values(ascending=False)
    return {"n_days": int(len(j)), "corr": corr, "window": [str(j.index[0].date()), str(j.index[-1].date())],
            "largest_divergences": [f"{k.date()} {v:.4f}" for k, v in d.head(5).items()]}


GATES = [("1 roll recorded", gate1_roll_recorded), ("2 roll trap", gate2_roll_trap),
         ("3 multipliers", gate3_multipliers), ("4 session", gate4_session),
         ("5 no fill", gate5_no_fill), ("6 in range", gate6_in_range)]


def load_spy() -> pd.Series:
    d = pd.read_csv(SPY_DAILY, usecols=["timestamp", "symbol", "close"])
    d = d[d["symbol"] == "SPY"]
    return pd.Series(d["close"].to_numpy(), index=pd.to_datetime(d["timestamp"]))


def validate_symbol(sym: str, df: pd.DataFrame, meta: dict, rolls: dict, sp: dict, spy: pd.Series | None) -> dict:
    ctx = {"symbol": sym, "meta": meta, "rolls": rolls, "specs": sp, "et": et_frame(df), "spy": spy}
    out = {}
    for name, fn in GATES:
        out[name] = fn(df, ctx)
        print(f"    [PASS] {sym:4} gate {name:16} {json.dumps(out[name], default=str)[:110]}")
    if sym == "ES" and spy is not None:
        out["7 es vs spy"] = gate7_es_vs_spy(df, ctx)
        print(f"    [PASS] {sym:4} gate 7 es vs spy    corr={out['7 es vs spy']['corr']:.4f} n={out['7 es vs spy']['n_days']}")
    return out


def do_validate() -> int:
    meta = json.loads(META.read_text(encoding="utf-8"))
    rolls = json.loads(ROLLS.read_text(encoding="utf-8"))
    sp = specs()
    spy = load_spy() if SPY_DAILY.exists() else None
    report = {"validated_utc": now_iso(), "fixture_meta": META.name, "gates": {}}
    for sym, m in meta["symbols"].items():
        p = REPO / m["fixture"]
        if sha256(p) != m["fixture_sha256"]:
            raise GateError(f"{sym}: fixture on disk differs from the meta's sha256; rebuild")
        df = pd.read_parquet(p)
        report["gates"][sym] = validate_symbol(sym, df, meta, rolls[sym], sp, spy)
    report["all_passed"] = True
    REPORT.write_text(json.dumps(report, indent=1, default=str) + "\n", encoding="utf-8")
    print(f"\n  ALL GATES PASSED -> {REPORT.name}")
    return 0


# -------------------------------------------------------------- --self-test

def synthetic_book(seed: int = 0, n_days: int = 300) -> tuple[pd.DataFrame, dict, dict, pd.Series]:
    """An ES-shaped book on the found template: 18:00->16:59 ET, weekdays, 0.25 grid,
    two rolls, absent minutes, and a SPY that tracks it."""
    rng = np.random.default_rng(seed)
    days = pd.bdate_range("2024-01-08", periods=n_days)
    ts, px, iid, vol = [], [], [], []
    price = 4800.0
    inst = 100
    roll_days = {days[40], days[95]}
    spy_close = {}
    for d in days:
        if d in roll_days:
            inst += 1
            price += 12.0                      # a real basis jump between contracts
        start = (d - pd.Timedelta(days=1)).replace(hour=18)      # previous calendar day 18:00 ET
        for k in range(1380):
            t = start + pd.Timedelta(minutes=k)
            if 1020 <= (t.hour * 60 + t.minute) < 1080:          # never trades 17:00-17:59 (impossible here)
                continue
            if rng.random() < 0.03:                              # absent minutes
                continue
            price += rng.normal(0, 0.8)
            o = round(price / 0.25) * 0.25
            c_ = round((price + rng.normal(0, 0.5)) / 0.25) * 0.25
            ts.append(t); px.append((o, max(o, c_), min(o, c_), c_)); iid.append(inst); vol.append(int(rng.integers(1, 500)))
            price = c_
        spy_close[d] = price / 10.0 * (1 + rng.normal(0, 0.0002))
    idx = pd.DatetimeIndex(ts).tz_localize(ET).tz_convert("UTC")
    arr = np.array(px)
    df = pd.DataFrame({"instrument_id": iid, "open": arr[:, 0], "high": arr[:, 1], "low": arr[:, 2],
                       "close": arr[:, 3], "volume": vol}, index=idx)
    df.index.name = "ts_event"
    ii = df["instrument_id"].to_numpy()
    ch = np.flatnonzero(ii[1:] != ii[:-1]) + 1
    rolls = {"n_flip_backs": 0, "rolls": [{"from_instrument_id": int(ii[i - 1]), "to_instrument_id": int(ii[i]),
                                           "ts_utc": df.index[i].isoformat()} for i in ch]}
    meta = {"roll_rule": "v", "adjustment": "unadjusted (synthetic)", "roll_rule_meaning": "test",
            "symbols": {"ES": {"requested_start": "2024-01-01", "requested_end": "2025-12-31"}}}
    spy = pd.Series(spy_close)
    return df, meta, rolls, spy


def do_self_test() -> int:
    sp = specs()
    df, meta, rolls, spy = synthetic_book()
    print("  clean synthetic book:")
    validate_symbol("ES", df, meta, rolls, sp, spy)

    def expect_raise(label, fn):
        """The break must trip THE GATE IT TARGETS, not a neighbour: the label's
        'gate N' prefix has to be the prefix of the raised message."""
        want = label.split(":")[0]
        try:
            fn()
        except GateError as exc:
            if not str(exc).startswith(want):
                raise SystemExit(f"SELF-TEST FAILED: {label} tripped the wrong gate: {str(exc)[:100]}")
            print(f"    [FIRES] {label:44} -> {str(exc)[:90]}")
            return
        raise SystemExit(f"SELF-TEST FAILED: {label} did not raise")

    def run(d, m=meta, r=rolls, s=spy):
        validate_symbol("ES", d, m, r, sp, s)

    # gate 1: drop one roll from the artifact
    r1 = {"n_flip_backs": 0, "rolls": rolls["rolls"][:1]}
    expect_raise("gate 1: roll missing from artifact", lambda: run(df, r=r1))
    # gate 2: a 20% jump INSIDE a contract (unflagged)
    d2 = df.copy(); j = len(d2) // 3
    d2.iloc[j:, d2.columns.get_indexer(["open", "high", "low", "close"])] *= 1.20
    d2[["open", "high", "low", "close"]] = (d2[["open", "high", "low", "close"]] / 0.25).round() * 0.25
    expect_raise("gate 2: unflagged 20% jump", lambda: run(d2))
    # gate 3: prices off the tick grid
    d3 = df.copy(); d3["close"] = d3["close"] + 0.1
    expect_raise("gate 3: price off the 0.25 grid", lambda: run(d3))
    # gate 4: a bar on a Saturday session, AFTER the last bar so no instrument change is created
    d4 = df.copy()
    last_et = df.index[-1].tz_convert(ET)
    sat_day = last_et + pd.Timedelta(days=(5 - last_et.weekday()) % 7 or 7)
    sat = pd.DatetimeIndex([sat_day.replace(hour=10, minute=0).tz_convert("UTC")])
    extra = pd.DataFrame({"instrument_id": [int(df["instrument_id"].iloc[-1])], "open": [5000.0], "high": [5000.0],
                          "low": [5000.0], "close": [5000.0], "volume": [5]}, index=sat)
    d4 = pd.concat([d4, extra]).sort_index()
    expect_raise("gate 4: a Saturday bar", lambda: run(d4))
    # gate 5: a zero-volume bar
    d5 = df.copy(); d5.iloc[100, d5.columns.get_loc("volume")] = 0
    expect_raise("gate 5: a zero-volume bar", lambda: run(d5))
    # gate 6: a bar outside the requested window
    m6 = json.loads(json.dumps(meta)); m6["symbols"]["ES"]["requested_start"] = "2024-02-01"
    expect_raise("gate 6: bars before the requested start", lambda: run(df, m=m6))
    # gate 7: SPY values rotated by one day on the SAME dates -> overlap intact, correlation collapses
    s7 = pd.Series(np.roll(spy.to_numpy(), 1), index=spy.index)
    expect_raise("gate 7: SPY misaligned by one day", lambda: run(df, s=s7))
    # meta guard: an adjusted basis claimed on Databento continuous
    m1 = json.loads(json.dumps(meta)); m1["adjustment"] = "ratio"
    expect_raise("gate 1: basis stated as adjusted", lambda: run(df, m=m1))
    print("\n  SELF-TEST PASSED: every gate fires on the quantity it reads.")
    return 0


# ------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    for flag in ("plan", "self-test", "verify", "cost", "submit", "download", "build", "validate"):
        ap.add_argument(f"--{flag}", action="store_true")
    ap.add_argument("--tiers", default=None, help="e.g. 1,3 (default) or 1,2,3")
    ap.add_argument("--i-accept-the-cost", type=float, default=None, dest="accepted", metavar="USD")
    a = ap.parse_args()
    tiers = tiers_arg(a.tiers)
    if a.self_test:
        return do_self_test()
    if a.verify:
        return do_verify()
    if a.cost:
        return do_cost(tiers)
    if a.submit:
        return do_submit(tiers, a.accepted)
    if a.download:
        return do_download()
    if a.build:
        return do_build()
    if a.validate:
        return do_validate()
    return do_plan(tiers)


if __name__ == "__main__":
    raise SystemExit(main())
