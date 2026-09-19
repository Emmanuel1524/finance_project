"""Baseline V0: regras do EA Robo_Abertura_WDO_Genial v1.35 (`reference/mt5/*.mq5`).

Só decide (ver `base.py`); não conhece high/low/close da barra corrente, custos nem execução.
Mapeamento: `on_session_open` ↔ `IniciarSessao`; `on_bar_open` ↔ `ProcessarPrimeiraVela` /
`ProcessarVelaSeguinte`; ordens do Padrão 3 ↔ `ColocarOrdensCanal`.
"""
from __future__ import annotations

from typing import Any

from ..config import Config, round_tick
from .base import BarOpen, OrderIntent, SessionDecision, SessionOpen


class BaselineV0:
    name = "baseline_v0"

    def __init__(self, config: Config):
        self.c = config
        self.pattern = 0
        self.direction = 0
        self.wait = False
        self.reference: Any = None
        self.open_rsi = float("nan")
        self.pdh = self.pdl = self.sup = self.inf = 0.0
        self.ema_support = self.ema_resistance = 0.0

    # ------------------------------------------------------------------ sessão
    def on_session_open(self, ctx: SessionOpen) -> SessionDecision:
        c = self.c
        emas = list(ctx.emas)
        self.pdh, self.pdl = ctx.pdh, ctx.pdl
        self.sup = round_tick(ctx.pdh - c.channel_offset, c.tick_size)   # canal superior
        self.inf = round_tick(ctx.pdl + c.channel_offset, c.tick_size)   # canal inferior
        self.ema_support = max((x for x in emas if x <= ctx.open), default=0.0)
        self.ema_resistance = min((x for x in emas if x >= ctx.open), default=0.0)
        self.open_rsi = ctx.rsi
        self.pattern, self.direction, self.wait, self.reference = 0, 0, False, None

        # Posição herdada mantém seus SL/TP; não abre outra hoje.
        if ctx.position_carried:
            return SessionDecision(label="POSITION_CARRIED", stand_down=True)

        op = ctx.open
        orders: list[OrderIntent] = []
        if op > self.pdh:                       # acima do canal: Padrão 4, venda
            self.pattern, self.direction = 4, -1
            self.wait = ctx.rsi > c.rsi_sell_max
        elif op < self.pdl:                     # abaixo do canal: Padrão 4, compra
            self.pattern, self.direction = 4, 1
            self.wait = ctx.rsi < c.rsi_buy_min
        elif op >= self.sup:                    # dentro do canal superior: Padrão 3, venda
            self.pattern, self.direction = 3, -1
            orders = self._channel_orders(-1)
        elif op <= self.inf:                    # dentro do canal inferior: Padrão 3, compra
            self.pattern, self.direction = 3, 1
            orders = self._channel_orders(1)
        else:                                   # entre os canais: Padrão 1 (toque de média)
            self.pattern = 1
            self.direction = 1 if op > max(emas) else -1 if op < min(emas) else 0
        return SessionDecision(orders=orders, label=f"P{self.pattern}")

    def _channel_orders(self, side: int) -> list[OrderIntent]:
        c = self.c
        if side < 0:
            stop, limit = self.sup - c.breakout_points, self.pdh + c.breakout_points
        else:
            stop, limit = self.inf + c.breakout_points, self.pdl - c.breakout_points
        orders = []
        if c.channel_mode in (0, 1):
            orders.append(OrderIntent(side, "stop", round_tick(stop, c.tick_size), "P3_STOP", lifetime="session"))
        if c.channel_mode in (0, 2):
            orders.append(OrderIntent(side, "limit", round_tick(limit, c.tick_size), "P3_LIMIT", lifetime="session"))
        return orders

    # ------------------------------------------------------------------ barras
    def on_bar_open(self, bar: BarOpen) -> list[OrderIntent]:
        c = self.c
        if self.pattern == 1 and bar.index_in_session == 0:
            return self._p1_touch_orders(bar)
        if self.pattern == 1 and bar.index_in_session == 1:
            self.pattern, self.reference = 2, bar.prev_bar          # Padrão 2 contínuo
        if self.pattern == 2 and self.reference is not None:
            ref = self.reference
            # Fade da vela anterior: mínima = COMPRA, máxima = VENDA. Se as duas forem tocadas na
            # mesma barra a ordem é desconhecida; convenção do V0: compra primeiro (R3 em aberto).
            return [
                OrderIntent(1, "limit", ref.low, "P2_LOW", "P2_AMBIGUOUS_LOW_FIRST"),
                OrderIntent(-1, "limit", ref.high, "P2_HIGH", "P2_AMBIGUOUS_LOW_FIRST"),
            ]
        if self.pattern == 4:
            immediate = (
                (self.direction > 0 and c.rsi_buy_min <= self.open_rsi <= c.rsi_buy_max)
                or (self.direction < 0 and c.rsi_sell_min <= self.open_rsi <= c.rsi_sell_max)
            )
            crossed = (
                (self.direction > 0 and not self.wait and bar.rsi <= c.rsi_buy_max)
                or (self.direction < 0 and not self.wait and bar.rsi >= c.rsi_sell_min)
            )
            if immediate or crossed:            # decidido com IFR já conhecido: mercado na abertura
                return [OrderIntent(self.direction, "market", None, "P4_RSI")]
            if bar.index_in_session >= 1 and self.wait and bar.prev_bar is not None:
                ref, side = bar.prev_bar, self.direction
                if side > 0:                    # toque da mínima (fade) ou da máxima (rompimento)
                    return [OrderIntent(1, "limit", ref.low, "P4_WAIT_REFERENCE"),
                            OrderIntent(1, "stop", ref.high, "P4_WAIT_REFERENCE")]
                return [OrderIntent(-1, "stop", ref.low, "P4_WAIT_REFERENCE"),
                        OrderIntent(-1, "limit", ref.high, "P4_WAIT_REFERENCE")]
        return []

    def _p1_touch_orders(self, bar: BarOpen) -> list[OrderIntent]:
        """Padrão 1: toque da primeira média (zona = média ± tolerância) na 1ª barra."""
        c, orders = self.c, []
        sup, res = self.ema_support, self.ema_resistance
        if sup:
            orders.append(OrderIntent(1, "limit", round_tick(sup, c.tick_size) + c.ema_touch_tolerance, "P1_EMA", "P1_EMA_DOUBLE"))
        if res:
            orders.append(OrderIntent(-1, "limit", round_tick(res, c.tick_size) - c.ema_touch_tolerance, "P1_EMA", "P1_EMA_DOUBLE"))
        if len(orders) == 2 and abs(bar.open - res) < abs(bar.open - sup):
            orders.reverse()                    # se as duas forem tocadas, a média mais próxima da abertura vem primeiro
        return orders

    def on_bar_close(self, bar: Any, *, entered: bool) -> None:
        # Padrão 2: sem entrada, a barra que acabou de fechar vira a nova referência.
        if self.pattern == 2 and self.reference is not None and not entered:
            self.reference = bar
