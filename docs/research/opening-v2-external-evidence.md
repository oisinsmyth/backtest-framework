# The opening model's v2: external evidence on the target, the decision, the exits and the inputs

*2026-09-28. Commissioned by the principal: "Give each group to a Fable 5.1 Agent and tell it to first do online
research about each point, then reason and combine all the results back to you." Three agents, one group each, were
told to research first, then reason about this study, and to read no data file and edit nothing. Their reports are
kept below **verbatim**. Written before Phase 4 has run, so no Phase 4 result shaped them; they did read D645-D647,
so D646/D647's in-sample findings did.*

**Status of what is below, and how to cite it:**
- **The sources D652 leans on were checked on 2026-09-28 (the table below); the rest were not.** Several are practitioner or vendor pages, not
  peer-reviewed (dev.to/FirmTape, tradingstats.net, the mql5 replication, Volatility Box, SpotGamma, oxfordstrat).
  Two arXiv papers are dated 2026 (2605.04004, 2607.01550). A record that leans on any one of them checks it first
  (memory: verify the claims inside an option).
- **Items the agents mark [reasoning] or *(reasoning)* are theirs, not a source's.** Numbers they derive from D647
  (the payoff matrix, the ~0.26 CONT breakeven, the ~0.2-0.4 bp/day ceiling) are in-sample and seen.
- **What the programme did with it:** D652 pre-registers a separate construction built on these reports (the
  principal, 2026-09-28: "lets make those changes and test them as a separate model"; the vault after an in-sample
  test; the observables plus A4 rescaled). OA-A10 records it beside OA-A8.

## Citation check (2026-09-28, the principal: "do 1"), for the sources D652 leans on

Each was opened at its source. "Holds" means the report's claim matches the source; anything else is corrected here.

