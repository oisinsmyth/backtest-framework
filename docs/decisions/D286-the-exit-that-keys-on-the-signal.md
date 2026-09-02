# D286 — The exit that keys on the signal

**Status:** PRE-REGISTERED. Committed **before the runner exists**. Nothing here is a result.
**Date:** 2026-09-02
**Area:** Strategy research · **personal track**

---

## Why, and it came from an objection rather than from the data

[D285](D285-the-factor-neutral-book.md) closed on hurdle B. Its persistence
diagnostic showed the edge still accruing at fifteen bars (`t` rising from 1.71
to 5.00), and my proposed response was **to hold longer**.

**The principal objected: why keep holding if the signal says the move is over?**

**It never said so.** D285's exit is *hold while the name stays in the top or
bottom N*. With N = 10 drawn from ~1,570 qualifying names, **a position exits
when ten OTHER names become more extreme.** The held name's own `hist_L` is not
consulted. It is evicted by strangers.

**That is why the persistence table looks the way it does** — the evicted names
still carry edge because the ranking removed them for reasons unrelated to their
own state. So the question is not *how long* to hold. It is **whether exiting
for the right reason is worth anything.**

**And the objection also refutes the fix I was about to pre-register.** A longer
hold collects a *falling* per-bar edge (10.70 → 6.96 bp) while adding exposure.
It raises breakeven only by amortising one round trip over more bars — **cost
accounting, not a better signal.** That distinction is now a standing note in
`CLAUDE.md`, and **this study is built to measure it rather than assume it.**

---

## The construction

Base is D285's, unvaried: **long the N lowest lagged `hist_L`, short the N
highest**, ±1 per name so the book is dollar-neutral by construction, daily
close-to-close, on `us_shorts_daily_raw.csv.gz`. **N ∈ {10, 25, 50} per leg.**

**Only the EXIT changes, and the four arms are chosen to separate the two
mechanisms the note above distinguishes:**

| arm | exit fires when | what it is |
|---|---|---|
| `disp` | the name leaves the top/bottom N — **D285's rule** | the **control** |
| **`sig`** | **`hist_L` crosses zero** — the long leg's score rises to ≥ 0, the short leg's falls to ≤ 0 | **EDGE-SHARPENING: exit for the right reason** |
| `hyst` | the name leaves the top/bottom **2N** | **COST-CUTTING: same reason, just slower** |
| `cap` | D285's rule, **or** the trade's cumulative return falls below **−5%** | the principal's left-tail question |

**`sig` has ZERO free parameters.** A zero crossing is where the signal itself
says the acceleration has turned; nothing is chosen, so nothing can be fitted.

**`hyst` exists to make the comparison honest.** If it raises breakeven as much
as `sig` does, the gain is amortisation and not selection — which is exactly the
confusion the standing note warns about, and it would be dishonest to run `sig`
without a pure cost-cutting arm beside it.

**`cap`'s −5% is a judgement and is declared as one.** D285's trades have a
**mean of +36.44 bp against a median of +82.11** — a heavy left tail dragging the
mean down by ~46 bp, which is what makes the question worth asking. The trade-loss
distribution is reported so a reader can see whether the cap bites sensibly.

**Cells: 4 arms × 3 N = 12, plus `rnd-N` and `tail-N` at each N = 6. Total 18.**

**Costs, unchanged from D285:** 5 bp/side, `rf` 4% on the long leg, borrow 3%/yr
on the short leg, PPY 252, seed 0, 300 null draws.

---

## Controls

`rnd-N` (random from the whole universe) and **`tail-N`** (random from the 2N most
extreme |lagged `hist_L`| names — matched on the volatility tail, random on
*which* tail). **`tail-N` is the binding one**, for the reason D283 and D284
established: `hist_L` is signed acceleration, so both tails are the volatile
names, and a whole-universe control is beaten by the tail tax alone.

---

## Hurdles

| | standard |
|---|---|
| **M** | Mean move per trade ≥ `2c` = 10 bp per name round trip |
| **B1** | **Breakeven half-spread ≥ 15 bp/side** — D285's bar, kept **for comparability**. This is the pre-registered gate |
| **B2** | **Breakeven ≥ the book's OWN measured median trailing Corwin-Schultz half-spread.** Self-calibrating, and the honest bar |
| **NEU** | \|correlation to the equal-weight universe\| ≤ 0.20 |
| **V** | Positive net CAGR |
| **C** | Beats `rnd-N` **and** `tail-N`, Sharpe and money, gross and net |
| **F** | Best-of-18 floor (D228), one shared offset vector |
| **E′** | ≥3.0 effective instruments over the held book, ≥500 trades. **Expected to degenerate to ≈ N**; the runner must say so when it does |
| **H** | Rotation null — **REPORTED, NOT DECISIVE** (R7's corollary, four demonstrations) |

**B is split deliberately.** D285 guessed 15 bp/side and the held names measured
**33.81**, so the guess was generous by more than a factor of two. **B1 keeps the
comparison to D285 honest; B2 is what tradeability actually requires.** A cell
clearing B1 but not B2 is **not tradeable**, and the result must say so in those
words. Corwin-Schultz is upward-biased on this population, so B2 is a
conservative bar and that is stated with it.

---

## Predictions

| | prediction | direction | confidence |
|---|---|---|---|
| **G1** | **`sig` beats `disp` on breakeven at all three N** — exiting for the right reason is worth something | **for** | **moderate** |
| **G2** | **`hyst` raises breakeven by AT LEAST as much as `sig` does.** If pure cost-cutting matches exiting-for-the-right-reason, the gain is amortisation and `sig` has found nothing | **AGAINST the interesting reading** | **moderate** |
| **G3** | **No cell clears B2**, on any arm at any N | **AGAINST** | **high** |
| **G4** | **`cap` raises the mean move but shortens holds enough to LOWER breakeven** — the left tail is real, and truncating it costs more turnover than it saves in losses | **AGAINST** | **moderate** |
| **G5** | **`sig` has a higher net SHARPE than `hyst` even where its breakeven is lower.** This is the separation the standing note asks for: cost coverage and risk-adjusted return moving in opposite directions | **for** | **low-moderate** |

**G2 is the load-bearing prediction and it is declared against the reading I
would prefer.** **What would falsify it: `hyst` raising breakeven by less than
`sig` at N = 25.** That outcome says exiting on the signal's own state is worth
more than exiting later for the same arbitrary reason — the first evidence in
this programme that an exit rule carries information.

---

## Ledger

| | |
|---|---:|
| carried — D256 21, D279 20, D281 10, D282 19, D283 26, D284 13, D285 18 | **127** |
| fresh — 4 arms × 3 N, + 2 controls × 3 N | **18** |
| **total** | **145** |

**Disclosed under [R13](../RULES.md#r13):** the exit rule was chosen **after
seeing D285's decay curve**, and D280's 165 statistics shaped this search space.
**No best-of floor computed from eighteen cells prices either**, and saying so is
not a formality — it is why a cell clearing here still needs an out-of-sample
test before it means anything.

---

## Stop

**If no arm beats `disp` on breakeven, the exit rule carries nothing and this
line is closed** — no fifth arm, no threshold sweep on `cap`, no alternative
reversion definition.

**If `hyst` matches or beats `sig`, the gain is amortisation** and must be
reported as cost-cutting, not as a better signal, however good the number looks.

**If a cell clears B2**, it is still not a book entry: [R8](../RULES.md#r8) needs
a pre-registered out-of-sample test, and **D246's reserved wide-universe cohort
remains unspent** and is the candidate.
