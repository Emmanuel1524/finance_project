"""Auxiliares de teste: dados sintéticos determinísticos e estratégia roteirizada."""
from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pandas as pd

from wdo import OrderIntent, SessionDecision, SessionOpen

TZ = "America/Sao_Paulo"


def make_bars(days: int = 45, seed: int = 7, bars_per_day: int = 48, start: str = "2026-03-02") -> pd.DataFrame:
    """Passeio aleatório M5 (09:00 em diante), dias úteis, OHLC válido no tick de 0,5; com gaps overnight."""
    rng = np.random.RandomState(seed)
    rows, price = [], 5000.0
    for day in pd.bdate_range(start, periods=days):
        price += rng.normal(0, 4)                       # gap de abertura
        for i in range(bars_per_day):
            ts = day + pd.Timedelta(hours=9) + pd.Timedelta(minutes=5 * i)
            o = round(price * 2) / 2
            c = round((price + rng.normal(0, 1.6)) * 2) / 2
            h = round((max(o, c) + abs(rng.normal(0, 0.9))) * 2) / 2
            l = round((min(o, c) - abs(rng.normal(0, 0.9))) * 2) / 2
            rows.append([ts, o, max(h, o, c), min(l, o, c), c, int(rng.randint(100, 900))])
            price = c
    return pd.DataFrame(rows, columns=["datetime", "open", "high", "low", "close", "volume"])


def bar(dt: str = "2026-03-30 09:00", open=5000.0, high=5001.0, low=4999.0, close=5000.0, rsi=50.0):
    """Barra de teste (aceita por `process_session_bar` / `process_position`)."""
    return SimpleNamespace(datetime=pd.Timestamp(dt, tz=TZ), open=open, high=high, low=low, close=close, rsi=rsi)


def session_ctx(open=5000.0, pdh=5100.0, pdl=4900.0, emas=None, rsi=50.0, carried=False) -> SessionOpen:
    return SessionOpen(pd.Timestamp("2026-03-30").date(), open, pdh, pdl,
                       tuple(emas or (4990.0, 4991.0, 4992.0, 4993.0, 4994.0, 4995.0)), rsi, carried)


class ScriptedStrategy:
    """Estratégia mínima: devolve ordens fixas por índice de barra da sessão (para testar o simulador)."""
    name = "scripted"

    def __init__(self, script: dict[int, list[OrderIntent]] | None = None, session_orders=()):
        self.script = script or {}
        self.session_orders = list(session_orders)
        self.seen: list = []

    def on_session_open(self, ctx):
        return SessionDecision(orders=self.session_orders, label="SCRIPTED")

    def on_bar_open(self, bar):
        self.seen.append(bar)
        return list(self.script.get(bar.index_in_session, []))

    def on_bar_close(self, bar, *, entered):
        pass


def events_until(result, t: pd.Timestamp) -> pd.DataFrame:
    """Eventos com datetime <= t, sem o encerramento artificial de fim de dados (depende do futuro por definição)."""
    ev = result.events
    return ev[(ev.datetime <= t) & (ev.detail != "END_OF_DATA")].reset_index(drop=True)


def equity_until(result, t: pd.Timestamp) -> pd.DataFrame:
    eq = result.equity
    return eq[eq.datetime <= t].reset_index(drop=True)
