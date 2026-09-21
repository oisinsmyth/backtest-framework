"""Property tests for `data/recorder.py` (D608) — the forward data recorder, ledger doc §13A.3.

Conventions per D78 (derandomized hypothesis; seeding owned by the library rather than a
hand-rolled seed parameter) as amended by D537 (`derandomize=True` fixes the seed but NOT the
examples drawn — since hypothesis 6.156.6 the constant pool is harvested from `sys.modules` at
test time, so a failure here reproduces within a run but the example set is not byte-stable
between a full-suite run and a single-file run; reproduce a failure with the whole suite).
`max_examples=40` and `deadline=None` keep the file inside the default gate.

WHAT IS WORTH A PROPERTY HERE. The exact strings are pinned by
`tests/golden/test_recorder_ledger.hand.txt` and the closed cases by
`tests/unit/test_recorder.py`. What no finite set of examples covers is the SHAPE of the three
guarantees this module exists to make:

  * **nothing is ever overwritten** — the dangerous case is N records landing in ONE second, and
    the collision ladder is quantified over here rather than exercised at N = 3;
  * **a gap report partitions the eligible windows** — every closed window is either satisfied by
    a record inside it or named as a gap, never both and never neither, for arbitrary stamps;
  * **`GAPS.md` only grows** — for any sequence of batches, every earlier state of the file is a
    byte prefix of every later one.

Plus the availability rule, which is a property and not a case: for ANY `published_at`, including
one after the fetch, the availability time is `fetched_at`.

Each example gets its own temporary directory; `tmp_path` is function-scoped and would otherwise
accumulate across examples. No network, no fixture, no strategy return, and no date from
2024-01-01 on outside a synthetic 2026 schedule, which is a clock and not a price.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings, strategies as st

from backtest_framework.data.recorder import (
    Gap,
    Job,
    Record,
    Recorder,
    append_gaps,
    availability_time,
    check_gaps,
    iso_utc,
    sha256_bytes,
)

SETTINGS = settings(derandomize=True, max_examples=40, deadline=None)

UTC = dt.timezone.utc
BASE = dt.datetime(2026, 9, 14, 12, 0, 0, tzinfo=UTC)

payloads = st.lists(st.binary(min_size=0, max_size=64), min_size=1, max_size=12)
#: seconds-since-BASE offsets, deliberately drawn with heavy repetition so within-second
#: collisions are the common case rather than a rare one
offsets = st.lists(st.integers(min_value=0, max_value=3), min_size=1, max_size=12)
hhmm = st.builds(lambda h, m: f"{h:02d}:{m:02d}", st.integers(0, 23), st.integers(0, 59))
et_dates = st.dates(min_value=dt.date(2026, 1, 1), max_value=dt.date(2026, 12, 31))


def _clock(instants: list[dt.datetime]):
    state = {"n": 0}

    def tick() -> dt.datetime:
        when = instants[min(state["n"], len(instants) - 1)]
        state["n"] += 1
        return when

    return tick


def _job(name: str, window: tuple[str, str]) -> Job:
    return Job(name=name, cadence="daily", window_et=window,
               source_url="https://example.invalid/x", parser=None, status="ready",
               window_basis="synthetic, property test")


def _stub(name: str, when: dt.datetime) -> Record:
    return Record(job=name, key=name, path=f"{name}.html", fetched_at=iso_utc(when),
                  published_at=None, bytes=1, sha256="0" * 64, source_url=None, method="fetched")


# ------------------------------------------------------------------------- nothing is overwritten
@given(bodies=payloads, secs=offsets)
@SETTINGS
def test_every_record_is_its_own_file_however_they_collide(bodies, secs) -> None:
    """Ledger doc unit test 31, as a property. N records give N paths and N files, each holding
    exactly the bytes that produced it — whatever the clock does."""
    instants = [BASE + dt.timedelta(seconds=secs[i % len(secs)]) for i in range(len(bodies))]
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        rec = Recorder(root, clock=_clock(instants))
        made = [rec.record("j", "k", (lambda b=b: (b, {})), ext="html") for b in bodies]

        paths = [r.path for r in made]
        assert len(set(paths)) == len(bodies)                       # no path reused
        on_disk = sorted(p.name for p in (root / "j").glob("*.html"))
        assert on_disk == sorted(paths)                             # one file per record, no more
        for body, r in zip(bodies, made, strict=True):
            assert (root / "j" / r.path).read_bytes() == body       # unmodified, and undisturbed
            assert r.sha256 == hashlib.sha256(body).hexdigest()
            assert r.bytes == len(body)
        # equal content gives equal checksums; different content gives different ones
        for (b1, r1), (b2, r2) in zip(zip(bodies, made, strict=True),
                                      zip(bodies[1:], made[1:], strict=True), strict=False):
            assert (r1.sha256 == r2.sha256) == (b1 == b2)


@given(bodies=payloads, secs=offsets)
@SETTINGS
def test_the_read_order_is_the_write_order(bodies, secs) -> None:
    instants = [BASE + dt.timedelta(seconds=secs[i % len(secs)]) for i in range(len(bodies))]
    instants.sort()                      # a real clock never goes backwards
    with tempfile.TemporaryDirectory() as td:
        rec = Recorder(Path(td), clock=_clock(instants))
        written = [rec.record("j", "k", (lambda b=b: (b, {})), ext="html").path for b in bodies]
        assert [r.path for r in rec.records("j")] == written


@given(body=st.binary(min_size=0, max_size=200))
@SETTINGS
def test_the_bytes_are_never_normalised(body) -> None:
    """D594 LF-pins text before hashing. A response is not source, and this module never does."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        r = Recorder(root, clock=lambda: BASE).record("j", "k", lambda: (body, {}), ext="bin")
        assert (root / "j" / r.path).read_bytes() == body
        assert sha256_bytes(body) == hashlib.sha256(body).hexdigest() == r.sha256
        assert Recorder(root).records("j")[0].sha256 == r.sha256   # and it re-verifies on read


