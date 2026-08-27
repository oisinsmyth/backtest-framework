"""Scratchpad — does D224's volume-gate result reproduce on 1h bars, no stop?

Reuses run_assembled_strategy.py (ema/sma/score_book/returns_of/random_matched_null/
trades_of/volume_matrix) and run_sampling_invariance.py (ppy/sharpe) unmodified.
Nothing under src/, docs/, scripts/ is touched.
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(r"C:\Users\O\Desktop\Projects\Backtest Framework")
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.data.cleaner import clean  # noqa: E402
from backtest_framework.data.csv_fixture import load_fixture_csv_with_volumes  # noqa: E402
from backtest_framework.research import macd as M  # noqa: E402
from backtest_framework.research.breakout_intraday import census_days, resample  # noqa: E402
from backtest_framework.validation.dsr import expected_max_sharpe  # noqa: E402


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module  # dataclasses resolve __module__ through sys.modules
    spec.loader.exec_module(module)
    return module


S = _load("run_sampling_invariance", "run_sampling_invariance.py")
A = _load("run_assembled_strategy", "run_assembled_strategy.py")

# score_book / random_matched_null read A.BAR_MINUTES for ppy and annualisation.
# Retarget the imported MODULE OBJECT (not the file) so the scoring code is reused
# verbatim at 1h rather than restated (D212).
assert A.BAR_MINUTES == 15 and A.FEE_BPS == 10.0
A.BAR_MINUTES = 60
assert S.ppy(A.BAR_MINUTES) == 8760.0

FIXTURE = REPO / "data" / "fixtures" / "crypto_binance_15m_raw.csv.gz"
SYMBOLS = ("BTCUSDT", "ETHUSDT")
SOURCE_MINUTES = 15
TARGET_MINUTES = 60
LENGTH, SIGNAL = 34, 9        # 1h defaults — the 34-hour channel
N_SIMS, SEED = 400, 0
VERDICT_COUNT, FRESH_LOOKS = 3833, 10

CELLS = (
    ("A_parent", None),
    ("B_gate_matched", 50),    # 50h == 200 x 15min, the wall-clock match to D224
    ("B_gate_literal", 200),   # the literal parameters, 200h
)


def build_positions_1h(bars, volumes: np.ndarray, vol_window: int | None):
    """Long-flat, lag=1, no stop. Gate evaluated at the ENTRY bar only, read at the
    DECISION bar (ratio_ok[1:] = live_gate[:-1]) — D224's semantics exactly."""
    close = np.asarray([b.bar.close for b in bars], dtype=float)

    start = M.impulse_warm_up_bars(LENGTH, SIGNAL)
    score = M.impulse_signal_score(M.impulse_macd_series(bars, LENGTH, SIGNAL))
    decided = M.positions(score, start=start, long_short=False)
    raw = np.asarray((0.0,) + tuple(decided[:-1]), dtype=float)

    ratio_ok = np.zeros(len(bars), dtype=bool)
    if vol_window is not None:
        ve, vs = A.ema(volumes, vol_window), A.sma(volumes, vol_window)
        live_gate = np.where(np.isnan(vs), False, ve > vs)
        ratio_ok[1:] = live_gate[:-1]

    pos = np.zeros(len(bars), dtype=float)
    gate_blocked = 0
    i = start
    while i < len(bars):
        if raw[i] == 0.0:
            i += 1
            continue
        if vol_window is not None and not ratio_ok[i]:
            gate_blocked += 1
            while i < len(bars) and raw[i] != 0.0:
                i += 1
            continue
        j = i
        while j < len(bars) and raw[j] != 0.0:
            pos[j] = raw[j]
            j += 1
        i = j
    return pos, {"start": start, "gate_blocked": gate_blocked, "close": close, "raw": raw}


def hourly_series(cleaned, vol_by_symbol):
    out = {}
    for sym in SYMBOLS:
        bars = cleaned[sym]
        vols = vol_by_symbol[sym]
        census = census_days(bars, source_minutes=SOURCE_MINUTES)
        keep = census.complete
        hb, hv, report = resample(bars, list(vols), TARGET_MINUTES, keep,
                                  source_minutes=SOURCE_MINUTES)
        report.check()
        kept = set(keep)
        fine = [b for b in bars if b.timestamp.date() in kept]
        fine_v = np.asarray([v for b, v in zip(bars, vols) if b.timestamp.date() in kept])
        if len(fine) != len(hb) * 4:
            raise ValueError(f"{sym}: shared calendar did not hold")
        # SANITY: volume must be conserved by the aggregation.
        assert abs(sum(hv) - float(fine_v.sum())) < 1e-6 * max(1.0, float(fine_v.sum()))
        out[sym] = {
            "bars": hb,
            "volumes": np.asarray(hv, dtype=float),
            "n_15m": len(fine),
            "complete_days": len(keep),
            "dropped_days": len(census.incomplete),
            "first": hb[0].timestamp.isoformat(),
            "last": hb[-1].timestamp.isoformat(),
        }
    return out


