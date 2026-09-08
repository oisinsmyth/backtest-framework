# D393 — the sign-sequence family: does the ORDER of returns carry anything the magnitudes do not?

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). **Nothing here is a
result.** No cell scored, no null run, no book proposed.
**Date:** 2026-09-08 · **Area:** signal research · **personal track**

**No holdout testing. Holdout reads spent by this record: 0. Programme total: 1** (D371).

**Build (R16):** today's panel, `load_ragged(dividend_bound=True)`, `keep_v2` floor, F0,
next-open fill. **Nothing is inherited from a pre-D333 record**, so no cross-build identity is
owed. **Number:** D393, in this branch's reserved D390–D399 block (`e5c9189`); renumber on
collision.

---

## 0. Why this candidate, and the argument is D392's

`docs/research/the-signal-hunt-part2.md` §4.2 proposed this family and ranked it **below** B1, on
the grounds that its direction could not be declared. **[D392](D392-RESULT-the-base-rate-atlas.md)
promoted it**, by measuring what a purely random long earns conditioned on the pool it draws from:

| conditional pool, n=30,000, cap 20, **no signal at all** | spread of the median random long |
|---|--:|
| **price tercile** | **36.8 bp** |
| **momentum tercile** | **32.2 bp** |
| volatility tercile | 12.2 bp |

**A candidate that tilts on price or momentum starts with a large floor to beat.** Sign statistics
are unit-free, price-free and magnitude-free **by construction** — the one family in the catalogue
that structurally cannot tilt on either of the two widest base rates. That is also FINDINGS §14's
problem (*a cross-sectional rank on a quantity carrying units ranks those units*) answered by
construction rather than by a normalisation that failed.

**The scores** (`scripts/ragged_sign_scores.py`, committed, causal by truncation audit — all three
identical on 2,786,556 cells): `up_run_21`, `sign_flips_21`, `up_frac_21`.

---

## 1. The direction, DECLARED — and §4.2's objection answered rather than ignored

§4.2 said: *"Direction: undeclared until Stage 0 … a candidate whose direction cannot be declared
is a candidate whose mechanism is not yet written."* **Gate 1h forbids running it that way**, so
either a mechanism gets written or the candidate does not run.

**The mechanism, drawn from the record rather than invented.** Sign persistence measures
**one-sided participation**. This universe's long side is *reversal*-shaped, twice measured:

- **FINDINGS §31:** *"Every E1 member on a reversal-type score has positive timing"* — `rev_5` +42,
  `rev_21` +38, `hist_L` +46 bp over their own names at random times.
- **FINDINGS §39:** on the floored universe **the loser decile rises**.

> **DECLARED DIRECTION: LONG on a sustained DOWN-run** — a low `up_run_21` / low `up_frac_21` /
> low `sign_flips_21` is a name under sustained one-sided selling, and on this universe that
> reverts.

A result in the opposite direction is reported **DIRECTION-INVERTED** and **counts against the
mechanism** even if the number is good.

**The doubt is retained, not dropped.** §4.2 recorded: *"magnitude-free may also be edge-free. A
signal that discards how far price moved has discarded most of what a return is."* That is the
principal's reservation and mine, and **Q1 below is written to expect exactly it.**

---

## 2. Stage 0 — the kill conditions, committed before the runner

Instrument: `scripts/d268_score_independence.py`'s method, as D390's Stage 0 used it — the
correlation structure **within each bar over eligible names** (the operative lens, since selection
is cross-sectional), with the pooled within-name reading beside it for comparability.

| | condition | verdict if it fires |
|---|---|---|
| **K1** | \|ρ\| > 0.5 against `rev_5`, `rev_21`, `trailing_return` or `mom_252_21` | **it is trailing return with the magnitude thrown away, not a new input.** Drop it |
| **K2** | \|ρ\| > 0.5 against `rvol21` or `atr_norm` | a volatility proxy; drop |
| **K3** | the three sign scores carry **< 2.0 effective inputs** among themselves | one statistic wearing three names; pick one and say which |

