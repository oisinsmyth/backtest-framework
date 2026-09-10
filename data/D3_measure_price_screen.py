"""D3 [MEASURED IN BRIEF] part 2 -- does the $5 price screen bind, and what does the
price-screened (original-paper-construction) file say about GP vs OperProf?

Same endpoints as D3_measure_same_signal.py.
NOTE on the file: CZ's 30_PredictorAltPorts.R builds LiqScreen_Price_gt_5 with
`mutate(filterstr="abs(prc) > 5")` only, so each signal keeps its SignalDoc construction --
GP = VW quintiles, OperProf = EW quintiles. The file is therefore NOT construction-matched
across signals; it is reported here because it is the file that carries the programme's own
$5 floor, and because lane C4 recorded it.
"""
import csv, io, json, math, os, zipfile, collections

HERE = os.path.dirname(os.path.abspath(__file__))


def tstat(xs):
    n = len(xs)
    m = sum(xs) / n
    v = sum((x - m) ** 2 for x in xs) / (n - 1)
    se = math.sqrt(v / n)
    return m, m / se, n


def corr(xs, ys):
    n = len(xs); mx = sum(xs) / n; my = sum(ys) / n
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs)); sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)


def load(zname, signals):
    z = zipfile.ZipFile(os.path.join(HERE, zname))
    m = z.namelist()[0]
    out = collections.defaultdict(lambda: collections.defaultdict(dict))
    nbad = 0
    with z.open(m) as f:
        for row in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8")):
            if row["signalname"] not in signals:
                continue
            v = row["ret"]
            if v in ("NA", ""):
                nbad += 1
                continue
            out[row["signalname"]][row["port"]][row["date"]] = float(v)
    return out, nbad


SIGS = {"GP", "OperProf", "OperProfRD", "CBOperProf"}
p5, bad5 = load("D3_CZ_AltPorts_Price_gt_5.zip", SIGS)
ew, badew = load("D3_CZ_QuintilesEW.zip", SIGS)
print("NA returns dropped: price_gt_5 %d   quintilesEW %d" % (bad5, badew))

res = {}
print("\n=== how much does the $5 screen move GP's own series? (both files, GP) ===")
for s in ("GP", "OperProf"):
    ds = sorted(set(p5[s]["LS"]) & set(ew[s]["LS"]))
    a = [p5[s]["LS"][d] for d in ds]
    b = [ew[s]["LS"][d] for d in ds]
    c = corr(a, b)
    mx = max(abs(x - y) for x, y in zip(a, b))
    print("  %-9s corr(price>5 file, forcedEW file) = %+0.4f   max|diff| = %.4f   n=%d" % (s, c, mx, len(ds)))
    res["screen_%s" % s] = {"corr": c, "maxabsdiff": mx, "n": len(ds)}

print("\n=== price>5 file, ORIGINAL-PAPER construction per signal (GP=VW, OperProf=EW) ===")
for lo, lbl in ((None, "full overlap"), ("2010-01-01", "2010-01 onward"), ("2014-01-01", "2014-01 onward")):
    print("[%s]" % lbl)
    row = {}
    for s in ("GP", "OperProf", "OperProfRD", "CBOperProf"):
        ports = p5[s]
        qs = sorted(k for k in ports if k != "LS")
        ds = sorted(set.intersection(*[set(ports[q]) for q in qs]))
        if lo:
            ds = [d for d in ds if d >= lo]
        uni = {d: sum(ports[q][d] for q in qs) / len(qs) for d in ds}
        ex = [ports[qs[-1]][d] - uni[d] for d in ds]
        m, t, n = tstat(ex)
        ls = [ports["LS"][d] for d in sorted(ports["LS"]) if (not lo or d >= lo)]
        ml, tl, nl = tstat(ls)
        print("   %-12s nq=%2d  long-uni %+0.4f [t %+0.2f, n %d]   LS %+0.4f [t %+0.2f]" % (s, len(qs), m, t, n, ml, tl))
        row[s] = {"nq": len(qs), "long_minus_uni": m, "t": t, "n": n, "LS": ml, "LS_t": tl}
    res["price5_%s" % lbl] = row
    ds = sorted(set(p5["GP"]["LS"]) & set(p5["OperProf"]["LS"]))
    if lo:
        ds = [d for d in ds if d >= lo]
    print("   corr(GP LS, OperProf LS) = %+0.4f  n=%d" % (corr([p5["GP"]["LS"][d] for d in ds], [p5["OperProf"]["LS"][d] for d in ds]), len(ds)))

json.dump(res, open(os.path.join(HERE, "D3_price_screen_measurement.json"), "w"), indent=1, default=str)
print("\nwrote D3_price_screen_measurement.json")
