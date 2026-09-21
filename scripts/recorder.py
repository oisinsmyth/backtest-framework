"""The forward data recorder's command line — D608, ledger doc §13A.3 "Track 2".

    uv run python scripts/recorder.py --selftest          # no network: the guards, proved to fire
    uv run python scripts/recorder.py --check             # gap check only, no fetch
    uv run python scripts/recorder.py --run               # ONE PASS over the `ready` jobs
    uv run python scripts/recorder.py --run --job bls_cpi_schedule    # one job, for a smoke

ONE PASS, AND THE HOST RE-INVOKES. `scripts/run_futures_acquisition.py:57` states the shape:
"one pass; the harness re-invokes on exit". This script fetches each ready job once, checks for
gaps, appends one health line and exits. It installs nothing, schedules nothing and daemonises
nothing — deposit Q17 ("Recorder hosting: which always-on machine or server, with what backup?")
is the principal's open question, and D608 answers only what the host would have to do:

  * invoke this command on a timer (any scheduler: Task Scheduler, cron, systemd, launchd);
  * start that timer on boot, because "survive reboots" is a property of the host, not of a
    process that exits in seconds;
  * keep `data/raw/recorder/` on a disk that is backed up — it is a CACHE and it is NOT
    disposable (`CLAUDE.md`, "Files"), and some of what it holds is free to fetch only today;
  * read the last line of `data/raw/recorder/health.jsonl`. A recorder that is not being invoked
    writes nothing at all, and only the host can tell that from a recorder with nothing to do.

EXIT CODES. 0 on a pass that fetched everything it could, **including a pass that found gaps** —
a gap is logged, never fatal, because a run that aborts on the first hole records nothing about
the rest. 1 only when the command itself could not run (a bad `--jobs` file, a failed self-test).

NOTHING HERE FILLS A GAP. See `backtest_framework.data.recorder`, which has no `fill_gap`.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from backtest_framework.data.recorder import (  # noqa: E402
    ChecksumMismatch,
    Gap,
    Job,
    JobConfigError,
    OverwriteRefused,
    RateLimiter,
    Record,
    Recorder,
    Run,
    RunOutcome,
    append_gaps,
    availability_time,
    check_gaps,
    check_gaps_scope,
    fetcher,
    health_line,
    iso_utc,
    load_jobs,
    sha256_bytes,
    utc_now,
)

JOBS = REPO / "data" / "recorder" / "jobs.json"
GAPS = REPO / "data" / "recorder" / "GAPS.md"
ROOT = REPO / "data" / "raw" / "recorder"

#: One request start every 2 s across all jobs. These are public government and exchange pages
#: and this is one pass over a handful of them; politeness costs nothing here.
MIN_INTERVAL = 2.0

#: D48/"declared outputs need a guard": the health line's keys are declared and asserted BEFORE
#: the line is written, so a renamed field breaks the run rather than the monitor reading it.
REQUIRED_HEALTH_KEYS = ("schema", "start", "end", "attempted", "ok", "failed", "bytes", "gaps", "host")


def P(*a: object) -> None:
    """Every line flushes: a backgrounded run redirects stdout to a file and Python block-buffers
    off a tty, so without this a healthy run looks hung (`run_futures_acquisition.py:105`)."""
    print(*a, flush=True)


def expect_raise(fn, exc_type: type[BaseException], what: str) -> None:
    """The self-test idiom of `scripts/stage0_d581_gamma_close.py:39`, widened past AssertionError
    because this module's guards raise named errors. A guard that has never been seen to fire is
    a guard nobody has tested."""
    try:
        fn()
    except exc_type as exc:
        P(f"    RAISES on {what}: {type(exc).__name__}: {str(exc)[:90]}")
        return
    raise AssertionError(f"guard did not raise {exc_type.__name__} on {what}")


# ------------------------------------------------------------------------------------- the pass
def run_once(jobs: list[Job], root: Path, gaps_path: Path, *, only: str | None = None,
             since: dt.date | None = None, fetch_limiter: RateLimiter | None = None) -> int:
    rec = Recorder(root)
    started = utc_now()
    limiter = fetch_limiter if fetch_limiter is not None else RateLimiter(MIN_INTERVAL)

    ready = [j for j in jobs if j.status == "ready"]
    if only is not None:
        named = [j for j in jobs if j.name == only]
        if not named:
            raise JobConfigError(f"--job {only!r} is not in the schedule ({len(jobs)} jobs)")
        if named[0].status != "ready":
            raise JobConfigError(f"--job {only!r} has status {named[0].status!r}; only 'ready' runs")
        ready = named

    skipped = [j for j in jobs if j.status != "ready"]
    P(f"[recorder] {len(jobs)} jobs: {len(ready)} to fetch, {len(skipped)} not ready")
    for j in skipped:
        P(f"    skip {j.name:24s} {j.status:12s} {j.note[:80]}")

    outcomes: list[RunOutcome] = []
    for job in ready:
        assert job.source_url is not None  # Job.__post_init__ guarantees it for 'ready'
        try:
            r = rec.record(
                job.name, job.name, fetcher(job.source_url, limiter=limiter),
                ext=job.ext, source_url=job.source_url,
            )
            P(f"    ok   {job.name:24s} {r.bytes:>9,} bytes  {r.sha256[:12]}  {r.path}")
            outcomes.append(RunOutcome(job=job.name, ok=True, bytes_written=r.bytes))
        except Exception as exc:  # noqa: BLE001 — nothing aborts the pass; every failure is named
            P(f"    FAIL {job.name:24s} {type(exc).__name__}: {str(exc)[:110]}")
            outcomes.append(RunOutcome(job=job.name, ok=False, error=type(exc).__name__,
                                       detail=str(exc)))

    found = report_gaps(jobs, rec, gaps_path, since=since)
    ended = utc_now()
    line = health_line(Run(start=iso_utc(started), end=iso_utc(ended),
                           outcomes=tuple(outcomes), gaps=tuple(found)))
    missing = [k for k in REQUIRED_HEALTH_KEYS if k not in line]
    if missing:
        raise AssertionError(f"health line is missing declared keys {missing}: {sorted(line)}")
    rec.append_health(line)
    P(f"[recorder] health -> {rec.health_path}")
    P(f"[recorder] {json.dumps(line, sort_keys=True)}")
    return 0


def report_gaps(jobs: list[Job], rec: Recorder, gaps_path: Path, *,
                since: dt.date | None = None) -> list[Gap]:
    scope = check_gaps_scope(jobs)
    P(f"[gaps] checked {len(scope['checked'])}: {', '.join(scope['checked']) or '-'}")
    if scope["not_checked_intraday"]:
        P(f"[gaps] NOT checked, intraday: {', '.join(scope['not_checked_intraday'])}")
    if scope["not_checked_not_ready"]:
        P(f"[gaps] NOT checked, not ready: {', '.join(scope['not_checked_not_ready'])}")

    by_job: dict[str, list[Record]] = {}
    for name in scope["checked"]:
        try:
            by_job[name] = rec.records(name)
        except FileNotFoundError:
            by_job[name] = []
        except ChecksumMismatch as exc:
            P(f"[gaps] {name}: CHECKSUM MISMATCH, reading unverified for the gap check only: {exc}")
            by_job[name] = rec.records(name, verify=False)

    found = check_gaps(jobs, by_job, utc_now(), since=since)
    if not found:
        P("[gaps] none")
        return []
    added = append_gaps(gaps_path, found, now_utc=utc_now())
    P(f"[gaps] {len(found)} open, {added} newly logged -> {gaps_path}")
    for g in found[:20]:
        P(f"    {g.date_et}  {g.job:24s} window closed {g.window_close_utc}")
    P("[gaps] NOT FILLED. Section 13A.3: gaps are never filled with estimates.")
    return found


# ---------------------------------------------------------------------------------- the selftest
PAY_A = b"schedule v1\n"
PAY_B = b"schedule v2\n"


def selftest(tmp: Path) -> int:
    """The good case FIRST, then every guard proved to fire on a deliberate break."""
    P("[selftest] 1. the GOOD case: three records, three files, two digests")
    root = tmp / "root"
    t0 = dt.datetime(2026, 9, 21, 14, 30, tzinfo=dt.timezone.utc)
    t1 = dt.datetime(2026, 9, 21, 14, 31, tzinfo=dt.timezone.utc)
    seq = iter([t0, t0, t1])
    rec = Recorder(root, clock=lambda: next(seq, t1))

    r1 = rec.record("probe", "probe", lambda: (PAY_A, {"content-type": "text/html"}), ext="html",
                    published_at="2026-09-18T08:30:00Z")
    r2 = rec.record("probe", "probe", lambda: (PAY_A, {}), ext="html")
    r3 = rec.record("probe", "probe", lambda: (PAY_B, {}), ext="html")
    for r in (r1, r2, r3):
        P(f"    {r.path}  {r.bytes} bytes  {r.sha256[:12]}  fetched_at {r.fetched_at}")

    assert r1.path != r2.path, "test 31: a second fetch must be a NEW FILE"
    assert r1.sha256 == r2.sha256, "test 31: same content, same checksum"
    assert r1.sha256 != r3.sha256, "test 31: checksums differ only if content differs"
    assert (root / "probe" / r1.path).read_bytes() == PAY_A, "record 1's bytes were changed"
    assert sha256_bytes((root / "probe" / r1.path).read_bytes()) == r1.sha256
    assert len(list((root / "probe").glob("*.html"))) == 3
    P("    test 31 holds: 3 files, 3 paths, 2 digests, record 1 untouched")

    assert availability_time(r1) == r1.fetched_at, "test 32"
    assert availability_time(r1) != r1.published_at, "test 32"
    P(f"    test 32 holds: availability {availability_time(r1)} ignores published_at "
      f"{r1.published_at}")

    assert [r.path for r in rec.records("probe")] == [r1.path, r2.path, r3.path]
    P("    read order == write order, and every checksum re-verified on read")

    P("[selftest] 2. the GOOD case: a schedule with every window satisfied has NO gaps")
    daily = Job(name="daily_probe", cadence="daily", window_et=("09:00", "17:00"),
                source_url="https://example.invalid/d", parser=None, status="ready",
                window_basis="synthetic, --selftest")
    weekly = Job(name="weekly_probe", cadence="weekly", weekday=4, window_et=("15:30", "23:00"),
                 source_url="https://example.invalid/w", parser=None, status="ready",
                 window_basis="synthetic, --selftest")
    now = dt.datetime(2026, 9, 22, 4, 0, tzinfo=dt.timezone.utc)
    full = {
        "daily_probe": [_stub("daily_probe", f"2026-09-{d:02d}T14:00:00Z") for d in range(16, 22)],
        "weekly_probe": [_stub("weekly_probe", "2026-09-18T20:00:00Z")],
    }
    assert check_gaps([daily, weekly], full, now, since=dt.date(2026, 9, 16)) == []
    P("    7 eligible windows, 7 satisfied, 0 gaps — the check can pass")

    P("[selftest] 3. a MISSED window produces a Gap and a GAPS.md line")
    sparse = {
        "daily_probe": [_stub("daily_probe", s) for s in (
            "2026-09-16T14:00:00Z", "2026-09-17T22:00:00Z",   # 09-17 is LATE, outside the window
            "2026-09-18T20:59:00Z", "2026-09-21T13:00:00Z")],
        "weekly_probe": [],
    }
    gaps = check_gaps([daily, weekly], sparse, now, since=dt.date(2026, 9, 16))
    assert len(gaps) == 4, f"want 4 gaps, got {len(gaps)}"
    assert [(g.date_et, g.job) for g in gaps] == [
        ("2026-09-17", "daily_probe"), ("2026-09-18", "weekly_probe"),
        ("2026-09-19", "daily_probe"), ("2026-09-20", "daily_probe")]
    gp = tmp / "GAPS.md"
    assert append_gaps(gp, gaps, now_utc=now) == 4
    for line in gp.read_text(encoding="utf-8").splitlines()[-4:]:
        P(f"    {line}")
    assert append_gaps(gp, gaps, now_utc=now) == 0, "append_gaps must not duplicate a logged gap"
    P("    a second append of the same gaps adds 0 lines — append-only, never rewritten")

    P("[selftest] 4. the guards, each proved to RAISE on a deliberate break")
    expect_raise(lambda: _overwrite(root / "probe" / r1.path), OverwriteRefused,
                 "writing to a path that already exists")
    expect_raise(lambda: _corrupt_then_read(rec, root, r1.path), ChecksumMismatch,
                 "a manifest whose sha does not match the bytes on disk")
    expect_raise(lambda: rec.record("probe", "probe", lambda: (PAY_A, {}), ext="html",
                                    published_at="2026-09-18 08:30"), JobConfigError,
                 "a published_at that is not an ISO-Z 20-character instant")
    expect_raise(lambda: rec.record("../escape", "k", lambda: (PAY_A, {}), ext="html"),
                 JobConfigError, "a job name that could escape its directory")
    expect_raise(lambda: Job(name="j", cadence="daily", window_et=("09:00", "17:00"),
                             source_url=None, parser=None, status="ready",
                             window_basis="x"), JobConfigError,
                 "status 'ready' with no source_url")
    expect_raise(lambda: Job(name="j", cadence="weekly", window_et=("09:00", "17:00"),
                             source_url="https://example.invalid", parser=None, status="ready",
                             window_basis="x"), JobConfigError,
                 "cadence 'weekly' with no weekday")
    expect_raise(lambda: Job(name="j", cadence="daily", window_et=("17:00", "09:00"),
                             source_url="https://example.invalid", parser=None, status="ready",
                             window_basis="x"), JobConfigError,
                 "a window that closes before it opens")
    expect_raise(lambda: Job(name="j", cadence="daily", window_et=("09:00", "17:00"),
                             source_url="https://example.invalid", parser=None, status="ready",
                             window_basis=" "), JobConfigError,
                 "a window with no stated basis")
    expect_raise(lambda: check_gaps([daily], sparse, now, since=dt.date(2026, 10, 1)),
                 JobConfigError, "a `since` after the ET date of now")
    expect_raise(lambda: rec.record("probe", "probe", lambda: ("not bytes", {}), ext="html"),
                 TypeError, "a fetch() that returns str instead of bytes")

    P("[selftest] 5. the real schedule loads, and its scope is named")
    jobs = load_jobs(JOBS)
    scope = check_gaps_scope(jobs)
    P(f"    {len(jobs)} jobs; checked {len(scope['checked'])}, "
      f"not ready {len(scope['not_checked_not_ready'])}, "
      f"intraday {len(scope['not_checked_intraday'])}")
    assert all(j.source_url for j in jobs if j.status == "ready")
    assert not any(j.source_url for j in jobs if j.status != "ready")

    P("[selftest] 6. there is no gap filler")
    from backtest_framework.data import recorder as mod
    assert not hasattr(mod, "fill_gap")
    bad = [n for n in dir(mod) if not n.startswith("_") and mod.FORBIDDEN_NAME_RE.search(n)]
    assert bad == ["FILL_IS_FORBIDDEN"], bad
    P(f"    {mod.FILL_IS_FORBIDDEN}")

    P("[selftest] PASS")
    return 0


def _stub(job: str, fetched_at: str) -> Record:
    return Record(job=job, key=job, path=f"{job}.html", fetched_at=fetched_at, published_at=None,
                  bytes=1, sha256="0" * 64, source_url=None, method="fetched")


def _overwrite(path: Path) -> None:
    from backtest_framework.data.recorder import _write_new_bytes
    _write_new_bytes(path, b"this must never land")


def _corrupt_then_read(rec: Recorder, root: Path, name: str) -> None:
    """Break exactly the scalar the guard compares (the file's bytes), not something near it."""
    victim = root / "probe" / name
    keep = victim.read_bytes()
    victim.write_bytes(keep + b"x")
    try:
        rec.records("probe")
    finally:
        victim.write_bytes(keep)


# ------------------------------------------------------------------------------------------ main
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--jobs", type=Path, default=JOBS)
    ap.add_argument("--root", type=Path, default=ROOT, help="raw cache root (data/raw/recorder)")
    ap.add_argument("--gaps", type=Path, default=GAPS)
    ap.add_argument("--job", type=str, default=None, help="run exactly one ready job")
    ap.add_argument("--since", type=str, default=None, help="first ET date to gap-check, YYYY-MM-DD")
    ap.add_argument("--run", action="store_true", help="one pass: fetch, gap check, health line")
    ap.add_argument("--check", action="store_true", help="gap check only, no fetch")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            return selftest(Path(td))

    since = dt.date.fromisoformat(args.since) if args.since else None
    jobs = load_jobs(args.jobs)

    if args.check:
        report_gaps(jobs, Recorder(args.root), args.gaps, since=since)
        return 0
    if args.run:
        return run_once(jobs, args.root, args.gaps, only=args.job, since=since)

    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
