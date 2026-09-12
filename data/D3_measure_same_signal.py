"""D3 [MEASURED IN BRIEF] -- are gross-profits-to-assets and operating-profits-to-book-equity
the same signal, measured INSIDE ONE DATASET with construction HELD FIXED?

Endpoints (all Chen-Zimmermann v2.0.0 / release 2025.10, Google Drive, ids from the
openassetpricing.com "Portfolios / Full Sets Alt" folder listing decoded from _DRIVE_ivd):
  1KjptjrRi96ko_tR8zFjXCyYfNlyiHGiI  PredictorAltPorts_QuintilesEW.zip   18,290,738 B sha1 4d9f4dfd4828
  1ef905SSlCDyh1KU9W1tJs5sfBFz0HPUt  PredictorAltPorts_QuintilesVW.zip   18,947,238 B sha1 12fb2eaa34c6
  1pFBX0LTyoSwH7i8mT4kPCS_3QghlbODD  PredictorAltPorts_DecilesEW.zip     32,544,201 B sha1 18b7d1dfb2a4
  1mL44YJHwiLt_ZRdjmiU7-_i4QVtWURLD  PredictorAltPorts_LiqScreen_Price_gt_5.zip 24,987,135 B sha1 278eb1e42c73
  10sOryk_ddjkXagaajTKUk1nwJs2ZLRiI  PredictorLSretWide.csv               3,293,172 B sha1 71fe880a8923
The last two byte counts and sha1 prefixes match lane C4's recorded provenance exactly.

Why the forced-construction files: CZ's code 30_PredictorAltPorts.R builds the LiqScreen files
with `mutate(filterstr=...)` only -- each signal KEEPS its original-paper weighting and quantile
cut (SignalDoc: GP = VW quintiles, OperProf = EW, OperProfRD = VW deciles NYSE). The
Quintiles*/Deciles* files instead force `q_cut` and `sweight` for every continuous predictor, so
they are the only CZ files in which GP and OperProf share a construction.
"""
import csv, io, json, math, os, sys, zipfile, collections

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = {}
FAIL = []


def tstat(xs):
    n = len(xs)
    if n < 3:
        return None, None, n
    m = sum(xs) / n
    v = sum((x - m) ** 2 for x in xs) / (n - 1)
    se = math.sqrt(v / n)
    return m, (m / se if se > 0 else None), n


def corr(xs, ys):
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if sx == 0 or sy == 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)


def load_ports(zname, signals):
    """-> {signal: {port: {date: ret}}}, plus diagnostics. Sentinel census included."""
    z = zipfile.ZipFile(os.path.join(HERE, zname))
    member = z.namelist()[0]
    out = collections.defaultdict(lambda: collections.defaultdict(dict))
    diag = {"member": member, "rows": 0, "na_ret": 0, "le_minus99": 0,
            "nonfinite": 0, "rows_kept": 0, "ports_seen": collections.Counter()}
    want = set(signals)
    with z.open(member) as f:
        r = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8"))
        for row in r:
            diag["rows"] += 1
            if row["signalname"] not in want:
                continue
            v = row["ret"]
            if v in ("NA", "", "NaN", None):
                diag["na_ret"] += 1
                continue
            x = float(v)
            if not math.isfinite(x):
                diag["nonfinite"] += 1
                continue
            if x <= -99.0:                      # French-style sentinel census on a non-French file
                diag["le_minus99"] += 1
                continue
            out[row["signalname"]][row["port"]][row["date"]] = x
            diag["rows_kept"] += 1
            diag["ports_seen"][(row["signalname"], row["port"])] += 1
    diag["ports_seen"] = {"%s|%s" % k: v for k, v in sorted(diag["ports_seen"].items())}
    return out, diag


def paired(a, b, lo=None, hi=None):
    """Pair STRICTLY on equal date keys. Returns (dates, xs, ys)."""
    ds = sorted(set(a) & set(b))
    if lo:
        ds = [d for d in ds if d >= lo]
    if hi:
        ds = [d for d in ds if d <= hi]
    return ds, [a[d] for d in ds], [b[d] for d in ds]


