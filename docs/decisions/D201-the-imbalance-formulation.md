# D201 — the imbalance formulation, with and without stops

**Status:** Pre-registered — written and committed BEFORE the run
**Date:** 2026-08-24
**Category:** Signals & strategy interface
**Source:** the formulation tabled during D197's design, and a counts-only census run before this document

> A result section will be appended and nothing above it edited.

## What this is, and why it is not a fourth refinement

D200 closed the S6 reversal line. This is outside that closure and the distinction is
mechanical, not rhetorical:

```
D_below   = sum of POSITIVE net over buckets BELOW the close      (demand underneath)
S_above   = sum of NEGATIVE net, as a magnitude, ABOVE the close  (supply overhead)
imbalance = (D_below - S_above) / (D_below + S_above)              in [-1, +1]
```

The closed line read the single bucket **at** the price and could only speak on the ~20% of
bars outside the erasure envelope. This reads the **whole field on both sides**, excludes
the bucket at the close entirely, and has an answer on every bar. It claims net inventory
skew predicts *direction*, not that inventory at a boundary predicts *reversal*.

**It is still the same map, whose placement D197 measured at −0.007 and −0.012.** A map can
be locally uninformative and carry real aggregate skew, so that verdict does not settle
this — but the prior is unfavourable and this document is not going to pretend otherwise.

## The census, run before this document

Counts only. It answered the design question it was built for and then raised a worse one.

| | BTC erased | BTC raw | ETH erased | ETH raw |
|---|---:|---:|---:|---:|
| defined readings | 3,990 | 3,990 | 2,940 | 2,952 |
| median \|imbalance\| | 0.653 | 0.644 | 0.497 | 0.595 |
| **sign flips, whole decade** | **9** | 13 | 13 | 29 |
| one flip per | 443 bars | 307 | 226 | 102 |
| cost drag at 40 bps | 0.7%/yr | 1.0% | 1.3% | 2.9% |
| **share of bars LONG** | **89.4%** | **93.3%** | 62.2% | 70.0% |
| longest single sign run | **3,504 bars** | 3,633 | 1,793 | 1,985 |

**No deadband is pre-registered.** The worry that drove the census — that an always-in rule
would flip every few bars and pay 40 bps each time — is refuted. Turnover is negligible.
`X = 0` stays, parameter-free.

### The two things the census actually found

**1. The effective sample is nine decisions.** BTC's erased field changes sign **nine times
in eleven years**. This is not a strategy with 4,000 observations; it is a strategy with
nine, and every Sharpe it produces is the product of nine regime calls. Any null
distribution against it will be wide and almost nothing will be resolvable. That is stated
here so a pass cannot later be read as well-evidenced.

**2. It is long 89–93% of the time, and that is mechanical.** In an uptrend price sits near
its highs, so almost all accumulated mass is *below* it — `D_below` dominates `S_above` by
construction, not by insight. Over a decade in which BTC rose roughly 300×, an always-in
book that is long 89% of the time **is buy-and-hold with occasional interruptions**.

That inverts which hurdle matters. In D197 the control was primary and the null was
decisive. Here **buy-and-hold is the control that matters**: a 89%-long book beats it only
if the other 11% adds value, and that is exactly the question worth asking.

### And an answer to a question D197 could not ask

Erased and raw agree on **sign for 93.7% of BTC bars and 92.3% of ETH's**, median
difference 0.084 and 0.165. D197's census found the erasure destroys 70% of pivots and
decides almost everything about the boundary reading. For the aggregate reading it is
nearly irrelevant. The erasure was doing the work in one formulation and not in the other,
which no run before this could separate.

## The rule

Long while `imbalance > 0`, short while `< 0`, flat only when undefined. The signal is read
on bar `t`'s close and the position held from `t+1`, so the close that decides never also
pays — D197–D199's convention.

Sensor is D197's primary throughout: k=2, cluster_atr=0.5. Costs 40 bps a leg, full equity,
no leverage. Nothing is re-swept.

**Two stop policies, which is what was asked for:**

- **no stop** — exit only when the signal flips. The pure test of the reading.
- **with stop** — the same entries plus a protective 2 × ATR(20) level fixed at the price
  the position opened at. After a stop-out the book stays **flat until the signal changes
  state**; re-entering while the signal reads unchanged would simply be stopped again next
  bar, repeatedly. No target — adding one changes two things at once.

**A consequence of that, named now:** sign runs reach 3,504 bars. A single stop-out early in
a long run parks the book flat until the signal flips, which can be *years*. The with-stop
arm must therefore report **share of bars flat**, and a large number there is the
explanation for whatever its Sharpe turns out to be.

**Two fields:** erased (S6 as D197 defines it) and raw (`erase=False`, the pure cumulative
map).

## The bar

Both required, on **both** symbols, on the primary — **erased field, no stop**:

1. **Beat buy-and-hold.** The hurdle that matters, for the reason above.
2. **Beat the matched local-band null by ≥ +0.10 Sharpe**, 500 draws, seed 0.

