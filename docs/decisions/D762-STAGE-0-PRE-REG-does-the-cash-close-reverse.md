# D762 STAGE 0 PRE-REGISTRATION — does the cash close reverse? A premise check on whether the closing auction's pressure (15:50 → 16:00) gives back in the futures between 16:00 and 16:10 (ES, NQ, YM, RTY; prop book)

*2026-10-02. Prop book.*
- *The principal: "Lets do some premise checks for the cash close?". This followed the reasoning that the only
  reversals on file to clear their nulls are tied to a clock (scheduled, forced flow: D710, D630, D685).*
- *Numbered D762, claimed with the documentation-review session.*
- ***Committed alone, before the fixture's builder and the runner exist.** In-sample only (2016-01-04 → 2023-12-29).*

## 0. The mechanism and what is already on file

**The mechanism.** The cash equity close at 16:00 is the day's largest forced trade: index funds, leveraged-ETF
rebalancing, rebalance days and MOC orders.
- Those orders are price-insensitive and time-constrained. The pressure they put on the index shows in the futures
  in the final minutes, when exchange imbalance information is published and the auction is crossed.
- **If that pressure is temporary** (inventory taken on by liquidity providers, not information), part of the move
  into 16:00 should reverse once the auction has cleared.
- **Index futures keep trading after 16:00,** and a prop account must be flat by 16:10. The 16:00–16:10 window is
  tradable within the book's clock.

**On file, and why this is not a repeat:**
- **D461:** read volume only, no returns. After 16:00, futures volume is a monotone decay from the cash close: the
  16:00 minute holds 21% of the 16:00–17:00 hour.
- **D622:** the last-hour decline and the overnight that follows. UNRESOLVED; it never read 16:00–16:10.
- **D640:** the LETF close-flow model, killed by its own 11:00 placebo. Its late-day effect was day-level
  continuation (14:30 → 16:00), not a close-specific flow. It read the 2024-01 → 2025-02 slice for NQ's 14:30–16:00
  windows, not for the post-close window.
- **F2** (D707, D716) follows the day from 15:30 to 16:00 and earns. This record asks whether the final minutes of
  that path give back after the close. It shares a signal with F2 but not a clock.

## 1. Data: a new fixture (validation declared now)

**`fut_index_close_1m.csv.gz`**, built by `scripts/build_fut_index_close_1m.py`, a variant of D462's
`build_fut_index_1m.py`:
- **Coverage:** ES, NQ, YM and RTY, one-minute bars **15:30–16:14 ET** (bar starts), from the raw `ohlcv-1m`
  archive (`data/raw/databento/*/*.ohlcv-1m.dbn.zst`).
