"""K1 final stage: classify each 8-A12B / Form-25 pair into a DIRECTED exchange
listing transfer and count by year and direction.

ORIGIN       from the 25-NSE accession prefix (= the filing exchange's CIK),
             else parsed from the issuer-filed Form 25 document.
DESTINATION  from the 8-A12B cover page "Name of each exchange on which each
             class is to be registered".
SECURITY     from the 8-A12B cover page "Title of each class to be so registered".

Negative controls reported: ZZ-NOTAFORM index rows (0), bogus accession paths
(all error), placebo CIK-shuffled pairing (from K1_pair.py), and a deliberate
check that a KNOWN transfer (PepsiCo 2017 NYSE->NASDAQ) is classified correctly.
"""
import collections, csv, datetime as dt, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "K1_doccache")

PREFIX = {"0000876661": "NYSE", "0001143362": "NYSE_ARCA",
          "0001354457": "NASDAQ", "0001417835": "CBOE",
          "0001143313": "NYSE_AMERICAN"}
ACC = re.compile(r"/(\d{10})-(\d\d)-(\d{6})")

def read(path):
    p = os.path.join(CACHE, path.replace("/", "_"))
    if not os.path.exists(p):
        return None
    t = open(p, encoding="utf-8", errors="replace").read()
    return None if t.startswith("__") else t

def detag(t):
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    for a, b in (("&nbsp;", " "), ("&amp;", "&"), ("&#146;", "'"),
                 ("&rsquo;", "'"), ("&#8217;", "'"), ("&quot;", '"'),
                 ("&#160;", " "), ("&#8220;", '"'), ("&#8221;", '"')):
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t)

EXCH = [
    ("NYSE_AMERICAN", r"NYSE\s*American|NYSE\s*MKT|NYSE\s*Amex|American Stock Exchange"),
    ("NYSE_ARCA",     r"NYSE\s*Arca|Archipelago"),
    ("NYSE_NATIONAL", r"NYSE\s*National|National Stock Exchange"),
    ("NYSE_CHICAGO",  r"NYSE\s*Chicago|Chicago Stock Exchange"),
    ("NASDAQ",        r"(?i)nasdaq"),
    ("CBOE",          r"(?i)cboe|BATS"),
    ("IEX",           r"(?i)investors exchange"),
    ("LTSE",          r"(?i)long-?term stock exchange"),
    ("MIAX",          r"(?i)miax|miami international"),
    ("NYSE",          r"New York Stock Exchange|NYSE"),
]
def exch_of(s):
    for n, p in EXCH:
        if re.search(p, s):
            return n
    return ""

COMMON = re.compile(r"(?i)common stock|common share|ordinary share|"
                    r"class\s+[a-d]\s+common|shares of beneficial interest|"
                    r"common unit|depositary shares representing common")
NOTCOMMON = re.compile(r"(?i)\bnotes?\b|debenture|\bbonds?\b|warrant|\bunits?\b|"
                       r"\brights?\b|preferred|subordinat|senior\s|capital securit|"
                       r"%|due\s+(19|20)\d\d|contingent value")

HDR = re.compile(r"(?i)name\s+of\s+each\s+exchange\s+on\s+which(?:\s+each)?"
                 r"\s+class\s+is\s+to\s+be\s+registered|"
                 r"name\s+of\s+each\s+exchange\s+on\s+which\s+registered")

def parse_8a(txt):
    """In the flattened 8-A cover page both column HEADERS come first and the
    VALUES follow, so the class title and the exchange name both sit in the
    segment after the 'Name of each exchange...' header."""
    flat = detag(txt)
    m = HDR.search(flat)
    if not m:
        return None
    seg = flat[m.end(): m.end() + 1400]
    m2 = re.search(r"(?i)if this form relates|securities to be registered "
                   r"pursuant to section 12\(g\)|item 1\.|title of class", seg)
    if m2:
        seg = seg[:m2.start()]
    dest = exch_of(seg)
    # class title = the text before the first exchange-name token
    cls = seg
    if dest:
        for n, p in EXCH:
            if n == dest:
                mm = re.search(p, seg)
                if mm:
                    cls = seg[:mm.start()]
                break
    return {"dest": dest, "dest_ctx": seg[:200], "cls": cls[:240]}

