"""D1 measurement 2: the NEGATIVE-DENOMINATOR SIGN FLIP, counted on real filings.

Claim under test:  for a ratio signal, "outlier treatment" and "dropping
loss-makers" are the SAME node whenever the denominator can change sign, because
a firm with a negative numerator AND a negative denominator receives a POSITIVE
ratio and lands in the TOP of the sort.  Total assets cannot be negative, so
GP/AT is immune; book equity can be, so OP/BE is not.

Endpoint: https://data.sec.gov/api/xbrl/frames/<taxonomy>/<tag>/USD/<period>.json
(SEC's own XBRL "frames" API -- one concept, all filers, one period.)
CAVEAT carried from the programme's own notes: `frames` returns LAST-FILED values,
so this is a cross-sectional census of the data as it now stands, not a
point-in-time panel.  Counts, not returns, are what is claimed.

NEGATIVE CONTROLS
  C1  a period that cannot exist (CY1890Q1I) must return no facts.
  C2  Assets <= 0 must be EXACTLY ZERO firms -- an accounting identity.  If this
      fires, the harvest is not what its field name says it is.
  C3  StockholdersEquity < 0 must be NON-zero -- the complement of C2; if both
      were zero the file would be a plausible shell with no facts in it.
  C4  the two frames must not be the same document: their fact counts and the
      set of CIKs must differ.
"""
import json, urllib.request, os, math

UA = "backtest-framework research research@backtest-framework.org"
HERE = os.path.dirname(os.path.abspath(__file__))
L = []


def say(s=""):
    print(s); L.append(s)


def frame(tag, period, taxonomy="us-gaap", unit="USD"):
    url = "https://data.sec.gov/api/xbrl/frames/%s/%s/%s/%s.json" % (taxonomy, tag, unit, period)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read()
            ct = r.headers.get("Content-Type", "")
            code = r.status
    except urllib.error.HTTPError as e:
        return None, e.code, e.headers.get("Content-Type", ""), len(e.read() or b""), url
    try:
        d = json.loads(body)
    except Exception:
        return None, code, ct, len(body), url
    return d, code, ct, len(body), url


say("=" * 78)
say("D1 MEASUREMENT 2 -- negative-denominator sign flip, SEC XBRL frames API")
say("=" * 78)

PERIOD_I, PERIOD_D = "CY2023Q4I", "CY2023"
got = {}
for tag, per in [("Assets", PERIOD_I), ("StockholdersEquity", PERIOD_I),
                 ("GrossProfit", PERIOD_D), ("OperatingIncomeLoss", PERIOD_D),
                 ("NetIncomeLoss", PERIOD_D)]:
    d, code, ct, nbytes, url = frame(tag, per)
    n = len(d.get("data", [])) if d else 0
    say("  %-20s %-10s HTTP %s  %-20s %9d bytes  facts %5d"
        % (tag, per, code, ct.split(";")[0], nbytes, n))
    if d:
        say("       label from the file itself: %r   unit %r   pts %s"
            % (d.get("label"), d.get("uom"), d.get("pts")))
        got[tag] = {e["cik"]: e["val"] for e in d["data"]}

# ---------------------------------------------------------------- controls
say()
say("NEGATIVE CONTROLS")
d, code, ct, nbytes, url = frame("Assets", "CY1890Q1I")
n_impossible = len(d.get("data", [])) if d else 0
say("  [%s] C1 impossible period CY1890Q1I returns no facts  (HTTP %s, %d bytes, facts %d)"
    % ("PASS" if n_impossible == 0 else "**FIRED**", code, nbytes, n_impossible))

A = got.get("Assets", {})
nonpos = [(c, v) for c, v in A.items() if v <= 0]
say("  [%s] C2 Assets <= 0 is EXACTLY ZERO firms  (found %d of %d)"
    % ("PASS" if len(nonpos) == 0 else "**FIRED**", len(nonpos), len(A)))
if nonpos[:5]:
    say("       examples: %s" % nonpos[:5])

SE = got.get("StockholdersEquity", {})
neg_se = [(c, v) for c, v in SE.items() if v < 0]
say("  [%s] C3 StockholdersEquity < 0 is NON-zero  (found %d of %d)"
    % ("PASS" if len(neg_se) > 0 else "**FIRED**", len(neg_se), len(SE)))

