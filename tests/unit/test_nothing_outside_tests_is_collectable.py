"""No tracked `.py` outside `tests/` is reachable by pytest's collector (D546).

Seven tracked files matched pytest's DEFAULT `python_files` patterns while living in `data/`,
`scripts/` and `working/`, and all seven matched on the `*_test.py` suffix. On the other side:
158 tracked test files under `tests/`, every one named `test_*.py`, none named `*_test.py`. So
the second default pattern earned this repository nothing and reached into three directories
that hold no tests.

**Collection is import.** Six of the seven were `__main__`-guarded and inert;
`data/A4-filing-text/A4_header_test.py` was not. It fetched from SEC and wrote
`A4_header_rows.json` through a RELATIVE path, so the file landed wherever pytest was invoked.
That is how it was found — a stray artifact in the repository root after a census run during
Lane 8. It is guarded now, and `test_nothing_collectable_fetches_or_writes_at_import` below is
what keeps all seven that way.

`pyproject.toml`'s `testpaths = ["tests"]` already protects the default run; firing this needs
an explicit path or a repo-wide collection. The hazard is real and narrow, and this file says
so rather than inflating it — but the explicit-path half is NOT closed by any pytest setting,
which is why the import-safety assertion exists beside the pattern ones.

WHY THIS READS THE CONFIG INSTEAD OF RESTATING IT
-------------------------------------------------
The fix is one line of `pyproject.toml`, and a line of config is a setting, not a gate — anyone
who does not know what it was for can widen it back. But a gate that hard-codes `["test_*.py"]`
would be a SECOND COPY of the fact, and two copies of one fact drifting apart is what
`README.md` names as this project's most repeated defect. So the patterns are read back out of
`pyproject.toml` with `tomllib`, and the assertions are about what those patterns match.

The subtlest failure is the key being DELETED rather than widened: pytest then falls back to its
defaults silently, and a gate that only compared against a hard-coded narrow list would still
pass. Its absence is asserted first, and separately, so the message names that specific
regression.

WHY NOT RENAME THE OFFENDER
---------------------------
`A4_header_test.py` is cited by name at
`docs/research/Scan-100926/R1-04-filing-text-at-scale.md:645`, and `data/` is evidence — the
same reason D542 handed two unparseable `data/*.json` files to the principal instead of
deleting them. The config change touches no evidence and covers six files a rename would not.
"""

import ast
import fnmatch
import subprocess
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PYPROJECT = REPO / "pyproject.toml"

# What pytest collects when `python_files` is unset. Recorded here as the thing being narrowed
# AWAY from, so the proof below can show the narrowing is doing work.
PYTEST_DEFAULT_PYTHON_FILES = ("test_*.py", "*_test.py")

# A floor, because a pattern list that matches NOTHING satisfies "no offenders outside tests/"
# perfectly. Six gates in this repository have now been found passing on an empty scan, and from
# the outside an empty scan and a clean one are the same green.
MINIMUM_TESTS = 150


def _configured_patterns() -> list[str] | None:
    """`python_files` from `pyproject.toml`, or None if the key is absent."""
    config = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    return config.get("tool", {}).get("pytest", {}).get("ini_options", {}).get("python_files")


