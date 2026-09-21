"""Hurdle P (RULES.md R11), dollar-native — D590.

R11's six criteria have been computed four times, each time inside the runner that
needed them, each time on a slightly different convention: D266 (P1 as `size = 0.04/dd`),
D440 (P4 as the account's life), D495 (P5's exact haircut), D500/D501 (P3 as a rate),
D503 (all six at once, on the forward slice). This module is the one implementation, so
the fifth record does not become a fifth convention.

WHAT R11 SAYS TODAY, after all six amendments, is not what its header table says:

  P1  a SIZING RULE that cannot fail (restatement 2026-09-08). Its output is a NUMBER —
      the post-sizing return — never PASS/FAIL. `p1_size` returns numbers.
  P2  no exposure across the VENUE'S flatten time (amendment 2026-08-29). Venue-specific.
  P3  a RATE, not a maximum (amendment 2026-09-13): P3a breaches/year <= 1.0, P3b life
      cost <= 33%, P3c the worst day REPORTED and no longer a gate.
  P4  no longer a hard hurdle (restatement 2026-09-12): binding is *expected profit
      before breach > the account's cost*; a life >= 1 year is preferred, not binding;
      and "time-to-breach" is the ACCOUNT'S LIFE, never 1/(per-hold breach rate)
      (RULING 2026-09-11).
  P5  a CALCULATION CONVENTION, not a screen (restatement 2026-09-12): the 30% single-day
      haircut. **The R11 header table still says 40%. 30% is operative** — the restatement
      supersedes the table, `scripts/d495_agree_confluence.py` has used 0.30 since
      2026-09-12, and this module uses 0.30. RULES.md is append-only and is NOT edited
      here; the discrepancy is recorded in D590 instead.
  P6  a structural fact about a venue: only Topstep and MyFundedFutures permit automation
      when funded.

DOLLAR-NATIVE, AND THAT IS THE WHOLE DESIGN (D542). The prop floor is an **absolute
dollar distance from a ratcheting peak on a cumulative-SUM equity curve**:

    eq += x;  peak = max(peak, eq);  dead if peak - eq >= cap

It is not a fraction of a compounded peak, so `analytics/metrics.py:max_drawdown` —
which computes exactly that — is the wrong instrument and is deliberately not imported.
Every quantity crossing this module's boundary is US DOLLARS, except `sigma_frac` and
`D` inside `expected_profit_before_breach`, which are ACCOUNT FRACTIONS and are reached
only through `expected_profit_before_breach_usd`, which converts and asserts. A unit
slip on exactly that boundary crashed D503's first run.

RAISE, NEVER DEFAULT (D48). Every guard here raises. A hurdle that returns a plausible
wrong number is worse than one that stops.

REPRODUCTION. `tests/unit/test_hurdle_p.py` and `tests/golden/test_hurdle_p_ledger.py`
hold this module against the published numbers it inherits, by loading the reference
runners by file path (from the tests, never from this package) and never editing them:

  * `p3` / `max_drawdown_life` vs `scripts/d501_worst_day_frequency.py` on D501's own
    in-sample input path (NQ AGREE M=5, 1,873 sessions 2016-01-07..2023-12-29);
  * `p4_life` vs `data/d440_lifecycle.json`'s published MFFU Rapid EOD 50K / SPY /
    voltgt cell (f* 0.007, V $77.74, funded life 0.135 years);
  * `hurdle_p` vs `scripts/d503_forward_book.py:hurdle_p`, function against function, on
    random series (D503's own daily series is not committed, and its inputs are the
    2024+ forward slice, which this module does not read);
  * `p5_recognised` vs `scripts/d495_agree_confluence.py:p5_recognised`, property test.
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Literal

import numpy as np

__all__ = [
    "ACCOUNT_DEFAULT",
    "EOD",
    "INTRA",
    "P3A_BAR",
    "P3B_BAR",
    "P5_CAP",
    "STATIC",
    "TRADING_DAYS",
    "Plan",
    "expected_profit_before_breach",
    "expected_profit_before_breach_usd",
    "gauss_provider",
    "hurdle_p",
    "load_venue",
    "max_drawdown_life",
    "measured_provider",
    "notional_series",
    "p1_size",
    "p2_flatten",
    "p3",
    "p4_life",
    "p5_recognised",
    "p6",
    "p_at_least_one",
    "per_year",
    "recurrence_years",
    "sigma_series",
    "simulate_provider",
    "venue_keys",
    "venue_record",
]

# ---------------------------------------------------------------- constants, all sourced

TRADING_DAYS = 252
ACCOUNT_DEFAULT = 50_000.0
DD_FRACTION = 0.04                  # R11 P1: the account's WHOLE loss budget
P3_CAP_FRACTION = 0.02              # R11 P3: the daily loss limit, 2% of the account
P3A_BAR = 1.0                       # R11 P3 amendment 2026-09-13: breaches a year
P3B_BAR = 0.33                      # R11 P3 amendment 2026-09-13: share of the life
P5_CAP = 0.30                       # R11 P5 restatement 2026-09-12 (the header table's 40% is stale)
P4_LIFE_PREFERRED_YEARS = 1.0       # R11 P4 restatement 2026-09-12: preferred, NOT binding

# The lower unit guard on `expected_profit_before_breach_usd`: $0.50 a day on a $50,000
# account. Below one tick of every instrument these venues offer, so a daily dollar sigma
# cannot reach it and a FRACTION passed where dollars belong always does.
MIN_SIGMA_FRAC = 1e-5

EOD, INTRA, STATIC = "eod", "intra", "static"

# d440_lifecycle.py's constants, reproduced so `p4_life` can reproduce its published cell.
VOL_WINDOW = 21                     # D259: "the prior 21 holds only"
VOL_CAP = 4.0                       # D259: "capped", at 4x static
SEED_D440 = 20260911

_REPO = Path(__file__).resolve().parents[3]
VENUES_JSON = _REPO / "data" / "prop_venues.json"


# ---------------------------------------------------------------- the venue


@dataclass(frozen=True)
class Plan:
    """A prop plan's geometry. Field names, order and defaults are `d386_full_lifecycle.Plan`.

    Declared here rather than imported because `src/` may not depend on `scripts/`.
    `tests/unit/test_hurdle_p.py` asserts field-by-field equality with every entry of
    `d386_full_lifecycle.PLANS`, so the duplication is checked rather than trusted.
    """

    firm: str
    size: int
    fee_eval: float            # one-time, or per month if monthly=True
    monthly: bool
    fee_activation: float
    target: float
    dd_eval: float
    kind_eval: str
    lock_eval: float | None    # ref cap, relative to start; None = never locks
    dd_fund: float
    kind_fund: str
    lock_fund: float | None
    qual_threshold: float      # minimum daily profit for a day to count
    qual_days: int
    min_total: float           # minimum net profit since last payout
    caps: tuple                # payout cap schedule; last value repeats
    max_payouts: int
    min_payout: float
    safety_net: float          # balance must stay at or above start + this to withdraw
    consistency: float | None  # best day <= consistency * profit-since-payout, else wait
    fund_start: float = 0.0
    post_payout_floor: float | None = None
    start_funded: bool = False
    notes: str = ""


_VENUE_CACHE: dict[str, Any] = {}


def _venues() -> dict:
    if "doc" not in _VENUE_CACHE:
        if not VENUES_JSON.exists():
            raise FileNotFoundError(f"no venue terms at {VENUES_JSON}")
        _VENUE_CACHE["doc"] = json.loads(VENUES_JSON.read_text(encoding="utf-8"))
    return _VENUE_CACHE["doc"]


def venue_keys() -> list[str]:
    """Every venue key in `data/prop_venues.json`, sorted."""
    return sorted(_venues()["venues"])


def venue_record(key: str) -> dict:
    """The full record for `key`, every field carrying its own provenance."""
    v = _venues()["venues"]
    if key not in v:
        raise KeyError(f"unknown venue {key!r}; known: {sorted(v)}")
    return v[key]


def load_venue(key: str) -> Plan:
    """The venue's `Plan`, rebuilt from `data/prop_venues.json`."""
    rec = venue_record(key)
    plan = rec["plan"]
    kw: dict[str, Any] = {}
    for f in fields(Plan):
        if f.name not in plan:
            raise KeyError(f"venue {key!r} has no field {f.name!r} in prop_venues.json")
        val = plan[f.name]["value"]
        kw[f.name] = tuple(val) if f.name == "caps" else val
    return Plan(**kw)


