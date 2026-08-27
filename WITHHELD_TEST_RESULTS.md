# D237 — the recovery rule on withheld data

**STAGE 2 — THE VERDICT.** T1 carries it; T3 is a sanity check, not a confirmation.

*seed 0, 30.5s. The rule is untouched from D234.*

## The three tests

| | isolates | symbols | live bars | arm | B&H | **Δ** | boot p05 | boot p95 | rot p95 | H1 | H2 | H3 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|:--:|:--:|:--:|
| **T1** | instruments | 60 | 1,515 | **+0.779** | +0.230 | **+0.549** | -0.152 | +1.158 | +0.194 | ✓ | ✓ | ✓ |
| T2 | both (confounded) | 60 | 413 | **+1.016** | +1.146 | **-0.130** | -1.346 | +0.465 | +0.014 | ✗ | ✗ | ✗ |
| **T3** | period | 57 | 413 | **+0.898** | +1.234 | **-0.336** | -1.475 | +0.418 | +0.378 | ✗ | ✗ | ✗ |

*H3 floor is +0.128 — 25% of the mined delta of +0.511.*

## Detail

| | CAGR | vol | max DD | exposure | entries | min/sym |
|---|---:|---:|---:|---:|---:|---:|
| T1 arm | 5.49% | 5.9% | -9.04% | 19.7% | 1,190 | 9 |
| T1 B&H | 8.34% | 17.8% | -37.92% | 100.0% | 60 | 1 |
| T2 arm | 3.42% | 2.7% | -2.07% | 17.2% | 319 | 1 |
| T2 B&H | 20.02% | 12.5% | -12.56% | 100.0% | 60 | 1 |
| T3 arm | 3.64% | 3.3% | -2.94% | 15.6% | 281 | 2 |
| T3 B&H | 23.72% | 14.1% | -14.06% | 100.0% | 57 | 1 |

## The reading, as declared in advance

> **INSTRUMENT-GENERAL, PERIOD-SPECIFIC. The 2018-24 regime made it. Weak, and consistent with the +0.978 correlation between the two universes.**

