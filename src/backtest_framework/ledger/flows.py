"""Section 4 of the settlement flow ledger: the participant flow terms (D610).

WHAT THIS IS AND WHY IT EXISTS BEFORE ANY DATA
----------------------------------------------
`SETTLEMENT_FLOW_LEDGER_PREREG.md` (v1.9, an untracked read-only deposit document) is a
pre-registration whose core is a handful of closed-form expressions: a leveraged fund's
required rebalance, its split between futures and swap routes, a scalar Kalman update, a
roll's two legs, a one-parameter constrained regression. **None of it existed in this
repository.** `costs/futures_impact.py` (D604) implements Sections 5.3 and 8A.4 and nothing
else did; `scripts/power_table.py`'s string `"A: P1 rebalance"` is a stage LABEL in a
planning table, not an implementation of P1.

Every function here is that algebra and nothing else. It reads no fixture, fits nothing,
and computes no strategy return. The tests are hand calculations because the arithmetic is
small enough to check with a pen, and a hand calculation is the only ground truth available
before a single day of fund holdings is on disk.

THE FORMULAS, QUOTED VERBATIM
-----------------------------
Section 4, line 143::

    All flows are in **contracts of the traded contract month**, signed (+ = buy). For day t
    and evaluation time tau:

line 146::

    r[t, tau] = P_held(t, tau) / Settle_held(t-1) - 1

line 151::

    The ledger uses **r[t, tau] as the forecast of the settlement-to-settlement return** (a
    martingale assumption, decision D3).

P1, line 156::

    Q1 = Sum_funds AUM[t-1] x L x (L - 1) x r[t, tau] x f_fut[t-1] / (multiplier x P_held)

P1, line 160::

    Variance term `var_Q1` comes from uncertainty in the final return between tau and
    settlement: `(AUM x L(L-1) x f_fut)^2 x sigma^2_remaining(tau)`, where sigma_remaining
    is the return volatility from tau to settlement, estimated from prior days.

P2, line 165::

    Q2 = Sum_funds AUM x L(L-1) x r x (1 - f_fut) x (1 - n) / (multiplier x P_held)

P2, lines 168-169::

    `n` in [0, 1] = internal netting fraction. **Latent**, estimated (Section 8).
    Pre-hedging is handled by the global pre-absorption parameter in the update step
    (Section 5), not separately.

Section 5.1, lines 361-362::

    mu_total = Sum active Q_i
    sigma^2_total = Sum var_Q_i      (independence assumed; decision D5)

Section 8A.5, line 518::

    Large-lot threshold `L_min` = the 90th percentile trade size of that contract over the
    trailing 20 days (prior days only).

Section 3.1, line 69::

    **Contract months matter.** Funds hold the months specified by their index or
    methodology, which may **not** be the front month. Flow is mapped to the contract
    months actually held (from holdings).

(The document writes the Greek letters, the multiplication sign and the minus sign as such;
they are spelled out here because this file is source and the repository pins its
encodings.)

THREE THINGS THAT ARE DECISIONS, NOT IMPLEMENTATION
---------------------------------------------------
**1. Line 156 is evaluated LEFT TO RIGHT, and that is load-bearing.** Required unit test 1
(line 707) asserts the L = -2 case gives exactly +3e8 on AUM = 1e9 and r = 0.05. Measured
on this machine: ``1e9 * 6 * 0.05`` is exactly ``300000000.0``, and ``1e9 * (6 * 0.05)`` is
``300000000.00000006``. 0.05 is not a binary fraction, so the association is not free. The
document writes the factors in one order and this module multiplies them in that order.

**2. Line 160's variance is in NOTIONAL SQUARED and line 156's Q1 is in CONTRACTS. The
document does not reconcile them and this module refuses to guess.** Section 5.1 then sums
``Q_i`` into ``mu_total`` and ``var_Q_i`` into ``sigma^2_total``, and Section 5.2 divides
one by the other -- so the two must be in consistent units before they meet, and line 160's
expression has no ``/ (multiplier x P_held)`` in it while line 156 does. :func:`var_q1`
therefore returns notional-squared by default and returns contracts-squared **only** when
the caller passes ``multiplier`` and ``p_held`` explicitly; passing one without the other
raises. The choice is made at the call site, visibly, rather than inside a library that
cannot know which convention a study meant.

**3. Routing is EXACT at the endpoints and one ulp wide in the interior.** Required unit
test 3 (line 709) names only the endpoints -- ``f_fut = 0`` routes all to P2, ``f_fut = 1``
routes all to P1 -- and those are exact because multiplying a finite double by 1.0 is
lossless. Their sum in the interior is not: ``total * f + total * (1 - f)`` differs from
``total`` for 26 of the 99 values ``f = 0.01 ... 0.99`` on the golden's numbers, always by
exactly one ulp. That is inherent in writing P1 and P2 as two independent products rather
than as a split of one, so :func:`route` computes each from its own quoted formula and the
tests assert the endpoints with ``==`` and the interior to one ulp. A version that computed
``Q2 = (total - Q1) * (1 - n)`` would conserve exactly and would no longer be line 165.

WHAT IS NOT HERE
----------------
No estimation of ``n`` (Section 8), no creation model (P3/P4), no TAS proxy (P5/P6), no
impact (that is `costs/futures_impact.py`, D604), and no trading rule beyond the two timing
constraints in `ledger/update.py`. Section 8's fitted parameters are a study's output, not
a library's.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

__all__ = [
    "FlowTerm",
    "LedgerError",
    "aggregate",
    "held_months",
    "held_return",
    "is_large",
    "large_lot_threshold",
    "q1_notional",
    "q1_rebalance",
    "q2_swap",
    "route",
    "var_q1",
]

#: 8A.5 line 518. The quantile, as a fraction, and the window, in prior days.
LARGE_LOT_QUANTILE = 0.90
LARGE_LOT_LOOKBACK_DAYS = 20


class LedgerError(ValueError):
    """Raised by every guard in `backtest_framework.ledger`.

    One exception type across the four modules, so a caller that wants to distinguish a
    ledger refusal from an arbitrary `ValueError` can, and a `--selftest` proving the guards
    fire can catch one name.
    """


def _finite(name: str, value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise LedgerError(f"{name} must be a real number, got {value!r}")
    out = float(value)
    if not math.isfinite(out):
        raise LedgerError(f"{name} is not finite: {value!r}")
    return out


def _leverage(name: str, value: float) -> float:
    """A fund's L. Finite; anything else is a fund fact nobody sourced."""
    return _finite(name, value)