def universe(ports, portnames):
    """EW average of the quantile portfolios = the sort's own equal-weighted universe,
    on dates where EVERY quantile is present."""
    sets = [set(ports[p]) for p in portnames]
    ds = sorted(set.intersection(*sets))
    return {d: sum(ports[p][d] for p in portnames) / len(portnames) for d in ds}


def block(label, ports, sigA, sigB, topport, allports, era):
    res = {}
    lo, hi = era
    for obj, getter in (("LS", lambda s: ports[s]["LS"]),
                        ("long", lambda s: ports[s][topport])):
        ds, xs, ys = paired(getter(sigA), getter(sigB), lo, hi)
        res["corr_%s" % obj] = corr(xs, ys)
        res["n_%s" % obj] = len(ds)
        res["dates_%s" % obj] = (ds[0], ds[-1]) if ds else None
    for s in (sigA, sigB):
        uni = universe(ports[s], allports)
        ds, xs, us = paired(ports[s][topport], uni, lo, hi)
        ex = [x - u for x, u in zip(xs, us)]
        m, t, n = tstat(ex)
        res["%s_longminusuni_mean" % s] = m
        res["%s_longminusuni_t" % s] = t
        res["%s_longminusuni_n" % s] = n
        mr, tr, _ = tstat(xs)
        mu, tu, _ = tstat(us)
        res["%s_long_mean" % s] = mr
        res["%s_uni_mean" % s] = mu
        ml, tl, nl = tstat([ports[s]["LS"][d] for d in sorted(ports[s]["LS"]) if (not lo or d >= lo) and (not hi or d <= hi)])
        res["%s_LS_mean" % s] = ml
        res["%s_LS_t" % s] = tl
        res["%s_LS_n" % s] = nl
    OUT[label] = res
    return res


SIGS = ["GP", "OperProf", "OperProfRD", "CBOperProf", "AssetGrowth", "BM", "Mom12m", "Beta"]

print("=" * 100)
print("D3 [MEASURED IN BRIEF]  GP (gross profits / assets) vs OperProf (operating profits / book equity)")
print("=" * 100)

FILES = [("D3_CZ_QuintilesEW.zip", "quintilesEW", "05", ["01", "02", "03", "04", "05"]),
         ("D3_CZ_QuintilesVW.zip", "quintilesVW", "05", ["01", "02", "03", "04", "05"]),
         ("D3_CZ_DecilesEW.zip", "decilesEW", "10", ["%02d" % i for i in range(1, 11)]),
         ("D3_CZ_AltPorts_Price_gt_5.zip", "price_gt_5_OPconstruction", None, None)]

loaded = {}
for zname, tag, topport, allports in FILES:
    ports, diag = load_ports(zname, SIGS)
    loaded[tag] = (ports, topport, allports)
    OUT["diag_" + tag] = diag
    print("\n--- %s (%s) ---" % (tag, zname))
    print("   rows=%d kept=%d  NA_ret=%d  nonfinite=%d  ret<=-99=%d" %
          (diag["rows"], diag["rows_kept"], diag["na_ret"], diag["nonfinite"], diag["le_minus99"]))
    print("   ports present:", {k: v for k, v in diag["ports_seen"].items() if k.split("|")[0] in ("GP", "OperProf")})

# ---------------------------------------------------------------- CONTROLS
print("\n" + "=" * 100)
print("CONTROLS")
print("=" * 100)

# P2 identity: LS must equal top minus bottom, to machine precision, in every forced file.
for tag in ("quintilesEW", "quintilesVW", "decilesEW"):
    ports, topport, allports = loaded[tag]
    for s in ("GP", "OperProf"):
        ds, ls, _ = paired(ports[s]["LS"], ports[s][topport])
        mx = 0.0
        for d in ds:
            mx = max(mx, abs(ports[s]["LS"][d] - (ports[s][topport][d] - ports[s][allports[0]][d])))
        OUT["P2_identity_%s_%s" % (tag, s)] = mx
        ok = mx < 1e-9
        print("P2 identity  %-12s %-9s  max|LS-(top-bottom)| = %.3e  %s" % (tag, s, mx, "PASS" if ok else "**FAIL**"))
        if not ok:
            FAIL.append("P2 %s %s" % (tag, s))

