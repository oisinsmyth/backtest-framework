"""The frozen-protocol layer: freeze a model, seal a window, open it once — D594.

D85 gives the framework its look-ahead guarantee **by construction**: a fitter
receives training data as `Mapping[str, DataView]` built from the training slice,
so the test window is physically absent from anything it can reach. That guards the
DATA. It cannot guard the three things a researcher carries in their head between
one run and the next:

  * the **parameters** — refitted, nudged, "obviously better" after a look;
  * the **code** — one edited line in the estimator the result was declared on;
  * the **dates** — an evaluation window quietly extended until it pays.

This module is the complementary protocol layer for those three. It is deliberately
small and deliberately loud (D48): every guard raises a named exception rather than
returning a sentinel, and nothing here returns a wrong number in place of an error.

WHAT IT CONSOLIDATES (it replaces no runner; it names conventions this repository
already keeps, so a new runner can import them instead of retyping them):

  * committed provenance as a module constant, not a live git call — `SPEC` in
    `scripts/run_d555_tsmom_replication.py:37` and `run_d574_...:45`, emitted as
    `"spec"` / `"commit"`.  `live_git=True` is available and is never required;
    exactly one runner in the repository does it live
    (`run_d357_holdout_read.py:876`).
  * chunked `sha256(path)` per input (`run_d555:79`), emitted as `fixture_sha256`,
    `strip_sha256`, ...
  * the three-layer reserved-slice guard: filter at the loader, assert after
    loading, record in the artefact — `filter_before`, `assert_none_at_or_after`,
    `window_record`.
  * refusal as a RETURN CODE from the real entry point, so a test can call the real
    function and get a 2 back (`run_d574:99`, `d503_forward_book.do_run`) —
    `refuse_without_word`.
  * `registry.trial_registry.canonical_json` for anything that gets hashed.

And it implements the frozen-protocol clauses pre-registered in the deposit:
`SETTLEMENT_FLOW_LEDGER_PREREG.md` §13A.4 (freeze parameters, stage set and code
hash; no refits during evaluation; any change restarts the count under a NEW frozen
file), §13A.7(2) (the evaluation length is fixed before evaluation starts and not
extended afterwards), §13A.8 control 1 (one look only, the opening is logged with a
timestamp, a second opening is refused) and unit tests 34, 60, 64, 65;
`OPENING_AGENT_STATE_PREREG.md` §12A control 1 and unit tests 18, 20;
`INDEX_REWEIGHT_FLOW_PREREG.md` §11 (`FROZEN_2027.json`).

THIS MODULE CHOOSES NO SEAL DATE, AND THE OMISSION IS THE POINT
--------------------------------------------------------------
The deposit documents seal 2025-03-01 → 2026-09-18. This repository's futures
holdout is 2024-01-01 onward (`RESERVED_FROM`, defined once at `run_d555:43` and
imported by seven runners). Those are two different windows over two different
programmes, and reconciling them is the principal's open decision, not a default a
library gets to pick. So `SealedWindow` takes both dates explicitly and has no
defaults, `filter_before` and friends take `reserved_from` as an argument, and
every test in this module's suite uses synthetic windows. Importing this module can
never silently change which slice a runner reads.

THE NEWLINE PIN (D550/D551)
---------------------------
Any value that is a hash of serialised bytes is a function of the writer's newline
handling. `save_events_json` used `Path.write_text`, so one fixture froze to two
different snapshot ids depending on whose machine ran it. The rule here:

  * **code is text and is LF-pinned before hashing** — CRLF and lone CR are
    normalised to LF, so a checkout with `core.autocrlf=true` and one with
    `core.autocrlf=input` agree;
  * **a fixture is hashed as the bytes on disk** — it is `.csv.gz`, where
    "normalising a newline" is corruption, and raw bytes is what `run_d555:79`
    already does, so every `fixture_sha256` already published still reproduces;
  * **every file this module writes is opened with `newline="\\n"`** and
    `encoding="utf-8"`, never `Path.write_text`.

`tests/golden/test_frozen_ledger.hand.txt` is the arithmetic: the same three bytes
on disk hash to 0263... as text and 679e... as binary.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256 as _sha256
from pathlib import Path
from typing import Any

import numpy as np

from backtest_framework.registry.trial_registry import canonical_json

__all__ = [
    "SCHEMA",
    "OPEN_SCHEMA",
    "CHUNK",
    "FrozenError",
    "FrozenExistsError",
    "FrozenDriftError",
    "AlreadyOpenedError",
    "VaultGuardError",
    "ReservedSliceError",
    "FileDigest",
    "FrozenRecord",
    "OpenRecord",
    "SealedWindow",
    "sha256_bytes",
    "sha256_file",
    "normalise_newlines",
    "freeze",
    "load_frozen",
    "assert_frozen",
    "assert_evaluation_length",
    "filter_before",
    "assert_none_at_or_after",
    "window_record",
    "open_once",
    "refuse_without_word",
]

SCHEMA = "frozen/1"
OPEN_SCHEMA = "open/1"
CHUNK = 1 << 20  # 1 MiB, as run_d555:79

_NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")
_DAY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")

_REFUSAL = (
    "REFUSED: --run reads {what}; "
    "re-run with --principals-word only on the principal's word."
)


# ---------------------------------------------------------------------------
# errors — named, because a protocol breach must not arrive as a ValueError
# from three frames down (D48)
# ---------------------------------------------------------------------------
class FrozenError(Exception):
    """The frozen protocol was used incorrectly, or its inputs are unusable."""


class FrozenExistsError(FrozenError):
    """A frozen file already exists and would have been overwritten.

    Ledger §13A.4: *"Any change restarts the count at N = 0 under a new frozen
    file."* Overwriting is how a restart gets hidden, so it is refused.
    """


class FrozenDriftError(FrozenError):
    """What is on disk now is not what was frozen (ledger unit tests 34 and 60)."""


class AlreadyOpenedError(FrozenError):
    """The sealed window was already opened for this model (unit tests 65 / 20)."""


class VaultGuardError(FrozenError):
    """An opening was attempted without a valid frozen model (unit tests 64 / 18)."""


class ReservedSliceError(FrozenError, AssertionError):
    """A row at or after the reserved date reached code that must not see it.

    It subclasses `AssertionError` as well as `FrozenError` on purpose: the seven
    runners that carry this guard today write `raise AssertionError(...)`, and
    `expect_raise` (`scripts/stage0_d581_gamma_close.py:39`) catches
    `AssertionError`. A runner can adopt this class without its own self-test
    quietly ceasing to catch the raise.
    """


# ---------------------------------------------------------------------------
# hashing
# ---------------------------------------------------------------------------
def normalise_newlines(b: bytes) -> bytes:
    """CRLF and lone CR to LF. The one transform applied before hashing text."""
    return b.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def sha256_bytes(b: bytes) -> str:
    """sha256 of exactly these bytes. No normalisation, no encoding step."""
    if not isinstance(b, (bytes, bytearray, memoryview)):
        raise FrozenError(f"sha256_bytes takes bytes, not {type(b).__name__}")
    return _sha256(bytes(b)).hexdigest()


def sha256_file(
    path: str | Path, *, text_normalise: bool = True, chunk_size: int = CHUNK
) -> str:
    """sha256 of a file, read in `chunk_size` chunks (run_d555:79).

    `text_normalise=True` (the default, and what `freeze` uses for CODE) hashes the
    LF-pinned bytes, so the digest is a fact about the file's content rather than
    about the checkout's newline policy (D551). `text_normalise=False` (what
    `freeze` uses for FIXTURES) hashes the bytes on disk unchanged, and is
    bit-identical to the chunked loop already published as `fixture_sha256`.

    A CRLF straddling a chunk boundary is handled by carrying the trailing `\\r`
    into the next chunk; `tests/property/test_frozen_property.py` quantifies over
    chunk sizes and byte strings to show the chunked digest equals the
    whole-buffer one.
    """
    p = Path(path)
    if chunk_size < 1:
        raise FrozenError(f"chunk_size must be >= 1, got {chunk_size}")
    if not p.is_file():
        raise FrozenError(f"not a file: {p}")
    h = _sha256()
    pending = b""
    with open(p, "rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            if not text_normalise:
                h.update(chunk)
                continue
            buf = pending + chunk
            if buf.endswith(b"\r"):
                # may be the first half of a CRLF split across the boundary
                pending, buf = b"\r", buf[:-1]
            else:
                pending = b""
            h.update(normalise_newlines(buf))
    if pending:
        h.update(normalise_newlines(pending))  # a lone trailing CR is a line end
    return h.hexdigest()


# ---------------------------------------------------------------------------
# the frozen record
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class FileDigest:
    """One frozen file. `name` is the identity; `path` is where this machine kept it."""

    name: str
    path: str
    sha256: str


@dataclass(frozen=True)
class FrozenRecord:
    """A frozen model: parameters, code digests, fixture digests, evaluation length.

    `content_sha256` is the record's identity and covers exactly what was frozen —
    schema, name, params, each file's BASENAME and digest, evaluation_days, spec and
    instruction. It excludes `frozen_utc` (or the record would have no stable
    identity), the derived digests, `git_head` (live and machine-dependent) and each
    file's `path` (a fact about one machine — D551's whole lesson).
    """

    schema: str
    name: str
    frozen_utc: str
    params: dict[str, Any]
    params_sha256: str
    code: tuple[FileDigest, ...]
    fixtures: tuple[FileDigest, ...]
    evaluation_days: int | None
    spec: str | None
    instruction: str | None
    git_head: str | None
    content_sha256: str
    path: Path | None = None


def _identity_payload(
    *,
    name: str,
    params: Mapping[str, Any],
    code: Sequence[FileDigest],
    fixtures: Sequence[FileDigest],
    evaluation_days: int | None,
    spec: str | None,
    instruction: str | None,
) -> str:
    return canonical_json(
        {
            "schema": SCHEMA,
            "name": name,
            "params": dict(params),
            "code": [{"name": d.name, "sha256": d.sha256} for d in code],
            "fixtures": [{"name": d.name, "sha256": d.sha256} for d in fixtures],
            "evaluation_days": evaluation_days,
            "spec": spec,
            "instruction": instruction,
        }
    )


def _digest_files(
    paths: Iterable[str | Path], *, text_normalise: bool, kind: str
) -> tuple[FileDigest, ...]:
    out: list[FileDigest] = []
    seen: dict[str, str] = {}
    for raw in paths:
        p = Path(raw)
        if not p.is_file():
            raise FrozenError(f"{kind} file does not exist: {p}")
        if p.name in seen:
            raise FrozenError(
                f"two {kind} files share the basename {p.name!r} ({seen[p.name]} and "
                f"{p}); the frozen identity is keyed on basenames so that it does not "
                "depend on where this machine kept the files, and a collision is "
                "refused rather than silently resolved"
            )
        seen[p.name] = str(p)
        out.append(
            FileDigest(
                name=p.name,
                path=p.as_posix(),
                sha256=sha256_file(p, text_normalise=text_normalise),
            )
        )
    return tuple(sorted(out, key=lambda d: d.name))


def _validate_params(params: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(params, Mapping):
        raise FrozenError(f"params must be a mapping, not {type(params).__name__}")
    bad = [k for k in params if not isinstance(k, str)]
    if bad:
        raise FrozenError(f"params keys must be strings; got {bad!r}")
    obj = dict(params)
    try:
        canonical_json(obj)
    except TypeError as exc:
        raise FrozenError(f"params are not JSON-serialisable: {exc}") from exc
    return obj


def _git_head(cwd: Path) -> str:
    """The one live git call, behind `live_git=True` and never required."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise FrozenError(
            f"live_git=True but `git rev-parse HEAD` failed in {cwd}: {exc}"
        ) from exc
    head = out.stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise FrozenError(f"`git rev-parse HEAD` returned {head!r}")
    return head


