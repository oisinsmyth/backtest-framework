"""The panel loader chokepoint: one door onto every bulk panel, with the seal on it — D609.

WHY A CHOKEPOINT, AND WHY THIS ONE
----------------------------------
D594 built the frozen-protocol helpers — `filter_before`, `assert_none_at_or_after`,
`window_record`, `refuse_without_word` — and named them as the thing "a new runner can import
instead of retyping". Measured on 2026-09-22, **no runner imports any of them.** The importers
are their own tests, `scripts/freeze.py`, and `validation/track3.py`'s `assert_frozen`. Zero
runners. Meanwhile 232 raw `read_csv`/`read_parquet` calls sit across 122 scripts, `RESERVED_FROM`
is defined at `scripts/run_d555_tsmom_replication.py:43` and re-exported by eight more runners,
and seven `--principals-word` runners hand-roll the refusal `frozen.refuse_without_word`
(`frozen.py:972`) prints.

A helper nobody calls is not a guard. **This module is the call site**: one function that a
runner uses INSTEAD of `pd.read_csv`, which cannot be used without naming a cut, and which
carries the three-layer guard, the manifest digest and the window record on every read.

WHAT IT DOES NOT DO, STATED SO NOBODY READS IT AS DONE
------------------------------------------------------
**No runner is migrated onto it by this record.** The migration set is written down instead,
so that a later record migrates a named list rather than whatever it notices:

  * the nine that define or import `RESERVED_FROM` — `run_d555_tsmom_replication.py:43` and
    `run_d556`, `run_d557`, `run_d558`, `run_d559`, `run_d561`, `run_d562`, `run_d564`,
    `run_d565`, plus `stage0_d581_gamma_close.py` (its `RESERVED_FROM` import);
  * the seven `--principals-word` runners — `d503_forward_book.py`,
    `run_d473_downleg_component.py`, `run_d490_range_reversion.py`,
    `run_d498_k8_and_second_clocks.py`, `run_d566_joint_forward_read.py`,
    `run_d574_basis_momentum_forward.py`, `run_d578_sd_net_short_forward.py`.

**The read log has no committed home.** `read_log=` appends one JSON line wherever the caller
points it and the default is to write nothing. Where a programme-wide read log should live, and
whether it is committed, is the same open question as the seal date — see below.

**IT PICKS NO SEAL DATE.** `reserved_from` has NO DEFAULT and never will. D594's module docstring
gives the reason and it has got sharper since: the deposit seals 2025-03-01 → 2026-09-18, this
repository reserves 2024-01-01 onward, and `data/fixtures/fut_book_depth_1m.csv.gz` — D604's own
depth panel — spans 2026-08-11 to 2026-09-09, which is inside the deposit's vault window AND
after this repository's seal. `depth_bar` (`costs/futures_impact.py:361`) handles it by passing
`reserved_from = day`, i.e. by asserting nothing. That panel is the case that proves a default
would be a wrong answer for someone: **loading it here with `reserved_from="2024-01-01"` and no
word returns ZERO ROWS**, correctly, and the reconciliation is the principal's decision.

THE THREE LAYERS, AND WHERE THEY COME FROM
------------------------------------------
Layer 1 filter, layer 2 assert, layer 3 record — `frozen.filter_before`,
`frozen.assert_none_at_or_after`, `frozen.window_record`, in that order, unchanged. This module
adds the two facts they cannot know: **which column** (`panel_catalogue.py`) and **which file**
(`data/data_manifest.json`, whose sha256 is re-derived on every read with
`frozen.sha256_file(text_normalise=False)` — bit-identical to `build_data_manifest.py:63` and to
`run_d555:79`, and the only hashing route used here).

THE HONEST-SKIP RULE LIVES HERE NOW
-----------------------------------
`panel_status` is the distinction `tests/conftest.py` used to hold in `requires_panel` and
`loading_a_panel`, lifted verbatim: a missing file the
manifest lists is a panel D536 untracked and a skip; a missing file it does not list is a wrong
path, a renamed artifact or a fixture nobody built, and is a bug. `tests/conftest.py` is now a
four-line adapter over this function, and the two places that had retyped the rule by hand —
`scripts/futures_impact_table.py:293` and `tests/unit/test_fut_book_depth.py:58` — call it.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, Mapping, Sequence

import numpy as np

from ..registry.trial_registry import canonical_json
from ..validation.frozen import (
    assert_none_at_or_after,
    filter_before,
    refuse_without_word,
    sha256_file,
    window_record,
)
from .csv_fixture import _open_text
from .panel_catalogue import DAY_FORMATS, PERIOD_FORMATS, PanelSpec, spec_for

__all__ = [
    "REPO",
    "MANIFEST",
    "PanelStatus",
    "PanelError",
    "PanelAbsent",
    "PanelDigestError",
    "PanelRefused",
    "PanelCutError",
    "WINDOW_KEYS",
    "panel_names",
    "panel_status",
    "absent_reason",
    "unlisted_message",
    "manifest_entry",
    "convert_cut",
    "LoadedPanel",
    "load_panel",
]

REPO = Path(__file__).resolve().parents[3]
MANIFEST = REPO / "data" / "data_manifest.json"

PanelStatus = Literal["present", "absent_listed", "absent_unlisted"]
"""`present` the file is on disk; `absent_listed` the manifest knows it and it is not;
`absent_unlisted` neither — which is a bug, never absent data."""

WINDOW_KEYS: tuple[str, ...] = (
    "first_session_read",
    "last_session_read",
    "reserved_from",
    "sessions_read",
    "distinct_sessions_read",
    "reserved_rows_read",
)
"""The six keys `frozen.window_record` emits, and the six `windows_update` merges."""

_DAY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_MONTH_START_RE = re.compile(r"^(\d{4})-(\d{2})-01$")
_YEAR_START_RE = re.compile(r"^(\d{4})-01-01$")


class PanelError(Exception):
    """The loader was used in a way that cannot be answered with a correct frame (D48)."""


class PanelAbsent(PanelError, FileNotFoundError):
    """The panel is not on disk. `status` says whether the manifest knows it.

    It subclasses `FileNotFoundError` because that is what `tests/conftest.py` has always
    raised for the unlisted case, and a caller catching `FileNotFoundError` must keep working.
    """

    def __init__(self, message: str, *, status: PanelStatus) -> None:
        super().__init__(message)
        self.status: PanelStatus = status


class PanelDigestError(PanelError):
    """What is on disk does not hash to what `data/data_manifest.json` records."""


class PanelRefused(PanelError):
    """An opening of the reserved slice was asked for without the principal's word."""


