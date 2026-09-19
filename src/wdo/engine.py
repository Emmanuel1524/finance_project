"""Motor de replay bar-by-bar (OHLC conservador e auditável). Executa qualquer `Strategy`.

O módulo não simula ticks ou book. Toda decisão intrabar com OHLC é registrada e usa a ordem
adversa para a estratégia quando a sequência é desconhecida. Regras de execução (docs 05 §3–§5):

- a estratégia só vê a abertura da barra corrente e barras anteriores fechadas; gatilhos que
  dependem do range da barra chegam como ordens a nível (`stop`/`limit`);
- ordem a nível tocada na barra executa no nível, ou na abertura se ela já passou do nível (gap);
  sempre com slippage contra e dentro do range OHLC;
- várias ordens do mesmo lado tocadas na mesma barra: vale o **pior** preço; de lados opostos:
  vale a prioridade declarada pela estratégia;
- a barra de entrada também é processada: stop pela janela inteira (premissa adversa) e alvo só
  a partir da barra seguinte;
- saídas com gap: stop executa no pior entre o stop e a abertura; alvo, no melhor.

`ENGINE_VERSION` identifica o simulador. Resultados só são comparáveis dentro da mesma versão;
qualquer mudança de comportamento exige nova versão e aprovação (docs 05 §10).
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .config import Config, round_tick
from .data import validate_bars
from .indicators import add_point_in_time_indicators
from .strategies import BarOpen, BaselineV0, OrderIntent, SessionOpen, Strategy

ENGINE_VERSION = "1.0.0"


@dataclass
class Position:
    trade_id: int
    side: int
    entry_datetime: pd.Timestamp
    entry_price: float
    quantity: float
    stop_initial: float
    target_initial: float
    mae: float = 0.0
    mfe: float = 0.0
    entry_reason: str = ""


@dataclass
class BacktestResults:
    trades: pd.DataFrame
    equity: pd.DataFrame
    events: pd.DataFrame
    config: Config
    engine_version: str = ENGINE_VERSION
    strategy_name: str = ""


class WDOReplayEngine:
    def __init__(self, config: Config, strategy: Strategy | None = None):
        self.c = config
        self.strategy = strategy if strategy is not None else BaselineV0(config)
        self.cash = config.initial_capital
        self.position: Position | None = None
        self.resting: list[OrderIntent] = []      # ordens de vida "session" (Padrão 3)
        self.events: list[dict] = []
        self.closed: list[dict] = []
        self.trade_id = 0
        self.trades_today = 0
        self.session_active = False
        self.prev_bar = None
        self.prior_daily = pd.DataFrame()

    # ------------------------------------------------------------------ utilidades
    def event(self, when, event, detail=""):
        self.events.append({"datetime": when, "event": event, "detail": detail})

    def fill(self, side: int, price: float) -> float:
        """Preço com slippage contra `side` (compra paga mais; venda recebe menos), no tick."""
        return round_tick(price + side * self.c.slippage_points, self.c.tick_size)

    # ------------------------------------------------------------------ entradas
    @staticmethod
    def level_fill(intent: OrderIntent, bar) -> float | None:
        """Preço de execução de uma ordem a nível na barra; None se não foi tocada.

        `stop` (rompimento): compra sobe até o nível, venda cai até o nível; se a barra já abre além
        do nível, executa na abertura (pior). `limit` (fade): compra cai até o nível, venda sobe até
        o nível; se a barra já abre além do nível, executa na abertura (gap real).
        """
        side, level = intent.side, intent.price
        if intent.kind == "stop":
            if side > 0:
                return max(bar.open, level) if bar.high >= level else None
            return min(bar.open, level) if bar.low <= level else None
        if side > 0:
            return min(bar.open, level) if bar.low <= level else None
        return max(bar.open, level) if bar.high >= level else None

    def select_entry(self, intents: list[OrderIntent], bar):
        """Escolhe (intent, preço_bruto, tag) executado na barra, ou None."""
        market = [i for i in intents if i.kind == "market"]
        if market:
            return market[0], bar.open, market[0].tag
        touched = [(i, price) for i in intents if (price := self.level_fill(i, bar)) is not None]
        if not touched:
            return None
        if len({i.side for i, _ in touched}) == 1:
            side = touched[0][0].side          # mesmo lado: pior preço para quem opera
            chosen = max(touched, key=lambda t: t[1]) if side > 0 else min(touched, key=lambda t: t[1])
        else:
            chosen = touched[0]                # lados opostos: prioridade da estratégia
        intent, price = chosen
        tag = intent.conflict_tag if len(touched) > 1 and intent.conflict_tag else intent.tag
        return intent, price, tag

    def open_position(self, when, side: int, raw_price: float, reason: str) -> Position:
        entry = self.fill(side, raw_price)
        self.trade_id += 1
        self.trades_today += 1
        self.position = Position(
            self.trade_id, side, when, entry, self.c.quantity,
            round_tick(entry - side * self.c.loss_points, self.c.tick_size),
            round_tick(entry + side * self.c.gain_points, self.c.tick_size),
            entry_reason=reason,
        )
        self.resting.clear()
        self.event(when, "ENTRY", reason)
        return self.position

    def manage_entry_bar(self, bar) -> None:
        """Barra de entrada: a ordem dos extremos é desconhecida, então vale a hipótese adversa.

        Stop avaliado com a janela inteira da barra; alvo só a partir da barra seguinte; MFE só
        conta o fechamento.
        """
        p = self.position
        adverse = (p.entry_price - bar.low) if p.side > 0 else (bar.high - p.entry_price)
        p.mae = max(p.mae, adverse, 0.0)
        p.mfe = max(p.mfe, (bar.close - p.entry_price) * p.side, 0.0)
        hit_stop = bar.low <= p.stop_initial if p.side > 0 else bar.high >= p.stop_initial
        if hit_stop:
            self.exit(bar.datetime, p.stop_initial, "STOP_LOSS_ENTRY_BAR")

    # ------------------------------------------------------------------ saídas
    def exit(self, when, price, reason):
        p = self.position
        exit_price = self.fill(-p.side, price)
        gross = (exit_price - p.entry_price) * p.side * p.quantity * self.c.point_value_brl
        costs = 2 * p.quantity * (self.c.commission_per_contract + self.c.fees_per_contract)
        self.cash += gross - costs
        self.closed.append({
            "trade_id": p.trade_id, "side": "LONG" if p.side > 0 else "SHORT",
            "entry_datetime": p.entry_datetime, "entry_price": p.entry_price, "entry_reason": p.entry_reason,
            "exit_datetime": when, "exit_price": exit_price, "quantity": p.quantity,
            "stop_price_inicial": p.stop_initial, "target_price_inicial": p.target_initial, "exit_reason": reason,
            "gross_pnl": gross, "costs": costs, "net_pnl": gross - costs, "duration": when - p.entry_datetime,
            "equity_after_trade": self.cash,
            "MAE": p.mae * self.c.point_value_brl * p.quantity, "MFE": p.mfe * self.c.point_value_brl * p.quantity,
        })
        self.event(when, "EXIT", reason)
        self.position = None

    def process_position(self, bar) -> None:
        """Stop/alvo de uma posição aberta em barra anterior. Gap: stop pior, alvo melhor."""
        p = self.position
        if p is None:
            return
        adverse = (p.entry_price - bar.low) if p.side > 0 else (bar.high - p.entry_price)
        favorable = (bar.high - p.entry_price) if p.side > 0 else (p.entry_price - bar.low)
        p.mae, p.mfe = max(p.mae, adverse), max(p.mfe, favorable)
        if p.side > 0:
            hit_stop, hit_target = bar.low <= p.stop_initial, bar.high >= p.target_initial
            stop_price, target_price = min(bar.open, p.stop_initial), max(bar.open, p.target_initial)
        else:
            hit_stop, hit_target = bar.high >= p.stop_initial, bar.low <= p.target_initial
            stop_price, target_price = max(bar.open, p.stop_initial), min(bar.open, p.target_initial)
        if hit_stop and hit_target:
            if self.c.intrabar_policy in ("adverse", "stop_first"):
                self.exit(bar.datetime, stop_price, "STOP_INTRABAR_AMBIGUOUS")
            else:
                self.exit(bar.datetime, target_price, "TARGET_INTRABAR_AMBIGUOUS")
        elif hit_stop:
            self.exit(bar.datetime, stop_price, "STOP_LOSS")
        elif hit_target:
            self.exit(bar.datetime, target_price, "TAKE_PROFIT")

    # ------------------------------------------------------------------ sessão
    def start_session(self, session: pd.DataFrame) -> bool:
        """Consulta a estratégia com o que é conhecido antes da 1ª barra. False = dia sem dados prontos."""
        first = session.iloc[0]
        prior = self.prior_daily.loc[: first.datetime.normalize() - pd.Timedelta(nanoseconds=1)]
        if prior.empty:
            return False
        emas = tuple(first[f"ema_{tf}_{n}"] for tf in ("h1", "d1") for n in (13, 17, 21))
        if any(pd.isna(value) for value in emas) or pd.isna(first.rsi):
            return False
        ctx = SessionOpen(first.datetime.date(), first.open, prior.iloc[-1].high, prior.iloc[-1].low,
                          emas, first.rsi, self.position is not None)
        decision = self.strategy.on_session_open(ctx)
        self.resting = [o for o in decision.orders]
        self.trades_today = self.c.max_trades_per_day if decision.stand_down else 0
        self.event(first.datetime, "SESSION", decision.label)
        return True

    def process_session_bar(self, bar, index: int) -> bool:
        """Decisão e execução de entrada na barra de sessão. Retorna True se entrou."""
        if self.position is not None or self.trades_today >= self.c.max_trades_per_day:
            return False
        view = BarOpen(bar.datetime, bar.open, bar.rsi, index, self.prev_bar)
        intents = list(self.resting) + list(self.strategy.on_bar_open(view))
        chosen = self.select_entry(intents, bar)
        if chosen is None:
            return False
        intent, raw_price, tag = chosen
        self.open_position(bar.datetime, intent.side, raw_price, tag)
        self.manage_entry_bar(bar)
        return True

    # ------------------------------------------------------------------ replay
    def run(self, bars: pd.DataFrame, trade_start=None, trade_end=None) -> BacktestResults:
        """Replay. `bars` pode incluir histórico anterior a `trade_start` (aquecimento dos indicadores);
        só se opera dentro de [trade_start, trade_end]. Nunca passe barras posteriores a `trade_end`."""
        data = add_point_in_time_indicators(validate_bars(bars, self.c.timezone), self.c)
        self.prior_daily = data.set_index("datetime").resample("1D").agg(high=("high", "max"), low=("low", "min")).dropna()
        trade_data = data
        if trade_start is not None:
            trade_data = trade_data[trade_data.datetime >= trade_start]
        if trade_end is not None:
            trade_data = trade_data[trade_data.datetime <= trade_end]

        equities = []
        minutes = trade_data.datetime.dt.hour * 60 + trade_data.datetime.dt.minute
        in_window = (minutes >= self.c.start_hour * 60 + self.c.start_minute) & (minutes < self.c.end_hour * 60 + self.c.end_minute)
        for _, day in trade_data.groupby(trade_data.datetime.dt.date, sort=True):
            session = day[in_window.loc[day.index]]
            self.session_active = (not session.empty) and self.start_session(session)
            session_index = {ts: i for i, ts in enumerate(session.datetime)}
            for bar in day.itertuples(index=False):
                self.process_position(bar)     # SL/TP seguem ativos fora da janela (ordens anexadas)
                index = session_index.get(bar.datetime)
                entered = False
                if index is not None and self.session_active:
                    entered = self.process_session_bar(bar, index)
                unrealized = 0.0
                if self.position is not None:
                    unrealized = (bar.close - self.position.entry_price) * self.position.side * self.position.quantity * self.c.point_value_brl
                equities.append({"datetime": bar.datetime, "equity": self.cash + unrealized, "cash": self.cash,
                                 "in_position": self.position is not None})
                if index is not None:
                    if self.session_active:
                        self.strategy.on_bar_close(bar, entered=entered)
                    self.prev_bar = bar
            self.resting.clear()
            self.session_active = False
        if self.position is not None and not trade_data.empty:
            self.exit(trade_data.iloc[-1].datetime, trade_data.iloc[-1].close, "END_OF_DATA")
        return BacktestResults(pd.DataFrame(self.closed), pd.DataFrame(equities), pd.DataFrame(self.events),
                               self.c, ENGINE_VERSION, self.strategy.name)


def run_backtest(bars: pd.DataFrame, start="2026-01-01", end="2026-09-01", initial_capital=10_000,
                 config: Config | None = None, strategy: Strategy | None = None) -> BacktestResults:
    """Replay no intervalo [start, end]. `bars` pode ter histórico anterior a `start` (aquecimento) mas
    as barras posteriores a `end` são descartadas aqui: o futuro nunca entra no cálculo."""
    config = config or Config(initial_capital=initial_capital)
    data = validate_bars(bars, config.timezone)
    begin = pd.Timestamp(start, tz=config.timezone)
    finish = pd.Timestamp(end, tz=config.timezone) + pd.Timedelta(days=1) - pd.Timedelta(minutes=5)
    history = data[data.datetime <= finish].copy()
    return WDOReplayEngine(config, strategy).run(history, trade_start=begin, trade_end=finish)
