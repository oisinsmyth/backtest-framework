# D399 — the ratcheted structural line: a strict two-sided trend state, a line that only widens, and a retracement entry the 15-minute bars resolve

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). **Nothing here is a
result.** No cell scored, no null drawn, no book proposed, nothing admitted (R15).
**Date:** 2026-09-09 · **Area:** signal research · **personal track** · Specified by the principal.
**Number:** D399, the last of this branch's reserved D390–D399 block.

**No holdout testing. Holdout reads spent by this record: 0. Programme total: 1** (D371).

**Build (R16):** **Stage 0** — `us_shorts_daily_raw.csv.gz` via `load_ragged(dividend_bound=True)`,
`keep_v2` floor, F0, next-open fill (D340), `EB.simulate_event` via `run_d359`. **Stage 1** —
`cohort3/cohort4/holdout_intraday_15m` panels, fill convention declared in §7 and **not inherited**.

---

## 0. The construction in one sentence, and the three objects it is made of

**In a name whose structural trend is steep in one direction, hold a line that only ever moves
AWAY from price, and take the trade when price comes back to that line — with the 15-minute bars
deciding where inside the retracement the entry, stop and target sit.**

| | object | what it does | measured? |
|---|---|---|---|
| **1** | **level dead band, δ = 1e-3** | makes the state *strict*: both slopes must clear a 28.7%/yr trend, not merely be positive | **YES** — [D398 amendment 9](D398-RESULT-the-structural-state-is-a-direction-not-a-trigger.md) |
| **2** | **gradient hysteresis, `h`** | the held gradient does not update until a refit moves it by more than `h`. Stabilises the line and suppresses state flicker at the δ boundary | no |
| **3** | **the widening ratchet** | between re-anchors the line's level moves only AWAY from price. **It is therefore NOT a stop** — it defines a zone price can RETURN to | no |

**δ = 1e-3 is fixed by the principal on D398's measurement and is not a free parameter here.**
It was chosen on the frequency it buys — combined state 95% → ~42%, 709 onsets on the 48
15m-reachable names — **before any return was computed, and it will not be swept.** D398 A9.3
records why that matters: the band is a *pure filter*, it creates no onsets, so every value of δ is
paid for in sample and a δ chosen against an outcome would be D366's 164-standard-error mistake
under a new name.

---

## 1. What the record already knows, disclosed before the design rather than after

### 1a. From D398, and it is why the construction is shaped this way

- **The structural state is a DIRECTION, not a trigger.** Even at δ = 1e-3 it is on ~42% of
  addressable bars. **The trendline supplies the sign; the ratchet touch and the overlays are the
  entire selection mechanism.** This record is designed on that basis.
- **`er63` is an empty filter** — ≥0.5 retains 0.2–0.4%, ≥0.7 retains 0.0%. **Dropped, not swept.**
- **The overlays are DIRECTION-NEUTRAL** — UP and DOWN retention agree within ~1 pp on all twelve
  cells measured. **Neither ER nor the volatility band will make the short leg behave differently
  from the long leg.** If the two legs diverge, it is not these overlays doing it.
- **The overlays are INDEPENDENT** — 0 of 108 intersections breached 5 pp. Combined retention
  multiplies, so this record's event count is predictable in advance and §4 predicts it.
- **Survivorship is a ~6% tilt on state FREQUENCY** (dead tilt 1.06 DOWN, 0.95 UP) — **but that
  counts BARS, not RETURN**, and a name that delists delivers a far larger short return than a
  survivor in the same state. **Stage 0 therefore runs dead-inclusive on 1,573 names precisely
  because Stage 1 cannot.**

### 1b. The hurdle D240 already set for a structural line, and it lost

D240 built a sloped stop off this same `(g_lo, i_lo)` pair, with an ATR buffer and a floor — *"the
construction this record spent two amendments getting right"*. Against R7's matched-exit-count null:

| | trades cut | Sharpe | null p95 | percentile | |
|---|--:|--:|--:|--:|---|
| **A1 — structural sloped stop** | 56 of 245 | +0.720 | +0.758 | **89.1st** | ✗ |
| **A2 — flat −8% stop** | 40 of 245 | +0.822 | +0.741 | **99.6th** | ✓ |

