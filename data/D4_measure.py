"""D4 [MEASURED IN BRIEF] -- arrival and concentration of a characteristic premium.

Endpoints (all Ken French Data Library, fetched by D4_fetch.py, 2026-09-10):
  Portfolios_Formed_on_OP_CSV.zip        (deciles on operating profitability)
  Portfolios_Formed_on_BE-ME_CSV.zip     (deciles on book-to-market)
  F-F_Research_Data_5_Factors_2x3_CSV.zip (RMW, Mkt-RF, RF)
  6_Portfolios_ME_OP_2x3_CSV.zip         (for the RMW reconstruction control)

Every block read is identified by its header line and that header is printed.
Sentinels -99.99 / -999 are censused per block and REMOVED, and the census is reported.
"""
import csv, io, json, math, os, random, zipfile, collections

HERE = os.path.dirname(os.path.abspath(__file__))
SENT = (-99.99, -999.0, -99.99000, -999.00)
LOG = {}


# ---------------------------------------------------------------- file readers
def read_block(zipname, header_substr, ncols_min=2):
    """Return (header_line, colnames, {YYYY-MM: [floats]}, census). Monthly blocks only."""
    z = zipfile.ZipFile(os.path.join(HERE, zipname))
    name = z.namelist()[0]
    lines = z.read(name).decode("latin-1").splitlines()
    hdr_i = None
    for i, l in enumerate(lines):
        if header_substr in l:
            hdr_i = i
            break
    if hdr_i is None:
        raise SystemExit("block header not found: %r in %s" % (header_substr, zipname))
    header_line = lines[hdr_i].rstrip()
    colnames = [c.strip() for c in lines[hdr_i + 1].split(",")][1:]
    out = {}
    census = collections.Counter()
    n_rows = 0
    for l in lines[hdr_i + 2:]:
        s = l.strip()
        if not s:
            break
        f = s.split(",")
        d = f[0].strip()
        if not (len(d) == 6 and d.isdigit()):
            break          # left the monthly block (annual block / next header)
        vals = []
        for x in f[1:]:
            x = x.strip()
            if x == "":
                vals.append(None); continue
            v = float(x)
            if v in SENT:
                census[round(v, 2)] += 1
                vals.append(None)
            else:
                vals.append(v)
        out[d[:4] + "-" + d[4:]] = vals
        n_rows += 1
    LOG[zipname + " :: " + header_substr.strip()] = {
        "header_line_verbatim": header_line,
        "column_header_verbatim": lines[hdr_i + 1].rstrip(),
        "n_columns": len(colnames),
        "n_monthly_rows": n_rows,
        "first_month": min(out), "last_month": max(out),
        "sentinel_census": {str(k): v for k, v in sorted(census.items())},
    }
    return header_line, colnames, out, census


def read_ff_factors(zipname, want):
    """FF factor CSV: monthly block runs until the first non-6-digit key."""
    z = zipfile.ZipFile(os.path.join(HERE, zipname))
    name = z.namelist()[0]
    lines = z.read(name).decode("latin-1").splitlines()
    hdr_i = None
    for i, l in enumerate(lines):
        if l.strip().startswith(",") and "Mkt-RF" in l:
            hdr_i = i
            break
    cols = [c.strip() for c in lines[hdr_i].split(",")][1:]
    idx = {c: j for j, c in enumerate(cols)}
    out = {}
    census = collections.Counter()
    n = 0
    for l in lines[hdr_i + 1:]:
        s = l.strip()
        f = [x.strip() for x in s.split(",")]
        if not (len(f[0]) == 6 and f[0].isdigit()):
            if f[0] and not f[0].isdigit():
                break
            continue
        rec = {}
        for c in want:
            v = float(f[1 + idx[c]])
            if v in SENT:
                census[round(v, 2)] += 1
                v = None
            rec[c] = v
        out[f[0][:4] + "-" + f[0][4:]] = rec
        n += 1
    LOG[zipname + " :: monthly factors"] = {
        "column_header_verbatim": lines[hdr_i].rstrip(),
        "n_monthly_rows": n, "first_month": min(out), "last_month": max(out),
        "sentinel_census": {str(k): v for k, v in sorted(census.items())},
    }
    return out