# N3a self-correlation must be exactly 1.0; N3b one-month-shifted must NOT be 1.0.
ports, topport, allports = loaded["quintilesEW"]
gp = ports["GP"]["LS"]
ds = sorted(gp)
self_c = corr([gp[d] for d in ds], [gp[d] for d in ds])
shifted = {ds[i]: gp[ds[i + 1]] for i in range(len(ds) - 1)}
dsh, a, b = paired(gp, shifted)
shift_c = corr(a, b)
OUT["N3_self_corr"] = self_c
OUT["N3_shift1_corr"] = shift_c
print("N3 self-corr(GP,GP) = %.12f   %s" % (self_c, "PASS" if abs(self_c - 1.0) < 1e-12 else "**FAIL**"))
print("N3 corr(GP, GP shifted 1m) = %.4f   %s (a 1.0 here would mean my date keys are ignored)"
      % (shift_c, "PASS" if abs(shift_c - 1.0) > 0.2 else "**FAIL**"))
if abs(self_c - 1.0) >= 1e-12 or abs(shift_c - 1.0) <= 0.2:
    FAIL.append("N3")

# N3c DELIBERATE BREAK: the identity check must FIRE on a corrupted book.
broken = {d: v for d, v in ports["GP"]["LS"].items()}
kd = sorted(broken)[100]
broken[kd] = broken[kd] + 1.0
mx = max(abs(broken[d] - (ports["GP"]["05"][d] - ports["GP"]["01"][d])) for d in sorted(broken))
OUT["N3c_break_fires"] = mx
print("N3c deliberate break (one month +1.00): identity check now max = %.4f -> %s"
      % (mx, "FIRES (good)" if mx > 1e-9 else "**DID NOT FIRE -- the check is useless**"))
if mx <= 1e-9:
    FAIL.append("N3c")

# N4 EW vs VW must differ: if the forced files were the same file, the whole measurement is void.
pew = loaded["quintilesEW"][0]["GP"]["LS"]
pvw = loaded["quintilesVW"][0]["GP"]["LS"]
ds, a, b = paired(pew, pvw)
OUT["N4_EWvsVW_corr"] = corr(a, b)
OUT["N4_EWvsVW_maxabsdiff"] = max(abs(x - y) for x, y in zip(a, b))
print("N4 GP LS: corr(EWfile, VWfile) = %.4f  max|diff| = %.4f  %s"
      % (OUT["N4_EWvsVW_corr"], OUT["N4_EWvsVW_maxabsdiff"],
         "PASS (files differ)" if OUT["N4_EWvsVW_maxabsdiff"] > 1e-6 else "**FAIL**"))
if OUT["N4_EWvsVW_maxabsdiff"] <= 1e-6:
    FAIL.append("N4")

# P1 positive control: reproduce CZ's own published GP figure from the LSretWide file.
wide = {}
with open(os.path.join(HERE, "D3_CZ_monthly_LS.csv"), encoding="utf-8") as f:
    r = csv.reader(f)
    hdr = next(r)
    idx = {c: i for i, c in enumerate(hdr)}
    for row in r:
        d = row[0]
        for s in ("GP", "OperProf"):
            v = row[idx[s]]
            if v not in ("NA", ""):
                wide.setdefault(s, {})[d] = float(v)
doc = {r["Acronym"]: r for r in csv.DictReader(open(os.path.join(HERE, "D3_SignalDoc.csv"), encoding="utf-8-sig"))}
for s, claim in (("GP", (0.31, 2.49)), ("OperProf", (None, 2.55))):
    d0 = "%s-07-31" % doc[s]["SampleStartYear"][:4]
    d1 = "%s-12-31" % doc[s]["SampleEndYear"][:4]
    xs = [v for d, v in sorted(wide[s].items()) if d0 <= d <= d1]
    m, t, n = tstat(xs)
    OUT["P1_%s" % s] = {"mean": m, "t": t, "n": n, "window": [d0, d1],
                        "SignalDoc_Return": doc[s]["Return"], "SignalDoc_T": doc[s]["T-Stat"]}
    print("P1 %-9s original-paper construction %s..%s  n=%3d  mean=%.4f t=%.2f  | SignalDoc says Return=%s T=%s"
          % (s, d0, d1, n, m, t, doc[s]["Return"] or "-", doc[s]["T-Stat"] or "-"))

