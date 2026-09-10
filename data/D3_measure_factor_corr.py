"""D3 [MEASURED IN BRIEF] part 3 -- cross-dataset, cross-team correlation:
does French's RMW (operating profits / book equity, Fama-French construction, CRSP+Compustat)
look more like Chen-Zimmermann's OperProf (same DEFINITION, different team and code) or more like
Chen-Zimmermann's GP (different definition, same team and code)?

The point of the design: RMW~CZ-OperProf is the POSITIVE control (definition held, everything else
changed). RMW~CZ-GP is the treatment (definition changed, team/dataset also changed). If the
positive control is much higher, the definition is the binding difference even across datasets.

Endpoints:
  mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_CSV.zip
     11,948 B  sha1 c9218d2ab2ff
  mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Portfolios_Formed_on_OP_CSV.zip
    135,027 B  sha1 a889a239cee5
  CZ PredictorAltPorts_QuintilesVW.zip / _QuintilesEW.zip  (see D3_measure_same_signal.py)

HAZARDS HANDLED EXPLICITLY
  (a) French files carry -99.99 / -999 as MISSING sentinels. Census them; never average them.
  (b) Each French portfolio file stacks SEVERAL blocks (EW returns, VW returns, firm counts,
      average firm size, and an ANNUAL block) under one header. Prove which block was read by
      compounding the monthly block and matching French's own annual block.
"""
import csv, io, json, math, os, re, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = {}
FAIL = []
SENT = (-99.99, -999.0, -99.0)


def tstat(xs):
    n = len(xs); m = sum(xs) / n
    v = sum((x - m) ** 2 for x in xs) / (n - 1)
    return m, m / math.sqrt(v / n), n


def corr(xs, ys):
    n = len(xs); mx = sum(xs) / n; my = sum(ys) / n
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs)); sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)


def french_blocks(zname):
    """Split a French CSV into blocks keyed by the text line that precedes them.
    Returns list of (header_text, fieldnames, {key: [floats]}) and a sentinel census."""
    z = zipfile.ZipFile(os.path.join(HERE, zname))
    txt = z.read(z.namelist()[0]).decode("latin-1").splitlines()
    blocks = []
    cur_label = "PREAMBLE"
    cur_cols = None
    cur_rows = {}
    sent = 0
    for ln in txt:
        s = ln.strip()
        if not s:
            continue
        parts = [p.strip() for p in s.split(",")]
        if parts[0] == "" and len(parts) > 2:          # a column-header line
            if cur_cols and cur_rows:
                blocks.append((cur_label, cur_cols, cur_rows))
            cur_cols = parts[1:]
            cur_rows = {}
            continue
        if re.fullmatch(r"\d{6}|\d{4}", parts[0]) and cur_cols:
            vals = []
            for p in parts[1:]:
                try:
                    x = float(p)
                except ValueError:
                    x = None
                if x is not None and any(abs(x - s0) < 1e-6 for s0 in SENT):
                    sent += 1
                    x = None
                vals.append(x)
            cur_rows[parts[0]] = vals
            continue
        # narrative line -> label for the NEXT block
        if cur_cols and cur_rows:
            blocks.append((cur_label, cur_cols, cur_rows))
            cur_cols = None
            cur_rows = {}
        cur_label = s[:110]
    if cur_cols and cur_rows:
        blocks.append((cur_label, cur_cols, cur_rows))
    return blocks, sent


# ---------- French OP portfolios: identify the blocks and PROVE which one was read
blocks, sent_op = french_blocks("D3_FrenchOP.zip")
print("Portfolios_Formed_on_OP: %d blocks, sentinel (-99.99/-999) cells censused = %d" % (len(blocks), sent_op))
for i, (lab, cols, rows) in enumerate(blocks):
    ks = sorted(rows)
    print("  block %d  n=%-5d keylen=%d  %s..%s  | %s" % (i, len(rows), len(ks[0]), ks[0], ks[-1], lab[:82]))
OUT["french_op_blocks"] = [{"i": i, "label": lab, "n": len(rows), "keylen": len(sorted(rows)[0]),
                            "first": sorted(rows)[0], "last": sorted(rows)[-1], "ncols": len(cols)}
                           for i, (lab, cols, rows) in enumerate(blocks)]
OUT["french_op_sentinels"] = sent_op

