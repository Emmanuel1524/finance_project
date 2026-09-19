"""Partições de dados e guarda de acesso (docs 06 §6) + cenário de configuração."""
from pathlib import Path

import pandas as pd
import pytest
from helpers import make_bars
from wdo import Config, Partitions, run_backtest, run_partition_backtest, select, validate_bars

CONFIG = Path(__file__).resolve().parent.parent / "configs" / "wdo_default.toml"


def year_bars():
    """~9 meses de barras sintéticas (12 barras/dia) cobrindo pesquisa, validação e holdout."""
    return validate_bars(make_bars(days=175, seed=5, bars_per_day=12, start="2026-01-02"))


def test_decided_boundaries_are_loaded_and_ordered():
    parts = Partitions.from_toml(CONFIG)
    assert (parts.research.start, parts.research.end) == ("2026-01-02", "2026-06-30")
    assert (parts.validation.start, parts.validation.end) == ("2026-07-01", "2026-07-31")
    assert (parts.holdout.start, parts.holdout.end) == ("2026-08-03", "2026-09-01")


def test_overlapping_partitions_are_rejected(tmp_path):
    bad = tmp_path / "bad.toml"
    bad.write_text('[partitions]\nresearch_start="2026-01-02"\nresearch_end="2026-07-15"\nvalidation_start="2026-07-01"\n'
                   'validation_end="2026-07-31"\nholdout_start="2026-08-03"\nholdout_end="2026-09-01"\n', encoding="utf-8")
    with pytest.raises(ValueError, match="sobrep"):
        Partitions.from_toml(bad)


def test_research_never_contains_later_bars_and_other_partitions_are_denied_by_default():
    parts, bars = Partitions.from_toml(CONFIG), year_bars()
    history, start, end = select(bars, parts, "research")
    assert history.datetime.max() <= pd.Timestamp("2026-06-30 23:55", tz="America/Sao_Paulo")
    for name in ("validation", "holdout"):
        with pytest.raises(PermissionError, match=name):
            select(bars, parts, name)
        with pytest.raises(PermissionError):
            run_partition_backtest(bars, parts, name, Config())


def test_authorized_validation_uses_earlier_history_only_as_warm_up():
    parts, bars, cfg = Partitions.from_toml(CONFIG), year_bars(), Config()
    result = run_partition_backtest(bars, parts, "validation", cfg, authorized=True)
    assert result.equity.datetime.min() >= pd.Timestamp("2026-07-01", tz=cfg.timezone)        # só opera na janela
    assert result.equity.datetime.max() <= pd.Timestamp("2026-07-31 23:55", tz=cfg.timezone)  # e nunca depois dela
    assert (result.events.event == "SESSION").sum() >= 15        # indicadores já aquecidos com o histórico de pesquisa


def test_research_result_does_not_depend_on_bars_after_the_partition():
    parts, bars, cfg = Partitions.from_toml(CONFIG), year_bars(), Config()
    via_guard = run_partition_backtest(bars, parts, "research", cfg)
    direct = run_backtest(bars[bars.datetime <= pd.Timestamp("2026-06-30 23:55", tz=cfg.timezone)], start="2026-01-02", end="2026-06-30", config=cfg)
    pd.testing.assert_frame_equal(via_guard.trades, direct.trades)
    pd.testing.assert_frame_equal(via_guard.equity, direct.equity)


def test_provisional_cost_scenario_and_daily_limit_are_in_the_default_config():
    cfg = Config.from_toml(CONFIG)
    assert (cfg.point_value_brl, cfg.slippage_points, cfg.commission_per_contract + cfg.fees_per_contract) == (10.0, 0.5, 1.0)
    assert cfg.max_trades_per_day == 1 and cfg.intrabar_policy == "adverse"