def parse_25(txt):
    m = re.search(r"<exchange>.*?<entityName>([^<]*)</entityName>", txt, re.S)
    if m:
        xent = m.group(1)
    else:
        xent = detag(txt)[:6000]
    m = re.search(r"<descriptionClassSecurity>([^<]*)</descriptionClassSecurity>", txt)
    sd = m.group(1).strip() if m else ""
    if not sd:
        f = detag(txt)
        m = re.search(r"(?i)description of class of securit(?:y|ies)[:\s]*(.{0,140})", f)
        sd = m.group(1).strip() if m else ""
    m = re.search(r"<ruleProvision>([^<]*)</ruleProvision>", txt)
    rule = m.group(1).strip() if m else ""
    if not rule:
        m = re.search(r"12d2-2\s*\(\s*([abc])\s*\)(?:\s*\(\s*(\d)\s*\))?", detag(txt))
        rule = (f"12d2-2({m.group(1)})" + (f"({m.group(2)})" if m.group(2) else "")) \
               if m else ""
    return {"orig": exch_of(xent), "sec_desc": sd, "rule": rule}

FUND = re.compile(r"(?i)\b(trust|fund|etf|ishares|spdr|proshares|invesco|"
                  r"wisdomtree|vaneck|direxion|powershares|portfolio|index|"
                  r"series|advisorshares|first trust|global x|etfs?)\b")

pairs = [p for p in csv.DictReader(open(os.path.join(HERE, "K1_pairs.tsv"),
                                       encoding="utf-8"), delimiter="\t")
         if abs(int(p["gap"])) <= 45 and p["a_date"] >= "2010-01-01"]
print("pairs considered (|gap|<=45, 2010+):", len(pairs))

rows, nomiss = [], collections.Counter()
for p in pairs:
    a = read(p["a_file"])
    if a is None:
        nomiss["8A_missing"] += 1
        continue
    pa = parse_8a(a)
    if pa is None:
        nomiss["8A_no_exchange_header"] += 1
        continue
    m = ACC.search(p["r_file"])
    if p["r_form"].startswith("25-NSE") and m and m.group(1) in PREFIX:
        orig, sd, rule = PREFIX[m.group(1)], "", "(exchange-filed)"
    else:
        r = read(p["r_file"])
        if r is None:
            nomiss["25_missing"] += 1
            continue
        pr = parse_25(r)
        orig, sd, rule = pr["orig"], pr["sec_desc"], pr["rule"]
    rows.append(dict(cik=p["cik"], company=p["company"], a_date=p["a_date"],
                     r_date=p["r_date"], gap=p["gap"], r_form=p["r_form"],
                     orig=orig, dest=pa["dest"], cls=pa["cls"],
                     rule=rule, sec_desc=sd, dest_ctx=pa["dest_ctx"],
                     fundish=bool(FUND.search(p["company"]))))
print("resolved rows:", len(rows), " dropped:", dict(nomiss))

# --- SELF-TEST: a known transfer must classify correctly -------------------
pep = [r for r in rows if r["cik"] == "77476" and r["a_date"].startswith("2017")]
print("\n=== SELF-TEST: PepsiCo 2017 (known NYSE -> NASDAQ transfer) ===")
if not pep:
    print("  *** FAIL: PepsiCo 2017 pair not present in the candidate set ***")
else:
    for r in pep:
        ok = (r["orig"] == "NYSE" and r["dest"] == "NASDAQ")
        print(f"  orig={r['orig']} dest={r['dest']} cls={r['cls'][:60]!r} "
              f"-> {'PASS' if ok else '*** FAIL ***'}")
# deliberate break: the same parser must NOT find a destination in a Form 25
broke = parse_8a("<html>Form 25 body with no exchange column header</html>")
print("  deliberate-break check (parser on a doc with no exchange header):",
      "PASS (returned None)" if broke is None else f"*** FAIL: {broke}")

