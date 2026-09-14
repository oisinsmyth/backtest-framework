# D528 ADDENDUM 13 — the corrected chain, and why a passive entry costs 13× what it saves

Date: 2026-09-15. Runners: `working/d528_corrected_chain.py`, `d528_confirmation_entry.py`.

**Nothing admitted (R15). Reserved slice NOT read.** Wide 5-minute fixture, 2010 → 2026-04-10,
corrected entry chain (`slope_ok` dropped, drift alignment kept — ADDENDUM 12). Every figure
out-of-time: cuts from 2010–2019, evaluated on 2020–2026.

---

## 1. The corrected chain worked — it made the study reliable, and the answer did not change

**34,084 candidates against 2,834 — 12×, as predicted.** And the defect that invalidated every
previous cell is gone: **top-3 concentration is now 0.9–5.4%**, down from 22–46%. This is the first
properly-sampled measurement in D528.

Micro universe (the only tradeable one), 10,256 candidates, mean cost $4.58:

| target | frame | forecast | n | P(target) | win% | gross $ | net $ | median $ | control |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| level | frozen | off | 10,256 | 26.8% | 31.1% | −2.36 | −6.94 | −6.0 | |
| level | drift | off | 10,256 | 21.3% | 28.3% | −1.90 | −6.49 | −5.0 | |
| reflect | frozen | off | 10,256 | 14.0% | 23.8% | −1.80 | −6.39 | −7.5 | |
| reflect | drift | off | 10,256 | 10.0% | 22.6% | −1.35 | −5.93 | −6.0 | |
| **reflect** | **drift** | **ON** | 5,870 | 11.7% | 21.7% | **−0.97** | **−5.57** | −5.0 | **median \*** |

**The forecast is significant on the median in all eight forecast-ON cells** (\* = above the
matched control's p95), on 5,870 trades, out of time. It lifts P(traverse, price-referenced) from
14.7% to **19.0%**.

**And it is worth +$0.38 per trade against a $4.58 cost — about 8%.** The first honest measurement
in this study was +$0.50 against $4.68, or 11%. **Nine addenda, a 12× sample, a corrected chain, a
vindicated drift rule and a genuine forecast have moved 11% to 8%.** It has not moved.

`reflect` + `drift` is confirmed as the best target/frame, so ADDENDUM 5's two exit changes survive
the corrected chain and the level-chasing re-test. The book remains uninvestable: best micro
configuration Sharpe net **−0.86**, maxDD **16.5×** the $2,000 trailing limit; all-roots 92–256×.

## 2. The confirmation entry: both readings fail, and the passive one fails instructively

The principal specified: wait for a close beyond σ, then rest an order and let the retrace trigger
it, stale after 5/10 bars. That description is ambiguous in a way that matters, so **both readings
were built** rather than one guessed. For a short at the high extreme:

| mode | rests | fills when | entry cost |
|---|---|---|---|
| `limit_deeper` | **above** the market (a sell limit) | price extends further | **half** crossing + $3.00 |
| `stop_retrace` | **below** the market (a sell stop) | price turns back | full crossing + $3.00 |

Micro universe, out of time, staleness 10:

| mode | offset | fill% | P(target) | win% | gross $ | net $ |
|---|---:|---:|---:|---:|---:|---:|
| **market** (baseline) | — | 100% | 9.9% | 22.4% | **−1.26** | **−5.86** |
| `limit_deeper` | 0.50σ | 71.8% | **2.5%** | 13.0% | **−11.82** | −15.61 |
| `stop_retrace` | 0.25σ | 78.6% | **25.0%** | 28.0% | −3.17 | −7.77 |

### 2.1 The passive entry's adverse selection is structural, not a cost adjustment

It was reported to the principal that passive fills would be "optimistic by an unknown amount"
because adverse selection was unmodelled. **That framing was wrong by an order of magnitude.**
Adverse selection here needs no modelling at all — **the fill condition IS the adverse selection.**
A resting limit placed deeper into the extreme only fills when price keeps going, so it
systematically selects the excursions that did **not** revert.

P(target) collapses from **9.9% to 2.5%**; gross from −$1.26 to −$11.82. No offset (0.25/0.50/1.00)
or staleness (5/10) rescues it.

**The arithmetic of the error: the spread saving is ~$0.79 per trade; the selection damage is
~$10.56. A factor of thirteen.** Rule to carry: **a passive entry placed in the direction of the
move cannot be costed as "market minus half the spread"** — the fill condition must be simulated,
because it selects the outcome.

### 2.2 `stop_retrace` does what it was designed to do, and still loses

Waiting for the turn genuinely confirms reversion: **P(target) more than doubles (9.9% → 25.0%)**
and the win rate rises (22.4% → 28.0%). But gross is *worse*: −$3.17 against −$1.26 — because part
of the move has been surrendered to obtain the confirmation, so the remaining distance to the
mirror is shorter while the stop sits closer.

**That is the conservation of hit × payoff for the fourth time in D528** — after the stop ladder
(ADDENDUM 4), the geometry sweep (ADDENDUM 7) and the forecast (ADDENDUM 12). The dial moved 2.5×
and the product did not.

The forecast helps only the market entry (−1.26 → −1.03) and actively **hurts** `stop_retrace`
(−3.17 → −3.64).

### 2.3 One self-test that could not fail, found and fixed

The first version of the mode test used **monotone ramps**, on which `stop_retrace` can never fill
by construction, and carried **no assertion** — so it printed OK on a check incapable of failing.
Replaced with an extend-only fixture and an extend-then-retrace fixture, with the expected fill
pattern asserted in both directions. A second iteration of that fixture also failed on its own
geometry (the pullback did not reach back through the signal price inside the staleness window),
which is recorded in the code so the next reader does not repeat it.

## 3. Disposition

1. **The corrected chain is the baseline for all future work on this fixture.** `slope_ok` stays
   dropped; drift alignment stays.
2. **Best known configuration: market entry, mirror target, drift-carried exits, forecast on.**
   Gross −$0.97, net −$5.57 on micro. Nine ideas tested across two days and **the entry we started
   with is still the best entry.**
3. **The passive-cost route is closed.** It attacked the correct constraint — cost binds, and
   $3.00 of $4.58 is immovable commission — but the only part execution can reach is the ~$0.79
   crossing half, and reaching for it costs 13× what it saves.
4. **No component line, no promotion.** The axis remains the principal's to close.

**Open:** a depth × confirmation sweep is running on the principal's hypothesis that a deeper
extreme may decouple hit rate from payoff. A prediction is on record in that runner's docstring —
that `hit × payoff` on gross stays flat while `cost / payoff` falls, so any net improvement is cost
amortisation rather than decoupling. The grace-period idea (a forecast valid for 10/15/20 bars) is
sidelined at the principal's instruction.
