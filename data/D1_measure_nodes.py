"""D1 independent measurement: what two unexamined construction nodes do to a
LONG LEG versus to a SPREAD, using only Kenneth R. French's published portfolio
returns.  No private data.  Pure stdlib.

Endpoint: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/
  Portfolios_Formed_on_OP_CSV.zip    (operating profitability, VW/EW, 3/5/10 buckets)
  Portfolios_Formed_on_E-P_CSV.zip   (earnings/price, with a SEPARATE "<= 0" bucket
                                      for loss-makers -- the node made observable)
  F-F_Research_Data_5_Factors_2x3_CSV.zip  (RF)

NODE A -- dropping loss-makers.  French puts firms with negative earnings in their
          own bucket and forms the E/P deciles on positive-E/P firms only, so the
          node is directly observable: what does the dropped set earn, how big is
          it, and what happens to the bottom leg if you put it back?
NODE B -- outlier treatment applied to the RETURN SERIES (winsorise / trim /
          asymmetric trim / level-vs-log), measured on a LONG LEG and on the
          SPREAD side by side, which no source in this corpus does.
"""
import zipfile, os, re, math, json, random

HERE = os.path.dirname(os.path.abspath(__file__))
FF = os.path.join(HERE, "ff")
OUT = []


def say(s=""):
    print(s)
    OUT.append(s)


# ---------------------------------------------------------------- parsing
def read_blocks(zname):
    """Split a French CSV into labelled blocks -> {label: (header, {date: [vals]})}."""
    z = zipfile.ZipFile(os.path.join(FF, zname))
    name = z.namelist()[0]
    txt = z.read(name).decode("latin-1").splitlines()
    blocks, label, header, rows = {}, None, None, None
    for line in txt:
        s = line.rstrip()
        if not s.strip():
            continue
        if re.match(r"^\s*\d{6}\s*,", s):                    # monthly data row
            parts = [p.strip() for p in s.split(",")]
            if rows is not None:
                rows[int(parts[0])] = [float(p) for p in parts[1:] if p != ""]
            continue
        if re.match(r"^\s*\d{4}\s*,", s):                    # annual row - skip
            continue
        if s.startswith(","):                                # column header
            header = [p.strip() for p in s.split(",")[1:] if p.strip() != ""]
            continue
        if rows and label is not None:
            blocks[label] = (header, rows)
        label, rows, header = s.strip(), {}, None
    if rows and label is not None:
        blocks[label] = (header, rows)
    return blocks


def pick(blocks, want):
    for lab, (h, r) in blocks.items():
        if want.lower() in lab.lower():
            ks = list(r)
            if ks and ks[0] > 100000 and (ks[0] % 100) <= 12:
                return lab, h, r
    raise KeyError(want)


def col(h, r, name, lo=None, hi=None):
    j = h.index(name)
    return {d: v[j] for d, v in sorted(r.items())
            if (lo is None or d >= lo) and (hi is None or d <= hi)}


def tstat(xs):
    n = len(xs)
    m = sum(xs) / n
    v = sum((x - m) ** 2 for x in xs) / (n - 1)
    sd = math.sqrt(v)
    return m, sd, m / (sd / math.sqrt(n)), n


# ---------------------------------------------------------------- outlier ops
def winsorise(xs, q):
    """Rank-based two-sided winsorisation: replace the k lowest and k highest by
    the (k+1)-th order statistic, k = floor(q*n).  Deterministic, count-exact."""
    n = len(xs)
    k = int(math.floor(q * n))
    if k == 0:
        return list(xs), 0
    s = sorted(xs)
    lo, hi = s[k], s[n - 1 - k]
    out = [min(max(x, lo), hi) for x in xs]
    changed = sum(1 for a, b in zip(xs, out) if a != b)
    return out, changed


def trim(xs, q_lo, q_hi):
    """Drop the floor(q_lo*n) lowest and floor(q_hi*n) highest observations."""
    n = len(xs)
    klo, khi = int(math.floor(q_lo * n)), int(math.floor(q_hi * n))
    s = sorted(xs)
    kept = s[klo: n - khi] if khi else s[klo:]
    return kept, n - len(kept)


