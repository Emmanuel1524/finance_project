"""Partições temporais dos dados e guarda de acesso (docs 06 §6).

Pesquisa: uso livre. Validação: só com `authorized=True` (consulta registrada, uso esparso).
Holdout: só com `authorized=True`, concedido pelo usuário; nunca durante a Fase 1.

`select` devolve as barras **até o fim da partição** (o histórico anterior serve de aquecimento
dos indicadores; barras posteriores ao fim da partição nunca saem daqui) e a janela operável.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import logging
import tomllib

import pandas as pd

from .config import Config
from .data import load_mt5_export
from .engine import BacktestResults, run_backtest
from .strategies import Strategy

log = logging.getLogger(__name__)
NAMES = ("research", "validation", "holdout")


@dataclass(frozen=True)
class Partition:
    name: str
    start: str      # data inicial (inclusive), AAAA-MM-DD
    end: str        # data final (inclusive), AAAA-MM-DD


@dataclass(frozen=True)
class Partitions:
    research: Partition
    validation: Partition
    holdout: Partition

    @classmethod
    def from_toml(cls, path: str | Path, section: str = "partitions") -> "Partitions":
        with open(path, "rb") as handle:
            values = tomllib.load(handle)[section]
        parts = {n: Partition(n, values[f"{n}_start"], values[f"{n}_end"]) for n in NAMES}
        unknown = set(values) - {f"{n}_{k}" for n in NAMES for k in ("start", "end")}
        if unknown:
            raise ValueError(f"Chaves desconhecidas em [{section}]: {sorted(unknown)}")
        obj = cls(**parts)
        obj.validate()
        return obj

    def get(self, name: str) -> Partition:
        if name not in NAMES:
            raise ValueError(f"Partição desconhecida: {name!r}; use {NAMES}")
        return getattr(self, name)

    def validate(self) -> None:
        ordered = [self.get(n) for n in NAMES]
        for p in ordered:
            if pd.Timestamp(p.start) > pd.Timestamp(p.end):
                raise ValueError(f"Partição {p.name}: início depois do fim")
        for a, b in zip(ordered, ordered[1:]):
            if pd.Timestamp(a.end) >= pd.Timestamp(b.start):
                raise ValueError(f"Partições {a.name} e {b.name} se sobrepõem ou estão fora de ordem")


def select(bars: pd.DataFrame, parts: Partitions, name: str, *, authorized: bool = False,
           timezone: str = "America/Sao_Paulo") -> tuple[pd.DataFrame, str, str]:
    """(barras até o fim da partição, início, fim). Recusa validação/holdout sem autorização."""
    part = parts.get(name)
    if name != "research" and not authorized:
        raise PermissionError(
            f"Acesso à partição '{name}' negado: exige autorização explícita (docs 06 §6). "
            "O holdout só é aberto uma vez, com a estratégia congelada e autorização do usuário."
        )
    if name != "research":
        log.warning("Acesso autorizado à partição '%s' (%s → %s): registrar a consulta.", name, part.start, part.end)
    finish = pd.Timestamp(part.end, tz=timezone) + pd.Timedelta(days=1) - pd.Timedelta(minutes=5)
    return bars[bars.datetime <= finish].copy(), part.start, part.end


def load_partition_bars(path: str | Path, parts: Partitions, name: str, *, authorized: bool = False,
                        timezone: str = "America/Sao_Paulo") -> tuple[pd.DataFrame, str, str]:
    """Lê o export do MT5 e devolve só as barras permitidas para a partição (futuro descartado na entrada)."""
    return select(load_mt5_export(path, timezone), parts, name, authorized=authorized, timezone=timezone)


def run_partition_backtest(bars: pd.DataFrame, parts: Partitions, name: str, config: Config,
                           strategy: Strategy | None = None, *, authorized: bool = False) -> BacktestResults:
    history, start, end = select(bars, parts, name, authorized=authorized, timezone=config.timezone)
    return run_backtest(history, start=start, end=end, config=config, strategy=strategy)
