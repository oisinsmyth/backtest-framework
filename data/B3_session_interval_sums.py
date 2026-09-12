rows = {
    # Bogousslavsky (2021) Internet Appendix Table IA.2: long/short leg alphas, bp,
    # $5 filter, >$100m mktcap, quote midpoints, VW deciles, 1986-2015. OV then 13 intervals.
    'GP aL':   (0.07, [-0.06, -0.03, 0.40, 0.24, 0.14, 0.22, 0.11, 0.19, 0.03, 0.06, 0.34, 0.26, -0.13]),
    'GP aS':   (0.32, [-0.19, -0.52, -0.31, -0.29, -0.24, -0.13, -0.14, -0.03, -0.16, 0.04, -0.16, 0.14, 1.10]),
    'NI aL':   (0.09, [0.20, 0.30, 0.30, 0.05, 0.31, -0.12, 0.30, -0.05, 0.16, 0.10, 0.28, -0.28, -0.87]),
    'NI aS':   (1.49, [-0.48, -0.95, -0.67, -0.27, -0.21, -0.14, -0.08, 0.03, -0.22, -0.16, -0.24, -0.04, 0.84]),
    'IV aL':   (-1.27, [0.40, 0.78, 0.23, 0.41, 0.06, 0.08, -0.01, 0.17, 0.02, 0.05, 0.16, 0.26, -0.14]),
    'IV aS':   (3.79, [-1.17, -1.62, -1.02, -0.88, -0.39, -0.34, -0.21, -0.41, -0.10, -0.12, -0.57, -0.70, 1.12]),
    # Table IA.6: long-short decile alphas, $10 filter, quote midpoints
    'BM ls a10':  (-2.69, [0.64, 0.40, -0.30, -0.04, 0.17, 0.13, 0.02, 0.45, -0.07, 0.09, 0.04, 0.18, 0.98]),
    'GP ls a10':  (-0.09, [0.08, 0.42, 0.66, 0.49, 0.35, 0.34, 0.19, 0.23, 0.17, -0.01, 0.50, 0.09, -1.21]),
    'NI ls a10':  (-1.31, [0.66, 1.18, 0.94, 0.26, 0.54, -0.05, 0.33, -0.07, 0.36, 0.21, 0.51, -0.28, -1.67]),
    'AC ls a10':  (0.58, [0.78, 0.43, 0.00, -0.42, -0.06, 0.26, 0.21, -0.00, -0.21, 0.06, -0.13, -0.29, -0.40]),
    'MOM ls a10': (6.36, [-0.17, -0.51, -0.01, 0.35, 0.22, -0.16, -0.23, -0.23, -0.03, 0.04, -0.14, -0.29, -0.57]),
    'SIZE ls a10': (-1.10, [-0.28, -0.23, -0.33, -0.23, 0.04, -0.00, -0.05, 0.09, -0.02, 0.09, 0.10, 0.39, 2.91]),
    # Table IA.7: long-short decile alphas, $5 filter, trade-based prices (9:30 bucket)
    'GP ls a5t':  (-1.69, [1.83, 0.50, 0.74, 0.62, 0.33, 0.37, 0.19, 0.12, 0.16, 0.01, 0.52, -0.02, -1.57]),
    'BM ls a5t':  (-2.10, [0.34, 0.18, -0.31, -0.36, 0.13, -0.01, 0.25, 0.51, -0.10, 0.15, 0.09, 0.45, 1.44]),
}

for k, (ov, intra) in rows.items():
    s = sum(intra)
    print('%-12s OV %7.2f  intraday %7.2f  total %7.2f  intraday/total %s'
          % (k, ov, s, ov + s, ('%.2f' % ((s) / (ov + s))) if abs(ov + s) > 1e-9 else 'n/a'))

print()
print('GP long-short from legs ($5, midquote): OV %.2f intraday %.2f'
      % (rows['GP aL'][0] - rows['GP aS'][0],
         sum(rows['GP aL'][1]) - sum(rows['GP aS'][1])))
print('NI long-short from legs ($5, midquote): OV %.2f intraday %.2f'
      % (rows['NI aL'][0] - rows['NI aS'][0],
         sum(rows['NI aL'][1]) - sum(rows['NI aS'][1])))
print('IV long-short from legs ($5, midquote): OV %.2f intraday %.2f'
      % (rows['IV aL'][0] - rows['IV aS'][0],
         sum(rows['IV aL'][1]) - sum(rows['IV aS'][1])))

print()
# programme cost arithmetic
rt = 67.6  # bp round trip, stated in lane context
gp_long_intraday_day = sum(rows['GP aL'][1])
print('GP long-leg intraday alpha %.2f bp/day; 21-day month = %.1f bp' % (gp_long_intraday_day, 21 * gp_long_intraday_day))
print('daily open/close round trip for 21 days = %.0f bp' % (21 * rt))
print('shortfall factor = %.1fx' % (21 * rt / (21 * gp_long_intraday_day)))
print('one round trip vs one day of intraday alpha = %.1fx' % (rt / gp_long_intraday_day))

# LPS ROE monthly
print()
print('LPS ROE: overnight -0.95%%/mo, intraday +1.42%%/mo, close-to-close %.2f%%' % (-0.95 + 1.42))
print('intraday as share of close-to-close = %.0f%%' % (100 * 1.42 / (1.42 - 0.95)))
print('LPS ROE intraday 142 bp/mo vs 21 daily round trips %.0f bp -> short by %.1fx' % (21 * rt, 21 * rt / 142))
