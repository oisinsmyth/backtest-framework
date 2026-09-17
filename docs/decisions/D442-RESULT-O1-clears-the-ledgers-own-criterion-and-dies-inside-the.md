# D442 RESULT — `O1` clears the ledger's own criterion, dies inside an enumerated rotation null, and its mask would close the account anyway

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D442-RESULT-O1-clears-the-ledgers-own-criterion-and-dies-inside-the-rotation-null-and-the-mask-breaks-the-inactivity-rule.md`. The H1 above is the full title.*

**Pre-registration:** [`D442`](D442-O1-the-volatility-regime-abstention-rule-on-C1.md), committed
before the runner existed. **Runner:** `scripts/d442_abstention.py`. **Evidence:**
`data/d442_abstention.json`. **Six of seven predictions resolved as written**, §6 — including the
one whose conditional I pre-registered and which fired on the negative branch.

---

## THE HEADLINE

> **`G1` PASS · `G2` FAIL · `G3` PASS → `O1` IS AN EXPOSURE CUT WITH A STORY.**
>
> **That is the candidate ledger's own sentence, written before any of this was measured, and it
> is the verdict.**

**`G1`, the inherited criterion, passes and passes comfortably** — at `θ` = 0.20 on SPY, floor-touch
falls **59.4%** against a P&L fall of **28.6%**, a **+30.8 point** margin, and it passes on **13 of
16** symbol-threshold cells.

**Then the control takes it apart.** The abstention mask rotated against its own hold sequence —
**all 3,265 offsets ENUMERATED, so the p95 carries no sampling error whatsoever**:

| SPY, `θ` = 0.20 | treatment | ROT p50 | ROT p95 / p05 |
|---|---:|---:|---:|
| mean hold, bp | **3.59** | **5.02** | 6.19 (p95) |
| floor-touch 1× | **0.572%** | **1.487%** | 0.915% (p05) |
| **`V`, static, 0.7%** | **60** | **−53** | **223** (p95) → **inside** |
| **`V`, voltgt, 0.7%** | **70** | **72** | **365** (p95) → **inside** |

> **The gate is genuinely informative about WHERE the excursions are — its floor-touch rate sits
> below the 5th percentile of every rotation, which no exposure cut alone achieves.**
> **And it buys nothing in account value.** On vol-targeted sizing the treatment lands at **70
> against a rotation median of 72** — a randomly-placed abstention of identical count and identical
> run-lengths does the same job.

**The secondary control agrees.** `BLKRAND`, matched on count and run-length multiset: **p50 98,
p95 325, treatment 70.** The treatment is below the median of that null too.

## 1. What the rotation actually revealed, and why `G1` was not enough

**`G1` compares gated against UNGATED. It has no way to ask whether the gate's PLACEMENT matters.**

The enumeration answers that in one line: the real mask cuts floor-touch **far** better than any
rotation (below p05) **and** preserves P&L **worse** than a typical rotation (below p50). **Both
halves are real. They cancel.**

> **The inherited criterion is NECESSARY AND NOT SUFFICIENT**, because it scores a 59% touch cut
> against a 29% P&L cut as a win while never establishing the exchange rate between them. **`V` is
> the exchange rate, and at that price the trade is flat.**

**This is a correction to the ledger's own sentence, earned rather than asserted:** *"survives iff
floor-touch falls relatively more than expected P&L"* is the right instinct and the wrong test.
**The test is the shape-matched null.**

## 2. Both lenses, kept apart

### Per-trade — `G1` by symbol at the primary `θ` = 0.20

| symbol | traded | abstained | mean bp | Δ P&L | Δ touch | `G1` |
|---|---:|---:|---:|---:|---:|---|
| **SPY** | 2,623 | 19.7% | 3.59 | −28.6% | **−59.4%** | **PASS** |
| QQQ | 2,574 | 21.2% | 3.84 | −34.6% | −46.4% | PASS |
| IWM | 2,618 | 19.8% | 2.86 | −39.1% | −45.3% | PASS |
| DIA | 2,532 | 20.6% | 2.69 | −32.1% | **−74.8%** | PASS |

**`G1` fails in 3 of 16 cells, all IWM** — at `θ` = 0.10, 0.30 and 0.40, where the P&L cost outruns
the touch cut. **IWM is the symbol that was negative everywhere in D440 as well.**

### Account — `V` and funded life, MFFU Rapid EOD 50K

```
sym  rule    BASE V   O1 V     dV      d(funded years)
SPY  static      92     60    -32          +0.09
SPY  voltgt      78     70     -7          +0.01
QQQ  static      69    262   +192          +0.56
QQQ  voltgt      39     33     -6          -0.08
IWM  static     -77   -102    -26          -0.01
IWM  voltgt     -80    -51    +29          -0.00
DIA  static      98    250   +151          +0.59
DIA  voltgt      65    125    +59          -0.28
```

> **QQQ-static `+192` and DIA-static `+151` are UNCONTROLLED.** The rotation was enumerated on the
> primary symbol only, exactly as pre-registered. **On SPY, where the null exists, an increment of
> that size sits comfortably inside it** — the rotation's maximum reaches **+2,395**. **Nothing here
> claims those two cells are real, and the next study on this line should enumerate them before
> anyone reaches for them.**

**`G3` passes on both sizing rules and it is the weakest kind of pass:** funded life rises 0.15 →
0.24 years (static) and 0.14 → 0.15 (voltgt). **P4 needs 3.00.** Under the
[R11 ruling of 2026-09-11](../RULES.md#r11) that is the operative statistic, and **`O1` moves it by
five weeks.**

## 3. THE SECOND KILL, AND IT IS INDEPENDENT OF ALL THE ECONOMICS

**`X-g` predicted the longest abstention run would exceed 7 sessions. It does, by more than an order
of magnitude:**

| `θ` | SPY | QQQ | IWM | DIA |
|---|---:|---:|---:|---:|
| 0.10 | 40 | 48 | 32 | 41 |
| **0.20** | **88** | 84 | 67 | 57 |
| 0.30 | 98 | 94 | 88 | 93 |
| 0.40 | 131 | 131 | 91 | 97 |

> **MyFundedFutures enforces a 7-day inactivity rule. At the primary threshold this gate goes flat
> for 88 consecutive sessions — roughly four months, and it is the 2020 volatility regime.**
> **D386's assumptions list states the inactivity rules are NOT modelled because "at every risk
> level tested they are cleared comfortably." That was true of every candidate before this one.
> An abstention rule is exactly the construction that breaks it.**

**So even at a threshold where the economics worked, the account would be closed for inactivity
before the strategy was allowed to prove anything.** **`θ` = 0.10 still goes flat for 40 sessions.**
**There is no threshold on the pre-registered grid that both abstains meaningfully and stays inside
the rule.**

## 4. Gates

| | |
|---|---|
| **`[A1]` lag audit** | the mask re-derived in a second implementation that never calls the gate; perturbing hold `t` leaves the mask at `t` unchanged; **a peeking gate caught as distinguishable** |
| **`[A2]` sign audit, in money** | abstaining on every loser raises total P&L, on every winner lowers it |
| **`[A3]` right-quantity** | the gated series differs exactly where the mask is and nowhere else; abstain share within 0.05 of `θ` |
| **`[REP]`** | BASE-static and BASE-voltgt reproduce **D440's cells bit-identically**, all 8 |
| **`[A5]` control eligibility** | every ROT offset preserves count exactly and run-count to within the one wrap seam |
| **`[A6]` both ends of the dial** | a never-abstaining mask reproduces BASE bit-identically; a fully-abstaining mask gives `V` = `−fee` **exactly** |

**`[A6]` found a real defect on its first run.** A fully-abstained series has zero variance, so the
notional divided by zero and the test reached the right answer **through NaN propagation** — right
answer, wrong reason. `d440_lifecycle.notional_series` now returns zero notional explicitly for a
degenerate series. **D440's `[P1]` and `[REP]` still pass, so no committed number moved.**

## 5. Speed, stated because the rule requires it

**Profiled rather than estimated: 0.0504 s per rotation offset**, so the full enumeration is 2.7
minutes per rule and the whole report **5m58s**. **No subsampling was needed and none was used** —
the p95's sampling error is genuinely zero, which is the entire reason the pre-registration chose
enumeration. My pre-profile guess was 14 minutes, **2.4× wrong in the direction that would have
bought a needless optimisation pass.**

## 6. Predictions

| | prediction | outcome |
|---|---|---|
| **X-a** | both tails cut; mean P&L falls **15–40%** at `θ` = 0.20 | **CONFIRMED** — 28.6 / 34.6 / 39.1 / 32.1%, all four inside |
| **X-b** | floor-touch falls **35–65%**; `G1` passes | **CONFIRMED on `G1`**; three of four inside the band, **DIA at 74.8% above it** |
| **X-c** | **the account gains more than the return does** — the concave-payoff argument | **WRONG.** `dV` is *negative* on the primary symbol under both sizing rules, and zero against the null |
| **X-d** | adds more to static than voltgt; voltgt increment inside ±25% of BASE | **PARTLY WRONG** — direction mixed, and DIA-voltgt is +91% |
| **X-e** | ROT p50 below BASE **and** the treatment clears ROT p95 | **first half CONFIRMED** (p50 −53 and 72 against BASE 92 and 78); **second half FAILED — and the pre-registered conditional fired: "if it does not, `O1` is an exposure cut and the ledger's own sentence is the verdict."** |
| **X-f** | `G3` passes, P4 still fails, life under 1.5 years | **CONFIRMED** — 0.24 years |
| **X-g** | longest run exceeds 7 sessions | **CONFIRMED, by 12×** — and it is §3, a second independent kill |

**X-c is the one that mattered and it is the one that was wrong.** The concavity argument — a big up
move only raises the floor while a big down move breaches — is sound in isolation and **does not
survive the gate also removing the up moves.** D440 named the hazard and I did not carry it into the
prediction: **SPY's best hold in sixteen years is the session after its worst, the gate abstains on
both, and that is the whole result.**

## 7. What this does and does not settle

- **It does not close `O1`**, and under [R15](../RULES.md#r15) it cannot. **It is one gate — trailing
  realised volatility — on one construction, on four symbols.** §8 of the pre-registration said so
  before the run: **a failure here is a verdict on this gate, not on abstention as an idea.**
- **It does not rescue C1** and was never able to. **P4 still fails by 12×.**
- **What it does settle is the ledger's criterion.** *"Floor-touch falls relatively more than
  expected P&L"* is necessary and **not sufficient**, and the shape-matched rotation is what shows
  it. **Any future abstention or gating candidate on either book is screened against a rotation that
  matches count AND run-lengths, not against the ungated arm.**
- **And it puts the inactivity rule on the map.** It has been unmodelled in every prop record
  because no prior candidate could trip it. **Any gate that can go flat must now report its maximum
  run alongside its returns.**

## 8. What it leaves

1. **QQQ-static and DIA-static are uncontrolled and look large.** Enumerating their rotations is
   ~3 minutes each and is the cheapest open item this study creates.
2. **A gate that abstains for 88 sessions is the wrong instrument even if the economics worked.**
   If abstention is revisited, the constraint to design against is **run length**, not threshold —
   a gate with a cap on consecutive flat days is a different object and was not tested.
3. **The gate's floor-touch performance is real** — below the 5th percentile of 3,265 rotations. **It
   is the P&L cost that eats it.** Anything that keeps the touch reduction while paying less P&L is
   the surviving question, and nothing here says such a thing exists.
