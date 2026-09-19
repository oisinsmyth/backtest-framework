# D561 — PRE-REGISTRATION: three sharpenings of D555's trend book, evaluated separately — **power** (the 13-year null), **sizing** (a leverage cap on the rates legs), **role** (trend as a drawdown overlay, against a null that diversifies as well as noise)

**Pre-registration. Committed before the runner exists (R8). Result in a separate file.** In
sample 2016-01-04 → 2023-12-29 for S2 and S3; S1 scores 2011-01-03 → 2023-12-29 by declaration;
**the 2024+ slice is RESERVED AND NOT READ.** Nothing admitted (R15). Nothing closed.

*2026-09-19. The principal asked what to make of D555 and whether the mechanism could be sharpened.
The assessment given was: the signal side cannot be sharpened from that record (the family already
spanned the speed axis and sat at its null's median; the offset profile is one realisation of one
window), and the three levers that are real are statistical power, position sizing, and the role
the book plays beside other components. The principal asked for each to be evaluated. This record
declares the three evaluations, their statistics, their nulls and their predictions before any of
them is computed. Every construction here is D555's 12-month book with one thing changed, and the
one thing is named per cell.*

---

## 0. What is shared with D555, unchanged

Fixture, live spans, same-contract daily returns with placeholder rows dropped, MOP's EW volatility
(centre of mass 60), the 40 % target, month-end signals held a month, the equal average over live
roots, the 252-session purge on the rotation null, the three audits and the exactness guard. The
runner imports D555's functions; **D555's 12m published book is rebuilt in-process and must
reproduce +0.304 gross on 2016–2023 to the printed precision before anything else runs** (the
harness check of this record). D556's cell A carry book is rebuilt the same way for S3 and must
reproduce −0.204.

## 1. S1 — power: the same construction on the declared long window, nulled

D555 §6 said the primary window's null is too wide to pass a trend book of published size and that
the 2011–2023 null "costs two minutes". This is that read, declared.

- **Cell:** D555's 12m published book, uncapped, scored **2011-01-03 → 2023-12-29** (3,353
  sessions). Its gross Sharpe is already in D555's record (+0.46); the unknown is the null.
- **N1-L:** enumerated sign rotation within each root's live span on the long window, common
  offset, **purged 252 sessions at both ends**, profile stored. Sortino beside the Sharpe (R17).
- **Statistic:** the observed 2011–2023 gross Sharpe against N1-L's p95 and percentile rank.
- **Predictions, in the runner's quantities:**

| # | prediction | reasoning |
|---|---|---|
| **S1-P1** | N1-L's Sharpe spread narrows by the square root of the session ratio: **sd(N1-L) between 0.38 and 0.48** (D555's purged N1 sd × √(2065/3353) = 0.55 × 0.785 ≈ 0.43) | a rotation null of a persistent sign book scales like a random walk in the number of independent holds |
| **S1-P2** | **p95 between +0.60 and +0.80**; the observed +0.46 is **inside**, rank between 0.80 and 0.95 | the long window adds 2011–2015 at +0.82, but the null's centre moves with it |
| **S1-P3** (falsifier) | if the observed clears N1-L's p95, the primary window was the problem and the effect is there at the programme's standard on 13 years — **still not promotable** (the long window is a declared diagnostic and its second half is the primary's in-sample) | |

## 2. S2 — sizing: a per-root leverage cap on the published book

D555 §3: the 40 % target on a two-year note whose ex-ante vol fell to 0.3 % is a position of 121×
notional; SR3 reached 111×, ZF 26×; the book's largest single days are those legs (ZT −6.8 % on
2021-11-26). The published construction has no cap. This cell adds one and nothing else.

- **Construction:** at each month-end, per root, `w = sign × min(0.40 / σ, CAP)`; held a month;
  equal average over positioned roots, as D555. **CAP ∈ {1, 5, 10, 20}**, four cells. **CAP = 10 is
  the declared cell** (it binds on the four rates legs whose leverage exceeds it and on nothing
  else at a typical month-end; 20 binds on ZT, SR3 and ZF only; 5 reaches the ten-year and the
  yen; 1 is the equal-notional book, dominated by the highest-vol roots). CAP = ∞ is D555's primary
  and is reported beside them as the reference, not as a member of the family.
