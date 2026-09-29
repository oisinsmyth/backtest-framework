"""D629 §6's CL/NG extension of scripts/check_sierra_aggressor.py: synthetic inputs only, no market file opened."""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
_spec = importlib.util.spec_from_file_location("check_sierra_aggressor", REPO / "scripts" / "check_sierra_aggressor.py")
K = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(K)


def test_the_selftest_fires_every_guard():
    assert K.selftest() == 0


def test_the_bounds_are_d626s_sample_and_the_principals_rulings():
    assert K.D626_SESSIONS == ("2026-09-21", "2026-10-09")
    assert (K.D629_R_BAR, K.D629_MIN_SESSIONS) == (0.8, 10)
    assert K.CLNG_CONTRACTS == {"CL": ("CLX26", "CLF27"), "NG": ("NGX26", "NGF27")}
    assert K.ENERGY_FROM == dt.date(2026, 10, 11)


def test_a_clng_call_without_run_or_check_is_refused():
    assert K.main(["--root", "CL"]) == 2
    assert K.main(["--root", "NG"]) == 2


def test_the_guard_refuses_before_the_read_even_with_a_marker(tmp_path):
    mk, tj = tmp_path / "m.json", tmp_path / "t.json"
    mk.write_text(json.dumps({"gate": {"verdict": "PASS"}}), encoding="utf-8")
    tj.write_text(json.dumps({"jobs": [{"label": "topup-trades", "downloaded_utc": "x"}]}), encoding="utf-8")
    with pytest.raises(K.CheckError, match="REFUSING"):
        K.d629_guard("CL", today=dt.date(2026, 9, 29), marker=mk, topup_jobs=tj)
    K.d629_guard("CL", today=dt.date(2026, 10, 11), marker=mk, topup_jobs=tj)


def test_the_verdict_counts_sessions_not_pairs():
    # two contracts on the same 6 days = 12 pairs but only 6 sessions: UNRESOLVED under the 10-session floor
    days = [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2026-09-21", periods=6)]
    net = np.arange(12) * 7 - 40
    sc = pd.DataFrame({"contract": ["CLX26"] * 6 + ["CLF27"] * 6, "day": days * 2, "sc_total": 100, "sc_net": net})
    tr = sc.rename(columns={"sc_total": "tr_total", "sc_net": "tr_net"}).assign(clock="ts_recv")
    v = K.d629_verdict(sc, tr)
    assert (v["pairs"], v["sessions"]) == (12, 6)
    assert v["verdict"].startswith("UNRESOLVED")
