# D473 — COMPONENT candidate: the overnight leg after a negative overnight leg. One declared construction, two exits, the in-sample component line, the predictions, and the forward read declared

**Pre-registration of a component record. Committed before the runner exists (R8).** In-sample
result in a separate file; **the forward read is a separate command in the same runner that is
NOT run under this record** — it reads the reserved 2024+ slices and runs only on the
principal's word, under a RESULT of its own. D473 taken after `ls docs/decisions` and
`git log --all` on both worktrees showed D472 as the highest number.

## 0. Provenance (C-e), stated so the selection is on the record

Found in D470 as one of 32 stage-0 cells (the principal's continuation hypothesis, sign
reversed); fails D470's in-sample family maximum in dollars and, in D472, on the z and Sharpe
scales (2.78 vs p95 3.13; +0.70 vs +0.79 on ES-W2) — **eight years cannot beat the best of
eight gates on a drifting series**; replicates on SPY and IWM cash 2010–2015 (gap after a down
gap +5.5 / +7.7 bp vs ≈ 0, 1.9 / 2.0 SE, both single nulls cleared, 11 of 12 symbol-years) and
on SPY cash 2016–2023 (+6.1 vs −0.5, 1.9 SE). The principal chose to take it to a component
record on the replication, against the in-sample family failure; both stand in the ledger row.
**No in-sample sharpening between D472 and this record** (D472's exchange: every variant is
another cell, and the forward slice is one-shot).

## 1. The construction (fixed here; nothing chosen after this commit)

**K7 — long the overnight leg on nights that follow a negative overnight leg.**

- **Instrument:** NQ, one MNQ ($2/pt), $3 a round trip — chosen on cost share, a known number
  (in-sample $3 is 23% of NQ's gated mean against 28% on ES). **ES (one MES) is reported
  identically as the check root**; the two are one construction (ρ 0.92) and only NQ is the
  candidate.
- **Entry:** the 18:00 open (`h18_o`) of a same-front session (D449's roll rule).
- **Gate:** the overnight leg into the entry day, `h08_c / h18_o − 1` of the previous session
  row, **≤ 0** (D470's G-B, down side; read at the previous session, so a Friday leg gates a
  Sunday-evening entry). Nights whose prior leg is undefined (the previous session was a roll
  night or lacked either print) are not traded.
- **Exit, primary:** the 09:00 print (`h08_c`), the window D470 and D472 tested.
- **Exit, secondary (declared, multiplicity two):** the 09:30 open of the same session from
  `fut_index_sessions` (`p0930`), the print the cash replication ends on. Reported beside the
  primary in-sample and forward; **the primary is the candidate**.
- **Size unit and cost** per the ledger; daily P&L in dollars on the root's session calendar,
  zero on untraded nights.

## 2. The in-sample component line (2016-01-04 → 2023-12-29, computed by the runner)

Net and gross Sharpe with monthly block-bootstrap SE, mean and σ per traded night, hit, skew,
worst night, annual net, by year; correlation with K1 (ES full-session hold, D466) and with the
ungated NQ overnight leg; the single-cell nulls N1 (exact rotation) and N2 (run-length) as
D470; the standard's checks C-a..C-d with the family failure recorded against C-a's
multiplicity. Also, **as in-sample facts to be predicted forward, not as filters:**

- **Dose–response:** gated mean by the size of the prior leg (0 to −25 bp, −25 to −50, −50 to
  −100, below −100), with n and SE per bin.
- **The tail:** the ten worst gated nights named; the gated component's worst night, its 1% and
  0.1% night quantiles, and the share of nights below −2% of a $50k account at one micro (P3
  at minimum size).
- **Regime:** the gated-minus-other difference by calendar year and by trailing-21-day σ
  tercile, reported (D470 read the futures gap as 2020–2022; the cash gap was spread across
  years; the forward read tests which).

## 3. The forward read (declared; not run here)

**Slices:** NQ and ES futures 2024-01-02 → 2026-09-09 from the D467 table (and `p0930` for the
secondary exit); SPY and IWM cash 2024-01-02 → 2026-08-26 from the equity 15m fixture. Roughly
190 gated futures nights and 200 gated cash nights per symbol.

**Statistics:** the gated mean, the other side, their difference with SE, on each slice; the
component's forward net Sharpe at one MNQ; the dose–response bins; the worst forward night; the
pooled difference z across NQ futures and SPY cash (inverse-variance weights, the two being
different instruments on overlapping nights — reported, and the futures-only z beside it).

**Promotion rule (the ledger's PROVISIONAL mechanism, applied forward):**

- **PROVISIONAL entry** if the forward gated-minus-other difference is **positive on NQ futures
  AND on SPY cash**, and the **pooled z ≥ 1.5**, and the forward gated net Sharpe on NQ is
  **> 0**.
- **Full entry** if additionally the futures-only difference z ≥ 2, or the pooled z ≥ 2.5.
- **Removed** if the futures difference is negative, or the pooled z < 0.5, or the forward
  gated net Sharpe on NQ is below −0.3.
- Between those: stays a pick, with the forward numbers recorded; no re-read.

**Runner guard:** `--forward` refuses to run without `--principals-word`, prints the slices it is
about to read, and writes its own artefact; the in-sample command never touches 2024+.

## 4. Predictions

- **X-a (in-sample line)** NQ K7: gated net Sharpe **+0.62 (SE ≈ 0.25)**, gross mean **+$13.3**,
  σ ≈ $172, 887 nights (D470's numbers reproduce exactly); ES +0.70. Secondary exit (09:30):
  gated mean **higher by 10–40%** and σ higher by 10–20% (the 09:00–09:30 leg adds drift and
  variance); Sharpe within ±0.1 of the primary.
- **X-b (dose–response, in-sample)** the gated mean **rises monotonically** with the size of the
  prior fall across the four bins; the below-−100 bp bin carries at least twice the 0-to-−25 bin
  per night, on fewer than 15% of gated nights.
- **X-c (tail)** worst gated night on one MNQ between **−$800 and −$1,300** (2020-03); nights
  below −2% of the account at one micro: **0**; 1% quantile between −$350 and −$500.
- **X-d (correlation)** ρ(K7, K1) **0.35–0.55** (K7 is a subset of the nights and a part of the
  session); ρ(K7, ungated NQ overnight leg) **0.6–0.75**.
- **X-e (forward, written now so the read is checkable)** NQ gated mean **+$6 to +$16**, other
  side **−$6 to +$6**; futures-only z **0.8–2.0**; SPY cash gap after a down gap **+3 to +8 bp**;
  pooled z **1.3–2.5**; dose–response monotone in at least three of four bins; worst forward
  night on one MNQ **−$400 to −$900**. Under the rule: **PROVISIONAL more likely than not;
  full entry unlikely on this many nights.**
- **X-f** in-sample runtime under 3 min; forward under 2 min.

## 5. Files

This record · `scripts/run_d473_downleg_component.py` (`--insample`, `--forward --principals-word`,
`--selftest`) · `data/d473_downleg_insample.json` · later `data/d473_downleg_forward.json` ·
RESULT (in-sample) · RESULT (forward, separate).
