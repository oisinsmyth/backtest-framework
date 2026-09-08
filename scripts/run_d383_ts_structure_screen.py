"""D383 -- the TIME-SERIES market-structure screen on the 57-ETF 15-minute panel.

    uv run python scripts/run_d383_ts_structure_screen.py --selftest
    uv run python scripts/run_d383_ts_structure_screen.py --prep       # load, cut to mining, cache the panel
    uv run python scripts/run_d383_ts_structure_screen.py --features   # the 19 feature grids  (--workers N)
    uv run python scripts/run_d383_ts_structure_screen.py --events     # 114 trailing-percentile grids -> events
    uv run python scripts/run_d383_ts_structure_screen.py --observed   # the 600 + 312 cells, no nulls
    uv run python scripts/run_d383_ts_structure_screen.py --nulls --draws 200
    uv run python scripts/run_d383_ts_structure_screen.py --report

Pre-registration: docs/decisions/D383-the-time-series-structure-screen-at-15-minutes.md
(`af91504`, amended `cb864cb`) -- committed BEFORE this file existed (R8).

WHAT THIS FILE MUST COMPUTE, SECTION BY SECTION, because a runner computing something
ADJACENT to its own pre-registration is this programme's most expensive recurring defect
(D384 compared one density where its own s4 said "sampled over bars"):

  s1  OBJECT   `data/fixtures/etf_intraday_15m_panel.csv.gz` through `run_macd_ladder.load_panel`
               -- 57 x 55,726 FIFTEEN-MINUTE bars, not 57 x 2,156 daily closes. MINING is the
               first bar through 2023-12-31 (38,648 bars/symbol); 2024-01-01 onward is RESERVED
               and this file has no path to it. `[GATE]` is an EXPLICIT call here because
               `load_panel` does not make one. `panel.dates` is date-only, so anything needing a
               calendar hold reads the bar's own timestamp.
  s2  EVENT    the PERCENTILE OF x[i,t] WITHIN THAT NAME'S OWN TRAILING x[i, t-W .. t-1]
               crossing into the declared extreme decile. No cross-sectional comparison anywhere.
               Long-flat, equal-weighted, per name, lag = 1.
               W in (26, 52, 130, 260, 390, 780); hold in (4, 13, 26, 78), primary 26.
  s3  GRID     13 declared feature-directions + 6 undeclared scored BOTH tails = 25 directions.
               25 x 6 x 4 = 600 cells. The reversed book of each declared feature is reported
               SEPARATELY and is not in the floor.
  s4  NULLS    rotation, and matched-count random entry. The floor is BEST-OF-150 WITHIN EACH
               HOLD (25 directions x 6 windows) under ONE SHARED DRAW per iteration. Never across
               holds -- a 78-bar hold earns ~20x a 4-bar hold per trade by construction.
  s5  METRIC   PRIMARY (R15) gross mean per TRADE against the s4 floors; bp per BAR HELD beside it
               (s8's abandon condition is stated on bp-per-bar, so it carries its own floors);
               excess over buy-and-hold at MATCHED exposure; turnover, entries per year and median
               hold in CALENDAR time BEFORE any performance number; the SHAPE across six windows.
  s6  AUDITS   [SPLIT] [GATE] [LAG] [TS] [DIR] [BH] [POS] [X], plus [SIGN] and [QTY].

THE GRID IS NEVER MATERIALISED. 600 cells on a 57 x 38,648 panel is 2 GB of percentile grid
alone. One feature-window is computed at a time and reduced to compact event index arrays; the
nulls hold one HOLD's books at a time. Every stage prints its own working set.

THE NULL KERNEL IS RUN-BASED AND PROVED BIT-IDENTICAL TO THE GRID KERNEL. `trades_of_runs`
rotates a book's CIRCULAR RUNS instead of rolling 2.2M cells and re-scanning them; `[POS]`
proves it equals `trades_grid(roll(pos))` element for element on a TIE-HEAVY book, rotated and
not, before a single draw is taken. Measured 26.1 ms -> 5.6 ms per cell-draw.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


RP = _load("ragged_panel", "ragged_panel.py")
FN = _load("fast_null", "fast_null.py")
FB = _load("ragged_features", "ragged_features.py")
ST = _load("ragged_structure_scores", "ragged_structure_scores.py")
PR = _load("ragged_profile", "ragged_profile.py")

STUDY = 383
DATA = REPO / "data"
TEMP = REPO / "temp"
FIXTURE = DATA / "fixtures" / "etf_intraday_15m_panel.csv.gz"
EVENTS_JSON = DATA / "fixtures" / "etf_intraday_15m_panel_events.json"

# ---------------------------------------------------------------- s1, the split
MINING_END = "2023-12-31"        # last MINING day. Default-deny; there is no flag that widens it.
RESERVED_FIRST = "2024-01-01"    # RESERVED. Not read, not scored, not summarised.

# ---------------------------------------------------------------- s2, the construction
WINDOWS = (26, 52, 130, 260, 390, 780)      # 1, 2, 5, 10, 15, 30 sessions. Reported, never picked.
HOLDS = (4, 13, 26, 78)                     # 1h, half session, one session, three sessions.
PRIMARY_HOLD = 26                           # nominated in advance (s2)
DECILE = 10.0                               # the extreme decile
MIN_TRAILING_OBS = 20                       # D382's own `k < 20: continue`, inherited not invented
WARMUP = 1000                               # >= the profile sensor's 183-bar warm-up + the 780 window
LAG = 1

# ---------------------------------------------------------------- s3, gate 1h
DECLARED = {                                # long end, from the feature's own definition in code
    "upper_wick": "LOW", "lower_wick": "HIGH", "wick_asym": "LOW", "body_frac": "HIGH",
    "close_in_range": "HIGH", "gap_frac": "LOW", "struct_trend": "HIGH", "retrace_leg": "HIGH",
    "fvg_signed": "HIGH", "dist_hvn": "LOW", "mass_imbalance": "LOW", "gap_reversal": "HIGH",
    "mass_here": "HIGH"}
UNDECLARED = ("range_frac", "park_vol_21", "gk_minus_cc", "fvg_dist", "choch_dist", "dist_lvn")
FEATURES = tuple(sorted(set(DECLARED) | set(UNDECLARED)))

DIRS = ([(f, DECLARED[f] == "LOW", "declared") for f in sorted(DECLARED)]
        + [(f, True, "undeclared_lo") for f in UNDECLARED]
        + [(f, False, "undeclared_hi") for f in UNDECLARED])
REVERSED_DIRS = [(f, DECLARED[f] != "LOW", "reversed") for f in sorted(DECLARED)]
assert len(DIRS) == 25 and len(REVERSED_DIRS) == 13 and len(FEATURES) == 19

RF, BORROW = 0.04, 0.0
SEED = 20260908
SQ2 = 3.0 - 2.0 * np.sqrt(2.0)

PANEL_CACHE = TEMP / "d383_panel.npz"
SCORE_CACHE = TEMP / "d383_scores.npz"
EVENT_CACHE = TEMP / "d383_events.npz"
OBSERVED = DATA / "d383_observed.json"
NULLS = DATA / "d383_nulls.json"
REPORT = DATA / "d383_ts_structure_screen.json"

_ESTIMATORS = ("ragged_features.py", "ragged_structure_scores.py", "ragged_profile.py",
               "run_macd_ladder.py", "ragged_panel.py")


def cache_key() -> str:
    """Fixture AND every estimator module's mtime. A stale cache is numbers that look fine."""
    parts = [f"{FIXTURE.name}:{FIXTURE.stat().st_mtime_ns}"]
    for f in _ESTIMATORS:
        parts.append(f"{f}:{(REPO / 'scripts' / f).stat().st_mtime_ns}")
    return "|".join(parts)


_PEAK = [0.0]


def rss_gb() -> float:
    try:
        import psutil
        return psutil.Process(os.getpid()).memory_info().rss / 1e9
    except Exception:                                            # pragma: no cover
        return float("nan")


def note_peak(label=""):
    g = rss_gb()
    if g == g and g > _PEAK[0]:
        _PEAK[0] = g
    if label:
        print(f"    [MEM] {label}: {g:.2f} GB (peak {_PEAK[0]:.2f} GB)", flush=True)
    return g


# ==========================================================================
# the mined panel
# ==========================================================================
class MinedPanel:
    """A `ragged_panel.RaggedPanel`-shaped view of the RECTANGULAR 15-minute panel, cut to the
    mining window. `live` is all-True by construction -- that is what makes it a panel, and what
    `load_panel` refuses to accept otherwise -- so `RP.score`, `RP.enforce_live` and
    `fast_null.NullContext` all work on it unchanged.

    `dates` is DATE-ONLY, exactly as `load_panel` builds it, and each value repeats ~26 times.
    Calendar quantities read `stamps` / `minutes`, never `dates` (s1 amendment)."""

    def __init__(self, symbols, stamps, closes, log_returns, total_log_returns, cost_fraction):
        self.symbols = tuple(symbols)
        self.stamps = list(stamps)
        self.dates = tuple(s[:10] for s in self.stamps)
        self.closes = closes
        self.log_returns = log_returns
        self.total_log_returns = total_log_returns
        self.cost_fraction = cost_fraction
        n, T = closes.shape
        self.live = np.ones((n, T), dtype=bool)
        self.index_of = {s: (0, T - 1) for s in self.symbols}
        ep = datetime(1970, 1, 1)
        self.minutes = np.array([(datetime.fromisoformat(s) - ep).total_seconds() / 60.0
                                 for s in self.stamps])

    @property
    def shape(self):
        return self.closes.shape

    def n_live(self):
        return self.live.sum(axis=0)

    def zero_cost(self):
        """The GROSS panel. R15: a signal is a positive GROSS mean per trade above its nulls."""
        return MinedPanel(self.symbols, self.stamps, self.closes, self.log_returns,
                          self.total_log_returns, np.zeros_like(self.cost_fraction))

    @property
    def ppy(self):
        """Bars per YEAR, measured off the panel's own timestamps -- never assumed."""
        span = (self.minutes[-1] - self.minutes[0]) / (365.25 * 1440.0)
        return self.shape[1] / span