def _write_json(target: Path, obj: Any) -> None:
    """LF-pinned, UTF-8. Never `Path.write_text` — that translates newlines (D551)."""
    text = json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False)
    with open(target, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text + "\n")


def freeze(
    path: str | Path,
    *,
    name: str,
    params: Mapping[str, Any],
    code_paths: Iterable[str | Path],
    fixture_paths: Iterable[str | Path] = (),
    evaluation_days: int | None = None,
    spec_commit: str | None = None,
    instruction: str | None = None,
    live_git: bool = False,
) -> FrozenRecord:
    """Freeze a model to `FROZEN_<name>.json` and refuse to overwrite one.

    `path` is the output DIRECTORY (created if absent), or the target `.json` file
    itself — in which case its basename must already be `FROZEN_<name>.json`, so a
    typo cannot produce a frozen file the loader will never look for.

    Ledger §13A.4 step 2, verbatim: *"store parameter values, stage set and code
    version hash in `results/settlement_flow/FROZEN_<stage>.json`. No refits during
    evaluation."* `evaluation_days` is §13A.7(2)'s pre-computed length, fixed here
    and checked by `assert_evaluation_length`.

    Code is hashed as TEXT (LF-pinned); fixtures are hashed as BINARY. See the
    module docstring and `tests/golden/test_frozen_ledger.hand.txt`.
    """
    if not isinstance(name, str) or not _NAME_RE.fullmatch(name):
        raise FrozenError(
            f"name must match {_NAME_RE.pattern} so it can be a filename; got {name!r}"
        )
    if evaluation_days is not None:
        if isinstance(evaluation_days, bool) or not isinstance(evaluation_days, int):
            raise FrozenError(
                f"evaluation_days must be an int or None, got {evaluation_days!r}"
            )
        if evaluation_days < 1:
            raise FrozenError(f"evaluation_days must be >= 1, got {evaluation_days}")
    for label, val in (("spec_commit", spec_commit), ("instruction", instruction)):
        if val is not None and not isinstance(val, str):
            raise FrozenError(f"{label} must be a string or None, got {val!r}")

    p = Path(path)
    filename = f"FROZEN_{name}.json"
    if p.suffix == ".json":
        if p.name != filename:
            raise FrozenError(
                f"the target file must be named {filename} for name={name!r}, got {p.name}"
            )
        target = p
    else:
        target = p / filename
    # nothing is created on disk until every input has been validated, so a refused
    # freeze leaves no directory behind to be mistaken for a started one
    if target.exists():
        raise FrozenExistsError(
            f"{target} already exists and freeze() will not overwrite it. A parameter, "
            "rule or code change restarts the evaluation count at N = 0 under a NEW "
            "frozen file (ledger 13A.4); delete or rename the old one deliberately."
        )

    obj = _validate_params(params)
    code = _digest_files(code_paths, text_normalise=True, kind="code")
    if not code:
        raise FrozenError("freeze() needs at least one code file; a frozen model with "
                          "no code hash cannot detect a code change")
    fixtures = _digest_files(fixture_paths, text_normalise=False, kind="fixture")
    target.parent.mkdir(parents=True, exist_ok=True)
    head = _git_head(target.parent.resolve()) if live_git else None

    payload = _identity_payload(
        name=name,
        params=obj,
        code=code,
        fixtures=fixtures,
        evaluation_days=evaluation_days,
        spec=spec_commit,
        instruction=instruction,
    )
    rec = FrozenRecord(
        schema=SCHEMA,
        name=name,
        frozen_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        params=obj,
        params_sha256=sha256_bytes(canonical_json(obj).encode("utf-8")),
        code=code,
        fixtures=fixtures,
        evaluation_days=evaluation_days,
        spec=spec_commit,
        instruction=instruction,
        git_head=head,
        content_sha256=sha256_bytes(payload.encode("utf-8")),
        path=target,
    )
    _write_json(target, _record_to_json(rec))
    return rec


