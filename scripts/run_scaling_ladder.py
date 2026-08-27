"""D222 — does the fine-bar advantage grow as the matched window gets longer?

    uv run python scripts/run_scaling_ladder.py
    uv run python scripts/run_scaling_ladder.py --report-only

Offline, deterministic. `docs/decisions/D222-does-the-fine-bar-advantage-grow-with-the-window.md`
was written and committed BEFORE this file existed.

WHAT IS BEING TESTED
--------------------
D221 left a small positive residual on the liquid symbols. This asks whether that
residual is STRUCTURE OR NOISE by testing a SHAPE:

    delta(k) = Sharpe(15m matched) - Sharpe(native),  k in {4, 32, 96}

A residual that is noise has no reason to order itself by k.

THE CONFOUND THIS FILE EXISTS TO AVOID
--------------------------------------
Warm-up scales with k: 42 days at k=4, 339 at k=32, 1,016 at k=96. Measured
naively, each rung would run on a shorter and LATER span than the one below, and a
growing delta would be indistinguishable from the later period behaving
differently. So EVERY rung scores on ONE span, set by the largest warm-up in the
whole ladder, and `_assert_shared_span` refuses to publish if that ever stops
holding. D221's delta(4) is deliberately NOT reused: it was measured over 8.3
years against this study's ~5.6.

RESOLVABILITY
-------------
A trend over three points on two symbols is weak by construction, so each delta
carries a block bootstrap. Both arms are recomputed on the SAME resampled index
set, so the pairing survives the resample. Hurdle L without hurdle M is a pattern
in noise, and this runner reports that as the finding when it is.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.data.cleaner import clean  # noqa: E402
from backtest_framework.data.csv_fixture import (  # noqa: E402
    load_fixture_csv_with_volumes,
)
from backtest_framework.research.breakout_intraday import (  # noqa: E402
    census_days,
    resample,
)
from backtest_framework.research.breakout_study import DEFAULT_TIERS  # noqa: E402


def _load_d221():
    spec = importlib.util.spec_from_file_location(
        "run_sampling_invariance", REPO / "scripts" / "run_sampling_invariance.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# The arm, the annualisation and the Sharpe come from D221 — reused, not restated (D212).
S = _load_d221()

FIXTURE = REPO / "data" / "fixtures" / "crypto_binance_15m_raw.csv.gz"
SUMMARY = REPO / "data" / "scaling_ladder_summary.json"
RESULTS = REPO / "SCALING_RESULTS.md"

SOURCE_MINUTES = 15
SYMBOLS = ("BTCUSDT", "ETHUSDT")
BASE_LENGTH, BASE_SIGNAL = 34, 9
RUNGS = (("1h", 60, 4), ("8h", 480, 32), ("1d", 1440, 96))

BLOCK_DAYS = 30
N_BOOT = 400
SEED = 0
FRESH_LOOKS = 6


def matched_params(k: int) -> tuple[int, int]:
    """Naive x k. D221 falsified the need for the lag correction — the derived
    (133, 33) gave no advantage over (136, 36) — so the rule is to multiply by
    the frequency ratio and say so."""
    return BASE_LENGTH * k, BASE_SIGNAL * k


def series_for(bars, volumes, target_minutes: int, keep_days):
    if target_minutes == SOURCE_MINUTES:
        kept = set(keep_days)
        return [b for b in bars if b.timestamp.date() in kept]
    coarse, _v, report = resample(
        bars, volumes, target_minutes, keep_days, source_minutes=SOURCE_MINUTES
    )
    report.check()
    return coarse


def _assert_shared_span(built: dict, symbol: str) -> None:
    """Every config must cover the same wall-clock interval to within ONE COARSE BAR.

    Not an identical timestamp: a daily bar can only begin at 00:00 UTC and an 8h
    bar at 00/08/16:00, so configs on different grids CANNOT share an exact start.
    Demanding that is impossible, and the first version of this function did — it
    fired on the first run, which is the gate working. The real invariant is that
    no config sees materially more of the sample than another, and the bound is the
    coarsest bar in the ladder."""
    tolerance = max(v["minutes"] for v in built.values()) * 60.0  # seconds
    firsts = {label: v["first_ts"] for label, v in built.items()}
    lasts = {label: v["last_ts"] for label, v in built.items()}
    start_spread = (max(firsts.values()) - min(firsts.values())).total_seconds()
    end_spread = (max(lasts.values()) - min(lasts.values())).total_seconds()
    if start_spread > tolerance:
        raise ValueError(
            f"{symbol}: starts spread {start_spread / 3600:.1f}h, more than one "
            f"coarse bar ({tolerance / 3600:.1f}h) — {firsts}"
        )
    if end_spread > tolerance:
        raise ValueError(
            f"{symbol}: ends spread {end_spread / 3600:.1f}h, more than one "
            f"coarse bar ({tolerance / 3600:.1f}h) — {lasts}"
        )


def score_stream(gross: np.ndarray, position: np.ndarray, minutes: int) -> dict:
    years = len(gross) / S.ppy(minutes)
    turnover = float(np.abs(np.diff(position)).sum()) if len(position) > 1 else 0.0
    nets = {}
    for tier in DEFAULT_TIERS:
        net = gross.copy()
        net[1:] += np.log1p(-(tier.fee_bps / 1e4) * np.abs(np.diff(position)))
        nets[tier.name] = S.sharpe(net, minutes)
    return {
        "gross_sharpe": S.sharpe(gross, minutes),
        "gross_total_return": float(np.expm1(np.sum(gross))),
        "net_sharpe": nets,
        "round_trips": int(turnover / 2),
        "round_trips_per_year": (turnover / 2 / years) if years else 0.0,
        "exposure": float(np.mean(np.abs(position))),
        "years": years,
        "n_live_bars": int(len(gross)),
        "bar_minutes": minutes,
    }


def daily_series(bars, values: np.ndarray) -> dict:
    out: dict = {}
    for b, v in zip(bars, values, strict=True):
        d = b.timestamp.date()
        out[d] = out.get(d, 0.0) + float(v)
    return out


def paired_bootstrap(
    fine_daily: dict, coarse_daily: dict, minutes_fine: int, minutes_coarse: int, seed: int
) -> dict:
    """Block bootstrap on the SHARED daily grid, both arms resampled on the SAME
    index set so the pairing survives. The statistic is the Sharpe difference,
    recomputed on each resample rather than approximated."""
    days = sorted(set(fine_daily) & set(coarse_daily))
    a = np.array([fine_daily[d] for d in days])
    b = np.array([coarse_daily[d] for d in days])
    n_blocks = max(1, len(days) // BLOCK_DAYS)
    rng = np.random.default_rng(seed)
    out = np.empty(N_BOOT)
    for i in range(N_BOOT):
        starts = rng.integers(0, max(1, len(days) - BLOCK_DAYS), size=n_blocks)
        idx = np.concatenate([np.arange(s, s + BLOCK_DAYS) for s in starts])
        idx = idx[idx < len(days)]
        # Daily aggregation makes both arms comparable: annualise on 365.
        fa, fb = a[idx], b[idx]
        sa = float(np.mean(fa) / np.std(fa, ddof=1) * np.sqrt(365.0)) if np.std(fa, ddof=1) > 0 else 0.0
        sb = float(np.mean(fb) / np.std(fb, ddof=1) * np.sqrt(365.0)) if np.std(fb, ddof=1) > 0 else 0.0
        out[i] = sa - sb
    obs_a = float(np.mean(a) / np.std(a, ddof=1) * np.sqrt(365.0))
    obs_b = float(np.mean(b) / np.std(b, ddof=1) * np.sqrt(365.0))
    return {
        "delta_daily_basis": obs_a - obs_b,
        "p5": float(np.percentile(out, 5)),
        "p50": float(np.percentile(out, 50)),
        "p95": float(np.percentile(out, 95)),
        "ci_width": float(np.percentile(out, 95) - np.percentile(out, 5)),
        "share_positive": float((out > 0).mean()),
        "n_days": len(days),
        "n_boot": N_BOOT,
        "block_days": BLOCK_DAYS,
    }


def run(cleaned: dict) -> dict:
    rows, per_symbol, calendar = [], {}, {}

    for sym in SYMBOLS:
        bars = cleaned[sym]
        volumes = [1.0] * len(bars)
        day_census = census_days(bars, source_minutes=SOURCE_MINUTES)
        keep = day_census.complete
        calendar[sym] = {
            "complete_days": len(keep),
            "dropped_days": len(day_census.incomplete),
        }

        built = {}
        for name, minutes, k in RUNGS:
            length, signal = matched_params(k)
            for label, mins, ln, sg in (
                (f"native_{name}", minutes, BASE_LENGTH, BASE_SIGNAL),
                (f"fine_x{k}", SOURCE_MINUTES, length, signal),
            ):
                series = series_for(bars, volumes, mins, keep)
                position, ret, start = S.arm(series, ln, sg)
                built[label] = {
                    "series": series,
                    "position": position,
                    "ret": ret,
                    "start": start,
                    "minutes": mins,
                    "rung": name,
                    "k": k,
                    "params": (ln, sg),
                    "first_live": series[start].timestamp,
                }

        # ONE span for the whole ladder, set by the largest warm-up in it.
        common = max(v["first_live"] for v in built.values())
        scored = {}
        for label, v in built.items():
            idx = next(i for i, b in enumerate(v["series"]) if b.timestamp >= common)
            live_bars = v["series"][idx:]
            pos = v["position"][idx:]
            gross = v["ret"][idx:] * pos
            v["first_ts"] = live_bars[0].timestamp
            v["last_ts"] = live_bars[-1].timestamp
            scored[label] = score_stream(gross, pos, v["minutes"]) | {
                "rung": v["rung"],
                "k": v["k"],
                "params": list(v["params"]),
                "daily": daily_series(live_bars, gross),
            }
        _assert_shared_span(built, sym)

        deltas = {}
        for name, minutes, k in RUNGS:
            fine, native = scored[f"fine_x{k}"], scored[f"native_{name}"]
            boot = paired_bootstrap(
                fine["daily"], native["daily"], SOURCE_MINUTES, minutes, SEED
            )
            deltas[name] = {
                "k": k,
                "delta_gross_sharpe": fine["gross_sharpe"] - native["gross_sharpe"],
                "fine_gross_sharpe": fine["gross_sharpe"],
                "native_gross_sharpe": native["gross_sharpe"],
                "fine_rt_per_year": fine["round_trips_per_year"],
                "native_rt_per_year": native["round_trips_per_year"],
                "bootstrap": boot,
            }
            for label, s in ((f"fine_x{k}", fine), (f"native_{name}", native)):
                rows.append(
                    {"symbol": sym, "config": label}
                    | {kk: vv for kk, vv in s.items() if kk != "daily"}
                )
        per_symbol[sym] = {
            "common_start": common.isoformat(),
            "span_years": scored[f"native_{RUNGS[0][0]}"]["years"],
            "deltas": deltas,
        }

    return {
        "produced": time.strftime("%Y-%m-%d"),
        "calendar": calendar,
        "rows": rows,
        "per_symbol": per_symbol,
        "verdict": verdict(per_symbol),
        "fresh_looks": FRESH_LOOKS,
        "seed": SEED,
    }


def verdict(per_symbol: dict) -> dict:
    order = [name for name, _, _ in RUNGS]
    direction, shape, resolvable = {}, {}, {}
    for sym, block in per_symbol.items():
        d = [block["deltas"][n]["delta_gross_sharpe"] for n in order]
        direction[sym] = all(x > 0 for x in d)
        shape[sym] = d[0] < d[1] < d[2]
        span = block["deltas"][order[-1]]["bootstrap"]["ci_width"]
        gap = (
            block["deltas"][order[-1]]["bootstrap"]["delta_daily_basis"]
            - block["deltas"][order[0]]["bootstrap"]["delta_daily_basis"]
        )
        resolvable[sym] = bool(abs(gap) > span)
    return {
        "K_direction_all_positive": direction,
        "L_shape_monotone_increasing": shape,
        "M_gap_exceeds_ci_width": resolvable,
        "K_holds": all(direction.values()),
        "L_holds": all(shape.values()),
        "M_holds": all(resolvable.values()),
        "rung_order": order,
    }


def render(p: dict) -> str:
    out: list[str] = []
    w = out.append
    v = p["verdict"]
    w("# The scaling ladder — D222")
    w("")
    w(f"**Produced:** {p['produced']} · **Reproduce:** "
      "`uv run python scripts/run_scaling_ladder.py` (offline, deterministic) ·")
    w("Record: [`D222`](docs/decisions/D222-does-the-fine-bar-advantage-grow-with-the-window.md) ·")
    w("Artifact: `data/scaling_ladder_summary.json`")
    w("")
    w("Is the fine-bar residual **structure or noise**? A residual that is noise has no")
    w("reason to order itself by `k`. **Every rung scores on one shared span**, set by the")
    w("largest warm-up in the ladder, so a growing gap cannot be the later period.")
    w("")
    w("## Δ(k) — the shape under test")
    w("")
    w("| symbol | rung | k | native | 15m matched | **Δ** | bootstrap p5..p95 | resolvable |")
    w("|---|---|---:|---:|---:|---:|---:|:--:|")
    for sym, block in p["per_symbol"].items():
        for name in v["rung_order"]:
            d = block["deltas"][name]
            b = d["bootstrap"]
            crosses = b["p5"] <= 0.0 <= b["p95"]
            w(f"| {sym} | {name} | {d['k']} | {d['native_gross_sharpe']:+.3f} | "
              f"{d['fine_gross_sharpe']:+.3f} | **{d['delta_gross_sharpe']:+.3f}** | "
              f"{b['p5']:+.3f} .. {b['p95']:+.3f} | {'no' if crosses else 'yes'} |")
    w("")
    w("## Verdict")
    w("")
    w("| hurdle | | holds |")
    w("|---|---|:--:|")
    w(f"| **K** | Δ > 0 at every k | {'yes' if v['K_holds'] else 'no'} |")
    w(f"| **L** | Δ(4) < Δ(32) < Δ(96) | {'yes' if v['L_holds'] else 'no'} |")
    w(f"| **M** | the Δ(96)−Δ(4) gap exceeds its own CI width | "
      f"{'yes' if v['M_holds'] else 'no'} |")
    w("")
    w("**L without M is a pattern in noise.** Per symbol:")
    w("")
    w("| symbol | K | L | M |")
    w("|---|:--:|:--:|:--:|")
    for sym in p["per_symbol"]:
        w(f"| {sym} | {'yes' if v['K_direction_all_positive'][sym] else 'no'} | "
          f"{'yes' if v['L_shape_monotone_increasing'][sym] else 'no'} | "
          f"{'yes' if v['M_gap_exceeds_ci_width'][sym] else 'no'} |")
    w("")
    w("## Trading rate — N5")
    w("")
    w("| symbol | rung | native RT/yr | 15m matched RT/yr |")
    w("|---|---|---:|---:|")
    for sym, block in p["per_symbol"].items():
        for name in v["rung_order"]:
            d = block["deltas"][name]
            w(f"| {sym} | {name} | {d['native_rt_per_year']:,.1f} | "
              f"{d['fine_rt_per_year']:,.1f} |")
    w("")
    w("**No config is promoted by this study.** It asks how an estimator behaves, not")
    w("whether an arm is tradeable.")
    w("")
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()
    if not args.report_only:
        t0 = time.time()
        raw, volumes = load_fixture_csv_with_volumes(FIXTURE)
        cleaned, _ = clean(raw, volumes)
        payload = run(cleaned)
        SUMMARY.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"wrote {SUMMARY.name} in {time.time() - t0:.1f}s")
    payload = json.loads(SUMMARY.read_text(encoding="utf-8"))
    RESULTS.write_text(render(payload), encoding="utf-8")
    v = payload["verdict"]
    print(f"K {v['K_holds']}  L {v['L_holds']}  M {v['M_holds']}")
    for sym, block in payload["per_symbol"].items():
        ds = [f"{block['deltas'][n]['delta_gross_sharpe']:+.3f}" for n in v["rung_order"]]
        print(f"  {sym:<9} delta(4,32,96) = {'  '.join(ds)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
