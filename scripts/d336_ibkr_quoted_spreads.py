"""D336 -- quoted-spread validation of the estimator convention (PB vs PUB vs AR).

    uv run python scripts/d336_ibkr_quoted_spreads.py --plan
    uv run python scripts/d336_ibkr_quoted_spreads.py --pull --host 127.0.0.1 --port 7497 --client-id 336
    uv run python scripts/d336_ibkr_quoted_spreads.py --compare
    uv run python scripts/d336_ibkr_quoted_spreads.py --selftest

Pre-registration: docs/decisions/D336-quoted-spread-validation.md. The selection
rule is D332 Part C's and is not re-derived here.

--plan      stratified sample (5 price x 5 dollar-volume quintiles, 4 per cell,
            default_rng(336)) of live, split-free names with 252 finite closes in
            the fixture's last 252 bars -> data/d336_sample.json. No network.
--pull      the principal's IBKR session: reqContractDetails, then one daily
            BID_ASK reqHistoricalData per name behind a 30-per-600-s token bucket
            (BID_ASK counts double against IBKR's 60/10 min). Raw bars cached
            to data/raw/ibkr/<sym>.csv (git-ignored) with _meta.json. Resumable.
            Errors 162 / 10167 / 354 are logged per name and never filled; ten
            consecutive subscription failures abort. Bar semantics gate: IBKR
            daily BID_ASK bars carry open = time-avg bid, close = time-avg ask,
            so close >= open on >= 99% of a name's bars or the pull stops.
            THIS PATH NEVER WRITES A BAR THE CLIENT DID NOT RETURN.
--compare   per name, quoted half = (close - open) / 2 / mid, median over days;
            fixture OHLC on exactly the quoted dates (inner join, no look-ahead)
            -> PB, PUB, AR; errors in log spread; MALE; 5x5 strata; one
            select_winner() call -> data/d336_comparison.json.
--selftest  plan on the real fixture, Abdi-Ranaldo on synthetic data, the token
            bucket on a fake clock, a mocked IB client through the pull path
            into a temp dir and --compare on that cache, and every assertion
            raising on a deliberately broken input.

`ib_async` is imported lazily inside the pull only; every other mode runs without
a broker library.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import tempfile
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "data" / "fixtures" / "us_shorts_daily_raw.csv.gz"
META = REPO / "data" / "fixtures" / "us_shorts_daily_raw.meta.json"
SAMPLE_OUT = REPO / "data" / "d336_sample.json"
RAW_DIR = REPO / "data" / "raw" / "ibkr"
COMPARE_OUT = REPO / "data" / "d336_comparison.json"

WINDOW_END = "2026-08-26"
END_DATETIME = "20260826 23:59:59 US/Eastern"
DURATION = "1 Y"
BAR_SIZE = "1 day"
WHAT_TO_SHOW = "BID_ASK"
USE_RTH = True
FORMAT_DATE = 1

WINDOW_BARS = 252
DV_BARS = 63
N_Q = 5
PER_CELL = 4
SEED = 336

MIN_QUOTED_DAYS = 200           # [N]
FLOOR = 1e-4                    # 1 bp proportional: the log floor for clamped zeros
G_TOL = 0.05                    # [G] |ln(IB mid / fixture close)| on the last common date
SEMANTICS_FRAC = 0.99           # bar-semantics gate: close >= open on this share of bars
BUCKET_CAPACITY = 30
BUCKET_SECONDS = 600.0
MAX_CONSECUTIVE_MISSING = 10
SUBSCRIPTION_CODES = {354, 10167}
LOGGED_CODES = {162, 10167, 354}

RULE = "lowest median absolute error in log spread"   # D332 Part C, verbatim
ESTIMATORS = ("PB", "PUB", "AR")
EXCH_MAP = {"NYSE": "NYSE", "NASDAQ": "NASDAQ", "AMEX": "AMEX",
            "NYSE MKT": "AMEX", "BATS": "BATS"}

LN2 = math.log(2.0)
LN15 = math.log(1.5)


def _log(*a):
    print(*a, flush=True)


def _jsonable(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, float) and not math.isfinite(o):
        return None
    raise TypeError(f"not jsonable: {type(o)}")


def _dump(obj, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, default=_jsonable))


# --------------------------------------------------------------------------
# the programme's own estimators, loaded from the files that define them
# --------------------------------------------------------------------------

_MODS: dict = {}


def _load_script(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def estimators():
    """corwin_schultz (D285, unchanged) and _trail / CS_BARS (ragged_vol_scores)."""
    if not _MODS:
        d285 = _load_script("d336_d285_spread_estimate", "d285_spread_estimate.py")
        rvs = _load_script("d336_ragged_vol_scores", "ragged_vol_scores.py")
        _MODS.update(cs=d285.corwin_schultz, trail=rvs._trail, CS_BARS=int(rvs.CS_BARS))
    return _MODS


def abdi_ranaldo_half(H, L, C):
    """Abdi-Ranaldo (2017) half-spread, once per name.

    c_t = ln C_t, eta_t = (ln H_t + ln L_t)/2,
    S^2 = 4 * mean_t[(c_t - eta_t)(c_t - eta_{t+1})], S = sqrt(max(S^2, 0)), half = S/2.
    """
    H, L, C = (np.asarray(x, float) for x in (H, L, C))
    with np.errstate(invalid="ignore", divide="ignore"):
        c = np.log(C)
        eta = (np.log(H) + np.log(L)) / 2.0
        x = (c[:-1] - eta[:-1]) * (c[:-1] - eta[1:])
    if not np.isfinite(x).any():
        return float("nan")
    s2 = 4.0 * float(np.nanmean(x))
    s = math.sqrt(max(s2, 0.0))
    return s / 2.0


def ohlc_estimates(H, L, C):
    """PB, PUB, AR (all proportional HALF spreads) on one name's rows, in order."""
    est = estimators()
    H2, L2 = np.asarray(H, float)[None, :], np.asarray(L, float)[None, :]
    live = np.ones(H2.shape, dtype=bool)
    cs = est["cs"](H2, L2, live)[0]              # round trip, clamped >= 0, pair (t-1, t) at t-1
    fin = np.isfinite(cs)
    pb = float(np.nanmedian(cs)) / 2.0 if fin.any() else float("nan")
    # ragged_vol_scores.py:144-147 -- the newest pair this may read ends at bar
    # t and is stored at t-1; shifting by one own bar is the causality argument.
    lagged = np.concatenate([[np.nan], cs[:-1]])
    trail = est["trail"](lagged, est["CS_BARS"], lambda w: np.nanmean(w, axis=1))
    pub = float(np.nanmedian(trail)) / 2.0 if np.isfinite(trail).any() else float("nan")
    zero_rate = float(np.mean(cs[fin] == 0.0)) if fin.any() else float("nan")
    return {"PB": pb, "PUB": pub, "AR": abdi_ranaldo_half(H, L, C),
            "zero_rate": zero_rate, "n_cs": int(fin.sum()),
            "n_trail": int(np.isfinite(trail).sum())}


