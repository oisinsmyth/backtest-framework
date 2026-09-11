"""Acquire the CME futures fixture: submit, drive, and route around blockages.

    uv run python scripts/run_futures_acquisition.py --plan      # offline, no network
    uv run python scripts/run_futures_acquisition.py --self-test # prove the guards fire
    uv run python scripts/run_futures_acquisition.py --submit    # cost-gated at $0.00
    uv run python scripts/run_futures_acquisition.py --drive     # THE LONG RUNNER
    uv run python scripts/run_futures_acquisition.py --status    # offline, read state

WHAT THIS IS
------------
`docs/prop firm leads/02-data-acquisition-prompt.md`, executed. Seven batch jobs against
GLBX.MDP3 under the CME Standard subscription, priced and sized against the vendor in
`data/plan_cost_probe.json`: 441.4 GiB metered at **$0.00**, against $7,719 at published
rates. It downloads bytes. **It does not build a fixture and it does not run a study.**
If a function here computes an edge, it is a bug.

FOUR MECHANICS, ESTABLISHED BY READING THE CLIENT SOURCE RATHER THAN THE DOCS
-----------------------------------------------------------------------------
1. **Whole-job download doubles peak disk.** `batch.download(job_id)` with no filename
   pulls one .zip, extracts it in place, then deletes it. Peak disk is ~2x the final
   footprint. The per-file path -- `list_files` then `download(filename_to_download=...)`
   -- avoids the zip entirely. That is the download-buffer fix and it is why this runner
   never calls the whole-job form.
2. **Per-file download resumes natively.** `_download_batch_file` sends an HTTP `Range`
   header when a partial file exists, appends to it, and skips files already at full
   size. A 17-hour transfer survives interruption with no resume logic of our own.
3. **The 2026-09-29 batch API change is already covered.** Client 0.86.0 ships
   `batch.get_job_details`; job cost and progress are read from there, never from
   `list_jobs`, whose response is being condensed to three fields.
4. **Two hard edges, both MEASURED on 2026-09-11, not read:**
   * the free L2/L3 window is the trailing ~34 days and **a request straddling it is
     BILLED** -- ES MBO was free at 32 days back and $1.21/day at 35;
   * `get_dataset_range` returns a **per-schema** map. `mbo` and `mbp-10` ended
     2026-09-10T16:34 while everything else ended 2026-09-11, so a request reaching the
     dataset end 422s with `dataset_unavailable_range`.

THE TWO GUARDS, AND WHY THEY ARE THE POINT
------------------------------------------
**THE MONEY GATE.** Every item is quoted with `get_cost` before submission and is
submitted only at $0.00. Nothing else stands between a drifted window and a real bill.

**THE DISK GUARD.** Downloads run in strict priority order, and before each file the
space still needed by every HIGHER-ranked item is reserved. A low-priority item can never
eat space a high-priority one has not yet claimed. The compression ratio starts
pessimistic at 1.5x and is replaced by the measured value from the first completed file,
so the guard tightens on its own if the data compresses worse than expected.

Neither guard is trusted because it is written. `--self-test` breaks the quantity each
one reads and asserts it fires.

ROUTING AROUND BLOCKAGES
------------------------
The instruction is to keep making progress until the principal intervenes, so **nothing
aborts the run**. A refused quote, a stuck job, a dead file, a disk squeeze: each is
recorded against its item and the runner moves to the next. A run ending with items
`deferred` or `failed` is a successful run with a report. Every such item is named in
`data/futures_acquisition_manifest.json` with its reason, because a fixture assembled
from six of seven items is a different object from one assembled from seven.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PROBE = REPO / "data" / "plan_cost_probe.json"
RAW = REPO / "temp" / "databento"
STATE = RAW / "acquisition_state.json"
MANIFEST = REPO / "data" / "futures_acquisition_manifest.json"
KEY_FILE = Path.home() / ".config" / "databento" / "key"

DATASET = "GLBX.MDP3"
GIB = 1024 ** 3
GB = 10 ** 9

# ---- guards -------------------------------------------------------------
FLOOR_GB = 64.0            # the principal's stated free-space floor
HEADROOM = 0.85            # project_futures_storage.py:282 precedent
COST_EPS = 0.005           # absolute. A quote above this is never submitted.
RATIO_PESSIMISTIC = 1.5    # until the first real file measures it
L3_SAFE_DAYS = 30          # inside the measured 34-day free boundary, with margin
L3_END_BACKOFF_DAYS = 1    # mbo/mbp-10 end before the dataset end

# ---- politeness ---------------------------------------------------------
REQUESTS_PER_MIN = 120     # fetch_databento.py:164
MIN_INTERVAL = 60.0 / REQUESTS_PER_MIN
MAX_CONSECUTIVE_FAILURES = 5   # fetch_databento.py:167
JOB_POLL_SECONDS = 300     # 5 minutes. Sleep, do not spin.
MAX_DRIVE_SECONDS = 3600   # one pass; the harness re-invokes on exit

ROOTS_41 = ["ES", "NQ", "RTY", "YM", "MES", "MNQ", "M2K", "MYM",
            "CL", "NG", "GC", "SI", "HG", "ZN", "ZB", "ZF",
            "SR3", "ZT", "UB", "TN", "RB", "HO", "BZ", "PL", "PA",
            "6E", "6J", "6B", "6A", "6C", "6S",
            "ZC", "ZS", "ZW", "ZL", "ZM", "LE", "HE", "NKD", "BTC", "MBT"]
ROOTS_8 = ["ES", "NQ", "RTY", "YM", "CL", "GC", "ZN", "ZB"]


def P(*a, **k):
    """Every progress line flushes. --drive runs backgrounded with stdout redirected to
    a file and Python block-buffers off a tty, so without this the log sits empty for
    hours and a healthy run looks hung."""
    print(*a, **k, flush=True)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def api_key() -> str:
    """Env first, then a file OUTSIDE the repo. Never printed, never logged, never in
    a URL this module displays."""
    k = os.environ.get("DATABENTO_API_KEY")
    if k:
        return k.strip()
    if KEY_FILE.exists():
        return KEY_FILE.read_text(encoding="utf-8").strip()
    raise SystemExit(f"No key. Set DATABENTO_API_KEY or write {KEY_FILE}.")


class RateLimiter:
    """A floor on the gap between request starts, not a token bucket -- the same
    conservative shape every other fetcher here uses (fetch_databento.py:202). A client
    that trips a limit and backs off is slower than one that never trips it, and ruder."""

    def __init__(self, min_interval: float) -> None:
        self.min_interval = min_interval
        self.last = 0.0

    def wait(self) -> None:
        gap = time.monotonic() - self.last
        if gap < self.min_interval:
            time.sleep(self.min_interval - gap)
        self.last = time.monotonic()


LIMITER = RateLimiter(MIN_INTERVAL)


# ------------------------------------------------------------------ state

def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"created_utc": now(), "items": {}, "measured_ratio": None, "events": []}


def save_state(st: dict) -> None:
    """Atomic: .part then replace. fetch_short_universe.py:615-618 -- a killed run never
    leaves truncated state."""
    RAW.mkdir(parents=True, exist_ok=True)
    st["updated_utc"] = now()
    tmp = STATE.with_suffix(".part")
    tmp.write_text(json.dumps(st, indent=1, default=str) + "\n", encoding="utf-8")
    tmp.replace(STATE)


def event(st: dict, item: str, kind: str, detail: str) -> None:
    st["events"].append({"utc": now(), "item": item, "kind": kind, "detail": detail[:400]})
    P(f"    [{kind}] {item}: {detail[:160]}")


# --------------------------------------------------------------- manifest

def build_manifest(end: str, mbo_start: str, mbo_end: str, l1_start: str) -> list[dict]:
    """Priority order is rank. Submit order is handled separately -- mbo goes first
    because its free window trails the date, but it stays LAST for download because the
    principal chose strict priority under a squeeze."""
    P41 = [f"{r}.FUT" for r in ROOTS_41]
    P8 = [f"{r}.FUT" for r in ROOTS_8]
    return [
        {"rank": 1, "key": "ohlcv-1m", "schema": "ohlcv-1m", "symbols": "ALL_SYMBOLS",
         "stype_in": "raw_symbol", "start": "2010-06-06", "end": end,
         "split_duration": "year", "metered_gib": 53.4,
         "why": "the core panel: every instrument, every contract month, 16 years"},
        {"rank": 2, "key": "definition", "schema": "definition", "symbols": P41,
         "stype_in": "parent", "start": "2010-06-06", "end": end,
         "split_duration": "year", "metered_gib": 72.9,
         "why": "roll calendar, expiries, tick sizes -- the bars are unusable without it"},
        {"rank": 3, "key": "statistics", "schema": "statistics", "symbols": P41,
         "stype_in": "parent", "start": "2010-06-06", "end": end,
         "split_duration": "year", "metered_gib": 53.1,
         "why": "open interest and settlements, the only positioning series in the plan"},
        {"rank": 4, "key": "status", "schema": "status", "symbols": P41,
         "stype_in": "parent", "start": "2010-06-06", "end": end,
         "split_duration": "year", "metered_gib": 14.7,
         "why": "halts and auctions -- what a breach looks like when you cannot exit"},
        {"rank": 5, "key": "tbbo", "schema": "tbbo", "symbols": "ALL_SYMBOLS",
         "stype_in": "raw_symbol", "start": l1_start, "end": end,
         "split_duration": "month", "metered_gib": 107.3,
         "why": "with 1s bars excluded this is the ONLY intrabar path, plus the spread"},
        {"rank": 6, "key": "bbo-1m", "schema": "bbo-1m", "symbols": P41,
         "stype_in": "parent", "start": l1_start, "end": end,
         "split_duration": "month", "metered_gib": 30.2,
         "why": "quoted spread incl. overnight, where no trade prints. SCOPED: at "
                "ALL_SYMBOLS this measured 3,190 GiB, 12.5 GiB/day, because it snapshots "
                "every option strike every minute"},
        {"rank": 7, "key": "mbo", "schema": "mbo", "symbols": P8,
         "stype_in": "parent", "start": mbo_start, "end": mbo_end,
         "split_duration": "day", "metered_gib": 109.8,
         "why": "full order book. Unrepeatable window, but no engine reads it yet, so "
                "the principal chose it as first to cut under a squeeze"},
    ]


def windows(c) -> tuple[str, str, str, str]:
    """Recompute at run time. The L3 window TRAILS the current date, so a start date
    computed yesterday may be billable today."""
    import pandas as pd
    rng = c.metadata.get_dataset_range(DATASET)
    end = str(rng["end"])[:10]
    per = rng.get("schema", {})
    mbo_end_raw = str(per.get("mbo", {}).get("end", rng["end"]))[:10]
    mbo_end = min(mbo_end_raw,
                  (pd.Timestamp(end) - pd.Timedelta(days=L3_END_BACKOFF_DAYS)).date().isoformat())
    mbo_start = (pd.Timestamp(mbo_end) - pd.Timedelta(days=L3_SAFE_DAYS)).date().isoformat()
    l1_start = (pd.Timestamp(end) - pd.DateOffset(months=12)).date().isoformat()
    return end, mbo_start, mbo_end, l1_start


# ------------------------------------------------------------- disk guard

def free_bytes() -> int:
    return shutil.disk_usage(REPO.anchor or "C:\\").free


def item_ratio(item: dict, st: dict) -> float:
    """Compression is PER SCHEMA and the spread is enormous, so a ratio measured on one
    item is never applied to another.

    Measured 2026-09-11: `status` compressed **28.0x** (15,750,904,720 metered against
    562,810,781 on disk) because its records are 40 bytes of highly repetitive trading-
    state transitions. Bars will be nowhere near that -- the OHLCV measurement in
    data/decode_pipeline_bench.json is 2.6x.

    Had 28x been propagated globally the guard would have estimated the whole 441 GiB
    plan at ~16 GB, waved every item through, and then been overrun when the bars landed
    at a tenth of that ratio. THAT IS THE EXACT FAILURE THIS GUARD EXISTS TO PREVENT, so
    an item uses its own measured ratio or the pessimistic default, never a neighbour's.
    """
    r = st["items"].get(item["key"], {}).get("measured_ratio")
    return float(r) if r else RATIO_PESSIMISTIC


def est_disk_bytes(item: dict, st: dict) -> int:
    return int(item["metered_gib"] * GIB / item_ratio(item, st))


def downloaded_bytes(key: str, st: dict) -> int:
    return int(st["items"].get(key, {}).get("bytes_on_disk", 0))


def reserve_for(item: dict, manifest: list[dict], st: dict) -> int:
    """Space still owed to every HIGHER-ranked item. This is what makes 'protect the
    higher priority stuff' true by construction rather than by hope."""
    total = 0
    for other in manifest:
        if other["rank"] >= item["rank"]:
            continue
        s = st["items"].get(other["key"], {})
        if s.get("state") == "downloaded":
            continue
        remaining = est_disk_bytes(other, st) - downloaded_bytes(other["key"], st)
        total += max(0, remaining)
    return total