# ---------------------------------------------------------------- [SPLIT]
def assert_SPLIT(stamps, dropped, n_full):
    """[SPLIT] default-deny. The BAR LISTS are cut, not only a grid; the cut is proved to have
    BITTEN (a cut that removes nothing guards nothing) and proved to have left nothing on or
    after the reserved boundary."""
    if dropped <= 0:
        raise AssertionError(
            "[SPLIT] cut nothing -- either the panel ends before the boundary or the comparison "
            "is not biting. A cut that cannot remove a bar guards nothing.")
    if len(stamps) == 0:
        raise AssertionError("[SPLIT] emptied the bar list")
    worst = max(s[:10] for s in stamps)
    if worst >= RESERVED_FIRST:
        raise AssertionError(f"[SPLIT] left a reserved bar in the panel: {worst}")
    if len(stamps) + dropped != n_full:
        raise AssertionError(f"[SPLIT] {len(stamps)} + {dropped} != {n_full} bars")
    return dict(mining_bars=len(stamps), reserved_bars_cut=dropped, boundary=MINING_END,
                first=stamps[0], last=stamps[-1])


def stage_prep(force=False):
    """Load through the DECLARED loader, cut to mining, cache the arrays. Everything downstream
    reads the cache and never touches a bar object again -- which is what keeps the later stages'
    working set under 400 MB."""
    print("\nPREP -- run_macd_ladder.load_panel on the 15-minute PANEL, cut to the mining window")
    if PANEL_CACHE.exists() and not force:
        z = np.load(PANEL_CACHE, allow_pickle=False)
        if str(z["_key"][0]) == cache_key():
            print(f"  cache hit {PANEL_CACHE.name}")
            return
        print("  cache key changed -- rebuilding")

    from backtest_framework.data.csv_fixture import load_fixture_csv_with_volumes
    ML = _load("run_macd_ladder", "run_macd_ladder.py")

    meta = RP.assert_gates_passed(FIXTURE)      # [GATE] -- explicit; load_panel makes no such call
    gate_names = sorted(k for k, v in meta["gates"].items()
                        if isinstance(v, dict) and "failures" in v)
    print(f"  [GATE] assert_gates_passed accepts {FIXTURE.name}: {', '.join(gate_names)}")

    stash = {}

    def _patched(path):
        """One CSV read, not two. `load_panel` needs the bars; the volume-profile axis needs the
        volumes, which `TimestampedBar` does not carry (D48/D60)."""
        bars, vols = load_fixture_csv_with_volumes(path)
        stash["ts"] = {s: [tb.timestamp for tb in bars[s]] for s in bars}
        stash["vol"] = vols
        return bars

    ML.FIXTURE, ML.EVENTS, ML.load_fixture_csv = FIXTURE, EVENTS_JSON, _patched
    t0 = time.time()
    panel, cleaned = ML.load_panel()                             # the DECLARED loader (s1 amendment)
    print(f"  load_panel {time.time() - t0:.0f}s -- {len(panel.symbols)} x "
          f"{panel.closes.shape[1]:,} bars, {panel.dividends_matched} dividends matched, "
          f"{panel.dividends_unmatched} unmatched")
    note_peak("after load_panel")

    symbols = list(panel.symbols)
    n_full = panel.closes.shape[1]
    full_stamps = [tb.timestamp.isoformat(sep=" ") for tb in cleaned[symbols[0]]]
    for s in symbols:                                  # rectangular: one timeline for every name
        if [tb.timestamp.isoformat(sep=" ") for tb in cleaned[s]] != full_stamps:
            raise AssertionError(f"{s}: the panel is not on one timeline")
    cut = sum(1 for s in full_stamps if s[:10] <= MINING_END)
    stamps = full_stamps[:cut]
    sp = assert_SPLIT(stamps, n_full - cut, n_full)
    print(f"  [SPLIT] {sp['mining_bars']:,} mining bars {sp['first']} -> {sp['last']}; "
          f"{sp['reserved_bars_cut']:,} reserved bars CUT from the bar lists")

    n = len(symbols)
    O = np.empty((n, cut)); H = np.empty((n, cut)); L = np.empty((n, cut))
    Cl = np.empty((n, cut)); V = np.empty((n, cut))
    for i, s in enumerate(symbols):
        bars = cleaned[s][:cut]
        O[i] = [b.bar.open for b in bars]
        H[i] = [b.bar.high for b in bars]
        L[i] = [b.bar.low for b in bars]
        Cl[i] = [b.bar.close for b in bars]
        vm = dict(zip(stash["ts"][s], stash["vol"][s]))
        V[i] = [vm[b.timestamp] for b in bars]         # matched on TIMESTAMP, never on index
    note_peak("grids built")

    TEMP.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        PANEL_CACHE, open=O, high=H, low=L, close=Cl, volume=V,
        closes=panel.closes[:, :cut], log_returns=panel.log_returns[:, :cut],
        total_log_returns=panel.total_log_returns[:, :cut],
        cost_fraction=panel.cost_fraction,
        _symbols=np.array(symbols), _stamps=np.array(stamps),
        _key=np.array([cache_key()]), _split=np.array([json.dumps(sp)]),
        _divs=np.array([panel.dividends_matched, panel.dividends_unmatched]))
    print(f"  wrote {PANEL_CACHE.relative_to(REPO)}")
    note_peak("prep done")


def load_mined():
    """Everything downstream loads THIS -- arrays only, no bar objects."""
    if not PANEL_CACHE.exists():
        raise FileNotFoundError(f"{PANEL_CACHE} missing -- run --prep first")
    z = np.load(PANEL_CACHE, allow_pickle=False)
    if str(z["_key"][0]) != cache_key():
        raise AssertionError(f"{PANEL_CACHE.name} is STALE (fixture or estimator mtime changed) "
                             "-- re-run --prep --force. A stale cache is numbers that look fine.")
    symbols = [str(s) for s in z["_symbols"]]
    stamps = [str(s) for s in z["_stamps"]]
    panel = MinedPanel(symbols, stamps, z["closes"], z["log_returns"],
                       z["total_log_returns"], z["cost_fraction"])
    g = {k: z[k] for k in ("open", "high", "low", "close", "volume")}
    sp = json.loads(str(z["_split"][0]))
    if sp["last"][:10] > MINING_END or panel.dates[-1] > MINING_END:
        raise AssertionError(f"[SPLIT] the cached panel runs to {sp['last']}, past {MINING_END}")
    return panel, g, sp


# ==========================================================================
# the 19 features -- the SAME estimators D382 called, on a different object
# ==========================================================================
def _stamped(stamps, O, H, L, C):
    from backtest_framework.data.bars import TimestampedBar
    from backtest_framework.simulator.fills import Bar
    ts = [datetime.fromisoformat(s) for s in stamps]
    return [TimestampedBar(ts[j], Bar(O[j], H[j], L[j], C[j])) for j in range(len(ts))]


def features_for(panel, g, rows):
    """The 19 grids for `rows`, a stride of symbol indices."""
    sub = [panel.symbols[i] for i in rows]
    gg = {k: np.ascontiguousarray(g[k][rows]) for k in ("open", "high", "low", "close")}
    live = np.ones(gg["close"].shape, dtype=bool)
    out = {}
    b = FB.intrabar_scores(gg, live)
    for k in FB.INTRABAR_SCORES:
        out[k] = np.asarray(b[k], float)

    cleaned = {s: _stamped(panel.stamps, gg["open"][i], gg["high"][i], gg["low"][i], gg["close"][i])
               for i, s in enumerate(sub)}

    class _P:
        symbols = tuple(sub)
        closes = gg["close"]

    h = ST.structure_scores(gg, cleaned, _P(), live)
    for k in ST.STRUCTURE_SCORES:
        out[k] = np.asarray(h[k], float)
    # rebuild_every defaults to 1 -- D382's own call, unchanged (s1 amendment: only the OBJECT
    # changes). A once-per-session cadence loses 15% of mass_here/mass_imbalance coverage.
    d, census = PR.build_profile_scores(_P(), cleaned, np.ascontiguousarray(g["volume"][rows]),
                                        WARMUP, live=live)
    for k in PR.PROFILE_SCORES:
        out[k] = np.asarray(d[k], float)
    return out, census


def _worker_main(argv):
    """One process's stride of symbols. PROCESSES, not threads: `structure_scores` and the
    volume-profile sensor are GIL-bound pure Python (D288's lesson, fast_null's efficiency floor).
    STRIDE, not slice -- though this panel is rectangular, so the strides are equal by
    construction and `--features` asserts every symbol was written exactly once."""
    k, nw, path = int(argv[0]), int(argv[1]), Path(argv[2])
    panel, g, _sp = load_mined()
    rows = np.arange(len(panel.symbols))[k::nw]
    t0 = time.time()
    sc, census = features_for(panel, g, rows)
    np.savez_compressed(path, _rows=rows, _census=np.array([json.dumps(census)]), **sc)
    print(f"    worker {k}: {rows.size} symbols in {time.time() - t0:.0f}s, "
          f"{rss_gb():.2f} GB", flush=True)


def stage_features(workers=4, force=False):
    print(f"\nFEATURES -- the 19 grids on the mining panel ({workers} processes)")
    if SCORE_CACHE.exists() and not force:
        z = np.load(SCORE_CACHE, allow_pickle=False)
        if str(z["_key"][0]) == cache_key():
            print(f"  cache hit {SCORE_CACHE.name}")
            return
        print("  cache key changed -- rebuilding")
    panel, _g, _sp = load_mined()
    n, T = panel.shape
    t0 = time.time()

    parts = [TEMP / f"d383_feat_{k}.npz" for k in range(workers)]
    procs = [subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
                               "--worker", str(k), str(workers), str(parts[k])])
             for k in range(workers)]
    for p in procs:
        if p.wait() != 0:
            raise RuntimeError(f"a feature worker exited {p.returncode}")

    out = {k: np.full((n, T), np.nan) for k in FEATURES}
    census = {"too_short": 0, "no_density": 0, "with_profile": 0, "symbols": 0}
    seen = np.zeros(n, bool)
    for path in parts:
        # `np.load` returns a LAZY HANDLE Windows will not let you delete until it is closed
        # (PICKUP 0f). Closed here rather than at garbage-collection time.
        with np.load(path, allow_pickle=False) as z:
            rows = z["_rows"]
            if seen[rows].any():
                raise AssertionError("[STRIDE] the strides overlap -- a symbol would be written twice")
            seen[rows] = True
            for k in FEATURES:
                out[k][rows] = z[k]
            c = json.loads(str(z["_census"][0]))
        for kk in census:
            census[kk] += c.get(kk, 0)
    if not seen.all():
        raise AssertionError(f"[STRIDE] {int((~seen).sum())} symbols were never built")
    print(f"  built in {time.time() - t0:.0f}s; volume-profile census {census}")
    for k in FEATURES:
        cov = float(np.isfinite(out[k]).sum()) / (n * T)
        print(f"    {k:<16} coverage {cov:6.1%}   "
              f"[{np.nanmin(out[k]):+.4g}, {np.nanmax(out[k]):+.4g}]")
    np.savez_compressed(SCORE_CACHE, _key=np.array([cache_key()]),
                        _census=np.array([json.dumps(census)]), **out)
    for path in parts:
        path.unlink()
    print(f"  wrote {SCORE_CACHE.relative_to(REPO)}")
    note_peak("features done")


