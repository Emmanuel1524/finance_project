"""Backtest/replay do robô de abertura do WDO (B3)."""
from .config import Config, round_tick
from .data import (
    REQUIRED_COLUMNS, build_continuous_contract, load_csv_or_parquet, load_http_ohlcv, load_mt5_export, validate_bars,
)
from .engine import BacktestResults, PendingOrder, Position, WDOReplayEngine, run_backtest
from .indicators import add_point_in_time_indicators, rsi_wilder
from .metrics import metrics
from .reporting import plot_results, print_backtest_report

__all__ = [
    "Config", "round_tick", "REQUIRED_COLUMNS", "validate_bars", "load_csv_or_parquet", "load_mt5_export",
    "load_http_ohlcv", "build_continuous_contract", "rsi_wilder", "add_point_in_time_indicators",
    "PendingOrder", "Position", "BacktestResults", "WDOReplayEngine", "run_backtest", "metrics",
    "print_backtest_report", "plot_results",
]