class PanelCutError(PanelError):
    """`reserved_from` cannot be expressed in this panel's own date format."""


# ---------------------------------------------------------------------------
# the manifest, and the honest-skip rule (tests/conftest.py:39-115, verbatim)
# ---------------------------------------------------------------------------
@lru_cache(maxsize=1)
def _manifest() -> dict[str, Any]:
    if not MANIFEST.exists():  # pragma: no cover - the manifest is committed
        return {}
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def panel_names() -> frozenset[str]:
    """The basenames D536 untracked, read from the manifest.

    This set is what makes the skip rule safe: a missing file whose name is in here is a panel
    the repository deliberately stopped carrying, and skipping is right. A missing file whose
    name is NOT in here is a bug -- a typo'd path, a renamed artifact, a fixture nobody built --
    and it re-raises. Without that distinction the guard would convert every FileNotFoundError
    into a green run, which is how a suite stops testing anything.
    """
    manifest = _manifest()
    if not manifest:  # pragma: no cover - the manifest is committed
        return frozenset()
    return frozenset(Path(f["path"]).name for f in manifest["files"])


@lru_cache(maxsize=1)
def _entries_by_name() -> dict[str, dict[str, Any]]:
    manifest = _manifest()
    if not manifest:  # pragma: no cover - the manifest is committed
        return {}
    return {Path(f["path"]).name: f for f in manifest["files"]}


def manifest_entry(path: str | Path) -> dict[str, Any] | None:
    """The manifest row for a path, matched on BASENAME as the skip rule matches."""
    return _entries_by_name().get(Path(path).name)


