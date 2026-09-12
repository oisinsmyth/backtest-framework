# D463 — market intraday momentum, the last 30 minutes, on ES / NQ / YM / RTY: the lane-13 falsification criteria, and hurdle P's P3, P4 and P5 computed for the first time

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file. **The first
forward-return look at a prop candidate on the futures themselves.** In-sample **2010-06-06 to
2023-12-29**; **2024-01-02 to 2026-09-09 is parsed into the D462 fixtures and stays UNREAD** — the
confirmation slice, opened only under a later record on the principal's word. No holdout of any
other fixture is touched. D463 taken after `ls docs/decisions` and `git log --all` (both worktrees)
showed D462 last.

## 0. The candidate, and why it is the one to run first

Lane 13 (`docs/research/Prop-Firm-080926/13-documented-intraday-effects.md`, C-13.1) rated this the
only near-miss with a real mechanism: **the return over the last 30 minutes of the session is
positively predicted by the return over the rest of the day** (Gao, Han, Li & Zhou 2018, JFE;
Baltussen, Da, Lammers & Martens 2021, JFE — the futures paper: ES β = 6.18, t = 5.0, R²_OOS 2.29%;
NQ 6.36; YM 5.02; Russell 6.00; 1974–2020), attributed to gamma-hedging demand near the close. It
is **flat at the close by construction** (P2), holds **30 minutes** (the ledger's "scissors close on
long windows": a short hold puts the floor many σ away), costs a tick and a commission on ES, and
**its one unpublished quantity — the path inside the window on open equity — is exactly what the
D462 one-minute fixtures now carry.** The lane wrote five falsification criteria; they are adopted
here verbatim where testable and one is declared untestable on our data.

## 1. The construction (declared; nothing swept)

- **Fixtures:** D462's `fut_{ES,NQ,YM,RTY}_rth_1m.csv.gz` and `fut_index_sessions.csv.gz`, gates
  passed. **ES is the primary instrument**; NQ, YM, RTY are reported. Per-point values: ES $50,
  NQ $20, YM $5, RTY $50.
- **Predictor** `rROD_d` = open of the 15:30 bar on day d ÷ close of the 15:59 bar on day d−1 − 1
  (Baltussen's: previous close to 30 minutes before the close). **Same-contract days only**: a day
  whose front contract differs from the previous session's is dropped (D448's rule; ~4 a year).
  Reported beside: `rFH_d` = open of the 10:00 bar ÷ open of the 09:30 bar − 1 (Gao's first half-hour).
- **Trade:** long if `rROD > 0`, short if `< 0`, entered at the **open of the 15:30 bar**, exited at
  the **close of the 15:59 bar** (the 16:00 print); no stop. `rLH_d` = the last-30-minute return.
  Days with `rROD = 0` or an early close (fewer than 380 bars) are skipped.
- **Path:** within the 30 bars, the position's running P&L from the 1-minute lows (long) or highs
  (short): **MAE** (worst mark), MFE, and the end, all in points and in dollars per contract.
- **Cost:** ES round trip = **1 tick ($12.50) + $4.50 commission** per contract, declared; NQ 1 tick
  ($5) + $4.50; YM $5 + $4.50; RTY $5 + $4.50. Net = gross − cost. (Futures cost is a quote, not
  a range — the one instrument in the repo where the cost line is not an estimate.)

## 2. The nulls (both from lane 13 §falsification)

- **N1 — time rotation of the sign series, enumerated.** `sign(rROD)` rolled by every offset
  k = 1 … T−1 over the in-sample days, the strategy's mean per trade recomputed on the real `rLH`;
  exact p50 / p95 / p99 (~3,400 offsets). Keeps the sign series' persistence; destroys alignment.
- **N2 — sign randomisation.** i.i.d. random signs, 10,000 draws: the same statistic. Destroys
  everything including the persistence; a benchmark for N1.
- **Both nulls are also run on the last-30-minute drift itself** (always long): the "always long"
  mean per trade is reported so the momentum effect is separated from the late-day drift D250 found.

## 3. The criteria (lane 13's five, verbatim where testable) and hurdle P

- **F1** gross mean per trade > 0 **and above both nulls' p95** (p50 and p95 reported, D373's margin
  on N2's sampled p95).
- **F2** per-trade σ and **the full MAE distribution inside the window**, per contract, in dollars:
  p50 / p90 / p99 / worst, and **P(MAE > $1,000)** (P3's 2% of a $50k account) and **P(MAE > $2,000)**
  (the 4% floor) at one contract.
- **F3** β(rROD) on 2010–2023 with **the sign and rough magnitude of Baltussen's 6.18** (OLS of
  `rLH` on `rROD`, Newey–West t); **the post-2018 subsample β below 3.0 falsifies** the candidate
  for our purposes (the McLean–Pontiff haircut arriving).
- **F4** the gamma mechanism — *stronger on negative net-gamma days* — **is not testable here: no
  options data.** Declared untestable and not replaced by a proxy. Reported instead, without a
  bar: the effect's sign on all four index futures (a real hedging-demand effect should not be
  ES-only) and its era split (2010–14 / 2015–19 / 2020–23).
- **F5** both lenses: per trade (bp and $/contract) and per bar deployed (bp/bar over the 30 held
  bars), never compared.
- **Hurdle P on the sized series** (P3, P4, P5 have never been computed on anything — D375 §5):
  size by the C4 rule as D440 ran it, **N_t contracts = f · $50,000 / σ̂_t** with σ̂_t the dollar
  σ of the per-contract trade P&L over the **prior 21 trades** (R9), capped at 4× the static
  notional, at **f ∈ {0.2%, 0.4%, 0.7%, 1.1%}** of the account (D440's grid, declared not chosen),
  contracts rounded down, minimum 0 (a day the rule sizes below one contract is skipped; the
  MES route is out of scope). Then, on the MFFU Rapid EOD 50K plan through D440's measured-path
  provider — each trading day's (d_low, d_high, d_end) in dollars from the within-window path —
  **P3** the share of days with a loss > 2% of the account and the worst day; **P4** the funded
  account's expected life in years (the 600-day horizon survival as D440 reported it) and `V`
  per evaluation with its block-bootstrap SE; **P5** the largest single day as a share of
  trailing-year profit, and the share of years in which it exceeds 40%.

**The bar (one primary, R14): ES, in-sample.** F1 ∧ F3 (both halves) ∧ **P4 ≥ 3 years at some
f on the grid with `V` > 0 by 2 SE at that f** ∧ P3's worst day ≤ 2% at that f ∧ P5 ≤ 40% at that f.
**Candidate for the unread 2024–2026 slice: all of it.** Anything short of that is reported as
what it is.

## 4. Predictions (MODERATE on F1–F3 from the literature with the decay haircut; LOW on hurdle P — the first computation)

- **X-a** F3: ES β(rROD) 2010–2023 **+2.5 to +6.0** (×100), t **2 to 5**; post-2018 **+0.5 to
  +3.5** — the 3.0 falsification line is a coin. NQ ≥ ES; YM and RTY same sign.
- **X-b** F1: mean per trade **+1.5 to +4.0 bp** (≈ 0.6–1.6 ES points, $30–80 per contract at
  today's levels; less in dollars early in the sample), hit rate **52–55%**; the always-long drift
  **+0.5 to +1.5 bp** (D250's late-day drift), so the sign adds +1 to +3 over it; N1 p95 ≈ +1.2 to
  +2.0 bp, N2 p95 ≈ +1.0 to +1.6; F1 passes on ES, a coin on RTY (fewer years).
- **X-c** F2: per-trade σ **18–28 bp** ($350–700/contract at 2023 levels); MAE inside the window
  p50 **6–10 bp**, p99 **50–90 bp**, worst **> 200 bp** (2015-08-24 or a March-2020 close);
  **P(MAE > $1,000) at one contract 2–6%; P(MAE > $2,000) 0.3–1.5%** — the lane's "1.58σ"
  arithmetic made concrete.
- **X-d** cost: net per trade = gross − 0.4 to 0.6 bp; **net positive at every f** — this is the
  one line in the programme where cost is not the verdict.
- **X-e** hurdle P: at f = 0.2% the rule sizes **0 contracts on most days** (σ̂ ≈ $500 → 0.2% × $50k
  / $500 = 0.2 contracts) — the grid's small end is empty for a futures contract on a $50k
  account; at f = 0.7–1.1% (1–2 contracts) **P3's worst day breaches 2% in every era**, **P4's
  expected life is under 1 year at every f**, and P5 fails in the years the effect is thin.
  **The candidate fails hurdle P on the size scissors the ledger described, with a positive net
  edge.** If P4 clears at any f, that is the finding of the year and the confirmation slice
  is the next record.
- **X-f** F4's reported checks: same sign on all four; the era split shows the effect **strongest
  2010–14, weaker 2020–23** (the decay), not the reverse.

## 5. Not in scope

The 2024–2026 slice; any stop, target or intraday exit variant; any other window (the 30 minutes
is Baltussen's, not a sweep); micros; any sweep of f beyond the declared grid; the options data
F4 needs. Fiftieth look by object; look #1 of the prop track on the instrument itself.

## 6. Files

This record · `scripts/run_d463_intraday_momentum.py` (`--run`, `--selftest`) ·
`data/d463_intraday_momentum.json`, `data/d463_trades.csv.gz` · RESULT.

---

## ADDENDUM, 2026-09-12, before the runner runs — the window and the instruments the data allows

D462's build (its ADDENDUM) found the archive lacks the index futures' day session on most days
before 2016 and declared a usable start per root. **This record's in-sample window is therefore
the usable start (expected 2016-01-04 for ES, NQ, YM) to 2023-12-29** — about eight years, not
thirteen and a half — and the runner reads the start from `fut_index_1m.meta.json` rather than
from a constant. **RTY is not run**: its fixture failed D462's G4 as pre-registered and is not
committed. Nothing else in §1–§5 changes; X-a's "2010–2023" and the era split's first cell
(2010–14) become the window's own thirds, and the post-2018 β test in F3 is unchanged (2018–2023
is inside the usable window). The predictions' sizes were written for the longer window and are
left as written.