def _record_to_json(rec: FrozenRecord) -> dict[str, Any]:
    return {
        "schema": rec.schema,
        "name": rec.name,
        "frozen_utc": rec.frozen_utc,
        "params": rec.params,
        "params_sha256": rec.params_sha256,
        "code": [{"name": d.name, "path": d.path, "sha256": d.sha256} for d in rec.code],
        "fixtures": [
            {"name": d.name, "path": d.path, "sha256": d.sha256} for d in rec.fixtures
        ],
        "evaluation_days": rec.evaluation_days,
        "spec": rec.spec,
        "instruction": rec.instruction,
        "git_head": rec.git_head,
        "content_sha256": rec.content_sha256,
    }


def _files_from_json(rows: Any, kind: str, where: Path) -> tuple[FileDigest, ...]:
    if not isinstance(rows, list):
        raise FrozenDriftError(f"{where}: {kind!r} is not a list")
    out: list[FileDigest] = []
    for row in rows:
        try:
            out.append(
                FileDigest(str(row["name"]), str(row["path"]), str(row["sha256"]))
            )
        except (TypeError, KeyError) as exc:
            raise FrozenDriftError(
                f"{where}: a {kind} entry is missing name/path/sha256: {row!r}"
            ) from exc
    return tuple(out)


def load_frozen(path: str | Path) -> FrozenRecord:
    """Read a frozen file and verify it is internally consistent.

    Both derived digests are recomputed from the stored fields: a frozen file that
    has been hand-edited — the easiest way to "unfreeze" a model — raises
    `FrozenDriftError` here, before any caller reads a parameter out of it. Same
    instrument as `SnapshotIntegrityError` in `data/snapshot_store.py`.
    """
    p = Path(path)
    if not p.is_file():
        raise FrozenError(f"no frozen file at {p}")
    with open(p, encoding="utf-8") as fh:
        try:
            raw = json.load(fh)
        except json.JSONDecodeError as exc:
            raise FrozenDriftError(f"{p} is not valid JSON: {exc}") from exc
    if not isinstance(raw, dict):
        raise FrozenDriftError(f"{p} does not hold a JSON object")
    if raw.get("schema") != SCHEMA:
        raise FrozenDriftError(
            f"{p}: schema is {raw.get('schema')!r}, this module writes {SCHEMA!r}"
        )
    missing = [
        k
        for k in ("name", "frozen_utc", "params", "params_sha256", "code", "fixtures",
                  "evaluation_days", "spec", "instruction", "content_sha256")
        if k not in raw
    ]
    if missing:
        raise FrozenDriftError(f"{p}: frozen file is missing {missing}")
    params = raw["params"]
    if not isinstance(params, dict):
        raise FrozenDriftError(f"{p}: 'params' is not an object")

    rec = FrozenRecord(
        schema=SCHEMA,
        name=str(raw["name"]),
        frozen_utc=str(raw["frozen_utc"]),
        params=params,
        params_sha256=str(raw["params_sha256"]),
        code=_files_from_json(raw["code"], "code", p),
        fixtures=_files_from_json(raw["fixtures"], "fixtures", p),
        evaluation_days=raw["evaluation_days"],
        spec=raw["spec"],
        instruction=raw["instruction"],
        git_head=raw.get("git_head"),
        content_sha256=str(raw["content_sha256"]),
        path=p,
    )
    want_params = sha256_bytes(canonical_json(rec.params).encode("utf-8"))
    if want_params != rec.params_sha256:
        raise FrozenDriftError(
            f"{p}: params_sha256 is {rec.params_sha256} but the stored params hash to "
            f"{want_params} -- the frozen file has been edited"
        )
    want_content = sha256_bytes(
        _identity_payload(
            name=rec.name,
            params=rec.params,
            code=rec.code,
            fixtures=rec.fixtures,
            evaluation_days=rec.evaluation_days,
            spec=rec.spec,
            instruction=rec.instruction,
        ).encode("utf-8")
    )
    if want_content != rec.content_sha256:
        raise FrozenDriftError(
            f"{p}: content_sha256 is {rec.content_sha256} but the stored record hashes "
            f"to {want_content} -- the frozen file has been edited"
        )
    return rec


