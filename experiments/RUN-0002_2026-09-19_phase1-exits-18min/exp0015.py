import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tools
from wdo.strategies.candidates_run2 import V0NoChannelSymmetricRR

D14 = """# EXP-0014 — decisão: REJECT (NÃO SUSTENTADO; reabertura do EXP-0008 concluída)
Resultado: PF 0.49, WR 40.4%, PnL -R$1268, DD 14.34%, 99 trades, payoff 0.73, expectância -R$12.81, meses + 1/5.
Placebo (10 sorteios): média -R$13.49, p95 -R$4.27, máx -R$3.06: excesso +R$0.68/trade (ruído). 95 de 99 saídas por horário (17:55): a deriva de 25 min é menor que o custo de ida e volta (~R$12).
Conclusão: o EXP-0008 deixa de ser BLOCKED: NÃO SUSTENTADO no WDO nesta amostra e custos provisórios (entrada 17:30, saída 17:55).
Integrity: Look-ahead PASS (fechamento das 09:30 e fechamento anterior; entrada 17:30) | Point-in-time PASS | Replay unchanged YES (janela de sessão 09:00-18:00 é Config do candidato) | New leakage risk NO | Leakage tests: pendente até o fim da run
Overfitting: hipótese estrutural YES (literatura); micro-tuning NO; complexidade justificada YES; estabilidade checada YES (1/5); concentração aceitável YES (top5 36.2%); validação consultada NO; premissa desafiada YES (janela livre, D9); placebo reportado YES
"""

H = """# EXP-0015 — Fades do V0 (sem canal) com payoff simétrico 1:1 (stop 10 = alvo 10)
Pai: RUN-0001/EXP-0005 (fronteira; data-informed, usado como controle rotulado). Ramo: V0-Filters. Família: arquitetura de saída (payoff).
**hypothesis_source:** mecanismo (o payoff 0,6 do V0 obriga ~62,5% de acerto e perde ~R$12/trade sem edge; com 1:1 o ponto de equilíbrio cai para ~50% + custo) — Run 1, aprendizado estrutural 1. Sem fonte de literatura específica.
**Premissa desafiada:** o alvo curto de 6 pts (relação risco/retorno 0,6).
**Reabertura:** (i) mecanismo novo: EXP-0005/0006 só valem sob saída fixa 10/6; aqui muda-se a ESTRUTURA de payoff (1:1), não o alvo para vizinhos (6→6,5...).
**Os 4 pontos:** (i) alvo de 6 com stop de 10 exige acerto muito alto; (ii) alvo = stop = 10 pts (uma alternativa a priori, 0 novos parâmetros); (iii) muda o perfil de payoff de 0,6 para 1,0, não é um vizinho; (iv) sustenta: expectância > 0 e acima do placebo com portões OK; rejeita: caso contrário.
Graus de liberdade: 0. Nota: a entrada (V0 sem P3) é data-informed; sem contraparte adaptativa (controle já é o V0 de saída 10/6: EXP-0005).
"""

if __name__ == "__main__":
    tools.write_decision(tools.RUN / "EXP-0014_late-day-momentum-exit", D14)
    m14 = tools.load_metrics(tools.RUN / "EXP-0014_late-day-momentum-exit" / "metrics.json")
    tools.add_registry(tools.registry_row2("EXP-0014", "RUN-0001/EXP-0008", "Intraday-Momentum-LateDay", "intraday-momentum",
                       "First-half-hour return predicts last half-hour; entry 17:30, exit 17:55", "ExitSpec stop=0.25*range, exit_time 17:55; session 09:00-18:00", "REJECT", m14,
                       "literatura", "opening-only window; fixed exits", "(i) new mechanism (exit_time)", 1, 6))
    exp5 = tools.load_metrics(tools.ROOT / "experiments" / "RUN-0001_2026-09-19_phase1-first-18min" / "EXP-0005_v0-no-channel" / "metrics.json")
    tools.run_experiment2("EXP-0015", "v0-nochannel-symmetric-rr", V0NoChannelSymmetricRR, H,
                          {"strategy": "V0NoChannelSymmetricRR", "exit": "stop=target=10 pts", "dof": 0}, exp5)
