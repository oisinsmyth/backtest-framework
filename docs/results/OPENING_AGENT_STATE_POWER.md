# Opening agent-state model: POWER (before any stage runs)

*`scripts/power_opening.py` → `data/opening/power.json`. OPENING_AGENT_STATE_PREREG.md §10 and ledger 9A.2, on
the walk-forward's out-of-sample sessions (§11 trains on 252 first). It reads D644's labels and the DISPERSION
of the raw 60-minute move from the t0+1 close. No mean return is computed, and no move is signed by any state,
label or agent.*

## The samples (t0 = 10:00; 09:45 in brackets)

- Out-of-sample sessions: 2,030 (2,030); classified days ES 2,006, NQ 2,026.
- **Same-day ES/NQ agreement of the labels:** ρ = 0.424 (0.431), so the pooled n_eff is **2,831** (2,807). The plan assumed 2,700–2,900 on the full sample before the vault.
- **Same-day correlation of the 60-minute moves:** ρ = 0.911 (0.897); n_eff **2,125** (2,140).
- σ of the 60-minute move: ES 36.0 bp, NQ 47.8 bp. The micro round trip is ES 3.27 bp, NQ 2.31 bp (0.066 σ pooled).

## Minimum detectable effects (t0 = 10:00)

| test | n_eff | SE | MDE t = 2 | 80% power | Holm across 2 t0, 80% | programme α 0.005, 80% | plan (t = 2) |
|---|---:|---:|---:|---:|---:|---:|---|
| H-O1 accuracy lift (binomial, base 0.617) | 2,831 | 0.0091 | 0.0183 | 0.0256 | 0.0282 | 0.0333 | — |
| H-O1, the deposit's 1/√n_eff | 2,831 | 0.0188 | 0.0376 | 0.0526 | 0.0579 | 0.0686 | 0.04 |
| H-O2 decision value, all days | 2,125 | 0.0217 | 0.0434 σ | 0.0607 σ | 0.0669 σ | 0.0792 σ | 0.04 σ |
| the policy's traded days (35%) | 744 | 0.0367 | 0.0733 σ | 0.1027 σ | 0.1130 σ | 0.1338 σ | 0.065 σ |
| H-O6, per agent (a correlation) | 2,831 | 0.0188 | 0.0376 | 0.0526 | 0.0579 | 0.0686 | 0.04 |

## In basis points, against the cost

- **H-O2 (per day, all days):** MDE 1.84 bp at t = 2, 3.35 bp at the programme's α with 80% power, against a pooled micro round trip of 2.79 bp. Class at t = 2: **individually_testable**; at the programme's bar: **underpowered**.
- **Per traded day (35%):** MDE 3.10 bp at t = 2, 5.66 bp at the programme's bar. Class at t = 2 against the cost: **underpowered**.

## The plausible-effect statement (ledger 9A.2)

- **H-O2 and the traded days.** The floor that matters is the cost. A state policy whose edge per traded day is
  below one micro round trip cannot be net-positive, whatever its t. **The traded-days row is the one to read
  against it**: H-O2's all-days statistic averages in the no-trade days (0 by §9), so its bp MDE is per calendar
  day, not per trade.
- **H-O1.** There is no in-repository prior for day-type classification lift at the open. The MDE is stated
  against the deposit's plan (0.04 at t = 2) and the 61.7% base rate (RANGE with REV merged,
  O-D4, which also makes the base rate harder to beat). The prior reads (OA-A2) point to
  small effects: D531 (the opening-range breakout loses to the base rate), D463 (intraday momentum is a third
  of its published size), D581 (dealer gamma orders nothing at the close).
- **H-O6.** One correlation per agent. The MDE applies to each agent's own signature.
- **Track 3 (§12):** the consistency route is likely unless the edge exceeds ~0.115 σ
  per trade. The Track 1 estimate decides which route after Phase 5.