# ==========================================================================
# s2 -- the TRAILING percentile, and [TS]
# ==========================================================================
def pct_trailing(x, W, min_obs=MIN_TRAILING_OBS):
    """The percentile of x[i,t] WITHIN THAT NAME'S OWN TRAILING x[i, t-W .. t-1]:

        pct = 100 * (#{trailing < x[t]} + 0.5 * #{trailing == x[t]}) / #{trailing finite}

    Mid-rank -- D382's own `100*(r + 0.5)/k` convention written for a window that EXCLUDES the
    ranked point. NaN where x[t] is not finite or fewer than `min_obs` trailing observations
    exist (D382's `k < 20: continue`, inherited rather than invented).

    THE WINDOW NEVER CONTAINS BAR t. `rolling(W+1)` spans x[t-W .. t] because that is the only
    way pandas will rank x[t] at all; x[t]'s own contribution is then removed EXACTLY:

        rank(min) = 1 + #{window < x[t]} = 1 + #{trailing < x[t]}   (x[t] is not < itself)
        rank(max) = #{window <= x[t]}    = 1 + #{trailing < x[t]} + #{trailing == x[t]}
        count     = 1 + #{trailing finite}

    so `below = rmin - 1`, `ties = rmax - rmin`, `weff = count - 1`, with no residue.
    `assert_TS` proves the result against a literal `x[i, t-W:t]` slice, and `[X]` proves that
    assertion RAISES on a percentile that peeks at bar t."""
    import pandas as pd
    r = pd.DataFrame(x.T).rolling(W + 1, min_periods=1)
    rmin = r.rank(method="min").to_numpy().T
    rmax = r.rank(method="max").to_numpy().T
    cnt = r.count().to_numpy().T
    below = rmin - 1.0
    ties = rmax - rmin
    weff = cnt - 1.0
    with np.errstate(invalid="ignore", divide="ignore"):
        p = 100.0 * (below + 0.5 * ties) / weff
    p[~np.isfinite(x)] = np.nan
    p[weff < min_obs] = np.nan
    return p


def pct_peeking(x, W, min_obs=MIN_TRAILING_OBS):
    """[X] THE BROKEN ONE -- the window is t-W .. t INCLUSIVE, so bar t ranks against itself.
    Never called by the study; it exists so `assert_TS` can be shown to fail."""
    import pandas as pd
    r = pd.DataFrame(x.T).rolling(W + 1, min_periods=1)
    rmin = r.rank(method="min").to_numpy().T
    rmax = r.rank(method="max").to_numpy().T
    cnt = r.count().to_numpy().T
    with np.errstate(invalid="ignore", divide="ignore"):
        p = 100.0 * ((rmin - 1.0) + 0.5 * (rmax - rmin + 1.0)) / cnt
    p[~np.isfinite(x)] = np.nan
    p[cnt - 1.0 < min_obs] = np.nan
    return p


def pct_brute(x, W, i, t, min_obs=MIN_TRAILING_OBS):
    """A LITERAL slice of the trailing window. It cannot contain bar t: `x[i, t-W:t]` stops one
    short of it, which is the whole point."""
    v = x[i, t]
    if not np.isfinite(v):
        return float("nan")
    w = x[i, max(0, t - W):t]
    w = w[np.isfinite(w)]
    if w.size < min_obs:
        return float("nan")
    return 100.0 * (float((w < v).sum()) + 0.5 * float((w == v).sum())) / w.size


def assert_TS(x, W, p, n_probe=500, seed=0):
    """[TS] the trailing percentile reads ONLY t-W .. t-1, never bar t itself. Two probes:

      (a) EXACT equality against `pct_brute`, whose window is a literal slice ending at t-1.
          This is the decisive one -- a peeking percentile disagrees on every bar.
      (b) the pre-registration's own probe: set bar t to an extreme and require the percentile
          to be EXACTLY 100. A peeking window puts x[t] in its own comparison set, so it can
          only reach 100*(k + 0.5)/(k + 1) < 100, and this fires too."""
    rng = np.random.default_rng(seed)
    n, T = x.shape
    bad = 0
    for _ in range(n_probe):
        i = int(rng.integers(0, n))
        t = int(rng.integers(WARMUP, T))
        a, b = p[i, t], pct_brute(x, W, i, t)
        if not (a == b or (a != a and b != b)):
            bad += 1
            if bad <= 3:
                print(f"       [TS] MISMATCH ({i},{t}): fast {a!r} vs literal slice {b!r}")
    if bad:
        raise AssertionError(f"[TS] the percentile disagrees with a literal t-W..t-1 slice on "
                             f"{bad}/{n_probe} probes -- it is reading bar t")
    hits = 0
    for _ in range(80):
        i = int(rng.integers(0, n))
        t = int(rng.integers(WARMUP, T))
        w = x[i, max(0, t - W):t]
        if np.isfinite(w).sum() < MIN_TRAILING_OBS:
            continue
        y = np.concatenate([w, [1e12]])
        v = pct_brute(y[None, :], W, 0, y.size - 1)
        if v == v:
            hits += 1
            if v != 100.0:
                raise AssertionError(f"[TS] an extreme at bar t scores {v!r}, not exactly 100 -- "
                                     "bar t is inside its own comparison window")
    return dict(probes=n_probe, extreme_probes=hits)


# ==========================================================================
# events, books, trades
# ==========================================================================
def events_of(p, tail_low):
    """s2: the percentile CROSSING INTO the extreme decile. `tail_low` selects the LOW decile."""
    prev = np.full_like(p, np.nan)
    prev[:, 1:] = p[:, :-1]
    with np.errstate(invalid="ignore"):
        ev = (((p <= DECILE) & (prev > DECILE)) if tail_low
              else ((p >= 100.0 - DECILE) & (prev < 100.0 - DECILE)))
    ev[:, :WARMUP] = False
    return ev


def eligible_of(p):
    """The bars a book COULD have entered on -- the percentile is defined and the warm-up is
    past. The matched-count null draws from exactly this mask, per name: a null that trades bars
    the study could not enter is not a control (D347's rotation traded the sub-$5 tail, D351)."""
    e = np.isfinite(p)
    e[:, :WARMUP] = False
    return e


def runs_from_events(rows, cols, n, T, hold):
    """The LINEAR runs of the long-flat book: every event at t holds [t+1, t+1+hold), merged
    where they overlap or touch. Equal-length intervals with sorted starts merge in one pass --
    a new run begins at event k iff t_k > t_{k-1} + hold. `assert_POS` proves this equals the
    per-event loop and the difference-array grid."""
    if rows.size == 0:
        z64 = np.zeros(0, np.int64)
        return np.zeros(0, np.int64), z64, z64
    order = np.lexsort((cols, rows))
    r, c = rows[order], cols[order]
    new = np.ones(r.size, bool)
    new[1:] = (r[1:] != r[:-1]) | (c[1:] > c[:-1] + hold)
    starts = np.flatnonzero(new)
    ends = np.append(starts[1:], r.size) - 1                # last event of each merged chain
    a = c[starts] + LAG
    b = np.minimum(c[ends] + LAG + hold, T)
    keep = a < T
    return (r[starts][keep].astype(np.int64), a[keep].astype(np.int64),
            (b - a)[keep].astype(np.int64))


def trades_of_runs(row, a, L, C, T, off=None):
    """Per-trade gross return in bp, each trade's length in bars, and its (row, start).

    `off` rotates each name's book CIRCULARLY -- exactly `np.roll(pos[i], off[i])`. A run that
    crosses the wrap becomes two trades, which is what rolling the grid produces; the output is
    ordered by (row, start), so the sums run in the grid kernel's own order and the means are
    bit-identical rather than merely close."""
    if row.size == 0:
        return np.zeros(0), np.zeros(0), np.zeros(0, np.int64), np.zeros(0, np.int64)
    if off is None:
        r2, s, e = row, a, a + L
    else:
        s = (a + off[row]) % T
        e = s + L
        over = e > T
        m = int(over.sum())
        r2 = np.concatenate([row, row[over]])
        s = np.concatenate([s, np.zeros(m, dtype=s.dtype)])
        e = np.concatenate([np.where(over, T, e), e[over] - T])
    order = np.lexsort((s, r2))
    r2, s, e = r2[order], s[order], e[order]
    lo = np.where(s > 0, C[r2, np.maximum(s - 1, 0)], 0.0)
    hi = C[r2, e - 1]
    return np.expm1(hi - lo) * 1e4, (e - s).astype(float), r2, s


def positions_grid(rows, cols, n, T, hold):
    """[POS] the (n, T) book, built by a difference array from the events."""
    d = np.zeros((n, T + 1), dtype=np.int32)
    np.add.at(d, (rows, np.minimum(cols + LAG, T)), 1)
    np.add.at(d, (rows, np.minimum(cols + LAG + hold, T)), -1)
    pos = np.cumsum(d[:, :T], axis=1) > 0
    pos[:, :WARMUP] = False
    return pos


def positions_loop(rows, cols, n, T, hold):
    """[POS] the same book by a per-event Python loop -- the slow one the fast paths must equal."""
    pos = np.zeros((n, T), dtype=bool)
    for i, t in zip(rows, cols):
        pos[i, t + LAG:min(t + LAG + hold, T)] = True
    pos[:, :WARMUP] = False
    return pos


def trades_grid(pos, C):
    """[POS] trades read off the (n, T) grid -- the kernel `trades_of_runs` replaces."""
    d = np.diff(pos.astype(np.int8), axis=1, prepend=0, append=0)
    si, st = np.nonzero(d == 1)
    ei, et = np.nonzero(d == -1)
    if si.size == 0:
        return np.zeros(0), np.zeros(0)
    lo = np.where(st > 0, C[si, np.maximum(st - 1, 0)], 0.0)
    hi = C[ei, np.minimum(et - 1, C.shape[1] - 1)]
    return np.expm1(hi - lo) * 1e4, (et - st).astype(float)


def roll_rows(pos, off):
    out = np.empty_like(pos)
    for i in range(pos.shape[0]):
        out[i] = np.roll(pos[i], int(off[i]))
    return out