# ---------------------------------------------------------------- P1, the sizing rule


def p1_size(d_usd: Sequence[float] | np.ndarray, cap_usd: float = 2_000.0) -> dict:
    """R11 P1: size so the trailing drawdown reaches `cap_usd`, and report the NUMBER.

    Never returns PASS/FAIL — P1 is a sizing rule and cannot fail (restatement
    2026-09-08). The output is the size multiplier and the annual dollars after it.

    The drawdown is the dollar distance from a ratcheting peak on the cumulative SUM of
    the daily dollars (D542), so the multiplier is exactly `cap_usd / max_trailing_dd`:
    trading k times the size multiplies every daily dollar, and therefore the drawdown,
    by k.

    HONEST ABOUT THE BASIS. R11 P1 measures the trailing drawdown on **OPEN** equity;
    a daily-close series has no intraday excursion, so `max_trailing_dd_usd` here is the
    CLOSED-equity drawdown and is a LOWER bound on the open-equity one. The multiplier is
    therefore an UPPER bound on the permitted size and the post-sizing return an upper
    bound on the return. `basis` says so in the returned dict.
    """
    x = np.asarray(d_usd, dtype=float)
    if x.size == 0:
        raise ValueError("p1_size: empty series")
    if not np.isfinite(x).all():
        raise ValueError("p1_size: series holds a non-finite value")
    if not (cap_usd > 0) or not math.isfinite(cap_usd):
        raise ValueError(f"p1_size: cap_usd must be a positive dollar amount, got {cap_usd!r}")
    eq = np.cumsum(x)
    dd = float((np.maximum.accumulate(np.maximum(eq, 0.0)) - eq).max())
    if not (dd > 0.0):
        raise ValueError("p1_size: the series never draws down from its running peak, so "
                         "no size satisfies a drawdown limit by construction -- P1 has no "
                         "answer here and returning one would be a false affordance (D48)")
    mult = cap_usd / dd
    mean = float(x.mean())
    return {
        "cap_usd": float(cap_usd),
        "max_trailing_dd_usd": dd,
        "size_multiplier": mult,
        "usd_per_year_at_traded_size": mean * TRADING_DAYS,
        "post_sizing_usd_per_year": mean * TRADING_DAYS * mult,
        "n_sessions": int(x.size),
        "basis": "closed equity (daily closes); R11 P1 measures OPEN equity, which is "
                 "deeper -- so the multiplier and the post-sizing return are UPPER bounds",
    }


# ---------------------------------------------------------------- P2, the flatten time


def _minutes_et(hhmm: str) -> int:
    if not isinstance(hhmm, str) or len(hhmm) != 5 or hhmm[2] != ":":
        raise ValueError(f"p2_flatten: {hhmm!r} is not an ET time 'HH:MM'")
    h, m = hhmm[:2], hhmm[3:]
    if not (h.isdigit() and m.isdigit()):
        raise ValueError(f"p2_flatten: {hhmm!r} is not an ET time 'HH:MM'")
    hi, mi = int(h), int(m)
    if not (0 <= hi <= 23 and 0 <= mi <= 59):
        raise ValueError(f"p2_flatten: {hhmm!r} is not a valid 24h ET time")
    return hi * 60 + mi


