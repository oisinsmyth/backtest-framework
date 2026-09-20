# D567 — STAGE 0 DESIGN (not yet run): the grains at harvest — the elevator and merchant as the constrained party, on corn, soybeans and wheat

**A design, committed before any outcome is read.** Nothing here is a result; no session is
scored; the 2024+ slice of every fixture named stays shut. The design fixes the avatars, the
state variables, the windows, the outcomes, the seasonal control and the falsifiers, so that
when Stage 0 runs it measures premises rather than finds them. The principal asked for the
design first (2026-09-20), after NG (D565, D566) taught two things this design carries: a
"state variable" can be a synonym for the month, and a scheduled premium harvested without a
state check assumes the curve state that carries it.

---

## 1. The avatars, and what each constraint does to the curve

Three roots, one constrained party, one crop calendar each — declared from the physical market,
not from any P&L.

| root | crop · harvest | the constrained party | what binds, and when | the curve's response the mechanism predicts |
|---|---|---|---|---|
| **ZC** corn | US corn · **September → November** | the elevator and merchant: buys cash grain from farmers who must sell at harvest, stores it, sells futures against it | bin space and working capital are finite; at harvest supply arrives faster than storage and logistics absorb it | the harvest contract (Z) must clear by price against deferred (H): **carry widens to full carry** when stocks are ample; when stocks are tight the front holds up or inverts |
| **ZS** soybeans | US soybeans · **September → November** (crush and export pull begin at once) | the same merchant, plus the crusher and the exporter, who compete for the same bushels | same bins, shorter storage season, a larger export share | the harvest contract (X) against January (F): same prediction, weaker carry because the pull is faster |
| **ZW** wheat (SRW) | US soft red winter · **June → August** | the same merchant three months earlier, in a crop with a large world market and a small US share | bins are empty from the prior crop, so storage binds less; the constraint is more often quality and export logistics | the harvest contract (N) against September (U) and December (Z): the weakest of the three by the mechanism's own logic, which is a prediction and not an excuse |

Two other windows are declared because the crop calendar names them ex ante and the NG read
showed a scheduled premium has two ends:

- **The weather-premium window, corn and soybeans, June 1 → August 31.** The new-crop contract
  (Z for corn, X for soybeans) carries a premium for the growing-season weather risk, paid by the
  end user and processor buying forward. In a normal year it decays into harvest; in a drought
  year (2012) it does the opposite with a tail. This is the grain analogue of the NG winter
  premium and it is the *outright* new-crop contract, not the spread.
- **The post-harvest carry window, December 1 → February 28.** After harvest the merchant is paid
  the carry to store; as grain moves and bins empty the carry narrows. Long the front against the
  deferred is the mechanism's direction here. It is the reverse of the harvest window and must
  be scored separately, never netted.

## 2. The state variables, point-in-time, and the one that is not available

| variable | source on disk | what it measures | availability lag used |
|---|---|---|---|
| **stocks-to-use, S/U** | WASDE monthly CSVs, April 2010 → September 2026 (`data/raw/usda/wasde/`): `Ending Stocks` ÷ `Use, Total`, million bushels, for the marketing year in progress at formation (the `Proj.` year for the new crop from the May report onward; the `Est.` year before) — commodity `Corn` in *U.S. Feed Grain and Corn Supply and Use*, `Oilseed, Soybean` in *U.S. Soybeans and Products Supply and Use*, `Wheat` in *U.S. Wheat Supply and Use* | how full the bins will be relative to the pull on them | the report's own `ReleaseDate` (about the 10th–12th of the month); the last report released **before** the formation session |
| **formation basis** | the strip: `F(T2)/F(T1) − 1` at formation, T1/T2 by the delivery rule (grains: delivery ≥ *m*+2), and its ratio to **full carry** (the interest plus storage cost of holding one contract-month, taken as the CBOT storage rate of 5¢ a bushel a month plus SOFR on the price) | whether the curve is already in the state the mechanism names — the premise NG exposed | the formation session |
| **commercial net short, COT** | `cftc_cot_raw` legacy and disaggregated, on disk for ZC, ZS, ZW | the merchant's hedging pressure at harvest | the report date (Tuesday) released Friday; the last release before formation |
| **September 1 stocks** (old-crop carryout) | WASDE's September report carries it as the marketing-year `Ending Stocks` `Est.`; the NASS *Grain Stocks* report itself needs a Quick Stats key the agent cannot register | the bins' state on the eve of harvest | the September WASDE release |
| **storage capacity** | **not available keylessly** (NASS off-farm capacity). S/U stands in for stocks-against-capacity, and the record says so | | |

