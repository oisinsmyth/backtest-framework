"""Golden tests for `data/attention.py` (D612).

Hand arithmetic in `test_attention_ledger.hand.txt`, per CONTRIBUTING step 2: every number below
was produced by two calculators that never import this codebase — GNU `awk` with `%.17g` and GNU
`sha256sum` fed by `printf` in Git Bash, and .NET's `[Math]::Sqrt` and
`System.Security.Cryptography.SHA256` over a literal `[byte[]]` from PowerShell — and they agreed
on every line. The anchor case asserts the published SHA-256 of the empty string, so a suite where
`hashlib` had been swapped for something else fails on the first assertion rather than on a subtle
one.

WHY THIS TIER. Three of the four cases are POINT-IN-TIME BOUNDARIES, and a boundary is money in
the sense a fill price is: a feature that reads one minute early is not slightly optimistic, it is
a look-ahead, and nothing downstream can detect it afterwards. R9 is the price list — a monotone
effect spanning 465 percentage points that vanished entirely once its conditioner was lagged by
one bar. The fourth is a digest, which belongs here for D551's reason: one writer that did not pin
its newline gave the same fixture two snapshot ids on two operating systems, and a snapshot id is
the provenance identifier logged with every trial.

Every input here is a literal written into the test. `data/fixtures/attention_sample.csv.gz` is
NOT read: a golden that reads a fixture pins the fixture and not the arithmetic. No market bar is
read, no return is computed, and no row dated 2024-01-01 or later is touched.
"""

from __future__ import annotations

import datetime as dt
import hashlib
from pathlib import Path

import pytest

from backtest_framework.data.attention import (
    att_accel,
    queries_hash,
    wiki_available_at,
    wiki_is_available,
    zscore_matched,
)
from backtest_framework.validation.frozen import sha256_file

UTC = dt.timezone.utc

# --- the hand ledger's constants, transcribed from test_attention_ledger.hand.txt -------------
SHA_EMPTY = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
SHA_Q_LF = "0c592012e55d5c2b9276e20810ac978c14250f0c01bd207b5e58b94446475222"
SHA_Q_CRLF = "df3f65a3f31eecfeaa4a220bda2864ef4fe773bd8aac28a2a43afb5bad89180a"

# Case 2: five matched Mondays at hour 14, values 10..18; the scored value is 20.
SD_HAND = 3.1622776601683795          # sqrt(10), ddof = 1
Z_HAND = 1.8973665961010275           # 6 / sqrt(10) = 3*sqrt(10)/5

# Case 1: the 13:00-14:00 hour is available at 14:15:00Z and at no earlier instant.
HOUR = dt.datetime(2019, 11, 4, 13, 0, tzinfo=UTC)
AVAILABLE_AT = dt.datetime(2019, 11, 4, 14, 15, 0, tzinfo=UTC)

HAND = Path(__file__).with_suffix(".hand.txt")


def test_the_hand_ledger_is_present_and_names_its_two_calculators():
    """A golden whose companion has been deleted is a golden with no ground truth."""
    text = HAND.read_text(encoding="utf-8")
    assert "sha256sum" in text and "System.Security.Cryptography.SHA256" in text
    assert SHA_EMPTY in text and Z_HAND.__repr__() in text
    for case in ("Case 1", "Case 2", "Case 3", "Case 4"):
        assert case in text


def test_the_anchor_two_independent_calculators_agree_on_sha256_of_nothing():
    assert hashlib.sha256(b"").hexdigest() == SHA_EMPTY


