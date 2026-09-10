"""C2 independent measurement: construction dispersion of the operating-profitability
premium, using only Kenneth R. French's published portfolio returns.

Endpoint: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/
  Portfolios_Formed_on_OP_CSV.zip      (univariate OP portfolios, VW and EW,
                                        terciles / quintiles / deciles, monthly)
  6_Portfolios_ME_OP_2x3_CSV.zip       (2x3 size-OP portfolios, VW and EW, monthly)
  F-F_Research_Data_5_Factors_2x3_CSV.zip  (published RMW and RF, monthly)

No private data. Pure stdlib. Reports mean, t, and sign for every cell of a
construction grid, plus four negative controls.
"""
import zipfile, os, math, re, json

HERE = os.path.dirname(os.path.abspath(__file__))
FF = os.path.join(HERE, "ff")


def read_blocks(zname, cname):
    """Split a French CSV into labelled blocks -> {label: (header, {date:[vals]})}."""
    txt = zipfile.ZipFile(os.path.join(FF, zname)).read(cname).decode("latin-1").splitlines()
    blocks, label, header, rows = {}, None, None, None
    for line in txt:
        s = line.rstrip()
        if not s.strip():
            continue
        if re.match(r"^\s*\d{6}\s*,", s):
            parts = [p.strip() for p in s.split(",")]
            d = int(parts[0])
            vals = []
            for p in parts[1:]:
                if p == "":
                    continue
                vals.append(float(p))
            if rows is not None:
                rows[d] = vals
            continue
        if re.match(r"^\s*\d{4}\s*,", s):          # annual rows - skip
            continue
        if s.startswith(","):                       # column header line
            header = [p.strip() for p in s.split(",")[1:] if p.strip() != ""]
            continue
        # a text line: either prose or a block title. Treat as block title only if
        # the next header/data will follow. We just record the latest text line.
        if rows is not None and len(rows) > 0 and label is not None:
            blocks[label] = (header, rows)
        label, rows, header = s.strip(), {}, None
    if rows is not None and len(rows) > 0 and label is not None:
        blocks[label] = (header, rows)
    return blocks


def monthly(blocks, want):
    """Return (header, {date:[vals]}) for the first block whose label contains `want`
    and whose keys look monthly."""
    for lab, (h, r) in blocks.items():
        if want.lower() in lab.lower():
            ks = list(r)
            if ks and ks[0] > 100000 and (ks[0] % 100) <= 12:
                return lab, h, r
    raise KeyError(want)


def tstat(xs):
    n = len(xs)
    m = sum(xs) / n
    v = sum((x - m) ** 2 for x in xs) / (n - 1)
    sd = math.sqrt(v)
    return m, sd, m / (sd / math.sqrt(n)), n


op = read_blocks("Portfolios_Formed_on_OP_CSV.zip", "Portfolios_Formed_on_OP.csv")
p6 = read_blocks("6_Portfolios_ME_OP_2x3_CSV.zip", "6_Portfolios_ME_OP_2x3.csv")
f5 = read_blocks("F-F_Research_Data_5_Factors_2x3_CSV.zip", "F-F_Research_Data_5_Factors_2x3.csv")

print("OP blocks:", list(op))
print("6P blocks:", list(p6))
print("F5 blocks:", list(f5))

lab_vw, h_vw, vw = monthly(op, "Value Weight")
lab_ew, h_ew, ew = monthly(op, "Equal Weight")
print("\nVW block:", repr(lab_vw), "cols", h_vw, "n", len(vw), "range", min(vw), max(vw))
print("EW block:", repr(lab_ew), "cols", h_ew, "n", len(ew), "range", min(ew), max(ew))

lab6vw, h6vw, p6vw = monthly(p6, "Average Value Weighted Returns -- Monthly")
print("6P VW block:", repr(lab6vw), "cols", h6vw, "n", len(p6vw))

lab5, h5, ff5 = monthly(f5, "")
print("F5 block:", repr(lab5), "cols", h5, "n", len(ff5), "range", min(ff5), max(ff5))

RFi = h5.index("RF")
RMWi = h5.index("RMW")
RF = {d: v[RFi] for d, v in ff5.items()}
RMW = {d: v[RMWi] for d, v in ff5.items()}

# ---------------------------------------------------------------- NEGATIVE CONTROLS
print("\n" + "=" * 72)
print("NEGATIVE CONTROLS")
print("=" * 72)

# NC1: RMW identity. RMW = 1/2(SmallRobust+BigRobust) - 1/2(SmallWeak+BigWeak)
iSH = h6vw.index("SMALL HiOP"); iBH = h6vw.index("BIG HiOP")
iSL = h6vw.index("SMALL LoOP"); iBL = h6vw.index("BIG LoOP")
ds = sorted(set(p6vw) & set(RMW))
diffs = [0.5 * (p6vw[d][iSH] + p6vw[d][iBH]) - 0.5 * (p6vw[d][iSL] + p6vw[d][iBL]) - RMW[d] for d in ds]
print("NC1 RMW identity from 6 portfolios vs published RMW: n=%d  max|diff|=%.4f  mean|diff|=%.5f"
      % (len(ds), max(abs(x) for x in diffs), sum(abs(x) for x in diffs) / len(ds)))