def main() -> int:
    t0 = time.time()
    raw, volumes = load_fixture_csv_with_volumes(FIXTURE)
    cleaned, _ = clean(raw, volumes)
    volm = A.volume_matrix(cleaned, raw, volumes)
    series = hourly_series(cleaned, volm)

    rows, meta = [], {}
    for sym in SYMBOLS:
        bars = series[sym]["bars"]
        vol = series[sym]["volumes"]
        scored, parent_pack = {}, None
        for label, vw in CELLS:
            pos, m = build_positions_1h(bars, vol, vw)
            ret = A.returns_of(m["close"])
            start = m["start"]
            if label == "A_parent":
                parent_pack = (pos, ret, start)
            sc = A.score_book(pos, ret, start)
            sc |= {"cell": label, "symbol": sym, "vol_window": vw,
                   "gate_blocked": m["gate_blocked"]}
            scored[label] = sc

        parent = scored["A_parent"]
        ppos, pret, pstart = parent_pack
        for label, vw in CELLS:
            sc = scored[label]
            removed = max(0, parent["n_trades"] - sc["n_trades"])
            sc["trades_removed_vs_parent"] = removed
            sc["delta_net_sharpe_vs_parent"] = sc["net_sharpe"] - parent["net_sharpe"]
            sc["delta_gross_sharpe_vs_parent"] = sc["gross_sharpe"] - parent["gross_sharpe"]
            if label == "A_parent" or removed == 0:
                sc |= {k: float("nan") for k in
                       ("null_sharpe_p95", "null_total_p95", "null_sharpe_sd",
                        "null_total_sd", "sharpe_pct_in_null", "total_pct_in_null",
                        "floor_fresh", "floor_verdict")}
                sc["H_selectivity"] = False
            else:
                nsh, ntot = A.random_matched_null(ppos, pret, pstart, removed, N_SIMS, SEED)
                p_sh = float((nsh < sc["net_sharpe"]).mean() * 100.0)
                p_tot = float((ntot < sc["net_total_return"]).mean() * 100.0)
                var_pp = float(np.var(nsh / math.sqrt(S.ppy(60)), ddof=1))
                sc |= {
                    "null_sharpe_p95": float(np.percentile(nsh, 95.0)),
                    "null_total_p95": float(np.percentile(ntot, 95.0)),
                    "null_sharpe_sd": float(np.std(nsh, ddof=1)),
                    "null_total_sd": float(np.std(ntot, ddof=1)),
                    "null_sharpe_mean": float(np.mean(nsh)),
                    "null_total_mean": float(np.mean(ntot)),
                    "sharpe_pct_in_null": p_sh,
                    "total_pct_in_null": p_tot,
                    "H_selectivity": bool(p_sh >= 95.0 and p_tot >= 95.0),
                    "floor_fresh": expected_max_sharpe(FRESH_LOOKS, var_pp) * math.sqrt(S.ppy(60)),
                    "floor_verdict": expected_max_sharpe(VERDICT_COUNT, var_pp) * math.sqrt(S.ppy(60)),
                }
                sc["clears_fresh_floor"] = bool(sc["net_sharpe"] > sc["floor_fresh"])
                sc["clears_verdict_floor"] = bool(sc["net_sharpe"] > sc["floor_verdict"])
            sc["P_beats_parent"] = bool(
                sc["net_sharpe"] > parent["net_sharpe"]
                and sc["net_total_return"] > parent["net_total_return"]
            )
            rows.append(sc)
        meta[sym] = {k: series[sym][k] for k in
                     ("n_15m", "complete_days", "dropped_days", "first", "last")}
        meta[sym]["n_1h"] = len(bars)
        meta[sym]["warm_up_bars"] = parent["n_trades"] and M.impulse_warm_up_bars(LENGTH, SIGNAL)

    payload = {"rows": rows, "calendar": meta,
               "config": {"bar_minutes": 60, "length": LENGTH, "signal": SIGNAL,
                          "fee_bps": A.FEE_BPS, "n_sims": N_SIMS, "seed": SEED,
                          "ppy": S.ppy(60)}}
    out = Path(__file__).with_name("gate_1h_summary.json")
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, default=float) + "\n",
                   encoding="utf-8")

    hdr = f"{'sym':<8} {'cell':<16} {'grossSh':>8} {'netSh':>8} {'gross$':>10} {'net$':>10} {'exp':>6} {'trades':>7} {'RT/yr':>7} {'hold':>5} {'blk':>5}"
    print(hdr)
    for r in rows:
        print(f"{r['symbol']:<8} {r['cell']:<16} {r['gross_sharpe']:+8.3f} {r['net_sharpe']:+8.3f} "
              f"{r['gross_total_return']*100:9.1f}% {r['net_total_return']*100:9.1f}% "
              f"{r['exposure']:6.3f} {r['n_trades']:7d} {r['round_trips_per_year']:7.0f} "
              f"{r['median_hold_bars']:5.0f} {r['gate_blocked']:5d}")
    print()
    print(f"{'sym':<8} {'cell':<16} {'rmvd':>5} {'netSh':>8} {'nullp95':>8} {'nullsd':>7} {'pctSh':>6} {'pct$':>6} {'H':>5} {'fl@10':>7} {'fl@3833':>8}")
    for r in rows:
        if r["cell"] == "A_parent":
            continue
        print(f"{r['symbol']:<8} {r['cell']:<16} {r['trades_removed_vs_parent']:5d} "
              f"{r['net_sharpe']:+8.3f} {r['null_sharpe_p95']:+8.3f} {r['null_sharpe_sd']:7.3f} "
              f"{r['sharpe_pct_in_null']:6.1f} {r['total_pct_in_null']:6.1f} "
              f"{'PASS' if r['H_selectivity'] else 'FAIL':>5} "
              f"{r['floor_fresh']:+7.3f} {r['floor_verdict']:+8.3f}")
    print()
    for sym, m in meta.items():
        print(sym, m)
    print(f"done in {time.time()-t0:.1f}s -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
