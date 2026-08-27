"""D224 — the assembled strategy: best window, volume gate, 2-ATR trailing ratchet.

    uv run python scripts/run_assembled_strategy.py
    uv run python scripts/run_assembled_strategy.py --report-only

Offline, deterministic, seeded. `docs/decisions/D224-the-assembled-strategy.md` was
written and committed BEFORE this file existed.

WHY A FACTORIAL AND NOT A STACK
-------------------------------
Three components at once. If the stack is only run whole and it works, nothing is
learned about WHICH part did it. So: parent / +gate / +stop / +both. Four cells
cost the same four looks and expose the INTERACTION, which the D223 census
predicts will be negative — the volume gate selects into loud markets, loud
markets revert (VR 1.35 quiet vs 0.67 loud), and a trailing stop in a reverting
market is a whipsaw generator.

WHY THE RANDOM NULL CARRIES THE VERDICT
---------------------------------------
The parent's average trade earns 14.4 bp (BTC) against a 20 bp round trip, so
REMOVING TRADES AT RANDOM GAINS MONEY. Any component that cuts trade count improves
net PnL mechanically. The matched-count null is the only thing that separates a
real effect from having traded less, and a cell that improves net PnL without
clearing it is reported as a failure.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import math
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.data.cleaner import clean  # noqa: E402
from backtest_framework.data.csv_fixture import (  # noqa: E402
    load_fixture_csv_with_volumes,
)
from backtest_framework.research import macd as M  # noqa: E402
from backtest_framework.simulator.fills import (  # noqa: E402
    StopSide,
    stop_fill_price,
)
from backtest_framework.validation.dsr import expected_max_sharpe  # noqa: E402


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


S = _load("run_sampling_invariance", "run_sampling_invariance.py")  # ppy, sharpe

FIXTURE = REPO / "data" / "fixtures" / "crypto_binance_15m_raw.csv.gz"
SUMMARY = REPO / "data" / "assembled_strategy_summary.json"
RESULTS = REPO / "ASSEMBLED_RESULTS.md"

SYMBOLS = ("BTCUSDT", "ETHUSDT")
BAR_MINUTES = 15
K = 4
LENGTH, SIGNAL = 34 * K, 9 * K  # (136, 36) — the 33-hour channel, selected in D224
VOL_WINDOW = 200  # EMA(200) over SMA(200), same period: diurnally self-cancelling
ATR_WINDOW = 14 * K  # 56 — the standard 14 scaled by the same k
ATR_MULTIPLE = 2.0
FEE_BPS = 10.0  # maker_10bp, the tier the verdict is read at
N_SIMS = 400
SEED = 0
NULL_PERCENTILE = 95.0
MIN_TRADES = 30
MDE_SHARPE = 0.18  # stated in D224 before the run
VERDICT_COUNT = 3833  # D224's declared ledger
FRESH_LOOKS = 10

CELLS = (
    ("A_parent", False, False),
    ("B_gate", True, False),
    ("C_stop", False, True),
    ("D_gate_and_stop", True, True),
)


# --------------------------------------------------------------------------
# Sensors
# --------------------------------------------------------------------------


def ema(values: np.ndarray, window: int) -> np.ndarray:
    alpha = 2.0 / (window + 1.0)
    out = np.empty_like(values)
    out[0] = values[0]
    for i in range(1, len(values)):
        out[i] = alpha * values[i] + (1.0 - alpha) * out[i - 1]
    return out


def sma(values: np.ndarray, window: int) -> np.ndarray:
    out = np.full(values.shape, np.nan)
    if len(values) < window:
        return out
    c = np.cumsum(values)
    out[window - 1] = c[window - 1] / window
    out[window:] = (c[window:] - c[:-window]) / window
    return out


def rolling_atr(high, low, close, window: int) -> np.ndarray:
    """Arithmetic mean of true range — `terrain.mean_true_range`'s convention.

    The repo has no Wilder ATR anywhere and this study does not introduce one.
    `test_rolling_atr_matches_terrains_scalar_version` pins the two together."""
    tr = np.zeros_like(close)
    tr[0] = high[0] - low[0]
    prev = close[:-1]
    tr[1:] = np.maximum(
        high[1:] - low[1:], np.maximum(np.abs(high[1:] - prev), np.abs(low[1:] - prev))
    )
    out = np.full(close.shape, np.nan)
    c = np.cumsum(tr)
    out[window] = (c[window] - c[0]) / window
    out[window + 1 :] = (c[window + 1 :] - c[1 : -window]) / window
    return out


# --------------------------------------------------------------------------
# The book
# --------------------------------------------------------------------------


def build_positions(bars, volumes: np.ndarray, gated: bool, stopped: bool) -> tuple[np.ndarray, dict]:
    """Long-flat exposure held THROUGH each bar, decided from the previous close.

    THE INFORMATION BOUNDARY. The signal for the exposure held through bar t is
    read from bar t-1's close (lag=1, the repo convention). The volume gate is
    read at the same instant. The trailing stop is the one component that looks
    at bar t itself — it must, because a stop is defined by the bar's own range —
    but it can only ever REMOVE exposure from t onward and never add it, and the
    fill is floored at the bar's open so a gap-through cannot fill at the stop.
    """
    high = np.asarray([b.bar.high for b in bars], dtype=float)
    low = np.asarray([b.bar.low for b in bars], dtype=float)
    close = np.asarray([b.bar.close for b in bars], dtype=float)
    open_ = np.asarray([b.bar.open for b in bars], dtype=float)

    start = M.impulse_warm_up_bars(LENGTH, SIGNAL)
    score = M.impulse_signal_score(M.impulse_macd_series(bars, LENGTH, SIGNAL))
    decided = M.positions(score, start=start, long_short=False)
    raw = np.asarray((0.0,) + tuple(decided[:-1]), dtype=float)

    ratio_ok = np.zeros(len(bars), dtype=bool)
    ve, vs = ema(volumes, VOL_WINDOW), sma(volumes, VOL_WINDOW)
    live_gate = np.where(np.isnan(vs), False, ve > vs)
    ratio_ok[1:] = live_gate[:-1]  # read at the decision bar, not the fill bar

    atr = rolling_atr(high, low, close, ATR_WINDOW)

    pos = np.zeros(len(bars), dtype=float)
    ret_override: dict[int, float] = {}
    stop_exits = 0
    gate_blocked = 0
    i = start
    while i < len(bars):
        if raw[i] == 0.0:
            i += 1
            continue
        # A new trade begins at i. The gate decides whether it opens at all.
        if gated and not ratio_ok[i]:
            gate_blocked += 1
            while i < len(bars) and raw[i] != 0.0:
                i += 1
            continue
        stop = -np.inf
        peak = -np.inf
        j = i
        while j < len(bars) and raw[j] != 0.0:
            fill = (
                stop_fill_price(StopSide.SELL_STOP, stop, bars[j].bar)
                if (stopped and stop > -np.inf)
                else None
            )
            if fill is not None:
                # THE STOP BAR IS STILL A HELD BAR. Zeroing the position here
                # would let the book escape the whole adverse move that triggered
                # the stop — look-ahead, and it inflated gross Sharpe to +4.2
                # before it was caught. The book is long from the previous close
                # to the FILL, and the fill comes from `simulator.fills`, which
                # already encodes D10: a gapped stop fills at the OPEN, not the
                # stop price. Restating that here would have been D212 again.
                pos[j] = raw[j]
                ret_override[j] = float(np.log(fill / close[j - 1]))
                stop_exits += 1
                j += 1
                while j < len(bars) and raw[j] != 0.0:
                    j += 1
                break
            pos[j] = raw[j]
            if stopped and np.isfinite(atr[j]):
                peak = max(peak, high[j])
                stop = max(stop, peak - ATR_MULTIPLE * atr[j])
            j += 1
        i = j
    return pos, {
        "start": start,
        "stop_exits": stop_exits,
        "gate_blocked": gate_blocked,
        "open": open_,
        "close": close,
        "low": low,
        "ret_override": ret_override,
    }


def returns_of(close: np.ndarray) -> np.ndarray:
    r = np.zeros_like(close)
    r[1:] = np.log(close[1:] / close[:-1])
    return r


def score_book(pos: np.ndarray, ret: np.ndarray, start: int) -> dict:
    live = pos[start:]
    gross = ret[start:] * live
    cost = np.zeros_like(gross)
    cost[1:] = np.log1p(-(FEE_BPS / 1e4) * np.abs(np.diff(live)))
    net = gross + cost
    years = len(live) / S.ppy(BAR_MINUTES)
    turnover = float(np.abs(np.diff(live)).sum())
    holds = []
    run = 0
    for v in live:
        if v != 0.0:
            run += 1
        elif run:
            holds.append(run)
            run = 0
    if run:
        holds.append(run)
    return {
        "gross_sharpe": S.sharpe(gross, BAR_MINUTES),
        "net_sharpe": S.sharpe(net, BAR_MINUTES),
        "gross_total_return": float(np.expm1(gross.sum())),
        "net_total_return": float(np.expm1(net.sum())),
        "exposure": float(np.mean(np.abs(live))),
        "round_trips": int(turnover / 2),
        "round_trips_per_year": (turnover / 2 / years) if years else 0.0,
        "median_hold_bars": float(np.median(holds)) if holds else 0.0,
        "n_trades": len(holds),
        "years": years,
    }


def trades_of(pos: np.ndarray, ret: np.ndarray, start: int) -> list[tuple[int, int]]:
    out = []
    i = start
    while i < len(pos):
        if pos[i] == 0.0:
            i += 1
            continue
        j = i
        while j < len(pos) and pos[j] != 0.0:
            j += 1
        out.append((i, j))
        i = j
    return out


def random_matched_null(
    parent_pos, ret, start, n_remove: int, n_sims: int, seed: int
) -> tuple[np.ndarray, np.ndarray]:
    """Remove the same COUNT of the parent's trades at random. The only control
    that separates a real effect from having traded less."""
    spans = trades_of(parent_pos, ret, start)
    rng = np.random.default_rng(seed)
    sh = np.empty(n_sims)
    tot = np.empty(n_sims)
    for s in range(n_sims):
        keep = np.ones(len(spans), dtype=bool)
        if 0 < n_remove <= len(spans):
            keep[rng.choice(len(spans), n_remove, replace=False)] = False
        book = np.zeros_like(parent_pos)
        for k, (a, b) in enumerate(spans):
            if keep[k]:
                book[a:b] = parent_pos[a:b]
        sc = score_book(book, ret, start)
        sh[s] = sc["net_sharpe"]
        tot[s] = sc["net_total_return"]
    return sh, tot


def run(cleaned: dict, volume_by_symbol: dict) -> dict:
    rows, per_symbol = [], {}
    for sym in SYMBOLS:
        bars = cleaned[sym]
        vol = volume_by_symbol[sym]
        scored = {}
        parent_pos = None
        for label, gated, stopped in CELLS:
            pos, meta = build_positions(bars, vol, gated, stopped)
            ret = returns_of(meta["close"])
            # The stop bar's return is truncated at the fill, not discarded.
            for idx, value in meta["ret_override"].items():
                ret[idx] = value
            start = meta["start"]
            if label == "A_parent":
                parent_pos, parent_ret, parent_start = pos, ret, start
            sc = score_book(pos, ret, start)
            sc |= {
                "cell": label,
                "gated": gated,
                "stopped": stopped,
                "stop_exits": meta["stop_exits"],
                "gate_blocked": meta["gate_blocked"],
            }
            scored[label] = sc

        parent = scored["A_parent"]
        for label, _, _ in CELLS:
            sc = scored[label]
            removed = max(0, parent["n_trades"] - sc["n_trades"])
            if label == "A_parent" or removed == 0:
                sc |= {
                    "null_sharpe_p95": float("nan"),
                    "null_total_p95": float("nan"),
                    "null_sharpe_sd": float("nan"),
                    "sharpe_pct_in_null": float("nan"),
                    "total_pct_in_null": float("nan"),
                    "H_selectivity": False,
                    "floor_fresh": float("nan"),
                    "floor_verdict": float("nan"),
                    "G_clears_fresh_floor": False,
                    "G_clears_verdict_floor": False,
                }
            else:
                nsh, ntot = random_matched_null(
                    parent_pos, parent_ret, parent_start, removed, N_SIMS, SEED
                )
                p_sh = float((nsh < sc["net_sharpe"]).mean() * 100.0)
                p_tot = float((ntot < sc["net_total_return"]).mean() * 100.0)
                # HURDLE G. var_trials comes from the SIMULATED NULL, not from
                # this study's own cells. D219's amendment recorded that a
                # sweep containing real effects inflates var_trials; here that
                # is extreme — C_stop's -3.17 is a genuine effect, and using
                # the cells puts the floor at +4.9 annualised, which is not a
                # noise floor for anything. The matched-count null IS the null
                # distribution, so its variance is the right estimate.
                var_pp = float(np.var(nsh / math.sqrt(S.ppy(BAR_MINUTES)), ddof=1))
                floor_v = expected_max_sharpe(VERDICT_COUNT, var_pp) * math.sqrt(
                    S.ppy(BAR_MINUTES)
                )
                floor_f = expected_max_sharpe(FRESH_LOOKS, var_pp) * math.sqrt(
                    S.ppy(BAR_MINUTES)
                )
                sc |= {
                    "null_sharpe_p95": float(np.percentile(nsh, NULL_PERCENTILE)),
                    "null_total_p95": float(np.percentile(ntot, NULL_PERCENTILE)),
                    "null_sharpe_sd": float(np.std(nsh, ddof=1)),
                    "sharpe_pct_in_null": p_sh,
                    "total_pct_in_null": p_tot,
                    "H_selectivity": bool(
                        p_sh >= NULL_PERCENTILE and p_tot >= NULL_PERCENTILE
                    ),
                    "floor_fresh": floor_f,
                    "floor_verdict": floor_v,
                    "G_clears_fresh_floor": bool(sc["net_sharpe"] > floor_f),
                    "G_clears_verdict_floor": bool(sc["net_sharpe"] > floor_v),
                }
            sc |= {
                "trades_removed_vs_parent": removed,
                "P_beats_parent": bool(
                    sc["net_sharpe"] > parent["net_sharpe"]
                    and sc["net_total_return"] > parent["net_total_return"]
                ),
                "E_powered": bool(sc["n_trades"] >= MIN_TRADES),
                "symbol": sym,
            }
            rows.append(sc)

        best_part = max(scored["B_gate"]["net_sharpe"], scored["C_stop"]["net_sharpe"])
        per_symbol[sym] = {
            "interaction_net_sharpe": scored["D_gate_and_stop"]["net_sharpe"] - best_part,
            "best_single_component": best_part,
            "full_stack": scored["D_gate_and_stop"]["net_sharpe"],
            "parent_net_sharpe": parent["net_sharpe"],
        }

    return {
        "produced": time.strftime("%Y-%m-%d"),
        "config": {
            "k": K,
            "length": LENGTH,
            "signal": SIGNAL,
            "vol_window": VOL_WINDOW,
            "atr_window": ATR_WINDOW,
            "atr_multiple": ATR_MULTIPLE,
            "fee_bps": FEE_BPS,
            "mde_sharpe": MDE_SHARPE,
        },
        "rows": rows,
        "per_symbol": per_symbol,
        "verdict": verdict(rows, per_symbol),
        "fresh_looks": 10,
        "seed": SEED,
    }


def verdict(rows: list[dict], per_symbol: dict) -> dict:
    clearing_h = [r["cell"] + "/" + r["symbol"] for r in rows if r["H_selectivity"]]
    beating_parent = [
        r["cell"] + "/" + r["symbol"] for r in rows if r["P_beats_parent"]
    ]
    survivors = [
        r["cell"] + "/" + r["symbol"]
        for r in rows
        if r["H_selectivity"]
        and r["P_beats_parent"]
        and r["E_powered"]
        and r["G_clears_verdict_floor"]
    ]
    clears_h_and_p = [
        r["cell"] + "/" + r["symbol"]
        for r in rows
        if r["H_selectivity"] and r["P_beats_parent"] and r["E_powered"]
    ]
    return {
        "cells_clearing_H": clearing_h,
        "cells_beating_parent": beating_parent,
        "survivors": survivors,
        "clear_H_and_P_but_not_G": [
            c for c in clears_h_and_p if c not in survivors
        ],
        "interaction_negative_on_both": all(
            v["interaction_net_sharpe"] < 0 for v in per_symbol.values()
        ),
        "interactions": {s: v["interaction_net_sharpe"] for s, v in per_symbol.items()},
        "mde_sharpe": MDE_SHARPE,
    }


def render(p: dict) -> str:
    out: list[str] = []
    w = out.append
    v, c = p["verdict"], p["config"]
    w("# The assembled strategy — D224")
    w("")
    w(f"**Produced:** {p['produced']} · **Reproduce:** "
      "`uv run python scripts/run_assembled_strategy.py` (offline, deterministic, seed 0) ·")
    w("Record: [`D224`](docs/decisions/D224-the-assembled-strategy.md) ·")
    w("Artifact: `data/assembled_strategy_summary.json`")
    w("")
    w(f"15m bars, Impulse acceleration `({c['length']}, {c['signal']})` (k={c['k']}, a "
      f"33-hour channel) · volume gate `EMA({c['vol_window']}) > SMA({c['vol_window']})` on "
      f"entry only · trailing ratchet at {c['atr_multiple']:.0f}×ATR({c['atr_window']}) · "
      f"net of {c['fee_bps']:.0f} bp per side.")
    w("")
    w("## The factorial")
    w("")
    w("| symbol | cell | gate | stop | net Sharpe | net total | gross Sharpe | RT/yr | hold | trades |")
    w("|---|---|:--:|:--:|---:|---:|---:|---:|---:|---:|")
    for r in p["rows"]:
        w(f"| {r['symbol']} | {r['cell']} | {'y' if r['gated'] else '-'} | "
          f"{'y' if r['stopped'] else '-'} | {r['net_sharpe']:+.3f} | "
          f"{r['net_total_return'] * 100:,.1f}% | {r['gross_sharpe']:+.3f} | "
          f"{r['round_trips_per_year']:,.0f} | {r['median_hold_bars']:,.0f} | "
          f"{r['n_trades']:,} |")
    w("")
    w("## Hurdle H — the matched-count random null")
    w("")
    w("Because the parent's average trade does not cover its fees, **removing trades at")
    w("random gains money**. A cell that improves net PnL without clearing this null has not")
    w("shown selectivity — it has traded less.")
    w("")
    w("| symbol | cell | removed | net Sharpe | null p95 | pct in null (Sh / $) | **H** | beats parent |")
    w("|---|---|---:|---:|---:|---:|:--:|:--:|")
    for r in p["rows"]:
        if r["cell"] == "A_parent":
            continue
        w(f"| {r['symbol']} | {r['cell']} | {r['trades_removed_vs_parent']:,} | "
          f"{r['net_sharpe']:+.3f} | {r['null_sharpe_p95']:+.3f} | "
          f"{r['sharpe_pct_in_null']:.0f} / {r['total_pct_in_null']:.0f} | "
          f"{'PASS' if r['H_selectivity'] else 'FAIL'} | "
          f"{'yes' if r['P_beats_parent'] else 'no'} |")
    w("")
    w("## Hurdle G — the multiplicity floor")
    w("")
    w("**`var_trials` is taken from the simulated null, not from this study's own cells.**")
    w("D219's amendment recorded that a sweep containing real effects inflates it; here that")
    w("is extreme — `C_stop`'s −3.17 is a genuine effect, and using the cells puts the floor")
    w("at **+4.9 annualised**, which is not a noise floor for anything. The matched-count")
    w("null IS the null distribution, so its variance is the right estimate.")
    w("")
    w("| symbol | cell | net Sharpe | null sd | floor @ 10 (fresh) | floor @ 3,833 (verdict) | G |")
    w("|---|---|---:|---:|---:|---:|:--:|")
    for r in p["rows"]:
        if r["cell"] == "A_parent" or r["null_sharpe_sd"] != r["null_sharpe_sd"]:
            continue
        w(f"| {r['symbol']} | {r['cell']} | {r['net_sharpe']:+.3f} | "
          f"{r['null_sharpe_sd']:.3f} | {r['floor_fresh']:+.3f} | "
          f"{r['floor_verdict']:+.3f} | "
          f"{'PASS' if r['G_clears_verdict_floor'] else 'FAIL'} |")
    w("")
    w("## Interaction — is the stack worth more than its parts?")
    w("")
    w("| symbol | best single component | full stack (D) | **interaction** |")
    w("|---|---:|---:|---:|")
    for sym, b in p["per_symbol"].items():
        w(f"| {sym} | {b['best_single_component']:+.3f} | {b['full_stack']:+.3f} | "
          f"**{b['interaction_net_sharpe']:+.3f}** |")
    w("")
    if v["clear_H_and_P_but_not_G"]:
        w("**Cells that clear selectivity and beat the parent, but not the multiplicity")
        w(f"floor: {', '.join(v['clear_H_and_P_but_not_G'])}.** That is D214's pattern — a")
        w("result publishable as a first study is not publishable as the n-th look.")
        w("")
    w(f"**Survivors: {len(v['survivors'])}.** Minimum detectable effect on this fixture is")
    w(f"**{v['mde_sharpe']:.2f} Sharpe** (D222); anything smaller is not a finding here.")
    w("")
    return "\n".join(out) + "\n"


def volume_matrix(cleaned: dict, raw: dict, volumes: dict) -> dict:
    """Volumes aligned to the CLEANED grid by timestamp.

    `TimestampedBar` carries no volume by design (D48/D60), so the series is
    threaded alongside the bars rather than attached to them."""
    out = {}
    for sym in SYMBOLS:
        by_ts = {
            tb.timestamp: v
            for tb, v in zip(raw[sym], volumes[sym], strict=True)
        }
        out[sym] = np.asarray(
            [by_ts[b.timestamp] for b in cleaned[sym]], dtype=float
        )
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()
    if not args.report_only:
        t0 = time.time()
        raw, volumes = load_fixture_csv_with_volumes(FIXTURE)
        cleaned, _ = clean(raw, volumes)
        payload = run(cleaned, volume_matrix(cleaned, raw, volumes))
        SUMMARY.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"wrote {SUMMARY.name} in {time.time() - t0:.1f}s")
    payload = json.loads(SUMMARY.read_text(encoding="utf-8"))
    RESULTS.write_text(render(payload), encoding="utf-8")
    v = payload["verdict"]
    print("survivors:", v["survivors"] or "none")
    print("clearing H:", v["cells_clearing_H"] or "none")
    print("interactions:", {k: round(x, 3) for k, x in v["interactions"].items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
