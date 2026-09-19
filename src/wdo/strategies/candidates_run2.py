"""Candidatos da RUN-0002 (Fase 1): arquitetura de saída adaptativa (ExitSpec, motor 1.1.0), janelas livres.

Cada classe documenta hipótese, origem e o que desafia do V0. Features só com barras fechadas (point-in-time).
Constante a priori K_RANGE: risco por trade = 25% do range do dia anterior (conhecido na abertura), o que dá ~10 pts
num dia típico, comparável ao stop do V0; é UMA alternativa registrada antes de rodar, não uma busca.
"""
from __future__ import annotations

from dataclasses import replace
from statistics import median
from datetime import time

from ..config import Config
from .base import BarOpen, ExitSpec, OrderIntent, SessionDecision, SessionOpen
from .candidates import V0NoChannel

K_RANGE = 0.25
EXIT_AT = time(17, 55)          # antes do fim do pregão regular (o dado tem barras até 18:25)


class OrbAdaptiveExit:
    """EXP-0009 (pai: EXP-0002 reaberto por MECANISMO NOVO). ORB de 5 min com saída adaptativa.

    Entrada como no EXP-0002 (corpo da 1ª barra, entrada a mercado na 2ª). Saída: stop = K × range do dia anterior,
    trailing com a mesma distância, sem alvo fixo, saída por horário 17:55. Graus de liberdade: 1 (K).
    """
    name = "exp0009_orb_adaptive_exit"

    def __init__(self, config: Config, k: float = K_RANGE):
        self.c, self.k, self.range_ = config, k, None

    def on_session_open(self, ctx: SessionOpen) -> SessionDecision:
        self.range_ = ctx.pdh - ctx.pdl
        return SessionDecision(label="ORB_ADAPT")

    def on_bar_open(self, bar: BarOpen) -> list[OrderIntent]:
        if bar.index_in_session == 1 and bar.prev_bar is not None and self.range_:
            body = bar.prev_bar.close - bar.prev_bar.open
            if body == 0:
                return []
            d = self.k * self.range_
            return [OrderIntent(1 if body > 0 else -1, "market", None, "ORB_ADAPT",
                                exit=ExitSpec(stop_points=d, trailing_points=d, exit_time=EXIT_AT))]
        return []

    def on_bar_close(self, bar, *, entered: bool) -> None:
        pass


class OrbFixedExit(OrbAdaptiveExit):
    """EXP-0010 (controle do EXP-0009): mesma entrada e mesma arquitetura (stop=trailing, sem alvo, horário 17:55),
    porém distância FIXA de 10 pts (a do stop do V0). Graus de liberdade: 0. Testa se a adaptação ao range vale."""
    name = "exp0010_orb_fixed_exit"

    def on_bar_open(self, bar: BarOpen) -> list[OrderIntent]:
        out = super().on_bar_open(bar)
        if not out:
            return out
        spec = ExitSpec(stop_points=10.0, trailing_points=10.0, exit_time=EXIT_AT)
        return [replace(i, exit=spec) for i in out]


class V0NoChannelScaledRR(V0NoChannel):
    """EXP-0016 (reserva; pai: EXP-0005). Fades do V0 (sem canal P3) com saída
    simétrica escalada pelo range: stop = alvo = K × range do dia anterior (R:R 1:1) no lugar de 10/6 fixos."""
    name = "exp0016_v0_nochannel_scaled_rr"

    def __init__(self, config: Config, k: float = K_RANGE):
        super().__init__(config)
        self.k, self.range_ = k, None

    def on_session_open(self, ctx: SessionOpen) -> SessionDecision:
        self.range_ = ctx.pdh - ctx.pdl
        return super().on_session_open(ctx)

    def on_bar_open(self, bar: BarOpen) -> list[OrderIntent]:
        intents = super().on_bar_open(bar)
        if not intents or not self.range_:
            return intents
        d = self.k * self.range_
        spec = ExitSpec(stop_points=d, target_points=d)
        return [replace(i, exit=spec) for i in intents]


