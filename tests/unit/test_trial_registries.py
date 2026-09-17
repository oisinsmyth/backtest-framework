"""`data/trial_registries.json` against the studies that already published from it.

Two tiers, and the distinction is the point:

* **The cross-artifact tier runs anywhere**, including a clone with no databases. It checks the
  new record against `data/macd_ladder_summary.json`, whose `prior.per_registry` block three
  published studies depend on (`run_macd_ladder.py`, `run_impulse_macd.py:561`,
  `run_volume_filter.py:606`, all through `prior_etf_trials()`). Two derived records of the same
  databases, written by different scripts at different times, must agree -- and if they ever
  disagree, one of them is wrong about the evidence for a deflated-Sharpe hurdle.

* **The on-disk tier runs only where the registries are**, and is a skip elsewhere. It is the one
  that would catch a registry being truncated or replaced.

A registry is append-only STRUCTURALLY, not by convention: `trial_id` is the PRIMARY KEY and there
is no DELETE, UPDATE, REPLACE or VACUUM anywhere in `backtest_framework.registry`. So `rows` may
grow and must never shrink, and that asymmetry is what the on-disk tier asserts.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
ARTIFACT = REPO / "data" / "trial_registries.json"
LADDER = REPO / "data" / "macd_ladder_summary.json"


def _artifact() -> dict:
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def _rows_on_disk(path: Path) -> int:
    """Read-only, and never via TrialRegistry -- its constructor opens read-write and runs DDL."""
    uri = "file:" + path.as_posix() + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as conn:
        return int(conn.execute("select count(*) from trials").fetchone()[0])


# --------------------------------------------------------------- runs anywhere, clone included


def test_the_record_exists_and_covers_every_registry_it_claims_to():
    data = _artifact()
    entries = data["registries"]
    assert entries, "the artifact lists no registries, which is not a state this repository has"
    assert data["totals"]["registries"] == len(entries)
    assert data["totals"]["live"] == sum(1 for e in entries if e["status"] == "live")
    assert {e["status"] for e in entries} <= {"live", "superseded", "demo"}
    paths = [e["path"] for e in entries]
    assert len(set(paths)) == len(paths), "a path is recorded twice"


def test_the_etf_pool_matches_the_ladder_study_registry_by_registry():
    """The twelve the published multiplicity count is computed over.

    `macd_ladder_summary.json` carries its own `prior.per_registry` breakdown, written by a
    different script. Two independent derived records of the same databases; if they drift, the
    number under the README's headline is in question.
    """
    pool = {e["registry"]: e for e in _artifact()["registries"] if e["in_etf_pool"]}
    prior = json.loads(LADDER.read_text(encoding="utf-8"))["prior"]["per_registry"]

    assert set(pool) == set(prior), (
        f"the ETF pool disagrees on membership: only here {sorted(set(pool) - set(prior))}, "
        f"only in macd_ladder_summary.json {sorted(set(prior) - set(pool))}"
    )
    wrong = [
        f"  {name}: trial_registries.json says {pool[name]['rows']} rows / "
        f"{pool[name]['distinct_config_json']} configs, macd_ladder_summary.json says "
        f"{rec['rows']} / {rec['distinct_configs']}"
        for name, rec in prior.items()
        if pool[name]["rows"] != rec["rows"]
        or pool[name]["distinct_config_json"] != rec["distinct_configs"]
    ]
    assert not wrong, "two derived records of the same registries disagree:\n" + "\n".join(wrong)


def test_the_published_totals_reconcile():
    """`raw_rows` and the deduplicated pool must equal what the study published."""
    pool = _artifact()["etf_pool"]
    mult = json.loads(LADDER.read_text(encoding="utf-8"))["multiplicity"]
    prior = json.loads(LADDER.read_text(encoding="utf-8"))["prior"]

    assert pool["raw_rows"] == mult["raw_row_ceiling"], (
        f"raw rows {pool['raw_rows']} against the published ceiling {mult['raw_row_ceiling']}"
    )
    assert pool["distinct_configs_deduplicated"] == prior["distinct_configs"], (
        f"pool {pool['distinct_configs_deduplicated']} against the published "
        f"{prior['distinct_configs']}"
    )


def test_the_total_is_recorded_as_not_being_the_column_sum():
    """The one thing a reader is most likely to get wrong, so the file must say it.

    Summing the per-registry distinct-config column gives 2.16x the real pool, because the same
    config payload is logged in several registries. A hurdle computed from the sum would be far
    too lenient, so the artifact states the gap rather than leaving it to be noticed.
    """
    pool = _artifact()["etf_pool"]
    assert pool["sum_of_per_registry_distinct_configs"] > pool["distinct_configs_deduplicated"]
    assert (
        pool["collapsed_by_cross_registry_dedup"]
        == pool["sum_of_per_registry_distinct_configs"] - pool["distinct_configs_deduplicated"]
    )
    assert str(pool["sum_of_per_registry_distinct_configs"]) in pool["why_the_column_does_not_sum"]


def test_the_two_double_armed_registries_are_recorded_as_such():
    """`e1_universe` and `swing_universe` each hold two arms whose rows share `config_json`.

    The arm identity is only in `trial_id`, so `distinct_config_json` is half the trial count for
    these two. If that ever stops being true the artifact is describing different databases.
    """
    by = {e["registry"]: e for e in _artifact()["registries"]}
    for name in ("e1_universe", "swing_universe"):
        e = by[name]
        assert e["distinct_trial_id"] == e["rows"], f"{name}: trial_id is the primary key"
        assert e["distinct_config_json"] * 2 == e["rows"], (
            f"{name}: expected two arms sharing each config -- {e['rows']} rows over "
            f"{e['distinct_config_json']} configs"
        )


def test_the_five_registries_with_no_other_committed_count_are_here():
    """The reason this file exists: these five appear in no other artifact in the tree."""
    recorded = {e["registry"] for e in _artifact()["registries"]}
    orphans = {
        "breakout_study",
        "breakdown_study",
        "breakout_universe",
        "crypto_pairs",
        "breakout_intraday",
    }
    missing = sorted(orphans - recorded)
    assert not missing, f"{missing} have no committed trial count anywhere once this file drops them"


# ------------------------------------------------------- only where the databases actually are


def test_no_registry_has_lost_rows_since_it_was_recorded():
    data = _artifact()
    checked = 0
    shrunk = []
    for e in data["registries"]:
        path = REPO / e["path"]
        if not path.exists():
            continue
        checked += 1
        rows = _rows_on_disk(path)
        if rows < e["rows"]:
            shrunk.append(f"  {e['path']}: {rows} on disk, {e['rows']} recorded")
    if checked == 0:
        pytest.skip(
            "no trial registry is present here — they are gitignored and local; "
            "data/trial_registries.json is the committed record of what they held"
        )
    assert not shrunk, (
        "a registry is append-only (trial_id is the PRIMARY KEY; nothing in "
        "backtest_framework.registry deletes, updates or vacuums), so fewer rows means the file "
        "was truncated or replaced:\n" + "\n".join(shrunk)
    )
