# J5 — Point-in-time panel construction: what is actually stated, and where

External evidence only. **I have no access to this programme's fixture, loader or code and
claim nothing about any of them.** Every statement below is about a published paper, a
vendor manual, or a public reference implementation. The question that created this lane
(*does the fixture preserve an entirely missing session or forward-fill it?*) is a question
about this programme's data and **this brief cannot answer it** — it can only say what the
outside world does and what each choice is documented to cost.

**No return magnitude is reported in this brief**, so the round-5 killer screen ("where does
the effect live") has nothing to bite on. One observation in that direction belongs up
front anyway: **every convention in this lane binds hardest in the cheap, thin tail** — the
triggers are zero-volume days, bid/ask-average prints instead of closes, and vendor
stale-price flags, all of which concentrate in low-priced illiquid names. A panel
convention is not price-neutral even though it is return-silent.

---

## HEADLINE — three findings, in order of how much they should change what the programme does

**1. THE BAR IS CLEARED, AND BY THE VENDOR FIRST. CRSP STATES IN ONE SENTENCE THAT IT DOES
NOT FORWARD-FILL.**

> "There is no price data from one trading day applied to the next trading day."
> — CRSP, *Stock and Index Data Description Guide*, PDF p.76 (printed p.72), PRICE, END OF
> PERIOD. [PRIMARY DATA DOC] [read in full — relevant sections verbatim]

That is the cleanest convention sentence in the lane. It is accompanied by a full
missing-data vocabulary: a price with no close and no quote is **zero**, a bid/ask average
is **negative**, and a return that cannot be computed carries one of **four named missing
codes** (−66 / −77 / −88 / −99) rather than a number. **In CRSP daily, a multi-day halt is
visible** — as rows that exist, with `vol = 0`, with a negative or zero price, and with
`ret = −99.0`. The row is not dropped and the price is not carried.

**2. THE REFERENCE IMPLEMENTATIONS ARE UNANIMOUS ON THE RULE, AND THE RULE IS NOT "DON'T
FORWARD-FILL" — IT IS "FILL THE LABEL, NEVER THE PRICE."**

I read two replication packages line by line — Chen & Zimmermann's Open Source Asset
Pricing (212 published predictors) and Jensen–Kelly–Pedersen's *Replication Crisis*
package (*Journal of Finance* 2023) — and grepped both exhaustively for forward-fills.
**Both forward-fill heavily. Neither forward-fills a price or a return.** What gets carried
is SIC codes, credit ratings, tickers, governance indices, IBES actuals, 13F holdings, FX
rates and **portfolio-membership labels**. See §5 and the negative control in §6 — the grep
that must return zero returns zero, and the same regex returns 28 hits on other columns.

**3. AND THERE IS ONE DOCUMENTED, AUTHOR-SANCTIONED EXCEPTION, AND IT IS THE ONE THIS
PROGRAMME USES.** Shane Corwin's own published sample program for the Corwin–Schultz
high–low spread estimator **detects a non-trading day and substitutes the previous day's
high–low range**, re-anchored to today's close. JKP's `BIDASK_HL` macro reproduces it.
`CLAUDE.md` instructs that held-name spreads be estimated with Corwin–Schultz off the OHLC;
**the estimator's reference implementation fabricates a high and a low on a no-trade day by
construction.** §3.4. This is reported, not recommended.

**What the literature does NOT state, and this is the negative half of the headline:** the
prose papers do not state panel mechanics at all. Gu, Kelly & Xiu (2020, RFS) — one of the
most-cited modern panels — says *"For ease of presentation, we assume a balanced panel of
stocks, and defer the discussion on missing data to Section 2.1"*, and Section 2.1 then
discusses only missing **characteristics**. **The ragged edge itself is never addressed.**
That is the H4 pattern repeating: **the date is stated, the mechanics are not.** So §1–§4
lean on code and manuals, exactly as the lane anticipated.

---

## SOURCES, RANKED BY HOW EXPLICIT THEY ARE

| # | Source | What it states | Type / establishment |
|---|---|---|---|
| 1 | CRSP, *Stock and Index Data Description Guide* (CHASS mirror) | No price carried across days; zero = no price; −66/−77/−88/−99 missing-return codes; Begin/End of Valid Data indices on a master calendar | [PRIMARY DATA DOC] [read in full — relevant sections verbatim] |
| 2 | Jensen, Kelly & Pedersen, `ReplicationCrisis` / `GlobalFactors` SAS | Per-name min–max grid; missing return ⇒ 0 in the cum-return index, stated in a comment; `ret_lag_dif` gap rule; **excludes Compustat `prcstd = 5`, quoting its meaning and its 14.5% frequency** | [PRIMARY DATA DOC — code for JF 2023] [read in full — code read line by line, not executed] |
| 3 | Chen & Zimmermann, OSAP `CrossSection` (R / Stata / Python) | Missing-return rows **dropped**; `fill_date_gaps` builds a per-name backbone "to create a clean panel for lag operations"; `replace ret = 0 if mi(ret)` in 26 momentum/reversal predictors | [PRIMARY DATA DOC] [read in full — code read line by line, not executed] |
| 4 | Corwin, *Sample SAS Program* (Notre Dame, 2019) | Flags `INOTRADE` on `PRC<0 OR VOLUME=0`, then **replaces missing high/low with the retained prior-day range**; `IF N1>=12` monthly minimum | [PRIMARY DATA DOC — author's own code] [read in full] |
| 5 | zipline (Quantopian) source | Pipeline uses `include_start_date=False` — **IPO day excluded**, with the reason in the docstring; `price` field ffilled by default; ffill explicitly truncated at `end_date`; `ReindexBarReader` fills a superset calendar with NaN | [SOFTWARE DOC] [read in full — relevant modules verbatim] |
| 6 | Ince & Porter, "Individual Equity Return Data from Thomson Datastream: Handle with Care!" | "CRSP will report no data whereas TDS reports the last valid data point"; TDS **pads** after cessation; their screen deletes trailing zero returns | [PEER-REVIEWED, JFR 2006 — quoted from the 2003 preliminary draft; see §8] [read in full — the draft] |
| 7 | Scheuch, Voigt, Weiss, Frey, *Tidy Finance* (open textbook), WRDS/CRSP chapter | `drop_na(ret_excess, mktcap, mktcap_lag)`; keeps only months inside `secinfostartdt`–`secinfoenddt`; **lags by date-shift-and-join, and sets the positional-`lag()` discrepancy as an exercise** | [SOFTWARE DOC / textbook] [read in full — chapter verbatim] |
| 8 | Microsoft `qlib`, `docs/component/data.rst` | "open, close, high, low, volume, money and factor will be set to NaN if the stock is suspended" | [SOFTWARE DOC] [read in full] |
| 9 | Gu, Kelly & Xiu (2020), RFS 33(5) | Assumes a balanced panel "for ease of presentation"; fills missing **characteristics** with the cross-sectional median; never states the ragged-edge treatment | [PEER-REVIEWED] [read in full] |
| 10 | Ang, Hodrick, Xing & Zhang, NBER WP 10852 (pub. JF 2006) | "with more than 17 daily observations" — a minimum-observation rule, with no definition of "observation" | [WORKING PAPER — published JF 2006] [read in full] |
| 11 | Lo & MacKinlay (1990), "An Econometric Analysis of Nonsynchronous Trading" | The canonical documentation of what stale/infrequent prices do to return moments | [PEER-REVIEWED, JoE 1990] [abstract only — verbatim from NBER w2960] |
| 12 | pandas, `DataFrame.rolling` | `min_periods`: "Minimum number of observations in window required to have a value; otherwise, result is np.nan" | [SOFTWARE DOC] [read in full — parameter text verbatim] |
| 13 | Standard & Poor's, *Compustat Xpressfeed — Understanding the Data* | Confirms `PRCSTD` = "Price Status Code –- Daily" and a reference table `r_prc_stat`/`PRCSTDCD`; **does not enumerate code 5** | [VENDOR OFFICIAL DOC] [read in full — searched, absent] |

---

## 1. ENTRY — what is a name's first usable bar?

### 1.1 The vendor: the first daily bar IS the first trading day; the first MONTHLY bar is not

CRSP daily begins at the first trading date. The header field is explicit:

> "Begin of Stock Data is the date that data begins for the security, in YYYYMMDD format. It
> is the date of the first period in the time series arrays and is always greater than zero."
> — CRSP guide, PDF p.19 (printed p.15). [PRIMARY DATA DOC] [verbatim]

So **the IPO day is in the daily file.** What is *not* in it is a return on that day:

> "−66.0 Valid current price but no valid previous price. Either first price, unknown
> exchange between current and previous price, or more than 10 periods between time t and
> the time of the preceding price t′."
> — CRSP guide, PDF p.45 (printed p.41), HOLDING PERIOD TOTAL RETURN. [verbatim]

The monthly file states a different and stronger entry rule:

> "In a monthly database, Price or Bid/Ask Average is the price on the last trading date of
> the month. **The price series begins the first month-end after the security begins trading
> and ends the last complete month of trading.**"
> — CRSP guide, PDF p.76 (printed p.72). [verbatim, emphasis mine]

**That is an entry convention and an exit convention in one sentence**, and it is the only
place in this lane where a vendor states both.

### 1.2 The reference implementations: the first bar carries no return, by construction

JKP set it to missing explicitly rather than letting `lag()` produce garbage:

```sas
ret = ri/lag(ri)-1;
ret_local = ri_local/lag(ri_local)-1;
ret_lag_dif = intck(&period., lag(datadate), datadate);
if first.iid then do;
    ret=.;
    ret_local=.;
    ret_lag_dif=.;
end;
```
— `GlobalFactors/project_macros.sas`, ll. 698–707. [PRIMARY DATA DOC] [verbatim]

Corwin does the same for the high–low range — `IF FIRST.PERMNO THEN DO; LOPRCR=.; HIPRCR=.;
END;` — with the intent stated in the banner comment: `** REPLACE WITH MISSING VALUES WHEN
BEGINNING OF SERIES HAS HIGH=LOW *`.

### 1.3 The only source that states WHY the first bar is unusable — and it excludes it

zipline's `AssetFinder.lifetimes` is the most explicit statement I found anywhere, in any
source type, on whether the IPO day counts:

> ```
> include_start_date : bool
>     Whether or not to count the asset as alive on its start_date.
>
>     This is useful in a backtesting context where `lifetimes` is being
>     used to signify "do I have data for this asset as of the morning of
>     this date?"  For many financial metrics, (e.g. daily close), data
>     isn't available for an asset until the end of the asset's first
>     day.
> ```
> — `zipline/assets/assets.py`, ll. 1444–1462. [SOFTWARE DOC] [verbatim]

And the Pipeline engine **passes `False`**, so the IPO day is outside the tradeable mask:

```python
lifetimes = finder.lifetimes(
    sessions[start_idx - extra_rows:end_idx],
    include_start_date=False,
    country_codes=(domain.country_code,),
)
```
— `zipline/pipeline/engine.py`, l. 508–512. The implementation is `mask = lifetimes.start <
raw_dates` (strict `<`). [verbatim]

**This is the lane's answer to "is the IPO day included?": the most-used open-source daily
engine says no, and says why in one sentence — the close is not knowable at the open of the
day it is printed.**

### 1.4 "First N days excluded" — I could not find a stated N with a reason

I looked for a convention of the form "we exclude the first N days/months after listing" and
**did not find one stated with a justification** in anything I read verbatim. What exists
instead is **minimum-observation rules**, which exclude young names as a side effect rather
than by design:

- Ang, Hodrick, Xing & Zhang: *"We run the regression for all stocks on AMEX, NASDAQ and the
  NYSE, with more than 17 daily observations."* (NBER w10852; replicated verbatim as a
  description in Detzel et al.). **The paper does not say whether "observations" means rows
  or non-missing returns.** [WORKING PAPER] [read in full]
- Corwin's own code: `IF N1>=12;` — a monthly spread estimate requires at least 12 daily
  spread estimates. [read in full]
- OSAP `ReturnSkew.py`: `predictors.filter(pl.col("ndays") >= 15)`, and the comment resolves
  the ambiguity Ang et al. leave open, **in the permissive direction**:
  `# Count includes all rows (even those with missing returns) to match original logic`.
  [verbatim] **A 15-of-21 rule that counts rows, not valid returns, is not the same screen
  as one that counts valid returns**, and OSAP says it is matching the original paper.
- OSAP `min_periods` values on rolling windows range from 1 to 72 across predictors
  (`min_periods=1` for `CredRatDG` and `DivYieldST`; `20` for `Beta`; `36` for
  `BetaLiquidityPS`; `48/60` for the `betaRR` family; `72` for `BetaTailRisk`). **There is no
  single convention; each predictor carries the original paper's number.**

### 1.5 Shortened window, or excluded? Both exist, in the same repository

- **Excluded, via calendar-aware lags.** OSAP's `Mom12m` is
  `(1+l.ret)*…*(1+l11.ret) − 1`; any missing lag makes the product missing, so a name with
  fewer than 11 prior months has no signal. The python port reproduces this with
  `stata_multi_lag(..., fill_gaps=True)`.
- **Shortened silently, with no guard at all.** zipline's `SimpleMovingAverage` is
  `out[:] = nanmean(data, axis=0)` — and the class comment is about suppressing warnings, not
  about sufficiency:
  > ```
  > # numpy's nan functions throw warnings when passed an array containing only
  > # nans, but they still returns the desired value (nan), so we ignore the
  > # warning.
  > ```
  — `zipline/pipeline/factors/basic.py`, ll. 102–113. **There is no `min_periods` equivalent.
  A 63-day SMA over a window with 3 valid observations returns the mean of 3, silently.**
  [SOFTWARE DOC] [verbatim]

pandas, by contrast, makes the guard the default for integer windows:

> "min_periods int, default None — Minimum number of observations in window required to have
> a value; otherwise, result is np.nan. For a window that is specified by an offset,
> min_periods will default to 1. For a window that is specified by an integer, min_periods
> will default to the size of the window."
> — pandas `DataFrame.rolling`. [SOFTWARE DOC] [verbatim]

**That default is the opposite of zipline's behaviour**, and "for an offset window,
min_periods defaults to 1" is the trap: a time-based window silently accepts one observation.

---

## 2. EXIT — does the row end, continue as missing, or continue as a constant?

*Delisting returns are spent ground and treated here as known background. This section is
only about the shape of the panel after the last bar.*

**Four independent sources, four different mechanisms, one answer: THE ROW ENDS, or becomes
NaN. Nothing continues as a constant — except in one vendor, where it does, and that is the
documented failure mode.**

**(a) CRSP — the row ends.**
> "End of Stock Data is the date that data ends for the security, in YYYYMMDD format. It is
> the date of the last period in the time series arrays and is always greater than zero."
> — CRSP guide, PDF p.37 (printed p.33). [verbatim]

**(b) Datastream — the row continues as a constant, and this is the canonical citation for
why that is a problem.**
> "The approach used by TDS and CRSP when a user requests data after a firm ceases trading is
> different. CRSP will report no data whereas TDS reports the last valid data point. TDS pads
> the time period after the firm ceases trading with constant values equal to the last month
> (or day) that the firm traded."
> — Ince & Porter. [see §8 on which version this is quoted from]

And their remedy, which is a *screen on the fabricated zeros*, not on the prices:
> "To identify and eliminate these dummy records we delete all monthly observations from TDS
> from the end of the sample to the first non-zero return."

With the cost of the remedy stated:
> "We realize that a small number of valid zero return observations may be lost at the end of
> the sample."

**This is the single most directly on-point source in the lane for the programme's standing
rule that a fabricated price is a fabricated return.** It documents the failure mode, names
the vendor, and gives the standard repair — and it tells you the repair has a price.

**(c) zipline — NaN after `end_date`, and the reason is written down.**
```python
# forward-filling will incorrectly produce values after the end of
# an asset's lifetime, so write NaNs back over the asset's
# end_date.
normed_index = df.index.normalize()
for asset in df.columns:
    if history_end >= asset.end_date:
        # if the window extends past the asset's end date, set
        # all post-end-date values to NaN in that asset's series
        df.loc[normed_index > asset.end_date, asset] = nan
```
— `zipline/data/data_portal.py`, ll. 1025–1033. [SOFTWARE DOC] [verbatim]

**This is the clearest statement anywhere that the two questions are different: inside a
life, forward-filling is the default; past the end of the life, it is named "incorrect" and
explicitly undone.**

**(d) OSAP and JKP — the row simply does not exist.** Neither builds a panel-wide grid (§4),
so a dead name has no rows after its last observation. OSAP additionally drops the
missing-return rows it does have:
```r
crspmret <- crspm %>% select(permno, date, yyyymm, ret) %>% filter(!is.na(ret)) %>% …
…
crspdret = crspdret[ !is.na(ret) ]
```
— `Portfolios/Code/11_ProcessCRSP.R`, ll. 69 and 109. [verbatim]

**(e) Tidy Finance — both: bound the row range by the vendor's own validity dates, then drop
the missing.**
> "we keep only months within permno-specific start dates (`secinfostartdt`) and end dates
> (`secinfoenddt`)"
> "Since excess returns and market capitalization are crucial for all our analyses, we can
> safely exclude all observations with missing returns or market capitalization."
> `crsp_monthly <- crsp_monthly |> drop_na(ret_excess, mktcap, mktcap_lag)`
> — *Tidy Finance*, "WRDS, CRSP, and Compustat". [SOFTWARE DOC / textbook] [verbatim]

**Note the word "safely".** It is asserted, not argued, and it is the step that converts a
NaN into a missing row — which §3.3 shows is not a free operation.

---

## 3. GAPS INSIDE A LIFE — missing row, NaN, or forward-filled price?

### 3.1 The vendors disagree, and both states are documented

| Vendor | A session inside a life with no trade | Evidence |
|---|---|---|
| CRSP daily | **Row exists.** `vol = 0`; price is a **negative bid/ask average** or **zero**; `ret = −99.0`. Nothing carried. | "There is no price data from one trading day applied to the next trading day." (PDF p.76) / "If neither price nor bid/ask average is available, Price or Bid/Ask Average is set to zero." (PDF p.75, PRICE, END OF PERIOD) / "RMISSP −99.0 missing return due to missing price." (PDF p.124, Appendix V) |
| Compustat Security Daily | **Row exists with a forward-filled price**, flagged `prcstd = 5` | JKP footnote, below |
| Datastream | **Row exists with a forward-filled price**, unflagged | Ince & Porter, §2(b) |
| qlib (as a convention) | **Row exists, all OHLCV NaN** | "open, close, high, low, volume, money and factor will be set to NaN if the stock is suspended" — `docs/component/data.rst`, l. 197 |

That CRSP keeps the row as a zero-volume row is not only stated — it is **relied on** in
published work. OSAP's implementation of Liu (2006, JFE 82, 631–671) counts them directly:

```python
df["countzero"] = np.where(df["vol"] == 0, 1, 0)
```
— `ZZ1_zerotrade_zerotradeAlt1_zerotradeAlt12.py`. [verbatim]

**A measure whose whole content is the number of zero-volume days could not exist if the
vendor dropped the row or filled the price.** That is a useful existence proof and it is the
closest thing in this lane to an answer to G3's original question, for CRSP.

### 3.2 THE BEST QUOTE IN THE LANE: a JF replication package screens out the vendor's
forward-filled prices, names the flag, and gives its frequency

> ```
> [1]: This screen ensures that the return is always computed between two days with a price.
>      The ret_day_dif lets the user check if it's within a reasonable range.
>      Compustat have some observations whre prc and curcdd is missing and div and curcddiv is
>      not missing. In other words dividend ex-date occuring outside trading days
>      should not be used to compute returns. Further, the screen on prcstd ensures that
>      returns are computed with non-stale prices.
>      Specifically prcstd in (3, 4, 10) ensures that the price is taken from observable
>      market data. The main excluded prcstd is 5, which is "No prices available, last actual
>      price was carried forward".
>      This is prevalent in the G_SECD where it accounts for 14.5% of the observations.
> ```
> — JKP, `GlobalFactors/project_macros.sas`, ll. 1383–1389 (footnote `[1]`), referenced from
> the active screen at l. 697: `set __comp_sf1(where = (not missing(ri) and prcstd in (3, 4,
> 10)));` [PRIMARY DATA DOC] [verbatim]

Three things at once: **a vendor forward-fills prices; the vendor flags it; and in the global
daily file the flag fires on 14.5% of rows.** A programme that forbids forward-filling has, in
this footnote, both the justification and the magnitude of what it is avoiding.

**Caveat, stated because it matters:** the 14.5% figure is JKP's own count on Compustat
`g_secd`, which is the **global** file — not US. It is not a US number and I did not find a
US number.

### 3.3 The consequences of each choice — where they are documented

**(i) A forward-filled price fabricates a zero return; the documented consequence is
contamination of every return moment.** The canonical reference is Lo & MacKinlay (1990):

> "We develop a stochastic model of nonsynchronous asset prices based on sampling with random
> censoring. In addition to generalizing existing models of non-trading our framework allows
> the explicit calculation of the effects of infrequent trading on the time series properties
> of asset returns. These are empirically testable implications for the variances,
> autocorrelations, and cross-autocorrelations of returns to individual stocks as well as to
> portfolios. We construct estimators to quantify the magnitude of non-trading effects in
> commonly used stock returns data bases and show the extent to which this phenomenon is
> responsible for the recent rejections of the random walk hypothesis."
> — NBER w2960 abstract. [PEER-REVIEWED, *Journal of Econometrics* 1990] [abstract only]

**Establishment note, and it is a real limitation: I read the abstract, not the paper.** The
abstract establishes that the effects on variances and autocorrelations are *calculable and
material*; it does not by itself give a sign or a magnitude for a daily US single-name panel,
and I am not asserting one. What it does establish is that this is a named, modelled,
fifty-year-old problem and not a data-hygiene footnote.

The applied literature then uses the fabricated zeros as a *quality signal* rather than
treating them as data. JKP census them twice, in comments that state the reason:
```sas
a.ret_lag_dif, (a.ret_local = 0) as ret_zero,
…
sum(a.ret_local = 0) as zero_obs  /* Some firms have almost inclusively zero returns. These should be excluded */
```
— `market_chars.sas`, ll. 53 and 392. [verbatim] And the delisting date itself is defined off
a non-zero return: `set __returns(where=(not missing(ret_local) and ret_local^=0)); /* Take
delisting date to be last day of trading with non missing and non zero return [2]*/`
(`project_macros.sas`, l. 718). **A zero return is treated as evidence of non-trading, not as
a return.**

**(ii) A missing row silently corrupts lags and shortens windows — and this failure mode is
documented three times, in three different source types.**

First, as the *stated purpose* of a utility in OSAP:
> ```python
> def fill_date_gaps(…):
>     """
>     Fill date gaps to create a clean panel for lag operations.
>     Replicates Stata: xtset [group_col] [time_col]; tsfill
>     """
> ```
> — `Signals/pyCode/utils/stata_replication.py`, ll. 199–212. [verbatim]

Second, as a *step with its intent in the comment* in JKP:
> `* Ensure that there is a lag of 1 month between each obs;`
> — `market_chars.sas`, l. 60. [verbatim]

Third — and this is the most pedagogically explicit statement of the failure mode I found
anywhere — as a **textbook exercise**:
> "The most simple and consistent way to add a column with lagged market cap values is to add
> one month to each observation and then join the information to our monthly CRSP data."
> `mktcap_lag <- crsp_monthly |> mutate(date = date %m+% months(1)) |> select(permno, date, mktcap_lag = mktcap)`
> `crsp_monthly <- crsp_monthly |> left_join(mktcap_lag, join_by(permno, date))`
> "If you wonder why we do not use the `lag()` function, e.g., via `crsp_monthly |> group_by(permno) |> mutate(mktcap_lag = lag(mktcap))`, take a look at the Exercises."
>
> Exercise: "Compute `mktcap_lag` using `lag()` (R) or `shift()` (Python) rather than using
> joins as above. Filter out all the rows where the lag-based market capitalization measure
> is different from the one we computed above. **Why are the two measures different?**"
> — *Tidy Finance*, "WRDS, CRSP, and Compustat". [SOFTWARE DOC / textbook] [verbatim]

**The answer to that exercise is the whole of this sub-question.** On a panel with missing
rows, a positional shift reaches across the gap and silently returns a value from the wrong
date; a date-shift-and-join returns `NA`. **Both reference implementations use the join, and
both say so.** OSAP:
```r
signallag = setDT(signal)[ , .(permno, yyyymm, signal, port) ][ , yyyymm := yyyymm + 1 ]…
crspret = crspret %>% left_join(signallag %>% select(permno,yyyymm,signallag, port), by = c('permno','yyyymm'))
```
— `Portfolios/Code/01_PortfolioFunction.R`. [verbatim]

**(iii) And a third consequence that neither of (i) nor (ii) covers: a return computed ACROSS
a gap is a multi-day return wearing a one-day label.** This is the one failure mode that both
CRSP and JKP guard explicitly, and it is the one a "drop the missing rows" policy creates.

CRSP's guard is the 10-period rule:
> "It is based on a purchase on the most recent time previous to this day when the security
> had a valid price. Usually, this time is the previous calendar period."
> — CRSP guide, PDF p.45 (printed p.41). [verbatim]
> "RMISSG −66.0 more than 10 trading days between this day and the day of latest preceding
> price." — CRSP guide, PDF p.124 (printed p.120), Appendix V, MISSING RETURN CODES. [verbatim]

**So CRSP's daily return spans a gap of up to 10 trading days and is then declared missing.**
A return labelled day *t* in `crsp.dsf` is not necessarily a one-day return.

JKP carry that gap width as a column and screen on it at three different thresholds, each with
its reason in the comment:
```sas
ret_miss = missing(ret_x) or ret_lag_dif^=1; /* We set returns with more than one month between price observations to missing (only impact Compustat data) */
…
where ret_lag_dif <= 5 and not missing(ret_exc); * Impose a maximum lag of 5 days between return calculation;
…
where ret_lag_dif > 14;  /* Only used returns based on prices that are not more than two weeks old */
```
— `market_chars.sas` l. 102, `project_macros.sas` l. 1046, `market_chars.sas` l. 400.
[verbatim] Plus the macro-level default: `%let max_date_lag = 14;` for daily and `= 1;` for
monthly (`project_macros.sas`, ll. 893–897).

There is even a **calibration note** for that threshold, left in the code as a commented-out
diagnostic:
> `/* proc freq data=comp_dsf; tables ret_day_dif; run; *Check: 97.2% of non missing ret_day_dif are <=3. 98.8% are <=4; 99.75% are <=10. This might be a reasonable general cutoff for settings returns to 0*/`
> — `project_macros.sas`, l. 788. [verbatim]

**That is the closest thing in this lane to a stated basis for choosing a gap threshold**, and
it is a frequency table, not a principle.

### 3.4 The exception, and it is the one that touches this programme directly

`CLAUDE.md` instructs that the spread of the names HELD be estimated with Corwin–Schultz off
the OHLC. **The estimator's reference implementation forward-fills the high and the low
across non-trading days on purpose.** Corwin's own sample program:

```sas
** RETAIN GOOD HIGH-LOW PRICES AND REPLACE IN CASES WHERE HIGH=LOW                   *
** REPLACE WITH MISSING VALUES WHEN BEGINNING OF SERIES HAS HIGH=LOW                 *
DATA SAMPLE2 (DROP = LOPRCR HIPRCR);
RETAIN LOPRCR HIPRCR;
…
IF LOPRC=HIPRC OR LOPRC<=0 OR HIPRC<=0 OR PRC<=0 OR VOLUME=0 THEN DO; *DROP BAD PRICES AND ZERO VOLU[ME];
  ISAMEPRC=0; IF LOPRC=HIPRC THEN ISAMEPRC=1;
  INOTRADE=0; IF PRC<0 OR VOLUME=0 THEN INOTRADE=1;
  LOPRC=.; HIPRC=.;
END;
…
*REPLACE MISSING/BAD HIGH AND LOW PRICES WITH RETAINED VALUES;
ELSE DO;
  *REPLACE IF WITHIN PRIOR DAY'S RANGE;
  IF LOPRCR<=PRC<=HIPRCR THEN DO; LOPRC=LOPRCR; HIPRC=HIPRCR; HLRESET=1; END;
  *REPLACE IF BELOW PRIOR DAY'S RANGE;
  IF PRC<LOPRCR THEN DO; LOPRC=PRC; HIPRC=HIPRCR-(LOPRCR-PRC); HLRESET=2; END;
  *REPLACE IF ABOVE PRIOR DAY'S RANGE;
  IF PRC>HIPRCR THEN DO; LOPRC=LOPRCR+(PRC-HIPRCR); HIPRC=PRC; HLRESET=3; END;
END;
```
— Shane Corwin, *Sample SAS Program*, sites.nd.edu/scorwin/files/2019/12/. [PRIMARY DATA DOC
— author's own code] [read in full]

JKP reproduce it in `%macro bidask_hl(out=, data=, __min_obs=)`, described in their own header
as *"Corwin-Schultz High-Low Bid-ask Estimator - Heavily inspired by Shane Corwins code … -
Primary change: I adjust prices for stock splits"* (`char_macros.sas`, ll. 156–162), with the
same logic and the same `hlreset` flag (ll. 176–219) and an added guard
`if prc_low ^= 0 and prc_high/prc_low > 8 then do; prc_low = .; prc_high = .; end;`.

**Three things follow, and I am reporting them, not recommending anything:**
1. The trigger set is `VOLUME=0 OR PRC<0 OR LOPRC=HIPRC OR LOPRC<=0 OR HIPRC<=0 OR PRC<=0` —
   **which is exactly the no-trade/halt/thin-name set.** A Corwin–Schultz estimate on a halted
   or non-trading name is computed from a synthetic range.
2. The carry is **range-preserving and close-anchored** (`HLRESET=2`/`3` slide the retained
   range so it brackets today's close) — not a naive `ffill` of two price levels. So it is a
   more defensible construction than "fill the price", and it is still a fabricated high and a
   fabricated low.
3. `INOTRADE` and `HLRESET` are **flags the author outputs**, so the fabrication is
   countable. A programme wanting to stay inside its own rule has an auditable route: count
   the rows, or compute the estimator on `HLRESET=0` rows only. **Whether the resulting
   estimate is still Corwin–Schultz is a question neither source addresses.**

---

## 4. THE RAGGED EDGE — aligning different start/stop dates without look-ahead

### 4.1 The standard treatment is NOT a panel-wide grid. It is a PER-NAME grid.

Both replication packages build the grid from **each name's own first and last observation**,
then left-join. Neither reindexes to the union of all names' dates.

OSAP:
```python
# create a backbone of group-time with no gaps
out = (
    df.group_by(group_col)
    .agg(
        pl.col(time_col).min().alias("time_min"),
        pl.col(time_col).max().alias("time_max"),
    )
    .with_columns(
        pl.date_ranges(
            pl.col("time_min").dt.offset_by(start_padding),
            pl.col("time_max").dt.offset_by(end_padding),
            period_str,
        ).alias(time_col)
    )
    .explode(time_col)
    .select([group_col, time_col])
)

# merge input onto backbone and sort
out = out.join(df, on=[group_col, time_col], how="left")
```
— `Signals/pyCode/utils/stata_replication.py`, `fill_date_gaps_pl`, ll. 233–262. [verbatim]

JKP:
```sas
* Ensure that there is a lag of 1 month between each obs;
proc sql;
    create table __stock_coverage as
    select id, min(eom) as start_date, max(eom) as end_date
    from __monthly_chars1
    group by id;
quit;

%expand(data=__stock_coverage, out=__full_range, id_vars=id, start_date=start_date, end_date=end_date, freq='month', new_date_name=eom);

proc sql;
    create table __monthly_chars2 as
    select a.id, a.eom, missing(b.id) as obs_miss, …
    from __full_range as a left join __monthly_chars1 as b
    on a.id=b.id and a.eom=b.eom
    order by id, eom;
quit;
```
— `market_chars.sas`, ll. 60–78, with `%expand` at `project_macros.sas` ll. 197–211.
[verbatim]

**This is the convention, stated in code twice, independently: materialise the gaps INSIDE a
name's life so lags are calendar-correct; do NOT extend a name beyond its own first and last
observation.** The ragged edge is preserved by never building the rectangle, and look-ahead is
avoided at the edge because no row exists where no observation existed.

**Which means neither reference implementation builds the object this programme builds.** A
grid formed as the union of all names' dates is a third design, and I found **no published
source that states it as a convention**. What I can say is what the two that exist avoid by
not building it, and what the one library that *does* build it does instead (§4.2).

### 4.2 The one implementation that DOES align to a common grid, and how it fills

zipline aligns readers whose calendars differ onto a superset calendar:

> ```
> class ReindexBarReader(with_metaclass(ABCMeta)):
>     """
>     A base class for readers which reindexes results, filling in the additional
>     indices with empty data.
>
>     Used to align the reading assets which trade on different calendars.
>
>     Currently only supports a ``trading_calendar`` which is a superset of the
>     ``reader``'s calendar.
>     …
>     - first_trading_session : pd.Timestamp
>        The first trading session the reader should provide. Must be specified,
>        since the ``reader``'s first session may not exactly align with the
>        desired calendar.
> ```
> — `zipline/data/resample.py`, ll. 601–630. [SOFTWARE DOC] [verbatim]

And "empty data" is defined exactly:
```python
def get_value(self, sid, dt, field):
    # Give an empty result if no data is present.
    try:
        return self._reader.get_value(sid, dt, field)
    except NoDataOnDate:
        if field == 'volume':
            return 0
        else:
            return np.nan
```
— same file. [verbatim] The on-disk daily reader is consistent: a missing bar is stored as
`0` and converted on read — `if price == 0: return nan` (`bcolz_daily_bars.py`, l. 701).

**So the only source that aligns to a common grid fills with NaN and volume 0 — not with a
forward-filled price.** Its forward-fill lives in a separate, opt-in, clearly-labelled place
(§4.3).

### 4.3 The one place where a default DOES forward-fill, and what it is scoped to

```python
def get_history_window(self, assets, end_dt, bar_count, frequency, field,
                       data_frequency, ffill=True):
    """
    …
    ffill : boolean
        Forward-fill missing values. Only has effect if field
        is 'price'.
    """
```
— `zipline/data/data_portal.py`, ll. 915–947. [verbatim]

**`ffill=True` is the default.** The fill is scoped to the synthetic `price` field — `close`,
`open`, `high`, `low`, `volume` are *not* filled — and it reaches back **before** the window
to seed a leading NaN via `get_last_traded_dt`, so a name halted across the whole window still
gets a price. Then it is truncated at `end_date` (§2(c)).

**This is the source that "recommends forward-filling", in the lane's sense: report it, do not
adopt it.** Its own comment supplies the argument against adopting it wholesale — it calls the
post-death case "incorrect" and patches it — but it offers **no stated reason for the in-life
case**, and does not bound how stale the carried price may be. That is the gap between zipline
and CRSP (10 trading days) / JKP (`max_date_lag = 14`), both of which bound it.

### 4.4 Look-ahead: what is actually stated

**The only explicit look-ahead reasoning I found about panel mechanics is a code comment.**

```r
## apply filters and sign
# note the signal dataset is lagged further down, so
# filtering here does not look ahead
```
— OSAP, `Portfolios/Code/01_PortfolioFunction.R`. [verbatim]

That is an argument about *ordering*: filter-then-lag is safe because the lag is applied to the
already-filtered object. And the lag mechanism is the date-shift-and-join of §3.3(ii), which is
the look-ahead-safe construction — a positional shift on a gappy panel is not.

zipline's corresponding guard is structural rather than argued: the pipeline requests
`extra_rows` *before* `start_date` so trailing windows are filled with real history rather than
with whatever the window start happens to contain, and **refuses to run if that history does
not exist**:
> "extra_rows : int — Number of extra rows to compute before `start_date`. Extra rows are
> needed by terms like moving averages that require a trailing window of data."
> … `raise NoFurtherDataError.from_lookback_window(initial_message="Insufficient data to
> compute Pipeline:", …)`
> — `zipline/pipeline/engine.py`, `_compute_root_mask`. [verbatim]

**Beyond these, I found no source — peer-reviewed, working paper, vendor or software — that
states a look-ahead convention for aligning a ragged panel to a common date grid.** §9.4.

---

## 5. THE CROSS-CUTTING RULE: fill the label, never the price

This was not in the lane's four sub-questions and it is the most transferable finding, so it
gets its own section.

Both replication packages forward-fill extensively. **Every single fill target is a
slow-moving characteristic, an identifier, a link key, or a portfolio label. Not one is a
price, a return, a high, a low, or a volume** (§6 is the control).

| Package | What IS forward-filled | Where |
|---|---|---|
| OSAP | `sic`, `sicCRSP`, `ticker`, `credrat`, `G` (governance), `anndats_act`, `cd3`, `ppent`, `pstkq`, `mve_permco`, `me_datadate`, `EarningsStreak`, 13F holdings, IBES actuals | 28 `ffill` call sites across `Predictors/`, `Placebos/`, `DataDownloads/`; plus `utils/forward_fill.py`, whose docstring scopes it: *"to forward-fill missing quarterly financial data to replicate Stata's behavior when quarterly fields (ceqq, atq, etc.) are missing"* |
| OSAP | **the portfolio assignment itself**, for multi-month holds: `group_by(permno) %>% fill(port) %>% filter(!is.na(port))` | `01_PortfolioFunction.R` |
| JKP | **the FX rate only**: `/* Carry forward fx observations in case gaps*/` | `project_macros.sas`, l. 233 |

**The shape of the rule: a characteristic that was true yesterday is probably still true
today, so carrying it is an estimate. A price that did not print did not print, so carrying it
is a fabrication.** Neither package states the rule in those words — it is inferred from the
complete absence of price fills against 28 characteristic fills, which is why §6 exists.

**And one more distinction worth carrying out of this lane:** what OSAP does to a missing
return is *not* a forward-fill, it is a **zero-fill**, and it appears in **24 distinct Stata
predictor/placebo files (26 occurrences; two files apply it twice)** and **16 of the python
ports**:

```stata
use permno time_avail_m ret using "$pathDataIntermediate/SignalMasterTable", clear
replace ret = 0 if mi(ret)
gen Mom12m = ( (1+l.ret)*(1+l2.ret)*…*(1+l11.ret) ) - 1
```
— `Signals/LegacyStataCode/Predictors/Mom12m.do`, ll. 3–8; python port
`df["ret"] = df["ret"].fillna(0)` (`Predictors/Mom12m.py`, l. 44). The full Stata list, counted
not asserted: `Mom12m`, `Mom6m`, `Mom12mOffSeason`, `Mom6mJunk`, `MomRev`, `MomVol`,
`MomSeason`, `MomSeason06YrPlus`, `MomSeason11YrPlus`, `MomSeason16YrPlus`, `MomSeasonShort`,
`MomOffSeason`, `MomOffSeason06YrPlus`, `MomOffSeason11YrPlus`, `MomOffSeason16YrPlus`,
`STreversal`, `MRreversal`, `LRreversal`, `IntMom`, `IndMom`, `FirmAgeMom`, `BetaBDLeverage`,
`ZZ1_IntanBM_IntanSP_IntanCFP_IntanEP`, `ZZ1_EarningsValueRelevance_EarningsTimeliness_EarningsConservatism`. [verbatim]

JKP do the same thing in a subtler place, and **state it in the comment**:
```sas
ri_x = ri_x*sum(1, ret_x); /* By using sum instead of 1+ret missing returns are set to 0 */
```
— `market_chars.sas`, l. 93. [verbatim] (SAS `sum(1,.)` is `1`, where `1+.` is missing — so the
idiom *is* the zero-fill, chosen deliberately.)

**So: the reference implementation of 212 published predictors, and the replication package of
a 2023 JF paper, both fabricate a zero return on a row whose return is missing — in order to
keep a rolling window from going missing.** It is done on rows that exist, not on rows that
are created, so it is a narrower fabrication than forward-filling a price. It is still a
fabricated return, it is still unremarked in the prose, and it is the single most widespread
convention I found in this lane.

---

## 6. NEGATIVE CONTROLS AND METHOD NOTES

**No parameterised endpoint was harvested in this lane.** Every fetch was a single static
document or a single raw source file at a fixed URL, so the CDN-replay failure mode from H1
has no surface here. I state that rather than reporting a control I did not need.

**I did run a control on my own central claim**, because "neither package forward-fills a
price" is an assertion about an *absence* and those are the ones that invert:

| Probe over the full OSAP tree (`--include=*.py`) | Hits |
|---|---|
| A. `\.ffill\(\)|forward_fill\(\)|fillna\(method=.ffill` — does the pattern work at all? | **28** |
| B. the same, restricted to `ret`, `prc`, `ret_x`, `ret_local`, `ret_exc`, `close`, `prc_adj` — **must be 0 if the claim is true** | **0** |
| C. which column names ARE filled | `cd3`, `ticker`, `sicCRSP`, `sic`, `pstkq`, `mve_permco`, `G`, `ppent`, `me_datadate`, `credrat`, `anndats_act`, `EarningsStreak` |
| D. an impossible token (`zzz_nonexistent_token_qqq`) — must be 0 | **0** |

And the same on JKP's SAS: the only `carry forward` / `carried forward` strings in the whole
pipeline are the **FX** fill (l. 233) and the **`prcstd = 5` description they exclude**
(l. 1387). Control token: 0.

**So A and C prove the instrument works, B and D prove the answer is zero, and the absence is
measured rather than assumed.** The one thing this control does NOT cover is the
Corwin–Schultz `RETAIN` block (§3.4) — **which my first `ffill`-shaped grep missed entirely,
because SAS's `RETAIN` does not look like a forward-fill.** I found it only by grepping for
the words "carry forward". **That is the live lesson: a search for a forward-fill by its
pandas name will not find a forward-fill written in SAS, and the one exception in the lane is
the one my first pass missed.**

**Summariser discipline.** Three items were first seen through a summariser and all three were
then re-read directly from the bytes before being quoted: the Ince & Porter sentences (grepped
out of the extracted page text), the CRSP `prc` zero convention (read from the PDF's own
extracted text with page indices), and the qlib suspension sentence (read from
`docs/component/data.rst` on GitHub, not from the rendered docs). **No quotation in this brief
rests on a summariser's paraphrase.** Where I have only an abstract, I say so in the same
sentence as the claim (Lo & MacKinlay, §3.3(i)).

**Code was read, never executed.** Nothing in this lane was run.

---

## 7. BLOCKS, LOGGED BY TOOL AND RESPONSE

1. **WebFetch** → `https://wrds-support.wharton.upenn.edu/hc/en-us/articles/115003411052-SAS-Code-Extracts-Closing-Price-of-the-First-Trading-Day-for-All-CRSP-Stocks` → **HTTP 403 Forbidden**, no body returned.
2. **Bash/curl** (project-mailbox UA) → same URL → **HTTP 404**, 11,947 bytes of Zendesk error page. So the article ID in the search result does not resolve; this is not a UA block but a dead link. **WRDS sample-construction documentation is therefore NOT established in this brief**, and the lane's WRDS prong is unmet (§9.1).
3. **Bash/curl** → `https://www.crsp.org/wp-content/uploads/guides/CRSP_US_Stock_&_Indexes_Database_Data_Descriptions_Guide.pdf` → **HTTP 404**, served a 190,807-byte HTML error page that `file` identifies as HTML, not PDF. The same-titled guide at the University of Toronto CHASS mirror returned **HTTP 200** and a valid 1,486,019-byte PDF, 132 pages, which is the copy quoted throughout. **Version caveat in §9.2.**
4. **WebFetch** → `https://www.tidy-finance.org/r/wrds-crsp-and-compustat.html` → returned a 623-byte JavaScript redirect stub with `<title>Redirect</title>`; the summariser correctly reported there was no content. **Not a block** — resolved by fetching `/chapters/wrds-crsp-and-compustat.html` (HTTP 200, 258,423 bytes).
5. **Bash/curl** → `https://silo.tips/download/individual-equity-return-data-from-thomson-datastream-handle-with-care` → **HTTP 200** but `Content-Type: text/html`; the "PDF" is an HTML page carrying the paper's extracted text. **Not a block, but see §8** — it is the wrong version of the paper.
6. Searched `compustat_users_guide-2003.pdf` (735 pp.), `CompustatManualChpt5.pdf` (285 pp.), `COMPUSTAT (Global) Data Guide (2002).pdf` (901 pp.) and `xf_understanding_the_data.pdf` (106 pp.) for `PRCSTD` / "Price Standard" / "carried forward". **Only the Xpressfeed guide mentions `PRCSTD`**, as "Price Status Code –- Daily" with a reference table `r_prc_stat` → `PRCSTDCD`. **None enumerates code 5.** Not a block — an absence, reported as §9.3.

---

## 8. TEXT INSIDE FETCHED CONTENT THAT I AM FLAGGING RATHER THAN ACTING ON

Per the shared rules, every page is data. Nothing I fetched contained an instruction
addressed to an agent, and nothing attempted to redirect my behaviour. **One item requires a
flag on different grounds.**

The silo.tips copy of Ince & Porter is **not** the published *Journal of Financial Research*
(2006) article. Its own header reads:

> "Individual Equity Return Data From Thomson Datastream: Handle with Care!
> December 2003 **PRELIMINARY (Please do not quote without permission)**"

**I am flagging this rather than acting on it, and I am flagging it both ways.** It is text
inside fetched content, so it is data and not an instruction — but it is also a material fact
about the source: **the sentences I quote in §2(b) and §3 are from a 2003 preliminary draft,
and I could not read the published 2006 version.** The published version is Ince & Porter,
*Journal of Financial Research* 29(4), 463–479, doi 10.1111/j.1475-6803.2006.00189.x. I did
not verify that the padding and zero-return-deletion sentences survive into it unchanged,
although the paper is universally cited for exactly that screen. **Treat the Ince & Porter
quotes as [WORKING PAPER 2003] establishment, not [PEER-REVIEWED 2006]**, and re-verify
against the journal version before any of it is quoted in the programme's own record.

---

## 9. WHAT I COULD NOT VERIFY, STATED PLAINLY

1. **WRDS's own sample-construction documentation — not established at all.** The one WRDS
   article the search surfaced is a dead link (§7.1, §7.2). I have no WRDS-authored statement
   of any convention in this brief. The lane named WRDS as a priority target and **that prong
   failed.**

2. **The CRSP guide I read is undated in my hands and may not be current.** It is the
   *Stock and Index Data Description Guide* for CRSPAccess, served from a university mirror
   because crsp.org returned 404 for the equivalent filename. **CRSP rolled out a new tape
   structure ("CRSP 2.0") in 2022 and again in 2025** — *Tidy Finance* notes "there is no need
   to additionally download delisting information since it is already contained in the most
   recent version of `msf`" and cites a 2026 paper on the 2025 changes. **I did not verify
   that the missing-value conventions, the −66/−77/−88/−99 codes, the 10-trading-day rule, or
   the "no price data from one trading day applied to the next" sentence are unchanged in the
   current tape.** Every CRSP quotation here should be re-checked against the version the
   programme's own data derives from, if any.

3. **No vendor-official enumeration of Compustat `prcstd = 5`.** The string *"No prices
   available, last actual price was carried forward"* is quoted **from JKP's SAS comment**,
   which is a researcher quoting the vendor. The Xpressfeed guide confirms the variable and
   its reference table exist but does not list the codes (§7.6). **So the best-quoted
   forward-fill flag in this brief is established at one remove, and the 14.5% frequency is
   JKP's own count on the GLOBAL daily file, not a US number.**

4. **No stated convention for aligning a ragged panel to a UNION-OF-ALL-DATES grid.** Both
   replication packages build per-name min–max grids and never form the rectangle; zipline
   forms a common grid but only as a superset *trading calendar*, not as a union of names'
   observed dates. **I found no source of any type that states the union-of-names construction
   as a convention, states its look-ahead properties, or documents its failure modes.** If
   that construction has a literature, I did not find it.

5. **No stated "exclude the first N days after listing" convention with a reason.** §1.4. What
   exists is minimum-observation rules with no stated basis for their numbers, ranging from 1
   to 72 periods in a single repository. **If a principled N exists in the literature, I did
   not find it**, and I specifically did not find any source that distinguishes "exclude the
   first N bars" from "require N valid observations" as a design choice.

6. **Ang, Hodrick, Xing & Zhang's "more than 17 daily observations" is not defined.** The
   paper does not say whether an observation is a row or a non-missing return; Detzel et al.
   restate it without resolving it; OSAP's analogous code resolves it the permissive way
   (`# Count includes all rows (even those with missing returns)`) and claims that matches the
   original. **I could not verify which the original meant.**

7. **Lo & MacKinlay (1990) is abstract-only.** §3.3(i). I have not established any sign or
   magnitude for stale-price contamination in a daily US single-name panel from that source,
   and I do not assert one. I also did not read the counter-literature I saw referenced
   (Anderson et al., "Stock return autocorrelation is not spurious"), so **I am not
   representing the Lo–MacKinlay result as uncontested.**

8. **Bali, Engle & Murray's *Empirical Asset Pricing* textbook — not consulted.** The lane
   asked for textbook and handbook treatments of panel construction. I reached one open
   textbook (*Tidy Finance*, which turned out to be one of the strongest sources here) and
   **zero closed ones.** Whether Bali–Engle–Murray states any of these conventions explicitly
   is unknown to me. OSAP cites it for `ReturnSkew` ("following Bali, Engle and Murray 2015,
   Table 14.10"), which suggests it specifies constructions in detail, but I did not read it.

9. **Ken French's library documentation — not consulted in this lane.** It was J3's target and
   I did not duplicate it; I also did not check whether it states anything about entry, exit or
   gaps. If it does, this brief misses it.

10. **I verified no claim against the programme's own fixture, loader, or any market data, and
    the question that created this lane remains unanswered.** Whether *this* panel preserves a
    missing session, NaNs it, or fills it is a two-line check on the programme's own data that
    **nobody has run**, and no amount of external evidence substitutes for it. The practical
    value of this brief is that it tells you what to look for: **a row that exists with
    `volume = 0`, a price equal to the previous close, a return of exactly `0.0` on a day the
    name did not trade, and whether the gap-spanning return is labelled one bar or many.**

---

## What this file does not claim

Nothing here is a measurement of any market. No strategy is implied, nothing is closed and
nothing is admitted — that remains the principal's call under R15. Both books are unchanged.
Every convention reported is the convention of the source named beside it and of nothing else;
where a source is silent I have said it is silent rather than inferring what would be
sensible. **The one recommendation-shaped sentence in this brief is §3.4's observation that
Corwin–Schultz's own reference code fabricates a high and a low on a no-trade day, and it is a
report of what the code does, not advice about what to do with it.**
