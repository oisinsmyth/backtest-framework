"""C4 [MEASURED IN BRIEF] -- concentration and robustness of the post-publication long leg."""
import csv, io, json, math, os, zipfile, collections

HERE = os.path.dirname(os.path.abspath(__file__))


def tstat(xs):
    n = len(xs)
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


def load_sig(zpath, sig):
    z = zipfile.ZipFile(os.path.join(HERE, zpath))
    out = collections.defaultdict(dict)
    with z.open(z.namelist()[0]) as f:
        for row in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8")):
            if row["signalname"] == sig and row["ret"] not in ("NA", ""):
                out[row["port"]][row["date"][:7]] = float(row["ret"])
    return out


mkt = load_ff5_mkt()
OUT = {}
for sig in ["GP", "CBOperProf", "OperProf", "OperProfRD"]:
    ap = load_sig("C4_CZ_price_gt5.zip", sig)
    ports = sorted(p for p in ap if p != "LS")
    lp, sp = ports[-1], ports[0]
    months = sorted(k for k in ap[lp] if "2014-01" <= k <= "2024-12" and k in mkt)
    lmm = {k: ap[lp][k] - mkt[k] for k in months}
    ls = {k: ap[lp][k] - ap[sp][k] for k in months}
    blk = {}
    m, t, n = tstat(list(lmm.values()))
    blk["post_pub_long_minus_mkt"] = {"mean": round(m, 4), "t": round(t, 2), "n": n}
    # leave-one-year-out
    yrs = sorted({k[:4] for k in months})
    loo = {}
    for y in yrs:
        xs = [v for k, v in lmm.items() if k[:4] != y]
        mm, tt, nn = tstat(xs)
        loo[y] = {"mean_excl": round(mm, 4), "t_excl": round(tt, 2)}
    blk["leave_one_year_out_long_minus_mkt"] = loo
    blk["worst_LOO_year"] = min(loo, key=lambda y: loo[y]["mean_excl"])
    # drop the covid quarter
    xs = [v for k, v in lmm.items() if not ("2020-02" <= k <= "2020-04")]
    mm, tt, nn = tstat(xs)
    blk["long_minus_mkt_excl_2020Q1"] = {"mean": round(mm, 4), "t": round(tt, 2), "n": nn}
    # months to half the post-pub long-short sum
    tot = sum(v for v in ls.values() if True)
    srt = sorted(ls.items(), key=lambda x: -x[1])
    c = 0.0
    k_half = 0
    for i, (kk, vv) in enumerate(srt, 1):
        c += vv
        if c >= 0.5 * tot:
            k_half = i
            break
    blk["LS_months_to_half_of_post_pub_sum"] = {"k": k_half, "of_n": len(ls),
                                                "pct_of_months": round(100.0 * k_half / len(ls), 1),
                                                "sum_pct_mo": round(tot, 1)}
    # same for the long-minus-market series
    tot2 = sum(lmm.values())
    srt2 = sorted(lmm.items(), key=lambda x: -x[1])
    c = 0.0; k2 = 0
    for i, (kk, vv) in enumerate(srt2, 1):
        c += vv
        if c >= 0.5 * tot2:
            k2 = i
            break
    blk["LmM_months_to_half"] = {"k": k2, "of_n": len(lmm), "pct_of_months": round(100.0 * k2 / len(lmm), 1),
                                 "sum_pct_mo": round(tot2, 1)}
    # 1% symmetric trim of the long-minus-market series
    vals = sorted(lmm.values())
    k = max(1, int(round(0.01 * len(vals))))
    blk["LmM_trims"] = {
        "raw_mean": round(sum(vals) / len(vals), 4),
        "ex_top_%d" % k: round(sum(vals[:-k]) / (len(vals) - k), 4),
        "ex_bottom_%d" % k: round(sum(vals[k:]) / (len(vals) - k), 4),
        "trimmed_both": round(sum(vals[k:-k]) / (len(vals) - 2 * k), 4),
        "median": round(vals[len(vals) // 2], 4),
    }
    OUT[sig] = blk

print(json.dumps(OUT, indent=1))
json.dump(OUT, open(os.path.join(HERE, "C4_robust.json"), "w"), indent=1)
