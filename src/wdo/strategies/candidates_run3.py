"""Candidatos da RUN-0003 (Fase 1): mecanismos independentes sobre a arquitetura ORB estrutural (EXP-0011).

Todos herdam a entrada/saída de `OrbStructuralStop` (stop no extremo oposto da 1ª barra, sem trailing, sem alvo,
saída 17:55) e mudam UMA coisa, com hipótese registrada antes (ver experiments/RUN-0003_*/EXP-*/hypothesis.md).
Só informação de barras fechadas (point-in-time).
"""
from __future__ import annotations

from statistics import median

from ..config import Config
from .base import BarOpen, ExitSpec, OrderIntent, SessionDecision, SessionOpen
from .candidates_run2 import EXIT_AT, OrbStructuralStop


class OrbStructuralRelVolume(OrbStructuralStop):
    """EXP-0017. Só opera se o volume da 1ª barra > mediana dos volumes das 1ªs barras das 20 sessões anteriores
    (sem 10 sessões de histórico não opera). Literatura: "stocks in play" (Zarattini, Barbon & Aziz 2024)."""
    name = "exp0017_orb_structural_relvolume"

    def __init__(self, config: Config, window: int = 20, min_history: int = 10):
        super().__init__(config)
        self.window, self.min_history = window, min_history
        self.first_vols: list[float] = []
        self.hist: list[float] = []
        self.today_vol = None

    def on_session_open(self, ctx: SessionOpen) -> SessionDecision:
        self.hist, self.today_vol = [], None
        return super().on_session_open(ctx)

    def on_bar_close(self, bar, *, entered: bool) -> None:
        if (bar.datetime.hour, bar.datetime.minute) == (9, 0):        # 1ª barra da sessão, já fechada
            self.hist = self.first_vols[-self.window:]
            self.today_vol = bar.volume
            self.first_vols.append(bar.volume)

    def on_bar_open(self, bar: BarOpen) -> list[OrderIntent]:
        if bar.index_in_session != 1:
            return []
        if len(self.hist) < self.min_history or self.today_vol is None or self.today_vol <= median(self.hist):
            return []
        return super().on_bar_open(bar)


class OrbStructuralTrendAligned(OrbStructuralStop):
    """EXP-0018. Continuação só a favor da tendência D1: abertura acima das 3 EMAs D1 fechadas = só compras; abaixo
    das 3 = só vendas; entre elas = sem filtro."""
    name = "exp0018_orb_structural_trend_aligned"

    def __init__(self, config: Config):
        super().__init__(config)
        self.allowed = 0

    def on_session_open(self, ctx: SessionOpen) -> SessionDecision:
        d1 = ctx.emas[3:]
        self.allowed = 1 if ctx.open > max(d1) else -1 if ctx.open < min(d1) else 0
        return super().on_session_open(ctx)

    def on_bar_open(self, bar: BarOpen) -> list[OrderIntent]:
        return [o for o in super().on_bar_open(bar) if self.allowed == 0 or o.side == self.allowed]


class OrbStructuralSecondEntry(OrbStructuralStop):
    """EXP-0019. Depois de o 1º trade ser stopado, UMA re-entrada na mesma direção quando uma barra FECHADA fecha de novo
    além do extremo da 1ª barra (dentro da janela), com o mesmo stop estrutural e saída 17:55. Exige
    `max_trades_per_day = 2` (D9). A estratégia infere o stop-out com as mesmas regras do motor (barra fechada)."""
    name = "exp0019_orb_structural_second_entry"
    leakage_config = {"max_trades_per_day": 2}

    def __init__(self, config: Config):
        super().__init__(config)
        self._reset()

    def _reset(self):
        self.first_hi = self.first_lo = None
        self.n_entries = 0
        self.side = 0
        self.stop = None
        self.pending_side = 0
        self.pending_stop = None
        self.stopped_at = None
        self.reentry_signal = False

    def on_session_open(self, ctx: SessionOpen) -> SessionDecision:
        self._reset()
        return super().on_session_open(ctx)

    def on_bar_open(self, bar: BarOpen) -> list[OrderIntent]:
        prev = bar.prev_bar
        if bar.index_in_session == 1 and self.n_entries == 0:
            if prev is not None:
                self.first_hi, self.first_lo = prev.high, prev.low
            out = super().on_bar_open(bar)
            if out:
                self.pending_side, self.pending_stop = out[0].side, out[0].exit.stop_price
            return out
        if self.reentry_signal and self.n_entries == 1:
            self.reentry_signal = False
            if self.side > 0 and bar.open - self.first_lo > 1.0:
                return [OrderIntent(1, "market", None, "ORB_STRUCT_RE", exit=ExitSpec(stop_price=self.first_lo, exit_time=EXIT_AT))]
            if self.side < 0 and self.first_hi - bar.open > 1.0:
                return [OrderIntent(-1, "market", None, "ORB_STRUCT_RE", exit=ExitSpec(stop_price=self.first_hi, exit_time=EXIT_AT))]
        return []

    def on_bar_close(self, bar, *, entered: bool) -> None:
        if entered:
            self.n_entries += 1
            if self.n_entries == 1:
                self.side, self.stop = self.pending_side, self.pending_stop
        if self.n_entries != 1 or self.first_hi is None:
            return
        if self.stopped_at is None:
            hit = bar.low <= self.stop if self.side > 0 else bar.high >= self.stop     # mesma regra do motor (barra fechada)
            if hit:
                self.stopped_at = bar.datetime
            return
        if bar.datetime > self.stopped_at:
            if (self.side > 0 and bar.close > self.first_hi) or (self.side < 0 and bar.close < self.first_lo):
                self.reentry_signal = True