def p2_flatten(exit_times_et: Sequence[str], venue: str) -> bool:
    """R11 P2: is every exit at or before the VENUE'S stated flatten time (ET)?

    `exit_times_et` are the strategy's exit clock times as "HH:MM" in **US/Eastern** —
    the same clock `data/prop_venues.json` quotes, so a CT venue rule (Topstep's 15:10
    CT) has already been converted there and is never converted twice here.

    Raises when the venue's flatten time is unverified, which is the only honest answer:
    R11's amendment says whether a venue forbids the overnight "is a fact about the
    venue, to be quoted from its own documentation, never assumed."
    """
    rec = venue_record(venue)
    ft = rec["flatten_time_et"]["value"]
    if ft is None:
        raise ValueError(f"p2_flatten: {venue}'s flatten time is UNVERIFIED -- "
                         f"{rec['flatten_time_et']['provenance']}")
    if len(exit_times_et) == 0:
        raise ValueError("p2_flatten: no exit times given; an empty set trivially passes "
                         "and that is not a measurement (D48)")
    limit = _minutes_et(ft)
    return all(_minutes_et(t) <= limit for t in exit_times_et)


# ---------------------------------------------------------------- P3, the rate


def max_drawdown_life(d: Sequence[float] | np.ndarray,
                      cap: float) -> tuple[int, float, list]:
    """Deaths and mean life, where a death is the TRAILING drawdown first reaching `cap`.

    Ported verbatim from `scripts/d501_worst_day_frequency.py` and asserted equal to it.
    The account restarts FLAT after each death, which is what a prop account does: a new
    one is bought. `(n_deaths, mean_life_in_sessions, episodes)`, the mean UNROUNDED and
    0.0 when it never dies. Dollar-native: `eq` is a cumulative SUM and `cap` an absolute
    dollar distance from the running peak (D542).
    """
    if cap <= 0:
        raise ValueError("cap must be a positive dollar amount")
    lives, eq, peak, start = [], 0.0, 0.0, 0
    for i, x in enumerate(d):
        eq += x
        peak = max(peak, eq)
        if peak - eq >= cap:
            lives.append((start, i, i - start + 1))
            eq, peak, start = 0.0, 0.0, i + 1
    n_life = [t[2] for t in lives]
    return len(lives), float(np.mean(n_life)) if lives else 0.0, lives


def _life_with_p3(d: np.ndarray, trail_dd: float, p3_cap: float) -> list[int]:
    """D503's second walker: a death on EITHER the trailing drawdown OR a P3 breach."""
    lives, eq, peak, start = [], 0.0, 0.0, 0
    for i, x in enumerate(d):
        eq += x
        peak = max(peak, eq)
        if peak - eq >= trail_dd or x <= -p3_cap:
            lives.append(i - start + 1)
            eq, peak, start = 0.0, 0.0, i + 1
    return lives


def recurrence_years(n_events: int, n_sessions: int) -> float:
    """Mean sessions between events, in years of 252. inf when never seen (d501's)."""
    if n_events <= 0:
        return float("inf")
    return (n_sessions / n_events) / TRADING_DAYS


def p_at_least_one(n_events: int, n_sessions: int, horizon: int) -> float:
    """P(>=1 event in `horizon` sessions) at the empirical per-session rate (d501's)."""
    if n_sessions <= 0:
        raise ValueError("no sessions")
    rate = n_events / n_sessions
    return float(1.0 - (1.0 - rate) ** horizon)


def p3(d_usd: Sequence[float] | np.ndarray, account: float = ACCOUNT_DEFAULT) -> dict:
    """R11 P3 as amended 2026-09-13: a RATE (P3a), a life cost (P3b), a reported worst day (P3c).

    P3a  days beyond 2% of the account, annualised over the window       bar <= 1.0 / yr
    P3b  1 - E[life | drawdown OR P3 breach] / E[life | drawdown alone]  bar <= 0.33
    P3c  the worst day, in dollars, in daily sigma, and as a share of the account's
         WHOLE 4% loss budget. Reported. No longer a gate.
    """
    x = np.asarray(d_usd, dtype=float)
    if x.size < 2:
        raise ValueError(f"p3 needs at least 2 sessions, got {x.size}")
    if not np.isfinite(x).all():
        raise ValueError("p3: series holds a non-finite value")
    if not (account > 0) or not math.isfinite(account):
        raise ValueError(f"p3: account must be a positive dollar amount, got {account!r}")
    trail_dd = DD_FRACTION * account
    p3_cap = P3_CAP_FRACTION * account
    n = int(x.size)
    sd = float(x.std(ddof=1))
    n_br = int((x <= -p3_cap).sum())
    p3a = n_br / n * TRADING_DAYS
    nd_dd, life_dd, _ = max_drawdown_life(x, trail_dd)
    lives2 = _life_with_p3(x, trail_dd, p3_cap)
    life_both = float(np.mean(lives2)) if lives2 else 0.0
    p3b = (1.0 - life_both / life_dd) if life_dd > 0 else float("nan")
    return {
        "account_usd": float(account),
        "p3_cap_usd": p3_cap,
        "trailing_dd_usd": trail_dd,
        "n_sessions": n,
        "p3a_breaches": n_br,
        "p3a_breaches_per_year": p3a,
        "p3a_bar": P3A_BAR,
        "p3a_pass": bool(p3a <= P3A_BAR),
        "p3a_recurrence_years": recurrence_years(n_br, n),
        "p3b_life_cost": p3b,
        "p3b_bar": P3B_BAR,
        "p3b_pass": bool(np.isfinite(p3b) and p3b <= P3B_BAR),
        "p3c_worst_day_usd": float(x.min()),
        "p3c_in_sigma": float(x.min() / sd) if sd > 0 else float("nan"),
        "p3c_share_of_loss_budget": float(-x.min() / trail_dd),
        "life_dd_only_sessions": life_dd,
        "life_with_p3_sessions": life_both,
        "deaths_dd_only": nd_dd,
        "deaths_with_p3": len(lives2),
        "p_breach_in_252": p_at_least_one(n_br, n, TRADING_DAYS),
        "daily_sigma_usd": sd,
    }


