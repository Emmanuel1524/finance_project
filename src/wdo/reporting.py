"""Relatório textual e gráficos dos resultados do backtest."""
from __future__ import annotations

import pandas as pd

from .engine import BacktestResults
from .metrics import metrics


def print_backtest_report(results: BacktestResults) -> None:
    report=pd.Series(metrics(results)); print(report.to_string())


def plot_results(results: BacktestResults) -> None:
    import matplotlib.pyplot as plt
    t,e=results.trades,results.equity
    if e.empty: print("Sem barras/operacões para plotar."); return
    fig,ax=plt.subplots(3,2,figsize=(15,12)); eq=e.set_index("datetime").equity; dd=eq-eq.cummax()
    eq.plot(ax=ax[0,0],title="Equity curve",ylabel="R$"); dd.plot(ax=ax[0,1],title="Drawdown",ylabel="R$")
    (eq-results.config.initial_capital).plot(ax=ax[1,0],title="PnL acumulado",ylabel="R$")
    if not t.empty:
        t.net_pnl.plot.hist(ax=ax[1,1],bins=20,title="Distribuição do PnL",xlabel="R$")
        monthly=t.set_index("exit_datetime").net_pnl.resample("ME").sum(); monthly.plot.bar(ax=ax[2,0],title="PnL mensal",ylabel="R$")
        t.assign(month=t.exit_datetime.dt.to_period("M")).groupby("month").size().plot.bar(ax=ax[2,1],title="Trades por mês",ylabel="Quantidade")
    plt.tight_layout()