def _fraction(name: str, value: float) -> float:
    out = _finite(name, value)
    if not 0.0 <= out <= 1.0:
        raise LedgerError(f"{name} must lie in [0, 1], got {out!r}")
    return out


def _positive(name: str, value: float) -> float:
    out = _finite(name, value)
    if out <= 0.0:
        raise LedgerError(f"{name} must be positive, got {out!r}")
    return out


# --------------------------------------------------------------------------- the return


def held_return(p_held: float, settle_prev: float) -> float:
    """Line 146: ``r[t, tau] = P_held(t, tau) / Settle_held(t-1) - 1``.

    ``p_held`` is the holdings-weighted price of the fund's held contract(s) at tau;
    ``settle_prev`` is the holdings-weighted PRIOR SETTLEMENT of the same contracts. Both
    must be positive: a zero or negative settlement is not a cheap contract, it is a bad
    row, and dividing by it would hand a finite-looking return to everything downstream.

    Line 151 is the part that is a modelling assumption rather than arithmetic -- this
    number is then used as the forecast of the whole day's settlement-to-settlement return
    -- and it is stated here because the function's NAME does not say it.
    """
    p = _positive("p_held", p_held)
    s = _positive("settle_prev", settle_prev)
    return p / s - 1.0


# --------------------------------------------------------------------------- P1 and P2


def _leverage_coefficient(L: float) -> float:
    """``L x (L - 1)``, the coefficient every rebalance term carries.

    Zero at L = 0 and L = 1 (required unit test 2: the L = +1 funds UNG and USO contribute
    no rebalance flow at all and are in the universe for creations only), positive outside
    the open interval (0, 1), and 6 at L = -2 against 2 at L = +2 -- which is why line 707
    says both are POSITIVE on a positive return and why the inverse fund's is the larger.
    """
    return L * (L - 1.0)