# ---------------------------------------------------------------- P4, the account's life


def expected_profit_before_breach(sharpe: float, sigma_frac: float,
                                  D: float = DD_FRACTION) -> tuple[float, float]:
    """(expected profit, expected life in days) in ACCOUNT-FRACTION units.

    Verbatim `scripts/d496_book_sharpe_bar.expected_profit_before_breach`. **`sigma_frac`
    and `D` are FRACTIONS of the account, not dollars.** Reach it through
    `expected_profit_before_breach_usd` unless reproducing D496/D503 exactly.
    """
    if sigma_frac <= 0:
        return float("nan"), float("nan")
    mu = sigma_frac * sharpe / np.sqrt(TRADING_DAYS)
    if abs(mu) < 1e-15:
        return 0.0, (D / sigma_frac) ** 2            # driftless limit
    theta = 2.0 * mu / sigma_frac ** 2
    e_max = (sigma_frac ** 2 / (2.0 * mu)) * (np.expm1(theta * D))
    profit = e_max - D
    return float(profit), float(profit / mu)


def expected_profit_before_breach_usd(sharpe: float, sigma_usd: float,
                                      account: float = ACCOUNT_DEFAULT,
                                      dd_usd: float | None = None) -> tuple[float, float]:
    """The same Brownian barrier, in DOLLARS, with the unit boundary asserted.

    This wrapper exists because feeding dollars to `expected_profit_before_breach`
    crashed D503's first run. It converts, and it refuses the two shapes that slip cannot
    take: a daily sigma at or above the whole account (dollars where a fraction belongs),
    and a daily sigma below `MIN_SIGMA_FRAC` of it (a FRACTION where dollars belong).

    `MIN_SIGMA_FRAC = 1e-5` is $0.50 a day on a $50,000 account. Every instrument these
    venues offer has a tick worth $0.25 or more, so a series with any activity at all
    cannot have a daily sigma below it, and a fraction passed by mistake always is.
    """
    if not (account > 0) or not math.isfinite(account):
        raise ValueError(f"account must be a positive dollar amount, got {account!r}")
    if not math.isfinite(sigma_usd) or sigma_usd <= 0:
        raise ValueError(f"sigma_usd must be a positive dollar amount, got {sigma_usd!r}")
    dd = DD_FRACTION * account if dd_usd is None else dd_usd
    if not (0 < dd <= account):
        raise ValueError(f"dd_usd {dd!r} must be a dollar amount in (0, account={account}]")
    sigma_frac = sigma_usd / account
    if not (MIN_SIGMA_FRAC <= sigma_frac < 1.0):
        raise ValueError(
            f"sigma_usd/account = {sigma_frac!r}, outside [{MIN_SIGMA_FRAC}, 1): a DAILY "
            f"sigma of {sigma_usd} on a {account} account is not a daily sigma. Pass "
            f"DOLLARS here and FRACTIONS to expected_profit_before_breach -- the slip "
            f"that crashed D503's first run")
    if not math.isfinite(sharpe):
        raise ValueError(f"sharpe must be finite, got {sharpe!r}")
    profit, life = expected_profit_before_breach(sharpe, sigma_frac, dd / account)
    return profit * account, life


def sigma_series(r: np.ndarray) -> np.ndarray:
    """Trailing std over the PRIOR `VOL_WINDOW` observations only (d440's, verbatim).

    Index t uses r[t-21:t] and never r[t]; D440's lag audit re-derives this independently.
    """
    n = len(r)
    out = np.full(n, np.nan)
    for t in range(VOL_WINDOW, n):
        out[t] = r[t - VOL_WINDOW:t].std(ddof=1)
    return out


def notional_series(r: np.ndarray, target_dollar_vol: float, rule: str) -> np.ndarray:
    """Notional per observation so the dollar vol hits `target_dollar_vol` (d440's, verbatim)."""
    if rule not in ("static", "voltgt"):
        raise ValueError(f"rule must be 'static' or 'voltgt', got {rule!r}")
    sig_full = r.std(ddof=1)
    if not (sig_full > 0.0):
        return np.zeros(len(r))
    base = target_dollar_vol / sig_full
    if rule == "static":
        return np.full(len(r), base)
    sig = sigma_series(r)
    n = np.where(np.isnan(sig), base, target_dollar_vol / np.maximum(sig, 1e-12))
    return np.minimum(n, VOL_CAP * base)


def gauss_provider(mu_daily: float, sd_daily: float, k: int) -> Callable:
    """d386's own increment, verbatim (d440's `make_gauss_provider`). Dollars per day."""
    sd = sd_daily / math.sqrt(k)
    dmu = mu_daily / k

    def provider(_day: int, live_idx: np.ndarray, rng) -> tuple:
        inc = rng.normal(dmu, sd, size=(len(live_idx), k))
        cum = np.cumsum(inc, axis=1)
        return cum.min(1), cum.max(1), cum[:, -1]

    return provider


