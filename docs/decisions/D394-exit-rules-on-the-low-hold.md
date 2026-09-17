# D394 — stops, targets and trailing stops on the low hold: can an exit rule close a 6× cost gap?

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). **Nothing here is a
result.** No cell scored, no null run, no book proposed.
**Date:** 2026-09-08 · **Area:** signal research · **personal track** · Requested by the principal.

**No holdout testing. Holdout reads spent by this record: 0. Programme total: 1** (D371).

**Build (R16):** today's panel, `load_ragged(dividend_bound=True)`, `keep_v2` floor, F0, next-open
fill (D340). **Number:** D394, in this branch's reserved D390–D399 block.

**This is a NEW CONSTRUCTION, not a D393 cell.** D393 §3 froze the exit as `cap ∈ {5,10,20,40,60}`.
Adding a stop, a target or a trail changes *how long capital is deployed and on what condition*,
which under D289's fourth amendment needs its own pre-registration rather than being bolted onto
D393. **D393's hurdles, nulls and verdicts are untouched by this record.**

---

## 0. The gap this is trying to close, stated as arithmetic before anything is run

[D393 Addendum 6](D393-ADDENDUM-6-the-ten-cells-and-the-price-split.md) measured all ten cells.
On the low holds:

| | trades | gross | 2c | net | ratio |
|---|--:|--:|--:|--:|--:|
| **E1/cap10** — the primary here | 22,855 | **+10.52** | 61.40 | −50.88 | **0.17×** |
| E1/cap5 — reported beside it | 24,777 | +4.72 | 61.48 | −56.76 | 0.08× |

**Cost per trade is one round trip, ~61 bp, and an exit rule does not change it** — the entries are
identical, only the exit moves. So the ratio improves *only* if gross per trade rises.

> **To reach gate 1c's 1.0×, gross must go +10.52 → ~61 at cap 10 — a 5.8× increase. At cap 5,
> +4.72 → ~61, a 13× increase.**

**That is the bar. It is stated here, before the runner exists, so no later cell can be reported as
progress without being measured against it.**

---

## 1. The mechanism, declared — and the record already predicts the sign

An exit rule cannot create edge. It **redistributes an existing return distribution** by truncating
one tail of each trade's path. It raises the mean only where the truncated region has adverse
expected continuation.

**The cap-20 ledger already says which tail carries this book** (D393 Addendum 1 §1):

| | value |
|---|--:|
| mean | +22.06 |
| **mean after dropping the top 1%** | **−19.82** |
| mean after dropping the bottom 1% | +60.29 |
| symmetric trim | +18.38 |

**The right tail carries the mean: removing the best 1% of trades costs about 42 bp of it.** The top
trade alone (GME, 2021-01-28) is **8.38%** of the ledger.

> **DECLARED MECHANISM AND DIRECTION:**
> - **A TAKE PROFIT truncates the right tail and should REDUCE gross.** This is declared *against*
>   the take-profit arm.
> - **A STOP LOSS truncates the left tail and may RAISE gross**, but only to the extent that names
>   breaching the stop keep falling. A stop does not excise a loss — it *realises* one.
> - **A TRAILING STOP is a take profit on any name that trends and then gives back**, so on a
>   right-tail-carried book it is expected to behave like the take profit: **reduce gross.**
>
> **A result in the opposite direction on any arm is reported DIRECTION-INVERTED and counts against
> the mechanism even if the number is good.**

---

## 2. The construction, frozen before any number is seen

- **Universe, entries, hedge, truncation:** identical to D393 §3 — floored (`keep_v2`), F0,
  eligible, E1 on `up_run_21`, long, every event taken, no slot cap, next-open fill (D340).
  **Only the exit changes.**
- **Holds:** **cap 10 is PRIMARY**, cap 5 reported beside it. Both declared now.
- **Exits are BAR-CLOSE rules on information through t−1, filled at the next open.**