# ------------------------------------------------------------------------------- the availability
@given(pub_offset=st.integers(min_value=-4000, max_value=4000))
@SETTINGS
def test_availability_is_fetched_at_wherever_published_at_sits(pub_offset) -> None:
    """Ledger doc unit test 32 / deposit D23, as a property: the answer does not depend on
    `published_at`, not even when the source claims to have published AFTER the fetch."""
    published = iso_utc(BASE + dt.timedelta(hours=pub_offset))
    with tempfile.TemporaryDirectory() as td:
        rec = Recorder(Path(td), clock=lambda: BASE)
        r = rec.record("j", "k", lambda: (b"x", {}), ext="html", published_at=published)
        assert availability_time(r) == iso_utc(BASE) == r.fetched_at
        assert availability_time(r) == availability_time(
            rec.record("j", "k", lambda: (b"x", {}), ext="html"))


# ----------------------------------------------------------------------------------- the gap set
@given(open_t=hhmm, close_t=hhmm, day=et_dates)
@SETTINGS
def test_a_window_closes_after_it_opens_in_utc_on_every_day_of_the_year(open_t, close_t, day) -> None:
    """Including both DST transition days. The conversion goes through the zone, so this holds
    without a special case — and the UTC span differs from the wall-clock span by at most an hour."""
    if open_t > close_t:
        open_t, close_t = close_t, open_t
    j = _job("j", (open_t, close_t))
    o, c = j.window_utc(day)
    assert c >= o
    wall = (int(close_t[:2]) * 60 + int(close_t[3:])) - (int(open_t[:2]) * 60 + int(open_t[3:]))
    assert abs((c - o).total_seconds() / 60 - wall) <= 60


@given(stamps=st.lists(st.integers(min_value=0, max_value=60 * 60 * 24 * 7), max_size=10),
       open_t=hhmm, close_t=hhmm)
