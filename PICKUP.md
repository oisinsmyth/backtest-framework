# PICKUP - handoff for the next session

**Updated 2026-09-02, end of the session in which the concentrated DAILY short's two survivors
turned out to be look-ahead and were withdrawn.** D264 -> D280, plus standing rule R13.

---

## 0. THE ONE-LINE STATE

**BOTH short branches are now closed. Nothing in this programme currently has a surviving cell.**

- **The INTRADAY single-name short is closed on every lever it has** - D264 through
  [D278](docs/decisions/D278-the-instrument-holdout.md).
- **The DAILY concentrated short is now ALSO closed** -
  [D279](docs/decisions/D279-the-concentrated-short-on-dead-inclusive-names.md), **0 of 14, no
  survivors.** Its first RESULT reported two survivors and **they were look-ahead. Withdrawn.**

Everything intraday closed on one condition, in which the trade count cancels and hit rate never
appears:

```
mean move per trade  >=  2c        (the round-trip cost)
2c = 4.00 bp LOW - 8.42 bp ALL - 12.84 bp HIGH
```

**Six signal families, three input families, a volume profile three ways, two exit levers, a
300-cell mine and a 16-name instrument holdout all failed that bar.** Nothing failed for want of a
null.

**D279 closed on something different and worse: it never reached the cost question.** Re-scored at
zero fees, zero borrow and zero rf, `S1_short|top25` posts **-0.432 Sharpe and -0.26% CAGR**. Every
cell in the grid has a negative net CAGR, every breakeven borrow rate is negative, and the
best-of-14 floor is **-0.178** against a best cell of **-0.337**. **On the daily fixture the binding
constraint is the drift, not the toll.**

**What is live is one pre-registered study and one untouched branch.** See section 5.

## 1. PICK THIS UP FIRST - the D279 look-ahead, because the lesson is a runner lesson

**`run_concentrated_short.top_n` ranked the qualifying names with `score[:, t]` - `hist_L` computed
from the close of the very bar the position was about to be paid for - and then held that position
through bar t's return.**

`hold_book` lags the qualifying MASK correctly and always did (`p[:, 1:] = mask[:, :-1]`), so
**which names QUALIFIED was honest and [D256](docs/decisions/D256-the-book-on-single-names.md) is
untouched.** What was contaminated is **which N of the qualifiers were HELD** - which is exactly the
quantity hurdle C exists to test.

```
corr(hist_L at t,   hist_L at t-1)   +0.9805      the score barely moves when lagged
corr(hist_L at t,   return at t)     +0.0737      ranking on this is peeking
corr(hist_L at t-1, return at t)     -0.0103      the tradeable version

top25   UNLAGGED  +1.43% CAGR  +2.250 SR      LAGGED  -0.32%  -0.638
top50   UNLAGGED  +2.05% CAGR  +1.865 SR      LAGGED  -0.56%  -0.659
```

