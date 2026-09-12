# H6 — Block length and the choice of resampling scheme

**Round 4, lane H6. External evidence only.** I have no access to this programme's files, fixtures
or numbers and claim nothing about them. Every quantity below is either transcribed from a source I
read, or computed by me from a formula I read, on **synthetic** series. Where I ran the published
selector, I ran it on simulated data of the stated sample size — never on anything of this
programme's.

**The lane's bar, as commissioned:** name the kill number. *Would a data-driven block length differ
materially from 20 at the serial dependence of daily equity returns?*

---

## HEADLINE — THE KILL NUMBER, AND IT SPLITS

The answer is **not** "20 is fine", and it is **not** "20 is wrong". It is that **20 is the right
answer to a question nobody in this programme asked**, and which of the two real cases you are in
depends entirely on *which series is being resampled* — the distinction the commission asked me to
be precise about.

I derived a closed form from the equations I read, **verified it reproduces the paper's own
published table to two decimals in five of six cells**, and then ran the reference implementation's
actual algorithm on synthetic series at this programme's sample size (N = 4,190).

| the series actually being resampled | Politis–White/PPW b̂ for the **circular** block bootstrap, N = 4,190 |
|---|---|
| i.i.d. white noise | median **1.3** (p10–p90: 0.5–2.7) |
| GARCH(1,1) **returns** — white mean, persistent vol | median **1.5** (0.6–3.0) |
| AR(1) ρ = 0.05 | median **3.6** |
| AR(1) ρ = 0.10 | median **6.3** |
| AR(1) ρ = 0.20 | median **9.8** |
| **AR(1) ρ = 0.45** | median **19.2** ← *this is what b = 20 is optimal for* |
| GARCH(1,1) **squared** returns | median **132** |
| AR(1) ρ = 0.95 (a slow conditioner) | median **112** (theory says 134) |
| product of two independent AR(1) ρ = 0.98 (a correlation of two slow conditioners) | median **119** (theory says 157) |

**Read that table as two findings, not one.**

1. **For a per-bar book-return series or a per-trade mean, the inherited 20 is roughly 5–15× too
   long.** The selector wants **1 to 4**. To justify 20 you would need a first-order autocorrelation
   of **ρ ≈ 0.45** in the resampled series (exact: b_CB = 20 ⟺ ρ = 0.4499 at N = 4,190; b_CB = 21 ⟺
   ρ = 0.4718). Nothing in daily single-name equity returns is remotely near 0.45.
   **But this direction of error is the harmless one, and I say so plainly in §1.4**: the bias term
   is −G/b, so *too-long blocks reduce bias and only inflate variance*. Concretely, at b = 20 the
   long-run-variance estimate carries a relative sd of √(4b/3N) = **8.0%**, versus **3.6%** at
   b = 4 — so the standard error you bootstrap is noisy to about **4%** instead of **1.8%**. That is
   a real cost and a small one. **On this half, the honest verdict is: the inherited choice is
   defensible, wasteful, and not worth a study.**

2. **For any statistic whose summand is persistent — a correlation of slow-moving conditioning
   variables, or anything volatility-driven — the inherited 20 is 5–8× too SHORT, and this
   direction of error is the dangerous one.** Too-short blocks make the bias term −G/b large and
   *negative*, i.e. they **understate** the long-run variance, giving intervals that are too narrow
   and nulls that are too easy to beat. The same GARCH return path that asks for b̂ = 1.5 when you
   bootstrap its mean asks for **b̂ = 132** when you bootstrap the mean of its squares. That is the
   whole "selector tuned on returns vs. on the statistic" distinction, in one row of a table.

**And the third finding, which I did not expect and which outranks both:** at ρ ≥ 0.95 the
*selector itself breaks down at this sample size*, and both reference implementations break it the
same way and silently. See §1.5 and §6. There is also a hard theoretical wall: Politis–White
Theorem 3.1 assumes **b = o(N^(1/2))**, and √4,190 = **64.7**. A b̂ of 112 or 132 is outside the
regime in which the selector's own optimality is proved. **For the persistent-conditioner
statistics, the right conclusion is not "use a longer block" — it is that the block bootstrap has
run out of sample.**

**What I would tell the principal in one sentence:** the block length was never the problem on the
return-side statistics and the sensitivity study there would return "no material difference";
the problem is that *the same 20* is being carried onto persistent-summand statistics where it is
too short by a factor of six, and where the fix is not a better b but a different scheme (§3).

---

## 0. What I read, how, and how well

The commission's summariser rule was binding here and I honoured it: **every formula stated below
was extracted from the PDF locally with `pypdf` and read as text.** WebFetch's summariser returned
its "this is binary/encoded data" refusal on five of the six PDFs; in each case the bytes were on
disk and `pypdf` read them without difficulty. **No formula in this brief passed through a
summariser.** The one exception is flagged in §6 and was then independently confirmed against
source code.