def q1_notional(aum_prev: float, L: float, r: float, f_fut: float) -> float:
    """Line 156's NUMERATOR: ``AUM[t-1] x L x (L - 1) x r[t, tau] x f_fut[t-1]``, in USD.

    This is what required unit test 1 calls "notional before contract conversion". It is a
    separate function from :func:`q1_rebalance` because the document's own test is stated on
    it and because the multiplier and the held price are properties of the CONTRACT, not of
    the fund.

    The multiplications are associated LEFT TO RIGHT, as line 156 writes them. Measured:
    ``1e9 * 6 * 0.05`` is exactly ``3e8`` and ``1e9 * (6 * 0.05)`` is ``300000000.00000006``.
    """
    a = _finite("aum_prev", aum_prev)
    lev = _leverage("L", L)
    ret = _finite("r", r)
    f = _fraction("f_fut", f_fut)
    if a < 0.0:
        raise LedgerError(f"aum_prev must be non-negative, got {a!r}")
    return a * _leverage_coefficient(lev) * ret * f


def q1_rebalance(
    aum_prev: float, L: float, r: float, f_fut: float, multiplier: float, p_held: float
) -> float:
    """Line 156 in full, in CONTRACTS of the traded month, signed (+ = buy, line 143).

    ``multiplier`` is the contract's units per point (10,000 MMBtu for NG, 1,000 barrels for
    CL) and ``p_held`` is the held contract's price at tau. Both positive; the quotient is
    taken once, after the numerator, so that a caller comparing against :func:`q1_notional`
    sees the same numerator bit for bit.
    """
    m = _positive("multiplier", multiplier)
    p = _positive("p_held", p_held)
    return q1_notional(aum_prev, L, r, f_fut) / (m * p)


def var_q1(
    aum_prev: float,
    L: float,
    f_fut: float,
    sigma_remaining: float,
    *,
    multiplier: float | None = None,
    p_held: float | None = None,
) -> float:
    """Line 160: ``(AUM x L(L-1) x f_fut)^2 x sigma^2_remaining(tau)``.

    ``sigma_remaining`` is a RETURN volatility (a standard deviation, not a variance) from
    tau to settlement, "estimated from prior days". It is squared here, once, because line
    160 writes ``sigma^2_remaining``.

    **UNITS, AND THE DOCUMENT'S OWN INCONSISTENCY.** Line 160 has no
    ``/ (multiplier x P_held)`` in it, so as written this variance is in USD-squared while
    line 156's ``Q1`` is in contracts -- and Section 5.2 then divides one by the other.
    With neither ``multiplier`` nor ``p_held`` this function returns line 160 verbatim, in
    notional squared. With both, it divides by ``(multiplier x p_held) ** 2`` and returns
    contracts squared, which is what :func:`aggregate` needs if ``mu_total`` is in contracts.
    Passing exactly one raises: the unit is the caller's decision and half of it is not a
    decision.
    """
    a = _finite("aum_prev", aum_prev)
    lev = _leverage("L", L)
    f = _fraction("f_fut", f_fut)
    sd = _finite("sigma_remaining", sigma_remaining)
    if a < 0.0:
        raise LedgerError(f"aum_prev must be non-negative, got {a!r}")
    if sd < 0.0:
        raise LedgerError(
            f"sigma_remaining is a standard deviation and must be non-negative, got {sd!r}. "
            "Line 160 squares it; a negative input would square away the error."
        )
    scale = a * _leverage_coefficient(lev) * f
    out = scale * scale * sd * sd
    if multiplier is None and p_held is None:
        return out
    if multiplier is None or p_held is None:
        raise LedgerError(
            "var_q1: pass BOTH multiplier and p_held to get contracts-squared, or NEITHER to "
            "get line 160's notional-squared. Line 160 omits the contract conversion that "
            "line 156 applies, so the units of var_Q1 and Q1 differ in the document itself "
            "and Section 5.1 sums them into quantities Section 5.2 divides. Half a "
            "conversion is not a convention."
        )
    denom = _positive("multiplier", multiplier) * _positive("p_held", p_held)
    return out / (denom * denom)