class OrbNyOpen:
    """EXP-0020. ORB de 5 min na abertura dos EUA (09:30 America/New_York): corpo da barra das 09:30 ET, entrada a mercado na
    abertura da barra seguinte, stop estrutural no extremo oposto, sem alvo, saída 17:55. O DST dos EUA é tratado por
    `tz_convert` (point-in-time). Exige janela de sessão que cubra 10:30–11:35 BRT (Config do candidato)."""
    name = "exp0020_orb_ny_open"
    leakage_config = {"end_hour": 12, "end_minute": 0}

    def __init__(self, config: Config):
        self.c = config
        self.bar_open = self.bar_close = self.bar_high = self.bar_low = None

    def on_session_open(self, ctx: SessionOpen) -> SessionDecision:
        self.bar_open = self.bar_close = self.bar_high = self.bar_low = None
        return SessionDecision(label="ORB_NY")

    @staticmethod
    def _et(dt):
        e = dt.tz_convert("America/New_York")
        return (e.hour, e.minute)

    def on_bar_close(self, bar, *, entered: bool) -> None:
        if self._et(bar.datetime) == (9, 30):                          # barra 09:30–09:35 ET, já fechada
            self.bar_open, self.bar_close, self.bar_high, self.bar_low = bar.open, bar.close, bar.high, bar.low

    def on_bar_open(self, bar: BarOpen) -> list[OrderIntent]:
        if self.bar_open is None or bar.prev_bar is None or self._et(bar.prev_bar.datetime) != (9, 30):
            return []
        body = self.bar_close - self.bar_open
        if body > 0 and bar.open - self.bar_low > 1.0:
            return [OrderIntent(1, "market", None, "ORB_NY", exit=ExitSpec(stop_price=self.bar_low, exit_time=EXIT_AT))]
        if body < 0 and self.bar_high - bar.open > 1.0:
            return [OrderIntent(-1, "market", None, "ORB_NY", exit=ExitSpec(stop_price=self.bar_high, exit_time=EXIT_AT))]
        return []


class OrbStructuralPdhTarget(OrbStructuralStop):
    """EXP-0021. Arquitetura do EXP-0011 com ALVO ESTRUTURAL: extremo do dia anterior na direção do trade (PDH para compra,
    PDL para venda) se estiver a >= 2 pts da abertura; caso contrário, sem alvo."""
    name = "exp0021_orb_structural_pdh_target"

    def __init__(self, config: Config):
        super().__init__(config)
        self.pdh = self.pdl = None

    def on_session_open(self, ctx: SessionOpen) -> SessionDecision:
        self.pdh, self.pdl = ctx.pdh, ctx.pdl
        return super().on_session_open(ctx)

    def on_bar_open(self, bar: BarOpen) -> list[OrderIntent]:
        out = super().on_bar_open(bar)
        if not out or self.pdh is None:
            return out
        o = out[0]
        target = None
        if o.side > 0 and self.pdh - bar.open >= 2.0:
            target = self.pdh
        elif o.side < 0 and bar.open - self.pdl >= 2.0:
            target = self.pdl
        spec = ExitSpec(stop_price=o.exit.stop_price, target_price=target, exit_time=EXIT_AT)
        return [OrderIntent(o.side, "market", None, "ORB_STRUCT_TGT", exit=spec)]