- **Family for N2: the four capped cells.** N1 per cell rotates the signs with the capped scale
  in place, 2016–2023, purge 252. Sortino beside every Sharpe.
- **Statistic:** gross Sharpe 2016–2023 of the CAP = 10 cell, with its N1 p50/p95, and the
  family maximum against N2.
- **Reported beside it:** the roots the cap binds on and the share of month-ends it binds; per-root
  contribution to P&L and the top-1/3/5 root share; the sector split; the largest single day; max
  drawdown; turnover and breakeven; eras and years.
- **The component line.** The dollar book at minimum size holds one contract per root per sign;
  a leverage cap on the return-space weights does not alter it. The component line for every S2
  cell is therefore **D555 §4's dollar line, re-emitted by this runner from the same signs** (net
  +0.06, σ $8,762, fails C-a, C-c, C-d), and the runner asserts it reproduces those numbers. ρ with
  the ledger's live entry remains ABSENT for the reason D555 gave.
- **Predictions:**

| # | prediction | reasoning |
|---|---|---|
| **S2-P1** | CAP = 10 gross Sharpe 2016–2023 **below D555's +0.304**; point **+0.10 to +0.30** | ZT, ZF and TN are three of the five best roots; the cap cuts exactly their weight |
| **S2-P2** | the largest single-day loss of the CAP = 10 book is **smaller in magnitude than the uncapped book's**, and the book's daily kurtosis falls | the −6.8 % and −4.5 % days are the levered legs |
| **S2-P3** | top-3 root share of P&L falls **below 50 %** (uncapped: ZT, ZF, NQ reach half) | breadth is what the cap buys |
| **S2-P4** | monotone: gross Sharpe **rises with CAP** across {1, 5, 10, 20, ∞} | the vol target is where the construction's Sharpe lives; each cap removes some of it |
| **S2-P5** | no capped cell clears its N1 p95; the family maximum does not clear N2 | nothing here adds information the null lacks |
| **S2-P6** (falsifier) | CAP = 10 **above** +0.304 means the levered legs were costing Sharpe, not earning it, and the record says so | |

## 3. S3 — role: the overlay question, with a null that diversifies as well as noise does

D556 §4 measured the deposit's real claim for a second component: adding carry at −0.20 to trend
at +0.30 cut the book's drawdown by a fifth. The same question in the other direction is trend's
value to a book it does not carry on Sharpe: **does it pay on the base's worst days, and does it
shorten the base's drawdown by more than an uncorrelated random sign book would?** The second
clause is the point. Any uncorrelated series shortens a vol-matched drawdown; the rotation null is
exactly an uncorrelated persistent sign book with trend's own turnover and vol, so it is the right
control for the diversification-against-noise part, and what survives it is convexity.

- **Overlay X:** D555's 12m published book (uncapped), 2016–2023. The CAP = 10 book is run as a
  second overlay, diagnostic.
- **Bases B, all on 2016–2023, in daily simple returns off the breadth fixture:**
  - **B1 — ES long-only**, one unit of the front contract. The literature's base for "crisis
    alpha".
  - **B2 — 60/40**, 0.6 × ES + 0.4 × ZN, both long, rebalanced daily (declared as a crude balanced
    base, not a claim about any portfolio).
  - **B3 — D556's cell A carry book**, rebuilt in-process, the deposit's own candidate co-component.
- **Statistics, per (B, X):**
  1. **c5** — the mean of X on B's **worst 5 % of days** (about 103 sessions), divided by X's own
     daily sd. Also on the worst 10 %. And the hit rate of X on those days.
  2. **DD ratio** — max drawdown of the vol-matched equal blend `(B/σ_B + X/σ_X)/2` divided by max
     drawdown of `B/σ_B`, both in cumulative daily return units (D542's convention, negative
     levels). Below 1 is a shorter drawdown.
  3. ρ daily and monthly; the Sharpe and Sortino of B, of X, and of the blend.
