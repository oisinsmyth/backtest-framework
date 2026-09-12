# D484 — RESULT: the log MACD is a real signal that fails only on cost, and the off-diagonal ordering is confirmed

**2026-09-12.** Runner [`scripts/d484_offdiagonal_and_macd.py`](../../scripts/d484_offdiagonal_and_macd.py) ·
artifact [`data/d484_offdiagonal_and_macd.json`](../../data/d484_offdiagonal_and_macd.json) ·
pre-registration [D484 PRE-REG](D484-PRE-REG-the-off-diagonal-lookback-and-the-log-impulse-MACD-as-momentum-signals.md),
committed before the runner existed.

**PROVENANCE NOTE:** the runner's first commit was swept into another session's commit
(`2f48f6e`, an unrelated retail-flow note) because that session committed while my file was
staged in the shared working tree. The code there is correct but misattributed; I did not
rewrite a commit a live session had just made.

8 roots, 2016-01-04 → 2023-12-29, ~44,000 contract-pure hourly bars each. 2024+ sealed.

---

## 1. The verdicts

| part | P1 pooled | vs R1 p95 | P2 family max | vs R1 family p95 | verdict |
|---|---:|---:|---:|---:|---|
| **A** off-diagonal lookback | −0.00317 | **−62.2 SE** | +0.01784 | **−23.5 SE** | **FAIL both** |
| **B1** log **impulse** MACD | **+0.00961** | **+39.6 SE** | **+0.03256** | **+13.8 SE** | **PASS both** |
| **B2** plain log MACD | **+0.00720** | **+32.4 SE** | **+0.03369** | **+24.3 SE** | **PASS both** |

**This is the first pass in the entire momentum sequence.** Both MACD variants clear both
pre-registered bars, on eight instruments, against a null that preserves the signal's own
autocorrelation.

**And the pass is not an artefact of a lenient null — it is the opposite.** Z-e held: R2 (the
naive per-observation shuffle) has p95 **+0.00255** against R1 (rotation) **+0.00433**, so the
shuffle is **1.7× too narrow**. Had I used it, MACD would have looked *more* significant than it
is. The pre-registration's reasoning for making the rotation primary was right, and MACD passes
the *stricter* of the two by a wide margin.

## 2. And it is not tradeable — §5, which the first version of this runner failed to compute

| root | micro | best cell | σ ticks | cost ticks | gross ticks | **net** | **gross/cost** |
|---|---|---|---:|---:|---:|---:|---:|
| ES | MES | B1, H=5 | 63.7 | 3.409 | 0.922 | **−2.487** | **0.27** |
| NQ | MNQ | B2, H=5 | 217.0 | 7.009 | 3.849 | **−3.160** | **0.55** |
| YM | MYM | B2, H=5 | 137.0 | 7.009 | 1.978 | **−5.031** | **0.28** |

**0 of 84 costable cells is net positive.** The best reaches **55% of its cost**.

**An edge in σ units only becomes money when multiplied by σ in ticks**, and that conversion is
the whole of this table. A pooled +0.0096 σ is overwhelming against a null and small against a
fixed fee.

## 3. The arithmetic that says exactly what would unlock it

*Post-hoc consequences of the measured edge, not pre-registered tests.*

**On a FULL NQ contract the signal is already profitable.** NQ's tick is worth $5.00 against
MNQ's $0.50, so a $3 commission is **0.60 ticks** instead of 6.00:

    NQ full:  cost = 0.60 + 1.009 = 1.609 ticks   against gross 3.849   ->  NET +2.24 ticks

**But `COMPONENTS_PROP.md` C-d forbids it.** One full NQ contract runs a daily σ of roughly
465 ticks × $5 = **$2,326**, against the standard's **$500** cap for a $50k account — **4.7×
over**. This is D469's structure exactly, repeated on a different instrument: *the micro is the
only size the account admits, and the micro's per-contract fee is what kills it.*

**So the binding constraint is the fee, and it can be priced:**

- **MNQ needs commission ≤ $1.42** per round trip (budget = (3.849 − 1.009) × $0.50), against
  the $3.00 D466 declares.
- **MES is hopeless at any commission**: gross 0.922 ticks is *below* the 1.009-tick crossing
  alone, so even a zero-fee broker loses.
- **The two best cells overall sit on GC and CL** (+0.0326 and +0.0337 σ) — and neither has a
  micro in the committed specs, so §5 could not cost them. **The strongest signals are on the
  roots I cannot price.** That is a real limitation of this record, not an omission, and MGC and
  MCL do exist in the world.

## 4. The principal's structural point is confirmed — Z-c held

**Off-diagonal beats diagonal: −0.00317 against −0.00525**, and **the best Part A cell is
L=13, H=5 — a lookback 2.6× the holding period.** The top of the Part A table is dominated by
L ≥ 8 with H ≥ 3, and the bottom by L=1.

