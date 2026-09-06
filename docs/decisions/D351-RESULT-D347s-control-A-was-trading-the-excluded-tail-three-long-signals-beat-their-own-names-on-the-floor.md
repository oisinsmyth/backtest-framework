# D351 RESULT — D347's control A was trading the excluded tail: on the floored universe three long signals beat their own names at random times, and the short verdict stands

**Status:** RESULT. Pre-registered at `c291a7a`, runner at `1fe5101` — both before this file
existed (R8). `keep_v2`, F0, next-open fill, hedged against the floored market, D345's kernel,
cap exit; everything as D347 and D349 ran it except the rotation domain.
**Date:** 2026-09-06
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is a book. Nothing is promoted. D347's headline is withdrawn; D349's stands.**

---

## 1. The verdict

**Four of seven, and the load-bearing one held.** D347's and D349's stored control-A draws
are reproduced to 0.0 from their own seeds by their own code path, and 8–13% of each
signal's rotated events landed off the floor — on the name's own sub-$5 and illiquid
spells — where the forward hedged excess averages **+226 to +318 bp** per forty bars
against +1.7 on the eligible universe. Confined to the floored universe (A′), the control
is a quarter of what D347 reported, and three of its four long signals are above it.

| kernel, cap exit, bp per trade | side | observed | A as run p50 / p95 | **A′ p50 / p95 / max** | above A′ / B / C | timing as stated → **timing′** | off-floor share, mean F |
|---|---|--:|--:|--:|---|--:|--:|
| `hist_L` | long | +60.4 | +70.8 / +90.8 | **+23.9 / +41.8 / +51.6** | **yes / yes / yes** | −10.4 → **+36.5** | 13.1%, +303 |
| `rev_21` | long | +46.5 | +59.6 / +80.1 | **+12.9 / +26.5 / +34.7** | **yes / yes / yes** | −13.2 → **+33.5** | 13.3%, +316 |
| `rsi` turn | long | +16.0 | +45.2 / +60.3 | +6.9 / +28.0 / +37.6 | no / no / no | −29.2 → +9.1 | 10.8%, +226 |
| `rsi` decile | long | +30.4 | +48.0 / +65.8 | **+10.6 / +24.4 / +30.3** | **yes / yes / yes** | −17.6 → **+19.8** | 11.0%, +307 |
| `on_share` | short | −40.9 | −66.6 / −48.5 | −41.4 / −22.3 / −13.6 | no / no / no | +25.6 → **+0.4** | 7.9%, +319 |
| `skew_63` | short | −3.6 | −70.5 / −40.9 | −33.1 / −0.3 / +21.3 | no / no / no | +66.9 → +29.5 | 11.9%, +301 |
| `close_in_range` | short | −11.5 | −56.3 / −46.8 | −22.7 / −16.4 / −11.0 | yes / yes / no | +44.9 → +11.2 | 10.6%, +251 |
| `rsi` decile | short | −1.8 | −67.0 / −54.1 | −35.2 / −23.9 / −9.2 | yes / yes / no | +65.2 → +33.4 | 9.6%, +278 |
| `rsi` turn | short | −18.6 | −69.1 / −50.7 | −37.0 / −20.3 / −17.0 | yes / no / no | +50.5 → +18.4 | 9.9%, +304 |

100 distinct A′ draws each; B and C are the studies' own and are unchanged by this.

## 2. What the defect was, exactly

`rotate_confined` rolls each name's event series within `finT` — every bar on which the
name has a price — and then clears the bars before the hedge is defined. The observed
events are confined to `elig = finT & keep_v2` after that bar. A rotated event on a bar
where the name's as-traded close was under $5, or its dollar volume failed the cut, or its
dollar-volume estimate did not yet exist, is a bar the strategy is forbidden to trade; the
kernel traded it because it checks `finT` and not `keep`. Those bars are the illiquid tail
D339 removed from the universe, and on the names these signals touch they earn +226 to +318
bp per forty bars — the rebounds of cheap names, which D339 found to be every book's top
trade and none of their edge. Eleven to thirteen percent of a long signal's rotated events
landing there is enough to move the control's centre from +24 to +71.

The same defect, on the short side, put the null *short* the tail: D349's control A at −56
to −70 was the cost of shorting those rebounds, and "the timing is real and large" was its
mirror image.

## 3. What changes, study by study

**D347 — headline withdrawn.** `hist_L`, `rev_21` and the `rsi` decile are above A′, B and
C: three of four long signals have timing against their own names on the floored universe,
+20 to +37 bp a trade over a real but modest cohort premium (A′ centred +7 to +24 over a
universe base rate of +1.7). Q1 as D347 pre-registered it is confirmed. The `rsi` turn
remains inside every control. What does not change: D347's interaction reversal (no
rotation was involved), and its cost line — `hist_L` nets **−3.1 after the PUB round trip**
(63.5 bp) and +33.4 after the PB one on the cap exit; nothing nets positive at the published
spread. The edge is real and the published spread eats it, which is where this programme
has stood since D285.

**D349 — verdict stands, numbers withdrawn.** Every short is negative in mean before cost
and none beats control C (Q5 confirmed). "Every one beats its own names by 26 to 67" is
replaced by: `on_share`'s timing is +0.4 and `skew_63` is inside A′; three of five are
above A′ by 11 to 33. The names the shorts touch rise 22 to 41 bp at random eligible
times, not 56 to 70. The mirrors still pay.

