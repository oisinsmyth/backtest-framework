"""Continuous-contract stitching, and the gates that decide whether to trust it.

**No vendor data is needed to build or test this module.** That is deliberate: §12
of `docs/research/futures-data/data-purchase-proposal.md` requires the acceptance
tests to exist BEFORE a fixture does, and every external source consulted during
the free-data search said the same thing — the hard part of futures data is not
obtaining bars, it is stitching them.

WHY THIS IS THE HARD PART
-------------------------
A futures contract expires. A "continuous" series is therefore a fiction assembled
from many contracts, and three independent choices decide what it means:

    WHEN to roll        expiry, or volume crossover, or open-interest crossover
    HOW to adjust       ratio, difference, or not at all
    WHAT the price is   settlement or last trade, RTH or the full session

Get any of them wrong and you still get a complete, plausible, well-formed series.
Nothing errors. This is the failure mode that produces confident nonsense, which is
why the gates below are the point of the module rather than a garnish on it.

THE MEASURED FAILURE THIS MODULE EXISTS TO REJECT
--------------------------------------------------
Yahoo's `ES=F` was measured during the free-data search and is broken in a specific,
diagnosable way:

  * close 2024-12-20 **5840.26** -> Monday open **6001.75**: a **+2.77% gap** on a
    day SPY moved +0.60%
  * **15 of the top 16 ES-vs-SPY divergences fall on quarterly expiries**
  * **`adjclose` was a verbatim copy of `close` on 1258/1258 bars** — the series is
    not back-adjusted at all
  * it rolls **at expiry, not at volume crossover**, so the last 4-5 days of each
    quarter track the dying contract (volume 1,996k -> 532k), contaminating 7-8%
    of the sample

**A gate suite that has never rejected anything is not evidence.** So the tests pin
that signature and assert these gates reject it.

ROLLING ON VOLUME, NOT THE CALENDAR
-----------------------------------
`fetch_databento.py` defaults to roll rule `v`, and this module's default matches
it. The proposal originally wrote `ES.c.0`; `c` is almost certainly *calendar*,
which is the Yahoo failure above bought deliberately.

Crossover is required to PERSIST for `min_persist` sessions. A single day where the
back month prints more volume is noise — often an expiry-week spread trade — and
rolling on it produces a calendar full of one-day round trips.

RATIO VERSUS DIFFERENCE, AND WHY BOTH ARE KEPT
-----------------------------------------------
Back-adjustment removes the roll gap by restating history. Two conventions:

    RATIO       multiply history by (new / old). Preserves RETURNS exactly.
                Can drive deep history negative-adjacent or explosive over
                decades, and cannot be used where the price crosses zero.
    DIFFERENCE  add (new - old) to history. Preserves PRICE DIFFERENCES exactly.
                Survives negative prices — which is not hypothetical, CL settled
                at -$37.63 on 2020-04-20. Distorts returns in deep history.

**Returns are what this programme scores, so RATIO is the default.** Difference is
implemented because a study touching 2020 crude needs it, and because a series that
disagrees between the two conventions by more than rounding is telling you the roll
gaps are large enough to matter.

The UNADJUSTED series is always retained. Adjusted prices are a derived view and a
fixture that keeps only the derived view cannot be re-derived under a different
convention.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

# A single bar moving more than this without a documented cause is the D226 gate,
# reused here. On futures it is a roll gap or a bad print, never a real session.
MOVE_LIMIT = 0.15

# How many consecutive sessions the back month must out-trade the front before the
# crossover counts as a roll rather than as noise.
MIN_PERSIST = 2

# Yahoo's ES=F rolls at expiry, and the dying contract's volume collapses roughly
# 4x over the last week. A roll whose front-month volume share is below this at the
# roll date is a late roll -- the defining symptom.
MIN_VOLUME_SHARE_AT_ROLL = 0.35


@dataclass(frozen=True)
class Contract:
    """One delivery month. `dates` are ISO strings on the common session grid."""

    symbol: str
    dates: tuple[str, ...]
    close: np.ndarray
    volume: np.ndarray
    open_interest: np.ndarray | None = None
    expiry: str | None = None

    def __post_init__(self) -> None:
        n = len(self.dates)
        if not (len(self.close) == len(self.volume) == n):
            raise ValueError(f"{self.symbol}: ragged arrays")
        if n == 0:
            raise ValueError(f"{self.symbol}: empty contract")


@dataclass(frozen=True)
class Roll:
    date: str
    from_symbol: str
    to_symbol: str
    from_price: float
    to_price: float
    from_volume: float
    to_volume: float

    @property
    def gap_ratio(self) -> float:
        return self.to_price / self.from_price

    @property
    def front_volume_share(self) -> float:
        tot = self.from_volume + self.to_volume
        return self.from_volume / tot if tot else float("nan")


@dataclass
class Continuous:
    dates: tuple[str, ...]
    unadjusted: np.ndarray
    adjusted: np.ndarray
    source_symbol: tuple[str, ...]
    rolls: tuple[Roll, ...]
    method: str
    adjustment: str
    gates: dict = field(default_factory=dict)

    @property
    def log_returns(self) -> np.ndarray:
        r = np.diff(np.log(self.adjusted))
        return np.concatenate([[0.0], r])


def _series_on(contract: Contract, grid: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """Project a contract onto the common grid. NaN where it does not trade — never
    forward-filled, per `ragged_panel`'s contract 4: a fabricated price is a
    fabricated return."""
    idx = {d: i for i, d in enumerate(contract.dates)}
    close = np.full(len(grid), np.nan)
    vol = np.zeros(len(grid))
    for i, d in enumerate(grid):
        j = idx.get(d)
        if j is not None:
            close[i] = contract.close[j]
            vol[i] = contract.volume[j]
    return close, vol


def build_roll_calendar(contracts: list[Contract], *, method: str = "volume",
                        min_persist: int = MIN_PERSIST) -> list[Roll]:
    """Roll dates from activity, not from the calendar.

    `contracts` must be in delivery order. For each adjacent pair the roll is the
    first session where the back month out-trades the front for `min_persist`
    consecutive sessions AND both quote a price.
    """
    if method not in ("volume", "open_interest"):
        raise ValueError(f"unknown roll method {method!r}")

    grid = sorted({d for c in contracts for d in c.dates})
    rolls: list[Roll] = []

    for front, back in zip(contracts, contracts[1:]):
        fc, fv = _series_on(front, grid)
        bc, bv = _series_on(back, grid)
        if method == "open_interest":
            if front.open_interest is None or back.open_interest is None:
                raise ValueError("open_interest roll needs open interest on both")
            fv, _ = _series_on(Contract(front.symbol, front.dates,
                                        front.open_interest, front.volume), grid)
            bv, _ = _series_on(Contract(back.symbol, back.dates,
                                        back.open_interest, back.volume), grid)

        both = np.isfinite(fc) & np.isfinite(bc)
        wins = both & (bv > fv)

        roll_at = None
        run = 0
        for i in range(len(grid)):
            run = run + 1 if wins[i] else 0
            if run >= min_persist:
                roll_at = i - min_persist + 1
                break
        if roll_at is None:
            # No crossover ever observed. Fall back to the last session both
            # traded -- and the gate below will flag the series, because a
            # complex where no contract ever crosses over is not a real one.
            candidates = np.flatnonzero(both)
            if candidates.size == 0:
                continue
            roll_at = int(candidates[-1])

        rolls.append(Roll(
            date=grid[roll_at], from_symbol=front.symbol, to_symbol=back.symbol,
            from_price=float(fc[roll_at]), to_price=float(bc[roll_at]),
            from_volume=float(fv[roll_at]), to_volume=float(bv[roll_at]),
        ))
    return rolls


def stitch(contracts: list[Contract], rolls: list[Roll], *,
           adjustment: str = "ratio", method: str = "volume") -> Continuous:
    """Splice contracts into one series and back-adjust it.

    BACK-adjusted: the most recent contract keeps its real prices and history is
    restated. That is the convention that makes today's number match the screen,
    and it is why the whole series changes every time a new roll happens -- which
    is exactly why the unadjusted series is retained alongside.
    """
    if adjustment not in ("ratio", "difference", "none"):
        raise ValueError(f"unknown adjustment {adjustment!r}")

    grid = sorted({d for c in contracts for d in c.dates})
    roll_at = {r.date: r for r in rolls}

    # Which contract is front at each session: contracts[k] until its roll date.
    active = np.zeros(len(grid), dtype=int)
    k = 0
    for i, d in enumerate(grid):
        if k < len(rolls) and d >= rolls[k].date:
            k += 1
        active[i] = min(k, len(contracts) - 1)

    projected = [_series_on(c, grid)[0] for c in contracts]
    raw = np.array([projected[active[i]][i] for i in range(len(grid))])
    src = tuple(contracts[active[i]].symbol for i in range(len(grid)))

    # Walk BACKWARDS accumulating the adjustment, so the newest segment is
    # untouched and each earlier one carries every later roll's correction.
    adj = raw.copy()
    factor, offset = 1.0, 0.0
    for r in reversed(rolls):
        if adjustment == "ratio":
            factor *= r.gap_ratio
        elif adjustment == "difference":
            offset += r.to_price - r.from_price
        before = np.array([d < r.date for d in grid])
        if adjustment == "ratio":
            adj = np.where(before, raw * factor, adj)
        elif adjustment == "difference":
            adj = np.where(before, raw + offset, adj)

    return Continuous(
        dates=tuple(grid), unadjusted=raw, adjusted=adj, source_symbol=src,
        rolls=tuple(rolls), method=method, adjustment=adjustment,
    )


def acceptance_gates(series: Continuous, *,
                     reference: np.ndarray | None = None,
                     expiry_dates: set[str] | None = None,
                     move_limit: float = MOVE_LIMIT) -> dict:
    """The gates §12 requires before any study reads a futures fixture.

    Each returns a `failures` list so `ragged_panel.assert_gates_passed` can read
    the block without knowing what any individual gate means.
    """
    gates: dict = {}
    adj = series.adjusted
    finite = np.isfinite(adj)

    # 1. No unexplained single-bar move. D226's gate, and on futures the usual
    #    cause is an unadjusted roll gap rather than a split.
    moves = np.abs(np.diff(np.log(adj[finite])))
    big = np.flatnonzero(moves > move_limit)
    dates = [d for d, f in zip(series.dates, finite) if f]
    gates["no_unexplained_large_move"] = {
        "limit": move_limit,
        "worst": float(moves.max()) if moves.size else 0.0,
        "failures": [{"date": dates[i + 1], "move": float(moves[i])}
                     for i in big[:20]],
    }

    # 2. THE ADJUSTMENT MUST HAVE HAPPENED. Yahoo's adjclose was a verbatim copy
    #    of close on 1258/1258 bars -- a series that claims to be adjusted and is
    #    identical to the raw one is not adjusted, it is mislabelled.
    identical = bool(np.allclose(series.adjusted[finite], series.unadjusted[finite],
                                 rtol=0, atol=1e-12))
    should_differ = series.adjustment != "none" and len(series.rolls) > 0 and any(
        abs(r.gap_ratio - 1.0) > 1e-9 for r in series.rolls)
    gates["adjustment_actually_applied"] = {
        "adjusted_equals_unadjusted": identical,
        "failures": (["adjusted series is a verbatim copy of the unadjusted one, "
                      "which is the measured Yahoo ES=F signature"]
                     if identical and should_differ else []),
    }

    # 3. ROLLS MUST BE ON CROSSOVER, NOT EXPIRY. The symptom of a calendar roll is
    #    that the front month is already moribund when the roll happens.
    late = [{"date": r.date, "from": r.from_symbol,
             "front_volume_share": round(r.front_volume_share, 4)}
            for r in series.rolls
            if np.isfinite(r.front_volume_share)
            and r.front_volume_share < MIN_VOLUME_SHARE_AT_ROLL]
    gates["rolls_on_crossover_not_expiry"] = {
        "min_front_volume_share": MIN_VOLUME_SHARE_AT_ROLL,
        "rolls": len(series.rolls),
        "failures": late,
    }

    # 4. A roll ON an expiry date is the calendar rule wearing a crossover's name.
    if expiry_dates:
        on_expiry = [r.date for r in series.rolls if r.date in expiry_dates]
        gates["no_roll_on_an_expiry_date"] = {
            "failures": on_expiry,
            "note": ("rolling exactly at expiry leaves the last sessions of each "
                     "cycle tracking the dying contract -- measured at 7-8% of "
                     "the sample on Yahoo's ES=F"),
        }

    # 5. DIVERGENCE FROM A REFERENCE MUST NOT CONCENTRATE ON ROLLS. This is the
    #    test that actually caught Yahoo: 15 of its top 16 ES-vs-SPY divergences
    #    fell on quarterly expiries, which is not a market fact, it is an artefact.
    if reference is not None and reference.shape == adj.shape:
        ok = finite & np.isfinite(reference)
        r_ser = np.diff(np.log(adj[ok]))
        r_ref = np.diff(np.log(reference[ok]))
        d = np.abs(r_ser - r_ref)
        ds = [x for x, f in zip(series.dates, ok) if f][1:]
        top = np.argsort(d)[::-1][:16]
        roll_dates = {r.date for r in series.rolls}
        near = sum(1 for i in top if ds[i] in roll_dates)
        gates["divergence_not_concentrated_at_rolls"] = {
            "top_n": int(len(top)),
            "of_which_on_a_roll_date": int(near),
            "failures": ([f"{near}/{len(top)} largest divergences sit on roll "
                          f"dates -- the measured Yahoo signature"]
                         if near > len(top) // 2 else []),
        }

    gates["passed"] = not any(
        v.get("failures") for v in gates.values() if isinstance(v, dict))
    return gates
