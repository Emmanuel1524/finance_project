"""Candidatos da pesquisa (Fase 1). Cada classe documenta hipótese e pai; o V0 permanece intocado.

Todos respeitam o contrato point-in-time de `base.py`: só a abertura da barra corrente e barras fechadas.
"""
from __future__ import annotations

from dataclasses import replace
from statistics import median

from ..config import Config
from .base import BarOpen, OrderIntent, SessionDecision, SessionOpen
from .baseline_v0 import BaselineV0


class V0VolGate(BaselineV0):
    """EXP-0001 (pai: V0). Filtro de não operar em regime de baixa volatilidade.

    Hipótese: com stop/alvo fixos (10/6 pts) e ~1,2 pt de custo por trade, dias em que o range do dia anterior
    é pequeno oferecem pouca excursão para o alvo; operar só em regime de volatilidade alta (D7: range do dia
    anterior > mediana dos 20 pregões anteriores) evita trades cuja economia é estruturalmente ruim.
    Sem histórico suficiente (< 10 pregões) o regime é desconhecido: não opera (conservador).
    """
    name = "exp0001_v0_volgate"

    def __init__(self, config: Config, window: int = 20, min_history: int = 10):
        super().__init__(config)
        self.window, self.min_history, self.ranges = window, min_history, []

    def on_session_open(self, ctx: SessionOpen) -> SessionDecision:
        self.ranges.append(ctx.pdh - ctx.pdl)          # range do dia anterior: conhecido na abertura
        hist = self.ranges[-self.window:]
        if len(hist) < self.min_history or self.ranges[-1] <= median(hist):
            return SessionDecision(label="SKIP_LOWVOL", stand_down=True)
        return super().on_session_open(ctx)


class OpeningMomentum:
    """EXP-0002 (pai: V0; família nova). Continuação da direção da 1ª barra (opening range breakout de 5 min).

    Hipótese: o V0 é essencialmente de reversão (fade). A literatura de momentum intradiário e de ORB
    (Gao et al. 2018; Zarattini & Aziz 2023) sugere continuação da direção inicial. Regra: direção do corpo da
    1ª barra (close − open); entra a mercado na abertura da 2ª barra; sem trade se o corpo for zero.
    Saídas: as do V0 (Config), para isolar a mudança de arquitetura de entrada.
    """
    name = "exp0002_opening_momentum"

    def __init__(self, config: Config):
        self.c = config

    def on_session_open(self, ctx: SessionOpen) -> SessionDecision:
        return SessionDecision(label="ORB5")

    def on_bar_open(self, bar: BarOpen) -> list[OrderIntent]:
        if bar.index_in_session == 1 and bar.prev_bar is not None:
            body = bar.prev_bar.close - bar.prev_bar.open          # 1ª barra já fechada
            if body > 0:
                return [OrderIntent(1, "market", None, "ORB_LONG")]
            if body < 0:
                return [OrderIntent(-1, "market", None, "ORB_SHORT")]
        return []

    def on_bar_close(self, bar, *, entered: bool) -> None:
        pass


class V0TrendAligned(BaselineV0):
    """EXP-0003 (pai: V0). Só opera a favor da tendência diária.

    Hipótese: os fades contra-tendência do V0 são estruturalmente mais fracos. Tendência (candles D1 fechados):
    abertura acima das 3 EMAs D1 = alta (só compras); abaixo das 3 = baixa (só vendas); entre elas = sem
    filtro. Ordens do lado contrário à tendência são descartadas.
    """
    name = "exp0003_v0_trend_aligned"

    def __init__(self, config: Config):
        super().__init__(config)
        self.allowed = 0

    def on_session_open(self, ctx: SessionOpen) -> SessionDecision:
        d1 = ctx.emas[3:]
        self.allowed = 1 if ctx.open > max(d1) else -1 if ctx.open < min(d1) else 0
        decision = super().on_session_open(ctx)
        return replace(decision, orders=[o for o in decision.orders if self._ok(o.side)])

    def _ok(self, side: int) -> bool:
        return self.allowed == 0 or side == self.allowed

    def on_bar_open(self, bar: BarOpen) -> list[OrderIntent]:
        return [o for o in super().on_bar_open(bar) if self._ok(o.side)]