class LateDayMomentumExit:
    """EXP-0014 (pai: EXP-0008, reaberto por MECANISMO NOVO: `exit_time`). Momentum intradiário (Gao et al. 2018).

    r1 = fechamento das 09:30 / fechamento da sessão anterior − 1. Às 17:30 entra a mercado na direção de r1 com
    stop = K × range do dia anterior e saída por horário às 17:55. Janela de sessão 09:00–18:00 (Config do candidato).
    """
    name = "exp0014_late_day_momentum_exit"

    def __init__(self, config: Config, k: float = K_RANGE):
        self.c, self.k = config, k
        self.last_close = self.prior_close = self.r1 = self.range_ = None

    def on_session_open(self, ctx: SessionOpen) -> SessionDecision:
        self.prior_close, self.r1, self.range_ = self.last_close, None, ctx.pdh - ctx.pdl
        return SessionDecision(label="LATE_MOM_EXIT")

    def on_bar_open(self, bar: BarOpen) -> list[OrderIntent]:
        t = bar.datetime
        if self.r1 and self.range_ and (t.hour, t.minute) == (17, 30):
            return [OrderIntent(1 if self.r1 > 0 else -1, "market", None, "LATE_MOM_EXIT",
                                exit=ExitSpec(stop_points=self.k * self.range_, exit_time=EXIT_AT))]
        return []

    def on_bar_close(self, bar, *, entered: bool) -> None:
        self.last_close = bar.close
        t = bar.datetime
        if (t.hour, t.minute) == (9, 25) and self.prior_close:
            self.r1 = (bar.close / self.prior_close - 1) or None


class OpeningRange30Breakout:
    """EXP-0013 (família nova). Rompimento do range de abertura de 30 min (09:00–09:30), stop estrutural.

    Range = máxima/mínima das barras 09:00–09:25. Depois das 09:30, se uma barra FECHADA fecha acima da máxima
    (abaixo da mínima), entra a mercado na abertura da barra seguinte; stop no lado oposto do range; sem alvo;
    saída por horário 17:55. Graus de liberdade: 0 (o range de 30 min é o construto).
    """
    name = "exp0013_or30_breakout"

    def __init__(self, config: Config):
        self.c, self.hi, self.lo = config, None, None

    def on_session_open(self, ctx: SessionOpen) -> SessionDecision:
        self.hi = self.lo = None
        return SessionDecision(label="OR30")

    def on_bar_close(self, bar, *, entered: bool) -> None:
        if (bar.datetime.hour, bar.datetime.minute) < (9, 30):
            self.hi = bar.high if self.hi is None else max(self.hi, bar.high)
            self.lo = bar.low if self.lo is None else min(self.lo, bar.low)

    def on_bar_open(self, bar: BarOpen) -> list[OrderIntent]:
        t, prev = bar.datetime, bar.prev_bar
        if (t.hour, t.minute) < (9, 30) or self.hi is None or prev is None:
            return []
        if prev.close > self.hi and bar.open - self.lo > 1.0:          # guarda: stop estrutural deve ficar do lado protetivo
            side, stop = 1, self.lo
        elif prev.close < self.lo and self.hi - bar.open > 1.0:
            side, stop = -1, self.hi
        else:
            return []
        return [OrderIntent(side, "market", None, "OR30_BREAK", exit=ExitSpec(stop_price=stop, exit_time=EXIT_AT))]


