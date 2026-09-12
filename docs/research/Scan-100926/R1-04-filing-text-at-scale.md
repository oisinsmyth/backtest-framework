# R1-04 — FILING TEXT AT SCALE

**Lane A4, campaign Scan-100926, round 1.** External evidence only. Nothing here touches the
programme's private data and no claim is made about it. Under [R15] nothing in this file closes or
admits anything.

**Contact string used for every SEC fetch:** `Backtest-Framework-Research research@backtest-framework.org`.
Pacing 0.38–0.50 s between requests, single-threaded, one process. No account, no credential, no
form, no API-key registration. Scratchpad files all prefixed `A4_`.

**Every measurement in this brief is re-runnable.** The probe scripts, their raw logs, and the
derived JSON are in [`data/A4-filing-text/`](../../../data/A4-filing-text/) — per `CLAUDE.md`, a file
a record quotes is evidence and belongs in `data/`. Each `[MEASURED IN BRIEF]` claim names the script.

---

## 0. THE ANSWER, STATED FIRST

**Text-level work is NOT out of reach at this programme's scale. The volume question is not the
binding constraint and the arithmetic is not close.** A 2010–2026 pass that finds every 8-K
containing a dividend-declaration phrase, resolves it to a filing, and attaches that filing's 8-K
item codes and its exact acceptance timestamp costs **~40,000 requests and ~0.31 GB — about 2¼ hours
at 5 requests/second.** [MEASURED IN BRIEF, §5]. The naive route — download the dissemination feed —
costs **4.39 TB** [MEASURED IN BRIEF, §5], and that is the number that has been scaring this
question off. It is the wrong route.

