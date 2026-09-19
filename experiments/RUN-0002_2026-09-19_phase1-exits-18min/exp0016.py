import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tools
from wdo.strategies.candidates_run2 import GapAndGoFillStop

D15 = """# EXP-0015 — decisão: REJECT (NÃO SUSTENTADO)
Resultado: PF 0.877, WR 49.3%, PnL -R$472, DD 12.86%, 71 trades, payoff 0.90, expectância -R$6.65, meses + 3/5, top5 17.5%.
Pai EXP-0005 (10/6): PnL -R$182, expectância -R$2.56: o payoff 1:1 NÃO melhorou (pior). Placebo (10 sorteios): média -R$14.62, máx -R$2.56; excesso +R$8 (~1 erro-padrão, não distinguível).
Só o P4_RSI é positivo (+R$424, 13 trades, WR 69%); P1_EMA (32 trades) -R$579.
Integrity: Look-ahead PASS | Point-in-time PASS | Replay unchanged YES | New leakage risk NO | Leakage tests: pendente até o fim da run
Overfitting: hipótese estrutural YES (mecanismo de payoff); micro-tuning NO; complexidade justificada YES (0 dof); estabilidade checada YES; concentração aceitável YES; validação consultada NO; premissa desafiada YES (payoff 0.6); placebo reportado YES
"""

H = """# EXP-0016 — Gap-and-go com invalidação estrutural no preenchimento do gap
Pai: V0 (família nova; sem linha equivalente em knowledge.md — o EXP-0007 foi o fade de gap fora do range, direção oposta e outro construto). Ramo: Gap-and-Go. Família: continuação de gap.
**hypothesis_source:** literatura (Gao et al. 2018: retorno do fechamento anterior até a 1ª meia hora prevê a última; estudo arXiv 2605.04004 em MNQ: continuação de gap tão provável quanto preenchimento) + mecanismo (o preenchimento do gap invalida a tese: stop estrutural sem parâmetro).
**Premissa do V0 desafiada:** operar fades com saída fixa 10/6; janela livre (D9).
**Hipótese:** entrar na direção do gap da abertura, com stop no fechamento anterior e saída por horário 17:55, tem expectância acima do acaso.
**Os 4 pontos:** (i) fades/1ª barra não capturam o gap; (ii) direção do gap, stop = fechamento anterior, sem alvo, saída 17:55; guarda |gap| >= 2 pts (evita stop degenerado; não é parâmetro a otimizar); (iii) família e arquitetura novas; (iv) sustenta: expectância > 0 e acima do placebo com portões OK; rejeita: caso contrário.
Graus de liberdade: 0 (a guarda de 2 pts é mínimo técnico). Janela de sessão 09:00–18:00 (Config do candidato).
"""

if __name__ == "__main__":
    tools.write_decision(tools.RUN / "EXP-0015_v0-nochannel-symmetric-rr", D15)
    m15 = tools.load_metrics(tools.RUN / "EXP-0015_v0-nochannel-symmetric-rr" / "metrics.json")
    tools.add_registry(tools.registry_row2("EXP-0015", "RUN-0001/EXP-0005", "V0-Filters", "payoff-structure", "V0 fades (no channel) with symmetric 1:1 exit (10/10)",
                       "ExitSpec stop=target=10", "REJECT", m15, "mecanismo", "TP 6 / SL 10 payoff 0.6", "(i) new mechanism (payoff structure)", 0, 7))
    cfg = replace(tools.CFG, start_hour=9, start_minute=0, end_hour=18, end_minute=0)
    tools.run_experiment2("EXP-0016", "gap-and-go-fill-stop", GapAndGoFillStop, H,
                          {"strategy": "GapAndGoFillStop", "stop": "prior close", "exit_time": "17:55", "session_window": "09:00-18:00", "min_gap": 2.0, "dof": 0},
                          tools.load_metrics(tools.RUN / "EXP-0000_baseline-v0" / "metrics.json"), cfg=cfg)
