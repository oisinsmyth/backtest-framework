# D786 STAGE 0 PRE-REG: five China-open fade filters, read once against the outcome (candidates 2, 3, 21, 95 and 117 of the 210-verdict filter debate)

*2026-10-03. The principal: "Run the pre-registered batch read on those five candidates".*

- **What it is:** a single in-sample read of the accuracy of five pre-entry filters on gold's China-open fade (D765's
  construction, D767's selection and D770's passive book). The filter debate rejected all 210 candidates
  (`temp/gold_china_filter_debate/FINAL_REPORT_AGENTS_210.md`).
  - Most rejections were argued, not measured. Accuracy was derived as ρ(Z, x)·ρ(x, y) + ρ(Z, g)·ρ(g, y), which
    assumes Z has no path to y except through x and g.
  - The analyst's review named five candidates where that assumption, or a never-run split, carries the verdict.
- **The order (R8):** this record is committed before the runner exists, the runner before its one run, and the
  result separately.
- **It admits nothing.** The slice is 2016–2023, already read for this construction by D765, D767, D770 and the
  debate's oracle. A pass here can only nominate a candidate for a separately pre-registered confirmation. The
  principal decides whether to spend 2024+ data on it.
- **Nothing on or after 2024-01-01 is read.** Every input is asserted, as in the debate's oracle.

## 0. What is known, and what is not

| # | candidate | its accuracy before this read | how the five were chosen |
|---|---|---|---|
| 2 | B-US, US-afternoon opposition | **read:** ρ(g_US, y) +0.0524, on its rotation p97.5 (+0.0520) (D765 JSON) | the one published input at the 0.05 screen; its clock and year splits were never run |
| 21 | A-INVAUD, the AUD-confirmed open (−F3) | **read:** D767 spearman(F3, gross) −0.0515, so −F3 is +0.0515 | the other published input at 0.05; the sign was read after the run (post hoc) |
| 3 | A-PREM, onshore-premium pressure | **unread.** Derived −0.003 (ρ(dev, x) +0.056 × −0.063; ρ(dev, g) +0.010 × +0.031) | the only measured channel from onshore pricing into x |
| 95 | A-CLIENTELE, the tug of war | **unread.** Derived +0.000 (ρ(R_US, x) +0.002, ρ(R_US, g) −0.009) | the only input orthogonal to both x and g |
| 117 | A-TRANSIENT, Hasbrouck R* | **unread.** Argued 0.01–0.04 as a modulator | the debate's best-built outcome-free profile (split-half +0.465, size-free, year-balanced) |

- **Choosing 3, 95 and 117 was outcome-blind:** the analyst saw only their outcome-free profiles and the debate's
  arguments.
- **Choosing 2 and 21 was not:** their accuracies were published. A pass on either is labelled POST HOC and cannot
  nominate. Their reads are reproductions, plus the splits the debate said would move both agents.

## 1. The construction (unchanged)

- **D765's MGC cell through D767's own functions,** exactly as the debate's oracle builds it
  (`temp/gold_china_filter_debate/oracle/oracle_run.py`, `build()`):
  - x = P(09:30) − P(09:00) Beijing on GC; side = −sign(x); entry at the 09:31 open, exit at P(15:00);
  - candidates are D765-eligible sessions with x ≠ 0; one MGC at \$10 a point;
  - the taker book costs \$5.93 a round trip.
- **The passive book is D770's primary,** through its own functions: rest at the 09:30 touch, filled on a
  trade-through within 30 minutes, exit at the 15:00 touch. Cost is \$3.00 plus D770's MGC exit adjustment, filled
  sessions only.
- **The selection is D767's `wf_select`:** the walk-forward top third, with a 250-candidate window and at least 100
  finite.
- **The pool is D767's `pool_mask` of each candidate's own score:** the sessions its selection could take.

## 2. The five scores (frozen as the debate declared them; LOG.md lines cited)

The prior-60 scale is D767's `prior_median_abs`: the median |·| over the prior 60 candidates, at least 40 finite,
strictly prior.

1. **Candidate 2 (LOG 247):** S = −sign(x) · g_US / prior-60 median |g_US|.
   - g_US is D765's own column: P(17:00 ET on the prior weekday) − P(SHFE's last close), defined only when that
     close is before 17:00 ET.