@SETTINGS
def test_the_gap_report_partitions_the_closed_windows(stamps, open_t, close_t) -> None:
    """Every window that has closed is EITHER satisfied by a record inside it OR named as a gap.
    Never both, never neither — which is the claim `GAPS.md` makes to whoever reads it."""
    if open_t > close_t:
        open_t, close_t = close_t, open_t
    j = _job("probe", (open_t, close_t))
    since = dt.date(2026, 9, 14)
    now = dt.datetime(2026, 9, 22, 4, 0, tzinfo=UTC)
    records = [_stub("probe", BASE + dt.timedelta(seconds=s)) for s in stamps]

    gaps = check_gaps([j], {"probe": records}, now, since=since)
    gapped = {g.date_et for g in gaps}
    assert len(gapped) == len(gaps)                     # one line per window, never two

    day = since
    eligible, satisfied = 0, 0
    while day <= now.astimezone(dt.timezone.utc).date():
        o, c = j.window_utc(day)
        if c <= now:
            eligible += 1
            inside = any(o <= r.fetched_dt <= c for r in records)
            satisfied += inside
            assert inside != (day.isoformat() in gapped), day
        day += dt.timedelta(days=1)
    assert eligible - satisfied == len(gaps)


@given(stamps=st.lists(st.integers(min_value=0, max_value=60 * 60 * 24 * 7), max_size=8),
       extra=st.integers(min_value=0, max_value=60 * 60 * 24 * 7))
@SETTINGS
def test_adding_a_record_can_only_remove_gaps(stamps, extra) -> None:
    """Monotone in the records: a recorder that fetched MORE is never reported as having missed
    more. A gap report that could grow on new data would be unreadable."""
    j = _job("probe", ("09:00", "17:00"))
    since, now = dt.date(2026, 9, 14), dt.datetime(2026, 9, 22, 4, 0, tzinfo=UTC)
    before = {_stub("probe", BASE + dt.timedelta(seconds=s)) for s in stamps}
    after = before | {_stub("probe", BASE + dt.timedelta(seconds=extra))}
    g1 = {g.date_et for g in check_gaps([j], {"probe": list(before)}, now, since=since)}
    g2 = {g.date_et for g in check_gaps([j], {"probe": list(after)}, now, since=since)}
    assert g2 <= g1


# -------------------------------------------------------------------------------- GAPS.md grows
@given(batches=st.lists(st.lists(st.integers(min_value=1, max_value=28), min_size=0, max_size=5),
                        min_size=1, max_size=5))
@SETTINGS
def test_gaps_md_only_ever_grows_and_never_repeats_a_key(batches) -> None:
    """Append-only, in the strong sense: every earlier state of the file is a byte PREFIX of every
    later one, so no `logged` column is ever rewritten and no line is ever lost. And a gap already
    logged is not logged twice, so a recorder running hourly does not make one hole into twenty."""
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "GAPS.md"
        seen: set[str] = set()
        states: list[bytes] = []
        for n, batch in enumerate(batches):
            gaps = [Gap(job="probe", cadence="daily", date_et=f"2026-09-{d:02d}",
                        window_et=("09:00", "17:00"),
                        window_close_utc=f"2026-09-{d:02d}T21:00:00Z") for d in batch]
            fresh = {g.date_et for g in gaps} - seen
            added = append_gaps(path, gaps, now_utc=BASE + dt.timedelta(days=n))
            assert added == len(fresh)
            seen |= fresh
            states.append(path.read_bytes())

        for earlier, later in zip(states, states[1:], strict=False):
            assert later.startswith(earlier)
        text = path.read_text(encoding="utf-8")
        assert "\r" not in text
        body = [ln for ln in text.splitlines() if ln.startswith("| 2026-")]
        assert len(body) == len(seen)
        assert len({ln.split("|")[1].strip() for ln in body}) == len(seen)


# ------------------------------------------------------------------------------- the config guards
@given(name=st.text(min_size=1, max_size=12).filter(
    lambda s: not s.replace("_", "a").replace("-", "a").replace(".", "a").isalnum()))
@SETTINGS
def test_a_name_outside_the_alphabet_is_always_refused(name) -> None:
    """The name becomes a directory and a filename; anything that could escape one raises."""
    from backtest_framework.data.recorder import JobConfigError

    with tempfile.TemporaryDirectory() as td:
        with pytest.raises((JobConfigError, TypeError)):
            Recorder(Path(td), clock=lambda: BASE).record(name, "k", lambda: (b"x", {}), ext="html")
