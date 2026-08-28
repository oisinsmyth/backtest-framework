"""A loader for a RAGGED panel — the one D252's dead-inclusive fixture needs.

`run_macd_ladder.load_panel` refuses a panel whose symbols have different bar
counts, and THAT REQUIREMENT IS EXACTLY WHAT DELETES DEAD NAMES. A company that
delists in 2014 cannot be present on every date, so a rectangular panel silently
drops the cohort a short study exists to measure.

THE CONTRACT, fixed in D256 before this file was written:

  1. PER-SYMBOL LIVE WINDOWS. A symbol contributes only between its own first and
     last bar. Outside it the return is zero and THE POSITION IS FORCED TO ZERO.
  2. EQUAL WEIGHT OVER LIVE NAMES, NOT OVER `n`. The portfolio return at bar `t`
     is the mean over names live at `t`. Dividing by a constant `n` would shrink
     every early-period return -- the defect class behind D244's "BTC alone at
     1/35 weight" error, which reported +1.13% for a +48.15% series.
  3. A DELISTING IS AN EXIT AT THE LAST AVAILABLE PRICE, DECIDED WITH NO
     FOREKNOWLEDGE. The rule may not see that a name dies.
  4. NO FORWARD-FILLING. A fabricated price is a fabricated return.

Indicators are computed on each symbol's OWN contiguous series and scattered into
the global grid at that symbol's date indices, so a 252-bar window always means
252 of that symbol's bars.
"""

from __future__ import annotations

import csv
import gzip
import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class Bar:
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class Stamped:
    timestamp: str
    bar: Bar


class RaggedPanel:
    """(n, T) grids over the union date grid, plus the `live` mask that makes them
    honest. `closes` is NaN outside a symbol's window so a misuse raises rather
    than silently reading a fabricated price."""

    def __init__(self, symbols, dates, closes, log_returns, total_log_returns,
                 cost_fraction, live, index_of):
        self.symbols = symbols
        self.dates = dates
        self.closes = closes
        self.log_returns = log_returns
        self.total_log_returns = total_log_returns
        self.cost_fraction = cost_fraction
        self.live = live
        self.index_of = index_of          # symbol -> (t0, t1) inclusive on the grid

    @property
    def shape(self):
        return self.closes.shape

    def n_live(self):
        return self.live.sum(axis=0)


def assert_gates_passed(fixture: Path) -> dict:
    """Refuse a fixture whose meta does not assert its own gates passed.

    D256 was run against an intermediate build that had printed `GATES FAILED`
    and been left on disk. The file decompressed to EOF cleanly -- which rules out
    truncation and NOTHING ELSE -- and its meta carried the failing gate report in
    a key the caller read straight past. It contained a x300 and a x66.7 fabricated
    single-bar return, on the short side, where an up-spike is the loss.

    THE LOADER IS THE CHOKEPOINT EVERY STUDY GOES THROUGH, so the check belongs
    here rather than in each runner's preamble."""
    meta_path = fixture.with_suffix("").with_suffix(".meta.json")
    if not meta_path.exists():
        raise FileNotFoundError(f"{fixture.name}: no meta.json beside it -- cannot verify gates")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    gates = meta.get("gates")
    if not isinstance(gates, dict):
        raise ValueError(f"{fixture.name}: meta has no `gates` block; refusing to load")
    # ONLY a block carrying an explicit `failures` list is a gate. The same object
    # also holds REPORTS -- `largest_25_moves`, `unconfirmed_splits`,
    # `moves_across_a_trading_halt`, `excluded_for_data_quality` -- which describe
    # what the build found and rejected. A first version of this check read those
    # as failures and refused a clean fixture, which is the mirror of the error it
    # exists to prevent: a check that cannot pass is as useless as one that cannot
    # fail.
    gate_names = [k for k, v in gates.items() if isinstance(v, dict) and "failures" in v]
    if not gate_names:
        raise ValueError(f"{fixture.name}: meta `gates` block declares no gate with a "
                         "`failures` list; refusing to load")
    failed = {k: len(gates[k]["failures"]) for k in gate_names
              if isinstance(gates[k]["failures"], list) and gates[k]["failures"]}
    if failed:
        raise ValueError(
            f"{fixture.name}: GATES FAILED {failed} -- this fixture is not fit to load. "
            "Rebuild it; do not work around this check.")
    return meta


