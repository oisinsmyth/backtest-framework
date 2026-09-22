# D614 PRE-REGISTRATION — **does the noon 0DTE strike ladder order the last half hour of the ES day session?** The volume-weighted centroid of same-day-expiring option volume accumulated to **12:00 ET**, three and a half hours before the scored window opens, against `1e4·log(P1600/P1530)` on 2016-01-04 → 2023-12-29: the **level** coefficient as the primary (not the interaction the reused code returns), a **grid-only placebo that must fail**, the day's own move and the overnight in the fixed control set, a band family of three, the enumerated session-shift null two-sided with **both tails scored separately**, an **economic bar of 15 bp per sigma** below which a statistical pass closes the line, and the strike-versus-contract commensurability audit the earlier draft lacked; the ES 2024+ slice declared reserved and unread

**Pre-registration committed alone, before the runner exists (R8). In sample 2016-01-04 →
2023-12-29 only.** Nothing admitted (R15). The forward slice exists for this line — D503 spent ES
and NQ 2024+ for the MACD and K8 constructions, and multiplicity is per line, not per file (the
principal's correction of 2026-09-10) — and is **declared reserved, unread, and read only on the
principal's word if the primary passes both the statistical and the economic bar**. A component
line is computed whatever the verdict.

*2026-09-21. **Disclosure, first, because it sets what this trial can and cannot claim.** A first
design of this study was drafted and then put through an adversarial review before any
pre-registration was committed. That review found five specification defects and, to prove the
audits could fire, **measured the in-sample quantities of the 15:30-cutoff version**. Those
readings are therefore no longer blind, and this record does not re-use them as a test: the
15:30-cutoff cells and the whole variance block are carried here as **descriptive measurements
with no verdict weight**, and the trial is spent on a **conditioner that did not exist on disk when
the review ran** — the noon cutoff, built by [D613](D613-FIXTURE-the-ES-option-volume-panel-in-ET-clock-buckets.md).
The prior is set accordingly in §5: 57.5 % of pre-15:30 0DTE volume is already in by noon, so the
noon centroid is correlated with the 15:30 one whose in-sample reading is known to be null, and the
honest prior on a pass is **low**, not raised by the change of variable.*

*The five defects, each fixed below and each named so the fix is checkable: **(1)** the reused
`c_only` in `scripts/stage0_d581_gamma_close.py` returns `beta[2]`, which with `add_constant` is
the coefficient on the **interaction** `F5·F2`, not on the level `F2` — verified here on a
level-only synthetic panel, where the level reads +5.13 and the D581-style `c` reads +0.006 — so a
design reusing it verbatim would have scored a hypothesis the mechanism does not make; **(2)** a
conditioner with **no option content at all** (the equal-weighted centroid of the listed strike
grid) ranked 0.905–0.966 in its own session-shift null, because a band centred on the current price
over a 5-point ladder carries a sawtooth remainder of `P1530 mod 5` worth up to 0.19 sigma against
a mean signal of 0.262 sigma; **(3)** the 15:30 conditioner correlates −0.45 with the 09:30 → 15:30
return and the sign of the pull coefficient flips with the control set, and the accumulation window
is not the session but **00:00 → 15:29 ET**, because the builder's string compare puts the prior
evening's Globex hours outside it; **(4)** on **7.0 %** of sessions the volume-dominant 0DTE
`underlying` is a different contract from the minute bars' front, which displaces `K − P1530` by
about four sigma with a fixed sign in clusters around the quarterlies; **(5)** the concentration
variable is 0.969-correlated with its own Herfindahl floor `1/n`, and D409's imported Dg1 guard
returns +0.05 on every variant including a floor-only placebo, so it **cannot fire**.*

---

## 1. The conditioner, and why noon

From `data/fixtures/fut_es_0dte_volume_cutoffs.csv.gz` (D613), which carries each ES-family
option's traded volume per session in five ET clock buckets. Rows are kept where the option
**expires that session** and `expiry_hhmm >= "15:30"` — the second clause drops the AM-settled
quarterly, which has already expired by the window, and the 13:00 half-day expiries.

| symbol | definition |
|---|---|
| `v12(K)` | `v_0000_1200` summed over calls and puts at strike `K` — **the conditioner's weight** |
| `K12` | `Σ K·v12(K) / Σ v12(K)`, the volume-weighted centroid of the noon ladder |
| **`PIN12`** | `(K12 − P1530)/sigma30` — **the primary conditioner**, signed, in sigma units |
| `PING` | `(mean of the listed strikes in the same set − P1530)/sigma30` — **the grid-only placebo**, no volume |
| `PIN12x` | `(the single heaviest strike by `v12` − P1530)/sigma30` |
| `PIN1530` | the same centroid from `v_0000_1200 + v_1200_1530` — **descriptive only, its reading is not blind** |
| `sigma30` | the trailing-252-session realised sigma of the 15:30 → 16:00 window, **lagged one session** |

**Why the noon cutoff is the whole point.** The scored window opens at 15:30. A conditioner that
accumulates to 15:30 is contemporaneous with the move it is asked to predict, which is defect (3):
it cannot be told apart from the day's drift, and the review showed the coefficient's **sign**
depends on which drift terms are controlled. Volume to noon is fixed three and a half hours
earlier, so the 12:00 → 14:30 and 14:30 → 15:30 price increments become clean controls that sit
strictly between the conditioner and the window. Calls and puts are summed because without an
aggressor side the two cannot be signed apart, and because a strike's hedging demand does not
depend on which right carries it.

**What the conditioner is a proxy for, stated plainly.** `v12` counts **contracts traded, not
position**: 0DTE volume is largely intraday round trips that leave nothing at 15:30, and it carries
no side. Prior-close open interest, the only position measure on disk, predates the day's 0DTE
trading entirely. **Neither variable measures the 15:30 dealer position.** This record claims the
traded-volume proxy and reports the per-session ratio of 0DTE volume to 0DTE open interest so the
size of the gap is on the page.

## 2. The specification, fixed here and not after the read

```
y  = R2                                   = 1e4·log(P1600/P1530), basis points
x1 = ON    /sigma30_bp                    prior 16:00 -> 09:30
x2 = DAY0  /sigma30_bp                    09:30 -> 12:00      (inside the accumulation window)
x3 = MIDE  /sigma30_bp                    12:00 -> 14:30      (after it, before the window)
x4 = F5    /sigma30_bp                    14:30 -> 15:30      (D581's conditioner)
x5 = PING                                 the grid-only placebo
x6 = PIN12                                <- THE PRIMARY, the LEVEL coefficient
x7 = (F5/sigma30_bp)·PIN12                the interaction, a labelled diagnostic, never the primary
```

Ordinary least squares, Newey–West at lag 5, **week-block bootstrap SE on the primary beside**
(1,000 draws, seed stated), and the coefficient read **by name from a column index asserted in an
audit that fires on a column swap** — defect (1). Weighted least squares by `1/sigma30²` is the
declared robustness arm and must agree in sign; it is not a second primary. `y` stays in basis
points so the coefficient is **bp per sigma of `PIN12`** and is directly comparable to the economic
bar.

**The band family.** The primary uses **no band** — every listed strike carries its volume weight —
because a band centred on `P1530` truncates the side the price came from (the review measured the
in-band volume share at mean 0.46, p10 0.23, correlated −0.52 with the day's absolute move), and a
band centred on a pre-session anchor forces the centroid to one side on any day the price has
moved. Both are endogenous; no truncation is not. The `± 4·sigma30` and `± 2·sigma30` bands are the
family's other two members, each with its own `PING`, and **N2 is the maximum of `|c|` over the
three**.

**Session eligibility.** ≥ 380 one-minute ES bars; no roll (`contract` equal to the previous
session's); at least one PM-expiring 0DTE option with positive noon volume; a finite `sigma30` from
≥ 200 prior observations; and — defect (4) — **the volume-dominant 0DTE `underlying` equal to the
minute bars' `contract`**, the session dropped otherwise, with the count reported by era and by
quarter.

## 3. The bars

| # | bar | consequence |
|---|---|---|
| **B1** | `\|c\|` above the **p95 of `\|c\|`** in the enumerated session-shift null of `PIN12`, every other column held fixed | inside ⇒ NOT SUPPORTED |
| **B2** | `\|NW t\| ≥ 2.0` | below ⇒ NOT SUPPORTED |
| **B3** | the family maximum of `\|c\|` above its own N2 p95 | inside ⇒ the reading is one of three looks |
| **B4** | **the placebo `PING` must FAIL its own bar** in the mirror regression (`PING` in the primary slot, `PIN12` controlled) | `PING` passing ⇒ **VOID**: a no-information conditioner clears the same bar, and nothing about options is established. Do not proceed on `PIN12` alone |
| **B5** | **the economic bar: `\|c\| ≥ 15` bp per sigma of `PIN12`** | a statistical pass below it is recorded as **"real but not tradeable"** and **closes the line**. At the mean `\|PIN12\|` the move must beat roughly three times the MES round trip to be worth a Stage 1 (R7's addition: report against doing nothing, not only against the null) |
| **B6** | the sign-flip null (`PIN12 → ε·PIN12`, ε ∈ {−1,+1} per session, **2,000 draws, seed 614** — the one sampled null in this study, because the group is 2^n and not enumerable) places `\|c\|` above its p95 | inside ⇒ the direction carries nothing and only the magnitude did |

**Both signs are scored separately** (the principal's instruction of 2026-09-21). For **every**
cell the result carries the **upper-tail rank** (`c` above the null's p95, the attraction reading,
dealers long 0DTE gamma) and the **lower-tail rank** (`c` below the null's p05, the repulsion
reading, dealers short — the convention D581's own volume build assumed), each with its percentile
and both tail values. The two-sided bar is what the trial is spent on; **a one-sided rank is never
re-declared as the primary after the fact** (D581's kill 3).

**The verdict strings, declared now so none is chosen later.**

| outcome | verdict |
|---|---|
| `PING` passes B1–B3 | **VOID** — the bar is clearable without option content |
| B1–B3 pass, `c > 0`, B5 passes | **SUPPORTED, attraction** — consistent with dealers long 0DTE gamma |
| B1–B3 pass, `c < 0`, B5 passes | **SUPPORTED, repulsion** — consistent with dealers short 0DTE gamma |
| B1–B3 pass, B5 fails | **REAL BUT NOT TRADEABLE** — the line closes |
| B1 or B2 fails | **NOT SUPPORTED** |

## 4. The controls, and the one that cannot be built

**The 2×2 is complete**, which it would not be on the committed D581 fixture alone: that column is
populated only where `expiry_date == session`, so a volume-weighted centroid of later expiries
cannot be formed from it. The D613 panel carries a row for **every** (option, session) that traded,
so the horizon can be moved with the weighting held fixed — the one control the review called
unbuildable.

| arm | holds fixed | destroys | prediction |
|---|---|---|---|
| `PING`, the grid centroid | the ladder, the band, the price | **all** option content | null (B4) |
| **horizon-matched**: volume-weighted centroid of **later** expiries, noon cutoff | the weighting, the ladder | the expiry-day demand | null — **the sharpest control in the study**, because only the horizon moves |
| **weight-matched**: open-interest-weighted centroid of **the same 0DTE strikes** | the horizon, the strike set | the volume weighting | null |
| both-levers: OI-weighted centroid of later expiries | the ladder and the moneyness structure | the demand **and** the weighting | null, and **labelled as moving two levers at once** |

A difference between the primary and the horizon-matched arm is attributable to the expiry alone; a
difference from the both-levers arm is not, and is reported as such rather than as evidence.

## 5. Predictions, and the prior

| # | prediction | falsified by |
|---|---|---|
| P-1 | `\|c\|` on `PIN12` is above the shift null's `\|c\|` p95 with `\|NW t\| ≥ 2` | inside |
| P-2 | `PING`'s mirror coefficient is **inside** its null | `PING` passing, which voids the trial |
| P-3 | all three controls of §4 are inside their nulls, the **horizon-matched** one especially | a control that passes, which says the statistic reads the ladder rather than the expiry |
| P-4 | `corr(PIN12, PIN1530) > 0.6`, since 57.5 % of the volume is shared | a low correlation, which would mean the noon ladder is a different object and the prior should be re-read |
| P-5 | `\|c\|` is larger where `\|PIN12\|` is small (within a ladder step or two) | flat or rising in `\|PIN12\|` |
| P-6 | the commensurability drop removes 5–9 % of sessions, clustered at the quarterlies | a materially different share, which would mean the front-month rule is not what this record thinks |
| P-7 | `sd(PING)` is larger before 2022 than after, because 5 points was 23 bp at ES 2100 and 10.5 bp at 4767 | no era difference, which would mean the sawtooth is not the mechanism behind defect (2) |
| P-8 | the effect, if any, is at least as strong after 2022-05-02, when the Tuesday and Thursday families filled the week | stronger only in the thin early era, which is also where the sawtooth is largest |

**Point prior that P-1 passes: 0.05–0.15.** Lower than a fresh mechanism test would carry, and
deliberately so: D581 conditioned this same `R2` series eight ways and found nothing above its
null; the review measured the 15:30 version of this very conditioner and found `|t| ≤ 0.83` in
every specification it tried; the noon conditioner shares most of its volume with that one; and the
minimum detectable effect at this sample and window is of the order of a few basis points, which is
the same order as the round-trip cost. **This trial is worth spending because the identification is
clean and the placebo is decisive, not because the effect is likely.**

## 6. Power, stated before the run

`sd(R2) ≈ 34.6` bp in sample. The eligible count after every filter in §2 is expected near 1,100
sessions (the review measured 1,263 PM-0DTE sessions, 1,197 with a full session and a valid
`sigma30`, 1,113 after the roll filter; the commensurability drop of P-6 applies on top). At
`sd(PIN12)` of order 0.3, `se(c) ≈ 3.3` bp per sigma, so the **MDE at `|t| = 2` is about 6.6 bp per
sigma, near 8.6 bp once D581's 1.28× week-block clustering inflation is applied**. At the mean
`|PIN12|` that is an expected move of about 2 bp, roughly 0.06 of `sd(R2)`, about three ES ticks of
which one is the spread. **That is why B5 exists**: the statistical bar and the economic bar are
different numbers here, and a pass on the first without the second is not a candidate. The weekday
split is therefore **reported as counts only and not scored** — the review measured pre-2022
Tuesday at 31 sessions and Thursday at 19.

## 7. Reported beside, descriptive, with no verdict weight

**The variance block, explicitly not a test.** `RVR = log(RV(15:30→16:00)/RV(14:30→15:00))` from
one-minute log returns, with the **bipower** ratio `(π/2)·Σ|r_i||r_{i−1}|` beside; the
concentration of the noon ladder three ways — raw Herfindahl `C`, floor-normalised
`(C − 1/n)/(1 − 1/n)`, and over the nearest nine listed strikes; the two guards that **can** fire,
`|corr(C, sigma30)| ≤ 0.40` and `corr(C, 1/n) ≤ 0.60`, replacing D409's Dg1 which defect (5) shows
cannot; the terciles of each within volatility terciles (D409's T3 form); and release sessions
flagged from the sourced calendar of
[D585](D585-FIXTURE-sourced-us-economic-release-calendar-with-times.md) so the FOMC and CPI slots
sitting in the denominator are visible. **A year-block bootstrap SE, not a shift null**, because the
review measured `ac1(C) = 0.907` and a shifted copy of a variable that persistent is still nearly
the same variable. The review's in-sample reading is recorded in the result for completeness and
carries no verdict: de-floored concentration marked a **louder** close, not a quieter one, at
`t ≈ +3.0` to `+3.5`, surviving the volatility terciles — the opposite of the pinning prediction and
consistent either with concentrated 0DTE volume marking event days or with dealers short gamma.

**Also beside:** `PIN1530` in the primary specification, descriptive; the two-by-two of
`sign(PIN12)` against `sign(F5)`; the ten largest `|R2|` sessions named with their `PIN12`; the
sawtooth amplitude `2.5/(sigma30·P1530/1e4)` and the strike count per session, by era; the 0DTE
volume-to-open-interest ratio; and `R2` split into its 15:30 → 15:45 and 15:45 → 16:00 halves.

**Component line, mandatory whatever the verdict** (CLAUDE.md): the pull trade at **one MES**, in
at 15:30 in the primary cell's direction, flat at 16:00, cost in **dollars computed by the runner**
($3 a round trip plus one crossed tick at the MES tick value, D469's line). Net **and** gross,
**Sharpe and Sortino together** (R17), exposure, hit rate, payoff, skew, kurtosis, maxDD, the trade
count with mean, **median** and the **symmetric 1 % trim reported three ways**, the breakeven cost
in bp a side, and **ρ of its daily dollars with the admitted MACD arm**, computed in this runner by
chaining `scripts/d504_arm_full_history.py` over the same sessions rather than quoted from another
record's window or cost line — the error D466 caught.

## 8. The audits, each with a break that hits the scalar the assertion reads

1. **Harness.** D581's regression on D581's own gamma sign reproduces its artifact's `b =
   0.10279094253358505` and `c = −0.022772686672947903` to 1e-9 **before any new statistic is
   scored**. This doubles as the standing proof of defect (1): the reproduced `c` is the
   interaction.
2. **Column order.** On a level-only synthetic panel the named level coefficient reads ≈ +5 and the
   interaction ≈ 0; **the design matrix with its two columns swapped must raise.**
3. **Centroid, second path.** `K12` by the algebraic reroute `P1530 + Σ((K−P1530)·v)/Σv` against
   `ΣKv/Σv` at rtol 1e-12; the break is `/n` in place of `/Σv`. A row permutation is **not** used as
   a break: a groupby sum is order-invariant and that break could never fire (D584's lesson).
4. **The AM-quarterly filter**, evaluated **only on the quarterly expiry sessions**, because
   dropping the filter is silent on ~97 % of sessions and a pooled assertion would pass.
5. **Volume weights bite.** The median `|K12 − PING-centroid|` must exceed 0.5 points; if it does
   not, `PIN12` is `PING` and the study stops there.
6. **Commensurability** (defect 4). The volume-dominant 0DTE `underlying` equals the minute bars'
   `contract` on every kept session; the break is the front map shifted one session.
7. **Look-ahead, the general form.** The whole construction is re-run on `sessions ≤ t` and
   `sigma30[t]`, `PIN12[t]` and `C[t]` must be **bit-identical** to the full-panel values. Two
   breaks: dropping the `.shift(1)` on `sigma30`, and replacing the trailing tercile with a
   whole-sample `qcut`.
8. **Sign in money.** A synthetic panel `R2 = +5·PIN12 + noise` with **no** interaction must give a
   level coefficient above +2.5; the break is `PIN12 → −PIN12`, which must flip it. D581's own
   sign audit is **not** reused: its panel is a pure interaction and would pass on a sign-inverted
   level.
9. **Right quantity.** `corr(PIN12, the later-expiry control) < 0.50`, every control row's
   `expiry_date > session`, and the control row count above zero; the break points the control's
   filter at `== session`, which sends the correlation to ≈ 1 and fails the `.all()`.
10. **The shift null's zero offset** reproduces the observed `c`; `REQUIRED_OUTPUTS` before the
    write, proven to raise on a missing key; and **no session or option row at or after
    2024-01-01** in either fixture.

**Trial accounting.** One confirmatory test: `c` on `PIN12`, two-sided, under the specification
fixed in §2 and the bars of §3. The two tail ranks are readings of that one fit; the two other band
members are carried by N2; the placebo, the two open-interest controls and every item in §7 are
diagnostics or descriptions. Declared beside the fact that this `R2` series has been conditioned
before — eight cells by D581, none above its null, and the 15:30 version of this conditioner by the
review that preceded this record.

## 9. What this record does not do

It declares no closure rule: the ruling on the line is the principal's (R15). It does not read the
reserved slice and does not pre-register the forward test, which is a separate record on the
principal's word and only if both bars pass. It does not sign the 0DTE flow, which needs the
aggressor-flagged year that is itself reserved. It does not test NQ, the weekly families
separately, or any gamma weighting — the gamma-weighted version of this question is D581's and is
answered. It re-uses the in-sample readings of the 15:30 conditioner and of the variance block as
**descriptions only**, and it does not treat their having been measured as licence to select among
them.