class OrbStructuralStop(OrbAdaptiveExit):
    """EXP-0011 (pai: EXP-0010). ORB de 5 min com a arquitetura da literatura: stop ESTRUTURAL no extremo oposto da 1ª
    barra, sem trailing, sem alvo, saída por horário 17:55 (Zarattini & Aziz 2023). Graus de liberdade: 0.
    Guarda: sem trade se a abertura da 2ª barra já estiver além do stop (gap), para não gerar stop inválido."""
    name = "exp0011_orb_structural_stop"

    def on_bar_open(self, bar: BarOpen) -> list[OrderIntent]:
        prev = bar.prev_bar
        if bar.index_in_session != 1 or prev is None:
            return []
        body = prev.close - prev.open
        if body == 0:
            return []
        if body > 0 and bar.open - prev.low > 1.0:
            return [OrderIntent(1, "market", None, "ORB_STRUCT", exit=ExitSpec(stop_price=prev.low, exit_time=EXIT_AT))]
        if body < 0 and prev.high - bar.open > 1.0:
            return [OrderIntent(-1, "market", None, "ORB_STRUCT", exit=ExitSpec(stop_price=prev.high, exit_time=EXIT_AT))]
        return []


class OrbStructuralVolGate(OrbStructuralStop):
    """EXP-0012 (pai: EXP-0011). Mesma arquitetura, só em regime de volatilidade alta (D7: range do dia anterior >
    mediana dos 20 pregões anteriores; sem 10 pregões de histórico não opera). ROTULADO data-informed: o padrão
    "dia de baixa volatilidade perde" apareceu nos EXP-0000/0009/0010/0011 (mesma amostra). Graus de liberdade: 0."""
    name = "exp0012_orb_structural_volgate"

    def __init__(self, config: Config):
        super().__init__(config)
        self.ranges = []

    def on_session_open(self, ctx: SessionOpen) -> SessionDecision:
        self.range_ = ctx.pdh - ctx.pdl
        self.ranges.append(self.range_)
        hist = self.ranges[-20:]
        if len(hist) < 10 or self.range_ <= median(hist):
            return SessionDecision(label="SKIP_LOWVOL", stand_down=True)
        return SessionDecision(label="ORB_STRUCT_VOL")


class V0NoChannelSymmetricRR(V0NoChannel):
    """EXP-0015 (pai: EXP-0005, fronteira; reaberto por MECANISMO NOVO). Fades do V0 (sem canal) com payoff SIMÉTRICO
    1:1 (stop = alvo = 10 pts) no lugar de stop 10 / alvo 6. Graus de liberdade: 0 (mesmo stop do V0, alvo = stop)."""
    name = "exp0015_v0_nochannel_symmetric_rr"

    def on_bar_open(self, bar: BarOpen) -> list[OrderIntent]:
        intents = super().on_bar_open(bar)
        spec = ExitSpec(stop_points=10.0, target_points=10.0)
        return [replace(i, exit=spec) for i in intents]


class GapAndGoFillStop:
    """EXP-0016 (família nova). Continuação do gap de abertura com invalidação estrutural no preenchimento do gap.

    Gap = abertura da sessão − fechamento da sessão anterior (17:55). Entra a mercado na 1ª barra na direção do gap;
    stop no fechamento anterior (o gap preenchido invalida a tese); sem alvo; saída por horário 17:55. Guarda: sem
    trade se |gap| < 2 pts (stop degenerado). Janela de sessão 09:00–18:00 (Config do candidato). Graus de liberdade: 0."""
    name = "exp0016_gap_and_go_fill_stop"

    def __init__(self, config: Config):
        self.c, self.last_close, self.prior_close = config, None, None

    def on_session_open(self, ctx: SessionOpen) -> SessionDecision:
        self.prior_close = self.last_close
        return SessionDecision(label="GAP_GO")

    def on_bar_open(self, bar: BarOpen) -> list[OrderIntent]:
        if bar.index_in_session != 0 or self.prior_close is None:
            return []
        gap = bar.open - self.prior_close
        if abs(gap) < 2.0:
            return []
        return [OrderIntent(1 if gap > 0 else -1, "market", None, "GAP_GO",
                            exit=ExitSpec(stop_price=self.prior_close, exit_time=EXIT_AT))]

    def on_bar_close(self, bar, *, entered: bool) -> None:
        self.last_close = bar.close
