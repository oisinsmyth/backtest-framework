"""What every bulk panel's DATE COLUMN is, declared once — D609.

`data/data_manifest.json` says a panel exists, how big it is and what it hashes to. It does
not say **which of its columns is the session**, and neither does anything else: of the 42
`.meta.json` sidecars beside the fixtures, exactly one carries a `columns` key and that one is
incomplete. So every reserved-slice guard in this repository names its own column inline —
`df[df["day"] < RESERVED_FROM]` at `scripts/run_d555_tsmom_replication.py:98`, and again in
eight more runners — and a panel whose date column is spelled differently gets whatever the
author remembered.

This module is that knowledge in one table, hand-declared from a read of all 126 manifest
panels' own headers on 2026-09-22 (`scripts/panel_catalogue_check.py --audit` re-reads them and
reports every disagreement).

THE FOUR WRONG CUTS, WHICH ARE THE REASON A TABLE BEATS A CONVENTION
--------------------------------------------------------------------
Several panels carry MORE THAN ONE date-shaped column, and cutting on the wrong one is silent:

  * `fut_micro_flow_5m.bucket_start` is `2025-09-10 20:00:00` on session `2025-09-11` — the
    prior EVENING, because the Globex session opens at 18:00 ET. A cut on `bucket_start` keeps
    the first reserved session's overnight leg.
  * `fut_btc_1m.ts_utc` is the same shape (`2017-12-17T23:00` on day `2017-12-18`).
  * `fut_es_options_eod.expiry_date` is in the FUTURE of its `session`, so a cut on it drops
    rows a study is entitled to and keeps none it is not — wrong in the other direction, and
    just as invisible.
  * `prev_day` on the eight session panels is one session EARLIER than `day`, so a cut on it
    lets exactly one reserved session through.

And a family of KNOWN-AT columns — `published_at_et`, `published_et`, `oi_pub_et`,
`release_date_nominal`, `ref_session` — which are facts about when a number was published, not
about which session it belongs to. They are listed in `wrong_cuts` so `load_panel` refuses to
be pointed at them, rather than being left out and therefore available.

ONE PANEL DOES NOT CARRY AN ISO DATE, AND IT IS TWO PANELS STACKED
------------------------------------------------------------------
`hkm_factors.csv.gz` keys on `period`. `validation.frozen.filter_before` raises on it
(`frozen.py:758-760` refuses anything that is not `YYYY-MM-DD`), which is correct and
unhelpful: the panel is then simply unguarded. The period formats convert the CUT into the
panel's units instead, so the comparison is exact and a cut the format cannot express raises.

**It was declared `yyyymm` on the strength of its first row, `197001`, and the loader's own
fixed-width check caught that within a minute of first running.** The file holds 664 MONTHLY
rows keyed `YYYYMM` and 220 QUARTERLY rows keyed `YYYYQ` — `19701` is 1970 Q1, five characters
— told apart by the `freq` column. Against a `202401` cut the mixed-width lexical comparison
gives the right answer on every row in this file, and that is a coincidence of where the digits
fall rather than a property. It is declared `year_prefix`: the comparison key is the leading
four digits, the cut must be 1 January, and the two frequencies are compared on the one field
they share.

`yyyy_mm` is the treatment for `period = 2000-01`, which is
`data/fixtures/oecd_ir3tib_monthly.csv`'s shape. **That file is a plain `.csv` and is therefore
NOT a manifest panel** (`build_data_manifest.py:57` selects by bulk suffix), so it has no row
here; the format is supported and exercised on a synthetic panel in `tests/unit/test_panels.py`.

NINETEEN PANELS DECLARE NO DATE COLUMN, AND THEY ARE REFUSED RATHER THAN WAVED THROUGH
---------------------------------------------------------------------------------------
Sixteen `.npz` arrays (`d358_series_*` ×12, `d376_series`, `d377_ensemble`, `d382_scores`,
`d291_null_surface`), two aggregate tables (`d506_cells`, `d508_quintiles`) and one summary
(`D2_sas_vs_py_summ_stats.parquet`) have no session column. `date_col=None` is the declaration
that a reserved-slice cut **cannot** be applied, and `load_panel` raises on them. A loader that
returned them unfiltered would be a chokepoint with a hole in it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Mapping

__all__ = [
    "DateFormat",
    "Reader",
    "PanelSpec",
    "CatalogueError",
    "SPECS",
    "names",
    "spec_for",
    "spec_for_path",
    "DAY_FORMATS",
    "PERIOD_FORMATS",
]

DateFormat = Literal["iso_day", "iso_ts", "date32", "yyyymm", "yyyy_mm", "year_prefix", "none"]
"""How the date column spells a date.

