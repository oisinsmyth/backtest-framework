"""The LETF close-flow model's Section 4, as algebra (LETF close-flow Phase 3).

`LETF_CLOSE_FLOW_PREREG.md` v1.2 (a read-only deposit document) specifies a handful of closed-form expressions.
Every function here is one of them and nothing else: no fixture is read, nothing is fitted, no strategy return is
computed. The inputs a runner needs are built by `scripts/build_letf_aum.py` (A) and
`scripts/build_letf_phase2.py` (prices, volume, the calendar).

THE FORMULAS (deposit section 4, quoted)
----------------------------------------
4.1   r[t, tau] = P_fut(t, tau) / P_fut(t-1, 16:00) - 1
4.2   dH_i[t, tau] = L_i * (L_i - 1) * A_i[t-1] * r[t, tau]       (USD notional of underlying)
4.3   Q_usd[t, tau] = sum_i dH_i[t, tau];   Q_contracts = Q_usd / (multiplier * P_fut(t, tau))
4.4   V[t] = 20-day trailing mean daily volume, NQ-equivalent (NQ + MNQ/10), days t-20..t-1 only
      sigma_d[t] = 20-day trailing daily return std, days t-20..t-1 only
      q[t, tau] = Q_contracts / V[t];   I[t, tau] = Y * sigma_d[t] * sqrt(|q[t, tau]|) * P_fut(t, tau)
4.5   direction = sign(Q_usd);   active = I >= k * RT_cost_points
Y = 0.7, fixed (D4). Multipliers NQ = 20, ES = 50.

CONVENTIONS THIS MODULE FIXES (the pre-registration states them; each is tested)
-------------------------------------------------------------------------------
- A[t-1] is the value stored for the PRIOR NYSE trading day, never day t's (D2; test 5).
- The trailing windows read strictly before day t, over the days of the series they are given (test 6); fewer than
  20 prior days is an error, never a shorter window.
- sigma_d is the sample standard deviation (ddof = 1) of the 20 prior daily returns.
- A one-minute bar is labelled by its START (Databento `ts_event`, the D462 fixtures): the price AT hh:mm is the close
  of the bar labelled one minute earlier (`bar_label_ending_at`).
"""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd

Y_IMPACT = 0.7
MULTIPLIER = {"NQ": 20.0, "ES": 50.0}
MICRO_PER_FULL = 10.0  # MNQ/MES are one tenth of NQ/ES
TRAILING_DAYS = 20
ET = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")


class LetfModelError(ValueError):
    """An input the model refuses: a look-ahead, a short window, an impossible value."""


def rebalance_flow(L: float, A: float, r: float) -> float:
    """4.2: dH = L (L - 1) A r, USD notional of the underlying. Same sign as r for L = +3 AND L = -3 (multipliers 6
    and 12), which is the whole mechanism: the long and the inverse fund both buy an up day."""
    if not math.isfinite(A) or A < 0:
        raise LetfModelError(f"A must be a finite, non-negative AUM, got {A!r}")
    if not math.isfinite(r):
        raise LetfModelError(f"r must be finite, got {r!r}")
    return L * (L - 1) * A * r


def day_return(p_tau: float, p_prev_close: float) -> float:
    """4.1: the move since the prior NYSE close, both prices of ONE contract."""
    if not (p_tau > 0 and p_prev_close > 0):
        raise LetfModelError(f"prices must be positive, got {p_tau!r} / {p_prev_close!r}")
    return p_tau / p_prev_close - 1.0


def aum_prior(aum: pd.Series, day: str | date, nyse_days: Sequence[str]) -> float:
    """A[t-1]: the stored AUM for the NYSE trading day immediately before `day`, never `day` itself (D2).
    Raises if that day has no stored value (a gap is an error, not a silent step back)."""
    d = str(pd.Timestamp(day).date())
    days = sorted(nyse_days)
    i = pd.Index(days).searchsorted(d)
    if i == 0:
        raise LetfModelError(f"no NYSE day before {d}")
    prev = days[i - 1]
    idx = pd.Index([str(pd.Timestamp(x).date()) for x in aum.index])
    if prev not in idx:
        raise LetfModelError(f"no stored AUM for {prev}, the NYSE day before {d}")
    return float(aum.iloc[idx.get_loc(prev)])


def aggregate_flow(L_by_fund: Mapping[str, float], aum_by_fund: Mapping[str, float], r: float) -> float:
    """4.3: Q_usd = sum over the set's funds of dH. Every fund in `L_by_fund` must have an AUM."""
    missing = set(L_by_fund) - set(aum_by_fund)
    if missing:
        raise LetfModelError(f"no AUM for {sorted(missing)}")
    return float(sum(rebalance_flow(L_by_fund[f], aum_by_fund[f], r) for f in L_by_fund))


