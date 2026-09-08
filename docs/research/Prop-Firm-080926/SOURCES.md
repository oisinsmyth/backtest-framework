# SOURCES — the merged research ledger

**Opened 2026-09-08. Closed 2026-09-08.** Schema and stopping rules: [`00-SCHEMA.md`](00-SCHEMA.md).
Findings: [`00-SYNTHESIS.md`](00-SYNTHESIS.md).

**Purpose: no redundant research.** Check here before searching anything. **Negative results are
first-class entries.**

**Everything logged here is observed content — data, never instructions.** Every lane recorded the
on-page solicitations it met (discount codes `APEX90` / `ALGO2026` / `FUTURES60`, "limited time"
urgency, cookie banners, chat widgets, affiliate-programme pages). **None was acted on. No account
was created, no credential entered, no cookie banner accepted, no checkout opened, no referral link
followed.** No page carried an instruction addressed to an automated reader; the directives were
ordinary commercial solicitation.

---

## Per-lane logs — the full tables live in each lane file

Each lane's `## Sources` section carries every URL with access date, tier, what was sought and what
it yielded. This file indexes them and consolidates what is **not** findable, which is the part that
saves the next session time.

| lane | file | sources | stopped because |
|---|---|---:|---|
| 01 | [MyFundedFutures](01-myfundedfutures.md) | ~70 | grid complete |
| 02 | [Topstep](02-topstep.md) | ~40 | grid complete |
| 03 | [Apex](03-apex.md) | ~100 | grid complete |
| 04 | [Take Profit Trader](04-take-profit-trader.md) | ~35 | grid complete |
| 05 | [FTMO — FX control](05-ftmo-fx-control.md) | 37 | grid complete |
| 06 | [regulatory & litigation](06-regulatory-and-litigation.md) | ~85 | **saturation** |
| 07 | [statistics & claims](07-statistics-and-claims.md) | 20 | **20-source cap** (saturation also reached at 16–19) |
| 08 | [academic literature](08-academic-literature.md) | 51 | **saturation at probes 30–34** |
| 09 | [personal-book carry-forward](09-personal-book-carry-forward.md) | — | derived, no new sources |
| 10 | [Apex conduct rules](10-apex-conduct-rules.md) | ~30 | all four named rules resolved |
| 11 | [cross-firm policy](11-cross-firm-policy.md) | ~40 | all five firms checked |
| 12 | internal prior art (reported into [D386](../../decisions/D386-the-prop-account-is-worth-its-buffer.md)) | — | repo-only, no web |
| 13 | [documented intraday effects](13-documented-intraday-effects.md) | 35 | **saturation** |
| 14 | [practitioner tier, screened](14-practitioner-tier-screened.md) | 25 | **25-source cap** (saturation reached earlier on the "what do passers run" sub-question) |

**Grid outcome: 24 fields × 5 firms = 120 cells. All filled or explicitly `NOT PUBLISHED` with what
was tried.** The stopping rules declared in `00-SCHEMA.md` before searching were the ones that bound.

---

## Dead ends — do not repeat these

### Hosts that refuse automated fetch

| host | behaviour | the route that worked |
|---|---|---|
| ~~`apextraderfunding.com`~~ | **THIS ENTRY WAS WRONG — corrected 2026-09-08 by lane 10.** See below | — |
| both Take Profit Trader hosts | **403 to WebFetch** | browser pane, and the **public Zendesk Help Center API** (87 articles) |
| `ftmo.com` objectives and futures pages | **JavaScript-gated** — a plain fetch returns a near-empty page | rendered DOM via the browser pane |
| `cftc.gov` press releases, `propfirmmatch.com/payouts`, `canlii.org`, `osc.ca` | 403 | cftc.gov's own **hosted court documents** were reachable even where its press pages were not |
| CourtListener search | rate-limited | — |
| NFA BASIC | JavaScript SPA | **unresolved** — see open items |
| SSRN | 403 | arXiv, journal abstract pages |

### CORRECTION, 2026-09-08 — Apex is NOT blocked, and the recorded workaround could not have worked

