"""D4 driver: controls first, then the measurement."""
import json, math, os, sys, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from D4_measure import *   # noqa

OUT = {}
CTRL = {}

# ===================================================== 1. CONTROLS, RUN FIRST
# C0  self-test of k_half on inputs whose answer is known a priori.
CTRL["C0_k_half_selftest"] = {
    "constant_1pct_x132_expect_66": k_half([1.0] * 132)[0],
    "one_month_carries_all_expect_1": k_half([0.0] * 131 + [10.0])[0],
    "two_equal_months_expect_1": k_half([0.0] * 130 + [5.0, 5.0])[0],
    "negative_total_expect_None": k_half([-1.0] * 132)[0],
}
CTRL["C0_PASS"] = (CTRL["C0_k_half_selftest"]["constant_1pct_x132_expect_66"] == 66
                   and CTRL["C0_k_half_selftest"]["one_month_carries_all_expect_1"] == 1
                   and CTRL["C0_k_half_selftest"]["two_equal_months_expect_1"] == 1
                   and CTRL["C0_k_half_selftest"]["negative_total_expect_None"] is None)

# ----- load the blocks, each identified by its own header text
h_vw, cols_vw, op_vw, cen_vw = read_block("D4_Portfolios_Formed_on_OP_CSV.zip",
                                          "Average Value Weight Returns -- Monthly")
h_ew, cols_ew, op_ew, cen_ew = read_block("D4_Portfolios_Formed_on_OP_CSV.zip",
                                          "Average Equal Weighted Returns -- Monthly")
h_nf, cols_nf, op_nf, cen_nf = read_block("D4_Portfolios_Formed_on_OP_CSV.zip",
                                          "Number of Firms in Portfolios")
h_bm, cols_bm, bm_vw, cen_bm = read_block("D4_Portfolios_Formed_on_BE-ME_CSV.zip",
                                          "  Value Weight Returns -- Monthly")
h_bme, cols_bme, bm_ew, cen_bme = read_block("D4_Portfolios_Formed_on_BE-ME_CSV.zip",
                                             "  Equal Weight Returns -- Monthly")
h_6, cols_6, six_vw, cen_6 = read_block("D4_6_Portfolios_ME_OP_2x3_CSV.zip",
                                        "Average Value Weighted Returns -- Monthly")
ff5 = read_ff_factors("D4_F-F_Research_Data_5_Factors_2x3_CSV.zip",
                      ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"])
ff3 = read_ff_factors("D4_F-F_Research_Data_Factors_CSV.zip", ["Mkt-RF", "SMB", "HML", "RF"])

CTRL["C1_blocks_read"] = LOG

# C2  the MUST-RETURN-ZERO census: after stripping, no retained value may equal a sentinel,
#     and no monthly portfolio return may be below -95% or above +250%.
bad = 0
checked = 0
for src in (op_vw, op_ew, bm_vw, bm_ew, six_vw):
    for m, vals in src.items():
        for v in vals:
            if v is None:
                continue
            checked += 1
            if v in SENT or v < -95.0 or v > 250.0:
                bad += 1
CTRL["C2_must_be_zero"] = {"values_checked": checked, "sentinels_or_absurd_surviving": bad,
                           "PASS": bad == 0}

# C3  sentinel census by block, reported not assumed
CTRL["C3_sentinel_census"] = {
    "OP_vw_monthly": dict(cen_vw), "OP_ew_monthly": dict(cen_ew),
    "OP_num_firms": dict(cen_nf),
    "BE-ME_vw_monthly": dict(cen_bm), "BE-ME_ew_monthly": dict(cen_bme),
    "6_ME_OP_vw_monthly": dict(cen_6),
}

# C4  RECONSTRUCT RMW from the 6 ME x OP (2x3) portfolios using French's own definition
#     RMW = 1/2(SmallRobust + BigRobust) - 1/2(SmallWeak + BigWeak)
i = {c: j for j, c in enumerate(cols_6)}
need = ["SMALL LoOP", "ME1 OP2", "SMALL HiOP", "BIG LoOP", "ME2 OP2", "BIG HiOP"]
have = [c for c in need if c in i]
recon = {}
if len(have) == 6:
    for m, v in six_vw.items():
        a = v[i["SMALL HiOP"]]; b = v[i["BIG HiOP"]]
        c = v[i["SMALL LoOP"]]; d = v[i["BIG LoOP"]]
        if None in (a, b, c, d):
            continue
        recon[m] = 0.5 * (a + b) - 0.5 * (c + d)
common = sorted(set(recon) & set(m for m in ff5 if ff5[m]["RMW"] is not None))
diffs = [abs(recon[m] - ff5[m]["RMW"]) for m in common]
CTRL["C4_rmw_reconstruction"] = {
    "columns_found": have, "n_common_months": len(common),
    "max_abs_diff_pct_pts": max(diffs) if diffs else None,
    "mean_abs_diff_pct_pts": (sum(diffs) / len(diffs)) if diffs else None,
    "published_RMW_mean": sum(ff5[m]["RMW"] for m in common) / len(common) if common else None,
    "reconstructed_mean": sum(recon[m] for m in common) / len(common) if common else None,
    "PASS_if_max_diff_below_0.02": (max(diffs) < 0.02) if diffs else False,
}

# C5  NEGATIVE CONTROL on the concentration CLAIM itself: the statistic is computed on
#     series that nobody calls a concentrated anomaly -- the market excess return, on
#     windows chosen ONLY by their t-statistic, not by their concentration.
print(json.dumps({k: v for k, v in CTRL.items() if k != "C1_blocks_read"}, indent=1, default=str))
json.dump(CTRL, open(os.path.join(HERE, "D4_controls.json"), "w"), indent=1, default=str)
