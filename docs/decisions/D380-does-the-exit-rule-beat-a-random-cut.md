# D380 — does the exit rule beat a random cut of the same trades? The R7 control D235 needed

**Date:** 2026-09-08
**Kind:** **SIGNAL TEST (R15), on an OVERLAY.** Governed by [R7](../RULES.md#r7). Admits nothing, reads no holdout.
**Pre-registered under R8 — committed before the runner exists. Result committed separately.**
**Completes:** [D378](D378-RESULT-the-entry-day-does-matter-and-it-survives-losing-its-best-trade.md) §7,
which excluded exits by design and said why.

---

## 0. Why this record exists, and why it is a separate study

The principal asked whether **entry and exit** timing could raise per-trade return.
[D378](D378-RESULT-the-entry-day-does-matter-and-it-survives-losing-its-best-trade.md) answered the
entry half: **yes** — +15.98 bp per trade at +26.9 SE, surviving leave-one-out at +9.8 SE — and it
deliberately did not touch exits, because **[R7](../RULES.md#r7) requires a different control and
bundling the two would repeat a known error.**

> **R7:** a study that applies an **overlay** — a stop, a target, a partial exit, anything modifying
> positions a base rule already chose — must be controlled against a null that **keeps the base book
> and randomises only the overlay's decisions, matched on how many it makes.** A rotation null is the
> wrong control here.

**D235 is the precedent and the warning.** Seven stop and target overlays all beat their baseline and
all cleared a pre-registered **rotation** null — at a p95 of **−0.284**, a bar anything not actively
harmful would clear. Against the correct control — **cutting the same 146 of 1,124 trades short at
random bars** — the best overlay landed at the **63rd percentile**, with the median random-exit book
at +0.785 against the real +0.794. **The trigger carried no information at all.**

---

## 1. What is frozen

**D373's primary cell, inherited unchanged**, as D374/D376/D377/D378 all inherited it: a fresh `rev_5`
dip inside the `mom_252_21` top decile, long, next-open fill (D340), hedged against the floored
market, **40-bar cap**. Cell **10:90 / cap 40**, mining prefix only.

`[MIR]` must reproduce **3,932 trades, 796 names, gross mean +160.55, median +51.55** before anything
else runs.

**Hedge convention: H0**, the incumbent, for the same reason D378 used it — `[MIR]` against D373's
committed numbers is otherwise impossible. **The headline is reported under D377's H1 beside it.**

**The entry set is fixed and identical under every rule tested here.** An exit rule changes *hold
lengths*, never *which trades exist*, so **the trade count stays 3,932 under every arm** and the
per-trade comparison is like-for-like by construction. `[OVL]` proves this rather than assuming it.

---

## 2. The overlays

| | rule | free parameters | |
|---|---|---|---|
| **E0** | the incumbent **40-bar cap** | none | baseline |
| **E1** | **signal invalidation** — exit when the name's own `rev_5` percentile reverts past 50, capped at 40 | **none** | **PRIMARY.** The kernel's own `("invalidation", 40)`; the exit a dip entry ought to have |
| **E2** | **profit target** at **+200 bp** cumulative hedged, capped at 40 | one, **declared here** | exploratory |
| **E3** | **stop** at **−200 bp** cumulative hedged, capped at 40 | one, **declared here** | exploratory |

**E1 is primary because it has no free parameter and therefore no search.** It is also the exit
`CLAUDE.md` singles out: *"check what the exit keys on — D285's fired on displacement by unrelated
names, not on its own signal reverting."* E1 keys on the name's own signal reverting, which is the
version worth testing.

### AMENDMENT to §2, 2026-09-08 — **`[OVL]` fired. "Invalidation" names two different objects and only one of them is an overlay.**

*Written before any result, under §9's instruction: "`[OVL]` fails → what is being tested is a
different book, not an overlay, and R7 does not govern it. **Re-scope before running.**"*

**The kernel's `("invalidation", 40)` run does not share the baseline's entries.** Measured:

| | |
|---|---:|
| signal events in the cell | **10,270** |
| baseline trades (40-bar cap) | **3,932** |
| **kernel invalidation trades** | **7,945** |
| entries in both | 3,810 |
| **only in the invalidation run** | **4,135** |
| mean hold, shared entries | baseline **39.94** · invalidation **6.32** |

**The cause is re-entry, not the exit.** Under a 40-bar cap a signal firing while the name is still
held is suppressed; exiting at a mean of 6.32 bars frees the name to take signals the cap swallowed.
**Invalidation more than doubles the book.**

**So the record must separate two objects that share a name:**

1. **E1, THE OVERLAY — what this study tests.** Apply the invalidation condition to **the baseline's
   own 3,932 trades**, cutting early, **allowing no new entries**. Trade count fixed, `[OVL]` holds,
   and **R7's matched-count control is the right control**.
2. **The full invalidation BOOK — a different construction.** 7,945 trades, mean hold 6.32. **R7 does
   not govern it**, a random-cut control would be meaningless for it, and it needs a rotation or
   cohort control of its own. **It is REPORTED here with NO control and NO verdict**, and it is owed
   its own pre-registration.

**The re-cut is validated against the kernel rather than trusted.** On all **3,810 shared entries**
the re-cut invalidation hold equals the kernel's, **zero mismatches** — so object 1 uses the kernel's
own exit logic, re-applied without re-entry. `[CUT]` covers the arithmetic; this covers the rule.

**This is not a loosening.** The pre-registered question — *does the exit rule beat a random cut of
the same trades* — is answerable only about object 1, because object 2 has no "same trades" to cut.
**Object 2 is the more interesting candidate** and D378's front-loading result points straight at it;
that is a reason to pre-register it properly, not to smuggle it in here without a control.

**E2 and E3 are exploratory and priced as such.** Their ±200 bp thresholds are **declared in this
record**, round, symmetric, and roughly the observed mean per trade — **not swept**. Any claim
resting on all three is scored against a **best-of-3 floor** (the max over the three rules within
each draw); E1's own claim carries no such floor because nothing was selected to reach it.

---

## 3. The control — R7's, not a rotation

> **For each rule E_k: keep the base book. Take exactly the trades E_k shortens, keep that set and
> that count fixed, and cut each of them at a bar drawn uniformly from its own available window
> `[1, hold_E0)`. Randomise nothing else.**

This is D235's corrected control, and it is deliberately the **harder** version: it **grants the rule
its trade selection for free** and asks only whether it cut at the right *bar*. That isolates exit
**timing**, which is the question.

**Reported beside it, and looser:** a control that also re-draws *which* trades are cut, at the same
count. If E1 beats the loose control and fails the strict one, the rule is picking trades and not
bars, and the record will say exactly that.

**Each rule gets its own control with its own N**, because a target fires on a different number of
trades than an invalidation does. **A control matched on the wrong count is not matched** — R7's
whole point, and `CLAUDE.md`'s: *matched-count ≠ matched-turnover ≠ matched-volatility.*

**Draws: 2,000**, five parts × 400, keyed `default_rng([SEED, 380, ARM, draw])`.

---

## 4. How it is computed, and the one place that is exact and the one that is not

**Per-trade paths are stored once and re-cut.** The baseline exports each trade's per-bar hedged
return, exactly as D365 exported `d365_trade_paths_95_80.csv.gz` and D373's segmentation probe
re-cut them. Every rule and every control draw is then a **re-cut of the same stored paths** — no
kernel re-run per draw.

- **The per-TRADE lens is EXACT under re-cutting.** A trade's P&L is the sum of its own path to
  whatever bar it ends on; nothing about it depends on what else the book held.
- **The per-BAR deployed lens is NOT.** An earlier exit frees a slot, which changes what the book
  holds next, which changes every subsequent bar. **Re-cut paths cannot produce a valid deployed
  series.**

**So:** the primary statistic and all 2,000 control draws are per-trade, from re-cut paths.
**The deployed book is reported only for E0 and E1, from a genuine kernel re-run**, and is never
compared to a control draw. Stated here so the limitation is a design choice and not a discovery.

`[CUT]` asserts the re-cut baseline reproduces the kernel's own per-trade P&L to < 1e-9 before any
rule is applied — the analogue of D377's `[REC]`, which caught a real specification error at 1e-3.

---

## 5. The hurdles

| | hurdle | |
|---|---|---|
| **U1** | **E1's gross mean per trade > its strict control's p95**, by more than 2 SE | **PRIMARY. The study's question.** |
| **U2** | **U1 with the largest trade removed** | **GATE.** D373's H1 died on one trade; D378 pre-registered leave-one-out and it passed. It stays a gate |
| **U3** | *reported* — the same comparison on the **median** per trade, and against the **loose** control | where the gain lives, and whether it is trade selection rather than timing |
| **U4** | *reported* — **what the exit keys on**: the share of exits fired by the trigger vs by the 40-bar cap, and the hold-length distribution under each rule | `CLAUDE.md`'s D285 lesson. **An overlay that almost never fires is not an exit rule** |
| **U5** | *reported* — E2 and E3 against their own controls, and against a **best-of-3 floor** | exploratory, priced |

**U1 and U2 must both hold for E1 to be said to work.** Everything else is reported.

**Cost is not a gate** (R15) and is reported: each rule's mean holding run, turnover per bar, implied
round trips per year, and the gross-per-trade figure against the measured round trip under **both**
PB and PUB — because D378 showed that which convention holds decides whether an effect this size is
deployable at all.

---

## 6. Assertions

| tag | what it proves |
|---|---|
| **`[MIR]`** | the baseline reproduces D373's committed 3,932 / +160.55 / +51.55 |
| **`[CUT]`** | the re-cut baseline reproduces the kernel's own per-trade P&L to **< 1e-9**; the actual max deviation is reported, not merely compared to the bound (§4) |
| **`[OVL]`** | **this is an overlay and not a different book**: entries identical to E0, trade count identical, and **every trade's hold under E_k ≤ its hold under E0**. A rule that lengthens a trade is not an overlay |
| **`[R7]`** | the control keeps the base book and cuts **the same trades**, at the **same count**, at bars drawn from each trade's **own** window — asserted per draw, not sampled |
| **`[FIRE]`** | the count of trades each rule actually shortens is reported per rule, and the runner **refuses** to report a rule that fires on **fewer than 1%** of trades: its control would be matched on almost nothing |
| **`[DIR]`** | the HIGH tail: a duplicated ledger outranks a zeroed one |
| **`[X]`** | **the one that matters** — every audit above must **RAISE** on a deliberately broken book, including a "control" that cuts a *different* set of trades than the rule did, and an overlay that *lengthens* a trade |

**Persist before rendering.**

---

## 7. The search cost

**E1 carries none** — no free parameter, no cell selection, the exit already in the kernel. **E2 and
E3 carry one declared threshold each**, fixed in §2 before the runner exists and not swept; any claim
spanning all three is scored against a best-of-3 floor. Under [R13](../RULES.md#r13) this adds **one
look** to the winners'-dip ledger, disclosed, on a fixture already spent.

**Authorisation.** D378's reopening authorised **one** test and this is not it. **This study needs
the principal's own authorisation**, and this record does not presume it — it is a pre-registration
sitting ready, not a licence.

---

## 8. Predictions

**Five studies running now — D373, D374, D376, D377, D378 — have had my direction right more often
than my magnitude. Here I expect to be wrong about the direction of the headline, and I am saying so
first.**

| | prediction |
|---|---|
| **Q1** | **AGAINST my own proposal: U1 FAILS.** E1 does not beat a random cut of the same trades. **The mechanism:** D378 measured the edge decaying *smoothly in time* — 7.82 → 6.86 → 6.12 → 4.02 → 3.94 bp per bar. **A smooth time decay means any cut at a similar average bar captures similar value**, so the *state* the rule keys on adds little beyond the *time* it implies. If that is right, this is a closing result |
| **Q2** | E1's mean **holding run is materially shorter** than 40 — under **25 bars** — so it is a real overlay and not a rule that never fires |
| **Q3** | E1 **beats the LOOSE control while failing the STRICT one**, i.e. it picks *which* trades to cut better than it picks *when* — the split U3 exists to expose |
| **Q4** | E1's **gross mean per trade falls below E0's +160.55**, because a shorter hold collects fewer bars even at a better rate (D378's two lenses), while its **bp per bar rises above E0's +4.02** |
| **Q5** | **the trigger fires on more than half of trades** — an invalidation exit on a mean-reverting entry should be the binding exit more often than the cap |
| **Q6** | **E2 and E3 both fail their own controls**, and the best-of-3 floor makes the joint claim worse than E1's alone |
| **Q7** | `[CUT]`'s max deviation is **below 1e-12** — the re-cut is a sum of the same addends in the same order, unlike D377's `[REC]`, which had a genuine association-order difference |

---

## 9. What would make me abandon this

- **`[CUT]` fails** → the re-cut does not reproduce the kernel; stop, fix, publish nothing. D377's
  analogue fired at 1e-3 and found a real specification error.
- **`[OVL]` fails** → what is being tested is a different book, not an overlay, and R7 does not
  govern it. Re-scope before running.
- **`[FIRE]` refuses a rule** → it shortens under 1% of trades and its control is matched on almost
  nothing. Report that instead; a rule that never fires cannot be tested.
- **U1 fails and U3 shows the loose control also beats E1** → the rule adds nothing at all, at either
  margin. **That is a clean closing result on exits and should be written as one**, not softened.

---

*Pre-registered 2026-09-08. Runner does not exist at the time of this commit (R8). **Not authorised
to run** — D378's reopening covered one test and this is a second.*