THREE = ("NYSE", "NASDAQ", "NYSE_AMERICAN")
common_cls = [r for r in rows if COMMON.search(r["cls"] or "")
              and not NOTCOMMON.search(r["cls"] or "")]
print(f"\nof {len(rows)} resolved pairs, 8-A12B registers COMMON EQUITY in "
      f"{len(common_cls)}")

op = [r for r in common_cls if not r["fundish"]]
print("of those, not fund/ETF-named:", len(op))

directed = [r for r in op if r["orig"] in THREE and r["dest"] in THREE
            and r["orig"] != r["dest"]]
print("DIRECTED transfers among the three operating-company venues:", len(directed))

# dedupe: an issuer sometimes files the 8-A12B more than once for the same move
directed.sort(key=lambda z: z["a_date"])
ded, last = [], {}
dups = 0
for r in directed:
    k = (r["cik"], r["orig"], r["dest"])
    d = dt.date.fromisoformat(r["a_date"])
    if k in last and (d - last[k]).days <= 120:
        dups += 1
        continue
    last[k] = d
    ded.append(r)
print(f"after de-duplicating repeat filings of the same move within 120d: "
      f"{len(ded)} ({dups} duplicates removed)")
directed = ded

print("\n=== TRANSFERS PER YEAR BY DIRECTION (8-A12B date) ===")
yr = collections.defaultdict(collections.Counter)
for r in directed:
    yr[int(r["a_date"][:4])][f'{r["orig"]}->{r["dest"]}'] += 1
keys = sorted({k for c in yr.values() for k in c},
              key=lambda k: -sum(yr[y][k] for y in yr))
w = max(len(k) for k in keys) + 2
print("year " + "".join(f"{k:>{w}s}" for k in keys) + f"{'TOTAL':>8s}")
for y in range(2010, 2027):
    if y not in yr:
        print(f"{y} " + "".join(f"{0:>{w}d}" for k in keys) + f"{0:>8d}")
        continue
    print(f"{y} " + "".join(f"{yr[y][k]:>{w}d}" for k in keys) +
          f"{sum(yr[y].values()):>8d}")
print("ALL  " + "".join(f"{sum(yr[y][k] for y in yr):>{w}d}" for k in keys) +
      f"{len(directed):>8d}")

print("\n=== UP vs DOWN, collapsed ===")
UP = {("NASDAQ", "NYSE"), ("NYSE_AMERICAN", "NYSE"), ("NYSE_AMERICAN", "NASDAQ")}
DOWN = {("NYSE", "NASDAQ"), ("NYSE", "NYSE_AMERICAN"), ("NASDAQ", "NYSE_AMERICAN")}
cu = collections.Counter()
for r in directed:
    t = (r["orig"], r["dest"])
    cu["to_NYSE_from_NASDAQ" if t == ("NASDAQ", "NYSE") else
       "to_NASDAQ_from_NYSE" if t == ("NYSE", "NASDAQ") else
       "to_NYSE_AMERICAN" if t[1] == "NYSE_AMERICAN" else
       "from_NYSE_AMERICAN"] += 1
for k, v in cu.most_common():
    print(f"  {k:24s} {v}")

with open(os.path.join(HERE, "K1_transfers.tsv"), "w", encoding="utf-8",
          newline="") as fh:
    cols = ["a_date", "r_date", "gap", "cik", "company", "orig", "dest",
            "r_form", "rule", "cls", "sec_desc"]
    w2 = csv.DictWriter(fh, fieldnames=cols, delimiter="\t",
                        extrasaction="ignore")
    w2.writeheader()
    for r in sorted(directed, key=lambda z: z["a_date"]):
        r["cls"] = (r["cls"] or "")[:70].replace("\t", " ")
        w2.writerow(r)
print("\nwrote K1_transfers.tsv", len(directed))

print("\n=== every directed transfer, listed (for eyeball verification) ===")
for r in sorted(directed, key=lambda z: z["a_date"]):
    print(f"  {r['a_date']}  {r['orig']:13s} -> {r['dest']:13s} "
          f"{r['company'][:44]:44s} cik={r['cik']}")
