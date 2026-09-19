"""Contrato entre estratégia e simulador.

A estratégia **decide**; o simulador **executa**. Contrato point-in-time:

- `on_session_open` recebe só o que é conhecido antes da 1ª barra da sessão;
- `on_bar_open` recebe a abertura da barra corrente, indicadores já defasados e a barra anterior
  **fechada**. High/low/close da barra corrente **não** estão disponíveis: uma decisão que dependa
  do range da barra deve ser expressa como ordem a nível (`stop`/`limit`), e é o simulador quem
  decide se e a que preço ela executa;
- `on_bar_close` recebe a barra completa depois de processada, para atualizar estado.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol, Sequence


@dataclass(frozen=True)
class OrderIntent:
    """Ordem desejada. `stop`: rompimento (compra sobe até o nível; venda cai até o nível).
    `limit`: fade (compra cai até o nível; venda sobe até o nível). `market`: a mercado na abertura."""
    side: int                                   # +1 compra, -1 venda
    kind: Literal["market", "stop", "limit"]
    price: float | None = None                  # None para `market`
    tag: str = ""
    conflict_tag: str | None = None             # tag usada se várias ordens forem tocadas na mesma barra
    lifetime: Literal["bar", "session"] = "bar"


@dataclass(frozen=True)
class SessionOpen:
    """Informação conhecida antes da 1ª barra da sessão."""
    date: Any
    open: float
    pdh: float
    pdl: float
    emas: tuple[float, ...]                     # 13/17/21 em H1 e depois em D1 (candles fechados)
    rsi: float
    position_carried: bool


@dataclass(frozen=True)
class SessionDecision:
    orders: Sequence[OrderIntent] = ()
    label: str = ""                             # aparece no evento SESSION
    stand_down: bool = False                    # True: não operar hoje


@dataclass(frozen=True)
class BarOpen:
    datetime: Any
    open: float
    rsi: float                                  # IFR até a barra anterior (point-in-time)
    index_in_session: int
    prev_bar: Any | None                        # barra anterior FECHADA (open/high/low/close)


class Strategy(Protocol):
    name: str

    def on_session_open(self, ctx: SessionOpen) -> SessionDecision: ...

    def on_bar_open(self, bar: BarOpen) -> list[OrderIntent]: ...

    def on_bar_close(self, bar: Any, *, entered: bool) -> None: ...
