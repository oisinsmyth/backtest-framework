# D356 RESULT — the two books blend to a higher Sharpe than either, above every draw of both paired nulls, and the arithmetic says exactly how much

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D356-RESULT-the-two-books-blend-to-a-higher-sharpe-than-either-and-the-arithmetic-says-exactly-how-much.md`. The H1 above is the full title.*

**Status:** RESULT. Pre-registered at `d1844b7`, runner at `0a34c6c`, the target-arm data at
`e58ebcd`, the addendum in the pre-registration — all before this file existed (R8). Target
arm only (D355 kept the target). `keep_v2`, F0, next-open fill, depth 2, k=40, PUB primary,
PB beside.
**Date:** 2026-09-06
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is promoted. The blend is a candidate portfolio for the out-of-sample read.**

---

## 1. The verdict

**Four of six, and the load-bearing one held.** The 50/50 capital blend of `rsi` k=40 and
`hist_L` k=40 nets **+8.78 bp/bar under PUB at a net Sharpe of 0.442**, against 0.268 and
0.401 for the parents, on a correlation of the two gross series of **+0.21**. It is above
every one of 100 paired time rotations (p95 −0.45) and every one of the 24 paired rank
rotations (p95 −0.11) on net Sharpe, and on net bp/bar, gross, and both cost lines.

| PUB, bp/bar | gross | cost | **net** | vol | **net Sharpe** | max DD (net) |
|---|--:|--:|--:|--:|--:|--:|
| `rsi` k=40 | 12.70 | 7.56 | +5.14 | 305 | 0.268 | 10,471 |
| `hist_L` k=40 | 26.73 | 14.31 | +12.42 | 491 | 0.401 | 23,208 |
| **blend 50/50** | 19.71 | 10.93 | **+8.78** | 315 | **0.442** | 15,004 |

Under PB the blend nets +14.76 at a Sharpe of 0.743 (parents 0.538 and 0.620).

## 2. What the blend is and is not

**It is the covariance.** The blend's vol (315) is barely above `rsi`'s (305) while its net
is 71% higher, because `hist_L`'s 1.6× vol enters at half weight against a correlation of
0.21. The arithmetic prediction from the parents' net, vol and correlation reproduces the
realised Sharpe to four decimals — which is a statement about the definition, not a finding:
a linear blend's Sharpe *is* that arithmetic. **Q6 was an identity as written**, and the
record says so rather than reading its failure as evidence.

**It is not a new left tail.** The worst 1% of bars (32 each) overlap on two dates
(2024-02-22, 2024-03-04); the worst 1% of trades share one name (SMCI). And it is not two
independent books either: **on 46% of bars the two hold the same name on the same side**,
1.5% on opposite sides. Both are reversal-type selectors at the extreme of 1,573 names, and
they agree on the names often; they disagree on the timing and the rest, which is where the
0.21 comes from.

**Q3 falsified**: the blend's drawdown (15,004 bp on the net series) sits between the
parents', not below the smaller. A 50/50 capital blend inherits half of `hist_L`'s drawdown
and the two books' drawdowns are not simultaneous enough to offset it.

## 3. Predictions

| | | outcome |
|---|---|---|
| **Q1** | correlation of the gross series < 0.4 | **CONFIRMED** — +0.21 |
| **Q2** | *(load-bearing)* blend PUB net Sharpe above the better parent's | **CONFIRMED** — 0.442 vs 0.401 |
| **Q3** | blend max DD below the smaller parent's | **FALSIFIED** — 15,004 vs 10,471 |
| **Q4** | worst-1% bars overlap < 25%; worst-1% trades share ≤ 3 names | **CONFIRMED** — 6.2%; one name |
| **Q5** | above the paired time rotation's p95 on net Sharpe | **CONFIRMED** — 0.442 vs −0.450, 100 of 100 |
| **Q6** | *(against)* exceeds the arithmetic by > 0.05 | **FALSIFIED** — an identity; diff 0.0000 |
| *check* | parents == D346 to 0.0; [LIN] 1e-12; [V] 1e-9 | held — 0.0; 1.8e-15; 1.5e-11 |

Four of six.

## 4. Stop conditions, executed

- **Q2 holds → the blend is a candidate portfolio.** Whether D357's one read is spent on the
  blend or on the declared single book is the principal's choice, recorded in D357's
  addendum. Reading the blend reads both parents, so the read yields all three sets of
  hurdles at once, with the hurdles gating whichever construction the addendum names.
- **No secondary arm** (addendum): the target stays.
- Nothing is promoted. Book: empty.

## 5. Deviations and what the run found

- **Q6 was pre-registered as a prediction and is an identity.** For a linear blend the
  Sharpe computed from the parents' net, vol and their measured correlation equals the
  realised one exactly. The prediction should have been on the correlation (Q1), which it
  also was. Recorded as a pre-registration error.
- The max drawdown is defined on the cumulative **net** per-bar series for the parents and
  the blend alike (gross drawdowns beside: 8,423 / 16,697 / 11,043); the worst-1% sets are
  `ceil(0.01·N)`; both are stated in the JSON.
- The paired null draws sit at a Sharpe near −0.9 with a correlation near 0: rotated books
  are uncorrelated and lose; the blend's correlation of 0.21 is itself above every draw.

## 6. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | via the shared prep |
| **[ID]** | both parents == D346 to 0.0; the null-path simulator call reproduces the observed book and ledger bit-identically |
| **[M]** | the masks coincide, 3,187 bars |
| **[LIN]** · **[V]** | net and gross to 1.8e-15; variance to 1.5e-11 |
| **[T]** | worst-1% sets by argsort and by partition threshold agree; no boundary ties; occupancy rebuilt from the ledgers matches the simulator's counts except the open tail |
| **[A]** · **[N]** | each parent's rotation keeps counts and multisets on every name |
| **[6]** | [LIN] raises on a 60/40 blend; [V] raises with ρ forced to 0 |
| **[P]** | JSON round-trip 0.0 |

**Speed:** self-test 7 s; 1.8 s a null draw; 100 draws over two processes in 3 min; report 8 s.

## 7. What this establishes

1. **A portfolio of the two candidate books has a net Sharpe of 0.44 under the published
   spread**, above either book and above every draw of both paired nulls, with no new look
   and a stated correlation of 0.21.
2. **The two books hold the same name on the same side on 46% of bars** and still
   correlate at 0.21; the diversification is in timing, not in names.
3. **The blend's drawdown is between the parents'**, not below both; capital blending does
   not remove `hist_L`'s left tail, it halves it.
4. **A linear blend's Sharpe is arithmetic**; the only prediction worth making about a
   blend is the correlation.

## 8. Files

`data/d356_null_target_p{0,1}.json` · `data/d356_blend.json` · `scripts/run_d356_blend.py` ·
the pre-registration's addendum
