# D584 STAGE 0 RESULT — **M1 NOT SUPPORTED, M2 NOT SUPPORTED, the negative control UNRESOLVED on its letter.** The 8 least liquid roots earn **+5.46 bp per root-day more than the 9 most liquid, rank 0.85 in the 24,310 splits** (p95 +7.40), a Spearman of +0.02 where the mechanism predicts a negative one, 5 of 12 years — and the whole difference sits on the two roots the book holds least (PL, 107 days; GC, 61 days). The 21 sessions after a volatility spike earn **−0.57 bp/day less than the rest (SE 2.26), rank 0.44 in the 3,224 enumerated shifts**, 5 of 10 years, profile peak at lag 31–35. The BM signal's correlation with commercial positioning is inside the bar (−0.15 and −0.11, SE 0.05 and 0.04), the prior week's commercial flow predicts nothing (−0.03), but the same-week signed flow is **−0.35** — above the declared 0.3 — with the sign opposite to "riding the flow" and equal to what commercials-against-price (−0.47, negative on 16 of 16 roots) hands any book. Nothing follows.

*2026-09-21. Design committed in `958bf07` before the runner (R8), on the principal's word
reopening this item of the D582-closed list. **Runner** `scripts/stage0_d584_bm_m1_m2_nc.py`,
artifact `data/stage0_d584_bm_m1_m2_nc.json`, 27 s. **Harness first:** the rebuilt book's
PRIMARY-window gross Sharpe equals D564's artifact, +0.692157 to 1e-9; every audit passed its
clean case and raised on its break inside the run (the harness on the series rolled one session;
the per-root leg return by a pandas groupby second path, raising on `held` shifted one session;
the spike state by a pandas rolling quantile, raising on the state shifted one session, 88
sessions apart; the observed split and the zero shift each reproducing the observed statistic;
sign in money +9.9 bp on both synthetic constructions and −10.0 at rank 0.00 negated; the COT
read by D573's own second path on 50 seeded cells, raising on HP shifted one month-end; the
correlation known answer, raising on the copy not permuted; the root sets disjoint and covering
the 17; treated and untreated sessions disjoint and covering the span; the declared-outputs
guard). **Read:** the breadth fixture's closes and hourly volumes and the settlement strip for
the 17 roots to 2023-12-29; the COT legacy commercial rows released before 2024-01-01 for the 16
roots it carries (BZ has none); D564's artifact. **Not read:** any session, volume or COT release
from 2024-01-01 on. No cost, no book beyond D564's, nothing admitted (R15).*

**One flaw caught by the self-test before the run:** the first draft's break for the leg-return
audit rolled the grid along time, which leaves every per-root mean unchanged, so the audit could
never have fired on it; the break was changed to the roots rotated one place, which hits what
the assertion reads ([[break-what-the-assertion-reads]]).

---

## 1. M1 — the less liquid roots