def load_ragged(fixture: Path, events: Path | None, *, fee_bps: float,
                require_gates: bool = True) -> tuple[RaggedPanel, dict]:
    if require_gates:
        assert_gates_passed(fixture)
    rows: dict[str, list] = {}
    with gzip.open(fixture, "rt") as f:
        for r in csv.DictReader(f):
            rows.setdefault(r["symbol"], []).append(
                (r["timestamp"][:10], float(r["open"]), float(r["high"]),
                 float(r["low"]), float(r["close"]), float(r["volume"])))

    symbols = sorted(rows)
    for s in symbols:
        rows[s].sort()
    grid = sorted({d for s in symbols for d, *_ in rows[s]})
    pos_of = {d: i for i, d in enumerate(grid)}
    n, T = len(symbols), len(grid)

    closes = np.full((n, T), np.nan)
    live = np.zeros((n, T), dtype=bool)
    index_of, cleaned, holes = {}, {}, {}

    for i, s in enumerate(symbols):
        idx = np.array([pos_of[d] for d, *_ in rows[s]], dtype=int)
        # CONTIGUITY: a symbol with internal holes would make "252 bars" mean
        # something different from 252 sessions. Measured, never assumed.
        gaps = int(np.sum(np.diff(idx) != 1))
        if gaps:
            holes[s] = gaps
        closes[i, idx] = [c for _d, _o, _h, _l, c, _v in rows[s]]
        live[i, idx] = True
        index_of[s] = (int(idx[0]), int(idx[-1]))
        cleaned[s] = [Stamped(d, Bar(o, h, l, c, v)) for d, o, h, l, c, v in rows[s]]

    # returns are computed WITHIN each symbol's own series, never across its gap
    log_returns = np.zeros((n, T))
    for i, s in enumerate(symbols):
        idx = np.array([pos_of[d] for d, *_ in rows[s]], dtype=int)
        px = np.log(closes[i, idx])
        log_returns[i, idx[1:]] = np.diff(px)

    total = log_returns.copy()
    div_count = 0
    if events is not None and Path(events).exists():
        ev = json.loads(Path(events).read_text(encoding="utf-8"))
        payload = ev.get("dividends", ev) if isinstance(ev, dict) else ev
        index_by_symbol = {s: i for i, s in enumerate(symbols)}
        for s, items in (payload.items() if isinstance(payload, dict) else []):
            i = index_by_symbol.get(s)
            if i is None:
                continue
            for it in items:
                # two shapes in the wild: ["2016-11-08T00:00:00", 0.09] and
                # {"date": ..., "amount": ...}. Both handled, neither assumed.
                if isinstance(it, (list, tuple)):
                    d, amt = str(it[0])[:10], float(it[1])
                else:
                    d = str(it.get("date") or it.get("ex_date") or "")[:10]
                    amt = float(it.get("amount", it.get("dividend", 0.0)) or 0.0)
                t = pos_of.get(d)
                if t is None or amt <= 0.0 or not live[i, t] or np.isnan(closes[i, t]):
                    continue
                total[i, t] += math.log1p(amt / closes[i, t])
                div_count += 1

    meta = {
        "n_symbols": n, "bars": T, "span": (grid[0], grid[-1]),
        "symbols_with_internal_holes": len(holes),
        "worst_hole_count": max(holes.values()) if holes else 0,
        "dividends_applied": div_count,
        "median_bars_per_symbol": int(np.median(live.sum(axis=1))),
        "min_bars_per_symbol": int(live.sum(axis=1).min()),
        "names_live_at_start": int(live[:, 0].sum()),
        "names_live_at_end": int(live[:, -1].sum()),
    }
    panel = RaggedPanel(symbols, grid, closes, log_returns, total,
                        np.full(n, fee_bps / 1e4), live, index_of)
    return panel, cleaned


# --------------------------------------------------------------------------
# scoring, live-aware
# --------------------------------------------------------------------------


def enforce_live(position: np.ndarray, panel: RaggedPanel, start: int) -> np.ndarray:
    """Contract point 1 and 3: no exposure outside a symbol's own window, and a
    delisting closes the position at the last available bar."""
    out = position * panel.live
    out[:, :start] = 0.0
    return out


def pooled_returns(panel: RaggedPanel, position: np.ndarray, start: int) -> np.ndarray:
    """Contract point 2: the mean is over LIVE names, never over `n`."""
    pos = enforce_live(position, panel, start)
    sm = np.expm1(panel.total_log_returns) * panel.live
    turn = np.abs(np.diff(pos, axis=1, prepend=0.0))
    gross = (pos * sm).sum(axis=0)
    cost = (panel.cost_fraction[:, None] * turn).sum(axis=0)
    denom = np.maximum(panel.n_live(), 1)
    return ((gross - cost) / denom)[start:]


def legs(panel: RaggedPanel, position: np.ndarray, start: int):
    pos = enforce_live(position, panel, start)[:, start:]
    denom = np.maximum(panel.n_live()[start:], 1)
    return (float((np.maximum(pos, 0.0).sum(axis=0) / denom).mean()),
            float((np.maximum(-pos, 0.0).sum(axis=0) / denom).mean()))