def panel_status(path: str | Path) -> PanelStatus:
    """Present, absent-but-listed, or absent-and-unlisted. The whole decision, in one place."""
    p = Path(path)
    if p.exists():
        return "present"
    return "absent_listed" if p.name in panel_names() else "absent_unlisted"


def absent_reason(name: str) -> str:
    """The skip reason for a listed panel (`tests/conftest.py:84`, verbatim)."""
    return (
        f"{name} absent — the bulk panels left the index in D536. "
        "See data/data_manifest.json for its sha256 and git blob id."
    )


def unlisted_message(path: str | Path) -> str:
    """The bug message for an unlisted absence (`tests/conftest.py:74-78`, verbatim)."""
    return (
        f"{path} does not exist and `data/data_manifest.json` does not list it, so it is "
        "not a bulk panel D536 untracked -- it is a wrong path, a renamed artifact or a "
        "fixture nobody built. Skipping here would report a bug as absent data."
    )


# ---------------------------------------------------------------------------
# the cut
# ---------------------------------------------------------------------------
def _check_iso_day(value: Any, label: str = "reserved_from") -> str:
    if not isinstance(value, str) or not _DAY_RE.fullmatch(value):
        raise PanelError(
            f"{label} must be a zero-padded ISO day 'YYYY-MM-DD', got {value!r}. It has NO "
            "DEFAULT on purpose: the deposit seals 2025-03-01..2026-09-18 and this repository "
            "reserves 2024-01-01 onward, and a library that picked one would silently change "
            "which slice a runner reads."
        )
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise PanelError(f"{label}={value!r} is not a real date: {exc}") from exc
    return value


def convert_cut(date_format: str, reserved_from: str) -> str:
    """`reserved_from`, in the panel's own date units.

    A day format takes it unchanged -- `frozen._day_strings` slices the column to ten
    characters, so `2024-01-01T09:30:00` and `2024-01-01` compare identically.

    A PERIOD format converts: `2024-01-01` becomes `202401` (yyyymm) or `2024-01` (yyyy_mm),
    both of which sort lexically the way they sort chronologically because both are fixed-width
    and zero-padded. A cut that is not the first of a month CANNOT be expressed in a monthly
    panel's units -- there is no string that means "after the 14th of January" on a series with
    one row for January -- so it raises rather than rounding, which would move the cut by up to
    a month in a direction nobody chose.

    `year_prefix` is the same argument one step coarser, and it exists because one panel forced
    it. See `_period_keys`.
    """
    _check_iso_day(reserved_from)
    if date_format in DAY_FORMATS:
        return reserved_from
    if date_format == "year_prefix":
        m = _YEAR_START_RE.fullmatch(reserved_from)
        if not m:
            raise PanelCutError(
                f"this panel's period column stacks two frequencies, so the finest cut it can "
                f"express unambiguously is a YEAR, and {reserved_from!r} is not 1 January. See "
                "`_period_keys` for why. Pass the 1 January of the year the cut falls in, and "
                "say in the record that the cut was widened to a year."
            )
        return m.group(1)
    if date_format in PERIOD_FORMATS:
        m = _MONTH_START_RE.fullmatch(reserved_from)
        if not m:
            raise PanelCutError(
                f"this panel is keyed on a {date_format} PERIOD, and the cut {reserved_from!r} "
                "is not the first of a month, so the panel's own units cannot express it. "
                "Rounding would move the cut by up to a month in a direction nobody chose. "
                "Pass the first of the month the cut falls in, and say in the record that the "
                "panel is monthly."
            )
        return f"{m.group(1)}{m.group(2)}" if date_format == "yyyymm" else f"{m.group(1)}-{m.group(2)}"
    raise PanelCutError(
        f"date_format {date_format!r} carries no date, so no cut can be applied to it"
    )


