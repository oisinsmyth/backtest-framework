"""Power analysis and minimum detectable effects — D588.

Implements the planning arithmetic pre-registered, in identical words, in five
User-Doc-Deposit documents:

  * `SETTLEMENT_FLOW_LEDGER_PREREG.md` §9A (formulas, planning table, rules),
    §9B (the route an underpowered stage takes instead), §13A.7 (how power feeds
    the three tracks), unit tests 51-63;
  * `LETF_CLOSE_FLOW_PREREG.md` §6A and §6B;
  * `SHOCK_CLASSIFIER_PREREG.md` §7A and §7B;
  * `INDEX_REWEIGHT_FLOW_PREREG.md` §8B.1;
  * `OPENING_AGENT_STATE_PREREG.md` §10.

The pre-registered formulas, verbatim from ledger §9A:

    Flow / correlation tests:   SE ~= 1 / sqrt(n_eff)
    Price tests:                SE  = sigma_trade / sqrt(n_eff)
    Minimum detectable effect:  MDE_t2 ~= 2   x SE   (significance at t = 2)
                                MDE_80 ~= 2.8 x SE   (80% power at t = 2)
    Clustering (design effect): n_eff = n / (1 + (m - 1) x rho)

WHAT THIS MODULE IS NOT. It computes no strategy return and reads no market
fixture. Every number here is *planning* arithmetic: a claim about how small an
effect a given sample could resolve, not a claim about any effect. §9A.1 is
explicit that the planning table's entries are estimates "recomputed on real data
before each stage", which is why `write_power_md` stamps that sentence into every
file it writes.

UNITS. Two regimes, and mixing them is the failure this module exists to make
hard to commit silently:

  * CORRELATION UNITS (dimensionless). `se_correlation` returns 1/sqrt(n_eff);
    the MDE that follows is a correlation, comparable to a plausible-effect
    statement written as a correlation.
  * PRICE UNITS (multiples of sigma). `se_mean` returns sigma/sqrt(n_eff) in
    whatever unit sigma carries — the deposit docs always quote sigma_trade, so
    the MDE reads as "0.09 sigma". Per ledger §9A.1 an illustrative 35-minute
    sigma of ~1.1% (NG) turns 0.05 sigma into ~6 bp; this module never performs
    that last conversion, because it has no price.

`PowerRow` carries whichever of the two it was built in, and `write_power_md`
prints a `units` column so a reader is never left to guess.

House style follows `validation/dsr.py`: stdlib plus numpy, no scipy, every guard
raising loudly rather than returning a sentinel.
"""

from __future__ import annotations

import datetime as _dt
import math
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

import numpy as np

# MDE_80's constant, pre-registered in every deposit doc as the bare "2.8".
#   z_0.975 + z_0.80 = 1.9599639845400545 + 0.8416212335729143 = 2.801585218112969
# The docs fix 2.8, and ledger unit test 52 asserts the value that 2.8 produces
# (n_eff = 2,500 -> MDE_80 = 0.056), so 2.8 is used exactly and the true sum is
# recorded here rather than substituted for it.
Z80_TWO_SIDED = 2.8
Z80_TWO_SIDED_EXACT = 2.801585218112969

# Ledger §13A.4 / §13A.7(4): the frozen Track 3 trading target.
TRACK3_TARGET_N = 300

PowerClass = Literal["individually_testable", "underpowered"]
ForwardRoute = Literal["forward", "9B"]
Track3RouteName = Literal["efficacy_n300", "combined_evidence"]


# --------------------------------------------------------------------------- clustering


def design_effect(m: float, rho: float) -> float:
    """Kish design effect, dimensionless: ``1 + (m - 1) * rho`` (ledger §9A).

    `m` is observations per cluster (a mean, so a float: 4.5 observations per day
    is a real answer); `rho` is the within-cluster correlation. Ledger unit test
    51: m = 10 and rho = 0.1 give 1.9, so n_eff = n / 1.9.

    Raises on m < 1, and on rho outside [-1/(m-1), 1] — the interval on which a
    design effect is non-negative. Below the floor the formula returns a negative
    or zero divisor and n_eff would come back negative or infinite, which reads on
    a page as a wildly *well*-powered stage. At m = 1 there is no clustering and
    any rho is vacuous, so the floor is -inf there.
    """
    if m < 1.0:
        raise ValueError(f"design_effect needs m >= 1 (observations per cluster), got {m}")
    if not math.isfinite(rho):
        raise ValueError(f"rho must be finite, got {rho}")
    floor = -math.inf if m == 1.0 else -1.0 / (m - 1.0)
    if rho > 1.0 or rho < floor:
        raise ValueError(
            f"rho={rho} is outside [{floor}, 1] for m={m}: a design effect of "
            f"{1.0 + (m - 1.0) * rho} is not a usable divisor"
        )
    return 1.0 + (m - 1.0) * rho