- **Null N1-O:** rotate X's signs with D555's rule (2016–2023, purge 252), recompute c5 and the
  DD ratio at each surviving offset against the fixed B. p50 and p95 of each. **The declared
  statistic is c5 on B1 against its null p95.** The DD ratio's null answers the diversification
  question directly: the observed ratio is compared with the null's p05 (a shorter drawdown than
  95 % of random sign books).
- **Predictions:**

| # | prediction | reasoning |
|---|---|---|
| **S3-P1** | c5 on B1 **> 0 and above N1-O's p95**; point **+0.15 to +0.50 σ** | March 2020 (trend +21 %) and 2022 are inside the window; the null's c5 is centred near its tilt, about 0 |
| **S3-P2** | c5 on B3 (carry) **> 0**; point +0.10 to +0.40 σ | D556 §4: the worst-5 %-day overlap was 29 %, and trend earned in carry's worst month |
| **S3-P3** | DD ratio on B1 **below the null's p05**: trend shortens the equity drawdown by more than noise does | convexity, if it exists here, is exactly this |
| **S3-P4** | DD ratio on B3 **below 1** but **not below the null's p05** | D556's one-fifth cut is consistent with diversification alone at ρ 0.18 |
| **S3-P5** | ρ(X, B1) daily between −0.30 and +0.10 | trend on 36 roots is long equities half the time and short in the drawdowns |
| **S3-P6** (falsifier) | c5 on B1 inside its null with S3-P3 also failing means trend's value beside equities on this window is diversification, not convexity, and the "crisis alpha" reading of D555's 2020/2022 years is a two-event coincidence the null reproduces | |

## 4. What is scored, and what is not promotable

Three declared statistics, one per sharpening: S1's observed long-window Sharpe against N1-L; S2's
CAP = 10 gross Sharpe against N1 and the four-cell family against N2; S3's c5 on B1 against N1-O.
Everything else in §1–§3 is diagnostic. **No cell in this record is a candidate for either book**:
S1 is a read on a diagnostic window; S2's component line is D555's, which fails C-a, C-c and C-d;
S3 scores a role, not a component, and the assembled prop book's live arm has no daily P&L on disk
to overlay. What S3 can change is the *disposition* of trend in `docs/COMPONENTS_PROP.md`'s notes
(overlay, not component) and the question the next study asks.

## 5. Runner assertions

D555's three audits re-run on the rebuilt book and each proven to raise (lag on an unlagged grid;
sign in money on a negated and a mis-lagged gross grid; right quantity on a daily grid). New:
**(a)** the rebuilt D555 primary equals +0.304 and the rebuilt D556 cell A equals −0.204 to 1e-9 in
daily P&L against the committed artifacts' printed Sharpes to three decimals; **(b)** the capped
book at CAP = ∞ is bit-identical to the uncapped book, and at CAP = 10 differs from it on exactly
the roots and month-ends where 0.40/σ > 10, proven by a second implementation over the month-end
grid; **(c)** the worst-5 % day set of each base is recomputed by a pandas quantile path and must
match the numpy path; **(d)** the exactness guard on 20 offsets against the plain loop for the
long-window null and for the capped cell. `REQUIRED_OUTPUTS` guarded; `max_drawdown_convention`
block first; every text-IO call carries `encoding="utf-8"`.

## 6. What is read, and what is not

The breadth fixture from 2010-06-07 for warm-up, the curve table for B3, both filtered below
2024-01-01 before anything is computed. **Not read: any session from 2024-01-02 onward.** No new
fixture. Projected wall time under five minutes: the long-window null is 3,352 offsets of one
published cell, the capped family 2,064 × 4, the overlay null 2,064 × 2 overlays × 3 bases, each
offset a `book_return` call.

## 7. What this record does not do

No new signal. No reversal leg read off D555's offset profile (that profile is one realisation of
one window and the only unread slice is the assembled book's). No covariance-scaled or
cross-root-hedged book (HOP), which is a different construction. No de-seasonalised carry in B3. No
overlay on the ledger's live arm. A capped book that loses Sharpe and gains breadth is recorded as
that trade, priced; it is not a candidate.
