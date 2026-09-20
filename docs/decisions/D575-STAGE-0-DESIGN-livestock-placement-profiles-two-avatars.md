# D575 STAGE 0 DESIGN — the livestock placement profiles: D570's short-spread construction at every calendar month on **live cattle and lean hogs**, with the best placement predicted from **the supply calendar** and, for cattle, a **named competing avatar (the feedlot's placement hedge)** whose prediction is disjoint — declared before any outcome is read

**Stage 0 design, committed before the runner exists. Diagnostic on 2011 → 2023; the 2024+ slice is
not read on any source.** Nothing admitted (R15). *A pre-registration in substance for one declared
construction a root, as D571 was: the placements are predicted here, the constructions are fixed
in writing, the pass rule is the construction's own twelve placements, and the RESULT is the
record any disposition stands on. This is the avatar programme's closing test: the last two
roots with unseen placement profiles.*

*2026-09-20. D571 showed that a placement profile does not transfer across roots — the soybean
profile predicted corn and meal and was falsified on wheat and oil — so the prediction for each
livestock root is made from that root's own supply calendar, not from any profile already seen.
What the grains taught is carried: the always-on control per positioned day (D568), the
construction's own placement null as the pass rule (D570), the composition and sign predicted
before the read (D574), and one declared construction a root.*

**What has been seen on these roots.** Nothing of this construction. D556 and D557 ranked LE and
HE among 17 or 36 roots on carry; D564 held them in basis-momentum legs (LE +5.8 %, HE +5.7 % of
the in-sample book); D573 placed them in hedging-pressure legs. No spread, no placement, no
per-month figure on either root has been read.

---

## 1. The construction, fixed (D570's, unchanged)

At the last session before calendar month *m*: **T1 = the first listed delivery month strictly
after the third holding month, T2 the next listed; short T1 / long T2**, one contract a leg,
held on every session of months *m*, *m*+1, *m*+2, flat otherwise, the pair fixed for the window.
Twelve placements a root. Return `−(r1 − r2)`, flat sessions as zeros. The **always-on control**:
the rule-rolled first-nearby pair (delivery ≥ *m*+2, re-read monthly), short, every month.

Contract months: live cattle G J M Q V Z; lean hogs G J K M N Q V Z. The pairs the rule picks:

| *m* | holds | **LE** pair | **HE** pair |
|---|---|---|---|
| 1 | Jan–Mar | J/M | J/K |
| 2 | Feb–Apr | M/Q | K/M |
| 3 | Mar–May | M/Q | M/N |
| 4 | Apr–Jun | Q/V | N/Q |
| 5 | May–Jul | Q/V | Q/V |
| 6 | Jun–Aug | V/Z | V/Z |
| 7 | Jul–Sep | V/Z | V/Z |
| 8 | Aug–Oct | Z/G | Z/G |
| 9 | Sep–Nov | Z/G | Z/G |
| 10 | Oct–Dec | G/J | G/J |
| 11 | Nov–Jan | G/J | G/J |
| 12 | Dec–Feb | J/M | J/K |

Both are full contracts (40,000 lb, $400 a point in cents a pound, tick $10; no micro); $6 a
round trip plus one tick a leg a side, four sides a window.

## 2. The avatars and the predictions

**Lean hogs — the supply calendar.** Hog slaughter peaks in October → December and troughs in
June → July; the summer contracts carry the seasonal premium and the December contract the
seasonal discount. A short nearby pays when the nearby delivers into the glut and the deferred
past it: placements whose T1 is October or December against a deferred in the new year's
recovery. **Predicted best placement in {7, 8, 9}** (V/Z or Z/G). The short **loses** where the
nearby is a summer contract whose premium builds through the spring: **{2, 3, 4} ≤ 0** (K/M,
M/N, N/Q). Falsifier: best placement outside {6, 7, 8, 9, 10}.

**Live cattle — two avatars, disjoint predictions.**
- *The supply calendar.* Fed-cattle marketings peak May → July and prices are seasonally
  highest in March → April. The short nearby pays where T1 delivers into the summer supply
  peak against a deferred past it: **{3, 4, 5}** (M/Q, Q/V). The short loses where the nearby
  is a spring contract building its premium: **{10, 11, 12} ≤ 0** (G/J, J/M).
- *The feedlot's placement hedge.* Placements peak in October; the feedlot sells the contract
  matching its marketing date five to six months out (February → April delivery) at placement.
  Hedging pressure then sits on the deferred spring contracts in the fall and is earned back as
  delivery approaches — which pays a **long** deferred against the nearer contract in
  November → January: the short construction's **{10, 11}** would be its *best* placements. This
  is the merchant-at-harvest avatar's livestock form and it predicts the opposite of the supply
  calendar at those months.

**Declared:** the supply calendar is the primary prediction on cattle; the hedge avatar is
named so that a best placement in {10, 11} is read as *that* avatar supported and the supply
calendar refuted, not as chance. Falsifier for both: best placement in {1, 2, 6, 7, 8, 9}.

**Declared constructions (full line, one a root):** **HE *m*8 (Aug → Oct, Z/G)** and **LE *m*4
(Apr → Jun, Q/V)**. The always-on control is predicted **≤ 0 per positioned day on both roots**
(the nearby strengthens against the deferred on average, as on every grain).

**Chance.** Each three-month set is right by chance one time in four; both roots in their sets,
one in sixteen.

## 3. The decision rule, declared

- **The supply-calendar avatar is supported** if both roots' best placements (2011–2023 Sharpe)
  are in their sets and both controls are ≤ 0; **partially supported** if one is; **refuted** on
  a root whose best is in its falsifier set. Cattle's hedge avatar is **supported instead** if
  cattle's best is in {10, 11}.
- **A root's declared construction is a candidate** if positive on 2016–2023, best of its own
  twelve on 2011–2023 and above its always-on control per positioned day; it then gets the full
  line — gross and net Sharpe / Sortino with SE, positioned months, per window, per month, the
  dollar book at one contract with C-a / C-c / C-d — and a row in `COMPONENTS_PROP.md` on its
  numbers, the twelve placements its enumerated null. **A placement that wins but was not
  declared is a null cell, seen, not licensed.**
- **The avatar programme closes on this result** unless a declared construction is a candidate:
  if neither root's declared placement is best of twelve, the seasonal-spread line on the
  commodity curve has no open construction, and the record says so for the principal to close
  or not.

## 4. Reported beside, diagnostic

Per root: the twelve-placement table (Sharpe 2011–2023 and 2016–2023, Sortino, bp per
positioned day, per-window hit, the pair, windows scored); the always-on control's Sharpe, per-day
return and calendar-month profile; the COT disaggregated **producer/merchant** net short share of
open interest (on disk from 2006) at each declared window's formation and its change through
the window, with its Spearman against the window return — **no prediction is made on it**; the
audits of D570 on each declared construction (pair by a second path, survival, held-contract,
lag, sign in money for a short spread, right quantity), each proven to raise; placement *m*
asserted to reproduce the declared series exactly.

## 5. What is read, and what is not

The settlement strip for LE and HE 2010-06 → 2023-12-29; the breadth fixture for the calendar
and the specifications; the COT fixture, disaggregated producer/merchant, through 2023, as a
recorded diagnostic. **Not read: anything from 2024-01-01 on, on any source.** No Cattle on
Feed or Hogs and Pigs report is used: NASS needs a key this programme does not hold, and the
calendar the avatars stand on is the USDA's published seasonal pattern, not a series.

## 6. What this record does not do

No gate; no sizing; no netting across roots; no re-placement after reading. A candidate here is
confirmed only by its root's 2024+ slice, on the principal's word.
