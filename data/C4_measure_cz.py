"""C4 [MEASURED IN BRIEF] -- post-publication decay of gross profitability on Chen-Zimmermann data.

Endpoints:
  openassetpricing.com Google-Drive files (drive.usercontent.google.com/download?id=...):
    10sOryk_ddjkXagaajTKUk1nwJs2ZLRiI  monthly long-short returns, original-paper construction
    1mL44YJHwiLt_ZRdjmiU7-_i4QVtWURLD  PredictorAltPorts_LiqScreen_Price_gt_5
    1Q4YatQ3soRU_V7VeACwUn2bnCnmhDUI2  PredictorAltPorts_LiqScreen_ME_gt_NYSE20pct
  raw.githubusercontent.com/OpenSourceAP/CrossSection/master/SignalDoc.csv
All byte counts reproduce round 1's recorded counts exactly.
"""
import csv, io, json, math, os, zipfile, collections

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = {}


def tstat(xs):
    n = len(xs)
    if n < 3:
        return None, None, n
    m = sum(xs) / n
    v = sum((x - m) ** 2 for x in xs) / (n - 1)
    se = math.sqrt(v / n)
    return m, (m / se if se > 0 else None), n


def load_signaldoc():
    rows = list(csv.DictReader(open(os.path.join(HERE, "C4_SignalDoc.csv"), encoding="utf-8-sig")))
    return {r["Acronym"]: r for r in rows}


def load_monthly_ls():
    """original-paper construction, wide file: date + one column per predictor."""
    f = open(os.path.join(HERE, "C4_CZ_monthly_LS.csv"), encoding="utf-8")
    r = csv.reader(f)
    hdr = next(r)
    cols = hdr[1:]
    data = {c: {} for c in cols}
    for row in r:
        d = row[0]
        for c, v in zip(cols, row[1:]):
            if v not in ("NA", ""):
                data[c][d] = float(v)
    return data


def load_altport(zpath):
    """returns dict signal -> port -> {date: (ret, Nlong, Nshort)}"""
    z = zipfile.ZipFile(os.path.join(HERE, zpath))
    name = z.namelist()[0]
    out = collections.defaultdict(lambda: collections.defaultdict(dict))
    with z.open(name) as f:
        r = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8"))
        for row in r:
            if row["ret"] in ("NA", ""):
                continue
            out[row["signalname"]][row["port"]][row["date"]] = (
                float(row["ret"]),
                row.get("Nlong") or "",
                row.get("Nshort") or "",
            )
    return out


def window(series, lo, hi):
    """series: {date_str: val}; lo/hi inclusive 'YYYY-MM' bounds."""
    return [v for d, v in sorted(series.items()) if lo <= d[:7] <= hi]


WINDOWS = [
    ("in_sample_1963_2010", "1963-07", "2010-12"),
    ("post_sample_pre_pub_2011_2013", "2011-01", "2013-12"),
    ("post_publication_2014_2024", "2014-01", "2024-12"),
    ("post_pub_strict_2013_2024", "2013-05", "2024-12"),
    ("programme_window_2010_2024", "2010-01", "2024-12"),
    ("post_2005_2005_2024", "2005-01", "2024-12"),
    ("last_five_2020_2024", "2020-01", "2024-12"),
]

SIGS = ["GP", "CBOperProf", "OperProf", "OperProfRD"]

sd = load_signaldoc()
OUT["signaldoc"] = {
    s: {k: sd[s][k] for k in ("Authors", "Year", "Journal", "SampleStartYear", "SampleEndYear",
                              "Sign", "Return", "T-Stat", "Stock Weight", "LS Quantile",
                              "Portfolio Period", "Filter", "Cat.Signal")}
    for s in SIGS + (["GPlag"] if "GPlag" in sd else [])
}

# ---------- negative controls ----------
ctrl = {}
ctrl["C1_nonexistent_signal_rows"] = {"queried": "ThisSignalCannotExist", "rows": 0, "must_be": 0}
ctrl["C2_telepathy_category_rows"] = {
    "rows": sum(1 for r in sd.values() if r.get("Cat.Data") == "Telepathy"), "must_be": 0}

mls = load_monthly_ls()
ctrl["C1_nonexistent_signal_rows"]["rows"] = len(mls.get("ThisSignalCannotExist", {}))

# ---------- original-paper construction ----------
res = {}
for s in SIGS:
    res[s] = {}
    for nm, lo, hi in WINDOWS:
        xs = window(mls[s], lo, hi)
        m, t, n = tstat(xs)
        res[s][nm] = {"mean_pct_mo": m, "t": t, "n_months": n}
OUT["A_original_paper_construction"] = res

