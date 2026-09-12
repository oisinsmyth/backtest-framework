# D405 PRE-REGISTRATION — the capital-gains overhang: a price-level map of shares still held

**R8: committed before the runner exists. Result separately.**

**Number.** `D405`, taken by PICKUP's three-command procedure at commit time and not before — which
is not pedantry. `D390` was taken twice in one hour on 2026-09-09 by a session that checked
`ls docs/decisions/`, and **`D404` was taken by another session while this document was being
drafted.** `git log --all` shows D400–D404 used and nothing at D405+; the only reserved block is
`D390–D399` (`945cbb5`, `worktree-signal-hunt-part2`, live). Both branches were active when this
number was claimed, so it was committed immediately to stake it.

**Drafted before it was numbered.** This document existed in full, and was reviewed by the principal,
as `DRAFT-capital-gains-overhang.md` before any number was attached. Two of its design decisions —
§2 and §3.1 — are the principal's, in response to the draft.

Nothing here has been run. No fixture has been touched for it.

---

## 1. The thesis

D403 closed on a diagnosis, not just a failure:

> A wick is evidence that interest was **absorbed**, not that it **remains**. If price spiked to 110
> and came back, the sellers at 110 were filled — the zone is spent.

Six programmes built maps out of completed trading and read them as forecasts of trading to come.
Supply and demand, forward-looking, is **unfilled interest**: orders resting, or holders with a
reason to transact. We cannot see the book (§9), so this takes the other route — **holders with a
reason.** The disposition effect is that reason: investors are reluctant to realise losses, so shares
bought above the current price sit as overhead supply until they are worked off.

**The mechanical discriminator, which matters more than the story.** All six failures were pure
functions of the past price path, which is exactly why a rotation control killed them: rotating
preserves the path and destroys only the alignment, and the alignment carried nothing. **This
construction is not a function of the price path alone** — two identical price paths with different
volume histories give different maps. That is testable in minutes and §6.1 makes it the first thing
measured.

**Not previously built here.** TERRAIN's `PriceDensity`
(`src/backtest_framework/research/terrain.py:91`) is a **flat-window** normalised mass over price
buckets — every bar in the lookback counts equally and nothing decays. There is no work anywhere in
the repo on overhang, the disposition effect, or turnover-weighted inventory. **The decay kernel is
the whole difference** (§3.3).

---

## 2. "MASS" IS SHARES. THERE IS NO GRAVITY HERE.

**Mass means the number of shares still held whose purchase price sits at `p`.** It is an accounting
quantity. It is not a field, it exerts no attraction, and there is no potential.

**This is stated as a constraint because the physics metaphor has already cost this programme once.**
D403 was framed as a "potential energy map", and that framing smuggled in a mechanism — wells,
barriers, Boltzmann occupancy — which then determined the test. An occupancy study was built and run
before anyone checked the object was a potential. It was not: 0 of 4 names monotone in every cell.

**If an analogy is wanted, it is a CONTACT REACTION, not gravity.** Gravity acts at a distance;
underwater holders do nothing until price arrives at their entry. The distinction is not decorative —
it determines the test:

| framing | prediction | status |
|---|---|---|
| **distance** (gravity, potential) | price is drawn toward / repelled by high-mass regions wherever it currently is | **tested in D403, flat** |
| **contact** (this draft) | nothing happens until price ARRIVES at the level, then supply appears | untested |

§6.4 conditions on **arrival**, not on state, and that is the single most important structural
difference from all six prior looks.

---

## 3. THE CONSTRUCTION

### 3.1 Where the mass goes within a bar — the candle's own quantiles

Day `u` traded `V_u` shares somewhere inside `[L_u, H_u]` and a daily bar cannot say where. **Volume
is not uniform across that range**: wicks are *rejected* excursions where price was brief, and the
body is where the bar opened and closed. So the volume is placed as a piecewise-uniform distribution
whose knots are the candle's own structure:

```
[L,        body_bot]     q_low  of V      density = q_low  * V / (body_bot - L)
[body_bot, body_top]     q_body of V      density = q_body * V / (body_top - body_bot)
[body_top, H       ]     q_high of V      density = q_high * V / (H - body_top)
```

with `body_bot = min(O,C)`, `body_top = max(O,C)`, and `q_low + q_body + q_high = 1`.

Three properties earn this over a point mass or a flat range:

1. **A point mass gives a comb.** D403's bare wick stack was ~96 disjoint teeth because thin objects
   on a wide axis do not overlap, and repairing it cost a bandwidth. A bar's range has width by
   construction.
2. **It stays piecewise-constant**, so the exact difference-array build survives and **there is still
   no kernel and no bandwidth** — the free parameter D403 had to buy back is never bought here.
3. **It subsumes the wick idea rather than discarding it.** D403's object becomes the tail shape of
   this one, now carrying the size it always lacked.

**Degenerate bars.** A candle with no upper wick (`H == body_top`), or a doji (`O == C`), leaves a
quantile with nowhere to go. **Rule: allocate only to segments of strictly positive width and
renormalise across those.** Zero-range bars (`H == L`) contribute nothing. Malformed bars — the five
in 4,137,239 with `close < low` — are **masked, not clamped**.

### 3.2 The knots are MEASURED, not chosen

`(q_low, q_body, q_high)` is a free parameter, and it does not have to be. **Calibrate it against
observed intraday volume.**

`data/fixtures/etf_intraday_15m_panel.csv.gz` — 57 ETFs, gate-passed, 26 bars a session. For each
session, compute where the day's 15m volume actually sits relative to that day's `L`, `body_bot`,
`body_top`, `H`, and take the empirical shares. That fixes the knots from data rather than from
taste.

- **The ETF panel is used deliberately**: it is not a spendable cohort, so **cohort3 and cohort4 stay
  untouched**.
- The calibration is a **property of the data, not of an outcome** — no forward return enters it.
- It is run **once and committed before the study**, so it cannot be retuned afterwards.
- Uniform-across-range (`q` proportional to segment width) is carried as the **null shape**, and the
  measured shape is reported beside it. If they agree, the elaboration bought nothing and that is
  worth knowing.

### 3.3 The decay — THE POINT OF THE WHOLE CONSTRUCTION

Mass placed on day `u` survives to `t` with probability

```
w_u(t) = PRODUCT over s in (u, t] of (1 - theta_s),      theta_s = V_s / (k * Vbar_s)
```

`Vbar_s` is the trailing mean volume, so `theta` has mean `1/k` and **the map decays in volume-time,
not calendar time.** `k` is a half-life measured in *shares turned over*, not days.

**This is the ingredient no prior map had.** Two names with identical price paths, one with a volume
spike: the spike wipes the older inventory in one and not the other. That is information the OHLC
path cannot carry, and it is why §6.1 can come out negative rather than being a formality.

`k` in {20, 60, 120, 250}, reported as a shape across all four. **No cell is chosen by outcome.**

True turnover is `V_s / shares outstanding` and the repo has no shares-outstanding series. The
relative-volume proxy is the substitute and **its arbitrariness is this construction's main
weakness** — stated here rather than buried. No gate in §6 depends on which `k` wins.

### 3.4 What comes out, and it is SIGNED

Let `F_t(p)` be surviving mass density at price `p` and `P_t` the current price. **Mass above and
below the current price are different populations and are never aggregated** — stock held above is
potential supply from holders sitting on losses; stock held below is held at a profit and behaves
differently. Collapsing them was part of what made D403 mush.

| quantity | definition | what it is |
|---|---|---|
| `OS_t` | mass above `P_t`, over total | share of still-held stock that is **underwater** |
| `SU_t` | mass below `P_t`, over total | the same, in profit |
| `R_t` | mass-weighted mean surviving purchase price | reference price |
| `g_t` | `(P_t − R_t) / P_t` | **capital-gains overhang**, the scalar with a literature |
| `F_t(b)` | surviving mass in band `b` | the **level** read — the zone object proper |

