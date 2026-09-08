# D382 — the market-structure screen on the liquid universe

**Date:** 2026-09-08
**Kind:** **STAGE-1 SCREEN (R14), signal hunt under R15.** Admits nothing. **Reads no holdout, and installs a guard that cannot.**
**Pre-registered under R8 — committed before the runner exists. Result committed separately.**

---

## 0. Why this record exists

**The market-structure feature set has never been run on the liquid universe.** D290's 51 features
span eight axes; three of them are price action and market structure derived from OHLCV alone:

| axis | features | builder |
|---|---|---|
| **B** intrabar shape | `upper_wick` `lower_wick` `wick_asym` `body_frac` `close_in_range` `range_frac` `gap_frac` | `scripts/ragged_features.py::intrabar_scores` |
| **D** volume profile | `dist_hvn` `dist_lvn` `mass_here` `mass_imbalance` | `scripts/ragged_profile.py::build_profile_scores` |
| **H** harvested structure | `fvg_dist` `fvg_signed` `struct_trend` `retrace_leg` `choch_dist` `park_vol_21` `gk_minus_cc` `gap_reversal` | `scripts/ragged_structure_scores.py::structure_scores` |

**Every study that touches them — D290, D291, D323, D328, D329, D352 — is single-name work.** They
have never been run where a round trip costs ~6 bp instead of ~151.

**And the cost structure is the whole argument.** On `us_shorts_daily` the held names measure
**37.72 bp/side** and D373's book earned +3.859 bp/bar gross against 3.92 bp/bar of cost — net
**−0.063**. S1's universe charges **~1.5–1.8 bp/side**. **The same per-bar edge that dies on single
names clears comfortably on ETFs**, which is why both book entries came from there and nothing else
ever has.

**The principal's framing, and it corrects mine:** the finding that an ETF is a poor *short* target —
too little idiosyncratic variance, so the trade becomes a market call — is about **shorts**. A
**long-flat** book has no such problem. S1 and S2 are exactly that shape.

### What makes this different from a rerun