**K1 IS THE EXPECTED KILLER AND THIS RECORD SAYS SO IN ADVANCE.** Fifteen up days out of
twenty-one is, mechanically, a positive trailing return. The whole claim is that *magnitude-free*
buys independence; K1 is the measurement that decides whether it does. **If K1 fires the record
stops at §2** and the finding is that discarding magnitude does not discard the momentum tilt.

**Stage 0 also reports, before any null:**

1. **The exposure arithmetic, computed before it is predicted** (§38 rule 2): entries per bar ×
   hold = open positions.
2. **The D392 atlas floor for this candidate's own pool, declared in advance** — looked up with
   `run_d392_base_rate_atlas.lookup(atlas, trades, cap, side, pool)`, which **raises** outside the
   grid rather than extrapolating. The pool is named in §3 *before* the number is seen.
3. **The four groups with the top trade NAMED and its bar printed** (D322).

---

## 3. The construction, frozen before Stage 0 runs

- **Universe:** floored (`keep_v2`), deal-filtered (F0), eligible, after the hedge is defined.
- **Score:** the sign statistic at **t−1**, cross-sectional percentile among ≥50 finite names,
  through `run_d350.lagged`'s pipeline (floored → F0 → warm-based → shifted one bar).
- **Event shapes:** E1/E3 as `run_d350.shape_masks` defines them — E1 a fresh entry into the
  bottom decile, E3 the recovery out of it. **E2 is not run**: it is the top-decile entry, the
  wrong end for a declared reversal long, and running it would be a direction sweep.
- **Entry:** LONG at the next open (D340), every event taken, no slot cap, hedged against the
  floored universe's equal-weight return, truncated at delisting.
- **Exit:** cap ∈ {5, 10, 20, 40, 60} reported in full and **not picked** (R14's fourth
  amendment). **Primary cap 20**, declared now as the grid's midpoint.
- **Atlas pool for H1's floor:** **`ALL`**, declared now. The mechanism claims *no* tilt on price,
  volatility or momentum — so the unconditional floor is the honest comparator, and if Stage 0's
  correlations say otherwise the conditional pool is used instead **and the record says the pool
  changed and why**.

---

## 4. The nulls

On the primary exit, every null's events satisfying the observed events' eligibility mask (D351),
asserted per draw batch. Every p95 carries its **bootstrap SE**; a margin within **2 SE** is
**UNRESOLVED**, never passed (D369). **None of these is a finite group**, so C2b's enumeration
remedy does not apply and the SE is the only guard — stated so its absence is a decision.

- **A′** — each name's events rotated within its eligible bars. **2,000 draws.**
- **B** — each event's name replaced by a random eligible name in the same `rsi` bucket that day.
  **1,000 draws.**
- **B_s** — **load-bearing.** Each event's name replaced by a random eligible name **in the same
  `rev_21` decile** that day. **2,000 draws.** *This is §52's rule applied before the fact: if the
  sign statistic is a trailing-return proxy, this null holds the trailing return fixed and the
  candidate has nothing left.* K1 tests that as a correlation; B_s tests it in money.
- **C** — random direction on the per-trade ledger. **2,000 draws.**

---

## 5. The hurdles — each names its PARTNER (D289 sixth amendment)

| | hurdle | partner |
|---|---|---|
| **H1** | **Signal (R15).** Gross mean per trade > 0, above the p95 of A′, B, **B_s** and C against a **best-of-10 floor** (§7), **and above the D392 atlas floor for the declared pool** | **H2** |
| **H2** | **Size (1c′).** Gross ≥ 1.0× the measured round trip, **beside the per-bar edge on the deployed base at the same hold**; clearing the ratio while the per-bar edge falls versus a shorter cap is **HOLD-DRIVEN**, not clearing (D289 seventh) | **H1** |
| **H3** | **Capturability (1e).** Open-entry t ≥ 2.0 **and** retention ≥ 50% | each other |
| **H4** | **Breadth (H4′).** `names_to_half_share` ≥ the p05 of A′ on this study's own draws | — |
| **H5** | **Independence (1d′).** ρ to S1, S2 and the retired S6/C9 against the p95 of the pair distribution **in this candidate's own pool** — **and a paired difference of means on matched bars beside it**, because ρ is blind to level and failing 1d′ alone is a **REPLACEMENT** question | **the paired means test** |
| **H6** | **Cost, reported not gating.** Net PB and PUB; the held names' **measured** Corwin–Schultz half-spread; breakeven; turnover, holding run, dead share (1g) | — |
| **H7** | **Horizon (1i).** The cap profile in full; an edge peak is horizon-**unresolved** — **with the per-name effect at the peak beside `t`** | the per-name effect |