# ---------------------------------------------------------------------------
# the period-format guard: frozen's three layers, in the panel's own units
# ---------------------------------------------------------------------------
def _period_keys(frame: Any, col: str, date_format: str) -> list[str]:
    """The comparison key per row: what is compared, lexically, against the converted cut.

    For `yyyymm`/`yyyy_mm` the key is the value, and every value must be the SAME WIDTH --
    lexical order is chronological order only for fixed-width zero-padded strings, and the
    check is here rather than assumed because it FIRED THE FIRST TIME IT WAS RUN.

    `data/fixtures/hkm_factors.csv.gz` is two panels stacked under one `period` column: 664
    MONTHLY rows keyed `YYYYMM` (`197001`) and 220 QUARTERLY rows keyed `YYYYQ` (`19701` =
    1970 Q1), told apart by the `freq` column. Against a `202401` cut the mixed-width
    comparison happens to give the right answer for every row in this file, and that is a
    coincidence of where the digits fall, not a property anything guarantees. So the panel is
    declared `year_prefix`: the key is the leading four digits, the cut must be 1 January, and
    both frequencies are then compared on the one field they genuinely share.
    """
    vals = [str(v) for v in frame[col].tolist()]
    bad = [v for v in vals if len(v) < 4 or not v[:4].isdigit()]
    if bad:
        raise PanelError(
            f"the period column {col!r} holds values that do not begin with a four-digit "
            f"year, e.g. {bad[:3]}"
        )
    if date_format == "year_prefix":
        return [v[:4] for v in vals]
    widths = {len(v) for v in vals}
    if len(widths) > 1:
        raise PanelError(
            f"the period column {col!r} mixes widths {sorted(widths)}; a lexical comparison "
            "against the cut is only chronological when every period is the same fixed width. "
            "A column that stacks two frequencies is declared `year_prefix`, not `yyyymm`."
        )
    return vals


def _period_filter(frame: Any, col: str, cut: str, date_format: str) -> Any:
    keys = _period_keys(frame, col, date_format)
    return frame[np.array([k < cut for k in keys], dtype=bool)]


def _period_assert(frame: Any, col: str, cut: str, date_format: str) -> None:
    hit = [k for k in _period_keys(frame, col, date_format) if k >= cut]
    if hit:
        raise PanelError(
            f"[HOLDOUT] {len(hit)} row(s) at or after the reserved period {cut} reached the "
            f"path, first {hit[0]}. The reserved slice is read once, on the principal's word, "
            "under a pre-registration (R8)."
        )


def _period_record(
    frame: Any, col: str, cut: str, reserved_from: str, date_format: str
) -> dict[str, Any]:
    vals = _period_keys(frame, col, date_format)
    return {
        "first_session_read": min(vals) if vals else None,
        "last_session_read": max(vals) if vals else None,
        "reserved_from": reserved_from,
        "sessions_read": len(vals),
        "distinct_sessions_read": len(set(vals)),
        "reserved_rows_read": sum(1 for v in vals if v >= cut),
    }


# ---------------------------------------------------------------------------
# reading
# ---------------------------------------------------------------------------
def _read_frame(spec: PanelSpec, path: Path, usecols: Sequence[str] | None) -> Any:
    import pandas as pd

    cols = None if usecols is None else list(usecols)
    dtypes = spec.read_dtypes()
    if cols is not None:
        dtypes = {k: v for k, v in dtypes.items() if k in cols}
    if spec.reader == "csv":
        # `_open_text` (csv_fixture.py:49) is the repository's one gzip-transparent text opener
        # and it declares `encoding="utf-8"` itself; pandas is handed the open handle, so a
        # second `encoding=` here would be the one pandas ignores.
        with _open_text(path, "r") as handle:
            frame = pd.read_csv(handle, usecols=cols, dtype=dtypes or None)
    elif spec.reader == "parquet":
        frame = pd.read_parquet(path, columns=cols)
    else:
        raise PanelError(
            f"{spec.name}: reader {spec.reader!r} produces no table with a date column, so it "
            "cannot be cut. Read it with numpy directly and say in the record why no cut "
            "applies."
        )
    if spec.date_col is not None and spec.date_col not in frame.columns:
        raise PanelError(
            f"{spec.name}: the catalogue declares date_col={spec.date_col!r} and the file's "
            f"header does not carry it (it has {list(frame.columns)[:8]}...). The catalogue is "
            "wrong or the panel changed; `scripts/panel_catalogue_check.py --audit` says which."
        )
    if spec.date_format == "date32":
        # arrow date32 arrives as datetime-like, and `frozen._day_strings` REFUSES a datetime
        # dtype rather than coercing it, because a coerced datetime64 stringifies to
        # '2024-01-01T00:00:00.000000000' and sorts AFTER '2024-01-01'. This is that
        # conversion, done once, at the door, exactly as frozen's own error message prescribes.
        frame = frame.copy()
        frame[spec.date_col] = pd.to_datetime(frame[spec.date_col]).dt.strftime("%Y-%m-%d")
    return frame