> *"The plain stop beat the clever one … The elaborate anchor added nothing over a constant."*

**This record escapes that test only because its line is not an exit.** §3c makes the ratchet an
**entry** object and §5 fixes the exit as a cap. **If any later amendment turns the line into a
stop, A1's 89.1st percentile is the bar it must clear, and a flat stop must be run beside it.**

### 1c. FINDINGS §5's ceiling, and §8's closure

- **§5:** the best of 600 exit levels, chosen with hindsight, improved S1 by **+0.017 Sharpe**; and
  per D256's correction *"a take-profit on these rules is simply a bad exit."* **One row is not
  dead: 61.8% of stop levels beat S2's base, so the effect is HAVING a stop, not a particular
  level.** §5 of this record obeys that: the exit is declared once and not searched.
- **§8** closes *"directional shorts on liquid ETFs"* (D238, D240, D247, D248, D249). **This is a
  single-name universe, dead-inclusive at Stage 0, which is a different instrument class** — but
  the closure is named here so the principal is deciding knowingly. **Only the principal reopens
  an avenue (R15).**

### 1d. R13 — the search already spent on this overlay pair

**D394 Addendum 4 built the volatility × path-efficiency taxonomy and D395 pre-registered its best
cell. The exact best-of-36 label permutation floor killed it: CHOP +28.39 against +31.26 ± 0.13 —
twenty-two standard errors below.** Different universe and different purpose (tail-chopping, not
trend confirmation), so it does not decide this record. **It is disclosed search cost and it is a
warning: this pair of overlays has already produced a cell that looked good and did not survive its
own search floor.**

### 1d′. The STRUCTURE programme's 86 looks, and why this record does not inherit them

**Found while checking for a decision-number collision**, in the R13 ledger of
`D403-the-wick-stack-potential-map-read-at-15-minutes.md` — a **concurrent record on master doing
the same architecture, daily-built and 15-minute-read.** Its ledger lists five prior looks at a
price-level map, and one of them is the module this record is built on.

| | scope | ledger | bears on D399? |
|---|---|--:|---|
| **STRUCTURE, D173 + D204–D211** | the five `STRUCTURE_MODEL.md` components | **86 looks**, CLOSED by D211 | **the components are shared** — see below |
| TERRAIN, D189–D203 | volume-at-price, supply/demand bands | 259 looks, CLOSED terminal | adjacent, **not counted** — a fitted trendline is not a level map |
| D272 / D273 | `dist_hvn` / `dist_lvn` as scores | run and closed | no |

**D211's closure is scope-limited and says so in its own first line:** *"closed on **BTC/ETH 15m
bars** as a source of tradeable directional signal."* And its "What is not closed" is explicit:

> *"The components are reusable and several are pinned by test: the BOS/CHoCH state machine with
> D173's lag, the fair-value-gap detector, the R-unit excursion, and the two matched controls."*

**The programme has already acted on that reading.** D211 closed on 2026-08-24; **D240 admitted S2
to `docs/BOOK.md` on 2026-08-28 using `pivots` from the same module.** Reuse outside D211's scope
is established practice, not a novelty introduced here.

> **THE JUDGEMENT, STATED SO IT CAN BE OVERRULED: the 86 looks do NOT transfer.** D211's hypothesis
> was a five-component discretionary price-action model on crypto 15-minute bars; this record's is
> a two-sided trend state and a retracement on US single names on daily bars. Different hypothesis,
> different universe, different frequency, and the shared detector is explicitly blessed for reuse.
> **This record's R13 count is its own 48 cells (§6). If the principal reads the ledger as
> transferring, the hurdles must be reset before the runner exists, not after.**

**And the concurrent record is flagged deliberately.** D403 and D399 are different objects — a wick
stack read at 15 minutes against a fitted trendline read at 15 minutes — but they share one open
question, **the 15-minute fill convention (§7)**, and it should not be decided twice, differently,
in two live records.

### 1e. Cost, which killed the last thing tried at this frequency

**D247 failed on cost at 15 minutes on 57 ETFs: 334 turnover units per symbol-year, breakeven
0.13 bp against ~1.6 bp charged — a 12× gap.** This construction should turn over far less, being
event-driven rather than signal-flip, **but §6 states the required arithmetic before the runner
exists and no cell may be reported as progress without it.**

