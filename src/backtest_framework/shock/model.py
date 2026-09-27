"""The information-vs-liquidity shock classifier's sections 4-5, as functions (shock classifier Phase 2).

`SHOCK_CLASSIFIER_PREREG.md` v1.2 (read-only deposit), with SC-A1..A7 (`docs/internal/SHOCK_CLASSIFIER_AMENDMENTS.md`).
No fixture is read here and no forward return is computed: the inputs are minute price grids built by
`scripts/build_shock_phase2.py`.

THE DEFINITIONS (deposit, quoted)
---------------------------------
4.1  sigma_tod[t, m] = 1.4826 x median(|r_1m| at minute m over sessions t-60 ... t-1)
4.2  r_w[b] = P[b] / P[b - w] - 1;  thresh_w = z x sigma_tod[t, m(b)] x sqrt(w);  shock if |r_w[b]| > thresh_w;
     t0 = close of bar b; d = sign(r_w[b]); S = |P[b] - P[b - w]|; cooldown 60 min; both windows at one bar -> once,
     labelled with the shorter window
4.3  beta[t], rho[t] = OLS beta and correlation of peer 1-min returns on traded 1-min returns, session-window bars
     from days t-60 ... t-1; a peer is valid if |rho| >= 0.3
4.4  C_j = r_peer_j,w / (beta_j x r_own,w);  C = median over valid peers;  >= 2 valid peers or the class is NONE
4.5  event = t0 within [release - 1 min, release + 5 min]
4.6  INFO if C >= c_hi, or (event and C >= 0.3);  LIQ if C <= c_lo and not event;  NONE otherwise (0.6 / 0.2 primary)
4.7  INFO -> +d (continuation);  LIQ -> -d (reversion)
5.1  stress fill = the WORST close among bars t0+1 ... t0+5 for the trade direction
5.3  a bar that spans both the stop and the target records the STOP
"""
from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

MAD_SCALE = 1.4826
LOOKBACK_SESSIONS = 60
COOLDOWN_MIN = 60
VALID_RHO = 0.3
MIN_PEERS = 2
EVENT_OVERRIDE_C = 0.3
EVENT_BEFORE_MIN, EVENT_AFTER_MIN = 1, 5
C_HI, C_LO, Z = 0.6, 0.2, 4.0
ET, UTC = ZoneInfo("America/New_York"), ZoneInfo("UTC")
WINDOWS = {"NQ": ("09:35", "14:55"), "ES": ("09:35", "14:55"), "CL": ("09:05", "13:25"), "GC": ("08:25", "12:25")}


class ShockModelError(ValueError):
    pass


def sigma_tod(abs_r1: pd.DataFrame) -> pd.DataFrame:
    """4.1 on a (session x minute) matrix of |r_1m|: row t is 1.4826 x the median of rows t-60 ... t-1 per column.
    Day t never enters its own row; the first 60 rows are NaN."""
    return MAD_SCALE * abs_r1.rolling(LOOKBACK_SESSIONS, min_periods=LOOKBACK_SESSIONS).median().shift(1)


def detect(prices: np.ndarray, minutes: Sequence[str], sig: np.ndarray, window: tuple[str, str], z: float = Z,
           windows: Sequence[int] = (1, 3)) -> list[dict]:
    """4.2 over one session. `prices[i]` is the close of the bar labelled `minutes[i]`; `sig[i]` the day's sigma_tod
    for that minute's 1-minute return. Detection runs on bars inside `window`; the cooldown is 60 minutes after t0;
    a bar where both windows fire is recorded once with the shorter window."""
    mins = list(minutes)
    lo, hi = window
    out: list[dict] = []
    block_until = -1
    for i, m in enumerate(mins):
        if not (lo <= m <= hi) or i <= block_until:
            continue
        hit = None
        for w in sorted(windows):
            if i - w < 0 or not (np.isfinite(prices[i]) and np.isfinite(prices[i - w]) and np.isfinite(sig[i])):
                continue
            r = prices[i] / prices[i - w] - 1
            if abs(r) > z * sig[i] * math.sqrt(w):
                hit = {"i": i, "minute": m, "w": w, "r": float(r), "d": int(np.sign(r)),
                       "S": float(abs(prices[i] - prices[i - w])), "thresh": float(z * sig[i] * math.sqrt(w))}
                break  # the shorter window wins
        if hit:
            out.append(hit)
            block_until = i + COOLDOWN_MIN  # bars are one minute apart within a session
    return out


