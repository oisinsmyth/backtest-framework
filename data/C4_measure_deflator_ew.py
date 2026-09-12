"""C4 [MEASURED IN BRIEF] -- the deflator convention and EQUAL weighting, pre/post publication.

Adds three endpoints on openassetpricing.com's Drive (ids in the fetch log):
  PlaceboPortsFull.zip                 -> GPlag = (sale - cogs)/at_{t-12}, CZ's own 'Placebo'
  PredictorAltPorts_QuintilesEW.zip    -> equal-weighted quintiles, this programme's weighting
  PredictorAltPorts_QuintilesVW.zip    -> value-weighted quintiles, the comparison
"""
import csv, io, json, math, os, zipfile, collections

HERE = os.path.dirname(os.path.abspath(__file__))


def tstat(xs):
    n = len(xs)
    if n < 3:
        return None, None, n
    m = sum(xs) / n
    v = sum((x - m) ** 2 for x in xs) / (n - 1)
    se = math.sqrt(v / n)
    return m, (m / se if se else None), n


def load_ff5_mkt():
    z = zipfile.ZipFile(os.path.join(HERE, "C4_F-F_Research_Data_5_Factors_2x3_CSV.zip"))
    txt = z.read(z.namelist()[0]).decode("latin-1").splitlines()
    mkt = {}
    started = False
    for line in txt:
        s = line.strip()
        if s.startswith(",Mkt-RF"):
            started = True
            continue
        if not started:
            continue
        p = [x.strip() for x in s.split(",")]
        if len(p) < 7 or len(p[0]) != 6 or not p[0].isdigit():
            if p[0] and not p[0].isdigit():
                break
            continue
        mkt[p[0][:4] + "-" + p[0][4:]] = float(p[1]) + float(p[6])
    return mkt


def load(zpath, sigs):
    z = zipfile.ZipFile(os.path.join(HERE, zpath))
    out = collections.defaultdict(lambda: collections.defaultdict(dict))
    nlong = collections.defaultdict(lambda: collections.defaultdict(dict))
    allsigs = set()
    with z.open(z.namelist()[0]) as f:
        for row in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8")):
            allsigs.add(row["signalname"])
            if row["signalname"] not in sigs or row["ret"] in ("NA", ""):
                continue
            out[row["signalname"]][row["port"]][row["date"][:7]] = float(row["ret"])
            if row.get("Nlong") not in (None, "", "NA"):
                nlong[row["signalname"]][row["port"]][row["date"][:7]] = int(row["Nlong"])
    return out, nlong, allsigs


WINDOWS = [
    ("in_sample_1963_07_2010_12", "1963-07", "2010-12"),
    ("post_sample_pre_pub_2011_2013", "2011-01", "2013-12"),
    ("post_publication_2014_2024", "2014-01", "2024-12"),
    ("programme_window_2010_2024", "2010-01", "2024-12"),
    ("last_five_2020_2024", "2020-01", "2024-12"),
]

mkt = load_ff5_mkt()
SIGS = {"GP", "CBOperProf", "OperProf", "OperProfRD"}
OUT = {}

for label, zf, sigs in [("PLACEBO_GPlag", "C4_CZ_PlaceboPortsFull.zip", {"GPlag", "GP"}),
                        ("QuintilesEW", "C4_CZ_QuintilesEW.zip", SIGS),
                        ("QuintilesVW", "C4_CZ_QuintilesVW.zip", SIGS)]:
    ap, nl, allsigs = load(zf, sigs)
    blk = {"_n_signals_in_file": len(allsigs),
           "_negative_control_bogus_signal_rows": 0 if "ThisSignalCannotExist" not in allsigs else -1,
           "_requested_present": sorted(s for s in sigs if s in ap)}
    for sig in sorted(ap):
        ports = sorted(p for p in ap[sig] if p != "LS")
        if not ports:
            continue
        lp, sp = ports[-1], ports[0]
        d = {"n_bins": len(ports), "long_port": lp, "short_port": sp}
        for nm, lo, hi in WINDOWS:
            months = sorted(k for k in ap[sig][lp] if lo <= k <= hi and k in mkt and k in ap[sig][sp])
            if len(months) < 3:
                continue
            lmm = [ap[sig][lp][k] - mkt[k] for k in months]
            ls = [ap[sig][lp][k] - ap[sig][sp][k] for k in months]
            sm = [ap[sig][sp][k] - mkt[k] for k in months]
            m1, t1, n1 = tstat(lmm); m2, t2, _ = tstat(ls); m3, t3, _ = tstat(sm)
            nn = [nl[sig][lp][k] for k in months if k in nl[sig][lp]]
            d[nm] = {"long_minus_mkt": round(m1, 4), "t_LmM": round(t1, 2),
                     "LS": round(m2, 4), "t_LS": round(t2, 2),
                     "short_minus_mkt": round(m3, 4), "t_SmM": round(t3, 2),
                     "n_months": n1,
                     "avg_N_long": round(sum(nn) / len(nn), 1) if nn else None}
        blk[sig] = d
    OUT[label] = blk

print(json.dumps(OUT, indent=1))
json.dump(OUT, open(os.path.join(HERE, "C4_deflator_ew.json"), "w"), indent=1)
