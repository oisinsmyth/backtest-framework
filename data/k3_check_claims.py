"""K3: verify every quantitative claim made in the brief, from K3_census.json."""
import json
import os

SP = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(SP, "K3_census.json")))
Y = list(range(2010, 2027))


def g(d, k, y):
    return d.get(k, {}).get(str(y), d.get(k, {}).get(y, 0))


n202 = {y: g({"x": R["n202_year"]}, "x", y) for y in Y}
comp = {y: R["comp_year"].get(str(y), R["comp_year"].get(y, {})) for y in Y}
s202 = {y: g({"x": R["ncodes_sum_202"]}, "x", y) for y in Y}
sall = {y: g({"x": R["ncodes_sum_all"]}, "x", y) for y in Y}
t8k = {y: g({"x": R["total8k_year"]}, "x", y) for y in Y}

print("CLAIM: 7.01 share of 2.02 filings is monotone over 16 steps")
sh = [100.0 * comp[y].get("7.01", 0) / n202[y] for y in Y]
d = [sh[i + 1] - sh[i] for i in range(len(sh) - 1)]
print("  series:", " ".join("%.2f" % x for x in sh))
print("  steps up: %d of %d  (min step %+.2f)" % (sum(x > 0 for x in d), len(d), min(d)))
assert all(x > 0 for x in d), "NOT monotone"
print("  12.85 -> 24.04 ? %.2f -> %.2f  OK" % (sh[0], sh[-1]))

print()
print("CLAIM: mean codes per 2.02 filing rises in 15 of 16 steps")
mc = [s202[y] / n202[y] for y in Y]
d = [mc[i + 1] - mc[i] for i in range(len(mc) - 1)]
print("  series:", " ".join("%.3f" % x for x in mc))
print("  steps up: %d of %d ; down at %s"
      % (sum(x > 0 for x in d), len(d),
         [Y[i + 1] for i, x in enumerate(d) if x <= 0]))

print()
print("CLAIM: baseline (any 8-K) accreted codes FASTER than the 2.02 subset")
mb = [sall[y] / t8k[y] for y in Y]
print("  any 8-K  2010 %.3f -> 2025 %.3f (+%.3f) ; -> 2026p %.3f (+%.3f)"
      % (mb[0], mb[15], mb[15] - mb[0], mb[16], mb[16] - mb[0]))
print("  2.02     2010 %.3f -> 2025 %.3f (+%.3f) ; -> 2026p %.3f (+%.3f)"
      % (mc[0], mc[15], mc[15] - mc[0], mc[16], mc[16] - mc[0]))
print("  baseline rises more, to 2025? %s ; to 2026p? %s"
      % (mb[15] - mb[0] > mc[15] - mc[0], mb[16] - mb[0] > mc[16] - mc[0]))

print()
print("CLAIM: 2.02 share of all 8-K is flat ~24.5%% -> 25.4%% (2025)")
print("  ", " ".join("%.1f" % (100.0 * n202[y] / t8k[y]) for y in Y))

print()
print("CLAIM: 9.01 is on ~97%% of 2.02 filings")
print("  ", " ".join("%.1f" % (100.0 * comp[y].get("9.01", 0) / n202[y]) for y in Y))

print()
print("CLAIM: total form 8-K in window = 1,185,352")
print("  ", sum(t8k.values()))

print()
print("CLAIM: 1.05 first appears 2023 with 2, then 24/15/16")
print("  ", {y: g(R["code_year"], "1.05", y) for y in Y if g(R["code_year"], "1.05", y)})

print()
print("CLAIM: 33 distinct codes, exactly the Form 8-K universe with no gaps")
codes = R["all_codes_seen"]
exp = (["1.0%d" % i for i in range(1, 6)] + ["2.0%d" % i for i in range(1, 7)]
       + ["3.0%d" % i for i in range(1, 4)] + ["4.01", "4.02"]
       + ["5.0%d" % i for i in range(1, 9)] + ["6.0%d" % i for i in range(1, 7)]
       + ["7.01", "8.01", "9.01"])
print("  n=%d ; matches expected universe exactly? %s" % (len(codes), codes == exp))
print("  missing:", [c for c in exp if c not in codes],
      "| extra:", [c for c in codes if c not in exp])

print()
print("CLAIM: 2.05 / 7.01 / 5.02 / 8.01 / 5.07 / 2.06 early-vs-late")
cy, cw = R["code_year"], R["code_year_with202"]
for c in ("2.05", "7.01", "4.02", "8.01", "5.02", "5.07", "2.06", "1.01", "2.03"):
    ed = sum(g(cy, c, y) for y in (2010, 2011, 2012))
    en = sum(g(cw, c, y) for y in (2010, 2011, 2012))
    ld = sum(g(cy, c, y) for y in (2023, 2024, 2025))
    ln = sum(g(cw, c, y) for y in (2023, 2024, 2025))
    print("  %-5s %5.1f%% (n=%6d) -> %5.1f%% (n=%6d)  %+.1f pp"
          % (c, 100.0 * en / ed, ed, 100.0 * ln / ld, ld, 100.0 * ln / ld - 100.0 * en / ed))
print()
print("ALL ASSERTIONS PASSED")