| arm | rule, on the position's cumulative return `cx` through t−1 |
|---|---|
| **S** stop loss | exit when `cx ≤ −s` |
| **T** take profit | exit when `cx ≥ +p` |
| **R** trailing stop | exit when `cx ≤ peak(cx) − r`, `peak` over the position's own life |

- **Levels, declared now:** `s, p, r ∈ {5%, 10%, 20%}`.
- **The seven families the principal asked for:** S, T, R, S×T, S×R, T×R, S×T×R.
- **The cap is always still in force.** Every arm is the exit rule **OR** the cap, whichever fires
  first, exactly as the kernel already ORs `cap_hit` with its trigger.

### 2a′. AMENDMENT, 2026-09-08, BEFORE THE RUNNER EXISTS — D380 already built this, and it changes the fill and the null

**Found while looking for the kernel's exit hooks: `scripts/run_d380_exit_rules.py` and
[D380 RESULT](D380-RESULT-no-exit-overlay-beats-not-cutting-and-R7s-control.md)
already exist**, on master, dated the same day. Three consequences, all adopted here.

**1. The kernel is not touched at all.** D380 established that per-trade P&L is the sum of a trade's
own per-bar path, so **every rule is a re-cut of one stored cumulative-sum matrix** — no kernel
re-run per cell, and no new exit mode in `d345_event_book`. `trade_paths`, `pnl_at`, `assert_CUT`,
`assert_OVL` and the control machinery are **imported from D380, not reimplemented.**

**2. THE FILL CONVENTION CHANGES, and §2's "next open" was not implementable.** The re-cut matrix is
close-to-close; **a next-open exit is not representable in it.** D380's convention is
`hold = first_breach_index + 1` — **exit at the CLOSE of the bar the rule fires on**, a
market-on-close order. That is adopted, because the alternative is a second convention for the same
quantity. **It is mildly more favourable than next-open**, so the sensitivity — holding one further
bar — is reported for the best cell.

**3. THE NULL IS R7's CONTROL, not a bare best-of-63.** D380's pre-registration establishes that an
overlay must be nulled against a control that **keeps the base book and randomises only the
overlay's decisions, matched on how many it makes.** The best-of-63 floor of §3 still prices the
*search*; R7's control prices each *rule*. Both apply, and the search floor is the binding one.

**4. D380'S WARNING IS INHERITED, and it constrains how §4's answers may be read:**

> *"R7's strict control is not a fixed benchmark. It inherits whichever trades the rule selects, so
> its difficulty varies by a factor of fifteen across rules and U1 verdicts are NOT comparable
> between them."*

**So no cell of the 63 may be ranked against another by its control verdict.** They are ranked on
gross ÷ 2c, which is a fixed bar, and their controls are read one at a time.

**5. D380's RESULT IS PRIOR EVIDENCE FOR §4's PREDICTIONS, and it is disclosed under R13.** On
D373's winners'-dip long at a 40-bar cap it found: ***"Every exit overlay destroys value against
simply not cutting"*** — baseline **+160.55**/trade, best overlay **+62.43**, a **−200 bp stop
collapsing to +13.99**. **That is a different construction and a different hold**, so it does not
decide this record — but Q1, Q2 and Q3 were written before it was found and it points the same way.

---

### 2a. INTRABAR STOPS ARE OUT OF SCOPE, and the reason is a defect this programme has already shipped

`d345_event_book.simulate_event` reads `r1T` (close-to-close) and `ocT` (open-to-close). **It has no
high/low path.** A stop that fires when price *touches* a level intrabar needs high/low, a fill
assumption for a gap through the level, and a decision about same-bar entry-and-exit.