**THE LESSON, and it is new to the programme: a lagged position built from an UNLAGGED RANKING is
still look-ahead, and the base being correctly lagged is what hides it.** Every look-ahead guard we
own points at `hold_book`, and `hold_book` was right. The defect entered one layer above it, in a
function that *filters* an already-lagged book - a place nothing was watching, because filtering a
lagged book feels like it cannot introduce a lag error. **[R9](docs/RULES.md#r9)'s third appearance**
after D224 and D248, and the second on `hist_L` specifically.

**The fix now lives INSIDE `top_n`**, not at the call site, because three other modules call it.
**One consequence:** re-running `scripts/d279_lookahead_check.py` no longer reproduces its own
UNLAGGED column - its two arms have become lag-1 and lag-2. The correlations still reproduce; the
UNLAGGED Sharpes are only reproducible against the pre-fix runner and are quoted from the withdrawn
artefact, kept as `data/d279_concentrated_summary.WITHDRAWN_lookahead.json`.

**Three further caveats in D279's corrected RESULT, all still live for anything that inherits this
construction:**

1. **Hurdle H is FAILED for that study, not passed.** `S1_short|all` scores the **100th percentile
   on both legs with -0.757 Sharpe and -2.45% CAGR**; seven of fourteen cells clear it and all
   fourteen lose money. [R7](docs/RULES.md#r7)'s corollary applies. **Do not reuse that null
   unmodified.**
2. **Hurdle C is scored against ONE random draw, not a distribution.** The same control cell scored
   **-1.528** in the runner and **-1.633** in the decomposition; at S2/N=50 the gap is 0.16 Sharpe.
   `rotation_nulls` takes 300 draws and C took one.
3. **E' degenerates on a rotating book.** `top25` scored **28.00 on 28 names** - the correlation
   matrix is the identity, because almost no *pair* shares the 250-bar overlap minimum. It silently
   became "how many names were held >=250 bars", on which `top10` scores **1.00 on one name**. **The
   runner still has this defect**; `data/d279_concentrated_summary.json` carries an
   `Eprime_panel_defect` flag on every cell and the honest values are in
   `data/d279_eprime_corrected.log`.

## 1a. THE EDGE IS ENTIRELY OVERNIGHT - [D280](docs/decisions/D280-the-forecast-precheck.md)

**D280 is a MEASUREMENT record - it scores no cell, ranks no name and proposes no rule, and its
ledger is 0.** It ran BEFORE any pre-registration because it decides whether there is anything to
pre-register.

**THE HEADLINE, and it is the largest result of the D264-D280 sequence.** Cross-sectional IC of the
R9-lagged `hist_L` against each PART of the next bar, out of sample. Negative = tradeable for a
short:

```
universe   target       mean IC       t
ALL        total        -0.00524   -1.79
ALL        gap          -0.01531   -4.71     <-- the edge
ALL        intraday     +0.00168   +0.65     <-- nothing
QUAL       total        +0.00462   +1.43
QUAL       gap          -0.01255   -3.45
QUAL       intraday     +0.00868   +2.85     <-- runs AGAINST the short
```

> **There is a real, correctly-signed OVERNIGHT edge and a wrong-signed INTRADAY move that cancels
> it. Close-to-close - the only quantity D256 and D279 ever measured - is the SUM OF THE TWO, which
> is why it read as noise.**

- **No intraday stop, target, partial exit or overlay can reach it**, and taking the position at the
  open to shed overnight risk discards the edge and keeps the leg that fights it. **Both branches
  close on one measurement.**
- **It is NOT ex-dividend drops** - the obvious confound, since `gap` is raw OHLC and a short OWES
  the dividend. Dividend-adjusted the IC is **-0.01498 (t -4.59)**; ex-dates excluded, **-0.01494**.
  Only 0.834% of bars go ex next session. **On those 216 bars the IC is -0.05197**, 3.4x the average,
  so the mechanism is real and localised - **charge dividends explicitly in any book built on this.**
- **AN IC IS NOT MONEY.** An overnight book trades a full round trip EVERY NIGHT - ~252/yr against
  ~17/yr for D279's ~15-day holds - so D265's bar (`mean move per trade >= 2c`, 10 bp at 5 bp/side)
  must be cleared **15x more often**. A rough prior, **not computed from these artefacts**, puts the
  per-night edge near 4 bp against that 10 bp toll. **D282 is pre-registered to measure it. Do not
  predict it.**

**THE STRUCTURAL FINDING, and it is the second thing to carry out of this session:**

> **D256 and D279 both filter on `hist_L < 0 & md_L >= 0` and then rank the survivors by `hist_L`
> again. The filter and the ranking are the SAME VARIABLE. The signal is spent by the time the
> ranking runs, and what remains inside the filtered set reverses.**

Cross-sectional IC - Spearman, within each bar, against the NEXT bar's return, out of sample:

```
hist_L over ALL live names       mean IC -0.00524   t -1.79   2,173 bars   correctly signed
hist_L over the QUALIFYING set   mean IC +0.00462   t +1.43   2,147 bars   WRONG SIGN
```

**That is the whole of why D279's ranking bought +0.203 gross Sharpe on a book sitting at -0.432.**

**What else D280 settled:**

- **The DEMA + velocity/acceleration/jerk extrapolation is dead.** It loses to naive persistence in
  **all 48** level comparisons, all nine delta comparisons and all nine range comparisons.
  Derivatives correct the smoother's own lag rather than forecasting; longer n is monotonically
  worse; jerk hurts in 8 of 12 cells (noise multiplier C(2k,k) = 20).
- **16 OHLC derivative terms carry 13.50-15.76 EFFECTIVE inputs**, not the sub-3 collapse predicted.
  **The intrabar axis is real, independent, and carries no predictive power** - the mirror image of
  D268's lesson, and it belongs beside it.
- **`open(t+1) := close(t)` is NOT free.** Median |gap| **0.5263%**, mean **0.9393%**,
  **|gap|/|body| = 0.515**. Range is separately predictable at correlation **+0.87** and
  persistence-of-range still beats the DEMA stack on MAE, so range is a sizing input at best.
- **Multiplicity: 165 statistics across five parts, 161 distinct.** The median largest |t| under a
  161-test null is **2.86**, so the best *extrapolation* result (**|t| 2.29**) is a best-of and is
  **not evidence**, and the only un-searched baseline (`hist_L` alone, all names, t **-1.79**) is not
  significant either. **The overnight numbers are the exception: |t| 4.71, 5.07 and 5.97 clear a
  best-of-161 correction comfortably**, and part 4's gap leg was declared in the script before it
  ran. **The t is small on 2.2M name-bars because n is 2,173 BARS** - the IC is computed within each
  bar and averaged.

## 2. WHAT WAS CLOSED, AND ON WHAT

| | closed by | on |
|---|---|---|
| S1 / S2 shorts, intraday, single names | D264 | 0 of 12 cells; commission alone beats the breakeven |
| entry timing | D265 | early entries are 1.57× the bar; whole-book +0.38%/yr |
| magnitude calibration, 9 price scores | D267 | 0 of 27; whole Q1–Q5 spread < one round trip |
| the consensus proposal | D268 | 2.87 effective inputs of 9; **RSI is trailing return at ρ +0.78** |
| volume as a third input | D270 | orthogonal at ρ 0.09, best cell 0.92× the bar |
| the volume profile, as an input | D272 | most orthogonal thing measured (ρ 0.085), 0 of 6 |
| the volume profile, as a travel estimator | D273 | travel is flat in room; the node is a distance |
| exits, time-based | D274 | **a random exit bar beats a fixed one** |
| change of character | D275 | legs run 182.7 bp median, the rule captures 0.57 bp |
| exits, structural | D276 | removing churn made it worse; exposure 47% → 4.5% killed it |
| the mine, 300 cells | D277 | best +0.392 against a best-of-300 floor of +0.605 |
| **all five in-sample winners** | **D278** | **every one reverses sign on 16 fresh names** |
| **the concentrated DAILY short** | **D279** | **0 of 14; `top25` is −0.432 Sharpe GROSS, so it loses before costs** |
| the DEMA derivative forecast | **D280** | loses to naive persistence in **all 48** level comparisons, all 9 delta, all 9 range |
| **intraday exit overlays on this construction** | **D280** | **the edge is entirely overnight** (gap IC −0.01531 t −4.71; intraday +0.00168 t +0.65) |
| taking the position at the open to shed overnight risk | **D280** | same measurement, reversed — it discards the edge and keeps the leg fighting it |

## 3. THE FIVE THINGS WORTH CARRYING

1. **The cost bar is `mean move per trade ≥ 2c`, and it is signal-independent.** The trade count
   cancels; hit rate never enters. Any future intraday construction should be screened on this
   first, for the cost of one measurement.
2. **Most technical indicators are monotone transforms of trailing return.** D268: nine scores,
   **2.87 effective inputs**; RSI ↔ macd_line at **+0.85**. "Several indicators agree" is usually
   one indicator agreeing with itself. `scripts/d268_score_independence.py` is the instrument.
3. **Overnight drift is a property of VOLATILITY, not of equities.** Low-vol names accrue it
   **intraday with the sign reversed** (+4.36% overnight vs +5.56% intraday); high-vol names run
   +13.81% vs −8.97%. D247's +8.59%/−0.36% is an average over instruments, not a constant. **This
   belongs in the wide extended-hours pre-registration before it runs.**
4. **A correlation on a continuous score does not survive to its tails.** ρ = −0.83 between
   `mass_imbalance` and `impulse_md` gave only **53% bar overlap** at the quintile extremes — and
   +0.392 against −0.481 Sharpe. I called them "near-identical" and was wrong.
5. **A LAGGED POSITION BUILT FROM AN UNLAGGED RANKING IS STILL LOOK-AHEAD, AND THE BASE BEING
   CORRECTLY LAGGED IS WHAT HIDES IT.** D279's `hold_book` shifted the qualifying mask by one bar
   and always did; `top_n` then chose *which N of the qualifiers to hold* on the unlagged score.
   **Every look-ahead guard this programme owns points at `hold_book`, and `hold_book` was right.**
   Anything that *filters* an already-lagged book is a place to check, precisely because it feels
   like it cannot introduce a lag error. **A second, independent re-derivation of the held set from
   `score[:, t-1]` — not a call into the same function — is the cheap guard**, and D281's runner
   is the first to carry one.

## 4. R13 IS NEW AND IT CHANGES HOW LEDGERS ARE COUNTED

**[R13](docs/RULES.md#r13): a ledger is scoped to a hypothesis and transfers only where it shaped
the search.** Written after the principal pushed back twice, correctly, on inherited counts.

- terrain's **259** is disclosed, not carried (D272)
- the ETF programme's **45,783** is disclosed, not carried — **D218 scopes its own floor to "this
  fixture"**, meaning 57 ETFs daily
- what carries into the single-name work is **~118**, because D264–D276 built the bases and scores

**D247–D276 keep the older single-cumulative convention and are NOT restated.** R13 explains the
discontinuity rather than erasing it.

**And nothing reopened.** Every closure above fired on a hurdle failure, not on multiplicity.

## 5. WHAT IS ACTUALLY LIVE

1. **The wide extended-hours decomposition** — fixture built and gated (`c25218d`), nothing
   decomposed, prediction declared. **Add the volatility split from §3.3 before running it.**
2. ~~A concentrated ranked short on the DAILY dead-inclusive fixture~~ — **RUN AND CLOSED, D279.
   0 of 14.** Its stop fired. Nothing further may be tuned on that fixture.
3. **[D281](docs/decisions/D281-the-unfiltered-ranking.md) — rank the WHOLE universe, removing the
   filter/ranking collision D280 measured and changing nothing else.** Pre-registered before its
   runner existed; **result pending at the time this handoff was written.** It inherits D280's 150
   comparisons under [R13](docs/RULES.md#r13) test 2, because D280 shaped its search space.
4. **[D282](docs/decisions/D282-the-overnight-only-short.md) - the cost arithmetic of the overnight construction** part 4 implies: ~252 round trips a
   year against D265's `2c` bar. **Pre-registered by another agent; result pending. Do not predict
   it.**
5. **The volatility tilt D280 part 4 turned up** — `zh + zv + za + zr` reaches IC **−0.01373
   (t −5.07)** on all live names, the only directional statistic in that record that clears its own
   multiplicity. **It is a volatility tilt, not a stronger `hist_L`** (flip `zr`'s sign and the IC
   goes positive), it does nothing on the qualifying set, `zr` alone was never scored, and no book,
   cost model or `sigma^2` tax has been applied to it. **Needs its own pre-registration.**
6. **The factor-neutral branch of FINDINGS §9** — still untouched after D256, D264, D279 and D280.
7. **Prop track:** rung 2's micro/mini form and rung 3, both free, both untested.
   [D266](docs/decisions/D266-the-prop-cross-screen.md) screened this session's work against
   hurdle P and the best cell earned +0.535%/yr after P1 sizing. BOOK_PROP.md stays empty.

## 6. DATA THAT NOW EXISTS

| | |
|---|---|
| `single_name_intraday_15m_{raw,panel}.csv.gz` | 8 names, 55,004 bars, 26.0/session, gates PASS |
| `holdout_intraday_15m_raw.csv.gz` | 16 names, 899,196 rows — fetch finished, D278 spent it |
| `cohort3_intraday_15m_raw.csv.gz` | **8 names, 448,861 rows, gates PASS, all 28 steps REAL. UNSPENT — spendable ONCE** |
| Alpha Vantage 15m cache | 57 ETFs + 24 single names, ~2,500 slices. **Any of these starts at zero requests.** |

**The provider limit is settled, do not re-probe it:** `TIME_SERIES_INTRADAY` serves **nothing**
for a delisted ticker (TWTR/FRC/SIVB/AABA, four for four). `TIME_SERIES_DAILY_ADJUSTED` does.
**41.6% of the 2013–17 cohort is unreachable at 15 minutes**, so every intraday single-name study
is survivor-only and the bias runs *against* a short.

---

## EARLIER THE SAME DAY — the D264 session, as it stood mid-way

*Superseded by the section above; kept because its data-layer notes are still accurate.*

---

## 0. THIS SESSION — D264 ran and closed. Three commits.

```
fc5b080  D264 RESULT: closed -- zero of twelve, and the cost decides, not the signal
7492402  Single-name 15m fixture: gates pass, and all 30 flagged steps are real
56c6156  D264 PRE-REGISTRATION, committed BEFORE the fixture is scored
```

**Working tree CLEAN. Suite 1,831 passing, 5 deselected, 1 failing** — the same pre-existing
`test_every_gap_is_a_non_empty_band_that_price_left_behind`. **Still not to be fixed.**

**Next decision number is D265.** Both counters (`docs/decisions/README.md`, `docs/RULES.md` R5)
are correct.

### What was built and is now durable

| | |
|---|---|
| `data/fixtures/single_name_intraday_15m_raw.csv.gz` | 8 names, 448,279 rows, 2018→2026, gates PASS |
| `data/fixtures/single_name_intraday_15m_panel.csv.gz` | **8 × 55,004 bars, 2,117 sessions, exactly 26.0/session** |
| `scripts/select_single_name_intraday.py` | the sample rule, on a window disjoint from the test span |
| `scripts/fetch_single_name_intraday.py` | fetcher, reusing the ETF one's helpers |
| `scripts/classify_single_name_steps.py` | D226's allow-list, built by measurement |
| `scripts/run_single_name_intraday.py` | 16 cells, six hurdles, every leg computed |

**~848 Alpha Vantage requests spent. Any further single-name intraday work on PG LMT PM MO CLF SM
YELP RH starts at zero requests.**

### THE PROVIDER LIMIT THAT SHAPES ALL FUTURE INTRADAY WORK — measured, five calls

**`TIME_SERIES_INTRADAY` serves NOTHING for a delisted ticker.** TWTR, FRC, SIVB and AABA all
return `Invalid API call` at 155 bytes; AAPL returns a clean 546 bars. **`TIME_SERIES_DAILY_ADJUSTED`
DOES serve dead names** — that is how D252 built a 35.7%-dead daily fixture.

**So any intraday single-name study on this provider is survivor-only, and 41.6% of the 2013–2017
cohort is unreachable.** Do not re-probe this; it is settled. If a dead-inclusive intraday fixture
is ever needed, it requires a different vendor (Polygon, Databento) and that is a spending decision.

### The result, in one line

**Zero of twelve short cells cleared.** The construction produces the **largest gross short edge
this programme has measured** — held bars returning **−28.87%/yr**, hurdle H cleared on both legs at
the **96.9th / 99.7th** percentile — and loses **15.84%/yr**, because:

```
exposure x edge   +8.31%/yr        (continuously compounded; percentages do not add)
- sigma^2 tax     -4.87%           59% of the gross, exactly as FINDINGS 1b describes
= realisable      +3.43%           still profitable at this point
- trading cost   -20.68%           324 turns/yr at 6.42 bp/side -- 6.0x the realisable gross
= net            -17.24%
```

**And the kill is assumption-free: mean commission ALONE is 1.92 bp against a 1.06 bp breakeven.
The cell loses at a zero spread**, so the verdict does not depend on the half-spread figure that was
named in advance as the design's weakest number.

**The closure is bounded**: it closes *that construction on those eight survivor names, personal
track*. It does not close the intraday short, because the survivorship bias runs **against** the
short and that direction was declared before the data was seen.

---

## 0b. THE THREE THINGS FROM D264 WORTH ACTING ON

### (a) OVERNIGHT DRIFT IS A PROPERTY OF VOLATILITY, AND THIS CHANGES A QUEUED STUDY

| | overnight/yr | intraday/yr |
|---|---:|---:|
| **LOW vol** — PG LMT PM MO | +4.36% | **+5.56%** |
| **HIGH vol** — CLF SM YELP RH | +13.81% | **−8.97%** |
| *57 ETFs — D247* | *+8.59%* | *−0.36%* |

**In low-volatility names the drift accrues INTRADAY and the sign reverses.** D247's figure is an
average over instruments whose volatility differs, not an asset-class constant.

> **ACT ON THIS: the wide extended-hours pre-registration in §4c below should carry a VOLATILITY
> SPLIT.** It already asks where untraded-window drift accrues across 11 instruments, and PICKUP
> already records SPY and QQQ disagreeing 33% against 91%. **D264 says that disagreement has a
> measurable axis.** Add it to the design *before* running, alongside the EEM/FXI prediction that is
> already declared.

### (b) COST PER BASIS POINT IS A FUNCTION OF PRICE — post-hoc, disclosed, NOT tested

IBKR charges **per share**, so commission in bps is inversely proportional to price. Inside the
high-vol stratum it varied twenty-fold:

| | RH | YELP | SM | CLF |
|---|---:|---:|---:|---:|
| commission, bp/side | **0.20** | 1.44 | 1.89 | **4.15** |

**A high-priced, high-volatility name gets the high stratum's edge at a fraction of its commission.**
Invisible on ETFs, which cluster in price.

> **This is NOT eligible as a D264 follow-up** — D264's stop forbids an additional stratum, and
> computing a per-symbol verdict now is precisely the complement-chasing D246 Constraint 3 forbids.
> **It is eligible as its own pre-registration with the provenance stated**, which Constraint 3
> explicitly permits. If you take it: select on price × volatility on a pre-period, fetch a fresh
> sample, and declare in advance that the breakeven must exceed commission alone.

### (c) BREADTH IS NOT CAPPED AT 2.2

**Effective instruments 3.02 of 8 single names**, against **2.23** on 57 ETFs and 1.80 of 35 on
crypto. FINDINGS §4's saturation near 2.2 is a property of the ETF universe, **not a ceiling**. Any
future breadth argument should stop quoting 2.2 as universal.

---

## 0c. WHAT IS STILL LIVE, IN PRIORITY ORDER

1. **The wide extended-hours decomposition** (§4c) — fixture built and gated, nothing decomposed,
   prediction already declared. **Add D264's volatility split before running.**
2. **Rung 2's free micro/mini form and rung 3** (§4) — untested, free, prop track.
3. **The factor-neutral branch of FINDINGS §9** — never attempted on the 1,580-name daily fixture.
4. **The price-stratified intraday question** (0b above) — needs its own pre-registration.

**Note on the personal track's short side:** with D264 closed, *directional* shorts are now closed on
liquid ETFs (D238/D240/D247/D248/D249), on single names daily (D256), and on concentrated single
names intraday (D264). **The remaining untested shapes are factor-neutral, not directional.**

---

## PREVIOUS SESSION — the futures data layer

*Written 2026-09-01 at the end of the session that built the free half of the futures data layer.
Everything below this line predates D264 and is preserved unedited; §1 and §2 restate that
session's tree state, not the current one — see §0 above for the current state.*

Read this first, then [`docs/decisions/D262-the-futures-data-layer-and-the-free-rung.md`](docs/decisions/D262-the-futures-data-layer-and-the-free-rung.md).
Everything below is verifiable from the repo; nothing here is a plan I intend to be trusted on faith.

---

## 1. State of the tree

**Working tree is CLEAN. Everything is committed.** Nine commits this session, `520e71b..0b40695`.

```
0b40695  WP4: the 2010-2017 backfill lands, and the 57-ETF extended fixture is REFUSED
8df1bc1  fetch_databento: close the two guard gaps found by reviewing the guards
0b99ac1  fetch_etf_intraday: --extended writes its OWN fixture, and 64 bars not 26
1043544  D262: the futures data layer documented, and three corrections to the proposal
02d8277  Continuous-contract stitcher, and the gates that reject a bad splice
4ef9a61  Databento client: verify-first, and structurally unable to spend
c18a4e6  CFTC Commitments of Traders: rung 1 of the ladder, built and committed
b1af940  futures-data: close lane 01, and close the forum search entirely
520e71b  data-purchase-proposal.md: the full costing, with the tick figure corrected
```

**Suite: 1,831 passing, 5 deselected, 1 failing.** The failure is
`tests/property/test_structure_invariants.py::test_every_gap_is_a_non_empty_band_that_price_left_behind`
and it is **PRE-EXISTING and explicitly not to be fixed.** Do not "helpfully" repair it.

**Next decision number is D263.** The README counter was stale at D260 and is now correct.

---

## 2. THE ONE THING BLOCKING PROGRESS, and it is not yours to unblock

`scripts/fetch_databento.py --verify` **cannot run: there is no Databento key on this machine**, and
no account behind it.

```
key file expected at:  C:\Users\O\.config\databento\key        (does not exist)
or env var:            DATABENTO_API_KEY                        (not set)
```

**Do not create the account. Do not handle, write, or ask for the key.** The principal has been given
the two steps (sign up choosing **usage-based $0/mo, NOT Standard**; save the key to that path). If
they say it is done, run `--verify` — it is free, metadata endpoints only, ~7 calls, ~4 seconds.

### What `--verify` settles, and why it matters more than it looks

**The single inferred number the entire $181.81 costing rests on.** We derived **$28.00/GiB** from
Databento's own two worked examples. **Their published `list_unit_prices` example shows `ohlcv-1m` at
280.0** for an unnamed dataset — ten times that. Unit prices are per-dataset so it is *probably* not a
contradiction, but the spread is **$182 against $1,820** and probably is not good enough.

It also resolves `ES.c.0` / `ES.v.0` / `ES.n.0` to settle whether the roll-rule letters mean what
`databento-python`'s `RollRule` enum implies. **See §5 — this one nearly cost real money.**

---

## 3. What now exists that did not before

| | |
|---|---|
| `scripts/fetch_cftc_cot.py` + fixture | **rung 1 of the ladder, free, BUILT** |
| `scripts/futures_continuous.py` | the stitcher §12 requires, tested against **no vendor data** |
| `scripts/fetch_databento.py` | a client that **cannot spend by accident** |
| `docs/cftc_cot.md`, `docs/databento_api.md` | provider references |

**`data/fixtures/cftc_cot_raw.csv.gz` — 210,717 rows, 28 symbols, three report families,
1986-01-15 → 2026-08-25, 3.1 MB, COMMITTED.** It is the only source in the futures data layer that
may be committed, because COT is a work of the US government and is public domain.

**Also durable:** the Alpha Vantage 15-minute cache is now **complete at 11,400 slices** (526 MB,
gitignored), including the 2010–2017 backfill. **Any future extended-hours study starts at zero
requests.**

---

## 4. UPDATE — rung 1 was screened after this file was first written, and it CLOSED

**[D263](docs/decisions/D263-the-cot-positioning-prescreen.md), commits `4dd6d3c` (design, before
the run) and `48c2d36` (result).**

**Zero of eight cells cleared. Monotonicity failed on all eight**, which is the decisive one —
`nonreportable (disagg)` runs +1.83 / −5.53 / **−19.33** / +8.82 / −1.32. Best gross was
**+1.26%/yr** against a 2% bar. **2020 is not the cause**: seven of eight signs survive its removal,
so the result is *empty* rather than regime-dependent.

**Weekly category positioning is CLOSED for the prop track.** The stop applies: no threshold sweep,
no second lookback, no third category. **Do not reopen it with a variant.**

**Two things worth carrying forward:**

- **The largest spread had the WRONG SIGN** — `managed_money` at −7.32%/yr against a declared `+1`.
  Disclosed, not claimed: it is non-monotone, and D246 Constraint 3 forbids re-reading a falsified
  direction. Do not resurrect it as a momentum signal.
- **THE PANEL SURVIVES AND IS THE REAL ASSET.** 11 contract/ETF pairs, 9,232 weekly observations,
  16.2 years, **effective instruments 3.76, MDE 0.21** — assembled free from two committed fixtures
  and better powered than anything the prop track has run. `scripts/prescreen_cot_positioning.py`
  builds it in ~20 seconds. **Any future weekly cross-sectional question should be asked here.**

### So what is next

**Rung 2's free form — the micro/mini split — is still untested**, and it is a *different
construction on a different quantity*, named on the ladder before D263 ran. It is not a rescue.
Scope it to **ES/MES (272 weeks) and NQ/MNQ (302 weeks)**; M2K has 136, MYM 78, MSI 5. Thin, and R10
applies to two correlated instruments.

**Rung 3 — open interest against volume — is also untested and free.**

**And weigh this honestly before spending:** the ladder's premise was that positioning/flow is one
of the few families with the shape hurdle P wants. **The cheapest rung came back empty.** That is
evidence about the family, bought for £0, and it is exactly what §7.5 was built to produce. It does
not close intraday order flow — a weekly survey says nothing about an hours horizon — but it should
lower the prior before ~$205 is spent.

---

## 4b. The original next step (superseded by §4 above)

**Screen rung 1.** The ladder in §7.5 of the proposal says test the cheap instruments before buying
the expensive one, and rung 1 is now sitting in the repo.

> **This is a STUDY, so it needs its own pre-registration under R8 before anything is scored.**
> D262 is a *data acquisition* record — it deliberately scored nothing. Do not read the fixture and
> report a number without registering first. That is the whole discipline of this repo.

**The question worth registering:** does institutional-versus-retail positioning, as the CFTC
classifies it, carry information at a weekly horizon?

**Two constructions are available and they are not the same test:**

1. **Category positioning** — `leveraged_money` / `asset_manager` / `dealer` net positioning and its
   changes, per contract. Available on the widest history.
2. **The micro/mini split** — the free weekly form of rung 2. **THIS IS THE FINDING OF THE SESSION:**
   the CFTC reports micros as their own contracts (MES `13874U`, MNQ `209747`, M2K `239747`,
   MYM `124608`, plus micro metals), each with its own `nonrept` small-trader column. The proposal
   costs this at $14.28 of Databento minute bars to *infer* the split from contract choice; the CFTC
   classifies the traders directly.

**BUT READ THIS BEFORE SCOPING IT.** A contract enters COT only once it has enough *reportable*
traders, which lags listing by years:

| | listed | first COT report |
|---|---|---|
| MES | 2019-05-06 | **2020-07-28** |
| MNQ | 2019-05-06 | 2020-08-04 |
| M2K | 2019-05-06 | **2021-11-30** |
| MYM | 2019-05-06 | **2022-07-26** |
| MSI / MHG | 2022 | **2026-01** — unusable |

**So it is ES/MES and NQ/MNQ at ~6 years, not four pairs at seven.** Scope the registration to the
pairs that have history, and state the breadth honestly — two correlated pairs is thin, and R10
applies.

**Rung 3 is also free** and needs no new data: open interest against volume, in the fixture already.

---

## 4c. INTRADAY — a wide extended-hours fixture is built and gated, decomposition NOT run

**Commit `c25218d`. `data/fixtures/wide_extended_15m_raw.csv.gz` — 2,440,395 rows, 11 symbols,
2010-01 → 2026-08, all four gates PASS. Zero API requests; every slice was already cached.**

Built to settle a question **D259 explicitly left open**: SPY and QQQ *disagree* about where the
overnight drift accrues — the untraded 20:00–04:00 window carries **33% of SPY's and 91% of QQQ's**
— and D259 said in terms that *"nothing should be built on the untraded window's dominance."*
Four instruments cannot separate noise from structure. This is eleven.

**Universe:** SPY QQQ IWM DIA GLD SLV USO UNG GDX EEM FXI. Selected by **coverage** (median ≥45
extended bars of 64), a data-quality rule fixed before any decomposition ran and one that cannot
select on the quantity being measured.

### THE NEXT STEP, AND THE PREDICTION IS ALREADY DECLARED

**20:00–04:00 ET is Asian trading hours.** EEM and FXI track markets that are **open** during the
window the US calls untraded. **So if the untraded-window drift is a real transfer of information,
those two should show the LARGEST untraded share. If they do not, the effect is an artefact of
measuring a closed market rather than a real overnight risk** — and that would materially weaken
the case that overnight futures holds are structurally bad for hurdle P.

**Declare that prediction in the pre-registration before running it.** D263 showed the value: the
biggest number in that table had the wrong sign, and only the advance declaration made it legible
rather than reinterpretable.

**This is a STUDY. It needs its own R8 pre-registration.** Nothing was decomposed.

### Two findings from the build itself

- **THE EVENTS SIDECAR CANNOT EXPRESS A SPIN-OFF.** XLF qualified on coverage and was excluded
  anyway: it closes 23.63 on 2016-09-16 and opens 19.30 — **then holds there all day on 5.9M
  shares.** A −18.3% step persisting at full volume is a corporate action, the XLRE real-estate
  spin-off, and **Alpha Vantage's `SPLITS` reports zero splits for XLF.** `SPLITS` + `DIVIDENDS`
  between them do not cover spin-offs and this project has no general handling. **Check any new
  symbol for one before trusting its returns.**
- **D226's gate spec always required a documented real-events allow-list** — "no move above 15%
  *that is not on a documented list of real events*". The four-symbol build never needed the second
  half of that sentence. It exists now, the threshold is unchanged at 15%, and admission uses D252's
  test: does the move revert (bad print), persist at volume (corporate action), or is it
  corroborated (real).

---

## 5. Traps found this session that will bite you if you do not know them

**The symbol map is derived for a reason. Never type a CFTC contract code.**
`%CRUDE OIL%` matches **seven** contracts. Worse, **`%NATURAL GAS%` matches the main Henry Hub
contract NOT AT ALL** — the CFTC abbreviates it to `NAT GAS NYME`, so the pattern returns two
plausible wrong answers and no right one. A wrong code returns a full, well-formed series for the
wrong market and **nothing downstream errors**.

**The COT open-interest identity is not `OI == sum(long)`.** That fails on 94% of rows. A **spread
position is one long AND one short held by the same trader** — inside open interest, outside the
directional columns. It is `OI == sum(long) + sum(spread) == sum(short) + sum(spread)`, and it then
holds on **55,661/55,661 rows exactly**.

**Key COT dates on `release_date_nominal`, never `report_date`.** Report is Tuesday, release is the
**Friday of that week** — not a flat +3, because the survey day shifts on holidays. Rows before 1993
carry **no release date at all**, deliberately: there was no weekly schedule then and a fabricated
date would look usable.

**`6E` predates the euro.** Legacy rows run from 1986 under the name `EURO FX`; the euro began
1999-01-01 and continuous coverage starts exactly **1999-01-05** after a 644-week gap. **Use
1999-01-05 onward.** `RTY` separately spans an ICE venue change (2008–2017).

**The provider's typos are load-bearing.** `swap__positions_short_all` and
`swap__positions_spread_all` have **double underscores**; `noncomm_postions_spread_all` says
**"postions"**. Pinned by test. If you "fix" them the columns go silently empty.

**`ES.c.0` is almost certainly the CALENDAR roll — rolling at expiry.** §11 of the proposal
hard-coded it. That is precisely the defect §12's acceptance tests were written to catch in Yahoo's
`ES=F`. **The default is now `ES.v.0`.** Do not revert it on the basis of the proposal's text.

**The 57-ETF extended-hours fixture is REFUSED, on measurement.** Only **2 of 57 symbols** reach a
median 58 of 64 session slots; the tail is at 27–28; the raggedness is **liquidity-correlated**,
which is disqualifying for anything volume-related. And an unfiltered **+428.52%** bad print survives
(EWJ 2018-05-23 08:15 prints 11.46 on 912 shares against ~60.60 either side). `--extended` refuses
with the numbers as the reason. **Use `fetch_index_extended.py`**, which applies D259's
corroboration filter and carries a `suspect` column.

---

## 6. Two mistakes I made, so you do not repeat the shape of them

**I overwrote a committed fixture's meta.** The commit *before* it existed specifically to stop
`--extended` clobbering the regular-hours artifact. It parameterised the fixture path and the events
path and **missed the meta.** Caught only because `git status` flagged the committed file as
modified. Fixed by giving one function (`build_targets`) all three paths, plus a test asserting
`do_build` reaches for no unparameterised output constant. **Three constants with two swapped hides
the one you forget.**

**I wrote gates that were wrong before they were right** — the open-interest identity passed on 5.82%
of rows on its first version, and the release convention put a Friday report's release on itself
(zero lag, look-ahead by construction). Both were found by *looking at the output*, not by reasoning.
**Run the gate and read the number before believing it.**

**Practical note:** `Bash` heredocs on this machine mangle backslashes — a `"\n"` inside a Python
heredoc became a literal newline and silently broke a string, and an earlier `str.replace` missed for
the same reason. **Use the Edit/Write tools for anything containing escapes.**

---

## 7. Standing constraints — these do not lapse

**Alpha Vantage key** at `C:\Users\O\.config\alphavantage\key`, read via `ALPHAVANTAGE_API_KEY`
first. **Never inlined, never printed, never logged, redacted from any displayed URL.** Pace at
**66 req/min** against the 75 ceiling. Cache every response; hard stop after 5 consecutive failures.
**The ToS requires this repo stay private.**

**Exchange-licensed data is NEVER committed.** CME, Sierra Chart and NinjaTrader all forbid
redistribution. `.gitignore` carries `data/raw/databento/`, `data/raw/futures/`,
`data/fixtures/*futures*`, `data/fixtures/*glbx*`. The pattern is **gitignored cache + committed
re-fetch script + committed `.meta.json`**. CFTC COT is the sole exception and only because it is
public domain.

**Raw caches are not committed (D191); derived fixtures are.**

**No purchase without the principal's explicit decision.** `--submit` refuses without a passed
`--verify` *and* an accepted figure, and is then deliberately unwired. **Leave it that way** until
the purchase is actually decided — wire it up in the same commit, not before.

---

## 8. Where things are

| | |
|---|---|
| the costed purchase | `docs/research/futures-data/data-purchase-proposal.md` |
| the twelve-lane free search | `docs/research/futures-data/00-SYNTHESIS.md` |
| this session's record | `docs/decisions/D262-...md` |
| standing rules R1–R12 | `docs/RULES.md` |
| the two books | `docs/BOOK.md` (personal), `docs/BOOK_PROP.md` (prop — **admitted arms: none**) |
| substantive findings | `docs/FINDINGS.md` |
| providers | `docs/alpha_vantage_api.md`, `docs/cftc_cot.md`, `docs/databento_api.md` |

**Prop track status: every candidate so far is closed.** C1, C2, C3 and D261's spreads all failed —
three of them on **shape** rather than return, which is why the smart-money detector was worth
reaching for: order flow and positioning are among the few signal families with the shape hurdle P
wants. **Rung 1 is the cheapest available test of that idea and it is ready to screen.**

---

## 9. If you do only one thing

**Pre-register the COT screen and run it.** It costs nothing, the data is committed, and a negative
result is worth as much as a positive one — it would tell the principal not to spend £205 on the
Databento purchase at all.