def score(panel: RaggedPanel, position: np.ndarray, start: int, *,
          ppy: float, rf_annual: float, borrow_annual: float) -> dict:
    r = pooled_returns(panel, position, start)
    long_f, short_f = legs(panel, position, start)
    rf = math.expm1(math.log1p(rf_annual) / ppy)
    bor = math.expm1(math.log1p(borrow_annual) / ppy)
    ex = r - long_f * rf - short_f * bor
    sd = float(np.std(ex, ddof=1))
    eq = np.cumprod(1.0 + r)
    yrs = len(r) / ppy
    dd = eq / np.maximum.accumulate(eq) - 1.0
    pos = enforce_live(position, panel, start)
    active = (pos != 0.0).astype(float)
    entries_per = np.sum(np.diff(active, axis=1, prepend=0.0)[:, start:] > 0.0, axis=1)
    traded = entries_per[entries_per > 0]
    edge = float(np.mean(r)) * ppy
    expo = long_f + short_f
    return {
        "excess_sharpe": (float(np.mean(ex)) / sd * math.sqrt(ppy)) if sd > 0 else 0.0,
        "terminal_multiple": float(eq[-1]),
        "cagr": float(eq[-1] ** (1.0 / yrs) - 1.0) if eq[-1] > 0 else -1.0,
        "total_return": float(eq[-1] - 1.0),
        "vol": float(np.std(r, ddof=1) * math.sqrt(ppy)),
        "max_drawdown": float(dd.min()),
        "worst_bar": float(r.min()),
        "exposure_gross": expo,
        "exposure_long": long_f, "exposure_short": short_f,
        # FINDINGS section 1a -- reported as the PRODUCT, never the edge alone
        "gross_edge_annual": edge,
        "edge_per_unit_exposure": float(edge / expo) if expo > 0 else float("nan"),
        "entries": int(entries_per.sum()),
        "symbols_traded": int((entries_per > 0).sum()),
        "min_entries_per_traded_symbol": int(traded.min()) if len(traded) else 0,
        "turnover_units": float(np.abs(np.diff(pos, axis=1)).sum()),
        "clears_E": bool(entries_per.sum() >= 100 and len(traded) > 0 and traded.min() >= 30),
    }


def rotation_null(panel: RaggedPanel, position: np.ndarray, start: int, *, n_sims: int,
                  seed: int, ppy: float, rf_annual: float, borrow_annual: float):
    """Matched-count rotation, ROLLED WITHIN EACH SYMBOL'S OWN LIVE WINDOW.

    Rolling across the whole grid would place exposure on bars where the name did
    not exist, which `enforce_live` would then delete -- silently lowering the
    null's exposure and making the hurdle easier. Rolled inside the window instead."""
    rng = np.random.default_rng(seed)
    pos = enforce_live(position, panel, start)
    sh = np.empty(n_sims)
    mn = np.empty(n_sims)
    windows = [panel.index_of[s] for s in panel.symbols]
    for k in range(n_sims):
        rot = np.zeros_like(pos)
        for i, (a, b) in enumerate(windows):
            seg = pos[i, a:b + 1]
            if seg.size > 1:
                rot[i, a:b + 1] = np.roll(seg, int(rng.integers(0, seg.size)))
        sc = score(panel, rot, start, ppy=ppy, rf_annual=rf_annual,
                   borrow_annual=borrow_annual)
        sh[k] = sc["excess_sharpe"]
        mn[k] = sc["total_return"]
    return sh, mn


def concurrency(panel: RaggedPanel, position: np.ndarray, start: int, seed: int = 0) -> dict:
    """R10, normalised by LIVE names so a growing universe is not read as crowding."""
    pos = enforce_live(position, panel, start)[:, start:]
    lv = panel.live[:, start:]
    held = pos != 0.0
    n, T = held.shape
    rng = np.random.default_rng(seed)
    rot = np.zeros_like(held)
    for i in range(n):
        idx = np.flatnonzero(lv[i])
        if idx.size > 1:
            rot[i, idx] = np.roll(held[i, idx], int(rng.integers(0, idx.size)))
    nl = np.maximum(lv.sum(axis=0), 1)
    a, r = held.sum(axis=0), rot.sum(axis=0)
    return {
        "mean_held": float(a.mean()), "max_held": int(a.max()),
        "mean_share_of_live": float((a / nl).mean()),
        "max_share_of_live": float((a / nl).max()),
        "rot_mean_held": float(r.mean()), "rot_max_held": int(r.max()),
        "sd_ratio": float(a.std() / r.std()) if r.std() > 0 else float("nan"),
    }


def effective_instruments(panel: RaggedPanel, start: int, min_overlap: int = 250) -> float:
    """1 / (w' R w) at equal weights, on pairs with enough overlapping bars."""
    r, lv = panel.log_returns[:, start:], panel.live[:, start:]
    n = r.shape[0]
    R = np.eye(n)
    for i in range(n):
        for j in range(i + 1, n):
            m = lv[i] & lv[j]
            if m.sum() >= min_overlap:
                a, b = r[i][m], r[j][m]
                if a.std() > 0 and b.std() > 0:
                    R[i, j] = R[j, i] = float(np.corrcoef(a, b)[0, 1])
    return float(n * n / R.sum())
