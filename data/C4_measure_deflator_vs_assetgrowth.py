"""C4 [MEASURED IN BRIEF] -- is the current-asset deflator's long-leg increment the ASSET GROWTH
anomaly's return?

GP/AT == (GP/AT_-1) / (AT/AT_-1) is an identity (R2-02 section 2.2). This asks the separate
question of whether the RETURN increment from using current assets is the investment anomaly's
realised return. Answer: no -- corr(increment, AssetGrowth long leg) = -0.106 in-sample and
-0.294 post-publication, small and the wrong sign.

Endpoints: PredictorAltPorts_QuintilesEW.zip (drive id 1KjptjrRi96ko_tR8zFjXCyYfNlyiHGiI) and
PlaceboPortsFull.zip (1ciopYrT7e9tzKCt8f1he6uwJFiaD1ZkE) from openassetpricing.com's Drive;
SignalDoc.csv from raw.githubusercontent.com/OpenSourceAP/CrossSection/master/SignalDoc.csv.
"""
import csv, io, json, math, os, zipfile, collections

HERE = os.path.dirname(os.path.abspath(__file__))


def load(z, sigs):
    zf = zipfile.ZipFile(os.path.join(HERE, z))
    out = collections.defaultdict(lambda: collections.defaultdict(dict))
    with zf.open(zf.namelist()[0]) as f:
        for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8")):
            if r["signalname"] in sigs and r["ret"] not in ("NA", ""):
                out[r["signalname"]][r["port"]][r["date"][:7]] = float(r["ret"])
    return out


def ts(xs):
    n = len(xs)
    m = sum(xs) / n
    v = sum((x - m) ** 2 for x in xs) / (n - 1)
    return m, m / math.sqrt(v / n), n


def corr(x, y):
    n = len(x)
    mx = sum(x) / n
    my = sum(y) / n
    sx = math.sqrt(sum((a - mx) ** 2 for a in x))
    sy = math.sqrt(sum((b - my) ** 2 for b in y))
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)


def lmu(d):
    """long leg minus the sort's own universe, and the long-short, from a 5-bin file."""
    ports = sorted(p for p in d if p != "LS")
    ms = sorted(set.intersection(*[set(d[p]) for p in ports]))
    uni = {k: sum(d[p][k] for p in ports) / len(ports) for k in ms}
    return ({k: d[ports[-1]][k] - uni[k] for k in ms},
            {k: d[ports[-1]][k] - d[ports[0]][k] for k in ms})


ew = load("C4_CZ_QuintilesEW.zip", {"GP", "AssetGrowth"})
gp_l, _ = lmu(ew["GP"])
ag_l, ag_ls = lmu(ew["AssetGrowth"])
gl_l, _ = lmu(load("C4_CZ_PlaceboPortsFull.zip", {"GPlag"})["GPlag"])
sd = {r["Acronym"]: r for r in csv.DictReader(
    open(os.path.join(HERE, "C4_SignalDoc.csv"), encoding="utf-8-sig"))}

OUT = {"AssetGrowth_signaldoc": {k: sd["AssetGrowth"][k] for k in
                                 ("Sign", "Return", "T-Stat", "SampleEndYear", "Year", "Stock Weight")},
       "note": "CZ's portfolio bins are already oriented by Sign, so bin 05 is the predicted-high-return "
               "bin; for AssetGrowth (Sign -1) that is the LOW-asset-growth leg, which is the tradeable one.",
       "windows": {}}

ks = sorted(set(gp_l) & set(gl_l) & set(ag_l))
for lab, lo, hi in [("in_sample_1963_07_2010_12", "1963-07", "2010-12"),
                    ("post_pub_2014_2024", "2014-01", "2024-12"),
                    ("programme_window_2010_2024", "2010-01", "2024-12")]:
    k = [x for x in ks if lo <= x <= hi]
    delta = [gp_l[x] - gl_l[x] for x in k]
    agl = [ag_l[x] for x in k]
    agls = [ag_ls[x] for x in k]
    m, t, n = ts(delta)
    ma, ta, _ = ts(agl)
    ml, tl, _ = ts(agls)
    OUT["windows"][lab] = {
        "deflator_increment_GP_minus_GPlag": round(m, 4), "t": round(t, 2),
        "AssetGrowth_long_minus_own_universe": round(ma, 4), "t_AG_long": round(ta, 2),
        "AssetGrowth_LS": round(ml, 4), "t_AG_LS": round(tl, 2),
        "corr_increment_with_AG_long": round(corr(delta, agl), 4),
        "corr_increment_with_AG_LS": round(corr(delta, agls), 4),
        "n_months": n}

print(json.dumps(OUT, indent=1))
json.dump(OUT, open(os.path.join(HERE, "C4_deflator_vs_assetgrowth.json"), "w"), indent=1)
