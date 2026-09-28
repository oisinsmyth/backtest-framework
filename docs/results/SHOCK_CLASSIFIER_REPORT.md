# Shock classifier: REPORT (deposit §11)

**Verdict: GATE 1 FAILED on all four instruments, 2026-09-28.** The full record is
[D643](../decisions/D643-RESULT-shock-classifier-fails-gate-1-on-all-four.md). The numbers are in
`data/shock/phase3_signal.json`, the 96 configurations evaluated are in `data/shock/trials.csv`, and the event-study
figure is [`data/shock/phase3_event_study.svg`](../../data/shock/phase3_event_study.svg). The pre-registration is
[D642](../decisions/D642-PRE-REG-shock-classifier-signal-frame-h1-h4.md) and the power step is
[SHOCK_CLASSIFIER_POWER.md](SHOCK_CLASSIFIER_POWER.md).

## The evidence

- **GC, the one powered cell, is a clean null.** The INFO − LIQ divergence in the 30-minute move is +0.28 bp (t 0.21;
  95% interval −2.4 to +3.0 bp) against a 4.5 bp cost. Its LIQ class has 304 shocks spread over every year.
- **NQ, ES and CL are inconclusive, as POWER said they would be,** and what they show points nowhere:
  - NQ: Δ −0.8 bp;
  - ES: LIQ *continues* (Δ −16.5 bp, and the fade still loses ex-2020);
  - CL: Δ +19.4 bp, at the 86th percentile of its own label placebo, carried by 23 shocks in the 2020 crash.
- **Neither class differs from the unconditional shock** on any instrument (SC-A2). The classification adds nothing to
  what D528/D499 already measured.
- **H3's label placebo and H4's dose-response fail everywhere.**
- **INFO's curve is flat to ±1.2 bp for an hour.** INFO's trade grosses $0.14–$0.74 against a $4.57–$6.93 micro round
  trip, and every component line is negative or empty (the best, CL LIQ, is net Sharpe +0.04 on 4 trades a year).

## What was learned

A peer-confirmation ratio on one-minute bars does not separate continuation from reversion. On the index and energy
markets the LIQ label is mostly a picture of the 2020 crash: 1.2–2.3% of shocks, and nearly none after 2021. The
deposit's aggressor-flow feature was never available in-sample (SC-A3). Whether a flow-signed classifier separates the
classes is not answered here, and nothing in this run argues for buying the data to find out.