**Market-structure features are the family least likely to rediscover S1.** S1 is a smoothed
moving-average construction — `smma(34)` / `zlema(34)` channel. FVG, CHoCH, swing structure and
retracement legs are built from **swing points and gaps**. Mechanically different instruments, so the
prior on correlation is genuinely low — the opposite of [D373](D373-RESULT-the-winners-dip-is-the-retired-book-and-one-GME-trade.md),
where a construction re-derived from different-sounding premises held **70% of the same positions**.
**Gate 1d′ still runs at stage 1** ([R14](../RULES.md#r14)'s fixed ordering); here it is expected to
pass rather than dreaded.

---

## 1. The fixture, and the split declared before anything runs

**`data/fixtures/universe_wide_w1_raw.csv.gz`** — daily OHLCV on the wide liquid ETF universe from
[D245](D245-the-wide-universe.md), starting **2009-11-11**, screened above $5M/day. Loaded through
`ragged_panel.load_ragged`, which is fixture-generic, with `assert_gates_passed` on entry.

**This fixture is NOT clean.** D245 records that it **contains** S1's 57- and 60-name sets, so it is
already spent for S1 and S2. Under the principal's ruling of 2026-09-07 a **brand-new construction**
may mine spent in-sample data provided nothing crosses into a holdout; the cost is the **prior**, not
validity. **This is a brand-new construction and nothing crosses.**

**THE TIME SPLIT, DECLARED NOW AND NEVER READ BY THIS STUDY:**

| | |
|---|---|
| **MINING** | first bar → **2019-12-31** |
| **RESERVED** | **2020-01-01 → present. Untouched.** |

**A time split rather than an instrument split, because S1's own record says the instrument holdout is
the easy one.** S1 passed **two** instrument holdouts — the two ETF universes correlate at
**ρ = +0.978**, so passing proves little — and then **failed the era holdout**: negative excess
Sharpe, beating buy-and-hold by a fifth of its own floor. It also failed on crypto at the 29.1st
percentile.

**`[SPLIT]` installs a default-deny guard**: the runner truncates the panel at the mining boundary and
**asserts no bar beyond it is ever loaded into a score, a null or a book.** This is a screen — R14
puts the holdout at stage 4 or not at all — so there is no authorised path to the reserved window
here, and the guard has no override.

---

## 2. The construction, frozen

**Long-flat, equal-weighted across the universe, daily bars, `lag = 1`** — exposure held through bar
*t* is decided on *t−1*'s close. The same shape as S1 and S2, and the same shape the principal asked
for: **flat by default, in on a signal, out on the exit.**

**Direction is DECLARED LONG before the run** (gate 1h). A feature that works only reversed is
reported as **direction-inverted** and counts against its stated mechanism, exactly as D290's
`wick_asym` was.

**Entry:** the feature's cross-sectional percentile crosses into its extreme decile, as D290 defined
an event. **Exit:** a fixed hold, swept over **{5, 10, 20, 40}** bars and **reported, never picked**
([R14](../RULES.md#r14), 2026-09-03). **Cap 20 is nominated primary** in advance so that a single
number can be quoted without selection.

**19 features × 4 holds = 76 cells.** Priced in §5.

---

## 3. What is measured

**Primary, per R15:** **gross mean per trade**, against the nulls of §4. **Cost is reported and gates
nothing at this stage.**

**Reported beside it, and the second one is the hurdle that matters for a directional book:**

1. The four groups in full (`CLAUDE.md`): performance net **and** gross with exposure; the trade
   distribution with both-tail trims; what the winners depend on; the null distribution, not the
   percentile alone.
2. **Excess over BUY-AND-HOLD at matched exposure.** D290: **fifty of fifty-one long-only books are
   market drift.** A long-flat book that does not beat B&H on the exposure it actually takes has
   found nothing, whatever its nulls say.
3. **Gate 1e, capturability, at stage 1** — open-entry `t` and retention. **This is the specific
   failure mode this feature family has.** On single names D290's two strongest intrabar candidates
   died here: `close_in_range` cleared its nulls at CV t **+6.19** and min z **+12.08** and retained
   **19%** at open entry; `wick_asym` cleared all three nulls at t **+10.51** with open-entry t
   **−1.77** and **115% of the effect overnight**. **A feature that fires on the close and moves in
   the gap is not tradeable**, and that is a property of the family, not of the universe.
4. **The overnight/intraday decomposition per feature**, so 3's cause is visible rather than inferred.
5. **Gate 1d′ against S1 and S2** ([D376](D376-RESULT-two-unrelated-books-here-correlate-at-0.48-and-two-cohort-books-at-0.92.md)):
   correlation compared to the p95 of the pair distribution among books from this universe, **with the
   pool named**. A raw correlation quoted without its pool is uninterpretable.

---

## 4. The nulls

D290's three, unchanged, so the verdicts are comparable to the only other screen of these features:

| | what it randomises | what it catches |
|---|---|---|
| **rotation** | per-name timing | signals that are not timed |
| **within-bar permutation** | the score across names inside a bar | signals that are not cross-sectional |
| **tail-randomised** | which names occupy the extreme | signals that are not about the tail |

**`min z > 0` across all three**, as D290 required. **Plus name-split CV** (gate 1f): pick the peak
cell on half A, score it on half B, over K = 10 re-randomised splits — necessary and **explicitly not
sufficient**, and never quoted alone.

---

## 5. The search cost, stated

**19 features × 4 holds = 76 cells, and that is a large search on a fixture already spent for S1.**

- **A best-of-76 floor**: the null draws are taken **under a shared per-name offset**, and the floor
  is the **max over all 76 cells within each draw** — D367's construction, as D373 used at
  best-of-5.
- **Every cell is reported**, not the survivor.
- Under [R13](../RULES.md#r13) this adds **one look** to a new ledger; under R14's first amendment,
  selection on spent data costs the **prior**, not validity, and the reserved window is what the
  prior is spent against.

---

## 6. Assertions

| tag | what it proves |
|---|---|
| **`[SPLIT]`** | **no bar at or beyond 2020-01-01 reaches any score, null or book.** Default-deny, no override, asserted after every stage |
| **`[GATE]`** | `assert_gates_passed` on the fixture before anything is computed |
| **`[LAG]`** | exposure through bar *t* is decided on *t−1* — re-derived by a **second implementation that never calls the position builder** ([R9](../RULES.md#r9); D248's error lived in an ad-hoc script upstream of every null) |
| **`[FEAT]`** | each axis's builder reproduces its own module's self-test on this panel before its scores are used |
| **`[DIR]`** | the declared LONG direction is scored as declared, and the reversed book is reported separately (gate 1h) |
| **`[BH]`** | the buy-and-hold comparator is at **matched exposure**, and the runner refuses to report an excess figure without it |
| **`[X]`** | **the one that matters** — every audit above must **RAISE** on a deliberately broken book, including a score that peeks at bar *t* and a panel that includes a reserved-window bar |

**Persist before rendering.**

---

## 7. Predictions

**Five studies running have had my direction right and my magnitude wrong. These are recorded to be
scored against that.**

| | prediction |
|---|---|
| **Q1** | **at least one of the 19 clears all three nulls with `min z > 0`** at some hold. On single names 24 of 51 did |
| **Q2** | **AGAINST the study: fewer than 3 of the 19 survive gate 1e.** The family's move is concentrated in the gap, and a next-open fill misses it. **This is the outcome I expect to kill it** |
| **Q3** | **axis H survives better than axis B.** Structure features key on multi-bar geometry; intrabar shape keys on the close, which is where the overnight problem lives |
| **Q4** | **no cell beats buy-and-hold at matched exposure by more than 2 SE.** D290's fifty-of-fifty-one, on a universe with a stronger drift |
| **Q5** | **gate 1d′ passes** — the best survivor's correlation to S1 and S2 sits inside this universe's own pair distribution. Mechanically different instruments, as §0 argues |
| **Q6** | the best cell's hold is **20 or 40**, not 5 — a 5-bar hold cannot amortise even a 6 bp round trip against a per-bar edge of a few tenths of a basis point |
| **Q7** | `[SPLIT]` and `[LAG]` both hold on the first run. If either fails, §8 applies and nothing is reported |

---

## 8. What would make me abandon this

- **`[SPLIT]` fails** → a reserved bar reached a score. **Stop, fix, publish nothing, and treat the
  reserved window as compromised until proven otherwise.**
- **`[LAG]` fails** → look-ahead. D279 lost ~93% of its apparent edge to exactly that.
- **Fewer than 3 features survive gate 1e** → Q2 realised. **The family is not tradeable at a
  next-open fill on daily bars**, and the honest conclusion is that it needs an intraday fixture or
  nothing. Say so; do not sweep holds looking for a survivor.
- **Nothing beats buy-and-hold at matched exposure** → the screen found market drift, which is
  D290's result on a new universe and should be written as one.

---

*Pre-registered 2026-09-08. Runner does not exist at the time of this commit (R8). No holdout is read
and none may be: the reserved window is guarded default-deny with no override.*
