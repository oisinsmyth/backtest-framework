# working/leads/ — external-evidence briefs for the negative-space leads

**Commissioned 2026-09-09.** One brief per lead of
[`docs/research/the-negative-space-scan.md`](../../docs/research/the-negative-space-scan.md),
each researched against the published literature and primary data documentation by a separate
agent working in parallel.

| file | lead | scan score |
|---|---|---:|
| `R1-cross-asset-regime.md` | cross-asset regime state as the gate — **pre-registered as [D404](../../docs/decisions/D404-the-cross-asset-state.md)** | 18 |
| `X1-residual-reversal.md` | cluster-residual reversal | 17 |
| `K1-calendar.md` | the calendar screen | 17 |
| `N1-short-interest.md` | short interest / days-to-cover | 17 |
| `V1-cef-discount.md` | the closed-end fund discount | 16 |
| `X2-lead-lag.md` | lead–lag between size cohorts | 15 |
| `C1-combination.md` | combining independent weak inputs | 13 |

---

## THE CONTRACT, AND IT IS THE WHOLE REASON THESE SIT IN `working/` RATHER THAN `docs/`

**Nothing in this directory is a finding of this programme.** Every file is a report of what
*other people have published*, assembled by an agent from web sources. That makes it a
fundamentally different kind of object from anything in `docs/`, and it is quarantined here
until it has been read by a human and consolidated.

**Three rules govern how these may be used:**

1. **A brief is EVIDENCE ABOUT THE OUTSIDE WORLD, never a measurement on this fixture.** No
   number in here was computed on any data this programme owns. A magnitude quoted from a paper
   was measured on *that paper's* universe, in *that paper's* era, at *that paper's* cost
   assumption — and this programme's universe is equal-weighted, dead-inclusive, floored at $5
   and charged per share, which is not the universe any of those papers used. **A quoted effect
   size is a prior, not a prediction.**

2. **CITING ONE OF THESE IN A DECISION RECORD REQUIRES CHECKING THE SOURCE.** The briefs carry
   provenance tags — `[PEER-REVIEWED]`, `[WORKING PAPER]`, `[PRIMARY DATA DOC]`,
   `[SALES INSTRUMENT]`, `[UNVERIFIED]` — and the tags are the point. A `[SALES INSTRUMENT]`
   is a vendor, broker or newsletter page whose statistics section is the *sales* instrument;
   the standing rule for that class of source is to compute its claims rather than repeat them.
   **An agent's summary of a paper is not a reading of the paper.**

3. **THEY DO NOT CLOSE ANYTHING AND THEY DO NOT ADMIT ANYTHING.** Under
   [R15](../../docs/RULES.md#r15) only the principal closes a research avenue, and published
   evidence that an effect is dead is a reason to *rank a lead lower*, not a closure. Equally, a
   supportive literature is not a result: every lead still owes its own Stage 0 premise number
   measured on this fixture before any design is written.

**The briefs were commissioned with a deliberate bias toward the negative** — each agent was
asked to hunt for the strongest published refutation, the replication failures, the decay
studies and the "this is just X in disguise" reductions, on the view that a lead killed cheaply
by someone else's published work is the best return available here. **A brief that reads as
enthusiastic should be treated with more suspicion than one that reads as damning.**

## Lifecycle

Under `working/`'s own contract these are in-flight and must not linger. When a brief has been
read and consolidated, its conclusions belong in the scan record's entry for that lead (or in a
decision record), and the brief itself moves to `temp/`. **A file still sitting here across
several sessions is telling you it was never read.**