# ---------------------------------------------------------------- Case 1, the 14:15 boundary
def test_case1_the_pageview_publication_boundary():
    assert wiki_available_at(HOUR) == AVAILABLE_AT
    # 13*3600 + 3600 + 900 = 51300 s past midnight = 14:15:00, the hand ledger's arithmetic.
    assert (AVAILABLE_AT - AVAILABLE_AT.replace(hour=0, minute=0)).total_seconds() == 51300

    for probe, want in (
        (dt.time(14, 9, 59), False),
        (dt.time(14, 10, 0), False),      # test 22, first half
        (dt.time(14, 14, 59), False),     # one second short
        (dt.time(14, 15, 0), True),       # test 22, second half
        (dt.time(14, 15, 1), True),
    ):
        tau = dt.datetime.combine(HOUR.date(), probe, tzinfo=UTC)
        assert wiki_is_available(HOUR, tau) is want, (probe, want)


# ------------------------------------------------------------------ Case 2, the matched z-score
MONDAYS = [(dt.date(2019, 9, 30) + dt.timedelta(days=7 * k), 14, 10.0 + 2.0 * k) for k in range(5)]
SCORED = (dt.date(2019, 11, 4), 14, 20.0)


def test_case2_the_matched_zscore():
    assert [d.weekday() for d, _h, _v in MONDAYS] == [0] * 5
    assert SCORED[0].weekday() == 0
    assert [v for _d, _h, v in MONDAYS] == [10.0, 12.0, 14.0, 16.0, 18.0]

    z = zscore_matched([*MONDAYS, SCORED], SCORED[0], 14)
    assert z == pytest.approx(Z_HAND, abs=1e-15)
    # and the closed form, computed a third way inside the test rather than copied:
    assert z == pytest.approx(6.0 / SD_HAND, abs=0.0)
    assert SD_HAND == pytest.approx(10.0**0.5, abs=0.0)


def test_case2_the_ddof_choice_is_the_one_the_hand_ledger_names():
    """ddof=1, not 0. With ddof=0 the same five numbers give sd = sqrt(8) and z = 2.1213…, a 12%
    larger score that would move a `z > 2` breadth count. The hand ledger records the alternative
    so that the choice is visible as a choice."""
    z = zscore_matched([*MONDAYS, SCORED], SCORED[0], 14)
    ddof0 = 6.0 / (8.0**0.5)
    assert ddof0 == pytest.approx(2.1213203435596424, abs=1e-15)
    assert abs(z - ddof0) > 0.2


# -------------------------------------------------------------------- Case 3, the accel ramp
BASE = dt.datetime(2019, 11, 4, 9, 0, tzinfo=UTC)


def test_case3_att_accel_on_the_hand_ledgers_ramp_and_flat():
    ramp = {BASE + dt.timedelta(hours=k): v
            for k, v in enumerate([0.5, 0.5, 0.5, 1.5, 2.5, 3.5])}
    assert att_accel(ramp, BASE + dt.timedelta(hours=5)) == pytest.approx(2.0, abs=1e-15)

    flat = {BASE + dt.timedelta(hours=6 + k): 3.5 for k in range(6)}
    # EXACTLY zero, not "about zero": the two means are the same doubles in the same order.
    assert att_accel(flat, BASE + dt.timedelta(hours=11)) == 0.0


# ------------------------------------------------------------------- Case 4, the newline pin
def test_case4_queries_hash_is_lf_pinned(tmp_path: Path):
    crlf = tmp_path / "QUERIES.md"
    crlf.write_bytes(b"# Q\r\n- Natural_gas\r\n")     # write_bytes, never write_text (D551)
    assert crlf.stat().st_size == 20

    assert queries_hash(crlf) == SHA_Q_LF
    assert sha256_file(crlf, text_normalise=False) == SHA_Q_CRLF
    assert SHA_Q_LF != SHA_Q_CRLF

    lf = tmp_path / "same.md"
    lf.write_bytes(b"# Q\n- Natural_gas\n")
    assert lf.stat().st_size == 18
    assert queries_hash(lf) == SHA_Q_LF            # one identity for one content
    assert hashlib.sha256(b"# Q\n- Natural_gas\n").hexdigest() == SHA_Q_LF

    # Tampering moves it: one appended byte, a different digest.
    with open(crlf, "ab") as fh:
        fh.write(b"x")
    assert queries_hash(crlf) != SHA_Q_LF