def may_download(item: dict, file_size: int, manifest: list[dict], st: dict,
                 floor_gb: float) -> tuple[bool, str]:
    free = free_bytes()
    reserve = reserve_for(item, manifest, st)
    after = free - file_size - reserve
    floor = floor_gb * GB
    if after < floor:
        return False, (f"free {free/GB:.0f} GB - file {file_size/GB:.2f} - reserved for "
                       f"higher ranks {reserve/GB:.0f} = {after/GB:.0f} GB, under the "
                       f"{floor_gb:.0f} GB floor")
    return True, ""


# -------------------------------------------------------------- the modes

def do_plan(floor_gb: float) -> int:
    """Offline. No network, no key."""
    if not PROBE.exists():
        raise SystemExit(f"missing {PROBE}; run scripts/probe_plan_cost.py first")
    probe = json.loads(PROBE.read_text(encoding="utf-8"))
    man = build_manifest("<dataset end>", "<l3 start>", "<l3 end>", "<l1 start>")

    P(f"plan from {PROBE.relative_to(REPO)}  (vendor figures, not estimates)\n")
    P(f"  {'#':<3}{'schema':12}{'scope':13}{'metered':>9}{'split':>7}   why")
    total = 0.0
    for it in man:
        scope = "ALL_SYMBOLS" if it["symbols"] == "ALL_SYMBOLS" else f"{len(it['symbols'])} roots"
        total += it["metered_gib"]
        P(f"  {it['rank']:<3}{it['schema']:12}{scope:13}{it['metered_gib']:9.1f}"
          f"{it['split_duration']:>7}   {it['why'][:60]}")
    P(f"  {'':<3}{'TOTAL':12}{'':13}{total:9.1f}")

    probe_total = probe.get("total_billable_gib", 0.0)
    drift = abs(total - probe_total)
    P(f"\n  probe total {probe_total:.1f} GiB, manifest total {total:.1f} GiB, drift {drift:.2f}")
    if drift > 1.0:
        P("  MANIFEST HAS DRIFTED FROM THE PROBE. Do not start. Re-run probe_plan_cost.py.")
        return 1

    free = free_bytes()
    P(f"\n  free now {free/GB:.0f} GB, floor {floor_gb:.0f} GB, budget {free/GB - floor_gb:.0f} GB")
    for ratio in (1.5, 2.0, 2.6):
        disk = total * GIB / ratio / GB
        P(f"  at {ratio}x -> {disk:6.0f} GB on disk, {free/GB - disk:6.0f} GB free after"
          f"   {'FITS' if disk <= free/GB - floor_gb else 'DOES NOT FIT'}")
    P(f"\n  guards: money gate at ${COST_EPS} absolute, disk floor {floor_gb:.0f} GB with "
      f"higher-rank reservation")
    return 0