def n_eff(n: int, m: float, rho: float) -> float:
    """Effective sample size, in observations: ``n / design_effect(m, rho)``.

    Ledger §9A formula block. `n` is the raw observation count, not the cluster
    count. Raises on n < 1, on any `design_effect` violation, and on the one
    admissible-but-degenerate corner: rho exactly at its floor -1/(m-1) makes the
    design effect 0, and n/0 is not an effective sample size — it is a division by
    zero dressed as infinite power.
    """
    if n < 1:
        raise ValueError(f"n_eff needs n >= 1 observations, got {n}")
    deff = design_effect(m, rho)
    if deff <= 0.0:
        raise ValueError(
            f"design effect is {deff} at m={m}, rho={rho} (rho at its floor -1/(m-1)): "
            f"n_eff is undefined there"
        )
    return float(n) / deff


def _flatten_clusters(
    values: object, cluster_ids: object
) -> tuple[np.ndarray, np.ndarray]:
    """Normalise the two accepted input shapes into (values, integer cluster codes).

    FLAT FORM (`cluster_ids` given): one label per observation, the form the deposit
    docs' data arrives in (a day id, a year, an instrument).

    GROUPED FORM (`cluster_ids=None`): `values` is a sequence of per-cluster
    sequences. This form exists so the empty-cluster guard can FIRE. In the flat
    form an empty cluster is unrepresentable — a label with no observations is a
    label that simply is not in the array, and `np.unique` cannot return it — so a
    guard written against the flat form alone could never run and would be worse
    than no guard at all (CLAUDE.md: "a self-test that cannot fail is worse than
    none"). Passing `[[1.0, 2.0], [], [3.0, 4.0]]` is how a caller loses a cluster,
    and it raises.
    """
    if cluster_ids is None:
        groups = list(values)  # type: ignore[call-overload]
        arrays = []
        for position, group in enumerate(groups):
            arr = np.asarray(group, dtype=float).ravel()
            if arr.size == 0:
                raise ValueError(
                    f"icc_from_clusters got an empty cluster at position {position} of "
                    f"{len(groups)}: an empty cluster still shifts k and therefore every "
                    f"mean square. Drop it explicitly or fix the grouping."
                )
            arrays.append(arr)
        if not arrays:
            raise ValueError("icc_from_clusters got no clusters")
        y = np.concatenate(arrays)
        codes = np.concatenate(
            [np.full(arr.size, index, dtype=np.intp) for index, arr in enumerate(arrays)]
        )
        return y, codes

    y = np.asarray(values, dtype=float).ravel()
    ids = np.asarray(cluster_ids).ravel()
    if y.size != ids.size:
        raise ValueError(f"values and cluster_ids differ in length: {y.size} vs {ids.size}")
    if y.size == 0:
        raise ValueError("icc_from_clusters got no observations")
    _, inverse = np.unique(ids, return_inverse=True)
    return y, np.asarray(inverse).ravel().astype(np.intp)


