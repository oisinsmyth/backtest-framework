"""C4 [MEASURED IN BRIEF] -- each leg against ITS OWN sort's universe.

A long leg measured against the CRSP value-weighted market mixes in the size premium
whenever the leg is equal-weighted (round 2's `B1` benchmark problem). The within-sort
benchmark is the mean of the five quintile portfolios of the SAME file, which is the
sort's own (equal-count) universe. Reported alongside the VW-market version.
"""
import csv, io, json, math, os, zipfile, collections

HERE = os.path.dirname(os.path.abspath(__file__))
SIGS = {"GP", "CBOperProf", "OperProf", "OperProfRD"}


def tstat(xs):
    n = len(xs)
    if n < 3:
        return None, None, n
    m = sum(xs) / n
    v = sum((x - m) ** 2 for x in xs) / (n - 1)
    se = math.sqrt(v / n)
    return m, (m / se if se else None), n


def load(zpath, sigs):
    z = zipfile.ZipFile(os.path.join(HERE, zpath))
    out = collections.defaultdict(lambda: collections.defaultdict(dict))
    with z.open(z.namelist()[0]) as f:
        for row in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8")):
            if row["signalname"] in sigs and row["ret"] not in ("NA", ""):
                out[row["signalname"]][row["port"]][row["date"][:7]] = float(row["ret"])
    return out


WINDOWS = [("in_sample_1963_07_2010_12", "1963-07", "2010-12"),
           ("post_sample_pre_pub_2011_2013", "2011-01", "2013-12"),
           ("post_publication_2014_2024", "2014-01", "2024-12"),
           ("programme_window_2010_2024", "2010-01", "2024-12"),
           ("last_five_2020_2024", "2020-01", "2024-12")]

OUT = {}
for label, zf, sigs in [("QuintilesEW", "C4_CZ_QuintilesEW.zip", SIGS),
                        ("QuintilesVW", "C4_CZ_QuintilesVW.zip", SIGS),
                        ("PLACEBO", "C4_CZ_PlaceboPortsFull.zip", {"GPlag"})]:
    ap = load(zf, sigs)
    blk = {}
    for sig in sorted(ap):
        ports = sorted(p for p in ap[sig] if p != "LS")
        if len(ports) != 5:
            blk[sig] = {"SKIPPED_n_bins": len(ports)}
            continue
        lp, sp = ports[-1], ports[0]
        d = {"bins": ports}
        # the sort's own universe: simple mean of the five quintile returns
        months = sorted(set.intersection(*[set(ap[sig][p]) for p in ports]))
        uni = {k: sum(ap[sig][p][k] for p in ports) / 5.0 for k in months}
        # negative control: universe minus universe, and sum of (port - universe) must be ~0
        resid = [sum(ap[sig][p][k] - uni[k] for p in ports) for k in months]
        d["C7_sum_of_deviations_from_own_universe_max_abs"] = max(abs(x) for x in resid)
        for nm, lo, hi in WINDOWS:
            ms = [k for k in months if lo <= k <= hi]
            if len(ms) < 3:
                continue
            lu = [ap[sig][lp][k] - uni[k] for k in ms]
            su = [ap[sig][sp][k] - uni[k] for k in ms]
            ls = [ap[sig][lp][k] - ap[sig][sp][k] for k in ms]
            m1, t1, n1 = tstat(lu); m2, t2, _ = tstat(su); m3, t3, _ = tstat(ls)
            d[nm] = {"long_minus_own_universe": round(m1, 4), "t": round(t1, 2),
                     "short_minus_own_universe": round(m2, 4), "t_short": round(t2, 2),
                     "LS": round(m3, 4), "t_LS": round(t3, 2), "n_months": n1,
                     "long_share_of_LS": round(m1 / m3, 2) if m3 else None}
        blk[sig] = d
    OUT[label] = blk

print(json.dumps(OUT, indent=1))
json.dump(OUT, open(os.path.join(HERE, "C4_ownuniverse.json"), "w"), indent=1)