def q2_swap(
    aum_prev: float,
    L: float,
    r: float,
    f_fut: float,
    n: float,
    multiplier: float,
    p_held: float,
) -> float:
    """Line 165: the swap-routed rebalance that survives the counterparty's internal netting.

    ``n`` in [0, 1] is line 168's latent netting fraction and is ASSERTED into that range
    rather than clipped -- an ``n`` outside it is a fitting failure (Section 8 constrains it)
    and a clip would launder that failure into a plausible flow. ``n = 1`` gives exactly
    0.0: the bank nets the whole client book internally and nothing reaches CME.

    Line 169 is carried here because it is the thing most easily double-counted:
    "Pre-hedging is handled by the global pre-absorption parameter in the update step
    (Section 5), not separately." Nothing in this function models pre-hedging.
    """
    f = _fraction("f_fut", f_fut)
    net = _fraction("n", n)
    m = _positive("multiplier", multiplier)
    p = _positive("p_held", p_held)
    a = _finite("aum_prev", aum_prev)
    lev = _leverage("L", L)
    ret = _finite("r", r)
    if a < 0.0:
        raise LedgerError(f"aum_prev must be non-negative, got {a!r}")
    return a * _leverage_coefficient(lev) * ret * (1.0 - f) * (1.0 - net) / (m * p)


def route(
    aum_prev: float,
    L: float,
    r: float,
    f_fut: float,
    n: float,
    multiplier: float,
    p_held: float,
) -> tuple[float, float]:
    """``(Q1, Q2)`` for one fund: the futures-routed and swap-routed halves of its rebalance.

    Required unit test 3 (line 709): ``f_fut = 0`` routes all rebalance to P2 and
    ``f_fut = 1`` routes all to P1. Both endpoints are EXACT here -- at ``f_fut = 1``, Q2's
    ``(1 - f)`` factor is ``0.0`` and at ``f_fut = 0``, Q1's ``f`` factor is, and a product
    with a zero factor is a zero.

    In the INTERIOR ``Q1 + Q2`` at ``n = 0`` is within one ulp of the unrouted total but not
    always equal to it; see the module docstring. Each half is computed from its own quoted
    formula because that is what the document registered.
    """
    q1 = q1_rebalance(aum_prev, L, r, f_fut, multiplier, p_held)
    q2 = q2_swap(aum_prev, L, r, f_fut, n, multiplier, p_held)
    return q1, q2


# --------------------------------------------------------------------------- aggregation


@dataclass(frozen=True)
class FlowTerm:
    """One participant's contribution to the ledger at tau.

    ``q`` is in contracts of the traded month, signed (+ = buy, line 143). ``var`` is in the
    SQUARE of whatever unit ``q`` is in -- see :func:`var_q1` for why that sentence has to be
    written down. ``active`` is Section 5.1's word: "Sum ACTIVE Q_i", because Section 6
    turns participants on stage by stage and a dropped stage's term must contribute nothing
    rather than be deleted from the caller's list.
    """

    name: str
    q: float
    var: float
    active: bool = True


def aggregate(terms: Iterable[FlowTerm]) -> tuple[float, float]:
    """Section 5.1 lines 361-362: ``(mu_total, sigma^2_total)`` over the ACTIVE terms.

    Both sums use :func:`math.fsum`, which is correctly rounded and therefore ORDER
    INDEPENDENT. That is a decision: "Sum active Q_i" says nothing about an order, and a
    naive loop makes the ledger's total depend on the order participants happened to be
    declared in -- so two studies that enabled the same stages in a different sequence would
    print different last bits and neither would be wrong. `math.fsum` removes the question.

    Refuses duplicate names (a participant counted twice is the defect line 352 names for
    P8a/P8b, arriving here instead), non-finite entries, and a negative variance. Line 362's
    "independence assumed; decision D5" is why the variances simply add: no covariance term
    exists in the document, and this function does not invent one.
    """
    seen: set[str] = set()
    qs: list[float] = []
    vs: list[float] = []
    for t in terms:
        if not isinstance(t, FlowTerm):
            raise LedgerError(f"aggregate: expected FlowTerm, got {type(t).__name__}")
        if t.name in seen:
            raise LedgerError(
                f"aggregate: participant {t.name!r} appears twice. One participant is one "
                "term; a repeat double-counts its flow AND its variance."
            )
        seen.add(t.name)
        if not t.active:
            continue
        qs.append(_finite(f"{t.name}.q", t.q))
        v = _finite(f"{t.name}.var", t.var)
        if v < 0.0:
            raise LedgerError(f"aggregate: {t.name!r} has a negative variance {v!r}")
        vs.append(v)
    if not qs:
        raise LedgerError(
            "aggregate: no active terms. Section 5.1 sums 'active Q_i'; an empty ledger has "
            "no prior, and returning (0, 0) would hand the update step a zero-variance "
            "certainty it never earned."
        )
    return math.fsum(qs), math.fsum(vs)