# ---------------------------------------------------------------- load
op = read_blocks("Portfolios_Formed_on_OP_CSV.zip")
ep = read_blocks("Portfolios_Formed_on_E-P_CSV.zip")
f5 = read_blocks("F-F_Research_Data_5_Factors_2x3_CSV.zip")

say("=" * 78)
say("D1  [MEASURED IN BRIEF]  endpoint: mba.tuck.dartmouth.edu/.../ken.french/ftp/")
say("vintage stamp inside every file: 'This file was created using the 202607 CRSP database.'")
say("=" * 78)
say("OP blocks: %s" % list(op))
say("EP blocks: %s" % list(ep))

op_lab_ew, op_h_ew, op_r_ew = pick(op, "Equal Weight")
op_lab_vw, op_h_vw, op_r_vw = pick(op, "Value Weight")
ep_lab_ew, ep_h_ew, ep_r_ew = pick(ep, "Equal Weight")
ep_lab_vw, ep_h_vw, ep_r_vw = pick(ep, "Value Weight")
ep_lab_n, ep_h_n, ep_r_n = pick(ep, "Number of Firms")
ep_lab_s, ep_h_s, ep_r_s = pick(ep, "Average Firm Size")
f5_lab, f5_h, f5_r = pick(f5, "")

say("OP EW block %r cols %s" % (op_lab_ew, op_h_ew))
say("EP EW block %r cols %s" % (ep_lab_ew, ep_h_ew))
say("EP N  block %r cols %s" % (ep_lab_n, ep_h_n))
say("F5 block %r cols %s" % (f5_lab, f5_h))

RF = col(f5_h, f5_r, "RF")

# ================================================================ NEG CONTROLS
say()
say("=" * 78)
say("NEGATIVE CONTROLS  (each states what MUST be true; a failure is reported)")
say("=" * 78)
nc = {}

# NC1  winsorising at q=0 must be an exact identity
probe = list(col(op_h_ew, op_r_ew, "Hi 10").values())
w0, ch0 = winsorise(probe, 0.0)
nc["NC1 winsorise q=0 is an exact identity"] = (
    max(abs(a - b) for a, b in zip(probe, w0)) == 0.0 and ch0 == 0)

# NC2  count altered by a rank winsorisation must be EXACTLY 2*floor(q*n)
n_probe = len(probe)
_, ch1 = winsorise(probe, 0.01)
nc["NC2 winsorise 1/99 alters exactly 2*floor(.01n)=%d obs" % (2 * int(0.01 * n_probe))] = (
    ch1 == 2 * int(math.floor(0.01 * n_probe)))

# NC3  sentinel census: -99.99 / -999 must not appear in any block we use
sent = 0
for (h, r) in [(op_h_ew, op_r_ew), (op_h_vw, op_r_vw), (ep_h_ew, ep_r_ew),
               (ep_h_vw, ep_r_vw), (ep_h_n, ep_r_n), (ep_h_s, ep_r_s)]:
    for d, v in r.items():
        sent += sum(1 for x in v if x in (-99.99, -999.0))
nc["NC3 sentinel (-99.99/-999) count in every block used == 0"] = (sent == 0)

# NC4  the long leg and the spread must never be the same number
hi = col(op_h_ew, op_r_ew, "Hi 10")
lo = col(op_h_ew, op_r_ew, "Lo 10")
same = sum(1 for d in hi if d in RF and abs((hi[d] - RF[d]) - (hi[d] - lo[d])) < 1e-12)
nc["NC4 long-leg series never equals spread series (guards double-read) == 0"] = (same == 0)

# NC5  IDENTITY: EW 'Lo 30' must equal the firm-count-weighted mean of EW deciles 1-3
ep_n_cols = ep_h_n
dec_names = ["Lo 10", "2-Dec", "3-Dec"]
maxdiff, ndiff = 0.0, 0
for d in sorted(ep_r_ew):
    try:
        rs = [col(ep_h_ew, ep_r_ew, c)[d] for c in dec_names]
        ns = [col(ep_h_n, ep_r_n, c)[d] for c in dec_names]
    except Exception:
        continue
    if sum(ns) == 0:
        continue
    recon = sum(a * b for a, b in zip(rs, ns)) / sum(ns)
    truth = col(ep_h_ew, ep_r_ew, "Lo 30")[d]
    maxdiff = max(maxdiff, abs(recon - truth))
    ndiff += 1
