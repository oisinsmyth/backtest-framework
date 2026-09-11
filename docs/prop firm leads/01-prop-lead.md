# 01 — Six leads toward an initial prop book ~~, and one of them is unblocked today~~

> **THE TITLE'S SECOND HALF IS WITHDRAWN, 2026-09-11.** The lead it referred to was already done.
> Left struck rather than rewritten, because the heading is what a reader indexes on and a silently
> corrected one hides that the record was wrong. **See the amendment block below.**

**Recorded 2026-09-10.** Produced by reading [`BOOK_PROP.md`](../BOOK_PROP.md), the D258–D379 chain
and the consolidated research tree against each other. **This is a LEADS record.**

> **It closes nothing, admits nothing, and elevates nothing.** No measurement was made for it.
> Under [R8](../RULES.md#r8) every item below needs a pre-registration committed **before** its
> runner exists, and under [R15](../RULES.md#r15) only the principal opens or closes an avenue.
> Where it cites the research tree it cites it as **`[EXT]` evidence about the outside world**,
> never as a measurement on any fixture here.

---

## AMENDMENT, 2026-09-11 — **§1 AND §2 WERE ALREADY DONE, AND THE ERROR WAS MINE**

**§1 and §2 below are WITHDRAWN.** They are struck through in place rather than deleted, because a
record that quietly loses its wrong half is not a record.

**What I did.** I built §1 on one line in [`BOOK_PROP.md`](../BOOK_PROP.md) — *"No record here holds
MyFundedFutures' ladder terms, and §4 of D379 is not computable without them"* — and reported it as
a live blocker that the research folder unblocked. **That line is from the D379 amendment of
2026-09-08, and [D386](../decisions/D386-the-prop-account-is-worth-its-buffer.md) discharged it the
same day.** I read the page that stated the gap and not the record that had already closed it.
**That is this programme's own recorded failure mode — tying a claim to a record without reading the
object it points at — and I repeated it.**

**What already exists, and it is more than §1 and §2 proposed:**

| | |
|---|---|
| **MFFU's terms, in code** | [`scripts/d386_full_lifecycle.py`](../../scripts/d386_full_lifecycle.py) lines 248–271 — **five MFFU plans**, with drawdown type and lock level, qualifying-day counters, consistency, cap schedule, payout count, minimum withdrawal, safety net, post-payout floor change, and monthly billing |
| **`P(pass)`** | computed — [`scripts/d386_pass_rate.py`](../../scripts/d386_pass_rate.py); MFFU Rapid 50K **26.3%**, 100K **19.2%** |
| **`V` per evaluation purchased** | D386's results table, 8,000 paths × 600 days, **maximised over a risk grid**, with break-even Sharpe well-defined |
| **the verdict** | **MFFU Rapid EOD is the vehicle** — break-even Sharpe **≈ 0.00**, `$209` one-time, **`$0` activation**, no payout cap, a `$150` qualifying threshold, and **no funded consistency rule.** `V` at Sharpe 1.5 is **`$3,015`** on the 50K against Topstep's **`$916`**, because MFFU averages **4.03 payouts per evaluation against Topstep's 0.52** |

**§5.2 is also absorbed, not open.** D386 does not merely tolerate MFF's absent funded consistency
rule — **it counts it as one of the reasons MFFU wins the table.** Nothing there needs recalibrating.

**What this leaves, and it is the real gap — the INPUT, not the framework.** `d386_full_lifecycle`
draws `rng.normal(dmu, sd)`: **it values a Gaussian trader**, parameterised by `(Sharpe, vol)`. The
prop research's own sharpest structural finding is that this is the wrong object — *"the one quantity
the funded account is priced on is the one quantity the literature does not measure… every screen-4
verdict is therefore a σ-based lower bound on severity, not a measurement"* — and beside it,
**drawdown is 17× more persistent out-of-sample than Sharpe** (R² 0.34 against 0.02). **So D386
parameterises on the unstable statistic and approximates the persistent one with a Gaussian.**

**We hold what the literature does not.** [D259](../decisions/D259-the-extended-session-and-the-overnight-interior.md)
measured C1's actual path — median MAE **0.55%**, **p99 3.98% sitting exactly on the 4% floor**,
worst **13.85%**, 2020's p99 at **7.05%** — fat-tailed and regime-dependent, which a Gaussian at
matched vol cannot produce. That is why vol-targeting cut 2020's breach rate **87-fold**; a Gaussian
model would show almost no such gain.

> **THE NEXT STUDY IS THE JOIN: replace D386's Gaussian increments with D259's measured path.**
> Pre-registered as **[D440](../decisions/D440-the-measured-path-through-the-lifecycle-model.md)**.
> It needs no futures data, and it **supersedes §3** — C1's size sweep stops being *"unsearched
> below 0.48×"* and becomes an **argmax of `V`** on the risk grid D386 already sweeps.

**§4, §5.1 and §6 stand unchanged.** §8's order of work is reissued at the end of this amendment
block.

### §8 REISSUED

| | |
|---|---|
| **1** | **the measured-path join — [D440](../decisions/D440-the-measured-path-through-the-lifecycle-model.md)**, on the equity proxy, now |
| **2** | **D386's own open item 4** — *settle whether MFFU's Rapid floor lock is automatic or purchased; its own pages contradict.* One primary-source read, and everything post-lock rests on it |
| **3** | **the settlement check (§5.1)**, when the futures bars land — **and note it is a KILL-CHECK ON D440's INPUT**, not a refinement of it |
| **4** | **re-run D440 on ES** rather than the proxy |
| **5** | **the hold-length curve (§4)** — still the most speculative, still the only route to a fifth candidate |

**~~1 · `P(pass)` + the ladder~~** and **~~2 · P5~~** are struck from the order: both are done.

---

## 0. The state of the track, stated first

**[D258](../decisions/D258-the-prop-track-candidates.md) fixed four candidates in advance and all
four are resolved.**

| | state |
|---|---|
| **C1** — session-boundary hold | **closed standalone, then REOPENED and clears P4** under vol-targeted sizing |
| **C2** — intraday reversion | **closed** — negative edge in **all seven** asset classes; nineteen of twenty cells negative |
| **C3** — opening range | **closed on SHAPE** — hit rate above 50% with **skew −0.51 to −0.80**, the worse of the two shapes for P1 |
| **C4** — sizing wrapper | never a candidate. **The vol-targeting method is the track's one durable output** |

**C1 as it now stands** ([D259](../decisions/D259-the-extended-session-and-the-overnight-interior.md),
vol-targeted at a 0.4% target, cap 4×):

| | |
|---|---|
| average size | **0.48×** |
| breach rate | **0.06%** — against static 1×'s 2.09% |
| **expected life** | **6.40 years** — P4 needs > 3 |
| annual return | **+4.41%** |
| **expected profit before breach** | **28.20% of account value** |

**A fifth candidate would need a new mechanism, not a new parameter** — the bar has now rejected
three constructions on **shape** rather than on return.

---

## ~~1. `D379 §4` IS COMPUTABLE TODAY — the missing input is already in this repo~~

> **WITHDRAWN 2026-09-11 — see the amendment above. D386 had already done this, on 2026-09-08.**
> The terms below are accurate and the reading of field 21 stands; **what is wrong is the claim that
> anything was blocked on them.** Kept in full because the field-21 geometry is still the right way
> to read the instrument.

[`BOOK_PROP.md`](../BOOK_PROP.md) states the blocker plainly:

> *"**No record here holds MyFundedFutures' ladder terms**, and §4 of
> [D379](../decisions/D379-the-prop-account-is-a-down-and-out-call-and-hurdle-P-has-no-objective-function.md)
> is not computable without them."*

**[`docs/research/Prop-Firm-080926/01-myfundedfutures.md`](../research/Prop-Firm-080926/01-myfundedfutures.md)
holds them in full, fields 16–21** — and they are **not the Apex-shaped ladder the prop synthesis
costed:**

| field | Rapid / Rapid EOD | Builder |
|---|---|---|
| **19 · payout cap per withdrawal** | **NO CAP** — *"There is no cap on how much you can request per payout cycle."* Daily cadence, $500 min, **non-terminating** | **flat $2,000** (50K), **max 5 sim payouts**, then forced promotion |
| **17 · profit split** | **90 / 10** | 80 / 20 |
| **18 · first-payout eligibility** | **24 h after first trade**, buffer cleared, **≥ $500** | ≥ 2 qualifying days, ≥ $500 |
| **21 · what a payout does to the floor** | **locks the floor at `$100` and IT NEVER TRAILS AGAIN** | same |

### Why field 21 is the load-bearing one

> **After the first payout the barrier stops ratcheting.** Distance to breach becomes
> `balance − $100`, permanently. **P1's trailing floor — the thing that killed C1 standalone, and
> the quantity the whole of [hurdle P](../RULES.md#r11) is built around — applies only until the
> first payout.**

**`BOOK_PROP`'s own D379 amendment already prices that difference**: at zero edge on a
Topstep-like eval, a **static** floor gives optional stopping's **40.0%** while a **trailing** floor
gives **26.5%** — *"the ratchet costs roughly 13 points of pass rate."*

**So the object is not "survive indefinitely". It is REACH THE FIRST PAYOUT**, after which the
geometry changes kind, not degree. On Rapid that is 24 hours and $500.

**And it settles D379 §2's open question** — *"the right size is the smallest that reaches the ladder
with high probability, not the smallest that survives"* — because the ladder is now specified:
**on Rapid there is no cap to reach**, so the "size to zero" objection does not bite the way §2
assumed, while on Builder the cap is flat $2,000 × 5 and terminates.

**`[EXT]` caveat, and it is `01-myfundedfutures.md`'s own:** MFFU publishes **no** first-party
pass-rate or payout statistics — `/stats` redirects to a login wall. The figures circulating
(20.35% pass, 28.56% of funded earning a payout) are **secondary with no URL behind them**, and the
payout totals from two secondary sources are **mutually inconsistent**. **Nothing in that tier is
adopted.**

## ~~2. `P(pass)` is computable from machinery that already exists~~

> **WITHDRAWN 2026-09-11 — it was not merely computable, it was COMPUTED.**
> [`scripts/d386_pass_rate.py`](../../scripts/d386_pass_rate.py), and the rates are in D386's own
> table. **The sentence below is true and useless.**

`BOOK_PROP` says so directly: the same **MAE-against-a-ratcheting-floor simulation D259 already
built, stopped at a profit target instead of run to breach** — *"the cheapest of the open items and
it is the missing half of the ladder question."*

**With §1 that closes the valuation end to end:**

```
V  =  N x [ P(pass) x E[payout | funded]  -  fee ]        with N purchasable
fee / P(pass)  =  the acquisition cost of ONE funded account
```

**This is where `BOOK_PROP`'s "20 accounts needed for $50k" line actually lives**, and it has never
been computed with a real ladder.

## 3. C1's value-maximising size was never searched — **superseded by [D440](../decisions/D440-the-measured-path-through-the-lifecycle-model.md)**

> **AMENDED 2026-09-11.** The observation stands: the sweep stopped where P4 cleared and the value
> maximum is at or below its boundary. **What changes is that it is no longer its own study** —
> D386 already maximises `V` over a risk grid, so under D440 this becomes an **argmax of `V`**
> rather than a sweep with no objective. The five caveats below are unchanged and all still live.

| avg size | breach | expected life | ann return | **profit before breach** |
|---:|---:|---:|---:|---:|
| **0.48×** | 0.06% | **6.40 yr** | +4.41% | **28.20%** |
| 0.71× | 0.18% | 2.33 yr | +6.61% | 14.71% |
| 0.95× | 0.57% | — | +8.79% | 6.08% |
| 1.42× | 2.95% | — | +13.04% | 1.75% |

**Profit before breach falls monotonically 28.20% → 1.75% while annual return rises monotonically
+4.41% → +13.04%.** The sweep **stopped at 0.48× because that is where P4 cleared**, so the value
maximum lies **at or below the boundary of the sweep and was never searched** (D379 §2, in its own
words).

**Five caveats `BOOK_PROP` already carries on this table, all still live:** the 0.4% vol target was
chosen **after** seeing the breach data and is not pre-registered; it is **in-sample throughout**;
the path is measured on **equity extended-hours bars, not futures**; +4.41%/yr is **gross of the
firm's own costs**; and **2020 is one event** carrying an 87× improvement.

## 4. Where a FIFTH candidate would come from — the hold-length interior optimum

**The research and this repo hit the same wall from opposite sides, and neither record notices.**

| | |
|---|---|
| `[EXT]` prop research, the shape constraint | *"**THE SCISSORS CLOSE ON LONG WINDOWS, NOT ON SMALL EDGES.**"* Every prop rejection is a **size** rejection — a short window forces contract count up against the **4% MLL**. **Widening the window relaxes the lower bound without touching the upper one** |
| `[REPO]` D259 | **C1's 22-hour window failed on MAE** — p99 3.98% sitting *exactly* on the **4% floor**. The long window blew the same 4% from the **path** side |

> **Both bounds are the same 4%, and they move in OPPOSITE directions with hold length. Nobody has
> drawn that curve.**

**Two independent precedents that an interior optimum is the right expectation:**
D379 found the account's value **non-linear in size with an interior optimum**; and `[EXT]` lane 13
found survival **non-monotone in size** — 8.1% at N=1, **0.5% at N=2–3**, back to 7.8% at N=10 —
*from an entirely separate calculation*, which `BOOK_PROP` notes reproduces D379 §2.

**This is a specification for a new mechanism rather than another parameter on a dead candidate**,
which is what §0 says a fifth candidate requires.

## 5. Two cheap checks that could save the work

### 5.1 The settlement-rule question — the highest-stakes check on the track

`[EXT]` lane 19: China runs the natural experiment the US cannot. Same underlying, same days,
2016-01-11 → 2019-11-29:

| | |
|---|---|
| **T+1 cash index** | **−0.073% (t −4.03)** |
| **T+0 IF future** | **+0.055% (t +3.19)** |

**Opposite signs, both significant.** The claim `[EXT]` makes: **the overnight drift is a property
of the SETTLEMENT RULE, not of the passage of time.**

> **C1 is the only candidate still open, its +9.04%/yr is measured on EQUITY extended-hours bars,
> and it would be traded as a FUTURE. If the drift is a T+1 artefact it may not exist in the
> instrument at all.**

**Falsifier: computable on any fixture holding both SPX and ES.** Recorded as `[EXT]` and **not
adopted** — the A/H same-company design behind it was not read here.

### ~~5.2 P5's stated rationale does not hold at the chosen venue~~

> **WITHDRAWN 2026-09-11 as a loose end.** The fact is right and D386 had already priced it:
> **the absent funded consistency rule is one of the reasons MFFU wins D386's table**, not an
> un-modelled discrepancy. Whether P5 stays as a house standard stricter than the venue remains the
> principal's call — but **nothing is waiting on it.**

[R11](../RULES.md#r11) justifies **P5** with *"consistency rules cap a single day at 30–50%."*

`[EXT]` field 16: **MFF's funded-stage consistency rule is NONE** on Rapid, Rapid EOD and Pro — it
binds in the **evaluation** only (50% / 30%), and Builder's 50% applies at the **payout stage**
against the cycle, not the target.

**`BOOK_PROP` says the venue is decided: *"MyFundedFutures, or nothing"*** — the only firm clearing
both **P2** (a ~22-hour hold from the 18:00 ET Globex open to the 16:10 ET close) and **P6**
(automation permitted at the funded stage).

> **Same shape as the `$5`-floor case in the research consolidation: the hurdle may well stand, but
> the reason written under it does not describe the venue it is being applied to.**
> **[D375](../decisions/D375-the-hurdle-audit-the-stage-one-gates-are-sound-and-hurdle-P-is-half-untested.md)
> already records P3, P4 and P5 as never computed on anything.** **Whether P5 is recalibrated,
> kept as a house standard stricter than the venue, or dropped is the principal's call and nothing
> here decides it.**

**And D379 §5 argues P5 should be computed FIRST regardless:** near the barrier the account's
convexity **inverts** — variance becomes free once the option is nearly worthless — so a
construction exploiting it would **clear P1 and P4 and be killed by P5.**

## 6. Two constraints that sit on all of the above

### 6.1 We hold no futures data

**Everything on this page is measured on an extended-hours equity proxy covering 16 of 23 futures
hours.** `[EXT]` [`futures-data/`](../research/consolidated/data/05-futures-data-sources.md):

| | |
|---|---|
| ES + NQ + RTY + YM, 15 years, `GLBX.MDP3` `ohlcv-1m` | **$30** |
| the Databento signup credit | **$125**, **expires in 6 months**, one set per team |
| `P(MAE ≤ $2,000/contract)` for the last-30-minute trade | **~$8**, inside that credit |

**Three traps, all `[EXT]`:** use `stype_in="continuous"` (**never `parent`**); use
`batch.submit_job`, because **streaming re-bills on retry**; and RTY reaches only ~9 years because
the E-mini Russell moved to CME in 2017.

### 6.2 Screen on the diversified complex, not on four equity indices

`[REPO]`, from the C2 multi-symbol work — **effective breadth of the daily P&L series:**

| book | symbols | **effective** |
|---|---:|---:|
| 4 equity indices — *what C1, C2 and C3 were screened on* | 4 | **1.17** |
| **diversified futures complex** — indices + energy + metals + rates + international | 12 | **3.00** |
| all 55 ETFs | 55 | 2.35 |

**A futures-complex book has 2.6× the breadth of an equity-index book — worth `√2.6 ≈ 1.6×` on IR
for any candidate with a positive edge**, before a second arm is even found. **And 55 symbols give
LESS breadth than 12**, the same saturation [FINDINGS §4](../FINDINGS.md) measured on ETFs.

---

## 7. What this record does NOT claim

- **It does not claim a strategy exists.** The candidate list is exhausted; three constructions have
  been rejected on shape. ~~**What is newly actionable is the VALUATION half**, which turns out to
  have been blocked on a number already in this repo.~~ **AMENDED 2026-09-11: the valuation half was
  already built by D386. What is actionable is the INPUT to it** — see the amendment block.
- **It does not elevate anything.** Every `[EXT]` line is evidence about the outside world, was
  never measured on this fixture, and stays in [`docs/research/`](../research/README.md) under the
  standing ruling of 2026-09-09.
- **It does not amend a hurdle or loosen a threshold.** ~~§5.2 reports that a rationale and a venue
  term disagree. **It does not resolve that.**~~ **AMENDED: D386 had already priced it.**
- **It does not reopen C2 or C3.** Both are closed on measurements, not on assumptions.
- ~~**The `[EXT]` prop figures are `E[extracted] = b` arithmetic on Apex/Topstep geometry**
  ([D386](../decisions/D386-the-prop-account-is-worth-its-buffer.md) is the repo's own version).
  **MFF's field-21 geometry is different and nothing has recomputed it.**~~
  **WITHDRAWN 2026-09-11 — D386 recomputed it, across five MFFU plans, and MFFU wins its table.**
- **AND ONE THING THIS RECORD GOT WRONG, KEPT AT THE END SO IT IS NOT LOST:** its headline lead was
  built on a stated gap without reading the record that had closed it **the same day**. The whole of
  §1 and §2 followed from that. **The failure mode is already in this programme's own memory, and
  the record it was committed to is the one place it should not have happened.**

## 8. Order of work — **REISSUED 2026-09-11, see the amendment block at the top**

**Each needs its own pre-registration under [R8](../RULES.md#r8), committed before the runner
exists.**

| | why it goes here |
|---|---|
| ~~**1 · `P(pass)` + the ladder (§1, §2)**~~ | ~~cheapest, uses machinery that exists~~ — **STRUCK: done by D386, 2026-09-08** |
| ~~**2 · P5 (§5.2)**~~ | ~~D379 §5's argument~~ — **STRUCK: priced by D386 as a reason MFFU wins** |
| **1 · the measured-path join** — [D440](../decisions/D440-the-measured-path-through-the-lifecycle-model.md) | D386 values a **Gaussian** trader; D259 measured a **real** path. Nobody has run one through the other, **and it needs no futures data** |
| **2 · the floor-lock check** | D386's own open item 4 — *its own pages contradict*, and everything post-lock rests on it |
| **3 · the settlement check (§5.1)** | when the bars land. **A kill-check on D440's INPUT**, not a refinement of it |
| **4 · re-run D440 on ES** | the proxy covers 16 of 23 hours; the instrument is the object |
| **5 · the hold-length curve (§4)** | the search direction for a fifth candidate, and the most speculative |

**Data acquisition (§6.1) gates 3, 4 and 5 on real futures bars rather than the equity proxy.
Items 1 and 2 do not wait on it.**