| artefact | how obtained | type | established |
|---|---|---|---|
| Patton, Politis & White (2009), *Correction to "Automatic Block-Length Selection…"*, Econometric Reviews 28(4):372–375 — [PDF](https://public.econ.duke.edu/~ap172/Patton_Politis_White_2009.pdf) | WebFetch → PDF on disk → `pypdf` | [PEER-REVIEWED] | **[read in full]** — all 4 pages, incl. corrected Tables 1–4 |
| Politis & White (2004), *Automatic Block-Length Selection for the Dependent Bootstrap*, Econometric Reviews 23(1):53–70 — [PDF](https://public.econ.duke.edu/~ap172/Politis_White_2004.pdf) | WebFetch → PDF on disk → `pypdf` | [PEER-REVIEWED] | **[read in full]** for §§1–4 (pp. 53–62), incl. Theorem 3.1, Lemma 3.1, eqs (1)–(15), the flat-top window, the footnote-c bandwidth rule and Theorems 3.2/3.3. Appendix proofs skimmed. |
| Nordman (2008/2009), *A Note on the Stationary Bootstrap's Variance*, Ann. Statist. 37(1):359–370 — [PDF](https://projecteuclid.org/journals/annals-of-statistics/volume-37/issue-1/A-note-on-the-stationary-bootstraps-variance/10.1214/07-AOS567.pdf) | WebFetch → PDF on disk → `pypdf` | [PEER-REVIEWED] | **[read in full]** for §§1–2 and Remarks 1–4 (pp. 359–364) |
| Phipson & Smyth (2010), *Permutation P-values Should Never Be Zero*, SAGMB 9(1) art. 39 — [arXiv PDF](https://arxiv.org/pdf/1603.05766) | WebFetch → PDF on disk → `pypdf` | [PEER-REVIEWED] | **[read in full]** for §§1–6.1, incl. the size formula and both p-value formulas |
| Hemerik & Goeman (2018), *Exact testing with random permutations*, TEST 27(4):811–825 — [arXiv PDF](https://arxiv.org/pdf/1411.7565) | WebFetch → PDF on disk → `pypdf` | [PEER-REVIEWED] | **[read in full]** for §§1–3.3, incl. Definition 1, Theorem 1 + both proofs, Condition 1, Proposition 1, Definition 2, Theorem 2 |
| `arch.bootstrap.optimal_block_length` and `_single_optimal_block` — [source](https://raw.githubusercontent.com/bashtage/arch/main/arch/bootstrap/base.py) | WebFetch of raw `.py` (not a PDF; returned verbatim in a code block) | [SOFTWARE DOC] | **[read in full]** — both functions, every line |
| `np::b.star` R documentation — [search.r-project.org](http://search.r-project.org/library/np/html/b.star.html) | WebFetch | [SOFTWARE DOC] | **[read in full]** — arguments and defaults |
| Schmidheiny, *Clustering in the Linear Model* (Short Guides to Microeconometrics, Fall 2025) — [PDF](https://www.schmidheiny.name/teaching/clustering.pdf) | WebFetch → PDF on disk → `pypdf` | [UNVERIFIED] teaching note, not peer-reviewed | **[read in full]** for §§1–5, incl. the Moulton equicorrelated error structure |
| Lahiri (1999), *Theoretical comparisons of block bootstrap methods*, Ann. Statist. 27:386–404 | not fetched | [PEER-REVIEWED] | **[abstract only]** — and see the warning in §2.1: its stationary-bootstrap result is **wrong** and superseded |
| Petersen (2009 RFS), Thompson (2011 JFE), Cameron–Gelbach–Miller (2008, 2011), Moulton (1990), Driscoll–Kraay (1998), Jöckel (1986), Andrews & Buchinsky (2000), Künsch (1989), Politis & Romano (1992, 1994), Langsrud (2005), Southworth et al. (2009), Lahiri (1993, 1995) | WebSearch result text only | mixed [PEER-REVIEWED] | **[snippet only]** — cited for existence and headline claim, **no formula from any of these is stated as read** |

**My own computation, and how to check it.** Scripts are in the session scratchpad
(`pwsel.py`, `q95.py`, `trunc.py`); they use only the venv's numpy. `pwsel.py` is a line-for-line
transcription of `arch`'s `_single_optimal_block` (which I read in full) plus synthetic generators.
Nothing there touches this programme's data.

**Nothing addressed to me was found in any source.** No page, PDF or search result contained text
directed at the reader-as-agent, instructions to take an action, or claims of authority. I
downloaded nothing deliberately: the PDFs are WebFetch's own on-disk cache, which the commission
explicitly identified as the route to take.

---

## 1. Data-driven block-length selection: what the selector actually is

### 1.1 The formulas, as read

Politis & White (2004), Theorem 3.1 (attributed to Lahiri 1999), for a stationary series with
autocovariance R(s) and spectral density g(w) := Σ_s R(s)·cos(ws):

- Bias(σ̂²_{b,CB}) = −G/b + o(1/b)   — eq. (2); **the same for MB (footnote d) and SB (eq. 4)**
- Var(σ̂²_{b,CB}) = (b/N)·D_CB + o(b/N)  — eq. (3)
- **G = Σ_{k=−∞}^{∞} |k|·R(k)**
- **D_CB = (4/3)·g²(0)**
- D_SB — *as originally printed* — = 4g²(0) + (2/π)∫(1+cos w)g²(w)dw

**PPW (2009) corrects exactly one thing, and it matters:** "*The correct value for the variance
constant D_SB defined in Theorem 3.1 of Politis and White (2004) is D_SB = 2g²(0)*". Nordman (2008)
states the same correction from the other side: `D_SB ≡ (3/2)·D_CBB`, and 2/(4/3) = 3/2. ✓

The optimal block lengths, eqs (6) and (11):

    b_opt,SB = (2G² / D_SB)^(1/3) · N^(1/3)
    b_opt,CB = [ (2G² / D_CB)^(1/3) · N^(1/3) ]        [·] = nearest integer

With the corrected D_SB these collapse to a form I can evaluate by hand:

    b_opt,SB = |G / g(0)|^(2/3) · N^(1/3)
    b_opt,CB = (3/2)^(1/3) · b_opt,SB  =  1.1447 · b_opt,SB

**Nordman (2008) Remark 3 states the same constant independently** — "*Theorem 1 yields the optimal
constant as C = |G/{2πf(0)}|^(2/3)*" — and 2πf(0) = g(0) under his Fourier convention. Nordman
Remark 3 also states `ℓ̂_SB = (2/3)^(1/3)·ℓ̂_CBB`, which is the same 1.1447 ratio inverted. Three
sources, read directly, agreeing.

**PPW's corrected estimator, eqs (8)–(9) + (13)–(14),** plugs in a **flat-top lag-window** estimate:

    λ(t) = 1 for |t| ∈ [0, ½];  2(1−|t|) for |t| ∈ [½, 1];  0 otherwise
    Ĝ   = Σ_{k=−M}^{M} λ(k/M)·|k|·R̂(k)
    ĝ(w)= Σ_{k=−M}^{M} λ(k/M)·R̂(k)·cos(wk)
    D̂_SB = 2ĝ²(0)   [corrected]        D̂_CB = (4/3)·ĝ²(0)

**and the bandwidth M is not free** — PW footnote c, p. 59, which I read: let m̂ be the smallest
positive integer with |ρ̂(m̂+k)| < c·√(log N / N) for k = 1,…,K_N, with **c = 2**, **K_N = max(5,
√(log₁₀ N))**, then **M = 2m̂**.

### 1.2 The closed form for AR(1), and the check that it is right

For AR(1) with parameter ρ: G/g(0) = 2ρ/(1−ρ²), so

    b_opt,SB = |2ρ/(1−ρ²)|^(2/3) · N^(1/3)

I evaluated this against PPW (2009) **Table 1**, which I read:

| | paper b_SB | mine | paper b_CB | mine |
|---|---|---|---|---|
| ρ=0.7, N=200 | 11.47 | **11.47** | [13.12] | 13.12 |
| ρ=0.7, N=800 | 18.20 | **18.20** | [20.83] | 20.83 |
| ρ=0.1, N=200 | 2.01 | **2.01** | [2.31] | 2.30 |
| ρ=0.1, N=800 | 3.20 | **3.20** | [3.66] | 3.66 |
| ρ=−0.4, N=200 | 5.66 | **5.66** | [6.48] | 6.48 |
| ρ=−0.4, N=800 | 8.99 | **8.99** | [10.23] | **10.29** |

Five of six b_CB cells match exactly and all six b_SB cells match exactly. **The last cell is off by
0.06 and I could not reconcile it**: 8.99 × 1.14471 = 10.29, not 10.23, and the same ratio is right
in the other five rows. I record it as an unexplained discrepancy in the published table rather than
pretending it away. It does not affect anything here.

**Note the sign asymmetry, because it will matter in §1.4:** b_opt depends on |ρ| only. A series
with ρ = −0.05 and one with ρ = +0.05 get the **same** recommended block length — but the *bias they
suffer from getting it wrong points in opposite directions*.

### 1.3 The kill number, at this programme's N

N = 4,190 ⇒ N^(1/3) = 16.12.

| ρ of the resampled series | b_opt,SB | b_opt,CB |
|---:|---:|---:|
| 0.00 | 0 → 1 | 0 → 1 |
| 0.02 | 1.9 | 2.2 |
| 0.05 | 3.5 | 4.0 |
| 0.10 | 5.6 | 6.4 |
| 0.20 | 9.0 | 10.3 |
| 0.30 | 12.2 | 14.0 |
| **0.45** | 17.5 | **20.0** |
| 0.50 | 19.5 | 22.4 |
| 0.90 | 72.2 | 82.6 |
| 0.95 | 116.7 | 133.6 |

**b_CB = 20 ⟺ ρ = 0.4499. b_CB = 21 ⟺ ρ = 0.4718.** The one-bar difference between the two decision
records' 20 and 21 corresponds to a difference of **0.022 in assumed first-order autocorrelation** —
i.e. the two records are, in the selector's currency, the same number, and neither is a number about
daily equity returns.

Note also that b_opt scales as **N^(1/3)**. If the fixture grows from 4,190 bars to 8,380, the
optimal block grows only by 2^(1/3) = 1.26. **A block length inherited across fixtures of different
length is wrong by less than most people fear** — a 4× change in N moves b by 1.6×.

### 1.4 The direction of the error, which is the part that actually decides whether to care

From Theorem 3.1, which I read: **Bias(σ̂²_b) = −G/b**, and G = Σ|k|R(k).

- **Positively-dependent summand (G > 0):** too-short blocks **understate** σ²_∞ → intervals too
  narrow, nulls too easy to beat. Too-long blocks are the **conservative** error.
- **Negatively-dependent summand (G < 0):** the signs flip. Too-short blocks **overstate** σ²_∞.
  Daily single-name returns often carry small *negative* first-order autocorrelation (bid–ask
  bounce), so on a single-name return series a too-short block is conservative and a too-long block
  is conservative too (via reduced |bias|) — the choice is nearly free.

The cost of over-long b is pure variance, and it is computable from eq. (3) alone:

    relative sd of σ̂²_b,CB  =  √(4b / 3N)

| b | rel. sd of the variance estimate | ⇒ rel. sd of the *standard error* |
|---:|---:|---:|
| 1 | 1.8% | 0.9% |
| 4 | 3.6% | 1.8% |
| 20 | 8.0% | **4.0%** |
| 21 | 8.2% | 4.1% |
| 60 | 13.8% | 6.9% |

And the MSE penalty for using b = r·b_opt is exactly **(1/3)r⁻² + (2/3)r** (algebra from eqs (2)–(3)
and (7); at r = 1 it equals 1 ✓). At b = 20 against b_opt = 3.5, r = 5.7 and the penalty is **3.8×
MSE ≈ 1.95× RMSE** — but almost all of that is the variance term, which is the term that does not
bias a p-value.

**This is the "confirms an inherited choice" outcome the commission asked me to be willing to
report, and on the return-side statistics I report it.** A sensitivity study on b for a per-bar book
return or a per-trade mean would find the interval widening by a few percent and the conclusion
unchanged. **It is not worth a decision record.** The one thing worth doing is one line of code:
run the selector once, note it says 1–4, and record that 20 was retained deliberately as the
conservative side. That converts an inherited number into a chosen one for the cost of a minute.

### 1.5 Where the selector itself fails, and both implementations fail identically

The bandwidth M is capped in both reference implementations at **m_max = ⌈√N⌉ + K_N ≈ 70** at
N = 4,190. **That cap is not in Politis & White (2004)** — I read §§3–4 and Theorems 3.2/3.3 and
found no such cap; it is an implementation addition.

For a persistent series the cap truncates Ĝ = Σ λ(k/M)|k|R̂(k) before the sum has converged, because
|k|ρ^|k| peaks at k ≈ −1/ln ρ (k ≈ 50 at ρ = 0.98). Fraction of the true G captured at M = 70:

| ρ | Ĝ/G at M=70 | b̂/b_opt (b ∝ G^(2/3)) | b_opt,CB | b̂ predicted | b̂ observed (200 reps) |
|---:|---:|---:|---:|---:|---:|
| 0.05 | 1.000 | 1.000 | 4.0 | 4.0 | 3.6 |
| 0.50 | 1.000 | 1.000 | 22.4 | 22.4 | — |
| 0.90 | 0.963 | 0.975 | 82.6 | 80.6 | 74.9 |
| 0.95 | 0.735 | 0.814 | 133.6 | 108.8 | 112.4 |
| **0.98** | **0.286** | **0.434** | 248.8 | 108.0 | **142.9** |

The truncation prediction tracks the observed selector output. **At ρ = 0.98 the selector returns
roughly 55–60% of the block length its own theory calls for, and reports nothing.** In my runs the
median chosen M sat exactly at the cap (70) for every ρ ≥ 0.95 — the diagnostic is available and
free: **if M comes back at m_max, the selector did not converge and its b̂ is a lower bound.**

**And it does not matter, because the theory has already expired.** Theorem 3.1 assumes
`b = o(N^(1/2))` and √4,190 = 64.7. Both 108 and 249 are outside it. For AR(1) ρ = 0.98 the
effective sample size is N(1−ρ)/(1+ρ) = **42 independent observations** in 4,190 bars. **You cannot
block-bootstrap 42 effective observations into a usable interval, and no choice of b fixes that.**

### 1.6 Returns versus the statistic — the distinction, stated concretely

PW's theory is for the **sample mean of the series X_t that is being resampled**. Nordman Remark 1,
which I read, extends it to smooth functions H(Ȳ_n) of a multivariate mean — and states explicitly
that the relevant series is then **the linearising influence series** `X_t = H(μ) + c′(Y_t − μ)`
where c holds the first partial derivatives of H at μ. **So the correct input to the selector is not
returns. It is the summand of the statistic.**

Three cases, from the table in the headline:

- **Per-bar book returns** → the summand *is* the return. Near-white. **b̂ ≈ 1–4.**
- **A per-trade mean** → the summand is per-trade P&L in time order. Same regime unless the trades
  cluster; I have no external evidence on its autocorrelation and say so in §8.
- **A correlation between two slow-moving conditioners** → the summand is (x_t − x̄)(y_t − ȳ)-type.
  For two independent Gaussian AR(1)s with parameter ρ, the product series has autocorrelation
  **ρ^(2k)**, i.e. it behaves like an AR(1) with parameter **ρ²**. At ρ = 0.98 that is 0.9604, and
  b_opt,CB = **157**. My simulation of exactly this object returned a median b̂ of **119** — short of
  theory, for the truncation reason in §1.5, and **six times the inherited 20.**

**If one thing from this brief goes into a runner, make it this:** the selector must be fed the
summand of the statistic, not the return series, and the two answers differ by up to two orders of
magnitude on the same data.

---

## 2. Stationary vs. circular vs. moving-block

### 2.1 A warning about the literature itself, before any comparison

**Lahiri (1999) Ann. Statist. 27:386–404 contains an error in the stationary bootstrap's variance,
and every comparison built on it before 2008 is void.** Nordman (2009), which I read, is explicit:
"*This manuscript corrects the variance of the SB estimator, and thereby invalidates all prior
comparisons of ARE involving the SB as well as previous optimal block size calculations for SB.*"
He locates the error precisely — a sign, "(sin ω)²" where "−(sin ω)²" belongs, in lines (5) and (8)
of Lahiri's Lemma 5.3(i).

**Consequences for anyone reading the older literature:**

- Lahiri's headline that "random block lengths typically lead to larger MSE" — **which is what the
  search-result abstract for Lahiri (1999) still says today** — is wrong for the stationary
  bootstrap. Nordman: the SB "*surprisingly matches*" the variance of the *non-overlapping* block
  bootstrap, not something worse.
- **PW (2004) Lemma 3.1's bound `0.331 ≤ ARE_CB/SB ≤ 0.481` is superseded.** PPW (2009) replaces
  the whole lemma with a point value: **ARE_CB/SB = (2/3)^(2/3) ≈ 0.7631**.
- PW (2004)'s simulation Tables 1–4 are wrong and **PPW (2009) reprints all four**. Anyone citing
  a table from the 2004 paper is citing a retracted number.

**If any decision record in this programme cites Lahiri (1999) or Politis & White (2004) for a
number about the stationary bootstrap, that citation needs the 2008/2009 correction attached.** I
have no idea whether any does; I can only flag the hazard.

### 2.2 What actually differs

Transcribing the mechanism from PW (2004) §3.1, which I read: all three schemes wrap the data on a
circle, draw i.i.d. uniform starting points, and differ **only in the distribution F_b of block
length**.

| | block length | overlap | key property |
|---|---|---|---|
| **Moving block (MBB)** — Künsch (1989), Liu & Singh (1992) | fixed b | yes | σ̂²_MBB = (b/Q)Σ(X̄_{i,b} − X̄_N)², Q = N−b+1. Identical to the Bartlett spectral estimator at the origin, to full-overlap subsampling, and to overlapping batch means — **PW list all four names for the same estimator.** |
| **Circular (CBB)** — Politis & Romano (1992) | fixed b | yes, wrapped | Same first-order bias *and* variance as MBB (PW footnote d, read). **b_opt,MB ≡ b_opt,CB**, and PW state explicitly that b̂_opt,CB "*can be considered to be an estimator of the optimal block size for the moving blocks bootstrap as well*". |
| **Stationary (SB)** — Politis & Romano (1994) | Geometric, mean b | yes, wrapped | Bootstrap paths are **stationary**. Costs 24% in MSE efficiency (ARE 0.7631). |

**So the CBB-vs-MBB choice is, to first order, not a choice at all** — same bias, same variance,
same optimal b. The documented difference is the edge effect: the MBB's implied weighting
under-weights observations near the two ends, and wrapping removes it. **I have this at [snippet
only]** from search-result text; PW (2004) §3.1 as I read it describes the wrapping step for all
schemes without spelling out the edge-effect argument, and I did not read Politis & Romano (1992).

**The CBB-vs-SB choice is a real trade with a measured price:**

- **Cost of SB:** asymptotically **ARE_CB/SB = 0.7631**, i.e. the SB's optimal MSE is ~31% larger.
  PPW's corrected Table 4 (read) puts the *finite-sample attainable* relative efficiency at
  0.82–0.87 for ρ = 0.7 and 0.63–0.69 for ρ = −0.4 at N = 200–800.
- **Benefit of SB:** "*the SB method is less sensitive to block size misspecification as compared to
  CB and/or the moving blocks bootstrap*" (PW §3, read, citing Politis & Romano 1994), and its
  resampled paths are stationary.

**Which reads directly onto this programme's situation.** If a block length is going to be
inherited rather than selected — which is the premise of this lane — then **robustness to
misspecifying it is worth more than 24% of variance efficiency.** The stationary bootstrap is the
scheme that forgives an inherited b. That is a real, cheap improvement available today, and it does
not require choosing b at all well.

### 2.3 Documented failure modes

Each of these is **[snippet only]**; I read none of the cited papers and state no formula from them.

- **Long memory.** Lahiri (1993) is cited as the first analysis of the MBB under long memory, with
  validity only where the normalised sample mean is asymptotically normal; Hall, Jing & Lahiri
  (1998) developed subsampling for transformed-Gaussian cases where the MBB is **invalid**. The
  mechanism given in the secondary sources is that independent blocks cannot reproduce dependence
  between far-apart observations. *Relevance here: a conditioning variable at ρ = 0.98 over 4,190
  bars is empirically indistinguishable from long memory at this N.*
- **Heavy tails.** Lahiri (1995) is cited on MBB behaviour for normalised sums of heavy-tailed
  variables. *Relevance: a two-sided fat-tailed trade book.*
- **Non-smooth statistics.** All the theory above is for the sample mean and for smooth functions of
  means (Nordman Remark 1, read). **A maximum, a quantile, a drawdown, or a "names to reach half
  the P&L" count is none of those**, and nothing I read licenses a block bootstrap for them.
- **All three schemes require b/N → 0 and b → ∞.** Nordman's A.3 is stronger still: `ℓ·log n / n →
  0`. At N = 4,190 that is comfortable at b = 20 and uncomfortable at b = 130.

---

## 3. When a block bootstrap is the wrong scheme, and a group is right

This is the strongest section of the brief, because the literature is exact where the block
bootstrap is only asymptotic — and because it lets me state this programme's own 26-offset finding
as a theorem rather than an observation.

### 3.1 The group-invariance framework

Hemerik & Goeman (2018), read in full. Let G be a **finite group** of transformations g : 𝒳 → 𝒳
(identity present, inverses present, closed under composition). The null H_p is any hypothesis
implying that the joint distribution of {T(gX) : g ∈ G} is invariant under every g ∈ G — which holds
in particular when **X =ᵈ gX** for all g ∈ G.

**Theorem 1 (read, with both proofs):** sort T(gX) over g ∈ G as T^(1) ≤ … ≤ T^(#G) and reject when
T(X) > T^(k) with **k = ⌈(1−α)·#G⌉**. Then under H_p, **P{reject} ≤ α**. Exactly. In finite samples.
No mixing condition, no b, no N → ∞.

**The group structure is load-bearing, and its absence is not a technicality.** The proof turns on
`Gg = G` for all g ∈ G. Hemerik & Goeman: "*When the set G is not a group, the test can be highly
anti-conservative or conservative*", citing Southworth et al. (2009) on "balanced permutations",
which "*is not a subgroup*" and yields anti-conservative tests. **Check that whatever this programme
rotates or permutes is closed under composition and contains the identity.** A circular shift by
integer offsets on a length-T series is the cyclic group ℤ_T — fine. An offset set that excludes
small offsets, or excludes the identity, or is drawn subject to a constraint, **is not a group and
the exactness is gone.**

**Rotations are explicitly in scope.** Hemerik & Goeman name Langsrud (2005) for rotation groups
alongside permutations and sign-flips.

### 3.2 The granularity floor, exactly

Phipson & Smyth (2010), read in full. For an exhaustive enumeration the p-value is

    p_t = (b_t + 1) / (m_t + 1)

where m_t is the number of distinct non-identity statistic values and b_t the number exceeding the
observation. **With a group of #G = G elements including the identity, m_t = G − 1 and the smallest
attainable p-value is exactly 1/G.** For a randomly-drawn subset of m transformations (identity
included), the exact p-value is

    p_u = (b + 1) / (m + 1)

and the naive B/m is "*understated by about 1/m*", with size **P(p̂ ≤ α) = (⌊mα⌋ + 1)/(m + 1)**,
which "*is never less than 1/(m+1) regardless of how stringent the desired rate α is chosen*".

Hemerik & Goeman's Proposition 1 sharpens this from the other direction: under their Condition 1 the
group test is exact **if and only if α ∈ {0, 1/m, 2/m, …, (m−1)/m}**. So α = 0.05 is generally not
an attainable level, and the test at nominal 0.05 silently runs at the largest attainable level
below it.

**Now the programme's own case, made exact.** With a rotation group of **G = 26**:

| α | k = ⌈(1−α)·26⌉ | rejects when | actual size |
|---:|---:|---|---:|
| 0.05 | 25 | T(X) is the **strict maximum** of all 26 | **1/26 = 0.0385** |
| 0.01 | 26 | T(X) > max(all 26), **impossible** | **0** |

**So the programme's finding is not "26 offsets is too few draws" — it is that at α = 0.01 the test
has power identically zero for every alternative, however large, and at α = 0.05 the strongest
possible evidence the experiment can produce is p = 0.0385.** That is a property of #G alone. It is
in Phipson & Smyth's exhaustive formula and in Hemerik & Goeman's Proposition 1, and **increasing
the number of draws cannot touch it, because there are only 26 things to draw.** The programme
reached this independently; the literature agrees and gives the closed form.

For contrast, the enumerable time rotation of a single market-level series over ~4,190 offsets has
min p = **1/4,190 = 2.4 × 10⁻⁴** — no granularity problem whatever.

### 3.3 Random draws from a large group are exact, which is the good news

**Hemerik & Goeman Theorem 2 (read):** let G′ = (id, g₂, …, g_w) with g₂…g_w drawn uniformly from G
(with **or** without replacement), k′ = ⌈(1−α)w⌉. Reject when T(X) > T^(k′)(X, G′). Then the
rejection probability under H_p is **at most α**. Exactly, for any w — including w = 26 or w = 200.

**Two things follow directly for the per-name rotations this programme says are not enumerable.**

1. **They do not need to be enumerable.** The product group (ℤ_T)^N is a group; its order is
   astronomically large; drawing w of its elements uniformly and using p = (b+1)/(w+1) is **exact**,
   not approximate. The granularity floor is 1/(w+1), set by *draws*, not by the group. **There is
   no bias to carry here** — which is a materially better position than the "the bias stands and
   only more draws touch it" framing the commission described.
2. **The identity must be in the list.** Hemerik & Goeman fix g₁ = id, "*reflecting the original
   observation*"; Phipson & Smyth show that omitting it makes the naive p̂ "*almost never
   stochastically larger than uniform*" and note that "*appreciable anti-conservativeness also
   occurs if very few (e.g. 25–100) random permutations are used*". **A runner that computes
   `mean(null >= observed)` over w draws is running the anti-conservative estimator, not the exact
   test.** `(1 + count) / (1 + w)` is the whole fix and it costs nothing.

### 3.4 The one hazard in a rotation null that nobody's arithmetic will catch

Exactness requires the null to actually imply invariance under **every** g ∈ G. For a circular shift
on a real time series, that is the assumption that the series is **circularly** stationary — i.e.
that joining bar 4,190 to bar 1 is as legitimate as any other adjacency. It is not: exactly one seam
per rotation is a splice between 2026 and 2010. For a Gaussian AR(1), a genuine adjacent step has sd
√(2(1−ρ)) in unconditional-sd units while the seam step has sd √2, so the seam is:

| ρ | sd of a real adjacent step | sd of the seam step | ratio |
|---:|---:|---:|---:|
| 0.05 | 1.378 | 1.414 | **1.0×** — invisible |
| 0.50 | 1.000 | 1.414 | 1.4× |
| 0.90 | 0.447 | 1.414 | 3.2× |
| 0.98 | 0.200 | 1.414 | **7.1×** |

It is present in **every** rotation, so it does not cancel — for a persistent series it shifts the
whole null distribution. **Near-white series are immune; the same slow-moving conditioners that
broke the block-length selector in §1.5 break the rotation null too, and for the same underlying
reason — 4,190 bars is not many bars when ρ = 0.98.**

**This is the same failure the programme's own memory already records under a different name**
(a null whose events do not satisfy the observed events' eligibility). I did not find a paper
addressing the circular seam for rotation tests specifically, and I flag that in §8.

### 3.5 So when is a block bootstrap wrong and a group right?

| the question being asked | scheme |
|---|---|
| "how uncertain is this estimate?" — a standard error, a confidence interval | **block bootstrap.** A group has no answer; it tests a null, it does not build an interval. |
| "could this have arisen under a null with a stated invariance?" — and the invariance is a genuine group | **group test.** Exact in finite samples; no b to choose; no mixing condition; no `b = o(√N)` wall. |
| the statistic is a max, a quantile, a drawdown, a count | **neither, without more work.** The block bootstrap theory read here covers the sample mean and smooth functions of means, and no more. |
| the effective sample is ~40 observations (a ρ=0.98 conditioner) | **neither.** Report the effective sample size and stop. |

**The practical point for this programme:** on any statistic where a genuine invariance null exists,
the group test is *strictly better* than the block bootstrap — exact rather than asymptotic, and
free of the entire block-length question this lane was commissioned about. **The right response to
"we never chose b from the data" may be to need b less often.**

---

## 4. Cross-sectional dependence

**Weakest section in the brief; treat accordingly.** I read one teaching handout in full and
everything else at snippet level.

### 4.1 The arithmetic that reproduces the programme's own ~10

Schmidheiny §3 (read) gives Moulton's (1986) equicorrelated structure verbatim:
`V[u_g|X_g] = σ²_u[ρ_u ιι′ + (1−ρ)I]`, i.e. unit variance and common pairwise correlation ρ_u within
a cluster. From that structure — elementary algebra, not a quotation — the variance of a cluster
mean of M equicorrelated variables is (σ²/M)[1 + (M−1)ρ], so the **effective number of independent
observations** is

    n_eff = M / [1 + (M − 1)ρ̄]

At M = 1,573 names: **ρ̄ = 0.0994 gives n_eff = 10.0.** So the programme's "~10 effective
independent instruments across 1,573 names" is exactly what a mean pairwise daily return
correlation of **0.10** implies. That is a plausible number for a broad US equity cross-section and
the two figures are mutually consistent — a useful cross-check on their own estimate, though it is
consistency, not confirmation.

The design-effect formula `1 + (n−1)ρ` itself I have **[snippet only]**, attributed to Moulton
(1990) and the survey-sampling design-effect literature.

### 4.2 What the clustering literature says, at snippet level

- **Petersen (2009, RFS 22(1):435–480)** [snippet only] — the canonical finance-panel treatment;
  reported recommendation is that with more firms than years, absorb the time effect with year
  dummies and cluster by firm; with few clusters in one dimension, clustering on the more frequent
  dimension is nearly identical to two-way.
- **Thompson (2011, JFE 99:1–10)** [snippet only] — "simple formulas" for clustering by both firm
  and time; reported as arguing that with far more firms than periods, **clustering by time removes
  most of the bias** unless within-firm correlation greatly exceeds within-time correlation.
- **Cameron, Gelbach & Miller (2008, 2011)** [snippet only] — two-way clustering, and the wild
  cluster bootstrap; asymptotics run in the **number of clusters**, and standard tests over-reject
  with roughly **5–30** clusters.

**The one thing that transfers cleanly, and it is the important one.** In this framework, a panel of
1,573 names × 4,190 bars clustered by time is **4,190 clusters** — plentiful. The dangerous
dimension is never the number of names. And **a block bootstrap over bars, resampling entire
cross-sections as units, is already doing the "cluster by time" job**: it preserves within-bar
cross-sectional dependence exactly, because the bar moves as a unit. So the block bootstrap this
programme already runs is, if it resamples whole bars, the right treatment for cross-sectional
dependence — provided it resamples **whole bars** and not name-bar cells.

**That is a check worth running and I cannot run it:** does the resampling unit contain the entire
cross-section of a bar, or does it draw within-bar? If the latter, the ~10 effective instruments
becomes ~1,573 by accident and every interval is roughly √157 ≈ 12.5× too narrow. I have no
knowledge of which it is.

---

## 5. The p95's bias and standard error at B draws

The commission asked what the literature says about the bias, not for a re-derivation of the
programme's rule. **The honest report is that the literature's headline result points the other way
from the premise, and that a second, separate effect rescues the premise for the conventions people
actually use.** I verified this numerically rather than taking either side on faith.

### 5.1 Three distinct effects, routinely conflated

1. **The Monte-Carlo p-value bias — real, well documented, and in the "too lenient" direction.**
   Phipson & Smyth (read in full): p̂ = B/m is "*understated by about 1/m*", and the resulting test
   has size (⌊mα⌋+1)/(m+1) > α for essentially all small α. **This is the published result that
   supports the programme's concern**, and it is about *p-values*, not about quantiles.
2. **The second-order bias of a sample quantile — points the WRONG way for a normal null.** The
   classical order-statistic expansion has bias ∝ Q''(p)·p(1−p)/(2(B+2)), and Q''(0.95) > 0 for the
   normal, so the (B+1)-plotting-position p95 is biased **upward** — *away* from the centre, i.e.
   conservative. Evaluating it: Q''(0.95) = z/φ(z)² = +154.6, giving a predicted bias of
   **+3.67/(B+2) = +0.0182 sd at B = 200**. **The measurement in §5.2 returns +0.0182 for exactly
   that convention**, so the expansion and the simulation agree and the direction is not in doubt.
3. **The plotting-position/convention effect — points the right way and dominates (2).** Taking the
   ⌈0.95B⌉-th order statistic of B draws targets p = ⌈0.95B⌉/(B+1) ≈ 0.9453 at B = 200, not 0.95.

### 5.2 What I measured

Monte Carlo, standard normal null, true p95 = 1.644854, 200,000 replications per cell
(40,000 at B = 10,000); script `q95.py`:

| B | convention | mean | **bias (sd units)** | **sd (sd units)** |
|---:|---|---:|---:|---:|
| 200 | numpy default (`linear`) | 1.6196 | **−0.0252** | **0.1455** |
| 200 | ⌈0.95B⌉-th order statistic | 1.6172 | **−0.0276** | 0.1456 |
| 200 | Weibull, (B+1) position | 1.6630 | **+0.0182** | 0.1498 |
| 500 | numpy default | 1.6347 | −0.0101 | 0.0937 |
| 1,000 | numpy default | 1.6397 | −0.0052 | 0.0666 |
| 2,000 | numpy default | 1.6423 | −0.0026 | 0.0470 |
| 10,000 | numpy default | 1.6443 | −0.0006 | 0.0213 |

On a right-skewed null (exp(N(0,1))) the picture is the same in direction: at B = 200 the default
convention's bias is **−0.033 sd** with sd **0.35 sd**.

The asymptotic formula agrees: SE(q̂_p) = √(p(1−p)/B)/f(q_p), which for the normal p95 gives
**2.113/√B** — 0.149 at B = 200, against the measured 0.146.

### 5.3 The verdict

**The programme's premise is correct for the two conventions anyone actually uses** — `numpy`'s
default `np.quantile(..., 0.95)` and the ⌈0.95B⌉-th order statistic are both biased **toward the
centre**, by about **0.026 sd of the null at B = 200**. It becomes *anti*-conservative only if you
switch to the (B+1) plotting position, which almost nobody does.

**But the bias is the smaller problem by a factor of 5.6.** At B = 200 the p95's **sd is 0.146 sd of
the null** and its bias is 0.026. So a rule that carries 2 SE is carrying ±0.29 sd, and the bias
adds a further 0.18 SE on the conservative side. **The programme's 2-SE rule is the right rule and
it is right for the variance reason, not the bias reason** — and it is roughly 18% more conservative
than it advertises, which is a fine direction to be wrong in.

**Precision as a function of B**, for the normal p95, in sd units of the null:

| B | SE(p̂95) | B needed for that SE |
|---:|---:|---|
| 200 | 0.146 | — |
| 500 | 0.094 | — |
| 1,000 | 0.067 | SE = 0.10 sd → **B ≈ 450** |
| 2,000 | 0.047 | SE = 0.05 sd → **B ≈ 1,790** |
| 10,000 | 0.021 | SE = 0.02 sd → **B ≈ 11,200** |

**So the honest cost of resolving a marginal cell is: going from 200 to 2,000 draws (10× the
compute) buys a 3.1× tighter p95.** The √B wall is the whole story; there is no cheaper route
through it except exhaustive enumeration where the group permits, which the programme has already
discovered.

Two published anchors for choosing B, both **[snippet only]** — I read neither and state no formula
from them: **Andrews & Buchinsky (2000, Econometrica 68(1):23–51)**, a three-step method for
choosing B to a specified accuracy for standard errors, intervals, tests and p-values; and **Jöckel
(1986, Ann. Statist. 14(1):336–347)**, on the finite-sample power loss of a Monte Carlo test as a
function of the number of replications. **Jöckel is the reference that most directly names the
thing the programme is worried about** — that a finite-draw null is less powerful than an infinite
one — and it is the one I would read next.

---

## 6. Reference implementations, and where they disagree

**They exist, they implement the corrected 2009 formula, and they disagree with each other and with
the paper on tuning constants.** Nobody documents the disagreement.

`arch` (Python) — I read `optimal_block_length` and `_single_optimal_block` in full from source.
The docstring's formula came back through WebFetch first, and I then confirmed it line-for-line
against the code, so it is **not** a summariser figure:

```
b_max = ceil(min(3*sqrt(n), n/3))
kn    = max(5, int(log10(n)))
m_max = ceil(sqrt(n)) + kn
cv    = 2 * sqrt(log10(n) / n)
...   m = 2 * max(opt_m, 1);  m = min(m, m_max)
d_sb  = 2   * lr_acv**2        # <- the CORRECTED D_SB
d_cb  = 4/3 * lr_acv**2
b_sb  = ((2*g**2)/d_sb)**(1/3) * nobs**(1/3);  b_sb = min(b_sb, b_max)
```

**This matches PW eqs (6)/(11) with the PPW (2009) correction applied. The implementation is
faithful to the paper's mathematics.** Three deviations, none of them in the paper:

| | PW (2004), as read | `arch` | `np::b.star` (R) |
|---|---|---|---|
| band constant c | **2** | 2 | **qnorm(0.975) = 1.96** |
| K_N | **max(5, √(log₁₀ N))** = 5 at N=4,190 | `max(5, int(log10 n))` = **5** | `ceiling(log10(n))` = **4** |
| cap on M | **none stated** | `⌈√n⌉ + kn` = **70** | `ceiling(sqrt(n)) + Kn` = **69** |
| cap on b | **none stated** | `⌈min(3√n, n/3)⌉` = **195** | `ceiling(min(3*sqrt(n), n/3))` = **195** |

And `arch` warns in its own docstring, verbatim: "*The block lengths do not match this
implementation since the autocovariances and autocorrelations are all computed using the maximum
sample length rather than a common sampling length*" — referring to Patton's MATLAB program, the
authors' own reference code. **So the three implementations of one algorithm are known by their
maintainers to return different numbers.** Also available: R's `blocklength::pwsd`, and Patton's
original MATLAB (the URL in PW 2004 is dead; PPW 2009 gives
`economics.ox.ac.uk/members/andrew.patton/code.html`, which I did not fetch).

**How much does the disagreement matter?** At the low-ρ end where daily returns live, not at all —
K_N = 4 vs 5 and c = 1.96 vs 2 both move m̂ by at most a lag, and b is 1–4 either way. At the
high-ρ end it is swamped by the m_max truncation both share. **So: the implementations disagree,
the disagreement is undocumented, and it is not the thing that will hurt you.** The m_max cap is.

---

## 7. What did NOT clear the bar, kept visible so nobody re-researches it

- **The claim that the SB "has the largest variance among block bootstraps."** Widely repeated,
  still in the abstract text returned for Lahiri (1999). **False** — Nordman (2008). Do not use.
- **Any pre-2009 ARE number for SB vs CB**, including PW (2004)'s own Lemma 3.1 bound of
  [0.331, 0.481] and all four of PW (2004)'s simulation tables. Superseded.
- **A modern, verified figure for the daily first-order autocorrelation of an equal-weighted US
  equity portfolio return.** I tried and could not get one I would stand behind — see §8.1. This
  matters because it is the single input that would settle whether b̂ for a book-return series is 1
  or 8.
- **A "block bootstrap for finance" tutorial with a recommended default.** Several exist; none I
  found grounds a default in anything but precedent, which is the exact failure mode this lane was
  commissioned to examine. Nothing worth citing.
- **Two-way clustered *bootstrap* schemes for panels.** They exist (multiway wild bootstrap); I did
  not establish any of it well enough to write down, and the "resample whole bars" observation in
  §4.2 makes it largely moot for this programme's object.

---

## 8. What I could not verify, stated plainly

1. **The daily first-order autocorrelation of any series this programme actually resamples.** I have
   no access to their data and I could not find a modern, citable figure for the daily
   autocorrelation of an equal-weighted US equity book over 2010–2026. What I did find, at
   **[snippet only]**, is contradictory and mostly historical: one source reports index daily
   autocorrelation "significantly positive until the end of the 1990s, switched to significantly
   negative since the early 2000s"; another reports nonsynchronous trading inducing a **negative**
   lag-1 autocorrelation strongest in equal-weighted indices of illiquid stocks; the older
   literature (Lo–MacKinlay-era) reports strongly positive equal-weighted index autocorrelation.
   **These cannot all be right for the same object and I did not resolve them.** The programme can
   settle it in one line on its own data, and should, because it is the only input the kill number
   needs. My table in §1.3 covers ρ from 0 to 0.5, so whatever they measure, the answer is there.
2. **The autocorrelation of a per-trade P&L series in time order.** No external evidence. If trades
   cluster in time (and a slot-limited book with a refill pool suggests they might), the summand is
   not white and b̂ is not 1.
3. **Whether the programme's block bootstrap resamples whole bars or name-bar cells** (§4.2). This
   is the single biggest unknown in the brief and it is a property of their code, not the
   literature. If it draws within-bar, every interval is far too narrow and nothing in §1 matters.
4. **The 0.06 discrepancy in PPW (2009) Table 1, row ρ = −0.4, N = 800** (§1.2). My closed form
   reproduces five of six b_CB cells exactly and misses that one. I could not explain it and did not
   assume it away.
5. **The circular-seam problem for rotation tests** (§3.4). I reasoned it out from the exactness
   condition I read in Hemerik & Goeman; **I found no paper addressing it and state it as my
   argument, not as a citation.** It should be treated as a hypothesis to check, not a finding.
6. **Politis & Romano (1992) and (1994), Künsch (1989), Lahiri (1993/1995/1999), Langsrud (2005),
   Southworth et al. (2009), Petersen (2009), Thompson (2011), Cameron–Gelbach–Miller (2008/2011),
   Moulton (1990), Driscoll–Kraay (1998), Jöckel (1986), Andrews & Buchinsky (2000).** Not read.
   Cited above only for existence and headline claim, always tagged. **No formula attributed to any
   of them in this brief was read by me**, with the single exception of the Moulton equicorrelated
   structure, which I read in Schmidheiny's teaching handout (not in Moulton).
7. **PW (2004)'s Appendix proofs, and Nordman (2008) §§3–4.** Skimmed, not read. I took Theorems
   3.1–3.3 and Nordman's Theorem 1 as stated.
8. **`np::b.star`'s and `blocklength::pwsd`'s actual source.** I read `np::b.star`'s documented
   argument defaults, not its code. `arch`'s code I read in full. The comparison table in §6
   therefore mixes one read-in-full implementation with one read-from-documentation.
9. **Whether any of this programme's decision records cite Lahiri (1999) or PW (2004) for a
   superseded number** (§2.1). I have no access to them and raise it only as a hazard to check.
10. **The programme's own D373 rule, D361/C2b enumeration results, and the 26-offset finding.** I
    know these only from the commissioning text. §3.2 shows the published framework *implies* the
    26-offset result; it is not independent confirmation of anything they measured.

---

## Appendix — the three things worth doing, ranked, and the one thing not worth doing

1. **Feed the selector the summand of the statistic, not the return series** (§1.6). This is where
   the inherited 20 is wrong by 6×, in the dangerous direction, and it is free to fix.
2. **Use `(1 + count) / (1 + draws)` for every Monte-Carlo and rotation p-value** (§3.3). One
   character of code; converts an anti-conservative estimator into an exact test; and for the
   per-name rotations it removes the bias the programme currently believes it has to live with.
3. **Assert that the chosen bandwidth M came back below m_max** whenever the selector is run
   (§1.5). Free diagnostic; catches the silent failure at high persistence; and where it fires, the
   right response is to report the effective sample size and abandon the block bootstrap, not to
   raise b.
4. **Do not run a block-length sensitivity study on the return-side statistics.** The arithmetic in
   §1.4 says it would move the standard error by a few percent and change no conclusion. **The
   inherited choice is fine there and this lane ends on that half of the question**, exactly as the
   commission allowed for.
