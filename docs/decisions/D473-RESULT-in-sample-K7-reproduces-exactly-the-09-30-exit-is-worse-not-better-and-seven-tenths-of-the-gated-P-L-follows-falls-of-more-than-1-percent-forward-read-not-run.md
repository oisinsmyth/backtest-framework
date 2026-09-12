# D473 RESULT (in-sample) — K7 reproduces exactly, the 09:30 exit is worse not better, and seven tenths of the gated P&L follows overnight falls of more than 1%. The forward read is not run.

**In-sample result of the component record D473.** Runner `scripts/run_d473_downleg_component.py --insample`
(`--selftest` passes, including the refusal of `--forward` without the principal's word; 1.2 min),
artefact `data/d473_downleg_insample.json`. **2016-01-04 → 2023-12-29 only; the 2024+ futures
and cash slices are untouched.** The forward read has its own RESULT when and if it runs.

## 0. The component line (the ledger's quantities, computed by the runner)

| K7, one micro, $3 | nights | gross $/night | σ | other side | diff (SE) | hit | skew | worst | **net Sharpe (SE)** | gross Sharpe | N1 p95 | N2 p95 + 2 SE | C-a | C-c | C-d |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| **NQ, exit 09:00 (the candidate)** | 887 of 2,009 (44%) | **+13.32** | 172 | −1.57 | +14.89 (7.19) = **2.1 SE** | 57.3% | +0.35 | −$794 | **+0.62 (0.25)** | +0.80 | 11.27 ✓ | 11.82 ✓ | ✓ | ✓ | ✓ |
| NQ, exit 09:30 (secondary) | 887 | +10.63 | 176 | −1.58 | +12.21 (7.35) = 1.7 SE | 55.6% | +0.38 | −$986 | +0.45 (0.26) | +0.63 | 10.18 ✓ | 10.92 ✗ | ✗ | ✓ | ✓ |
| ES, exit 09:00 (check root) | 904 of 2,015 (45%) | +10.66 | 115 | −1.37 | +12.03 (4.88) = **2.5 SE** | 57.3% | +0.40 | −$685 | **+0.70 (0.26)** | +0.97 | 8.37 ✓ | 8.61 ✓ | ✓ | ✓ | ✓ |
| ES, exit 09:30 | 904 | +9.34 | 121 | −0.82 | +10.16 (5.05) = 2.0 SE | 56.3% | +0.13 | −$875 | +0.55 (0.28) | +0.81 | 8.25 ✓ | 8.50 ✓ | ✓ | ✓ | ✓ |

D470's numbers reproduce to the cent. **C-a passes on the point estimate on NQ and ES at the
primary exit; the multiplicity caveat against it is D470/D472's family failure and is carried in
the ledger row** — this record does not re-litigate it. Correlations on the NQ calendar:
ρ(K7, K1 ES full session) **+0.39**, ρ(K7, the ungated NQ overnight leg) **+0.73**, ρ(K7 NQ,
K7 ES) +0.85. Annual net at one MNQ: +$1,118.

## 1. Three things the in-sample facts say, recorded before the forward read

**The 09:30 exit is worse, not better.** I predicted the 09:00–09:30 leg would add 10–40% to
the mean; it subtracts 20% on NQ and 12% on ES, adds to the worst night (−$986 against −$794)
and takes the NQ Sharpe from +0.62 to +0.45. **The primary exit stands and the secondary is
recorded as the weaker of the two**; the cash replication's 09:30 endpoint was a property of the
cash data, not a better print.

**The dose–response is not monotone on NQ and the effect is at the extremes.** By the size of
the prior overnight fall (exit 09:00, $ per night, SE):

| prior leg | (−25, 0] bp | (−50, −25] | (−100, −50] | ≤ −100 |
|---|---:|---:|---:|---:|
| NQ | +10.57 (6.2), n 380 | −4.53 (11.2), n 196 | +1.69 (14.5), n 170 | **+59.53 (21.8), n 141** |
| ES | +6.19 (4.0), n 454 | +9.12 (7.6), n 211 | +9.17 (9.7), n 148 | **+38.97 (22.2), n 91** |

The ≤ −100 bp bin is 16% of NQ's gated nights and carries **$8.4k of the $11.8k gated P&L**
(71%); on ES it is 10% of nights and 37%. ES is monotone, NQ is not (its two middle bins are
flat at wide SE). **The prediction X-b was half right**: the big-fall bin is 5.6× the small-fall
bin, but on 16% of nights rather than under 15%, and the middle is not ordered. This is written
down now because it is the natural next sharpening and it must not be one: the forward read
tests the declared gate (≤ 0), and the bins are reported forward as they are here.

**The regime.** By trailing-21-day σ tercile, gated / other: high +16.7 / −4.4, mid +32.7 / +11.6,
low −0.2 / −9.6 on NQ (ES: +12.1 / +1.0, +23.7 / −1.3, +4.9 / −4.0). The gated side beats the
other in all three terciles on both roots; the *level* of the gated mean is in the high and mid
terciles. By year the sides are equal in 2016, 2018 and 2019 and apart in 2017 and 2020–2023 —
five of eight years on NQ, six of eight on ES.

**The tail** at one micro: worst night −$794 (2020-03-12), 1% quantile −$496, 0.1% −$714, **no
night below −2% of a $50k account**; the ten worst are all March 2020 and the 2022 selloff
mornings — the gate buys after falls, and its losses are continuation of the same falls. P3 at
minimum size is not the binding constraint; P4 (life) would be, as for every micro construction
here, and is the assembled book's question.

## 2. Predictions

| | predicted | observed | |
|---|---|---|---|
| X-a NQ +0.62, $13.3, σ 172, 887; ES +0.70; 09:30 mean +10–40%, σ +10–20%, Sharpe ±0.1 | | exact; exact; **09:30 mean −20%, σ +2%, Sharpe −0.17** | reproduction right; the secondary exit **wrong in direction** |
| X-b monotone; ≤ −100 bin ≥ 2× on < 15% | | NQ not monotone, ES monotone; 5.6× on 16% | half right |
| X-c worst −$800 to −$1,300; 0 below −2%; q1% −$350 to −$500 | | −$794; 0; −$496 | right (worst just inside) |
| X-d ρ(K7, K1) 0.35–0.55; ρ(K7, ungated) 0.6–0.75 | | +0.39; +0.73 | right |

## 3. Status

**K7 is a component candidate with its in-sample line on the record, C-a..C-d passing at the
primary exit, the family multiplicity caveat recorded, and its promotion test declared and
unrun.** The ledger's *Scored and NOT entered* table carries the row until the forward read
(`--forward --principals-word`) produces PROVISIONAL, FULL, REMOVED or PICK under D473 §3's
rule. Nothing about the gate, the exit or the instrument changes between this record and that
read.
