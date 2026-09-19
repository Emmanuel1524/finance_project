"""Parâmetros do cenário de backtest (espelham os `input` do EA MQL5 v1.35 + premissas de custo)."""
from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path
from typing import Literal
import tomllib



@dataclass
class Config:
    symbol: str = "WDOFUT"
    quantity: float = 1.0
    gain_points: float = 6.0
    loss_points: float = 10.0
    channel_offset: float = 7.0
    breakout_points: float = 0.5
    channel_mode: int = 0  # 0 stop+fade, 1 stop, 2 fade
    magic: int = 55001
    deviation_points: float = 30.0
    ema_touch_tolerance: float = 1.0
    rsi_period: int = 7
    rsi_buy_min: float = 10.0
    rsi_buy_max: float = 16.0
    rsi_sell_min: float = 86.0
    rsi_sell_max: float = 90.0
    start_hour: int = 9
    start_minute: int = 0
    end_hour: int = 10
    end_minute: int = 30
    timezone: str = "America/Sao_Paulo"
    tick_size: float = 0.5
    point_value_brl: float = 10.0  # premissa configurável: R$ por ponto/contrato
    slippage_points: float = 0.0
    commission_per_contract: float = 0.0
    fees_per_contract: float = 0.0
    initial_capital: float = 10_000.0
    # Com OHLC não se conhece a ordem dos extremos. "adverse" é obrigatório padrão.
    intrabar_policy: Literal["adverse", "stop_first", "target_first"] = "adverse"

    @classmethod
    def from_toml(cls, path: str | Path, section: str = "backtest") -> "Config":
        """Carrega um cenário de `configs/*.toml`; chaves desconhecidas falham alto."""
        with open(path, "rb") as handle:
            values = tomllib.load(handle)[section]
        unknown = sorted(set(values).difference(f.name for f in fields(cls)))
        if unknown:
            raise ValueError(f"Chaves desconhecidas em {path}: {unknown}")
        return cls(**values)


def round_tick(price: float, tick_size: float = 0.5) -> float:
    """Equivalente a NormPreco: arredonda ao tick mais próximo."""
    return round(round(price / tick_size) * tick_size, 10)
