# D531 RESULT — the opening-range breakout does not clear on any root; **the volume gate broke its prediction in the interesting direction**

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D531-RESULT-the-opening-range-breakout-does-not-clear-on-any-root-and-the-volume-gate-broke-its-prediction.md`. The H1 above is the full title.*

*2026-09-14. Spec committed in `e357945` BEFORE the runner (R8). In sample 2016-01-04 → 2023-12-29;
the 2024+ slice was **not read**. Nothing admitted (R15).*

**Verdict under the declared rule: DOES NOT PASS.** The primary sits inside its own null and the
family maximum sits inside the family null. Both were required.

---

## 1. The declared verdict

| | | |
|---|---|---|
| **PRIMARY** — N = 6, pooled CL/GC/SI/NG, gated | hit **49.33 %**, n **3,758** | N1 p95 **50.80 %** → **INSIDE** |
| net per trade | **−$1.65** | gross +$2.56 against the $4.21 round trip (D527) |
| **N2 family maximum**, 36 cells | 52.29 % (`NQ-N12-all`) | family p95 **54.02 %** → **INSIDE** |

**One cell of thirty-six clears its own N1** — `NQ-N12-all`, 51.82 % against 51.71 %. At p95 on 36
cells the expectation under no edge is **1.8**, so one is *fewer* than chance would give. NQ is
calibration-only and ineligible for component #2 regardless.

**No candidate root clears anything.** The best candidate cells by net are `SI-N6-gated` (+$1.98) and
`GC-N12-gated` (+$1.08); both sit inside their own N1 p95, and picking them after the fact is exactly
what the family null exists to price.

## 2. The two pre-registered predictions

**P-A HELD — and it is the implementation check.** *Zero of six* ES cells clear N1, as predicted from
D487's measured first-half-hour-reverses-into-the-last slope of −0.102 (0.024), −4.3 SE. A
breakout-continuation on ES trades against a measured headwind, and did. Had ES come out strongly
positive I would have suspected the runner before believing it; it did not.

**P-B BROKE, in the direction that is worth something.** I predicted the gate would **cost** accuracy,
because D506 measured an activity filter buying +0.85 points of fee dilution and costing **−2.09**
points of accuracy. Instead the gate **adds +0.38 points of hit rate** averaged over 18 gated/ungated
pairs, and it moves **gross** more than it moves accuracy:

| cell | gross, ungated → gated | net gated |
|---|---|---|
| SI, N = 6 | +$2.14 → **+$6.19** | **+$1.98** |
| GC, N = 12 | +$2.00 → **+$5.29** | **+$1.08** |
| NG, N = 3 | +$0.73 → +$2.09 | −$2.12 |

**This is a sign, not a result.** +0.38 points over 18 pairs is weak, and it is mixed — the gate helps
SI by +3.19 points and hurts GC by −1.63 at the same N. What makes it worth chasing is *which* prior
it contradicts: the volume gate was condemned on ETFs, and D226's own disclosure says why that was
weak evidence — *"ETF volume is a weak instrument… a quiet tape can mean the authorised participants
simply did not need to trade… it cuts one way: a NEGATIVE here is weaker evidence against the gate as
a concept."* On real contract volume the sign flips. **That is the first evidence the ETF caveat was
the binding one**, and it is followed up separately rather than claimed here.

## 3. What the run establishes about the construction, beyond the verdict

**The session-native correction worked for two of four candidates and must not be overclaimed.**
Derived spans, from each root's own volume profile:

    CL   bars 0-67   09:00-14:35 ET   correct: crude's session ends 14:30
    NG   bars 0-67   09:00-14:35      correct
    ES   bars 6-83   09:30-15:59      correct: the RTH open
    NQ   bars 5-83   09:25-15:59
    GC   bars 0-83   NOT TRIMMED
    SI   bars 0-83   NOT TRIMMED

GC and SI keep the full template because their tail volume stays above the declared 10 %-of-peak
floor, even though D530 measured their share of session volume in the last hour at **5.4 %** and
**4.4 %** against an even 14.3 %. **So for GC and SI this run is still partly on the equity
template.** The floor is the wrong instrument for a root that trades thinly but continuously: a
share-of-session-volume rule would trim them, a share-of-peak rule does not. Recorded because the
next session-native study should use the former.

**The both-sides skip fired on real data** — 17 sessions on CL, 18 on GC, 23 on SI, 7 on NG, 7 on ES,
4 on NQ. Those are sessions where one 5-minute bar spans both the opening-range high and low, and
OHLC cannot order the two touches. Booking the favourable one is the artefact the external research
names, and these counts measure what it would have been worth: **76 sessions across six roots**, each
of which a naive implementation resolves in its own favour.

## 4. What this does and does not close

**It closes nothing.** Under R15, and the standing rule that only the principal closes an avenue,
this is one construction — opening range, breakout continuation, hold to the session close, three
lengths, six roots — that does not clear its nulls.

**It does narrow the prior usefully.** ORB continuation now has a measured negative on **four
commodity roots, on their own clock, at five minutes**, where before it had a measured negative on a
*precondition*, on two index roots, on the wrong clock — and D487's own title concedes it closed
*"before a breakout is tested."* The next person to propose it has a real number to argue with
instead of an inference.

---

Runner: [`scripts/run_d531_orb_session_native.py`](../../scripts/run_d531_orb_session_native.py)
(`--selftest` carries [LAG], [SIGN] and [QTY], plus an [X] break that must fire). Artefact:
[`data/d531_orb_session_native.json`](../../data/d531_orb_session_native.json).
