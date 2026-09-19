import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tools
from wdo.strategies.candidates_run2 import OrbFixedExit

D9 = """# EXP-0009 — decisão: REJECT (NÃO SUSTENTADO sob saída adaptativa por range)
Resultado (Research): PF 0.84, WR 30.0%, PnL -R$990, DD 18.02%, 100 trades, payoff 1.96, expectância -R$9.9, meses + 3/5, top5 trades 44.7%.
Placebo (10 sorteios, direção aleatória, mesma saída): expectância média -R$14.5, p95 -R$4.25, máx +R$2.25. Excesso do candidato +R$4.6/trade < 1 erro-padrão (~R$11): indistinguível do acaso. Reprova nos portões: DD 18% > 15%, top-5 44.7% > 40%, expectância < 0.
Saídas: 82% por TRAILING_STOP (stop = trailing = 0,25 × range) — o trailing com a mesma distância do stop retira o trade cedo; perda concentrada em dias de baixa volatilidade (-R$1044 em 52 trades vs +R$54 em 48): com stop escalado pequeno, custo+slippage pesam mais (razão custo/risco) — hipótese de mecanismo, formulada APÓS ver o resultado (data-informed).
Integrity checks:
- Look-ahead review: PASS (range do dia anterior e corpo da 1ª barra fechada; ExitSpec calculada na abertura da 2ª barra)
- Point-in-time features: PASS
- Replay assumptions unchanged: YES
- New leakage risk introduced: NO
- Leakage tests (05 §11) executed: pendente até o fim da run (tests/test_candidates_run2_leakage.py); resultado registrado no run_report
Overfitting review:
- Clear structural hypothesis: YES (literatura + mecanismo; reabertura por mecanismo novo)
- Micro-parameter tuning performed: NO (K=0.25 única alternativa a priori)
- Added complexity justified: NO (a controle fixa decide, EXP-0010)
- Temporal stability checked: YES (fev -1179; 3/5 meses +)
- PnL concentration acceptable: NO (top5 44.7%)
- Validation data consulted unnecessarily: NO
- Baseline assumption challenged with a stated hypothesis: YES (payoff 0.6 fixo)
- Excess over random-entry placebo reported: YES
"""

H = """# EXP-0010 — CONTROLE fixo do EXP-0009 (ORB de 5 min, stop = trailing = 10 pts, sem alvo, saída 17:55)
Pai: EXP-0009. Ramo: Opening-Momentum. Família: momentum + arquitetura de saída (contraparte fixa).
**hypothesis_source:** mecanismo (ablação: a adaptação ao range earns its place?). Reabertura: (i) mecanismo novo (mesma arquitetura do EXP-0009).
**Premissa desafiada:** que a distância de saída deva acompanhar a volatilidade do dia.
**Hipótese:** se a adaptação ao range agrega robustez (drawdown, estabilidade), o EXP-0009 supera esta contraparte fixa; se as duas ficam próximas, a mais simples (0 graus de liberdade) vence (06 §5).
**Os 4 pontos:** (i) distância variável adiciona um parâmetro (K); (ii) mesma arquitetura com distância fixa de 10 pts (= stop do V0); (iii) isola SÓ a adaptação (não é vizinho: mesma arquitetura, uma única troca); (iv) sustenta a adaptação: EXP-0009 melhor que este em drawdown/estabilidade/excesso sobre o placebo de forma material; rejeita: semelhante ou pior.
Graus de liberdade: 0.
"""

if __name__ == "__main__":
    import json
    tools.write_decision(tools.RUN / "EXP-0009_orb-adaptive-exit", D9)
    m9 = tools.load_metrics(tools.RUN / "EXP-0009_orb-adaptive-exit" / "metrics.json")
    tools.add_registry(tools.registry_row2("EXP-0009", "RUN-0001/EXP-0002", "Opening-Momentum", "momentum+exit-architecture",
                       "ORB with range-scaled stop, trailing, no target, EOD exit", "ExitSpec adaptive (K=0.25*range), exit 17:55", "REJECT", m9,
                       "literatura+mecanismo", "payoff 0.6 fixed TP/SL", "(i) new mechanism", 1, 1))
    parent = m9
    tools.run_experiment2("EXP-0010", "orb-fixed-exit-control", OrbFixedExit, H,
                          {"strategy": "OrbFixedExit", "exit": "stop=trail=10 pts, no target, exit_time 17:55", "dof": 0}, parent)
