# Research tooling — the hazards, and the defences that cost nothing

[← method index](00-index.md) · prev: [replication and multiple testing](03-replication-and-multiple-testing.md)

**Everything here was learned by being burned.** Each defence is one line of discipline and each was
added *after* a fabrication got through.

---

## 1 · A summariser is WEAKER than `[snippet only]`, not stronger — a four-time pattern

**The rule was added to every round-4 prompt after round 3. It then caught three more instances inside
the round it was added.**

| | what the summariser produced | what was true |
|---|---|---|
| R3 `G3` | a **fabricated table** of percentages | **not in the document** |
| R4 `H4` | *"does not contain explicit price screens"* | **it does** — would have **inverted the brief's main finding** |
| R4 `H2` | **"12.3%", "14.6–20.6% CAAR"** attributed to a named PDF | the PDF is an **undergraduate honors thesis with none of those numbers** |
| R4 `H6` | — | **refused 5 of 6 PDFs — the honest failure mode** |

> **Three of the four are SILENT failures that look like readings.**
> **The two round-4 briefs that bypassed the summariser entirely — parsing HTML/JATS locally,
> extracting every formula with `pypdf` — produced the round's most reliable numbers.**

**And it caught a fifth in round 6:** `K5` derived a closed form itself rather than trust a summariser
and **found the summariser's worked number wrong — 0.3% claimed, 0.2506% computed.**

## 2 · An HTTP 200 can be wrong — nine flavours

**The two that fabricated whole harvests:**

- **A CDN cache that ignores a query parameter and silently replays another query's results.** It
  fabricated **two entire harvests** before a negative control caught it.
- **A price source returning a DIFFERENT COMPANY's prices at HTTP 200** — **23.4% of a 64-ticker
  delisting panel.**

**Two more, both committed as evidence:** a host returning **`text/html`, 1,651 bytes,
`<title>404Handler</title>`** at a `.pdf` URL (`data/k5_rotman_blume_stambaugh_404_at_http200.html`),
and **a retrieval path that silently ignores the parameter the whole census depends on** — an
impossible code returned the identical count to no filter at all.

> **THE DEFENCE GENERALISES AND COSTS NOTHING: when harvesting a parameterised endpoint, census a
> value that MUST return zero.** `K3`'s mandated negative control caught a broken route **before it
> produced a brief.**

## 3 · Two things that look like blocks and are not

- **WebFetch's *"corrupted PDF"* response is not a block** — **the bytes land on disk and `pypdf`
  reads them.** One round-3 brief converted **seven "unreadable" fetches into full readings** this
  way, and several round-2 `[UNVERIFIED]` tags may have been avoidable.
- **Every IBKR 403 was a User-Agent exclusion**, not a host block.

> **THE HOUSE RULE THIS EARNS: a logged block names the TOOL and the RESPONSE, never the host.**
> Already in memory, and confirmed twice more since.

## 4 · Documentation versus code — five instances, and the code was right every time

| | |
|---|---|
| `E9` | docs say `shrout / cfacshr`; **the shipped code computes `shrout * cfacshr`** — a 7:1 split becomes a **49-fold error** |
| `F3` | three second-hand restatements said "lagged"; **the paper and the code comment both say CURRENT** |
| `G6` ×3 | a signal validated against **the wrong variable**; a placebo pair that is **not a clean placebo**; a library whose documentation **misstates both of its seasonally-differenced variants** |

> **Round 3 found the first of this class; round 4 found three more. THE CLASS IS NOW FIVE INSTANCES
> AND SHOULD BE ASSUMED, NOT DISCOVERED.**

**And it is not only external:** **Ken French's documentation says four different things**, and the
page one lane relied on **is the odd one out** (`D3` §1.3).

## 5 · Draft versus published — three instances, twice the sign flipped

- A paper whose **draft and published abstracts differ in SIGN** (+0.02% → −0.01%), **and whose prose
  disagrees with its own tables** on three high-fee shares (`D8`).
- The founding decay paper: **82 characteristics / ~10% / 35%** in draft against **97 / 26% / 58%** in
  publication (`F5`).
- **A 9% versus 53.5% swing on one winsorization choice** between draft and published versions of the
  paper that **invented the term "non-standard errors"** (`F7`).
- **And the freely-indexed one can be the wrong one:** a draft says turnover predicts post-2005 net
  returns; **the published version says no predictor is reliable and turnover enters with the wrong
  sign.**

> **The campaign then made the error itself**, collapsing a **6 May 2014 working paper** into the
> published 2015 article inside its own record. Caught by round 4, **corrected in place, and recorded
> as the commissioner's error rather than the lane's** — the lane had tagged it `[WORKING PAPER]` and
> listed the published version among what it could **not** verify.

## 6 · Operational hygiene

- **A shared scratchpad is not harmless.** **263 files, one directory, every agent across five
  rounds** — and **two agents silently overwrote each other's helper script mid-run.** **Lane-unique
  filenames are now required.**
- **A privacy slip, disclosed by the agent itself:** a first `sec.gov` fetch used a User-Agent
  containing **the principal's personal email address.** The committed code is clean. **All future
  EDGAR work uses the project contact string.**
- **A zero hit count in an overlap audit means the lane does not OVERLAP. It does not mean the
  question is NEW.** The commissioner conflated the two and a whole named literature was sitting
  there. *(Already a standing memory.)*

## 7 · The tagging discipline every brief carries

`[read in full]` · `[abstract only]` · `[snippet only]` · `[UNVERIFIED]` · **`[MEASURED IN BRIEF]`**
means an agent measured a **public** file or endpoint — **never this fixture.**

> **Under [R15](../../../RULES.md#r15) nothing in the research tree closes or admits anything.**

---

**Sources.** [`../README.md` §"Research tooling"](../../README.md) ·
[`the-timestamp-round.md` §1.3, §1.4](../../the-timestamp-round.md) ·
[`the-selection-round.md` §1.12](../../the-selection-round.md) ·
[`the-reversal-round.md` §1.9, §1.10](../../the-reversal-round.md) ·
[`R4-01` §10](../../Scan-100926/R4-01-the-nine-unexamined-nodes.md) ·
[`R4-03` §1.2, §1.3](../../Scan-100926/R4-03-are-these-two-signals-the-same-signal.md).