def icc_from_clusters(
    values: Sequence[float] | Sequence[Sequence[float]] | np.ndarray,
    cluster_ids: Sequence[object] | np.ndarray | None = None,
) -> float:
    """One-way random-effects ANOVA intraclass correlation, dimensionless.

    The estimator (ANOVA / "ICC(1)", Shrout-Fleiss ICC(1,1)), with the standard n0
    correction for unequal cluster sizes:

        MSB = SSB / (k - 1),   SSB = sum_i n_i * (ybar_i - ybar)^2
        MSW = SSW / (N - k),   SSW = sum_i sum_j (y_ij - ybar_i)^2
        n0  = (N - sum_i n_i^2 / N) / (k - 1)
        ICC = (MSB - MSW) / (MSB + (n0 - 1) * MSW)

    `ybar` is the grand mean over all N observations (not the mean of cluster
    means). n0 is the "average" cluster size the unequal-size design behaves like;
    it equals the common size when sizes are equal and is strictly below the
    arithmetic mean size otherwise, which is the whole point of the correction.

    The estimate is NOT clamped at zero. A negative ICC is a real finding — less
    within-cluster agreement than chance — and clamping it would silently inflate
    the design effect. It is bounded below by -1/(n0 - 1) by construction.

    This is the rho the deposit docs mean by "estimated from the data": ledger
    §9A ("m = observations per cluster; rho = within-cluster correlation"), shock
    classifier §7A ("shocks cluster in time ... n_eff uses the design effect with
    day clusters"), index §8B.1 (within-year correlation over 10 year-clusters),
    opening §10 (rho_same_day for pooled ES+NQ).

    TWO INPUT SHAPES, one of them so the empty-cluster guard can fire — see
    `_flatten_clusters`. `icc_from_clusters(values, cluster_ids)` is the flat form;
    `icc_from_clusters(groups)` takes a sequence of per-cluster sequences.

    Raises on fewer than 2 clusters, on any empty cluster (grouped form), on a
    design with no within-cluster degrees of freedom (every cluster of size 1,
    where MSW does not exist), and on zero total variance (where the ratio is 0/0).
    """
    y, inverse = _flatten_clusters(values, cluster_ids)
    if not np.all(np.isfinite(y)):
        raise ValueError("icc_from_clusters got a non-finite value; clean or drop it explicitly")

    k = int(inverse.max()) + 1
    if k < 2:
        raise ValueError(f"icc_from_clusters needs at least 2 clusters, got {k}")
    sizes = np.bincount(inverse, minlength=k).astype(float)

    total_n = float(y.size)
    if total_n <= k:
        raise ValueError(
            f"icc_from_clusters needs N > k for the within-cluster mean square: "
            f"N={int(total_n)}, k={k} (every cluster of size 1 has no within variation)"
        )

    grand_mean = float(y.mean())
    total_ss = float(np.sum((y - grand_mean) ** 2))
    if total_ss <= 0.0:
        raise ValueError("icc_from_clusters got zero total variance: the ICC ratio is 0/0")

    cluster_sums = np.bincount(inverse, weights=y, minlength=k)
    cluster_means = cluster_sums / sizes
    ss_between = float(np.sum(sizes * (cluster_means - grand_mean) ** 2))
    ss_within = float(np.sum((y - cluster_means[inverse]) ** 2))

    ms_between = ss_between / (k - 1)
    ms_within = ss_within / (total_n - k)
    n0 = (total_n - float(np.sum(sizes**2)) / total_n) / (k - 1)

    denominator = ms_between + (n0 - 1.0) * ms_within
    if denominator == 0.0:
        raise ValueError("icc_from_clusters denominator is zero: the ICC is undefined here")
    return float((ms_between - ms_within) / denominator)


def n_eff_from_clusters(
    values: Sequence[float] | Sequence[Sequence[float]] | np.ndarray,
    cluster_ids: Sequence[object] | np.ndarray | None = None,
) -> float:
    """n_eff in observations, straight from clustered data (ledger §9A.2 rule 1).

    m is the MEAN cluster size N/k and rho is `icc_from_clusters`. Note that the
    ICC's own n0 is below N/k whenever cluster sizes are unequal, so with very
    unequal sizes and a strongly negative ICC the pair (N/k, rho) can fall outside
    `design_effect`'s domain and this raises. That is the intended outcome: it says
    the two quantities were estimated under different notions of "cluster size" and
    the resulting n_eff would not be interpretable.
    """
    y, inverse = _flatten_clusters(values, cluster_ids)
    rho = icc_from_clusters(y, inverse)
    k = int(inverse.max()) + 1
    mean_size = float(y.size) / k
    return n_eff(int(y.size), mean_size, rho)


# --------------------------------------------------------------------------- cross-series


class _PanelLike(Protocol):
    """The two grids `n_eff_cross_series` reads off a ragged panel.

    Structural rather than a `RaggedPanel` import: `RaggedPanel` lives in
    `scripts/ragged_panel.py`, and the library does not import research scripts.
    """

    log_returns: np.ndarray
    live: np.ndarray


