"""SnapshotStore: freeze fetched data and run only on frozen snapshots.

yfinance restates history, so the same code can give different results months apart.
The engine therefore reads snapshots rather than live fetches, and every trial logs
its snapshot_id.

snapshot_id is the sha256 of the payload bytes (bars.csv + events.json):
- Re-freezing the same data gives the same id, so anyone can reproduce a reported
  snapshot_id from a committed fixture.
- Restated history gives different bytes and so a new id.
- load() re-hashes and raises SnapshotIntegrityError on a mismatch.

A snapshot whose validation has hard violations is still written (for inspection)
but marked quarantined; load() raises QuarantinedSnapshotError unless
allow_quarantined=True.

Layout: <root>/<snapshot_id>/{bars.csv, events.json, meta.json}. Snapshots are local
and not committed; data enters the repo as committed fixtures.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Sequence

from .bars import TimestampedBar
from .cleaner import CleaningReport
from .corporate_actions import CorporateActions, load_events_json, save_events_json
from .csv_fixture import load_fixture_csv_with_extras, save_fixture_csv
from .validator import ValidationResult


class SnapshotIntegrityError(Exception):
    """The stored payload no longer hashes to its snapshot_id."""


class QuarantinedSnapshotError(Exception):
    """The snapshot failed its validation check and cannot be loaded for a run."""


@dataclass(frozen=True)
class Snapshot:
    snapshot_id: str
    bars_by_symbol: dict[str, list[TimestampedBar]]
    volumes_by_symbol: dict[str, list[float]]
    actions: CorporateActions
    meta: dict
    extras: dict[str, dict[str, list[float]]] = field(default_factory=dict)
    """Provider columns beyond the standard seven, e.g. Binance klines' separate base,
    quote and taker-buy volumes. Empty for snapshots without extra columns."""


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
        extra_columns: Mapping[str, Mapping[str, Sequence[float]]] | None = None,
    ) -> str:
        staging = self.root / f"_staging_{uuid.uuid4().hex}"
        staging.mkdir()
        try:
            save_fixture_csv(
                staging / "bars.csv", bars_by_symbol, volumes_by_symbol, extra_columns
            )
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
                # Same payload already frozen. Meta is not part of the id, so refresh it
                # with the latest validation; this lets a fixed validator lift a wrong
                # quarantine.
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
                f"snapshot {snapshot_id!r} payload hashes to {actual!r}; the frozen data has "
                "been modified and will not be loaded"
            )

        meta = json.loads((directory / "meta.json").read_text(encoding="utf-8"))
        if meta.get("quarantined") and not allow_quarantined:
            raise QuarantinedSnapshotError(
                f"snapshot {snapshot_id!r} is quarantined because it failed validation; "
                "pass allow_quarantined=True to inspect it"
            )

        bars, volumes, extras = load_fixture_csv_with_extras(directory / "bars.csv")
        return Snapshot(
            snapshot_id=snapshot_id,
            bars_by_symbol=bars,
            volumes_by_symbol=volumes,
            actions=load_events_json(directory / "events.json"),
            meta=meta,
            extras=extras,
        )


def _hash_payload(directory: Path) -> str:
    digest = hashlib.sha256()
    for name in ("bars.csv", "events.json"):
        digest.update((directory / name).read_bytes())
    return digest.hexdigest()
