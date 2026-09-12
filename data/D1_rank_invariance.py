"""D1 measurement 3: WHICH OUTLIER / TRANSFORM CHOICES ARE EXACT NO-OPS FOR A SORT.

Claim under test.  A quantile sort is a RANK statistic, so any weakly monotone
transform of the sorting variable leaves portfolio membership unchanged, while any
transform that DELETES observations changes every breakpoint.  If that is right:

  level -> log of a positive characteristic   EXACT no-op  (genuinely arbitrary)
  winsorise at 1/99, then form deciles        EXACT no-op  (cutoff inside the
                                                            extreme bucket)
  TRIM at 1/99, then form deciles             NOT a no-op
  winsorise at 20/80, then form deciles       NOT a no-op  (cutoff coarser than
                                                            the bucket: ties collapse)

Run on a REAL, fat-tailed, tie-heavy cross-section: gross profit over total assets
for every US filer reporting both, from the SEC's own XBRL frames API.

NEGATIVE CONTROLS
  P1  a NON-monotone transform must change membership -- if it does not, the test
      has no power and every "no-op" below is meaningless.
  P2  winsorising at a cutoff COARSER than the bucket width must change membership.
  P3  the characteristic must actually contain extreme values and ties, else the
      no-op results are vacuous; both are counted and printed.
"""
import json, urllib.request, math, os

UA = "backtest-framework research research@backtest-framework.org"
HERE = os.path.dirname(os.path.abspath(__file__))
L = []


def say(s=""):
    print(s); L.append(s)


def fr(tag, per, tx="us-gaap"):
    u = "https://data.sec.gov/api/xbrl/frames/%s/%s/USD/%s.json" % (tx, tag, per)
    r = urllib.request.Request(u, headers={"User-Agent": UA})
    return json.loads(urllib.request.urlopen(r, timeout=60).read())


