# PROPOSAL — flat-by-default: whose job is it, and what would it actually take?

**STATUS: A PROPOSAL. Nothing under `docs/` is changed by it** except one correction to my own
research record (§5), which is mine to fix. `docs/FINDINGS.md`, `docs/RULES.md` and
`docs/decisions/` are untouched. **Three decisions are asked for in §6 and all three are the
principal's.**

Written 2026-09-08, after the C-line (C1/C1b/C2/C2b) spent a day hunting a market-state gate that
would make a sleeve flat by default.

---

## 0. The short version

**The requirement I was working to is not a programme standard, the programme already assigns it
elsewhere — twice — and the mechanism I proposed for delivering it does not work at the hold
lengths this record uses.** All three of those are quotable from existing records; none is my
finding.

---

## 1. The requirement, and where it came from

On 2026-09-07 the principal set it: *"I want a flat by default strategy that I can incorporate
into my current book, one that is out of the market most of the time."* I recorded it as **P1** in
`docs/research/the-signal-hunt-part2.md` §1 and rebuilt the candidate ranking around it — §2
concluded *"Group C stops being optional. Every candidate in Groups A and B now needs a named
time-series gate before it is a proposal at all."*

**That reordering drove the whole C-line**, and it is the part now in question.

---

## 2. The programme already assigns flatness to the allocator, in two independent places

**[D358](../docs/decisions/D358-RESULT-the-sleeve-is-never-flat-name-level-rarity-does-not-make-time-level-flatness.md)
§2**, in its own words:

> *"Flatness has to come from a time-series condition — a market-level state, an era signal — which
> is exactly **the allocator's job in the principal's multi-strategy book**. The correct reading of
> a sleeve like this one is therefore: **always on when the allocator switches it on**, and its
> series tells the allocator what it earns per unit of capital while on."*

and its rule 1:

> *"For a multi-strategy book that gate is the allocator's, and the sleeve's series is what it
> allocates **to**, not **when**."*

**[FINDINGS §39](../docs/FINDINGS.md) rule 2**, arrived at independently on the short side:

> *"The short side's value is regime-conditional: it exists where the loser cohort falls … **which
> is the allocator's gate, not a signal's.**"*

**And the pipeline agrees by omission — checked gate by gate, not asserted.**
[D289](../docs/decisions/D289-the-promotion-pipeline.md) runs 1a–1i, 2a–2d, stage 3 (R6 + R7 + R10
+ the four groups), stage 4 (the holdout read) and 5a–5c. **Not one of them is an exposure or
flatness gate.**

The near misses are all *reporting* requirements, and that is the pattern:

| | what it requires | gate? |
|---|---|---|
| **D289 2a** | *"say which moved: edge per unit exposure, or cost per trade"* | no — a reporting rule about hold vs cost |
| **D289 1g** | turnover, holding run, dead share | *"reported, no bar"*, in D289's own words |
| **R10** | how many names the book holds at once — mean, max, fraction of bars above a crowding line | reported beside the table; no threshold |
| **FINDINGS §38 rule 2** | entries/bar × hold = open positions, computed before it is claimed | an arithmetic obligation, not a bar |

> **The record already requires exposure to be REPORTED in four places and GATES it in none.** That
> is not an oversight; it is the same division `docs/BOOK.md`'s standing condition 4 states —
> *"A place in the book is not a decision to trade. **Sizing, leverage and capital allocation are
> separate decisions** and are recorded separately."*

> **So flat-by-default has never been a programme standard.** It is a preference for this hunt,
> and the programme's own position — stated twice, and built into the pipeline by omission — is
> that when to be on belongs to the allocator.

---

## 3. And the mechanism I proposed does not deliver it

**`the-signal-hunt-part2.md` §2a says: *"A gate supplies the flatness; the trigger supplies the
breadth."* [FINDINGS §47](../docs/FINDINGS.md) rule 3 says the opposite:**

> *"**A gate that blocks entry is not a flatness mechanism.** If flatness is the goal, the exit has
> to be gated too; entry gating changes which trades are taken, not how long capital is deployed."*

**D367 measured it**: a gate **shut on 90.8% of bars** left a book **invested 91.6%** of them,
holding 22.5 names on average, because the gate blocks *entry* and positions ran to a 252-bar cap.
FINDINGS §47 records the consequence bluntly — *"Every earlier description of this construction as
flat most of the time was wrong."*

