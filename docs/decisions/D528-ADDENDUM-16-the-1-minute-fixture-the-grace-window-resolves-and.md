# D528 ADDENDUM 16 — the 1-minute fixture: the grace window resolves, σ is sub-diffusive, and the two lenses invert

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D528-ADDENDUM-16-the-1-minute-fixture-the-grace-window-resolves-and-sigma-is-sub-diffusive.md`. The H1 above is the full title.*

Date: 2026-09-15. Runners: `scripts/build_fut_day1m.py`, `working/d528_one_minute.py`.

**Nothing admitted (R15). Reserved slice NOT read** — the loader caps at 2026-04-10 and asserts.
Out of time throughout: forecast fitted on days < 2020-01-01, every figure on days ≥ 2020-01-01.
Both lenses. Design enumerated as M1–M12 and confounds as O1–O5 in the runner, printed with the
result. Predictions P1–P4 were committed in the runner's docstring before the run.

---

## 1. The fixture

`data/fixtures/fut_day1m.parquet`: **49,433,958 bars, 36 roots, 135,179 root-sessions**, 382 MiB,
decoded from all 26 `ohlcv-1m` files (11.38 GiB) in 43.1 min. The 5-minute decode cache aggregates
*at decode time*, so the minute detail was already gone and the archive had to be re-read.

It inherits rather than re-derives: `ids_of` validity windows (D520), the front month taken from
`fut_breadth_hourly` by join, the `present`/`same_front` flags (D506), and the duplicate-minute
guard. `build_fut_day5m.set_bar_minutes(n)` rebinds the width, the bars-per-session count, the
cache directory **and** filename tag, and both output paths together, so a caller cannot
half-retarget it and write 1-minute bars into the committed 5-minute fixture.

**The width-specific gate passed on every row: all 49,433,958 carry `n == 1`.** At 1-minute width
the reaggregation is a no-op, so any `n > 1` would mean duplicate instrument-minutes in the
archive. Median 392.3 bars a session of 420. The coverage report reproduces the 5-minute
universe — full bands for index and energy from 2016, HE/LE on their own 275-slot session, and
`NEVER` for 6S, BTC, BZ, NKD, PA, PL, SR3 — so the universe did not shift under the new
resolution.

## 2. Two legs, and the "23×" I quoted in ADDENDUM 15 was wrong

That figure was the **raw eligible bar count**, not a power claim; adjacent candidates share
nearly all of their window. Corrected before the run, and the study splits accordingly:

| leg | params | eligible bars/session | what it measures |
|---|---|---:|---|
| `bar` | H=10, TAU=20, W∈{0,10,15,20}, stale 10 | **350** (was 14) | same construction, 5× finer *scale* |
| `clock` | H=50, TAU=100, W∈{0,50,75,100}, stale 50 | **70** | same wall-clock *trade*, denser sampling |

## 3. The four predictions: two confirmed, one refuted, one split

### P1 — CONFIRMED. `clock` reproduces the 5-minute trade

Predicted micro market gross in [−3.5, −0.5]. **Measured −$2.29** (the 5-minute comparable was
−$3.23). The clock leg is the same trade and behaves like it, which is what licenses reading the
`bar` leg as a change of scale rather than a change of construction.

### P2 — REFUTED, and the reason is the more interesting result

Predicted `bar`'s cost/payoff worse than `clock`'s by a factor in [1.8, 2.7]. **Measured 1.52×**
(23.6% against 15.5%). I derived the prediction from σ ∝ √t; the fixture says otherwise:

| leg | target $ | \|y\|/σ at fill | implied σ |
|---|---:|---:|---:|
| `bar` (10-bar window) | 18.20 | 3.05 | 5.97 |
| `clock` (50-bar window) | 27.33 | 2.55 | 10.72 |

σ rises by **1.795×** for a 5× longer window, not 2.236×. **Intraday σ scales as t^0.36, not
t^0.50, over the 10→50 minute range.** That is sub-diffusive — it *is* the mean reversion, read
off the variance scaling instead of off a trade, and it independently corroborates the premise
this whole study has been chasing through P&L. It also means a finer scale is materially cheaper
to trade than a random walk predicts, which is why P2 came in low.

Note also that realised depth differs by scale: \|y\|/σ at the fill is **3.05** on `bar` against
**2.55** on `clock`, off the same 2.0σ floor. The finer scale overshoots its threshold more —
the spike behaviour ADDENDUM 10 identified, now visible as a scale effect.

### P3 — SPLIT. Resolved on `bar`; **still degenerate on `clock`, for a different reason**

The degeneracy test (signal count per W; adjacent W must differ by >1%):

| leg / cut | W ladder | steps | verdict |
|---|---|---|---|
| `bar` q25 | 25,238 → 54,826 → 61,028 → 65,250 | 117%, 11.3%, 6.9% | **RESOLVED** |
| `bar` q10 | 10,819 → 30,565 → 36,455 → 41,275 | 183%, 19.3%, 13.2% | **RESOLVED** |
| `clock` q25 | 1,262 → 2,967 → 3,012 → 3,012 | 135%, 1.5%, **0.0%** | STILL DEGENERATE |
| `clock` q10 | 359 → 1,284 → 1,306 → 1,306 | 258%, 1.7%, **0.0%** | STILL DEGENERATE |

**The clock leg's degeneracy is coverage saturation, not bar scarcity** — a different mechanism
from the 5-minute one, and it should have been predicted. At q=25 a 75-bar look-back contains no
fire bar with probability 0.75²⁵ ≈ 0.08%, so W=75 and W=100 are the same experiment. This is
ADDENDUM 14's C1 confound reappearing on a new axis, and it generalises:

> **The grace window is only studiable where W × q is small enough that coverage does not
> saturate.** No quantity of data fixes a saturated window; only a tighter cut or a shorter
> window does. The `bar` leg satisfies the condition, the `clock` leg cannot at any sample size.

### P4 — CONFIRMED. The grace window is worth about $0.20 and has a ten-minute shelf life

`bar`, micro, market entry, gross $ per trade:

| cut | W=0 | W=10 | W=15 | W=20 |
|---|---:|---:|---:|---:|
| q25 | −0.62 | **−0.42** | −0.49 | −0.54 |
| q10 | −0.34 | **−0.15** | −0.21 | −0.23 |

**+$0.20 at W=10, peaking there and decaying after** — positive, well under $1, exactly as
predicted. The decay is new and quantitative: the forecast has a genuine **~10-bar (10-minute)
shelf life**, and holding it longer admits worse trades. On the 5-minute fixture this shape was
invisible because W=15 and W=20 were the same experiment.

## 4. The best cell D528 has produced, and why it still does not count

`bar` / micro / market / q10 / W=10: **gross −$0.15 on 19,460 out-of-time trades**, net −$4.46,
cost/payoff 21.3%, and a **+$0.57** margin over its count-matched control — the largest control
margin in the study on a large sample. In the book lens at q10/W=0, 1 slot: **gross −$0.03** on
5,831 trades, Sharpe_gross −0.01.

Gross is essentially zero at scale. **By the standing rule — a signal is a positive gross mean
per trade above the nulls, and "beats the control" is empty below zero — this is not a signal.**
It is the cleanest statement yet of what the construction actually is: after the stop-and-target
geometry the market pays **nothing** gross, and the entire deficit is the $4.31 round trip
against a $20.24 perfect payoff.

## 5. `stop_retrace`: conservation for the seventh time, and it inverts across scales

`bar`, micro, q10/W=10: ysig 2.97 → **yfill 2.07**, so **31% of the move surrendered**; P(target)
14.8% → 24.6%; gross −0.15 → **−0.76** (worse). Seventh appearance.

But on `clock` it goes the other way: q25/W=0 `stop_retrace` 0.50 lifts gross from −2.29 to
**−0.92**, with a control margin of **+$1.63**. The reason is in the delay columns —
the retrace costs 2.54 bars of a 10-bar window (**25%** of the move) on `bar` but 6.80 bars of a
50-bar window (**14%**) on `clock`. **Confirmation is worth having only where it is cheap
relative to the window**, which is a scale statement, not a verdict on the order type.

## 6. Both lenses, and they invert — which is the reason both were asked for

| leg / cell | slots | n | expo | gross $ | net $ | Sh_n | maxDD | ×limit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `bar` market q10 W=0 | 1 | 5,831 | 0.3% | **−0.03** | −4.37 | −1.35 | 25,459 | 12.7× |
| `bar` market q10 W=10 | 1 | 14,373 | 1.0% | −0.19 | −4.54 | −2.08 | 65,261 | **32.6×** |
| `bar` market q25 W=10 | 1 | 23,310 | 1.7% | −0.42 | −4.77 | −2.53 | 111,280 | **55.6×** |
| `clock` market q25 W=0 | 1 | 602 | 0.1% | −2.57 | −6.83 | −0.58 | 4,477 | **2.2×** |

**The per-trade lens prefers `bar` by 15× (−0.15 against −2.29); the book lens prefers `clock` by
15–25× on drawdown (2.2× the limit against 32.6–55.6×).** They are not in conflict — frequency
multiplies whatever the per-trade expectancy is, and this expectancy is negative, so trading 24×
more often converts a small per-trade deficit into a catastrophic equity curve. Exposure is
0.1–1.7% throughout: the book is almost never on, so no Sharpe here is a component candidate
regardless of sign.

**The rule this establishes: at a negative net expectancy, a finer scale is strictly worse no
matter how much better its per-trade number looks.** A per-trade improvement only becomes a book
improvement after gross clears cost, and it has not.

## 7. Four scale-change defects, three of them silent under slightly different arithmetic

Every one was caught by an assertion rather than producing a wrong number, and each cost a run:

1. **`fit_win`'s design matrix.** `T_LOC`/`T_BAR`/`STT` are derived from `H` at import, so
   rebinding `R.H` for the clock leg left the matrix at width 10. It raised a broadcast error —
   the *lucky* outcome. Had 50 divided 10 it would have fitted the wrong design matrix to 49
   million bars and printed a plausible result. Fixed with `R.set_h()`.
2. **`tod_and_vol`'s profile stack** is allocated at a hardcoded session width of 84; both legs
   died on `(420,) into (84,)`. Fixed with `d528_wide.set_session(width, base_w, min_bars)`,
   which moves all three session-shaped constants together.
3. **The self-test that could not fail.** Check `[4]` printed the eligible-bar arithmetic and
   declared itself satisfied while never calling `tod_and_vol` — so it passed on a runner that
   could not complete one session. Replaced with `[4b]` (the profile on thirty real-shaped
   420-bar sessions) and **`[4c]`**, which puts the 84-bar width back and asserts it raises, so
   `[4b]` is demonstrably capable of failing.
4. **`causal_features` was 89% of the study cost** at 420 bars (3.82 ms of 4.28 ms; 9.4 min a
   pass). Its two per-bar loops are now vectorised where the window is constant-length and kept
   as loops where it is clipped: **6.1× faster, bit-identical** on 15 cases spanning smooth,
   tie-heavy and flat paths at n=60…421, wired into the module's self-test with a companion check
   that the comparison *rejects* a one-bar-different baseline window.

**The lesson is about the surface, not the study: bar-width assumptions live in module-level
constants in at least four separate places, and a scale change reaches them only if something
enumerates them.** Two of the four would have been silent under slightly different arithmetic.

## 8. Disposition

1. **The grace window is resolved and it resolves negative.** +$0.20 a trade at a 10-minute shelf
   life, against a $4.31 round trip. It is real, it is measurable at 19,460 trades out of time,
   and it is an order of magnitude short.
2. **`bar` is the only scale at which the axis is studiable**, and `clock` cannot be made so —
   coverage saturates for any W × q that admits a useful window.
3. **Gross is zero at scale.** −$0.15 on 19,460 trades, −$0.03 in the book lens. The construction
   is entirely a cost story and there is no remaining execution route: ADDENDUM 13 closed the
   passive entry (13× what it saves), and $3.00 of the $4.31 is immovable commission.
4. **A finer scale is strictly worse for the book while gross is negative** — 32.6–55.6× the
   trailing limit against `clock`'s 2.2×.
5. **No component line, no promotion.** Best book Sharpe on this fixture is −0.58 at 0.1%
   exposure. The axis remains the principal's to close.

**Withdrawn:** the "23×" power figure from ADDENDUM 15 (it was a raw bar count), and the σ ∝ √t
assumption behind P2.

**New and worth carrying beyond D528:** intraday σ scales as **t^0.36** over 10→50 minutes on
these roots — a variance-ratio statement, independent of any trading rule, and the first
corroboration of the reversion premise that does not route through a P&L.

**Outstanding for the principal:** whether the reserved slice (2026-04-11 → 2026-09-09) is
considered spent after five months of it were read in the ADDENDUM 12 defect.
