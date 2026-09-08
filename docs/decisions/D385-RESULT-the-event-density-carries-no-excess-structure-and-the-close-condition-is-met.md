# D385 RESULT — no excess structure at any power, half-life or event type, and this time `n_eff` was adequate

**P1 fails everywhere. §10's close condition is MET — on the declared statistic, unlike D384.**
**Under R15 the family's status is the principal's; this record does not close it.**

Pre-registration `63bf19a`, amendment `1fdd865`, runner `787fb24` — all predate this file (R8).
Stage 0: scores no cell, admits nothing, touches no multiplicity ledger (R13), reads no holdout.

60 names, 25 draws, 4 event types × 4 powers × 3 event half-lives, mining to 2019-12-31.
2,596 cells in 5,446 s.

---

## 1. The verdict

| criterion | cells clearing |
|---|---|
| **P1 as pre-registered** — observed TV > N2 p95 **by more than 2 SE** | **1 / 2,592** |
| p95 alone, margin dropped | 188 / 2,592 = **7.3%** (chance 5.0%) |
| against the loose null N1 | 118 / 2,592 = **4.6%** |

**And `n_eff` was adequate this time, which is what makes the failure readable.** 57.7 / 115.4 / 227.6
across the three event half-lives, maximum relative spread **0.1188** — inside the **0.12** bound the
`n ≥ 4·hl_ev` filter entails. D384 failed at `n_eff` 14.5 and could not distinguish "no shape" from
"no data". **This one can.**

§10: *"P1 fails at every `p`, every half-life and every type, with `n_eff` reported adequate → the
family carries no excess structure a volatility-matched shuffle cannot produce. Close it, and this
time the close is on the declared statistic."* **That condition is met.**

---

## 2. The grid

```
           type  hl_ev   p    n   n_eff   obs TV  null p95   CLEARS  support  offgrid   peak u
      swing low     20   1   60    57.7   0.3082    0.3794     0/60    0.164   0.0000   -1.00%
      swing low     20   8   60    57.7   0.4371    0.5863     0/60    0.249   0.0000  -11.38%
      swing low     80   1   58   227.6   0.3598    0.4854     0/58    0.252   0.0043   -4.56%
     swing high     20   1   60    57.7   0.3221    0.3830     0/60    0.164   0.0000    7.00%
     swing high     80   8   58   227.6   0.4502    0.6000     0/58    0.338   0.0044   22.69%
   lowest in 20     20   1   59    57.6   0.4305    0.6075     0/59    0.252   0.0008   -7.13%
   lowest in 20     80   1    7   210.9   0.4739    0.7330      0/7    0.360   0.1213  -15.00%
  highest in 20     20   1   60    57.7   0.4908    0.5651     0/60    0.184   0.0010   10.31%
  highest in 20     80   1   51   217.4   0.5060    0.6148     0/51    0.252   0.0043   18.00%
```
*(abridged; all 48 cells in `data/d385_event_density.json`)*

**`lowest in 20` at half-life 80 kept only 7 of 60 names** and carries 12.1% off-grid mass. **That
cell is not evidence and nothing in this record rests on it.**

---

## 3. The power sweep did something it was not supposed to

Observed TV rises with `p` — but the null's p95 rises faster, so the gap widens *against* the
hypothesis at every step. That much is the variance cost §2 predicted and priced.

**What was not predicted is that `p` walks the peak into the tail:**

```
  swing low, hl_ev 20:   p=1  peak -1.00%   |peak| 2.19%   support 0.164
                         p=2  peak -2.50%   |peak| 2.81%   support 0.181
                         p=4  peak -6.56%   |peak| 6.75%   support 0.208
                         p=8  peak -11.38%  |peak| 11.38%  support 0.249
```

The ratio `f/g` is largest where `g` is *smallest*, so raising it to a power preferentially amplifies
the thin-denominator tail rather than the overlaps it was designed for. **The `g > 0.05·max g`
support floor is not strong enough to contain this.** So "no clearing at any `p`" is a sound verdict
at `p = 1` and a progressively weaker one as `p` rises, because high `p` is partly measuring the
tail. **The synthetic checks in §2 of the pre-registration did not catch this** — they used a smooth
Gaussian `g` with no thin tail to amplify.

**Any successor using the read-time power needs a stronger denominator floor, declared in advance,
and should treat `p > 2` as suspect until it has one.**

---

## 4. The one strong signal in the data is an artefact, and Q4 is why it was caught

Against the null's **centre** rather than its p95, `highest in 20` looks emphatic:

```
  highest in 20  hl 40  p=1:  45/60 above centre   sign p = 6.7e-05   median z +0.73
  highest in 20  hl 80  p=1:  44/51 above centre   sign p = 6.1e-08   median z +1.01
  lowest  in 20  hl 20  p=1:  21/59 above centre   sign p = 0.99      median z -0.27
```

**Q9's prediction Q4 said: *"lows and highs behave the SAME, not oppositely. If they differ I will
suspect a sign or masking error before I believe a directional claim."* They differ. So I checked.**