**Both lenses, never on the same statistic** (FINDINGS §10).

---

## 6. Predictions

**Q1 is against the candidate and is the expected outcome.**

| | prediction |
|---|---|
| **Q1** | *(against)* **K1 FIRES**: at least one sign score correlates \|ρ\| > 0.5 with `rev_21` or `trailing_return`, and the record stops at §2. Fifteen up days of twenty-one is a positive trailing return |
| **Q2** | K2 does **not** fire — sign statistics are not a volatility proxy; \|ρ\| to `rvol21` stays under 0.3 |
| **Q3** | K3 clears: the three carry ≥ 2.0 effective inputs, because a run length, a flip count and a mean are different reductions of the same sign vector |
| **Q4** | *(against)* exposure ≥ 90% on the primary cell — a decile crossing on ~700 eligible names is not a flat sleeve, and D358's arithmetic says so before the run |
| **Q5** | if Stage 1 runs, the book is **inside B_s's p95** — the same mechanism as Q1, measured in money rather than in correlation |
| **Q6** | the declared direction holds: the low end of the sign statistics is the profitable long end, not the high end |

---

## 7. The search cost, stated

**Multiplicity 10** — 2 shapes (E1, E3) × 5 caps — and H1 is measured against a **best-of-10
floor**, the maximum over cells **within each draw**, as D367 and D373 built theirs.

**Under R13, what carries.** D350's 138 and D352's 139 members **do not carry**: this family is not
in that pool (`run_d350.load_pool` enumerates 46 names and this is not among them), so that screen
did not shape this search. **What does carry is one look** —
`docs/research/the-signal-hunt-part2.md`'s eight-candidate enumeration, disclosed as the space this
was drawn from, and D392's conditional table, which is why this candidate was promoted over B2.
**Disclosed, not summed into a floor no measurement could clear** (R13's corollary).

**This record spends no holdout read.**

---

## 8. Assertions the runner must carry

- **[L]** from `scripts/lag_audit.py` — `assert_slot_lagged` or `assert_mask_is_lagged` as the
  construction requires, **plus `raises_on_broken` on a deliberately unlagged input.** *D391
  listed this requirement and did not implement it; that is the reason the shared helper exists,
  and this is the first record written after it.*
- **[T]** the scores are causal — `ragged_sign_scores.py`'s truncation audit, re-run in the runner
  rather than trusted from the module's own self-test.
- **[E]** every null event satisfies the observed events' eligibility mask (D351), per draw batch.
- **[Bs]** `B_s` draws only from the event's own `rev_21` decile on that bar, never an event name;
  pool membership asserted per draw.
- **[N]** each null's centre reported against the universe base rate; a null centred far from it
  fails the run rather than earning a mechanism.
- **[P]** the JSON is **persisted before it is rendered** (D371 lost its evidence to a `KeyError`
  in a print loop; D391's runner reproduced the same defect).
- **[X]** the self-test **RAISES** on (a) the declared direction flipped and (b) a `B_s` draw from
  the wrong decile.

---

## 9. What would make me abandon this

- **K1 fires** (Q1, expected) → **record it and stop.** Do not sweep window lengths looking for one
  that decorrelates: that is the search that produced D366's gate, which cleared 164 standard
  errors and then failed out of sample.
- **The book is inside `B_s`** → the sign statistic is `rev_21` without the magnitude, and §52's
  rule closes it the same way it closed the winners' dip.
- **The direction inverts** → DIRECTION-INVERTED, recorded as counting against the mechanism.
- **Any hurdle needs a holdout read** → **do not spend it.**

---

**Status footer.** No runner exists. `docs/BOOK.md` holds S1 and S2, neither at capital;
`docs/BOOK_PROP.md` is empty. Nothing here is a result, and **only the principal closes a research
avenue (R15).**
