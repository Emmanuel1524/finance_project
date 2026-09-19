"""Análises B e C (não são tentativas), partição de PESQUISA apenas.

B: placebo reforçado (200 sorteios) da arquitetura ORB estrutural (EXP-0011): o sinal de direção supera o acaso?
C: deriva intradiária da amostra (abertura -> 17:55) como mecanismo independente da assimetria long/short.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tools
from wdo.strategies.candidates_run2 import OrbStructuralStop

R2 = tools.ROOT / "experiments" / "RUN-0002_2026-09-19_phase1-exits-18min"

if __name__ == "__main__":
    # ---------------- B
    rec = tools.Recorder(OrbStructuralStop(tools.CFG))
    res = tools.run_partition_backtest(tools.research_bars(), tools.PARTS, "research", tools.CFG, strategy=rec)
    entries = {t: rec.specs.get(t) for t in res.trades.entry_datetime}
    cand_exp = float(res.trades.net_pnl.mean())
    t0 = time.time()
    n_draws = 200
    jobs = [(entries, tools.CFG, 5000 + i) for i in range(n_draws)]
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=8) as pool:
        draws = list(pool.map(tools._placebo_draw, jobs, chunksize=4))
    exps = np.array([d["expectancy"] for d in draws])
    secs = time.time() - t0
    p_emp = float((exps >= cand_exp).mean())
    b = {"candidate_expectancy": round(cand_exp, 2), "draws": n_draws, "runtime_s": round(secs, 1),
         "placebo_mean": round(float(exps.mean()), 2), "placebo_sd": round(float(exps.std(ddof=1)), 2),
         "placebo_p5_p50_p95": [round(float(x), 2) for x in np.percentile(exps, [5, 50, 95])], "placebo_max": round(float(exps.max()), 2),
         "P(placebo >= candidato)": round(p_emp, 3), "z": round((cand_exp - exps.mean()) / exps.std(ddof=1), 2)}

    # ---------------- C
    bars = tools.research_bars()
    bars = bars[bars.datetime.dt.date.isin(sorted(set(res.trades.entry_datetime.dt.date)))]
    day = bars.groupby(bars.datetime.dt.date)
    first_open = day.apply(lambda g: g.iloc[0].open)
    late = day.apply(lambda g: g[(g.datetime.dt.hour == 17) & (g.datetime.dt.minute == 55)].close.iloc[0] if ((g.datetime.dt.hour == 17) & (g.datetime.dt.minute == 55)).any() else np.nan)
    drift = (late - first_open).dropna()
    c = {"days": int(len(drift)), "mean_open_to_1755_pts": round(float(drift.mean()), 2), "median": round(float(drift.median()), 2),
         "share_up": round(float((drift > 0).mean()), 3), "t_stat_mean": round(float(drift.mean() / (drift.std(ddof=1) / np.sqrt(len(drift)))), 2),
         "sum_pts": round(float(drift.sum()), 1), "sd_pts": round(float(drift.std(ddof=1)), 2)}
    md = f"""# Análises B e C (não são tentativas; partição de pesquisa)

## B — placebo reforçado da arquitetura ORB estrutural (EXP-0011)
200 sorteios (sementes 5000–5199) de direção aleatória nos mesmos {len(entries)} instantes de entrada, mesma saída (stop no extremo oposto da 1ª barra, saída 17:55).
```
{json.dumps(b, indent=1, ensure_ascii=False)}
```
Leitura: o candidato (+R$ {cand_exp:.1f}/trade) fica em z = {b['z']} do acaso; P(placebo ≥ candidato) = {p_emp:.3f}. {'O sinal de direção supera o acaso com folga estatística.' if p_emp < 0.05 else 'Não há folga estatística clara: o sinal de direção não é distinguível do acaso com esta amostra.'}

## C — deriva intradiária da amostra (abertura 09:00 → fechamento 17:55), nos dias com sessão
```
{json.dumps(c, indent=1, ensure_ascii=False)}
```
Leitura: {'deriva positiva relevante: favorece compras e explica parte da assimetria long/short (mecanismo independente da regra).' if c['t_stat_mean'] > 2 else 'deriva não significativa (|t| < 2): a assimetria long/short observada NÃO é explicada por uma deriva intradiária estatisticamente detectável.'} Sem custos; em pontos de preço.
"""
    (tools.RUN / "analysis_bc.md").write_text(md, encoding="utf-8")
    print(md.encode("ascii", "replace").decode())
