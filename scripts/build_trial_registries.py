"""The committed record of the trial registries, which are 295 MB and live on one disk.

    python scripts/build_trial_registries.py --build     # writes data/trial_registries.json
    python scripts/build_trial_registries.py --verify    # re-reads the databases against it
    python scripts/build_trial_registries.py --print

WHY THIS EXISTS
---------------
PHILOSOPHY Pillar 3 and `docs/decisions/D20-trialregistry-every-backtest-run-appends-config.md`
rest the whole multiplicity argument on one property: **a trial count cannot be reconstructed
retroactively, so it has to be captured live.** Nineteen SQLite registries hold that capture. All
nineteen are gitignored (`.gitignore:22`), none is in `data/data_manifest.json`, and until this
file existed the word `sqlite` appeared in no reader-facing document in the repository.

The ETF programme's twelve registries already had their counts committed, inside
`data/macd_ladder_summary.json` under `prior.per_registry` -- which is D191's "cache the raw,
commit the derived" applied properly, and it is why the published 45,783 IS re-derivable from the
tree. **Five registries had no committed count anywhere**: `breakout_study`, `breakdown_study`,
`breakout_universe`, `crypto_pairs`, `breakout_intraday`. For those, roughly 75 MB of logged trial
history, Pillar 3's "cannot be reconstructed retroactively" was not a caution but a description of
the state. This file closes that.

It records provenance. It does not change, re-derive or second-guess any published number.

FOUR WAYS A NAIVE COUNT GOES WRONG, EACH MEASURED RATHER THAN ASSUMED
---------------------------------------------------------------------
1. **The total is not the column sum, and it is not close.** The twelve ETF registries'
   distinct-config counts sum to 97,966. De-duplicated ACROSS registries they are 45,346, because
   52,620 config payloads are byte-identical in more than one file -- the same cohort and
   cost-stack payload is logged in `e1_universe`, `combined_universe`, `portfolio_universe` and
   `swing_universe` alike. A reader who sums the column gets 2.16x the real pool. The sum is
   therefore recorded here EXPLICITLY, beside the deduplicated total, so that the gap is a stated
   fact rather than an apparent arithmetic error.
2. **Two registries hold two study arms each, and the logged config cannot see it.**
   `e1_universe` is 41,760 rows over 20,880 configs and `swing_universe` is 20,880 over 10,440:
   each holds two arms whose paired rows share `config_json` AND `trial_hash`, with the arm
   identity living only in `trial_id`. "Distinct config = distinct trial" is false for these two,
   so `distinct_trial_id` is recorded beside `distinct_config_json` and the collapse is visible.
3. **A sha256 here is a hash under READ-ONLY access, and that qualifier is load-bearing.** Reads
   do not move the bytes (every registry is `journal_mode=delete`, so there is no WAL sidecar).
   But `TrialRegistry.__init__` opens the file READ-WRITE and runs `CREATE TABLE IF NOT EXISTS`
   plus `commit()`, and every `scripts/run_*.py` constructs one at module setup -- so merely
   importing a runner can move a registry's bytes without logging a single trial. This script
   connects with `mode=ro` and never constructs a `TrialRegistry`. A hash mismatch with equal row
   counts means the file was opened for writing, not that a trial was logged.
4. **Three scripts publish a count off these files, not one.** `run_macd_ladder.py`,
   `run_impulse_macd.py:561` and `run_volume_filter.py:606`, all through
   `run_macd_ladder.prior_etf_trials()`. A claim about "the published trial count" is a claim
   about all three.

WHY NOT `data/data_manifest.json`
---------------------------------
`build_data_manifest.py` selects by SUFFIX (`BULK_SUFFIXES`, `:53`). Adding `.sqlite` there would
reclassify these as *bulk panels*, move the count of 118, and falsify the "118 panels, 116 not in
git" sentence everywhere it is quoted. A registry is provenance, not a panel, and a panel is
re-fetchable where a registry is not. Separate contract, separate file.

**Nothing here reads a metric.** If a function in this file parses `metrics_json`, it is a bug.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ARTIFACT = REPO / "data" / "trial_registries.json"
LADDER = REPO / "data" / "macd_ladder_summary.json"

#: The pool `run_macd_ladder.prior_etf_trials()` counts, hand-enumerated there at :729-742 with no
#: comment saying why the other five are excluded. It is programme membership -- these twelve are
#: the ETF-fixture programme; `breakout_study`, `breakdown_study`, `breakout_universe`,
#: `breakout_intraday` and `crypto_pairs` are the crypto/breakout programme and are a different
#: line of work, not an oversight. Recorded here because that was nowhere in the tree.
ETF_POOL = (
    "e1_universe",
    "combined_universe",
    "portfolio_universe",
    "swing_universe",
    "capacity_portfolio",
    "etf_universe",
    "gross_sweep",
    "capacity_study",
    "convention_sensitivity",
    "pairs_study_v1",
    "pairs_study_v2",
    "pairs_study_v3",
)

#: `data/archive/breakout_v1/` predates D98, which re-defined the trial pool and states that
#: pre-fix registry rows must not be mixed with post-fix ones. It is recorded and excluded from
#: every total: stating the supersession is more useful than silently dropping the file.
SUPERSEDED = ("data/archive/breakout_v1/breakout_study_registry.sqlite",)

#: Ten rows written by `scripts/run_first_result.py` while the registry itself was being built.
#: Real logged trials, no study depends on them, and it is the only registry outside `data/`.
DEMO = ("trial_registry.sqlite",)


def registry_paths() -> list[Path]:
    found = sorted(REPO.glob("data/**/*.sqlite"))
    root = REPO / "trial_registry.sqlite"
    if root.exists():
        found.append(root)
    return found


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_counts(path: Path) -> tuple[int, int, set[str]]:
    """Rows, distinct trial_id, and the set of distinct config payloads -- READ-ONLY.

    `mode=ro` rather than a plain connect, and never `TrialRegistry(path)`: the constructor opens
    read-write and runs DDL, which moves the bytes of a file that is the evidence and is not in
    git. See the module docstring, hazard 3.
    """
    uri = "file:" + path.as_posix() + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as conn:
        rows = conn.execute("select count(*) from trials").fetchone()[0]
        ids = conn.execute("select count(distinct trial_id) from trials").fetchone()[0]
        configs = {c for (c,) in conn.execute("select distinct config_json from trials")}
    return int(rows), int(ids), configs


def status_of(rel: str) -> str:
    if rel in SUPERSEDED:
        return "superseded"
    if rel in DEMO:
        return "demo"
    return "live"


def stem_of(rel: str) -> str:
    name = Path(rel).name
    return name[: -len("_registry.sqlite")] if name.endswith("_registry.sqlite") else name


def scan() -> dict:
    entries = []
    pool_configs: set[str] = set()
    pool_sum = 0

    for path in registry_paths():
        rel = path.relative_to(REPO).as_posix()
        rows, ids, configs = read_counts(path)
        stem = stem_of(rel)
        entries.append(
            {
                "path": rel,
                "registry": stem,
                "status": status_of(rel),
                "in_etf_pool": stem in ETF_POOL and status_of(rel) == "live",
                "rows": rows,
                "distinct_trial_id": ids,
                "distinct_config_json": len(configs),
                "bytes": path.stat().st_size,
                "sha256": sha256_of(path),
            }
        )
        if stem in ETF_POOL and status_of(rel) == "live":
            pool_configs |= configs
            pool_sum += len(configs)

    live = [e for e in entries if e["status"] == "live"]
    pool = [e for e in entries if e["in_etf_pool"]]

    return {
        "measured_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "note": (
            "The trial registries: 295 MB of live-captured multiplicity evidence, gitignored, on "
            "one disk, and listed in no other manifest. PHILOSOPHY Pillar 3 and D20 rest on a "
            "trial count being captured live because it cannot be reconstructed afterwards -- so "
            "this file is the derived record of what the databases held when it was written. It "
            "is provenance, not a recovery path: unlike data/data_manifest.json there is no blob "
            "id, because these were never tracked. If a registry is lost, the counts below are "
            "what survives of it."
        ),
        "read_access": (
            "Every sha256 here is taken under sqlite3 mode=ro. TrialRegistry.__init__ opens a "
            "registry READ-WRITE and runs CREATE TABLE IF NOT EXISTS, and every scripts/run_*.py "
            "constructs one at import, so a hash can move without a trial being logged. A hash "
            "mismatch at an UNCHANGED row count means the file was opened for writing."
        ),
        "etf_pool": {
            "members": list(ETF_POOL),
            "why_these": (
                "The pool run_macd_ladder.prior_etf_trials() counts (:729-742). Membership is by "
                "programme -- these twelve are the ETF-fixture line; breakout_study, "
                "breakdown_study, breakout_universe, breakout_intraday and crypto_pairs are the "
                "crypto/breakout line and are a different body of work, not an omission. The "
                "enumeration there carries no comment saying so, which is why it is said here."
            ),
            "predicate": "distinct logged config payload, de-duplicated across registries (D98/D116/D126/D142)",
            "raw_rows": sum(e["rows"] for e in pool),
            "distinct_configs_deduplicated": len(pool_configs),
            "sum_of_per_registry_distinct_configs": pool_sum,
            "collapsed_by_cross_registry_dedup": pool_sum - len(pool_configs),
            "why_the_column_does_not_sum": (
                f"The per-registry distinct-config column sums to {pool_sum}, and the pool is "
                f"{len(pool_configs)}. The difference, {pool_sum - len(pool_configs)}, is config "
                "payloads that are byte-identical in more than one registry: the same cohort and "
                "cost-stack payload is logged by several studies. Summing the column overstates "
                "the pool by about 2.2x, which would understate every deflated-Sharpe hurdle "
                "computed from it."
            ),
        },
        "totals": {
            "registries": len(entries),
            "live": len(live),
            "live_rows": sum(e["rows"] for e in live),
            "bytes": sum(e["bytes"] for e in entries),
        },
        "registries": entries,
    }


def build() -> dict:
    fresh = scan()
    # Keep the date the numbers last MOVED, not the date the command last ran. Otherwise --build
    # is not idempotent, every run is a diff, and a dated measurement stops meaning anything.
    # Round ten has already found two generators in this repository that grew their own output.
    if ARTIFACT.exists():
        old = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        candidate = dict(fresh)
        candidate["measured_at"] = old.get("measured_at", fresh["measured_at"])
        if candidate == old:
            return old
    return fresh


def cmd_build() -> int:
    data = build()
    ARTIFACT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    t = data["totals"]
    p = data["etf_pool"]
    print(
        f"{t['registries']} registries ({t['live']} live), {t['bytes'] / 1048576:.1f} MB -> "
        f"{ARTIFACT.relative_to(REPO).as_posix()}"
    )
    print(f"  ETF pool: {p['raw_rows']:,} rows, {p['distinct_configs_deduplicated']:,} distinct configs")
    print(f"  column sums to {p['sum_of_per_registry_distinct_configs']:,}; the pool is not the sum")
    missing = [e["registry"] for e in data["registries"] if e["status"] == "live" and e["rows"] == 0]
    if missing:
        print(f"  EMPTY: {missing}")
    return 0


def cmd_verify() -> int:
    if not ARTIFACT.exists():
        raise SystemExit(f"{ARTIFACT.relative_to(REPO).as_posix()} does not exist -- run --build")
    recorded = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    by_path = {e["path"]: e for e in recorded["registries"]}
    present = {p.relative_to(REPO).as_posix() for p in registry_paths()}

    problems, absent, grew = [], [], []
    for rel, rec in by_path.items():
        if rel not in present:
            absent.append(rel)
            continue
        rows, ids, configs = read_counts(REPO / rel)
        if rows < rec["rows"]:
            problems.append(
                f"  {rel}: {rows} rows on disk, {rec['rows']} recorded -- a registry is "
                "append-only (trial_id is the PRIMARY KEY and nothing in the package deletes), "
                "so FEWER rows means the file was truncated or replaced"
            )
        elif rows > rec["rows"]:
            grew.append(f"  {rel}: {rec['rows']} -> {rows} rows")
        elif sha256_of(REPO / rel) != rec["sha256"]:
            problems.append(
                f"  {rel}: same {rows} rows, different bytes -- opened read-write without a "
                "trial being logged (see `read_access` in the artifact)"
            )
    for rel in sorted(present - set(by_path)):
        problems.append(f"  {rel}: on disk and not recorded -- run --build")

    print(f"{len(by_path)} recorded, {len(present)} on disk, {len(absent)} absent here")
    if grew:
        print(f"{len(grew)} registry(ies) grew since the measurement, which is normal:")
        print("\n".join(grew))
        print("  run --build to re-record")
    if problems:
        print(f"{len(problems)} problem(s):")
        print("\n".join(problems))
        return 1
    print("every present registry matches the record")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--print", action="store_true", dest="to_stdout")
    args = ap.parse_args(argv)

    if args.to_stdout:
        sys.stdout.write(json.dumps(build(), indent=2) + "\n")
        return 0
    if args.build:
        return cmd_build()
    if args.verify:
        return cmd_verify()
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
