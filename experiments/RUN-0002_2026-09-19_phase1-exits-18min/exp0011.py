import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tools
from wdo.strategies.candidates_run2 import OrbStructuralStop

D10 = """# EXP-0010 — decisão: REFINE (uma mudança ESTRUTURAL específica: remover o trailing, stop estrutural da literatura)
Resultado: PF 0.778, WR 40%, PnL -R$995, DD 13.55%, 100 trades, payoff 1.17, expectância -R$9.95, top5 34.9%, meses + 2/5.
Placebo (10 sorteios): expectância média -R$19.9, p95 -R$13.4, máx -R$12.85: o candidato fica ACIMA de todos os sorteios (excesso +R$9.9/trade); ainda < 0 após custos, então reprova só no portão de expectância (e concentração mensal por lucro total <= 0).
Controle vs EXP-0009: a adaptação ao range NÃO se paga (mesmo PnL, DD 13.5% vs 18.0%, excesso 9.9 vs 4.6, 0 vs 1 grau de liberdade) => preferir a versão fixa.
Diagnóstico: 77% das saídas por TRAILING_STOP (distância 10 = stop): whipsaw converte o sinal em perdas; o placebo também perde ~R$20/trade nessa arquitetura.
Integrity: Look-ahead PASS | Point-in-time PASS | Replay unchanged YES | New leakage risk NO | Leakage tests: pendente até o fim da run
Overfitting: hipótese estrutural YES; micro-tuning NO; complexidade justificada YES (0 dof); estabilidade checada YES; concentração aceitável YES (34.9%); validação consultada NO; premissa do V0 desafiada YES; placebo reportado YES
"""

H = """# EXP-0011 — ORB de 5 min com stop ESTRUTURAL, sem trailing, saída 17:55 (arquitetura da literatura)
Pai: EXP-0010 (frontier do ramo). Ramo: Opening-Momentum. Família: momentum + arquitetura de saída.
**hypothesis_source:** literatura (Zarattini & Aziz 2023: stop no extremo oposto da 1ª barra, sem trailing, posição mantida até o fechamento) + achado do EXP-0010 (77% de saídas por trailing curto; sinal acima do placebo, mas whipsaw).
**Premissa desafiada:** que a saída deva incluir trailing e distância derivada do stop do V0.
**Reabertura:** (i) mecanismo novo (stop por nível + ausência de trailing + saída por horário; não testado antes).
**Hipótese:** o sinal de continuação da 1ª barra é real mas pequeno; o trailing de 1R o converte em whipsaw. Um stop estrutural, sem trailing e com saída no fim do dia, preserva os movimentos maiores.
**Os 4 pontos:** (i) trailing de 10 pts sai cedo em 77% dos trades e o acaso perde ~R$20/trade; (ii) stop = extremo oposto da 1ª barra (nível), sem trailing, sem alvo, saída 17:55; (iii) muda a ARQUITETURA (remove trailing, stop por estrutura), não é um vizinho numérico; (iv) sustenta: expectância > 0 após custos e acima do placebo, DD dentro do portão; rejeita: caso contrário.
Graus de liberdade: 0. Risco: stop estrutural pode ser largo (drawdown); a guarda descarta trades com gap além do stop.
"""

if __name__ == "__main__":
    tools.write_decision(tools.RUN / "EXP-0010_orb-fixed-exit-control", D10)
    m10 = tools.load_metrics(tools.RUN / "EXP-0010_orb-fixed-exit-control" / "metrics.json")
    tools.add_registry(tools.registry_row2("EXP-0010", "EXP-0009", "Opening-Momentum", "momentum+exit-architecture",
                       "Fixed counterpart: does range-scaling earn its place?", "Same architecture, stop=trail=10 fixed", "REFINE", m10,
                       "mecanismo (ablação)", "distance must scale with volatility", "(i) new mechanism", 0, 2))
    tools.run_experiment2("EXP-0011", "orb-structural-stop", OrbStructuralStop, H,
                          {"strategy": "OrbStructuralStop", "exit": "stop=opposite extreme of 1st bar, no trailing, no target, exit_time 17:55", "dof": 0}, m10)
