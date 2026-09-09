# `docs/research/` — the research record

**Research stays here.** By the principal's ruling of 2026-09-09, **nothing in this directory is
elevated into [`FINDINGS.md`](../FINDINGS.md), [`RULES.md`](../RULES.md), the books or a decision
record without his explicit permission.** A tag saying `[EXTERNAL — NOT MEASURED HERE]` is not a
substitute for that permission; that mistake was made once and reverted (`7611123`).

Under [R15](../RULES.md#r15) **nothing here closes or admits anything.**

---

## The lead scan — three rounds, 2026-09-08 → 2026-09-09

| round | record | territories | outcome |
|---|---|---|---|
| **1** | [`the-negative-space-scan.md`](the-negative-space-scan.md) | seven leads from the repo's negative space, then seven external briefs | **11 leads, 3 standing** · **2 method findings** |
| **2** | [`the-forced-seller-and-the-cost-wall.md`](the-forced-seller-and-the-cost-wall.md) | index reconstitution · Form 4 · earnings dates · sizing · execution cost · corporate supply | **4 signal verdicts, none surviving cost** · **4 method findings** |
| **3** | [`the-plumbing-round.md`](the-plumbing-round.md) | fund flows · the death process · halts · 13D/13G · lending revenue · data defects | **6 lanes negative** · **2 live bugs, 1 vendor mechanism, 1 open code check** |
| **4** | [`the-timestamp-round.md`](the-timestamp-round.md) | 8-K item codes · litigation · FDA calendars · the `$5` floor · a second price source · block length | **3 signal lanes dead** · **round 3's own fix broken; the reference implementation ejects; no second source exists** |

**Commissioning contracts and the exclusion lists** — the durable part, because they record what
each round was kept off and why: [`working/leads/README.md`](../../working/leads/README.md) ·
[`working/leads2/README.md`](../../working/leads2/README.md) ·
[`working/leads3/README.md`](../../working/leads3/README.md). **The briefs themselves** sit beside
them in `working/leads/`, `working/leads2/` and `working/leads3/`, under a quarantine contract: a
brief is evidence about the outside world and **never** a measurement on this fixture, and citing
one requires reading the source, because an agent's summary of a paper is not a reading of it.

---

## THE PATTERN ACROSS ALL THREE ROUNDS

**Four rounds, twenty-five briefs, zero strategies — and eleven things the programme was wrong
about.** *(Seven briefs in round 1, six in each of rounds 2, 3 and 4; counted, not estimated.)*

**Round 4 was the first `3 signal + 3 method` slate**, changed from `4+2` on this evidence. **All
three signal lanes died; all three method lanes returned, and two broke something the programme
currently believes.** The design change was correct and the margin was not close. That is not a disappointing result reported apologetically; it is the actual yield, and it
has been consistent enough across three independent rounds to be treated as the expected shape.

| | what it changed | where |
|---|---|---|
| best-of-N floor is blind to **sign-fitting** | a composite of 16 pure-noise signals clears the floor by **+1.28** | R1 |
| the "ETF" fixture is **27% closed-end funds** | 23 of 24 deaths were fund wind-ups, not failures | R1 |
| **Corwin–Schultz understates** small/illiquid spreads | **33.8 bp/side may be a floor, not an estimate** | R2 |
| the **auction cut-off is 15:50** | a close-decided book cannot fill at that close | R2 |
| a scalar factor **cannot** express a spin-off | date-dependent by construction; child has no pre-WI history | R2 |
| **two live bugs** in `d331_edgar_deals.py` | a look-ahead, and a filter that silently returns zero | R3 |
| the vendor documents **two adjustment bases** | the mechanism behind "15m adjusted, daily not" | R3 |
| the delisting-return question is **one code check** | and both answers flatter a long book | R3 |
| **`acceptanceDateTime` has a MIXED timezone** | 35 of 60 are ET mislabelled `Z` — **R3's own recommended fix is unsound** | R4 |
| the **reference implementation** of the literature **ejects** | on 12-month holds whose papers date the screen to formation, and says so nowhere | R4 |
| block length 20 is **~6× too short on persistent conditioners** | the direction that makes nulls **easier** | R4 |

**Why it keeps happening this way.** Every lane is commissioned with a *premise number* — a count,
a rate, an `n_eff` — that must be obtainable **before** any return is measured. Signal territories
die on that number. **Method and data lanes have no premise number to die on**, so what they return
is whatever is actually true about the plumbing. Rounds 2 and 3 each deliberately commissioned two
non-signal lanes for this reason, and both times those lanes outproduced the four beside them.

**The scoring frame did NOT predict this.** Round 1 scored its leads on seven axes; the
lowest-scoring lead ranked first after evidence, and the failing axis was `KILL`, **which was
measuring my knowledge rather than the lead.** Rounds 2 and 3 dropped pre-scoring in favour of
territories with a clear premise number.

---

## MY OWN COMMISSIONING PREMISES THAT WERE WRONG

Recorded together because the pattern matters more than any one of them, and because a scan that
only records what the agents got wrong is not an honest scan.

1. **Round 2 was all route (a).** [`future-strategies.md §0`](../future-strategies.md) names two
   ways out of the liquidity-compensation trap and I commissioned four lanes on the first and none
   on the second. Round 3 fixed it with `G2` and `G3`.
2. **Buyback granular disclosure.** I sent `F6` after data that **does not exist** — the 2023 rule
   was **vacated by the Fifth Circuit on 2023-12-19** before producing any.
3. **Index flow lives in large liquid names.** It does not. It is dead there and alive exactly where
   the per-share cost model is worst.
4. **The Chapter 11 crash is after the last print.** It is normally **inside the tape** — 131
   trading days from filing to delisting on average.
5. **Lending revenue is arithmetically identical to alpha.** Right arithmetically, **inverted
   economically**: selecting for lendability selects for negative alpha.
6. **Route (b) applies to halts.** It does not — a multi-day halt reprices inside **one auction**.
   The move is large but **not slow**.
7. **The spin-off-as-split mechanism explained our 5× shape.** It did not; that was a genuine 5:1
   split across two fixture bases. Withdrawn in
   [`the-forced-seller-and-the-cost-wall.md`](the-forced-seller-and-the-cost-wall.md) §1.4.
8. **The 22:00 EDGAR cut-off applies generally.** It applies to **Schedule 13D/13G only**; I
   generalised it to 8-K when writing round 4's prompt. Amended in
   [`the-plumbing-round.md`](the-plumbing-round.md) §1.1.
9. **`H2`'s resolution leg is "the more interesting half."** It is the deader one — a published
   measured null at N = 2,021.
10. **Route (b) would rescue a lane by inverting the cost ratio.** It inverts the ratio exactly as
    designed and **converts a cost problem into a signal problem**, which is still a problem
    ([`the-timestamp-round.md`](the-timestamp-round.md) §1.8).

**And one correction I asserted and then withdrew**, kept visible in
[`working/leads3/README.md`](../../working/leads3/README.md): I claimed the round-1 record misstated
D264 as forty names. It did not — it was a hypothetical. **Twice in one session I tied a claim to an
existing record without reading the object it pointed at.**

---

## RESEARCH TOOLING — what the briefs learned about the tools themselves

**A hazard worse than a block, and it is now a FOUR-TIME pattern.** **Any figure obtained through a
summariser is WEAKER than `[snippet only]`, not stronger** — a rule added to every round-4 prompt
after round 3, which then caught three more instances inside the round it was added:

| | what the summariser produced | what was true |
|---|---|---|
| R3 `G3` | a **fabricated table** of percentages | not in the document |
| R4 `H4` | *"does not contain explicit price screens"* | **it does** — would have inverted the brief's main finding |
| R4 `H2` | **"12.3%", "14.6–20.6% CAAR"** attributed to a named PDF | the PDF is an **undergraduate honors thesis with none of those numbers** |
| R4 `H6` | — | **refused 5 of 6 PDFs**, the honest failure mode |

**Three of the four are silent failures that look like readings.** The two round-4 briefs that
bypassed the summariser entirely — parsing HTML/JATS locally, extracting every formula with `pypdf`
— produced the round's most reliable numbers.

**AND AN HTTP 200 CAN BE WRONG.** Round 4 found two: **a CDN cache that ignores a query parameter
and silently replays another query's results** (which fabricated two entire harvests before a
negative control caught it), and **a price source that returns a DIFFERENT COMPANY's prices at
HTTP 200** — 23.4% of a 64-ticker delisting panel. **The defence generalises and costs nothing:
when harvesting a parameterised endpoint, census a value that MUST return zero.**

