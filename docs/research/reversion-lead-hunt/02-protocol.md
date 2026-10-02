# Debate protocol (both agents in a pair follow this)

You are one of TWO agents in a pair: one CONSERVATIVE, one CREATIVE. You talk to your partner DIRECTLY with the
`SendMessage` tool (load it with `ToolSearch` query `select:SendMessage` if needed), addressed to your partner's
agent ID. **The main session will send you your partner's ID in a message shortly after you start; until it
arrives, do Phase 1 on your own.** Do not message the main session except as described at the end.

## Files

- Your pair's directory (given in your prompt) holds:
  - `<role>_notes.md` — your own working notes and candidate list (only YOU write your file; your partner may read it);
  - `scripts/` and `out/` — premise-test scripts and outputs (prefix your files with your role, e.g. `crea_...`);
  - `AGREED.md` — the agreed leads. **Only the CONSERVATIVE writes it**, after each lead is explicitly accepted by both.
- Do not read the other pair's directory (the pairs must stay independent).

## Phase 1 — independent work (before the debate)

- Read `BRIEF.md` (one level up), `CLAUDE.md`, `docs/data-available.md`, `docs/research/mean-reversion-inventory.md`,
  and whatever records you need. Search the web for mechanisms and papers.
- **CREATIVE:** generate at least 10 candidate effects, deliberately outside the repo's well-worn paths
  (other markets' structure, other participants' constraints, exchange mechanics, cross-market linkages, calendar
  and institutional rules, option-market plumbing, data the repo has but has not used for reversion). Run quick
  premise tests on the most promising.
- **CONSERVATIVE:** build your own candidate list (at least 5), weighted toward mechanisms with documented forced
  flow and strong evidence; and write an audit checklist from the repo's failure modes (sub-cost size, momentum in
  disguise, 2020–2022 concentration, look-ahead, rotation-null equivalence, decay as markets deepen, rare and lumpy,
  multiple testing across your own search). Run premise tests too.

## Phase 2 — the debate (direct messages)

- Open by sending your partner your candidate list: each with a one-paragraph mechanism, the novelty argument, and
  any premise-test numbers (script path + gross/net per micro + n + year split).
- **The conservative attacks; the creative defends, repairs, or replaces.** Disputes are settled by evidence: either
  of you may run a test and send the script path and numbers. Keep messages dense and specific (no pleasantries).
- The conservative may also propose leads, and the creative may attack them.
- A lead is ACCEPTED only when both of you say so explicitly in a message. The conservative then appends it to
  `AGREED.md` in the BRIEF's output format, with the verdict/rebuttal line filled in.
- Replace dropped candidates with new ones and keep going. **Do not finish until `AGREED.md` holds 5 solid leads**
  that meet the BRIEF's bar. If, after real effort, a lead is accepted with a reservation, record the reservation;
  never pad the list with leads you do not believe.

## Waiting

- When you have sent your partner something that needs a reply, you may end your turn with a one-line status; your
  partner's reply will resume you. **Never end your turn without either (a) having sent your partner a message that
  needs a reply, or (b) being finished.** Never sleep or poll.

## Finishing

- When `AGREED.md` holds 5 accepted leads, the CONSERVATIVE writes `FINAL.md` in the pair directory: the 5 leads
  (ranked, with the prior for each), the strongest candidates that were dropped and why (one line each), and any
  dissent. Then the conservative tells the creative it is done.
- Your FINAL reply (your last message, which reaches the main session automatically) must be: for the conservative,
  the contents of `FINAL.md`; for the creative, at most 10 lines: what you would rank differently and any dissent.