**The gap in the state variable, closed the same day.** The 2016–2020 WASDE archive refused
curl and the principal's own browser rejected the zip on a scanner check. It was unpacked inside
the built-in browser's page session with the browser's native inflater and filtered there to the
corn, soybean and wheat US supply-and-use rows (`data/raw/usda/wasde/wasde_2016_2020_grains_su.csv`,
6,330 rows, 59 reports, 2016-01-12 → 2020-12-10, each with its release date). Together with the
2010–2015 archive and the 2021 → 2026 monthly files, S/U is point-in-time for all thirteen
harvests. The gitignored raw cache holds it; the derived fixture is built by Stage 0's runner.

## 3. The outcomes

For each root, each window, each year 2011 → 2023 (13 harvests; wheat's window and corn's and
soybeans' weather window also 13), at the formation session (the last session before the window)
and the exit session (the window's last session), on the same contracts:

- **spread return** `r1 − r2` of the pair chosen at formation (positive when the front outperforms
  the deferred); the mechanism predicts it **negative** in the harvest window when S/U is high;
- **front return** `r1`, the outright, for the weather-premium window (predicted negative in
  non-drought years) and as the harvest-low check;
- **basis change** `basis_exit − basis_formation`, the persistence measure the deposit's mechanism
  names.

Both in return space and in dollars at minimum size (ZC, ZS and ZW have no micro: one full
contract, $6 a round trip plus one tick a leg; D564's per-root σ at minimum size was $376, $778
and $682 a day, so a spread at one contract a leg sits inside C-d and an outright does not).

## 4. The tests, and the seasonal control that decides them

Every test is run twice: on the raw outcome, and on the outcome's **residual against its
same-window mean over the other twelve years** (leave-one-year-out). NG's storage state had a
Spearman of −0.17 with the front's next month and −0.02 with the residual: the second number is
the one that counts, because the first was the calendar wearing a state variable's clothes.

| # | test | declared expectation | what a failure means |
|---|---|---|---|
| **T1 calendar** | per-year table of the harvest-window spread and front return; mean, hit, t over 13 | spread negative in ≥ 8 of 13 on corn and soybeans; weaker on wheat | no harvest effect to gate |
| **T2 state** | Spearman of S/U (last release before formation) with the harvest-window spread return, raw and residual, year-block permutation p | **negative** (fuller bins → wider carry); the residual keeps at least half the raw | S/U is the calendar; the merchant's constraint is priced by the schedule alone, as NG's was |
| **T3 premise** | at formation, is the curve already at full carry? the share of harvests where the formation basis ≥ 80 % of full carry, by S/U tercile | when S/U is high the curve is *already* at full carry at formation and the spread has nothing left to widen — the NG failure mode; the tradeable state is high S/U with the basis **below** full carry | if the premise fails there is no window to enter, only a state to have been in |
| **T4 hedging pressure** | commercial net short at formation vs the window's spread return, raw and residual | negative (more merchant selling → weaker front) | the merchant is not the marginal seller of the front at harvest |
| **T5 weather premium** | corn and soybean new-crop outright, June → August, per year; the front's return split by whether the July WASDE cut yield | negative in ≥ 8 of 13; the drought years (2012, and any year the July yield cut exceeds 5 %) are the tail | no decaying premium; or a premium whose tail is larger than its mean |
| **T6 post-harvest carry** | December → February spread return per year | **positive** (the front gains as the carry narrows) in ≥ 7 of 13; smaller than T1 | the carry does not narrow on schedule |
| **T7 the reverse state** | the harvest window when S/U is in its lowest tercile | the spread return is **positive** or flat (tight bins, no clearing problem) | if it is still negative the state variable is irrelevant and the effect is calendar |

**n_eff is thirteen harvests per root, not sessions**, and the design says so: p-values by year-block
permutation, terciles not quintiles, and the per-year table printed before any statistic.

## 5. What Stage 0 will and will not do

- It reads 2011 → 2023 only, on the strip, the WASDE files and the COT fixture, all filtered
  below 2024-01-01 before anything is computed.
- It reads outcomes, so it is the deposit's selection budget being spent on a premise: **one
  window per mechanism, declared here**, no sweep. If a window in §1 turns out to be the wrong
  month, that is a finding about the calendar, not a licence to slide it.
- It produces no pre-registration. A construction follows only if T2 or T3 survives the
  residual test on corn or soybeans; it will be **flat by default**, gated on S/U and the
  formation basis at declared terciles, one contract a leg, held through the declared window,
  with the always-on spread as its control and D555's purged rotation as its placement null — the
  D565 shape with the state gate NG did not have.
- Livestock (LE, HE) is a separate design: no storage, the hedger is the feedlot, the state
  variable is Cattle on Feed and the disaggregated COT. It is not in this record.
