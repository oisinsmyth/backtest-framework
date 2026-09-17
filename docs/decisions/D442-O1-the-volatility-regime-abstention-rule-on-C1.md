# D442 — `O1`: the volatility-regime abstention rule on C1, on both lenses

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file. **No
holdout is read and none exists** — D259 read the whole 2010–2026 window. Equity extended-hours
bars; the same 12,985 holds D440 built and committed.

## 1. What this is, and why it is being run NOW

**`O1` is the last unscreened entry in the prop candidate ledger**, where it has always been
described as *"a volatility-regime day classifier as an **abstention rule**, not a strategy —
`[PROP]`, **and it is not an edge**"*, with a survival criterion **declared there before any of this
was measured**:

> **It survives iff floor-touch probability falls RELATIVELY MORE than expected P&L. Else it is an
> exposure cut with a story.**

**That criterion is inherited, not invented here**, and it is `G1` below unchanged.

**What is new is the reason to run it.**
[D440](D440-RESULT-the-gaussian-was-worth-five-sixths-of-the-value-and-it.md)
measured that **82–86% of the damage a real path does to a funded account is SERIAL STRUCTURE, not
kurtosis** — a Gaussian at matched moments is worth `$770`, the same holds i.i.d. `$654`, the
historical sequence `$78`. **A rule that removes exposure during clustered adverse periods is the
remedy that finding points at, and `O1` is the only candidate of that shape on the ledger.**

**What this is NOT.** Not a new signal — `O1` adds nothing to C1's entry rule and can only subtract
exposure. Not an admission test: no holdout exists on this fixture. Not a reopening of C2 or C3.
**And not a second look at vol targeting** — that is a *sizing* rule and is already inside D440's
numbers; `O1` is on/off, and §3 runs it both instead of and on top of vol targeting precisely
because the two share a conditioner.

## 2. The gate

```
sigma_t   trailing realised vol over the PRIOR 21 holds only (R9), never including hold t.
          The same estimator D440 lag-audited; inherited, not chosen.
q_t       the rolling 252-hold quantile of sigma, also strictly trailing.
ABSTAIN   sigma_t > q_t(1 - theta)          -> the hold is NOT taken: d_low = d_high = d_end = 0
PRIMARY   theta = 0.20   (abstain on the top vol quintile)
GRID      theta in {0.10, 0.20, 0.30, 0.40}, all four reported; the primary is declared here
```

**Warm-up: the first 273 holds of each symbol have no trailing quantile and are always traded.**
Stated so the count is not mistaken for a choice.

**A flat day does not ratchet the floor.** That is the point of an abstention rule and it is what
distinguishes it from sizing to zero vol.

## 3. The arms, and the two lenses

| arm | sizing | gate |
|---|---|---|
| **BASE-static** | constant notional | none — **D440's static MEASURED, reproduced** |
| **BASE-voltgt** | D259's rule | none — **D440's voltgt MEASURED, reproduced** |
| **O1-static** | constant notional | `O1` |
| **O1-voltgt** | D259's rule | `O1` |

**Per-trade lens:** holds traded and abstained; mean and **median** hold return; **floor-touch rate**
= the share of TRADED holds whose own `max_dd` exceeds 4% / 2% / 1.33% (the 1×/2×/3× notionals).

**Account lens:** D440's lifecycle, unchanged — `V` per evaluation purchased, **funded life**,
`P(pass)`, `P(ever paid)`, on MFFU Rapid EOD 50K across D386's risk grid.