nc["NC5 EW 'Lo 30' == count-weighted EW deciles 1-3 (n=%d, max|diff|=%.4f pp)" % (ndiff, maxdiff)] = (maxdiff < 0.02)

# NC6  power check: symmetric trimming of a SYMMETRIC series must not move the mean
random.seed(20260910)
sym = [random.gauss(0, 5) for _ in range(len(probe))]
kept, _ = trim(sym, 0.01, 0.01)
d_sym = abs(sum(kept) / len(kept) - sum(sym) / len(sym))
kept_r, _ = trim(probe, 0.01, 0.01)
d_real = abs(sum(kept_r) / len(kept_r) - sum(probe) / len(probe))
nc["NC6 power: sym-trim moves a SYMMETRIC series by %.4f pp, the real leg by %.4f pp" % (d_sym, d_real)] = (d_sym < d_real)

# NC7  a value that MUST be zero: months where the '<=0' bucket holds firms but
#      reports a sentinel return
n_neg = col(ep_h_n, ep_r_n, "<= 0")
r_neg = col(ep_h_ew, ep_r_ew, "<= 0")
bad = sum(1 for d in n_neg if n_neg[d] > 0 and r_neg.get(d, 0.0) in (-99.99, -999.0))
nc["NC7 months with firms in '<=0' but a sentinel return == 0"] = (bad == 0)

for k, v in nc.items():
    say("  [%s] %s" % ("PASS" if v else "**FIRED**", k))

# ================================================================ NODE A
say()
say("=" * 78)
say("NODE A -- DROPPING LOSS-MAKERS.  French E/P file, %s .. %s" %
    (min(ep_r_ew), max(ep_r_ew)))
say("French's own construction note: 'Portfolios: Earnings < 0; bottom 30%, middle")
say("40%, top 30%; quintiles; deciles.  Firms with negative earnings are in only")
say("the Earnings < 0 portfolio.'  So the drop is OBSERVABLE, not inferred.")
say("=" * 78)