def _tracked_python_files() -> list[str]:
    """Tracked `*.py` as posix-relative paths, filtered to what is on disk.

    `git ls-files` reports the INDEX. A path staged for deletion but not yet committed is in the
    index and absent from the worktree; the principal routinely has several in flight, and
    D542's first class scan crashed on exactly that.
    """
    listed = subprocess.run(
        ["git", "ls-files", "*.py"], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.split()
    return [rel for rel in listed if (REPO / rel).exists()]


def _collectable(paths: list[str], patterns: tuple[str, ...] | list[str]) -> list[str]:
    """The subset pytest would collect, matching on BASENAME as pytest itself does."""
    return [rel for rel in paths if any(fnmatch.fnmatch(Path(rel).name, p) for p in patterns)]


def _effective_patterns() -> tuple[str, ...] | list[str]:
    """What pytest would actually use: the configured list, or its defaults if the key is absent.

    `is None` and not `or`. An EMPTY list is a configured value, not a missing one, and folding
    the two together would make the floor test silently pass on `python_files = []` by scanning
    with the defaults — a gate reporting on a configuration the repository does not have.
    """
    patterns = _configured_patterns()
    return PYTEST_DEFAULT_PYTHON_FILES if patterns is None else patterns


# Calls that WRITE or FETCH. A read at import is survivable; these two are not, and they are
# exactly what happened: `A4_header_test.py` fetched from SEC and wrote a relative path while
# pytest was merely collecting it.
WRITING_ATTRS = {"write_text", "write_bytes", "writelines", "to_csv", "to_parquet", "savefig"}
WRITING_FUNCS = {"json.dump", "pickle.dump", "np.save", "np.savez", "numpy.save"}
# `urllib.request.`, not `urllib.` -- `urllib.parse.urlencode` is string work and flagging it
# would be wrong. The limitation this leaves is stated in `_import_time_hazards`.
FETCHING_PREFIXES = ("urllib.request.", "requests.", "socket.", "httpx.")


def _is_main_guard(node: ast.stmt) -> bool:
    return (
        isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and isinstance(node.test.left, ast.Name)
        and node.test.left.id == "__name__"
    )


def _opens_for_writing(call: ast.Call, name: str) -> bool:
    """`open(p)` and `gzip.open(p)` are only hazards in a write mode.

    Same mode-reading care as `test_encoding_is_declared._is_binary_mode`: `gzip.open`'s
    default is "rb" while the builtin's is "r", and both default to reading.
    """
    if name not in {"open", "gzip.open", "io.open"}:
        return False
    mode = None
    if len(call.args) >= 2 and isinstance(call.args[1], ast.Constant):
        mode = call.args[1].value
    for kw in call.keywords:
        if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
            mode = kw.value.value
    return isinstance(mode, str) and any(c in mode for c in "wax+")


def _import_time_hazards(source: str) -> list[tuple[int, str]]:
    """(line, expression) for every write or fetch that runs when the module is IMPORTED.

    Statements inside a `def`, a `class` or an `if __name__ == "__main__":` block do not run on
    import. Not skipping the defs made the first version of this scan report 84-139 "module-level
    calls" per file, nearly all of them inside functions -- a measurement with no signal in it.

    WHAT IT CANNOT SEE, stated rather than discovered later: a fetch behind a local helper.
    `A4_header_test.py` called `get(url)` at module level and `get` wraps `urlopen` inside a
    function, so the network call is invisible here -- what caught that file was its module-level
    WRITE. A syntactic scan reports what is written where it is written; it is a tripwire on the
    two shapes that have actually bitten, not a proof of import-purity.
    """
    hazards: list[tuple[int, str]] = []
    for node in ast.parse(source).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if _is_main_guard(node):
            continue
        for sub in ast.walk(node):
            if not isinstance(sub, ast.Call):
                continue
            name = ast.unparse(sub.func)
            if (
                name.split(".")[-1] in WRITING_ATTRS
                or name in WRITING_FUNCS
                or _opens_for_writing(sub, name)
                or name.startswith(FETCHING_PREFIXES)
            ):
                hazards.append((sub.lineno, ast.unparse(sub)[:80]))
    return hazards


def test_python_files_is_configured():
    """The key's ABSENCE is the regression, not just a wrong value.

    Delete it and pytest silently restores `["test_*.py", "*_test.py"]` — the exact state D546
    closed. A gate that only checked the narrow list against today's tree would pass.
    """
    patterns = _configured_patterns()
    assert patterns is not None, (
        "pyproject.toml's [tool.pytest.ini_options] no longer sets python_files, so pytest has "
        f"fallen back to its defaults {list(PYTEST_DEFAULT_PYTHON_FILES)} and will import "
        "tracked files outside tests/ again. See D546."
    )
    assert patterns, "python_files is set to an empty list; pytest would collect no tests at all"


def test_the_scan_finds_the_tests_it_is_meant_to_read():
    """The input, before the verdict. A gate over an empty set is a green light."""
    patterns = _effective_patterns()
    tracked = _tracked_python_files()
    under_tests = _collectable([r for r in tracked if r.startswith("tests/")], patterns)
    assert len(under_tests) >= MINIMUM_TESTS, (
        f"only {len(under_tests)} tracked test file(s) under tests/ match {list(patterns)}. "
        f"Either the patterns stopped matching this repository's tests (in which case the "
        f"suite is quietly smaller than it looks) or the scan lost its input. Both look "
        f"identical from here, which is why this floor exists."
    )


def test_nothing_outside_tests_matches_the_collection_patterns():
    patterns = _effective_patterns()
    tracked = _tracked_python_files()
    outside = _collectable([r for r in tracked if not r.startswith("tests/")], patterns)
    assert not outside, (
        f"these tracked file(s) live outside tests/ and match {list(patterns)}, so pytest will "
        f"IMPORT them on any repo-wide collection: {outside}. Collection is import, and at "
        f"least one such file has run network fetches and written a relative path at module "
        f"level. Rename it to something the patterns do not match, or narrow the patterns."
    )


def test_the_narrowing_is_still_doing_work():
    """Re-derive the reason for the setting instead of trusting that it had one.

    If every offender is one day renamed or retired, the default patterns become harmless and
    this configuration is cargo. The gate should say so rather than standing guard over nothing
    — the same discipline as re-deriving an allow-list rather than believing it.
    """
    tracked = _tracked_python_files()
    outside = [r for r in tracked if not r.startswith("tests/")]
    would_collect = _collectable(outside, PYTEST_DEFAULT_PYTHON_FILES)
    assert would_collect, (
        "no tracked file outside tests/ matches pytest's DEFAULT python_files any more, so "
        "narrowing the patterns no longer protects anything. That is good news: delete the "
        "setting and this file, or rewrite both to say what they now guard."
    )


def test_the_two_failure_modes_are_distinguishable():
    """A widened list and an emptied one must redden DIFFERENT assertions.

    Break what each assertion reads. A gate whose failures are indistinguishable tells you
    something broke and not what — and the fix for a widened pattern (rename or re-narrow) is
    nothing like the fix for an empty one (the scan has lost its input).
    """
    tracked = _tracked_python_files()
    outside = [r for r in tracked if not r.startswith("tests/")]
    under_tests = [r for r in tracked if r.startswith("tests/")]

    # Widened to pytest's defaults: offenders appear, the floor still holds.
    assert _collectable(outside, PYTEST_DEFAULT_PYTHON_FILES)
    assert len(_collectable(under_tests, PYTEST_DEFAULT_PYTHON_FILES)) >= MINIMUM_TESTS

    # Emptied: no offenders — the offender assertion PASSES — and the floor is what catches it.
    assert _collectable(outside, []) == []
    assert len(_collectable(under_tests, [])) < MINIMUM_TESTS


def test_basename_matching_is_what_pytest_does():
    """`python_files` patterns without a slash match the file's name, not its path.

    Matching the whole relative path instead would make `test_*.py` miss every file in a
    subdirectory, and the offender assertion would pass by seeing nothing.
    """
    assert _collectable(["data/x/A4_header_test.py"], ["*_test.py"]) == ["data/x/A4_header_test.py"]
    assert _collectable(["data/x/A4_header_test.py"], ["test_*.py"]) == []
    assert _collectable(["tests/unit/test_thing.py"], ["test_*.py"]) == ["tests/unit/test_thing.py"]


def test_nothing_collectable_fetches_or_writes_at_import():
    """The invariant underneath the config change, and the one the config could NOT reach.

    Narrowing `python_files` closes `pytest .`. It does not close `pytest <path>`: an
    explicitly-named path is an INITIAL path and pytest skips the pattern check for those, so
    it imports the module before discovering there are no tests in it. Measured against three
    instruments -- `python_files`, a root conftest's `collect_ignore_glob`, and
    `addopts --ignore-glob` -- all three leak (D546 RESULT).

    So for any file someone might plausibly hand to pytest, import-safety is the only remaining
    defence, and it is a property of the module. A READ at import is left alone: two of these
    files read a committed `data/*.json` at import and that is survivable. Writing and fetching
    are not, and they are precisely what happened.
    """
    offenders = {}
    for rel in _tracked_python_files():
        if rel.startswith("tests/"):
            continue
        if not _collectable([rel], PYTEST_DEFAULT_PYTHON_FILES):
            continue
        hazards = _import_time_hazards((REPO / rel).read_text(encoding="utf-8"))
        if hazards:
            offenders[rel] = hazards
    assert not offenders, (
        f"these file(s) match pytest's default collection patterns AND write or fetch at "
        f"import, so naming one on a pytest command line does it: {offenders}. No pytest "
        f"setting prevents this. Move the work under `if __name__ == \"__main__\":`, which is "
        f"what the other files here already do."
    )


def test_the_import_safety_scan_fires(tmp_path):
    """Break what the assertion reads: the bytes of a module, through the same helper.

    Each case is one line of module-level code, and the pair that must NOT fire is as important
    as the pair that must -- a scan that flags every read would have been silenced on arrival.
    """
    fetches = "import urllib.request\nurllib.request.urlopen('http://x')\n"
    assert _import_time_hazards(fetches) == [(2, "urllib.request.urlopen('http://x')")]

    writes = "import json\njson.dump([], open('out.json', 'w'))\n"
    assert len(_import_time_hazards(writes)) == 2  # the dump and the write-mode open

    write_text = "from pathlib import Path\nPath('x').write_text('y')\n"
    assert _import_time_hazards(write_text) == [(2, "Path('x').write_text('y')")]

    # Guarded: the same line, under __main__, is not reachable by an import.
    guarded = "import json\nif __name__ == '__main__':\n    json.dump([], open('o', 'w'))\n"
    assert _import_time_hazards(guarded) == []

    # Inside a def: not reachable either. This is the case that made a naive scan useless.
    in_def = "import json\ndef go():\n    json.dump([], open('o', 'w'))\n"
    assert _import_time_hazards(in_def) == []

    # A READ is deliberately not a hazard, in either open() spelling.
    assert _import_time_hazards("open('x')\n") == []
    assert _import_time_hazards("import gzip\ngzip.open('x')\n") == []
    assert _import_time_hazards("from pathlib import Path\nPath('x').read_text()\n") == []
