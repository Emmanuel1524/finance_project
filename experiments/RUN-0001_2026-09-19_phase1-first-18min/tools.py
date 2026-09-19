"""Utilitários da RUN-0001: avaliação padronizada de candidatos na partição de PESQUISA.

Não altera o motor. Métricas, diagnósticos (06 §3–§4, §11), regimes D7, portões D3 e gravação de artefatos.
"""
from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from wdo import Config, Partitions, load_partition_bars, run_partition_backtest

ROOT = Path(__file__).resolve().parents[2]
RUN = Path(__file__).resolve().parent
CFG_PATH = ROOT / "configs" / "wdo_default.toml"
CFG = Config.from_toml(CFG_PATH)
PARTS = Partitions.from_toml(CFG_PATH)
_BARS = None
GATES = dict(min_trades=30, max_dd_pct=15.0, top5_trades_share=0.40, max_month_share=0.40)
REGISTRY_FIELDS = ["experiment_id", "parent_id", "research_branch", "hypothesis_family", "hypothesis", "change_summary",
                   "decision", "net_pnl", "profit_factor", "win_rate", "max_drawdown_pct", "trade_count", "payoff",
                   "expectancy", "top5_trades_share", "max_month_share", "months_positive", "gates_pass", "timestamp"]


def research_bars():
    global _BARS
    if _BARS is None:
        _BARS, _, _ = load_partition_bars(ROOT / "data" / "raw" / "wdo_data.csv", PARTS, "research", timezone=CFG.timezone)
    return _BARS


def run_strategy(strategy_factory=None, cfg=None):
    """Replay na partição de pesquisa (guarda de partições; nunca `authorized=True`)."""
    cfg = cfg or CFG
    strategy = strategy_factory(cfg) if strategy_factory else None
    return run_partition_backtest(research_bars(), PARTS, "research", cfg, strategy=strategy)


def _regimes(bars: pd.DataFrame) -> pd.DataFrame:
    d = bars.groupby(bars.datetime.dt.date).agg(high=("high", "max"), low=("low", "min"), close=("close", "last"))
    d["range"] = d.high - d.low
    med = d["range"].rolling(20, min_periods=10).median()
    d["vol_high_next"] = (d["range"] > med).shift(1)                   # regime do pregão seguinte, conhecido no fechamento anterior
    d["ret5"] = (d.close / d.close.shift(5) - 1)
    d["up_next"] = (d["ret5"] > 0).shift(1)
    return d


