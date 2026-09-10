"""D2, post-bar check: my section 5 uses JKP's *SAS* build. JKP also ship a *Python*
build and a comparison file. If the two builds disagree on the characteristics I used,
my numbers are build-specific and must say so.

File: documentation/sas_to_python/data/sas_vs_py_summ_stats.parquet (402 rows x 21 cols)
"""
import pandas as pd, numpy as np

d = pd.read_parquet("D2_sas_vs_py_summ_stats.parquet")
used = ["gp_at", "gp_atl1", "op_at", "op_atl1", "ope_be", "ope_bel1", "cop_at",
        "ni_be", "niq_be", "niq_at", "niq_be_chg1", "niq_at_chg1", "ocf_at",
        "ocf_at_chg1", "saleq_su", "niq_su", "qmj_prof", "resff3_12_1",
        "bidaskhl_21d", "zero_trades_21d", "resff3_6_1"]
sub = d[d.characteristic.isin(used)].copy()
sub["mean_absdiff_pct"] = 100 * (sub.mean_py - sub.mean_sas).abs() / sub.mean_sas.abs()
sub["q2_absdiff_pct"] = 100 * (sub.q2_py - sub.q2_sas).abs() / sub.q2_sas.abs().replace(0, np.nan)
print(f"{'characteristic':<16}{'pearson':>9}{'spearman':>10}{'mean_sas':>12}"
      f"{'mean_py':>12}{'|d|mean%':>10}{'|d|med%':>9}")
for _, r in sub.sort_values("pearson corr").iterrows():
    print(f"{r.characteristic:<16}{r['pearson corr']:>9.3f}{r['spearman r-corr']:>10.4f}"
          f"{r.mean_sas:>12.5f}{r.mean_py:>12.5f}"
          f"{r.mean_absdiff_pct:>10.2f}{r.q2_absdiff_pct:>9.2f}")

print(f"\nacross ALL {len(d)} characteristics in the comparison file:")
for c, lab in [("pearson corr", "Pearson"), ("spearman r-corr", "Spearman rank")]:
    x = d[c].dropna()
    print(f"  {lab:<14} median {x.median():.4f}   "
          f"p05 {x.quantile(.05):.4f}   min {x.min():.4f}   "
          f"share < 0.90: {100*(x < .90).mean():.1f}%   share < 0.50: {100*(x<.5).mean():.1f}%")
print("\nworst 8 by Pearson (all characteristics):")
print(d.nsmallest(8, "pearson corr")[["characteristic", "pearson corr",
                                      "spearman r-corr"]].to_string(index=False))
