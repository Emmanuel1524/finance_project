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
- saídas com gap: stop executa no pior entre o stop e a abertura; alvo, no melhor;
- (1.1.0) a estratégia pode anexar uma `ExitSpec` a cada entrada (stop por pontos ou nível, alvo opcional,
  trailing, saída por horário) com a MESMA semântica conservadora; sem `ExitSpec`, vale o `Config` (V0).

`ENGINE_VERSION` identifica o simulador. Resultados só são comparáveis dentro da mesma versão;
qualquer mudança de comportamento exige nova versão e aprovação (docs 05 §10).
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .config import Config, round_tick
from .data import validate_bars
from .indicators import add_point_in_time_indicators
from .strategies import BarOpen, BaselineV0, ExitSpec, OrderIntent, SessionOpen, Strategy

ENGINE_VERSION = "1.1.0"


@dataclass
class Position:
    trade_id: int
    side: int
    entry_datetime: pd.Timestamp
    entry_price: float
    quantity: float
    stop_initial: float
    target_initial: float | None
    mae: float = 0.0
    mfe: float = 0.0
    entry_reason: str = ""
    stop_current: float | None = None            # stop vigente (o trailing só o aperta)
    trail_points: float | None = None
    exit_deadline: pd.Timestamp | None = None
    best_price: float | None = None              # melhor preço já visto em barras fechadas

    def __post_init__(self):
        if self.stop_current is None:
            self.stop_current = self.stop_initial
        if self.best_price is None:
            self.best_price = self.entry_price


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

    def resolve_exit(self, side: int, entry: float, when, spec: ExitSpec | None):
        """(stop, alvo|None, trailing|None, horário-limite|None) de um trade. Sem `spec`: `Config` (V0).

        `spec` inválida falha alto (ValueError): stop do lado errado, sem stop, distância <= 0, horário já passado.
        """
        tick = self.c.tick_size
        if spec is None:
            return (round_tick(entry - side * self.c.loss_points, tick),
                    round_tick(entry + side * self.c.gain_points, tick), None, None)
        if (spec.stop_points is None) == (spec.stop_price is None):
            raise ValueError("ExitSpec exige exatamente um entre stop_points e stop_price (toda posição tem stop protetivo)")
        if spec.stop_points is not None:
            if spec.stop_points <= 0:
                raise ValueError(f"stop_points deve ser > 0 (recebido {spec.stop_points})")
            stop = round_tick(entry - side * spec.stop_points, tick)
        else:
            stop = round_tick(spec.stop_price, tick)
        if (entry - stop) * side <= 0:
            raise ValueError(f"stop {stop} não está do lado protetivo da entrada {entry} (lado {side})")
        if spec.target_points is not None and spec.target_price is not None:
            raise ValueError("ExitSpec aceita no máximo um entre target_points e target_price")
        target = None
        if spec.target_points is not None:
            if spec.target_points <= 0:
                raise ValueError(f"target_points deve ser > 0 (recebido {spec.target_points})")
            target = round_tick(entry + side * spec.target_points, tick)
        elif spec.target_price is not None:
            target = round_tick(spec.target_price, tick)
        if target is not None and (target - entry) * side <= 0:
            raise ValueError(f"alvo {target} não está do lado favorável da entrada {entry} (lado {side})")
        if spec.trailing_points is not None and spec.trailing_points <= 0:
            raise ValueError(f"trailing_points deve ser > 0 (recebido {spec.trailing_points})")
        deadline = None
        if spec.exit_time is not None:
            deadline = when.normalize() + pd.Timedelta(hours=spec.exit_time.hour, minutes=spec.exit_time.minute)
            if deadline <= when:
                raise ValueError(f"exit_time {spec.exit_time} não é posterior à entrada ({when})")
        return stop, target, spec.trailing_points, deadline

    def open_position(self, when, side: int, raw_price: float, reason: str, exit_spec: ExitSpec | None = None) -> Position:
        entry = self.fill(side, raw_price)
        stop, target, trail, deadline = self.resolve_exit(side, entry, when, exit_spec)
        self.trade_id += 1
        self.trades_today += 1
        self.position = Position(self.trade_id, side, when, entry, self.c.quantity, stop, target,
                                 entry_reason=reason, trail_points=trail, exit_deadline=deadline)
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
        hit_stop = bar.low <= p.stop_current if p.side > 0 else bar.high >= p.stop_current
        if hit_stop:
            self.exit(bar.datetime, p.stop_current, "STOP_LOSS_ENTRY_BAR")

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
            "stop_price_inicial": p.stop_initial,
            "target_price_inicial": float("nan") if p.target_initial is None else p.target_initial, "exit_reason": reason,
            "gross_pnl": gross, "costs": costs, "net_pnl": gross - costs, "duration": when - p.entry_datetime,
            "equity_after_trade": self.cash,
            "MAE": p.mae * self.c.point_value_brl * p.quantity, "MFE": p.mfe * self.c.point_value_brl * p.quantity,
        })
        self.event(when, "EXIT", reason)
        self.position = None

    def process_position(self, bar) -> None:
        """Saídas de uma posição aberta em barra anterior: horário, stop (inclusive trailing) e alvo.

        Horário: saída a mercado na abertura da 1ª barra com horário >= o limite (antes de qualquer movimento
        da barra). Stop/alvo com gap: stop pior, alvo melhor; ambos na mesma barra: política intrabar.
        O trailing só é atualizado com esta barra depois de ela ser processada (vale para a seguinte).
        """
        p = self.position
        if p is None:
            return
        if p.exit_deadline is not None and bar.datetime >= p.exit_deadline:
            self.exit(bar.datetime, bar.open, "TIME_EXIT")
            return
        adverse = (p.entry_price - bar.low) if p.side > 0 else (bar.high - p.entry_price)
        favorable = (bar.high - p.entry_price) if p.side > 0 else (p.entry_price - bar.low)
        p.mae, p.mfe = max(p.mae, adverse), max(p.mfe, favorable)
        has_target = p.target_initial is not None
        if p.side > 0:
            hit_stop = bar.low <= p.stop_current
            hit_target = has_target and bar.high >= p.target_initial
            stop_price = min(bar.open, p.stop_current)
            target_price = max(bar.open, p.target_initial) if has_target else None
        else:
            hit_stop = bar.high >= p.stop_current
            hit_target = has_target and bar.low <= p.target_initial
            stop_price = max(bar.open, p.stop_current)
            target_price = min(bar.open, p.target_initial) if has_target else None
        stop_reason = "STOP_LOSS" if p.stop_current == p.stop_initial else "TRAILING_STOP"
        if hit_stop and hit_target:
            if self.c.intrabar_policy in ("adverse", "stop_first"):
                self.exit(bar.datetime, stop_price, "STOP_INTRABAR_AMBIGUOUS")
            else:
                self.exit(bar.datetime, target_price, "TARGET_INTRABAR_AMBIGUOUS")
        elif hit_stop:
            self.exit(bar.datetime, stop_price, stop_reason)
        elif hit_target:
            self.exit(bar.datetime, target_price, "TAKE_PROFIT")
        else:
            self.update_trailing(bar)

    def update_trailing(self, bar) -> None:
        """Aperta o stop com o melhor preço de barras JÁ FECHADAS; nunca o afrouxa."""
        p = self.position
        if p is None or p.trail_points is None:
            return
        if p.side > 0:
            p.best_price = max(p.best_price, bar.high)
            p.stop_current = max(p.stop_current, round_tick(p.best_price - p.trail_points, self.c.tick_size))
        else:
            p.best_price = min(p.best_price, bar.low)
            p.stop_current = min(p.stop_current, round_tick(p.best_price + p.trail_points, self.c.tick_size))

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
        self.open_position(bar.datetime, intent.side, raw_price, tag, intent.exit)
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