def circ_runs_of(pos):
    """The CIRCULAR runs of a boolean book. A row's head and tail runs are ONE run when they
    touch across the wrap, because that is what `np.roll` makes of them."""
    d = np.diff(pos.astype(np.int8), axis=1, prepend=0, append=0)
    si, st = np.nonzero(d == 1)
    ei, et = np.nonzero(d == -1)
    row, a, L = si.astype(np.int64), st.astype(np.int64), (et - st).astype(np.int64)
    keep = np.ones(row.size, bool)
    for i in np.flatnonzero(pos[:, 0] & pos[:, -1]):
        idx = np.flatnonzero(row == i)
        if idx.size < 2:
            continue                       # a fully covered row is already one circular run
        L[idx[-1]] += L[idx[0]]
        keep[idx[0]] = False
    return row[keep], a[keep], L[keep]


def trade_cumsum(panel):
    """One cumulative sum of each name's TOTAL log return, reused by every draw."""
    tl = np.where(np.isfinite(panel.total_log_returns), panel.total_log_returns, 0.0)
    return np.cumsum(tl, axis=1)


# ==========================================================================
# audits
# ==========================================================================
def assert_LAG(p, tail_low, hold, n, T, span=6000):
    """[LAG] exposure through bar t is decided on t-1, RE-DERIVED BY A SECOND IMPLEMENTATION
    that never calls `events_of`, `runs_from_events` or either position builder. It reads the
    percentile grid directly, bar by bar, in pure Python."""
    hi = min(T, WARMUP + span)
    lo = max(1, WARMUP - hold - 2)
    rows, cols = np.nonzero(events_of(p, tail_low))
    fast = positions_grid(rows, cols, n, T, hold)
    ref = np.zeros((n, T), dtype=bool)
    for i in range(n):
        row = p[i]
        for t in range(lo, hi):
            v, u = row[t], row[t - 1]
            if v != v or u != u or t < WARMUP:
                continue
            fires = (v <= DECILE < u) if tail_low else (v >= 100.0 - DECILE > u)
            if fires:
                ref[i, t + LAG:min(t + LAG + hold, T)] = True
    ref[:, :WARMUP] = False
    if not np.array_equal(fast[:, WARMUP:hi], ref[:, WARMUP:hi]):
        raise AssertionError("[LAG] the second implementation disagrees -- the book may read bar t")
    return True


def assert_POS(rows, cols, n, T, hold, C, off):
    """[POS] three builders and two trade kernels agree BIT-FOR-BIT: the per-event loop, the
    difference-array grid, and the run kernel -- rotated and not. The 4.7x speed is only allowed
    because this equality is checked, not assumed."""
    a = positions_loop(rows, cols, n, T, hold)
    b = positions_grid(rows, cols, n, T, hold)
    if not np.array_equal(a, b):
        raise AssertionError("[POS] the difference-array builder disagrees with the per-event loop")
    r, s, L = runs_from_events(rows, cols, n, T, hold)
    g_tr, g_ln = trades_grid(b, C)
    k_tr, k_ln, _, _ = trades_of_runs(r, s, L, C, T)
    if not (np.array_equal(g_tr, k_tr) and np.array_equal(g_ln, k_ln)):
        raise AssertionError("[POS] the run kernel disagrees with the grid kernel (unrotated)")
    cr, ca, cL = circ_runs_of(b)
    g_tr, g_ln = trades_grid(roll_rows(b, off), C)
    k_tr, k_ln, _, _ = trades_of_runs(cr, ca, cL, C, T, off)
    if not (np.array_equal(g_tr, k_tr) and np.array_equal(g_ln, k_ln)):
        raise AssertionError("[POS] the run kernel disagrees with the grid kernel (rotated)")
    return True


def assert_BH(panel, start, ppy):
    """[BH] buy-and-hold at MATCHED exposure. Refuses to produce an excess without a comparator."""
    s = RP.score(panel, np.ones(panel.shape), start, ppy=ppy, rf_annual=RF, borrow_annual=BORROW)
    if not s["exposure_gross"] > 0.9:
        raise AssertionError(f"[BH] the comparator's exposure is {s['exposure_gross']:.3f}, not ~1")
    return s


def assert_SIGN(panel, ppy, scorer=None):
    """[SIGN] the sign audit, IN MONEY. A favourable move must PAY, and the same move must pay a
    long and a short OPPOSITELY. A sign asserted in prose inverted D280; this one is asserted on
    the scorer's own output. `scorer` is injectable so `[X]` can hand it a sign-blind one."""
    sc = scorer or (lambda p: RP.score(panel, p, WARMUP, ppy=ppy, rf_annual=0.0, borrow_annual=0.0))
    n, T = panel.shape
    up = np.zeros((n, T))
    good = int(np.argmax(panel.total_log_returns[0, WARMUP:])) + WARMUP
    up[0, good] = 1.0
    a, b = sc(up), sc(-up)
    if not a["total_return"] > 0:
        raise AssertionError(f"[SIGN] a long through the best bar returns {a['total_return']:+.6f}")
    if not b["total_return"] < 0:
        raise AssertionError(f"[SIGN] a short through the best bar returns {b['total_return']:+.6f}")
    if abs(a["total_return"] + b["total_return"]) > 1e-9:
        raise AssertionError("[SIGN] long and short do not move oppositely on the same bar")
    # AND THE DIVIDEND, in money and in opposite directions. On the largest ex-dividend bar in
    # the panel, holding LONG through it must earn the distribution and holding SHORT must OWE it.
    ex = panel.total_log_returns - panel.log_returns
    i_d, t_d = np.unravel_index(int(np.argmax(ex)), ex.shape)
    if float(ex[i_d, t_d]) <= 0.0:
        raise AssertionError("[SIGN] no ex-dividend bar carries a positive distribution")
    Ct = trade_cumsum(panel)
    Cp = np.cumsum(np.where(np.isfinite(panel.log_returns), panel.log_returns, 0.0), axis=1)
    r_ = np.array([i_d], np.int64); s_ = np.array([t_d], np.int64); L_ = np.array([1], np.int64)
    tot_bp = float(trades_of_runs(r_, s_, L_, Ct, T)[0][0])
    px_bp = float(trades_of_runs(r_, s_, L_, Cp, T)[0][0])
    if not (tot_bp - px_bp) > 0:
        raise AssertionError(f"[SIGN] a LONG through the ex-dividend bar earns "
                             f"{tot_bp - px_bp:+.4f} bp from the distribution, not a gain")
    if not (-tot_bp) - (-px_bp) < 0:
        raise AssertionError("[SIGN] a SHORT through the ex-dividend bar does not owe the distribution")
    return dict(best_bar_long=a["total_return"], best_bar_short=b["total_return"],
                max_dividend_log=float(ex[i_d, t_d]),
                div_bar=f"{panel.symbols[i_d]} {panel.stamps[t_d]}",
                div_long_bp=tot_bp - px_bp, div_short_bp=(-tot_bp) - (-px_bp))


def assert_QTY(panel, rows, cols, hold=PRIMARY_HOLD):
    """[QTY] right-quantity: the compounded grid I MEANT to score differs from the one I did
    not. `total_log_returns` (dividends reinvested on the ex-date bar) is not `log_returns`
    (price only), and this book is scored on the first."""
    a = trade_cumsum(panel)
    b = np.cumsum(np.where(np.isfinite(panel.log_returns), panel.log_returns, 0.0), axis=1)
    if np.array_equal(a, b):
        raise AssertionError("[QTY] the total-return and price-return grids are identical -- the "
                             "dividend leg is not being compounded")
    n, T = panel.shape
    r, s, L = runs_from_events(rows, cols, n, T, hold)
    ta, _, _, _ = trades_of_runs(r, s, L, a, T)
    tb, _, _, _ = trades_of_runs(r, s, L, b, T)
    if float(ta.mean()) == float(tb.mean()):
        raise AssertionError("[QTY] the two grids score this book identically")
    return dict(total_return_mean_bp=float(ta.mean()), price_return_mean_bp=float(tb.mean()))


# ==========================================================================
# cost, reported beside the primary (R15: gross decides at the signal stage)
# ==========================================================================
def corwin_schultz(H, L):
    """Per-bar proportional ROUND-TRIP spread. Lifted from
    `scripts/d285_spread_estimate.corwin_schultz`, whose `live` is all-True on this panel.
    D285 missed a guessed 15 bp/side bar by 0.65 and the HELD names measured 33.8 -- so the
    spread reported here is the one the held names actually printed, not a fee assumption."""
    h1, l1, h2, l2 = H[:, :-1], L[:, :-1], H[:, 1:], L[:, 1:]
    ok = np.isfinite(h1) & np.isfinite(h2) & (l1 > 0) & (l2 > 0)
    with np.errstate(invalid="ignore", divide="ignore"):
        b = np.log(h1 / l1) ** 2 + np.log(h2 / l2) ** 2
        gg = np.log(np.maximum(h1, h2) / np.minimum(l1, l2)) ** 2
        a = (np.sqrt(2.0 * b) - np.sqrt(b)) / SQ2 - np.sqrt(gg / SQ2)
        s = 2.0 * np.expm1(a) / (1.0 + np.exp(a))
    s = np.where(ok & np.isfinite(s), np.maximum(s, 0.0), np.nan)
    out = np.full(H.shape, np.nan)
    out[:, :-1] = s
    return out


# ==========================================================================
# the observed pass
# ==========================================================================
def _dist(tr):
    """CLAUDE.md group 2 -- the trade distribution, with the SYMMETRIC 1% trim and all three
    means. Dropping only winners is a flag, not a verdict (D307)."""
    m = tr.size
    if m == 0:
        return {}
    q_lo, q_hi = np.percentile(tr, [1.0, 99.0])
    sd = float(tr.std(ddof=1)) if m > 1 else float("nan")
    z = (tr - tr.mean()) / sd if sd == sd and sd > 0 else np.zeros(m)
    wins, losses = tr[tr > 0], tr[tr <= 0]
    tot = float(tr.sum())
    return dict(
        n=int(m), mean_bp=float(tr.mean()), median_bp=float(np.median(tr)), sd_bp=sd,
        win_rate=float((tr > 0).mean()),
        payoff=(float(wins.mean() / abs(losses.mean()))
                if losses.size and losses.mean() != 0 and wins.size else float("nan")),
        skew=float((z ** 3).mean()), kurtosis=float((z ** 4).mean()),
        mean_ex_top1=float(tr[tr <= q_hi].mean()), mean_ex_bottom1=float(tr[tr >= q_lo].mean()),
        mean_trimmed1=float(tr[(tr >= q_lo) & (tr <= q_hi)].mean()),
        top1pct_share_of_pnl=float(tr[tr >= q_hi].sum() / tot) if tot else float("nan"),
        mean_below_median=bool(float(tr.mean()) < float(np.median(tr))))


