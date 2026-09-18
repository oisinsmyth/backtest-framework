"""Every published drawdown states its own sign, and the statement is re-derived (D542).

The repository publishes drawdown in two signs: `analytics.metrics` returns a positive
fraction of peak, `research/terrain_strategies` publishes it negative. D542 collapsed the
arithmetic to one implementation and left the artifacts alone, so the disagreement is
DISCLOSED rather than removed — and a disclosure nothing checks is a comment.

These gates check the marker against the values it describes, not merely its presence.
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location(
        "label_drawdown_convention", REPO / "scripts" / "label_drawdown_convention.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["label_drawdown_convention"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


L = _load()

# A floor, because every one of these tests scans a DISCOVERED set. Four of seven count
# gates in this repository once passed on an empty match, and the failure mode is silent:
# the scan finds nothing, the problem list is empty, and the assertion reads as a pass.
# 83 artifacts carried a drawdown level when D542 was written.
MINIMUM_ARTIFACTS = 70


def test_the_census_finds_the_artifacts_it_is_meant_to_scan():
    rows = L.census()
    assert len(rows) >= MINIMUM_ARTIFACTS, (
        f"only {len(rows)} artifact(s) found; the scan has lost its input rather than "
        f"the repository having lost its drawdowns"
    )
    assert any(c == "negative" for _, c, _ in rows)
    assert any(c == "positive" for _, c, _ in rows)


def test_every_artifact_declares_a_sign_that_matches_its_own_values():
    assert L.cmd_check() == 0


def test_differences_are_not_counted_as_levels():
    """`d_maxdd` is a difference of two drawdowns and is signed by definition.

    Counting it as a level made three files look like they held both conventions at once
    — `breakout_study_summary.json` reads as 8 negative among 250 positive on the loose
    pattern, and every one of the 8 is a `d_maxdd`. A marker derived from that census
    would have refused three files for a disagreement that is not there.
    """
    payload = {"max_drawdown": 0.25, "d_maxdd": -0.03, "mean_d_maxdd": -0.01}
    assert L.levels(payload) == [0.25]
    assert L.convention_of(L.levels(payload)) == "positive"


def test_a_file_holding_both_signs_is_refused_not_labelled():
    """One marker cannot describe two conventions, and half a disclosure is worse than
    none — it would tell a reader the file is safe to read one way when it is not."""
    assert L.convention_of([0.25, -0.25]) == "MIXED"
    assert L.convention_of([]) is None
    assert L.convention_of([0.0, 0.0]) is None


def test_the_gate_fires_when_a_marker_contradicts_its_values(tmp_path, monkeypatch):
    """Break what the assertion READS — the sign inside the marker — not its name.

    A gate that only checks the marker's presence would pass on a file whose marker says
    `positive` over negative values, which is the exact failure a convention marker exists
    to prevent.
    """
    sandbox = tmp_path / "repo"
    (sandbox / "data").mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=sandbox, check=True)

    honest = {"max_drawdown_convention": {"sign": "negative"}, "max_drawdown": -0.25}
    lying = {"max_drawdown_convention": {"sign": "positive"}, "max_drawdown": -0.25}
    missing = {"max_drawdown": -0.25}
    for name, payload in (("honest.json", honest), ("lying.json", lying), ("bare.json", missing)):
        (sandbox / "data" / name).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    subprocess.run(["git", "add", "data"], cwd=sandbox, check=True)

    monkeypatch.setattr(L, "REPO", sandbox)
    rows = dict((rel, conv) for rel, conv, _ in L.census())
    assert rows == {
        "data/bare.json": "negative",
        "data/honest.json": "negative",
        "data/lying.json": "negative",
    }
    assert L.cmd_check() == 1, "the check passed on a lying marker and a missing one"


def test_the_marker_insertion_moves_no_value(tmp_path, monkeypatch):
    """The premise of D542's choice: the artifacts are labelled, never rewritten."""
    sandbox = tmp_path / "repo"
    (sandbox / "data").mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=sandbox, check=True)
    # Deliberately awkward: CRLF, four-space indent, a float whose repr must survive.
    original = '{\r\n    "max_drawdown": -0.8339900882218974,\r\n    "nested": {"maxdd": -0.5}\r\n}\r\n'
    target = sandbox / "data" / "awkward.json"
    target.write_bytes(original.encode("utf-8"))
    subprocess.run(["git", "add", "data"], cwd=sandbox, check=True)
    monkeypatch.setattr(L, "REPO", sandbox)

    assert L.cmd_write() == 0
    raw = target.read_bytes()
    after = json.loads(raw.decode("utf-8"))
    assert after.pop("max_drawdown_convention")["sign"] == "negative"
    assert after == json.loads(original)
    # The float survived to the last digit, and no LF was spliced into a CRLF file.
    assert b"-0.8339900882218974" in raw
    assert raw.replace(b"\r\n", b"").count(b"\n") == 0


def test_writing_twice_is_a_fixed_point(tmp_path, monkeypatch):
    """`build_decision_register --write` once grew its own output on every run. A labeller
    that appends a second marker each time would do the same, invisibly."""
    sandbox = tmp_path / "repo"
    (sandbox / "data").mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=sandbox, check=True)
    target = sandbox / "data" / "one.json"
    target.write_text(json.dumps({"max_drawdown": 0.25}, indent=2), encoding="utf-8")
    subprocess.run(["git", "add", "data"], cwd=sandbox, check=True)
    monkeypatch.setattr(L, "REPO", sandbox)

    assert L.cmd_write() == 0
    once = target.read_bytes()
    assert L.cmd_write() == 0
    assert target.read_bytes() == once


@pytest.mark.parametrize(
    "key, is_level",
    [
        ("max_drawdown", True),
        ("maxdd", True),
        ("combined_max_drawdown", True),
        ("real_max_drawdown", True),
        ("bh_max_drawdown", True),
        ("hold_maxdd", True),
        ("d_maxdd", False),
        ("mean_d_maxdd", False),
        ("median_d_maxdd", False),
        ("max_drawdown_bars", False),
        ("sharpe", False),
    ],
)
def test_the_key_partition_is_the_one_the_census_claims(key, is_level):
    assert bool(L.levels({key: -0.25})) is is_level
