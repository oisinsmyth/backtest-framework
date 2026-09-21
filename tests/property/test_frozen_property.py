"""Property tests for `validation/frozen.py` (D594).

Conventions per D78 (derandomized hypothesis; seeding owned by the library rather
than a hand-rolled seed parameter) as amended by D537 (`derandomize=True` fixes the
seed but NOT the examples drawn — since hypothesis 6.156.6 the constant pool is
harvested from `sys.modules` at test time, so a failure here reproduces within a run
but the example set is not byte-stable between a full-suite run and a single-file
run; reproduce a failure with the whole suite). `max_examples=40` and
`deadline=None` keep the file inside the default gate.

WHAT IS WORTH A PROPERTY HERE. The digests themselves are pinned by
`tests/golden/test_frozen_ledger.hand.txt`; the closed cases are pinned by
`tests/unit/test_frozen.py`. What no finite set of examples covers is the SHAPE of
the two failures this module exists to prevent:

  * **a chunk boundary landing inside a CRLF.** The straddle is a property of the
    file length modulo the buffer size, and a 1 MiB buffer means the first example
    that would have caught it needs a megabyte of exactly the wrong bytes. Here the
    chunk size and the byte string are both quantified over.
  * **a digest that is a fact about the machine rather than the content** — D551's
    defect. Quantified: relocating every input file, reordering the caller's lists
    and re-running the freeze must leave `content_sha256` fixed, while changing one
    byte of one input must move it.

Plus the reserved-slice guard's arithmetic identity, which is the property the
three-layer idiom actually claims: whatever `filter_before` keeps, layer 2 accepts,
and `sessions_read` is conserved across the split.

No fixture is read, no strategy return is computed, and no seal date is chosen —
every date below is drawn inside a synthetic 2001-2002 span.
"""

from __future__ import annotations

import datetime as dt

import pytest
from hypothesis import given, settings, strategies as st

from backtest_framework.registry.trial_registry import canonical_json
from backtest_framework.validation.frozen import (
    FrozenDriftError,
    SealedWindow,
    assert_frozen,
    assert_none_at_or_after,
    filter_before,
    freeze,
    load_frozen,
    normalise_newlines,
    sha256_bytes,
    sha256_file,
    window_record,
)

SETTINGS = settings(derandomize=True, max_examples=40, deadline=None)

# bytes built mostly from CR, LF and one ordinary character, so a drawn example is
# dense in the boundary cases instead of being random noise that almost never
# contains a CRLF at all.
NEWLINE_BYTES = st.lists(
    st.sampled_from([b"\r", b"\n", b"\r\n", b"a", b"", b"\n\r"]), max_size=24
).map(b"".join)

DAY = st.dates(
    min_value=dt.date(2001, 1, 1), max_value=dt.date(2002, 12, 31)
).map(lambda d: d.isoformat())

PARAM_VALUE = st.one_of(
    st.integers(-1000, 1000),
    st.text(max_size=8),
    st.booleans(),
    st.none(),
    st.lists(st.integers(-10, 10), max_size=4),
)
PARAMS = st.dictionaries(st.text(min_size=1, max_size=6), PARAM_VALUE, max_size=5)


# --------------------------------------------------------------- the newline pin
@SETTINGS
@given(blob=NEWLINE_BYTES, chunk=st.integers(min_value=1, max_value=9))
def test_the_chunked_text_digest_equals_the_whole_buffer_digest(tmp_path_factory,
                                                                blob, chunk):
    p = tmp_path_factory.mktemp("chunk") / "x.py"
    p.write_bytes(blob)
    assert sha256_file(p, text_normalise=True, chunk_size=chunk) == sha256_bytes(
        normalise_newlines(blob)
    )
    assert sha256_file(p, text_normalise=False, chunk_size=chunk) == sha256_bytes(blob)


@SETTINGS
@given(blob=NEWLINE_BYTES)
def test_text_hashing_is_invariant_to_the_checkouts_newline_policy(tmp_path_factory,
                                                                   blob):
    """LF, CRLF and CR renderings of one content share a text digest — D551."""
    d = tmp_path_factory.mktemp("policy")
    lf = normalise_newlines(blob)
    crlf = lf.replace(b"\n", b"\r\n")
    cr = lf.replace(b"\n", b"\r")
    digests = set()
    for i, variant in enumerate((lf, crlf, cr)):
        q = d / f"v{i}.py"
        q.write_bytes(variant)
        digests.add(sha256_file(q, text_normalise=True))
    assert len(digests) == 1


@SETTINGS
@given(blob=NEWLINE_BYTES)
def test_normalise_newlines_is_idempotent_and_never_adds_a_cr(blob):
    once = normalise_newlines(blob)
    assert normalise_newlines(once) == once
    assert b"\r" not in once
    assert once.count(b"\n") == blob.count(b"\n") + blob.replace(
        b"\r\n", b"\n"
    ).count(b"\r")


