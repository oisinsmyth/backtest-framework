# D403 PRE-REGISTRATION — the wick-stack potential map, built daily and read at 15 minutes

**R8: committed before the runner exists. Result separately.**

**Number.** `D403`. Taken by the three-command procedure in PICKUP §"READ THIS BEFORE YOU
PICK A DECISION NUMBER", not by `ls docs/decisions/`: `git log --all` shows D399–D402 used
and nothing at D403+; the only reserved block is `D390–D399` (`945cbb5`,
`worktree-signal-hunt-part2`, live 18 minutes ago). Master takes D400 and upward.

---

## 1. The question

The principal's construction. Each daily candle carries two zones:

- **supply zone** = `[max(O,C), H]` — the upper wick
- **demand zone** = `[L, min(O,C)]` — the lower wick

Stack both, over a trailing 100 daily bars, onto the price axis and read the resulting
scalar field at 15-minute resolution. **Think of it as a potential energy map.**

Two questions, both **descriptive**:

1. At what magnitude of the map do 15m **swing lows, swing highs and reversals** occur —
   and, since the principal invited additions, at what magnitude does price **dwell**,
   **reject**, **traverse**, and **retest**?
2. At what **frequency** does price break above the upper peak or below the lower peak of
   the map, and **by how much** does it break out when it does?

**This study takes no position and scores no book.** It measures an object. That is the
whole scope, and §10 says what it deliberately does not do.

---

## 2. R13 LEDGER — THIS IS THE SIXTH LOOK AT A PRICE-LEVEL MAP

The principal said he was aware this had been looked at before. It has been looked at five
times, under five names, and every one carries a written close. **The ledger transfers.**

| # | programme | object | disposition |
|---|---|---|---|
| 1 | TERRAIN, D189–D203 | volume-at-price; swing supply/demand bands; signed inventory field | **CLOSED, terminal** — 259 looks |
| 2 | STRUCTURE, D173, D204–D211 | CHoCH/BOS, flipped levels, fair value gaps | **CLOSED** by D211 — 86 looks |
| 3 | D272, D273 | `dist_hvn` / `dist_lvn` as cross-sectional scores | run and closed |
| 4 | BREAKOUT family, D109–D165, D249, D254 | Donchian breaks; wedge breakout | off-thesis, dormant; wedge **closed** |
| 5 | DENSITY line, D384–D388 | kernel density over an EMA-centred log-price axis | **RETIRED by the principal, 2026-09-09** |

Two prior results sit directly under this construction. **D196** built swing supply/demand
bands: **0 of 20 cells cleared both hurdles**, and six cells beat randomly-placed levels
*while losing money*. **D197–D203** built a signed inventory field — the nearest existing
thing to a potential map — across five refinements scoring **−0.007, −0.156, −0.013,
−0.052, −0.822** against their nulls.

And TERRAIN's close is not an absence of signal. It is a **mechanism**:

> Inventory accumulates below price exactly when price has been *falling into* it, so
> trading it fades a decline. Fading lost in every form measured — 16 of 16, 16 of 16,
> 8 of 8, 11 years of 11. **The map's local structure is not uninformative about
> direction; it is reliably wrong.**

**This study inherits that as a pre-registered prediction, not as a footnote.** §5.6 states
it in this map's own quantities and §7 makes it a named outcome. A sixth look that does not
answer the fifth's mechanism is a wasted look.

**What is actually new,** and the only reason this is worth a number:

1. **The zone is wick-only.** Prior maps stacked volume, full ranges, or signed inventory.
   `upper_wick` / `lower_wick` exist in `scripts/ragged_features.py:155` as per-bar
   features — they have never been stacked into a price-axis field.
2. **It is cross-timeframe.** Daily map, 15m read. Every prior map was built and read on
   one clock.
3. **The question is descriptive.** All five programmes asked whether a map predicts
   returns. None reported where events actually sit on the map against a matched base
   rate. That description is the deliverable here, and it is worth having on file whichever
   way it comes out.

---

## 3. THE OBJECT

### 3.1 Construction

For name `n` and session day `D`, using **daily bars `D−100 … D−1` only** — day `D` is
never read:

```
body_top_i = max(O_i, C_i)        body_bot_i = min(O_i, C_i)
supply_i   = [body_top_i, H_i]    demand_i   = [L_i, body_bot_i]

M_raw(p)   = SUM_i 1{p in supply_i} + SUM_i 1{p in demand_i}        (ADDITIVE)
```