# ---------------------------------------------------------------- statistics
def moments(xs):
    n = len(xs)
    m = sum(xs) / n
    d = [x - m for x in xs]
    v = sum(y * y for y in d) / (n - 1)
    sd = math.sqrt(v)
    se = sd / math.sqrt(n)
    s = sorted(xs)
    med = s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])
    sk = (sum(y ** 3 for y in d) / n) / (sum(y * y for y in d) / n) ** 1.5 if sd else 0.0
    ku = (sum(y ** 4 for y in d) / n) / (sum(y * y for y in d) / n) ** 2 - 3.0 if sd else 0.0
    return dict(n=n, mean=m, median=med, sd=sd, t=(m / se if se else None),
                skew=sk, exkurt=ku, frac_pos=sum(1 for x in xs if x > 0) / n)


def k_half(xs):
    """Smallest k such that the k largest months sum to >= half the TOTAL sum.
    Defined only when the total sum is positive."""
    tot = sum(xs)
    if tot <= 0:
        return None, tot
    c = 0.0
    for i, v in enumerate(sorted(xs, reverse=True), 1):
        c += v
        if c >= 0.5 * tot:
            return i, tot
    return len(xs), tot


def topk_share(xs, k):
    tot = sum(xs)
    if tot == 0:
        return None
    return sum(sorted(xs, reverse=True)[:k]) / tot


def trims(xs, pct=0.01):
    s = sorted(xs)
    n = len(s)
    k = max(1, int(round(pct * n)))
    return dict(k_trimmed_each_tail=k,
                raw_mean=sum(s) / n,
                ex_top=sum(s[:-k]) / (n - k),
                ex_bottom=sum(s[k:]) / (n - k),
                trimmed_both=sum(s[k:-k]) / (n - 2 * k))


def maxdd(xs):
    """Max drawdown of the compounded monthly relative series, % units in, fraction out."""
    lvl, peak, worst, trough = 1.0, 1.0, 0.0, None
    for i, x in enumerate(xs):
        lvl *= (1.0 + x / 100.0)
        peak = max(peak, lvl)
        dd = lvl / peak - 1.0
        if dd < worst:
            worst, trough = dd, i
    return worst, trough


def drop_worst_k(xs, k):
    s = sorted(xs)
    return sum(s[k:]) / (len(s) - k)


def drop_best_k(xs, k):
    s = sorted(xs)
    return sum(s[:-k]) / (len(s) - k)


