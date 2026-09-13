# D525 — is intraday path persistence an **index-root property** or a **tick-coarseness artefact**? **NKD decides**

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file.
**Tested on the 25 roots this statistic has NEVER been computed on. The 2024+ slice is
DELIBERATELY NOT SPENT — §6 gives the power calculation that is the reason.**

**No return is read as P&L, no cost, no position (R15).**

---

## 0. Where this comes from, and what is already spent

D523's efficiency-LEVEL label was **voided** because it demanded near-monotonicity and was biased
down by bid-ask bounce. The principal then set three constraints: keep a **volatility-invariant
path-efficacy** statistic, keep the horizon **intraday** because the market is fractal in
timeframe, and **stop pooling** a time series into a mean.

Design check `7ad8551` (`working/d525_scaling_design_check.py`) built the statistic those
constraints force and validated it. **It also looked at ten roots in sample, so those ten are
spent for this line:** NQ, ES, YM, RTY, CL, GC, ZN, ZT, 6E, NG. What it found, standardised:

    PERSISTENT      ES -2.1 SE · YM -2.1 · RTY -2.1 · NQ -1.8     implied Hu 0.509-0.512
    ANTI-PERSISTENT 6E +7.2 · GC +6.9 · ZN +3.9 · NG +3.2 · ZT +3.1 · CL +1.1

**Two hypotheses explain that pattern equally well, and this record separates them.**

- **H-INDEX.** Persistence is a property of **equity index futures** — the deepest books, the
  heaviest index-arbitrage and momentum flow, the products where a directional intraday move gets
  extended rather than absorbed.
- **H-TICK.** Persistence is an artefact of **tick fineness**. The design check measured that
  bid-ask bounce **steepens** the slope, i.e. manufactures false anti-persistence, and that
  dropping k = 1, 2 removes only **33%** of it. The four "persistent" roots — NQ 17, RTY 11, YM 10,
  ES 5 median ticks per five-minute move — are **the four finest-tick roots in the universe**, and
  the anti-persistent ones are coarse. **The in-sample pattern is exactly what pure bounce would
  produce.**

## 1. THE DISCRIMINATING CASE: NKD

**NKD is a Nikkei 225 index future whose median five-minute move is 2 ticks.** It is an index root
with a *coarse* tick, and it is **unspent** — this statistic has never been computed on it.

    H-INDEX  predicts NKD is PERSISTENT      deviation NEGATIVE, near the index group's -0.0097
    H-TICK   predicts NKD is ANTI-PERSISTENT deviation POSITIVE, near ZT/ZF/ZB's +0.012 .. +0.025

**The two hypotheses predict OPPOSITE SIGNS on the same root, each with |t| > 2.** That is the
whole reason this record exists, and it is why the primary is a single root rather than a pooled
average.

## 2. The statistic — FROZEN from the design check, nothing tuned

Per session, on the first **73 consecutive closes** (bars 0..72) giving **N = 72** returns:

1. `r_t` = five-minute close-to-close log returns.
2. **Vol-standardise:** divide each `r_t` by a **centred** rolling mean of `|r|`, window 13. The
   centred form is legitimate because this is a **label**, not a signal. Measured in the design
   check: it leaves a constant rescaling **exact**, cuts the U-shaped-profile bias from −0.0260 to
   **−0.0022** (12×) and a single 10× bar from −0.0589 to −0.0211, while retaining **88%** of the
   Hu = 0.55 signal.
3. Aggregate to scale `k` and form `E(k) = |net| / Σ|r_k|`. **Scales `k ∈ {3, 4, 6, 8, 9, 12, 18,
   24}`** — the divisors of 72 at `k ≥ 3`, the bounce-robust set.
4. **`slope` = OLS slope of `log E(k)` on `log k`.** For a self-similar path
   `log E(k) = (1 − Hu)·log k + const`, so **slope = 1 − Hu**.
5. `deviation = mean(slope) − benchmark`. **NEGATIVE = persistent (Hu > 0.5).**

**THE BENCHMARK IS SIMULATED, NEVER THE CLOSED FORM.** Fractional Gaussian noise at Hu = 0.50, via
Davies–Harte exact circulant embedding, N = 72, the same scale set, the same standardisation,
**8,000 paths at seed 525**. The measured value is **+0.5477**; the closed form says 0.5000, so the
finite-window bias is **+0.0477 — larger than the entire Hu 0.50→0.55 effect.** Using the closed
form would manufacture mean reversion out of arithmetic. This is D471's `C ≠ 1` lesson in a new
place, and the benchmark constants are frozen here rather than recomputed per run.

