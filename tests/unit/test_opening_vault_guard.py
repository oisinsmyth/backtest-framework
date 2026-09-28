"""Phase 0b of the opening model (deposit test 18; OPENING_AGENT_STATE_PREREG.md s.13 line 353): the vault guard
covers ES, NQ, SPY, QQQ and the ES/NQ options data for 2025-03-01 -> 2026-09-18.

Each of the model's loaders is fed a SYNTHETIC frame or file holding one in-sample session (2025-02-28) and one vault
session (2025-03-03), and must hand the model the first and never the second. The guards are then broken on purpose
and must RAISE (the assert layer behind the filter), because a guard that cannot fail is worse than none. No real
market data is read.
"""
from __future__ import annotations

import gzip
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from backtest_framework.validation.frozen import ReservedSliceError  # noqa: E402

IN, VAULT, CUT = "2025-02-28", "2025-03-03", "2025-03-01"


def _load(name: str, fn: str):
    if name in sys.modules:
        return sys.modules[name]
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    assert s is not None and s.loader is not None
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


def _gz_csv(path: Path, df: pd.DataFrame) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8", compression="gzip")
    return path


def _bars(tmp: Path) -> Path:
    rows = [{"root": r, "session": s, "hhmm": "09:30", "open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0,
             "volume": 1} for r in ("ES", "NQ") for s in (IN, VAULT)]
    return _gz_csv(tmp / "bars.csv.gz", pd.DataFrame(rows))


def _etf_slices(root: Path) -> None:
    for sym in ("SPY", "QQQ"):
        for month, day in (("2025-02", IN), ("2025-03", VAULT)):
            p = root / "raw" / "alphavantage" / "1min" / sym / f"{month}.json.gz"
            p.parent.mkdir(parents=True, exist_ok=True)
            ser = {f"{day} {hm}:00": {"2. high": "1", "3. low": "1", "4. close": "1"} for hm in ("09:30", "15:59")}
            with gzip.open(p, "wt", encoding="utf-8") as fh:
                json.dump({"Time Series (1min)": ser}, fh)


