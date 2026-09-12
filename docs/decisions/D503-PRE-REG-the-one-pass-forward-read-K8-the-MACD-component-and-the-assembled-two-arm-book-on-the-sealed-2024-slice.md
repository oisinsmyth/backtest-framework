# D503 — PRE-REG: the one-pass forward read — K8, the MACD component, and the **assembled two-arm book** on the sealed 2024+ slice

**2026-09-13.** Committed **before the runner exists** ([R8](../RULES.md#r8)) and on its own, to
claim the number.

**On the principal's word:** *"Ok lets action on 1. there is another provisional strategy in
prop-book.md, we should run both at the same time and then also a combined book, with stats."*

**This is the read [BOOK_PROP.md](../BOOK_PROP.md) parked K8 for.** Its parking note of
2026-09-12 declared the condition exactly: *"the read waits for a second component … and then
K8's promotion, the second component's promotion and hurdle P on the assembled book are read
together in one pass on 2024+."* The second component now exists. **This is that one pass, and
it spends 2024-01-02 → 2026-09-09 for both components and for the book. There is no re-read.**

---

## 1. Two things to settle before anything runs

### 1a. ρ is already measured, in-sample, and it decides the structure

**ρ(K8, MACD component) = +0.190** over the 1,873 common in-sample sessions (+0.269 on K8's 817
trading sessions alone). Computed on 2016–2023 only, so **no holdout was spent to learn it.**

**Below C-b's 0.3, so the MACD component routes to Book 1's ledger and not to the vault.** One
account, two arms, one shared 4% floor. Had ρ been ≥ 0.3 this would have been a two-account read
with no combined hurdle P, per the vault's rule 4.

In-sample baselines for the assembled book, so the forward figures have something to be compared
against:

| | mean/session | daily σ | net Sharpe | worst day |
|---|---:|---:|---:|---:|
| MACD component (NQ AGREE M=5, 1 MNQ) | +$8.22 | $180 | **+0.723** | −$1,315 |
| K8 (long the NQ day session after a down day, 1 MNQ) | +$6.41 | $171 | **+0.595** | −$1,025 |
| **assembled book, 1 MNQ each, summed** | **+$14.63** | **$271** | **+0.856** | **−$1,801** |

**That worst day is 90% of the account's entire $2,000 loss budget in one session**, which is the
single most important thing this read has to price. It is *not* a reason to skip the read — it is
the reason hurdle P is tested on the book and not on the arms.

### 1b. A closure I have to declare a reading of, because it is one day old

The principal closed **the hourly clock** for the prop book on 2026-09-13 after D499: *"any
hourly-horizon construction on the eight gated roots at micro cost."*

**My reading, stated so it can be overturned in one line:** that closure is about a **~1-hour
holding horizon** — D499's construction faded the *next hour* and its arithmetic is *"the fee is
7–24% of the expected hourly move on the micros"*, explicitly contrasted with **"2.4% for the
whole day session"**. The MACD component **decides** on an hourly grid but **holds for the
session**: minimum hold 5 hours, 1.02 round trips a session, flat at 16:00. It sits in the
day-session category the closure quotes approvingly, not in the hourly-horizon category the
closure rejects. **If the principal means the closure to cover the hourly decision clock as
well, this read should not happen and the component is closed instead.**

## 2. The two components, specified exactly

**K8 — ledger entry #1, PROVISIONAL.** Long **one MNQ** from the 09:30 open **plus one tick** to
the 15:59 close, on days after the NQ day session closed **below** its open (≈44% of sessions).
$3 a round trip. Runs on the 1-minute fixture via
[`scripts/run_d498_k8_and_second_clocks.py`](../../scripts/run_d498_k8_and_second_clocks.py).

**The MACD component — candidate, not yet a ledger entry.** NQ front month by volume, traded as
**one MNQ**, day session only: decide at each hour's close from h09, execute at the next hour's
open, enter when the log Impulse MACD (34/9) and the plain log MACD histogram (12/26/9) **agree
in sign**, exit when the signal turns after **≥ 5 hours** held, forced flat at the close of h15
(16:00 ET). $3 + 1.009 ticks a round trip. Runs on the hourly fixture.

**Neither is re-tuned, re-gated or re-scored.** The specifications above are frozen as committed.

## 3. The promotion rules, declared before the read

**K8's rule is already pre-registered in D498 §3 and is used verbatim** — I am not writing a new
one for it, and K8's forward read is taken from **its own guarded command**
(`--forward --principals-word`), not reimplemented:

> FULL if forward gross mean > 0, net Sharpe > 0 and z(after-down − after-up) ≥ 1;
> REMOVED if net Sharpe < −0.3 or the difference is negative; otherwise PROVISIONAL.

**The MACD component's rule, declared here for the first time, mirroring K8's three-way shape and
using C-a's existing bar rather than a new one:**

| verdict | condition on the forward slice |
|---|---|
| **REMOVED** | net Sharpe < −0.3, **or** gross mean per round trip ≤ 0 (the signal is gone, not merely the cost) |
| **FULL** | net Sharpe > **+0.5** (C-a's bar) **and** gross mean per round trip > 0 |
| **PROVISIONAL** | anything else |

**The rotation null on the forward slice is REPORTED and does NOT gate.** Gating on a threshold
*and* a null would let me choose which one to believe after the fact.

**The book's rule:**

| | |
|---|---|
| the book is **assembled** | only if **neither** component is REMOVED |
| the book is **admitted to `BOOK_PROP.md`** | only if it is assembled **and** clears **hurdle P, all six**, on the forward slice, under the **amended P3** (P3a ≤ 1.0 breach/yr, P3b ≤ 33% of the account's life, P3c reported) |
| otherwise | nothing is admitted, and the record says which test failed |

## 4. The book's construction, and what it deliberately does not do

**One MNQ on each arm, independently, summed.** Net exposure therefore ranges −2 to +2 MNQ; when
the arms oppose, the book is flat but has paid two sets of costs.

**No netting, no shared sizing, no arm weighting.** A netted implementation would save cost when
the arms disagree, and a vol-weighted one would change the risk split — **both are new
constructions and neither is tested here.** The un-netted sum is the conservative reading and it
is what the two committed specifications produce if run side by side.

**Calendar:** the **union** of both arms' session calendars, with an arm contributing **zero** on
a session it did not trade. The runner reports how many sessions each arm was absent for —
in-sample, 54 of K8's 871 trades (6%) fell on sessions the hourly fixture's purity mask excludes,
and that asymmetry must be visible rather than silently intersected away.

## 5. The statistics required, all four groups ([CLAUDE.md](../../CLAUDE.md))

1. **Performance, net AND gross side by side** — per arm and for the book: mean and median per
   session and per trade, daily σ, Sharpe, exposure (sessions traded / sessions available),
   max drawdown in dollars, mean move per trade against `2c`, and **breakeven cost in ticks**.
2. **Trade distribution** — count, mean, median, hit rate, payoff, holding run, skew, kurtosis,
   and the **1% trim from BOTH tails** with all three means reported (ex-top, ex-bottom,
   trimmed).
3. **What the winners depend on** — sessions to reach half the P&L, top-1/5/10 session share,
   profitable years **and quarters**, and the split by calendar year (2024 / 2025 / 2026), which
   is the regime axis [D501](D501-the-worst-day-is-a-regime-not-a-habit.md) made the live
   question.
4. **Nulls — the distribution, not the percentile** — rotation null on the forward slice for each
   arm and for the book, with **p50, p95 and the p95's bootstrap SE**, and any margin inside
   2 SE recorded **UNRESOLVED**.

**Plus, specific to this read:**

- **In-sample beside forward for every headline number**, and the **decay ratio** on each.
- **ρ(K8, MACD) on the forward slice**, beside the in-sample +0.190 — because C-b was checked on
  in-sample data and a correlation that rises above 0.3 out of sample changes the routing.
- **Hurdle P, all six, on the book**: P1 sizing, P2 flatten (both arms exit by 16:00 ET, inside a
  16:10 flatten), **P3a/P3b/P3c amended**, P4 expected profit before breach against the fee,
  P5 the exact 30% haircut, P6 venue.
- **The empirical trailing-4% account life on the book**, by D501's walker, beside D496's
  Brownian figure — because the Brownian model proved *pessimistic* by 45% on one arm.

## 6. Predictions

| | prediction |
|---|---|
| **V-a** | **both** components' forward net Sharpe is **positive but lower** than in-sample — the honest prior for any in-sample-selected cell |
| **V-b** | the MACD component lands **PROVISIONAL**, not FULL: forward net Sharpe in (0, +0.5) |
| **V-c** | K8 lands **FULL** — its rule needs only gross > 0, Sharpe > 0 and z ≥ 1, which is a far lower bar than C-a |
| **V-d** | the book's Sharpe **exceeds both arms'** on the forward slice, because ρ stays below 0.3 |
| **V-e** | forward ρ stays **below 0.3** (in-sample +0.190) |
| **V-f** | the book **FAILS P3a** — the combined worst day is 90% of the loss budget in-sample, and two arms on one floor breach a daily limit more often than one |
| **V-g** | the book's **empirical** account life exceeds D496's Brownian estimate for its Sharpe, as it did on the single arm (256 against 177) |

## 7. Checks the runner must carry

1. **Both arms' P&L series re-derived on the union calendar**, with an assertion that the book's
   series equals the sum arm-by-arm and session-by-session — and a deliberate one-session
   misalignment must make it **raise**.
2. **The holdout boundary asserted**: every forward session is ≥ 2024-01-02, and **no in-sample
   session is read** by the forward path. A deliberately widened window must raise.
3. **K8's forward numbers taken from its own runner's artifact**, and asserted equal to what this
   runner reads from its trade CSV — two paths to the same figure.
4. **`net = gross − cost × trips`** asserted exactly, per arm and for the book.
5. **The rotation null preserves the rotated object's duty cycle and run structure**, as in D502.
6. **P3a/P3b computed by the same functions as D501** (imported, not re-implemented), so the
   amended hurdle is applied identically to the arm and to the book.
7. Every `[X]` break fires on the **scalar** the assertion compares.

## 8. What this cannot do

- **It is one read and it is spent afterwards.** After D503, 2024-01-02 → 2026-09-09 on the NQ
  day session is **spent for both components and for the book**. No cell may be re-read on it,
  sharpened against it, or re-scored on it.
- **It admits at most one thing**: the assembled book, to `BOOK_PROP.md`, and only on hurdle P
  all six. Nothing else is admitted ([R15](../RULES.md#r15)).
- **Fills remain open-of-next-segment / open-plus-a-tick at the measured half-spread.** No queue,
  no partial fills. Every figure is an upper bound, and the *worst day* — the figure P3 reads —
  is the one most exposed to that optimism.
- **It does not test netting, weighting, a third arm, or any filter.** D502 closed the filter
  question for now; this read is the two frozen specifications and their sum.
