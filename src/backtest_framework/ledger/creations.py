"""Creations, the execution-day lag, the hedged fraction, and the window split (D611).

WHAT THIS IS
------------
`SETTLEMENT_FLOW_LEDGER_PREREG.md` P3.4 and P3.5 (lines 215-237), which is the participant
the whole premium model exists to feed. The mechanism, lines 173-179, verbatim::

    **Mechanism (sequence on a creation day):**
    1. Retail buys ETF shares. The ETF market maker sells them and is left short the ETF.
    2. The market maker hedges by buying futures **intraday** (hedged fraction h).
    3. At execution, the market maker creates shares via the authorised participant. The
       fund invests the new cash in futures at Lx exposure.
    4. The market maker sells its hedge futures at the same time.

    Steps 3 and 4 net out for the hedged fraction. Only **(1 - h)** of the creation flow
    lands in the settlement window as net flow. Redemptions mirror this. For inverse funds,
    the sign follows L.

THE FORMULAS, QUOTED
--------------------
P3.4 line 217::

    Target: `dCreate_f[t] = (shares_out[t] - shares_out[t-1]) x NAV_f[t]` (USD, point-in-time,
    respecting `published_at` and Q11).

P3.4 line 226, the execution day::

    **Execution day:** if `lag_c = 0`, the creation flow is transacted today and the model
    forecasts it. If `lag_c = 1`, today's fund purchase comes from yesterday's orders and is
    taken as known (`Q3_known`), while C2 forecasts tomorrow's. Which date `shares_out`
    reflects is resolved by Q11.

P3.5 "Hedging split", lines 231-237::

    Create_flow = L_f x dCreate_f / (multiplier x P_held)   (fund futures trade on execution day)
    h           = 1 / (1 + exp(-(h0 - h1 x stress)))        (h1 >= 0: more stress -> less hedged)
    Q3_window   = (1 - h) x Create_flow                     (enters the ledger)
    Q3_intraday = h x Create_flow                           (already executed intraday; only
                                                             visible via the update step)

    `h0, h1` are fitted in Stage C2 against realised window flow (decision D11).

P3.7 line 271, the attention term, and Section 8 line 472, the constraints::

    - **Hedging split:** replace `stress` with `stress + g1 x att_accel` in the h function
      (g1 >= 0). Viral surges are when market makers are most likely to fall behind.

    - Constraints: p, n, n9 in [0, 1]; R > 0; h1 >= 0; g1 >= 0.

WHERE THE SIGN COMES FROM, AND WHY IT IS WORTH A PARAGRAPH
-----------------------------------------------------------
`Create_flow` takes its sign from `L x dCreate`, and required unit test 19 is the case that
makes it non-obvious: a KOLD CREATION -- new money into a -2x fund -- makes the fund SELL
futures, so the flow is negative even though the share count went up. The sign is carried by
`L`, never by `dCreate`, and the four cases (creation and redemption on a long and on an
inverse fund) are all asserted rather than the two that read naturally.

WHAT IS NOT HERE
----------------
No fitting. `h0`, `h1`, `g1`, `a0..a3` and `b1..b4` are Stage C2/C3 parameters estimated in
walk-forward training windows against realised window flow (Section 8, decision D11), and
neither the flow nor the fund panel exists on disk. This module evaluates the functions those
parameters go into; it has no opinion on their values and supplies no defaults for them.
"""

from __future__ import annotations

import math

from .funds import FundModelError

__all__ = [
    "CreationError",
    "create_flow",
    "creation_term",
    "delta_create",
    "hedged_fraction",
    "split",
]


class CreationError(FundModelError):
    """A creation-model input was impossible, or the logistic saturated at its own boundary."""