def _short(value: Any, n: int = 80) -> str:
    s = canonical_json(value) if not isinstance(value, str) else repr(value)
    return s if len(s) <= n else s[: n - 3] + "..."


def _check_files(
    frozen: Sequence[FileDigest],
    supplied: Iterable[str | Path],
    *,
    kind: str,
    text_normalise: bool,
    where: Path,
) -> None:
    by_name: dict[str, Path] = {}
    for raw in supplied:
        q = Path(raw)
        if q.name in by_name:
            raise FrozenError(
                f"two supplied {kind} paths share the basename {q.name!r}"
            )
        by_name[q.name] = q
    frozen_names = {d.name for d in frozen}
    for d in sorted(frozen, key=lambda x: x.name):
        found_path = by_name.get(d.name)
        if found_path is None:
            raise FrozenDriftError(
                f"{where}: the frozen {kind} {d.name!r} was not supplied to "
                f"assert_frozen (expected sha256 {d.sha256})"
            )
        if not found_path.is_file():
            raise FrozenDriftError(
                f"{where}: the frozen {kind} {d.name!r} is missing from disk at "
                f"{found_path} (expected sha256 {d.sha256})"
            )
        found = sha256_file(found_path, text_normalise=text_normalise)
        if found != d.sha256:
            raise FrozenDriftError(
                f"{where}: {kind} {d.name!r} DRIFTED -- frozen sha256 {d.sha256}, "
                f"found {found} at {found_path}. Ledger 13A.4: no refits or code "
                "changes during evaluation; a change restarts the count under a new "
                "frozen file."
            )
    extras = sorted(set(by_name) - frozen_names)
    if extras:
        raise FrozenDriftError(
            f"{where}: {kind} {extras[0]!r} was supplied but is not in the frozen "
            f"record (frozen {kind}: {sorted(frozen_names)})"
        )