Sessions with `net == 0` or a zero path at any scale are **dropped and counted** (in sample this
was 6–283 per root, worst on ZT).

## 3. The primary statistic — ONE (R14)

**`deviation` for NKD, over NKD's full clean history (2016 → 2023-12-29), vol-standardised,
k ≥ 3.**

Reported beside it, always: the session count, the dropped-session count, the SE as
`sd(slope)/√n_sessions`, and the implied Hu.

**Expected precision:** NKD holds ~1,959 clean sessions; at the measured per-session
`sd = 0.197` that is **SE ≈ 0.0044**. H-INDEX's −0.0097 gives t ≈ −2.2; H-TICK's +0.012…+0.025
gives t ≈ +2.7…+5.7.

## 4. Stage B — transport across all 25 unspent roots

Run the same statistic on every unspent root: **SR3, NKD, TN, UB, ZB, ZC, ZF, ZW, 6B, ZS, HG, SI,
ZL, ZM, 6J, 6A, 6C, 6S, HE, LE, PL, BZ, BTC, HO, RB.**

**B1 — the tick relationship.** Spearman across the 25 roots between `deviation` and **median
five-minute move in ticks**, whose values are **already published in D523 §7.3** and are quoted
here so they cannot be re-chosen: SR3 2, NKD 2, TN 2, UB 2, ZB 2, ZC 2, ZF 2, ZW 2, 6B 3, ZS 3,
HG 3, SI 3, ZL 3, ZM 3, 6J 4, 6A 4, 6C 4, 6S 4, HE 4, LE 4, PL 6, BZ 6, BTC 6, HO 15, RB 16.

**Under H-TICK this correlation is strongly NEGATIVE** (coarser tick → more positive deviation).
Under H-INDEX it is **near zero among non-index roots**, because tick fineness would then be
incidental. At n = 25 the Spearman SE is `1/√24 = 0.204`.

**B2 — the residual index effect.** `deviation` regressed on `log(median ticks)` across all 35
roots, with the **five index roots** (ES, NQ, YM, RTY, NKD) carrying an indicator. **H-INDEX
requires the indicator to be negative and significant after the tick term absorbs the bounce.**
This is the only test that can hold both mechanisms at once, and its index rows are 4/5 spent, so
it is reported as **supporting evidence, not as a gate.**

**B3 — the regime premise, which is what "stop pooling" demands.** Per unspent root: the
**lag-1 autocorrelation** of the per-session slope series, and the **sd of its yearly means**
against the iid expectation `sd/√(sessions per year)`. In sample this exceeded the iid value on 6
of 10 roots. **This is reported per root as a time series property and never pooled into one
number.**

## 5. Decision rule, pre-registered

- **H-INDEX SUPPORTED** — NKD's deviation is **negative** with |t| > 2, and B1's tick correlation
  is weaker than −0.5. Persistence is then a property of index futures, not of the tick, and the
  next record may design a causal feature for it.
- **H-TICK SUPPORTED** — NKD's deviation is **positive** with |t| > 2, and B1's tick correlation is
  at or below −0.5. **The design check's "index roots are persistent" reading is then withdrawn as
  a bounce artefact**, and no causal work follows until the statistic is recomputed on a
  bounce-free mid price (§7).
- **UNRESOLVED** — |t| ≤ 2 on NKD, or NKD and B1 point the same way. Recorded as unresolved; no
  interpretation is offered and the 2024+ slice stays unspent.

## 6. WHY THE 2024+ HOLDOUT IS DELIBERATELY NOT SPENT

Measured before writing this record, not assumed:

    the four index roots' per-session slopes are CORRELATED:  ES-NQ 0.697  ES-YM 0.702
                                                              ES-RTY 0.494 NQ-YM 0.391
                                                              NQ-RTY 0.361 YM-RTY 0.414
                                                              mean off-diagonal rho = 0.510

    holdout 2024-01-01 .. 2026-09-09:  2,652 root-sessions over 668 distinct days
    EFFECTIVE n with rho 0.510 over 4 roots = 1,048, not 2,652
    SE = 0.197/sqrt(1,048) = 0.0061   against an effect of -0.0097  ->  expected t -1.60

    POWER, one-sided at 0.05:   effect -0.0097 -> 48%      -0.0080 -> 37%
                                effect -0.0060 -> 26%      -0.0050 -> 21%