2. **Candidate 21 (LOG 2917):** S = −F3 = sign(x) · x_6A / prior-60 median |x_6A|, through D767's `scores()`.
3. **Candidate 3 (LOG 434, as built at LOG 770; A's `prem.py`):**
   - The premium on SGE day D′ is p(D′) = SHAU_PM(D′) × 31.1035 / CNY fix(D′) − P_GC(14:15 Beijing on D′).
     - P_GC is D765's front-month close at the minute.
     - The fix is `data/fixtures/cny_central_parity.csv`, through D769's `load_fix`.
     - The SHAU file is copied from the debate's delivery to `data/fixtures/sge_shau_benchmark_2016_2023.csv`, with
       its meta.
   - **The chain:** day-over-day changes of p on the same GC contract; a roll day or a missing day contributes 0;
     the changes are cumulated.
   - dev(D′) = chain(D′) − the mean of the chain over the 20 SGE days strictly before D′ (all 20 required); undefined
     where p(D′) is undefined.
   - **For session D:** dev of the last SGE day strictly before D, and none older than 5 calendar days.
   - S = −sign(x) · dev / prior-60 median |dev|.
4. **Candidate 95 (LOG 6850; A's `clientele.py`):**
   - R_US = log P(13:30 ET) − log P(08:20 ET) on the US weekday before the session's date, through D765's `Px`.
     Both prices must be on one contract and not void, and 13:30 ET must be before 09:00 Beijing (asserted).
   - S = sign(x) · R_US / prior-60 median |R_US|.
   - **Declared secondary (as at the time):** the London morning, R_LDN = log P(08:20 ET) − log P(03:00 ET), in
     place of R_US.
5. **Candidate 117 (LOG 8333; A's `impact.py`):** the paid GC tbbo in [09:00, 09:30) Beijing, through D770's
   reader (read-only, cut at 09:30 and asserted).
   - Keep the dominant contract by traded size, trades with side B (+1) or A (−1), and valid quotes (ask > bid).
   - m is the pre-trade midquote in ticks.
   - **Immediate impact:** i1 = mean of q_t(m_{t+1} − m_t).
   - **β1** is the coefficient on q_t in the OLS of (m_{t+20} − m_t) on [q_t, Σ_{j=1..20} q_{t+j}].
   - R* = β1 / i1 when i1 > 0. A session needs at least 60 trades in the window and at least 50 after the filter.
   - S = −(R* − the median of R* over the prior 60 candidates, at least 40 finite, strictly prior). Transient opens
     score high.

## 3. The statistics, the null and the gates

- **Accuracy (the debate's requirement 5):** Spearman ρ(S, gross) over the candidate's own pool. On the taker book
  it is the primary; on the passive book (pool ∩ filled) the secondary.
- **The null:** the exact rotation of the INPUT over the candidate sequence, every offset 1 … n−1 (SE 0).
  - The rotated input is rolled with its NaNs. S is rebuilt with each session's own sign(x) and the rotated series'
    own prior-60 scale (for 117, its own trailing median).
  - This keeps S's tie to |x| and to the calendar, and breaks only the input's alignment with the session.
  - Reported: p50, p95, and the rank of the observed value.
- **The book:** the walk-forward third. Reported: mean net and its t, taker and passive; B1 (the largest month-share
  gap against the pool); B2 (total net outside Dec–Mar).
  - The third's mean net is also rotated through D767's `rotation()` form (row 0 is the observed value): p50, p95,
    rank.
- **The gates, per candidate, on the taker book:**
  - **A:** ρ ≥ 0.05 AND above the rotation p95;
  - **G2:** the third's mean net > 0 and net t ≥ 2;
  - **B1:** month gap ≤ 5 points;
  - **B2:** net outside Dec–Mar > 0.
- **The readings, in order:**
  - **NO EFFECT:** A fails;
  - **BELOW THE BAR:** A passes, G2 fails;
  - **SEASONAL:** A, G2 and B1 pass, B2 fails;
  - **SUPPORTED IN-SAMPLE:** all four pass.
- **A season-free reading is declared now, not after:** A, G2 and B1 only.
  - The analyst's review found the Dec–Mar split to be a post hoc contrast of about 2.3 SE, with a null monthly
    omnibus (chi² 10.6 on 11 df). B2 is therefore reported both as the debate's gate and without it.
- **Passive:** the same gates on the passive book are reported. A passive-only pass is read PASSIVE ONLY, under D770's
  adverse-selection caveat.
- **Multiplicity:** Holm across the three unread candidates (3, 95, 117), on the rotation p-value of ρ, at a
  one-sided 0.05.
  - A SUPPORTED reading on 3, 95 or 117 nominates only if it also survives Holm.
  - 2 and 21 are POST HOC whatever they read.

## 4. Power (stated before the run)

- **The pool** is about 1,400–1,450 per candidate, so the SE of ρ is about 0.026, and the rotation p95 sits near
  +0.043.
- **At a true ρ of 0.05:**
  - P(A) is about 0.5, since the bar is the point estimate;
  - Holm's first step at α/3 needs about +0.056, so P(nominate) is about 0.4.
- **At a true ρ of 0.10,** P(A) is about 0.97, and Holm's first step about 0.96.
- **G2 is the binding gate.** The debate's oracle puts P(G2) at about 0.18 at ρ 0.10 and 0.49 at ρ 0.13 (taker), and
  about 0.48 and 0.76 (passive).
  - A real filter at the debate's argued 0.02–0.05 reads NO EFFECT or BELOW THE BAR with high probability.
  - This read can CONFIRM the debate's rejections as measurements, and find only a large effect.

## 5. Predictions (the analyst's, before the run)

- **All five read NO EFFECT or BELOW THE BAR.**
- **2 and 21 reproduce their published values** (+0.052 and +0.0515 up to pool differences), with no split above
  0.10.
- **3, 95 and 117 read within ±0.05 of zero,** and the measured ρ agrees in sign with the derived chain within 2 SE.
  A disagreement beyond 2 SE would be the first evidence that the screen's no-direct-path assumption fails.
- **Prior that any of the three unread candidates is SUPPORTED IN-SAMPLE and survives Holm:** about 2%.

## 6. Reported beside the gates

1. **Measured against derived:** ρ for each candidate next to the debate's derived or argued value (§0), with the
   difference in SE.
2. **Splits of ρ:**
   - EST against EDT;
   - Dec–Mar against Apr–Nov;
   - by year (8 values);
   - before and after the SHFE day-session auction (2023-05-26; 133 sessions after).
3. **The four groups** for each candidate's taker third:
   - net and gross side by side, Sharpe and Sortino annualised by the book's own trades a year;
   - the trade distribution: count, mean, median, win rate, payoff, skew, kurtosis, and the three 1% trimmed means;
   - what the winners depend on: profitable years, net without the best year, the five largest trades;
   - the nulls (§3).
4. **The component line** for each taker third:
   - net Sharpe at \$5.93, hit rate, skew, gross beside net;
   - its daily ρ with the unfiltered D765 MGC fade (the same clock: a gated subset of it), D775 and D777's MNQ book,
     through D777's functions as D780 did.
   - D755's other-lines file no longer exists (temp); its components are not computed and are named.
5. **Profiles for each score,** to check the build against the debate's figures:
   - defined count, ρ(S, |x|), ρ(Z, x), ρ(Z, g);
   - the selected count, month and year gaps, and the Dec–Mar share.
6. **Candidate 95's London-morning secondary,** with the same statistics.

## 7. Runner assertions

- **Right quantity, first:**
  - the taker book reproduces D767's MGC pool (1,697 candidates, mean gross +\$3.14, t 2.49, mean net −\$2.79);
  - the passive book reproduces D770 (1,466 filled, +\$2.12 gross, −\$0.92 net);
  - spearman(F3, gross) on D767's U pool reproduces −0.051523 to 1e-6;
  - D765's ρ(g_US, y) is reproduced on D765's own set (n 1,657, +0.052436).
- **The lag audit,** a second implementation on 40 sampled sessions per score, explicit loops and no pandas rolling:
  - every input is stamped strictly before 09:30 Beijing (117) or before 09:00 (2, 3, 95);
  - the prior-60 scales use strictly prior candidates;
  - the selection flag matches a hand-written quantile.
- **The sign audit in money:** a reversal pays the fade; a mirrored book raises.
- **The rotation:** offset 0 reproduces the observed ρ and the observed third; the offsets enumerated are exactly
  n − 1.
- **The seal:** a planted 2024 row raises in the SHAU loader, the fix, the D765 cache and the paid reader.
- **Speed:** the tbbo reads for 117 and the passive book run in processes over days[i::N], with chunk == whole proven
  bit-identically on a sample in the self-test.
- **The self-test** includes a planted score correlated with gross that passes A, and a shuffled one that fails it.

## 8. Output, and the decision it feeds

- `scripts/stage0_d786_china_open_five_filters.py`; `data/stage0_d786_china_open_five_filters.json` (statistics
  only). The result is a separate record.
- **If 3, 95 or 117 reads SUPPORTED IN-SAMPLE and survives Holm,** the analyst recommends a pre-registered 2024+
  confirmation. It would be split at the SHFE auction change, with its power stated, and the principal decides
  whether to spend the slice.
- **Otherwise,** the five argued rejections become measured ones, and the debate's no-direct-path assumption is
  checked on the five inputs where it mattered. The filter line on this fade keeps one open item: candidate 16 (SGE
  volume), which needs data.