def assert_frozen(
    path: str | Path,
    *,
    params: Mapping[str, Any],
    code_paths: Iterable[str | Path],
    fixture_paths: Iterable[str | Path] = (),
) -> None:
    """Refuse to proceed unless params, code and fixtures still match the freeze.

    Ledger unit test 34: *"Frozen-protocol guard: evaluation code refuses to run if
    the parameters differ from `FROZEN_<stage>.json`."*

    The FIRST drifted item is named, in a fixed order — **params, then code, then
    fixtures**, each in sorted order — so the message is deterministic and, when
    both a parameter and a file have moved, it reports the parameter, which is the
    thing a human tuned. Every message carries expected and found.
    """
    rec = load_frozen(path)
    where = rec.path if rec.path is not None else Path(path)
    now = _validate_params(params)

    for key in sorted(set(rec.params) | set(now)):
        if key not in now:
            raise FrozenDriftError(
                f"{where}: the frozen param {key!r} is absent from the params supplied "
                f"(frozen value {_short(rec.params[key])})"
            )
        if key not in rec.params:
            raise FrozenDriftError(
                f"{where}: param {key!r} was supplied but is not in the frozen record "
                f"(supplied value {_short(now[key])}); frozen keys "
                f"{sorted(rec.params)}"
            )
        want, got = rec.params[key], now[key]
        if canonical_json(want) != canonical_json(got):
            raise FrozenDriftError(
                f"{where}: param {key!r} DRIFTED -- frozen {_short(want)} "
                f"(sha256 {sha256_bytes(canonical_json(want).encode('utf-8'))}), "
                f"found {_short(got)} "
                f"(sha256 {sha256_bytes(canonical_json(got).encode('utf-8'))}). "
                "Ledger 13A.4: no refits during evaluation."
            )

    _check_files(rec.code, code_paths, kind="code", text_normalise=True, where=where)
    _check_files(
        rec.fixtures, fixture_paths, kind="fixture", text_normalise=False, where=where
    )