def measured_provider(d_end: np.ndarray, d_low: np.ndarray, d_high: np.ndarray, *,
                      target_dollar_vol: float | None, rule: str, n_paths: int,
                      shuffle: bool, seed: int) -> Callable:
    """d440's `make_measured_provider`, taking arrays instead of a DataFrame.

    `target_dollar_vol=None` means the three arrays are ALREADY DOLLARS at the traded
    size and no notional scaling happens (`rule` must then be "static"). A dollar amount
    means they are RETURNS and are scaled by `notional_series`, which is the path that
    reproduces D440.
    """
    r = np.asarray(d_end, dtype=float)
    lo = np.asarray(d_low, dtype=float)
    hi = np.asarray(d_high, dtype=float)
    if not (r.shape == lo.shape == hi.shape) or r.ndim != 1:
        raise ValueError(f"d_end/d_low/d_high must be one-dimensional and equal in length, "
                         f"got {r.shape}, {lo.shape}, {hi.shape}")
    if r.size == 0:
        raise ValueError("measured_provider: empty series")
    if (lo > 0.0).any() or (hi < 0.0).any():
        raise ValueError("measured_provider: d_low must be <= 0 and d_high >= 0 (both are "
                         "measured RELATIVE to the day's start)")
    if ((r < lo - 1e-9) | (r > hi + 1e-9)).any():
        raise ValueError("measured_provider: d_end lies outside [d_low, d_high]")
    if target_dollar_vol is None:
        if rule != "static":
            raise ValueError("measured_provider: a dollar series cannot be vol-targeted "
                             "here -- rule must be 'static' when target_dollar_vol is None")
        N = np.ones(r.size)
    else:
        if not (target_dollar_vol > 0) or not math.isfinite(target_dollar_vol):
            raise ValueError(f"target_dollar_vol must be a positive dollar amount, "
                             f"got {target_dollar_vol!r}")
        N = notional_series(r, target_dollar_vol, rule)
    LO, HI, EN = lo * N, hi * N, r * N
    n = r.size
    rng = np.random.default_rng(seed)
    if shuffle:
        order = rng.integers(0, n, size=(n_paths, 1))
    else:
        order = np.arange(min(n_paths, n)).reshape(-1, 1)

    def provider(day: int, live_idx: np.ndarray, _rng) -> tuple:
        if shuffle:
            j = rng.integers(0, n, size=len(live_idx))
        else:
            j = (order[live_idx, 0] + day) % n
        return LO[j], HI[j], EN[j]

    return provider


def _caps(p: Plan, k: int) -> float:
    return p.caps[k] if k < len(p.caps) else p.caps[-1]


def simulate_provider(p: Plan, provider: Callable, *, n_paths: int = 15_000,
                      days: int = 750, seed: int = 20260908) -> dict:
    """d386's full-lifecycle loop with the daily increment injected (d440's, verbatim).

    `provider(day, live_idx, rng) -> (d_low, d_high, d_end)`, all three in DOLLARS
    relative to the day's start. Everything else — evaluation, funded geometry, the lock
    level, the qualifying-day counter, the consistency rule, the payout ladder, the
    safety net, the post-payout floor and the fee clock — is D386's.
    """
    rng = np.random.default_rng(seed)
    cap_arr = np.asarray(p.caps, dtype=float)
    cap_last = len(p.caps) - 1
    n = n_paths
    bal = np.zeros(n)
    ref = np.zeros(n)
    alive = np.ones(n, bool)
    funded = np.full(n, p.start_funded)
    qual = np.zeros(n, np.int32)
    prof = np.zeros(n)
    best = np.zeros(n)
    npay = np.zeros(n, np.int32)
    paid = np.zeros(n)
    months = np.zeros(n)
    paid_activation = np.zeros(n, bool)
    ever_funded = np.full(n, p.start_funded)
    d_eval = np.zeros(n)
    d_fund = np.zeros(n)

    for d in range(days):
        live = alive
        if not live.any():
            break
        idx = np.flatnonzero(live)
        m = idx.size
        d_fund[live & funded] += 1.0
        d_eval[live & ~funded] += 1.0

        d_low, d_high, d_end = provider(d, idx, rng)

        b = bal[live]
        r = ref[live]
        f = funded[live]
        dd = np.where(f, p.dd_fund, p.dd_eval)
        lock = np.where(f, np.inf if p.lock_fund is None else p.lock_fund,
                        np.inf if p.lock_eval is None else p.lock_eval)
        base = np.where(f, p.fund_start, 0.0)
        r_eff = np.minimum(np.maximum(r, base), lock)
        floor = r_eff - dd
        if p.post_payout_floor is not None:
            floor = np.where(npay[live] > 0, p.post_payout_floor, floor)

        breach = (b + d_low) <= floor

        kind = np.where(f, p.kind_fund, p.kind_eval)
        new_ref = r.copy()
        is_eod = kind == EOD
        is_in = kind == INTRA
        new_ref[is_eod] = np.maximum(r[is_eod], (b + d_end)[is_eod])
        new_ref[is_in] = np.maximum(r[is_in], (b + d_high)[is_in])
        b = b + d_end

        passed = (~f) & (b >= p.target) & (~breach)

        pnl = d_end
        q = qual[live] + ((f & (pnl >= p.qual_threshold)) & (~breach)).astype(np.int32)
        pr = prof[live] + np.where(f & (~breach), pnl, 0.0)
        bd = np.maximum(best[live], np.where(f & (~breach), pnl, 0.0))

        withdrawable = b - (p.fund_start + p.safety_net)
        cap_now = cap_arr[np.minimum(npay[live], cap_last)]
        cons_ok = (np.ones(m, bool) if p.consistency is None
                   else (bd <= p.consistency * np.maximum(pr, 1e-9)))
        eligible = (f & (~breach) & (q >= p.qual_days) & (pr >= p.min_total)
                    & cons_ok & (withdrawable >= p.min_payout))
        amount = np.where(eligible, np.minimum(cap_now, np.maximum(withdrawable, 0.0)), 0.0)
        b = b - amount
        np_new = npay[live] + eligible.astype(np.int32)
        q = np.where(eligible, 0, q)
        pr = np.where(eligible, 0.0, pr)
        bd = np.where(eligible, 0.0, bd)

        closed_out = np_new >= p.max_payouts
        still = (~breach) & (~closed_out)

        bal[idx] = b
        ref[idx] = np.where(passed, p.fund_start, new_ref)
        qual[idx] = q
        prof[idx] = pr
        best[idx] = bd
        npay[idx] = np_new
        paid[idx] += amount
        alive[idx] = still
        newly = passed & still
        bal[idx[newly]] = p.fund_start
        funded[idx[newly]] = True
        ever_funded[idx[newly]] = True
        if p.monthly:
            months[idx[~funded[idx]]] += 1.0 / 21.0
        need_act = idx[newly & (~paid_activation[idx])]
        paid_activation[need_act] = True

    fees = (p.fee_eval * np.maximum(months, 1.0 / 21.0) if p.monthly
            else np.full(n, p.fee_eval)) + p.fee_activation * paid_activation
    v = paid - fees
    breached = ~alive & (npay < p.max_payouts)
    life = d_eval + d_fund
    return {
        "V": float(v.mean()), "V_se": float(v.std(ddof=1) / math.sqrt(n)),
        "paid_mean": float(paid.mean()), "paid_median": float(np.median(paid)),
        "p_paid": float((paid > 0).mean()), "p_pass": float(ever_funded.mean()),
        "fees_mean": float(fees.mean()), "n_payouts_mean": float(npay.mean()),
        "p_alive_at_horizon": float(alive.mean()),
        "p_breached": float(breached.mean()),
        "life_days_mean": float(life.mean()),
        "fund_days_mean": float(d_fund[ever_funded].mean()) if ever_funded.any() else float("nan"),
    }


