"""K3 reduce: de-duplicate 8-K submissions by accession and build the census.

Pass 1  census of SUBMISSIONS (dedupe on accession number).
Pass 2  same-issuer-same-DAY absorption (dedupe on (cik, accession), because a
        co-registrant filing genuinely belongs to each registrant).
"""
import collections
import glob
import json
import os

SP = os.path.dirname(os.path.abspath(__file__))
Y0, Y1 = 2010, 2026

# Negative controls: item codes that do not exist in Form 8-K.
IMPOSSIBLE = ["9.99", "2.99", "1.99", "0.00", "10.01", "3.99", "7.99", "4.99",
              "2.07", "5.10", "6.07"]


def files():
    fs = sorted(glob.glob(os.path.join(SP, "K3_rows_*.tsv")))
    assert fs, "no worker output found"
    return fs


def stream():
    for fp in files():
        with open(fp, encoding="utf-8") as fh:
            for line in fh:
                p = line.rstrip("\n").split("\t")
                if len(p) != 5:
                    continue
                yield p  # ai, fd, form, items, cik


def codes_of(items):
    return sorted(set(c.strip() for c in items.split(",") if c.strip()))


def main():
    # ---------------- pass 1: census on unique submissions ----------------
    seen = set()
    dup = 0
    oow = 0
    form_year = collections.defaultdict(collections.Counter)
    code_year = collections.defaultdict(collections.Counter)
    code_year_with202 = collections.defaultdict(collections.Counter)
    comp_year = collections.defaultdict(collections.Counter)
    n202_year = collections.Counter()
    ncodes_sum_202 = collections.Counter()
    ncodes_sum_all = collections.Counter()
    ncodes_hist_202 = collections.defaultdict(collections.Counter)
    empty_year = collections.Counter()
    total8k_year = collections.Counter()
    maxcodes = (0, None)
    examples = {}   # code -> a sample accession co-filed with 2.02 (for hand-check)
    examples_any = {}  # code -> any sample accession carrying that code

    for ai, fd, form, items, cik in stream():
        k = int(ai)
        if k in seen:
            dup += 1
            continue
        seen.add(k)
        yr = int(fd[:4])
        form_year[form][yr] += 1
        if not (Y0 <= yr <= Y1):
            oow += 1
            continue
        if form != "8-K":
            continue
        total8k_year[yr] += 1
        cs = codes_of(items)
        if not cs:
            empty_year[yr] += 1
            continue
        ncodes_sum_all[yr] += len(cs)
        if len(cs) > maxcodes[0]:
            maxcodes = (len(cs), (ai, fd, items, cik))
        has202 = "2.02" in cs
        for c in cs:
            code_year[c][yr] += 1
            if c not in examples_any:
                examples_any[c] = (ai, fd, items, cik)
            if has202:
                code_year_with202[c][yr] += 1
                if c not in examples:
                    examples[c] = (ai, fd, items, cik)
        if has202:
            n202_year[yr] += 1
            ncodes_sum_202[yr] += len(cs)
            ncodes_hist_202[yr][len(cs)] += 1
            for c in cs:
                if c != "2.02":
                    comp_year[yr][c] += 1
    del seen

    # ---------------- pass 2: same-issuer-same-day ----------------
    pair = set()
    day202 = set()
    for ai, fd, form, items, cik in stream():
        if form != "8-K":
            continue
        yr = int(fd[:4])
        if not (Y0 <= yr <= Y1):
            continue
        key = int(ai) * 10000000000 + int(cik)
        if key in pair:
            continue
        pair.add(key)
        if "2.02" in codes_of(items):
            day202.add(int(cik) * 100000000 + int(fd.replace("-", "")))

    # code -> year -> count of (cik,accession) records WITHOUT 2.02 in-submission
    #                 but where that cik filed a 2.02 8-K the SAME DAY
    sameday = collections.defaultdict(collections.Counter)
    nonco = collections.defaultdict(collections.Counter)  # denominator
    for ai, fd, form, items, cik in stream():
        if form != "8-K":
            continue
        yr = int(fd[:4])
        if not (Y0 <= yr <= Y1):
            continue
        key = int(ai) * 10000000000 + int(cik)
        if key not in pair:
            continue
        pair.discard(key)
        cs = codes_of(items)
        if not cs or "2.02" in cs:
            continue
        sd = (int(cik) * 100000000 + int(fd.replace("-", ""))) in day202
        for c in cs:
            nonco[c][yr] += 1
            if sd:
                sameday[c][yr] += 1

    res = dict(
        n_unique_submissions=len(day202) and None,  # placeholder, set below
        n_duplicate_records_dropped=dup,
        n_out_of_window=oow,
        form_year={f: dict(c) for f, c in form_year.items()},
        total8k_year=dict(total8k_year),
        empty_items_year=dict(empty_year),
        code_year={c: dict(v) for c, v in code_year.items()},
        code_year_with202={c: dict(v) for c, v in code_year_with202.items()},
        comp_year={y: dict(v) for y, v in comp_year.items()},
        n202_year=dict(n202_year),
        ncodes_sum_202=dict(ncodes_sum_202),
        ncodes_sum_all=dict(ncodes_sum_all),
        ncodes_hist_202={y: dict(v) for y, v in ncodes_hist_202.items()},
        max_codes_submission=maxcodes,
        impossible_codes_probed=IMPOSSIBLE,
        impossible_found={c: dict(code_year.get(c, {})) for c in IMPOSSIBLE},
        all_codes_seen=sorted(code_year.keys()),
        sameday_no202={c: dict(v) for c, v in sameday.items()},
        nonco_denom={c: dict(v) for c, v in nonco.items()},
        examples_cofiled_with_202=examples,
        examples_any=examples_any,
    )
    res["n_unique_submissions"] = sum(sum(v.values()) for v in form_year.values())
    with open(os.path.join(SP, "K3_census.json"), "w") as fh:
        json.dump(res, fh, indent=1, default=str)

    print("unique 8-K-family submissions (all years):", res["n_unique_submissions"])
    print("duplicate records dropped (co-registrants):", dup)
    print("out of 2010-2026 window:", oow)
    print("form 8-K in window:", sum(total8k_year.values()))
    print("distinct item codes seen:", len(res["all_codes_seen"]))
    print(res["all_codes_seen"])
    print()
    print("=== NEGATIVE CONTROL (impossible codes) ===")
    for c in IMPOSSIBLE:
        print("  %-6s -> %s" % (c, res["impossible_found"][c] or "ZERO in every year"))
    print()
    print("max codes on one submission:", maxcodes)


if __name__ == "__main__":
    main()