No baseline hurdle: there is no predecessor book for a rule that did not exist before.

**The raw field is a pre-registered variant, not a second attempt at the bar.** If raw
passes where erased fails, that is **not a pass** — taking the better of two is two shots,
and it becomes a hypothesis for a later document instead. Fixed here, before any number
exists.

Reported alongside: long and short legs separately; share of bars long, short and flat;
turnover and realised cost drag; the by-year split; and **the outcome of each individual
sign flip**, because with nine of them the per-decision detail *is* the result.

## Multiplicity

2 fields × 2 stop policies × 2 symbols = **8 cells**, each against 500 null draws, plus 4
paired comparisons (stop vs none, erased vs raw) = **12 looks**. Own ledger.

The S6 family's 60 looks are **closed** and not merged, but this uses the same map and that
lineage is disclosed rather than laundered by a new document number.

## Predictions

**H1 — the primary fails to beat the null by the floor on at least one symbol.** Predicted
**TRUE**, high confidence. This is the prediction I have been consistently right about
across D197, D198 and D199.

**H2 — nothing beats buy-and-hold.** Predicted **TRUE**, high confidence. An 89%-long book
must earn its keep in the remaining 11%, and every short-side exposure in this family has
lost: short leg worse than long in 16 of 16 cells in D197, and again in 16 of 16 in D199.

**H3 — the stop makes things worse on at least one symbol.** Predicted **TRUE**,
moderate-to-high. A 2 × ATR stop on a position held for a median 28 bars and up to 3,504
will be hit by ordinary noise, after which the book waits for a signal state change that
may be years away. The stop does not tighten risk here so much as convert holding into
absence.

**H4 — erased and raw differ by less than the floor on both symbols.** Predicted **TRUE**,
moderate. The census puts sign agreement at 92–94%. If true, the erasure is decisive for
the boundary reading and irrelevant for the aggregate one — worth having in writing either
way.

**H5 — no cell resolves anything: every null percentile falls between the 10th and the
90th.** Predicted **TRUE**, moderate. A power statement, not a performance one: nine to
twenty-nine decisions cannot separate a signal from a wide null.

**H6 — the long leg outperforms the short leg on both symbols, in every cell.** Predicted
**TRUE**, high confidence.

**The interesting failure mode, named in advance.** If the primary beats buy-and-hold, the
first suspicion is not that the map works but that the book happened to be flat or short
through **one** drawdown — 2018 or 2022 — out of nine total decisions. One lucky regime call
in nine is not an edge, it is a coin landing well. The per-flip breakdown is mandatory
reporting for exactly this reason, and a pass carried by a single flip will be reported as
a failure of evidence rather than a success of strategy.

## Verification

- Look-ahead **guard and poison pair** on the imbalance series (D173, D181).
- The imbalance stays in `[-1, +1]`; the bucket at the close contributes to neither sum.
- `erase=False` leaves `gross` monotone non-decreasing — nothing is ever destroyed — paired
  with a test that the erased field **does** lose mass, so the flag is provably not inert.
- **`PositionResult` pinned against `StrategyResult`** on a non-overlapping book, where the
  two must agree exactly. This pin already earned itself: it caught the position curve
  applying each bar's return to the *previous* bar's position, holding one bar past every
  exit and missing the first bar of every position.
- A flip keeps continuous exposure — the same-bar handoff the trade-list path silently
  drops, which is why a position series exists at all.
- A stopped-out book stays flat until the signal changes state.
- Cost charged once per unit of exposure changed.
- Census reproduces; full suite green; mypy clean; `--report-only` re-renders identically.

---

## RESULT — appended after the run; nothing above this line edited

**No configuration passes on both symbols.** The pre-registered bar is not met by anything.
8 cells, 500 null draws each, 198 seconds.

| cell | Sharpe | B&H | null Δ | pct | long% | flat% |
|---|---:|---:|---:|---:|---:|---:|
| **BTC erased nostop** *(primary)* | +0.677 | +0.756 | −0.052 | 20.2 | 88.8 | 0.7 |
| BTC erased stop | **+0.761** | +0.756 | **+0.718** | 91.4 | 88.7 | 8.5 |
| BTC raw nostop | +0.674 | +0.756 | −0.015 | 35.6 | 92.7 | 0.7 |
| BTC raw stop | −0.207 | +0.756 | −0.814 | 6.6 | 2.4 | **94.3** |
| **ETH erased nostop** *(primary)* | +0.083 | +0.315 | −0.077 | 26.6 | 61.4 | 1.2 |
| ETH erased stop | +0.011 | +0.315 | −0.100 | 34.6 | 17.8 | 45.6 |
| ETH raw nostop | **+0.382** | +0.315 | **+0.112** | 93.4 | 69.4 | 0.8 |
| ETH raw stop | **+0.385** | +0.315 | **+0.110** | 90.0 | 69.2 | 0.9 |

