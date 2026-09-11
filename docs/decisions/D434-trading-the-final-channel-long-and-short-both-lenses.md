# D434 — trading the final channel, long and short, both lenses

*Pre-registration. Written before the runner exists (R8). The construction is frozen at the
principal's final settings line of 2026-09-10; the trading rule below is the FIRST rule tried on
it and is not searched. Numbers in §2 are in-sample and are disclosed as such.*

## 0. What is being tested, in one sentence

Does the direction of the D399 channel — as finally constructed, a support and a resistance line
that live and die together — predict the sign of the next bars' return, long in a rising channel
and short in a falling one, gross of cost first and net of a measured spread second?

## 1. The construction, frozen, and where it lives

`CELL_FINAL` in `scripts/d399_new_sample.py`, the live page's settings line transcribed field for
field:

    k=2 mp=2 maxp=0 carry=7 dh=20 dg=0 mw=10 body=on bdepth=2 bbars=2 syn=on anchor=quantile
    aq=0.2 dmode=rank decay=0.76 height=anchored ttl=on walk=on btol=-1 chain=body_only
    reach=130 stalew=35 staled=18 stalestat=mean fittol=16 pairbreak=on pairdraw=on fit=ols
    ttol=0.37 mt=1

It was chosen by eye over several hundred settings of a dial page on 24 (name, window) pairs
drawn under a declared rule (seeds 20260910 and 20260911, `data/d399_final.json`,
`data/d399_final_draw2.json`). **That is the R13 search:** roughly 200 settings looked at on 24
windows, no score, the principal's eye as the criterion. None of it touched a trading rule or a
return. The lines are causal by construction — every fit reads only pivots confirmed `k` bars
back, and `[L]` re-derives gradient, level and origin at sampled bars from a truncated rebuild of
the bars themselves — so the state at close `t` is knowable at close `t`.

Everything in `recalc_pair` that could leak has an assertion on it: `[S]` bar order, `[R]` no
line more than the break depth through a body, `[C]` no inverted channel, `[Z]` no line drawn
again after a body closed through it, `[L]` causality. They run on every name in the runner.

## 2. The state, and what the record already knows about it (in-sample)