def assert_evaluation_length(
    path: str | Path, evaluation_days: int | None
) -> None:
    """The evaluation length cannot change once evaluation has started.

    Ledger unit test 60, and §13A.7(2): *"The evaluation length is fixed in
    `FROZEN_<stage>.json` **before** evaluation starts, and not extended
    afterwards."* Extending a window until it pays is the cheapest of all the ways
    to manufacture a result, and it leaves no trace anywhere else.
    """
    rec = load_frozen(path)
    where = rec.path if rec.path is not None else Path(path)
    if rec.evaluation_days != evaluation_days:
        raise FrozenDriftError(
            f"{where}: evaluation_days was frozen at {rec.evaluation_days} and this run "
            f"asks for {evaluation_days}. Ledger 13A.7(2): the evaluation length is "
            "fixed before evaluation starts and not extended afterwards."
        )


# ---------------------------------------------------------------------------
# the sealed window, and the three-layer reserved-slice guard
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SealedWindow:
    """An explicit, inclusive [start, end] window of ISO dates. NO DEFAULTS.

    The deposit seals 2025-03-01 → 2026-09-18; this repository reserves 2024-01-01
    onward. Both dates are always passed in, by the caller, at the call site — see
    the module docstring for why a library must not pick.
    """

    start: str
    end: str

    def __post_init__(self) -> None:
        for label, v in (("start", self.start), ("end", self.end)):
            if not isinstance(v, str):
                raise FrozenError(f"{label} must be an ISO date string, got {v!r}")
            # the regex is not redundant: strptime accepts "2001-3-01", which is a
            # real date but sorts wrongly against the zero-padded days in a fixture,
            # and every comparison in this module is lexical
            if not _DAY_RE.fullmatch(v):
                raise FrozenError(
                    f"{label}={v!r} is not a zero-padded ISO date (YYYY-MM-DD)"
                )
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError as exc:
                raise FrozenError(f"{label}={v!r} is not an ISO date: {exc}") from exc
        if self.start > self.end:
            raise FrozenError(
                f"sealed window is unsorted: start {self.start} > end {self.end}"
            )

    def contains(self, day: str) -> bool:
        """True for a day inside the seal. ISO strings compare correctly lexically."""
        d = _as_day(day)
        return self.start <= d <= self.end

    def as_list(self) -> list[str]:
        return [self.start, self.end]


def _as_day(day: Any) -> str:
    s = day if isinstance(day, str) else str(day)
    if not _DAY_RE.match(s):
        raise FrozenError(f"not an ISO day string: {day!r}")
    return s[:10]