def deciles(xs, J=10):
    """Rank into J buckets by the characteristic; returns {key: bucket}.
    Ties broken by key so the assignment is deterministic and comparable."""
    order = sorted(xs, key=lambda k: (xs[k], k))
    n = len(order)
    out = {}
    for i, k in enumerate(order):
        out[k] = min(J - 1, (i * J) // n)
    return out


def wins(xs, q):
    vals = sorted(xs.values())
    n = len(vals)
    k = int(math.floor(q * n))
    if k == 0:
        return dict(xs)
    lo, hi = vals[k], vals[n - 1 - k]
    return {kk: min(max(v, lo), hi) for kk, v in xs.items()}


def trimmed(xs, q):
    vals = sorted(xs.values())
    n = len(vals)
    k = int(math.floor(q * n))
    lo, hi = vals[k], vals[n - 1 - k]
    return {kk: v for kk, v in xs.items() if lo <= v <= hi}


say("=" * 78)
say("D1 MEASUREMENT 3 -- rank invariance of a sort, on a real SEC cross-section")
say("endpoint: https://data.sec.gov/api/xbrl/frames/us-gaap/{GrossProfit,Assets}/USD/")
say("=" * 78)
GP = fr("GrossProfit", "CY2023")
A = fr("Assets", "CY2023Q4I")
g = {e["cik"]: e["val"] for e in GP["data"]}
a = {e["cik"]: e["val"] for e in A["data"]}
x = {c: g[c] / a[c] for c in (set(g) & set(a)) if a[c] > 0}
say("GP/AT cross-section: n = %d filers (CY2023 flow over CY2023Q4I stock)" % len(x))
v = sorted(x.values())
say("  min %+.3f  p1 %+.3f  p25 %+.3f  median %+.3f  p75 %+.3f  p99 %+.3f  max %+.3f"
    % (v[0], v[int(.01 * len(v))], v[int(.25 * len(v))], v[len(v) // 2],
       v[int(.75 * len(v))], v[int(.99 * len(v))], v[-1]))
nties = len(v) - len(set(v))
say("  P3 extremity and ties present?  |max| / p99 = %.1f ;  tied values = %d"
    % (abs(v[-1]) / max(1e-9, abs(v[int(.99 * len(v))])), nties))

base = deciles(x)


def diff(other_assign, universe=None):
    keys = set(base) & set(other_assign) if universe is None else universe
    return sum(1 for k in keys if base[k] != other_assign[k]), len(keys)


say()
say("MEMBERSHIP CHANGES vs the raw-characteristic decile sort (J = 10)")
# monotone transform: log of a positive characteristic.  restrict to x>0 so log exists
pos = {k: vv for k, vv in x.items() if vv > 0}
base_pos = deciles(pos)
log_pos = deciles({k: math.log(vv) for k, vv in pos.items()})
dmoved = sum(1 for k in pos if base_pos[k] != log_pos[k])
say("  level -> LOG of the sorting variable (x>0 subsample, n=%d):   %d of %d names move"
    % (len(pos), dmoved, len(pos)))

# sqrt and z-score: two more monotone transforms on the same subsample
sq = deciles({k: math.sqrt(vv) for k, vv in pos.items()})
mu = sum(pos.values()) / len(pos)
sd = math.sqrt(sum((vv - mu) ** 2 for vv in pos.values()) / (len(pos) - 1))
zs = deciles({k: (vv - mu) / sd for k, vv in pos.items()})
say("  level -> SQRT                                               %d of %d names move"
    % (sum(1 for k in pos if base_pos[k] != sq[k]), len(pos)))
say("  level -> Z-SCORE                                            %d of %d names move"
    % (sum(1 for k in pos if base_pos[k] != zs[k]), len(pos)))

# winsorise at 1/99 -- cutoff strictly inside the extreme decile
w1 = deciles(wins(x, 0.01))
n1, tot = diff(w1)
say("  WINSORISE the characteristic at 1/99, then sort                %d of %d names move" % (n1, tot))
w25 = deciles(wins(x, 0.025))
say("  WINSORISE at 2.5/97.5                                          %d of %d names move" % diff(w25))
w5 = deciles(wins(x, 0.05))
say("  WINSORISE at 5/95                                              %d of %d names move" % diff(w5))

# P2: a cutoff COARSER than the bucket width must bite
w20 = deciles(wins(x, 0.20))
n20, t20 = diff(w20)
say("  P2 WINSORISE at 20/80 (coarser than a decile)                  %d of %d names move  <- must be > 0"
    % (n20, t20))

# trim at 1/99 -- deletes observations, so breakpoints move
tr = trimmed(x, 0.01)
tr_assign = deciles(tr)
nt = sum(1 for k in tr if base[k] != tr_assign[k])
say("  TRIM the characteristic at 1/99, then sort (n drops %d -> %d)   %d of %d SURVIVING names move"
    % (len(x), len(tr), nt, len(tr)))
tr5 = trimmed(x, 0.05)
tr5a = deciles(tr5)
say("  TRIM at 5/95 (n drops %d -> %d)                                 %d of %d surviving names move"
    % (len(x), len(tr5), sum(1 for k in tr5 if base[k] != tr5a[k]), len(tr5)))

# P1: a NON-monotone transform must bite
nm = deciles({k: vv - 0.5 * vv * vv for k, vv in x.items()})
n_nm, t_nm = diff(nm)
say("  P1 NON-monotone transform x - 0.5x^2                           %d of %d names move  <- must be > 0"
    % (n_nm, t_nm))

say()
say("TOP-DECILE MEMBERSHIP SPECIFICALLY (the LONG LEG), same comparisons")
top0 = {k for k, b in base.items() if b == 9}
for lab, assign, uni in [("winsorise 1/99", w1, set(base)),
                         ("winsorise 5/95", w5, set(base)),
                         ("winsorise 20/80", w20, set(base)),
                         ("trim 1/99", tr_assign, set(tr)),
                         ("trim 5/95", tr5a, set(tr5)),
                         ("non-monotone (control)", nm, set(base))]:
    top1 = {k for k in uni if assign.get(k) == 9}
    say("  %-24s long leg %4d -> %4d names;  entered %3d, left %3d (%.1f%% of the leg turned over)"
        % (lab, len(top0 & uni), len(top1), len(top1 - top0), len((top0 & uni) - top1),
           100.0 * len(top1 ^ (top0 & uni)) / max(1, len(top0 & uni))))

say()
say("VERDICT")
say("  A weakly monotone transform of the sorting variable -- log, sqrt, z-score,")
say("  or winsorisation at a cutoff inside the extreme bucket -- is an EXACT no-op")
say("  for a quantile sort.  Trimming at the same cutoff is not: it deletes names,")
say("  moves every breakpoint, and turns over part of the long leg.  The two")
say("  branches of 'winsorise versus trim at the same cutoff' are therefore NOT")
say("  practically equivalent for a SORT, whatever they do in a regression.")

open(os.path.join(HERE, "D1_rank_invariance.txt"), "w").write("\n".join(L))
print("\nwrote D1_rank_invariance.txt")