def p4_life(source: Callable | Sequence[float] | np.ndarray, plan: Plan, *,
            basis: Literal["usd", "return"] = "usd",
            target_dollar_vol: float | None = None, rule: str = "static",
            lows: Sequence[float] | np.ndarray | None = None,
            highs: Sequence[float] | np.ndarray | None = None,
            n_paths: int = 8_000, days: int = 600, seed: int = SEED_D440,
            shuffle: bool = False) -> dict:
    """R11 P4 as restated 2026-09-12: the ACCOUNT'S life, and the profit before breach.

    `source` is either a path provider `(day, live_idx, rng) -> (lo, hi, end)` in dollars,
    or a one-dimensional daily series. For a series, `basis` names the units and IS the
    unit assertion:

      basis="usd"     the values ARE dollars at the traded size. `target_dollar_vol` must
                      be None and `rule` "static" — a dollar series cannot be re-sized here.
      basis="return"  the values are FRACTIONAL returns and `target_dollar_vol` (dollars)
                      is required. This is D440's path and the one that reproduces it.

    `lows`/`highs` are the day's running minimum and maximum relative to its start, in the
    same units. Omitted, they default to `min(x, 0)` and `max(x, 0)` — **the optimistic
    bracket**: a close-only series has no intraday excursion, the venue kills on the
    intraday low, so the life this returns is an UPPER bound. `path_basis` says which.

    R11 P4's binding clause is `expected_profit_usd > account_cost_usd`; the >= 1 year
    life is PREFERRED, not binding, and both flags are returned separately.
    """
    if rule not in ("static", "voltgt"):
        raise ValueError(f"rule must be 'static' or 'voltgt', got {rule!r}")
    if n_paths < 1 or days < 1:
        raise ValueError(f"n_paths and days must be positive, got {n_paths}, {days}")
    if callable(source):
        if lows is not None or highs is not None:
            raise ValueError("p4_life: lows/highs are meaningless beside a provider")
        provider = source
        path_basis = "caller-supplied provider"
        n_obs = None
    else:
        x = np.asarray(source, dtype=float)
        if x.ndim != 1 or x.size < 2:
            raise ValueError(f"p4_life: need a one-dimensional series of at least 2 "
                             f"sessions, got shape {x.shape}")
        if not np.isfinite(x).all():
            raise ValueError("p4_life: series holds a non-finite value")
        if basis == "usd":
            if target_dollar_vol is not None:
                raise ValueError("p4_life: basis='usd' means the series is ALREADY dollars "
                                 "at the traded size; target_dollar_vol must be None")
            if rule != "static":
                raise ValueError("p4_life: basis='usd' cannot be vol-targeted here; "
                                 "rule must be 'static'")
        elif basis == "return":
            if target_dollar_vol is None:
                raise ValueError("p4_life: basis='return' needs target_dollar_vol in "
                                 "DOLLARS, so a fractional series can be sized")
        else:
            raise ValueError(f"basis must be 'usd' or 'return', got {basis!r}")
        if lows is None and highs is None:
            lo = np.minimum(x, 0.0)
            hi = np.maximum(x, 0.0)
            path_basis = ("close-only (OPTIMISTIC): no intraday excursion beyond the "
                          "close, so the life is an upper bound")
        elif lows is None or highs is None:
            raise ValueError("p4_life: give both lows and highs, or neither")
        else:
            lo = np.asarray(lows, dtype=float)
            hi = np.asarray(highs, dtype=float)
            path_basis = "measured intraday path"
        n_obs = int(x.size)
        if not shuffle:
            n_paths = min(n_paths, n_obs)      # d440: distinct starts only
        provider = measured_provider(x, lo, hi, target_dollar_vol=target_dollar_vol,
                                     rule=rule, n_paths=n_paths, shuffle=shuffle, seed=seed)
    out = simulate_provider(plan, provider, n_paths=n_paths, days=days, seed=seed)
    cost = float(plan.fee_eval + plan.fee_activation)
    life_years = out["life_days_mean"] / TRADING_DAYS
    fund_years = out["fund_days_mean"] / TRADING_DAYS
    return {
        "firm": plan.firm, "size": plan.size,
        "path_basis": path_basis, "basis": basis, "rule": rule,
        "n_paths": int(n_paths), "days": int(days), "seed": int(seed),
        "n_observations": n_obs,
        "expected_profit_usd": out["paid_mean"],
        "expected_fees_usd": out["fees_mean"],
        "account_cost_usd": cost,
        "net_per_cycle_usd": out["V"],
        "net_per_cycle_usd_se": out["V_se"],
        "expected_life_days": out["life_days_mean"],
        "expected_life_years": life_years,
        "expected_funded_life_days": out["fund_days_mean"],
        "expected_funded_life_years": fund_years,
        "p_alive": out["p_alive_at_horizon"],
        "p_breached": out["p_breached"],
        "p_paid": out["p_paid"],
        "p_pass": out["p_pass"],
        "n_payouts_mean": out["n_payouts_mean"],
        "P4_binding_profit_exceeds_cost": bool(out["paid_mean"] > cost),
        "P4_preferred_life_years_bar": P4_LIFE_PREFERRED_YEARS,
        "P4_preferred_life_pass": bool(fund_years >= P4_LIFE_PREFERRED_YEARS),
        "note": "R11 P4 restatement 2026-09-12: profit before breach vs the account's "
                "cost is BINDING; the >= 1 year life is PREFERRED, not binding. The "
                "life is the ACCOUNT'S, never 1/(per-hold breach rate) (RULING 2026-09-11)",
    }