def delta_create(shares_out: float, shares_prev: float, nav: float) -> float:
    """P3.4 line 217: `dCreate_f[t] = (shares_out[t] - shares_out[t-1]) x NAV_f[t]`, in USD.

    Positive is a creation (shares outstanding rose), negative a redemption. `nav` is day
    `t`'s NAV per share, as the line writes it -- not `t-1`'s, which is the one `inav` uses.
    """
    for label, value in (
        ("shares_out", shares_out),
        ("shares_prev", shares_prev),
        ("nav", nav),
    ):
        if not math.isfinite(value):
            raise CreationError(f"delta_create: {label} must be finite, got {value!r}")
    if shares_out < 0.0 or shares_prev < 0.0:
        raise CreationError(
            f"delta_create: share counts must be non-negative, got {shares_out!r} and "
            f"{shares_prev!r}"
        )
    if nav <= 0.0:
        raise CreationError(
            f"delta_create: NAV must be positive, got {nav!r}. A zero NAV reports every "
            f"creation as no flow at all."
        )
    return (shares_out - shares_prev) * nav


def creation_term(lag_c: int, realised_prev: float | None, forecast: float | None) -> float:
    """Line 226: which of the two numbers the ledger carries today.

    `lag_c = 1`  -> `Q3_known`, yesterday's orders executing today, so the REALISED share
                    change from t-1 is used and the forecast is not consulted at all.
    `lag_c = 0`  -> the creation is transacted today and the model forecasts it.

    Required unit test 4 is both halves, and the halves are exclusive: at `lag_c = 1` a
    forecast may be supplied and is ignored (C2 is forecasting TOMORROW's, which is a
    different day's term), and at `lag_c = 0` there is no realised number to use.

    `lag_c` is a Section 3.2 fund fact per fund; any value other than 0 or 1 raises rather
    than falling through to a default, because a fund whose cut-off has not been sourced must
    stop the ledger rather than quietly take somebody else's lag.
    """
    if not isinstance(lag_c, int) or isinstance(lag_c, bool):
        raise CreationError(f"creation_term: lag_c must be an int, got {lag_c!r}")
    if lag_c == 1:
        if realised_prev is None:
            raise CreationError(
                "creation_term: lag_c = 1 takes today's purchase from YESTERDAY's orders "
                "(Q3_known, line 226) and realised_prev is None. There is nothing known to "
                "use, and substituting the forecast would silently make this lag_c = 0."
            )
        if not math.isfinite(realised_prev):
            raise CreationError(f"creation_term: realised_prev must be finite, got {realised_prev!r}")
        return realised_prev
    if lag_c == 0:
        if forecast is None:
            raise CreationError(
                "creation_term: lag_c = 0 forecasts today's creation (line 226) and forecast "
                "is None."
            )
        if not math.isfinite(forecast):
            raise CreationError(f"creation_term: forecast must be finite, got {forecast!r}")
        return forecast
    raise CreationError(
        f"creation_term: lag_c = {lag_c!r}. Section 3.2 defines the lag parameter as "
        f"`lag_c` in {{0, 1}} and nothing else is a described execution timing."
    )


