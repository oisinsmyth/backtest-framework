# D324 — is the fragility a property of the BOOK or of the SIGNAL?

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8).
Nothing here is a result.
**Date:** 2026-09-04
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 1. Why this, and why now

[D322](D322-the-four-group-report.md) measured the incumbent book's composition
for the first time and found two things that no Sharpe column shows:

```
6 names of 718 make half the P&L;  one name is 17%, ten are 65%
57.3% of the P&L is in the CHEAPEST price tercile, mean +118.47 bp/trade,
       where commission is 7.01 bp round trip against 0.87 in the top tercile
```

[D323](D323-RESULT-the-ranking-inverts-and-k-was-never-re-read.md) then found the
candidate ranking **inverts** with width, and that three candidates tie or beat the
incumbent — `retrace_leg` +0.557, `rev_21` +0.498, `rsi` +0.481 against the
incumbent's +0.549.

**Those two facts have never been put together.** Sharpe is tied across four
candidates and this fixture cannot resolve the +0.008 between the top two.
**Composition is not tied and has been measured for exactly one of them.**

**If a candidate earns the same Sharpe across forty names instead of six, or in
$100 names instead of $28 names, it is a materially better book at identical
Sharpe** — and that difference is far larger than anything the Sharpe column can
express.

## 2. The declared question, and what counts as "healthier" — fixed BEFORE the numbers

**PRIMARY: names to reach half the P&L.** Higher is healthier. The incumbent's is
**6 of 718** and it is the most fragile number in the programme.

**SECONDARY: the low-price tercile's share of P&L.** Lower is healthier, because
commission there is **8× the cost in basis points** and D284 died on the price
axis.

**Reported but NOT used to rank**, so that a favourable one cannot be promoted to
the headline after the fact: top-1/5/10 name share, era balance, dead-vs-alive,
the symmetric-trim group 2 block, and the breakeven multiple.

**A composite score is deliberately NOT constructed.** Two declared statistics
read separately are harder to fit than one blended number.

## 3. The cells, and the confound that decides how they are read

**`k` mechanically drives name concentration** — a 40-bar hold produces roughly an
eighth of the trades of a 5-bar hold, over fewer names. `retrace_leg`'s best cell
is **k = 40** and the incumbent's is **k = 10**, so an unmatched comparison would
measure the holding period and call it the signal.

**So every candidate is run twice:**

| | |
|---|---|
| **its own best cell** from D323 — the book someone would actually run |
| **k = 10, dv28 off** — a fully MATCHED cell across all four |

Candidates: **the incumbent confluence, `retrace_leg`, `rev_21`, `rsi`.**
`N_eff` = 2, target exit, no overlay. Costed per D318 with D321's `[F]`
held-name turnover.

**Trade count is reported beside every composition statistic**, because names-to-
half-P&L cannot be read without it.

## 4. Predictions

Three are against, and Q2 is load-bearing.

| | prediction |
|---|---|
| **Q1** | the incumbent reproduces D322's group 2 and group 3 exactly. **A harness check** |
| **Q2** | **no candidate is materially healthier than the incumbent on BOTH declared statistics at the MATCHED cell** — none reaches ≥ 12 names to half the P&L *and* a lower low-price share. *Against — load-bearing* |
| **Q3** | **the price dependence is a property of the BOOK, not the signal** — every candidate puts > 45% of its P&L in the low-price tercile. *Against the study's hope* |
| **Q4** | **name concentration is book-level too** — every candidate needs ≤ 10 names for half the P&L at the matched cell. *Against* |
| **Q5** | at each candidate's **own best** cell, names-to-half rises with `k`, and the rise is explained by trade count — so the own-best comparison is uninformative and the matched cell is the one that counts |
| **Q6** | dead names remain at least as profitable per trade as alive names for every candidate, as D322 found for the incumbent (+75.95 against +65.32). **If this fails for a candidate, that candidate has a survivorship problem the incumbent does not** |
| **Q7** | every candidate's mean sits below its median, as the incumbent's does — the two-sided tail signature is book-level |

## 5. Stop conditions

- **Q2 confirms** → composition is a property of the book, no candidate is
  structurally healthier, and **the entry axis closes for a reason that is not
  Sharpe.** Expected.
- **Q2 fails** → a candidate with equal Sharpe has materially better composition.
  **That would be the most useful finding available on this fixture**, and it
  needs its own pre-registered confirmation. It is not a promotion.
- **Q6 fails for a candidate** → that candidate is set aside regardless of its
  other numbers.
- **Q1 fails** → misimplemented; nothing else is read.

## 6. Assertions

1. **[1] Reproduction.** The incumbent's group 2 and group 3 reproduce
   `data/d322_four_group_report.json` to floating point, and its D323 cell
   reproduces `data/d323_shortlist.json`.
2. **[2] The ledger reconciles**, with the residual reported — D307c's 0.1530 bp
   was positions still open at the end of the run, and D322 saw 0.1326.
3. **[3] The symmetric trim is symmetric** — `n_dropped_top == n_dropped_bottom`.
4. **[F] FILL** — turnover on the names held; the nominal-slot form is rejected.
5. **[S] SPREAD BASIS** — round trips from the names held; the universe median is
   rejected.
6. **[C] Cost dimensions** against d295's 52.1893; the doubled form rejected.
7. **[4] Every cell is a distinct book.**
8. **[5] The self-test raises** on a book handed free money inside the mask.

## 7. Scope

**Out:** any candidate outside the four named; width; the overlay; dv28 as a
treatment — D323's Q7 showed it is fitted to the confluence, so it is **off**
everywhere here except the incumbent's own-best cell, where it is part of that
cell's definition; and the holdout.

**This study cannot promote anything.** It measures composition on books that
already exist. **If Q2 confirms, the fragility is structural and no signal on this
shortlist fixes it** — which is a more useful closure than another tied Sharpe.

## 8. Files

`docs/decisions/D324-composition-of-the-top-candidates.md` (this record) · runner
and data to follow, in separate commits. Prior evidence:
`data/d322_four_group_report.json`, `data/d323_shortlist.json`,
`data/d323b_analysis.json`.