def n_eff_cross_series(panel: _PanelLike, start: int, min_overlap: int = 250) -> float:
    """Effective number of INDEPENDENT instruments: ``1 / (w' R w)`` at equal weights.

    Dimensionless — a count. With n series and equal weights w = 1/n this is
    ``n^2 / sum(R)``: n when the correlation matrix is the identity, 1 when every
    series is perfectly correlated.

    This is the cross-series counterpart of the within-cluster design effect, and
    it is what the deposit docs mean when they pool instruments — ledger §13A.7(2)
    divides `n_needed` by an instrument count, opening §10 pools ES+NQ, and both
    assume the instruments carry independent information that a correlation matrix
    can price.

    PORTED, BIT-FOR-BIT, from `scripts/ragged_panel.py:effective_instruments`
    (D256's panel). The loop, the `min_overlap` gate, the zero-standard-deviation
    skip and `np.corrcoef` are reproduced unchanged rather than vectorised, so the
    two functions return the identical float; `tests/unit/test_power.py` asserts
    equality to 1e-12 on a synthetic ragged panel. The copy exists because `src`
    must not import from `scripts`, not because the arithmetic differs.

    `start` is the first column index scored; pairs sharing fewer than
    `min_overlap` live bars keep a correlation of 0 (i.e. count as independent).
    """
    if start < 0:
        raise ValueError(f"n_eff_cross_series needs start >= 0, got {start}")
    if min_overlap < 2:
        raise ValueError(f"min_overlap must be at least 2 bars, got {min_overlap}")
    r, lv = panel.log_returns[:, start:], panel.live[:, start:]
    n = r.shape[0]
    if n < 1:
        raise ValueError("n_eff_cross_series got a panel with no series")
    correlation = np.eye(n)
    for i in range(n):
        for j in range(i + 1, n):
            m = lv[i] & lv[j]
            if m.sum() >= min_overlap:
                a, b = r[i][m], r[j][m]
                if a.std() > 0 and b.std() > 0:
                    correlation[i, j] = correlation[j, i] = float(np.corrcoef(a, b)[0, 1])
    return float(n * n / correlation.sum())


# --------------------------------------------------------------------------- SE and MDE


def se_correlation(n_eff_value: float) -> float:
    """Standard error of a correlation estimate, dimensionless: ``1 / sqrt(n_eff)``.

    Ledger §9A, "Flow / correlation tests". Raises below n_eff = 2: a standard
    error on one observation is not a number this module will hand back.
    """
    if not math.isfinite(n_eff_value) or n_eff_value < 2.0:
        raise ValueError(f"se_correlation needs n_eff >= 2, got {n_eff_value}")
    return 1.0 / math.sqrt(n_eff_value)


def se_mean(sigma: float, n_eff_value: float) -> float:
    """Standard error of a mean, in sigma's own units: ``sigma / sqrt(n_eff)``.

    Ledger §9A, "Price tests" (there sigma is sigma_trade, the per-trade return
    standard deviation, so the result reads as a multiple of sigma). Raises below
    n_eff = 2, and on a non-positive or non-finite sigma.
    """
    if not math.isfinite(sigma) or sigma <= 0.0:
        raise ValueError(f"se_mean needs a positive finite sigma, got {sigma}")
    if not math.isfinite(n_eff_value) or n_eff_value < 2.0:
        raise ValueError(f"se_mean needs n_eff >= 2, got {n_eff_value}")
    return sigma / math.sqrt(n_eff_value)


def mde(se: float, t: float = 2.0) -> float:
    """Minimum detectable effect at significance t, in the units of `se`: ``t * se``.

    Ledger §9A: MDE_t2 ~= 2 x SE. The smallest true effect whose estimate would
    clear |t| at this standard error — NOT an 80%-power figure; at MDE_t2 the test
    rejects half the time. Use `mde_80` for the powered version.
    """
    if not math.isfinite(se) or se <= 0.0:
        raise ValueError(f"mde needs a positive finite se, got {se}")
    if not math.isfinite(t) or t <= 0.0:
        raise ValueError(f"mde needs a positive finite t, got {t}")
    return t * se


def mde_80(se: float) -> float:
    """Minimum detectable effect at 80% power, in the units of `se`: ``2.8 * se``.

    Ledger §9A. 2.8 ~= z_0.975 + z_0.80 = 1.95996... + 0.84162... = 2.80159...;
    the docs pre-register the rounded 2.8 and unit test 52 pins the value it gives
    (n_eff = 2,500 -> 0.056), so 2.8 is used exactly. See `Z80_TWO_SIDED_EXACT`.
    """
    if not math.isfinite(se) or se <= 0.0:
        raise ValueError(f"mde_80 needs a positive finite se, got {se}")
    return Z80_TWO_SIDED * se