class V0NoChannel(BaselineV0):
    """EXP-0005 (pai: V0). Ablação da família de sinal Padrão 3 (ordens no canal PDH/PDL ± offset).

    Hipótese: as entradas de canal são zonas de stop-run (compra em fade no piso/rompimento no topo com liquidez de
    stops); com alvo 6 / stop 10 uma entrada sem edge acertaria ~62,5%, e o P3 acerta 33-50% (seleção adversa).
    Nos dias de abertura dentro do canal a estratégia não opera. Sem parâmetros novos.
    """
    name = "exp0005_v0_no_channel"

    def on_session_open(self, ctx: SessionOpen) -> SessionDecision:
        decision = super().on_session_open(ctx)
        if decision.label == "P3":
            return SessionDecision(label="SKIP_P3", stand_down=True)
        return decision


class V0NoChannelVolGate(V0VolGate):
    """EXP-0006 (pai: EXP-0005). Combina duas restrições estruturais já testadas isoladamente:
    sem família de canal (P3) e só em regime de volatilidade alta. Sem parâmetros novos."""
    name = "exp0006_v0_no_channel_volgate"

    def on_session_open(self, ctx: SessionOpen) -> SessionDecision:
        decision = super().on_session_open(ctx)
        if decision.label == "P3":
            return SessionDecision(label="SKIP_P3", stand_down=True)
        return decision


class OutsideRangeFade:
    """EXP-0007 (pai: V0; família de exploração). Fade de abertura fora do range do dia anterior, sem filtro de IFR.

    Hipótese: o único componente do V0 com excesso de acerto (P4: abertura acima da PDH/abaixo da PDL) pode
    dever-se à exaustão do movimento overnight, e não ao IFR. Regra: se a abertura da sessão está acima da PDH,
    vende a mercado na abertura da 1ª barra; abaixo da PDL, compra. Sem IFR, sem canal, sem médias.
    """
    name = "exp0007_outside_range_fade"

    def __init__(self, config: Config):
        self.c, self.side = config, 0

    def on_session_open(self, ctx: SessionOpen) -> SessionDecision:
        self.side = -1 if ctx.open > ctx.pdh else 1 if ctx.open < ctx.pdl else 0
        return SessionDecision(label="OUTSIDE_RANGE" if self.side else "INSIDE_RANGE", stand_down=self.side == 0)

    def on_bar_open(self, bar: BarOpen) -> list[OrderIntent]:
        if bar.index_in_session == 0 and self.side:
            return [OrderIntent(self.side, "market", None, "OUTSIDE_FADE")]
        return []

    def on_bar_close(self, bar, *, entered: bool) -> None:
        pass


class LateDayMomentum:
    """EXP-0008 (pai: V0; família nova). Momentum intradiário: retorno da 1ª meia hora prevê a última (Gao et al. 2018).

    Regra: r1 = fechamento das 09:30 / fechamento da sessão anterior - 1 (só conhecido às 09:30). Às 17:30 entra a
    mercado na direção de r1. Exige janela de sessão 09:00-18:00 (Config do candidato). Saídas do V0 (Config).
    """
    name = "exp0008_late_day_momentum"

    def __init__(self, config: Config, entry_hour: int = 17, entry_minute: int = 30):
        self.c, self.eh, self.em = config, entry_hour, entry_minute
        self.last_close = self.prior_close = self.r1 = None

    def on_session_open(self, ctx: SessionOpen) -> SessionDecision:
        self.prior_close, self.r1 = self.last_close, None
        return SessionDecision(label="LATE_DAY_MOM")

    def on_bar_open(self, bar: BarOpen) -> list[OrderIntent]:
        t = bar.datetime
        if self.r1 and (t.hour, t.minute) == (self.eh, self.em):
            return [OrderIntent(1 if self.r1 > 0 else -1, "market", None, "LATE_MOM")]
        return []

    def on_bar_close(self, bar, *, entered: bool) -> None:
        self.last_close = bar.close
        t = bar.datetime
        if (t.hour, t.minute) == (9, 25) and self.prior_close:      # a barra 09:25 fecha às 09:30
            self.r1 = (bar.close / self.prior_close - 1) or None
