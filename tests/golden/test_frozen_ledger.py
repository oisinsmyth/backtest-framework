"""Golden tests for `validation/frozen.py` (D594).

Hand arithmetic in `test_frozen_ledger.hand.txt`, per CONTRIBUTING step 2: every
digest below was produced by two calculators that never import this codebase — GNU
`sha256sum` fed by `printf`, and .NET `System.Security.Cryptography.SHA256` over a
literal `[byte[]]` — and they agreed on every line. The anchor case asserts the
published SHA-256 of the empty string, so a suite where `hashlib` had been swapped
for something else fails on the first assertion rather than on a subtle one.

A digest belongs in this tier for the same reason a fill price does. D551: the same
fixture froze to snapshot id 51756f0d on Windows and 1bb6fe9c on Linux because one
writer used `Path.write_text`, and a snapshot id is the provenance identifier logged
with every trial. Case 1 is that defect turned into an assertion — b"b\\r\\n" hashes
to 0263... as text and 679e... as binary, and the module's rule (code is text and is
LF-pinned; a fixture is hashed raw) is what makes the first of those two stable
across checkouts and the second equal to every `fixture_sha256` already published.

Every input file here is written with `write_bytes` from an explicit literal. No
market fixture is read, and no seal date is chosen: the window this module is for is
always passed in by its caller.
"""

from __future__ import annotations

import hashlib
import json

import pytest

from backtest_framework.registry.trial_registry import canonical_json
from backtest_framework.validation.frozen import (
    FrozenDriftError,
    FrozenExistsError,
    freeze,
    load_frozen,
    sha256_bytes,
    sha256_file,
)

# --- the hand ledger's constants, transcribed from test_frozen_ledger.hand.txt ---
SHA_EMPTY = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
SHA_A_LF = "87428fc522803d31065e7bce3cf03fe475096631e5e07bbd7a0fde60c4cf25c7"
SHA_B_LF = "0263829989b6fd954f72baaf2fc64bc2e2f01d692d4de72986ea808f6e99813f"
SHA_B_CRLF = "679e273f78fc8f8ba114db23c2dce80cc77c91083939825ca830152f2f080d08"
SHA_UPPER_A_LF = "06f961b802bc46ee168555f066d28f4f0e9afdf3f88174c1ee6f9de004fc30a0"

PARAMS_CANONICAL = '{"k":3,"tau":"15:00"}'
PARAMS_SHA = "e3d5888fb02d109fed7f6f35db88b55e2612d0030de70dd0833f6d607abd2585"

IDENTITY_PAYLOAD = (
    '{"code":[{"name":"alpha.py","sha256":"'
    + SHA_A_LF
    + '"},{"name":"beta.py","sha256":"'
    + SHA_B_LF
    + '"}],"evaluation_days":200,"fixtures":[{"name":"gamma.bin","sha256":"'
    + SHA_B_CRLF
    + '"}],"instruction":null,"name":"demo","params":{"k":3,"tau":"15:00"},'
    '"schema":"frozen/1","spec":null}'
)
IDENTITY_LEN = 429
CONTENT_SHA = "4cddcb766de70ff1c8a33cbcd1c89af7dc3d939af163dcc446b50dbfeef9ee8a"

# the params dict is built with "tau" FIRST, deliberately: a change from
# canonical_json to a plain json.dumps would move the digest and fail here.
PARAMS = {"tau": "15:00", "k": 3}


def _bench(tmp_path):
    """The golden's three files, written as explicit bytes (never write_text)."""
    alpha = tmp_path / "alpha.py"
    beta = tmp_path / "beta.py"
    gamma = tmp_path / "gamma.bin"
    alpha.write_bytes(b"a\n")
    beta.write_bytes(b"b\r\n")
    gamma.write_bytes(b"b\r\n")
    return alpha, beta, gamma


# ---------------------------------------------------------------- Case 0
def test_case_0_anchor_the_empty_string_and_one_line_of_text():
    assert sha256_bytes(b"") == SHA_EMPTY
    assert sha256_bytes(b"a\n") == SHA_A_LF
    assert sha256_bytes(b"A\n") == SHA_UPPER_A_LF


# ---------------------------------------------------------------- Case 1
def test_case_1_the_same_three_bytes_hash_two_ways_and_the_rule_picks_one(tmp_path):
    _, beta, _ = _bench(tmp_path)
    assert beta.read_bytes() == b"b\r\n"

    assert sha256_file(beta, text_normalise=True) == SHA_B_LF
    assert sha256_file(beta, text_normalise=False) == SHA_B_CRLF
    assert SHA_B_LF != SHA_B_CRLF  # D551, as an assertion

    # the text digest is a fact about the CONTENT: the LF-only copy agrees
    lf_copy = tmp_path / "beta_lf.py"
    lf_copy.write_bytes(b"b\n")
    assert sha256_file(lf_copy, text_normalise=True) == SHA_B_LF
    assert sha256_file(lf_copy, text_normalise=False) == SHA_B_LF


def test_case_1_binary_mode_reproduces_the_published_fixture_sha256_loop(tmp_path):
    """`text_normalise=False` is bit-identical to run_d555:79's chunked loop.

    Re-implemented here rather than imported, so the test does not depend on a
    runner: if the two ever disagree, every `fixture_sha256` in `data/*.json`
    silently stops reproducing.
    """
    _, _, gamma = _bench(tmp_path)
    blob = bytes(range(256)) * 40 + b"\r\n\r" + bytes(range(256))
    big = tmp_path / "big.csv.gz"
    big.write_bytes(blob)

    def d555_sha256(path):
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()

    for p in (gamma, big):
        assert sha256_file(p, text_normalise=False) == d555_sha256(p)