# the EW monthly block and the EW annual block
mon_ew = [b for b in blocks if len(sorted(b[2])[0]) == 6 and "Equal" in b[0]]
ann_ew = [b for b in blocks if len(sorted(b[2])[0]) == 4 and "Equal" in b[0]]
print("\nEW monthly blocks found: %d ; EW annual blocks found: %d" % (len(mon_ew), len(ann_ew)))
if mon_ew and ann_ew:
    lab_m, cols_m, rows_m = mon_ew[0]
    lab_a, cols_a, rows_a = ann_ew[0]
    ci = cols_m.index("Hi 10") if "Hi 10" in cols_m else None
    cj = cols_a.index("Hi 10") if "Hi 10" in cols_a else None
    print("  monthly label: %s" % lab_m[:100])
    print("  annual  label: %s" % lab_a[:100])
    if ci is not None and cj is not None:
        worst = 0.0; npairs = 0
        for y in sorted(rows_a):
            ms = [rows_m["%s%02d" % (y, m)][ci] for m in range(1, 13) if "%s%02d" % (y, m) in rows_m]
            if len(ms) != 12 or any(v is None for v in ms):
                continue
            comp = 1.0
            for v in ms:
                comp *= (1 + v / 100.0)
            comp = (comp - 1) * 100.0
            a = rows_a[y][cj]
            if a is None:
                continue
            worst = max(worst, abs(comp - a)); npairs += 1
        OUT["P3_compound_vs_annual_worst_pp"] = worst
        OUT["P3_compound_vs_annual_years"] = npairs
        print("  P3 POSITIVE CONTROL: compounding the MONTHLY EW 'Hi 10' block against French's own")
        print("     ANNUAL EW 'Hi 10' block over %d years -> worst |diff| = %.6f pp  %s"
              % (npairs, worst, "PASS" if worst < 0.05 else "**FAIL**"))
        if worst >= 0.05:
            FAIL.append("P3")
        # N5: a control that MUST return zero -- compounding the WRONG block must NOT match
        vw_mon = [b for b in blocks if len(sorted(b[2])[0]) == 6 and "Value" in b[0]]
        if vw_mon:
            _, cols_v, rows_v = vw_mon[0]
            cv = cols_v.index("Hi 10")
            worst_wrong = 0.0; nw = 0
            for y in sorted(rows_a):
                ms = [rows_v["%s%02d" % (y, m)][cv] for m in range(1, 13) if "%s%02d" % (y, m) in rows_v]
                if len(ms) != 12 or any(v is None for v in ms):
                    continue
                comp = 1.0
                for v in ms:
                    comp *= (1 + v / 100.0)
                a = rows_a[y][cj]
                if a is None:
                    continue
                worst_wrong = max(worst_wrong, abs((comp - 1) * 100 - a)); nw += 1
            OUT["N5_wrongblock_worst_pp"] = worst_wrong
            print("     N5 same test against the VALUE-WEIGHTED monthly block (the block I did NOT mean")
            print("        to read): worst |diff| = %.4f pp over %d years -> %s"
                  % (worst_wrong, nw, "the test DISCRIMINATES (good)" if worst_wrong > 1.0 else "**the test cannot tell the blocks apart**"))
            if worst_wrong <= 1.0:
                FAIL.append("N5")

# ---------- FF5 RMW
fb, sent_ff = french_blocks("D3_FF5.zip")
print("\nFF5 file: %d blocks, sentinels censused = %d" % (len(fb), sent_ff))
for i, (lab, cols, rows) in enumerate(fb):
    ks = sorted(rows)
    print("  block %d n=%-5d keylen=%d %s..%s | %s" % (i, len(rows), len(ks[0]), ks[0], ks[-1], lab[:70]))
mon = [b for b in fb if len(sorted(b[2])[0]) == 6][0]
_, ffcols, ffrows = mon
ri = ffcols.index("RMW")
rmw = {}
for k, v in ffrows.items():
    if v[ri] is not None:
        rmw["%s-%s" % (k[:4], k[4:])] = v[ri]
print("  RMW monthly: n=%d  %s..%s  mean=%.4f" % (len(rmw), min(rmw), max(rmw), sum(rmw.values()) / len(rmw)))
OUT["rmw_n"] = len(rmw)
OUT["rmw_range"] = [min(rmw), max(rmw)]
OUT["rmw_mean"] = sum(rmw.values()) / len(rmw)

# ---------- CZ series, both weightings
def cz(zname, sigs):
    z = zipfile.ZipFile(os.path.join(HERE, zname))
    out = {}
    with z.open(z.namelist()[0]) as f:
        for row in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8")):
            if row["signalname"] in sigs and row["port"] == "LS" and row["ret"] not in ("NA", ""):
                out.setdefault(row["signalname"], {})[row["date"][:7]] = float(row["ret"])
    return out


print("\n" + "=" * 96)
print("CROSS-DATASET CORRELATIONS WITH FRENCH'S RMW (monthly, overlapping months only)")
print("=" * 96)
res = {}
for zname, tag in (("D3_CZ_QuintilesVW.zip", "CZ VW quintiles"), ("D3_CZ_QuintilesEW.zip", "CZ EW quintiles")):
    d = cz(zname, {"GP", "OperProf", "OperProfRD", "CBOperProf"})
    for s in ("OperProf", "GP", "OperProfRD", "CBOperProf"):
        if s not in d:
            continue
        for lo, lbl in ((None, "full overlap"), ("2010-01", "2010-01 onward")):
            ks = sorted(set(d[s]) & set(rmw))
            if lo:
                ks = [k for k in ks if k >= lo]
            c = corr([d[s][k] for k in ks], [rmw[k] for k in ks])
            res["%s|%s|%s" % (tag, s, lbl)] = {"corr": c, "n": len(ks), "first": ks[0], "last": ks[-1]}
            print("  %-16s %-12s %-15s corr(RMW, .) = %+0.4f   n=%d  %s..%s"
                  % (tag, s, lbl, c, len(ks), ks[0], ks[-1]))
OUT["rmw_corr"] = res

print("\n" + "=" * 96)
print("CONTROL SUMMARY: %s" % ("ALL PASS" if not FAIL else "FAILURES %s" % FAIL))
print("=" * 96)
OUT["control_failures"] = FAIL
json.dump(OUT, open(os.path.join(HERE, "D3_factor_corr_measurement.json"), "w"), indent=1, default=str)
print("wrote D3_factor_corr_measurement.json")
