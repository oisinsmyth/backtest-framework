# D535 RESULT — **DOES NOT PASS**, and the guards earned their keep: the contrast **inverted in 2021**, and the declared statistic is nearly orthogonal to the structure that is actually there

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D535-RESULT-does-not-pass-and-the-guards-earned-their-keep-the-contrast-inverted-in-2021-and-is-orthogonal-to-the-real-structure.md`. The H1 above is the full title.*

*2026-09-15. Spec committed in `bbaa99f` BEFORE the runner (R8). In sample 2016-01-04 → 2023-12-29;
the 2024+ slice was **not read**. Nothing admitted (R15). Nothing closed.*

**The principal asked for the ranking and warned that something might be averaged away. Something
was — three things — and all three are declared diagnostics, so none of them is promotable and none
rescues the verdict.**

---

## 1. The declared verdict

| | | |
|---|---|---|
| **PRIMARY** — top decile, 60 min, contrast | **+0.0287 σ** (WITH +0.1771, AGAINST +0.1484), n 343/344 | null p50 +0.0023, **p95 +0.1348** → **INSIDE** |
| **N2 family**, 6 declared cells | best **+0.0618** (tercile-60) | p95 **+0.1662** → **INSIDE** |

| prediction | | |
|---|---|---|
| **P-1** primary > 0 and clears | +0.0287 | **fails** |
| **P-2** monotone across deciles | Spearman **+0.139** vs N3 p95 +0.915 | **fails** |
| **P-3** ≥ 8 of 10 roots positive | **5 of 10** | **fails** |
| **P-4** falsifier (contrast ≤ 0) | +0.0287 | not inverted |
| **P-5** G1 sub-cells agree in sign | WITH agree, AGAINST agree | **interpretable** |

## 2. G5 — the one the principal's intuition was pointing at

| | n | contrast |
|---|---:|---:|
| **2016–2019** | 160/161 | **+0.2464** |
| **2020–2023** | 183/183 | **−0.1686** |

**The pooled +0.0287 is the average of two eras of opposite sign.** Year by year (a descriptive
refinement of the same declared diagnostic, not a new test):

| 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| +0.257 | +0.084 | +0.415 | +0.226 | +0.419 | **−0.405** | **−0.437** | **−0.232** |

**Five consecutive positive years, then three consecutive negative ones.** Dropping 2020 entirely —
in case the volatility shock and a lagging trailing σ manufactured it — makes the second era **more**
negative, **−0.4337**, so the flip is not a 2020 artefact. It dates to 2021.

**And it is the AGAINST arm that moved, not the WITH arm.** AGAINST reads +0.093, +0.075, −0.160,
+0.076, −0.190 through 2020 and then **+0.416, +0.684, +0.378**. From 2021 the trade that *fades* the
overnight move became the profitable one. The mechanism did not decay — **it inverted**.

**This is not promotable and I am not promoting it.** The pre-registration declared the era split a
diagnostic precisely so that a favourable half could not be lifted out afterwards; the per-year cells
hold 49–107 trades with a |gn| 99th percentile of 2.1–6.7, so each year is noisy. What it establishes
is why the average is near zero — not that an edge exists in either half.

## 3. G3 — the profile is not monotone, and the top decile is the WORST of the upper range

| `pct ≥` | 0.0 | 0.2 | 0.4 | 0.6 | 0.7 | **0.8** | **0.9** |
|---|---:|---:|---:|---:|---:|---:|---:|
| contrast | +0.0358 | +0.0336 | +0.0252 | +0.0521 | +0.0955 | **+0.1042** | **+0.0287** |

The contrast builds steadily to the 8th decile and then **collapses in the extreme tail** — which is
where the illiquidity story says it should be strongest. **The bucket I declared primary is the
weakest part of the range above the median**, and the tercile cell (+0.0618) beats the decile cell.

Had this record run only its primary bucket — which is effectively what D534 did — it would have
reported a small number and learned nothing about the shape. **Neither 0.7 nor 0.8 is promotable
either**: both are diagnostic under the declared family, and both sit under the family p95 of +0.1662
in any case, so there is no cherry to pick.

## 4. G1 and G2 — the declared statistic is close to orthogonal to the structure in the data

**G2, ten markets:** CL +0.044, GC +0.118, SI +0.132, NG **−0.179**, HG +0.051, HO −0.006, RB −0.062,
ZN **−0.142**, 6E +0.103, ZC **−0.128**. **5 of 10 positive** — a coin flip. Whatever the equal-weighted
four-root number says, the WITH/AGAINST effect is not a property of futures markets generally.

**G1, the four-way decomposition**, is where the useful observation is:

| night | break | n | mean | median | trim |
|---|---|---:|---:|---:|---:|
| **up** | up | 182 | +0.219 | **+0.238** | +0.238 |
| **up** | dn | 164 | +0.278 | +0.053 | +0.260 |
| dn | dn | 161 | +0.130 | +0.093 | +0.129 |
| dn | up | 180 | +0.032 | −0.058 | +0.034 |

Pooled by night direction alone: **after an UP night the break pays +0.247 (median +0.168); after a
DOWN night it pays +0.078 (median +0.000).**

**Both breaks after an up night pay — including the short.** So this is not direction: it is
**break-quality keyed to the night's sign**. The declared contrast measures WITH minus AGAINST, which
cuts across that structure rather than along it, and averages most of it away. The difference is
roughly 2.2 SE and entirely post-hoc, so it is a hypothesis for a separate record, not a finding.

## 5. The bug the coverage guard caught

**ZC returned `pct finite 0` — the whole root empty.** Cause: `night_state` hard-coded the night's open
as **h18**, and **corn reopens at 19:00 CT**, so `h18_o` is populated on **6 %** of ZC sessions. Every
corn row went NaN through `log|lr|`.

The assert I added after D533's silent-NaN bug stopped the run *at the root*, not four screens later.
The fix is the invariant rather than the symptom: **the night's open is the root's own first populated
night hour**, and the close its last — no hour is hard-coded, which is how `session_span` already
treats the day. A `[EDGE]` selftest now covers a grain-shaped night, a session missing its last hour,
and an `[X]` case where h18 *is* present and must win.

## 6. Component line

| root | trades | **per year** | gross $ | net $ | hit | net SR (SE 0.36) | skew |
|---|---:|---:|---:|---:|---:|---:|---:|
| CL | 89 | 11 | +12.09 | +8.09 | 55.1 % | +0.38 | +2.97 |
| GC | 93 | 12 | +4.30 | −0.70 | 51.6 % | −0.03 | −3.55 |
| SI | 90 | 11 | +29.44 | **+21.44** | 52.2 % | **+0.59** | +5.77 |
| NG | 83 | 10 | −0.45 | −5.45 | 45.8 % | −0.39 | −4.09 |
| **BOOK** | | | | | | **+0.45** | |

**SI clears C-a at +0.59 and it means nothing.** Eleven trades a year, skew +5.77, an SE of 0.36 on
the point estimate, and the era table above says the whole construction changed sign in 2021.
**The duty cycle is read before the Sharpe, as pre-registered** — a construction trading eleven times
a year cannot carry a book line, and a degenerate cell has beaten a rotation null in this programme
before.

## 7. What this leaves

**Nothing closed, nothing admitted.** The continuous ranking answers D534's power problem — 687
top-decile trades instead of 505 gated ones, across ten markets instead of four — and the answer is
that **the WITH/AGAINST contrast is not there**: inside its null, non-monotone, a coin flip across
markets, and sign-flipped between halves of the sample.

**Three things came out of the guards, all unpromotable, all worth a separate record if the principal
wants one:**

1. **The 2021 inversion**, carried by the AGAINST arm, on five-then-three consecutive years.
2. **The shape** — the effect peaks in the 8th decile, not the extreme tail, which contradicts the
   monotone reading the illiquidity story implies.
3. **Night direction, not night/break agreement** — after an up night, breaks follow through in
   *either* direction; after a down night, they do not.

**The third is the only one that is a new hypothesis rather than a caveat**, and it is the same shape
D534 reached from the other side: *these night states predict how well a break works, not which way it
goes.* Two records have now said that, from different constructions.

---

Runner: [`scripts/run_d535_illiq_ranked.py`](../../scripts/run_d535_illiq_ranked.py) — `--selftest`
carries **[X]** on the trailing rank's causality, **[LAG]** that a whole-sample quantile would leak
and the trailing one does not, **[SIGN]** with an inverted-night break, **[G1]** that the four-way
split partitions WITH/AGAINST exactly, **[G4]** that a planted tail moves the mean and not the trim,
**[G3]** that a planted ramp reads Spearman +1, **[EDGE]** on the per-root night open, and **[QTY]**
that each bucket threshold binds.
Artefact: [`data/d535_illiq_ranked.json`](../../data/d535_illiq_ranked.json).
