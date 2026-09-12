# Benchmark choice — against what should a long leg be measured?

[← method index](00-index.md) · next: [nulls and block length](02-nulls-and-block-length.md)

**Round 1's central conflict was about the long leg. Round 2 found it was about the BENCHMARK.**

---

## The reduction `[EXT]` `B1`

`A3` reported the long leg failing gross at **Var(t) = 0.98 against the VW market**; `A2` reported
**Var(t) = 1.35–1.81 against each sort's own name-weighted universe.**

> **`B1`, reconciling arithmetically (§4): a mismatched benchmark injects sd 1.2–2.8%/month, which
> predicts Var(t) of 0.76–1.19.** So **0.98 sits inside the artefact's own range** and is *"a
> benchmark artefact."*
> **`[CONFLICT E2]` — recorded as `B1`'s verdict, not adopted. Both stand.**

**And `B1` further reduced the round-1 split to one identity whose sign flipped in this programme's
era.**

## What the literature actually uses, and whether it justifies it `[EXT]` `B1` §2

**It mostly does not.** §2 is the census; §3 does the arithmetic of the alternatives; **§7 asks
whether `A2`'s benchmark is right or BUILDS IN THE ANSWER** — the question a reader should carry into
every long-leg number in this tree.

## The recommendation `[EXT]` `B1` §8

**Measure a long leg against its own equal-weighted universe.** That is what rounds 3 and 4 then did —
**and it produced [`F1`](../signals/02-long-leg-versus-short-leg.md), the campaign's central open
conflict, because two lanes implemented "its own universe" differently.**

## `G3` — and implementing it wrongly is worth 13.6 bp/month and a sign `[CONFLICT G3]`

`C4` used the simple mean of its five quintiles, *"which for an equal-count sort is its equal-weighted
universe."*

> **`D4`: the conditional is right — but if those quintiles use NYSE breakpoints, the simple mean is
> NOT the EW universe.** On French's deciles the same shortcut is **13.6 bp/month and FLIPS THE
> SIGN.**
> **`D4` flags it as a QUESTION for `C4`'s construction, not a refutation. Unresolved — and it is one
> of the two things that would settle `F1`.**

**`C3` did not make that error**, and `D4` reproduced `C3`'s figure to four decimals on a different
script. → [agreement A11](../conflicts/03-agreements.md)

## The SMB exposure an equal-weighted construction acquires `[EXT]` `B1` §9 / `[CONFLICT E1]`

`A3`: CFM attribute the long-leg advantage to **an SMB exposure created by the 2×3 construction.**
**`B1`, reading CFM in full: the SMB exposure appears WHEN THE HEDGE IS THE CAP-WEIGHTED INDEX BLITZ
EXPLICITLY REFUSED**; with Blitz's own 50/50 hedge, CFM find *"no striking difference of Sharpe ratio
between the long and short legs"* and **an optimal short weight of 30%, not zero.**

**`B1` supplies verbatim figure notes and body text; `A3`'s entry is a one-line characterisation.
Both stand.**

## Is a characteristic-matched benchmark constructible from free data? `[EXT]` `B1` §5

Answered there. **And §6 makes the absolute-return case** — the argument that a long-only book should
be scored on absolute return rather than against any benchmark at all, **which is the only framing
under which this programme's actual books are scored.**

## `[REPO]` what this programme does instead, and why it does not collide

This programme scores in **bp/bar on a slot book** and **per trade on the path-invariant lens**, and
**`CLAUDE.md` forbids comparing the two on the same statistic.** Its controls are **rotations of the
book's own names and times**, not factor benchmarks:

| | |
|---|---|
| [FINDINGS §28](../../../FINDINGS.md) | no long signal beats its own names at random times |
| [FINDINGS §32](../../../FINDINGS.md) | **a null must live in the universe the strategy trades** |
| [FINDINGS §50](../../../FINDINGS.md) | removing a book's best names tests nothing **unless every null draw loses ITS OWN best names** |

> **The external benchmark question and this programme's rotation nulls are answers to the same
> question in different currencies.** `B1`'s *"does the benchmark build in the answer?"* is
> §50's *"does the null lose its own best names?"* — **and this programme has already been caught by
> the second, which is the same class of error.**

---

**Sources.** [`R2-01`](../../Scan-100926/R2-01-the-benchmark-question.md) ·
[`R1-02` §7](../../Scan-100926/R1-02-persistent-characteristics.md) ·
[`R1-03` §8](../../Scan-100926/R1-03-the-long-only-problem.md) ·
[`R4-04` §8](../../Scan-100926/R4-04-when-does-the-premium-arrive.md) ·
repo: [FINDINGS §28, §32, §50](../../../FINDINGS.md).