**The binding constraint is the extraction step's error rate, and specifically its RECALL, which
nobody has measured — including the one paper that does this exact task.** The best published
precision on 8-K event tagging is 96%, but only by discarding 66% of tags, on a corpus that starts
in **2022** (4½ of this programme's 16½ years), and the paper **never reports recall at all**
(§3.1). The best peer-reviewed error rate for extracting a typed *numeric fact* from filing prose —
with professional-auditor gold labels and 1.1M training sentences — is **78.0 micro-F1, i.e. a 22%
entity-level error rate** (§3.3). An NER tagger trained on SEC filing text scores **66.7% precision
in-domain** (§3.4) — within a point of this programme's own measured 67% phrase-match precision.

**And there is a specific reason that matters more than the level of the error rate.** Round 5's
statistic is a *share*: what fraction of dividend/split announcements arrive inside an earnings
release. A phrase-matching step's misses are **not plausibly independent of that share** — a
declaration buried in a nine-page earnings release is harder to phrase-match than a standalone
three-paragraph dividend release, which means the measurement error is correlated with the thing
being measured and **biases the absorption share in a knowable direction (downward on absorption)
but by an unknown amount.** §3.6. That, not bytes, is what stands between this lane and closing
round 5's open question.

**What I would therefore report as the lane's result:** the route exists, is cheap, is licensed, and
has a documented error rate for the extraction step — **but the documented error rate is a
*precision* figure, and the statistic round 5 needs is a share whose bias is governed by *recall*,
which is undocumented everywhere I looked.** Closing round 5's question needs a hand-built gold
standard of a few hundred filings. That is a day of work, not a data-acquisition project.

**And I ran the route end to end on one month to check it is real** (§3.7). 493 matched documents →
337 filings → `.hdr.sgml` retrieved **337/337, zero failures** → **60.2% carry Item 2.02 (results of
operations).** Round 5 measured **62.2%** of dividend initiations absorbed into an earnings release.
**Two layers that could not see each other land 2 points apart.** That is corroboration worth having
and it is **not** a result: it is one month, January is the seasonally worst month to pick, round 5's
population was *initiations* rather than all declarations, and the phrase family's recall is still
unmeasured. Do not quote 60.2% as an annual figure.

---

## 1. WHAT IS FREE AND BULK-RETRIEVABLE FOR FILING TEXT

### 1.1 The four products, measured

All sizes below are `Content-Length` from live HEAD requests [MEASURED IN BRIEF, 2026-09-10].

| Product | What it is | Back to | Size, measured |
|---|---|---|---|
| **EDGAR full-text search** `https://efts.sec.gov/LATEST/search-index` | Per-*document* inverted index over filing bodies **and exhibits** | **2001** (documented and confirmed, §1.3) | JSON, ≤100 hits/page, **hard 10,000-hit ceiling** |
| **Quarterly full index** `/Archives/edgar/full-index/YYYY/QTRn/master.idx` | One row per filing: CIK, name, form, date, path | 1994Q3 | 26.8 MB (2010Q1) → 32.4 MB (2021Q1) → 33.2 MB (2026Q1); `.gz` 4.47 MB, `.zip` 4.26 MB |
| **Daily index** `/Archives/edgar/daily-index/YYYY/QTRn/master.YYYYMMDD.idx` | Same, one business day | 1994 | 460 KB (`master.20210104.idx`, 5,327 rows, 241 × 8-K, 6 × 8-K/A); `form.20210104.idx` 805 KB |
| **Dissemination feed** `/Archives/edgar/Feed/YYYY/QTRn/YYYYMMDD.nc.tar.gz` | **Every document of every filing that day**, SGML-wrapped, in one tarball | 1994-ish | **136 MB (2010-01-04) → 674 MB (2021-01-04) → 2.65 GB (2023-03-10)**; 33-day sample below |
| `submissions.zip` | Per-CIK filing histories (metadata, not text) | — | **1,562,779,836 B = 1.56 GB**, 2026-09-10 |
| `companyfacts.zip` | XBRL facts (not text; lane A1's territory) | — | 1,408,478,936 B = 1.41 GB |

`/Archives/edgar/Oldloads/20210104.nc.tar.gz` → **HTTP 403** (not 404). The Oldloads directory
exists but that filename pattern is not it; I did not chase the correct pattern.

The old CGI full-text endpoint `/cgi-bin/srqsb?text=test` → **HTTP 503**. Dead; do not build on it.

### 1.2 Feed tarball sizes, 33-day sample across the window

Two sample dates per year, 2010→2026, walking forward to the next day the feed exists
[MEASURED IN BRIEF, `A4_feed_sizes.py`]:

```
2010-03-10   288 MB    2016-03-10   805 MB    2022-03-10  1573 MB
2010-09-15   218 MB    2016-09-15   542 MB    2022-09-15  1734 MB
2011-03-10   239 MB    2017-03-10   886 MB    2023-03-10  2645 MB
2011-09-15   333 MB    2017-09-15   477 MB    2023-09-15  1718 MB
2012-03-12   368 MB    2018-03-12   937 MB    2024-03-11  2263 MB
2012-09-17   161 MB    2018-09-17  1012 MB    2024-09-16  1703 MB
2013-03-11   502 MB    2019-03-11   909 MB    2025-03-10  2364 MB
2013-09-16   349 MB    2019-09-16  1182 MB    2025-09-15  1854 MB
2014-03-10   629 MB    2020-03-10   712 MB    2026-03-10  2199 MB
2014-09-15   359 MB    2020-09-15  1654 MB
2015-03-10   569 MB    2021-03-10  1372 MB    n=33 mean 1041 MB, median 886 MB
2015-09-15   298 MB    2021-09-15  1486 MB
```

Per-year mean × trading days, summed over 2010-01 → 2026-08: **4.39 TB compressed.** Flat-mean ×
4,187 days: 4.36 TB. The two agree, so the growth trend does not change the order of magnitude.

### 1.3 EDGAR full-text search: PARAMETERS, with the zero-control beside every count

**THIS IS THE SECTION THE LANE BRIEF WARNED ABOUT, AND THE WARNING WAS CORRECT AND INCOMPLETE.**

Base query throughout: `q="declared a quarterly dividend"`, `forms=8-K` where stated,
`dateRange=custom&startdt=2021-01-01&enddt=2021-01-31` where stated. Full script:
`A4_fts_probe.py`, `A4_fts_probe2.py`. [MEASURED IN BRIEF]

| Parameter | Control value that must return zero | Result | Verdict |
|---|---|---|---|
| `q` | `"zzqxvnqq impossible control phrase"` | **0** (`relation: eq`, 977-byte body) | **works** |
| `forms` | `ZZ-NOTAFORM` | **0** (1,014 B) | **works** |
| `startdt`/`enddt` | 1995 window; also `startdt` after `enddt` | **0** both (1,070 B) | **works** |
| `ciks` | `0000000001` | **0** (1,007 B); real CIK `0000752642` → 81 | **works** |
| `items` | `9.99`, and the literal string `GARBAGE` | **10,000 / 61,842 bytes — BYTE-IDENTICAL to no filter** | **SILENTLY IGNORED — CONFIRMED** |
| `locationCode` (singular) | `ZZ` | **10,000 / 63,920 B — byte-identical to baseline AND to a parameter named `zzgarbageparam`** | **SILENTLY IGNORED — NEW** |
| `locationCodes` (plural) | `ZZ` | **0**; `NJ` → 1,029 | **works** |
| `category` | `not-a-category` | 10,000 / 63,923 B = baseline | **silently ignored** |
| `hits` | `100` | identical total, body 1 byte longer | **ignored (no page-size control)** |
| `from` | `9990` and `10000` | HTTP **200** with `hits.total` **absent entirely** and a 1,132-byte body | **hard window; see below** |

**Three things follow and each is load-bearing.**

1. **The prior round's finding on `items` is confirmed, and its cause is now known: `items` is not a
   documented EDGAR FTS parameter at all.** The official FAQ (§1.4) lists exactly four filters —
   form type, company name, CIK, date range. There is no item filter in the UI or the FAQ. The
   endpoint ignores *any* unrecognised parameter silently; `zzgarbageparam=1` returns the same
   63,923 bytes as `category=not-a-category` and as `locationCode=ZZ`. **So the failure mode is not
   "a filter that lies"; it is "unknown parameters are dropped without error".** That is worse,
   because it means a *misspelt* real parameter behaves exactly like a nonexistent one — which is
   precisely what `locationCode` vs `locationCodes` demonstrates: **one letter decides whether your
   filter applies, and the wrong spelling returns a plausible, larger, wrong answer at HTTP 200.**
2. **`forms=8-K` filters on the ROOT form and therefore INCLUDES 8-K/A.** In a 2015 census,
   `forms=8-K` returned 670 and the first page contained **99 × `8-K` and 1 × `8-K/A`**, every one
   with `root_forms: ["8-K"]`. `forms=8-K/A` is an exact filter (4/4 hits were 8-K/A). **You cannot
   exclude amendments with `forms=`; you must filter client-side on `_source.form`.** §4.
3. **10,000-hit hard ceiling.** Any slice returning `relation: "gte"` at `value: 10000` is truncated
   and you are not told which hits were dropped. `"declared a quarterly dividend"` over the whole
   2010-01-01 → 2026-08-26 window hits the ceiling; **per-year slices do not** (max 698). So the
   window must be sliced, and the slice must be chosen by measuring, not assumed.

### 1.4 Documented syntax and limits, from the SEC's own FAQ

`https://www.sec.gov/edgar/search/efts-faq.html`, fetched and de-tagged locally
[PRIMARY DATA DOC] [read in full]:

> "Full-Text Search will allow you to search the full text of all EDGAR filings submitted
> electronically **since 2001**. The full text of a filing includes all data in the filing itself as
> well as all attachments (such as exhibits) to the filing."

Confirmed live: 2000 window → 0; 2001 window → 78; 2004 → 361 [MEASURED IN BRIEF].

> "Wildcard searches on stem words are supported by appending a `*` … **is not supported in exact
> phrase matches or in boolean searches**."

Confirmed: `"declared a quarterly divid*"` inside quotes → **0 hits** [MEASURED IN BRIEF].

Boolean `OR`, `NOT`, `-`, and `NEAR(n)` (default 10 words) are documented. Confirmed: an OR of two
phrases returned 94 where the phrases alone returned 45 and ~50; `"stock split" -"reverse"` returned
212; bare `declared quarterly dividend` (implied AND) returned 864 [MEASURED IN BRIEF].

**NO STEMMING, and this one is easy to trip over.** Jan-2021, `forms=8-K`: `dividend` → **2,456**;
`dividends` → **2,414**; `dividend*` → **3,202**; `"dividend"` in quotes → 2,456 (identical);
`DIVIDEND` → 2,456 (case-insensitive, as documented). **Singular and plural are different tokens
and neither is a superset of the other.** [MEASURED IN BRIEF, `A4_last.py`]

**What the FTS JSON gives you per hit:** `_id` = `accession:filename`, `ciks`, `display_names`
(with tickers), `form`, `root_forms`, `adsh`, `file_date`, `period_ending`, `sics`, `biz_states`,
`file_num`, `film_num`, `sequence`, `xsl`. **It does NOT give an acceptance timestamp.** `file_date`
is the filing date. §4.

**One hit ≠ one filing.** FTS indexes each *document* separately. In Jan-2021, 45 hits resolved to
**38 distinct accessions (ratio 0.844)**; 7 accessions matched on two documents each (typically the
8-K body *and* its EX-99.1 press release). Any count of FTS hits over-states filings by ~19%
[MEASURED IN BRIEF].

All 100 indexed documents in a Jan-2021 sample were `.htm`. I found **no** evidence in this sample
that PDF-only exhibits are indexed, and no evidence that they are not. Unresolved.

### 1.5 Byte-range behaviour is PATH-DEPENDENT — a conflict with the carried-forward finding

The campaign rules carry "SEC silently ignores Range headers". **That is true on some paths and
false on others** [MEASURED IN BRIEF, `A4_docsize.py`]:

- `full-index/2021/QTR1/master.idx` with `Range: bytes=0-999`, `Accept-Encoding: identity` →
  **HTTP 200, 32,441,322 bytes returned, no `Content-Range`.** Range ignored, despite the HEAD
  response advertising `Accept-Ranges: bytes`.
- `Feed/2010/QTR1/20100104.nc.tar.gz` with `Range: bytes=0-4095` → **HTTP 206,
  `Content-Range: bytes 0-4095/136165356`, 4,096 bytes.** Range honoured.

**Record both. I would weight the measurement over the carried rule** because the rule is stated
without a path and I have the path for each. Practically: **never assume a Range worked — compare
the returned length to the requested length.** A 32 MB body at HTTP 200 where you asked for 1 KB is
the eleventh flavour of a wrong 200.

### 1.6 Two more wrong-200 / wrong-status flavours measured here

- **`efts.sec.gov` intermittent HTTP 500 with a 36-byte body.** 3 of 22 requests in the first probe
  pass (~14%) at 0.35 s pacing returned HTTP 500, 36 bytes. **All three succeeded on retry** at
  0.40 s with identical queries. Not a rate-limit 429, not a content error — transient. **A harvest
  without retry-on-500 silently loses ~14% of slices.** (Compare: one agent last campaign lost 286
  of 352 filings to unpaced threads. This is the same failure with a different cause.)
- **Identical `took` proves a cached replay.** Four identical repeats of `q=dividend` returned the
  same total (2,456) — good. But three repeats of an unsliced query returned **byte-identical
  63,312-byte bodies with the same Elasticsearch `"took":559`.** A repeat that returns the same
  `took` is **not** an independent confirmation; it is the cache. To re-verify a count, perturb the
  query (e.g. shift the window by a day) rather than repeat it.
- `https://efts.sec.gov/robots.txt` → **HTTP 403, 23-byte body `{"message":"Forbidden"}`.** There is
  no robots.txt on the FTS host.

### 1.7 The critical path correction: the accession prefix is the FILER AGENT's CIK

`/Archives/edgar/data/<CIK>/<accession-no-dashes>/<file>` **404s with a 291–305-byte gzipped S3
`NoSuchKey` body if you use the CIK embedded in the accession number.** For
`0000059255-10-000008` the accession prefix CIK is 59255 but the issuer is CIK **1011657**; with the
issuer CIK every path 200s, with the prefix CIK every path 404s — *including* paths that the same
directory's `index.json` lists as present. [MEASURED IN BRIEF, `A4_paths.py`, `A4_repeat.py`]

The SEC's own documentation says so explicitly
(`https://www.sec.gov/os/accessing-edgar-data` [PRIMARY DATA DOC] [read in full]):

> "The first set of numbers (0001193125) is the CIK of the entity submitting the filing. **This
> could be the company or a third-party filer agent.**"

**This is a plausible, silent, survivorship-shaped bug for any text puller** (the programme's puller
already has two unrepaired bugs): it would lose exactly those issuers who use a filer agent, 404 at
a rate that looks like "old filings aren't there", and never raise.

---

## 2. WHAT HAS BEEN PUBLISHED USING FILING TEXT — biased toward the negative

### 2.1 The strand map, and what each actually claims

**Readability.** Li (2008) introduced the Fog index on 10-Ks. **Loughran & McDonald, "Measuring
Readability in Financial Disclosures", Journal of Finance 69(4), 2014** [PEER-REVIEWED]
[abstract only] demolish it: the Fog index is "poorly specified in financial applications", one of
its two components misspecified and the other hard to measure, because it scores finance vocabulary
("liability", "amortization") as complexity. Their replacement is **10-K file size**. **The strand's
own leading authors say the measure that generated the literature does not measure what it claims.**

**Sentiment / lexicons.** Loughran & McDonald (2011) is the foundational finance lexicon, motivated
by a documented error rate on the prior standard: roughly three-quarters of words the Harvard-IV
psychosocial dictionary marks negative are **not** negative in a filing context. I did **not** open
the 2011 paper, so I carry that figure as **[abstract only / secondary]** and will not put a number
on it beyond "roughly three-quarters". It is nonetheless the right shape of evidence: **an
off-the-shelf lexicon applied to filings has a large, published, domain-specific misclassification
rate.** Loughran & McDonald's 2016 *Journal of Accounting Research* survey and their later
"Textual Analysis in Finance" are the authoritative reviews [PEER-REVIEWED] [abstract only].

**Year-over-year similarity — the strongest return claim, and the one that does not fit here.**
Cohen, Malloy & Nguyen, "Lazy Prices", NBER w25084 / *Journal of Finance* 75(3) 1371–1415 (2020)
[PEER-REVIEWED] [read in relevant part, local PDF extraction]. Verbatim from the paper:

- Sample **1995–2014**. Headline L/S (non-changers minus changers) **"34-58 basis points per month
  — up to 7% per year (t=3.59) in value-weighted abnormal returns"**. The famous **188 bp/month
  (t=2.76)** is the **Risk Factors section** subsample, not the main result.
- On costs, the paper **argues** rather than nets: "this does not appear to be a function of
  transaction costs or limits to arbitrage… the portfolios have very modest turnover… the average
  'changer' firm (to be shorted) is actually larger than the average long at $3.5B market cap (vs
  $2.5B)". **There is no cost-netted return anywhere in it.**
- `grep` for `subperiod|sub-period|second half` across all 67 pages: **no match.** The only
  subperiod reported is post-SOX **2003–2014**.

**So for this programme, specifically:** the sample **ends in 2014** (5 of the programme's 16½
years); the edge is **short-side-concentrated** by construction ("shorts changers") and shorting is
excluded ground here; it needs the **whole 10-K/10-Q text**, i.e. the expensive route not the cheap
one; it is **value-weighted** where this programme is equal-weighted; and no post-2010 subperiod and
no net-of-cost number exist in the paper. Kent Daniel's conference discussion
[WORKING PAPER / slides] [read in relevant part] is constructive rather than damning — his main
asks are for a quarter-over-quarter variant and for the negative returns to show up around earnings
announcements, untested in the paper.

**Specific-item / event extraction.** §3 — that is the crux and gets its own section.

### 2.2 Does any of it survive post-2010 under cost-honest treatment? I could not find a study that asks

**This is the honest negative and I want it stated plainly rather than dressed up.** I searched for
a study that tests filing-text return signals in a post-2010 subsample net of realistic costs. **I
did not find one.** What exists is the general cost-honest frame, which is not text-specific:

**Chen & Velikov, "Zeroing In on the Expected Returns of Anomalies"** (*JFQA*; SSRN 3624932)
[PEER-REVIEWED] [abstract only — I did not open the paper]: 204 anomalies, net of effective
bid-ask spreads and post-publication decay, **the average anomaly's expected return is ~4 bp/month**,
the strongest net **~10 bp at best** after controlling for data mining, and the split is **at
end-2005** for the algorithmic-trading era. McLean & Pontiff (2016) [PEER-REVIEWED]
[snippet only] find returns decline ~26% from in-sample to the post-sample/pre-publication window —
which is **not** a post-2010 test.

**Therefore: "filing-text signals survive post-2010 net of cost" is not a result that exists in
either direction.** It is an evidential gap. Given the previous campaign's own finding that the
gross edge is gone post-2005 at **7 bp/month, t=0.45** in the top 90% of market cap, **the prior
should be that text signals decay like everything else, and the absence of a text-specific test is
not reassurance.**

### 2.3 Corpus resources, and why they do not serve this lane

**EDGAR-CORPUS** (Loukas et al., arXiv 2109.14394) [PEER-REVIEWED, EMNLP-W] [read in relevant part]:
**10-K only, 1993–2020, 6.5B tokens, 38,009 companies**, item-split JSON, with `edgar-crawler`
open-sourced. It is the largest free filing-text corpus and it is **the wrong form and the wrong
window**: no 8-Ks, and it stops in 2020.

**A source I am explicitly discounting, and naming, because the campaign rules earned that rule.**
`arXiv:2101.04480` "Text Analysis in Financial Disclosures" surfaced high in search as a survey.
On local extraction its title page reads: single author, **`sravula@my.harrisburgu.edu`** —
a student address at Harrisburg University, an **unrefereed preprint**. [UNVERIFIED] [read in part].
**I took no number from it.** This is the same pattern as the previous campaign's
"invented percentages attributed to a named PDF that turned out to be an undergraduate thesis";
the defence is opening the first page, which costs nothing.

---

## 3. THE EXTRACTION PROBLEM — THE CRUX

### 3.1 The one paper that does exactly this lane's task, and its one missing number

**Dolphin, Dursun, Blankenship, Adams & Pike, "Grounded Event Extraction from SEC 8-K Filings with
a Fine-Grained Taxonomy", arXiv:2607.08346v1 [cs.CL], 9 Jul 2026.**
[WORKING PAPER — **and partly a SALES INSTRUMENT**: corresponding author `rian@massive.com`, with
the data behind `massive.com/docs/rest/stocks/filings/8-k-disclosures`] [**read in full**, local
pypdf extraction]. Every figure below is verbatim from the extracted text.

It states this lane's premise better than the lane does:

> "None of this information is recoverable from item codes, under which a clinical trial readout and
> a dividend declaration are both, typically, Item 8.01 filings."

**What it did.** Two stages: (1) schema-constrained tagging against a three-tier taxonomy of **119
event types**, every tag anchored to a **verbatim quote validated by fuzzy n-gram match** against
the filing; (2) a **separate** pass that re-reads only the cited quote against the category
definition and assigns a 1–5 quality score. Applied to **292,984 Form 8-K filings by 9,669 filers,
January 2022 – June 2026**, yielding 608,346 records of which 7,258 are explicit no-match, leaving
**601,088 validated tags over 286,968 filings (mean 2.1 per filing)**. Score distribution: 34% at 5,
21% at 4, **45% at scores 1–3**.

**The documented error rate, which is what the bar asks for.** Judged by a stronger LLM over
**5,125 tags stratified across all 119 types and all five scores**:

| Filter | Tags retained | Precision | Tags whose claimed event is absent from the filing |
|---|---|---|---|
| score 1 | — | **12%** | **8%** |
| score ≥ 4 | **55%** | **93%** | **0.2%** (0.1% at ≥4 per the abstract) |
| score = 5 | **34%** | **96%** | none observed in sample |

They also show the score only works as a dial **because it is assigned in a dedicated second pass**:
an inline self-rating "places roughly three quarters of all tags at the top score", i.e. it
collapses to a binary flag. That is a genuinely useful methodological finding and it generalises.

**THE MISSING NUMBER. `grep -i recall` over all 9 pages: NO MATCH. `grep -i "false negative"`: NO
MATCH.** The paper measures precision at several operating points and **never measures recall.**
The evaluation sample is stratified over *tags the system emitted*, so by construction it cannot see
a declaration the system failed to tag. **For a share statistic — "what fraction of dividend
initiations arrive inside an earnings release" — recall is the quantity that controls the bias, and
it is absent.** §3.6.

**Other limits, in the authors' own words and to their credit stated:**

> "Quote grounding prevents fabricated evidence but not fabricated inference, and the second-stage
> grader sees only the cited quote, so it cannot catch a quote that reads correctly in isolation
> while the surrounding filing contradicts it; this residual is small at high confidence … but
> cannot be assumed to be zero."

- **Corpus begins 2022.** Covers **4½ of this programme's 16½ years**. Nothing is published at this
  quality for 2010–2021.
- **Filings whose parsed text exceeds ~150,000 characters are excluded** — "almost always large
  exhibit attachments". A coverage hole, and not a random one.
- Evaluation is **LLM-as-judge, not human gold**. The paper itself cites self-preference bias in
  LLM judges as a known failure surface; it uses a different, stronger judge, which mitigates but
  does not eliminate.
- Item codes were read **from the filing text** by matching the 32 legal codes as line headers,
  recovering items for **99.8%** of filings. (**Cheaper and more reliable: the SGML header's
  `<ITEMS>` tag, §4.3, which 200s for 51/51 filings I tested across 2010–2026.**)
- The economic evaluation "**makes no return-prediction claims**." Its result is that fine-grained
  tags add **1.3 percentage points** of explained variance in *reaction magnitude* over item codes
  (vs 0.4 pp the other way). **1.3 pp of R² in |reaction| is not a signal and the authors do not
  present it as one.**

### 3.2 ExtractBench — the strongest negative, on a harder task than this lane's

**Ferguson et al., "ExtractBench", arXiv:2602.12247v2 [cs.LG], 13 Feb 2026.**
[WORKING PAPER — vendor-authored, Contextual AI, `github.com/ContextualAI/extract-bench`]
[**read in full**, local pypdf extraction]. Verbatim figures:

- 35 documents, 2,076 pages, 12,867 evaluatable fields, **67.9 hours of expert annotation** (of
  which **56 hours on the SEC 10-K/Qs alone**). SEC domain: **7 documents, 422 pages, 9,071 gold
  values, a 369-field schema.**
- Across **210 extraction attempts** by six frontier models: **51% valid JSON (107/210)**,
  **aggregate pass rate 4.6% (844/18,516 field evaluations)**. Best model **6.9%**.
- **"The headline finding is the complete failure on SEC 10-K/Q filings: no model produced valid
  output for any of the seven documents."** That one domain is 84% of all field evaluations.
- **Excluding 10-K/Q, pass rate 28.0% (844/3,018).**
- **"when models produce valid JSON, field-level accuracy ranges from 65% to 80%, with an aggregate
  of 72.9%"** — and the authors flag it themselves as a **biased sample** (only the attempts that
  succeeded).

**How much of this transfers, stated honestly.** The 0%-valid headline is driven by **schema
breadth (369 fields) and output length**, not by the difficulty of finding a dividend declaration.
Extracting one dated fact from one 8-K is a far easier task and the 0% figure should **not** be
quoted as if it applied. **What does transfer is the 72.9% aggregate field-level accuracy on valid
outputs** — because that is a per-field number, and it sits in the same band as the 66.7% NER
precision (§3.4), the 78.0 F1 XBRL-tagging ceiling (§3.3), and the programme's own 67% phrase-match
precision. **Four independent measurements of "extract a typed fact from filing prose" land between
67% and 78%.** That convergence is the most useful thing in this section.

Note also: **"Credit agreements span 100–250 pages, exposing Claude's 100-page PDF limit while other
models achieve 85%+ accuracy."** Credit agreements are the document class that produced this
programme's own reported false positive.

### 3.3 The peer-reviewed ceiling for typed numeric facts in filing prose: 78.0 F1

**Loukas, Fergadiotis, Chalkidis, Spyropoulou, Malakasiotis, Androutsopoulos & Paliouras, "FiNER:
Financial Numeric Entity Recognition for XBRL Tagging", ACL 2022, arXiv:2203.06482**
[PEER-REVIEWED] [**read in relevant part**, local pypdf extraction].

- Dataset **FiNER-139: 1.1M sentences with gold XBRL tags**, from 10-K/10-Q filings **2016–2020**,
  **annotated by professional auditors**, 139 entity types (of 6,008 in us-gaap), ≥1,000 appearances
  each. **91.2% of gold spans are numeric expressions.**
- **Table 3, entity-level micro-F1 / macro-F1 (avg of 3 seeds), verbatim:** spaCy 48.6 / 37.6;
  BiLSTM (words) 77.3 / 73.8; BiLSTM (subwords) 71.3 / 68.6; BERT (subwords) 75.1 / 72.6;
  BiLSTM(words)+CRF 69.4 / 67.3; BiLSTM(subwords)+CRF 76.2 / 73.4; **BERT(subwords)+CRF 78.0 / 75.2
  — the best.**

**Read this as the ceiling, because the conditions are close to ideal and better than anything this
programme could arrange:** auditor-grade gold labels, 1.1M training sentences, exact-span scoring,
a fixed and finite label set, and the facts already marked up by the filer. **The best result is a
22% entity-level error rate.** An off-the-shelf general NER tool (spaCy) gets **48.6** — a 51% error
rate. **"Use a standard NER library" is not a route.**

### 3.4 In-domain NER on SEC filings: 66.7% precision, 34.3% sentence error

**Zheng, Li, Yao & Long, "Reliable Financial Named Entity Recognition under Domain Shift:
Confidence Estimation and Selective Prediction", arXiv:2608.19558** (Washington University in St.
Louis; Southern Methodist University) [WORKING PAPER] [**read in relevant part**, local pypdf
extraction]. Table II, verbatim, trained and tested **in-domain on the FIN corpus of SEC filings**:

| Model | Domain | P | R | F1 | Halluc.% | ECE |
|---|---|---|---|---|---|---|
| BERT-base | **FIN (SEC filings)** | **66.7 ± 2.3** | **74.2 ± 1.4** | **70.3 ± 1.5** | – | 0.102 |
| BERT-base | FiNER-ORD (financial news) | 39.1 | 37.6 | **38.3** | – | 0.071 |
| BERT-base | TweetNER7 (social) | 35.2 | 18.4 | **24.1** | – | 0.074 |
| Qwen2.5-0.5B+LoRA | FIN | 40.5 | 34.7 | 37.4 | 3.6 | 0.362 |
| Qwen2.5-1.5B+LoRA | FIN | 47.7 | 44.7 | 46.2 | 4.3 | 0.322 |

And the abstention result, verbatim: abstention "reduces sentence error from **34.3% to below 2% on
the highest-confidence 40% of in-domain inputs** and remains useful on financial news, but recovers
no usefully large clean subset under the extreme social-media shift."

**Three things this gives the lane.**
1. **A published in-domain precision on SEC filing text of 66.7%.** The programme's own measured
   phrase-match precision was ~67%. **The programme's number is not a sign of a sloppy
   implementation; it is the literature's own number for this task.** (Exactly the shape of the
   previous campaign's finding about 33.8 bp/side.)