**It is an event-rate artefact, created by this record's own tying rule.**

```
        swing low: rate  24.0/100  ->  centring EMA half-life  167 bars
       swing high: rate  23.3/100  ->  centring EMA half-life  171 bars
     lowest in 20: rate   6.7/100  ->  centring EMA half-life  600 bars
    highest in 20: rate  18.3/100  ->  centring EMA half-life  218 bars
```

In a decade-long bull market **20-bar highs outnumber 20-bar lows 2.60× (57 of 59 matched names)**.
Because §3 ties `hl_bars = hl_ev / rate`, that rate gap becomes a **600-bar vs 218-bar centring EMA**
— so `lowest in 20` and `highest in 20` are measured **in different coordinates** and were never the
symmetric pair the comparison assumed.

**The control is decisive.** The swing types have a matched rate ratio of **1.000×** and near-identical
tied half-lives (167 vs 171 bars) — genuinely symmetric — and they behave **identically**: both
39/58 above centre at half-life 80, `p` = 6.0e-03. **Where the two directions are actually
comparable, they agree.** The asymmetry lives entirely where the construction made them incomparable.

**No directional mechanism is filed.** The statistic does not order the outcome once the coordinate is
matched.

**This is also a construction defect worth carrying forward:** tying the centring half-life to the
event rate makes rare and common event types mutually incomparable. Anything that wants to compare
types must fix the centring span across them, and pay for it elsewhere.

---

## 5. Predictions scored

| | prediction | outcome |
|---|---|---|
| **Q1** | **P1 clears somewhere** — unlike D384 this is not testing the return distribution against a null built to preserve it | **FALSIFIED.** 1 of 2,592, and 4.6% against the loose null — below chance |
| **Q2** | the clearing is stronger for the 20-bar extremes than the 2-bar fractals | **VACUOUS on clearing** (nothing clears). On displacement the 20-bar extremes *are* stronger — but §4 shows that is the rate artefact, not the level-vs-wiggle distinction the prediction claimed |
| **Q3** | **P2 humps and does not rise monotonically** — `p`'s variance cost overtakes its benefit by `p = 8` | **FALSIFIED, and worse than predicted.** There is no hump because there is no rise: displacement **decays monotonically** in `p` (0.73 → 0.61 → 0.41 → 0.44). `p` never helps at any point |
| **Q4** | **lows and highs behave the SAME.** If they differ, suspect an error before believing a directional claim | **HELD, and it did its job.** They differed; the check found the tying rule had made them incomparable; the genuinely symmetric pair agrees exactly. **The most useful prediction in the record** |
| **Q5** | the support fraction **falls** with `p` | **FALSIFIED, in the opposite direction.** It *rises*, 0.164 → 0.249, because `h = h_eff·√p` widens `g` and more of the grid clears the floor. The reparametrisation caused it and I did not foresee it |
| **Q6** | **AGAINST myself: `n_eff` still binding at half-life 20** | **FALSIFIED as stated, right in spirit.** `n_eff` is fine (57.7, spread inside its bound). The binding constraint moved to the **event rate through the `n ≥ 4·hl_ev` filter** — `lowest in 20` at half-life 80 kept 7 of 60 names |
| **Q7** | `[FLAT]` and `[DECONF]` hold first time | **HELD** (0.0444 and 0.184 against a 1.009 control) — **but `[STAT]` and `[CAUSAL]` each fired first**, so the underlying hope that the assertions would pass on the first run was wrong for the second study running |

**Four of seven falsified.** Q4 is the one that paid for itself.

---

## 6. Assertions

| tag | value |
|---|---|
| `[REC]` lfilter vs explicit loop, tie-heavy | **0.000e+00**, bit-identical |
| `[REC]` vectorised rolling extreme vs the loop it replaced | equal on an all-ties input |
| `[STAT]` pooled statistic vs independent per-bar loop | **0.000e+00** |
| `[CAUSAL]` `s_t` under a future shock | **0.000e+00** |
| `[NEFF]` max relative spread | **0.1188**, inside the derived 0.12 bound |
| `[FLAT]` max manufactured tilt across `p` | 0.0444 |
| `[DECONF]` reparametrised / fixed-`h` control | 0.184 / **1.009** |
| `[NULL]` \|r\| autocorr: observed 0.188, **N2 keeps 0.152**, N1 destroys −0.025; same event function | as specified |
| `[X]` REC, NEFF spread, NEFF floor, DECONF, CAUSAL, NULL | all raise |

**`[STAT]` and `[CAUSAL]` each caught a real bug before any number was read** — the EMA's zero-state
initialisation putting 14.3% of bars off-grid, and full-sample estimation of `rate`/`hl_bars`/`h_eff`
leaking the future into every bar. Both are in the runner commit `787fb24`.

---

## 7. The runtime is a fact about the runner, not about the problem