def _day_strings(frame: Any, col: str | None) -> np.ndarray:
    """The day column, as a 1-D array of `YYYY-MM-DD` strings.

    Accepts a pandas DataFrame (with `col`) or any numpy/str sequence (with
    `col=None`). A datetime-like column is REFUSED rather than coerced: `str()` on
    `datetime64[ns]` gives `2024-01-01T00:00:00.000000000`, which compares against
    `"2024-01-01"` as *greater*, so a coercion here would silently let the first
    reserved session through the very guard that exists to stop it.
    """
    seq = frame if col is None else frame[col]
    arr = np.asarray(seq)
    if arr.ndim != 1:
        raise FrozenError(f"expected a 1-D day column, got shape {arr.shape}")
    if arr.size == 0:
        return np.array([], dtype="U10")
    if arr.dtype.kind in "Mmfiub":
        raise FrozenError(
            f"the day column has dtype {arr.dtype}; this guard compares ISO date "
            "STRINGS (the convention every fixture here uses). Convert with "
            "`.dt.strftime('%Y-%m-%d')` at the call site rather than letting this "
            "function coerce -- a coerced datetime64 stringifies to "
            "'2024-01-01T00:00:00.000000000', which sorts AFTER '2024-01-01'."
        )
    vals = [str(v) for v in arr]
    bad = [v for v in vals if not _DAY_RE.match(v)]
    if bad:
        raise FrozenError(f"day values are not ISO dates, e.g. {bad[:3]}")
    return np.array([v[:10] for v in vals], dtype="U10")


def filter_before(frame: Any, col: str | None, reserved_from: str) -> Any:
    """Layer 1 of the guard: drop every row at or after `reserved_from` AT THE LOADER.

    `df = df[df["day"] < RESERVED_FROM]`, as run_d574:106 — made a named function so
    the eighth runner to need it imports rather than retypes it. Returns the same
    kind of object it was given: a DataFrame stays a DataFrame (index untouched, so
    `.reset_index(drop=True)` remains the caller's call), an ndarray stays an
    ndarray, any other sequence comes back as a list.
    """
    cut = _as_day(reserved_from)
    days = _day_strings(frame, col)
    mask = days < cut
    if col is None:
        if isinstance(frame, np.ndarray):
            return frame[mask]
        return [v for v, m in zip(frame, mask) if m]
    return frame[mask]


def assert_none_at_or_after(frame: Any, col: str | None, reserved_from: str) -> None:
    """Layer 2: assert AFTER loading that nothing reserved survived.

    Layer 1 and layer 2 are deliberately not the same code path — filtering and
    checking with one expression proves only that the expression is self-consistent.
    Raises `ReservedSliceError`, which is also an `AssertionError`.
    """
    cut = _as_day(reserved_from)
    days = _day_strings(frame, col)
    hit = days >= cut
    n = int(hit.sum())
    if n:
        first = str(days[hit][0])
        raise ReservedSliceError(
            f"[HOLDOUT] {n} row(s) at or after the reserved date {cut} reached the "
            f"path, first {first}. The reserved slice is read once, on the "
            "principal's word, under a pre-registration (R8)."
        )


def window_record(frame: Any, col: str | None, reserved_from: str) -> dict[str, Any]:
    """Layer 3: the `"windows"` block an artefact carries, so the read is on record.

    Shape follows the runners' own (`run_d555` emits `reserved_from`, `run_d558:528`
    emits `last_session_read`): what was read, how much of it, and the date that was
    not crossed. `reserved_rows_read` is reported rather than asserted — the assert
    is layer 2's job, and a record that silently raised would not be a record.
    """
    cut = _as_day(reserved_from)
    days = _day_strings(frame, col)
    n_reserved = int((days >= cut).sum())
    # numpy 2 has no min/max loop for the "<U10" dtype, so this uses Python's, on
    # ISO strings, where lexical order IS chronological order.
    vals: list[str] = days.tolist()
    return {
        "first_session_read": min(vals) if vals else None,
        "last_session_read": max(vals) if vals else None,
        "reserved_from": cut,
        "sessions_read": int(days.size),
        "distinct_sessions_read": int(np.unique(days).size) if days.size else 0,
        "reserved_rows_read": n_reserved,
    }


# ---------------------------------------------------------------------------
# one look only
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class OpenRecord:
    """One logged opening of a sealed window."""

    schema: str
    opened_utc: str
    model: str
    window: list[str]
    instruction: str
    frozen_path: str
    frozen_sha256: str
    frozen_content_sha256: str
    log_path: Path | None = None


def _read_openings(log_path: Path) -> list[dict[str, Any]]:
    if not log_path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    with open(log_path, encoding="utf-8") as fh:
        for i, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise VaultGuardError(
                    f"{log_path}:{i} is not valid JSON ({exc}); the opening log is the "
                    "evidence that the window was opened once, so a damaged log is a "
                    "refusal, not a fresh start"
                ) from exc
            if not isinstance(obj, dict):
                raise VaultGuardError(f"{log_path}:{i} does not hold a JSON object")
            rows.append(obj)
    return rows