**Two things that look like blocks and are not.** WebFetch's **"corrupted PDF" response is not a
block** — the bytes land on disk and `pypdf` reads them; one round-3 brief converted **seven
"unreadable" fetches into full readings** this way, and several round-2 `[UNVERIFIED]` tags may have
been avoidable. And **every IBKR 403 was a User-Agent exclusion**, not a host block.

**The house rule this earns, already in memory and now confirmed twice more: a logged block names
the TOOL and the RESPONSE, never the host.**

**A privacy slip, disclosed by the agent itself.** A round-3 agent's first `sec.gov` fetch used a
User-Agent containing the principal's **personal email address** before switching to a neutral
string. **The committed code is clean** — `scripts/d331_edgar_deals.py` sends a project mailbox, and
the address appears nowhere in `scripts/`, `docs/` or `data/`. **Any future EDGAR work must use the
project contact string**; SEC fair-access requires an email-shaped token, which is why an agent
reached for one.

---

## WHAT IS OPEN — stated as questions, none of them answered here

**None of these has been measured. All are the principal's to authorise.**

1. **Does a held name falling through the `$5` floor get EJECTED or CARRIED to its delisting?**
   Settleable with no external data. If carried, the Shumway delisting-return bias applies; **if
   ejected, that is an undeclared stop-loss at `$5` truncating every trade's left tail.**