def hedged_fraction(
    h0: float,
    h1: float,
    stress: float,
    *,
    g1: float = 0.0,
    att_accel: float = 0.0,
) -> float:
    """P3.5 line 232 with P3.7 line 271's attention term:

        h = 1 / (1 + exp(-(h0 - h1 x (stress + g1 x att_accel))))

    `h1 >= 0` and `g1 >= 0` are Section 8 line 472's constraints and are ENFORCED here, not
    assumed: line 232's own gloss is "h1 >= 0: more stress -> less hedged", and a negative h1
    inverts the mechanism -- more stress, MORE hedged, less flow in the window -- which would
    read as a fitted result rather than as a sign error.

    The logistic is evaluated in the numerically stable branch (`exp(-x)` for `x >= 0`,
    `exp(x)/(1+exp(x))` below) so that a large magnitude `x` underflows toward the right
    boundary instead of overflowing. A result that has REACHED 0.0 or 1.0 raises: h is in the
    OPEN interval mathematically (required unit test 18), doubles saturate at about
    |x| = 37, and an h of exactly 1.0 would send the entire creation flow intraday on an
    arithmetic artefact.
    """
    for label, value in (
        ("h0", h0),
        ("h1", h1),
        ("stress", stress),
        ("g1", g1),
        ("att_accel", att_accel),
    ):
        if not math.isfinite(value):
            raise CreationError(f"hedged_fraction: {label} must be finite, got {value!r}")
    if h1 < 0.0:
        raise CreationError(
            f"hedged_fraction: h1 = {h1!r} violates Section 8 line 472's constraint h1 >= 0. "
            f"Line 232 reads it as 'more stress -> less hedged'; a negative h1 is the "
            f"opposite mechanism wearing a fitted coefficient."
        )
    if g1 < 0.0:
        raise CreationError(
            f"hedged_fraction: g1 = {g1!r} violates line 472's constraint g1 >= 0 (P3.7 line "
            f"271: viral surges are when market makers are most likely to fall behind)."
        )
    x = h0 - h1 * (stress + g1 * att_accel)
    if x >= 0.0:
        h = 1.0 / (1.0 + math.exp(-x))
    else:
        e = math.exp(x)
        h = e / (1.0 + e)
    if not 0.0 < h < 1.0:
        raise CreationError(
            f"hedged_fraction: the logistic saturated to {h!r} at x = {x!r}. h is in the OPEN "
            f"interval (0, 1) and a double reaches the boundary near |x| = 37; at h = 1.0 the "
            f"whole creation flow is declared already hedged intraday, and at h = 0.0 all of "
            f"it is declared to land in the window. Neither is a measurement."
        )
    return h


def create_flow(L: int, delta_create_usd: float, multiplier: float, p_held: float) -> float:
    """P3.5 line 231: `Create_flow = L_f x dCreate_f / (multiplier x P_held)`.

    In CONTRACTS of the held month, signed, positive = buy. `multiplier` is the contract size
    in units per point (10,000 MMBtu for NG, 1,000 bbl for CL -- `ledger/funds.py`), and
    `p_held` is the held contract's price, so `multiplier x P_held` is one contract's
    notional in USD.
    """
    if not isinstance(L, int) or isinstance(L, bool):
        raise CreationError(f"create_flow: L must be an int, got {L!r}")
    if L == 0:
        raise CreationError("create_flow: L = 0 is not a fund")
    for label, value in (
        ("delta_create_usd", delta_create_usd),
        ("multiplier", multiplier),
        ("p_held", p_held),
    ):
        if not math.isfinite(value):
            raise CreationError(f"create_flow: {label} must be finite, got {value!r}")
    if multiplier <= 0.0:
        raise CreationError(f"create_flow: multiplier must be positive, got {multiplier!r}")
    if p_held <= 0.0:
        raise CreationError(
            f"create_flow: p_held = {p_held!r}. A non-positive held price inverts the sign of "
            f"the flow, and CL has printed a negative settlement once (2020-04-20): the "
            f"contract conversion is undefined there and this refuses rather than returning a "
            f"backwards contract count."
        )
    return L * delta_create_usd / (multiplier * p_held)


def split(h: float, flow: float) -> tuple[float, float]:
    """P3.5 lines 233-234: `Q3_window = (1 - h) x Create_flow`, `Q3_intraday = h x Create_flow`.

    Returned in that order, in contracts, both signed the same way as `flow`.

    The two legs are computed as the document writes them -- `(1 - h) * flow` and
    `h * flow`, not one of them as the residual of the other -- so their sum reconstructs
    `flow` to within one rounding rather than exactly. The residual form would be exact and
    would not be this formula; the error is bounded by an ulp of `flow` and the golden states
    it rather than the tests hiding it behind a tolerance nobody chose.
    """
    if not math.isfinite(h) or not 0.0 < h < 1.0:
        raise CreationError(
            f"split: h = {h!r} is not in the open interval (0, 1). Use hedged_fraction, which "
            f"is where that interval is enforced."
        )
    if not math.isfinite(flow):
        raise CreationError(f"split: flow must be finite, got {flow!r}")
    return (1.0 - h) * flow, h * flow
