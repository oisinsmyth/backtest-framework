"""D221 — does Impulse MACD care about the sampling rate, or only about the window?

    uv run python scripts/run_sampling_invariance.py
    uv run python scripts/run_sampling_invariance.py --report-only

Offline, deterministic. `docs/decisions/D221-does-the-indicator-care-about-sampling-rate.md`
was written and committed BEFORE this file existed.

WHAT IS BEING TESTED
--------------------
Sampling invariance, as a PAIRED test with a real null. Two estimators covering the
same WALL-CLOCK window on the same asset over the same days:

    A   1h bars, default (34, 9)          <- the reference
    B   15m bars, x4 (136, 36)            <- the proposal as stated
    C   15m bars, lag-matched (133, 33)   <- derived: Wilder lag is n-1, SMA lag (s-1)/2
    D   15m bars, default (34, 9)         <- the floor: right indicator, wrong sampling

Under the null that price is a continuous process and this indicator measures a
WINDOW, A and B compute nearly the same statistic. Any disagreement is attributable
to one specific thing: the intrabar path detail only the finer sampling sees.

WHY THE 1h SERIES IS RESAMPLED FROM THE 15m SOURCE
--------------------------------------------------
So the two series cannot disagree about what happened. `resample` is exact OHLCV
aggregation (D161) — the 1h bars are built from the very trades the 15m bars are
built from, so a gap between A and B is the sampling rate and nothing else.

The alternative was the repo's only native 1h crypto fixture, and it is not usable:
`crypto_intraday_1h_raw` is **50.4% zero-volume bars**, and the cleaner drops 17,520
of them, leaving an irregular ~2h series wearing a 1h label. That is recorded here
because it is a fact about the fixture that outlives this study.

GROSS IS PRIMARY
----------------
The question is whether the two agree AS SIGNALS. Costs confound it — B decides on a
4x finer grid and pays more for the same wall-clock decisions — so net is reported
beside gross at every tier and never substituted for it.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.data.cleaner import clean  # noqa: E402
from backtest_framework.data.csv_fixture import (  # noqa: E402
    load_fixture_csv_with_volumes,
)
from backtest_framework.research import macd as M  # noqa: E402
from backtest_framework.research.breakout_intraday import (  # noqa: E402
    census_days,
    resample,
)
from backtest_framework.research.breakout_study import DEFAULT_TIERS  # noqa: E402

FIXTURE = REPO / "data" / "fixtures" / "crypto_binance_15m_raw.csv.gz"
SUMMARY = REPO / "data" / "sampling_invariance_summary.json"
RESULTS = REPO / "docs" / "results" / "SAMPLING_RESULTS.md"

SOURCE_MINUTES = 15
SYMBOLS = ("BTCUSDT", "ETHUSDT", "XEMUSDT", "BTGUSDT")
MINUTES_PER_DAY = 1440

# (label, bar minutes, length, signal)
CONFIGS = (
    ("A_1h_default", 60, 34, 9),
    ("B_15m_x4", 15, 136, 36),
    ("C_15m_lag_matched", 15, 133, 33),
    ("D_15m_default", 15, 34, 9),
)
REFERENCE = "A_1h_default"
PROPOSAL = "B_15m_x4"

DELTA_HURDLE = 0.15  # hurdle I
CORR_HURDLE = 0.80  # hurdle I
FRESH_LOOKS = 4


def ppy(bar_minutes: int) -> float:
    """365 calendar days x bars per day — D17's rule on crypto's 365-day calendar
    (D108), carried down to the bar. 35,040 at 15m, 8,760 at 1h."""
    return 365.0 * (MINUTES_PER_DAY // bar_minutes)


def sharpe(per_bar: np.ndarray, bar_minutes: int) -> float:
    if len(per_bar) < 3:
        return 0.0
    sd = float(np.std(per_bar, ddof=1))
    if sd <= 0.0:
        return 0.0
    return float(np.mean(per_bar)) / sd * float(np.sqrt(ppy(bar_minutes)))


def build_series(cleaned: dict) -> tuple[dict, dict, dict]:
    """The 15m and 1h series for every symbol, on a SHARED CALENDAR.

    A partial UTC day is excluded at BOTH frequencies, so sampling rate is the only
    variable (D161). `ResampleReport.check()` raises rather than warns if the
    arithmetic does not hold."""
    by_15m, by_1h, meta = {}, {}, {}
    for sym in SYMBOLS:
        bars = cleaned[sym]
        volumes = [1.0] * len(bars)  # volume is unused here; the census needs a list
        day_census = census_days(bars, source_minutes=SOURCE_MINUTES)
        keep = day_census.complete
        hourly, _hv, report = resample(
            bars, volumes, 60, keep, source_minutes=SOURCE_MINUTES
        )
        report.check()
        kept = set(keep)
        fine = [b for b in bars if b.timestamp.date() in kept]
        if len(fine) != len(hourly) * 4:
            raise ValueError(
                f"{sym}: {len(fine)} 15m bars against {len(hourly)} 1h bars — the "
                "shared calendar did not hold"
            )
        by_15m[sym], by_1h[sym] = fine, hourly
        meta[sym] = {
            "complete_days": len(keep),
            "dropped_days": len(day_census.incomplete),
            "n_15m_bars": len(fine),
            "n_1h_bars": len(hourly),
            "first": fine[0].timestamp.isoformat(),
            "last": fine[-1].timestamp.isoformat(),
        }
    return by_15m, by_1h, meta


def arm(bars, length: int, signal: int) -> tuple[np.ndarray, np.ndarray, int]:
    """Position and per-bar log return for the acceleration rung, long-flat, lag=1."""
    closes = np.asarray([b.bar.close for b in bars], dtype=float)
    ret = np.zeros_like(closes)
    ret[1:] = np.log(closes[1:] / closes[:-1])
    start = M.impulse_warm_up_bars(length, signal)
    score = M.impulse_signal_score(M.impulse_macd_series(bars, length, signal))
    decided = M.positions(score, start=start, long_short=False)
    position = np.asarray((0.0,) + tuple(decided[:-1]), dtype=float)
    return position, ret, start


def hourly_buckets(bars, values: np.ndarray) -> dict:
    """Sum a per-bar series into (date, hour) buckets so a 15m arm and a 1h arm can
    be correlated on one grid. Log returns are additive, so this is exact."""
    out: dict = defaultdict(float)
    for b, v in zip(bars, values, strict=True):
        ts = b.timestamp
        out[(ts.date(), ts.hour)] += float(v)
    return out


def run(cleaned: dict) -> dict:
    by_15m, by_1h, meta = build_series(cleaned)
    rows, per_symbol = [], {}

    for sym in SYMBOLS:
        built = {}
        for label, minutes, length, sig in CONFIGS:
            bars = by_1h[sym] if minutes == 60 else by_15m[sym]
            if len(bars) < M.impulse_warm_up_bars(length, sig) + 2000:
                continue
            position, ret, start = arm(bars, length, sig)
            built[label] = {
                "bars": bars,
                "position": position,
                "ret": ret,
                "start": start,
                "minutes": minutes,
                "first_live": bars[start].timestamp,
            }
        if REFERENCE not in built or PROPOSAL not in built:
            continue

        # EVERY config scores on the SAME WALL-CLOCK SPAN, or the comparison is
        # between different samples rather than different sampling rates.
        common = max(v["first_live"] for v in built.values())
        streams = {}
        for label, v in built.items():
            idx = next(
                i for i, b in enumerate(v["bars"]) if b.timestamp >= common
            )
            live = v["position"][idx:]
            ret = v["ret"][idx:]
            bars = v["bars"][idx:]
            gross = ret * live
            years = len(live) / ppy(v["minutes"])
            turnover = float(np.abs(np.diff(live)).sum())
            nets = {}
            for tier in DEFAULT_TIERS:
                net = gross.copy()
                net[1:] += np.log1p(-(tier.fee_bps / 1e4) * np.abs(np.diff(live)))
                nets[tier.name] = sharpe(net, v["minutes"])
            mean_abs_move = (
                float(np.mean(np.abs(np.diff(np.cumsum(gross))))) if len(gross) > 1 else 0.0
            )
            trades = int(turnover / 2)
            streams[label] = {
                "gross_sharpe": sharpe(gross, v["minutes"]),
                "gross_total_return": float(np.expm1(np.sum(gross))),
                "net_sharpe": nets,
                "round_trips": trades,
                "round_trips_per_year": trades / years if years else 0.0,
                "exposure": float(np.mean(np.abs(live))),
                "years": years,
                "n_live_bars": int(len(live)),
                "bar_minutes": v["minutes"],
                "hourly": hourly_buckets(bars, gross),
                "mean_abs_bar_move_bp": mean_abs_move * 1e4,
            }

        ref = streams[REFERENCE]
        for label, s in streams.items():
            keys = sorted(set(s["hourly"]) & set(ref["hourly"]))
            a = np.array([ref["hourly"][k] for k in keys])
            b = np.array([s["hourly"][k] for k in keys])
            rho = (
                float(np.corrcoef(a, b)[0, 1])
                if len(keys) > 2 and a.std() > 0 and b.std() > 0
                else float("nan")
            )
            rows.append(
                {
                    "symbol": sym,
                    "config": label,
                    "bar_minutes": s["bar_minutes"],
                    "gross_sharpe": s["gross_sharpe"],
                    "gross_total_return": s["gross_total_return"],
                    "net_sharpe": s["net_sharpe"],
                    "round_trips": s["round_trips"],
                    "round_trips_per_year": s["round_trips_per_year"],
                    "exposure": s["exposure"],
                    "years": s["years"],
                    "n_live_bars": s["n_live_bars"],
                    "delta_vs_reference": s["gross_sharpe"] - ref["gross_sharpe"],
                    "corr_with_reference_hourly": rho,
                    "n_shared_hours": len(keys),
                }
            )
        per_symbol[sym] = {
            "common_start": common.isoformat(),
            "delta_B_minus_A": streams[PROPOSAL]["gross_sharpe"] - ref["gross_sharpe"],
            "corr_B_vs_A": next(
                r["corr_with_reference_hourly"]
                for r in rows
                if r["symbol"] == sym and r["config"] == PROPOSAL
            ),
        }

    return {
        "produced": time.strftime("%Y-%m-%d"),
        "calendar": meta,
        "rows": rows,
        "per_symbol": per_symbol,
        "verdict": verdict(per_symbol, rows),
        "fresh_looks": FRESH_LOOKS,
    }


def verdict(per_symbol: dict, rows: list[dict]) -> dict:
    deltas = {s: v["delta_B_minus_A"] for s, v in per_symbol.items()}
    corrs = {s: v["corr_B_vs_A"] for s, v in per_symbol.items()}
    within = {s: abs(d) <= DELTA_HURDLE for s, d in deltas.items()}
    correlated = {s: (c == c and c >= CORR_HURDLE) for s, c in corrs.items()}
    # Hurdle J: the arithmetic gate, per config, at the reference tier.
    gate = {}
    for r in rows:
        cost_per_rt_bp = 2 * DEFAULT_TIERS[-1].fee_bps
        gate[f"{r['symbol']}/{r['config']}"] = {
            "round_trips_per_year": r["round_trips_per_year"],
            "annual_drag_at_taker_40bp": r["round_trips_per_year"] * cost_per_rt_bp / 1e4,
            "net_sharpe_at_taker_40bp": r["net_sharpe"]["taker_40bp"],
            "tradeable_at_any_tier": any(v > 0 for v in r["net_sharpe"].values() if v),
        }
    return {
        "deltas_B_minus_A": deltas,
        "corrs_B_vs_A": corrs,
        "within_delta_hurdle": within,
        "clears_corr_hurdle": correlated,
        "invariance_holds": bool(all(within.values()) and all(correlated.values())),
        "delta_hurdle": DELTA_HURDLE,
        "corr_hurdle": CORR_HURDLE,
        "arithmetic_gate": gate,
    }


def render(p: dict) -> str:
    out: list[str] = []
    w = out.append
    v = p["verdict"]
    w("# Sampling invariance — D221")
    w("")
    w(f"**Produced:** {p['produced']} · **Reproduce:** "
      "`uv run python scripts/run_sampling_invariance.py` (offline, deterministic) ·")
    w("Record: [`D221`](../decisions/D221-does-the-indicator-care-about-sampling-rate.md) ·")
    w("Artifact: `data/sampling_invariance_summary.json`")
    w("")
    w("Two estimators covering the **same wall-clock window** on the same asset over the")
    w("same days. The 1h series is exact OHLCV aggregation of the 15m source (D161), so a")
    w("gap between them is the sampling rate and nothing else.")
    w("")
    w("## Gross — the primary comparison")
    w("")
    w("| symbol | config | bars | gross Sharpe | Δ vs 1h | ρ with 1h | RT/yr |")
    w("|---|---|---:|---:|---:|---:|---:|")
    for r in p["rows"]:
        rho = r["corr_with_reference_hourly"]
        w(f"| {r['symbol']} | {r['config']} | {r['bar_minutes']}m | "
          f"{r['gross_sharpe']:+.3f} | {r['delta_vs_reference']:+.3f} | "
          f"{rho:.2f} | {r['round_trips_per_year']:,.0f} |")
    w("")
    w("## Verdict — hurdle I")
    w("")
    w(f"Invariance holds if `|Δ| <= {DELTA_HURDLE}` **and** `ρ >= {CORR_HURDLE}` on every symbol.")
    w("")
    w("| symbol | Δ (B−A) | within ±0.15 | ρ | ρ ≥ 0.80 |")
    w("|---|---:|:--:|---:|:--:|")
    for sym in v["deltas_B_minus_A"]:
        d = v["deltas_B_minus_A"][sym]
        c = v["corrs_B_vs_A"][sym]
        w(f"| {sym} | {d:+.3f} | {'yes' if v['within_delta_hurdle'][sym] else 'no'} | "
          f"{c:.2f} | {'yes' if v['clears_corr_hurdle'][sym] else 'no'} |")
    w("")
    w(f"**Invariance holds: {'YES' if v['invariance_holds'] else 'NO'}.**")
    w("")
    w("## Net — hurdle J, the arithmetic gate")
    w("")
    w("| symbol / config | RT/yr | drag @ 40bp | net Sharpe @ 40bp | tradeable at any tier |")
    w("|---|---:|---:|---:|:--:|")
    for key, g in v["arithmetic_gate"].items():
        w(f"| {key} | {g['round_trips_per_year']:,.0f} | "
          f"{g['annual_drag_at_taker_40bp'] * 100:,.0f}% | "
          f"{g['net_sharpe_at_taker_40bp']:+.3f} | "
          f"{'yes' if g['tradeable_at_any_tier'] else 'no'} |")
    w("")
    w("## The fixture finding that outlives this study")
    w("")
    w("`crypto_intraday_1h_raw`, the repo's only **native** 1h crypto fixture, is **50.4%")
    w("zero-volume bars**. The cleaner drops 17,520 of them, leaving an irregular ~2h series")
    w("wearing a 1h label. It is unusable for any frequency comparison and for any volume")
    w("work. That is why the 1h arm here is resampled rather than fetched.")
    w("")
    w("**No config is promoted by this study under any outcome** — it asks how an estimator")
    w("behaves, not whether an arm is tradeable. A positive gross Sharpe here gets its own")
    w("pre-registration or it gets nothing.")
    w("")
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()

    if not args.report_only:
        t0 = time.time()
        raw, volumes = load_fixture_csv_with_volumes(FIXTURE)
        cleaned, _report = clean(raw, volumes)
        payload = run(cleaned)
        SUMMARY.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"wrote {SUMMARY.name} in {time.time() - t0:.1f}s")

    payload = json.loads(SUMMARY.read_text(encoding="utf-8"))
    RESULTS.write_text(render(payload), encoding="utf-8")
    v = payload["verdict"]
    print("invariance holds:", v["invariance_holds"])
    for sym, d in v["deltas_B_minus_A"].items():
        print(f"  {sym:<9} delta {d:+.3f}   rho {v['corrs_B_vs_A'][sym]:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