def diagnostics(result) -> dict:
    t, eq, c = result.trades.copy(), result.equity, result.config
    out: dict = {"engine_version": result.engine_version, "strategy": result.strategy_name}
    n = len(t)
    out["trade_count"] = n
    if n == 0:
        out.update(net_pnl=0.0, profit_factor=None, win_rate=None, gates_pass=False, gates={"min_trades": False})
        return out
    pnl = t.net_pnl
    wins, losses = pnl[pnl > 0], pnl[pnl < 0]
    gp, gl = wins.sum(), -losses.sum()
    out.update(net_pnl=round(float(pnl.sum()), 2), gross_profit=round(float(gp), 2), gross_loss=round(float(gl), 2),
               profit_factor=round(float(gp / gl), 3) if gl > 0 else None, win_rate=round(float(len(wins) / n * 100), 2),
               avg_win=round(float(wins.mean()), 2) if len(wins) else 0.0, avg_loss=round(float(losses.mean()), 2) if len(losses) else 0.0,
               payoff=round(float(wins.mean() / -losses.mean()), 3) if len(wins) and len(losses) else None,
               expectancy=round(float(pnl.mean()), 2), avg_duration_min=round(float(t.duration.dt.total_seconds().mean() / 60), 1))
    # sequências
    s = (pnl > 0).astype(int).to_numpy()
    def longest(v):
        best = cur = 0
        for x in s:
            cur = cur + 1 if x == v else 0
            best = max(best, cur)
        return best
    out["max_consec_wins"], out["max_consec_losses"] = longest(1), longest(0)
    # drawdown (equity por barra) e duração
    curve = eq.set_index("datetime").equity
    dd = curve - curve.cummax()
    out["max_drawdown_brl"] = round(float(dd.min()), 2)
    out["max_drawdown_pct"] = round(float(-dd.min() / c.initial_capital * 100), 2)
    daily_eq = curve.groupby(curve.index.date).last()
    under = (daily_eq < daily_eq.cummax()).astype(int).to_numpy()
    run = best = 0
    for u in under:
        run = run + 1 if u else 0
        best = max(best, run)
    out["max_days_underwater"] = int(best)
    # mensal / rolante / diário
    t["exit_day"] = t.exit_datetime.dt.date
    monthly = t.groupby(t.exit_datetime.dt.strftime("%Y-%m")).net_pnl.sum()
    out["monthly_pnl"] = {k: round(float(v), 2) for k, v in monthly.items()}
    out["months_positive"] = f"{int((monthly > 0).sum())}/{len(monthly)}"
    total = pnl.sum()
    out["max_month_share"] = round(float(monthly.max() / total), 3) if total > 0 else None
    daily = t.groupby("exit_day").net_pnl.sum().reindex(sorted(set(eq.datetime.dt.date)), fill_value=0.0)
    roll = daily.rolling(20).sum().dropna()
    out["rolling20_min"], out["rolling20_pos_frac"] = round(float(roll.min()), 2), round(float((roll > 0).mean()), 3)
    # concentração
    out["top5_trades_share"] = round(float(pnl.nlargest(5).clip(lower=0).sum() / gp), 3) if gp > 0 else None
    out["top5_days_share"] = round(float(daily.nlargest(5).clip(lower=0).sum() / daily.clip(lower=0).sum()), 3) if (daily > 0).any() else None
    out["worst_trade"], out["worst_5_sum"] = round(float(pnl.min()), 2), round(float(pnl.nsmallest(5).sum()), 2)
    # long/short e por padrão
    out["by_side"] = {k: {"n": int(len(g)), "pnl": round(float(g.net_pnl.sum()), 2)} for k, g in t.groupby("side")}
    out["by_entry"] = {k: {"n": int(len(g)), "pnl": round(float(g.net_pnl.sum()), 2), "wr": round(float((g.net_pnl > 0).mean() * 100), 1)}
                       for k, g in t.groupby("entry_reason")}
    out["entry_bar_exits"] = int((t.exit_datetime == t.entry_datetime).sum())
    # regimes D7 (grupos com < 15 trades = inconclusivo)
    reg = _regimes(research_bars())
    for col, names in (("vol_high_next", ("vol_alta", "vol_baixa")), ("up_next", ("alta_5d", "baixa_5d"))):
        flags = t.entry_datetime.dt.date.map(reg[col])
        groups = {}
        for val, name in ((True, names[0]), (False, names[1])):
            g = t[flags == val]
            groups[name] = {"n": int(len(g)), "pnl": round(float(g.net_pnl.sum()), 2),
                            "status": "inconclusivo" if len(g) < 15 else "ok"}
        out["regime_" + col] = groups
    # portões D3
    dd_ok = out["max_drawdown_pct"] <= GATES["max_dd_pct"]
    gates = {"min_trades": n >= GATES["min_trades"], "max_drawdown": bool(dd_ok),
             "top5_trades": out["top5_trades_share"] is not None and out["top5_trades_share"] <= GATES["top5_trades_share"],
             "month_concentration": out["max_month_share"] is not None and out["max_month_share"] <= GATES["max_month_share"],
             "expectancy_positive": out["expectancy"] > 0}
    out["gates"], out["gates_pass"] = {k: bool(v) for k, v in gates.items()}, bool(all(gates.values()))
    return out


