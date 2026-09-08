"""D194's BUCKET-SPAN CENSUS, run on the 15-minute ETF PANEL, on the MINING WINDOW ONLY.

    uv run python scripts/d383_span_census.py

WHY THIS RUNS BEFORE D383's RUNNER EXISTS. D383 §7 Q7 nominates axis D -- the volume-profile
features `dist_hvn`, `dist_lvn`, `mass_here`, `mass_imbalance` -- as the one thing it expects to
survive. Every one of those is read off a `terrain.PriceDensity`, and that object's own `spans`
docstring records the way it can be wrong while looking right:

    "At 15m a bar's range is often narrower than one bucket, `span == 1`, and the map silently
     degenerates into the very histogram the spreading exists to avoid -- while looking exactly
     like a legitimate volume profile."

[D194](../docs/decisions/D194-the-s1-sensor-re-tested-at-15m.md) pre-registers reporting this
census BEFORE any verdict, and fixes what it decides: **"If the median span is 1, that is the
headline finding regardless of what the null test says, and any pass would be a pass for a
mechanism other than volume-at-price."** So the premise is measured before the study that rests
on it is built, not after it has produced a number somebody wants to keep.

NOTHING HERE SCORES A CELL. No forward return is read, no rule is proposed, no position is
taken. This measures a property of the sensor's input.

THE PARAMETERS ARE NOT CHOSEN HERE. Every one is lifted from `scripts/ragged_profile.py`, whose
own self-test asserts them equal to `run_volume_profile.py`'s -- D272's values, on this exact
15-minute panel, and every one inside the sensor's sanctioned set (it raises on anything else).
Choosing new ones would make this a census of a configuration D383 will not run.

THE FIXTURE IS THE PANEL, NOT THE RAW FIXTURE, and that distinction is the whole of D383's
2026-09-08 amendment: `ragged_panel.load_ragged` keys its grid on `timestamp[:10]`, so fed a
15-minute fixture it collapses ~26 intraday bars into one calendar slot and keeps the last
write -- 57 x 2,156 instead of 57 x 55,726, with no error and no warning. `[LOADER]` below
re-derives both numbers from the bars it actually loaded rather than quoting them.

FOUR ASSERTIONS, and `--selftest` shows each one RAISING on the input it exists to catch:

  [GATE]    `ragged_panel.assert_gates_passed` accepts the panel's own meta.
  [RECT]    the panel is RECTANGULAR -- the requirement `load_panel` enforces and the reason
            `build_intraday_panel.py` iterates its intersection to a fixed point.
  [SPLIT]   default-deny. Every bar at or after 2024-01-01 is cut from the BAR LISTS, not
            merely from a grid, and the cut is proved to have bitten.
  [WINDOW]  every bar the sensor could have read -- the sampled bar, its 180-bar profile
            lookback and its 182-bar ATR window -- lies inside the mining window, checked on
            the bar's own timestamp rather than on the index arithmetic that produced it.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.data.bars import Bar, TimestampedBar          # noqa: E402
from backtest_framework.data.csv_fixture import load_fixture_csv_with_volumes  # noqa: E402
from backtest_framework.research.terrain import VolumeProfileSensor   # noqa: E402


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


RP = _load("ragged_panel", "ragged_panel.py")

FIX = REPO / "data" / "fixtures"
PANEL = FIX / "etf_intraday_15m_panel.csv.gz"
OUT = REPO / "data" / "d383_span_census.json"

# D383 §1: MINING is the first bar through 2023-12-31; RESERVED is 2024-01-01 onward and is
# not read by anything here. Default-deny with no override -- there is no flag to widen it.
SPLIT_LAST_MINING_DAY = "2023-12-31"
RESERVED_FIRST_DAY = "2024-01-01"

# Lifted from scripts/ragged_profile.py, which asserts them equal to run_volume_profile.py's.
LOOKBACK_BARS = 180        # ~7 sessions at 26 bars/session; in the sensor's sanctioned set
BUCKET_ATR = 0.5           # sanctioned set: 0.25 / 0.5
ATR_WINDOW = 182           # calendar-matched to the lookback, as D272 matched it
VOLUME_UNITS = "shares"    # the fixture's column IS share count (D187's defect otherwise)

# The census is a sample, not a full sweep: 45,600 densities place a median far past any
# precision this decision needs, and a full sweep is 3.1M densities for the same answer.
SAMPLES_PER_SYMBOL = 800
SEED = 0

PCT = (1, 5, 10, 25, 50, 75, 90, 95, 99)


# --------------------------------------------------------------------------
# the guards, as functions, so the self-test can break each one
# --------------------------------------------------------------------------


def assert_rectangular(symbols, bars) -> int:
    """[RECT] one bar count for every symbol, or the panel is not a panel."""
    counts = {len(bars[s]) for s in symbols}
    if len(counts) != 1:
        raise AssertionError(
            f"the panel is not rectangular -- bar counts {sorted(counts)}. `load_panel` "
            "refuses this, which is why build_intraday_panel.py iterates its cleaned "
            "timestamp intersection to a fixed point.")
    return counts.pop()


def cut_to_mining(symbols, bars, volumes):
    """[SPLIT] cut the BAR LISTS at the boundary, default-deny, and prove the cut bit."""
    mining, mining_vol, dropped = {}, {}, 0
    for s in symbols:
        keep = [j for j, tb in enumerate(bars[s])
                if tb.timestamp.date().isoformat() <= SPLIT_LAST_MINING_DAY]
        dropped += len(bars[s]) - len(keep)
        mining[s] = [bars[s][j] for j in keep]
        mining_vol[s] = [volumes[s][j] for j in keep]
    if dropped == 0:
        raise AssertionError(
            "[SPLIT] cut nothing -- either the panel ends before the boundary or the "
            "comparison is not biting. A cut that cannot remove a bar guards nothing.")
    if not all(mining[s] for s in symbols):
        raise AssertionError("[SPLIT] emptied a symbol's bar list")
    worst = max(mining[s][-1].timestamp.date().isoformat() for s in symbols)
    if worst >= RESERVED_FIRST_DAY:
        raise AssertionError(f"[SPLIT] left a reserved bar in the panel: {worst}")
    return mining, mining_vol, dropped, worst


def assert_window_is_mining(sym, bars, lo_index, hi_index):
    """[WINDOW] the deepest and shallowest bars the sensor will read are both mining bars.

    Checked on the TIMESTAMPS rather than on the index arithmetic that produced them, so
    an off-by-one in the sampling cannot satisfy this by agreeing with itself."""
    if lo_index < 0 or hi_index >= len(bars):
        raise AssertionError(f"{sym}: the sensor's window runs off the bar list "
                             f"[{lo_index}, {hi_index}] against {len(bars)} bars")
    for j in (lo_index, hi_index):
        d = bars[j].timestamp.date().isoformat()
        if d > SPLIT_LAST_MINING_DAY:
            raise AssertionError(f"{sym}: the sensor would read {d}, past the split")


# --------------------------------------------------------------------------
# loading
# --------------------------------------------------------------------------


def load_mining_bars():
    meta = RP.assert_gates_passed(PANEL)
    gate_names = sorted(k for k, v in meta["gates"].items()
                        if isinstance(v, dict) and "failures" in v)
    print(f"  [GATE]   assert_gates_passed accepts {PANEL.name}: {', '.join(gate_names)}")

    t0 = time.time()
    bars, volumes = load_fixture_csv_with_volumes(PANEL)
    symbols = sorted(bars)
    n_bars = assert_rectangular(symbols, bars)
    stamps = [tb.timestamp for tb in bars[symbols[0]]]
    dates = {t.date().isoformat() for t in stamps}
    print(f"  [RECT]   {len(symbols)} symbols x {n_bars:,} bars, rectangular, "
          f"{stamps[0].isoformat()} .. {stamps[-1].isoformat()}  ({time.time() - t0:.0f}s)")
    print(f"           the SAME rows through `load_ragged`, which keys its grid on "
          f"timestamp[:10], would be {len(symbols)} x {len(dates):,} -- "
          f"{n_bars / len(dates):.1f} bars a session collapsed into one slot, last write wins")

    mining, mining_vol, dropped, worst = cut_to_mining(symbols, bars, volumes)
    kept = len(mining[symbols[0]])
    print(f"  [SPLIT]  cut {dropped:,} reserved rows ({RESERVED_FIRST_DAY} onward); "
          f"{kept:,} mining bars per symbol remain, last {worst}")
    return symbols, mining, mining_vol, dict(
        panel_symbols=len(symbols), panel_bars=n_bars,
        panel_first=stamps[0].isoformat(), panel_last=stamps[-1].isoformat(),
        load_ragged_would_be_bars=len(dates),
        bars_per_session=round(n_bars / len(dates), 2),
        mining_bars_per_symbol=kept, reserved_rows_cut=dropped,
        mining_last_bar_date=worst)


# --------------------------------------------------------------------------
# the census
# --------------------------------------------------------------------------


def census(symbols, bars, vols):
    sensor = VolumeProfileSensor(LOOKBACK_BARS, BUCKET_ATR, VOLUME_UNITS,
                                 atr_window=ATR_WINDOW)
    warm = sensor.warm_up_bars() - 1            # first index `density` will answer at
    reach = max(LOOKBACK_BARS, ATR_WINDOW) - 1  # bars behind the sampled one it reads
    rng = np.random.default_rng(SEED)
    pooled = np.zeros(1024, dtype=np.int64)     # counts of span values, grown on demand
    med, sbs, per_symbol = [], [], {}
    n_none = 0

    t0 = time.time()
    for s in symbols:
        b, v, m = bars[s], vols[s], len(bars[s])
        if m <= warm:
            raise AssertionError(f"{s}: {m} mining bars against a {warm + 1}-bar warm-up")
        idx = sorted(int(x) for x in rng.choice(np.arange(warm, m),
                                                size=min(SAMPLES_PER_SYMBOL, m - warm),
                                                replace=False))
        assert_window_is_mining(s, b, idx[0] - reach, idx[-1])
        sm, ss = [], []
        for j in idx:
            d = sensor.density(b, j, v)
            if d is None:
                n_none += 1
                continue
            bc = np.bincount(np.asarray(d.spans, dtype=np.int64))
            if bc.size > pooled.size:
                grown = np.zeros(bc.size, dtype=np.int64)
                grown[:pooled.size] = pooled
                pooled = grown
            pooled[:bc.size] += bc
            sm.append(d.median_span)
            ss.append(d.single_bucket_share)
        med.extend(sm)
        sbs.extend(ss)
        per_symbol[s] = dict(n=len(sm), median_span=float(np.median(sm)),
                             single_bucket_share=float(np.median(ss)))
    print(f"  {len(med):,} densities over {len(symbols)} symbols "
          f"({time.time() - t0:.0f}s); {n_none:,} returned None")

    med, sbs = np.asarray(med), np.asarray(sbs)
    span_values = np.nonzero(pooled)[0]
    counts = pooled[span_values]
    tot = int(counts.sum())
    cum = np.cumsum(counts)

    def pooled_pct(q):
        return float(span_values[min(int(np.searchsorted(cum, q / 100.0 * tot)),
                                     span_values.size - 1)])

    return dict(
        n_densities=int(med.size), n_density_none=n_none, contributing_bars=tot,
        pooled_span=dict(
            mean=float((span_values * counts).sum() / tot),
            **{f"p{q}": pooled_pct(q) for q in PCT},
            share_span_1=float(counts[span_values == 1].sum() / tot),
            share_span_le_2=float(counts[span_values <= 2].sum() / tot),
            histogram={int(x): int(c) for x, c in zip(span_values[:24], counts[:24])}),
        median_span=dict(mean=float(med.mean()),
                         **{f"p{q}": float(np.percentile(med, q)) for q in PCT},
                         share_at_or_below_1=float((med <= 1.0).mean())),
        single_bucket_share=dict(mean=float(sbs.mean()),
                                 **{f"p{q}": float(np.percentile(sbs, q)) for q in PCT}),
        per_symbol=per_symbol,
        worst_symbol_median_span=float(min(v["median_span"] for v in per_symbol.values())),
        best_symbol_median_span=float(max(v["median_span"] for v in per_symbol.values())),
    )


# --------------------------------------------------------------------------
# the self-test -- an assertion that cannot fail is worse than none
# --------------------------------------------------------------------------


def _bar(day, lo, hi):
    return TimestampedBar(datetime.fromisoformat(f"{day}T09:30:00"), Bar(lo, hi, lo, hi))


def selftest() -> None:
    """Every guard above, called on the input it exists to catch. Each must raise."""
    raised = []

    def must_raise(label, fn):
        try:
            fn()
        except (AssertionError, ValueError, FileNotFoundError):
            raised.append(label)
        else:
            raise AssertionError(f"{label} accepted an input it must have refused")

    # [RECT] -- a ragged panel, which is what a naive intersection produces.
    must_raise("[RECT] ragged bar counts", lambda: assert_rectangular(
        ["A", "B"], {"A": [_bar("2020-01-02", 1, 2)] * 3, "B": [_bar("2020-01-02", 1, 2)] * 4}))

    # [SPLIT] -- a panel that ends before the boundary, so the cut removes nothing.
    must_raise("[SPLIT] cut removed nothing", lambda: cut_to_mining(
        ["A"], {"A": [_bar("2020-06-01", 1, 2)]}, {"A": [1.0]}))

    # [SPLIT] -- a panel whose bars are ALL reserved, so the cut empties it.
    must_raise("[SPLIT] cut emptied a symbol", lambda: cut_to_mining(
        ["A"], {"A": [_bar("2024-06-03", 1, 2)]}, {"A": [1.0]}))

    # [WINDOW] -- a sampled index whose lookback reaches a reserved bar.
    mixed = [_bar("2023-12-29", 1, 2), _bar("2024-01-02", 1, 2)]
    must_raise("[WINDOW] reads past the split",
               lambda: assert_window_is_mining("A", mixed, 0, 1))

    # [WINDOW] -- a window running off the end of the bar list.
    must_raise("[WINDOW] runs off the bar list",
               lambda: assert_window_is_mining("A", mixed, -3, 1))

    # [GATE] -- a file with no meta beside it must be refused by the real function.
    must_raise("[GATE] no meta.json",
               lambda: RP.assert_gates_passed(FIX / "etf_intraday_15m_panel_events.json"))

    # And the guards must ACCEPT the shapes they are meant to pass, or they are just
    # unconditional failures wearing an assertion's clothes.
    good = {"A": [_bar("2023-12-28", 1, 2), _bar("2024-01-02", 1, 2)],
            "B": [_bar("2023-12-28", 1, 2), _bar("2024-01-02", 1, 2)]}
    assert assert_rectangular(["A", "B"], good) == 2
    _m, _v, dropped, worst = cut_to_mining(["A", "B"], good, {"A": [1.0, 1.0], "B": [1.0, 1.0]})
    assert dropped == 2 and worst == "2023-12-28", (dropped, worst)
    assert_window_is_mining("A", good["A"], 0, 0)
    print(f"  [X] {len(raised)} guards RAISE on a deliberately broken input, and all three "
          "accept a sound one")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true", help="run the guards only")
    a = ap.parse_args()

    print(__doc__.split("\n")[0] + "\n")
    selftest()
    if a.selftest:
        return 0

    symbols, bars, vols, shape = load_mining_bars()
    print(f"\n  sensor: lookback {LOOKBACK_BARS} bars, bucket {BUCKET_ATR} ATR, "
          f"ATR window {ATR_WINDOW} bars, volume in {VOLUME_UNITS} "
          f"(ragged_profile.py's constants, unchanged)")
    rep = census(symbols, bars, vols)

    p, m, s = rep["pooled_span"], rep["median_span"], rep["single_bucket_share"]
    print(f"\n  POOLED span over {rep['contributing_bars']:,} contributing bars:")
    print(f"    p05 {p['p5']:.0f}  p25 {p['p25']:.0f}  MEDIAN {p['p50']:.0f}  "
          f"p75 {p['p75']:.0f}  p95 {p['p95']:.0f}   mean {p['mean']:.2f}")
    print(f"    span == 1: {p['share_span_1']:.2%}   span <= 2: {p['share_span_le_2']:.2%}")
    print(f"\n  PER-DENSITY median_span over {rep['n_densities']:,} densities:")
    print(f"    p01 {m['p1']:.1f}  p05 {m['p5']:.1f}  p25 {m['p25']:.1f}  MEDIAN {m['p50']:.1f}  "
          f"p75 {m['p75']:.1f}  p95 {m['p95']:.1f}   mean {m['mean']:.2f}")
    print(f"    densities with median_span <= 1: {m['share_at_or_below_1']:.3%}")
    print(f"    worst symbol {rep['worst_symbol_median_span']:.1f}, "
          f"best symbol {rep['best_symbol_median_span']:.1f}")
    print("\n  single_bucket_share (fraction of contributing bars landing in ONE bucket):")
    print(f"    p05 {s['p5']:.3f}  p25 {s['p25']:.3f}  MEDIAN {s['p50']:.3f}  "
          f"p75 {s['p75']:.3f}  p95 {s['p95']:.3f}   mean {s['mean']:.3f}")

    verdict = ("DEGENERATE -- the median span is 1, so the profile is a close-price histogram "
               "wearing a volume label. D194: price-density features are INVALID at 15m "
               "regardless of what any signal test says."
               if m["p50"] <= 1.0 else
               "NOT DEGENERATE -- the median span is above 1, so a bar's volume is genuinely "
               "spread across buckets and the map is a volume profile rather than a "
               "close-price histogram. D194's invalidating condition does NOT fire.")
    print(f"\n  VERDICT: {verdict}")

    OUT.write_text(json.dumps(dict(
        study="D383", diagnostic="D194 bucket-span census",
        fixture=PANEL.name, window="MINING ONLY, first bar .. " + SPLIT_LAST_MINING_DAY,
        reserved_untouched=f"{RESERVED_FIRST_DAY} onward, cut from the bar lists before sampling",
        sensor=dict(lookback_bars=LOOKBACK_BARS, bucket_atr=BUCKET_ATR,
                    atr_window=ATR_WINDOW, volume_units=VOLUME_UNITS,
                    source="scripts/ragged_profile.py, == run_volume_profile.py (D272)"),
        sampling=dict(per_symbol=SAMPLES_PER_SYMBOL, seed=SEED),
        shape=shape, verdict=verdict, **rep), indent=1), encoding="utf-8")
    print(f"\n  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