def quoted_half(open_, close):
    """Per-day quoted half-spread from an IBKR daily BID_ASK bar.

    open = time-average bid, close = time-average ask. Returns (ok, half) where
    ok marks the days with close >= open > 0 that the per-name median uses.
    """
    o, c = np.asarray(open_, float), np.asarray(close, float)
    ok = np.isfinite(o) & np.isfinite(c) & (c >= o) & (o > 0)
    with np.errstate(invalid="ignore", divide="ignore"):
        half = (c - o) / 2.0 / ((o + c) / 2.0)
    return ok, half


def floor_and_log(est):
    """ln(est) with est floored at 1 bp; returns (log, n_floored, floored_mask)."""
    est = np.asarray(est, float)
    mask = est < FLOOR
    return np.log(np.maximum(est, FLOOR)), int(mask.sum()), mask


def select_winner(errs):
    """D332 Part C: lowest median absolute error in log spread. Called ONCE."""
    select_winner.calls += 1
    male = {k: float(np.median(np.abs(np.asarray(v, float)))) for k, v in errs.items()}
    winner = min(male, key=male.get)
    return winner, male


select_winner.calls = 0


# --------------------------------------------------------------------------
# assertions (record section 5)
# --------------------------------------------------------------------------

def assert_W(sym, quoted_dates, joined_dates, window_end=WINDOW_END):
    q = np.asarray(quoted_dates, dtype=str)
    j = np.asarray(joined_dates, dtype=str)
    if len(j) != len(q):
        raise AssertionError(f"[W] {sym}: join length {len(j)} != quoted days {len(q)} "
                             f"(a quoted date is missing from the fixture)")
    if not np.array_equal(q, j):
        raise AssertionError(f"[W] {sym}: joined dates are not the quoted dates")
    if len(j) > 1 and not np.all(j[1:] > j[:-1]):
        raise AssertionError(f"[W] {sym}: dates not strictly increasing")
    if len(j) and j[-1] > window_end:
        raise AssertionError(f"[W] {sym}: last date {j[-1]} > {window_end} (look-ahead)")


def assert_U(sym, quoted, est):
    if not (np.isfinite(quoted) and quoted > 0):
        raise AssertionError(f"[U] {sym}: quoted half {quoted!r} not finite and > 0")
    for k in ESTIMATORS:
        v = est[k]
        if not (np.isfinite(v) and v >= 0):
            raise AssertionError(f"[U] {sym}: {k} = {v!r} not finite and >= 0")


def assert_N(sym, n, min_days=MIN_QUOTED_DAYS):
    if n < min_days:
        raise AssertionError(f"[N] {sym}: {n} quoted days < {min_days}")


def assert_G(sym, ib_mid, fixture_close, tol=G_TOL):
    if not (ib_mid > 0 and fixture_close > 0):
        raise AssertionError(f"[G] {sym}: non-positive price {ib_mid}, {fixture_close}")
    d = abs(math.log(ib_mid / fixture_close))
    if not d < tol:
        raise AssertionError(f"[G] {sym}: |ln(IB mid / fixture close)| = {d:.4f} >= {tol} "
                             f"(adjusted-vs-unadjusted or wrong contract)")


def assert_Z(est, log_est, n_floored):
    est = np.asarray(est, float)
    log_est = np.asarray(log_est, float)
    mask = est < FLOOR
    if int(mask.sum()) != n_floored:
        raise AssertionError(f"[Z] floored count {n_floored} != {int(mask.sum())} estimates below 1 bp")
    if not np.all(log_est[mask] == math.log(FLOOR)):
        raise AssertionError("[Z] a floored estimate was not logged at the 1 bp floor")
    if not np.all(np.isfinite(log_est)):
        raise AssertionError("[Z] a non-finite log estimate survived the floor")


def assert_K(n_calls, rule):
    if n_calls != 1:
        raise AssertionError(f"[K] select_winner called {n_calls} times, not once")
    if rule != RULE:
        raise AssertionError(f"[K] rule {rule!r} != {RULE!r}")


def assert_P(times, capacity=BUCKET_CAPACITY, per_seconds=BUCKET_SECONDS):
    """[P] no half-open window of `per_seconds` holds more than `capacity` acquires."""
    t = np.sort(np.asarray(times, float))
    if t.size > capacity:
        span = t[capacity:] - t[:-capacity]
        if np.min(span) < per_seconds:
            raise AssertionError(f"[P] {capacity + 1} acquires within {np.min(span):.1f} s < {per_seconds:.0f} s")
    for a in t:
        if int(np.sum((t >= a) & (t < a + per_seconds))) > capacity:
            raise AssertionError(f"[P] window starting {a:.1f} holds > {capacity} acquires")


def check_bar_semantics(sym, open_, close, frac=SEMANTICS_FRAC):
    o, c = np.asarray(open_, float), np.asarray(close, float)
    if o.size == 0:
        raise SystemExit(f"bar semantics unverified: {sym} returned no bars")
    share = float(np.mean(c >= o))
    if share < frac:
        raise SystemExit(f"bar semantics unverified: {sym} close >= open on "
                         f"{share:.1%} of {o.size} bars (< {frac:.0%}); "
                         f"open should be avg bid and close avg ask")
    return share


# --------------------------------------------------------------------------
# --plan
# --------------------------------------------------------------------------

def load_fixture(symbols=None):
    df = pd.read_csv(FIXTURE, dtype={"timestamp": str, "symbol": str})
    if symbols is not None:
        df = df[df["symbol"].isin(list(symbols))]
    df = df.copy()
    df["date"] = df["timestamp"].str.slice(0, 10)
    return df