Additive, per the principal's ruling of 2026-09-09: the two stacks **sum**, they do not net.

```
C_ref      = close of day D-1
p_u        = argmax M_raw over p > C_ref          (upper peak)
p_l        = argmax M_raw over p < C_ref          (lower peak)
tau        = min M_raw on [p_l, p_u]              (the valley floor between them)

M(p)       = max(M_raw(p) - tau, 0)
```

The pedestal `tau` is the trough **between the two peaks**, anchored at the last daily
close. Subtracting it and clamping leaves a well: zero at the floor, rising to a barrier
each side, zero again out in the tails where the stack thins below `tau`.

### 3.2 No grid

`M` is **piecewise-constant with at most 400 breakpoints**, so it is built exactly on the
sorted zone endpoints by a difference array (`+1` at each `a`, `−1` at each `b`, cumsum)
and read by `searchsorted`. **There is no price grid and therefore no grid-resolution free
parameter.** This is deliberate: D384's density carried a bandwidth that scaled with
`sd(x)`, so on volatile names the smudge was widest exactly where events were common — one
name reached a 17%-wide kernel with zero modes. A piecewise-constant field has no bandwidth
to be wrong about.

### 3.3 Degeneracies, declared in advance

- `O == C` (doji): body is a point; both zones survive with positive width. Kept.
- `H == body_top` (no upper wick): **zero-width supply zone, contributes nothing.** Kept as
  a no-op rather than widened to a minimum.
- Malformed bars — the five bars in 4,137,239 with `close < low`, a provider ex-dividend
  artefact the build gates do not catch — are **masked, not clamped** (D280 convention).
- Zero-range bars (17,886, 0.43%) contribute no zones and are **NaN, not 0/0**.
- A day with `p_u` or `p_l` undefined (no positive `M_raw` on one side of `C_ref`) is
  **dropped from the breakout arm and reported as a count**, not silently skipped.

### 3.4 Free parameters, swept and read as a SHAPE (R14)