---

## 2. The universes, and the holdout problem stated rather than finessed

| | names | dead | used for |
|---|--:|--:|---|
| `us_shorts_daily_raw` | **1,573** | **35.7%** | **Stage 0**, in full |
| the 15m-reachable slice | **48** | **0%** | Stage 1, and reported as a Stage 0 slice throughout |
| `us_shorts_daily_holdout` | 803 | 33.9% | **NOT READ BY THIS RECORD** |

**Two facts carried forward from D398 §1 because they constrain what any result can claim:**

1. **`holdout_intraday_15m` is NOT a holdout for a daily signal.** All 16 of its names sit in the
   daily mining fixture. It is disjoint from cohort3/cohort4 and nothing more. **No section of this
   record treats it as out-of-sample.**
2. **The 15m fixture is survivor-only and cannot be otherwise on this API tier** — 41.6% of the
   2013–2017 cohort is unreachable at that frequency.

> **CONSEQUENCE, DECLARED: this record cannot produce out-of-sample evidence and does not claim
> any.** Stage 1 is measured on 48 survivors that were in the mining universe throughout. **A route
> to R8 exists — fetch 15m for names drawn from the 803, ~38 minutes at 66 calls/min — and it is
> named here as the prerequisite for any future promotion, not done inside this record.**

---

## 3. The construction, frozen

### 3a. The state (δ fixed)

```
On DAILY bars, per name, on its OWN live bars, k=3 / WINDOW=252 / MIN_PIVOTS=3 (S2's, imported):

    g_lo[t], c_lo[t] = OLS fit of log(swing-low  price) on bar index, pivots in [t-252, t-k]
    g_hi[t], c_hi[t] = OLS fit of log(swing-high price) on bar index, same window

    G_lo, G_hi       = the HELD gradients (section 3b)

    UP   := G_lo >  1e-3  AND  G_hi >  1e-3
    DOWN := G_lo < -1e-3  AND  G_hi < -1e-3
```

**The state reads the HELD gradients, not the raw ones.** That is the principal's specification —
*"we do not change the gradient until it is outside a certain dead band"* — and it means the
hysteresis also suppresses state flicker at the δ boundary. §4 Q2 predicts the size of that effect.

**Warm-up: 252 of the name's own live bars**, per D398 §6 — `rolling_fit` clips its window's lower
edge to zero and would otherwise emit a slope on as few as three pivots.

### 3b. The hysteresis, and `h` is NOT a new free parameter

```
    at the name's first eligible bar:  G := g,  and the line is anchored
    thereafter, each bar:
        if |g[t] - G| > h:   RE-ANCHOR   G := g[t],  L := g[t]*t + c[t]
        else:                G unchanged, and the line ratchets (3c)
```

**`h := δ = 1e-3.`** The gradient must move by one dead band's worth to re-anchor. **This reuses the
one constant the principal already fixed rather than introducing a second**, and it is declared
here so it cannot later be tuned. Applied to `g_lo` and `g_hi` independently, since both feed §3a.

### 3c. The ratchet — the line only ever moves AWAY from price

**The operative line is the LOW line in UP and the HIGH line in DOWN**, matching S2's A1, which
also read `(g_lo, i_lo)`.

```
    L[t] = the held line's LEVEL at bar t   (log price)
    l[t] = G*t + c_held                     equivalently

    on a RE-ANCHOR:  L[t] := g[t]*t + c[t]                    the fresh fit
    otherwise:       UP    L[t] := min(L[t-1] + G,  g[t]*t + c[t])
                     DOWN  L[t] := max(L[t-1] + G,  g[t]*t + c[t])
```

**The ratchet operates on the LINE'S LEVEL AT `t`, never on the raw intercept** — with `G` held,
two fits with different intercepts are not comparable at bar 0 in any meaningful way, and
comparing levels at the current bar is the quantity the rule is actually about.

**THE LINE STILL ADVANCES AT `G`, and this must not be misread as a flat line.** The equivalent
offset form makes it plain — reproject the fresh fit onto the held gradient, then ratchet the
offset:

```
    c_cand[t] = (g[t]*t + c[t]) - G*t
    UP    c_held[t] := min(c_held[t-1], c_cand[t])       the offset only ever widens
    DOWN  c_held[t] := max(c_held[t-1], c_cand[t])
          L[t]      := G*t + c_held[t]
```

The two forms are algebraically identical (`L[t-1] + G = G*t + c_held[t-1]`). **So in an uptrend
the line RISES at `G` every bar; what only ever widens is its OFFSET below price.** A line that
literally only moved down or sideways would not be a trendline at all, and asserting `L[t] − L[t−1]
== G` on every non-re-anchor bar is `[R]` in §8.

> **THIS IS NOT A STOP AND THE RECORD SAYS SO ONCE, HERE.** A line that only widens is almost never
> reached from the wrong side. **Its purpose is (i) to mark structural change at its re-anchors and
> (ii) to define a level price can RETURN to.** The exit is §5's cap. §1b is why this distinction
> is load-bearing.

### 3d. The event — a retracement to the ratcheted line

```
    UP   EVENT at t  iff  state UP at t   AND  close[t] <= L[t]      price back to support
    DOWN EVENT at t  iff  state DOWN at t AND  close[t] >= L[t]      price back to resistance
```

**Bar-CLOSE, on information through t−1 for the state and the line, filled at the next open
(D340).** **Intrabar touch is OUT OF SCOPE at Stage 0** and the reason is D394 §2a: the daily
kernel has no high/low path, an intrabar rule needs a new fill convention, *"and a new fill
convention is where D391's look-ahead came from"*. **Resolving the touch intrabar is precisely what
Stage 1 buys, and §7 makes that the thing being tested.**

### 3e. The overlays

`er63` is dropped (§1a). Declared grid, **8 cells**:

| | values |
|---|---|
| ER window | **{10, 21}** |
| ER threshold | **{0.3, 0.5}** |
| volatility band `\|rvol21 / SMA300(rvol21) − 1\| ≤ X` | **{0.25, 0.50}** |

**PRIMARY, declared now: `er10 ≥ 0.3` AND `band ≤ 0.25`.** The least restrictive ER cell, because
D398 showed the state itself already selects nothing and the events are the scarce resource.
**All eight are reported (R14) and H1 is a best-of-8 floor (§6).**

---

## 4. Stage 0 — the premise, and it can fail in twenty minutes

**Stage 0 is DAILY ONLY, on all 1,573 dead-inclusive names. It reads no 15-minute bar.**

**Its first output is the event count**, because §3c's line may simply never be touched:

> **KILL CONDITION K0: if the PRIMARY cell yields fewer than 400 events per direction on the
> 1,573, the construction is not measurable as specified and the record stops and says so.**
> Widening the grid to rescue it is forbidden — that is D366's search and D393 §9 names its price.

Then, per direction, per cell, the four groups (CLAUDE.md), the D392 atlas floor for the observed
trade count looked up with `run_d392_base_rate_atlas.lookup` — **which now has no gaps at cap 5 or
cap 1** (D392 Addendum 2) — and the exposure arithmetic.

### Predictions, six, and three are against the construction

| | prediction |
|---|---|
| **Q1** | *(against)* **the ratcheted line is rarely touched**: the primary cell yields **fewer than 3,000 events per direction** on the 1,573, against ~2.5 M state-bars |
| **Q2** | hysteresis at `h = 1e-3` **cuts episode count by more than 15%** and **raises median episode length by more than 15%** against D398's raw-gradient state, while moving frequency by **less than 3 pp** |
| **Q3** | *(against)* **gross per trade does not clear the atlas floor on the SHORT side.** FINDINGS §30 and §39: every short signal beats its own names at random times and still loses, and the loser decile rises |
| **Q4** | the LONG side clears its atlas floor at the primary cap, but by **less than 2×** |
| **Q5** | *(against)* **the best of the 8 cells sits inside its own best-of-8 floor** — the grid explains itself |
| **Q6** | **dead names carry more than 25% of the SHORT side's gross P&L** while holding only ~20% of the addressable bars — the return-side question D398 Q6 explicitly could not answer |