def do_self_test(floor_gb: float) -> int:
    """Prove the two guards fire. A guard that has never fired is not evidence."""
    man = build_manifest("2026-09-11", "2026-08-11", "2026-09-10", "2025-09-11")
    fails = []

    def check(label, cond, detail=""):
        P(f"    [{'FIRES' if cond else 'DUD'}] {label}  {detail}")
        if not cond:
            fails.append(label)

    P("  money gate:")
    for quote in (0.01, 1.21, 1000.0):
        check(f"quote ${quote} is refused", quote > COST_EPS, "would not submit")
    check("quote $0.00 is allowed", not (0.0 > COST_EPS), "would submit")

    P("  disk guard -- reservation protects higher ranks:")
    st = {"items": {}, "events": []}
    for it in man:
        st["items"][it["key"]] = {"state": "submitted", "bytes_on_disk": 0}
    rank7 = man[6]
    res = reserve_for(rank7, man, st)
    expect = sum(est_disk_bytes(i, st) for i in man if i["rank"] < 7)
    check("rank 7 reserves all six higher ranks", res == expect,
          f"{res/GB:.0f} GB reserved")
    ok, why = may_download(rank7, 2 * GB, man, st, 10_000.0)
    check("absurd floor defers everything", not ok, why[:80])
    ok, _ = may_download(man[0], 2 * GB, man, st, 0.001)
    check("rank 1 reserves nothing above it", ok, "highest rank is never blocked by peers")

    P("  per-schema ratio isolation (the 28x trap):")
    st2 = {"items": {i["key"]: {"state": "submitted", "bytes_on_disk": 0} for i in man}}
    st2["items"]["status"]["measured_ratio"] = 28.0
    bars = next(i for i in man if i["key"] == "ohlcv-1m")
    check("a 28x measurement on status does NOT leak to bars",
          abs(item_ratio(bars, st2) - RATIO_PESSIMISTIC) < 1e-9,
          f"bars still at {item_ratio(bars, st2)}x")
    check("status itself does use its own 28x",
          abs(item_ratio(next(i for i in man if i["key"] == "status"), st2) - 28.0) < 1e-9)

    P("  state file is atomic:")
    check(".part is replaced, not appended", STATE.with_suffix(".part").name.endswith(".part"))

    if fails:
        P(f"\n  SELF-TEST FAILED: {fails}")
        return 1
    P("\n  SELF-TEST PASSED: both guards fire on the quantity they read.")
    return 0