# ---------------------------------------------------------------- Case 2
def test_case_2_canonical_params_text_and_digest():
    assert canonical_json(PARAMS) == PARAMS_CANONICAL
    assert len(PARAMS_CANONICAL.encode("utf-8")) == 21
    assert sha256_bytes(PARAMS_CANONICAL.encode("utf-8")) == PARAMS_SHA


# ---------------------------------------------------------------- Case 3
def test_case_3_the_frozen_records_identity(tmp_path):
    alpha, beta, gamma = _bench(tmp_path)
    out = tmp_path / "results"
    rec = freeze(
        out,
        name="demo",
        params=PARAMS,
        code_paths=[beta, alpha],  # listed out of order on purpose
        fixture_paths=[gamma],
        evaluation_days=200,
    )

    assert len(IDENTITY_PAYLOAD.encode("utf-8")) == IDENTITY_LEN
    assert sha256_bytes(IDENTITY_PAYLOAD.encode("utf-8")) == CONTENT_SHA

    assert rec.params_sha256 == PARAMS_SHA
    assert rec.content_sha256 == CONTENT_SHA
    assert [d.name for d in rec.code] == ["alpha.py", "beta.py"]  # sorted, not as given
    assert [d.sha256 for d in rec.code] == [SHA_A_LF, SHA_B_LF]
    assert [(d.name, d.sha256) for d in rec.fixtures] == [("gamma.bin", SHA_B_CRLF)]
    assert rec.evaluation_days == 200
    assert rec.spec is None and rec.instruction is None and rec.git_head is None

    frozen_file = out / "FROZEN_demo.json"
    assert rec.path == frozen_file

    # the file on disk carries the same identity, is LF-pinned, and round-trips
    raw = frozen_file.read_bytes()
    assert b"\r\n" not in raw
    obj = json.loads(raw.decode("utf-8"))
    assert obj["content_sha256"] == CONTENT_SHA
    assert obj["params"] == {"k": 3, "tau": "15:00"}
    assert load_frozen(frozen_file).content_sha256 == CONTENT_SHA


def test_case_3_identity_ignores_where_the_files_were_kept(tmp_path):
    """Same content, different directory, same content_sha256. D551's lesson."""
    shas = []
    for i in (1, 2):
        home = tmp_path / f"machine_{i}" / ("deep/er" if i == 2 else "")
        home.mkdir(parents=True)
        alpha, beta, gamma = _bench(home)
        shas.append(
            freeze(
                tmp_path / f"out_{i}",
                name="demo",
                params=PARAMS,
                code_paths=[alpha, beta],
                fixture_paths=[gamma],
                evaluation_days=200,
            ).content_sha256
        )
    assert shas == [CONTENT_SHA, CONTENT_SHA]


# ---------------------------------------------------------------- Case 4
def test_case_4_one_changed_byte_in_one_code_file_is_named(tmp_path):
    from backtest_framework.validation.frozen import assert_frozen

    alpha, beta, gamma = _bench(tmp_path)
    out = tmp_path / "results"
    freeze(
        out,
        name="demo",
        params=PARAMS,
        code_paths=[alpha, beta],
        fixture_paths=[gamma],
        evaluation_days=200,
    )
    fp = out / "FROZEN_demo.json"

    # unchanged: silent
    assert_frozen(fp, params=PARAMS, code_paths=[alpha, beta], fixture_paths=[gamma])

    alpha.write_bytes(b"A\n")  # one byte, one file
    with pytest.raises(FrozenDriftError) as ei:
        assert_frozen(fp, params=PARAMS, code_paths=[alpha, beta],
                      fixture_paths=[gamma])
    msg = str(ei.value)
    assert "alpha.py" in msg and "beta.py" not in msg
    assert SHA_A_LF in msg and SHA_UPPER_A_LF in msg


def test_case_4_a_drifted_param_is_reported_before_a_drifted_file(tmp_path):
    from backtest_framework.validation.frozen import assert_frozen

    alpha, beta, gamma = _bench(tmp_path)
    out = tmp_path / "results"
    freeze(out, name="demo", params=PARAMS, code_paths=[alpha, beta],
           fixture_paths=[gamma], evaluation_days=200)
    fp = out / "FROZEN_demo.json"

    alpha.write_bytes(b"A\n")
    with pytest.raises(FrozenDriftError) as ei:
        assert_frozen(fp, params={"tau": "15:00", "k": 4},
                      code_paths=[alpha, beta], fixture_paths=[gamma])
    msg = str(ei.value)
    assert "param 'k'" in msg and "alpha.py" not in msg


def test_freeze_refuses_to_overwrite(tmp_path):
    alpha, beta, gamma = _bench(tmp_path)
    out = tmp_path / "results"
    kw = dict(name="demo", params=PARAMS, code_paths=[alpha, beta],
              fixture_paths=[gamma], evaluation_days=200)
    freeze(out, **kw)
    with pytest.raises(FrozenExistsError) as ei:
        freeze(out, **kw)
    assert "FROZEN_demo.json" in str(ei.value)
    assert "restarts the evaluation count" in str(ei.value)