**Q6 is the one that decides whether Stage 1's short leg means anything.** If the short side's P&L
is concentrated in names that delist, **a Stage 1 short measured on 48 survivors is measuring
something else**, and the record must say so rather than report a number.

### Stage 0 kill conditions

- **K0** fires (§4 above) → stop.
- **The primary fails to clear its atlas floor on BOTH sides** → stop; no nulls are drawn.
- **Q5 holds** (best cell inside its best-of-8 floor) → the search explains the result; stop.
- **Stage 1 is NOT authorised by this record.** It requires the principal's explicit release.

---

## 5. The exit, declared once and not searched

**Cap only.** `cap ∈ {5, 10, 20}` bars, **primary cap 10**, plus **"state ends"** reported beside
them as a fourth, non-primary exit.

**No stop and no take profit at Stage 0**, and the reason is measured rather than stylistic:
FINDINGS §5 — the best of 600 levels chosen with hindsight was worth **+0.017 Sharpe**, and on
single names *"all nine take-profit cells still hurt"*. **The caps match D393/D394's so the atlas
floors exist without interpolation.**

> ### AMENDMENT 5a, 2026-09-09, AFTER THE FIRST STAGE 0 RUN — THE CAP WAS MINE, NOT THE PRINCIPAL'S
>
> **The principal's specification was *"entries, stop losses and take profits at the 15m
> timeframe"*. It contains no cap. I introduced one, made it PRIMARY, and relegated "the state
> ends" — the natural daily analogue of a construction whose exits are all 15-minute objects — to
> a non-primary line that the first runner then did not compute at all.**
>
> **What this contaminates, named precisely:** §2a of the RESULT reports **14 of 16 cell-families
> as HOLD-DRIVEN** and rests the cost verdict on it. **That is a statement about MY cap grid, not
> about the principal's construction.** Under a state-end exit there is one hold, so
> cost-amortisation-versus-edge does not arise in the same form.
>
> **What it does NOT contaminate:** the look-ahead correction (§0), the event counts (§1), the
> atlas comparison at fixed caps, and **Q6's 72.4%** — that last is a P&L attribution and holds at
> every cap tested (42.8 / 72.4 / 53.9%).
>
> **THE STATE-END EXIT IS PROMOTED TO PRIMARY** and run. Declared before it is computed:
>
> - **Exit when the state ends**, i.e. the bar the held gradients stop clearing ±δ. Implemented
>   through the kernel's `invalidation` mode with a score encoding the state, **lagged like the
>   mask** (`score_T[t]` is what is known at the close of `t−1`), and a nominal cap of `T` so the
>   cap never binds. The realised hold distribution is reported, not assumed.
> - **The caps stay, reported beside it**, because they are what the atlas can floor.
>
> **AND THE HONEST LIMIT, STATED BEFORE THE NUMBER: THE ATLAS CANNOT FLOOR THIS EXIT.** D392
> measures a **fixed-cap** random book; its grid runs to cap 60 and `lookup` raises beyond. D398
> measured the median episode at δ=1e-3 as **122 bars held (UP)** and 65 (DOWN), so a state-end
> book sits outside the grid *and* has a variable hold the grid's cap axis does not describe.
> **The cap-60 floor is reported AS THE NEAREST, saying so (D392 §5's own rule), and it is not a
> pass.** A state-end book's proper comparator is a **matched-hold** null — A′ or B_s — which is
> H4 and is not spent unless H3 clears.

---

## 6. Hurdles

| | |
|---|---|
| **H1 — the search** | the best of the 8 cells must clear a **best-of-8 floor** computed within each draw, as D367/D373/D393 build theirs. **A single-cell p95 is not this record's floor** |
| **H2 — the atlas** | gross per trade above `lookup(trades, cap, side)`'s p95, **with the 2-SE UNRESOLVED band applied** (D369/D373): a margin inside 2 SE is UNRESOLVED, not a pass |
| **H3 — cost** | **gross ÷ 2c ≥ 1.0**, with `2c` from Corwin–Schultz on the names actually HELD (D285), reported net and gross side by side |
| **H4 — nulls** | **only if H1–H3 clear**: A′, B_s and C, per D393's battery. **Nulls are not spent on a cell that has not cleared the cheap bars** |

**R13 disclosure carried by this record: 8 cells × 3 caps × 2 directions = 48 Stage 0 cells**, plus
D393's ten and D394's 126 already on the programme's ledger.

---

## 7. Stage 1 — and its PRIMARY test is whether 15 minutes earns its place at all

**Not authorised by this record.** Specified here so the mechanism is declared in advance.

**THE MECHANISM, STATED: 15 minutes buys resolution INSIDE the retracement zone** — where in the
touch the entry sits, how tight a stop can be without being noise, and whether a target is
reachable within the session. A daily bar cannot resolve any of that; 26 bars a session can.

> **PRIMARY COMPARISON: the SAME construction, same events, at DAILY-close fills versus 15-MINUTE
> fills. If the 15-minute layer does not beat the daily one, the intraday layer is unjustified and
> the record says so.** That is a like-for-like test, and it is the only one that isolates what the
> frequency itself is worth.

**Two things Stage 1 must decide explicitly rather than inherit:**

1. **The fill convention**, which D394 §2a and D391 both say is where look-ahead enters. Declared
   at Stage 1, with its own lag audit.
2. **The cost model. Corwin–Schultz is a DAILY-OHLC estimator** and its assumptions do not survive
   a 26-bar session. **A 15-minute spread estimate is a decision, not an inheritance**, and D285 is
   the record of what guessing costs — a guessed 15 bp/side missed by 0.65 against 33.8 measured.

---

## 8. Assertions the runner must carry

- **[S2]** the state's slope grids reproduce `run_uptrend_onset`'s path bit-identically at δ = 0
  and `h` = 0 — the pin D398 already carries, re-asserted so this record's ragged scatter is proved
  and not assumed.
- **[D0]** at δ = 0 and `h` = 0 the state reproduces **D398 §1 bar-for-bar** on all four cells.
- **[R]** the ratchet is **monotone between re-anchors**: the offset `c_held = L[t] − G·t` moves
  only in the widening direction (non-increasing for the low line, non-decreasing for the high
  line), asserted over the whole grid, so a line that crept toward price would raise.

> **TWO CORRECTIONS TO THIS SECTION, made in writing before the runner existed rather than
> silently:**
>
> 1. **`h` = ∞ was written where `h` = 0 is meant**, in both [S2] and [D0]. `h` = ∞ means
>    `|g − G| > h` is never true, which **freezes the gradient at its first value forever** — the
>    opposite of the control. **`h` = 0 re-anchors every bar, so `G ≡ g`**, which is what
>    reproduces D398 and S2.
> 2. **[R]'s "`L[t] − L[t−1] == G` exactly" was wrong** and contradicted §3c's own `min`/`max`. The
>    line advances at exactly `G` **only when the fresh fit does not widen it further**; when the
>    ratchet binds, `L` drops below `L[t−1] + G`. **The invariant that actually holds is the offset
>    monotonicity above**, and that is what is asserted.
- **[L]** the state, the line and the event at bar `t` recomputed from a panel **truncated at `t`**
  equal their full-panel values; `lag_audit.raises_on_broken` on a shifted grid.
- **[X]** the self-test RAISES on (a) a ratchet allowed to move toward price and (b) an event
  condition reading bar `t`'s own close.
- **[W]** no state bar precedes a name's own 252nd own-live bar.
- **[E]** every event sits on an eligible bar (D351).
- **[P]** the JSON persisted **before** it is rendered (D371; D391 repeated it).
- **Four groups** on the primary, with **the top trade named and its bar printed** (D322).

---

## 9. What this record will NOT do

- **It will not admit anything.** Clearing a hurdle is not admission (R8, `docs/BOOK.md`).
- **It will not read the holdout**, at either frequency.
- **It will not sweep δ, `h`, the caps, or the overlay grid** to rescue a failing cell.
- **It will not turn the line into a stop** without meeting §1b's A1 hurdle in a new record.
- **It will not run Stage 1** without the principal's explicit release.
- **It will not open or close a research avenue (R15).**

---

**Status footer.** No runner exists. `docs/BOOK.md` holds S1 and S2, neither at capital;
`docs/BOOK_PROP.md` is empty. Nothing here is a result.