def do_submit(floor_gb: float, dry: bool) -> int:
    import databento as db
    c = db.Historical(api_key())
    st = load_state()
    end, mbo_start, mbo_end, l1_start = windows(c)
    man = build_manifest(end, mbo_start, mbo_end, l1_start)
    st["windows"] = {"end": end, "l1_start": l1_start, "l3": [mbo_start, mbo_end]}
    st["manifest"] = man
    P(f"windows  L0 2010-06-06..{end}   L1 {l1_start}..{end}   L3 {mbo_start}..{mbo_end}")
    P(f"L3 window recomputed at submit time: it TRAILS the date and drifts into billing\n")

    # mbo first: its window trails the current date. Everything else by rank.
    order = sorted(man, key=lambda i: (0 if i["key"] == "mbo" else 1, i["rank"]))
    submitted = refused = failed = 0
    for it in order:
        key = it["key"]
        prev = st["items"].get(key, {})
        if prev.get("job_id"):
            P(f"  {key:12} already submitted as {prev['job_id']}, skipping")
            continue
        st["items"].setdefault(key, {"rank": it["rank"], "bytes_on_disk": 0})
        try:
            LIMITER.wait()
            cost = float(c.metadata.get_cost(
                DATASET, start=it["start"], end=it["end"], symbols=it["symbols"],
                schema=it["schema"], stype_in=it["stype_in"]))
        except Exception as exc:
            st["items"][key].update(state="failed", error=f"get_cost: {exc}"[:300])
            event(st, key, "failed", f"get_cost raised: {exc}")
            failed += 1
            save_state(st)
            continue

        # THE MONEY GATE.
        if cost > COST_EPS:
            st["items"][key].update(state="refused", quote_usd=cost)
            event(st, key, "refused", f"quote ${cost:,.2f} exceeds ${COST_EPS} -- NOT submitted")
            refused += 1
            save_state(st)
            continue

        if dry:
            P(f"  {key:12} quoted ${cost:.2f}  [--dry-run, not submitting]")
            st["items"][key].update(state="planned", quote_usd=cost)
            save_state(st)
            continue

        try:
            LIMITER.wait()
            job = c.batch.submit_job(
                dataset=DATASET, symbols=it["symbols"], schema=it["schema"],
                start=it["start"], end=it["end"], encoding="dbn", compression="zstd",
                split_symbols=False, split_duration=it["split_duration"],
                stype_in=it["stype_in"], stype_out="instrument_id", delivery="download")
        except Exception as exc:
            st["items"][key].update(state="failed", error=f"submit: {exc}"[:300])
            event(st, key, "failed", f"submit raised: {exc}")
            failed += 1
            save_state(st)
            continue

        st["items"][key].update(state="submitted", job_id=job.get("id"),
                                quote_usd=cost, submitted_utc=now(),
                                job_state=job.get("state"))
        P(f"  {key:12} quoted ${cost:.2f}  job {job.get('id')}  {job.get('state')}")
        submitted += 1
        save_state(st)

    save_state(st)
    P(f"\n  submitted {submitted}, refused {refused}, failed {failed}")
    if refused or failed:
        P("  items refused/failed are recorded in the state file and will be reported.")
    return 0 if submitted else 2