*(Buy-and-hold reads +0.756 here against D197's +0.773 because this book starts at bar 0
rather than at the first signal. Same asset, same fixture, marginally different span.)*

**These are the first positive Sharpes in the entire programme** — and they are positive for
the least interesting available reason, which the next section is about.

### The primary fails cleanly, on both symbols

Erased field, no stop: **−0.052 and −0.077** against the null, at the 20th and 27th
percentile, and below buy-and-hold on both. H1 and the primary verdict are unambiguous.

### Three cells cleared both hurdles, and all three are one decision

`BTC | erased | stop` clears both. Its per-decision breakdown:

| | bars held | log return | share of total |
|---|---:|---:|---:|
| **one long** | **3,503** | +5.117 | **92.4%** |
| the other nine decisions | — | +0.419 | 7.6% |

**A single 9.6-year long position is 92.4% of everything the strategy made.** That is not a
strategy, it is "be long BTC for a decade" — which is why it beats buy-and-hold by **0.005
Sharpe**, a margin indistinguishable from rounding.

And its null delta is not what it looks like. Real +0.761 against a null **p95 of +0.773**:
the real result sits *below* the null's 95th percentile. The +0.718 delta comes from the
null *mean* being dragged to +0.043 by draws that went short at the wrong moments. "Beating
the null by 0.72" here means *being long a rising asset beats a random field that sometimes
shorts it*. It says nothing about the map.

`ETH | raw | nostop` is the same shape: one 1,984-bar long is **77.8%** of the total, real
+0.382 against a null p95 of +0.394 — again below it.

**Every cell that cleared a hurdle is carried by one multi-year long.** The named failure
mode fired, though not in the direction predicted: the document guessed one lucky *short*
through a drawdown, and it is one lucky *long* through the bull run. Structurally identical
— one decision out of ten — and directionally wrong, which is recorded rather than rounded.

### The predictions

**H1 — primary fails the null on at least one symbol.** **CONFIRMED**, on both.

**H2 — nothing beats buy-and-hold.** **FALSIFIED.** Three cells beat it: BTC erased+stop by
0.005, ETH raw+nostop by 0.067, ETH raw+stop by 0.070. None on both symbols, and the BTC
margin is noise, but the prediction as written is wrong.

**H3 — the stop makes things worse on at least one symbol.** **CONFIRMED**, and
`BTC | raw | stop` is the mechanism in its purest form: **94.3% of bars flat, 2.4% long,
Sharpe −0.207**. One stop-out early in a multi-year run parked the book for the rest of the
decade, exactly as the document predicted a 2-ATR stop would do against sign runs of 3,504
bars. The stop did not tighten risk; it converted holding into absence.

**H4 — erased and raw differ by less than the floor on both symbols.** **FALSIFIED.** BTC
agrees (0.003) but ETH differs by **0.299** with no stop. The census measured 92.3% sign
agreement on ETH and that residual 7.7% moved the Sharpe by three floors — because with 16
to 30 decisions, a handful of disagreements is a large fraction of the evidence.

**H5 — every null percentile between the 10th and 90th.** **FALSIFIED.** Four cells fall
outside (6.6, 90.0, 91.4, 93.4). The underlying power problem is real but shows up
differently than predicted: the same sensor family produces **+0.718** on one
symbol/configuration and **−0.814** on another. That spread across configurations *is* the
nine-decisions problem, expressed as instability rather than as narrowness.

**H6 — long leg beats short leg everywhere.** **CONFIRMED, 8 of 8.** Continuing 16/16 in
D197 and 16/16 in D199.

### What the run established

**The mechanical long bias is the whole story.** The census predicted the book would be long
89–93% of the time because in an uptrend almost all mass sits below price. It was, and the
consequence is that the book's Sharpe is buy-and-hold's Sharpe minus the cost of its
occasional departures. Every departure that helped was one long run; every stop that fired
turned a holding into an absence.

**The erasure is irrelevant to this reading, and that answers D197's open question.** Sign
agreement 92–94%; BTC's erased and raw results differ by 0.003. The erasure decided almost
everything about the boundary rule and almost nothing about the aggregate one.

**Nine decisions cannot be tested.** The verdict here does not rest on 4,000 bars. It rests
on ten regime calls per cell, one of which is 92% of the result. No null, however many
draws, can make that a measurement.

### Ledger

**D201: 12 looks, own ledger.** Same map as the S6 family's closed 60, disclosed.

### Recommendation

The imbalance formulation is **not** an edge. What it is, mechanically, is a slightly worse
buy-and-hold with a structural long bias produced by the shape of an uptrend, and the
configurations that appear to beat their null do so because a random field sometimes shorts
a rising asset and this one mostly does not.

The honest closing position on the S6 map as a whole: its placement carried no information
at the bucket level (D197), no information at a boundary under three refinements
(D198/D199), and no information in aggregate here that survives the every-symbol rule.
Testing it a fifth way would need a genuinely new claim rather than a new reading of the
same field, and the same reasoning that closed S1 and the S6 reversal line applies.