def power_class(mde_value: float, plausible_effect: float) -> PowerClass:
    """Ledger §9A.2 rule 3, as a label.

    "if MDE_t2 > the plausible effect, the stage is labelled underpowered. It may
    not be adopted on an individual significance test. It is evaluated under
    Section 9B instead."

    Both arguments must be in the SAME units (correlation, or multiples of sigma)
    — the comparison is meaningless otherwise and nothing downstream can detect
    the mix. Equality counts as testable, matching the rule's strict ">".
    """
    if not math.isfinite(mde_value) or mde_value <= 0.0:
        raise ValueError(f"power_class needs a positive finite mde, got {mde_value}")
    if not math.isfinite(plausible_effect) or plausible_effect <= 0.0:
        raise ValueError(
            f"power_class needs a positive finite plausible effect, got {plausible_effect}"
        )
    return "underpowered" if mde_value > plausible_effect else "individually_testable"


# --------------------------------------------------------------------------- track routing


@dataclass(frozen=True)
class ForwardPlan:
    """Ledger §13A.7(2). `n_needed` in observations, `evaluation_days` in trading days."""

    n_needed: float
    evaluation_days: float | None
    route: ForwardRoute


def forward_evaluation_days(
    plausible_effect: float, instruments: int, floor: float = 120.0, cap: float = 500.0
) -> ForwardPlan:
    """Power-based forward evaluation length, per ledger §13A.7(2):

        n_needed        = (2 / plausible_effect)^2      (flow tests, correlation units)
        evaluation_days = max(120, n_needed / instruments), capped at 500 trading days

    `plausible_effect` is in correlation units; `instruments` is the number of
    markets the forward recorder observes per trading day. Returns `route="9B"`
    with `evaluation_days=None` when the length exceeds the cap — the stage then
    "skips individual forward testing and goes straight to its 9B method".

    Ledger unit test 59: plausible 0.1 with 2 instruments gives n_needed = 400 and
    200 evaluation days (route "forward"); plausible 0.05 gives 1,600, exceeds the
    cap, and routes to 9B.

    WHICH QUANTITY MEETS THE CAP. The doc's prose says "if `n_needed` would exceed
    the cap" while its formula line caps `evaluation_days`; the two agree on both
    worked cases in test 59 (800 > 500 and 200 <= 500) but diverge for a large
    instrument count. This implementation caps `evaluation_days`, following the
    formula line, because the cap is stated in trading days and `n_needed` is an
    observation count — and because more instruments genuinely do shorten the
    calendar. Recorded rather than silently chosen.
    """
    if not math.isfinite(plausible_effect) or plausible_effect <= 0.0:
        raise ValueError(
            f"forward_evaluation_days needs a positive finite plausible effect, "
            f"got {plausible_effect}"
        )
    if instruments < 1:
        raise ValueError(f"forward_evaluation_days needs at least 1 instrument, got {instruments}")
    if floor <= 0.0 or cap <= 0.0 or cap < floor:
        raise ValueError(f"forward_evaluation_days needs 0 < floor <= cap, got {floor}, {cap}")
    n_needed = (2.0 / plausible_effect) ** 2
    days = max(floor, n_needed / instruments)
    if days > cap:
        return ForwardPlan(n_needed=n_needed, evaluation_days=None, route="9B")
    return ForwardPlan(n_needed=n_needed, evaluation_days=days, route="forward")


@dataclass(frozen=True)
class Track3Route:
    """Ledger §13A.7(4). `se` and `mde` in multiples of sigma (per trade)."""

    se: float
    mde: float
    route: Track3RouteName