def _winners(tr, rows, starts, panel):
    """CLAUDE.md group 3 -- what the winners depend on. The top trade is NAMED and its bar
    printed: D322 reported the share, never looked, and 15 studies ran on fabricated days."""
    symbols = panel.symbols
    tot = float(tr.sum())
    per = np.zeros(len(symbols))
    np.add.at(per, rows, tr)
    order = np.argsort(-per)
    csum = np.cumsum(per[order])
    half = int(np.searchsorted(csum, 0.5 * tot) + 1) if tot > 0 else -1
    yrs = np.array([int(panel.stamps[t][:4]) for t in starts])
    by_year = {}
    for y in sorted(set(int(v) for v in yrs)):
        v = tr[yrs == y]
        by_year[int(y)] = dict(n=int(v.size), mean_bp=float(v.mean()), total_bp=float(v.sum()))
    px = panel.closes[rows, starts]
    lo = px <= np.median(px)
    top = int(np.argmax(tr))
    return dict(
        names_to_half_pnl=half, n_names=int((per != 0).sum()),
        top1_name_share=float(per[order[0]] / tot) if tot else float("nan"),
        top5_name_share=float(per[order[:5]].sum() / tot) if tot else float("nan"),
        top10_name_share=float(per[order[:10]].sum() / tot) if tot else float("nan"),
        top_names=[symbols[i] for i in order[:5]],
        by_year=by_year, profitable_years=int(sum(1 for v in by_year.values() if v["total_bp"] > 0)),
        low_price_half_mean_bp=float(tr[lo].mean()), high_price_half_mean_bp=float(tr[~lo].mean()),
        price_median=float(np.median(px)),
        top_trade=dict(symbol=symbols[int(rows[top])], entry_bar=panel.stamps[int(starts[top])],
                       bp=float(tr[top]),
                       share_of_pnl=float(tr[top] / tot) if tot else float("nan")))


def cell_row(panel, panel0, rows, cols, hold, C, cs_half, ppy, full=False):
    """One cell. GROSS is the primary (R15); NET is computed beside it and decides nothing here."""
    n, T = panel.shape
    if rows.size < 50:
        return None
    r, s, L = runs_from_events(rows, cols, n, T, hold)
    tr, ln, trow, tstart = trades_of_runs(r, s, L, C, T)
    if tr.size < 30:
        return None
    pos = positions_grid(rows, cols, n, T, hold).astype(float)   # RP.legs negates it
    sg = RP.score(panel0, pos, WARMUP, ppy=ppy, rf_annual=RF, borrow_annual=BORROW)
    sn = RP.score(panel, pos, WARMUP, ppy=ppy, rf_annual=RF, borrow_annual=BORROW)
    bh = RP.score(panel0, np.full((n, T), sg["exposure_gross"]), WARMUP,
                  ppy=ppy, rf_annual=RF, borrow_annual=BORROW)
    # NET per trade: one round trip of that NAME's own IBKR per-side cost, charged in bp.
    net_tr = tr - 2.0 * panel.cost_fraction[trow] * 1e4
    held = cs_half[trow, tstart]                       # the spread of the names actually HELD
    mins = panel.minutes[np.minimum((tstart + ln - 1).astype(np.int64), T - 1)] \
        - panel.minutes[tstart]
    out = dict(
        events=int(rows.size), trades=int(tr.size),
        mean_bp=float(tr.mean()), median_bp=float(np.median(tr)),
        bp_per_bar=float(tr.sum() / ln.sum()) if ln.sum() > 0 else float("nan"),
        mean_run_bars=float(ln.mean()), median_run_bars=float(np.median(ln)),
        median_run_minutes=float(np.median(mins)), mean_run_minutes=float(mins.mean()),
        net_mean_bp=float(net_tr.mean()),
        entries_per_year=float(sg["entries"] * ppy / (T - WARMUP)),
        turnover_per_bar=float(sg["turnover_units"] / (n * (T - WARMUP))),
        exposure=sg["exposure_gross"], vol=sg["vol"], max_drawdown=sg["max_drawdown"],
        gross_cagr=sg["cagr"], gross_sharpe=sg["excess_sharpe"],
        net_cagr=sn["cagr"], net_sharpe=sn["excess_sharpe"],
        bh_matched_cagr=bh["cagr"], bh_matched_sharpe=bh["excess_sharpe"],
        excess_over_bh_cagr=sg["cagr"] - bh["cagr"],
        held_half_spread_bp=float(np.nanmedian(held)) if held.size else float("nan"),
        ibkr_half_cost_bp=float(np.mean(panel.cost_fraction[trow]) * 1e4),
        breakeven_bp_per_side=float(tr.mean()) / 2.0,
        clears_E=bool(sg["clears_E"]))
    if full:
        out["distribution"] = _dist(tr)
        out["winners"] = _winners(tr, trow, tstart, panel)
    return out


def stage_events(force=False):
    """The 114 percentile grids, reduced to compact event index arrays. ONE grid is alive at a
    time -- the 600-cell grid is never materialised."""
    print(f"\nEVENTS -- {len(FEATURES)} features x {len(WINDOWS)} windows, one grid at a time")
    if EVENT_CACHE.exists() and not force:
        z = np.load(EVENT_CACHE, allow_pickle=False)
        if str(z["_key"][0]) == cache_key():
            print(f"  cache hit {EVENT_CACHE.name}")
            return
        print("  cache key changed -- rebuilding")
    panel, _g, _sp = load_mined()
    n, T = panel.shape
    zs = np.load(SCORE_CACHE, allow_pickle=False)
    out, meta = {}, {}
    t0 = time.time()
    # [TS] is checked on the FIRST feature-window AND on the two THREE-VALUED features -- ties are
    # where a rank rewrite disagrees, and `struct_trend` and `fvg_signed` are all ties.
    ts_on = {(FEATURES[0], WINDOWS[0]), ("struct_trend", WINDOWS[0]), ("struct_trend", WINDOWS[-1]),
             ("fvg_signed", WINDOWS[2]), ("range_frac", WINDOWS[3])}
    ts_report = {}
    for f in FEATURES:
        x = zs[f]
        for W in WINDOWS:
            p = pct_trailing(x, W)
            if (f, W) in ts_on:
                ts_report[f"{f}|{W}"] = assert_TS(x, W, p)
                print(f"  [TS] {f}|W{W}: the percentile equals a literal t-W..t-1 slice on "
                      f"{ts_report[f'{f}|{W}']['probes']} probes; an extreme at bar t scores "
                      f"exactly 100 on {ts_report[f'{f}|{W}']['extreme_probes']} probes")
            elig = eligible_of(p)
            for tail, tag in ((True, "lo"), (False, "hi")):
                r, c = np.nonzero(events_of(p, tail))
                out[f"{f}|{W}|{tag}|r"] = r.astype(np.int32)
                out[f"{f}|{W}|{tag}|c"] = c.astype(np.int32)
            out[f"{f}|{W}|elig"] = np.packbits(elig, axis=1)     # 275 KB, not 17.6 MB
            meta[f"{f}|{W}"] = dict(eligible=int(elig.sum()),
                                    events_lo=int(out[f"{f}|{W}|lo|r"].size),
                                    events_hi=int(out[f"{f}|{W}|hi|r"].size))
            del p, elig
        print(f"    {f:<16} {time.time() - t0:5.0f}s  " +
              "  ".join(f"W{W}:{meta[f'{f}|{W}']['events_lo']:>6,}/"
                        f"{meta[f'{f}|{W}']['events_hi']:>6,}" for W in WINDOWS), flush=True)
        note_peak()
    np.savez_compressed(EVENT_CACHE, _key=np.array([cache_key()]),
                        _meta=np.array([json.dumps(meta)]),
                        _ts=np.array([json.dumps(ts_report)]),
                        _shape=np.array([n, T]), **out)
    print(f"  wrote {EVENT_CACHE.relative_to(REPO)} ({time.time() - t0:.0f}s)")
    note_peak("events done")


def _ev(z, f, W, tag):
    return z[f"{f}|{W}|{tag}|r"].astype(np.int64), z[f"{f}|{W}|{tag}|c"].astype(np.int64)


def _elig(z, f, W, T):
    return np.unpackbits(z[f"{f}|{W}|elig"], axis=1, count=T).astype(bool)