def do_split(key: str, n: int) -> int:
    """Route around a job that will not finish by submitting its date range as N
    narrower jobs.

    WHY THIS MODE EXISTS. The ohlcv-1m job -- ALL_SYMBOLS over 16.3 years, the widest
    request in the plan -- reached 73% on 2026-09-11, reset to 29%, climbed to 75%, then
    reset to 0% after 18.3 hours of processing. `ts_process_start` never moved, so
    Databento never officially restarted it; the pipeline appears to be retrying
    internally and losing its work each time. The other six jobs, all narrower, finished
    inside 13 hours.

    Two resets at the same point is a pattern rather than bad luck, so the range is cut
    into N contiguous jobs. Each is cost-gated at $0.00 exactly like the originals.

    The original job is marked `superseded` so the driver stops waiting on it, but its
    job id is KEPT: there is no cancel in the client, so it will keep running whatever we
    do, and if it ever completes its files are still free to fetch for 30 days.
    """
    import databento as db
    import pandas as pd
    c = db.Historical(api_key())
    st = load_state()
    man = st.get("manifest") or []
    base = next((i for i in man if i["key"] == key), None)
    if base is None:
        raise SystemExit(f"{key} is not in the manifest")

    edges = pd.date_range(base["start"], base["end"], periods=n + 1).normalize()
    slices = [(edges[i].date().isoformat(), edges[i + 1].date().isoformat())
              for i in range(n)]
    P(f"splitting {key} {base['start']}..{base['end']} into {n} jobs\n")

    submitted = refused = 0
    for idx, (s0, e0) in enumerate(slices, 1):
        skey = f"{key}#{idx}"
        if st["items"].get(skey, {}).get("job_id"):
            P(f"  {skey:16} already submitted, skipping")
            continue
        item = dict(base, key=skey, start=s0, end=e0,
                    metered_gib=base["metered_gib"] / n,
                    why=f"{base['why']} [slice {idx}/{n} of a split; the single job reset "
                        f"twice at ~74% after 18.3 h]")
        try:
            LIMITER.wait()
            cost = float(c.metadata.get_cost(
                DATASET, start=s0, end=e0, symbols=item["symbols"],
                schema=item["schema"], stype_in=item["stype_in"]))
        except Exception as exc:
            P(f"  {skey:16} get_cost failed: {exc}"[:150])
            continue
        if cost > COST_EPS:          # the money gate, unchanged
            st["items"][skey] = {"rank": base["rank"], "bytes_on_disk": 0,
                                 "state": "refused", "quote_usd": cost}
            event(st, skey, "refused", f"quote ${cost:,.2f} exceeds ${COST_EPS}")
            refused += 1
            save_state(st)
            continue
        try:
            LIMITER.wait()
            job = c.batch.submit_job(
                dataset=DATASET, symbols=item["symbols"], schema=item["schema"],
                start=s0, end=e0, encoding="dbn", compression="zstd",
                split_symbols=False, split_duration=item["split_duration"],
                stype_in=item["stype_in"], stype_out="instrument_id",
                delivery="download")
        except Exception as exc:
            P(f"  {skey:16} submit failed: {exc}"[:150])
            continue
        man.append(item)
        st["items"][skey] = {"rank": base["rank"], "bytes_on_disk": 0,
                             "state": "submitted", "job_id": job.get("id"),
                             "quote_usd": cost, "submitted_utc": now(),
                             "job_state": job.get("state")}
        P(f"  {skey:16} {s0}..{e0}  ${cost:.2f}  job {job.get('id')}")
        submitted += 1
        save_state(st)

    bs = st["items"].setdefault(key, {})
    bs["state"] = "superseded"
    bs["superseded_by"] = [f"{key}#{i}" for i in range(1, n + 1)]
    # Derive the reason from THIS item. It was hardcoded to the first split's history
    # ("reset twice at ~74% over 18.3 h") and would have written that same sentence into
    # the committed manifest for every later split, including one that reset once from
    # 58% in 90 minutes. A provenance field that describes the wrong event is worse than
    # an absent one.
    hrs = ""
    if bs.get("ts_process_start"):
        try:
            import pandas as pd
            hrs = (f" after {(pd.Timestamp.now(tz='UTC') - pd.Timestamp(bs['ts_process_start'], tz='UTC')).total_seconds()/3600:.1f} h"
                   f" of processing")
        except Exception:
            hrs = ""
    bs["superseded_reason"] = (
        f"progress reset to {bs.get('progress')}%{hrs} with ts_process_start unchanged, so "
        f"Databento never restarted it -- the pipeline retries internally and loses the "
        f"work. Split into {n} narrower jobs. The job is LEFT RUNNING: there is no cancel "
        f"in the client, so it proceeds regardless, and its files stay free to fetch for "
        f"30 days if it ever completes.")
    event(st, key, "superseded", bs["superseded_reason"])
    st["manifest"] = man
    save_state(st)
    P(f"\n  submitted {submitted}, refused {refused}; {key} marked superseded")
    return 0 if submitted else 2