| source | the report's claim | at the source | verdict |
|---|---|---|---|
| Cboe press release, 2022-04-13 ([link](https://ir.cboe.com/news/news-details/2022/Cboe-to-Add-Tuesday-and-Thursday-Expirations-for-SPX-Weeklys-Options-04-13-2022/default.aspx)) | Tuesday expiries 2022-04-18, Thursday 2022-05-11 | those are the **listing** dates. The first Tuesday **expiry** is 2022-04-26 and the first Thursday expiry is **2022-05-19** | **CORRECTED.** Every session carries a same-day SPX expiry from **2022-05-16** (the Monday of the week of the first Thursday expiry), not from 2022-05-11. D652 §2's date follows the listing date, so its stated rule and its date disagree by 3 sessions |
| Barbon & Buraschi, *Gamma Fragility* ([SSRN 3725454](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3725454)) | $gamma imbalance ÷ ADV; momentum (reversal) from negative (positive) gamma × illiquidity | "dollar gamma imbalance … as a fraction of the average daily volume of the underlying"; the effect is stronger in less liquid names | **HOLDS.** D652's denominator is a **disclosed variant**: the 09:30 → t0 window's dollar volume over 20 sessions, not full-day ADV (window-matched, per report C) |
| Mesfin, [arXiv 2605.04004](https://arxiv.org/abs/2605.04004) (v1 2026-05-05, v3 2026-09-15) | MNQ 2021–25; none of 14 OHLCV families pass | as stated: 947 days of 5-minute data, 14 families, none pass all five criteria. **Omitted by the report:** two control signals do pass (RTH confluence, OOS t 3.11; a London-session signal, t 4.30) | **HOLDS, with the omission noted.** A single-author preprint |
| Kurth, Eisler, Rej & Bouchaud, [arXiv 2607.01550](https://arxiv.org/abs/2607.01550) (2026-07-02) | short-term trend died on small-tick contracts; intact on large-tick | as stated: since ~2009, trend P&L has collapsed on small-tick contracts and is "essentially intact" on large-tick ones, which the authors attribute to HFT liquidity withdrawal | **HOLDS.** A preprint (CFM authors) |
| FirmTape on DEV ([link](https://dev.to/firmtape/intraday-momentum-is-dead-in-the-0dte-era-we-measured-it-on-1085-spx-sessions-43g0), 2026-08-27) | 1,085 SPX sessions; slope flat (t 0.6); +0.055 (t 3.1) on short-gamma days, ~15% | as stated (2022-04-14 → 2026-08-20; +0.006 ± 0.009). Gamma is the vendor's own "tape-signed 0DTE dealer book at 15:30" | **HOLDS as reported, WEAK as evidence:** a gamma-data vendor's blog, not reviewed, with a proprietary signed-gamma measure |

Not re-opened, because they are well-established published papers cited for their central results: Gao, Han, Li &
Zhou (JFE 2018); Baltussen, Da, Lammers & Martens (JFE 2021); Elkan (2001); Kaminski & Lo (2014); Dim, Eraker &
Vilkov (0DTE gamma, SSRN 4692190); Brogaard, Han & Won (0DTE volatility). The practitioner pages (tradingstats,
mql5, Volatility Box, SpotGamma, oxfordstrat) stay unchecked and carry no weight in D652.

## The combined reading (written by the session that commissioned them)

1. **The label is the wrong question.** CONT is open-to-close; the published continuation is a last-half-hour,
   hedging-driven effect (Gao et al. 2018; Baltussen et al. 2021), so the 60-minute trade exits before most of what
   the label measures. Two alternative fixes: label by the trade's own outcome (A), or hold the continuation trade
   to the close (B).
2. **Decide on expected value, not argmax.** argmax + θ over a 62% RANGE class is a symmetric-cost rule on an
   asymmetric problem (Elkan 2001). Shift the threshold; do not resample the classes (van den Goorbergh et al. 2022).
3. **Exits by state.** The 0.5 × opening-range stop sits at ~0.56 σ of the hour (touched ~58% of the time by a
   driftless path). A stop subtracts on a mean-reverting trade (Kaminski & Lo); the gap fade is one. Wider for
   continuation.
4. **Dealer gamma is the one mechanism offered for trend days**, as $gamma over dollar volume (Barbon & Buraschi),
   and the 0DTE era erodes a t-1 open-interest measure of it. The break is a ramp from 2022; declare the date from
   the calendar.
5. **What it does not fix: power.** On S-A's observables the ceiling is ~0.2-0.6 bp a day against a vault that can
   resolve ~4-8 bp. The gain, if any, has to come from inputs that rank the outcome.

## The three reports, verbatim

<!-- report A -->
### Group A — what the opening model should predict

Scope: web research plus reasoning; no repository data read, nothing edited. Repo context from D645/D646/D647 only. Items marked **[reasoning]** are mine, not a finding.

#### Framing that the literature forces

Every published intraday-continuation result on index products is about the **last half-hour**, not the whole session. Gao, Han, Li & Zhou (JFE 2018; SPY 1993–2013) find the first half-hour predicts the last half-hour, R² 1.6%, stronger on volatile, high-volume and news days ([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2440866)). Baltussen, Da, Lammers & Martens (JFE 2021; 60+ futures 1974–2020) find the rest-of-day return predicts the last half-hour, that it **reverts over the next days**, and tie it to gamma hedging (option market makers, leveraged ETFs) concentrated near the close ([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3760365)); they note intraday jumps predict subsequent returns but "the bulk of the hedge" is late-day. From memory (not confirmed today, the PDF was blocked): Gao et al. report no significant prediction of the midday half-hours. **[reasoning]** The CONT label (open-to-close continuation) therefore contains a large component generated *after* the 60-minute trade has exited, by flows that do not exist at t0. That is consistent with D647: CONT one-vs-rest AUC 0.506, yet p_CONT ranks the 60-minute trade (Spearman 0.62 over deciles). The label is mis-specified for the decision; the classifier may be less blind than the label makes it look.

#### 1. Match the target to the trade

**What the research says.** López de Prado's critique of fixed-horizon labels is that they ignore the path (a stopped-out trade can be labelled a winner) and take no account of the exits actually used; the triple-barrier method labels by which of profit-target / stop / time barrier is touched first, and **meta-labeling** trains a secondary model on whether a fixed primary rule's trade makes money, separating side from size ([Quant Memo](https://www.quantmemo.com/concepts/triple-barrier-labeling), [mlfinpy](https://mlfinpy.readthedocs.io/en/latest/Labelling.html), [Wikipedia](https://en.wikipedia.org/wiki/Meta-Labeling)). Joubert (JFDS 2022) formalises meta-labeling as a filter/sizer that improves Sharpe and drawdown of a primary strategy, and the Singh & Joubert experiment finds it helps mainly by removing false positives — and says explicitly that a bad primary is only "reduced on the downside" ([JFDS](https://jfds.pm-research.com/content/4/3/31), [PDF](https://hudsonthames.org/wp-content/uploads/2022/04/Does-Meta-Labeling-Add-to-Signal-Efficacy.pdf)). Decision theory: fit with a proper score (log loss) and choose the action by expected value — Elkan's optimal threshold is a function of the payoff asymmetry, not 0.5 or argmax ([Elkan 2001](https://cseweb.ucsd.edu/~elkan/rescale.pdf), [scikit-learn](https://scikit-learn.org/stable/auto_examples/model_selection/plot_cost_sensitive_learning.html)). Patton's point that the loss must match the quantity the forecaster was asked for applies directly ([Patton](https://public.econ.duke.edu/~ap172/Patton_bregman_comparison_22dec16.pdf)). The intraday-regime literature labels by fixed-horizon or end-of-session returns, never by the trade's own exits; the closest academic precedent for a decision-matched intraday rule is Zarattini–Aziz–Barbon's noise-area breakout (SPY 2007–2024, Sharpe 1.33) ([SSRN](https://ssrn.com/abstract=4824172)), whose independent replication held to 2024 and went to ~zero Sharpe in 2025–26 on both SPY and ES ([codecat replication](https://github.com/codecat-ops/zarattini-2024-momentum-spy)).

**Applied here.** D647's oracle (CONT +12.6 bp, FADE +6.4 bp) is a ceiling on a label the trade cannot see. Replace the state label with the *outcome of the pre-registered trade itself*: does B1 (follow d0, 0.5×range stop, 60-minute stop) net > 0; does the gap-fade net > 0. Two facts already favour this: FADE days fill a median 80% of the gap **inside the hour** (D647 §5), and p_CONT's dose-response is on the 60-minute trade. The RANGE class disappears: "no trade" becomes a threshold decision on a calibrated probability rather than a 62% base class swallowing the argmax.

**Pitfalls.** (i) Circularity is fine as long as features stop at t0 and the label engine is the *same* exit engine that scores the policy (assert the label's P&L equals the scorer's on every row; the repo's `assert_matches_scorer` rule). (ii) The 09:45 and 10:00 labels share ~45 minutes of path — one family, Holm across t0. (iii) Do **not** resample or reweight the classes: van den Goorbergh et al. (JAMIA 2022) show under/over-sampling and SMOTE wreck calibration and do not raise AUC; shift the threshold instead ([arXiv](https://arxiv.org/abs/2202.09101)). (iv) This label points toward short-horizon price-path momentum, which the repo's memory records as empty on futures at every horizon — expectation for the B1 side is low; the fade side is the better bet. (v) D647 already looked at the in-sample through this lens (deciles); the only clean test is the vault or forward recording.

**Pre-registrable spec A (meta-label of the pre-registered trade).**
- Primaries: P1 = B1 (d0 at close of t0+1); P2 = fade toward prior close, only on |gap| ≥ 0.25 ATR. Exits exactly D645 §6.3 minus the state-flip.
- Label: y = 1{net P&L of primary > 0}, computed by the scoring engine (diagnostic only: the triple-barrier three-way outcome — target +0.5×range / stop / time).
- Model: L2 multinomial → binary logistic, same five observables + market dummy, same 252/63 walk-forward and C grid, no class weights.
- Decision: trade primary k iff p̂·m⁺ − (1−p̂)·m⁻ > 0, with m⁺, m⁻ the training window's mean net win and loss of primary k (Elkan threshold, fixed before the test window).
- Fit statistic: log loss vs base rate. Decision statistic: policy net bp/day, policy's own net > 0 (D645 second condition), HAC t vs B1; report top-decile lift with a day-block bootstrap.
- Inference: four cells (2 primaries × 2 t0), Holm; one look on the vault (2025-03 onward) or forward.
- Assertions: label == scorer P&L; leak canary; the oracle (true y) must reproduce a positive net (a check that can fire).

**Expected size.** Log loss will likely improve (the target is now the thing the features rank). Decision value is bounded by D647's own deciles: top-decile continuation +1.6 bp net (t ≈ 0.8), fade top decile +2.5 bp net (t ≈ 1.2) — on ~10% of days that is ~0.2–0.4 bp/day, under POWER's MDE of 1.84 bp. Honest verdict: on S-A features this fixes the failure mode (RANGE dominance, argmax+θ) but probably not the power problem; its main value is making Phase 4 agent information *tradable within the hour* instead of scored against a 6-hour label.

#### 2. A binary "trend day or not?"

**What the research says.** Market Profile day types are hindsight labels; practitioners' own guides say a day "becomes" a trend day only after it trends ([Timeless Market Theory](https://timelessmarkettheory.com/concepts/day-types)); the one quantitative test found the classic structures do not cover the modern market though the initial balance matters ([Wikipedia summary](https://en.wikipedia.org/wiki/Market_profile)). Crabel's NR7/ORB claims are practitioner statistics; an independent 33-year, 42-market test of the 2-bar NR pattern exists but is a vendor study ([Oxfordstrat](https://oxfordstrat.com/trading-strategies/toby-crabel-narrow-range-1/)). Academic ORB: Tsai et al. (IEEE Access 2019) find >8% p.a. on five index futures 2003–2013 with a short optimal probing time in US markets ([ADS](https://ui.adsabs.harvard.edu/abs/2019IEEEA...732061T/abstract)); Mesfin (arXiv 2026, MNQ 2021–25, walk-forward, 2-pt friction) finds ORB-long at a 75-minute hold net +2.8 pts but t 0.88 and year-unstable, ORB-short negative, and gap-continuation-short t 1.46 on 35 trades — none of 14 OHLCV families pass ([arXiv](https://arxiv.org/abs/2605.04004)). Day-level "trending vs oscillating" ML on SPY/QQQ (2000–2024, VIX/ATR/macro features) beats naive by 1–15% but the authors call it a regime filter, not alpha ([MDPI](https://www.mdpi.com/1911-8074/19/4/262)) — **[reasoning]** a range-threshold label is mostly a volatility forecast, and volatility clustering is why it is predictable; direction is the hard part. Tang et al. claim ~70% accuracy predicting SSE-50 intraday trend from the first 10 minutes but report no base rate ([T&F](https://www.tandfonline.com/doi/full/10.1080/0013791X.2023.2205841)) — weak. Bergsma et al. (2020) show first-30-minute option order flow predicts rest-of-day returns for single stocks, strongest in small/illiquid names — not the index ([Wiley](https://onlinelibrary.wiley.com/doi/10.1111/fima.12284)). Class-imbalance methodology: rare-event work in HFT uses thresholding and cost-weighting, not resampling ([arXiv 2503.09988](https://arxiv.org/abs/2503.09988)).

**Applied here — the trap.** D647's one-vs-rest CONT AUC of 0.506 **is** the binary trend-day discrimination. Collapsing to two classes changes the loss weighting and the decision rule, not the information; with these features, no threshold makes a 16%-prevalence class with AUC 0.5 tradable. The literature's one lever on trend days is dealer gamma: Baltussen et al. find momentum present when net gamma exposure is negative and stronger the more negative; the 0DTE-era note below agrees. That is the repo's A4 agent, i.e. Phase 4 — so the binary target is the right *scorecard* for Phase 4, not a new S-A model.

**Pre-registrable spec B (scorecard).** y = 1{CONT} under D644's unchanged rule (prevalence fixed by the label, not chosen). L2 logistic, no class weights. Report PR-AUC and precision@top-10% against prevalence, with block-bootstrap SE. Agent-stage retention bar: precision@10% ≥ 2× prevalence and PR-AUC ≥ 1.5× prevalence. Decision, if it ever passes: Elkan threshold from the training-window oracle payoffs (m⁺ ≈ the +12.6 bp class, m⁻ the stopped-out loss). Pitfalls: multiplicity across agent stages (Holm), 0DTE-era prevalence drift (report by era), and a positive control that the true-label oracle clears the bar.

**Expected size.** None on S-A features (by construction). If A4 at t0 carries what Baltussen's NGE carries, a CONT AUC in the 0.55–0.60 range is plausible **[reasoning, thin]**; nothing published gives a t0-conditioned number.

#### 0DTE era

Adams, Dim, Eraker, Fontaine, Ornthanalai & Vilkov: index vol ~60 bp lower on days with 0DTE trading; dealers hold **positive** net gamma through expiry days; higher gamma predicts *negative* high-frequency momentum and stronger E-mini order-flow reversals ([Quantpedia summary](https://quantpedia.com/do-sp500-0dtes-options-increase-market-volatility/), [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5641974)). Amaya, Garcia-Ares, Pearson & Vasquez (Jan 2025, Cboe trade data Jul 2020–Jun 2023): OMM gamma typically positive and dampening, occasionally negative with at most +3.3 pp daily vol ([PDF](https://cdn.cboe.com/resources/education/research_publications/gammasqueezes.pdf)). A non-peer-reviewed measurement of 1,085 SPX sessions 2022-04 to 2026-08 finds the unconditional last-half-hour momentum slope flat (t 0.6, sign alternating by year) but +0.055 (t 3.1) on the 15% of sessions where dealers are short gamma ([dev.to](https://dev.to/firmtape/intraday-momentum-is-dead-in-the-0dte-era-we-measured-it-on-1085-spx-sessions-43g0)). The Zarattini replication's 2025–26 collapse and Mesfin's 2023–25 instability point the same way. D647's B1 by-year (positive 2017–20 and 2024, negative 2021–23 and 2025) is consistent. Implication: expect CONT prevalence and payoff to be lower post-2022 except on short-gamma days; any v2 reports pre/post-2022 separately.

#### Ranked recommendation

1. **Spec A, fade primary first, continuation second** — the label matches the decision, the fade already resolves inside the hour, no class imbalance to handle, and it removes the argmax-over-RANGE failure. Expected gain small on S-A; genuine on structure.
2. **Spec B as the Phase 4 scorecard** (PR-AUC / precision@10% for CONT), not as a new S-A model — the binary AUC is already measured at 0.506.
3. **Condition on A4 (dealer gamma) at t0** as the first Phase 4 stage tested under both specs — the only mechanism the literature offers for trend days, and the one the 0DTE-era evidence keeps.
Do not retest any of this on the 2016–2025-02 in-sample; D647 has seen it.

#### Sources
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2440866
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3760365
- https://www.quantmemo.com/concepts/triple-barrier-labeling
- https://mlfinpy.readthedocs.io/en/latest/Labelling.html
- https://en.wikipedia.org/wiki/Meta-Labeling
- https://jfds.pm-research.com/content/4/3/31
- https://hudsonthames.org/wp-content/uploads/2022/04/Does-Meta-Labeling-Add-to-Signal-Efficacy.pdf
- https://cseweb.ucsd.edu/~elkan/rescale.pdf
- https://scikit-learn.org/stable/auto_examples/model_selection/plot_cost_sensitive_learning.html
- https://public.econ.duke.edu/~ap172/Patton_bregman_comparison_22dec16.pdf
- https://arxiv.org/abs/2202.09101
- https://arxiv.org/abs/2503.09988
- https://ssrn.com/abstract=4824172
- https://github.com/codecat-ops/zarattini-2024-momentum-spy
- https://timelessmarkettheory.com/concepts/day-types
- https://en.wikipedia.org/wiki/Market_profile
- https://oxfordstrat.com/trading-strategies/toby-crabel-narrow-range-1/
- https://ui.adsabs.harvard.edu/abs/2019IEEEA...732061T/abstract
- https://arxiv.org/abs/2605.04004
- https://www.mdpi.com/1911-8074/19/4/262
- https://www.tandfonline.com/doi/full/10.1080/0013791X.2023.2205841
- https://onlinelibrary.wiley.com/doi/10.1111/fima.12284
- https://quantpedia.com/do-sp500-0dtes-options-increase-market-volatility/
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5641974
- https://cdn.cboe.com/resources/education/research_publications/gammasqueezes.pdf
- https://dev.to/firmtape/intraday-momentum-is-dead-in-the-0dte-era-we-measured-it-on-1085-spx-sessions-43g0
- https://tradingstats.net/gap-fill-strategy/ (vendor; NQ 2015–25 gap-fill by ATR tier, used only as colour)

<!-- report B -->
### Report: decision rule and exits for the opening-regime model (Group B: points 2, 3, 7)

Scope: web research plus reasoning. Nothing in the repository's data was read or run; D645–D647 were read for context. Statements marked *(reasoning)* are my inference, not a source's.

#### Point 2 — Trade on expected value, not argmax

**Literature.** Elkan (2001): once probabilities are trusted, the optimal decision minimises expected cost under the cost matrix, not argmax; two-action threshold `p* = C_FP/(C_FP+C_FN)`; rebalancing training data is the wrong lever ([ACM](https://dl.acm.org/doi/10.5555/1642194.1642224), [Semantic Scholar](https://www.semanticscholar.org/paper/The-Foundations-of-Cost-Sensitive-Learning-Elkan/7fed3e00be2bb09510f5f7cad7ac106e6c94a359); multi-class thresholding [Springer 2025](https://link.springer.com/article/10.1007/s11634-025-00651-8); [scikit-learn post-tuning](https://scikit-learn.org/stable/auto_examples/model_selection/plot_cost_sensitive_learning.html)). Calibration is the precondition: Kull et al. 2019 show Dirichlet calibration (multinomial logit on log-probs) beats temperature scaling and introduce class-wise ECE, the right diagnostic when the actionable class is rare ([NeurIPS 2019](https://proceedings.neurips.cc/paper/2019/hash/8ca01ea920679a0fe3728441494041b9-Abstract.html)). Kelly from estimated probabilities over-bets; the fraction shrinks with the estimate's variance (Baker & McHale 2013, [INFORMS](https://pubsonline.informs.org/doi/10.1287/deca.2013.0271); [arXiv 1701.02814](https://arxiv.org/pdf/1701.02814)). Meta-labelling trains a secondary model on whether the primary's trade paid, for filtering/sizing ([Wikipedia](https://en.wikipedia.org/wiki/Meta-Labeling), [Hudson & Thames](https://hudsonthames.org/meta-labeling-a-toy-example/)); the standing critique: a secondary model on the same features adds no information and lowered mean Sharpe in grid simulations ([QuantConnect](https://www.quantconnect.com/forum/discussion/14706/why-meta-labeling-is-not-a-silver-bullet/)).

**Applied here** *(reasoning)*. argmax+θ=0.45 over a 62% base class is a symmetric-cost rule on an asymmetric problem, and is why CONT is never traded. Using D647's oracle numbers as a payoff matrix (with-d0 on true CONT ≈ +12.6 net; against-gap on true FADE ≈ +6.4; wrong-way ≈ −9 to −12; RANGE ≈ −2.8), EV(with d0) at base rates ≈ 0.17×12.6 − 0.21×9 − 0.62×2.8 ≈ −1.5 bp, matching B1's −2.0. Solving EV=0 with p_F≈0.2 gives a CONT breakeven near **p_C ≈ 0.26** — the top two deciles, where D647 found p_CONT ranks the trade (Spearman 0.62; top decile +1.6 net, t≈0.8). The EV rule therefore turns a 1.5–2%-of-rows policy into perhaps 10–20%, which also fixes POWER's per-traded-day problem. The gain is bounded by discrimination (CONT AUC 0.506): expect +1 to +3 bp net per trade at S-A, not the oracle's +12.6, until Phase 4 moves the CONT probabilities. Meta-labelling on the trade's own P&L label is not the "same orange" here (day-type label ≠ exit-defined trade outcome; it is D647's horizon-matched hypothesis in another form), but it is a second fitted model on the same in-sample and doubles the selection surface.

**Pre-registrable spec.**
- At t0, for candidate trades A (with d0) and B (against the gap): `EV_X = Σ_s p_s · m_s(X) − c_t`, with `m_s(X)` = mean gross bp of trade X under the registered exits on training-window sessions with true label s, and `c_t` = the round-trip cost in bp at the current price (fixed dollars ÷ price × multiplier — the NG lesson, dollars not bp).
- Shrink `m_s(X)` toward the pooled all-window mean with weight `n_s/(n_s+50)` (~75 CONT rows per market per 252-session window is too few for a raw mean).
- Trade the higher-EV side if `EV > δ`; δ = 0 primary, δ = 1 bp the single robustness variant; flat otherwise. No sizing (one micro makes Kelly a threshold; Baker–McHale shrinkage is the δ).
- Calibration guard: per-class reliability and class-wise ECE on OOS windows; Dirichlet recalibration fitted on the training window's inner CV folds only if the CONT reliability slope is < 0.8 in training, declared before the run.
- Pitfalls: δ and the shrinkage constant are choices; the rule was conceived after D647's oracle payoffs, so in-sample re-runs confirm nothing; the vault is one look.

#### Point 3 — Size the stop to the holding period

**Literature.** Kaminski & Lo: under a random walk a stop always lowers expected return; the stopping premium is positive only with positive serial correlation and proportional to it; for mean-reverting returns stops destroy value ([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=968338), [MIT](https://dspace.mit.edu/bitstream/handle/1721.1/114876/Lo_When%20Do%20Stop-Loss.pdf)). Lo & Remorov 2017: with transaction costs tight stops underperform; they outperform only when serial correlation is high enough ([SSRN](https://doi.org/10.2139/ssrn.2695383), [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1386418117300472)). The ORB evidence is a live example: the Zarattini/Aziz QQQ rule (stop at the far side of the first 5-min candle, ~24% hit rate, +0.13R) reproduces gross on five index CFDs 2015–2026 but nets ≈0 to −0.08R because a tight stop makes the fixed round trip ≈0.1R ([mql5 replication, Sept 2026](https://www.mql5.com/en/blogs/post/776235); [CXO on the no-spread assumption](https://www.cxoadvisory.com/technical-trading/day-trading-with-an-opening-range-breakout-strategy/); stocks paper stop = 10% of 14-day ATR, [SSRN 4729284](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4729284)). Volatility-scaled stops reduce noise stop-outs relative to fixed ones (practitioner backtests only, [Volatility Box](https://volatilitybox.com/research/volatility-adjusted-stop-losses/)).

**Applied here** *(reasoning)*. Stop = 0.5 × the 09:30→t0 range. Expected range of a driftless path over T ≈ 1.6σ√T, so at t0=10:00 the stop ≈ 0.8σ_30min ≈ 0.56σ_60min. A barrier at 0.56σ of the horizon is touched with probability ≈2(1−Φ(0.56)) ≈ 58% driftless — consistent with B1's 47% stop rate and 31–35% on true-label days. **The stop sits inside the hold's noise band.** FADE is a gap fill (median 80% within the hour), the mean-reverting case where stops subtract; 35% of *true* FADE trades were stopped, so the stop is plausibly converting winners into losers. For CONT a stop pays only if within-hour serial correlation exists, and the 0DTE evidence below says it is weaker than in 2016–2020.

**Pre-registrable spec.**
- `σ_h` = trailing 20-session std of the log return from the t0+1 close to the t0+61 close (same clock, prior sessions only).
- FADE: **no price stop**; state-flip and 60-min time stop; a target at the prior close (the gap fill), since the payoff is bounded there.
- CONT: stop at `1.5 × σ_h` from entry (≈13% driftless touch); state-flip and time stop unchanged.
- Report stop-out share and mean net with/without the stop, one pair per state; no grid.
- Pitfalls: 1.5 was chosen after seeing stop-out rates; declare once. A wider stop fattens the loss tail: report trimmed means and the losing-tail size. Expected effect: FADE per-trade mean up a few bp with fatter losses; CONT roughly neutral. Evidence for the exact multiplier is thin (no peer-reviewed intraday index study).

#### Point 7 — Choose the entry time on purpose

**Literature.** The two states want different clocks. Gap fills front-load: ES/NQ 2020–2025 (5-min bars, 803/839 days, non-peer-reviewed) 51–61% of fills by 10:00 ET, 66–73% by 10:30, 87–91% by noon; fill rates fall from ~78% (<0.3 ATR) to ~8% (>1.2 ATR) ([tradingstats](https://tradingstats.net/when-do-gaps-fill/)). Continuation is a rest-of-day phenomenon: the return to 15:30 predicts the last half-hour across 60+ futures 1974–2020, tied to gamma and leveraged-ETF hedging ([Baltussen et al. JFE 2021](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3760365); [Gao et al. JFE 2018](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2440866)). Crabel's ORB trades a fixed "stretch" off the open early; the Zarattini stocks paper found the 5-minute range dominated 15/30/60 ([danfin](https://danfin.net/opening-range-breakout-research)). H-O3 says information keeps arriving (log-loss gain 2.4% → 5.7%; predicted not-RANGE 2.6% → 10% by 11:00).

**Applied here** *(reasoning)*. Waiting helps CONT and hurts FADE: by 10:30 most of a fillable gap is gone, while a trend day still has 5.5 hours. The single t0 and 60-minute hold is the worst compromise for both.

**Pre-registrable spec.**
- FADE: t0 = 09:45 only; entry at the t0+1 close; exits as in point 3.
- CONT: t0 = 10:30 (initial-balance close; H-O3 gain 3.8%); entry at the t0+1 close; hold to 15:55 with the 1.5σ_h stop scaled to that horizon (σ_h over 10:31→15:55); state-flip at 11:00 retained.
- H-O4's latency curve re-run per state at its own t0.
- Pitfall: CONT's label is open-to-close, so a hold-to-close overlaps the label's definition — fine out of sample (a trade, not a feature), circular in-sample (D647). Two t0 × two states = four cells; Holm across them.

#### The 0DTE era

Real but mixed. A non-peer-reviewed retest of 1,085 SPX sessions (2022-04 → 2026-08) finds the rest-of-day → last-half-hour slope flat overall and every year (t 0.6), positive only on dealer short-gamma sessions (~15% of days) ([FirmTape](https://dev.to/firmtape/intraday-momentum-is-dead-in-the-0dte-era-we-measured-it-on-1085-spx-sessions-43g0)). Dim, Eraker & Vilkov: positive market-maker gamma strengthens intraday reversal, negative strengthens momentum, effects dissipating within about an hour ([SSRN](https://papers.ssrn.com/sol3/Delivery.cfm/4692190.pdf?abstractid=4692190), [QuantPedia](https://quantpedia.com/do-sp500-0dtes-options-increase-market-volatility/)); a Cboe-hosted study argues short 0DTE gamma raises intraday vol, concentrated morning/midday ([Cboe](https://cdn.cboe.com/resources/education/research_publications/gammasqueezes.pdf)). D647's B1 gross by year (positive 2017–2020 and 2024, negative 2021–2023 and 2025) is consistent with continuation weakening after 2021 *(reasoning)*. Implication: a 2016–2025 walk-forward's CONT payoff matrix is probably optimistic for the vault years; the A4 dealer-gamma agent is the natural conditioner for the CONT clock.

#### Ranked recommendation

1. **EV rule with point-in-time payoffs in dollars** (point 2). Structural: the only change that makes CONT tradable at all and multiplies the trade count enough to be testable. Expected per-trade net small positive (+1 to +3 bp) at S-A's discrimination; larger only if Phase 4 lifts CONT's AUC.
2. **State-specific exits** (point 3): no price stop and a gap-fill target for FADE; 1.5σ_h stop for CONT. Theory and the ORB replications agree on direction; the size is uncertain.
3. **State-specific entry times** (point 7): FADE at 09:45, CONT at 10:30 with a hold to the close. Largest expected effect for CONT, weakest external evidence post-2022.

All three were conceived after D646/D647 on the in-sample; they belong in one v2 pre-registration (one family, Holm across cells), tested once on the vault or by forward recording, with the component line (net and gross Sharpe and Sortino, trimmed means, dollar cost at one micro) reported whatever the verdict.

<!-- report C -->
### Group C report: liquidity-scaled agent pressures and the 2022 break

Read for context only: D645, D647, and OPENING_AGENT_STATE_PREREG.md §4. No data files read, nothing run, nothing edited. Everything under "reasoning" is mine, not sourced.

#### 5. Scale each agent's pressure by the liquidity it meets

**What the research says.**
- *Square-root law.* A metaorder of size Q in a market trading V per day moves price by roughly Y·σ·√(Q/V), nearly independent of schedule while participation is modest; the recent unifying framework adds time decay after execution ([Bouchaud](https://bouchaud.substack.com/p/the-square-root-law-of-market-impact); [Maitrier & Bouchaud 2025](https://arxiv.org/abs/2506.07711)). Kyle-Obizhaeva invariance gives the same denominators from dimensional analysis: dollar volume and return variance are the only market quantities that enter ([Kyle & Obizhaeva 2016](https://pages.nes.ru/aobizhaeva/Kyle_Obizhaeva_Invariance.pdf)). Both say the natural unit of a flow is participation (Q/V) times σ, not Q.
- *Predictable flows are absorbed, concavely.* Bessembinder et al. (JFE 2016) find narrower spreads, deeper books and better resiliency on the predictable USO roll days, i.e. sunshine trading, no predation ([paper](https://www.ou.edu/content/dam/price/Finance/CFS/paper/pdf/Bessembinder%20Paper.pdf)). Brøgger (JBF 2021) on leveraged VIX ETPs: larger and more predictable flows have *smaller* price-impact coefficients, and front-running them is unprofitable after cost ([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3497537)). This matches your leveraged-commodity finding that the biggest funds showed no effect and only ~⅓ of naive impact appeared.
- *Dealer gamma.* Barbon & Buraschi define the explanatory variable as dealers' **dollar gamma imbalance divided by ADV of the underlying**, and show intraday momentum (reversal) comes from negative (positive) imbalance *interacted with illiquidity* ([Gamma Fragility](https://www.abarbon.com/assets/Barbon_Buraschi_2021_Gamma_Fragility.pdf)). Baltussen, Da, Lammers & Martens (JFE 2021) tie last-30-minute momentum across 60+ futures to gamma and leveraged-ETF hedging, with reversal over following days ([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3760365)).
- *Leveraged ETFs / vol-control.* Barbon, Beckmeyer, Buraschi & Moerke: a 1-sd LETF rebalancing flow moves the last half-hour by ~4× its mean return, LETF flow hits 2-4× harder than same-size option delta flow, but the LETF effect has *decayed over time* ([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3925725)). Ivanov & Lenkey (JFM 2018) find that once capital flows are netted the LETF effect is economically insignificant ([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2504012)). Practitioner desks normalise by window volume: BofA quotes NQ rebalancing as roughly a quarter of notional traded in the last five minutes ([search summary](https://macrogrisa.substack.com/p/monitoring-systematic-flows-and-investor)); Goldman/Nomura publish CTA and vol-control flows in $bn with no liquidity denominator, which is exactly the weakness.
- *CTA flow.* No study isolates CTA impact on ES at the morning horizon. The one microstructural paper on short-term trend says the post-2008 feedback loop died on small-tick contracts because HFT market makers withdraw ahead of predictable directional flow ([arXiv 2607.01550](https://arxiv.org/abs/2607.01550)); ES is a large-tick contract, which is the one place that paper says the loop survives.

**Reasoning applied to this study.** The standardised z (O-D2) folds an unknown AUM into the scale, which is fine, but it also drops the *state-dependent* part of impact: the same ΔE in a thin week moves more. Which agents need it, in order:
1. **A4** — the only agent with a research-standard denominator (Barbon-Buraschi: $gamma / ADV). Its pressure is already in dollars (G × gap), so divide by trailing dollar volume.
2. **A7** — already a same-window measurement; its natural unit is a participation rate, signed large-lot volume over total window volume.
3. **A2/A3** — daily-scale flows, mostly executed across the day and at the close (Baltussen et al.), so the *morning* effect is second-order; a √ scaling by trailing dollar volume is the right functional form but I expect little gain.
4. **A1** — a distance, not a size; the liquidity it meets is the opening-window depth. Weak case.
5. **A5, A6** — not flows (A5 is a realised reaction, A6 an arbitrage bound). Leave unscaled.

**Pitfall that matters most here:** dividing by *same-day* 09:30→t0 volume is point-in-time but confounded — a heavy opening is itself a trend-day tell (`vol_z` is already a feature), so the participation denominator shrinks the pressure precisely on the days the classifier should fire. Use a trailing denominator as primary and same-day participation as a declared secondary. Other pitfalls: ADV inflated in roll weeks (sum the root's expiries, do not use front-month only); the σ used for scaling must be through t−1; denominators need the same 250-session standardisation window as the numerator or the z is not comparable across eras.

**Pre-registrable specification (point-in-time inputs only).**
- `DV_w(t) = mean over sessions t−20…t−1 of dollar volume traded 09:30→t0` (window-matched liquidity).
- `A4: P4* = −G(t−1) × (open − prior_close) / DV_w(t)`; then z over 250 sessions as now.
- `A7: P7* = Σ signed large-lot volume 09:30→t0 / Σ all volume 09:30→t0` (primary); secondary divides by `DV_w`.
- `A2, A3: P* = sign(ΔE) × σ20 × sqrt(|ΔE| / DV_20)` with DV_20 the trailing 20-day RTH dollar volume; the AUM constant is absorbed by the z.
- One contrast per agent: scaled vs the registered raw z, scored on CONT AUC and log loss with the Holm budget declared, on the vault or forward data only.

**Expected effect.** Small. Rescaling cannot create information a raw pressure lacks; D647's CONT AUC is 0.506 with observables, and Phase 4 has not yet examined any agent against the labels. If the raw z's carry signal, liquidity scaling plausibly adds 0.01–0.02 AUC (my estimate, from the ⅓ realised-impact and concavity results: it mainly fixes scale, not sign). If raw shows nothing, scaling will not rescue it. Contested: Ivanov-Lenkey vs Barbon et al. on whether mechanical flows move prices at all once offsets are netted.

#### 6. Allow for the 2022 break

**What the research says.**
- *Dates (calendar, not results).* SPX Tuesday expiries 2022-04-18, Thursday 2022-05-11, making every weekday an expiry ([Cboe](https://ir.cboe.com/news/news-details/2022/Cboe-to-Add-Tuesday-and-Thursday-Expirations-for-SPX-Weeklys-Options-04-13-2022/default.aspx)); ES Tue/Thu options 2022-04-25 ([CME](https://www.cmegroup.com/media-room/press-releases/2022/3/31/cme_group_to_launche-minisp500tuesdayandthursdayweeklyoptionsona.html)); NQ Tue/Thu options 2022-10-03 ([CME](https://www.cmegroup.com/media-room/press-releases/2022/9/08/cme_group_to_launche-mininasdaq-100tuesdayandthursdayweeklyoptio.html)); micro ES/NQ M-Th options 2023-02-13. 0DTE share of SPX volume: ~5% (2016), 45% (2023), 47% (2024), 59% (2025) ([Cboe](https://www.cboe.com/insights/posts/spx-0-dte-options-jump-to-record-62-share-in-august/)). So the "break" is a ramp from 2022, not a step.
- *Volatility, both sides.* Brogaard, Han & Won: a 1-sd rise in 0DTE volume raises volatility ~9% of its mean, retail-driven, surviving a gamma control ([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4426358)). Adams, Dim, Eraker, Fontaine, Ornthanalai & Vilkov: 0DTE presence *lowers* index volatility by ~60 bp annualised; market-maker net gamma is positive on average and higher gamma predicts stronger order-flow reversal and negative high-frequency momentum over ~1-hour windows; the channel is longer-dated positions rolling down to 0DTE, not same-day trading ([Quantpedia summary](https://quantpedia.com/do-sp500-0dtes-options-increase-market-volatility/); [Cboe research](https://cdn.cboe.com/resources/education/research_publications/gammasqueezes.pdf)). Both magnitudes are small against regime-level vol swings; the disagreement is on sign, and the identification (Tue/Thu before May 2022 as the control) is exactly the calendar above.
- *Practitioner view.* SpotGamma: pre-bell 0DTE orders are hedged at once, so the day's largest move is often the first 15-30 minutes, followed by mean reversion between call/put walls in positive gamma ([SpotGamma](https://spotgamma.com/0dte/)). Unaudited, but consistent with Dim et al.'s reversal result.
- *Break handling.* Pesaran, Pick & Pranovich: optimal weights are exponential under continuous drift and piecewise-constant across regimes under a discrete break ([paper](https://files.econ.cam.ac.uk/people-files/mhp1/fp13/PPP-Revision-1.pdf)); Pesaran-Timmermann recommend combining windows when the break is uncertain ([Monash summary](https://www.monash.edu/business/econometrics-and-business-statistics/research/publications/ebs/forecasting_under_strucural_break_uncertainty.pdf)). Andrews sup-Wald / Bai-Perron locate unknown dates ([Casini & Perron](https://arxiv.org/pdf/1805.03807)) — useful as a *diagnostic*, never as the way to pick the date.

**Reasoning applied.** Two channels, opposite signs. (a) Dim et al.'s positive average dealer gamma plus stronger reversal implies fewer CONT and more FADE/RANGE after 2022; the label frequencies by year that §5.3 already requires will show it directly. (b) **A4 is the agent the break damages:** it is built from t−1 open interest, and 0DTE gamma is listed and traded the same day, so post-2022 A4 measures a shrinking fraction of true dealer gamma. The sign assumption (customers long puts, short calls) is also least safe for retail 0DTE flow, which Brogaard et al. find is speculative. Note D647's B1-by-year pattern (gross positive 2017-2020 and 2024, negative 2021-2023 and 2025) does not fit a clean 2022 step; so I would not expect the era dummy alone to be decisive.

**Pitfalls.** Choosing the date after seeing per-year results (declare it from the calendar above); the post-break sample — from 2023 after the walk-forward's training window, roughly 1,500 session-markets and ~225 CONT events, AUC SE ≈ 0.02, so only a ≥0.05 AUC shift is resolvable and anything smaller is UNRESOLVED per D373's rule; era interactions on every agent burn the parameter budget.

**Pre-registrable specification.**
- Break dates: ES `2022-05-11`, NQ `2022-10-03` (the first session on which every weekday carries an index expiry for that market). Sensitivity ±1 quarter reported, never selected.
- Handling rule (primary): one indicator `post × z4` only; all other coefficients pooled. Secondary: training weights with a declared half-life of 500 sessions (Pesaran-Pick-Pranovich's continuous-break case), no interaction.
- Guards: label frequencies per market, year and era reported before fitting; the post-era CONT count and its AUC SE printed by the runner; the era contrast scored only on the vault or forward data.

**Expected effect.** Direction uncertain: 0DTE plausibly *hurts* CONT detection through A4's mis-measurement and a lower CONT base rate, while making FADE more predictable. Size: small and probably unresolvable in-sample; the honest deliverable is a declared date and a power statement.

#### Ranked recommendation
1. Run Phase 4 as registered (raw z's) before any of this; no scaling creates information.
2. Pre-register A4 as $gamma × gap / trailing window dollar volume and A7 as a participation rate — the two with research-standard denominators and no same-day confound.
3. Pre-register the per-market calendar break with one `post × z4` interaction, plus the era power computation up front.
4. Only if 2 shows signal: √-participation scaling of A2/A3.
5. Half-life weighting as robustness, not primary.
