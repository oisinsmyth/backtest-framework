# D420 — fire once per episode: is a re-entry a worse trade than a first entry?

**Status:** design and bar committed BEFORE the runner exists (R8). Result separately.
**Date:** 2026-09-10
**Area:** Strategy research · execution · the book

**Number.** `D420`, by PICKUP's three-command procedure: D400–D419 used, `D407–D410` reserved
(`044f839`), `D390–D399` reserved for `worktree-signal-hunt-part2` (`945cbb5`, live 15 hours ago).
Master takes D420.

**The principal's standing decision holds:** no holdout until there is a tradeable indicator.

---

## 1. What the principal asked for, and what it can and cannot do

*"Sharpen the trade conditions so that it fires once, and if it exits it doesn't re-enter."*

[D419](D419-RESULT-the-target-recycles-capital-and-the-round-trip-prices.md) found the
book net-negative at every rule because a 20%-a-day turnover pays ~6.4 bp/bar against ~3 gross,
and closed with *"turnover, not exits, is where this line's cost lives."* A no-re-entry rule is the
natural response. **Its effect has to be stated precisely before it is measured, because it is not
the effect the words suggest:**

- **On a capacity-bound book it does not reduce turnover.** With a fixed five-day hold and a full
  book, each occupied slot turns over once in five days whatever the entry rule; cost per bar is
  `utilisation × round trip / hold`. D419's 50-slot book ran at 99.5% utilisation on 43 touches
  a day against ~10 freed slots — excluding re-entries swaps *which* names take the slots, and the
  round trips keep coming. **On the book, the rule is a selection filter.**
- **In the per-trade ledger it reduces the trade count** — and its value there is whether the
  trades it removes were worse than the ones it keeps.

**So the question is the same in both lenses: is a re-entry a worse trade than a first entry?**
And there is a reason in the record to expect the answer the wrong way. A re-entry is a name that
fell into zone A, was held five days, and then fell further into a *deeper* zone B — which is the
deep-decline population D416's late stalls and D418's through-the-zone closes found pays **more**,
not less.

---

## 2. THE RULE — parameter-free primary, a cooldown as shape

D413's zones, D413's entry at the touch-day close, D417's five-bar time stop, no other exit.

**EPISODE (primary).** *A name fires once per episode.* When a position on name `X` exits at day
`e`, **every zone on `X` that is alive at `e`** — armed at `a ≤ e`, not yet touched — **is
consumed** and can never fire. A zone armed *after* `e` starts a new episode and may fire.

```
per name, in touch order:
  event k is ENTERED   if   a_k > last_exit        (its zone was armed after the last exit)
  event k is a RE-ENTRY if  a_k <= last_exit        (its zone was alive during the last trade)
  on entry:  last_exit = exit day of that trade
```

This uses only the zone's arming day and the trade's exit day — nothing is tuned.

**COOLDOWN(K) — shape, cannot clear.** A name is ineligible for `K` days after any exit,
`K ∈ {5, 20}`. Declared so the parameter-free rule can be read against a plain clock.

**In the book lens the rule lives inside the simulator**, because whether event `j` was entered
depends on capacity: on every exit the departing name's live zones are marked consumed, and the
refill skips consumed events. In the per-trade lens every event is "entered" and the walk is the
sequential one above.

---

## 3. THE TWO LENSES — both, on separate statistics

### 3a. Per-trade

```
r_first = r_base on ENTERED events        (first entries of an episode)
r_re    = r_base on RE-ENTRY events       (what the rule throws away)
```

**T1 — `mean(r_first) − mean(r_re) > 0` by more than 2 SE (unpaired).** The rule keeps the
better trades. **If the sign is negative the rule is discarding the better trades**, and that is
recorded as the finding it would be. Reported with the re-entry share, and the trade distribution
of both populations per CLAUDE.md (mean, median, win, symmetric 1% trim).

### 3b. The book

D419's 50-slot book, same seeds, same priority (cell 2 first, then random), FIXED exit, with
EPISODE applied inside the refill. Scored in bp/bar, monthly block-bootstrap SE on the paired daily
difference.

**T2 — the EPISODE book's net bp/bar exceeds FIXED's net by more than 2 SE.**

**Control — matched-count random exclusion.** EPISODE excludes some share `s` of the events; the
control excludes a random `s` of events, drawn once and fixed, 50 draws. It matches the exclusion
*rate* and destroys the re-entry *identification*. **T3 — the EPISODE book's net exceeds the
control's p95**, margin outside 2 SE of that p95 (D373). This is the control the rule needs: a
random thinning of a capacity-bound pool changes selection too, and the rule must beat it.

**Utilisation and turnover are reported and are the check on §1's claim:** if the book stays
full and turnover stays at ~20%/day, the rule's entire effect is selection, and cost per bar does
not move.

**The cell-2 book (10 slots) is the declared secondary**, same three tests, unable to clear D420
on its own.

---

## 4. Stage 0

| | check |
|---|---|
| **P1** | the re-entry share, pooled and cell 2, under EPISODE and each COOLDOWN; the distribution of `last_exit − a_k` for re-entries — how long the consumed zones had been alive |
| **P2** | D419's FIXED book reproduces exactly (same seeds → same 40,977 trades) before EPISODE is switched on |
| **P3** | `[RECON]`, `[HOLD]` inherited; **`[ONCE]`** — no name holds two positions at once, and no re-entry event appears in any EPISODE book's ledger |
| **P4** | **look at the object** — one name's full episode history printed: each zone, its arming and touch days, whether it fired or was consumed and by which exit |

---

## 5. Predictions

| | prediction | confidence |
|---|---|---|
| **X-a** | the re-entry share is **20–35%** of events pooled and **higher in cell 2** — deep declines stack zones | moderate |
| **X-b** | **T1 fails with the wrong sign**: re-entries pay *more* than first entries, because they are the deeper-decline population | moderate |
| **X-c** | on the 50-slot book, **utilisation stays above 98% and turnover within 1 point of 20%/day** — §1's claim, measured | high |
| **X-d** | **T2 fails** — the EPISODE book's net is within 2 SE of FIXED's, because the swapped-in fresh names are no better than the re-entries they replace | moderate |
| **X-e** | **T3 fails** — EPISODE does not beat a matched-count random exclusion | moderate |
| **X-f** | COOLDOWN(20) removes more events than EPISODE and does worse than it in both lenses | moderate |

**X-b is the study.** If re-entries are the *better* trades, "fire once" is a rule that improves
the book's story and worsens its ledger, and the sharpening the principal is reaching for has to
come from somewhere else — the hold, or the entry rate. If re-entries are worse, the rule is a
real selection improvement and the only question left is whether it is large enough to move net.

---

## 6. What this does not do

- **No holdout read**, by the principal's standing decision. No 15m data.
- **Does not change the hold, the exit or the entry price.** One rule, one parameter-free
  primary, two shape values.
- **Does not claim a turnover reduction it cannot deliver on a full book.** §1.
- **Does not recommend a disposition.** That is the principal's.

---

## 7. R13

Twentieth look by object on price levels; seventh on execution. No new data spent.

**Cost: minutes; the 50-draw control is projected before it runs.**