2. **A baseline sentence-level error rate of 34.3% in-domain**, and a documented way to trade it
   down: **abstain on the low-confidence 60% and error falls below 2%.** That is the same
   precision/coverage dial the 8-K paper found (96% at 34% retained). **Two independent papers, two
   tasks, the same conclusion: usable precision is purchased with roughly two-thirds of the
   population.**
3. **A fine-tuned generative model at 1.5B is WORSE in-domain than BERT-base** (46.2 vs 70.3 F1)
   with 3.6–4.3% hallucination and 1.4–5.4% invalid JSON. Model size is not the lever; in-domain
   training data is.

### 3.5 What I measured myself about the false positives

**14 of 14 randomly drawn "dividend"-mentioning 8-K documents that my declaration-phrase family did
NOT match contained no common-stock dividend declaration.** Jan-2021, `forms=8-K`, seed 7, documents
fetched and the ±180-character window around each `dividend` occurrence printed and read
[MEASURED IN BRIEF, `A4_recall.py`]. The classes, with the actual language:

| Class | n | Example text |
|---|---|---|
| Securities-purchase-agreement representation | 4 | "the Company has not declared or made any dividend or distribution of cash or other property to its stockholders" |
| **Credit agreement / indenture DEFINED TERM** | 2 | "'Distributions' shall mean … dividends on, or other payments or distributions on account of …" |
| By-laws / certificate of incorporation record-date clause | 2 | "the date for the payment of any dividend … as the record date" |
| Earnings-release non-GAAP definition or balance-sheet line | 3 | "Free cash flow after dividends is defined as …"; "Dividend payable 24,242" |
| Risk-factor / forward-looking boilerplate | 1 | "our dividend is dependent on a number of factors" |
| Convertible-note clause | 1 | "any note(s) issued … as a dividend thereon" |
| Royalty-trust distribution tax note | 1 | "EXPECTED TO BE FREE OF DIVIDEND INCOME TAXES" |