WINDOWS = [("full", None, None), ("prog 2010-01..2026-06", 201001, 202606)]
nodeA = {}
for wname, w0_, w1_ in WINDOWS:
    nneg = col(ep_h_n, ep_r_n, "<= 0", w0_, w1_)
    sneg = col(ep_h_s, ep_r_s, "<= 0", w0_, w1_)
    tot = {}
    for d in nneg:
        tot[d] = sum(col(ep_h_n, ep_r_n, c, w0_, w1_)[d]
                     for c in ["<= 0", "Lo 10", "2-Dec", "3-Dec", "4-Dec", "5-Dec",
                               "6-Dec", "7-Dec", "8-Dec", "9-Dec", "Hi 10"])
    share = [100.0 * nneg[d] / tot[d] for d in sorted(nneg) if tot[d] > 0]
    say()
    say("[%s]  SIZE OF THE DROPPED SET" % wname)
    say("  loss-makers as %% of all sorted firms: mean %.2f%%  min %.2f%%  max %.2f%%  (n=%d months)"
        % (sum(share) / len(share), min(share), max(share), len(share)))
    # size tilt
    for wgt, lab in [("<= 0", "loss-makers"), ("Lo 10", "lowest E/P decile"),
                     ("Hi 10", "highest E/P decile")]:
        s = col(ep_h_s, ep_r_s, wgt, w0_, w1_)
        vals = [v for v in s.values() if v > 0]
        say("  average firm size, %-18s $%.1f m" % (lab, sum(vals) / len(vals)))
    # returns
    say("[%s]  WHAT THE DROPPED SET EARNS" % wname)
    for wt, hh, rr in [("EW", ep_h_ew, ep_r_ew), ("VW", ep_h_vw, ep_r_vw)]:
        for cname, lab in [("<= 0", "loss-makers"), ("Lo 10", "lowest E/P decile"),
                           ("Hi 10", "highest E/P decile (THE LONG LEG)")]:
            xs = list(col(hh, rr, cname, w0_, w1_).values())
            m, sd, t, n = tstat(xs)
            say("  %s %-38s mean %+7.3f  t %+6.2f  sd %5.2f  n %d" % (wt, lab, m, t, sd, n))
    # the counterfactual bottom leg: put the loss-makers back in
    say("[%s]  PUTTING THEM BACK: the bottom leg with and without loss-makers" % wname)
    for wt, hh, rr in [("EW", ep_h_ew, ep_r_ew), ("VW", ep_h_vw, ep_r_vw)]:
        lo_only, lo_plus, hi_l, ds = [], [], [], []
        for d in sorted(col(hh, rr, "Lo 10", w0_, w1_)):
            rl = col(hh, rr, "Lo 10", w0_, w1_)[d]
            rn = col(hh, rr, "<= 0", w0_, w1_)[d]
            nl = col(ep_h_n, ep_r_n, "Lo 10", w0_, w1_)[d]
            nn = col(ep_h_n, ep_r_n, "<= 0", w0_, w1_)[d]
            sl = col(ep_h_s, ep_r_s, "Lo 10", w0_, w1_)[d]
            sn = col(ep_h_s, ep_r_s, "<= 0", w0_, w1_)[d]
            if nl + nn == 0:
                continue
            if wt == "EW":
                comb = (rl * nl + rn * nn) / (nl + nn)
            else:
                wl, wn = nl * sl, nn * sn
                comb = (rl * wl + rn * wn) / (wl + wn) if (wl + wn) > 0 else rl
            lo_only.append(rl)
            lo_plus.append(comb)
            hi_l.append(col(hh, rr, "Hi 10", w0_, w1_)[d])
            ds.append(d)
        m1, _, t1, n1 = tstat(lo_only)
        m2, _, t2, _ = tstat(lo_plus)
        sp_drop = [a - b for a, b in zip(hi_l, lo_only)]
        sp_keep = [a - b for a, b in zip(hi_l, lo_plus)]
        ml, _, tl, _ = tstat(hi_l)
        md, _, td, _ = tstat(sp_drop)
        mk, _, tk, _ = tstat(sp_keep)
        say("  %s bottom leg, loss-makers DROPPED (French 'Lo 10')  mean %+7.3f  t %+6.2f" % (wt, m1, t1))
        say("  %s bottom leg, loss-makers KEPT   (reconstructed)    mean %+7.3f  t %+6.2f" % (wt, m2, t2))
        say("  %s LONG LEG 'Hi 10' -- IDENTICAL under both branches  mean %+7.3f  t %+6.2f" % (wt, ml, tl))
        say("  %s SPREAD  Hi-Lo, loss-makers dropped                 mean %+7.3f  t %+6.2f" % (wt, md, td))
        say("  %s SPREAD  Hi-Lo, loss-makers kept                    mean %+7.3f  t %+6.2f" % (wt, mk, tk))
        say("  %s ===> node moves the SPREAD by %+0.3f pp/mo (t %+0.2f) and the LONG LEG by 0.000 pp/mo (0.00) BY CONSTRUCTION"
            % (wt, mk - md, tk - td))
        nodeA["%s/%s" % (wname, wt)] = dict(lo_drop=m1, lo_keep=m2, hi=ml,
                                            spread_drop=md, spread_keep=mk,
                                            t_spread_drop=td, t_spread_keep=tk, n=n1)