# --------------------------------------------------------------------------- held months


def held_months(
    holdings: Mapping[str, float], *, default_to_front: bool = False
) -> dict[str, float]:
    """Required unit test 12 (line 718): the share of a fund's flow each HELD month receives.

    Line 718: "Contract mapping: flow is attributed to the held contract months per
    holdings, not the front month by default." Line 69: funds hold the months their index
    specifies, "which may **not** be the front month".

    ``holdings`` maps a contract month label to the fund's position in CONTRACTS. Weights are
    ``|contracts| / sum |contracts|`` and sum to 1 within 1e-12 (checked). The absolute value
    is deliberate: an inverse fund is short every month it holds, and the DIRECTION of its
    rebalance flow is already carried by ``L(L-1)`` and by ``r``, so taking the sign from the
    holdings as well would count it twice.

    **Holdings of mixed sign in one fund are refused.** Long one month and short another is a
    calendar spread, and Section 4 defines no share of a flow for it.

    ``default_to_front=True`` ALWAYS raises. It exists so the refusal has a name a caller can
    reach for and find closed: there is no front-month fallback, by line 718 and by line 70's
    "Never back-fill today's composition across history".
    """
    if default_to_front:
        raise LedgerError(
            "held_months: there is no front-month default. Line 718 -- 'flow is attributed to "
            "the held contract months per holdings, NOT the front month by default' -- and "
            "line 69 -- funds hold the months their index specifies, 'which may not be the "
            "front month'. A fund whose holdings are unknown for a day has no ledger entry "
            "for that day; it does not get the front month."
        )
    if not isinstance(holdings, Mapping):
        raise LedgerError(f"held_months: holdings must be a mapping, got {type(holdings).__name__}")
    if not holdings:
        raise LedgerError(
            "held_months: empty holdings. Point-in-time holdings are the input (line 70); a "
            "day without them is a day without a P1 term, not a day on the front month."
        )
    values = {str(k): _finite(f"holdings[{k!r}]", v) for k, v in holdings.items()}
    signs = {math.copysign(1.0, v) for v in values.values() if v != 0.0}
    if len(signs) > 1:
        raise LedgerError(
            f"held_months: holdings {sorted(values)} carry both signs. A fund long one month "
            "and short another holds a calendar spread, and Section 4 defines no share of a "
            "flow for it."
        )
    total = math.fsum(abs(v) for v in values.values())
    if total <= 0.0:
        raise LedgerError(
            "held_months: every holding is zero, so no month can receive a share of the flow."
        )
    weights = {k: abs(v) / total for k, v in values.items()}
    got = math.fsum(weights.values())
    if abs(got - 1.0) > 1e-12:
        raise LedgerError(f"held_months: weights sum to {got!r}, not 1.0")
    return weights


# --------------------------------------------------------------------------- large lots


