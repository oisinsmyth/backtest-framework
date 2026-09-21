"""Unit gates for `validation/frozen.py` (D594).

Each test names the pre-registered clause it discharges, the way `test_cost_stack.py`
names "VERIFICATION_SCHEME.md Step 3". The clauses live in the deposit's frozen
protocol:

  * `SETTLEMENT_FLOW_LEDGER_PREREG.md` §13A.4 and unit test 34 — evaluation code
    refuses to run if the parameters differ from `FROZEN_<stage>.json`;
  * §13A.7(2) and unit test 60 — the evaluation length cannot change once
    evaluation has started;
  * §13A.8 control 1 and unit tests 64, 65 — the vault opens once per model, the
    opening is logged, a second opening is refused, and opening requires a frozen
    model to exist;
  * `OPENING_AGENT_STATE_PREREG.md` §12A control 1 and unit tests 18, 20 — the same
    two sentences for the opening-agent document;
  * `INDEX_REWEIGHT_FLOW_PREREG.md` §11 — `FROZEN_2027.json`, frozen before the
    announcement.

NO SEAL DATE IS CHOSEN ANYWHERE IN THIS FILE. The deposit seals 2025-03-01 →
2026-09-18 and this repository reserves 2024-01-01 onward; reconciling them is the
principal's open decision, so every window below is synthetic (`2001-…`), and
`SealedWindow` has no defaults to fall back on. No fixture is read and no strategy
return is computed.
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from backtest_framework.validation.frozen import (
    AlreadyOpenedError,
    FrozenDriftError,
    FrozenError,
    FrozenExistsError,
    ReservedSliceError,
    SealedWindow,
    VaultGuardError,
    assert_evaluation_length,
    assert_frozen,
    assert_none_at_or_after,
    filter_before,
    freeze,
    load_frozen,
    normalise_newlines,
    open_once,
    refuse_without_word,
    sha256_bytes,
    sha256_file,
    window_record,
)

PARAMS = {"tau": "15:00", "k": 3}
SYNTHETIC = SealedWindow("2001-03-01", "2002-09-18")  # synthetic; see the docstring


@pytest.fixture()
def bench(tmp_path):
    """A frozen model: two code files, one fixture, 200 evaluation days."""
    alpha = tmp_path / "alpha.py"
    beta = tmp_path / "beta.py"
    gamma = tmp_path / "gamma.csv.gz"
    alpha.write_bytes(b"a\n")
    beta.write_bytes(b"b\r\n")
    gamma.write_bytes(b"\x1f\x8b\x08\x00binary\r\nbytes")
    out = tmp_path / "results"
    rec = freeze(
        out,
        name="stageA",
        params=PARAMS,
        code_paths=[alpha, beta],
        fixture_paths=[gamma],
        evaluation_days=200,
        spec_commit="7085aac",
        instruction="the principal, 2001-01-01: 'freeze stage A'",
    )
    return {
        "dir": out,
        "fp": out / "FROZEN_stageA.json",
        "rec": rec,
        "alpha": alpha,
        "beta": beta,
        "gamma": gamma,
        "code": [alpha, beta],
        "fixtures": [gamma],
    }


# ----------------------------------------------------------------- hashing
def test_normalise_newlines_maps_crlf_and_lone_cr_to_lf():
    assert normalise_newlines(b"a\r\nb\rc\nd") == b"a\nb\nc\nd"
    assert normalise_newlines(b"") == b""
    assert normalise_newlines(b"\r") == b"\n"


def test_sha256_bytes_refuses_a_str():
    with pytest.raises(FrozenError, match="takes bytes"):
        sha256_bytes("a\n")  # type: ignore[arg-type]


def test_sha256_file_chunking_cannot_split_a_crlf(tmp_path):
    """A CRLF straddling the chunk boundary must not become two line ends."""
    p = tmp_path / "x.py"
    p.write_bytes(b"ab\r\ncd\r\n")
    whole = sha256_bytes(b"ab\ncd\n")
    for size in range(1, 12):
        assert sha256_file(p, chunk_size=size) == whole


def test_sha256_file_raises_on_a_missing_file_and_a_zero_chunk(tmp_path):
    with pytest.raises(FrozenError, match="not a file"):
        sha256_file(tmp_path / "nope.py")
    (tmp_path / "x.py").write_bytes(b"a\n")
    with pytest.raises(FrozenError, match="chunk_size"):
        sha256_file(tmp_path / "x.py", chunk_size=0)


# ----------------------------------------------------------------- freeze
def test_freeze_writes_frozen_name_json_lf_pinned(bench):
    """Ledger 13A.4(2) / INDEX_REWEIGHT §11: the file is `FROZEN_<name>.json`."""
    assert bench["fp"].is_file()
    raw = bench["fp"].read_bytes()
    assert b"\r\n" not in raw  # D551: never Path.write_text
    obj = json.loads(raw.decode("utf-8"))
    assert obj["name"] == "stageA"
    assert obj["spec"] == "7085aac"
    assert obj["instruction"] == "the principal, 2001-01-01: 'freeze stage A'"
    assert obj["git_head"] is None  # live_git defaults off; SPEC is a constant


def test_freeze_refuses_to_overwrite_an_existing_frozen_file(bench):
    """Ledger 13A.4: a change restarts the count under a NEW frozen file."""
    with pytest.raises(FrozenExistsError, match="will not overwrite"):
        freeze(bench["dir"], name="stageA", params=PARAMS,
               code_paths=bench["code"], fixture_paths=bench["fixtures"],
               evaluation_days=200)


@pytest.mark.parametrize(
    "kwargs, match",
    [
        ({"name": "stage A"}, "must match"),
        ({"name": "../escape"}, "must match"),
        ({"evaluation_days": 0}, ">= 1"),
        ({"evaluation_days": 1.5}, "must be an int"),
        ({"params": {"k": object()}}, "not JSON-serialisable"),
        ({"params": {3: "x"}}, "keys must be strings"),
        ({"code_paths": []}, "at least one code file"),
        ({"spec_commit": 7}, "spec_commit"),
    ],
)
def test_freeze_guards_its_inputs(tmp_path, kwargs, match):
    a = tmp_path / "a.py"
    a.write_bytes(b"a\n")
    base = dict(name="stageA", params=PARAMS, code_paths=[a], evaluation_days=200)
    base.update(kwargs)
    with pytest.raises(FrozenError, match=match):
        freeze(tmp_path / "out", **base)


def test_freeze_raises_on_a_missing_input_and_on_colliding_basenames(tmp_path):
    a = tmp_path / "a.py"
    a.write_bytes(b"a\n")
    with pytest.raises(FrozenError, match="does not exist"):
        freeze(tmp_path / "o1", name="s", params={}, code_paths=[tmp_path / "gone.py"])
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "a.py").write_bytes(b"a\n")
    with pytest.raises(FrozenError, match="share the basename"):
        freeze(tmp_path / "o2", name="s", params={}, code_paths=[a, sub / "a.py"])


def test_freeze_to_an_explicit_json_path_must_use_the_right_filename(tmp_path):
    a = tmp_path / "a.py"
    a.write_bytes(b"a\n")
    ok = freeze(tmp_path / "FROZEN_s.json", name="s", params={}, code_paths=[a])
    assert ok.path == tmp_path / "FROZEN_s.json"
    with pytest.raises(FrozenError, match="must be named FROZEN_t.json"):
        freeze(tmp_path / "wrong.json", name="t", params={}, code_paths=[a])


# ----------------------------------------------------------------- load
def test_load_frozen_catches_a_hand_edited_frozen_file(bench):
    """The easiest way to unfreeze a model is to edit the JSON. It is caught."""
    obj = json.loads(bench["fp"].read_text(encoding="utf-8"))
    obj["params"]["k"] = 4
    with open(bench["fp"], "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh)
    with pytest.raises(FrozenDriftError, match="params_sha256"):
        load_frozen(bench["fp"])


def test_load_frozen_catches_an_edited_code_digest(bench):
    obj = json.loads(bench["fp"].read_text(encoding="utf-8"))
    obj["code"][0]["sha256"] = "0" * 64
    obj["params_sha256"] = obj["params_sha256"]  # untouched, so content is the check
    with open(bench["fp"], "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh)
    with pytest.raises(FrozenDriftError, match="content_sha256"):
        load_frozen(bench["fp"])


def test_load_frozen_raises_on_a_missing_file_and_bad_json(tmp_path):
    with pytest.raises(FrozenError, match="no frozen file"):
        load_frozen(tmp_path / "FROZEN_x.json")
    bad = tmp_path / "FROZEN_x.json"
    bad.write_bytes(b"{not json")
    with pytest.raises(FrozenDriftError, match="not valid JSON"):
        load_frozen(bad)


# --------------------------------------------- ledger unit test 34: the guard
def test_ut34_assert_frozen_is_silent_when_nothing_moved(bench):
    assert (
        assert_frozen(bench["fp"], params=PARAMS, code_paths=bench["code"],
                      fixture_paths=bench["fixtures"])
        is None
    )


def test_ut34_a_drifted_param_is_named_with_expected_and_found(bench):
    with pytest.raises(FrozenDriftError) as ei:
        assert_frozen(bench["fp"], params={"tau": "15:00", "k": 4},
                      code_paths=bench["code"], fixture_paths=bench["fixtures"])
    msg = str(ei.value)
    assert "param 'k' DRIFTED" in msg and "frozen 3" in msg and "found 4" in msg
    assert "13A.4" in msg


def test_ut34_a_missing_or_extra_param_key_is_named(bench, tmp_path):
    with pytest.raises(FrozenDriftError, match="frozen param 'k' is absent"):
        assert_frozen(bench["fp"], params={"tau": "15:00"},
                      code_paths=bench["code"], fixture_paths=bench["fixtures"])
    with pytest.raises(FrozenDriftError, match="param 'extra' was supplied"):
        assert_frozen(bench["fp"], params={**PARAMS, "extra": 1},
                      code_paths=bench["code"], fixture_paths=bench["fixtures"])


def test_ut34_a_drifted_code_file_is_named_before_a_drifted_fixture(bench):
    bench["beta"].write_bytes(b"B\r\n")
    bench["gamma"].write_bytes(b"\x1f\x8b\x08\x00OTHER")
    with pytest.raises(FrozenDriftError) as ei:
        assert_frozen(bench["fp"], params=PARAMS, code_paths=bench["code"],
                      fixture_paths=bench["fixtures"])
    msg = str(ei.value)
    assert "code 'beta.py' DRIFTED" in msg and "gamma.csv.gz" not in msg


def test_ut34_a_code_file_deleted_from_disk_is_named(bench):
    bench["alpha"].unlink()
    with pytest.raises(FrozenDriftError, match="alpha.py' is missing from disk"):
        assert_frozen(bench["fp"], params=PARAMS, code_paths=bench["code"],
                      fixture_paths=bench["fixtures"])


def test_ut34_an_unsupplied_or_extra_file_is_named(bench, tmp_path):
    with pytest.raises(FrozenDriftError, match="'beta.py' was not supplied"):
        assert_frozen(bench["fp"], params=PARAMS, code_paths=[bench["alpha"]],
                      fixture_paths=bench["fixtures"])
    extra = tmp_path / "delta.py"
    extra.write_bytes(b"d\n")
    with pytest.raises(FrozenDriftError, match="'delta.py' was supplied but"):
        assert_frozen(bench["fp"], params=PARAMS,
                      code_paths=[*bench["code"], extra],
                      fixture_paths=bench["fixtures"])


def test_ut34_a_crlf_only_change_to_a_code_file_is_NOT_drift(bench):
    """The newline pin, from the other side: a checkout policy is not a change."""
    bench["beta"].write_bytes(b"b\n")  # was b"b\r\n"
    assert_frozen(bench["fp"], params=PARAMS, code_paths=bench["code"],
                  fixture_paths=bench["fixtures"])


def test_a_fixture_is_hashed_raw_so_a_newline_change_IS_drift(bench):
    """And a fixture is bytes: `.csv.gz` has no newlines to normalise."""
    bench["gamma"].write_bytes(b"\x1f\x8b\x08\x00binary\nbytes")
    with pytest.raises(FrozenDriftError, match="fixture 'gamma.csv.gz' DRIFTED"):
        assert_frozen(bench["fp"], params=PARAMS, code_paths=bench["code"],
                      fixture_paths=bench["fixtures"])


# ------------------------------------- ledger unit test 60: evaluation length
def test_ut60_evaluation_length_cannot_be_extended(bench):
    assert assert_evaluation_length(bench["fp"], 200) is None
    with pytest.raises(FrozenDriftError) as ei:
        assert_evaluation_length(bench["fp"], 260)
    msg = str(ei.value)
    assert "frozen at 200" in msg and "asks for 260" in msg and "13A.7(2)" in msg


def test_ut60_a_frozen_none_and_a_supplied_number_also_differ(tmp_path):
    a = tmp_path / "a.py"
    a.write_bytes(b"a\n")
    freeze(tmp_path / "o", name="s", params={}, code_paths=[a])
    with pytest.raises(FrozenDriftError, match="frozen at None"):
        assert_evaluation_length(tmp_path / "o" / "FROZEN_s.json", 120)


# ----------------------------------------------------------- sealed window
def test_sealed_window_takes_explicit_dates_and_has_no_defaults():
    with pytest.raises(TypeError):
        SealedWindow()  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        SealedWindow("2001-03-01")  # type: ignore[call-arg]


def test_sealed_window_refuses_an_unsorted_or_non_iso_window():
    with pytest.raises(FrozenError, match="unsorted"):
        SealedWindow("2002-09-18", "2001-03-01")
    with pytest.raises(FrozenError, match="not an ISO date"):
        SealedWindow("2001-13-01", "2002-09-18")
    with pytest.raises(FrozenError, match="zero-padded"):
        SealedWindow("2001-3-01", "2002-09-18")  # a real date that sorts wrongly
    with pytest.raises(FrozenError, match="ISO date string"):
        SealedWindow(2001, "2002-09-18")  # type: ignore[arg-type]
    assert SealedWindow("2001-03-01", "2001-03-01").as_list() == ["2001-03-01"] * 2


def test_sealed_window_contains_is_inclusive_at_both_ends():
    assert SYNTHETIC.contains("2001-03-01")
    assert SYNTHETIC.contains("2002-09-18")
    assert SYNTHETIC.contains("2001-12-31")
    assert not SYNTHETIC.contains("2001-02-28")
    assert not SYNTHETIC.contains("2002-09-19")


# ------------------------------------------- the three-layer reserved guard
DAYS = ["2001-12-30", "2001-12-31", "2002-01-01", "2002-01-02"]
CUT = "2002-01-01"


def test_layer1_filter_before_on_a_dataframe_and_on_a_sequence():
    pd = pytest.importorskip("pandas")
    df = pd.DataFrame({"day": DAYS, "x": [1, 2, 3, 4]})
    got = filter_before(df, "day", CUT)
    assert list(got["day"]) == DAYS[:2] and list(got["x"]) == [1, 2]
    assert list(filter_before(DAYS, None, CUT)) == DAYS[:2]
    assert list(filter_before(np.array(DAYS), None, CUT)) == DAYS[:2]
    assert filter_before([], None, CUT) == []


def test_layer2_assert_none_at_or_after_raises_and_names_the_first_row():
    pd = pytest.importorskip("pandas")
    df = pd.DataFrame({"day": DAYS})
    with pytest.raises(ReservedSliceError) as ei:
        assert_none_at_or_after(df, "day", CUT)
    msg = str(ei.value)
    assert "[HOLDOUT]" in msg and "2 row(s)" in msg and "first 2002-01-01" in msg
    # and it is silent on the filtered frame — layer 1 then layer 2, as the runners do
    assert assert_none_at_or_after(filter_before(df, "day", CUT), "day", CUT) is None


def test_layer2_is_an_assertionerror_too_so_expect_raise_still_catches_it():
    """`scripts/stage0_d581_gamma_close.py:39` catches AssertionError."""
    with pytest.raises(AssertionError):
        assert_none_at_or_after(DAYS, None, CUT)


def test_layer3_window_record_has_the_windows_block_shape():
    rec = window_record(DAYS, None, CUT)
    assert rec == {
        "first_session_read": "2001-12-30",
        "last_session_read": "2002-01-02",
        "reserved_from": CUT,
        "sessions_read": 4,
        "distinct_sessions_read": 4,
        "reserved_rows_read": 2,
    }
    assert window_record(filter_before(DAYS, None, CUT), None, CUT)[
        "reserved_rows_read"
    ] == 0
    empty = window_record([], None, CUT)
    assert empty["first_session_read"] is None and empty["sessions_read"] == 0


def test_a_datetime_column_is_refused_rather_than_coerced():
    """np.datetime64 stringifies to '2002-01-01T00:00:00.000000000' — which sorts
    AFTER '2002-01-01', so a silent coercion would let the first reserved session
    straight through the guard that exists to stop it."""
    col = np.array(DAYS, dtype="datetime64[ns]")
    with pytest.raises(FrozenError, match="dtype datetime64"):
        assert_none_at_or_after(col, None, CUT)
    # the reason, demonstrated:
    assert str(col[2]) > CUT and str(col[2])[:10] == CUT


def test_non_iso_day_values_are_refused():
    with pytest.raises(FrozenError, match="not ISO dates"):
        filter_before(["Jan 2002"], None, CUT)
    with pytest.raises(FrozenError, match="not an ISO day string"):
        filter_before(DAYS, None, "2002/01/01")


# ------------------------------- ledger unit tests 64 / 65 (and opening 18 / 20)
def test_ut64_opening_without_a_frozen_model_is_refused(tmp_path):
    with pytest.raises(VaultGuardError, match="no frozen model at"):
        open_once(tmp_path / "openings.jsonl", window=SYNTHETIC, model="m1",
                  instruction="the principal, 2001-01-01: 'open it'",
                  frozen_path=tmp_path / "FROZEN_absent.json")


def test_ut64_opening_against_a_hand_edited_frozen_model_is_refused(bench):
    obj = json.loads(bench["fp"].read_text(encoding="utf-8"))
    obj["evaluation_days"] = 400
    with open(bench["fp"], "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh)
    with pytest.raises(VaultGuardError, match="did not load"):
        open_once(bench["dir"] / "openings.jsonl", window=SYNTHETIC, model="m1",
                  instruction="the principal, 2001-01-01: 'open it'",
                  frozen_path=bench["fp"])


def test_ut64_opening_against_drifted_code_is_refused(bench):
    bench["alpha"].write_bytes(b"A\n")
    with pytest.raises(VaultGuardError) as ei:
        open_once(bench["dir"] / "openings.jsonl", window=SYNTHETIC, model="m1",
                  instruction="the principal, 2001-01-01: 'open it'",
                  frozen_path=bench["fp"], params=PARAMS,
                  code_paths=bench["code"], fixture_paths=bench["fixtures"])
    assert "alpha.py" in str(ei.value) and "refusing to open" in str(ei.value)


def test_ut65_the_opening_is_logged_and_a_second_one_is_refused(bench):
    log = bench["dir"] / "openings.jsonl"
    instruction = "the principal, 2001-01-01: 'open the window for m1'"
    out = open_once(log, window=SYNTHETIC, model="m1", instruction=instruction,
                    frozen_path=bench["fp"], params=PARAMS,
                    code_paths=bench["code"], fixture_paths=bench["fixtures"])

    assert out.window == ["2001-03-01", "2002-09-18"]
    assert out.instruction == instruction  # verbatim
    assert out.frozen_content_sha256 == bench["rec"].content_sha256
    assert out.frozen_sha256 == sha256_file(bench["fp"])
    assert out.opened_utc.endswith("Z") and len(out.opened_utc) == 20

    raw = log.read_bytes()
    assert b"\r\n" not in raw and raw.endswith(b"\n")
    rows = [json.loads(ln) for ln in raw.decode("utf-8").splitlines()]
    assert len(rows) == 1 and rows[0]["model"] == "m1"
    assert rows[0]["instruction"] == instruction
    assert rows[0]["frozen_sha256"] == out.frozen_sha256

    with pytest.raises(AlreadyOpenedError) as ei:
        open_once(log, window=SYNTHETIC, model="m1", instruction=instruction,
                  frozen_path=bench["fp"])
    assert "already opened for model 'm1'" in str(ei.value)
    assert out.opened_utc in str(ei.value)
    # refused means refused: nothing was appended
    assert log.read_bytes() == raw


def test_ut65_a_different_model_may_open_and_the_log_appends(bench):
    log = bench["dir"] / "openings.jsonl"
    kw = dict(window=SYNTHETIC, frozen_path=bench["fp"])
    open_once(log, model="m1", instruction="the principal: 'm1'", **kw)
    open_once(log, model="m2", instruction="the principal: 'm2'", **kw)
    rows = [json.loads(ln) for ln in log.read_text(encoding="utf-8").splitlines()]
    assert [r["model"] for r in rows] == ["m1", "m2"]


def test_a_damaged_opening_log_is_a_refusal_not_a_fresh_start(bench):
    log = bench["dir"] / "openings.jsonl"
    log.write_bytes(b'{"model": "m1"\n')
    with pytest.raises(VaultGuardError, match="not valid JSON"):
        open_once(log, window=SYNTHETIC, model="m1",
                  instruction="the principal: 'm1'", frozen_path=bench["fp"])


def test_open_once_guards_its_own_arguments(bench):
    log = bench["dir"] / "openings.jsonl"
    with pytest.raises(FrozenError, match="SealedWindow"):
        open_once(log, window=("2001-03-01", "2002-09-18"), model="m1",  # type: ignore[arg-type]
                  instruction="x", frozen_path=bench["fp"])
    with pytest.raises(FrozenError, match="model must be"):
        open_once(log, window=SYNTHETIC, model="  ", instruction="x",
                  frozen_path=bench["fp"])
    with pytest.raises(FrozenError, match="verbatim"):
        open_once(log, window=SYNTHETIC, model="m1", instruction="",
                  frozen_path=bench["fp"])


# ----------------------------------------------------------------- refusal
def test_refuse_without_word_returns_2_and_prints_the_d574_message():
    """The D574 shape, called for real — `run(False, log=...)` returns 2."""
    said = []
    rc = refuse_without_word(False, "the reserved 2024+ slice on NQ", log=said.append)
    assert rc == 2
    assert said == [
        "REFUSED: --run reads the reserved 2024+ slice on NQ; "
        "re-run with --principals-word only on the principal's word."
    ]


def test_refuse_without_word_returns_0_on_the_word_and_says_nothing():
    said = []
    assert refuse_without_word(True, "anything", log=said.append) == 0
    assert said == []


def test_refuse_without_word_refuses_a_truthy_non_bool():
    """`refuse_without_word("no")` must not read as the principal's word."""
    with pytest.raises(FrozenError, match="must be a bool"):
        refuse_without_word("no", "x", log=lambda *a: None)  # type: ignore[arg-type]
