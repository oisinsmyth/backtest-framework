"""C2 independent measurement II: the SAME long leg, four benchmarks.

Round 2 found one paper whose cash-based-operating-profitability LONG LEG was
+14 bp/month (t 1.95) against CAPM and +35 bp/month (t 5.98) against FF3.
This reproduces that shape on public data: Kenneth French's high-operating-
profitability long leg, scored against cash, CAPM, FF3, FF4(+RMW), FF5.

Endpoint: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/
Pure stdlib OLS via normal equations with Gaussian elimination. iid t-stats.
"""
import os, math, json
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("g", os.path.join(HERE, "C2_measure_op_grid.py"))

# re-read the files directly rather than importing (the grid script prints a lot)
import zipfile, re
FF = os.path.join(HERE, "ff")


def read_blocks(zname, cname):
    txt = zipfile.ZipFile(os.path.join(FF, zname)).read(cname).decode("latin-1").splitlines()
    blocks, label, header, rows = {}, None, None, None
    for line in txt:
        s = line.rstrip()
        if not s.strip():
            continue
        if re.match(r"^\s*\d{6}\s*,", s):
            parts = [p.strip() for p in s.split(",")]
            rows[int(parts[0])] = [float(p) for p in parts[1:] if p != ""]
            continue
        if re.match(r"^\s*\d{4}\s*,", s):
            continue
        if s.startswith(","):
            header = [p.strip() for p in s.split(",")[1:] if p.strip() != ""]
            continue
        if rows:
            blocks[label] = (header, rows)
        label, rows, header = s.strip(), {}, None
    if rows:
        blocks[label] = (header, rows)
    return blocks


def pick(blocks, want):
    for lab, (h, r) in blocks.items():
        if want.lower() in lab.lower():
            ks = list(r)
            if ks and ks[0] > 100000 and (ks[0] % 100) <= 12:
                return h, r
    raise KeyError(want)


def ols(y, X):
    """X is list of rows (without intercept). Returns (coefs incl. intercept, tstats)."""
    n = len(y)
    k = len(X[0]) + 1
    A = [[0.0] * k for _ in range(k)]
    b = [0.0] * k
    rows = [[1.0] + list(x) for x in X]
    for i in range(n):
        for a in range(k):
            b[a] += rows[i][a] * y[i]
            for c in range(k):
                A[a][c] += rows[i][a] * rows[i][c]
    # solve A beta = b  (Gauss-Jordan with partial pivoting), keep A^-1 for SEs
    M = [A[r][:] + [1.0 if r == c else 0.0 for c in range(k)] for r in range(k)]
    for col in range(k):
        p = max(range(col, k), key=lambda r: abs(M[r][col]))
        M[col], M[p] = M[p], M[col]
        pv = M[col][col]
        M[col] = [v / pv for v in M[col]]
        for r in range(k):
            if r != col and M[r][col] != 0.0:
                f = M[r][col]
                M[r] = [M[r][j] - f * M[col][j] for j in range(2 * k)]
    Ainv = [row[k:] for row in M]
    beta = [sum(Ainv[a][c] * b[c] for c in range(k)) for a in range(k)]
    resid = [y[i] - sum(beta[a] * rows[i][a] for a in range(k)) for i in range(n)]
    s2 = sum(r * r for r in resid) / (n - k)
    se = [math.sqrt(s2 * Ainv[a][a]) for a in range(k)]
    return beta, [beta[a] / se[a] for a in range(k)], n


op = read_blocks("Portfolios_Formed_on_OP_CSV.zip", "Portfolios_Formed_on_OP.csv")
p6 = read_blocks("6_Portfolios_ME_OP_2x3_CSV.zip", "6_Portfolios_ME_OP_2x3.csv")
f5 = read_blocks("F-F_Research_Data_5_Factors_2x3_CSV.zip", "F-F_Research_Data_5_Factors_2x3.csv")
h_vw, vw = pick(op, "Value Weight")
h_ew, ew = pick(op, "Equal Weight")
h6, p6vw = pick(p6, "Average Value Weighted Returns -- Monthly")
h5, ff5 = pick(f5, "TBill")

I = {n: h5.index(n) for n in ("Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF")}

BENCH = [("cash (no benchmark)", []),
         ("CAPM", ["Mkt-RF"]),
         ("FF3", ["Mkt-RF", "SMB", "HML"]),
         ("FF3+RMW", ["Mkt-RF", "SMB", "HML", "RMW"]),
         ("FF5", ["Mkt-RF", "SMB", "HML", "RMW", "CMA"])]

LEGS = [("VW Hi30 OP long leg", h_vw, vw, "Hi 30"),
        ("VW Hi20 OP long leg", h_vw, vw, "Hi 20"),
        ("VW Hi10 OP long leg", h_vw, vw, "Hi 10"),
        ("EW Hi30 OP long leg", h_ew, ew, "Hi 30"),
        ("VW Hi30-Lo30 SPREAD", h_vw, vw, "SPREAD30"),
        ("EW Hi30-Lo30 SPREAD", h_ew, ew, "SPREAD30")]

WINDOWS = [("full 1963-07..2026-06", 196307, 202606),
           ("prog 2010-01..2026-06", 201001, 202606)]

out = []
for wn, a, b in WINDOWS:
    print("=" * 86)
    print("WINDOW", wn)
    print("=" * 86)
    print("%-22s %-20s %9s %8s %7s" % ("leg", "benchmark", "alpha%/mo", "t", "n"))
    for lname, hh, dd, col in LEGS:
        ds = sorted(d for d in dd if a <= d <= b and d in ff5)
        if col == "SPREAD30":
            y = [dd[d][hh.index("Hi 30")] - dd[d][hh.index("Lo 30")] for d in ds]
        else:
            y = [dd[d][hh.index(col)] - ff5[d][I["RF"]] for d in ds]
        for bn, facs in BENCH:
            X = [[ff5[d][I[f]] for f in facs] for d in ds] if facs else [[] for d in ds]
            if facs:
                beta, t, n = ols(y, X)
                alpha, ta = beta[0], t[0]
            else:
                n = len(y)
                m = sum(y) / n
                sd = math.sqrt(sum((x - m) ** 2 for x in y) / (n - 1))
                alpha, ta = m, m / (sd / math.sqrt(n))
            print("%-22s %-20s %+9.3f %+8.2f %7d" % (lname, bn, alpha, ta, n))
            out.append(dict(window=wn, leg=lname, benchmark=bn, alpha=alpha, t=ta, n=n))
        print()

print("=" * 86)
print("BENCHMARK-INDUCED RANGE, same leg same window")
print("=" * 86)
for wn, a, b in WINDOWS:
    for lname, _, _, _ in LEGS:
        sub = [o for o in out if o["window"] == wn and o["leg"] == lname]
        al = [o["alpha"] for o in sub]
        ts = [o["t"] for o in sub]
        print("%-22s %-22s alpha [%+.3f, %+.3f] (x%.2f)  t [%+.2f, %+.2f]  sign flips %s  crosses 1.96 %s"
              % (wn, lname, min(al), max(al),
                 (max(al) / min(al)) if min(al) > 0 else float('nan'),
                 min(ts), max(ts),
                 "YES" if min(al) < 0 < max(al) else "no",
                 "YES" if min(ts) < 1.96 < max(ts) else "no"))

json.dump(out, open(os.path.join(HERE, "C2_benchmark_results.json"), "w"), indent=1)
print("\nwrote C2_benchmark_results.json")