# ---------------------------------------------------------------------------
# the result
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class LoadedPanel:
    """One panel read through the door, with the evidence that it was."""

    name: str
    path: Path
    frame: Any
    record: dict[str, Any]
    sha256: str
    status: PanelStatus
    spec: PanelSpec

    def windows_update(self, existing: Mapping[str, Any]) -> dict[str, Any]:
        """Merge this read's six window keys INTO a runner's own `"windows"` block.

        `run_d555:848-850` writes a hand-built `"windows"` block whose keys are `primary`,
        `long`, `reserved_from`, `sessions_primary`, `sessions_long`, `month_ends` -- and only
        `reserved_from` overlaps `window_record`'s six. A loader that REPLACED the block would
        delete five keys the runner's own pre-registration names, so this merges, and raises
        rather than overwriting when a key it owns already holds a different value: two panels
        cut on two different dates inside one artefact is a defect, not a merge.
        """
        out = dict(existing)
        for key in WINDOW_KEYS:
            value = self.record[key]
            if key in out and out[key] != value:
                raise PanelError(
                    f"windows[{key!r}] is already {out[key]!r} and this read of {self.name!r} "
                    f"would make it {value!r}. Merge reads that share a cut; two different "
                    "cuts in one artefact is a defect, and silently keeping the last one "
                    "would put a window in the record that no read used."
                )
            out[key] = value
        return out