def large_lot_threshold(
    trade_sizes_by_day: Mapping[str, Sequence[float]],
    day: str,
    lookback_days: int = LARGE_LOT_LOOKBACK_DAYS,
    *,
    quantile: float = LARGE_LOT_QUANTILE,
) -> float:
    """8A.5 line 518: ``L_min``, the 90th percentile trade size over the trailing PRIOR days.

    ``trade_sizes_by_day`` maps an ISO day to that day's trade sizes, in lots, already
    restricted to ONE contract. Sizes are pooled across the ``lookback_days`` days strictly
    BEFORE ``day`` and the threshold is taken by NEAREST RANK: sort ascending and take the
    element at 1-based rank ``ceil(quantile x N)``.

    **Nearest rank, not interpolation, and the reason is line 753.** The document names no
    percentile definition and the seven common ones disagree. Linear interpolation between
    order statistics (numpy's default) returns a size no trade had, and line 753's "trades
    exactly at L_min count as large" is a claim about a real trade. Nearest rank keeps
    ``L_min`` an observed size, so the tie clause has something to be true of.

    **A day at or after ``day`` RAISES.** It is not filtered away: a same-day trade reaching
    a trailing window is the look-ahead line 518's "prior days only" forbids, and a silent
    filter leaves the caller believing a guard ran. This is `costs/futures_impact.py:361
    depth_bar`'s refusal shape, followed deliberately so the deposit's two trailing windows
    refuse identically. A short window raises for `depth_bar`'s other reason: "A short window
    silently averaged is how a warm-up period becomes a result."
    """
    if not isinstance(trade_sizes_by_day, Mapping):
        raise LedgerError(
            f"large_lot_threshold: trade_sizes_by_day must be a mapping, got "
            f"{type(trade_sizes_by_day).__name__}"
        )
    if not isinstance(day, str) or not day:
        raise LedgerError(f"large_lot_threshold: day must be a non-empty ISO string, got {day!r}")
    if isinstance(lookback_days, bool) or not isinstance(lookback_days, int):
        raise LedgerError(f"large_lot_threshold: lookback_days must be an int, got {lookback_days!r}")
    if lookback_days <= 0:
        raise LedgerError(f"large_lot_threshold: lookback_days must be positive, got {lookback_days}")
    q = _finite("quantile", quantile)
    if not 0.0 < q <= 1.0:
        raise LedgerError(f"large_lot_threshold: quantile must lie in (0, 1], got {q!r}")

    leaked = sorted(d for d in trade_sizes_by_day if d >= day)
    if leaked:
        raise LedgerError(
            f"large_lot_threshold: {len(leaked)} day(s) at or after the evaluation day {day} "
            f"reached the trailing window, first {leaked[0]}. 8A.5 line 518 says 'over the "
            "trailing 20 days (PRIOR days only)'; a same-day trade in L_min is look-ahead."
        )
    prior = sorted(trade_sizes_by_day)[-lookback_days:]
    if len(prior) < lookback_days:
        raise LedgerError(
            f"large_lot_threshold: only {len(prior)} prior day(s) before {day}, and the window "
            f"asks for {lookback_days}. A short window silently pooled is how a warm-up period "
            "becomes a result; skip the day or ask for a shorter lookback in writing."
        )
    pool: list[float] = []
    for d in prior:
        sizes = trade_sizes_by_day[d]
        if isinstance(sizes, (str, bytes)) or not isinstance(sizes, Sequence):
            raise LedgerError(f"large_lot_threshold: sizes for {d} must be a sequence, got {sizes!r}")
        for s in sizes:
            v = _finite(f"trade size on {d}", s)
            if v <= 0.0:
                raise LedgerError(
                    f"large_lot_threshold: a trade size of {v!r} on {d}. A trade has a positive "
                    "size; a zero or negative one is a sign convention leaking into a quantity "
                    "that has none."
                )
            pool.append(v)
    if not pool:
        raise LedgerError(
            f"large_lot_threshold: the {lookback_days} prior days before {day} hold no trades "
            "at all, so there is no distribution to take a percentile of."
        )
    pool.sort()
    rank = math.ceil(q * len(pool))
    return pool[rank - 1]


def is_large(size: float, l_min: float) -> bool:
    """Line 753: "trades exactly at L_min count as large" -- so the comparison is ``>=``.

    Stated as its own function rather than left inline because the tie is the whole content
    of the clause, and an inline ``>`` somewhere in a study would be undetectable.
    """
    s = _positive("size", size)
    m = _positive("l_min", l_min)
    return s >= m