**5,446 s at 3.28× on 6 workers — 55% efficiency.** Half the machine was idle for 90 minutes because
I profiled two call timings, called the cost inherent, and launched. The principal had to ask.
`parallel_map` now always reports achieved efficiency and shouts below 70% (`dc30d00`); this run
predates the change, so its own log carries no `[SPEED]` line.

---

## 8. What this establishes, and what it does not

**Establishes**, on the declared statistic with adequate `n_eff`:

- **Event mass relative to time spent carries no excess structure a volatility-matched shuffle cannot
  produce** — on 60 ETFs, 4 event types, 3 half-lives, 4 powers, 2,516 daily bars.
- **The sharpening power never helps.** Displacement decays monotonically in `p`, and beyond `p=2` the
  power is partly measuring the thin-denominator tail rather than overlaps.
- **Tying the centring half-life to the event rate makes event types mutually incomparable** (600 vs
  218 bars), which is a construction defect independent of the verdict.

**Does not establish:**

- Anything about **rare event types** — reversals (2.4/100) and moves >2% (4.0/100) were excluded by
  my narrowing in §3, which was flagged for objection and never tested.
- Anything about **`lowest in 20` at long half-lives** — 7 of 60 names.
- Anything about the **principal's decay-coherence fork**, which §3 parked with a scaffold and which
  remains open.

**Nothing admitted to either book. No hurdle cleared. No holdout read.**

---

*Result committed 2026-09-08, separately from the pre-registration, per R8. §10's close condition is
met; under R15 the decision to close the family is the principal's.*

---

## AMENDMENT, 2026-09-08 — THE CLOSE CONDITION SHOULD NOT BE ACTED ON. THE STAGE-0 STATISTIC CANNOT ANSWER THE FAMILY'S QUESTION.

**Raised by the principal: "It seems our idea didn't work as intended, I would take that to mean bad
design not doesn't work?" He is right, and more strongly than §1 and §8 of this record admit.**

**Two different questions were conflated across D384 and D385, both by me:**

| | |
|---|---|
| what the premise check **asks** | is the density's **SHAPE** distinguishable from a volatility-matched shuffle's? |
| what the family is **for** | does price **BEHAVE DIFFERENTLY** near high-density regions? |

**TV(density, shuffle density) is a functional of the DENSITY ALONE. The signal is a functional of
(DENSITY, FORWARD RETURNS). The statistic never looks at a return.**

Demonstrated in `temp/d385_statistic_blindness.py`, holding the real RZV path — and therefore the
density, and therefore the statistic — **exactly fixed**, and attaching two different forward-return
processes:

```
  D385 statistic on the real path:  observed TV 0.3288   null p95 0.4390   -> does NOT clear

  returns blind to the density      corr +0.095   top-vs-bottom quintile   +14.4 bp   t = +0.25
  returns DEPEND on the density     corr +0.551   top-vs-bottom quintile  +289.6 bp   t = +4.62
```

**TV is 0.3288 in both worlds and clears in neither.** One of them has a density that predicts
forward returns at t = +4.6. **The statistic cannot tell them apart.**

**Caveat, stated so this is not overclaimed:** the demonstration attaches returns exogenously to a
fixed path, whereas in reality path and returns are the same object, so a genuine predictive
relationship would leave *some* trace in the density. The claim is **not** that TV is provably blind.
The claim is that the mapping from (density, returns) to TV is **many-to-one**, TV was never designed
to detect the second argument, and therefore **a null TV licenses no conclusion about the signal.**

### What this changes

**WITHDRAWN: the framing of §1 and §8 that §10's close condition being met is a verdict on the
family.** It is a verdict on the *declared statistic*, and the declared statistic is the wrong
instrument for the question. **The close condition should NOT be acted on.** Under R15 the decision
was always the principal's; this amendment removes my implicit recommendation to take it.

**STANDS, and is not affected:**
- Every measured defect in §3 and §4 — the tying rule making event types incomparable (600 vs 218
  bar coordinates), the read-time power amplifying the thin denominator, the 2.60× rate asymmetry
  and the artefact it generated. **These are design faults, and they are mine.**
- Every assertion in §6, and the two real bugs `[STAT]` and `[CAUSAL]` caught.
- The **construction itself is proved and fast**: `[REC]` bit-identical, `[STAT]` and `[CAUSAL]` at
  0.000e+00. The apparatus works; it was pointed at the wrong question.
- The narrow negative that survives: **at `p=1`, on the properly-matched swing types, with adequate
  `n_eff`, the density's SHAPE is not unusual.** That is true and it is a small claim.

### What the family actually needs

**A direct signal test, not a premise check**: condition on the density — is price near a
high-density region of its own event distribution — and measure **forward returns**, against a null
that shuffles, scored as R15 requires (positive gross mean per trade above the nulls). That needs its
own pre-registration under R8, and it is the principal's call whether to spend one.

**And the stage-0 instinct that produced D384 and D385 was a misapplication of my own rule.** The
memory says *measure the conditioner's own persistence before designing a study that conditions on
it.* **Persistence is not the same as distinguishability-from-a-shuffle**, and I substituted the
second for the first across two studies and roughly 110 minutes of compute.