# ---------------------------------------------------------------------------
# the door
# ---------------------------------------------------------------------------
def load_panel(
    name: str,
    *,
    reserved_from: str,
    word: bool = False,
    usecols: Sequence[str] | None = None,
    instruction: str | None = None,
    read_log: Path | str | None = None,
) -> LoadedPanel:
    """Read a catalogued panel with the reserved slice cut off, and record that it was.

    `reserved_from` HAS NO DEFAULT. See the module docstring.

    THE TWO MODES

    * **blocked** (`word=False`, `instruction=None`, the default) -- layer 1 `filter_before`,
      layer 2 `assert_none_at_or_after`, layer 3 `window_record`, in that order, on a frame
      that has never held a reserved row.
    * **opened** (`word=True` and a non-empty `instruction`) -- the panel is read WHOLE, and
      then the blocked read is run again, independently, and the opened frame's rows before the
      cut must equal it. That is `run_d574:106-108`'s three hand-written lines, made free and
      generic: it compares the whole frame rather than `["root","day","close"]`, so a column the
      author did not think to list cannot differ unnoticed. It costs a second read of the file,
      deliberately -- checking a filter with the filter proves only that the filter is
      self-consistent.

    Asking to open WITHOUT the word -- passing an `instruction` while `word` is False -- raises
    `PanelRefused` carrying `frozen.refuse_without_word`'s own message. `word=True` with no
    instruction raises: the principal's words are what makes the opening a record.

    `usecols` must include the date column; a projection that drops it would disarm the guard.
    `read_log`, when given, appends one JSON line per read -- the window record, the digest, the
    instruction and a UTC stamp. It writes nothing by default and has no committed home yet.
    """
    spec = spec_for(name)
    _check_iso_day(reserved_from)
    if not isinstance(word, bool):
        raise PanelError(f"word must be a bool, got {word!r}")

    if spec.date_col is None:
        raise PanelError(
            f"{spec.name} declares no date column (date_format='none'), so a reserved-slice "
            "cut cannot be applied to it and this loader will not pretend otherwise. Nineteen "
            "of the 126 manifest panels are in this class -- sixteen .npz arrays and three "
            "aggregate tables. Read it directly, and say in the record why no cut applies."
        )
    cut = convert_cut(spec.date_format, reserved_from)

    if usecols is not None:
        cols = list(usecols)
        if spec.date_col not in cols:
            raise PanelError(
                f"{spec.name}: usecols={cols} does not include the date column "
                f"{spec.date_col!r}. Projecting it away would leave nothing for the guard to "
                "read, and the read would be unguarded rather than loudly wrong."
            )
        # A wrong cut may be READ -- `run_d555` needs `prev_day` and the ledger needs
        # `published_at_et`. What `wrong_cuts` forbids is being the column the CUT uses, and
        # that is enforced by `PanelSpec.__post_init__` and by the catalogue test, not here.

    path = REPO / spec.path
    status = panel_status(path)
    if status == "absent_unlisted":
        raise PanelAbsent(unlisted_message(path), status=status)
    if status == "absent_listed":
        raise PanelAbsent(absent_reason(path.name), status=status)

    entry = manifest_entry(path)
    if entry is None:  # pragma: no cover - status would have been absent_unlisted
        raise PanelError(f"{spec.name}: no manifest row for {spec.path}")
    digest = sha256_file(path, text_normalise=False)
    if digest != entry["sha256"]:
        raise PanelDigestError(
            f"{spec.path} hashes to {digest} and data/data_manifest.json records "
            f"{entry['sha256']}. A changed panel is a study whose numbers may have moved "
            "underneath it -- the event D70 committed the bytes to make visible. Rebuild the "
            "manifest deliberately or recover the file: "
            f"`git cat-file blob {entry.get('git_blob')} > {spec.path}`."
        )

    opening = instruction is not None
    if opening and not word:
        said: list[str] = []
        refuse_without_word(False, f"the reserved slice of {spec.name} from {reserved_from}", log=said.append)
        raise PanelRefused(said[0])
    if word and not (isinstance(instruction, str) and instruction.strip()):
        raise PanelError(
            "instruction must be the principal's words, verbatim, with a date. An opening "
            "whose reason is not recorded is not a record of anything (frozen.open_once)."
        )

    is_period = spec.date_format in PERIOD_FORMATS
    blocked = _read_frame(spec, path, usecols)
    if is_period:
        blocked_frame = _period_filter(blocked, spec.date_col, cut, spec.date_format)
        _period_assert(blocked_frame, spec.date_col, cut, spec.date_format)
        blocked_record = _period_record(
            blocked_frame, spec.date_col, cut, reserved_from, spec.date_format
        )
    else:
        blocked_frame = filter_before(blocked, spec.date_col, cut)
        assert_none_at_or_after(blocked_frame, spec.date_col, cut)
        blocked_record = window_record(blocked_frame, spec.date_col, cut)

    if not word:
        frame, record = blocked_frame, blocked_record
    else:
        opened = _read_frame(spec, path, usecols)
        in_sample = (
            _period_filter(opened, spec.date_col, cut, spec.date_format)
            if is_period
            else filter_before(opened, spec.date_col, cut)
        )
        left = in_sample.reset_index(drop=True)
        right = blocked_frame.reset_index(drop=True)
        if not left.equals(right):
            raise PanelError(
                f"[OPEN] {spec.name}: the opened frame's rows before {cut} ({len(left)}) do not "
                f"equal the blocked loader's ({len(right)}). The opened read must contain the "
                "blocked one exactly -- if it does not, the two reads are not of the same "
                "object and neither number means what it says (run_d574:106-108)."
            )
        frame = opened
        record = (
            _period_record(opened, spec.date_col, cut, reserved_from, spec.date_format)
            if is_period
            else window_record(opened, spec.date_col, cut)
        )

    full = dict(record)
    full.update(
        {
            "panel": spec.name,
            "path": spec.path,
            "date_col": spec.date_col,
            "date_format": spec.date_format,
            "cut_applied": cut,
            "rows_read": int(len(frame)),
            "sha256": digest,
            "opened_on_the_word": bool(word),
            "status": status,
        }
    )

    if read_log is not None:
        line = dict(full)
        line["instruction"] = instruction
        line["read_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        log_path = Path(read_log)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8", newline="\n") as handle:
            handle.write(canonical_json(line) + "\n")

    return LoadedPanel(
        name=spec.name,
        path=path,
        frame=frame,
        record=full,
        sha256=digest,
        status=status,
        spec=spec,
    )