def plan(fx, meta, rng_seed=SEED):
    syms = meta["symbols"]
    alive = [s for s, v in syms.items() if v.get("cohort") == "alive"]
    last = [s for s in alive if syms[s].get("last_bar") == WINDOW_END]
    nosplit = [s for s in last if int(syms[s].get("n_splits") or 0) == 0]

    dates = np.sort(fx["date"].unique())
    window = dates[-WINDOW_BARS:]
    dv_dates = window[-DV_BARS:]
    sub = fx[fx["symbol"].isin(nosplit) & fx["date"].isin(window)]
    if sub.duplicated(["symbol", "date"]).any():
        raise AssertionError("fixture has duplicate (symbol, date) rows in the window")
    close = sub.pivot(index="date", columns="symbol", values="close").reindex(window)
    vol = sub.pivot(index="date", columns="symbol", values="volume").reindex(window)
    n_fin = np.isfinite(close.to_numpy(dtype=float)).sum(axis=0)
    n_fin = pd.Series(n_fin, index=close.columns)
    eligible = sorted(n_fin.index[n_fin >= WINDOW_BARS])
    in_fixture = sorted(close.columns)

    price_med = close[eligible].median(axis=0)
    dv_mean = (close[eligible] * vol[eligible]).loc[dv_dates].mean(axis=0)
    price_q = pd.qcut(price_med, N_Q, labels=False).astype(int)
    dv_q = pd.qcut(dv_mean, N_Q, labels=False).astype(int)

    cells = {}
    for s in eligible:
        cells.setdefault((int(price_q[s]), int(dv_q[s])), []).append(s)
    for k in cells:
        cells[k] = sorted(cells[k])

    rng = np.random.default_rng(rng_seed)
    chosen = {}                      # symbol -> (native cell, drawn-from cell)
    short = []
    for pq in range(N_Q):
        for dq in range(N_Q):
            members = cells.get((pq, dq), [])
            k = min(PER_CELL, len(members))
            pick = list(rng.choice(members, size=k, replace=False)) if k else []
            for s in pick:
                chosen[str(s)] = ((pq, dq), (pq, dq))
            if k < PER_CELL:
                short.append(((pq, dq), PER_CELL - k))

    fills = []
    for (pq, dq), need in short:
        filled = []
        for dist in range(1, N_Q):
            for pq2 in (pq - dist, pq + dist):
                if need == 0 or not 0 <= pq2 < N_Q:
                    continue
                pool = [s for s in cells.get((pq2, dq), []) if s not in chosen]
                k = min(need, len(pool))
                if k == 0:
                    continue
                for s in rng.choice(pool, size=k, replace=False):
                    chosen[str(s)] = ((pq, dq), (pq2, dq))
                    filled.append({"symbol": str(s), "from_cell": [pq2, dq]})
                need -= k
        fills.append({"cell": [pq, dq], "n_native": len(cells.get((pq, dq), [])),
                      "filled": filled, "unfilled": need})

    rows = []
    for s, (cell, src) in chosen.items():
        ex = syms[s].get("exchange")
        if ex not in EXCH_MAP:
            raise AssertionError(f"{s}: exchange {ex!r} has no primaryExchange mapping")
        r = {"symbol": s, "exchange": ex, "primaryExchange": EXCH_MAP[ex],
             "price_q": cell[0], "dv_q": cell[1],
             "price_med": float(price_med[s]), "dv_mean": float(dv_mean[s])}
        if src != cell:
            r["filled_from_cell"] = [src[0], src[1]]
            r["native_price_q"] = int(price_q[s])
        rows.append(r)
    rows.sort(key=lambda r: (r["price_q"], r["dv_q"], r["symbol"]))

    sample = {
        "record": "D336",
        "written_before_any_quote_was_seen": True,
        "window_start": str(window[0]), "window_end": str(window[-1]),
        "window_bars": WINDOW_BARS, "dv_bars": DV_BARS, "dv_window_start": str(dv_dates[0]),
        "seed": rng_seed, "n_quintiles": N_Q, "per_cell": PER_CELL,
        "eligibility": {
            "n_meta_symbols": len(syms),
            "n_alive": len(alive),
            "n_alive_last_bar_2026_08_26": len(last),
            "n_alive_last_bar_no_splits": len(nosplit),
            "n_of_those_in_fixture_window": len(in_fixture),
            "n_eligible_252_finite_closes": len(eligible),
            "n_sampled": len(rows),
        },
        "price_quintile_edges": [float(x) for x in np.quantile(price_med.to_numpy(), np.linspace(0, 1, N_Q + 1))],
        "dv_quintile_edges": [float(x) for x in np.quantile(dv_mean.to_numpy(), np.linspace(0, 1, N_Q + 1))],
        "cell_counts": {f"{pq},{dq}": len(cells.get((pq, dq), [])) for pq in range(N_Q) for dq in range(N_Q)},
        "fills": fills,
        "rows": rows,
    }
    return sample


def _print_plan(sample):
    e = sample["eligibility"]
    _log(f"window {sample['window_start']} .. {sample['window_end']} ({sample['window_bars']} bars), "
         f"dollar-volume over the last {sample['dv_bars']} (from {sample['dv_window_start']})")
    for k, v in e.items():
        _log(f"  {k:36s} {v}")
    _log("  eligible names per cell (rows price_q 0..4 low->high, cols dv_q 0..4):")
    for pq in range(N_Q):
        _log("    " + " ".join(f"{sample['cell_counts'][f'{pq},{dq}']:4d}" for dq in range(N_Q)))
    if sample["fills"]:
        for f in sample["fills"]:
            _log(f"  FILL cell {f['cell']}: native {f['n_native']}, filled {f['filled']}, unfilled {f['unfilled']}")
    else:
        _log("  no cell short of 4: no fills")
    ex = pd.Series([r["primaryExchange"] for r in sample["rows"]]).value_counts().to_dict()
    _log(f"  primaryExchange: {ex}")


def cmd_plan():
    t0 = time.time()
    meta = json.loads(META.read_text())
    fx = load_fixture()
    sample = plan(fx, meta)
    _print_plan(sample)
    _dump(sample, SAMPLE_OUT)
    _log(f"wrote {SAMPLE_OUT} ({len(sample['rows'])} names) in {time.time() - t0:.0f}s")
    return sample


# --------------------------------------------------------------------------
# --pull
# --------------------------------------------------------------------------