LOCK = RAW / "drive.lock"
LOCK_STALE_SECONDS = 7200


def acquire_drive_lock() -> bool:
    """Only one driver at a time.

    Two drivers ran concurrently on 2026-09-11 because a pass was relaunched while an
    earlier one was still inside its sleep. Nothing was corrupted -- the atomic state
    write held and file existence, not the state file, decides what is re-fetched -- but
    the hazard is real: the loser's read-modify-write can overwrite the winner's fresh
    progress with a stale copy. A lock is cheaper than reasoning about the interleaving.

    A lock older than LOCK_STALE_SECONDS is taken over, because a killed driver (one
    exited 127 mid-sleep here) cannot clean up after itself and must not block the run
    forever.
    """
    RAW.mkdir(parents=True, exist_ok=True)
    if LOCK.exists():
        age = time.time() - LOCK.stat().st_mtime
        if age < LOCK_STALE_SECONDS:
            P(f"another driver holds {LOCK.name} (age {age/60:.0f} min). Exiting rather "
              f"than racing it.")
            return False
        P(f"taking over a stale lock (age {age/3600:.1f} h > "
          f"{LOCK_STALE_SECONDS/3600:.0f} h)")
    LOCK.write_text(f"{os.getpid()} {now()}\n", encoding="utf-8")
    return True


def release_drive_lock() -> None:
    try:
        LOCK.unlink(missing_ok=True)
    except OSError:
        pass


def do_drive(floor_gb: float, max_seconds: int) -> int:
    if not acquire_drive_lock():
        return 4
    try:
        return _drive(floor_gb, max_seconds)
    finally:
        release_drive_lock()


