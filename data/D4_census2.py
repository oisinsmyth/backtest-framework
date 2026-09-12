"""D4 ARRIVAL-STATISTIC CENSUS, hardened after the v1 control FIRED.

v1 used literal substrings and returned 0 for "t-statistic" in Engelberg/McLean/Pontiff and
0 for "average return" in Chen/Zimmermann -- both certainly present in substance. Cause:
pdftotext inserts spaces and splits hyphens, and the papers use "t-stat"/"mean return".
So every probe is now a REGEX tolerant of whitespace and hyphen variants, and the
must-be-positive control is re-run. A census whose control fails is not reported as evidence.
"""
import os, re, json

HERE = os.path.dirname(os.path.abspath(__file__))

PAPERS = {
    "Novy-Marx 2012 WP, The Other Side of Value (73pp)": "D4_osov.txt",
    "Engelberg/McLean/Pontiff 2017 WP, Anomalies and News": "D4_anomalies_news.txt",
    "Hou/Xue/Zhang 2017 NBER WP 23394, Replicating Anomalies": "D4_hxz_replicating.pdf.txt",
    "McLean/Pontiff WP, Does Academic Research Destroy...": "D4_mclean_pontiff.pdf.txt",
    "Chen/Zimmermann 2021 FEDS 2021-037, Open Source X-Sec AP": "D4_chen_zimmermann.pdf.txt",
    "Ilmanen et al 2021 JOIM, How Do Factor Premia Vary Over Time": "D4_ilmanen_joim.txt",
}

S = r"[\s\-‐-―]*"        # optional whitespace / any hyphen-dash


def rx(*alts):
    return re.compile("|".join(alts), re.I)


PROBES = {
    # --- arrival / concentration IN TIME
    "drawdown":            rx(r"draw" + S + r"down", r"under" + S + r"water", r"peak" + S + r"to" + S + r"trough"),
    "best/worst month":    rx(r"(best|worst|largest|top)" + S + r"(\w+\s+){0,2}months?\b",
                              r"months?\s+(with|of)\s+the\s+(best|worst|largest)"),
    "months to half":      rx(r"months?" + S + r"to" + S + r"(reach|half)", r"half" + S + r"(of\s+)?the" + S + r"(total|cumulative|sum)"),
    "fraction of months":  rx(r"(fraction|percent(age)?|proportion|share|number)\s+of\s+(the\s+)?months",
                              r"months?\s+(are|were|with)\s+positive", r"positive" + S + r"months?",
                              r"hit" + S + r"rate"),
    "concentrat*":         rx(r"concentrat"),
    # --- shape of the monthly distribution
    "skewness":            rx(r"skew"),
    "kurtosis":            rx(r"kurtos", r"fat" + S + r"tail"),
    "winsorise/trim":      rx(r"winsoriz", r"winsoris", r"\btrimm?(ed|ing)\b"),
    # --- clustering / regimes
    "recession/cycle":     rx(r"recession", r"business" + S + r"cycle", r"NBER"),
    "regime":              rx(r"regime"),
    "cluster":             rx(r"cluster"),
    # --- concentration IN NAMES
    "few names carry it":  rx(r"(few|handful of|small number of)\s+(\w+\s+){0,2}(stocks|firms|names|companies)",
                              r"wealth" + S + r"creation", r"driven\s+by\s+a\s+few"),
    # --- required horizon
    "required horizon":    rx(r"how\s+long", r"required\s+(sample|horizon)",
                              r"(years|decades)\s+(of\s+data\s+)?(are\s+)?(needed|required)",
                              r"long" + S + r"horizon"),
}

MUST_POS = {
    # v2's control FIRED again: Novy-Marx (2012) writes "test-statistic" 26 times and never
    # "t-statistic"; Engelberg/McLean/Pontiff write "standard error" 11 times and never
    # "t-statistic" at all. Both times the PROBE was wrong, not the paper silent.
    "t-statistic/t-stat": rx(r"\b(t|test)" + S + r"stat", r"\bt" + S + r"value", r"standard" + S + r"error"),
    "average/mean return": rx(r"(average|mean)" + S + r"(monthly\s+)?(excess\s+)?returns?"),
}
MUST_ZERO = {"impossible token": rx(r"zzqqx")}

OUT = {}
for label, fn in PAPERS.items():
    p = os.path.join(HERE, fn)
    if not os.path.exists(p):
        OUT[label] = {"ERROR": "missing " + fn}
        continue
    txt = open(p, encoding="utf-8", errors="replace").read()
    rec = {"chars": len(txt), "first_line": txt.strip().splitlines()[0][:90]}
    rec["counts"] = {k: len(v.findall(txt)) for k, v in PROBES.items()}
    rec["CTRL_pos"] = {k: len(v.findall(txt)) for k, v in MUST_POS.items()}
    rec["CTRL_zero"] = {k: len(v.findall(txt)) for k, v in MUST_ZERO.items()}
    rec["CTRL_PASS"] = (all(x > 0 for x in rec["CTRL_pos"].values())
                        and all(x == 0 for x in rec["CTRL_zero"].values()))
    OUT[label] = rec

json.dump(OUT, open(os.path.join(HERE, "D4_census2.json"), "w"), indent=1)

keys = list(PROBES)
print("ARRIVAL-STATISTIC CENSUS (regex, whitespace/hyphen tolerant). 0 = the paper never uses the term.")
print()
w = 24
print("probe".ljust(w) + "".join(("P%d" % (i + 1)).rjust(6) for i in range(len(OUT))))
for i, (label, r) in enumerate(OUT.items(), 1):
    print("   P%d = %s   [ctrl %s]" % (i, label, "PASS" if r.get("CTRL_PASS") else "FAIL " + str(r.get("CTRL_pos"))))
print()
for k in keys:
    print(k.ljust(w) + "".join(str(r["counts"][k]).rjust(6) for r in OUT.values()))
print()
print("controls".ljust(w) + "".join(("PASS" if r["CTRL_PASS"] else "FAIL").rjust(6) for r in OUT.values()))
print("t-stat hits".ljust(w) + "".join(str(r["CTRL_pos"]["t-statistic/t-stat"]).rjust(6) for r in OUT.values()))
print("mean-return hits".ljust(w) + "".join(str(r["CTRL_pos"]["average/mean return"]).rjust(6) for r in OUT.values()))