# ================================================================ NODE B
say()
say("=" * 78)
say("NODE B -- OUTLIER TREATMENT APPLIED TO THE RETURN SERIES, and LEVEL vs LOG.")
say("Object 1: EW top OP decile MINUS RF   (a cash-funded LONG LEG)")
say("Object 2: EW top OP decile MINUS EW bottom OP decile  (the SPREAD)")
say("=" * 78)
nodeB = {}
for wname, w0_, w1_ in WINDOWS:
    for wt, hh, rr in [("EW", op_h_ew, op_r_ew), ("VW", op_h_vw, op_r_vw)]:
        H = col(hh, rr, "Hi 10", w0_, w1_)
        L = col(hh, rr, "Lo 10", w0_, w1_)
        ds = [d for d in sorted(H) if d in RF]
        leg = [H[d] - RF[d] for d in ds]
        spr = [H[d] - L[d] for d in ds]
        for oname, obj in [("LONG LEG (Hi10-RF)", leg), ("SPREAD (Hi10-Lo10)", spr)]:
            m0, _, t0, n0 = tstat(obj)
            say()
            say("[%s] %s %s   n=%d" % (wname, wt, oname, n0))
            say("   %-34s mean %+7.3f  t %+6.2f   |dt| ref" % ("raw (no outlier treatment)", m0, t0))
            rows = []
            for lab, fn in [
                ("winsorise 1/99", lambda x: winsorise(x, 0.01)[0]),
                ("trim 1/99", lambda x: trim(x, 0.01, 0.01)[0]),
                ("winsorise 5/95", lambda x: winsorise(x, 0.05)[0]),
                ("trim 5/95", lambda x: trim(x, 0.05, 0.05)[0]),
                ("trim TOP 1% only (drop winners)", lambda x: trim(x, 0.0, 0.01)[0]),
                ("trim BOTTOM 1% only (drop losers)", lambda x: trim(x, 0.01, 0.0)[0]),
            ]:
                y = fn(obj)
                m, _, t, n = tstat(y)
                say("   %-34s mean %+7.3f  t %+6.2f   |dt| %5.2f   n %d" % (lab, m, t, abs(t - t0), n))
                rows.append((lab, m, t, abs(t - t0), n))
            # level vs log
            mlog = sum(math.log(1 + x / 100.0) for x in obj) / len(obj) * 100.0
            say("   %-34s mean %+7.3f            (level minus log = %+0.3f pp/mo)"
                % ("LOG convention, mean log(1+r)", mlog, m0 - mlog))
            nodeB["%s/%s/%s" % (wname, wt, oname)] = dict(raw_mean=m0, raw_t=t0,
                                                          rows=rows, log_mean=mlog, n=n0)

# the log node on the two objects, stated side by side
say()
say("=" * 78)
say("THE LEVEL-vs-LOG NODE, SIGN CHECK ON THE TWO OBJECTS")
say("(WWW compute log_premium = log(1+r_hi) - log(1+r_lo); a long leg has no")
say(" second leg whose variance can cancel, so the two objects should differ.)")
say("=" * 78)
for wname, w0_, w1_ in WINDOWS:
    for wt, hh, rr in [("EW", op_h_ew, op_r_ew), ("VW", op_h_vw, op_r_vw)]:
        H = col(hh, rr, "Hi 10", w0_, w1_)
        L = col(hh, rr, "Lo 10", w0_, w1_)
        ds = [d for d in sorted(H) if d in RF]
        leg = [H[d] - RF[d] for d in ds]
        spr = [H[d] - L[d] for d in ds]
        log_leg = [100 * (math.log(1 + H[d] / 100) - math.log(1 + RF[d] / 100)) for d in ds]
        log_spr = [100 * (math.log(1 + H[d] / 100) - math.log(1 + L[d] / 100)) for d in ds]
        a, _, ta, _ = tstat(leg)
        b, _, tb, _ = tstat(log_leg)
        c, _, tc, _ = tstat(spr)
        e, _, te, _ = tstat(log_spr)
        _, sdH, _, _ = tstat([H[d] for d in ds])
        _, sdL, _, _ = tstat([L[d] for d in ds])
        say("[%s] %s  LONG LEG  level %+0.3f (t %+.2f) -> log %+0.3f (t %+.2f)   change %+0.3f"
            % (wname, wt, a, ta, b, tb, b - a))
        say("[%s] %s  SPREAD    level %+0.3f (t %+.2f) -> log %+0.3f (t %+.2f)   change %+0.3f"
            % (wname, wt, c, tc, e, te, e - c))
        say("        sd(Hi)=%0.2f  sd(Lo)=%0.2f  -> half the variance gap = %+0.3f pp/mo"
            % (sdH, sdL, (sdL ** 2 - sdH ** 2) / 2 / 100))

with open(os.path.join(HERE, "D1_measurement.json"), "w") as f:
    json.dump({"negative_controls": {k: bool(v) for k, v in nc.items()},
               "node_A_lossmakers": nodeA, "node_B_outliers": nodeB}, f, indent=1)
with open(os.path.join(HERE, "D1_measurement.txt"), "w") as f:
    f.write("\n".join(OUT))
print("\nwrote D1_measurement.txt / .json")
