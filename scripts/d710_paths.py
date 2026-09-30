"""D710: where the bytes live, for the three D710 scripts.

A worktree carries the TRACKED data (`data/calendar/`, `data/futures_costs.json`, ...) but not the gitignored raw
cache or the large fixtures, which live in the main checkout's `data/`. So:

  * tracked outputs (the calendars this line derives) are written under THIS checkout's `data/`   -> `tracked()`
  * the raw cache and the fixtures are read from the first `data/` up the tree that holds the
    fixture, or from an explicit `--data-root`                                                     -> `data_root()`
"""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FIXTURE_PROBE = Path("fixtures") / "fut_day1m.parquet"


def data_root(explicit: str | Path | None = None) -> Path:
    if explicit:
        p = Path(explicit)
        if not (p / FIXTURE_PROBE).exists():
            raise FileNotFoundError(f"--data-root {p} holds no {FIXTURE_PROBE}")
        return p
    for cand in [REPO / "data", *[q / "data" for q in REPO.parents]]:
        if (cand / FIXTURE_PROBE).exists():
            return cand
    raise FileNotFoundError(f"no data/ with {FIXTURE_PROBE} at or above {REPO}")


def tracked(*parts: str) -> Path:
    return REPO.joinpath("data", *parts)