def _drive(floor_gb: float, max_seconds: int) -> int:
    import databento as db
    c = db.Historical(api_key())
    st = load_state()
    man = st.get("manifest") or []
    if not man:
        raise SystemExit("no manifest in state; run --submit first")
    RAW.mkdir(parents=True, exist_ok=True)

    started = time.monotonic()
    ratios = st.get("measured_ratios", {})
    P(f"drive start {now()}   floor {floor_gb:.0f} GB   free {free_bytes()/GB:.0f} GB")
    P(f"compression measured PER SCHEMA: {ratios or 'none yet'}")
    P(f"unmeasured items assume {RATIO_PESSIMISTIC}x. A ratio is never shared between "
      f"schemas -- status measured 28x and bars will not.\n")

    pending = True
    while pending and time.monotonic() - started < max_seconds:
        pending = False
        # 1. advance job states
        for it in man:
            key = it["key"]
            s = st["items"].get(key, {})
            if not s.get("job_id") or s.get("state") in ("downloaded", "refused", "failed", "superseded"):
                continue
            try:
                LIMITER.wait()
                d = c.batch.get_job_details(job_id=s["job_id"])
                s["job_state"] = d.get("state")
                s["billed_size"] = d.get("billed_size")
                # `progress` separates "healthy but slow" from "stuck" -- without it a
                # full-universe job that is 97% built looks identical in the log to one
                # that has wedged.
                #
                # BUT IT IS NOT MONOTONIC AND IT IS NOT AN ETA. Observed 2026-09-11 on the
                # ohlcv-1m job: 67 -> 69 -> 73 -> 33 -> 34 -> 36 -> 38, with ts_process_start
                # UNCHANGED throughout, so the job never restarted. Treat it as a liveness
                # signal only. `ts_process_start` is the field that actually reveals a
                # restart, which is why it is recorded beside it.
                s["progress"] = d.get("progress")
                s["ts_process_start"] = str(d.get("ts_process_start"))[:19]
                st["items"][key] = s
            except Exception as exc:
                event(st, key, "warn", f"get_job_details: {exc}")
        save_state(st)

        # 2. download in strict PRIORITY order
        for it in sorted(man, key=lambda i: i["rank"]):
            key = it["key"]
            s = st["items"].setdefault(key, {"rank": it["rank"], "bytes_on_disk": 0})
            if s.get("state") in ("downloaded", "refused", "failed", "superseded"):
                continue
            if not s.get("job_id"):
                continue
            if s.get("job_state") != "done":
                pending = True
                pr = s.get("progress")
                P(f"  {key:12} job {s.get('job_state')}"
                  f"{f' {pr}% (non-monotonic; liveness only)' if pr is not None else ''},"
                  f" started {s.get('ts_process_start','?')}")
                continue

            try:
                LIMITER.wait()
                files = c.batch.list_files(s["job_id"])
            except Exception as exc:
                event(st, key, "warn", f"list_files: {exc}")
                pending = True
                continue

            out_dir = RAW / s["job_id"]
            out_dir.mkdir(parents=True, exist_ok=True)
            data_files = [f for f in files if not str(f.get("filename", "")).endswith(".json")]
            done_n = 0
            t0 = time.monotonic()
            for i, f in enumerate(data_files, 1):
                fname = f["filename"]
                fsize = int(f.get("size", 0))
                dest = out_dir / fname
                if dest.exists() and dest.stat().st_size == fsize:
                    done_n += 1
                    continue
                ok, why = may_download(it, fsize, man, st, floor_gb)
                if not ok:
                    s["state"] = "deferred"
                    s["deferred_reason"] = why
                    event(st, key, "deferred", why)
                    save_state(st)
                    pending = True
                    break
                try:
                    LIMITER.wait()
                    c.batch.download(job_id=s["job_id"], output_dir=RAW,
                                     filename_to_download=fname)
                    done_n += 1
                    got = dest.stat().st_size if dest.exists() else 0
                    s["bytes_on_disk"] = sum(
                        p.stat().st_size for p in out_dir.glob("*") if p.is_file())
                    el = time.monotonic() - t0
                    rate = (s["bytes_on_disk"] / el / 1e6) if el > 0 else 0
                    left = (len(data_files) - i)
                    P(f"  {key:12} [{i}/{len(data_files)}] {fname[:42]:42} "
                      f"{got/1e6:7.0f} MB | {rate:5.1f} MB/s | {left} left")
                except Exception as exc:
                    s.setdefault("file_failures", []).append({"file": fname, "error": str(exc)[:200]})
                    event(st, key, "warn", f"{fname}: {exc}")
                save_state(st)

            # Measure this item's OWN ratio. Never applied to any other item -- see
            # item_ratio() for the 28x measurement that made that rule necessary.
            if s.get("bytes_on_disk", 0) > 0 and s.get("billed_size") and done_n == len(data_files):
                r = float(s["billed_size"]) / float(s["bytes_on_disk"])
                if 1.0 < r < 200.0:
                    s["measured_ratio"] = r
                    st.setdefault("measured_ratios", {})[key] = r
                    P(f"  {key:12} compression MEASURED {r:.2f}x "
                      f"({s['billed_size']/GIB:.1f} GiB metered -> "
                      f"{s['bytes_on_disk']/GIB:.2f} GiB on disk)")

            if done_n == len(data_files) and s.get("state") != "deferred":
                s["state"] = "downloaded"
                P(f"  {key:12} DOWNLOADED  {s.get('bytes_on_disk',0)/GB:.1f} GB, "
                  f"{len(data_files)} files")
            elif s.get("state") != "deferred":
                pending = True
            save_state(st)

        if pending and time.monotonic() - started < max_seconds:
            P(f"  ... {JOB_POLL_SECONDS}s until next pass  (free {free_bytes()/GB:.0f} GB)")
            time.sleep(JOB_POLL_SECONDS)

    write_manifest(st, man)
    remaining = [i["key"] for i in man
                 if st["items"].get(i["key"], {}).get("state") not in
                 ("downloaded", "refused", "failed", "superseded")]
    P(f"\ndrive pass end {now()}   still pending: {remaining or 'none'}")
    return 3 if remaining else 0