def stage_observed():
    print(f"\nOBSERVED -- {len(DIRS)} declared directions x {len(WINDOWS)} windows x {len(HOLDS)} "
          f"holds = {len(DIRS) * len(WINDOWS) * len(HOLDS)} cells; "
          f"{len(REVERSED_DIRS) * len(WINDOWS) * len(HOLDS)} reversed cells reported SEPARATELY "
          f"([DIR], gate 1h)")
    t0 = time.time()
    panel, g, sp = load_mined()
    panel0 = panel.zero_cost()
    n, T = panel.shape
    ppy = panel.ppy
    C = trade_cumsum(panel)
    cs_half = corwin_schultz(g["high"], g["low"]) / 2.0 * 1e4

    audits = {}
    audits["BH"] = assert_BH(panel0, WARMUP, ppy)
    print(f"  [BH] unit-exposure buy-and-hold, GROSS: CAGR {audits['BH']['cagr']:+.2%}  "
          f"Sharpe {audits['BH']['excess_sharpe']:+.3f}   (ppy = {ppy:,.0f} bars/yr)")
    audits["SIGN"] = assert_SIGN(panel0, ppy)
    print(f"  [SIGN] a long through the best bar pays {audits['SIGN']['best_bar_long']:+.6f}, the "
          f"short {audits['SIGN']['best_bar_short']:+.6f}; on {audits['SIGN']['div_bar']} the "
          f"dividend pays a long {audits['SIGN']['div_long_bp']:+.2f} bp and costs a short "
          f"{audits['SIGN']['div_short_bp']:+.2f} bp")
    print(f"  [COST] IBKR per side, median over names {np.median(panel.cost_fraction) * 1e4:.3f} bp;"
          f"  Corwin-Schultz half-spread over all name-bars, median {np.nanmedian(cs_half):.2f} bp")

    z = np.load(EVENT_CACHE, allow_pickle=False)
    f0, W0 = FEATURES[0], WINDOWS[0]
    r0, c0 = _ev(z, f0, W0, "lo")
    rng = np.random.default_rng([SEED, STUDY, 0])
    audits["POS"] = bool(assert_POS(r0, c0, n, T, HOLDS[0], C, rng.integers(0, T, size=n)))
    print(f"  [POS] loop == grid == run kernel, rotated and not, on {f0}|W{W0}|lo|h{HOLDS[0]} "
          f"({r0.size:,} events)")
    audits["QTY"] = assert_QTY(panel, r0, c0)
    print(f"  [QTY] total-return {audits['QTY']['total_return_mean_bp']:+.3f} bp vs price-return "
          f"{audits['QTY']['price_return_mean_bp']:+.3f} bp -- the two grids differ")

    ctx = FN.NullContext(panel0)
    pos0 = positions_grid(r0, c0, n, T, PRIMARY_HOLD).astype(float)
    ctx.assert_matches_scorer(pos0, lambda p: RP.score(panel0, p, WARMUP, ppy=ppy, rf_annual=RF,
                                                       borrow_annual=BORROW),
                              start=WARMUP, rf_annual=RF, borrow_annual=BORROW, ppy=ppy)
    audits["fast_null_assert_matches_scorer"] = True
    print("  [FN] fast_null.light_score agrees EXACTLY with RP.score on the real book")

    cells, done = {}, 0
    for group, dirs in (("grid", DIRS), ("reversed", REVERSED_DIRS)):
        for f, tail_low, kind in dirs:
            tag = "lo" if tail_low else "hi"
            for W in WINDOWS:
                rows, cols = _ev(z, f, W, tag)
                for h in HOLDS:
                    c = cell_row(panel, panel0, rows, cols, h, C, cs_half, ppy,
                                 full=(h == PRIMARY_HOLD))
                    done += 1
                    if c:
                        c.update(feature=f, window=W, hold=h, tail=tag, group=group, kind=kind)
                        cells[f"{f}|{W}|{h}|{tag}"] = c
            print(f"    {group:<8} {f:<16} {kind:<14} {time.time() - t0:5.0f}s", flush=True)
            note_peak()

    lf, ltail = DIRS[0][0], DIRS[0][1]
    p = pct_trailing(np.load(SCORE_CACHE, allow_pickle=False)[lf], WINDOWS[0])
    assert_LAG(p, ltail, HOLDS[0], n, T)
    audits["LAG"] = True
    print(f"  [LAG] {lf}|W{WINDOWS[0]} re-derived bar by bar by a second implementation: agree")

    OBSERVED.write_text(json.dumps(dict(
        study=STUDY, split=sp, ppy=ppy, warmup=WARMUP, min_trailing_obs=MIN_TRAILING_OBS,
        windows=list(WINDOWS), holds=list(HOLDS), primary_hold=PRIMARY_HOLD, decile=DECILE,
        n_grid_cells=len(DIRS) * len(WINDOWS) * len(HOLDS),
        n_reversed_cells=len(REVERSED_DIRS) * len(WINDOWS) * len(HOLDS),
        declared=DECLARED, undeclared=list(UNDECLARED), audits=audits,
        cost=dict(ibkr_per_side_bp_median=float(np.median(panel.cost_fraction) * 1e4),
                  cs_half_spread_bp_all_bars_median=float(np.nanmedian(cs_half))),
        event_meta=json.loads(str(z["_meta"][0])), ts=json.loads(str(z["_ts"][0])),
        cells=cells), indent=1))
    print(f"  wrote {OBSERVED.relative_to(REPO)}  ({len(cells)} of {done} cells defined, "
          f"{time.time() - t0:.0f}s)")
    note_peak("observed done")
    return cells


# ==========================================================================
# s4 -- the two nulls, best-of-150 WITHIN EACH HOLD
# ==========================================================================
def stage_nulls(draws):
    ncell = len(DIRS) * len(WINDOWS)
    print(f"\nNULLS -- {draws} draws x 2 families; the floor is BEST-OF-{ncell} WITHIN EACH HOLD, "
          f"under ONE SHARED DRAW per iteration (s4)")
    t0 = time.time()
    panel, _g, sp = load_mined()
    n, T = panel.shape
    ppy = panel.ppy
    C = trade_cumsum(panel)
    z = np.load(EVENT_CACHE, allow_pickle=False)

    cellkeys = [(f, W, tail_low) for f, tail_low, _k in DIRS for W in WINDOWS]
    # int32 throughout: 150 cells x ~200k events x 2 indices is 480 MB at int64 and 240 at int32,
    # and the whole stage has to fit beside the eligibility masks.
    ev = {(f, W, tl): tuple(a.astype(np.int32) for a in _ev(z, f, W, "lo" if tl else "hi"))
          for f, W, tl in cellkeys}
    elig = {(f, W): _elig(z, f, W, T) for f in FEATURES for W in WINDOWS}
    n_ev = {k: np.bincount(v[0], minlength=n) for k, v in ev.items()}
    print(f"  {len(cellkeys)} feature-direction x window cells per hold; events and eligibility "
          f"masks loaded ({time.time() - t0:.0f}s)")
    note_peak("null inputs")

    # THE NULL MUST LIVE IN THE TRADEABLE UNIVERSE. D347's rotation traded the sub-$5 tail and
    # its headline inverted when that was fixed (D351). Checked, not assumed, on both sides.
    for (f, W, _tl), (r, c) in ev.items():
        if not elig[(f, W)][r, c].all():
            raise AssertionError(f"[NULL] {f}|{W}: an OBSERVED event sits off its own eligibility mask")
    print("  [NULL] every observed event satisfies its own eligibility mask")

    # PER-CELL null draws as well as the pre-registered best-of-150 floor. 600 cells x `draws` x 2
    # families x 2 statistics is under 4 MB, and it is the only way to say whether the floor is
    # DECISIVE or is being set by the variance of one thin cell (R7's "the distribution, not the
    # percentile alone"). The headline stays the pre-registered floor.
    def one_hold(_key, h):
        """One hold, end to end. Everything it reads -- `ev`, `elig`, `n_ev`, `C` -- is
        READ-ONLY, which is what makes the threaded fan-out safe without a lock. Each hold gets
        its own RNG stream keyed on the hold, so the draws are independent across holds and
        SHARED across the 150 cells within one, which is what s4 asks for."""
        runs = {}
        for k, (r, c) in ev.items():
            rr, aa, LL = circ_runs_of(positions_grid(r, c, n, T, h))
            runs[k] = (rr.astype(np.int32), aa.astype(np.int32), LL.astype(np.int32))
        rng = np.random.default_rng([SEED, STUDY, h])
        Pr = np.full((len(cellkeys), draws, 2), np.nan)
        Pe = np.full((len(cellkeys), draws, 2), np.nan)
        fl_r, fl_e, ra_r, ra_e = [], [], [], []
        checked = False
        th = time.time()
        for d in range(draws):
            off = rng.integers(0, T, size=n)          # ONE offset vector, shared by every cell
            m = r_ = -np.inf
            for j, k in enumerate(cellkeys):
                rr, aa, LL = runs[k]
                tr, ln, _, _ = trades_of_runs(rr, aa, LL, C, T, off)
                if tr.size >= 30:
                    a_, b_ = float(tr.mean()), float(tr.sum() / ln.sum())
                    Pr[j, d] = (a_, b_)
                    m, r_ = max(m, a_), max(r_, b_)
            fl_r.append(m)
            ra_r.append(r_)

            perm = np.array([rng.permutation(T) for _ in range(n)])   # ONE permutation set, shared
            m = r_ = -np.inf
            for j, k in enumerate(cellkeys):
                f, W, _tl = k
                msk, cnt = elig[(f, W)], n_ev[k]
                rr, cc = [], []
                for i in range(n):
                    if cnt[i] == 0:
                        continue
                    pi = perm[i]
                    sel = pi[msk[i, pi]][:cnt[i]]    # matched count, drawn from THIS cell's own mask
                    rr.append(np.full(sel.size, i, np.int64))
                    cc.append(sel)
                a = np.concatenate(rr) if rr else np.zeros(0, np.int64)
                b = np.concatenate(cc) if cc else np.zeros(0, np.int64)
                if not checked:
                    if not msk[a, b].all():
                        raise AssertionError(f"[NULL] {f}|{W}: a drawn entry is off the eligibility mask")
                    if not np.array_equal(np.bincount(a, minlength=n),
                                          np.minimum(cnt, msk.sum(axis=1))):
                        raise AssertionError(f"[NULL] {f}|{W}: the entry count is not matched per name")
                r2, a2, L2 = runs_from_events(a, b, n, T, h)
                tr, ln, _, _ = trades_of_runs(r2, a2, L2, C, T)
                if tr.size >= 30:
                    a_, b_ = float(tr.mean()), float(tr.sum() / ln.sum())
                    Pe[j, d] = (a_, b_)
                    m, r_ = max(m, a_), max(r_, b_)
            checked = True
            fl_e.append(m)
            ra_e.append(r_)
            if (d + 1) % 20 == 0 or d + 1 == draws:
                el = time.time() - th
                print(f"    hold {h:>2}  {d + 1}/{draws}  {el:5.0f}s  {el / (d + 1):.2f} s/draw  "
                      f"eta {(draws - d - 1) * el / (d + 1) / 60:.0f} min  "
                      f"[MEM] {rss_gb():.2f} GB", flush=True)
        del runs
        return dict(rotation=(fl_r, ra_r, Pr), entry=(fl_e, ra_e, Pe))

    got = FN.parallel_map(one_hold, [(h, h) for h in HOLDS], workers=len(HOLDS))
    note_peak("nulls computed")
    floors, rates, per = {}, {}, {}
    for h in HOLDS:
        for fam in ("rotation", "entry"):
            fl, ra, P = got[h][fam]
            floors[f"{fam}|{h}"], rates[f"{fam}|{h}"], per[f"{fam}|{h}"] = fl, ra, P

    def summ(v):
        v = np.asarray(v, float)
        v = v[np.isfinite(v)]
        if v.size == 0:
            return None
        return dict(n=int(v.size), p50=float(np.percentile(v, 50)),
                    p95=float(np.percentile(v, 95)), max=float(v.max()), min=float(v.min()),
                    mean=float(v.mean()), sd=float(v.std(ddof=1)) if v.size > 1 else float("nan"))

    percell = {}
    for fam in ("rotation", "entry"):
        for h in HOLDS:
            P = per[f"{fam}|{h}"]
            for j, (f, W, tl) in enumerate(cellkeys):
                key = f"{fam}|{f}|{W}|{h}|{'lo' if tl else 'hi'}"
                percell[key] = dict(mean_bp=summ(P[j, :, 0]), bp_per_bar=summ(P[j, :, 1]))

    out = dict(study=STUDY, draws=draws, split=sp, ppy=ppy, cells_per_hold=len(cellkeys),
               mean_bp_floors={k: summ(v) for k, v in floors.items() if v},
               bp_per_bar_floors={k: summ(v) for k, v in rates.items() if v},
               per_cell=percell,
               note=(f"best-of-{ncell} WITHIN EACH HOLD (25 feature-directions x 6 windows), under "
                     "one shared offset vector and one shared permutation set per draw. NEVER "
                     "across holds: a 78-bar hold earns ~20x a 4-bar hold per trade by "
                     "construction, so a cross-hold max is set entirely by the longest (D382's "
                     "own correction). `per_cell` carries each cell's OWN null distribution "
                     "beside the pre-registered floor -- reported, never substituted for it."))
    NULLS.write_text(json.dumps(out, indent=1))
    print(f"  wrote {NULLS.relative_to(REPO)} ({time.time() - t0:.0f}s)")
    for k in sorted(out["mean_bp_floors"]):
        v, w = out["mean_bp_floors"][k], out["bp_per_bar_floors"][k]
        print(f"    {k:<14} mean/trade p50 {v['p50']:+9.2f} p95 {v['p95']:+9.2f} max {v['max']:+9.2f}"
              f"  |  bp/bar p50 {w['p50']:+7.3f} p95 {w['p95']:+7.3f}")
    note_peak("nulls done")
    return out


