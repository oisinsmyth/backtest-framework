# 02 — The data-acquisition prompt for the prop side

**Recorded 2026-09-10.** A ready-to-paste prompt for a fresh session, plus the reasoning behind each
constraint in it. **The prompt itself is §2; everything else is why it says what it says.**

> **This is infrastructure, not a study.** [R8](../RULES.md#r8) pre-registration is owed by the
> measurements in [`01-prop-lead.md`](01-prop-lead.md) §8, **not** by the fetch. Acquiring the data
> does not open, close or admit anything.

---

## 1. Why this fetch, and what it unblocks

[`01-prop-lead.md`](01-prop-lead.md) §6.1: **we hold no futures data.** Every number on the prop
track — C1's +9.04%/yr, its MAE p99 of 3.98%, the 6.40-year expected life — is measured on an
**extended-hours equity proxy covering 16 of 23 futures hours.** The instrument the book would
actually trade has never been looked at.

**Three of the five items in `01` §8 are gated on this fetch:**

| gated item | what it needs |
|---|---|
| **§5.1 · the settlement check** | **ES on days matched to SPY.** If the overnight drift is a T+1 cash artefact it may not exist in a T+0 future at all — and C1 is the only candidate still open |
| **§3 · C1's size sweep below 0.48×** | the **intrabar path** on real futures, in **dollars per contract** |
| **§4 · the hold-length curve** | the same path at **every** hold length, which is the whole point |

**And one item is priced separately and is trivially cheap:** `P(MAE ≤ $2,000/contract)` for the
last-30-minute trade — **~$8**, the single query `01` §6.1 names.

## 2. THE PROMPT

Paste everything between the rules into a fresh session in this repo.

---

> **Task: acquire a CME futures fixture for the prop track, validate it, and commit it. Do not run
> any study on it.**
>
> **Read first, and do not re-derive what they already establish:**
> `docs/prop firm leads/01-prop-lead.md` (§6.1 the data gate, §6.2 the breadth correction, §8 the
> order of work) · `docs/research/consolidated/data/05-futures-data-sources.md` (the vendor answer
> and its three traps) · `docs/research/futures-data/00-SYNTHESIS.md` §1 and §6 (the rate
> derivation, and the roll warning) · `docs/BOOK_PROP.md` (what the fixture is for) ·
> `CLAUDE.md` and `docs/RULES.md`.
>
> ### Hard boundaries
>
> 1. **I create the Databento account and obtain the API key. You do not.** Stop and ask if no key
>    is present in the environment. **Never enter payment details, create accounts, or accept terms
>    on my behalf.**
> 2. **Budget cap: the `$125` signup credit, and you must not exceed `$110` of it.** Report the
>    projected spend and **wait for my go-ahead before any billable call.**
> 3. **This is a fetch, not a study.** No returns, no signals, no strategy code. If you find
>    yourself computing an edge, stop.
> 4. **Nothing here is elevated into `FINDINGS.md`, `RULES.md` or either book.**
>
> ### What to acquire
>
> **Dataset `GLBX.MDP3`, schema `ohlcv-1m`, `stype_in="continuous"`.** ES from 2010-06-06 is the
> full available history.
>
> **Tier 1 — the four equity indices, and get these even if the budget forces a cut elsewhere:**
> `ES`, `NQ`, `RTY`, `YM`. **RTY reaches only ~9 years — the E-mini Russell moved to CME in 2017.
> That is market structure, not a vendor limit; do not treat the short history as an error.**
>
> **Tier 2 — the diversified complex.** `01` §6.2: a 12-symbol complex has **effective breadth
> 3.00** against **1.17** for four equity indices, *"worth `√2.6 ≈ 1.6×` on IR for any candidate
> with a positive edge."* Extend across **energy, metals and rates**. **Propose the symbol list
> with a per-symbol cost line and let me approve it** — do not assume my mapping of "the complex"
> onto CME products is right.
>
> **Tier 3 — the micros, and say so if the budget cannot carry them:** `MES`, `MNQ`, `M2K`, `MYM`.
> **Reason: C1's sizing sweep lands at 0.48× and a fractional ES contract does not exist.** A micro
> is 1/10 of its e-mini, so **the micros are what the sizing actually trades.** They list from 2019,
> so use the e-mini for the price path and the micro only for contract-size and cost realism.
>
> ### Cost discipline, before anything billable
>
> 1. **Call `list_unit_prices(dataset="GLBX.MDP3")` first.** The published rate rests on **one
>    inferred step** — that `ohlcv-1m` bills like `trades`. This confirms it in 30 seconds. **Report
>    the actual table.**
> 2. **`get_billable_size` and `get_cost` on every request before submitting it.** Give me a total.
>    The prior estimate is **~$0.51/symbol-year**, so ES+NQ+RTY+YM over 15 years should land near
>    **$30**. **If your dry run differs by more than 2×, stop and tell me — do not proceed.**
> 3. **Use `batch.submit_job`, never streaming. Streaming re-bills on retry**; batch bills once and
>    allows 30 days of free re-downloads.
> 4. **Never `stype_in="parent"`** — it resolves to every outright *plus* every calendar spread, and
>    it will burn the credit.
> 5. The credit **expires in 6 months, is one set per team, and they police farming.** Do not create
>    a second account under any circumstances.
>
> ### Validation gates — the fixture is NOT usable until all of these pass
>
> **Write each as an assertion that RAISES, and prove each one fires by breaking what it reads.**
> This repo has been caught three times by an unexamined corporate-action or instrument basis.
>
> 1. **The roll is a construction, and you must record which one.** A continuous series is stitched.
>    **State the roll rule and the adjustment basis (unadjusted / ratio / difference) explicitly in
>    the fixture metadata, and emit the roll dates as a separate committed artifact.**
> 2. **THE ROLL TRAP, AND IT IS THE ONE THAT MATTERS MOST HERE.** The downstream consumer measures
>    **maximum adverse excursion against a ratcheting floor.** **A synthetic roll gap in an adjusted
>    series will be scored as an adverse excursion that never happened.** Assert that no roll date
>    produces a bar-to-bar move outside the distribution of non-roll moves, and **flag every roll
>    date so the MAE code can exclude or handle it deliberately.**
> 3. **Contract multipliers and tick sizes, per symbol, committed as data.** The 4% MLL is a
>    **dollar** limit (`$2,000` on a 50K), so a path in index points is not usable. ES is `$50`/pt
>    and MES `$5`/pt — **verify every one from the exchange's own spec, do not hardcode from
>    memory.**
> 4. **Session calendar.** `GLBX.MDP3` is the full ~23-hour Globex session with **no RTH filter**.
>    **Assert the session boundaries you find rather than assuming 18:00→17:00 ET**, and record how
>    holidays and half-days appear. **Count the sessions and state the number.**
> 5. **Bars are absent, not fabricated.** *"No bar prints for a minute without a trade"* is the
>    assumption the whole cost estimate rests on. **Assert there is no forward-fill**, and report
>    the empty-minute rate per symbol per session — it is a liquidity measurement in its own right.
> 6. **A negative control on the harvest.** *"When harvesting a parameterised endpoint, census a
>    value that MUST return zero."* Request a symbol or date range that **cannot** exist and assert
>    it returns nothing. **Two harvests in this programme's research were fabricated by an endpoint
>    that silently ignored its parameter, and a mandated negative control caught a third before it
>    produced a brief.**
> 7. **Cross-check ES against the equity fixture.** ES and SPY track the same index. **Correlate
>    daily closes over the overlapping window and state the number.** This is the cheapest possible
>    check that you downloaded the instrument you think you did — *"an HTTP 200 can be wrong"*, and
>    one catalogued flavour is **a price source returning a different company's prices at HTTP
>    200.**
>
> ### Where it goes
>
> - **Raw downloads → `temp/`** (deletable any time, unasked, unread).
> - **The validated fixture and its metadata → `data/`.** A file a record quotes is evidence.
> - **The loader/validator → `scripts/`.**
> - **Cache any costly derived array in `temp/`, keyed on the fixture AND every producing module's
>   mtime.**
> - **Do not re-download to recover from a mistake** — batch allows 30 days of free re-downloads;
>   use them.
>
> ### Operating rules
>
> - **Anything over ~2 minutes → `run_in_background: true`. Never `nohup` or `&`.** **Never pipe a
>   background command through `tail`/`grep`** — redirect to a log file and tail that. **Never
>   poll**; you are re-invoked on real exit.
> - **State the projected wall time before launching anything over ~10 minutes, do one optimisation
>   pass, and say what you did.**
> - **A logged block names the TOOL and the RESPONSE, never the host.** Every IBKR 403 in this
>   programme's research was a User-Agent exclusion.
> - **Use the project contact string for any SEC or vendor identification. Never a personal email.**
>
> ### What to report when done
>
> 1. **Actual spend against the `$125` credit, and what remains.**
> 2. **Every symbol, its date range, its bar count, and its empty-minute rate.**
> 3. **The roll rule, the adjustment basis, and the roll-date artifact's path.**
> 4. **Each validation gate: passed, and the evidence it fired when deliberately broken.**
> 5. **The ES↔SPY correlation number.**
> 6. **What you could NOT verify, stated plainly** — and anything you chose not to open.
>
> **Do not proceed to any measurement in `01-prop-lead.md` §8. Those need their own
> pre-registration under R8, committed before their runner exists.**

---

## 3. The four constraints in that prompt that are not obvious

**Why the human does the signup.** Creating accounts and entering payment details are not things an
agent does on the principal's behalf, credit or no credit. **The split is: I sign up and hold the
key; the agent verifies pricing, dry-runs the cost, waits for approval, then fetches.**

**Why the roll trap gets its own gate.** Every downstream consumer of this fixture measures **MAE
against a ratcheting floor.** An adjusted continuous series contains **synthetic** bar-to-bar moves at
each roll. **Scored naively, a roll gap is an adverse excursion that never happened** — and on a 4%
floor that is the difference between a candidate clearing P4 and breaching. This is the same class as
the thirty fabricated return days of [FINDINGS §18](../FINDINGS.md) and the 15m-versus-daily
adjustment split, and it is the first time it would bite the prop track.

**Why the micros are in scope.** C1's vol-targeted sizing lands at **0.48× average size**, and
**there is no fractional ES contract.** A micro is 1/10 of its e-mini, so **the micros are the
instrument the sizing rule actually implies.** Nobody has said this in any record — the sizing sweep
was run in continuous notional.

**Why ES↔SPY is the last gate.** It costs nothing, it uses a fixture we already hold, and it is the
only check that answers *"is this the instrument I think it is?"* rather than *"is this file
well-formed?"* — which is exactly the gap that the nine catalogued flavours of wrong HTTP 200 live
in.

## 4. What this fetch does NOT buy

- **It does not supply an edge.** `01` §0: the candidate list is exhausted and a fifth candidate
  needs a new mechanism.
- **It does not settle §1 or §2 of `01`** — the ladder and `P(pass)` are computable **today**, on
  machinery that already exists, and **neither needs futures data.** If only one thing is done
  next, it should be those, not this.
- **It does not remove the equity proxy's results** — it makes them checkable against the
  instrument, which may confirm or invert them.
