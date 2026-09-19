"""Análise A (não é tentativa): placebo de SELEÇÃO para o filtro de volatilidade do EXP-0012, e diagnósticos do item 4.

Sorteia subconjuntos aleatórios (sem reposição) de 45 dos 100 trades do EXP-0011 e compara com o EXP-0012.
Só lê trades.csv já gravados (partição de pesquisa); não roda replay.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

R2 = Path(__file__).resolve().parents[1] / "RUN-0002_2026-09-19_phase1-exits-18min"
OUT = Path(__file__).resolve().parent
t11 = pd.read_csv(next(R2.glob("EXP-0011_*")) / "trades.csv", parse_dates=["entry_datetime", "exit_datetime"])
t12 = pd.read_csv(next(R2.glob("EXP-0012_*")) / "trades.csv", parse_dates=["entry_datetime", "exit_datetime"])
m12 = json.loads(next(R2.glob("EXP-0012_*")).joinpath("metrics.json").read_text(encoding="utf-8"))


def stats(pnl: np.ndarray):
    gp, gl = pnl[pnl > 0].sum(), -pnl[pnl < 0].sum()
    top5 = np.sort(pnl)[-5:].clip(min=0).sum() / gp if gp > 0 else np.nan
    return pnl.mean(), (gp / gl if gl > 0 else np.inf), top5


pnl11 = t11.net_pnl.to_numpy()
pnl12 = t12.net_pnl.to_numpy()
n_sub, n_draw = len(pnl12), 20000
subset_of = set(t12.entry_datetime) <= set(t11.entry_datetime)
rng = np.random.default_rng(20260919)
draws = np.array([stats(rng.choice(pnl11, n_sub, replace=False)) for _ in range(n_draw)])
obs_mean, obs_pf, obs_top5 = stats(pnl12)
p_mean = float((draws[:, 0] >= obs_mean).mean())
p_pf = float((draws[:, 1] >= obs_pf).mean())
p_top5 = float((draws[:, 2] >= obs_top5).mean())   # prob. de o acaso ser TÃO concentrado quanto o observado
q = lambda a: [round(float(x), 3) for x in np.percentile(a, [5, 50, 95])]

# diagnósticos item 4: long/short e metade inicial/final do período de pesquisa
def split(t, label):
    t = t.copy()
    mid = t.entry_datetime.min() + (t.entry_datetime.max() - t.entry_datetime.min()) / 2
    return {
        label: {
            "long": {"n": int((t.side == "LONG").sum()), "pnl": round(float(t[t.side == "LONG"].net_pnl.sum()), 1)},
            "short": {"n": int((t.side == "SHORT").sum()), "pnl": round(float(t[t.side == "SHORT"].net_pnl.sum()), 1)},
            "1a metade": {"n": int((t.entry_datetime <= mid).sum()), "pnl": round(float(t[t.entry_datetime <= mid].net_pnl.sum()), 1)},
            "2a metade": {"n": int((t.entry_datetime > mid).sum()), "pnl": round(float(t[t.entry_datetime > mid].net_pnl.sum()), 1)},
        }
    }


diag = {**split(t11, "EXP-0011"), **split(t12, "EXP-0012")}

md = f"""# Análise A — placebo de seleção do filtro de volatilidade (EXP-0012)  [não é tentativa]

Método: {n_draw:,} subconjuntos aleatórios (sem reposição, semente fixa) de {n_sub} dos {len(pnl11)} trades do EXP-0011 (arquitetura sem filtro), comparados com o EXP-0012 (os mesmos trades sob o filtro D7 de alta volatilidade). Os {n_sub} trades do EXP-0012 são um subconjunto dos do EXP-0011: **{subset_of}**.

| Métrica | EXP-0012 (observado) | Acaso: p5 / mediana / p95 | P(acaso ≥ observado) |
|---|---|---|---|
| PnL médio por trade (R$) | {obs_mean:.1f} | {' / '.join(map(str, q(draws[:, 0])))} | **{p_mean:.3f}** |
| Profit Factor | {obs_pf:.2f} | {' / '.join(map(str, q(draws[:, 1])))} | **{p_pf:.3f}** |
| Top-5 trades / lucro bruto | {obs_top5:.2f} | {' / '.join(map(str, q(draws[:, 2])))} | {p_top5:.3f} |

**Leitura.** A probabilidade de uma seleção ao acaso (do mesmo tamanho, dentro dos trades da própria arquitetura) igualar o PnL médio do EXP-0012 é **{p_mean:.1%}**; a do PF é {p_pf:.1%}. Isso mede a sorte de *selecionar* dias, não a de a arquitetura ter edge. A regra de volatilidade (D7) foi escolhida DEPOIS de ver a decomposição na mesma amostra (data-informed), então mesmo uma probabilidade baixa não a torna evidência independente; e a concentração (top-5 = {obs_top5:.0%} do lucro bruto) é {'esperada' if p_top5 > 0.2 else 'incomum'} para subconjuntos deste tamanho (P = {p_top5:.2f}).

## Item 4 — diagnósticos (long/short e metades do período de pesquisa)
```
{json.dumps(diag, indent=1, ensure_ascii=False)}
```
Nota: assimetria long/short e diferença entre metades **sem mecanismo independente** não geram hipótese nesta run (seriam decomposição).
"""
(OUT / "selection_placebo.md").write_text(md, encoding="utf-8")
print(md)
