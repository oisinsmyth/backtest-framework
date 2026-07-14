"""SnapshotStore (D24, D72): fetch once, freeze, and only ever run on frozen data.

yfinance restates history — identical code produces different results months apart,
silently making TrialRegistry entries incomparable. So the engine never reads live
fetches; it reads snapshots, and every trial logs its snapshot_id.

Content-addressed identity: snapshot_id = sha256 over the frozen payload bytes
(bars.csv + events.json). Consequences, all deliberate (D72):
- Same data re-frozen → the SAME id (idempotent; also what makes a results doc's
  snapshot_id reproducible by anyone from a committed fixture).
- A restated history → different bytes → a NEW id — the D24 U-gate falls straight
  out of the addressing scheme instead of needing a version counter.
- load() re-hashes and refuses on mismatch — byte-identical or nothing.

Quarantine (D26): a snapshot whose validation has hard violations is still written
(for inspection) but flagged; load() raises QuarantinedSnapshotError unless
allow_quarantined=True is passed explicitly. Quarantined data cannot reach the
engine by any default path — structural, not conventional (Pillar 1).

Layout: <root>/<snapshot_id>/{bars.csv, events.json, meta.json}. The default root
data/snapshots/ has been gitignored since the day-one .gitignore — snapshots are
local artifacts; committed fixtures are how data enters the repo.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from .bars import TimestampedBar
from .cleaner import CleaningReport
from .corporate_actions import CorporateActions, load_events_json, save_events_json
from .csv_fixture import load_fixture_csv_with_volumes, save_fixture_csv
from .validator import ValidationResult


class SnapshotIntegrityError(Exception):
    """The stored payload no longer hashes to its snapshot_id."""


class QuarantinedSnapshotError(Exception):
    """The snapshot failed its sanity gate (D26) and cannot be loaded for a run."""


@dataclass(frozen=True)
class Snapshot:
    snapshot_id: str
    bars_by_symbol: dict[str, list[TimestampedBar]]
    volumes_by_symbol: dict[str, list[float]]
    actions: CorporateActions
    meta: dict


class SnapshotStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def create(
        self,
        bars_by_symbol: Mapping[str, Sequence[TimestampedBar]],
        actions: CorporateActions,
        volumes_by_symbol: Mapping[str, Sequence[float]] | None = None,
        cleaning_report: CleaningReport | None = None,
        validation: ValidationResult | None = None,
        extra_meta: dict | None = None,
    ) -> str:
        staging = self.root / f"_staging_{uuid.uuid4().hex}"
        staging.mkdir()
        try:
            save_fixture_csv(staging / "bars.csv", bars_by_symbol, volumes_by_symbol)
            save_events_json(staging / "events.json", actions)

            snapshot_id = _hash_payload(staging)

            quarantined = validation is not None and not validation.passed
            meta = {
                "snapshot_id": snapshot_id,
                "quarantined": quarantined,
                "cleaning_report": cleaning_report.to_meta() if cleaning_report else None,
                "validation": validation.to_meta() if validation else None,
                **(extra_meta or {}),
            }
            (staging / "meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8")

            final = self.root / snapshot_id
            if final.exists():
                # Identical PAYLOAD already frozen — idempotent on content. Meta is
                # provenance of the latest freeze (validator version, reports), not
                # part of the identity, so it refreshes: otherwise a fixed validator
                # could never un-quarantine data it had wrongly flagged (D72).
                (final / "meta.json").write_text(
                    (staging / "meta.json").read_text(encoding="utf-8"), encoding="utf-8"
                )
                shutil.rmtree(staging)
            else:
                staging.rename(final)
            return snapshot_id
        except Exception:
            shutil.rmtree(staging, ignore_errors=True)
            raise

    def load(self, snapshot_id: str, allow_quarantined: bool = False) -> Snapshot:
        directory = self.root / snapshot_id
        if not directory.is_dir():
            raise FileNotFoundError(f"no snapshot {snapshot_id!r} under {self.root}")

        actual = _hash_payload(directory)
        if actual != snapshot_id:
            raise SnapshotIntegrityError(
                f"snapshot {snapshot_id!r} payload hashes to {actual!r} — the frozen data has "
                "been modified; refusing to load it (D24)"
            )

        meta = json.loads((directory / "meta.json").read_text(encoding="utf-8"))
        if meta.get("quarantined") and not allow_quarantined:
            raise QuarantinedSnapshotError(
                f"snapshot {snapshot_id!r} is quarantined (failed its sanity gate, D26) — "
                "pass allow_quarantined=True only for inspection, never for a run"
            )

        bars, volumes = load_fixture_csv_with_volumes(directory / "bars.csv")
        return Snapshot(
            snapshot_id=snapshot_id,
            bars_by_symbol=bars,
            volumes_by_symbol=volumes,
            actions=load_events_json(directory / "events.json"),
            meta=meta,
        )


def _hash_payload(directory: Path) -> str:
    digest = hashlib.sha256()
    for name in ("bars.csv", "events.json"):
        digest.update((directory / name).read_bytes())
    return digest.hexdigest()