# ---------------------------------------------------------------- P5, the haircut


def p5_recognised(daily_usd: Sequence[float] | np.ndarray) -> dict:
    """R11's exact single-day haircut at 30%. Verbatim `d495_agree_confluence.p5_recognised`.

    `recognised = total - max(0, best - 0.30 * total)`. **The R11 header table still says
    40%; 30% is operative** (restatement 2026-09-12, refined the same day). Not a screen:
    nothing is rejected for concentrating profit.
    """
    d = np.asarray(daily_usd, dtype=float)
    total = float(d.sum())
    best = float(d.max()) if len(d) else 0.0
    if total <= 0:
        return {"total_usd": total, "best_day_usd": best, "best_day_share": float("nan"),
                "haircut_usd": 0.0, "recognised_usd": total, "haircut_applies": False}
    excess = max(0.0, best - P5_CAP * total)
    return {"total_usd": total, "best_day_usd": best, "best_day_share": best / total,
            "haircut_usd": excess, "recognised_usd": total - excess,
            "haircut_applies": excess > 0}


# ---------------------------------------------------------------- P6, the venue fact


def p6(venue: str) -> dict:
    """R11 P6: does the venue permit automation at the FUNDED stage? A fact, not a measurement."""
    rec = venue_record(venue)
    a = rec["automation_permitted_funded"]
    return {"venue": venue, "firm": rec["firm"], "size": rec["size"],
            "automation_permitted_funded": bool(a["value"]),
            "p6_pass": bool(a["value"]), "provenance": a["provenance"]}


# ---------------------------------------------------------------- all six


def hurdle_p(d_usd: Sequence[float] | np.ndarray, venue_key: str,
             account: float = ACCOUNT_DEFAULT, *, seed: int = SEED_D440,
             label: str | None = None, exit_times_et: Sequence[str] | None = None,
             n_paths: int = 8_000, days: int = 600,
             run_lifecycle: bool = True) -> dict:
    """All six criteria on one daily dollar series at one venue, in D503's key shape.

    Every key `scripts/d503_forward_book.py:hurdle_p` returns is present and carries the
    same value on the same input, so a D503 figure can be checked against this module
    field by field. Three things are ADDED rather than changed, and each is a correction
    D590 records rather than a silent improvement:

      * `P1_post_sizing_usd_per_year` is D503's — `mean * 252` at the traded size, which
        is NOT post-sizing. `P1_size_multiplier` and `P1_post_sizing_usd_per_year_sized`
        are the sizing R11 P1 actually asks for.
      * `P2_pass` is computed from `exit_times_et` against the venue's own flatten time
        when exits are supplied, and is None when they are not. D503 hard-coded True.
      * `P4_lifecycle_*` is the account's life through the venue's real mechanics
        (D440/D386), beside D503's Brownian `P4_expected_*`.
    """
    x = np.asarray(d_usd, dtype=float)
    if x.size < 2:
        raise ValueError(f"hurdle_p needs at least 2 sessions, got {x.size}")
    if not np.isfinite(x).all():
        raise ValueError("hurdle_p: series holds a non-finite value")
    plan = load_venue(venue_key)
    rec = venue_record(venue_key)
    n = int(x.size)
    mu, sd = float(x.mean()), float(x.std(ddof=1))
    sharpe = mu / sd * np.sqrt(TRADING_DAYS) if sd > 0 else np.nan
    neg = np.minimum(x, 0.0)
    down = math.sqrt(float((neg * neg).sum()) / (n - 1))
    sortino = mu / down * math.sqrt(TRADING_DAYS) if down > 0 else float("nan")

    g3 = p3(x, account)
    if sd > 0 and sharpe > 0:
        ep, ep_life = expected_profit_before_breach_usd(
            float(sharpe), sd, account, DD_FRACTION * account)
    else:
        ep, ep_life = None, None
    h5 = p5_recognised(x)
    g6 = p6(venue_key)
    ft = rec["flatten_time_et"]["value"]
    if exit_times_et is None:
        p2_pass: bool | None = None
        p2_note = (f"not asserted: no exit times supplied. {venue_key}'s flatten time is "
                   f"{ft!r} ET" if ft else
                   f"not asserted, and {venue_key}'s flatten time is UNVERIFIED")
    else:
        p2_pass = p2_flatten(exit_times_et, venue_key)
        p2_note = (f"every exit at or before {ft} ET" if p2_pass
                   else f"an exit falls after {ft} ET")
    try:
        sizing = p1_size(x, DD_FRACTION * account)
    except ValueError as e:
        sizing = {"size_multiplier": None, "post_sizing_usd_per_year": None,
                  "max_trailing_dd_usd": None, "basis": f"unavailable: {e}"}
    out = {
        "label": label if label is not None else venue_key,
        "venue": venue_key,
        "firm": plan.firm,
        "account_usd": float(account),
        "n_sessions": n,
        "mean_usd": mu,
        "daily_sigma_usd": sd,
        "sharpe": float(sharpe) if np.isfinite(sharpe) else float("nan"),
        "sortino": sortino,
        # ---- P1
        "P1_post_sizing_usd_per_year": mu * TRADING_DAYS,
        "P1_max_trailing_dd_usd": sizing["max_trailing_dd_usd"],
        "P1_size_multiplier": sizing["size_multiplier"],
        "P1_post_sizing_usd_per_year_sized": sizing["post_sizing_usd_per_year"],
        "P1_basis": sizing["basis"],
        "P1_note": "D503's P1_post_sizing_usd_per_year is mean*252 at the traded size "
                   "and is NOT post-sizing; the *_sized key is (D590)",
        # ---- P2
        "P2_pass": p2_pass,
        "P2_note": p2_note,
        "P2_flatten_time_et": ft,
        "P2_flatten_provenance": rec["flatten_time_et"]["provenance"],
        # ---- P3
        "P3a_breaches_per_year": g3["p3a_breaches_per_year"],
        "P3a_bar": P3A_BAR,
        "P3a_pass": g3["p3a_pass"],
        "P3a_breaches": g3["p3a_breaches"],
        "P3a_recurrence_years": g3["p3a_recurrence_years"],
        "P3b_life_cost": g3["p3b_life_cost"],
        "P3b_bar": P3B_BAR,
        "P3b_pass": g3["p3b_pass"],
        "P3c_worst_day_usd": g3["p3c_worst_day_usd"],
        "P3c_worst_day_in_sigma": g3["p3c_in_sigma"],
        "P3c_share_of_loss_budget": g3["p3c_share_of_loss_budget"],
        "P3_daily_loss_limit_usd": rec["daily_loss_limit"]["value"],
        "P3_daily_loss_limit_provenance": rec["daily_loss_limit"]["provenance"],
        "life_dd_only_sessions": g3["life_dd_only_sessions"],
        "life_with_P3_sessions": g3["life_with_p3_sessions"],
        "deaths_dd_only": g3["deaths_dd_only"],
        "deaths_with_P3": g3["deaths_with_p3"],
        # ---- P4
        "P4_expected_profit_usd": ep,
        "P4_expected_life_days": ep_life,
        # ---- P5
        "P5_best_day_share": h5["best_day_share"],
        "P5_haircut_usd": h5["haircut_usd"],
        "P5_total_usd": h5["total_usd"],
        "P5_recognised_usd": h5["recognised_usd"],
        "P5_haircut_applies": h5["haircut_applies"],
        "P5_cap": P5_CAP,
        "P5_pass": True,
        "P5_note": "a calculation convention, never a screen (R11 restatement "
                   "2026-09-12). The R11 header table's 40% is stale; 30% is operative",
        # ---- P6
        "P6": g6["provenance"],
        "P6_pass": g6["p6_pass"],
        "p_breach_in_252": g3["p_breach_in_252"],
    }
    if run_lifecycle:
        lc = p4_life(x, plan, basis="usd", n_paths=n_paths, days=days, seed=seed)
        out.update({f"P4_lifecycle_{k}": v for k, v in lc.items()})
    return out


