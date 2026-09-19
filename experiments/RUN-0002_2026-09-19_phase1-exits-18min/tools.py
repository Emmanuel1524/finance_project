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


# ====================================================================== RUN-0002: extensões
import os
import random
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace as _replace

from wdo import ExitSpec, OrderIntent, SessionDecision

REGISTRY_FIELDS = REGISTRY_FIELDS + ["hypothesis_source", "assumptions_challenged", "reopening_reason", "degrees_of_freedom",
                                     "placebo_mean_expectancy", "placebo_p95_expectancy", "placebo_excess", "placebo_draws",
                                     "cumulative_trials"]
PREV_TRIALS = 8          # experimentos da RUN-0001 sobre a mesma partição de pesquisa


class Recorder:
    """Envolve a estratégia, registra a ExitSpec por barra de entrada (para o placebo) e delega tudo."""

    def __init__(self, inner):
        self.inner, self.name, self.specs = inner, inner.name, {}

    def on_session_open(self, ctx):
        return self.inner.on_session_open(ctx)

    def on_bar_open(self, bar):
        intents = self.inner.on_bar_open(bar)
        for i in intents:
            spec = i.exit
            if spec is not None and spec.stop_price is not None:      # placebo simétrico: converte nível em distância
                spec = _replace(spec, stop_price=None, stop_points=abs(bar.open - spec.stop_price))
            if spec is not None or i.exit is None:
                self.specs[bar.datetime] = spec
                break
        return intents

    def on_bar_close(self, bar, *, entered):
        self.inner.on_bar_close(bar, entered=entered)


class PlaceboStrategy:
    """Entradas de direção ALEATÓRIA nos mesmos instantes das entradas realizadas do candidato, com a mesma saída."""
    name = "placebo"

    def __init__(self, entries, seed):
        self.entries, self.rng = entries, random.Random(seed)

    def on_session_open(self, ctx):
        return SessionDecision(label="PLACEBO")

    def on_bar_open(self, bar):
        if bar.datetime in self.entries:
            return [OrderIntent(self.rng.choice((1, -1)), "market", None, "PLACEBO", exit=self.entries[bar.datetime])]
        return []

    def on_bar_close(self, bar, *, entered):
        pass


def _placebo_draw(args):
    entries, cfg, seed = args
    res = run_strategy(lambda c: PlaceboStrategy(entries, seed), cfg)
    t = res.trades
    return {"n": int(len(t)), "expectancy": float(t.net_pnl.mean()) if len(t) else 0.0,
            "wr": float((t.net_pnl > 0).mean() * 100) if len(t) else 0.0, "pnl": float(t.net_pnl.sum())}


def placebo(entries, cfg, n_draws=10, seed0=1000):
    """n_draws sorteios (sementes fixas) em paralelo; devolve estatísticas da expectância do acaso."""
    jobs = [(entries, cfg, seed0 + i) for i in range(n_draws)]
    with ProcessPoolExecutor(max_workers=min(os.cpu_count() or 2, n_draws, 8)) as pool:
        draws = list(pool.map(_placebo_draw, jobs))
    exp = sorted(d["expectancy"] for d in draws)
    return {"draws": n_draws, "mean_expectancy": round(sum(exp) / len(exp), 2), "p95_expectancy": round(exp[int(0.95 * (len(exp) - 1))], 2),
            "max_expectancy": round(exp[-1], 2), "mean_wr": round(sum(d["wr"] for d in draws) / len(draws), 1),
            "mean_trades": round(sum(d["n"] for d in draws) / len(draws), 1)}


def load_metrics(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def run_experiment2(exp_id, slug, factory, hypothesis_md, strategy_config, parent_metrics, cfg=None, n_draws=10):
    """Hipótese gravada ANTES de rodar; replay na pesquisa; placebo; imprime candidato × V0 × pai × placebo."""
    import time as _time
    cfg = cfg or CFG
    d = start_experiment(f"{exp_id}_{slug}", hypothesis_md)
    rec = Recorder(factory(cfg))
    result = run_partition_backtest(research_bars(), PARTS, "research", cfg, strategy=rec)
    m = finish_experiment(d, result, strategy_config)
    entries = {t: rec.specs.get(t) for t in result.trades.entry_datetime}
    t0 = _time.time()
    pl = placebo(entries, cfg, n_draws) if len(entries) else None
    m["placebo"] = pl
    if pl:
        m["placebo_excess_expectancy"] = round(m["expectancy"] - pl["mean_expectancy"], 2)
        m["placebo_runtime_s"] = round(_time.time() - t0, 1)
    m["degrees_of_freedom"] = strategy_config.get("dof")
    (d / "metrics.json").write_text(json.dumps(m, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    base = load_metrics(RUN / "EXP-0000_baseline-v0" / "metrics.json")
    print("V0 (baseline)      :", line(base))
    print("PAI                :", line(parent_metrics))
    print("CANDIDATO          :", line(m))
    print("PLACEBO            :", pl, "| excesso da expectância:", m.get("placebo_excess_expectancy"))
    for k in ("months_positive", "monthly_pnl", "rolling20_min", "rolling20_pos_frac", "top5_trades_share", "top5_days_share",
              "max_month_share", "max_consec_losses", "max_days_underwater", "max_drawdown_pct", "worst_trade", "entry_bar_exits",
              "by_side", "by_entry", "regime_vol_high_next", "regime_up_next", "gates", "gates_pass"):
        print(k, "=", json.dumps(m.get(k), ensure_ascii=False))
    print("exit reasons:", result.trades.exit_reason.value_counts().to_dict())
    return d, m


def registry_row2(exp_id, parent, branch, family, hypothesis, change, decision, m, source, challenged, reopening, dof, n_in_run):
    row = registry_row(exp_id, parent, branch, family, hypothesis, change, decision, m)
    pl = m.get("placebo") or {}
    row.update(hypothesis_source=source, assumptions_challenged=challenged, reopening_reason=reopening, degrees_of_freedom=dof,
               placebo_mean_expectancy=pl.get("mean_expectancy"), placebo_p95_expectancy=pl.get("p95_expectancy"),
               placebo_excess=m.get("placebo_excess_expectancy"), placebo_draws=pl.get("draws"), cumulative_trials=PREV_TRIALS + n_in_run)
    return row