**The ranking, read before the statistic** (median front-contract dollar volume per session over
the positioned span; `μ` the root's leg return in bp per positioned root-day, its SE, its days):

| set | root | median $/session | μ bp | SE | days |
|---|---|---|---|---|---|
| low | PA | 0.30 bn | −2.9 | 6.2 | 1,285 |
| low | HE | 0.43 bn | +0.2 | 3.4 | 2,691 |
| low | **PL** | 0.67 bn | **+34.5** | 27.0 | **107** |
| low | BZ | 0.75 bn | +5.3 | 5.6 | 2,044 |
| low | LE | 0.87 bn | +0.5 | 2.3 | 1,978 |
| low | ZL | 0.98 bn | +13.1 | 5.6 | 985 |
| low | ZM | 1.19 bn | +2.1 | 3.4 | 2,155 |
| low | ZW | 1.33 bn | +3.2 | 3.7 | 2,602 |
| high | RB | 2.35 bn | −3.3 | 5.0 | 2,016 |
| high | HO | 2.53 bn | +3.7 | 5.7 | 1,460 |
| high | ZC | 2.53 bn | +1.2 | 3.8 | 1,765 |
| high | NG | 2.91 bn | +6.1 | 5.4 | 2,776 |
| high | HG | 4.25 bn | +3.5 | 5.0 | 647 |
| high | ZS | 4.55 bn | +2.6 | 3.6 | 1,228 |
| high | SI | 4.99 bn | +8.9 | 10.4 | 328 |
| high | CL | 21.1 bn | +3.2 | 7.7 | 1,672 |
| high | **GC** | 25.4 bn | **−12.2** | 9.0 | **61** |

| | predicted | observed |
|---|---|---|
| Δ_LIQ, low 8 − high 9 | > 0, rank ≥ 0.95 of 24,310 | **+5.46 bp/root-day, rank 0.853** (p05 −7.18, p50 −0.16, p95 +7.40) |
| Spearman of μ on liquidity rank | negative | **+0.020** |
| years with Δ_LIQ > 0 | — | **5 of 12** (2020 +19.5, 2022 −12.1, 2021 +9.3, 2016 +7.8, 2017 −5.8) |
| eras | post-2016 not weaker | 2011–2015 +12.09 (rank 0.80); 2016–2023 +4.80 (rank 0.91) |
| terciles, 6 least − 6 most | — | +6.41 |
| M1b, the root's own low-liquidity months | > 0, rank ≥ 0.95 | **−4.83 bp/root-day** on 125 of 1,200 root-months, rank 0.17 of 139 shifts |

**Verdict: NOT SUPPORTED.** Inside its null, the rank ordering flat, the year count at chance,
and the within-root time version negative. **Look at the object:** the +5.46 is two numbers.
Platinum sits in the low set at +34.5 on 107 positioned days (SE 27), gold in the high set at
−12.2 on 61 days (SE 9) — the two roots the High4/Low4 book holds least, each a handful of
months. Without them the low set's mean is +3.1 and the high set's +3.2, from the table above:
**Δ_LIQ ≈ −0.2.** A 17-number statistic whose sign is set by its two thinnest cells is not
evidence of a loop gain that scales with depth, and the split null said as much at 0.85.

## 2. M2 — after volatility spikes

The cross-root 21-session realised vol has median 25 % annualised over the span, its 80th
percentile 30 %, its maximum 80 % on 2020-04-06. Against its own trailing-756-session 80th
percentile the state is ON for **759 of 3,225 positioned sessions (19 entries)** and the 21
sessions after any spike session cover **1,260 sessions, 39 % of the span** — not a rare event
at this threshold. Spike sessions by year: 2012 21 · 2013 0 · 2014 43 · 2015 154 · 2016 98 ·
2017 0 · 2018 24 · 2019 74 · 2020 165 · 2021 40 · 2022 104 · 2023 1.

| | predicted | observed |
|---|---|---|
| coverage | ≥ 6 of 12 years with ≥ 21 treated sessions | **10** (the bar is met; the test resolves) |
| Δ_VOL, treated − untreated | > 0, rank ≥ 0.95 of 3,224 shifts | **−0.57 bp/day**, SE 2.26, t −0.25; **rank 0.440** (p05 −4.96, p50 −0.07, p95 +4.75); non-overlapping rank 0.441 of 3,140 (84 named) |
| lag profile peak | inside 1–21 | **31–35** (+22.5); 1–5 +7.4, 6–10 +12.4, 11–15 −9.1, 16–20 +10.2, 21–25 +5.7 |
| years with Δ_VOL > 0 | ≥ 2/3 of 10 | **5 of 10** (2015 −39.8 on 210 treated; 2023 +27.2 on 21; 2014 +15.1; 2018 −13.1; 2021 +10.3) |
| eras | post-2016 not weaker | 2011–2015 −1.86 (rank 0.35); 2016–2023 −0.20 (rank 0.53) — holds because both are zero |
| the "risk-limit lag", 6–26 | reported | −1.71, rank 0.33 |
| as pre-registered (`ffill = 1`) · terciles | reported | −3.20 (rank 0.14) · +0.25 (rank 0.56) |
| treated mean · median · trimmed vs untreated | — | +2.31 · +0.41 · +2.75 vs +2.89 |
| contemporaneous Spearman of r with VOL (§2.8's level) | reported, no prediction | +0.017 |
| monthly Spearman of the book with the prior month's VOL | — | +0.099, year-block SE 0.104 |

**Verdict: NOT SUPPORTED.** The book after a spike is the book: +2.3 against +2.9 bp/day, the
difference a quarter of its SE, the rank at the null's centre in both eras, both windows and
all three cells, and the one year that carried a large treated count (2015, 210 sessions)
carried the largest loss. There is no lag at which the profile is more than one bin of noise,
and the peak bin sits outside any window the mechanism would name. §2.8's "increasing in
volatility" is +0.017 as a level.

## 3. The negative control — commercial positioning

Sixteen roots (BZ excluded, no COT series). HP = commercials' long / (long + short), mean of the
last 4 reports released on or before each month-end; 151 month-ends.

| statistic | bar | observed | SE (year-block) |
|---|---|---|---|
| NC1: cross-sectional Spearman of BM with HP, mean over month-ends | \|ρ\| < 0.3 | **−0.147** (2011–2015 −0.002; 2016–2023 −0.231); per-root time-series mean −0.173 | 0.054 |
| NC1: with ΔHP over 12 month-ends | \|ρ\| < 0.3 | **−0.108** (−0.029; −0.154); time-series mean −0.067 | 0.040 |
| NC2: weekly book return vs same-week signed commercial flow, 652 weeks | \|ρ\| < 0.3 | Pearson **−0.354**, Spearman **−0.370** (2011–2015 −0.41; 2016–2023 −0.32) | 0.038 |
| NC2: vs the prior week's flow, 651 weeks | \|ρ\| < 0.3 | −0.028 / +0.011 | 0.025 |

**Verdict on the letter: UNRESOLVED** — the largest |ρ| is 0.370, between the 0.3 bar and the
0.5 kill.

**What the out-of-bar number is.** The design wrote the falsifier as "the book's P&L rides the
commercials' flow", which is a *positive* correlation of the signed flow with the return, and
then declared the bar on |ρ| without the sign. The observed number is negative. The diagnostic
computed beside it, unsigned by the book, is the weekly correlation of each root's own front
return with the commercials' change in net/OI over the same week: **−0.47 on average, negative
on 16 of 16 roots** (CL −0.03, NG −0.17, the grains −0.57 to −0.64, PL −0.64, GC −0.55). That is
the known relation — commercials sell into rallies and buy into declines, in every market — and
a book long any root inherits it as a negative signed-flow correlation whether or not the book
has anything to do with hedging. The −0.35 is that relation attenuated by the book's mixed legs;
it says the commercials trade against the book's winners in the same week, which is the opposite
of the book being carried by their flow, and the lead (−0.03) says their prior-week flow carries
no information about the book. On the signal itself the control is inside the bar with room to
spare (−0.15 and −0.11, five and three SE inside), the post-2016 value (−0.23) the larger. The
verdict stays UNRESOLVED because that is what the declared rule returns; the record's reading is
that the control holds on the mechanism's meaning, and that the design should have declared the
sign ([[predictions-must-be-checkable]]: a falsifier with a direction needs a bar with one).

## 4. What this says about the mechanism

Three more of `BASIS_MOMENTUM.md` §3's implications are now read on the seen book, and with M7
(D583) four of the four that need no fetch have failed: the loop gain does not show in market
depth (M1), in the sessions after volatility rises (M2), or around the reporting calendar (M7);
the one that held is M6, the post-2010 non-decay (D564 P-4), which is consistent with the
mechanism but also with a signal that simply did not decay. The negative control, on its
meaning, holds: the BM sort is not a hedging-pressure sort (−0.15 at the signal), and the
commercials' flow does not lead the book.

The two readings D583 left open stand: either the intermediary-capacity story is wrong for
these 17 roots, or its instruments here are wrong. What is now added is that the instruments the
deposit itself named as free — depth, volatility, the calendar — all fail together, on a book
whose in-sample Sharpe is +0.69 gross and which sits inside its own rotation null once purged
(D564). M4, the He–Kelly–Manela capital ratio, remains the only test that could separate the
readings; it is a fetch and a separate design; with the line's forward slice spent (D574)
nothing could act on it, and this record does not recommend it.

## 5. What this record did not do

It did not run M3, M4 or M5; did not vary the spike threshold, the window or the split beyond
the profile and the terciles read declared in §3 of the design; did not build any conditioned
construction; did not read the funding or option fixtures; did not read any session from
2024-01-01 on. No cost was applied and no component line is due: the book scored is D564's.

**Design amendments, recorded:** (i) M1's per-year count treats a root not held in a year as
absent from that year's set (the first run voided every year on it); (ii) the commercials-
against-price diagnostic in §3 was added after the NC2 number was seen, is labelled as such, and
changes no verdict.

**Memory:** the sign lesson is [[predictions-must-be-checkable]] applied to a control's bar,
and the two-thinnest-cells lesson is [[look-at-the-object-before-reporting-it]]; both exist and
neither needs a new file. The suite at commit: the two remaining failures are a concurrent
agent's uncommitted work (a D587 citation without a record; an untracked script tripping the
index-count gate), not this record's.