So decoupling the lookback from the hold **is** the right structural move and D474/D475 were
measuring a worse construction than they could have. **It does not rescue raw sign momentum** —
Part A still fails both bars, at −62 SE pooled — but the ordering the principal predicted is
real and is now measured rather than assumed.

## 5. Predictions

| | prediction | outcome | |
|---|---|---|---|
| **Z-a** | Part A pooled fails R1 | HELD | −62.2 SE |
| **Z-b** | Part A family max fails too | HELD | −23.5 SE |
| **Z-c** | off-diagonal beats diagonal, best cell L>H | **HELD** | L=13, H=5 |
| **Z-d** | B1 zero state > 40% **and** B1 beats B2 | **BROKEN** | zero state only **14.4%** |
| **Z-e** | R2 narrower than R1 | HELD | +0.00255 vs +0.00433 |
| **Z-f** | nothing tradeable at micro cost | HELD | 0 of 84 |

**Z-d broke on its first clause only.** B1 *did* beat B2 pooled (+0.00961 vs +0.00720), as
predicted. But the impulse zero state covers just **14.4%** of bars, not the >40% I expected —
the synthetic check showed 100% zero in a range and 0% in a trend, so real markets sit *outside*
the band far more often than I assumed. **The impulse filter is barely filtering**, and B1's
small advantage over B2 therefore cannot be attributed to the no-trade state. That attribution
is untested and I am not claiming it.

## 6. What this changes

- **Price-path momentum is no longer uniformly dead.** D471/D473/D474/D475 closed sign-momentum
  from 10 seconds to 5 hours. **A smoothed, log-price MACD is a different construction and it
  carries real information** — which is a direct instance of the *construction vs axis* lesson,
  this time in my favour rather than against me.
- **The obstacle is now unambiguously cost, not signal.** That is a better problem: it has
  numbers attached (§3) and it points at the account's size constraint rather than at the market.
- **It admits nothing.** A gross edge that reaches 55% of cost is a signal, not a trade
  ([R15](../RULES.md#r15)). Nothing enters `COMPONENTS_PROP.md` or either book, and **2024+
  stays sealed.**

## 7. What is owed next, and none of it is authorised by this record

1. **Cost the GC and CL cells** — the two strongest signals, on roots §5 could not price. MGC
   and MCL specs are not in `data/futures_contract_specs.json` and would have to be fetched
   from CME as `futures_contract_specs.json` was.
2. **The volume-clock exit (D472, +1.18 pp) is not applied here**, so every net figure above
   understates. On NQ that is worth checking against the 0.55 ratio.
3. **A parameter search is the obvious temptation and is explicitly refused.** 12/26/9 and 34/9
   were declared in advance and nothing else was tried. Any search is a separate
   pre-registration and a much more dangerous study.
4. **Is B1's edge the zero state or just the smoothing?** §5 shows the filter is nearly inert at
   14.4%, so the honest hypothesis is that both variants are measuring the same smoothed trend.
   Testing that needs a variant with the band removed.

## 8. Checks, and one failure of mine to disclose

**The first version of this runner did not compute §5's TRADEABLE bar or §6's Z-f at all** —
both pre-registered, both silently absent. That is exactly the failure my standing note names:
*check the runner computes what the pre-reg declared.* They were added and the run repeated; the
nulls are seeded so every other figure reproduced unchanged.

28 self-test checks. Smoothers verified against hand-computed values (EMA seeding and first
step, SMMA's `1 + (2−1)/4 = 1.25`, SMMA slower than EMA at equal n, ZLEMA tracking a ramp with
0.44 error against EMA's 9.47). The impulse zero state is shown to be **100% in a synthetic
range and 0% in a synthetic trend**, so it genuinely discriminates — which is what makes its
14.4% on real data a finding rather than a bug. `edge_sigma` recovers a planted 0.05 σ edge,
reads ~0 on unrelated series, is scale-free under ×1000, and ignores zero signals.

**Two self-test failures during construction, both my test rather than the code, and the second
was instructive:**

- A disagreement check asserted L=1 ≠ L=13 at **one hand-picked bar** where they happened to
  agree. The meaningful claim is that they are different *series*; they disagree on **40.6%** of
  bars.
- The "autocorrelated signal" used to justify the rotation null was `sign(diff(random walk))` —
  but **a random walk's increments are independent**, so that series is i.i.d. and the check was
  comparing two near-zero autocorrelations. It could not have distinguished the nulls at all.
  Replaced with the real constructions, which read lag-1 ρ of **+0.748** (L=13 lookback, whose
  consecutive signals share 12 of 13 increments) and **+0.886** (impulse MACD histogram).
  Rotation preserves both exactly; the shuffle drops them to +0.004 and −0.007.

**Profiled before launch:** 5 ms per root-draw → **4.0 min**. I expected far worse — wrong for
the third time in this session, which is why CLAUDE.md says profile first.

Runtime gates: every root's own G1–G5 read and required to pass, RTY excluded on its stated G2
failure, `same_front` only, contract-pure over the trailing 78 bars, and a raising gate on any
row past 2023.