say("  [%s] C4 the Assets and StockholdersEquity frames are different documents "
    "(fact counts %d vs %d; CIKs in one and not the other: %d)"
    % ("PASS" if (len(A) != len(SE) and len(set(A) ^ set(SE)) > 0) else "**FIRED**",
       len(A), len(SE), len(set(A) ^ set(SE))))

# ---------------------------------------------------------------- the census
say()
say("=" * 78)
say("THE CENSUS -- how large is the affected subset, and where does it land?")
say("period: %s (instantaneous) and %s (duration).  frames = last-filed values." % (PERIOD_I, PERIOD_D))
say("=" * 78)
OI = got.get("OperatingIncomeLoss", {})
NI = got.get("NetIncomeLoss", {})
GP = got.get("GrossProfit", {})

both_se_oi = sorted(set(SE) & set(OI))
say("filers with BOTH StockholdersEquity and OperatingIncomeLoss: %d" % len(both_se_oi))
q = {"be<0": 0, "oi<0": 0, "be<0 & oi<0 (SIGN FLIP -> positive ratio)": 0,
     "be<0 & oi>=0 (ratio turns negative)": 0, "be>0 & oi<0": 0, "be>0 & oi>=0": 0}
flip_vals = []
for c in both_se_oi:
    be, oi = SE[c], OI[c]
    if be < 0:
        q["be<0"] += 1
    if oi < 0:
        q["oi<0"] += 1
    if be < 0 and oi < 0:
        q["be<0 & oi<0 (SIGN FLIP -> positive ratio)"] += 1
        flip_vals.append(oi / be)
    elif be < 0 and oi >= 0:
        q["be<0 & oi>=0 (ratio turns negative)"] += 1
    elif be > 0 and oi < 0:
        q["be>0 & oi<0"] += 1
    elif be > 0 and oi >= 0:
        q["be>0 & oi>=0"] += 1
for k, v in q.items():
    say("   %-44s %5d   %5.2f%%" % (k, v, 100.0 * v / len(both_se_oi)))
if flip_vals:
    flip_vals.sort()
    say()
    say("   the sign-flipped OP/BE values (numerator<0, denominator<0 -> POSITIVE):")
    say("     n %d   min %+.3f   median %+.3f   max %+.3f" %
        (len(flip_vals), flip_vals[0], flip_vals[len(flip_vals) // 2], flip_vals[-1]))
    say("     how many exceed +1.00 (i.e. would sit at the very top of an OP/BE sort)? %d"
        % sum(1 for v in flip_vals if v > 1.0))
    say("     how many exceed the 90th percentile of the WELL-DEFINED (BE>0) OP/BE? see below")

well = sorted(OI[c] / SE[c] for c in both_se_oi if SE[c] > 0)
if well:
    p90 = well[int(.90 * len(well))]
    p99 = well[int(.99 * len(well))]
    say("   well-defined OP/BE (BE>0): n %d   p90 %+.3f   p99 %+.3f" % (len(well), p90, p99))
    say("   sign-flipped firms above the BE>0 p90 cutoff: %d of %d (%.1f%% of the flips)"
        % (sum(1 for v in flip_vals if v > p90), len(flip_vals),
           100.0 * sum(1 for v in flip_vals if v > p90) / max(1, len(flip_vals))))
    say("   --> THESE WOULD ENTER THE TOP DECILE OF AN UNFILTERED OP/BE SORT.")

# the deflator immunity claim, counted
say()
say("THE DEFLATOR-IMMUNITY CLAIM, COUNTED")
both_gp_at = sorted(set(GP) & set(A))
flip_at = sum(1 for c in both_gp_at if A[c] <= 0)
say("   filers with BOTH GrossProfit and Assets: %d" % len(both_gp_at))
say("   of those, filers whose DENOMINATOR (Assets) is <= 0, i.e. can sign-flip: %d" % flip_at)
say("   so GP/AT cannot sign-flip and OP/BE can, on this census, %d vs %d firms."
    % (flip_at, q["be<0 & oi<0 (SIGN FLIP -> positive ratio)"]))
say("   NetIncomeLoss < 0 (loss-makers, duration %s): %d of %d = %.1f%%"
    % (PERIOD_D, sum(1 for v in NI.values() if v < 0), len(NI),
       100.0 * sum(1 for v in NI.values() if v < 0) / max(1, len(NI))))

open(os.path.join(HERE, "D1_sec_signflip.txt"), "w").write("\n".join(L))
print("\nwrote D1_sec_signflip.txt")