**The two are never compared on one statistic** (`CLAUDE.md`; [R11](../RULES.md#r11)'s ruling of
2026-09-11). `G1` is per-trade. `G2` and `G3` are account. **Each is reported in its own units.**

## 4. Controls — and a matched COUNT is not enough

**Abstaining reduces exposure, and less exposure mechanically reduces floor-touches.** That is the
"exposure cut with a story" the ledger warns of, so the control must share the treatment's nuisance.

| | what it destroys | what it preserves |
|---|---|---|
| **ROT** *(primary)* | the gate's ALIGNMENT with returns | the mask **exactly** — count, run lengths, clustering |
| **BLKRAND** *(secondary)* | the gate's run-length realisation | the count and the run-length **distribution** |

**`ROT` is ENUMERATED, not sampled.** The group is the `n − 1` circular offsets of the mask against
its own symbol's hold sequence — **~3,265 for SPY, finite and small** — so `CLAUDE.md`'s rule
applies: enumerate and the p95's sampling SE is **exactly zero**. Enumerated in full for the
per-trade statistics on every cell, and for `V` **on the primary cell** (~3,265 lifecycle runs at
~0.12 s ≈ 7 minutes).

**`BLKRAND` exists only to catch a rotation accidentally aligned with something periodic** —
day-of-week, month-end. 200 draws, reported as a distribution.

**A matched-count i.i.d. abstention is NOT run as a control** and this is deliberate: it churns,
and a churning control for a persistent selector is the error D291 cost 87 cells to.

## 5. The bar

- **`G1` — the ledger's own, inherited:** the **relative** fall in floor-touch rate **exceeds** the
  **relative** fall in mean hold P&L, at the primary `θ`, per-trade lens.
- **`G2`:** `V` at the `V`-maximising size **rises** against the matched BASE arm **and** sits
  **above the enumerated `ROT` p95**.
- **`G3`:** **funded life rises** against the matched BASE arm. **P4's three-year bar is quoted for
  reference and is NOT expected to clear** — D440's best cell anywhere was 1.01 years.

**`G1 ∧ G2` is what would make `O1` worth carrying. `G3` without `G2` is an exposure cut with a
story, which is exactly what the ledger said to look for.**

## 6. Predictions (MODERATE — the mechanism is clear, the magnitudes are not)

- **X-a** `O1` cuts **both** tails, because volatility clustering is direction-blind. **SPY's best
  hold in sixteen years (2020-03-13, +11.27%) is the session after its worst (2020-03-12, −9.53%)
  and the gate abstains on both.** Mean hold P&L falls by **15–40%** at `θ` = 0.20.
- **X-b** floor-touch falls by **more** than that — **35–65%** — because the excursions are where the
  vol is. **`G1` PASSES**, and it passes for a reason that is nearly mechanical.
- **X-c** **the account gains more than the return does**, because a ratcheting floor makes the
  payoff **concave in the path**: a large up move only raises the floor, a large down move breaches.
  **This is the one prediction that is not mechanical and it is the reason to run the study.**
- **X-d** `O1` adds **more to static than to voltgt**, because vol targeting already exploits the
  same conditioner. **On voltgt the increment is inside ±25% of the BASE `V`.**
- **X-e** the enumerated `ROT` p50 lands **below** BASE (a randomly-placed abstention costs
  exposure and buys nothing), and the treatment clears `ROT`'s p95. **If it does not, `O1` is an
  exposure cut and the ledger's own sentence is the verdict.**
- **X-f** **`G3` passes and P4 still fails** — funded life rises but stays **under 1.5 years** at the
  `V`-maximising size, against D440's 0.14.
- **X-g** at `θ` = 0.20 the **longest abstention run exceeds 7 sessions** on at least one symbol,
  which would touch MFFU's 7-day inactivity rule. **D386 does not model it; if the run is long the
  rule becomes a real constraint and is reported as one, not silently ignored.**

## 7. Runner assertions

All three, plus the two D440 needed, plus one this study needs — **each proven to RAISE on a break
that hits the scalar it compares, not the name it reads.**

1. **Lag audit** — re-derive the gate mask in a second implementation that never calls the gate
   function, and assert that perturbing hold `t` leaves the mask at `t` unchanged. **A gate that
   sees its own day is this study's whole failure mode.**
2. **Sign audit, in money** — abstaining on a *losing* hold must raise terminal P&L and abstaining on
   a *winning* hold must lower it.
3. **Right-quantity** — assert the gated series differs from the ungated one in exactly the abstained
   positions and nowhere else, and that the count matches `θ` within the warm-up allowance.
4. **`[REP]`** — BASE-static and BASE-voltgt reproduce D440's committed cells **bit-identically**
   from `data/d440_holds.csv.gz`. **If they do not, the study stops.**
5. **Control eligibility** — every `ROT` mask has the **same count and the same multiset of run
   lengths** as the treatment mask.
6. **Abstention is inert** — a fully-abstaining mask gives `V` = `−fee` exactly and a never-abstaining
   mask reproduces BASE bit-identically. **Both ends of the dial, both checked.**

## 8. Not in scope

No futures data. No holdout. No change to C1's entry, hold or exit. No change to hurdle P, to the
venue, or to D440's lifecycle model. **No second conditioner** — this is realised volatility only,
and if `O1` fails on it that is a verdict on this gate, **not on abstention as an idea**.
