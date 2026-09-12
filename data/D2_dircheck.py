"""D2: is JKP's `ret` already signed by `direction`? If not, two of my six control
factors may mismatch for a trivial reason. Checked rather than assumed."""
import pandas as pd, numpy as np

d = pd.read_parquet("D2_US_factors_SAS.parquet")
d["date"] = pd.to_datetime(d["date"])
PUB = {"niq_su": 0.19, "saleq_su": 0.05, "resff3_12_1": 0.28, "qmj_prof": 0.22,
       "bidaskhl_21d": -0.09, "zero_trades_21d": 0.09}
print(f"{'factor':<17}{'direction':>12}{'IR_asis':>9}{'published':>11}")
for k, v in PUB.items():
    s = d[d.name == k]
    ir = s.ret.mean() / s.ret.std(ddof=1)
    print(f"{k:<17}{str(sorted(set(s.direction))):>12}{ir:>9.3f}{v:>11.2f}")

print("\nsanity -- if `ret` is ALREADY direction-signed these are positive:")
for k in ["ret_12_1", "market_equity", "be_me", "gp_at", "qmj", "age"]:
    s = d[d.name == k]
    print(f"  {k:<15} dir={str(sorted(set(s.direction))):<6} "
          f"mean%/mo={100*s.ret.mean():+.3f}  "
          f"IR_ann={np.sqrt(12)*s.ret.mean()/s.ret.std(ddof=1):+.2f}")

print("\nhow many of the 153 have a NEGATIVE full-sample mean?")
g = d.groupby("name").ret.mean()
print(f"  {int((g < 0).sum())} of {len(g)}")
print("  most negative:", g.nsmallest(6).round(5).to_dict())