**A 48%-powered confirmation is a coin flip, and a failure would be uninformative.** Pooling four
index roots does **not** give four times the observations — they move together, so the naive SE is
1.6× too small. **The unspent ROOTS carry ~25× more independent information than the unspent
DATES**, so the transport test above is the higher-powered use of what remains, and the 2024+ slice
is preserved for a properly powered question later.

## 7. Predictions, in the runner's own quantities

| | prediction | why |
|---|---|---|
| **P1** | **NKD's deviation is POSITIVE, +0.005 to +0.020** — i.e. **H-TICK wins** | the four "persistent" roots are precisely the four finest-tick roots, and the design check measured bounce producing exactly this gradient with only 33% removed by `k ≥ 3` |
| **P2** | **B1's tick Spearman is below −0.5** | same mechanism, now across 25 unseen roots |
| **P3** | **B2's index indicator is negative but within 2 SE** — real but small once the tick term absorbs the bounce | the standardised index effect was already only ~2 SE with 4 roots |
| **P4** | **B3: yearly-mean spread exceeds the iid expectation on more than half the unspent roots** | it did on 6 of 10 in sample, and vol regimes are the best-established fact in this repo |

**P1 predicts against the principal's reading and against my own design check.** If NKD comes in
negative, H-INDEX gains a genuine out-of-sample confirmation on the one root that could
discriminate — and it will have beaten a stated prediction to get there.

## 8. Checks the runner must carry, each able to fire

1. **The slope recovers Hu.** On Davies–Harte fGn at Hu ∈ {0.40, 0.50, 0.60}, the measured slope
   is monotone decreasing and within 0.01 of the design check's published values (0.6465, 0.5456,
   0.4432 at k ≥ 3 unstandardised). **[X]** must fail if the scale set is changed.
2. **The circulant embedding is PSD** at every Hu used, asserted rather than clipped silently.
3. **Vol-standardisation is exact under a constant rescale** — slope of `R` equals slope of `4R`
   **bit-identically** — and reduces the U-shape bias to under 0.005. **[X]** the un-standardised
   path must show the larger bias.
4. **`E(k)` is computed on non-overlapping aggregates**: the `k`-bar returns partition the window,
   `Σ` of them equals the window net exactly, and `net` is **invariant to k** to 1e-12.
5. **Sessions are whole and contiguous:** 73 consecutive bar slots from bar 0, asserted on a
   hand-punched hole, with `present` and `same_front` already applied.
6. **`net == 0` sessions are dropped, not silently NaN'd**, and the count is reported per root.
7. **The benchmark constants are the frozen ones** — the runner asserts the simulated benchmark at
   seed 525 reproduces +0.5477 (standardised) and +0.5436 (raw) to 1e-3, and **raises** otherwise,
   because a drifting benchmark would move every verdict.
8. **The tick table is the PUBLISHED one** — the runner reads the 35 values from D523's artefact or
   this record and asserts they match, never recomputing them, so B1's covariate cannot be
   re-chosen after seeing the outcome.
9. **The runner computes the pre-registered primary** — NKD's standardised `k ≥ 3` deviation — and
   asserts it, because D506 compared a different quantity than its spec declared and D523 never
   computed a secondary it had declared.
10. **Duty cycle:** every reported number carries its session count and its dropped count.
11. **The 2024+ slice is never loaded.** The loader asserts `max(day) <= 2023-12-29` and raises.

## 9. What follows either way — the bounce-free replication

**Declared now so it is not designed after the fact.** Whatever §5 returns, the statistic is
contaminated by bounce at a level that `k ≥ 3` only partly removes. The replication is the same
computation on a **bounce-free mid price** from the `bbo-1m` or `tbbo` already on disk — 12 months,
so it cannot test transport across eras, but it can test whether a root's *sign* survives losing
the bounce. **If a root's sign flips on the mid, the close-price result is void for that root.**

That replication is a separate record and is **not** run here.

## 10. What this record does not do

No P&L, no cost, no position, no hurdle P, no component line — there is no construction. Nothing
enters `FINDINGS.md`, `RULES.md`, `COMPONENTS_PROP.md` or either book on this record's authority
(R8, R15). **The ten roots spent by the design check are not re-read as evidence, and 2024-01-01
onward is not read at all.**

---

# 11. RETIRED, 2026-09-14, BEFORE THE RUNNER WAS WRITTEN — **the primary was invalid and one defect biased the test toward its own hypothesis**

**Retired on the principal's instruction after he asked whether there was any point running a
defective design. There was not.** No compute was spent on it; the runner never existed. Audit
figures below are measured, not asserted.

