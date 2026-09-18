"""Every tracked `.json` parses, or is named here with a reason (D546).

`docs/decisions/D542-RESULT-two-predictions-falsified-and-a-verdict-that-flipped.md:201` wrote,
about two saved HTTP 429 error pages found during Lane 6's artifact census:

    A tracked JSON that does not parse should fail a test, and none does.

None did. This is that test. It was written three lanes later, which is itself worth recording:
naming a hole in a committed record is not the same act as closing it, and the sentence sat
there being true.

WHAT IT COSTS
-------------
813 tracked files, 119 MB, about one second. `json.loads` is given BYTES rather than decoded
text so that an encoding failure counts as a parse failure too — a `data/*.json` that is not
valid UTF-8 is as unusable as one that is not valid JSON, and reading it as text first would
raise a different exception from a different line.

WHY THE ALLOW-LIST IS RE-DERIVED AND NOT TRUSTED
------------------------------------------------
`data/D3_wb_2018.json` and `data/D3_wb_2019.json` are 117 bytes each of
`<html><body><h1>429 Too Many Requests</h1>`. Nothing in the tree reads them. D542 handed them
to the principal rather than deleting them, because `data/` is evidence and retirement is
written, not quiet — so they are exempted here rather than fixed.

An exemption that outlives its subject is worse than no exemption: it grants amnesty to a path
that no longer needs it, and nothing ever says so. So each allowed path must still EXIST and
still FAIL to parse. Refetch the data, or delete the files, and this gate reddens and asks for
the list to be edited. That is the `--check` discipline from Lane 6's drawdown labeller: derive
the marker from the values rather than believing the marker.
"""

import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# Tracked, unparseable, and deliberately kept. Path -> why it is here and who owns removing it.
ALLOWED = {
    "data/D3_wb_2018.json": (
        "saved HTTP 429 error page, 117 bytes, read by nothing (D542 RESULT). Retirement is the "
        "principal's call; data/ is evidence."
    ),
    "data/D3_wb_2019.json": (
        "saved HTTP 429 error page, 117 bytes, read by nothing (D542 RESULT). Retirement is the "
        "principal's call; data/ is evidence."
    ),
}

# A floor, because a scan that has lost its input reports zero failures and looks like a pass.
MINIMUM_FILES = 700


def _tracked_json() -> list[str]:
    """Tracked `*.json` as posix-relative paths, filtered to what is on disk.

    `git ls-files` reports the INDEX, so a file staged for deletion is listed and absent. The
    principal routinely has several in flight — two were staged for deletion while this gate was
    being written — and reading one raises before any assertion is reached.
    """
    listed = subprocess.run(
        ["git", "ls-files", "*.json"], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.split()
    return [rel for rel in listed if (REPO / rel).exists()]


def _parse_failure(path: Path) -> str | None:
    """The reason `path` is not usable JSON, or None if it parses.

    Bytes, not text: an encoding failure and a syntax failure are both "this artifact cannot be
    read", and the caller should not have to catch two exception types from two layers.
    """
    try:
        json.loads(path.read_bytes())
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return f"{type(exc).__name__}: {exc}"
    return None


def test_the_scan_finds_the_artifacts_it_is_meant_to_read():
    """The input, before the verdict."""
    tracked = _tracked_json()
    assert len(tracked) >= MINIMUM_FILES, (
        f"only {len(tracked)} tracked .json file(s) found; the scan has lost its input rather "
        f"than the repository having lost its artifacts. A census of zero reports no failures."
    )


def test_every_tracked_json_parses():
    failures = {}
    for rel in _tracked_json():
        if rel in ALLOWED:
            continue
        reason = _parse_failure(REPO / rel)
        if reason is not None:
            failures[rel] = reason
    assert not failures, (
        f"{len(failures)} tracked JSON artifact(s) do not parse: {failures}. A committed "
        f"artifact that cannot be read is not evidence of anything; the two that prompted this "
        f"gate were saved HTTP error pages that had been in the tree for days. Refetch it, or "
        f"name it in ALLOWED with the reason and whose call its removal is."
    )


def test_the_allow_list_is_still_earned():
    """Every exemption must still have a subject, and that subject must still be broken.

    Break what the assertion reads: fix either file and this fails, which is the point. An
    exemption nobody revisits is how a repository ends up carrying a permanent excuse for a
    problem it fixed years ago.
    """
    stale = {}
    for rel, reason in ALLOWED.items():
        path = REPO / rel
        if not path.exists():
            stale[rel] = "no longer present, so remove it from ALLOWED"
            continue
        if _parse_failure(path) is None:
            stale[rel] = "parses now, so remove it from ALLOWED; the exemption is spent"
    assert not stale, (
        f"the allow-list has gone stale: {stale}. It is derived from the files, not from "
        f"memory, so this is the gate asking to be edited rather than a regression."
    )


def test_the_gate_fires_on_unreadable_json(tmp_path):
    """Through the same helper the scan uses, on the bytes that are actually there.

    A probe that keys on something other than what the gate reads proves nothing — in Lane 9 one
    of mine matched an LF byte sequence against a CRLF file, broke nothing, and reported the
    case as passing.
    """
    good = tmp_path / "good.json"
    good.write_bytes(b'{"a": 1}')
    assert _parse_failure(good) is None

    # The exact shape of the two allowed files: an HTML error page saved with a .json suffix.
    page = tmp_path / "error.json"
    page.write_bytes(b"<html><body><h1>429 Too Many Requests</h1>\n</body></html>\n")
    assert _parse_failure(page) is not None

    truncated = tmp_path / "truncated.json"
    truncated.write_bytes(b'{"a": 1')
    assert _parse_failure(truncated) is not None

    # Not valid UTF-8: unusable for the same practical reason, caught by the same call.
    mojibake = tmp_path / "cp1252.json"
    mojibake.write_bytes(b'{"note": "\x97"}')
    assert _parse_failure(mojibake) is not None