def track3_route(edge_sigma: float, n: int = TRACK3_TARGET_N) -> Track3Route:
    """Track 3 trading-target power check, per ledger §13A.7(4).

    At N = 300 trades, SE = 1/sqrt(300) = 0.0577 sigma and MDE (t = 2) = 0.1155
    sigma (the docs round this to "SE ~= 0.058 sigma, MDE ~= 0.115 sigma"). If the
    Track 1 edge estimate is at or above the MDE, the frozen N = 300 efficacy test
    is the primary promotion route; below it, N = 300 is underpowered and the route
    becomes combined evidence, with the forward test acting as a futility and
    consistency check.

    `edge_sigma` is the Track 1 edge per trade in multiples of sigma, so the unit
    matches the MDE without conversion. Ledger unit test 62: 0.08 sigma selects
    combined evidence, 0.15 sigma selects the N = 300 efficacy route.

    Ledger §13A.8(4) requires the haircut — 50% of the in-sample walk-forward edge,
    or the vault estimate if lower — to be applied BEFORE this call. This function
    cannot tell a haircut edge from a raw one; pass the haircut number.
    """
    if not math.isfinite(edge_sigma) or edge_sigma <= 0.0:
        raise ValueError(f"track3_route needs a positive finite edge in sigma, got {edge_sigma}")
    # sigma = 1 makes the result read in multiples of sigma_trade: se_mean(1, n) = 1/sqrt(n).
    se = se_mean(1.0, float(n))
    threshold = mde(se)
    route: Track3RouteName = "efficacy_n300" if edge_sigma >= threshold else "combined_evidence"
    return Track3Route(se=se, mde=threshold, route=route)


# --------------------------------------------------------------------------- the POWER.md row


@dataclass(frozen=True)
class PowerRow:
    """One line of `results/<study>/POWER.md` and of `TRACK_MAP.md` (ledger §13A.2, v1.8).

    Units: `n` observations; `m` observations per cluster; `rho` and (in the
    correlation regime) `se`, `mde_t2`, `mde_80`, `plausible_effect` are
    dimensionless; in the price regime those four are multiples of `sigma`.
    `sigma` is None in the correlation regime and carries the value used in the
    price regime.

    `plausible_effect` and `power_class` are Optional so that a row lacking its
    §9A.2 rule 2 statement can be CONSTRUCTED and then caught by
    `validate_track_map` — ledger unit test 63. A row is never silently classified
    without one.
    """

    stage: str
    test: str
    n: int
    m: float
    rho: float
    n_eff: float
    se: float
    mde_t2: float
    mde_80: float
    plausible_effect: float | None
    power_class: str | None
    track: str
    note: str
    sigma: float | None = None

    @property
    def units(self) -> str:
        """"correlation" or "sigma" — which regime `se` and the MDEs are in."""
        return "correlation" if self.sigma is None else "sigma"

    @property
    def adoption_by_significance_blocked(self) -> bool:
        """Ledger §9A.2 rule 3 and unit test 53, as a boolean the row exposes.

        True unless the row is classified `individually_testable`. An underpowered
        stage "may not be adopted on an individual significance test"; a row with
        no plausible-effect statement has not been classified at all, and §13A.2
        requires the class before the stage runs, so it is blocked too. Blocking is
        the safe direction: the cost of a wrong True is a 9B validation that was
        not strictly required.
        """
        return self.power_class != "individually_testable"


def power_row(
    stage: str,
    test: str,
    n: int,
    m: float,
    rho: float,
    track: str,
    plausible_effect: float | None = None,
    sigma: float | None = None,
    note: str = "",
) -> PowerRow:
    """Build a `PowerRow`, computing n_eff, SE, MDE_t2, MDE_80 and the power class.

    `sigma=None` selects the correlation regime (SE = 1/sqrt(n_eff)); a positive
    `sigma` selects the price regime (SE = sigma/sqrt(n_eff)) and the MDEs come
    back in multiples of sigma. `plausible_effect` must be in the SAME regime; pass
    None only to record a stage whose §9A.2 rule 2 statement is still outstanding,
    which `validate_track_map` will then refuse.
    """
    effective = n_eff(n, m, rho)
    se = se_correlation(effective) if sigma is None else se_mean(sigma, effective)
    t2 = mde(se)
    p80 = mde_80(se)
    cls = None if plausible_effect is None else power_class(t2, plausible_effect)
    return PowerRow(
        stage=stage,
        test=test,
        n=n,
        m=m,
        rho=rho,
        n_eff=effective,
        se=se,
        mde_t2=t2,
        mde_80=p80,
        plausible_effect=plausible_effect,
        power_class=cls,
        track=track,
        note=note,
        sigma=sigma,
    )


