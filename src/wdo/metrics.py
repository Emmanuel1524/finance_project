"""Métricas de desempenho (estilo relatório do MT5) a partir de `BacktestResults`."""
from __future__ import annotations

import numpy as np

from .engine import BacktestResults


def metrics(results: BacktestResults) -> dict:
    t=results.trades; c=results.config
    if t.empty: return {"Capital inicial":c.initial_capital,"Capital final":c.initial_capital,"Total Trades":0}
    pnl=t.net_pnl; wins=pnl[pnl>0]; losses=pnl[pnl<0]; curve=results.equity.equity
    running_max=curve.cummax(); dd=curve-running_max; dd_pct=dd/running_max.replace(0,np.nan)
    signs=(pnl>0).astype(int); groups=(signs!=signs.shift()).cumsum(); streak=signs.groupby(groups).sum(); loss_streak=(1-signs).groupby(groups).sum()
    days=max(1,results.equity.datetime.dt.date.nunique()); position_pct=results.equity.in_position.mean()*100
    gross_profit=wins.sum(); gross_loss=losses.sum(); final=c.initial_capital+pnl.sum()
    return {"Capital inicial":c.initial_capital,"Capital final":final,"Net Profit":pnl.sum(),"Gross Profit":gross_profit,"Gross Loss":gross_loss,
      "Profit Factor":gross_profit/abs(gross_loss) if gross_loss else np.inf,"Expected Payoff":pnl.mean(),"Total Return %":(final/c.initial_capital-1)*100,
      "Maximum Drawdown R$":dd.min(),"Maximum Drawdown %":dd_pct.min()*100,"Recovery Factor":pnl.sum()/abs(dd.min()) if dd.min() else np.inf,
      "Total Trades":len(t),"Total LONG trades":(t.side=="LONG").sum(),"Total SHORT trades":(t.side=="SHORT").sum(),"Winning Trades":len(wins),"Losing Trades":len(losses),
      "Win Rate %":len(wins)/len(t)*100,"LONG Win Rate %":t.loc[t.side=="LONG","net_pnl"].gt(0).mean()*100,"SHORT Win Rate %":t.loc[t.side=="SHORT","net_pnl"].gt(0).mean()*100,
      "Average Trade":pnl.mean(),"Average Winner":wins.mean(),"Average Loser":losses.mean(),"Largest Winner":wins.max(),"Largest Loser":losses.min(),
      "Payoff Ratio":wins.mean()/abs(losses.mean()) if len(losses) else np.inf,"Consecutive Wins máximo":streak.max(),"Consecutive Losses máximo":loss_streak.max(),
      "tempo médio por operação":t.duration.mean(),"maior duração":t.duration.max(),"menor duração":t.duration.min(),"operações médias por dia":len(t)/days,"percentual do período em posição":position_pct}