def open_once(
    log_path: str | Path,
    *,
    window: SealedWindow,
    model: str,
    instruction: str,
    frozen_path: str | Path,
    params: Mapping[str, Any] | None = None,
    code_paths: Iterable[str | Path] = (),
    fixture_paths: Iterable[str | Path] = (),
) -> OpenRecord:
    """Open a sealed window once, for one model, and log it. A second call refuses.

    Ledger §13A.8 control 1, verbatim: *"The vault is opened once per model, after
    the model has passed every in-sample gate and been frozen (code hash,
    parameters, retained stages, rules) ... The opening is logged with a timestamp.
    A second opening is refused."* Opening §12A control 1 is the same sentence.

    Two guards, in order:

      * the frozen file must exist and load (`load_frozen` re-derives both digests,
        so a hand-edited frozen model is caught here) — else `VaultGuardError`,
        which is unit test 64 / 18's "unless `FROZEN_VAULT.json` exists";
      * if `params` is given, the full `assert_frozen` drift check runs and any
        drift is re-raised as `VaultGuardError` — opening a window against code
        that is not the frozen code is the failure the seal exists to prevent.

    Then the log is read; a prior entry for the same `model` raises
    `AlreadyOpenedError` naming the earlier timestamp (unit test 65 / 20). The log
    is append-only JSON lines, written with `newline="\\n"`.

    `instruction` is recorded verbatim, the convention the forward runners already
    keep (`run_d574:103`).
    """
    if not isinstance(window, SealedWindow):
        raise FrozenError(
            f"window must be a SealedWindow with explicit dates, got {type(window).__name__}"
        )
    if not isinstance(model, str) or not model.strip():
        raise FrozenError("model must be a non-empty string")
    if not isinstance(instruction, str) or not instruction.strip():
        raise FrozenError(
            "instruction must be the principal's words, verbatim, with a date"
        )

    fp = Path(frozen_path)
    if not fp.is_file():
        raise VaultGuardError(
            f"no frozen model at {fp}: the sealed window {window.start}..{window.end} "
            "cannot be opened until the model has been frozen (ledger 13A.8 control 1)"
        )
    try:
        rec = load_frozen(fp)
    except FrozenError as exc:
        raise VaultGuardError(f"the frozen model at {fp} did not load: {exc}") from exc
    if params is not None:
        try:
            assert_frozen(
                fp, params=params, code_paths=code_paths, fixture_paths=fixture_paths
            )
        except FrozenError as exc:
            raise VaultGuardError(
                f"refusing to open {window.start}..{window.end} for {model!r}: {exc}"
            ) from exc

    lp = Path(log_path)
    for row in _read_openings(lp):
        if row.get("model") == model:
            raise AlreadyOpenedError(
                f"the sealed window was already opened for model {model!r} at "
                f"{row.get('opened_utc')} (logged in {lp}). One look only: a second "
                "opening is refused (ledger 13A.8 control 1). A changed model is a "
                "NEW model, with its own frozen file and its own name."
            )

    out = OpenRecord(
        schema=OPEN_SCHEMA,
        opened_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        model=model,
        window=window.as_list(),
        instruction=instruction,
        frozen_path=fp.as_posix(),
        frozen_sha256=sha256_file(fp, text_normalise=True),
        frozen_content_sha256=rec.content_sha256,
        log_path=lp,
    )
    lp.parent.mkdir(parents=True, exist_ok=True)
    line = canonical_json(
        {
            "schema": out.schema,
            "opened_utc": out.opened_utc,
            "model": out.model,
            "window": out.window,
            "instruction": out.instruction,
            "frozen_path": out.frozen_path,
            "frozen_sha256": out.frozen_sha256,
            "frozen_content_sha256": out.frozen_content_sha256,
        }
    )
    with open(lp, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(line + "\n")
    return out


def refuse_without_word(word: bool, what: str, log: Any = print) -> int:
    """Return 2 and print the refusal unless the principal's word was given.

    The shape is `run_d574:99`'s, and the reason it is a RETURN CODE from the real
    entry point rather than a `sys.exit` in `__main__` is that a self-test can then
    call the real function — `run(False, log=lambda *a: None)` — and assert `rc ==
    2`. A refusal proven by reading the source is not proven.
    """
    if not isinstance(word, bool):
        raise FrozenError(f"word must be a bool, got {word!r}")
    if word:
        return 0
    log(_REFUSAL.format(what=what))
    return 2