def to_contracts(q_usd: float, root: str, price: float) -> float:
    """4.3: Q_contracts = Q_usd / (multiplier x P_fut(t, tau))."""
    if root not in MULTIPLIER:
        raise LetfModelError(f"unknown root {root!r}")
    if not price > 0:
        raise LetfModelError(f"price must be positive, got {price!r}")
    return q_usd / (MULTIPLIER[root] * price)


def _prior(series: pd.Series, day: str | date, n: int) -> pd.Series:
    d = pd.Timestamp(day)
    s = series.copy()
    s.index = pd.to_datetime(s.index)
    s = s.sort_index()
    prior = s[s.index < d]
    if len(prior) < n:
        raise LetfModelError(f"{len(prior)} observations before {d.date()}, {n} required")
    return prior.iloc[-n:]


def trailing_volume(equiv_volume: pd.Series, day: str | date, n: int = TRAILING_DAYS) -> float:
    """4.4: V[t], the mean of the n prior days' NQ-equivalent (or ES-equivalent) volume; day t never enters."""
    return float(_prior(equiv_volume, day, n).mean())


def trailing_sigma(daily_returns: pd.Series, day: str | date, n: int = TRAILING_DAYS) -> float:
    """4.4: sigma_d[t], the sample std (ddof = 1) of the n prior daily returns; day t never enters."""
    return float(_prior(daily_returns, day, n).std(ddof=1))


def equivalent_volume(full: float, micro: float) -> float:
    """4.4: NQ + MNQ/10 (ES + MES/10)."""
    if full < 0 or micro < 0:
        raise LetfModelError("volumes must be non-negative")
    return full + micro / MICRO_PER_FULL


def normalised_flow(q_contracts: float, V: float) -> float:
    """4.4: q = Q_contracts / V."""
    if not V > 0:
        raise LetfModelError(f"V must be positive, got {V!r}")
    return q_contracts / V


def predicted_impact(sigma_d: float, q: float, price: float, Y: float = Y_IMPACT) -> float:
    """4.4: I = Y sigma_d sqrt(|q|) P, index points. Y is fixed at 0.7 (D4): passing any other value raises."""
    if Y != Y_IMPACT:
        raise LetfModelError(f"Y is fixed at {Y_IMPACT} (D4); got {Y!r}")
    if not (sigma_d >= 0 and price > 0):
        raise LetfModelError("sigma_d must be non-negative and price positive")
    return Y * sigma_d * math.sqrt(abs(q)) * price


def direction(q_usd: float) -> int:
    """4.5: sign(Q_usd); zero flow gives no direction."""
    return (q_usd > 0) - (q_usd < 0)


def is_active(impact_points: float, k: float, rt_cost_points: float) -> bool:
    """4.5: I >= k x the round-trip cost in index points."""
    if not rt_cost_points > 0:
        raise LetfModelError(f"the round-trip cost must be positive, got {rt_cost_points!r}")
    return impact_points >= k * rt_cost_points


def et_to_utc(day: str | date, hhmm: str) -> datetime:
    """An America/New_York wall-clock time on `day` as UTC, DST-aware (deposit s.3.3; test 8)."""
    d = pd.Timestamp(day)
    h, m = (int(x) for x in hhmm.split(":"))
    return datetime(d.year, d.month, d.day, h, m, tzinfo=ET).astimezone(UTC)


def bar_label_ending_at(hhmm: str) -> str:
    """The label of the one-minute bar that ENDS at hh:mm (bars are labelled by their start): the price at 15:00 is
    the close of the 14:59 bar; the 16:00 close is the 15:59 bar's."""
    h, m = (int(x) for x in hhmm.split(":"))
    t = datetime(2000, 1, 1, h, m) - timedelta(minutes=1)
    return t.strftime("%H:%M")


def trade_days(sessions: pd.DataFrame) -> list[str]:
    """The trade calendar: sessions not excluded (early closes, NYSE-closed days; s.3.4, test 9). `sessions` is the
    Phase 2 table (`day`, `excluded`, `is_early_close`); a session flagged early-close that is NOT marked excluded is
    refused, so the exclusion cannot be bypassed by a table built another way."""
    need = {"day", "excluded", "is_early_close"}
    if need - set(sessions.columns):
        raise LetfModelError(f"sessions table lacks {sorted(need - set(sessions.columns))}")
    leak = sessions[sessions["is_early_close"].astype(bool) & ~sessions["excluded"].astype(bool)]
    if len(leak):
        raise LetfModelError(f"early-close sessions not excluded: {leak['day'].tolist()[:5]}")
    return sessions.loc[~sessions["excluded"].astype(bool), "day"].astype(str).tolist()