class TokenBucket:
    """At most `capacity` acquires in any `per_seconds` window (sliding log)."""

    def __init__(self, capacity=BUCKET_CAPACITY, per_seconds=BUCKET_SECONDS,
                 clock=time.monotonic, sleep=time.sleep):
        self.capacity, self.per_seconds = int(capacity), float(per_seconds)
        self.clock, self.sleep = clock, sleep
        self.log = deque()
        self.n_waits = 0

    def _evict(self, now):
        while self.log and now - self.log[0] >= self.per_seconds:
            self.log.popleft()

    def acquire(self):
        now = self.clock()
        self._evict(now)
        while len(self.log) >= self.capacity:
            wait = self.log[0] + self.per_seconds - now
            self.n_waits += 1
            self.sleep(max(wait, 1e-3))
            now = self.clock()
            self._evict(now)
        self.log.append(now)
        return now


def _bar_date(d):
    s = str(d)
    if len(s) == 8 and s.isdigit():
        return f"{s[:4]}-{s[4:6]}-{s[6:]}"
    return s[:10]


def _account_type(accounts):
    if not accounts:
        return "unknown"
    if all(a.startswith(("DU", "DF")) for a in accounts):
        return "paper"
    if all(a.startswith("U") for a in accounts):
        return "live"
    return "mixed"


def _is_subscription_error(code, msg):
    m = (msg or "").lower()
    return code in SUBSCRIPTION_CODES or "subscri" in m or "market data permissions" in m


