# D452 RESULT — D440 on the instrument: the same verdict, and clustering explains 94% of the gap rather than 83%

**MEASUREMENT record. No hurdle is claimed and no candidate is admitted.** Closes
[D451](D451-RESULT-the-complete-acquisition-T1-is-testable-and-the-cash-futures-gap-tracks-the-RATE-cycle-not-the-settlement-rule.md)
§6 item 1. **Runner:** `scripts/d452_d440_on_es.py`, which imports `d440_lifecycle` unchanged.
**Evidence:** `data/d452_d440_on_es.json`. **All four predictions hold — the first time this
session.**

---

## THE ANSWER

> **`T1` UNRESOLVED · `T2` FAIL · `T3` UNRESOLVED → NOT A CANDIDATE.**
>
> **The same verdict D440 reached on the equity proxy, now reached on the instrument that would
> actually be traded, across 3,584 holds covering 2010-06-07 → 2026-09-09.**

**C1 is now measured end to end on ES. No proxy caveat remains anywhere in the chain.**

## 1. What D449 did not do, and this does

**D449 put ES holds through the lifecycle and reported `V` at the best grid point. That is one
number.** D440 is a study: **two controls that separate kurtosis from clustering, a circular block
bootstrap for an honest SE, an era split, and three gates.** None of it had ever been run on the
instrument. **`d440_lifecycle.py` is not edited** — its `run_cell`, `block_bootstrap_V` and
provider machinery are imported and called on the ES frame, and **`[P1]` is re-run here**, because
a study that skips its own gate on the grounds that it passed elsewhere is not running it.

## 2. The controls — and the clustering finding is STRONGER on the instrument

| best risk, static | GAUSS | SHUF | MEASURED | shortfall | **fat-marginal share** |
|---|---:|---:|---:|---:|---:|
| **ES** | 889 | 849 | **227** | 74.5% | **5.9%** |
| proxy | 770 | 654 | 92 | 88.1% | 17.1% |

> **On ES the fat marginal explains 5.9% of the gap and SERIAL STRUCTURE explains 94.1%** —
> against 17.1% / 82.9% on the proxy. **D440's central mechanism is not weakened by moving to the
> instrument; it is sharpened.**

**And the reason it sharpens is worth stating, because it runs against intuition.** ES's kurtosis
is **18.82**, higher than SPY's 14.96 — **more fat tail, and LESS of the damage attributable to
it.** **Kurtosis and the kurtosis-attributable damage move in opposite directions across the two
instruments, which is about as direct a demonstration as this question admits that the tail is not
the mechanism.**

**The vol-targeting cross-check reproduces too:** on `SHUF`, where the clustering has been
destroyed, vol targeting **loses** value (849 → 591), exactly as it did on the proxy (654 → 344).
**It is an instrument for exploiting clustering, and on a series without clustering it is pure
cost.**

## 3. The bar

**ES series:** mean 0.0533%/hold, sd 1.028%, **annualised Sharpe 0.824**, skew 0.18, kurtosis 18.82.

### `T1` — circular block bootstrap · **UNRESOLVED**

| `b` | `V` | SE | [p05, p95] | margin | `P(V>0)` |
|---:|---:|---:|---|---:|---:|
| 1 | 673 | 595 | [6, 1,731] | **1.13 SE** | 0.955 |
| 20 | 499 | 499 | [−66, 1,426] | **1.00 SE** | 0.870 |
| 60 | 319 | 394 | [−107, 1,048] | **0.81 SE** | 0.770 |

**Against a 2-SE bar.** **And the bootstrap centre falls monotonically as `b` grows — 673 → 499 →
319 — toward the historical sequence's own 92.** That is D440's signature appearing a third time:
**resampling in blocks destroys the clustering that does the damage, so a longer block is a harsher
and more honest null.**

### `T2` — P4, expected **funded** life > 3 years · **FAIL**

**0.27 years (67 days) at the `V`-maximising size, and nothing on the grid clears three years:**

```
0.2% = 0.86 yr     0.4% = 0.27 yr     0.7% = 0.11 yr     1.1% = 0.07 yr
```

**Not one path of 3,584 is alive at the 600-day horizon. It fails by roughly elevenfold**, under
the [R11 ruling of 2026-09-11](../RULES.md#r11) that P4 is the account's life.

### `T3` — 2021–2026 alone · **UNRESOLVED**

**1,456 holds, `V` = 65 ± 198, 0.33 SE, `P(V>0)` = 0.565.**

## 4. ES is worth MORE than the proxy, at every comparable point

| | ES | proxy |
|---|---:|---:|
| static, MEASURED, best | **227** | 92 |
| voltgt, MEASURED, best | **92** | 78 |

**Continuing [D451](D451-RESULT-the-complete-acquisition-T1-is-testable-and-the-cash-futures-gap-tracks-the-RATE-cycle-not-the-settlement-rule.md)
§3: the proxy is the conservative series, not the optimistic one.** **That is now confirmed on the
full lifecycle and not only on the hold path** — and it is the third record in which D440 §8a's
declared direction turns out to be backwards.

## 5. Predictions — four for four

| | prediction | outcome |
|---|---|---|
| **V1** | GAUSS ≫ MEASURED, SHUF between, **clustering carrying most of the gap** | **CONFIRMED, and more extreme** — 94.1% against the proxy's 82.9% |
| **V2** | `T2` fails, **not narrowly** | **CONFIRMED** — 0.27 years against 3.00, an elevenfold miss |
| **V3** | `T1` UNRESOLVED | **CONFIRMED** — 0.81 to 1.13 SE |
| **V4** | ES's `V` above the proxy's | **CONFIRMED** — 227 vs 92, and 92 vs 78 |

**Four for four, and it is the first clean sweep this session.** **The honest reading is that these
were the easy predictions** — every one of them extrapolated a mechanism already measured on the
proxy, and the hard predictions this session (the ones about direction, magnitude and which term
carried an effect) were the ones that failed.

## 6. What this settles for the prop track

- **C1 is measured end to end on the instrument and it is NOT A CANDIDATE.** The verdict was never
  in doubt after D440; what was in doubt was whether the proxy was hiding something. **It was
  hiding something, and what it hid made the proxy look WORSE than the instrument.**
- **Every ES-versus-proxy caveat in the chain is now discharged**: the settlement rule (D447, D448,
  D451), the untraded window (D449, D451), the entry print (D450), and now the full lifecycle.
- **The prop candidate ledger stays empty.** D258's four are resolved, `O1` is resolved, and C1
  fails P4 on the instrument by elevenfold.

## 7. What it leaves

1. **The `q − r` regression D451 §6 names** — turning its arithmetic consistency check into a test.
2. **The thin-print explanation for why the proxy overstates excursion** — D451 §6 item 2, now
   supported by a second record and still unmeasured.
3. **The hold-length curve**, which remains the only route to a fifth candidate and which the ES
   series now makes measurable at every horizon rather than at the single 22-hour one C1 fixes.