# NC2: a quantity that MUST be exactly zero
iHi30 = h_vw.index("Hi 30")
nz = sum(1 for d in vw if (vw[d][iHi30] - vw[d][iHi30]) != 0.0)
print("NC2 self-difference Hi30-Hi30 nonzero months (must be 0): %d of %d" % (nz, len(vw)))

# NC3: sentinel census - a value that must return zero in this window
sent = sum(1 for d in vw for v in vw[d] if v in (-99.99, -999.0))
sent_all = sum(1 for d in ew for v in ew[d] if v in (-99.99, -999.0))
pre = sum(1 for d in vw if d < 196307)
print("NC3 sentinel (-99.99/-999) cells in VW monthly: %d ; EW monthly: %d ; dates before 196307: %d (all must be 0)"
      % (sent, sent_all, pre))

# NC4: proof the VW and EW blocks are genuinely different objects (not the same block twice)
common = sorted(set(vw) & set(ew))
d_ve = sum(abs(vw[d][iHi30] - ew[d][iHi30]) for d in common) / len(common)
print("NC4 mean|VW Hi30 - EW Hi30| = %.4f pp/month (must be >0; 0 would mean one block read twice)" % d_ve)

# NC5: census that must return zero - the OP file's own stated coverage
print("NC5 months in VW block outside [196307, 202606]: %d"
      % sum(1 for d in vw if d < 196307 or d > 202606))

# ---------------------------------------------------------------- THE GRID
print("\n" + "=" * 72)
print("THE CONSTRUCTION GRID  (OP = operating profits / book equity, Fama-French defn)")
print("t is iid:  mean / (sd/sqrt(n)).  Returns in percent per month.")
print("=" * 72)

cuts = {"tercile 30/70": ("Hi 30", "Lo 30"),
        "quintile 20/80": ("Hi 20", "Lo 20"),
        "decile 10/90": ("Hi 10", "Lo 10")}
weights = {"VW": (h_vw, vw), "EW": (h_ew, ew)}
windows = {"full 1963-07..2026-06": (196307, 202606),
           "prog 2010-01..2026-06": (201001, 202606)}

rows = []
for wname, (hh, dd) in weights.items():
    for cname, (hi, lo) in cuts.items():
        ihi, ilo = hh.index(hi), hh.index(lo)
        for sname, (a, b) in windows.items():
            ds2 = sorted(d for d in dd if a <= d <= b and d in RF)
            spread = [dd[d][ihi] - dd[d][ilo] for d in ds2]
            longleg = [dd[d][ihi] - RF[d] for d in ds2]
            for lens, xs in (("spread Hi-Lo", spread), ("long leg - RF", longleg)):
                m, sd, t, n = tstat(xs)
                rows.append((wname, cname, sname, lens, m, t, n))
                print("%-3s %-15s %-22s %-14s  mean %+6.3f  t %+6.2f  n %4d" %
                      (wname, cname, sname, lens, m, t, n))

# the 2x3 (RMW-style) construction for comparison
print("\n2x3 size-OP construction (the RMW convention), same two windows:")
for sname, (a, b) in windows.items():
    ds2 = sorted(d for d in RMW if a <= d <= b)
    m, sd, t, n = tstat([RMW[d] for d in ds2])
    print("  published RMW            %-22s  mean %+6.3f  t %+6.2f  n %4d" % (sname, m, t, n))
    ds3 = sorted(d for d in p6vw if a <= d <= b and d in RF)
    for leg, idx in (("SMALL HiOP - RF", iSH), ("BIG HiOP - RF", iBH)):
        m, sd, t, n = tstat([p6vw[d][idx] - RF[d] for d in ds3])
        print("  VW %-22s %-22s  mean %+6.3f  t %+6.2f  n %4d" % (leg, sname, m, t, n))

# ---------------------------------------------------------------- SUMMARY
print("\n" + "=" * 72)
print("DISPERSION SUMMARY")
print("=" * 72)
for lens in ("spread Hi-Lo", "long leg - RF"):
    for sname in windows:
        sub = [r for r in rows if r[3] == lens and r[2] == sname]
        ms = [r[4] for r in sub]
        ts = [r[5] for r in sub]
        nneg = sum(1 for m in ms if m < 0)
        nsig = sum(1 for t in ts if abs(t) > 1.96)
        print("%-14s %-22s  n_cells %d  mean range [%+.3f, %+.3f]  t range [%+.2f, %+.2f]  "
              "negative-mean cells %d  |t|>1.96 cells %d"
              % (lens, sname, len(sub), min(ms), max(ms), min(ts), max(ts), nneg, nsig))

json.dump([{"weight": r[0], "cut": r[1], "window": r[2], "lens": r[3],
            "mean_pct_per_month": r[4], "t": r[5], "n_months": r[6]} for r in rows],
          open(os.path.join(HERE, "C2_op_grid_results.json"), "w"), indent=1)
print("\nwrote C2_op_grid_results.json")
