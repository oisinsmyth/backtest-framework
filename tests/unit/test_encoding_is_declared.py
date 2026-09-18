"""Text IO in `scripts/` states its encoding, and the count that does not may only fall (D543).

313 tracked runners do text IO without ever passing `encoding=`, so their default comes from
the platform — UTF-8 on the Linux runner, cp1252 on the Windows machine this repository is
written on. Same code, different bytes, and nothing declared which was intended.

**It has not bitten, and that is measured rather than assumed.** Of the no-`encoding=` call
sites, zero were found to touch a non-ASCII byte: 716 of them read or write `json.dumps`
output, `ensure_ascii` is never set to `False` anywhere in the repository, and no tracked
`.json` file contains a non-ASCII byte. So this is a prophylactic gap, and a ratchet is the
honest instrument for a prophylactic gap — the existing sites are frozen research runners and
are not worth editing, but a NEW one should not be free.

WHY THIS IS A TEST AND NOT A LINT RULE
--------------------------------------
The review prescribed ruff's `PLW1514` (unspecified-encoding). Two problems, both measured:

1. **It is a preview rule.** `ruff check scripts --select PLW1514` prints
   `warning: Selection PLW1514 has no effect because preview is not enabled` and checks
   nothing — a gate that cannot fire. Reaching it means enabling a rule set that changes
   between ruff versions, which is the exact failure `pyproject.toml`'s own comment records
   for leaving `select` unset.
2. **It sees about a ninth of the surface.** With `--preview` it reports 121 sites against the
   1,126 counted here, because it only recognises `read_text`/`write_text` on a syntactically
   visible `Path(...)` receiver and does not cover `pandas.read_csv`/`to_csv` or `gzip.open`
   at all.

So the rule lives here, where its scope is this project's to state.
"""

import ast
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]

# Bare-name calls that open a path.
PATH_OPENERS = {"open"}
# Method calls that read or write a path's text.
TEXT_METHODS = {"read_text", "write_text", "open", "read_csv", "to_csv"}

# The ceiling, recorded on 2026-09-18. IT MAY FALL AND NEVER RISE. Not a target: the sites are
# in frozen runners and D543 declines to edit evidence for tidiness.
CEILING = 1126

# A floor, because this scans a DISCOVERED set and an empty scan satisfies a ceiling silently.
# Four of seven count gates in this repository once passed on an empty match, and the failure
# mode is indistinguishable from a pass. If the count falls below this, read the scan before
# celebrating.
FLOOR = 900

MINIMUM_RUNNERS = 500