## 11.1 The primary was invalid — NKD is not a comparable index root

**NKD's median day-session volume is 3,301 contracts. ES's is 1,205,239** — **365× thinner** —
because the Japanese cash market is **closed** during 09:00–15:59 ET. NKD in this window is a thin
offshore proxy trading on US-hours flow.

    ES  1,205,239     NQ 292,397     RTY 129,405     YM 113,748     NKD 3,301

§1's framing — *"an index root with a coarse tick"* — was therefore **wrong**: NKD is a **thin**
root with a coarse tick, and **thinness, tick coarseness and time zone all move together on it**.
A positive result would have been consistent with H-TICK; a negative one could not have confirmed
H-INDEX, because there was no way to attribute it. **A primary of n = 1 root had no attribution.**

## 11.2 A defect that biased the test TOWARD the hypothesis

§2 dropped sessions with `net == 0`. **Those are perfect round trips — the most mean-reverting
sessions there are.** Measured on fGn rounded to a tick grid:

| grid | sessions dropped | bias in the surviving mean |
|---|---:|---:|
| 0.25σ | 1.18% | +0.0014 |
| 1.0σ | 4.57% | **+0.0047** |
| 2.0σ | 9.14% | **+0.0073** |

**The in-sample effect this record set out to confirm was −0.0098, so the bias was 48–75% of the
signal — and largest on the coarse-tick roots, which are precisely the ones §4 contrasts.** ZT
dropped 9.8% of its sessions in sample. A test cannot be run whose own missing-data rule pushes it
toward its hypothesis by half the effect size.

## 11.3 The instrument contained the artefact under test, and the fix was already on disk

The design check measured the statistic's bounce sensitivity at **+0.0996** over `ψ/σ` 0→1 with
`k ≥ 3`. This record proposed to settle *whether the signal is bounce* using a **bounce-contaminated
instrument**, and deferred the bounce-free replication to §9 — a later record. **That is the wrong
order**, and the `bbo-1m` and `tbbo` mid prices were already acquired.

## 11.4 And the deeper objection, which retires the STATISTIC and not only this spec

**The scaling exponent cannot label a session, which is the thing it was built to do.**

    per-session sd of the slope                          0.2050
    Hu = 0.55 (mild trend)   effect 0.0491   ONE-SESSION t = +0.24   sessions for t=2:  70
    Hu = 0.60 (strong)       effect 0.1025   ONE-SESSION t = +0.50   sessions for t=2:  17

A one-session `t` of **+0.24** means a single session's slope carries almost no information about
that session. Any usable read needs **~70 sessions pooled**, which is a quarterly average — **the
opposite of the intraday state the principal asked for.** The statistic therefore fights the
requirement that motivated it, independent of the bounce. Two further points stand alongside:
`ρ = 0.51` among the index roots means *"4 of 4 agree"* is ~1.6 independent observations, and an
implied `Hu` of 0.509–0.512 is economically empty against a fee that is 2.4% of the NQ day move.

## 11.5 What the audit produced that IS kept

**The path-length estimator replaces the efficiency-ratio form outright.** Regress
`log Σ|r_k|` on `log k`; since `Σ|r_k| ~ N·σ·k^(Hu−1)`, the **slope is `Hu − 1`**. It contains
**no `net`**, therefore no `log(0)`, no dropped sessions and **no selection whatsoever** — while the
per-session sd is **identical (0.2043 vs 0.2043)**. Strictly better on bias, neutral on variance.

Also kept: the simulated-benchmark discipline (the finite-window bias is +0.0477 at N = 72, larger
than the whole effect), and the measured fact that vol-standardisation buys 12× profile-invariance
for 12% of the signal.

## 11.6 What replaces it

**Measure on the bounce-free mid first** — the principal's instruction, and the right order.
A paired design on the SAME sessions with two price series (trade close vs quoted mid) measures the
bounce contribution as a **difference**, which is far more precise than any cross-period comparison
and answers the H-TICK/H-INDEX question directly.

**And it necessarily spends part of the reserved slice, which is recorded rather than hidden:**
`bbo-1m` exists only for **2025-09-11 → 2026-09-11**, inside the window §6 reserved. That is
accepted because §6 itself showed the slice was only **48% powered** for the close-price
confirmation it was being held for, because this is a **validity check on the instrument** rather
than a test of an edge, and because the quoted data exists nowhere else.

**Nothing is closed by this retirement.** The question — does intraday path persistence exist, and
is it an index property — is **untested**, not answered.
