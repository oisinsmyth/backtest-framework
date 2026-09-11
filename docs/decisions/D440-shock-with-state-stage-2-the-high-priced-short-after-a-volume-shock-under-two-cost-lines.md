# D440 — shock-with-state, stage 2: the high-priced short after a volume shock, under two cost lines

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file. In-sample
on the mining fixture; **no holdout is read**. D400–D439 used, D407–D410 and D390–D399 reserved.

## 1. What is left of the construction, and why

D437 found the volume shock adds to its state in two of four components; D438 found only **B —
a 3× volume bar in the top price tercile, sold short** — carries that increment at every horizon
(+13 at 5 bars to +37 at 60, above its state-matched control's p95 throughout), and that the
increment lives in the widest third of B's names, where the modelled round trip is 84 bp. **A, C,
D are dropped; the drop is disclosed as post-hoc** (A never cleared its control on any horizon;
C and D showed no increment). D439 measured passive execution on the 15m fixtures: a limit at the
open filled on a 5 bp trade-through fills 92% of the time, the chase on the unfilled 8% costs 9 bp
per order, and net capture is 0.66 of the modelled half-spread (0.72 in the wide tercile, 0.57
on shock days) — and it found the modelled half-spread on liquid names is a range, not a quote.

## 2. The object

`rv_x3` (VOL_t ≥ 3 × ADV20) ∧ `price_hi` at the close of `t−1`, placed at `t`, filled at `t`'s
open — D436's B mask (12,597 events, asserted). **Short.** Every event, one position per name,
market-hedged, D345's kernel through `run_d359` (the D435–D438 path). **Cap 20 primary; cap 40
reported** (D438: net positive crossed only at 40–60, at 1.4 SE). Equal weight (the kernel's).

## 3. The two cost lines, both printed on every table

- **Crossed (the incumbent):** `trade_block`'s 2c under PUB + IBKR commission + D337's `gc_htb`
  borrow. This is the line the repo gates on.
- **Passive at the open (D439's assumption, labelled):** per trade, **2c PUB × (1 − 0.66) + 9 bp
  chase + borrow** — the measured capture fraction on the 15m fixtures' names (17–55 bp/side
  modelled), applied to B's names (D438: 33 / 53 / 84 bp round trips by tercile, i.e. inside
  that range). Per bar: `cost2 × 0.34 + 9 × turnover + borrow × turnover`. **It is an assumption
  in two ways, both stated: the fraction was measured on other names, and the modelled half-
  spread it discounts may be a range rather than a quote (D439 §2) — in which case the true
  crossed cost is lower and the passive line is closer to the truth than the incumbent.**

## 4. Measured

Per trade: gross, both nets, median, hold, by year, era halves, the spread tercile split
(D438's cuts, both nets), the calendar split (D437: on/off the earnings cadence). The book:
deployed gross, both cost lines, both nets per bar, monthly block-bootstrap SEs, Sharpe under
each line, by year; concentration (names to half the P&L, top-1% share). **Nulls (D437's):**
state-matched random events (same state, same daily count, non-shock cells, 100 draws) for the
increment; time rotation (100 draws). `[P2]` the cap-20 per-trade gross equals D438's B cell to
1e-9; `[F]` the events are D436's.

## 5. The bar

- **T1** per-trade gross above the state-matched control's p95 (D373's margin) — the increment.
- **T2** the book's net per bar under the **crossed** line > 0 by 2 SE — the incumbent verdict.
- **T3** the book's net per bar under the **passive** line > 0 by 2 SE.
- **T4** the second half of the sample (2018-06 onward, the era split) net under the passive line
  > 0 by 2 SE.
- **T5** gross above the time-rotation p95.

**Candidate for the holdout reads (holdout 1 then holdout 2, once each, both unseen by this
line): T1 ∧ T3 ∧ T4 ∧ T5.** T2 is reported and not required: it is known to fail at cap 20
(D437: B's deployed 2-crossing net −0.38) and the candidate condition rests, explicitly, on the
D439 assumption — a holdout read would test the *signal* on new names; the cost question stays
an assumption until a quote is pulled. **Written here so it cannot be softened later.**

## 6. Predictions (computed from D437/D438/D439; MODERATE)

- **X-a** per trade at cap 20: gross **+38.8** (`[P2]`); crossed net **−18 ± 3**; passive net
  **+7 ± 3** (2c 52.2 × 0.34 = 17.7, + 9 chase, + 4.9 borrow = 31.6). At cap 40: gross +68.9,
  crossed +7, passive **+37**.
- **X-b** the book at cap 20: gross **+2.24/bar** (D437), crossed net **−0.4 ± 0.6**, passive net
  **+0.6 ± 0.6 — T3 a coin, more likely to fail at 2 SE than pass**; at cap 40 passive net
  **+1.0 ± 0.6**, about 1.7 SE.
- **X-c** T1 passes (+21 over p95 +31 at cap 20 — D438), T5 passes.
- **X-d** era 2 stronger than era 1 (D437's by-year: 2021 +183, 2016 +103): passive net in the
  second half **+0.8 to +1.5/bar**; T4 near 2 SE.
- **X-e** the wide tercile carries the increment (+34) and, under the passive line, nets
  **+40 to +60 per trade**; the narrow tercile nets negative under both lines.
- **X-f** on-cadence events +41 vs off +38 (D437) — the calendar split is flat for B; concentration:
  16–20 names to half the P&L, top-1% share 100% ± 20 (D438's cap-20 figure, 108%).

X-b is the study. If the passive line nets positive at 2 SE, the object goes to the holdouts
carrying an execution assumption that only a quote pull can retire.

## 7. Not in scope

The holdouts (this record does not open them); A, C, D; any new state; sizing beyond equal
weight. Fortieth look by object; the second forward-return look at this construction.