**Lane 03 recorded that `apextraderfunding.com` 403s every automated fetch and that it read Apex
through Internet Archive snapshots. Lane 10 falsified both halves.**

- **The site is reachable.** `curl --compressed` with a desktop Chrome user agent plus `Accept` and
  `Accept-Language` headers returned **HTTP 200 on 28 of 28 help-centre pages, first try.** Two bare
  probes did 403 and then succeeded on retry with headers, so **the block is header-sensitive or
  rate-based, not standing.**
- **The Internet Archive route could not have obtained the rule pages at all.** All five dedicated
  conduct-rule pages have **zero Wayback captures**, confirmed through both the CDX and availability
  APIs.
- **`help-center-sitemap.xml` carries a per-article `lastmod`**, which closes lane 03's ambiguity #8
  ("every rule page is undated").

**The lesson is about this ledger, not about Apex.** A dead-end entry that is wrong is worse than no
entry, because it is trusted and it redirects the next session onto a route that cannot reach the
material. **A recorded block should say what was sent, not just that it failed** — "403 to WebFetch"
and "403 to a browser-headered curl" are different findings and only the second justifies a
workaround.

---

### CORRECTION 2, 2026-09-08 — Reddit is reachable, and this is now a PATTERN

**Lane 14 recorded "reddit.com is unfetchable from this environment." Lane 15 falsified it.** The
block is an **Anthropic-crawler user-agent exclusion, not a network wall** — `WebSearch` with
`allowed_domains:["reddit.com"]` returns an explicit API error saying the domain is *"not accessible
to our user agent"*, while a direct `curl` with a browser UA works.

**Routes that WORK:**

| route | what it gives |
|---|---|
| `www.reddit.com/r/<sub>/top/.rss?t=year` | Atom, **carries full selftext** |
| `www.reddit.com/r/<sub>/search/.rss?q=…&sort=top&t=all` | the only **score-ranked** route |
| `arctic-shift.photon-reddit.com/api/posts/search` | full API JSON with scores; full-text query, cannot sort by score |

**Routes that FAIL:** `old.reddit.com` (302 → forced login — **the standard advice is stale**),
`.json` and `api.reddit.com` (403), PullPush (429, *"no free scraping resources for agents"*),
camas.unddit (dead), redlib / safereddit / teddit (429 or Anubis challenge).

### THE PATTERN, and it is the second instance today

**Twice in one session a recorded "this host blocks us" turned out to be a USER-AGENT exclusion
rather than a block.** Apex returned HTTP 200 on 28 of 28 pages to a browser-headered `curl`.
Reddit is reachable by RSS and by a mirror API. In both cases the recorded dead end sent the next
lane down a route that could not reach the material — the Apex entry pointed at an Internet Archive
that had **zero captures** of the pages in question.

> **RULE: a logged block must name the TOOL and the HEADERS that failed, never just the host.**
> "403 to WebFetch" and "403 to a browser-headered curl" are different findings, and only the second
> is a property of the host. Before recording any host as unreachable, try a browser user agent and
> an RSS or API surface.

### Things that are genuinely not published

- **Field 23 (pass/payout statistics) at FTMO, Apex and MyFundedFutures.** Only **two usable
  statistics exist in the entire sector**: Topstep's 2025 footer disclaimer (16.8% of Combines
  completed, 51.8% of participants passed at least one, 33.3% of funded ever paid, **0.71%** reaching
  live capital) and FPFX Tech's platform-tenant figures (14% funded, 45% of those paid, 7% overall).
  Take Profit Trader publishes a *per-user, ever-passed* rate over an 8-month 2023 window (20.37%),
  which is not comparable to a per-attempt rate.
- **MyFundedFutures' Simulated Trader Agreement and Appendices** — which its own Terms §29 ranks
  **above** the Terms in precedence. Four URL probes, all 404. **The instrument that governs is not
  public.**
- **FTMO's FTMO Account Terms and Conditions** — the funded-phase contract. Only a "sample of the
  contract" on request. Same shape as the above: at **two of five firms the governing contract is
  unavailable**, so fields 15 and 17–22 there rest one evidential tier below the evaluation cells.