- **The front contract** for each (root, day) is taken from `fut_index_sessions` (D462's front by full-day volume),
  not re-derived. A session's post-close bars therefore belong to the same contract as its day-session bars.
- **The seal:** only archive files dated 2016-01-01 → 2023-12-31 are decoded. The builder asserts that no row on or
  after 2024-01-01 survives, and the self-test proves that assertion raises.
- **Runs on the system python** (databento is installed only there).

**Validation, before any return is read:**
- **V1:** on the overlap 15:30–15:59, every bar present in both this fixture and `fut_{root}_rth_1m` has the same
  open, high, low, close and volume on ≥ 99.9% of bars.
- **V2:** ≥ 95% of the sessions that have a 15:59 bar also have at least one bar in 16:05–16:09.
- **If a root fails,** it is dropped and the record says so. No gate is relaxed.

## 2. Sessions and quantities (fixed now)

**Eligible sessions:**
- D462's sessions in 2016-01-04 → 2023-12-29 (RTY from 2017-07-10);
- not a roll session, and one contract across every bar used;
- the 15:49, 15:59 and 12:00-placebo bars present;
- at least one bar in 16:05–16:09;
- **early-close days are out** (no 15:59 bar).

**Prices** follow D727's convention: P_t is the close of the bar starting t−1, forward-filled within the window.

| quantity | definition |
|---|---|
| **x, the pressure** | P₁₆:₀₀ − P₁₅:₅₀ (the final ten minutes: the imbalance period) |
| **y, the response** | P₁₆:₁₀ − P₁₆:₀₀ (the close of the 16:09 bar against that of the 15:59 bar) |
| x₃₀ (reported) | P₁₆:₀₀ − P₁₅:₃₀ (F2's window) |
| placebos | the same pair one hour earlier (x = P₁₅:₀₀ − P₁₄:₅₀, y = P₁₅:₁₀ − P₁₅:₀₀) and at noon (x = P₁₂:₀₀ − P₁₁:₅₀, y = P₁₂:₁₀ − P₁₂:₀₀) |
| $ | points × the micro's $ per point (MES 5, MNQ 2, MYM 0.5, M2K 5) |
| cost | each micro's `default_line` round trip in `data/futures_costs.json` |

## 3. The checks

**C1 — size (reported, and the premise's floor).** Per root: sd(y) and mean \|y\| in $ per micro, against the cost.
And the same for x.

**C2 — the reversal exists (per root).**
- **The statistic:** Spearman ρ(x, y).
- **The null:** the **exact enumerated rotation** of y across that root's eligible sessions (offsets 1 … n−1). Its p05,
  p50 and p95 are reported (SE 0).
- **Passes:** ρ < 0 and below the rotation's p05 (one-sided), **after Holm across the four roots** at α = 0.05.
- **Also reported:** the OLS slope of y on x, with a Newey-West(5) t.

**C3 — it is the close, not generic.** For each root passing C2, the close's ρ must be more negative than **both**
placebos' ρ by more than 2 SE. The SE is a paired day-block bootstrap of the difference (2,000 draws, seed 762). A
margin within 2 SE is UNRESOLVED (D373).

**C4 — the prize.**
- **The fade:** take the side −sign(x) at P₁₆:₀₀ and exit at P₁₆:₁₀, on sessions whose \|x\| is in the walk-forward
  top third (250 prior eligible sessions of that root, strictly prior).
- **Passes:** the mean **gross** ≥ the cost, with t ≥ 2.
- **The four groups** at one micro, net and gross, are reported for every root whatever C2 and C3 show.

**The readings, per root:**

| reading | when |
|---|---|
| **NO REVERSAL** | C2 fails |
| **GENERIC** | C2 passes; C3 fails (a placebo reverses as much) |
| **UNRESOLVED** | C2 passes; a C3 margin is within 2 SE |
| **NO PRIZE** | C2 and C3 pass; C4 fails |
| **PREMISE HOLDS** | C2, C3 and C4 pass |

**What follows a PREMISE HOLDS:** a trading pre-registration, read on the held 2024-01 → 2025-02 slice and the
forward recorder, on the principal's word. It is never admitted from this in-sample run.

## 4. Reported, never gating

- **Heavy-auction days against the rest:** ρ and the C4 fade on quarterly-expiry Fridays (S&P rebalance), month-end
  sessions and the Russell reconstitution day (late June; RTY). This is the dose-response the mechanism predicts.
- **x₃₀ as the pressure** (F2's window) and the day's open-to-close move as the pressure.
- **The response at 16:05 and 16:15** (the window's shape).
- **ρ of the C4 fade's daily net** with F2, C1 and D737 (`data/d748_component_books.csv`).
- **By year;** long against short; the top trades named.
- **The cost after 16:00:** the fade's net with one extra tick of crossing, because post-close spreads may be wider
  than the day-session line.

## 5. Size the prize (stated now)

- **Guess.** The final ten minutes' move has an sd of perhaps 2–3 ES points ($10–15 per MES). If a tenth to a fifth of
  it reverses within ten minutes, the top-third fade's gross is about $2–5 per MES, against a cost of $4.42.
- **The cost.** It binds here as it did in D499 and D528. The question is whether the close's forced flow is large
  enough to lift the reversal above the generic one.
- **Power.** About 1,950 sessions per root (RTY about 1,600) give C2 an SE on ρ of about 0.023, so a ρ of −0.06 is
  detectable. C4 has about 650 trades per root.

## 6. The runner's assertions (each proved to raise in `--selftest`)

1. **The fixture's V1 and V2** are re-read from its meta, and the run stops if either failed.
2. **Lag and right quantity:** for 40 sampled sessions per root, a plain loop over the raw fixture rows re-derives x,
   y, the placebos and the walk-forward tercile flag. **Break:** a tercile including the current session must raise.
3. **Sign in money:** a favourable move pays long and short positively.
4. **The rotation's offset 0** equals the observed ρ.
5. **The seal:** a 2024-dated row injected into any input raises.
6. **Synthetic:** a planted reversal in the close window and not in the placebos passes C2 and C3. Noise fails C2 about
   95% of the time.

**Speed.** The fixture build decodes eight yearly archive files on processes (D462 took 6.2 minutes for 16 years on 6
workers), so it should take about 3–4 minutes. Each runner rotation is about 2,000 offsets of a vectorised rank
correlation, roughly 10 s a root. **The projected wall time is under 2 minutes** for the runner.

**Outputs:** `data/stage0_d762_cash_close.json`; the fixture and its meta in `data/fixtures/` (the panel gitignored,
the meta tracked).

## 7. Predictions (Opus)

- **P1: C2 passes on at least two roots** (P 0.6). Some reversal after the auction is likely: liquidity providers
  who absorbed the imbalance unwind.
- **P2: C3 is UNRESOLVED or fails on most roots that pass C2** (P 0.5). Ten-minute reversals happen at every clock
  (D499).
- **P3: C4 fails everywhere** (P 0.7): the reversal is real but worth less than $4. The likeliest exception is RTY,
  which has the largest $ moves per micro.
- **P(PREMISE HOLDS on any root) ≈ 0.12.**
