# D421 — the three depth conditions, both lenses

**Status:** design and bar committed BEFORE the runner exists (R8). Result separately.
**Date:** 2026-09-10
**Area:** Strategy research · the candidate

**Number.** `D421`, by PICKUP's three-command procedure: D400–D420 used, `D407–D410` reserved
(`044f839`), `D390–D399` reserved for `worktree-signal-hunt-part2` (`945cbb5`, live 15 hours ago).
Master takes D421.

**The principal's standing decision holds:** no holdout until there is a tradeable indicator.

**This is the [draft](DRAFT-capturing-the-deeper-zone.md), made a pre-registration at the
principal's instruction: *"run all three depth studies on both path variant and invariant lens."***

---

## 1. Why, in one paragraph

Five results point at one population — later touches (D412/D413), the deepest collapses (D416),
closes through the zone (D418), and D420's re-entries at **+16.70 bp against +9.47** — and every
exclusion rule tried removes it. The deeper zone is the better trade and it is identifiable at
the touch. This tests three ways of naming it, as **selection conditions** on D413's unchanged
trade: entry at the touch-day close, five-bar hold, no stop.

---

## 2. THE THREE DEFINITIONS — code, committed with this record

The flags are computed by `scripts/d421_depth_flags.py`, committed alongside this file. **It reads
no outcome** — it walks each name's zones in touch order and attaches three flags per event. The
runner imports it; nothing is re-implemented in prose.

| | condition | parameters |
|---|---|---|
| **DEEP-1 — re-entry** | the zone was alive during the name's previous trade (`a_k ≤ last_exit`) — D420's classification | none |
| **DEEP-2 — breach above** — **PRIMARY** | a **higher** same-side zone on the name was touched within the last 60 sessions **and its far edge traded through** on or before this touch day | none beyond the zone life |
| DEEP-3 — stack depth | distinct prior zones on the name touched in the trailing 20 sessions: **1 / 2 / 3+** | the 20-session window |

**Primary is DEEP-2** because it is the principal's structural framing — the stack above has
*failed* and this is the next level down — and because it is the one definition D420 did not
already look at.

### 2a. Stage 0, computed before this was written — facts, not predictions

```
                                pooled     cell 2
DEEP-1  re-entry                 51.8%      72.0%      == D420, exactly: the module reproduces its classification
DEEP-2  breach above             38.8%      55.3%
DEEP-3  stack 1 / 2 / 3+     32.5 / 30.4 / 37.1    30.6 / 31.4 / 38.0
overlap  DEEP-2 within DEEP-1  53.0%      DEEP-1 within DEEP-2  70.8%
```

**The two structural definitions are genuinely different:** 29% of breach-above events are first
entries (the zone above was breached, its trade closed, and this deeper zone armed afterwards).
The stack buckets split the events into near-thirds, so the shape test has equal power per rung.

---

## 3. THE ARITHMETIC, stated before the bar

- Pooled, a DEEP-1 event pays +16.70 gross against ~27 bp: **0.6× coverage** — better than 0.41×,
  not tradeable. In cell 2, +31.04 against ~23: **1.35× per trade.**
- **Selection does not reduce turnover on a full book** (D420 §3). Its only lever is gross per
  trade. A *requirement* thins the pool as well, and that is the second lever (§5).
- **Nothing here is out of sample.** D420 found the re-entry premium on this fixture. What this
  can add: whether depth *scales*, what the structural definition adds, what the *book* does with
  depth, and whether the premium is in **both halves** of the sample — the base edge was not.

---

## 4. THE PER-TRADE LENS

| | condition |
|---|---|
| **T1** | `mean(r_base | DEEP-2) − mean(r_base | not DEEP-2) > 0` by **2 SE** |

Reported beside it, no gate: the CLAUDE.md distribution for both populations (mean, median, win,
symmetric 1% trim); the same split for DEEP-1 (known, +7.22); DEEP-3's three buckets and whether
they are **monotone**; the cell-2 stratum; and **a per-year table with a first-half / second-half
split (2010–2017 / 2018–2026)** — the robustness question that matters most, never looked at.

---

## 5. THE BOOK LENS — D419's simulator, three seeds, FIXED exit

| book | slots | refill order |
|---|---|---|
| FIXED | 50 | cell 2, then random — D419's book, reproduced bit-identically before any depth book runs |
| **DEEP2-PRIORITY** | 50 | **DEEP-2 first**, then cell 2, then random |
| DEEP2-REQUIRED | 50 | pool restricted to DEEP-2 events; same order within |
| DEEP1-PRIORITY, DEEP3(≥2)-PRIORITY | 50 | shape |
| cell-2 FIXED / DEEP2-PRIORITY / DEEP2-REQUIRED | 10 | the secondary |

| | condition |
|---|---|
| **T2** | DEEP2-PRIORITY **net** bp/bar exceeds FIXED's net by **2 SE**, monthly block bootstrap, mean over seeds |
| **T3** | it exceeds the **p95 of a random-priority control** — the same *number* of events promoted to the front of the queue, chosen at random, 50 draws — margin outside 2 SE of that p95 (D373) |

A priority rule on a capacity-bound book changes selection whatever it prioritises; the rule must
beat a random one. `[RECON]`, `[CHUNK]` and the bit-identical FIXED reproduction are inherited.

**The REQUIRED books are reported and not gated**: utilisation, turnover, cost per bar, gross,
net. They are the "trade less" lever D419 and D420 both pointed at, and §5a says what they would
have to show.

### 5a. The cell-2 secondary, and the bar for calling this a candidate

The cell-2 ∩ DEEP-2 books carry the same T1–T3 at 2 SE, labelled secondary, unable to clear D421
alone. **Declared now, so it is not written afterwards:** this construction becomes a candidate
for the holdout under the principal's rule only if **the cell-2 DEEP2-REQUIRED book is
net-positive, beats its random control, and the per-year table shows the depth premium in the
second half of the sample.** Short of all three it is a better-understood construction that is
still not tradeable.

---

## 6. Predictions

| | prediction | confidence |
|---|---|---|
| **X-b** | **DEEP-2 pays more than DEEP-1**: +20–25 bp pooled against +16.70 — a breached zone above is deeper than a touched one | moderate |
| X-c | DEEP-3 is **monotone**: 3+ > 2 > 1 | moderate |
| X-d | the DEEP2-PRIORITY 50-slot book raises gross per trade toward +18 and net by ~+0.5 bp/bar, **still net-negative** | moderate-high |
| **X-e** | **the cell-2 DEEP2-REQUIRED book is net-positive, inside 2 SE of zero** | low-moderate |
| **X-f** | **the depth premium is present in both halves of the sample**, unlike the base edge | low |

(X-a is a fact — §2a — and is not predicted.) **X-e and X-f are the study**: X-e is the prize and
X-f is whether the prize is real.

---

## 7. What this does not do

- **No holdout read.** No 15m data. No exit rule. No change to the entry price or the hold.
- **No sweep.** Three definitions, one primary, one window parameter in the shape arm.
- **Does not claim independence from D420.** §3.
- **Does not recommend a disposition.** That is the principal's.

---

## 8. R13

Twenty-first look by object on price levels; the first on the candidate's *selection* since
ADDENDUM 2 chose cell 2. **Every one of the twenty before it has failed its bar.** No new data
spent.

**Cost: minutes; the 50-draw controls are projected before they run.**