# ------------------------------------------------- the identity is content-only
@SETTINGS
@given(params=PARAMS, blob_a=NEWLINE_BYTES, blob_b=st.binary(max_size=24),
       swap=st.booleans(), days=st.one_of(st.none(), st.integers(1, 500)))
def test_content_sha256_survives_relocation_and_reordering(tmp_path_factory, params,
                                                           blob_a, blob_b, swap, days):
    root = tmp_path_factory.mktemp("identity")
    shas = []
    for i, sub in enumerate(("here", "somewhere/much/deeper")):
        home = root / f"m{i}" / sub
        home.mkdir(parents=True)
        a, z, b = home / "alpha.py", home / "zeta.py", home / "gamma.csv.gz"
        a.write_bytes(blob_a)
        z.write_bytes(blob_a + b"z")
        b.write_bytes(blob_b)
        # machine 2 keeps the files deeper AND lists them in the opposite order
        code = [a, z] if (i == 0) != swap else [z, a]
        rec = freeze(
            root / f"out{i}",
            name="p",
            params=params,
            code_paths=code,
            fixture_paths=[b],
            evaluation_days=days,
        )
        shas.append(rec.content_sha256)
        assert load_frozen(rec.path).content_sha256 == rec.content_sha256
    assert shas[0] == shas[1]
    # the params' digest is the canonical text's digest, whatever the insertion order
    assert shas and sha256_bytes(canonical_json(params).encode("utf-8")) == load_frozen(
        root / "out0" / "FROZEN_p.json"
    ).params_sha256


@SETTINGS
@given(blob=st.binary(max_size=24), extra=st.binary(min_size=1, max_size=4))
def test_one_changed_byte_of_code_moves_the_identity_and_is_caught(tmp_path_factory,
                                                                   blob, extra):
    d = tmp_path_factory.mktemp("drift")
    a = d / "alpha.py"
    a.write_bytes(blob)
    rec = freeze(d / "out", name="p", params={"k": 1}, code_paths=[a])

    changed = blob + extra
    if normalise_newlines(changed) == normalise_newlines(blob):
        return  # a pure newline rendering is deliberately NOT drift; see the unit test
    a.write_bytes(changed)
    with pytest.raises(FrozenDriftError, match="alpha.py"):
        assert_frozen(rec.path, params={"k": 1}, code_paths=[a])

    rec2 = freeze(d / "out2", name="p", params={"k": 1}, code_paths=[a])
    assert rec2.content_sha256 != rec.content_sha256


@SETTINGS
@given(params=PARAMS, key=st.text(min_size=1, max_size=6), bump=st.integers(1, 9))
def test_any_param_change_is_caught_and_the_message_names_the_key(tmp_path_factory,
                                                                  params, key, bump):
    d = tmp_path_factory.mktemp("param")
    a = d / "alpha.py"
    a.write_bytes(b"a\n")
    rec = freeze(d / "out", name="p", params=params, code_paths=[a])
    assert_frozen(rec.path, params=params, code_paths=[a])  # silent when unchanged

    moved = dict(params)
    moved[key] = ["changed", bump]  # never equal to a drawn value (ints only, <= 4)
    if canonical_json(moved) == canonical_json(params):
        return
    with pytest.raises(FrozenDriftError) as ei:
        assert_frozen(rec.path, params=moved, code_paths=[a])
    assert repr(key) in str(ei.value)


# ------------------------------------------------- the reserved-slice guard
@SETTINGS
@given(days=st.lists(DAY, max_size=30), cut=DAY)
def test_layer1_and_layer2_agree_and_conserve_the_row_count(days, cut):
    kept = filter_before(days, None, cut)
    assert assert_none_at_or_after(kept, None, cut) is None  # layer 2 accepts layer 1
    assert all(d < cut for d in kept)

    before = window_record(days, None, cut)
    after = window_record(kept, None, cut)
    assert before["sessions_read"] == len(days)
    assert after["sessions_read"] == len(kept)
    assert before["reserved_rows_read"] == len(days) - len(kept)
    assert after["reserved_rows_read"] == 0
    if kept:
        assert after["last_session_read"] < cut
        assert after["first_session_read"] <= after["last_session_read"]


@SETTINGS
@given(days=st.lists(DAY, min_size=1, max_size=30), cut=DAY)
def test_filtering_twice_is_filtering_once(days, cut):
    once = list(filter_before(days, None, cut))
    twice = list(filter_before(once, None, cut))
    assert once == twice


@SETTINGS
@given(start=DAY, end=DAY, probe=DAY)
def test_sealed_window_contains_is_exactly_the_closed_interval(start, end, probe):
    if start > end:
        start, end = end, start
    w = SealedWindow(start, end)
    assert w.contains(probe) == (start <= probe <= end)
    assert w.contains(start) and w.contains(end)