def per_year(d_usd: Sequence[float] | np.ndarray, dates: Sequence[str],
             account: float = ACCOUNT_DEFAULT) -> list[dict]:
    """One row a calendar year. D503/D504's price-level warning made operational.

    Sigma at a fixed micro doubled as NQ's level doubled, so a single window-wide P3c or
    C-d figure describes no year in the window. Every P3 number here is recomputed inside
    the year, and years holding fewer than 2 sessions are reported with NaN statistics
    rather than dropped — a dropped year is a year nobody looked at.
    """
    x = np.asarray(d_usd, dtype=float)
    if len(dates) != x.size:
        raise ValueError(f"{len(dates)} dates against {x.size} sessions")
    if x.size == 0:
        raise ValueError("per_year: empty series")
    yrs = np.array([str(d)[:4] for d in dates])
    rows = []
    for y in sorted(set(yrs.tolist())):
        m = yrs == y
        xi = x[m]
        row: dict[str, Any] = {"year": y, "n_sessions": int(m.sum()),
                               "total_usd": float(xi.sum()),
                               "worst_day_usd": float(xi.min()),
                               "best_day_usd": float(xi.max())}
        if xi.size < 2:
            row.update({"mean_usd": float(xi.mean()), "daily_sigma_usd": float("nan"),
                        "sharpe": float("nan"), "sortino": float("nan"),
                        "p3a_breaches": int((xi <= -P3_CAP_FRACTION * account).sum()),
                        "p3a_breaches_per_year": float("nan"),
                        "p3c_share_of_loss_budget": float(-xi.min() / (DD_FRACTION * account)),
                        "max_trailing_dd_usd": float("nan"),
                        "p1_size_multiplier": float("nan"),
                        "note": "fewer than 2 sessions: no dispersion statistic exists"})
            rows.append(row)
            continue
        g = p3(xi, account)
        sd = g["daily_sigma_usd"]
        mu = float(xi.mean())
        neg = np.minimum(xi, 0.0)
        down = math.sqrt(float((neg * neg).sum()) / (xi.size - 1))
        try:
            sz = p1_size(xi, DD_FRACTION * account)
            mdd, mult = sz["max_trailing_dd_usd"], sz["size_multiplier"]
        except ValueError:
            mdd, mult = float("nan"), float("nan")
        row.update({
            "mean_usd": mu, "daily_sigma_usd": sd,
            "sharpe": mu / sd * math.sqrt(TRADING_DAYS) if sd > 0 else float("nan"),
            "sortino": mu / down * math.sqrt(TRADING_DAYS) if down > 0 else float("nan"),
            "p3a_breaches": g["p3a_breaches"],
            "p3a_breaches_per_year": g["p3a_breaches_per_year"],
            "p3a_pass": g["p3a_pass"],
            "p3c_share_of_loss_budget": g["p3c_share_of_loss_budget"],
            "max_trailing_dd_usd": mdd,
            "p1_size_multiplier": mult,
            "note": "",
        })
        rows.append(row)
    return rows
