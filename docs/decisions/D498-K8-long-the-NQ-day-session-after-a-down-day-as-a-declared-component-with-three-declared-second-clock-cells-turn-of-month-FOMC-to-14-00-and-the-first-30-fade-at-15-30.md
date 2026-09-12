# D498 — K8: long the NQ day session after a down day, as a declared component; with three declared second-clock cells (turn-of-month, FOMC to 14:00, the first-30 fade at 15:30)

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file.
In-sample **2016-01-04 → 2023-12-29** on the D462 one-minute regular-hours fixtures (full
sessions), intraday only; **2024+ unread** (the runner raises past 2023; the forward read is a
separate guarded command and is not run under this record). D498 taken after D496 and D497 were taken by the other session within minutes of my checks (recorded, not resolved); it showed free
in `git log --all` from the other session.

## 0. Why, and what has been seen

The principal needs at least weekly trades. D495's one pick (fade after a top-decile down day,
14 trades a year) failed the family bar because its **other side** — long NQ's day session after
*any* down day — was +10.2 bp on 761 days. That is a state with a 38% base rate, a per-trade
mean seven times the cost, and seven times the pick's sample. **It was seen in D495 as a
control, not scored; that selection is stated, and it is why the in-sample line below enters
the ledger as PROVISIONAL at best and the 2024+ read is the test.** Three further cells are
declared for a second clock, each with a mechanism on the record: the turn-of-month effect, the
pre-FOMC drift, and the first-half-hour → last-half-hour reversal D487 measured (ES −0.10,
−4.3 SE, 2020–2022).

## 1. The cells (declared; nothing added after the numbers)

All: entry at the stated bar's open plus one tick in the trade direction, exit at the stated
bar's close, one MES / one MNQ, $3 a round trip. NQ is the candidate root, ES the check root.
Sides as stated; no other side is traded.

- **K8 (the component candidate):** **long** the day session (09:30 → 15:59) when yesterday's
  day-session return R_{t−1} < 0 (the same R as D495: 09:30 open → 15:59 close of the previous
  full session). Its other side is the day session after an up day, reported.
- **E1 — turn-of-month:** **long** the day session on the last trading day of a month and the
  first three trading days of the next (four sessions a month). Other side: all other days.
- **E2 — FOMC decision day, to the announcement:** **long** 09:30 → the 13:59 bar's close (the
  14:00 print) on scheduled FOMC decision days (the second day of each meeting, from the Fed's
  calendars, listed in the runner; the 2020-03-03 and 2020-03-15 unscheduled decisions
  excluded, one was a Sunday). Other side: the same 09:30 → 14:00 window on all other days.
- **E3 — the first-30 fade:** at 15:30, enter **opposite** to the sign of the first-30 return
  (09:30 open → 09:59 close), exit at the 15:59 close. Both signs traded as one cell (the
  statistic is the return in the trade direction); the other side is the same window with the
  first-30 sign followed, i.e. the negative of the cell.

## 2. Statistics

Per cell and root: trades and share of sessions; gross mean, median, 1%-trimmed mean, in $ and
bp; net mean; hit; payoff; skew; MAE p50 / p95 / worst and days below −2% of $50k at one micro;
**the net Sharpe of the daily series on the session calendar with its block-bootstrap SE**; by
year; sub-periods 2016–2020 / 2021–2023; the other side in the trade direction; **ρ of the
daily series with K8 and with the ungated NQ day session** (C-b).

## 3. Nulls and bars

- **N1** exact rotation of each cell's state series against the day returns (all offsets ≥ 2).
- **N2** the family maximum of the difference-between-sides z under a common rotation offset
  over the eight cell-roots (four cells × two roots).
- **N3** sign flip for the Sharpe.
- **K8's bar:** the ledger's C-a (net Sharpe > 0.5 at one MNQ) and C-c, C-d on the in-sample
  line → **PROVISIONAL entry** (the selection in §0 is the reason it cannot be full); below C-a
  → recorded, not entered. **Forward rule (2024-01-02 → 2026-09-09, on the principal's word, a
  separate RESULT):** FULL if the forward gross mean > 0, the forward net Sharpe > 0 and the
  difference against after-up days has z ≥ 1; REMOVED if the forward net Sharpe < −0.3 or the
  difference is negative; otherwise stays PROVISIONAL.
- **E1–E3's bar:** PROCEED if own N1 cleared, z above the family p95 and net Sharpe > 0.3; PICK
  if N1 and the Sharpe without the family bar; else closed.

## 4. Predictions

- **X-a** K8 NQ: 45–50% of sessions, gross **+9 to +12 bp** (≈ $18–24), hit 55–58%, **net Sharpe
  +0.40 to +0.60** (C-a marginal), positive in ≥ 6 of 8 years and both sub-periods; ES +4 to +6
  bp, Sharpe +0.15 to +0.35. ρ(K8, ungated NQ day session) **0.6–0.7**.
- **X-b** E1 TOM on NQ: **+8 to +15 bp** a day on ≈ 48 days a year, above N1, z **1.5–2.5**
  (marginal against the family), Sharpe +0.3 to +0.5 as a component; ES smaller.
- **X-c** E2 FOMC to 14:00: **+8 to +20 bp** on ≈ 64 days, SE ≈ 15, inside N1 or marginal —
  the pre-FOMC drift is smaller after 2015 than in the published sample.
- **X-d** E3 first-30 fade: **+3 to +6 bp** a trade on every session, positive pooled, driven
  by 2020–2022 and **negative in 2016–2017**; clears N1 pooled; **net Sharpe +0.1 to +0.4** (the
  last-30 σ is small against $3); not above the family bar.
- **X-e** ρ(E1, K8), ρ(E2, K8), ρ(E3, K8) all **< 0.3** (different clocks); ρ(E3, ungated day
  session) **< 0.2**.
- **X-f** Runtime under 3 min.

## 5. Files

This record · `scripts/run_d498_k8_and_second_clocks.py` (`--run`, `--forward --principals-word`,
`--selftest`) · `data/d498_k8_second_clocks.json` · trade files · RESULT (in-sample) · RESULT
(forward, separate, if run).
