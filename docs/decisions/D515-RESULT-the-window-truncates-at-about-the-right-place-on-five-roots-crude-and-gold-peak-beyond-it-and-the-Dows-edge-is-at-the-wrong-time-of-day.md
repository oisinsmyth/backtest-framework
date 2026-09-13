# D515 RESULT — the window truncates at about the right place on five roots, crude and gold peak beyond it, and the Dow's problem is not speed but **time of day**. Nothing clears the family bar

**Result of D515** (spec `78fb1f3`). Runner `scripts/run_d515_horizon_ladder.py --run`
(`--selftest` passes, seven checks; 0.8 min), artefact `data/d515_horizon_ladder.json`.
**2016-01-04 → 2023-12-29, eight roots. A signal measurement: no cost, no flatten, no day-session
constraint. No 2024+ slice was read.**

## 0. The ladder

`edge_sigma` = mean(signal × forward) / sd(forward), on the frozen AGREE state at every hourly
segment, forward from the open of t+1. The arm's window is ~7 segments; a session is 23.

| root | H1 | H2 | H3 | H5 | H8 | H13 | H21 | H34 | peak |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ES | +0.0069 | +0.0114 | +0.0148 | **+0.0164** | +0.0156 | +0.0090 | −0.0094 | −0.0110 | 5 |
| NQ | +0.0117 | +0.0168 | +0.0190 | **+0.0224** | +0.0183 | +0.0045 | −0.0238 | −0.0247 | 5 |
| YM | +0.0041 | +0.0076 | +0.0128 | **+0.0170** | +0.0145 | +0.0103 | +0.0014 | +0.0108 | 5 |
| ZN | +0.0031 | +0.0008 | +0.0013 | **+0.0032** | +0.0010 | −0.0026 | −0.0149 | −0.0209 | 5 |
| ZB | +0.0036 | +0.0051 | +0.0080 | **+0.0111** | +0.0086 | +0.0026 | −0.0091 | −0.0081 | 5 |
| **GC** | +0.0116 | +0.0156 | +0.0186 | +0.0286 | +0.0368 | **+0.0416** | +0.0272 | +0.0193 | **13** |
| **CL** | +0.0120 | +0.0166 | +0.0213 | +0.0268 | +0.0302 | **+0.0354** | +0.0332 | +0.0280 | **13** |
| 6E | −0.0056 | −0.0115 | −0.0133 | −0.0141 | −0.0154 | −0.0129 | −0.0073 | −0.0042 | negative throughout |

**Nothing clears the family bar.** Over 64 cells and 1,625 common offsets the rotation gives p50
**+0.0278** and p95 **+0.0444**, against an observed maximum of **+0.0416** (GC at H = 13) — **7.9% of
offsets beat the best real cell.** Seventeen of 64 clear their *own* single-cell null (all four short
NQ horizons, GC at H1–H13, CL at H1–H2), and **none survives the multiplicity correction.**

**The primary** — pooled `edge_sigma` over YM, CL and 6E at H = 13 — is **+0.0099** against its own
rotation p95 of **+0.0144**, with 13.7% of offsets at or above it. **It does not clear.**

**Verdict by the pre-registered rule: TRUNCATED AT ABOUT THE RIGHT PLACE.** §3 below says why that
label is too coarse for what was found.

## 1. Where in the clock the edge actually is — the decomposition that reframes the question

The principal's hypothesis was **slower**. A one-bar edge split by segment group says the more
important variable is **when**, not how long. Diagnostic `working/d515_where_in_the_clock_scratch.py`:

| root | day segments (what the arm trades) | overnight segments (what it never trades) | reading |
|---|---:|---:|---|
| NQ | **+0.0275** | −0.0008 | the edge is in the day |
| ZN | **+0.0225** | −0.0096 | the edge is in the day |
| ES | +0.0177 | −0.0014 | the edge is in the day |
| GC | +0.0153 | +0.0095 | the edge is in the day |
| ZB | +0.0095 | +0.0001 | the edge is in the day |
| CL | +0.0107 | +0.0142 | even across the clock |
| **YM** | **−0.0004** | **+0.0078** | **the edge is at NIGHT** |
| 6E | −0.0115 | −0.0023 | negative in both |

**The Dow is not slow. It is trading the wrong hours.** Its day-session edge is **−0.0004**, which is
zero, and what little it has is overnight — precisely the hours the arm is forbidden to hold. D514
exonerated the exit; this exonerates the horizon and names the actual cause.

**And ZN's day-session edge is +0.0225, the second largest of the eight** — larger than the S&P's.
The arm still loses $12.83 a trade there. That is D513's addendum's "cost-dead" diagnosis shown at
the signal level: **ZN's problem was never the signal.**

## 2. Why NQ, in one sentence

**NQ has the largest day-session edge of the eight (+0.0275) and the cheapest cost relative to its
move (3.2%, against 6.3% for the next best).** Both, at once. ZN has nearly the same edge and a
$18.62 crossing; YM has the same cost and no day edge at all. The arm needs both and only one root
supplies them.

## 3. The decision rule's label is too coarse, and the record says so rather than hiding behind it

The pre-registered verdict is one of three global labels, and the result **splits by root**:

- **Truncated at about the right place** on ES, NQ, YM, ZN, ZB — they peak at H = 5, inside the
  window, and **turn negative by H = 21**, which is the overnight giving back what the session built.
  FINDINGS §70's off-hours reversal predicted exactly this and it is confirmed here on a second
  statistic.
- **Peaking beyond the window** on GC and CL, at H = 13, and staying positive to H = 34. **The
  principal's hypothesis is the right shape for these two** — and neither clears the family bar, so
  it is a shape, not a finding.
- **Absent** on 6E at every horizon.

**A caveat that must travel with CL.** An existing note records that the D467 fixture **pools
expiries on CL** — *"a flat id→symbol dict merges contracts a decade apart… CL's +1.09 gross Sharpe
is suspect."* This record reads the **breadth** fixture, not D467's, and **I have not verified whether
it shares the defect.** Until someone does, **CL's row here is provisional** and the crude half of the
slow-signal story should not be leaned on.

## 4. Predictions

| | predicted | observed | |
|---|---|---|---|
| X-a | pooled edge on the signal-dead roots at H = 13 in [−0.01, +0.01], not clearing | **+0.0099**, not clearing | right |
| X-b | peaks at H ≤ 8 on ≥ 6 of 8 roots | **5 of 8** | wrong, narrowly — GC and CL peak at 13, 6E at 34 |
| X-c | NQ positive at every H, declining by H = 34 **without turning negative** | NQ turns **−0.0238 at H21 and −0.0247 at H34** | **wrong on the last clause**, and informatively so |
| X-d | pooled over all eight at H = 21 and H = 34 below its H = 5 value | +0.0137 → −0.0010, −0.0019 | right |
| X-e | family p95 in [+0.02, +0.05]; at most two cells clear, one on NQ | p95 **+0.0444**; **zero** clear | band right, and stricter than predicted |
| X-f | the verdict is TRUNCATED AT ABOUT THE RIGHT PLACE | as labelled, but see §3 | right on the label, too coarse for the result |

**Four of six.** X-c is the useful miss: NQ's edge does not merely decay past the session, it
**inverts**, which is the same overnight reversal that closed the hourly clock in D499.

## 5. What stands

- **The principal was not reaching.** The ladder has exactly the shape the hypothesis predicts, on
  the two roots whose price discovery runs around the clock rather than concentrating in the US
  session. **It does not clear a 64-cell family bar**, so it is an observation and not a finding.
- **For the Dow specifically the hypothesis is refuted and replaced**: its day-session edge is zero
  and its edge is overnight. Not speed — time of day.
- **The prop book cannot use either half.** A 13-segment hold crosses the overnight, which P2's
  flatten forbids, and the overnight line is closed for prop. **If any of this is ever pursued it is
  personal-book work at full size**, where the cost line is different.
- **ZN is the sharpest cost-dead case on the board**: the second-largest day-session edge of eight
  roots and a $18.62 crossing against it.
- **CL's row is provisional** pending a check of whether the breadth fixture pools expiries the way
  D467's does.
- **Nothing was spent.** No 2024+ slice was read.

## 6. Files

Runner · this record · the artefact · `working/d515_where_in_the_clock_scratch.py` and its CSV ·
D513's addendum · D514 · FINDINGS §70 · PICKUP.

---

## ADDENDUM, 2026-09-13 — CL's row is CONFIRMED, not provisional. The breadth fixture does not pool expiries on crude

**§3 flagged CL as provisional pending a check of whether the breadth fixture shares D467's
expiry-pooling defect. It does not, and neither does D467's own CL front-month table.** Check:
`working/check_breadth_cl_expiry_pooling.py`.

| test | result |
|---|---|
| the two fixtures' CL midday close, 3,629 common days | **identical to 2.15e-16** relative |
| the two fixtures' CL contract label, same days | **identical on every day** |
| 2019 alone, where the note measured 16 of 140 CL symbols ambiguous | **zero** disagreement over 258 sessions |
| year-by-year midday close against WTI's actual history | 2016 low **$26.84**, 2020 low **$12.11**, 2022 high **$122.59**, 2011 high **$113.83** — all correct |
| the six widest own-session high/low ratios | all **April 2020 on CLM0**, the negative-oil episode, and real |

**Why the defect could not reach the output.** The front-month rule selects by **volume**. A contract
ten years out has negligible volume and never wins the slot, so the ambiguous mapping was filtered
out by the selection before it could reach a session row. The defect is real in the id dictionary and
absent from this table.

**Consequences.** CL's ladder row here stands as measured. The same narrowing applies to D495's CL
gross Sharpe of +1.09, which the standing note asked be treated as suspect on these grounds — it is
not suspect on these grounds. **What remains exposed** is any study reading *all* contracts rather
than the volume-selected front month: term structure, calendar spreads, per-expiry open interest.
Those still need the windowed mapping.

**A check that could not fire, recorded so nobody rebuilds it.** My first version flagged any contract
*label* whose rows span more than a year. It flags **34 of 36 roots, including NQ, ES and YM**, which
the standing note calls clean — because `CLZ5` legitimately denotes December 2015 **and** December
2025 crude under CME's single-digit-year convention. **A recurring label is expected; the defect is
bars attributed to the same session.** The discriminating tests compare the two builders against each
other and the output against an independent reference.

**This does not change any D515 number, verdict or null.** It removes a caveat.