# ==========================================================================
# the report
# ==========================================================================
def _shape_of(vals):
    """s5.4 / R14's 2026-09-08 addition: read the SHAPE across the swept window as evidence.

    MONOTONE IS TESTED FIRST, and that ordering is the point. A profile falling smoothly from
    +31.55 to +24.20 has a large max-minus-median relative to its own MAD, so a knife-edge test
    applied first calls it a knife-edge -- which is exactly backwards. A monotone progression is
    the most informative shape here, not the most suspicious one."""
    got = [v for v in vals if v is not None]
    if len(got) < 3:
        return "incomplete"
    a = np.array(got)
    d = np.diff(a)
    if np.all(d >= 0):
        return "monotone rising in W"
    if np.all(d <= 0):
        return "monotone falling in W"
    med = float(np.median(a))
    mad = float(np.median(np.abs(a - med)))
    if a.max() - med > 3.0 * (mad + 1e-12):
        return "knife-edge (UNRESOLVED, s5.4)"
    if int(np.argmax(a)) in (0, len(a) - 1):
        return "edge peak (UNRESOLVED, gate 1i)"
    return "interior hump"


def stage_report():
    obs = json.loads(OBSERVED.read_text())
    nul = json.loads(NULLS.read_text())
    cells = obs["cells"]
    grid = {k: v for k, v in cells.items() if v["group"] == "grid"}
    rev = {k: v for k, v in cells.items() if v["group"] == "reversed"}

    pc = nul.get("per_cell", {})
    for key, c in grid.items():
        h, f, W, tag = c["hold"], c["feature"], c["window"], c["tail"]
        fm = nul["mean_bp_floors"][f"rotation|{h}"], nul["mean_bp_floors"][f"entry|{h}"]
        fr = nul["bp_per_bar_floors"][f"rotation|{h}"], nul["bp_per_bar_floors"][f"entry|{h}"]
        c["clears_mean_rotation"] = c["mean_bp"] > fm[0]["p95"]
        c["clears_mean_entry"] = c["mean_bp"] > fm[1]["p95"]
        c["clears_rate_rotation"] = c["bp_per_bar"] > fr[0]["p95"]
        c["clears_rate_entry"] = c["bp_per_bar"] > fr[1]["p95"]
        c["clears_both_mean"] = c["clears_mean_rotation"] and c["clears_mean_entry"]
        c["clears_both_rate"] = c["clears_rate_rotation"] and c["clears_rate_entry"]
        # REPORTED BESIDE THE FLOOR, NEVER INSTEAD OF IT: the cell against its OWN null, which is
        # the un-multiplicity-corrected comparison and the one that says where the effect is.
        own = {}
        for fam in ("rotation", "entry"):
            s = pc.get(f"{fam}|{f}|{W}|{h}|{tag}")
            if s and s.get("mean_bp"):
                a, b = s["mean_bp"], s["bp_per_bar"]
                own[fam] = dict(
                    mean_p50=a["p50"], mean_p95=a["p95"],
                    mean_z=((c["mean_bp"] - a["mean"]) / a["sd"]) if a.get("sd") else None,
                    rate_p50=b["p50"], rate_p95=b["p95"],
                    beats_own_mean_p95=c["mean_bp"] > a["p95"],
                    beats_own_rate_p95=c["bp_per_bar"] > b["p95"])
        c["own_null"] = own

    n_mean = sum(1 for c in grid.values() if c["clears_both_mean"])
    n_rate = sum(1 for c in grid.values() if c["clears_both_rate"])
    n_pos = sum(1 for c in grid.values() if c["mean_bp"] > 0)
    n_rot = sum(1 for c in grid.values() if c["clears_mean_rotation"])
    n_ent = sum(1 for c in grid.values() if c["clears_mean_entry"])
    n_own = sum(1 for c in grid.values()
                if all(v.get("beats_own_mean_p95") for v in c["own_null"].values())
                and len(c["own_null"]) == 2)
    n_own_rate = sum(1 for c in grid.values()
                     if all(v.get("beats_own_rate_p95") for v in c["own_null"].values())
                     and len(c["own_null"]) == 2)

    shapes = {}
    for f, tail_low, _kind in DIRS:
        tag = "lo" if tail_low else "hi"
        for h in HOLDS:
            v = [grid.get(f"{f}|{W}|{h}|{tag}", {}).get("mean_bp") for W in WINDOWS]
            r = [grid.get(f"{f}|{W}|{h}|{tag}", {}).get("bp_per_bar") for W in WINDOWS]
            shapes[f"{f}|{tag}|{h}"] = dict(mean_bp=v, bp_per_bar=r, shape=_shape_of(v))

    # [DIR] / Q5 -- both directions reported, and the LEDGER COUNTS BOTH (gate 1h)
    inverted = []
    for f in sorted(DECLARED):
        tag = "lo" if DECLARED[f] == "LOW" else "hi"
        rtag = "hi" if tag == "lo" else "lo"
        bd = max((grid[f"{f}|{W}|{h}|{tag}"]["mean_bp"] for W in WINDOWS for h in HOLDS
                  if f"{f}|{W}|{h}|{tag}" in grid), default=float("nan"))
        br = max((rev[f"{f}|{W}|{h}|{rtag}"]["mean_bp"] for W in WINDOWS for h in HOLDS
                  if f"{f}|{W}|{h}|{rtag}" in rev), default=float("nan"))
        pd_ = grid.get(f"{f}|{WINDOWS[0]}|{PRIMARY_HOLD}|{tag}", {}).get("mean_bp")
        inverted.append(dict(feature=f, declared_long_end=DECLARED[f],
                             best_declared_mean_bp=bd, best_reversed_mean_bp=br,
                             primary_hold_W26_mean_bp=pd_,
                             DIRECTION_INVERTED=bool(br > bd)))
    und = []
    for f in UNDECLARED:
        bl = max((grid[f"{f}|{W}|{h}|lo"]["mean_bp"] for W in WINDOWS for h in HOLDS
                  if f"{f}|{W}|{h}|lo" in grid), default=float("nan"))
        bh_ = max((grid[f"{f}|{W}|{h}|hi"]["mean_bp"] for W in WINDOWS for h in HOLDS
                   if f"{f}|{W}|{h}|hi" in grid), default=float("nan"))
        und.append(dict(feature=f, best_low_tail_mean_bp=bl, best_high_tail_mean_bp=bh_,
                        better_tail="hi" if bh_ > bl else "lo"))

    ranked = sorted(grid.values(), key=lambda c: -c["mean_bp"])
    best_by_hold = {}
    for h in HOLDS:
        cs = [c for c in grid.values() if c["hold"] == h]
        if cs:
            b = max(cs, key=lambda c: c["mean_bp"])
            br = max(cs, key=lambda c: c["bp_per_bar"])
            best_by_hold[str(h)] = dict(
                by_mean=dict(cell=f"{b['feature']}|{b['window']}|{b['hold']}|{b['tail']}",
                             **{k: b[k] for k in ("mean_bp", "median_bp", "bp_per_bar", "trades",
                                                  "events", "entries_per_year", "exposure",
                                                  "excess_over_bh_cagr", "clears_both_mean")}),
                by_rate=dict(cell=f"{br['feature']}|{br['window']}|{br['hold']}|{br['tail']}",
                             bp_per_bar=br["bp_per_bar"], mean_bp=br["mean_bp"],
                             clears_both_rate=br["clears_both_rate"]))

    keys = ("mean_bp", "median_bp", "bp_per_bar", "net_mean_bp", "trades", "events",
            "entries_per_year", "median_run_bars", "median_run_minutes", "turnover_per_bar",
            "exposure", "gross_cagr", "net_cagr", "bh_matched_cagr", "excess_over_bh_cagr",
            "held_half_spread_bp", "ibkr_half_cost_bp", "breakeven_bp_per_side",
            "clears_both_mean", "clears_both_rate")
    rep = dict(
        study=STUDY, kind="STAGE-1 SCREEN (R14), signal hunt under R15. Admits nothing.",
        preregistration="docs/decisions/D383-the-time-series-structure-screen-at-15-minutes.md",
        split=obs["split"], ppy=obs["ppy"], warmup=obs["warmup"], draws=nul["draws"],
        grid=dict(feature_directions=len(DIRS), windows=list(WINDOWS), holds=list(HOLDS),
                  cells=len(DIRS) * len(WINDOWS) * len(HOLDS), defined=len(grid),
                  reversed_cells_reported_separately=len(rev)),
        headline=dict(cells_clearing_BOTH_floors_on_mean_per_trade=n_mean,
                      cells_clearing_BOTH_floors_on_bp_per_bar=n_rate,
                      cells_clearing_rotation_only_on_mean=n_rot,
                      cells_clearing_entry_only_on_mean=n_ent,
                      cells_beating_their_OWN_null_p95_on_mean=n_own,
                      cells_beating_their_OWN_null_p95_on_bp_per_bar=n_own_rate,
                      cells_with_positive_gross_mean=n_pos, cells_defined=len(grid)),
        floors=dict(mean_bp=nul["mean_bp_floors"], bp_per_bar=nul["bp_per_bar_floors"]),
        best_by_hold=best_by_hold,
        top20=[dict(cell=f"{c['feature']}|{c['window']}|{c['hold']}|{c['tail']}",
                    **{k: c[k] for k in keys}) for c in ranked[:20]],
        bottom5=[dict(cell=f"{c['feature']}|{c['window']}|{c['hold']}|{c['tail']}",
                      mean_bp=c["mean_bp"], bp_per_bar=c["bp_per_bar"]) for c in ranked[-5:]],
        shapes=shapes, direction_audit=inverted, undeclared_tails=und,
        cost=obs["cost"], audits=obs["audits"], ts=obs["ts"], cells=cells)
    REPORT.write_text(json.dumps(rep, indent=1))
    print(f"\nwrote {REPORT.relative_to(REPO)}")

    print(f"\n  HEADLINE  {n_mean} of {len(grid)} defined cells clear BOTH pre-registered "
          f"best-of-150 floors on gross mean per trade; {n_rate} clear both on bp/bar.")
    print(f"            {n_pos} have a positive gross mean. Against each cell's OWN null "
          f"(no multiplicity correction): {n_own} on mean, {n_own_rate} on bp/bar.")
    for h in HOLDS:
        v = nul["mean_bp_floors"][f"rotation|{h}"], nul["mean_bp_floors"][f"entry|{h}"]
        b = best_by_hold.get(str(h), {}).get("by_mean", {})
        print(f"    hold {h:>2}: best {b.get('cell','-'):<28} {b.get('mean_bp', float('nan')):+9.2f} bp"
              f"   rotation p50/p95 {v[0]['p50']:+8.2f}/{v[0]['p95']:+8.2f}"
              f"   entry p50/p95 {v[1]['p50']:+8.2f}/{v[1]['p95']:+8.2f}")
    return rep


