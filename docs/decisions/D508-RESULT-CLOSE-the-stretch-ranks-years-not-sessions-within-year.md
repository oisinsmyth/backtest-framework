# D508 RESULT — CLOSE: the 200-day stretch ranks **years, not sessions**. Within a year it runs the other way, and the top quintile loses to a random gate of matched persistence

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D508-RESULT-CLOSE-the-stretch-ranks-years-not-sessions-within-year-it-runs-the-other-way-and-the-top-quintile-loses-to-a-matched-random-gate.md`. The H1 above is the full title.*

**Result of D508** (spec `c47feae`). Runner `scripts/run_d508_stretch_ranker.py --run`
(`--selftest` passes, eight checks; seconds), artefact `data/d508_stretch_ranker.json`, quintile
table `data/d508_quintiles.csv.gz`. **1,876 sessions, 2016-01-04 → 2023-12-29. The arm's 2024+ slice
was not scored** (see §1).

## 0. The arm is reproduced exactly, which is what makes the ranking meaningful

The runner imports the frozen arm — `d504_arm_full_history.build` for the signal,
`d491_conditional_hold.simulate` for the state machine — and reproduces **D504's own published
per-year figures on this window exactly: 1,876 sessions and $15,423 of net P&L against their 1,876
and $15,423.** Nothing about the construction was re-implemented, so what is ranked is the admitted
arm and not a copy of it.

## 1. The primary, and it does not clear its own null

| cell | Spearman ρ | N1 p05 | N1 p50 | N1 p95 | offsets ≥ obs | offsets ≤ obs |
|---|---:|---:|---:|---:|---:|---:|
| **\|log(P/SMA200)\|, the primary** | **+0.0089** | −0.0491 | +0.0035 | +0.0449 | **43.0%** | 57.0% |
| \|log(P/EMA200)\| | +0.0088 | −0.0473 | +0.0023 | +0.0434 | 42.3% | 57.7% |
| signed log(P/SMA200) | **−0.0342** | −0.0502 | +0.0020 | +0.0446 | 86.9% | **13.1%** |
| signed log(P/EMA200) | −0.0334 | −0.0477 | +0.0015 | +0.0438 | 86.7% | 13.3% |

**The absolute measure sits at the 43rd percentile of its own exact rotation.** The N2 family bar
over the four cells and 1,875 common offsets is p50 +0.0158 and **p95 +0.0505**, against an observed
family maximum of **+0.0089** — **58.0% of offsets beat the best of the four real cells.**

**The two-sided read is reported because the signed cells came out negative**, and an upper-tail
share does not test a negative observation. Against the lower tail they do not clear either: −0.0342
against a p05 of −0.0502, at the 13th percentile. The arm does slightly worse when price is further
**above** its 200-day average, and the effect is inside the null on both sides.

**Verdict by the pre-registered rule: CLOSE.**

## 2. The quintile table, which is where it gets interesting

| q | range of \|log(P/SMA200)\| | n | net $/session | gross $/session | net Sharpe | gross Sharpe | gross $/trade | net $/trade | hit | worst | P3a |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.000–0.054 | 376 | +6.63 | +10.06 | +0.61 | +0.92 | +10.28 | +6.77 | 47.6% | −888 | 0.00 |
| 2 | 0.054–0.083 | 375 | +3.58 | +7.27 | +0.35 | +0.71 | +6.90 | +3.40 | 44.0% | −897 | 0.00 |
| 3 | 0.083–0.106 | 375 | +3.54 | +7.15 | +0.36 | +0.73 | +6.93 | +3.43 | 44.5% | −852 | 0.00 |
| 4 | 0.106–0.141 | 375 | +6.92 | +10.50 | +0.68 | +1.04 | +10.28 | +6.78 | 45.6% | −498 | 0.00 |
| **5** | **0.141–0.286** | 375 | **+20.45** | **+23.95** | **+1.36** | **+1.60** | **+23.95** | **+20.45** | 48.8% | −1,315 | 0.33 |

**On its face this is a strong ranking**: the top quintile earns three times the net per session of
any other and more than double the gross per trade. **Two controls dispose of it.**

**(a) N3, the control the record declared as the decider.** A random persistent gate matched on
**both duty cycle and run-length distribution** — 20% duty, 2,000 draws — has p50 **+0.797** and p95
**+2.136**. The observed top quintile is **+1.364**, and **23.9% of matched random gates beat it.**
A persistent one-day-in-five gate on a regime-concentrated arm is worth a great deal by accident,
because it sometimes lands on the regime that carries the P&L. The top quintile is inside that band.

**The band is four times wider than D502 measured** (+0.797 here against ≈ +0.2 there) because
D502's gate ran at ~82% duty and this one at 20%: the fewer sessions a gate keeps, the more of the
arm's concentration it can catch or miss. **Prediction X-d assumed D502's number would transfer and
it does not — a matched-random band must be recomputed at the duty cycle actually used.**

**(b) N4, the year-proxy decomposition, and it reverses the sign.**

| 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | mean | pooled |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| −0.055 | −0.066 | −0.028 | −0.070 | −0.062 | −0.059 | **+0.055** | −0.049 | **−0.0419** | **+0.0089** |

**Within a year the relationship is negative in seven years of eight, averaging −0.042, while the
pooled figure is +0.009.** That is a sign reversal between the pooled and stratified reads. The arm
is a regime construction — 2020 and 2022 carry most of its in-sample P&L — and those are also the
years price sits furthest from its 200-day average. **The stretch is ranking which year it is, not
which session to trade**, and once the year is held fixed it ranks the wrong way.

## 3. Predictions

| | predicted | observed | |
|---|---|---|---|
| X-a | pooled ρ in [+0.02, +0.06], clears N1 | **+0.0089**, does not clear | **wrong** — smaller than predicted |
| X-b | within-year mean \|ρ̄\| < 0.03, pooled mostly a year proxy | **−0.0419**, pooled a year proxy | half right: the proxy diagnosis holds, the size and **sign** were wrong |
| X-c | net Sharpe rises q1→q5 while gross per trade rises much less or falls | net +0.61 → +1.36, **gross $/trade +10.28 → +23.95** | **wrong** — gross rises as much as net, so this is NOT D502's cost channel |
| X-d | the N3 band near +0.2, top quintile not beating it by > 1 SE | band p50 **+0.797**, 23.9% of gates beat the observed | conclusion right, **band level wrong by 4×** (see §2a) |
| X-e | SMA and EMA agree within 0.01 of Spearman | **0.0001** | right |
| X-f | the signed versions are weaker than the absolute | signed **−0.034** against absolute +0.009 | **wrong** — signed is larger in magnitude, with the opposite sign |
| X-g | the verdict is CLOSE | CLOSE | right |

**Three of seven.** X-c is the most useful miss: I expected D502's finding that a regime cell raises
net and lowers gross, and here **gross rose with net**, which means the top quintile is not an
artefact of trading less. It is an artefact of *which sessions* it trades, and N3 and N4 are what
show that.

## 4. What stands

- **CLOSE recommended for the 200-day stretch as a ranker of this arm**, absolute or signed, SMA or
  EMA; the principal closes. The absolute measure is at the 43rd percentile of its own rotation, the
  family maximum is beaten by 58% of offsets, the top quintile is inside a matched-random band, and
  the within-year relationship has the opposite sign to the pooled one.
- **The measurement worth keeping is the sign reversal itself**: a conditioner that ranks a
  regime-concentrated arm pooled can rank it backwards within each regime. **Stratify any conditioner
  on this arm by year before believing it**, because the arm's P&L is concentrated in two of eight
  in-sample years and any conditioner correlated with "which year" will inherit that.
- **And a matched-random band must be computed at the duty cycle in use.** D502's ≈ +0.2 was measured
  at 82% duty; at 20% duty the same construction gives +0.797. Quoting the old number would have
  passed this cell.
- **Nothing was spent.** The arm's 2024+ slice was never scored: `simulate` is row-independent
  (asserted in the selftest), so the sessions were clipped before simulating and 2024 onward was
  never evaluated. The daily close series is read in full only because the 200-day average needs the
  history before the window, and only closes at or before d−1 are ever used.
- **This could not have promoted anything in any case** (§0 of the spec): the arm has no unread slice
  on NQ, so a ranker found here could never have been confirmed.

## 5. Files

Runner · this record · the artefact · the quintile table · PICKUP.
