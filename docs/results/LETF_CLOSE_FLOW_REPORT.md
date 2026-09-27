# LETF close-flow model: REPORT (deposit §11)

**Verdict: KILLED at Gate 1, 2026-09-27.** The full record is
[D640](../decisions/D640-RESULT-letf-close-flow-killed-by-its-own-11am-placebo.md). The numbers are in
`data/letf/letf_close_flow_signal.json`; the 71 configurations evaluated are in `data/letf/trials.csv`.

## The evidence

- **H1 passes in two primary cells:** NQ 14:30 (+5.6 bp against a 1.6 bp cost, HAC t 2.54, Holm p 0.028) and
  NQ 15:00 (+5.8 bp, t 2.84, Holm p 0.014). NQ 15:30 and all three ES cells fail.
- **H4 kills them.** The identical rule at 11:00 → 12:00 is significant on NQ (+3.3 bp, t 2.08 against |t| < 2).
  That is the deposit's own kill condition: generic late-day momentum, not LETF flow.
- **The slice no prior study read, 2024-01 → 2025-02, is flat:** −0.2, +0.9 and −1.8 bp at 14:30, 15:00 and 15:30 on
  NQ. No ES day activates there.
- **H3: no AUM scaling.** The NDX set's L(L−1)A grew elevenfold, 2016 → 2025, and the effect did not grow with it.
- **LETF-A7: against the model's own predicted impact**, the NQ moves are about half the claim in 2016–2023, and at
  15:30 significantly below it (a powered null).

## What was learned

The leveraged-ETF rebalance flow is real and arrives at the close (D530's volume hump), but its predicted price
effect is not separable from return-of-day continuation. That continuation also shows up at 11:00, belongs to
2016–2023, and is gone after. ES cannot be tested at the deposit's bar: the S&P funds' flow activates on 3% of days.
The v2 overlays (deposit §14) have no v1 effect to build on.