_TRACK_MAP_REQUIRED = (
    ("stage", "a stage name"),
    ("track", "a track (ledger 13A.2)"),
    ("n_eff", "an n_eff"),
    ("se", "an SE"),
    ("mde_t2", "an MDE (t = 2)"),
    # plausible_effect BEFORE power_class deliberately: a row with no plausible-effect
    # statement also has no class, and naming the class first would report the symptom
    # rather than the cause (ledger 9A.2 rule 2 precedes rule 3).
    ("plausible_effect", "a plausible-effect statement (ledger 9A.2 rule 2)"),
    ("power_class", "a power class (ledger 9A.2 rule 3)"),
)


def validate_track_map(rows: Sequence[PowerRow]) -> None:
    """Ledger unit test 63: "every stage has a track, a power class, n_eff, SE, MDE
    and a plausible-effect statement before it runs."

    Raises `ValueError` naming the FIRST offending row and the first field it is
    missing. A missing field is None, an empty/blank string, or a non-finite
    number. Returns None on a clean table — there is nothing to report when every
    row is complete.
    """
    if len(rows) == 0:
        raise ValueError("validate_track_map got no rows: an empty TRACK_MAP has nothing to gate")
    for index, row in enumerate(rows):
        for field, description in _TRACK_MAP_REQUIRED:
            value = getattr(row, field, None)
            missing = (
                value is None
                or (isinstance(value, str) and value.strip() == "")
                or (isinstance(value, float) and not math.isfinite(value))
            )
            if missing:
                raise ValueError(
                    f"TRACK_MAP row {index} (stage={row.stage!r}, test={row.test!r}) is "
                    f"missing {description}: {field}={value!r}. Ledger 13A.2 requires it "
                    f"before the stage runs."
                )


# --------------------------------------------------------------------------- the writer

_HEADER_RECOMPUTE = (
    "Every value below is PLANNING arithmetic. Ledger §9A.1: the planning table holds "
    "estimates, and the real n_eff (with the design effect from the observed "
    "within-cluster correlation), SE and MDE are **recomputed on real data before each "
    "stage runs** and this file rewritten. A number here has never been compared with a "
    "market outcome."
)

_COLUMNS = (
    "Stage",
    "Test",
    "Track",
    "n",
    "m",
    "rho",
    "n_eff",
    "Units",
    "SE",
    "MDE (t = 2)",
    "MDE (80%)",
    "Plausible effect",
    "Power class",
    "Adoption by significance",
    "Note",
)


def _fmt(value: float | None, places: int = 4) -> str:
    if value is None:
        return "—"
    return f"{value:,.{places}f}"


def write_power_md(
    rows: Sequence[PowerRow], path: str | Path, title: str = "POWER", date: str | None = None
) -> Path:
    """Write the ledger §9A.1 / §13A.2 power table to `path`; return the path written.

    Parent directories are created. The caller supplies the path: this module does
    NOT decide the `results/<study>/POWER.md` convention the deposit docs specify,
    because no `results/` tree exists in this repository yet and inventing one here
    would put a directory layout in a library function.

    The header stamps the date (UTC today unless `date` is given, so a golden test
    can pin it) and the "recomputed on real data" sentence above. `validate_track_map`
    runs first: an incomplete table is not written at all.
    """
    validate_track_map(rows)
    stamp = date if date is not None else _dt.datetime.now(_dt.timezone.utc).date().isoformat()
    lines = [
        f"# {title}",
        "",
        f"**Generated:** {stamp} · `backtest_framework.validation.power` (D588)",
        "",
        _HEADER_RECOMPUTE,
        "",
        "| " + " | ".join(_COLUMNS) + " |",
        "|" + "|".join("---" for _ in _COLUMNS) + "|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.stage,
                    row.test,
                    row.track,
                    f"{row.n:,}",
                    _fmt(row.m, 2),
                    _fmt(row.rho, 4),
                    _fmt(row.n_eff, 1),
                    row.units,
                    _fmt(row.se),
                    _fmt(row.mde_t2),
                    _fmt(row.mde_80),
                    _fmt(row.plausible_effect),
                    row.power_class or "—",
                    "BLOCKED" if row.adoption_by_significance_blocked else "permitted",
                    row.note or "—",
                ]
            )
            + " |"
        )
    lines += [
        "",
        "**Adoption by significance** is BLOCKED for every row not classed "
        "`individually_testable` (ledger §9A.2 rule 3): an underpowered stage is evaluated "
        "under §9B instead, and a non-significant result there is recorded as "
        "*inconclusive*, never as *no effect* (rule 5).",
        "",
    ]
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return out
