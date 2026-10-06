# Security policy

## Supported versions

Only the latest release on `main` receives fixes.

## Reporting a vulnerability

Please report security issues privately through GitHub:
**Security** tab → **Report a vulnerability**. Do not open a public issue.

You can expect an acknowledgement within a week. This is a single-maintainer project, so fixes
are made on a best-effort basis.

This library runs backtests on data you supply. The only code that makes network calls is the
yfinance loader in `src/backtest_framework/data/yfinance_source.py`, and nothing in the package
handles credentials.