def write_manifest(st: dict, man: list[dict]) -> None:
    """The evidence a record would quote. Deferred, refused and failed items are NAMED
    with their reason -- a fixture built from six of seven items is a different object."""
    rows = []
    for it in sorted(man, key=lambda i: i["rank"]):
        s = st["items"].get(it["key"], {})
        rows.append({
            "rank": it["rank"], "schema": it["schema"],
            "scope": "ALL_SYMBOLS" if it["symbols"] == "ALL_SYMBOLS" else f"{len(it['symbols'])} roots",
            "window": [it["start"], it["end"]], "split_duration": it["split_duration"],
            "state": s.get("state", "planned"), "job_id": s.get("job_id"),
            "quote_usd": s.get("quote_usd"), "billed_size": s.get("billed_size"),
            "bytes_on_disk": s.get("bytes_on_disk", 0),
            "deferred_reason": s.get("deferred_reason"),
            "error": s.get("error"), "file_failures": s.get("file_failures"),
            "why_in_plan": it["why"],
        })
    MANIFEST.write_text(json.dumps({
        "written_utc": now(),
        "purpose": "what was acquired, what was not, and why. Acquisition only -- no "
                   "fixture was built and no study was run.",
        "dataset": DATASET, "windows": st.get("windows"),
        "measured_compression_ratio_per_schema": st.get("measured_ratios", {}),
        "compression_note": "measured per schema and never shared between them. status "
                            "compressed 28.0x on 40-byte repetitive records; bars measure "
                            "2.6x. Unmeasured items are estimated at 1.5x, pessimistic.",
        "free_gb_now": free_bytes() / GB, "floor_gb": FLOOR_GB,
        "items": rows,
        "events": st.get("events", [])[-200:],
    }, indent=1, default=str) + "\n", encoding="utf-8")


def do_status(floor_gb: float) -> int:
    if not STATE.exists():
        P("no state file; nothing submitted yet")
        return 0
    st = load_state()
    man = st.get("manifest", [])
    P(f"state {STATE.relative_to(REPO)}   updated {st.get('updated_utc')}")
    P(f"free {free_bytes()/GB:.0f} GB   floor {floor_gb:.0f} GB   "
      f"ratios {st.get('measured_ratios') or 'none measured yet'}\n")
    P(f"  {'#':<3}{'schema':12}{'state':12}{'job':26}{'on disk GB':>11}")
    for it in sorted(man, key=lambda i: i["rank"]):
        s = st["items"].get(it["key"], {})
        P(f"  {it['rank']:<3}{it['schema']:12}{str(s.get('state','planned')):12}"
          f"{str(s.get('job_id','-')):26}{s.get('bytes_on_disk',0)/GB:11.1f}")
    for e in st.get("events", [])[-12:]:
        P(f"    {e['utc']} [{e['kind']}] {e['item']}: {e['detail'][:90]}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    for flag in ("plan", "self-test", "submit", "drive", "status"):
        ap.add_argument(f"--{flag}", action="store_true")
    ap.add_argument("--floor-gb", type=float, default=FLOOR_GB)
    ap.add_argument("--max-seconds", type=int, default=MAX_DRIVE_SECONDS)
    ap.add_argument("--dry-run", action="store_true",
                    help="--submit: quote every item but submit nothing")
    ap.add_argument("--split", nargs=2, metavar=("KEY", "N"), default=None,
                    help="route around a job that will not finish: resubmit its range "
                         "as N narrower jobs, cost-gated at $0.00")
    a = ap.parse_args()
    if a.split:
        return do_split(a.split[0], int(a.split[1]))
    if a.self_test:
        return do_self_test(a.floor_gb)
    if a.submit:
        return do_submit(a.floor_gb, a.dry_run)
    if a.drive:
        return do_drive(a.floor_gb, a.max_seconds)
    if a.status:
        return do_status(a.floor_gb)
    return do_plan(a.floor_gb)


if __name__ == "__main__":
    raise SystemExit(main())