# reproduce the full-panel decay (MP-style) on the same file
panel = {}
for s, ser in mls.items():
    r = sd.get(s)
    if not r or r.get("Cat.Signal") != "Predictor":
        continue
    try:
        se = int(r["SampleEndYear"]); py = int(r["Year"])
    except Exception:
        continue
    ins = [v for d, v in ser.items() if d[:4] and int(d[:4]) <= se]
    post = [v for d, v in ser.items() if int(d[:4]) > py]
    post05 = [v for d, v in ser.items() if int(d[:4]) > py and d[:4] >= "2005"]
    mi, ti, ni = tstat(ins); mp_, tp, np_ = tstat(post); m5, t5, n5 = tstat(post05)
    if mi is None or mp_ is None or ni < 60 or np_ < 24:
        continue
    panel[s] = {"in_sample_mean": mi, "in_sample_t": ti, "in_sample_n": ni,
                "post_pub_mean": mp_, "post_pub_t": tp, "post_pub_n": np_,
                "post_pub_post2005_mean": m5, "post_pub_post2005_n": n5,
                "sample_end": se, "pub_year": py}
OUT["B_panel_decay"] = panel

# pooled decay: mean of (post/in) is unstable when in-sample is near zero; report
# the MP normalisation (each month's return divided by that signal's in-sample mean)
def pooled_ratio(key):
    num = []
    for s, d in panel.items():
        if d["in_sample_mean"] and d["in_sample_mean"] > 0.05:  # positive, non-degenerate
            num.append(d[key] / d["in_sample_mean"])
    num.sort()
    n = len(num)
    return {"n_signals": n, "mean_ratio": sum(num) / n if n else None,
            "median_ratio": num[n // 2] if n else None,
            "p25": num[n // 4] if n else None, "p75": num[3 * n // 4] if n else None}


OUT["C_pooled_decay_ratios"] = {
    "post_pub_over_in_sample": pooled_ratio("post_pub_mean"),
    "post_pub_post2005_over_in_sample": pooled_ratio("post_pub_post2005_mean"),
}
for s in SIGS:
    d = panel.get(s)
    if d:
        OUT["C_pooled_decay_ratios"].setdefault("focal_signal_ratios", {})[s] = {
            "post_pub_over_in": d["post_pub_mean"] / d["in_sample_mean"] if d["in_sample_mean"] else None,
            "post_pub_post2005_over_in": d["post_pub_post2005_mean"] / d["in_sample_mean"] if d["in_sample_mean"] else None,
        }
        # percentile of GP's ratio within the panel
        rs = sorted(dd["post_pub_mean"] / dd["in_sample_mean"] for dd in panel.values()
                    if dd["in_sample_mean"] and dd["in_sample_mean"] > 0.05)
        myr = d["post_pub_mean"] / d["in_sample_mean"] if d["in_sample_mean"] else None
        if myr is not None:
            OUT["C_pooled_decay_ratios"]["focal_signal_ratios"][s]["percentile_in_panel"] = \
                round(100.0 * sum(1 for x in rs if x < myr) / len(rs), 1)

# ---------- alt universes: legs, not just spread ----------
for label, zf in [("price_gt_5", "C4_CZ_price_gt5.zip"),
                  ("ME_gt_NYSE20pct", "C4_CZ_me_nyse20.zip")]:
    ap = load_altport(zf)
    blk = {}
    for s in SIGS:
        ports = sorted(p for p in ap[s].keys() if p != "LS")
        hi_p, lo_p = ports[-1], ports[0]
        sign = sd[s].get("Sign", "1")
        long_p, short_p = (hi_p, lo_p) if str(sign).strip() in ("1", "1.0", "") else (lo_p, hi_p)
        blk[s] = {"n_bins": len(ports), "long_port": long_p, "short_port": short_p, "sign": sign}
        for nm, lo, hi in WINDOWS:
            ls = window({d: v[0] for d, v in ap[s]["LS"].items()}, lo, hi)
            lg = window({d: v[0] for d, v in ap[s][long_p].items()}, lo, hi)
            sh = window({d: v[0] for d, v in ap[s][short_p].items()}, lo, hi)
            mls_, tls, nls = tstat(ls)
            mlg, tlg, nlg = tstat(lg)
            msh, tsh, nsh = tstat(sh)
            # breadth: names in the long bin
            nlong = [int(v[1]) for d, v in ap[s][long_p].items() if lo <= d[:7] <= hi and v[1] not in ("", "NA")]
            blk[s][nm] = {
                "LS_mean": mls_, "LS_t": tls, "n_months": nls,
                "long_mean": mlg, "long_t": tlg,
                "short_mean": msh, "short_t": tsh,
                "long_minus_short_check": (mlg - msh) if (mlg is not None and msh is not None) else None,
                "avg_names_in_long_bin": (sum(nlong) / len(nlong)) if nlong else None,
            }
        # negative control: a portfolio minus itself must be exactly zero
        same = [a - b for a, b in zip(window({d: v[0] for d, v in ap[s][long_p].items()}, "1963-07", "2024-12"),
                                     window({d: v[0] for d, v in ap[s][long_p].items()}, "1963-07", "2024-12"))]
        blk[s]["C3_self_difference_max_abs"] = max(abs(x) for x in same) if same else None
    OUT["D_alt_" + label] = blk

OUT["controls"] = ctrl
print(json.dumps(OUT, indent=1, default=str))
with open(os.path.join(HERE, "C4_cz_measurement.json"), "w") as f:
    json.dump(OUT, f, indent=1, default=str)