`g_t` is what the literature uses; `F_t(b)` is the level map. Both are carried and both go through §6.

### 3.5 Implementation

The survival weight is multiplicative, so this is a recursion rather than a `T x L` rebuild:

```
F_{t+1} = (1 - theta_{t+1}) * F_t  +  V_{t+1} * bar_shape(L, body_bot, body_top, H)
```

One vector update per bar on a fixed per-name log-price grid — `O(T x gridN)`, roughly 4.2M
operations per name, so the full 1,573-name panel is minutes. Same recursion shape as D384's density,
which is already understood here.

**The grid is a free parameter** (the intra-bar shape is exact; the recursion's axis is not), so
`[GRID]` recomputes every object statistic at double resolution and requires agreement.

### 3.6 Assertions before anything is believed

- **`[SPLITVOL]` — split consistency of VOLUME, not just price.** The fixture is split-adjusted; if
  volume is not adjusted in the same direction, dollar volume jumps by the split ratio on the split
  date and the map plants a fabricated mountain there. Assert `close x volume` is continuous across
  every split in `us_shorts_daily_raw_events.json`. **D403's `[ALIGN]` caught a 5x error of exactly
  this family** — ServiceNow's map at five times its own prices — and nothing else would have seen it.
- `[SHAPE]` — the intra-bar distribution integrates to `V_u` exactly, including every degenerate
  case of §3.1; and the renormalisation is asserted on a doji and on a wickless bar specifically.
- `[MASS]` — `F_t` integrates to the recursively-tracked surviving total, to machine precision.
- `[DECAY]` — a synthetic name with one volume spike loses the predicted fraction of its mass. The
  break must move **that scalar**, not merely the assertion's name.
- `[LAG]` — `F_t` uses bars `<= t-1` only, re-derived by a second implementation that never calls the
  recursion. Killed D279's first result: 93% of its apparent edge.
- `[SPLIT]` — D387's default-deny holdout guard verbatim, no unlock, proved to bite.

---

## 4. R13 — THIS IS LOOK #7

| # | programme | disposition |
|---|---|---|
| 1 | TERRAIN, D189–D203 | CLOSED terminal — 259 looks |
| 2 | STRUCTURE, D173, D204–D211 | CLOSED — 86 looks |
| 3 | D272, D273 — the profile as an input | run and CLOSED |
| 4 | BREAKOUT family | off-thesis, dormant; wedge CLOSED |
| 5 | DENSITY line, D384–D388 | RETIRED by the principal |
| 6 | D403 — the wick-stack potential | **CLOSED by the principal, 2026-09-09** |

**Six programmes, six written closes, none paid.** The ledger transfers in full, and that base rate
is why §6 is a stage-0 discriminator with abandon conditions rather than a study with a sweep.

---

## 5. UNIVERSE

`data/fixtures/us_shorts_daily_raw.csv.gz` via `RP.load_ragged` — 1,573 names, 2010-01-04 →
2026-08-26, dead-inclusive, OHLC **and volume**. Eligibility `elig = finT & keep_v2`. **No holdout is
read**; `us_shorts_daily_holdout2.csv.gz` stays unspent. The ETF 15m panel is used for §3.2's
calibration only. **cohort3 and cohort4 are not touched.**

---

## 6. THE TEST — STAGE 0 IS AN AFTERNOON AND IS PROBABLY THE KILLER

Nothing downstream runs until every gate passes. Each abandon condition is written now.

### 6.1 Does the object contain non-price information at all?

**The cheapest test that separates this from all six failures, and it runs first.** Rebuild the map
with **volume permuted across days within the name**, price path untouched. Correlate the
volume-shuffled `g` and `F` against the real ones.

> **ABANDON if `corr > 0.9`.** The volume is decorative, the object is another function of the price
> path, and it dies where the other six died. **Cost of finding out: minutes.**

### 6.2 Is it an old signal wearing a new name?

Independence against the existing score set, D272's `A1` machinery.

> **ABANDON if `|rho| > 0.5` against any existing score.** D272's `dist_hvn` scored 0.555 and simply
> **was** `impulse_md` renamed — found *after* a full study was built on it. Report the correlation
> with 12-month momentum **explicitly and first**: the overhang's headline use in the literature is
> as a momentum proxy, and this repo has mined momentum to exhaustion (D288's 31-candidate mine).
> That is the specific expected failure.

### 6.3 Does the conditioner persist?

Autocorrelation and half-life of `g_t` and of `F_t` at the current price.

> **ABANDON if the half-life is under one bar.** Conditioning on something that does not persist is
> conditioning on noise. Standing stage-0 premise check.

### 6.4 THE CONTACT TEST — conditioned on ARRIVAL, not on state

Only if §6.1–6.3 pass. **This is the structural break from all six prior looks** (§2).

An **arrival** is price entering a band it has not touched for `N` sessions. On each upward arrival
into a band, measure the forward return, and ask whether arrivals into **high surviving overhead
mass** stall more than arrivals into low-mass bands.

The control is what makes it a test rather than a restatement:

| control | destroys | keeps |
|---|---|---|
| **VOL-SHUF** | the volume information only | the price path **exactly** |
| **MATCHED-BAND** | the mass at the band | the distance travelled and the time since last touch |
| **A′** | alignment of map and price | the real path and the real map |
| N2 / B / B_c | serial structure / house pair | — |

**VOL-SHUF and MATCHED-BAND are reported first.** MATCHED-BAND is not optional: D273 produced a
monotone 62.6% → 1.3% ordering that **any random line reproduces**, because a nearer level is more
likely to be reached. Distance and recency must be held or the result is arithmetic.

Scored on **gross mean per trade** (R15 — cost is engineered afterwards and decides nothing at the
signal stage), both lenses, never on the same statistic (FINDINGS §10). Every rotation confined to
`elig`, never `finT` — D351's defect moved a control's centre from +24 to +71 and inverted a
published headline. Distributions not percentiles: p50 and p95 with the p95's bootstrap SE, margins
inside 2 SE recorded **UNRESOLVED** (D373).

---

## 7. WHAT WOULD MAKE THIS INTERESTING

1. **The volume carries information (§6.1), it is independent (§6.2), and arrivals into high overhead
   mass stall above VOL-SHUF and MATCHED-BAND.** That would be the first price-level object in seven
   looks whose novel ingredient survives its own control.
2. **It is momentum renamed (§6.2 fails).** Expected, cheap, and worth one afternoon rather than one
   study.
3. **The volume is decorative (§6.1 fails).** Then "absorbed vs remaining" is wrong, or not repairable
   with volume, and the supply-and-demand line should close rather than produce an eighth look.

---

## 8. WHAT THIS DOES NOT DO

- No position, no book consequence, no admission. Stage 0 scores nothing.
- **No holdout read.** Default-deny guard, no `allow_holdout`.
- Does not spend cohort3 or cohort4.
- **Does not proceed past a failed gate by loosening it.** D197–D203 ran five refinements, each
  beating its predecessor, none moving the null gap — and the one that fixed the *statistic* produced
  the worst result of the five.

---

## 9. THE HONEST CEILING

This approximates **holders with a reason to trade**. It does not observe **resting orders**, which
is what supply and demand actually is. That needs the book: D336's quoted-spread pull, blocked on the
principal's TWS session and top-of-book only, or Databento, which has a costed plan and no submit
path. Parked in PICKUP §0d2 with options open interest and execution anchors. **If the book becomes
reachable, it outranks this.**
