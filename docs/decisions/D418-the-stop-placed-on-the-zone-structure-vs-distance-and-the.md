# D418 — the stop placed on the zone: structure vs distance, and the entry-validity filter it implies

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D418-the-stop-placed-on-the-zone-structure-vs-distance-and-the-validity-filter-it-implies.md`. The H1 above is the full title.*

**Status:** design and bar committed BEFORE the runner exists (R8). Result separately.
**Date:** 2026-09-10
**Area:** Strategy research · execution

**Number.** `D418`, by PICKUP's three-command procedure: D400–D417 used, `D407–D410` reserved
(`044f839`), `D390–D399` reserved for `worktree-signal-hunt-part2` (`945cbb5`, live 14 hours ago).
Master takes D418.

**The principal's standing decision holds:** no holdout until there is a tradeable indicator.

---

## 1. What this asks, and why it is not D417 again

[D417](D417-RESULT-no-exit-beats-the-time-stop-because-the-expected.md)
anchored its stop on the **entry price** — `entry − a·ATR` — and found that conditional on being
1.5 ATR down, the expected remaining move is not negative, so the stop forfeits it. **This anchors
the stop on the ZONE.** For a demand trade the stop sits at the zone's far edge, `lo_u`: a close
through the zone is the thesis invalidated. The conditional being tested is different — *given
price has breached the level the trade was built on, is the remaining move negative?* — and it
has a mechanism behind it, which D417's did not.

It also has a reason to doubt it in the record already: D412 and D413 found levels are not
consumed on contact and later touches pay *more*. A breach may not mean what the thesis says.

**Daily arm only.** D417 §5 showed intraday triggering moves stop fills by under a basis point and
flips no sign; resolution cannot answer a placement question.

---

## 2. TWO THINGS THE STRUCTURE IMPLIES THAT D417 DID NOT HAVE

### 2a. An entry-validity condition, knowable at `t`

The entry is the touch-day close. On many events — cell 2's especially, where D414 found the
momentum runs through the close — that close is already **through** the zone's far edge. Under a
structure stop those trades cannot be entered: the stop is breached before the trade exists.

**So the rule is a filter as well as a stop, and unlike D416's stall filter this one is knowable
at the moment of entry.** Whether the events it excludes are the good ones or the bad ones is a
gate of its own (§4, T3), and it may matter more than the stop does.

### 2b. The control that separates the ZONE from the DISTANCE

A structure stop sits at *some* distance from entry on every event, and D417 showed tighter ATR
stops are monotonically worse. "The stop at the zone edge underperforms" would say nothing unless
it underperforms **a stop at the same distance that is not at the zone.** The control is the LVL
move applied to stops:

> For every entered event, the structure stop's distance in ATR units, `d_i = (entry_i − stop_i) /
> ATR_i`, is **permuted across entered events within side**, and the control stop is placed at
> `entry_i − d_{π(i)} · ATR_i`. Same walker, same fills. The distance distribution is preserved
> exactly (`[MATCH]` holds by construction); the link to the zone is destroyed.

**Rule minus control is what the zone knows beyond how far away it is.** 50 permutations; each
event's control return is averaged over draws, and the paired delta is taken per event.

---

## 3. THE CONSTRUCTION

D413's 180,050 resolved touches, unchanged; entry at the touch-day close `C[t]`; the time stop at
the close of `t+5` in every arm; cell-2 flags at ADDENDUM 2's median cuts. Path-invariant.

**Three stop placements, one primary.** For a demand zone `[lo_u, hi_u]` (long); supply is the
mirror via `sign`.

| | stop at | what it is |
|---|---|---|
| **ST-edge — PRIMARY** | `lo_u` | the zone's far edge: the thesis invalidated |
| ST-mid — shape | `(lo_u + hi_u) / 2` | halfway through the zone |
| ST-buf — shape | `lo_u − 0.25·ATR` | a small buffer beyond the edge, the usual practice |

**Entry validity:** the trade is entered only if `sign × (C[t] − stop) > 0`. Events failing this
are **dropped**, per variant, and their fixed-exit return `r_base` is reported.

**Fills:** D417's conventions inherited — at the trigger unless the day's open is already through
it, then at the open; the stop is checked against the day's low from `t+1` to `t+5`; `[FILL]`
asserted on every exit. **No take profit is paired with any stop** — D417 found the target neutral.

```
r_stop     = sign × (log P_exit − log C[t])          the structure-stop trade, entered events
r_base     = sign × (log C[t+5] − log C[t])          D413's fixed exit, same events
r_ctrl     = the same trade with the distance-permuted stop, averaged over 50 draws
delta_base = r_stop − r_base                         paired, per entered event
delta_ctrl = r_stop − r_ctrl                         paired, per entered event
dropped    = r_base on the events the validity condition excludes
```

Every arm is one round trip from the same entry, so every paired delta is net of matched costs.
`early_share`, `hold`, `bp_per_day`, `std_ratio`, `max_loss`, win rate, and D417's *would-have /
filled-at* pair on the early-exited trades are reported beside every gate.

---

## 4. THE BAR — three separate questions, ST-edge, pooled

| | question | condition |
|---|---|---|
| **T1** | does the stop beat the fixed exit? | `mean(delta_base) > 0` by **2 paired SE** on entered events |
| **T2** | does the ZONE matter, or only the distance? | `mean(delta_ctrl) > 0` by **2 paired SE** on entered events |
| **T3** | is the validity condition a good filter? | `mean(r_base | entered) − mean(r_base | dropped) > 0` by **2 SE** (unpaired) |

**Each gate answers a different question and each can clear on its own.** T1 without T2 is D417's
finding at a different distance. **T3 is the one that would be usable if it cleared** — a
structure-derived entry condition, knowable at `t`, independent of any stop. Three tests at 2 SE
is three chances, stated.

**Cell 2 is the declared secondary** with the same three tests, unable to clear D418 on its own.

---

## 5. Stage 0

| | check |
|---|---|
| **P1** | counts reproduce; **the drop share per variant**, pooled and cell 2; the structure stop's distance from entry in ATR units, p10/50/90 — how tight the zone stop actually is |
| **P2** | `[MATCH]` — the control's ATR-unit distance distribution equals the rule's to `0.0e+00` |
| **P3** | D417's SL 1.5 on the **same entered events**, for reference: is the zone stop tighter or looser than 1.5 ATR, and does it do better or worse than an ATR stop on the events it can enter? |
| **P4** | **look at the object** — one cell-2 event end to end: zone, entry, stop, the path, the exit, the control's stop and exit |

---

## 6. Predictions

| | prediction | confidence |
|---|---|---|
| **X-a** | the edge stop's median distance is **0.8–1.2 ATR** — tighter than D417's 1.5 — because the touch-day close usually sits inside the zone | moderate |
| **X-b** | **25–45% of events are already through the edge at the close** and are dropped; **more in cell 2** than pooled, because D414 found cell 2's momentum runs through the close | moderate |
| **X-c** | **T1 fails** — tighter is worse (D417's monotone), and the breach conditional does not rescue it | moderate-high |
| **X-d** | **T2 fails** — placement at the zone adds nothing beyond its distance; `\|delta_ctrl\|` inside 2 SE | moderate |
| **X-e** | **T3 passes pooled** — the events whose close is already through the zone have a lower fixed-exit return than the ones still on the right side of it: a breach at the close is the continuation, and requiring the close to hold is a good filter | moderate |
| **X-f** | in cell 2 the filter's effect is larger — the entered subset's baseline exceeds +30.26 by more than 5 bp | low-moderate |

**X-e is the study.** If the zone's far edge carries no information as a stop (X-c, X-d) but does
as an entry condition (X-e), then the structure's use is in *deciding whether to take the trade*,
not in *where to leave it* — and that would be the first structure-derived condition in this line
that is both knowable at entry and worth something.

---

## 7. What this does not do

- **No holdout read**, by the principal's standing decision. No 15m arm (§1).
- No book, no slot cap. **No sweep** beyond the three declared placements. No take profit.
- **Does not recommend a disposition.** That is the principal's.

---

## 8. R13

Eighteenth look by object on price levels; fifth on execution; no new data spent.

**Cost: seconds on a fixture already on disk.**