def start_experiment(exp_dir: str, hypothesis_md: str) -> Path:
    """Cria a pasta e grava a hipótese ANTES de rodar."""
    d = RUN / exp_dir
    d.mkdir(exist_ok=False)
    (d / "hypothesis.md").write_text(hypothesis_md, encoding="utf-8")
    return d


def finish_experiment(d: Path, result, strategy_config: dict) -> dict:
    m = diagnostics(result)
    (d / "metrics.json").write_text(json.dumps(m, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    (d / "strategy_config.json").write_text(json.dumps({**strategy_config, "engine_version": result.engine_version,
                                                        "base_config": CFG.__dict__}, indent=1, default=str), encoding="utf-8")
    result.trades.to_csv(d / "trades.csv", index=False)
    eq = result.equity.set_index("datetime").equity
    eq.groupby(eq.index.date).last().rename("equity_eod").to_csv(d / "equity.csv")
    return m


def line(m: dict) -> str:
    if not m.get("trade_count"):
        return "sem trades"
    return (f"PF {m['profit_factor']} | WR {m['win_rate']}% | PnL R$ {m['net_pnl']} | MaxDD {m['max_drawdown_pct']}% | "
            f"Trades {m['trade_count']} | Payoff {m['payoff']} | Exp R$ {m['expectancy']}")


def write_decision(d: Path, text: str) -> None:
    (d / "decision.md").write_text(text, encoding="utf-8")


def add_registry(row: dict) -> None:
    path = RUN / "registry.csv"
    new = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=REGISTRY_FIELDS)
        if new:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in REGISTRY_FIELDS} | {"timestamp": datetime.now().isoformat(timespec="seconds")})


def registry_row(exp_id, parent, branch, family, hypothesis, change, decision, m) -> dict:
    return dict(experiment_id=exp_id, parent_id=parent, research_branch=branch, hypothesis_family=family,
                hypothesis=hypothesis, change_summary=change, decision=decision, net_pnl=m.get("net_pnl"),
                profit_factor=m.get("profit_factor"), win_rate=m.get("win_rate"), max_drawdown_pct=m.get("max_drawdown_pct"),
                trade_count=m.get("trade_count"), payoff=m.get("payoff"), expectancy=m.get("expectancy"),
                top5_trades_share=m.get("top5_trades_share"), max_month_share=m.get("max_month_share"),
                months_positive=m.get("months_positive"), gates_pass=m.get("gates_pass"))


def show(exp_id, parent_id="EXP-0000"):
    """Imprime comparação candidato × V0 × pai a partir de metrics.json (artefatos já gravados)."""
    load = lambda i: json.loads((next(RUN.glob(f"{i}_*")) / "metrics.json").read_text(encoding="utf-8"))
    m = load(exp_id)
    print("BASELINE V0 :", line(load("EXP-0000")))
    print("PAI", parent_id, ":", line(load(parent_id)))
    print("CANDIDATO   :", line(m))
    for k in ("months_positive", "monthly_pnl", "rolling20_min", "rolling20_pos_frac", "top5_trades_share", "top5_days_share",
              "max_month_share", "max_consec_losses", "max_days_underwater", "worst_trade", "entry_bar_exits", "by_side",
              "by_entry", "regime_vol_high_next", "regime_up_next", "gates", "gates_pass"):
        print(k, "=", json.dumps(m.get(k), ensure_ascii=False))
    return m


def run_experiment(exp_id, slug, factory, hypothesis_md, strategy_config, parent_id="EXP-0000", cfg=None):
    """Grava a hipótese ANTES de rodar, roda na partição de pesquisa e imprime comparação com V0 e pai."""
    d = start_experiment(f"{exp_id}_{slug}", hypothesis_md)
    result = run_strategy(factory, cfg)
    finish_experiment(d, result, strategy_config)
    return d, show(exp_id, parent_id)