# N1 negative control: a non-profitability predictor, same file, same construction.
ports, topport, allports = loaded["quintilesEW"]
for other in ("AssetGrowth", "BM", "Mom12m", "Beta"):
    if other not in ports:
        continue
    ds, a, b = paired(ports["GP"]["LS"], ports[other]["LS"])
    OUT["N1_corr_GP_%s" % other] = {"corr": corr(a, b), "n": len(ds)}
    print("N1 corr(GP LS, %-12s LS) = %+0.4f  n=%d" % (other, corr(a, b), len(ds)))

# ---------------------------------------------------------------- MEASUREMENTS
print("\n" + "=" * 100)
print("MEASUREMENTS -- construction held fixed, both signals, one dataset")
print("=" * 100)
for tag in ("quintilesEW", "decilesEW", "quintilesVW"):
    ports, topport, allports = loaded[tag]
    for era, lbl in (((None, None), "full overlap"), (("2010-01-01", None), "2010-01 onward"),
                     (("2014-01-01", None), "2014-01 onward")):
        r = block("%s|%s" % (tag, lbl), ports, "GP", "OperProf", topport, allports, era)
        print("\n[%s, %s]" % (tag, lbl))
        print("  corr(GP, OperProf)  long-short %+0.4f (n=%d)   long leg %+0.4f (n=%d)"
              % (r["corr_LS"], r["n_LS"], r["corr_long"], r["n_long"]))
        for s in ("GP", "OperProf"):
            print("   %-9s  LS %+0.4f [t %+0.2f, n %d]   long %+0.4f   uni %+0.4f   long-uni %+0.4f [t %+0.2f, n %d]"
                  % (s, r["%s_LS_mean" % s], r["%s_LS_t" % s], r["%s_LS_n" % s],
                     r["%s_long_mean" % s], r["%s_uni_mean" % s],
                     r["%s_longminusuni_mean" % s], r["%s_longminusuni_t" % s], r["%s_longminusuni_n" % s]))

# extra family members, EW quintiles, 2010+
ports, topport, allports = loaded["quintilesEW"]
print("\n[quintilesEW, all four family members, long leg minus own EW universe]")
for era, lbl in (((None, None), "full"), (("2010-01-01", None), "2010+")):
    lo, hi = era
    row = {}
    for s in ("GP", "OperProf", "OperProfRD", "CBOperProf"):
        if s not in ports or "LS" not in ports[s]:
            continue
        uni = universe(ports[s], allports)
        ds, xs, us = paired(ports[s][topport], uni, lo, hi)
        m, t, n = tstat([x - u for x, u in zip(xs, us)])
        ml, tl, nl = tstat([ports[s]["LS"][d] for d in sorted(ports[s]["LS"]) if (not lo or d >= lo)])
        row[s] = {"long_minus_uni": m, "t": t, "n": n, "LS": ml, "LS_t": tl}
        print("  %-12s %-6s  long-uni %+0.4f [t %+0.2f, n %d]   LS %+0.4f [t %+0.2f]" % (s, lbl, m, t, n, ml, tl))
    OUT["family_%s" % lbl] = row

# pairwise correlations among the four, EW quintiles, full overlap
print("\n[quintilesEW, pairwise LS correlations among family members, full overlap]")
fam = [s for s in ("GP", "OperProf", "OperProfRD", "CBOperProf") if s in ports]
pw = {}
for i in range(len(fam)):
    for j in range(i + 1, len(fam)):
        ds, a, b = paired(ports[fam[i]]["LS"], ports[fam[j]]["LS"])
        pw["%s~%s" % (fam[i], fam[j])] = {"corr": corr(a, b), "n": len(ds)}
        print("  %-12s ~ %-12s  %+0.4f  (n=%d)" % (fam[i], fam[j], corr(a, b), len(ds)))
OUT["family_pairwise_LS_corr"] = pw

print("\n" + "=" * 100)
print("CONTROL SUMMARY: %s" % ("ALL PASS" if not FAIL else "FAILURES: %s" % FAIL))
print("=" * 100)
OUT["control_failures"] = FAIL
json.dump(OUT, open(os.path.join(HERE, "D3_same_signal_measurement.json"), "w"), indent=1, default=str)
print("wrote D3_same_signal_measurement.json")