# ---------------------------------------------------------------- nulls
def null_k_half(mean, sd, n, draws, seed):
    """iid Gaussian with MATCHED mean and sd -- no fat tails, no clustering at all."""
    rng = random.Random(seed)
    ks = []
    for _ in range(draws):
        xs = [rng.gauss(mean, sd) for _ in range(n)]
        k, tot = k_half(xs)
        ks.append(k if k is not None else None)
    good = [k for k in ks if k is not None]
    good.sort()
    return dict(draws=draws, n_with_positive_sum=len(good),
                p05=good[int(0.05 * len(good))], p50=good[len(good) // 2],
                p95=good[int(0.95 * len(good))], mean=sum(good) / len(good))


def null_k_half_bootstrap(xs, draws, seed):
    """iid resample WITH replacement of the observed months: preserves the marginal
    distribution (fat tails included), destroys any time structure."""
    rng = random.Random(seed)
    n = len(xs)
    ks = []
    for _ in range(draws):
        s = [xs[rng.randrange(n)] for _ in range(n)]
        k, tot = k_half(s)
        if k is not None:
            ks.append(k)
    ks.sort()
    return dict(draws=draws, n_with_positive_sum=len(ks), p05=ks[int(0.05 * len(ks))],
                p50=ks[len(ks) // 2], p95=ks[int(0.95 * len(ks))], mean=sum(ks) / len(ks))


def max_rolling_share(xs, w):
    """Share of the total sum earned in the best contiguous w-month window.
    This statistic IS order-dependent, unlike k_half."""
    tot = sum(xs)
    if tot <= 0:
        return None
    best = max(sum(xs[i:i + w]) for i in range(len(xs) - w + 1))
    return best / tot


def perm_p_rolling(xs, w, draws, seed):
    """Permutation null for max_rolling_share: same months, order destroyed.
    Tests CLUSTERING IN TIME and nothing else."""
    obs = max_rolling_share(xs, w)
    if obs is None:
        return None
    rng = random.Random(seed)
    s = list(xs)
    vals = []
    for _ in range(draws):
        rng.shuffle(s)
        v = max_rolling_share(s, w)
        if v is not None:
            vals.append(v)
    vals.sort()
    ge = sum(1 for v in vals if v >= obs)
    return dict(observed=obs, draws=len(vals), p50=vals[len(vals) // 2],
                p95=vals[int(0.95 * len(vals))], p_value=(ge + 1) / (len(vals) + 1))


def lb_autocorr(xs, lags=6):
    n = len(xs)
    m = sum(xs) / n
    d = [x - m for x in xs]
    c0 = sum(y * y for y in d)
    out = {}
    q = 0.0
    for L in range(1, lags + 1):
        r = sum(d[i] * d[i + L] for i in range(n - L)) / c0
        out["rho%d" % L] = r
        q += r * r / (n - L)
    out["ljung_box_Q"] = n * (n + 2) * q
    out["lb_df"] = lags
    return out


# ---------------------------------------------------------------- report
def report(label, xs, months, draws=20000, seed=20260910, roll=12):
    mo = moments(xs)
    k, tot = k_half(xs)
    srt = sorted(range(len(xs)), key=lambda i: -xs[i])
    rec = dict(label=label, window=[months[0], months[-1]], **mo)
    rec["total_sum_pct_months"] = tot
    rec["k_half"] = k
    rec["k_half_pct_of_months"] = (100.0 * k / len(xs)) if k else None
    rec["top1_share"] = topk_share(xs, 1)
    rec["top5_share"] = topk_share(xs, 5)
    rec["top10_share"] = topk_share(xs, 10)
    rec["best_month"] = [months[srt[0]], xs[srt[0]]]
    rec["worst_month"] = [months[srt[-1]], xs[srt[-1]]]
    rec["trims_1pct"] = trims(xs)
    nk = max(1, int(round(0.01 * len(xs))))
    rec["mirror"] = dict(k=3, drop_best_3=drop_best_k(xs, 3), drop_worst_3=drop_worst_k(xs, 3),
                         drop_both_3=sum(sorted(xs)[3:-3]) / (len(xs) - 6))
    dd, tr = maxdd(xs)
    rec["maxdd"] = dd
    rec["maxdd_trough_month"] = months[tr] if tr is not None else None
    rec["ann_sharpe"] = (mo["mean"] / mo["sd"] * math.sqrt(12)) if mo["sd"] else None
    rec["years_for_t2"] = ((2.0 / (mo["mean"] / mo["sd"] * math.sqrt(12))) ** 2
                           if mo["sd"] and mo["mean"] > 0 else None)
    if k is not None:
        rec["null_k_half_iid_gaussian_matched"] = null_k_half(mo["mean"], mo["sd"], len(xs), 4000, seed)
        rec["null_k_half_iid_bootstrap"] = null_k_half_bootstrap(xs, 4000, seed + 1)
    rec["clustering_max_%dmo_window" % roll] = perm_p_rolling(xs, roll, 4000, seed + 2)
    rec["autocorr"] = lb_autocorr(xs)
    return rec