def pull(ib, rows, out_dir, make_contract, bucket, meta_base, log=_log,
         max_consecutive_missing=MAX_CONSECUTIVE_MISSING):
    """Drive any client exposing reqContractDetails / reqHistoricalData /
    managedAccounts (and optionally errorEvent) over the sample. Resumable:
    names with an existing CSV are skipped. Writes only what the client returned.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    meta_path = out_dir / "_meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    meta.update(meta_base)
    meta.setdefault("symbols_ok", [])
    meta.setdefault("symbols_unresolved", [])
    meta.setdefault("symbols_error", {})
    meta.setdefault("symbols_codes", {})
    meta.setdefault("semantics_share", {})
    meta["n_sample"] = len(rows)

    errors = []

    def on_error(reqId, errorCode, errorString, contract=None, *rest):
        errors.append((reqId, int(errorCode), str(errorString),
                       getattr(contract, "symbol", None)))

    ev = getattr(ib, "errorEvent", None)
    if ev is not None:
        ev += on_error

    def save():
        meta["updated_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        _dump(meta, meta_path)

    consecutive = 0
    n_new = 0
    try:
        for i, r in enumerate(rows):
            sym = r["symbol"]
            csv = out_dir / f"{sym}.csv"
            if csv.exists():
                if sym not in meta["symbols_ok"]:
                    meta["symbols_ok"].append(sym)
                log(f"[{i + 1:3d}/{len(rows)}] {sym:6s} cached, skip")
                continue
            contract = make_contract(sym, r["primaryExchange"])
            cds = ib.reqContractDetails(contract)
            if not cds:
                log(f"[{i + 1:3d}/{len(rows)}] {sym:6s} UNRESOLVED by reqContractDetails")
                if sym not in meta["symbols_unresolved"]:
                    meta["symbols_unresolved"].append(sym)
                save()
                continue
            qc = cds[0].contract
            bucket.acquire()
            n0 = len(errors)
            bars = ib.reqHistoricalData(qc, endDateTime=END_DATETIME, durationStr=DURATION,
                                        barSizeSetting=BAR_SIZE, whatToShow=WHAT_TO_SHOW,
                                        useRTH=USE_RTH, formatDate=FORMAT_DATE)
            codes = [(c, m) for (_, c, m, _) in errors[n0:]]
            logged = [{"code": c, "msg": m} for c, m in codes if c in LOGGED_CODES or _is_subscription_error(c, m)]
            if logged:
                meta["symbols_codes"][sym] = logged
                for c, m in codes:
                    log(f"[{i + 1:3d}/{len(rows)}] {sym:6s} code {c}: {m}")
            if not bars:
                meta["symbols_error"][sym] = logged or [{"code": None, "msg": "no bars returned"}]
                if any(_is_subscription_error(c, m) for c, m in codes):
                    consecutive += 1
                    if consecutive >= max_consecutive_missing:
                        save()
                        raise SystemExit(f"subscription missing: {consecutive} consecutive names "
                                         f"returned subscription errors (last {sym})")
                save()
                continue
            consecutive = 0
            df = pd.DataFrame({
                "date": [_bar_date(b.date) for b in bars],
                "open": [float(b.open) for b in bars],
                "high": [float(b.high) for b in bars],
                "low": [float(b.low) for b in bars],
                "close": [float(b.close) for b in bars],
                "volume": [float(b.volume) for b in bars],
                "average": [float(getattr(b, "average", float("nan"))) for b in bars],
                "barCount": [int(getattr(b, "barCount", 0)) for b in bars],
            })
            share = check_bar_semantics(sym, df["open"].to_numpy(), df["close"].to_numpy())
            df.to_csv(csv, index=False)
            n_new += 1
            meta["semantics_share"][sym] = share
            meta["symbols_error"].pop(sym, None)
            if sym not in meta["symbols_ok"]:
                meta["symbols_ok"].append(sym)
            log(f"[{i + 1:3d}/{len(rows)}] {sym:6s} {len(df)} bars {df['date'].iloc[0]}..{df['date'].iloc[-1]} "
                f"close>=open {share:.1%}")
            save()
    finally:
        if ev is not None:
            try:
                ev -= on_error
            except Exception:
                pass
        save()
    return {"n_new": n_new, "meta": meta}


def cmd_pull(host, port, client_id):
    import ib_async                                  # lazy: only this path needs it
    from ib_async import IB, Stock

    sample = json.loads(SAMPLE_OUT.read_text())
    ib = IB()
    # ib_insync named this setConnectionOptions; ib_async 2.x renamed it
    # setConnectOptions and stores the bytes in client.connectOptions. Must be
    # set BEFORE connect(): it rides on the handshake.
    pace = None
    client = getattr(ib, "client", None)
    for name in ("setConnectOptions", "setConnectionOptions"):
        if hasattr(client, name):
            getattr(client, name)("+PACEAPI")
            pace = f"client.{name}('+PACEAPI')"
            break
    else:
        if hasattr(client, "connectOptions"):
            client.connectOptions = b"+PACEAPI"
            pace = "client.connectOptions = b'+PACEAPI'"
    _log(f"connecting {host}:{port} clientId={client_id}; pacing option: {pace or 'not available in this ib_async'}")
    ib.connect(host, port, clientId=client_id, readonly=True)
    accounts = list(ib.managedAccounts())
    meta_base = {
        "record": "D336",
        "provider": "Interactive Brokers TWS API via ib_async",
        "ib_async_version": getattr(ib_async, "__version__", "?"),
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "accounts": accounts, "account_type": _account_type(accounts),
        "whatToShow": WHAT_TO_SHOW, "useRTH": USE_RTH, "end": END_DATETIME,
        "durationStr": DURATION, "barSizeSetting": BAR_SIZE, "formatDate": FORMAT_DATE,
        "exchange": "SMART", "currency": "USD", "pacing": pace,
        "bucket": {"capacity": BUCKET_CAPACITY, "per_seconds": BUCKET_SECONDS},
        "sample_file": str(SAMPLE_OUT.relative_to(REPO)),
        "bar_semantics": "open = time-average bid, close = time-average ask, "
                         "high = max ask, low = min bid (IBKR BID_ASK daily bars)",
    }
    bucket = TokenBucket()
    try:
        res = pull(ib, sample["rows"], RAW_DIR, lambda s, pe: Stock(s, "SMART", "USD", primaryExchange=pe),
                   bucket, meta_base)
    finally:
        ib.disconnect()
    m = res["meta"]
    _log(f"done: ok {len(m['symbols_ok'])}, unresolved {len(m['symbols_unresolved'])}, "
         f"error {len(m['symbols_error'])}; bucket waited {bucket.n_waits} times")


# --------------------------------------------------------------------------
# --compare
# --------------------------------------------------------------------------

def compare(sample, fx, raw_dir, out_path, log=_log):
    raw_dir = Path(raw_dir)
    calls0 = select_winner.calls
    syms = [r["symbol"] for r in sample["rows"]]
    fx = fx[fx["symbol"].isin(syms)]
    groups = {s: g.sort_values("date") for s, g in fx.groupby("symbol")}

    rows, missing = [], []
    for r in sample["rows"]:
        sym = r["symbol"]
        p = raw_dir / f"{sym}.csv"
        if not p.exists():
            missing.append(sym)
            continue
        ib = pd.read_csv(p, dtype={"date": str}).sort_values("date")
        ok, half = quoted_half(ib["open"].to_numpy(), ib["close"].to_numpy())
        q = ib[ok]
        qdates = q["date"].to_numpy(dtype=str)
        assert_N(sym, len(qdates))
        quoted = float(np.median(half[ok]))
        g = groups.get(sym)
        if g is None:
            raise AssertionError(f"[W] {sym}: not in the fixture")
        j = g[g["date"].isin(qdates)]
        assert_W(sym, qdates, j["date"].to_numpy(dtype=str))
        H, L, C = (j[k].to_numpy(dtype=float) for k in ("high", "low", "close"))
        est = ohlc_estimates(H, L, C)
        ib_mid_last = float((q["open"].iloc[-1] + q["close"].iloc[-1]) / 2.0)
        assert_G(sym, ib_mid_last, float(C[-1]))
        assert_U(sym, quoted, est)
        rows.append({"symbol": sym, "price_q": r["price_q"], "dv_q": r["dv_q"],
                     "n_ib_bars": int(len(ib)), "n_quoted_days": int(len(qdates)),
                     "first_date": str(qdates[0]), "last_date": str(qdates[-1]),
                     "quoted_half_bp": quoted * 1e4,
                     "PB_bp": est["PB"] * 1e4, "PUB_bp": est["PUB"] * 1e4, "AR_bp": est["AR"] * 1e4,
                     "zero_rate": est["zero_rate"], "n_cs": est["n_cs"], "n_trail": est["n_trail"],
                     "ib_mid_last": ib_mid_last, "fixture_close_last": float(C[-1]),
                     "g_abs_log": abs(math.log(ib_mid_last / float(C[-1])))})
    if not rows:
        raise AssertionError("no name has a raw CSV to compare")

    quoted = np.array([r["quoted_half_bp"] for r in rows]) / 1e4
    errs, floored = {}, {}
    for k in ESTIMATORS:
        est = np.array([r[f"{k}_bp"] for r in rows]) / 1e4
        le, nf, mask = floor_and_log(est)
        assert_Z(est, le, nf)
        errs[k] = le - np.log(quoted)
        floored[k] = nf
        for i, r in enumerate(rows):
            r[f"log_err_{k}"] = float(errs[k][i])
            r[f"floored_{k}"] = bool(mask[i])

    winner, male = select_winner(errs)
    n_calls = select_winner.calls - calls0
    assert_K(n_calls, RULE)

    strata = {}
    for pq in range(N_Q):
        for dq in range(N_Q):
            idx = [i for i, r in enumerate(rows) if r["price_q"] == pq and r["dv_q"] == dq]
            if not idx:
                continue
            cell = {"n": len(idx), "quoted_half_bp_median": float(np.median(quoted[idx]) * 1e4)}
            for k in ESTIMATORS:
                cell[f"median_log_err_{k}"] = float(np.median(errs[k][idx]))
                cell[f"MALE_{k}"] = float(np.median(np.abs(errs[k][idx])))
            strata[f"{pq},{dq}"] = cell

    zr = np.array([r["zero_rate"] for r in rows])
    hi, lo = zr > 0.5, zr < 0.25
    q3_hi = float(np.median(errs["PB"][hi])) if hi.any() else None
    q3_lo = float(np.median(errs["PB"][lo])) if lo.any() else None
    q4_med = float(np.median(quoted) * 1e4)
    predictions = {
        "Q1": {"text": "MALE(PUB) < MALE(PB) and MALE(PB) > ln 2",
               "MALE_PUB": male["PUB"], "MALE_PB": male["PB"], "ln2": LN2,
               "holds": bool(male["PUB"] < male["PB"] and male["PB"] > LN2)},
        "Q2": {"text": "MALE(AR) < min(MALE(PB), MALE(PUB))",
               "MALE_AR": male["AR"], "holds": bool(male["AR"] < min(male["PB"], male["PUB"]))},
        "Q3": {"text": "zero rate > 50%: median log_err_PB < -ln 2; zero rate < 25%: within +/- ln 1.5",
               "n_zero_gt_50": int(hi.sum()), "median_log_err_PB_zero_gt_50": q3_hi,
               "n_zero_lt_25": int(lo.sum()), "median_log_err_PB_zero_lt_25": q3_lo,
               "holds_hi": (q3_hi < -LN2) if q3_hi is not None else None,
               "holds_lo": (abs(q3_lo) < LN15) if q3_lo is not None else None},
        "Q4": {"text": "sample median quoted half-spread in [18, 28] bp",
               "median_quoted_half_bp": q4_med, "holds": bool(18.0 <= q4_med <= 28.0)},
        "Q5": {"text": "winner's MALE < ln 1.5 (else no daily OHLC estimator is fit; declared floor)",
               "winner": winner, "MALE_winner": male[winner], "ln1.5": LN15,
               "holds": bool(male[winner] < LN15)},
    }
    predictions["Q3"]["holds"] = (predictions["Q3"]["holds_hi"] is not False
                                  and predictions["Q3"]["holds_lo"] is not False
                                  and (predictions["Q3"]["holds_hi"] is not None
                                       or predictions["Q3"]["holds_lo"] is not None))

    out = {
        "record": "D336",
        "selection_rule": RULE,
        "select_winner_calls": n_calls,
        "winner": winner,
        "MALE": male,
        "n_compared": len(rows), "n_missing_csv": len(missing), "missing_csv": missing,
        "n_floored_at_1bp": floored,
        "floor_proportional": FLOOR,
        "median_quoted_half_bp": q4_med,
        "median_est_bp": {k: float(np.median([r[f"{k}_bp"] for r in rows])) for k in ESTIMATORS},
        "assertions_passed": ["W", "U", "N", "K", "Z", "G"],
        "predictions": predictions,
        "strata": strata,
        "rows": rows,
    }
    _dump(out, Path(out_path))

    log(f"compared {len(rows)} names ({len(missing)} without a CSV); winner = {winner} by '{RULE}'")
    log(f"  median quoted half {q4_med:.1f} bp; median est bp: "
        + ", ".join(f"{k} {out['median_est_bp'][k]:.1f}" for k in ESTIMATORS))
    log("  MALE: " + ", ".join(f"{k} {male[k]:.3f} (x{math.exp(male[k]):.2f})" for k in ESTIMATORS)
        + f"; floored at 1 bp: {floored}")
    for k in ESTIMATORS:
        log(f"  strata MALE_{k} (rows price_q 0..4, cols dv_q 0..4):")
        for pq in range(N_Q):
            log("    " + " ".join(f"{strata[f'{pq},{dq}'][f'MALE_{k}']:6.3f}" if f"{pq},{dq}" in strata else "     -"
                                   for dq in range(N_Q)))
    for qk, qv in predictions.items():
        log(f"  {qk}: {'HOLDS' if qv['holds'] else 'FAILS'} -- {qv['text']}")
    log(f"wrote {out_path}")
    return out


def cmd_compare():
    sample = json.loads(SAMPLE_OUT.read_text())
    fx = load_fixture([r["symbol"] for r in sample["rows"]])
    return compare(sample, fx, RAW_DIR, COMPARE_OUT)


# --------------------------------------------------------------------------
# --selftest
# --------------------------------------------------------------------------

class _Event:
    def __init__(self):
        self.handlers = []

    def __iadd__(self, h):
        self.handlers.append(h)
        return self

    def __isub__(self, h):
        self.handlers.remove(h)
        return self

    def emit(self, *a):
        for h in list(self.handlers):
            h(*a)


class MockIB:
    """Synthetic daily BID_ASK bars with IBKR semantics: open = avg bid, close =
    avg ask, mid = the fixture close on that date. Half-spread `half` with 30%
    multiplicative noise. Only for --selftest."""

    def __init__(self, window_by_sym, half=0.0020, unresolved=(), sub_missing=(),
                 bad_semantics=False, seed=0):
        self.window = window_by_sym
        self.half = half
        self.unresolved, self.sub_missing = set(unresolved), set(sub_missing)
        self.bad_semantics = bad_semantics
        self.rng = np.random.default_rng(seed)
        self.errorEvent = _Event()
        self.n_hist = 0
        self.n_details = 0

    def managedAccounts(self):
        return ["DU0000000"]

    def reqContractDetails(self, contract):
        self.n_details += 1
        if contract.symbol in self.unresolved:
            return []
        return [SimpleNamespace(contract=SimpleNamespace(
            symbol=contract.symbol, exchange="SMART", currency="USD",
            primaryExchange=contract.primaryExchange, conId=1))]

    def reqHistoricalData(self, contract, endDateTime, durationStr, barSizeSetting,
                          whatToShow, useRTH, formatDate=1, **kw):
        self.n_hist += 1
        assert (whatToShow, useRTH, barSizeSetting, durationStr, endDateTime) == \
            (WHAT_TO_SHOW, USE_RTH, BAR_SIZE, DURATION, END_DATETIME), "pull parameters drifted"
        sym = contract.symbol
        if sym in self.sub_missing:
            self.errorEvent.emit(self.n_hist, 354, "Requested market data is not subscribed.", contract)
            return []
        g = self.window[sym]
        bars = []
        for d, mid in zip(g["date"], g["close"]):
            h = max(self.half * (1.0 + 0.3 * self.rng.standard_normal()), 1e-5)
            bid, ask = mid * (1 - h), mid * (1 + h)
            if self.bad_semantics:
                bid, ask = ask, bid
            bars.append(SimpleNamespace(date=d.replace("-", ""), open=bid, high=max(bid, ask) * 1.001,
                                        low=min(bid, ask) * 0.999, close=ask, volume=0.0,
                                        average=mid, barCount=0))
        return bars


def _expect_raise(label, fn, exc=(AssertionError, SystemExit)):
    try:
        fn()
    except exc as e:
        _log(f"    [6] {label:44s} raised: {str(e)[:90]}")
        return
    raise AssertionError(f"[6] {label}: did not raise on a broken input")


def cmd_selftest():
    t0 = time.time()
    _log("== (a) --plan logic on the real fixture")
    meta = json.loads(META.read_text())
    fx = load_fixture()
    sample = plan(fx, meta)
    _print_plan(sample)
    assert len(sample["rows"]) == N_Q * N_Q * PER_CELL, f"sample has {len(sample['rows'])} names, not 100"
    cell_n = pd.Series([f"{r['price_q']},{r['dv_q']}" for r in sample["rows"]]).value_counts()
    assert len(cell_n) == N_Q * N_Q and (cell_n == PER_CELL).all(), "not 4 per cell"
    n_filled = sum(1 for r in sample["rows"] if "filled_from_cell" in r)
    assert n_filled == sum(len(f["filled"]) for f in sample["fills"]), "fills not documented"
    assert len({r["symbol"] for r in sample["rows"]}) == len(sample["rows"]), "duplicate symbol"
    sample2 = plan(fx, meta)
    assert [r["symbol"] for r in sample2["rows"]] == [r["symbol"] for r in sample["rows"]], "plan not deterministic"
    if SAMPLE_OUT.exists():
        on_disk = json.loads(SAMPLE_OUT.read_text())
        same = [r["symbol"] for r in on_disk["rows"]] == [r["symbol"] for r in sample["rows"]]
        assert same, f"{SAMPLE_OUT} differs from the plan logic"
        _log(f"  matches {SAMPLE_OUT.name} on disk: {same}")
    _log(f"  (a) OK: 100 names, 4 per cell, {n_filled} filled, deterministic")

    _log("== (b) Abdi-Ranaldo on synthetic data")
    rng = np.random.default_rng(0)
    n = 5000
    m = np.cumsum(rng.normal(0.0, 0.02, n))
    d = np.abs(rng.normal(0.0, 0.01, n))
    H, L = np.exp(m + d), np.exp(m - d)
    q = np.where(rng.random(n) < 0.5, -1.0, 1.0)
    s = math.log(1.005)
    half = abdi_ranaldo_half(H, L, np.exp(m + q * s))
    _log(f"  half_AR with 50 bp bounce: {half * 1e4:.2f} bp (target 50, tol 5)")
    assert abs(half - 0.005) < 0.0005, "[S] AR missed the synthetic 50 bp half-spread"
    half0 = abdi_ranaldo_half(H, L, np.exp(m))
    half_walk = abdi_ranaldo_half(np.exp(m), np.exp(m), np.exp(m))
    _log(f"  half_AR, C = exp(m) inside the H/L band: {half0!r}; pure random walk H = L = C: {half_walk!r}")
    assert half_walk == 0.0, "[S] AR not exactly 0 on a pure random walk"
    assert half0 == 0.0 or half0 < 1e-9, "[S] AR not zero (to rounding) with no bounce"
    # PUB's trailing window may only look back: perturb bar k, nothing at <= k moves
    est = estimators()
    cs = rng.random(300)
    lag = np.concatenate([[np.nan], cs[:-1]])
    base = est["trail"](lag, est["CS_BARS"], lambda w: np.nanmean(w, axis=1))
    cs2 = cs.copy()
    cs2[150] += 10.0
    lag2 = np.concatenate([[np.nan], cs2[:-1]])
    pert = est["trail"](lag2, est["CS_BARS"], lambda w: np.nanmean(w, axis=1))
    assert np.array_equal(base[:151], pert[:151], equal_nan=True), "PUB window looked ahead"
    assert not np.array_equal(base[151:], pert[151:], equal_nan=True)
    _log("  (b) OK; trailing-21 window is causal")

    _log("== (c) TokenBucket on a fake clock")
    clk = SimpleNamespace(t=0.0)
    tb = TokenBucket(BUCKET_CAPACITY, BUCKET_SECONDS, clock=lambda: clk.t,
                     sleep=lambda s: setattr(clk, "t", clk.t + s))
    times = []
    for _ in range(100):
        clk.t += float(rng.uniform(0.0, 30.0))
        times.append(tb.acquire())
    times = np.array(times)
    worst = np.min(times[BUCKET_CAPACITY:] - times[:-BUCKET_CAPACITY])
    _log(f"  100 acquires, {tb.n_waits} waits; min span of 31 consecutive acquires {worst:.1f} s (>= 600 required)")
    assert_P(times)
    assert tb.n_waits > 0, "[P] the bucket was never binding; the test proves nothing"
    _log("  (c) OK")

    _log("== (d) mocked IB client through the pull path and --compare, in a temp dir")
    diag = [r for r in sample["rows"] if r["price_q"] == r["dv_q"]]        # 20 names, 5 cells
    others = [r for r in sample["rows"] if r["price_q"] != r["dv_q"]]
    rows = diag + others[:2]
    unresolved, sub_missing = others[0]["symbol"], others[1]["symbol"]
    dates = np.sort(fx["date"].unique())[-WINDOW_BARS:]
    sub = fx[fx["symbol"].isin([r["symbol"] for r in rows]) & fx["date"].isin(dates)]
    window_by_sym = {s: g.sort_values("date")[["date", "close"]] for s, g in sub.groupby("symbol")}
    mini = dict(sample, rows=rows)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        mock = MockIB(window_by_sym, half=0.0020, unresolved=[unresolved], sub_missing=[sub_missing])
        tb = TokenBucket(clock=lambda: clk.t, sleep=lambda s: setattr(clk, "t", clk.t + s))
        base = {"provider": "mock", "accounts": mock.managedAccounts(),
                "account_type": _account_type(mock.managedAccounts())}
        res = pull(mock, rows, td / "raw", lambda s, pe: SimpleNamespace(symbol=s, primaryExchange=pe),
                   tb, base, log=lambda *a: None)
        m = res["meta"]
        assert res["n_new"] == 20 and len(m["symbols_ok"]) == 20, m
        assert m["symbols_unresolved"] == [unresolved] and list(m["symbols_error"]) == [sub_missing]
        assert m["symbols_codes"][sub_missing][0]["code"] == 354
        assert m["account_type"] == "paper" and mock.n_hist == 21 and mock.n_details == 22
        assert not (td / "raw" / f"{sub_missing}.csv").exists(), "an error wrote a CSV"
        _log(f"  pull: {res['n_new']} CSVs, unresolved {m['symbols_unresolved']}, "
             f"error {dict(m['symbols_error'])}")
        res2 = pull(mock, rows, td / "raw", lambda s, pe: SimpleNamespace(symbol=s, primaryExchange=pe),
                    tb, base, log=lambda *a: None)
        assert res2["n_new"] == 0 and mock.n_hist == 22, "resume re-pulled cached names"
        _log("  resume: 0 new CSVs, only the errored name re-requested")
        csv0 = pd.read_csv(td / "raw" / f"{rows[0]['symbol']}.csv", dtype={"date": str})
        assert csv0["date"].iloc[0].count("-") == 2 and len(csv0) == WINDOW_BARS
        out = compare(mini, fx, td / "raw", td / "cmp.json", log=lambda *a: None)
        assert out["n_compared"] == 20 and out["n_missing_csv"] == 2
        assert out["select_winner_calls"] == 1 and out["selection_rule"] == RULE
        assert out["winner"] in ESTIMATORS and len(out["strata"]) == 5
        assert 18.0 <= out["median_quoted_half_bp"] <= 22.0, out["median_quoted_half_bp"]
        assert all(r["n_quoted_days"] == WINDOW_BARS and r["last_date"] == WINDOW_END for r in out["rows"])
        assert all(r["g_abs_log"] < 1e-9 for r in out["rows"])
        assert json.loads((td / "cmp.json").read_text())["selection_rule"] == RULE
        _log(f"  compare: {out['n_compared']} names, median quoted {out['median_quoted_half_bp']:.1f} bp "
             f"(injected 20), winner {out['winner']}, MALE "
             + ", ".join(f"{k} {out['MALE'][k]:.3f}" for k in ESTIMATORS)
             + f", floored {out['n_floored_at_1bp']}")
        _log("  predictions on the mock (not evidence): "
             + ", ".join(f"{k} {'holds' if v['holds'] else 'fails'}" for k, v in out["predictions"].items()))

        _log("== (e) every assertion raises on a deliberately broken input")
        mock_bad = MockIB(window_by_sym, bad_semantics=True)
        _expect_raise("bar semantics gate (open > close)",
                      lambda: pull(mock_bad, rows[:1], td / "bad", lambda s, pe: SimpleNamespace(symbol=s, primaryExchange=pe),
                                   tb, base, log=lambda *a: None))
        assert not (td / "bad" / f"{rows[0]['symbol']}.csv").exists(), "the gate wrote a CSV"
        mock_sub = MockIB(window_by_sym, sub_missing=[r["symbol"] for r in rows])
        _expect_raise("10 consecutive subscription errors abort",
                      lambda: pull(mock_sub, rows, td / "sub", lambda s, pe: SimpleNamespace(symbol=s, primaryExchange=pe),
                                   tb, base, log=lambda *a: None))
        assert mock_sub.n_hist == MAX_CONSECUTIVE_MISSING
        # [W]
        qd = np.array(["2026-08-24", "2026-08-25", "2026-08-26"])
        _expect_raise("[W] quoted date missing from fixture", lambda: assert_W("X", qd, qd[:2]))
        _expect_raise("[W] misaligned dates", lambda: assert_W("X", qd, np.array(["2026-08-23", "2026-08-25", "2026-08-26"])))
        _expect_raise("[W] look-ahead past window end", lambda: assert_W("X", np.append(qd, "2026-08-27"), np.append(qd, "2026-08-27")))
        _expect_raise("[W] non-increasing dates", lambda: assert_W("X", qd[[0, 2, 1]], qd[[0, 2, 1]]))
        assert_W("X", qd, qd)
        # [U]
        good = {"PB": 1e-3, "PUB": 2e-3, "AR": 1.5e-3}
        _expect_raise("[U] negative estimate", lambda: assert_U("X", 1e-3, dict(good, PB=-1e-4)))
        _expect_raise("[U] NaN estimate", lambda: assert_U("X", 1e-3, dict(good, AR=float("nan"))))
        _expect_raise("[U] quoted zero", lambda: assert_U("X", 0.0, good))
        assert_U("X", 1e-3, good)
        # [N]
        _expect_raise("[N] 199 quoted days", lambda: assert_N("X", MIN_QUOTED_DAYS - 1))
        assert_N("X", MIN_QUOTED_DAYS)
        # [G]
        _expect_raise("[G] IB mid 10% off fixture close", lambda: assert_G("X", 11.0, 10.0))
        _expect_raise("[G] exactly at tolerance", lambda: assert_G("X", 10.0 * math.exp(G_TOL), 10.0))
        assert_G("X", 10.2, 10.0)
        # [Z]
        e = np.array([0.0, 5e-5, 2e-3])
        le, nf, _ = floor_and_log(e)
        assert nf == 2 and le[0] == math.log(FLOOR)
        _expect_raise("[Z] floored count under-reported", lambda: assert_Z(e, le, nf - 1))
        _expect_raise("[Z] floored value not at the floor", lambda: assert_Z(e, np.array([-20.0, le[1], le[2]]), nf))
        assert_Z(e, le, nf)
        # [K]
        _expect_raise("[K] select_winner called twice", lambda: assert_K(2, RULE))
        _expect_raise("[K] rule text differs", lambda: assert_K(1, "lowest mean absolute error in log spread"))
        assert_K(1, RULE)
        # semantics gate as a function
        _expect_raise("bar semantics 98%", lambda: check_bar_semantics("X", np.r_[np.zeros(98), 2.0, 2.0], np.r_[np.ones(98), 1.0, 1.0]))
        # [P] an unpaced acquire log (one every 10 s: 31 in 300 s) must fail
        _expect_raise("[P] unpaced acquire log", lambda: assert_P(np.arange(100) * 10.0))
        assert_P(np.arange(100) * 20.0)                         # 30 per 600 s exactly: allowed
        _log("  (e) OK")
    _log(f"SELFTEST PASSED in {time.time() - t0:.0f}s")


# --------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--plan", action="store_true", help="write data/d336_sample.json from the fixture")
    g.add_argument("--pull", action="store_true", help="pull daily BID_ASK bars from a live TWS/Gateway session")
    g.add_argument("--compare", action="store_true", help="PB vs PUB vs AR against the quoted half-spread")
    g.add_argument("--selftest", action="store_true", help="plan, AR, bucket, mocked pull+compare, assertions")
    ap.add_argument("--host", default=None)
    ap.add_argument("--port", type=int, default=None)
    ap.add_argument("--client-id", type=int, default=None)
    a = ap.parse_args(argv)
    if a.pull:
        if a.host is None or a.port is None or a.client_id is None:
            ap.error("--pull needs --host, --port and --client-id")
        if not SAMPLE_OUT.exists():
            ap.error(f"{SAMPLE_OUT} missing: run --plan first")
        cmd_pull(a.host, a.port, a.client_id)
    elif a.plan:
        cmd_plan()
    elif a.compare:
        cmd_compare()
    elif a.selftest:
        cmd_selftest()
    return 0


if __name__ == "__main__":
    sys.exit(main())
