"""Append-only trial registry (D20).

Every backtest run must be logged before any real experimentation happens — Deflated
Sharpe requires knowing how many trials were attempted, and that count can't be
reconstructed after the fact; this is the one component that can't be retrofitted.
Backed by SQLite so it survives process restarts for free. Append-only is enforced by
the primary key, not by convention (see PHILOSOPHY.md, Pillar 1 — trust is structural).
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class TrialAlreadyExistsError(Exception):
    """Raised when attempting to insert a trial_id that's already in the registry."""


@dataclass(frozen=True)
class TrialRecord:
    trial_id: str
    config: dict[str, Any]
    params: dict[str, Any]
    metrics: dict[str, Any]
    snapshot_id: str
    seed: int
    trial_hash: str
    created_at: str


def canonical_json(obj: Any) -> str:
    """Deterministic JSON: sorted keys, no whitespace ambiguity — same object, same string."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def compute_trial_hash(config: dict[str, Any], snapshot_id: str, seed: int) -> str:
    """Hash of (config, snapshot_id, seed). Identical inputs must hash identically, and
    the hash must change under any semantic change to any of the three (D20)."""
    payload = canonical_json({"config": config, "snapshot_id": snapshot_id, "seed": seed})
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class TrialRegistry:
    """A local, file-backed, append-only log of every backtest trial run."""

    def __init__(self, path: str | Path):
        self._path = Path(path)
        self._conn = sqlite3.connect(self._path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS trials (
                trial_id TEXT PRIMARY KEY,
                config_json TEXT NOT NULL,
                params_json TEXT NOT NULL,
                metrics_json TEXT NOT NULL,
                snapshot_id TEXT NOT NULL,
                seed INTEGER NOT NULL,
                trial_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def add_trial(
        self,
        trial_id: str,
        config: dict[str, Any],
        params: dict[str, Any],
        metrics: dict[str, Any],
        snapshot_id: str,
        seed: int,
    ) -> str:
        """Append a new trial and return its trial_hash.

        Raises TrialAlreadyExistsError if trial_id is already present — the registry is
        append-only by construction (the primary key constraint), not by convention.
        """
        trial_hash = compute_trial_hash(config, snapshot_id, seed)
        created_at = datetime.now(timezone.utc).isoformat()
        try:
            self._conn.execute(
                """
                INSERT INTO trials
                    (trial_id, config_json, params_json, metrics_json, snapshot_id, seed, trial_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trial_id,
                    canonical_json(config),
                    canonical_json(params),
                    canonical_json(metrics),
                    snapshot_id,
                    seed,
                    trial_hash,
                    created_at,
                ),
            )
            self._conn.commit()
        except sqlite3.IntegrityError as exc:
            raise TrialAlreadyExistsError(f"trial_id {trial_id!r} already exists in the registry") from exc
        return trial_hash

    def get_trial(self, trial_id: str) -> TrialRecord:
        row = self._conn.execute(
            "SELECT trial_id, config_json, params_json, metrics_json, snapshot_id, seed, trial_hash, created_at "
            "FROM trials WHERE trial_id = ?",
            (trial_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"no trial with trial_id {trial_id!r}")
        return _row_to_record(row)

    def all_trials(self) -> list[TrialRecord]:
        rows = self._conn.execute(
            "SELECT trial_id, config_json, params_json, metrics_json, snapshot_id, seed, trial_hash, created_at "
            "FROM trials ORDER BY created_at"
        ).fetchall()
        return [_row_to_record(row) for row in rows]

    def __len__(self) -> int:
        (count,) = self._conn.execute("SELECT COUNT(*) FROM trials").fetchone()
        return count

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> TrialRegistry:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


def _row_to_record(row: tuple[Any, ...]) -> TrialRecord:
    trial_id, config_json, params_json, metrics_json, snapshot_id, seed, trial_hash, created_at = row
    return TrialRecord(
        trial_id=trial_id,
        config=json.loads(config_json),
        params=json.loads(params_json),
        metrics=json.loads(metrics_json),
        snapshot_id=snapshot_id,
        seed=seed,
        trial_hash=trial_hash,
        created_at=created_at,
    )
