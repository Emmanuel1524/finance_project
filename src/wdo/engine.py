"""Motor de replay bar-by-bar do Robo_Abertura_WDO_Genial v1.35 (OHLC conservador e auditável).

O módulo não simula ticks ou book. Toda decisão intrabar com OHLC é registrada
e usa a ordem adversa para a estratégia quando a sequência é desconhecida.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

from .config import Config, round_tick
from .data import validate_bars
from .indicators import add_point_in_time_indicators


@dataclass
class PendingOrder:
    side: int
    kind: Literal["stop", "limit"]
    price: float
    tag: str


@dataclass
class Position:
    trade_id: int; side: int; entry_datetime: pd.Timestamp; entry_price: float
    quantity: float; stop_initial: float; target_initial: float; mae: float = 0.; mfe: float = 0.


@dataclass
class BacktestResults:
    trades: pd.DataFrame
    equity: pd.DataFrame
    events: pd.DataFrame
    config: Config


class WDOReplayEngine:
    def __init__(self, config: Config):
        self.c = config; self.cash = config.initial_capital; self.position = None; self.pending = []
        self.events, self.closed = [], []; self.trade_id = 0; self.day_state = None

    def event(self, when, event, detail=""):
        self.events.append({"datetime": when, "event": event, "detail": detail})

    def fill(self, side: int, price: float) -> float:
        return round_tick(price + side * self.c.slippage_points, self.c.tick_size)

    def enter(self, when, side, price, reason):
        if self.position is not None or self.day_state["operated"]: return
        entry = self.fill(side, price); self.trade_id += 1
        self.position = Position(self.trade_id, side, when, entry, self.c.quantity,
                                 round_tick(entry - side*self.c.loss_points, self.c.tick_size),
                                 round_tick(entry + side*self.c.gain_points, self.c.tick_size))
        self.day_state["operated"] = True; self.pending.clear(); self.event(when, "ENTRY", reason)

    def exit(self, when, price, reason):
        p = self.position; exit_price = self.fill(-p.side, price)
        gross = (exit_price - p.entry_price) * p.side * p.quantity * self.c.point_value_brl
        costs = 2 * p.quantity * (self.c.commission_per_contract + self.c.fees_per_contract)
        self.cash += gross - costs
        self.closed.append({"trade_id": p.trade_id, "side": "LONG" if p.side > 0 else "SHORT", "entry_datetime": p.entry_datetime,
            "entry_price": p.entry_price, "exit_datetime": when, "exit_price": exit_price, "quantity": p.quantity,
            "stop_price_inicial": p.stop_initial, "target_price_inicial": p.target_initial, "exit_reason": reason,
            "gross_pnl": gross, "costs": costs, "net_pnl": gross-costs, "duration": when-p.entry_datetime,
            "equity_after_trade": self.cash, "MAE": p.mae*self.c.point_value_brl*p.quantity, "MFE": p.mfe*self.c.point_value_brl*p.quantity})
        self.event(when, "EXIT", reason); self.position = None

    def process_position(self, bar):
        p = self.position
        if p is None: return
        adverse = (p.entry_price - bar.low) if p.side > 0 else (bar.high - p.entry_price)
        favorable = (bar.high - p.entry_price) if p.side > 0 else (p.entry_price - bar.low)
        p.mae = max(p.mae, adverse); p.mfe = max(p.mfe, favorable)
        hit_stop = bar.low <= p.stop_initial if p.side > 0 else bar.high >= p.stop_initial
        hit_target = bar.high >= p.target_initial if p.side > 0 else bar.low <= p.target_initial
        if hit_stop and hit_target:
            reason = "STOP_INTRABAR_AMBIGUOUS" if self.c.intrabar_policy in ("adverse", "stop_first") else "TARGET_INTRABAR_AMBIGUOUS"
            self.exit(bar.datetime, p.stop_initial if "STOP" in reason else p.target_initial, reason)
        elif hit_stop: self.exit(bar.datetime, p.stop_initial, "STOP_LOSS")
        elif hit_target: self.exit(bar.datetime, p.target_initial, "TAKE_PROFIT")

    def process_pending(self, bar):
        hits = []
        for order in self.pending:
            hit = (order.side > 0 and ((order.kind == "stop" and bar.high >= order.price) or (order.kind == "limit" and bar.low <= order.price))) or (order.side < 0 and ((order.kind == "stop" and bar.low <= order.price) or (order.kind == "limit" and bar.high >= order.price)))
            if hit: hits.append(order)
        if hits:
            # Se duas pernas forem alcançadas na mesma barra, escolhe o pior preço para o lado.
            order = min(hits, key=lambda o:o.price) if hits[0].side > 0 else max(hits, key=lambda o:o.price)
            self.enter(bar.datetime, order.side, order.price, f"P3_{order.tag}")

    def start_day(self, day_bars):
        first = day_bars.iloc[0]; prior = self.prior_daily.loc[:first.datetime.normalize()-pd.Timedelta(nanoseconds=1)]
        if prior.empty: return
        pdh, pdl = prior.iloc[-1].high, prior.iloc[-1].low
        emas = [first[f"ema_{tf}_{n}"] for tf in ("h1", "d1") for n in (13,17,21)]
        if any(pd.isna(emas)) or pd.isna(first.rsi): return
        self.day_state = {"date": first.datetime.date(), "operated": False, "pattern": 0, "direction": 0, "reference": None,
                          "pdh": pdh, "pdl": pdl, "sup": round_tick(pdh-self.c.channel_offset,self.c.tick_size), "inf": round_tick(pdl+self.c.channel_offset,self.c.tick_size),
                          "ema_support": max((x for x in emas if x <= first.open), default=0.), "ema_resistance": min((x for x in emas if x >= first.open), default=0.), "open_rsi": first.rsi}
        # Uma posição herdada mantém seus SL/TP na corretora; não abre outra hoje.
        if self.position is not None:
            self.day_state["operated"] = True
            self.event(first.datetime, "SESSION", "POSITION_CARRIED")
            return
        s = self.day_state; op = first.open
        if op > s["pdh"]: s.update(pattern=4,direction=-1,wait=first.rsi > self.c.rsi_sell_max)
        elif op < s["pdl"]: s.update(pattern=4,direction=1,wait=first.rsi < self.c.rsi_buy_min)
        elif op >= s["sup"]: s.update(pattern=3,direction=-1); self.place_channel_orders(-1)
        elif op <= s["inf"]: s.update(pattern=3,direction=1); self.place_channel_orders(1)
        else:
            s["pattern"] = 1; s["direction"] = 1 if op > max(emas) else -1 if op < min(emas) else 0
        self.event(first.datetime, "SESSION", f"P{s['pattern']}")

    def place_channel_orders(self, side):
        s=self.day_state
        stop = s["sup"]-self.c.breakout_points if side < 0 else s["inf"]+self.c.breakout_points
        limit = s["pdh"]+self.c.breakout_points if side < 0 else s["pdl"]-self.c.breakout_points
        if self.c.channel_mode in (0,1): self.pending.append(PendingOrder(side,"stop",round_tick(stop,self.c.tick_size),"STOP"))
        if self.c.channel_mode in (0,2): self.pending.append(PendingOrder(side,"limit",round_tick(limit,self.c.tick_size),"LIMIT"))

    def signal(self, bar, index_in_session):
        s=self.day_state
        if s is None or s["operated"]: return
        if s["pattern"] == 1 and index_in_session == 0:
            sup,res=s["ema_support"],s["ema_resistance"]
            buy = sup and bar.low <= round_tick(sup,self.c.tick_size)+self.c.ema_touch_tolerance
            sell = res and bar.high >= round_tick(res,self.c.tick_size)-self.c.ema_touch_tolerance
            if buy and sell: self.enter(bar.datetime, 1 if abs(bar.open-sup)<=abs(res-bar.open) else -1, bar.open, "P1_EMA_DOUBLE")
            elif buy: self.enter(bar.datetime,1,bar.open,"P1_EMA")
            elif sell: self.enter(bar.datetime,-1,bar.open,"P1_EMA")
            return
        if s["pattern"] == 1 and index_in_session == 1:
            s["pattern"] = 2; s["reference"] = self.previous_bar
        if s["pattern"] == 2 and s["reference"] is not None:
            ref=s["reference"]
            if bar.low <= ref.low and bar.high >= ref.high: self.enter(bar.datetime,1,bar.open,"P2_AMBIGUOUS_LOW_FIRST")
            elif bar.low <= ref.low: self.enter(bar.datetime,1,bar.open,"P2_LOW")
            elif bar.high >= ref.high: self.enter(bar.datetime,-1,bar.open,"P2_HIGH")
            else: s["reference"] = bar
        elif s["pattern"] == 4:
            immediate=(s["direction"]>0 and self.c.rsi_buy_min<=s["open_rsi"]<=self.c.rsi_buy_max) or (s["direction"]<0 and self.c.rsi_sell_min<=s["open_rsi"]<=self.c.rsi_sell_max)
            crossed=(s["direction"]>0 and not s["wait"] and bar.rsi<=self.c.rsi_buy_max) or (s["direction"]<0 and not s["wait"] and bar.rsi>=self.c.rsi_sell_min)
            if immediate or crossed: self.enter(bar.datetime,s["direction"],bar.open,"P4_RSI")
            elif index_in_session >= 1 and s["wait"]:
                ref=self.previous_bar
                if bar.low<=ref.low or bar.high>=ref.high: self.enter(bar.datetime,s["direction"],bar.open,"P4_WAIT_REFERENCE")

    def run(self, bars: pd.DataFrame) -> BacktestResults:
        data=add_point_in_time_indicators(validate_bars(bars,self.c.timezone),self.c)
        daily=data.set_index("datetime").resample("1D").agg(high=("high","max"),low=("low","min")).dropna(); self.prior_daily=daily
        equities=[]; self.previous_bar=None
        for date, day in data.groupby(data.datetime.dt.date, sort=True):
            session=day[(day.datetime.dt.hour*60+day.datetime.dt.minute >= self.c.start_hour*60+self.c.start_minute) & (day.datetime.dt.hour*60+day.datetime.dt.minute < self.c.end_hour*60+self.c.end_minute)]
            if not session.empty: self.start_day(session)
            session_positions = {timestamp: i for i, timestamp in enumerate(session.datetime)}
            for bar in day.itertuples(index=False):
                # SL/TP seguem ativos fora da janela, como ordens anexadas pelo MT5.
                self.process_position(bar)
                if bar.datetime in session_positions and self.day_state is not None:
                    i = session_positions[bar.datetime]
                    self.process_pending(bar); self.signal(bar,i)
                unrealized=0 if self.position is None else (bar.close-self.position.entry_price)*self.position.side*self.position.quantity*self.c.point_value_brl
                equities.append({"datetime":bar.datetime,"equity":self.cash+unrealized,"cash":self.cash,"in_position":self.position is not None})
                if bar.datetime in session_positions: self.previous_bar=bar
            self.pending.clear(); self.day_state=None
        if self.position is not None: self.exit(data.iloc[-1].datetime,data.iloc[-1].close,"END_OF_DATA")
        return BacktestResults(pd.DataFrame(self.closed),pd.DataFrame(equities),pd.DataFrame(self.events),self.c)


def run_backtest(bars: pd.DataFrame, start="2026-01-01", end="2026-09-01", initial_capital=10_000, config: Config | None=None) -> BacktestResults:
    config = config or Config(initial_capital=initial_capital)
    data=validate_bars(bars,config.timezone); begin=pd.Timestamp(start,tz=config.timezone); finish=pd.Timestamp(end,tz=config.timezone)+pd.Timedelta(days=1)-pd.Timedelta(minutes=5)
    return WDOReplayEngine(config).run(data[(data.datetime>=begin)&(data.datetime<=finish)].copy())
