# D451 RESULT — on the complete acquisition: T+1 is testable at last, and the cash-futures gap tracks the RATE cycle, not the settlement rule

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D451-RESULT-the-complete-acquisition-T1-is-testable-and-the-cash-futures-gap-tracks-the-RATE-cycle-not-the-settlement-rule.md`. The H1 above is the full title.*

**MEASUREMENT record.** The re-run D450 §7 asked for, now that the acquisition has finished.
**Driver:** `scripts/rerun_es_studies_on_completion.py`, which waited and then ran the three
committed runners unchanged. **Full output:** `temp/es_rerun.log`. **Amends
[D448](D448-RESULT-the-direct-test-the-drift-is-in-the-T0-future-too-and.md)
§3 and strengthens [D449](D449-RESULT-the-untraded-window-was-not-the-problem-the-proxy.md)
§1.**

---

## THE ANSWER

> **The T+1 era is now testable — 432 pairs — and the settlement hypothesis fails on it
> DECISIVELY, in the direction opposite to its own prediction.**
>
> **The cash-futures gap is the carry term `q − r`, and it tracks the INTEREST-RATE CYCLE. The
> three settlement regimes happen to coincide with three rate regimes, which is exactly the era
> confound [D447](D447-the-settlement-hypothesis-is-not-supported-the-drift-runs-the.md)
> warned about — now identified rather than suspected.**

**The acquisition completed**: `ohlcv-1m` covering **2010-06-06 → 2026-09-09**, every chunk
`downloaded`. A concurrent session independently verified the whole transfer — **129 files,
111.0 GB, zero corruption, nine bar slices tiling 2010–2026 with no gaps.**

## 1. D448 re-run — the regime table, with T+1 present for the first time

**2,530 matched pairs, up from 1,747.** Gate: **corr(ES, SPY) = 0.9950 overnight, 0.9996 RTH.**

| regime | n | SPY overnight | ES overnight | **ES − SPY** |
|---|---:|---:|---:|---:|
| **T+3** | 791 | 1.88% | 3.21% | **+1.09 bp/day** |
| **T+2** | 1,307 | 9.11% | 8.50% | **−0.31** |
| **T+1** | **432** | **9.52%** | **6.33%** | **−1.66** |

> **The settlement hypothesis says cash diverges from futures BECAUSE cash settles later, so the
> divergence must SHRINK as `n` falls toward the futures' T+0. It does the opposite: the gap grows
> monotonically in magnitude, +1.09 → −0.31 → −1.66, and is LARGEST at T+1 — the regime where cash
> is closest to futures in settlement terms.**

**And the carry reading accounts for all three**, because `ES − SPY(price) = q − r`:

| era | rate environment | `q − r` implied | observed |
|---|---|---:|---:|
| T+3, 2010–2017 | ZIRP, `q` ≈ 2%, `r` ≈ 0.3% | ≈ **+1.7%/yr** | **+2.75%/yr** |
| T+2, 2017–2024 | a full hiking-and-cutting cycle | ≈ **0** | **−0.78%/yr** |
| T+1, 2024–2026 | `r` ≈ 4.5%, `q` ≈ 1.3% | ≈ **−3.2%/yr** | **−4.18%/yr** |

**Sign right in all three; magnitude right to within a point.** `[q` and `r` were not extracted;
this is an arithmetic consistency check, as in D448 §3.`]`

## 2. This AMENDS D448 §3

**D448 reported `ES − SPY` overnight at `+0.59 bp/day, t +3.54` = `+1.49%/yr` and called it carry.
On the complete sample it is `−0.11 bp/day, t −0.82` — INSIGNIFICANT.**

**The mechanism was right and the level was an artefact of a truncated sample.** D448 ended at
2022-08, inside the low-rate era, so it measured one half of a cycle. **Over a full rate cycle the
carry term averages to approximately zero**, which is what a financing spread should do and what a
settlement effect would not.

> **D448's headline — the drift is in the T+0 future too, and the settlement kill-check is
> discharged — is UNCHANGED and better supported.** What is withdrawn is its *"+1.49%/yr"* as a
> standing number. **A carry estimate measured over half a rate cycle is a statement about that
> half.**

## 3. D449 re-run — the finding INVERTS, in the reassuring direction

**2,595 matched holds, 2011-02-08 → 2026-08-26.**

| | ES | proxy | ratio |
|---|---:|---:|---:|
| mean MAE | 0.698% | 0.708% | **0.99** |
| p50 | 0.457% | 0.472% | 0.97 |
| p99 | 3.370% | 3.354% | 1.00 |
| **breach 1×** | **1.195%** | **1.387%** | **0.86** |
| breach 2× | 10.906% | 12.100% | 0.90 |
| breach 3× | 25.279% | 27.784% | 0.91 |

> **ES's MAE is not larger than the proxy's. It is marginally SMALLER, and its breach rate is
> 9–14% LOWER.** D449 §8a's premise — that the proxy understates the excursion and every `V` is an
> upper bound — **is wrong in sign on the complete sample.**

**The candidate explanation, and it is not measured here:** SPY's extended-hours bars are built
from **thin** prints, which widens their high-low range, and a wider bar inflates a measured MAE.
**That exaggeration appears to exceed what the invisible 20:00–04:00 window conceals.** The proxy's
problem was never the window it could not see; it is the prints it *could*.

**The lifecycle follows:** ES **78 / 49** against the proxy's **53 / 19** — **ES is worth more, not
less**, confirming the correction D450 already forced on `Z3`.

## 4. D450 re-run — unchanged, on 45% more data

**2,530 holds. Gate 4.44 × 10⁻¹⁶. Identity residual −2.37 × 10⁻¹³ bp.**

| term | SPY bp/day | ES bp/day | ES−SPY %/yr |
|---|---:|---:|---:|
| hold | 5.39 | 5.15 | −0.62% |
| **step** | **+0.36** | **+0.53** | **+0.42%** |
| full | 5.76 | 5.68 | −0.19% |

**The entry step is +0.42%/yr, identical to the smaller sample, and still runs opposite to the
staleness hypothesis.** **The fallback branch still never fires**: 2,518 of 2,530 entries at
exactly 18:00, 11 at 18:15, one at 18:30. **D259's `ENTRY_STALE_FLOOR` has never bound, on any
sample yet measured.**

## 5. What this settles for the prop track

- **The settlement kill-check is now closed on all three regimes**, including the one that could
  not be tested before. **C1's drift exists in the instrument, and nothing about the settlement
  rule threatens it.**
- **The equity proxy is CONSERVATIVE, not optimistic.** Every D440 number computed on it carries a
  slightly *pessimistic* path, not an upper bound. **That is the opposite of what D440 §8a
  declared, and it is the second time this session that a stated conservatism ran the other way.**
- **Nothing rescues C1.** Under the [R11 ruling](../RULES.md#r11) P4 is the account's life, and
  D440 measured **0.14 years against a three-year bar**. **This changes the input's provenance, not
  the verdict.**

## 6. What it leaves

1. **D440 itself has not been re-run on ES.** D449 re-runs the *hold path*; D440's full
   lifecycle-with-controls on the complete ES series is a separate, larger study.
2. **§3's thin-print explanation is a candidate.** Comparing bar WIDTH between SPY's
   extended-hours bars and ES's over the same minutes would settle it, and the data for it is now
   committed.
3. **The rate-cycle reading of §1 is arithmetic, not a measurement.** Extracting `q` and `r` and
   regressing the gap on them is the honest version, and it would turn a consistency check into a
   test.
