"""C1 pass 4: how stable is an AS-FILED quarterly panel?

FSDS `sub.txt` carries `prevrpt` ("Previous Report - TRUE indicates that the
submission information was subsequently amended"). Counting it, plus the 10-Q/A
form counts, measures how often a point-in-time quarterly observation is later
revised -- which is the integrity question under any filing-driven build.
Also counts nciks>1 (multi-registrant submissions).
"""
import zipfile, io, csv, json
from collections import Counter

ZIPS = ["C1_fsds_2013q2.zip", "C1_fsds_2013q3.zip", "C1_fsds_2013q4.zip",
        "C1_fsds_2019q2.zip", "C1_fsds_2019q3.zip", "C1_fsds_2019q4.zip",
        "C1_fsds_2025q2.zip", "C1_fsds_2025q3.zip", "C1_fsds_2025q4.zip"]

out = {}
for zf in ZIPS:
    c = Counter()
    with zipfile.ZipFile(zf) as z, z.open("sub.txt") as f:
        for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8", errors="replace"),
                                delimiter="\t"):
            form = r["form"]
            c["ALL"] += 1
            if form in ("10-Q", "10-K", "10-Q/A", "10-K/A"):
                c[form] += 1
            if form == "10-Q":
                if r["prevrpt"] == "1":
                    c["10Q_prevrpt"] += 1
                if r["nciks"] not in ("1", ""):
                    c["10Q_multiregistrant"] += 1
                if r["detail"] == "0":
                    c["10Q_detail0"] += 1
    q = c["10-Q"]
    out[zf] = {
        "submissions": c["ALL"], "10-Q": q, "10-K": c["10-K"],
        "10-Q/A": c["10-Q/A"], "10-K/A": c["10-K/A"],
        "10-Q later amended (prevrpt=1)": c["10Q_prevrpt"],
        "pct_10Q_later_amended": round(100 * c["10Q_prevrpt"] / max(1, q), 2),
        "10-Q/A as pct of 10-Q": round(100 * c["10-Q/A"] / max(1, q), 2),
        "10-Q multi-registrant (nciks>1)": c["10Q_multiregistrant"],
        "10-Q not fully detail-tagged (detail=0)": c["10Q_detail0"],
    }
    print(zf, json.dumps(out[zf]))

json.dump(out, open("C1_fsds_amendments.json", "w"), indent=1)
print("WROTE C1_fsds_amendments.json")
