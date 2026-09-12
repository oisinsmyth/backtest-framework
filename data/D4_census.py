"""D4 ARRIVAL-STATISTIC CENSUS.

For each paper read in full as local text, count case-insensitive occurrences of the words
an ARRIVAL or CONCENTRATION statistic would have to use, beside the words that every one of
these papers certainly does use.

NEGATIVE CONTROLS, both directions:
  POSITIVE: "t-statistic"/"t-stat" and "average return" MUST be > 0 in every paper --
            if one returns 0 the extraction is broken, not the paper silent.
  ZERO:     a token that cannot appear ("zzqqx") MUST return 0 in every paper --
            if it does not, the counter is broken.
"""
import os, re, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))

PAPERS = {
    "Novy-Marx 2012 WP, The Other Side of Value (73pp)": "D4_osov.txt",
    "Engelberg/McLean/Pontiff 2017 WP, Anomalies and News": "D4_anomalies_news.txt",
    "Hou/Xue/Zhang 2017 NBER WP 23394, Replicating Anomalies": "D4_hxz_replicating.pdf.txt",
    "McLean/Pontiff WP, Does Academic Research Destroy...": "D4_mclean_pontiff.pdf.txt",
    "Chen/Zimmermann 2021 FEDS 2021-037, Open Source Cross-Sectional AP": "D4_chen_zimmermann.pdf.txt",
    "Ilmanen et al 2021 JOIM, How Do Factor Premia Vary Over Time": "D4_ilmanen_joim.txt",
}

ARRIVAL = [
    # concentration in time
    "months to", "best month", "worst month", "best k", "top month",
    "positive months", "fraction of months", "percent of months", "proportion of months",
    "hit rate", "concentrat", "drawdown", "draw-down", "underwater",
    "half of the total", "half the total", "half of the cumulative",
    # shape of the monthly distribution
    "skew", "kurtos", "fat tail", "fat-tail", "winsor", "trim",
    # clustering / regimes
    "recession", "business cycle", "regime", "cluster",
    # concentration in names
    "number of stocks that", "few stocks", "handful of", "wealth creation",
    # horizon
    "horizon", "how long", "required sample",
]
MUST_BE_POSITIVE = ["t-statistic", "average return"]
MUST_BE_ZERO = ["zzqqx"]

OUT = {}
for label, fn in PAPERS.items():
    p = os.path.join(HERE, fn)
    if not os.path.exists(p):
        OUT[label] = {"ERROR": "missing " + fn}
        continue
    txt = open(p, encoding="utf-8", errors="replace").read()
    low = txt.lower()
    rec = {"chars": len(txt), "first_line": txt.strip().splitlines()[0][:90]}
    rec["arrival_words"] = {w: low.count(w) for w in ARRIVAL}
    rec["arrival_words_nonzero"] = {w: c for w, c in rec["arrival_words"].items() if c}
    rec["CONTROL_must_be_positive"] = {w: low.count(w) for w in MUST_BE_POSITIVE}
    rec["CONTROL_must_be_zero"] = {w: low.count(w) for w in MUST_BE_ZERO}
    rec["CONTROL_PASS"] = (all(v > 0 for v in rec["CONTROL_must_be_positive"].values())
                           and all(v == 0 for v in rec["CONTROL_must_be_zero"].values()))
    OUT[label] = rec

json.dump(OUT, open(os.path.join(HERE, "D4_census.json"), "w"), indent=1)
for label, r in OUT.items():
    if "ERROR" in r:
        print("!!", label, r["ERROR"]); continue
    print("=" * 100)
    print(label)
    print("   first line:", r["first_line"])
    print("   CONTROLS  must-be-positive %s  must-be-zero %s  -> %s"
          % (r["CONTROL_must_be_positive"], r["CONTROL_must_be_zero"],
             "PASS" if r["CONTROL_PASS"] else "FAIL"))
    print("   arrival words PRESENT :", r["arrival_words_nonzero"])
    print("   arrival words ABSENT  :", sorted(w for w, c in r["arrival_words"].items() if not c))
