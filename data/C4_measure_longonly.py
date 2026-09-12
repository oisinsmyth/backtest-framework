"""C4 [MEASURED IN BRIEF] -- the LONG LEG of gross profitability against the market, pre/post publication.

Joins Chen-Zimmermann PredictorAltPorts (liquidity-screened) to Ken French's
F-F_Research_Data_5_Factors_2x3 (Mkt-RF + RF = the CRSP value-weighted market total return),
because a long leg's RAW return is not an alpha and the programme is long-only.
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
    return m, (m / se if se > 0 else None), n


def load_ff5():
    z = zipfile.ZipFile(os.path.join(HERE, "C4_F-F_Research_Data_5_Factors_2x3_CSV.zip"))
    txt = z.read(z.namelist()[0]).decode("latin-1").splitlines()
    mkt, fac = {}, {}
    started = False
    for line in txt:
        s = line.strip()
        if s.startswith(",Mkt-RF"):
            started = True
            continue
        if not started:
            continue
        parts = [p.strip() for p in s.split(",")]
        if len(parts) < 7 or len(parts[0]) != 6 or not parts[0].isdigit():
            if started and parts[0] and not parts[0].isdigit():
                break
            continue
        ym = parts[0][:4] + "-" + parts[0][4:]
        v = [float(x) for x in parts[1:7]]
        mkt[ym] = v[0] + v[5]           # Mkt-RF + RF = market total return, percent
        fac[ym] = dict(zip(["MktRF", "SMB", "HML", "RMW", "CMA", "RF"], v))
    return mkt, fac


def load_altport_sig(zpath, sig):
    z = zipfile.ZipFile(os.path.join(HERE, zpath))
    out = collections.defaultdict(dict)
    with z.open(z.namelist()[0]) as f:
        r = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8"))
        for row in r:
            if row["signalname"] != sig or row["ret"] in ("NA", ""):
                continue
            out[row["port"]][row["date"][:7]] = float(row["ret"])
    return out


WINDOWS = [
    ("in_sample_1963_07_2010_12", "1963-07", "2010-12"),
    ("post_sample_pre_pub_2011_2013", "2011-01", "2013-12"),
    ("post_publication_2014_2024", "2014-01", "2024-12"),
    ("programme_window_2010_2024", "2010-01", "2024-12"),
    ("last_five_2020_2024", "2020-01", "2024-12"),
]

mkt, fac = load_ff5()
OUT = {"market_series": {"source": "F-F_Research_Data_5_Factors_2x3, Mkt-RF + RF",
                         "first": min(mkt), "last": max(mkt), "n": len(mkt)}}

# ---- negative / positive controls on the join ----
ctrl = {}
ctrl["C4_market_mean_1963_07_2024_12_pct_mo"] = round(
    sum(v for k, v in mkt.items() if "1963-07" <= k <= "2024-12") /
    sum(1 for k in mkt if "1963-07" <= k <= "2024-12"), 4)
ctrl["C5_market_minus_itself_max_abs"] = max(abs(mkt[k] - mkt[k]) for k in mkt)
ctrl["C6_months_in_1800s"] = sum(1 for k in mkt if k < "1900-01")  # must be 0

res = {}
for label, zf in [("price_gt_5", "C4_CZ_price_gt5.zip"),
                  ("ME_gt_NYSE20pct", "C4_CZ_me_nyse20.zip")]:
    res[label] = {}
    for sig in ["GP", "CBOperProf", "OperProf", "OperProfRD"]:
        ap = load_altport_sig(zf, sig)
        ports = sorted(p for p in ap if p != "LS")
        lp, sp = ports[-1], ports[0]
        blk = {"long_port": lp, "short_port": sp}
        for nm, lo, hi in WINDOWS:
            months = sorted(k for k in ap[lp] if lo <= k <= hi and k in mkt)
            lmm = [ap[lp][k] - mkt[k] for k in months]
            smm = [ap[sp][k] - mkt[k] for k in months]
            ls = [ap[lp][k] - ap[sp][k] for k in months]
            m1, t1, n1 = tstat(lmm); m2, t2, _ = tstat(smm); m3, t3, _ = tstat(ls)
            blk[nm] = {"long_minus_mkt_pct_mo": m1, "t": t1, "n_months": n1,
                       "short_minus_mkt_pct_mo": m2, "t_short": t2,
                       "LS_pct_mo": m3, "t_LS": t3,
                       "share_of_LS_in_long_leg": (m1 / m3) if m3 else None}
        # yearly shape of long-minus-market, post-publication
        yr = collections.defaultdict(list)
        for k in sorted(ap[lp]):
            if k in mkt and k >= "2010-01":
                yr[k[:4]].append(ap[lp][k] - mkt[k])
        blk["yearly_long_minus_mkt_pct_mo_2010on"] = {y: round(sum(v) / len(v), 3) for y, v in sorted(yr.items())}
        yr2 = collections.defaultdict(list)
        for k in sorted(ap[lp]):
            if k in ap[sp] and k >= "2010-01":
                yr2[k[:4]].append(ap[lp][k] - ap[sp][k])
        blk["yearly_LS_pct_mo_2010on"] = {y: round(sum(v) / len(v), 3) for y, v in sorted(yr2.items())}
        # the single largest month of the post-2013 long-short, named
        post = [(k, ap[lp][k] - ap[sp][k]) for k in sorted(ap[lp]) if k >= "2013-01" and k in ap[sp]]
        post_sorted = sorted(post, key=lambda x: -x[1])
        tot = sum(v for _, v in post)
        blk["largest_post2013_LS_months"] = [{"month": k, "LS_pct": round(v, 2),
                                              "share_of_post2013_sum": round(v / tot, 3) if tot else None}
                                             for k, v in post_sorted[:5]]
        blk["most_negative_post2013_LS_months"] = [{"month": k, "LS_pct": round(v, 2)} for k, v in post_sorted[-3:]]
        blk["post2013_n_months"] = len(post)
        res[label][sig] = blk

OUT["long_only_view"] = res

# ---- the era-vs-publication discriminator on French factors ----
# HML/SMB published 1992-93; RMW/CMA published 2015; Mkt is not an anomaly.
def fwin(key, lo, hi):
    xs = [fac[k][key] for k in sorted(fac) if lo <= k <= hi]
    return tstat(xs)


era = {}
for key in ["MktRF", "SMB", "HML", "RMW", "CMA"]:
    era[key] = {}
    for nm, lo, hi in [("1963_07_2010_12", "1963-07", "2010-12"),
                       ("1963_07_2013_06", "1963-07", "2013-06"),
                       ("2013_07_2026_07", "2013-07", "2026-07"),
                       ("2010_01_2026_07", "2010-01", "2026-07"),
                       ("2020_01_2026_07", "2020-01", "2026-07")]:
        m, t, n = fwin(key, lo, hi)
        era[key][nm] = {"mean_pct_mo": round(m, 4) if m is not None else None,
                        "t": round(t, 2) if t is not None else None, "n": n}
OUT["era_discriminator_french_factors"] = era
OUT["controls"] = ctrl

print(json.dumps(OUT, indent=1, default=str))
with open(os.path.join(HERE, "C4_longonly_measurement.json"), "w") as f:
    json.dump(OUT, f, indent=1, default=str)