``iso_day``   ``2024-01-01``
``iso_ts``    ``2024-01-01T09:30:00`` or ``2024-01-01 09:30:00`` — the day is its first ten
              characters either way, which is what `frozen._day_strings` slices.
``date32``    an arrow ``date32[day]``, so pandas hands back `datetime.date`/`datetime64`
              rather than a string. `frozen._day_strings` REFUSES a datetime dtype rather than
              coercing it (a coerced `datetime64` stringifies to
              ``2024-01-01T00:00:00.000000000``, which sorts AFTER ``2024-01-01``), so the
              column is converted to ISO strings at the loader before the guard sees it.
``yyyymm``    ``197001``   — the cut is converted, not the column.
``yyyy_mm``   ``2000-01``  — likewise. No manifest panel uses it; see the module docstring.
``year_prefix`` the column stacks two frequencies and only its leading four digits are a
              shared field, so the finest expressible cut is a year. One panel, `hkm_factors`.
``none``      there is no date column. The panel cannot be cut and `load_panel` says so.
"""

Reader = Literal["csv", "parquet", "npz"]

DAY_FORMATS: frozenset[str] = frozenset({"iso_day", "iso_ts", "date32"})
"""The formats whose column is (or becomes) a `YYYY-MM-DD`-prefixed string."""

PERIOD_FORMATS: frozenset[str] = frozenset({"yyyymm", "yyyy_mm", "year_prefix"})
"""The formats where the CUT is converted into the panel's own units."""

_VALID_FORMATS = DAY_FORMATS | PERIOD_FORMATS | {"none"}
_VALID_READERS = frozenset({"csv", "parquet", "npz"})


class CatalogueError(Exception):
    """A spec is self-contradictory, or a name is not in the catalogue."""


@dataclass(frozen=True)
class PanelSpec:
    """One manifest panel's identity, date column and traps.

    `path` is repo-relative POSIX and is spelled EXACTLY as `data/data_manifest.json` spells
    it, because the loader looks the manifest entry up by that string to get the sha256.
    """

    name: str
    path: str
    date_col: str | None
    date_format: DateFormat
    reader: Reader
    wrong_cuts: tuple[str, ...] = ()
    dtype_hints: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name or "/" in self.name:
            raise CatalogueError(f"panel name must be a bare identifier, got {self.name!r}")
        if not self.path or "\\" in self.path:
            raise CatalogueError(f"{self.name}: path must be repo-relative POSIX, got {self.path!r}")
        if self.date_format not in _VALID_FORMATS:
            raise CatalogueError(f"{self.name}: unknown date_format {self.date_format!r}")
        if self.reader not in _VALID_READERS:
            raise CatalogueError(f"{self.name}: unknown reader {self.reader!r}")
        if (self.date_col is None) != (self.date_format == "none"):
            raise CatalogueError(
                f"{self.name}: date_col={self.date_col!r} and date_format="
                f"{self.date_format!r} disagree. A panel with no date column declares "
                '`None` and `"none"` together, and one with a date column declares neither.'
            )
        if self.date_col is not None and self.date_col in self.wrong_cuts:
            raise CatalogueError(
                f"{self.name}: {self.date_col!r} is declared BOTH as the date column and as a "
                "wrong cut. wrong_cuts names the columns that must never receive reserved_from; "
                "the one that must is date_col, and they cannot be the same column."
            )
        if len(set(self.wrong_cuts)) != len(self.wrong_cuts):
            raise CatalogueError(f"{self.name}: wrong_cuts repeats a column: {self.wrong_cuts}")

    def read_dtypes(self) -> dict[str, str]:
        """The `dtype=` mapping a csv read uses.

        The date column and every wrong cut are forced to `str` — not for tidiness. Two of
        them are NUMBERS if pandas is left to infer: `hkm_factors.period` reads as int64
        `197001`, and `d456_8k_events.cik` as int64 `1675149`, losing four leading zeros that
        are part of the identifier. `dtype_hints` is the per-panel override on top.
        """
        out: dict[str, str] = {}
        if self.date_col is not None:
            out[self.date_col] = "str"
        for col in self.wrong_cuts:
            out[col] = "str"
        out.update(self.dtype_hints)
        return out