**The prior lane's reported false positive — "a credit-agreement defined term rather than an event"
— is not an anecdote. It is the second-largest class in a blind draw of 14.** Two of 14 are exactly
it, and four more are the same mechanism in a different contract (SPA representations). **Contract
exhibits attached to 8-Ks are the dominant noise source, and they are long**, so a pipeline that
reads whole submissions pays for them twice: in bytes and in false positives.

**Also measured: the bare word is useless as a screen.** Jan-2021 `forms=8-K`: `dividend` matched
2,456 documents → **1,440 distinct filings**; the 8-phrase declaration family matched 493 documents
→ 337 filings, of which 329 were inside the mention set. **So 1,111 filings mention "dividend" and
do not match a declaration phrase, and my blind draw of 14 of them found 0 declarations.**

### 3.6 THE BIAS ARGUMENT, WHICH IS THE LANE'S REAL FINDING

Round 5's statistic is a **share**: of dividend/split announcements, what fraction arrive inside an
earnings release. Write it as A = D∩E / D, where D is the set of announcements and E the subset
inside an earnings release (Item 2.02 / an EX-99 earnings press release).

A phrase-matching or model-based extractor gives you D̂, not D. **The measured share Â is unbiased
only if the extractor's recall is the same inside and outside earnings releases.** There is a
concrete reason to expect it is not:

- A standalone dividend release is short, titled, and built around the declaration sentence. The
  declaration phrase is in the first paragraph and usually in the document title.
- A declaration absorbed into a quarterly earnings release sits in paragraph 14 of a nine-page
  document, often inside a table, often phrased as "also announced" or "the Board approved", often
  in a "Capital Return" subheading, and competing with the non-GAAP-definition and
  dividend-payable-balance-sheet language I found in §3.5.
- It is also **more likely to exceed the 150,000-character cut the 8-K paper applies**, and more
  likely to be the filing where the matched document is the earnings exhibit rather than the body.

**Direction:** recall is plausibly *lower* inside earnings releases, so **Â understates A** — the
absorption problem is probably *worse* than a text-matched census would say, which is the direction
that matters for a programme that must exclude earnings dates. **Magnitude: unknown, and not
bounded by anything I found published.**

**This is why a precision number does not discharge the lane's bar on its own.** The only thing that
fixes it is a **gold standard stratified on the thing suspected of driving the bias** — hand-label
a few hundred 8-Ks drawn separately from Item-2.02 filings and from non-2.02 filings, and measure
recall **within each stratum**. That is a small job and it is the job.

### 3.7 THE ROUTE RUN END TO END — and it reproduces round 5's number from a different layer

I ran the full Route C join on one month to prove the mechanism works, not to produce a headline
[MEASURED IN BRIEF, `A4_absorption_demo.py`]. Jan-2021, `forms=8-K`, the 8-phrase declaration family,
then `.hdr.sgml` for every resulting filing:

- **493 matched documents → 337 distinct filings.** Of the 493, **489 were `8-K` and 4 were `8-K/A`**
  — §1.3's warning, showing up in live data.
- **`.hdr.sgml` retrieved 337/337. Zero failures.** The metadata leg of Route C is not flaky.
- Item incidence across the 337 filings: `9.01` 323 (95.8%), **`2.02` 203 (60.2%)**, `8.01` 151
  (44.8%), `7.01` 109 (32.3%), then a thin tail (`1.01` 10, `5.02` 9, `5.03` 9, `3.02` 4, …).
  **Exactly one filing had `9.01` as its only item.**
- The matched document was the 8-K body itself in 106 of 337; in the rest it was an exhibit.

**So: 60.2% of phrase-matched dividend declarations in Jan-2021 arrived in a filing that also
carries Item 2.02 — results of operations, i.e. an earnings release.** Round 5 measured **62.2% of
dividend initiations** absorbed into a quarterly earnings release. **Two measurement layers that
could not see each other — round 5's construction, and a phrase census joined to SGML headers —
land 2 points apart.**

**Four caveats, and they matter more than the agreement does.**
1. **One month, and the worst month to pick.** January is a heavy Q4-reporting month, so Item-2.02
   incidence is **seasonally high**. 60.2% is an upper-ish estimate for a full year and must not be
   quoted as an annual figure. A 17-year, 204-month version is 219 FTS requests away (§5) and is the
   thing to run.
2. **Declarations, not initiations.** Round 5's 62.2% is about *initiations*, a rarer and different
   population. The agreement is suggestive, not a replication.
3. **The phrase family's recall is still unmeasured**, so §3.6's bias applies to this 60.2% exactly
   as it applies to anything else built this way — and in the direction that makes the true share
   *higher*.
4. **Item 2.02 present ≠ the declaration was inside the earnings text.** A filing can carry 2.02 and
   8.01 with the dividend in a separate EX-99.2. 44.8% here carry 8.01 as well. Separating
   "co-filed with" from "absorbed into" needs the document-level join, not the filing-level one.

**What this establishes for the lane, narrowly and defensibly: the measurement layer round 6 could
not reach IS reachable, the join runs at 337/337, and on the one month tested it agrees with round
5 rather than contradicting it.** What it does not establish is the share itself.

---

## 4. THE LOOK-AHEAD PROBLEM IN TEXT

### 4.1 The single most important primary-source sentence, and it is about point-in-time

`https://www.sec.gov/os/accessing-edgar-data`, section "Post-acceptance corrections and deletions"
[PRIMARY DATA DOC] [read in full], verbatim:

> "Filings are sometimes authorized by SEC staff for removal or correction … Corrections processed
> during a given business day will be incorporated in the indexes built that evening. **However,
> removals processed on subsequent business days will not be reflected in any previous daily, feed,
> or oldload index. The full and quarterly index files are rebuilt weekly, early on Saturday
> mornings, so that any post-acceptance correction (PAC) deletes or updates are incorporated.**"