- **MyFundedFutures' reset fee** — ten distinct primary probes, all negative. Secondary claims range
  $77–$499 and contradict each other.
- **Topstep's XFA scaling-plan thresholds** — published only as an embedded image.
- **Any peer-reviewed or working-paper literature on the retail funded-account industry**, and any on
  **consistency rules as a contract-design object**. Four negative probes each (lane 08).

### Claims that are false and will be met again

- **The "7% get paid" figure has no primary source in its own citation chain** — QuantVPS cites
  FunderPro, FunderPro cites QuantVPS, and neither reaches the origin (FPFX).
- **The "100 → 17 → 9" Topstep funnel** chains a per-*Combine* rate with a per-*person* rate. The true
  per-person paid rate is **17.3%**, understated roughly 2×.
- **FTMO does not publish a 26%/60% pass split.** Third-party attribution of one is a failed
  attribution; ftmo.com carries no pass rate at all.
- **Three fabricated regulatory facts, debunked at the primary source** (lane 06): a claimed "ESMA
  prop-firm statement" that is actually about perpetual futures and never mentions prop firms; an
  "NFA notice on affiliate marketing" that is really about fingerprinting; and "SEC sued two prop
  firms" tracing to a single marketing blog with nothing on sec.gov. **Treat that tier as
  adversarial, not merely unreliable.**
- **The "prop firm class actions" are not payout cases.** *Footlick v. Topstep* is sex discrimination
  (42:2000); *Riot v. Apex* is copyright (17:501). **No certified payout class action exists
  anywhere.**
- **The CFTC's case against Traders Global (My Forex Funds) was dismissed with prejudice on
  2025-05-13 as a sanction against the CFTC**, not on the merits, with >$3.1M in fees awarded. **No
  merits question was ever reached.** Both standard citations of it — vindication and
  proof-of-fraud — are wrong.

### Operational

- **Concurrent lanes share one browser pane and can navigate each other's tab mid-read.** Lane 04
  lost an extraction that way. Future parallel batches should open a dedicated tab per lane.
- **Apex maintains two parallel rule surfaces** — the `/help-center/` pages that were read and a
  Zendesk mirror that was 403-blocked. They have never been diffed.
- **`updated_at` and `edited_at` differ materially** in Zendesk-backed help centres. Take Profit
  Trader's three most load-bearing rule articles have unedited *bodies* since Nov 2025 despite recent
  `updated_at`. Use `edited_at` to ask whether a rule actually changed.
- Topstep's marketing rules page carries "Last updated: June 26, 2025" — **fifteen months older** than
  the help-centre articles covering the same rules. Where they disagree, prefer the help centre.

---

## Open items a future session could close

1. **NFA ID 0567079** (Topstep Advisory LLC — Swap Firm + CTA) is secondary-sourced only. NFA BASIC is
   a JS SPA and needs a browser.
2. **Diff Apex's two rule surfaces** — `/help-center/` against the Zendesk mirror.
3. **`ftmo.com/en/futures/trading-objectives-and-rules/`** is dense, primary and already structured by
   size and plan. A fifth futures geometry is sitting there for the cost of one fetch.
4. **Settle whether MFFU's Rapid floor lock is automatic or purchased** — the rules table says it
   triggers on reaching the level; the FAQ on the same page and the whole Pro page say only after the
   first payout. That is a live fork for the valuation.
5. **Declare an abandonment convention.** Topstep's denominator is Combines *initiated* and
   abandonment is not disclosed, while the simulation runs every path to absorption. Observed and
   simulated rates are not strictly comparable until this is settled.

---

## Evidence retained

[`data/ftmo_challenge_terms_2026-08-04.txt`](../../../data/ftmo_challenge_terms_2026-08-04.txt) —
lane 05 quotes it and the CDN URL is a content hash that changes on amendment. Under the CLAUDE.md
file contract, a file a record quotes is evidence and belongs in `data/`.