def _tracked_runners() -> list[Path]:
    """Tracked `scripts/*.py`, filtered to what is on disk.

    `git ls-files` reports the INDEX. A path staged for deletion but not yet committed is in
    the index and absent from the worktree, and reading it raises — the principal routinely has
    several in flight, and the first version of D542's class scan crashed on exactly that.
    """
    listed = subprocess.run(
        ["git", "ls-files", "scripts/*.py"], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.split()
    return [REPO / rel for rel in listed if (REPO / rel).exists()]


def _is_binary_mode(call: ast.Call) -> bool:
    """`open(p, "rb")` has no encoding to declare, and counting it would be noise.

    `gzip.open` is the one whose DEFAULT is binary — `"rb"`, not `"r"` — so an unannotated
    `gzip.open(p)` has no encoding to declare either. Getting that backwards inflated the
    count by 25 before it was caught, and an inflated ceiling is a ratchet with slack in it.
    """
    mode = None
    if len(call.args) >= 2 and isinstance(call.args[1], ast.Constant):
        mode = call.args[1].value
    for kw in call.keywords:
        if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
            mode = kw.value.value

    is_gzip = (
        isinstance(call.func, ast.Attribute)
        and call.func.attr == "open"
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id == "gzip"
    )
    if mode is None:
        return is_gzip
    return isinstance(mode, str) and "b" in mode


def _undeclared_sites(source: str) -> list[tuple[int, str]]:
    """(line, callee) for every text-IO call that passes no `encoding=`.

    `csv.reader`, `csv.writer`, `csv.DictReader` and `csv.DictWriter` are deliberately NOT
    counted. They take a file OBJECT, not a path, and have no `encoding` parameter — counting
    them would double-count the `open()` that produced the object and would make the ceiling
    unreachable by any amount of correct work.
    """
    found: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            name = node.func.id
            if name not in PATH_OPENERS:
                continue
        elif isinstance(node.func, ast.Attribute):
            name = node.func.attr
            if name not in TEXT_METHODS:
                continue
        else:
            continue
        if _is_binary_mode(node):
            continue
        if any(kw.arg == "encoding" for kw in node.keywords):
            continue
        found.append((node.lineno, name))
    return found


def _count() -> tuple[int, int]:
    """(call sites, files carrying at least one) across the tracked runners."""
    sites = 0
    files = 0
    for path in _tracked_runners():
        hits = _undeclared_sites(path.read_text(encoding="utf-8"))
        sites += len(hits)
        files += 1 if hits else 0
    return sites, files


@pytest.fixture(scope="module")
def counted() -> tuple[int, int]:
    return _count()


def test_the_scan_finds_the_runners_it_is_meant_to_read(counted):
    """The input, before the number. A ratchet over an empty set is a green light."""
    runners = _tracked_runners()
    assert len(runners) >= MINIMUM_RUNNERS, (
        f"only {len(runners)} tracked runner(s) found; the scan has lost its input rather than "
        f"the repository having lost its scripts"
    )


def test_undeclared_encoding_may_fall_and_never_rise(counted):
    sites, files = counted
    assert sites <= CEILING, (
        f"{sites} text-IO call(s) in scripts/ pass no encoding=, above the recorded ceiling of "
        f"{CEILING}. A NEW one is not free: pass encoding='utf-8' explicitly. The existing ones "
        f"are frozen research runners and D543 declines to edit them."
    )
    assert sites >= FLOOR, (
        f"{sites} is below the floor of {FLOOR}. Either {CEILING - sites} sites were genuinely "
        f"fixed — in which case lower CEILING to {sites} and say so in a record — or the scan "
        f"stopped seeing its input, which looks identical from here."
    )


def test_the_ratchet_fires_on_one_more_undeclared_call(tmp_path):
    """Break what the assertion READS — the count — not its name.

    A ceiling that no realistic input can exceed is a gate that cannot fire, and this file's
    whole claim is that a new runner cannot add silently.
    """
    module = tmp_path / "new_runner.py"
    module.write_text(
        "from pathlib import Path\n"
        "def go(p):\n"
        "    return Path(p).read_text()\n",
        encoding="utf-8",
    )
    hits = _undeclared_sites(module.read_text(encoding="utf-8"))
    assert hits == [(3, "read_text")]

    declared = tmp_path / "good_runner.py"
    declared.write_text(
        "from pathlib import Path\n"
        "def go(p):\n"
        "    return Path(p).read_text(encoding='utf-8')\n",
        encoding="utf-8",
    )
    assert _undeclared_sites(declared.read_text(encoding="utf-8")) == []


def test_binary_mode_is_not_counted():
    """`open(p, 'rb')` has no encoding to declare. Counting it would put a floor under the
    ceiling that no amount of correct work could reach."""
    assert _undeclared_sites("open('x', 'rb')\n") == []
    assert _undeclared_sites("open('x', mode='wb')\n") == []
    assert _undeclared_sites("open('x')\n") == [(1, "open")]
    assert _undeclared_sites("open('x', 'w')\n") == [(1, "open")]

    # `gzip.open` is the exception: its default is "rb", where builtin `open`'s is "r".
    assert _undeclared_sites("import gzip\ngzip.open('x')\n") == []
    assert _undeclared_sites("import gzip\ngzip.open('x', 'rt')\n") == [(2, "open")]
    # As it happens no runner relies on the default -- the count is 1,126 either way -- so this
    # guard is here for correctness rather than for the number it produces today.


def test_csv_readers_are_not_counted():
    """They take a file object, not a path, and have no `encoding` parameter. Counting them
    would double-count the `open()` above them — the category error that made a naive census
    report 1,180 where the remediable surface is 1,126."""
    assert _undeclared_sites("import csv\ncsv.reader(f)\n") == []
    assert _undeclared_sites("import csv\ncsv.DictWriter(f, [])\n") == []


def test_every_tracked_file_is_utf8_or_declared_binary():
    """The class behind B18, not the six instances (D543).

    `.gitattributes` opens with `* text=auto eol=lf`. `text=auto` is CONTENT DETECTION, not a
    declaration, and git's heuristic is "does it contain NUL" — so a cp1252 log with no NULs is
    classified text and line-ending-normalised by a tool that cannot read it.

    Six tracked files are not valid UTF-8 and are now named `binary` individually. A seventh
    would arrive silently, which is what this catches. It asserts the PROPERTY (not UTF-8 ⇒
    declared binary) rather than the list, so the right fix for a new one is to declare it, not
    to edit a number here.
    """
    listed = subprocess.run(
        ["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.split("\n")
    paths = [REPO / rel for rel in listed if rel and (REPO / rel).exists()]
    assert len(paths) > 2000, "the scan lost its input rather than the repository losing files"

    undecodable = []
    for path in paths:
        try:
            path.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            undecodable.append(path.relative_to(REPO).as_posix())

    if not undecodable:  # pragma: no cover - six exist today
        return
    attrs = subprocess.run(
        ["git", "check-attr", "binary", "--", *undecodable],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    undeclared = [
        rel for rel in undecodable if f"{rel}: binary: set" not in attrs
    ]
    assert not undeclared, (
        f"these tracked files are not valid UTF-8 and `.gitattributes` still calls them text, "
        f"so git will line-ending-normalise bytes it cannot read: {undeclared}"
    )


def test_the_binary_declaration_gate_can_fail(tmp_path):
    """Break what the assertion reads. A file that is not UTF-8 and not declared must fail.

    Run in a sandbox repository rather than by editing `.gitattributes` here, so the gate is
    proved live without the proof itself touching tracked state.
    """
    sandbox = tmp_path / "repo"
    (sandbox / "data").mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=sandbox, check=True)
    (sandbox / ".gitattributes").write_text("* text=auto eol=lf\n", encoding="utf-8")
    # 0x97 is an em dash in cp1252 and an invalid UTF-8 start byte. No NULs, so git's
    # `text=auto` heuristic calls it text -- which is precisely the case B18 is about.
    (sandbox / "data" / "console.log").write_bytes(b"symbol  \x97 YES\r\n")
    subprocess.run(["git", "add", "-A"], cwd=sandbox, check=True)

    with pytest.raises(UnicodeDecodeError):
        (sandbox / "data" / "console.log").read_bytes().decode("utf-8")
    attrs = subprocess.run(
        ["git", "check-attr", "binary", "--", "data/console.log"],
        cwd=sandbox,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert "data/console.log: binary: set" not in attrs, (
        "git now declares an undeclared non-UTF-8 file binary on its own; D543's reason for "
        "naming the six individually no longer holds"
    )


def test_json_is_why_this_has_never_bitten():
    """The measured reason the ceiling is a ratchet and not an emergency.

    `json.dumps` escapes non-ASCII by default, so a runner that writes JSON through an
    undeclared encoding still writes ASCII. If any runner ever passes `ensure_ascii=False`,
    that argument stops holding and the 313 files become a live divergence rather than a
    latent one — so the absence is asserted rather than remembered.
    """
    offenders = []
    for path in _tracked_runners():
        if "ensure_ascii" in path.read_text(encoding="utf-8"):
            offenders.append(path.relative_to(REPO).as_posix())
    assert not offenders, (
        f"these runners set ensure_ascii, so their JSON output may carry non-ASCII bytes "
        f"through an undeclared encoding: {offenders}"
    )