**Read what that says. The quarterly `full-index` is NOT point-in-time — it is rebuilt weekly with
retroactive deletions applied. The daily index and the Feed tarballs ARE point-in-time, and are the
only products that preserve what was actually visible on the day.** Confirmed by the file metadata:
every `full-index/*/master.idx` I HEADed, from 2010Q1 to 2026Q1, carries
`Last-Modified: Sat, 05 Sep 2026` — **a 2010 quarterly index last rebuilt five days before I fetched
it.** The daily file `master.20210104.idx` carries `Last-Modified: Tue, 05 Jan 2021`.

**A text pipeline built on `full-index` therefore inherits a survivorship bias in the filing
population itself** — small, but in the same family as the programme's six confirmed
survivors-only-ticker-map findings, and with the same signature: it never raises.

### 4.2 Content date vs availability date

Same page, verbatim:

> "EDGAR accepts new filer applications, new filings, and changes to filer data each business day,
> Monday through Friday, from 6:00 a.m. to 10:00 p.m., ET. Indexes incorporating the current
> business day's filings are updated nightly starting about 10:00 p.m., ET … **Some filing
> submissions that begin after 5:30 p.m. ET — or 10:00 p.m. for Ownership forms 3, 4, 5 — will be
> disseminated the next business day, showing up in the following business day's index.**"

So for a filing accepted after 17:30 ET, **`filingDate` is day t and public availability is day
t+1.** For a daily-bar, overnight-edge book this is precisely the one-bar error that matters. The
programme's puller is reported to key on `filingDate`. **That is not merely imprecise; for the
after-17:30 population it is wrong by a bar in the look-ahead direction.**

A text pipeline must key on, in order of preference:
1. **`<ACCEPTANCE-DATETIME>` from the SGML header** (§4.3) — unlabelled, documented ET, no
   conversion to get wrong;
2. **the daily index file the filing first appears in** — the operational definition of "available";
3. **never** `filingDate`, and **never** the FTS `file_date` (which is the filing date and is the
   only date FTS gives you — **FTS alone cannot be made causal**).

### 4.3 `.hdr.sgml` is the authoritative header and it works for every era

[MEASURED IN BRIEF, `A4_final_probe.py`] — 3 real 8-Ks per year, 2010–2026, 51 filings, addressed by
**issuer** CIK:

| | 2010 | 2011 | 2012 | 2013 | 2014 | 2015 → 2026 |
|---|---|---|---|---|---|---|
| `<accession>.hdr.sgml` | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | **3/3 every year** |
| `<accession>-index-headers.html` | **0/3** | **0/3** | **0/3** | **0/3** | **1/3** | 3/3 every year |

**The carried finding "`-index-headers.html` returns 404 for every 2010-2013 filing" is confirmed
and EXTENDS INTO 2014** (1 of 3 in 2014 succeeded; the boundary is inside 2014, which I did not
narrow further). **`.hdr.sgml` is the fix and is available for the whole window.**

Size: **mean 921 B, median 897 B, max 1,166 B** over 51 filings. It contains everything a causal
8-K pipeline needs:

```
<ACCEPTANCE-DATETIME>20220128160229
<ACCESSION-NUMBER>0000883948-22-000010
<TYPE>8-K
<PERIOD>20220128
<ITEMS>8.01
<ITEMS>9.01
<FILING-DATE>20220128
<CIK>0000883948
```

**Item codes parsed from `<ITEMS>` for all 51 filings across all 17 years.** And note the asymmetry
I measured: **the complete-submission `.txt` header carries only the textual description
("ITEM INFORMATION: Other Events"), not the numeric code; `.hdr.sgml` carries the code.** For item
codes plus acceptance time at one request per filing, **`.hdr.sgml` at ~900 bytes is the object**,
not the 217 KB `.txt`.

### 4.4 The `acceptanceDateTime` timezone defect — my measurement CONFLICTS with the prior round's

18 filings (3 per era, 6 eras), `data.sec.gov/submissions/CIK##########.json` `filings.recent`
versus the `.hdr.sgml` `<ACCEPTANCE-DATETIME>` [MEASURED IN BRIEF, `A4_header_test.py`]:

- **7 of 18 accessions were NOT IN `filings.recent` at all** — a separate and independent defect,
  §4.5.
- Of the **11 comparable pairs, 10 were converted correctly** from Eastern to UTC (+5h under EST,
  +4h under EDT; e.g. hdr `2014-03-14T16:36:49` → json `2014-03-14T20:36:49.000Z`, and hdr
  `2025-01-31T16:01:46` → json `2025-01-31T21:01:46.000Z`).
- **1 of 11 carried the Eastern wall clock mislabelled `Z`**: accession `0000059255-10-000008`,
  hdr `2010-02-18T17:32:26`, json `2010-02-18T17:32:26.000Z`. **Identical wall clock, stamped UTC.**

**So: 1/11 = 9% here, against the prior round's 35/60 (58%) and 32/51 (63%). CONFLICT, RECORDED, NOT
ADJUDICATED.** Which I would weight and why: **the prior round's, on sample size and on breadth.**
n=11 is far too small to estimate a rate, and my 11 are a narrow and probably unrepresentative draw
— all 8-Ks, all containing a dividend phrase, 3 per era, concentrated in a handful of large filer
agents. **What my measurement does establish independently is that the defect is REAL and still
present** (one unambiguous instance), and that **the `.hdr.sgml` value is the unambiguous reference
against which the defect is visible at all** — which is the operational conclusion either way. **It
does not rehabilitate `acceptanceDateTime`, and nobody should read 9% as "mostly fine".**

### 4.5 `filings.recent` truncates — 7 of 18 accessions were missing

For issuers with long filing histories, older accessions are **not** in the base
`submissions/CIK##########.json`; they live in the additional shards named under `filings.files[]`.
**7 of 18 of my filings (39%) were absent from `filings.recent`** and would be silently dropped by a
puller that reads only that block. Given the programme's puller already has two unrepaired bugs,
this is a third thing to check rather than assume.

### 4.6 Amendments

- **8-K/A volume is small:** daily index 2021-01-04, **6 × 8-K/A against 241 × 8-K = 2.4%**; FTS
  `q=the` Jan-2024 returned **292** 8-K/A (against an 8-K count that hit the 10,000 ceiling).
  Zero-control `forms=ZZ-NOTAFORM` → **0** in the same pass [MEASURED IN BRIEF].
- **`forms=8-K` silently includes 8-K/A** (§1.3). An amendment filed months later carries a later
  acceptance timestamp but may restate a *prior* event; including it without filtering mixes a
  t+90 document into a t event set. **Filter on `_source.form`, and key the event on the original
  filing's acceptance time, not the amendment's.**
- **Post-acceptance deletions are a distinct and worse case than amendments** (§4.1): the filing is
  *removed*, with no amendment marker, and the retroactive rebuild of `full-index` hides that it
  ever existed.

---

## 5. THE FEASIBILITY ARITHMETIC

All inputs measured in this brief; working shown so it can be re-run and disputed.

**Measured unit costs.** Feed tarball: mean 1,041 MB/day over a 33-day sample. Complete-submission
`.txt` for an 8-K: **mean 216,743 B, median 221,280 B** (n=12). The single FTS-identified
**document** (usually the EX-99.1): **mean 13,547 B, median 6,625 B** (n=12). `.hdr.sgml`: **mean
921 B** (n=51). FTS result page: ~60 KB for 100 hits.

### Route A — the dissemination feed (every document of every filing)

- Requests: **~4,187**, one per trading day.
- Bytes: per-year mean × trading days, summed = **4.39 TB compressed**; largest single member 2.65 GB.
- Verdict: **not the route.** 4.4 TB to answer a question about ~18,000 filings is a 250,000× waste.
  It is also the only route that is *complete*, so it is the fallback if the targeted route's recall
  cannot be established — which is the actual decision point.

### Route B — one item code over 2010–2026, metadata only

The literal sub-question. Using the stated 1,185,352 8-K submissions in the window:

- **`.hdr.sgml` for every 8-K** (gives `<ITEMS>` *and* `<ACCEPTANCE-DATETIME>`):
  1,185,352 × 921 B = **1.09 GB**, **1,185,352 requests**.
  At 10 req/s = **32.9 h** of requests; at a sustainable 5 req/s = **65.9 h**.
- **Complete submission text for every 8-K**: 1,185,352 × 216,743 B = **0.26 TB**, same request count.
- Shortcut that removes almost all of it: `submissions.zip` is **1.56 GB in ONE request** and carries
  item codes per filing. Round 6 already censused all 1,185,352 at item granularity, so **this
  layer is already paid for.**

### Route C — the targeted route, and the one I would actually run

Phrase-family census over 2010–2026 (two dividend phrase families, per-year slices, zero-control 0
in all 17 years):

| Step | Count | Bytes | Requests |
|---|---|---|---|
| FTS year-sliced pages, 100 hits/page | 21,825 documents | ~13 MB | **219** |
| Dedupe to filings at the measured 0.844 ratio | ~18,420 filings | — | 0 |
| Fetch only the matched document (mean 13,547 B) | 21,825 | **0.30 GB** | **21,825** |
| `.hdr.sgml` for item codes + acceptance time | 18,420 | **17 MB** | **18,420** |
| **TOTAL** | | **~0.31 GB** | **~40,464** |

At 5 req/s: **2.25 hours.** At 10 req/s: 1.1 hours. **Three orders of magnitude inside the feed
route, and if round 6's item-code census is reusable the `.hdr.sgml` leg drops out and the whole
thing is 219 FTS requests plus 21,825 document fetches.**

**Measured per-year FTS counts, with the zero-control beside them** [`A4_census.json`]:

| Phrase | 2010 | 2015 | 2020 | 2025 | Σ 2010–2026 |
|---|---|---|---|---|---|
| `"declared a quarterly dividend"` | 480 | 670 | 599 | 663 | **10,597** |
| `"declared a cash dividend"` | 488 | 691 | 657 | 758 | **11,228** |
| `"board of directors declared"` | 1,476 | 2,396 | 2,169 | 2,346 | **36,772** |
| `"stock split"` | 5,813 | 5,762 | — | — | **106,683** |
| `"two-for-one stock split"` | — | — | 47 | 23 | **1,325** |
| **`"zzqxvnqq impossible control phrase"`** | **0** | **0** | **0** | **0** | **0 (all 17 years)** |

Every year-slice returned `relation: "eq"` — none hit the 10,000 ceiling, so the per-year slicing is
the right granularity and the counts are exact rather than truncated.

**One arithmetic sanity note, flagged as NOT a measurement:** the 8-phrase declaration family found
**337 filings in Jan-2021**, which is the right order for a month of US quarterly declarations. I
did **not** verify it against a dividend-payer universe and it is not evidence of recall.

**`"two-for-one stock split"` falls from 90 (2016) to 12 (2026)** — consistent with splits having
become rare, but also with ratio wording drifting ("2-for-1", "1:2", "2:1"). **Phrase families decay
as language drifts, and the decay looks like a real-world trend.** Any multi-year phrase census needs
its vocabulary re-validated per era or it manufactures a time trend.

---

## 6. LICENSING AND TERMS

[PRIMARY DATA DOC] [read in full]: `https://www.sec.gov/os/accessing-edgar-data`,
`https://www.sec.gov/about/privacy-information` (Internet Security Policy section),
`https://www.sec.gov/developer`, `https://www.sec.gov/robots.txt`.

**What is permitted.** "Anyone can access and download this information for free." Scripted access
is explicitly contemplated: "We allow scripted access to sec.gov content and have some resources for
developers", with "We do not offer technical support for developing or debugging scripted
processes."

**The hard constraints, verbatim.**

> "Current guidelines limit users to a total of no more than **10 requests per second, regardless of
> the number of machines used to submit requests.** If a user or application submits more than 10
> requests per second, further requests from the IP address(es) may be limited for a brief period.
> **Once the rate of requests has dropped below the threshold for 10 minutes, the user may resume**
> accessing content on SEC.gov."

> "The SEC does **not allow 'unclassified' bots or automated tools to crawl the site.** Any request
> that has been identified as part of an unclassified bot or an automated tool outside of the
> acceptable policy will be managed to ensure fair access for all users."