# ==========================================================================
# [X] -- every audit RAISES on a deliberately broken input
# ==========================================================================
def stage_selftest():
    global WARMUP
    print("\nSELFTEST -- [X], and each break hits the SCALAR that assertion actually reads")
    raised = []

    def must_raise(label, fn):
        try:
            fn()
        except (AssertionError, ValueError, FileNotFoundError) as e:
            raised.append((label, type(e).__name__))
            print(f"    RAISED   {label}")
            return
        raise AssertionError(f"[X] {label} did not raise -- a self-test that cannot fail is "
                             "worse than none")

    # ---------------------------------------------------------------- [SPLIT]
    must_raise("[SPLIT] a cut that removed nothing",
               lambda: assert_SPLIT(["2019-01-02 09:30:00"], 0, 1))
    must_raise("[SPLIT] a RESERVED bar left in the panel",
               lambda: assert_SPLIT(["2019-01-02 09:30:00", "2024-01-02 09:30:00"], 5, 7))
    must_raise("[SPLIT] the bar arithmetic does not close",
               lambda: assert_SPLIT(["2019-01-02 09:30:00"], 5, 99))
    assert assert_SPLIT(["2019-01-02 09:30:00", "2023-12-29 15:45:00"], 3, 5)["mining_bars"] == 2

    # ---------------------------------------------------------------- [GATE]
    must_raise("[GATE] a file with no meta beside it", lambda: RP.assert_gates_passed(EVENTS_JSON))
    RP.assert_gates_passed(FIXTURE)
    print("    ACCEPTS  [GATE] the real fixture, [SPLIT] a correctly cut bar list")

    # ---------------------------------------------------------------- [TS], on a TIE-HEAVY input
    n, T = 8, 4000
    keep_warm = WARMUP
    WARMUP = 800
    try:
        rng = np.random.default_rng(0)
        x = rng.standard_normal((n, T))
        x[0] = rng.integers(-1, 2, T).astype(float)     # struct_trend's own three-valued shape
        x[1] = np.where(rng.random(T) < 0.4, 0.0, x[1])
        x[rng.random((n, T)) < 0.03] = np.nan
        W = 130
        good = pct_trailing(x, W)
        r = assert_TS(x, W, good, n_probe=300)
        print(f"    ACCEPTS  [TS] the honest percentile: {r['probes']} literal-slice probes, "
              f"{r['extreme_probes']} extreme probes")
        must_raise("[TS] a percentile that PEEKS at bar t",
                   lambda: assert_TS(x, W, pct_peeking(x, W), n_probe=300))

        # ------------------------------------------------------------ [POS] / [LAG]
        C = np.cumsum(rng.standard_normal((n, T)) * 1e-3, axis=1)
        rows, cols = np.nonzero(events_of(good, True))
        off = rng.integers(0, T, size=n)
        assert_POS(rows, cols, n, T, 13, C, off)
        print(f"    ACCEPTS  [POS] loop == grid == run kernel on {rows.size:,} tie-heavy events, "
              "rotated and not")

        def broken_runs():
            """The run kernel entered ONE BAR EARLY -- the exact scalar `assert_POS` compares."""
            r_, a_, L_ = runs_from_events(rows, cols, n, T, 13)
            a_ = np.maximum(a_ - 1, 0)
            g_tr, _ = trades_grid(positions_grid(rows, cols, n, T, 13), C)
            k_tr, _, _, _ = trades_of_runs(r_, a_, L_, C, T)
            if not np.array_equal(g_tr, k_tr):
                raise AssertionError("[POS] the run kernel disagrees with the grid kernel")
        must_raise("[POS] a run kernel entered one bar early", broken_runs)

        def broken_rot():
            """A rotation that FORGETS the wrap split -- the null's own kernel, broken."""
            b = positions_grid(rows, cols, n, T, 13)
            cr, ca, cL = circ_runs_of(b)
            s = (ca + off[cr]) % T
            e = np.minimum(s + cL, T)                   # clipped instead of wrapped
            o = np.lexsort((s, cr))
            lo = np.where(s[o] > 0, C[cr[o], np.maximum(s[o] - 1, 0)], 0.0)
            k_tr = np.expm1(C[cr[o], e[o] - 1] - lo) * 1e4
            g_tr, _ = trades_grid(roll_rows(b, off), C)
            if not np.array_equal(g_tr, k_tr):
                raise AssertionError("[POS] the run kernel disagrees with the grid kernel (rotated)")
        must_raise("[POS] a rotation that clips instead of wrapping", broken_rot)

        assert_LAG(good, True, 13, n, T, span=1500)
        print("    ACCEPTS  [LAG] the second implementation agrees on the synthetic book")

        def broken_lag():
            """A book entered on bar t itself -- the array `assert_LAG` compares."""
            peek = positions_grid(rows, cols - 1, n, T, 13)
            ref = positions_grid(rows, cols, n, T, 13)
            if not np.array_equal(peek, ref):
                raise AssertionError("[LAG] the second implementation disagrees")
        must_raise("[LAG] a book entered one bar early", broken_lag)
    finally:
        WARMUP = keep_warm

    # ---------------------------------------------------------------- on the real panel
    if PANEL_CACHE.exists():
        panel, _g, sp = load_mined()
        p0 = panel.zero_cost()
        ppy = panel.ppy
        print(f"    ACCEPTS  [SPLIT] cached panel: {sp['mining_bars']:,} mining bars "
              f"{sp['first']} -> {sp['last']}; {sp['reserved_bars_cut']:,} reserved bars cut")
        bh = assert_BH(p0, WARMUP, ppy)
        print(f"    ACCEPTS  [BH] {bh['cagr']:+.2%} CAGR at exposure {bh['exposure_gross']:.3f}, "
              f"ppy {ppy:,.0f}")
        must_raise("[BH] a panel with zero exposure", lambda: assert_BH(_Dead(p0), WARMUP, ppy))
        s = assert_SIGN(p0, ppy)
        print(f"    ACCEPTS  [SIGN] long {s['best_bar_long']:+.6f} / short {s['best_bar_short']:+.6f}")

        def sign_blind(p):
            """A scorer that cannot tell a long from a short -- [SIGN]'s own scalar, broken."""
            return RP.score(p0, np.abs(p), WARMUP, ppy=ppy, rf_annual=0.0, borrow_annual=0.0)
        must_raise("[SIGN] a sign-blind scorer", lambda: assert_SIGN(p0, ppy, scorer=sign_blind))

        rows = np.zeros(200, np.int64)
        cols = np.arange(WARMUP + 10, WARMUP + 10 + 200 * 40, 40, dtype=np.int64)
        assert_QTY(panel, rows, cols)
        print("    ACCEPTS  [QTY] the total-return and price-return grids differ")
        must_raise("[QTY] a panel whose dividend leg is not compounded",
                   lambda: assert_QTY(_NoDiv(panel), rows, cols))
    else:
        print("    (panel cache absent -- [BH]/[SIGN]/[QTY] run after --prep)")

    print(f"\n  [X] {len(raised)} guards RAISE on the input each one exists to catch, and every "
          "one accepts a sound input")
    return True


class _Dead(MinedPanel):
    """A panel whose names are never live -- [BH] must refuse it rather than divide by nothing."""

    def __init__(self, p):
        super().__init__(p.symbols, p.stamps, p.closes, p.log_returns,
                         p.total_log_returns, p.cost_fraction)
        self.live = np.zeros_like(self.live)


class _NoDiv(MinedPanel):
    """A panel whose dividend leg was never compounded -- [QTY] must refuse it."""

    def __init__(self, p):
        super().__init__(p.symbols, p.stamps, p.closes, p.log_returns,
                         p.log_returns, p.cost_fraction)


# ==========================================================================
def main() -> int:
    ap = argparse.ArgumentParser()
    for f in ("selftest", "prep", "features", "events", "observed", "nulls", "report", "all"):
        ap.add_argument(f"--{f}", action="store_true")
    ap.add_argument("--worker", nargs=3, default=None)
    ap.add_argument("--draws", type=int, default=200)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if a.worker:
        _worker_main(a.worker)
        return 0
    print(f"D383  the TIME-SERIES market-structure screen at 15 minutes  "
          f"({len(DIRS)} feature-directions x {len(WINDOWS)} windows x {len(HOLDS)} holds = "
          f"{len(DIRS) * len(WINDOWS) * len(HOLDS)} cells)")
    ran = False
    for flag, fn in (("selftest", stage_selftest), ("prep", lambda: stage_prep(a.force)),
                     ("features", lambda: stage_features(a.workers, a.force)),
                     ("events", lambda: stage_events(a.force)), ("observed", stage_observed),
                     ("nulls", lambda: stage_nulls(a.draws)), ("report", stage_report)):
        if getattr(a, flag) or a.all:
            fn()
            ran = True
    if not ran:
        ap.error("one of --selftest --prep --features --events --observed --nulls --report --all")
    print(f"\n[MEM] peak working set this process: {_PEAK[0]:.2f} GB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