The channel is DRAWN at close `t` when both lines qualify (`pair_draw`). Its direction is the
sign of the two gradients:

    UP    at t:  channel drawn, g_support > δ and g_resistance > δ      (δ = 1e-3 /bar, D399's)
    DOWN  at t:  channel drawn, g_support < -δ and g_resistance < -δ
    FLAT  otherwise — including a drawn channel whose two lines disagree in sign

On the 24 drawn windows, under the final cell, the forward close-to-close log return by state
(state at close `t`, return close `t` → close `t+h`), computed by `d399_new_sample.run_one`'s
`fwd` — the number that motivates this record, and it is in-sample twice over (the windows the
construction was chosen on, and the same bars the state is read from):

### 2a. The in-sample table (24 windows, 6,240 name-bars; bp; state at close t)

| h | state | n | mean | median | win % |
|---|---|---|---|---|---|
| 1 | UP | 1,250 | −4.1 | 4.2 | 52 |
| 1 | DOWN | 813 | +11.4 | 8.1 | 52 |
| 1 | all bars | 6,240 | +5.1 | 7.6 | 52 |
| 5 | UP | 1,250 | −1.0 | 23.5 | 52 |
| 5 | DOWN | 813 | +75.1 | 76.9 | 57 |
| 5 | all bars | 6,240 | +23.7 | 41.4 | 54 |
| 21 | UP | 1,250 | −2.8 | 9.7 | 51 |
| 21 | DOWN | 813 | **+239.7** | 284.1 | 63 |
| 21 | all bars | 6,238 | +78.3 | 138.1 | 56 |

**Read plainly, before any rule is built:** on the windows the construction was chosen on, a
rising channel is followed by *nothing* (the UP state underperforms the unconditional bar at
every horizon) and a falling channel is followed by a *rise* (+240 bp over 21 bars against +78
for all bars). That is the opposite of trend-following on the short side and null on the long
side. It is 24 windows, chosen by eye, and it counts for nothing as evidence — but it is the
record's own number, and R9's corollary applies: it is stated here so the result cannot be
read against a story that was never predicted.

**Consequence for the design.** "Long in a rising channel, short in a falling one" is the rule
the principal asked for and the natural reading of the construction, and §2a predicts it fails
on both sides. The mirror — long after a DOWN channel — is a *different rule*, and choosing it
now would be choosing it on this table. Both are therefore declared as ARMS of one record, each
with the same hurdle, and the ledger carries two rules, not one:

    ARM T (trend):    long UP, short DOWN          — the rule asked for; §2a predicts it fails
    ARM C (contrary): long DOWN, short UP          — the rule §2a suggests; in-sample-motivated

The universe is 1,573 names; the 24 windows are 1.5% of it and are reported separately, so an
ARM C result is read on names its motivation never saw. **Which arm(s) to run is the principal's
decision and is recorded here before the runner is written.**

## 3. The rule, declared by the principal (2026-09-10), and not searched

Superseding the two arms sketched above: the principal gave an entry condition and an exit
overlay in his own words, and this is what is tested. §2a is disclosed but did NOT shape it —
that table is per-bar state with no exit rule, and an ATR stop and target change the return
distribution entirely, so it is a weak prior here rather than a determinant.

**ENTER** at the close of bar `e`, when at that close

- both lines are drawn ("an agreement between support and resistance");
- their gradients have the SAME sign and both exceed δ;
- they are SIMILAR: `|g_sup − g_res| ≤ τ · max(|g_sup|, |g_res|)` — the channel is roughly
  parallel, "the gradient is similar in trend up or down";
- the `keep_v2` floor holds at `e`.

Long if both rise, short if both fall. Entry price is `close[e]`; the first bar at risk is
`e+1` — the repo's `score[:, t-1] → held at t` convention exactly. `τ` is the one quantity the
principal did not fix; **{0.25, 0.50, 1.00} is declared here, 0.50 is the headline**, and the
grid is 3 × 3 = 9 cells with the target below (R13).

**EXIT** on bars `e+1` onward, whichever comes first:

| | long | short |
|---|---|---|
| TARGET | `high ≥ resistance + m·ATR` | `low ≤ support − m·ATR` |
| TRAIL | `low ≤ support − 1·ATR`, ratcheting **up** only | `high ≥ resistance + 1·ATR`, ratcheting **down** only |
| GONE | neither line is drawn any more | same |
| EOD | the name's last bar | same |

`m ∈ {1, 2, 3}`, headline 2 — "a tp 1-3 ATR above resistance". The trail is the principal's
"trailing loss 1 ATR below the support line": the support line moves with its own gradient, so
the stop moves with it, and it never loosens. ATR is a 20-bar trailing mean of true range
(D412's convention), read at `u−1`. A stop and a target inside the same bar scores as the
**stop** (the bar's path is unknown at daily resolution); a gap through a level fills at the
open, not the level.

**"Keep going with only one."** The exit fires on GONE only when *neither* line is drawn; while
one survives the trade continues, using that line for its half of the rule and the other side's
last drawn segment, frozen, for the other. The frozen cell couples the two sides
(`pairbreak`/`pairdraw` on), which would make GONE fire at the first break and leave the
target and trail nothing to say — so two construction variants are run and both reported:

- **INDEPENDENT** — `pair_break = pair_draw = off`, the sides live and die separately. This is
  the principal's rule as stated, and it is the **headline**.
- **PAIRED** — `CELL_FINAL` exactly, the control.

Nothing else in the construction is touched. A name is long or short but never both, and a new
entry can only occur after the previous trade on that name has exited.

**Universe.** The whole `us_shorts_daily_raw` ragged panel (1,573 names), the construction run
from each name's first bar, states read only where D343's `keep_v2` floor holds at `t-1` (raw
close ≥ $5, dollar volume at or above the 28th percentile, DV finite). GME included — its window
was the construction's first ground truth, but the trading rule never saw it; it is one name of
1,573 and is reported separately as a check.

**Two lenses, never compared on the same statistic (FINDINGS §10):**

- *Path-invariant, per trade.* A trade is one entry to its exit on one name. Its return is
  `dir × (log(exit/entry) + Σ dividend component over held bars)`, where the dividend component
  is `total_log_returns − log_returns` from the panel — so a dividend pays a long and costs a
  short (D280's inversion, asserted by `[S]`). Gross, and net of the round-trip spread charged
  once. Every trade counts; there is no slot cap.
- *Path-variant, the book.* Equal weight `1/n_live` across every name in position each bar (the
  panel's pooled convention), long and short legs pooled and also reported separately, scored by
  `ragged_panel.score` at `rf = 4%`, `borrow = 3%`, 252 bars a year. **The book cannot represent
  an intrabar fill**: it holds close-to-close over the same bars, so it is the same trades with
  close-only exits. That difference is stated rather than hidden, and it is why the two lenses
  are never compared on the same statistic.

**The split guard.** The daily fixture is not split-adjusted. Any trade spanning a single-bar
`|log return| > 0.40` is rejected as an unadjusted split, the same threshold the D399 sample draw
used, and the count is reported rather than hidden.

**Cost.** Fee 0. The spread of the names HELD, Corwin-Schultz off their own OHLC
(`d285_spread_estimate.corwin_schultz`), averaged over held bars — never an assumed figure. Net
per-trade return = gross − the held-name spread (one round trip). Breakeven spread = the gross
mean per trade, reported beside it.

## 4. The statistic, and the hurdles, committed

**Primary:** the GROSS mean log return per trade, long trades and short trades SEPARATELY.
A side is a signal if (i) its gross mean per trade is positive — for the short side, the return
is signed so that a fall pays positively — and (ii) it exceeds the null's p95 by more than
2 bootstrap SE of that p95 (D373's rule; a margin within 2 SE is UNRESOLVED, not a pass).

**Secondary:** the book's net bp/bar per side against the same null; both sides' gross mean per
trade vs its median (a mean below its median is the tell that a tail is doing the work, D285);
the 1%-both-tails trimmed mean beside the raw one.

**The null (R7):** a within-name time rotation of each name's OWN position series
(`fast_null.rotation_null`), which keeps the trade count, the holding lengths and the turnover
of every name and destroys only the timing — the construction's claim is timing. `n_sims = 300`,
seed 0; p50 and p95 reported with the p95's bootstrap SE (1,000 resamples of the 300). The null
runs on the SAME `keep_v2` mask as the observed positions (`fast_null.NullContext(mask=...)`), so
it cannot trade the sub-$5 tail the observed book cannot (D347/D351).

**Falsification, stated now:** a side whose gross mean per trade is at or below the null's p50
has no timing content in this rule and this record says so; a side that clears gross and fails
net names its breakeven spread and stops there. Only the principal closes an avenue; this record
reports.

## 5. Predictions, checkable, from the record's own quantities

P1  Long trades outnumber short trades by more than 2:1. (US equities 2010–2026; rising channels
    are the common case, and the entry needs a *parallel* channel, which a panic rarely draws.)
P2  Median holding is 5–20 bars, SHORTER than the channel's own median life of 9–10, because the
    trail exits before the channel does.
P3  The trail (`stop`) is the modal exit and accounts for more than half of all exits; `target`
    is under 20%. The stop sits 1 ATR from a line that hugs the swing extremes, the target 2 ATR
    beyond the far side of the channel, so the near barrier is far nearer.
P4  The held names' Corwin-Schultz round-trip spread is 20–60 bp. (D285's held names measured
    33.8 bp/side on a similar floor.)
P5  Fewer than 5% of trades are on GME.
P6  From §2a, the short side's gross mean per trade is NEGATIVE. Stated from 24 in-sample
    windows; if the universe contradicts it, those windows were not representative and that is
    itself the finding.

**A prediction is checked and reported before any result is read as evidence.** P3 in particular
is a design check, not a hope: a rule whose target never fills is a stop-loss study wearing a
target's clothes, and if P3 comes in at the extreme (target under 5%) the honest reading is that
the exit is a trailing stop alone and the target multiple is decorative.

A prediction outside its band is reported as such before any result is read as evidence.

## 6. Assertions the runner must carry

1. **Lag audit** — a second implementation re-derives `pos[:, t]` from the per-name state
   arrays at `t-1` by a separate code path that never calls the position builder, and asserts
   equality; plus the `[L]` truncation audit on a sample of names inside the runner.
2. **Sign audit, in money** — the name-bar with the largest positive `total_log_returns` inside a
   long position must add to the long leg's gross and subtract from a short position's; a
   dividend bar must move a long and a short oppositely (`assert_dividends_match_loader`).
3. **Right-quantity** — the compounded per-trade return grid must differ from the per-bar grid it
   was not meant to score, and `NullContext.assert_matches_scorer` is called once on the real book
   before any null.
4. **Non-vacuity** — the null's observed book has ≥ 100 trades on each side and the lag audit
   compared ≥ 1,000 name-bars; an audit that checked nothing has passed here before.
5. **Universe** — every null position satisfies the observed `keep_v2` mask (asserted, not
   assumed).

## 7. Runtime, stated before launch

`recalc_pair` is pure Python: measured 0.4 s per name over ~4,000 bars, so 1,573 names ≈ 10 min
serial. GIL-bound → 8 subprocesses over `symbols[i::8]`, chunk == whole asserted bit-identically
on two names first; projected ≈ 2 min. Nulls on `fast_null` (numpy, threads) — 300 sims on one
book measured ~30 s. Total under 5 minutes.

## 8. What this record will NOT do

It will not vary a single dial of the construction, try a second entry rule, add a stop, a
target or a holding cap, or filter by anything. If the rule as declared fails, the next record
starts from the failure, with this one's search added to the ledger.