def _es_options(root: Path) -> None:
    fx = root / "fixtures"
    _gz_csv(fx / "fut_es_options_eod.csv.gz", pd.DataFrame(
        [{"session": s, "right": "C", "strike": 5000.0, "expiry_date": "2025-03-21", "expiry_hhmm": "09:30",
          "underlying": "ESH5", "oi": 100, "settle": 60.0} for s in (IN, VAULT)]))
    days = [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2025-02-18", "2025-03-31")]
    _gz_csv(fx / "cme_session_calendar.csv.gz", pd.DataFrame({"root": "ES", "day": days, "is_trading": 1}))
    _gz_csv(fx / "fut_settle_strip.csv.gz", pd.DataFrame(
        [{"root": "ES", "contract": "ESH5", "ref": d, "settle": 5000.0} for d in days]))


def _scid(sc: Path, sym: str, days: list[str], rec: np.dtype) -> None:
    epoch = pd.Timestamp("1899-12-30")
    r = np.zeros(len(days), dtype=rec)
    for i, d in enumerate(days):
        t = pd.Timestamp(f"{d} 09:35", tz="America/New_York").tz_convert("UTC").tz_localize(None)
        r[i]["dt"] = int((t - epoch) / pd.Timedelta(microseconds=1))
        r[i]["v"], r[i]["av"], r[i]["n"] = 1, 1, 1
    sc.mkdir(parents=True, exist_ok=True)
    (sc / f"{sym}-CME.scid").write_bytes(b"\0" * 56 + r.tobytes())


def test_opening_18_the_vault_guard_covers_every_opening_input(tmp_path, monkeypatch) -> None:
    """ES/NQ bars, SPY/QQQ, the ES options (A4), the NQ options fixture, A7 from Sierra ticks, and the Phase 4 loader
    of agents.csv and a7.csv: each keeps 2025-02-28 and never passes 2025-03-03."""
    # ES/NQ one-minute bars (Gate O0, labels, the stage runner's load)
    G0 = _load("opening_gate0", "opening_gate0.py")
    monkeypatch.setattr(G0, "BARS", _bars(tmp_path))
    b = G0.load_bars()
    assert set(b["session"]) == {IN}
    # SPY/QQQ (A6) through the agents builder
    B = _load("build_opening_agents", "build_opening_agents.py")
    _etf_slices(tmp_path)
    for sym in ("SPY", "QQQ"):
        e = B.etf_frame(sym, tmp_path, ["2025-02", "2025-03"])
        assert list(e.index) == [IN], sym
    # ES options (A4's dealer gamma): the vault session gets no G
    _es_options(tmp_path)
    g = B.dealer_gamma("ES", tmp_path, [IN, VAULT])
    assert np.isfinite(g[IN]) and not np.isfinite(g[VAULT])
    # NQ options fixture: layer 2 drops, layer 3 raises
    N = _load("build_fut_nq_options_eod", "build_fut_nq_options_eod.py")
    t = pd.DataFrame({"session": [IN, VAULT], "oi_ref_session": ["2025-02-27", IN],
                      "oi_pub_et": ["2025-02-27T21:00", "2025-02-28T21:00"]})
    kept = N.filter_before(t, "session", N.RESERVED_FROM)
    assert list(kept["session"]) == [IN]
    N.vault_check(kept)
    with pytest.raises(ReservedSliceError):
        N.vault_check(t)
    # A7 from Sierra's tick files: the vault session is never a row
    A = _load("build_opening_a7", "build_opening_a7.py")
    sessions = ["2025-02-26", "2025-02-27", IN, VAULT]
    _gz_csv(tmp_path / "fixtures" / "fut_index_sessions.csv.gz",
            pd.DataFrame({"root": "ES", "day": sessions, "contract": "ESH5"}))
    _scid(tmp_path / "sc", "ESH25", sessions, A.REC)
    monkeypatch.setattr(A, "SC_DATA", tmp_path / "sc")
    monkeypatch.setattr(A, "META", tmp_path / "a7.meta.json")
    res = A.build(tmp_path)
    assert VAULT not in set(res["session"]) and IN in set(res["session"])
    # the Phase 4-5 loader of the derived files
    P = _load("opening_phase45", "opening_phase45.py")
    monkeypatch.setattr(P, "R", SimpleNamespace(ROOTS=("ES", "NQ"), CHECKPOINTS=("10:00",)), raising=False)
    od = tmp_path / "od"
    od.mkdir()
    pd.DataFrame([{"root": r, "session": s, **{f"z{k}": 1.0 for k in range(1, 7)}} for r in ("ES", "NQ")
                  for s in (IN, VAULT)]).to_csv(od / "agents.csv", index=False)
    pd.DataFrame([{"root": r, "session": s, "a7_10:00": 0.1} for r in ("ES", "NQ")
                  for s in (IN, VAULT)]).to_csv(od / "a7.csv", index=False)
    ag = P.load_agents(od)
    for r in ("ES", "NQ"):
        assert list(ag[r].index) == [IN], r


@pytest.mark.parametrize("module,fn", [("opening_gate0", "opening_gate0.py"),
                                       ("build_opening_agents", "build_opening_agents.py"),
                                       ("opening_phase45", "opening_phase45.py")])
def test_a_broken_filter_leaves_the_assert_layer_to_raise(tmp_path, monkeypatch, module, fn) -> None:
    """Break each loader's filter (identity): the vault row reaches the assert layer, which must raise."""
    M = _load(module, fn)
    monkeypatch.setattr(M, "filter_before", lambda df, col, cut: df)
    frame = pd.DataFrame({"session": [IN, VAULT], "day": [IN, VAULT]})
    with pytest.raises(ReservedSliceError):
        if module == "opening_gate0":
            monkeypatch.setattr(M, "BARS", _bars(tmp_path))
            M.load_bars()
        elif module == "build_opening_agents":
            M.cut(frame, "day")
        else:
            M._sealed(frame)