_ROWS: tuple[PanelSpec, ...] = (
    PanelSpec("D2_US_factors_SAS", "data/D2_US_factors_SAS.parquet", "date", "date32", "parquet", ()),
    PanelSpec("D2_sas_vs_py_summ_stats", "data/D2_sas_vs_py_summ_stats.parquet", None, "none", "parquet", ()),
    PanelSpec("attention_sample", "data/fixtures/attention_sample.csv.gz", "observed_at_utc", "iso_ts", "csv", ("available_at_utc",)),
    PanelSpec("cftc_cot_raw", "data/fixtures/cftc_cot_raw.csv.gz", "report_date", "iso_day", "csv", ("release_date_nominal",)),
    PanelSpec("cme_session_calendar", "data/fixtures/cme_session_calendar.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("cohort3_intraday_15m_raw", "data/fixtures/cohort3_intraday_15m_raw.csv.gz", "timestamp", "iso_ts", "csv", ()),
    PanelSpec("cohort4_intraday_15m_raw", "data/fixtures/cohort4_intraday_15m_raw.csv.gz", "timestamp", "iso_ts", "csv", ()),
    PanelSpec("crypto_binance_15m_raw", "data/fixtures/crypto_binance_15m_raw.csv.gz", "timestamp", "iso_ts", "csv", ()),
    PanelSpec("crypto_book_2018_raw", "data/fixtures/crypto_book_2018_raw.csv.gz", "timestamp", "iso_ts", "csv", ()),
    PanelSpec("crypto_daily_2015_2025_raw", "data/fixtures/crypto_daily_2015_2025_raw.csv.gz", "timestamp", "iso_ts", "csv", ()),
    PanelSpec("crypto_intraday_15m_raw", "data/fixtures/crypto_intraday_15m_raw.csv.gz", "timestamp", "iso_ts", "csv", ()),
    PanelSpec("crypto_intraday_1h_raw", "data/fixtures/crypto_intraday_1h_raw.csv.gz", "timestamp", "iso_ts", "csv", ()),
    PanelSpec("crypto_intraday_30m_raw", "data/fixtures/crypto_intraday_30m_raw.csv.gz", "timestamp", "iso_ts", "csv", ()),
    PanelSpec("crypto_universe_2015_2025_raw", "data/fixtures/crypto_universe_2015_2025_raw.csv.gz", "timestamp", "iso_ts", "csv", ()),
    PanelSpec("d291_null_surface", "data/d291_null_surface.npz", None, "none", "npz", ()),
    PanelSpec("d358_series_hist_L_10", "data/d358_series_hist_L_10.npz", None, "none", "npz", ()),
    PanelSpec("d358_series_hist_L_10_inv", "data/d358_series_hist_L_10_inv.npz", None, "none", "npz", ()),
    PanelSpec("d358_series_hist_L_2", "data/d358_series_hist_L_2.npz", None, "none", "npz", ()),
    PanelSpec("d358_series_hist_L_2_inv", "data/d358_series_hist_L_2_inv.npz", None, "none", "npz", ()),
    PanelSpec("d358_series_hist_L_5", "data/d358_series_hist_L_5.npz", None, "none", "npz", ()),
    PanelSpec("d358_series_hist_L_5_inv", "data/d358_series_hist_L_5_inv.npz", None, "none", "npz", ()),
    PanelSpec("d358_series_rev_5_10", "data/d358_series_rev_5_10.npz", None, "none", "npz", ()),
    PanelSpec("d358_series_rev_5_10_inv", "data/d358_series_rev_5_10_inv.npz", None, "none", "npz", ()),
    PanelSpec("d358_series_rev_5_2", "data/d358_series_rev_5_2.npz", None, "none", "npz", ()),
    PanelSpec("d358_series_rev_5_2_inv", "data/d358_series_rev_5_2_inv.npz", None, "none", "npz", ()),
    PanelSpec("d358_series_rev_5_5", "data/d358_series_rev_5_5.npz", None, "none", "npz", ()),
    PanelSpec("d358_series_rev_5_5_inv", "data/d358_series_rev_5_5_inv.npz", None, "none", "npz", ()),
    PanelSpec("d361_trades_gap_up_fade", "data/d361_trades_gap_up_fade.csv.gz", "date_entry", "iso_day", "csv", ("date_g", "delist_date", "last_live_date")),
    PanelSpec("d365_trade_paths_95_80", "data/d365_trade_paths_95_80.csv.gz", "date", "iso_day", "csv", ()),
    PanelSpec("d376_series", "data/d376_series.npz", None, "none", "npz", ()),
    PanelSpec("d377_ensemble", "data/d377_ensemble.npz", None, "none", "npz", ()),
    PanelSpec("d382_scores", "data/d382_scores.npz", None, "none", "npz", ()),
    PanelSpec("d440_holds", "data/d440_holds.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("d443_issuance_panel", "data/d443_issuance_panel.csv.gz", "avail_date", "iso_day", "csv", ("fiscal_date",)),
    PanelSpec("d444_bs_instants", "data/d444_bs_instants.csv.gz", "filed", "iso_day", "csv", ("fiscal_date",)),
    PanelSpec("d444_issuance_panel", "data/d444_issuance_panel.csv.gz", "avail_date", "iso_day", "csv", ("fiscal_date",), {"cik": "str"}),
    PanelSpec("d449_es_holds", "data/d449_es_holds.csv.gz", "day", "iso_day", "csv", ("prev_day",)),
    PanelSpec("d454_insider_events", "data/d454_insider_events.csv.gz", "filing", "iso_day", "csv", ("trans_min", "trans_max"), {"cik": "str"}),
    PanelSpec("d454_insider_owner_rows", "data/d454_insider_owner_rows.csv.gz", "filing", "iso_day", "csv", ("trans",), {"RPTOWNERCIK": "str"}),
    PanelSpec("d456_8k_events", "data/d456_8k_events.csv.gz", "filing", "iso_day", "csv", ("report",), {"cik": "str"}),
    PanelSpec("d463_trades", "data/d463_trades.csv.gz", "day", "iso_day", "csv", ("prev_day",)),
    PanelSpec("d490_trades_dev_ES", "data/d490_trades_dev_ES.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("d490_trades_dev_NQ", "data/d490_trades_dev_NQ.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("d492_trades_dev_ES_A", "data/d492_trades_dev_ES_A.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("d492_trades_dev_ES_B", "data/d492_trades_dev_ES_B.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("d492_trades_dev_NQ_A", "data/d492_trades_dev_NQ_A.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("d492_trades_dev_NQ_B", "data/d492_trades_dev_NQ_B.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("d495_trades_ES_A", "data/d495_trades_ES_A.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("d495_trades_ES_B", "data/d495_trades_ES_B.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("d495_trades_NQ_A", "data/d495_trades_NQ_A.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("d495_trades_NQ_B", "data/d495_trades_NQ_B.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("d498_trades_ES_E1", "data/d498_trades_ES_E1.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("d498_trades_ES_E2", "data/d498_trades_ES_E2.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("d498_trades_ES_E3", "data/d498_trades_ES_E3.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("d498_trades_ES_K8", "data/d498_trades_ES_K8.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("d498_trades_NQ_E1", "data/d498_trades_NQ_E1.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("d498_trades_NQ_E2", "data/d498_trades_NQ_E2.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("d498_trades_NQ_E3", "data/d498_trades_NQ_E3.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("d498_trades_NQ_K8", "data/d498_trades_NQ_K8.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("d498_trades_forward_ES_K8", "data/d498_trades_forward_ES_K8.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("d498_trades_forward_NQ_K8", "data/d498_trades_forward_NQ_K8.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("d499_trades_6E", "data/d499_trades_6E.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("d499_trades_CL", "data/d499_trades_CL.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("d499_trades_ES", "data/d499_trades_ES.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("d499_trades_GC", "data/d499_trades_GC.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("d499_trades_NQ", "data/d499_trades_NQ.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("d499_trades_YM", "data/d499_trades_YM.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("d499_trades_ZB", "data/d499_trades_ZB.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("d499_trades_ZN", "data/d499_trades_ZN.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("d504_signal_and_returns", "data/d504_signal_and_returns.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("d506_cells", "data/d506_cells.csv.gz", None, "none", "csv", ()),
    PanelSpec("d508_quintiles", "data/d508_quintiles.csv.gz", None, "none", "csv", ()),
    PanelSpec("d526_curve_strip_CL_GC", "data/d526_curve_strip_CL_GC.csv.gz", "ref", "iso_day", "csv", ()),
    PanelSpec("es_c1_holds", "data/fixtures/es_c1_holds.csv.gz", "day", "iso_day", "csv", ("prev_day",)),
    PanelSpec("es_daily_marks", "data/fixtures/es_daily_marks.csv.gz", "day", "iso_day", "csv", ("prev_day",)),
    PanelSpec("es_front_1m_boundaries", "data/fixtures/es_front_1m_boundaries.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("es_hold_ladder", "data/fixtures/es_hold_ladder.csv.gz", "day", "iso_day", "csv", ("prev_day",)),
    PanelSpec("es_minute_bars", "data/fixtures/es_minute_bars.parquet", "day", "iso_day", "parquet", ()),
    PanelSpec("es_stop_grid", "data/fixtures/es_stop_grid.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("etf_intraday_15m_panel", "data/fixtures/etf_intraday_15m_panel.csv.gz", "timestamp", "iso_ts", "csv", ()),
    PanelSpec("etf_intraday_15m_raw", "data/fixtures/etf_intraday_15m_raw.csv.gz", "timestamp", "iso_ts", "csv", ()),
    PanelSpec("etf_wide_daily_raw", "data/fixtures/etf_wide_daily_raw.csv.gz", "timestamp", "iso_ts", "csv", ()),
    PanelSpec("fut_ES_rth_1m", "data/fixtures/fut_ES_rth_1m.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("fut_NQ_rth_1m", "data/fixtures/fut_NQ_rth_1m.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("fut_RTY_rth_1m", "data/fixtures/fut_RTY_rth_1m.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("fut_YM_rth_1m", "data/fixtures/fut_YM_rth_1m.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("fund_holdings_quarterly", "data/fixtures/fund_holdings_quarterly.csv.gz", "filed_date", "iso_day", "csv", ("period_end",)),
    PanelSpec("fund_nav_daily", "data/fixtures/fund_nav_daily.csv.gz", "date", "iso_day", "csv", ("fetched_at",)),
    PanelSpec("fund_panel_projected", "data/fixtures/fund_panel_projected.csv.gz", "date", "iso_day", "csv", ("anchor_filed_date", "anchor_period_end")),
    PanelSpec("fut_book_depth_1m", "data/fixtures/fut_book_depth_1m.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("fut_breadth_hourly", "data/fixtures/fut_breadth_hourly.csv.gz", "day", "iso_day", "csv", ("prev_day",)),
    PanelSpec("fut_btc_1m", "data/fixtures/fut_btc_1m.csv.gz", "day", "iso_day", "csv", ("ts_utc",)),
    PanelSpec("fut_cleared_volume_cm_daily", "data/fixtures/fut_cleared_volume_cm_daily.csv.gz", "session", "iso_day", "csv", ("published_et",)),
    PanelSpec("fut_crossing_tbbo", "data/fixtures/fut_crossing_tbbo.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("fut_curve_front_next", "data/fixtures/fut_curve_front_next.csv.gz", "ref", "iso_day", "csv", ()),
    PanelSpec("fut_day1m", "data/fixtures/fut_day1m.parquet", "day", "iso_day", "parquet", ()),
    PanelSpec("fut_day1m_mid", "data/fixtures/fut_day1m_mid.parquet", "day", "iso_day", "parquet", ()),
    PanelSpec("fut_day5m", "data/fixtures/fut_day5m.parquet", "day", "iso_day", "parquet", ()),
    PanelSpec("fut_day5m_mid", "data/fixtures/fut_day5m_mid.parquet", "day", "iso_day", "parquet", ()),
    PanelSpec("fut_es_0dte_signed_flow", "data/fixtures/fut_es_0dte_signed_flow.csv.gz", "session", "iso_day", "csv", ()),
    PanelSpec("fut_es_0dte_volume_cutoffs", "data/fixtures/fut_es_0dte_volume_cutoffs.csv.gz", "session", "iso_day", "csv", ()),
    PanelSpec("fut_es_options_eod", "data/fixtures/fut_es_options_eod.csv.gz", "session", "iso_day", "csv", ("expiry_date", "oi_pub_et")),
    PanelSpec("fut_index_rolls", "data/fixtures/fut_index_rolls.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("fut_index_sessions", "data/fixtures/fut_index_sessions.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("fut_micro_flow_5m", "data/fixtures/fut_micro_flow_5m.csv.gz", "session", "iso_day", "csv", ("bucket_start",)),
    PanelSpec("fut_micro_flow_rolls", "data/fixtures/fut_micro_flow_rolls.csv.gz", "session", "iso_day", "csv", ()),
    PanelSpec("fut_open_interest_daily", "data/fixtures/fut_open_interest_daily.csv.gz", "session", "iso_day", "csv", ("published_at_et", "ref_session")),
    PanelSpec("fut_sessions_hourly", "data/fixtures/fut_sessions_hourly.csv.gz", "day", "iso_day", "csv", ("prev_day",)),
    PanelSpec("fut_sessions_rolls", "data/fixtures/fut_sessions_rolls.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("fut_settle_strip", "data/fixtures/fut_settle_strip.csv.gz", "ref", "iso_day", "csv", ()),
    PanelSpec("fut_spread_1m", "data/fixtures/fut_spread_1m.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("fut_spread_all_1m", "data/fixtures/fut_spread_all_1m.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("fut_trade_counts", "data/fixtures/fut_trade_counts.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("gdelt_hourly_sample", "data/fixtures/gdelt_hourly_sample.csv.gz", "hour_utc", "iso_ts", "csv", ("available_at_utc",)),
    PanelSpec("hkm_factors", "data/fixtures/hkm_factors.csv.gz", "period", "year_prefix", "csv", ()),
    PanelSpec("holdout_intraday_15m_panel", "data/fixtures/holdout_intraday_15m_panel.csv.gz", "timestamp", "iso_ts", "csv", ()),
    PanelSpec("holdout_intraday_15m_raw", "data/fixtures/holdout_intraday_15m_raw.csv.gz", "timestamp", "iso_ts", "csv", ()),
    PanelSpec("index_extended_15m_raw", "data/fixtures/index_extended_15m_raw.csv.gz", "timestamp", "iso_ts", "csv", ()),
    PanelSpec("micro_minute_volume", "data/fixtures/micro_minute_volume.csv.gz", "day", "iso_day", "csv", ()),
    PanelSpec("robintrack_energy_funds", "data/fixtures/robintrack_energy_funds.csv.gz", "ts_utc", "iso_ts", "csv", ()),
    PanelSpec("single_name_intraday_15m_panel", "data/fixtures/single_name_intraday_15m_panel.csv.gz", "timestamp", "iso_ts", "csv", ()),
    PanelSpec("single_name_intraday_15m_raw", "data/fixtures/single_name_intraday_15m_raw.csv.gz", "timestamp", "iso_ts", "csv", ()),
    PanelSpec("universe_daily_2015_2024_raw", "data/fixtures/universe_daily_2015_2024_raw.csv.gz", "timestamp", "iso_ts", "csv", ()),
    PanelSpec("universe_daily_extended_raw", "data/fixtures/universe_daily_extended_raw.csv.gz", "timestamp", "iso_ts", "csv", ()),
    PanelSpec("universe_holdout_daily_raw", "data/fixtures/universe_holdout_daily_raw.csv.gz", "timestamp", "iso_ts", "csv", ()),
    PanelSpec("universe_holdout_extended_raw", "data/fixtures/universe_holdout_extended_raw.csv.gz", "timestamp", "iso_ts", "csv", ()),
    PanelSpec("universe_holdout_forward", "data/fixtures/universe_holdout_forward.csv.gz", "timestamp", "iso_ts", "csv", ()),
    PanelSpec("universe_parent57_forward", "data/fixtures/universe_parent57_forward.csv.gz", "timestamp", "iso_ts", "csv", ()),
    PanelSpec("universe_wide_w1_raw", "data/fixtures/universe_wide_w1_raw.csv.gz", "timestamp", "iso_ts", "csv", ()),
    PanelSpec("universe_wide_w5_raw", "data/fixtures/universe_wide_w5_raw.csv.gz", "timestamp", "iso_ts", "csv", ()),
    PanelSpec("us_shorts_daily_holdout", "data/fixtures/us_shorts_daily_holdout.csv.gz", "timestamp", "iso_ts", "csv", ()),
    PanelSpec("us_shorts_daily_holdout2", "data/fixtures/us_shorts_daily_holdout2.csv.gz", "timestamp", "iso_ts", "csv", ()),
    PanelSpec("us_shorts_daily_raw", "data/fixtures/us_shorts_daily_raw.csv.gz", "timestamp", "iso_ts", "csv", ()),
    PanelSpec("wide_extended_15m_raw", "data/fixtures/wide_extended_15m_raw.csv.gz", "timestamp", "iso_ts", "csv", ()),
)

SPECS: tuple[PanelSpec, ...] = _ROWS
"""Every manifest panel, one row each, sorted by file name as the manifest lists them."""

_BY_NAME: dict[str, PanelSpec] = {}
_BY_PATH: dict[str, PanelSpec] = {}
for _spec in _ROWS:
    if _spec.name in _BY_NAME:
        raise CatalogueError(f"duplicate panel name {_spec.name!r} in the catalogue")
    if _spec.path in _BY_PATH:
        raise CatalogueError(f"duplicate panel path {_spec.path!r} in the catalogue")
    _BY_NAME[_spec.name] = _spec
    _BY_PATH[_spec.path] = _spec
del _spec


def names() -> tuple[str, ...]:
    """Every catalogued panel name, in catalogue order."""
    return tuple(s.name for s in _ROWS)


def spec_for(name: str) -> PanelSpec:
    """The spec for a panel name. Raises rather than guessing at a near miss (D48)."""
    try:
        return _BY_NAME[name]
    except KeyError:
        near = [n for n in _BY_NAME if name.lower() in n.lower()][:5]
        raise CatalogueError(
            f"no catalogue entry for panel {name!r}"
            + (f"; did you mean one of {near}?" if near else "")
            + ". A panel this repository holds must be declared in panel_catalogue.py before "
            "load_panel can read it -- an undeclared panel has no declared date column, and a "
            "loader that guessed at one would be the defect this module exists to remove."
        ) from None


def spec_for_path(path: str) -> PanelSpec:
    """The spec for a repo-relative POSIX manifest path."""
    try:
        return _BY_PATH[path]
    except KeyError:
        raise CatalogueError(f"no catalogue entry for path {path!r}") from None
