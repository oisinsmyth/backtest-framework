# D419 — the three exits through the path-variant lens: what a freed slot is worth

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D419-the-three-exits-through-the-path-variant-lens-what-a-freed-slot-is-worth.md`. The H1 above is the full title.*

**Status:** design and bar committed BEFORE the runner exists (R8). Result separately.
**Date:** 2026-09-10
**Area:** Strategy research · execution · the book

**Number.** `D419`, by PICKUP's three-command procedure: D400–D418 used, `D407–D410` reserved
(`044f839`), `D390–D399` reserved for `worktree-signal-hunt-part2` (`945cbb5`, live 14 hours ago).
Master takes D419.

**The principal's standing decision holds:** no holdout until there is a tradeable indicator.

---

## 1. Why D417 could not see this, and why the principal is right to push

[D417](D417-RESULT-no-exit-beats-the-time-stop-because-the-expected.md)
scored every exit **per trade**: a stopped trade forfeits ~15 bp of remaining expectation, and in
that lens the capital then sits idle. **That lens models no capital.** CLAUDE.md's own words:
*"their difference is opportunity cost, which nothing here has measured."*

**In a slot-limited book an early exit frees a slot, and the slot takes a fresh entry.** A fresh
entry's expectation is front-loaded — ADDENDUM 3's marginals, `+6.3, +9.4, +6.9, +6.1, +1.5` by
day in cell 2 — so recycling capital out of the *tail* of one trade into the *head* of another can
beat holding even when each exit is slightly negative on its own. That is the case trading
intuition makes for stops, it is legitimate, and D417 was blind to it by construction.

**The repo has been here once.** [D295](D295-RESULT-the-anti-pattern-won-and-the-book-was-pinned.md)
built a slot-and-refill simulator on a different signal and found **0 of 19 exit cells cleared**;
the profit target came closest (+4.95 bp/bar, beat its null and its floor, failed cost). FINDINGS
§10 records why most of that turnover was unpriced: the book was pinned so an exit on a
still-selected name re-entered the same name. **D413's stream is event-driven, not rank-pinned** —
a freed slot refills from *today's touches*, a genuinely different name — so the mechanism D295
could not express is expressible here.

---

## 2. THE TWO TRAPS, each with a control built in

1. **The marginal trade pays a full round trip.** Every recycle is an entry that would otherwise
   not have been taken; it earns its full return *and* pays its cost. Pooled, +13.2 gross against
   ~33 bp of neutral cost is net-negative per extra trade — the D413 arithmetic — so recycling can
   raise gross and lower net at once. **Gross and net are reported side by side and the gate is
   net.**
2. **An exit rule's nuisance on a book is turnover.** A rule that trades more refills more,
   pays more, and changes the book's composition regardless of what it knows. The control is
   D295's: **`sampled_runs`** — each position is exited after a random hold drawn from the rule's
   own realised run distribution, everything else identical. It matches turnover, cost and refill
   frequency and destroys only the rule's information. *A control must share the treatment's
   nuisance, not just its count.*

**And the swap itself is priced, not inferred** — D304's **replacement premium**: for every early
exit, what the arriving trade earned minus what the departing one would have earned to its
scheduled exit, **split by whether a replacement was available that day.** If no touch arrived,
the slot idled and the premium is `0 − forfeited`. The mechanism only works when the bench is deep
enough that a freed slot finds a fresh entry at once, and that is measured rather than assumed.

---

## 3. THE BOOK

**Candidates:** D413's 180,050 resolved touches, entering at the touch-day close. **Slots:** `N =
50` primary; `25` and `100` as shape. **Refill priority when touches exceed free slots:** cell-2
events first, then at random with a fixed seed; three seeds are run and the spread across them
reported, so the ranking's arbitrariness is visible rather than hidden.

**The bar order is D295's, and it is the correctness argument:**

```
for each day t:
  1. MARK every position held during t, once:
       if its exit rule triggers intrabar on t (OHLC of t, D417's fills)  ->  mark = sign*(log fill - log C[t-1]),
                                                                              slot free at the close of t
       else                                                                ->  mark = sign*(log C[t] - log C[t-1]);
                                                                              if age == 5 at the close, close at C[t]
  2. drop anything delisted out from under us (no price at t)
  3. REFILL freed slots from touches on day t, entering at C[t]  ->  earns from t+1
  4. book return for t = SUM of marks / N          (idle slots earn zero; per-OCCUPIED-slot also reported)
```

**`[RECON]`** — total book P&L equals total position P&L to `< 1e-9` relative, on every rule.
D295's assertion [5], the one that caught a bar credited to two positions. **`[HOLD]`** — the
no-exit book holds exactly five bars. **`[MECH]`** — the target's winning runs are shorter than its
losing runs. **`[SIGN]`** — an oracle that exits at each position's best close is strongly
positive.

**Exit rules — D417's primaries, unchanged, plus its combination as shape:**

| | rule | status |
|---|---|---|
| FIXED | time stop only, close of `t+5` | the baseline |
| **SL** | `entry − 1.5·ATR`, D417's fills | primary |
| **TS** | `best − 1.5·ATR`, trail updated at each close | primary |
| **TP** | `entry + 2.0·ATR` | primary |
| SLTP | SL 1.5 + TP 2.0 | shape |

**Costs:** every trade is charged its own name's **neutral round trip** — ADDENDUM 2's estimator,
the 60-bar trailing median Corwin–Schultz plus IBKR's per-share — at entry. `net bp/bar = gross
bp/bar − turnover × cost`.

---

## 4. THE BAR — per family, on the 50-slot book

**Scored in bp/bar on the book, never beside D417's per-trade numbers.** SEs by **monthly block
bootstrap** of the paired daily difference (1,000 resamples), because daily book returns are
autocorrelated.

| | condition |
|---|---|
| **T1** | the family's **net** bp/bar exceeds FIXED's net by **more than 2 SE** |
| **T2** | the family's **net** bp/bar exceeds the **p95 of its own `sampled_runs` control** (200 draws), margin outside 2 SE of that p95 (D373's rule) |

**Both must hold.** T1 without T2 is turnover that happened to pay on this path. T2 without T1 is
a rule that beats random exits and still loses to no exit at all. Three families is three tests at
2 SE, stated. Gross is reported beside every net; **a family that clears gross and fails net is
recorded as exactly that** — an execution improvement priced out by its own turnover.

**The cell-2 book — declared secondary.** Cell 2 alone, `N = 10`, same rules, same gates, unable
to clear D419 on its own.

**The replacement premium** is reported per family, split by *replacement available / slot idled*,
and is not gated: it is the number that says *why* a family did what it did.

---

## 5. Stage 0

| | check |
|---|---|
| **P1** | counts reproduce; **utilisation** (share of slot-days occupied) and **same-day refill share** (freed slots that found a touch that day) per book — the bench depth the mechanism needs |
| **P2** | FIXED's book: bp/bar gross and net, trades, turnover, holding run — and its per-trade mean must reconcile to D413's +13.21 on the trades it took |
| **P3** | each family's realised run distribution, from which its control is drawn |
| **P4** | **look at the object** — one slot's month printed as a ledger: entries, exits, marks, refills |

---

## 6. Predictions

| | prediction | confidence |
|---|---|---|
| **X-a** | utilisation at 50 slots is **above 90%** and same-day refill above 95% — 43 touches a day against a handful of freed slots | high |
| **X-b** | **gross:** SL and TS below FIXED; **TP above FIXED** by 0.2–0.6 bp/bar — it forfeits nothing and recycles into front-loaded entries | moderate |
| **X-c** | **net, pooled: T1 fails for all three.** The recycled trade earns +13 and costs ~33; every family's extra turnover is priced out | moderate-high |
| **X-d** | **cell-2 book: TP is net-positive against FIXED but inside 2 SE** — the recycled trade earns +30 against ~23 | low-moderate |
| **X-e** | the replacement premium for TP exits is **positive gross and near zero net**; for SL exits **negative** on both | moderate |
| **X-f** | **T2: TP beats its turnover-matched control gross; SL and TS do not** — the target's information is real (it exits *after* the move) and the stop's is not | moderate |

**X-b against X-c is the study.** If the target raises gross and loses net, the path-variant lens
has found what D417 could not — a real execution improvement — and priced it out with the same
cost arithmetic that has governed this line since ADDENDUM 2. If the target clears net on the
cell-2 book, that is the first exit rule in the programme to survive both lenses, and it would be
so because the marginal trade there is net-positive.

---

## 7. What this does not do

- **No holdout read**, by the principal's standing decision.
- No 15m data. No parameter sweep beyond D417's primaries and one shape combination.
- **Does not re-search the entry.** The candidate stream, the priority and the hold are fixed.
- **Does not quote path-invariant and path-variant on the same statistic.** D417's per-trade
  deltas and this book's bp/bar are two lenses on one question and are kept apart.
- **Does not recommend a disposition.** That is the principal's.

---

## 8. R13

Nineteenth look by object on price levels; sixth on execution; the first through the book. No new
data spent.

**Cost: a few minutes for the books; the 200-draw controls are projected and reported before they
run, per CLAUDE.md.**