def beta_rho(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """4.3: OLS beta of peer returns y on traded returns x, and their correlation."""
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    if len(x) < 3 or x.var() == 0 or y.var() == 0:
        return float("nan"), float("nan")
    cxy = float(((x - x.mean()) * (y - y.mean())).mean())
    return cxy / float(x.var()), cxy / math.sqrt(float(x.var()) * float(y.var()))


def rolling_beta_rho(daily_sums: pd.DataFrame) -> pd.DataFrame:
    """4.3 over sessions from per-day sums (n, sx, sy, sxx, syy, sxy): day t's beta and rho use days t-60 ... t-1."""
    s = daily_sums.rolling(LOOKBACK_SESSIONS, min_periods=LOOKBACK_SESSIONS).sum().shift(1)
    n = s["n"]
    cxy = s["sxy"] / n - s["sx"] * s["sy"] / n ** 2
    vx = s["sxx"] / n - (s["sx"] / n) ** 2
    vy = s["syy"] / n - (s["sy"] / n) ** 2
    return pd.DataFrame({"beta": cxy / vx, "rho": cxy / np.sqrt(vx * vy)}, index=daily_sums.index)


def confirmation(r_own: float, peers: Sequence[tuple[float, float, float]]) -> tuple[float, int]:
    """4.4: peers as (r_peer_w, beta, rho). Returns (C, number of valid peers); C is NaN below two valid peers."""
    cj = [rp / (b * r_own) for rp, b, rho in peers
          if np.isfinite(rp) and np.isfinite(b) and np.isfinite(rho) and abs(rho) >= VALID_RHO and b != 0 and r_own != 0]
    if len(cj) < MIN_PEERS:
        return float("nan"), len(cj)
    return float(np.median(cj)), len(cj)


def event_flag(t0: datetime, releases: Sequence[datetime]) -> bool:
    """4.5: t0 in [release - 1 min, release + 5 min], inclusive at both ends."""
    return any(r - timedelta(minutes=EVENT_BEFORE_MIN) <= t0 <= r + timedelta(minutes=EVENT_AFTER_MIN) for r in releases)


def classify(C: float, event: bool, c_hi: float = C_HI, c_lo: float = C_LO) -> str:
    """4.6. A NaN C (fewer than two valid peers) is NONE."""
    if not np.isfinite(C):
        return "NONE"
    if C >= c_hi or (event and C >= EVENT_OVERRIDE_C):
        return "INFO"
    if C <= c_lo and not event:
        return "LIQ"
    return "NONE"


def trade_direction(cls: str, d: int) -> int:
    """4.7: INFO follows the shock, LIQ opposes it, NONE does not trade."""
    return {"INFO": d, "LIQ": -d}.get(cls, 0)


def stress_fill(closes_t1_to_t5: Sequence[float], direction: int) -> float:
    """5.1: the worst close among bars t0+1 ... t0+5 for the trade: the highest for a buy, the lowest for a sell."""
    c = [x for x in closes_t1_to_t5 if np.isfinite(x)]
    if not c or direction not in (1, -1):
        raise ShockModelError("a stress fill needs closes and a direction of +1 or -1")
    return max(c) if direction == 1 else min(c)


def bar_exit(high: float, low: float, stop: float, target: float, direction: int) -> str | None:
    """5.3's intra-bar rule: a bar that reaches both the stop and the target records the STOP (pessimistic)."""
    if direction == 1:
        hit_stop, hit_target = low <= stop, high >= target
    elif direction == -1:
        hit_stop, hit_target = high >= stop, low <= target
    else:
        raise ShockModelError("direction must be +1 or -1")
    if hit_stop:
        return "stop"
    return "target" if hit_target else None


def in_window(root: str, minute: str) -> bool:
    lo, hi = WINDOWS[root]
    return lo <= minute <= hi


def eligible_session(day: str, roll_days: set[str], usable: set[str]) -> bool:
    """3.2 / SC-A6: shocks are detected only on usable sessions that are not roll days."""
    return day in usable and day not in roll_days


def et_to_utc(day: str, hhmm: str) -> datetime:
    d = pd.Timestamp(day)
    h, m = (int(x) for x in hhmm.split(":"))
    return datetime(d.year, d.month, d.day, h, m, tzinfo=ET).astimezone(UTC)