**D348 — numbers stand, mechanism withdrawn.** Its rotation was of a score already masked
to the floor, so its null lived in the tradeable universe. The "disagreement" between D347
and D348 that D348 §2 explained by construction was one null being broken. Under A′ the
event ledger and the slot book agree: the long side has timing on both lenses. The finding
that the rank rotation is the harder null on a slot book stands.

**D350 — consistent.** Its grid rotated within `elig`; its 43 of 138 members above A were
the first sign. Its kernel stage now runs both domains and reports them side by side.

**D290 — not re-opened.** Its rotation null rotated the score within each name's live bars
on an unfloored universe, so its null and its universe agreed; nothing here touches it.

## 4. Predictions

| | | outcome |
|---|---|---|
| **Q1** | *(load-bearing)* `hist_L` and `rev_21` above A′'s p95 | **CONFIRMED** — +60.4 vs +41.8; +46.5 vs +26.5 |
| **Q2** | stored A reproduced; off-floor share > 8% and off-floor F > +40 for every signal | **FALSIFIED** on the letter — `on_share` 7.9%; every other signal 9.6–13.3%; every off-floor mean +226 to +319; reproduction 0.0 on all nine |
| **Q3** | A′ for `hist_L` within ±10 of the grid's +25 | **CONFIRMED** — +23.9 |
| **Q4** | shorts' timing shrinks by more than half for every one; ≥ 2 inside A′ | **FALSIFIED** — `rsi` decile shrinks 49%, `close_in_range` 75%, the rest 56–98%; two inside |
| **Q5** | D349's verdict stands | **CONFIRMED** |
| **Q6** | *(against)* some long A′ still centred above +40 | **FALSIFIED** — +7 to +24 |
| **Q7** | both `rsi` references inside A′ | **FALSIFIED** — the decile is above by 6 |
| *check* | counts kept; every rotated event eligible; no NaN | held on every draw |

Four of seven.

## 5. Stop conditions, executed

- **Q1 holds → D347's verdict is withdrawn in writing.** Its record carries the amendment;
  FINDINGS §28 and STACK item 18 are amended; D348 §2's mechanism is withdrawn in its
  record; the memory rule is rewritten. **The pair book's long side reopens** on the event
  lens — `hist_L`/E1, `rev_21`/E1 and the `rsi` decile are real against drift-matched
  controls — and D350's kernel stage says which of its five survivors join them.
- **Q4 partly holds → D349's timing values are withdrawn** and replaced; its verdict
  stands.
- Nothing is promoted. Book: empty.

## 6. Why the assertions missed it

D347's [A] asserted that control A keeps every name's event count and that no rotated
trade carries a NaN; it never asserted that a rotated event is a bar the observed events
could have occupied. The pre-registration said "within its priced bars" and the runner did
exactly that. The tell was in plain sight — a null centred at +45 to +71 over a universe
whose base rate is +1.7 — and this programme wrote a mechanism ("cohort drift"), a scope
claim, and a memory rule on it before asking what the null was trading. The check took one
line on the cached grid. **From here every null asserts that its events satisfy the same
eligibility mask as the observed ones, and reports the share that would not.**

## 7. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | via the shared prep |
| **[R347]** / **[R349]** | the first 5 stored control-A draws of every signal reproduce from the study's seed by its own code path to 0.0 |
| **[OFF]** | dense and sparse off-floor shares agree; the grid equals a direct per-cell recomputation at 200 off-floor landing cells to 2.2e-15 |
| **[A′]** | every draw keeps every name's event count exactly; every rotated event satisfies `elig`; no NaN P&L |
| **[S]** | 300 sampled trades on an A′ ledger equal the open-fill recomputation against the floored market to 0.0, long and short signs |
| **[6]** | [A′] raises on a draw rotated within `finT` |

**Speed:** self-test 13 s; 100 A′ draws in 105–144 s per signal, nine processes at once;
report 2 s.

## 8. What this establishes

1. **On the floored universe, `hist_L`, `rev_21` and the `rsi` decile as long events beat
   their own names at random times, a random same-day same-bucket name, and a random
   direction.** The long side of this programme has timing on the event lens as well as
   the slot lens.
2. **The cohort premium is real and small**: +7 to +24 bp per forty bars over the universe
   for the names these signals touch, not +45 to +71.
3. **No short signal is real**; the shorts' names rise 22 to 41 bp at random eligible
   times, and `on_share`'s timing is zero.
4. **A null must live in the universe the strategy trades.** Eleven percent of a rotation
   landing on the excluded tail was enough to invert a study's headline, and the tail is
   exactly where D339 found the fixture's largest returns.
5. **The published spread still eats the long edge**: `hist_L` −3.1 net per trade under
   PUB, +33.4 under PB. The candidate for the pair book's long trigger is a real signal
   whose tradeability turns on D336's quoted spreads.

## 9. Files

`data/d351_aprime_{d347,d349}_*.json` (nine) · `data/d351_control_a_on_the_floor.json` ·
`scripts/run_d351_control_a_on_the_floor.py` · amendments appended to the D347, D348 and D349
results · the grid check that found it, `temp/d350_rotation_domain_check.py` (temp; its
numbers are re-derived by the runner's self-test)