**The precise statement, which reconciles that with D361's real 28% exposure at a 10-bar hold:**

> **Entry gating delivers flatness only when the hold is SHORT relative to the gate's off-periods.
> At long holds it delivers almost none. A flat-by-default sleeve needs a gate AND a short hold,
> or a gated EXIT — and a gated exit has never been tested in this programme.**

That is a **design constraint**, not a standards change, and it is the actionable part of this
note: it says what a flat sleeve would have to look like, and names the one construction that
could deliver it and never has.

---

## 4. What the C-line cost, and what it bought

Read against §2 and §3, the C-line was hunting a gate that (a) the programme assigns to the
allocator and (b) could not have produced flatness at the holds in use. It still produced real
measurements, which is why this is a re-framing rather than a retraction:

| | |
|---|---|
| **C1** | breadth has no premise; dispersion appeared to |
| **C1b** | **dispersion is volatility** (ρ 0.774); withdrawn. **Six states, none forecasts the winner cohort** |
| **C2** | the 200-day gate is the state variable, not calm-market — and its exact margin over a random gate of the same shape is **+0.52 bp** |
| **C2b** | all four D361 verdicts stand; every 200-draw p95 was too low |

**The evidence against the gate route is therefore not only structural but empirical:** six states
tested, none forecasts the cohort the candidates live in, and the one surviving gate buys half a
basis point over chance.

---

## 5. The correction I owe, and am making

`docs/research/the-signal-hunt-part2.md` §2a currently contradicts FINDINGS §47. **I am correcting
it in place** — it is my own research record, not a programme standard, and leaving a published
FINDINGS section contradicted by a working note is worse than either reading. The correction
states §3's constraint and cites §47 and D367.

**Nothing else is edited.**

---

## 6. The decisions asked for — all three the principal's

**(a) Is flat-by-default a requirement for this hunt, given §2?**
If it is a *preference* rather than a *requirement*, the candidate list widens immediately: A1's
path efficiency, B2's gap-that-does-not-fill and D393's surviving sign scores all become
admissible without a gate attached, and **the C-line's ranking of Group C above Groups A and B is
withdrawn.**

**(b) If it IS a requirement, should the gated-EXIT construction be pre-registered?**
Per §3 it is the only untested route to genuine flatness. It is a different construction — it
changes how long capital is deployed rather than which trades are taken — and under D289's fourth
amendment that needs its own pre-registration rather than being bolted onto an existing record.

**(c) Should candidates otherwise be judged on the DEPLOYED BASE — what they earn while on?**
The machinery already exists and is already required: `deployed_block`
(`scripts/run_d358_flat_sleeve.py:147`, re-exported by D359) computes return per unit of *deployed*
capital, and **D289's seventh amendment already makes the per-bar deployed edge a required
companion column** under gates 1c′/2c′. So this asks for a reading convention, not new code.

**The structural precedent for (c) is R11's P1**, restated on 2026-09-08:

> *"**So P1 is not a hurdle** … It implies a candidate can *fail* P1, which no candidate can; and
> it hides that P1's real output is a **number** — the post-sizing return … **Size the account so
> trailing drawdown ≤ 4% on OPEN equity. Report the post-sizing return, and judge the candidate on
> that number.** P1 is never reported as PASS or FAIL."*
> — `docs/RULES.md:243-253`

**Exposure is the same shape of thing as drawdown**: not a gate a candidate passes or fails, but a
deployment fact that converts its gross into a number the allocator can use. If (c) is adopted the
convention would read: *a sleeve's claim is its deployed-base return while on; exposure is
reported, never gated; and where flatness matters it is the allocator's decision or an explicit
gated-exit construction, not an entry gate.*

---

## 7. What this note does NOT claim

- **It does not close the gate line.** Only the principal closes an avenue (R15). C2's gated fade
  remains the one short in the record above all its nulls, at a +0.52 bp exact margin.
- **It does not propose trading anything.**
- **It does not amend D289, RULES.md or FINDINGS.md.** If (c) is adopted, D289's stage 5 or the
  seventh amendment is where it would belong — that is a separate edit, on the principal's word.