> "Please declare your user agent in request headers: `Sample Company Name
> AdminContact@<sample company domain>.com`" with `Accept-Encoding: gzip, deflate`.

**So: the declared, contactable User-Agent is what makes you "classified". An undeclared scraper is
outside policy regardless of rate.** Note also the 10-minute cool-down: a rate breach is not
instantly forgiven, which matters for a 40,000-request run.

**`robots.txt` does NOT restrict the data.** It is a stock Drupal file: it disallows `/core/`,
`/profiles/`, `/admin/`, `/search/`, `/search?`, `/user/register`, and various READMEs. **It does not
mention `/Archives/`, `/cgi-bin/`, or `/files/`.** `efts.sec.gov` serves no robots.txt at all (403,
23-byte JSON).

**Redistribution, stated as the uncertainty it is.** I found **no SEC statement granting or
restricting redistribution of filing text**, and I want to be precise about why that is not the same
as permission. The SEC's own *works* are US government works and not copyrightable (17 USC 105), but
**the filings are authored by registrants, not by the SEC**, and the SEC's pages do not purport to
license them. What I did find is unrelated: SEC **trademark** licensing, handled at
`EDGARTrademark@sec.gov`. There is also a **fee-based EDGAR Public Dissemination Service (PDS)** for
real-time dissemination, which is contractual and which I did not examine — the free `/Archives/`
copy is the dissemination-lagged equivalent.

**Practical position.** Bulk retrieval for internal research, paced and declared, is squarely
permitted. **Republishing harvested filing text as a dataset is a question I did not resolve and
would not assume** — note that the two vendor-authored papers in §3 both *release* derived tags and
cleaned text, which is evidence of practice, not of law.

**Things a researcher must not do, from the above:** exceed 10 req/s in aggregate across machines;
run undeclared automated tools; assume a 403/429 clears instantly.

---

## 7. WHAT WOULD HAVE TO BE TRUE FOR THIS LANE TO CHANGE ANYTHING

Stated as falsifiable conditions rather than a recommendation, because this lane closes nothing.

1. **Recall of the extraction step, measured within strata.** Hand-label a stratified sample of
   8-Ks — drawn separately from Item-2.02 filings and non-2.02 filings, because §3.6 says the bias
   lives in exactly that contrast — and report recall **per stratum** with a confidence interval.
   Until then round 5's absorption share has an unbounded bias of known sign.
2. **A phrase vocabulary validated per era,** not once. `"two-for-one stock split"` fell 90 → 12
   across the window; some of that is real and some is wording drift, and nothing here separates them.
3. **The pipeline keyed on `<ACCEPTANCE-DATETIME>` from `.hdr.sgml`**, with the daily index as the
   availability check, `full-index` used for nothing point-in-time, `_source.form` filtered for
   amendments, and the issuer CIK (never the accession prefix) in every path.
4. **A measured negative control on every harvest**, per campaign rule — and now specifically a
   *parameter* control, because §1.3 shows an unrecognised or misspelt parameter returns a larger,
   plausible, wrong answer at HTTP 200 with no error.

**And the thing worth saying out loud: every figure in §3 is a measurement of DISCLOSURE BEHAVIOUR,
not of return predictability.** The one paper that ran an event study on 182,174 events
explicitly "makes no return-prediction claims" and its economic result is **1.3 percentage points**
of explained variance in reaction *magnitude*. **Nothing in this lane is evidence that a text-derived
event set predicts returns.** It is evidence about whether the measurement layer can be built.

---

## 8. SOURCE LEDGER

| Source | Type | Established |
|---|---|---|
| `efts.sec.gov/LATEST/search-index` — 60+ parameterised queries, §1.3/1.4/1.6/5 | PRIMARY DATA DOC | **[MEASURED IN BRIEF]** |
| `sec.gov/edgar/search/efts-faq.html` | PRIMARY DATA DOC | [read in full], local de-tag |
| `sec.gov/os/accessing-edgar-data` | PRIMARY DATA DOC | [read in full], local de-tag |
| `sec.gov/about/privacy-information`, `sec.gov/developer`, `sec.gov/robots.txt` | PRIMARY DATA DOC | [read in full] |
| `/Archives/edgar/{full-index,daily-index,Feed}`, `submissions.zip`, `.hdr.sgml`, `-index-headers.html`, `index.json` — 250+ HEAD/GET | PRIMARY DATA DOC | **[MEASURED IN BRIEF]** |
| `data.sec.gov/submissions/CIK*.json` — 18 acceptance-time comparisons | PRIMARY DATA DOC | **[MEASURED IN BRIEF]** |
| End-to-end Route C join, Jan-2021: 337 filings, 337 `.hdr.sgml`, §3.7 | PRIMARY DATA DOC | **[MEASURED IN BRIEF]** |
| Blind read of 14 phrase-family misses, §3.5 | PRIMARY DATA DOC | **[MEASURED IN BRIEF]** |
| Dolphin et al., *Grounded Event Extraction from SEC 8-K Filings*, arXiv:2607.08346v1 | WORKING PAPER + **SALES INSTRUMENT** (massive.com) | **[read in full]**, local pypdf |
| Ferguson et al., *ExtractBench*, arXiv:2602.12247v2 | WORKING PAPER (vendor: Contextual AI) | **[read in full]**, local pypdf |
| Loukas et al., *FiNER*, ACL 2022, arXiv:2203.06482 | PEER-REVIEWED | [read in relevant part], local pypdf |
| Zheng et al., *Reliable Financial NER under Domain Shift*, arXiv:2608.19558 | WORKING PAPER | [read in relevant part], local pypdf |
| Cohen, Malloy & Nguyen, *Lazy Prices*, NBER w25084 / JF 75(3) | PEER-REVIEWED | [read in relevant part], local pypdf |
| Loukas et al., *EDGAR-CORPUS*, arXiv:2109.14394 | PEER-REVIEWED (workshop) | [read in relevant part], local pypdf |
| Daniel, discussion of *Lazy Prices* (slides) | WORKING PAPER | [read in relevant part], local pypdf |
| Loughran & McDonald, *Measuring Readability in Financial Disclosures*, JF 69(4) 2014 | PEER-REVIEWED | **[abstract only]** |
| Loughran & McDonald, *Textual Analysis in Accounting and Finance: A Survey*, JAR 2016 | PEER-REVIEWED | **[abstract only]** |
| Loughran & McDonald (2011) Harvard-IV misclassification "~three-quarters" | PEER-REVIEWED | **[snippet only — NOT OPENED]** |
| Chen & Velikov, *Zeroing In on the Expected Returns of Anomalies* | PEER-REVIEWED | **[abstract only — NOT OPENED]** |
| McLean & Pontiff (2016) 26% decline | PEER-REVIEWED | **[snippet only]** |
| Ravula, *Text Analysis in Financial Disclosures*, arXiv:2101.04480 | **[UNVERIFIED]** unrefereed student preprint | [read title page] — **no number taken** |

**Blocks, logged by tool and response, never by host.**
- `urllib` GET `efts.sec.gov/LATEST/search-index` → **HTTP 500, 36-byte body**, 3 of 22 requests at
  0.35 s pacing; all 3 succeeded on retry at 0.40 s. Transient, not a block.
- `curl` GET `https://efts.sec.gov/robots.txt` → **HTTP 403, 23 bytes, `{"message":"Forbidden"}`**.
- `urllib` HEAD `/Archives/edgar/Oldloads/20210104.nc.tar.gz` → **HTTP 403**.
- `urllib` GET `/cgi-bin/srqsb?text=test` → **HTTP 503**.
- `urllib` GET `/Archives/edgar/data/<filer-agent-CIK>/<accn>/...` → **HTTP 404, 291–305-byte gzipped
  S3 `<Error><Code>NoSuchKey</Code>`**. My path error, not a block; §1.7.
- `urllib` GET `sec.gov/about/sec-website-policies` and `sec.gov/about/website-policies` → **HTTP 404
  with a 53,435-byte HTML body**. A 404 serving a full page shell — the flavour already on the
  programme's list, seen again.
- **No tool was blocked. No 429 was earned.** Total volume across the lane was roughly 800 requests
  at 0.35–0.50 s, single-threaded.

---

## 9. WHAT I COULD NOT VERIFY, STATED PLAINLY

1. **Recall of any extraction method on dated corporate facts in filing prose — by anyone, including
   me.** The one paper that tags 8-K events at corpus scale does not contain the word "recall".
   I measured precision-adjacent quantities and the false-positive taxonomy; **I did not build a
   gold standard and I did not measure recall.** This is the lane's central unverified quantity and
   everything in §3.6 depends on it.
2. **Whether the extractor's recall differs inside versus outside earnings releases.** §3.6 is an
   argument from document structure, not a measurement. The sign is argued; the magnitude is unknown.
3. **Whether the 60.2% Item-2.02 incidence in §3.7 holds outside January.** It is **one month**, and
   January is seasonally the worst case (heavy Q4 reporting). I ran no other month. The 17-year
   version costs 219 FTS requests plus ~18,420 header fetches and I did not run it. **Do not quote
   60.2% as an annual figure.**
   Related and separate: §3.7 measures *Item 2.02 present on the same filing*, which is **not** the
   same as *the declaration appearing inside the earnings text*. I did not do the document-level
   split that would separate those, and 44.8% of the same filings also carry Item 8.01.
4. **The true `acceptanceDateTime` mislabelling rate.** My 1/11 (9%) conflicts with the prior round's
   58% and 63% and my n is far too small to settle it. I weight the prior round's. The defect's
   existence is confirmed; its frequency is not established by me.
5. **Where inside 2014 the `-index-headers.html` boundary falls.** 0/3 in 2010–2013, 1/3 in 2014,
   3/3 from 2015. I did not narrow it within 2014.
6. **Whether EDGAR FTS indexes PDF-only and image-only exhibits.** All 100 documents in my sample
   were `.htm`. Neither confirmed nor refuted, and it matters for recall on older filings.
7. **Whether `forms=` accepts a comma-separated list, and whether a partly-invalid list is silently
   dropped.** Not tested. Given §1.3, assume the worst until measured.
8. **The exact `from` ceiling.** `from=40` works; `from=9990` and `from=10000` return HTTP 200 with
   `hits.total` **absent** and a 1,132-byte body I did not parse. The practical ceiling is the
   10,000-hit window; the precise maximum `from` is untested.
9. **Redistribution rights over harvested filing text.** No SEC statement found either way. The
   fee-based PDS terms were not examined. Do not treat "I found no prohibition" as permission.
10. **Loughran & McDonald (2011)'s "roughly three-quarters" Harvard-IV misclassification figure.** I
    did not open that paper. It is the single number in this brief I am carrying from a summariser,
    it is flagged as such in §2.1 and §8, and **nothing here rests on it.**
11. **Chen & Velikov's 4 bp/month and the end-2005 split.** [abstract only]. I did not open the
    paper and no conclusion here depends on the exact figure.
12. **Any claim that a text-derived signal earns a return, post-2010 or otherwise.** I found **no**
    study testing filing-text signals in a post-2010 subsample net of realistic costs. **That is an
    evidential gap, not a negative result, and it is certainly not a positive one.**
13. **The correct `Oldloads` filename pattern** (403 on my guess), and therefore whether Oldloads
    offers a point-in-time alternative to the Feed.
14. **Whether round 6's item-code census is reusable for the join in Route C.** I have no access to
    it; the arithmetic in §5 is given both with and without that leg.