**That is a new fill convention, and a new fill convention is where D391's look-ahead came from**
(+43.02 → +8.00, from a mask that read its own bar's low). **It is not being added inside a study
whose purpose is to test an exit rule.**

**Consequence, stated plainly rather than buried:** a bar-close stop is **weaker and more
pessimistic** than a real intrabar stop. If the bar-close arms fail, an intrabar version is not
thereby excluded — but it would be a separate record, with its own fill audit.

---

## 3. The search cost, and it is large

**Cell count: 63 per hold.** Singles 3×3 = 9; pairs 3 combinations × 3×3 = 27; triple 3×3×3 = 27.
**Two holds ⇒ 126 cells**, plus the two unmodified cap cells as the baseline.

> **H1 for this record is measured against a BEST-OF-63 floor within each draw on the primary
> hold** — the maximum over the 63 cells per draw, exactly as D367/D373 built theirs and as D393 §7
> specifies for its ten. **A best-of-63 floor is far higher than a single-cell p95.**

**This is the largest search in the programme's history and the record says so before it runs.**
**R13:** what carries as disclosed search is D393's ten cells and this record's 126. **Nothing here
may be reported as clearing anything against a single-cell floor.**

---

## 4. Predictions — three of the four are AGAINST the construction

| | prediction |
|---|---|
| **Q1** | *(against)* **No cell reaches gross ÷ 2c ≥ 1.0.** The best of all 126 stays below **0.6×**, because a 5.8× rise in gross is not something an exit rule delivers |
| **Q2** | *(against)* **The take-profit arm REDUCES gross at every level**, monotonically in `p` — tighter target, lower gross — because the right tail carries the mean |
| **Q3** | *(against)* **The trailing arm also reduces gross**, for the same reason, and tracks T more closely than it tracks S |
| **Q4** | The stop arm **raises** gross at loose levels (20%) and **reduces** it at tight ones (5%), because a tight stop realises noise |
| **Q5** | The best single cell of the 126 is **inside the best-of-63 floor's p95** — i.e. the whole search is explained by having looked 63 times |
| **Q6** | Median gross rises where mean gross falls on the T arm — the tell that a target trades a fat right tail for consistency |

**Q1, Q2 and Q3 are declared against. If the take profit RAISES gross, the mechanism in §1 is
wrong and the record must say so.**

---

## 5. Kill conditions

- **Q1 holds (no cell clears 1.0×)** → the exit-rule route to profitability on the low hold is
  answered NO, and the record stops without nulls. **Nulls are only spent if some cell clears.**
- **The best cell is inside the best-of-63 floor** → the search explains itself; stop.
- **Any arm needs a holdout read** → **do not spend it.**
- **Do NOT widen the level grid, add levels, or add holds** to rescue a failing arm. That is
  D366's search, and D393 §9 names it: 164 standard errors in sample, failed out of sample.

---

## 6. Assertions the runner must carry

- **[L]** the exit decision uses `cx` through **t−1** only; verified in a second implementation that
  re-derives one position's exit bar from the raw return path, plus `raises_on_broken`.
- **[X]** the self-test RAISES on (a) a stop that reads bar t's own return and (b) a trailing peak
  that includes the current bar.
- **[B]** with every level set to infinity, each arm reproduces the plain cap ledger
  **bit-identically** — the null construction of this study must equal D393's cell exactly.
- **[M]** the cap is still ORed in: no trade in any arm holds longer than the cap.
- **[H]** hand cases for all three rules on a constructed path, before the fixture.
- **[P]** the JSON is persisted **before** it is rendered (D371; D391 repeated it).
- **Four groups** on the primary, with the top trade **named and its bar printed** (D322).

---

## 7. What this record will NOT do

- **It will not admit anything.** Clearing a hurdle is not admission (R8, and `docs/BOOK.md`).
- **It will not close D393**, whose four nulls stand and whose best-of-10 floor is still uncomputed.
- **It will not report a picked cell as a result** without its best-of-63 floor.

---

**Status footer.** No runner exists. `docs/BOOK.md` holds S1 and S2, neither at capital;
`docs/BOOK_PROP.md` is empty. Nothing here is a result, and **only the principal closes a research
avenue (R15).**