2. **Recompute D285's 33.8 bp/side under EDGE.** It sets the sign of every cost conclusion
   downstream. Closed-form drop-in on the same OHLC inputs.
3. **The two `d331_edgar_deals.py` bugs** — reported, not repaired.
4. **Does the fixture preserve entirely missing sessions, or forward-fill them?** It decides whether
   a multi-day halt is even visible, and it is a prerequisite for counting them.
5. **Reconcile D343's "eight-month halt" against a public record that looks like ~32 months.**
   Neither figure verified here.
6. **Reconcile `FINDINGS.md`'s 1,573-name panel against its 1,580-name build-out figure.**
7. **The cause-of-death census on the equity fixture** — §60's own rule, never applied to it.
8. **Whether `FINDINGS.md` §59 and §60 should stand.** They are the same class of elevation as the
   reverted §61–63, committed before the ruling existed. **Left standing and flagged.**
9. **Key EDGAR look-ahead on the SGML `<ACCEPTANCE-DATETIME>` header, not on the submissions JSON.**
   The JSON field's timezone is mixed; the header reproduced `filingDate` on 60 of 60.
10. **One call would settle the point-in-time listing map**: `LISTING_STATUS` with `date=`,
    cross-checked against SEC MIDAS. Not executed — no key was used and none was registered for.
11. **`adjusted=false` on the intraday endpoint puts both fixtures on one corporate-action basis.**
    The cheapest known fix for a mismatch that has already cost this programme once.
12. **`CLAUDE.md` says per-name rotations carry an irreducible p95 bias. They do not** — random draws
    from a group with the identity included and `p = (1+b)/(1+w)` are exact for any `w`.
    **Amending standing guidance is the principal's call.**
13. **Does this session's regime-conditioner calibration need re-blocking?** It used ~26 bars per
    block on correlations of slow-moving conditioners, where the selector wants ~157. **Flagged,
    not checked.**

---

## The rest of this directory

Earlier work, predating the scan: [`the-signal-hunt-part2.md`](the-signal-hunt-part2.md) ·
[`equity-quote-and-auction-data-proposal.md`](equity-quote-and-auction-data-proposal.md) ·
[`futures-data/`](futures-data/) — **includes the overnight-venue survey (Blue Ocean, IBEOS,
Databento, Tiingo) that is now standing exclusion ground** · [`shorts/`](shorts/) ·
[`Prop-Firm-080926/`](Prop-Firm-080926/).