| parameter | values |
|---|---|
| lookback `W` | **100** (principal's), plus 50 and 200 as shape |
| peak plateau tiebreak | interval midpoint (primary), near edge (shape) |
| barrier quantile `q` for a "high-M region" | 0.5, 0.7, 0.9 of the day's positive `M` |
| forward horizon `H` (15m bars) | 4, 8, 26 (one session) |
| swing `k` | 2, 3 — the pinned set at `terrain_swing.py:75` |
| sigma thresholds | D388's `KS = {"move": (2.0, 2.5), "reversal": (1.0, 1.5)}` |

**No parameter is chosen by outcome.** The record reports every cell.

---

## 4. UNIVERSE AND THE THREE-WAY PARTITION

### 4.1 Instrument

The map needs daily OHLC; the read needs 15m OHLC. Both exist offline.

- **daily** — `data/fixtures/us_shorts_daily_raw.csv.gz`, 1,573 names, 2010-01-04 →
  2026-08-26, loaded **only** through `RP.load_ragged` (which is where
  `assert_gates_passed` lives, `scripts/ragged_panel.py:76-111`). The runner asserts every
  study name is present and that the fixture's gates carry empty `failures`.
- **15m** — `data/fixtures/cohort4_intraday_15m_raw.csv.gz`, **24 single names**,
  1,350,162 rows, 2018-01-02 → 2026-08-31, RTH, full OHLCV.

**Single names, not the 57-ETF panel.** D401 measured `n_eff = 2.17 instruments out of 57`
at 15 minutes. Fifty-seven ETFs would make every significance number in this study close to
fictional. The ETF panel is used **only** for the §5.1 shape-check of the object, where
nothing is tested and `n_eff` is irrelevant.

**Spend status, flagged rather than assumed.** Cohort4 was fetched and step-classified
2026-09-02 and is referenced by **no decision record found**. This study records itself as
its first use. If a record surfaces showing otherwise, that claim must be revisited before
any result here is quoted.

### 4.2 The partition

The principal asked for three groups with **the initial partition small compared to the
others**. There is no existing three-way name partition in the programme; the house idiom
is *shuffle once with the pinned seed, take contiguous prefixes, never re-pick*
(`scripts/fetch_short_universe.py:223-227`).

```
tickers = sorted(cohort4)                      # deterministic input
random.Random(20260828).shuffle(tickers)       # POOL_SEED, the programme's pinned seed
G1 = tickers[:4]     G2 = tickers[4:12]     G3 = tickers[12:]
```

| group | names | role |
|---|---:|---|
| **G1 — design** | 4 | Look at the object. Every construction choice, degeneracy and diagnostic is settled here. Statistics computed on G1 are **reported as exploratory and are not evidence.** |
| **G2 — measurement** | 8 | The pre-registered measurements of §5, run once, after G1 is frozen. |
| **G3 — confirmation** | 12 | Untouched until G1 and G2 are committed. Run once, unchanged. |

`random.Random(POOL_SEED)` is used rather than `hash()`, which
`scripts/d290_direction_nulls.py:40-44` records as **not reproducible** — Python randomises
`hash()` per process.

**`cohort3_intraday_15m_raw.csv.gz` (8 names) is not touched by this study.** PICKUP flags
it unspent and spendable once; it is worth more as a future out-of-sample fixture than as
padding here.

### 4.3 Windows

- **Scored to 2023-12-31.** D383 reserves 2024+. That leaves 2018-01-02 → 2023-12-31,
  ~1,500 sessions per name, and preserves a genuine forward slice.
- Daily map history reaches back to 2010, so the 100-bar lookback costs no 15m coverage.

### 4.4 Eligibility

`elig = finT & keep_v2` — `scripts/d348_prep.py:259,278-279`, with `keep_v2` from
`scripts/d339_universe_floor.py:120-129`: as-traded close at `t−1` ≥ \$5, dollar volume
above the 28th percentile, and `isfinite(DV)`.

**Every null in §6 rotates inside `elig`, never inside `finT`.** That is the D351 defect
verbatim: 8–13% of D347's rotated events landed on bars the strategy was forbidden to
trade, earned +226 to +318 bp against +1.7 on the eligible universe, and **inverted the
headline**. The runner asserts null-event eligibility share `== 1.0`.

---

## 5. WHAT IS MEASURED

### 5.1 THE OBJECT FIRST — before any statistic

The D385 and D387 lesson, twice in one session: a test statistic was reported without ever
inspecting the construction, and both times the object was flat. So the runner's **first**
output, on G1 and on the ETF panel, is the map itself:

- number of modes of `M_raw`; **is it bimodal at all?** "The two peaks" presupposes it, and
  a 100-day wick stack may be one blob with `tau` sitting somewhere arbitrary
- distribution of `M_raw` max, of `tau`, of `tau / max M_raw` (how much is pedestal)
- fraction of the price axis clamped to zero
- barrier widths and heights, in daily-sigma units
- where `C_ref` sits relative to `p_l` and `p_u`
- **ten plotted maps, named, with their dates**, so the object is looked at and not
  summarised

**If `M_raw` is unimodal in the majority of name-days, the peak-anchored pedestal is
reported as ill-posed and §5.5 is re-specified before it is run — not after seeing its
result.**

### 5.2 Occupancy — the primary observable

If `M` is a potential, the first question is not a conditional mean, it is whether price
*avoids* high-`M` prices at all.

Partition the axis into the map's own constant intervals `j`, each with level `M_j` and
width `w_j`. Express `w_j` in units of the name's daily EW sigma so widths are comparable
across names. Count 15m closes falling in each interval.

```
occupancy(M) = SUM_j visits_j / SUM_j w_j      over intervals with M_j in a bin of M
```

**Per unit price width — that normalisation is the whole point.** Raw visit counts against
`M` would recover only that price visits mid-range, which is also where the stack is
thickest. Report `log occupancy` against `M`, its slope `beta`, and **the curve, not the
slope alone.**

### 5.3 Events — the principal's question

For each event type, the **mean magnitude of the map at the event's price**, in three
currencies: raw count `M`, within-day percentile of `M`, and `M / max M`.

| event | definition | source |
|---|---|---|
| swing high / low | strict-and-unique `k`-bar fractal | `research/terrain_swing.py:106` |
| reversal | sign flip with **both legs** `> k * sigma_t` | D388 `events_sigma`, `run_d388_rare_event_levels.py:49` |
| large move | `abs(r) > k * sigma_t` | same |
| **reject** | enters a high-`M` region, exits the side it came from within `H` | new, §5.4 |
| **traverse** | enters a high-`M` region, exits the far side within `H` | new, §5.4 |
| **retest** | returns to a broken peak within `H` after a §5.5 break | new |
| **gap-over** | a single 15m bar jumps a high-`M` region entirely | new |

**Thresholds are in the name's own sigma, never in percent.** D387 carried ETF-calibrated
2% thresholds onto single names at 3–5× the volatility; `move >2%` fired on a **median
28.3% of bars** and above 30% on 282 of 600 names, which made the object flat by
construction. D388's sigma units collapsed cross-name rarity spread **4.37× → 1.37×**.

**Every event's base rate is reported beside its conditional mean.** Swing lows at `k=2`
fire on **24% of ETF bars** (D385 §54). An "event" on a quarter of bars is not an event,
and a conditional mean over it is the unconditional mean wearing a hat.

### 5.4 Reject vs traverse — the direct test of the claim

A high-`M` region is a maximal interval with `M >= q * max M` for `q` in {0.5, 0.7, 0.9}.
On entry from outside, classify the exit within `H` bars as **reject** (same side),
**traverse** (far side), or **unresolved**. Report `reject / (reject + traverse)` against
`M` inside the region.

This is what supply and demand actually assert, and unlike a swing point it has no
definitional freedom to be gamed.

### 5.5 Breakout and breakdown — the principal's second question

**Breakout** = first 15m close `> p_u`; **breakdown** = first 15m close `< p_l`, per
session.

- **Frequency**, per session and per name-year, both directions.
- **Conditioned on `abs(p_u − C_ref)` in daily-sigma units.** Not optional: D273 produced a
  beautiful monotone 62.6% → 1.3% ordering that **any random line reproduces**, because a
  nearer level is more likely to be reached. Reachability is arithmetic.
- **Conditioned on barrier height `M(p_u)` and barrier width** — the potential reading
  predicts crossing rate falls with barrier height. This is the shape that would make the
  map non-decorative.
- **Excursion**: `max(high) − p_u` over the next `H` bars, in daily-sigma units and in
  percent. Reported with **median beside mean**, and trimmed 1% from **both** tails —
  dropping only winners is a flag, not a verdict (D307).

### 5.6 THE TERRAIN PREDICTION, in this map's quantities

TERRAIN found the map's local structure reliably wrong because inventory accumulates below
price exactly when price is falling into it. The wick-stack should inherit this: a run of
down days leaves lower wicks below price, so `M` is high beneath a falling price **because**
it fell.

Pre-registered: report `corr(M at C_ref, trailing 20-day return)` and the event means
**stratified on trailing return sign**. If the map's magnitude at price is largely a
restatement of where price recently was, that is the finding, and it is the same finding
TERRAIN reported — arrived at independently, on a new object.

---

## 6. CONTROLS AND NULLS

Beating a path-shuffle is nearly free — D388 beat one in **34 of 36 cells at p to 7.2e-11**
and beat a rotated map in **0 of 36**. The rotation is the test.

| tag | control | destroys | keeps |
|---|---|---|---|
| **A′** | pair a session's 15m path with **the same name's map from a different day**, offset within `elig` | the alignment of map and price | the real path, the real map, the real events, exactly |
| **OCC** | occupancy- and time-of-day-matched non-event bars, same name-days | the event | where price actually goes |
| **LVL** | **distance-matched random level** — `scripts/null_overlay_levels.py` | the map's claim that *this* level is special | the distance, which is what drives reachability |
| **N2** | iid bootstrap of standardised 15m returns rescaled by the observed vol path | serial structure | return distribution and vol clustering |

**A′ is decisive and reported first.** OCC and LVL are the base-rate corrections without
which §5.3 and §5.5 have no meaning. N2 is carried because it is cheap and because its
*gap* to A′ is itself informative — that gap is exactly what killed the density line.

**Distributions, not percentiles alone**: p50 and p95 beside every score, with the p95's
bootstrap SE, and **any margin inside 2 SE recorded UNRESOLVED** (D373). The A′ rotation
group is finite — one offset per eligible day, ~1,500 per name — so **A′ is ENUMERATED, not
sampled**, and its SE is exactly 0.

---

## 7. WHAT WOULD MAKE THIS INTERESTING

No signal claim is made, so there is no hurdle in the R15 sense. The outcomes, named now:

1. **The map is a potential.** `log occupancy` falls monotonically in `M`, events
   concentrate at high `M` **above A′**, and breakout rate falls with barrier height. That
   would be the first price-level map in six looks to survive its rotation.
2. **The map is decorative.** Occupancy flat in `M`; event means at or below A′. The
   construction is a restatement of the visited range. Same ending as the density line.
3. **The map is reliably wrong** — TERRAIN's mechanism, reproduced on a new object.
   `M` high beneath price *because* price fell into it, and events at high `M` continuing
   rather than reversing. **This is a real result and the most likely one**, and it is worth
   the sixth look on its own.

---

## 8. ABANDON CONDITIONS, committed now

- `M_raw` unimodal on a **majority** of name-days → §5.5's two-peak framing is ill-posed;
  re-specify the pedestal **before** running it, and say so in the record.
- Occupancy slope `beta` within 2 SE of zero on **G1 and G2** → the map does not shape where
  price goes; G3 is **not spent** and the line reports flat.
- Event mean `M` fails to exceed **A′** in a majority of cells → the object carries no
  information the map's own alignment does not already supply, and the study reports the
  description and stops.

---

## 9. RUNNER ASSERTIONS

All three house audits, plus the guards this family has earned. **Each is verified to
RAISE on a deliberately broken input** — and the break must hit **the scalar the assertion
reads**, not merely its name; three deliberate breaks were duds in one session on exactly
that error.

| tag | asserts |
|---|---|
| `[LAG]` | the map for day `D` uses only bars `D−100 … D−1`, re-derived by a **second implementation that never calls the map builder**. Killed D279's first result — 93% of its apparent edge |
| `[PIVOT]` | a `k`-fractal at `t` is unknowable until `t+k`; the runner uses the confirmed-pivot offset at `terrain_swing.py:121`. D391 shipped this bug and it cost 82% of its result. `scripts/lag_audit.py` is run |
| `[SIGN]` | a bar with a large upper wick puts mass **above** its body and none below; a close above `p_u` is a **rise**. A sign asserted in prose inverted D280 |
| `[QTY]` | `integral M_raw dp` equals the summed zone width exactly; the pedestal-subtracted map **differs** from the un-subtracted one |
| `[SPLIT]` | D387's no-unlock audit hook verbatim — refuses any path containing "holdout", and `assert_SPLIT` proves it **bites** by attempting one open and requiring the refusal. **This runner defines no `allow_holdout`** |
| `[ELIG]` | every A′-rotated day satisfies `elig`; rotated-event eligibility share `== 1.0` (D351) |
| `[BASE]` | every event's base rate is computed and non-degenerate; **raises** if any event fires on more than 20% of bars without that being reported |
| `[T+1]` | every forward window starts at `t+1`. D391's first run reported **+110.5 bp** purely from including bar `t`, because the arms were defined by where that bar's close sat |
| `[OBJ]` | §5.1 ran and produced a non-empty object dump before any statistic was computed |
| `[FAST]` | `assert_matches_scorer` once, and `parallel_map`'s `[SPEED]` line reported |

---

## 10. WHAT THIS STUDY DOES NOT DO

- **It takes no position, scores no book, and admits nothing.** No `BOOK.md` or
  `BOOK_PROP.md` consequence follows from any outcome.
- **It reads no holdout.** Not `us_shorts_daily_holdout.csv.gz` (spent, D371, 2026-09-07),
  not `us_shorts_daily_holdout2.csv.gz` (built, unspent), not
  `holdout_intraday_15m_panel.csv.gz` (spent, D278). The guard is default-deny with no
  unlock.
- **It does not touch 2024+**, reserved by D383.
- **It does not spend cohort3.**
- **It uses non-causal swing points knowingly.** A `k`-fractal is two-sided. That is
  admissible for a descriptive magnitude question and **inadmissible for a decision**, so
  no decision is taken. The sigma-unit events of §5.3 are causal and are the ones any
  successor study would inherit.

---

## 11. COMPUTE

24 names × ~1,500 sessions × a 400-breakpoint difference-array build is negligible; the 15m
read is ~940k `searchsorted` calls. The cost is the A′ enumeration, ~1,500 offsets ×
940k reads, which vectorises to one `searchsorted` per offset.

**Projected wall time: 5–10 minutes.** If the first timing exceeds that, one optimisation
pass happens **before** the launch and the record says what it did — D385 ran 92 minutes at
3.28× on 6 workers (55% efficiency) while two call timings were profiled and the cost
declared inherent.

---

*Pre-registered 2026-09-09, before the runner exists (R8). Sixth look at a price-level map;
the R13 ledger carries 259 terrain looks and 86 structure looks into this one.*
